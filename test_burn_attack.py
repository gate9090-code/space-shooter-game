"""
Boss BURN_ATTACK Pattern Test
- Boss fires 8-directional blue energy projectiles every 5 seconds
- Projectiles travel in all directions
- SPACE: Manual trigger
- ESC: Exit
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
pygame.display.set_caption("Boss BURN_ATTACK Pattern Test")
clock = pygame.time.Clock()

# 색상
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 50, 50)
BLUE = (100, 150, 255)
CYAN = (0, 255, 255)

# BURN_ATTACK 설정 (config/entities.py에서 가져온 값)
BURN_ATTACK_SETTINGS = {
    "projectile_count": 8,       # 8방향
    "fire_interval": 5.0,        # 5초마다 자동 발사
    "projectile_speed": 200.0,   # 픽셀/초
    "damage": 15.0,
    "projectile_size": 40,       # 크기
    "lifetime": 5.0,             # 5초 수명
}

# BurnProjectile 클래스
class BurnProjectile:
    def __init__(self, x, y, direction):
        self.x = x
        self.y = y
        self.direction = direction  # Vector2
        self.speed = BURN_ATTACK_SETTINGS["projectile_speed"]
        self.size = BURN_ATTACK_SETTINGS["projectile_size"]
        self.lifetime = BURN_ATTACK_SETTINGS["lifetime"]
        self.age = 0.0
        self.is_alive = True

        # 색상 (파란색 에너지)
        self.color = BLUE

    def update(self, dt):
        # 위치 업데이트
        self.x += self.direction.x * self.speed * dt
        self.y += self.direction.y * self.speed * dt

        # 나이 증가
        self.age += dt

        # 수명 체크
        if self.age >= self.lifetime:
            self.is_alive = False

        # 화면 밖으로 나가면 제거
        if self.x < -100 or self.x > SCREEN_WIDTH + 100:
            self.is_alive = False
        if self.y < -100 or self.y > SCREEN_HEIGHT + 100:
            self.is_alive = False

    def draw(self, screen):
        # 원형 발사체 그리기 (외곽선 + 내부)
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.size // 2)
        pygame.draw.circle(screen, CYAN, (int(self.x), int(self.y)), self.size // 2 - 5, 3)

        # 중심점
        pygame.draw.circle(screen, WHITE, (int(self.x), int(self.y)), 5)


# Boss 클래스 (간단 버전)
class SimpleBoss:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.size = 120
        self.color = RED

        # BURN_ATTACK 관련
        self.burn_projectiles = []
        self.last_burn_attack_time = 0.0

    def fire_burn_projectiles(self, current_time):
        """8방향으로 burn 발사체 발사"""
        projectile_count = BURN_ATTACK_SETTINGS["projectile_count"]

        # 8방향으로 균등하게 발사
        for i in range(projectile_count):
            angle = (2 * math.pi / projectile_count) * i
            direction_x = math.cos(angle)
            direction_y = math.sin(angle)
            direction = pygame.math.Vector2(direction_x, direction_y).normalize()

            projectile = BurnProjectile(self.x, self.y, direction)
            self.burn_projectiles.append(projectile)

        self.last_burn_attack_time = current_time
        print(f"INFO: Fired {projectile_count} burn projectiles")

    def update(self, dt, current_time):
        # 자동 발사 (5초마다)
        if current_time - self.last_burn_attack_time >= BURN_ATTACK_SETTINGS["fire_interval"]:
            self.fire_burn_projectiles(current_time)

        # 발사체 업데이트
        for projectile in self.burn_projectiles:
            projectile.update(dt)

        # 죽은 발사체 제거
        self.burn_projectiles = [p for p in self.burn_projectiles if p.is_alive]

    def draw(self, screen):
        # 보스 그리기 (빨간 원)
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.size)
        pygame.draw.circle(screen, WHITE, (int(self.x), int(self.y)), self.size, 5)

        # 중심 표시
        pygame.draw.circle(screen, WHITE, (int(self.x), int(self.y)), 8)

        # 발사체 그리기
        for projectile in self.burn_projectiles:
            projectile.draw(screen)


# Boss 생성
boss = SimpleBoss(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)

# 폰트
font = pygame.font.Font(None, 36)
small_font = pygame.font.Font(None, 24)

# 게임 시작 시간
start_time = pygame.time.get_ticks() / 1000.0

# 메인 루프
running = True
while running:
    dt = clock.tick(60) / 1000.0  # 초 단위
    current_time = pygame.time.get_ticks() / 1000.0 - start_time

    # 이벤트 처리
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            elif event.key == pygame.K_SPACE:
                # 스페이스바: 수동 발사
                boss.fire_burn_projectiles(current_time)

    # 업데이트
    boss.update(dt, current_time)

    # 그리기
    screen.fill(BLACK)

    # 안내선 (중심 십자선)
    pygame.draw.line(screen, (50, 50, 50), (SCREEN_WIDTH // 2, 0), (SCREEN_WIDTH // 2, SCREEN_HEIGHT), 1)
    pygame.draw.line(screen, (50, 50, 50), (0, SCREEN_HEIGHT // 2), (SCREEN_WIDTH, SCREEN_HEIGHT // 2), 1)

    # Boss 그리기
    boss.draw(screen)

    # UI 안내문
    title = font.render("Boss BURN_ATTACK Pattern Test", True, WHITE)
    screen.blit(title, (20, 20))

    instruction1 = small_font.render("ESC: Exit  |  SPACE: Manual Fire", True, CYAN)
    screen.blit(instruction1, (20, 60))

    instruction2 = small_font.render("Boss fires 8-directional blue projectiles every 5 seconds", True, BLUE)
    screen.blit(instruction2, (20, 90))

    # 발사 쿨다운 표시
    time_until_next = BURN_ATTACK_SETTINGS["fire_interval"] - (current_time - boss.last_burn_attack_time)
    if time_until_next > 0:
        cooldown_text = small_font.render(f"Next auto-fire in: {time_until_next:.1f}s", True, RED)
    else:
        cooldown_text = small_font.render("Auto-fire ready!", True, (0, 255, 0))
    screen.blit(cooldown_text, (20, 120))

    # 발사체 수 표시
    projectile_count_text = small_font.render(f"Active projectiles: {len(boss.burn_projectiles)}", True, WHITE)
    screen.blit(projectile_count_text, (20, 150))

    # FPS 표시
    fps_text = small_font.render(f"FPS: {int(clock.get_fps())}", True, WHITE)
    screen.blit(fps_text, (SCREEN_WIDTH - 120, 20))

    # 패턴 설명
    pattern_title = small_font.render("BURN_ATTACK Pattern:", True, WHITE)
    screen.blit(pattern_title, (SCREEN_WIDTH - 400, 60))

    pattern_info = [
        f"Projectile count: {BURN_ATTACK_SETTINGS['projectile_count']}",
        f"Fire interval: {BURN_ATTACK_SETTINGS['fire_interval']}s",
        f"Speed: {BURN_ATTACK_SETTINGS['projectile_speed']} px/s",
        f"Lifetime: {BURN_ATTACK_SETTINGS['lifetime']}s",
        f"Damage: {BURN_ATTACK_SETTINGS['damage']}",
    ]

    for i, info in enumerate(pattern_info):
        info_text = small_font.render(info, True, BLUE)
        screen.blit(info_text, (SCREEN_WIDTH - 400, 90 + i * 25))

    pygame.display.flip()

pygame.quit()
print("INFO: Test completed")
