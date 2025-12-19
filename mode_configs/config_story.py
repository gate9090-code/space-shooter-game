"""
Story Mode Configuration
5 Sets × 5 Waves = 25 Total Waves

스토리: "지구의 마지막 비행사"
- 카오스 vs 안드로메다 우주 전쟁
- 여주인공: 10년 전 카오스 침공으로 가족을 잃은 지구인 비행사
- 아르테미스: 불시착한 안드로메다인, 여주인공의 스승
"""

from pathlib import Path

# =========================================================
# 스토리 모드 배경 설정 (지구 배경)
# =========================================================
STORY_BACKGROUNDS = {
    # Set 1 (Waves 1-5) - 도시 폐허
    1: "bg_ruins.jpg",
    2: "bg_ruins.jpg",
    3: "bg_ruins.jpg",
    4: "bg_ruins.jpg",
    5: "bg_ruins.jpg",

    # Set 2 (Waves 6-10) - 지하 군사 기지
    6: "bg_bunker.jpg",
    7: "bg_bunker.jpg",
    8: "bg_bunker.jpg",
    9: "bg_bunker.jpg",
    10: "bg_bunker.jpg",

    # Set 3 (Waves 11-15) - 불타는 연구소
    11: "bg_lab_fire.jpg",
    12: "bg_lab_fire.jpg",
    13: "bg_lab_fire.jpg",
    14: "bg_lab_fire.jpg",
    15: "bg_lab_fire.jpg",

    # Set 4 (Waves 16-20) - 지구 방어 사령부
    16: "bg_command.jpg",
    17: "bg_command.jpg",
    18: "bg_command.jpg",
    19: "bg_command.jpg",
    20: "bg_command.jpg",

    # Set 5 (Waves 21-25) - 차원 게이트
    21: "bg_gate.jpg",
    22: "bg_gate.jpg",
    23: "bg_gate.jpg",
    24: "bg_gate.jpg",
    25: "bg_gate.jpg",  # Final Boss
}

# 회상 컷씬용 특별 배경
SPECIAL_BACKGROUNDS = {
    "cemetery": "bg_cemetery.jpg",  # 1막 회상: 묘지 공원
}

# =========================================================
# 세트 정보
# =========================================================
SET_INFO = {
    1: {
        "name": "폐허의 귀환",
        "name_en": "RETURN TO RUINS",
        "waves": [1, 2, 3, 4, 5],
        "story": "10년 만에 돌아온 고향...\n폐허가 된 그곳에서 카오스를 발견한다.",
        "color": (180, 100, 80),  # 황폐한 갈색
        "checkpoint_wave": 1,
        "has_memory_cutscene": True,  # 1막에만 회상 컷씬 존재
        "memory_trigger_wave": 2,  # 웨이브 2 클리어 후 발동
        "boss_name": "Shadow Scout",
        "boss_name_kr": "그림자 정찰대장",
    },
    2: {
        "name": "숨겨진 기지",
        "name_en": "HIDDEN OUTPOST",
        "waves": [6, 7, 8, 9, 10],
        "story": "도시 아래 잠든 비밀...\n프로젝트 아크의 흔적을 찾아서.",
        "color": (80, 120, 100),  # 군사 녹색
        "checkpoint_wave": 6,
        "has_cutscene": True,
        "cutscene_trigger_wave": 7,  # 웨이브 7 클리어 후 발동
        "cutscene_type": "classified_document",  # 기밀 문서 효과
        "data_collect_after_cutscene": 3,  # 컷씬 완료 후 3개 데이터 자동 수집
        "data_collect_name": "프로젝트 아크 문서",
        "boss_name": "Data Extractor",
        "boss_name_kr": "데이터 추출자",
    },
    3: {
        "name": "불타는 연구소",
        "name_en": "BURNING LABORATORY",
        "waves": [11, 12, 13, 14, 15],
        "story": "타오르는 불길 속에서\n잊힌 기술의 진실을 마주한다.",
        "color": (200, 120, 60),  # 불꽃 오렌지
        "checkpoint_wave": 11,
        "has_cutscene": True,
        "cutscene_trigger_wave": 12,  # 웨이브 12 클리어 후 발동
        "cutscene_type": "damaged_hologram",  # 손상된 홀로그램 효과
        "data_collect_after_cutscene": 3,  # 컷씬 완료 후 3개 데이터 자동 수집
        "data_collect_name": "게이트 연구 데이터",
        "boss_name": "Inferno Guardian",
        "boss_name_kr": "불꽃 수호자",
    },
    4: {
        "name": "잊힌 진실",
        "name_en": "FORGOTTEN TRUTH",
        "waves": [16, 17, 18, 19, 20],
        "story": "지구 방어 사령부의 기록...\n10년 전 그날의 진실이 밝혀진다.",
        "color": (120, 140, 180),  # 차가운 파랑
        "checkpoint_wave": 16,
        "has_cutscene": True,
        "cutscene_trigger_wave": 17,  # 웨이브 17 클리어 후 발동
        "cutscene_type": "shattered_mirror",  # 깨진 거울 효과
        "data_collect_after_cutscene": 3,  # 컷씬 완료 후 3개 데이터 자동 수집
        "data_collect_name": "사령부 기밀 기록",
        "boss_name": "Memory Phantom",
        "boss_name_kr": "기억의 망령",
    },
    5: {
        "name": "새벽의 결의",
        "name_en": "DAWN'S RESOLUTION",
        "waves": [21, 22, 23, 24, 25],
        "story": "차원 게이트 앞에서\n새로운 결의를 다진다.",
        "color": (160, 100, 200),  # 차원의 보라
        "checkpoint_wave": 21,
        "has_cutscene": True,
        "cutscene_trigger_wave": 22,  # 웨이브 22 클리어 후 발동
        "cutscene_type": "star_map",  # 성간 항해 인터페이스 효과
        "data_collect_after_cutscene": 3,  # 컷씬 완료 후 3개 데이터 자동 수집
        "data_collect_name": "차원 게이트 좌표",
        "boss_name": "Chaos Vanguard Commander",
        "boss_name_kr": "카오스 선봉대 사령관",
    },
}

# =========================================================
# 스토리 모드 게임 플레이 설정
# =========================================================
TOTAL_SETS = 5
WAVES_PER_SET = 5
TOTAL_WAVES = TOTAL_SETS * WAVES_PER_SET  # 25

# 세트 전환 화면 표시 시간 (초)
SET_TRANSITION_DURATION = 4.0

# 세트 완료 화면 표시 시간 (초)
SET_COMPLETE_DISPLAY_TIME = 5.0

# 세트 완료 보상
SET_CLEAR_REWARDS = {
    1: {"coins": 100, "gems": 5},
    2: {"coins": 200, "gems": 10},
    3: {"coins": 300, "gems": 15},
    4: {"coins": 400, "gems": 20},
    5: {"coins": 500, "gems": 30},  # Final reward
}

# =========================================================
# 스토리 모드 적 스폰 설정
# =========================================================
STORY_ENEMY_SCALING = {
    # Set 1: Normal
    1: {"hp_mult": 1.0, "speed_mult": 1.0, "damage_mult": 1.0},
    # Set 2: Slightly harder
    2: {"hp_mult": 1.2, "speed_mult": 1.1, "damage_mult": 1.1},
    # Set 3: Medium
    3: {"hp_mult": 1.5, "speed_mult": 1.2, "damage_mult": 1.2},
    # Set 4: Hard
    4: {"hp_mult": 2.0, "speed_mult": 1.3, "damage_mult": 1.3},
    # Set 5: Very Hard
    5: {"hp_mult": 3.0, "speed_mult": 1.5, "damage_mult": 1.5},
}

# =========================================================
# 체크포인트 시스템
# =========================================================
def get_checkpoint_wave(wave_num: int) -> int:
    """
    주어진 웨이브의 체크포인트 웨이브 번호 반환

    Args:
        wave_num: 현재 웨이브 번호 (1-25)

    Returns:
        체크포인트 웨이브 번호
    """
    set_num = ((wave_num - 1) // WAVES_PER_SET) + 1
    return SET_INFO[set_num]["checkpoint_wave"]


def get_set_number(wave_num: int) -> int:
    """
    주어진 웨이브가 속한 세트 번호 반환

    Args:
        wave_num: 웨이브 번호 (1-25)

    Returns:
        세트 번호 (1-5)
    """
    return ((wave_num - 1) // WAVES_PER_SET) + 1


def is_set_complete(wave_num: int) -> bool:
    """
    현재 웨이브가 세트의 마지막 웨이브인지 확인

    Args:
        wave_num: 웨이브 번호 (1-25)

    Returns:
        세트 완료 여부
    """
    return (wave_num % WAVES_PER_SET) == 0


def get_background_path(wave_num: int) -> Path:
    """
    웨이브에 해당하는 배경 이미지 경로 반환

    Args:
        wave_num: 웨이브 번호 (1-25)

    Returns:
        배경 이미지 경로
    """
    bg_filename = STORY_BACKGROUNDS.get(wave_num, "bg_hangar.jpg")
    # 스토리 모드 전용 배경 폴더 사용
    return Path(f"assets/story_mode/backgrounds/{bg_filename}")


# =========================================================
# 웨이브 목표 시스템
# =========================================================
class WaveObjective:
    """웨이브 목표 유형"""
    EXTERMINATION = "extermination"  # 적 N마리 처치
    SURVIVAL = "survival"            # N초 동안 생존
    DEFENSE = "defense"              # 오브젝트 방어
    DATA_COLLECT = "data_collect"    # 데이터 수집
    ESCORT = "escort"                # 대상 호위
    RESCUE = "rescue"                # NPC 구출
    BOSS_HUNT = "boss_hunt"          # 보스 처치


# Act별 웨이브 목표 설정
WAVE_OBJECTIVES = {
    # ACT 1: 폐허의 귀환
    1: {
        "type": WaveObjective.EXTERMINATION,
        "target": 15,
        "description": "정찰을 위해 잔류군 제거",
        "description_en": "Eliminate remnants for reconnaissance",
    },
    2: {
        "type": WaveObjective.EXTERMINATION,
        "target": 18,
        "description": "잔류군 격파 및 지역 확보",
        "description_en": "Defeat remnants and secure area",
    },
    3: {
        "type": WaveObjective.SURVIVAL,
        "target": 60,  # 60초
        "description": "카오스 추격대로부터 도망",
        "description_en": "Escape from Chaos pursuers",
    },
    4: {
        "type": WaveObjective.EXTERMINATION,
        "target": 20,
        "description": "안전 구역 확보",
        "description_en": "Secure safe zone",
    },
    5: {
        "type": WaveObjective.BOSS_HUNT,
        "target": 1,
        "description": "섀도우 스카우트 처치",
        "description_en": "Defeat Shadow Scout",
    },
    # ACT 2: 숨겨진 기지
    6: {
        "type": WaveObjective.DEFENSE,
        "target": 45,  # 45초
        "description": "벙커 입구 방어",
        "description_en": "Defend bunker entrance",
    },
    7: {
        "type": WaveObjective.EXTERMINATION,
        "target": 20,
        "description": "벙커 내부 소탕",
        "description_en": "Clear bunker interior",
    },
    8: {
        "type": WaveObjective.EXTERMINATION,
        "target": 22,
        "description": "벙커 중앙 구역 소탕",
        "description_en": "Clear bunker central area",
    },
    9: {
        "type": WaveObjective.ESCORT,
        "target": 100,  # 100% 진행률
        "description": "생존자 캡슐 호위",
        "description_en": "Escort survivor capsule",
    },
    10: {
        "type": WaveObjective.BOSS_HUNT,
        "target": 1,
        "description": "데이터 추출자 처치",
        "description_en": "Defeat Data Extractor",
    },
    # ACT 3: 불타는 연구소
    11: {
        "type": WaveObjective.SURVIVAL,
        "target": 75,  # 75초
        "description": "화염 속 탈출구 탐색",
        "description_en": "Search for escape in flames",
        "hazard": "fire",
    },
    12: {
        "type": WaveObjective.EXTERMINATION,
        "target": 20,
        "description": "연구소 구역 확보",
        "description_en": "Secure laboratory area",
    },
    13: {
        "type": WaveObjective.DEFENSE,
        "target": 60,  # 60초
        "description": "소화 시스템 가동",
        "description_en": "Activate fire suppression",
    },
    14: {
        "type": WaveObjective.RESCUE,
        "target": 2,
        "description": "갇힌 과학자 구출",
        "description_en": "Rescue trapped scientists",
    },
    15: {
        "type": WaveObjective.BOSS_HUNT,
        "target": 1,
        "description": "인페르노 가디언 처치",
        "description_en": "Defeat Inferno Guardian",
    },
    # ACT 4: 잊힌 진실
    16: {
        "type": WaveObjective.EXTERMINATION,
        "target": 25,
        "description": "사령부 진입로 확보",
        "description_en": "Secure command center entrance",
    },
    17: {
        "type": WaveObjective.DEFENSE,
        "target": 90,  # 90초
        "description": "통신 타워 방어",
        "description_en": "Defend communication tower",
    },
    18: {
        "type": WaveObjective.SURVIVAL,
        "target": 120,  # 120초
        "description": "대규모 공습 방어",
        "description_en": "Survive massive assault",
    },
    19: {
        "type": WaveObjective.EXTERMINATION,
        "target": 25,
        "description": "사령부 핵심 구역 돌파",
        "description_en": "Break through command center core",
    },
    20: {
        "type": WaveObjective.BOSS_HUNT,
        "target": 1,
        "description": "기억의 망령 처치",
        "description_en": "Defeat Memory Phantom",
    },
    # ACT 5: 새벽의 결의
    21: {
        "type": WaveObjective.EXTERMINATION,
        "target": 25,
        "description": "방어선 제거",
        "description_en": "Destroy defense line",
    },
    22: {
        "type": WaveObjective.DEFENSE,
        "target": 120,  # 120초
        "description": "게이트 동력원 가동",
        "description_en": "Activate gate power source",
    },
    23: {
        "type": WaveObjective.ESCORT,
        "target": 100,
        "description": "차원 열쇠 운반",
        "description_en": "Transport dimensional key",
    },
    24: {
        "type": WaveObjective.EXTERMINATION,
        "target": 30,
        "description": "최후 저항군 섬멸",
        "description_en": "Annihilate final resistance",
    },
    25: {
        "type": WaveObjective.BOSS_HUNT,
        "target": 1,
        "description": "카오스 사령관 처치",
        "description_en": "Defeat Chaos Commander",
    },
}


# =========================================================
# Act별 환경 메커니즘
# =========================================================
ACT_MECHANICS = {
    # ACT 1: 폐허 (Collapsing Ruins)
    1: {
        "name": "무너지는 폐허",
        "name_en": "Collapsing Ruins",
        "mechanics": [
            {
                "type": "falling_debris",
                "interval": 10.0,  # 10초마다
                "warning_time": 2.0,  # 2초 경고
                "damage": 20,
                "description": "무너지는 잔해 - 경고 후 낙하",
            },
            {
                "type": "dust_storm",
                "waves": [3, 4],  # 적용 웨이브
                "visibility_reduction": 0.3,  # 시야 30% 감소
                "enemy_speed_reduction": 0.2,  # 적 속도 20% 감소
                "description": "먼지 폭풍 - 시야 감소",
            },
        ],
        "visual_effects": ["dust_particles", "debris_fall"],
    },
    # ACT 2: 지하 벙커 (Underground Bunker)
    2: {
        "name": "지하 벙커",
        "name_en": "Underground Bunker",
        "mechanics": [
            {
                "type": "ally_turret",
                "count": 3,
                "damage": 15,
                "fire_rate": 1.0,
                "description": "아군 터렛 - 지원 사격",
            },
            {
                "type": "narrow_corridor",
                "funnel_points": [(400, 300), (800, 300), (600, 500)],
                "description": "좁은 통로 - 적 병목",
            },
            {
                "type": "blast_door",
                "waves": [7, 9],
                "time_limit": 30.0,  # 30초 내 통과
                "description": "방화문 - 시간 내 통과",
            },
        ],
        "visual_effects": ["bunker_lights", "steam_vents"],
    },
    # ACT 3: 불타는 연구소 (Burning Lab)
    3: {
        "name": "불타는 연구소",
        "name_en": "Burning Laboratory",
        "mechanics": [
            {
                "type": "fire_spread",
                "interval": 20.0,  # 20초마다 확산
                "safe_zone_shrink": 0.1,  # 안전 구역 10% 축소
                "damage_per_second": 5,
                "description": "화염 확산 - 안전 구역 축소",
            },
            {
                "type": "explosive_barrel",
                "count": 5,
                "explosion_radius": 100,
                "damage": 50,
                "chain_reaction": True,
                "description": "폭발물 통 - 연쇄 폭발",
            },
            {
                "type": "sprinkler_system",
                "trigger": "defense_complete",
                "effect": "extinguish_fire",
                "description": "스프링클러 - 화염 진화",
            },
        ],
        "visual_effects": ["fire_particles", "smoke", "ember_glow"],
    },
    # ACT 4: 통신 기지 (Comm Base)
    4: {
        "name": "통신 기지",
        "name_en": "Communication Base",
        "mechanics": [
            {
                "type": "transmission_progress",
                "base_speed": 1.0,
                "enemy_proximity_penalty": 0.5,  # 적 근접 시 속도 감소
                "description": "전송 진행률 - 적 근접 시 감소",
            },
            {
                "type": "emp_wave",
                "interval": 30.0,  # 30초마다
                "skill_disable_duration": 5.0,  # 스킬 5초 비활성화
                "description": "EMP 파동 - 스킬 일시 비활성화",
            },
            {
                "type": "support_drone",
                "trigger": "hp_below_30",
                "heal_amount": 50,
                "cooldown": 60.0,
                "description": "지원 드론 - 위기 시 지원",
            },
        ],
        "visual_effects": ["hologram_static", "antenna_pulse"],
    },
    # ACT 5: 차원 게이트 (Dimensional Gate)
    5: {
        "name": "차원 게이트",
        "name_en": "Dimensional Gate",
        "mechanics": [
            {
                "type": "dimensional_rift",
                "interval": 15.0,  # 15초마다
                "spawn_portal_duration": 5.0,
                "enemy_teleport": True,
                "description": "차원 균열 - 적 순간이동 포탈",
            },
            {
                "type": "gravity_anomaly",
                "zones": [(300, 200), (700, 400), (500, 600)],
                "radius": 80,
                "trajectory_bend": 30,  # 각도
                "description": "중력 이상 - 탄환/적 궤도 변경",
            },
            {
                "type": "gate_charge",
                "per_kill": 2,  # 킬당 2% 충전
                "max_charge": 100,
                "description": "게이트 충전 - 적 처치 시 에너지 충전",
            },
        ],
        "visual_effects": ["portal_swirl", "energy_field", "dimensional_crack"],
    },
}


# =========================================================
# 지구 갤러리 시스템 (수집 요소)
# =========================================================
EARTH_GALLERY = {
    "total_fragments": 20,
    "fragments_per_act": 4,
    "seasons": {
        "spring": {
            "name": "봄",
            "fragments": [
                {"id": "spring_1", "image": "gallery_spring_cherry.jpg", "description": "매년 이맘때면 가족과 벚꽃 구경을 갔었어."},
                {"id": "spring_2", "image": "gallery_spring_park.jpg", "description": "엄마가 좋아하던 산책로야."},
                {"id": "spring_3", "image": "gallery_spring_garden.jpg", "description": "우리 집 정원에 피던 꽃들..."},
                {"id": "spring_4", "image": "gallery_spring_rain.jpg", "description": "봄비 내리던 날의 냄새가 아직도 기억나."},
                {"id": "spring_5", "image": "gallery_spring_sunrise.jpg", "description": "새벽에 일어나 본 봄의 일출."},
            ],
        },
        "summer": {
            "name": "여름",
            "fragments": [
                {"id": "summer_1", "image": "gallery_summer_beach.jpg", "description": "아빠랑 수영 배웠던 곳..."},
                {"id": "summer_2", "image": "gallery_summer_forest.jpg", "description": "숨바꼭질하던 숲이 이렇게 아름다웠구나."},
                {"id": "summer_3", "image": "gallery_summer_sunset.jpg", "description": "여름 저녁의 노을..."},
                {"id": "summer_4", "image": "gallery_summer_stars.jpg", "description": "캠핑 가서 본 별들."},
                {"id": "summer_5", "image": "gallery_summer_firefly.jpg", "description": "반딧불이 날아다니던 밤."},
            ],
        },
        "autumn": {
            "name": "가을",
            "fragments": [
                {"id": "autumn_1", "image": "gallery_autumn_mountain.jpg", "description": "단풍놀이... 다시 갈 수 있을까."},
                {"id": "autumn_2", "image": "gallery_autumn_field.jpg", "description": "추수 때 할머니 댁에 갔었지."},
                {"id": "autumn_3", "image": "gallery_autumn_leaves.jpg", "description": "낙엽 밟던 소리가 좋았어."},
                {"id": "autumn_4", "image": "gallery_autumn_moon.jpg", "description": "추석에 본 보름달."},
                {"id": "autumn_5", "image": "gallery_autumn_harvest.jpg", "description": "풍요로웠던 수확의 계절."},
            ],
        },
        "winter": {
            "name": "겨울",
            "fragments": [
                {"id": "winter_1", "image": "gallery_winter_snow.jpg", "description": "첫눈 오던 날, 모두가 웃었어."},
                {"id": "winter_2", "image": "gallery_winter_christmas.jpg", "description": "마지막 크리스마스... 10년 전이야."},
                {"id": "winter_3", "image": "gallery_winter_fireplace.jpg", "description": "벽난로 앞에서 따뜻했던 밤."},
                {"id": "winter_4", "image": "gallery_winter_aurora.jpg", "description": "오로라를 본 적 있어... 꿈같았어."},
                {"id": "winter_5", "image": "gallery_winter_newyear.jpg", "description": "새해 첫날의 희망찬 아침."},
            ],
        },
    },
    "drop_rates": {
        "normal_enemy": 0.05,  # 5%
        "elite_enemy": 0.15,   # 15%
        "boss": 1.0,           # 100% (확정)
    },
    "rewards": {
        "season_complete": "해당 계절 배경 스킨 해금",
        "all_complete": "숨겨진 에필로그 해금",
    },
}


def get_wave_objective(wave_num: int) -> dict:
    """웨이브 목표 정보 반환"""
    return WAVE_OBJECTIVES.get(wave_num, {
        "type": WaveObjective.EXTERMINATION,
        "target": 15,
        "description": "적 섬멸",
        "description_en": "Eliminate enemies",
    })


def get_act_mechanics(act_num: int) -> dict:
    """Act별 환경 메커니즘 반환"""
    return ACT_MECHANICS.get(act_num, {})


def get_gallery_fragment_info(fragment_id: str) -> dict:
    """갤러리 조각 정보 반환"""
    for season_data in EARTH_GALLERY["seasons"].values():
        for fragment in season_data["fragments"]:
            if fragment["id"] == fragment_id:
                return fragment
    return {}


print("INFO: config_story.py loaded")
