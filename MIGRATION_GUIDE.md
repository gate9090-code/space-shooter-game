# 📘 Import 마이그레이션 가이드

프로젝트 리팩토링 후 Import 문을 업데이트하는 빠른 참조 가이드입니다.

---

## 🔄 빠른 변환 표

### config 모듈

| Before | After |
|--------|-------|
| `import config` | `import config` (동일하게 작동) |
| `from config import FPS` | `from config.core import FPS` (권장) |
| `from config import ENEMY_BASE_HP` | `from config.entities import ENEMY_BASE_HP` |
| `from config import WAVE_SCALING` | `from config.gameplay import WAVE_SCALING` |
| `from config import UI_COLORS` | `from config.visuals import UI_COLORS` |
| `from config import ASSET_DIR` | `from config.assets import ASSET_DIR` |
| `from config import BGM_FILES` | `from config.audio import BGM_FILES` |

### objects 모듈 (완전히 제거됨)

| Before | After |
|--------|-------|
| `from objects import Player` | `from entities.player import Player` |
| `from objects import Enemy, Boss` | `from entities.enemies import Enemy, Boss` |
| `from objects import Weapon, Bullet` | `from entities.weapons import Weapon, Bullet` |
| `from objects import CoinGem, HealItem` | `from entities.collectibles import CoinGem, HealItem` |
| `from objects import Turret, Drone` | `from entities.support_units import Turret, Drone` |
| `from objects import Particle` | `from effects.screen_effects import Particle` |
| `from objects import DamageNumber` | `from effects.combat_effects import DamageNumber` |
| `from objects import WaveTransitionEffect` | `from effects.transitions import WaveTransitionEffect` |
| `from objects import PolaroidMemoryEffect` | `from cutscenes.memory_effects import PolaroidMemoryEffect` |
| `from objects import StoryBriefingEffect` | `from cutscenes.story_effects import StoryBriefingEffect` |

### utils 모듈 (완전히 제거됨)

| Before | After |
|--------|-------|
| `from utils import start_wave` | `from game_logic.wave_manager import start_wave` |
| `from utils import spawn_enemy` | `from game_logic.spawning import spawn_enemy` |
| `from utils import reset_game_data` | `from game_logic.game_state import reset_game_data` |
| `from utils import update_random_event` | `from game_logic.events import update_random_event` |
| `from utils import generate_tactical_options` | `from game_logic.upgrades import generate_tactical_options` |
| `from utils import create_explosion_particles` | `from game_logic.helpers import create_explosion_particles` |

### ui 모듈 (완전히 제거됨)

| Before | After |
|--------|-------|
| `from ui import draw_hud` | `from ui_render.hud import draw_hud` |
| `from ui import draw_pause_and_over_screens` | `from ui_render.menus import draw_pause_and_over_screens` |
| `from ui import draw_boss_health_bar` | `from ui_render.combat_ui import draw_boss_health_bar` |
| `from ui import draw_shop_screen` | `from ui_render.shop import draw_shop_screen` |
| `from ui import draw_wave_prepare_screen` | `from ui_render.wave_ui import draw_wave_prepare_screen` |
| `from ui import render_text_with_emoji` | `from ui_render.helpers import render_text_with_emoji` |

---

## 📝 실전 예제

### 예제 1: Combat Mode 파일

**Before:**
```python
import config
from objects import Player, Enemy, Bullet, Drone, Turret
from utils import start_wave, check_wave_clear, update_game_objects
from ui import draw_hud, draw_pause_and_over_screens
```

**After:**
```python
import config  # 또는 더 구체적으로
from config.core import FPS
from config.gameplay import WAVE_SCALING

from entities.player import Player
from entities.enemies import Enemy
from entities.weapons import Bullet
from entities.support_units import Drone, Turret

from game_logic.wave_manager import start_wave, check_wave_clear, update_game_objects

from ui_render.hud import draw_hud
from ui_render.menus import draw_pause_and_over_screens
```

### 예제 2: Narrative Mode 파일

**Before:**
```python
from objects import (
    PolaroidMemoryEffect,
    ClassifiedDocumentEffect,
    ShatteredMirrorEffect
)
```

**After:**
```python
from cutscenes.memory_effects import PolaroidMemoryEffect, ShatteredMirrorEffect
from cutscenes.document_effects import ClassifiedDocumentEffect
```

### 예제 3: Spawn System 파일

**Before:**
```python
from objects import Enemy
from utils import spawn_enemy, create_spawn_effect
```

**After:**
```python
from entities.enemies import Enemy
from game_logic.spawning import spawn_enemy
from game_logic.helpers import create_spawn_effect
```

---

## 🎯 모듈별 상세 매핑

### config/ 모듈

#### core.py
```python
# 화면, FPS, 기본 색상, UI 레이아웃
SCREEN_WIDTH_INIT, SCREEN_HEIGHT_INIT, FPS
WHITE, BLACK, RED, GREEN, YELLOW, BLUE
UI_LAYOUT, UI_EFFECTS, BG_LEVELS, TEXT_LEVELS
```

#### visuals.py
```python
# 폰트, 색상 테마, 시각 효과 설정
FONT_SYSTEM, WAVE_COLOR_THEMES
PARTICLE_SETTINGS, SHOCKWAVE_SETTINGS
```

#### entities.py
```python
# 플레이어, 적, 무기 통계
PLAYER_BASE_HP, PLAYER_BASE_SPEED
ENEMY_BASE_HP, ENEMY_TYPES
WEAPON_COOLDOWN_BASE, BULLET_SPEED
SHIP_TYPES
```

#### gameplay.py
```python
# 웨이브, 게임 상태, 이벤트, 업그레이드
GAME_STATE_*, TOTAL_WAVES, WAVE_SCALING
RANDOM_EVENTS, TACTICAL_UPGRADE_OPTIONS
SYNERGIES
```

#### assets.py
```python
# 파일 경로, 리소스 위치
ASSET_DIR, FONT_DIR, IMAGE_DIR
WAVE_BACKGROUND_POOLS
```

#### audio.py
```python
# 사운드, 음악 설정
BGM_FILES, SFX_FILES
WAVE_BGM_MAPPING
DEFAULT_BGM_VOLUME
```

### entities/ 모듈

```python
from entities.player import Player
from entities.enemies import Enemy, Boss
from entities.weapons import Weapon, Bullet, BurnProjectile
from entities.collectibles import CoinGem, HealItem
from entities.support_units import Turret, Drone
```

### effects/ 모듈

```python
# 화면 효과
from effects.screen_effects import (
    Particle, ScreenFlash, ScreenShake, DamageFlash,
    TimeSlowEffect, LevelUpEffect, DynamicTextEffect
)

# 전투 효과
from effects.combat_effects import (
    DamageNumber, DamageNumberManager, AnimatedEffect
)

# 사망 효과
from effects.death_effects import (
    DeathEffectManager, VortexEffect, PixelateEffect
)

# 전환 효과
from effects.transitions import (
    WaveTransitionEffect, BackgroundTransition, ParallaxLayer
)

# 게임 애니메이션
from effects.game_animations import (
    PlayerVictoryAnimation, WaveClearFireworksEffect,
    Meteor, StaticField
)
```

### cutscenes/ 모듈

```python
# 베이스
from cutscenes.base import BaseCutsceneEffect, render_dialogue_box

# 스토리
from cutscenes.story_effects import StoryBriefingEffect

# 메모리
from cutscenes.memory_effects import (
    PolaroidMemoryEffect, ShatteredMirrorEffect, DualMemoryEffect
)

# 문서
from cutscenes.document_effects import (
    ClassifiedDocumentEffect, BurningRecordEffect, FilmReelEffect
)

# 세계
from cutscenes.world_effects import (
    StarMapEffect, AndromedaWorldEffect, TwoWorldsEffect
)

# 통신
from cutscenes.communication_effects import (
    HologramMessageEffect, RadioWaveEffect, CountdownEffect
)

# 애니메이션
from cutscenes.animation_effects import ShipEntranceEffect

# 전투
from cutscenes.combat_effects import (
    BunkerCannonEffect, CombatMotionEffect, CannonShell
)
```

### game_logic/ 모듈

```python
# 게임 상태
from game_logic.game_state import (
    reset_game_data, handle_level_up, get_next_level_threshold
)

# 웨이브 관리
from game_logic.wave_manager import (
    start_wave, check_wave_clear, advance_to_next_wave,
    update_game_objects
)

# 스폰
from game_logic.spawning import (
    spawn_enemy, handle_spawning, spawn_gem,
    auto_place_turrets
)

# 이벤트
from game_logic.events import (
    update_random_event, get_active_event_modifiers
)

# 업그레이드
from game_logic.upgrades import (
    generate_tactical_options, handle_tactical_upgrade,
    trigger_ship_ability
)

# 헬퍼
from game_logic.helpers import (
    create_explosion_particles, create_hit_particles,
    create_shockwave, update_visual_effects
)
```

### ui_render/ 모듈

```python
# HUD
from ui_render.hud import draw_hud, draw_skill_indicators

# 메뉴
from ui_render.menus import (
    draw_pause_and_over_screens, draw_settings_menu
)

# 전투 UI
from ui_render.combat_ui import (
    draw_boss_health_bar, draw_random_event_ui
)

# 상점
from ui_render.shop import (
    draw_shop_screen, draw_tactical_menu
)

# 웨이브 UI
from ui_render.wave_ui import (
    draw_wave_prepare_screen, draw_wave_clear_screen,
    draw_victory_screen
)

# 헬퍼
from ui_render.helpers import (
    get_font, render_text_with_emoji, HPBarShake
)
```

---

## 🔍 자동 변환 스크립트

파일 전체를 한 번에 마이그레이션하려면:

```python
# migrate_imports.py
import re

def migrate_imports(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # objects 모듈 변환
    replacements = {
        r'from objects import Player': 'from entities.player import Player',
        r'from objects import Enemy': 'from entities.enemies import Enemy',
        r'from objects import Boss': 'from entities.enemies import Boss',
        r'from objects import Bullet': 'from entities.weapons import Bullet',
        r'from objects import Weapon': 'from entities.weapons import Weapon',
        # ... 추가 규칙
    }

    for pattern, replacement in replacements.items():
        content = re.sub(pattern, replacement, content)

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

# 사용
# migrate_imports('your_file.py')
```

---

## ⚠️ 주의사항

### 1. 동적 Import
```python
# Before (동적)
PolaroidMemoryEffect = __import__('objects', fromlist=['PolaroidMemoryEffect']).PolaroidMemoryEffect

# After (정적으로 변경)
from cutscenes.memory_effects import PolaroidMemoryEffect
```

### 2. 순환 Import 방지
```python
# ❌ 잘못된 예
# entities/player.py
from systems.combat_system import calculate_damage  # 상위 레벨 import

# ✅ 올바른 예
# entities/player.py에서는 하위 레벨만 import
from config.entities import PLAYER_MAX_HP
```

### 3. 패키지 레벨 Import
```python
# 둘 다 작동하지만, 구체적인 import 권장
from entities import Player  # OK
from entities.player import Player  # Better (명확함)
```

---

## 📚 참고 자료

- [REFACTORING_COMPLETE.md](REFACTORING_COMPLETE.md) - 전체 리팩토링 보고서
- Python Import System: https://docs.python.org/3/reference/import.html
- PEP 8 Style Guide: https://pep8.org/

---

**작성일**: 2026-01-02
**버전**: 1.0
