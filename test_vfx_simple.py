"""
간단한 VFX 테스트 - 디버깅용
"""
import pygame
import sys
from pathlib import Path

print("=== VFX Simple Test ===")

# Pygame 초기화
pygame.init()
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("VFX Simple Test")
clock = pygame.time.Clock()

print("1. Pygame initialized")

# VFXManager 임포트 및 초기화
try:
    from systems.vfx_manager import VFXManager
    vfx_manager = VFXManager()
    print("2. VFXManager created")
except Exception as e:
    print(f"ERROR creating VFXManager: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 사용 가능한 효과 출력
effects_list = vfx_manager.list_effects()
print(f"3. Available effects: {effects_list}")

# 효과 리스트
effects = []

# 테스트: 화면 중앙에 효과 생성
try:
    center = (400, 300)
    print(f"4. Creating shockwave at {center}...")

    # 단일 효과 테스트
    shockwave = vfx_manager.create_shockwave(
        center=center,
        category="hit_effects",
        variant="normal"
    )

    if shockwave:
        print(f"   - Shockwave created: {shockwave}")
        print(f"   - Image: {shockwave.image}")
        print(f"   - Max size: {shockwave.max_size}")
        print(f"   - Duration: {shockwave.duration}")
        effects.append(shockwave)
    else:
        print("   - ERROR: shockwave is None!")

except Exception as e:
    print(f"ERROR creating shockwave: {e}")
    import traceback
    traceback.print_exc()

print(f"5. Total effects created: {len(effects)}")

# 메인 루프
running = True
frame = 0

print("6. Starting main loop...")

while running and frame < 100:  # 100 프레임만 실행
    dt = clock.tick(60) / 1000.0
    frame += 1

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # 배경 (검정)
    screen.fill((0, 0, 0))

    # 효과 업데이트
    for effect in effects[:]:
        effect.update(dt)
        if not effect.is_alive:
            effects.remove(effect)
            print(f"Frame {frame}: Effect died")

    # 효과 그리기
    for effect in effects:
        if frame % 10 == 0:  # 10프레임마다 출력
            print(f"Frame {frame}: Drawing effect at age={effect.age:.2f}, is_alive={effect.is_alive}")
        effect.draw(screen)

    # 십자선 표시 (중앙)
    pygame.draw.line(screen, (255, 0, 0), (390, 300), (410, 300), 2)
    pygame.draw.line(screen, (255, 0, 0), (400, 290), (400, 310), 2)

    # 정보 표시
    font = pygame.font.Font(None, 24)
    text = font.render(f"Frame: {frame} | Effects: {len(effects)}", True, (255, 255, 255))
    screen.blit(text, (10, 10))

    pygame.display.flip()

pygame.quit()
print(f"7. Test completed. Ran {frame} frames.")
