# modes/base_hub_mode.py
"""
BaseHubMode - 기지 허브 모드 (Modern Circular Design)
전투 사이에 함선 교체, 업그레이드, 미션 선택을 수행하는 기지 화면

Design: 중앙 모함 + 원형 아이콘 + 도해 스타일 연결선 + 갤러리 바
- 중앙: 우주모함 이미지 (플로팅 애니메이션)
- 모함 주변: 원형 시설 아이콘 (도해 스타일 연결선)
- 상단: 미니멀 상태바
- 하단: 시설 갤러리 바
- 중앙 하단: 출격 버튼
"""

import pygame
import math
import random
import time
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from pathlib import Path

import config
from modes.base_mode import GameMode, ModeConfig
from systems.save_system import get_save_system
from systems.dialogue_loader import get_dialogue_loader


# =============================================================================
# 색상 테마 (가이드 이미지 참조)
# =============================================================================

BASEHUB_COLORS = {
    # 배경
    "bg_dark": (8, 12, 20),
    "bg_panel": (18, 24, 35),
    "bg_icon": (25, 32, 45),

    # 강조
    "accent_cyan": (80, 200, 255),
    "accent_blue": (100, 150, 255),
    "accent_gold": (255, 200, 80),

    # 시설별 색상
    "hangar": (80, 140, 255),
    "workshop": (80, 220, 140),
    "shop": (255, 180, 80),
    "briefing": (180, 120, 255),
    "training": (255, 100, 100),
    "archive": (150, 120, 200),
}


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
# 플레어 파티클 시스템 (시설 아이콘에서 분출)
# =============================================================================

@dataclass
class FlareParticle:
    """플레어 파티클"""
    x: float
    y: float
    vx: float
    vy: float
    size: float
    alpha: float
    life: float
    max_life: float
    rotation: float = 0.0
    rotation_speed: float = 0.0


class FlareSystem:
    """시설 아이콘에서 분출되는 플레어 효과"""

    def __init__(self, flare_image_path: str):
        self.particles: List[FlareParticle] = []
        self.flare_image: Optional[pygame.Surface] = None
        self.spawn_timer = 0.0
        self.spawn_interval = 0.6  # 플레어 생성 간격 (초)
        self.base_size = 80  # 기본 플레어 크기 (크게 증가)

        # 플레어 이미지 로드
        try:
            img = pygame.image.load(flare_image_path).convert_alpha()
            self.flare_image = pygame.transform.smoothscale(img, (self.base_size, self.base_size))
        except Exception as e:
            print(f"WARNING: Failed to load flare image: {e}")
            self.flare_image = None

    def spawn_flare(self, x: float, y: float):
        """특정 위치에서 플레어 생성"""
        if not self.flare_image:
            return

        # 랜덤 방향으로 분출 (속도 증가)
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(50, 120)
        vx = math.cos(angle) * speed
        vy = math.sin(angle) * speed

        self.particles.append(FlareParticle(
            x=x,
            y=y,
            vx=vx,
            vy=vy - 30,  # 약간 위로 향하는 경향
            size=random.uniform(0.8, 1.5),  # 크기 범위 증가
            alpha=255,
            life=random.uniform(1.5, 2.5),  # 수명 증가
            max_life=random.uniform(1.5, 2.5),
            rotation=random.uniform(0, 360),
            rotation_speed=random.uniform(-120, 120),
        ))

    def update(self, dt: float, icon_positions: List[Tuple[int, int]]):
        """플레어 업데이트 및 간헐적 생성"""
        self.spawn_timer += dt

        # 간헐적으로 랜덤 아이콘에서 플레어 생성
        if self.spawn_timer >= self.spawn_interval and icon_positions:
            self.spawn_timer = 0.0
            self.spawn_interval = random.uniform(0.5, 1.5)  # 다음 생성까지 랜덤 간격

            # 랜덤 아이콘 선택하여 플레어 생성
            pos = random.choice(icon_positions)
            # 2-4개의 플레어를 한 번에 생성
            for _ in range(random.randint(2, 4)):
                self.spawn_flare(pos[0], pos[1])

        # 기존 파티클 업데이트
        for particle in self.particles[:]:
            particle.x += particle.vx * dt
            particle.y += particle.vy * dt
            particle.vy += 15 * dt  # 약한 중력
            particle.life -= dt
            particle.alpha = 255 * (particle.life / particle.max_life)
            particle.rotation += particle.rotation_speed * dt
            particle.size *= 0.995  # 서서히 작아짐

            if particle.life <= 0 or particle.alpha <= 5:
                self.particles.remove(particle)

    def draw(self, screen: pygame.Surface):
        """플레어 렌더링"""
        if not self.flare_image:
            return

        for particle in self.particles:
            if particle.alpha > 5:
                # 크기 및 회전 적용 (base_size 사용)
                size = int(self.base_size * particle.size)
                if size < 10:
                    continue

                scaled = pygame.transform.smoothscale(self.flare_image, (size, size))
                rotated = pygame.transform.rotate(scaled, particle.rotation)
                rotated.set_alpha(int(particle.alpha))

                # 중심 기준으로 그리기
                rect = rotated.get_rect(center=(int(particle.x), int(particle.y)))
                screen.blit(rotated, rect)


# =============================================================================
# 원형 시설 아이콘 (Modern Design)
# =============================================================================

@dataclass
class CircularFacilityIcon:
    """원형 시설 아이콘 - 모던 UI 디자인"""
    name: str
    display_name: str
    description: str

    # 화면 기준 위치 (아이콘 배치용)
    screen_x: float = 0.0
    screen_y: float = 0.0

    # 모함 연결 포인트 (상대 좌표 0.0~1.0)
    carrier_rel_x: float = 0.5
    carrier_rel_y: float = 0.5

    # 시각 요소
    color: Tuple[int, int, int] = (80, 140, 255)
    icon_char: str = "◆"
    icon_image: Optional[pygame.Surface] = None
    facility_image: Optional[pygame.Surface] = None  # 시설 내부 이미지

    # 상태
    radius: int = 50
    hover_progress: float = 0.0
    glow_phase: float = 0.0
    rect: Optional[pygame.Rect] = None
    clickable: bool = True

    def get_center(self) -> Tuple[int, int]:
        """아이콘 중심점 반환"""
        return (int(self.screen_x), int(self.screen_y))

    def update_rect(self):
        """클릭 영역 업데이트"""
        center = self.get_center()
        self.rect = pygame.Rect(
            center[0] - self.radius,
            center[1] - self.radius,
            self.radius * 2,
            self.radius * 2
        )


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

        # 배경 (facility_bg 이미지 사용)
        self.background = self._load_facility_background()
        self.particle_system = ParticleSystem(self.screen_size, count=25)

        # 플레어 시스템 초기화
        flare_path = str(config.ASSET_DIR / "images" / "facilities" / "facility_flare.png")
        self.flare_system = FlareSystem(flare_path)

        # 우주모함 이미지
        self.carrier_image = self._load_carrier_image()
        self.carrier_rect: Optional[pygame.Rect] = None  # 모함 위치 저장

        # 갤러리 바 설정 - 더 크게, 위로 배치 (아이콘 생성 전에 설정 필요)
        self.gallery_bar_height = 170  # 하단 바 높이 더 증가
        self.gallery_icon_radius = 52  # 갤러리 아이콘 크기

        # 원형 시설 아이콘 생성 (Modern Design)
        self.facility_icons = self._create_facility_icons()
        self.hovered_icon: Optional[str] = None

        # 출격 버튼 (모함 내부에 위치)
        self.launch_hover = False
        self.launch_glow = 0.0

        # 플레이 시간
        self.play_start_time = time.time()
        self.total_play_time = self.engine.shared_state.get('total_play_time', 0)

        # 새 게임 플래그 초기화
        if self.is_new_game:
            self.engine.shared_state['is_new_game'] = False

        # 음성 시스템 (컷씬용)
        self.voice_system = None

        # 커스텀 커서 로드
        self.custom_cursor = self._load_custom_cursor()

        print("INFO: BaseHubMode initialized (Unified Flow)")

    def _show_opening_cutscene(self):
        """게임 오프닝 컷씬 표시"""
        from objects import StoryBriefingEffect
        from mode_configs import config_story_dialogue

        # JSON 우선 로드 시도
        dialogue_loader = get_dialogue_loader()
        scene_data = dialogue_loader.load_scene("intro_opening")

        if scene_data:
            # JSON에서 로드
            print("INFO: Loading intro cutscene from JSON")
            dialogues = scene_data.get("dialogues", [])
            title = scene_data.get("title", "ACT 1: REMNANTS OF EARTH")
            location = scene_data.get("location", "EARTH ORBIT - SECTOR 7")
            bg_filename = scene_data.get("background", "bg_ruins.jpg")
            bg_path = config.ASSET_DIR / "story_mode" / "backgrounds" / bg_filename
            if not bg_path.exists():
                bg_path = config.ASSET_DIR / "images" / "backgrounds" / bg_filename
        else:
            # Fallback: 기존 Python 설정에서 로드
            print("INFO: Loading intro cutscene from config (fallback)")
            opening_data = config_story_dialogue.get_set_opening(1)
            if not opening_data:
                print("WARNING: No opening data found, skipping cutscene")
                self.opening_shown = True
                return
            dialogues = opening_data.get("dialogues", [])
            title = opening_data.get("title", "PROLOGUE")
            location = opening_data.get("location", "MOTHERSHIP - ARK PRIME")
            bg_path = config.ASSET_DIR / "images" / "backgrounds" / "bg_ruins.jpg"

        # 배경 fallback
        if not bg_path.exists():
            bg_path = config.ASSET_DIR / "images" / "backgrounds" / "bg_space.jpg"

        # 오프닝 브리핑 효과 생성
        briefing = StoryBriefingEffect(
            screen_size=self.screen_size,
            dialogue_data=dialogues,
            background_path=bg_path,
            title=title,
            location=location
        )
        briefing.set_fonts(self.fonts)
        briefing.on_complete = self._on_opening_complete

        # 음성 시스템 초기화 및 연결
        self._init_voice_system_for_cutscene()
        if self.voice_system:
            briefing.on_dialogue_start = self._speak_dialogue
            briefing.voice_system = self.voice_system  # 음성 시스템 참조 연결 (자동 진행 동기화용)
            # 첫 대사 음성 수동 호출 (StoryBriefingEffect 생성 시 이미 첫 대사가 준비됨)
            if dialogues:
                first_dialogue = dialogues[0]
                self._speak_dialogue(
                    first_dialogue.get("speaker", "NARRATOR"),
                    first_dialogue.get("text", "")
                )

        self.active_cutscene = briefing
        print("INFO: Showing game opening cutscene")

    def _init_voice_system_for_cutscene(self):
        """컷씬용 음성 시스템 초기화"""
        try:
            from systems.voice_system import VoiceSystem, EdgeTTSAdapter, Pyttsx3Adapter, SilentAdapter
            from mode_configs import config_story_dialogue

            voice_settings = config_story_dialogue.VOICE_SYSTEM_SETTINGS
            char_voice_settings = config_story_dialogue.CHARACTER_VOICE_SETTINGS

            if not voice_settings.get("enabled", False):
                self.voice_system = None
                return

            self.voice_system = VoiceSystem(
                enabled=True,
                default_adapter=voice_settings.get("default_adapter", "edge")
            )

            for char_id, settings in char_voice_settings.items():
                adapter_type = settings.get("adapter", "edge")
                if adapter_type == "edge":
                    adapter = EdgeTTSAdapter(
                        voice=settings.get("voice", "ko-KR-SunHiNeural"),
                        rate=settings.get("rate", "+0%"),
                        pitch=settings.get("pitch", "+0Hz"),
                        style=settings.get("style"),
                        style_degree=settings.get("style_degree", 1.0),
                        auto_emotion=settings.get("auto_emotion", True)
                    )
                elif adapter_type == "pyttsx3":
                    adapter = Pyttsx3Adapter(
                        rate=settings.get("rate", 150),
                        volume=settings.get("volume", 1.0)
                    )
                else:
                    adapter = SilentAdapter()
                self.voice_system.register_character(char_id, adapter)

            self.voice_system.start()
            print("INFO: Voice system initialized for opening cutscene")

        except Exception as e:
            print(f"WARNING: Voice system init failed for cutscene: {e}")
            self.voice_system = None

    def _speak_dialogue(self, speaker: str, text: str):
        """대사 음성 재생"""
        if self.voice_system and self.voice_system.enabled:
            clean_text = text
            if text.startswith("(") and ")" in text:
                clean_text = text.strip("()")
            self.voice_system.speak(speaker, clean_text)

    def _on_opening_complete(self):
        """오프닝 컷씬 완료 콜백"""
        self.active_cutscene = None
        self.opening_shown = True
        # 음성 시스템 정리
        if self.voice_system:
            self.voice_system.stop()
            self.voice_system = None
        print("INFO: Opening cutscene complete, entering BaseHub")

    def _load_custom_cursor(self) -> Optional[pygame.Surface]:
        """커스텀 커서 이미지 로드"""
        cursor_path = config.ASSET_DIR / "images" / "items" / "mouse_action.png"
        try:
            if cursor_path.exists():
                cursor_img = pygame.image.load(str(cursor_path)).convert_alpha()
                cursor_size = 64  # 2배 크기
                cursor_img = pygame.transform.smoothscale(cursor_img, (cursor_size, cursor_size))
                print("INFO: Custom cursor loaded")
                return cursor_img
        except Exception as e:
            print(f"WARNING: Failed to load custom cursor: {e}")
        return None

    def _load_facility_background(self) -> pygame.Surface:
        """facility_bg 이미지를 배경으로 로드"""
        bg_path = config.ASSET_DIR / "images" / "facilities" / "facility_bg.png"
        try:
            if bg_path.exists():
                img = pygame.image.load(str(bg_path)).convert()
                return pygame.transform.smoothscale(img, self.screen_size)
        except Exception as e:
            print(f"WARNING: Failed to load facility_bg: {e}")

        # 폴백: 어두운 우주 배경
        surf = pygame.Surface(self.screen_size)
        surf.fill((10, 15, 25))
        return surf

    def _load_carrier_image(self) -> Optional[pygame.Surface]:
        """우주모함 이미지 로드"""
        # PNG 형식 우선
        bg_paths = [
            config.ASSET_DIR / "images" / "base" / "basehub_mother_01.png",
            config.ASSET_DIR / "images" / "base" / "carrier_bg.png",
            config.ASSET_DIR / "images" / "base" / "basehub_bg_01.png",
            config.ASSET_DIR / "images" / "base" / "basehub_bg_0000.png",
            config.ASSET_DIR / "images" / "base" / "basehub_bg_02.png",
        ]

        for bg_path in bg_paths:
            try:
                if bg_path.exists():
                    return pygame.image.load(str(bg_path)).convert_alpha()
            except Exception:
                continue
        return None

    def _create_facility_icons(self) -> List[CircularFacilityIcon]:
        """원형 시설 아이콘 생성 - 모함 타원 주위를 둘러싸는 배치"""
        SCREEN_WIDTH, SCREEN_HEIGHT = self.screen_size

        # 화면 중심 (모함 위치 기준) - 하단 아이콘 공간 확보
        center_x = SCREEN_WIDTH // 2
        center_y = (SCREEN_HEIGHT - 100) // 2

        # 타원 반경 (모함에 더 가깝게 - 타원 경계에 닿도록)
        ellipse_rx = SCREEN_WIDTH * 0.36  # 가로 반경 증가
        ellipse_ry = SCREEN_HEIGHT * 0.32  # 세로 반경 증가

        # 6개 아이콘을 타원 위에 배치 (각도로 계산)
        # 좌측 상단부터 시계방향: workshop, shop, briefing, archive, training, hangar
        icon_angles = [
            ("workshop", -120, 0.25, 0.30),   # 좌상단
            ("shop", -60, 0.75, 0.30),        # 우상단
            ("briefing", 0, 0.85, 0.50),      # 우측
            ("archive", 60, 0.70, 0.70),      # 우하단
            ("training", 120, 0.30, 0.70),    # 좌하단
            ("hangar", 180, 0.15, 0.50),      # 좌측
        ]

        icons_data = []
        for name, angle_deg, rel_x, rel_y in icon_angles:
            angle_rad = math.radians(angle_deg)
            x = center_x + ellipse_rx * math.cos(angle_rad)
            y = center_y + ellipse_ry * math.sin(angle_rad)

            icon_info = {
                "hangar": ("HANGAR", "함선 선택", BASEHUB_COLORS["hangar"], "✈"),
                "workshop": ("WORKSHOP", "업그레이드", BASEHUB_COLORS["workshop"], "⚙"),
                "shop": ("SUPPLY", "보급품 구매", BASEHUB_COLORS["shop"], "★"),
                "briefing": ("BRIEFING", "미션 브리핑", BASEHUB_COLORS["briefing"], "◎"),
                "training": ("TRAINING", "훈련 모드", BASEHUB_COLORS["training"], "⚔"),
                "archive": ("ARCHIVE", "성찰의 기록", BASEHUB_COLORS["archive"], "📚"),
            }

            display_name, description, color, icon_char = icon_info[name]
            icons_data.append({
                "name": name,
                "display_name": display_name,
                "description": description,
                "screen_x": x,
                "screen_y": y,
                "carrier_rel_x": rel_x,
                "carrier_rel_y": rel_y,
                "color": color,
                "icon_char": icon_char,
            })

        # 아이콘 크기 (화면 크기에 반응) - 부속실 원 크기 더 증가
        base_radius = min(SCREEN_WIDTH, SCREEN_HEIGHT) * 0.095
        base_radius = max(70, min(105, int(base_radius)))

        icons = []
        for data in icons_data:
            # 시설 내부 이미지 로드 시도
            facility_image = self._load_facility_image(data["name"])
            icon_image = self._load_facility_icon(data["name"])

            icons.append(CircularFacilityIcon(
                name=data["name"],
                display_name=data["display_name"],
                description=data["description"],
                screen_x=data["screen_x"],
                screen_y=data["screen_y"],
                carrier_rel_x=data["carrier_rel_x"],
                carrier_rel_y=data["carrier_rel_y"],
                color=data["color"],
                icon_char=data.get("icon_char", "◆"),
                icon_image=icon_image,
                facility_image=facility_image,
                radius=base_radius,
                glow_phase=random.uniform(0, math.pi * 2),
            ))
        return icons

    def _load_facility_image(self, facility_name: str) -> Optional[pygame.Surface]:
        """시설 내부 이미지 로드 (원형 썸네일용)"""
        # PNG 형식 우선
        image_paths = [
            config.ASSET_DIR / "images" / "facilities" / f"facility_{facility_name}.png",
            config.ASSET_DIR / "images" / "facilities" / f"facility_{facility_name}.jpg",
            config.ASSET_DIR / "images" / "base" / f"{facility_name}_interior.png",
            config.ASSET_DIR / "images" / "base" / f"{facility_name}_interior.jpg",
            config.ASSET_DIR / "images" / "base" / f"{facility_name}_bg.png",
            config.ASSET_DIR / "images" / "base" / f"{facility_name}_bg.jpg",
        ]

        for path in image_paths:
            try:
                if path.exists():
                    img = pygame.image.load(str(path)).convert_alpha()
                    # 정사각형으로 크롭
                    w, h = img.get_size()
                    size = min(w, h)
                    crop_x = (w - size) // 2
                    crop_y = (h - size) // 2
                    cropped = img.subsurface((crop_x, crop_y, size, size))
                    return pygame.transform.smoothscale(cropped, (120, 120))
            except Exception:
                continue
        return None

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
            except Exception:
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
            # 컷씬이 완료되었는지 확인 (on_complete 콜백에서 이미 처리되었을 수 있음)
            # active_cutscene이 None이 아니고 is_alive가 False면 수동 해제
            if self.active_cutscene and hasattr(self.active_cutscene, 'is_alive') and not self.active_cutscene.is_alive:
                # on_complete 콜백이 호출되지 않은 경우에만 수동 해제
                self.active_cutscene = None
                self.opening_shown = True
            return

        # 페이드 인
        if self.fade_alpha > 0:
            self.fade_alpha = max(0, self.fade_alpha - 400 * dt)

        # 파티클
        self.particle_system.update(dt)

        # 플레어 시스템 업데이트 (시설 아이콘 위치 전달)
        icon_positions = [icon.get_center() for icon in self.facility_icons]
        self.flare_system.update(dt, icon_positions)

        # 마우스 호버
        mouse_pos = pygame.mouse.get_pos()

        # 원형 아이콘 호버 체크
        self.hovered_icon = None
        for icon in self.facility_icons:
            icon.update_rect()
            # 원형 충돌 검사 (더 정확함)
            center = icon.get_center()
            dx = mouse_pos[0] - center[0]
            dy = mouse_pos[1] - center[1]
            distance = math.sqrt(dx * dx + dy * dy)

            if distance <= icon.radius:
                self.hovered_icon = icon.name
                icon.hover_progress = min(1.0, icon.hover_progress + dt * 8)
            else:
                icon.hover_progress = max(0.0, icon.hover_progress - dt * 5)
            icon.glow_phase += dt * 2.5

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

        # 3. 중앙 모함 이미지
        self._render_carrier(screen)

        # 4. 원형 아이콘 + 연결선
        self._render_facility_icons(screen)

        # 5. 플레어 효과 (아이콘 위에 렌더링)
        self.flare_system.draw(screen)

        # 6. 하단 갤러리 바
        self._render_gallery_bar(screen)

        # 7. 출격 버튼
        self._render_launch_button(screen)

        # 8. 호버 툴팁
        if self.hovered_icon:
            self._render_tooltip(screen)

        # 9. 페이드 인
        if self.fade_alpha > 0:
            fade_surface = pygame.Surface(self.screen_size, pygame.SRCALPHA)
            fade_surface.fill((0, 0, 0, int(self.fade_alpha)))
            screen.blit(fade_surface, (0, 0))

        # 10. 오프닝 컷씬 (최상단에 렌더링)
        if self.active_cutscene:
            if hasattr(self.active_cutscene, 'render'):
                self.active_cutscene.render(screen)
            elif hasattr(self.active_cutscene, 'draw'):
                self.active_cutscene.draw(screen)

        # 11. 커스텀 커서 (최상단에 렌더링)
        if self.custom_cursor:
            mouse_pos = pygame.mouse.get_pos()
            # 커서 핫스팟을 중앙으로 조정
            cursor_rect = self.custom_cursor.get_rect(center=mouse_pos)
            screen.blit(self.custom_cursor, cursor_rect)

    def _render_carrier(self, screen: pygame.Surface):
        """중앙 모함 이미지 렌더링"""
        SCREEN_WIDTH, SCREEN_HEIGHT = self.screen_size
        center_x = SCREEN_WIDTH // 2
        # 화면 중앙에서 약간 위로 배치 (하단 아이콘 공간 확보)
        center_y = (SCREEN_HEIGHT - 100) // 2

        # 플로팅 애니메이션
        float_offset = math.sin(self.animation_time * 1.0) * 5

        carrier_rect = None

        if self.carrier_image:
            # 크기 조정 - 모함 이미지 더 크게 (화면 전체 활용)
            orig_w, orig_h = self.carrier_image.get_size()
            max_size = min(SCREEN_WIDTH * 0.80, (SCREEN_HEIGHT - 150) * 0.85)
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
            new_w, new_h = 350, 180
            carrier_rect = pygame.Rect(0, 0, new_w, new_h)
            carrier_rect.center = (center_x, int(center_y + float_offset))

            pygame.draw.rect(screen, (40, 60, 100), carrier_rect, border_radius=15)
            pygame.draw.rect(screen, (80, 120, 180), carrier_rect, 2, border_radius=15)

            text = self.fonts["large"].render("CARRIER", True, (150, 180, 220))
            text_rect = text.get_rect(center=carrier_rect.center)
            screen.blit(text, text_rect)

        # 모함 rect 저장
        self.carrier_rect = carrier_rect

        # 타이틀을 모함 위에 렌더링 - 밝은 색상 (어두운 배경용)
        if carrier_rect:
            title_text = self.fonts["large"].render("ECHO CARRIER", True, (180, 200, 230))
            title_rect = title_text.get_rect(centerx=carrier_rect.centerx, bottom=carrier_rect.top - 15)
            screen.blit(title_text, title_rect)

    def _render_facility_icons(self, screen: pygame.Surface):
        """원형 시설 아이콘 + 도해 스타일 연결선 렌더링"""
        if not self.carrier_rect:
            return

        for icon in self.facility_icons:
            hover = icon.hover_progress
            center = icon.get_center()
            radius = icon.radius

            # === 1. 모함으로의 연결선 ===
            self._render_elbow_connection(screen, icon)

            # === 2. 시설 내부 이미지 (원형 마스킹) 또는 아이콘 문자 ===
            if icon.facility_image:
                # 원형 이미지 (테두리 없음, 원 전체 채움)
                self._draw_circular_image(screen, icon.facility_image, center, radius, inner_image_ratio=1.0)
            else:
                # 컬러 원 배경 (이미지 없을 때)
                pygame.draw.circle(screen, icon.color, center, radius)

                # 아이콘 문자
                icon_font = self.fonts.get("large", self.fonts["medium"])
                icon_text = icon_font.render(icon.icon_char, True, (255, 255, 255))
                icon_text_rect = icon_text.get_rect(center=center)
                screen.blit(icon_text, icon_text_rect)

            # === 3. 테두리 삭제 (요청사항) ===
            # 테두리 없음

            # === 4. 시설 이름 라벨 (아이콘 아래) ===
            self._render_icon_label(screen, icon)

    def _render_elbow_connection(self, screen: pygame.Surface, icon: CircularFacilityIcon):
        """도해 스타일 꺾인선 연결선 렌더링 - 얇은 검은색, 모함 내부로 연장"""
        if not self.carrier_rect:
            return

        # 아이콘 중심
        icon_center = icon.get_center()

        # 모함 연결 포인트 (모함 내부로 약간 더 깊게)
        carrier_point_x = self.carrier_rect.x + int(self.carrier_rect.width * icon.carrier_rel_x)
        carrier_point_y = self.carrier_rect.y + int(self.carrier_rect.height * icon.carrier_rel_y)
        carrier_point = (carrier_point_x, carrier_point_y)

        # 아이콘 테두리에서 시작점 계산
        dx = carrier_point_x - icon_center[0]
        dy = carrier_point_y - icon_center[1]
        distance = math.sqrt(dx * dx + dy * dy)
        if distance > 0:
            start_x = icon_center[0] + int(dx / distance * icon.radius)
            start_y = icon_center[1] + int(dy / distance * icon.radius)
        else:
            start_x, start_y = icon_center

        start_point = (start_x, start_y)

        # 직선 연결 (elbow 없이) - 아이콘에서 모함 내부까지
        line_color = (40, 40, 40)  # 얇은 검은색
        line_width = 1

        # 선 그리기 (시작점 -> 모함 연결점)
        pygame.draw.line(screen, line_color, start_point, carrier_point, line_width)

        # 모함 연결점에 작은 원 마커 (검은색)
        pygame.draw.circle(screen, (30, 30, 30), carrier_point, 3)

    def _draw_circular_image(self, screen: pygame.Surface, image: pygame.Surface,
                            center: Tuple[int, int], radius: int, inner_image_ratio: float = 1.0):
        """이미지를 원형으로 마스킹하여 그리기

        Args:
            inner_image_ratio: 내부 이미지 크기 비율 (1.0 = 원 전체, 0.8 = 80% 크기)
        """
        diameter = radius * 2

        # 내부 이미지 크기 계산
        inner_diameter = int(diameter * inner_image_ratio)
        offset = (diameter - inner_diameter) // 2

        # 이미지 크기 조정
        scaled = pygame.transform.smoothscale(image, (inner_diameter, inner_diameter))

        # 원형 마스크 생성
        mask_surf = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
        pygame.draw.circle(mask_surf, (255, 255, 255, 255), (radius, radius), radius)

        # 마스크 적용
        masked = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
        masked.blit(scaled, (offset, offset))
        masked.blit(mask_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

        screen.blit(masked, (center[0] - radius, center[1] - radius))

    def _render_icon_label(self, screen: pygame.Surface, icon: CircularFacilityIcon):
        """아이콘 아래 시설 이름 라벨 - 밝은 색상 (어두운 배경용)"""
        center = icon.get_center()
        hover = icon.hover_progress

        # 시설 이름 - 밝은 색상 (어두운 배경용)
        name_color = (220, 230, 250) if hover > 0.3 else (160, 170, 190)
        name_font = self.fonts.get("small", self.fonts["tiny"])
        name_text = name_font.render(icon.display_name, True, name_color)
        name_rect = name_text.get_rect(centerx=center[0], top=center[1] + icon.radius + 8)
        screen.blit(name_text, name_rect)

        # 설명 (호버 시에만) - 밝은 색상
        if hover > 0.2:
            desc_color = (140, 160, 200)
            desc_font = self.fonts.get("tiny", self.fonts["small"])
            desc_text = desc_font.render(icon.description, True, desc_color)
            desc_rect = desc_text.get_rect(centerx=center[0], top=name_rect.bottom + 2)
            screen.blit(desc_text, desc_rect)

    def _render_gallery_bar(self, screen: pygame.Surface):
        """하단 시설 아이콘 렌더링 - 배경 없이 아이콘만"""
        SCREEN_WIDTH, SCREEN_HEIGHT = self.screen_size

        # 배경 바 없음 - 아이콘만 렌더링

        # 각 시설의 미니 아이콘 배치 - 간격 크게 넓힘
        num_icons = len(self.facility_icons)
        spacing = 160  # 간격 대폭 증가
        total_width = (num_icons - 1) * spacing
        start_x = (SCREEN_WIDTH - total_width) // 2  # 완전 중앙 정렬
        icon_y = SCREEN_HEIGHT - 90  # 화면 하단에서 90px 위

        for i, icon in enumerate(self.facility_icons):
            icon_x = start_x + spacing * i
            mini_radius = self.gallery_icon_radius

            # 호버 상태
            is_hovered = icon.name == self.hovered_icon
            hover_scale = 1.0 + (0.1 * icon.hover_progress)
            current_radius = int(mini_radius * hover_scale)

            # 시설 이미지 또는 아이콘 문자 (테두리 없음)
            if icon.facility_image:
                self._draw_circular_image(screen, icon.facility_image,
                                        (icon_x, icon_y), current_radius)
            else:
                # 컬러 배경
                pygame.draw.circle(screen, icon.color, (icon_x, icon_y), current_radius)

                # 아이콘 문자
                mini_font = self.fonts.get("medium", self.fonts["small"])
                char_text = mini_font.render(icon.icon_char, True, (255, 255, 255))
                char_rect = char_text.get_rect(center=(icon_x, icon_y))
                screen.blit(char_text, char_rect)

            # 시설 이름 (아이콘 아래) - 밝은 텍스트 (어두운 배경용)
            label_color = (220, 230, 250) if is_hovered else (150, 160, 180)
            label_font = self.fonts.get("tiny", self.fonts["small"])
            label_text = label_font.render(icon.display_name, True, label_color)
            label_rect = label_text.get_rect(centerx=icon_x, top=icon_y + current_radius + 4)
            screen.blit(label_text, label_rect)

    def _render_tooltip(self, screen: pygame.Surface):
        """호버 툴팁 렌더링"""
        mouse_x, mouse_y = pygame.mouse.get_pos()

        for icon in self.facility_icons:
            if icon.name == self.hovered_icon:
                tip_text = f"클릭하여 {icon.display_name} 입장"
                tip_font = self.fonts.get("small", self.fonts["tiny"])
                tip_surf = tip_font.render(tip_text, True, (200, 220, 255))

                tip_w = tip_surf.get_width() + 20
                tip_h = tip_surf.get_height() + 12
                tip_x = min(mouse_x + 15, self.screen_size[0] - tip_w - 10)
                tip_y = mouse_y - tip_h - 8

                # 툴팁 배경
                tip_bg = pygame.Surface((tip_w, tip_h), pygame.SRCALPHA)
                pygame.draw.rect(tip_bg, (20, 28, 45, 240),
                               (0, 0, tip_w, tip_h), border_radius=6)
                pygame.draw.rect(tip_bg, (*icon.color, 180),
                               (0, 0, tip_w, tip_h), 1, border_radius=6)
                screen.blit(tip_bg, (tip_x, tip_y))
                screen.blit(tip_surf, (tip_x + 10, tip_y + 6))
                break

    def _get_launch_button_rect(self) -> pygame.Rect:
        """출격 버튼 rect (모함 원 외부 하단에 배치)"""
        # 텍스트 크기에 맞게 박스 크기 계산
        text_surf = self.fonts["medium"].render("LAUNCH", True, (255, 255, 255))
        text_w, text_h = text_surf.get_size()
        padding_x, padding_y = 24, 14  # 좌우/상하 패딩
        btn_w = text_w + padding_x * 2
        btn_h = text_h + padding_y * 2

        # 모함 rect가 있으면 모함 원 바깥 아래에 배치
        if self.carrier_rect:
            btn_x = self.carrier_rect.centerx - btn_w // 2
            # 모함 하단에서 30px 아래 (원 바깥으로)
            btn_y = self.carrier_rect.bottom + 30
            return pygame.Rect(btn_x, btn_y, btn_w, btn_h)
        else:
            # 모함 rect가 없으면 화면 중앙 하단
            SCREEN_WIDTH, SCREEN_HEIGHT = self.screen_size
            return pygame.Rect(SCREEN_WIDTH // 2 - btn_w // 2,
                             SCREEN_HEIGHT // 2 + 150, btn_w, btn_h)

    def _render_launch_button(self, screen: pygame.Surface):
        """출격 버튼 렌더링 (미니멀 디자인)"""
        rect = self._get_launch_button_rect()
        hover = self.launch_glow

        # 버튼 배경 Surface
        btn_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)

        # 배경 색상 (호버 시 밝아짐)
        bg_r = int(160 + hover * 40)
        bg_g = int(60 + hover * 25)
        bg_b = int(50 + hover * 20)
        pygame.draw.rect(btn_surf, (bg_r, bg_g, bg_b, 230),
                        (0, 0, rect.width, rect.height), border_radius=8)

        # 테두리 (호버 시 밝아짐)
        border_color = (int(220 + hover * 35), int(100 + hover * 50), int(80 + hover * 40))
        pygame.draw.rect(btn_surf, border_color,
                        (0, 0, rect.width, rect.height), 2, border_radius=8)

        screen.blit(btn_surf, rect.topleft)

        # 텍스트 (다른 라벨과 같은 medium 폰트)
        text_color = (255, 255, 255) if hover > 0.3 else (240, 240, 240)
        text = self.fonts["medium"].render("LAUNCH", True, text_color)
        text_rect = text.get_rect(center=rect.center)
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

            # 원형 아이콘 클릭 (원형 충돌 검사)
            for icon in self.facility_icons:
                center = icon.get_center()
                dx = mouse_pos[0] - center[0]
                dy = mouse_pos[1] - center[1]
                distance = math.sqrt(dx * dx + dy * dy)
                if distance <= icon.radius and icon.clickable:
                    self._on_facility_click(icon.name)
                    return

            # 갤러리 바 아이콘 클릭
            gallery_clicked = self._check_gallery_click(mouse_pos)
            if gallery_clicked:
                self._on_facility_click(gallery_clicked)
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
                pygame.K_5: "training",
                pygame.K_6: "archive",
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

    def _check_gallery_click(self, mouse_pos: Tuple[int, int]) -> Optional[str]:
        """갤러리 바 아이콘 클릭 체크 - 렌더링과 동일한 레이아웃 사용"""
        SCREEN_WIDTH, SCREEN_HEIGHT = self.screen_size

        # 각 아이콘 위치 확인 - _render_gallery_bar와 동일한 계산
        num_icons = len(self.facility_icons)
        spacing = 160  # _render_gallery_bar와 동일
        total_width = (num_icons - 1) * spacing
        start_x = (SCREEN_WIDTH - total_width) // 2
        icon_y = SCREEN_HEIGHT - 90  # _render_gallery_bar와 동일

        for i, icon in enumerate(self.facility_icons):
            icon_x = start_x + spacing * i
            dx = mouse_pos[0] - icon_x
            dy = mouse_pos[1] - icon_y
            distance = math.sqrt(dx * dx + dy * dy)
            if distance <= self.gallery_icon_radius + 8:  # 여유 있게
                return icon.name

        return None

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
        elif facility_name == "training":
            from modes.training_mode import TrainingMode
            self.request_push_mode(TrainingMode)
        elif facility_name == "archive":
            from modes.archive_mode import ArchiveMode
            self.request_push_mode(ArchiveMode)

    def _on_launch_click(self):
        """출격 버튼 클릭"""
        print("INFO: Launching mission!")

        # shared_state에서 최신 데이터 사용 (Hangar에서 변경한 함선 반영)
        self.engine.shared_state['global_score'] = self.game_data.get('credits', 0)
        # current_ship은 이미 shared_state에 저장되어 있으므로 덮어쓰지 않음

        from modes.wave_mode import WaveMode
        self.request_switch_mode(WaveMode)

    # =========================================================================
    # 라이프사이클
    # =========================================================================

    def on_enter(self):
        super().on_enter()
        if hasattr(self, 'sound_manager') and self.sound_manager:
            self.sound_manager.play_bgm("base_bgm")

        # 커스텀 커서 사용 시 기본 커서 숨김
        if self.custom_cursor:
            pygame.mouse.set_visible(False)

    def on_exit(self):
        elapsed = time.time() - self.play_start_time
        self.engine.shared_state['total_play_time'] = self.total_play_time + elapsed

        # 기본 커서 복원
        pygame.mouse.set_visible(True)

        super().on_exit()

    def on_resume(self, return_data=None):
        super().on_resume(return_data)
        self.game_data["credits"] = self.engine.shared_state.get('global_score', 0)
        self.game_data["current_ship"] = self.engine.shared_state.get('current_ship', 'FIGHTER')

        # 커스텀 커서 복원
        if self.custom_cursor:
            pygame.mouse.set_visible(False)


print("INFO: base_hub_mode.py loaded (Modern Circular Design)")
