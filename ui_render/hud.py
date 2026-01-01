# ui_render/hud.py
# HUD (Head-Up Display) rendering functions

import pygame
import math
from typing import Tuple, TYPE_CHECKING
import config
from game_logic import get_next_level_threshold
from .helpers import get_font, render_text_with_emoji

if TYPE_CHECKING:
    from entities.player import Player


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
    icon_font = get_font("icon")
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
        ability_font = get_font("large")
        ability_icon_text = ability_font.render("E", True, config.WHITE)
        ability_icon_rect = ability_icon_text.get_rect(center=(ability_indicator_x, ability_indicator_y - 5))
        screen.blit(ability_icon_text, ability_icon_rect)

        # 능력 이름 (아이콘 아래)
        ability_name_font = get_font("tiny")
        ability_name = ability_info.get('name', 'Ability')[:8]  # 최대 8글자
        ability_name_text = ability_name_font.render(ability_name, True, config.WHITE)
        ability_name_rect = ability_name_text.get_rect(center=(ability_indicator_x, ability_indicator_y + ability_radius + 12))
        screen.blit(ability_name_text, ability_name_rect)

        # 쿨다운 시간 표시 (쿨다운 중일 때만)
        if not ability_ready and ability_remaining > 0:
            cooldown_font = get_font("small")
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
            reincarnation_font = get_font("large")
            reincarnation_icon = render_text_with_emoji(
                config.UI_ICONS["REINCARNATION"],
                reincarnation_font,
                config.UI_COLORS["DANGER"],
                "MEDIUM"
            )
            icon_rect = reincarnation_icon.get_rect(center=(icon_x + icon_size // 2, icon_y + icon_size // 2))
            screen.blit(reincarnation_icon, icon_rect)


def draw_skill_indicators(
    screen: pygame.Surface,
    screen_size: Tuple[int, int],
    player: "Player",
    current_time: float
):
    """하단에 모든 스킬들을 네모 박스로 표시합니다 (쿨다운과 동일 높이)"""
    SCREEN_WIDTH, SCREEN_HEIGHT = screen_size
    settings = config.SKILL_INDICATOR_SETTINGS

    box_size = settings["box_size"]
    icon_spacing = settings["icon_spacing"]
    base_y = SCREEN_HEIGHT - settings["base_y"]

    # 이모지 폰트 가져오기
    emoji_font = config.EMOJI_FONTS.get("MEDIUM")
    text_font = get_font("micro")
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
    name_font = get_font("micro")
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
