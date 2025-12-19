# modes/hangar_mode.py
"""
HangarMode - 격납고 모드 (Unified Modern UI)
함선 선택 및 장착 화면

함선 타입:
- Fighter: 균형 잡힌 기본 함선
- Interceptor: 빠른 속도, 약한 방어
- Bomber: 강한 화력, 느린 속도
- Tank: 강한 방어, 느린 화력
"""

import pygame
import math
from typing import Dict, Optional, List
from dataclasses import dataclass

import config
from modes.base_mode import GameMode, ModeConfig
from ui_components import UILayoutManager, TabData, TabState, UnifiedParticleSystem


# config.py에서 함선 정의 가져오기
SHIP_TYPES = config.SHIP_TYPES


class HangarMode(GameMode):
    """
    격납고 모드 - Unified Modern UI Design

    특징:
    - 통일된 UI 컴포넌트 사용
    - 상단 가로 탭 (함선 선택)
    - 중앙 함선 프리뷰 + 스탯 패널 (600px)
    - WCAG 대비율 준수 색상
    """

    def get_config(self) -> ModeConfig:
        return ModeConfig(
            mode_name="hangar",
            perspective_enabled=False,
            background_type="static",
            parallax_enabled=False,
            meteor_enabled=False,
            show_wave_ui=False,
            show_skill_indicators=False,
            wave_system_enabled=False,
            spawn_system_enabled=False,
            asset_prefix="hangar",
        )

    def init(self):
        """격납고 모드 초기화"""
        config.GAME_MODE = "hangar"

        # UI 매니저 초기화
        self.ui_manager = UILayoutManager(self.screen_size, self.fonts)

        # 플레이어 데이터
        self.owned_ships = self.engine.shared_state.get('owned_ships', ['FIGHTER'])
        self.selected_ship = self.engine.shared_state.get('selected_ship', 'FIGHTER')
        self.credits = self.engine.shared_state.get('global_score', 0)

        # UI 상태
        self.current_ship = self.selected_ship
        self.preview_rotation = 0.0

        # 배경 및 파티클
        self.background = self._create_background()
        self.particle_system = UnifiedParticleSystem(self.screen_size, 40, "hangar")

        # 애니메이션 상태
        self.animation_time = 0.0
        self.purchase_flash = 0.0

        # 함선 탭 데이터 생성 (config.SHIP_TYPES 기반)
        self.tabs = []
        for ship_id, ship in SHIP_TYPES.items():
            # 색상 매핑
            color = self._get_ship_color(ship_id)
            self.tabs.append(TabData(
                id=ship_id,
                name=ship.get("name", ship_id),
                icon=ship.get("icon", "🚀"),
                color=color
            ))

        self.tab_states: Dict[str, TabState] = {tab.id: TabState() for tab in self.tabs}
        self.tab_rects: Dict[str, pygame.Rect] = {}

        # 버튼 상태
        self.confirm_rect = None
        self.back_rect = None
        self.confirm_hover = False
        self.back_hover = False

        print("INFO: HangarMode initialized (Unified UI)")

    def _get_ship_color(self, ship_id: str):
        """함선 ID에 따른 색상 반환"""
        color_map = {
            "FIGHTER": config.CATEGORY_COLORS["STATS"],
            "INTERCEPTOR": config.CATEGORY_COLORS["UTILITY"],
            "BOMBER": config.CATEGORY_COLORS["ATTACK"],
            "STEALTH": config.CATEGORY_COLORS["SPECIAL"],
            "TITAN": config.CATEGORY_COLORS["DEFENSE"],
        }
        return color_map.get(ship_id, config.CATEGORY_COLORS["STATS"])

    def _create_background(self) -> pygame.Surface:
        """배경 생성"""
        bg = self.ui_manager.create_gradient_background(
            base_color=(10, 15, 28),
            variation=20
        )

        # 격납고 기둥 패턴
        pillar_color = (22, 28, 42)
        for i in range(5):
            x = 100 + i * 350
            pygame.draw.rect(bg, pillar_color, (x, 0, 30, self.screen_size[1]))
            pygame.draw.rect(bg, (28, 35, 52), (x + 5, 0, 20, self.screen_size[1]))

        # 바닥 조명
        light_surf = pygame.Surface(self.screen_size, pygame.SRCALPHA)
        for i in range(50):
            alpha = int(15 * (1 - i / 50))
            pygame.draw.ellipse(light_surf, (80, 130, 200, alpha),
                              (self.screen_size[0] // 2 - 200 - i * 3,
                               self.screen_size[1] - 100 - i,
                               400 + i * 6, 80 + i))
        bg.blit(light_surf, (0, 0))

        return bg

    def update(self, dt: float, current_time: float):
        """업데이트"""
        self.animation_time += dt
        self.preview_rotation += dt * 15
        self.purchase_flash = max(0, self.purchase_flash - dt * 3)

        # 파티클 업데이트
        self.particle_system.update(dt)

        # 마우스 위치
        mouse_pos = pygame.mouse.get_pos()

        # 탭 호버 업데이트
        for tab_id, rect in self.tab_rects.items():
            state = self.tab_states[tab_id]
            if rect and rect.collidepoint(mouse_pos):
                state.hover_progress = min(1.0, state.hover_progress + dt * 6)
            else:
                state.hover_progress = max(0.0, state.hover_progress - dt * 4)

        # 버튼 호버
        if self.confirm_rect:
            self.confirm_hover = self.confirm_rect.collidepoint(mouse_pos)
        if self.back_rect:
            self.back_hover = self.back_rect.collidepoint(mouse_pos)

    def render(self, screen: pygame.Surface):
        """렌더링"""
        # 배경
        screen.blit(self.background, (0, 0))

        # 파티클
        self.particle_system.render(screen)

        # 타이틀
        ship_color = self._get_ship_color(self.current_ship)
        glow_intensity = (math.sin(self.animation_time * 2.5) + 1) / 2
        self.ui_manager.render_title(screen, "H A N G A R", ship_color, glow_intensity)

        # 크레딧 표시
        self.ui_manager.render_credit_box(screen, self.credits, self.purchase_flash)

        # 함선 탭 (탭 너비는 함선 수에 따라 조정)
        tab_width = min(130, (self.screen_size[0] - 100) // max(1, len(self.tabs)))
        self.tab_rects = self.ui_manager.render_horizontal_tabs(
            screen, self.tabs, self.current_ship, self.tab_states, tab_width=tab_width
        )

        # 함선 상세 정보
        self._render_ship_details(screen)

        # 버튼
        self._render_buttons(screen)

        # 키보드 힌트
        hint_keys = "1-" + str(len(self.tabs))
        self.ui_manager.render_keyboard_hints(screen, f"{hint_keys} Ships  |  Enter Confirm  |  ESC Back")

    def _render_ship_details(self, screen: pygame.Surface):
        """함선 상세 정보 렌더링"""
        if self.current_ship not in SHIP_TYPES:
            return

        ship_data = SHIP_TYPES[self.current_ship]
        ship_color = self._get_ship_color(self.current_ship)
        is_owned = self.current_ship in self.owned_ships
        is_selected = self.current_ship == self.selected_ship

        # 콘텐츠 패널
        panel_rect = self.ui_manager.render_content_panel(
            screen, ship_data.get("name", self.current_ship), ship_color
        )

        # 함선 프리뷰 영역 (상단)
        preview_y = panel_rect.y + 45
        preview_height = 160

        # 프리뷰 배경
        preview_surf = pygame.Surface((panel_rect.width - 30, preview_height), pygame.SRCALPHA)
        preview_surf.fill((*config.BG_LEVELS["PANEL"], 150))
        screen.blit(preview_surf, (panel_rect.x + 15, preview_y))

        # 함선 아이콘 (회전)
        center_x = panel_rect.x + panel_rect.width // 2
        center_y = preview_y + preview_height // 2

        # 회전하는 원 배경
        radius = 50
        for i in range(8):
            angle = self.preview_rotation * math.pi / 180 + (i * math.pi / 4)
            dot_x = center_x + radius * math.cos(angle)
            dot_y = center_y + radius * math.sin(angle)
            alpha = int(100 + 50 * math.sin(angle + self.animation_time * 2))
            dot_surf = pygame.Surface((8, 8), pygame.SRCALPHA)
            pygame.draw.circle(dot_surf, (*ship_color, alpha), (4, 4), 4)
            screen.blit(dot_surf, (dot_x - 4, dot_y - 4))

        # 함선 아이콘
        icon_font = pygame.font.Font(None, 80)
        if is_owned:
            icon_color = ship_color
        else:
            icon_color = config.LOCKED_COLORS["ICON"]

        icon_text = icon_font.render(ship_data.get("icon", "🚀"), True, icon_color)
        screen.blit(icon_text, icon_text.get_rect(center=(center_x, center_y)))

        # 선택/보유 뱃지
        cost = ship_data.get("cost", 0)
        if is_selected:
            badge_text = "EQUIPPED"
            badge_color = config.STATE_COLORS["SUCCESS"]
            badge_bg = config.STATE_COLORS["SUCCESS_DIM"]
        elif is_owned:
            badge_text = "OWNED"
            badge_color = config.STATE_COLORS["INFO"]
            badge_bg = config.STATE_COLORS["INFO_DIM"]
        else:
            badge_text = f"${cost:,}"
            badge_color = config.STATE_COLORS["GOLD"]
            badge_bg = config.STATE_COLORS["GOLD_DIM"]

        badge_surf = pygame.Surface((90, 26), pygame.SRCALPHA)
        badge_surf.fill((*badge_bg, 200))
        screen.blit(badge_surf, (center_x - 45, preview_y + preview_height - 35))
        pygame.draw.rect(screen, badge_color,
                        (center_x - 45, preview_y + preview_height - 35, 90, 26), 1, border_radius=5)
        badge_label = self.fonts["small"].render(badge_text, True, badge_color)
        screen.blit(badge_label, badge_label.get_rect(center=(center_x, preview_y + preview_height - 22)))

        # 설명
        desc_y = preview_y + preview_height + 12
        desc_color = config.TEXT_LEVELS["SECONDARY"] if is_owned else config.LOCKED_COLORS["TEXT"]
        desc = ship_data.get("description", "")
        desc_text = self.fonts["medium"].render(desc, True, desc_color)
        screen.blit(desc_text, desc_text.get_rect(center=(center_x, desc_y)))

        # 스탯 바 영역
        stats_y = desc_y + 30
        stats = ship_data.get("stats", {"hp": 100, "speed": 300, "damage": 25, "fire_rate": 1.0})
        stat_names = [
            ("HP", stats.get("hp", 100), 250),
            ("SPEED", stats.get("speed", 300), 500),
            ("DMG", stats.get("damage", 25), 60),
            ("RATE", stats.get("fire_rate", 1.0), 2.0)
        ]

        bar_width = panel_rect.width - 80
        bar_height = 18
        bar_x = panel_rect.x + 40

        for i, (name, value, max_val) in enumerate(stat_names):
            y = stats_y + i * 32

            # 스탯 이름
            name_text = self.fonts["small"].render(name, True, config.TEXT_LEVELS["TERTIARY"])
            screen.blit(name_text, (bar_x, y))

            # 바 배경
            pygame.draw.rect(screen, config.BG_LEVELS["PANEL"],
                           (bar_x + 55, y + 2, bar_width - 55, bar_height), border_radius=4)

            # 바 채우기
            fill_ratio = min(1.0, value / max_val)
            fill_width = int((bar_width - 55) * fill_ratio)
            fill_color = ship_color if is_owned else config.LOCKED_COLORS["BORDER"]
            pygame.draw.rect(screen, fill_color,
                           (bar_x + 55, y + 2, fill_width, bar_height), border_radius=4)

            # 값 표시
            value_str = f"{int(value)}" if name != "RATE" else f"{value:.1f}x"
            value_text = self.fonts["small"].render(value_str, True, config.TEXT_LEVELS["SECONDARY"])
            screen.blit(value_text, (bar_x + bar_width + 8, y))

        # 어빌리티 정보
        ability_y = stats_y + len(stat_names) * 32 + 12

        ability_surf = pygame.Surface((panel_rect.width - 30, 48), pygame.SRCALPHA)
        ability_surf.fill((*config.BG_LEVELS["CARD"], 180))
        screen.blit(ability_surf, (panel_rect.x + 15, ability_y))
        pygame.draw.rect(screen, ship_color,
                        (panel_rect.x + 15, ability_y, panel_rect.width - 30, 48), 1, border_radius=8)

        # 어빌리티 이름
        ability_color = ship_color if is_owned else config.LOCKED_COLORS["TEXT"]
        ability_name = ship_data.get("ability", {}).get("name", "Ability")
        ability_name_text = self.fonts["medium"].render(f"[E] {ability_name}", True, ability_color)
        screen.blit(ability_name_text, (panel_rect.x + 28, ability_y + 6))

        # 어빌리티 설명
        ability_desc = ship_data.get("ability", {}).get("description", "")
        ability_desc_text = self.fonts["small"].render(ability_desc, True, config.TEXT_LEVELS["TERTIARY"])
        screen.blit(ability_desc_text, (panel_rect.x + 28, ability_y + 28))

    def _render_buttons(self, screen: pygame.Surface):
        """버튼 렌더링"""
        is_owned = self.current_ship in self.owned_ships
        is_selected = self.current_ship == self.selected_ship
        cost = SHIP_TYPES.get(self.current_ship, {}).get("cost", 0)
        can_afford = self.credits >= cost

        # 확인/구매 버튼 텍스트 및 활성화 상태
        if is_selected:
            btn_text = "EQUIPPED"
            btn_enabled = False
        elif is_owned:
            btn_text = "EQUIP"
            btn_enabled = True
        elif can_afford:
            btn_text = "BUY"
            btn_enabled = True
        else:
            btn_text = "BUY"
            btn_enabled = False

        # 액션 버튼 (좌측 하단)
        self.confirm_rect = self.ui_manager.render_action_button(
            screen, btn_text, self.confirm_hover, btn_enabled
        )

        # 뒤로가기 버튼 (우측 하단)
        self.back_rect = self.ui_manager.render_back_button(screen, self.back_hover)

    def handle_event(self, event: pygame.event.Event):
        """이벤트 처리"""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = event.pos

            # 탭 클릭
            for tab_id, rect in self.tab_rects.items():
                if rect.collidepoint(mouse_pos):
                    self.current_ship = tab_id
                    self.sound_manager.play_sfx("click")
                    return

            # 확인/구매 버튼
            if self.confirm_rect and self.confirm_rect.collidepoint(mouse_pos):
                self._on_confirm()
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
                self._on_confirm()
                return

            # 숫자 키로 함선 선택
            ship_list = list(SHIP_TYPES.keys())
            key_map = {pygame.K_1: 0, pygame.K_2: 1, pygame.K_3: 2,
                      pygame.K_4: 3, pygame.K_5: 4, pygame.K_6: 5}
            if event.key in key_map:
                idx = key_map[event.key]
                if idx < len(ship_list):
                    self.current_ship = ship_list[idx]
                    self.sound_manager.play_sfx("click")

    def _on_confirm(self):
        """확인/구매"""
        is_owned = self.current_ship in self.owned_ships
        is_selected = self.current_ship == self.selected_ship

        if is_selected:
            return

        if is_owned:
            # 장착
            self.selected_ship = self.current_ship
            self.engine.shared_state['selected_ship'] = self.selected_ship
            self.sound_manager.play_sfx("level_up")
            print(f"INFO: Equipped ship: {self.current_ship}")
        else:
            # 구매
            cost = SHIP_TYPES.get(self.current_ship, {}).get("cost", 0)
            if self.credits >= cost:
                self.credits -= cost
                self.owned_ships.append(self.current_ship)

                self.engine.shared_state['global_score'] = self.credits
                self.engine.shared_state['owned_ships'] = self.owned_ships

                self.purchase_flash = 1.0
                self.sound_manager.play_sfx("level_up")
                print(f"INFO: Purchased ship: {self.current_ship}")
            else:
                self.sound_manager.play_sfx("error")

    def _on_back(self):
        """뒤로가기"""
        self.engine.shared_state['global_score'] = self.credits
        self.engine.shared_state['owned_ships'] = self.owned_ships
        self.engine.shared_state['selected_ship'] = self.selected_ship
        self.engine.save_shared_state()
        self.request_pop_mode()

    def on_enter(self):
        super().on_enter()

    def on_exit(self):
        self.engine.shared_state['global_score'] = self.credits
        self.engine.shared_state['owned_ships'] = self.owned_ships
        self.engine.shared_state['selected_ship'] = self.selected_ship
        self.engine.save_shared_state()
        super().on_exit()


print("INFO: hangar_mode.py loaded (Unified Modern UI)")
