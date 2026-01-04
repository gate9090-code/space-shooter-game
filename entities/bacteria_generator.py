# entities/bacteria_generator.py
"""
Bacteria Generator - 박테리아를 투하하는 생성기
Wave 6+ 홀수 웨이브에 등장
"""

import pygame
import math
import random
from typing import List, Tuple
import config
from asset_manager import AssetManager


class BacteriaGenerator:
    """박테리아를 투하하는 생성기 - 원운동 패턴"""

    def __init__(self, screen_size: Tuple[int, int], current_wave: int):
        """
        Args:
            screen_size: (width, height)
            current_wave: 현재 웨이브 번호
        """
        self.screen_width, self.screen_height = screen_size
        self.current_wave = current_wave

        # 타입 설정
        self.type_config = config.ENEMY_TYPES["BACTERIA_GENERATOR"]

        # 위치 (화면 상단 중앙에서 시작)
        self.center_x = self.screen_width // 2
        self.orbit_center_y = int(self.screen_height * 0.4)  # 타원 중심 (화면 40% 지점)
        self.pos = pygame.math.Vector2(self.center_x, -100)

        # 이동 패턴
        self.speed = config.ENEMY_BASE_SPEED * self.type_config["speed_mult"]
        self.descending = True  # 하강 중
        self.orbiting = False  # 타원운동 중 여부
        self.fading_out = False  # 페이드아웃 중 여부

        # 타원운동 설정 (가로로 긴 타원)
        self.orbit_radius_x = int(self.screen_width * 0.35)  # 가로 반지름 (35%)
        self.orbit_radius_y = int(self.screen_height * 0.15)  # 세로 반지름 (15%)
        self.orbit_angle = 0.0  # 현재 각도 (라디안)
        self.orbit_speed = 0.2  # 회전 속도 (라디안/초, 아주 느리게 - 1.0에서 0.2로)

        # 스탯
        self.max_hp = 9999  # 무적
        self.hp = self.max_hp
        self.damage = 0  # 충돌 데미지 없음

        # 이미지 로드
        size_ratio = config.IMAGE_SIZE_RATIOS["ENEMY"]
        image_size = int(self.screen_height * size_ratio * self.type_config["size_mult"])
        image_path = config.ASSET_DIR / "images" / "gameplay" / "enemies" / self.type_config["image"]

        try:
            self.original_image = AssetManager.get_image(image_path, (image_size, image_size))
        except Exception as e:
            # 폴백: 보라색 원
            self.original_image = pygame.Surface((image_size, image_size), pygame.SRCALPHA)
            pygame.draw.circle(self.original_image, (200, 100, 255), (image_size//2, image_size//2), image_size//2)
            print(f"WARNING: bacteria_generator.png not found, using fallback. Error: {e}")

        self.image = self.original_image.copy()
        self.image_rect = self.image.get_rect(center=(int(self.pos.x), int(self.pos.y)))

        # 히트박스 (공격 불가)
        hitbox_size = int(image_size * config.ENEMY_HITBOX_RATIO)
        self.hitbox = pygame.Rect(0, 0, hitbox_size, hitbox_size)
        self.hitbox.center = (int(self.pos.x), int(self.pos.y))

        # 박테리아 투하 시스템
        self.spawn_bacteria_count = self.type_config["spawn_bacteria_count"]  # 50개
        self.spawn_bacteria_interval = self.type_config["spawn_bacteria_interval"]  # 3초
        self.bacteria_spawned = 0  # 투하한 박테리아 개수
        self.last_spawn_time = 0.0
        self.spawned_bacteria: List = []  # 생성된 박테리아 리스트

        # 페이드아웃
        self.alpha = 255
        self.fade_speed = 200  # 투명도 감소 속도 (초당)

        # 상태
        self.dead = False

    def update(self, dt: float, current_time: float) -> List:
        """업데이트 - 박테리아 투하 포함

        Returns:
            새로 생성된 박테리아 리스트
        """
        newly_spawned_bacteria = []

        # 1. 화면 진입 (타원 궤도까지 하강)
        if self.descending:
            self.pos.y += self.speed * dt
            # 타원 궤도 시작 지점 (상단)
            orbit_start_y = self.orbit_center_y - self.orbit_radius_y
            if self.pos.y >= orbit_start_y:
                self.pos.y = orbit_start_y
                self.pos.x = self.center_x
                self.descending = False
                self.orbiting = True
                self.last_spawn_time = current_time  # 투하 시작
                print(f"INFO: Bacteria Generator reached elliptical orbit at y={orbit_start_y}")

        # 2. 타원운동하며 박테리아 투하
        elif self.orbiting and not self.fading_out:
            # 타원운동 (반시계 방향, 아주 느리게)
            self.orbit_angle += self.orbit_speed * dt
            if self.orbit_angle >= 2 * math.pi:
                self.orbit_angle -= 2 * math.pi

            # 위치 계산 (타원 궤도)
            self.pos.x = self.center_x + self.orbit_radius_x * math.cos(self.orbit_angle)
            self.pos.y = self.orbit_center_y + self.orbit_radius_y * math.sin(self.orbit_angle)

            # 박테리아 투하 (5개씩)
            if self.bacteria_spawned < self.spawn_bacteria_count:
                if current_time - self.last_spawn_time >= self.spawn_bacteria_interval:
                    from entities.bacteria import Bacteria

                    # 5개 생성 (원형으로 분산, 뭉치지 않게)
                    for i in range(5):
                        # 원형으로 균등 분산 (각도를 5등분)
                        angle = (2 * math.pi / 5) * i + random.uniform(-0.3, 0.3)  # 약간의 랜덤성 추가
                        distance = random.uniform(80, 150)  # 거리도 랜덤하게 (더 넓게 분산)
                        random_x = self.pos.x + distance * math.cos(angle)
                        random_y = self.pos.y + distance * math.sin(angle)

                        bacteria = Bacteria(
                            spawn_pos=(random_x, random_y),
                            screen_size=(self.screen_width, self.screen_height),
                            spawn_time=current_time
                        )
                        newly_spawned_bacteria.append(bacteria)
                        self.spawned_bacteria.append(bacteria)
                        self.bacteria_spawned += 1

                    self.last_spawn_time = current_time
                    print(f"INFO: Generator spawned 5 bacteria ({self.bacteria_spawned}/{self.spawn_bacteria_count})")

            # 모든 박테리아 투하 완료 시 페이드아웃 시작
            if self.bacteria_spawned >= self.spawn_bacteria_count:
                self.fading_out = True
                print("INFO: Generator starting fade out after spawning all bacteria")

        # 3. 페이드아웃
        elif self.fading_out:
            # 계속 타원운동하며 페이드아웃
            self.orbit_angle += self.orbit_speed * dt
            if self.orbit_angle >= 2 * math.pi:
                self.orbit_angle -= 2 * math.pi

            self.pos.x = self.center_x + self.orbit_radius_x * math.cos(self.orbit_angle)
            self.pos.y = self.orbit_center_y + self.orbit_radius_y * math.sin(self.orbit_angle)

            # 알파 감소
            self.alpha -= self.fade_speed * dt
            if self.alpha <= 0:
                self.alpha = 0
                self.dead = True  # 완전히 사라지면 제거
                print("INFO: Generator faded out completely")

            # 이미지 투명도 적용
            self.image = self.original_image.copy()
            self.image.set_alpha(int(self.alpha))

        # 위치 업데이트
        self.image_rect.center = (int(self.pos.x), int(self.pos.y))
        self.hitbox.center = (int(self.pos.x), int(self.pos.y))

        return newly_spawned_bacteria

    def draw(self, screen: pygame.Surface):
        """화면에 그리기"""
        screen.blit(self.image, self.image_rect)
