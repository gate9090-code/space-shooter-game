# ui_render/shop.py
# Shop and upgrade UI rendering functions

import pygame
import time
from typing import Tuple, Dict
import config
from .helpers import get_font, render_text_with_emoji


# =========================================================
# 1. 화면 그리기 함수
# =========================================================


def draw_shop_screen(
    screen: pygame.Surface,
    screen_size: Tuple[int, int],
    font_title: pygame.font.Font,
    font_medium: pygame.font.Font,
    current_score: int,
    player_upgrades: dict,
):
    """상점 화면을 그립니다. (영구 업그레이드) - 개선된 카드 스타일"""
    SCREEN_WIDTH, SCREEN_HEIGHT = screen_size
    overlay = pygame.Surface(screen_size, pygame.SRCALPHA)
    overlay.fill(config.UI_COLORS["OVERLAY"])
    screen.blit(overlay, (0, 0))

    center_x = SCREEN_WIDTH // 2

    # 전체 콘텐츠 높이 계산 후 중앙 배치
    card_spacing = 85
    card_height = 70
    header_height = 80
    footer_height = 40
    num_items = 4  # COOLDOWN, MAX_HP, SPEED, REINCARNATION

    total_content_height = header_height + (num_items * card_spacing) + footer_height
    y_start = (SCREEN_HEIGHT - total_content_height) // 2

    # 제목 (크기 축소, 통일감)
    title_text = render_text_with_emoji(
        f"{config.UI_ICONS['SHOP']} PERMANENT UPGRADE SHOP",
        font_medium,
        config.UI_COLORS["PRIMARY"],
        "MEDIUM"
    )
    screen.blit(title_text, title_text.get_rect(center=(center_x, y_start + 20)))

    # 코인 표시 (크기 축소)
    coin_font = get_font("small")
    coin_text = render_text_with_emoji(
        f"{config.UI_ICONS['COIN']} Your Coins: {current_score}",
        coin_font,
        config.UI_COLORS["COIN_GOLD"],
        "SMALL"
    )
    screen.blit(coin_text, coin_text.get_rect(center=(center_x, y_start + 55)))

    # 업그레이드 옵션 그리기
    upgrade_items = config.UPGRADE_KEYS

    # 비용 계산 함수
    def get_upgrade_cost(level):
        return config.PERMANENT_UPGRADE_COST_BASE * (level + 1)

    # 아이콘 매핑 (config에서 가져오기)
    upgrade_icons = {
        "COOLDOWN": config.UI_ICONS["FIRE_RATE"],
        "MAX_HP": config.UI_ICONS["HP"],
        "SPEED": config.UI_ICONS["SPEED"],
        "REINCARNATION": config.UI_ICONS["REINCARNATION"]
    }

    cards_start_y = y_start + header_height + 10

    for i, (key, name) in enumerate(upgrade_items.items()):
        current_level = player_upgrades.get(key, 0)

        # 환생은 특별 처리: 고정 비용 500, 최대 3개
        if key == "REINCARNATION":
            cost = config.REINCARNATION_COST
            max_level = config.REINCARNATION_MAX
        else:
            cost = get_upgrade_cost(current_level)
            max_level = 10

        can_afford = current_score >= cost and current_level < max_level

        # 카드 위치 계산
        card_y = cards_start_y + i * card_spacing
        card_width = 650
        card_x = center_x - card_width // 2

        # 카드 배경
        card_bg_color = config.UI_COLORS["CARD_BG"] if can_afford else (40, 30, 30, 230)
        card_surface = pygame.Surface((card_width, card_height), pygame.SRCALPHA)
        card_surface.fill(card_bg_color)
        screen.blit(card_surface, (card_x, card_y))

        # 왼쪽: 번호 박스
        number_box_size = 55
        number_box_x = card_x + 10
        number_box_y = card_y + (card_height - number_box_size) // 2

        pygame.draw.rect(
            screen,
            config.UI_COLORS["PRIMARY"] if can_afford else (100, 100, 100),
            (number_box_x, number_box_y, number_box_size, number_box_size)
        )

        # 번호 텍스트
        number_font = get_font("large")
        number_text = number_font.render(str(i + 1), True, config.BLACK)
        number_rect = number_text.get_rect(
            center=(number_box_x + number_box_size // 2, number_box_y + number_box_size // 2)
        )
        screen.blit(number_text, number_rect)

        # 중앙: 업그레이드 정보 (크기 조정)
        info_x = card_x + number_box_size + 20
        icon = upgrade_icons.get(key, config.UI_ICONS["LEVEL_UP"])

        name_font = get_font("medium")
        name_text = render_text_with_emoji(f"{icon} {name}", name_font, config.WHITE, "SMALL")
        screen.blit(name_text, (info_x, card_y + 8))

        # 레벨 바 (별 모양)
        stars = "★" * current_level + "☆" * (max_level - current_level)
        level_font = get_font("small")
        level_text = render_text_with_emoji(
            f"{stars} LV {current_level}/{max_level}",
            level_font,
            config.UI_COLORS["PRIMARY"] if current_level > 0 else config.UI_COLORS["TEXT_SECONDARY"],
            "SMALL"
        )
        screen.blit(level_text, (info_x, card_y + 38))

        # 우측: 비용
        if current_level >= max_level:
            cost_text_content = "MAX"
            cost_color = config.UI_COLORS["PRIMARY"]
        elif can_afford:
            cost_text_content = f"Cost: {cost}"
            cost_color = config.UI_COLORS["COIN_GOLD"]
        else:
            cost_text_content = f"Need: {cost - current_score} more"
            cost_color = config.UI_COLORS["DANGER"]

        cost_font = get_font("small")
        cost_text = cost_font.render(cost_text_content, True, cost_color)
        cost_rect = cost_text.get_rect(
            midright=(card_x + card_width - 15, card_y + card_height // 2)
        )
        screen.blit(cost_text, cost_rect)

    # 하단 안내
    instruction_y = cards_start_y + len(upgrade_items) * card_spacing + 20
    exit_font = get_font("small")
    # render_text_with_emoji 대신 일반 렌더링 사용 (글자 깨짐 방지)
    exit_text = exit_font.render("Press 'C' to Close Shop | Press 'ESC' to Quit Game", True, config.UI_COLORS["TEXT_SECONDARY"])
    screen.blit(exit_text, exit_text.get_rect(center=(center_x, instruction_y)))


def draw_tactical_menu(
    screen: pygame.Surface,
    screen_size: Tuple[int, int],
    font_title: pygame.font.Font,
    font_medium: pygame.font.Font,
    game_data: dict,
):
    """
    전술 레벨업 메뉴를 그립니다. (개선된 카드 스타일 - 가독성 향상)
    통일된 색상 시스템 사용
    """
    SCREEN_WIDTH, SCREEN_HEIGHT = screen_size
    overlay = pygame.Surface(screen_size, pygame.SRCALPHA)
    overlay.fill(config.UI_COLORS["OVERLAY"])
    screen.blit(overlay, (0, 0))

    center_x = SCREEN_WIDTH // 2

    # game_data에서 필요한 정보 추출
    current_level = game_data.get("player_level", 1)
    current_wave = game_data.get("current_wave", 1)
    options = game_data.get("tactical_options", [])

    # 전체 콘텐츠 높이 계산 후 중앙 배치
    card_spacing = 90  # 110 → 90 (간격 축소)
    card_height = 80   # 95 → 80 (카드 높이 축소)
    header_height = 80 # 120 → 80 (헤더 높이 축소)
    footer_height = 40

    total_content_height = header_height + (len(options) * card_spacing) + footer_height
    y_start = (SCREEN_HEIGHT - total_content_height) // 2

    # 헤더 시작 위치
    header_y = y_start

    # 제목 - 크기 축소
    level_text = render_text_with_emoji(
        f"{config.UI_ICONS['LEVEL_UP']} LEVEL UP! {config.UI_ICONS['LEVEL_UP']}",
        font_medium,
        config.UI_COLORS["PRIMARY"],
        "MEDIUM"
    )
    screen.blit(level_text, level_text.get_rect(center=(center_x, header_y + 20)))

    # 서브타이틀 (레벨 + 웨이브 정보) - 크기 축소
    subtitle_font = get_font("small")  # 작은 폰트
    subtitle_text = render_text_with_emoji(
        f"Level {current_level} | Wave {current_wave}",
        subtitle_font,
        config.TEXT_LEVELS["PRIMARY"],
        "SMALL"
    )
    screen.blit(subtitle_text, subtitle_text.get_rect(center=(center_x, header_y + 55)))

    # 옵션 카드 그리기
    cards_start_y = header_y + header_height + 10
    card_rects = []  # 클릭 영역 저장

    # 마우스 위치 (호버 효과용)
    mouse_pos = pygame.mouse.get_pos()

    for i, option in enumerate(options):
        key_number = i + 1
        option_name = option["name"]
        effect_str = option["effect_str"]
        description = option.get("description", "")

        # 카드 위치 계산
        card_y = cards_start_y + i * card_spacing
        card_width = 700  # 800 → 700 (너비 축소)
        card_x = center_x - card_width // 2

        # 카드 rect 저장 (클릭 감지용)
        card_rect = pygame.Rect(card_x, card_y, card_width, card_height)
        card_rects.append(card_rect)

        # 호버 효과 체크
        is_hovered = card_rect.collidepoint(mouse_pos)

        # 카드 배경 (반투명) - 통일된 색상 + 호버 효과
        card_surface = pygame.Surface((card_width, card_height), pygame.SRCALPHA)
        if is_hovered:
            card_surface.fill((*config.BG_LEVELS["CARD"], 255))  # 호버시 더 밝게
        else:
            card_surface.fill((*config.BG_LEVELS["CARD"], 220))
        screen.blit(card_surface, (card_x, card_y))

        # 호버시 테두리 추가
        if is_hovered:
            pygame.draw.rect(screen, config.STATE_COLORS["GOLD"], card_rect, 3)

        # 왼쪽 번호 박스 (크기 유지)
        number_box_size = 65
        number_box_x = card_x + 15
        number_box_y = card_y + (card_height - number_box_size) // 2

        # 번호 박스 배경 (테두리 없음) - 통일된 색상
        pygame.draw.rect(
            screen,
            config.STATE_COLORS["GOLD"],
            (number_box_x, number_box_y, number_box_size, number_box_size)
        )

        # 번호 텍스트 (크기 유지)
        number_text = font_title.render(str(key_number), True, config.BLACK)
        number_rect = number_text.get_rect(
            center=(number_box_x + number_box_size // 2, number_box_y + number_box_size // 2)
        )
        screen.blit(number_text, number_rect)

        # 옵션 이름 (크기 축소) - 통일된 색상
        name_x = card_x + number_box_size + 25
        name_text = render_text_with_emoji(
            option_name,
            font_medium,  # font_title → font_medium (축소)
            config.STATE_COLORS["SUCCESS"],
            "MEDIUM"
        )
        screen.blit(name_text, (name_x, card_y + 8))

        # 효과 설명 (크기 축소) - 통일된 색상
        effect_font = get_font("small")  # 효과 설명
        effect_text = effect_font.render(effect_str, True, config.STATE_COLORS["GOLD"])
        screen.blit(effect_text, (name_x, card_y + 35))

        # 설명 텍스트 (크기 축소) - 통일된 색상
        if description:
            desc_font = get_font("light_tiny")  # 설명 텍스트 (Light)
            desc_text = desc_font.render(description, True, config.TEXT_LEVELS["SECONDARY"])
            screen.blit(desc_text, (name_x, card_y + 58))

    # 하단 안내 문구 (크기 축소, 깜빡임 효과)
    instruction_y = cards_start_y + len(options) * card_spacing + 20

    # 깜빡임 효과
    blink = int(time.time() * 2) == 0
    if blink:
        instruction_text = render_text_with_emoji(
            f"{config.UI_ICONS['INFO']} Click or Press (1-4) to Choose {config.UI_ICONS['INFO']}",
            font_medium,  # font_title → font_medium (축소)
            config.UI_COLORS["PRIMARY"],
            "MEDIUM"
        )
        screen.blit(instruction_text, instruction_text.get_rect(center=(center_x, instruction_y)))

    # 클릭 영역을 game_data에 저장
    game_data["level_up_card_rects"] = card_rects
