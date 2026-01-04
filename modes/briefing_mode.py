# modes/briefing_mode.py
"""
BriefingMode - 작전실 (Episode 시스템 기반)

Episode 기반 미션 선택:
- 메인 에피소드 (ep1~ep5): 스토리 진행
- 훈련장: 무한 웨이브 (자유 전투)
"""

import pygame
import math
import json
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass

import config
from modes.base_mode import GameMode, ModeConfig
from mode_configs.config_episodes import (
    get_episode, EpisodeData, SegmentType
)
from systems.episode_resource_loader import get_episode_loader
from ui_components import UILayoutManager, TabData, TabState, UnifiedParticleSystem


@dataclass
class EpisodeCard:
    """에피소드 카드"""
    episode_id: str
    rect: pygame.Rect
    is_available: bool
    is_completed: bool
    hover_progress: float = 0.0


class BriefingMode(GameMode):
    """
    작전실 모드 - Episode 시스템 기반

    특징:
    - 에피소드 목록 표시 (ep1~ep5)
    - 에피소드 선택 및 출격
    - 훈련장 (무한 웨이브)
    - 미션 완료 시 BaseHub 귀환
    """

    # 에피소드 ID 목록 (순서대로)
    # 두 개의 미션 라인
    MAIN_CAMPAIGN_IDS = ["ep1", "ep2", "ep3", "ep4", "ep5"]
    GALACTIC_WAR_IDS = ["gw_ep1", "gw_ep2", "gw_ep3", "gw_ep4", "gw_ep5"]

    def get_config(self) -> ModeConfig:
        return ModeConfig(
            mode_name="briefing",
            perspective_enabled=False,
            background_type="static",
            parallax_enabled=False,
            meteor_enabled=False,
            show_wave_ui=False,
            show_skill_indicators=False,
            wave_system_enabled=False,
            spawn_system_enabled=False,
            asset_prefix="briefing",
        )

    def init(self):
        """작전실 모드 초기화"""
        config.GAME_MODE = "briefing"

        # UI 매니저 초기화
        self.ui_manager = UILayoutManager(self.screen_size, self.fonts)

        # 진행 상황 로드
        self._load_campaign_progress()

        # UI 상태
        self.selected_tab = "main_campaign"  # main_campaign, galactic_war
        self.selected_episode: Optional[str] = None
        self.hovered_episode: Optional[str] = None

        # 스크롤 상태
        self.scroll_offset = 0
        self.max_scroll = 0

        # 배경 및 파티클
        self.background = self._create_background()
        self.particle_system = UnifiedParticleSystem(self.screen_size, 45, "briefing")

        # 애니메이션 상태
        self.animation_time = 0.0
        self.pulse_phase = 0.0

        # 탭 데이터 - 두 개의 미션 라인
        self.tabs = [
            TabData(id="main_campaign", name="MAIN CAMPAIGN", icon="★", color=(80, 160, 255)),
            TabData(id="galactic_war", name="GALACTIC WAR", icon="⚔", color=(255, 100, 100)),
        ]
        self.tab_states: Dict[str, TabState] = {tab.id: TabState() for tab in self.tabs}
        self.tab_rects: Dict[str, pygame.Rect] = {}

        # 에피소드 카드
        self.episode_cards: List[EpisodeCard] = []

        # 에피소드 데이터 캐시
        self.episodes_data: Dict[str, EpisodeData] = {}
        self._load_episodes_data()

        # 버튼 상태
        self.launch_rect = None
        self.back_rect = None
        self.launch_hover = False
        self.back_hover = False

        # 다음 에피소드 자동 선택
        self._auto_select_next_episode()

        print("INFO: BriefingMode initialized (Episode System)")

    def _get_current_episode_ids(self) -> List[str]:
        """현재 선택된 탭의 에피소드 ID 목록 반환"""
        if self.selected_tab == "galactic_war":
            return self.GALACTIC_WAR_IDS
        else:
            return self.MAIN_CAMPAIGN_IDS

    def _load_episodes_data(self):
        """에피소드 데이터 로드 - 두 미션 라인 모두"""
        for ep_id in self.MAIN_CAMPAIGN_IDS + self.GALACTIC_WAR_IDS:
            episode = get_episode(ep_id)
            if episode:
                self.episodes_data[ep_id] = episode
                print(f"DEBUG: Loaded episode {ep_id}: {episode.title}")

    def _create_background(self) -> pygame.Surface:
        """배경 생성"""
        bg_path = config.ASSET_DIR / "images" / "base" / "facilities" / "facility_bg.png"
        try:
            if bg_path.exists():
                bg = pygame.image.load(str(bg_path)).convert()
                return pygame.transform.smoothscale(bg, self.screen_size)
        except Exception as e:
            print(f"WARNING: Failed to load facility_bg for briefing: {e}")

        # 폴백: 기본 그라데이션 배경
        bg = self.ui_manager.create_gradient_background(
            base_color=(8, 12, 28),
            variation=22
        )
        return bg

    def _load_campaign_progress(self):
        """캠페인 진행 상황 로드"""
        self.completed_episodes: List[str] = []
        self.current_act: int = 1

        save_path = Path("saves/campaign_progress.json")
        try:
            if save_path.exists():
                with open(save_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.completed_episodes = data.get("completed_episodes", [])
                self.current_act = data.get("current_act", 1)

                # shared_state 동기화
                self.engine.shared_state['completed_episodes'] = self.completed_episodes
                self.engine.shared_state['current_act'] = self.current_act
                print(f"INFO: Loaded campaign progress - completed: {len(self.completed_episodes)} episodes, act: {self.current_act}")
            else:
                self.completed_episodes = self.engine.shared_state.get('completed_episodes', [])
                self.current_act = self.engine.shared_state.get('current_act', 1)
        except Exception as e:
            print(f"WARNING: Failed to load campaign progress: {e}")
            self.completed_episodes = []
            self.current_act = 1

    def _auto_select_next_episode(self):
        """다음 에피소드 자동 선택"""
        episode_ids = self._get_current_episode_ids()
        for ep_id in episode_ids:
            if ep_id not in self.completed_episodes:
                if self._is_episode_available(ep_id):
                    self.selected_episode = ep_id
                    return

        # 모두 완료했으면 마지막 에피소드 선택
        if episode_ids:
            self.selected_episode = episode_ids[-1]

    def _is_episode_available(self, episode_id: str) -> bool:
        """에피소드 진행 가능 여부"""
        episode = self.episodes_data.get(episode_id)
        if not episode:
            return False

        # 첫 번째 에피소드는 항상 가능
        if episode_id in ["ep1", "gw_ep1"]:
            return True

        # 이전 에피소드가 완료되어야 함
        # ep2 → ep1, gw_ep2 → gw_ep1
        if episode_id.startswith("gw_ep"):
            episode_num = int(episode_id.replace("gw_ep", ""))
            prev_episode_id = f"gw_ep{episode_num - 1}"
        else:
            episode_num = int(episode_id.replace("ep", ""))
            prev_episode_id = f"ep{episode_num - 1}"

        return prev_episode_id in self.completed_episodes

    def _get_current_episodes(self) -> Dict[str, EpisodeData]:
        """현재 탭의 에피소드 목록"""
        episode_ids = self._get_current_episode_ids()
        return {ep_id: self.episodes_data[ep_id] for ep_id in episode_ids if ep_id in self.episodes_data}

    def update(self, dt: float, current_time: float):
        """업데이트"""
        self.animation_time += dt
        self.pulse_phase = (math.sin(self.animation_time * 3) + 1) / 2

        # 파티클 업데이트
        self.particle_system.update(dt)

        # 마우스 위치
        mouse_pos = pygame.mouse.get_pos()
        self.hovered_episode = None

        # 탭 호버 업데이트
        for tab_id, rect in self.tab_rects.items():
            state = self.tab_states[tab_id]
            if rect and rect.collidepoint(mouse_pos):
                state.hover_progress = min(1.0, state.hover_progress + dt * 6)
            else:
                state.hover_progress = max(0.0, state.hover_progress - dt * 4)

        # 에피소드 카드 호버 업데이트
        for card in self.episode_cards:
            if card.rect.collidepoint(mouse_pos):
                self.hovered_episode = card.episode_id
                card.hover_progress = min(1.0, card.hover_progress + dt * 6)
            else:
                card.hover_progress = max(0.0, card.hover_progress - dt * 4)

        # 버튼 호버
        if self.launch_rect:
            self.launch_hover = self.launch_rect.collidepoint(mouse_pos)
        if self.back_rect:
            self.back_hover = self.back_rect.collidepoint(mouse_pos)

    def render(self, screen: pygame.Surface):
        """렌더링"""
        # 배경
        screen.blit(self.background, (0, 0))

        # 파티클
        self.particle_system.render(screen)

        # 타이틀
        tab_color = self._get_tab_color()
        glow_intensity = (math.sin(self.animation_time * 2) + 1) / 2
        self.ui_manager.render_title(screen, "MISSION SELECT", tab_color, glow_intensity)

        # 탭
        self.tab_rects = self.ui_manager.render_horizontal_tabs(
            screen, self.tabs, self.selected_tab, self.tab_states, tab_width=180
        )

        # 에피소드 목록
        self._render_episode_list(screen)

        # 에피소드 상세 (선택된 경우)
        if self.selected_episode:
            self._render_episode_detail(screen)

        # 버튼
        self._render_buttons(screen)

        # 키보드 힌트
        self.ui_manager.render_keyboard_hints(screen, "Click Episode  |  Enter Launch  |  ESC Back")

    def _get_tab_color(self) -> Tuple[int, int, int]:
        """현재 탭 색상"""
        for tab in self.tabs:
            if tab.id == self.selected_tab:
                return tab.color
        return (80, 160, 255)

    def _render_episode_list(self, screen: pygame.Surface):
        """에피소드 목록 렌더링"""
        episodes = self._get_current_episodes()
        tab_color = self._get_tab_color()

        # 콘텐츠 패널
        panel_rect = self.ui_manager.render_content_panel(
            screen, "Story Episodes", tab_color
        )

        # 에피소드 카드 영역
        self.episode_cards.clear()
        card_start_y = panel_rect.y + 55
        card_height = 100
        card_spacing = 15
        card_width = panel_rect.width - 40

        # 전체 콘텐츠 높이 계산
        total_content_height = len(episodes) * (card_height + card_spacing)
        visible_height = panel_rect.height - 75
        self.max_scroll = max(0, total_content_height - visible_height)

        # 스크롤 범위 제한
        self.scroll_offset = max(0, min(self.scroll_offset, self.max_scroll))

        # 클리핑 영역 설정
        clip_rect = pygame.Rect(panel_rect.x, card_start_y, panel_rect.width, visible_height)
        screen.set_clip(clip_rect)

        episode_ids = self._get_current_episode_ids()
        for i, ep_id in enumerate(episode_ids):
            episode = episodes.get(ep_id)
            if not episode:
                continue

            card_y = card_start_y + i * (card_height + card_spacing) - self.scroll_offset

            # 화면 밖 카드 스킵
            if card_y + card_height < card_start_y - 20:
                continue
            if card_y > panel_rect.bottom:
                continue

            card_rect = pygame.Rect(
                panel_rect.x + 20,
                card_y,
                card_width,
                card_height
            )

            is_available = self._is_episode_available(ep_id)
            is_completed = ep_id in self.completed_episodes
            is_selected = ep_id == self.selected_episode

            # 카드 객체 추가
            self.episode_cards.append(EpisodeCard(
                episode_id=ep_id,
                rect=card_rect,
                is_available=is_available,
                is_completed=is_completed,
            ))

            # 호버 진행도
            hover_progress = 0.0
            for card in self.episode_cards:
                if card.episode_id == ep_id:
                    hover_progress = card.hover_progress
                    break

            # 카드 렌더링
            self._render_episode_card(
                screen, card_rect, ep_id, episode,
                is_available, is_completed, is_selected, hover_progress
            )

        # 클리핑 해제
        screen.set_clip(None)

    def _render_episode_card(
        self, screen: pygame.Surface, rect: pygame.Rect,
        episode_id: str, episode: EpisodeData,
        is_available: bool, is_completed: bool, is_selected: bool,
        hover_progress: float
    ):
        """에피소드 카드 렌더링 - Web Button 스타일"""
        # Episode별 색상 (에피소드 번호 추출: ep1 -> 1, gw_ep1 -> 1)
        if episode_id.startswith("gw_ep"):
            episode_num = int(episode_id.replace("gw_ep", ""))
        else:
            episode_num = int(episode_id.replace("ep", ""))

        episode_colors = {
            1: (80, 160, 255),   # 파랑
            2: (80, 200, 140),   # 녹색
            3: (255, 180, 80),   # 주황
            4: (200, 100, 150),  # 분홍
            5: (150, 100, 220),  # 보라
        }
        type_color = episode_colors.get(episode_num, (80, 160, 255))

        # === Web Button 스타일: 좌측 컬러 박스 + 우측 밝은 텍스트 영역 ===

        icon_box_width = 140  # 좌측 박스 너비

        # 좌측 EPISODE 박스 (Episode 컬러)
        icon_rect = pygame.Rect(rect.x, rect.y, icon_box_width, rect.height)

        if not is_available:
            icon_color = (100, 100, 120)  # 회색
        elif is_completed:
            icon_color = (40, 180, 100)  # 녹색
        elif is_selected:
            # 선택 시 더 밝게
            icon_color = tuple(min(255, int(c * 1.3)) for c in type_color)
        else:
            icon_color = type_color

        # 호버 시 약간 밝아짐
        if hover_progress > 0 and is_available:
            icon_color = tuple(min(255, int(c + 25 * hover_progress)) for c in icon_color)

        pygame.draw.rect(screen, icon_color, icon_rect, border_radius=8)

        # EPISODE 번호 및 텍스트 (좌측 박스 내부)
        ep_font = self.fonts.get("xlarge", self.fonts["large"])
        ep_num_text = f"{episode_num}"
        ep_num_surf = ep_font.render(ep_num_text, True, (255, 255, 255))
        ep_num_rect = ep_num_surf.get_rect(center=(icon_rect.centerx, icon_rect.centery - 15))
        screen.blit(ep_num_surf, ep_num_rect)

        # "EP" 라벨
        ep_label_font = self.fonts.get("small", self.fonts["tiny"])
        ep_label_surf = ep_label_font.render("EP", True, (240, 240, 240))
        ep_label_rect = ep_label_surf.get_rect(center=(icon_rect.centerx, icon_rect.centery + 18))
        screen.blit(ep_label_surf, ep_label_rect)

        # 우측 텍스트 영역 (밝은 배경)
        text_rect = pygame.Rect(rect.x + icon_box_width, rect.y,
                               rect.width - icon_box_width, rect.height)

        # 텍스트 영역 배경
        if not is_available:
            text_bg_color = (200, 200, 210)  # 어두운 회색
            name_color = (100, 100, 120)
        elif is_completed:
            text_bg_color = (230, 245, 235)  # 녹색 톤
            name_color = (40, 100, 60)
        elif is_selected:
            text_bg_color = (235, 240, 250)  # 밝은 파랑 톤
            name_color = (30, 50, 80)
        else:
            text_bg_color = (240, 242, 245)  # 밝은 회색
            name_color = (40, 45, 55)

        pygame.draw.rect(screen, text_bg_color, text_rect, border_radius=8)

        # 전체 테두리
        border_color = icon_color if is_available else (150, 150, 160)
        if is_selected:
            pygame.draw.rect(screen, border_color, rect, 3, border_radius=8)  # 선택 시 두껍게
        else:
            pygame.draw.rect(screen, border_color, rect, 2, border_radius=8)

        # 에피소드 제목 (한글)
        text_x = text_rect.x + 20
        title_font = self.fonts.get("medium", self.fonts["small"])
        title_surf = title_font.render(episode.title, True, name_color)
        screen.blit(title_surf, (text_x, text_rect.y + 12))

        # 영문 제목
        title_en = getattr(episode, 'title_en', '') or episode_id.upper()
        subtitle_color = type_color if is_available else (120, 120, 130)
        if not is_available:
            subtitle_color = (120, 120, 130)
        subtitle_font = self.fonts.get("small", self.fonts["tiny"])
        subtitle_surf = subtitle_font.render(title_en, True, subtitle_color)
        screen.blit(subtitle_surf, (text_x, text_rect.y + 38))

        # 설명
        desc_color = (80, 90, 110) if is_available else (120, 120, 130)
        desc = episode.description[:55] + "..." if len(episode.description) > 55 else episode.description
        desc_font = self.fonts.get("light_small", self.fonts["tiny"])
        desc_surf = desc_font.render(desc, True, desc_color)
        screen.blit(desc_surf, (text_x, text_rect.y + 62))

        # 우측 상태 영역
        right_x = text_rect.right - 100

        if is_completed:
            # 완료 뱃지 (우측 상단)
            badge_x = text_rect.right - 75
            badge_y = text_rect.y + 10
            badge_surf = pygame.Surface((70, 26), pygame.SRCALPHA)
            badge_surf.fill((60, 200, 120, 220))
            screen.blit(badge_surf, (badge_x, badge_y))
            pygame.draw.rect(screen, (40, 160, 90), (badge_x, badge_y, 70, 26), 2, border_radius=6)
            clear_text = self.fonts["medium"].render("CLEAR", True, (255, 255, 255))
            screen.blit(clear_text, clear_text.get_rect(center=(badge_x + 35, badge_y + 13)))

            # 재도전 표시 (작게)
            retry_font = self.fonts.get("tiny", self.fonts["small"])
            retry_text = retry_font.render("REPLAY", True, (100, 120, 140))
            screen.blit(retry_text, (badge_x + 10, badge_y + 30))
        elif is_available:
            # 보상 표시 (우측 하단)
            rewards = episode.rewards
            if rewards and rewards.get("credits", 0) > 0:
                coin_x = text_rect.right - 110
                coin_y = text_rect.bottom - 28

                # 코인 아이콘
                pygame.draw.circle(screen, (255, 200, 60), (coin_x, coin_y + 8), 8)

                # 보상 금액
                reward_text = self.fonts["medium"].render(f"+{rewards['credits']}", True, (200, 150, 30))
                screen.blit(reward_text, (coin_x + 16, coin_y))
        else:
            # 잠금 표시 (우측 중앙)
            lock_font = self.fonts.get("small", self.fonts["tiny"])
            lock_text = lock_font.render("LOCKED", True, (130, 130, 140))
            lock_rect = lock_text.get_rect(center=(text_rect.right - 50, text_rect.centery))
            screen.blit(lock_text, lock_rect)

    def _render_episode_detail(self, screen: pygame.Surface):
        """선택된 에피소드 상세 정보"""
        episode = self.episodes_data.get(self.selected_episode)
        if not episode:
            return

        # 화면 하단에 상세 정보 패널
        detail_rect = pygame.Rect(
            self.screen_size[0] // 2 - 350,
            self.screen_size[1] - 150,
            700,
            90
        )

        # 패널 배경
        panel_surf = pygame.Surface((detail_rect.width, detail_rect.height), pygame.SRCALPHA)
        panel_surf.fill((20, 30, 50, 220))
        screen.blit(panel_surf, detail_rect.topleft)
        pygame.draw.rect(screen, (60, 80, 120), detail_rect, 1, border_radius=8)

        # 에피소드 정보
        # 에피소드 번호 추출
        if self.selected_episode.startswith("gw_ep"):
            episode_num = int(self.selected_episode.replace("gw_ep", ""))
            series_name = "Galactic War"
        else:
            episode_num = int(self.selected_episode.replace("ep", ""))
            series_name = "Episode"

        # 제목
        title_text = f"{series_name} {episode_num}: {episode.title}"
        title_surf = self.fonts["medium"].render(title_text, True, (255, 255, 255))
        screen.blit(title_surf, (detail_rect.x + 20, detail_rect.y + 15))

        # 세그먼트 정보
        segment_counts = {}
        for seg in episode.segments:
            seg_name = seg.type.name
            segment_counts[seg_name] = segment_counts.get(seg_name, 0) + 1

        seg_parts = [f"{name}: {count}" for name, count in segment_counts.items()]
        seg_str = " | ".join(seg_parts[:4])  # 최대 4개만 표시
        seg_font = self.fonts.get("light_small", self.fonts["small"])
        seg_surf = seg_font.render(f"Segments: {seg_str}", True, (160, 170, 190))
        screen.blit(seg_surf, (detail_rect.x + 20, detail_rect.y + 45))

        # 보상 정보
        rewards = episode.rewards
        if rewards:
            reward_parts = []
            if rewards.get("credits", 0) > 0:
                reward_parts.append(f"Credits: {rewards['credits']}")
            if rewards.get("exp", 0) > 0:
                reward_parts.append(f"EXP: {rewards['exp']}")

            if reward_parts:
                reward_str = " | ".join(reward_parts)
                reward_surf = self.fonts["small"].render(f"Rewards: {reward_str}", True, (255, 220, 100))
                screen.blit(reward_surf, (detail_rect.right - reward_surf.get_width() - 20, detail_rect.y + 35))

    def _render_buttons(self, screen: pygame.Surface):
        """버튼 렌더링"""
        can_launch = False
        if self.selected_episode:
            can_launch = self._is_episode_available(self.selected_episode)

        # 출격 버튼
        self.launch_rect = self.ui_manager.render_action_button(
            screen, "LAUNCH", self.launch_hover, can_launch, danger=True
        )

        # 뒤로가기 버튼
        self.back_rect = self.ui_manager.render_back_button(screen, self.back_hover)

    def handle_event(self, event: pygame.event.Event):
        """이벤트 처리"""
        # 마우스 휠 스크롤
        if event.type == pygame.MOUSEWHEEL:
            scroll_speed = 40
            self.scroll_offset -= event.y * scroll_speed
            self.scroll_offset = max(0, min(self.scroll_offset, self.max_scroll))
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = event.pos

            # 탭 클릭
            for tab_id, rect in self.tab_rects.items():
                if rect.collidepoint(mouse_pos):
                    self.selected_tab = tab_id
                    self.scroll_offset = 0
                    # 탭 변경 시 해당 미션 라인의 첫 번째 에피소드 자동 선택
                    self._auto_select_next_episode()
                    if hasattr(self, 'sound_manager') and self.sound_manager:
                        self.sound_manager.play_sfx("click")
                    return

            # 에피소드 카드 클릭
            for card in self.episode_cards:
                if card.rect.collidepoint(mouse_pos) and card.is_available:
                    self.selected_episode = card.episode_id
                    if hasattr(self, 'sound_manager') and self.sound_manager:
                        self.sound_manager.play_sfx("click")
                    return

            # 출격 버튼
            if self.launch_rect and self.launch_rect.collidepoint(mouse_pos):
                self._on_launch()
                return

            # 뒤로가기 버튼
            if self.back_rect and self.back_rect.collidepoint(mouse_pos):
                self._on_back()
                return

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._on_back()
                return

            if event.key == pygame.K_RETURN:
                self._on_launch()
                return

            # TAB 키는 탭이 하나뿐이므로 무시

    def _on_launch(self):
        """에피소드 출격"""
        if not self.selected_episode:
            return

        if not self._is_episode_available(self.selected_episode):
            return

        episode = self.episodes_data.get(self.selected_episode)
        if not episode:
            return

        print(f"INFO: Launching episode: {self.selected_episode}")

        if hasattr(self, 'sound_manager') and self.sound_manager:
            self.sound_manager.play_sfx("level_up")

        # EpisodeMode로 전환
        from modes.episode_mode import EpisodeMode
        self.request_switch_mode(EpisodeMode, episode_id=self.selected_episode)

    def _on_back(self):
        """뒤로가기 - BaseHub로"""
        self.request_pop_mode()

    def on_enter(self):
        super().on_enter()
        # 진행 상황 다시 로드
        self._load_campaign_progress()
        self._auto_select_next_episode()

    def on_exit(self):
        super().on_exit()


print("INFO: briefing_mode.py loaded (Episode System)")
