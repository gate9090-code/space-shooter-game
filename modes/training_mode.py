# modes/training_mode.py
"""
TrainingMode - 스킬 연습 모드

특징:
- 무한 HP (죽지 않음)
- 자유롭게 스킬 선택/테스트
- 웨이브 기반 자동 적 스폰
- 12개 스킬 완전 지원
- 언제든 기지로 복귀 가능
"""

import pygame
import random
import time
import math
from typing import List, Dict, Optional, Tuple

import config
from mode_configs import config_training
from modes.base_mode import GameMode, ModeConfig
# Entity imports from new modules
from entities.player import Player
from entities.enemies import Enemy
from entities.weapons import Bullet
from entities.collectibles import CoinGem
from entities.support_units import Drone, Turret
from systems.combat_system import CombatSystem
from systems.skill_system import SkillSystem
from systems.effect_system import EffectSystem
from systems.spawn_system import SpawnSystem, SpawnConfig
from systems.ui_system import UISystem, UIConfig
from game_logic import reset_game_data, update_game_objects


class TrainingSpawnManager:
    """웨이브 기반 자동 적 스폰 관리자"""

    def __init__(self, screen_size: Tuple[int, int]):
        self.screen_size = screen_size
        self.current_wave = 1
        self.wave_timer = 0.0
        self.spawn_timer = 0.0
        self.loop_count = 0
        self.wave_changed = False
        self.wave_change_display_timer = 0.0

        # 현재 웨이브 설정 로드
        self._load_wave_config()

    def _load_wave_config(self):
        """현재 웨이브 설정 로드"""
        wave_data = config_training.TRAINING_WAVES.get(self.current_wave, {})
        self.wave_name = wave_data.get("name", f"WAVE {self.current_wave}")
        self.min_enemies = wave_data.get("min_enemies", config_training.MIN_ENEMIES)
        self.max_enemies = wave_data.get("max_enemies", config_training.MAX_ENEMIES)
        self.spawn_interval = wave_data.get("spawn_interval", config_training.SPAWN_INTERVAL)
        self.enemy_distribution = wave_data.get("enemy_distribution", {"NORMAL": 1.0})
        self.wave_duration = wave_data.get("duration", 60)

        # 루프 시 난이도 증가 적용
        if self.loop_count > 0:
            difficulty_mult = config_training.WAVE_LOOP_DIFFICULTY_MULT ** self.loop_count
            self.min_enemies = int(self.min_enemies * difficulty_mult)
            self.max_enemies = int(self.max_enemies * difficulty_mult)
            self.spawn_interval = max(0.2, self.spawn_interval / difficulty_mult)

    def update(self, dt: float, current_enemy_count: int, enemies_list: list, screen_height: int) -> Tuple[int, bool]:
        """
        스폰 시스템 업데이트
        Returns: (spawned_count, wave_changed)
        """
        spawned_count = 0
        wave_changed = False

        # 웨이브 변경 표시 타이머
        if self.wave_change_display_timer > 0:
            self.wave_change_display_timer -= dt

        # 웨이브 타이머 업데이트
        if self.wave_duration is not None:
            self.wave_timer += dt
            if self.wave_timer >= self.wave_duration:
                wave_changed = self._advance_wave()

        # 적 수 기반 스폰 트리거
        if current_enemy_count < self.min_enemies:
            # 즉시 스폰 (min_enemies까지 채우기)
            spawn_needed = min(self.min_enemies - current_enemy_count, config_training.SPAWN_BATCH_SIZE)
            for _ in range(spawn_needed):
                enemy = self._spawn_enemy(screen_height)
                if enemy:
                    enemies_list.append(enemy)
                    spawned_count += 1
            self.spawn_timer = 0.0
        elif current_enemy_count < self.max_enemies:
            # 일정 간격으로 스폰
            self.spawn_timer += dt
            if self.spawn_timer >= self.spawn_interval:
                enemy = self._spawn_enemy(screen_height)
                if enemy:
                    enemies_list.append(enemy)
                    spawned_count += 1
                self.spawn_timer = 0.0

        return spawned_count, wave_changed

    def _advance_wave(self) -> bool:
        """다음 웨이브로 진행"""
        self.wave_timer = 0.0

        if self.current_wave >= config_training.TOTAL_TRAINING_WAVES:
            if config_training.WAVE_LOOP_ENABLED:
                self.current_wave = 1
                self.loop_count += 1
                print(f"INFO: Wave loop {self.loop_count + 1} started")
            # else: 마지막 웨이브 유지
        else:
            self.current_wave += 1

        self._load_wave_config()
        self.wave_change_display_timer = 2.0  # 2초간 웨이브 변경 표시
        print(f"INFO: Wave changed to {self.wave_name}")
        return True

    def _spawn_enemy(self, screen_height: int) -> Optional[Enemy]:
        """확률 분포에 따라 적 스폰"""
        enemy_type = self._select_enemy_type()
        pos = self._get_spawn_position()

        try:
            enemy = Enemy(
                pos=pygame.math.Vector2(pos),
                screen_height=screen_height,
                chase_probability=1.0,
                enemy_type=enemy_type,
            )
            print(f"DEBUG: Enemy spawned at {pos}, type={enemy_type}")
            return enemy
        except Exception as e:
            import traceback
            print(f"ERROR: Failed to spawn enemy: {e}")
            traceback.print_exc()
            return None

    def _select_enemy_type(self) -> str:
        """확률 분포에서 적 타입 선택"""
        distribution = self.enemy_distribution
        total = sum(distribution.values())
        rand = random.random() * total

        cumulative = 0.0
        for enemy_type, probability in distribution.items():
            cumulative += probability
            if rand <= cumulative:
                return enemy_type

        return "NORMAL"  # 폴백

    def _get_spawn_position(self) -> Tuple[int, int]:
        """스폰 위치 결정 (상단/좌우)"""
        screen_w, screen_h = self.screen_size
        margin = config_training.SPAWN_MARGIN

        # 스폰 위치 설정 확인
        positions = config_training.SPAWN_POSITIONS
        available = []
        if positions.get("top", True):
            available.append("top")
        if positions.get("sides", True):
            available.extend(["left", "right"])

        if not available:
            available = ["top"]

        location = random.choice(available)

        if location == "top":
            x = random.randint(margin, screen_w - margin)
            y = random.randint(-50, 0)
        elif location == "left":
            x = random.randint(-50, 0)
            y = random.randint(margin, screen_h // 2)
        else:  # right
            x = random.randint(screen_w, screen_w + 50)
            y = random.randint(margin, screen_h // 2)

        return (x, y)

    def reset(self):
        """스폰 매니저 리셋"""
        self.current_wave = 1
        self.wave_timer = 0.0
        self.spawn_timer = 0.0
        self.loop_count = 0
        self.wave_change_display_timer = 0.0
        self._load_wave_config()

    def get_wave_info(self) -> Dict:
        """현재 웨이브 정보 반환"""
        return {
            "wave": self.current_wave,
            "name": self.wave_name,
            "loop": self.loop_count,
            "timer": self.wave_timer,
            "duration": self.wave_duration,
            "display_timer": self.wave_change_display_timer,
        }


class TrainingMode(GameMode):
    """스킬 연습 모드"""

    def get_config(self) -> ModeConfig:
        """모드 설정 반환"""
        # screen_size는 super().__init__() 이후에 설정되므로 getattr 사용
        screen_size = getattr(self, 'screen_size', (1920, 1080))
        return ModeConfig(
            mode_name="training",
            perspective_enabled=True,
            perspective_apply_to_player=True,
            perspective_apply_to_enemies=True,
            perspective_apply_to_bullets=True,
            perspective_apply_to_gems=True,
            player_speed_multiplier=1.0,
            player_start_pos=(screen_size[0] // 2, screen_size[1] // 2),
            player_afterimages_enabled=True,
            background_type="static",
            parallax_enabled=False,
            meteor_enabled=False,
            show_wave_ui=False,
            show_stage_ui=False,
            show_minimap=False,
            show_skill_indicators=True,
            wave_system_enabled=False,
            spawn_system_enabled=False,
            random_events_enabled=False,
            asset_prefix="training",
        )

    def __init__(self, engine):
        super().__init__(engine)

        # 훈련 모드 전용 설정
        self.invincible = True  # 무적 모드
        self.skill_points = 99  # 무한 스킬 포인트

        # 웨이브 기반 스폰 매니저 (init에서 초기화)
        self.spawn_manager: Optional[TrainingSpawnManager] = None

        # UI 상태
        self.show_skill_menu = False
        self.show_help = False  # H키로만 도움말 표시
        self.hovered_skill: Optional[str] = None  # 현재 호버된 스킬

        # 활성화된 스킬 목록 (표시용)
        self.active_skills: List[Dict] = []

        # 12개 스킬 선택 상태 (토글 방식)
        self.selected_skills = {skill: False for skill in config_training.SKILL_ORDER}

        # 스킬 레벨 추적 (12개)
        self.skill_levels = {skill: 0 for skill in config_training.SKILL_ORDER}

        # 스킬 활성화 효과 큐
        self.skill_activation_queue: List[Dict] = []

        # 스킬 메뉴 배경 이미지
        self.skill_menu_bg: Optional[pygame.Surface] = None

    def init(self):
        """훈련 모드 초기화"""
        config.GAME_MODE = "training"

        # 시스템 초기화
        self.combat_system = CombatSystem()
        self.skill_system = SkillSystem()
        self.effect_system = EffectSystem()
        self.spawn_system = SpawnSystem(SpawnConfig(
            enemy_spawn_interval=2.0,
            enemy_spawn_count=1,
            boss_enabled=False,
        ))
        self.ui_system = UISystem(UIConfig(
            show_hp_bar=True,
            show_score=False,
            show_wave_info=False,
            show_level_info=True,
            show_skill_indicators=True,
        ))

        # 게임 데이터 초기화
        self.game_data = reset_game_data()
        self.game_data['game_state'] = config.GAME_STATE_RUNNING
        self.game_data['player_level'] = 10  # 시작 레벨 10

        # 플레이어 생성 (강화된 상태)
        self.spawn_player(
            pos=self.config.player_start_pos,
            upgrades=self.engine.shared_state.get('player_upgrades', {})
        )

        # 플레이어 강화 (훈련용)
        if self.player:
            self.player.max_hp = 9999
            self.player.hp = 9999

        # 배경 설정
        self.background = self._load_background()

        # 스킬 메뉴 버튼 영역
        self.skill_buttons: Dict[str, pygame.Rect] = {}
        self.menu_buttons: Dict[str, pygame.Rect] = {}

        # 폰트 초기화 (engine.fonts가 없을 때만 폴백 사용)
        if not self.fonts or not isinstance(self.fonts, dict):
            self.fonts = {
                "huge": pygame.font.Font(None, 48),
                "large": pygame.font.Font(None, 36),
                "medium": pygame.font.Font(None, 24),
                "small": pygame.font.Font(None, 20),
                "tiny": pygame.font.Font(None, 18),
                "micro": pygame.font.Font(None, 15),
            }

        # 웨이브 기반 스폰 매니저 초기화
        self.spawn_manager = TrainingSpawnManager(self.screen_size)

        # 스킬 메뉴 배경 이미지 로드
        self._load_skill_menu_bg()

        print("INFO: Training Mode initialized")

    def _load_skill_menu_bg(self):
        """스킬 메뉴 배경 이미지 로드"""
        try:
            bg_path = config.ASSET_DIR / "images" / "ui" / "skill_menu_bg.jpg"
            if bg_path.exists():
                self.skill_menu_bg = pygame.image.load(str(bg_path)).convert()
                # 메뉴 크기에 맞게 스케일
                self.skill_menu_bg = pygame.transform.scale(self.skill_menu_bg, (800, 600))
                print("INFO: Skill menu background loaded")
            else:
                print(f"WARNING: Skill menu background not found: {bg_path}")
        except Exception as e:
            print(f"WARNING: Failed to load skill menu background: {e}")

    def _load_background(self) -> Optional[pygame.Surface]:
        """훈련장 배경 로드 - facility_bg 이미지 사용"""
        try:
            # facility_bg 이미지 로드 시도
            bg_path = config.ASSET_DIR / "images" / "base" / "facilities" / "facility_bg.png"
            if bg_path.exists():
                bg = pygame.image.load(str(bg_path)).convert()
                return pygame.transform.smoothscale(bg, self.screen_size)
        except Exception as e:
            print(f"WARNING: Failed to load facility_bg for training: {e}")

        # 폴백: 기존 배경
        try:
            bg_path = config.ASSET_DIR / "images" / "backgrounds" / "bg1.jpg"
            if bg_path.exists():
                bg = pygame.image.load(str(bg_path)).convert()
                return pygame.transform.scale(bg, self.screen_size)
        except Exception as e:
            print(f"WARNING: Failed to load training background: {e}")
        return None

    def update(self, dt: float, current_time: float):
        """훈련 모드 업데이트"""
        if self.game_data["game_state"] != config.GAME_STATE_RUNNING:
            return

        # 플레이어 무적 유지
        if self.invincible and self.player:
            self.player.hp = self.player.max_hp

        # 웨이브 기반 자동 스폰
        if self.spawn_manager:
            current_enemy_count = len([e for e in self.enemies if e.is_alive])
            spawned, wave_changed = self.spawn_manager.update(
                dt, current_enemy_count, self.enemies, self.screen_size[1]
            )
            if wave_changed:
                self._on_wave_change()

        # 적 이동 제한 (화면 중앙 아래로 진입 불가)
        self._limit_enemy_movement()

        # 기본 업데이트
        scaled_dt = self.update_common(dt, current_time)

        # 플레이어 업데이트 (이동 입력)
        self.update_player(scaled_dt, current_time)

        # update_game_objects 사용 (스킬 처리 포함)
        if self.player:
            update_game_objects(
                self.player, self.enemies, self.bullets, self.gems,
                self.effects, self.screen_size, scaled_dt, current_time,
                self.game_data,
                damage_numbers=None,
                damage_number_manager=self.damage_number_manager,
                screen_shake=self.screen_shake,
                sound_manager=self.sound_manager,
                death_effect_manager=self.death_effect_manager
            )

        # 죽은 적 카운트 및 Starfall 트리거
        dead_enemies = [e for e in self.enemies if not e.is_alive]
        if dead_enemies and self.player and self.player.has_starfall:
            for _ in dead_enemies:
                self._apply_starfall_effect()

        # Starfall 타이머 업데이트
        if self.player and hasattr(self.player, 'starfall_timer') and self.player.starfall_timer > 0:
            self.player.starfall_timer = max(0, self.player.starfall_timer - scaled_dt)

        # 죽은 적/총알/젬 제거
        self.enemies = [e for e in self.enemies if e.is_alive]
        self.bullets = [b for b in self.bullets if b.is_alive]
        self.gems = [g for g in self.gems if not g.collected]

        # 드론 업데이트
        for drone in self.drones[:]:
            drone.update(scaled_dt, self.enemies, self.bullets)
            if not drone.is_alive:
                self.drones.remove(drone)

        # 터렛 업데이트
        for turret in self.turrets[:]:
            turret.update(scaled_dt, self.enemies, self.bullets)
            if not turret.is_alive:
                self.turrets.remove(turret)

        # 이펙트 업데이트 및 죽은 이펙트 제거
        for effect in self.effects[:]:
            if hasattr(effect, 'update'):
                # AnimatedEffect는 (dt, current_time) 필요
                effect.update(scaled_dt, current_time)
            if hasattr(effect, 'is_alive') and not effect.is_alive:
                self.effects.remove(effect)

        # 패시브 스킬 업데이트 (재생 등)
        self.skill_system.update_passive_skills(
            self.player, self.enemies, self.effects, scaled_dt, current_time
        )

        # 스킬 활성화 효과 업데이트
        for effect in self.skill_activation_queue[:]:
            effect["timer"] -= dt
            if effect["timer"] <= 0.5:
                effect["alpha"] = max(0, int(effect["timer"] / 0.5 * 255))
            if effect["timer"] <= 0:
                self.skill_activation_queue.remove(effect)

    def _handle_collisions(self):
        """충돌 처리 - update_game_objects에서 처리하므로 여기서는 호출 안 함"""
        # 참고: 총알-적 충돌과 스킬 효과, 젬 충돌 모두
        # utils.py의 update_game_objects에서 처리됨
        pass

    # =========================================================
    # 스킬 효과 처리 함수들
    # =========================================================

    def _apply_explosive_effect(self, hit_pos, hit_enemy):
        """폭발 스킬 효과 적용"""
        from effects.screen_effects import Shockwave
        from game_logic import create_explosion_particles

        radius = self.player.explosive_radius
        damage = config.ATTRIBUTE_SKILL_SETTINGS.get("EXPLOSIVE", {}).get("damage_ratio", 0.5) * 50

        # 폭발 이펙트
        create_explosion_particles(hit_pos, self.effects)
        self.effects.append(Shockwave(hit_pos, radius))

        # 범위 내 다른 적에게 데미지
        for enemy in self.enemies:
            if enemy == hit_enemy or not enemy.is_alive:
                continue
            distance = hit_pos.distance_to(enemy.pos)
            if distance < radius:
                # 거리에 따른 데미지 감소
                damage_ratio = 1.0 - (distance / radius) * 0.5
                enemy.take_damage(damage * damage_ratio)

                # Chain Explosion (연쇄 폭발)
                if self.player.has_chain_explosion and not enemy.is_alive:
                    if random.random() < 0.3:  # 30% 연쇄 확률
                        self._apply_explosive_effect(enemy.pos, enemy)

    def _apply_lightning_effect(self, hit_pos):
        """번개 체인 스킬 효과 적용"""
        from effects.screen_effects import LightningEffect

        chain_count = self.player.lightning_chain_count
        chain_range = config.ATTRIBUTE_SKILL_SETTINGS.get("LIGHTNING", {}).get("chain_range", 250)
        damage = config.ATTRIBUTE_SKILL_SETTINGS.get("LIGHTNING", {}).get("damage", 30)

        hit_enemies = []
        current_pos = hit_pos

        for _ in range(chain_count):
            nearest_enemy = None
            nearest_distance = float('inf')

            for enemy in self.enemies:
                if not enemy.is_alive or enemy in hit_enemies:
                    continue
                distance = current_pos.distance_to(enemy.pos)
                if distance < chain_range and distance < nearest_distance:
                    nearest_enemy = enemy
                    nearest_distance = distance

            if not nearest_enemy:
                break

            # 번개 이펙트
            self.effects.append(LightningEffect(current_pos, nearest_enemy.pos))

            # 데미지 적용
            nearest_enemy.take_damage(damage)
            hit_enemies.append(nearest_enemy)
            current_pos = nearest_enemy.pos

    def _apply_frost_effect(self, enemy):
        """빙결/둔화 스킬 효과 적용"""
        slow_ratio = self.player.frost_slow_ratio

        # 슬로우 적용 (적에게 apply_slow 메서드가 있으면)
        if hasattr(enemy, 'apply_slow'):
            enemy.apply_slow(slow_ratio, 2.0)  # 2초 지속
        else:
            # apply_slow가 없으면 직접 속도 감소 적용
            if hasattr(enemy, 'speed'):
                if not hasattr(enemy, '_original_speed'):
                    enemy._original_speed = enemy.speed
                enemy.speed = enemy._original_speed * (1.0 - slow_ratio)
                enemy._slow_timer = 2.0

        # Deep Freeze (완전 동결)
        if self.player.has_deep_freeze:
            freeze_chance = self.player.freeze_chance
            if random.random() < freeze_chance:
                if hasattr(enemy, 'apply_freeze'):
                    enemy.apply_freeze(1.5)  # 1.5초 동결
                else:
                    # apply_freeze가 없으면 속도를 0으로
                    if hasattr(enemy, 'speed'):
                        enemy.speed = 0
                        enemy._freeze_timer = 1.5

    def _apply_execute_effect(self, enemy):
        """처형 스킬 효과 적용"""
        if not enemy.is_alive:
            return

        threshold = self.player.execute_threshold
        hp_ratio = enemy.hp / enemy.max_hp if enemy.max_hp > 0 else 1.0

        if hp_ratio <= threshold:
            enemy.hp = 0
            enemy.is_alive = False
            # 처형 이펙트 (보라색 파티클)
            from game_logic import create_hit_particles
            create_hit_particles(enemy.pos, self.effects)

    def _apply_starfall_effect(self):
        """별똥별 스킬 효과 적용 (적 처치 시)"""
        from effects.screen_effects import StarfallEffect

        # 쿨다운 체크
        if hasattr(self.player, 'starfall_timer') and self.player.starfall_timer > 0:
            return

        # 랜덤 위치에 별똥별 생성
        star_count = getattr(self.player, 'starfall_count', 5)
        screen_w, screen_h = self.screen_size

        for _ in range(star_count):
            star_pos = pygame.math.Vector2(
                random.uniform(100, screen_w - 100),
                random.uniform(50, screen_h * 0.5)  # 화면 상단 절반에만
            )

            # StarfallEffect가 있으면 추가
            try:
                self.effects.append(StarfallEffect(star_pos))
            except:
                pass

            # 범위 데미지
            starfall_radius = 100
            starfall_damage = 80
            for enemy in self.enemies:
                if not enemy.is_alive:
                    continue
                distance = star_pos.distance_to(enemy.pos)
                if distance < starfall_radius:
                    enemy.take_damage(starfall_damage)

        # 쿨다운 설정
        self.player.starfall_timer = getattr(self.player, 'starfall_cooldown', 30.0)

    def _limit_enemy_movement(self):
        """적 이동 제한 - 화면 중앙 아래로 진입 불가"""
        screen_h = self.screen_size[1]
        limit_y = screen_h * config_training.ENEMY_MOVEMENT_LIMIT

        for enemy in self.enemies:
            if enemy.is_alive and enemy.pos.y > limit_y:
                # 제한선 아래로 내려가면 되돌림
                enemy.pos.y = limit_y
                # 방향 반전 (위로 이동하도록)
                if hasattr(enemy, 'velocity') and enemy.velocity.y > 0:
                    enemy.velocity.y = -abs(enemy.velocity.y) * 0.5

    def _on_wave_change(self):
        """웨이브 변경 시 호출"""
        if self.spawn_manager:
            wave_info = self.spawn_manager.get_wave_info()
            # 웨이브 변경 알림 표시
            self.skill_activation_queue.append({
                "name": wave_info["name"],
                "level": 0,
                "color": (255, 200, 100),
                "timer": 2.0,
                "alpha": 255,
            })

    def render(self, screen: pygame.Surface):
        """훈련 모드 렌더링"""
        # 배경
        if self.background:
            screen.blit(self.background, (0, 0))
        else:
            screen.fill((20, 25, 40))

        # 게임 오브젝트
        for gem in self.gems:
            gem.draw(screen)
        for turret in self.turrets:
            turret.draw(screen)
        for enemy in self.enemies:
            enemy.draw(screen)
        for bullet in self.bullets:
            bullet.draw(screen)
        for drone in self.drones:
            drone.draw(screen)

        # Static Field 시각 효과 (플레이어 주변 원형 필드)
        if self.player and getattr(self.player, 'has_static_field', False):
            self._render_static_field(screen)

        # Regeneration 시각 효과 (녹색 힐링 파티클)
        if self.player and getattr(self.player, 'regeneration_rate', 0) > 0:
            self._render_regeneration_effect(screen)

        # Phoenix 준비 상태 시각 효과 (주황색 불꽃)
        if self.player and getattr(self.player, 'has_phoenix_rebirth', False):
            self._render_phoenix_ready(screen)

        if self.player:
            self.player.draw(screen)

        # 이펙트 렌더링 (Shockwave, LightningEffect 등)
        for effect in self.effects:
            if hasattr(effect, 'draw') and hasattr(effect, 'is_alive'):
                if effect.is_alive:
                    effect.draw(screen)

        # 데미지 넘버 렌더링
        if self.damage_number_manager:
            self.damage_number_manager.draw(screen)

        # 훈련 모드 UI
        self._render_training_ui(screen)

        # 활성 스킬 패널 (좌측)
        self._render_active_skills(screen)

        # 스킬 활성화 효과 (화면 상단 중앙)
        self._render_skill_activation(screen)

        # 도움말
        if self.show_help:
            self._render_help(screen)

        # 스킬 메뉴
        if self.show_skill_menu:
            self._render_skill_menu(screen)

    def _render_training_ui(self, screen: pygame.Surface):
        """훈련 모드 UI 렌더링"""
        screen_w, screen_h = self.screen_size

        # 상단 정보 바
        info_bg = pygame.Surface((screen_w, 50), pygame.SRCALPHA)
        info_bg.fill((0, 0, 0, 180))
        screen.blit(info_bg, (0, 0))

        # 제목
        title_font = self.fonts.get("large", pygame.font.Font(None, 36))
        title = title_font.render("TRAINING ROOM", True, (100, 200, 255))
        screen.blit(title, (20, 10))

        # 웨이브 정보
        info_font = self.fonts.get("medium", pygame.font.Font(None, 24))
        if self.spawn_manager:
            wave_info = self.spawn_manager.get_wave_info()
            wave_text = wave_info["name"]
            if wave_info["loop"] > 0:
                wave_text += f" (Loop {wave_info['loop'] + 1})"
            wave_render = info_font.render(wave_text, True, (255, 200, 100))
            screen.blit(wave_render, (screen_w // 2 - wave_render.get_width() // 2, 8))

            # 적 수 표시
            current_enemies = len([e for e in self.enemies if e.is_alive])
            max_enemies = self.spawn_manager.max_enemies
            enemy_text = info_font.render(f"Enemies: {current_enemies} / {max_enemies}", True, (200, 200, 200))
            screen.blit(enemy_text, (screen_w // 2 - enemy_text.get_width() // 2, 28))

        # 하단 조작 안내 (SPACE, E, A 제거됨)
        help_bg = pygame.Surface((screen_w, 35), pygame.SRCALPHA)
        help_bg.fill((0, 0, 0, 150))
        screen.blit(help_bg, (0, screen_h - 35))

        small_font = self.fonts.get("small", pygame.font.Font(None, 20))
        controls = "[S] Skills  [R] Reset  [H] Help  [ESC] Exit"
        ctrl_text = small_font.render(controls, True, (180, 180, 180))
        screen.blit(ctrl_text, (screen_w // 2 - ctrl_text.get_width() // 2, screen_h - 28))

    def _render_static_field(self, screen: pygame.Surface):
        """Static Field 시각 효과 렌더링 - 강화된 전기장 효과"""
        if not self.player or not getattr(self.player, 'has_static_field', False):
            return

        # Static Field 설정값 가져오기
        static_settings = config.ATTRIBUTE_SKILL_SETTINGS.get("STATIC_FIELD", {})
        radius = static_settings.get("radius", 180)

        player_x = int(self.player.pos.x)
        player_y = int(self.player.pos.y)

        # 시간 기반 펄스 효과 (더 빠르고 강하게)
        current_time = pygame.time.get_ticks() / 1000.0
        pulse = 0.6 + 0.4 * math.sin(current_time * 5)  # 더 강한 펄싱

        # 큰 외곽 글로우 (더 밝고 넓게)
        for i in range(5):
            glow_radius = int(radius + 20 - i * 15)
            alpha = int(80 * pulse * (1 - i * 0.15))
            glow_surface = pygame.Surface((glow_radius * 2 + 10, glow_radius * 2 + 10), pygame.SRCALPHA)
            # 밝은 청록색
            color = (50, 255, 255, alpha)
            pygame.draw.circle(glow_surface, color, (glow_radius + 5, glow_radius + 5), glow_radius)
            screen.blit(glow_surface, (player_x - glow_radius - 5, player_y - glow_radius - 5))

        # 메인 원형 테두리 (두껍고 밝게)
        border_alpha = int(220 * pulse)
        border_surface = pygame.Surface((radius * 2 + 20, radius * 2 + 20), pygame.SRCALPHA)
        pygame.draw.circle(border_surface, (100, 255, 255, border_alpha),
                          (radius + 10, radius + 10), radius, 5)
        # 더 밝은 내부 테두리
        pygame.draw.circle(border_surface, (200, 255, 255, border_alpha),
                          (radius + 10, radius + 10), radius, 2)
        screen.blit(border_surface, (player_x - radius - 10, player_y - radius - 10))

        # 전기 아크 효과 (번개 선)
        num_arcs = 12
        for i in range(num_arcs):
            arc_angle = (current_time * 3 + i * (2 * math.pi / num_arcs)) % (2 * math.pi)
            # 시작점 (플레이어 근처)
            start_r = 30
            start_x = player_x + int(math.cos(arc_angle) * start_r)
            start_y = player_y + int(math.sin(arc_angle) * start_r)
            # 끝점 (테두리 근처)
            end_r = radius * (0.85 + 0.15 * math.sin(current_time * 8 + i * 2))
            end_x = player_x + int(math.cos(arc_angle + math.sin(current_time * 6 + i) * 0.3) * end_r)
            end_y = player_y + int(math.sin(arc_angle + math.sin(current_time * 6 + i) * 0.3) * end_r)

            # 번개 선 (굵은 글로우 + 얇은 코어)
            arc_alpha = int(180 * pulse)
            pygame.draw.line(screen, (50, 200, 255), (start_x, start_y), (end_x, end_y), 3)
            pygame.draw.line(screen, (200, 255, 255), (start_x, start_y), (end_x, end_y), 1)

        # 회전하는 전기 파티클 (더 크고 많이)
        num_particles = 16
        for i in range(num_particles):
            angle = (current_time * 2.5 + i * (2 * math.pi / num_particles)) % (2 * math.pi)
            particle_r = radius * (0.5 + 0.4 * math.sin(current_time * 4 + i * 0.7))
            px = player_x + int(math.cos(angle) * particle_r)
            py = player_y + int(math.sin(angle) * particle_r)
            particle_alpha = int(255 * pulse)
            # 더 큰 파티클
            size = 8 + int(4 * math.sin(current_time * 7 + i))
            particle_surface = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            pygame.draw.circle(particle_surface, (150, 255, 255, particle_alpha), (size, size), size)
            pygame.draw.circle(particle_surface, (255, 255, 255, particle_alpha), (size, size), size // 2)
            screen.blit(particle_surface, (px - size, py - size))

    def _render_regeneration_effect(self, screen: pygame.Surface):
        """Regeneration 시각 효과 - 강화된 힐링 이펙트"""
        if not self.player or self.player.regeneration_rate <= 0:
            return

        player_x = int(self.player.pos.x)
        player_y = int(self.player.pos.y)

        current_time = pygame.time.get_ticks() / 1000.0
        pulse = 0.6 + 0.4 * math.sin(current_time * 3)

        # 큰 녹색 힐링 오라 (여러 레이어)
        for layer in range(3):
            aura_radius = 50 + layer * 15
            aura_alpha = int(60 * pulse * (1 - layer * 0.25))
            aura_surf = pygame.Surface((aura_radius * 2 + 10, aura_radius * 2 + 10), pygame.SRCALPHA)
            pygame.draw.circle(aura_surf, (50, 255, 100, aura_alpha),
                             (aura_radius + 5, aura_radius + 5), aura_radius)
            screen.blit(aura_surf, (player_x - aura_radius - 5, player_y - aura_radius - 5))

        # 빛나는 테두리
        border_alpha = int(180 * pulse)
        border_surf = pygame.Surface((110, 110), pygame.SRCALPHA)
        pygame.draw.circle(border_surf, (100, 255, 150, border_alpha), (55, 55), 50, 3)
        screen.blit(border_surf, (player_x - 55, player_y - 55))

        # 위로 올라가는 힐링 파티클 (더 많고 크게)
        num_particles = 12
        for i in range(num_particles):
            phase = (current_time * 2.0 + i * 0.25) % 2.0
            if phase < 1.8:
                # 나선형으로 올라가는 효과
                spiral_angle = phase * 3 + i * 0.5
                offset_x = math.sin(spiral_angle) * (20 + phase * 10)
                offset_y = -phase * 60  # 위로 이동
                px = player_x + int(offset_x)
                py = player_y + int(offset_y)

                # 투명도
                if phase < 0.3:
                    alpha = int(255 * (phase / 0.3))
                elif phase > 1.5:
                    alpha = int(255 * (1.8 - phase) / 0.3)
                else:
                    alpha = 255

                # 더 큰 녹색 힐링 파티클 + 십자가 모양
                size = 8 + int(4 * math.sin(current_time * 6 + i))
                particle_surf = pygame.Surface((size * 2 + 4, size * 2 + 4), pygame.SRCALPHA)
                # 원형 글로우
                pygame.draw.circle(particle_surf, (50, 255, 100, alpha // 2), (size + 2, size + 2), size + 2)
                # 십자가 (힐링 심볼)
                pygame.draw.line(particle_surf, (200, 255, 200, alpha),
                               (size + 2, 2), (size + 2, size * 2 + 2), 2)
                pygame.draw.line(particle_surf, (200, 255, 200, alpha),
                               (2, size + 2), (size * 2 + 2, size + 2), 2)
                screen.blit(particle_surf, (px - size - 2, py - size - 2))

        # "HEAL" 텍스트 효과 (주기적으로)
        text_phase = (current_time * 0.5) % 1.0
        if text_phase < 0.3:
            text_alpha = int(200 * (1 - text_phase / 0.3))
            font = self.fonts.get("medium", self.fonts["small"])
            heal_text = font.render("+HP", True, (100, 255, 100))
            heal_surf = heal_text.copy()
            heal_surf.set_alpha(text_alpha)
            screen.blit(heal_surf, (player_x - heal_text.get_width() // 2, player_y - 70))

    def _render_phoenix_ready(self, screen: pygame.Surface):
        """Phoenix 준비 상태 시각 효과 - 강화된 불사조 화염 오라"""
        if not self.player:
            return
        if not getattr(self.player, 'has_phoenix_rebirth', False):
            return
        # 쿨다운 중이면 효과 감소
        cooldown = getattr(self.player, 'phoenix_cooldown', 0)
        if cooldown > 0:
            return  # 쿨다운 중이면 효과 없음

        player_x = int(self.player.pos.x)
        player_y = int(self.player.pos.y)

        current_time = pygame.time.get_ticks() / 1000.0
        pulse = 0.5 + 0.5 * math.sin(current_time * 5)

        # 큰 불꽃 오라 (여러 레이어)
        for layer in range(4):
            aura_radius = 60 + layer * 20
            # 주황-빨강 그라디언트
            r = min(255, 255 - layer * 20)
            g = max(50, 150 - layer * 40)
            aura_alpha = int(70 * pulse * (1 - layer * 0.2))
            aura_surf = pygame.Surface((aura_radius * 2 + 20, aura_radius * 2 + 20), pygame.SRCALPHA)
            pygame.draw.circle(aura_surf, (r, g, 0, aura_alpha),
                             (aura_radius + 10, aura_radius + 10), aura_radius)
            screen.blit(aura_surf, (player_x - aura_radius - 10, player_y - aura_radius - 10))

        # 불꽃 테두리 (밝은 주황)
        border_alpha = int(200 * pulse)
        border_surf = pygame.Surface((140, 140), pygame.SRCALPHA)
        pygame.draw.circle(border_surf, (255, 200, 50, border_alpha), (70, 70), 65, 4)
        pygame.draw.circle(border_surf, (255, 255, 100, border_alpha), (70, 70), 65, 2)
        screen.blit(border_surf, (player_x - 70, player_y - 70))

        # 회전하는 큰 불꽃 파티클
        num_flames = 16
        for i in range(num_flames):
            angle = (current_time * 2.5 + i * (2 * math.pi / num_flames)) % (2 * math.pi)
            radius = 55 + 20 * math.sin(current_time * 4 + i * 0.5)
            fx = player_x + int(math.cos(angle) * radius)
            fy = player_y + int(math.sin(angle) * radius)

            # 불꽃 크기와 색상 (주황-노랑-빨강)
            flame_size = 10 + int(6 * math.sin(current_time * 7 + i))
            flame_alpha = int(220 * pulse)

            flame_surf = pygame.Surface((flame_size * 2 + 8, flame_size * 2 + 8), pygame.SRCALPHA)
            # 외부 글로우 (주황)
            pygame.draw.circle(flame_surf, (255, 100, 0, flame_alpha // 2),
                             (flame_size + 4, flame_size + 4), flame_size + 4)
            # 중간 (밝은 주황)
            pygame.draw.circle(flame_surf, (255, 180, 50, flame_alpha),
                             (flame_size + 4, flame_size + 4), flame_size)
            # 코어 (노랑)
            pygame.draw.circle(flame_surf, (255, 255, 150, flame_alpha),
                             (flame_size + 4, flame_size + 4), flame_size // 2)
            screen.blit(flame_surf, (fx - flame_size - 4, fy - flame_size - 4))

        # 위로 올라가는 불꽃
        for i in range(8):
            phase = (current_time * 3 + i * 0.3) % 1.5
            if phase < 1.2:
                offset_x = math.sin(current_time * 4 + i * 1.5) * 30
                offset_y = -phase * 80
                fx = player_x + int(offset_x)
                fy = player_y + int(offset_y)

                alpha = int(200 * (1 - phase / 1.2))
                size = int(8 * (1 - phase / 1.5))
                if size > 0:
                    flame_surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
                    pygame.draw.circle(flame_surf, (255, 200, 50, alpha), (size, size), size)
                    screen.blit(flame_surf, (fx - size, fy - size))

        # "PHOENIX" 텍스트 (주기적)
        text_phase = (current_time * 0.3) % 1.0
        if text_phase < 0.2:
            text_alpha = int(180 * (1 - text_phase / 0.2))
            font = self.fonts.get("small", self.fonts["small"])
            text = font.render("PHOENIX READY", True, (255, 200, 100))
            text_surf = text.copy()
            text_surf.set_alpha(text_alpha)
            screen.blit(text_surf, (player_x - text.get_width() // 2, player_y + 60))

    def _render_active_skills(self, screen: pygame.Surface):
        """활성화된 스킬 패널 (화면 좌측) - 상세 정보 및 레벨 포함"""
        if not self.player:
            return

        # 스킬 정보 수집 (상세 정보 포함)
        skills_info = []

        if self.player.has_explosive:
            # config에서 설정값 가져오기
            settings = config.TRAINING_SKILL_SETTINGS.get("EXPLOSIVE", {})
            dmg_ratio = config.ATTRIBUTE_SKILL_SETTINGS.get("EXPLOSIVE", {}).get("damage_ratio", 0.5)
            level = self.skill_levels.get("explosive", 1)
            max_level = settings.get("max_level", 10)
            is_max = level >= max_level
            skills_info.append({
                "name": "Explosive Shot",
                "level": level,
                "max_level": max_level,
                "is_max": is_max,
                "color": (255, 100, 100),
                "icon": "💥",
                "details": [
                    f"Explosion Radius: {self.player.explosive_radius:.0f} px",
                    f"Explosion Damage: {dmg_ratio * 100:.0f}% of bullet",
                    "Trigger: Enemy killed by bullet",
                ],
                "next_level": f"+{settings.get('radius_per_level', 20)} radius" if not is_max else None
            })

        if self.player.has_lightning:
            settings = config.TRAINING_SKILL_SETTINGS.get("LIGHTNING", {})
            chain_range = config.ATTRIBUTE_SKILL_SETTINGS.get("LIGHTNING", {}).get("chain_range", 250)
            dmg_ratio = config.ATTRIBUTE_SKILL_SETTINGS.get("LIGHTNING", {}).get("damage_ratio", 0.7)
            level = self.skill_levels.get("lightning", 1)
            max_level = settings.get("max_level", 7)
            is_max = level >= max_level
            skills_info.append({
                "name": "Chain Lightning",
                "level": level,
                "max_level": max_level,
                "is_max": is_max,
                "color": (100, 200, 255),
                "icon": "⚡",
                "details": [
                    f"Chain Count: {self.player.lightning_chain_count}",
                    f"Chain Range: {chain_range} px",
                    f"Chain Damage: {dmg_ratio * 100:.0f}% of bullet",
                ],
                "next_level": f"+{settings.get('chain_per_level', 1)} chain" if not is_max else None
            })

        if self.player.has_frost:
            settings = config.TRAINING_SKILL_SETTINGS.get("FROST", {})
            frost_duration = settings.get("slow_duration", 2.0)
            freeze_duration = settings.get("freeze_duration", 1.5)
            level = self.skill_levels.get("frost", 1)
            max_level = settings.get("max_level", 5)
            is_max = level >= max_level
            skills_info.append({
                "name": "Frost Nova",
                "level": level,
                "max_level": max_level,
                "is_max": is_max,
                "color": (150, 220, 255),
                "icon": "❄️",
                "details": [
                    f"Slow: {self.player.frost_slow_ratio * 100:.0f}% ({frost_duration:.1f}s)",
                    f"Freeze: {self.player.freeze_chance * 100:.0f}% ({freeze_duration:.1f}s)",
                ],
                "next_level": f"+10% slow/freeze" if not is_max else None
            })

        if len(self.drones) > 0:
            settings = config.TRAINING_SKILL_SETTINGS.get("DRONE", {})
            drone_dmg = config.DRONE_SETTINGS.get("damage", 10)
            drone_range = config.DRONE_SETTINGS.get("shoot_range", 200)
            drone_cd = config.DRONE_SETTINGS.get("shoot_cooldown", 0.5)
            level = len(self.drones)
            max_level = settings.get("max_count", 5)
            is_max = level >= max_level
            skills_info.append({
                "name": "Attack Drone",
                "level": level,
                "max_level": max_level,
                "is_max": is_max,
                "color": (200, 200, 100),
                "icon": "🛸",
                "details": [
                    f"Damage: {drone_dmg} | Range: {drone_range}px",
                    f"Fire Rate: {1/drone_cd:.1f}/sec",
                ],
                "next_level": "+1 drone" if not is_max else None
            })

        if len(self.turrets) > 0:
            settings = config.TRAINING_SKILL_SETTINGS.get("TURRET", {})
            turret_dmg = config.TURRET_SETTINGS.get("damage", 15)
            turret_range = config.TURRET_SETTINGS.get("shoot_range", 250)
            turret_cd = config.TURRET_SETTINGS.get("shoot_cooldown", 0.8)
            turret_dur = config.TURRET_SETTINGS.get("duration", 30)
            level = len(self.turrets)
            max_level = settings.get("max_count", 3)
            is_max = level >= max_level
            skills_info.append({
                "name": "Auto Turret",
                "level": level,
                "max_level": max_level,
                "is_max": is_max,
                "color": (150, 150, 200),
                "icon": "🗼",
                "details": [
                    f"Damage: {turret_dmg} | Range: {turret_range}px",
                    f"Duration: {turret_dur}s",
                ],
                "next_level": "+1 turret" if not is_max else None
            })

        if self.player.regeneration_rate > 0:
            settings = config.TRAINING_SKILL_SETTINGS.get("REGENERATION", {})
            level = self.skill_levels.get("regeneration", 1)
            max_level = settings.get("max_level", 10)
            is_max = level >= max_level
            skills_info.append({
                "name": "Regeneration",
                "level": level,
                "max_level": max_level,
                "is_max": is_max,
                "color": (100, 255, 100),
                "icon": "💚",
                "details": [
                    f"Heal Rate: {self.player.regeneration_rate:.1f} HP/sec",
                    f"HP: {self.player.hp:.0f}/{self.player.max_hp:.0f}",
                ],
                "next_level": f"+{settings.get('rate_per_level', 2)} HP/s" if not is_max else None
            })

        # 추가 6개 스킬 표시
        if getattr(self.player, 'has_chain_explosion', False):
            level = self.skill_levels.get("chain_explosion", 1)
            skills_info.append({
                "name": "Chain Explosion",
                "level": level,
                "max_level": 3,
                "is_max": level >= 3,
                "color": (255, 150, 50),
                "icon": "💣",
                "details": [
                    f"Chain Chance: 30%",
                    f"Max Depth: 3",
                ],
                "next_level": None
            })

        if getattr(self.player, 'has_static_field', False):
            level = self.skill_levels.get("static_field", 1)
            radius = getattr(self.player, 'static_field_radius', 180)
            damage = getattr(self.player, 'static_field_damage', 10)
            skills_info.append({
                "name": "Static Field",
                "level": level,
                "max_level": 5,
                "is_max": level >= 5,
                "color": (100, 255, 255),
                "icon": "⚡",
                "details": [
                    f"Radius: {radius}px",
                    f"DPS: {damage}",
                ],
                "next_level": None
            })

        if getattr(self.player, 'has_deep_freeze', False):
            level = self.skill_levels.get("deep_freeze", 1)
            chance = getattr(self.player, 'deep_freeze_chance', 0.1)
            duration = getattr(self.player, 'deep_freeze_duration', 1.5)
            skills_info.append({
                "name": "Deep Freeze",
                "level": level,
                "max_level": 5,
                "is_max": level >= 5,
                "color": (220, 240, 255),
                "icon": "🧊",
                "details": [
                    f"Freeze Chance: {chance * 100:.0f}%",
                    f"Duration: {duration:.1f}s",
                ],
                "next_level": None
            })

        if getattr(self.player, 'has_execute', False):
            level = self.skill_levels.get("execute", 1)
            threshold = getattr(self.player, 'execute_threshold', 0.1)
            skills_info.append({
                "name": "Execute",
                "level": level,
                "max_level": 5,
                "is_max": level >= 5,
                "color": (200, 100, 255),
                "icon": "💀",
                "details": [
                    f"Threshold: {threshold * 100:.0f}% HP",
                    "Instant kill below threshold",
                ],
                "next_level": None
            })

        if getattr(self.player, 'has_starfall', False):
            level = self.skill_levels.get("starfall", 1)
            count = getattr(self.player, 'starfall_count', 5)
            cooldown = getattr(self.player, 'starfall_cooldown', 30)
            skills_info.append({
                "name": "Starfall",
                "level": level,
                "max_level": 5,
                "is_max": level >= 5,
                "color": (255, 215, 0),
                "icon": "⭐",
                "details": [
                    f"Star Count: {count}",
                    f"Cooldown: {cooldown:.0f}s",
                ],
                "next_level": None
            })

        if getattr(self.player, 'has_phoenix', False):
            level = self.skill_levels.get("phoenix", 1)
            revive_ratio = getattr(self.player, 'phoenix_revive_ratio', 0.5)
            cooldown = getattr(self.player, 'phoenix_cooldown', 60)
            skills_info.append({
                "name": "Phoenix Rebirth",
                "level": level,
                "max_level": 3,
                "is_max": level >= 3,
                "color": (255, 150, 50),
                "icon": "🔥",
                "details": [
                    f"Revive HP: {revive_ratio * 100:.0f}%",
                    f"Cooldown: {cooldown:.0f}s",
                ],
                "next_level": None
            })

        if not skills_info:
            # 스킬이 없을 때 안내 표시
            panel_x = 10
            panel_y = 70
            panel_w = 220
            panel_h = 80

            panel_bg = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
            panel_bg.fill((20, 30, 50, 180))
            pygame.draw.rect(panel_bg, (80, 80, 100), (0, 0, panel_w, panel_h), 1, border_radius=5)
            screen.blit(panel_bg, (panel_x, panel_y))

            title_font = self.fonts.get("small", pygame.font.Font(None, 20))
            title = title_font.render("NO ACTIVE SKILLS", True, (120, 120, 140))
            screen.blit(title, (panel_x + 10, panel_y + 10))

            hint_font = self.fonts.get("micro", self.fonts["small"])
            hints = ["Press S to open skill menu", "Or use keys 1-6 to add skills"]
            for i, hint in enumerate(hints):
                hint_text = hint_font.render(hint, True, (100, 100, 120))
                screen.blit(hint_text, (panel_x + 10, panel_y + 35 + i * 16))
            return

        # 패널 그리기
        panel_x = 10
        panel_y = 70  # 상단 바 아래
        panel_w = 250
        item_h = 80  # 카드 높이
        panel_h = len(skills_info) * item_h + 35

        # 반투명 배경
        panel_bg = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel_bg.fill((15, 25, 40, 220))
        pygame.draw.rect(panel_bg, (60, 100, 160), (0, 0, panel_w, panel_h), 2, border_radius=8)
        screen.blit(panel_bg, (panel_x, panel_y))

        # 제목
        title_font = self.fonts.get("medium", pygame.font.Font(None, 24))
        title = title_font.render("ACTIVE SKILLS", True, (100, 180, 255))
        screen.blit(title, (panel_x + 10, panel_y + 8))

        # 각 스킬 표시
        name_font = self.fonts.get("small", pygame.font.Font(None, 20))
        detail_font = self.fonts.get("micro", self.fonts["small"])
        level_font = self.fonts.get("micro", self.fonts["small"])

        y_offset = panel_y + 35
        for skill in skills_info:
            # 스킬 배경 (개별 카드)
            card_h = item_h - 6
            card_bg = pygame.Surface((panel_w - 16, card_h), pygame.SRCALPHA)
            card_bg.fill((30, 40, 60, 180))
            pygame.draw.rect(card_bg, skill["color"] + (100,), (0, 0, panel_w - 16, card_h), 1, border_radius=4)
            screen.blit(card_bg, (panel_x + 8, y_offset))

            # 스킬 이름 + 레벨 (색상 강조)
            level = skill.get("level", 1)
            max_level = skill.get("max_level", 10)
            is_max = skill.get("is_max", False)

            if is_max:
                level_str = " [MAX]"
                level_color = (255, 215, 0)  # 골드
            else:
                level_str = f" Lv.{level}/{max_level}"
                level_color = (180, 180, 180)

            name_text = name_font.render(skill["name"], True, skill["color"])
            screen.blit(name_text, (panel_x + 14, y_offset + 4))

            level_text = level_font.render(level_str, True, level_color)
            screen.blit(level_text, (panel_x + 14 + name_text.get_width(), y_offset + 6))

            # 세부 정보
            detail_y = y_offset + 22
            for detail in skill["details"]:
                detail_text = detail_font.render(detail, True, (200, 200, 200))
                screen.blit(detail_text, (panel_x + 16, detail_y))
                detail_y += 13

            # 다음 레벨 효과 표시 (하단, 녹색)
            next_level = skill.get("next_level")
            if next_level:
                next_text = level_font.render(f"Next: {next_level}", True, (150, 255, 150))
                screen.blit(next_text, (panel_x + 16, y_offset + card_h - 14))
            elif is_max:
                max_text = level_font.render("Maximum level reached!", True, (255, 215, 0))
                screen.blit(max_text, (panel_x + 16, y_offset + card_h - 14))

            y_offset += item_h

    def _render_help(self, screen: pygame.Surface):
        """도움말 렌더링"""
        screen_w, screen_h = self.screen_size

        # 반투명 배경
        overlay = pygame.Surface(self.screen_size, pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        screen.blit(overlay, (0, 0))

        # 도움말 패널
        panel_w, panel_h = 500, 400
        panel_x = screen_w // 2 - panel_w // 2
        panel_y = screen_h // 2 - panel_h // 2

        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel.fill((30, 40, 60, 240))
        pygame.draw.rect(panel, (100, 150, 255), (0, 0, panel_w, panel_h), 2, border_radius=10)
        screen.blit(panel, (panel_x, panel_y))

        # 제목
        title_font = self.fonts.get("large", pygame.font.Font(None, 36))
        title = title_font.render("TRAINING ROOM", True, (100, 200, 255))
        screen.blit(title, (panel_x + panel_w // 2 - title.get_width() // 2, panel_y + 20))

        # 설명
        help_font = self.fonts.get("medium", pygame.font.Font(None, 24))
        help_lines = [
            "",
            "Practice your skills without dying!",
            "",
            "Wave System:",
            "  - Enemies spawn automatically",
            "  - 5 waves with increasing difficulty",
            "  - Waves loop with harder enemies",
            "",
            "Controls:",
            "  S - Open skill menu (12 skills)",
            "  R - Reset all skills",
            "  H - Toggle this help",
            "  ESC - Return to base",
            "",
            "You are invincible in training mode.",
        ]

        y_offset = panel_y + 60
        for line in help_lines:
            if line:
                text = help_font.render(line, True, (220, 220, 220))
                screen.blit(text, (panel_x + 30, y_offset))
            y_offset += 25

    def _render_skill_menu(self, screen: pygame.Surface):
        """12개 스킬 선택 메뉴 렌더링 (4x3 그리드)"""
        screen_w, screen_h = self.screen_size

        # 반투명 배경
        overlay = pygame.Surface(self.screen_size, pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        # 스킬 패널 크기
        panel_w, panel_h = 800, 600
        panel_x = screen_w // 2 - panel_w // 2
        panel_y = screen_h // 2 - panel_h // 2

        # 배경 이미지 또는 기본 배경
        if self.skill_menu_bg:
            screen.blit(self.skill_menu_bg, (panel_x, panel_y))
            # 배경 위에 반투명 오버레이
            bg_overlay = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
            bg_overlay.fill((0, 0, 0, 120))
            screen.blit(bg_overlay, (panel_x, panel_y))
        else:
            panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
            panel.fill((30, 40, 60, 240))
            screen.blit(panel, (panel_x, panel_y))

        # 테두리
        pygame.draw.rect(screen, (100, 200, 100), (panel_x, panel_y, panel_w, panel_h), 3, border_radius=10)

        # 제목
        title_font = self.fonts.get("huge", pygame.font.Font(None, 48))
        title = title_font.render("SKILL ARSENAL", True, (255, 215, 0))
        screen.blit(title, (panel_x + panel_w // 2 - title.get_width() // 2, panel_y + 15))

        # 그리드 설정 (4x3)
        grid_cols = 4
        grid_rows = 3
        card_w = 175
        card_h = 120
        card_margin_x = 12
        card_margin_y = 10
        grid_start_x = panel_x + (panel_w - (card_w * grid_cols + card_margin_x * (grid_cols - 1))) // 2
        grid_start_y = panel_y + 60

        self.skill_buttons.clear()
        mouse_pos = pygame.mouse.get_pos()
        self.hovered_skill = None

        # 폰트
        name_font = self.fonts.get("medium", pygame.font.Font(None, 24))
        type_font = self.fonts.get("micro", self.fonts["small"])
        shortcut_font = self.fonts.get("tiny", self.fonts["small"])

        # 12개 스킬 렌더링
        for idx, skill_key in enumerate(config_training.SKILL_ORDER):
            skill_data = config_training.SKILL_DEFINITIONS.get(skill_key, {})
            col = idx % grid_cols
            row = idx // grid_cols

            card_x = grid_start_x + col * (card_w + card_margin_x)
            card_y = grid_start_y + row * (card_h + card_margin_y)
            card_rect = pygame.Rect(card_x, card_y, card_w, card_h)
            self.skill_buttons[skill_key] = card_rect

            # 선택 상태 확인
            is_selected = self.selected_skills.get(skill_key, False)
            is_hover = card_rect.collidepoint(mouse_pos)
            skill_color = skill_data.get("color", (150, 150, 150))

            if is_hover:
                self.hovered_skill = skill_key

            # 카드 배경
            card_surf = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
            if is_selected:
                # 선택된 상태: 스킬 색상 배경 + 글로우
                card_surf.fill((*skill_color, 80))
                pygame.draw.rect(card_surf, skill_color, (0, 0, card_w, card_h), 3, border_radius=8)
                # 글로우 효과
                glow_surf = pygame.Surface((card_w + 8, card_h + 8), pygame.SRCALPHA)
                pygame.draw.rect(glow_surf, (*skill_color, 60), (0, 0, card_w + 8, card_h + 8), border_radius=10)
                screen.blit(glow_surf, (card_x - 4, card_y - 4))
            elif is_hover:
                # 호버 상태
                card_surf.fill((60, 70, 90, 200))
                pygame.draw.rect(card_surf, skill_color, (0, 0, card_w, card_h), 2, border_radius=8)
            else:
                # 기본 상태
                card_surf.fill((40, 50, 70, 180))
                pygame.draw.rect(card_surf, (80, 90, 110), (0, 0, card_w, card_h), 1, border_radius=8)

            screen.blit(card_surf, card_rect)

            # 스킬 이름
            skill_name = skill_data.get("name", skill_key)
            name_color = skill_color if is_selected else (200, 200, 200)
            name_text = name_font.render(skill_name, True, name_color)
            screen.blit(name_text, (card_x + 10, card_y + 8))

            # 스킬 타입 (우측 상단)
            skill_type = skill_data.get("type", "")
            type_text = type_font.render(skill_type, True, (150, 150, 170))
            screen.blit(type_text, (card_x + card_w - type_text.get_width() - 8, card_y + 10))

            # 단축키 표시 (좌측 하단)
            shortcut = skill_data.get("shortcut", "")
            if shortcut:
                shortcut_text = shortcut_font.render(f"[{shortcut}]", True, (120, 120, 140))
                screen.blit(shortcut_text, (card_x + 8, card_y + card_h - 20))

            # 선택됨 표시 (체크마크)
            if is_selected:
                check_font = self.fonts.get("medium", self.fonts["small"])
                check_text = check_font.render("V", True, (100, 255, 100))
                screen.blit(check_text, (card_x + card_w - 22, card_y + card_h - 24))

                # 레벨 표시
                level = self.skill_levels.get(skill_key, 1)
                max_level = skill_data.get("max_level", 10)
                level_text = shortcut_font.render(f"Lv.{level}", True, (255, 215, 0))
                screen.blit(level_text, (card_x + card_w - 50, card_y + card_h - 20))

        # 호버된 스킬 상세 설명 (하단)
        desc_y = grid_start_y + grid_rows * (card_h + card_margin_y) + 10
        desc_bg = pygame.Surface((panel_w - 40, 80), pygame.SRCALPHA)
        desc_bg.fill((20, 30, 50, 200))
        pygame.draw.rect(desc_bg, (80, 100, 140), (0, 0, panel_w - 40, 80), 1, border_radius=5)
        screen.blit(desc_bg, (panel_x + 20, desc_y))

        if self.hovered_skill:
            skill_data = config_training.SKILL_DEFINITIONS.get(self.hovered_skill, {})
            desc_font = self.fonts.get("medium", pygame.font.Font(None, 24))
            detail_font = self.fonts.get("tiny", self.fonts["small"])

            # 스킬 이름 + 설명
            skill_name = skill_data.get("name", self.hovered_skill)
            skill_desc = skill_data.get("description", "")
            name_text = desc_font.render(f"{skill_name}: {skill_desc}", True, skill_data.get("color", (200, 200, 200)))
            screen.blit(name_text, (panel_x + 30, desc_y + 10))

            # 상세 정보
            details = skill_data.get("details", [])
            detail_x = panel_x + 30
            for i, detail in enumerate(details[:3]):  # 최대 3개
                detail_text = detail_font.render(detail, True, (180, 180, 180))
                screen.blit(detail_text, (detail_x, desc_y + 35 + i * 15))
                detail_x += detail_text.get_width() + 20
        else:
            hint_font = self.fonts.get("small", pygame.font.Font(None, 20))
            hint_text = hint_font.render("Hover over a skill to see details. Click to toggle selection.", True, (150, 150, 170))
            screen.blit(hint_text, (panel_x + panel_w // 2 - hint_text.get_width() // 2, desc_y + 30))

        # 하단 버튼
        btn_y = desc_y + 90
        btn_w = 120
        btn_h = 35
        btn_spacing = 20
        total_btn_w = btn_w * 3 + btn_spacing * 2
        btn_start_x = panel_x + (panel_w - total_btn_w) // 2

        self.menu_buttons.clear()

        # APPLY 버튼
        apply_rect = pygame.Rect(btn_start_x, btn_y, btn_w, btn_h)
        self.menu_buttons["apply"] = apply_rect
        apply_hover = apply_rect.collidepoint(mouse_pos)
        apply_color = (80, 200, 80) if apply_hover else (60, 150, 60)
        pygame.draw.rect(screen, apply_color, apply_rect, border_radius=5)
        pygame.draw.rect(screen, (100, 255, 100), apply_rect, 2, border_radius=5)
        apply_text = name_font.render("APPLY", True, (255, 255, 255))
        screen.blit(apply_text, (apply_rect.centerx - apply_text.get_width() // 2, apply_rect.centery - apply_text.get_height() // 2))

        # RESET 버튼
        reset_rect = pygame.Rect(btn_start_x + btn_w + btn_spacing, btn_y, btn_w, btn_h)
        self.menu_buttons["reset"] = reset_rect
        reset_hover = reset_rect.collidepoint(mouse_pos)
        reset_color = (200, 100, 80) if reset_hover else (150, 80, 60)
        pygame.draw.rect(screen, reset_color, reset_rect, border_radius=5)
        pygame.draw.rect(screen, (255, 120, 100), reset_rect, 2, border_radius=5)
        reset_text = name_font.render("RESET", True, (255, 255, 255))
        screen.blit(reset_text, (reset_rect.centerx - reset_text.get_width() // 2, reset_rect.centery - reset_text.get_height() // 2))

        # CLOSE 버튼
        close_rect = pygame.Rect(btn_start_x + (btn_w + btn_spacing) * 2, btn_y, btn_w, btn_h)
        self.menu_buttons["close"] = close_rect
        close_hover = close_rect.collidepoint(mouse_pos)
        close_color = (100, 100, 120) if close_hover else (70, 70, 90)
        pygame.draw.rect(screen, close_color, close_rect, border_radius=5)
        pygame.draw.rect(screen, (150, 150, 170), close_rect, 2, border_radius=5)
        close_text = name_font.render("CLOSE", True, (200, 200, 200))
        screen.blit(close_text, (close_rect.centerx - close_text.get_width() // 2, close_rect.centery - close_text.get_height() // 2))

    def handle_event(self, event: pygame.event.Event):
        """이벤트 처리"""
        if event.type == pygame.KEYDOWN:
            # ESC 키는 Training Mode에서 특별 처리 (기지 복귀)
            if event.key == pygame.K_ESCAPE:
                # 메뉴가 열려있으면 메뉴 닫기
                if self.show_skill_menu or self.show_help:
                    self.show_skill_menu = False
                    self.show_help = False
                else:
                    # 기지로 복귀
                    self._return_to_base()
                return

            # 스킬 메뉴 열기/닫기
            if event.key == pygame.K_s:
                self.show_skill_menu = not self.show_skill_menu
                self.show_help = False
                return

            # 도움말 토글
            if event.key == pygame.K_h:
                self.show_help = not self.show_help
                self.show_skill_menu = False
                return

            # 메뉴가 열려있을 때는 다른 입력 무시
            if self.show_skill_menu or self.show_help:
                return

            # P: 일시정지
            if event.key == pygame.K_p:
                current_state = self.game_data.get("game_state", config.GAME_STATE_RUNNING)
                if current_state == config.GAME_STATE_RUNNING:
                    self.game_data["game_state"] = config.GAME_STATE_PAUSED
                elif current_state == config.GAME_STATE_PAUSED:
                    self.game_data["game_state"] = config.GAME_STATE_RUNNING
                return

            # 스킬 리셋
            if event.key == pygame.K_r:
                self._reset_all_skills()

            # 숫자키로 스킬 토글 (1~0, -, = 키)
            elif event.key in [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5, pygame.K_6,
                               pygame.K_7, pygame.K_8, pygame.K_9, pygame.K_0, pygame.K_MINUS, pygame.K_EQUALS]:
                skill_index = self._key_to_skill_index(event.key)
                if skill_index is not None:
                    self._toggle_skill_by_index(skill_index)

        # 마우스 클릭
        elif event.type == pygame.MOUSEBUTTONDOWN:
            # 스킬 메뉴에서 클릭
            if self.show_skill_menu and event.button == 1:
                mouse_pos = event.pos
                # 스킬 버튼 클릭 처리
                for skill_name, rect in self.skill_buttons.items():
                    if rect.collidepoint(mouse_pos):
                        self._toggle_skill(skill_name)
                        return
                # 메뉴 버튼 클릭 처리
                if "apply" in self.menu_buttons and self.menu_buttons["apply"].collidepoint(mouse_pos):
                    self._apply_selected_skills()
                    self.show_skill_menu = False
                    return
                if "reset" in self.menu_buttons and self.menu_buttons["reset"].collidepoint(mouse_pos):
                    self._reset_skill_selection()
                    return
                if "close" in self.menu_buttons and self.menu_buttons["close"].collidepoint(mouse_pos):
                    self.show_skill_menu = False
                    return

            # 메뉴가 없을 때만 게임 플레이 마우스 처리
            if not self.show_skill_menu and not self.show_help:
                self.handle_mouse_click(event)

    def _add_skill(self, skill_name: str):
        """스킬 추가 - config에서 설정값을 읽어 Player 속성 설정"""
        if not self.player:
            return

        import math
        settings = config.TRAINING_SKILL_SETTINGS.get(skill_name.upper(), {})

        if skill_name == "explosive":
            max_level = settings.get("max_level", 10)
            if self.skill_levels["explosive"] >= max_level:
                print(f"INFO: Explosive is at MAX level ({max_level})")
                return

            self.skill_levels["explosive"] += 1
            level = self.skill_levels["explosive"]

            if level == 1:
                self.player.has_explosive = True
                self.player.explosive_radius = settings.get("base_radius", 100)
            else:
                self.player.explosive_radius = min(
                    self.player.explosive_radius + settings.get("radius_per_level", 20),
                    settings.get("max_radius", 300)
                )

            self._show_skill_activation("Explosive Shot", level, (255, 100, 100))
            print(f"INFO: Explosive Lv.{level} - Radius: {self.player.explosive_radius}")

        elif skill_name == "lightning":
            max_level = settings.get("max_level", 7)
            if self.skill_levels["lightning"] >= max_level:
                print(f"INFO: Lightning is at MAX level ({max_level})")
                return

            self.skill_levels["lightning"] += 1
            level = self.skill_levels["lightning"]

            if level == 1:
                self.player.has_lightning = True
                self.player.lightning_chain_count = settings.get("base_chain_count", 3)
            else:
                self.player.lightning_chain_count = min(
                    self.player.lightning_chain_count + settings.get("chain_per_level", 1),
                    settings.get("max_chains", 10)
                )

            self._show_skill_activation("Chain Lightning", level, (100, 200, 255))
            print(f"INFO: Lightning Lv.{level} - Chains: {self.player.lightning_chain_count}")

        elif skill_name == "frost":
            max_level = settings.get("max_level", 5)
            if self.skill_levels["frost"] >= max_level:
                print(f"INFO: Frost is at MAX level ({max_level})")
                return

            self.skill_levels["frost"] += 1
            level = self.skill_levels["frost"]

            if level == 1:
                self.player.has_frost = True
                self.player.frost_slow_ratio = settings.get("base_slow_ratio", 0.3)
                self.player.freeze_chance = settings.get("base_freeze_chance", 0.1)
            else:
                self.player.frost_slow_ratio = min(
                    self.player.frost_slow_ratio + settings.get("slow_per_level", 0.1),
                    settings.get("max_slow_ratio", 0.7)
                )
                self.player.freeze_chance = min(
                    self.player.freeze_chance + settings.get("freeze_per_level", 0.1),
                    settings.get("max_freeze_chance", 0.5)
                )

            self._show_skill_activation("Frost Nova", level, (150, 220, 255))
            print(f"INFO: Frost Lv.{level} - Slow: {self.player.frost_slow_ratio:.0%}, Freeze: {self.player.freeze_chance:.0%}")

        elif skill_name == "drone":
            max_count = settings.get("max_count", 5)
            if len(self.drones) >= max_count:
                print(f"INFO: Drone is at MAX count ({max_count})")
                return

            self.skill_levels["drone"] += 1
            level = self.skill_levels["drone"]

            # 드론 생성 - 궤도 각도 계산
            orbit_angle = len(self.drones) * (2 * math.pi / max(1, len(self.drones) + 1))
            drone = Drone(self.player, orbit_angle)
            self.drones.append(drone)
            self.player.drone_count = len(self.drones)

            self._show_skill_activation("Attack Drone", level, (200, 200, 100))
            print(f"INFO: Drone Lv.{level} - Total: {len(self.drones)}")

        elif skill_name == "turret":
            max_count = settings.get("max_count", 3)
            if len(self.turrets) >= max_count:
                print(f"INFO: Turret is at MAX count ({max_count})")
                return

            self.skill_levels["turret"] += 1
            level = self.skill_levels["turret"]

            # 터렛 생성 - 플레이어 위치 근처에 배치
            angle = len(self.turrets) * (math.pi / 3)  # 60도씩 간격
            distance = 100
            turret_x = self.player.pos.x + math.cos(angle) * distance
            turret_y = self.player.pos.y + math.sin(angle) * distance
            turret = Turret((turret_x, turret_y))
            self.turrets.append(turret)
            self.player.turret_count = len(self.turrets)

            self._show_skill_activation("Auto Turret", level, (150, 150, 200))
            print(f"INFO: Turret Lv.{level} - Total: {len(self.turrets)}")

        elif skill_name == "regeneration":
            max_level = settings.get("max_level", 10)
            if self.skill_levels["regeneration"] >= max_level:
                print(f"INFO: Regeneration is at MAX level ({max_level})")
                return

            self.skill_levels["regeneration"] += 1
            level = self.skill_levels["regeneration"]

            if level == 1:
                self.player.regeneration_rate = settings.get("base_rate", 2.0)
            else:
                self.player.regeneration_rate = min(
                    self.player.regeneration_rate + settings.get("rate_per_level", 2.0),
                    settings.get("max_rate", 20.0)
                )

            self._show_skill_activation("Regeneration", level, (100, 255, 100))
            print(f"INFO: Regeneration Lv.{level} - Rate: {self.player.regeneration_rate} HP/sec")

    def _show_skill_activation(self, skill_name: str, level: int, color: tuple):
        """스킬 활성화 효과 표시"""
        self.skill_activation_queue.append({
            "name": skill_name,
            "level": level,
            "color": color,
            "timer": 1.5,  # 1.5초 표시
            "alpha": 255,
        })

    def _reset_all_skills(self):
        """모든 스킬 초기화 (12개 스킬 지원)"""
        if not self.player:
            return

        # 플레이어 스킬 속성 초기화 - 기존 6개
        self.player.has_explosive = False
        self.player.explosive_radius = 0
        self.player.has_lightning = False
        self.player.lightning_chain_count = 0
        self.player.has_frost = False
        self.player.frost_slow_ratio = 0
        self.player.freeze_chance = 0
        self.player.regeneration_rate = 0
        self.player.drone_count = 0
        self.player.turret_count = 0

        # 추가 6개 스킬 초기화
        self.player.has_chain_explosion = False
        self.player.chain_explosion_depth = 0
        self.player.chain_explosion_chance = 0

        self.player.has_static_field = False
        self.player.static_field_radius = 0
        self.player.static_field_damage = 0

        self.player.has_deep_freeze = False
        self.player.deep_freeze_chance = 0
        self.player.deep_freeze_duration = 0

        self.player.has_execute = False
        self.player.execute_threshold = 0

        self.player.has_starfall = False
        self.player.starfall_count = 0
        self.player.starfall_cooldown = 0
        self.player.starfall_timer = 0

        self.player.has_phoenix = False
        self.player.phoenix_revive_ratio = 0
        self.player.phoenix_cooldown = 0
        self.player.phoenix_timer = 0

        # 드론/터렛 제거
        self.drones.clear()
        self.turrets.clear()

        # 스킬 레벨 초기화
        self.skill_levels = {skill: 0 for skill in config_training.SKILL_ORDER}

        # 선택 상태도 초기화
        self.selected_skills = {skill: False for skill in config_training.SKILL_ORDER}

        # 알림 표시
        self.skill_activation_queue.append({
            "name": "SKILLS RESET",
            "level": 0,
            "color": (255, 255, 255),
            "timer": 1.5,
            "alpha": 255,
        })

        print("INFO: All skills have been reset")

    def _add_skill_by_index(self, index: int):
        """인덱스로 스킬 추가"""
        skills = ["explosive", "lightning", "frost", "drone", "turret", "regeneration"]
        if 0 <= index < len(skills):
            self._add_skill(skills[index])

    def _render_skill_activation(self, screen: pygame.Surface):
        """스킬 활성화 효과 렌더링 (화면 상단 중앙)"""
        if not self.skill_activation_queue:
            return

        screen_w, screen_h = self.screen_size
        y_offset = 80  # 상단 바 아래에서 시작

        for effect in self.skill_activation_queue:
            # 표시할 텍스트 생성
            if effect["level"] > 0:
                text = f"{effect['name']} Lv.{effect['level']}"
            else:
                text = effect["name"]

            # 폰트 및 색상
            font = self.fonts.get("large", pygame.font.Font(None, 36))
            color = effect["color"]
            alpha = effect["alpha"]

            # 텍스트 렌더링
            text_surf = font.render(text, True, color)
            text_surf.set_alpha(alpha)

            # 화면 중앙 상단에 배치
            x = screen_w // 2 - text_surf.get_width() // 2
            screen.blit(text_surf, (x, y_offset))

            y_offset += 40

    def _return_to_base(self):
        """기지로 복귀"""
        print("INFO: Returning to Base Hub from Training")
        self.request_pop_mode()

    def _key_to_skill_index(self, key: int) -> Optional[int]:
        """키 코드를 스킬 인덱스로 변환"""
        key_mapping = {
            pygame.K_1: 0,  # explosive
            pygame.K_2: 1,  # chain_explosion
            pygame.K_3: 2,  # lightning
            pygame.K_4: 3,  # static_field
            pygame.K_5: 4,  # frost
            pygame.K_6: 5,  # deep_freeze
            pygame.K_7: 6,  # execute
            pygame.K_8: 7,  # starfall
            pygame.K_9: 8,  # drone
            pygame.K_0: 9,  # turret
            pygame.K_MINUS: 10,  # regeneration
            pygame.K_EQUALS: 11,  # phoenix
        }
        return key_mapping.get(key)

    def _toggle_skill_by_index(self, index: int):
        """인덱스로 스킬 토글 및 즉시 적용"""
        if 0 <= index < len(config_training.SKILL_ORDER):
            skill_name = config_training.SKILL_ORDER[index]
            self._toggle_skill(skill_name)
            # 숫자키로 토글할 때 즉시 적용
            self._apply_selected_skills()

    def _toggle_skill(self, skill_name: str):
        """스킬 선택 상태 토글 (트레이닝 모드에서는 모든 스킬 자유 선택)"""
        if skill_name not in self.selected_skills:
            return

        # 토글
        self.selected_skills[skill_name] = not self.selected_skills[skill_name]

        status = "selected" if self.selected_skills[skill_name] else "deselected"
        print(f"INFO: Skill {skill_name} {status}")

    def _reset_skill_selection(self):
        """스킬 선택 상태 초기화"""
        self.selected_skills = {skill: False for skill in config_training.SKILL_ORDER}
        print("INFO: Skill selection reset")

    def _reset_player_skills_only(self):
        """플레이어 스킬 속성만 초기화 (선택 상태는 유지)"""
        if not self.player:
            return

        # 플레이어 스킬 속성 초기화 - 기존 6개
        self.player.has_explosive = False
        self.player.explosive_radius = 0
        self.player.has_lightning = False
        self.player.lightning_chain_count = 0
        self.player.has_frost = False
        self.player.frost_slow_ratio = 0
        self.player.freeze_chance = 0
        self.player.regeneration_rate = 0
        self.player.drone_count = 0
        self.player.turret_count = 0

        # 추가 6개 스킬 초기화
        self.player.has_chain_explosion = False
        self.player.chain_explosion_depth = 0
        self.player.chain_explosion_chance = 0

        self.player.has_static_field = False
        self.player.static_field_radius = 0
        self.player.static_field_damage = 0

        self.player.has_deep_freeze = False
        self.player.deep_freeze_chance = 0
        self.player.deep_freeze_duration = 0

        self.player.has_execute = False
        self.player.execute_threshold = 0

        self.player.has_starfall = False
        self.player.starfall_count = 0
        self.player.starfall_cooldown = 0
        self.player.starfall_timer = 0

        self.player.has_phoenix = False
        self.player.phoenix_revive_ratio = 0
        self.player.phoenix_cooldown = 0
        self.player.phoenix_timer = 0

        # 드론/터렛 제거
        self.drones.clear()
        self.turrets.clear()

        # 스킬 레벨 초기화
        self.skill_levels = {skill: 0 for skill in config_training.SKILL_ORDER}

    def _apply_selected_skills(self):
        """선택된 스킬들을 플레이어에 적용"""
        if not self.player:
            return

        # 선택 상태 백업
        selected_backup = self.selected_skills.copy()

        # 먼저 모든 스킬 초기화 (플레이어 속성만)
        self._reset_player_skills_only()

        # 선택 상태 복원
        self.selected_skills = selected_backup

        # 선택된 스킬들 적용
        applied_count = 0
        for skill_name, is_selected in self.selected_skills.items():
            if is_selected:
                self._apply_skill(skill_name)
                applied_count += 1

        if applied_count > 0:
            self.skill_activation_queue.append({
                "name": f"{applied_count} SKILLS APPLIED",
                "level": 0,
                "color": (100, 255, 100),
                "timer": 1.5,
                "alpha": 255,
            })
            print(f"INFO: Applied {applied_count} skills")
        else:
            print("INFO: No skills selected to apply")

    def _apply_skill(self, skill_name: str):
        """개별 스킬 적용"""
        if not self.player:
            return

        import math

        # 스킬 레벨 1로 설정
        self.skill_levels[skill_name] = 1

        settings = config.TRAINING_SKILL_SETTINGS.get(skill_name.upper(), {})
        skill_data = config_training.SKILL_DEFINITIONS.get(skill_name, {})

        if skill_name == "explosive":
            self.player.has_explosive = True
            self.player.explosive_radius = settings.get("base_radius", 100)

        elif skill_name == "chain_explosion":
            # 연쇄 폭발 설정
            self.player.has_chain_explosion = True
            self.player.chain_explosion_depth = settings.get("max_chain_depth", 3)
            self.player.chain_explosion_chance = settings.get("chain_chance", 0.3)

        elif skill_name == "lightning":
            self.player.has_lightning = True
            self.player.lightning_chain_count = settings.get("base_chain_count", 3)

        elif skill_name == "static_field":
            # 정적 필드 설정
            self.player.has_static_field = True
            self.player.static_field_radius = settings.get("base_radius", 180)
            self.player.static_field_damage = settings.get("damage_per_tick", 10)

        elif skill_name == "frost":
            self.player.has_frost = True
            self.player.frost_slow_ratio = settings.get("base_slow_ratio", 0.3)
            self.player.freeze_chance = settings.get("base_freeze_chance", 0.1)

        elif skill_name == "deep_freeze":
            # 완전 동결 설정
            self.player.has_deep_freeze = True
            self.player.deep_freeze_chance = settings.get("base_chance", 0.1)
            self.player.deep_freeze_duration = settings.get("duration", 1.5)

        elif skill_name == "execute":
            # 처형 설정
            self.player.has_execute = True
            self.player.execute_threshold = settings.get("base_threshold", 0.1)

        elif skill_name == "starfall":
            # 별똥별 설정
            self.player.has_starfall = True
            self.player.starfall_count = settings.get("base_count", 5)
            self.player.starfall_cooldown = settings.get("cooldown", 30.0)
            self.player.starfall_timer = 0.0

        elif skill_name == "drone":
            # 드론 1개 생성
            orbit_angle = 0
            drone = Drone(self.player, orbit_angle)
            self.drones.append(drone)
            self.player.drone_count = len(self.drones)

        elif skill_name == "turret":
            # 터렛 1개 생성
            turret_x = self.player.pos.x + 100
            turret_y = self.player.pos.y
            turret = Turret((turret_x, turret_y))
            self.turrets.append(turret)
            self.player.turret_count = len(self.turrets)

        elif skill_name == "regeneration":
            self.player.regeneration_rate = settings.get("base_rate", 2.0)

        elif skill_name == "phoenix":
            # 피닉스 부활 설정
            self.player.has_phoenix = True
            self.player.phoenix_revive_ratio = settings.get("revive_hp_ratio", 0.5)
            self.player.phoenix_cooldown = settings.get("base_cooldown", 60.0)
            self.player.phoenix_timer = 0.0

        print(f"INFO: Applied skill: {skill_name}")
