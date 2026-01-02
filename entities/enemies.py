# entities/enemies.py
# 적 우주선 및 보스 클래스

import pygame
import math
import random
from typing import Tuple
import config
from asset_manager import AssetManager
from entities.weapons import BurnProjectile


class Enemy:
    """적 우주선 클래스"""

    def __init__(
        self,
        pos: pygame.math.Vector2,
        screen_height: int,
        chase_probability: float = 1.0,
        enemy_type: str = "NORMAL",
    ):

        # 0. 적 타입 설정
        self.enemy_type = enemy_type
        self.type_config = config.ENEMY_TYPES.get(
            enemy_type, config.ENEMY_TYPES["NORMAL"]
        )

        # 1. 위치 및 이동
        self.pos = pos
        self.speed = config.ENEMY_BASE_SPEED * self.type_config["speed_mult"]
        self.chase_probability = chase_probability  # 플레이어 추적 확률 (0.0 ~ 1.0)
        self.wander_direction = pygame.math.Vector2(
            random.uniform(-1, 1), random.uniform(-1, 1)
        ).normalize()
        self.wander_timer = 0.0
        self.wander_change_interval = 2.0  # 방황 방향 변경 간격 (초)

        # 2. 스탯 (타입 배율 적용)
        self.max_hp = config.ENEMY_BASE_HP * self.type_config["hp_mult"]
        self.hp = self.max_hp
        self.damage = config.ENEMY_ATTACK_DAMAGE * self.type_config["damage_mult"]
        self.last_attack_time = 0.0
        self.coin_multiplier = self.type_config["coin_mult"]  # 코인 드롭 배율

        # 3. 이미지 및 히트박스 (타입별 크기 적용)
        size_ratio = config.IMAGE_SIZE_RATIOS["ENEMY"]
        image_size = int(screen_height * size_ratio * self.type_config["size_mult"])

        # 이미지 로드 및 색상 tint 적용
        original_image = AssetManager.get_image(
            config.ENEMY_SHIP_IMAGE_PATH, (image_size, image_size)
        )
        self.color = self.type_config["color_tint"]  # 사망 효과용 색상 저장
        self.size = image_size // 2  # 사망 효과용 크기 저장 (반지름)
        self.image = self._apply_color_tint(original_image, self.color)
        self.image_rect = self.image.get_rect(center=(self.pos.x, self.pos.y))

        hitbox_size = int(image_size * config.ENEMY_HITBOX_RATIO)
        self.hitbox = pygame.Rect(0, 0, hitbox_size, hitbox_size)
        self.hitbox.center = (int(self.pos.x), int(self.pos.y))

        self.is_alive = True
        self.is_boss = False  # 보스 여부

        # 4. 히트 플래시 효과 속성
        self.hit_flash_timer = 0.0
        self.is_flashing = False
        self.original_image = self.image.copy()

        # 4-1. 플레이어 접촉 시 화상 이미지
        self.is_burning = False  # 플레이어와 접촉 중 여부
        # Burn 이미지를 10% 작게 표시
        burn_size = int(image_size * 0.9)
        burn_image = AssetManager.get_image(
            config.ENEMY_SHIP_BURN_IMAGE_PATH,
            (burn_size, burn_size),
        )
        # 화상 이미지는 불꽃 효과이므로 색상 tint를 적용하지 않음 (원본 그대로 사용)
        self.burn_image = burn_image

        # 5. 속성 스킬 상태 이펙트
        self.is_frozen = False  # 완전 동결 상태
        self.freeze_timer = 0.0
        self.is_slowed = False  # 슬로우 상태
        self.slow_timer = 0.0
        self.slow_ratio = 0.0  # 슬로우 비율 (0.0 ~ 1.0)
        self.base_speed = self.speed  # 기본 속도 저장

        # 6. 포위 공격용 고유 ID (해시값 사용)
        self.enemy_id = id(self)  # 객체의 고유 ID

        # 7. 타입별 특수 능력
        # SHIELDED: 재생 보호막
        self.has_shield = self.type_config.get("has_shield", False)
        self.shield_regen_rate = self.type_config.get("shield_regen_rate", 0.0)
        self.last_regen_time = 0.0

        # SUMMONER: 사망 시 소환
        self.summon_on_death = self.type_config.get("summon_on_death", False)
        self.summon_count = self.type_config.get("summon_count", 0)

        # KAMIKAZE: 자폭
        self.explode_on_contact = self.type_config.get("explode_on_contact", False)
        self.explosion_damage = self.type_config.get("explosion_damage", 0.0)
        self.explosion_radius = self.type_config.get("explosion_radius", 0)
        self.has_exploded = False  # 자폭 여부 (한 번만 폭발)

        # 8. 웨이브 전환 AI 모드
        self.is_respawned = self.type_config.get(
            "is_respawned", False
        )  # 리스폰 적 여부
        self.is_retreating = False  # 퇴각 모드 (기존 적)
        self.is_circling = False  # 회전 공격 모드 (빨간 적)
        self.circle_angle = random.uniform(0, 2 * math.pi)  # 회전 시작 각도 (랜덤)
        self.retreat_target = None  # 퇴각 목표 위치
        self.escaped = False  # 화면 밖으로 도망 성공 여부 (킬 카운트 제외용)

    def _apply_color_tint(
        self, image: pygame.Surface, tint_color: tuple
    ) -> pygame.Surface:
        """이미지에 색상 tint를 적용합니다."""
        if tint_color == (255, 255, 255):
            return image  # 원본 색상 그대로

        # 새 surface 생성 (알파 채널 유지)
        tinted = image.copy()

        # 색상 overlay 적용 (BLEND_RGB_MULT 대신 BLEND_RGBA_MULT 사용)
        color_overlay = pygame.Surface(image.get_size(), pygame.SRCALPHA)
        color_overlay.fill((*tint_color, 128))  # 반투명 색상
        tinted.blit(color_overlay, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

        return tinted

    def move_towards_player(
        self, player_pos: pygame.math.Vector2, dt: float, other_enemies: list = None
    ):
        """플레이어를 향해 이동하되, 다른 적들과 거리를 유지하고 포위 공격합니다."""

        direction = player_pos - self.pos
        distance_to_player = direction.length()

        if direction.length_squared() > 0:
            direction = direction.normalize()

            # 포위 공격: 플레이어 주변에 원형으로 분산
            flank_force = pygame.math.Vector2(0, 0)
            if (
                config.ENEMY_FLANK_ENABLED
                and distance_to_player < config.ENEMY_FLANK_DISTANCE
            ):
                # 적의 ID를 기반으로 목표 각도 계산 (각 적마다 고유한 각도)
                import math

                base_angle = (self.enemy_id % 360) * (math.pi / 180)  # ID 기반 각도

                # 플레이어 중심으로 목표 위치 계산
                target_offset_x = math.cos(base_angle) * config.ENEMY_FLANK_DISTANCE
                target_offset_y = math.sin(base_angle) * config.ENEMY_FLANK_DISTANCE
                target_pos = pygame.math.Vector2(
                    player_pos.x + target_offset_x, player_pos.y + target_offset_y
                )

                # 목표 위치로 이동하는 힘
                to_target = target_pos - self.pos
                if to_target.length_squared() > 0:
                    flank_force = to_target.normalize() * 0.5  # 포위 힘

            # 기본 추적 방향에 포위 힘 추가
            direction = direction + flank_force
            if direction.length_squared() > 0:
                direction = direction.normalize()

            # 분리 행동 (Separation): 다른 적들과 거리 유지 - 강화 버전
            separation_force = pygame.math.Vector2(0, 0)
            if other_enemies:
                # 보스는 더 큰 분리 반경 사용
                if hasattr(self, "is_boss") and self.is_boss:
                    separation_radius = (
                        config.ENEMY_SEPARATION_RADIUS * 3.0
                    )  # 보스는 3배
                    separation_strength = (
                        config.ENEMY_SEPARATION_STRENGTH * 2.0
                    )  # 보스는 2배 강도
                else:
                    separation_radius = config.ENEMY_SEPARATION_RADIUS
                    separation_strength = config.ENEMY_SEPARATION_STRENGTH

                separation_count = 0
                for other in other_enemies:
                    if other is not self and other.is_alive:
                        diff = self.pos - other.pos
                        distance = diff.length()

                        # 너무 가까우면 밀어내기
                        if 0 < distance < separation_radius:
                            # 거리에 반비례하는 힘 (가까울수록 강함)
                            # 제곱 반비례로 변경하여 가까울수록 훨씬 강하게
                            force_magnitude = (
                                (separation_radius - distance) / separation_radius
                            ) ** 2
                            if distance > 0:
                                diff_normalized = diff.normalize()
                                separation_force += diff_normalized * force_magnitude
                                separation_count += 1

                # 분리 힘 적용 (정규화하지 않고 강도만 곱함)
                if separation_force.length_squared() > 0:
                    # 여러 적과 겹칠수록 더 강한 분리 힘
                    separation_force = separation_force * separation_strength

            # 최종 이동 방향 = 플레이어 추적 + 분리 행동
            # 분리 힘이 강할 때는 추적보다 분리 우선
            separation_magnitude = separation_force.length()
            if separation_magnitude > 1.0:
                # 분리 힘이 강하면 추적 방향의 영향을 줄임
                direction_weight = max(0.3, 1.0 - (separation_magnitude * 0.3))
                final_direction = direction * direction_weight + separation_force
            else:
                final_direction = direction + separation_force

            if final_direction.length_squared() > 0:
                final_direction = final_direction.normalize()

            self.pos += final_direction * self.speed * dt

            # rect 및 hitbox 위치 업데이트
            self.image_rect.center = (int(self.pos.x), int(self.pos.y))
            self.hitbox.center = self.image_rect.center

    def take_damage(self, damage: float, player=None):
        """피해를 입습니다."""
        # Execute 스킬: 체력 임계값 이하 적 즉사
        if (
            player
            and hasattr(player, "execute_threshold")
            and player.execute_threshold > 0
        ):
            hp_ratio = self.hp / self.max_hp
            if hp_ratio <= player.execute_threshold:
                self.hp = 0
                self.is_alive = False
                return  # 즉시 종료

        self.hp -= damage
        if self.hp <= 0:
            self.is_alive = False
        else:
            # 히트 플래시 트리거
            self.hit_flash_timer = config.HIT_FLASH_DURATION
            self.is_flashing = True

    def attack(self, player: "Player", current_time: float) -> bool:
        """플레이어를 공격합니다. 공격 성공 시 True 반환"""
        if current_time - self.last_attack_time >= config.ENEMY_ATTACK_COOLDOWN:
            player.take_damage(self.damage)
            self.last_attack_time = current_time
            return True
        return False

    def update(
        self,
        player_pos: pygame.math.Vector2,
        dt: float,
        other_enemies: list = None,
        screen_size: tuple = None,
        current_time: float = 0.0,
    ):
        """적의 상태를 업데이트합니다."""
        if self.is_alive:
            # SHIELDED 타입: 보호막 재생
            if self.has_shield and self.hp < self.max_hp:
                regen_amount = self.max_hp * self.shield_regen_rate * dt
                self.hp = min(self.max_hp, self.hp + regen_amount)

            # 상태 이펙트 타이머 업데이트
            # 프리즈 상태 업데이트
            if self.is_frozen:
                self.freeze_timer -= dt
                if self.freeze_timer <= 0:
                    self.is_frozen = False
                # 프리즈 상태면 이동 안함
                return

            # 슬로우 상태 업데이트
            if self.is_slowed:
                self.slow_timer -= dt
                if self.slow_timer <= 0:
                    self.is_slowed = False
                    self.speed = self.base_speed  # 속도 복구

            # === 웨이브 전환 AI 모드 ===
            # 1. 퇴각 모드 (기존 적 - 외곽으로 이동)
            if self.is_retreating:
                self._retreat_to_edge(dt, screen_size)
                return

            # 2. 회전 공격 모드 (빨간 적 - 플레이어 주위 회전)
            if self.is_circling:
                self._circle_around_player(player_pos, dt)
                # 히트 플래시 업데이트 후 리턴
                if self.is_flashing:
                    self.hit_flash_timer -= dt
                    if self.hit_flash_timer <= 0:
                        self.is_flashing = False
                        self.image = self.original_image.copy()
                return

            # === 일반 AI 모드 ===
            # 추적 확률에 따라 플레이어를 추적할지 결정
            if random.random() < self.chase_probability:
                # 플레이어를 추적 (다른 적들 정보 전달)
                self.move_towards_player(player_pos, dt, other_enemies)
            else:
                # 방황 모드: 랜덤 방향으로 이동
                self.wander_timer += dt
                if self.wander_timer >= self.wander_change_interval:
                    # 새로운 랜덤 방향 설정
                    self.wander_direction = pygame.math.Vector2(
                        random.uniform(-1, 1), random.uniform(-1, 1)
                    ).normalize()
                    self.wander_timer = 0.0

                # 방황 방향으로 이동
                self.pos += (
                    self.wander_direction * self.speed * dt * 0.5
                )  # 방황 시 속도 50%
                self.image_rect.center = (int(self.pos.x), int(self.pos.y))
                self.hitbox.center = self.image_rect.center

            # 히트 플래시 타이머 업데이트
            if self.is_flashing:
                self.hit_flash_timer -= dt
                if self.hit_flash_timer <= 0:
                    self.is_flashing = False
                    self.image = self.original_image.copy()

    def _retreat_to_edge(self, dt: float, screen_size: tuple = None):
        """화면 상부로 서서히 퇴각"""
        if screen_size is None:
            screen_size = (1920, 1080)  # 기본값

        # 퇴각 목표: 항상 화면 상부 (현재 x 위치 유지)
        if self.retreat_target is None:
            margin = 100  # 화면 밖 여유
            self.retreat_target = pygame.math.Vector2(self.pos.x, -margin)

        # 목표를 향해 서서히 이동
        direction = self.retreat_target - self.pos
        distance = direction.length()

        if distance > 5:  # 아직 도착 안함
            direction = direction.normalize()
            # 서서히 이동 (속도 0.5배)
            self.pos += direction * self.speed * 0.5 * dt
            self.image_rect.center = (int(self.pos.x), int(self.pos.y))
            self.hitbox.center = self.image_rect.center
        else:
            # 화면 밖 도달 - 제거 대상으로 표시 (도망 성공)
            self.escaped = True  # 공격이 아닌 도망으로 사라짐
            self.is_alive = False

    def _circle_around_player(self, player_pos: pygame.math.Vector2, dt: float):
        """플레이어 주위 80픽셀에서 회전하며 공격 기회를 노림"""
        orbit_radius = 80  # 회전 반경
        orbit_speed = 2.0  # 회전 속도 (rad/s)

        # 회전 각도 업데이트
        self.circle_angle += orbit_speed * dt

        # 목표 위치 계산 (플레이어 주위 원형 궤도)
        target_x = player_pos.x + math.cos(self.circle_angle) * orbit_radius
        target_y = player_pos.y + math.sin(self.circle_angle) * orbit_radius
        target_pos = pygame.math.Vector2(target_x, target_y)

        # 현재 위치에서 목표 위치로 부드럽게 이동
        direction = target_pos - self.pos
        distance = direction.length()

        if distance > 1:
            # 빠르게 궤도로 진입, 궤도 도달 후 회전 유지
            move_speed = self.speed * 2 if distance > orbit_radius else self.speed
            direction = direction.normalize()
            self.pos += direction * move_speed * dt

        self.image_rect.center = (int(self.pos.x), int(self.pos.y))
        self.hitbox.center = self.image_rect.center

    def _calculate_perspective_scale(self, screen_height: int) -> float:
        """Y 위치 기반 원근감 스케일 계산"""
        if not config.PERSPECTIVE_ENABLED or not config.PERSPECTIVE_APPLY_TO_ENEMIES:
            return 1.0

        # Y 위치 비율 계산 (0.0 = 상단, 1.0 = 하단)
        depth_ratio = self.pos.y / screen_height
        depth_ratio = max(0.0, min(1.0, depth_ratio))  # 0~1 범위로 제한

        # 스케일 계산 (상단 = 작게, 하단 = 크게)
        scale = config.PERSPECTIVE_SCALE_MIN + (
            depth_ratio * (config.PERSPECTIVE_SCALE_MAX - config.PERSPECTIVE_SCALE_MIN)
        )
        return scale

    # ✅ [추가] 화면에 객체를 그리는 draw 메서드
    def draw(self, screen: pygame.Surface):
        """적 객체를 화면에 그리고 체력 바를 표시합니다."""
        # 원근감 스케일 계산
        perspective_scale = self._calculate_perspective_scale(screen.get_height())

        # 이미지 선택 우선순위: 화상 > 히트 플래시 > 동결 > 기본
        if self.is_burning:
            # 플레이어와 접촉 중 - 화상 이미지 사용
            current_image = self.burn_image
        elif self.is_flashing:
            # 피격 시 - 히트 플래시 (붉은색 가미)
            flash_surface = self.original_image.copy()
            flash_surface.fill(
                config.HIT_FLASH_COLOR, special_flags=pygame.BLEND_RGB_ADD
            )
            current_image = flash_surface
        elif self.is_frozen:
            # 동결 상태 - 흰색-푸른색 가미
            freeze_surface = self.original_image.copy()
            freeze_surface.fill(
                config.FREEZE_FLASH_COLOR, special_flags=pygame.BLEND_RGB_ADD
            )
            current_image = freeze_surface
        else:
            # 기본 이미지
            current_image = self.image

        # 원근감 적용된 이미지 생성
        if (
            config.PERSPECTIVE_ENABLED
            and config.PERSPECTIVE_APPLY_TO_ENEMIES
            and perspective_scale != 1.0
        ):
            scaled_image = pygame.transform.smoothscale(
                current_image,
                (
                    int(current_image.get_width() * perspective_scale),
                    int(current_image.get_height() * perspective_scale),
                ),
            )
            scaled_rect = scaled_image.get_rect(center=self.image_rect.center)
        else:
            scaled_image = current_image
            scaled_rect = self.image_rect

        # 상태 이펙트 시각 효과 (이미지 뒤에 광선 효과)
        if self.is_frozen:
            # 프리즈: 밝은 청백색 광선 효과
            self._draw_glow_effect(
                screen, (180, 220, 255), intensity=3, layers=3, scale=perspective_scale
            )
        elif self.is_slowed:
            # 슬로우: 파란색 광선 효과
            self._draw_glow_effect(
                screen, (100, 150, 255), intensity=2, layers=2, scale=perspective_scale
            )

        # 이미지 그리기
        screen.blit(scaled_image, scaled_rect)

        # 체력 바 그리기
        self.draw_health_bar(screen, perspective_scale)

    def draw_health_bar(self, screen: pygame.Surface, perspective_scale: float = 1.0):
        """적의 현재 체력을 이미지 위에 작은 바로 표시합니다."""

        # 체력 바를 이미지 너비의 35%로 축소 (1/2 크기, 원근감 스케일 적용)
        bar_width = int(self.image_rect.width * 0.35 * perspective_scale)
        bar_height = max(2, int(3 * perspective_scale))  # 최소 2픽셀
        # 체력 바를 이미지 상단 정중앙에 배치
        bar_x = self.image_rect.centerx - bar_width // 2
        # 이미지 상단에 바로 붙임 (이미지 내부 상단)
        bar_y = self.image_rect.top + 2

        # 배경 (검은색)
        pygame.draw.rect(screen, config.BLACK, (bar_x, bar_y, bar_width, bar_height))

        # 현재 체력 (초록색)
        health_ratio = self.hp / self.max_hp
        current_health_width = int(bar_width * health_ratio)
        pygame.draw.rect(
            screen, config.GREEN, (bar_x, bar_y, current_health_width, bar_height)
        )

    def _draw_glow_effect(
        self,
        screen: pygame.Surface,
        color: tuple,
        intensity: int = 2,
        layers: int = 2,
        scale: float = 1.0,
    ):
        """이미지 윤곽선 기반 광선 효과 (Glow Effect)"""
        # 이미지의 알파 채널을 이용한 마스크 생성
        try:
            # 이미지를 복사하여 마스크 생성
            glow_surface = pygame.Surface(self.image.get_size(), pygame.SRCALPHA)

            # 여러 레이어로 광선 효과 생성
            for layer in range(layers, 0, -1):
                # 각 레이어마다 크기와 투명도 조정
                scale_factor = 1.0 + (layer * intensity * 0.02)  # 2%씩 확대
                scale_factor *= scale  # 원근감 스케일 적용
                alpha = int(80 / layer)  # 레이어마다 투명도 감소

                # 확대된 이미지 생성
                scaled_size = (
                    int(self.image.get_width() * scale_factor),
                    int(self.image.get_height() * scale_factor),
                )
                scaled_image = pygame.transform.scale(self.image, scaled_size)

                # 색상 적용
                colored_surface = scaled_image.copy()
                colored_surface.fill(color + (0,), special_flags=pygame.BLEND_RGBA_MULT)
                colored_surface.fill(
                    (255, 255, 255, alpha), special_flags=pygame.BLEND_RGBA_MIN
                )

                # 중앙 정렬하여 그리기
                offset_x = (scaled_size[0] - self.image.get_width()) // 2
                offset_y = (scaled_size[1] - self.image.get_height()) // 2
                glow_rect = colored_surface.get_rect(center=self.image_rect.center)
                screen.blit(colored_surface, glow_rect)
        except:
            # 광선 효과 실패 시 원형 광선으로 폴백
            for layer in range(layers, 0, -1):
                radius = self.image_rect.width // 2 + layer * intensity
                alpha = int(60 / layer)

                glow_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(
                    glow_surf, color + (alpha,), (radius, radius), radius
                )
                glow_rect = glow_surf.get_rect(center=self.image_rect.center)
                screen.blit(glow_surf, glow_rect)


class Boss(Enemy):
    """보스 적 클래스 - Enemy를 상속받되 크기와 체력이 훨씬 큼"""

    def __init__(
        self,
        pos: pygame.math.Vector2,
        screen_height: int,
        boss_name: str = "Boss",
        wave_number: int = 5,
    ):
        # Enemy 초기화를 호출하되, 이미지 크기를 재설정하기 위해 super() 호출 전에 준비

        # 1. 위치 및 이동
        self.pos = pos
        self.speed = config.ENEMY_BASE_SPEED
        self.chase_probability = 1.0  # 보스는 항상 추적
        self.wander_direction = pygame.math.Vector2(0, 0)
        self.wander_timer = 0.0
        self.wander_change_interval = 2.0

        # 2. 스탯
        self.max_hp = config.ENEMY_BASE_HP
        self.hp = self.max_hp
        self.damage = config.ENEMY_ATTACK_DAMAGE
        self.last_attack_time = 0.0

        # 3. 보스 전용 속성
        self.is_boss = True
        self.boss_name = boss_name
        self.wave_number = wave_number

        # 4. 이미지 및 히트박스 (보스 이름에 따라 크기 다르게)
        if boss_name == "The Swarm Queen":
            size_multiplier = 2.0  # 웨이브 5 보스: 2배 크기
        elif boss_name == "The Void Core":
            size_multiplier = 5.0  # 웨이브 10 보스: 5배 크기
        else:
            size_multiplier = 3.0  # 기본 보스: 3배 크기

        size_ratio = config.IMAGE_SIZE_RATIOS["ENEMY"] * size_multiplier
        image_size = int(screen_height * size_ratio)

        self.color = (255, 50, 50)  # 보스 색상 (빨간색)
        self.size = image_size // 2  # 사망 효과용 크기 저장 (반지름)
        self.image = AssetManager.get_image(
            config.ENEMY_SHIP_IMAGE_PATH, (image_size, image_size)
        )
        self.image_rect = self.image.get_rect(center=(self.pos.x, self.pos.y))

        hitbox_size = int(image_size * config.ENEMY_HITBOX_RATIO)
        self.hitbox = pygame.Rect(0, 0, hitbox_size, hitbox_size)
        self.hitbox.center = (int(self.pos.x), int(self.pos.y))

        self.is_alive = True

        # 5. 히트 플래시 효과 속성 (Enemy에서도 있지만 이미지가 재설정되므로 다시 저장)
        self.hit_flash_timer = 0.0
        self.is_flashing = False
        self.original_image = self.image.copy()

        # 5-1. 플레이어 접촉 시 화상 이미지 (Boss도 Enemy처럼 동일하게 적용)
        self.is_burning = False
        # Burn 이미지를 10% 작게 표시
        burn_size = int(image_size * 0.9)
        burn_image = AssetManager.get_image(
            config.ENEMY_SHIP_BURN_IMAGE_PATH,
            (burn_size, burn_size),
        )
        self.burn_image = burn_image  # 보스는 색상 tint 없이 원본 사용

        # 6. 속성 스킬 상태 이펙트 (보스는 영향받지 않지만 속성은 필요)
        self.is_frozen = False
        self.freeze_timer = 0.0
        self.is_slowed = False
        self.slow_timer = 0.0
        self.slow_ratio = 0.0
        self.base_speed = self.speed

        # 7. 포위 공격용 고유 ID
        self.enemy_id = id(self)

        # 8. 보스 패턴 시스템
        self.current_phase = 0  # 현재 페이즈 (0, 1, 2)
        self.current_pattern = None  # 현재 실행 중인 패턴
        self.pattern_timer = 0.0  # 패턴 타이머

        # Circle Strafe 패턴
        self.orbit_angle = 0.0  # 현재 궤도 각도

        # Charge Attack 패턴
        self.is_charging = False
        self.charge_direction = pygame.math.Vector2(0, 0)
        self.last_charge_time = 0.0

        # Berserk 모드
        self.is_berserk = False

        # Summon 패턴
        self.last_summon_time = 0.0
        self.summoned_enemies = []  # 소환된 적 참조 리스트

        # Burn Attack 패턴
        self.last_burn_attack_time = 0.0
        self.burn_projectiles = []  # 발사된 burn 발사체 리스트

    def update(
        self,
        player_pos: pygame.math.Vector2,
        dt: float,
        other_enemies: list = None,
        screen_size: tuple = None,
        current_time: float = 0.0,
    ):
        """보스의 상태와 패턴을 업데이트합니다."""
        if not self.is_alive:
            return

        # 페이즈 체크 및 업데이트
        hp_ratio = self.hp / self.max_hp
        if hp_ratio <= 0.33 and self.current_phase < 2:
            self.current_phase = 2
        elif hp_ratio <= 0.66 and self.current_phase < 1:
            self.current_phase = 1

        # Berserk 모드 체크 (HP 25% 이하)
        if (
            hp_ratio <= config.BOSS_PATTERN_SETTINGS["BERSERK"]["hp_threshold"]
            and not self.is_berserk
        ):
            self.is_berserk = True
            self.speed = (
                self.base_speed * config.BOSS_PATTERN_SETTINGS["BERSERK"]["speed_mult"]
            )
            self.damage = (
                config.ENEMY_ATTACK_DAMAGE
                * config.BOSS_PATTERN_SETTINGS["BERSERK"]["damage_mult"]
            )

        # 패턴 타이머 업데이트
        self.pattern_timer += dt

        # 소환 패턴 (쿨다운 체크)
        if (
            current_time - self.last_summon_time
            >= config.BOSS_PATTERN_SETTINGS["SUMMON_MINIONS"]["summon_cooldown"]
        ):
            if random.random() < 0.3:  # 30% 확률로 소환 시도
                self._summon_minions(other_enemies)
                self.last_summon_time = current_time

        # 돌진 패턴 (쿨다운 체크)
        if (
            current_time - self.last_charge_time
            >= config.BOSS_PATTERN_SETTINGS["CHARGE_ATTACK"]["cooldown"]
        ):
            if random.random() < 0.4:  # 40% 확률로 돌진 시도
                self._start_charge(player_pos)
                self.last_charge_time = current_time

        # Burn 발사체 공격 패턴 (일정 주기로 발사)
        burn_settings = config.BOSS_PATTERN_SETTINGS["BURN_ATTACK"]
        if current_time - self.last_burn_attack_time >= burn_settings["fire_interval"]:
            self._fire_burn_projectiles()
            self.last_burn_attack_time = current_time

        # Burn 발사체 업데이트
        for proj in self.burn_projectiles[:]:
            proj.update(dt, screen_size)
            if not proj.is_alive:
                self.burn_projectiles.remove(proj)

        # 현재 패턴에 따라 이동
        if self.is_charging:
            self._update_charge(dt)
        elif self.current_pattern == "CIRCLE_STRAFE":
            self._update_circle_strafe(player_pos, dt)
        else:
            # 기본 추적 (Enemy의 move_towards_player 사용)
            super().move_towards_player(player_pos, dt, other_enemies)

        # 히트 플래시 타이머 업데이트
        if self.is_flashing:
            self.hit_flash_timer -= dt
            if self.hit_flash_timer <= 0:
                self.is_flashing = False
                self.image = self.original_image.copy()

    def _summon_minions(self, enemy_list: list):
        """미니언을 소환합니다."""
        if enemy_list is None:
            return

        summon_count = config.BOSS_PATTERN_SETTINGS["SUMMON_MINIONS"][
            "summon_count"
        ].get(self.wave_number, 2)
        minion_hp_ratio = config.BOSS_PATTERN_SETTINGS["SUMMON_MINIONS"][
            "minion_hp_ratio"
        ]

        for i in range(summon_count):
            # 보스 주변에 랜덤 위치 생성
            offset_x = random.uniform(-100, 100)
            offset_y = random.uniform(-100, 100)
            spawn_pos = pygame.math.Vector2(
                self.pos.x + offset_x, self.pos.y + offset_y
            )

            # 미니언 생성 (NORMAL 타입)
            # Note: Enemy class is defined in this same file
            minion = Enemy(
                spawn_pos, self.image_rect.height * 10, 1.0, "NORMAL"
            )  # screen_height 근사값
            minion.hp = self.max_hp * minion_hp_ratio
            minion.max_hp = minion.hp

            enemy_list.append(minion)
            self.summoned_enemies.append(minion)

    def _fire_burn_projectiles(self):
        """Burn 발사체를 사방으로 발사합니다."""
        burn_settings = config.BOSS_PATTERN_SETTINGS["BURN_ATTACK"]
        projectile_count = burn_settings["projectile_count"]

        # 사방으로 균등하게 발사 (원형 배치)
        for i in range(projectile_count):
            angle = (2 * math.pi / projectile_count) * i
            direction = pygame.math.Vector2(math.cos(angle), math.sin(angle))

            projectile = BurnProjectile(self.pos.copy(), direction)
            self.burn_projectiles.append(projectile)

    def draw_burn_projectiles(self, screen: pygame.Surface):
        """Burn 발사체들을 그립니다."""
        for proj in self.burn_projectiles:
            proj.draw(screen)

    def check_burn_collision_with_player(self, player) -> float:
        """모든 Burn 발사체와 플레이어의 충돌을 검사하고 총 데미지를 반환합니다."""
        total_damage = 0.0
        for proj in self.burn_projectiles[:]:
            if proj.check_collision_with_player(player):
                total_damage += proj.damage
                proj.is_alive = False  # 충돌한 발사체 제거
        return total_damage

    def _start_charge(self, player_pos: pygame.math.Vector2):
        """돌진 공격 시작."""
        self.is_charging = True
        direction = player_pos - self.pos
        if direction.length_squared() > 0:
            self.charge_direction = direction.normalize()
        self.pattern_timer = 0.0

    def _update_charge(self, dt: float):
        """돌진 공격 업데이트."""
        charge_duration = config.BOSS_PATTERN_SETTINGS["CHARGE_ATTACK"][
            "charge_duration"
        ]

        if self.pattern_timer >= charge_duration:
            self.is_charging = False
            return

        charge_speed = (
            self.base_speed
            * config.BOSS_PATTERN_SETTINGS["CHARGE_ATTACK"]["charge_speed_mult"]
        )
        self.pos += self.charge_direction * charge_speed * dt

        # 위치 및 hitbox 업데이트
        self.image_rect.center = (int(self.pos.x), int(self.pos.y))
        self.hitbox.center = self.image_rect.center

    def _update_circle_strafe(self, player_pos: pygame.math.Vector2, dt: float):
        """원형 궤도 이동 패턴."""
        orbit_radius = config.BOSS_PATTERN_SETTINGS["CIRCLE_STRAFE"]["orbit_radius"]
        orbit_speed = config.BOSS_PATTERN_SETTINGS["CIRCLE_STRAFE"]["orbit_speed"]

        # 각도 업데이트
        self.orbit_angle += orbit_speed * dt

        # 플레이어 주변 궤도 위치 계산
        target_x = player_pos.x + math.cos(self.orbit_angle) * orbit_radius
        target_y = player_pos.y + math.sin(self.orbit_angle) * orbit_radius
        target_pos = pygame.math.Vector2(target_x, target_y)

        # 목표 위치로 이동
        direction = target_pos - self.pos
        if direction.length_squared() > 0:
            direction = direction.normalize()
            self.pos += direction * self.speed * dt

        # 위치 및 hitbox 업데이트
        self.image_rect.center = (int(self.pos.x), int(self.pos.y))
        self.hitbox.center = self.image_rect.center

    def draw(self, screen: pygame.Surface):
        """보스를 화면에 그립니다. (크로마틱 어버레이션 효과 포함)"""
        # 이미지 선택 우선순위: 화상 > 히트 플래시 > 동결 > 기본
        if self.is_burning:
            # 플레이어와 접촉 중 - 화상 이미지 사용
            self.image = self.burn_image
        elif self.is_flashing:
            # 피격 시 - 히트 플래시 (붉은색 가미)
            flash_surface = self.original_image.copy()
            flash_surface.fill(
                config.HIT_FLASH_COLOR, special_flags=pygame.BLEND_RGB_ADD
            )
            self.image = flash_surface
        elif self.is_frozen:
            # 동결 상태 - 흰색-푸른색 가미
            freeze_surface = self.original_image.copy()
            freeze_surface.fill(
                config.FREEZE_FLASH_COLOR, special_flags=pygame.BLEND_RGB_ADD
            )
            self.image = freeze_surface

        # 크로마틱 어버레이션 효과 (RGB 분리) - 투명도 유지
        if config.CHROMATIC_ABERRATION_SETTINGS["BOSS"]["enabled"]:
            offset = config.CHROMATIC_ABERRATION_SETTINGS["BOSS"]["offset"]

            # 원본 이미지의 알파 채널 보존
            width, height = self.image.get_size()

            # 빨간 채널 이미지 생성 (투명도 유지)
            red_surface = self.image.copy()
            red_array = pygame.surfarray.pixels3d(red_surface)
            red_alpha = pygame.surfarray.pixels_alpha(red_surface)

            # Green, Blue 채널 제거
            red_array[:, :, 1] = 0
            red_array[:, :, 2] = 0

            # 알파 채널 유지하면서 전체 투명도 조정
            red_alpha[:] = (red_alpha[:] * 0.6).astype("uint8")  # 60% 투명도
            del red_array, red_alpha  # 배열 잠금 해제
            screen.blit(red_surface, (self.image_rect.x - offset, self.image_rect.y))

            # 파란 채널 이미지 생성 (투명도 유지)
            blue_surface = self.image.copy()
            blue_array = pygame.surfarray.pixels3d(blue_surface)
            blue_alpha = pygame.surfarray.pixels_alpha(blue_surface)

            # Red, Green 채널 제거
            blue_array[:, :, 0] = 0
            blue_array[:, :, 1] = 0

            # 알파 채널 유지하면서 전체 투명도 조정
            blue_alpha[:] = (blue_alpha[:] * 0.6).astype("uint8")  # 60% 투명도
            del blue_array, blue_alpha  # 배열 잠금 해제
            screen.blit(blue_surface, (self.image_rect.x + offset, self.image_rect.y))

        # 원본 이미지 (중앙)
        screen.blit(self.image, self.image_rect)

    def _draw_glow_effect(
        self, screen: pygame.Surface, color: tuple, intensity: int = 2, layers: int = 2
    ):
        """이미지 윤곽선 기반 광선 효과 (Glow Effect) - Boss용"""
        # 보스는 크로마틱 어버레이션이 있어 광선 효과 단순화
        for layer in range(layers, 0, -1):
            radius = self.image_rect.width // 2 + layer * intensity * 2
            alpha = int(60 / layer)

            glow_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, color + (alpha,), (radius, radius), radius)
            glow_rect = glow_surf.get_rect(center=self.image_rect.center)
            screen.blit(glow_surf, glow_rect)
