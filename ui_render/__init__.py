# ui_render/__init__.py
# UI rendering module - exports all UI rendering functions

# Helper functions and classes
from .helpers import (
    get_font,
    render_text_with_emoji,
    HPBarShake
)

# HUD functions
from .hud import (
    draw_hud,
    draw_skill_indicators
)

# Menu functions
from .menus import (
    draw_pause_and_over_screens,
    draw_settings_menu,
    draw_death_effect_ui
)

# Combat UI functions
from .combat_ui import (
    draw_boss_health_bar,
    draw_random_event_ui,
    draw_stage_transition_screen
)

# Shop/upgrade UI functions
from .shop import (
    draw_shop_screen,
    draw_tactical_menu
)

# Wave UI functions
from .wave_ui import (
    draw_wave_prepare_screen,
    draw_wave_clear_screen,
    draw_victory_screen,
    draw_boss_clear_choice
)

__all__ = [
    # Helper functions and classes
    'get_font',
    'render_text_with_emoji',
    'HPBarShake',

    # HUD functions
    'draw_hud',
    'draw_skill_indicators',

    # Menu functions
    'draw_pause_and_over_screens',
    'draw_settings_menu',
    'draw_death_effect_ui',

    # Combat UI functions
    'draw_boss_health_bar',
    'draw_random_event_ui',
    'draw_stage_transition_screen',

    # Shop/upgrade UI functions
    'draw_shop_screen',
    'draw_tactical_menu',

    # Wave UI functions
    'draw_wave_prepare_screen',
    'draw_wave_clear_screen',
    'draw_victory_screen',
    'draw_boss_clear_choice',
]
