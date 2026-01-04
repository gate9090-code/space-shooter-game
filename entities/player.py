# entities/player.py
# 플레이어 우주선 클래스

import pygame
import math
import random
from typing import Tuple, List, Dict
import config
from asset_manager import AssetManager
from entities.weapons import Weapon


class Player:
    """플레이어 우주선 클래스"""

    def __init__(
        self,
        pos: pygame.math.Vector2,
        screen_height: int,
        upgrades: Dict[str, int],
        ship_type: str = None,
    ):
        # 0. 영구 업그레이드 저장
        self.upgrades = upgrades

        # 0-1. 함선 타입 설정
        self.ship_type = ship_type or config.DEFAULT_SHIP
        self.ship_data = config.SHIP_TYPES.get(
            self.ship_type, config.SHIP_TYPES[config.DEFAULT_SHIP]
        )
        self.ship_stats = self.ship_data["stats"]

        # 1. 위치 및 이동
        self.pos = pos
        self.base_speed = config.PLAYER_BASE_SPEED
        self.speed = self.base_speed  # 실제 이동 속도 (업그레이드 적용 후)

        # 2. 체력 스탯
        # 플레이어 초기 최대 체력 (영구 업그레이드 적용 전)
        self.initial_max_hp = config.PLAYER_BASE_HP

        # 영구 업그레이드를 기반으로 스탯 계산 (함선 배율 적용 포함)
        self.calculate_stats_from_upgrades()

        # 최대 체력 (전술 레벨업으로 증가 가능)
        self.max_hp = self.initial_max_hp

        # 현재 체력 (최대치로 시작)
        self.hp = self.max_hp

        # 사망 플래그 (HP가 0이 된 적 있으면 True, 부활 시 False로 리셋)
        self.is_dead = False

        # 3. 이미지 및 히트박스 (Titan 크기로 표준화)
        # Titan 기준 크기 (589x500) -> 화면 높이 14.52% 기준으로 계산 (21% 증가)
        standard_size = int(screen_height * 0.1452)  # Titan 크기 기준

        # 함선 이미지 로드 시도
        ship_image_path = (
            config.GAMEPLAY_DIR
            / "player"
            / self.ship_data.get("image", "fighter_front.png")
        )

        # 원본 이미지를 먼저 로드하여 종횡비 확인
        if ship_image_path.exists():
            try:
                original_img = pygame.image.load(str(ship_image_path)).convert_alpha()
                orig_width, orig_height = original_img.get_size()

                # 종횡비 유지하면서 높이를 standard_size로 맞춤
                aspect_ratio = orig_width / orig_height
                target_height = standard_size
                target_width = int(target_height * aspect_ratio)

                self.image = AssetManager.get_image(
                    ship_image_path, (target_width, target_height)
                )
            except Exception as e:
                print(f"WARNING: Failed to load ship image {ship_image_path}: {e}")
                # 기본 플레이어 이미지 사용
                self.image = AssetManager.get_image(
                    config.PLAYER_SHIP_IMAGE_PATH, (standard_size, standard_size)
                )
        else:
            # 기본 플레이어 이미지 사용
            self.image = AssetManager.get_image(
                config.PLAYER_SHIP_IMAGE_PATH, (standard_size, standard_size)
            )

        self.image_rect = self.image.get_rect(center=(self.pos.x, self.pos.y))

        # 히트박스는 이미지 높이 기준으로 설정
        hitbox_size = int(standard_size * config.PLAYER_HITBOX_RATIO)
        self.hitbox = pygame.Rect(0, 0, hitbox_size, hitbox_size)
        self.hitbox.center = (int(self.pos.x), int(self.pos.y))

        # 3-1. 전술 레벨업 속성 (무기)
        self.is_piercing = False  # 관통 속성

        # 3-2. 전술 레벨업 속성 (추가 속성)
        self.has_explosive = False  # 폭발 속성
        self.explosive_radius = 100.0  # 폭발 범위
        self.has_chain_explosion = False  # 연쇄 폭발
        self.has_lightning = False  # 번개 속성
        self.lightning_chain_count = 0  # 연쇄 횟수
        self.has_static_field = False  # 정전기장
        self.has_frost = False  # 빙결 속성
        self.frost_slow_ratio = 0.0  # 둔화 비율
        self.has_deep_freeze = False  # 심화 빙결
        self.freeze_chance = 0.0  # 빙결 확률

        # 3-3. 방어 속성
        self.damage_reduction = 0.0  # 피해 감소 비율
        self.regeneration_rate = 0.0  # 초당 HP 회복량
        self.last_regen_time = 0.0  # 마지막 회복 시간

        # 3-4. 유틸리티 속성
        self.coin_drop_multiplier = 1.0  # 코인 드롭 배율
        self.exp_multiplier = 1.0  # 경험치 배율
        self.has_coin_magnet = False  # 코인 자석 효과

        # 3-5. 지원 유닛 (동료 시스템)
        self.turret_count = 0  # 보유한 터렛 슬롯 수
        self.pending_turret_placements = 0  # 배치 대기 중인 터렛 수
        self.drone_count = 0  # 보유한 드론 수

        # 3-6. 획득한 스킬 추적 (스킬 이름: 획득 횟수)
        self.acquired_skills = {}

        # 3-7. 활성화된 시너지 추적 (시너지 효과 이름 리스트)
        self.active_synergies = []

        # 3-8. 스킬 활성화 타임 추적 (스킬 UI 표시용)
        self.skill_last_trigger = {
            "add_explosive": 0.0,
            "add_lightning": 0.0,
            "add_frost": 0.0,
        }

        # 3-9. 박테리아 달라붙기 시스템
        self.attached_bacteria_count = 0  # 현재 달라붙은 박테리아 수
        self.bacteria_speed_reduction = 0.0  # 박테리아로 인한 속도 감소 비율

        # 4. 무기 초기화 (함선 배율 + Workshop 업그레이드 적용)
        damage_mult = self.ship_stats.get("damage_mult", 1.0)
        cooldown_mult = self.ship_stats.get("cooldown_mult", 1.0)

        base_cooldown = config.WEAPON_COOLDOWN_BASE

        # 영구 쿨다운 업그레이드 적용
        cd_level = self.upgrades.get("COOLDOWN", 0)
        cd_reduction_ratio = config.PERMANENT_COOLDOWN_REDUCTION_RATIO * cd_level

        # Workshop FIRE_RATE: -10% cooldown per level
        fire_rate_level = self.upgrades.get("FIRE_RATE", 0)
        workshop_cd_reduction = 0.10 * fire_rate_level

        final_cooldown = (
            base_cooldown
            * (1 - cd_reduction_ratio - workshop_cd_reduction)
            * cooldown_mult
        )
        final_cooldown = max(0.05, final_cooldown)  # 최소 쿨다운 제한

        # 데미지 계산
        base_damage = config.BULLET_DAMAGE_BASE

        # Workshop DAMAGE: +8% per level
        damage_level = self.upgrades.get("DAMAGE", 0)
        if damage_level > 0:
            base_damage = base_damage * (1 + 0.08 * damage_level)

        # 무기 인스턴스 생성 (함선 데미지 배율 적용)
        self.weapon = Weapon(
            damage=int(base_damage * damage_mult),
            cooldown=final_cooldown,
            bullet_count=1,
            spread_angle=5.0,
        )

        # Workshop PIERCING: +1 penetration per level
        piercing_level = self.upgrades.get("PIERCING", 0)
        if piercing_level > 0:
            self.is_piercing = True

        # 5. 히트 플래시 효과 속성
        self.hit_flash_timer = 0.0  # 히트 플래시 타이머
        self.is_flashing = False  # 현재 플래시 중인지
        self.was_hit_recently = False  # 최근 피격 여부 (CombatMotionEffect용)

        # 6. 원본 이미지 저장 (히트 플래시용)
        self.original_image = self.image.copy()

        # 7. 궁극기 시스템 (Q 키)
        self.ultimate_type = "NOVA_BLAST"  # 기본 궁극기 타입
        self.ultimate_charge = config.ULTIMATE_SETTINGS[
            "charge_time"
        ]  # 궁극기 충전 타이머
        self.ultimate_cooldown_timer = 0.0  # 궁극기 쿨다운 타이머
        self.ultimate_active = False  # 궁극기 활성화 상태
        self.ultimate_timer = 0.0  # 궁극기 효과 지속 시간
        self.ultimate_effects = []  # 궁극기 시각 효과 리스트
        # Time Freeze용
        self.time_freeze_active = False
        self.time_freeze_timer = 0.0
        # Orbital Strike용
        self.orbital_strikes = []  # [(target_pos, delay, strike_timer), ...]
        self.orbital_strike_timer = 0.0

        # 9. 고급 스킬 속성 (Wave 11-15)
        self.execute_threshold = 0.0  # Execute: 즉사 체력 임계값 (0.2 = 20%)
        self.has_phoenix = False  # Phoenix Rebirth: 부활 스킬
        self.phoenix_cooldown = 0.0  # Phoenix 쿨다운 타이머 (120초)
        self.has_berserker = False  # Berserker: 저체력 시 공격력 증가
        self.has_starfall = False  # Starfall: 킬마다 별똥별 소환
        self.starfall_kill_counter = 0  # Starfall 킬 카운터
        self.has_arcane_mastery = False  # Arcane Mastery: 모든 속성 효과 +50%
        self.second_chance_rate = 0.0  # Second Chance: 치명타 회피 확률

        # 10. 이동 효과 시스템
        self.velocity = pygame.math.Vector2(0, 0)  # 현재 이동 속도 벡터
        self.trail_particles = (
            []
        )  # 이동 트레일 파티클 [(pos, lifetime, color, size), ...]
        self.afterimages = []  # 잔상 효과 [(image, pos, alpha, lifetime), ...]
        self.last_trail_spawn = 0.0  # 마지막 트레일 생성 시간
        self.trail_spawn_interval = 0.02  # 트레일 생성 간격 (초)
        self.disable_afterimages = False  # 잔상 비활성화 플래그 (공성 모드용)
        self.disable_trail = False  # 트레일 비활성화 플래그 (승리 애니메이션용)

        # 10-2. 배기가스 이미지 로드
        self._load_gas_effect_image()

        # 10-1. 이동 방향 기울기(틸트) 시스템
        self.current_tilt = 0.0  # 현재 기울기 각도 (도)
        self.target_tilt = 0.0  # 목표 기울기 각도 (도)
        self.tilt_speed = 8.0  # 기울기 보간 속도 (클수록 빠르게 기울어짐)
        self.max_tilt_angle = 15.0  # 최대 기울기 각도 (도)
        self.tilt_return_speed = 5.0  # 원위치 복귀 속도

        # 11. 함선 특수 능력 시스템 (E 키)
        self.ship_ability_type = self.ship_data.get("special")  # 함선 특수 능력 타입
        self.ship_ability_cooldown = 0.0  # 능력 쿨다운 타이머
        self.ship_ability_active = False  # 능력 활성화 상태
        self.ship_ability_timer = 0.0  # 능력 지속 시간

        # 함선별 능력 초기화
        self._init_ship_ability()

        # 12. 마우스 이동 시스템
        self.mouse_target = None  # 마우스 클릭 목표 위치 (Vector2 또는 None)
        self.mouse_move_speed_mult = 1.0  # 마우스 이동 속도 배율
        self.mouse_arrival_threshold = 10.0  # 목표 도달 판정 거리 (px)

    def _init_ship_ability(self):
        """함선별 특수 능력 초기화"""
        ability = self.ship_ability_type

        # INTERCEPTOR: Evasion Boost (2초 무적 대시)
        self.evasion_active = False
        self.evasion_duration = 2.0
        self.evasion_cooldown_max = 15.0

        # BOMBER: Bomb Drop (AoE 폭탄)
        self.bomb_damage = 500
        self.bomb_radius = 200
        self.bomb_cooldown_max = 10.0

        # STEALTH: Cloaking (3초 은신)
        self.cloak_active = False
        self.cloak_duration = 3.0
        self.cloak_cooldown_max = 20.0
        self.cloak_alpha = 255  # 은신 시 투명도

        # TITAN: Shield (피해 흡수)
        self.shield_active = False
        self.shield_hp = 0
        self.shield_max_hp = 0
        self.shield_absorption = 0.30  # 30% 피해 흡수
        self.shield_cooldown_max = 25.0
        self.shield_duration = 8.0

        # Titan 함선일 경우 실드 최대치 설정
        if self.ship_type == "TITAN":
            self.shield_max_hp = int(self.max_hp * 0.5)  # 최대 HP의 50%

    def _load_gas_effect_image(self):
        """배기가스 이미지 로드 (함선별)"""
        try:
            # 함선별 배기가스 효과 파일명 가져오기
            exhaust_filename = self.ship_data.get("exhaust_effect", "gas_effect_01.png")
            gas_effect_path = config.ASSET_DIR / "images" / "effects" / exhaust_filename

            if gas_effect_path.exists():
                # 원본 이미지 로드 (크기 조정 없이)
                self.gas_effect_image = pygame.image.load(str(gas_effect_path)).convert_alpha()
                print(f"INFO: Gas effect image loaded for {self.ship_type}: {exhaust_filename}")
            else:
                print(f"WARNING: Gas effect image not found: {gas_effect_path}")
                self.gas_effect_image = None
        except Exception as e:
            print(f"WARNING: Failed to load gas effect image: {e}")
            self.gas_effect_image = None

    def calculate_stats_from_upgrades(self):
        """영구 업그레이드 레벨을 기반으로 플레이어 스탯을 계산합니다. (함선 배율 + Workshop 업그레이드 적용)"""

        # 함선 배율 가져오기
        hp_mult = self.ship_stats.get("hp_mult", 1.0)
        speed_mult = self.ship_stats.get("speed_mult", 1.0)

        # === 기존 영구 업그레이드 (상점) ===
        # 최대 HP 계산 (기존 레벨 시스템)
        hp_level = self.upgrades.get("MAX_HP", 1)
        hp_bonus = config.PERMANENT_MAX_HP_BONUS_AMOUNT * (hp_level - 1)
        base_hp = config.PLAYER_BASE_HP + hp_bonus

        # === Workshop 업그레이드 적용 ===
        # Workshop MAX_HP: +10% per level
        workshop_hp_level = self.upgrades.get("MAX_HP", 0)
        if workshop_hp_level > 0:
            base_hp = base_hp * (1 + 0.10 * workshop_hp_level)

        # 함선 배율 적용
        self.initial_max_hp = int(base_hp * hp_mult)

        # 이동 속도 계산
        speed_level = self.upgrades.get("SPEED", 0)
        speed_bonus = config.PERMANENT_SPEED_BONUS_AMOUNT * speed_level
        base_speed = self.base_speed + speed_bonus

        # Workshop SPEED: +5% per level
        workshop_speed_level = self.upgrades.get("SPEED", 0)
        if workshop_speed_level > 0:
            base_speed = base_speed * (1 + 0.05 * workshop_speed_level)

        # 함선 배율 적용
        self.speed = base_speed * speed_mult

        # === Workshop 스킬 적용 ===
        # Chain Lightning
        if self.upgrades.get("CHAIN_LIGHTNING", 0) > 0:
            self.has_lightning = True
            self.lightning_chain_count = 3

        # Explosive Rounds
        if self.upgrades.get("EXPLOSIVE_ROUNDS", 0) > 0:
            self.has_explosive = True

        # Freeze Shot
        if self.upgrades.get("FREEZE_SHOT", 0) > 0:
            self.has_frost = True
            self.frost_slow_ratio = 0.5

        # Execute
        if self.upgrades.get("EXECUTE", 0) > 0:
            self.execute_threshold = 0.15  # 15% HP 이하 즉사

        # Phoenix Rebirth
        if self.upgrades.get("PHOENIX", 0) > 0:
            self.has_phoenix = True

        # Coin Magnet
        if self.upgrades.get("COIN_MAGNET", 0) > 0:
            self.has_coin_magnet = True

        # Coin Multiplier
        if self.upgrades.get("COIN_MULT", 0) > 0:
            self.coin_drop_multiplier = 1.5

        # HP Regeneration
        if self.upgrades.get("HP_REGEN", 0) > 0:
            self.regeneration_rate = 2.0  # 초당 2 HP 회복

        # Defense (-3% per level)
        defense_level = self.upgrades.get("DEFENSE", 0)
        if defense_level > 0:
            self.damage_reduction = 0.03 * defense_level

    def update_bacteria_attachment(self, bacteria_count: int):
        """박테리아 달라붙기 업데이트

        Args:
            bacteria_count: 현재 달라붙은 박테리아 수
        """
        self.attached_bacteria_count = bacteria_count

        # 박테리아 수에 따른 속도 감소 (1개당 10% 감소, 최대 90%)
        if bacteria_count > 0:
            self.bacteria_speed_reduction = min(0.10 * bacteria_count, 0.90)
        else:
            self.bacteria_speed_reduction = 0.0

    def get_effective_speed(self) -> float:
        """박테리아 속도 감소를 반영한 실제 이동 속도 반환

        Returns:
            현재 적용되어야 하는 실제 속도
        """
        return self.speed * (1.0 - self.bacteria_speed_reduction)

    def move(
        self,
        keys: Dict,
        dt: float,
        screen_size: Tuple[int, int],
        current_time: float = 0.0,
        game_data: Dict = None,
    ):
        """키 입력 또는 마우스 클릭 목표를 기반으로 플레이어를 이동시키고 이동 효과를 생성합니다."""

        # 이동 벡터 초기화
        velocity = pygame.math.Vector2(0, 0)

        # 키보드 입력에 따라 속도 설정
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            velocity.x = -1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            velocity.x = 1
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            velocity.y = -1
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            velocity.y = 1

        # 키보드 입력이 있으면 마우스 타겟 취소
        if velocity.length_squared() > 0:
            self.mouse_target = None

        # 마우스 이동 목표가 있고 키보드 입력이 없으면 마우스 이동
        if self.mouse_target is not None and velocity.length_squared() == 0:
            to_target = self.mouse_target - self.pos
            dist = to_target.length()

            if dist > self.mouse_arrival_threshold:
                # 목표 방향으로 이동
                velocity = to_target.normalize()
            else:
                # 목표에 도달 - 타겟 클리어
                self.mouse_target = None

        # 보스 웨이브 속도 버프 계산 (20% 증가)
        speed_multiplier = 1.0
        if game_data and game_data.get("current_wave") in config.BOSS_WAVES:
            speed_multiplier = 1.2  # 보스 웨이브에서 20% 속도 증가

        # 대각선 이동 시 속도 보정 (정규화)
        if velocity.length_squared() > 0:
            # 박테리아 속도 감소 적용
            base_speed = self.get_effective_speed()
            effective_speed = base_speed * speed_multiplier * self.mouse_move_speed_mult
            velocity = velocity.normalize() * effective_speed * dt
            self.velocity = velocity / dt  # 초당 속도 벡터 저장
            self.pos += velocity

            # 이동 효과 생성 (속도에 따라) - 파티클 기법 비활성화, 직접 렌더링 방식으로 변경
            # self._create_movement_effects(current_time)

            # 고속 이동 시 잔상 효과만 유지
            speed_magnitude = self.velocity.length()
            speed_ratio = speed_magnitude / self.speed if self.speed > 0 else 0
            if speed_ratio > 0.7 and not self.disable_afterimages:
                # 잔상 생성 (투명도 있는 플레이어 이미지)
                afterimage = self.image.copy()
                alpha = int(100 * speed_ratio)
                afterimage.set_alpha(alpha)

                # 잔상에 현재 기울기 적용
                if abs(self.current_tilt) > 0.5:
                    afterimage = pygame.transform.rotate(afterimage, self.current_tilt)

                self.afterimages.append({
                    "image": afterimage,
                    "pos": self.pos.copy(),
                    "alpha": alpha,
                    "lifetime": 0.15,
                    "max_lifetime": 0.15,
                })
        else:
            self.velocity = pygame.math.Vector2(0, 0)

        # 화면 경계 제한
        SCREEN_WIDTH, SCREEN_HEIGHT = screen_size
        half_width = self.image_rect.width / 2
        half_height = self.image_rect.height / 2

        self.pos.x = max(half_width, min(self.pos.x, SCREEN_WIDTH - half_width))
        self.pos.y = max(half_height, min(self.pos.y, SCREEN_HEIGHT - half_height))

        # rect 및 hitbox 위치 업데이트
        self.image_rect.center = (int(self.pos.x), int(self.pos.y))
        self.hitbox.center = self.image_rect.center

    def set_mouse_target(self, pos: Tuple[int, int]):
        """마우스 클릭 위치를 이동 목표로 설정합니다."""
        self.mouse_target = pygame.math.Vector2(pos[0], pos[1])

    def clear_mouse_target(self):
        """마우스 이동 목표를 취소합니다."""
        self.mouse_target = None

    # =========================================================
    # 마우스 우클릭 공격 시스템 (가까운 적 타겟팅)
    # =========================================================
    def find_nearest_enemy(self, enemies: list) -> object:
        """
        가장 가까운 적을 찾아 반환합니다.

        Args:
            enemies: 적 객체 리스트

        Returns:
            가장 가까운 적 객체 또는 None
        """
        if not enemies:
            return None

        closest_enemy = None
        closest_dist = float("inf")

        for enemy in enemies:
            if not hasattr(enemy, "pos"):
                continue
            dist = (enemy.pos - self.pos).length()
            if dist < closest_dist:
                closest_dist = dist
                closest_enemy = enemy

        return closest_enemy

    def get_direction_to_enemy(self, enemy) -> pygame.math.Vector2:
        """
        적 방향으로의 단위 벡터를 반환합니다.

        Args:
            enemy: 적 객체

        Returns:
            적 방향 단위 벡터 또는 (0, -1) (위쪽)
        """
        if enemy is None or not hasattr(enemy, "pos"):
            return pygame.math.Vector2(0, -1)  # 기본: 위쪽

        to_enemy = enemy.pos - self.pos
        if to_enemy.length() > 0:
            return to_enemy.normalize()
        return pygame.math.Vector2(0, -1)

    '''
    def _create_movement_effects(self, current_time: float):
        """이동 속도와 방향에 따른 시각 효과 생성"""
        import random

        # 속도에 따른 효과 강도 계산
        speed_magnitude = self.velocity.length()
        speed_ratio = speed_magnitude / self.speed  # 0.0 ~ 1.0+

        # 최소 속도 임계값 (너무 느리면 효과 안 나옴)
        if speed_ratio < 0.3:
            return

        # 트레일 생성 주기 체크
        if current_time - self.last_trail_spawn < self.trail_spawn_interval:
            return

        self.last_trail_spawn = current_time

        # 이동 방향의 반대로 파티클 생성
        if self.velocity.length_squared() > 0:
            direction = self.velocity.normalize()
            # 플레이어 뒤쪽에서 파티클 생성
            offset = -direction * (self.image_rect.width * 0.3)
            spawn_pos = self.pos + offset

            # 속도에 따른 파티클 수 (빠를수록 많이)
            particle_count = int(2 + speed_ratio * 3)

            for _ in range(particle_count):
                # 약간의 랜덤 분산 (좌우로 더 퍼지도록)
                spread = pygame.math.Vector2(
                    random.uniform(-15, 15),
                    random.uniform(-8, 8)
                )
                particle_pos = spawn_pos + spread

                # 속도에 따른 색상 틴트 (이미지에 적용)
                if speed_ratio < 0.4:
                    color_tint = (150, 150, 160)  # 연한 회색
                elif speed_ratio < 0.7:
                    color_tint = (255, 180, 120)  # 주황빛
                elif speed_ratio < 0.9:
                    color_tint = (255, 200, 140)  # 밝은 오렌지-노랑
                else:
                    color_tint = (255, 255, 255)  # 최고속: 원본 색상

                # 파티클 크기 (스케일)
                base_scale = 0.8 + speed_ratio * 1.2
                scale = base_scale + random.uniform(-0.2, 0.3)
                scale = max(0.5, scale)

                # 파티클 수명 (더 길게)
                lifetime = 0.5 + speed_ratio * 0.6

                # 회전 각도 (랜덤)
                rotation = random.uniform(0, 360)

                self.trail_particles.append({
                    'pos': particle_pos.copy(),
                    'lifetime': lifetime,
                    'max_lifetime': lifetime,
                    'color_tint': color_tint,
                    'scale': scale,
                    'rotation': rotation,
                    'use_image': self.gas_effect_image is not None,  # 이미지 사용 여부
                    'velocity': pygame.math.Vector2(
                        random.uniform(-30, 30),
                        random.uniform(-15, 15)
                    )  # 확산 속도
                })

        # 고속 이동 시 잔상 효과 추가
        if speed_ratio > 0.5:
            # 잔상 생성 (투명도 있는 플레이어 이미지)
            afterimage = self.image.copy()

            # 🌟 청록색 플라즈마 필터 추가
            PLASMA_COLOR = (100, 255, 255)
            afterimage.fill(PLASMA_COLOR, special_flags=pygame.BLEND_RGB_MULT)


            alpha = int(150 * speed_ratio)  # 속도에 따라 투명도 조절
            afterimage.set_alpha(min(alpha, 255)) # 255 초과 방지
            afterimage.set_alpha(alpha)

            # 잔상에 현재 기울기 적용
            if abs(self.current_tilt) > 0.5:
                afterimage = pygame.transform.rotate(afterimage, self.current_tilt)

            self.afterimages.append({
                'image': afterimage,
                'pos': self.pos.copy(),
                'alpha': alpha,
                'lifetime': 0.3,  # 잔상 지속 시간
                'max_lifetime': 0.3
            })
            '''

    def _create_movement_effects(self, current_time: float):
        """이동 속도와 방향에 따른 시각 효과 생성"""
        import random

        # 속도에 따른 효과 강도 계산
        speed_magnitude = self.velocity.length()
        speed_ratio = speed_magnitude / self.speed  # 0.0 ~ 1.0+

        # 최소 속도 임계값 (너무 느리면 효과 안 나옴)
        if speed_ratio < 0.3:
            return

        # 트레일 생성 주기 체크
        if current_time - self.last_trail_spawn < self.trail_spawn_interval:
            return

        self.last_trail_spawn = current_time

        # 이동 방향의 반대로 파티클 생성
        if self.velocity.length_squared() > 0:
            direction = self.velocity.normalize()
            # 플레이어 뒤쪽에서 파티클 생성
            offset = -direction * (self.image_rect.width * 0.3)
            spawn_pos = self.pos + offset

            # 속도에 따른 파티클 수 (빠를수록 많이)
            particle_count = int(2 + speed_ratio * 3)

            for _ in range(particle_count):
                # 약간의 랜덤 분산
                spread = pygame.math.Vector2(
                    random.uniform(-10, 10), random.uniform(-10, 10)
                )
            particle_pos = spawn_pos + spread

        if speed_ratio < 0.5:
            color = (100, 150, 255)  # 파란색
        elif speed_ratio < 0.8:
            color = (150, 200, 255)  # 하늘색
        else:
            color = (255, 215, 0)  # 주황색

            # 속도에 따른 파티클 크기
            size = int(3 + speed_ratio * 5)

            # 파티클 수명 (속도가 빠를수록 길게)
            lifetime = 0.3 + speed_ratio * 0.3

            self.trail_particles.append(
                {
                    "pos": particle_pos.copy(),
                    "lifetime": lifetime,
                    "max_lifetime": lifetime,
                    "color": color,
                    "size": size,
                }
            )

            # 고속 이동 시 잔상 효과 추가 (공성 모드에서는 비활성화)
            if speed_ratio > 0.7 and not self.disable_afterimages:
                # 잔상 생성 (투명도 있는 플레이어 이미지)
                afterimage = self.image.copy()
                alpha = int(100 * speed_ratio)  # 속도에 따라 투명도 조절
                afterimage.set_alpha(alpha)

                # 잔상에 현재 기울기 적용
                if abs(self.current_tilt) > 0.5:
                    afterimage = pygame.transform.rotate(afterimage, self.current_tilt)

                self.afterimages.append(
                    {
                        "image": afterimage,
                        "pos": self.pos.copy(),
                        "alpha": alpha,
                        "lifetime": 0.15,  # 잔상 지속 시간
                        "max_lifetime": 0.15,
                    }
                )

    def activate_ultimate(self, enemies: List):
        """궁극기를 발동합니다 (Q 키)

        Args:
            enemies: 현재 적 리스트

        Returns:
            bool: 궁극기 발동 성공 여부
        """
        # 충전 확인
        if self.ultimate_charge < config.ULTIMATE_SETTINGS["charge_time"]:
            return False

        # 쿨다운 확인
        if self.ultimate_cooldown_timer > 0:
            return False

        # 궁극기 타입별 효과 발동
        if self.ultimate_type == "NOVA_BLAST":
            self._activate_nova_blast(enemies)
        elif self.ultimate_type == "TIME_FREEZE":
            self._activate_time_freeze(enemies)
        elif self.ultimate_type == "ORBITAL_STRIKE":
            self._activate_orbital_strike(enemies)

        # 쿨다운 시작
        self.ultimate_cooldown_timer = config.ULTIMATE_SETTINGS["cooldown"]
        self.ultimate_charge = 0.0

        print(f"INFO: Ultimate '{self.ultimate_type}' activated!")
        return True

    def _activate_nova_blast(self, enemies: List):
        """Nova Blast 궁극기 - 주변 대규모 폭발"""
        settings = config.ULTIMATE_SETTINGS["NOVA_BLAST"]

        # 폭발 효과 추가
        self.ultimate_effects.append(
            {
                "type": "NOVA_BLAST",
                "pos": self.pos.copy(),
                "radius": 0,
                "max_radius": settings["radius"],
                "timer": settings["duration"],
                "color": settings["color"],
            }
        )

        # 범위 내 모든 적에게 데미지 및 넉백
        for enemy in enemies:
            dist = (enemy.pos - self.pos).length()
            if dist <= settings["radius"]:
                # 데미지 적용
                enemy.take_damage(settings["damage"])

                # 넉백 적용
                if dist > 0:
                    knockback_dir = (enemy.pos - self.pos).normalize()
                    enemy.pos += (
                        knockback_dir
                        * settings["knockback"]
                        * (1 - dist / settings["radius"])
                    )

    def _activate_time_freeze(self, enemies: List):
        """Time Freeze 궁극기 - 모든 적 시간 정지"""
        settings = config.ULTIMATE_SETTINGS["TIME_FREEZE"]

        self.time_freeze_active = True
        self.time_freeze_timer = settings["duration"]

    def _activate_orbital_strike(self, enemies: List):
        """Orbital Strike 궁극기 - 레이저 공격"""
        settings = config.ULTIMATE_SETTINGS["ORBITAL_STRIKE"]

        # 모든 적 위치에 레이저 타겟 설정
        import random

        targets = []
        for i in range(min(settings["strike_count"], len(enemies) * 2)):
            if enemies:
                target_enemy = random.choice(enemies)
                targets.append(
                    {
                        "pos": target_enemy.pos.copy(),
                        "delay": i * settings["strike_interval"],
                        "timer": 0.0,
                        "active": False,
                    }
                )

        self.orbital_strikes = targets
        self.orbital_strike_timer = 0.0

    def take_damage(self, damage: float):
        """플레이어가 피해를 입습니다."""
        # 이미 사망 상태면 추가 데미지 무시
        if self.hp <= 0:
            return

        # Second Chance 스킬: 치명타 회피 (사망 직전에만 발동)
        if hasattr(self, "second_chance_rate") and self.second_chance_rate > 0:
            would_die = (self.hp - damage * (1.0 - self.damage_reduction)) <= 0
            if would_die and random.random() < self.second_chance_rate:
                print(f"INFO: Second Chance! Dodged lethal damage!")
                return  # 피해 무시

        # 피해 감소 적용
        actual_damage = damage * (1.0 - self.damage_reduction)
        self.hp -= actual_damage
        self.hp = max(0, self.hp)

        # 사망 시 플래그 설정
        if self.hp <= 0:
            self.is_dead = True

        # 히트 플래시 트리거
        self.hit_flash_timer = config.HIT_FLASH_DURATION
        self.is_flashing = True

        # 피격 플래그 설정 (CombatMotionEffect 이동 시간 리셋용)
        self.was_hit_recently = True

    def heal(self, amount: float):
        """플레이어의 체력을 회복합니다."""
        # 사망 상태면 회복하지 않음 (게임 오버 상태)
        if self.is_dead or self.hp <= 0:
            return
        self.hp += amount
        self.hp = min(self.hp, self.max_hp)

    def increase_max_hp(self, amount: int):
        """최대 체력을 증가시키고 현재 체력을 비례적으로 조정합니다."""
        if amount <= 0:
            return

        # HP가 0 이하면 max_hp만 증가 (게임 오버 상태에서는 회복 안 함)
        if self.hp <= 0:
            self.max_hp += amount
            print(
                f"INFO: Max HP increased to {self.max_hp}, HP remains at 0 (game over state)"
            )
            return

        # 현재 체력 비율 유지
        health_ratio = self.hp / self.max_hp if self.max_hp > 0 else 1.0

        # 최대 체력 증가
        self.max_hp += amount

        # 현재 체력을 비례적으로 증가 (체력 비율 유지)
        self.hp = self.max_hp * health_ratio

        print(f"INFO: Max HP increased to {self.max_hp}, current HP: {self.hp}")

    def increase_speed(self, amount: int):
        """이동 속도를 증가시킵니다."""
        if amount <= 0:
            return
        self.speed += amount
        print(f"INFO: Speed increased to {self.speed}")

    def add_damage_reduction(self, ratio: float):
        """피해 감소 비율을 추가합니다."""
        if ratio <= 0:
            return
        self.damage_reduction = min(0.75, self.damage_reduction + ratio)  # 최대 75%
        print(f"INFO: Damage reduction: {self.damage_reduction * 100:.0f}%")

    def add_regeneration(self, rate: float):
        """초당 체력 회복량을 추가합니다."""
        if rate <= 0:
            return
        self.regeneration_rate += rate
        print(f"INFO: Regeneration rate: {self.regeneration_rate} HP/s")

    def update_regeneration(self, current_time: float):
        """시간에 따라 체력을 회복합니다."""
        # 사망 상태면 회복하지 않음 (게임 오버 상태)
        if self.is_dead or self.hp <= 0:
            return
        if self.regeneration_rate > 0 and self.hp < self.max_hp:
            # 1초마다 회복
            if current_time - self.last_regen_time >= 1.0:
                self.heal(self.regeneration_rate)
                self.last_regen_time = current_time

    def update(self, dt: float, screen_size: Tuple[int, int], current_time: float):
        """플레이어 상태를 업데이트합니다."""
        # 무기 쿨타임 업데이트
        self.weapon.update(dt)

        # 체력 재생 업데이트
        self.update_regeneration(current_time)

        # 히트 플래시 타이머 업데이트
        if self.is_flashing:
            self.hit_flash_timer -= dt
            if self.hit_flash_timer <= 0:
                self.is_flashing = False
                self.image = self.original_image.copy()

        # 궁극기 충전 타이머 업데이트
        if self.ultimate_charge < config.ULTIMATE_SETTINGS["charge_time"]:
            self.ultimate_charge += dt
            self.ultimate_charge = min(
                self.ultimate_charge, config.ULTIMATE_SETTINGS["charge_time"]
            )

        # 궁극기 쿨다운 타이머 업데이트
        if self.ultimate_cooldown_timer > 0:
            self.ultimate_cooldown_timer -= dt
            self.ultimate_cooldown_timer = max(0, self.ultimate_cooldown_timer)

        # Time Freeze 효과 타이머
        if self.time_freeze_active:
            self.time_freeze_timer -= dt
            if self.time_freeze_timer <= 0:
                self.time_freeze_active = False
                self.time_freeze_timer = 0.0

        # Orbital Strike 타이머 업데이트
        if self.orbital_strikes:
            self.orbital_strike_timer += dt
            for strike in self.orbital_strikes:
                if (
                    not strike["active"]
                    and self.orbital_strike_timer >= strike["delay"]
                ):
                    strike["active"] = True
                    strike["timer"] = config.ULTIMATE_SETTINGS["ORBITAL_STRIKE"][
                        "beam_duration"
                    ]

                if strike["active"]:
                    strike["timer"] -= dt

            # 완료된 스트라이크 제거
            self.orbital_strikes = [
                s for s in self.orbital_strikes if s["timer"] > 0 or not s["active"]
            ]

        # 궁극기 시각 효과 업데이트
        for effect in self.ultimate_effects:
            effect["timer"] -= dt
            if effect["type"] == "NOVA_BLAST":
                # 폭발 반경 확장
                progress = 1 - (
                    effect["timer"] / config.ULTIMATE_SETTINGS["NOVA_BLAST"]["duration"]
                )
                effect["radius"] = effect["max_radius"] * progress

        # 완료된 효과 제거
        self.ultimate_effects = [e for e in self.ultimate_effects if e["timer"] > 0]

        # 함선 특수 능력 업데이트
        self._update_ship_ability(dt)

        # 이동 방향 기울기(틸트) 업데이트
        self._update_tilt(dt)

    def _update_tilt(self, dt: float):
        """이동 방향에 따른 기울기 업데이트"""
        # 속도 벡터가 있으면 기울기 목표 계산
        if self.velocity.length() > 0.1:
            # 좌우 이동에 따른 기울기 (X축 속도 기반)
            horizontal_ratio = self.velocity.x / self.speed if self.speed > 0 else 0
            # 최대 기울기 각도로 클램핑
            self.target_tilt = -horizontal_ratio * self.max_tilt_angle

            # 추가: 위/아래 이동 시 약간의 피치 효과 (선택적)
            # vertical_ratio = self.velocity.y / self.speed if self.speed > 0 else 0
            # 위로 이동 시 약간 앞으로 기울기 효과는 2D에서 표현하기 어려우므로 생략
        else:
            # 이동하지 않으면 원위치로 복귀
            self.target_tilt = 0.0

        # 부드러운 보간 (현재 기울기 → 목표 기울기)
        tilt_diff = self.target_tilt - self.current_tilt

        if abs(tilt_diff) > 0.1:
            # 이동 중일 때는 빠르게, 정지 시에는 천천히 복귀
            if self.velocity.length() > 0.1:
                interpolation_speed = self.tilt_speed
            else:
                interpolation_speed = self.tilt_return_speed

            self.current_tilt += tilt_diff * interpolation_speed * dt
        else:
            self.current_tilt = self.target_tilt

        # 각도 클램핑
        self.current_tilt = max(
            -self.max_tilt_angle, min(self.max_tilt_angle, self.current_tilt)
        )

    def _update_ship_ability(self, dt: float):
        """함선 특수 능력 상태 업데이트"""
        # 쿨다운 감소
        if self.ship_ability_cooldown > 0:
            self.ship_ability_cooldown -= dt
            self.ship_ability_cooldown = max(0, self.ship_ability_cooldown)

        # 능력 활성화 시 타이머 감소
        if self.ship_ability_active:
            self.ship_ability_timer -= dt

            # INTERCEPTOR: Evasion Boost
            if self.ship_ability_type == "evasion_boost":
                if self.ship_ability_timer <= 0:
                    self.evasion_active = False
                    self.ship_ability_active = False
                    self.ship_ability_cooldown = self.evasion_cooldown_max
                    print("INFO: Evasion Boost ended")

            # STEALTH: Cloaking
            elif self.ship_ability_type == "cloaking":
                if self.ship_ability_timer <= 0:
                    self.cloak_active = False
                    self.ship_ability_active = False
                    self.ship_ability_cooldown = self.cloak_cooldown_max
                    self.cloak_alpha = 255
                    print("INFO: Cloaking ended")
                else:
                    # 은신 중 투명도 조절 (깜빡임 효과)
                    import math

                    flicker = 0.3 + 0.2 * math.sin(self.ship_ability_timer * 10)
                    self.cloak_alpha = int(255 * flicker)

            # TITAN: Shield
            elif self.ship_ability_type == "shield":
                if self.ship_ability_timer <= 0 or self.shield_hp <= 0:
                    self.shield_active = False
                    self.ship_ability_active = False
                    self.ship_ability_cooldown = self.shield_cooldown_max
                    print("INFO: Shield ended")

    def use_ship_ability(self, enemies: list = None, effects: list = None) -> bool:
        """함선 특수 능력 사용 (E 키)"""
        # 쿨다운 중이면 사용 불가
        if self.ship_ability_cooldown > 0:
            return False

        # 능력이 없으면 사용 불가
        if self.ship_ability_type is None:
            return False

        # 이미 활성화 중이면 사용 불가
        if self.ship_ability_active:
            return False

        print(f"INFO: Using ship ability: {self.ship_ability_type}")

        # INTERCEPTOR: Evasion Boost (2초 무적 대시)
        if self.ship_ability_type == "evasion_boost":
            self.evasion_active = True
            self.ship_ability_active = True
            self.ship_ability_timer = self.evasion_duration
            # 속도 일시적으로 2배 증가
            self.speed *= 2.0
            return True

        # BOMBER: Bomb Drop (AoE 폭탄) - 즉시 발동
        elif self.ship_ability_type == "bomb_drop":
            self.ship_ability_cooldown = self.bomb_cooldown_max
            # 폭탄 효과 생성 (effects 리스트에 추가)
            if effects is not None:
                bomb_effect = {
                    "type": "bomb_drop",
                    "pos": self.pos.copy(),
                    "radius": self.bomb_radius,
                    "damage": self.bomb_damage,
                    "timer": 0.5,  # 폭발 지속 시간
                    "max_timer": 0.5,
                }
                effects.append(bomb_effect)
            # 범위 내 적에게 피해
            if enemies:
                for enemy in enemies:
                    dist = (enemy.pos - self.pos).length()
                    if dist <= self.bomb_radius:
                        # 거리에 따른 데미지 감소
                        damage_ratio = 1.0 - (dist / self.bomb_radius) * 0.5
                        enemy.take_damage(int(self.bomb_damage * damage_ratio))
            return True

        # STEALTH: Cloaking (3초 은신)
        elif self.ship_ability_type == "cloaking":
            self.cloak_active = True
            self.ship_ability_active = True
            self.ship_ability_timer = self.cloak_duration
            return True

        # TITAN: Shield (피해 흡수)
        elif self.ship_ability_type == "shield":
            self.shield_active = True
            self.shield_hp = self.shield_max_hp
            self.ship_ability_active = True
            self.ship_ability_timer = self.shield_duration
            return True

        return False

    def get_ship_ability_info(self) -> dict:
        """함선 특수 능력 정보 반환 (UI 표시용)"""
        if self.ship_ability_type is None:
            return {"name": "None", "ready": False, "cooldown": 0, "max_cooldown": 0}

        ability_names = {
            "evasion_boost": "Evasion Boost",
            "bomb_drop": "Bomb Drop",
            "cloaking": "Cloaking",
            "shield": "Shield",
        }

        max_cooldowns = {
            "evasion_boost": self.evasion_cooldown_max,
            "bomb_drop": self.bomb_cooldown_max,
            "cloaking": self.cloak_cooldown_max,
            "shield": self.shield_cooldown_max,
        }

        return {
            "name": ability_names.get(self.ship_ability_type, "Unknown"),
            "ready": self.ship_ability_cooldown <= 0 and not self.ship_ability_active,
            "active": self.ship_ability_active,
            "cooldown": self.ship_ability_cooldown,
            "max_cooldown": max_cooldowns.get(self.ship_ability_type, 10.0),
            "timer": self.ship_ability_timer if self.ship_ability_active else 0,
        }

    def is_invulnerable(self) -> bool:
        """무적 상태 확인 (Evasion Boost 또는 Cloaking)"""
        return self.evasion_active or self.cloak_active

    def take_damage_with_shield(self, damage: float) -> float:
        """실드 적용 후 실제 피해량 반환"""
        if self.shield_active and self.shield_hp > 0:
            # 실드로 흡수할 피해량
            absorbed = int(damage * self.shield_absorption)
            self.shield_hp -= absorbed
            if self.shield_hp < 0:
                self.shield_hp = 0
            return damage - absorbed
        return damage

    def update_movement_effects(self, dt: float):
        """이동 효과 업데이트 (파티클 트레일과 잔상)"""
        # 트레일 파티클 업데이트
        for particle in self.trail_particles[:]:
            particle["lifetime"] -= dt
            if particle["lifetime"] <= 0:
                self.trail_particles.remove(particle)
            else:
                # 확산 효과 적용 (배기가스가 퍼짐)
                if 'velocity' in particle:
                    particle['pos'] += particle['velocity'] * dt
                    # 속도 감소 (마찰)
                    particle['velocity'] *= 0.95

        # 잔상 업데이트
        for afterimage in self.afterimages[:]:
            afterimage["lifetime"] -= dt
            if afterimage["lifetime"] <= 0:
                self.afterimages.remove(afterimage)
            else:
                # 페이드 아웃 효과
                fade_ratio = afterimage["lifetime"] / afterimage["max_lifetime"]
                afterimage["image"].set_alpha(int(afterimage["alpha"] * fade_ratio))

    def _calculate_perspective_scale(self, screen_height: int) -> float:
        """Y 위치 기반 원근감 스케일 계산"""
        if not config.PERSPECTIVE_ENABLED or not config.PERSPECTIVE_APPLY_TO_PLAYER:
            return 1.0

        # Y 위치 비율 계산 (0.0 = 상단, 1.0 = 하단)
        depth_ratio = self.pos.y / screen_height
        depth_ratio = max(0.0, min(1.0, depth_ratio))

        # 스케일 계산
        scale = config.PERSPECTIVE_SCALE_MIN + (
            depth_ratio * (config.PERSPECTIVE_SCALE_MAX - config.PERSPECTIVE_SCALE_MIN)
        )
        return scale

    def draw(self, screen: pygame.Surface):
        """플레이어 객체를 화면에 그립니다."""
        # 원근감 스케일 계산
        perspective_scale = self._calculate_perspective_scale(screen.get_height())

        # 1. 잔상 효과 그리기 (플레이어 뒤에)
        for afterimage in self.afterimages:
            # 잔상에도 원근감 적용
            if (
                config.PERSPECTIVE_ENABLED
                and config.PERSPECTIVE_APPLY_TO_PLAYER
                and perspective_scale != 1.0
            ):
                afterimage_scale = self._calculate_perspective_scale(
                    screen.get_height()
                )
                scaled_afterimage = pygame.transform.smoothscale(
                    afterimage["image"],
                    (
                        int(afterimage["image"].get_width() * afterimage_scale),
                        int(afterimage["image"].get_height() * afterimage_scale),
                    ),
                )
                rect = scaled_afterimage.get_rect(
                    center=(int(afterimage["pos"].x), int(afterimage["pos"].y))
                )
                screen.blit(scaled_afterimage, rect)
            else:
                rect = afterimage["image"].get_rect(
                    center=(int(afterimage["pos"].x), int(afterimage["pos"].y))
                )
                screen.blit(afterimage["image"], rect)

        # 2. 배기가스 이미지 직접 그리기 (플레이어 뒤, 타원 궤도 기반)
        if self.gas_effect_image and not self.disable_trail:
            # 속도 계산
            speed = self.velocity.length()
            max_speed = self.speed * 1.5  # 최대 속도 추정
            speed_ratio = min(1.0, speed / max_speed) if max_speed > 0 else 0

            # 최소 속도 체크 (낮은 속도에서도 배기가스 표시)
            if speed_ratio > 0.1:
                # 이동 방향 계산
                if self.velocity.length_squared() > 0:
                    direction = self.velocity.normalize()

                    # 이동 방향 각도 계산
                    move_angle = math.atan2(direction.y, direction.x)

                    # 우주선 뒤쪽 타원 궤도의 가장자리 지점 계산
                    # 타원: 가로(a) = 우주선 너비의 25%, 세로(b) = 우주선 높이의 15%
                    ellipse_a = self.image_rect.width * 0.25  # 가로 반지름 (줄임)
                    ellipse_b = self.image_rect.height * 0.15  # 세로 반지름 (줄임)

                    # 이동 방향의 반대쪽 타원 경계 지점 (배기가스 시작점)
                    # 반대 방향이므로 angle + π
                    back_angle = move_angle + math.pi
                    ellipse_x = ellipse_a * math.cos(back_angle)
                    ellipse_y = ellipse_b * math.sin(back_angle)

                    # 배기가스 시작 위치 (우주선 중심 + 타원 경계)
                    # 우주선 바로 뒤에 배치 (배율 감소: 1.5 → 0.8)
                    exhaust_offset = pygame.math.Vector2(ellipse_x, ellipse_y) * 0.8
                    exhaust_base_pos = self.pos + exhaust_offset

                    # 배기가스 타입에 따라 다른 크기 및 크롭 설정
                    exhaust_filename = self.ship_data.get("exhaust_effect", "gas_effect_01.png")

                    # 원본 이미지 크롭 (속도에 따라)
                    orig_height = self.gas_effect_image.get_height()
                    orig_width = self.gas_effect_image.get_width()

                    if "gas_effect_02" in exhaust_filename:
                        # 플라즈마: 크기 축소, 머리부분(밝은 부분) 잘라냄
                        gas_length = int(self.image_rect.height * (0.3 + speed_ratio * 0.8) * perspective_scale)  # 길이 축소
                        gas_width = int(self.image_rect.width * 0.5 * perspective_scale)  # 너비 축소

                        # 하단 40% 잘라내기 (60-80% 구간의 밝은 부분 제거)
                        # 180도 회전 후 밝은 부분이 우주선 쪽으로 가는 것을 방지
                        crop_start = 0
                        crop_height = int(orig_height * 0.6)  # 상단 60%만 사용
                    else:
                        # 화염: 더 넓게, 블러 효과 위해 너비 증가
                        gas_length = int(self.image_rect.height * (0.4 + speed_ratio * 1.2) * perspective_scale)
                        gas_width = int(self.image_rect.width * 1.0 * perspective_scale)  # 0.6 → 1.0 (넓게)

                        # 상단 20% 잘라내기 (꼬리 부분, 배기가스 적은 곳 제거)
                        # 하단 80%만 사용 (밝은 배기가스 부분만)
                        crop_start = int(orig_height * 0.2)
                        crop_height = orig_height - crop_start

                    if crop_height > 0:
                        # 크롭된 부분만 추출
                        cropped_gas = self.gas_effect_image.subsurface(
                            pygame.Rect(0, crop_start, orig_width, crop_height)
                        ).copy()

                        # 스케일 (크롭된 이미지를 목표 크기로)
                        scaled_gas = pygame.transform.smoothscale(
                            cropped_gas,
                            (gas_width, gas_length)
                        )

                        # 타입별 투명도 조절
                        if "gas_effect_02" in exhaust_filename:
                            # 플라즈마: 약간 더 투명하게
                            alpha = int(60 + speed_ratio * 120)  # 60 ~ 180
                        else:
                            # 화염: 블러 효과를 위해 더 투명하게
                            alpha = int(50 + speed_ratio * 100)  # 50 ~ 150 (더 투명)

                        scaled_gas.set_alpha(alpha)

                        # 이미지를 180도 회전 (밝은 부분이 우주선 쪽으로)
                        scaled_gas = pygame.transform.rotate(scaled_gas, 180)

                        # 회전 (이동 방향에 맞춤)
                        # 배기가스는 항상 우주선 반대 방향을 향해야 함
                        angle_deg = math.degrees(move_angle) + 90  # 이동 방향의 반대 방향
                        rotated_gas = pygame.transform.rotate(scaled_gas, -angle_deg)

                        # 배기가스 최종 위치 계산
                        # 회전된 이미지의 한쪽 끝(밝은 부분)이 우주선 엔진 출구에 오도록 조정
                        rotated_rect = rotated_gas.get_rect()

                        # 배기가스 이미지 타입에 따라 다른 오프셋 적용
                        # gas_effect_01 (화염): 상단 20% 잘림, 밝은 부분만 사용
                        # gas_effect_02 (플라즈마): 하단 40% 잘림, 어두운 꼬리 부분만 사용
                        if "gas_effect_02" in exhaust_filename:
                            offset_ratio = 0.25  # 플라즈마: 밝은 부분 제거로 감소
                        else:
                            offset_ratio = 0.4  # 화염: 상단 잘림으로 감소 (0.5 → 0.4)

                        offset_distance = gas_length * offset_ratio
                        final_offset = pygame.math.Vector2(
                            -direction.x * offset_distance,
                            -direction.y * offset_distance
                        )
                        exhaust_pos = exhaust_base_pos + final_offset

                        # 화면에 그리기
                        rect = rotated_gas.get_rect(center=(int(exhaust_pos.x), int(exhaust_pos.y)))
                        screen.blit(rotated_gas, rect)

        # 3. 그릴 이미지 결정 (히트 플래시 적용 + 능력 효과)
        if self.is_flashing:
            # 피격 시 - 붉은색 가미
            flash_surface = self.original_image.copy()
            flash_surface.fill(
                config.HIT_FLASH_COLOR, special_flags=pygame.BLEND_RGB_ADD
            )
            draw_image = flash_surface
        elif getattr(self, "cloak_active", False):
            # 클로킹: 반투명 + 보라색 틴트
            cloak_surface = self.image.copy()
            cloak_surface.set_alpha(80)  # 반투명
            # 보라색 틴트
            tint_surface = pygame.Surface(cloak_surface.get_size(), pygame.SRCALPHA)
            tint_surface.fill((100, 50, 150, 50))
            cloak_surface.blit(
                tint_surface, (0, 0), special_flags=pygame.BLEND_RGBA_ADD
            )
            draw_image = cloak_surface
        elif getattr(self, "evasion_active", False):
            # 회피 부스트: 노란색 글로우
            evasion_surface = self.image.copy()
            glow_surface = pygame.Surface(evasion_surface.get_size(), pygame.SRCALPHA)
            glow_surface.fill((255, 255, 100, 60))
            evasion_surface.blit(
                glow_surface, (0, 0), special_flags=pygame.BLEND_RGBA_ADD
            )
            draw_image = evasion_surface
        else:
            draw_image = self.image

        # 3-1. 이동 방향 기울기(틸트) 적용
        if abs(self.current_tilt) > 0.5:
            # 이미지 회전 (기울기 각도 적용)
            draw_image = pygame.transform.rotate(draw_image, self.current_tilt)

        # 4. 플레이어 이미지 그리기 (원근감 + 틸트 적용)
        if (
            config.PERSPECTIVE_ENABLED
            and config.PERSPECTIVE_APPLY_TO_PLAYER
            and perspective_scale != 1.0
        ):
            scaled_image = pygame.transform.smoothscale(
                draw_image,
                (
                    int(draw_image.get_width() * perspective_scale),
                    int(draw_image.get_height() * perspective_scale),
                ),
            )
            scaled_rect = scaled_image.get_rect(center=self.image_rect.center)
            screen.blit(scaled_image, scaled_rect)
        else:
            # 기울기가 있을 경우 중심점 유지
            draw_rect = draw_image.get_rect(center=self.image_rect.center)
            screen.blit(draw_image, draw_rect)

        # 5. 궁극기 시각 효과 렌더링
        for effect in self.ultimate_effects:
            if effect["type"] == "NOVA_BLAST":
                # 확장하는 원형 폭발 이펙트
                pygame.draw.circle(
                    screen,
                    effect["color"],
                    (int(effect["pos"].x), int(effect["pos"].y)),
                    int(effect["radius"]),
                    5,
                )

        # 6. Time Freeze 화면 틴트
        if self.time_freeze_active:
            settings = config.ULTIMATE_SETTINGS["TIME_FREEZE"]
            tint = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
            tint.fill(settings["screen_tint"])
            screen.blit(tint, (0, 0))

        # 7. Orbital Strike 레이저 렌더링
        for strike in self.orbital_strikes:
            if strike["active"] and strike["timer"] > 0:
                settings = config.ULTIMATE_SETTINGS["ORBITAL_STRIKE"]
                # 레이저 빔 (빨간 원)
                pygame.draw.circle(
                    screen,
                    settings["color"],
                    (int(strike["pos"].x), int(strike["pos"].y)),
                    settings["strike_radius"],
                    3,
                )
                # 내부 빛나는 효과
                pygame.draw.circle(
                    screen,
                    (255, 200, 200),
                    (int(strike["pos"].x), int(strike["pos"].y)),
                    settings["strike_radius"] // 2,
                )

        # 8. Ship Ability: Shield 시각 효과
        if getattr(self, "shield_active", False):
            shield_hp = getattr(self, "shield_hp", 0)
            shield_max = getattr(self, "shield_max_hp", 1)
            shield_ratio = shield_hp / shield_max if shield_max > 0 else 0

            # 보호막 반지름 (플레이어 크기 기반)
            shield_radius = int(
                max(self.image.get_width(), self.image.get_height()) * 0.8
            )

            # 펄스 효과 (시간에 따라 크기 변화)
            pulse = 1.0 + 0.05 * math.sin(pygame.time.get_ticks() * 0.01)
            shield_radius = int(shield_radius * pulse)

            # 쉴드 색상 (HP에 따라 변화)
            if shield_ratio > 0.5:
                shield_color = (100, 180, 255)  # 파랑
            elif shield_ratio > 0.25:
                shield_color = (255, 200, 100)  # 노랑
            else:
                shield_color = (255, 100, 100)  # 빨강

            # 외곽 원 (두꺼운 테두리)
            pygame.draw.circle(
                screen,
                shield_color,
                (int(self.pos.x), int(self.pos.y)),
                shield_radius,
                4,
            )

            # 내부 반투명 원
            shield_surface = pygame.Surface(
                (shield_radius * 2, shield_radius * 2), pygame.SRCALPHA
            )
            pygame.draw.circle(
                shield_surface,
                (*shield_color, 40),
                (shield_radius, shield_radius),
                shield_radius,
            )
            screen.blit(
                shield_surface,
                (int(self.pos.x) - shield_radius, int(self.pos.y) - shield_radius),
            )
