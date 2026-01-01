# Game Logic Package

Clean, domain-specific organization of game logic functions extracted from utils.py.

## Package Structure

```
game_logic/
├── __init__.py           (112 lines) - Package exports
├── game_state.py         ( 98 lines) - State management
├── wave_manager.py       (638 lines) - Wave progression & combat
├── spawning.py           (343 lines) - Enemy/item spawning
├── events.py             (177 lines) - Random event system
├── upgrades.py           (392 lines) - Upgrades & abilities
└── helpers.py            (274 lines) - Visual effects & utilities
```

**Total: 2,034 lines** (down from 1,882 lines in single file with better organization)

## Quick Import

```python
# Import everything
from game_logic import *

# Or import specific functions
from game_logic import (
    reset_game_data,
    start_wave,
    update_game_objects,
    handle_spawning,
    generate_tactical_options
)
```

## Module Purposes

- **game_state.py**: Game data initialization, level progression, stage tracking
- **wave_manager.py**: Wave control, game object updates, collision detection, rendering
- **spawning.py**: Enemy spawning logic, gem spawning, turret placement
- **events.py**: Random event triggering and effects (Treasure Rain, Meteor Shower, etc.)
- **upgrades.py**: Tactical upgrades, synergies, ship abilities
- **helpers.py**: Particle effects, visual effects, screen shake, game reset

## 38 Exported Functions

See `MIGRATION_GUIDE.md` for complete list and migration instructions.
