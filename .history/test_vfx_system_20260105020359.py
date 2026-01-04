"""
VFX System 테스트 스크립트

이미지만 교체해서 다양한 효과를 만드는 시스템 테스트
마우스 클릭으로 다양한 효과 생성
"""

import pygame
import sys
from pathlib import Path

# 경로 설정
sys.path.insert(0, str(Path(__file__).parent))

from systems.vfx_manager import VFXManager

# Pygame 초기화
pygame.init()
screen = pygame.display.set_mode((1200, 800))
pygame.display.set_caption("VFX System Test - Click to create effects")
clock = pygame.time.Clock()
font = pygame.font.Font(None, 24)
title_font = pygame.font.Font(None, 36)

# VFXManager 초기화
vfx_manager = VFXManager()

# 효과 리스트
effects = []

# 현재 선택된 효과
current_category = "hit_effects"
current_variant = "normal"
effect_index = 0

# 사용 가능한 효과 목록
available_effects = vfx_manager.list_effects()
all_effects_list = []
for category, variants in available_effects.items():
    for variant in variants:
        all_effects_list.append((category, variant))

print("\n=== VFX System Test ===")
print(f"Total effects available: {len(all_effects_list)}")
for i, (cat, var) in enumerate(all_effects_list):
    print(f"  {i+1}. {cat}/{var}")

# 메인 루프
running = True
show_help = True
frame = 0

while running:
    dt = clock.tick(60) / 1000.0
    frame += 1

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.MOUSEBUTTONDOWN:
            # 클릭 위치에 현재 선택된 효과 생성
            pos = event.pos

            # 다중 파동 효과 생성
            new_effects = vfx_manager.create_multi_shockwave(
                center=pos,
                category=current_category,
                variant=current_variant
            )

            effects.extend(new_effects)
            print(f"Created {len(new_effects)} waves at {pos}: {current_category}/{current_variant}")

        elif event.type == pygame.KEYDOWN:
            # 숫자 키로 효과 선택
            if pygame.K_1 <= event.key <= pygame.K_9:
                effect_index = event.key - pygame.K_1
                if effect_index < len(all_effects_list):
                    current_category, current_variant = all_effects_list[effect_index]
                    print(f"Selected effect: {current_category}/{current_variant}")

            # 화살표 키로 효과 순환
            elif event.key == pygame.K_RIGHT:
                effect_index = (effect_index + 1) % len(all_effects_list)
                current_category, current_variant = all_effects_list[effect_index]
                print(f"Selected effect: {current_category}/{current_variant}")

            elif event.key == pygame.K_LEFT:
                effect_index = (effect_index - 1) % len(all_effects_list)
                current_category, current_variant = all_effects_list[effect_index]
                print(f"Selected effect: {current_category}/{current_variant}")

            # H 키로 도움말 토글
            elif event.key == pygame.K_h:
                show_help = not show_help

            # R 키로 설정 리로드
            elif event.key == pygame.K_r:
                vfx_manager.reload_config()
                available_effects = vfx_manager.list_effects()
                all_effects_list = []
                for category, variants in available_effects.items():
                    for variant in variants:
                        all_effects_list.append((category, variant))
                print("Config reloaded!")

            # C 키로 효과 전부 클리어
            elif event.key == pygame.K_c:
                effects.clear()
                print("All effects cleared!")

    # 배경 그리기 (그라디언트)
    for y in range(screen.get_height()):
        color_val = int(20 + (y / screen.get_height()) * 30)
        pygame.draw.line(screen, (color_val, color_val, color_val * 1.2), (0, y), (screen.get_width(), y))

    # 효과 업데이트
    for effect in effects[:]:
        effect.update(dt)
        if not effect.is_alive:
            effects.remove(effect)

    # 효과 그리기
    for effect in effects:
        effect.draw(screen)

    # UI 그리기
    # 제목
    title_text = title_font.render("VFX System Test", True, (255, 255, 255))
    screen.blit(title_text, (10, 10))

    # 현재 선택된 효과
    current_text = font.render(f"Current Effect: {current_category} / {current_variant}", True, (100, 255, 100))
    screen.blit(current_text, (10, 60))

    # 통계
    stats_text = font.render(f"Active Effects: {len(effects)} | Frame: {frame}", True, (200, 200, 200))
    screen.blit(stats_text, (10, 90))

    # 도움말
    if show_help:
        help_y = 140
        help_texts = [
            "Controls:",
            "  Mouse Click - Create effect at cursor",
            "  1-9 - Select effect by number",
            "  Left/Right Arrow - Cycle effects",
            "  R - Reload config",
            "  C - Clear all effects",
            "  H - Toggle help",
            "",
            "Available Effects:"
        ]

        for i, (cat, var) in enumerate(all_effects_list):
            is_selected = (cat == current_category and var == current_variant)
            color = (255, 255, 100) if is_selected else (150, 150, 150)
            effect_text = f"  {i+1}. {cat}/{var}"
            if is_selected:
                effect_text += " <---"
            help_texts.append(effect_text)

        for text in help_texts:
            color = (255, 255, 255) if text.startswith("  ") or text == "" else (200, 200, 255)
            if "<---" in text:
                color = (255, 255, 100)
            help_surf = font.render(text, True, color)
            screen.blit(help_surf, (10, help_y))
            help_y += 25

    # 커서 위치에 크로스헤어 표시
    mouse_pos = pygame.mouse.get_pos()
    pygame.draw.circle(screen, (100, 255, 100), mouse_pos, 5, 1)
    pygame.draw.line(screen, (100, 255, 100), (mouse_pos[0] - 10, mouse_pos[1]), (mouse_pos[0] + 10, mouse_pos[1]), 1)
    pygame.draw.line(screen, (100, 255, 100), (mouse_pos[0], mouse_pos[1] - 10), (mouse_pos[0], mouse_pos[1] + 10), 1)

    pygame.display.flip()

pygame.quit()
print("Test completed.")
