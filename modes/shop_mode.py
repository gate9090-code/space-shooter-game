# modes/shop_mode.py
"""
ShopMode - 상점 모드 (Unified Modern UI)
소모품 아이템 구매

카테고리:
- 수리: HP 회복 아이템
- 공격: 폭탄, 미사일 등
- 방어: 쉴드, 보호막
- 특수: 시간정지, 코인부스터 등
- 생존: 추가 생명
"""

import pygame
import math
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass

import config
from modes.base_mode import GameMode, ModeConfig
from ui_render import render_text_with_emoji
from ui_components import UILayoutManager, TabData, TabState, UnifiedParticleSystem


# =============================================================================
# 상점 아이템 카테고리 정의 (통일된 색상 사용)
# =============================================================================
SHOP_CATEGORIES = {
    "repair": {
        "name": "Repair",
        "icon": "🔧",
        "color": config.CATEGORY_COLORS["REPAIR"],
        "items": [
            {"id": "REPAIR_KIT_50", "name": "🔧 Repair Kit", "desc": "Restore 50% HP at battle start", "cost": 200, "max_stock": 5},
            {"id": "REPAIR_KIT_FULL", "name": "🛠️ Full Repair", "desc": "Restore 100% HP at battle start", "cost": 350, "max_stock": 3},
        ]
    },
    "attack": {
        "name": "Attack",
        "icon": "💣",
        "color": config.CATEGORY_COLORS["ATTACK"],
        "items": [
            {"id": "MEGA_BOMB", "name": "💣 Mega Bomb", "desc": "Damage all enemies on screen (1 use)", "cost": 500, "max_stock": 3},
            {"id": "HOMING_MISSILES", "name": "🚀 Homing Missiles x3", "desc": "3 guided missiles that track enemies", "cost": 250, "max_stock": 5},
            {"id": "EMP_GRENADE", "name": "⚡ EMP Grenade", "desc": "Stun all enemies for 3 seconds", "cost": 350, "max_stock": 3},
        ]
    },
    "defense": {
        "name": "Defense",
        "icon": "🛡️",
        "color": config.CATEGORY_COLORS["DEFENSE"],
        "items": [
            {"id": "EMERGENCY_SHIELD", "name": "🛡️ Emergency Shield", "desc": "Nullify next hit (1 time)", "cost": 300, "max_stock": 3},
            {"id": "SHIELD_GENERATOR", "name": "🔰 Shield Generator", "desc": "+50 shield for 30 seconds", "cost": 400, "max_stock": 3},
        ]
    },
    "special": {
        "name": "Special",
        "icon": "✨",
        "color": config.CATEGORY_COLORS["SPECIAL"],
        "items": [
            {"id": "TIME_FREEZE", "name": "⏰ Time Freeze", "desc": "Stop time for 5 seconds (1 use)", "cost": 600, "max_stock": 2},
            {"id": "COIN_DOUBLER", "name": "💰 Coin Doubler", "desc": "Double coins in next battle", "cost": 400, "max_stock": 3},
            {"id": "LUCKY_CHARM", "name": "🍀 Lucky Charm", "desc": "+50% drop rate in next battle", "cost": 300, "max_stock": 3},
        ]
    },
    "survival": {
        "name": "Survival",
        "icon": "❤️",
        "color": config.CATEGORY_COLORS["SURVIVAL"],
        "items": [
            {"id": "EXTRA_LIFE", "name": "❤️ Extra Life", "desc": "Revive once when killed (consumable)", "cost": 1500, "max_stock": 5},
        ]
    },
}


@dataclass
class ShopItem:
    """상점 아이템 데이터"""
    item_id: str
    rect: pygame.Rect
    hover_progress: float = 0.0


class ShopMode(GameMode):
    """
    상점 모드 - Unified Modern UI Design

    특징:
    - 통일된 UI 컴포넌트 사용
    - 상단 가로 탭 (5개 카테고리)
    - 중앙 콘텐츠 패널 (600px)
    - WCAG 대비율 준수 색상
    """

    def get_config(self) -> ModeConfig:
        return ModeConfig(
            mode_name="shop",
            perspective_enabled=False,
            background_type="static",
            parallax_enabled=False,
            meteor_enabled=False,
            show_wave_ui=False,
            show_skill_indicators=False,
            wave_system_enabled=False,
            spawn_system_enabled=False,
            asset_prefix="shop",
        )

    def init(self):
        """상점 모드 초기화"""
        config.GAME_MODE = "shop"

        # UI 매니저 초기화
        self.ui_manager = UILayoutManager(self.screen_size, self.fonts)

        # 플레이어 인벤토리 데이터
        self.inventory = self.engine.shared_state.get('player_inventory', {}).copy()
        self.credits = self.engine.shared_state.get('global_score', 0)

        # UI 상태
        self.selected_category = "repair"
        self.hovered_item: Optional[str] = None
        self.scroll_offset = 0
        self.max_scroll = 0

        # 배경 및 파티클
        self.background = self._create_background()
        self.particle_system = UnifiedParticleSystem(self.screen_size, 40, "shop")

        # 애니메이션 상태
        self.animation_time = 0.0
        self.purchase_flash = 0.0

        # 탭 데이터 생성
        self.tabs = [
            TabData(id=cat_id, name=cat["name"], icon=cat["icon"], color=cat["color"])
            for cat_id, cat in SHOP_CATEGORIES.items()
        ]
        self.tab_states: Dict[str, TabState] = {tab.id: TabState() for tab in self.tabs}
        self.tab_rects: Dict[str, pygame.Rect] = {}

        # 아이템 목록
        self.shop_items: List[ShopItem] = []

        # 버튼 상태
        self.back_rect = None
        self.back_hover = False

        # 커스텀 커서
        self.custom_cursor = self._load_base_cursor()

        print("INFO: ShopMode initialized (Unified UI)")

    def _create_background(self) -> pygame.Surface:
        """배경 생성 - facility_bg 이미지 사용"""
        # facility_bg 이미지 로드 시도
        bg_path = config.ASSET_DIR / "images" / "base" / "facilities" / "facility_bg.png"
        try:
            if bg_path.exists():
                bg = pygame.image.load(str(bg_path)).convert()
                return pygame.transform.smoothscale(bg, self.screen_size)
        except Exception as e:
            print(f"WARNING: Failed to load facility_bg for shop: {e}")

        # 폴백: 기본 그라데이션 배경
        bg = self.ui_manager.create_gradient_background(
            base_color=(15, 22, 28),
            variation=15
        )
        return bg

    def update(self, dt: float, current_time: float):
        """업데이트"""
        self.animation_time += dt
        self.purchase_flash = max(0, self.purchase_flash - dt * 3)

        # 파티클 업데이트
        self.particle_system.update(dt)

        # 마우스 위치
        mouse_pos = pygame.mouse.get_pos()
        self.hovered_item = None

        # 탭 호버 업데이트
        for tab_id, rect in self.tab_rects.items():
            state = self.tab_states[tab_id]
            if rect and rect.collidepoint(mouse_pos):
                state.hover_progress = min(1.0, state.hover_progress + dt * 6)
            else:
                state.hover_progress = max(0.0, state.hover_progress - dt * 4)

        # 아이템 호버 업데이트
        for item in self.shop_items:
            if item.rect.collidepoint(mouse_pos):
                self.hovered_item = item.item_id
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

        # 파티클
        self.particle_system.render(screen)

        # 타이틀
        glow_intensity = (math.sin(self.animation_time * 2.5) + 1) / 2
        self.ui_manager.render_title(screen, "S U P P L Y   S H O P",
                                     config.STATE_COLORS["SUCCESS"], glow_intensity)

        # 크레딧 표시
        self.ui_manager.render_credit_box(screen, self.credits, self.purchase_flash)

        # 카테고리 탭
        self.tab_rects = self.ui_manager.render_horizontal_tabs(
            screen, self.tabs, self.selected_category, self.tab_states, tab_width=110
        )

        # 아이템 목록
        self._render_items(screen)

        # 하단 버튼
        self.back_rect = self.ui_manager.render_back_button(screen, self.back_hover)

        # 키보드 힌트
        self.ui_manager.render_keyboard_hints(screen, "1-5 Categories  |  Scroll Mouse  |  ESC Back")

        # 커스텀 커서
        self._render_base_cursor(screen, self.custom_cursor)

    def _render_items(self, screen: pygame.Surface):
        """아이템 목록 렌더링 - Web Button 디자인 스타일"""
        cat_data = SHOP_CATEGORIES[self.selected_category]
        header_color = cat_data["color"]

        # 콘텐츠 패널
        panel_rect = self.ui_manager.render_content_panel(
            screen, cat_data["name"], header_color
        )

        # 아이템 목록
        items = cat_data["items"]
        self.shop_items.clear()

        layout = config.UI_LAYOUT
        item_height = 100  # 높이 증가 (더 큰 아이콘 박스를 위해)
        item_spacing = layout["ITEM_SPACING"]
        item_width = panel_rect.width - 30
        content_start_y = panel_rect.y + 42

        # 스크롤 계산
        total_content_height = len(items) * (item_height + item_spacing)
        visible_height = panel_rect.height - 65
        self.max_scroll = max(0, total_content_height - visible_height)
        self.scroll_offset = min(self.scroll_offset, self.max_scroll)

        for i, item in enumerate(items):
            item_y = content_start_y + i * (item_height + item_spacing) - self.scroll_offset

            # 화면 밖 스킵
            if item_y + item_height < content_start_y or item_y > panel_rect.bottom - 20:
                continue

            item_rect = pygame.Rect(panel_rect.x + 15, item_y, item_width, item_height)

            # 아이템 추가
            self.shop_items.append(ShopItem(item_id=item["id"], rect=item_rect))

            # 현재 보유량
            current_stock = self.inventory.get(item["id"], 0)
            max_stock = item.get("max_stock", 99)
            can_afford = self.credits >= item["cost"]
            can_buy = can_afford and current_stock < max_stock
            is_maxed = current_stock >= max_stock

            # 호버 진행도
            hover_progress = 0.0
            for si in self.shop_items:
                if si.item_id == item["id"]:
                    hover_progress = si.hover_progress
                    break

            # === Web Button 스타일: 좌측 컬러 아이콘 박스 + 우측 밝은 텍스트 영역 ===

            icon_box_width = 120  # 좌측 아이콘 박스 너비

            # 좌측 아이콘 박스 (카테고리 컬러)
            icon_rect = pygame.Rect(item_rect.x, item_rect.y, icon_box_width, item_height)
            if is_maxed:
                icon_color = config.STATE_COLORS["GOLD"]
            elif not can_buy:
                icon_color = (100, 100, 120)  # 회색
            else:
                icon_color = header_color  # 카테고리 색상

            # 호버 시 약간 밝아짐
            if hover_progress > 0 and can_buy:
                icon_color = tuple(min(255, int(c + 30 * hover_progress)) for c in icon_color)

            pygame.draw.rect(screen, icon_color, icon_rect, border_radius=8)

            # 아이콘 박스 내부에 큰 이모지 표시
            icon_emoji = cat_data["icon"]
            icon_font = self.fonts.get("xlarge", self.fonts["large"])  # 큰 폰트
            icon_surf = render_text_with_emoji(icon_emoji, icon_font, (255, 255, 255), "LARGE")
            icon_surf_rect = icon_surf.get_rect(center=(icon_rect.centerx, icon_rect.centery))
            screen.blit(icon_surf, icon_surf_rect)

            # 우측 텍스트 영역 (밝은 배경)
            text_rect = pygame.Rect(item_rect.x + icon_box_width, item_rect.y,
                                   item_rect.width - icon_box_width, item_height)

            # 텍스트 영역 배경 (밝은 회색)
            if is_maxed:
                text_bg_color = (235, 230, 220)  # 골드 톤
                name_color = config.STATE_COLORS["GOLD"]
            elif not can_buy:
                text_bg_color = (200, 200, 210)  # 어두운 회색
                name_color = (100, 100, 120)
            else:
                text_bg_color = (240, 242, 245)  # 밝은 회색
                name_color = (40, 45, 55)  # 어두운 텍스트

            pygame.draw.rect(screen, text_bg_color, text_rect, border_radius=8)

            # 전체 테두리 (얇게)
            border_color = icon_color if can_buy else (150, 150, 160)
            pygame.draw.rect(screen, border_color, item_rect, 2, border_radius=8)

            # 아이템 이름 (텍스트 영역 좌측)
            name_x = text_rect.x + 18
            name_y = text_rect.y + 12
            name_text = render_text_with_emoji(item["name"], self.fonts["medium"], name_color, "MEDIUM")
            screen.blit(name_text, (name_x, name_y))

            # 설명 (Light 폰트 - 가독성 향상)
            desc_color = (80, 90, 110) if (can_buy or is_maxed) else (120, 120, 130)
            desc_font = self.fonts.get("light_small", self.fonts["small"])
            desc_text = desc_font.render(item["desc"], True, desc_color)
            screen.blit(desc_text, (name_x, name_y + 28))

            # 보유량 표시
            stock_color = (60, 120, 200) if current_stock < max_stock else config.STATE_COLORS["GOLD"]
            stock_text = self.fonts["tiny"].render(f"Stock: {current_stock}/{max_stock}", True, stock_color)
            screen.blit(stock_text, (name_x, text_rect.bottom - 24))

            # 비용 (우측 하단)
            if not is_maxed:
                cost_x = text_rect.right - 110
                cost_y = text_rect.bottom - 26

                coin_color = config.STATE_COLORS["GOLD"] if can_afford else (160, 100, 100)
                pygame.draw.circle(screen, coin_color, (cost_x, cost_y + 8), 8)

                cost_color = config.STATE_COLORS["GOLD"] if can_afford else (180, 80, 80)
                cost_text = self.fonts["medium"].render(f"{item['cost']:,}", True, cost_color)
                screen.blit(cost_text, (cost_x + 16, cost_y))

            # MAX 뱃지 (우측 상단)
            if is_maxed:
                badge_x = text_rect.right - 70
                badge_y = text_rect.y + 12
                badge_surf = pygame.Surface((60, 26), pygame.SRCALPHA)
                badge_surf.fill((255, 215, 0, 220))  # 골드 배경
                screen.blit(badge_surf, (badge_x, badge_y))
                pygame.draw.rect(screen, (200, 160, 0), (badge_x, badge_y, 60, 26), 2, border_radius=6)
                max_text = self.fonts["medium"].render("MAX", True, (40, 40, 40))
                screen.blit(max_text, max_text.get_rect(center=(badge_x + 30, badge_y + 13)))

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

            # 아이템 클릭
            for item in self.shop_items:
                if item.rect.collidepoint(mouse_pos):
                    self._purchase_item(item.item_id)
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
                pygame.K_1: "repair", pygame.K_2: "attack",
                pygame.K_3: "defense", pygame.K_4: "special",
                pygame.K_5: "survival",
            }
            if event.key in cat_keys:
                self.selected_category = cat_keys[event.key]
                self.scroll_offset = 0
                self.sound_manager.play_sfx("click")

    def _purchase_item(self, item_id: str):
        """아이템 구매"""
        item_data = None
        for cat_data in SHOP_CATEGORIES.values():
            for item in cat_data["items"]:
                if item["id"] == item_id:
                    item_data = item
                    break
            if item_data:
                break

        if not item_data:
            return

        current_stock = self.inventory.get(item_id, 0)
        max_stock = item_data.get("max_stock", 99)
        cost = item_data["cost"]

        if self.credits < cost:
            self.sound_manager.play_sfx("error")
            return

        if current_stock >= max_stock:
            self.sound_manager.play_sfx("error")
            return

        # 구매 처리
        self.credits -= cost
        self.inventory[item_id] = current_stock + 1

        self.engine.shared_state['global_score'] = self.credits
        self.engine.shared_state['player_inventory'] = self.inventory

        self.purchase_flash = 1.0
        self.sound_manager.play_sfx("level_up")
        print(f"INFO: Purchased {item_id} (Stock: {current_stock + 1})")

    def _on_back(self):
        """뒤로가기"""
        self.engine.shared_state['global_score'] = self.credits
        self.engine.shared_state['player_inventory'] = self.inventory
        self.engine.save_shared_state()
        self.request_pop_mode()

    def on_enter(self):
        super().on_enter()
        if self.custom_cursor:
            self._enable_custom_cursor()

    def on_exit(self):
        self.engine.shared_state['global_score'] = self.credits
        self.engine.shared_state['player_inventory'] = self.inventory
        self.engine.save_shared_state()
        self._disable_custom_cursor()
        super().on_exit()


print("INFO: shop_mode.py loaded (Unified Modern UI)")
