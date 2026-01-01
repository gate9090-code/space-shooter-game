# game_logic/__init__.py
"""
Game logic package.
Central module for all game logic functions organized by domain.
"""

# Game state management
from .game_state import (
    reset_game_data,
    handle_level_up,
    get_next_level_threshold,
    get_current_stage,
    check_stage_transition,
)

# Wave management
from .wave_manager import (
    start_wave,
    check_wave_clear,
    advance_to_next_wave,
    get_wave_scaling,
    select_enemy_type,
    update_game_objects,
    draw_objects,
)

# Spawning
from .spawning import (
    spawn_enemy,
    handle_spawning,
    spawn_gem,
    calculate_turret_positions,
    auto_place_turrets,
)

# Events
from .events import (
    try_trigger_random_event,
    start_random_event,
    update_random_event,
    end_random_event,
    get_active_event_modifiers,
)

# Upgrades and tactical systems
from .upgrades import (
    generate_tactical_options,
    check_and_activate_synergies,
    handle_tactical_upgrade,
    trigger_ship_ability,
)

# Helpers (visual effects, utilities, game reset)
from .helpers import (
    create_explosion_particles,
    create_hit_particles,
    create_boss_hit_particles,
    create_shockwave,
    create_spawn_effect,
    create_dynamic_text,
    trigger_screen_shake,
    create_time_slow_effect,
    update_visual_effects,
    draw_visual_effects,
    reset_game,
)

__all__ = [
    # Game state
    'reset_game_data',
    'handle_level_up',
    'get_next_level_threshold',
    'get_current_stage',
    'check_stage_transition',
    # Wave management
    'start_wave',
    'check_wave_clear',
    'advance_to_next_wave',
    'get_wave_scaling',
    'select_enemy_type',
    'update_game_objects',
    'draw_objects',
    # Spawning
    'spawn_enemy',
    'handle_spawning',
    'spawn_gem',
    'calculate_turret_positions',
    'auto_place_turrets',
    # Events
    'try_trigger_random_event',
    'start_random_event',
    'update_random_event',
    'end_random_event',
    'get_active_event_modifiers',
    # Upgrades
    'generate_tactical_options',
    'check_and_activate_synergies',
    'handle_tactical_upgrade',
    'trigger_ship_ability',
    # Helpers
    'create_explosion_particles',
    'create_hit_particles',
    'create_boss_hit_particles',
    'create_shockwave',
    'create_spawn_effect',
    'create_dynamic_text',
    'trigger_screen_shake',
    'create_time_slow_effect',
    'update_visual_effects',
    'draw_visual_effects',
    'reset_game',
]
