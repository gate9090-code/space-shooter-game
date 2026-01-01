# ui_components.py
"""
통일된 UI 컴포넌트 시스템
모든 모드에서 공유하는 UI 렌더링 함수들

특징:
- config.py의 UI_LAYOUT, UI_COLORS 사용
- WCAG 대비율 준수
- 일관된 레이아웃
"""

import pygame
import math
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass

import config
from ui_render import render_text_with_emoji


# =============================================================================
# 데이터 클래스
# =============================================================================

@dataclass
class TabData:
    """탭 데이터"""
    id: str
    name: str
    icon: str = ""
    color: Tuple[int, int, int] = (100, 150, 200)
    enabled: bool = True


@dataclass
class TabState:
    """탭 상태"""
    hover_progress: float = 0.0
    rect: Optional[pygame.Rect] = None


# =============================================================================
# UI 레이아웃 매니저
# =============================================================================

class UILayoutManager:
    """
    통일된 UI 레이아웃 관리자
    모든 모드에서 동일한 레이아웃을 보장
    """

    def __init__(self, screen_size: Tuple[int, int], fonts: Dict[str, pygame.font.Font]):
        self.screen_size = screen_size
        self.fonts = fonts
        self.layout = config.UI_LAYOUT

    # =========================================================================
    # 영역 계산
    # =========================================================================

    def get_content_panel_rect(self) -> pygame.Rect:
        """중앙 콘텐츠 패널 영역"""
        w = self.layout["CONTENT_PANEL_WIDTH"]
        h = int(self.screen_size[1] * self.layout["CONTENT_PANEL_HEIGHT_RATIO"])
        x = (self.screen_size[0] - w) // 2
        y = self.layout["CONTENT_START_Y"]
        return pygame.Rect(x, y, w, h)

    def get_tab_area(self, num_tabs: int, tab_width: int = 95) -> Tuple[int, int, int]:
        """탭 영역 계산 - (start_x, y, total_width)"""
        spacing = self.layout["TAB_SPACING"]
        total_width = tab_width * num_tabs + spacing * (num_tabs - 1)
        start_x = (self.screen_size[0] - total_width) // 2
        y = self.layout["TAB_Y"]
        return start_x, y, total_width

    # =========================================================================
    # 배경 생성
    # =========================================================================

    def create_gradient_background(
        self,
        base_color: Tuple[int, int, int] = None,
        variation: int = 20
    ) -> pygame.Surface:
        """그라데이션 배경 생성"""
        if base_color is None:
            base_color = config.BG_LEVELS["SCREEN"]

        bg = pygame.Surface(self.screen_size)

        for y in range(self.screen_size[1]):
            ratio = y / self.screen_size[1]
            r = min(255, int(base_color[0] + variation * ratio))
            g = min(255, int(base_color[1] + variation * ratio))
            b = min(255, int(base_color[2] + variation * ratio))
            pygame.draw.line(bg, (r, g, b), (0, y), (self.screen_size[0], y))

        return bg

    # =========================================================================
    # 타이틀 렌더링 (프리미엄 디자인)
    # =========================================================================

    def render_title(
        self,
        screen: pygame.Surface,
        title_text: str,
        glow_color: Tuple[int, int, int] = None,
        glow_intensity: float = 0.5
    ):
        """통일된 타이틀 렌더링 - 미니멀 디자인"""
        center_x = self.screen_size[0] // 2
        title_y = self.layout["TITLE_Y"]

        # 타이틀 텍스트 (글로우 제거, 단순 그림자만)
        shadow = self.fonts["large"].render(title_text, True, (0, 0, 0))
        shadow.set_alpha(80)
        screen.blit(shadow, shadow.get_rect(center=(center_x + 1, title_y + 1)))

        # 타이틀 텍스트
        title = self.fonts["large"].render(title_text, True, config.TEXT_LEVELS["PRIMARY"])
        screen.blit(title, title.get_rect(center=(center_x, title_y)))

    # =========================================================================
    # 크레딧 박스 렌더링 (프리미엄 디자인)
    # =========================================================================

    def render_credit_box(
        self,
        screen: pygame.Surface,
        credits: int,
        flash_intensity: float = 0.0
    ):
        """통일된 크레딧 표시 - 미니멀 디자인"""
        box_width = self.layout["CREDIT_BOX_WIDTH"]
        box_height = self.layout["CREDIT_BOX_HEIGHT"]
        margin = self.layout["SCREEN_MARGIN"]

        box_x = self.screen_size[0] - box_width - margin
        box_y = margin

        # 외부 글로우 제거 - 미니멀 디자인

        # 배경 (단색)
        box_surf = pygame.Surface((box_width, box_height), pygame.SRCALPHA)

        if flash_intensity > 0:
            # 구매 성공 시 골드 플래시
            flash_alpha = int(100 * flash_intensity)
            box_surf.fill((*config.STATE_COLORS["GOLD_DIM"], flash_alpha + 160))
        elif flash_intensity < 0:
            # 구매 실패 시 빨간 플래시
            flash_alpha = int(100 * abs(flash_intensity))
            box_surf.fill((*config.STATE_COLORS["DANGER_DIM"], flash_alpha + 160))
        else:
            box_surf.fill((*config.BG_LEVELS["PANEL"], 200))

        screen.blit(box_surf, (box_x, box_y))

        # 테두리
        border_color = config.STATE_COLORS["GOLD"] if flash_intensity != 0 else (95, 105, 125)
        pygame.draw.rect(screen, border_color, (box_x, box_y, box_width, box_height), 2,
                        border_radius=self.layout["TAB_BORDER_RADIUS"])

        # 코인 아이콘 (원형)
        coin_x = box_x + 28
        coin_y = box_y + box_height // 2
        pygame.draw.circle(screen, config.STATE_COLORS["GOLD"], (coin_x, coin_y), 10)
        pygame.draw.circle(screen, (255, 240, 180), (coin_x - 2, coin_y - 2), 4)
        pygame.draw.circle(screen, (0, 0, 0), (coin_x, coin_y), 10, 1)

        # 금액 텍스트
        credit_text = self.fonts["medium"].render(f"{credits:,}", True, config.STATE_COLORS["GOLD"])
        screen.blit(credit_text, (coin_x + 18, box_y + (box_height - credit_text.get_height()) // 2))

    # =========================================================================
    # 가로 탭 렌더링 (프리미엄 디자인)
    # =========================================================================

    def render_horizontal_tabs(
        self,
        screen: pygame.Surface,
        tabs: List[TabData],
        selected_id: str,
        tab_states: Dict[str, TabState],
        tab_width: int = 95
    ) -> Dict[str, pygame.Rect]:
        """
        통일된 가로 탭 렌더링 - 네온 글로우 + 그라데이션 효과

        Returns:
            Dict[str, pygame.Rect]: 탭 ID별 rect (클릭 감지용)
        """
        tab_rects = {}
        num_tabs = len(tabs)
        start_x, start_y, _ = self.get_tab_area(num_tabs, tab_width)

        tab_height = self.layout["TAB_HEIGHT"]
        spacing = self.layout["TAB_SPACING"]
        border_radius = self.layout["TAB_BORDER_RADIUS"]

        for i, tab in enumerate(tabs):
            rect = pygame.Rect(
                start_x + i * (tab_width + spacing),
                start_y,
                tab_width,
                tab_height
            )
            tab_rects[tab.id] = rect

            # 상태 가져오기
            state = tab_states.get(tab.id, TabState())
            is_selected = tab.id == selected_id
            hover = state.hover_progress

            # 크기 고정 (호버 시 확장 제거 - 떨림 방지)
            draw_rect = rect

            # 글로우 효과 제거 - 미니멀 디자인

            # 탭 배경
            tab_surf = pygame.Surface((draw_rect.width, draw_rect.height), pygame.SRCALPHA)

            if not tab.enabled:
                tab_surf.fill(config.INTERACTION_STATES["DISABLED"]["bg"])
                border_color = config.INTERACTION_STATES["DISABLED"]["border"]
                text_color = config.INTERACTION_STATES["DISABLED"]["text"]
            elif is_selected:
                # 선택됨: 단색 배경 (그라데이션 제거)
                tab_surf.fill((*tab.color, 200))
                border_color = tuple(min(255, c + 40) for c in tab.color)
                text_color = config.TEXT_LEVELS["PRIMARY"]
            elif hover > 0:
                # 호버: 색상 변화만 (크기 변화 없음)
                alpha = int(160 + 60 * hover)
                brightness = int(50 + 20 * hover)
                tab_surf.fill((brightness, brightness + 5, brightness + 12, alpha))
                border_color = tab.color
                text_color = config.TEXT_LEVELS["PRIMARY"]
            else:
                # 일반
                tab_surf.fill((*config.BG_LEVELS["CARD"], 180))
                border_color = (65, 72, 88)
                text_color = config.TEXT_LEVELS["SECONDARY"]

            screen.blit(tab_surf, draw_rect.topleft)

            # 하이라이트 제거 - 미니멀 디자인

            # 테두리
            pygame.draw.rect(screen, border_color, draw_rect,
                           2 if is_selected else 1, border_radius=border_radius)

            # 선택 표시 바 (하단) - 글로우 제거
            if is_selected:
                bar_width = draw_rect.width - 16
                pygame.draw.rect(screen, tab.color,
                               (draw_rect.x + 8, draw_rect.bottom - 4, bar_width, 3),
                               border_radius=2)

            # 아이콘 (이모지)
            if tab.icon:
                icon_text = render_text_with_emoji(tab.icon, self.fonts["small"], text_color, "SMALL")
                icon_rect = icon_text.get_rect(center=(draw_rect.centerx, draw_rect.centery))
                screen.blit(icon_text, icon_rect)
            else:
                # 텍스트만
                name_text = self.fonts["small"].render(tab.name[:8], True, text_color)
                screen.blit(name_text, name_text.get_rect(center=draw_rect.center))

        return tab_rects

    # =========================================================================
    # 콘텐츠 패널 렌더링 (프리미엄 디자인)
    # =========================================================================

    def render_content_panel(
        self,
        screen: pygame.Surface,
        header_text: str = "",
        header_color: Tuple[int, int, int] = None
    ) -> pygame.Rect:
        """
        통일된 콘텐츠 패널 배경 렌더링 - 미니멀 디자인

        Returns:
            pygame.Rect: 패널 영역
        """
        panel_rect = self.get_content_panel_rect()

        if header_color is None:
            header_color = config.STATE_COLORS["INFO"]

        # 글로우/그림자 제거 - 미니멀 디자인

        # 단색 배경 (더 어둡게 - 텍스트 가시성 향상)
        panel_surf = pygame.Surface((panel_rect.width, panel_rect.height), pygame.SRCALPHA)
        panel_surf.fill((15, 18, 25, 210))
        screen.blit(panel_surf, panel_rect.topleft)

        # 테두리
        pygame.draw.rect(screen, (55, 62, 78), panel_rect, 1, border_radius=12)

        # 헤더 바 (단일 라인)
        pygame.draw.line(screen, header_color,
                        (panel_rect.x + 2, panel_rect.y),
                        (panel_rect.x + panel_rect.width - 2, panel_rect.y), 2)

        # 헤더 텍스트 (글로우 제거)
        if header_text:
            header_surf = self.fonts["medium"].render(header_text.upper(), True, header_color)
            screen.blit(header_surf, (panel_rect.x + 20, panel_rect.y + 14))

        return panel_rect

    # =========================================================================
    # 아이템 카드 렌더링
    # =========================================================================

    def render_item_card(
        self,
        screen: pygame.Surface,
        rect: pygame.Rect,
        name: str,
        description: str,
        hover_progress: float = 0.0,
        is_affordable: bool = True,
        is_maxed: bool = False,
        cost: int = 0,
        level_info: str = "",
        header_color: Tuple[int, int, int] = None
    ):
        """통일된 아이템 카드 렌더링"""
        if header_color is None:
            header_color = config.STATE_COLORS["INFO"]

        # 크기 고정 (호버 시 확장 제거 - 떨림 방지)
        draw_rect = rect

        # 배경 색상 결정
        card_surf = pygame.Surface((draw_rect.width, draw_rect.height), pygame.SRCALPHA)

        if is_maxed:
            card_surf.fill((*config.STATE_COLORS["SUCCESS_DIM"], 200))
            border_color = config.STATE_COLORS["SUCCESS"]
            name_color = config.STATE_COLORS["SUCCESS"]
        elif hover_progress > 0 and is_affordable:
            alpha = int(160 + 60 * hover_progress)
            card_surf.fill((*config.BG_LEVELS["ELEVATED"], alpha))
            border_color = header_color
            name_color = config.TEXT_LEVELS["PRIMARY"]
        elif not is_affordable:
            card_surf.fill((*config.LOCKED_COLORS["BG"], 180))
            border_color = config.LOCKED_COLORS["BORDER"]
            name_color = config.LOCKED_COLORS["TEXT"]
        else:
            card_surf.fill(config.UI_COLORS["CARD_BG"])
            border_color = config.UI_COLORS["PANEL_BORDER"]
            name_color = config.TEXT_LEVELS["SECONDARY"]

        screen.blit(card_surf, draw_rect.topleft)
        pygame.draw.rect(screen, border_color, draw_rect, 1, border_radius=10)

        # 이름 (이모지 포함)
        name_text = render_text_with_emoji(name, self.fonts["medium"], name_color, "MEDIUM")
        screen.blit(name_text, (draw_rect.x + 12, draw_rect.y + 10))

        # 설명 (Light 폰트 - 가독성 향상)
        desc_color = config.TEXT_LEVELS["TERTIARY"] if is_affordable or is_maxed else config.LOCKED_COLORS["TEXT"]
        desc_font = self.fonts.get("light_small", self.fonts["small"])
        desc_text = desc_font.render(description, True, desc_color)
        screen.blit(desc_text, (draw_rect.x + 12, draw_rect.y + 38))

        # 레벨 정보 (Regular 폰트)
        if level_info:
            level_font = self.fonts.get("regular_small", self.fonts["small"])
            level_text = level_font.render(level_info, True, config.TEXT_LEVELS["TERTIARY"])
            screen.blit(level_text, (draw_rect.x + 12, draw_rect.y + 58))

        # 비용 (우측)
        if not is_maxed and cost > 0:
            cost_x = draw_rect.right - 95
            cost_y = draw_rect.y + 15

            # 코인 아이콘
            coin_color = config.STATE_COLORS["GOLD"] if is_affordable else config.LOCKED_COLORS["ICON"]
            pygame.draw.circle(screen, coin_color, (cost_x, cost_y + 6), 7)

            # 비용 텍스트
            cost_color = config.STATE_COLORS["GOLD"] if is_affordable else config.STATE_COLORS["DANGER"]
            cost_text = self.fonts["small"].render(f"{cost:,}", True, cost_color)
            screen.blit(cost_text, (cost_x + 14, cost_y))

        # MAX 뱃지
        if is_maxed:
            badge_x = draw_rect.right - 65
            badge_y = draw_rect.y + 28
            badge_surf = pygame.Surface((52, 22), pygame.SRCALPHA)
            badge_surf.fill((*config.STATE_COLORS["SUCCESS_DIM"], 200))
            screen.blit(badge_surf, (badge_x, badge_y))
            pygame.draw.rect(screen, config.STATE_COLORS["SUCCESS"],
                           (badge_x, badge_y, 52, 22), 1, border_radius=4)
            max_text = self.fonts["small"].render("MAX", True, config.STATE_COLORS["SUCCESS"])
            screen.blit(max_text, max_text.get_rect(center=(badge_x + 26, badge_y + 11)))

    # =========================================================================
    # 버튼 렌더링 (프리미엄 디자인)
    # =========================================================================

    def render_back_button(
        self,
        screen: pygame.Surface,
        hover: bool = False,
        text: str = "BACK"
    ) -> pygame.Rect:
        """통일된 뒤로가기 버튼 (우측 하단) - 미니멀 글래스 스타일"""
        btn_width = self.layout["BTN_BACK_WIDTH"]
        btn_height = self.layout["BTN_HEIGHT"]
        margin = self.layout["SCREEN_MARGIN"]

        rect = pygame.Rect(
            self.screen_size[0] - btn_width - margin,
            self.screen_size[1] - btn_height - margin // 2,
            btn_width,
            btn_height
        )

        # 크기 고정 (호버 시 확장 제거 - 떨림 방지)
        draw_rect = rect

        # 그림자
        if hover:
            shadow_surf = pygame.Surface((draw_rect.width + 6, draw_rect.height + 6), pygame.SRCALPHA)
            pygame.draw.rect(shadow_surf, (0, 0, 0, 40), (3, 4, draw_rect.width, draw_rect.height),
                           border_radius=self.layout["BTN_BORDER_RADIUS"])
            screen.blit(shadow_surf, (draw_rect.x - 2, draw_rect.y - 1))

        # 버튼 배경 (그라데이션)
        btn_surf = pygame.Surface((draw_rect.width, draw_rect.height), pygame.SRCALPHA)
        for y in range(draw_rect.height):
            ratio = y / draw_rect.height
            if hover:
                brightness = int(72 + 15 * (1 - ratio))
                alpha = 225
            else:
                brightness = int(48 + 10 * (1 - ratio))
                alpha = 200
            pygame.draw.line(btn_surf, (brightness, brightness + 4, brightness + 12, alpha),
                           (0, y), (draw_rect.width, y))

        screen.blit(btn_surf, draw_rect.topleft)

        # 상단 하이라이트
        highlight_alpha = 50 if hover else 30
        highlight_surf = pygame.Surface((draw_rect.width - 16, 2), pygame.SRCALPHA)
        highlight_surf.fill((255, 255, 255, highlight_alpha))
        screen.blit(highlight_surf, (draw_rect.x + 8, draw_rect.y + 3))

        # 테두리
        border_color = (130, 140, 165) if hover else (90, 98, 118)
        pygame.draw.rect(screen, border_color, draw_rect, 2,
                        border_radius=self.layout["BTN_BORDER_RADIUS"])

        # 화살표 아이콘 + 텍스트
        text_color = config.TEXT_LEVELS["PRIMARY"] if hover else config.TEXT_LEVELS["SECONDARY"]
        arrow = self.fonts["small"].render("◀", True, text_color)
        screen.blit(arrow, (draw_rect.x + 12, draw_rect.centery - arrow.get_height() // 2))

        text_surf = self.fonts["medium"].render(text, True, text_color)
        screen.blit(text_surf, (draw_rect.x + 32, draw_rect.centery - text_surf.get_height() // 2))

        return rect

    def render_action_button(
        self,
        screen: pygame.Surface,
        text: str,
        hover: bool = False,
        enabled: bool = True,
        danger: bool = False
    ) -> pygame.Rect:
        """통일된 액션 버튼 (좌측 하단) - 글로우 효과"""
        btn_width = self.layout["BTN_ACTION_WIDTH"]
        btn_height = self.layout["BTN_HEIGHT"]
        margin = self.layout["SCREEN_MARGIN"]

        rect = pygame.Rect(
            margin,
            self.screen_size[1] - btn_height - margin // 2,
            btn_width,
            btn_height
        )

        # 크기 고정 (호버 시 확장 제거 - 떨림 방지)
        draw_rect = rect

        # 색상 결정
        if not enabled:
            base_color = config.LOCKED_COLORS["BG"]
            glow_color = None
            border_color = config.LOCKED_COLORS["BORDER"]
            text_color = config.LOCKED_COLORS["TEXT"]
        elif danger:
            base_color = config.STATE_COLORS["DANGER_DIM"]
            glow_color = config.STATE_COLORS["DANGER"]
            border_color = config.STATE_COLORS["DANGER"]
            text_color = config.TEXT_LEVELS["PRIMARY"]
        else:
            base_color = config.STATE_COLORS["SUCCESS_DIM"]
            glow_color = config.STATE_COLORS["SUCCESS"]
            border_color = config.STATE_COLORS["SUCCESS"]
            text_color = config.TEXT_LEVELS["PRIMARY"]

        # 글로우/그림자 제거 - 미니멀 디자인

        # 버튼 배경 (단색)
        btn_surf = pygame.Surface((draw_rect.width, draw_rect.height), pygame.SRCALPHA)
        alpha = 220 if enabled else 160
        btn_surf.fill((*base_color, alpha))
        screen.blit(btn_surf, draw_rect.topleft)

        # 테두리 (호버 시 밝게)
        border_width = 2 if hover else 1
        pygame.draw.rect(screen, border_color, draw_rect, border_width,
                        border_radius=self.layout["BTN_BORDER_RADIUS"])

        text_surf = self.fonts["medium"].render(text, True, text_color)
        screen.blit(text_surf, text_surf.get_rect(center=draw_rect.center))

        return rect

    # =========================================================================
    # 키보드 힌트 렌더링
    # =========================================================================

    def render_keyboard_hints(
        self,
        screen: pygame.Surface,
        hints: str
    ):
        """통일된 키보드 힌트 (하단 중앙) - Light 폰트"""
        hint_y = self.screen_size[1] - self.layout["HINT_Y_OFFSET"]

        hint_font = self.fonts.get("light_small", self.fonts["small"])
        hint_text = hint_font.render(hints, True, config.TEXT_LEVELS["MUTED"])
        screen.blit(hint_text, hint_text.get_rect(center=(self.screen_size[0] // 2, hint_y)))

    # =========================================================================
    # 스크롤바 렌더링
    # =========================================================================

    def render_scrollbar(
        self,
        screen: pygame.Surface,
        panel_rect: pygame.Rect,
        scroll_offset: float,
        max_scroll: float,
        visible_height: float,
        total_height: float
    ):
        """스크롤바 렌더링"""
        if max_scroll <= 0:
            return

        scrollbar_x = panel_rect.right - 10
        scrollbar_y = panel_rect.y + 45
        scrollbar_height = panel_rect.height - 65

        # 배경
        pygame.draw.rect(screen, (45, 50, 62),
                        (scrollbar_x, scrollbar_y, 6, scrollbar_height),
                        border_radius=3)

        # 핸들
        handle_height = max(30, scrollbar_height * (visible_height / total_height))
        handle_y = scrollbar_y + (scroll_offset / max_scroll) * (scrollbar_height - handle_height)

        pygame.draw.rect(screen, (95, 105, 125),
                        (scrollbar_x, handle_y, 6, handle_height),
                        border_radius=3)


# =============================================================================
# 파티클 시스템 (통일)
# =============================================================================

@dataclass
class Particle:
    """파티클 데이터"""
    x: float
    y: float
    vx: float
    vy: float
    size: float
    alpha: float
    color: Tuple[int, int, int]
    life: float
    max_life: float


class UnifiedParticleSystem:
    """통일된 파티클 시스템"""

    def __init__(self, screen_size: Tuple[int, int], count: int = 50,
                 color_scheme: str = "default"):
        self.screen_size = screen_size
        self.particles: List[Particle] = []
        self.max_particles = count
        self.color_scheme = color_scheme

        # 색상 스킴 정의
        self.color_schemes = {
            "default": [
                (100, 150, 255),
                (150, 100, 255),
                (100, 200, 255),
            ],
            "workshop": [
                (255, 180, 80),
                (255, 150, 50),
                (200, 220, 255),
            ],
            "shop": [
                (100, 200, 150),
                (80, 180, 220),
                (220, 180, 80),
            ],
            "hangar": [
                (100, 150, 255),
                (80, 120, 200),
                (150, 100, 255),
            ],
            "briefing": [
                (80, 120, 200),
                (100, 80, 180),
                (60, 140, 200),
            ],
        }

    def _get_colors(self) -> List[Tuple[int, int, int]]:
        return self.color_schemes.get(self.color_scheme, self.color_schemes["default"])

    def _spawn_particle(self):
        """파티클 생성"""
        import random
        colors = self._get_colors()

        self.particles.append(Particle(
            x=random.randint(0, self.screen_size[0]),
            y=random.randint(0, self.screen_size[1]),
            vx=random.uniform(-12, 12),
            vy=random.uniform(-18, -5),
            size=random.uniform(1, 2.5),
            alpha=random.uniform(30, 70),
            color=random.choice(colors),
            life=random.uniform(3, 7),
            max_life=random.uniform(3, 7)
        ))

    def update(self, dt: float):
        """파티클 업데이트"""
        import random

        while len(self.particles) < self.max_particles:
            self._spawn_particle()

        for p in self.particles[:]:
            p.x += p.vx * dt
            p.y += p.vy * dt
            p.life -= dt
            p.alpha = max(0, (p.life / p.max_life) * 70)

            if p.life <= 0 or p.y < -20:
                self.particles.remove(p)
                # 새 파티클은 하단에서 생성
                if len(self.particles) < self.max_particles:
                    new_p = Particle(
                        x=random.randint(0, self.screen_size[0]),
                        y=self.screen_size[1] + random.randint(0, 20),
                        vx=random.uniform(-12, 12),
                        vy=random.uniform(-18, -5),
                        size=random.uniform(1, 2.5),
                        alpha=random.uniform(30, 70),
                        color=random.choice(self._get_colors()),
                        life=random.uniform(3, 7),
                        max_life=random.uniform(3, 7)
                    )
                    self.particles.append(new_p)

    def render(self, screen: pygame.Surface):
        """파티클 렌더링"""
        for p in self.particles:
            if p.alpha > 0:
                alpha_val = max(0, min(255, int(p.alpha)))
                color = (p.color[0], p.color[1], p.color[2], alpha_val)
                size = max(1, int(p.size))

                surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
                pygame.draw.circle(surf, color, (size, size), size)
                screen.blit(surf, (int(p.x - size), int(p.y - size)))


# =============================================================================
# UI 전환 애니메이션
# =============================================================================

class UITransition:
    """
    UI 요소의 등장/퇴장 전환 애니메이션을 관리하는 클래스.
    슬라이드 인/아웃, 페이드 인/아웃 효과를 지원합니다.
    """
    def __init__(self, duration: float = 0.3):
        """
        Args:
            duration: 전환 애니메이션 지속 시간 (초)
        """
        self.duration = duration
        self.progress = 0.0  # 0.0 = 시작, 1.0 = 완료
        self.is_active = False
        self.direction = "in"  # "in" 또는 "out"
        self.start_time = 0.0

    @staticmethod
    def ease_out_cubic(t: float) -> float:
        """부드러운 감속 이징 함수"""
        return 1.0 - pow(1.0 - t, 3)

    @staticmethod
    def ease_in_cubic(t: float) -> float:
        """부드러운 가속 이징 함수"""
        return t * t * t

    def start(self, direction: str = "in"):
        """
        전환 애니메이션을 시작합니다.

        Args:
            direction: "in" (나타남) 또는 "out" (사라짐)
        """
        self.is_active = True
        self.direction = direction
        self.progress = 0.0
        self.start_time = pygame.time.get_ticks() / 1000.0

    def update(self) -> bool:
        """
        전환 애니메이션을 업데이트합니다.

        Returns:
            bool: 애니메이션이 아직 활성 상태인지 여부
        """
        if not self.is_active:
            return False

        current_time = pygame.time.get_ticks() / 1000.0
        elapsed = current_time - self.start_time
        self.progress = min(1.0, elapsed / self.duration)

        if self.progress >= 1.0:
            self.is_active = False

        return self.is_active

    def get_alpha(self) -> int:
        """현재 알파값 반환 (0-255)"""
        eased = self.ease_out_cubic(self.progress)
        if self.direction == "in":
            return int(255 * eased)
        else:
            return int(255 * (1.0 - eased))

    def get_slide_offset(self, distance: int = 50) -> Tuple[int, int]:
        """
        슬라이드 오프셋 반환 (위에서 아래로)

        Args:
            distance: 슬라이드 이동 거리 (픽셀)

        Returns:
            Tuple[int, int]: (x_offset, y_offset)
        """
        eased = self.ease_out_cubic(self.progress)
        if self.direction == "in":
            # 위에서 아래로 슬라이드 인
            offset = int(distance * (1.0 - eased))
            return (0, -offset)
        else:
            # 아래에서 위로 슬라이드 아웃
            offset = int(distance * eased)
            return (0, -offset)

    def get_scale(self) -> float:
        """현재 스케일 반환 (0.0-1.0)"""
        eased = self.ease_out_cubic(self.progress)
        if self.direction == "in":
            return 0.9 + 0.1 * eased  # 0.9 → 1.0
        else:
            return 1.0 - 0.1 * eased  # 1.0 → 0.9

    def is_complete(self) -> bool:
        """전환 애니메이션이 완료되었는지 확인"""
        return not self.is_active and self.progress >= 1.0


class ButtonHoverEffect:
    """
    버튼 호버 효과를 관리하는 클래스.
    부드러운 확대/색상 변화를 제공합니다.
    """
    def __init__(self):
        self.hover_progress: Dict[str, float] = {}  # 버튼 ID별 호버 진행도
        self.transition_speed = 8.0  # 전환 속도

    def update(self, button_id: str, is_hovered: bool, dt: float):
        """
        버튼의 호버 상태를 업데이트합니다.

        Args:
            button_id: 버튼 고유 ID
            is_hovered: 현재 호버 상태
            dt: 델타 타임
        """
        if button_id not in self.hover_progress:
            self.hover_progress[button_id] = 0.0

        target = 1.0 if is_hovered else 0.0
        current = self.hover_progress[button_id]

        # 부드러운 전환
        diff = target - current
        self.hover_progress[button_id] += diff * self.transition_speed * dt
        self.hover_progress[button_id] = max(0.0, min(1.0, self.hover_progress[button_id]))

    def get_progress(self, button_id: str) -> float:
        """버튼의 현재 호버 진행도 반환 (0.0-1.0)"""
        return self.hover_progress.get(button_id, 0.0)

    def get_scale(self, button_id: str) -> float:
        """버튼의 현재 스케일 반환"""
        progress = self.get_progress(button_id)
        return 1.0 + 0.05 * progress  # 최대 5% 확대

    def get_brightness(self, button_id: str) -> float:
        """버튼의 현재 밝기 반환 (1.0-1.3)"""
        progress = self.get_progress(button_id)
        return 1.0 + 0.3 * progress


print("INFO: ui_components.py loaded (Unified UI System)")
