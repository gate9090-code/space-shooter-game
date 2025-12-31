# modes/wave_mode.py
"""
WaveMode - 웨이브 모드
20웨이브 클리어 목표, 원근법 적용, 랜덤 배경
"""

import pygame
import random
from typing import Dict, Any, Optional, List, Tuple

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
from systems.save_system import (
    get_save_system, extract_player_save_data, apply_player_save_data
)


class WaveMode(GameMode):
    """
    웨이브 모드

    특징:
    - 20웨이브 클리어 목표
    - 원근법 적용 (Y축 기반 스케일링)
    - 랜덤 배경 선택
    - 웨이브 클리어 → 레벨업 → 다음 웨이브
    """

    def get_config(self) -> ModeConfig:
        """웨이브 모드 설정"""
        return ModeConfig(
            mode_name="wave",
            perspective_enabled=True,
            perspective_apply_to_player=True,
            perspective_apply_to_enemies=True,
            perspective_apply_to_bullets=True,
            perspective_apply_to_gems=True,
            player_speed_multiplier=1.0,
            player_start_pos=(self.screen_size[0] // 2, self.screen_size[1] // 2),
            player_afterimages_enabled=True,
            background_type="parallax",
            parallax_enabled=True,
            meteor_enabled=True,
            show_wave_ui=True,
            show_stage_ui=False,
            show_minimap=False,
            show_skill_indicators=True,
            wave_system_enabled=True,
            spawn_system_enabled=True,
            random_events_enabled=True,
            asset_prefix="wave",
        )

    def init(self):
        """웨이브 모드 초기화"""
        # config에 모드 설정
        config.GAME_MODE = "wave"

        # 시스템 초기화
        self.combat_system = CombatSystem()
        self.skill_system = SkillSystem()
        self.effect_system = EffectSystem()
        self.spawn_system = SpawnSystem(SpawnConfig(
            enemy_spawn_interval=1.0,
            enemy_spawn_count=1,
            boss_enabled=True,
        ))
        self.ui_system = UISystem(UIConfig(
            show_hp_bar=True,
            show_score=True,
            show_wave_info=True,
            show_level_info=True,
            show_skill_indicators=True,
        ))

        # 저장 시스템
        self.save_system = get_save_system()

        # 저장된 진행 불러오기 여부 확인
        self.continue_from_save = self.engine.shared_state.get('continue_wave_save', False)
        self.engine.shared_state['continue_wave_save'] = False  # 플래그 리셋

        # 게임 데이터 초기화
        self.game_data = reset_game_data()
        self.game_data['score'] = self.engine.shared_state.get('global_score', 0)
        self.game_data['game_state'] = config.GAME_STATE_WAVE_PREPARE
        self.game_data['wave_phase'] = 'normal'  # 웨이브 페이즈: normal, cleanup

        # 플레이어 생성
        self.spawn_player(
            pos=self.config.player_start_pos,
            upgrades=self.engine.shared_state.get('player_upgrades', {})
        )

        # 저장된 진행 불러오기
        if self.continue_from_save:
            self._load_saved_progress()

        # 패럴랙스 배경 생성
        self._init_parallax_layers()

        # 유성 효과
        self.meteors: List[Meteor] = []
        self.meteor_spawned_this_wave = False

        # 배경 이미지 캐시 로드
        self._load_background_cache()

        # 현재 배경
        self.current_wave_bg = 0
        self.current_background = None
        self.background_transition = None

        # 무한 스크롤 배경 (웨이브 진행 중 동일 배경 이동)
        self.scroll_enabled = config.CONTINUOUS_SLIDE_ENABLED
        self.scroll_speed = config.BACKGROUND_SCROLL_SPEED
        self.scroll_offset = 0.0  # 현재 스크롤 위치

        # 설정 메뉴 관련
        self.settings_bars = {}
        self.dragging_bgm = False
        self.dragging_sfx = False

        # 메뉴 버튼 클릭 영역 (마우스 클릭 지원)
        self.menu_button_rects: Dict[str, pygame.Rect] = {}

        # 시각적 피드백 효과 (base_mode의 공통 메서드 사용)
        self._init_visual_feedback_effects()

        # 전투 모션 효과 (고속 비행 연출)
        self.combat_motion_effect = CombatMotionEffect(self.screen_size)
        self.player_prev_pos = None  # 이동 감지용

        print("INFO: WaveMode initialized")

    def _load_saved_progress(self):
        """저장된 진행 불러오기"""
        save_data = self.save_system.load_wave_progress()
        if not save_data:
            print("WARNING: No save data found to continue")
            return

        # 게임 데이터 복원
        saved_game = save_data.get("game_data", {})
        self.game_data["current_wave"] = saved_game.get("current_wave", 1)
        self.game_data["score"] = saved_game.get("score", 0)
        self.game_data["player_level"] = saved_game.get("player_level", 1)
        self.game_data["kill_count"] = saved_game.get("kill_count", 0)

        # 웨이브 타겟 킬 업데이트
        current_wave = self.game_data["current_wave"]
        if current_wave in config.WAVE_SCALING:
            self.game_data["wave_target_kills"] = config.WAVE_SCALING[current_wave]["target_kills"]

        # 플레이어 데이터 복원
        saved_player = save_data.get("player_data", {})
        if saved_player and self.player:
            apply_player_save_data(self.player, saved_player)

        print(f"INFO: Loaded saved progress - Wave {self.game_data['current_wave']}, Level {self.game_data['player_level']}")

    def save_progress(self):
        """현재 진행 저장"""
        if not self.player:
            return False

        player_data = extract_player_save_data(self.player)
        player_upgrades = self.engine.shared_state.get('player_upgrades', {})

        return self.save_system.save_wave_progress(
            self.game_data,
            player_data,
            player_upgrades
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

    def _load_background_cache(self):
        """배경 이미지 캐시 로드"""
        self.background_image_cache = {}
        self.wave_backgrounds = {}

        # 기본 배경 (bg1~bg40)
        for bg_num in range(1, 41):
            bg_filename = f"bg{bg_num}.jpg"
            try:
                bg_path = config.BACKGROUND_DIR / bg_filename
                self.background_image_cache[bg_num] = AssetManager.get_image(bg_path, self.screen_size)
            except Exception as e:
                # 폴백: 검은 배경
                self.background_image_cache[bg_num] = pygame.Surface(self.screen_size)
                self.background_image_cache[bg_num].fill((0, 0, 0))

    def update(self, dt: float, current_time: float):
        """웨이브 모드 업데이트"""
        # 공통 업데이트 (타임스케일, 화면 흔들림, 이펙트)
        scaled_dt = self.update_common(dt, current_time)

        # 배경 업데이트 (항상)
        self._update_background(dt)

        # 게임 상태별 업데이트
        if self.game_data["game_state"] == config.GAME_STATE_RUNNING:
            self._update_running(scaled_dt, current_time)
            # 전투 중 커스텀 커서 활성화
            if not self.custom_cursor_enabled:
                self.enable_custom_cursor(True)
            self.update_custom_cursor(dt)
        else:
            # 전투 외 상태에서 커스텀 커서 비활성화
            if self.custom_cursor_enabled:
                self.enable_custom_cursor(False)

        # 게임 오버 체크 (항상 - HP가 0 이하인지 확인)
        # 모든 상태에서 HP 0 이하면 게임 오버 (승리/게임오버 제외)
        if self.game_data["game_state"] not in [config.GAME_STATE_OVER, config.GAME_STATE_VICTORY]:
            if self.player and self.player.hp <= 0:
                self._check_game_over()

    def _update_background(self, dt: float):
        """배경 업데이트"""
        # 배경 전환 효과 (웨이브 변경 시)
        if self.background_transition and self.background_transition.is_active:
            self.background_transition.update(dt)
            # 트랜지션 완료 시 현재 배경 업데이트
            if not self.background_transition.is_active:
                self.current_background = self.background_transition.new_bg

        # 무한 스크롤 (게임 실행 중, 트랜지션 중이 아닐 때)
        if self.scroll_enabled and self.game_data["game_state"] == config.GAME_STATE_RUNNING:
            if not (self.background_transition and self.background_transition.is_active):
                # 스크롤 오프셋 업데이트 (위에서 아래로 이동)
                self.scroll_offset += self.scroll_speed * dt
                # 화면 높이를 넘으면 리셋
                if self.scroll_offset >= self.screen_size[1]:
                    self.scroll_offset = 0.0

        # 패럴랙스 레이어
        for layer in self.parallax_layers:
            layer.update(dt)

        # 유성 효과
        if config.METEOR_SETTINGS.get("enabled", True):
            current_wave = self.game_data.get('current_wave', 1)

            if 'last_meteor_wave' not in self.game_data:
                self.game_data['last_meteor_wave'] = 0

            if current_wave != self.game_data['last_meteor_wave'] and not self.meteor_spawned_this_wave:
                if len(self.meteors) == 0:
                    self.meteors.append(Meteor(self.screen_size))
                    self.meteor_spawned_this_wave = True
                    self.game_data['last_meteor_wave'] = current_wave

        for meteor in self.meteors[:]:
            meteor.update(dt)
            if not meteor.is_alive:
                self.meteors.remove(meteor)
                self.meteor_spawned_this_wave = False

    def _update_running(self, dt: float, current_time: float):
        """게임 실행 중 업데이트"""
        # 플레이어 업데이트
        self.update_player(dt, current_time)

        # 타겟팅 시스템 업데이트
        self.update_targeting(dt)

        # 객체 업데이트 (터렛, 드론, 총알)
        self.update_objects(dt)

        # HP 변화 감지를 위해 이전 HP 저장
        hp_before = self.player.hp if self.player else 0

        # 게임 객체 충돌 및 업데이트
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
        if self.player:
            is_moving = False
            move_direction = None
            if self.player_prev_pos is not None:
                dx = self.player.pos.x - self.player_prev_pos[0]
                dy = self.player.pos.y - self.player_prev_pos[1]
                is_moving = (abs(dx) > 2 or abs(dy) > 2)  # 일정 이상 움직임 감지
                if is_moving:
                    move_direction = (dx, dy)  # 방향 전환 감지용
            self.player_prev_pos = (self.player.pos.x, self.player.pos.y)
            # 플레이어 위치 전달 (줌/워프 효과 중심점)
            player_pos = (self.player.pos.x, self.player.pos.y)
            self.combat_motion_effect.update_player_movement(is_moving, dt, player_pos, move_direction)

            # 플레이어 피격 시 CombatMotionEffect 이동 시간 리셋
            if hasattr(self.player, 'was_hit_recently') and self.player.was_hit_recently:
                self.combat_motion_effect.reset_move_time()
                self.player.was_hit_recently = False

        self.combat_motion_effect.update(dt)

        # 웨이브 페이즈에 따른 처리
        wave_phase = self.game_data.get('wave_phase', 'normal')

        if wave_phase == 'normal':
            # EXP 바 체크 - 가득 차면 자동으로 레벨업 메뉴 열기 (normal 페이즈에서만)
            level_threshold = get_next_level_threshold(self.game_data["player_level"])
            if self.game_data.get("uncollected_score", 0) >= level_threshold:
                self.game_data["game_state"] = config.GAME_STATE_LEVEL_UP
                self.game_data["tactical_options"] = generate_tactical_options(self.player, self.game_data)
                self.game_data["skill_view_readonly"] = False  # 선택 가능하게 설정
                self.sound_manager.play_sfx("level_up")
                return  # 레벨업 메뉴로 전환, 나머지 업데이트 스킵
            # === 일반 페이즈 ===
            # 적 스폰
            handle_spawning(self.enemies, self.screen_size, current_time,
                           self.game_data, self.effects, self.sound_manager)

            # 젬 스폰
            spawn_gem(self.gems, self.screen_size, current_time, self.game_data)

            # 랜덤 이벤트
            update_random_event(self.game_data, current_time, dt,
                               self.player, self.gems, self.enemies, self.screen_size)

            # target_kills 달성 체크 → 전환 시작
            if check_wave_clear(self.game_data):
                self._trigger_wave_transition()

        elif wave_phase == 'cleanup':
            # === 정리 페이즈 (전환 후) ===
            # 적 스폰 없음 - 남은 적만 처리

            # 클리어 조건: 화면의 모든 적이 없음 (처치 또는 퇴각 완료)
            alive_enemies = [e for e in self.enemies if e.is_alive]

            if len(alive_enemies) == 0 and not self.game_data.get('victory_animation_active', False):
                # 플레이어 승리 애니메이션 시작
                self._start_victory_animation()

        elif wave_phase == 'victory_animation':
            # === 승리 애니메이션 페이즈 ===
            # PlayerVictoryAnimation이 완료되면 레벨업 화면으로 전환
            if not self.game_data.get('victory_animation_active', False):
                self.game_data["game_state"] = config.GAME_STATE_WAVE_CLEAR
                self.game_data["wave_phase"] = 'normal'
                self.sound_manager.play_sfx("wave_clear")
                print(f"INFO: Wave {self.game_data['current_wave']} cleared! (all enemies defeated or retreated)")

        # 스킬 패시브 업데이트
        self.skill_system.update_passive_skills(
            self.player, self.enemies, self.effects, dt, current_time
        )

    def _trigger_wave_transition(self):
        """target_kills 달성 시 웨이브 전환 처리"""
        print(f"INFO: Wave {self.game_data['current_wave']} target kills reached! Transitioning...")

        # 전투 모션 효과 즉시 종료
        self.combat_motion_effect.is_active = False

        # 페이즈 변경
        self.game_data['wave_phase'] = 'cleanup'

        # WaveTransitionEffect 추가 (화면 어두워짐 + 이미지 서서히 등장)
        from objects import WaveTransitionEffect
        try:
            transition_effect = WaveTransitionEffect(
                screen_size=self.screen_size,
                image_path=config.WAVE_HERO_IMAGE_PATH,
                darken_duration=1.0,
                image_duration=1.5,
                brighten_duration=0.5
            )
            self.effects.append(transition_effect)
        except Exception as e:
            print(f"WARNING: WaveTransitionEffect failed: {e}")

        # 모든 적을 퇴각 모드로 설정 (화면 상부로 퇴각)
        for enemy in self.enemies:
            if not enemy.is_alive:
                continue
            enemy.is_retreating = True
            enemy.is_circling = False  # 회전 모드 해제

        # 남은 젬 모두 제거
        gem_count = len(self.gems)
        if gem_count > 0:
            self.gems.clear()
            print(f"INFO: Cleared {gem_count} uncollected gems")

        self.sound_manager.play_sfx("level_up")  # 전환 사운드

        # 레벨업 효과 트리거 (웨이브 클리어 = 레벨업)
        self.level_up_effect.trigger(self.game_data["current_wave"])

    def _start_victory_animation(self):
        """웨이브 클리어 시 플레이어 승리 애니메이션 시작"""
        from objects import PlayerVictoryAnimation

        print(f"INFO: Starting victory animation for wave {self.game_data['current_wave']}")

        # 애니메이션 활성화 플래그
        self.game_data['victory_animation_active'] = True
        self.game_data['wave_phase'] = 'victory_animation'

        # 승리 애니메이션 생성
        def on_animation_complete():
            self.game_data['victory_animation_active'] = False
            print("INFO: Victory animation completed")

        victory_anim = PlayerVictoryAnimation(
            player=self.player,
            screen_size=self.screen_size,
            orbit_duration=2.5,   # 아주 천천히 회전
            move_duration=1.5     # 1.5초 동안 하단으로 이동
        )
        victory_anim.on_complete = on_animation_complete
        self.effects.append(victory_anim)

    def _check_game_over(self):
        """게임 오버 체크"""
        if not self.player:
            return

        # HP가 0보다 크면 생존
        if self.player.hp > 0:
            return

        # 이미 게임 오버 상태면 리턴
        if self.game_data["game_state"] == config.GAME_STATE_OVER:
            return

        # Phoenix Rebirth 체크 (스킬이 있고, 쿨다운이 완료된 경우에만)
        if getattr(self.player, 'has_phoenix', False) and getattr(self.player, 'phoenix_cooldown', 999) <= 0:
            self.player.hp = self.player.max_hp
            self.player.is_dead = False  # 부활 시 사망 플래그 리셋
            self.player.phoenix_cooldown = config.PHOENIX_REBIRTH_COOLDOWN_SECONDS
            # 부활 이펙트 추가
            self._add_revive_effects("Phoenix Rebirth!", (255, 150, 0))  # 오렌지색
            print("INFO: Phoenix Rebirth activated!")
            return

        # Reincarnation 체크
        if self.player.upgrades.get("REINCARNATION", 0) > 0:
            self.player.hp = self.player.max_hp
            self.player.is_dead = False  # 부활 시 사망 플래그 리셋
            self.player.upgrades["REINCARNATION"] -= 1
            self.engine.save_shared_state()
            # 부활 이펙트 추가
            self._add_revive_effects("Reincarnation!", (255, 80, 80))  # 빨간색
            print("INFO: Reincarnation consumed!")
            return

        # 게임 오버
        print(f"INFO: Game Over! Player HP: {self.player.hp}")
        self.game_data["game_state"] = config.GAME_STATE_OVER
        self.engine.save_shared_state()

    def _add_revive_effects(self, text: str, color: Tuple[int, int, int]):
        """부활 시 시각 효과 추가 (화면 플래시 + 텍스트)"""
        from objects import ScreenFlash, ReviveTextEffect

        # 화면 플래시 (0.4초)
        flash = ScreenFlash(self.screen_size, color=color, duration=0.4)
        self.effects.append(flash)

        # 부활 텍스트 (2초)
        text_effect = ReviveTextEffect(text, self.screen_size, color=color, duration=2.0)
        self.effects.append(text_effect)

        # 사운드 재생
        self.sound_manager.play_sfx("level_up")

    # =========================================================
    # 오토파일럿 자동 스킬 발동 (base_mode 오버라이드)
    # =========================================================
    def _trigger_auto_ultimate(self):
        """오토파일럿 궁극기 자동 발동"""
        if self.player and self.player.activate_ultimate(self.enemies):
            print("INFO: [AUTO] Ultimate activated!")

    def _trigger_auto_ability(self):
        """오토파일럿 특수 능력 자동 발동 (utils.trigger_ship_ability 사용)"""
        trigger_ship_ability(
            self.player, self.enemies, self.effects,
            effect_system=self.effect_system,
            sound_manager=self.sound_manager
        )

    def render(self, screen: pygame.Surface):
        """웨이브 모드 렌더링"""
        # 배경 렌더링
        self._render_background(screen)

        # 패럴랙스 레이어
        for layer in self.parallax_layers:
            layer.draw(screen)

        # 유성
        for meteor in self.meteors:
            meteor.draw(screen)

        # ===== UI 요소들 (플레이어/적보다 먼저 렌더링) =====
        # HUD (상단 UI)
        draw_hud(screen, self.screen_size, self.fonts["small"], self.player, self.game_data)

        # 보스 체력바
        boss = next((e for e in self.enemies if hasattr(e, 'is_boss') and e.is_boss and e.is_alive), None)
        if boss:
            current_wave = self.game_data.get("current_wave", 1)
            enemy_count = len([e for e in self.enemies if e.is_alive])
            draw_boss_health_bar(screen, self.screen_size, self.fonts["medium"], boss,
                                enemy_count=enemy_count, current_wave=current_wave)

        # 스킬 인디케이터 (쿨다운 UI)
        if self.game_data["game_state"] == config.GAME_STATE_RUNNING:
            draw_skill_indicators(screen, self.screen_size, self.player, pygame.time.get_ticks() / 1000.0)

        # 랜덤 이벤트 UI
        if self.game_data["game_state"] == config.GAME_STATE_RUNNING:
            draw_random_event_ui(screen, self.screen_size, self.game_data)

        # ===== 게임 객체 렌더링 (UI 위에 표시) =====
        self.render_common(screen)

        # 타겟 마커 렌더링 (적 위에 표시)
        self.render_target_marker(screen)

        # 상태별 오버레이
        self._render_overlay(screen)

        # 시각적 피드백 효과 렌더링 (최상위 레이어)
        self.damage_flash.render(screen)
        self.level_up_effect.render(screen)

        # 전투 모션 효과 (고속 비행 연출) - RUNNING 상태에서만
        if self.game_data["game_state"] == config.GAME_STATE_RUNNING:
            self.combat_motion_effect.draw(screen)

        # 커스텀 커서 렌더링 (최상위)
        self.render_custom_cursor(screen)

    def _render_background(self, screen: pygame.Surface):
        """배경 렌더링"""
        # 웨이브 전환 트랜지션 진행 중
        if self.background_transition and self.background_transition.is_active:
            self.background_transition.draw(screen)
        elif self.current_background:
            # 무한 스크롤 렌더링 (게임 실행 중 - 아래에서 위로)
            if self.scroll_enabled and self.game_data["game_state"] == config.GAME_STATE_RUNNING:
                offset = int(self.scroll_offset)
                # 첫 번째 배경 (아래로 이동)
                screen.blit(self.current_background, (0, offset))
                # 두 번째 배경 (위에서 이어서)
                screen.blit(self.current_background, (0, offset - self.screen_size[1]))
            else:
                # 일반 렌더링 (정지)
                screen.blit(self.current_background, (0, 0))
        else:
            screen.fill(config.BLACK)

    def _render_overlay(self, screen: pygame.Surface):
        """상태별 오버레이 렌더링"""
        state = self.game_data["game_state"]

        if state == config.GAME_STATE_SETTINGS:
            self.settings_bars = draw_settings_menu(
                screen, self.screen_size,
                self.fonts["huge"], self.fonts["large"],
                self.fonts["medium"], self.sound_manager
            )
        elif state == config.GAME_STATE_PAUSED:
            self.menu_button_rects = draw_pause_and_over_screens(
                screen, self.screen_size,
                self.fonts["huge"], self.fonts["medium"], self.game_data
            )
        elif state == config.GAME_STATE_OVER:
            self.menu_button_rects = draw_pause_and_over_screens(
                screen, self.screen_size,
                self.fonts["huge"], self.fonts["medium"], self.game_data
            )
        elif state == config.GAME_STATE_SHOP:
            draw_shop_screen(screen, self.screen_size, self.fonts["large"],
                           self.fonts["medium"], self.game_data['score'], self.player.upgrades)
        elif state == config.GAME_STATE_LEVEL_UP:
            draw_tactical_menu(screen, self.screen_size,
                             self.fonts["huge"], self.fonts["medium"], self.game_data)
        elif state == config.GAME_STATE_WAVE_PREPARE:
            draw_wave_prepare_screen(screen, self.screen_size,
                                    self.fonts["huge"], self.fonts["medium"], self.game_data)
        elif state == config.GAME_STATE_WAVE_CLEAR:
            draw_wave_clear_screen(screen, self.screen_size,
                                  self.fonts["huge"], self.fonts["medium"], self.game_data)
        elif state == config.GAME_STATE_VICTORY:
            fonts_dict = {"huge": self.fonts["huge"], "title": self.fonts["large"],
                         "medium": self.fonts["medium"], "small": self.fonts["small"]}
            draw_victory_screen(screen, self.game_data, self.player, fonts_dict)
        elif state == config.GAME_STATE_QUIT_CONFIRM:
            self.ui_system.draw_quit_confirm_overlay(screen, self.screen_size, self.fonts)
        elif state == config.GAME_STATE_TURRET_PLACEMENT:
            self._render_turret_placement_ui(screen)

    def handle_event(self, event: pygame.event.Event):
        """이벤트 처리"""
        # 설정 메뉴 이벤트
        if self.game_data["game_state"] == config.GAME_STATE_SETTINGS:
            self._handle_settings_event(event)
            return

        # 공통 이벤트 처리
        if self.handle_common_events(event):
            return

        # 상태별 이벤트 처리
        state = self.game_data["game_state"]

        if state == config.GAME_STATE_RUNNING:
            self._handle_running_event(event)
        elif state == config.GAME_STATE_WAVE_PREPARE:
            self._handle_wave_prepare_event(event)
        elif state == config.GAME_STATE_WAVE_CLEAR:
            self._handle_wave_clear_event(event)
        elif state == config.GAME_STATE_LEVEL_UP:
            self._handle_level_up_event(event)
        elif state == config.GAME_STATE_SHOP:
            self._handle_shop_event(event)
        elif state == config.GAME_STATE_OVER:
            self._handle_game_over_event(event)
        elif state == config.GAME_STATE_VICTORY:
            self._handle_victory_event(event)
        elif state == config.GAME_STATE_QUIT_CONFIRM:
            self._handle_quit_confirm_event(event)
        elif state == config.GAME_STATE_TURRET_PLACEMENT:
            self._handle_turret_placement_event(event)
        elif state == config.GAME_STATE_PAUSED:
            self._handle_paused_event(event)

    def _handle_settings_event(self, event: pygame.event.Event):
        """설정 메뉴 이벤트"""
        if event.type == pygame.KEYDOWN and event.key == pygame.K_F1:
            self.game_data["game_state"] = self.game_data.get("previous_game_state", config.GAME_STATE_RUNNING)

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_x, mouse_y = event.pos
            if "bgm_bar" in self.settings_bars and self.settings_bars["bgm_bar"].collidepoint(mouse_x, mouse_y):
                self.dragging_bgm = True
                bar = self.settings_bars["bgm_bar"]
                volume = (mouse_x - bar.x) / bar.width
                self.sound_manager.set_bgm_volume(max(0.0, min(1.0, volume)))
            elif "sfx_bar" in self.settings_bars and self.settings_bars["sfx_bar"].collidepoint(mouse_x, mouse_y):
                self.dragging_sfx = True
                bar = self.settings_bars["sfx_bar"]
                volume = (mouse_x - bar.x) / bar.width
                self.sound_manager.set_sfx_volume(max(0.0, min(1.0, volume)))

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging_bgm = False
            self.dragging_sfx = False

        elif event.type == pygame.MOUSEMOTION:
            if self.dragging_bgm and "bgm_bar" in self.settings_bars:
                bar = self.settings_bars["bgm_bar"]
                volume = (event.pos[0] - bar.x) / bar.width
                self.sound_manager.set_bgm_volume(max(0.0, min(1.0, volume)))
            elif self.dragging_sfx and "sfx_bar" in self.settings_bars:
                bar = self.settings_bars["sfx_bar"]
                volume = (event.pos[0] - bar.x) / bar.width
                self.sound_manager.set_sfx_volume(max(0.0, min(1.0, volume)))

    def _handle_running_event(self, event: pygame.event.Event):
        """게임 실행 중 이벤트"""
        # 마우스 클릭 처리 (좌클릭 이동, 우클릭 공격)
        if self.handle_mouse_click(event):
            return

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_q:
                if self.player.activate_ultimate(self.enemies):
                    print("INFO: Ultimate activated!")

            elif event.key == pygame.K_l:
                self.game_data["previous_game_state"] = self.game_data["game_state"]
                self.game_data["game_state"] = config.GAME_STATE_LEVEL_UP
                self.game_data["skill_view_readonly"] = True
                self.game_data["tactical_options"] = generate_tactical_options(self.player, self.game_data)

            elif event.key == pygame.K_e:
                # Ship special ability (E key) - utils.trigger_ship_ability 사용
                trigger_ship_ability(
                    self.player, self.enemies, self.effects,
                    effect_system=self.effect_system,
                    sound_manager=self.sound_manager
                )

    def _handle_wave_prepare_event(self, event: pygame.event.Event):
        """웨이브 준비 이벤트"""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            start_wave(self.game_data, pygame.time.get_ticks() / 1000.0, self.enemies)
            self.game_data["game_state"] = config.GAME_STATE_RUNNING

            new_wave = self.game_data["current_wave"]
            self.sound_manager.play_wave_bgm(new_wave)

            # 배경 전환 및 스크롤 오프셋 리셋
            self._transition_background(new_wave)
            self.scroll_offset = 0.0

            # 전투 모션 효과 리셋 (웨이브당 2회)
            self.combat_motion_effect.reset_wave()

    def _handle_wave_clear_event(self, event: pygame.event.Event):
        """웨이브 클리어 이벤트"""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # 웨이브 클리어 시 게임 오버 체크 (HP가 0인 상태로 클리어했을 수 있음)
            if self.player and self.player.hp <= 0:
                self._check_game_over()
                return

            # 다음 웨이브로 진행하기 전에 저장
            self.save_progress()

            advance_to_next_wave(self.game_data, self.player, self.sound_manager)

    def _handle_level_up_event(self, event: pygame.event.Event):
        """레벨업 이벤트 - 키보드 및 마우스 클릭 지원"""
        option_key = -1

        # 키보드 입력 처리
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_1: option_key = 0
            elif event.key == pygame.K_2: option_key = 1
            elif event.key == pygame.K_3: option_key = 2
            elif event.key == pygame.K_4: option_key = 3
            elif event.key == pygame.K_l:
                # 읽기 전용 창 닫기
                if "previous_game_state" in self.game_data:
                    self.game_data["game_state"] = self.game_data["previous_game_state"]
                else:
                    self.game_data["game_state"] = config.GAME_STATE_RUNNING
                self.game_data["tactical_options"] = []
                self.game_data["skill_view_readonly"] = False
                return

        # 마우스 클릭 처리
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = event.pos
            card_rects = self.game_data.get("level_up_card_rects", [])
            for i, card_rect in enumerate(card_rects):
                if card_rect.collidepoint(mouse_pos):
                    option_key = i
                    break

        # 옵션 선택 처리
        if option_key != -1 and not self.game_data.get("skill_view_readonly", False):
            handle_tactical_upgrade(
                option_key, self.player, self.enemies, self.bullets,
                self.gems, self.effects, self.game_data,
                self.game_data["tactical_options"],
                self.engine.shared_state.get("player_upgrades", {})
            )

            # 드론 생성 처리
            if "pending_drones" in self.game_data and len(self.game_data["pending_drones"]) > 0:
                for orbit_angle in self.game_data["pending_drones"]:
                    self.drones.append(Drone(self.player, orbit_angle))
                self.game_data["pending_drones"].clear()

            # 터렛 자동 배치 처리 (쿨다운 UI 상단)
            if self.game_data.get("pending_turrets", 0) > 0:
                self._auto_place_turrets()

            # 레벨업 후 게임 오버 체크 (HP가 0인 상태로 레벨업에 진입했을 수 있음)
            self._check_game_over()

    def _handle_shop_event(self, event: pygame.event.Event):
        """상점 이벤트"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_c:
                # 상점 닫기
                self.engine.shared_state['global_score'] = self.game_data['score']
                self.engine.shared_state['player_upgrades'] = self.player.upgrades
                self.engine.save_shared_state()

                if "previous_game_state" in self.game_data:
                    self.game_data["game_state"] = self.game_data["previous_game_state"]
                else:
                    self.game_data["game_state"] = config.GAME_STATE_RUNNING

            else:
                # 구매 처리
                purchase_key = -1
                if event.key == pygame.K_1: purchase_key = 0
                elif event.key == pygame.K_2: purchase_key = 1
                elif event.key == pygame.K_3: purchase_key = 2
                elif event.key == pygame.K_4: purchase_key = 3

                if purchase_key != -1:
                    self._process_shop_purchase(purchase_key)

    def _process_shop_purchase(self, purchase_key: int):
        """상점 구매 처리"""
        upgrade_keys = list(config.UPGRADE_KEYS.keys())
        if purchase_key >= len(upgrade_keys):
            return

        key = upgrade_keys[purchase_key]
        current_level = self.player.upgrades.get(key, 0)

        if key == "REINCARNATION":
            cost = config.REINCARNATION_COST
            max_level = config.REINCARNATION_MAX
        else:
            cost = config.PERMANENT_UPGRADE_COST_BASE * (current_level + 1)
            max_level = 10

        if current_level < max_level and self.game_data['score'] >= cost:
            self.game_data['score'] -= cost
            self.player.upgrades[key] = current_level + 1
            self.engine.shared_state['global_score'] = self.game_data['score']
            self.engine.shared_state['player_upgrades'] = self.player.upgrades
            self.engine.save_shared_state()
            self.player.calculate_stats_from_upgrades()

            if key == "MAX_HP":
                self.player.max_hp = self.player.initial_max_hp
                self.player.hp = min(self.player.hp, self.player.max_hp)
            elif key == "COOLDOWN":
                cd_level = self.player.upgrades.get("COOLDOWN", 0)
                cd_reduction_ratio = config.PERMANENT_COOLDOWN_REDUCTION_RATIO * cd_level
                self.player.weapon.cooldown = config.WEAPON_COOLDOWN_BASE * (1 - cd_reduction_ratio)

    def _handle_game_over_event(self, event: pygame.event.Event):
        """게임 오버 이벤트 - 마우스 클릭 지원"""
        # 마우스 클릭 처리
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = event.pos

            # Restart 버튼 클릭
            if "restart" in self.menu_button_rects:
                if self.menu_button_rects["restart"].collidepoint(mouse_pos):
                    self._restart_game()
                    self.sound_manager.play_sfx("button_click")
                    return

            # Return to Base 버튼 클릭
            if "return_base" in self.menu_button_rects:
                if self.menu_button_rects["return_base"].collidepoint(mouse_pos):
                    self.sound_manager.play_sfx("button_click")
                    self._return_to_base()
                    return

            # Quit 버튼 클릭
            if "quit" in self.menu_button_rects:
                if self.menu_button_rects["quit"].collidepoint(mouse_pos):
                    self.request_quit()
                    return

        # 키보드 처리 (기존 유지)
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                self._restart_game()
            elif event.key == pygame.K_b:
                # B키: 기지 복귀
                self._return_to_base()
            elif event.key == pygame.K_ESCAPE:
                self.request_quit()

    def _handle_victory_event(self, event: pygame.event.Event):
        """승리 이벤트 - 사이드 미션일 경우 BaseHub로 귀환"""
        if event.type == pygame.KEYDOWN:
            is_side_mission = self.engine.shared_state.get('is_side_mission', False)

            if event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                # 미션 완료 후 귀환
                if is_side_mission:
                    self._complete_side_mission_and_return()
                else:
                    self._mark_episode_complete()
                    self._return_to_base()
            elif event.key == pygame.K_r:
                self._restart_game()
            elif event.key == pygame.K_n and not is_side_mission:
                # N키: Boss Rush 시작
                self._start_boss_rush()
            elif event.key == pygame.K_b:
                # B키: Base Hub로 귀환
                if is_side_mission:
                    self._complete_side_mission_and_return()
                else:
                    self._mark_episode_complete()
                    self._return_to_base()
            elif event.key == pygame.K_q or event.key == pygame.K_ESCAPE:
                if is_side_mission:
                    self._complete_side_mission_and_return()
                else:
                    self._mark_episode_complete()
                    self._return_to_base()

    def _handle_paused_event(self, event: pygame.event.Event):
        """일시정지 이벤트 - P키는 handle_common_events에서 처리됨, 마우스 클릭 지원"""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = event.pos

            # Resume 버튼 클릭
            if "resume" in self.menu_button_rects:
                if self.menu_button_rects["resume"].collidepoint(mouse_pos):
                    self.game_data["game_state"] = config.GAME_STATE_RUNNING
                    self.sound_manager.play_sfx("button_click")
                    return

            # Workshop 버튼 클릭
            if "workshop" in self.menu_button_rects:
                if self.menu_button_rects["workshop"].collidepoint(mouse_pos):
                    self.sound_manager.play_sfx("button_click")
                    # WorkshopMode로 전환 (현재 모드 위에 push)
                    self._open_workshop()
                    return

            # Quit 버튼 클릭
            if "quit" in self.menu_button_rects:
                if self.menu_button_rects["quit"].collidepoint(mouse_pos):
                    self.game_data["previous_game_state"] = config.GAME_STATE_PAUSED
                    self.game_data["game_state"] = config.GAME_STATE_QUIT_CONFIRM
                    self.sound_manager.play_sfx("button_click")
                    return

        # 키보드 단축키
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_w:
                # W 키로 Workshop 열기
                self.sound_manager.play_sfx("button_click")
                self._open_workshop()

    def _handle_quit_confirm_event(self, event: pygame.event.Event):
        """종료 확인 이벤트"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_y:
                self.engine.save_shared_state()
                self.request_quit()
            elif event.key == pygame.K_n or event.key == pygame.K_ESCAPE:
                if "previous_game_state" in self.game_data:
                    self.game_data["game_state"] = self.game_data["previous_game_state"]
                else:
                    self.game_data["game_state"] = config.GAME_STATE_RUNNING

    def _handle_turret_placement_event(self, event: pygame.event.Event):
        """터렛 배치 이벤트"""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_x, mouse_y = event.pos

            # 터렛 생성
            new_turret = Turret(pos=(mouse_x, mouse_y))
            self.turrets.append(new_turret)
            self.sound_manager.play_sfx("turret_place")

            self.player.pending_turret_placements -= 1
            print(f"INFO: Turret placed at ({mouse_x}, {mouse_y}). Remaining: {self.player.pending_turret_placements}")

            # 모든 터렛 배치 완료
            if self.player.pending_turret_placements <= 0:
                self.game_data["game_state"] = config.GAME_STATE_RUNNING
                print("INFO: All turrets placed. Returning to game.")

    def _auto_place_turrets(self):
        """터렛을 쿨다운 UI 상단에 자동 배치 (utils.auto_place_turrets 사용)"""
        auto_place_turrets(self.turrets, self.game_data, self.screen_size,
                          Turret, self.sound_manager)

    def _transition_background(self, new_wave: int):
        """배경 전환"""
        if new_wave == self.current_wave_bg:
            return

        if new_wave in config.WAVE_BACKGROUND_POOLS:
            bg_pool = config.WAVE_BACKGROUND_POOLS[new_wave]
            selected_bg_num = random.choice(bg_pool)
            new_bg = self.background_image_cache.get(selected_bg_num)
            self.wave_backgrounds[new_wave] = new_bg
        else:
            new_bg = pygame.Surface(self.screen_size)
            new_bg.fill((0, 0, 0))

        old_bg = self.wave_backgrounds.get(self.current_wave_bg, self.current_background)
        if old_bg is None:
            old_bg = pygame.Surface(self.screen_size)
            old_bg.fill((0, 0, 0))

        effect_type = config.WAVE_TRANSITION_EFFECTS.get(new_wave, "fade_in")
        self.background_transition = BackgroundTransition(
            old_bg=old_bg, new_bg=new_bg, screen_size=self.screen_size,
            effect_type=effect_type, duration=config.BACKGROUND_TRANSITION_DURATION
        )

        self.current_wave_bg = new_wave
        self.current_background = new_bg

    def _restart_game(self):
        """게임 재시작"""
        config.BOSS_RUSH_MODE = False
        config.BOSS_RUSH_COMPLETED_WAVES = []

        self.game_data = reset_game_data()
        self.game_data['score'] = self.engine.shared_state.get('global_score', 0)
        self.game_data['game_state'] = config.GAME_STATE_WAVE_PREPARE

        self.spawn_player(
            pos=self.config.player_start_pos,
            upgrades=self.engine.shared_state.get('player_upgrades', {})
        )

        self.enemies.clear()
        self.bullets.clear()
        self.gems.clear()
        self.effects.clear()
        self.damage_number_manager.clear()
        self.turrets.clear()
        self.drones.clear()
        self.death_effect_manager.clear()

        print("INFO: Game restarted")

    def _start_boss_rush(self):
        """보스 러시 시작"""
        config.BOSS_RUSH_MODE = True
        config.BOSS_RUSH_COMPLETED_WAVES = []

        self.game_data['current_wave'] = config.BOSS_WAVES[0]
        self.game_data['kills_this_wave'] = 0
        self.game_data['wave_state'] = 'NOT_STARTED'

        self.enemies.clear()
        self.bullets.clear()
        self.gems.clear()
        self.effects.clear()
        self.damage_number_manager.clear()
        self.turrets.clear()
        self.drones.clear()

        self.player.hp = self.player.max_hp
        self.game_data["game_state"] = config.GAME_STATE_WAVE_PREPARE

        print("INFO: Boss Rush started!")

    def _mark_episode_complete(self):
        """현재 에피소드를 완료 처리"""
        current_act = self.engine.shared_state.get('current_act', 1)
        current_episode = self.engine.shared_state.get('current_episode', 1)

        # completed_episodes 딕셔너리 가져오기
        completed = self.engine.shared_state.get('completed_episodes')
        if completed is None or not isinstance(completed, dict):
            completed = {}

        # ACT ID를 문자열로 변환 (JSON 호환)
        act_key = str(current_act)

        if act_key not in completed:
            completed[act_key] = []

        if current_episode not in completed[act_key]:
            completed[act_key].append(current_episode)
            print(f"INFO: Episode {current_episode} of ACT {current_act} completed!")

        self.engine.shared_state['completed_episodes'] = completed

        # 점수를 global_score에 저장
        self.engine.shared_state['global_score'] = self.game_data.get('score', 0)

    def _return_to_base(self):
        """Base Hub로 귀환"""
        from modes.base_hub_mode import BaseHubMode
        self.request_switch_mode(BaseHubMode)
        print("INFO: Returning to Base Hub")

    def _complete_side_mission_and_return(self):
        """사이드 미션 완료 처리 후 BaseHub로 귀환 (base_mode 공통 메서드 사용)"""
        super()._complete_mission_and_return(mission_type="side")

    def on_exit(self):
        """모드 종료"""
        # 커스텀 커서 비활성화 (원래 커서 복원)
        if self.custom_cursor_enabled:
            self.enable_custom_cursor(False)

        # 상태 저장
        self.engine.shared_state['global_score'] = self.game_data.get('score', 0)
        if self.player:
            self.engine.shared_state['player_upgrades'] = self.player.upgrades

        super().on_exit()

    def _open_workshop(self):
        """Workshop(정비소) 모드 열기"""
        # 현재 상태 저장
        self.engine.shared_state['global_score'] = self.game_data.get('score', 0)
        if self.player:
            self.engine.shared_state['player_upgrades'] = self.player.upgrades

        # WorkshopMode를 현재 모드 위에 push
        from modes.workshop_mode import WorkshopMode
        self.request_push_mode(WorkshopMode)

    def on_resume(self, return_data=None):
        """Workshop에서 돌아올 때 호출"""
        super().on_resume(return_data)
        # Workshop에서 변경된 업그레이드 적용
        self.game_data['score'] = self.engine.shared_state.get('global_score', 0)
        if self.player:
            new_upgrades = self.engine.shared_state.get('player_upgrades', {})
            self.player.upgrades = new_upgrades
            self.player.calculate_stats_from_upgrades()
            print("INFO: Player upgrades applied from Workshop")


print("INFO: wave_mode.py loaded")
