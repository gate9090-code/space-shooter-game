# modes/archive_mode.py
"""
ArchiveMode - 성찰의 기록 보관소
철학적 대화를 다시 볼 수 있는 아카이브 시설
"""

import pygame
import math
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass

import config
from modes.base_mode import GameMode, ModeConfig


@dataclass
class DialogueEntry:
    """대화 항목"""
    key: str
    title: str
    subtitle: str
    category: str
    unlock_act: int  # 해금에 필요한 Act
    seen: bool = False
    unlocked: bool = False


class ArchiveMode(GameMode):
    """
    성찰의 기록 보관소
    철학적 대화 목록을 표시하고 선택 시 ReflectionMode로 이동
    """

    # =========================================================================
    # 개발자 테스트 모드 - True로 설정하면 모든 대화 해금
    # 배포 시 False로 변경할 것
    # =========================================================================
    DEV_MODE = True

    # 대화 카테고리
    CATEGORIES = {
        "earth_beauty": {
            "title": "지구의 아름다움",
            "title_en": "EARTH BEAUTY",
            "color": (100, 180, 120),
        },
        "philosophy": {
            "title": "철학적 성찰",
            "title_en": "PHILOSOPHY",
            "color": (150, 120, 200),
        }
    }

    # 대화 목록 (키, 제목, 부제, 카테고리, 해금 Act)
    DIALOGUE_LIST = [
        # 지구의 아름다움
        ("color_names", "색깔의 이름", "봄의 기억", "earth_beauty", 2),
        ("cloud_shapes", "구름의 모양", "여름 하늘", "earth_beauty", 2),
        ("rain_smell", "비의 냄새", "가을비", "earth_beauty", 3),
        ("why_stars_beautiful", "별이 아름다운 이유", "겨울밤", "earth_beauty", 3),
        ("why_flowers_fall", "꽃이 지는 이유", "낙화", "earth_beauty", 4),
        ("andromeda_records", "안드로메다 기록", "고대 영상", "earth_beauty", 4),
        # 철학적 성찰
        ("eternity_vs_moment", "영원 vs 순간", "석양", "philosophy", 4),
        ("chaos_eats_time", "시간을 먹는 카오스", "차원 게이트", "philosophy", 5),
        ("why_andromeda_stopped_time", "안드로메다가 시간을 멈춘 이유", "위원회 기록", "philosophy", 5),
        ("does_time_exist", "시간이란 존재하는가?", "최종 성찰", "philosophy", 6),
    ]

    def get_config(self) -> ModeConfig:
        return ModeConfig(
            mode_name="archive",
            perspective_enabled=False,
            wave_system_enabled=False,
            spawn_system_enabled=False,
            show_wave_ui=False,
        )

    def init(self):
        """초기화"""
        config.GAME_MODE = "archive"

        # 저장 파일에서 진행 상황 로드
        self._load_progress()

    def _load_progress(self):
        """저장 파일에서 진행 상황 로드"""
        import json
        from pathlib import Path

        save_path = Path("saves/campaign_progress.json")
        try:
            if save_path.exists():
                with open(save_path, 'r', encoding='utf-8') as f:
                    save_data = json.load(f)
                self.current_act = save_data.get('current_act', 1)
                self.seen_reflections = save_data.get('seen_reflections', [])
                self.game_cleared = save_data.get('game_cleared', False)
            else:
                # 저장 파일이 없으면 shared_state에서 가져옴
                self.current_act = self.engine.shared_state.get('current_act', 1)
                self.seen_reflections = self.engine.shared_state.get('seen_reflections', [])
                self.game_cleared = self.engine.shared_state.get('game_cleared', False)
        except Exception as e:
            print(f"WARNING: Failed to load progress: {e}")
            self.current_act = self.engine.shared_state.get('current_act', 1)
            self.seen_reflections = self.engine.shared_state.get('seen_reflections', [])
            self.game_cleared = self.engine.shared_state.get('game_cleared', False)

        # 대화 목록 생성
        self.dialogues: List[DialogueEntry] = []
        self._build_dialogue_list()

        # UI 상태
        self.scroll_offset = 0
        self.max_scroll = 0
        self.selected_index = -1
        self.hovered_index = -1
        self.animation_time = 0.0
        self.fade_alpha = 255

        # 카테고리별 접기/펼치기
        self.category_expanded = {
            "earth_beauty": True,
            "philosophy": True,
        }

        # 항목 rect 저장
        self.item_rects: List[pygame.Rect] = []
        self.category_rects: Dict[str, pygame.Rect] = {}

        # 커스텀 커서
        self.custom_cursor = self._load_base_cursor()

        if self.DEV_MODE:
            print("INFO: ArchiveMode DEV_MODE enabled - all dialogues unlocked")
        print("INFO: ArchiveMode initialized")

    def _build_dialogue_list(self):
        """대화 목록 빌드"""
        for key, title, subtitle, category, unlock_act in self.DIALOGUE_LIST:
            # DEV_MODE면 모두 해금
            if self.DEV_MODE:
                unlocked = True
            # 해금 조건 확인
            elif unlock_act == 6:
                # Act 6 = 게임 클리어
                unlocked = self.game_cleared
            else:
                unlocked = self.current_act >= unlock_act

            # 이미 본 대화인지 확인
            seen = key in self.seen_reflections

            self.dialogues.append(DialogueEntry(
                key=key,
                title=title,
                subtitle=subtitle,
                category=category,
                unlock_act=unlock_act,
                unlocked=unlocked,
                seen=seen,
            ))

    def _get_dialogues_by_category(self, category: str) -> List[DialogueEntry]:
        """카테고리별 대화 목록"""
        return [d for d in self.dialogues if d.category == category]

    # =========================================================================
    # 업데이트
    # =========================================================================

    def update(self, dt: float, current_time: float):
        self.animation_time += dt

        # 페이드 인
        if self.fade_alpha > 0:
            self.fade_alpha = max(0, self.fade_alpha - 400 * dt)

    # =========================================================================
    # 렌더링
    # =========================================================================

    def render(self, screen: pygame.Surface):
        SCREEN_WIDTH, SCREEN_HEIGHT = self.screen_size

        # 배경
        self._render_background(screen)

        # 헤더
        self._render_header(screen)

        # 대화 목록
        self._render_dialogue_list(screen)

        # 하단 안내
        self._render_footer(screen)

        # 페이드 인
        if self.fade_alpha > 0:
            fade_surf = pygame.Surface(self.screen_size, pygame.SRCALPHA)
            fade_surf.fill((0, 0, 0, int(self.fade_alpha)))
            screen.blit(fade_surf, (0, 0))

        # 커스텀 커서
        self._render_base_cursor(screen, self.custom_cursor)

    def _render_background(self, screen: pygame.Surface):
        """배경 렌더링 - facility_bg 이미지 사용"""
        # facility_bg 이미지 로드 시도
        if not hasattr(self, '_bg_image'):
            bg_path = config.ASSET_DIR / "images" / "facilities" / "facility_bg.png"
            try:
                if bg_path.exists():
                    self._bg_image = pygame.image.load(str(bg_path)).convert()
                    self._bg_image = pygame.transform.smoothscale(self._bg_image, self.screen_size)
                else:
                    self._bg_image = None
            except Exception as e:
                print(f"WARNING: Failed to load facility_bg for archive: {e}")
                self._bg_image = None

        if self._bg_image:
            screen.blit(self._bg_image, (0, 0))
        else:
            # 폴백: 그라데이션 배경
            for y in range(self.screen_size[1]):
                ratio = y / self.screen_size[1]
                r = int(15 + ratio * 10)
                g = int(12 + ratio * 15)
                b = int(30 + ratio * 20)
                pygame.draw.line(screen, (r, g, b), (0, y), (self.screen_size[0], y))

    def _render_header(self, screen: pygame.Surface):
        """헤더 렌더링"""
        SCREEN_WIDTH = self.screen_size[0]

        # 헤더 배경
        header_height = 100
        header_surf = pygame.Surface((SCREEN_WIDTH, header_height), pygame.SRCALPHA)
        header_surf.fill((10, 10, 25, 220))
        pygame.draw.line(header_surf, (80, 80, 150, 150),
                        (0, header_height - 1), (SCREEN_WIDTH, header_height - 1), 2)
        screen.blit(header_surf, (0, 0))

        # 타이틀
        title_font = self.fonts.get("large", self.fonts["medium"])
        title_text = title_font.render("성찰의 기록", True, (200, 180, 255))
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, 35))
        screen.blit(title_text, title_rect)

        # 서브타이틀
        subtitle_font = self.fonts.get("small", self.fonts["tiny"])
        subtitle_text = subtitle_font.render("ARCHIVE OF REFLECTIONS", True, (150, 140, 180))
        subtitle_rect = subtitle_text.get_rect(center=(SCREEN_WIDTH // 2, 65))
        screen.blit(subtitle_text, subtitle_rect)

        # 진행 상태
        total = len(self.dialogues)
        seen = sum(1 for d in self.dialogues if d.seen)
        unlocked = sum(1 for d in self.dialogues if d.unlocked)
        status_text = subtitle_font.render(
            f"해금: {unlocked}/{total}  |  완료: {seen}/{total}",
            True, (120, 120, 150)
        )
        status_rect = status_text.get_rect(center=(SCREEN_WIDTH // 2, 85))
        screen.blit(status_text, status_rect)

    def _render_dialogue_list(self, screen: pygame.Surface):
        """대화 목록 렌더링"""
        SCREEN_WIDTH, SCREEN_HEIGHT = self.screen_size

        # 목록 영역
        list_x = 100
        list_y = 120
        list_width = SCREEN_WIDTH - 200
        list_height = SCREEN_HEIGHT - 200

        # 클리핑
        list_rect = pygame.Rect(list_x, list_y, list_width, list_height)
        # pygame에서 클리핑 설정
        screen.set_clip(list_rect)

        self.item_rects.clear()
        self.category_rects.clear()

        current_y = list_y - self.scroll_offset
        item_index = 0

        for cat_key, cat_info in self.CATEGORIES.items():
            # 카테고리 헤더
            cat_rect = pygame.Rect(list_x, current_y, list_width, 50)
            self.category_rects[cat_key] = cat_rect

            if current_y + 50 > list_y and current_y < list_y + list_height:
                self._render_category_header(screen, cat_key, cat_info, cat_rect)

            current_y += 55

            # 카테고리가 펼쳐져 있으면 항목 표시
            if self.category_expanded.get(cat_key, True):
                dialogues = self._get_dialogues_by_category(cat_key)
                for dialogue in dialogues:
                    item_rect = pygame.Rect(list_x + 20, current_y, list_width - 40, 60)
                    self.item_rects.append((item_index, item_rect, dialogue))

                    if current_y + 60 > list_y and current_y < list_y + list_height:
                        is_hovered = item_index == self.hovered_index
                        is_selected = item_index == self.selected_index
                        self._render_dialogue_item(screen, dialogue, item_rect,
                                                  is_hovered, is_selected, cat_info["color"])

                    current_y += 65
                    item_index += 1

            current_y += 15  # 카테고리 간 간격

        # 최대 스크롤 계산
        self.max_scroll = max(0, current_y + self.scroll_offset - list_y - list_height + 50)

        # 클리핑 해제
        screen.set_clip(None)

        # 스크롤바 (필요시)
        if self.max_scroll > 0:
            self._render_scrollbar(screen, list_rect)

    def _render_category_header(self, screen: pygame.Surface, cat_key: str,
                                 cat_info: Dict, rect: pygame.Rect):
        """카테고리 헤더 렌더링"""
        expanded = self.category_expanded.get(cat_key, True)
        color = cat_info["color"]

        # 배경
        header_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        header_surf.fill((20, 20, 40, 180))
        pygame.draw.rect(header_surf, (*color, 150), (0, 0, rect.width, rect.height), 2, border_radius=8)
        screen.blit(header_surf, rect.topleft)

        # 접기/펼치기 아이콘
        arrow = "▼" if expanded else "▶"
        arrow_font = self.fonts.get("small", self.fonts["tiny"])
        arrow_text = arrow_font.render(arrow, True, color)
        screen.blit(arrow_text, (rect.x + 15, rect.y + 15))

        # 카테고리 이름
        title_font = self.fonts.get("medium", self.fonts["small"])
        title_text = title_font.render(cat_info["title"], True, (255, 255, 255))
        screen.blit(title_text, (rect.x + 45, rect.y + 10))

        # 영문 이름
        en_font = self.fonts.get("tiny", self.fonts["small"])
        en_text = en_font.render(cat_info["title_en"], True, (150, 150, 180))
        screen.blit(en_text, (rect.x + 45, rect.y + 30))

        # 개수
        dialogues = self._get_dialogues_by_category(cat_key)
        seen = sum(1 for d in dialogues if d.seen)
        total = len(dialogues)
        count_text = en_font.render(f"{seen}/{total}", True, color)
        count_rect = count_text.get_rect(right=rect.right - 20, centery=rect.centery)
        screen.blit(count_text, count_rect)

    def _render_dialogue_item(self, screen: pygame.Surface, dialogue: DialogueEntry,
                              rect: pygame.Rect, hovered: bool, selected: bool,
                              category_color: Tuple[int, int, int]):
        """개별 대화 항목 렌더링"""
        # 배경
        item_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)

        if not dialogue.unlocked:
            # 잠금 상태
            item_surf.fill((20, 20, 30, 150))
            border_color = (60, 60, 80, 150)
        elif hovered or selected:
            # 호버/선택
            item_surf.fill((40, 40, 70, 200))
            border_color = (*category_color, 255)
        else:
            # 일반
            item_surf.fill((25, 25, 45, 180))
            border_color = (80, 80, 120, 150)

        pygame.draw.rect(item_surf, border_color, (0, 0, rect.width, rect.height), 2, border_radius=6)
        screen.blit(item_surf, rect.topleft)

        # 상태 아이콘
        icon_x = rect.x + 20
        icon_y = rect.centery

        if not dialogue.unlocked:
            # 잠금
            icon = "🔒"
            icon_color = (100, 100, 120)
        elif dialogue.seen:
            # 완료
            icon = "✓"
            icon_color = (100, 200, 100)
        else:
            # 미완료
            icon = "○"
            icon_color = category_color

        icon_font = self.fonts.get("small", self.fonts["tiny"])
        icon_text = icon_font.render(icon, True, icon_color)
        icon_rect = icon_text.get_rect(center=(icon_x, icon_y))
        screen.blit(icon_text, icon_rect)

        # 제목
        title_x = rect.x + 50
        if dialogue.unlocked:
            title_color = (255, 255, 255) if (hovered or selected) else (220, 220, 240)
        else:
            title_color = (80, 80, 100)

        title_font = self.fonts.get("medium", self.fonts["small"])
        title_text = title_font.render(dialogue.title, True, title_color)
        screen.blit(title_text, (title_x, rect.y + 12))

        # 부제
        if dialogue.unlocked:
            subtitle_color = category_color if (hovered or selected) else (140, 140, 170)
        else:
            subtitle_color = (60, 60, 80)

        subtitle_font = self.fonts.get("tiny", self.fonts["small"])
        subtitle_text = subtitle_font.render(dialogue.subtitle, True, subtitle_color)
        screen.blit(subtitle_text, (title_x, rect.y + 35))

        # 해금 조건 (잠긴 경우)
        if not dialogue.unlocked:
            if dialogue.unlock_act == 6:
                unlock_hint = "게임 클리어 필요"
            else:
                unlock_hint = f"Act {dialogue.unlock_act} 도달 필요"

            hint_text = subtitle_font.render(unlock_hint, True, (80, 80, 100))
            hint_rect = hint_text.get_rect(right=rect.right - 20, centery=rect.centery)
            screen.blit(hint_text, hint_rect)

    def _render_scrollbar(self, screen: pygame.Surface, list_rect: pygame.Rect):
        """스크롤바 렌더링"""
        bar_width = 6
        bar_x = list_rect.right + 10
        bar_height = list_rect.height

        # 배경
        pygame.draw.rect(screen, (40, 40, 60),
                        (bar_x, list_rect.y, bar_width, bar_height), border_radius=3)

        # 핸들
        if self.max_scroll > 0:
            handle_height = max(30, bar_height * (bar_height / (bar_height + self.max_scroll)))
            handle_y = list_rect.y + (self.scroll_offset / self.max_scroll) * (bar_height - handle_height)

            pygame.draw.rect(screen, (100, 100, 150),
                            (bar_x, int(handle_y), bar_width, int(handle_height)), border_radius=3)

    def _render_footer(self, screen: pygame.Surface):
        """하단 안내 렌더링"""
        SCREEN_WIDTH, SCREEN_HEIGHT = self.screen_size

        footer_height = 60
        footer_y = SCREEN_HEIGHT - footer_height

        # 배경
        footer_surf = pygame.Surface((SCREEN_WIDTH, footer_height), pygame.SRCALPHA)
        footer_surf.fill((10, 10, 25, 220))
        pygame.draw.line(footer_surf, (80, 80, 150, 150),
                        (0, 0), (SCREEN_WIDTH, 0), 1)
        screen.blit(footer_surf, (0, footer_y))

        # 범례
        legend_font = self.fonts.get("tiny", self.fonts["small"])
        legend_items = [
            ("✓", "이미 본 대화", (100, 200, 100)),
            ("○", "새로운 대화", (150, 150, 200)),
            ("🔒", "미해금", (100, 100, 120)),
        ]

        x_offset = 50
        for icon, desc, color in legend_items:
            icon_text = legend_font.render(icon, True, color)
            screen.blit(icon_text, (x_offset, footer_y + 20))

            desc_text = legend_font.render(desc, True, (150, 150, 180))
            screen.blit(desc_text, (x_offset + 25, footer_y + 20))

            x_offset += 150

        # 조작 안내
        help_text = legend_font.render("클릭: 선택  |  ESC: 뒤로", True, (120, 120, 150))
        help_rect = help_text.get_rect(right=SCREEN_WIDTH - 50, centery=footer_y + 30)
        screen.blit(help_text, help_rect)

    # =========================================================================
    # 이벤트 처리
    # =========================================================================

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # 좌클릭
                self._handle_click(event.pos)
            elif event.button == 4:  # 스크롤 업
                self.scroll_offset = max(0, self.scroll_offset - 40)
            elif event.button == 5:  # 스크롤 다운
                self.scroll_offset = min(self.max_scroll, self.scroll_offset + 40)

        elif event.type == pygame.MOUSEMOTION:
            self._handle_hover(event.pos)

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._return_to_hub()
            elif event.key == pygame.K_UP:
                self._navigate(-1)
            elif event.key == pygame.K_DOWN:
                self._navigate(1)
            elif event.key == pygame.K_RETURN:
                if self.selected_index >= 0:
                    self._select_dialogue(self.selected_index)

    def _handle_click(self, pos: Tuple[int, int]):
        """클릭 처리"""
        # 카테고리 헤더 클릭
        for cat_key, cat_rect in self.category_rects.items():
            if cat_rect.collidepoint(pos):
                self.category_expanded[cat_key] = not self.category_expanded.get(cat_key, True)
                return

        # 대화 항목 클릭
        for idx, rect, dialogue in self.item_rects:
            if rect.collidepoint(pos):
                if dialogue.unlocked:
                    self._select_dialogue(idx)
                return

    def _handle_hover(self, pos: Tuple[int, int]):
        """호버 처리"""
        self.hovered_index = -1
        for idx, rect, dialogue in self.item_rects:
            if rect.collidepoint(pos) and dialogue.unlocked:
                self.hovered_index = idx
                break

    def _navigate(self, direction: int):
        """키보드 네비게이션"""
        unlocked_items = [(idx, d) for idx, _, d in self.item_rects if d.unlocked]
        if not unlocked_items:
            return

        if self.selected_index < 0:
            self.selected_index = unlocked_items[0][0] if direction > 0 else unlocked_items[-1][0]
        else:
            current_pos = next((i for i, (idx, _) in enumerate(unlocked_items)
                               if idx == self.selected_index), -1)
            if current_pos >= 0:
                new_pos = (current_pos + direction) % len(unlocked_items)
                self.selected_index = unlocked_items[new_pos][0]

    def _select_dialogue(self, index: int):
        """대화 선택"""
        for idx, _, dialogue in self.item_rects:
            if idx == index and dialogue.unlocked:
                print(f"INFO: Selected reflection: {dialogue.key}")
                self._start_reflection(dialogue.key)
                return

    def _start_reflection(self, scene_key: str):
        """ReflectionMode 시작"""
        # shared_state에 씬 정보 저장
        self.engine.shared_state['reflection_scene'] = {
            'scene_key': scene_key,
            'from_archive': True,
        }

        from modes.reflection_mode import ReflectionMode
        self.request_push_mode(ReflectionMode)

    def _return_to_hub(self):
        """BaseHub로 복귀"""
        self.request_pop_mode()

    # =========================================================================
    # 라이프사이클
    # =========================================================================

    def on_enter(self):
        super().on_enter()
        if self.custom_cursor:
            self._enable_custom_cursor()

    def on_exit(self):
        self._disable_custom_cursor()
        super().on_exit()

    def on_resume(self, return_data=None):
        """ReflectionMode에서 복귀 시"""
        super().on_resume(return_data)

        # 커스텀 커서 복원
        if self.custom_cursor:
            self._enable_custom_cursor()

        # 상태 갱신
        self.seen_reflections = self.engine.shared_state.get('seen_reflections', [])

        # 대화 목록 갱신
        for dialogue in self.dialogues:
            dialogue.seen = dialogue.key in self.seen_reflections


print("INFO: archive_mode.py loaded")
