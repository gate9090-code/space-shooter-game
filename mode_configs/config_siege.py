"""
Siege Mode Configuration - Galaga Style
갈라그 스타일 고정 슈터 모드 설정

원본 갈라그 레이아웃:
- 화면 상단 30%에 적 포메이션 (5열 x 10행 구조)
- 화면 하단 10%에 플레이어 고정
- 중간 영역은 다이브 공격/총알 이동 공간
"""

from pathlib import Path

# =========================================================
# 갈라그 모드 기본 설정
# =========================================================
GALAGA_MODE = True
PLAYER_FIXED_Y = True  # 플레이어 Y 고정

# 화면 설정 (참조용 - 실제 게임은 self.screen_size 사용)
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080

# =========================================================
# 플레이어 설정
# =========================================================
PLAYER_Y_OFFSET = 80       # 화면 하단에서의 오프셋 (픽셀)
PLAYER_Y_POS = SCREEN_HEIGHT - PLAYER_Y_OFFSET  # 레거시 호환
PLAYER_SPEED = 500         # 좌우 이동 속도
PLAYER_AREA_MARGIN = 0.15  # 플레이어 좌우 이동 제한 (화면 너비의 15% 마진)

# =========================================================
# 포메이션 설정 (갈라그 스타일)
# =========================================================
# 포메이션은 화면 상단 25% 영역에 배치
# 원본 갈라그: 보스(1열) - 호위(2열) - 드론(2열) 구조
FORMATION = {
    "rows": 4,              # 행 수 (보스1 + 전투기1 + 드론2)
    "cols": 8,              # 열 수
    "start_y_ratio": 0.08,  # 포메이션 시작 Y (화면 높이의 8%)
    "end_y_ratio": 0.30,    # 포메이션 끝 Y (화면 높이의 30%)
    "start_y": 80,          # 레거시 호환 (실제로는 비율 사용)
    "row_spacing": 70,      # 행 간격
    "col_spacing": 100,     # 열 간격
    "sway_amplitude": 30,   # 좌우 흔들림 폭
    "sway_speed": 0.5,      # 흔들림 속도
    "formation_width_ratio": 0.6,  # 포메이션 너비 (화면의 60%)
}

# =========================================================
# 웨이브 설정 (적 수 조정)
# =========================================================
WAVES = {
    1: {"drone": 6, "fighter": 0, "boss": 0, "name": "WAVE 1 - SCOUTS"},
    2: {"drone": 4, "fighter": 3, "boss": 0, "name": "WAVE 2 - FIGHTERS"},
    3: {"drone": 3, "fighter": 4, "boss": 1, "name": "WAVE 3 - COMMANDER"},
    4: {"drone": 5, "fighter": 4, "boss": 2, "name": "WAVE 4 - ASSAULT"},
    5: {"drone": 4, "fighter": 5, "boss": 3, "name": "WAVE 5 - FINAL STAND"},
}

TOTAL_WAVES = 5
WAVE_CLEAR_DELAY = 2.0  # 웨이브 클리어 후 대기 시간

# =========================================================
# 적 타입별 설정 (갈라그 스타일)
# =========================================================
ENEMY_TYPES = {
    "drone": {
        "hp": 20,
        "score": 50,
        "dive_score": 100,  # 다이브 중 처치 시 2배
        "image": "galaga_drone.png",
        "size": (72, 72),   # 크기 증가
        "dive_pattern": "straight",
        "dive_speed": 180,      # 다이브 속도 느리게 (350→180)
        "fire_rate": 6.0,       # 발사 간격 느리게 (4.0→6.0초)
        "bullet_speed": 150,    # 총알 속도 느리게 (300→150)
        "bullet_damage": 10,
        "entry_speed": 250,     # 진입 속도 느리게 (400→250)
        "formation_row": 2,     # 포메이션 행 (2-3행: 드론)
    },
    "fighter": {
        "hp": 40,
        "score": 80,
        "dive_score": 160,
        "image": "galaga_fighter.png",
        "size": (80, 80),   # 크기 증가
        "dive_pattern": "zigzag",
        "dive_speed": 160,      # 다이브 속도 느리게 (300→160)
        "fire_rate": 5.0,       # 발사 간격 느리게 (3.0→5.0초)
        "bullet_speed": 180,    # 총알 속도 느리게 (350→180)
        "bullet_damage": 15,
        "entry_speed": 220,     # 진입 속도 느리게 (350→220)
        "zigzag_amplitude": 60,
        "zigzag_frequency": 3,
        "formation_row": 1,     # 포메이션 행 (1행: 전투기)
    },
    "boss": {
        "hp": 100,
        "score": 150,
        "dive_score": 400,
        "image": "galaga_boss.png",
        "size": (96, 96),   # 크기 증가
        "dive_pattern": "swoop",  # 곡선 다이브
        "dive_speed": 140,      # 다이브 속도 느리게 (250→140)
        "fire_rate": 4.0,       # 발사 간격 느리게 (2.0→4.0초)
        "bullet_speed": 200,    # 총알 속도 느리게 (400→200)
        "bullet_damage": 20,
        "entry_speed": 200,     # 진입 속도 느리게 (300→200)
        "escort_count": 2,
        "formation_row": 0,     # 포메이션 행 (0행: 보스)
    },
}

# =========================================================
# 다이브 공격 설정 (갈라그 스타일)
# =========================================================
DIVE_SETTINGS = {
    "initial_delay": 2.5,      # 포메이션 완성 후 첫 다이브까지 대기
    "dive_interval": 2.0,      # 다이브 간격
    "max_divers": 2,           # 동시 다이브 최대 수
    "return_y_ratio": -0.1,    # 복귀 시 화면 상단 위치 (화면 높이의 -10%)
    "return_y": -80,           # 레거시 호환
    "dive_end_y_ratio": 1.1,   # 다이브 종료 Y (화면 밖으로 나가면 복귀)
    "fire_during_dive": True,  # 다이브 중 발사 허용
    "dive_fire_rate_mult": 0.5,  # 다이브 중 발사 속도 배율
}

# =========================================================
# 진입 경로 설정 (베지어 곡선)
# =========================================================
ENTRY_PATHS = {
    "left": {
        "start": (-100, 300),
        "control1": (300, 100),
        "control2": (500, 200),
    },
    "right": {
        "start": (SCREEN_WIDTH + 100, 300),
        "control1": (SCREEN_WIDTH - 300, 100),
        "control2": (SCREEN_WIDTH - 500, 200),
    },
    "top": {
        "start": (SCREEN_WIDTH // 2, -100),
        "control1": (SCREEN_WIDTH // 2 + 150, 150),
        "control2": (SCREEN_WIDTH // 2 - 150, 250),
    },
}

SPAWN_INTERVAL = 0.25  # 적 스폰 간격 (초)

# =========================================================
# 배경 설정
# =========================================================
BACKGROUND_SCROLL_SPEED = 50  # 별 배경 스크롤 속도
STAR_COUNT = 100              # 배경 별 개수

# =========================================================
# 이미지 경로
# =========================================================
SIEGE_IMAGE_DIR = Path("assets/modes/siege")
ENEMY_IMAGE_DIR = SIEGE_IMAGE_DIR / "enemies"
BACKGROUND_DIR = SIEGE_IMAGE_DIR / "backgrounds"

# =========================================================
# 레거시 설정 (기존 공성모드 호환용)
# =========================================================
TILE_SIZE = 64
TILE_FLOOR = 0
TILE_WALL = 1
TILE_SAFE_ZONE = 2
TILE_TOWER = 3
TILE_GUARD_SPAWN = 4
TILE_PATROL_SPAWN = 5
TILE_DESTRUCTIBLE = 6
TILE_PLAYER_START = 7

TOWER_MAX_HP = 500
TOWER_SIZE = 64
GUARD_ENEMY_RANGE = 250
GUARD_ENEMY_ATTACK_RANGE = 200
GUARD_ENEMY_HP = 50
GUARD_ENEMY_DAMAGE = 15
GUARD_ENEMY_FIRE_RATE = 1.0
PATROL_ENEMY_SPEED = 1.5
PATROL_ENEMY_HP = 40
PATROL_ENEMY_DAMAGE = 10
PATROL_ENEMY_PATROL_RADIUS = 150
PATROL_ENEMY_RANGE = 300
DESTRUCTIBLE_WALL_HP = 100

SIEGE_MAP_1 = [[0]]
SIEGE_MAPS = {1: SIEGE_MAP_1}
SIEGE_STAGES = {}

print("INFO: config_siege.py (Galaga Mode) loaded")
