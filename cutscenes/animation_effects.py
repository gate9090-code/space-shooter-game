"""
cutscenes/animation_effects.py
Ship and vehicle animation cutscene effects
"""

import pygame
import math
import random
from pathlib import Path
from cutscenes.base import BaseCutsceneEffect, render_dialogue_box


class ShipEntranceEffect:
    """
    비행선 진입 효과 - 화면 상단에서 진입 후 폐허 주변 선회

    연출:
    1. 비행선이 화면 상단 밖에서 진입
    2. 화면 중앙의 폐허 건물 주변을 천천히 타원형으로 선회
    3. 선회 중 대화 진행
    4. 대화 완료 후 비행선이 전투 위치(화면 하단)로 이동
    """

    PHASE_ENTRANCE = 0  # 화면 진입
    PHASE_CIRCLING = 1  # 폐허 주변 선회 + 대화
    PHASE_POSITIONING = 2  # 전투 위치로 이동
    PHASE_DONE = 3  # 완료

    def __init__(
        self,
        screen_size: tuple,
        player,
        dialogue_data: list,
        background_path: str = None,
        title: str = "",
        location: str = "",
    ):
        """
        Args:
            screen_size: 화면 크기 (width, height)
            player: Player 객체 (위치 제어용)
            dialogue_data: 대사 리스트 [{"speaker": "...", "text": "..."}, ...]
            background_path: 배경 이미지 경로
            title: 타이틀 텍스트
            location: 위치 텍스트
        """
        self.screen_size = screen_size
        self.player = player
        self.dialogue_data = dialogue_data
        self.title = title
        self.location = location

        self.is_alive = True
        self.phase = self.PHASE_ENTRANCE
        self.phase_timer = 0.0

        # 진입 애니메이션
        self.entrance_duration = 2.5  # 진입 시간 (초)
        self.start_pos = (screen_size[0] // 2, -100)  # 화면 상단 밖
        self.entrance_end_pos = (
            screen_size[0] // 2,
            screen_size[1] // 3,
        )  # 선회 시작 위치

        # 선회 애니메이션
        self.orbit_center = (screen_size[0] // 2, screen_size[1] // 2 - 50)  # 폐허 중심
        self.orbit_radius_x = screen_size[0] // 4  # 타원 가로 반경
        self.orbit_radius_y = screen_size[1] // 6  # 타원 세로 반경
        self.orbit_speed = 0.3  # 선회 속도 (라디안/초)
        self.orbit_angle = -math.pi / 2  # 시작 각도 (상단에서 시작)

        # 전투 위치
        self.battle_pos = (screen_size[0] // 2, int(screen_size[1] * 0.7))
        self.positioning_duration = 1.5

        # 대사 관련
        self.current_dialogue_index = 0
        self.typing_progress = 0.0
        self.typing_speed = 25.0  # 초당 글자 수
        self.current_text = ""
        self.full_text = ""
        self.waiting_for_click = False
        self.dialogue_started = False  # 선회 시작 후 대화 시작
        self.dialogue_start_delay = 1.0  # 선회 시작 후 대화 시작까지 딜레이
        self.dialogue_timer = 0.0

        # 배경 로드
        self.background = None
        if background_path:
            self._load_background(background_path)

        # 초상화 캐시
        self.portrait_cache = {}

        # 캐릭터 색상
        self.character_colors = {
            "ARTEMIS": (255, 220, 150),
            "PILOT": (150, 200, 255),
            "BOSS": (255, 100, 100),
            "NARRATOR": (200, 200, 200),
        }

        # 폰트
        self.fonts = {}

        # 콜백
        self.on_complete = None

        # 플레이어 원래 이미지/위치 저장
        if player:
            self.original_player_pos = player.pos.copy()
            player.pos = pygame.math.Vector2(self.start_pos)

        # 첫 대사 준비
        if self.dialogue_data:
            self._prepare_dialogue(0)

        print("INFO: ShipEntranceEffect initialized")

    def _load_background(self, path: str):
        """배경 이미지 로드"""
        try:
            img = pygame.image.load(path).convert()
            self.background = pygame.transform.scale(img, self.screen_size)
        except Exception as e:
            print(f"WARNING: Failed to load background: {path} - {e}")

    def _prepare_dialogue(self, index: int):
        """대사 준비"""
        if 0 <= index < len(self.dialogue_data):
            dialogue = self.dialogue_data[index]
            self.full_text = dialogue.get("text", "")
            self.current_text = ""
            self.typing_progress = 0.0
            self.waiting_for_click = False

    def _get_portrait(self, speaker: str) -> pygame.Surface:
        """초상화 이미지 가져오기"""
        if speaker in self.portrait_cache:
            return self.portrait_cache[speaker]

        try:
            from mode_configs.config_story_dialogue import CHARACTER_PORTRAITS

            path = CHARACTER_PORTRAITS.get(speaker)
        except ImportError:
            portrait_paths = {
                "ARTEMIS": "assets/story_mode/portraits/portrait_artemis.jpg",
                "PILOT": "assets/story_mode/portraits/portrait_pilot.png",
            }
            path = portrait_paths.get(speaker)

        if path:
            try:
                img = pygame.image.load(path).convert_alpha()
                target_size = (180, 180)
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

        if self.phase == self.PHASE_ENTRANCE:
            # 화면 진입 애니메이션
            progress = min(self.phase_timer / self.entrance_duration, 1.0)

            # 이징 (ease-out-cubic)
            eased = 1 - pow(1 - progress, 3)

            # 플레이어 위치 보간
            if self.player:
                new_x = (
                    self.start_pos[0]
                    + (self.entrance_end_pos[0] - self.start_pos[0]) * eased
                )
                new_y = (
                    self.start_pos[1]
                    + (self.entrance_end_pos[1] - self.start_pos[1]) * eased
                )
                self.player.pos = pygame.math.Vector2(new_x, new_y)

            if progress >= 1.0:
                self.phase = self.PHASE_CIRCLING
                self.phase_timer = 0.0
                self.dialogue_timer = 0.0
                print("INFO: Ship entrance complete, starting circling")

        elif self.phase == self.PHASE_CIRCLING:
            # 선회 애니메이션
            self.orbit_angle += self.orbit_speed * dt

            # 타원 궤도 계산
            orbit_x = (
                self.orbit_center[0] + math.cos(self.orbit_angle) * self.orbit_radius_x
            )
            orbit_y = (
                self.orbit_center[1] + math.sin(self.orbit_angle) * self.orbit_radius_y
            )

            if self.player:
                self.player.pos = pygame.math.Vector2(orbit_x, orbit_y)

            # 대화 시작 딜레이
            self.dialogue_timer += dt
            if (
                not self.dialogue_started
                and self.dialogue_timer >= self.dialogue_start_delay
            ):
                self.dialogue_started = True

            # 대화 진행
            if self.dialogue_started and self.dialogue_data:
                self._update_dialogue(dt)

        elif self.phase == self.PHASE_POSITIONING:
            # 전투 위치로 이동
            progress = min(self.phase_timer / self.positioning_duration, 1.0)

            # 이징 (ease-in-out-cubic)
            if progress < 0.5:
                eased = 4 * progress * progress * progress
            else:
                eased = 1 - pow(-2 * progress + 2, 3) / 2

            if self.player:
                # 현재 선회 위치에서 전투 위치로
                start_x = (
                    self.orbit_center[0]
                    + math.cos(self.orbit_angle) * self.orbit_radius_x
                )
                start_y = (
                    self.orbit_center[1]
                    + math.sin(self.orbit_angle) * self.orbit_radius_y
                )

                new_x = start_x + (self.battle_pos[0] - start_x) * eased
                new_y = start_y + (self.battle_pos[1] - start_y) * eased
                self.player.pos = pygame.math.Vector2(new_x, new_y)

            if progress >= 1.0:
                self.phase = self.PHASE_DONE
                self.is_alive = False
                if self.on_complete:
                    self.on_complete()
                print("INFO: ShipEntranceEffect complete")

    def _update_dialogue(self, dt: float):
        """대화 업데이트"""
        if self.current_dialogue_index >= len(self.dialogue_data):
            # 모든 대화 완료 → 전투 위치로 이동
            self.phase = self.PHASE_POSITIONING
            self.phase_timer = 0.0
            return

        if not self.waiting_for_click:
            self.typing_progress += self.typing_speed * dt
            char_count = int(self.typing_progress)

            if char_count >= len(self.full_text):
                self.current_text = self.full_text
                self.waiting_for_click = True
            else:
                self.current_text = self.full_text[:char_count]

    def handle_click(self):
        """클릭 처리"""
        if self.phase == self.PHASE_ENTRANCE:
            # 진입 스킵
            self.phase = self.PHASE_CIRCLING
            self.phase_timer = 0.0
            self.dialogue_timer = 0.0
            if self.player:
                self.player.pos = pygame.math.Vector2(self.entrance_end_pos)
            return

        if self.phase == self.PHASE_CIRCLING and self.dialogue_started:
            if not self.waiting_for_click:
                # 타이핑 스킵
                self.current_text = self.full_text
                self.waiting_for_click = True
            else:
                # 다음 대사
                self.current_dialogue_index += 1
                if self.current_dialogue_index >= len(self.dialogue_data):
                    # 대화 완료
                    self.phase = self.PHASE_POSITIONING
                    self.phase_timer = 0.0
                else:
                    self._prepare_dialogue(self.current_dialogue_index)

    def skip(self):
        """전체 스킵"""
        self.phase = self.PHASE_POSITIONING
        self.phase_timer = 0.0
        if self.player:
            self.player.pos = pygame.math.Vector2(self.battle_pos)

    def draw(self, screen: pygame.Surface):
        """렌더링"""
        if not self.is_alive and self.phase == self.PHASE_DONE:
            return

        # 배경
        if self.background:
            screen.blit(self.background, (0, 0))
        else:
            screen.fill((20, 20, 30))

        # 반투명 오버레이 (분위기)
        overlay = pygame.Surface(self.screen_size, pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 100))
        screen.blit(overlay, (0, 0))

        # 플레이어 그리기
        if self.player:
            # 플레이어 이미지 그리기
            player_rect = self.player.image.get_rect(
                center=(int(self.player.pos.x), int(self.player.pos.y))
            )
            screen.blit(self.player.image, player_rect)

        # 타이틀/위치 (진입 중에만)
        if self.phase == self.PHASE_ENTRANCE:
            self._draw_title(screen)

        # 대화 박스 (선회 중 대화 시작 후)
        if (
            self.phase == self.PHASE_CIRCLING
            and self.dialogue_started
            and self.dialogue_data
        ):
            if self.current_dialogue_index < len(self.dialogue_data):
                self._draw_dialogue_box(screen)

        # 클릭 힌트
        if self.waiting_for_click:
            self._draw_click_hint(screen)

    def _draw_title(self, screen: pygame.Surface):
        """타이틀 그리기"""
        if not self.title:
            return

        font = self.fonts.get("large") or self.fonts.get("medium")
        if not font:
            return

        # 페이드 인 효과
        alpha = min(int(255 * self.phase_timer / 1.0), 255)

        title_surf = font.render(self.title, True, (255, 200, 100))
        title_surf.set_alpha(alpha)
        title_rect = title_surf.get_rect(
            center=(self.screen_size[0] // 2, self.screen_size[1] // 6)
        )
        screen.blit(title_surf, title_rect)

        if self.location:
            loc_font = self.fonts.get("medium") or self.fonts.get("small")
            if loc_font:
                loc_surf = loc_font.render(self.location, True, (200, 200, 200))
                loc_surf.set_alpha(alpha)
                loc_rect = loc_surf.get_rect(
                    center=(self.screen_size[0] // 2, self.screen_size[1] // 6 + 40)
                )
                screen.blit(loc_surf, loc_rect)

    def _draw_dialogue_box(self, screen: pygame.Surface):
        """대화 박스 그리기"""
        if not self.dialogue_data or self.current_dialogue_index >= len(
            self.dialogue_data
        ):
            return

        dialogue = self.dialogue_data[self.current_dialogue_index]
        speaker = dialogue.get("speaker", "")

        # 폰트
        font = self.fonts.get("medium") or self.fonts.get("small")
        if not font:
            return

        # 초상화
        portrait = self._get_portrait(speaker)
        portrait_width = 180 if portrait else 0

        # 대화 박스 영역 (가로 1/2 크기, 중앙 정렬)
        box_margin = 50
        box_height = 140
        box_width = (self.screen_size[0] - box_margin * 2) // 2
        box_x = (self.screen_size[0] - box_width) // 2
        box_y = self.screen_size[1] - box_height - box_margin

        # 박스 배경
        box_surf = pygame.Surface((box_width, box_height), pygame.SRCALPHA)
        pygame.draw.rect(
            box_surf, (0, 0, 0, 200), (0, 0, box_width, box_height), border_radius=15
        )
        pygame.draw.rect(
            box_surf,
            (100, 100, 120),
            (0, 0, box_width, box_height),
            width=2,
            border_radius=15,
        )
        screen.blit(box_surf, (box_x, box_y))

        # 초상화 (좌측)
        if portrait:
            portrait_y = box_y + (box_height - portrait.get_height()) // 2
            screen.blit(portrait, (box_x + 10, portrait_y))

        # 화자 이름
        try:
            from mode_configs.config_story_dialogue import CHARACTER_NAMES

            speaker_name = CHARACTER_NAMES.get(speaker, speaker)
        except ImportError:
            speaker_name = speaker

        name_color = self.character_colors.get(speaker, (255, 255, 255))

        if speaker_name:
            name_surf = font.render(speaker_name, True, name_color)
            name_x = box_x + portrait_width + 30
            name_y = box_y + 15
            screen.blit(name_surf, (name_x, name_y))

        # 대사 텍스트
        text_x = box_x + portrait_width + 30
        text_y = box_y + 50
        text_width = box_width - portrait_width - 60

        # 줄바꿈 처리
        words = self.current_text.split(" ")
        lines = []
        current_line = ""

        for word in words:
            test_line = current_line + word + " "
            if font.size(test_line)[0] <= text_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word + " "
        if current_line:
            lines.append(current_line)

        # 텍스트 렌더링
        for i, line in enumerate(lines[:3]):  # 최대 3줄
            text_surf = font.render(line.strip(), True, (255, 255, 255))
            screen.blit(text_surf, (text_x, text_y + i * 28))

    def _draw_click_hint(self, screen: pygame.Surface):
        """클릭 힌트"""
        font = self.fonts.get("small")
        if not font:
            return

        alpha = int(128 + 127 * math.sin(pygame.time.get_ticks() / 300))
        hint_surf = font.render("Click to continue...", True, (200, 200, 200))
        hint_surf.set_alpha(alpha)
        hint_rect = hint_surf.get_rect(
            midbottom=(self.screen_size[0] // 2, self.screen_size[1] - 20)
        )
        screen.blit(hint_surf, hint_rect)


# =========================================================
# 시각적 피드백 효과 클래스들
# =========================================================


