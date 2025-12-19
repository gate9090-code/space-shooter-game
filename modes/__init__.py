# modes/__init__.py
"""
게임 모드 패키지

각 모드는 GameMode 베이스 클래스를 상속하여 구현
- MainMenuMode: 메인 메뉴
- WaveMode: 웨이브 모드
- SiegeMode: 공성 모드
- StoryMode: 스토리 모드
- BaseHubMode: 기지 허브 모드 (신규)
- HangarMode: 격납고 모드 (신규)
- WorkshopMode: 정비소 모드 (신규)
- BriefingMode: 브리핑룸 모드 (신규)
"""

from .base_mode import GameMode, ModeConfig
from .main_menu_mode import MainMenuMode
from .wave_mode import WaveMode
from .siege_mode import SiegeMode
from .base_hub_mode import BaseHubMode
from .hangar_mode import HangarMode
from .workshop_mode import WorkshopMode
from .briefing_mode import BriefingMode

__all__ = [
    "GameMode",
    "ModeConfig",
    "MainMenuMode",
    "WaveMode",
    "SiegeMode",
    "BaseHubMode",
    "HangarMode",
    "WorkshopMode",
    "BriefingMode",
]
