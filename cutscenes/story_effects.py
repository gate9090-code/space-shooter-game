"""
cutscenes/story_effects.py
Story briefing cutscene effects
"""

import pygame
import math
from pathlib import Path


class StoryBriefingEffect:
    """
    스토리 브리핑 효과 - 비주얼 노벨 스타일 대사 시스템

    특징:
    - 배경 이미지 + 어둡게 처리
    - 캐릭터 초상화 표시
    - 타이핑 효과로 대사 표시
    - 클릭으로 다음 대사 진행
    - ESC로 스킵 가능
    """

    PHASE_FADEIN = 0  # 배경 페이드인
    PHASE_DIALOGUE = 1  # 대사 진행 중
    PHASE_FADEOUT = 2  # 페이드아웃
    PHASE_DONE = 3  # 완료

    def __init__(
        self,
        screen_size: tuple,
        dialogue_data: list,
        background_path: str = None,
        title: str = "",
        location: str = "",
    ):
        """
        Args:
            screen_size: 화면 크기 (width, height)
            dialogue_data: 대사 리스트 [{"speaker": "...", "text": "..."}, ...]
            background_path: 배경 이미지 경로 (None이면 어두운 배경)
            title: 타이틀 텍스트 (예: "ACT 1: RETURN TO RUINS")
            location: 위치 텍스트 (예: "DESTROYED CITY")
        """
        self.screen_size = screen_size
        self.dialogue_data = dialogue_data
        self.title = title
        self.location = location

        self.is_alive = True
        self.phase = self.PHASE_FADEIN
        self.phase_timer = 0.0

        # 대사 관련
        self.current_dialogue_index = 0
        self.typing_progress = 0.0
        self.typing_speed = 30.0  # 초당 글자 수
        self.current_text = ""
        self.full_text = ""
        self.waiting_for_click = False

        # 페이드 타이밍
        self.fadein_duration = 0.8
        self.fadeout_duration = 0.5
        self.fade_alpha = 0.0

        # 배경 로드
        self.background = None
        self.background_overlay = None
        if background_path:
            self._load_background(background_path)
        self._create_overlay()

        # 초상화 캐시
        self.portrait_cache = {}

        # 캐릭터 색상 (기본값)
        self.character_colors = {
            "ARTEMIS": (255, 220, 150),
            "PILOT": (150, 200, 255),
            "BOSS": (255, 100, 100),
            "NARRATOR": (200, 200, 200),
        }

        # 폰트 (나중에 외부에서 설정)
        self.fonts = {}

        # 콜백
        self.on_complete = None

        # 첫 대사 준비
        if self.dialogue_data:
            self._prepare_dialogue(0)

    def _load_background(self, path: str):
        """배경 이미지 로드"""
        try:
            img = pygame.image.load(path).convert()
            self.background = pygame.transform.scale(img, self.screen_size)
        except Exception as e:
            print(f"WARNING: Failed to load background: {path} - {e}")
            self.background = None

    def _create_overlay(self):
        """어두운 오버레이 생성"""
        self.background_overlay = pygame.Surface(self.screen_size, pygame.SRCALPHA)
        self.background_overlay.fill((0, 0, 0, 180))

    def _prepare_dialogue(self, index: int):
        """대사 준비"""
        if 0 <= index < len(self.dialogue_data):
            dialogue = self.dialogue_data[index]
            self.full_text = dialogue.get("text", "")
            self.current_text = ""
            self.typing_progress = 0.0
            self.waiting_for_click = False

    def _get_portrait(self, speaker: str) -> pygame.Surface:
        """초상화 이미지 가져오기 (캐시 사용) - NARRATOR는 android 이미지 사용"""
        if speaker in self.portrait_cache:
            return self.portrait_cache[speaker]

        # config_story_dialogue에서 경로 가져오기
        try:
            from mode_configs.config_story_dialogue import CHARACTER_PORTRAITS

            path = CHARACTER_PORTRAITS.get(speaker)
        except ImportError:
            path = None

        # 폴백: 여러 경로 시도 (.png 우선)
        if not path or not Path(path).exists():
            # NARRATOR는 android 이미지 파일명 사용
            filename = "android" if speaker == "NARRATOR" else speaker.lower()

            portrait_paths = [
                Path("assets/data/episodes/ep1/portraits") / f"portrait_{filename}.png",
                Path("assets/data/episodes/ep1/portraits") / f"portrait_{filename}.jpg",
                Path("assets/data/episodes/shared/portraits")
                / f"portrait_{filename}.png",
                Path("assets/data/episodes/shared/portraits")
                / f"portrait_{filename}.jpg",
            ]

            for p in portrait_paths:
                if p.exists():
                    path = str(p)
                    break
            else:
                return None

        if path:
            try:
                img = pygame.image.load(path).convert_alpha()
                # 크기 조정 (200x200)
                target_size = (200, 200)
                img = pygame.transform.smoothscale(img, target_size)
                self.portrait_cache[speaker] = img
                return img
            except Exception as e:
                print(f"WARNING: Failed to load portrait for {speaker}: {e}")

        return None

    def set_fonts(self, fonts: dict):
        """폰트 설정"""
        self.fonts = fonts

    def update(self, dt: float):
        """업데이트"""
        if not self.is_alive:
            return

        self.phase_timer += dt

        if self.phase == self.PHASE_FADEIN:
            # 페이드인
            progress = min(self.phase_timer / self.fadein_duration, 1.0)
            self.fade_alpha = progress

            if progress >= 1.0:
                self.phase = self.PHASE_DIALOGUE
                self.phase_timer = 0.0

        elif self.phase == self.PHASE_DIALOGUE:
            # 타이핑 효과
            if not self.waiting_for_click:
                self.typing_progress += self.typing_speed * dt
                char_count = int(self.typing_progress)

                if char_count >= len(self.full_text):
                    self.current_text = self.full_text
                    self.waiting_for_click = True
                else:
                    self.current_text = self.full_text[:char_count]

        elif self.phase == self.PHASE_FADEOUT:
            # 페이드아웃
            progress = min(self.phase_timer / self.fadeout_duration, 1.0)
            self.fade_alpha = 1.0 - progress

            if progress >= 1.0:
                self.phase = self.PHASE_DONE
                self.is_alive = False
                if self.on_complete:
                    self.on_complete()

    def handle_click(self):
        """클릭 처리"""
        if self.phase == self.PHASE_FADEIN:
            # 페이드인 스킵
            self.phase = self.PHASE_DIALOGUE
            self.phase_timer = 0.0
            self.fade_alpha = 1.0
            return

        if self.phase != self.PHASE_DIALOGUE:
            return

        if not self.waiting_for_click:
            # 타이핑 스킵 - 전체 텍스트 표시
            self.current_text = self.full_text
            self.waiting_for_click = True
        else:
            # 다음 대사로
            self.current_dialogue_index += 1

            if self.current_dialogue_index >= len(self.dialogue_data):
                # 모든 대사 완료 - 페이드아웃
                self.phase = self.PHASE_FADEOUT
                self.phase_timer = 0.0
            else:
                self._prepare_dialogue(self.current_dialogue_index)

    def skip(self):
        """전체 스킵"""
        self.phase = self.PHASE_FADEOUT
        self.phase_timer = 0.0

    def draw(self, screen: pygame.Surface):
        """렌더링"""
        if not self.is_alive and self.phase == self.PHASE_DONE:
            return

        # 배경
        if self.background:
            screen.blit(self.background, (0, 0))
        else:
            screen.fill((10, 10, 20))

        # 오버레이 (페이드 적용)
        overlay = self.background_overlay.copy()
        overlay.set_alpha(int(180 * self.fade_alpha))
        screen.blit(overlay, (0, 0))

        # 페이드인/아웃 중이면 나머지 UI 표시 안함
        if self.phase == self.PHASE_FADEIN and self.fade_alpha < 0.5:
            return
        if self.phase == self.PHASE_FADEOUT and self.fade_alpha < 0.5:
            return

        # UI 알파
        ui_alpha = int(255 * self.fade_alpha)

        # 타이틀/위치
        self._draw_title(screen, ui_alpha)

        # 대사 박스
        self._draw_dialogue_box(screen, ui_alpha)

    def _draw_title(self, screen: pygame.Surface, alpha: int):
        """타이틀 그리기"""
        if not self.title:
            return

        font = self.fonts.get("large") or self.fonts.get("medium")
        if not font:
            return

        # 타이틀
        title_surf = font.render(self.title, True, (255, 255, 255))
        title_surf.set_alpha(alpha)
        title_rect = title_surf.get_rect(midtop=(self.screen_size[0] // 2, 50))
        screen.blit(title_surf, title_rect)

        # 위치
        if self.location:
            small_font = self.fonts.get("small") or font
            loc_surf = small_font.render(self.location, True, (180, 180, 180))
            loc_surf.set_alpha(alpha)
            loc_rect = loc_surf.get_rect(
                midtop=(self.screen_size[0] // 2, title_rect.bottom + 10)
            )
            screen.blit(loc_surf, loc_rect)

    def _draw_dialogue_box(self, screen: pygame.Surface, alpha: int):
        """대사 박스 그리기"""
        if self.current_dialogue_index >= len(self.dialogue_data):
            return

        dialogue = self.dialogue_data[self.current_dialogue_index]
        speaker = dialogue.get("speaker", "")

        # 대사 박스 영역 (하단 중앙, 가로 1/2 크기)
        box_height = 180
        box_width = (self.screen_size[0] - 100) // 2
        box_x = (self.screen_size[0] - box_width) // 2
        box_rect = pygame.Rect(
            box_x, self.screen_size[1] - box_height - 40, box_width, box_height
        )

        # 박스 배경
        box_surf = pygame.Surface((box_rect.width, box_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(
            box_surf,
            (20, 20, 40, 220),
            (0, 0, box_rect.width, box_rect.height),
            border_radius=10,
        )
        pygame.draw.rect(
            box_surf,
            (100, 100, 150, 200),
            (0, 0, box_rect.width, box_rect.height),
            2,
            border_radius=10,
        )
        box_surf.set_alpha(alpha)
        screen.blit(box_surf, box_rect.topleft)

        # 초상화 (모든 캐릭터 왼쪽 배치)
        portrait = self._get_portrait(speaker)
        portrait_width = 0
        if portrait:
            portrait_rect = portrait.get_rect()
            portrait_rect.bottomleft = (box_rect.left + 20, box_rect.bottom - 10)

            portrait_copy = portrait.copy()
            portrait_copy.set_alpha(alpha)
            screen.blit(portrait_copy, portrait_rect)
            portrait_width = portrait_rect.width + 30

        # 화자 이름
        name_color = self.character_colors.get(speaker, (255, 255, 255))
        font = self.fonts.get("medium") or self.fonts.get("small")

        # 텍스트 시작 X 위치 (초상화 오른쪽)
        text_left_x = box_rect.left + portrait_width + 20

        if font and speaker and speaker != "NARRATOR":
            # 이름 표시
            display_name = {
                "ARTEMIS": "아르테미스",
                "PILOT": "파일럿",
                "BOSS": "???",
            }.get(speaker, speaker)

            name_surf = font.render(display_name, True, name_color)
            name_surf.set_alpha(alpha)
            name_rect = name_surf.get_rect(topleft=(text_left_x, box_rect.top + 15))
            screen.blit(name_surf, name_rect)
            text_y = name_rect.bottom + 10
        else:
            text_y = box_rect.top + 20

        # 대사 텍스트
        small_font = self.fonts.get("small") or font
        if small_font and self.current_text:
            text_color = (255, 255, 255) if speaker != "NARRATOR" else (180, 180, 180)

            # 줄바꿈 처리 (초상화 위치에 따라 텍스트 영역 조정)
            max_width = box_rect.width - portrait_width - 60
            words = self.current_text.split()
            lines = []
            current_line = ""

            for word in words:
                test_line = current_line + (" " if current_line else "") + word
                if small_font.size(test_line)[0] <= max_width:
                    current_line = test_line
                else:
                    if current_line:
                        lines.append(current_line)
                    current_line = word
            if current_line:
                lines.append(current_line)

            # 텍스트 그리기
            for i, line in enumerate(lines):
                text_surf = small_font.render(line, True, text_color)
                text_surf.set_alpha(alpha)
                screen.blit(text_surf, (text_left_x, text_y + i * 28))

        # 클릭 대기 표시
        if self.waiting_for_click:
            indicator_text = (
                "Click to continue..."
                if self.current_dialogue_index < len(self.dialogue_data) - 1
                else "Click to finish..."
            )
            ind_surf = small_font.render(indicator_text, True, (150, 150, 150))
            ind_surf.set_alpha(
                int(alpha * (0.5 + 0.5 * math.sin(pygame.time.get_ticks() / 300)))
            )
            ind_rect = ind_surf.get_rect(
                bottomright=(box_rect.right - 20, box_rect.bottom - 15)
            )
            screen.blit(ind_surf, ind_rect)
