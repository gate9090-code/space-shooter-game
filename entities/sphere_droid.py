# entities/sphere_droid.py
"""
Sphere Droid - 사각형 순찰 패턴을 가진 드로이드
"""

import pygame
import math
from typing import Tuple
import config
from asset_manager import AssetManager


class SphereDroid:
    """사각형 순찰 패턴을 가진 스피어 드로이드"""

    def __init__(
        self,
        spawn_pos: Tuple[float, float],
        screen_size: Tuple[int, int],
        direction: str,  # "left" 또는 "right"
    ):
        """
        Args:
            spawn_pos: 투하 위치 (x, y)
            screen_size: (width, height)
            direction: "left" (반시계) 또는 "right" (시계)
        """
        self.screen_width, self.screen_height = screen_size
        self.pos = pygame.math.Vector2(spawn_pos)
        self.direction = direction  # "left" or "right"

        # 타입 설정
        self.type_config = config.ENEMY_TYPES["SPHERE_DROID"]

        # 스탯
        self.max_hp = config.ENEMY_BASE_HP * self.type_config["hp_mult"]
        self.hp = self.max_hp
        self.damage = config.ENEMY_ATTACK_DAMAGE * self.type_config["damage_mult"]
        self.speed = config.ENEMY_BASE_SPEED * self.type_config["speed_mult"]

        # 이미지
        size_ratio = config.IMAGE_SIZE_RATIOS["ENEMY"]
        image_size = int(self.screen_height * size_ratio * self.type_config["size_mult"])
        image_path = config.ASSET_DIR / "images" / "gameplay" / "enemies" / self.type_config["image"]
        self.image = AssetManager.get_image(image_path, (image_size, image_size))
        self.image_rect = self.image.get_rect(center=(int(self.pos.x), int(self.pos.y)))

        # 히트박스
        hitbox_size = int(image_size * config.ENEMY_HITBOX_RATIO)
        self.hitbox = pygame.Rect(0, 0, hitbox_size, hitbox_size)
        self.hitbox.center = (int(self.pos.x), int(self.pos.y))

        # 사각형 순찰 패턴 waypoints
        self.patrol_state = 0  # 0: 수평, 1: 하강, 2: 중앙이동, 3: 상승
        self.spawn_x = spawn_pos[0]  # 투하 지점 x (중앙 수렴 한계점)
        self.spawn_y = spawn_pos[1]  # 투하 지점 y

        # 경로 포인트 계산 (더 넓게 이동)
        edge_x = self.screen_width * 0.9 if direction == "right" else self.screen_width * 0.1
        bottom_y = self.screen_height * 0.9  # 하단 경계

        # Waypoints: [state0_target, state1_target, state2_target, state3_target]
        if direction == "left":  # 반시계 (←, ↓, →, ↑)
            self.waypoints = [
                pygame.math.Vector2(edge_x, spawn_pos[1]),      # 0: 좌측 끝으로 (10%)
                pygame.math.Vector2(edge_x, bottom_y),          # 1: 하강
                pygame.math.Vector2(self.spawn_x, bottom_y),    # 2: 투하 x좌표까지 (겹치지 않음)
                pygame.math.Vector2(self.spawn_x, spawn_pos[1]) # 3: 상승 (투하 지점)
            ]
        else:  # "right" - 시계 (→, ↓, ←, ↑)
            self.waypoints = [
                pygame.math.Vector2(edge_x, spawn_pos[1]),      # 0: 우측 끝으로 (90%)
                pygame.math.Vector2(edge_x, bottom_y),          # 1: 하강
                pygame.math.Vector2(self.spawn_x, bottom_y),    # 2: 투하 x좌표까지 (겹치지 않음)
                pygame.math.Vector2(self.spawn_x, spawn_pos[1]) # 3: 상승 (투하 지점)
            ]

        self.current_target = self.waypoints[0]

        # 상태
        self.is_alive = True
        self.color = (255, 255, 255)  # 원본 색상
        self.size = image_size // 2

        # 히트 플래시
        self.hit_flash_timer = 0.0
        self.is_flashing = False
        self.original_image = self.image.copy()

    def update(self, dt: float):
        """업데이트 - 사각형 순찰"""
        if not self.is_alive:
            return

        # 히트 플래시 업데이트
        if self.is_flashing:
            self.hit_flash_timer -= dt
            if self.hit_flash_timer <= 0:
                self.is_flashing = False
                self.image = self.original_image.copy()

        # 현재 타겟으로 이동
        direction = self.current_target - self.pos
        distance = direction.length()

        if distance > 5:  # 타겟에 도달하지 않음
            direction = direction.normalize()
            self.pos += direction * self.speed * dt
        else:  # 타겟 도달 → 다음 waypoint로
            self.patrol_state = (self.patrol_state + 1) % 4
            self.current_target = self.waypoints[self.patrol_state]

        # 위치 업데이트
        self.image_rect.center = (int(self.pos.x), int(self.pos.y))
        self.hitbox.center = (int(self.pos.x), int(self.pos.y))

    def take_damage(self, damage: float):
        """피격 처리"""
        self.hp -= damage
        if self.hp <= 0:
            self.hp = 0
            self.is_alive = False
        else:
            # 히트 플래시 (노란색)
            self.is_flashing = True
            self.hit_flash_timer = 0.1
            flash_image = self.original_image.copy()
            flash_image.fill((255, 255, 0, 128), special_flags=pygame.BLEND_RGBA_ADD)  # 노란색 플래시
            self.image = flash_image

    def draw(self, screen: pygame.Surface):
        """렌더링"""
        screen.blit(self.image, self.image_rect)

        # HP 바
        if self.hp < self.max_hp:
            bar_width = 40
            bar_height = 4
            bar_x = int(self.pos.x - bar_width // 2)
            bar_y = int(self.pos.y - 30)

            # 배경
            pygame.draw.rect(screen, (0, 0, 0), (bar_x, bar_y, bar_width, bar_height))

            # HP
            hp_ratio = self.hp / self.max_hp
            fill_width = int(bar_width * hp_ratio)
            color = (0, 255, 0) if hp_ratio > 0.5 else (255, 255, 0) if hp_ratio > 0.25 else (255, 0, 0)
            if fill_width > 0:
                pygame.draw.rect(screen, color, (bar_x, bar_y, fill_width, bar_height))
