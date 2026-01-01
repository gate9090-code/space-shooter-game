# ui_render/wave_ui.py
# Wave-specific UI rendering functions (wave prepare, clear, victory, boss clear choice)

import pygame
import math
from typing import Tuple, Dict
import config
from .helpers import get_font, render_text_with_emoji


# =========================================================
# 3. 웨이브 시스템 UI
# =========================================================


def draw_wave_prepare_screen(
    screen: pygame.Surface,
    screen_size: Tuple[int, int],
    font_title: pygame.font.Font,
    font_medium: pygame.font.Font,
    game_data: dict,
):
    """웨이브 시작 전 준비 화면 (마우스 클릭으로 시작)"""
    SCREEN_WIDTH, SCREEN_HEIGHT = screen_size
    center_x = SCREEN_WIDTH // 2
    center_y = SCREEN_HEIGHT // 2

    # 반투명 배경 - 통일된 색상
    overlay = pygame.Surface(screen_size, pygame.SRCALPHA)
    overlay.fill(config.UI_COLORS["OVERLAY"])
    screen.blit(overlay, (0, 0))

    # 메인 패널 (크기 축소)
    panel_width = 500
    panel_height = 320
    panel_x = center_x - panel_width // 2
    panel_y = center_y - panel_height // 2

    # 패널 배경 - 통일된 색상
    panel_bg = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
    panel_bg.fill((*config.BG_LEVELS["PANEL"], 240))
    screen.blit(panel_bg, (panel_x, panel_y))

    current_wave = game_data.get("current_wave", 1)
    wave_desc = config.WAVE_DESCRIPTIONS.get(current_wave, f"Wave {current_wave}")

    # 웨이브 번호 (크기 축소) - 통일된 색상
    wave_num_text = render_text_with_emoji(
        f"WAVE {current_wave}/{config.TOTAL_WAVES}",
        font_medium,
        config.STATE_COLORS["GOLD"],
        "MEDIUM"
    )
    screen.blit(wave_num_text, wave_num_text.get_rect(center=(center_x, panel_y + 60)))

    # 웨이브 설명 (크기 축소) - 통일된 색상
    desc_font = get_font("light_small")
    desc_text = render_text_with_emoji(
        wave_desc,
        desc_font,
        config.TEXT_LEVELS["PRIMARY"],
        "SMALL"
    )
    screen.blit(desc_text, desc_text.get_rect(center=(center_x, panel_y + 140)))

    # 목표 킬 수 (크기 축소) - 통일된 색상
    target_kills = game_data.get("wave_target_kills", 20)
    target_font = get_font("small")
    target_text = render_text_with_emoji(
        f"{config.UI_ICONS['SWORD']} Target: {target_kills} Kills",
        target_font,
        config.TEXT_LEVELS["SECONDARY"],
        "SMALL"
    )
    screen.blit(target_text, target_text.get_rect(center=(center_x, panel_y + 190)))

    # 시작 안내 (깜빡이는 효과, 크기 축소) - 통일된 색상
    alpha = int(127 + 128 * math.sin(pygame.time.get_ticks() / 500))
    start_font = get_font("medium")
    start_text = render_text_with_emoji(
        "Click to Start!",
        start_font,
        config.STATE_COLORS["GOLD"],
        "SMALL"
    )
    start_text.set_alpha(alpha)
    screen.blit(start_text, start_text.get_rect(center=(center_x, panel_y + 260)))


def draw_wave_clear_screen(
    screen: pygame.Surface,
    screen_size: Tuple[int, int],
    font_title: pygame.font.Font,
    font_medium: pygame.font.Font,
    game_data: dict,
):
    """웨이브 클리어 화면"""
    SCREEN_WIDTH, SCREEN_HEIGHT = screen_size
    center_x = SCREEN_WIDTH // 2
    center_y = SCREEN_HEIGHT // 2

    # 반투명 배경 - 통일된 색상
    overlay = pygame.Surface(screen_size, pygame.SRCALPHA)
    overlay.fill(config.UI_COLORS["OVERLAY"])
    screen.blit(overlay, (0, 0))

    # 메인 패널 (크기 축소)
    panel_width = 450
    panel_height = 300
    panel_x = center_x - panel_width // 2
    panel_y = center_y - panel_height // 2

    # 패널 배경 - 통일된 색상 (성공 컬러 틴트)
    panel_bg = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
    panel_bg.fill((*config.STATE_COLORS["SUCCESS_DIM"], 240))
    screen.blit(panel_bg, (panel_x, panel_y))

    current_wave = game_data.get("current_wave", 1)

    # 클리어 텍스트 (크기 축소) - 통일된 색상
    clear_text = render_text_with_emoji(
        f"{config.UI_ICONS['LEVEL_UP']} WAVE {current_wave} CLEAR!",
        font_medium,
        config.STATE_COLORS["SUCCESS"],
        "MEDIUM"
    )
    screen.blit(clear_text, clear_text.get_rect(center=(center_x, panel_y + 60)))

    # 통계 (크기 축소) - 통일된 색상
    kills = game_data.get("wave_kills", 0)
    total_kills = game_data.get("kill_count", 0)

    stats_y = panel_y + 140
    stats_font = get_font("small")
    kills_text = render_text_with_emoji(
        f"{config.UI_ICONS['SWORD']} Kills This Wave: {kills}",
        stats_font,
        config.TEXT_LEVELS["PRIMARY"],
        "SMALL"
    )
    screen.blit(kills_text, kills_text.get_rect(center=(center_x, stats_y)))

    total_font = get_font("small")
    total_text = render_text_with_emoji(
        f"Total Kills: {total_kills}",
        total_font,
        config.TEXT_LEVELS["SECONDARY"],
        "SMALL"
    )
    screen.blit(total_text, total_text.get_rect(center=(center_x, stats_y + 35)))

    # 크레딧 보상 표시 (Option B: 정비소 통합) - 통일된 색상
    credit_reward = game_data.get("last_wave_credits", 0)
    if credit_reward > 0:
        credit_font = get_font("medium")
        credit_text = render_text_with_emoji(
            f"{config.UI_ICONS['COIN']} +{credit_reward} Credits!",
            credit_font,
            config.STATE_COLORS["GOLD"],
            "MEDIUM"
        )
        screen.blit(credit_text, credit_text.get_rect(center=(center_x, stats_y + 70)))

    # 다음 웨이브 안내 (깜빡임, 크기 축소) - 통일된 색상
    alpha = int(127 + 128 * math.sin(pygame.time.get_ticks() / 500))

    next_font = get_font("medium")
    if current_wave < config.TOTAL_WAVES:
        next_text = render_text_with_emoji(
            "Click for Next Wave!",
            next_font,
            config.STATE_COLORS["GOLD"],
            "SMALL"
        )
    else:
        next_text = render_text_with_emoji(
            "ALL WAVES CLEARED! VICTORY!",
            next_font,
            config.STATE_COLORS["GOLD"],
            "SMALL"
        )

    next_text.set_alpha(alpha)
    screen.blit(next_text, next_text.get_rect(center=(center_x, panel_y + 235)))


# =========================================================
# 8. 승리 화면 (Victory Screen)
# =========================================================

def draw_victory_screen(
    screen: pygame.Surface,
    game_data: Dict,
    player,
    fonts: Dict[str, pygame.font.Font]
):
    """게임 승리 화면 그리기 (모든 웨이브 클리어)"""
    SCREEN_WIDTH, SCREEN_HEIGHT = screen.get_size()
    center_x = SCREEN_WIDTH // 2
    center_y = SCREEN_HEIGHT // 2

    # 반투명 오버레이 - 통일된 색상
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill(config.UI_COLORS["OVERLAY"])
    screen.blit(overlay, (0, 0))

    # 메인 패널 (다른 화면과 통일감 있는 크기)
    panel_width = 550
    panel_height = 420
    panel_x = center_x - panel_width // 2
    panel_y = center_y - panel_height // 2

    # 패널 배경 - 통일된 색상 (성공 컬러 틴트)
    panel_bg = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
    panel_bg.fill((*config.STATE_COLORS["SUCCESS_DIM"], 240))
    pygame.draw.rect(panel_bg, config.STATE_COLORS["SUCCESS"], (0, 0, panel_width, panel_height), 3)
    screen.blit(panel_bg, (panel_x, panel_y))

    # VICTORY 타이틀 (크기 축소) - 통일된 색상
    victory_text = render_text_with_emoji(
        "🏆 VICTORY! 🏆",
        fonts["medium"],
        config.STATE_COLORS["SUCCESS"],
        "MEDIUM"
    )
    victory_rect = victory_text.get_rect(center=(center_x, panel_y + 50))
    screen.blit(victory_text, victory_rect)

    # 부제목 (크기 축소) - 통일된 색상
    subtitle_font = get_font("medium")
    subtitle_text = render_text_with_emoji(
        "ALL WAVES CLEARED!",
        subtitle_font,
        config.TEXT_LEVELS["PRIMARY"],
        "SMALL"
    )
    subtitle_rect = subtitle_text.get_rect(center=(center_x, panel_y + 85))
    screen.blit(subtitle_text, subtitle_rect)

    # 구분선 - 통일된 색상
    line_y = panel_y + 110
    pygame.draw.line(
        screen,
        config.STATE_COLORS["SUCCESS"],
        (panel_x + 40, line_y),
        (panel_x + panel_width - 40, line_y),
        2
    )

    # 최종 스탯 표시 (크기 축소)
    stat_start_y = line_y + 30
    stat_spacing = 40

    stats = [
        ("💰 Total Score", f"{game_data['score']:,}"),
        ("⚔️ Total Kills", f"{game_data['kill_count']:,}"),
        ("✨ Player Level", f"{game_data['player_level']}"),
        (f"{config.UI_ICONS['HP']} Final HP", f"{int(player.hp)} / {int(player.max_hp)}"),
        ("🏆 Waves Cleared", f"{config.TOTAL_WAVES} / {config.TOTAL_WAVES}"),
    ]

    # 스탯용 폰트 (크기 축소)
    stat_font = get_font("small")

    for i, (label, value) in enumerate(stats):
        y_pos = stat_start_y + i * stat_spacing

        # 레이블 - 통일된 색상
        label_surf = render_text_with_emoji(
            label,
            stat_font,
            config.TEXT_LEVELS["SECONDARY"],
            "SMALL"
        )
        label_rect = label_surf.get_rect(midleft=(panel_x + 50, y_pos))
        screen.blit(label_surf, label_rect)

        # 값 - 통일된 색상
        value_text = stat_font.render(
            value,
            True,
            config.TEXT_LEVELS["PRIMARY"]
        )
        value_rect = value_text.get_rect(midright=(panel_x + panel_width - 50, y_pos))
        screen.blit(value_text, value_rect)

    # Base Hub 귀환 버튼 (강조) - 통일된 색상
    base_button_y = panel_y + panel_height - 130
    base_button_width = 200
    base_button_height = 40
    base_button_x = center_x - base_button_width // 2

    # 버튼 배경 (초록색 강조)
    base_btn_surface = pygame.Surface((base_button_width, base_button_height), pygame.SRCALPHA)
    base_btn_surface.fill((*config.STATE_COLORS["SUCCESS_DIM"], 200))
    screen.blit(base_btn_surface, (base_button_x, base_button_y))
    pygame.draw.rect(screen, config.STATE_COLORS["SUCCESS"],
                    (base_button_x, base_button_y, base_button_width, base_button_height), 3, border_radius=8)

    base_btn_font = get_font("medium")
    base_btn_text = base_btn_font.render("[H] Return to Base", True, config.TEXT_LEVELS["PRIMARY"])
    base_btn_rect = base_btn_text.get_rect(center=(center_x, base_button_y + base_button_height // 2))
    screen.blit(base_btn_text, base_btn_rect)

    # 보스 러시 제안 섹션 - 통일된 색상
    boss_rush_y = panel_y + panel_height - 75

    # 제안 텍스트
    proposal_font = get_font("light_small")
    proposal_text = render_text_with_emoji(
        "Or challenge Boss Rush Mode?",
        proposal_font,
        config.STATE_COLORS["WARNING"],
        "SMALL"
    )
    proposal_rect = proposal_text.get_rect(center=(center_x, boss_rush_y))
    screen.blit(proposal_text, proposal_rect)

    # 하단 안내 메시지 - 통일된 색상
    instruction_y = panel_y + panel_height - 45

    instruction_font = get_font("tiny")
    instruction_text = render_text_with_emoji(
        "B: Boss Rush | R: Restart | Q: Quit",
        instruction_font,
        config.TEXT_LEVELS["SECONDARY"],
        "SMALL"
    )
    instruction_rect = instruction_text.get_rect(center=(center_x, instruction_y))
    screen.blit(instruction_text, instruction_rect)

    # 감사 메시지 (패널 외부 하단) - 통일된 색상
    thanks_font = get_font("light_tiny")
    thanks_text = render_text_with_emoji(
        "Thank you for playing!",
        thanks_font,
        config.TEXT_LEVELS["SECONDARY"],
        "SMALL"
    )
    thanks_rect = thanks_text.get_rect(center=(center_x, SCREEN_HEIGHT - 30))
    screen.blit(thanks_text, thanks_rect)


def draw_boss_clear_choice(
    screen: pygame.Surface,
    game_data: Dict,
    fonts: Dict[str, pygame.font.Font]
) -> Dict[str, pygame.Rect]:
    """보스 클리어 후 선택 화면 (우상단에 선택 박스 표시)"""
    SCREEN_WIDTH, SCREEN_HEIGHT = screen.get_size()

    # 우상단 위치 설정
    choice_width = 320
    choice_height = 160
    choice_x = SCREEN_WIDTH - choice_width - 30
    choice_y = 30

    # 반투명 배경
    choice_bg = pygame.Surface((choice_width, choice_height), pygame.SRCALPHA)
    choice_bg.fill((*config.STATE_COLORS["SUCCESS_DIM"], 220))
    pygame.draw.rect(choice_bg, config.STATE_COLORS["SUCCESS"],
                    (0, 0, choice_width, choice_height), 3, border_radius=8)
    screen.blit(choice_bg, (choice_x, choice_y))

    # 타이틀
    title_font = get_font("medium")
    title_text = render_text_with_emoji(
        "🏆 Boss Cleared!",
        title_font,
        config.STATE_COLORS["SUCCESS"],
        "MEDIUM"
    )
    title_rect = title_text.get_rect(center=(choice_x + choice_width // 2, choice_y + 30))
    screen.blit(title_text, title_rect)

    # 버튼 설정
    button_width = 260
    button_height = 35
    button_x = choice_x + (choice_width - button_width) // 2

    # "Continue Wave" 버튼
    continue_y = choice_y + 65
    continue_rect = pygame.Rect(button_x, continue_y, button_width, button_height)

    mouse_pos = pygame.mouse.get_pos()
    is_continue_hover = continue_rect.collidepoint(mouse_pos)

    continue_color = config.STATE_COLORS["SUCCESS"] if is_continue_hover else (*config.STATE_COLORS["SUCCESS_DIM"], 180)
    continue_surface = pygame.Surface((button_width, button_height), pygame.SRCALPHA)
    continue_surface.fill(continue_color)
    screen.blit(continue_surface, (button_x, continue_y))
    pygame.draw.rect(screen, config.STATE_COLORS["SUCCESS"],
                    (button_x, continue_y, button_width, button_height), 2, border_radius=6)

    continue_font = get_font("small")
    continue_text = continue_font.render("[C] Continue Wave", True, config.TEXT_LEVELS["PRIMARY"])
    continue_text_rect = continue_text.get_rect(center=(button_x + button_width // 2, continue_y + button_height // 2))
    screen.blit(continue_text, continue_text_rect)

    # "Return to Base" 버튼
    return_y = choice_y + 110
    return_rect = pygame.Rect(button_x, return_y, button_width, button_height)

    is_return_hover = return_rect.collidepoint(mouse_pos)

    return_color = config.STATE_COLORS["WARNING"] if is_return_hover else (*config.STATE_COLORS["WARNING_DIM"], 180)
    return_surface = pygame.Surface((button_width, button_height), pygame.SRCALPHA)
    return_surface.fill(return_color)
    screen.blit(return_surface, (button_x, return_y))
    pygame.draw.rect(screen, config.STATE_COLORS["WARNING"],
                    (button_x, return_y, button_width, button_height), 2, border_radius=6)

    return_font = get_font("small")
    return_text = return_font.render("[B] Return to Base", True, config.TEXT_LEVELS["PRIMARY"])
    return_text_rect = return_text.get_rect(center=(button_x + button_width // 2, return_y + button_height // 2))
    screen.blit(return_text, return_text_rect)

    # 버튼 영역 반환
    return {
        "continue": continue_rect,
        "return_base": return_rect
    }
