"""
cutscenes package
All cutscene effect classes organized by category
"""

from .base import BaseCutsceneEffect, render_dialogue_box
from .story_effects import StoryBriefingEffect
from .memory_effects import (
    PolaroidMemoryEffect,
    ShatteredMirrorEffect,
    DualMemoryEffect,
    SeasonMemoryEffect,
    BrokenToyEffect,
)
from .document_effects import (
    ClassifiedDocumentEffect,
    BurningRecordEffect,
    FilmReelEffect,
)
from .world_effects import StarMapEffect, AndromedaWorldEffect, TwoWorldsEffect
from .communication_effects import HologramMessageEffect, RadioWaveEffect, CountdownEffect
from .animation_effects import ShipEntranceEffect
from .combat_effects import BunkerCannonEffect, CombatMotionEffect, CannonShell

__all__ = [
    # Base
    "BaseCutsceneEffect",
    "render_dialogue_box",
    # Story
    "StoryBriefingEffect",
    # Memory
    "PolaroidMemoryEffect",
    "ShatteredMirrorEffect",
    "DualMemoryEffect",
    "SeasonMemoryEffect",
    "BrokenToyEffect",
    # Document
    "ClassifiedDocumentEffect",
    "BurningRecordEffect",
    "FilmReelEffect",
    # World
    "StarMapEffect",
    "AndromedaWorldEffect",
    "TwoWorldsEffect",
    # Communication
    "HologramMessageEffect",
    "RadioWaveEffect",
    "CountdownEffect",
    # Animation
    "ShipEntranceEffect",
    # Combat
    "BunkerCannonEffect",
    "CombatMotionEffect",
    "CannonShell",
]
