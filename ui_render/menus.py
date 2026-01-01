# ui_render/menus.py
# Menu UI rendering functions (pause, game over, settings, death effects)

import pygame
import time
from typing import Tuple, Dict
import config
from .helpers import get_font, render_text_with_emoji


def draw_pause_and_over_screens(
    screen: pygame.Surface,
    screen_size: Tuple[int, int],
    font_title: pygame.font.Font,
    font_medium: pygame.font.Font,
    game_data: dict,
) -> Dict[str, pygame.Rect]:
    """
    일시정지 및 게임 오버 화면을 그립니다.

    Returns:
        Dict[str, pygame.Rect]: 버튼 ID와 클릭 영역 매핑
            - PAUSED: {"resume": Rect, "shop": Rect, "quit": Rect}
            - OVER: {"restart": Rect, "quit": Rect}
    """
    button_rects: Dict[str, pygame.Rect] = {}

    SCREEN_WIDTH, SCREEN_HEIGHT = screen_size
    overlay = pygame.Surface(screen_size, pygame.SRCALPHA)
    overlay.fill(config.UI_COLORS["OVERLAY"])
    screen.blit(overlay, (0, 0))

    center_x = SCREEN_WIDTH // 2
    center_y = SCREEN_HEIGHT // 2

    # 메뉴 패널 크기 (축소)
    menu_width = 450
    menu_height = 300
    menu_x = center_x - menu_width // 2
    menu_y = center_y - menu_height // 2

    # 패널 배경 - 통일된 색상 사용
    panel_bg = pygame.Surface((menu_width, menu_height), pygame.SRCALPHA)
    panel_bg.fill((*config.BG_LEVELS["PANEL"], 240))
    screen.blit(panel_bg, (menu_x, menu_y))

    # 현재 마우스 위치 (호버 효과용)
    mouse_pos = pygame.mouse.get_pos()

    if game_data["game_state"] == config.GAME_STATE_PAUSED:
        # ==================== 일시정지 메뉴 ====================
        # 타이틀 (크기 축소)
        title_text = render_text_with_emoji(
            f"{config.UI_ICONS['PAUSED']} PAUSED", font_medium, config.WHITE, "MEDIUM"
        )
        title_rect = title_text.get_rect(center=(center_x, menu_y + 50))
        screen.blit(title_text, title_rect)

        # 버튼 영역 시작
        button_start_y = menu_y + 110
        button_spacing = 55

        # 버튼 리스트 (ID, 텍스트, 색상)
        buttons = [
            ("resume", "Resume (P)", config.WHITE),
            ("workshop", "Workshop (W)", config.STATE_COLORS["WARNING"]),
            ("quit", "Quit (ESC)", config.UI_COLORS["DANGER"])
        ]

        button_font = get_font("medium")
        for i, (btn_id, text, color) in enumerate(buttons):
            btn_text = render_text_with_emoji(text, button_font, color, "SMALL")
            btn_rect = btn_text.get_rect(center=(center_x, button_start_y + i * button_spacing))

            # 버튼 배경 영역 계산
            btn_bg_width = btn_text.get_width() + 40
            btn_bg_height = btn_text.get_height() + 15
            btn_bg_rect = pygame.Rect(
                center_x - btn_bg_width // 2,
                btn_rect.centery - btn_bg_height // 2,
                btn_bg_width,
                btn_bg_height
            )

            # 버튼 Rect 저장 (클릭 감지용)
            button_rects[btn_id] = btn_bg_rect

            # 호버 효과
            is_hovered = btn_bg_rect.collidepoint(mouse_pos)
            if is_hovered:
                # 호버 시: 밝은 배경 + 테두리
                btn_bg = pygame.Surface((btn_bg_width, btn_bg_height), pygame.SRCALPHA)
                btn_bg.fill((*config.BG_LEVELS["ELEVATED"], 200))
                screen.blit(btn_bg, btn_bg_rect)
                pygame.draw.rect(screen, color, btn_bg_rect, 2, border_radius=6)
            else:
                # 일반: 기본 배경
                btn_bg = pygame.Surface((btn_bg_width, btn_bg_height), pygame.SRCALPHA)
                btn_bg.fill((*config.BG_LEVELS["CARD"], 160))
                screen.blit(btn_bg, btn_bg_rect)

            # 버튼 텍스트
            screen.blit(btn_text, btn_rect)

    else:  # GAME_STATE_OVER
        # ==================== 게임 오버 메뉴 ====================
        # 타이틀 (크기 축소)
        title_text = render_text_with_emoji(
            f"{config.UI_ICONS['GAME_OVER']} GAME OVER", font_medium, config.STATE_COLORS["DANGER"], "MEDIUM"
        )
        title_rect = title_text.get_rect(center=(center_x, menu_y + 50))
        screen.blit(title_text, title_rect)

        # 최종 점수 (강조)
        score_font = get_font("medium")
        score_text = render_text_with_emoji(
            f"{config.UI_ICONS['COIN']} FINAL COINS: {game_data['score']}",
            score_font,
            config.STATE_COLORS["GOLD"],
            "MEDIUM"
        )
        score_rect = score_text.get_rect(center=(center_x, menu_y + 130))

        # 점수 배경 - 통일된 색상
        score_bg = pygame.Surface((score_text.get_width() + 50, score_text.get_height() + 25), pygame.SRCALPHA)
        score_bg.fill((*config.BG_LEVELS["ELEVATED"], 180))
        score_bg_rect = score_bg.get_rect(center=score_rect.center)
        screen.blit(score_bg, score_bg_rect)
        screen.blit(score_text, score_rect)

        # 버튼 영역
        button_start_y = menu_y + 180
        button_spacing = 40

        # 버튼 리스트 (ID, 텍스트, 색상)
        buttons = [
            ("restart", "Restart (R)", config.TEXT_LEVELS["PRIMARY"]),
            ("return_base", "Return to Base (B)", config.STATE_COLORS["WARNING"]),
            ("quit", "Quit (ESC)", config.STATE_COLORS["DANGER"])
        ]

        button_font = get_font("medium")
        for i, (btn_id, text, color) in enumerate(buttons):
            btn_text = render_text_with_emoji(text, button_font, color, "SMALL")
            btn_rect = btn_text.get_rect(center=(center_x, button_start_y + i * button_spacing))

            # 버튼 배경 영역 계산
            btn_bg_width = btn_text.get_width() + 40
            btn_bg_height = btn_text.get_height() + 15
            btn_bg_rect = pygame.Rect(
                center_x - btn_bg_width // 2,
                btn_rect.centery - btn_bg_height // 2,
                btn_bg_width,
                btn_bg_height
            )

            # 버튼 Rect 저장 (클릭 감지용)
            button_rects[btn_id] = btn_bg_rect

            # 호버 효과
            is_hovered = btn_bg_rect.collidepoint(mouse_pos)
            if is_hovered:
                # 호버 시: 밝은 배경 + 테두리
                btn_bg = pygame.Surface((btn_bg_width, btn_bg_height), pygame.SRCALPHA)
                btn_bg.fill((*config.BG_LEVELS["ELEVATED"], 200))
                screen.blit(btn_bg, btn_bg_rect)
                pygame.draw.rect(screen, color, btn_bg_rect, 2, border_radius=6)
            else:
                # 일반: 기본 배경
                btn_bg = pygame.Surface((btn_bg_width, btn_bg_height), pygame.SRCALPHA)
                btn_bg.fill((*config.BG_LEVELS["CARD"], 160))
                screen.blit(btn_bg, btn_bg_rect)

            # 버튼 텍스트
            screen.blit(btn_text, btn_rect)

    return button_rects


def draw_settings_menu(screen: pygame.Surface, screen_size: Tuple[int, int],
                       font_huge: pygame.font.Font, font_title: pygame.font.Font,
                       font_medium: pygame.font.Font, sound_manager):
    """설정 메뉴 화면 그리기 (게임 스타일로 재구성, 마우스 드래그로 볼륨 조절)"""
    SCREEN_WIDTH, SCREEN_HEIGHT = screen_size
    center_x = SCREEN_WIDTH // 2
    center_y = SCREEN_HEIGHT // 2

    # 반투명 오버레이 - 통일된 색상
    overlay = pygame.Surface(screen_size, pygame.SRCALPHA)
    overlay.fill(config.UI_COLORS["OVERLAY"])
    screen.blit(overlay, (0, 0))

    # 메뉴 패널 크기
    panel_width = 700
    panel_height = 400
    panel_x = center_x - panel_width // 2
    panel_y = center_y - panel_height // 2

    # 패널 배경 - 통일된 색상
    panel_bg = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
    panel_bg.fill((*config.BG_LEVELS["PANEL"], 240))
    screen.blit(panel_bg, (panel_x, panel_y))

    # 타이틀 - 통일된 색상
    title_text = render_text_with_emoji(
        f"⚙️ SETTINGS ⚙️",
        font_title,
        config.STATE_COLORS["GOLD"],
        "LARGE"
    )
    title_rect = title_text.get_rect(center=(center_x, panel_y + 50))
    screen.blit(title_text, title_rect)

    # 볼륨 카드 시작 위치
    card_start_y = panel_y + 110
    card_spacing = 130
    card_width = 600
    card_height = 90

    # === BGM 볼륨 카드 ===
    bgm_card_y = card_start_y
    bgm_card_x = center_x - card_width // 2

    # 카드 배경 - 통일된 색상
    card_surface = pygame.Surface((card_width, card_height), pygame.SRCALPHA)
    card_surface.fill((*config.BG_LEVELS["CARD"], 220))
    screen.blit(card_surface, (bgm_card_x, bgm_card_y))

    # 아이콘 및 라벨 - 통일된 색상
    icon_text = render_text_with_emoji("🎵", font_title, config.STATE_COLORS["SUCCESS"], "LARGE")
    screen.blit(icon_text, (bgm_card_x + 20, bgm_card_y + 10))

    label_font = get_font("medium")
    label_text = label_font.render("Music (BGM)", True, config.TEXT_LEVELS["PRIMARY"])
    screen.blit(label_text, (bgm_card_x + 80, bgm_card_y + 15))

    # 볼륨 바
    bar_width = 400
    bar_height = 20
    bar_x = bgm_card_x + 80
    bar_y = bgm_card_y + 50

    # 배경 바 - 통일된 색상
    bg_rect_bgm = pygame.Rect(bar_x, bar_y, bar_width, bar_height)
    pygame.draw.rect(screen, config.BG_LEVELS["ELEVATED"], bg_rect_bgm, border_radius=10)

    # 볼륨 진행 바 - 통일된 색상
    bgm_volume = sound_manager.bgm_volume
    filled_width = int(bar_width * bgm_volume)
    if filled_width > 0:
        filled_rect = pygame.Rect(bar_x, bar_y, filled_width, bar_height)
        pygame.draw.rect(screen, config.STATE_COLORS["SUCCESS"], filled_rect, border_radius=10)

    # 테두리 - 통일된 색상
    pygame.draw.rect(screen, config.TEXT_LEVELS["PRIMARY"], bg_rect_bgm, 2, border_radius=10)

    # 슬라이더 핸들 (드래그 가능) - 통일된 색상
    handle_x = bar_x + filled_width - 8
    handle_y = bar_y - 5
    handle_rect = pygame.Rect(handle_x, handle_y, 16, 30)
    pygame.draw.rect(screen, config.STATE_COLORS["GOLD"], handle_rect, border_radius=5)
    pygame.draw.rect(screen, config.TEXT_LEVELS["PRIMARY"], handle_rect, 2, border_radius=5)

    # 볼륨 퍼센트 - 통일된 색상
    percent_text = font_medium.render(f"{int(bgm_volume * 100)}%", True, config.TEXT_LEVELS["PRIMARY"])
    screen.blit(percent_text, (bar_x + bar_width + 20, bar_y - 5))

    # === SFX 볼륨 카드 ===
    sfx_card_y = card_start_y + card_spacing
    sfx_card_x = center_x - card_width // 2

    # 카드 배경 - 통일된 색상
    card_surface_sfx = pygame.Surface((card_width, card_height), pygame.SRCALPHA)
    card_surface_sfx.fill((*config.BG_LEVELS["CARD"], 220))
    screen.blit(card_surface_sfx, (sfx_card_x, sfx_card_y))

    # 아이콘 및 라벨 - 통일된 색상
    icon_text_sfx = render_text_with_emoji("🔊", font_title, config.STATE_COLORS["INFO"], "LARGE")
    screen.blit(icon_text_sfx, (sfx_card_x + 20, sfx_card_y + 10))

    label_text_sfx = label_font.render("Sound Effects (SFX)", True, config.TEXT_LEVELS["PRIMARY"])
    screen.blit(label_text_sfx, (sfx_card_x + 80, sfx_card_y + 15))

    # 볼륨 바
    bar_x_sfx = sfx_card_x + 80
    bar_y_sfx = sfx_card_y + 50

    # 배경 바 - 통일된 색상
    bg_rect_sfx = pygame.Rect(bar_x_sfx, bar_y_sfx, bar_width, bar_height)
    pygame.draw.rect(screen, config.BG_LEVELS["ELEVATED"], bg_rect_sfx, border_radius=10)

    # 볼륨 진행 바 - 통일된 색상
    sfx_volume = sound_manager.sfx_volume
    filled_width_sfx = int(bar_width * sfx_volume)
    if filled_width_sfx > 0:
        filled_rect_sfx = pygame.Rect(bar_x_sfx, bar_y_sfx, filled_width_sfx, bar_height)
        pygame.draw.rect(screen, config.STATE_COLORS["INFO"], filled_rect_sfx, border_radius=10)

    # 테두리 - 통일된 색상
    pygame.draw.rect(screen, config.TEXT_LEVELS["PRIMARY"], bg_rect_sfx, 2, border_radius=10)

    # 슬라이더 핸들 - 통일된 색상
    handle_x_sfx = bar_x_sfx + filled_width_sfx - 8
    handle_y_sfx = bar_y_sfx - 5
    handle_rect_sfx = pygame.Rect(handle_x_sfx, handle_y_sfx, 16, 30)
    pygame.draw.rect(screen, config.STATE_COLORS["GOLD"], handle_rect_sfx, border_radius=5)
    pygame.draw.rect(screen, config.TEXT_LEVELS["PRIMARY"], handle_rect_sfx, 2, border_radius=5)

    # 볼륨 퍼센트 - 통일된 색상
    percent_text_sfx = font_medium.render(f"{int(sfx_volume * 100)}%", True, config.TEXT_LEVELS["PRIMARY"])
    screen.blit(percent_text_sfx, (bar_x_sfx + bar_width + 20, bar_y_sfx - 5))

    # 하단 안내 (깜빡임 효과) - 통일된 색상
    instruction_y = panel_y + panel_height - 40
    blink = int(time.time() * 2) % 2 == 0
    if blink:
        instruction_text = render_text_with_emoji(
            f"💡 Press F1 to Close Settings 💡",
            font_medium,
            config.STATE_COLORS["GOLD"],
            "MEDIUM"
        )
        screen.blit(instruction_text, instruction_text.get_rect(center=(center_x, instruction_y)))

    # 볼륨 바 영역 반환 (마우스 클릭 감지용)
    return {
        "bgm_bar": bg_rect_bgm,
        "sfx_bar": bg_rect_sfx
    }


def draw_death_effect_ui(screen: pygame.Surface, screen_size: Tuple[int, int],
                         death_effect_manager, font_small) -> Dict[str, pygame.Rect]:
    """화면 하단에 사망 효과 선택 UI 그리기

    Args:
        screen: 그릴 화면
        screen_size: 화면 크기
        death_effect_manager: DeathEffectManager 인스턴스
        font_small: 작은 폰트

    Returns:
        Dict[str, pygame.Rect]: 각 아이콘의 클릭 영역 딕셔너리
    """
    SCREEN_WIDTH, SCREEN_HEIGHT = screen_size

    # UI 패널 배경 (화면 하단) - 통일된 색상
    panel_height = config.DEATH_EFFECT_UI_HEIGHT
    panel_rect = pygame.Rect(0, SCREEN_HEIGHT - panel_height, SCREEN_WIDTH, panel_height)
    panel_surface = pygame.Surface((SCREEN_WIDTH, panel_height), pygame.SRCALPHA)
    panel_surface.fill((*config.BG_LEVELS["PANEL"], 200))  # 반투명 어두운 배경
    screen.blit(panel_surface, panel_rect)

    # 제목 텍스트 - 통일된 색상
    title_text = render_text_with_emoji(
        "Death Effects",
        font_small,
        config.TEXT_LEVELS["PRIMARY"],
        "TINY"
    )
    title_x = 20
    title_y = SCREEN_HEIGHT - panel_height + 40
    screen.blit(title_text, (title_x, title_y))

    # 아이콘 그리기
    icon_rects = {}
    icon_size = config.DEATH_EFFECT_ICON_SIZE
    icon_spacing = config.DEATH_EFFECT_ICON_SPACING
    start_x = 20
    start_y = SCREEN_HEIGHT - panel_height + 5

    effect_names = ["shatter", "particle_burst", "dissolve", "fade", "implode"]
    effect_labels = {
        "shatter": "💔",
        "particle_burst": "✨",
        "dissolve": "🌫️",
        "fade": "💨",
        "implode": "🌀"
    }

    for i, effect_name in enumerate(effect_names):
        x = start_x + i * icon_spacing
        y = start_y

        # 아이콘 영역 (사각형)
        icon_rect = pygame.Rect(x, y, icon_size, icon_size)
        icon_rects[effect_name] = icon_rect

        # 현재 선택된 효과인지 확인
        is_selected = (death_effect_manager.current_effect == effect_name)
        is_enabled = death_effect_manager.enabled_effects.get(effect_name, False)

        # 배경 색상 - 통일된 색상
        if is_selected:
            bg_color = (*config.STATE_COLORS["INFO"], 255)  # 밝은 파란색 (선택됨)
            border_width = 3
        elif is_enabled:
            bg_color = (*config.BG_LEVELS["ELEVATED"], 200)  # 회색 (활성화됨)
            border_width = 2
        else:
            bg_color = (*config.BG_LEVELS["CARD"], 150)  # 어두운 회색 (비활성화)
            border_width = 1

        # 아이콘 배경
        pygame.draw.rect(screen, bg_color, icon_rect)
        pygame.draw.rect(screen, config.TEXT_LEVELS["SECONDARY"], icon_rect, border_width)

        # 이모지 또는 텍스트 (PNG가 없을 경우 대체) - 통일된 색상
        emoji = effect_labels[effect_name]
        emoji_surface = render_text_with_emoji(emoji, font_small,
                                               config.TEXT_LEVELS["PRIMARY"], "SMALL")
        emoji_rect = emoji_surface.get_rect(center=icon_rect.center)
        screen.blit(emoji_surface, emoji_rect)

    return icon_rects
