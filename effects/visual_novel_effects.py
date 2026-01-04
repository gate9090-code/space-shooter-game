# effects/visual_novel_effects.py
"""
비주얼 노블 연출 기법 모음

다양한 비주얼 노블 효과들을 제공합니다.
- 타이핑 효과
- 페이드 인/아웃
- 화면 전환
- 캐릭터 애니메이션
- 특수 효과
"""

import pygame
import math
import random
from typing import Tuple, Optional, List


# ============================================================================
# 1. 텍스트 효과
# ============================================================================

class TypewriterEffect:
    """글자가 한 글자씩 나타나는 타이핑 효과 (사운드 지원)"""

    def __init__(self, text: str, speed: float = 0.05, sound_manager=None, play_sound: bool = True, sound_volume: float = 0.4):
        """
        Args:
            text: 표시할 전체 텍스트
            speed: 글자당 표시 시간 (초)
            sound_manager: SoundManager 인스턴스 (옵션)
            play_sound: 타이핑 사운드 재생 여부
            sound_volume: 타이핑 사운드 볼륨 (0.0 ~ 1.0)
        """
        self.full_text = text
        self.displayed_text = ""
        self.index = 0
        self.timer = 0
        self.speed = speed
        self.complete = False
        self.sound_manager = sound_manager
        self.play_sound = play_sound
        self.sound_volume = sound_volume

    def update(self, dt: float):
        """프레임마다 호출"""
        if self.complete:
            return

        self.timer += dt
        if self.timer >= self.speed:
            self.timer = 0
            if self.index < len(self.full_text):
                char = self.full_text[self.index]
                self.displayed_text += char
                self.index += 1

                # 타이핑 사운드 재생 (공백 제외)
                if self.play_sound and self.sound_manager and char.strip():
                    self.sound_manager.play_sfx("typing", volume_override=self.sound_volume)
            else:
                self.complete = True

    def skip(self):
        """스킵 - 전체 텍스트 즉시 표시"""
        self.displayed_text = self.full_text
        self.index = len(self.full_text)
        self.complete = True

    def reset(self, new_text: str = None):
        """리셋"""
        if new_text:
            self.full_text = new_text
        self.displayed_text = ""
        self.index = 0
        self.timer = 0
        self.complete = False


# ============================================================================
# 2. 페이드 효과
# ============================================================================

class FadeEffect:
    """화면 또는 이미지 페이드 인/아웃 효과"""

    def __init__(self, duration: float = 1.0, fade_in: bool = True):
        """
        Args:
            duration: 페이드 지속 시간 (초)
            fade_in: True면 페이드인, False면 페이드아웃
        """
        self.duration = duration
        self.elapsed = 0
        self.fade_in = fade_in
        self.alpha = 0 if fade_in else 255
        self.complete = False

    def update(self, dt: float):
        if self.complete:
            return

        self.elapsed += dt
        progress = min(self.elapsed / self.duration, 1.0)

        if self.fade_in:
            self.alpha = int(255 * progress)
        else:
            self.alpha = int(255 * (1 - progress))

        if progress >= 1.0:
            self.complete = True

    def apply(self, surface: pygame.Surface) -> pygame.Surface:
        """서피스에 페이드 적용"""
        surface_copy = surface.copy()
        surface_copy.set_alpha(self.alpha)
        return surface_copy

    def reset(self):
        """리셋"""
        self.elapsed = 0
        self.alpha = 0 if self.fade_in else 255
        self.complete = False


class CrossFade:
    """두 이미지 간 부드러운 전환"""

    def __init__(self, img1: pygame.Surface, img2: pygame.Surface, duration: float = 1.5):
        """
        Args:
            img1: 시작 이미지
            img2: 종료 이미지
            duration: 전환 시간 (초)
        """
        self.img1 = img1
        self.img2 = img2
        self.duration = duration
        self.elapsed = 0
        self.complete = False

    def update(self, dt: float):
        if self.complete:
            return

        self.elapsed += dt
        if self.elapsed >= self.duration:
            self.complete = True

    def render(self, screen: pygame.Surface, pos: Tuple[int, int] = (0, 0)):
        """화면에 크로스 페이드 렌더링"""
        progress = min(self.elapsed / self.duration, 1.0)

        # 첫 번째 이미지는 서서히 투명해짐
        img1_copy = self.img1.copy()
        img1_copy.set_alpha(int(255 * (1 - progress)))

        # 두 번째 이미지는 서서히 나타남
        img2_copy = self.img2.copy()
        img2_copy.set_alpha(int(255 * progress))

        screen.blit(img1_copy, pos)
        screen.blit(img2_copy, pos)


# ============================================================================
# 3. 캐릭터 애니메이션
# ============================================================================

class PortraitSlideIn:
    """캐릭터 초상화가 옆에서 슬라이드하며 등장"""

    def __init__(self, portrait: pygame.Surface, target_x: int,
                 start_x: int = -200, duration: float = 0.5, ease: str = "out"):
        """
        Args:
            portrait: 초상화 이미지
            target_x: 목표 X 좌표
            start_x: 시작 X 좌표
            duration: 애니메이션 시간 (초)
            ease: 이징 타입 ("in", "out", "inout", "linear")
        """
        self.portrait = portrait
        self.start_x = start_x
        self.target_x = target_x
        self.current_x = start_x
        self.duration = duration
        self.elapsed = 0
        self.ease = ease
        self.complete = False

    def update(self, dt: float):
        if self.complete:
            return

        self.elapsed += dt
        progress = min(self.elapsed / self.duration, 1.0)

        # 이징 적용
        if self.ease == "out":
            progress = 1 - (1 - progress) ** 3
        elif self.ease == "in":
            progress = progress ** 3
        elif self.ease == "inout":
            progress = 3 * progress ** 2 - 2 * progress ** 3

        self.current_x = self.start_x + (self.target_x - self.start_x) * progress

        if self.elapsed >= self.duration:
            self.complete = True

    def render(self, screen: pygame.Surface, y: int):
        """화면에 초상화 렌더링"""
        screen.blit(self.portrait, (int(self.current_x), y))


class PortraitBounce:
    """초상화가 통통 튀는 효과 (강조용)"""

    def __init__(self, portrait: pygame.Surface, pos: Tuple[int, int],
                 bounce_height: int = 20, duration: float = 0.5):
        self.portrait = portrait
        self.base_pos = pos
        self.bounce_height = bounce_height
        self.duration = duration
        self.elapsed = 0
        self.current_y_offset = 0

    def update(self, dt: float):
        self.elapsed += dt
        if self.elapsed < self.duration:
            progress = self.elapsed / self.duration
            # 사인 곡선으로 튀는 효과
            self.current_y_offset = -abs(math.sin(progress * math.pi) * self.bounce_height)
        else:
            self.current_y_offset = 0

    def render(self, screen: pygame.Surface):
        pos = (self.base_pos[0], self.base_pos[1] + int(self.current_y_offset))
        screen.blit(self.portrait, pos)


# ============================================================================
# 4. 화면 효과
# ============================================================================

class ScreenShake:
    """충격이나 폭발 연출용 화면 흔들림"""

    def __init__(self, intensity: int = 10, duration: float = 0.5):
        """
        Args:
            intensity: 흔들림 강도 (픽셀)
            duration: 지속 시간 (초)
        """
        self.intensity = intensity
        self.duration = duration
        self.elapsed = 0
        self.offset_x = 0
        self.offset_y = 0

    def update(self, dt: float):
        self.elapsed += dt

        if self.elapsed < self.duration:
            # 시간이 지날수록 약해짐
            progress = 1 - (self.elapsed / self.duration)
            shake_amount = self.intensity * progress
            self.offset_x = random.randint(-int(shake_amount), int(shake_amount))
            self.offset_y = random.randint(-int(shake_amount), int(shake_amount))
        else:
            self.offset_x = 0
            self.offset_y = 0

    def apply(self, pos: Tuple[int, int]) -> Tuple[int, int]:
        """위치에 흔들림 적용"""
        return (pos[0] + self.offset_x, pos[1] + self.offset_y)

    def is_active(self) -> bool:
        return self.elapsed < self.duration


class FlashEffect:
    """번쩍이는 화면 효과 (충격, 회상 등)"""

    def __init__(self, color: Tuple[int, int, int] = (255, 255, 255),
                 duration: float = 0.2):
        """
        Args:
            color: 플래시 색상 (RGB)
            duration: 지속 시간 (초)
        """
        self.color = color
        self.duration = duration
        self.elapsed = 0
        self.alpha = 255

    def update(self, dt: float):
        self.elapsed += dt
        progress = min(self.elapsed / self.duration, 1.0)
        self.alpha = int(255 * (1 - progress))

    def render(self, screen: pygame.Surface):
        """화면에 플래시 렌더링"""
        if self.alpha > 0:
            flash = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
            flash.fill((*self.color, self.alpha))
            screen.blit(flash, (0, 0))

    def is_active(self) -> bool:
        return self.alpha > 0


class VignetteEffect:
    """화면 가장자리를 어둡게 (영화같은 느낌)"""

    def __init__(self, screen_size: Tuple[int, int], intensity: int = 150):
        """
        Args:
            screen_size: 화면 크기
            intensity: 비네트 강도 (0-255)
        """
        self.screen_size = screen_size
        self.intensity = intensity
        self.vignette = self._create_vignette()

    def _create_vignette(self) -> pygame.Surface:
        """비네트 서피스 생성"""
        vignette = pygame.Surface(self.screen_size, pygame.SRCALPHA)
        center_x, center_y = self.screen_size[0] // 2, self.screen_size[1] // 2
        max_dist = math.sqrt(center_x**2 + center_y**2)

        for y in range(0, self.screen_size[1], 4):  # 최적화: 4픽셀마다
            for x in range(0, self.screen_size[0], 4):
                dist = math.sqrt((x - center_x)**2 + (y - center_y)**2)
                alpha = int((dist / max_dist) * self.intensity)
                pygame.draw.rect(vignette, (0, 0, 0, min(alpha, 255)),
                               (x, y, 4, 4))

        return vignette

    def render(self, screen: pygame.Surface):
        """화면에 비네트 렌더링"""
        screen.blit(self.vignette, (0, 0))


# ============================================================================
# 5. UI 효과
# ============================================================================

class TextBoxExpand:
    """대화창이 펼쳐지는 효과 (좌→우 또는 위→아래)"""

    def __init__(self, rect: pygame.Rect, duration: float = 0.3, direction: str = "horizontal", start_x: int = None):
        """
        Args:
            rect: 목표 사각형
            duration: 애니메이션 시간 (초)
            direction: 펼침 방향 ("horizontal" = 좌→우, "vertical" = 위→아래)
            start_x: 가로 펼침 시작 x 좌표 (None이면 rect.x 사용)
        """
        self.target_rect = rect
        self.direction = direction
        self.duration = duration
        self.elapsed = 0
        self.complete = False
        self.start_x = start_x if start_x is not None else rect.x

        if direction == "horizontal":
            self.current_width = 0
            self.target_width = rect.width
            self.current_height = rect.height
        else:  # vertical
            self.current_width = rect.width
            self.current_height = 0
            self.target_height = rect.height

    def update(self, dt: float):
        if self.complete:
            return

        self.elapsed += dt
        progress = min(self.elapsed / self.duration, 1.0)

        if self.direction == "horizontal":
            self.current_width = int(self.target_width * progress)
        else:  # vertical
            self.current_height = int(self.target_height * progress)

        if progress >= 1.0:
            self.complete = True

    def render(self, screen: pygame.Surface,
              color: Tuple[int, int, int, int] = (20, 20, 40, 200)):
        """대화창 렌더링"""
        rect = pygame.Rect(
            self.start_x,  # 시작 x 좌표부터 펼침
            self.target_rect.y,
            self.current_width,
            self.current_height
        )
        surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        surf.fill(color)
        screen.blit(surf, rect.topleft)


class ChoiceBox:
    """플레이어가 선택할 수 있는 선택지"""

    def __init__(self, choices: List[str], pos: Tuple[int, int]):
        """
        Args:
            choices: 선택지 목록
            pos: 시작 위치 (x, y)
        """
        self.choices = choices
        self.pos = pos
        self.selected = 0
        self.hover_index = -1
        self.rects = []
        self.result = None

    def handle_event(self, event: pygame.event.Event):
        """이벤트 처리"""
        if event.type == pygame.MOUSEMOTION:
            mouse_pos = event.pos
            self.hover_index = -1
            for i, rect in enumerate(self.rects):
                if rect.collidepoint(mouse_pos):
                    self.hover_index = i
                    return

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.hover_index >= 0:
                self.result = self.hover_index

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.selected = (self.selected - 1) % len(self.choices)
            elif event.key == pygame.K_DOWN:
                self.selected = (self.selected + 1) % len(self.choices)
            elif event.key == pygame.K_RETURN:
                self.result = self.selected

    def render(self, screen: pygame.Surface, font: pygame.font.Font):
        """선택지 렌더링"""
        self.rects = []
        y = self.pos[1]

        for i, choice in enumerate(self.choices):
            is_hover = (i == self.hover_index)
            is_selected = (i == self.selected)

            color = (255, 200, 100) if is_hover else (200, 200, 200)
            prefix = "► " if is_selected else "  "

            text = font.render(f"{prefix}{choice}", True, color)
            rect = text.get_rect(topleft=(self.pos[0], y))

            # 배경
            bg = pygame.Surface((rect.width + 20, rect.height + 10), pygame.SRCALPHA)
            bg_color = (50, 50, 100, 150) if is_hover else (30, 30, 60, 100)
            bg.fill(bg_color)
            screen.blit(bg, (rect.x - 10, rect.y - 5))

            screen.blit(text, rect)
            self.rects.append(rect)
            y += rect.height + 15


# ============================================================================
# 6. 특수 효과
# ============================================================================

class EmotionIcon:
    """캐릭터 위에 감정 아이콘 (!, ?, ♥ 등)"""

    ICONS = {
        "!": "!",
        "?": "?",
        "heart": "♥",
        "sweat": "💧",
        "angry": "💢",
        "zzz": "💤",
        "note": "♪"
    }

    def __init__(self, icon_type: str, pos: Tuple[int, int], duration: float = 1.0):
        """
        Args:
            icon_type: 아이콘 타입 (!, ?, heart, sweat, angry, zzz, note)
            pos: 표시 위치
            duration: 지속 시간 (초)
        """
        self.icon_type = icon_type
        self.pos = pos
        self.duration = duration
        self.elapsed = 0
        self.y_offset = 0

    def update(self, dt: float):
        self.elapsed += dt
        # 위아래로 흔들림
        self.y_offset = math.sin(self.elapsed * 8) * 5

    def render(self, screen: pygame.Surface, font: pygame.font.Font):
        """아이콘 렌더링"""
        if self.elapsed >= self.duration:
            return

        icon_char = self.ICONS.get(self.icon_type, "?")
        text = font.render(icon_char, True, (255, 255, 255))

        # 페이드 아웃
        if self.elapsed > self.duration * 0.7:
            alpha = int(255 * (1 - (self.elapsed - self.duration * 0.7) / (self.duration * 0.3)))
            text.set_alpha(alpha)

        screen.blit(text, (self.pos[0], self.pos[1] + int(self.y_offset)))

    def is_active(self) -> bool:
        return self.elapsed < self.duration


class CGPresentation:
    """CG 이미지 전체화면 표시 (중요 장면)"""

    def __init__(self, cg_image: pygame.Surface, screen_size: Tuple[int, int],
                 fade_duration: float = 1.5):
        """
        Args:
            cg_image: CG 이미지
            screen_size: 화면 크기
            fade_duration: 페이드 인 시간 (초)
        """
        self.cg_image = cg_image
        self.screen_size = screen_size
        self.fade_in = FadeEffect(duration=fade_duration, fade_in=True)
        self.display_timer = 0
        self.phase = "fade_in"  # fade_in, display, fade_out, done

    def update(self, dt: float):
        """업데이트"""
        if self.phase == "fade_in":
            self.fade_in.update(dt)
            if self.fade_in.complete:
                self.phase = "display"

        elif self.phase == "display":
            self.display_timer += dt

    def skip(self):
        """스킵"""
        self.phase = "done"

    def render(self, screen: pygame.Surface):
        """렌더링"""
        # 배경 검게
        screen.fill((0, 0, 0))

        # CG 이미지
        scaled_cg = pygame.transform.smoothscale(self.cg_image, self.screen_size)
        if self.phase == "fade_in":
            scaled_cg = self.fade_in.apply(scaled_cg)

        screen.blit(scaled_cg, (0, 0))


# ============================================================================
# 7. 자동화 기능
# ============================================================================

class AutoMode:
    """대사를 자동으로 넘김"""

    def __init__(self, delay_per_char: float = 0.05, min_delay: float = 2.0):
        """
        Args:
            delay_per_char: 글자당 대기 시간 (초)
            min_delay: 최소 대기 시간 (초)
        """
        self.delay_per_char = delay_per_char
        self.min_delay = min_delay
        self.timer = 0
        self.wait_time = 0
        self.waiting = False
        self.enabled = False

    def start_wait(self, text_length: int):
        """대사 길이에 따라 대기 시간 설정"""
        if not self.enabled:
            return

        self.waiting = True
        self.timer = 0
        # 최소 시간 + 글자 수에 비례
        self.wait_time = max(self.min_delay, text_length * self.delay_per_char)

    def update(self, dt: float) -> bool:
        """
        업데이트

        Returns:
            True면 다음 대사로 진행
        """
        if self.waiting:
            self.timer += dt
            if self.timer >= self.wait_time:
                self.waiting = False
                return True
        return False

    def toggle(self):
        """자동 모드 토글"""
        self.enabled = not self.enabled


class DialogueHistory:
    """지나간 대화 기록 보기"""

    def __init__(self, max_lines: int = 50):
        """
        Args:
            max_lines: 최대 저장 대화 수
        """
        self.history = []
        self.max_lines = max_lines
        self.showing = False
        self.scroll_offset = 0

    def add(self, speaker: str, text: str):
        """대화 추가"""
        self.history.append({"speaker": speaker, "text": text})
        if len(self.history) > self.max_lines:
            self.history.pop(0)

    def toggle(self):
        """표시 토글"""
        self.showing = not self.showing

    def scroll(self, delta: int):
        """스크롤"""
        self.scroll_offset += delta
        self.scroll_offset = max(-len(self.history) * 60, min(0, self.scroll_offset))

    def render(self, screen: pygame.Surface, font: pygame.font.Font):
        """렌더링"""
        if not self.showing:
            return

        # 반투명 배경
        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        screen.blit(overlay, (0, 0))

        # 대화 기록
        y = 50 + self.scroll_offset
        for entry in self.history:
            if y > -60 and y < screen.get_height():
                speaker_text = font.render(f"{entry['speaker']}:", True, (255, 200, 100))
                dialogue_text = font.render(entry['text'], True, (255, 255, 255))

                screen.blit(speaker_text, (100, y))
                screen.blit(dialogue_text, (100, y + 25))
            y += 60


class IntroBackgroundSequence:
    """인트로 배경 이미지 시퀀스 - 페이드인 효과로 순차 전환"""

    def __init__(self, image_paths: List[str], fade_duration: float = 1.5):
        """
        Args:
            image_paths: 배경 이미지 경로 리스트
            fade_duration: 페이드인 지속 시간 (초)
        """
        self.image_paths = image_paths
        self.fade_duration = fade_duration
        self.images = []
        self.current_index = 0
        self.fade_alpha = 0
        self.fade_timer = 0
        self.is_fading = False
        self.completed = False

        # 이미지 로드
        self._load_images()

    def _load_images(self):
        """배경 이미지 로드"""
        from pathlib import Path

        for path in self.image_paths:
            try:
                # intro_images 폴더에서 로드
                full_path = f"assets/images/intro_images/{path}"
                if Path(full_path).exists():
                    img = pygame.image.load(full_path).convert()
                    self.images.append(img)
                    print(f"INFO: Loaded intro background: {path}")
                else:
                    print(f"WARNING: Intro background not found: {full_path}")
            except Exception as e:
                print(f"WARNING: Failed to load intro background {path}: {e}")

    def start_next_image(self):
        """다음 이미지로 전환 시작"""
        if self.current_index < len(self.images) - 1:
            self.current_index += 1
            self.fade_alpha = 0
            self.fade_timer = 0
            self.is_fading = True
        elif self.current_index == len(self.images) - 1:
            self.completed = True

    def update(self, dt: float):
        """업데이트"""
        if self.is_fading:
            self.fade_timer += dt
            progress = min(self.fade_timer / self.fade_duration, 1.0)
            self.fade_alpha = int(255 * progress)

            if progress >= 1.0:
                self.is_fading = False

    def render(self, screen: pygame.Surface):
        """렌더링"""
        if not self.images:
            return

        screen_size = screen.get_size()

        # 현재 이미지 표시 (항상 표시)
        if self.current_index < len(self.images):
            current_img = pygame.transform.scale(self.images[self.current_index], screen_size)

            if self.is_fading:
                # 페이드인 중 - 이전 이미지 먼저 표시
                if self.current_index > 0:
                    prev_img = pygame.transform.scale(self.images[self.current_index - 1], screen_size)
                    screen.blit(prev_img, (0, 0))
                else:
                    # 첫 이미지는 검은 배경에서 페이드인
                    screen.fill((0, 0, 0))

                # 현재 이미지 위에 페이드인
                temp_surface = current_img.copy()
                temp_surface.set_alpha(self.fade_alpha)
                screen.blit(temp_surface, (0, 0))
            else:
                # 페이드 완료 - 현재 이미지만 표시
                screen.blit(current_img, (0, 0))

    def get_current_image_index(self):
        """현재 이미지 인덱스 반환"""
        return self.current_index


print("INFO: visual_novel_effects.py loaded - 16 effects available")
