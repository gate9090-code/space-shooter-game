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
from ui import render_text_with_emoji


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
    # 타이틀 렌더링
    # =========================================================================

    def render_title(
        self,
        screen: pygame.Surface,
        title_text: str,
        glow_color: Tuple[int, int, int] = None,
        glow_intensity: float = 0.5
    ):
        """통일된 타이틀 렌더링"""
        if glow_color is None:
            glow_color = config.STATE_COLORS["INFO"]

        center_x = self.screen_size[0] // 2
        title_y = self.layout["TITLE_Y"]

        # 글로우 효과
        glow_alpha = int(60 + 40 * glow_intensity)
        glow_surf = pygame.Surface((300, 45), pygame.SRCALPHA)
        pygame.draw.ellipse(glow_surf, (*glow_color, glow_alpha), (30, 8, 240, 28))
        screen.blit(glow_surf, (center_x - 150, title_y - 18))

        # 타이틀 텍스트
        title = self.fonts["large"].render(title_text, True, config.TEXT_LEVELS["PRIMARY"])
        screen.blit(title, title.get_rect(center=(center_x, title_y)))

    # =========================================================================
    # 크레딧 박스 렌더링
    # =========================================================================

    def render_credit_box(
        self,
        screen: pygame.Surface,
        credits: int,
        flash_intensity: float = 0.0
    ):
        """통일된 크레딧 표시"""
        box_width = self.layout["CREDIT_BOX_WIDTH"]
        box_height = self.layout["CREDIT_BOX_HEIGHT"]
        margin = self.layout["SCREEN_MARGIN"]

        box_x = self.screen_size[0] - box_width - margin
        box_y = margin

        # 배경
        box_surf = pygame.Surface((box_width, box_height), pygame.SRCALPHA)

        if flash_intensity > 0:
            # 구매 시 플래시 효과
            flash_alpha = int(80 * flash_intensity)
            box_surf.fill((*config.STATE_COLORS["SUCCESS"][:3], flash_alpha + 150))
        else:
            box_surf.fill(config.UI_COLORS["PANEL_BG"])

        screen.blit(box_surf, (box_x, box_y))

        # 테두리
        border_color = config.STATE_COLORS["GOLD"] if flash_intensity > 0 else (85, 95, 115)
        pygame.draw.rect(screen, border_color, (box_x, box_y, box_width, box_height), 2,
                        border_radius=self.layout["TAB_BORDER_RADIUS"])

        # 코인 아이콘 + 금액
        coin_text = render_text_with_emoji(
            f"$ {credits:,}",
            self.fonts["medium"],
            config.STATE_COLORS["GOLD"],
            "MEDIUM"
        )
        screen.blit(coin_text, coin_text.get_rect(center=(box_x + box_width // 2, box_y + box_height // 2)))

    # =========================================================================
    # 가로 탭 렌더링
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
        통일된 가로 탭 렌더링

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

            # 확장 효과
            expand = int(hover * 3)
            draw_rect = rect.inflate(expand, expand // 2)

            # 탭 배경
            tab_surf = pygame.Surface((draw_rect.width, draw_rect.height), pygame.SRCALPHA)

            if not tab.enabled:
                tab_surf.fill(config.INTERACTION_STATES["DISABLED"]["bg"])
                border_color = config.INTERACTION_STATES["DISABLED"]["border"]
                text_color = config.INTERACTION_STATES["DISABLED"]["text"]
            elif is_selected:
                # 선택됨: 카테고리 색상 사용
                tab_surf.fill((*tab.color, 200))
                border_color = tuple(min(255, c + 50) for c in tab.color)
                text_color = config.TEXT_LEVELS["PRIMARY"]
            elif hover > 0:
                # 호버
                alpha = int(160 + 60 * hover)
                tab_surf.fill((*config.BG_LEVELS["ELEVATED"], alpha))
                border_color = tab.color
                text_color = config.TEXT_LEVELS["PRIMARY"]
            else:
                # 일반
                tab_surf.fill(config.UI_COLORS["TAB_BG_NORMAL"])
                border_color = config.UI_COLORS["TAB_BORDER_NORMAL"]
                text_color = config.TEXT_LEVELS["SECONDARY"]

            screen.blit(tab_surf, draw_rect.topleft)
            pygame.draw.rect(screen, border_color, draw_rect,
                           2 if is_selected else 1, border_radius=border_radius)

            # 선택 표시 바 (하단)
            if is_selected:
                bar_width = draw_rect.width - 20
                pygame.draw.rect(screen, tab.color,
                               (draw_rect.x + 10, draw_rect.bottom - 3, bar_width, 3),
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
    # 콘텐츠 패널 렌더링
    # =========================================================================

    def render_content_panel(
        self,
        screen: pygame.Surface,
        header_text: str = "",
        header_color: Tuple[int, int, int] = None
    ) -> pygame.Rect:
        """
        통일된 콘텐츠 패널 배경 렌더링

        Returns:
            pygame.Rect: 패널 영역
        """
        panel_rect = self.get_content_panel_rect()

        if header_color is None:
            header_color = config.STATE_COLORS["INFO"]

        # 글래스모피즘 배경
        panel_surf = pygame.Surface((panel_rect.width, panel_rect.height), pygame.SRCALPHA)
        panel_surf.fill(config.UI_COLORS["PANEL_BG"])
        screen.blit(panel_surf, panel_rect.topleft)

        # 테두리
        pygame.draw.rect(screen, config.UI_COLORS["PANEL_BORDER"], panel_rect, 1,
                        border_radius=12)

        # 헤더 바
        pygame.draw.rect(screen, header_color,
                        (panel_rect.x, panel_rect.y, panel_rect.width, 3),
                        border_radius=2)

        # 헤더 텍스트
        if header_text:
            header_surf = self.fonts["medium"].render(header_text.upper(), True, header_color)
            screen.blit(header_surf, (panel_rect.x + 20, panel_rect.y + 12))

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

        # 확장 효과
        expand = int(hover_progress * 5)
        draw_rect = rect.inflate(expand, expand // 2)

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

        # 설명
        desc_color = config.TEXT_LEVELS["TERTIARY"] if is_affordable or is_maxed else config.LOCKED_COLORS["TEXT"]
        desc_text = self.fonts["small"].render(description, True, desc_color)
        screen.blit(desc_text, (draw_rect.x + 12, draw_rect.y + 38))

        # 레벨 정보
        if level_info:
            level_text = self.fonts["small"].render(level_info, True, config.TEXT_LEVELS["TERTIARY"])
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
    # 버튼 렌더링
    # =========================================================================

    def render_back_button(
        self,
        screen: pygame.Surface,
        hover: bool = False,
        text: str = "BACK"
    ) -> pygame.Rect:
        """통일된 뒤로가기 버튼 (우측 하단)"""
        btn_width = self.layout["BTN_BACK_WIDTH"]
        btn_height = self.layout["BTN_HEIGHT"]
        margin = self.layout["SCREEN_MARGIN"]

        rect = pygame.Rect(
            self.screen_size[0] - btn_width - margin,
            self.screen_size[1] - btn_height - margin // 2,
            btn_width,
            btn_height
        )

        # 버튼 배경
        btn_surf = pygame.Surface((btn_width, btn_height), pygame.SRCALPHA)
        if hover:
            btn_surf.fill(config.UI_COLORS["BTN_BACK_HOVER"])
            border_color = (120, 128, 155)
        else:
            btn_surf.fill(config.UI_COLORS["BTN_BACK_NORMAL"])
            border_color = (85, 92, 112)

        screen.blit(btn_surf, rect.topleft)
        pygame.draw.rect(screen, border_color, rect, 2,
                        border_radius=self.layout["BTN_BORDER_RADIUS"])

        # 텍스트
        text_surf = self.fonts["medium"].render(text, True, config.TEXT_LEVELS["SECONDARY"])
        screen.blit(text_surf, text_surf.get_rect(center=rect.center))

        return rect

    def render_action_button(
        self,
        screen: pygame.Surface,
        text: str,
        hover: bool = False,
        enabled: bool = True,
        danger: bool = False
    ) -> pygame.Rect:
        """통일된 액션 버튼 (좌측 하단)"""
        btn_width = self.layout["BTN_ACTION_WIDTH"]
        btn_height = self.layout["BTN_HEIGHT"]
        margin = self.layout["SCREEN_MARGIN"]

        rect = pygame.Rect(
            margin,
            self.screen_size[1] - btn_height - margin // 2,
            btn_width,
            btn_height
        )

        # 버튼 배경
        btn_surf = pygame.Surface((btn_width, btn_height), pygame.SRCALPHA)

        if not enabled:
            btn_surf.fill(config.INTERACTION_STATES["DISABLED"]["bg"])
            border_color = config.INTERACTION_STATES["DISABLED"]["border"]
            text_color = config.INTERACTION_STATES["DISABLED"]["text"]
        elif danger:
            if hover:
                btn_surf.fill(config.UI_COLORS["BTN_DANGER_HOVER"])
            else:
                btn_surf.fill(config.UI_COLORS["BTN_DANGER_NORMAL"])
            border_color = config.STATE_COLORS["DANGER"]
            text_color = config.TEXT_LEVELS["PRIMARY"]
        else:
            if hover:
                btn_surf.fill(config.UI_COLORS["BTN_ACTION_HOVER"])
                border_color = config.STATE_COLORS["SUCCESS"]
            else:
                btn_surf.fill(config.UI_COLORS["BTN_ACTION_NORMAL"])
                border_color = (72, 145, 115)
            text_color = config.TEXT_LEVELS["PRIMARY"]

        screen.blit(btn_surf, rect.topleft)
        pygame.draw.rect(screen, border_color, rect, 2,
                        border_radius=self.layout["BTN_BORDER_RADIUS"])

        # 텍스트
        text_surf = self.fonts["medium"].render(text, True, text_color)
        screen.blit(text_surf, text_surf.get_rect(center=rect.center))

        return rect

    # =========================================================================
    # 키보드 힌트 렌더링
    # =========================================================================

    def render_keyboard_hints(
        self,
        screen: pygame.Surface,
        hints: str
    ):
        """통일된 키보드 힌트 (하단 중앙)"""
        hint_y = self.screen_size[1] - self.layout["HINT_Y_OFFSET"]

        hint_text = self.fonts["small"].render(hints, True, config.TEXT_LEVELS["MUTED"])
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
