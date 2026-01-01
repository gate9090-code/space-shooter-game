# entities/weapons.py
# 무기 및 발사체 클래스

import pygame
import math
from typing import List
import config
from asset_manager import AssetManager


class Weapon:
    def __init__(
        self,
        damage: float,
        cooldown: float,
        bullet_count: int,
        spread_angle: float = 5.0,
    ):
        self.damage = damage
        self.cooldown = cooldown
        self.bullet_count = bullet_count
        self.spread_angle = spread_angle
        self.time_since_last_shot = 0.0  # 발사 쿨타임 추적

    def update(self, dt: float):
        """무기의 쿨타임을 업데이트합니다."""
        self.time_since_last_shot += dt

    def can_shoot(self) -> bool:
        """현재 발사 가능한지 확인합니다."""
        return self.time_since_last_shot >= self.cooldown

    def fire(
        self,
        start_pos: pygame.math.Vector2,
        target_pos: pygame.math.Vector2,
        bullets: List,
        piercing_state: bool,
        player=None,
    ):
        """
        지정된 목표 위치로 총알을 발사합니다.
        """
        if not self.can_shoot():
            return

        self.time_since_last_shot = 0.0  # 쿨타임 초기화

        # 목표 방향 벡터 계산
        direction = target_pos - start_pos
        base_angle = math.atan2(direction.y, direction.x)

        # Berserker 스킬: 저체력 시 데미지 2배
        bullet_damage = self.damage
        if player and hasattr(player, "has_berserker") and player.has_berserker:
            if player.hp / player.max_hp < 0.3:
                bullet_damage = int(self.damage * 2.0)

        # 발사각 분산 계산
        for i in range(self.bullet_count):
            if self.bullet_count == 1:
                angle_offset = 0
            else:
                # 총알 수에 따라 균등하게 각도를 분산
                angle_spread = self.spread_angle * (self.bullet_count - 1)
                start_offset = -angle_spread / 2
                angle_offset = start_offset + (i * self.spread_angle)

            # 각도를 라디안에서 쿼터니언 (이동 벡터)로 변환
            new_angle = base_angle + math.radians(angle_offset)
            bullet_direction = pygame.math.Vector2(
                math.cos(new_angle), math.sin(new_angle)
            ).normalize()

            # 새 총알 객체 생성 및 리스트에 추가
            bullet = Bullet(
                start_pos.copy(),
                bullet_direction,
                bullet_damage,
                piercing_state,  # 피어싱 상태를 Bullet에 전달
            )
            bullets.append(bullet)

    # 전술 레벨업을 위한 메서드 (utils.py에서 호출)
    def increase_damage(self, ratio: float):
        self.damage = int(self.damage * (1 + ratio))
        print(f"INFO: Damage increased to {self.damage}")

    def decrease_cooldown(self, ratio: float):
        self.cooldown = max(0.05, self.cooldown * (1 - ratio))
        print(f"INFO: Cooldown decreased to {self.cooldown:.2f}")

    def add_bullet(self):
        self.bullet_count += 1
        print(f"INFO: Bullet count increased to {self.bullet_count}")


class Bullet:
    """총알 클래스"""

    def __init__(
        self,
        pos: pygame.math.Vector2,
        direction: pygame.math.Vector2,
        damage: float,
        piercing: bool = False,
    ):

        # 1. 위치 및 이동
        self.pos = pos
        self.direction = direction.normalize()
        self.speed = config.BULLET_SPEED

        # 2. 스탯
        self.damage = damage
        self.is_alive = True

        # 3. 피어싱 기능
        self.is_piercing = piercing
        self.pierce_count = 0  # 관통한 적 수 (최대값 도달 시 제거)
        self.hit_enemies = set()  # 이미 맞춘 적 ID 집합 (중복 피격 방지)

        # 4. 총알 트레일 (잔상)
        self.trail_positions = []  # 이전 위치들 저장

        # 5. 스폰 시간 (벽 충돌 유예 기간용)
        self.spawn_time = pygame.time.get_ticks()

        # 6. 이미지 및 히트박스
        # bullet_image는 asset_manager에서 공통으로 사용하므로 최초 1회만 로드

    def initialize_image(self, screen_height: int):
        """화면 크기에 맞게 총알 이미지를 초기화합니다."""

        size_ratio = config.IMAGE_SIZE_RATIOS["BULLET"]
        image_size = int(screen_height * size_ratio)

        self.image = AssetManager.get_image(
            config.PLAYER_BULLET_IMAGE_PATH, (image_size, image_size)
        )
        self.image_rect = self.image.get_rect(center=(self.pos.x, self.pos.y))

        hitbox_size = int(image_size * config.BULLET_HITBOX_RATIO)
        self.hitbox = pygame.Rect(0, 0, hitbox_size, hitbox_size)
        self.hitbox.center = (int(self.pos.x), int(self.pos.y))

    def update(self, dt: float, screen_size: tuple):
        """총알 위치를 업데이트하고, 화면 밖으로 나가면 제거합니다."""

        if not hasattr(self, "image"):
            # 첫 update 시 이미지 초기화
            self.initialize_image(screen_size[1])

        if self.is_alive:
            # 현재 위치를 트레일에 추가
            self.trail_positions.append(self.pos.copy())

            # 트레일 길이 제한
            if len(self.trail_positions) > config.BULLET_TRAIL_LENGTH:
                self.trail_positions.pop(0)

            self.pos += self.direction * self.speed * dt
            self.image_rect.center = (int(self.pos.x), int(self.pos.y))
            self.hitbox.center = self.image_rect.center

            # 화면 밖으로 나가면 제거
            SCREEN_WIDTH, SCREEN_HEIGHT = screen_size
            if (
                self.pos.x < -50
                or self.pos.x > SCREEN_WIDTH + 50
                or self.pos.y < -50
                or self.pos.y > SCREEN_HEIGHT + 50
            ):
                self.is_alive = False

    def draw(self, screen: pygame.Surface):
        """총알 객체와 트레일을 화면에 그립니다."""
        if self.is_alive:
            # 이미지가 아직 초기화되지 않았다면 폴백 렌더링
            if not hasattr(self, "image") or self.image is None:
                # 간단한 원으로 그리기 (폴백)
                pygame.draw.circle(
                    screen, (255, 0, 0), (int(self.pos.x), int(self.pos.y)), 20, 0
                )
                pygame.draw.circle(
                    screen, (255, 255, 0), (int(self.pos.x), int(self.pos.y)), 20, 3
                )
                return

            # 원근감 스케일 계산
            perspective_scale = self._calculate_perspective_scale(screen.get_height())

            # 원근감 적용된 이미지
            if (
                config.PERSPECTIVE_ENABLED
                and config.PERSPECTIVE_APPLY_TO_BULLETS
                and perspective_scale != 1.0
            ):
                scaled_image = pygame.transform.scale(
                    self.image,
                    (
                        int(self.image.get_width() * perspective_scale),
                        int(self.image.get_height() * perspective_scale),
                    ),
                )
                scaled_rect = scaled_image.get_rect(center=self.image_rect.center)
            else:
                scaled_image = self.image
                scaled_rect = self.image_rect

            # 트레일 그리기 (뒤에서부터 앞으로, 점점 투명하게)
            for i, trail_pos in enumerate(self.trail_positions):
                alpha = int(
                    255
                    * (i + 1)
                    / len(self.trail_positions)
                    * config.BULLET_TRAIL_ALPHA_DECAY
                )
                alpha = max(0, min(255, alpha))

                # 트레일용 반투명 서피스 생성
                trail_surf = scaled_image.copy()
                trail_surf.set_alpha(alpha)
                trail_rect = trail_surf.get_rect(
                    center=(int(trail_pos.x), int(trail_pos.y))
                )
                screen.blit(trail_surf, trail_rect)

            # 총알 본체 그리기
            screen.blit(scaled_image, scaled_rect)

    def _calculate_perspective_scale(self, screen_height: int) -> float:
        """Y 위치 기반 원근감 스케일 계산"""
        if not config.PERSPECTIVE_ENABLED or not config.PERSPECTIVE_APPLY_TO_BULLETS:
            return 1.0

        # Y 위치 비율 계산 (0.0 = 상단, 1.0 = 하단)
        depth_ratio = self.pos.y / screen_height
        depth_ratio = max(0.0, min(1.0, depth_ratio))

        # 스케일 계산
        scale = config.PERSPECTIVE_SCALE_MIN + (
            depth_ratio * (config.PERSPECTIVE_SCALE_MAX - config.PERSPECTIVE_SCALE_MIN)
        )
        return scale


class BurnProjectile:
    """보스가 발사하는 Burn 발사체 클래스 - 플레이어와 충돌 시 데미지"""

    def __init__(self, pos: pygame.math.Vector2, direction: pygame.math.Vector2):
        """
        Args:
            pos: 발사 위치 (보스 위치)
            direction: 발사 방향 (정규화된 벡터)
        """
        self.pos = pygame.math.Vector2(pos)
        self.direction = (
            direction.normalize()
            if direction.length_squared() > 0
            else pygame.math.Vector2(1, 0)
        )

        # 설정값 로드
        burn_settings = config.BOSS_PATTERN_SETTINGS["BURN_ATTACK"]
        self.speed = burn_settings["projectile_speed"]
        self.damage = burn_settings["damage"]
        self.lifetime = burn_settings["lifetime"]
        self.age = 0.0
        self.is_alive = True

        # 이미지 로드
        image_size = burn_settings["projectile_size"]
        try:
            self.image = AssetManager.get_image(
                config.ENEMY_SHIP_BURN_IMAGE_PATH, (image_size, image_size)
            )
        except Exception:
            # 이미지 로드 실패 시 기본 서피스 생성
            self.image = pygame.Surface((image_size, image_size), pygame.SRCALPHA)
            pygame.draw.circle(
                self.image,
                (255, 100, 50),
                (image_size // 2, image_size // 2),
                image_size // 2,
            )

        self.image_rect = self.image.get_rect(center=(int(self.pos.x), int(self.pos.y)))

        # 히트박스 (이미지보다 약간 작게)
        hitbox_size = int(image_size * 0.7)
        self.hitbox = pygame.Rect(0, 0, hitbox_size, hitbox_size)
        self.hitbox.center = (int(self.pos.x), int(self.pos.y))

    def update(self, dt: float, screen_size: tuple = None):
        """발사체 업데이트"""
        if not self.is_alive:
            return

        # 수명 체크
        self.age += dt
        if self.age >= self.lifetime:
            self.is_alive = False
            return

        # 이동
        self.pos += self.direction * self.speed * dt

        # 위치 업데이트
        self.image_rect.center = (int(self.pos.x), int(self.pos.y))
        self.hitbox.center = self.image_rect.center

        # 화면 밖으로 나가면 제거
        if screen_size:
            margin = 100
            if (
                self.pos.x < -margin
                or self.pos.x > screen_size[0] + margin
                or self.pos.y < -margin
                or self.pos.y > screen_size[1] + margin
            ):
                self.is_alive = False

    def draw(self, screen: pygame.Surface):
        """발사체 그리기"""
        if not self.is_alive:
            return

        # 회전 효과 (나이에 따라 회전)
        rotation_angle = self.age * 180  # 초당 180도 회전
        rotated_image = pygame.transform.rotate(self.image, rotation_angle)
        rotated_rect = rotated_image.get_rect(center=self.image_rect.center)

        screen.blit(rotated_image, rotated_rect)

    def check_collision_with_player(self, player) -> bool:
        """플레이어와 충돌 검사"""
        if not self.is_alive:
            return False
        # Player 클래스는 is_dead 속성 사용 (is_alive가 아님)
        if hasattr(player, "is_dead") and player.is_dead:
            return False

        return self.hitbox.colliderect(player.hitbox)
