# game_logic/helpers.py
"""
Helper functions for visual effects, game initialization, and utilities.
Handles particle creation, screen effects, visual effect updates, and game reset.
"""

import pygame
import random
import math
import config
from typing import Dict, List, Tuple
from pathlib import Path
from entities.player import Player
from entities.enemies import Enemy
from entities.weapons import Bullet
from entities.collectibles import CoinGem, HealItem
from effects.combat_effects import AnimatedEffect


# =========================================================
# 시각 효과 헬퍼 함수들
# =========================================================

def create_explosion_particles(pos: Tuple[float, float], particles: List) -> None:
    """적 처치 시 폭발 파티클 생성"""
    from effects.screen_effects import Particle

    settings = config.PARTICLE_SETTINGS["EXPLOSION"]
    count = settings["count"]
    colors = settings["colors"]
    size_range = settings["size_range"]
    lifetime_range = settings["lifetime_range"]
    speed_range = settings["speed_range"]

    for _ in range(count):
        # 랜덤 방향
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(speed_range[0], speed_range[1])
        velocity = pygame.math.Vector2(math.cos(angle), math.sin(angle)) * speed

        # 랜덤 색상, 크기, 수명
        color = random.choice(colors)
        size = random.randint(size_range[0], size_range[1])
        lifetime = random.uniform(lifetime_range[0], lifetime_range[1])

        particle = Particle(pos, velocity, color, size, lifetime, gravity=True)
        particles.append(particle)


def create_hit_particles(pos: Tuple[float, float], particles: List) -> None:
    """일반 피격 시 파티클 생성"""
    from effects.screen_effects import Particle

    settings = config.PARTICLE_SETTINGS["HIT"]
    count = settings["count"]
    colors = settings["colors"]
    size_range = settings["size_range"]
    lifetime_range = settings["lifetime_range"]
    speed_range = settings["speed_range"]

    for _ in range(count):
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(speed_range[0], speed_range[1])
        velocity = pygame.math.Vector2(math.cos(angle), math.sin(angle)) * speed

        color = random.choice(colors)
        size = random.randint(size_range[0], size_range[1])
        lifetime = random.uniform(lifetime_range[0], lifetime_range[1])

        particle = Particle(pos, velocity, color, size, lifetime, gravity=False)
        particles.append(particle)


def create_boss_hit_particles(pos: Tuple[float, float], particles: List) -> None:
    """보스 피격 시 강화된 파티클 생성"""
    from effects.screen_effects import Particle

    settings = config.PARTICLE_SETTINGS["BOSS_HIT"]
    count = settings["count"]
    colors = settings["colors"]
    size_range = settings["size_range"]
    lifetime_range = settings["lifetime_range"]
    speed_range = settings["speed_range"]

    for _ in range(count):
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(speed_range[0], speed_range[1])
        velocity = pygame.math.Vector2(math.cos(angle), math.sin(angle)) * speed

        color = random.choice(colors)
        size = random.randint(size_range[0], size_range[1])
        lifetime = random.uniform(lifetime_range[0], lifetime_range[1])

        particle = Particle(pos, velocity, color, size, lifetime, gravity=True)
        particles.append(particle)


def create_shockwave(pos: Tuple[float, float], shockwave_type: str, effects: List) -> None:
    """충격파 효과 생성 (BOSS_SPAWN, BOSS_DEATH, BOSS_ATTACK)"""
    from effects.screen_effects import Shockwave

    if shockwave_type not in config.SHOCKWAVE_SETTINGS:
        return

    settings = config.SHOCKWAVE_SETTINGS[shockwave_type]
    shockwave = Shockwave(
        center=pos,
        max_radius=settings["max_radius"],
        duration=settings["duration"],
        color=settings["color"],
        width=settings["width"]
    )
    effects.append(shockwave)


def create_spawn_effect(pos: Tuple[float, float], effects: List) -> None:
    """적 스폰 포털 효과 생성"""
    from effects.game_animations import SpawnEffect

    spawn_effect = SpawnEffect(
        pos=pos,
        duration=config.SPAWN_EFFECT_DURATION,
        max_size=config.SPAWN_EFFECT_SIZE
    )
    effects.append(spawn_effect)


def create_dynamic_text(text: str, pos: Tuple[float, float], text_type: str, effects: List) -> None:
    """동적 텍스트 효과 생성 (BOSS_SPAWN, CRITICAL)"""
    from effects.screen_effects import DynamicTextEffect

    if text_type not in config.DYNAMIC_TEXT_SETTINGS:
        return

    settings = config.DYNAMIC_TEXT_SETTINGS[text_type]
    dynamic_text = DynamicTextEffect(
        text=text,
        size=settings["size"],
        color=settings["color"],
        pos=pos,
        duration_frames=settings["duration_frames"],
        shake_intensity=settings["shake_intensity"]
    )
    effects.append(dynamic_text)


def trigger_screen_shake(shake_type: str, screen_shake: 'ScreenShake') -> None:
    """화면 떨림 트리거 (PLAYER_HIT, BOSS_HIT, BOSS_SPAWN, BOSS_DEATH, ENEMY_DEATH)"""
    if shake_type not in config.SCREEN_SHAKE_SETTINGS:
        return

    settings = config.SCREEN_SHAKE_SETTINGS[shake_type]
    screen_shake.start_shake(
        intensity=settings["intensity"],
        duration_frames=settings["duration"]
    )


def create_time_slow_effect(effects: List) -> None:
    """타임 슬로우 효과 생성 (보스 처치 시)"""
    from effects.screen_effects import TimeSlowEffect

    settings = config.TIME_SLOW_SETTINGS["BOSS_DEATH"]
    time_slow = TimeSlowEffect(
        slow_factor=settings["slow_factor"],
        duration=settings["duration"]
    )
    effects.append(time_slow)


def update_visual_effects(effects: List, dt: float, screen_size: Tuple[int, int] = None, enemies: List = None) -> None:
    """모든 시각 효과 업데이트 (파티클, 충격파, 텍스트 등)"""
    from effects import (
        WaveTransitionEffect, PlayerVictoryAnimation, WaveClearFireworksEffect,
        StaticField, SpawnEffect
    )
    from effects.screen_effects import Particle, Shockwave, ImageShockwave, DynamicTextEffect, TimeSlowEffect, ScreenFlash, ReviveTextEffect, LightningEffect

    for effect in effects[:]:
        if isinstance(effect, (Particle, Shockwave, ImageShockwave, SpawnEffect)):
            effect.update(dt)
            if not effect.is_alive:
                effects.remove(effect)
        elif isinstance(effect, LightningEffect):
            effect.update(dt)
            if not effect.is_alive:
                effects.remove(effect)
        elif isinstance(effect, DynamicTextEffect):
            effect.update(dt)
            if not effect.is_alive:
                effects.remove(effect)
        elif isinstance(effect, TimeSlowEffect):
            effect.update(dt)
            if not effect.is_active:
                effects.remove(effect)
        elif isinstance(effect, StaticField):
            effect.update(dt)
            if enemies:
                effect.apply_damage(enemies, dt)
            if not effect.is_active:
                effects.remove(effect)
        elif isinstance(effect, ScreenFlash):
            effect.update(dt)
            if not effect.is_alive:
                effects.remove(effect)
        elif isinstance(effect, WaveTransitionEffect):
            effect.update(dt)
            if not effect.is_alive:
                effects.remove(effect)
        elif isinstance(effect, PlayerVictoryAnimation):
            effect.update(dt)
            if not effect.is_alive:
                effects.remove(effect)
        elif isinstance(effect, ReviveTextEffect):
            effect.update(dt)
            if not effect.is_alive:
                effects.remove(effect)
        elif isinstance(effect, WaveClearFireworksEffect):
            effect.update(dt)
            if not effect.is_alive:
                effects.remove(effect)
        elif isinstance(effect, AnimatedEffect):
            # 기존 AnimatedEffect는 current_time 필요
            current_time = pygame.time.get_ticks() / 1000.0
            effect.update(dt, current_time)
            if effect.is_finished:
                effects.remove(effect)


def draw_visual_effects(screen: pygame.Surface, effects: List, screen_offset: pygame.math.Vector2 = None) -> None:
    """모든 시각 효과 그리기"""
    from effects import (
        WaveTransitionEffect, WaveClearFireworksEffect,
        StaticField, SpawnEffect
    )
    from effects.screen_effects import Particle, Shockwave, ImageShockwave, DynamicTextEffect, TimeSlowEffect, ScreenFlash, ReviveTextEffect, LightningEffect

    if screen_offset is None:
        screen_offset = pygame.math.Vector2(0, 0)

    for effect in effects:
        if isinstance(effect, (Particle, Shockwave, ImageShockwave, SpawnEffect, AnimatedEffect, StaticField, ScreenFlash, WaveTransitionEffect, ReviveTextEffect, LightningEffect, WaveClearFireworksEffect)):
            effect.draw(screen)


# =========================================================
# 게임 리셋 함수
# =========================================================

def reset_game(screen_size: Tuple[int, int], player_upgrades: Dict[str, int]):
    """
    새로운 게임 세션을 위해 모든 객체와 데이터를 초기화합니다.
    """
    from .game_state import reset_game_data

    game_data = reset_game_data()

    # Player 객체 생성 시 영구 업그레이드 정보를 전달합니다.
    player = Player(
        pos=pygame.math.Vector2(screen_size[0] // 2, screen_size[1] // 2),
        screen_height=screen_size[1],
        upgrades=player_upgrades
    )

    enemies: List[Enemy] = []
    bullets: List[Bullet] = []
    gems: List[CoinGem | HealItem] = []
    effects: List[AnimatedEffect] = [] # HitImpact 대신 AnimatedEffect 사용

    # 스폰 시간을 game_data 내부 값으로 초기화
    game_data["last_enemy_spawn_time"] = 0.0
    game_data["last_gem_spawn_time"] = 0.0

    return player, enemies, bullets, gems, effects, game_data
