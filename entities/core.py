'''
Core game entities - Player, Enemy, Boss, Weapon, Bullet
Extracted from objects.py
'''
import pygame
import math
from typing import List, Dict, Tuple, Optional
from pathlib import Path
import config
from asset_manager import AssetManager
import random


# ============================================================
# Weapon
# ============================================================

# =========================================================
# 0. Weapon 클래스 (무기 로직)
# =========================================================
class Weapon:
    def __init__(self, damage: float, cooldown: float, bullet_count: int, spread_angle: float = 5.0):
        self.damage = damage
        self.cooldown = cooldown
        self.bullet_count = bullet_count
        self.spread_angle = spread_angle
        self.time_since_last_shot = 0.0 # 발사 쿨타임 추적

    def update(self, dt: float):
        """무기의 쿨타임을 업데이트합니다."""
        self.time_since_last_shot += dt

    def can_shoot(self) -> bool:
        """현재 발사 가능한지 확인합니다."""
        return self.time_since_last_shot >= self.cooldown

    def fire(self, start_pos: pygame.math.Vector2, target_pos: pygame.math.Vector2, bullets: List, piercing_state: bool, player=None):
        """
        지정된 목표 위치로 총알을 발사합니다.
        """
        if not self.can_shoot():
            return

        self.time_since_last_shot = 0.0 # 쿨타임 초기화

        # 목표 방향 벡터 계산
        direction = target_pos - start_pos
        base_angle = math.atan2(direction.y, direction.x)

        # Berserker 스킬: 저체력 시 데미지 2배
        bullet_damage = self.damage
        if player and hasattr(player, 'has_berserker') and player.has_berserker:
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
            bullet_direction = pygame.math.Vector2(math.cos(new_angle), math.sin(new_angle)).normalize()

            # 새 총알 객체 생성 및 리스트에 추가
            bullet = Bullet(
                start_pos.copy(),
                bullet_direction,
                bullet_damage,
                piercing_state # 피어싱 상태를 Bullet에 전달
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


# ============================================================
# Player
# ============================================================

# 2. 플레이어 클래스
# =========================================================

class Player:
    """플레이어 우주선 클래스"""

    def __init__(self, pos: pygame.math.Vector2, screen_height: int, upgrades: Dict[str, int], ship_type: str = None):
        # 0. 영구 업그레이드 저장
        self.upgrades = upgrades

        # 0-1. 함선 타입 설정
        self.ship_type = ship_type or config.DEFAULT_SHIP
        self.ship_data = config.SHIP_TYPES.get(self.ship_type, config.SHIP_TYPES[config.DEFAULT_SHIP])
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

        # 3. 이미지 및 히트박스 (함선 크기에 따라 조정)
        ship_size = self.ship_stats.get("size", "medium")
        size_ratio = config.SHIP_SIZE_RATIOS.get(ship_size, config.IMAGE_SIZE_RATIOS["PLAYER"])
        image_size = int(screen_height * size_ratio)

        # 함선 이미지 로드 시도
        ship_image_path = config.ASSET_DIR / "images" / "ships" / self.ship_data.get("image", "fighter_front.png")
        if ship_image_path.exists():
            self.image = AssetManager.get_image(ship_image_path, (image_size, image_size))
        else:
            # 기본 플레이어 이미지 사용
            self.image = AssetManager.get_image(config.PLAYER_SHIP_IMAGE_PATH, (image_size, image_size))
        self.image_rect = self.image.get_rect(center=(self.pos.x, self.pos.y))

        hitbox_size = int(image_size * config.PLAYER_HITBOX_RATIO)
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
            'add_explosive': 0.0,
            'add_lightning': 0.0,
            'add_frost': 0.0,
        }

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

        final_cooldown = base_cooldown * (1 - cd_reduction_ratio - workshop_cd_reduction) * cooldown_mult
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
            spread_angle=5.0
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
        self.ultimate_charge = config.ULTIMATE_SETTINGS["charge_time"]  # 궁극기 충전 타이머
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
        self.trail_particles = []  # 이동 트레일 파티클 [(pos, lifetime, color, size), ...]
        self.afterimages = []  # 잔상 효과 [(image, pos, alpha, lifetime), ...]
        self.last_trail_spawn = 0.0  # 마지막 트레일 생성 시간
        self.trail_spawn_interval = 0.02  # 트레일 생성 간격 (초)
        self.disable_afterimages = False  # 잔상 비활성화 플래그 (공성 모드용)

        # 10-1. 이동 방향 기울기(틸트) 시스템
        self.current_tilt = 0.0  # 현재 기울기 각도 (도)
        self.target_tilt = 0.0  # 목표 기울기 각도 (도)
        self.tilt_speed = 8.0  # 기울기 보간 속도 (클수록 빠르게 기울어짐)
        self.max_tilt_angle = 25.0  # 최대 기울기 각도 (도)
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

    def move(self, keys: Dict, dt: float, screen_size: Tuple[int, int], current_time: float = 0.0, game_data: Dict = None):
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
        if game_data and game_data.get('current_wave') in config.BOSS_WAVES:
            speed_multiplier = 1.2  # 보스 웨이브에서 20% 속도 증가

        # 대각선 이동 시 속도 보정 (정규화)
        if velocity.length_squared() > 0:
            effective_speed = self.speed * speed_multiplier * self.mouse_move_speed_mult
            velocity = velocity.normalize() * effective_speed * dt
            self.velocity = velocity / dt  # 초당 속도 벡터 저장
            self.pos += velocity

            # 이동 효과 생성 (속도에 따라)
            self._create_movement_effects(current_time)
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
        closest_dist = float('inf')

        for enemy in enemies:
            if not hasattr(enemy, 'pos'):
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
        if enemy is None or not hasattr(enemy, 'pos'):
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
                # 약간의 랜덤 분산
                spread = pygame.math.Vector2(
                    random.uniform(-10, 10),
                    random.uniform(-10, 10)
                )
                particle_pos = spawn_pos + spread


                if speed_ratio < 0.5: # 0.3을 0.5로 변경하여 트레일 색상 변화 구간 확대
                    color = (150, 200, 255)  # 연한 하늘색
                elif speed_ratio < 0.98:
                    color = (100, 100, 255)  # 푸른 보라색
                else:
                    color = (100, 255, 255)  # 고열의 마젠타 (가장 고속)if 
                    
                # 속도에 따른 파티클 크기
                base_size = 3 + speed_ratio * 5
                size = int(base_size + random.uniform(-1, 2))
                size = max(1, size) # 최소 크기 보장
            
            



                # 파티클 수명 (속도가 빠를수록 길게)
                lifetime = 0.3 + speed_ratio * 0.3

                self.trail_particles.append({
                    'pos': particle_pos.copy(),
                    'lifetime': lifetime,
                    'max_lifetime': lifetime,
                    'color': color,
                    'size': size
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
                random.uniform(-10, 10),
                random.uniform(-10, 10)
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

            self.trail_particles.append({
            'pos': particle_pos.copy(),
            'lifetime': lifetime,
            'max_lifetime': lifetime,
            'color': color,
            'size': size
            })

            # 고속 이동 시 잔상 효과 추가 (공성 모드에서는 비활성화)
            if speed_ratio > 0.7 and not self.disable_afterimages:
                # 잔상 생성 (투명도 있는 플레이어 이미지)
                afterimage = self.image.copy()
                alpha = int(100 * speed_ratio)  # 속도에 따라 투명도 조절
                afterimage.set_alpha(alpha)

                # 잔상에 현재 기울기 적용
                if abs(self.current_tilt) > 0.5:
                    afterimage = pygame.transform.rotate(afterimage, self.current_tilt)

                self.afterimages.append({
                    'image': afterimage,
                    'pos': self.pos.copy(),
                    'alpha': alpha,
                    'lifetime': 0.15,  # 잔상 지속 시간
                    'max_lifetime': 0.15
                })    









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
        self.ultimate_effects.append({
            "type": "NOVA_BLAST",
            "pos": self.pos.copy(),
            "radius": 0,
            "max_radius": settings["radius"],
            "timer": settings["duration"],
            "color": settings["color"],
        })

        # 범위 내 모든 적에게 데미지 및 넉백
        for enemy in enemies:
            dist = (enemy.pos - self.pos).length()
            if dist <= settings["radius"]:
                # 데미지 적용
                enemy.take_damage(settings["damage"])

                # 넉백 적용
                if dist > 0:
                    knockback_dir = (enemy.pos - self.pos).normalize()
                    enemy.pos += knockback_dir * settings["knockback"] * (1 - dist / settings["radius"])

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
                targets.append({
                    "pos": target_enemy.pos.copy(),
                    "delay": i * settings["strike_interval"],
                    "timer": 0.0,
                    "active": False,
                })

        self.orbital_strikes = targets
        self.orbital_strike_timer = 0.0

    def take_damage(self, damage: float):
        """플레이어가 피해를 입습니다."""
        # 이미 사망 상태면 추가 데미지 무시
        if self.hp <= 0:
            return

        # Second Chance 스킬: 치명타 회피 (사망 직전에만 발동)
        if hasattr(self, 'second_chance_rate') and self.second_chance_rate > 0:
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
        if amount <= 0: return

        # HP가 0 이하면 max_hp만 증가 (게임 오버 상태에서는 회복 안 함)
        if self.hp <= 0:
            self.max_hp += amount
            print(f"INFO: Max HP increased to {self.max_hp}, HP remains at 0 (game over state)")
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
        if amount <= 0: return
        self.speed += amount
        print(f"INFO: Speed increased to {self.speed}")

    def add_damage_reduction(self, ratio: float):
        """피해 감소 비율을 추가합니다."""
        if ratio <= 0: return
        self.damage_reduction = min(0.75, self.damage_reduction + ratio)  # 최대 75%
        print(f"INFO: Damage reduction: {self.damage_reduction * 100:.0f}%")

    def add_regeneration(self, rate: float):
        """초당 체력 회복량을 추가합니다."""
        if rate <= 0: return
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
            self.ultimate_charge = min(self.ultimate_charge, config.ULTIMATE_SETTINGS["charge_time"])

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
                if not strike["active"] and self.orbital_strike_timer >= strike["delay"]:
                    strike["active"] = True
                    strike["timer"] = config.ULTIMATE_SETTINGS["ORBITAL_STRIKE"]["beam_duration"]

                if strike["active"]:
                    strike["timer"] -= dt

            # 완료된 스트라이크 제거
            self.orbital_strikes = [s for s in self.orbital_strikes if s["timer"] > 0 or not s["active"]]

        # 궁극기 시각 효과 업데이트
        for effect in self.ultimate_effects:
            effect["timer"] -= dt
            if effect["type"] == "NOVA_BLAST":
                # 폭발 반경 확장
                progress = 1 - (effect["timer"] / config.ULTIMATE_SETTINGS["NOVA_BLAST"]["duration"])
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
        self.current_tilt = max(-self.max_tilt_angle, min(self.max_tilt_angle, self.current_tilt))

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
            particle['lifetime'] -= dt
            if particle['lifetime'] <= 0:
                self.trail_particles.remove(particle)

        # 잔상 업데이트
        for afterimage in self.afterimages[:]:
            afterimage['lifetime'] -= dt
            if afterimage['lifetime'] <= 0:
                self.afterimages.remove(afterimage)
            else:
                # 페이드 아웃 효과
                fade_ratio = afterimage['lifetime'] / afterimage['max_lifetime']
                afterimage['image'].set_alpha(int(afterimage['alpha'] * fade_ratio))

    def _calculate_perspective_scale(self, screen_height: int) -> float:
        """Y 위치 기반 원근감 스케일 계산"""
        if not config.PERSPECTIVE_ENABLED or not config.PERSPECTIVE_APPLY_TO_PLAYER:
            return 1.0

        # Y 위치 비율 계산 (0.0 = 상단, 1.0 = 하단)
        depth_ratio = self.pos.y / screen_height
        depth_ratio = max(0.0, min(1.0, depth_ratio))

        # 스케일 계산
        scale = config.PERSPECTIVE_SCALE_MIN + (depth_ratio * (config.PERSPECTIVE_SCALE_MAX - config.PERSPECTIVE_SCALE_MIN))
        return scale

    def draw(self, screen: pygame.Surface):
        """플레이어 객체를 화면에 그립니다."""
        # 원근감 스케일 계산
        perspective_scale = self._calculate_perspective_scale(screen.get_height())

        # 1. 잔상 효과 그리기 (플레이어 뒤에)
        for afterimage in self.afterimages:
            # 잔상에도 원근감 적용
            if config.PERSPECTIVE_ENABLED and config.PERSPECTIVE_APPLY_TO_PLAYER and perspective_scale != 1.0:
                afterimage_scale = self._calculate_perspective_scale(screen.get_height())
                scaled_afterimage = pygame.transform.smoothscale(
                    afterimage['image'],
                    (int(afterimage['image'].get_width() * afterimage_scale),
                     int(afterimage['image'].get_height() * afterimage_scale))
                )
                rect = scaled_afterimage.get_rect(center=(int(afterimage['pos'].x), int(afterimage['pos'].y)))
                screen.blit(scaled_afterimage, rect)
            else:
                rect = afterimage['image'].get_rect(center=(int(afterimage['pos'].x), int(afterimage['pos'].y)))
                screen.blit(afterimage['image'], rect)

        # 2. 트레일 파티클 그리기
        for particle in self.trail_particles:
            # 페이드 아웃 효과
            fade_ratio = particle['lifetime'] / particle['max_lifetime']
            alpha = int(255 * fade_ratio)

            # 파티클 크기도 점점 작아짐
            current_size = max(1, int(particle['size'] * fade_ratio * perspective_scale))

            # 투명도를 가진 서페이스 생성
            particle_surface = pygame.Surface((current_size * 2, current_size * 2), pygame.SRCALPHA)
            pygame.draw.circle(particle_surface, (*particle['color'], alpha),
                             (current_size, current_size), current_size)

            # 파티클 위치에 그리기
            rect = particle_surface.get_rect(center=(int(particle['pos'].x), int(particle['pos'].y)))
            screen.blit(particle_surface, rect)

        # 3. 그릴 이미지 결정 (히트 플래시 적용 + 능력 효과)
        if self.is_flashing:
            # 흰색으로 깜빡임
            flash_surface = self.original_image.copy()
            flash_surface.fill(config.HIT_FLASH_COLOR, special_flags=pygame.BLEND_RGB_ADD)
            draw_image = flash_surface
        elif getattr(self, 'cloak_active', False):
            # 클로킹: 반투명 + 보라색 틴트
            cloak_surface = self.image.copy()
            cloak_surface.set_alpha(80)  # 반투명
            # 보라색 틴트
            tint_surface = pygame.Surface(cloak_surface.get_size(), pygame.SRCALPHA)
            tint_surface.fill((100, 50, 150, 50))
            cloak_surface.blit(tint_surface, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
            draw_image = cloak_surface
        elif getattr(self, 'evasion_active', False):
            # 회피 부스트: 노란색 글로우
            evasion_surface = self.image.copy()
            glow_surface = pygame.Surface(evasion_surface.get_size(), pygame.SRCALPHA)
            glow_surface.fill((255, 255, 100, 60))
            evasion_surface.blit(glow_surface, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
            draw_image = evasion_surface
        else:
            draw_image = self.image

        # 3-1. 이동 방향 기울기(틸트) 적용
        if abs(self.current_tilt) > 0.5:
            # 이미지 회전 (기울기 각도 적용)
            draw_image = pygame.transform.rotate(draw_image, self.current_tilt)

        # 4. 플레이어 이미지 그리기 (원근감 + 틸트 적용)
        if config.PERSPECTIVE_ENABLED and config.PERSPECTIVE_APPLY_TO_PLAYER and perspective_scale != 1.0:
            scaled_image = pygame.transform.smoothscale(
                draw_image,
                (int(draw_image.get_width() * perspective_scale),
                 int(draw_image.get_height() * perspective_scale))
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
                pygame.draw.circle(screen, effect["color"],
                                   (int(effect["pos"].x), int(effect["pos"].y)),
                                   int(effect["radius"]), 5)

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
                pygame.draw.circle(screen, settings["color"],
                                   (int(strike["pos"].x), int(strike["pos"].y)),
                                   settings["strike_radius"], 3)
                # 내부 빛나는 효과
                pygame.draw.circle(screen, (255, 200, 200),
                                   (int(strike["pos"].x), int(strike["pos"].y)),
                                   settings["strike_radius"] // 2)

        # 8. Ship Ability: Shield 시각 효과
        if getattr(self, 'shield_active', False):
            shield_hp = getattr(self, 'shield_hp', 0)
            shield_max = getattr(self, 'shield_max_hp', 1)
            shield_ratio = shield_hp / shield_max if shield_max > 0 else 0

            # 보호막 반지름 (플레이어 크기 기반)
            shield_radius = int(max(self.image.get_width(), self.image.get_height()) * 0.8)

            # 펄스 효과 (시간에 따라 크기 변화)
            import math
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
            pygame.draw.circle(screen, shield_color,
                             (int(self.pos.x), int(self.pos.y)),
                             shield_radius, 4)

            # 내부 반투명 원
            shield_surface = pygame.Surface((shield_radius * 2, shield_radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(shield_surface, (*shield_color, 40),
                             (shield_radius, shield_radius), shield_radius)
            screen.blit(shield_surface, (int(self.pos.x) - shield_radius, int(self.pos.y) - shield_radius))


# =========================================================


# ============================================================
# Enemy
# ============================================================

# 3. 적 클래스
# =========================================================

class Enemy:
    """적 우주선 클래스"""

    def __init__(self, pos: pygame.math.Vector2, screen_height: int, chase_probability: float = 1.0, enemy_type: str = "NORMAL"):

        # 0. 적 타입 설정
        self.enemy_type = enemy_type
        self.type_config = config.ENEMY_TYPES.get(enemy_type, config.ENEMY_TYPES["NORMAL"])

        # 1. 위치 및 이동
        self.pos = pos
        self.speed = config.ENEMY_BASE_SPEED * self.type_config["speed_mult"]
        self.chase_probability = chase_probability  # 플레이어 추적 확률 (0.0 ~ 1.0)
        self.wander_direction = pygame.math.Vector2(random.uniform(-1, 1), random.uniform(-1, 1)).normalize()
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
        original_image = AssetManager.get_image(config.ENEMY_SHIP_IMAGE_PATH, (image_size, image_size))
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
        self.is_respawned = self.type_config.get("is_respawned", False)  # 리스폰 적 여부
        self.is_retreating = False  # 퇴각 모드 (기존 적)
        self.is_circling = False    # 회전 공격 모드 (빨간 적)
        self.circle_angle = random.uniform(0, 2 * math.pi)  # 회전 시작 각도 (랜덤)
        self.retreat_target = None  # 퇴각 목표 위치
        self.escaped = False  # 화면 밖으로 도망 성공 여부 (킬 카운트 제외용)

    def _apply_color_tint(self, image: pygame.Surface, tint_color: tuple) -> pygame.Surface:
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

    def move_towards_player(self, player_pos: pygame.math.Vector2, dt: float, other_enemies: list = None):
        """플레이어를 향해 이동하되, 다른 적들과 거리를 유지하고 포위 공격합니다."""

        direction = player_pos - self.pos
        distance_to_player = direction.length()

        if direction.length_squared() > 0:
            direction = direction.normalize()

            # 포위 공격: 플레이어 주변에 원형으로 분산
            flank_force = pygame.math.Vector2(0, 0)
            if config.ENEMY_FLANK_ENABLED and distance_to_player < config.ENEMY_FLANK_DISTANCE:
                # 적의 ID를 기반으로 목표 각도 계산 (각 적마다 고유한 각도)
                import math
                base_angle = (self.enemy_id % 360) * (math.pi / 180)  # ID 기반 각도

                # 플레이어 중심으로 목표 위치 계산
                target_offset_x = math.cos(base_angle) * config.ENEMY_FLANK_DISTANCE
                target_offset_y = math.sin(base_angle) * config.ENEMY_FLANK_DISTANCE
                target_pos = pygame.math.Vector2(player_pos.x + target_offset_x, player_pos.y + target_offset_y)

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
                if hasattr(self, 'is_boss') and self.is_boss:
                    separation_radius = config.ENEMY_SEPARATION_RADIUS * 3.0  # 보스는 3배
                    separation_strength = config.ENEMY_SEPARATION_STRENGTH * 2.0  # 보스는 2배 강도
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
                            force_magnitude = ((separation_radius - distance) / separation_radius) ** 2
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
        if player and hasattr(player, 'execute_threshold') and player.execute_threshold > 0:
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

    def attack(self, player: 'Player', current_time: float) -> bool:
        """플레이어를 공격합니다. 공격 성공 시 True 반환"""
        if current_time - self.last_attack_time >= config.ENEMY_ATTACK_COOLDOWN:
            player.take_damage(self.damage)
            self.last_attack_time = current_time
            return True
        return False

    def update(self, player_pos: pygame.math.Vector2, dt: float, other_enemies: list = None, screen_size: tuple = None, current_time: float = 0.0):
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
                    self.wander_direction = pygame.math.Vector2(random.uniform(-1, 1), random.uniform(-1, 1)).normalize()
                    self.wander_timer = 0.0

                # 방황 방향으로 이동
                self.pos += self.wander_direction * self.speed * dt * 0.5  # 방황 시 속도 50%
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
        scale = config.PERSPECTIVE_SCALE_MIN + (depth_ratio * (config.PERSPECTIVE_SCALE_MAX - config.PERSPECTIVE_SCALE_MIN))
        return scale

    # ✅ [추가] 화면에 객체를 그리는 draw 메서드
    def draw(self, screen: pygame.Surface):
        """적 객체를 화면에 그리고 체력 바를 표시합니다."""
        # 원근감 스케일 계산
        perspective_scale = self._calculate_perspective_scale(screen.get_height())

        # 히트 플래시 적용
        if self.is_flashing:
            flash_surface = self.original_image.copy()
            flash_surface.fill(config.HIT_FLASH_COLOR, special_flags=pygame.BLEND_RGB_ADD)
            current_image = flash_surface
        else:
            current_image = self.image

        # 원근감 적용된 이미지 생성
        if config.PERSPECTIVE_ENABLED and config.PERSPECTIVE_APPLY_TO_ENEMIES and perspective_scale != 1.0:
            scaled_image = pygame.transform.smoothscale(
                current_image,
                (int(current_image.get_width() * perspective_scale),
                 int(current_image.get_height() * perspective_scale))
            )
            scaled_rect = scaled_image.get_rect(center=self.image_rect.center)
        else:
            scaled_image = current_image
            scaled_rect = self.image_rect

        # 상태 이펙트 시각 효과 (이미지 뒤에 광선 효과)
        if self.is_frozen:
            # 프리즈: 밝은 청백색 광선 효과
            self._draw_glow_effect(screen, (180, 220, 255), intensity=3, layers=3, scale=perspective_scale)
        elif self.is_slowed:
            # 슬로우: 파란색 광선 효과
            self._draw_glow_effect(screen, (100, 150, 255), intensity=2, layers=2, scale=perspective_scale)

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
        pygame.draw.rect(screen, config.GREEN, (bar_x, bar_y, current_health_width, bar_height))

    def _draw_glow_effect(self, screen: pygame.Surface, color: tuple, intensity: int = 2, layers: int = 2, scale: float = 1.0):
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
                    int(self.image.get_height() * scale_factor)
                )
                scaled_image = pygame.transform.scale(self.image, scaled_size)

                # 색상 적용
                colored_surface = scaled_image.copy()
                colored_surface.fill(color + (0,), special_flags=pygame.BLEND_RGBA_MULT)
                colored_surface.fill((255, 255, 255, alpha), special_flags=pygame.BLEND_RGBA_MIN)

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
                pygame.draw.circle(glow_surf, color + (alpha,), (radius, radius), radius)
                glow_rect = glow_surf.get_rect(center=self.image_rect.center)
                screen.blit(glow_surf, glow_rect)

# =========================================================


# ============================================================
# Bullet
# ============================================================

# 4. 총알 클래스
# =========================================================

class Bullet:
    """총알 클래스"""

    def __init__(self, pos: pygame.math.Vector2, direction: pygame.math.Vector2, damage: float, piercing: bool = False):

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

        self.image = AssetManager.get_image(config.PLAYER_BULLET_IMAGE_PATH, (image_size, image_size))
        self.image_rect = self.image.get_rect(center=(self.pos.x, self.pos.y))

        hitbox_size = int(image_size * config.BULLET_HITBOX_RATIO)
        self.hitbox = pygame.Rect(0, 0, hitbox_size, hitbox_size)
        self.hitbox.center = (int(self.pos.x), int(self.pos.y))

    def update(self, dt: float, screen_size: Tuple[int, int]):
        """총알 위치를 업데이트하고, 화면 밖으로 나가면 제거합니다."""

        if not hasattr(self, 'image'):
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
            if (self.pos.x < -50 or self.pos.x > SCREEN_WIDTH + 50 or
                self.pos.y < -50 or self.pos.y > SCREEN_HEIGHT + 50):
                self.is_alive = False

    def draw(self, screen: pygame.Surface):
        """총알 객체와 트레일을 화면에 그립니다."""
        if self.is_alive:
            # 이미지가 아직 초기화되지 않았다면 폴백 렌더링
            if not hasattr(self, 'image') or self.image is None:
                # 간단한 원으로 그리기 (폴백)
                pygame.draw.circle(screen, (255, 0, 0), (int(self.pos.x), int(self.pos.y)), 20, 0)
                pygame.draw.circle(screen, (255, 255, 0), (int(self.pos.x), int(self.pos.y)), 20, 3)
                return

            # 원근감 스케일 계산
            perspective_scale = self._calculate_perspective_scale(screen.get_height())

            # 원근감 적용된 이미지
            if config.PERSPECTIVE_ENABLED and config.PERSPECTIVE_APPLY_TO_BULLETS and perspective_scale != 1.0:
                scaled_image = pygame.transform.scale(
                    self.image,
                    (int(self.image.get_width() * perspective_scale),
                     int(self.image.get_height() * perspective_scale))
                )
                scaled_rect = scaled_image.get_rect(center=self.image_rect.center)
            else:
                scaled_image = self.image
                scaled_rect = self.image_rect

            # 트레일 그리기 (뒤에서부터 앞으로, 점점 투명하게)
            for i, trail_pos in enumerate(self.trail_positions):
                alpha = int(255 * (i + 1) / len(self.trail_positions) * config.BULLET_TRAIL_ALPHA_DECAY)
                alpha = max(0, min(255, alpha))

                # 트레일용 반투명 서피스 생성
                trail_surf = scaled_image.copy()
                trail_surf.set_alpha(alpha)
                trail_rect = trail_surf.get_rect(center=(int(trail_pos.x), int(trail_pos.y)))
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
        scale = config.PERSPECTIVE_SCALE_MIN + (depth_ratio * (config.PERSPECTIVE_SCALE_MAX - config.PERSPECTIVE_SCALE_MIN))
        return scale

# =========================================================


# ============================================================
# Boss
# ============================================================

# 6. 보스 클래스
# =========================================================

class Boss(Enemy):
    """보스 적 클래스 - Enemy를 상속받되 크기와 체력이 훨씬 큼"""

    def __init__(self, pos: pygame.math.Vector2, screen_height: int, boss_name: str = "Boss", wave_number: int = 5):
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
        self.image = AssetManager.get_image(config.ENEMY_SHIP_IMAGE_PATH, (image_size, image_size))
        self.image_rect = self.image.get_rect(center=(self.pos.x, self.pos.y))

        hitbox_size = int(image_size * config.ENEMY_HITBOX_RATIO)
        self.hitbox = pygame.Rect(0, 0, hitbox_size, hitbox_size)
        self.hitbox.center = (int(self.pos.x), int(self.pos.y))

        self.is_alive = True

        # 5. 히트 플래시 효과 속성 (Enemy에서도 있지만 이미지가 재설정되므로 다시 저장)
        self.hit_flash_timer = 0.0
        self.is_flashing = False
        self.original_image = self.image.copy()

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

    def update(self, player_pos: pygame.math.Vector2, dt: float, other_enemies: list = None, screen_size: tuple = None, current_time: float = 0.0):
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
        if hp_ratio <= config.BOSS_PATTERN_SETTINGS["BERSERK"]["hp_threshold"] and not self.is_berserk:
            self.is_berserk = True
            self.speed = self.base_speed * config.BOSS_PATTERN_SETTINGS["BERSERK"]["speed_mult"]
            self.damage = config.ENEMY_ATTACK_DAMAGE * config.BOSS_PATTERN_SETTINGS["BERSERK"]["damage_mult"]

        # 패턴 타이머 업데이트
        self.pattern_timer += dt

        # 소환 패턴 (쿨다운 체크)
        if current_time - self.last_summon_time >= config.BOSS_PATTERN_SETTINGS["SUMMON_MINIONS"]["summon_cooldown"]:
            if random.random() < 0.3:  # 30% 확률로 소환 시도
                self._summon_minions(other_enemies)
                self.last_summon_time = current_time

        # 돌진 패턴 (쿨다운 체크)
        if current_time - self.last_charge_time >= config.BOSS_PATTERN_SETTINGS["CHARGE_ATTACK"]["cooldown"]:
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

        summon_count = config.BOSS_PATTERN_SETTINGS["SUMMON_MINIONS"]["summon_count"].get(self.wave_number, 2)
        minion_hp_ratio = config.BOSS_PATTERN_SETTINGS["SUMMON_MINIONS"]["minion_hp_ratio"]

        for i in range(summon_count):
            # 보스 주변에 랜덤 위치 생성
            offset_x = random.uniform(-100, 100)
            offset_y = random.uniform(-100, 100)
            spawn_pos = pygame.math.Vector2(self.pos.x + offset_x, self.pos.y + offset_y)

            # 미니언 생성 (NORMAL 타입)
            from objects import Enemy  # 순환 참조 방지
            minion = Enemy(spawn_pos, self.image_rect.height * 10, 1.0, "NORMAL")  # screen_height 근사값
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
        charge_duration = config.BOSS_PATTERN_SETTINGS["CHARGE_ATTACK"]["charge_duration"]

        if self.pattern_timer >= charge_duration:
            self.is_charging = False
            return

        charge_speed = self.base_speed * config.BOSS_PATTERN_SETTINGS["CHARGE_ATTACK"]["charge_speed_mult"]
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
        # 히트 플래시 적용
        if self.is_flashing:
            flash_surface = self.original_image.copy()
            flash_surface.fill(config.HIT_FLASH_COLOR, special_flags=pygame.BLEND_RGB_ADD)
            self.image = flash_surface

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
            red_alpha[:] = (red_alpha[:] * 0.6).astype('uint8')  # 60% 투명도
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
            blue_alpha[:] = (blue_alpha[:] * 0.6).astype('uint8')  # 60% 투명도
            del blue_array, blue_alpha  # 배열 잠금 해제
            screen.blit(blue_surface, (self.image_rect.x + offset, self.image_rect.y))

        # 원본 이미지 (중앙)
        screen.blit(self.image, self.image_rect)

    def _draw_glow_effect(self, screen: pygame.Surface, color: tuple, intensity: int = 2, layers: int = 2):
        """이미지 윤곽선 기반 광선 효과 (Glow Effect) - Boss용"""
        # 보스는 크로마틱 어버레이션이 있어 광선 효과 단순화
        for layer in range(layers, 0, -1):
            radius = self.image_rect.width // 2 + layer * intensity * 2
            alpha = int(60 / layer)

            glow_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, color + (alpha,), (radius, radius), radius)
            glow_rect = glow_surf.get_rect(center=self.image_rect.center)
            screen.blit(glow_surf, glow_rect)


# =========================================================
