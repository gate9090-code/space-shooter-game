# game_logic/events.py
"""
Random event system.
Handles random event triggering, updating, and effects.
"""

import pygame
import random
import config
from typing import Dict, List, Tuple
from entities.player import Player
from entities.enemies import Enemy
from entities.collectibles import CoinGem


def try_trigger_random_event(game_data: Dict, current_time: float):
    """웨이브 시작 시 랜덤 이벤트 발생 확률 체크"""
    current_wave = game_data["current_wave"]
    settings = config.RANDOM_EVENT_SETTINGS

    # 최소 웨이브 체크
    if current_wave < settings["min_wave"]:
        return

    # 보스 웨이브에서는 이벤트 발생 안함
    if current_wave in config.BOSS_WAVES:
        return

    # 확률 체크
    if random.random() < settings["chance_per_wave"]:
        # 랜덤 이벤트 선택
        event_type = random.choice(list(config.RANDOM_EVENTS.keys()))
        start_random_event(game_data, event_type, current_time)


def start_random_event(game_data: Dict, event_type: str, current_time: float):
    """랜덤 이벤트 시작"""
    if event_type not in config.RANDOM_EVENTS:
        return

    event_data = config.RANDOM_EVENTS[event_type]
    game_data["active_event"] = event_type
    game_data["event_start_time"] = current_time
    game_data["event_notification_timer"] = config.RANDOM_EVENT_SETTINGS["notification_duration"]

    # 이벤트별 타이머 초기화
    game_data["event_coin_spawn_timer"] = 0.0
    game_data["event_meteor_spawn_timer"] = 0.0
    game_data["event_meteors"] = []

    print(f"EVENT: {event_data['name']} started! {event_data['description']}")


def update_random_event(game_data: Dict, current_time: float, dt: float, player: Player, coins: List, enemies: List, screen_size: Tuple[int, int]):
    """랜덤 이벤트 업데이트 및 종료 체크"""
    active_event = game_data.get("active_event")
    if not active_event:
        return

    event_data = config.RANDOM_EVENTS[active_event]
    event_duration = event_data.get("duration", config.RANDOM_EVENT_SETTINGS["duration"])
    elapsed = current_time - game_data["event_start_time"]

    # 화면 크기 언팩
    SCREEN_WIDTH, SCREEN_HEIGHT = screen_size

    # 이벤트 알림 타이머 감소
    if game_data["event_notification_timer"] > 0:
        game_data["event_notification_timer"] -= dt

    # 이벤트 종료 체크
    if elapsed >= event_duration:
        end_random_event(game_data)
        return

    # 이벤트별 효과 처리
    effects = event_data.get("effects", {})

    # TREASURE_RAIN: 코인 스폰
    if active_event == "TREASURE_RAIN":
        game_data["event_coin_spawn_timer"] += dt
        spawn_rate = effects.get("coin_spawn_rate", 0.5)
        if game_data["event_coin_spawn_timer"] >= spawn_rate:
            game_data["event_coin_spawn_timer"] = 0.0
            # 랜덤 위치에 코인 스폰
            x = random.randint(100, SCREEN_WIDTH - 100)
            y = random.randint(100, SCREEN_HEIGHT - 100)
            coins.append(CoinGem(pygame.math.Vector2(x, y), SCREEN_HEIGHT))

    # HEALING_WINDS: HP 회복
    elif active_event == "HEALING_WINDS":
        hp_regen = effects.get("hp_regen_per_second", 2.0)
        player.heal(hp_regen * dt)

    # METEOR_SHOWER: 메테오 스폰 및 업데이트 (적 위치 기반 타겟팅)
    elif active_event == "METEOR_SHOWER":
        game_data["event_meteor_spawn_timer"] += dt
        spawn_rate = effects.get("meteor_spawn_rate", 1.5)
        if game_data["event_meteor_spawn_timer"] >= spawn_rate:
            game_data["event_meteor_spawn_timer"] = 0.0

            # 살아있는 적 중에서 랜덤하게 타겟 선택
            alive_enemies = [e for e in enemies if e.is_alive]
            if alive_enemies:
                target_enemy = random.choice(alive_enemies)
                # 적 위치 주변 랜덤 오프셋 (완전히 정확하지 않게)
                offset_x = random.randint(-50, 50)
                offset_y = random.randint(-30, 30)
                target_x = int(target_enemy.pos.x) + offset_x
                target_y = int(target_enemy.pos.y) + offset_y
            else:
                # 적이 없으면 랜덤 위치
                target_x = random.randint(100, SCREEN_WIDTH - 100)
                target_y = random.randint(100, SCREEN_HEIGHT - 100)

            meteor = {
                "target_x": target_x,
                "target_y": target_y,
                "timer": 0.0,
                "warning_duration": 1.2,  # 떨어지는 시간
                "active": False,
                "explosion_timer": 0.0,
                "explosion_duration": 0.5,  # 폭발 지속 시간
            }
            game_data["event_meteors"].append(meteor)

        # 메테오 업데이트
        meteors_to_remove = []
        for meteor in game_data["event_meteors"]:
            meteor["timer"] += dt

            if not meteor["active"] and meteor["timer"] >= meteor["warning_duration"]:
                # 메테오 충돌 - 폭발 시작
                meteor["active"] = True
                meteor["explosion_timer"] = 0.0
                damage = effects.get("meteor_damage", 150)
                radius = effects.get("meteor_radius", 100)

                # 범위 내 적에게 데미지
                meteor_pos = pygame.math.Vector2(meteor["target_x"], meteor["target_y"])
                for enemy in enemies:
                    if enemy.is_alive:
                        dist = (enemy.pos - meteor_pos).length()
                        if dist <= radius:
                            enemy.take_damage(damage)

            elif meteor["active"]:
                # 폭발 중 - 타이머 업데이트
                meteor["explosion_timer"] += dt
                if meteor["explosion_timer"] >= meteor["explosion_duration"]:
                    meteors_to_remove.append(meteor)

        # 종료된 메테오 제거
        for meteor in meteors_to_remove:
            game_data["event_meteors"].remove(meteor)


def end_random_event(game_data: Dict):
    """랜덤 이벤트 종료"""
    if game_data.get("active_event"):
        event_name = config.RANDOM_EVENTS[game_data["active_event"]]["name"]
        print(f"EVENT: {event_name} ended!")

    game_data["active_event"] = None
    game_data["event_start_time"] = 0.0
    game_data["event_notification_timer"] = 0.0
    game_data["event_meteors"] = []


def get_active_event_modifiers(game_data: Dict) -> Dict:
    """현재 활성화된 이벤트의 효과 배율을 반환"""
    active_event = game_data.get("active_event")
    if not active_event:
        return {}

    event_data = config.RANDOM_EVENTS.get(active_event, {})
    return event_data.get("effects", {})
