# ui_render/combat_ui.py
# Combat-related UI rendering functions (boss health bars, random events, stage transitions)

import pygame
from pathlib import Path
from typing import Tuple, Dict, Optional
import config
from .helpers import get_font, render_text_with_emoji


# Boss bar image cache
_boss_bar_image_cache: Dict[str, pygame.Surface] = {}


def _load_enemy_bar_image(bar_width: int, bar_height: int) -> Optional[pygame.Surface]:
    """적 HP 바 이미지 로드 (캐시 사용)"""
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
    name_font = get_font("large")
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
    hp_text_font = get_font("small")
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
        notification_font = get_font("huge")
        small_font = get_font("medium")

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
    event_font = get_font("small")
    event_text = f"{event_data['icon']} {event_data['name']}"
    event_surf = event_font.render(event_text, True, (255, 255, 255))
    event_rect = event_surf.get_rect(center=(bar_x + bar_width // 2, bar_y + bar_height // 2))
    screen.blit(event_surf, event_rect)

    # 남은 시간 표시 (우측)
    time_font = get_font("tiny")
    time_text = f"{int(remaining_time)}s"
    time_surf = time_font.render(time_text, True, (200, 200, 200))
    time_rect = time_surf.get_rect(midleft=(bar_x + bar_width + 10, bar_y + bar_height // 2))
    screen.blit(time_surf, time_rect)


# =========================================================
# 스테이지 전환 화면
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
