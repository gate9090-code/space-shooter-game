# mode_configs/config_episodes.py
"""
Episode 시스템 설정
- Episode: 미션의 상위 단위, 여러 Segment로 구성
- Segment: 개별 장면 (전투, 대화, 탐색, 성찰 등)
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum, auto


class SegmentType(Enum):
    """Segment 타입 정의"""
    BRIEFING = auto()      # 미션 브리핑
    COMBAT = auto()        # 웨이브 전투
    DIALOGUE = auto()      # 캐릭터 대화
    EXPLORATION = auto()   # 환경 탐색
    REFLECTION = auto()    # 철학적 성찰
    CUTSCENE = auto()      # 컷씬 연출
    ENDING = auto()        # 미션 종료


@dataclass
class SegmentData:
    """Segment 데이터 구조"""
    type: SegmentType

    # 공통
    background: Optional[str] = None

    # BRIEFING / DIALOGUE / ENDING
    dialogue_key: Optional[str] = None

    # COMBAT
    waves: Optional[List[int]] = None
    boss: bool = False

    # CUTSCENE
    effect: Optional[str] = None
    images: Optional[List[str]] = None

    # REFLECTION
    scene_key: Optional[str] = None
    optional: bool = True
    trigger_condition: Optional[str] = None

    # EXPLORATION
    points: Optional[List[str]] = None

    # 추가 데이터
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EpisodeData:
    """Episode 데이터 구조"""
    id: str
    title: str
    act: int
    segments: List[SegmentData]

    # 메타데이터
    description: str = ""
    unlock_condition: Optional[str] = None
    rewards: Dict[str, Any] = field(default_factory=dict)


# =========================================================
# Episode 정의
# =========================================================

EPISODES: Dict[str, EpisodeData] = {
    # ===== Act 1: 지구의 잔해 =====
    "ep1_return": EpisodeData(
        id="ep1_return",
        title="지구 귀환",
        act=1,
        description="3년 만의 귀환, 폐허가 된 지구 궤도 진입",
        segments=[
            SegmentData(
                type=SegmentType.BRIEFING,
                dialogue_key="act1_opening",  # 기존 JSON 파일과 일치
                background="bg_ruins.jpg"
            ),
            SegmentData(
                type=SegmentType.CUTSCENE,
                effect="FadeInEffect",
                background="bg_ruins.jpg",
                extra={"duration": 2.0}  # 컷씬 지속 시간
            ),
            SegmentData(
                type=SegmentType.COMBAT,
                waves=[1, 2, 3],
                background="bg_ruins.jpg"
            ),
            SegmentData(
                type=SegmentType.DIALOGUE,
                dialogue_key="act1_mid",  # 새로 생성 필요
                background="bg_ruins.jpg"
            ),
            SegmentData(
                type=SegmentType.COMBAT,
                waves=[4, 5],
                boss=True,
                background="bg_ruins.jpg"
            ),
            SegmentData(
                type=SegmentType.ENDING,
                dialogue_key="act1_ending"  # 새로 생성 필요
            )
        ],
        rewards={"credits": 200, "exp": 100}
    ),

    # ===== Act 2: 폐허 속의 메아리 =====
    "ep2_echoes": EpisodeData(
        id="ep2_echoes",
        title="폐허 속의 메아리",
        act=2,
        description="생존자 신호 추적, 과거의 기억과 마주함",
        segments=[
            SegmentData(
                type=SegmentType.BRIEFING,
                dialogue_key="ep2_briefing",
                background="bg_command.jpg"
            ),
            SegmentData(
                type=SegmentType.CUTSCENE,
                effect="PolaroidMemoryEffect",
                images=["memory_seoul_01.jpg", "memory_seoul_02.jpg"],
                background="bg_ruins.jpg"
            ),
            SegmentData(
                type=SegmentType.COMBAT,
                waves=[1, 2],
                background="bg_ruins.jpg"
            ),
            SegmentData(
                type=SegmentType.REFLECTION,
                scene_key="color_names",
                optional=True,
                trigger_condition="first_play",
                background="bg_spring_cherry.jpg"
            ),
            SegmentData(
                type=SegmentType.EXPLORATION,
                points=["building", "vehicle", "billboard"],
                background="bg_ruins.jpg"
            ),
            SegmentData(
                type=SegmentType.REFLECTION,
                scene_key="cloud_shapes",
                optional=True,
                background="bg_summer_sky.jpg"
            ),
            SegmentData(
                type=SegmentType.DIALOGUE,
                dialogue_key="ep2_survivor_signal",
                background="bg_ruins.jpg"
            ),
            SegmentData(
                type=SegmentType.COMBAT,
                waves=[3, 4, 5],
                boss=True,
                background="bg_ruins.jpg"
            ),
            SegmentData(
                type=SegmentType.ENDING,
                dialogue_key="ep2_mission_complete"
            )
        ],
        unlock_condition="ep1_return",
        rewards={"credits": 300, "exp": 150}
    ),

    # ===== Act 3: 블랙박스 =====
    "ep3_blackbox": EpisodeData(
        id="ep3_blackbox",
        title="블랙박스",
        act=3,
        description="격추된 카이론 정찰기에서 데이터 회수",
        segments=[
            SegmentData(
                type=SegmentType.BRIEFING,
                dialogue_key="ep3_briefing",
                background="bg_command.jpg"
            ),
            SegmentData(
                type=SegmentType.CUTSCENE,
                effect="FadeInEffect",
                background="bg_debris_field.jpg"
            ),
            SegmentData(
                type=SegmentType.COMBAT,
                waves=[1, 2, 3],
                background="bg_debris_field.jpg"
            ),
            SegmentData(
                type=SegmentType.REFLECTION,
                scene_key="rain_smell",
                optional=True,
                background="bg_autumn_rain.jpg"
            ),
            SegmentData(
                type=SegmentType.REFLECTION,
                scene_key="why_stars_beautiful",
                optional=True,
                background="bg_winter_night.jpg"
            ),
            SegmentData(
                type=SegmentType.DIALOGUE,
                dialogue_key="ep3_data_recovery",
                background="bg_debris_field.jpg"
            ),
            SegmentData(
                type=SegmentType.COMBAT,
                waves=[4, 5],
                boss=True,
                background="bg_debris_field.jpg"
            ),
            SegmentData(
                type=SegmentType.ENDING,
                dialogue_key="ep3_mission_complete"
            )
        ],
        unlock_condition="ep2_echoes",
        rewards={"credits": 400, "exp": 200}
    ),

    # ===== Act 4: 덫 =====
    "ep4_trap": EpisodeData(
        id="ep4_trap",
        title="덫",
        act=4,
        description="데이터 회수 중 적 증원 도착, 포위됨",
        segments=[
            SegmentData(
                type=SegmentType.BRIEFING,
                dialogue_key="ep4_briefing",
                background="bg_command.jpg"
            ),
            SegmentData(
                type=SegmentType.COMBAT,
                waves=[1, 2],
                background="bg_ambush.jpg"
            ),
            SegmentData(
                type=SegmentType.CUTSCENE,
                effect="AmbushEffect",
                background="bg_ambush.jpg",
                extra={"phase_dialogues": "act4_ambush"}
            ),
            SegmentData(
                type=SegmentType.REFLECTION,
                scene_key="why_flowers_fall",
                optional=True,
                background="bg_fallen_flowers.jpg"
            ),
            SegmentData(
                type=SegmentType.REFLECTION,
                scene_key="andromeda_records",
                optional=True,
                background="bg_andromeda_city.jpg"
            ),
            SegmentData(
                type=SegmentType.REFLECTION,
                scene_key="eternity_vs_moment",
                optional=True,
                background="bg_winter_night.jpg"
            ),
            SegmentData(
                type=SegmentType.COMBAT,
                waves=[3, 4, 5],
                boss=True,
                background="bg_ambush.jpg"
            ),
            SegmentData(
                type=SegmentType.ENDING,
                dialogue_key="ep4_mission_complete"
            )
        ],
        unlock_condition="ep3_blackbox",
        rewards={"credits": 500, "exp": 250}
    ),

    # ===== Act 5: 돌파 =====
    "ep5_breakthrough": EpisodeData(
        id="ep5_breakthrough",
        title="돌파",
        act=5,
        description="포위망 돌파, 최종 결전",
        segments=[
            SegmentData(
                type=SegmentType.BRIEFING,
                dialogue_key="ep5_briefing",
                background="bg_command.jpg"
            ),
            SegmentData(
                type=SegmentType.REFLECTION,
                scene_key="chaos_eats_time",
                optional=False,  # 필수 씬
                background="bg_winter_night.jpg"
            ),
            SegmentData(
                type=SegmentType.COMBAT,
                waves=[1, 2, 3],
                background="bg_breakthrough.jpg"
            ),
            SegmentData(
                type=SegmentType.REFLECTION,
                scene_key="why_andromeda_stopped_time",
                optional=False,  # 필수 씬
                background="bg_andromeda_city.jpg"
            ),
            SegmentData(
                type=SegmentType.DIALOGUE,
                dialogue_key="ep5_revelation",
                background="bg_breakthrough.jpg"
            ),
            SegmentData(
                type=SegmentType.COMBAT,
                waves=[4, 5],
                boss=True,
                background="bg_final_boss.jpg"
            ),
            SegmentData(
                type=SegmentType.REFLECTION,
                scene_key="does_time_exist",
                optional=False,  # 필수 씬 - 최종 철학 대화
                background="bg_gate.jpg"
            ),
            SegmentData(
                type=SegmentType.CUTSCENE,
                effect="VictoryEffect",
                background="bg_victory.jpg"
            ),
            SegmentData(
                type=SegmentType.ENDING,
                dialogue_key="ep5_mission_complete"
            )
        ],
        unlock_condition="ep4_trap",
        rewards={"credits": 1000, "exp": 500}
    )
}


# =========================================================
# JSON 기반 Episode 로더
# =========================================================

import json
from pathlib import Path

_json_episode_cache: Dict[str, EpisodeData] = {}


def _load_episode_from_json(episode_id: str) -> Optional[EpisodeData]:
    """JSON 파일에서 Episode 데이터 로드"""
    if episode_id in _json_episode_cache:
        return _json_episode_cache[episode_id]

    # JSON 파일 경로: data/episodes/{ep_id}/{ep_id}.json
    json_path = Path("assets/data/episodes") / episode_id / f"{episode_id}.json"

    if not json_path.exists():
        return None

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # scenes 데이터 (새 통합 구조)
        scenes = data.get("scenes", {})
        defaults = data.get("defaults", {})

        # Segment 데이터 변환
        segments = []
        for seg_data in data.get("segments", []):
            seg_type_str = seg_data.get("type", "DIALOGUE")
            try:
                seg_type = SegmentType[seg_type_str]
            except KeyError:
                print(f"WARNING: Unknown segment type: {seg_type_str}")
                continue

            # scene 키로 dialogue_key 결정 (새 구조)
            scene_name = seg_data.get("scene", "")
            dialogue_key = seg_data.get("dialogue_key") or scene_name

            # scene 데이터에서 배경 가져오기
            scene_data = scenes.get(scene_name, {}) if scene_name else {}
            background = seg_data.get("background") or scene_data.get("background") or defaults.get("background")

            # COMBAT 타입 처리
            boss = seg_data.get("boss")
            if isinstance(boss, str):
                # boss가 문자열이면 boss 타입 지정 (True로 처리)
                boss_name = boss
                boss = True
            else:
                boss_name = None
                boss = bool(boss)

            segment = SegmentData(
                type=seg_type,
                background=background,
                dialogue_key=dialogue_key,
                waves=seg_data.get("waves"),
                boss=boss,
                effect=seg_data.get("effect") or scene_data.get("effect"),
                images=seg_data.get("images") or scene_data.get("effect_data", {}).get("polaroid_images"),
                scene_key=seg_data.get("scene_key") or scene_name,
                optional=seg_data.get("optional", True),
                trigger_condition=seg_data.get("trigger_condition"),
                points=seg_data.get("points"),
                extra={
                    "rounds": seg_data.get("rounds"),
                    "enemies": seg_data.get("enemies"),
                    "spawn_rate": seg_data.get("spawn_rate"),
                    "duration": seg_data.get("duration"),
                    "location": scene_data.get("location", ""),
                    "color_tone": seg_data.get("color_tone"),
                    "boss_name": boss_name,
                    "effect_data": scene_data.get("effect_data", {}),
                }
            )
            segments.append(segment)

        # act 결정 (id에서 추출 또는 기본값)
        act = data.get("act", 1)
        if not act and episode_id.startswith("ep"):
            try:
                act = int(episode_id[2])  # "ep1" -> 1
            except (IndexError, ValueError):
                act = 1

        # EpisodeData 생성
        episode = EpisodeData(
            id=data.get("id", episode_id),
            title=data.get("title", ""),
            act=act,
            segments=segments,
            description=data.get("description", ""),
            unlock_condition=data.get("unlock_next"),  # JSON에서는 unlock_next 사용
            rewards=data.get("rewards", {})
        )

        _json_episode_cache[episode_id] = episode
        print(f"INFO: Loaded episode from JSON: {episode_id} ({len(segments)} segments)")
        return episode

    except Exception as e:
        print(f"WARNING: Failed to load episode JSON {episode_id}: {e}")
        import traceback
        traceback.print_exc()
        return None


# =========================================================
# Episode 헬퍼 함수
# =========================================================

def get_episode(episode_id: str) -> Optional[EpisodeData]:
    """Episode ID로 데이터 가져오기 (JSON 우선, Python 폴백)"""
    # ID 별칭 매핑 (레거시 ID → 새 ID)
    id_aliases = {
        "ep1_return": "ep1",
        "ep2_echoes": "ep2",
        "ep3_blackbox": "ep3",
        "ep4_trap": "ep4",
        "ep5_breakthrough": "ep5",
    }

    # 별칭 변환
    resolved_id = id_aliases.get(episode_id, episode_id)

    # 1순위: JSON 파일 (새 구조 폴더)
    episode = _load_episode_from_json(resolved_id)
    if episode:
        return episode

    # 2순위: JSON 파일 (원래 ID로 재시도)
    if resolved_id != episode_id:
        episode = _load_episode_from_json(episode_id)
        if episode:
            return episode

    # 3순위: Python 정의
    return EPISODES.get(episode_id)


def get_episodes_by_act(act: int) -> List[EpisodeData]:
    """특정 Act의 모든 Episode 가져오기"""
    return [ep for ep in EPISODES.values() if ep.act == act]


def get_all_episode_ids() -> List[str]:
    """모든 Episode ID 목록"""
    return list(EPISODES.keys())


def is_episode_unlocked(episode_id: str, completed_episodes: List[str]) -> bool:
    """Episode 해금 여부 확인"""
    episode = get_episode(episode_id)
    if not episode:
        return False

    # 해금 조건이 없으면 자동 해금
    if not episode.unlock_condition:
        return True

    # 해금 조건 Episode가 완료되었는지 확인
    return episode.unlock_condition in completed_episodes


def get_next_episode(current_episode_id: str) -> Optional[str]:
    """다음 Episode ID 반환"""
    episode_ids = get_all_episode_ids()
    try:
        current_index = episode_ids.index(current_episode_id)
        if current_index + 1 < len(episode_ids):
            return episode_ids[current_index + 1]
    except ValueError:
        pass
    return None


# =========================================================
# Segment 타입별 기본 설정
# =========================================================

SEGMENT_DEFAULTS = {
    SegmentType.BRIEFING: {
        "skip_allowed": True,
        "auto_advance": False,
        "duration": None  # 클릭으로 진행
    },
    SegmentType.COMBAT: {
        "skip_allowed": False,
        "auto_advance": True,
        "duration": None  # 전투 완료 시 자동 진행
    },
    SegmentType.DIALOGUE: {
        "skip_allowed": True,
        "auto_advance": False,
        "duration": None
    },
    SegmentType.EXPLORATION: {
        "skip_allowed": True,
        "auto_advance": False,
        "duration": 60.0  # 최대 탐색 시간
    },
    SegmentType.REFLECTION: {
        "skip_allowed": True,
        "auto_advance": False,
        "duration": None
    },
    SegmentType.CUTSCENE: {
        "skip_allowed": True,
        "auto_advance": True,
        "duration": 5.0  # 기본 지속 시간
    },
    SegmentType.ENDING: {
        "skip_allowed": False,
        "auto_advance": False,
        "duration": None
    }
}


print("INFO: config_episodes.py loaded")
