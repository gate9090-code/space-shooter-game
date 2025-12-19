# mode_configs/config_missions.py
"""
통합 미션 시스템 설정

미션 유형:
- story: 스토리 모드 미션 (StoryMode)
- wave: 웨이브 방어 미션 (WaveMode)
- siege: 공성 미션 (SiegeMode)
- training: 훈련장 (무한 웨이브)
"""

from typing import Dict, List, Any
from dataclasses import dataclass
from enum import Enum


class MissionType(Enum):
    """미션 유형"""
    STORY = "story"      # 스토리 모드
    WAVE = "wave"        # 웨이브 방어
    SIEGE = "siege"      # 공성전
    TRAINING = "training"  # 훈련장


class MissionCategory(Enum):
    """미션 분류"""
    MAIN = "main"        # 메인 스토리 (필수)
    SIDE = "side"        # 사이드 미션 (선택)
    TRAINING = "training"  # 훈련장


@dataclass
class MissionReward:
    """미션 보상"""
    credits: int = 0
    exp: int = 0
    items: List[str] = None
    unlock_ship: str = None
    unlock_weapon: str = None

    def __post_init__(self):
        if self.items is None:
            self.items = []


# =============================================================================
# 메인 스토리 미션
# =============================================================================

MAIN_MISSIONS: Dict[str, Dict[str, Any]] = {
    # =========================================================================
    # ACT 1: 폐허의 귀환
    # =========================================================================
    "act1_m1": {
        "type": MissionType.STORY,
        "category": MissionCategory.MAIN,
        "act": 1,
        "name": "정찰 임무",
        "name_en": "Recon Mission",
        "description": "폐허가 된 지구에서 생존자 흔적을 찾아라",
        "waves": [1, 2, 3],  # StoryMode 웨이브 1-3
        "prerequisite": None,
        "unlocks": ["act1_m2", "side_defense_1"],
        "rewards": MissionReward(credits=200, exp=100),
    },
    "act1_m2": {
        "type": MissionType.STORY,
        "category": MissionCategory.MAIN,
        "act": 1,
        "name": "추격전",
        "name_en": "The Chase",
        "description": "카오스 추격대로부터 탈출하라",
        "waves": [4],
        "prerequisite": "act1_m1",
        "unlocks": ["act1_m3"],
        "rewards": MissionReward(credits=150, exp=80),
    },
    "act1_m3": {
        "type": MissionType.STORY,
        "category": MissionCategory.MAIN,
        "act": 1,
        "name": "섀도우 스카우트",
        "name_en": "Shadow Scout",
        "description": "카오스 정찰대장을 처치하라",
        "waves": [5],  # 보스 웨이브
        "prerequisite": "act1_m2",
        "unlocks": ["act2_m1", "side_siege_1"],
        "rewards": MissionReward(credits=500, exp=200, unlock_weapon="plasma_cannon"),
        "is_boss": True,
    },

    # =========================================================================
    # ACT 2: 숨겨진 기지
    # =========================================================================
    "act2_m1": {
        "type": MissionType.STORY,
        "category": MissionCategory.MAIN,
        "act": 2,
        "name": "벙커 진입",
        "name_en": "Bunker Entry",
        "description": "지하 벙커로 진입하여 방어선을 뚫어라",
        "waves": [6],  # DEFENSE 목표
        "prerequisite": "act1_m3",
        "unlocks": ["act2_m2"],
        "rewards": MissionReward(credits=300, exp=150),
    },
    "act2_m2": {
        "type": MissionType.STORY,
        "category": MissionCategory.MAIN,
        "act": 2,
        "name": "벙커 소탕",
        "name_en": "Bunker Sweep",
        "description": "벙커 내부의 적을 소탕하라",
        "waves": [7],
        "prerequisite": "act2_m1",
        "unlocks": ["act2_m3", "side_defense_2"],
        "rewards": MissionReward(credits=250, exp=120),
    },
    "act2_m3": {
        "type": MissionType.STORY,
        "category": MissionCategory.MAIN,
        "act": 2,
        "name": "데이터 회수",
        "name_en": "Data Retrieval",
        "description": "프로젝트 아크 문서를 수집하라",
        "waves": [8],  # DATA_COLLECT 목표
        "prerequisite": "act2_m2",
        "unlocks": ["act2_m4"],
        "rewards": MissionReward(credits=400, exp=180),
    },
    "act2_m4": {
        "type": MissionType.STORY,
        "category": MissionCategory.MAIN,
        "act": 2,
        "name": "생존자 호위",
        "name_en": "Survivor Escort",
        "description": "생존자 캡슐을 안전하게 호위하라",
        "waves": [9],  # ESCORT 목표
        "prerequisite": "act2_m3",
        "unlocks": ["act2_m5"],
        "rewards": MissionReward(credits=350, exp=160),
    },
    "act2_m5": {
        "type": MissionType.STORY,
        "category": MissionCategory.MAIN,
        "act": 2,
        "name": "데이터 추출자",
        "name_en": "Data Extractor",
        "description": "카오스 데이터 추출자를 처치하라",
        "waves": [10],  # 보스 웨이브
        "prerequisite": "act2_m4",
        "unlocks": ["act3_m1", "side_siege_2"],
        "rewards": MissionReward(credits=600, exp=250),
        "is_boss": True,
    },

    # =========================================================================
    # ACT 3: 불타는 연구소
    # =========================================================================
    "act3_m1": {
        "type": MissionType.STORY,
        "category": MissionCategory.MAIN,
        "act": 3,
        "name": "화염 속 탈출",
        "name_en": "Escape Through Fire",
        "description": "불타는 연구소에서 탈출구를 찾아라",
        "waves": [11],  # SURVIVAL 목표
        "prerequisite": "act2_m5",
        "unlocks": ["act3_m2"],
        "rewards": MissionReward(credits=400, exp=200),
    },
    "act3_m2": {
        "type": MissionType.STORY,
        "category": MissionCategory.MAIN,
        "act": 3,
        "name": "게이트 데이터",
        "name_en": "Gate Data",
        "description": "차원 게이트 데이터를 확보하라",
        "waves": [12],  # DATA_COLLECT 목표
        "prerequisite": "act3_m1",
        "unlocks": ["act3_m3"],
        "rewards": MissionReward(credits=450, exp=220),
    },
    "act3_m3": {
        "type": MissionType.STORY,
        "category": MissionCategory.MAIN,
        "act": 3,
        "name": "소화 시스템",
        "name_en": "Fire Suppression",
        "description": "소화 시스템을 가동하여 화재를 진압하라",
        "waves": [13],  # DEFENSE 목표
        "prerequisite": "act3_m2",
        "unlocks": ["act3_m4", "side_defense_3"],
        "rewards": MissionReward(credits=400, exp=200),
    },
    "act3_m4": {
        "type": MissionType.STORY,
        "category": MissionCategory.MAIN,
        "act": 3,
        "name": "과학자 구출",
        "name_en": "Scientist Rescue",
        "description": "갇힌 과학자들을 구출하라",
        "waves": [14],  # RESCUE 목표
        "prerequisite": "act3_m3",
        "unlocks": ["act3_m5"],
        "rewards": MissionReward(credits=500, exp=250),
    },
    "act3_m5": {
        "type": MissionType.STORY,
        "category": MissionCategory.MAIN,
        "act": 3,
        "name": "인페르노 가디언",
        "name_en": "Inferno Guardian",
        "description": "연구소 수호자를 처치하라",
        "waves": [15],  # 보스 웨이브
        "prerequisite": "act3_m4",
        "unlocks": ["act4_m1"],
        "rewards": MissionReward(credits=700, exp=300, unlock_ship="bomber"),
        "is_boss": True,
    },

    # =========================================================================
    # ACT 4: 잊힌 진실
    # =========================================================================
    "act4_m1": {
        "type": MissionType.STORY,
        "category": MissionCategory.MAIN,
        "act": 4,
        "name": "사령부 진입",
        "name_en": "HQ Breach",
        "description": "카오스 사령부 진입로를 확보하라",
        "waves": [16],
        "prerequisite": "act3_m5",
        "unlocks": ["act4_m2"],
        "rewards": MissionReward(credits=500, exp=280),
    },
    "act4_m2": {
        "type": MissionType.STORY,
        "category": MissionCategory.MAIN,
        "act": 4,
        "name": "통신 타워",
        "name_en": "Comm Tower",
        "description": "통신 타워를 방어하며 좌표를 전송하라",
        "waves": [17],  # DEFENSE 목표
        "prerequisite": "act4_m1",
        "unlocks": ["act4_m3"],
        "rewards": MissionReward(credits=550, exp=300),
    },
    "act4_m3": {
        "type": MissionType.STORY,
        "category": MissionCategory.MAIN,
        "act": 4,
        "name": "대규모 공습",
        "name_en": "Massive Assault",
        "description": "대규모 카오스 공습을 막아내라",
        "waves": [18],  # SURVIVAL 목표
        "prerequisite": "act4_m2",
        "unlocks": ["act4_m4", "side_siege_3"],
        "rewards": MissionReward(credits=600, exp=320),
    },
    "act4_m4": {
        "type": MissionType.STORY,
        "category": MissionCategory.MAIN,
        "act": 4,
        "name": "좌표 완성",
        "name_en": "Coordinates Complete",
        "description": "차원 게이트 좌표를 완성하라",
        "waves": [19],  # DATA_COLLECT 목표
        "prerequisite": "act4_m3",
        "unlocks": ["act4_m5"],
        "rewards": MissionReward(credits=550, exp=300),
    },
    "act4_m5": {
        "type": MissionType.STORY,
        "category": MissionCategory.MAIN,
        "act": 4,
        "name": "기억의 망령",
        "name_en": "Memory Wraith",
        "description": "과거의 망령을 처치하라",
        "waves": [20],  # 보스 웨이브
        "prerequisite": "act4_m4",
        "unlocks": ["act5_m1"],
        "rewards": MissionReward(credits=800, exp=400),
        "is_boss": True,
    },

    # =========================================================================
    # ACT 5: 새벽의 결의
    # =========================================================================
    "act5_m1": {
        "type": MissionType.STORY,
        "category": MissionCategory.MAIN,
        "act": 5,
        "name": "방어선 돌파",
        "name_en": "Breach Defense",
        "description": "카오스 최종 방어선을 돌파하라",
        "waves": [21],
        "prerequisite": "act4_m5",
        "unlocks": ["act5_m2"],
        "rewards": MissionReward(credits=600, exp=350),
    },
    "act5_m2": {
        "type": MissionType.STORY,
        "category": MissionCategory.MAIN,
        "act": 5,
        "name": "게이트 동력",
        "name_en": "Gate Power",
        "description": "차원 게이트 동력원을 가동하라",
        "waves": [22],  # DEFENSE 목표
        "prerequisite": "act5_m1",
        "unlocks": ["act5_m3"],
        "rewards": MissionReward(credits=650, exp=380),
    },
    "act5_m3": {
        "type": MissionType.STORY,
        "category": MissionCategory.MAIN,
        "act": 5,
        "name": "차원 열쇠",
        "name_en": "Dimensional Key",
        "description": "차원 열쇠를 안전하게 운반하라",
        "waves": [23],  # ESCORT 목표
        "prerequisite": "act5_m2",
        "unlocks": ["act5_m4"],
        "rewards": MissionReward(credits=700, exp=400),
    },
    "act5_m4": {
        "type": MissionType.STORY,
        "category": MissionCategory.MAIN,
        "act": 5,
        "name": "최후 저항",
        "name_en": "Final Stand",
        "description": "카오스의 최후 저항을 섬멸하라",
        "waves": [24],
        "prerequisite": "act5_m3",
        "unlocks": ["act5_m5"],
        "rewards": MissionReward(credits=750, exp=420),
    },
    "act5_m5": {
        "type": MissionType.STORY,
        "category": MissionCategory.MAIN,
        "act": 5,
        "name": "카오스 사령관",
        "name_en": "Chaos Commander",
        "description": "카오스 사령관을 처치하고 전쟁을 끝내라",
        "waves": [25],  # 최종 보스
        "prerequisite": "act5_m4",
        "unlocks": [],  # 게임 클리어
        "rewards": MissionReward(credits=2000, exp=1000),
        "is_boss": True,
        "is_final": True,
    },
}


# =============================================================================
# 사이드 미션 (선택)
# =============================================================================

SIDE_MISSIONS: Dict[str, Dict[str, Any]] = {
    # =========================================================================
    # 방어 미션 (WaveMode)
    # =========================================================================
    "side_defense_1": {
        "type": MissionType.WAVE,
        "category": MissionCategory.SIDE,
        "name": "모함 방어 훈련",
        "name_en": "Carrier Defense Training",
        "description": "모함을 5웨이브 동안 방어하라",
        "wave_count": 5,
        "difficulty": 1,
        "prerequisite": "act1_m1",
        "unlocks": [],
        "rewards": MissionReward(credits=300, exp=100),
        "repeatable": True,
    },
    "side_defense_2": {
        "type": MissionType.WAVE,
        "category": MissionCategory.SIDE,
        "name": "보급선 호위",
        "name_en": "Supply Convoy Escort",
        "description": "보급선을 7웨이브 동안 호위하라",
        "wave_count": 7,
        "difficulty": 2,
        "prerequisite": "act2_m2",
        "unlocks": [],
        "rewards": MissionReward(credits=450, exp=150),
        "repeatable": True,
    },
    "side_defense_3": {
        "type": MissionType.WAVE,
        "category": MissionCategory.SIDE,
        "name": "전초기지 사수",
        "name_en": "Outpost Defense",
        "description": "전초기지를 10웨이브 동안 사수하라",
        "wave_count": 10,
        "difficulty": 3,
        "prerequisite": "act3_m3",
        "unlocks": [],
        "rewards": MissionReward(credits=600, exp=200),
        "repeatable": True,
    },

    # =========================================================================
    # 공성 미션 (SiegeMode)
    # =========================================================================
    "side_siege_1": {
        "type": MissionType.SIEGE,
        "category": MissionCategory.SIDE,
        "name": "적 초소 파괴",
        "name_en": "Destroy Enemy Outpost",
        "description": "카오스 초소를 파괴하라",
        "difficulty": 1,
        "prerequisite": "act1_m3",
        "unlocks": [],
        "rewards": MissionReward(credits=400, exp=120, unlock_weapon="missile_launcher"),
        "repeatable": False,
    },
    "side_siege_2": {
        "type": MissionType.SIEGE,
        "category": MissionCategory.SIDE,
        "name": "통신 중계소 파괴",
        "name_en": "Destroy Comm Relay",
        "description": "카오스 통신 중계소를 파괴하라",
        "difficulty": 2,
        "prerequisite": "act2_m5",
        "unlocks": [],
        "rewards": MissionReward(credits=550, exp=180),
        "repeatable": False,
    },
    "side_siege_3": {
        "type": MissionType.SIEGE,
        "category": MissionCategory.SIDE,
        "name": "병기 공장 습격",
        "name_en": "Raid Weapon Factory",
        "description": "카오스 병기 공장을 습격하라",
        "difficulty": 3,
        "prerequisite": "act4_m3",
        "unlocks": [],
        "rewards": MissionReward(credits=700, exp=250, unlock_ship="heavy_fighter"),
        "repeatable": False,
    },
}


# =============================================================================
# 훈련장 (무한 웨이브)
# =============================================================================

TRAINING_MISSION: Dict[str, Any] = {
    "training": {
        "type": MissionType.TRAINING,
        "category": MissionCategory.TRAINING,
        "name": "훈련장",
        "name_en": "Training Ground",
        "description": "무한 웨이브에서 실력을 연마하라",
        "wave_count": -1,  # 무한
        "prerequisite": None,  # 항상 사용 가능
        "rewards": MissionReward(),  # 보상 없음
    },
}


# =============================================================================
# 유틸리티 함수
# =============================================================================

def get_all_missions() -> Dict[str, Dict[str, Any]]:
    """모든 미션 데이터 반환"""
    all_missions = {}
    all_missions.update(MAIN_MISSIONS)
    all_missions.update(SIDE_MISSIONS)
    all_missions.update(TRAINING_MISSION)
    return all_missions


def get_mission(mission_id: str) -> Dict[str, Any]:
    """특정 미션 데이터 반환"""
    all_missions = get_all_missions()
    return all_missions.get(mission_id, None)


def get_available_missions(completed_missions: List[str]) -> Dict[str, Dict[str, Any]]:
    """
    현재 진행 가능한 미션 목록 반환

    Args:
        completed_missions: 완료된 미션 ID 목록

    Returns:
        진행 가능한 미션 딕셔너리
    """
    all_missions = get_all_missions()
    available = {}

    for mission_id, mission_data in all_missions.items():
        prerequisite = mission_data.get("prerequisite")

        # 선행 미션이 없거나 완료된 경우
        if prerequisite is None or prerequisite in completed_missions:
            # 이미 완료했고 반복 불가능한 미션 제외
            if mission_id in completed_missions:
                if not mission_data.get("repeatable", False):
                    continue

            available[mission_id] = mission_data

    return available


def get_next_main_mission(completed_missions: List[str]) -> str:
    """다음 메인 스토리 미션 ID 반환"""
    for mission_id, mission_data in MAIN_MISSIONS.items():
        if mission_id in completed_missions:
            continue

        prerequisite = mission_data.get("prerequisite")
        if prerequisite is None or prerequisite in completed_missions:
            return mission_id

    return None  # 모든 미션 완료


def get_unlocked_side_missions(completed_missions: List[str]) -> Dict[str, Dict[str, Any]]:
    """해금된 사이드 미션 목록 반환"""
    unlocked = {}

    for mission_id, mission_data in SIDE_MISSIONS.items():
        prerequisite = mission_data.get("prerequisite")

        if prerequisite is None or prerequisite in completed_missions:
            # 반복 불가능하고 이미 완료한 미션 제외
            if mission_id in completed_missions:
                if not mission_data.get("repeatable", False):
                    continue

            unlocked[mission_id] = mission_data

    return unlocked


def get_current_act(completed_missions: List[str]) -> int:
    """현재 진행 중인 Act 반환"""
    next_mission = get_next_main_mission(completed_missions)

    if next_mission is None:
        return 5  # 모든 미션 완료

    mission_data = get_mission(next_mission)
    return mission_data.get("act", 1)


print("INFO: config_missions.py loaded")
