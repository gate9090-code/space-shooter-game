"""
배기가스 위치 테스트 프로그램
상하좌우 이동 시 배기가스 위치를 여러 옵션으로 보여줌
"""
import pygame
import math
import sys
from pathlib import Path

# Pygame 초기화
pygame.init()

# 화면 설정
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("배기가스 위치 테스트 - 방향키로 이동, 1-6 숫자키로 옵션 선택, ESC 종료")

# 색상
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)

# 이미지 로드
ASSET_DIR = Path("assets")
player_img = pygame.image.load(str(ASSET_DIR / "images" / "gameplay" / "player" / "fighter_front.png")).convert_alpha()
player_img = pygame.transform.smoothscale(player_img, (80, 80))

gas_img = pygame.image.load(str(ASSET_DIR / "images" / "effects" / "gas_effect_01.png")).convert_alpha()

# 플레이어 위치
player_pos = pygame.math.Vector2(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
velocity = pygame.math.Vector2(0, 0)
speed = 300

# 배기가스 위치 옵션들
EXHAUST_OPTIONS = {
    1: {"name": "타원 0.5배 (가까움)", "multiplier": 0.5},
    2: {"name": "타원 0.8배 (약간 가까움)", "multiplier": 0.8},
    3: {"name": "타원 1.0배 (타원 경계)", "multiplier": 1.0},
    4: {"name": "타원 1.3배 (약간 멀리)", "multiplier": 1.3},
    5: {"name": "타원 1.5배 (멀리)", "multiplier": 1.5},
    6: {"name": "타원 1.8배 (아주 멀리)", "multiplier": 1.8},
}

current_option = 3  # 기본값

# 폰트
font = pygame.font.Font(None, 36)
small_font = pygame.font.Font(None, 24)

clock = pygame.time.Clock()

def draw_exhaust(screen, player_pos, player_rect, velocity, gas_img, multiplier):
    """배기가스 그리기"""
    if velocity.length() < 0.1:
        return

    direction = velocity.normalize()
    move_angle = math.atan2(direction.y, direction.x)

    # 타원 계산
    ellipse_a = player_rect.width * 0.25
    ellipse_b = player_rect.height * 0.15

    back_angle = move_angle + math.pi
    ellipse_x = ellipse_a * math.cos(back_angle)
    ellipse_y = ellipse_b * math.sin(back_angle)

    # 배기가스 위치
    exhaust_offset = pygame.math.Vector2(ellipse_x, ellipse_y) * multiplier
    exhaust_pos = player_pos + exhaust_offset

    # 배기가스 크기
    gas_width = int(player_rect.width * 0.6)
    gas_length = int(player_rect.height * 0.8)

    scaled_gas = pygame.transform.smoothscale(gas_img, (gas_width, gas_length))
    scaled_gas.set_alpha(180)

    # 좌우 이동 시 상하 반전
    angle_rad = math.atan2(direction.y, direction.x)
    is_horizontal = abs(abs(direction.x) - 1.0) < 0.3

    if is_horizontal:
        scaled_gas = pygame.transform.flip(scaled_gas, False, True)

    # 회전
    angle_deg = math.degrees(move_angle) - 90
    rotated_gas = pygame.transform.rotate(scaled_gas, angle_deg)

    # 그리기
    rect = rotated_gas.get_rect(center=(int(exhaust_pos.x), int(exhaust_pos.y)))
    screen.blit(rotated_gas, rect)

# 메인 루프
running = True
while running:
    dt = clock.tick(60) / 1000.0

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            # 숫자키로 옵션 선택
            elif event.key in [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5, pygame.K_6]:
                current_option = event.key - pygame.K_0

    # 입력 처리
    keys = pygame.key.get_pressed()
    velocity = pygame.math.Vector2(0, 0)

    if keys[pygame.K_LEFT]:
        velocity.x = -1
    if keys[pygame.K_RIGHT]:
        velocity.x = 1
    if keys[pygame.K_UP]:
        velocity.y = -1
    if keys[pygame.K_DOWN]:
        velocity.y = 1

    if velocity.length() > 0:
        velocity = velocity.normalize() * speed * dt
        player_pos += velocity

    # 화면 경계
    player_pos.x = max(50, min(SCREEN_WIDTH - 50, player_pos.x))
    player_pos.y = max(50, min(SCREEN_HEIGHT - 50, player_pos.y))

    # 그리기
    screen.fill(BLACK)

    # 배기가스 그리기
    player_rect = player_img.get_rect(center=(int(player_pos.x), int(player_pos.y)))
    draw_exhaust(screen, player_pos, player_rect, velocity, gas_img, EXHAUST_OPTIONS[current_option]["multiplier"])

    # 플레이어 그리기
    screen.blit(player_img, player_rect)

    # UI 그리기
    y_offset = 10
    for num, option in EXHAUST_OPTIONS.items():
        color = GREEN if num == current_option else WHITE
        text = f"{num}. {option['name']}"
        if num == current_option:
            text += " ← 현재 선택"

        rendered = small_font.render(text, True, color)
        screen.blit(rendered, (10, y_offset))
        y_offset += 30

    # 안내 메시지
    info_texts = [
        "방향키: 우주선 이동 (상하좌우)",
        "숫자 1-6: 배기가스 위치 옵션 선택",
        "ESC: 종료",
        "",
        f"현재 옵션: {current_option}번",
    ]

    y_offset = SCREEN_HEIGHT - 150
    for text in info_texts:
        rendered = small_font.render(text, True, YELLOW)
        screen.blit(rendered, (10, y_offset))
        y_offset += 30

    pygame.display.flip()

pygame.quit()
print(f"\n선택된 옵션: {current_option}번 - {EXHAUST_OPTIONS[current_option]['name']}")
print(f"multiplier 값: {EXHAUST_OPTIONS[current_option]['multiplier']}")
sys.exit(0)
