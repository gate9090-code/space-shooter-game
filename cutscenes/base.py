"""
cutscenes/base.py
Base class and helper functions for all cutscene effects
"""

import pygame
import math
from typing import Tuple, List, Callable, Dict, Optional


# =========================================================
# 공통 베이스 클래스: 컷씬 효과용
# =========================================================
class BaseCutsceneEffect:
    """
    모든 컷씬 효과 클래스의 공통 베이스 클래스

    공통 기능:
    - 페이즈 관리 (FADEIN, DISPLAY, DIALOGUE, FADEOUT, DONE)
    - 배경 이미지 로딩
    - 대화 시스템 (타이핑 효과, 클릭 진행)
    - 페이드 인/아웃
    - 이벤트 처리
    - 폰트 관리
    """

    # 공통 페이즈 상수
    PHASE_FADEIN = 0
    PHASE_DISPLAY = 1
    PHASE_DIALOGUE = 2
    PHASE_FADEOUT = 3
    PHASE_DONE = 4

    def __init__(
        self,
        screen_size: tuple,
        background_path: str = None,
        dialogue_after: list = None,
        sound_manager=None,
        special_effects: dict = None,
        scene_id: str = "base_scene",
    ):
        """
        Args:
            screen_size: 화면 크기 (width, height)
            background_path: 배경 이미지 경로
            dialogue_after: 대사 리스트 [{"speaker": "...", "text": "..."}, ...]
            sound_manager: 효과음 재생용
            special_effects: 특수 효과 설정
            scene_id: 씬 식별자 (리플레이용)
        """
        self.screen_size = screen_size
        self.background_path = background_path
        self.dialogue_after = dialogue_after or []
        self.sound_manager = sound_manager
        self.special_effects = special_effects or {}
        self.scene_id = scene_id

        self.is_alive = True
        self.phase = self.PHASE_FADEIN
        self.phase_timer = 0.0

        # 페이드 설정
        self.fadein_duration = 1.5
        self.fadeout_duration = 1.5
        self.fade_alpha = 0.0

        # 배경
        self.background = None
        if background_path:
            self._load_background(background_path)

        # 대화 관련
        self.current_dialogue_index = 0
        self.dialogue_text = ""
        self.typing_progress = 0.0
        self.typing_speed = 30.0
        self.waiting_for_click = False

        # 초상화 캐시
        self.portrait_cache = {}

        # 폰트
        self.fonts = {}

        # 콜백
        self.on_complete = None
        self.on_replay_request = None

    def _load_background(self, path: str, overlay_alpha: int = 0):
        """
        배경 이미지 로드

        Args:
            path: 이미지 경로
            overlay_alpha: 어두운 오버레이 알파값 (0=없음, 220=어둡게)
        """
        try:
            img = pygame.image.load(path).convert()
            self.background = pygame.transform.smoothscale(img, self.screen_size)

            if overlay_alpha > 0:
                overlay = pygame.Surface(self.screen_size, pygame.SRCALPHA)
                overlay.fill((0, 0, 0, overlay_alpha))
                self.background.blit(overlay, (0, 0))
        except Exception as e:
            print(f"WARNING: Failed to load background: {path} - {e}")
            self.background = pygame.Surface(self.screen_size)
            self.background.fill((20, 20, 30))

    def set_fonts(self, fonts: dict):
        """폰트 설정"""
        self.fonts = fonts

    def _get_portrait(self, speaker: str) -> pygame.Surface:
        """초상화 이미지 가져오기 (캐시 사용)"""
        if speaker in self.portrait_cache:
            return self.portrait_cache[speaker]

        try:
            from mode_configs.config_story_dialogue import CHARACTER_PORTRAITS

            path = CHARACTER_PORTRAITS.get(speaker)
        except ImportError:
            path = None

        if path:
            try:
                img = pygame.image.load(path).convert_alpha()
                target_size = (120, 120)
                img = pygame.transform.smoothscale(img, target_size)
                self.portrait_cache[speaker] = img
                return img
            except Exception as e:
                print(f"WARNING: Failed to load portrait for {speaker}: {e}")

        return None

    def _start_dialogue(self):
        """현재 대화 시작"""
        if self.current_dialogue_index < len(self.dialogue_after):
            self.dialogue_text = self.dialogue_after[self.current_dialogue_index].get(
                "text", ""
            )
            self.typing_progress = 0.0
            self.waiting_for_click = False

    def _update_dialogue(self, dt: float):
        """대화 업데이트 (타이핑 효과)"""
        if self.current_dialogue_index >= len(self.dialogue_after):
            return True  # 대화 완료

        if not self.waiting_for_click:
            self.typing_progress += dt * self.typing_speed
            if self.typing_progress >= len(self.dialogue_text):
                self.typing_progress = len(self.dialogue_text)
                self.waiting_for_click = True

        return False  # 대화 진행 중

    def _advance_dialogue(self):
        """다음 대화로 진행"""
        self.current_dialogue_index += 1
        if self.current_dialogue_index < len(self.dialogue_after):
            self._start_dialogue()
            return False  # 더 있음
        return True  # 대화 완료

    def _update_fadein(self, dt: float) -> bool:
        """페이드인 업데이트. 완료 시 True 반환"""
        progress = min(1.0, self.phase_timer / self.fadein_duration)
        self.fade_alpha = progress * 255
        return progress >= 1.0

    def _update_fadeout(self, dt: float) -> bool:
        """페이드아웃 업데이트. 완료 시 True 반환"""
        progress = min(1.0, self.phase_timer / self.fadeout_duration)
        self.fade_alpha = 255 * (1.0 - progress)
        return progress >= 1.0

    def update(self, dt: float):
        """업데이트 - 서브클래스에서 확장"""
        if not self.is_alive:
            return

        self.phase_timer += dt

        if self.phase == self.PHASE_FADEIN:
            if self._update_fadein(dt):
                self._on_fadein_complete()

        elif self.phase == self.PHASE_DIALOGUE:
            self._update_dialogue(dt)

        elif self.phase == self.PHASE_FADEOUT:
            if self._update_fadeout(dt):
                self._on_fadeout_complete()

    def _on_fadein_complete(self):
        """페이드인 완료 시 호출 - 서브클래스에서 오버라이드"""
        self.phase = self.PHASE_DISPLAY
        self.phase_timer = 0.0

    def _on_fadeout_complete(self):
        """페이드아웃 완료 시 호출"""
        self.phase = self.PHASE_DONE
        self.is_alive = False
        if self.on_complete:
            self.on_complete()

    def _transition_to_fadeout(self):
        """페이드아웃으로 전환"""
        self.phase = self.PHASE_FADEOUT
        self.phase_timer = 0.0

    def _transition_to_dialogue(self):
        """대화 페이즈로 전환"""
        self.phase = self.PHASE_DIALOGUE
        self.phase_timer = 0.0
        self._start_dialogue()

    def handle_event(self, event: pygame.event.Event) -> bool:
        """이벤트 처리 - 공통 로직"""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self._handle_click()

        elif event.type == pygame.KEYDOWN:
            if event.key in [pygame.K_SPACE, pygame.K_RETURN]:
                return self._handle_click()
            elif event.key == pygame.K_ESCAPE:
                self._transition_to_fadeout()
                return True

        return False

    def _handle_click(self) -> bool:
        """클릭 처리 - 서브클래스에서 확장 가능"""
        if self.phase == self.PHASE_DIALOGUE:
            if self.waiting_for_click:
                if self._advance_dialogue():
                    self._transition_to_fadeout()
            else:
                # 타이핑 스킵
                self.typing_progress = len(self.dialogue_text)
                self.waiting_for_click = True
            return True
        return False

    def render(self, screen: pygame.Surface):
        """렌더링 - 서브클래스에서 확장"""
        self._render_background(screen)

    def _render_background(self, screen: pygame.Surface):
        """배경 렌더링"""
        if self.background:
            bg_copy = self.background.copy()
            if self.fade_alpha < 255:
                bg_copy.set_alpha(int(self.fade_alpha))
            screen.blit(bg_copy, (0, 0))
        else:
            screen.fill((20, 20, 30))

    def _render_dialogue(
        self,
        screen: pygame.Surface,
        box_color: tuple = (20, 30, 40, 220),
        border_color: tuple = (100, 100, 150),
        text_color: tuple = (220, 220, 220),
    ):
        """대화창 렌더링 (초상화 포함)"""
        if not self.dialogue_after or self.current_dialogue_index >= len(
            self.dialogue_after
        ):
            return

        dialogue = self.dialogue_after[self.current_dialogue_index]
        speaker = dialogue.get("speaker", "")
        portrait = self._get_portrait(speaker) if speaker else None

        render_dialogue_box(
            screen,
            self.screen_size,
            self.fonts,
            dialogue,
            self.dialogue_text,
            self.typing_progress,
            self.waiting_for_click,
            box_color=box_color,
            border_color=border_color,
            text_color=text_color,
            has_portrait=(portrait is not None),
            portrait=portrait,
        )

    def _render_click_hint(self, screen: pygame.Surface, text: str = "클릭하여 계속"):
        """클릭 힌트 렌더링"""
        if "small" not in self.fonts:
            return

        alpha = int(128 + 127 * math.sin(pygame.time.get_ticks() / 300))
        hint_surf = self.fonts["small"].render(text, True, (200, 200, 200))
        hint_surf.set_alpha(alpha)
        hint_rect = hint_surf.get_rect(
            midbottom=(self.screen_size[0] // 2, self.screen_size[1] - 20)
        )
        screen.blit(hint_surf, hint_rect)


# =========================================================
# 공통 대화창 렌더링 헬퍼 함수
# =========================================================

# 대화창 바 이미지 캐시 (전역 변수)
_dialogue_bar_cache = {}

def _load_dialogue_bars():
    """대화창 바 이미지 로드 (캐싱) - 모든 화자 동일"""
    global _dialogue_bar_cache

    if _dialogue_bar_cache:
        return _dialogue_bar_cache

    try:
        import config
        from pathlib import Path

        bar_path = config.ASSET_DIR / "images" / "ui" / "dialogue_bar_basic.jpg"

        if not bar_path.exists():
            print(f"WARNING: Dialogue bar image not found: {bar_path}")
            return {}

        # 전체 이미지 로드
        bar_image = pygame.image.load(str(bar_path))

        # pygame display가 초기화되지 않았으면 그냥 로드, 초기화되었으면 convert
        try:
            bar_image = bar_image.convert()
        except pygame.error:
            pass  # display가 초기화되지 않은 경우 그냥 사용

        # 모든 화자가 동일한 이미지 사용
        _dialogue_bar_cache = {
            "ARTEMIS": bar_image,
            "PILOT": bar_image,
            "NARRATOR": bar_image,
        }

        print(f"INFO: Dialogue bar loaded from {bar_path}")
        return _dialogue_bar_cache

    except Exception as e:
        print(f"WARNING: Failed to load dialogue bar: {e}")
        return {}

def render_dialogue_box(
    screen: pygame.Surface,
    screen_size: tuple,
    fonts: dict,
    dialogue: dict,
    dialogue_text: str,
    typing_progress: float,
    waiting_for_click: bool,
    box_color: tuple = (20, 20, 40, 220),
    border_color: tuple = (100, 100, 150),
    text_color: tuple = (255, 255, 255),
    box_height: int = 180,
    has_portrait: bool = False,
    portrait: pygame.Surface = None,
    textbox_expand = None,
):
    """
    공통 대화창 렌더링 함수 - StoryBriefingEffect 스타일 (인트로 기준)

    Args:
        screen: 렌더링할 화면
        screen_size: (width, height) 화면 크기
        fonts: {"small": font, "medium": font} 폰트 딕셔너리
        dialogue: {"speaker": "...", "text": "..."} 대화 데이터
        dialogue_text: 전체 대사 텍스트
        typing_progress: 타이핑 진행률 (0~len)
        waiting_for_click: 클릭 대기 중 여부
        box_color: 박스 배경색 (R, G, B, A) - 기본값 StoryBriefingEffect와 동일
        border_color: 테두리 색상 (R, G, B) 또는 (R, G, B, A)
        text_color: 대사 텍스트 색상
        box_height: 박스 높이 - 기본 180 (StoryBriefingEffect와 동일)
        has_portrait: 초상화 표시 여부
        portrait: 초상화 Surface (has_portrait=True일 때)
        textbox_expand: TextBoxExpand 효과 객체 (선택 사항)
    """
    speaker = dialogue.get("speaker", "") if dialogue else ""

    screen_w, screen_h = screen_size

    # 위쪽으로 이동된 y 좌표 사용 (narrative_mode와 동일)
    box_y = screen_h - box_height - 150

    # TextBoxExpand 효과 적용
    if textbox_expand:
        # 펼침 중이거나 완료된 경우 모두 textbox_expand의 설정 사용
        if not textbox_expand.complete:
            actual_width = int(textbox_expand.current_width)
            actual_height = int(textbox_expand.current_height)
        else:
            # 완료 후에도 target_rect의 크기 사용
            actual_width = textbox_expand.target_rect.width
            actual_height = textbox_expand.target_rect.height
        actual_box_x = textbox_expand.start_x
        actual_box_y = textbox_expand.target_rect.y
        # 반환값을 위해 변수 할당
        box_x = actual_box_x
        box_width = actual_width
    else:
        # textbox_expand가 없으면 기본값 사용 (폴백)
        box_width = screen_w // 2
        box_x = 100
        actual_width = box_width
        actual_height = box_height
        actual_box_x = box_x
        actual_box_y = box_y

    # 대화창 바 이미지 로드
    dialogue_bars = _load_dialogue_bars()

    # 화자별 바 이미지 선택
    bar_image = dialogue_bars.get(speaker.upper()) if dialogue_bars else None

    if bar_image:
        # 이미지를 대화창 크기에 맞게 스케일
        scaled_bar = pygame.transform.smoothscale(bar_image, (actual_width, actual_height))
        screen.blit(scaled_bar, (actual_box_x, actual_box_y))
    else:
        # 이미지가 없으면 기본 박스 그리기 (폴백)
        box_surf = pygame.Surface((actual_width, actual_height), pygame.SRCALPHA)
        pygame.draw.rect(
            box_surf, box_color, (0, 0, actual_width, actual_height), border_radius=10
        )
        border_col = border_color if len(border_color) == 4 else border_color + (200,)
        pygame.draw.rect(
            box_surf, border_col, (0, 0, actual_width, actual_height), 2, border_radius=10
        )
        screen.blit(box_surf, (actual_box_x, actual_box_y))

    # 초상화 위치 계산 (textbox_expand 정보 기반)
    portrait_width = 0
    portrait_x = 0
    if has_portrait and portrait:
        # 화자에 따라 초상화 크기 조정
        speaker = dialogue.get("speaker", "") if dialogue else ""
        if speaker == "ARTEMIS":
            portrait_size = 364
        else:
            portrait_size = 338  # PILOT, NARRATOR

        # textbox_expand에서 그룹 정보 가져오기
        if textbox_expand:
            # 대화창 시작점 = 캐릭터 중심
            dialogue_box_start = textbox_expand.start_x
            # 캐릭터 중심에서 역산하여 캐릭터 왼쪽 위치 계산
            portrait_center_x = dialogue_box_start
            portrait_x = portrait_center_x - portrait_size // 2
        else:
            # 폴백: 전체 그룹 폭 계산 (화면 2/3)
            total_width = int(screen_w * 0.66)
            group_start_x = (screen_w - total_width) // 2
            portrait_x = group_start_x

        portrait_y = actual_box_y + box_height - portrait_size  # bottomleft 정렬 (대화창 바닥과 동일)

        # 초상화 스케일 및 표시
        portrait_copy = pygame.transform.smoothscale(
            portrait, (portrait_size, portrait_size)
        )
        screen.blit(portrait_copy, (portrait_x, portrait_y))
        portrait_width = portrait_size

    # 텍스트 시작 위치 (모든 화자 동일 위치 - ARTEMIS 기준 364px + 20px)
    # PILOT(338px)과 ARTEMIS(364px)의 텍스트 시작점을 통일
    max_portrait_size = 364  # ARTEMIS 크기
    text_left_x = portrait_x + max_portrait_size + 20  # 최대 캐릭터 크기 + 간격

    # 화자 이름 (모든 화자 표시, NARRATOR 포함)
    text_y = actual_box_y + 15
    if speaker and "medium" in fonts:
        try:
            from mode_configs.config_story_dialogue import (
                CHARACTER_COLORS,
                CHARACTER_NAMES,
            )

            name_color = CHARACTER_COLORS.get(speaker, (200, 200, 200))
            name = CHARACTER_NAMES.get(speaker, speaker)
        except ImportError:
            name_color = (200, 200, 200)
            name = speaker

        name_surf = fonts["medium"].render(name, True, name_color)
        screen.blit(name_surf, (text_left_x, text_y))
        text_y = text_y + name_surf.get_height() + 10
    else:
        text_y = actual_box_y + 20

    # 대사 텍스트 (단어 단위 줄바꿈 - StoryBriefingEffect 스타일)
    if "small" in fonts and dialogue_text:
        visible_text = dialogue_text[: int(typing_progress)]

        # 텍스트 영역 너비 계산 (대화창 우측 끝까지 - 우측 여백)
        # text_left_x부터 대화창 끝까지 사용 가능
        text_area_right = actual_box_x + actual_width - 60  # 우측 여백 (클릭 힌트 공간)
        max_width = text_area_right - text_left_x

        # 단어 단위 줄바꿈 (StoryBriefingEffect 방식)
        words = visible_text.split()
        lines = []
        current_line = ""

        for word in words:
            test_line = current_line + (" " if current_line else "") + word
            if fonts["small"].size(test_line)[0] <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)

        # NARRATOR 텍스트는 회색으로
        final_text_color = (180, 180, 180) if speaker == "NARRATOR" else text_color

        # 각 줄 렌더링
        for i, line in enumerate(lines):
            text_surf = fonts["small"].render(line, True, final_text_color)
            screen.blit(
                text_surf, (text_left_x, text_y + i * 28)
            )  # 28px 간격 (StoryBriefingEffect)

    # 클릭 대기 표시 (대화창 우측 내부, 깜빡이는 이모지)
    if waiting_for_click and "medium" in fonts:
        # 깜빡이는 효과를 위한 알파값 (시간 기반)
        import time
        alpha = int(abs(math.sin(time.time() * 3) * 155) + 100)  # 100~255 사이
        hint = fonts["medium"].render("▶", True, (200, 200, 200))
        hint.set_alpha(alpha)
        screen.blit(hint, (actual_box_x + actual_width - 40, actual_box_y + actual_height - 50))

    return box_x, box_y, box_width, box_height  # 필요시 반환
