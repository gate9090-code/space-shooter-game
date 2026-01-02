# config/assets.py
# Asset paths and settings: images, fonts, dimensions

import pygame
from pathlib import Path
from typing import Dict, Tuple, List

# =========================================================
# 3. 🖼️ 이미지 및 폰트 설정
# =========================================================

# 💡 자원(Asset) 루트 폴더 정의 (assets)
ASSET_DIR = Path("assets")

# 폰트 폴더 정의 및 경로
FONT_DIR = ASSET_DIR / "fonts"
FONT_PATH = FONT_DIR / "NanumGothicBold.ttf"

# 배경 이미지 전용 폴더 정의 및 경로 (최상위로 이동)
BACKGROUND_DIR = ASSET_DIR / "backgrounds"
BACKGROUND_IMAGE_PATH = BACKGROUND_DIR / "bg_default.png"

# 스토리 모드 배경 이미지 (웨이브별 고유 배경)
STORY_BACKGROUNDS = {
    1: "story_bg_01.jpg",  # wallpaperbetter 이미지 (붉은색 테마)
}

# 동적 배경 시스템 설정 (웨이브 1-5용)
DYNAMIC_BACKGROUND_ENABLED = True
DYNAMIC_BACKGROUND_IMAGE = "story_bg_01.jpg"  # 기본 이미지
DYNAMIC_BACKGROUND_WAVES = [1, 2, 3, 4, 5]  # 동적 배경 적용 웨이브

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

# 일반 객체 이미지 폴더 및 경로 (재구성된 구조)
IMAGE_DIR = ASSET_DIR / "images"

# Gameplay 이미지 (플레이어, 적, 수집 아이템)
GAMEPLAY_DIR = IMAGE_DIR / "gameplay"
PLAYER_SHIP_IMAGE_PATH = GAMEPLAY_DIR / "player" / "player_ship.png"
ENEMY_SHIP_IMAGE_PATH = GAMEPLAY_DIR / "enemies" / "enemy_ship.png"
ENEMY_SHIP_BURN_IMAGE_PATH = GAMEPLAY_DIR / "enemies" / "enemy_ship_burn.png"
PLAYER_BULLET_IMAGE_PATH = GAMEPLAY_DIR / "player" / "player_bullet.png"
COIN_GEM_IMAGE_PATH = GAMEPLAY_DIR / "collectibles" / "coin_gem.png"
GEM_HP_IMAGE_PATH = GAMEPLAY_DIR / "collectibles" / "gem_hp.png"

# VFX 이미지 (시각 효과)
VFX_DIR = IMAGE_DIR / "vfx"
IMPACT_FX_IMAGE_PATH = VFX_DIR / "combat" / "impact_fx.png"
EXPLOSION_IMAGE_PATH = VFX_DIR / "combat" / "explosion.png"
METEOR_HEAD_IMAGE_PATH = VFX_DIR / "combat" / "meteor_head.png"
METEOR_TRAIL_IMAGE_PATH = VFX_DIR / "combat" / "meteor_trail.png"
WAVE_CLEAR_FIREWORKS_PATH = VFX_DIR / "combat" / "wave_clear_fireworks.png"

# 스킬 이미지 폴더
SKILL_IMAGE_DIR = VFX_DIR / "skills"
STATIC_FIELD_IMAGE_PATH = SKILL_IMAGE_DIR / "static_field.png"

# UI 이미지 폴더
UI_DIR = IMAGE_DIR / "ui"
MENU_ICON_DIR = UI_DIR
WAVE_HERO_IMAGE_PATH = UI_DIR / "wave_hero.jpg"

# 화면 높이에 대한 객체 이미지 크기 비율 (0.0 ~ 1.0)
IMAGE_SIZE_RATIOS = {
    "PLAYER": 0.14,  # 플레이어 이미지 크기 비율
    "ENEMY": 0.11, # 적 이미지 크기 비율
    "BULLET": 0.035,  # 총알 이미지 크기 비율 (720p 기준 약 25픽셀)
    "COINGEM": 0.05,  # 코인 젬 이미지 크기 비율
    "GEMHP": 0.05,  # HP 젬 이미지 크기 비율
    "HITIMPACT": 0.13, # 충돌 이펙트 이미지 크기 비율
}
