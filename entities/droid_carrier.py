# entities/droid_carrier.py
"""
Droid Carrier - 드로이드를 투하하는 캐리어 적
Wave 6+부터 짝수 웨이브에 등장
"""

import pygame
import random
from typing import List, Optional, Tuple
import config
from asset_manager import AssetManager
from entities.enemies import Enemy


class DroidCarrier:
    """드로이드를 투하하는 캐리어 적"""

    def __init__(self, screen_size: Tuple[int, int], current_wave: int):
        """
        Args:
            screen_size: (width, height)
            current_wave: 현재 웨이브 번호
        """
        self.screen_width, self.screen_height = screen_size
        self.current_wave = current_wave

        # 타입 설정 가져오기
        self.type_config = config.ENEMY_TYPES["DROID_CARRIER"]

        # 위치 (화면 상단 중앙에서 시작)
        self.x = self.screen_width // 2
        self.y = -100  # 화면 위에서 진입
        self.pos = pygame.math.Vector2(self.x, self.y)

        # 이동 패턴
        self.speed = config.ENEMY_BASE_SPEED * self.type_config["speed_mult"] * 2.5  # 2.5배 속도 (더 빠르게)
        self.target_y = int(self.screen_height * 0.125)  # 화면 높이의 1/8 지점 (최상부)
        self.entered_screen = False  # 화면 진입 완료 여부
        self.retreating = False  # 퇴각 중 여부

        # 날개 offset (드로이드 투하 위치)
        self.wing_offset = 150  # 좌우 날개 간격 (더 넓게)

        # 스탯
        self.max_hp = config.ENEMY_BASE_HP * self.type_config["hp_mult"]
        self.hp = self.max_hp
        self.damage = 0  # 충돌 데미지 없음

        # 이미지 로드
        size_ratio = config.IMAGE_SIZE_RATIOS["ENEMY"]
        image_size = int(self.screen_height * size_ratio * self.type_config["size_mult"])
        image_path = config.ASSET_DIR / "images" / "gameplay" / "enemies" / self.type_config["image"]
        self.image = AssetManager.get_image(image_path, (image_size, image_size))
        self.image_rect = self.image.get_rect(center=(int(self.pos.x), int(self.pos.y)))

        # 히트박스
        hitbox_size = int(image_size * config.ENEMY_HITBOX_RATIO)
        self.hitbox = pygame.Rect(0, 0, hitbox_size, hitbox_size)
        self.hitbox.center = (int(self.pos.x), int(self.pos.y))

        # 드로이드 투하 시스템
        self.spawn_droid_count = self.type_config["spawn_droid_count"]  # 10개
        self.spawn_droid_interval = self.type_config["spawn_droid_interval"]  # 2초
        self.droids_spawned = 0  # 투하한 드로이드 개수
        self.last_spawn_time = 0.0
        self.spawned_droids: List[Enemy] = []  # 생성된 드로이드 리스트

        # HP 젬 드롭
        self.drops_hp_gem = self.type_config.get("drops_hp_gem", False)
        self.hp_gem_dropped = False  # HP 젬 드롭 여부

        # 사망 플래그
        self.dead = False

    def update(self, dt: float, current_time: float) -> List[Enemy]:
        """업데이트 - 드로이드 투하 포함

        Returns:
            새로 생성된 드로이드 리스트
        """
        newly_spawned_droids = []

        # 1. 화면 진입 (하강)
        if not self.entered_screen:
            self.pos.y += self.speed * dt
            if self.pos.y >= self.target_y:
                self.pos.y = self.target_y
                self.entered_screen = True
                self.last_spawn_time = current_time  # 투하 시작
                print(f"INFO: Carrier entered at y={self.target_y} (1/8 screen)")

        # 2. 정지 상태에서 드로이드 투하
        elif self.entered_screen and not self.retreating:
            # 캐리어는 정지 상태 유지 (좌우 이동 없음)

            # 드로이드 투하 (2개씩, 좌우 날개에서)
            if self.droids_spawned < self.spawn_droid_count:
                if current_time - self.last_spawn_time >= self.spawn_droid_interval:
                    from entities.sphere_droid import SphereDroid

                    # 좌측 날개에서 드로이드 투하 (반시계 방향)
                    left_spawn_x = self.pos.x - self.wing_offset
                    left_droid = SphereDroid(
                        spawn_pos=(left_spawn_x, self.pos.y),
                        screen_size=(self.screen_width, self.screen_height),
                        direction="left"
                    )
                    newly_spawned_droids.append(left_droid)
                    self.spawned_droids.append(left_droid)
                    self.droids_spawned += 1

                    # 우측 날개에서 드로이드 투하 (시계 방향)
                    right_spawn_x = self.pos.x + self.wing_offset
                    right_droid = SphereDroid(
                        spawn_pos=(right_spawn_x, self.pos.y),
                        screen_size=(self.screen_width, self.screen_height),
                        direction="right"
                    )
                    newly_spawned_droids.append(right_droid)
                    self.spawned_droids.append(right_droid)
                    self.droids_spawned += 1

                    self.last_spawn_time = current_time
                    print(f"INFO: Carrier spawned 2 droids from wings ({self.droids_spawned}/{self.spawn_droid_count})")

            # 모든 드로이드 투하 완료 시 퇴각 시작
            if self.droids_spawned >= self.spawn_droid_count:
                self.retreating = True
                print("INFO: Carrier retreating upward after deploying all droids")

        # 3. 퇴각 (위로 상승)
        elif self.retreating:
            self.pos.y -= self.speed * dt
            if self.pos.y < -200:
                self.dead = True  # 화면 밖으로 나가면 제거
                print("INFO: Carrier exited screen")

        # 위치 업데이트
        self.image_rect.center = (int(self.pos.x), int(self.pos.y))
        self.hitbox.center = (int(self.pos.x), int(self.pos.y))

        return newly_spawned_droids

    def take_damage(self, damage: float) -> bool:
        """피격 처리

        Returns:
            HP 젬 드롭 여부
        """
        if self.hp_gem_dropped:
            return False  # 이미 HP 젬 드롭했으면 추가 드롭 없음

        self.hp -= damage
        if self.hp <= 0:
            self.hp = 0

        # 피격 시 HP 젬 드롭 (1회만)
        if self.drops_hp_gem and not self.hp_gem_dropped:
            self.hp_gem_dropped = True
            print("INFO: Carrier hit! Dropping HP gem")
            return True  # HP 젬 드롭

        return False

    def draw(self, screen: pygame.Surface):
        """화면에 그리기"""
        screen.blit(self.image, self.image_rect)

        # HP 바 표시
        if self.hp < self.max_hp:
            bar_width = 80
            bar_height = 6
            bar_x = int(self.pos.x - bar_width // 2)
            bar_y = int(self.pos.y - 60)

            # 배경 (검은색)
            pygame.draw.rect(screen, (0, 0, 0), (bar_x, bar_y, bar_width, bar_height))

            # HP (초록색 → 노란색 → 빨간색)
            hp_ratio = self.hp / self.max_hp
            fill_width = int(bar_width * hp_ratio)

            if hp_ratio > 0.5:
                color = (0, 255, 0)
            elif hp_ratio > 0.25:
                color = (255, 255, 0)
            else:
                color = (255, 0, 0)

            if fill_width > 0:
                pygame.draw.rect(screen, color, (bar_x, bar_y, fill_width, bar_height))
