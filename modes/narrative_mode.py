# modes/narrative_mode.py
"""
NarrativeMode - 통합 스토리 연출 모드

모든 대화, 컷씬, 브리핑, 회상 씬을 단일 모드에서 처리합니다.

지원하는 연출 타입:
- DIALOGUE: 기본 대화 (배경 + 대화창)
- BRIEFING: 미션 브리핑 (타이틀 + 위치 + 대화)
- CUTSCENE: 특수 컷씬 (페이드, 줌, 흔들림 등 효과)
- REFLECTION: 철학적 명상 (몽환적 배경 + 오버레이)
- POLAROID: 폴라로이드 회상 (사진 + 대화)

사용법:
    # EpisodeMode에서 호출
    self.engine.shared_state['narrative_data'] = {
        'type': 'DIALOGUE',
        'scene_id': 'ep1_intro',
        'dialogues': [...],
        'background': 'bg_bunker.jpg',
    }
    from modes.narrative_mode import NarrativeMode
    self.request_push_mode(NarrativeMode)
"""

import pygame
import math
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass
from pathlib import Path

from modes.base_mode import GameMode, ModeConfig
import config


# 빈 대화 템플릿 (Graceful 처리용)
EMPTY_DIALOGUE = {"speaker": "UNKNOWN", "text": "...", "background": None}


@dataclass
class NarrativeModeConfig(ModeConfig):
    """Narrative 모드 설정"""
    mode_name: str = "narrative"
    perspective_enabled: bool = False
    wave_system_enabled: bool = False
    spawn_system_enabled: bool = False
    show_wave_ui: bool = False
    background_type: str = "static"


class NarrativeMode(GameMode):
    """
    통합 스토리 연출 모드

    모든 대화, 컷씬, 브리핑 등을 처리하는 단일 진입점입니다.
    """

    # 색상 톤 매핑 (ReflectionMode에서 가져옴)
    COLOR_TONES = {
        "sepia": (255, 240, 200, 60),     # 추억/향수
        "blue": (100, 150, 200, 80),      # 명상/성찰
        "purple": (150, 100, 200, 70),    # 신비/우주
        "gold": (255, 220, 100, 100),     # 깨달음
        "gray_blue": (150, 160, 180, 70), # 비 오는 날
        "warm": (255, 200, 150, 50),      # 따뜻함
        "cold": (150, 180, 220, 60),      # 차가움
    }

    # 스피커 이름 매핑
    SPEAKER_NAMES = {
        "ARTEMIS": "아르테미스",
        "PILOT": "파일럿",
        "NARRATOR": "나레이터",
        "UNKNOWN": "???",
    }

    # 스피커 색상 매핑
    SPEAKER_COLORS = {
        "ARTEMIS": (255, 180, 180),
        "PILOT": (180, 200, 255),
        "NARRATOR": (180, 255, 180),
        "UNKNOWN": (180, 180, 180),
    }

    def __init__(self, engine, **kwargs):
        """
        Args:
            engine: 게임 엔진
            **kwargs: 추가 설정 (scene_id, narrative_type 등)
        """
        # 연출 데이터 (shared_state에서 가져옴)
        self.narrative_type: str = "DIALOGUE"  # DIALOGUE, BRIEFING, CUTSCENE, REFLECTION, POLAROID
        self.scene_id: str = ""
        self.dialogues: List[Dict] = []
        self.background_path: str = ""
        self.title: str = ""
        self.location: str = ""
        self.color_tone: str = "blue"

        # 대화 진행 상태
        self.current_dialogue_index: int = 0
        self.dialogue_state: str = "intro"  # intro, typing, waiting, outro
        self.displayed_text: str = ""
        self.char_index: int = 0
        self.char_timer: float = 0
        self.wait_timer: float = 0

        # 현재 배경 추적 (배경 전환 감지용)
        self.current_bg_name: str = ""

        # 자동 진행 (레거시 StoryBriefingEffect 동작 복원)
        self.auto_advance: bool = True  # 자동 대화 진행 활성화
        self.auto_advance_delay: float = 0.5  # 음성 완료 후 추가 대기 시간 (초)
        self.auto_advance_timer: float = 0.0
        self.voice_finished: bool = False  # 음성 재생 완료 여부

        # 시각 효과
        self.background: Optional[pygame.Surface] = None
        self.color_overlay: Optional[pygame.Surface] = None
        self.fade_alpha: int = 255  # 페이드 인/아웃
        self.overlay_alpha: int = 0

        # 애니메이션
        self.time_elapsed: float = 0
        self.background_offset: float = 0

        # 포트레이트
        self.portraits: Dict[str, pygame.Surface] = {}
        self.current_speaker: str = ""
        self.current_text: str = ""

        # 특수 효과 상태
        self.effect_state: Dict[str, Any] = {}
        self.effect_timer: float = 0.0
        self.effect_duration: float = 2.0  # CUTSCENE 기본 지속 시간

        # 위임 효과 객체 (CUTSCENE 타입에서 사용)
        # PolaroidMemoryEffect, ClassifiedDocumentEffect, ShatteredMirrorEffect, StarMapEffect 등
        self.delegate_effect: Any = None

        # 음성 시스템
        self.voice_system = None

        # 콜백
        self.on_complete: Optional[Callable] = None

        # kwargs에서 추가 설정 가져오기
        self.narrative_type = kwargs.get('narrative_type', 'DIALOGUE')
        self.scene_id = kwargs.get('scene_id', '')

        super().__init__(engine)

    def get_config(self) -> ModeConfig:
        return NarrativeModeConfig()

    def init(self):
        """
        모드 초기화 (Graceful 에러 처리)

        - narrative_data 없어도 진행
        - JSON 로드 실패해도 진행
        - 대화 없으면 즉시 완료 (CUTSCENE 제외)
        """
        # shared_state에서 연출 데이터 가져오기 (안전한 접근)
        narrative_data = self.engine.shared_state.get("narrative_data", {})
        if not isinstance(narrative_data, dict):
            narrative_data = {}

        self.narrative_type = narrative_data.get("type", self.narrative_type)
        self.scene_id = narrative_data.get("scene_id", self.scene_id)
        self.dialogues = narrative_data.get("dialogues", [])
        self.background_path = narrative_data.get("background", "")
        self.title = narrative_data.get("title", "")
        self.location = narrative_data.get("location", "")
        self.color_tone = narrative_data.get("color_tone", "blue")
        self.effect_state = narrative_data.get("effects", {})

        # dialogues가 리스트인지 확인
        if not isinstance(self.dialogues, list):
            self.dialogues = []

        # JSON 파일에서 대화 로드 (scene_id가 있는 경우)
        if self.scene_id and not self.dialogues:
            self._load_scene_from_json()

        # 음성 시스템 초기화 (delegate effect 생성 전에 먼저 초기화)
        self._init_voice_system()

        # CUTSCENE 타입: 효과 클래스 위임 시도
        if self.narrative_type == "CUTSCENE":
            effect_created = self._create_delegate_effect()
            if effect_created:
                # 위임 효과가 생성되면 대화 진행 상태를 "delegate"로 설정
                self.dialogue_state = "delegate"
                print(f"INFO: CUTSCENE delegate effect created: {self.effect_state.get('type', 'unknown')}")
            elif not self.dialogues:
                # 효과도 없고 대화도 없으면 기본 CUTSCENE 동작
                print(f"INFO: CUTSCENE without dialogue - showing effect only")
                self.dialogues = []
        elif not self.dialogues:
            # CUTSCENE이 아닌데 대화 없으면 즉시 완료 (에러 아님)
            print(f"INFO: No dialogues for NarrativeMode (scene: {self.scene_id}), completing immediately")
            self._complete_narrative()
            return

        # 배경 로드 (실패해도 그라데이션 폴백) - 위임 효과가 없을 때만
        if not self.delegate_effect:
            self._load_background()

        # 색상 오버레이 생성 (REFLECTION 타입인 경우)
        if self.narrative_type == "REFLECTION":
            self._create_color_overlay()

        # 포트레이트 로드 (실패해도 계속 진행)
        self._load_portraits()

        # 커스텀 커서
        self.custom_cursor = self._load_base_cursor()

        # 대화 중 우주선 애니메이션 (DIALOGUE, BRIEFING 타입에서만)
        self.dialogue_ship_animation = None
        if self.narrative_type in ("DIALOGUE", "BRIEFING"):
            self._init_dialogue_ship_animation()

        # 대화 시작 (위임 효과가 없을 때만 intro로 설정)
        if self.dialogue_state != "delegate":
            self.dialogue_state = "intro"
        self.fade_alpha = 255

        print(f"INFO: NarrativeMode initialized - type: {self.narrative_type}, scene: {self.scene_id}, dialogues: {len(self.dialogues)}, state: {self.dialogue_state}")

    def _load_scene_from_json(self):
        """
        JSON 파일에서 장면 데이터 로드 (Graceful 에러 처리)

        우선순위:
        1. EpisodeResourceLoader (에피소드 기반 통합 JSON)
        2. DialogueLoader (레거시 개별 JSON 파일)

        - 파일 없어도 에러 없음 (빈 대화 반환)
        - 파싱 실패해도 에러 없음
        - dialogues 필드 없어도 에러 없음
        """
        # 1순위: EpisodeResourceLoader 시도
        episode_id = self.engine.shared_state.get("current_episode", "")
        if episode_id:
            try:
                from systems.episode_resource_loader import get_episode_loader
                loader = get_episode_loader()

                # 현재 에피소드 설정
                loader.set_episode(episode_id)

                # 장면 데이터 로드 (scene_id가 장면 이름)
                scene_data = loader.get_scene(self.scene_id)

                if scene_data and scene_data.get("dialogues"):
                    self.dialogues = scene_data.get("dialogues", [])
                    if not self.background_path:
                        self.background_path = loader.get_scene_background(self.scene_id)
                    if not self.title:
                        self.title = scene_data.get("title", "")
                    if not self.location:
                        self.location = scene_data.get("location", "")

                    print(f"INFO: Loaded scene from Episode '{episode_id}': {self.scene_id}, dialogues: {len(self.dialogues)}")
                    return
            except Exception as e:
                print(f"INFO: EpisodeResourceLoader failed for '{self.scene_id}': {e}")

        # 2순위: 레거시 DialogueLoader 폴백
        try:
            from systems.dialogue_loader import DialogueLoader

            scripts_path = config.ASSET_DIR / "data" / "episodes" / "ep1" / "scripts"

            loader = DialogueLoader(scripts_path)
            scene_data = loader.load_scene(self.scene_id)

            # scene_data는 항상 dict 반환 (DialogueLoader가 보장)
            if scene_data:
                self.dialogues = scene_data.get("dialogues", [])
                if not self.background_path:
                    self.background_path = scene_data.get("background", "")
                if not self.title:
                    self.title = scene_data.get("title", "")
                if not self.location:
                    self.location = scene_data.get("location", "")

                # dialogues가 비어있으면 정보 로그만 출력
                if self.dialogues:
                    print(f"INFO: Loaded scene from JSON: {self.scene_id}, dialogues: {len(self.dialogues)}")
                else:
                    print(f"INFO: Scene loaded but no dialogues: {self.scene_id}")

        except Exception as e:
            # 어떤 에러가 발생해도 조용히 처리
            print(f"INFO: Could not load scene '{self.scene_id}': {e} (continuing without dialogues)")

    def _load_background(self, bg_name: str = None):
        """
        배경 이미지 로드 (Graceful 에러 처리)

        우선순위:
        1. EpisodeResourceLoader (에피소드/shared 폴더)
        2. 레거시 경로 (story_mode/backgrounds 등)

        Args:
            bg_name: 로드할 배경 이름. None이면 self.background_path 사용
        """
        # 로드할 배경 결정
        target_bg = bg_name if bg_name else self.background_path

        if not target_bg:
            self._create_gradient_background()
            return

        # 이미 같은 배경이면 스킵
        if target_bg == self.current_bg_name and self.background:
            return

        # 1순위: EpisodeResourceLoader로 경로 해석
        episode_id = self.engine.shared_state.get("current_episode", "")
        if episode_id:
            try:
                from systems.episode_resource_loader import get_episode_loader
                loader = get_episode_loader()
                loader.set_episode(episode_id)

                # 에피소드 폴더 또는 shared 폴더에서 찾기
                resolved_path = loader.get_background(target_bg)
                if resolved_path and resolved_path.exists():
                    from asset_manager import AssetManager
                    self.background = AssetManager.get_image(resolved_path, self.screen_size)
                    self.current_bg_name = target_bg
                    print(f"INFO: Background loaded from episode: {resolved_path}")
                    return
            except Exception as e:
                print(f"INFO: EpisodeResourceLoader background failed: {e}")

        # 2순위: 레거시 경로들 시도 (에피소드 시스템으로 업데이트됨)
        paths = [
            config.ASSET_DIR / "data" / "episodes" / "ep1" / "backgrounds" / target_bg,
            config.ASSET_DIR / "data" / "episodes" / "ep1" / "backgrounds" / "reflection" / target_bg,
            config.ASSET_DIR / "images" / "backgrounds" / target_bg,
        ]

        for path in paths:
            if path.exists():
                try:
                    from asset_manager import AssetManager
                    self.background = AssetManager.get_image(path, self.screen_size)
                    self.current_bg_name = target_bg
                    print(f"INFO: Background loaded from {path}")
                    return
                except Exception as e:
                    print(f"WARNING: Failed to load {path}: {e}")
                    continue

        # 폴백: 그라데이션 배경 (에러 없이 graceful 처리)
        print(f"INFO: Background not found: {target_bg}, using gradient")
        self._create_gradient_background()
        self.current_bg_name = ""  # 그라데이션은 이름 없음

    def _create_gradient_background(self):
        """폴백용 그라데이션 배경 생성"""
        self.background = pygame.Surface(self.screen_size)

        # 연출 타입에 따른 색상
        if self.narrative_type == "REFLECTION":
            top_color = (20, 20, 40)
            bottom_color = (40, 40, 80)
        elif self.narrative_type == "BRIEFING":
            top_color = (15, 25, 45)
            bottom_color = (35, 55, 85)
        else:
            top_color = (10, 15, 25)
            bottom_color = (25, 35, 55)

        # 그라데이션 그리기
        for y in range(self.screen_size[1]):
            ratio = y / self.screen_size[1]
            r = int(top_color[0] + (bottom_color[0] - top_color[0]) * ratio)
            g = int(top_color[1] + (bottom_color[1] - top_color[1]) * ratio)
            b = int(top_color[2] + (bottom_color[2] - top_color[2]) * ratio)
            pygame.draw.line(self.background, (r, g, b), (0, y), (self.screen_size[0], y))

    def _create_color_overlay(self):
        """색상 오버레이 생성 (REFLECTION 전용)"""
        self.color_overlay = pygame.Surface(self.screen_size, pygame.SRCALPHA)
        tone = self.COLOR_TONES.get(self.color_tone, self.COLOR_TONES["blue"])
        self.color_overlay.fill(tone)

    def _load_portraits(self):
        """
        캐릭터 포트레이트 로드 (레거시 크기 200x200px)

        우선순위:
        1. EpisodeResourceLoader (에피소드/shared 폴더)
        2. 레거시 경로 (story_mode/portraits)
        """
        portrait_names = ["artemis", "pilot", "android", "narrator"]

        # 레거시 크기 (StoryMode와 동일)
        target_size = (200, 200)

        # EpisodeResourceLoader 준비
        episode_loader = None
        episode_id = self.engine.shared_state.get("current_episode", "")
        if episode_id:
            try:
                from systems.episode_resource_loader import get_episode_loader
                episode_loader = get_episode_loader()
                episode_loader.set_episode(episode_id)
            except Exception:
                pass

        for name in portrait_names:
            try:
                loaded = False

                # 1순위: EpisodeResourceLoader
                if episode_loader:
                    for ext in [".png", ".jpg"]:
                        resolved_path = episode_loader.get_portrait(f"portrait_{name}{ext}")
                        if resolved_path and resolved_path.exists():
                            portrait = pygame.image.load(str(resolved_path)).convert_alpha()
                            self.portraits[name.upper()] = pygame.transform.smoothscale(portrait, target_size)
                            loaded = True
                            print(f"INFO: Loaded portrait {name.upper()} from episode: {resolved_path}")
                            break

                # 2순위: 레거시 경로 (에피소드 시스템으로 업데이트됨)
                if not loaded:
                    paths = [
                        config.ASSET_DIR / "data" / "episodes" / "ep1" / "portraits" / f"portrait_{name}.png",
                        config.ASSET_DIR / "data" / "episodes" / "ep1" / "portraits" / f"portrait_{name}.jpg",
                    ]

                    for path in paths:
                        if path.exists():
                            portrait = pygame.image.load(str(path)).convert_alpha()
                            self.portraits[name.upper()] = pygame.transform.smoothscale(portrait, target_size)
                            loaded = True
                            print(f"INFO: Loaded portrait {name.upper()} from legacy: {path}")
                            break

                if not loaded:
                    print(f"WARNING: Portrait not found for {name.upper()}")
            except Exception as e:
                print(f"ERROR: Failed to load portrait {name.upper()}: {e}")

        # NARRATOR는 ANDROID 이미지 사용
        if "ANDROID" in self.portraits:
            self.portraits["NARRATOR"] = self.portraits["ANDROID"]
            print(f"INFO: Mapped portrait NARRATOR → ANDROID")

    def _init_voice_system(self):
        """음성 시스템 초기화"""
        print("DEBUG: _init_voice_system called")
        try:
            from systems.voice_system import VoiceSystem, EdgeTTSAdapter, Pyttsx3Adapter, SilentAdapter
            from mode_configs import config_story_dialogue

            # 음성 설정 가져오기
            voice_settings = config_story_dialogue.VOICE_SYSTEM_SETTINGS
            char_voice_settings = config_story_dialogue.CHARACTER_VOICE_SETTINGS

            print(f"DEBUG: voice_settings enabled={voice_settings.get('enabled', False)}")
            if not voice_settings.get("enabled", False):
                self.voice_system = None
                print("DEBUG: Voice system disabled by config")
                return

            # VoiceSystem 생성
            self.voice_system = VoiceSystem(
                enabled=True,
                default_adapter=voice_settings.get("default_adapter", "edge")
            )

            # 캐릭터별 음성 어댑터 등록
            for char_id, settings in char_voice_settings.items():
                adapter_type = settings.get("adapter", "edge")

                if adapter_type == "edge":
                    adapter = EdgeTTSAdapter(
                        voice=settings.get("voice", "ko-KR-SunHiNeural"),
                        rate=settings.get("rate", "+0%"),
                        pitch=settings.get("pitch", "+0Hz"),
                        style=settings.get("style"),
                        style_degree=settings.get("style_degree", 1.0),
                        auto_emotion=settings.get("auto_emotion", True),
                        static_effect=settings.get("static_effect", False)
                    )
                elif adapter_type == "pyttsx3":
                    adapter = Pyttsx3Adapter(
                        rate=settings.get("rate", 150),
                        volume=settings.get("volume", 1.0)
                    )
                else:
                    adapter = SilentAdapter()

                self.voice_system.register_character(char_id, adapter)

            # 음성 시스템 시작
            self.voice_system.start()
            print(f"INFO: NarrativeMode voice system initialized - system={self.voice_system is not None}")

        except ImportError as e:
            print(f"WARNING: Voice system not available: {e}")
            self.voice_system = None
        except Exception as e:
            print(f"WARNING: Voice system init failed: {e}")
            self.voice_system = None

    def _init_dialogue_ship_animation(self):
        """대화 중 우주선 회전 애니메이션 초기화"""
        try:
            from effects.game_animations import DialogueShipAnimation
            import config

            # 현재 선택된 우주선 가져오기
            current_ship = self.engine.shared_state.get('current_ship', config.DEFAULT_SHIP)

            # 우주선 데이터에서 이미지 파일명 가져오기
            ship_data = config.SHIP_TYPES.get(current_ship, config.SHIP_TYPES[config.DEFAULT_SHIP])
            ship_image_filename = ship_data.get('image', 'player_ship.png')

            # 우주선 이미지 경로 구성
            ship_image_path = config.IMAGE_DIR / "ships" / ship_image_filename

            # 플레이어 우주선 이미지 로드
            ship_image = pygame.image.load(str(ship_image_path)).convert_alpha()

            # 대화 중 우주선 애니메이션 생성 (135% 크기, 중간 타원 궤도)
            self.dialogue_ship_animation = DialogueShipAnimation(
                player_image=ship_image,
                screen_size=self.screen_size,
                scale=1.35  # 120-150% 범위에서 135% 선택
            )
            print(f"INFO: Dialogue ship animation initialized with {current_ship} ({ship_image_filename})")
        except Exception as e:
            print(f"WARNING: Failed to initialize dialogue ship animation: {e}")
            self.dialogue_ship_animation = None

    def _speak_dialogue(self, speaker: str, text: str):
        """대사 음성 재생"""
        if self.voice_system and self.voice_system.enabled:
            # 괄호 안의 독백/생각은 괄호 제거
            clean_text = text
            if text.startswith("(") and ")" in text:
                clean_text = text.strip("()")
            self.voice_system.speak(speaker, clean_text)

    def _skip_voice(self):
        """현재 음성 스킵"""
        if self.voice_system:
            self.voice_system.skip_current()

    def _cleanup_voice_system(self):
        """음성 시스템 정리"""
        if self.voice_system:
            self.voice_system.stop()
            self.voice_system = None

    def _complete_narrative(self):
        """연출 완료"""
        # 음성 시스템 정리
        self._cleanup_voice_system()

        # 본 씬 기록
        if self.scene_id:
            seen = self.engine.shared_state.get("seen_narratives", [])
            if self.scene_id not in seen:
                seen.append(self.scene_id)
                self.engine.shared_state["seen_narratives"] = seen

        # 콜백 호출
        if self.on_complete:
            self.on_complete()

        # 상위 모드로 복귀
        self.request_pop_mode({
            "narrative_complete": True,
            "scene_id": self.scene_id,
            "narrative_type": self.narrative_type
        })

    # =========================================================
    # 게임 루프
    # =========================================================

    def update(self, dt: float, current_time: float):
        """업데이트"""
        self.time_elapsed += dt

        # 대화 중 우주선 애니메이션 업데이트
        if self.dialogue_ship_animation:
            self.dialogue_ship_animation.update(dt)

        # 배경 미세 움직임 (REFLECTION 타입)
        if self.narrative_type == "REFLECTION":
            self.background_offset = math.sin(self.time_elapsed * 0.3) * 10

        # 대화 상태별 업데이트
        if self.dialogue_state == "intro":
            self._update_intro(dt)
        elif self.dialogue_state == "delegate":
            self._update_delegate(dt)
        elif self.dialogue_state == "typing":
            self._update_typing(dt)
        elif self.dialogue_state == "waiting":
            self._update_waiting(dt)
        elif self.dialogue_state == "cutscene_effect":
            self._update_cutscene_effect(dt)
        elif self.dialogue_state == "outro":
            self._update_outro(dt)

    def _update_intro(self, dt: float):
        """인트로 페이드 인"""
        fade_speed = 200 if self.narrative_type != "REFLECTION" else 150
        self.fade_alpha = max(0, self.fade_alpha - int(dt * fade_speed))

        if self.narrative_type == "REFLECTION":
            self.overlay_alpha = min(80, self.overlay_alpha + int(dt * 100))

        if self.fade_alpha <= 0:
            # CUTSCENE이고 대화가 없으면 일정 시간 후 자동 완료
            if self.narrative_type == "CUTSCENE" and not self.dialogues:
                self.dialogue_state = "cutscene_effect"
                self.effect_timer = 0.0
                self.effect_duration = self.effect_state.get("duration", 2.0)
            else:
                self.dialogue_state = "typing"
                self._start_dialogue()

    def _update_typing(self, dt: float):
        """타이핑 효과 (Graceful 에러 처리)"""
        # 범위 체크
        if self.current_dialogue_index >= len(self.dialogues):
            self.dialogue_state = "outro"
            return

        # 안전한 대화 접근
        current = self.dialogues[self.current_dialogue_index]
        if not isinstance(current, dict):
            current = EMPTY_DIALOGUE

        full_text = current.get("text", "...")  # 텍스트 없으면 "..." 표시

        self.char_timer += dt
        chars_per_second = 30  # StoryBriefingEffect와 동일한 타이핑 속도

        while self.char_timer >= 1.0 / chars_per_second and self.char_index < len(full_text):
            self.char_timer -= 1.0 / chars_per_second
            self.char_index += 1

        self.displayed_text = full_text[:self.char_index]

        if self.char_index >= len(full_text):
            self.dialogue_state = "waiting"
            self.wait_timer = 0

    def _update_waiting(self, dt: float):
        """
        클릭 대기 (또는 자동 진행)

        StoryBriefingEffect와 동일한 방식:
        1. 음성 시스템이 있으면 음성 재생 완료 대기
        2. 음성 완료 후 auto_advance_delay(0.5초) 대기
        3. 음성 시스템이 없으면 텍스트 길이 기반 대기
        """
        self.wait_timer += dt

        # 자동 진행
        if self.auto_advance:
            # 음성 시스템이 있으면 음성 재생 완료 확인
            if self.voice_system:
                if not self.voice_system.is_speaking():
                    # 음성 재생 완료
                    if not self.voice_finished:
                        self.voice_finished = True
                        self.auto_advance_timer = 0.0  # 음성 완료 시점부터 타이머 시작
                    else:
                        self.auto_advance_timer += dt
                        if self.auto_advance_timer >= self.auto_advance_delay:
                            self._advance_dialogue()
            else:
                # 음성 시스템이 없으면 텍스트 길이 기반 대기 (글자당 0.05초 + 0.5초)
                current_text = self.current_text or ""
                estimated_duration = len(current_text) * 0.05 + 0.5
                self.auto_advance_timer += dt
                if self.auto_advance_timer >= estimated_duration:
                    self._advance_dialogue()

    def _update_cutscene_effect(self, dt: float):
        """CUTSCENE 효과 표시 (대화 없을 때)"""
        self.effect_timer += dt
        if self.effect_timer >= self.effect_duration:
            self.dialogue_state = "outro"

    def _update_outro(self, dt: float):
        """아웃트로 페이드 아웃"""
        fade_speed = 200 if self.narrative_type != "REFLECTION" else 150
        self.fade_alpha = min(255, self.fade_alpha + int(dt * fade_speed))

        if self.fade_alpha >= 255:
            self._complete_narrative()

    def _update_delegate(self, dt: float):
        """위임 효과 업데이트"""
        if not self.delegate_effect:
            self.dialogue_state = "outro"
            return

        # 위임 효과 업데이트
        # update() 중 콜백으로 delegate_effect가 None이 될 수 있음
        effect = self.delegate_effect
        try:
            effect.update(dt)
        except Exception as e:
            print(f"WARNING: Delegate effect update error: {e}")
            self.delegate_effect = None
            self.dialogue_state = "outro"
            return

        # 위임 효과 완료 체크 (콜백에서 이미 None 설정됐을 수 있음)
        if self.delegate_effect is None:
            # 콜백에서 이미 처리됨 (dialogue_state도 이미 outro로 설정됨)
            return

        # is_alive 체크 (속성 없으면 True로 간주)
        is_alive = getattr(effect, 'is_alive', True)
        if not is_alive:
            print("INFO: Delegate effect completed (is_alive=False)")
            self.delegate_effect = None
            self.dialogue_state = "outro"

    # =========================================================
    # 위임 효과 (CUTSCENE) 생성
    # =========================================================

    def _create_delegate_effect(self) -> bool:
        """
        CUTSCENE 효과 클래스 생성 (위임 패턴)

        지원하는 효과:
        - PolaroidMemoryEffect: 폴라로이드 회상 (Act 1)
        - ClassifiedDocumentEffect: 기밀 문서 (Act 2)
        - FilmReelEffect: 손상된 홀로그램 (Act 3)
        - ShatteredMirrorEffect: 깨진 거울 (Act 4)
        - StarMapEffect: 별의 지도 (Act 5)

        Returns:
            True: 효과 생성 성공
            False: 효과 없음 또는 생성 실패
        """
        effect_type = self.effect_state.get("type", "")
        if not effect_type:
            return False

        print(f"INFO: Creating delegate effect: {effect_type}")

        try:
            # 에피소드 리소스 로더 준비
            episode_id = self.engine.shared_state.get("current_episode", "")
            episode_loader = None
            if episode_id:
                try:
                    from systems.episode_resource_loader import get_episode_loader
                    episode_loader = get_episode_loader()
                    episode_loader.set_episode(episode_id)
                except Exception as e:
                    print(f"WARNING: Failed to get episode loader: {e}")

            # 효과 데이터 (extra에서 effect_data 가져오기)
            effect_data = self.effect_state.get("effect_data", {})

            # 효과 타입별 생성
            if effect_type == "PolaroidMemoryEffect":
                return self._create_polaroid_effect(episode_loader, effect_data)
            elif effect_type == "ClassifiedDocumentEffect":
                return self._create_document_effect(episode_loader, effect_data)
            elif effect_type in ("FilmReelEffect", "DamagedHologramEffect"):
                return self._create_hologram_effect(episode_loader, effect_data)
            elif effect_type == "ShatteredMirrorEffect":
                return self._create_mirror_effect(episode_loader, effect_data)
            elif effect_type == "StarMapEffect":
                return self._create_starmap_effect(episode_loader, effect_data)
            else:
                print(f"WARNING: Unknown effect type: {effect_type}")
                return False

        except Exception as e:
            print(f"ERROR: Failed to create delegate effect: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _resolve_image_paths(self, image_names: list, episode_loader, subfolder: str = "effects") -> list:
        """이미지 경로 해석 (에피소드 폴더 → shared → 레거시)"""
        resolved = []
        for name in image_names:
            path = None

            # 1순위: 에피소드 리소스 로더
            if episode_loader:
                path = episode_loader.get_effect(name)
                if path and path.exists():
                    resolved.append(str(path))
                    continue

            # 2순위: 레거시 경로들 (cutscene_images로 통합됨)
            legacy_paths = [
                config.ASSET_DIR / "data" / "episodes" / "ep1" / "cutscene_images" / name,
                config.ASSET_DIR / "images" / "effects" / name,
            ]
            for lp in legacy_paths:
                if lp.exists():
                    resolved.append(str(lp))
                    break
            else:
                # 찾지 못하면 원본 이름 그대로 (효과 클래스에서 처리)
                resolved.append(name)

        return resolved

    def _resolve_background_path(self, bg_name: str, episode_loader) -> str:
        """배경 경로 해석"""
        if not bg_name:
            return ""

        # 1순위: 에피소드 리소스 로더
        if episode_loader:
            path = episode_loader.get_background(bg_name)
            if path and path.exists():
                return str(path)

        # 2순위: 레거시 경로들
        legacy_paths = [
            config.ASSET_DIR / "data" / "episodes" / "ep1" / "backgrounds" / bg_name,
            config.ASSET_DIR / "images" / "backgrounds" / bg_name,
        ]
        for lp in legacy_paths:
            if lp.exists():
                return str(lp)

        return bg_name

    def _create_polaroid_effect(self, episode_loader, effect_data: dict) -> bool:
        """PolaroidMemoryEffect 생성"""
        from cutscenes.memory_effects import PolaroidMemoryEffect

        # 이미지 경로 해석
        polaroid_images = effect_data.get("polaroid_images", [])
        if not polaroid_images:
            print("WARNING: No polaroid images specified")
            return False

        photo_paths = self._resolve_image_paths(polaroid_images, episode_loader)

        # 배경 경로
        bg_path = self._resolve_background_path(self.background_path, episode_loader)

        # 특수 효과
        special_effects = effect_data.get("special_effects", {})

        # 효과 생성
        self.delegate_effect = PolaroidMemoryEffect(
            screen_size=self.screen_size,
            photo_paths=photo_paths,
            background_path=bg_path,
            dialogue_after=[],  # 모든 사진 후 대화는 사용 안 함
            dialogue_per_photo=self.dialogues,  # 각 사진 등장 시 대화 표시
            sound_manager=getattr(self, 'sound_manager', None),
            special_effects=special_effects,
            scene_id=self.scene_id,
            voice_system=getattr(self, 'voice_system', None)  # 음성 시스템 전달
        )

        # 폰트 설정
        if self.fonts:
            self.delegate_effect.set_fonts(self.fonts)

        # 완료 콜백 설정
        self.delegate_effect.on_complete = self._on_delegate_complete

        return True

    def _create_document_effect(self, episode_loader, effect_data: dict) -> bool:
        """ClassifiedDocumentEffect 생성"""
        from cutscenes.document_effects import ClassifiedDocumentEffect

        # 문서 이미지 경로
        document_images = effect_data.get("document_images", [])
        document_paths = self._resolve_image_paths(document_images, episode_loader)

        # gate 이미지 경로
        gate_images = effect_data.get("gate_images", [])
        gate_paths = self._resolve_image_paths(gate_images, episode_loader)

        # 배경 경로
        bg_path = self._resolve_background_path(self.background_path, episode_loader)

        # 효과 생성
        self.delegate_effect = ClassifiedDocumentEffect(
            screen_size=self.screen_size,
            document_paths=document_paths,
            background_path=bg_path,
            dialogue_after=self.dialogues,
            sound_manager=getattr(self, 'sound_manager', None),
            special_effects=effect_data.get("special_effects", {}),
            scene_id=self.scene_id,
            gate_image_paths=gate_paths if gate_paths else None
        )

        # 폰트 설정
        if self.fonts:
            self.delegate_effect.set_fonts(self.fonts)

        # 완료 콜백 설정
        self.delegate_effect.on_complete = self._on_delegate_complete

        return True

    def _create_hologram_effect(self, episode_loader, effect_data: dict) -> bool:
        """FilmReelEffect (DamagedHologramEffect) 생성"""
        from cutscenes.document_effects import FilmReelEffect

        # 홀로그램 이미지 경로
        hologram_images = effect_data.get("hologram_images", [])
        hologram_paths = self._resolve_image_paths(hologram_images, episode_loader)

        # 배경 경로
        bg_path = self._resolve_background_path(self.background_path, episode_loader)

        # 효과 생성
        self.delegate_effect = FilmReelEffect(
            screen_size=self.screen_size,
            film_paths=hologram_paths,
            background_path=bg_path,
            dialogue_after=self.dialogues,
            sound_manager=getattr(self, 'sound_manager', None),
            special_effects=effect_data.get("special_effects", {}),
            scene_id=self.scene_id
        )

        # 폰트 설정
        if self.fonts:
            self.delegate_effect.set_fonts(self.fonts)

        # 완료 콜백 설정
        self.delegate_effect.on_complete = self._on_delegate_complete

        return True

    def _create_mirror_effect(self, episode_loader, effect_data: dict) -> bool:
        """ShatteredMirrorEffect 생성"""
        from cutscenes.memory_effects import ShatteredMirrorEffect

        # 파편 이미지 경로
        fragment_images = effect_data.get("fragment_images", [])
        fragment_paths = self._resolve_image_paths(fragment_images, episode_loader)

        # 배경 경로
        bg_path = self._resolve_background_path(self.background_path, episode_loader)

        # 효과 생성
        self.delegate_effect = ShatteredMirrorEffect(
            screen_size=self.screen_size,
            fragment_paths=fragment_paths,
            background_path=bg_path,
            dialogue_after=self.dialogues,
            sound_manager=getattr(self, 'sound_manager', None),
            special_effects=effect_data.get("special_effects", {}),
            scene_id=self.scene_id
        )

        # 폰트 설정
        if self.fonts:
            self.delegate_effect.set_fonts(self.fonts)

        # 완료 콜백 설정
        self.delegate_effect.on_complete = self._on_delegate_complete

        return True

    def _create_starmap_effect(self, episode_loader, effect_data: dict) -> bool:
        """StarMapEffect 생성"""
        from cutscenes.world_effects import StarMapEffect

        # 마커 이미지 경로
        marker_images = effect_data.get("marker_images", [])
        marker_paths = self._resolve_image_paths(marker_images, episode_loader)

        # 마커 위치
        marker_positions = effect_data.get("marker_positions", {})

        # 경로 순서
        route_order = effect_data.get("route_order", [])

        # 배경 경로
        bg_path = self._resolve_background_path(self.background_path, episode_loader)

        # 효과 생성
        self.delegate_effect = StarMapEffect(
            screen_size=self.screen_size,
            marker_paths=marker_paths,
            marker_positions=marker_positions,
            route_order=route_order,
            background_path=bg_path,
            dialogue_after=self.dialogues,
            sound_manager=getattr(self, 'sound_manager', None),
            special_effects=effect_data.get("special_effects", {}),
            scene_id=self.scene_id
        )

        # 폰트 설정
        if self.fonts:
            self.delegate_effect.set_fonts(self.fonts)

        # 완료 콜백 설정
        self.delegate_effect.on_complete = self._on_delegate_complete

        return True

    def _on_delegate_complete(self):
        """위임 효과 완료 콜백"""
        print("INFO: Delegate effect completed via callback")
        self.delegate_effect = None
        self.dialogue_state = "outro"

    def _start_dialogue(self):
        """
        대화 시작 (Graceful 에러 처리)

        - 인덱스 범위 초과 시 즉시 outro로 전환
        - 대화 데이터 필드 누락 시 기본값 사용
        - 배경 변경 실패해도 계속 진행
        """
        # 범위 체크 (Graceful 처리)
        if self.current_dialogue_index >= len(self.dialogues):
            print(f"INFO: Dialogue index out of range, transitioning to outro")
            self.dialogue_state = "outro"
            return

        # 현재 대화 가져오기 (안전한 접근)
        current = self.dialogues[self.current_dialogue_index]
        if not isinstance(current, dict):
            current = EMPTY_DIALOGUE

        # 필드 안전하게 추출 (누락 시 기본값)
        self.current_speaker = current.get("speaker", "UNKNOWN")
        self.current_text = current.get("text", "")
        self.char_index = 0
        self.displayed_text = ""
        self.auto_advance_timer = 0.0  # 타이머 리셋
        self.voice_finished = False  # 음성 완료 플래그 리셋

        # 대화별 배경 변경 (있는 경우)
        new_bg = current.get("background")
        if new_bg and new_bg != self.current_bg_name:
            self._load_background(new_bg)

        # 음성 재생
        text = current.get("text", "")
        if text and self.current_speaker:
            self._speak_dialogue(self.current_speaker, text)

    def _advance_dialogue(self):
        """다음 대화로 진행 (Graceful 에러 처리)"""
        # 자동 진행 타이머 및 플래그 리셋
        self.auto_advance_timer = 0.0
        self.voice_finished = False

        # 음성 스킵
        self._skip_voice()

        if self.dialogue_state == "typing":
            # 타이핑 중이면 즉시 완료 (안전한 접근)
            if self.current_dialogue_index < len(self.dialogues):
                current = self.dialogues[self.current_dialogue_index]
                if isinstance(current, dict):
                    self.displayed_text = current.get("text", "...")
                else:
                    self.displayed_text = "..."
            else:
                self.displayed_text = "..."
            self.char_index = len(self.displayed_text)
            self.dialogue_state = "waiting"
        elif self.dialogue_state == "waiting":
            # 다음 대화로
            self.current_dialogue_index += 1
            if self.current_dialogue_index >= len(self.dialogues):
                self.dialogue_state = "outro"
            else:
                self.dialogue_state = "typing"
                self._start_dialogue()

    # =========================================================
    # 렌더링
    # =========================================================

    def render(self, screen: pygame.Surface):
        """렌더링"""
        # 위임 효과가 있으면 위임 효과 렌더링
        if self.delegate_effect and self.dialogue_state == "delegate":
            # render() 또는 draw() 메서드 호출 (효과 클래스마다 다름)
            if hasattr(self.delegate_effect, 'render'):
                self.delegate_effect.render(screen)
            elif hasattr(self.delegate_effect, 'draw'):
                self.delegate_effect.draw(screen)
            return

        # 배경
        if self.background:
            if self.narrative_type == "REFLECTION":
                bg_rect = self.background.get_rect()
                bg_rect.centerx = self.screen_size[0] // 2 + int(self.background_offset)
                screen.blit(self.background, bg_rect)
            else:
                screen.blit(self.background, (0, 0))
        else:
            screen.fill((10, 10, 20))

        # 색상 오버레이 (REFLECTION 전용)
        if self.color_overlay and self.overlay_alpha > 0:
            overlay = self.color_overlay.copy()
            overlay.set_alpha(self.overlay_alpha)
            screen.blit(overlay, (0, 0))

        # 대화 중 우주선 애니메이션 (배경 후, UI 전)
        if self.dialogue_ship_animation and self.dialogue_state not in ("intro", "outro", "delegate"):
            self.dialogue_ship_animation.draw(screen)

        # 타이틀/위치 표시 (BRIEFING 타입)
        if self.narrative_type == "BRIEFING" and self.dialogue_state != "outro":
            self._render_briefing_header(screen)

        # 대화창 (render_dialogue_box가 포트레이트도 포함)
        if self.dialogue_state not in ("intro", "outro", "delegate"):
            self._render_dialogue(screen)

        # 페이드 효과
        if self.fade_alpha > 0:
            fade_surf = pygame.Surface(self.screen_size, pygame.SRCALPHA)
            fade_surf.fill((0, 0, 0, self.fade_alpha))
            screen.blit(fade_surf, (0, 0))

        # 힌트 텍스트
        if self.dialogue_state == "waiting":
            self._render_hint(screen)

        # 커스텀 커서
        self._render_base_cursor(screen, self.custom_cursor)

    def _render_briefing_header(self, screen: pygame.Surface):
        """브리핑 헤더 렌더링 (타이틀 + 위치)"""
        if not self.title and not self.location:
            return

        # 타이틀 표시 (화면 상단)
        y_offset = 60

        if self.title:
            title_font = self.fonts.get("large", self.fonts.get("medium"))
            title_surf = title_font.render(self.title, True, (255, 220, 100))
            title_rect = title_surf.get_rect(centerx=self.screen_size[0] // 2, y=y_offset)
            screen.blit(title_surf, title_rect)
            y_offset += 50

        if self.location:
            loc_font = self.fonts.get("medium", self.fonts.get("small"))
            loc_surf = loc_font.render(self.location, True, (150, 180, 220))
            loc_rect = loc_surf.get_rect(centerx=self.screen_size[0] // 2, y=y_offset)
            screen.blit(loc_surf, loc_rect)

    def _render_dialogue(self, screen: pygame.Surface):
        """대화창 렌더링 - render_dialogue_box 함수 사용 (인트로와 동일 포맷)"""
        from cutscenes.base import render_dialogue_box

        # 현재 대화 데이터 구성
        current_dialogue = {
            "speaker": self.current_speaker or "",
            "text": self.current_text or ""
        }

        # 현재 스피커의 포트레이트 가져오기
        portrait = None
        has_portrait = False
        if self.current_speaker:
            portrait_key = self.current_speaker.upper()
            if portrait_key in self.portraits:
                portrait = self.portraits[portrait_key]
                has_portrait = True
            else:
                # 디버그: 포트레이트가 없을 때만 출력 (한 번만)
                if not hasattr(self, '_missing_portraits'):
                    self._missing_portraits = set()
                if portrait_key not in self._missing_portraits:
                    self._missing_portraits.add(portrait_key)
                    print(f"DEBUG: Portrait not found for speaker '{portrait_key}'. Available: {list(self.portraits.keys())}")

        # 타이핑 진행률 계산
        typing_progress = len(self.displayed_text) if self.displayed_text else 0

        # 클릭 대기 여부 (자동 진행이 아닌 경우에만 표시)
        waiting_for_click = (self.dialogue_state == "waiting" and not self.auto_advance)

        # render_dialogue_box 호출 (인트로와 동일한 스타일)
        render_dialogue_box(
            screen=screen,
            screen_size=self.screen_size,
            fonts=self.fonts,
            dialogue=current_dialogue,
            dialogue_text=self.current_text or "",
            typing_progress=typing_progress,
            waiting_for_click=waiting_for_click,
            has_portrait=has_portrait,
            portrait=portrait
        )

    def _wrap_text(self, text: str, font: pygame.font.Font, max_width: int) -> List[str]:
        """텍스트 줄바꿈"""
        words = text.split(' ')
        lines = []
        current_line = ""

        for word in words:
            test_line = current_line + " " + word if current_line else word
            test_width = font.size(test_line)[0]
            if test_width <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word

        if current_line:
            lines.append(current_line)

        return lines

    def _render_hint(self, screen: pygame.Surface):
        """클릭 힌트 렌더링 (자동 진행 시 다른 메시지)"""
        font = self.fonts.get("tiny", self.fonts.get("small"))
        alpha = int(128 + 127 * math.sin(self.time_elapsed * 3))

        # 자동 진행 중이면 다른 메시지
        if self.auto_advance:
            # 진행 바 형태로 표시
            remaining = self.auto_advance_delay - self.auto_advance_timer
            if remaining > 0:
                progress = self.auto_advance_timer / self.auto_advance_delay
                hint_msg = f"자동 진행 중... (클릭으로 건너뛰기)"
            else:
                hint_msg = "계속..."
        else:
            hint_msg = "클릭하여 계속..."

        hint_text = font.render(hint_msg, True, (200, 200, 200))
        hint_text.set_alpha(alpha)
        screen.blit(hint_text, (self.screen_size[0] - 250, self.screen_size[1] - 50))

    def handle_event(self, event: pygame.event.Event):
        """이벤트 처리"""
        # 위임 효과가 있으면 위임 효과에 이벤트 전달
        if self.delegate_effect and self.dialogue_state == "delegate":
            if hasattr(self.delegate_effect, 'handle_event'):
                self.delegate_effect.handle_event(event)
            else:
                # 클릭 이벤트 처리 (handle_click 또는 on_click)
                is_click = (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1) or \
                           (event.type == pygame.KEYDOWN and event.key in (pygame.K_SPACE, pygame.K_RETURN))

                if is_click:
                    if hasattr(self.delegate_effect, 'handle_click'):
                        self.delegate_effect.handle_click()
                    elif hasattr(self.delegate_effect, 'on_click'):
                        pos = event.pos if hasattr(event, 'pos') else (0, 0)
                        self.delegate_effect.on_click(pos)

            # ESC로 스킵
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                if hasattr(self.delegate_effect, 'skip'):
                    self.delegate_effect.skip()
                else:
                    self.delegate_effect.is_alive = False
                self.dialogue_state = "outro"
            return

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                # 스킵 (바로 종료)
                self.dialogue_state = "outro"
                return

            if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                self._advance_dialogue()
                return

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                self._advance_dialogue()
                return

    # =========================================================
    # 라이프사이클
    # =========================================================

    def on_enter(self):
        super().on_enter()
        if self.custom_cursor:
            self._enable_custom_cursor()

    def on_exit(self):
        self._disable_custom_cursor()
        super().on_exit()


print("INFO: narrative_mode.py loaded")
