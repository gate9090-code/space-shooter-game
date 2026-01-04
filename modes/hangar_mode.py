# modes/hangar_mode.py
"""
HangarMode - 격납고 모드 (Gallery Style Design)
5개 함선을 대형 이미지로 한 화면에 전시

Design:
- 중앙 아크 배치: 5개 함선이 반원형으로 배열
- 대형 함선 이미지 (호버 시 확대 + 글로우)
- 호버 시 상세 스펙 툴팁 표시
- 선택된 함선은 강조 표시
- BaseHub 스타일의 세련된 비주얼
"""

import pygame
import math
import random
from typing import Dict, Optional, List, Tuple
from dataclasses import dataclass

import config
from modes.base_mode import GameMode, ModeConfig


# config.py에서 함선 정의 가져오기
SHIP_TYPES = config.SHIP_TYPES


# =============================================================================
# 색상 테마
# =============================================================================

HANGAR_COLORS = {
    "bg_dark": (8, 12, 24),
    "bg_panel": (15, 22, 38),
    "glow_cyan": (80, 180, 255),
    "glow_gold": (255, 200, 80),
    "text_primary": (240, 245, 255),
    "text_secondary": (160, 170, 190),
    "text_dim": (100, 110, 130),
    "equipped": (80, 255, 140),
    "locked": (80, 80, 100),
}


# =============================================================================
# 파티클 시스템
# =============================================================================

@dataclass
class HangarParticle:
    x: float
    y: float
    vx: float
    vy: float
    size: float
    alpha: float
    color: Tuple[int, int, int]
    life: float


class HangarParticleSystem:
    """우주 배경 파티클"""

    def __init__(self, screen_size: Tuple[int, int], count: int = 50):
        self.screen_size = screen_size
        self.particles: List[HangarParticle] = []
        self.max_count = count

        for _ in range(count):
            self._spawn()

    def _spawn(self, y: float = None):
        if y is None:
            y = random.uniform(0, self.screen_size[1])

        colors = [(60, 100, 180), (80, 140, 220), (100, 80, 200)]
        self.particles.append(HangarParticle(
            x=random.uniform(0, self.screen_size[0]),
            y=y,
            vx=random.uniform(-8, 8),
            vy=random.uniform(-15, -5),
            size=random.uniform(1, 2.5),
            alpha=random.uniform(40, 100),
            color=random.choice(colors),
            life=random.uniform(5, 12)
        ))

    def update(self, dt: float):
        for p in self.particles[:]:
            p.x += p.vx * dt
            p.y += p.vy * dt
            p.life -= dt

            if p.life <= 0 or p.y < -10:
                self.particles.remove(p)
                if len(self.particles) < self.max_count:
                    self._spawn(self.screen_size[1] + 10)

    def draw(self, screen: pygame.Surface):
        for p in self.particles:
            alpha = int(p.alpha * min(1, p.life / 3))
            if alpha > 5:
                surf = pygame.Surface((6, 6), pygame.SRCALPHA)
                pygame.draw.circle(surf, (*p.color, alpha), (3, 3), int(p.size))
                screen.blit(surf, (int(p.x - 3), int(p.y - 3)))


# =============================================================================
# 함선 슬롯 데이터
# =============================================================================

@dataclass
class ShipSlot:
    """함선 슬롯 정보"""
    ship_id: str
    base_x: float
    base_y: float
    base_scale: float
    angle: float  # 배치 각도 (라디안)
    hover_progress: float = 0.0
    rect: pygame.Rect = None


class HangarMode(GameMode):
    """
    격납고 모드 - Gallery Style Design

    특징:
    - 5개 함선을 반원형으로 대형 배치
    - 호버 시 확대 + 상세 스펙 툴팁
    - BaseHub 스타일 세련된 비주얼
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

        # 플레이어 데이터
        self.owned_ships = self.engine.shared_state.get('owned_ships', ['FIGHTER'])
        self.selected_ship = self.engine.shared_state.get('current_ship', 'FIGHTER')
        self.credits = self.engine.shared_state.get('global_score', 0)

        # 배경 및 파티클
        self.background = self._create_background()
        self.particle_system = HangarParticleSystem(self.screen_size, 60)

        # 함선 이미지 로드
        self.ship_images: Dict[str, pygame.Surface] = {}
        self._load_ship_images()

        # 함선 슬롯 생성
        self.ship_slots: List[ShipSlot] = []
        self._create_ship_slots()

        # 호버/선택 상태
        self.hovered_ship: Optional[str] = None
        self.animation_time: float = 0.0

        # 버튼 상태
        self.back_rect: Optional[pygame.Rect] = None
        self.back_hover: bool = False
        self.equip_rect: Optional[pygame.Rect] = None
        self.equip_hover: bool = False

        print("INFO: HangarMode initialized (Gallery Style)")

    def _create_background(self) -> pygame.Surface:
        """그라데이션 우주 배경 생성"""
        bg = pygame.Surface(self.screen_size)

        # 수직 그라데이션
        for y in range(self.screen_size[1]):
            ratio = y / self.screen_size[1]
            color = (
                int(8 + 15 * ratio),
                int(12 + 18 * ratio),
                int(24 + 30 * ratio)
            )
            pygame.draw.line(bg, color, (0, y), (self.screen_size[0], y))

        # 중앙 비네트 효과
        vignette = pygame.Surface(self.screen_size, pygame.SRCALPHA)
        center_x, center_y = self.screen_size[0] // 2, self.screen_size[1] // 2
        max_radius = max(self.screen_size) * 0.8

        for r in range(int(max_radius), 0, -20):
            alpha = int(30 * (1 - r / max_radius))
            pygame.draw.circle(vignette, (20, 40, 80, alpha), (center_x, center_y), r)

        bg.blit(vignette, (0, 0))
        return bg

    def _load_ship_images(self):
        """함선 이미지 로드"""
        ships_dir = config.ASSET_DIR / "images" / "gameplay" / "player"
        for ship_id, ship_data in config.SHIP_TYPES.items():
            image_name = ship_data.get("image", f"{ship_id.lower()}_front.png")
            image_path = ships_dir / image_name
            try:
                if image_path.exists():
                    img = pygame.image.load(str(image_path)).convert_alpha()
                    self.ship_images[ship_id] = img
                    print(f"INFO: Loaded ship image: {image_name}")
                else:
                    print(f"WARNING: Ship image not found: {image_path}")
            except Exception as e:
                print(f"WARNING: Failed to load ship image {image_name}: {e}")

    def _create_ship_slots(self):
        """함선 슬롯 배치 - 반원형 아크"""
        ship_ids = list(SHIP_TYPES.keys())
        num_ships = len(ship_ids)

        screen_w, screen_h = self.screen_size

        # 아크 중심과 반경
        arc_center_x = screen_w // 2
        arc_center_y = screen_h * 0.95  # 화면 하단에서 올라오는 느낌
        arc_radius = screen_h * 0.65

        # 각도 범위 (좌측에서 우측으로)
        start_angle = math.radians(160)  # 좌측
        end_angle = math.radians(20)     # 우측
        angle_range = start_angle - end_angle

        for i, ship_id in enumerate(ship_ids):
            # 균등 배치
            t = i / (num_ships - 1) if num_ships > 1 else 0.5
            angle = start_angle - t * angle_range

            # 위치 계산
            x = arc_center_x + arc_radius * math.cos(angle)
            y = arc_center_y - arc_radius * math.sin(angle) * 0.5  # y축 압축

            # 중앙일수록 크게, 양끝일수록 작게
            center_factor = 1 - abs(t - 0.5) * 2  # 0~1 (중앙이 1)
            base_scale = 0.22 + center_factor * 0.12  # 0.22 ~ 0.34

            self.ship_slots.append(ShipSlot(
                ship_id=ship_id,
                base_x=x,
                base_y=y,
                base_scale=base_scale,
                angle=angle
            ))

    def _get_ship_color(self, ship_id: str) -> Tuple[int, int, int]:
        """함선 ID에 따른 색상"""
        ship_data = SHIP_TYPES.get(ship_id, {})
        return ship_data.get("color", (100, 150, 255))

    def update(self, dt: float, current_time: float):
        """업데이트"""
        self.animation_time += dt

        # 파티클 업데이트
        self.particle_system.update(dt)

        # 마우스 위치
        mouse_pos = pygame.mouse.get_pos()

        # 호버 상태 업데이트
        self.hovered_ship = None
        for slot in self.ship_slots:
            if slot.rect and slot.rect.collidepoint(mouse_pos):
                self.hovered_ship = slot.ship_id
                slot.hover_progress = min(1.0, slot.hover_progress + dt * 5)
            else:
                slot.hover_progress = max(0.0, slot.hover_progress - dt * 3)

        # 버튼 호버
        if self.back_rect:
            self.back_hover = self.back_rect.collidepoint(mouse_pos)
        if self.equip_rect:
            self.equip_hover = self.equip_rect.collidepoint(mouse_pos)

    def render(self, screen: pygame.Surface):
        """렌더링"""
        # 배경
        screen.blit(self.background, (0, 0))

        # 파티클
        self.particle_system.draw(screen)

        # 타이틀
        self._render_title(screen)

        # 크레딧
        self._render_credits(screen)

        # 함선들 렌더링 (뒤에서 앞으로)
        sorted_slots = sorted(self.ship_slots, key=lambda s: s.base_y)
        for slot in sorted_slots:
            self._render_ship_slot(screen, slot)

        # 호버된 함선의 상세 정보
        if self.hovered_ship:
            self._render_ship_tooltip(screen, self.hovered_ship)

        # 버튼
        self._render_buttons(screen)

        # 키보드 힌트
        self._render_keyboard_hints(screen)

    def _render_title(self, screen: pygame.Surface):
        """타이틀 렌더링"""
        title_font = self.fonts.get("large", self.fonts["medium"])

        # 글로우 효과
        glow_intensity = (math.sin(self.animation_time * 2) + 1) / 2
        glow_color = (
            int(80 + 40 * glow_intensity),
            int(160 + 40 * glow_intensity),
            255
        )

        title_text = "H A N G A R"

        # 글로우
        glow_surf = title_font.render(title_text, True, glow_color)
        glow_surf.set_alpha(int(100 + 80 * glow_intensity))
        glow_rect = glow_surf.get_rect(centerx=self.screen_size[0] // 2, y=25)
        screen.blit(glow_surf, (glow_rect.x + 2, glow_rect.y + 2))

        # 메인 텍스트
        main_surf = title_font.render(title_text, True, HANGAR_COLORS["text_primary"])
        screen.blit(main_surf, glow_rect)

        # 서브타이틀
        sub_font = self.fonts.get("small", self.fonts["medium"])
        sub_text = f"SELECT YOUR SHIP  •  {len(self.owned_ships)}/{len(SHIP_TYPES)} OWNED"
        sub_surf = sub_font.render(sub_text, True, HANGAR_COLORS["text_secondary"])
        screen.blit(sub_surf, sub_surf.get_rect(centerx=self.screen_size[0] // 2, y=65))

    def _render_credits(self, screen: pygame.Surface):
        """크레딧 표시"""
        credit_font = self.fonts.get("medium", self.fonts["small"])
        credit_text = f"◆ {self.credits:,}"
        credit_surf = credit_font.render(credit_text, True, HANGAR_COLORS["glow_gold"])
        screen.blit(credit_surf, (self.screen_size[0] - credit_surf.get_width() - 30, 30))

    def _render_ship_slot(self, screen: pygame.Surface, slot: ShipSlot):
        """함선 슬롯 렌더링"""
        ship_id = slot.ship_id
        ship_data = SHIP_TYPES.get(ship_id, {})
        ship_color = self._get_ship_color(ship_id)

        is_owned = ship_id in self.owned_ships
        is_equipped = ship_id == self.selected_ship
        is_hovered = slot.hover_progress > 0.1

        # 호버/선택에 따른 스케일
        hover_scale = 1.0 + slot.hover_progress * 0.15
        final_scale = slot.base_scale * hover_scale

        # 플로팅 애니메이션
        float_offset = math.sin(self.animation_time * 1.5 + slot.angle * 2) * 8

        # 위치
        x = slot.base_x
        y = slot.base_y + float_offset

        # 함선 이미지 또는 폴백
        if ship_id in self.ship_images:
            img = self.ship_images[ship_id]

            # 스케일 계산
            target_height = int(self.screen_size[1] * final_scale)
            aspect = img.get_width() / img.get_height()
            target_width = int(target_height * aspect)

            scaled_img = pygame.transform.smoothscale(img, (target_width, target_height))

            # 미보유 시 어둡게
            if not is_owned:
                dark_surf = scaled_img.copy()
                dark_surf.fill((60, 60, 80), special_flags=pygame.BLEND_MULT)
                scaled_img = dark_surf

            # 글로우 효과 (호버 또는 장착됨)
            if is_hovered or is_equipped:
                glow_surf = pygame.Surface(
                    (target_width + 40, target_height + 40),
                    pygame.SRCALPHA
                )
                glow_color = HANGAR_COLORS["equipped"] if is_equipped else ship_color
                glow_alpha = int(60 + 40 * slot.hover_progress)

                # 글로우 원
                pygame.draw.ellipse(
                    glow_surf,
                    (*glow_color, glow_alpha),
                    (0, 10, target_width + 40, target_height + 20)
                )

                glow_rect = glow_surf.get_rect(center=(int(x), int(y)))
                screen.blit(glow_surf, glow_rect)

            # 함선 이미지
            img_rect = scaled_img.get_rect(center=(int(x), int(y)))
            screen.blit(scaled_img, img_rect)

            # 클릭 영역 저장
            slot.rect = img_rect.inflate(20, 20)
        else:
            # 폴백: 아이콘
            icon = ship_data.get("icon", "🚀")
            icon_font = self.fonts.get("huge", self.fonts["large"])
            icon_color = ship_color if is_owned else HANGAR_COLORS["locked"]
            icon_surf = icon_font.render(icon, True, icon_color)
            icon_rect = icon_surf.get_rect(center=(int(x), int(y)))
            screen.blit(icon_surf, icon_rect)
            slot.rect = icon_rect.inflate(40, 40)

        # 함선 이름 (하단)
        name_font = self.fonts.get("small", self.fonts["medium"])
        name = ship_data.get("name", ship_id)
        name_color = HANGAR_COLORS["text_primary"] if is_owned else HANGAR_COLORS["text_dim"]
        name_surf = name_font.render(name, True, name_color)
        name_rect = name_surf.get_rect(centerx=int(x), top=int(y + slot.base_scale * self.screen_size[1] * 0.5 + 10))
        screen.blit(name_surf, name_rect)

        # 장착됨 뱃지
        if is_equipped:
            badge_font = self.fonts.get("tiny", self.fonts["small"])
            badge_surf = badge_font.render("EQUIPPED", True, HANGAR_COLORS["equipped"])
            badge_rect = badge_surf.get_rect(centerx=int(x), top=name_rect.bottom + 5)
            screen.blit(badge_surf, badge_rect)

    def _render_ship_tooltip(self, screen: pygame.Surface, ship_id: str):
        """함선 상세 스펙 툴팁"""
        ship_data = SHIP_TYPES.get(ship_id, {})
        ship_color = self._get_ship_color(ship_id)
        is_owned = ship_id in self.owned_ships
        is_equipped = ship_id == self.selected_ship

        stats = ship_data.get("stats", {})

        # 툴팁 크기 및 위치
        tooltip_width = 320
        tooltip_height = 220

        # 화면 상단 중앙에 표시
        tooltip_x = (self.screen_size[0] - tooltip_width) // 2
        tooltip_y = 100

        # 배경
        tooltip_surf = pygame.Surface((tooltip_width, tooltip_height), pygame.SRCALPHA)
        tooltip_surf.fill((15, 22, 40, 230))

        # 테두리
        pygame.draw.rect(tooltip_surf, ship_color, (0, 0, tooltip_width, tooltip_height), 2, border_radius=12)

        # 상단 색상 바
        pygame.draw.rect(tooltip_surf, (*ship_color, 150), (0, 0, tooltip_width, 4))

        screen.blit(tooltip_surf, (tooltip_x, tooltip_y))

        # 함선 이름
        name_font = self.fonts.get("medium", self.fonts["small"])
        name = ship_data.get("name", ship_id)
        name_surf = name_font.render(name, True, ship_color)
        screen.blit(name_surf, (tooltip_x + 15, tooltip_y + 12))

        # 상태 뱃지
        if is_equipped:
            badge_text = "EQUIPPED"
            badge_color = HANGAR_COLORS["equipped"]
        elif is_owned:
            badge_text = "OWNED"
            badge_color = (100, 180, 255)
        else:
            cost = ship_data.get("cost", 0)
            badge_text = f"${cost:,}"
            badge_color = HANGAR_COLORS["glow_gold"]

        badge_font = self.fonts.get("small", self.fonts["medium"])
        badge_surf = badge_font.render(badge_text, True, badge_color)
        screen.blit(badge_surf, (tooltip_x + tooltip_width - badge_surf.get_width() - 15, tooltip_y + 15))

        # 설명
        desc_font = self.fonts.get("small", self.fonts["medium"])
        desc = ship_data.get("description", "")
        desc_surf = desc_font.render(desc, True, HANGAR_COLORS["text_secondary"])
        screen.blit(desc_surf, (tooltip_x + 15, tooltip_y + 42))

        # 구분선
        pygame.draw.line(screen, (*ship_color, 100),
                        (tooltip_x + 15, tooltip_y + 65),
                        (tooltip_x + tooltip_width - 15, tooltip_y + 65))

        # 스탯 바
        stat_labels = [
            ("HP", stats.get("hp_mult", 1.0), 2.0),
            ("SPEED", stats.get("speed_mult", 1.0), 1.5),
            ("DAMAGE", stats.get("damage_mult", 1.0), 2.0),
            ("RATE", 1.0 / stats.get("cooldown_mult", 1.0), 1.5),  # 쿨다운 역수
        ]

        bar_y = tooltip_y + 78
        bar_width = tooltip_width - 100
        bar_height = 14

        stat_font = self.fonts.get("tiny", self.fonts["small"])

        for i, (label, value, max_val) in enumerate(stat_labels):
            y = bar_y + i * 28

            # 라벨
            label_surf = stat_font.render(label, True, HANGAR_COLORS["text_secondary"])
            screen.blit(label_surf, (tooltip_x + 15, y))

            # 바 배경
            bar_rect = pygame.Rect(tooltip_x + 75, y + 2, bar_width, bar_height)
            pygame.draw.rect(screen, (30, 40, 60), bar_rect, border_radius=4)

            # 바 채우기
            fill_ratio = min(1.0, value / max_val)
            fill_width = int(bar_width * fill_ratio)
            fill_color = ship_color if is_owned else HANGAR_COLORS["locked"]
            pygame.draw.rect(screen, fill_color,
                           (bar_rect.x, bar_rect.y, fill_width, bar_height),
                           border_radius=4)

            # 값
            value_text = f"{value:.1f}x" if value != int(value) else f"{int(value)}x"
            value_surf = stat_font.render(value_text, True, HANGAR_COLORS["text_primary"])
            screen.blit(value_surf, (tooltip_x + tooltip_width - 40, y))

        # 어빌리티
        ability = ship_data.get("ability", {})
        if ability:
            ability_y = bar_y + len(stat_labels) * 28 + 8
            ability_name = ability.get("name", "")
            ability_font = self.fonts.get("small", self.fonts["medium"])
            ability_text = f"[E] {ability_name}"
            ability_surf = ability_font.render(ability_text, True, ship_color)
            screen.blit(ability_surf, (tooltip_x + 15, ability_y))

        # 클릭 힌트
        if is_owned and not is_equipped:
            hint_font = self.fonts.get("tiny", self.fonts["small"])
            hint_surf = hint_font.render("Click to Equip", True, HANGAR_COLORS["glow_cyan"])
            screen.blit(hint_surf, hint_surf.get_rect(centerx=tooltip_x + tooltip_width // 2,
                                                       bottom=tooltip_y + tooltip_height - 10))

    def _render_buttons(self, screen: pygame.Surface):
        """버튼 렌더링"""
        # 뒤로가기 버튼 (좌측 하단)
        back_font = self.fonts.get("medium", self.fonts["small"])
        back_text = "◀ BACK"
        back_color = HANGAR_COLORS["glow_cyan"] if self.back_hover else HANGAR_COLORS["text_secondary"]
        back_surf = back_font.render(back_text, True, back_color)

        back_x = 40
        back_y = self.screen_size[1] - 50
        self.back_rect = pygame.Rect(back_x - 10, back_y - 5, back_surf.get_width() + 20, back_surf.get_height() + 10)

        if self.back_hover:
            pygame.draw.rect(screen, (*HANGAR_COLORS["glow_cyan"], 30), self.back_rect, border_radius=8)

        screen.blit(back_surf, (back_x, back_y))

        # 장착 버튼 (우측 하단) - 호버된 함선이 소유 중이고 미장착일 때
        self.equip_rect = None
        if self.hovered_ship:
            is_owned = self.hovered_ship in self.owned_ships
            is_equipped = self.hovered_ship == self.selected_ship

            if is_owned and not is_equipped:
                equip_text = "EQUIP ▶"
                equip_color = HANGAR_COLORS["equipped"] if self.equip_hover else HANGAR_COLORS["text_primary"]
                equip_surf = back_font.render(equip_text, True, equip_color)

                equip_x = self.screen_size[0] - equip_surf.get_width() - 40
                equip_y = self.screen_size[1] - 50
                self.equip_rect = pygame.Rect(equip_x - 10, equip_y - 5,
                                             equip_surf.get_width() + 20, equip_surf.get_height() + 10)

                if self.equip_hover:
                    pygame.draw.rect(screen, (*HANGAR_COLORS["equipped"], 40), self.equip_rect, border_radius=8)

                pygame.draw.rect(screen, HANGAR_COLORS["equipped"], self.equip_rect, 2, border_radius=8)
                screen.blit(equip_surf, (equip_x, equip_y))

    def _render_keyboard_hints(self, screen: pygame.Surface):
        """키보드 힌트"""
        hint_font = self.fonts.get("tiny", self.fonts["small"])
        hints = "1-5 Select  •  Enter Equip  •  ESC Back"
        hint_surf = hint_font.render(hints, True, HANGAR_COLORS["text_dim"])
        hint_rect = hint_surf.get_rect(centerx=self.screen_size[0] // 2,
                                       bottom=self.screen_size[1] - 15)
        screen.blit(hint_surf, hint_rect)

    def handle_event(self, event: pygame.event.Event):
        """이벤트 처리"""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = event.pos

            # 함선 클릭 - 장착
            for slot in self.ship_slots:
                if slot.rect and slot.rect.collidepoint(mouse_pos):
                    self._try_equip_ship(slot.ship_id)
                    return

            # 뒤로가기 버튼
            if self.back_rect and self.back_rect.collidepoint(mouse_pos):
                self._on_back()
                return

            # 장착 버튼
            if self.equip_rect and self.equip_rect.collidepoint(mouse_pos):
                if self.hovered_ship:
                    self._try_equip_ship(self.hovered_ship)
                return

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._on_back()
                return

            if event.key == pygame.K_RETURN:
                if self.hovered_ship:
                    self._try_equip_ship(self.hovered_ship)
                return

            # 숫자 키로 함선 선택 및 장착
            ship_list = list(SHIP_TYPES.keys())
            key_map = {pygame.K_1: 0, pygame.K_2: 1, pygame.K_3: 2, pygame.K_4: 3, pygame.K_5: 4}
            if event.key in key_map:
                idx = key_map[event.key]
                if idx < len(ship_list):
                    self._try_equip_ship(ship_list[idx])

    def _try_equip_ship(self, ship_id: str):
        """함선 장착 시도"""
        if ship_id not in self.owned_ships:
            # 미보유 - 구매 시도
            cost = SHIP_TYPES.get(ship_id, {}).get("cost", 0)
            if self.credits >= cost:
                self.credits -= cost
                self.owned_ships.append(ship_id)
                self.engine.shared_state['global_score'] = self.credits
                self.engine.shared_state['owned_ships'] = self.owned_ships
                self.sound_manager.play_sfx("level_up")
                print(f"INFO: Purchased ship: {ship_id}")
            else:
                self.sound_manager.play_sfx("error")
            return

        if ship_id == self.selected_ship:
            # 이미 장착됨
            return

        # 장착
        self.selected_ship = ship_id
        self.engine.shared_state['current_ship'] = self.selected_ship
        self.sound_manager.play_sfx("level_up")
        print(f"INFO: Equipped ship: {ship_id}")

    def _on_back(self):
        """뒤로가기"""
        self.engine.shared_state['global_score'] = self.credits
        self.engine.shared_state['owned_ships'] = self.owned_ships
        self.engine.shared_state['current_ship'] = self.selected_ship
        self.engine.save_shared_state()
        self.request_pop_mode()

    def on_enter(self):
        super().on_enter()

    def on_exit(self):
        self.engine.shared_state['global_score'] = self.credits
        self.engine.shared_state['owned_ships'] = self.owned_ships
        self.engine.shared_state['current_ship'] = self.selected_ship
        self.engine.save_shared_state()
        super().on_exit()


print("INFO: hangar_mode.py loaded (Gallery Style)")
