# modes/combat_mode.py
"""
CombatMode - 통합 전투 모드

Episode 시스템에서 호출되는 전투 전담 모드입니다.
WaveMode의 검증된 구조를 기반으로 base_mode와 완벽 호환됩니다.

사용법:
    # EpisodeMode에서 호출
    self.engine.shared_state['combat_data'] = {
        'mode': 'story',  # story, wave, siege, endless
        'rounds': 3,      # 전투 라운드 수
        'enemies': ['scout', 'fighter'],  # 적 타입
        'boss': None,     # 보스 ID (있으면)
        'background': 'bg_ruins.jpg',
    }
    from modes.combat_mode import CombatMode
    self.request_push_mode(CombatMode)
"""

import pygame
import random
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass

import config
from modes.base_mode import GameMode, ModeConfig
from systems.combat_system import CombatSystem
from systems.skill_system import SkillSystem
from systems.effect_system import EffectSystem
from systems.spawn_system import SpawnSystem, SpawnConfig
from systems.ui_system import UISystem, UIConfig
from objects import (
    Player, Enemy, Bullet, ParallaxLayer, Meteor,
    BackgroundTransition, Drone, Turret, CombatMotionEffect
)
from asset_manager import AssetManager
from utils import (
    reset_game_data, start_wave, advance_to_next_wave, check_wave_clear,
    update_game_objects, handle_spawning, spawn_gem, generate_tactical_options,
    handle_tactical_upgrade, update_random_event, get_active_event_modifiers,
    get_next_level_threshold, auto_place_turrets, trigger_ship_ability,
)
from ui import (
    draw_hud, draw_pause_and_over_screens, draw_shop_screen,
    draw_tactical_menu, draw_wave_prepare_screen, draw_wave_clear_screen,
    draw_boss_health_bar, draw_victory_screen, draw_skill_indicators,
    draw_random_event_ui, draw_settings_menu,
)


@dataclass
class CombatConfig:
    """전투 설정"""
    mode: str = "story"  # story, wave, siege, endless
    rounds: int = 3  # 전투 라운드 수 (-1 for endless)
    enemies: List[str] = None  # 적 타입 리스트
    boss: Optional[str] = None  # 보스 ID
    background: str = ""  # 배경 이미지
    spawn_rate: float = 1.0  # 스폰 속도 배율
    difficulty: float = 1.0  # 난이도 배율


class CombatMode(GameMode):
    """
    통합 전투 모드

    Episode 시스템에서 전투 세그먼트를 처리합니다.
    WaveMode의 검증된 구조를 기반으로 base_mode와 완벽 호환됩니다.
    """

    def get_config(self) -> ModeConfig:
        """전투 모드 설정"""
        return ModeConfig(
            mode_name="combat",
            perspective_enabled=True,
            perspective_apply_to_player=True,
            perspective_apply_to_enemies=True,
            perspective_apply_to_bullets=True,
            perspective_apply_to_gems=True,
            player_speed_multiplier=1.0,
            player_start_pos=(self.screen_size[0] // 2, int(self.screen_size[1] * 0.7)),
            player_afterimages_enabled=True,
            background_type="static",
            parallax_enabled=True,
            meteor_enabled=False,
            show_wave_ui=True,
            show_stage_ui=False,
            show_minimap=False,
            show_skill_indicators=True,
            wave_system_enabled=True,
            spawn_system_enabled=True,
            random_events_enabled=False,
            asset_prefix="combat",
        )

    def init(self):
        """전투 모드 초기화"""
        config.GAME_MODE = "combat"

        # 전투 설정 로드
        self._load_combat_config()

        # 시스템 초기화
        self.combat_system = CombatSystem()
        self.skill_system = SkillSystem()
        self.effect_system = EffectSystem()
        self.spawn_system = SpawnSystem(SpawnConfig(
            enemy_spawn_interval=1.0 / self.combat_config.spawn_rate,
            enemy_spawn_count=1,
            boss_enabled=self.combat_config.boss is not None,
        ))
        self.ui_system = UISystem(UIConfig(
            show_hp_bar=True,
            show_score=True,
            show_wave_info=True,
            show_level_info=True,
            show_skill_indicators=True,
        ))

        # 게임 데이터 초기화
        self.game_data = reset_game_data()
        self.game_data['score'] = self.engine.shared_state.get('global_score', 0)
        self.game_data['game_state'] = config.GAME_STATE_WAVE_PREPARE

        # 전투 상태
        self.current_round = 0  # 현재 라운드 (0-indexed)
        self.total_rounds = self.combat_config.rounds
        self.combat_state = "prepare"  # prepare, fighting, round_clear, victory, defeat
        self.round_kills = 0
        self.round_target_kills = 10  # 라운드 클리어 조건

        # 플레이어 생성 (base_mode의 spawn_player 사용)
        # 참고: base_mode에서 self.bullets, self.enemies, self.gems, self.effects 이미 초기화됨
        self.spawn_player(
            pos=self.config.player_start_pos,
            upgrades=self.engine.shared_state.get('player_upgrades', {})
        )

        # 패럴랙스 배경
        self._init_parallax_layers()

        # 배경 이미지 로드
        self._load_background()

        # 설정 메뉴 관련
        self.settings_bars = {}
        self.dragging_bgm = False
        self.dragging_sfx = False
        self.menu_button_rects: Dict[str, pygame.Rect] = {}

        # 전투 모션 효과
        self.combat_motion_effect = CombatMotionEffect(self.screen_size)
        self.player_prev_pos = None

        # 시각적 피드백 효과 (base_mode의 공통 메서드 사용)
        self._init_visual_feedback_effects()

        # 스폰 타이머
        self._spawn_timer = 0.0
        self._prepare_timer = 0.0
        self._clear_timer = 0.0
        self._victory_timer = 0.0

        print(f"INFO: CombatMode initialized - mode: {self.combat_config.mode}, rounds: {self.total_rounds}")

    def _load_combat_config(self):
        """shared_state에서 전투 설정 로드"""
        combat_data = self.engine.shared_state.get("combat_data", {})

        enemies = combat_data.get("enemies")
        if enemies is None:
            enemies = ["scout", "fighter"]

        self.combat_config = CombatConfig(
            mode=combat_data.get("mode", "story"),
            rounds=combat_data.get("rounds", 3),
            enemies=enemies,
            boss=combat_data.get("boss"),
            background=combat_data.get("background", ""),
            spawn_rate=combat_data.get("spawn_rate", 1.0),
            difficulty=combat_data.get("difficulty", 1.0),
        )

    def _init_parallax_layers(self):
        """패럴랙스 레이어 초기화"""
        self.parallax_layers = []
        for layer_config in config.PARALLAX_LAYERS:
            layer = ParallaxLayer(
                screen_size=self.screen_size,
                star_count=layer_config["star_count"],
                speed_factor=layer_config["speed_factor"],
                star_size=layer_config["star_size"],
                color=layer_config["color"],
                twinkle=layer_config.get("twinkle", False)
            )
            self.parallax_layers.append(layer)

    def _load_background(self):
        """배경 이미지 로드"""
        self.story_background = None

        if not self.combat_config.background:
            # 기본 배경
            self._create_default_background()
            return

        # 여러 경로 시도
        from pathlib import Path
        paths = [
            config.ASSET_DIR / "story_mode" / "backgrounds" / self.combat_config.background,
            config.ASSET_DIR / "images" / "backgrounds" / self.combat_config.background,
        ]

        for path in paths:
            if path.exists():
                try:
                    img = pygame.image.load(str(path)).convert()
                    self.story_background = pygame.transform.scale(img, self.screen_size)
                    print(f"INFO: Combat background loaded: {path}")
                    return
                except Exception as e:
                    print(f"WARNING: Failed to load background {path}: {e}")

        # 폴백
        self._create_default_background()

    def _create_default_background(self):
        """기본 그라데이션 배경 생성"""
        self.story_background = pygame.Surface(self.screen_size)
        for y in range(self.screen_size[1]):
            ratio = y / self.screen_size[1]
            r = int(10 + 20 * ratio)
            g = int(15 + 25 * ratio)
            b = int(30 + 40 * ratio)
            pygame.draw.line(self.story_background, (r, g, b), (0, y), (self.screen_size[0], y))

    # =========================================================
    # 게임 루프 - WaveMode 패턴 준수
    # =========================================================

    def update(self, dt: float, current_time: float):
        """전투 모드 업데이트 - base_mode 상속 패턴 준수"""
        # 공통 업데이트 (타임스케일, 화면 흔들림, 이펙트) - base_mode 메서드
        scaled_dt = self.update_common(dt, current_time)

        # 패럴랙스 배경 업데이트 (항상)
        for layer in self.parallax_layers:
            layer.update(dt)

        # 전투 상태별 업데이트
        if self.combat_state == "prepare":
            self._update_prepare(dt)
        elif self.combat_state == "fighting":
            self._update_fighting(scaled_dt, current_time)
        elif self.combat_state == "round_clear":
            self._update_round_clear(dt)
        elif self.combat_state == "victory":
            self._update_victory(dt)
        elif self.combat_state == "defeat":
            self._update_defeat(dt)

        # 전투 모션 효과 업데이트
        if self.combat_motion_effect:
            self.combat_motion_effect.update(dt)

    def _update_prepare(self, dt: float):
        """전투 준비 상태 업데이트"""
        self._prepare_timer += dt
        if self._prepare_timer >= 1.5:
            self._start_round()

    def _update_fighting(self, dt: float, current_time: float):
        """전투 중 업데이트 - WaveMode._update_running 패턴"""
        game_state = self.game_data.get("game_state", config.GAME_STATE_RUNNING)

        if game_state == config.GAME_STATE_PAUSED:
            return

        if game_state == config.GAME_STATE_OVER:
            self.combat_state = "defeat"
            return

        # 플레이어 업데이트 - base_mode 메서드 사용
        self.update_player(dt, current_time)

        # 타겟팅 시스템 업데이트 - base_mode 메서드
        self.update_targeting(dt)

        # 객체 업데이트 (터렛, 드론, 총알) - base_mode 메서드
        self.update_objects(dt)

        # HP 변화 감지를 위해 이전 HP 저장
        hp_before = self.player.hp if self.player else 0

        # 게임 객체 충돌 및 업데이트 - WaveMode와 동일한 시그니처
        update_game_objects(
            self.player, self.enemies, self.bullets, self.gems,
            self.effects, self.screen_size, dt, current_time,
            self.game_data,
            damage_numbers=None,  # deprecated
            damage_number_manager=self.damage_number_manager,
            screen_shake=self.screen_shake,
            sound_manager=self.sound_manager,
            death_effect_manager=self.death_effect_manager
        )

        # HP 감소 감지 → 피격 효과 트리거 (base_mode 공통 메서드)
        self._trigger_damage_feedback(hp_before)

        # 시각적 피드백 효과 업데이트 (base_mode 공통 메서드)
        self._update_visual_feedback(dt)

        # 전투 모션 효과 (플레이어 이동 추적)
        self._update_combat_motion_effect(dt)

        # 적 스폰
        self._update_enemy_spawn(dt, current_time)

        # 킬 카운트 업데이트
        self._update_kill_count()

        # 라운드 클리어 체크
        self._check_round_clear()

        # 플레이어 사망 체크
        self._check_player_death()

    def _update_combat_motion_effect(self, dt: float):
        """전투 모션 효과 업데이트 (플레이어 이동 추적)"""
        if not self.player:
            return

        is_moving = False
        move_direction = None

        if self.player_prev_pos is not None:
            dx = self.player.pos.x - self.player_prev_pos[0]
            dy = self.player.pos.y - self.player_prev_pos[1]
            is_moving = (abs(dx) > 2 or abs(dy) > 2)
            if is_moving:
                move_direction = (dx, dy)

        self.player_prev_pos = (self.player.pos.x, self.player.pos.y)
        player_pos = (self.player.pos.x, self.player.pos.y)
        self.combat_motion_effect.update_player_movement(is_moving, dt, player_pos, move_direction)

    def _update_kill_count(self):
        """킬 카운트 업데이트 (죽은 적 수 계산)"""
        # game_data의 kill_count 변화 감지
        current_kills = self.game_data.get("kill_count", 0)
        if not hasattr(self, '_last_kill_count'):
            self._last_kill_count = 0

        new_kills = current_kills - self._last_kill_count
        if new_kills > 0:
            self.round_kills += new_kills
            self._last_kill_count = current_kills

    def _check_player_death(self):
        """플레이어 사망 체크"""
        if self.player and self.player.hp <= 0:
            self.game_data["game_state"] = config.GAME_STATE_OVER
            self.combat_state = "defeat"

    def _update_round_clear(self, dt: float):
        """라운드 클리어 상태 업데이트"""
        self._clear_timer += dt
        if self._clear_timer >= 2.0:
            # 다음 라운드 또는 승리
            self.current_round += 1
            if self.total_rounds > 0 and self.current_round >= self.total_rounds:
                self.combat_state = "victory"
            else:
                self._start_round()

    def _update_victory(self, dt: float):
        """승리 상태 업데이트"""
        self._victory_timer += dt
        if self._victory_timer >= 2.0:
            self._complete_combat(success=True)

    def _update_defeat(self, dt: float):
        """패배 상태 업데이트"""
        # 게임오버 화면 대기
        pass

    def _start_round(self):
        """라운드 시작"""
        self.combat_state = "fighting"
        self.round_kills = 0
        self._prepare_timer = 0
        self._clear_timer = 0
        self._last_kill_count = self.game_data.get("kill_count", 0)

        # 라운드 난이도 설정
        round_mult = 1.0 + (self.current_round * 0.2)
        self.round_target_kills = int(10 * round_mult * self.combat_config.difficulty)

        # 보스 라운드 체크
        if self.combat_config.boss and self.current_round == self.total_rounds - 1:
            self.round_target_kills = 1  # 보스 처치

        # 웨이브 시작
        start_wave(self.game_data, pygame.time.get_ticks() / 1000.0, self.enemies)
        self.game_data["game_state"] = config.GAME_STATE_RUNNING

        # 커스텀 커서 활성화
        if not self.custom_cursor_enabled:
            self.enable_custom_cursor(True)

        print(f"INFO: Round {self.current_round + 1}/{self.total_rounds} started - target: {self.round_target_kills}")

    def _update_enemy_spawn(self, dt: float, current_time: float):
        """적 스폰 업데이트"""
        if self.combat_state != "fighting":
            return

        # 최대 적 수 제한
        max_enemies = 15 + (self.current_round * 3)
        alive_enemies = [e for e in self.enemies if e.is_alive]
        if len(alive_enemies) >= max_enemies:
            return

        # 스폰 타이머
        self._spawn_timer += dt
        spawn_interval = 1.0 / self.combat_config.spawn_rate

        if self._spawn_timer >= spawn_interval:
            self._spawn_timer = 0
            self._spawn_enemy()

    def _spawn_enemy(self):
        """적 스폰"""
        if not self.combat_config.enemies:
            return

        # 랜덤 적 타입 선택
        enemy_type = random.choice(self.combat_config.enemies)

        # 스폰 위치 (화면 상단)
        x = random.randint(50, self.screen_size[0] - 50)
        y = -50

        # 적 생성 (Enemy 시그니처: pos, screen_height, chase_probability, enemy_type)
        enemy = Enemy(
            pos=pygame.math.Vector2(x, y),
            screen_height=self.screen_size[1],
            enemy_type=enemy_type.upper()  # Enemy는 대문자 타입 사용
        )

        # 난이도 적용
        enemy.hp = int(enemy.hp * self.combat_config.difficulty)
        enemy.max_hp = int(enemy.max_hp * self.combat_config.difficulty)

        self.enemies.append(enemy)

    def _check_round_clear(self):
        """라운드 클리어 체크"""
        if self.round_kills >= self.round_target_kills:
            self.combat_state = "round_clear"
            self.sound_manager.play_sfx("wave_clear")
            print(f"INFO: Round {self.current_round + 1} cleared!")

    def _complete_combat(self, success: bool):
        """전투 완료"""
        # 커스텀 커서 비활성화
        if self.custom_cursor_enabled:
            self.enable_custom_cursor(False)

        # shared_state 업데이트
        self.engine.shared_state['global_score'] = self.game_data.get('score', 0)

        # 상위 모드로 복귀
        self.request_pop_mode({
            "combat_complete": True,
            "success": success,
            "score": self.game_data.get('score', 0),
            "kills": self.game_data.get('kill_count', 0),
            "rounds_cleared": self.current_round if success else max(0, self.current_round - 1),
        })

    # =========================================================
    # 렌더링 - WaveMode 패턴 준수
    # =========================================================

    def render(self, screen: pygame.Surface):
        """전투 모드 렌더링 - base_mode render_common 사용"""
        # 배경
        if self.story_background:
            screen.blit(self.story_background, (0, 0))
        else:
            screen.fill((10, 15, 25))

        # 패럴랙스 레이어
        for layer in self.parallax_layers:
            layer.draw(screen)

        # HUD (상단 UI)
        if self.player:
            draw_hud(screen, self.screen_size, self.fonts["small"], self.player, self.game_data)

        # 스킬 인디케이터 (쿨다운 UI)
        if self.game_data["game_state"] == config.GAME_STATE_RUNNING:
            draw_skill_indicators(screen, self.screen_size, self.player, pygame.time.get_ticks() / 1000.0)

        # 게임 객체 렌더링 - base_mode의 render_common 사용
        self.render_common(screen)

        # 타겟 마커 렌더링 (적 위에 표시) - base_mode 메서드
        self.render_target_marker(screen)

        # 라운드 정보 UI
        self._render_round_info(screen)

        # 상태별 오버레이
        self._render_state_overlay(screen)

        # 시각적 피드백 효과 렌더링 (최상위 레이어)
        if self.damage_flash:
            self.damage_flash.render(screen)
        if self.level_up_effect:
            self.level_up_effect.render(screen)

        # 전투 모션 효과
        if self.combat_state == "fighting" and self.combat_motion_effect:
            self.combat_motion_effect.draw(screen)

        # 커스텀 커서 렌더링 (최상위) - base_mode 메서드
        self.render_custom_cursor(screen)

    def _render_round_info(self, screen: pygame.Surface):
        """라운드 정보 UI 렌더링"""
        if self.combat_state not in ["fighting", "round_clear"]:
            return

        font = self.fonts.get("medium", self.fonts.get("small"))

        # 라운드 번호
        round_text = f"ROUND {self.current_round + 1}/{self.total_rounds}"
        round_surf = font.render(round_text, True, (255, 220, 100))
        screen.blit(round_surf, (self.screen_size[0] // 2 - round_surf.get_width() // 2, 20))

        # 킬 카운트
        kills_text = f"KILLS: {self.round_kills}/{self.round_target_kills}"
        kills_surf = font.render(kills_text, True, (200, 200, 200))
        screen.blit(kills_surf, (self.screen_size[0] // 2 - kills_surf.get_width() // 2, 55))

    def _render_state_overlay(self, screen: pygame.Surface):
        """상태별 오버레이 렌더링"""
        if self.combat_state == "prepare":
            self._render_prepare_overlay(screen)
        elif self.combat_state == "round_clear":
            self._render_round_clear_overlay(screen)
        elif self.combat_state == "victory":
            self._render_victory_overlay(screen)
        elif self.combat_state == "defeat":
            self._render_defeat_overlay(screen)
        elif self.game_data.get("game_state") == config.GAME_STATE_PAUSED:
            self.menu_button_rects = draw_pause_and_over_screens(
                screen, self.screen_size,
                self.fonts["huge"], self.fonts["medium"], self.game_data
            )

    def _render_prepare_overlay(self, screen: pygame.Surface):
        """준비 오버레이"""
        font = self.fonts.get("large", self.fonts.get("medium"))

        text = f"ROUND {self.current_round + 1}"
        text_surf = font.render(text, True, (255, 255, 255))
        text_rect = text_surf.get_rect(center=(self.screen_size[0] // 2, self.screen_size[1] // 2))

        # 반투명 배경
        overlay = pygame.Surface(self.screen_size, pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))

        screen.blit(text_surf, text_rect)

    def _render_round_clear_overlay(self, screen: pygame.Surface):
        """라운드 클리어 오버레이"""
        font = self.fonts.get("large", self.fonts.get("medium"))

        text = "ROUND CLEAR!"
        text_surf = font.render(text, True, (100, 255, 100))
        text_rect = text_surf.get_rect(center=(self.screen_size[0] // 2, self.screen_size[1] // 2))

        screen.blit(text_surf, text_rect)

    def _render_victory_overlay(self, screen: pygame.Surface):
        """승리 오버레이"""
        font = self.fonts.get("large", self.fonts.get("medium"))

        text = "VICTORY!"
        text_surf = font.render(text, True, (255, 220, 100))
        text_rect = text_surf.get_rect(center=(self.screen_size[0] // 2, self.screen_size[1] // 2))

        # 반투명 배경
        overlay = pygame.Surface(self.screen_size, pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))

        screen.blit(text_surf, text_rect)

    def _render_defeat_overlay(self, screen: pygame.Surface):
        """패배 오버레이"""
        self.menu_button_rects = draw_pause_and_over_screens(
            screen, self.screen_size,
            self.fonts["huge"], self.fonts["medium"], self.game_data
        )

    # =========================================================
    # 이벤트 처리 - WaveMode 패턴 준수
    # =========================================================

    def handle_event(self, event: pygame.event.Event):
        """이벤트 처리"""
        # 공통 이벤트 처리 - base_mode 메서드
        if self.handle_common_events(event):
            return

        # 상태별 이벤트 처리
        if self.combat_state == "fighting":
            self._handle_fighting_event(event)
        elif self.combat_state == "defeat":
            self._handle_defeat_event(event)
        elif self.combat_state == "victory":
            self._handle_victory_event(event)

        # 일시정지 상태 이벤트
        if self.game_data.get("game_state") == config.GAME_STATE_PAUSED:
            self._handle_paused_event(event)

    def _handle_fighting_event(self, event: pygame.event.Event):
        """전투 중 이벤트 처리"""
        # 마우스 클릭 처리 (좌클릭 이동, 우클릭 공격) - base_mode 메서드
        if self.handle_mouse_click(event):
            return

        if event.type == pygame.KEYDOWN:
            # Q: 궁극기
            if event.key == pygame.K_q:
                if self.player and self.player.activate_ultimate(self.enemies):
                    print("INFO: Ultimate activated!")

            # E: 특수 능력
            elif event.key == pygame.K_e:
                trigger_ship_ability(
                    self.player, self.enemies, self.effects,
                    effect_system=self.effect_system,
                    sound_manager=self.sound_manager
                )

        # 커스텀 커서 업데이트
        self.update_custom_cursor(event.type == pygame.MOUSEMOTION and 0.016 or 0)

    def _handle_defeat_event(self, event: pygame.event.Event):
        """패배 상태 이벤트 처리"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                self._restart_combat()
            elif event.key == pygame.K_ESCAPE:
                self._complete_combat(success=False)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = event.pos

            # Restart 버튼
            if "restart" in self.menu_button_rects:
                if self.menu_button_rects["restart"].collidepoint(mouse_pos):
                    self._restart_combat()
                    return

            # Quit 버튼
            if "quit" in self.menu_button_rects:
                if self.menu_button_rects["quit"].collidepoint(mouse_pos):
                    self._complete_combat(success=False)
                    return

    def _handle_victory_event(self, event: pygame.event.Event):
        """승리 상태 이벤트 처리"""
        if event.type == pygame.KEYDOWN:
            if event.key in [pygame.K_RETURN, pygame.K_SPACE]:
                self._complete_combat(success=True)

    def _handle_paused_event(self, event: pygame.event.Event):
        """일시정지 상태 이벤트 처리"""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = event.pos

            # Resume 버튼
            if "resume" in self.menu_button_rects:
                if self.menu_button_rects["resume"].collidepoint(mouse_pos):
                    self.game_data["game_state"] = config.GAME_STATE_RUNNING
                    self.sound_manager.play_sfx("button_click")
                    return

            # Quit 버튼
            if "quit" in self.menu_button_rects:
                if self.menu_button_rects["quit"].collidepoint(mouse_pos):
                    self._complete_combat(success=False)
                    return

    def _restart_combat(self):
        """전투 재시작"""
        self.current_round = 0
        self.combat_state = "prepare"
        self._prepare_timer = 0
        self._clear_timer = 0
        self._victory_timer = 0
        self._spawn_timer = 0
        self.round_kills = 0

        # 게임 데이터 리셋
        self.game_data = reset_game_data()
        self.game_data['score'] = self.engine.shared_state.get('global_score', 0)
        self.game_data['game_state'] = config.GAME_STATE_WAVE_PREPARE

        # 게임 객체 초기화 - base_mode의 리스트 사용
        self.enemies.clear()
        self.bullets.clear()
        self.gems.clear()
        self.effects.clear()
        self.damage_number_manager.clear()

        # 플레이어 리셋
        if self.player:
            self.player.hp = self.player.max_hp
            self.player.is_dead = False
            self.player.pos = pygame.math.Vector2(self.config.player_start_pos)

        print("INFO: Combat restarted")

    # =========================================================
    # 라이프사이클
    # =========================================================

    def on_exit(self):
        """모드 종료"""
        # 커스텀 커서 비활성화
        if self.custom_cursor_enabled:
            self.enable_custom_cursor(False)

        # 상태 저장
        self.engine.shared_state['global_score'] = self.game_data.get('score', 0)
        if self.player:
            self.engine.shared_state['player_upgrades'] = self.player.upgrades

        super().on_exit()


print("INFO: combat_mode.py loaded")
