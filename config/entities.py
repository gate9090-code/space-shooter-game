# config/entities.py
# Entity settings: player, enemies, bosses, weapons, ships

import pygame
from typing import Dict, Tuple, List, Optional, Callable
import random
import math

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

# 보스 스폰 시스템
BOSS_SEQUENTIAL_SPAWN_DELAY = 3.0  # Wave 5 보스 순차 스폰 간격 (초)

# =========================================================
# 동료 유닛 설정 (Companion System)
# =========================================================

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

# 드론 시스템
DRONE_ORBIT_RADIUS_BASE = 80  # 드론 공전 반경 기본값
DRONE_ROTATION_SPEED = 2.0  # 드론 회전 속도 (rad/s)

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

# Training Room 스킬 설정 (레벨업 시스템)
TRAINING_SKILL_SETTINGS = {
    "EXPLOSIVE": {
        "base_radius": 100,          # 기본 반경
        "radius_per_level": 20,      # 레벨당 증가
        "max_radius": 300,           # 최대 반경
        "damage_ratio": 0.5,         # 데미지 비율
        "max_level": 10,
    },
    "LIGHTNING": {
        "base_chain_count": 3,       # 기본 체인 수
        "chain_per_level": 1,        # 레벨당 증가
        "max_chains": 10,            # 최대 체인 수
        "chain_range": 250,          # 체인 범위
        "damage_ratio": 0.7,         # 데미지 비율
        "max_level": 7,
    },
    "FROST": {
        "base_slow_ratio": 0.3,      # 기본 슬로우
        "slow_per_level": 0.1,       # 레벨당 증가
        "max_slow_ratio": 0.7,       # 최대 슬로우
        "base_freeze_chance": 0.1,   # 기본 동결 확률
        "freeze_per_level": 0.1,     # 레벨당 증가
        "max_freeze_chance": 0.5,    # 최대 동결 확률
        "slow_duration": 2.0,        # 슬로우 지속시간
        "freeze_duration": 1.5,      # 동결 지속시간
        "max_level": 5,
    },
    "DRONE": {
        "max_count": 5,              # 최대 드론 수
    },
    "TURRET": {
        "max_count": 3,              # 최대 터렛 수
    },
    "REGENERATION": {
        "base_rate": 2.0,            # 기본 회복률
        "rate_per_level": 2.0,       # 레벨당 증가
        "max_rate": 20.0,            # 최대 회복률
        "max_level": 10,
    },
    # 추가 스킬 설정 (트레이닝 모드용)
    "CHAIN_EXPLOSION": {
        "max_chain_depth": 3,        # 최대 연쇄 깊이
        "chain_chance": 0.3,         # 연쇄 확률
        "max_level": 3,
    },
    "STATIC_FIELD": {
        "base_radius": 180,          # 기본 반경
        "radius_per_level": 20,      # 레벨당 증가
        "max_radius": 280,           # 최대 반경
        "base_damage": 10,           # 기본 초당 데미지
        "damage_per_level": 5,       # 레벨당 증가
        "tick_interval": 0.5,        # 틱 간격
        "max_level": 5,
    },
    "DEEP_FREEZE": {
        "base_chance": 0.1,          # 기본 동결 확률
        "chance_per_level": 0.1,     # 레벨당 증가
        "max_chance": 0.5,           # 최대 동결 확률
        "duration": 1.5,             # 동결 지속시간
        "max_level": 5,
    },
    "EXECUTE": {
        "base_threshold": 0.1,       # 기본 처형 임계값 (HP 10%)
        "threshold_per_level": 0.05, # 레벨당 증가
        "max_threshold": 0.3,        # 최대 임계값 (HP 30%)
        "max_level": 5,
    },
    "STARFALL": {
        "base_count": 5,             # 기본 별 개수
        "count_per_level": 2,        # 레벨당 증가
        "max_count": 15,             # 최대 별 개수
        "radius": 100,               # 폭발 반경
        "damage": 50,                # 별당 데미지
        "cooldown": 30.0,            # 쿨다운 (초)
        "max_level": 5,
    },
    "PHOENIX": {
        "revive_hp_ratio": 0.5,      # 부활 시 HP 비율
        "base_cooldown": 60.0,       # 기본 쿨다운 (초)
        "cooldown_per_level": -10.0, # 레벨당 쿨다운 감소
        "min_cooldown": 30.0,        # 최소 쿨다운
        "invincibility_duration": 2.0,  # 부활 후 무적 시간
        "max_level": 3,
    },
}

# 부활 시스템 (Phoenix Rebirth)
PHOENIX_REBIRTH_COOLDOWN_SECONDS = 120.0  # 2분

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
