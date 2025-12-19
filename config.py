# config.py

import pygame
from typing import Dict, Tuple, List, Optional, Callable
from pathlib import Path
import random
import math

# =========================================================
# 1. ⚙️ 코어 시스템 설정 (화면, 색상, FPS)
# =========================================================

# 초기 화면 크기 (main.py에서 실제 모니터 크기로 업데이트됨)
SCREEN_WIDTH_INIT = 1920  # FHD: 32타일 × 60px = 1920
SCREEN_HEIGHT_INIT = 1080  # FHD: 18타일 × 60px = 1080
FPS = 60

# 색상 정의 
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
BLUE = (0, 100, 255)  # 레벨업 툴팁 색상

# =========================================================
# 1.1 통일된 UI 레이아웃 설정
# =========================================================

UI_LAYOUT = {
    # 패널 크기
    "CONTENT_PANEL_WIDTH": 600,
    "CONTENT_PANEL_HEIGHT_RATIO": 0.60,  # 화면 높이의 60%

    # 탭 설정 (상단 가로 배치 통일)
    "TAB_HEIGHT": 42,
    "TAB_SPACING": 6,
    "TAB_Y": 90,  # 타이틀 아래
    "TAB_BORDER_RADIUS": 8,

    # 버튼 설정
    "BTN_HEIGHT": 45,
    "BTN_MARGIN": 30,
    "BTN_BACK_WIDTH": 100,
    "BTN_ACTION_WIDTH": 140,
    "BTN_BORDER_RADIUS": 10,

    # 타이틀 설정
    "TITLE_Y": 45,
    "CREDIT_BOX_WIDTH": 180,
    "CREDIT_BOX_HEIGHT": 42,

    # 마진/패딩
    "SCREEN_MARGIN": 30,
    "CONTENT_START_Y": 138,  # 탭 아래
    "PANEL_PADDING": 15,
    "ITEM_HEIGHT": 80,
    "ITEM_SPACING": 6,

    # 키보드 힌트
    "HINT_Y_OFFSET": 18,  # 화면 하단에서의 오프셋
}

# =========================================================
# 1.2 명도 기반 색상 체계 (WCAG 대비율 준수)
# =========================================================

# 배경 계층 (어두운 순서) - 명도 기반
BG_LEVELS = {
    "SCREEN": (12, 14, 22),      # L=5%  - 가장 어두운 화면 배경
    "PANEL": (22, 26, 38),       # L=10% - 패널 배경
    "CARD": (32, 38, 52),        # L=15% - 카드/아이템 배경
    "ELEVATED": (48, 55, 72),    # L=22% - 호버 상태
    "HIGHLIGHT": (60, 68, 88),   # L=28% - 선택/강조 상태
}

# 텍스트 계층 (밝은 순서) - 배경과의 대비 보장
TEXT_LEVELS = {
    "PRIMARY": (255, 255, 255),    # L=100% - 주요 텍스트 (대비 15:1+)
    "SECONDARY": (200, 205, 218),  # L=80%  - 보조 텍스트 (대비 10:1+)
    "TERTIARY": (155, 162, 178),   # L=62%  - 부가 정보 (대비 6:1+)
    "DISABLED": (105, 112, 128),   # L=44%  - 비활성 텍스트 (대비 4.5:1)
    "MUTED": (75, 82, 98),         # L=32%  - 힌트/플레이스홀더
}

# 상태별 강조 색상 (채도와 명도 조절)
STATE_COLORS = {
    # 성공/긍정 - 녹색 계열
    "SUCCESS": (72, 199, 116),        # 밝은 녹색
    "SUCCESS_DIM": (38, 95, 58),      # 어두운 녹색 (배경용)
    "SUCCESS_GLOW": (72, 199, 116, 60),

    # 위험/경고 - 빨강 계열
    "DANGER": (239, 83, 80),          # 밝은 빨강
    "DANGER_DIM": (115, 42, 40),      # 어두운 빨강 (배경용)
    "DANGER_GLOW": (239, 83, 80, 60),

    # 경고 - 주황/노랑 계열
    "WARNING": (255, 183, 77),        # 밝은 주황
    "WARNING_DIM": (128, 92, 38),     # 어두운 주황 (배경용)
    "WARNING_GLOW": (255, 183, 77, 60),

    # 정보/강조 - 파랑 계열
    "INFO": (100, 181, 246),          # 밝은 파랑
    "INFO_DIM": (48, 88, 120),        # 어두운 파랑 (배경용)
    "INFO_GLOW": (100, 181, 246, 60),

    # 프리미엄/골드
    "GOLD": (255, 215, 77),           # 밝은 골드
    "GOLD_DIM": (128, 108, 38),       # 어두운 골드 (배경용)
    "GOLD_GLOW": (255, 215, 77, 60),
}

# 비활성/잠금 상태 전용 색상 (대비율 4.5:1 보장)
LOCKED_COLORS = {
    "BG": (28, 30, 38),              # 탈색된 배경
    "TEXT": (125, 130, 145),         # 대비율 5:1 보장
    "BORDER": (52, 56, 68),          # 경계선
    "ICON": (90, 95, 108),           # 아이콘
}

# 인터랙션 상태별 색상
INTERACTION_STATES = {
    "NORMAL": {
        "bg": (*BG_LEVELS["CARD"], 180),
        "border": (58, 65, 82),
        "text": TEXT_LEVELS["SECONDARY"],
    },
    "HOVER": {
        "bg": (*BG_LEVELS["ELEVATED"], 220),
        "border": (95, 145, 200),
        "text": TEXT_LEVELS["PRIMARY"],
    },
    "SELECTED": {
        "bg": (45, 72, 105, 235),
        "border": (100, 175, 255),
        "text": TEXT_LEVELS["PRIMARY"],
    },
    "DISABLED": {
        "bg": (*LOCKED_COLORS["BG"], 160),
        "border": LOCKED_COLORS["BORDER"],
        "text": LOCKED_COLORS["TEXT"],
    },
}

# 카테고리별 통일 색상 (모든 모드에서 공유)
CATEGORY_COLORS = {
    # 공격/무기 계열 - 빨강/주황
    "ATTACK": (230, 105, 95),
    "WEAPON": (230, 105, 95),
    "WEAPON_BASIC": (230, 105, 95),

    # 방어/생존 계열 - 녹색
    "DEFENSE": (75, 190, 130),
    "SURVIVAL": (75, 190, 130),
    "REPAIR": (75, 190, 130),

    # 스탯/기본 계열 - 파랑
    "STATS": (95, 165, 235),
    "INFO": (95, 165, 235),

    # 특수/마법 계열 - 보라
    "SPECIAL": (175, 125, 225),
    "ELEMENTAL": (175, 125, 225),

    # 유틸리티/지원 계열 - 노랑/골드
    "UTILITY": (235, 195, 95),
    "SUPPORT": (110, 185, 255),

    # 고급/프리미엄 - 빨강+골드
    "ADVANCED": (255, 115, 105),
    "PREMIUM": (255, 205, 105),
}

# 개선된 UI 색상 팔레트 (기존 호환 + 확장)
UI_COLORS = {
    # 기본 색상 (기존 호환)
    "BACKGROUND": BG_LEVELS["SCREEN"],
    "PRIMARY": STATE_COLORS["GOLD"],
    "SECONDARY": STATE_COLORS["INFO"],
    "DANGER": STATE_COLORS["DANGER"],
    "DANGER_DARK": STATE_COLORS["DANGER_DIM"],
    "SUCCESS": STATE_COLORS["SUCCESS"],
    "WARNING": STATE_COLORS["WARNING"],

    # 텍스트 색상
    "TEXT_PRIMARY": TEXT_LEVELS["PRIMARY"],
    "TEXT_SECONDARY": TEXT_LEVELS["SECONDARY"],
    "TEXT_DISABLED": TEXT_LEVELS["DISABLED"],

    # 오버레이
    "OVERLAY": (0, 0, 0, 200),
    "OVERLAY_LIGHT": (0, 0, 0, 150),

    # 카드/패널
    "CARD_BG": (*BG_LEVELS["CARD"], 220),
    "CARD_BORDER": (95, 145, 200),
    "PANEL_BG": (*BG_LEVELS["PANEL"], 185),
    "PANEL_BORDER": (58, 65, 82),

    # HP 관련
    "HP_LOW": STATE_COLORS["DANGER"],
    "HP_NORMAL": STATE_COLORS["SUCCESS"],

    # 코인/EXP
    "COIN_GOLD": STATE_COLORS["GOLD"],
    "EXP_BLUE": STATE_COLORS["INFO"],

    # 탭 색상
    "TAB_BG_NORMAL": (*BG_LEVELS["CARD"], 160),
    "TAB_BG_HOVER": (*BG_LEVELS["ELEVATED"], 200),
    "TAB_BG_SELECTED": (55, 85, 125, 220),
    "TAB_BORDER_NORMAL": (58, 65, 82),
    "TAB_BORDER_HOVER": (95, 145, 200),
    "TAB_BORDER_SELECTED": (120, 180, 255),

    # 버튼 색상
    "BTN_BACK_NORMAL": (48, 52, 68, 200),
    "BTN_BACK_HOVER": (72, 78, 98, 225),
    "BTN_ACTION_NORMAL": (55, 125, 95, 210),
    "BTN_ACTION_HOVER": (72, 165, 125, 235),
    "BTN_DANGER_NORMAL": (145, 55, 55, 210),
    "BTN_DANGER_HOVER": (185, 72, 72, 235),
}

# 데미지 넘버 색상
DAMAGE_NUMBER_COLOR = (255, 255, 100)      # 노란색
DAMAGE_NUMBER_CRIT_COLOR = (255, 100, 50)  # 주황색 (크리티컬용)

# 폰트 크기 설정 (화면 높이 대비 비율)
FONT_SIZE_RATIOS = {
    "HUGE": 0.055,       # 메인 타이틀 (레벨업, 게임 오버)
    "LARGE": 0.035,      # 서브 타이틀, 메뉴 제목
    "MEDIUM": 0.020,     # 본문, 버튼, 화자 이름
    "SMALL": 0.016,      # HUD 정보, 대화 텍스트
    "TINY": 0.015,       # 상세 정보
}

# 이모지 폰트 (main.py에서 초기화됨)
EMOJI_FONTS = {}

# UI 아이콘 (이모지 - 이모지 폰트 필요)
UI_ICONS = {
    "PAUSED": "⏸",         # 일시정지
    "RESUME": "▶",          # 재개
    "SHOP": "🛒",          # 상점
    "QUIT": "🚪",          # 종료
    "GAME_OVER": "☠",       # 게임 오버
    "COIN": "💰",          # 코인
    "RESTART": "🔄",       # 재시작
    "LEVEL_UP": "⭐",      # 레벨업
    "INFO": "💡",          # 정보
    "FIRE_RATE": "🎯",     # 연사력
    "HP": "💚",            # 체력
    "REINCARNATION": "❤️",  # 환생
    "SPEED": "⚡",           # 속도
    "SWORD": "⚔️",         # 검
    "EXP": "✨",           # 경험치
    "GUN": "🚦",           # 총
}

# =========================================================
# 2. 🚦 게임 상태 관리 🔫
# =========================================================

GAME_STATE_RUNNING = 1  # 게임 실행 중
GAME_STATE_OVER = 2  # 게임 오버
GAME_STATE_PAUSED = 3  # 일시 정지
GAME_STATE_SHOP = 4  # 영구 업그레이드 상점
GAME_STATE_LEVEL_UP = 5  # 전술 레벨업 메뉴 (킬 기반)
GAME_STATE_WAVE_CLEAR = 6  # 웨이브 클리어 (휴식 시간)
GAME_STATE_WAVE_PREPARE = 7  # 웨이브 시작 대기 (클릭으로 시작)
GAME_STATE_VICTORY = 8  # 게임 승리 (모든 웨이브 클리어)
GAME_STATE_SETTINGS = 10  # 설정 메뉴 (F1 키로 열기/닫기)
GAME_STATE_QUIT_CONFIRM = 11  # 종료 확인 (ESC 키로 열기)

# Boss Rush Mode 설정
BOSS_RUSH_MODE = False  # 보스 러시 모드 활성화 여부
BOSS_RUSH_COMPLETED_WAVES = []  # 보스 러시에서 완료한 웨이브 목록

# Death Effect 설정
DEATH_EFFECT_ICONS = {
    "shatter": "assets/images/effects/shatter.png",
    "particle_burst": "assets/images/effects/particle_burst.png",
    "dissolve": "assets/images/effects/dissolve.png",
    "fade": "assets/images/effects/fade.png",
    "implode": "assets/images/effects/implode.png",
    "vortex": "assets/images/effects/vortex.png",
    "pixelate": "assets/images/effects/pixelate.png"
}

# 적 유형별 죽음 효과 매핑
ENEMY_TYPE_DEATH_EFFECTS = {
    "NORMAL": "shatter",        # 일반: 파편화
    "TANK": "implode",          # 탱크: 내파 (무거운 느낌)
    "RUNNER": "fade",           # 러너: 빠른 페이드 (빠른 적)
    "SUMMONER": "vortex",       # 소환사: 소용돌이 (마법적 느낌)
    "SHIELDED": "dissolve",     # 보호막: 디졸브 (보호막 소멸)
    "KAMIKAZE": "particle_burst", # 카미카제: 폭발 파티클
    "RESPAWNED": "pixelate",    # 리스폰: 픽셀화 (디지털 글리치)
}

DEATH_EFFECT_UI_HEIGHT = 105  # UI 패널 높이
DEATH_EFFECT_ICON_SIZE = 55  # 아이콘 크기
DEATH_EFFECT_ICON_SPACING = 75  # 아이콘 간격

# =========================================================
# 3. 🖼️ 이미지 및 폰트 설정
# =========================================================

# 💡 자원(Asset) 루트 폴더 정의 (assets)
ASSET_DIR = Path("assets")

# 폰트 폴더 정의 및 경로
FONT_DIR = ASSET_DIR / "fonts"
FONT_PATH = FONT_DIR / "NanumGothicBold.ttf"

# 배경 이미지 전용 폴더 정의 및 경로
BACKGROUND_DIR = ASSET_DIR / "images" / "backgrounds"
BACKGROUND_IMAGE_PATH = BACKGROUND_DIR / "bg_default.png"

# 스토리 모드 배경 이미지 (웨이브별 고유 배경)
STORY_BACKGROUNDS = {
    1: "story_bg_01.jpg",  # wallpaperbetter 이미지 (붉은색 테마)
}

# 동적 배경 시스템 설정 (웨이브 1-5용)
DYNAMIC_BACKGROUND_ENABLED = True
DYNAMIC_BACKGROUND_IMAGE = "story_bg_01.jpg"  # 기본 이미지
DYNAMIC_BACKGROUND_WAVES = [1, 2, 3, 4, 5]  # 동적 배경 적용 웨이브

# 웨이브별 색상 테마 (Hue shift, saturation, brightness)
WAVE_COLOR_THEMES = {
    1: {"name": "Crimson Fire", "hue": 0, "sat": 1.0, "bright": 1.0},
    2: {"name": "Blazing Orange", "hue": 30, "sat": 1.1, "bright": 1.05},
    3: {"name": "Golden Dawn", "hue": 60, "sat": 1.0, "bright": 1.1},
    4: {"name": "Frozen Cyan", "hue": 180, "sat": 1.0, "bright": 1.0},
    5: {"name": "Mystic Purple", "hue": 270, "sat": 1.1, "bright": 0.95},
}

# 적 처치 시 배경 펄스 효과 설정
KILL_PULSE_ENABLED = True
KILL_PULSE_BASE_INTENSITY = 30  # 기본 강도 (0-255)
KILL_PULSE_MAX_INTENSITY = 150  # 최대 강도
KILL_PULSE_DECAY_RATE = 200  # 초당 감소량

# 웨이브별 배경 이미지 풀 설정 (Option 4: Hybrid)
# 각 웨이브는 지정된 배경 번호 풀에서 랜덤 선택
# 스토리 배경이 있는 웨이브는 스토리 배경 우선 사용
WAVE_BACKGROUND_POOLS = {
    # Act 1: 기초
    1: list(range(1, 9)),      # bg1.jpg~bg8.jpg (기존 복원)
    2: list(range(1, 9)),
    3: list(range(9, 17)),     # bg9.jpg~bg16.jpg
    4: list(range(9, 17)),
    5: [37, 38],               # bg37.jpg~bg38.jpg (미니보스)

    # Act 2: 중반
    6: list(range(17, 25)),    # bg17.jpg~bg24.jpg
    7: list(range(17, 25)),
    8: list(range(25, 37)),    # bg25.jpg~bg36.jpg
    9: list(range(25, 37)),
    10: [39, 40],              # bg39.jpg~bg40.jpg (중간보스)

    # Act 3: 후반
    11: list(range(1, 17)),    # 혼합 (재사용)
    12: list(range(9, 25)),
    13: list(range(17, 37)),
    14: list(range(25, 37)),
    15: [37, 38, 39],          # 보스 혼합 (강력보스)

    # Act 4: 최종
    16: list(range(25, 40)),   # 어두운 배경 위주
    17: list(range(30, 40)),
    18: list(range(33, 40)),
    19: list(range(35, 40)),
    20: [39, 40],              # bg39.jpg~bg40.jpg (최종보스)
}

# 웨이브별 배경 전환 효과 설정
WAVE_TRANSITION_EFFECTS = {
    1: "fade_in",           # 부드러운 페이드 인
    2: "slide_horizontal",  # 좌→우 슬라이드
    3: "zoom_in",           # 중심에서 확대
    4: "cross_fade",        # 교차 페이드
    5: "flash_zoom",        # 번쩍임 + 확대 (보스)
    6: "vertical_wipe",     # 위→아래 닦아내기
    7: "circular_reveal",   # 원형 확장
    8: "pixelate",          # 픽셀 분해→재조립
    9: "shake_fade",        # 흔들림 + 페이드
    10: "multi_flash",      # 다중 번쩍임 (최종 보스)
}

# 배경 전환 지속 시간 (초)
BACKGROUND_TRANSITION_DURATION = 2.0

# 무한 스크롤 배경 설정 (웨이브 진행 중 배경 이동 효과 - 아래에서 위로)
CONTINUOUS_SLIDE_ENABLED = False  # 스크롤 비활성화
BACKGROUND_SCROLL_SPEED = 600.0  # 스크롤 속도 (픽셀/초) - 매우 빠름

# 일반 객체 이미지 폴더 및 경로
IMAGE_DIR = ASSET_DIR / "images"
PLAYER_SHIP_IMAGE_PATH = IMAGE_DIR / "characters" / "player" / "player_ship.png"
ENEMY_SHIP_IMAGE_PATH = IMAGE_DIR / "characters" / "enemies" / "enemy_ship.png"
ENEMY_SHIP_BURN_IMAGE_PATH = IMAGE_DIR / "characters" / "enemies" / "enemy_ship_burn.png"
PLAYER_BULLET_IMAGE_PATH = IMAGE_DIR / "projectiles" / "player_bullet.png"
IMPACT_FX_IMAGE_PATH = IMAGE_DIR / "effects" / "impact_fx.png"
EXPLOSION_IMAGE_PATH = IMAGE_DIR / "effects" / "explosion.png"
METEOR_HEAD_IMAGE_PATH = IMAGE_DIR / "effects" / "meteor_head.png"
METEOR_TRAIL_IMAGE_PATH = IMAGE_DIR / "effects" / "meteor_trail.png"
COIN_GEM_IMAGE_PATH = IMAGE_DIR / "items" / "coin_gem.png"
GEM_HP_IMAGE_PATH = IMAGE_DIR / "items" / "gem_hp.png"

# 스킬 이미지 폴더
SKILL_IMAGE_DIR = IMAGE_DIR / "skills"
STATIC_FIELD_IMAGE_PATH = SKILL_IMAGE_DIR / "Static Field.png"

# 메뉴 아이콘 폴더
MENU_ICON_DIR = IMAGE_DIR / "ui"

# 웨이브 전환 이미지
WAVE_HERO_IMAGE_PATH = IMAGE_DIR / "ui" / "wave_hero.jpg"

# =========================================================
# 3.5. 🔊 사운드 및 음악 설정
# =========================================================

# 사운드 폴더 정의
SOUND_DIR = ASSET_DIR / "sounds"
BGM_DIR = SOUND_DIR / "bgm"
SFX_DIR = SOUND_DIR / "sfx"

# 배경 음악 (BGM) 파일 경로
BGM_FILES = {
    "normal": BGM_DIR / "wave_normal.mp3",      # 일반 웨이브 BGM
    "boss": BGM_DIR / "wave_boss.mp3",          # 보스 웨이브 BGM (Wave 5)
    "final_boss": BGM_DIR / "wave_final.mp3",   # 최종 보스 BGM (Wave 10)
    "victory": BGM_DIR / "victory.mp3",         # 승리 BGM
}

# 효과음 (SFX) 파일 경로
SFX_FILES = {
    "shoot": SFX_DIR / "shoot.wav",             # 총알 발사
    "enemy_hit": SFX_DIR / "enemy_hit.wav",     # 적 피격
    "enemy_death": SFX_DIR / "enemy_death.wav", # 적 사망
    "explosion": SFX_DIR / "explosion.wav",     # 폭발
    "coin_pickup": SFX_DIR / "coin_pickup.wav", # 코인 획득
    "heal_pickup": SFX_DIR / "heal_pickup.wav", # 힐 아이템 획득
    "level_up": SFX_DIR / "level_up.wav",       # 레벨업
    "boss_spawn": SFX_DIR / "boss_spawn.wav",   # 보스 등장
    "player_hit": SFX_DIR / "player_hit.wav",   # 플레이어 피격
    "wave_clear": SFX_DIR / "wave_clear.wav",   # 웨이브 클리어
    "button_click": SFX_DIR / "button_click.wav", # 버튼 클릭
    # Ship Ability SFX
    "ability_evasion": SFX_DIR / "ability_evasion.wav",   # INTERCEPTOR 회피
    "ability_bomb": SFX_DIR / "ability_bomb.wav",         # BOMBER 폭탄
    "ability_cloak": SFX_DIR / "ability_cloak.wav",       # STEALTH 은신
    "ability_shield": SFX_DIR / "ability_shield.wav",     # TITAN 쉴드
}

# 웨이브별 BGM 매핑
WAVE_BGM_MAPPING = {
    # Act 1
    1: "normal",
    2: "normal",
    3: "normal",
    4: "normal",
    5: "boss",        # 미니보스

    # Act 2
    6: "normal",
    7: "normal",
    8: "normal",
    9: "normal",
    10: "boss",       # 중간보스

    # Act 3
    11: "normal",
    12: "normal",
    13: "normal",
    14: "normal",
    15: "boss",       # 강력보스

    # Act 4
    16: "normal",
    17: "normal",
    18: "normal",
    19: "normal",
    20: "final_boss", # 최종보스
}

# 사운드 볼륨 설정 (0.0 ~ 1.0)
DEFAULT_BGM_VOLUME = 0.2   # 배경 음악 볼륨
DEFAULT_SFX_VOLUME = 0.5   # 효과음 볼륨

# 사운드 활성화 기본값
SOUND_ENABLED = True       # 사운드 시스템 활성화 여부


# 화면 높이에 대한 객체 이미지 크기 비율 (0.0 ~ 1.0)
IMAGE_SIZE_RATIOS = {
    "PLAYER": 0.14,  # 플레이어 이미지 크기 비율
    "ENEMY": 0.11, # 적 이미지 크기 비율
    "BULLET": 0.035,  # 총알 이미지 크기 비율 (720p 기준 약 25픽셀)
    "COINGEM": 0.05,  # 코인 젬 이미지 크기 비율
    "GEMHP": 0.05,  # HP 젬 이미지 크기 비율
    "HITIMPACT": 0.13, # 충돌 이펙트 이미지 크기 비율
}

# =========================================================
# 🎨 원근감 시스템 (Perspective System)
# =========================================================
# Y-Position 기반 원근감 표현 설정

PERSPECTIVE_ENABLED = True  # 원근감 시스템 활성화 여부

# 스케일 범위 (화면 상단 → 하단)
PERSPECTIVE_SCALE_MIN = 0.5  # 화면 상단 최소 크기 (60%)
PERSPECTIVE_SCALE_MAX = 1.3  # 화면 하단 최대 크기 (120%)

# 적용 대상별 설정
PERSPECTIVE_APPLY_TO_ENEMIES = True   # 적에게 적용
PERSPECTIVE_APPLY_TO_BULLETS = True   # 총알에게 적용
PERSPECTIVE_APPLY_TO_GEMS = True      # 젬/코인에게 적용
PERSPECTIVE_APPLY_TO_PLAYER = True    # 플레이어에게 적용

# 추가 효과 (선택적)
PERSPECTIVE_ALPHA_ENABLED = False     # 투명도 변화 활성화
PERSPECTIVE_ALPHA_MIN = 200           # 화면 상단 투명도 (200/255)
PERSPECTIVE_ALPHA_MAX = 255           # 화면 하단 투명도 (255/255)

# =========================================================
# 4. 🧑 플레이어 스탯 (PLAYER)
# =========================================================

PLAYER_BASE_SPEED = 300  # 픽셀/초 (300 → 260 밸런스 조정)
PLAYER_HITBOX_RATIO = 0.8  # 이미지 크기 대비 히트박스 비율
PLAYER_BASE_HP = 1200 # 플레이어 초기 기본 체력 (100 → 밸런스 조정)

# 궁극기 시스템 설정 (Q 키)
ULTIMATE_SETTINGS = {
    # 공통 설정
    "cooldown": 45.0,  # 궁극기 쿨다운 (초)
    "charge_time": 5.0,  # 게임 시작 후 첫 궁극기 충전 시간 (초)

    # 궁극기 종류별 설정
    "NOVA_BLAST": {
        "name": "Nova Blast",
        "description": "Massive explosion around player",
        "radius": 400,  # 폭발 반경
        "damage": 200,  # 폭발 데미지
        "knockback": 300,  # 넉백 거리
        "screen_shake": 20,  # 화면 흔들림 강도
        "duration": 0.5,  # 폭발 지속 시간
        "color": (255, 200, 50),  # 주황색 폭발
    },
    "TIME_FREEZE": {
        "name": "Time Freeze",
        "description": "Freeze all enemies for 5 seconds",
        "duration": 5.0,  # 시간 정지 지속 시간
        "slow_factor": 0.0,  # 적 속도 배율 (0 = 완전 정지)
        "color": (100, 200, 255),  # 파란색 효과
        "screen_tint": (50, 100, 150, 100),  # 화면 색조 (RGBA)
    },
    "ORBITAL_STRIKE": {
        "name": "Orbital Strike",
        "description": "Call down laser strikes on all enemies",
        "strike_count": 15,  # 레이저 공격 횟수
        "damage_per_strike": 80,  # 레이저당 데미지
        "strike_interval": 0.15,  # 레이저 간격 (초)
        "strike_radius": 60,  # 레이저 반경
        "color": (255, 50, 50),  # 빨간색 레이저
        "beam_duration": 0.3,  # 레이저 지속 시간
    },
}

# =========================================================
# 5. 🔫 무기 및 적 스탯 (WEAPON / ENEMY)
# =========================================================

BULLET_SPEED = 800  # 픽셀/초
BULLET_DAMAGE_BASE = 20.0  # 기본 총알 데미지 (12.0 → 10.0 밸런스 조정)
BULLET_HITBOX_RATIO = 0.3  # 총알 이미지 대비 히트박스 비율
WEAPON_COOLDOWN_BASE = 1.0  # 기본 발사 쿨다운 (초)
PIERCING_HIT_COUNT = 3 # 관통 총알의 최대 관통 횟수(50)

ENEMY_BASE_HP = 80.0  # 기본 적 체력 
ENEMY_BASE_SPEED = 120  # 기본 적 이동 속도 (150 → 120으로 낮춤)
ENEMY_ATTACK_DAMAGE = 10.0 # 적 공격 데미지 (10 )
ENEMY_ATTACK_COOLDOWN = 2.0 # 적 공격 쿨다운 (미사용일 수 있음)
ENEMY_HITBOX_RATIO = 0.7  # 적 이미지 대비 히트박스 비율

# === 적 타입 시스템 (5종) ===
# Wave 6+부터 점진적으로 등장하는 특수 적
ENEMY_TYPES = {
    "NORMAL": {
        "name": "일반",
        "hp_mult": 1.0,
        "speed_mult": 1.0,
        "damage_mult": 1.0,
        "coin_mult": 1.0,
        "color_tint": (255, 255, 255),  # 원본 색상
        "size_mult": 1.0,
        "unlock_wave": 1,  # 처음부터 등장
    },
    "TANK": {
        "name": "탱크",
        "hp_mult": 3.0,  # 체력 3배
        "speed_mult": 0.5,  # 속도 0.5배
        "damage_mult": 1.5,  # 데미지 1.5배
        "coin_mult": 2.0,  # 코인 2배
        "color_tint": (100, 255, 100),  # 녹색 계열
        "size_mult": 1.3,  # 크기 1.3배
        "unlock_wave": 6,
    },
    "RUNNER": {
        "name": "러너",
        "hp_mult": 0.5,  # 체력 0.5배
        "speed_mult": 2.0,  # 속도 2배
        "damage_mult": 0.7,  # 데미지 0.7배
        "coin_mult": 1.5,  # 코인 1.5배
        "color_tint": (255, 255, 100),  # 노란색 계열
        "size_mult": 0.8,  # 크기 0.8배
        "unlock_wave": 7,
    },
    "SUMMONER": {
        "name": "소환사",
        "hp_mult": 1.2,  # 체력 1.2배
        "speed_mult": 0.8,  # 속도 0.8배
        "damage_mult": 0.8,  # 데미지 0.8배
        "coin_mult": 2.5,  # 코인 2.5배
        "color_tint": (200, 100, 255),  # 보라색 계열
        "size_mult": 1.1,  # 크기 1.1배
        "unlock_wave": 9,
        "summon_on_death": True,  # 사망 시 작은 적 2마리 소환
        "summon_count": 2,
    },
    "SHIELDED": {
        "name": "보호막",
        "hp_mult": 1.5,  # 체력 1.5배
        "speed_mult": 0.9,  # 속도 0.9배
        "damage_mult": 1.0,  # 데미지 1.0배
        "coin_mult": 2.0,  # 코인 2배
        "color_tint": (100, 200, 255),  # 파란색 계열
        "size_mult": 1.0,  # 크기 1.0배
        "unlock_wave": 11,
        "has_shield": True,  # 재생 보호막 (초당 최대 HP의 2% 회복)
        "shield_regen_rate": 0.02,  # 초당 2% 회복
    },
    "KAMIKAZE": {
        "name": "카미카제",
        "hp_mult": 0.8,  # 체력 0.8배
        "speed_mult": 1.5,  # 속도 1.5배
        "damage_mult": 3.0,  # 접촉 시 3배 데미지
        "coin_mult": 1.5,  # 코인 1.5배
        "color_tint": (255, 100, 100),  # 빨간색 계열
        "size_mult": 0.9,  # 크기 0.9배
        "unlock_wave": 13,
        "explode_on_contact": True,  # 플레이어 접촉 시 자폭
        "explosion_damage": 20.0,  # 자폭 데미지
        "explosion_radius": 100,  # 폭발 범위 (시각 효과용)
    },
    "RESPAWNED": {
        "name": "리스폰",
        "hp_mult": 1.0,  # 체력 1.0배
        "speed_mult": 1.0,  # 속도 1.0배
        "damage_mult": 1.0,  # 데미지 1.0배
        "coin_mult": 1.5,  # 코인 1.5배 (보너스)
        "color_tint": (255, 80, 80),  # 붉은색
        "size_mult": 1.0,  # 크기 1.0배
        "unlock_wave": 1,  # 모든 웨이브에서 등장 가능
        "is_respawned": True,  # 리스폰 적 플래그
    },
}

# 웨이브별 적 타입 분포 (확률)
WAVE_ENEMY_TYPE_DISTRIBUTION = {
    # Act 1 (Wave 1-5): 일반만
    1: {"NORMAL": 1.0},
    2: {"NORMAL": 1.0},
    3: {"NORMAL": 1.0},
    4: {"NORMAL": 1.0},
    5: {"NORMAL": 1.0},  # 보스

    # Act 2 (Wave 6-10): TANK, RUNNER 등장
    6: {"NORMAL": 0.7, "TANK": 0.3},
    7: {"NORMAL": 0.6, "TANK": 0.2, "RUNNER": 0.2},
    8: {"NORMAL": 0.5, "TANK": 0.25, "RUNNER": 0.25},
    9: {"NORMAL": 0.4, "TANK": 0.2, "RUNNER": 0.2, "SUMMONER": 0.2},
    10: {"NORMAL": 1.0},  # 보스

    # Act 3 (Wave 11-15): SHIELDED, KAMIKAZE 등장
    11: {"NORMAL": 0.3, "TANK": 0.2, "RUNNER": 0.2, "SUMMONER": 0.15, "SHIELDED": 0.15},
    12: {"NORMAL": 0.25, "TANK": 0.15, "RUNNER": 0.2, "SUMMONER": 0.15, "SHIELDED": 0.15, "KAMIKAZE": 0.1},
    13: {"NORMAL": 0.2, "TANK": 0.15, "RUNNER": 0.2, "SUMMONER": 0.15, "SHIELDED": 0.15, "KAMIKAZE": 0.15},
    14: {"NORMAL": 0.15, "TANK": 0.15, "RUNNER": 0.2, "SUMMONER": 0.2, "SHIELDED": 0.15, "KAMIKAZE": 0.15},
    15: {"NORMAL": 1.0},  # 보스

    # Act 4 (Wave 16-20): 모든 타입 혼합
    16: {"NORMAL": 0.1, "TANK": 0.2, "RUNNER": 0.2, "SUMMONER": 0.2, "SHIELDED": 0.15, "KAMIKAZE": 0.15},
    17: {"NORMAL": 0.1, "TANK": 0.2, "RUNNER": 0.2, "SUMMONER": 0.2, "SHIELDED": 0.15, "KAMIKAZE": 0.15},
    18: {"NORMAL": 0.05, "TANK": 0.2, "RUNNER": 0.2, "SUMMONER": 0.2, "SHIELDED": 0.2, "KAMIKAZE": 0.15},
    19: {"NORMAL": 0.05, "TANK": 0.15, "RUNNER": 0.2, "SUMMONER": 0.2, "SHIELDED": 0.2, "KAMIKAZE": 0.2},
    20: {"NORMAL": 1.0},  # 최종 보스
}

# 적 분리 행동 설정 (밀집 방지)
ENEMY_SEPARATION_RADIUS = 100 # 다른 적과 유지할 최소 거리 (픽셀) - 60에서 100로 증가
ENEMY_SEPARATION_STRENGTH = 1.2  # 분리 행동 강도 (0.5에서 1.2로 증가, 높을수록 강함)

# 적 포위 공격 설정
ENEMY_FLANK_ENABLED = True  # 포위 공격 활성화
ENEMY_FLANK_DISTANCE = 200  # 포위 공격 시작 거리 (플레이어로부터)
ENEMY_FLANK_ANGLE_SPREAD = 30  # 포위 각도 분산 (도)

# === 보스 패턴 시스템 ===
BOSS_PATTERN_SETTINGS = {
    # 페이즈 시스템: HP 구간별 행동 변화
    "PHASE_THRESHOLDS": [1.0, 0.66, 0.33, 0.0],  # 100%, 66%, 33%, 0%

    # 패턴별 설정
    "CIRCLE_STRAFE": {
        "orbit_radius": 250,  # 궤도 반경
        "orbit_speed": 1.5,  # 회전 속도 (rad/s)
        "duration": 5.0,  # 패턴 지속 시간
    },
    "CHARGE_ATTACK": {
        "charge_speed_mult": 3.0,  # 돌진 속도 배율
        "charge_duration": 1.5,  # 돌진 지속 시간
        "cooldown": 8.0,  # 돌진 쿨다운
    },
    "BERSERK": {
        "speed_mult": 1.8,  # 광폭화 속도 배율
        "damage_mult": 1.5,  # 광폭화 데미지 배율
        "hp_threshold": 0.25,  # HP 25% 이하에서 활성화
    },
    "SUMMON_MINIONS": {
        "summon_count": {5: 2, 10: 3, 15: 4, 20: 5},  # 웨이브별 소환 수
        "summon_cooldown": 15.0,  # 소환 쿨다운
        "minion_hp_ratio": 0.15,  # 미니언 HP = 보스 최대 HP * 15%
    },
    "BURN_ATTACK": {
        "projectile_count": 8,  # 발사되는 burn 발사체 수 (사방으로)
        "fire_interval": 5.0,  # 발사 주기 (초)
        "projectile_speed": 200.0,  # 발사체 이동 속도 (픽셀/초)
        "damage": 15.0,  # 발사체 충돌 시 데미지
        "projectile_size": 40,  # 발사체 이미지 크기 (픽셀)
        "lifetime": 5.0,  # 발사체 수명 (초)
    },
}

# =========================================================
# 6. 💎 아이템/젬 드롭 설정 (ITEM / GEM)
# =========================================================
BASE_COIN_DROP_PER_KILL = 5  # 적 처치 시 기본 코인 드롭량 (1 → 5)
HEAL_AMOUNT = 15  # 힐링 아이템 획득 시 회복량
GEM_HITBOX_RATIO = 0.8  # 젬 이미지 대비 히트박스 비율

ENEMY_SPAWN_INTERVAL = 1.5  # 적 스폰 간격 (초)

# 웨이브별 코인 드롭 배율 (웨이브 진행 시 보상 증가)
WAVE_COIN_MULTIPLIER = {
    1: 1.0, 2: 1.0, 3: 1.0, 4: 1.0, 5: 2.0,      # Act 1 (보스 2배)
    6: 1.2, 7: 1.2, 8: 1.2, 9: 1.2, 10: 3.0,     # Act 2 (보스 3배)
    11: 1.5, 12: 1.5, 13: 1.5, 14: 1.5, 15: 4.0, # Act 3 (보스 4배)
    16: 2.0, 17: 2.0, 18: 2.0, 19: 2.0, 20: 5.0, # Act 4 (보스 5배)
}

# 캠페인 초기 크레딧
INITIAL_CAMPAIGN_CREDITS = 500

# =========================================================
# 6.5. 🌊 웨이브 시스템 (WAVE SYSTEM)
# =========================================================

# 전체 웨이브 설정
TOTAL_WAVES = 20  # 총 웨이브 수
BOSS_WAVES = [5, 10, 15, 20]  # 보스 웨이브

# 웨이브별 난이도 스케일링 (20 Wave System)
WAVE_SCALING = {
    # === Act 1: 기초 학습 (Wave 1-5) ===
    1: {"hp_mult": 1.0,   "speed_mult": 0.8,  "spawn_rate": 0.8,  "target_kills": 10,  "chase_prob": 0.3,  "damage_mult": 1.0},   # +5
    2: {"hp_mult": 1.3,   "speed_mult": 0.9,  "spawn_rate": 1.0,  "target_kills": 11,  "chase_prob": 0.4,  "damage_mult": 1.0},   # +5
    3: {"hp_mult": 1.6,   "speed_mult": 1.0,  "spawn_rate": 1.1,  "target_kills": 12,  "chase_prob": 0.5,  "damage_mult": 1.0},   # +5
    4: {"hp_mult": 2.0,   "speed_mult": 1.1,  "spawn_rate": 1.2,  "target_kills": 13,  "chase_prob": 0.6,  "damage_mult": 1.0},   # +5
    5: {"hp_mult": 30.0,  "speed_mult": 1.5,  "spawn_rate": 1.0,  "target_kills": 3,   "chase_prob": 1.0,  "damage_mult": 2.0},   # 미니보스 (유지)

    # === Act 2: 스킬 조합 (Wave 6-10) ===
    6: {"hp_mult": 2.5,   "speed_mult": 1.2,  "spawn_rate": 1.3,  "target_kills": 14,  "chase_prob": 0.7,  "damage_mult": 1.0},   # +5
    7: {"hp_mult": 3.0,   "speed_mult": 1.3,  "spawn_rate": 1.4,  "target_kills": 15,  "chase_prob": 0.75, "damage_mult": 1.0},   # +5
    8: {"hp_mult": 4.0,   "speed_mult": 1.4,  "spawn_rate": 1.5,  "target_kills": 16,  "chase_prob": 0.8,  "damage_mult": 1.0},   # +5
    9: {"hp_mult": 5.0,   "speed_mult": 1.5,  "spawn_rate": 1.6,  "target_kills": 17,  "chase_prob": 0.85, "damage_mult": 1.0},   # +5
    10: {"hp_mult": 60.0, "speed_mult": 1.8,  "spawn_rate": 1.0,  "target_kills": 1,   "chase_prob": 1.0,  "damage_mult": 2.5},   # 중간보스 (유지)

    # === Act 3: 엘리트 구간 (Wave 11-15) ===
    11: {"hp_mult": 6.5,  "speed_mult": 1.6,  "spawn_rate": 1.7,  "target_kills": 18,  "chase_prob": 0.85, "damage_mult": 1.2},   # +5
    12: {"hp_mult": 8.0,  "speed_mult": 1.7,  "spawn_rate": 1.8,  "target_kills": 19,  "chase_prob": 0.88, "damage_mult": 1.2},   # +5
    13: {"hp_mult": 10.0, "speed_mult": 1.8,  "spawn_rate": 1.9,  "target_kills": 20,  "chase_prob": 0.9,  "damage_mult": 1.3},   # +5
    14: {"hp_mult": 12.5, "speed_mult": 1.9,  "spawn_rate": 2.0,  "target_kills": 21,  "chase_prob": 0.92, "damage_mult": 1.3},   # +5
    15: {"hp_mult": 90.0, "speed_mult": 2.3,  "spawn_rate": 1.5,  "target_kills": 3,   "chase_prob": 1.0,  "damage_mult": 3.0},   # 강력보스 (유지)

    # === Act 4: 지옥 구간 (Wave 16-20) ===
    16: {"hp_mult": 15.0, "speed_mult": 2.0,  "spawn_rate": 2.1,  "target_kills": 23,  "chase_prob": 0.93, "damage_mult": 1.4},   # +5
    17: {"hp_mult": 18.0, "speed_mult": 2.1,  "spawn_rate": 2.2,  "target_kills": 25,  "chase_prob": 0.95, "damage_mult": 1.5},   # +5
    18: {"hp_mult": 22.0, "speed_mult": 2.2,  "spawn_rate": 2.3,  "target_kills": 27,  "chase_prob": 0.97, "damage_mult": 1.6},   # +5
    19: {"hp_mult": 27.0, "speed_mult": 2.3,  "spawn_rate": 2.4,  "target_kills": 30,  "chase_prob": 0.98, "damage_mult": 1.7},   # +5
    20: {"hp_mult": 120.0,"speed_mult": 2.5,  "spawn_rate": 1.0,  "target_kills": 1,   "chase_prob": 1.0,  "damage_mult": 3.5},   # 최종보스 (유지)
}


# =========================================================
# 6.5.1. 💰 웨이브 클리어 크레딧 보상 (Option B: 정비소 통합)
# =========================================================
# 웨이브 클리어 시 레벨업 대신 크레딧 보상 지급
# 모든 업그레이드는 기지의 정비소(Workshop)에서 구매

WAVE_CLEAR_CREDITS = {
    # Act 1: 기초 학습 (Wave 1-5) - 초반 보상 증가
    1: 150,   2: 180,   3: 220,   4: 280,   5: 800,   # 보스 보너스
    # Act 2: 스킬 조합 (Wave 6-10)
    6: 300,   7: 350,   8: 400,   9: 500,   10: 1200,  # 보스 보너스
    # Act 3: 엘리트 구간 (Wave 11-15)
    11: 500,  12: 600,  13: 700,  14: 800,  15: 2000, # 보스 보너스
    # Act 4: 지옥 구간 (Wave 16-20)
    16: 900,  17: 1000, 18: 1200, 19: 1500, 20: 3000, # 최종 보스 보너스
}

# 크레딧 보상 배율 (난이도별)
CREDIT_DIFFICULTY_MULTIPLIER = {
    "easy": 1.5,
    "normal": 1.0,
    "hard": 0.8,
}

# 웨이브별 난이도 스케일링
"""
WAVE_SCALING = {
    1: {"hp_mult": 1.0,   "speed_mult": 0.8,   "spawn_rate": 0.8,   "target_kills": 15,  "chase_prob": 0.3,  "damage_mult": 1.0},
    2: {"hp_mult": 1.2,   "speed_mult": 0.9,   "spawn_rate": 1.0,   "target_kills": 20,  "chase_prob": 0.4,  "damage_mult": 1.0},
    3: {"hp_mult": 1.5,   "speed_mult": 1.0,   "spawn_rate": 1.2,   "target_kills": 25,  "chase_prob": 0.5,  "damage_mult": 1.0},
    4: {"hp_mult": 2.0,   "speed_mult": 1.1,   "spawn_rate": 1.4,   "target_kills": 30,  "chase_prob": 0.6,  "damage_mult": 1.0},
    5: {"hp_mult": 50.0,  "speed_mult": 2.0,   "spawn_rate": 1.5,   "target_kills": 3,   "chase_prob": 1.0,  "damage_mult": 10.0},  # 보스 (3마리, 항상 추적, 강화)
    6: {"hp_mult": 3.0,   "speed_mult": 1.3,   "spawn_rate": 1.8,   "target_kills": 35,  "chase_prob": 0.7,  "damage_mult": 1.0},
    7: {"hp_mult": 4.0,   "speed_mult": 1.4,   "spawn_rate": 2.0,   "target_kills": 40,  "chase_prob": 0.75, "damage_mult": 1.0},
    8: {"hp_mult": 5.5,   "speed_mult": 1.5,   "spawn_rate": 2.2,   "target_kills": 45,  "chase_prob": 0.8,  "damage_mult": 1.0},
    9: {"hp_mult": 7.0,   "speed_mult": 1.6,   "spawn_rate": 2.4,   "target_kills": 50,  "chase_prob": 0.9,  "damage_mult": 1.0},
    10: {"hp_mult": 100.0, "speed_mult": 3.0,  "spawn_rate": 2.5,   "target_kills": 1,   "chase_prob": 1.0,  "damage_mult": 25.0}, # 최종 보스 (항상 추적, 극강화)
}
"""


# 웨이브 설명 (UI에 표시)
WAVE_DESCRIPTIONS = {
    # Act 1: 기초 학습
    1: "🎯  Tutorial Wave - Get Ready!",
    2: "⚔️  Wave 2 - Enemies Incoming",
    3: "⚠️  Wave 3 - Heavy Assault",
    4: "🔥  Wave 4 - Increasing Threat",
    5: "👹  MINI BOSS - The Swarm Queen",

    # Act 2: 스킬 조합
    6: "💀  Wave 6 - Elite Forces",
    7: "⚡  Wave 7 - Lightning Fast",
    8: "🌪️  Wave 8 - Chaos Unleashed",
    9: "☠️  Wave 9 - Dark Rising",
    10: "🔴  BOSS WAVE - The Void Core",

    # Act 3: 엘리트 구간
    11: "🎭  Wave 11 - Shadow Realm",
    12: "💥  Wave 12 - Explosive Mayhem",
    13: "🌊  Wave 13 - Tidal Fury",
    14: "🔮  Wave 14 - Arcane Power",
    15: "👑  BOSS WAVE - The Nightmare King",

    # Act 4: 지옥 구간
    16: "🔥  Wave 16 - Hell's Gate",
    17: "💀  Wave 17 - Death's Domain",
    18: "⚫  Wave 18 - Void Abyss",
    19: "🌌  Wave 19 - Final Stand",
    20: "👿  FINAL BOSS - The Destroyer",
}

# =========================================================
# 6.8. ✨ 시각 효과 설정 (VISUAL EFFECTS)
# =========================================================

# 파티클 효과 설정
PARTICLE_SETTINGS = {
    "EXPLOSION": {
        "count": 12,  # 폭발 시 생성되는 파티클 수
        "colors": [(255, 150, 50), (255, 100, 0), (255, 50, 0)],  # 주황/빨강 그라데이션
        "size_range": (5, 18),  # 파티클 크기 범위
        "lifetime_range": (0.3, 0.7),  # 생명 시간 범위
        "speed_range": (100, 300),  # 속도 범위
    },
    "HIT": {
        "count": 5,  # 피격 시 파티클 수
        "colors": [(255, 255, 100), (255, 200, 50)],  # 노란색
        "size_range": (2, 5),
        "lifetime_range": (0.2, 0.4),
        "speed_range": (50, 150),
    },
    "BOSS_HIT": {
        "count": 20,  # 보스 피격 시 파티클 수
        "colors": [(255, 50, 50), (255, 100, 100), (255, 150, 150)],  # 빨간색
        "size_range": (4, 10),
        "lifetime_range": (0.5, 1.0),
        "speed_range": (150, 400),
    },
}

# 충격파 효과 설정
SHOCKWAVE_SETTINGS = {
    "BOSS_SPAWN": {
        "max_radius": 300,
        "duration": 1.0,
        "color": (100, 150, 255),  # 파란색
        "width": 5,
    },
    "BOSS_DEATH": {
        "max_radius": 500,
        "duration": 1.5,
        "color": (255, 50, 50),  # 빨간색
        "width": 8,
    },
    "BOSS_ATTACK": {
        "max_radius": 200,
        "duration": 0.5,
        "color": (255, 100, 50),  # 주황색
        "width": 3,
    },
    "BULLET_HIT": {
        "max_radius": 80,  # 총알 충격파 반경 (40 → 80, 2배 증가)
        "duration": 0.6,  # 지속 시간 (0.3 → 0.6, 2배 증가)
        "color": (255, 255, 255),  # 하얀색
        "width": 3,  # 선 두께 (2 → 3)
        "alpha_start": 220,  # 시작 투명도 (더 밝게)
        "expand_speed": 2.0,  # 확장 속도 배율 (1.5 → 2.0, 더 빠르게)
        "wave_count": 3,  # 파동 개수 (다중 파동)
        "wave_interval": 0.08,  # 파동 간격 (초)
    },
}

# 화면 떨림 설정
SCREEN_SHAKE_SETTINGS = {
    "PLAYER_HIT": {"intensity": 8, "duration": 8},  # 플레이어 피격
    "BOSS_HIT": {"intensity": 5, "duration": 5},  # 보스 피격
    "BOSS_SPAWN": {"intensity": 15, "duration": 20},  # 보스 등장
    "BOSS_DEATH": {"intensity": 25, "duration": 30},  # 보스 사망
    "ENEMY_DEATH": {"intensity": 3, "duration": 3},  # 일반 적 사망
}

# 타임 슬로우 설정
TIME_SLOW_SETTINGS = {
    "BOSS_DEATH": {
        "slow_factor": 0.7,  # 70% 속도 (0.3 → 0.7로 변경)
        "duration": 0.8,  # 0.8초 지속
    },
}

# 히트 플래시 설정
HIT_FLASH_DURATION = 0.1  # 히트 플래시 지속 시간 (초)
HIT_FLASH_COLOR = (255, 255, 255)  # 흰색

# 총알 트레일 설정
BULLET_TRAIL_LENGTH = 4  # 트레일 잔상 개수
BULLET_TRAIL_ALPHA_DECAY = 0.6  # 트레일 투명도 감소 비율

# 배경 패럴랙스 설정 (3개 레이어)
# 기존 패럴랙스 레이어 (별) - 원래대로 3개
PARALLAX_LAYERS = [
    {
        "star_count": 50,
        "speed_factor": 0.2,
        "star_size": 1,
        "color": (100, 100, 120),  # 어두운 별
        "twinkle": False,
    },
    {
        "star_count": 30,
        "speed_factor": 0.5,
        "star_size": 2,
        "color": (150, 150, 180),  # 중간 밝기 별
        "twinkle": False,
    },
    {
        "star_count": 15,
        "speed_factor": 0.8,
        "star_size": 3,
        "color": (200, 200, 255),  # 밝은 별
        "twinkle": False,
    },
]

# =========================================================
# 🌠 간단한 유성 효과 (웨이브당 1개)
# =========================================================

# 유성(Meteor) 설정 - 단순화
METEOR_SETTINGS = {
    "enabled": True,
    "per_wave": 1,  # 웨이브당 1개만 생성
    "use_image": False,  # 이미지 사용 안함 (작은 원으로 표시)

    # 작은 유성 설정
    "speed": (300, 500),
    "size": (3, 5),  # 작은 크기
    "color": (180, 200, 230),
    "trail_length": 8,
}

# 성운 비활성화
NEBULA_SETTINGS = {
    "enabled": False,
}

# 별 반짝임 비활성화
STAR_TWINKLE_SETTINGS = {
    "enabled": False,
}

# 플레이어 이동 연동 비활성화
PARALLAX_PLAYER_LINK = {
    "enabled": False,
}

# 속성 스킬 설정
ATTRIBUTE_SKILL_SETTINGS = {
    "EXPLOSIVE": {
        "radius": 300,  # 폭발 반경
        "damage_ratio": 0.5,  # 폭발 데미지 = 총알 데미지 * 50%
    },
    "CHAIN_EXPLOSION": {
        "max_chain_depth": 3,  # 최대 연쇄 깊이
    },
    "LIGHTNING": {
        "chain_range": 250,  # 번개 체인 범위
        "damage_ratio": 0.7,  # 체인 데미지 = 원본 * 70%
    },
    "STATIC_FIELD": {
        "radius": 180,  # 정전기장 반경
        "duration": 3.0,  # 지속 시간 (초)
        "damage_per_sec": 10,  # 초당 데미지
        "tick_interval": 0.5,  # 데미지 틱 간격 (초)
    },
    "FROST": {
        "duration": 2.0,  # 슬로우 지속 시간 (초)
    },
    "DEEP_FREEZE": {
        "duration": 1.5,  # 프리즈 지속 시간 (초)
    },
}

# 동료 유닛 설정 (Companion System)
TURRET_SETTINGS = {
    "shoot_range": 350,  # 사거리
    "shoot_cooldown": 1.5,  # 발사 쿨다운 (초)
    "damage": 25,  # 데미지
    "bullet_speed": 600,  # 총알 속도
    "duration": 50.0,  # 지속 시간 (초)
    "max_count": 3,  # 최대 터렛 수
    "size": 40,  # 터렛 크기 (반지름) - 쿨다운 UI와 동일
}

DRONE_SETTINGS = {
    "orbit_radius": 80,  # 궤도 반경
    "orbit_speed": 2.5,  # 궤도 회전 속도 (rad/s)
    "shoot_range": 200,  # 사거리
    "shoot_cooldown": 0.6,  # 발사 쿨다운 (초)
    "damage": 6,  # 데미지
    "bullet_speed": 700,  # 총알 속도
    "max_count": 5,  # 최대 드론 수
    "size": 12,  # 드론 크기 (반지름)
}

# 터렛 배치 모드 게임 상태
GAME_STATE_TURRET_PLACEMENT = 9  # 터렛 배치 중

# 스폰 포털 설정 (강화)
SPAWN_EFFECT_DURATION = 1.2  # 포털 지속 시간 (0.5 → 1.2초로 증가)
SPAWN_EFFECT_SIZE = 120  # 포털 최대 크기 (60 → 120으로 증가)

# 동적 텍스트 설정 (지속 시간 증가)
DYNAMIC_TEXT_SETTINGS = {
    "BOSS_SPAWN": {
        "size": 80,
        "color": (255, 50, 50),
        "duration_frames": 120,  # 2초 (60 FPS 기준) 
        "shake_intensity": 5,
    },
    "CRITICAL": {
        "size": 30,
        "color": (255, 200, 0),
        "duration_frames": 30,  # 0.5초 
        "shake_intensity": 3,
    },
}

# 스킬 인디케이터 UI 설정
SKILL_INDICATOR_SETTINGS = {
    "box_size": 60,  # 네모 박스 크기
    "icon_spacing": 100,  # 아이콘 간 간격 (더 넓게)
    "base_y": 65,  # 화면 하단으로부터의 거리 (스킬명 표시 공간 확보)
    "inactive_dim": 0.5,  # 미획득 상태 어둡게 비율 (0.0~1.0)
    "text_offset_y": 14,  # 스킬명 텍스트 Y 오프셋 (이미지에 더 가깝게)
    "text_size": 24,  # 스킬명 텍스트 크기 (더 크게)
    "border_width": 2,  # 테두리 두께
    "passive_blink_speed": 0.8,  # 패시브 깜박임 속도 (Hz) - 더 느리게
    "synergy_glow_size": 8,  # 시너지 글로우 크기
}

# 스킬별 아이콘 및 색상 정의
SKILL_ICONS = {
    # 공격 스킬 (왼쪽)
    'toggle_piercing': {'icon': '➡️', 'name': 'Pierce', 'color': (255, 255, 100), 'side': 'left', 'order': 0, 'type': 'passive'},
    'add_explosive': {'icon': '💥', 'name': 'Explode', 'color': (255, 150, 0), 'side': 'left', 'order': 1, 'type': 'trigger', 'cooldown': 0.5},
    'add_lightning': {'icon': '⚡', 'name': 'Lightning', 'color': (100, 200, 255), 'side': 'left', 'order': 2, 'type': 'trigger', 'cooldown': 0.5},
    'add_frost': {'icon': '❄️', 'name': 'Frost', 'color': (0, 200, 255), 'side': 'left', 'order': 3, 'type': 'trigger', 'cooldown': 2.0},

    # 보조 스킬 (오른쪽)
    'increase_max_hp': {'icon': '❤️', 'name': 'Max HP', 'color': (255, 100, 100), 'side': 'right', 'order': 0, 'type': 'passive'},
    'add_regeneration': {'icon': '🌿', 'name': 'Regen', 'color': (100, 255, 100), 'side': 'right', 'order': 1, 'type': 'passive'},
    'toggle_coin_magnet': {'icon': '🧲', 'name': 'Magnet', 'color': (200, 150, 255), 'side': 'right', 'order': 2, 'type': 'passive'},
    'add_lucky_drop': {'icon': '🍀', 'name': 'Lucky', 'color': (100, 255, 150), 'side': 'right', 'order': 3, 'type': 'passive'},
}

# 시너지 아이콘 정의
SYNERGY_ICONS = {
    'explosive_pierce': {'icon': '🌟', 'name': 'Explosive Pierce'},
    'lightning_storm': {'icon': '🌟', 'name': 'Lightning Storm'},
    'frozen_explosion': {'icon': '🌟', 'name': 'Frozen Explosion'},
    'tank_build': {'icon': '🌟', 'name': 'Tank Build'},
    'treasure_hunter': {'icon': '🌟', 'name': 'Treasure Hunter'},
}

# 크로마틱 어버레이션 설정 (보스 효과)
CHROMATIC_ABERRATION_SETTINGS = {
    "BOSS": {
        "offset": 5,  # RGB 분리 픽셀 수
        "enabled": True,
    },
}

# Hit-stop 설정 (타격 정지 효과)
HIT_STOP_SETTINGS = {
    "enabled": True,
    "NORMAL_HIT": {
        "duration": 0.02,  # 일반 타격 정지 시간 (초)
        "enabled": False,  # 일반 타격은 비활성화 (너무 빈번)
    },
    "CRITICAL_HIT": {
        "duration": 0.05,  # 크리티컬 타격 정지 시간 (초)
        "enabled": True,
    },
    "BOSS_HIT": {
        "duration": 0.08,  # 보스 타격 정지 시간 (초)
        "enabled": True,
    },
    "EXECUTE": {
        "duration": 0.15,  # 처형 스킬 정지 시간 (초)
        "enabled": True,
    },
    "ULTIMATE": {
        "duration": 0.2,  # 궁극기 정지 시간 (초)
        "enabled": True,
    },
}

# Slow motion 설정 (시간 느리게 효과)
SLOW_MOTION_SETTINGS = {
    "enabled": True,
    "CRITICAL_SLOW": {
        "time_scale": 0.3,  # 30% 속도로 느려짐
        "duration": 0.1,  # 지속 시간 (초)
        "enabled": False,  # 크리티컬은 비활성화 (너무 빈번)
    },
    "BOSS_DEATH": {
        "time_scale": 0.2,  # 20% 속도로 느려짐
        "duration": 0.8,  # 지속 시간 (초)
        "enabled": True,
    },
    "PLAYER_LOW_HP": {
        "time_scale": 0.7,  # 70% 속도로 느려짐
        "hp_threshold": 0.15,  # HP 15% 이하일 때
        "enabled": False,  # 기본 비활성화 (선택적 기능)
    },
}

# =========================================================
# 7. 🎲 랜덤 이벤트 시스템
# =========================================================

RANDOM_EVENT_SETTINGS = {
    "chance_per_wave": 0.7,  # 각 웨이브마다 70% 확률로 이벤트 발생
    "min_wave": 2,  # 최소 2웨이브부터 이벤트 발생
    "duration": 60.0,  # 대부분 이벤트 지속시간 60초
    "notification_duration": 6.0,  # 이벤트 알림 표시 시간
}

# 랜덤 이벤트 타입 정의
RANDOM_EVENTS = {
    "BLOOD_MOON": {
        "name": "Blood Moon",
        "description": "Enemies are faster but drop double coins!",
        "icon": "🌕",
        "color": (255, 50, 50),
        "effects": {
            "enemy_speed_multiplier": 1.5,
            "coin_drop_multiplier": 2.0,
        },
        "screen_tint": (100, 0, 0, 30),  # 붉은 화면 틴트
    },
    "TREASURE_RAIN": {
        "name": "Treasure Rain",
        "description": "Coins fall from the sky!",
        "icon": "💰",
        "color": (255, 215, 0),
        "effects": {
            "coin_spawn_rate": 0.5,  # 0.5초마다 코인 스폰
        },
        "duration": 20.0,
    },
    "BERSERKER_RAGE": {
        "name": "Berserker Rage",
        "description": "Attack speed +100%, but take +50% damage!",
        "icon": "⚔️",
        "color": (255, 100, 0),
        "effects": {
            "attack_speed_multiplier": 2.0,
            "damage_taken_multiplier": 1.5,
        },
        "screen_tint": (100, 50, 0, 20),
    },
    "HEALING_WINDS": {
        "name": "Healing Winds",
        "description": "Regenerate 2 HP per second",
        "icon": "💚",
        "color": (100, 255, 100),
        "effects": {
            "hp_regen_per_second": 2.0,
        },
        "duration": 25.0,
    },
    "SLOW_MOTION": {
        "name": "Bullet Time",
        "description": "Everything moves in slow motion!",
        "icon": "⏱️",
        "color": (150, 150, 255),
        "effects": {
            "time_scale": 0.6,  # 모든 것이 60% 속도로
        },
        "screen_tint": (50, 50, 100, 25),
        "duration": 15.0,
    },
    "LUCKY_HOUR": {
        "name": "Lucky Hour",
        "description": "5x XP and healing orbs spawn frequently!",
        "icon": "🍀",
        "color": (100, 255, 150),
        "effects": {
            "xp_multiplier": 5.0,
            "heal_spawn_chance": 0.5,  # 적 사망시 50% 확률로 힐 드롭
        },
        "duration": 20.0,
    },
    "METEOR_SHOWER": {
        "name": "Meteor Shower",
        "description": "Meteors fall dealing area damage!",
        "icon": "☄️",
        "color": (255, 150, 50),
        "effects": {
            "meteor_spawn_rate": 1.5,  # 1.5초마다 메테오 스폰
            "meteor_damage": 150,
            "meteor_radius": 100,
        },
        "duration": 25.0,
    },
    "GHOSTLY_PRESENCE": {
        "name": "Ghostly Presence",
        "description": "Enemies become transparent and harder to hit!",
        "icon": "👻",
        "color": (200, 200, 255),
        "effects": {
            "enemy_opacity": 0.5,
            "enemy_evasion": 0.3,  # 30% 회피율
        },
        "screen_tint": (100, 100, 150, 20),
    },
}

# =========================================================
# 8. 💰 영구 업그레이드 (PERMANENT)
# =========================================================

PERMANENT_UPGRADE_COST_BASE = 100  # 업그레이드 기본 비용
PERMANENT_MAX_HP_BONUS_AMOUNT = 10  # 최대 HP +10
PERMANENT_SPEED_BONUS_AMOUNT = 25  # 이동 속도 +25
PERMANENT_COOLDOWN_REDUCTION_RATIO = 0.05  # 쿨타임 5% 감소

# 환생 시스템
REINCARNATION_COST = 500  # 환생 구매 비용 (고정)
REINCARNATION_MAX = 3  # 최대 환생 개수

# 영구 업그레이드 레벨 관리 키
# objects.py에서 upgrades.get("COOLDOWN", 0) 형태로 사용하기 위해 대문자 키로 변경
INITIAL_PLAYER_UPGRADES = {"COOLDOWN": 0, "MAX_HP": 1, "SPEED": 0, "REINCARNATION": 1}

# 영구 업그레이드 키-설명 매핑 (ui.py에서 사용)
UPGRADE_KEYS = {
    "COOLDOWN": "Fire Rate (쿨타임 감소)",
    "MAX_HP": "Max HP (최대 체력)",
    "SPEED": "Movement Speed (이동 속도)",
    "REINCARNATION": "Reincarnation (환생)",
}

# =========================================================
# 8. ✨ 전술 레벨업 옵션 (TACTICAL)
# =========================================================

# 전술 업그레이드 스탯 보너스 상수 (밸런스 조정)
TACTICAL_DAMAGE_BONUS_RATIO = 0.02  # 무기 데미지 2% 증가 (유지 - 이미 낮음)
TACTICAL_COOLDOWN_REDUCTION_RATIO = 0.05 # 무기 쿨타임 5% 감소 (유지)
TACTICAL_SPEED_BONUS_AMOUNT = 3  # 이동 속도 +3 (유지)
TACTICAL_HEALTH_BONUS_AMOUNT = 25 # 최대 체력 +25 (20 → 15 밸런스 조정)

# 레벨업 스케일링 (웨이브 클리어 시 자동 레벨업이므로 킬 기반은 보조)
LEVEL_UP_KILL_BASE = 20
LEVEL_UP_KILL_GROWTH = 1.2  # 다음 레벨업까지 필요한 킬 수 증가 비율

# 화면 내 최대 적 수 제한 (웨이브별)

MAX_ENEMIES_ON_SCREEN = {
    # Act 1
    1: 5,
    2: 7,
    3: 10,
    4: 12,
    5: 4,   # 미니보스 4마리

    # Act 2
    6: 15,
    7: 18,
    8: 20,
    9: 23,
    10: 2,  # 중간보스 2마리

    # Act 3
    11: 25,
    12: 27,
    13: 30,
    14: 32,
    15: 3,  # 강력보스 3마리

    # Act 4
    16: 35,
    17: 38,
    18: 40,
    19: 45,
    20: 1,  # 최종보스 1마리
}


# 전술 업그레이드 옵션 정의 (카테고리별 분류)
TACTICAL_UPGRADE_OPTIONS = [
    # ========================================
    # 🔫 무기 카테고리 (Weapon) - 기본 화력
    # ========================================
    {
        "id": 1,
        "name": "💥 Increased Damage",
        "category": "weapon_basic",
        "type": "weapon",
        "action": "increase_damage",
        "value": TACTICAL_DAMAGE_BONUS_RATIO,
        "effect_str": f"+{int(TACTICAL_DAMAGE_BONUS_RATIO * 100)}% DMG",
        "description": "Increase bullet damage",
    },
    {
        "id": 2,
        "name": "⚡ Rapid Fire",
        "category": "weapon_basic",
        "type": "weapon",
        "action": "decrease_cooldown",
        "value": TACTICAL_COOLDOWN_REDUCTION_RATIO,
        "effect_str": f"-{int(TACTICAL_COOLDOWN_REDUCTION_RATIO * 100)}% Cooldown",
        "description": "Fire faster",
    },
    {
        "id": 3,
        "name": "🔫 Bullet Hail",
        "category": "weapon_basic",
        "type": "weapon",
        "action": "add_bullet",
        "value": 1,
        "effect_str": "+1 Bullet",
        "description": "Fire more bullets",
    },
    {
        "id": 4,
        "name": "➡️ Piercing Rounds",
        "category": "weapon_basic",
        "type": "toggle",
        "action": "toggle_piercing",
        "value": True,
        "effect_str": "Bullets Pierce",
        "description": "Bullets go through enemies",
    },

    # ========================================
    # 💥 무기 카테고리 - 폭발형 (Explosive)
    # ========================================
    {
        "id": 5,
        "name": "💣 Explosive Bullets",
        "category": "weapon_explosive",
        "type": "attribute",
        "action": "add_explosive",
        "value": 1,
        "effect_str": "Enemies explode on death",
        "description": "Killed enemies explode",
    },
    {
        "id": 6,
        "name": "🔥 Chain Reaction",
        "category": "weapon_explosive",
        "type": "attribute",
        "action": "add_chain_explosion",
        "value": 1,
        "effect_str": "Explosions chain to nearby enemies",
        "description": "Explosions trigger more explosions",
        "requires": "explosive",
    },

    # ========================================
    # ⚡ 무기 카테고리 - 번개형 (Lightning)
    # ========================================
    {
        "id": 7,
        "name": "⚡ Chain Lightning",
        "category": "weapon_lightning",
        "type": "attribute",
        "action": "add_lightning",
        "value": 3,
        "effect_str": "Bullets chain to 3 enemies",
        "description": "Bullets jump to nearby enemies",
    },
    {
        "id": 8,
        "name": "🌩️ Static Field",
        "category": "weapon_lightning",
        "type": "attribute",
        "action": "add_static_field",
        "value": 1,
        "effect_str": "Enemies leave electric field",
        "description": "Damage enemies over time",
        "requires": "lightning",
    },

    # ========================================
    # ❄️ 무기 카테고리 - 빙결형 (Freeze)
    # ========================================
    {
        "id": 9,
        "name": "❄️ Frost Bullets",
        "category": "weapon_freeze",
        "type": "attribute",
        "action": "add_frost",
        "value": 0.3,
        "effect_str": "Slow enemies by 30%",
        "description": "Bullets slow enemies",
    },
    {
        "id": 10,
        "name": "🧊 Deep Freeze",
        "category": "weapon_freeze",
        "type": "attribute",
        "action": "add_deep_freeze",
        "value": 0.15,
        "effect_str": "15% chance to freeze enemies",
        "description": "Completely stop enemies",
        "requires": "frost",
    },

    # ========================================
    # 🛡️ 방어 카테고리 (Defense)
    # ========================================
    {
        "id": 11,
        "name": "❤️ Max Health Boost",
        "category": "defense",
        "type": "player",
        "action": "increase_max_hp",
        "value": TACTICAL_HEALTH_BONUS_AMOUNT,
        "effect_str": f"+{TACTICAL_HEALTH_BONUS_AMOUNT} Max HP",
        "description": "Increase maximum health",
    },
    {
        "id": 12,
        "name": "💨 Movement Speed",
        "category": "defense",
        "type": "player",
        "action": "increase_speed",
        "value": TACTICAL_SPEED_BONUS_AMOUNT,
        "effect_str": f"+{TACTICAL_SPEED_BONUS_AMOUNT} Speed",
        "description": "Move faster",
    },
    {
        "id": 13,
        "name": "🛡️ Damage Reduction",
        "category": "defense",
        "type": "player",
        "action": "add_damage_reduction",
        "value": 0.1,
        "effect_str": "Take 10% less damage",
        "description": "Reduce incoming damage",
    },
    {
        "id": 14,
        "name": "🌿 Regeneration",
        "category": "defense",
        "type": "player",
        "action": "add_regeneration",
        "value": 1,
        "effect_str": "+1 HP per second",
        "description": "Slowly recover health",
    },

    # ========================================
    # 💰 유틸리티 카테고리 (Utility)
    # ========================================
    {
        "id": 15,
        "name": "🧲 Coin Magnet",
        "category": "utility",
        "type": "toggle",
        "action": "toggle_coin_magnet",
        "value": True,
        "effect_str": "Auto-collect coins",
        "description": "Coins come to you",
    },
    {
        "id": 16,
        "name": "💰 Lucky Drop",
        "category": "utility",
        "type": "game",
        "action": "add_lucky_drop",
        "value": 0.5,
        "effect_str": "+50% Coin drops",
        "description": "Enemies drop more coins",
    },
    {
        "id": 17,
        "name": "⭐ Experience Boost",
        "category": "utility",
        "type": "game",
        "action": "add_exp_boost",
        "value": 0.3,
        "effect_str": "+30% Experience",
        "description": "Level up faster",
    },
    {
        "id": 18,
        "name": "💸 Coin Recovery",
        "category": "utility",
        "type": "game",
        "action": "coin_recovery",
        "value": 0.5,
        "effect_str": "Collect 50% uncollected coins",
        "description": "Instant coin collection",
    },

    # ========================================
    # 🔧 지원 카테고리 (Support) - 추가 화력
    # ========================================
    {
        "id": 19,
        "name": "🎯 Auto Turret",
        "category": "support",
        "type": "companion",
        "action": "add_turret",
        "value": 1,
        "effect_str": "Deploy auto turret",
        "description": "Turret shoots nearby enemies",
    },
    {
        "id": 20,
        "name": "🤖 Drone Companion",
        "category": "support",
        "type": "companion",
        "action": "add_drone",
        "value": 1,
        "effect_str": "Drone orbits and shoots",
        "description": "Drone follows and attacks",
    },

    # ========================================
    # 🎯 중급 스킬 (Wave 6-10) - 전술 강화
    # ========================================
    {
        "id": 21,
        "name": "🎯 Focused Shot",
        "category": "weapon_intermediate",
        "type": "weapon",
        "action": "reduce_spread",
        "value": 0.5,
        "effect_str": "-50% Bullet spread",
        "description": "Tighter bullet grouping",
    },
    {
        "id": 22,
        "name": "🔮 Homing Bullets",
        "category": "weapon_intermediate",
        "type": "weapon",
        "action": "add_homing",
        "value": True,
        "effect_str": "Bullets track enemies",
        "description": "Bullets seek targets",
    },
    {
        "id": 23,
        "name": "🩸 Vampirism",
        "category": "defense_intermediate",
        "type": "player",
        "action": "add_vampirism",
        "value": 0.15,
        "effect_str": "Heal 15% of damage dealt",
        "description": "Lifesteal on hit",
    },
    {
        "id": 24,
        "name": "🎭 Backstab",
        "category": "weapon_intermediate",
        "type": "weapon",
        "action": "add_backstab",
        "value": 1.5,
        "effect_str": "+150% rear damage",
        "description": "Bonus damage from behind",
    },
    {
        "id": 25,
        "name": "💫 Critical Strike",
        "category": "weapon_intermediate",
        "type": "weapon",
        "action": "add_critical",
        "value": 0.2,
        "effect_str": "20% crit chance (2x dmg)",
        "description": "Chance for double damage",
    },
    {
        "id": 26,
        "name": "⏱️ Time Warp",
        "category": "weapon_intermediate",
        "type": "attribute",
        "action": "add_time_warp",
        "value": 0.4,
        "effect_str": "Bullets slow by 40%",
        "description": "Hit enemies move slower",
    },
    {
        "id": 27,
        "name": "⚡ Storm Shield",
        "category": "defense_intermediate",
        "type": "player",
        "action": "add_storm_shield",
        "value": 10,
        "effect_str": "Damage nearby enemies (10/s)",
        "description": "Passive damage aura",
    },
    {
        "id": 28,
        "name": "🛡️ Thorns",
        "category": "defense_intermediate",
        "type": "player",
        "action": "add_thorns",
        "value": 0.5,
        "effect_str": "Reflect 50% damage",
        "description": "Return damage to attackers",
    },
    # ========================================
    # 고급 스킬 (Wave 11-15) - IDs 29-36
    # ========================================
    {
        "id": 29,
        "name": "🌪️ Bullet Storm",
        "category": "weapon_advanced",
        "type": "weapon",
        "action": "add_bullet_storm",
        "value": 1,
        "effect_str": "+1 Bullet, +50% Fire Rate",
        "description": "Fire more bullets faster",
    },
    {
        "id": 30,
        "name": "💀 Execute",
        "category": "weapon_advanced",
        "type": "weapon",
        "action": "add_execute",
        "value": 0.2,
        "effect_str": "Instant kill <20% HP",
        "description": "Execute low-health enemies",
    },
    {
        "id": 31,
        "name": "🔥 Phoenix Rebirth",
        "category": "defense_advanced",
        "type": "player",
        "action": "add_phoenix",
        "value": 1,
        "effect_str": "Revive once (120s CD)",
        "description": "Cheat death with full HP",
    },
    {
        "id": 32,
        "name": "💎 Diamond Skin",
        "category": "defense_advanced",
        "type": "player",
        "action": "add_diamond_skin",
        "value": 0.3,
        "effect_str": "30% Damage Reduction",
        "description": "Permanent damage reduction",
    },
    {
        "id": 33,
        "name": "⚔️ Berserker",
        "category": "weapon_advanced",
        "type": "player",
        "action": "add_berserker",
        "value": 1,
        "effect_str": "Low HP = High DMG",
        "description": "+100% DMG at <30% HP",
    },
    {
        "id": 34,
        "name": "🌟 Starfall",
        "category": "weapon_advanced",
        "type": "attribute",
        "action": "add_starfall",
        "value": 1,
        "effect_str": "Stars fall on kill",
        "description": "Summon stars every 5 kills",
    },
    {
        "id": 35,
        "name": "🧙 Arcane Mastery",
        "category": "weapon_advanced",
        "type": "weapon",
        "action": "add_arcane_mastery",
        "value": 1,
        "effect_str": "All elements +50%",
        "description": "Boost all elemental effects",
    },
    {
        "id": 36,
        "name": "⏳ Second Chance",
        "category": "defense_advanced",
        "type": "player",
        "action": "add_second_chance",
        "value": 0.15,
        "effect_str": "15% dodge lethal hits",
        "description": "Chance to avoid fatal damage",
    },
]

SKIP_LEVEL_COIN_RECOVERY_RATIO = 0.3  # Coin Recovery 선택 시 회수 비율

# =========================================================
# 웨이브별 스킬 풀 (Wave-based Skill Pools)
# =========================================================
# 각 웨이브 구간에서 제공되는 스킬 ID 리스트

WAVE_SKILL_POOLS = {
    # Wave 1-3: 초반 화력 집중 (기본 무기 스킬)
    "early": [1, 2, 3, 4, 11, 12, 15],  # Damage, Rapid Fire, Bullet Hail, Piercing, Max HP, Speed, Magnet

    # Wave 4-5: 빌드 특성 결정 (속성 무기 선택)
    "mid_early": [1, 2, 3, 5, 7, 9, 11, 13, 16, 18],  # 기본 + Explosive, Lightning, Frost + 방어/유틸

    # Wave 6-10: 중급 스킬 해금 (전술 강화)
    "mid": [1, 2, 3, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 16, 17, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28],  # 기본 + 중급 + 고급

    # Wave 11-15: 고급 스킬 (고급 무기 + 방어 스킬)
    "late": [1, 2, 6, 8, 10, 11, 12, 13, 14, 16, 17, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36],  # 고급 속성 + 방어 + 지원 + 중급 + 고급

    # Wave 16-20: 최종 구간 (모든 스킬)
    "endgame": list(range(1, 37)),  # 모든 스킬 (ID 1-36)
}

# 웨이브 번호 → 스킬 풀 매핑
def get_skill_pool_for_wave(wave: int) -> str:
    """웨이브 번호에 맞는 스킬 풀 키를 반환합니다."""
    if wave <= 3:
        return "early"  # Wave 1-3: 기본 스킬
    elif wave <= 5:
        return "mid_early"  # Wave 4-5: 속성 선택
    elif wave <= 10:
        return "mid"  # Wave 6-10: 중급 스킬
    elif wave <= 15:
        return "late"  # Wave 11-15: 고급 스킬
    else:
        return "endgame"  # Wave 16-20: 최종 스킬

# =========================================================
# 시너지 시스템 (Synergy System)
# =========================================================
# 특정 스킬 조합 시 추가 효과

SYNERGIES = [
    {
        "name": "Explosive Pierce",
        "requires": ["toggle_piercing", "add_explosive"],
        "effect": "explosive_pierce",
        "description": "💥➡️ Bullets pierce AND explode!",
        "bonus": {"explosion_radius": 1.5}
    },
    {
        "name": "Lightning Storm",
        "requires": ["add_lightning", "decrease_cooldown"],
        "effect": "lightning_storm",
        "description": "⚡⚡ More attacks = More lightning chains!",
        "bonus": {"chain_bonus": 2}
    },
    {
        "name": "Frozen Explosion",
        "requires": ["add_frost", "add_explosive"],
        "effect": "frozen_explosion",
        "description": "❄️💥 Frozen enemies explode for 2x damage!",
        "bonus": {"frozen_explosion_mult": 2.0}
    },
    {
        "name": "Tank Build",
        "requires": ["increase_max_hp", "add_regeneration"],
        "effect": "tank_build",
        "description": "❤️🌿 Regeneration doubled!",
        "bonus": {"regen_mult": 2.0}
    },
    {
        "name": "Treasure Hunter",
        "requires": ["toggle_coin_magnet", "add_lucky_drop"],
        "effect": "treasure_hunter",
        "description": "🧲💰 Coin drops tripled!",
        "bonus": {"coin_mult": 3.0}
    },
]

# =========================================================
# ⚡ 매직 넘버 상수화 (코드 가독성 개선)
# =========================================================

# 부활 시스템 (Phoenix Rebirth)
PHOENIX_REBIRTH_COOLDOWN_SECONDS = 120.0  # 2분

# UI 레이아웃
UI_CARD_SPACING = 85  # 카드 간격 (픽셀)
UI_CARD_PADDING = 20  # 카드 내부 여백

# 충격파 효과
SHOCKWAVE_WAVE_INTERVAL = 0.08  # 다중 파동 간격 (초)

# 보스 스폰 시스템
BOSS_SEQUENTIAL_SPAWN_DELAY = 3.0  # Wave 5 보스 순차 스폰 간격 (초)

# 드론 시스템
DRONE_ORBIT_RADIUS_BASE = 80  # 드론 공전 반경 기본값
DRONE_ROTATION_SPEED = 2.0  # 드론 회전 속도 (rad/s)

# 파티클 시스템
PARTICLE_LIFETIME_DEFAULT = 0.5  # 파티클 기본 수명 (초)
PARTICLE_SIZE_DEFAULT = 4  # 파티클 기본 크기 (픽셀)

# 성능 최적화
MAX_PARTICLES_ON_SCREEN = 500  # 화면 내 최대 파티클 수
BACKGROUND_IMAGE_CACHE_SIZE = 10  # 캐시할 배경 이미지 수 (Lazy Loading용)

# =========================================================
# 🎬 스토리 기반 스테이지 시스템
# =========================================================

# 게임 모드 설정
# "classic" - 기존 40개 배경 랜덤 방식 (전환 효과 O, 스토리 X)
# "story" - 5개 스테이지 고정 배경 방식 (스토리 전환 화면 O)
GAME_MODE = "siege"  # 기본값: 공성 모드 (테스트용)

# 스테이지 전환 게임 상태
GAME_STATE_STAGE_TRANSITION = "stage_transition"

# 스테이지 전환 메시지 지속 시간 (초)
STAGE_TRANSITION_DURATION = 30.0

# 스테이지 정보 딕셔너리
STAGE_INFO = {
    1: {
        "name": "격납고",
        "name_en": "HANGAR BAY",
        "waves": [1, 2, 3, 4, 5],
        "background": "bg_hangar.jpg",
        "story": "격납고가 침략당했다!\n우주선들이 파괴되고 있다...\n\n생존을 위해 싸워라!",
        "color": (100, 150, 200),  # 푸른색 계열
        "sound": "stage_transition.wav"
    },
    2: {
        "name": "동력로",
        "name_en": "POWER CORE",
        "waves": [6, 7, 8, 9, 10],
        "background": "bg_powercore.jpg",
        "story": "동력로에 침투했다!\n핵심 에너지가 폭주하고 있다...\n\n적들을 막아내라!",
        "color": (200, 100, 50),  # 주황색 계열
        "sound": "stage_transition.wav"
    },
    3: {
        "name": "연구 시설",
        "name_en": "LABORATORY COMPLEX",
        "waves": [11, 12, 13, 14, 15],
        "background": "bg_lab.jpg",
        "story": "연구 시설이 감염되었다!\n실험체들이 탈출했다...\n\n위험을 제거하라!",
        "color": (100, 200, 100),  # 녹색 계열
        "sound": "stage_transition.wav"
    },
    4: {
        "name": "함교",
        "name_en": "COMMAND BRIDGE",
        "waves": [16, 17, 18, 19, 20],
        "background": "bg_bridge.jpg",
        "story": "함교를 탈환하라!\n적의 사령부가 눈앞이다...\n\n최후의 전투가 시작된다!",
        "color": (150, 100, 200),  # 보라색 계열
        "sound": "stage_transition.wav"
    },
    5: {
        "name": "탈출 포드",
        "name_en": "ESCAPE POD",
        "waves": [21],  # 보스 러시
        "background": "bg_escape.jpg",
        "story": "탈출 준비 완료!\n하지만 적들이 최후의 공격을...\n\n모든 보스를 격파하고 탈출하라!",
        "color": (200, 50, 50),  # 빨간색 계열
        "sound": "effect-for-logo-intro-186595.mp3"  # 보스 러시는 다른 사운드
    }
}

# =========================================================
# 🏰 SIEGE MODE (공성 모드) 설정
# =========================================================

# 공성 모드 활성화 (True: 공성 모드, False: 기존 웨이브 모드)
SIEGE_MODE_ENABLED = True

# 타일 크기 (픽셀)
TILE_SIZE = 80  # 80x80 정사각형 타일 (24x12 = 1920x960, 플레이어 이동 편리)

# 타일 타입 정의
TILE_FLOOR = 0          # 바닥 (이동 가능)
TILE_WALL = 1           # 벽 (통과 불가)
TILE_SAFE_ZONE = 2      # 안전 지대 (적 공격 무효화)
TILE_TOWER = 3          # 파괴 목표 타워
TILE_GUARD_SPAWN = 4    # 고정 경비병 스폰 위치
TILE_PATROL_SPAWN = 5   # 순찰병 스폰 위치
TILE_DESTRUCTIBLE = 6   # 파괴 가능한 벽
TILE_PLAYER_START = 7   # 플레이어 시작 위치

# 3개 스테이지 미로 맵 데이터 (24x12 타일 = 1920x960 픽셀 @ 80px/타일)
# 타일 맵은 config.py에 정의되며, main.py에서 로드됩니다.
# 타일 범례: 0=바닥, 1=벽, 2=안전지대, 3=타워, 4=경비병, 5=순찰병, 6=파괴가능벽, 7=플레이어시작

# 스테이지 1: 간단한 미로 (초급) - 10x8 타일 = 800x640 픽셀
# 플레이어는 맵 외부(상단)에서 시작, row 0에 2칸 입구 있음
# 내부는 여러 벽으로 분리됨
# 타일 범례: 0=바닥, 1=벽, 3=타워, 6=파괴가능벽
SIEGE_MAP_1 = [
    [1,1,1,0,0,1,1,1,1,1],  # Top row - 2-tile entrance
    [1,0,0,0,0,0,0,0,0,1],  # Open corridor
    [1,0,1,1,6,1,1,1,0,1],  # Interior walls + 파괴가능벽
    [1,0,0,0,0,0,0,0,0,1],  # Open space
    [1,1,6,1,1,1,1,6,1,1],  # Walls + 파괴가능벽 양쪽
    [1,0,0,0,3,0,0,0,0,1],  # Tower in center (타워)
    [1,0,1,6,1,1,6,1,0,1],  # Bottom interior walls + 파괴가능벽
    [1,1,1,1,1,1,1,1,1,1],  # Bottom wall
]

# 스테이지 2: 복잡한 미로 (중급)
SIEGE_MAP_2 = [
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
    [1,7,0,0,0,0,0,1,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,1],
    [1,0,1,1,1,1,0,1,0,1,1,1,0,1,0,1,1,1,1,1,1,1,1,1,0,1],
    [1,2,0,0,0,1,0,0,0,0,0,1,0,0,0,1,0,0,0,0,0,0,0,0,0,1],
    [1,1,1,1,0,1,1,1,1,1,0,1,1,1,0,1,0,1,1,1,1,1,1,1,1,1],
    [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
    [1,0,1,1,1,1,1,0,1,1,1,1,0,1,1,1,1,1,1,1,1,1,1,1,0,1],
    [1,0,0,0,0,0,0,0,0,4,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
    [1,1,1,0,1,1,1,1,1,0,1,1,1,1,1,0,1,1,1,1,1,1,1,1,1,1],
    [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,4,0,0,0,0,0,0,0,1],
    [1,0,1,1,1,1,1,0,1,1,1,1,0,1,1,1,1,1,1,1,1,1,1,1,0,1],
    [1,0,0,0,0,0,0,0,0,5,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
    [1,1,1,1,1,1,0,1,1,1,1,1,0,1,1,1,1,1,1,1,1,1,6,6,0,1],
    [1,0,0,0,0,0,0,0,0,0,4,0,0,0,0,0,0,0,0,0,0,0,0,3,0,1],
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
]

# 스테이지 3: 매우 복잡한 미로 + 적 다수 (고급)
SIEGE_MAP_3 = [
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
    [1,7,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
    [1,0,1,1,1,1,1,1,0,1,0,1,1,1,1,1,1,1,1,1,1,1,1,1,0,1],
    [1,2,0,0,0,0,0,1,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,1,0,1],
    [1,1,1,1,1,1,0,1,1,1,0,1,0,1,1,1,1,1,1,1,1,1,0,1,0,1],
    [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,1],
    [1,0,1,1,1,1,1,1,1,0,1,1,1,1,0,1,1,1,1,1,1,1,1,1,0,1],
    [1,0,0,4,0,0,0,0,0,0,0,5,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
    [1,1,1,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,1,1],
    [1,0,0,0,0,0,0,4,0,0,0,0,5,0,0,0,0,0,0,0,0,0,0,0,0,1],
    [1,0,1,1,1,1,1,0,1,1,1,1,0,1,1,1,1,1,1,1,1,1,1,1,0,1],
    [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,4,0,0,0,0,0,0,0,0,0,1],
    [1,1,1,1,1,1,1,0,1,1,1,1,0,1,1,1,1,1,1,1,1,1,6,6,6,1],
    [1,0,0,0,0,4,0,0,0,5,0,0,0,0,0,0,0,0,0,0,0,0,0,3,0,1],
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
]

# 스테이지 미로 맵핑
SIEGE_MAPS = {
    1: SIEGE_MAP_1,
    2: SIEGE_MAP_2,
    3: SIEGE_MAP_3,
}

# 타워 설정
TOWER_MAX_HP = 500
TOWER_SIZE = 48  # 타일 크기와 동일

# 경비병 AI 설정
GUARD_ENEMY_RANGE = 250  # 경비병의 경계 범위 (픽셀)
GUARD_ENEMY_ATTACK_RANGE = 200  # 경비병의 공격 사거리

# 순찰병 AI 설정
PATROL_ENEMY_SPEED = 80  # 순찰병의 이동 속도
PATROL_ENEMY_RANGE = 300  # 순찰병의 경계 범위

# 파괴 가능한 벽 설정
DESTRUCTIBLE_WALL_HP = 300  # 100에서 300으로 증가

# =========================================================
# 15. 🚀 함선 시스템 (Ship System)
# =========================================================

# 함선 타입 정의
# stats: hp_mult, speed_mult, damage_mult, cooldown_mult (기본값 1.0 = 100%)
SHIP_TYPES = {
    "FIGHTER": {
        "name": "Fighter",
        "description": "Balanced starter ship",
        "stats": {
            "hp_mult": 1.0,       # 기본 HP
            "speed_mult": 1.0,    # 기본 속도
            "damage_mult": 1.0,   # 기본 데미지
            "cooldown_mult": 1.0, # 기본 쿨다운
            "size": "medium",
        },
        "special": None,
        "unlock": "default",
        "color": (255, 255, 100),  # 노란색
        "muzzle_flash": "white_ring_expand",  # 기존 하얀 링 효과 유지
        "image": "fighter_front.png",
    },
    "INTERCEPTOR": {
        "name": "Interceptor",
        "description": "Fast but fragile glass cannon",
        "stats": {
            "hp_mult": 0.65,      # HP 65%
            "speed_mult": 1.35,   # 속도 135%
            "damage_mult": 1.15,  # 데미지 115%
            "cooldown_mult": 0.85, # 쿨다운 85% (더 빠름)
            "size": "small",
        },
        "special": "evasion_boost",  # 2초 무적 대시
        "unlock": "clear_act1",
        "color": (100, 200, 255),  # 하늘색
        "muzzle_flash": "blue_flash",
        "image": "interceptor_front.png",
    },
    "BOMBER": {
        "name": "Bomber",
        "description": "Slow but powerful firepower",
        "stats": {
            "hp_mult": 1.4,       # HP 140%
            "speed_mult": 0.75,   # 속도 75%
            "damage_mult": 1.5,   # 데미지 150%
            "cooldown_mult": 1.2, # 쿨다운 120% (더 느림)
            "size": "large",
        },
        "special": "bomb_drop",  # AoE 폭탄 투하
        "unlock": "clear_act2",
        "color": (255, 100, 50),  # 주황색
        "muzzle_flash": "explosion_flash",
        "image": "bomber_front.png",
    },
    "STEALTH": {
        "name": "Stealth",
        "description": "Cloaking capable special ship",
        "stats": {
            "hp_mult": 0.8,       # HP 80%
            "speed_mult": 1.1,    # 속도 110%
            "damage_mult": 1.1,   # 데미지 110%
            "cooldown_mult": 0.9, # 쿨다운 90%
            "size": "medium",
        },
        "special": "cloaking",  # 3초 은신 (무적 + 타겟팅 불가)
        "unlock": "clear_act3",
        "color": (180, 100, 255),  # 보라색
        "muzzle_flash": "void_ripple",
        "image": "stealth_front.png",
    },
    "TITAN": {
        "name": "Titan",
        "description": "Ultimate battleship",
        "stats": {
            "hp_mult": 2.0,       # HP 200%
            "speed_mult": 0.6,    # 속도 60%
            "damage_mult": 1.6,   # 데미지 160%
            "cooldown_mult": 1.4, # 쿨다운 140% (더 느림)
            "size": "huge",
        },
        "special": "shield",  # 30% 피해 흡수 실드
        "unlock": "s_rank_all",
        "color": (255, 50, 50),  # 빨간색
        "muzzle_flash": "massive_flare",
        "image": "titan_front.png",
    },
}

# 기본 함선
DEFAULT_SHIP = "FIGHTER"

# 함선 크기에 따른 이미지 비율 (screen_height 기준)
SHIP_SIZE_RATIOS = {
    "small": 0.06,
    "medium": 0.075,
    "large": 0.09,
    "huge": 0.12,
}