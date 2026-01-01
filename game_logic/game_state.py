# game_logic/game_state.py
"""
Game state management functions.
Handles game data initialization, level progression, and state transitions.
"""

import config
from typing import Dict
from entities.player import Player


def reset_game_data() -> Dict:
    """게임 세션에 특화된 데이터를 초기화합니다."""
    return {
        "game_state": config.GAME_STATE_WAVE_PREPARE,  # 첫 웨이브 시작 전 대기
        "player_level": 1,
        "kill_count": 0,
        "score": 0,
        "uncollected_score": 0,  # 레벨업에 사용될 미회수 점수
        "last_enemy_spawn_time": 0.0, # 스폰 시간 추적을 game_data로 통합
        "last_gem_spawn_time": 0.0,   # 스폰 시간 추적을 game_data로 통합
        "enemy_spawn_interval_reduction": 0.0,
        # 웨이브 시스템
        "current_wave": 1,  # 현재 웨이브
        "wave_kills": 0,  # 현재 웨이브에서 처치한 적 수
        "wave_target_kills": config.WAVE_SCALING[1]["target_kills"],  # 웨이브 클리어 목표
        "wave_start_time": 0.0,  # 웨이브 시작 시간
        "wave_clear_levelup": False,  # 웨이브 클리어 레벨업 플래그
        # 보스 순차 스폰 시스템 (Wave 5)
        "boss_sequential_spawn_count": 0,  # 현재 웨이브에서 스폰된 보스 수
        "boss_sequential_spawn_delay": 3.0,  # 보스 간 스폰 간격 (초)
        # 랜덤 이벤트 시스템
        "active_event": None,  # 현재 활성화된 이벤트 타입 (키)
        "event_start_time": 0.0,  # 이벤트 시작 시간
        "event_notification_timer": 0.0,  # 이벤트 알림 표시 시간
        "event_coin_spawn_timer": 0.0,  # Treasure Rain용 코인 스폰 타이머
        "event_meteor_spawn_timer": 0.0,  # Meteor Shower용 메테오 스폰 타이머
        "event_meteors": [],  # Meteor Shower 메테오 리스트
    }


def handle_level_up(game_data: Dict):
    """레벨업 확정 시 게임 데이터를 업데이트합니다."""
    game_data["player_level"] += 1
    game_data["uncollected_score"] = 0
    print(f"INFO: Player Level up to {game_data['player_level']}")


def get_next_level_threshold(current_level: int) -> int:
    """다음 레벨업에 필요한 킬 수를 계산합니다."""
    BASE = config.LEVEL_UP_KILL_BASE
    GROWTH = config.LEVEL_UP_KILL_GROWTH

    if current_level == 1:
        return BASE
    else:
        return int(BASE * (GROWTH ** (current_level - 1)))


def get_current_stage(wave: int) -> tuple:
    """
    현재 웨이브에 해당하는 스테이지 번호와 정보를 반환합니다.

    Args:
        wave: 현재 웨이브 번호

    Returns:
        (stage_number, stage_info) 튜플
        stage_number: 스테이지 번호 (1-5)
        stage_info: config.STAGE_INFO의 딕셔너리 또는 None
    """
    # Boss Rush 모드 (Wave 21)
    if wave >= 21 or config.BOSS_RUSH_MODE:
        return (5, config.STAGE_INFO[5])

    # 일반 웨이브 (1-20)
    for stage_num, stage_data in config.STAGE_INFO.items():
        if wave in stage_data["waves"]:
            return (stage_num, stage_data)

    # 범위를 벗어난 경우 기본값
    return (1, config.STAGE_INFO[1])


def check_stage_transition(old_wave: int, new_wave: int) -> bool:
    """
    웨이브 전환 시 스테이지가 바뀌었는지 체크합니다.

    Args:
        old_wave: 이전 웨이브 번호
        new_wave: 새 웨이브 번호

    Returns:
        bool: 스테이지가 바뀌었으면 True
    """
    old_stage, _ = get_current_stage(old_wave)
    new_stage, _ = get_current_stage(new_wave)
    return old_stage != new_stage
