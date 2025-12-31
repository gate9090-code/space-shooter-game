# modes/workshop_mode.py
"""
WorkshopMode - 정비소 모드 (Unified Modern UI)

모든 업그레이드를 크레딧으로 구매하는 통합 시스템
- 통일된 UI 컴포넌트 사용
- WCAG 대비율 준수 색상
"""

import pygame
import math
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass

import config
from modes.base_mode import GameMode, ModeConfig
from ui import render_text_with_emoji
from ui_components import UILayoutManager, TabData, TabState, UnifiedParticleSystem


# =============================================================================
# 업그레이드 카테고리 정의 (통일된 색상 사용)
# =============================================================================
UPGRADE_CATEGORIES = {
    "stats": {
        "name": "Basic Stats",
        "icon": "📊",
        "color": config.CATEGORY_COLORS["STATS"],
        "upgrades": [
            {"id": "MAX_HP", "name": "💚 Max Health", "desc": "+20 HP per level", "base_cost": 100, "max_level": 10, "per_level": "+20 HP"},
            {"id": "SPEED", "name": "⚡ Movement Speed", "desc": "+25 speed per level", "base_cost": 100, "max_level": 10, "per_level": "+25 SPD"},
            {"id": "COOLDOWN", "name": "🎯 Fire Rate", "desc": "-5% cooldown per level", "base_cost": 120, "max_level": 10, "per_level": "-5% CD"},
            {"id": "DAMAGE", "name": "⚔️ Base Damage", "desc": "+15% damage per level", "base_cost": 150, "max_level": 10, "per_level": "+15% DMG"},
        ]
    },
    "weapon_basic": {
        "name": "Weapon Basic",
        "icon": "🔫",
        "color": config.CATEGORY_COLORS["ATTACK"],
        "upgrades": [
            {"id": "BULLET_COUNT", "name": "🔥 Bullet Hail", "desc": "+1 bullet per shot", "base_cost": 300, "max_level": 5, "per_level": "+1"},
            {"id": "PIERCING", "name": "➡️ Piercing Rounds", "desc": "Bullets pass through enemies", "base_cost": 500, "max_level": 1, "one_time": True},
            {"id": "FOCUSED_SHOT", "name": "🎯 Focused Shot", "desc": "-50% bullet spread", "base_cost": 400, "max_level": 1, "one_time": True},
            {"id": "HOMING", "name": "🏹 Homing Bullets", "desc": "Bullets track enemies", "base_cost": 800, "max_level": 1, "one_time": True},
            {"id": "CRITICAL", "name": "💥 Critical Strike", "desc": "20% crit chance (2x dmg)", "base_cost": 600, "max_level": 3, "per_level": "+10%"},
            {"id": "BACKSTAB", "name": "🗡️ Backstab", "desc": "+150% rear damage", "base_cost": 700, "max_level": 1, "one_time": True},
        ]
    },
    "elemental": {
        "name": "Elemental",
        "icon": "✨",
        "color": config.CATEGORY_COLORS["ELEMENTAL"],
        "upgrades": [
            {"id": "EXPLOSIVE", "name": "💣 Explosive Bullets", "desc": "Enemies explode on death", "base_cost": 600, "max_level": 1, "one_time": True},
            {"id": "CHAIN_EXPLOSION", "name": "🔥 Chain Reaction", "desc": "Explosions chain to nearby", "base_cost": 900, "max_level": 1, "one_time": True, "requires": "EXPLOSIVE"},
            {"id": "LIGHTNING", "name": "⚡ Chain Lightning", "desc": "Bullets chain to 3 enemies", "base_cost": 700, "max_level": 3, "per_level": "+1 chain"},
            {"id": "STATIC_FIELD", "name": "🌩️ Static Field", "desc": "Enemies leave electric field", "base_cost": 1000, "max_level": 1, "one_time": True, "requires": "LIGHTNING"},
            {"id": "FROST", "name": "❄️ Frost Bullets", "desc": "Slow enemies by 30%", "base_cost": 500, "max_level": 3, "per_level": "+10% slow"},
            {"id": "DEEP_FREEZE", "name": "🧊 Deep Freeze", "desc": "15% chance to freeze", "base_cost": 900, "max_level": 1, "one_time": True, "requires": "FROST"},
            {"id": "TIME_WARP", "name": "⏰ Time Warp", "desc": "Hit enemies move 40% slower", "base_cost": 800, "max_level": 1, "one_time": True},
        ]
    },
    "defense": {
        "name": "Defense",
        "icon": "🛡️",
        "color": config.CATEGORY_COLORS["DEFENSE"],
        "upgrades": [
            {"id": "DAMAGE_REDUCTION", "name": "🛡️ Damage Reduction", "desc": "-10% damage taken", "base_cost": 400, "max_level": 5, "per_level": "-10%"},
            {"id": "REGENERATION", "name": "💚 Regeneration", "desc": "+1 HP per second", "base_cost": 500, "max_level": 5, "per_level": "+1 HP/s"},
            {"id": "VAMPIRISM", "name": "🧛 Vampirism", "desc": "Heal 15% of damage dealt", "base_cost": 800, "max_level": 3, "per_level": "+5%"},
            {"id": "THORNS", "name": "🌵 Thorns", "desc": "Reflect 50% damage", "base_cost": 600, "max_level": 3, "per_level": "+25%"},
            {"id": "STORM_SHIELD", "name": "🌀 Storm Shield", "desc": "Damage nearby enemies", "base_cost": 700, "max_level": 3, "per_level": "+10 DPS"},
            {"id": "DIAMOND_SKIN", "name": "💎 Diamond Skin", "desc": "30% permanent reduction", "base_cost": 1500, "max_level": 1, "one_time": True},
            {"id": "PHOENIX", "name": "🔥 Phoenix Rebirth", "desc": "Revive once (120s CD)", "base_cost": 2000, "max_level": 1, "one_time": True},
            {"id": "SECOND_CHANCE", "name": "💫 Second Chance", "desc": "Survive fatal hit (60s CD)", "base_cost": 1200, "max_level": 1, "one_time": True},
        ]
    },
    "support": {
        "name": "Support Units",
        "icon": "🤖",
        "color": config.CATEGORY_COLORS["SUPPORT"],
        "upgrades": [
            {"id": "TURRET", "name": "🔧 Auto Turret", "desc": "Deploy auto turret", "base_cost": 800, "max_level": 3, "per_level": "+1 turret"},
            {"id": "DRONE", "name": "🛸 Drone Companion", "desc": "Drone orbits and shoots", "base_cost": 900, "max_level": 3, "per_level": "+1 drone"},
        ]
    },
    "utility": {
        "name": "Utility",
        "icon": "🧰",
        "color": config.CATEGORY_COLORS["UTILITY"],
        "upgrades": [
            {"id": "COIN_MAGNET", "name": "🧲 Coin Magnet", "desc": "Auto-collect coins", "base_cost": 300, "max_level": 1, "one_time": True},
            {"id": "LUCKY_DROP", "name": "🍀 Lucky Drop", "desc": "+50% coin drops", "base_cost": 500, "max_level": 3, "per_level": "+25%"},
            {"id": "EXP_BOOST", "name": "✨ Experience Boost", "desc": "+30% experience", "base_cost": 600, "max_level": 3, "per_level": "+15%"},
        ]
    },
    "advanced": {
        "name": "Advanced",
        "icon": "⭐",
        "color": config.CATEGORY_COLORS["ADVANCED"],
        "upgrades": [
            {"id": "BULLET_STORM", "name": "🌪️ Bullet Storm", "desc": "+1 Bullet, +50% Fire Rate", "base_cost": 1500, "max_level": 1, "one_time": True},
            {"id": "EXECUTE", "name": "☠️ Execute", "desc": "Instant kill <20% HP enemies", "base_cost": 1800, "max_level": 1, "one_time": True},
            {"id": "BERSERKER", "name": "😡 Berserker", "desc": "+100% DMG at <30% HP", "base_cost": 1200, "max_level": 1, "one_time": True},
            {"id": "STARFALL", "name": "🌟 Starfall", "desc": "Stars fall every 5 kills", "base_cost": 1600, "max_level": 1, "one_time": True},
            {"id": "ARCANE_MASTERY", "name": "🔮 Arcane Mastery", "desc": "All elements +50%", "base_cost": 2000, "max_level": 1, "one_time": True},
        ]
    },
}


@dataclass
class UpgradeItem:
    """업그레이드 항목"""
    category: str
    upgrade_id: str
    rect: pygame.Rect
    hover_progress: float = 0.0


class WorkshopMode(GameMode):
    """
    정비소 모드 - Unified Modern UI Design

    특징:
    - 통일된 UI 컴포넌트 사용
    - 상단 가로 탭 (7개 카테고리)
    - 중앙 콘텐츠 패널 (600px)
    - WCAG 대비율 준수 색상
    """

    def get_config(self) -> ModeConfig:
        return ModeConfig(
            mode_name="workshop",
            perspective_enabled=False,
            background_type="static",
            parallax_enabled=False,
            meteor_enabled=False,
            show_wave_ui=False,
            show_skill_indicators=False,
            wave_system_enabled=False,
            spawn_system_enabled=False,
            asset_prefix="workshop",
        )

    def init(self):
        """정비소 모드 초기화"""
        config.GAME_MODE = "workshop"

        # UI 매니저 초기화
        self.ui_manager = UILayoutManager(self.screen_size, self.fonts)

        # 플레이어 데이터
        self.player_upgrades = self.engine.shared_state.get('player_upgrades', {}).copy()
        self.credits = self.engine.shared_state.get('global_score', 0)

        # UI 상태
        self.selected_category = "stats"
        self.hovered_upgrade: Optional[str] = None
        self.scroll_offset = 0
        self.max_scroll = 0

        # 배경 및 파티클
        self.background = self._create_background()
        self.particle_system = UnifiedParticleSystem(self.screen_size, 50, "workshop")

        # 애니메이션 상태
        self.animation_time = 0.0
        self.purchase_flash = 0.0
        self.purchase_success_id: Optional[str] = None  # 구매 성공한 업그레이드 ID
        self.purchase_fail_time = 0.0  # 구매 실패 시각 효과

        # 탭 데이터 생성
        self.tabs = [
            TabData(id=cat_id, name=cat["name"], icon=cat["icon"], color=cat["color"])
            for cat_id, cat in UPGRADE_CATEGORIES.items()
        ]
        self.tab_states: Dict[str, TabState] = {tab.id: TabState() for tab in self.tabs}
        self.tab_rects: Dict[str, pygame.Rect] = {}

        # 업그레이드 아이템
        self.upgrade_items: List[UpgradeItem] = []

        # 버튼 상태
        self.back_rect = None
        self.back_hover = False

        # 커스텀 커서
        self.custom_cursor = self._load_base_cursor()

        print("INFO: WorkshopMode initialized (Unified UI)")

    def _create_background(self) -> pygame.Surface:
        """배경 생성 - facility_bg 이미지 사용"""
        # facility_bg 이미지 로드 시도
        bg_path = config.ASSET_DIR / "images" / "facilities" / "facility_bg.png"
        try:
            if bg_path.exists():
                bg = pygame.image.load(str(bg_path)).convert()
                return pygame.transform.smoothscale(bg, self.screen_size)
        except Exception as e:
            print(f"WARNING: Failed to load facility_bg for workshop: {e}")

        # 폴백: 기본 그라데이션 배경
        bg = self.ui_manager.create_gradient_background(
            base_color=config.BG_LEVELS["SCREEN"],
            variation=18
        )
        return bg

    def _draw_gear(self, surface: pygame.Surface, center: Tuple[int, int],
                   radius: int, color: Tuple[int, int, int]):
        """톱니바퀴 그리기"""
        pygame.draw.circle(surface, color, center, radius, 2)
        pygame.draw.circle(surface, color, center, radius - 15, 1)

        teeth = 12
        for i in range(teeth):
            angle = (2 * math.pi / teeth) * i
            inner_x = center[0] + (radius - 10) * math.cos(angle)
            inner_y = center[1] + (radius - 10) * math.sin(angle)
            outer_x = center[0] + (radius + 8) * math.cos(angle)
            outer_y = center[1] + (radius + 8) * math.sin(angle)
            pygame.draw.line(surface, color, (inner_x, inner_y), (outer_x, outer_y), 2)

    def _get_upgrade_cost(self, upgrade_data: dict, current_level: int) -> int:
        """업그레이드 비용 계산"""
        base_cost = upgrade_data["base_cost"]
        if upgrade_data.get("one_time") or upgrade_data.get("consumable"):
            return base_cost
        return int(base_cost * (1.5 ** current_level))

    def _can_purchase(self, upgrade_data: dict, current_level: int) -> bool:
        """구매 가능 여부"""
        max_level = upgrade_data["max_level"]
        if current_level >= max_level and not upgrade_data.get("consumable"):
            return False
        cost = self._get_upgrade_cost(upgrade_data, current_level)
        return self.credits >= cost

    def update(self, dt: float, current_time: float):
        """업데이트"""
        self.animation_time += dt
        self.purchase_flash = max(0, self.purchase_flash - dt * 3)
        self.purchase_fail_time = max(0, self.purchase_fail_time - dt * 4)

        # 구매 성공 효과 타이머
        if self.purchase_success_id and self.purchase_flash <= 0:
            self.purchase_success_id = None

        # 파티클 업데이트
        self.particle_system.update(dt)

        # 마우스 위치
        mouse_pos = pygame.mouse.get_pos()
        self.hovered_upgrade = None

        # 탭 호버 업데이트
        for tab_id, rect in self.tab_rects.items():
            state = self.tab_states[tab_id]
            if rect and rect.collidepoint(mouse_pos):
                state.hover_progress = min(1.0, state.hover_progress + dt * 6)
            else:
                state.hover_progress = max(0.0, state.hover_progress - dt * 4)

        # 업그레이드 호버 업데이트
        for item in self.upgrade_items:
            if item.rect.collidepoint(mouse_pos):
                self.hovered_upgrade = item.upgrade_id
                item.hover_progress = min(1.0, item.hover_progress + dt * 6)
            else:
                item.hover_progress = max(0.0, item.hover_progress - dt * 4)

        # 뒤로가기 버튼 호버
        if self.back_rect:
            self.back_hover = self.back_rect.collidepoint(mouse_pos)

    def render(self, screen: pygame.Surface):
        """렌더링"""
        # 배경
        screen.blit(self.background, (0, 0))

        # 구매 실패 시 빨간 플래시
        if self.purchase_fail_time > 0:
            fail_surf = pygame.Surface(self.screen_size, pygame.SRCALPHA)
            fail_alpha = int(60 * self.purchase_fail_time)
            fail_surf.fill((255, 50, 50, fail_alpha))
            screen.blit(fail_surf, (0, 0))

        # 파티클
        self.particle_system.render(screen)

        # 타이틀
        glow_intensity = (math.sin(self.animation_time * 2.5) + 1) / 2
        self.ui_manager.render_title(screen, "W O R K S H O P",
                                     config.STATE_COLORS["WARNING"], glow_intensity)

        # 크레딧 표시 (구매 실패 시 빨간색으로 변경)
        credit_flash = self.purchase_flash if self.purchase_fail_time <= 0 else -self.purchase_fail_time
        self.ui_manager.render_credit_box(screen, self.credits, credit_flash)

        # 카테고리 탭
        self.tab_rects = self.ui_manager.render_horizontal_tabs(
            screen, self.tabs, self.selected_category, self.tab_states, tab_width=95
        )

        # 업그레이드 목록
        self._render_upgrades(screen)

        # 하단 버튼
        self.back_rect = self.ui_manager.render_back_button(screen, self.back_hover)

        # 키보드 힌트
        self.ui_manager.render_keyboard_hints(screen, "1-7 Categories  |  Scroll Mouse  |  ESC Back")

        # 커스텀 커서
        self._render_base_cursor(screen, self.custom_cursor)

    def _render_upgrades(self, screen: pygame.Surface):
        """업그레이드 목록 렌더링"""
        cat_data = UPGRADE_CATEGORIES[self.selected_category]
        header_color = cat_data["color"]

        # 콘텐츠 패널
        panel_rect = self.ui_manager.render_content_panel(
            screen, cat_data["name"], header_color
        )

        # 업그레이드 목록
        upgrades = cat_data["upgrades"]
        self.upgrade_items.clear()

        layout = config.UI_LAYOUT
        item_height = layout["ITEM_HEIGHT"]
        item_spacing = layout["ITEM_SPACING"]
        item_width = panel_rect.width - 30
        content_start_y = panel_rect.y + 42

        # 스크롤 계산
        total_content_height = len(upgrades) * (item_height + item_spacing)
        visible_height = panel_rect.height - 65
        self.max_scroll = max(0, total_content_height - visible_height)
        self.scroll_offset = min(self.scroll_offset, self.max_scroll)

        for i, upgrade in enumerate(upgrades):
            item_y = content_start_y + i * (item_height + item_spacing) - self.scroll_offset

            # 화면 밖 스킵
            if item_y + item_height < content_start_y or item_y > panel_rect.bottom - 20:
                continue

            item_rect = pygame.Rect(panel_rect.x + 15, item_y, item_width, item_height)

            # 아이템 추가
            self.upgrade_items.append(UpgradeItem(
                category=self.selected_category,
                upgrade_id=upgrade["id"],
                rect=item_rect,
                hover_progress=0.0
            ))

            # 현재 레벨/상태
            current_level = self.player_upgrades.get(upgrade["id"], 0)
            max_level = upgrade["max_level"]
            cost = self._get_upgrade_cost(upgrade, current_level)
            can_buy = self._can_purchase(upgrade, current_level)
            is_maxed = current_level >= max_level and not upgrade.get("consumable")

            # 호버 진행도
            hover_progress = 0.0
            for item in self.upgrade_items:
                if item.upgrade_id == upgrade["id"]:
                    hover_progress = item.hover_progress
                    break

            # 구매 성공 효과
            is_just_purchased = (self.purchase_success_id == upgrade["id"])

            # 아이템 확장 효과 (호버 시 확대)
            expand = int(hover_progress * 8)
            draw_rect = item_rect.inflate(expand, expand // 2)

            # 아이템 배경 (통일된 색상)
            item_surf = pygame.Surface((draw_rect.width, draw_rect.height), pygame.SRCALPHA)

            # 구매 성공 시 골드 글로우
            if is_just_purchased:
                glow_alpha = int(100 * self.purchase_flash)
                item_surf.fill((*config.STATE_COLORS["GOLD"], glow_alpha))
                border_color = config.STATE_COLORS["GOLD"]
                name_color = config.STATE_COLORS["GOLD"]
                border_width = 3
            elif is_maxed:
                item_surf.fill((*config.STATE_COLORS["SUCCESS_DIM"], 200))
                border_color = config.STATE_COLORS["SUCCESS"]
                name_color = config.STATE_COLORS["SUCCESS"]
                border_width = 2
            elif hover_progress > 0 and can_buy:
                # 호버 시 밝아지는 효과
                brightness = int(40 + 40 * hover_progress)
                alpha = int(180 + 60 * hover_progress)
                item_surf.fill((brightness, brightness, brightness + 10, alpha))
                border_color = header_color
                name_color = config.TEXT_LEVELS["PRIMARY"]
                border_width = 2
            elif hover_progress > 0 and not can_buy:
                # 구매 불가 호버 - 빨간색 힌트
                item_surf.fill((*config.LOCKED_COLORS["BG"], 200))
                border_color = config.STATE_COLORS["DANGER"]
                name_color = config.LOCKED_COLORS["TEXT"]
                border_width = 2
            elif not can_buy:
                item_surf.fill((*config.LOCKED_COLORS["BG"], 160))
                border_color = config.LOCKED_COLORS["BORDER"]
                name_color = config.LOCKED_COLORS["TEXT"]
                border_width = 1
            else:
                item_surf.fill(config.UI_COLORS["CARD_BG"])
                border_color = config.UI_COLORS["PANEL_BORDER"]
                name_color = config.TEXT_LEVELS["SECONDARY"]
                border_width = 1

            screen.blit(item_surf, draw_rect.topleft)
            pygame.draw.rect(screen, border_color, draw_rect, border_width, border_radius=10)

            # ===== 카드 내부 레이아웃 (좌측: 정보, 우측: 비용/상태) =====
            left_margin = 14
            right_section_width = 110  # 우측 비용/상태 영역

            # 업그레이드 이름 (좌측 상단)
            name_text = render_text_with_emoji(upgrade["name"], self.fonts["medium"], name_color, "MEDIUM")
            screen.blit(name_text, (draw_rect.x + left_margin, draw_rect.y + 8))

            # 설명 (Light 폰트 - 가독성 향상)
            desc_color = config.TEXT_LEVELS["TERTIARY"] if (can_buy or is_maxed) else config.LOCKED_COLORS["TEXT"]
            desc_font = self.fonts.get("light_small", self.fonts["small"])
            desc_text = desc_font.render(upgrade["desc"], True, desc_color)
            screen.blit(desc_text, (draw_rect.x + left_margin, draw_rect.y + 32))

            # 레벨 진행 바 또는 상태 (하단 좌측)
            if not upgrade.get("one_time") and not upgrade.get("consumable"):
                bar_x = draw_rect.x + left_margin
                bar_y = draw_rect.y + 56
                bar_width = 140
                bar_height = 6

                # 진행 바 배경
                pygame.draw.rect(screen, config.BG_LEVELS["PANEL"],
                               (bar_x, bar_y, bar_width, bar_height), border_radius=3)

                # 진행 바 채우기
                progress = current_level / max_level
                if progress > 0:
                    fill_color = config.STATE_COLORS["SUCCESS"] if is_maxed else header_color
                    pygame.draw.rect(screen, fill_color,
                                   (bar_x, bar_y, int(bar_width * progress), bar_height), border_radius=3)

                # 레벨 텍스트 (진행 바 우측)
                level_text = self.fonts["small"].render(f"Lv.{current_level}/{max_level}", True,
                                                        config.TEXT_LEVELS["SECONDARY"])
                screen.blit(level_text, (bar_x + bar_width + 8, bar_y - 3))

            elif upgrade.get("one_time"):
                status_y = draw_rect.y + 54
                if current_level > 0:
                    # OWNED 뱃지
                    owned_surf = pygame.Surface((60, 18), pygame.SRCALPHA)
                    owned_surf.fill((*config.STATE_COLORS["SUCCESS_DIM"], 180))
                    screen.blit(owned_surf, (draw_rect.x + left_margin, status_y))
                    pygame.draw.rect(screen, config.STATE_COLORS["SUCCESS"],
                                   (draw_rect.x + left_margin, status_y, 60, 18), 1, border_radius=4)
                    owned_text = self.fonts["small"].render("OWNED", True, config.STATE_COLORS["SUCCESS"])
                    screen.blit(owned_text, (draw_rect.x + left_margin + 8, status_y + 2))
                else:
                    avail_text = self.fonts["small"].render("One-time unlock", True, config.TEXT_LEVELS["TERTIARY"])
                    screen.blit(avail_text, (draw_rect.x + left_margin, status_y))

            # ===== 우측 영역: 비용 또는 MAX 뱃지 =====
            right_x = draw_rect.right - right_section_width

            if is_maxed and not upgrade.get("consumable"):
                # MAX 뱃지 (중앙 정렬)
                badge_w, badge_h = 55, 24
                badge_x = right_x + (right_section_width - badge_w) // 2
                badge_y = draw_rect.y + (draw_rect.height - badge_h) // 2

                badge_surf = pygame.Surface((badge_w, badge_h), pygame.SRCALPHA)
                badge_surf.fill((*config.STATE_COLORS["SUCCESS_DIM"], 200))
                screen.blit(badge_surf, (badge_x, badge_y))
                pygame.draw.rect(screen, config.STATE_COLORS["SUCCESS"],
                               (badge_x, badge_y, badge_w, badge_h), 2, border_radius=6)
                max_text = self.fonts["medium"].render("MAX", True, config.STATE_COLORS["SUCCESS"])
                screen.blit(max_text, max_text.get_rect(center=(badge_x + badge_w // 2, badge_y + badge_h // 2)))

            else:
                # 비용 표시 (우측 중앙)
                cost_center_x = right_x + right_section_width // 2
                cost_y = draw_rect.y + 18

                # 코인 아이콘
                coin_color = config.STATE_COLORS["GOLD"] if can_buy else config.LOCKED_COLORS["ICON"]
                pygame.draw.circle(screen, coin_color, (cost_center_x - 30, cost_y + 5), 8)
                pygame.draw.circle(screen, (0, 0, 0), (cost_center_x - 30, cost_y + 5), 8, 1)

                # 비용 숫자
                cost_color = config.STATE_COLORS["GOLD"] if can_buy else config.STATE_COLORS["DANGER"]
                cost_text = self.fonts["medium"].render(f"{cost:,}", True, cost_color)
                screen.blit(cost_text, (cost_center_x - 18, cost_y - 2))

                # 레벨당 효과 (비용 아래 - Light 폰트)
                if "per_level" in upgrade:
                    effect_font = self.fonts.get("light_small", self.fonts["small"])
                    effect_text = effect_font.render(upgrade["per_level"], True, header_color)
                    effect_x = cost_center_x - effect_text.get_width() // 2
                    screen.blit(effect_text, (effect_x, cost_y + 24))

            # 클릭 가능 표시 (호버 + 구매 가능)
            if hover_progress > 0.5 and can_buy and not is_maxed:
                click_hint = self.fonts["small"].render("▶ BUY", True, header_color)
                click_hint.set_alpha(int(220 * hover_progress))
                hint_x = draw_rect.right - right_section_width + (right_section_width - click_hint.get_width()) // 2
                screen.blit(click_hint, (hint_x, draw_rect.bottom - 16))

        # 스크롤바
        if self.max_scroll > 0:
            self.ui_manager.render_scrollbar(
                screen, panel_rect, self.scroll_offset, self.max_scroll,
                visible_height, total_content_height
            )

    def handle_event(self, event: pygame.event.Event):
        """이벤트 처리"""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = event.pos

            # 탭 클릭
            for tab_id, rect in self.tab_rects.items():
                if rect.collidepoint(mouse_pos):
                    self.selected_category = tab_id
                    self.scroll_offset = 0
                    self.sound_manager.play_sfx("click")
                    return

            # 업그레이드 클릭
            for item in self.upgrade_items:
                if item.rect.collidepoint(mouse_pos):
                    self._purchase_upgrade(item.upgrade_id)
                    return

            # 뒤로가기 버튼
            if self.back_rect and self.back_rect.collidepoint(mouse_pos):
                self._on_back()
                return

        elif event.type == pygame.MOUSEWHEEL:
            self.scroll_offset = max(0, min(self.max_scroll, self.scroll_offset - event.y * 40))

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._on_back()
                return

            cat_keys = {
                pygame.K_1: "stats", pygame.K_2: "weapon_basic",
                pygame.K_3: "elemental", pygame.K_4: "defense",
                pygame.K_5: "support", pygame.K_6: "utility",
                pygame.K_7: "advanced",
            }
            if event.key in cat_keys:
                self.selected_category = cat_keys[event.key]
                self.scroll_offset = 0
                self.sound_manager.play_sfx("click")

    def _purchase_upgrade(self, upgrade_id: str):
        """업그레이드 구매"""
        upgrade_data = None
        for cat_data in UPGRADE_CATEGORIES.values():
            for upgrade in cat_data["upgrades"]:
                if upgrade["id"] == upgrade_id:
                    upgrade_data = upgrade
                    break
            if upgrade_data:
                break

        if not upgrade_data:
            return

        current_level = self.player_upgrades.get(upgrade_id, 0)

        if not self._can_purchase(upgrade_data, current_level):
            self.sound_manager.play_sfx("error")
            self.purchase_fail_time = 1.0  # 구매 실패 시각 효과
            return

        cost = self._get_upgrade_cost(upgrade_data, current_level)
        self.credits -= cost
        self.player_upgrades[upgrade_id] = current_level + 1

        self.engine.shared_state['global_score'] = self.credits
        self.engine.shared_state['player_upgrades'] = self.player_upgrades

        self.purchase_flash = 1.0
        self.purchase_success_id = upgrade_id  # 구매 성공한 업그레이드 ID 저장
        self.sound_manager.play_sfx("level_up")
        print(f"INFO: Purchased {upgrade_id} (Level {current_level + 1})")

    def _on_back(self):
        """뒤로가기"""
        self.engine.shared_state['global_score'] = self.credits
        self.engine.shared_state['player_upgrades'] = self.player_upgrades
        self.engine.save_shared_state()
        self.request_pop_mode()

    def on_enter(self):
        super().on_enter()
        if self.custom_cursor:
            self._enable_custom_cursor()

    def on_exit(self):
        self.engine.shared_state['global_score'] = self.credits
        self.engine.shared_state['player_upgrades'] = self.player_upgrades
        self.engine.save_shared_state()
        self._disable_custom_cursor()
        super().on_exit()


print("INFO: workshop_mode.py loaded (Unified Modern UI)")
