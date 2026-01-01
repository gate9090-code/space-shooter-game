# entities/collectibles.py
# 수집 가능한 아이템 클래스 (코인, 회복 아이템)

import pygame
from typing import Tuple, Dict
import config
from asset_manager import AssetManager


class CoinGem:
    """코인/젬 클래스 (적을 죽이면 드롭)"""

    COIN_AMOUNT = config.BASE_COIN_DROP_PER_KILL  # 코인 획득 시 점수

    def __init__(self, pos: Tuple[float, float], screen_height: int):

        # 1. 위치
        self.pos = pygame.math.Vector2(pos)

        # 2. 상태
        self.collected = False

        # 3. 이미지 및 히트박스
        size_ratio = config.IMAGE_SIZE_RATIOS["COINGEM"]
        image_size = int(screen_height * size_ratio)

        self.image = AssetManager.get_image(
            config.COIN_GEM_IMAGE_PATH, (image_size, image_size)
        )
        self.image_rect = self.image.get_rect(center=(self.pos.x, self.pos.y))

        hitbox_size = int(image_size * config.GEM_HITBOX_RATIO)
        self.hitbox = pygame.Rect(0, 0, hitbox_size, hitbox_size)
        self.hitbox.center = (int(self.pos.x), int(self.pos.y))

    def update(self, dt: float, player):
        """
        자석 효과가 있으면 플레이어에게 끌어당깁니다.
        """
        # 자석 효과 확인 (player에 has_coin_magnet 속성이 있다면)
        has_coin_magnet = getattr(player, "has_coin_magnet", False)

        if not self.collected and has_coin_magnet:
            # 플레이어와의 거리 계산
            direction = player.pos - self.pos
            distance = direction.length()

            # 자석 효과 범위 (플레이어 이미지 크기의 10배 정도로 가정)
            MAGNET_RANGE = player.image_rect.width * 10

            if distance < MAGNET_RANGE:
                # 플레이어에게 끌어당기는 속도 (거리와 비례)
                MAGNET_SPEED = 500.0
                if distance > 0:
                    direction = direction.normalize()
                    # 이동 속도를 dt와 MAGNET_SPEED로 계산
                    self.pos += direction * MAGNET_SPEED * dt
                    self.image_rect.center = (int(self.pos.x), int(self.pos.y))
                    self.hitbox.center = self.image_rect.center

    def collect(self, game_data: Dict) -> bool:
        """젬 수집 효과 적용 (점수 증가)"""
        if not self.collected:
            # 영구 코인과 레벨업 점수 모두 증가
            game_data["score"] += self.COIN_AMOUNT
            game_data["uncollected_score"] += self.COIN_AMOUNT
            self.collected = True
            return True
        return False

    def draw(self, screen: pygame.Surface):
        """젬 객체를 화면에 그립니다."""
        if not self.collected:
            # 원근감 스케일 계산
            perspective_scale = self._calculate_perspective_scale(screen.get_height())

            # 원근감 적용된 이미지
            if (
                config.PERSPECTIVE_ENABLED
                and config.PERSPECTIVE_APPLY_TO_GEMS
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
                screen.blit(scaled_image, scaled_rect)
            else:
                screen.blit(self.image, self.image_rect)

    def _calculate_perspective_scale(self, screen_height: int) -> float:
        """Y 위치 기반 원근감 스케일 계산"""
        if not config.PERSPECTIVE_ENABLED or not config.PERSPECTIVE_APPLY_TO_GEMS:
            return 1.0

        # Y 위치 비율 계산 (0.0 = 상단, 1.0 = 하단)
        depth_ratio = self.pos.y / screen_height
        depth_ratio = max(0.0, min(1.0, depth_ratio))

        # 스케일 계산
        scale = config.PERSPECTIVE_SCALE_MIN + (
            depth_ratio * (config.PERSPECTIVE_SCALE_MAX - config.PERSPECTIVE_SCALE_MIN)
        )
        return scale


class HealItem:
    """체력 회복 아이템 클래스"""

    HEAL_AMOUNT = config.HEAL_AMOUNT  # 회복량

    def __init__(self, pos: Tuple[float, float], screen_height: int):

        # 1. 위치
        self.pos = pygame.math.Vector2(pos)

        # 2. 상태
        self.collected = False

        # 3. 이미지 및 히트박스
        size_ratio = config.IMAGE_SIZE_RATIOS["GEMHP"]
        image_size = int(screen_height * size_ratio)

        self.image = AssetManager.get_image(
            config.GEM_HP_IMAGE_PATH, (image_size, image_size)
        )
        self.image_rect = self.image.get_rect(center=(self.pos.x, self.pos.y))

        hitbox_size = int(image_size * config.GEM_HITBOX_RATIO)
        self.hitbox = pygame.Rect(0, 0, hitbox_size, hitbox_size)
        self.hitbox.center = (int(self.pos.x), int(self.pos.y))

    def update(self, dt: float, player):
        """
        자석 효과가 있으면 플레이어에게 끌어당깁니다.
        """
        # 자석 효과 확인 (player에 has_coin_magnet 속성이 있다면)
        has_coin_magnet = getattr(player, "has_coin_magnet", False)

        if not self.collected and has_coin_magnet:
            # 플레이어와의 거리 계산
            direction = player.pos - self.pos
            distance = direction.length()

            # 자석 효과 범위 (플레이어 이미지 크기의 10배 정도로 가정)
            MAGNET_RANGE = player.image_rect.width * 10

            if distance < MAGNET_RANGE:
                # 플레이어에게 끌어당기는 속도 (거리와 비례)
                MAGNET_SPEED = 500.0
                if distance > 0:
                    direction = direction.normalize()
                    # 이동 속도를 dt와 MAGNET_SPEED로 계산
                    self.pos += direction * MAGNET_SPEED * dt
                    self.image_rect.center = (int(self.pos.x), int(self.pos.y))
                    self.hitbox.center = self.image_rect.center

    def collect(self, player) -> bool:
        """체력 회복 아이템 수집 효과 적용 (플레이어 HP 회복)"""
        if not self.collected:
            # 플레이어 체력 회복
            player.heal(self.HEAL_AMOUNT)
            self.collected = True
            return True
        return False

    def draw(self, screen: pygame.Surface):
        """젬 객체를 화면에 그립니다."""
        if not self.collected:
            screen.blit(self.image, self.image_rect)
