# modes/siege_mode.py
"""
SiegeMode - Galaga Style Fixed Shooter Mode
갈라그 스타일 고정 슈터 모드

특징:
- 플레이어는 화면 하단에 고정 (좌우 이동만 가능)
- 적은 포메이션을 이루며 화면 상단에 배치
- 웨이브 기반 스테이지 진행
- 베지어 곡선 진입, 다이브 공격
"""

import pygame
import math
import random
from typing import Dict, Any, List
from pathlib import Path

import config
from modes.base_mode import GameMode, ModeConfig
from systems.combat_system import CombatSystem
from systems.effect_system import EffectSystem
from systems.ui_system import UISystem, UIConfig
# DamageFlash, LevelUpEffect, HPBarShake는 base_mode에서 제공

# 갈라그 스타일 오브젝트
from entities.siege_entities import FormationEnemy, WaveManager

# 갈라그 설정
try:
    from mode_configs import config_siege as cfg
except ImportError:
    import mode_configs.config_siege as cfg


class SiegeMode(GameMode):
    """
    갈라그 스타일 공성 모드

    특징:
    - 고정 슈터 (플레이어 Y 고정, 좌우만 이동)
    - 포메이션 기반 적 배치
    - 웨이브 시스템
    - 다이브 공격
    """

    def get_config(self) -> ModeConfig:
        """갈라그 모드 설정"""
        # 실제 화면 크기 사용 (self.screen_size는 __init__에서 이미 설정됨)
        screen_w = self.screen_size[0]
        screen_h = self.screen_size[1]

        # 플레이어 Y 위치 (화면 하단에서 120px 위)
        player_y = screen_h - 120

        return ModeConfig(
            mode_name="siege",
            # 탑다운 뷰 - 원근법 비활성화
            perspective_enabled=False,
            perspective_apply_to_player=False,
            perspective_apply_to_enemies=False,
            perspective_apply_to_bullets=False,
            perspective_apply_to_gems=False,
            # 플레이어 (실제 화면 크기 기반)
            player_speed_multiplier=1.0,
            player_start_pos=(screen_w // 2, player_y),
            player_afterimages_enabled=False,
            # 배경
            background_type="stars",
            parallax_enabled=False,
            meteor_enabled=False,
            # UI
            show_wave_ui=True,
            show_stage_ui=False,
            show_minimap=False,
            show_skill_indicators=False,
            # 게임플레이
            wave_system_enabled=True,
            spawn_system_enabled=False,
            random_events_enabled=False,
            # 에셋
            asset_prefix="siege",
        )

    def init(self):
        """갈라그 모드 초기화"""
        config.GAME_MODE = "siege"

        # 적 이미지 캐시 리셋 (크기 변경 적용)
        FormationEnemy.reset_image_cache()

        # 시스템 초기화
        self.combat_system = CombatSystem()
        self.effect_system = EffectSystem()
        self.ui_system = UISystem(UIConfig(
            show_hp_bar=True,
            show_score=True,
            show_wave_info=True,
            show_level_info=False,
            show_minimap=False,
        ))

        # 게임 데이터
        self.game_data = {
            'game_state': config.GAME_STATE_RUNNING,
            'score': 0,
            'wave': 1,
            'high_score': 0,
        }

        # 플레이어 생성 (하단 중앙)
        self.spawn_player(
            pos=self.config.player_start_pos,
            upgrades={}
        )
        if self.player:
            self.player.disable_afterimages = True

        # 웨이브 매니저 (실제 화면 크기 전달)
        self.wave_manager = WaveManager(self.screen_size)

        # 적 총알 리스트
        self.enemy_bullets: List[Dict] = []

        # 배경 별 (실제 화면 크기 사용)
        self.stars = self._create_stars()

        # 웨이브 상태
        self.wave_clear_timer = 0.0
        self.wave_clear_delay = cfg.WAVE_CLEAR_DELAY
        self.waiting_for_next_wave = False
        self.game_complete = False

        # 시각적 효과 (base_mode의 공통 메서드 사용)
        self._init_visual_feedback_effects()

        # 메뉴 버튼
        self.menu_button_rects: Dict[str, pygame.Rect] = {}

        # 첫 웨이브 시작
        self.wave_manager.start_wave(1)

        print(f"INFO: SiegeMode (Galaga Style) initialized - Wave 1")

    def _create_stars(self) -> List[Dict]:
        """배경 별 생성 (실제 화면 크기 사용)"""
        stars = []
        screen_w, screen_h = self.screen_size
        for _ in range(cfg.STAR_COUNT):
            stars.append({
                'x': random.randint(0, screen_w),
                'y': random.randint(0, screen_h),
                'size': random.randint(1, 3),
                'speed': random.uniform(20, 80),
                'brightness': random.randint(100, 255),
            })
        return stars

    def update(self, dt: float, current_time: float):
        """갈라그 모드 업데이트"""
        if self.game_data["game_state"] != config.GAME_STATE_RUNNING:
            return

        # 공통 업데이트
        self.update_common(dt, current_time)

        # 배경 별 업데이트
        self._update_stars(dt)

        # 플레이어 이동 (좌우만)
        self._update_player_fixed_shooter(dt, current_time)

        # 객체 업데이트
        self.update_objects(dt)

        # 웨이브 매니저 업데이트 (실제 화면 크기 기반 기본값)
        screen_w, screen_h = self.screen_size
        default_player_pos = pygame.math.Vector2(screen_w // 2, screen_h - 120)
        score, wave_complete = self.wave_manager.update(
            dt, current_time,
            self.player.pos if self.player else default_player_pos,
            self.enemy_bullets
        )
        self.game_data['score'] += score

        # 적 총알 업데이트
        self._update_enemy_bullets(dt)

        # HP 변화 감지
        hp_before = self.player.hp if self.player else 0

        # 충돌 처리
        self._process_collisions()

        # HP 감소 → 피격 효과 (base_mode 공통 메서드)
        self._trigger_damage_feedback(hp_before)

        # 시각 효과 업데이트 (base_mode 공통 메서드)
        self._update_visual_feedback(dt)

        # 웨이브 클리어 처리
        if wave_complete and not self.waiting_for_next_wave:
            self.waiting_for_next_wave = True
            self.wave_clear_timer = 0.0
            self.level_up_effect.trigger(1)

        if self.waiting_for_next_wave:
            self.wave_clear_timer += dt
            if self.wave_clear_timer >= self.wave_clear_delay:
                self._start_next_wave()

        # 게임 오버 체크
        if self.player and self.player.hp <= 0:
            self.game_data["game_state"] = config.GAME_STATE_OVER

    def _update_stars(self, dt: float):
        """배경 별 업데이트 (아래로 스크롤)"""
        screen_w, screen_h = self.screen_size
        for star in self.stars:
            star['y'] += star['speed'] * dt
            if star['y'] > screen_h:
                star['y'] = 0
                star['x'] = random.randint(0, screen_w)

    def _update_player_fixed_shooter(self, dt: float, current_time: float):
        """플레이어 이동 (좌우만, Y 고정, 갈라그 스타일 행동반경 제한)"""
        if not self.player:
            return

        keys = pygame.key.get_pressed()

        # 실제 화면 크기 사용
        screen_w = self.screen_size[0]
        screen_h = self.screen_size[1]

        # 플레이어 Y 위치 (화면 하단에서 120px 위)
        player_y = screen_h - 120

        # 좌우 이동만 허용
        move_x = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            move_x = -1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            move_x = 1

        # 이동 적용 (속도 증가)
        speed = cfg.PLAYER_SPEED * dt
        self.player.pos.x += move_x * speed

        # 갈라그 스타일 행동반경 제한:
        # 포메이션 너비에 맞춰 플레이어도 해당 영역 내에서만 이동
        # PLAYER_AREA_MARGIN = 0.15 → 화면 양쪽 15% 마진
        margin = cfg.PLAYER_AREA_MARGIN
        min_x = screen_w * margin
        max_x = screen_w * (1 - margin)

        # 플레이어 반폭 고려
        half_width = 50
        if self.player.hitbox:
            half_width = self.player.hitbox.width // 2

        # 경계 적용 (마진 + 플레이어 반폭)
        self.player.pos.x = max(min_x + half_width, min(max_x - half_width, self.player.pos.x))

        # Y 위치 고정 (항상 강제)
        self.player.pos.y = player_y

        # image_rect와 hitbox 동기화 (중요!)
        self.player.image_rect.center = (int(self.player.pos.x), int(self.player.pos.y))
        self.player.hitbox.center = self.player.image_rect.center

        # 플레이어 상태 업데이트 (무기 쿨다운, 재생 등)
        self.player.update(dt, self.screen_size, current_time)
        self.player.update_movement_effects(dt)

        # Y 위치 및 rect 강제 고정 (update 내에서 변경되었을 수 있음)
        self.player.pos.y = player_y
        self.player.image_rect.center = (int(self.player.pos.x), int(self.player.pos.y))
        self.player.hitbox.center = self.player.image_rect.center

    def _update_enemy_bullets(self, dt: float):
        """적 총알 업데이트"""
        screen_w, screen_h = self.screen_size
        for bullet in self.enemy_bullets[:]:
            bullet["pos"] += bullet["vel"] * dt

            # 화면 밖 제거
            if (bullet["pos"].x < -50 or bullet["pos"].x > screen_w + 50 or
                bullet["pos"].y < -50 or bullet["pos"].y > screen_h + 50):
                self.enemy_bullets.remove(bullet)
                continue

            # 플레이어 피격
            if self.player:
                distance = bullet["pos"].distance_to(self.player.pos)
                if distance < 25:  # 플레이어 충돌 반경
                    self.player.take_damage(bullet["damage"])
                    if bullet in self.enemy_bullets:
                        self.enemy_bullets.remove(bullet)

    def _process_collisions(self):
        """충돌 처리"""
        if not self.player:
            return

        # 플레이어 총알 vs 적
        enemy_rects = self.wave_manager.get_all_enemy_rects()

        for bullet in self.bullets[:]:
            if bullet not in self.bullets:
                continue

            bullet_rect = pygame.Rect(
                bullet.pos.x - 5, bullet.pos.y - 5, 10, 10
            )

            for enemy, enemy_rect in enemy_rects:
                if not enemy.is_alive:
                    continue

                if bullet_rect.colliderect(enemy_rect):
                    # 데미지 적용
                    score = enemy.take_damage(bullet.damage)
                    self.game_data['score'] += score

                    # 총알 제거
                    if bullet in self.bullets:
                        self.bullets.remove(bullet)
                    break

        # 플레이어 vs 적 충돌 (접촉 데미지)
        for enemy, enemy_rect in enemy_rects:
            if not enemy.is_alive:
                continue

            player_rect = pygame.Rect(
                self.player.pos.x - 20, self.player.pos.y - 20, 40, 40
            )

            if player_rect.colliderect(enemy_rect):
                # 접촉 데미지
                self.player.take_damage(30)
                # 적도 파괴
                score = enemy.take_damage(9999)
                self.game_data['score'] += score

    def _start_next_wave(self):
        """다음 웨이브 시작"""
        self.waiting_for_next_wave = False
        next_wave = self.wave_manager.current_wave + 1

        if next_wave > cfg.TOTAL_WAVES:
            # 모든 웨이브 클리어
            self.game_complete = True
            self.game_data["game_state"] = config.GAME_STATE_VICTORY
            print("INFO: All waves cleared! Victory!")
        else:
            self.game_data['wave'] = next_wave
            self.wave_manager.start_wave(next_wave)
            print(f"INFO: Starting Wave {next_wave}")

    # =========================================================
    # 오토파일럿
    # =========================================================
    def _trigger_auto_ultimate(self):
        """오토파일럿 궁극기"""
        if self.player and self.player.activate_ultimate([]):
            print("INFO: [AUTO] Ultimate activated!")

    def _trigger_auto_ability(self):
        """오토파일럿 특수 능력"""
        if not self.player:
            return
        if self.player.use_ship_ability([], self.effects):
            print("INFO: [AUTO] Ship ability activated!")

    # =========================================================
    # 렌더링
    # =========================================================
    def render(self, screen: pygame.Surface):
        """갈라그 모드 렌더링"""
        # 배경 (검정)
        screen.fill((0, 0, 10))

        # 별 배경
        self._render_stars(screen)

        # 적 렌더링
        self.wave_manager.draw(screen)

        # 적 총알
        for bullet in self.enemy_bullets:
            size = bullet.get("size", 6)
            color = bullet.get("color", (255, 100, 100))
            pygame.draw.circle(screen, color,
                             (int(bullet["pos"].x), int(bullet["pos"].y)), size)

        # 공통 렌더링 (플레이어, 총알, 이펙트)
        self.render_common(screen)

        # HUD
        self._render_hud(screen)

        # 웨이브 클리어 텍스트
        if self.waiting_for_next_wave:
            self._render_wave_clear(screen)

        # 상태별 오버레이
        self._render_overlay(screen)

        # 시각 효과 (최상위)
        self.damage_flash.render(screen)
        self.level_up_effect.render(screen)

    def _render_stars(self, screen: pygame.Surface):
        """별 배경 렌더링"""
        for star in self.stars:
            brightness = star['brightness']
            color = (brightness, brightness, brightness)
            pygame.draw.circle(screen, color,
                             (int(star['x']), int(star['y'])), star['size'])

    def _render_hud(self, screen: pygame.Surface):
        """HUD 렌더링"""
        screen_w, screen_h = self.screen_size

        # HP 바
        if self.player:
            self.ui_system._draw_hp_bar(screen, self.screen_size, self.fonts, self.player, 20)

        # 점수
        score_text = self.fonts["medium"].render(
            f"SCORE: {self.game_data['score']:,}", True, config.WHITE
        )
        screen.blit(score_text, (20, 20))

        # 하이스코어
        high_score = max(self.game_data['score'], self.game_data.get('high_score', 0))
        high_text = self.fonts["small"].render(
            f"HIGH: {high_score:,}", True, (150, 150, 150)
        )
        screen.blit(high_text, (20, 55))

        # 웨이브 정보
        wave_name = self.wave_manager.get_wave_name()
        wave_text = self.fonts["medium"].render(wave_name, True, (255, 255, 100))
        wave_rect = wave_text.get_rect(midtop=(screen_w // 2, 10))
        screen.blit(wave_text, wave_rect)

        # 남은 적 수
        enemies_alive = self.wave_manager.get_enemies_alive()
        enemies_text = self.fonts["small"].render(
            f"ENEMIES: {enemies_alive}", True, (255, 150, 100)
        )
        enemies_rect = enemies_text.get_rect(midtop=(screen_w // 2, 45))
        screen.blit(enemies_text, enemies_rect)

    def _render_wave_clear(self, screen: pygame.Surface):
        """웨이브 클리어 텍스트"""
        screen_w, screen_h = self.screen_size
        # 깜박임 효과
        pulse = 0.5 + 0.5 * math.sin(pygame.time.get_ticks() / 150)

        clear_text = self.fonts["huge"].render("WAVE CLEAR!", True,
                                               (int(100 + 155 * pulse), 255, int(100 + 155 * pulse)))
        clear_rect = clear_text.get_rect(center=(screen_w // 2, screen_h // 2 - 50))
        screen.blit(clear_text, clear_rect)

        # 보너스 점수 표시
        bonus = self.wave_manager.current_wave * 1000
        bonus_text = self.fonts["medium"].render(f"BONUS: {bonus:,}", True, (255, 255, 100))
        bonus_rect = bonus_text.get_rect(center=(screen_w // 2, screen_h // 2 + 20))
        screen.blit(bonus_text, bonus_rect)

    def _render_overlay(self, screen: pygame.Surface):
        """상태별 오버레이"""
        from ui_render import draw_pause_and_over_screens

        state = self.game_data["game_state"]

        if state == config.GAME_STATE_PAUSED:
            self.menu_button_rects = draw_pause_and_over_screens(
                screen, self.screen_size,
                self.fonts["huge"], self.fonts["medium"], self.game_data
            )
        elif state == config.GAME_STATE_OVER:
            self.menu_button_rects = draw_pause_and_over_screens(
                screen, self.screen_size,
                self.fonts["huge"], self.fonts["medium"], self.game_data
            )
        elif state == config.GAME_STATE_VICTORY:
            self._render_victory_overlay(screen)
        elif state == config.GAME_STATE_QUIT_CONFIRM:
            self.ui_system.draw_quit_confirm_overlay(screen, self.screen_size, self.fonts)

    def _render_victory_overlay(self, screen: pygame.Surface):
        """승리 오버레이"""
        screen_w, screen_h = self.screen_size

        overlay = pygame.Surface(self.screen_size, pygame.SRCALPHA)
        overlay.fill((0, 50, 0, 180))
        screen.blit(overlay, (0, 0))

        # 승리 텍스트 (실제 화면 크기 사용)
        victory_text = self.fonts["huge"].render("MISSION COMPLETE!", True, (100, 255, 100))
        victory_rect = victory_text.get_rect(center=(screen_w // 2, screen_h // 2 - 80))
        screen.blit(victory_text, victory_rect)

        # 최종 점수
        final_score = self.game_data['score']
        score_text = self.fonts["medium"].render(f"FINAL SCORE: {final_score:,}", True, (255, 255, 100))
        score_rect = score_text.get_rect(center=(screen_w // 2, screen_h // 2))
        screen.blit(score_text, score_rect)

        # 안내 텍스트
        help_text = self.fonts["medium"].render("Press R to Restart, Q to Quit", True, config.WHITE)
        help_rect = help_text.get_rect(center=(screen_w // 2, screen_h // 2 + 80))
        screen.blit(help_text, help_rect)

    # =========================================================
    # 이벤트 처리
    # =========================================================
    def handle_event(self, event: pygame.event.Event):
        """이벤트 처리"""
        if self.handle_common_events(event):
            return

        state = self.game_data["game_state"]

        if state == config.GAME_STATE_RUNNING:
            self._handle_running_event(event)
        elif state == config.GAME_STATE_PAUSED:
            self._handle_paused_event(event)
        elif state == config.GAME_STATE_OVER:
            self._handle_game_over_event(event)
        elif state == config.GAME_STATE_VICTORY:
            self._handle_victory_event(event)
        elif state == config.GAME_STATE_QUIT_CONFIRM:
            self._handle_quit_confirm_event(event)

    def _handle_running_event(self, event: pygame.event.Event):
        """게임 실행 중 이벤트 (갈라가 스타일)"""
        if not self.player:
            return

        if event.type == pygame.MOUSEBUTTONDOWN:
            # 좌클릭: 클릭 위치로 이동
            if event.button == 1:
                self.player.set_mouse_target(event.pos)
            # 우클릭: 위쪽으로 발사 (갈라가 스타일)
            elif event.button == 3:
                self._fire_upward()

        # 스페이스바: 위쪽으로 발사
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            self._fire_upward()

    def _fire_at_mouse(self, mouse_pos):
        """마우스 위치로 발사"""
        if self.player and self.player.weapon.can_shoot():
            target_pos = pygame.math.Vector2(mouse_pos)
            self.player.weapon.fire(
                self.player.pos, target_pos, self.bullets,
                self.player.is_piercing, self.player
            )
            self.sound_manager.play_sfx("shoot")

    def _fire_upward(self):
        """위쪽으로 발사"""
        if self.player and self.player.weapon.can_shoot():
            # 플레이어 위쪽으로 발사
            target_pos = pygame.math.Vector2(self.player.pos.x, 0)
            self.player.weapon.fire(
                self.player.pos, target_pos, self.bullets,
                self.player.is_piercing, self.player
            )
            self.sound_manager.play_sfx("shoot")

    def _handle_paused_event(self, event: pygame.event.Event):
        """일시정지 이벤트"""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = event.pos

            if "resume" in self.menu_button_rects:
                if self.menu_button_rects["resume"].collidepoint(mouse_pos):
                    self.game_data["game_state"] = config.GAME_STATE_RUNNING
                    self.sound_manager.play_sfx("button_click")
                    return

            if "workshop" in self.menu_button_rects:
                if self.menu_button_rects["workshop"].collidepoint(mouse_pos):
                    self.sound_manager.play_sfx("button_click")
                    self._open_workshop()
                    return

            if "quit" in self.menu_button_rects:
                if self.menu_button_rects["quit"].collidepoint(mouse_pos):
                    self.game_data["previous_game_state"] = config.GAME_STATE_PAUSED
                    self.game_data["game_state"] = config.GAME_STATE_QUIT_CONFIRM
                    self.sound_manager.play_sfx("button_click")
                    return

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_w:
                self.sound_manager.play_sfx("button_click")
                self._open_workshop()

    def _handle_game_over_event(self, event: pygame.event.Event):
        """게임 오버 이벤트"""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = event.pos

            if "restart" in self.menu_button_rects:
                if self.menu_button_rects["restart"].collidepoint(mouse_pos):
                    self._restart_mission()
                    self.sound_manager.play_sfx("button_click")
                    return

            if "quit" in self.menu_button_rects:
                if self.menu_button_rects["quit"].collidepoint(mouse_pos):
                    self.request_quit()
                    return

        if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
            self._restart_mission()

    def _handle_victory_event(self, event: pygame.event.Event):
        """승리 이벤트 - 사이드 미션일 경우 BaseHub로 귀환"""
        if event.type == pygame.KEYDOWN:
            is_side_mission = self.engine.shared_state.get('is_side_mission', False)

            if event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                # 미션 완료 후 귀환
                if is_side_mission:
                    self._complete_siege_mission_and_return()
                else:
                    self.request_quit()
            elif event.key == pygame.K_r:
                self._restart_mission()
            elif event.key == pygame.K_q or event.key == pygame.K_ESCAPE:
                if is_side_mission:
                    self._complete_siege_mission_and_return()
                else:
                    self.request_quit()

    def _complete_siege_mission_and_return(self):
        """시즈 미션 완료 처리 후 BaseHub로 귀환 (base_mode 공통 메서드 사용)"""
        super()._complete_mission_and_return(mission_type="siege")

    def _handle_quit_confirm_event(self, event: pygame.event.Event):
        """종료 확인 이벤트"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_y:
                self.request_quit()
            elif event.key == pygame.K_n or event.key == pygame.K_ESCAPE:
                self.game_data["game_state"] = config.GAME_STATE_RUNNING

    def _restart_mission(self):
        """미션 재시작"""
        self.init()
        print("INFO: Mission restarted")

    def _open_workshop(self):
        """Workshop 열기"""
        self.engine.shared_state['global_score'] = self.game_data.get('score', 0)
        if self.player:
            self.engine.shared_state['player_upgrades'] = self.player.upgrades

        from modes.workshop_mode import WorkshopMode
        self.request_push_mode(WorkshopMode)

    def on_resume(self, return_data=None):
        """Workshop에서 돌아올 때"""
        super().on_resume(return_data)
        self.game_data['score'] = self.engine.shared_state.get('global_score', 0)
        if self.player:
            new_upgrades = self.engine.shared_state.get('player_upgrades', {})
            self.player.upgrades = new_upgrades
            self.player.calculate_stats_from_upgrades()
            print("INFO: Player upgrades applied from Workshop")


print("INFO: siege_mode.py (Galaga Style) loaded")
