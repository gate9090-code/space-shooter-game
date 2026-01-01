# config/visuals.py
# Visual settings: fonts, color schemes, visual effects

import pygame
from typing import Dict, Tuple, List, Optional, Callable

# 폰트 크기 설정 (화면 높이 대비 비율)
FONT_SIZE_RATIOS = {
    # 기본 크기
    "HUGE": 0.055,       # 메인 타이틀 (레벨업, 게임 오버) ~48px
    "LARGE": 0.035,      # 서브 타이틀, 메뉴 제목 ~36px
    "MEDIUM": 0.020,     # 본문, 버튼, 화자 이름 ~24px
    "SMALL": 0.016,      # HUD 정보, 대화 텍스트 ~20px
    "TINY": 0.015,       # 상세 정보 ~18px
    # 확장 크기
    "MICRO": 0.012,      # 세부 정보, 힌트 ~15px
    "MEGA": 0.08,        # 레벨업 효과 ~72px
    "ULTRA": 0.12,       # 웨이브 완료 ~100px
    "ICON": 0.045,       # 아이콘 텍스트 ~50px
}

# =========================================================
# 폰트 디자인 철학 (Font Design Philosophy)
# =========================================================
# 1. Bold (NanumGothicBold) - 제목, 레이블, 강조
#    - 타이틀/헤더: huge, large
#    - 버튼 텍스트, 메뉴 항목: medium
#    - 수치, 라벨: small
#
# 2. Regular (Malgun Gothic) - 일반 텍스트
#    - 상태 정보, 일반 안내문
#
# 3. Light (Malgun Gothic Semilight) - 설명, 본문
#    - 설명 텍스트, 도움말
#    - 대화창 텍스트
#    - 긴 문장의 가독성 향상
# =========================================================

# 폰트 카테고리별 시스템 폰트 설정
FONT_SYSTEM = {
    # Bold - 제목, 강조 (파일 폰트 사용)
    "BOLD": None,  # FONT_PATH 사용

    # Regular - 일반 텍스트 (시스템 폰트)
    "REGULAR": "Malgun Gothic",

    # Light - 설명, 본문 (시스템 폰트)
    "LIGHT": "Malgun Gothic Semilight",
    "LIGHT_FALLBACK": "Malgun Gothic",
}

# 이모지 폰트 (game_engine에서 초기화됨)
EMOJI_FONTS = {}

# UI 폰트 캐시 (game_engine에서 초기화됨)
# ui.py 등에서 인라인 폰트 대신 사용
UI_FONTS = {}

# 대화창 폰트 설정 (가는 폰트)
DIALOGUE_FONT_NAME = "Malgun Gothic Semilight"  # 시스템 폰트 이름
DIALOGUE_FONT_FALLBACK = "Malgun Gothic"  # 폴백 폰트

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
# 웨이브별 색상 테마 (Hue shift, saturation, brightness)
# =========================================================

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

# =========================================================
# ✨ 시각 효과 설정 (VISUAL EFFECTS)
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
HIT_FLASH_COLOR = (180, 60, 60)  # 붉은색 (원본 이미지에 가미)
FREEZE_FLASH_COLOR = (120, 140, 180)  # 푸른-흰색 (동결 효과)

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

# 파티클 시스템
PARTICLE_LIFETIME_DEFAULT = 0.5  # 파티클 기본 수명 (초)
PARTICLE_SIZE_DEFAULT = 4  # 파티클 기본 크기 (픽셀)

# 성능 최적화
MAX_PARTICLES_ON_SCREEN = 500  # 화면 내 최대 파티클 수
