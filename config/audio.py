# config/audio.py
# Audio settings: sound effects, music, volume

import pygame
from pathlib import Path
from typing import Dict, Tuple, List

# =========================================================
# 3.5. 🔊 사운드 및 음악 설정
# =========================================================

# 자원(Asset) 루트 폴더 정의 (assets)
ASSET_DIR = Path("assets")

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
    # UI SFX
    "typing": SOUND_DIR / "ui" / "sfx_typing.wav",        # 타이핑 사운드
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
