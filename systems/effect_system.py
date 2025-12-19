# systems/effect_system.py
"""
EffectSystem - 시각 효과 시스템
파티클, 충격파, 텍스트 효과 등 관리
모든 모드에서 공유
"""

import pygame
from typing import List, Tuple
import config
from objects import (
    Particle, Shockwave, DynamicTextEffect, SpawnEffect,
    TimeSlowEffect, AnimatedEffect
)


class EffectSystem:
    """
    이펙트 시스템 - 모든 모드에서 공유하는 시각 효과 로직

    기능:
    - 파티클 효과 생성/업데이트
    - 충격파 효과
    - 텍스트 효과
    - 타임 슬로우 효과
    """

    def __init__(self):
        """이펙트 시스템 초기화"""
        self.max_particles = config.MAX_PARTICLES_ON_SCREEN

    def update(
        self,
        effects: List,
        dt: float,
        screen_size: Tuple[int, int],
        enemies: List = None,
    ):
        """
        모든 이펙트 업데이트

        Args:
            effects: 이펙트 리스트
            dt: 델타 타임
            screen_size: 화면 크기
            enemies: 적 리스트 (일부 이펙트에서 필요)
        """
        for effect in effects[:]:
            # 이펙트 타입별 업데이트
            if hasattr(effect, 'update'):
                if isinstance(effect, Shockwave) and enemies:
                    effect.update(dt, enemies)
                else:
                    effect.update(dt)

            # 수명 체크
            if hasattr(effect, 'is_alive') and not effect.is_alive:
                effects.remove(effect)
            elif hasattr(effect, 'is_active') and not effect.is_active:
                effects.remove(effect)
            elif hasattr(effect, 'lifetime'):
                effect.lifetime -= dt
                if effect.lifetime <= 0:
                    effects.remove(effect)

        # 파티클 수 제한
        particle_count = sum(1 for e in effects if isinstance(e, Particle))
        if particle_count > self.max_particles:
            # 가장 오래된 파티클부터 제거
            particles = [e for e in effects if isinstance(e, Particle)]
            for p in particles[:particle_count - self.max_particles]:
                if p in effects:
                    effects.remove(p)

    def draw(
        self,
        screen: pygame.Surface,
        effects: List,
        screen_offset: Tuple[int, int] = (0, 0),
    ):
        """
        모든 이펙트 렌더링

        Args:
            screen: pygame 화면 Surface
            effects: 이펙트 리스트
            screen_offset: 화면 흔들림 오프셋
        """
        for effect in effects:
            if hasattr(effect, 'draw'):
                # 화면 흔들림 적용
                if screen_offset != (0, 0) and hasattr(effect, 'pos'):
                    original_pos = effect.pos.copy() if hasattr(effect.pos, 'copy') else effect.pos
                    if hasattr(effect.pos, 'x'):
                        effect.pos.x += screen_offset[0]
                        effect.pos.y += screen_offset[1]

                effect.draw(screen)

                # 위치 복원
                if screen_offset != (0, 0) and hasattr(effect, 'pos'):
                    effect.pos = original_pos

    # ===== 이펙트 생성 헬퍼 메서드 =====

    def create_explosion(
        self,
        effects: List,
        position: pygame.math.Vector2,
        color: Tuple[int, int, int] = (255, 150, 50),
        particle_count: int = 20,
        speed: float = 200,
    ):
        """폭발 파티클 효과 생성"""
        import random
        import math

        for _ in range(particle_count):
            angle = random.uniform(0, 2 * math.pi)
            velocity = pygame.math.Vector2(
                math.cos(angle) * random.uniform(speed * 0.5, speed),
                math.sin(angle) * random.uniform(speed * 0.5, speed)
            )

            particle = Particle(
                pos=position.copy(),
                velocity=velocity,
                color=color,
                size=random.uniform(3, 8),
                lifetime=random.uniform(0.3, 0.8)
            )
            effects.append(particle)

    def create_hit_effect(
        self,
        effects: List,
        position: pygame.math.Vector2,
        color: Tuple[int, int, int] = (255, 255, 100),
        particle_count: int = 5,
    ):
        """피격 파티클 효과 생성"""
        import random
        import math

        for _ in range(particle_count):
            angle = random.uniform(0, 2 * math.pi)
            velocity = pygame.math.Vector2(
                math.cos(angle) * random.uniform(50, 150),
                math.sin(angle) * random.uniform(50, 150)
            )

            particle = Particle(
                pos=position.copy(),
                velocity=velocity,
                color=color,
                size=random.uniform(2, 5),
                lifetime=random.uniform(0.2, 0.4)
            )
            effects.append(particle)

    def create_shockwave(
        self,
        effects: List,
        position: pygame.math.Vector2,
        max_radius: float = 100,
        duration: float = 0.3,
        color: Tuple[int, int, int] = (255, 255, 255),
    ):
        """충격파 효과 생성"""
        shockwave = Shockwave(
            pos=position.copy(),
            max_radius=max_radius,
            duration=duration,
            color=color
        )
        effects.append(shockwave)

    def create_dynamic_text(
        self,
        effects: List,
        position: pygame.math.Vector2,
        text: str,
        color: Tuple[int, int, int] = (255, 255, 255),
        size: int = 24,
        duration: float = 1.0,
    ):
        """동적 텍스트 효과 생성"""
        text_effect = DynamicTextEffect(
            pos=position.copy(),
            text=text,
            color=color,
            size=size,
            duration=duration
        )
        effects.append(text_effect)

    def create_spawn_effect(
        self,
        effects: List,
        position: pygame.math.Vector2,
        color: Tuple[int, int, int] = (100, 100, 255),
    ):
        """스폰 효과 생성"""
        spawn_effect = SpawnEffect(
            pos=position.copy(),
            color=color
        )
        effects.append(spawn_effect)

    def create_time_slow(
        self,
        effects: List,
        duration: float = 2.0,
        slow_factor: float = 0.3,
    ):
        """타임 슬로우 효과 생성"""
        # 기존 타임 슬로우 제거
        for effect in effects[:]:
            if isinstance(effect, TimeSlowEffect):
                effects.remove(effect)

        time_slow = TimeSlowEffect(
            duration=duration,
            slow_factor=slow_factor
        )
        effects.append(time_slow)

    # ===== Ship Ability 이펙트 =====

    def create_bomb_explosion(
        self,
        effects: List,
        position: pygame.math.Vector2,
        radius: float = 200,
    ):
        """폭탄 폭발 이펙트 (BOMBER 특수 능력)"""
        import random
        import math

        # 큰 충격파
        self.create_shockwave(effects, position, radius, 0.5, (255, 100, 50))

        # 두 번째 작은 충격파
        self.create_shockwave(effects, position, radius * 0.6, 0.35, (255, 200, 100))

        # 폭발 파티클 (많은 수)
        for _ in range(50):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(100, 400)
            velocity = pygame.math.Vector2(
                math.cos(angle) * speed,
                math.sin(angle) * speed
            )

            # 화염 색상 그라데이션
            color_choice = random.choice([
                (255, 100, 30),   # 주황
                (255, 180, 50),   # 노랑
                (255, 50, 20),    # 빨강
                (200, 50, 10),    # 어두운 빨강
            ])

            particle = Particle(
                pos=position.copy(),
                velocity=velocity,
                color=color_choice,
                size=random.uniform(4, 12),
                lifetime=random.uniform(0.4, 1.0)
            )
            effects.append(particle)

        # 동적 텍스트
        self.create_dynamic_text(effects, position, "BOOM!", (255, 100, 50), 40, 1.0)

    def create_shield_effect(
        self,
        effects: List,
        position: pygame.math.Vector2,
        radius: float = 60,
    ):
        """쉴드 활성화 이펙트 (TITAN 특수 능력)"""
        import random
        import math

        # 푸른 충격파
        self.create_shockwave(effects, position, radius * 1.5, 0.4, (100, 150, 255))

        # 쉴드 파티클 (원형으로)
        for i in range(20):
            angle = (2 * math.pi / 20) * i
            spawn_pos = pygame.math.Vector2(
                position.x + math.cos(angle) * radius * 0.5,
                position.y + math.sin(angle) * radius * 0.5
            )
            velocity = pygame.math.Vector2(
                math.cos(angle) * 50,
                math.sin(angle) * 50
            )

            particle = Particle(
                pos=spawn_pos,
                velocity=velocity,
                color=(100, 180, 255),
                size=random.uniform(3, 6),
                lifetime=random.uniform(0.5, 1.0)
            )
            effects.append(particle)

        self.create_dynamic_text(effects, position, "SHIELD!", (100, 180, 255), 30, 1.0)

    def create_cloak_effect(
        self,
        effects: List,
        position: pygame.math.Vector2,
    ):
        """클로킹 활성화 이펙트 (STEALTH 특수 능력)"""
        import random
        import math

        # 사라지는 파티클 효과
        for _ in range(30):
            offset_x = random.uniform(-40, 40)
            offset_y = random.uniform(-40, 40)
            spawn_pos = pygame.math.Vector2(
                position.x + offset_x,
                position.y + offset_y
            )

            # 위로 사라지는 효과
            velocity = pygame.math.Vector2(
                random.uniform(-20, 20),
                random.uniform(-100, -50)
            )

            # 보라/검정 색상
            color_choice = random.choice([
                (80, 50, 150),
                (50, 30, 100),
                (100, 70, 180),
            ])

            particle = Particle(
                pos=spawn_pos,
                velocity=velocity,
                color=color_choice,
                size=random.uniform(2, 5),
                lifetime=random.uniform(0.5, 1.2)
            )
            effects.append(particle)

        self.create_dynamic_text(effects, position, "CLOAK!", (150, 100, 200), 28, 1.0)

    def create_evasion_effect(
        self,
        effects: List,
        position: pygame.math.Vector2,
    ):
        """회피 부스트 이펙트 (INTERCEPTOR 특수 능력)"""
        import random
        import math

        # 빠른 충격파
        self.create_shockwave(effects, position, 80, 0.25, (255, 255, 100))

        # 스피드 라인 파티클
        for _ in range(25):
            angle = random.uniform(0, 2 * math.pi)
            spawn_pos = pygame.math.Vector2(
                position.x + math.cos(angle) * random.uniform(20, 50),
                position.y + math.sin(angle) * random.uniform(20, 50)
            )

            # 바깥으로 빠르게
            velocity = pygame.math.Vector2(
                math.cos(angle) * random.uniform(200, 400),
                math.sin(angle) * random.uniform(200, 400)
            )

            particle = Particle(
                pos=spawn_pos,
                velocity=velocity,
                color=(255, 255, 150),
                size=random.uniform(2, 4),
                lifetime=random.uniform(0.2, 0.5)
            )
            effects.append(particle)

        self.create_dynamic_text(effects, position, "EVASION!", (255, 255, 100), 28, 0.8)


print("INFO: effect_system.py loaded")
