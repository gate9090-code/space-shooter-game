# modes/reflection_mode.py
"""
ReflectionMode - 철학적 성찰 씬 전용 모드
EARTH_BEAUTY_DIALOGUES, PHILOSOPHY_DIALOGUES 대화를 몽환적 분위기로 연출
"""

import pygame
import math
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

from modes.base_mode import GameMode, ModeConfig
import config


@dataclass
class ReflectionModeConfig(ModeConfig):
    """Reflection 모드 설정"""
    mode_name: str = "reflection"
    perspective_enabled: bool = False
    wave_system_enabled: bool = False
    spawn_system_enabled: bool = False
    show_wave_ui: bool = False


class ReflectionMode(GameMode):
    """
    철학적 성찰 모드

    특징:
    - 몽환적 배경 + 색상 오버레이
    - 천천히 진행되는 대화
    - 음성 동기화 (선택적)
    """

    # 색상 톤 매핑
    COLOR_TONES = {
        "sepia": (255, 240, 200, 60),     # 추억/향수
        "blue": (100, 150, 200, 80),      # 명상/성찰
        "purple": (150, 100, 200, 70),    # 신비/우주
        "gold": (255, 220, 100, 100),     # 깨달음
        "gray_blue": (150, 160, 180, 70), # 비 오는 날
    }

    def __init__(self, engine, scene_key: str = None, **kwargs):
        """
        Args:
            engine: 게임 엔진
            scene_key: 표시할 씬 키 (EARTH_BEAUTY_DIALOGUES 또는 PHILOSOPHY_DIALOGUES)
        """
        # 씬 정보 (shared_state에서 가져오거나 직접 지정)
        self.scene_key = scene_key
        self.scene_data: Dict = {}
        self.dialogues: List[Dict] = []

        # 대화 진행 상태
        self.current_dialogue_index: int = 0
        self.dialogue_state: str = "intro"  # intro, typing, waiting, outro
        self.displayed_text: str = ""
        self.char_index: int = 0
        self.char_timer: float = 0
        self.wait_timer: float = 0
        self.current_text: str = ""  # 현재 대화 텍스트

        # 자동 진행 (StoryBriefingEffect와 동일 방식)
        self.auto_advance: bool = True
        self.auto_advance_delay: float = 0.5  # 음성 완료 후 대기 시간
        self.auto_advance_timer: float = 0.0
        self.voice_finished: bool = False

        # 음성 시스템
        self.voice_system = None

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

        super().__init__(engine)

    def get_config(self) -> ModeConfig:
        return ReflectionModeConfig()

    def init(self):
        """모드 초기화"""
        # shared_state에서 씬 정보 가져오기
        reflection_scene = self.engine.shared_state.get("reflection_scene", {})

        if not self.scene_key:
            self.scene_key = reflection_scene.get("scene_key")

        if not self.scene_key:
            print("ERROR: No scene_key provided for ReflectionMode")
            self._complete_reflection()
            return

        # 씬 데이터 로드
        self._load_scene_data()

        if not self.dialogues:
            print(f"ERROR: No dialogues found for scene: {self.scene_key}")
            self._complete_reflection()
            return

        # 배경 로드
        self._load_background()

        # 오버레이 생성
        self._create_color_overlay()

        # 포트레이트 로드
        self._load_portraits()

        # 음성 시스템 초기화
        self._init_voice_system()

        # 커스텀 커서
        self.custom_cursor = self._load_base_cursor()

        # 대화 시작
        self.dialogue_state = "intro"
        self.fade_alpha = 255

        print(f"INFO: ReflectionMode initialized with scene: {self.scene_key}")

    def _load_scene_data(self):
        """씬 데이터 로드"""
        from mode_configs.config_story_dialogue import (
            EARTH_BEAUTY_DIALOGUES, PHILOSOPHY_DIALOGUES
        )

        # EARTH_BEAUTY_DIALOGUES에서 찾기
        if self.scene_key in EARTH_BEAUTY_DIALOGUES:
            self.scene_data = EARTH_BEAUTY_DIALOGUES[self.scene_key]
        # PHILOSOPHY_DIALOGUES에서 찾기
        elif self.scene_key in PHILOSOPHY_DIALOGUES:
            self.scene_data = PHILOSOPHY_DIALOGUES[self.scene_key]
        else:
            print(f"WARNING: Scene not found: {self.scene_key}")
            return

        self.dialogues = self.scene_data.get("dialogues", [])

    def _load_background(self):
        """배경 이미지 로드"""
        from pathlib import Path

        bg_name = self.scene_data.get("background", "")

        if not bg_name:
            self._create_gradient_background()
            return

        # 여러 경로 시도 (에피소드 시스템)
        paths = [
            f"assets/data/episodes/ep1/backgrounds/reflection/{bg_name}",
            f"assets/data/episodes/ep1/backgrounds/{bg_name}",
            f"assets/backgrounds/{bg_name}",
        ]

        for path_str in paths:
            path = Path(path_str)
            if path.exists():
                try:
                    # AssetManager.get_image 사용 (클래스 메서드)
                    from asset_manager import AssetManager
                    self.background = AssetManager.get_image(path, self.screen_size)
                    print(f"INFO: Background loaded from {path}")
                    return
                except Exception as e:
                    print(f"WARNING: Failed to load {path}: {e}")
                    continue

        # 폴백: 그라데이션 배경
        print(f"WARNING: Background not found for {bg_name}, using gradient")
        self._create_gradient_background()

    def _create_gradient_background(self):
        """폴백용 그라데이션 배경 생성"""
        self.background = pygame.Surface(self.screen_size)

        # 씬 키에 따른 색상
        if "spring" in self.scene_key or "color" in self.scene_key or "flower" in self.scene_key:
            top_color = (60, 20, 40)
            bottom_color = (120, 60, 80)
        elif "summer" in self.scene_key or "cloud" in self.scene_key:
            top_color = (20, 40, 80)
            bottom_color = (60, 100, 140)
        elif "autumn" in self.scene_key or "rain" in self.scene_key:
            top_color = (40, 40, 50)
            bottom_color = (80, 70, 60)
        elif "winter" in self.scene_key or "star" in self.scene_key:
            top_color = (10, 10, 30)
            bottom_color = (30, 30, 60)
        elif "andromeda" in self.scene_key:
            top_color = (40, 20, 60)
            bottom_color = (80, 40, 100)
        else:
            top_color = (20, 20, 40)
            bottom_color = (40, 40, 80)

        # 그라데이션 그리기
        for y in range(self.screen_size[1]):
            ratio = y / self.screen_size[1]
            r = int(top_color[0] + (bottom_color[0] - top_color[0]) * ratio)
            g = int(top_color[1] + (bottom_color[1] - top_color[1]) * ratio)
            b = int(top_color[2] + (bottom_color[2] - top_color[2]) * ratio)
            pygame.draw.line(self.background, (r, g, b), (0, y), (self.screen_size[0], y))

    def _create_color_overlay(self):
        """색상 오버레이 생성"""
        self.color_overlay = pygame.Surface(self.screen_size, pygame.SRCALPHA)

        # 씬 키에 따른 색상 톤
        if "spring" in self.scene_key or "color" in self.scene_key or "flower" in self.scene_key:
            tone = self.COLOR_TONES["sepia"]
        elif "rain" in self.scene_key:
            tone = self.COLOR_TONES["gray_blue"]
        elif "star" in self.scene_key or "winter" in self.scene_key:
            tone = self.COLOR_TONES["blue"]
        elif "andromeda" in self.scene_key:
            tone = self.COLOR_TONES["purple"]
        elif "chaos" in self.scene_key or "eternity" in self.scene_key:
            tone = self.COLOR_TONES["gold"]
        else:
            tone = self.COLOR_TONES["blue"]

        self.color_overlay.fill(tone)

    def _load_portraits(self):
        """캐릭터 포트레이트 로드"""
        portrait_names = ["artemis", "pilot", "android"]
        for name in portrait_names:
            try:
                path = f"assets/data/episodes/ep1/portraits/portrait_{name}.png"
                portrait = self.asset_manager.load_image(path)
                if portrait:
                    # 크기 조정
                    height = int(self.screen_size[1] * 0.4)
                    width = int(portrait.get_width() * (height / portrait.get_height()))
                    self.portraits[name.upper()] = pygame.transform.scale(portrait, (width, height))
            except:
                pass

    def _init_voice_system(self):
        """음성 시스템 초기화"""
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

            self.voice_system.start()
            print("INFO: ReflectionMode voice system initialized")

        except ImportError as e:
            print(f"WARNING: Voice system not available: {e}")
            self.voice_system = None
        except Exception as e:
            print(f"WARNING: Voice system init failed: {e}")
            self.voice_system = None

    def _speak_dialogue(self, speaker: str, text: str):
        """대사 음성 재생"""
        if self.voice_system and self.voice_system.enabled:
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

    def _complete_reflection(self):
        """성찰 씬 완료"""
        # 음성 시스템 정리
        self._cleanup_voice_system()

        # 본 씬 기록
        seen = self.engine.shared_state.get("seen_reflections", [])
        if self.scene_key and self.scene_key not in seen:
            seen.append(self.scene_key)
            self.engine.shared_state["seen_reflections"] = seen

        # EpisodeMode로 복귀
        self.request_pop_mode({
            "reflection_complete": True,
            "scene_key": self.scene_key
        })

    # =========================================================
    # 게임 루프
    # =========================================================

    def update(self, dt: float, current_time: float):
        """업데이트"""
        self.time_elapsed += dt

        # 배경 미세 움직임
        self.background_offset = math.sin(self.time_elapsed * 0.3) * 10

        # 대화 상태별 업데이트
        if self.dialogue_state == "intro":
            self._update_intro(dt)
        elif self.dialogue_state == "typing":
            self._update_typing(dt)
        elif self.dialogue_state == "waiting":
            self._update_waiting(dt)
        elif self.dialogue_state == "outro":
            self._update_outro(dt)

    def _update_intro(self, dt: float):
        """인트로 페이드 인"""
        self.fade_alpha = max(0, self.fade_alpha - int(dt * 200))
        self.overlay_alpha = min(80, self.overlay_alpha + int(dt * 100))

        if self.fade_alpha <= 0:
            self.dialogue_state = "typing"
            self._start_dialogue()

    def _update_typing(self, dt: float):
        """타이핑 효과"""
        if self.current_dialogue_index >= len(self.dialogues):
            self.dialogue_state = "outro"
            return

        current = self.dialogues[self.current_dialogue_index]
        full_text = current.get("text", "")

        self.char_timer += dt
        chars_per_second = 30  # 타이핑 속도

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

        if self.auto_advance:
            if self.voice_system:
                if not self.voice_system.is_speaking():
                    if not self.voice_finished:
                        self.voice_finished = True
                        self.auto_advance_timer = 0.0
                    else:
                        self.auto_advance_timer += dt
                        if self.auto_advance_timer >= self.auto_advance_delay:
                            self._advance_dialogue()
            else:
                current_text = self.current_text or ""
                estimated_duration = len(current_text) * 0.05 + 0.5
                self.auto_advance_timer += dt
                if self.auto_advance_timer >= estimated_duration:
                    self._advance_dialogue()

    def _update_outro(self, dt: float):
        """아웃트로 페이드 아웃"""
        self.fade_alpha = min(255, self.fade_alpha + int(dt * 200))

        if self.fade_alpha >= 255:
            self._complete_reflection()

    def _start_dialogue(self):
        """대화 시작"""
        if self.current_dialogue_index < len(self.dialogues):
            current = self.dialogues[self.current_dialogue_index]
            self.current_speaker = current.get("speaker", "")
            self.current_text = current.get("text", "")
            self.char_index = 0
            self.displayed_text = ""
            self.auto_advance_timer = 0.0
            self.voice_finished = False

            # 음성 재생
            if self.current_text and self.current_speaker:
                self._speak_dialogue(self.current_speaker, self.current_text)

    def _advance_dialogue(self):
        """다음 대화로 진행"""
        # 타이머 및 플래그 리셋
        self.auto_advance_timer = 0.0
        self.voice_finished = False

        # 음성 스킵
        self._skip_voice()

        if self.dialogue_state == "typing":
            # 타이핑 중이면 즉시 완료
            current = self.dialogues[self.current_dialogue_index]
            self.displayed_text = current.get("text", "")
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
        # 배경 (미세 움직임 적용)
        if self.background:
            bg_rect = self.background.get_rect()
            bg_rect.centerx = self.screen_size[0] // 2 + int(self.background_offset)
            screen.blit(self.background, bg_rect)
        else:
            screen.fill((10, 10, 20))

        # 색상 오버레이
        if self.color_overlay and self.overlay_alpha > 0:
            overlay = self.color_overlay.copy()
            overlay.set_alpha(self.overlay_alpha)
            screen.blit(overlay, (0, 0))

        # 대화창 (render_dialogue_box가 포트레이트도 포함)
        # Note: _render_portrait 호출 제거 - render_dialogue_box에서 이미 포트레이트 렌더링
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

    def _render_portrait(self, screen: pygame.Surface):
        """캐릭터 포트레이트 렌더링"""
        if not self.current_speaker:
            return

        # 스피커 이름 매핑
        portrait_key = self.current_speaker

        if portrait_key not in self.portraits:
            return

        portrait = self.portraits[portrait_key]

        # 위치 (화면 왼쪽 또는 오른쪽)
        if self.current_speaker == "ARTEMIS":
            x = 50
        else:
            x = self.screen_size[0] - portrait.get_width() - 50

        y = self.screen_size[1] - portrait.get_height() - 150

        # 약간의 투명도
        portrait_copy = portrait.copy()
        portrait_copy.set_alpha(200)
        screen.blit(portrait_copy, (x, y))

    def _render_dialogue(self, screen: pygame.Surface):
        """대화창 렌더링 - render_dialogue_box 함수 사용 (인트로와 동일 포맷)"""
        if self.dialogue_state == "intro" or self.dialogue_state == "outro":
            return

        from cutscenes.base import render_dialogue_box

        # 현재 대화 데이터 구성
        current_dialogue = {
            "speaker": self.current_speaker or "",
            "text": self.current_text or ""
        }

        # 현재 스피커의 포트레이트 가져오기
        portrait = None
        has_portrait = False
        if self.current_speaker and self.current_speaker in self.portraits:
            portrait = self.portraits[self.current_speaker]
            has_portrait = True

        # 타이핑 진행률 계산
        typing_progress = len(self.displayed_text) if self.displayed_text else 0

        # render_dialogue_box 호출 (인트로와 동일한 스타일)
        render_dialogue_box(
            screen=screen,
            screen_size=self.screen_size,
            fonts=self.fonts,
            dialogue=current_dialogue,
            dialogue_text=self.current_text or "",
            typing_progress=typing_progress,
            _waiting_for_click=False,
            has_portrait=has_portrait,
            portrait=portrait
        )

    def _render_hint(self, screen: pygame.Surface):
        """클릭 힌트 렌더링"""
        font = self.fonts.get("tiny", self.fonts.get("small"))
        alpha = int(128 + 127 * math.sin(self.time_elapsed * 3))
        hint_text = font.render("클릭하여 계속...", True, (200, 200, 200))
        hint_text.set_alpha(alpha)
        screen.blit(hint_text, (self.screen_size[0] - 180, self.screen_size[1] - 50))

    def handle_event(self, event: pygame.event.Event):
        """이벤트 처리"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                # 스킵 확인 (선택적 씬인 경우)
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


print("INFO: reflection_mode.py loaded")
