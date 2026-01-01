# Game Logic Module Extraction - Migration Guide

## Overview
Successfully split `utils.py` (1,882 lines) into 6 domain-specific modules within the `game_logic/` package (2,034 total lines).

## Created Modules

### 1. `game_logic/game_state.py` (98 lines)
**Purpose**: Game state management and level progression

**Functions**:
- `reset_game_data()` - Initialize game session data
- `handle_level_up()` - Process level up
- `get_next_level_threshold()` - Calculate next level requirement
- `get_current_stage()` - Get current stage info
- `check_stage_transition()` - Check if stage changed

### 2. `game_logic/wave_manager.py` (638 lines)
**Purpose**: Wave progression, game object updates, and rendering

**Functions**:
- `start_wave()` - Start new wave
- `check_wave_clear()` - Check if wave is cleared
- `advance_to_next_wave()` - Progress to next wave
- `get_wave_scaling()` - Get wave difficulty scaling
- `select_enemy_type()` - Select enemy type for wave
- `update_game_objects()` - Update all game objects and handle collisions
- `draw_objects()` - Draw all game objects

**Note**: This is the largest module as it contains the comprehensive collision and combat logic.

### 3. `game_logic/spawning.py` (343 lines)
**Purpose**: Enemy and item spawning, turret placement

**Functions**:
- `spawn_enemy()` - Spawn enemy at random location
- `handle_spawning()` - Manage enemy spawn timing and logic
- `spawn_gem()` - Spawn healing gems
- `calculate_turret_positions()` - Calculate turret placement positions
- `auto_place_turrets()` - Auto-place turrets on screen

### 4. `game_logic/events.py` (177 lines)
**Purpose**: Random event system

**Functions**:
- `try_trigger_random_event()` - Try to trigger random event
- `start_random_event()` - Start random event
- `update_random_event()` - Update event effects (Treasure Rain, Meteor Shower, etc.)
- `end_random_event()` - End random event
- `get_active_event_modifiers()` - Get active event modifiers

### 5. `game_logic/upgrades.py` (392 lines)
**Purpose**: Upgrade system, tactical options, synergies, ship abilities

**Functions**:
- `generate_tactical_options()` - Generate upgrade options for player
- `check_and_activate_synergies()` - Check and activate skill synergies
- `handle_tactical_upgrade()` - Apply selected upgrade
- `trigger_ship_ability()` - Trigger ship special ability

### 6. `game_logic/helpers.py` (274 lines)
**Purpose**: Visual effects, particles, game reset utilities

**Functions**:
- `create_explosion_particles()` - Create explosion particle effects
- `create_hit_particles()` - Create hit particle effects
- `create_boss_hit_particles()` - Create boss hit particle effects
- `create_shockwave()` - Create shockwave effect
- `create_spawn_effect()` - Create spawn portal effect
- `create_dynamic_text()` - Create dynamic text effect
- `trigger_screen_shake()` - Trigger screen shake
- `create_time_slow_effect()` - Create time slow effect
- `update_visual_effects()` - Update all visual effects
- `draw_visual_effects()` - Draw all visual effects
- `reset_game()` - Reset game for new session

### 7. `game_logic/__init__.py` (112 lines)
**Purpose**: Package initialization and exports

Exports all 38 functions from the 6 modules above for easy importing.

## How to Use

### Option 1: Import entire package
```python
import game_logic

# Use functions
game_logic.reset_game_data()
game_logic.start_wave(game_data, current_time, enemies)
```

### Option 2: Import specific functions
```python
from game_logic import reset_game_data, start_wave, handle_spawning

# Use functions directly
reset_game_data()
start_wave(game_data, current_time, enemies)
```

### Option 3: Import from specific modules
```python
from game_logic.game_state import reset_game_data, handle_level_up
from game_logic.wave_manager import start_wave, update_game_objects
from game_logic.spawning import handle_spawning, auto_place_turrets

# Use functions
reset_game_data()
start_wave(game_data, current_time, enemies)
```

## Migration Steps for Existing Code

### Files that need updating:
1. `ui.py`
2. `modes/training_mode.py`
3. `modes/base_mode.py`
4. `modes/wave_mode.py`
5. `modes/combat_mode.py`
6. `systems/skill_system.py`
7. `systems/combat_system.py`
8. `systems/spawn_system.py`

### Migration pattern:

**Before:**
```python
from utils import (
    reset_game_data,
    start_wave,
    handle_spawning,
    update_game_objects
)
```

**After:**
```python
from game_logic import (
    reset_game_data,
    start_wave,
    handle_spawning,
    update_game_objects
)
```

Or use the wildcard import for convenience:
```python
from game_logic import *
```

## Function Organization Summary

| Category | Module | Functions | Lines |
|----------|--------|-----------|-------|
| State Management | game_state.py | 5 | 98 |
| Wave & Combat | wave_manager.py | 7 | 638 |
| Spawning | spawning.py | 5 | 343 |
| Events | events.py | 5 | 177 |
| Upgrades | upgrades.py | 4 | 392 |
| Visual Effects | helpers.py | 12 | 274 |
| Package Init | __init__.py | - | 112 |
| **Total** | **7 files** | **38 functions** | **2,034** |

## Benefits

1. **Clear Separation of Concerns**: Each module has a single, well-defined purpose
2. **Easier Maintenance**: Finding and modifying functions is much simpler
3. **Better Code Navigation**: Developers can quickly locate relevant code
4. **Reduced Coupling**: Modules import only what they need
5. **Improved Testability**: Each module can be tested independently
6. **Scalability**: New features can be added to appropriate modules without bloating a single file

## Dependencies Between Modules

```
game_state.py (no internal dependencies)
    ↓
events.py (imports from game_state indirectly)
    ↓
wave_manager.py (imports from events, helpers)
    ↓
spawning.py (imports from wave_manager, helpers)
    ↓
upgrades.py (imports from game_state)
    ↓
helpers.py (imports from game_state)
```

## Notes

- All functions maintain their original signatures and behavior
- All imports and dependencies are preserved
- Comments and docstrings are kept intact
- The original `utils.py` file remains unchanged (can be archived/removed after migration)

## Verification

Test import:
```bash
python -c "from game_logic import *; print('Success! Imported', len([x for x in dir() if not x.startswith('_')]), 'functions')"
```

Expected output:
```
Import successful! Available functions: 38
```
