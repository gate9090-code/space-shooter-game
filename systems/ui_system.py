# systems/ui_system.py
"""
UISystem - UI 렌더링 시스템
HUD, 메뉴, 오버레이 등 UI 렌더링
모든 모드에서 공유 (표시 항목만 다르게)
"""

import pygame
from typing import Dict, Tuple, Optional, List
from dataclasses import dataclass
import config


@dataclass
class UIConfig:
    """UI 설정"""
    # HUD 표시 설정
    show_hp_bar: bool = True
    show_score: bool = True
    show_wave_info: bool = True
    show_level_info: bool = True
    show_skill_indicators: bool = True
    show_minimap: bool = False

    # 위치 설정
    hp_bar_position: str = "top_left"
    score_position: str = "top_right"
    wave_position: str = "top_center"


class UISystem:
    """
    UI 시스템 - 모든 모드에서 공유하는 UI 로직

    기능:
    - HUD 렌더링 (HP, 스코어, 웨이브 등)
    - 메뉴 렌더링 (일시정지, 상점 등)
    - 오버레이 렌더링 (설정, 종료 확인 등)
    """

    def __init__(self, ui_config: UIConfig = None):
        """
        UI 시스템 초기화

        Args:
            ui_config: UI 설정
        """
        self.config = ui_config or UIConfig()

    def draw_hud(
        self,
        screen: pygame.Surface,
        screen_size: Tuple[int, int],
        fonts: Dict,
        player,
        game_data: Dict,
    ):
        """
        HUD 렌더링

        Args:
            screen: pygame 화면 Surface
            screen_size: 화면 크기
            fonts: 폰트 딕셔너리
            player: 플레이어
            game_data: 게임 데이터
        """
        margin = 20

        # HP 바
        if self.config.show_hp_bar and player:
            self._draw_hp_bar(screen, screen_size, fonts, player, margin)

        # 스코어
        if self.config.show_score:
            self._draw_score(screen, screen_size, fonts, game_data, margin)

        # 웨이브 정보
        if self.config.show_wave_info:
            self._draw_wave_info(screen, screen_size, fonts, game_data)

        # 레벨 정보
        if self.config.show_level_info and player:
            self._draw_level_info(screen, screen_size, fonts, player, game_data, margin)

    def _draw_hp_bar(
        self,
        screen: pygame.Surface,
        screen_size: Tuple[int, int],
        fonts: Dict,
        player,
        margin: int,
    ):
        """HP 바 렌더링"""
        bar_width = 250
        bar_height = 25
        x = margin
        y = margin

        # 배경
        pygame.draw.rect(screen, (50, 50, 50), (x, y, bar_width, bar_height))

        # HP 바
        hp_ratio = max(0, player.hp / player.max_hp)
        hp_color = config.UI_COLORS["HP_NORMAL"] if hp_ratio > 0.3 else config.UI_COLORS["HP_LOW"]
        pygame.draw.rect(screen, hp_color, (x, y, int(bar_width * hp_ratio), bar_height))

        # 테두리
        pygame.draw.rect(screen, config.WHITE, (x, y, bar_width, bar_height), 2)

        # HP 텍스트
        hp_text = fonts["small"].render(f"{int(player.hp)}/{int(player.max_hp)}", True, config.WHITE)
        text_rect = hp_text.get_rect(center=(x + bar_width // 2, y + bar_height // 2))
        screen.blit(hp_text, text_rect)

    def _draw_score(
        self,
        screen: pygame.Surface,
        screen_size: Tuple[int, int],
        fonts: Dict,
        game_data: Dict,
        margin: int,
    ):
        """스코어 렌더링"""
        score = game_data.get('score', 0)
        score_text = fonts["medium"].render(f"COIN: {score}", True, config.UI_COLORS["COIN_GOLD"])
        score_rect = score_text.get_rect(topright=(screen_size[0] - margin, margin))
        screen.blit(score_text, score_rect)

    def _draw_wave_info(
        self,
        screen: pygame.Surface,
        screen_size: Tuple[int, int],
        fonts: Dict,
        game_data: Dict,
    ):
        """웨이브 정보 렌더링"""
        current_wave = game_data.get('current_wave', 1)
        wave_kills = game_data.get('wave_kills', 0)
        target_kills = game_data.get('wave_target_kills', 0)

        # 웨이브 번호
        wave_text = fonts["medium"].render(f"WAVE {current_wave}", True, config.WHITE)
        wave_rect = wave_text.get_rect(midtop=(screen_size[0] // 2, 10))
        screen.blit(wave_text, wave_rect)

        # 킬 카운트
        kill_text = fonts["small"].render(f"Kills: {wave_kills}/{target_kills}", True, config.UI_COLORS["TEXT_SECONDARY"])
        kill_rect = kill_text.get_rect(midtop=(screen_size[0] // 2, 40))
        screen.blit(kill_text, kill_rect)

    def _draw_level_info(
        self,
        screen: pygame.Surface,
        screen_size: Tuple[int, int],
        fonts: Dict,
        player,
        game_data: Dict,
        margin: int,
    ):
        """레벨 정보 렌더링"""
        level = game_data.get('player_level', 1)
        level_text = fonts["small"].render(f"LV.{level}", True, config.UI_COLORS["PRIMARY"])
        level_rect = level_text.get_rect(topleft=(margin, 60))
        screen.blit(level_text, level_rect)

    def draw_pause_overlay(
        self,
        screen: pygame.Surface,
        screen_size: Tuple[int, int],
        fonts: Dict,
    ):
        """일시정지 오버레이 렌더링"""
        # 반투명 배경
        overlay = pygame.Surface(screen_size, pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        # 일시정지 텍스트
        pause_text = fonts["huge"].render("PAUSED", True, config.WHITE)
        pause_rect = pause_text.get_rect(center=(screen_size[0] // 2, screen_size[1] // 2 - 50))
        screen.blit(pause_text, pause_rect)

        # 안내 텍스트
        help_text = fonts["medium"].render("Press P to Resume", True, config.UI_COLORS["TEXT_SECONDARY"])
        help_rect = help_text.get_rect(center=(screen_size[0] // 2, screen_size[1] // 2 + 30))
        screen.blit(help_text, help_rect)

    def draw_game_over_overlay(
        self,
        screen: pygame.Surface,
        screen_size: Tuple[int, int],
        fonts: Dict,
        game_data: Dict,
    ):
        """게임 오버 오버레이 렌더링"""
        # 반투명 배경
        overlay = pygame.Surface(screen_size, pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        screen.blit(overlay, (0, 0))

        # 게임 오버 텍스트
        over_text = fonts["huge"].render("GAME OVER", True, config.UI_COLORS["DANGER"])
        over_rect = over_text.get_rect(center=(screen_size[0] // 2, screen_size[1] // 2 - 80))
        screen.blit(over_text, over_rect)

        # 스코어
        score = game_data.get('score', 0)
        score_text = fonts["large"].render(f"Final Score: {score}", True, config.UI_COLORS["COIN_GOLD"])
        score_rect = score_text.get_rect(center=(screen_size[0] // 2, screen_size[1] // 2))
        screen.blit(score_text, score_rect)

        # 웨이브
        wave = game_data.get('current_wave', 1)
        wave_text = fonts["medium"].render(f"Reached Wave: {wave}", True, config.WHITE)
        wave_rect = wave_text.get_rect(center=(screen_size[0] // 2, screen_size[1] // 2 + 50))
        screen.blit(wave_text, wave_rect)

        # 재시작 안내
        restart_text = fonts["medium"].render("Press R to Restart", True, config.UI_COLORS["TEXT_SECONDARY"])
        restart_rect = restart_text.get_rect(center=(screen_size[0] // 2, screen_size[1] // 2 + 120))
        screen.blit(restart_text, restart_rect)

    def draw_quit_confirm_overlay(
        self,
        screen: pygame.Surface,
        screen_size: Tuple[int, int],
        fonts: Dict,
    ):
        """종료 확인 오버레이 렌더링"""
        # 반투명 배경
        overlay = pygame.Surface(screen_size, pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        # 패널 배경
        panel_width = 500
        panel_height = 200
        panel_x = (screen_size[0] - panel_width) // 2
        panel_y = (screen_size[1] - panel_height) // 2

        panel = pygame.Surface((panel_width, panel_height))
        panel.fill((40, 40, 60))
        pygame.draw.rect(panel, config.WHITE, panel.get_rect(), 3)
        screen.blit(panel, (panel_x, panel_y))

        # 확인 메시지
        msg_text = fonts["large"].render("Quit Game?", True, config.WHITE)
        msg_rect = msg_text.get_rect(center=(screen_size[0] // 2, screen_size[1] // 2 - 30))
        screen.blit(msg_text, msg_rect)

        # 버튼
        y_text = fonts["medium"].render("Y - Quit", True, config.UI_COLORS["DANGER"])
        y_rect = y_text.get_rect(center=(screen_size[0] // 2 - 80, screen_size[1] // 2 + 40))
        screen.blit(y_text, y_rect)

        n_text = fonts["medium"].render("N - Cancel", True, config.UI_COLORS["SUCCESS"])
        n_rect = n_text.get_rect(center=(screen_size[0] // 2 + 80, screen_size[1] // 2 + 40))
        screen.blit(n_text, n_rect)

    def draw_victory_overlay(
        self,
        screen: pygame.Surface,
        screen_size: Tuple[int, int],
        fonts: Dict,
        game_data: Dict,
    ):
        """승리 오버레이 렌더링"""
        # 반투명 배경 (황금색)
        overlay = pygame.Surface(screen_size, pygame.SRCALPHA)
        overlay.fill((50, 40, 0, 180))
        screen.blit(overlay, (0, 0))

        # 승리 텍스트
        victory_text = fonts["huge"].render("VICTORY!", True, config.UI_COLORS["PRIMARY"])
        victory_rect = victory_text.get_rect(center=(screen_size[0] // 2, screen_size[1] // 2 - 80))
        screen.blit(victory_text, victory_rect)

        # 스코어
        score = game_data.get('score', 0)
        score_text = fonts["large"].render(f"Total Score: {score}", True, config.UI_COLORS["COIN_GOLD"])
        score_rect = score_text.get_rect(center=(screen_size[0] // 2, screen_size[1] // 2))
        screen.blit(score_text, score_rect)

        # 옵션
        options_y = screen_size[1] // 2 + 80

        r_text = fonts["medium"].render("R - Restart", True, config.WHITE)
        r_rect = r_text.get_rect(center=(screen_size[0] // 2 - 120, options_y))
        screen.blit(r_text, r_rect)

        b_text = fonts["medium"].render("B - Boss Rush", True, config.UI_COLORS["DANGER"])
        b_rect = b_text.get_rect(center=(screen_size[0] // 2 + 120, options_y))
        screen.blit(b_text, b_rect)

        q_text = fonts["medium"].render("Q - Quit", True, config.UI_COLORS["TEXT_SECONDARY"])
        q_rect = q_text.get_rect(center=(screen_size[0] // 2, options_y + 50))
        screen.blit(q_text, q_rect)


print("INFO: ui_system.py loaded")
