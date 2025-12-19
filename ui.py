# ui.py

import pygame
import math
from typing import Tuple, List, Dict, TYPE_CHECKING, Optional
import config
from utils import get_next_level_threshold

if TYPE_CHECKING:
    from objects import Player

# =========================================================
# 0. 이모지 렌더링 헬퍼 함수
# =========================================================

def render_text_with_emoji(
    text: str,
    font: pygame.font.Font,
    color: Tuple[int, int, int],
    emoji_font_size: str = "MEDIUM"
) -> pygame.Surface:
    """
    이모지와 일반 텍스트를 분리해서 렌더링하고 합칩니다.
    emoji_font_size: "SMALL", "MEDIUM", "LARGE", "HUGE" 중 하나
    """
    # config에서 이모지 폰트 가져오기
    emoji_font = config.EMOJI_FONTS.get(emoji_font_size, None)

    if emoji_font is None or not config.EMOJI_FONTS:
        # 이모지 폰트가 없으면 일반 폰트로만 렌더링
        return font.render(text, True, color)

    # config.UI_ICONS의 모든 이모지를 집합으로 만들기
    emoji_chars = set(config.UI_ICONS.values())
    # 별 문자도 추가 (★ ☆)
    emoji_chars.add("★")
    emoji_chars.add("☆")

    # 이모지와 일반 텍스트를 분리
    parts = []
    current_text = ""
    current_emoji = ""

    i = 0
    while i < len(text):
        char = text[i]
        char_code = ord(char)

        # 이모지인지 확인: config.UI_ICONS에 있거나, 넓은 유니코드 범위
        is_emoji = (
            char in emoji_chars or  # config에 정의된 이모지
            char_code > 0x1F000 or  # 이모지 유니코드 범위
            (0x2000 <= char_code <= 0x2BFF) or  # Miscellaneous Symbols
            char_code == 0xFE0F  # Variation Selector (이모지 변형)
        )

        if is_emoji:
            # 일반 텍스트가 있으면 저장
            if current_text:
                parts.append(("text", current_text))
                current_text = ""

            # 이모지 수집 (variation selector 포함 가능)
            current_emoji = char
            # 다음 문자가 variation selector면 포함
            if i + 1 < len(text) and ord(text[i + 1]) == 0xFE0F:
                current_emoji += text[i + 1]
                i += 1  # variation selector 건너뛰기

            parts.append(("emoji", current_emoji))
            current_emoji = ""
        else:
            current_text += char

        i += 1

    if current_text:
        parts.append(("text", current_text))

    # 각 부분을 렌더링
    surfaces = []
    for part_type, content in parts:
        if part_type == "emoji":
            surf = emoji_font.render(content, True, color)
        else:
            surf = font.render(content, True, color)
        surfaces.append(surf)

    # 하나의 Surface로 합치기
    if not surfaces:
        return font.render("", True, color)

    total_width = sum(s.get_width() for s in surfaces)
    max_height = max(s.get_height() for s in surfaces)

    combined = pygame.Surface((total_width, max_height), pygame.SRCALPHA)
    combined.fill((0, 0, 0, 0))  # 투명 배경

    x = 0
    for surf in surfaces:
        # 세로 중앙 정렬
        y = (max_height - surf.get_height()) // 2
        combined.blit(surf, (x, y))
        x += surf.get_width()

    return combined


# =========================================================
# HPBarShake 클래스 (피격 시 HP바 흔들림 효과)
# =========================================================

class HPBarShake:
    """
    데미지를 받았을 때 HP바가 흔들리는 효과를 관리하는 클래스.
    데미지 비율에 따라 흔들림 강도가 조절됩니다.
    """
    def __init__(self):
        self.is_active = False
        self.start_time = 0.0
        self.duration = 0.3  # 0.3초 지속
        self.intensity = 0  # 흔들림 강도 (픽셀)
        self.offset_x = 0
        self.offset_y = 0

    def trigger(self, damage_ratio: float):
        """
        흔들림 효과를 트리거합니다.

        Args:
            damage_ratio: 받은 데미지 / 최대 HP 비율 (0.0 ~ 1.0)
        """
        self.is_active = True
        self.start_time = pygame.time.get_ticks() / 1000.0
        # 데미지 비율에 따른 흔들림 강도 (3 ~ 10 픽셀)
        self.intensity = int(3 + damage_ratio * 7)

    def update(self) -> Tuple[int, int]:
        """
        흔들림 효과를 업데이트하고 오프셋을 반환합니다.

        Returns:
            Tuple[int, int]: (offset_x, offset_y) 흔들림 오프셋
        """
        if not self.is_active:
            return (0, 0)

        current_time = pygame.time.get_ticks() / 1000.0
        elapsed = current_time - self.start_time

        if elapsed >= self.duration:
            self.is_active = False
            self.offset_x = 0
            self.offset_y = 0
            return (0, 0)

        # 점점 감소하는 진폭
        progress = elapsed / self.duration
        decay = 1.0 - progress
        current_intensity = int(self.intensity * decay)

        # 빠른 주기로 흔들림 (사인파 기반)
        shake_speed = 50  # 흔들림 속도
        self.offset_x = int(math.sin(elapsed * shake_speed) * current_intensity)
        self.offset_y = int(math.cos(elapsed * shake_speed * 0.7) * current_intensity * 0.5)

        return (self.offset_x, self.offset_y)

    def get_offset(self) -> Tuple[int, int]:
        """현재 흔들림 오프셋을 반환합니다."""
        return (self.offset_x, self.offset_y)


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
    coin_font = pygame.font.Font(None, 24)
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
        number_font = pygame.font.Font(None, 36)
        number_text = number_font.render(str(i + 1), True, config.BLACK)
        number_rect = number_text.get_rect(
            center=(number_box_x + number_box_size // 2, number_box_y + number_box_size // 2)
        )
        screen.blit(number_text, number_rect)

        # 중앙: 업그레이드 정보 (크기 조정)
        info_x = card_x + number_box_size + 20
        icon = upgrade_icons.get(key, config.UI_ICONS["LEVEL_UP"])

        name_font = pygame.font.Font(None, 26)
        name_text = render_text_with_emoji(f"{icon} {name}", name_font, config.WHITE, "SMALL")
        screen.blit(name_text, (info_x, card_y + 8))

        # 레벨 바 (별 모양)
        stars = "★" * current_level + "☆" * (max_level - current_level)
        level_font = pygame.font.Font(None, 20)
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

        cost_font = pygame.font.Font(None, 22)
        cost_text = cost_font.render(cost_text_content, True, cost_color)
        cost_rect = cost_text.get_rect(
            midright=(card_x + card_width - 15, card_y + card_height // 2)
        )
        screen.blit(cost_text, cost_rect)

    # 하단 안내
    instruction_y = cards_start_y + len(upgrade_items) * card_spacing + 20
    exit_font = pygame.font.Font(None, 22)
    # render_text_with_emoji 대신 일반 렌더링 사용 (글자 깨짐 방지)
    exit_text = exit_font.render("Press 'C' to Close Shop | Press 'ESC' to Quit Game", True, config.UI_COLORS["TEXT_SECONDARY"])
    screen.blit(exit_text, exit_text.get_rect(center=(center_x, instruction_y)))


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

        button_font = pygame.font.Font(None, 24)
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
        score_font = pygame.font.Font(None, 28)
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
        button_start_y = menu_y + 195
        button_spacing = 50

        # 버튼 리스트 (ID, 텍스트, 색상)
        buttons = [
            ("restart", "Restart (R)", config.TEXT_LEVELS["PRIMARY"]),
            ("quit", "Quit (ESC)", config.STATE_COLORS["DANGER"])
        ]

        button_font = pygame.font.Font(None, 24)
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
    subtitle_font = pygame.font.Font(None, 24)  # 작은 폰트
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
        effect_font = pygame.font.Font(None, 22)  # 32 → 22 (축소)
        effect_text = effect_font.render(effect_str, True, config.STATE_COLORS["GOLD"])
        screen.blit(effect_text, (name_x, card_y + 35))

        # 설명 텍스트 (크기 축소) - 통일된 색상
        if description:
            desc_font = pygame.font.Font(None, 18)  # 24 → 18 (축소)
            desc_text = desc_font.render(description, True, config.TEXT_LEVELS["SECONDARY"])
            screen.blit(desc_text, (name_x, card_y + 58))

    # 하단 안내 문구 (크기 축소, 깜빡임 효과)
    instruction_y = cards_start_y + len(options) * card_spacing + 20

    # 깜빡임 효과
    import time
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


# =========================================================
# 2. HUD 그리기 함수
# =========================================================


def draw_hud(
    screen: pygame.Surface,
    screen_size: Tuple[int, int],
    font_medium: pygame.font.Font,
    player: "Player",
    game_data: dict,
):
    """
    HUD (Head-Up Display)를 그립니다. (HP 바, 레벨, 점수)
    """
    SCREEN_WIDTH, SCREEN_HEIGHT = screen_size
    center_x = SCREEN_WIDTH // 2

    # ==================== 좌상단 패널 (HP, 레벨, 킬) ====================
    panel_margin = 20
    panel_padding = 12
    panel_x = panel_margin
    panel_y = panel_margin

    # 패널 배경 (반투명) - 웨이브 정보 추가로 높이 증가 - 통일된 색상
    panel_width = 300
    panel_height = 115  # 90 → 115 (웨이브 정보 공간)
    panel_bg = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
    panel_bg.fill((*config.BG_LEVELS["PANEL"], 200))
    screen.blit(panel_bg, (panel_x, panel_y))

    # 1. HP 바 (패널 내부)
    bar_width = panel_width - (panel_padding * 2)
    bar_height = 28
    bar_x = panel_x + panel_padding
    bar_y = panel_y + panel_padding

    health_ratio = player.hp / player.max_hp if player.max_hp > 0 else 0

    # HP에 따른 색상 결정 - 통일된 색상
    if health_ratio <= 0.25:
        hp_color = config.STATE_COLORS["DANGER"]
    elif health_ratio <= 0.5:
        hp_color = config.STATE_COLORS["WARNING"]
    else:
        hp_color = config.STATE_COLORS["SUCCESS"]

    # HP 바 배경 (테두리 없음) - 통일된 색상
    pygame.draw.rect(screen, config.BG_LEVELS["ELEVATED"], (bar_x, bar_y, bar_width, bar_height))
    # HP 바 (현재 체력)
    if health_ratio > 0:
        pygame.draw.rect(screen, hp_color,
                        (bar_x, bar_y, int(bar_width * health_ratio), bar_height))

    # HP 텍스트 (바 중앙)
    hp_text = render_text_with_emoji(
        f"{config.UI_ICONS['HP']} {int(player.hp)} / {int(player.max_hp)}",
        font_medium,
        config.WHITE,
        "MEDIUM"
    )
    text_rect = hp_text.get_rect(center=(bar_x + bar_width // 2, bar_y + bar_height // 2))
    screen.blit(hp_text, text_rect)

    # 2. 레벨 & 킬 카운트 (HP 바 아래, 패널 내부) - 통일된 색상
    info_y = bar_y + bar_height + 10

    # 레벨 (왼쪽)
    level_text = render_text_with_emoji(
        f"{config.UI_ICONS['SWORD']} LV {game_data['player_level']}",
        font_medium,
        config.STATE_COLORS["GOLD"],
        "MEDIUM"
    )
    screen.blit(level_text, (bar_x, info_y))

    # 킬 카운트 (오른쪽)
    kill_text = render_text_with_emoji(
        f"Kills: {game_data['kill_count']}",
        font_medium,
        config.TEXT_LEVELS["PRIMARY"],
        "MEDIUM"
    )
    screen.blit(kill_text, (bar_x + bar_width - kill_text.get_width(), info_y))

    # 3. 웨이브 정보 (레벨/킬 카운트 아래) - 통일된 색상
    wave_y = info_y + 25
    current_wave = game_data.get("current_wave", 1)
    wave_kills = game_data.get("wave_kills", 0)
    wave_target = game_data.get("wave_target_kills", 20)

    wave_text = render_text_with_emoji(
        f"Wave {current_wave}/{config.TOTAL_WAVES}: {wave_kills}/{wave_target}",
        font_medium,
        config.STATE_COLORS["INFO"],
        "MEDIUM"
    )
    screen.blit(wave_text, (bar_x, wave_y))

    # ==================== 우상단 패널 (코인) ====================
    coin_panel_width = 200
    coin_panel_height = 50
    coin_panel_x = SCREEN_WIDTH - coin_panel_width - panel_margin
    coin_panel_y = panel_margin

    # 코인 패널 배경 (테두리 없음) - 통일된 색상
    coin_bg = pygame.Surface((coin_panel_width, coin_panel_height), pygame.SRCALPHA)
    coin_bg.fill((*config.BG_LEVELS["PANEL"], 200))
    screen.blit(coin_bg, (coin_panel_x, coin_panel_y))

    # 코인 텍스트 (중앙 정렬) - 통일된 색상
    coin_text = render_text_with_emoji(
        f"{config.UI_ICONS['COIN']} {game_data['score']}",
        font_medium,
        config.STATE_COLORS["GOLD"],
        "MEDIUM"
    )
    coin_rect = coin_text.get_rect(center=(coin_panel_x + coin_panel_width // 2,
                                            coin_panel_y + coin_panel_height // 2))
    screen.blit(coin_text, coin_rect)

    # ==================== 상단 중앙 (EXP 게이지) ====================
    level_threshold = get_next_level_threshold(game_data["player_level"])
    progress_ratio = min(1.0, game_data["uncollected_score"] / level_threshold)

    exp_panel_width = 400
    exp_panel_height = 45
    exp_panel_x = (SCREEN_WIDTH - exp_panel_width) // 2
    exp_panel_y = panel_margin

    # EXP 패널 배경 (테두리 없음) - 통일된 색상
    exp_bg = pygame.Surface((exp_panel_width, exp_panel_height), pygame.SRCALPHA)
    exp_bg.fill((*config.BG_LEVELS["PANEL"], 200))
    screen.blit(exp_bg, (exp_panel_x, exp_panel_y))

    # EXP 게이지 (패널 내부)
    gauge_width = exp_panel_width - (panel_padding * 2)
    gauge_height = 24
    gauge_x = exp_panel_x + panel_padding
    gauge_y = exp_panel_y + (exp_panel_height - gauge_height) // 2

    # 게이지 배경 (테두리 없음) - 통일된 색상
    pygame.draw.rect(screen, config.BG_LEVELS["ELEVATED"], (gauge_x, gauge_y, gauge_width, gauge_height))

    # EXP 바 (진행도) - 통일된 색상
    if progress_ratio > 0:
        pygame.draw.rect(screen, config.STATE_COLORS["INFO"],
                        (gauge_x, gauge_y, int(gauge_width * progress_ratio), gauge_height))

    # 게이지 텍스트 (중앙)
    gauge_value_text = render_text_with_emoji(
        f"{config.UI_ICONS['EXP']} {game_data['uncollected_score']}/{level_threshold}",
        font_medium,
        config.WHITE,
        "MEDIUM"
    )
    text_rect = gauge_value_text.get_rect(center=(gauge_x + gauge_width // 2, gauge_y + gauge_height // 2))
    screen.blit(gauge_value_text, text_rect)

    # 6. 무기 쿨다운 인디케이터 (화면 하단 중앙)
    # 플레이어의 무기 쿨다운 상태 표시
    weapon = player.weapon
    cooldown_ratio = min(1.0, weapon.time_since_last_shot / weapon.cooldown)

    # 원형 쿨다운 인디케이터
    indicator_size = 80
    indicator_x = SCREEN_WIDTH // 2
    indicator_y = SCREEN_HEIGHT - 60
    radius = indicator_size // 2

    # 배경 원 - 통일된 색상
    pygame.draw.circle(screen, config.BG_LEVELS["ELEVATED"], (indicator_x, indicator_y), radius)

    # 쿨다운 진행도 원 (시계방향으로 채워짐) - 통일된 색상
    if cooldown_ratio < 1.0:
        # 쿨다운 중 (빨간색)
        color = config.STATE_COLORS["DANGER"]
    else:
        # 발사 가능 (초록색)
        color = config.STATE_COLORS["SUCCESS"]

    # 부채꼴 게이지 그리기
    if cooldown_ratio > 0:
        import math
        start_angle = -math.pi / 2  # 12시 방향부터 시작
        end_angle = start_angle + (2 * math.pi * cooldown_ratio)

        # 부채꼴 모양으로 그리기
        points = [(indicator_x, indicator_y)]
        for i in range(int(cooldown_ratio * 100) + 1):
            angle = start_angle + (end_angle - start_angle) * i / 100
            x = indicator_x + int(radius * math.cos(angle))
            y = indicator_y + int(radius * math.sin(angle))
            points.append((x, y))

        if len(points) > 2:
            pygame.draw.polygon(screen, color, points)

    # 중앙 아이콘 (더 크게)
    icon_font = pygame.font.Font(None, 50)
    icon_text = render_text_with_emoji(config.UI_ICONS["GUN"], icon_font, config.WHITE, "MEDIUM")
    icon_rect = icon_text.get_rect(center=(indicator_x, indicator_y))
    screen.blit(icon_text, icon_rect)

    # ==================== Ship Ability 인디케이터 (무기 인디케이터 왼쪽) ====================
    ability_info = None
    if hasattr(player, 'get_ship_ability_info'):
        ability_info = player.get_ship_ability_info()

    if ability_info:
        ability_indicator_x = indicator_x - 120  # 무기 인디케이터 왼쪽에 위치
        ability_indicator_y = indicator_y
        ability_radius = 35

        # 쿨다운 비율 계산
        ability_cooldown = ability_info.get('cooldown', 0)
        ability_remaining = ability_info.get('remaining', 0)
        ability_ready = ability_info.get('ready', False)
        ability_active = ability_info.get('active', False)

        if ability_cooldown > 0:
            ability_ratio = 1.0 - (ability_remaining / ability_cooldown)
        else:
            ability_ratio = 1.0

        # 배경 원 - 통일된 색상
        pygame.draw.circle(screen, config.BG_LEVELS["ELEVATED"], (ability_indicator_x, ability_indicator_y), ability_radius)

        # 상태에 따른 색상 - 통일된 색상
        if ability_active:
            # 능력 활성화 중 - 노란색 테두리 + 펄스 효과
            ability_color = config.STATE_COLORS["WARNING"]
            pygame.draw.circle(screen, ability_color, (ability_indicator_x, ability_indicator_y), ability_radius, 4)
        elif ability_ready:
            # 사용 가능 - 초록색
            ability_color = config.STATE_COLORS["SUCCESS"]
        else:
            # 쿨다운 중 - 빨간색에서 초록색으로 전환
            ability_color = config.STATE_COLORS["DANGER"]

        # 쿨다운 진행도 원 그리기
        if ability_ratio > 0 and not ability_active:
            import math
            start_angle = -math.pi / 2
            end_angle = start_angle + (2 * math.pi * ability_ratio)

            points = [(ability_indicator_x, ability_indicator_y)]
            for i in range(int(ability_ratio * 100) + 1):
                angle = start_angle + (end_angle - start_angle) * i / 100
                x = ability_indicator_x + int(ability_radius * math.cos(angle))
                y = ability_indicator_y + int(ability_radius * math.sin(angle))
                points.append((x, y))

            if len(points) > 2:
                pygame.draw.polygon(screen, ability_color, points)

        # 능력 아이콘 (E키 표시)
        ability_font = pygame.font.Font(None, 32)
        ability_icon_text = ability_font.render("E", True, config.WHITE)
        ability_icon_rect = ability_icon_text.get_rect(center=(ability_indicator_x, ability_indicator_y - 5))
        screen.blit(ability_icon_text, ability_icon_rect)

        # 능력 이름 (아이콘 아래)
        ability_name_font = pygame.font.Font(None, 18)
        ability_name = ability_info.get('name', 'Ability')[:8]  # 최대 8글자
        ability_name_text = ability_name_font.render(ability_name, True, config.WHITE)
        ability_name_rect = ability_name_text.get_rect(center=(ability_indicator_x, ability_indicator_y + ability_radius + 12))
        screen.blit(ability_name_text, ability_name_rect)

        # 쿨다운 시간 표시 (쿨다운 중일 때만)
        if not ability_ready and ability_remaining > 0:
            cooldown_font = pygame.font.Font(None, 20)
            cooldown_text = cooldown_font.render(f"{ability_remaining:.1f}s", True, config.WHITE)
            cooldown_rect = cooldown_text.get_rect(center=(ability_indicator_x, ability_indicator_y + 10))
            screen.blit(cooldown_text, cooldown_rect)

    # ==================== 좌하단 (환생 아이콘) ====================
    reincarnation_count = player.upgrades.get("REINCARNATION", 0)
    if reincarnation_count > 0:
        reincarnation_panel_margin = 20
        reincarnation_panel_x = reincarnation_panel_margin
        reincarnation_panel_y = SCREEN_HEIGHT - 80

        # 환생 아이콘 크기
        icon_size = 40
        icon_spacing = 10

        for i in range(reincarnation_count):
            icon_x = reincarnation_panel_x + i * (icon_size + icon_spacing)
            icon_y = reincarnation_panel_y

            # 배경 원 (반투명 검정)
            pygame.draw.circle(screen, (0, 0, 0, 150), (icon_x + icon_size // 2, icon_y + icon_size // 2), icon_size // 2 + 2)

            # 환생 아이콘
            reincarnation_font = pygame.font.Font(None, 36)
            reincarnation_icon = render_text_with_emoji(
                config.UI_ICONS["REINCARNATION"],
                reincarnation_font,
                config.UI_COLORS["DANGER"],
                "MEDIUM"
            )
            icon_rect = reincarnation_icon.get_rect(center=(icon_x + icon_size // 2, icon_y + icon_size // 2))
            screen.blit(reincarnation_icon, icon_rect)


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
    desc_font = pygame.font.Font(None, 24)
    desc_text = render_text_with_emoji(
        wave_desc,
        desc_font,
        config.TEXT_LEVELS["PRIMARY"],
        "SMALL"
    )
    screen.blit(desc_text, desc_text.get_rect(center=(center_x, panel_y + 140)))

    # 목표 킬 수 (크기 축소) - 통일된 색상
    target_kills = game_data.get("wave_target_kills", 20)
    target_font = pygame.font.Font(None, 22)
    target_text = render_text_with_emoji(
        f"{config.UI_ICONS['SWORD']} Target: {target_kills} Kills",
        target_font,
        config.TEXT_LEVELS["SECONDARY"],
        "SMALL"
    )
    screen.blit(target_text, target_text.get_rect(center=(center_x, panel_y + 190)))

    # 시작 안내 (깜빡이는 효과, 크기 축소) - 통일된 색상
    import math
    alpha = int(127 + 128 * math.sin(pygame.time.get_ticks() / 500))
    start_font = pygame.font.Font(None, 26)
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
    stats_font = pygame.font.Font(None, 24)
    kills_text = render_text_with_emoji(
        f"{config.UI_ICONS['SWORD']} Kills This Wave: {kills}",
        stats_font,
        config.TEXT_LEVELS["PRIMARY"],
        "SMALL"
    )
    screen.blit(kills_text, kills_text.get_rect(center=(center_x, stats_y)))

    total_font = pygame.font.Font(None, 22)
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
        credit_font = pygame.font.Font(None, 28)
        credit_text = render_text_with_emoji(
            f"{config.UI_ICONS['COIN']} +{credit_reward} Credits!",
            credit_font,
            config.STATE_COLORS["GOLD"],
            "MEDIUM"
        )
        screen.blit(credit_text, credit_text.get_rect(center=(center_x, stats_y + 70)))

    # 다음 웨이브 안내 (깜빡임, 크기 축소) - 통일된 색상
    import math
    alpha = int(127 + 128 * math.sin(pygame.time.get_ticks() / 500))

    next_font = pygame.font.Font(None, 26)
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
# 4. 보스 체력바 그리기 함수
# =========================================================

# 보스 HP 바 이미지 캐시
_boss_bar_image_cache: Dict[str, pygame.Surface] = {}


def _load_enemy_bar_image(bar_width: int, bar_height: int) -> Optional[pygame.Surface]:
    """적 HP 바 이미지 로드 (캐시 사용)"""
    from pathlib import Path

    cache_key = f"enemy_bar_{bar_width}_{bar_height}"
    if cache_key in _boss_bar_image_cache:
        return _boss_bar_image_cache[cache_key]

    bar_path = Path("assets/images/ui/enemy_bar_01.png")
    if bar_path.exists():
        try:
            original = pygame.image.load(str(bar_path)).convert_alpha()
            scaled = pygame.transform.smoothscale(original, (bar_width, bar_height))
            _boss_bar_image_cache[cache_key] = scaled
            return scaled
        except Exception as e:
            print(f"WARNING: Failed to load enemy bar image: {e}")
    return None


def draw_boss_health_bar(
    screen: pygame.Surface,
    screen_size: Tuple[int, int],
    font_medium: pygame.font.Font,
    boss,
    enemy_count: int = 1,
    current_wave: int = 1
):
    """
    화면 상단에 큰 보스 체력바를 그립니다.
    Wave 5 보스전에서는 enemy_bar_01.png 이미지를 사용합니다.

    Args:
        boss: Boss 객체
        enemy_count: 현재 화면의 적 수 (보스전용 바 크기/강조 조절)
        current_wave: 현재 웨이브 (5, 10, 15, 20 보스 웨이브)
    """
    if not boss or not boss.is_alive:
        return

    SCREEN_WIDTH, SCREEN_HEIGHT = screen_size

    # 적 수에 따른 HP 바 크기 조절
    # 적이 많으면 더 크고 강조된 바
    if enemy_count >= 5:
        bar_width = int(SCREEN_WIDTH * 0.7)  # 70%
        bar_height = 45
    elif enemy_count >= 3:
        bar_width = int(SCREEN_WIDTH * 0.65)  # 65%
        bar_height = 40
    else:
        bar_width = int(SCREEN_WIDTH * 0.6)  # 60%
        bar_height = 35

    bar_x = (SCREEN_WIDTH - bar_width) // 2
    bar_y = 150  # HUD 아래 위치

    # 보스 이름 표시
    name_font = pygame.font.Font(None, 32)
    name_text = render_text_with_emoji(
        f"👹 {boss.boss_name} 👹",
        name_font,
        config.UI_COLORS["DANGER"],
        "MEDIUM"
    )
    name_rect = name_text.get_rect(center=(SCREEN_WIDTH // 2, bar_y - 25))
    screen.blit(name_text, name_rect)

    # 체력바 배경 패널
    panel_bg = pygame.Surface((bar_width + 20, bar_height + 50), pygame.SRCALPHA)
    panel_bg.fill((20, 20, 40, 200))
    screen.blit(panel_bg, (bar_x - 10, bar_y - 35))

    # 보스 웨이브(5, 10, 15, 20)에서는 이미지 HP 바 사용
    use_image_bar = current_wave in config.BOSS_WAVES

    if use_image_bar:
        # 이미지 기반 HP 바
        bar_image = _load_enemy_bar_image(bar_width, bar_height)

        if bar_image:
            # 배경 (어두운 버전)
            dark_bar = bar_image.copy()
            dark_bar.fill((50, 50, 50), special_flags=pygame.BLEND_RGB_MULT)
            screen.blit(dark_bar, (bar_x, bar_y))

            # 현재 체력 비율
            health_ratio = boss.hp / boss.max_hp
            current_health_width = int(bar_width * health_ratio)

            if current_health_width > 0:
                # 체력 부분만 마스킹하여 표시
                health_surface = pygame.Surface((current_health_width, bar_height), pygame.SRCALPHA)
                health_surface.blit(bar_image, (0, 0))

                # 체력에 따른 색조 변경
                if health_ratio <= 0.25:
                    # 위험 - 붉은 틴트
                    tint = pygame.Surface((current_health_width, bar_height), pygame.SRCALPHA)
                    tint.fill((255, 100, 100, 80))
                    health_surface.blit(tint, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
                elif health_ratio <= 0.5:
                    # 경고 - 주황 틴트
                    tint = pygame.Surface((current_health_width, bar_height), pygame.SRCALPHA)
                    tint.fill((255, 180, 100, 50))
                    health_surface.blit(tint, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

                screen.blit(health_surface, (bar_x, bar_y))

            # 테두리 (이미지 위에)
            pygame.draw.rect(screen, config.UI_COLORS["DANGER"],
                            (bar_x - 2, bar_y - 2, bar_width + 4, bar_height + 4), 2)
        else:
            # 이미지 없으면 기본 렌더링
            _draw_default_boss_bar(screen, bar_x, bar_y, bar_width, bar_height, boss)
    else:
        # 일반 웨이브는 기본 스타일
        _draw_default_boss_bar(screen, bar_x, bar_y, bar_width, bar_height, boss)

    # HP 텍스트 (중앙)
    hp_text_font = pygame.font.Font(None, 24)
    hp_text = hp_text_font.render(
        f"{int(boss.hp):,} / {int(boss.max_hp):,} HP",
        True,
        config.WHITE
    )
    hp_rect = hp_text.get_rect(center=(bar_x + bar_width // 2, bar_y + bar_height // 2))

    # 텍스트 그림자
    shadow_text = hp_text_font.render(
        f"{int(boss.hp):,} / {int(boss.max_hp):,} HP",
        True,
        (0, 0, 0)
    )
    shadow_rect = shadow_text.get_rect(center=(bar_x + bar_width // 2 + 1, bar_y + bar_height // 2 + 1))
    screen.blit(shadow_text, shadow_rect)
    screen.blit(hp_text, hp_rect)


def _draw_default_boss_bar(
    screen: pygame.Surface,
    bar_x: int,
    bar_y: int,
    bar_width: int,
    bar_height: int,
    boss
):
    """기본 보스 HP 바 렌더링 (이미지 없을 때)"""
    # 체력바 테두리 (빨간색)
    pygame.draw.rect(screen, config.UI_COLORS["DANGER"],
                    (bar_x - 2, bar_y - 2, bar_width + 4, bar_height + 4))

    # 체력바 배경 (검은색)
    pygame.draw.rect(screen, config.BLACK, (bar_x, bar_y, bar_width, bar_height))

    # 현재 체력 (빨간색 그라데이션)
    health_ratio = boss.hp / boss.max_hp
    current_health_width = int(bar_width * health_ratio)

    # 체력 색상 (체력에 따라 변경)
    if health_ratio > 0.5:
        hp_color = config.UI_COLORS["DANGER"]  # 빨간색
    elif health_ratio > 0.25:
        hp_color = config.UI_COLORS["WARNING"]  # 주황색
    else:
        hp_color = config.UI_COLORS["DANGER_DARK"]  # 진한 빨강

    pygame.draw.rect(screen, hp_color,
                    (bar_x, bar_y, current_health_width, bar_height))

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
    subtitle_font = pygame.font.Font(None, 26)
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
    stat_font = pygame.font.Font(None, 24)

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

    base_btn_font = pygame.font.Font(None, 28)
    base_btn_text = base_btn_font.render("[H] Return to Base", True, config.TEXT_LEVELS["PRIMARY"])
    base_btn_rect = base_btn_text.get_rect(center=(center_x, base_button_y + base_button_height // 2))
    screen.blit(base_btn_text, base_btn_rect)

    # 보스 러시 제안 섹션 - 통일된 색상
    boss_rush_y = panel_y + panel_height - 75

    # 제안 텍스트
    proposal_font = pygame.font.Font(None, 22)
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

    instruction_font = pygame.font.Font(None, 20)
    instruction_text = render_text_with_emoji(
        "B: Boss Rush | R: Restart | Q: Quit",
        instruction_font,
        config.TEXT_LEVELS["SECONDARY"],
        "SMALL"
    )
    instruction_rect = instruction_text.get_rect(center=(center_x, instruction_y))
    screen.blit(instruction_text, instruction_rect)

    # 감사 메시지 (패널 외부 하단) - 통일된 색상
    thanks_font = pygame.font.Font(None, 20)
    thanks_text = render_text_with_emoji(
        "Thank you for playing!",
        thanks_font,
        config.TEXT_LEVELS["SECONDARY"],
        "SMALL"
    )
    thanks_rect = thanks_text.get_rect(center=(center_x, SCREEN_HEIGHT - 30))
    screen.blit(thanks_text, thanks_rect)


# =========================================================
# 스킬 인디케이터 UI
# =========================================================

def draw_skill_indicators(
    screen: pygame.Surface,
    screen_size: Tuple[int, int],
    player: "Player",
    current_time: float
):
    """하단에 모든 스킬들을 네모 박스로 표시합니다 (쿨다운과 동일 높이)"""
    import math

    SCREEN_WIDTH, SCREEN_HEIGHT = screen_size
    settings = config.SKILL_INDICATOR_SETTINGS

    box_size = settings["box_size"]
    icon_spacing = settings["icon_spacing"]
    base_y = SCREEN_HEIGHT - settings["base_y"]

    # 이모지 폰트 가져오기
    emoji_font = config.EMOJI_FONTS.get("MEDIUM")
    text_font = pygame.font.Font(None, 16)
    if not emoji_font:
        return  # 이모지 폰트 없으면 스킵

    # 모든 스킬 정렬 (획득 여부 무관)
    left_skills = []
    right_skills = []

    for skill_name, skill_info in config.SKILL_ICONS.items():
        if skill_info['side'] == 'left':
            left_skills.append((skill_info['order'], skill_name, skill_info))
        else:
            right_skills.append((skill_info['order'], skill_name, skill_info))

    # 정렬 (order 기준)
    left_skills.sort()
    right_skills.sort()

    # 왼쪽 스킬 그리기 (쿨다운 왼쪽)
    cooldown_center_x = SCREEN_WIDTH // 2
    start_x_left = cooldown_center_x - 180  # 쿨다운으로부터 180px 왼쪽에서 시작

    for i, (order, skill_name, skill_info) in enumerate(left_skills):
        pos_x = start_x_left - (i * icon_spacing)
        _draw_single_skill_box(
            screen, (pos_x, base_y), skill_name, skill_info,
            player, current_time, box_size, settings, emoji_font, text_font
        )

    # 오른쪽 스킬 그리기 (쿨다운 오른쪽)
    start_x_right = cooldown_center_x + 180  # 쿨다운으로부터 180px 오른쪽에서 시작

    for i, (order, skill_name, skill_info) in enumerate(right_skills):
        pos_x = start_x_right + (i * icon_spacing)
        _draw_single_skill_box(
            screen, (pos_x, base_y), skill_name, skill_info,
            player, current_time, box_size, settings, emoji_font, text_font
        )


def _draw_single_skill_box(
    screen: pygame.Surface,
    pos: Tuple[int, int],
    skill_name: str,
    skill_info: dict,
    player: "Player",
    current_time: float,
    box_size: int,
    settings: dict,
    emoji_font: pygame.font.Font,
    text_font: pygame.font.Font
):
    """개별 스킬을 네모 박스로 그립니다 (개선된 스타일)"""
    import math

    pos_x, pos_y = pos
    skill_type = skill_info['type']
    icon_emoji = skill_info['icon']
    skill_name_text = skill_info['name']
    skill_color = skill_info['color']

    # 획득 여부
    is_acquired = skill_name in player.acquired_skills
    has_synergy = is_acquired and _has_synergy_with_skill(skill_name, player)

    # 네모 박스 위치 (중앙 기준)
    box_x = pos_x - box_size // 2
    box_y = pos_y - box_size // 2

    # 트리거 스킬의 쿨다운 비율 계산
    cooldown_ratio = 1.0
    if skill_type == 'trigger' and is_acquired:
        last_trigger = player.skill_last_trigger.get(skill_name, 0.0)
        time_since_trigger = current_time - last_trigger
        skill_cooldown = skill_info.get('cooldown', 1.0)
        cooldown_ratio = min(1.0, time_since_trigger / skill_cooldown)

    # 배경색 결정
    if not is_acquired:
        # 미획득: 전체 어둡게
        bg_color = (40, 40, 40)
    elif skill_type == 'passive':
        # 패시브: 고유색 + 깜박임
        blink_factor = 0.7 + 0.3 * math.sin(current_time * settings["passive_blink_speed"] * math.pi * 2)
        bg_color = tuple(int(c * blink_factor) for c in skill_color)
    else:
        # 트리거: 쿨다운에 따라 색상 회전 변화
        if cooldown_ratio < 1.0:
            # 쿨다운 중: 색상 회전 (빨강 -> 노랑 -> 초록)
            if cooldown_ratio < 0.5:
                # 0~0.5: 빨강 -> 노랑
                t = cooldown_ratio * 2
                bg_color = (
                    255,
                    int(255 * t),
                    0
                )
            else:
                # 0.5~1.0: 노랑 -> 초록
                t = (cooldown_ratio - 0.5) * 2
                bg_color = (
                    int(255 * (1 - t)),
                    255,
                    0
                )
        else:
            # 발사 가능: 초록색 - 통일된 색상
            bg_color = config.STATE_COLORS["SUCCESS"]

    # 네모 박스 그리기
    pygame.draw.rect(screen, bg_color, (box_x, box_y, box_size, box_size))

    # 쿨다운 게이지 (트리거 스킬만)
    if skill_type == 'trigger' and is_acquired and cooldown_ratio < 1.0:
        # 부채꼴 형태로 쿨다운 표시
        start_angle = -math.pi / 2  # 12시 방향부터
        end_angle = start_angle + (2 * math.pi * cooldown_ratio)

        points = [(pos_x, pos_y)]
        for i in range(int(cooldown_ratio * 100) + 1):
            angle = start_angle + (end_angle - start_angle) * i / 100
            x = pos_x + int((box_size // 2) * math.cos(angle))
            y = pos_y + int((box_size // 2) * math.sin(angle))
            points.append((x, y))

        if len(points) > 2:
            pygame.draw.polygon(screen, bg_color, points)

    # 테두리 (3px)
    border_color = (100, 100, 100) if not is_acquired else config.WHITE
    pygame.draw.rect(screen, border_color, (box_x, box_y, box_size, box_size), settings["border_width"])

    # 이모지 아이콘 렌더링
    icon_surf = emoji_font.render(icon_emoji, True, (255, 255, 255))

    # 미획득 시 어둡게
    if not is_acquired:
        dim_overlay = pygame.Surface(icon_surf.get_size(), pygame.SRCALPHA)
        dim_value = int(255 * settings["inactive_dim"])
        dim_overlay.fill((dim_value, dim_value, dim_value))
        temp_surf = icon_surf.copy()
        temp_surf.blit(dim_overlay, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        icon_surf = temp_surf

    # 중앙 정렬
    icon_rect = icon_surf.get_rect(center=(pos_x, pos_y))
    screen.blit(icon_surf, icon_rect)

    # 시너지 표시 (우상단 별)
    if has_synergy:
        star_font = config.EMOJI_FONTS.get("SMALL")
        if star_font:
            star_surf = star_font.render('✨', True, (255, 255, 100))
            star_rect = star_surf.get_rect(center=(box_x + box_size - 10, box_y + 10))
            screen.blit(star_surf, star_rect)

    # 하단에 스킬명 표시 (밝은 흰색, 더 크게)
    name_font = pygame.font.Font(None, settings["text_size"])
    name_surf = name_font.render(skill_name_text, True, (255, 255, 255))
    name_rect = name_surf.get_rect(center=(pos_x, pos_y + box_size // 2 + settings["text_offset_y"]))
    screen.blit(name_surf, name_rect)


def _has_synergy_with_skill(skill_name: str, player: "Player") -> bool:
    """해당 스킬과 관련된 시너지가 활성화되어 있는지 확인"""
    # 시너지별 필요 스킬 매핑
    synergy_map = {
        'toggle_piercing': ['explosive_pierce'],
        'add_explosive': ['explosive_pierce', 'frozen_explosion'],
        'add_lightning': ['lightning_storm'],
        'add_frost': ['frozen_explosion'],
        'increase_max_hp': ['tank_build'],
        'add_regeneration': ['tank_build'],
        'toggle_coin_magnet': ['treasure_hunter'],
        'add_lucky_drop': ['treasure_hunter'],
    }

    related_synergies = synergy_map.get(skill_name, [])

    for synergy in related_synergies:
        if synergy in player.active_synergies:
            return True

    return False


def draw_random_event_ui(screen: pygame.Surface, screen_size: Tuple[int, int], game_data: Dict):
    """랜덤 이벤트 UI 표시 (알림, 화면 틴트, 메테오 경고)"""
    active_event = game_data.get("active_event")
    if not active_event:
        return

    event_data = config.RANDOM_EVENTS.get(active_event)
    if not event_data:
        return

    width, height = screen_size

    # 1. 화면 틴트 효과
    screen_tint = event_data.get("screen_tint")
    if screen_tint:
        tint_surf = pygame.Surface(screen_size, pygame.SRCALPHA)
        tint_surf.fill(screen_tint)
        screen.blit(tint_surf, (0, 0))

    # 2. 이벤트 알림 (처음 3초간 표시)
    if game_data.get("event_notification_timer", 0) > 0:
        notification_font = pygame.font.Font(None, 48)
        small_font = pygame.font.Font(None, 28)

        # 이벤트 이름
        name_text = f"{event_data['icon']} {event_data['name']}"
        name_surf = notification_font.render(name_text, True, event_data["color"])
        name_rect = name_surf.get_rect(center=(width // 2, height // 4))

        # 배경 박스
        padding = 30
        box_rect = pygame.Rect(
            name_rect.left - padding,
            name_rect.top - padding,
            name_rect.width + padding * 2,
            name_rect.height + padding * 2 + 50
        )
        pygame.draw.rect(screen, (0, 0, 0, 180), box_rect, border_radius=15)
        pygame.draw.rect(screen, event_data["color"], box_rect, 3, border_radius=15)

        screen.blit(name_surf, name_rect)

        # 설명
        desc_surf = small_font.render(event_data["description"], True, (200, 200, 200))
        desc_rect = desc_surf.get_rect(center=(width // 2, height // 4 + 50))
        screen.blit(desc_surf, desc_rect)

    # 3. 메테오 떨어지는 애니메이션 및 폭발 효과 (METEOR_SHOWER 이벤트)
    if active_event == "METEOR_SHOWER":
        meteors = game_data.get("event_meteors", [])

        # 이미지 로드 (캐시 사용)
        try:
            if not hasattr(draw_random_event_ui, '_meteor_trail_img'):
                if config.METEOR_TRAIL_IMAGE_PATH.exists():
                    trail_img = pygame.image.load(str(config.METEOR_TRAIL_IMAGE_PATH)).convert_alpha()
                    # 트레일 이미지 크게 (떨어지는 모습용)
                    draw_random_event_ui._meteor_trail_img = pygame.transform.smoothscale(trail_img, (120, 180))
                else:
                    draw_random_event_ui._meteor_trail_img = None

            if not hasattr(draw_random_event_ui, '_meteor_head_img'):
                if config.METEOR_HEAD_IMAGE_PATH.exists():
                    head_img = pygame.image.load(str(config.METEOR_HEAD_IMAGE_PATH)).convert_alpha()
                    # 헤드 이미지 크게 (폭발 효과용)
                    draw_random_event_ui._meteor_head_img = pygame.transform.smoothscale(head_img, (150, 150))
                else:
                    draw_random_event_ui._meteor_head_img = None
        except Exception:
            draw_random_event_ui._meteor_trail_img = None
            draw_random_event_ui._meteor_head_img = None

        for meteor in meteors:
            target_pos = (int(meteor["target_x"]), int(meteor["target_y"]))

            if not meteor["active"]:
                # 떨어지는 중 - 트레일 이미지 사용
                progress = meteor["timer"] / meteor["warning_duration"]

                if draw_random_event_ui._meteor_trail_img:
                    # 시작 위치 (화면 위), 끝 위치 (타겟)
                    start_y = -150
                    end_y = target_pos[1]
                    current_y = start_y + (end_y - start_y) * progress

                    # 트레일 이미지 회전 (대각선 낙하)
                    rotated_trail = pygame.transform.rotate(draw_random_event_ui._meteor_trail_img, -60)
                    trail_rect = rotated_trail.get_rect(center=(target_pos[0], int(current_y)))
                    screen.blit(rotated_trail, trail_rect)

            else:
                # 폭발 중 - 헤드 이미지로 폭발 효과
                explosion_timer = meteor.get("explosion_timer", 0)
                explosion_duration = meteor.get("explosion_duration", 0.5)

                if explosion_timer < explosion_duration and draw_random_event_ui._meteor_head_img:
                    explosion_progress = explosion_timer / explosion_duration

                    # 폭발 크기 (처음에 커졌다가 줄어듦)
                    if explosion_progress < 0.3:
                        scale = 1.0 + explosion_progress * 2  # 1.0 -> 1.6
                    else:
                        scale = 1.6 - (explosion_progress - 0.3) * 1.5  # 1.6 -> 0.55

                    explosion_size = int(150 * scale)
                    if explosion_size > 10:
                        explosion_img = pygame.transform.smoothscale(
                            draw_random_event_ui._meteor_head_img,
                            (explosion_size, explosion_size)
                        )
                        # 투명도 (점점 사라짐)
                        alpha = int(255 * (1 - explosion_progress))
                        explosion_img.set_alpha(alpha)

                        explosion_rect = explosion_img.get_rect(center=target_pos)
                        screen.blit(explosion_img, explosion_rect)

                        # 폭발 글로우 효과
                        glow_surf = pygame.Surface((explosion_size * 2, explosion_size * 2), pygame.SRCALPHA)
                        glow_alpha = int(100 * (1 - explosion_progress))
                        pygame.draw.circle(glow_surf, (255, 150, 50, glow_alpha),
                                         (explosion_size, explosion_size), explosion_size)
                        glow_rect = glow_surf.get_rect(center=target_pos)
                        screen.blit(glow_surf, glow_rect)

    # 4. 활성 이벤트 표시 (화면 상단 중앙, 코인 바 아래)
    # 이벤트 기간 동안 계속 표시
    elapsed = pygame.time.get_ticks() / 1000.0 - game_data["event_start_time"]
    duration = event_data.get("duration", config.RANDOM_EVENT_SETTINGS["duration"])
    remaining_time = max(0, duration - elapsed)
    progress = max(0, min(1, elapsed / duration))

    # 이벤트 바 위치 (코인 표시 아래, 중앙 상단)
    bar_y = 45  # 코인 바 아래
    bar_width = 300
    bar_height = 30
    bar_x = (width - bar_width) // 2

    # 배경 박스
    bg_padding = 5
    bg_rect = pygame.Rect(bar_x - bg_padding, bar_y - bg_padding,
                          bar_width + bg_padding * 2, bar_height + bg_padding * 2)
    pygame.draw.rect(screen, (0, 0, 0, 150), bg_rect, border_radius=8)
    pygame.draw.rect(screen, event_data["color"], bg_rect, 2, border_radius=8)

    # 프로그레스 바
    progress_rect = pygame.Rect(bar_x, bar_y, bar_width, bar_height)
    pygame.draw.rect(screen, (40, 40, 40), progress_rect, border_radius=6)

    # 진행 바 (남은 시간)
    filled_width = int(bar_width * (1 - progress))
    if filled_width > 0:
        filled_rect = pygame.Rect(bar_x, bar_y, filled_width, bar_height)
        pygame.draw.rect(screen, event_data["color"], filled_rect, border_radius=6)

    # 이벤트 아이콘과 이름
    event_font = pygame.font.Font(None, 24)
    event_text = f"{event_data['icon']} {event_data['name']}"
    event_surf = event_font.render(event_text, True, (255, 255, 255))
    event_rect = event_surf.get_rect(center=(bar_x + bar_width // 2, bar_y + bar_height // 2))
    screen.blit(event_surf, event_rect)

    # 남은 시간 표시 (우측)
    time_font = pygame.font.Font(None, 20)
    time_text = f"{int(remaining_time)}s"
    time_surf = time_font.render(time_text, True, (200, 200, 200))
    time_rect = time_surf.get_rect(midleft=(bar_x + bar_width + 10, bar_y + bar_height // 2))
    screen.blit(time_surf, time_rect)


# =========================================================
# 설정 화면 (F1 키로 열기/닫기)
# =========================================================

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

    label_font = pygame.font.Font(None, 28)
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
    import time
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


# =========================================================
# 🎬 스테이지 전환 화면
# =========================================================

def draw_stage_transition_screen(screen: pygame.Surface, stage_num: int, stage_info: Dict, elapsed_time: float,
                                  font_huge: pygame.font.Font, font_large: pygame.font.Font,
                                  font_medium: pygame.font.Font):
    """
    스테이지 전환 화면을 그립니다.

    Args:
        screen: Pygame 화면 Surface
        stage_info: config.STAGE_INFO의 스테이지 데이터
        elapsed_time: 전환 화면이 시작된 후 경과 시간 (초)
        font_huge: 큰 폰트 (STAGE X 표시용)
        font_large: 대형 폰트 (스테이지 이름용)
        font_medium: 중형 폰트 (스토리 텍스트용)
    """
    screen_width = screen.get_width()
    screen_height = screen.get_height()

    # 페이드 인/아웃 효과 (0.0 ~ 1.0)
    fade_in_duration = 0.5
    fade_out_duration = 0.5
    total_duration = config.STAGE_TRANSITION_DURATION

    if elapsed_time < fade_in_duration:
        # 페이드 인
        alpha = int(255 * (elapsed_time / fade_in_duration))
    elif elapsed_time > total_duration - fade_out_duration:
        # 페이드 아웃
        remaining = total_duration - elapsed_time
        alpha = int(255 * (remaining / fade_out_duration))
    else:
        # 완전히 보임
        alpha = 255

    # 배경 어둡게 처리
    overlay = pygame.Surface((screen_width, screen_height))
    overlay.set_alpha(min(200, alpha))
    overlay.fill((0, 0, 0))
    screen.blit(overlay, (0, 0))

    # 스테이지 색상 강조 효과
    color_overlay = pygame.Surface((screen_width, screen_height))
    color_overlay.set_alpha(min(50, alpha // 5))
    color_overlay.fill(stage_info["color"])
    screen.blit(color_overlay, (0, 0))

    # 상단: "STAGE X" 텍스트
    stage_num_text = f"STAGE {stage_num}"
    stage_num_surface = font_huge.render(stage_num_text, True, stage_info["color"])
    stage_num_surface.set_alpha(alpha)
    stage_num_rect = stage_num_surface.get_rect(center=(screen_width // 2, screen_height // 4))
    screen.blit(stage_num_surface, stage_num_rect)

    # 중앙 상단: 영문 스테이지 이름
    name_en_surface = font_large.render(stage_info["name_en"], True, (255, 255, 255))
    name_en_surface.set_alpha(alpha)
    name_en_rect = name_en_surface.get_rect(center=(screen_width // 2, screen_height // 4 + 80))
    screen.blit(name_en_surface, name_en_rect)

    # 중앙: 한글 스테이지 이름
    name_kr_surface = font_large.render(stage_info["name"], True, (220, 220, 220))
    name_kr_surface.set_alpha(alpha)
    name_kr_rect = name_kr_surface.get_rect(center=(screen_width // 2, screen_height // 4 + 130))
    screen.blit(name_kr_surface, name_kr_rect)

    # 중앙 하단: 스토리 텍스트 (줄바꿈 처리)
    story_lines = stage_info["story"].split("\n")
    y_offset = screen_height // 2 + 50

    for line in story_lines:
        if line.strip():  # 빈 줄이 아닌 경우만
            story_surface = font_medium.render(line, True, (200, 200, 200))
            story_surface.set_alpha(alpha)
            story_rect = story_surface.get_rect(center=(screen_width // 2, y_offset))
            screen.blit(story_surface, story_rect)
        y_offset += 45  # 줄 간격

    # 하단: 진행 표시
    progress_text = f"Wave {stage_info['waves'][0]}"
    if len(stage_info['waves']) > 1:
        progress_text += f" - {stage_info['waves'][-1]}"

    progress_surface = font_medium.render(progress_text, True, stage_info["color"])
    progress_surface.set_alpha(alpha)
    progress_rect = progress_surface.get_rect(center=(screen_width // 2, screen_height - 100))
    screen.blit(progress_surface, progress_rect)

    # 장식 라인
    line_width = 300
    line_y = screen_height // 4 + 160
    pygame.draw.line(screen, (*stage_info["color"], min(alpha, 150)),
                     (screen_width // 2 - line_width // 2, line_y),
                     (screen_width // 2 + line_width // 2, line_y), 2)
