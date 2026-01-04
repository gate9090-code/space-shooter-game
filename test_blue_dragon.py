"""
Blue Dragon 이미지 움직임 테스트
- 좌우 이동 시 머리가 이동 방향을 향하도록 회전
- ESC: 종료
"""

import pygame
import math
import sys
from pathlib import Path

# 초기화
pygame.init()

# 화면 설정
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Blue Dragon Movement Test")
clock = pygame.time.Clock()

# 색상
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BLUE = (100, 150, 255)

# Blue Dragon 클래스
class BlueDragon:
    def __init__(self, x, y):
        # 이미지 로드
        img_path = Path("wave_blue-dragon.png")
        if not img_path.exists():
            print(f"ERROR: {img_path} not found!")
            sys.exit(1)

        # 원본 이미지 로드 (머리가 위쪽 중앙)
        self.original_image = pygame.image.load(str(img_path)).convert_alpha()

        # 크기 조정 (화면 높이의 25%)
        original_height = self.original_image.get_height()
        original_width = self.original_image.get_width()
        target_height = int(SCREEN_HEIGHT * 0.25)
        aspect_ratio = original_width / original_height
        target_width = int(target_height * aspect_ratio)

        self.original_image = pygame.transform.smoothscale(
            self.original_image, (target_width, target_height)
        )

        print(f"INFO: Loaded blue dragon image: {target_width}x{target_height}")

        # 위치
        self.x = x
        self.y = y

        # 이동
        self.speed = 200  # 픽셀/초
        self.velocity_x = self.speed
        self.velocity_y = 0

        # 현재 각도 (0도 = 위쪽, 90도 = 오른쪽, 180도 = 아래쪽, 270도 = 왼쪽)
        self.angle = 0
        self.image = self.original_image
        self.rect = self.image.get_rect(center=(self.x, self.y))

    def update(self, dt):
        # 위치 업데이트
        self.x += self.velocity_x * dt
        self.y += self.velocity_y * dt

        # 화면 경계에서 반사
        if self.x < 100 or self.x > SCREEN_WIDTH - 100:
            self.velocity_x = -self.velocity_x
        if self.y < 100 or self.y > SCREEN_HEIGHT - 100:
            self.velocity_y = -self.velocity_y

        # 이동 방향 계산 (각도)
        if self.velocity_x != 0 or self.velocity_y != 0:
            # atan2로 각도 계산 (라디안 -> 도)
            angle_rad = math.atan2(self.velocity_y, self.velocity_x)
            # 이미지 머리가 위쪽(0도)을 향하므로, 90도를 더해서 조정
            self.angle = math.degrees(angle_rad) + 90

        # 이미지 회전 (반시계방향)
        self.image = pygame.transform.rotate(self.original_image, -self.angle)
        self.rect = self.image.get_rect(center=(int(self.x), int(self.y)))

    def draw(self, screen):
        screen.blit(self.image, self.rect)

        # 디버그: 이동 벡터 표시
        end_x = int(self.x + self.velocity_x * 0.3)
        end_y = int(self.y + self.velocity_y * 0.3)
        pygame.draw.line(screen, BLUE, (int(self.x), int(self.y)), (end_x, end_y), 3)
        pygame.draw.circle(screen, WHITE, (end_x, end_y), 5)


# Blue Dragon 생성
dragons = [
    BlueDragon(SCREEN_WIDTH // 4, SCREEN_HEIGHT // 3),
    BlueDragon(SCREEN_WIDTH * 3 // 4, SCREEN_HEIGHT * 2 // 3),
]

# 두 번째 드래곤은 대각선으로 이동
dragons[1].velocity_x = 150
dragons[1].velocity_y = 100

# 폰트
font = pygame.font.Font(None, 36)
small_font = pygame.font.Font(None, 24)

# 메인 루프
running = True
while running:
    dt = clock.tick(60) / 1000.0  # 초 단위

    # 이벤트 처리
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            elif event.key == pygame.K_SPACE:
                # 스페이스바: 방향 변경
                for dragon in dragons:
                    dragon.velocity_x = -dragon.velocity_x
                    dragon.velocity_y = -dragon.velocity_y

    # 업데이트
    for dragon in dragons:
        dragon.update(dt)

    # 그리기
    screen.fill(BLACK)

    # 드래곤 그리기
    for dragon in dragons:
        dragon.draw(screen)

    # 안내문
    title = font.render("Blue Dragon Movement Test", True, WHITE)
    screen.blit(title, (20, 20))

    instruction1 = small_font.render("ESC: Exit  |  SPACE: Reverse Direction", True, BLUE)
    screen.blit(instruction1, (20, 60))

    instruction2 = small_font.render("Blue line = movement direction", True, BLUE)
    screen.blit(instruction2, (20, 90))

    # FPS 표시
    fps_text = small_font.render(f"FPS: {int(clock.get_fps())}", True, WHITE)
    screen.blit(fps_text, (SCREEN_WIDTH - 120, 20))

    pygame.display.flip()

pygame.quit()
print("INFO: Test completed")
