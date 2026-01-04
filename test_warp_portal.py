"""
워프 포탈 효과 테스트

마우스 클릭으로 포탈 생성
1-4 키로 색상 변경
우주선이 포탈에 빨려들어가는 효과
"""

import pygame
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from effects.physics_effects import WarpPortal, DepthEffect

# Pygame 초기화
pygame.init()
screen = pygame.display.set_mode((1200, 800))
pygame.display.set_caption("Warp Portal Test - Click to create portal")
clock = pygame.time.Clock()
font = pygame.font.Font(None, 24)
title_font = pygame.font.Font(None, 36)

# 워프 포탈 리스트
portals = []

# 우주선 이미지 (임시)
try:
    ship_image = pygame.image.load("assets/images/gameplay/player/fighter_front.png").convert_alpha()
    ship_image = pygame.transform.scale(ship_image, (64, 64))
except:
    # 폴백: 간단한 삼각형
    ship_image = pygame.Surface((64, 64), pygame.SRCALPHA)
    pygame.draw.polygon(ship_image, (100, 150, 255), [(32, 10), (10, 54), (54, 54)])
    pygame.draw.polygon(ship_image, (150, 200, 255), [(32, 10), (20, 50), (44, 50)])

# 우주선 상태
ship_pos = [600, 700]
ship_velocity = [0, 0]
being_pulled = False

# 현재 색상
current_color = "blue"
color_names = ["blue", "red", "green", "yellow"]

print("\n=== Warp Portal Test ===")
print("Controls:")
print("  Click - Create portal at mouse position")
print("  1-4 - Change portal color (Blue, Red, Green, Yellow)")
print("  W - Create portal with ship warp effect")
print("  C - Clear all portals")
print("  Space - Toggle ship pull effect")

running = True
frame = 0

while running:
    dt = clock.tick(60) / 1000.0
    frame += 1

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.MOUSEBUTTONDOWN:
            # 마우스 클릭 위치에 포탈 생성
            pos = event.pos

            portal = WarpPortal(
                center=pos,
                max_radius=150,
                particle_count=60,
                ring_count=3,
                duration=10.0,  # 10초 유지
                color_scheme=current_color
            )

            portals.append(portal)
            print(f"Portal created at {pos} with color={current_color}")

        elif event.type == pygame.KEYDOWN:
            # 색상 변경
            if pygame.K_1 <= event.key <= pygame.K_4:
                color_index = event.key - pygame.K_1
                current_color = color_names[color_index]
                print(f"Color changed to: {current_color}")

            # 우주선 워프 효과
            elif event.key == pygame.K_w:
                # 화면 중앙에 포탈 생성
                portal = WarpPortal(
                    center=(600, 400),
                    max_radius=200,
                    particle_count=80,
                    ring_count=4,
                    duration=5.0,
                    color_scheme=current_color
                )
                portals.append(portal)

                # 우주선을 포탈로 이동
                being_pulled = True
                print("Warp sequence initiated!")

            # 포탈 클리어
            elif event.key == pygame.K_c:
                portals.clear()
                being_pulled = False
                ship_pos = [600, 700]
                ship_velocity = [0, 0]
                print("All portals cleared")

            # 끌어당기기 토글
            elif event.key == pygame.K_SPACE:
                being_pulled = not being_pulled
                print(f"Ship pull: {'ON' if being_pulled else 'OFF'}")

    # 배경 (우주)
    screen.fill((5, 5, 20))

    # 별 배경
    for i in range(100):
        x = (i * 123) % 1200
        y = (i * 456) % 800
        size = (i % 3) + 1
        brightness = 100 + (i % 155)
        pygame.draw.circle(screen, (brightness, brightness, brightness), (x, y), size)

    # 포탈 업데이트 및 그리기
    for portal in portals[:]:
        portal.update(dt)

        if not portal.is_alive:
            portals.remove(portal)
            print("Portal closed")
        else:
            portal.draw(screen)

            # 우주선을 가장 가까운 포탈로 끌어당김
            if being_pulled and portals:
                # 가장 가까운 포탈 찾기
                closest_portal = min(portals, key=lambda p:
                    ((p.center.x - ship_pos[0])**2 + (p.center.y - ship_pos[1])**2)**0.5
                )

                # 끌어당기기
                new_pos = closest_portal.pull_object(tuple(ship_pos), dt, pull_strength=300)
                ship_pos[0] = new_pos[0]
                ship_pos[1] = new_pos[1]

                # 포탈 중심에 도달하면 사라짐 효과
                distance = ((closest_portal.center.x - ship_pos[0])**2 +
                           (closest_portal.center.y - ship_pos[1])**2)**0.5

                if distance < 30:
                    print("Ship entered portal!")
                    being_pulled = False
                    # 우주선을 다시 아래로
                    ship_pos = [600, 750]

    # 우주선 그리기
    ship_rect = ship_image.get_rect(center=(int(ship_pos[0]), int(ship_pos[1])))
    screen.blit(ship_image, ship_rect)

    # UI
    title_text = title_font.render("Warp Portal Test", True, (255, 255, 255))
    screen.blit(title_text, (10, 10))

    # 현재 색상
    color_text = font.render(f"Current Color: {current_color.upper()}", True, (255, 200, 100))
    screen.blit(color_text, (10, 60))

    # 통계
    stats_text = font.render(f"Portals: {len(portals)} | Ship Pull: {'ON' if being_pulled else 'OFF'}", True, (200, 200, 200))
    screen.blit(stats_text, (10, 90))

    # 도움말
    help_texts = [
        "Controls:",
        "  Click - Create portal",
        "  1-4 - Color (Blue/Red/Green/Yellow)",
        "  W - Create portal + warp ship",
        "  Space - Toggle ship pull",
        "  C - Clear all"
    ]

    help_y = 140
    for text in help_texts:
        color = (255, 255, 255) if text.startswith("  ") else (200, 200, 255)
        help_surf = font.render(text, True, color)
        screen.blit(help_surf, (10, help_y))
        help_y += 25

    # 커서
    mouse_pos = pygame.mouse.get_pos()
    pygame.draw.circle(screen, (100, 255, 100), mouse_pos, 5, 1)
    pygame.draw.line(screen, (100, 255, 100), (mouse_pos[0] - 10, mouse_pos[1]), (mouse_pos[0] + 10, mouse_pos[1]), 1)
    pygame.draw.line(screen, (100, 255, 100), (mouse_pos[0], mouse_pos[1] - 10), (mouse_pos[0], mouse_pos[1] + 10), 1)

    pygame.display.flip()

pygame.quit()
print("Test completed")
