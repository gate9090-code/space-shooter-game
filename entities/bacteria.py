# entities/bacteria.py
"""
Bacteria - 박테리아 (카오스 박테리아 생성기가 투하)
Wave 6+ 홀수 웨이브에 등장
"""

import pygame
import random
import math
from typing import Tuple, Optional
import config
from asset_manager import AssetManager


class Bacteria:
    """박테리아 - 플레이어 추적 및 달라붙기"""

    def __init__(
        self,
        spawn_pos: Tuple[float, float],
        screen_size: Tuple[int, int],
        spawn_time: float
    ):
        """
        Args:
            spawn_pos: 투하 위치 (x, y)
            screen_size: (width, height)
            spawn_time: 생성 시간 (듀레이션 계산용)
        """
        self.screen_width, self.screen_height = screen_size
        self.pos = pygame.math.Vector2(spawn_pos)
        self.spawn_time = spawn_time

        # 타입 설정
        self.type_config = config.ENEMY_TYPES["BACTERIA"]

        # 스탯
        self.max_hp = config.ENEMY_BASE_HP * self.type_config["hp_mult"]  # 99900 (일반 공격 무적)
        self.hp = self.max_hp
        self.damage_per_second = config.ENEMY_ATTACK_DAMAGE * self.type_config["damage_mult"]  # 15
        self.speed = config.ENEMY_BASE_SPEED * self.type_config["speed_mult"]

        # 이미지 로드
        size_ratio = config.IMAGE_SIZE_RATIOS["ENEMY"]
        image_size = int(self.screen_height * size_ratio * self.type_config["size_mult"])
        image_path = config.ASSET_DIR / "images" / "gameplay" / "enemies" / self.type_config["image"]

        try:
            self.original_image = AssetManager.get_image(image_path, (image_size, image_size))
            # 투명 배경 유지 (틴트 제거)
            self.image = self.original_image.copy()
        except Exception as e:
            # 폴백: 녹색 원
            self.image = pygame.Surface((image_size, image_size), pygame.SRCALPHA)
            pygame.draw.circle(self.image, (0, 255, 100), (image_size//2, image_size//2), image_size//2)
            print(f"WARNING: coli_bacteria.png not found, using fallback. Error: {e}")

        self.image_rect = self.image.get_rect(center=(int(self.pos.x), int(self.pos.y)))

        # 히트박스
        hitbox_size = int(image_size * config.ENEMY_HITBOX_RATIO)
        self.hitbox = pygame.Rect(0, 0, hitbox_size, hitbox_size)
        self.hitbox.center = (int(self.pos.x), int(self.pos.y))

        # 무작위 이동 AI
        self.target_pos = self._generate_random_target()
        self.move_timer = 0.0
        self.move_interval = random.uniform(1.0, 3.0)  # 1~3초마다 타겟 변경

        # 플레이어 추적 및 달라붙기
        self.attached_to_player = False
        self.attach_overlap_ratio = self.type_config["attach_overlap"]  # 0.1 (10%)
        self.last_damage_time = 0.0
        self.damage_interval = 1.0  # 1초마다 데미지

        # 듀레이션 (5초)
        self.duration = self.type_config["duration"]
        self.despawn_time = spawn_time + self.duration

        # 특수 무기 취약성
        self.vulnerable_to_special = self.type_config.get("vulnerable_to_special", True)

        # 상태
        self.is_alive = True
        self.dead = False  # wave_mode 호환성

    def _generate_random_target(self) -> pygame.math.Vector2:
        """화면 전역에서 랜덤 타겟 생성 (경계 밖 포함)"""
        margin = 100
        random_x = random.uniform(-margin, self.screen_width + margin)
        random_y = random.uniform(-margin, self.screen_height + margin)
        return pygame.math.Vector2(random_x, random_y)

    def update(self, dt: float, current_time: float, player_pos: Optional[pygame.math.Vector2] = None) -> Tuple[bool, float]:
        """업데이트

        Args:
            dt: 델타 타임
            current_time: 현재 시간
            player_pos: 플레이어 위치 (Vector2 또는 None)

        Returns:
            (달라붙음 여부, 이번 프레임 데미지)
        """
        if not self.is_alive:
            return (False, 0.0)

        # 듀레이션 체크 (5초 경과 시 자동 소멸)
        if current_time >= self.despawn_time:
            self.is_alive = False
            self.dead = True
            print(f"INFO: Bacteria expired after {self.duration}s")
            return (False, 0.0)

        damage_dealt = 0.0

        # 플레이어가 있으면 추적 및 달라붙기 시도
        if player_pos is not None:
            distance_to_player = (player_pos - self.pos).length()

            # 달라붙기 판정 (10% 겹침)
            attach_threshold = self.hitbox.width * (1.0 - self.attach_overlap_ratio)

            if distance_to_player <= attach_threshold:
                if not self.attached_to_player:
                    self.attached_to_player = True
                    self.last_damage_time = current_time
                    print("INFO: Bacteria attached to player!")

                # 달라붙은 상태: 플레이어 위치로 이동
                self.pos = player_pos.copy()

                # 1초마다 데미지
                if current_time - self.last_damage_time >= self.damage_interval:
                    damage_dealt = self.damage_per_second
                    self.last_damage_time = current_time

            else:
                # 달라붙지 않은 상태: 플레이어를 향해 이동
                self.attached_to_player = False
                direction = (player_pos - self.pos)
                if direction.length() > 0:
                    direction = direction.normalize()
                    self.pos += direction * self.speed * dt

        else:
            # 플레이어 없음: 무작위 이동
            self.attached_to_player = False
            self._random_movement(dt)

        # 위치 업데이트
        self.image_rect.center = (int(self.pos.x), int(self.pos.y))
        self.hitbox.center = (int(self.pos.x), int(self.pos.y))

        return (self.attached_to_player, damage_dealt)

    def _random_movement(self, dt: float):
        """무작위 이동 AI"""
        # 타겟 도달 체크
        distance = (self.target_pos - self.pos).length()
        if distance < 10:
            # 새 타겟 생성
            self.target_pos = self._generate_random_target()
            self.move_interval = random.uniform(1.0, 3.0)

        # 타겟으로 이동
        direction = (self.target_pos - self.pos)
        if direction.length() > 0:
            direction = direction.normalize()
            self.pos += direction * self.speed * dt

        # 일정 시간마다 타겟 변경
        self.move_timer += dt
        if self.move_timer >= self.move_interval:
            self.target_pos = self._generate_random_target()
            self.move_timer = 0.0
            self.move_interval = random.uniform(1.0, 3.0)

    def take_damage(self, damage: float, is_special_weapon: bool = False):
        """피격 처리

        Args:
            damage: 데미지량
            is_special_weapon: 특수 무기 여부 (static field, lightning chain)
        """
        # 일반 공격은 무시 (HP가 매우 높음)
        if not is_special_weapon:
            return  # 데미지 무시

        # 특수 무기 공격만 유효
        if is_special_weapon and self.vulnerable_to_special:
            self.hp -= damage
            if self.hp <= 0:
                self.hp = 0
                self.is_alive = False
                self.dead = True
                print("INFO: Bacteria destroyed by special weapon!")

    def draw(self, screen: pygame.Surface):
        """렌더링"""
        if self.is_alive:
            screen.blit(self.image, self.image_rect)

            # 디버그: 달라붙은 상태 표시 (작은 초록색 링)
            if self.attached_to_player:
                pygame.draw.circle(
                    screen,
                    (0, 255, 0),
                    (int(self.pos.x), int(self.pos.y)),
                    self.hitbox.width // 2 + 5,
                    2
                )
