"""
ImageShockwave 렌더링 테스트
"""
import pygame
import sys
from pathlib import Path

# Pygame 초기화
pygame.init()
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("Ring Effect Test")
clock = pygame.time.Clock()

# ImageShockwave 임포트
sys.path.insert(0, str(Path(__file__).parent))
from effects.screen_effects import ImageShockwave

# 효과 리스트
effects = []

# 메인 루프
running = True
frame = 0
while running:
    dt = clock.tick(60) / 1000.0
    frame += 1

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            # 클릭 위치에 링 효과 생성
            pos = event.pos
            ring = ImageShockwave(
                center=pos,
                max_size=240,  # 120 * 2
                duration=0.8,
                delay=0.0,
                color_tint=(255, 255, 255)
            )
            effects.append(ring)
            print(f"Ring effect created at {pos}, total effects: {len(effects)}")

    # 배경 그리기
    screen.fill((0, 0, 0))

    # 효과 업데이트
    for effect in effects[:]:
        effect.update(dt)
        if not effect.is_alive:
            effects.remove(effect)

    # 효과 그리기
    for effect in effects:
        effect.draw(screen)

    # 정보 표시
    font = pygame.font.Font(None, 24)
    info_text = f"Frame: {frame} | Effects: {len(effects)} | Click to create ring"
    text_surf = font.render(info_text, True, (255, 255, 255))
    screen.blit(text_surf, (10, 10))

    # 이미지 캐시 상태 표시
    cache_status = "Loaded" if ImageShockwave._image_cache is not None else "NOT LOADED"
    cache_text = f"Image Cache: {cache_status}"
    cache_surf = font.render(cache_text, True, (0, 255, 0) if ImageShockwave._image_cache else (255, 0, 0))
    screen.blit(cache_surf, (10, 40))

    if ImageShockwave._image_cache:
        size_text = f"Image Size: {ImageShockwave._image_cache.get_size()}"
        size_surf = font.render(size_text, True, (0, 255, 0))
        screen.blit(size_surf, (10, 70))

    pygame.display.flip()

pygame.quit()
print("Test completed.")
