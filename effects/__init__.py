'''
Effects Package - Visual effects for the game
효과 패키지 - 게임의 시각 효과들

This package contains all visual effect classes organized by category:
- screen_effects: Particles, flashes, shakes, basic effects
- combat_effects: Damage numbers and combat animations
- death_effects: Enemy death effects (shatter, vortex, pixelate)
- transitions: Scene and background transitions
- game_animations: Victory, wave clear, base arrival animations
'''

# Screen effects (particles, flashes, shakes, basic effects)
from .screen_effects import (
    Particle,
    ScreenFlash,
    ScreenShake,
    DamageFlash,
    DynamicTextEffect,
    ReviveTextEffect,
    NebulaParticle,
    SmokeParticle,
    BurstParticle,
    DissolveEffect,
    FadeEffect,
    ImplodeEffect,
    TimeSlowEffect,
    LevelUpEffect
)

# Combat effects (damage numbers, combat animations)
from .combat_effects import (
    DamageNumber,
    DamageNumberManager,
    AnimatedEffect
)

# Death effects (enemy death animations)
from .death_effects import (
    ShatterFragment,
    VortexEffect,
    PixelateEffect,
    DeathEffectManager
)

# Transition effects (scene and background transitions)
from .transitions import (
    WaveTransitionEffect,
    BackgroundTransition,
    ParallaxLayer
)

# Game animations (victory, wave clear, base arrival, etc.)
from .game_animations import (
    PlayerVictoryAnimation,
    WaveClearFireworksEffect,
    ReturnToBaseAnimation,
    BaseArrivalAnimation,
    DialogueShipAnimation,
    Meteor,
    StaticField,
    SpawnEffect
)

__all__ = [
    # Screen effects
    'Particle',
    'ScreenFlash',
    'ScreenShake',
    'DamageFlash',
    'DynamicTextEffect',
    'ReviveTextEffect',
    'NebulaParticle',
    'SmokeParticle',
    'BurstParticle',
    'DissolveEffect',
    'FadeEffect',
    'ImplodeEffect',
    'TimeSlowEffect',
    'LevelUpEffect',

    # Combat effects
    'DamageNumber',
    'DamageNumberManager',
    'AnimatedEffect',

    # Death effects
    'ShatterFragment',
    'VortexEffect',
    'PixelateEffect',
    'DeathEffectManager',

    # Transition effects
    'WaveTransitionEffect',
    'BackgroundTransition',
    'ParallaxLayer',

    # Game animations
    'PlayerVictoryAnimation',
    'WaveClearFireworksEffect',
    'ReturnToBaseAnimation',
    'BaseArrivalAnimation',
    'DialogueShipAnimation',
    'Meteor',
    'StaticField',
    'SpawnEffect',
]
