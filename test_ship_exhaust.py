"""
함선별 배기가스 효과 테스트 프로그램
1-5 숫자키로 함선 변경, 방향키로 이동하여 배기가스 확인
배기가스를 더 잘 보기 위해 이동 속도를 증가시켰습니다.
"""
import pygame
import sys
from pathlib import Path

# Pygame 초기화
pygame.init()

# 화면 설정
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("함선별 배기가스 테스트 - 1-5: 함선 변경, 방향키: 이동, ESC: 종료")

# 색상
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)

# config 및 entities 모듈 임포트
import config
from entities.player import Player

# 폰트
font = pygame.font.Font(None, 36)
small_font = pygame.font.Font(None, 24)

# 함선 타입 리스트
SHIP_TYPES = ["FIGHTER", "INTERCEPTOR", "BOMBER", "STEALTH", "TITAN"]
current_ship_index = 0

# 초기 플레이어 생성
upgrades = {}
player_pos = pygame.math.Vector2(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
player = Player(
    pos=player_pos,
    screen_height=SCREEN_HEIGHT,
    upgrades=upgrades,
    ship_type=SHIP_TYPES[current_ship_index]
)

# 우주선 이미지를 직접 확대
DISPLAY_SCALE = 3.5  # 우주선 크기 배율
original_image = player.image.copy()
new_width = int(player.image.get_width() * DISPLAY_SCALE)
new_height = int(player.image.get_height() * DISPLAY_SCALE)
player.image = pygame.transform.smoothscale(original_image, (new_width, new_height))
player.original_image = player.image.copy()
player.image_rect = player.image.get_rect(center=(player.pos.x, player.pos.y))

# 배기가스를 더 잘 보기 위해 속도 증가
player.speed = 600  # 기본 300에서 600으로 증가

clock = pygame.time.Clock()

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
            # 숫자키로 함선 변경
            elif event.key == pygame.K_1:
                current_ship_index = 0
                player = Player(pos=player_pos, screen_height=SCREEN_HEIGHT, upgrades=upgrades, ship_type=SHIP_TYPES[current_ship_index])
                original_image = player.image.copy()
                new_width = int(player.image.get_width() * DISPLAY_SCALE)
                new_height = int(player.image.get_height() * DISPLAY_SCALE)
                player.image = pygame.transform.smoothscale(original_image, (new_width, new_height))
                player.original_image = player.image.copy()
                player.image_rect = player.image.get_rect(center=(player.pos.x, player.pos.y))
                player.speed = 600
            elif event.key == pygame.K_2:
                current_ship_index = 1
                player = Player(pos=player_pos, screen_height=SCREEN_HEIGHT, upgrades=upgrades, ship_type=SHIP_TYPES[current_ship_index])
                original_image = player.image.copy()
                new_width = int(player.image.get_width() * DISPLAY_SCALE)
                new_height = int(player.image.get_height() * DISPLAY_SCALE)
                player.image = pygame.transform.smoothscale(original_image, (new_width, new_height))
                player.original_image = player.image.copy()
                player.image_rect = player.image.get_rect(center=(player.pos.x, player.pos.y))
                player.speed = 600
            elif event.key == pygame.K_3:
                current_ship_index = 2
                player = Player(pos=player_pos, screen_height=SCREEN_HEIGHT, upgrades=upgrades, ship_type=SHIP_TYPES[current_ship_index])
                original_image = player.image.copy()
                new_width = int(player.image.get_width() * DISPLAY_SCALE)
                new_height = int(player.image.get_height() * DISPLAY_SCALE)
                player.image = pygame.transform.smoothscale(original_image, (new_width, new_height))
                player.original_image = player.image.copy()
                player.image_rect = player.image.get_rect(center=(player.pos.x, player.pos.y))
                player.speed = 600
            elif event.key == pygame.K_4:
                current_ship_index = 3
                player = Player(pos=player_pos, screen_height=SCREEN_HEIGHT, upgrades=upgrades, ship_type=SHIP_TYPES[current_ship_index])
                original_image = player.image.copy()
                new_width = int(player.image.get_width() * DISPLAY_SCALE)
                new_height = int(player.image.get_height() * DISPLAY_SCALE)
                player.image = pygame.transform.smoothscale(original_image, (new_width, new_height))
                player.original_image = player.image.copy()
                player.image_rect = player.image.get_rect(center=(player.pos.x, player.pos.y))
                player.speed = 600
            elif event.key == pygame.K_5:
                current_ship_index = 4
                player = Player(pos=player_pos, screen_height=SCREEN_HEIGHT, upgrades=upgrades, ship_type=SHIP_TYPES[current_ship_index])
                original_image = player.image.copy()
                new_width = int(player.image.get_width() * DISPLAY_SCALE)
                new_height = int(player.image.get_height() * DISPLAY_SCALE)
                player.image = pygame.transform.smoothscale(original_image, (new_width, new_height))
                player.original_image = player.image.copy()
                player.image_rect = player.image.get_rect(center=(player.pos.x, player.pos.y))
                player.speed = 600

    # 입력 처리
    keys = pygame.key.get_pressed()

    # 플레이어 이동
    player.move(keys, dt, (SCREEN_WIDTH, SCREEN_HEIGHT), pygame.time.get_ticks() / 1000.0)

    # 플레이어 업데이트
    player.update(dt, (SCREEN_WIDTH, SCREEN_HEIGHT), pygame.time.get_ticks() / 1000.0)
    player.update_movement_effects(dt)

    # 그리기
    screen.fill(BLACK)

    # 플레이어 그리기 (배기가스 포함)
    player.draw(screen)

    # UI 그리기
    ship_name = SHIP_TYPES[current_ship_index]
    ship_data = config.SHIP_TYPES[ship_name]
    exhaust_type = ship_data.get("exhaust_effect", "N/A")

    y_offset = 10

    # 함선 목록
    for i, ship in enumerate(SHIP_TYPES):
        color = GREEN if i == current_ship_index else WHITE
        text = f"{i+1}. {ship}"
        if i == current_ship_index:
            text += f" ← 현재 선택 (배기가스: {exhaust_type})"

        rendered = small_font.render(text, True, color)
        screen.blit(rendered, (10, y_offset))
        y_offset += 30

    # 현재 속도 및 배기가스 상태 표시
    y_offset += 10
    speed_magnitude = player.velocity.length()
    speed_ratio = speed_magnitude / player.speed if player.speed > 0 else 0

    status_texts = [
        f"우주선 크기: {DISPLAY_SCALE:.1f}배 확대",
        f"현재 속도: {speed_magnitude:.1f} / {player.speed:.1f}",
        f"속도 비율: {speed_ratio:.2f} (배기가스 표시: {'ON' if speed_ratio > 0.1 else 'OFF'})",
        "",
        "※ 배기가스를 보려면 방향키를 눌러 이동하세요!",
    ]

    for text in status_texts:
        color = GREEN if speed_ratio > 0.1 else YELLOW
        rendered = small_font.render(text, True, color)
        screen.blit(rendered, (10, y_offset))
        y_offset += 25

    # 안내 메시지
    y_offset = SCREEN_HEIGHT - 120
    info_texts = [
        "숫자 1-5: 함선 변경",
        "방향키: 우주선 이동 (계속 누르고 있기)",
        "ESC: 종료",
    ]

    for text in info_texts:
        rendered = small_font.render(text, True, YELLOW)
        screen.blit(rendered, (10, y_offset))
        y_offset += 30

    pygame.display.flip()

pygame.quit()
print(f"\n최종 선택된 함선: {SHIP_TYPES[current_ship_index]}")
sys.exit(0)
