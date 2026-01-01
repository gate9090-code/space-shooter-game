# config/core.py
# Core system settings: screen size, colors, UI layout, fonts

import pygame
from typing import Dict, Tuple, List, Optional, Callable
from pathlib import Path

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
    "CONTENT_PANEL_WIDTH": 620,
    "CONTENT_PANEL_HEIGHT_RATIO": 0.62,  # 화면 높이의 62%

    # 탭 설정 (상단 가로 배치 통일)
    "TAB_HEIGHT": 46,
    "TAB_SPACING": 8,
    "TAB_Y": 95,  # 타이틀 아래
    "TAB_BORDER_RADIUS": 12,

    # 버튼 설정
    "BTN_HEIGHT": 48,
    "BTN_MARGIN": 30,
    "BTN_BACK_WIDTH": 110,
    "BTN_ACTION_WIDTH": 150,
    "BTN_BORDER_RADIUS": 12,

    # 타이틀 설정
    "TITLE_Y": 48,
    "CREDIT_BOX_WIDTH": 190,
    "CREDIT_BOX_HEIGHT": 46,

    # 마진/패딩
    "SCREEN_MARGIN": 32,
    "CONTENT_START_Y": 148,  # 탭 아래
    "PANEL_PADDING": 18,
    "ITEM_HEIGHT": 88,
    "ITEM_SPACING": 10,

    # 키보드 힌트
    "HINT_Y_OFFSET": 22,  # 화면 하단에서의 오프셋

    # 신규: 카드 디자인 설정 (Hades/Dead Cells 스타일)
    "CARD_ICON_SIZE": 42,
    "CARD_GLOW_SIZE": 8,
    "CARD_INNER_PADDING": 14,
}

# =========================================================
# 1.1.1 프리미엄 UI 효과 설정 (심미적 디자인)
# =========================================================

UI_EFFECTS = {
    # 글래스모피즘 효과
    "GLASS_BLUR_ALPHA": 0.85,
    "GLASS_BORDER_GLOW": 1.5,

    # 네온 글로우 효과
    "NEON_GLOW_RADIUS": 12,
    "NEON_GLOW_ALPHA": 0.4,
    "NEON_PULSE_SPEED": 2.5,

    # 호버 애니메이션
    "HOVER_SCALE_MAX": 1.04,
    "HOVER_TRANSITION_SPEED": 8.0,
    "HOVER_GLOW_INTENSITY": 0.6,

    # 카드 효과
    "CARD_SHADOW_OFFSET": (4, 6),
    "CARD_SHADOW_ALPHA": 0.35,
    "CARD_GRADIENT_STRENGTH": 0.15,

    # 아이콘 효과
    "ICON_GLOW_SIZE": 6,
    "ICON_BG_ALPHA": 0.7,
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
