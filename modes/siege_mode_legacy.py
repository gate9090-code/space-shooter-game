# modes/siege_mode.py
"""
SiegeMode - 공성 모드
타워 파괴 목표, 탑다운 뷰, 타일맵 기반
"""

import pygame
from typing import Dict, Any, List
from pathlib import Path

import config
from modes.base_mode import GameMode, ModeConfig
from systems.combat_system import CombatSystem
from systems.effect_system import EffectSystem
from systems.ui_system import UISystem, UIConfig
from objects import DamageFlash, LevelUpEffect
from ui import HPBarShake

# siege_objects에서 클래스 임포트
from modes.siege_objects import TileMap, Tower, DestructibleWall, GuardEnemy, PatrolEnemy


class SiegeMode(GameMode):
    """
    공성 모드

    특징:
    - 타워 파괴 목표
    - 탑다운 뷰 (원근법 비활성화)
    - 타일맵 기반 이동/충돌
    - 경비병/순찰병 AI
    """

    def get_config(self) -> ModeConfig:
        """공성 모드 설정"""
        return ModeConfig(
            mode_name="siege",
            # 탑다운 뷰 - 원근법 비활성화
            perspective_enabled=False,
            perspective_apply_to_player=False,
            perspective_apply_to_enemies=False,
            perspective_apply_to_bullets=False,
            perspective_apply_to_gems=False,
            # 플레이어
            player_speed_multiplier=0.8,
            player_start_pos=(960, 380),  # 맵 입구 상단
            player_afterimages_enabled=False,
            # 배경
            background_type="tilemap",
            parallax_enabled=False,
            meteor_enabled=False,
            # UI
            show_wave_ui=False,
            show_stage_ui=False,
            show_minimap=True,
            show_skill_indicators=False,
            # 게임플레이
            wave_system_enabled=False,
            spawn_system_enabled=False,
            random_events_enabled=False,
            # 에셋
            asset_prefix="siege",
        )

    def init(self):
        """공성 모드 초기화"""
        # config에 모드 설정
        config.GAME_MODE = "siege"

        # 시스템 초기화
        self.combat_system = CombatSystem()
        self.effect_system = EffectSystem()
        self.ui_system = UISystem(UIConfig(
            show_hp_bar=True,
            show_score=False,
            show_wave_info=False,
            show_level_info=False,
            show_minimap=True,
        ))

        # 게임 데이터 초기화
        self.game_data = {
            'game_state': config.GAME_STATE_RUNNING,
            'score': 0,
            'mission_objectives': [],
        }

        # 타일맵 생성
        self._init_tilemap()

        # 플레이어 생성
        self.spawn_player(
            pos=self.config.player_start_pos,
            upgrades={}  # 공성 모드는 업그레이드 없이 시작
        )
        if self.player:
            self.player.disable_afterimages = True

        # 공성 모드 전용 객체
        self.towers: List[Tower] = []
        self.destructible_walls: List[DestructibleWall] = []
        self.guards: List[GuardEnemy] = []
        self.patrols: List[PatrolEnemy] = []
        self.enemy_bullets: List[Dict] = []

        # 타일맵에서 객체 생성
        self._spawn_siege_objects()

        # 배경 이미지
        self._load_background()

        # 메뉴 버튼 클릭 영역 (마우스 클릭 지원)
        self.menu_button_rects: Dict[str, pygame.Rect] = {}

        # 시각적 피드백 효과
        self.damage_flash = DamageFlash(self.screen_size)
        self.level_up_effect = LevelUpEffect(self.screen_size)
        self.hp_bar_shake = HPBarShake()

        print(f"INFO: SiegeMode initialized - {len(self.towers)} towers, "
              f"{len(self.guards)} guards, {len(self.patrols)} patrols")

    def _init_tilemap(self):
        """타일맵 초기화"""
        # 타일맵 위치 계산 (화면 중앙)
        tilemap_offset_x = (self.screen_size[0] - 800) // 2  # 10타일 * 80px
        tilemap_offset_y = (self.screen_size[1] - 640) // 2  # 8타일 * 80px (중앙 배치)

        self.tilemap = TileMap(
            stage_num=1,
            x_offset=tilemap_offset_x,
            y_offset=tilemap_offset_y
        )

        # 타일맵 경계 저장
        self.tilemap_bounds = {
            'x_min': tilemap_offset_x,
            'x_max': tilemap_offset_x + self.tilemap.width * 80,
            'y_min': tilemap_offset_y,
            'y_max': tilemap_offset_y + self.tilemap.height * 80,
        }

    def _spawn_siege_objects(self):
        """공성 모드 객체 생성"""
        # 타워 생성
        for tower_pos in self.tilemap.tower_positions:
            self.towers.append(Tower(*tower_pos))

        # 파괴 가능한 벽 생성
        for wall_pos in self.tilemap.destructible_walls:
            self.destructible_walls.append(DestructibleWall(*wall_pos))

        # 경비병 생성 (타워 주변)
        guard_offsets = [(-100, 0), (100, 0), (0, -100), (0, 100)]
        for tower_pos in self.tilemap.tower_positions:
            for offset_x, offset_y in guard_offsets:
                guard_x = tower_pos[0] + offset_x
                guard_y = tower_pos[1] + offset_y
                self.guards.append(GuardEnemy(guard_x, guard_y))

        # 순찰병 생성
        patrol_positions = [(960, 760)] * 5  # 중심에서 시작
        for i, pos in enumerate(patrol_positions):
            patrol = PatrolEnemy(*pos)
            patrol.patrol_angle = i * 2 * 3.14159 / len(patrol_positions)
            patrol.patrol_radius = 300
            self.patrols.append(patrol)

    def _load_background(self):
        """배경 이미지 로드"""
        self.floor_image = None
        # 공성 모드 전용 배경 폴더 사용
        floor_path = Path("assets/siege_mode/backgrounds/siege_bg_01.jpg")

        if floor_path.exists():
            try:
                self.floor_image = pygame.image.load(str(floor_path)).convert()
                self.floor_image = pygame.transform.scale(self.floor_image, self.screen_size)
                print(f"INFO: Loaded siege background: {floor_path}")
            except Exception as e:
                print(f"WARNING: Failed to load floor image: {e}")
        else:
            print(f"WARNING: Siege background not found: {floor_path}")

    def update(self, dt: float, current_time: float):
        """공성 모드 업데이트"""
        if self.game_data["game_state"] != config.GAME_STATE_RUNNING:
            return

        # 공통 업데이트
        self.update_common(dt, current_time)

        # 플레이어 이동 (타일맵 충돌 체크 포함)
        self._update_player_with_collision(dt, current_time)

        # 객체 업데이트
        self.update_objects(dt)

        # 공성 전용 업데이트
        self._update_siege_objects(dt, current_time)

        # HP 변화 감지를 위해 이전 HP 저장
        hp_before = self.player.hp if self.player else 0

        # 충돌 처리
        self._process_siege_collisions()

        # HP 감소 감지 → 피격 효과 트리거
        if self.player and hp_before > self.player.hp:
            damage_taken = hp_before - self.player.hp
            damage_ratio = damage_taken / self.player.max_hp
            self.damage_flash.trigger(damage_ratio)
            self.hp_bar_shake.trigger(damage_ratio)

        # 시각적 피드백 효과 업데이트
        self.damage_flash.update()
        self.hp_bar_shake.update()
        self.level_up_effect.update(dt)

        # 승리 조건 체크
        self._check_victory()

        # 게임 오버 체크
        if self.player and self.player.hp <= 0:
            self.game_data["game_state"] = config.GAME_STATE_OVER

    def _update_player_with_collision(self, dt: float, current_time: float):
        """플레이어 이동 (타일맵 충돌 체크)"""
        if not self.player:
            return

        old_pos = self.player.pos.copy()
        keys = pygame.key.get_pressed()
        self.player.move(keys, dt, self.screen_size, current_time, self.game_data)

        # 타일맵 영역 내에서 벽 충돌 체크
        bounds = self.tilemap_bounds
        if (bounds['x_min'] <= self.player.pos.x <= bounds['x_max'] and
            bounds['y_min'] <= self.player.pos.y <= bounds['y_max']):
            if not self.tilemap.is_walkable(self.player.pos.x, self.player.pos.y):
                self.player.pos = old_pos

        # 플레이어 상태 업데이트 (히트 플래시, 재생 등)
        self.player.update(dt, self.screen_size, current_time)
        self.player.update_movement_effects(dt)

    def _update_siege_objects(self, dt: float, current_time: float):
        """공성 전용 객체 업데이트"""
        # 경비병 업데이트
        for guard in self.guards:
            if guard.is_alive:
                guard.update(self.player.pos, current_time, self.enemy_bullets, self.tilemap)

        # 순찰병 업데이트
        for patrol in self.patrols:
            if patrol.is_alive:
                patrol.update(self.player.pos, current_time, dt, self.enemy_bullets, self.tilemap)

        # 적 총알 업데이트
        for bullet in self.enemy_bullets[:]:
            bullet["pos"] += bullet["vel"] * dt

            # 화면 밖 제거
            if (bullet["pos"].x < -50 or bullet["pos"].x > self.screen_size[0] + 50 or
                bullet["pos"].y < -50 or bullet["pos"].y > self.screen_size[1] + 50):
                self.enemy_bullets.remove(bullet)
                continue

            # 플레이어 피격
            distance = bullet["pos"].distance_to(self.player.pos)
            if distance < 20:
                self.player.take_damage(bullet["damage"])
                if bullet in self.enemy_bullets:
                    self.enemy_bullets.remove(bullet)

    def _process_siege_collisions(self):
        """공성 모드 충돌 처리"""
        # 플레이어 총알 vs 타워
        for bullet in self.bullets[:]:
            if bullet not in self.bullets:
                continue

            for tower in self.towers:
                if not tower.is_alive:
                    continue

                distance = bullet.pos.distance_to(tower.pos)
                if distance < (config.TOWER_SIZE / 2 + bullet.hitbox.width / 2):
                    tower.take_damage(bullet.damage)
                    if bullet in self.bullets:
                        self.bullets.remove(bullet)
                    break

        # 플레이어 총알 vs 파괴 가능한 벽
        for bullet in self.bullets[:]:
            if bullet not in self.bullets:
                continue

            for wall in self.destructible_walls:
                if not wall.is_alive:
                    continue

                distance = bullet.pos.distance_to(wall.pos)
                if distance < (wall.size / 2 + bullet.hitbox.width / 2):
                    wall.take_damage(bullet.damage)
                    if bullet in self.bullets:
                        self.bullets.remove(bullet)
                    break

        # 플레이어 총알 vs 경비병
        for bullet in self.bullets[:]:
            if bullet not in self.bullets:
                continue

            for guard in self.guards:
                if not guard.is_alive:
                    continue

                distance = bullet.pos.distance_to(guard.pos)
                if distance < (guard.size / 2 + bullet.hitbox.width / 2):
                    guard.take_damage(bullet.damage)
                    if bullet in self.bullets:
                        self.bullets.remove(bullet)
                    break

        # 플레이어 총알 vs 순찰병
        for bullet in self.bullets[:]:
            if bullet not in self.bullets:
                continue

            for patrol in self.patrols:
                if not patrol.is_alive:
                    continue

                distance = bullet.pos.distance_to(patrol.pos)
                if distance < (patrol.size / 2 + bullet.hitbox.width / 2):
                    patrol.take_damage(bullet.damage)
                    if bullet in self.bullets:
                        self.bullets.remove(bullet)
                    break

    def _check_victory(self):
        """승리 조건 체크"""
        towers_alive = sum(1 for t in self.towers if t.is_alive)
        if towers_alive == 0:
            self.game_data["game_state"] = config.GAME_STATE_VICTORY
            # 승리 시 레벨업 효과 트리거
            self.level_up_effect.trigger(1)
            print("INFO: All towers destroyed! Mission complete!")

    # =========================================================
    # 오토파일럿 자동 스킬 발동 (base_mode 오버라이드)
    # =========================================================
    def _trigger_auto_ultimate(self):
        """오토파일럿 궁극기 자동 발동"""
        if self.player and self.player.activate_ultimate(self.enemies):
            print("INFO: [AUTO] Ultimate activated!")

    def _trigger_auto_ability(self):
        """오토파일럿 특수 능력 자동 발동"""
        if not self.player:
            return

        ability_type = getattr(self.player, 'ship_ability_type', None)
        if self.player.use_ship_ability(self.enemies, self.effects):
            print(f"INFO: [AUTO] Ship ability '{ability_type}' activated!")

    def render(self, screen: pygame.Surface):
        """공성 모드 렌더링"""
        # 배경
        if self.floor_image:
            screen.blit(self.floor_image, (0, 0))
        else:
            screen.fill((10, 10, 25))

        # 타일맵
        if self.tilemap:
            self.tilemap.draw(screen, camera_offset=(0, 0))

        # 파괴 가능한 벽
        for wall in self.destructible_walls:
            wall.draw(screen, camera_offset=(0, 0))

        # 타워
        for tower in self.towers:
            tower.draw(screen, camera_offset=(0, 0))

        # 경비병
        for guard in self.guards:
            guard.draw(screen, camera_offset=(0, 0))

        # 순찰병
        for patrol in self.patrols:
            patrol.draw(screen, camera_offset=(0, 0))

        # 적 총알
        for bullet in self.enemy_bullets:
            pygame.draw.circle(screen, (255, 100, 100),
                             (int(bullet["pos"].x), int(bullet["pos"].y)), 5)

        # ===== UI 요소들 (플레이어/적보다 먼저 렌더링) =====
        # HUD
        self._render_siege_hud(screen)

        # 오토파일럿 상태 표시
        if self.player and self.player.autopilot_enabled:
            self._draw_autopilot_indicator(screen)

        # 미니맵
        self._render_minimap(screen)

        # ===== 게임 객체 렌더링 (UI 위에 표시) =====
        self.render_common(screen)

        # 상태별 오버레이
        self._render_overlay(screen)

        # 시각적 피드백 효과 렌더링 (최상위 레이어)
        self.damage_flash.render(screen)
        self.level_up_effect.render(screen)

    def _draw_autopilot_indicator(self, screen: pygame.Surface):
        """오토파일럿 활성화 표시 (화면 우상단)"""
        import math

        # 깜박임 효과
        pulse = 0.7 + 0.3 * math.sin(pygame.time.get_ticks() / 200)

        # 배경 박스
        box_width, box_height = 100, 32
        box_x = self.screen_size[0] - box_width - 20
        box_y = 80

        # 반투명 배경
        box_surf = pygame.Surface((box_width, box_height), pygame.SRCALPHA)
        pygame.draw.rect(box_surf, (0, 150, 255, int(100 * pulse)), (0, 0, box_width, box_height), border_radius=6)
        pygame.draw.rect(box_surf, (0, 200, 255, int(200 * pulse)), (0, 0, box_width, box_height), 2, border_radius=6)
        screen.blit(box_surf, (box_x, box_y))

        # 텍스트
        font = self.fonts.get("small")
        if font:
            text_color = (int(150 + 105 * pulse), int(220 + 35 * pulse), 255)
            text_surf = font.render("AUTO", True, text_color)
            text_rect = text_surf.get_rect(center=(box_x + box_width // 2, box_y + box_height // 2))
            screen.blit(text_surf, text_rect)

    def _render_siege_hud(self, screen: pygame.Surface):
        """공성 모드 HUD"""
        # HP 바
        if self.player:
            self.ui_system._draw_hp_bar(screen, self.screen_size, self.fonts, self.player, 20)

        # 미션 목표
        towers_alive = sum(1 for t in self.towers if t.is_alive)
        total_towers = len(self.towers)

        mission_text = self.fonts["medium"].render(
            f"Towers: {total_towers - towers_alive}/{total_towers} destroyed",
            True, config.WHITE
        )
        mission_rect = mission_text.get_rect(midtop=(self.screen_size[0] // 2, 10))
        screen.blit(mission_text, mission_rect)

    def _render_minimap(self, screen: pygame.Surface):
        """미니맵 렌더링"""
        # 미니맵 크기와 위치
        minimap_size = 150
        minimap_x = self.screen_size[0] - minimap_size - 20
        minimap_y = 20

        # 미니맵 배경
        minimap_surface = pygame.Surface((minimap_size, minimap_size), pygame.SRCALPHA)
        minimap_surface.fill((0, 0, 0, 150))

        # 스케일 계산
        scale_x = minimap_size / self.screen_size[0]
        scale_y = minimap_size / self.screen_size[1]

        # 타워 표시 (빨간 사각형)
        for tower in self.towers:
            if tower.is_alive:
                x = int(tower.pos.x * scale_x)
                y = int(tower.pos.y * scale_y)
                pygame.draw.rect(minimap_surface, (255, 0, 0), (x - 3, y - 3, 6, 6))

        # 적 표시 (주황 점)
        for guard in self.guards:
            if guard.is_alive:
                x = int(guard.pos.x * scale_x)
                y = int(guard.pos.y * scale_y)
                pygame.draw.circle(minimap_surface, (255, 150, 0), (x, y), 2)

        for patrol in self.patrols:
            if patrol.is_alive:
                x = int(patrol.pos.x * scale_x)
                y = int(patrol.pos.y * scale_y)
                pygame.draw.circle(minimap_surface, (255, 200, 0), (x, y), 2)

        # 플레이어 표시 (초록 점)
        if self.player:
            x = int(self.player.pos.x * scale_x)
            y = int(self.player.pos.y * scale_y)
            pygame.draw.circle(minimap_surface, (0, 255, 0), (x, y), 4)

        # 테두리
        pygame.draw.rect(minimap_surface, config.WHITE, (0, 0, minimap_size, minimap_size), 2)

        screen.blit(minimap_surface, (minimap_x, minimap_y))

    def _render_overlay(self, screen: pygame.Surface):
        """상태별 오버레이"""
        from ui import draw_pause_and_over_screens

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
        overlay = pygame.Surface(self.screen_size, pygame.SRCALPHA)
        overlay.fill((0, 50, 0, 180))
        screen.blit(overlay, (0, 0))

        victory_text = self.fonts["huge"].render("MISSION COMPLETE!", True, (100, 255, 100))
        victory_rect = victory_text.get_rect(center=(self.screen_size[0] // 2, self.screen_size[1] // 2 - 50))
        screen.blit(victory_text, victory_rect)

        help_text = self.fonts["medium"].render("Press R to Restart, Q to Quit", True, config.WHITE)
        help_rect = help_text.get_rect(center=(self.screen_size[0] // 2, self.screen_size[1] // 2 + 50))
        screen.blit(help_text, help_rect)

    def handle_event(self, event: pygame.event.Event):
        """이벤트 처리"""
        # 공통 이벤트
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
        """게임 실행 중 이벤트"""
        # 오토파일럿 토글 (우클릭)
        if self.handle_autopilot_toggle(event):
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.player and self.player.weapon.can_shoot():
                mouse_pos = pygame.mouse.get_pos()
                target_pos = pygame.math.Vector2(mouse_pos)
                self.player.weapon.fire(
                    self.player.pos, target_pos, self.bullets,
                    self.player.is_piercing, self.player
                )
                self.sound_manager.play_sfx("shoot")

    def _handle_paused_event(self, event: pygame.event.Event):
        """일시정지 이벤트 - 마우스 클릭 지원"""
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

    def _handle_game_over_event(self, event: pygame.event.Event):
        """게임 오버 이벤트 - 마우스 클릭 지원"""
        # 마우스 클릭 처리
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = event.pos

            # Restart 버튼 클릭
            if "restart" in self.menu_button_rects:
                if self.menu_button_rects["restart"].collidepoint(mouse_pos):
                    self._restart_mission()
                    self.sound_manager.play_sfx("button_click")
                    return

            # Quit 버튼 클릭
            if "quit" in self.menu_button_rects:
                if self.menu_button_rects["quit"].collidepoint(mouse_pos):
                    self.request_quit()
                    return

        # 키보드 처리 (기존 유지)
        if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
            self._restart_mission()

    def _handle_victory_event(self, event: pygame.event.Event):
        """승리 이벤트"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                self._restart_mission()
            elif event.key == pygame.K_q:
                self.request_quit()

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


print("INFO: siege_mode.py loaded")
