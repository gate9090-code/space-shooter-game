"""
Advanced Effect System Demo - 확장된 이펙트 시스템 데모

이 파일은 새로운 이펙트 시스템의 사용법을 보여줍니다.

실행: python examples/effect_system_demo.py

조작:
- 마우스 클릭: 해당 위치에 이펙트 생성
- 1-9: 다양한 이펙트 선택
- Q/W/E/R: 복합 이펙트 선택
- SPACE: 모든 이펙트 제거
- H: 핫 리로드 (JSON 설정 다시 로드)
- ESC: 종료
"""

import sys
import os

# 프로젝트 루트를 path에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame
from systems.advanced_effect_system import get_advanced_effect_manager
from systems.effect_bridge import get_effect_bridge


def main():
    # Pygame 초기화
    pygame.init()
    screen = pygame.display.set_mode((1280, 720))
    pygame.display.set_caption("Advanced Effect System Demo")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 24)

    # 이펙트 시스템 초기화
    effect_manager = get_advanced_effect_manager()
    bridge = get_effect_bridge()

    # 선택된 이펙트
    current_effect = "hit_normal"
    current_composite = None

    # 이펙트 목록
    effects = [
        ("1", "hit_normal", "Normal Hit"),
        ("2", "hit_fire", "Fire Hit"),
        ("3", "hit_ice", "Ice Hit"),
        ("4", "hit_electric", "Electric Hit"),
        ("5", "hit_poison", "Poison Hit"),
        ("6", "critical_hit", "Critical Hit"),
        ("7", "boss_hit", "Boss Hit"),
        ("8", "skill_meteor_impact", "Meteor"),
        ("9", "skill_heal", "Heal"),
        ("0", "phoenix_ring", "Phoenix Ring"),
    ]

    composites = [
        ("Q", "explosion_full", "Full Explosion"),
        ("W", "boss_death_full", "Boss Death"),
        ("E", "critical_combo", "Critical Combo"),
        ("R", "meteor_full", "Meteor Full"),
    ]

    running = True
    while running:
        dt = clock.tick(60) / 1000.0

        # 이벤트 처리
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

                elif event.key == pygame.K_SPACE:
                    effect_manager.clear()
                    print("All effects cleared")

                elif event.key == pygame.K_h:
                    if effect_manager.hot_reload():
                        print("Config reloaded!")

                # 이펙트 선택
                for key, effect_name, _ in effects:
                    if event.unicode == key:
                        current_effect = effect_name
                        current_composite = None
                        print(f"Selected effect: {effect_name}")

                # 복합 이펙트 선택
                for key, composite_name, _ in composites:
                    if event.unicode.upper() == key:
                        current_composite = composite_name
                        current_effect = None
                        print(f"Selected composite: {composite_name}")

            elif event.type == pygame.MOUSEBUTTONDOWN:
                pos = event.pos

                if current_composite:
                    effect_manager.create_composite(current_composite, pos)
                    print(f"Created composite: {current_composite} at {pos}")
                elif current_effect:
                    effect_manager.create_effect(current_effect, pos)
                    print(f"Created effect: {current_effect} at {pos}")

        # 업데이트
        effect_manager.update(dt)

        # 렌더링
        screen.fill((20, 20, 30))

        # 격자 그리기 (시각적 참조용)
        for x in range(0, 1280, 100):
            pygame.draw.line(screen, (40, 40, 50), (x, 0), (x, 720))
        for y in range(0, 720, 100):
            pygame.draw.line(screen, (40, 40, 50), (0, y), (1280, y))

        # 이펙트 렌더링
        effect_manager.draw(screen)

        # UI 렌더링
        y_offset = 10

        # 제목
        title = font.render("Advanced Effect System Demo", True, (255, 255, 255))
        screen.blit(title, (10, y_offset))
        y_offset += 30

        # 현재 선택
        if current_composite:
            current_text = f"Current: {current_composite} (Composite)"
        else:
            current_text = f"Current: {current_effect}"
        current_surf = font.render(current_text, True, (255, 255, 100))
        screen.blit(current_surf, (10, y_offset))
        y_offset += 30

        # 이펙트 목록
        pygame.draw.line(screen, (100, 100, 100), (10, y_offset), (300, y_offset))
        y_offset += 10

        for key, effect_name, display_name in effects:
            color = (255, 255, 100) if effect_name == current_effect else (200, 200, 200)
            text = font.render(f"[{key}] {display_name}", True, color)
            screen.blit(text, (10, y_offset))
            y_offset += 22

        # 복합 이펙트 목록
        y_offset += 10
        pygame.draw.line(screen, (100, 100, 100), (10, y_offset), (300, y_offset))
        y_offset += 10

        for key, composite_name, display_name in composites:
            color = (255, 255, 100) if composite_name == current_composite else (200, 200, 200)
            text = font.render(f"[{key}] {display_name}", True, color)
            screen.blit(text, (10, y_offset))
            y_offset += 22

        # 조작 안내
        y_offset += 10
        pygame.draw.line(screen, (100, 100, 100), (10, y_offset), (300, y_offset))
        y_offset += 10

        instructions = [
            "Click: Create effect",
            "[SPACE] Clear all",
            "[H] Hot reload config",
            "[ESC] Exit",
        ]
        for instruction in instructions:
            text = font.render(instruction, True, (150, 150, 150))
            screen.blit(text, (10, y_offset))
            y_offset += 22

        # FPS
        fps_text = font.render(f"FPS: {int(clock.get_fps())}", True, (100, 100, 100))
        screen.blit(fps_text, (1200, 10))

        pygame.display.flip()

    pygame.quit()


def demo_bridge_usage():
    """
    EffectBridge 사용 예제

    기존 코드를 최소한으로 변경하면서 새 시스템 사용
    """
    print("\n=== EffectBridge Usage Demo ===\n")

    bridge = get_effect_bridge()

    # 1. 기존 API 스타일로 사용
    print("1. 기존 VFXManager 스타일:")
    print("   bridge.create_shockwave((400, 300), 'hit_effects', 'fire')")

    # 2. 새로운 편의 메서드 사용
    print("\n2. 새로운 편의 메서드:")
    print("   bridge.play_hit((400, 300), 'fire', is_critical=True)")
    print("   bridge.play_enemy_death((400, 300), 'boss')")
    print("   bridge.play_skill((400, 300), 'meteor')")
    print("   bridge.play_level_up((400, 300))")

    # 3. 직접 이펙트 생성
    print("\n3. 직접 이펙트 생성:")
    print("   bridge.create_effect('phoenix_ring', (400, 300))")
    print("   bridge.create_composite('explosion_full', (400, 300))")

    # 4. 커스텀 설정으로 생성
    print("\n4. 커스텀 설정 덮어쓰기:")
    print("   bridge.create_effect('hit_normal', (400, 300), overrides={")
    print("       'color_tint': [255, 0, 0],")
    print("       'duration': 2.0")
    print("   })")

    # 사용 가능한 이펙트 목록
    print("\n=== Available Effects ===")
    for effect in bridge.list_effects():
        print(f"  - {effect}")

    print("\n=== Available Composites ===")
    for composite in bridge.list_composites():
        print(f"  - {composite}")


if __name__ == "__main__":
    # 명령줄 인자 확인
    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        demo_bridge_usage()
    else:
        main()
