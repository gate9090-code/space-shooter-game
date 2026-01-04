# config/gameplay.py
# Gameplay settings: game states, waves, levels, upgrades, events

import pygame
from typing import Dict, Tuple, List, Optional, Callable
import random

# =========================================================
# 2. 🚦 게임 상태 관리
# =========================================================

GAME_STATE_RUNNING = 1  # 게임 실행 중
GAME_STATE_OVER = 2  # 게임 오버
GAME_STATE_PAUSED = 3  # 일시 정지
GAME_STATE_SHOP = 4  # 영구 업그레이드 상점
GAME_STATE_LEVEL_UP = 5  # 전술 레벨업 메뉴 (킬 기반)
GAME_STATE_WAVE_CLEAR = 6  # 웨이브 클리어 (휴식 시간)
GAME_STATE_WAVE_PREPARE = 7  # 웨이브 시작 대기 (클릭으로 시작)
GAME_STATE_VICTORY = 8  # 게임 승리 (모든 웨이브 클리어)
GAME_STATE_BOSS_CLEAR = 12  # 보스 클리어 (계속/복귀 선택)
GAME_STATE_SETTINGS = 10  # 설정 메뉴 (F1 키로 열기/닫기)
GAME_STATE_QUIT_CONFIRM = 11  # 종료 확인 (ESC 키로 열기)
GAME_STATE_TURRET_PLACEMENT = 9  # 터렛 배치 중
GAME_STATE_STAGE_TRANSITION = "stage_transition"  # 스테이지 전환

# Boss Rush Mode 설정
BOSS_RUSH_MODE = False  # 보스 러시 모드 활성화 여부
BOSS_RUSH_COMPLETED_WAVES = []  # 보스 러시에서 완료한 웨이브 목록

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
TOTAL_WAVES = 20  # 총 웨이브 수 (웨이브 모드)
STORY_TOTAL_WAVES = 25  # 스토리 모드 총 웨이브 수
BOSS_WAVES = [5, 10, 15, 20, 25]  # 보스 웨이브 (Wave 5: 블루 드래곤)

# 웨이브별 난이도 스케일링 (20 Wave System)
WAVE_SCALING = {
    # === Act 1: 기초 학습 (Wave 1-5) ===
    1: {"hp_mult": 1.0,   "speed_mult": 0.8,  "spawn_rate": 0.8,  "target_kills": 10,  "chase_prob": 0.3,  "damage_mult": 1.0},   # +5
    2: {"hp_mult": 1.3,   "speed_mult": 0.9,  "spawn_rate": 1.0,  "target_kills": 11,  "chase_prob": 0.4,  "damage_mult": 1.0},   # +5
    3: {"hp_mult": 1.6,   "speed_mult": 1.0,  "spawn_rate": 1.1,  "target_kills": 12,  "chase_prob": 0.5,  "damage_mult": 1.0},   # +5
    4: {"hp_mult": 2.0,   "speed_mult": 1.1,  "spawn_rate": 1.2,  "target_kills": 13,  "chase_prob": 0.6,  "damage_mult": 1.0},   # +5
    5: {"hp_mult": 50.0,  "speed_mult": 0.6,  "spawn_rate": 1.0,  "target_kills": 1,   "chase_prob": 1.0,  "damage_mult": 3.0},   # 블루 드래곤 보스

    # === Act 2: 스킬 조합 (Wave 6-10) ===
    6: {"hp_mult": 2.5,   "speed_mult": 1.2,  "spawn_rate": 1.3,  "target_kills": 14,  "chase_prob": 0.7,  "damage_mult": 1.0},   # +5 (일반 웨이브로 복귀)
    7: {"hp_mult": 3.0,   "speed_mult": 1.3,  "spawn_rate": 1.4,  "target_kills": 15,  "chase_prob": 0.75, "damage_mult": 1.0},   # +5
    8: {"hp_mult": 4.0,   "speed_mult": 1.4,  "spawn_rate": 1.5,  "target_kills": 16,  "chase_prob": 0.8,  "damage_mult": 1.0},   # +5
    9: {"hp_mult": 5.0,   "speed_mult": 1.5,  "spawn_rate": 1.6,  "target_kills": 17,  "chase_prob": 0.85, "damage_mult": 1.0},   # +5
    10: {"hp_mult": 60.0, "speed_mult": 1.8,  "spawn_rate": 1.0,  "target_kills": 1,   "chase_prob": 1.0,  "damage_mult": 2.5},   # 중간보스 (유지)

    # === Act 3: 엘리트 구간 (Wave 11-15) ===
    11: {"hp_mult": 6.5,  "speed_mult": 1.6,  "spawn_rate": 1.7,  "target_kills": 18,  "chase_prob": 0.85, "damage_mult": 1.2},   # +5
    12: {"hp_mult": 8.0,  "speed_mult": 1.7,  "spawn_rate": 1.8,  "target_kills": 19,  "chase_prob": 0.88, "damage_mult": 1.2},   # +5
    13: {"hp_mult": 10.0, "speed_mult": 1.8,  "spawn_rate": 1.9,  "target_kills": 20,  "chase_prob": 0.9,  "damage_mult": 1.3},   # +5
    14: {"hp_mult": 12.5, "speed_mult": 1.9,  "spawn_rate": 2.0,  "target_kills": 21,  "chase_prob": 0.92, "damage_mult": 1.3},   # +5
    15: {"hp_mult": 90.0, "speed_mult": 2.3,  "spawn_rate": 1.5,  "target_kills": 1,   "chase_prob": 1.0,  "damage_mult": 3.0},   # 강력보스 (유지)

    # === Act 4: 지옥 구간 (Wave 16-20) ===
    16: {"hp_mult": 15.0, "speed_mult": 2.0,  "spawn_rate": 2.1,  "target_kills": 23,  "chase_prob": 0.93, "damage_mult": 1.4},   # +5
    17: {"hp_mult": 18.0, "speed_mult": 2.1,  "spawn_rate": 2.2,  "target_kills": 25,  "chase_prob": 0.95, "damage_mult": 1.5},   # +5
    18: {"hp_mult": 22.0, "speed_mult": 2.2,  "spawn_rate": 2.3,  "target_kills": 27,  "chase_prob": 0.97, "damage_mult": 1.6},   # +5
    19: {"hp_mult": 27.0, "speed_mult": 2.3,  "spawn_rate": 2.4,  "target_kills": 30,  "chase_prob": 0.98, "damage_mult": 1.7},   # +5
    20: {"hp_mult": 120.0,"speed_mult": 2.5,  "spawn_rate": 1.0,  "target_kills": 1,   "chase_prob": 1.0,  "damage_mult": 3.5},   # 최종보스 (유지)

    # === Act 5: 최종 구간 - 스토리 모드 전용 (Wave 21-25) ===
    21: {"hp_mult": 30.0, "speed_mult": 2.4,  "spawn_rate": 2.5,  "target_kills": 32,  "chase_prob": 0.98, "damage_mult": 1.8},
    22: {"hp_mult": 35.0, "speed_mult": 2.5,  "spawn_rate": 2.6,  "target_kills": 35,  "chase_prob": 0.99, "damage_mult": 1.9},
    23: {"hp_mult": 40.0, "speed_mult": 2.6,  "spawn_rate": 2.7,  "target_kills": 38,  "chase_prob": 1.0,  "damage_mult": 2.0},
    24: {"hp_mult": 50.0, "speed_mult": 2.7,  "spawn_rate": 2.8,  "target_kills": 40,  "chase_prob": 1.0,  "damage_mult": 2.2},
    25: {"hp_mult": 150.0,"speed_mult": 2.8,  "spawn_rate": 1.0,  "target_kills": 1,   "chase_prob": 1.0,  "damage_mult": 4.0},   # 최종보스
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
    # Act 5: 최종 구간 - 스토리 모드 전용 (Wave 21-25)
    21: 1800, 22: 2000, 23: 2500, 24: 3000, 25: 5000, # 스토리 최종 보스 보너스
}

# 크레딧 보상 배율 (난이도별)
CREDIT_DIFFICULTY_MULTIPLIER = {
    "easy": 1.5,
    "normal": 1.0,
    "hard": 0.8,
}

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

    # Act 5: 최종 구간 (스토리 모드 전용)
    21: "⭐  Wave 21 - Cosmic Ascent",
    22: "🌟  Wave 22 - Stellar Onslaught",
    23: "💫  Wave 23 - Nebula Storm",
    24: "🌠  Wave 24 - Ultimate Test",
    25: "🏆  FINAL BOSS - The Origin",
}

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

SKIP_LEVEL_COIN_RECOVERY_RATIO = 0.3  # Coin Recovery 선택 시 회수 비율

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
# 🎬 스토리 기반 스테이지 시스템
# =========================================================

# 게임 모드 설정
# "classic" - 기존 40개 배경 랜덤 방식 (전환 효과 O, 스토리 X)
# "story" - 5개 스테이지 고정 배경 방식 (스토리 전환 화면 O)
GAME_MODE = "siege"  # 기본값: 공성 모드 (테스트용)

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

# UI 레이아웃
UI_CARD_SPACING = 85  # 카드 간격 (픽셀)
UI_CARD_PADDING = 20  # 카드 내부 여백

# 충격파 효과
SHOCKWAVE_WAVE_INTERVAL = 0.08  # 다중 파동 간격 (초)

# 배경 이미지 캐시 설정
BACKGROUND_IMAGE_CACHE_SIZE = 10  # 캐시할 배경 이미지 수 (Lazy Loading용)
