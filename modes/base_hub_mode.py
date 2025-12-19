# modes/base_hub_mode.py
"""
BaseHubMode - 기지 허브 모드 (Carrier Label Design)
전투 사이에 함선 교체, 업그레이드, 미션 선택을 수행하는 기지 화면

Design: 중앙 모함 + 연결선 라벨 + 미니멀 상태바
- 중앙: 우주모함 이미지 (플로팅 애니메이션)
- 모함 위: 시설 라벨 (연결선으로 표시)
- 상단: 미니멀 상태바
- 우하단: 출격 버튼
"""

import pygame
import math
import random
import time
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from pathlib import Path

import config
from modes.base_mode import GameMode, ModeConfig
from systems.save_system import get_save_system


# =============================================================================
# 파티클 시스템
# =============================================================================

@dataclass
class Particle:
    """배경 파티클"""
    x: float
    y: float
    vx: float
    vy: float
    size: float
    alpha: float
    color: Tuple[int, int, int]
    life: float = 1.0
    max_life: float = 1.0


class ParticleSystem:
    """파티클 매니저"""

    def __init__(self, screen_size: Tuple[int, int], count: int = 30):
        self.screen_size = screen_size
        self.particles: List[Particle] = []
        self.max_particles = count

        for _ in range(count):
            self._spawn_particle()

    def _spawn_particle(self, x: float = None, y: float = None):
        if x is None:
            x = random.uniform(0, self.screen_size[0])
        if y is None:
            y = random.uniform(0, self.screen_size[1])

        color_choices = [
            (80, 120, 200),
            (100, 80, 180),
            (60, 140, 200),
        ]

        self.particles.append(Particle(
            x=x, y=y,
            vx=random.uniform(-10, 10),
            vy=random.uniform(-20, -5),
            size=random.uniform(1, 2),
            alpha=random.uniform(30, 80),
            color=random.choice(color_choices),
            life=random.uniform(4, 10),
            max_life=random.uniform(4, 10),
        ))

    def update(self, dt: float):
        for particle in self.particles[:]:
            particle.x += particle.vx * dt
            particle.y += particle.vy * dt
            particle.life -= dt
            particle.alpha = 80 * (particle.life / particle.max_life)

            if particle.life <= 0 or particle.y < -10:
                self.particles.remove(particle)
                if len(self.particles) < self.max_particles:
                    self._spawn_particle(
                        x=random.uniform(0, self.screen_size[0]),
                        y=self.screen_size[1] + 10
                    )

    def draw(self, screen: pygame.Surface):
        for particle in self.particles:
            if particle.alpha > 5:
                surf = pygame.Surface((8, 8), pygame.SRCALPHA)
                pygame.draw.circle(
                    surf,
                    (*particle.color, int(particle.alpha)),
                    (4, 4),
                    max(1, int(particle.size))
                )
                screen.blit(surf, (int(particle.x - 4), int(particle.y - 4)))


# =============================================================================
# 시설 라벨 데이터 (모함 위 표시용)
# =============================================================================

@dataclass
class FacilityLabel:
    """모함 이미지 위에 표시되는 시설 라벨"""
    name: str
    display_name: str
    description: str
    # 모함 이미지 기준 상대 위치 (0.0 ~ 1.0)
    rel_x: float
    rel_y: float
    # 라벨 방향 ("left", "right", "top", "bottom")
    direction: str
    color: Tuple[int, int, int]
    # 아이콘 (이모지 문자 또는 이미지)
    icon_char: str = "◆"
    icon_image: Optional[pygame.Surface] = None
    hover_progress: float = 0.0
    glow_phase: float = 0.0
    rect: Optional[pygame.Rect] = None
    clickable: bool = True


# =============================================================================
# 메인 클래스
# =============================================================================

class BaseHubMode(GameMode):
    """
    기지 허브 모드 - Carrier Label Design
    모함 이미지 위에 연결선으로 시설 라벨 표시
    """

    def get_config(self) -> ModeConfig:
        return ModeConfig(
            mode_name="base_hub",
            perspective_enabled=False,
            player_speed_multiplier=0.0,
            background_type="static",
            parallax_enabled=False,
            meteor_enabled=False,
            show_wave_ui=False,
            show_stage_ui=False,
            show_minimap=False,
            show_skill_indicators=False,
            wave_system_enabled=False,
            spawn_system_enabled=False,
            random_events_enabled=False,
            asset_prefix="base",
        )

    def init(self):
        """기지 허브 모드 초기화"""
        config.GAME_MODE = "base_hub"
        SCREEN_WIDTH, SCREEN_HEIGHT = self.screen_size

        # 새 게임 여부 확인
        self.is_new_game = self.engine.shared_state.get('is_new_game', False)
        self.show_opening = self.engine.shared_state.get('show_opening', False)
        self.opening_shown = False
        self.active_cutscene = None  # 오프닝 컷씬

        # 폰트는 base_mode에서 engine.fonts로 이미 설정됨
        # self.fonts = engine.fonts (base_mode.__init__에서 처리)

        # 게임 데이터
        self.game_data = {
            "credits": self.engine.shared_state.get('global_score', 0),
            "current_ship": self.engine.shared_state.get('current_ship', 'FIGHTER'),
            "current_act": self.engine.shared_state.get('current_act', 1),
            "current_mission": self.engine.shared_state.get('current_mission', 'act1_m1'),
            "completed_missions": self.engine.shared_state.get('completed_missions', []),
        }

        # 애니메이션 타이머
        self.animation_time = 0.0
        self.fade_alpha = 255

        # 배경
        self.background = self._create_gradient_background()
        self.particle_system = ParticleSystem(self.screen_size, count=25)

        # 우주모함 이미지
        self.carrier_image = self._load_carrier_image()
        self.carrier_rect: Optional[pygame.Rect] = None  # 모함 위치 저장

        # 시설 라벨 생성 (모함 위 연결선)
        self.facility_labels = self._create_facility_labels()
        self.hovered_label: Optional[str] = None

        # 출격 버튼 (모함 내부에 위치)
        self.launch_hover = False
        self.launch_glow = 0.0

        # 플레이 시간
        self.play_start_time = time.time()
        self.total_play_time = self.engine.shared_state.get('total_play_time', 0)

        # 새 게임 플래그 초기화
        if self.is_new_game:
            self.engine.shared_state['is_new_game'] = False

        print("INFO: BaseHubMode initialized (Unified Flow)")

    def _show_opening_cutscene(self):
        """게임 오프닝 컷씬 표시"""
        from objects import StoryBriefingEffect
        from mode_configs import config_story_dialogue

        # 1막 오프닝 대사 가져오기
        opening_data = config_story_dialogue.get_set_opening(1)
        if not opening_data:
            print("WARNING: No opening data found, skipping cutscene")
            self.opening_shown = True
            return

        # 배경 이미지 경로
        bg_path = config.ASSET_DIR / "images" / "backgrounds" / "bg_ruins.jpg"
        if not bg_path.exists():
            bg_path = config.ASSET_DIR / "images" / "backgrounds" / "bg_space.jpg"

        # 오프닝 브리핑 효과 생성
        briefing = StoryBriefingEffect(
            screen_size=self.screen_size,
            dialogue_data=opening_data.get("dialogues", []),
            background_path=bg_path,
            title=opening_data.get("title", "PROLOGUE"),
            location=opening_data.get("location", "MOTHERSHIP - ARK PRIME")
        )
        briefing.set_fonts(self.fonts)
        briefing.on_complete = self._on_opening_complete

        self.active_cutscene = briefing
        print("INFO: Showing game opening cutscene")

    def _on_opening_complete(self):
        """오프닝 컷씬 완료 콜백"""
        self.active_cutscene = None
        self.opening_shown = True
        print("INFO: Opening cutscene complete, entering BaseHub")

    def _create_gradient_background(self) -> pygame.Surface:
        """그라데이션 배경 생성"""
        surf = pygame.Surface(self.screen_size)
        for y in range(self.screen_size[1]):
            ratio = y / self.screen_size[1]
            r = int(8 + ratio * 12)
            g = int(12 + ratio * 18)
            b = int(28 + ratio * 25)
            pygame.draw.line(surf, (r, g, b), (0, y), (self.screen_size[0], y))
        return surf

    def _load_carrier_image(self) -> Optional[pygame.Surface]:
        """우주모함 이미지 로드"""
        bg_paths = [
            config.ASSET_DIR / "images" / "base" / "carrier_bg.png",
            config.ASSET_DIR / "images" / "base" / "basehub_bg_01.png",
            config.ASSET_DIR / "images" / "base" / "basehub_bg_02.png",
        ]

        for bg_path in bg_paths:
            try:
                if bg_path.exists():
                    return pygame.image.load(str(bg_path)).convert_alpha()
            except Exception:
                continue
        return None

    def _create_facility_labels(self) -> List[FacilityLabel]:
        """모함 위 시설 라벨 생성"""
        labels_data = [
            {
                "name": "hangar",
                "display_name": "HANGAR",
                "description": "Select Ship",
                "rel_x": 0.15,
                "rel_y": 0.50,
                "direction": "left",
                "color": (80, 140, 255),
                "icon_char": "✈",  # 비행기 아이콘
            },
            {
                "name": "workshop",
                "display_name": "WORKSHOP",
                "description": "Upgrade",
                "rel_x": 0.35,
                "rel_y": 0.30,
                "direction": "top",
                "color": (80, 220, 140),
                "icon_char": "⚙",  # 기어 아이콘
            },
            {
                "name": "shop",
                "display_name": "SUPPLY",
                "description": "Buy Items",
                "rel_x": 0.65,
                "rel_y": 0.30,
                "direction": "top",
                "color": (255, 180, 80),
                "icon_char": "★",  # 별 아이콘
            },
            {
                "name": "briefing",
                "display_name": "BRIEFING",
                "description": "Mission Info",
                "rel_x": 0.85,
                "rel_y": 0.50,
                "direction": "right",
                "color": (180, 120, 255),
                "icon_char": "◎",  # 타겟 아이콘
            },
        ]

        labels = []
        for data in labels_data:
            # 아이콘 이미지 로드 시도
            icon_image = self._load_facility_icon(data["name"])

            labels.append(FacilityLabel(
                name=data["name"],
                display_name=data["display_name"],
                description=data["description"],
                rel_x=data["rel_x"],
                rel_y=data["rel_y"],
                direction=data["direction"],
                color=data["color"],
                icon_char=data.get("icon_char", "◆"),
                icon_image=icon_image,
                glow_phase=random.uniform(0, math.pi * 2),
            ))
        return labels

    def _load_facility_icon(self, facility_name: str) -> Optional[pygame.Surface]:
        """시설 아이콘 이미지 로드"""
        icon_paths = [
            config.ASSET_DIR / "images" / "icons" / f"{facility_name}_icon.png",
            config.ASSET_DIR / "images" / "base" / f"{facility_name}_icon.png",
            config.ASSET_DIR / "icons" / f"{facility_name}.png",
        ]

        for icon_path in icon_paths:
            try:
                if icon_path.exists():
                    icon = pygame.image.load(str(icon_path)).convert_alpha()
                    # 24x24 크기로 조정
                    return pygame.transform.smoothscale(icon, (24, 24))
            except Exception as e:
                print(f"DEBUG: Icon load failed for {facility_name}: {e}")
                continue
        return None

    # =========================================================================
    # 업데이트
    # =========================================================================

    def update(self, dt: float, current_time: float):
        self.animation_time += dt

        # 새 게임 오프닝 처리
        if self.show_opening and not self.opening_shown and not self.active_cutscene:
            self._show_opening_cutscene()
            self.engine.shared_state['show_opening'] = False

        # 컷씬 활성화 중이면 컷씬만 업데이트
        if self.active_cutscene:
            self.active_cutscene.update(dt)
            return

        # 페이드 인
        if self.fade_alpha > 0:
            self.fade_alpha = max(0, self.fade_alpha - 400 * dt)

        # 파티클
        self.particle_system.update(dt)

        # 마우스 호버
        mouse_pos = pygame.mouse.get_pos()

        # 시설 라벨 호버
        self.hovered_label = None
        for label in self.facility_labels:
            if label.rect and label.rect.collidepoint(mouse_pos):
                self.hovered_label = label.name
                label.hover_progress = min(1.0, label.hover_progress + dt * 8)
            else:
                label.hover_progress = max(0.0, label.hover_progress - dt * 5)
            label.glow_phase += dt * 2.5

        # 출격 버튼 호버
        launch_rect = self._get_launch_button_rect()
        self.launch_hover = launch_rect.collidepoint(mouse_pos)
        if self.launch_hover:
            self.launch_glow = min(1.0, self.launch_glow + dt * 5)
        else:
            self.launch_glow = max(0.0, self.launch_glow - dt * 3)

    # =========================================================================
    # 렌더링
    # =========================================================================

    def render(self, screen: pygame.Surface):
        SCREEN_WIDTH, SCREEN_HEIGHT = self.screen_size

        # 1. 배경
        screen.blit(self.background, (0, 0))

        # 2. 파티클
        self.particle_system.draw(screen)

        # 3. 상단 상태바
        self._render_top_bar(screen)

        # 4. 중앙 모함 + 라벨
        self._render_carrier_with_labels(screen)

        # 5. 출격 버튼
        self._render_launch_button(screen)

        # 6. 호버 툴팁
        if self.hovered_label:
            self._render_tooltip(screen)

        # 7. 페이드 인
        if self.fade_alpha > 0:
            fade_surface = pygame.Surface(self.screen_size, pygame.SRCALPHA)
            fade_surface.fill((0, 0, 0, int(self.fade_alpha)))
            screen.blit(fade_surface, (0, 0))

        # 8. 오프닝 컷씬 (최상단에 렌더링)
        if self.active_cutscene:
            if hasattr(self.active_cutscene, 'render'):
                self.active_cutscene.render(screen)
            elif hasattr(self.active_cutscene, 'draw'):
                self.active_cutscene.draw(screen)

    def _render_top_bar(self, screen: pygame.Surface):
        """상단 미니멀 상태바"""
        SCREEN_WIDTH = self.screen_size[0]
        bar_height = 50

        # 반투명 배경
        bar_bg = pygame.Surface((SCREEN_WIDTH, bar_height), pygame.SRCALPHA)
        bar_bg.fill((10, 15, 30, 200))
        pygame.draw.line(bar_bg, (60, 100, 180, 150),
                        (0, bar_height - 1), (SCREEN_WIDTH, bar_height - 1), 1)
        screen.blit(bar_bg, (0, 0))

        # 타이틀 (중앙)
        title_text = self.fonts["large"].render("ECHO CARRIER", True, (180, 200, 240))
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, 25))
        screen.blit(title_text, title_rect)

        # 크레딧 (좌측)
        credits = self.game_data.get("credits", 0)
        credit_text = self.fonts["medium"].render(f"$ {credits:,}", True, (255, 215, 100))
        screen.blit(credit_text, (20, 15))

        # 미션 (우측)
        act = self.game_data.get("current_act", 1)
        episode = self.game_data.get("current_episode", 1)
        mission_text = self.fonts["medium"].render(f"ACT {act}-E{episode}", True, (255, 160, 100))
        mission_rect = mission_text.get_rect(right=SCREEN_WIDTH - 20, centery=25)
        screen.blit(mission_text, mission_rect)

    def _render_carrier_with_labels(self, screen: pygame.Surface):
        """모함 + 시설 라벨 렌더링"""
        SCREEN_WIDTH, SCREEN_HEIGHT = self.screen_size
        center_x = SCREEN_WIDTH // 2
        center_y = SCREEN_HEIGHT // 2

        # 플로팅 애니메이션
        float_offset = math.sin(self.animation_time * 1.0) * 5

        carrier_rect = None

        if self.carrier_image:
            # 크기 조정
            orig_w, orig_h = self.carrier_image.get_size()
            max_size = min(SCREEN_WIDTH * 0.6, SCREEN_HEIGHT * 0.5)
            scale = min(max_size / orig_w, max_size / orig_h)
            new_w = int(orig_w * scale)
            new_h = int(orig_h * scale)

            # 글로우 효과
            glow_alpha = int(20 + 15 * math.sin(self.animation_time * 1.5))
            glow_surf = pygame.Surface((new_w + 60, new_h + 60), pygame.SRCALPHA)
            pygame.draw.ellipse(glow_surf, (60, 100, 180, glow_alpha),
                              (0, 0, new_w + 60, new_h + 60))
            screen.blit(glow_surf, (center_x - (new_w + 60) // 2,
                                   int(center_y + float_offset) - (new_h + 60) // 2))

            # 모함 이미지
            scaled_carrier = pygame.transform.smoothscale(self.carrier_image, (new_w, new_h))
            carrier_rect = scaled_carrier.get_rect(center=(center_x, int(center_y + float_offset)))
            screen.blit(scaled_carrier, carrier_rect)
        else:
            # 플레이스홀더
            new_w, new_h = 400, 200
            carrier_rect = pygame.Rect(0, 0, new_w, new_h)
            carrier_rect.center = (center_x, int(center_y + float_offset))

            pygame.draw.rect(screen, (40, 60, 100), carrier_rect, border_radius=15)
            pygame.draw.rect(screen, (80, 120, 180), carrier_rect, 2, border_radius=15)

            text = self.fonts["large"].render("CARRIER", True, (150, 180, 220))
            text_rect = text.get_rect(center=carrier_rect.center)
            screen.blit(text, text_rect)

        # 모함 rect 저장 (출격 버튼 위치용)
        self.carrier_rect = carrier_rect

        # 시설 라벨 렌더링
        if carrier_rect:
            self._render_facility_labels(screen, carrier_rect)

    def _render_facility_labels(self, screen: pygame.Surface, carrier_rect: pygame.Rect):
        """모함 위 시설 라벨 렌더링 (아이콘 + 텍스트 레이아웃)"""
        for label in self.facility_labels:
            # 모함 위 포인트 위치
            point_x = carrier_rect.x + int(carrier_rect.width * label.rel_x)
            point_y = carrier_rect.y + int(carrier_rect.height * label.rel_y)

            hover = label.hover_progress
            glow = 0.5 + 0.5 * math.sin(label.glow_phase)

            # 라벨 박스 크기 (아이콘 공간 포함하여 넓힘)
            box_w = 130 + int(hover * 20)
            box_h = 50 + int(hover * 8)
            line_length = 50 + int(hover * 15)

            # 방향에 따른 라벨 위치
            if label.direction == "left":
                label_x = point_x - line_length - box_w
                label_y = point_y - box_h // 2
                line_end = (label_x + box_w, point_y)
            elif label.direction == "right":
                label_x = point_x + line_length
                label_y = point_y - box_h // 2
                line_end = (label_x, point_y)
            elif label.direction == "top":
                label_x = point_x - box_w // 2
                label_y = point_y - line_length - box_h
                line_end = (point_x, label_y + box_h)
            else:  # bottom
                label_x = point_x - box_w // 2
                label_y = point_y + line_length
                line_end = (point_x, label_y)

            # 클릭 영역 저장
            label.rect = pygame.Rect(label_x, label_y, box_w, box_h)

            # 연결선 (글로우)
            line_width = 2 + int(hover * 2)
            line_alpha = int(100 + glow * 50 + hover * 100)

            # 글로우 라인
            glow_surf = pygame.Surface(self.screen_size, pygame.SRCALPHA)
            pygame.draw.line(glow_surf, (*label.color, int(line_alpha * 0.4)),
                           (point_x, point_y), line_end, line_width + 4)
            screen.blit(glow_surf, (0, 0))

            # 메인 라인
            pygame.draw.line(screen, (*label.color, line_alpha),
                           (point_x, point_y), line_end, line_width)

            # 포인트 마커 (모함 위)
            marker_radius = 4 + int(hover * 2)
            pygame.draw.circle(screen, label.color, (point_x, point_y), marker_radius + 3)
            pygame.draw.circle(screen, (255, 255, 255), (point_x, point_y), marker_radius)

            # 라벨 박스 배경
            box_surf = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
            bg_alpha = int(180 + hover * 50)
            pygame.draw.rect(box_surf, (20, 30, 50, bg_alpha),
                           (0, 0, box_w, box_h), border_radius=8)

            # 테두리
            border_alpha = int(150 + hover * 105)
            pygame.draw.rect(box_surf, (*label.color, border_alpha),
                           (0, 0, box_w, box_h), 2, border_radius=8)

            # 호버 시 내부 글로우
            if hover > 0:
                inner_glow = pygame.Surface((box_w - 4, box_h - 4), pygame.SRCALPHA)
                pygame.draw.rect(inner_glow, (*label.color, int(hover * 40)),
                               (0, 0, box_w - 4, box_h - 4), border_radius=6)
                box_surf.blit(inner_glow, (2, 2))

            screen.blit(box_surf, (label_x, label_y))

            # === 아이콘 + 텍스트 레이아웃 ===
            icon_area_w = 36  # 아이콘 영역 폭
            text_area_x = label_x + icon_area_w + 4
            text_area_w = box_w - icon_area_w - 8

            # 1) 아이콘 영역 (왼쪽)
            icon_center_x = label_x + icon_area_w // 2 + 4
            icon_center_y = label_y + box_h // 2

            if label.icon_image:
                # 이미지 아이콘 있으면 사용
                icon_rect = label.icon_image.get_rect(center=(icon_center_x, icon_center_y))
                screen.blit(label.icon_image, icon_rect)
            else:
                # 없으면 원 배경 + 텍스트 아이콘
                icon_size = 28 + int(hover * 4)
                icon_bg = pygame.Surface((icon_size, icon_size), pygame.SRCALPHA)
                # 원형 배경
                pygame.draw.circle(icon_bg, (*label.color, int(60 + hover * 40)),
                                 (icon_size // 2, icon_size // 2), icon_size // 2)
                pygame.draw.circle(icon_bg, (*label.color, int(150 + hover * 80)),
                                 (icon_size // 2, icon_size // 2), icon_size // 2, 2)
                screen.blit(icon_bg, (icon_center_x - icon_size // 2, icon_center_y - icon_size // 2))

                # 아이콘 문자
                icon_font = pygame.font.Font(None, 22)
                icon_color = (255, 255, 255) if hover > 0.3 else (200, 220, 240)
                icon_text = icon_font.render(label.icon_char, True, icon_color)
                icon_text_rect = icon_text.get_rect(center=(icon_center_x, icon_center_y))
                screen.blit(icon_text, icon_text_rect)

            # 2) 텍스트 영역 (오른쪽) - 세로 중앙 정렬
            # 시설 이름
            name_color = (255, 255, 255) if hover > 0.3 else (200, 210, 230)
            name_text = self.fonts["medium"].render(label.display_name, True, name_color)
            name_rect = name_text.get_rect(
                left=text_area_x,
                centery=label_y + box_h // 2 - 8
            )
            screen.blit(name_text, name_rect)

            # 설명
            desc_color = label.color if hover > 0.3 else (140, 150, 170)
            desc_font = pygame.font.Font(None, 17)
            desc_text = desc_font.render(label.description, True, desc_color)
            desc_rect = desc_text.get_rect(
                left=text_area_x,
                centery=label_y + box_h // 2 + 12
            )
            screen.blit(desc_text, desc_rect)

    def _render_tooltip(self, screen: pygame.Surface):
        """호버 툴팁"""
        mouse_x, mouse_y = pygame.mouse.get_pos()

        for label in self.facility_labels:
            if label.name == self.hovered_label:
                tip_text = f"Press to enter {label.display_name}"
                tip_font = pygame.font.Font(None, 20)
                tip_surf = tip_font.render(tip_text, True, (200, 220, 255))

                tip_w = tip_surf.get_width() + 16
                tip_h = tip_surf.get_height() + 10
                tip_x = min(mouse_x + 15, self.screen_size[0] - tip_w - 10)
                tip_y = mouse_y - tip_h - 5

                tip_bg = pygame.Surface((tip_w, tip_h), pygame.SRCALPHA)
                pygame.draw.rect(tip_bg, (20, 30, 50, 230),
                               (0, 0, tip_w, tip_h), border_radius=5)
                pygame.draw.rect(tip_bg, (*label.color, 150),
                               (0, 0, tip_w, tip_h), 1, border_radius=5)
                screen.blit(tip_bg, (tip_x, tip_y))
                screen.blit(tip_surf, (tip_x + 8, tip_y + 5))
                break

    def _get_launch_button_rect(self) -> pygame.Rect:
        """출격 버튼 rect (모함 이미지 내부 하단 중앙)"""
        btn_w, btn_h = 120, 45

        # 모함 rect가 있으면 모함 내부 하단에 배치
        if self.carrier_rect:
            btn_x = self.carrier_rect.centerx - btn_w // 2
            btn_y = self.carrier_rect.bottom - btn_h - 25  # 모함 하단에서 25px 위
            return pygame.Rect(btn_x, btn_y, btn_w, btn_h)
        else:
            # 모함 rect가 없으면 화면 중앙 하단
            SCREEN_WIDTH, SCREEN_HEIGHT = self.screen_size
            return pygame.Rect(SCREEN_WIDTH // 2 - btn_w // 2,
                             SCREEN_HEIGHT // 2 + 80, btn_w, btn_h)

    def _render_launch_button(self, screen: pygame.Surface):
        """출격 버튼 렌더링 (모함 내부 배치)"""
        rect = self._get_launch_button_rect()
        hover = self.launch_glow

        # 펄스 효과
        pulse = 0.95 + 0.05 * math.sin(self.animation_time * 4)
        pulse_expand = int((pulse - 0.95) * 30 + hover * 6)
        draw_rect = rect.inflate(pulse_expand, pulse_expand)

        # 외부 글로우 (모함 내부에서 빛나는 효과)
        glow_size = 20 + int(hover * 15)
        glow_surf = pygame.Surface((draw_rect.width + glow_size * 2,
                                   draw_rect.height + glow_size * 2), pygame.SRCALPHA)
        glow_alpha = int(40 + hover * 60)
        pygame.draw.rect(glow_surf, (255, 120, 80, glow_alpha),
                        (0, 0, glow_surf.get_width(), glow_surf.get_height()),
                        border_radius=15)
        screen.blit(glow_surf, (draw_rect.x - glow_size, draw_rect.y - glow_size))

        # 버튼 배경 (그라데이션 느낌)
        btn_surf = pygame.Surface((draw_rect.width, draw_rect.height), pygame.SRCALPHA)

        # 배경 색상
        bg_r = int(180 + hover * 50)
        bg_g = int(70 + hover * 30)
        bg_b = int(60 + hover * 20)
        pygame.draw.rect(btn_surf, (bg_r, bg_g, bg_b, 240),
                        (0, 0, draw_rect.width, draw_rect.height), border_radius=10)

        # 상단 하이라이트
        highlight = pygame.Surface((draw_rect.width - 4, 3), pygame.SRCALPHA)
        highlight.fill((255, 200, 180, int(80 + hover * 60)))
        btn_surf.blit(highlight, (2, 2))

        # 테두리
        border_r = int(255)
        border_g = int(140 + hover * 60)
        border_b = int(120 + hover * 60)
        pygame.draw.rect(btn_surf, (border_r, border_g, border_b),
                        (0, 0, draw_rect.width, draw_rect.height), 2, border_radius=10)

        screen.blit(btn_surf, draw_rect.topleft)

        # 아이콘 (로켓/화살표)
        icon_x = draw_rect.x + 18
        icon_y = draw_rect.centery
        arrow_offset = int(math.sin(self.animation_time * 5) * 2)

        # 로켓 아이콘 (삼각형 + 불꽃)
        rocket_color = (255, 255, 255)
        pygame.draw.polygon(screen, rocket_color, [
            (icon_x + arrow_offset, icon_y - 8),
            (icon_x + arrow_offset + 10, icon_y),
            (icon_x + arrow_offset, icon_y + 8),
        ])
        # 불꽃 효과
        flame_alpha = int(150 + 50 * math.sin(self.animation_time * 8))
        flame_surf = pygame.Surface((10, 8), pygame.SRCALPHA)
        pygame.draw.polygon(flame_surf, (255, 180, 80, flame_alpha), [
            (8, 4), (0, 0), (0, 8)
        ])
        screen.blit(flame_surf, (icon_x + arrow_offset - 10, icon_y - 4))

        # 텍스트
        text = self.fonts["medium"].render("LAUNCH", True, (255, 255, 255))
        text_rect = text.get_rect(center=(draw_rect.centerx + 8, draw_rect.centery))
        screen.blit(text, text_rect)

    # =========================================================================
    # 이벤트 처리
    # =========================================================================

    def handle_event(self, event: pygame.event.Event):
        # 오프닝 컷씬 활성화 중이면 컷씬 이벤트 처리
        if self.active_cutscene:
            self._handle_cutscene_event(event)
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = event.pos

            # 시설 라벨 클릭
            for label in self.facility_labels:
                if label.rect and label.rect.collidepoint(mouse_pos) and label.clickable:
                    self._on_facility_click(label.name)
                    return

            # 출격 버튼 클릭
            if self._get_launch_button_rect().collidepoint(mouse_pos):
                self._on_launch_click()
                return

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                # ESC키로 게임 종료
                pygame.quit()
                import sys
                sys.exit()

            # 숫자 키
            facility_keys = {
                pygame.K_1: "hangar",
                pygame.K_2: "workshop",
                pygame.K_3: "shop",
                pygame.K_4: "briefing",
            }
            if event.key in facility_keys:
                self._on_facility_click(facility_keys[event.key])
                return

            if event.key == pygame.K_RETURN:
                self._on_launch_click()
                return

    def _handle_cutscene_event(self, event: pygame.event.Event):
        """오프닝 컷씬 이벤트 처리"""
        if hasattr(self.active_cutscene, 'handle_event'):
            self.active_cutscene.handle_event(event)

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                # ESC로 컷씬 스킵
                if hasattr(self.active_cutscene, 'skip'):
                    self.active_cutscene.skip()
            elif event.key in (pygame.K_SPACE, pygame.K_RETURN):
                # 스페이스/엔터로 다음 대사
                if hasattr(self.active_cutscene, 'handle_click'):
                    self.active_cutscene.handle_click()

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # 마우스 클릭으로 다음 대사
            if hasattr(self.active_cutscene, 'handle_click'):
                self.active_cutscene.handle_click()

    def _on_facility_click(self, facility_name: str):
        """시설 클릭 처리"""
        print(f"INFO: Entering facility: {facility_name}")

        if facility_name == "hangar":
            from modes.hangar_mode import HangarMode
            self.request_push_mode(HangarMode)
        elif facility_name == "workshop":
            from modes.workshop_mode import WorkshopMode
            self.request_push_mode(WorkshopMode)
        elif facility_name == "shop":
            from modes.shop_mode import ShopMode
            self.request_push_mode(ShopMode)
        elif facility_name == "briefing":
            from modes.briefing_mode import BriefingMode
            self.request_push_mode(BriefingMode)

    def _on_launch_click(self):
        """출격 버튼 클릭"""
        print("INFO: Launching mission!")

        self.engine.shared_state['global_score'] = self.game_data.get('credits', 0)
        self.engine.shared_state['current_ship'] = self.game_data.get('current_ship', 'FIGHTER')

        from modes.wave_mode import WaveMode
        self.request_switch_mode(WaveMode)

    # =========================================================================
    # 라이프사이클
    # =========================================================================

    def on_enter(self):
        super().on_enter()
        if hasattr(self, 'sound_manager') and self.sound_manager:
            self.sound_manager.play_bgm("base_bgm")

    def on_exit(self):
        elapsed = time.time() - self.play_start_time
        self.engine.shared_state['total_play_time'] = self.total_play_time + elapsed
        super().on_exit()

    def on_resume(self, return_data=None):
        super().on_resume(return_data)
        self.game_data["credits"] = self.engine.shared_state.get('global_score', 0)
        self.game_data["current_ship"] = self.engine.shared_state.get('current_ship', 'FIGHTER')


print("INFO: base_hub_mode.py loaded (Carrier Label Design)")
