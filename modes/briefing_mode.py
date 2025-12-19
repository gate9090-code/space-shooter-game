# modes/briefing_mode.py
"""
BriefingMode - 작전실 (통합 미션 시스템)

미션 유형:
- 메인 스토리: StoryMode (필수 진행)
- 사이드 미션: WaveMode/SiegeMode (선택, 보상 획득)
- 훈련장: 무한 웨이브 (자유 전투)
"""

import pygame
import math
import json
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass

import config
from modes.base_mode import GameMode, ModeConfig
from mode_configs.config_missions import (
    MissionType, MissionCategory, MissionReward,
    get_all_missions, get_mission, get_available_missions,
    get_next_main_mission, get_unlocked_side_missions, get_current_act,
    MAIN_MISSIONS, SIDE_MISSIONS, TRAINING_MISSION
)
from ui_components import UILayoutManager, TabData, TabState, UnifiedParticleSystem


@dataclass
class MissionCard:
    """미션 카드"""
    mission_id: str
    rect: pygame.Rect
    is_available: bool
    is_completed: bool
    hover_progress: float = 0.0


class BriefingMode(GameMode):
    """
    작전실 모드 - 통합 미션 시스템

    특징:
    - 메인 미션 (스토리 진행)
    - 사이드 미션 (웨이브/시즈)
    - 훈련장 (무한 웨이브)
    - 미션 완료 시 BaseHub 귀환
    """

    def get_config(self) -> ModeConfig:
        return ModeConfig(
            mode_name="briefing",
            perspective_enabled=False,
            background_type="static",
            parallax_enabled=False,
            meteor_enabled=False,
            show_wave_ui=False,
            show_skill_indicators=False,
            wave_system_enabled=False,
            spawn_system_enabled=False,
            asset_prefix="briefing",
        )

    def init(self):
        """작전실 모드 초기화"""
        config.GAME_MODE = "briefing"

        # UI 매니저 초기화
        self.ui_manager = UILayoutManager(self.screen_size, self.fonts)

        # 진행 상황 로드
        self.completed_missions = self.engine.shared_state.get('completed_missions', [])
        self.current_act = get_current_act(self.completed_missions)

        # UI 상태
        self.selected_tab = "main"  # main, side, training
        self.selected_mission: Optional[str] = None
        self.hovered_mission: Optional[str] = None

        # 배경 및 파티클
        self.background = self._create_background()
        self.particle_system = UnifiedParticleSystem(self.screen_size, 45, "briefing")

        # 애니메이션 상태
        self.animation_time = 0.0
        self.pulse_phase = 0.0

        # 탭 데이터 (메인 미션 / 사이드 미션 / 훈련장)
        self.tabs = [
            TabData(id="main", name="MAIN MISSION", icon="★", color=(80, 160, 255)),
            TabData(id="side", name="SIDE MISSION", icon="○", color=(80, 200, 140)),
            TabData(id="training", name="TRAINING", icon="◇", color=(180, 140, 220)),
        ]
        self.tab_states: Dict[str, TabState] = {tab.id: TabState() for tab in self.tabs}
        self.tab_rects: Dict[str, pygame.Rect] = {}

        # 미션 카드
        self.mission_cards: List[MissionCard] = []

        # 버튼 상태
        self.launch_rect = None
        self.back_rect = None
        self.launch_hover = False
        self.back_hover = False

        # 현재 미션 자동 선택 (메인 미션)
        self._auto_select_next_mission()

        print("INFO: BriefingMode initialized (Mission System)")

    def _create_background(self) -> pygame.Surface:
        """배경 생성"""
        bg = self.ui_manager.create_gradient_background(
            base_color=(8, 12, 28),
            variation=22
        )

        # 그리드 패턴 (홀로그램 느낌)
        grid_color = (22, 32, 52)
        grid_spacing = 40
        for x in range(0, self.screen_size[0], grid_spacing):
            pygame.draw.line(bg, grid_color, (x, 0), (x, self.screen_size[1]), 1)
        for y in range(0, self.screen_size[1], grid_spacing):
            pygame.draw.line(bg, grid_color, (0, y), (self.screen_size[0], y), 1)

        # 상단 조명 효과
        light_surf = pygame.Surface(self.screen_size, pygame.SRCALPHA)
        for i in range(55):
            alpha = int(18 * (1 - i / 55))
            pygame.draw.ellipse(light_surf, (75, 115, 195, alpha),
                              (self.screen_size[0] // 2 - 240 - i * 2, -95 - i,
                               480 + i * 4, 190 + i * 2))
        bg.blit(light_surf, (0, 0))

        return bg

    def _auto_select_next_mission(self):
        """다음 메인 미션 자동 선택"""
        next_mission = get_next_main_mission(self.completed_missions)
        if next_mission:
            self.selected_mission = next_mission

    def _get_current_missions(self) -> Dict[str, Dict[str, Any]]:
        """현재 탭의 미션 목록 반환"""
        if self.selected_tab == "main":
            # 메인 미션: 현재 + 다음 몇 개
            available = get_available_missions(self.completed_missions)
            main_missions = {}
            for m_id, m_data in available.items():
                if m_data.get("category") == MissionCategory.MAIN:
                    main_missions[m_id] = m_data
            return main_missions

        elif self.selected_tab == "side":
            # 사이드 미션
            return get_unlocked_side_missions(self.completed_missions)

        elif self.selected_tab == "training":
            # 훈련장
            return TRAINING_MISSION

        return {}

    def update(self, dt: float, current_time: float):
        """업데이트"""
        self.animation_time += dt
        self.pulse_phase = (math.sin(self.animation_time * 3) + 1) / 2

        # 파티클 업데이트
        self.particle_system.update(dt)

        # 마우스 위치
        mouse_pos = pygame.mouse.get_pos()
        self.hovered_mission = None

        # 탭 호버 업데이트
        for tab_id, rect in self.tab_rects.items():
            state = self.tab_states[tab_id]
            if rect and rect.collidepoint(mouse_pos):
                state.hover_progress = min(1.0, state.hover_progress + dt * 6)
            else:
                state.hover_progress = max(0.0, state.hover_progress - dt * 4)

        # 미션 카드 호버 업데이트
        for card in self.mission_cards:
            if card.rect.collidepoint(mouse_pos):
                self.hovered_mission = card.mission_id
                card.hover_progress = min(1.0, card.hover_progress + dt * 6)
            else:
                card.hover_progress = max(0.0, card.hover_progress - dt * 4)

        # 버튼 호버
        if self.launch_rect:
            self.launch_hover = self.launch_rect.collidepoint(mouse_pos)
        if self.back_rect:
            self.back_hover = self.back_rect.collidepoint(mouse_pos)

    def render(self, screen: pygame.Surface):
        """렌더링"""
        # 배경
        screen.blit(self.background, (0, 0))

        # 파티클
        self.particle_system.render(screen)

        # 타이틀
        tab_color = self._get_tab_color()
        glow_intensity = (math.sin(self.animation_time * 2) + 1) / 2
        self.ui_manager.render_title(screen, "MISSION BRIEFING", tab_color, glow_intensity)

        # 탭
        self.tab_rects = self.ui_manager.render_horizontal_tabs(
            screen, self.tabs, self.selected_tab, self.tab_states, tab_width=180
        )

        # 미션 목록
        self._render_mission_list(screen)

        # 미션 상세 (선택된 경우)
        if self.selected_mission:
            self._render_mission_detail(screen)

        # 버튼
        self._render_buttons(screen)

        # 키보드 힌트
        self.ui_manager.render_keyboard_hints(screen, "TAB Switch  |  Click Mission  |  Enter Launch  |  ESC Back")

    def _get_tab_color(self) -> Tuple[int, int, int]:
        """현재 탭 색상"""
        for tab in self.tabs:
            if tab.id == self.selected_tab:
                return tab.color
        return (80, 160, 255)

    def _render_mission_list(self, screen: pygame.Surface):
        """미션 목록 렌더링"""
        missions = self._get_current_missions()
        tab_color = self._get_tab_color()

        # 콘텐츠 패널
        panel_rect = self.ui_manager.render_content_panel(
            screen, self._get_tab_description(), tab_color
        )

        # 미션 카드 영역
        self.mission_cards.clear()
        card_start_y = panel_rect.y + 55
        card_height = 80
        card_spacing = 12
        card_width = panel_rect.width - 40

        for i, (mission_id, mission_data) in enumerate(missions.items()):
            card_y = card_start_y + i * (card_height + card_spacing)

            # 패널 범위 확인
            if card_y + card_height > panel_rect.bottom - 20:
                break

            card_rect = pygame.Rect(
                panel_rect.x + 20,
                card_y,
                card_width,
                card_height
            )

            is_available = self._is_mission_available(mission_id)
            is_completed = mission_id in self.completed_missions
            is_selected = mission_id == self.selected_mission

            # 카드 객체 추가
            self.mission_cards.append(MissionCard(
                mission_id=mission_id,
                rect=card_rect,
                is_available=is_available,
                is_completed=is_completed,
            ))

            # 호버 진행도 가져오기
            hover_progress = 0.0
            for card in self.mission_cards:
                if card.mission_id == mission_id:
                    hover_progress = card.hover_progress
                    break

            # 카드 렌더링
            self._render_mission_card(
                screen, card_rect, mission_id, mission_data,
                is_available, is_completed, is_selected, hover_progress
            )

    def _render_mission_card(
        self, screen: pygame.Surface, rect: pygame.Rect,
        mission_id: str, mission_data: Dict,
        is_available: bool, is_completed: bool, is_selected: bool,
        hover_progress: float
    ):
        """미션 카드 렌더링"""
        # 확장 효과
        expand = int(hover_progress * 4)
        draw_rect = rect.inflate(expand, expand // 2)

        # 카드 배경
        card_surf = pygame.Surface((draw_rect.width, draw_rect.height), pygame.SRCALPHA)

        mission_type = mission_data.get("type", MissionType.STORY)

        # 타입별 색상
        if mission_type == MissionType.STORY:
            type_color = (80, 160, 255)  # 파랑
        elif mission_type == MissionType.WAVE:
            type_color = (80, 200, 140)  # 녹색
        elif mission_type == MissionType.SIEGE:
            type_color = (255, 140, 80)  # 주황
        else:
            type_color = (180, 140, 220)  # 보라

        if not is_available:
            card_surf.fill((40, 40, 50, 180))
            border_color = (70, 70, 80)
        elif is_selected:
            card_surf.fill((type_color[0] // 3, type_color[1] // 3, type_color[2] // 3, 220))
            border_color = type_color
        elif hover_progress > 0:
            alpha = int(160 + 55 * hover_progress)
            card_surf.fill((35, 45, 65, alpha))
            border_color = (95, 115, 155)
        else:
            card_surf.fill((25, 35, 55, 200))
            border_color = (60, 75, 100)

        screen.blit(card_surf, draw_rect.topleft)
        pygame.draw.rect(screen, border_color, draw_rect, 2, border_radius=10)

        # 왼쪽: 미션 타입 아이콘
        icon_x = draw_rect.x + 15
        icon_y = draw_rect.centery

        category = mission_data.get("category", MissionCategory.MAIN)
        if category == MissionCategory.MAIN:
            icon_text = "★"
            icon_color = (255, 220, 80)
        elif category == MissionCategory.SIDE:
            icon_text = "○"
            icon_color = type_color
        else:
            icon_text = "◇"
            icon_color = (180, 140, 220)

        icon_font = pygame.font.Font(None, 32)
        icon_surf = icon_font.render(icon_text, True, icon_color if is_available else (80, 80, 90))
        icon_rect = icon_surf.get_rect(center=(icon_x + 12, icon_y))
        screen.blit(icon_surf, icon_rect)

        # 미션 이름
        text_x = draw_rect.x + 50
        name_color = (255, 255, 255) if is_available else (100, 100, 110)
        name = mission_data.get("name", mission_id)
        name_text = self.fonts["medium"].render(name, True, name_color)
        screen.blit(name_text, (text_x, draw_rect.y + 15))

        # 미션 설명
        desc_color = (160, 170, 190) if is_available else (80, 85, 95)
        desc = mission_data.get("description", "")[:50]
        if len(mission_data.get("description", "")) > 50:
            desc += "..."
        desc_text = self.fonts["small"].render(desc, True, desc_color)
        screen.blit(desc_text, (text_x, draw_rect.y + 42))

        # 오른쪽: 상태/보상
        right_x = draw_rect.right - 100

        if is_completed:
            # 완료 뱃지
            badge_surf = pygame.Surface((70, 24), pygame.SRCALPHA)
            badge_surf.fill((40, 140, 80, 200))
            screen.blit(badge_surf, (right_x, draw_rect.centery - 12))
            pygame.draw.rect(screen, (80, 200, 120), (right_x, draw_rect.centery - 12, 70, 24), 1, border_radius=4)
            clear_text = self.fonts["small"].render("CLEAR", True, (140, 255, 180))
            screen.blit(clear_text, clear_text.get_rect(center=(right_x + 35, draw_rect.centery)))
        elif is_available:
            # 보상 표시
            rewards = mission_data.get("rewards")
            if rewards and hasattr(rewards, 'credits') and rewards.credits > 0:
                reward_text = self.fonts["small"].render(f"+{rewards.credits}", True, (255, 220, 100))
                screen.blit(reward_text, (right_x + 10, draw_rect.centery - 8))
        else:
            # 잠금
            lock_text = self.fonts["small"].render("LOCKED", True, (100, 100, 110))
            screen.blit(lock_text, (right_x + 5, draw_rect.centery - 8))

    def _render_mission_detail(self, screen: pygame.Surface):
        """선택된 미션 상세 정보"""
        mission_data = get_mission(self.selected_mission)
        if not mission_data:
            return

        # 화면 하단에 상세 정보 패널
        detail_rect = pygame.Rect(
            self.screen_size[0] // 2 - 300,
            self.screen_size[1] - 140,
            600,
            80
        )

        # 패널 배경
        panel_surf = pygame.Surface((detail_rect.width, detail_rect.height), pygame.SRCALPHA)
        panel_surf.fill((20, 30, 50, 220))
        screen.blit(panel_surf, detail_rect.topleft)
        pygame.draw.rect(screen, (60, 80, 120), detail_rect, 1, border_radius=8)

        # 미션 정보
        name = mission_data.get("name", self.selected_mission)
        desc = mission_data.get("description", "")

        name_text = self.fonts["medium"].render(name, True, (255, 255, 255))
        screen.blit(name_text, (detail_rect.x + 20, detail_rect.y + 15))

        desc_text = self.fonts["small"].render(desc, True, (180, 190, 210))
        screen.blit(desc_text, (detail_rect.x + 20, detail_rect.y + 45))

        # 보상 정보
        rewards = mission_data.get("rewards")
        if rewards:
            reward_parts = []
            if hasattr(rewards, 'credits') and rewards.credits > 0:
                reward_parts.append(f"Credits: {rewards.credits}")
            if hasattr(rewards, 'exp') and rewards.exp > 0:
                reward_parts.append(f"EXP: {rewards.exp}")
            if hasattr(rewards, 'unlock_weapon') and rewards.unlock_weapon:
                reward_parts.append(f"Unlock: {rewards.unlock_weapon}")

            if reward_parts:
                reward_str = " | ".join(reward_parts)
                reward_text = self.fonts["small"].render(f"Rewards: {reward_str}", True, (255, 220, 100))
                screen.blit(reward_text, (detail_rect.right - reward_text.get_width() - 20, detail_rect.y + 30))

    def _get_tab_description(self) -> str:
        """탭별 설명"""
        if self.selected_tab == "main":
            return f"Act {self.current_act} - Main Story Missions"
        elif self.selected_tab == "side":
            count = len(get_unlocked_side_missions(self.completed_missions))
            return f"Available Side Missions: {count}"
        else:
            return "Free Combat - Unlimited Waves"

    def _is_mission_available(self, mission_id: str) -> bool:
        """미션 진행 가능 여부"""
        mission = get_mission(mission_id)
        if not mission:
            return False

        prerequisite = mission.get("prerequisite")
        if prerequisite is None:
            return True

        return prerequisite in self.completed_missions

    def _render_buttons(self, screen: pygame.Surface):
        """버튼 렌더링"""
        can_launch = self.selected_mission is not None and self._is_mission_available(self.selected_mission)

        # 출격 버튼
        self.launch_rect = self.ui_manager.render_action_button(
            screen, "LAUNCH", self.launch_hover, can_launch, danger=True
        )

        # 뒤로가기 버튼
        self.back_rect = self.ui_manager.render_back_button(screen, self.back_hover)

    def handle_event(self, event: pygame.event.Event):
        """이벤트 처리"""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = event.pos

            # 탭 클릭
            for tab_id, rect in self.tab_rects.items():
                if rect.collidepoint(mouse_pos):
                    self.selected_tab = tab_id
                    self.selected_mission = None
                    if tab_id == "main":
                        self._auto_select_next_mission()
                    if hasattr(self, 'sound_manager') and self.sound_manager:
                        self.sound_manager.play_sfx("click")
                    return

            # 미션 카드 클릭
            for card in self.mission_cards:
                if card.rect.collidepoint(mouse_pos) and card.is_available:
                    self.selected_mission = card.mission_id
                    if hasattr(self, 'sound_manager') and self.sound_manager:
                        self.sound_manager.play_sfx("click")
                    return

            # 출격 버튼
            if self.launch_rect and self.launch_rect.collidepoint(mouse_pos):
                if self.selected_mission and self._is_mission_available(self.selected_mission):
                    self._on_launch()
                return

            # 뒤로가기 버튼
            if self.back_rect and self.back_rect.collidepoint(mouse_pos):
                self._on_back()
                return

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._on_back()
                return

            if event.key == pygame.K_RETURN:
                if self.selected_mission and self._is_mission_available(self.selected_mission):
                    self._on_launch()
                return

            if event.key == pygame.K_TAB:
                # 탭 순환
                tab_ids = [t.id for t in self.tabs]
                current_idx = tab_ids.index(self.selected_tab) if self.selected_tab in tab_ids else 0
                next_idx = (current_idx + 1) % len(tab_ids)
                self.selected_tab = tab_ids[next_idx]
                self.selected_mission = None
                if self.selected_tab == "main":
                    self._auto_select_next_mission()

    def _on_launch(self):
        """미션 출격"""
        if not self.selected_mission:
            return

        mission_data = get_mission(self.selected_mission)
        if not mission_data:
            return

        # 미션 정보 저장
        self.engine.shared_state['current_mission'] = self.selected_mission
        self.engine.shared_state['mission_data'] = mission_data
        self.engine.shared_state['from_briefing'] = True

        print(f"INFO: Launching mission: {self.selected_mission}")

        if hasattr(self, 'sound_manager') and self.sound_manager:
            self.sound_manager.play_sfx("level_up")

        # 미션 타입에 따라 모드 전환
        mission_type = mission_data.get("type", MissionType.STORY)

        if mission_type == MissionType.STORY:
            # 스토리 모드
            waves = mission_data.get("waves", [1])
            self.engine.shared_state['story_set'] = mission_data.get("act", 1)
            self.engine.shared_state['start_wave'] = waves[0] if waves else 1

            from modes.story_mode import StoryMode
            self.request_switch_mode(StoryMode)

        elif mission_type == MissionType.WAVE:
            # 웨이브 모드
            wave_count = mission_data.get("wave_count", 5)
            self.engine.shared_state['target_waves'] = wave_count
            self.engine.shared_state['is_side_mission'] = True

            from modes.wave_mode import WaveMode
            self.request_switch_mode(WaveMode)

        elif mission_type == MissionType.SIEGE:
            # 시즈 모드
            self.engine.shared_state['is_side_mission'] = True

            from modes.siege_mode import SiegeMode
            self.request_switch_mode(SiegeMode)

        elif mission_type == MissionType.TRAINING:
            # 훈련장 (무한 웨이브)
            self.engine.shared_state['is_training'] = True
            self.engine.shared_state['target_waves'] = -1  # 무한

            from modes.wave_mode import WaveMode
            self.request_switch_mode(WaveMode)

    def _on_back(self):
        """뒤로가기 - BaseHub로"""
        self.request_pop_mode()

    def on_enter(self):
        super().on_enter()
        # 진행 상황 다시 로드
        self.completed_missions = self.engine.shared_state.get('completed_missions', [])
        self.current_act = get_current_act(self.completed_missions)
        self._auto_select_next_mission()

    def on_exit(self):
        super().on_exit()


print("INFO: briefing_mode.py loaded (Mission System)")
