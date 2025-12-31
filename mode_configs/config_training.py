"""
Training Mode Configuration
트레이닝 모드 전용 웨이브 및 스폰 설정
"""

# =========================================================
# 트레이닝 모드 기본 설정
# =========================================================

# 적 관리 설정
MIN_ENEMIES = 3         # 화면 최소 적 수 (이 미만이면 자동 보충)
MAX_ENEMIES = 10        # 화면 최대 적 수
SPAWN_INTERVAL = 0.5    # 적 스폰 간격 (초)
SPAWN_BATCH_SIZE = 2    # 한 번에 스폰할 적 수
SPAWN_MARGIN = 50       # 화면 가장자리에서의 스폰 마진

# =========================================================
# 트레이닝 웨이브 설정 (5단계, 무한 루프)
# =========================================================
TRAINING_WAVES = {
    1: {
        "name": "WAVE 1 - BASIC",
        "min_enemies": 3,
        "max_enemies": 6,
        "spawn_interval": 0.8,
        "enemy_distribution": {"NORMAL": 1.0},
        "duration": 60,  # 웨이브 지속 시간 (초)
    },
    2: {
        "name": "WAVE 2 - VARIETY",
        "min_enemies": 4,
        "max_enemies": 8,
        "spawn_interval": 0.6,
        "enemy_distribution": {"NORMAL": 0.6, "RUNNER": 0.2, "TANK": 0.2},
        "duration": 60,
    },
    3: {
        "name": "WAVE 3 - CHALLENGE",
        "min_enemies": 5,
        "max_enemies": 10,
        "spawn_interval": 0.5,
        "enemy_distribution": {"NORMAL": 0.3, "TANK": 0.2, "RUNNER": 0.2, "SUMMONER": 0.15, "SHIELDED": 0.15},
        "duration": 60,
    },
    4: {
        "name": "WAVE 4 - ELITE",
        "min_enemies": 5,
        "max_enemies": 12,
        "spawn_interval": 0.4,
        "enemy_distribution": {"NORMAL": 0.2, "TANK": 0.15, "RUNNER": 0.15, "SUMMONER": 0.15, "SHIELDED": 0.2, "KAMIKAZE": 0.15},
        "duration": 90,
    },
    5: {
        "name": "WAVE 5 - CHAOS",
        "min_enemies": 6,
        "max_enemies": 15,
        "spawn_interval": 0.3,
        "enemy_distribution": {"NORMAL": 0.1, "TANK": 0.2, "RUNNER": 0.2, "SUMMONER": 0.2, "SHIELDED": 0.15, "KAMIKAZE": 0.15},
        "duration": None,  # 무한 (루프까지)
    },
}

TOTAL_TRAINING_WAVES = 5
WAVE_LOOP_ENABLED = True           # 마지막 웨이브 이후 1웨이브로 복귀
WAVE_LOOP_DIFFICULTY_MULT = 1.2    # 루프 시 난이도 배율 (적 수, 스폰 속도)

# =========================================================
# 스폰 위치 설정
# =========================================================
SPAWN_POSITIONS = {
    "top": True,      # 화면 상단만 활성화
    "sides": False,   # 화면 좌우 비활성화
    "bottom": False,  # 화면 하단 비활성화
}

# 적 이동 제한 (화면 중앙 아래로 진입 불가)
ENEMY_MOVEMENT_LIMIT = 0.5  # 화면 높이의 50% 이하로 진입 불가

# =========================================================
# 12개 스킬 정의 (트레이닝 모드 전용)
# =========================================================
SKILL_DEFINITIONS = {
    "explosive": {
        "name": "Explosive",
        "type": "공격",
        "color": (255, 100, 100),
        "description": "총알 명중 시 범위 폭발 데미지",
        "details": ["반경: 100~300px", "데미지: 기본 50%", "레벨당 반경 +20"],
        "max_level": 10,
        "shortcut": "1",
    },
    "chain_explosion": {
        "name": "Chain Explosion",
        "type": "공격",
        "color": (255, 150, 50),
        "description": "폭발 연쇄 반응으로 추가 폭발",
        "details": ["최대 연쇄: 3단계", "연쇄 확률: 30%"],
        "max_level": 3,
        "shortcut": "2",
    },
    "lightning": {
        "name": "Lightning",
        "type": "공격",
        "color": (100, 200, 255),
        "description": "연쇄 번개로 다수 적 공격",
        "details": ["체인 수: 3~10", "체인 범위: 250px", "데미지: 70%"],
        "max_level": 7,
        "shortcut": "3",
    },
    "static_field": {
        "name": "Static Field",
        "type": "패시브",
        "color": (100, 255, 255),
        "description": "플레이어 주변 지속 데미지 필드",
        "details": ["반경: 180px", "초당 데미지: 10", "틱 간격: 0.5초"],
        "max_level": 5,
        "shortcut": "4",
    },
    "frost": {
        "name": "Frost",
        "type": "CC",
        "color": (150, 220, 255),
        "description": "명중 시 적 이동속도 감소",
        "details": ["슬로우: 30~70%", "지속시간: 2초"],
        "max_level": 5,
        "shortcut": "5",
    },
    "deep_freeze": {
        "name": "Deep Freeze",
        "type": "CC",
        "color": (220, 240, 255),
        "description": "적 완전 동결 (이동 불가)",
        "details": ["동결 확률: 10~50%", "지속시간: 1.5초"],
        "max_level": 5,
        "shortcut": "6",
    },
    "execute": {
        "name": "Execute",
        "type": "공격",
        "color": (200, 100, 255),
        "description": "HP 낮은 적 즉시 처형",
        "details": ["처형 임계값: HP 10~30%", "보스 제외"],
        "max_level": 5,
        "shortcut": "7",
    },
    "starfall": {
        "name": "Starfall",
        "type": "궁극기",
        "color": (255, 215, 0),
        "description": "랜덤 위치에 별똥별 폭격",
        "details": ["별 개수: 5~15", "범위 데미지", "쿨다운: 30초"],
        "max_level": 5,
        "shortcut": "8",
    },
    "drone": {
        "name": "Drone",
        "type": "소환",
        "color": (200, 200, 100),
        "description": "플레이어 주위를 도는 공격 드론",
        "details": ["최대 5기", "자동 공격", "궤도 반경: 80px"],
        "max_level": 5,
        "shortcut": "9",
    },
    "turret": {
        "name": "Turret",
        "type": "소환",
        "color": (150, 150, 200),
        "description": "고정형 자동 공격 터렛",
        "details": ["최대 3기", "사거리: 350px", "지속시간: 50초"],
        "max_level": 3,
        "shortcut": "0",
    },
    "regeneration": {
        "name": "Regeneration",
        "type": "패시브",
        "color": (100, 255, 100),
        "description": "HP 자동 회복",
        "details": ["초당 회복: 2~20", "전투 중에도 적용"],
        "max_level": 10,
        "shortcut": "-",
    },
    "phoenix": {
        "name": "Phoenix Rebirth",
        "type": "패시브",
        "color": (255, 150, 50),
        "description": "사망 시 HP 50%로 부활",
        "details": ["쿨다운: 60초", "부활 시 무적 2초"],
        "max_level": 3,
        "shortcut": "=",
    },
}

# 스킬 순서 (UI 표시용)
SKILL_ORDER = [
    "explosive", "chain_explosion", "lightning", "static_field",
    "frost", "deep_freeze", "execute", "starfall",
    "drone", "turret", "regeneration", "phoenix",
]

print("INFO: config_training.py loaded")
