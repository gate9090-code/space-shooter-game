# utils.py

import pygame
import random
from typing import Dict, Tuple, List, Iterable
from pathlib import Path
import math
import config
# HitImpact 대신 AnimatedEffect로 수정하고, objects의 모든 클래스를 임포트하는 것이 안전합니다.
from objects import Player, Enemy, Bullet, CoinGem, HealItem, AnimatedEffect, Weapon, DamageNumber, DamageNumberManager, Boss

# =========================================================
# 0. 게임 데이터 관리 함수
# =========================================================


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


def start_wave(game_data: Dict, current_time: float, enemies: List = None):
    """웨이브를 시작합니다. 이전 웨이브의 적들을 제거합니다."""
    current_wave = game_data["current_wave"]

    # 이전 웨이브의 모든 적 제거 (특히 보스 웨이브에서 중요!)
    if enemies is not None:
        num_cleared = len(enemies)
        enemies.clear()
        if num_cleared > 0:
            print(f"INFO: Cleared {num_cleared} remaining enemies from previous wave")

    game_data["game_state"] = config.GAME_STATE_RUNNING
    game_data["wave_kills"] = 0

    # 웨이브 스케일링 데이터 가져오기 (범위 초과 시 마지막 웨이브 설정 사용)
    max_defined_wave = max(config.WAVE_SCALING.keys())
    wave_key = min(current_wave, max_defined_wave)
    game_data["wave_target_kills"] = config.WAVE_SCALING[wave_key]["target_kills"]

    game_data["wave_start_time"] = current_time
    game_data["wave_phase"] = "normal"  # 웨이브 페이즈 초기화

    # 보스 스폰 관련 초기화
    game_data["boss_sequential_spawn_count"] = 0  # Wave 5용 순차 스폰 카운터
    game_data[f"boss_spawned_wave_{current_wave}"] = False  # 현재 웨이브 보스 스폰 플래그 초기화

    # 랜덤 이벤트 발생 확률 체크
    try_trigger_random_event(game_data, current_time)

    print(f"INFO: Wave {current_wave} Started! Target: {game_data['wave_target_kills']} kills")


def check_wave_clear(game_data: Dict) -> bool:
    """웨이브 클리어 조건을 체크합니다."""
    if game_data["wave_kills"] >= game_data["wave_target_kills"]:
        return True
    return False


def advance_to_next_wave(game_data: Dict, player: Player = None, sound_manager = None):
    """다음 웨이브로 진행합니다. 웨이브 클리어 시 크레딧 보상을 지급합니다.

    [Option B] 레벨업 시스템 제거됨 - 모든 업그레이드는 기지 정비소에서 크레딧으로 구매
    """
    current_wave = game_data["current_wave"]

    # 크레딧 보상 지급 (Option B: 정비소 통합)
    credit_reward = config.WAVE_CLEAR_CREDITS.get(current_wave, 100)
    game_data["score"] = game_data.get("score", 0) + credit_reward
    game_data["last_wave_credits"] = credit_reward  # UI 표시용
    print(f"INFO: Wave {current_wave} cleared! +{credit_reward} credits (Total: {game_data['score']})")

    # Boss Rush 모드 체크
    if config.BOSS_RUSH_MODE:
        # 현재 웨이브를 완료 목록에 추가
        if current_wave not in config.BOSS_RUSH_COMPLETED_WAVES:
            config.BOSS_RUSH_COMPLETED_WAVES.append(current_wave)

        # 남은 보스 웨이브 찾기
        remaining_bosses = [wave for wave in config.BOSS_WAVES if wave not in config.BOSS_RUSH_COMPLETED_WAVES]

        if remaining_bosses:
            # 다음 보스로 진행
            game_data["current_wave"] = remaining_bosses[0]
            # [Option B] 크레딧만 지급, 레벨업 없이 바로 다음 웨이브 준비
            game_data["game_state"] = config.GAME_STATE_WAVE_PREPARE
            print(f"INFO: Boss Wave {current_wave} cleared! Next Boss: Wave {game_data['current_wave']}")
        else:
            # 모든 보스 클리어! 보스 러시 종료
            # 보너스 스테이지 코인 합산
            if 'boss_rush_saved_state' in game_data:
                original_coins = game_data['boss_rush_saved_state'].get('score', 0)
                current_coins = game_data['score']
                bonus_coins = current_coins - original_coins
                final_coins = original_coins + bonus_coins
                game_data['score'] = final_coins
                print(f"INFO: Boss Rush Coins - Original: {original_coins}, Bonus: {bonus_coins}, Total: {final_coins}")

            config.BOSS_RUSH_MODE = False
            config.BOSS_RUSH_COMPLETED_WAVES = []
            game_data["game_state"] = config.GAME_STATE_VICTORY
            if sound_manager:
                sound_manager.play_bgm("victory", loops=0, fade_ms=2000)
            print("INFO: BOSS RUSH COMPLETED! ALL BOSSES DEFEATED!")

    else:
        # Normal 모드: 일반 웨이브 진행
        # 스토리 모드는 25웨이브, 웨이브 모드는 20웨이브
        if config.GAME_MODE == "story":
            from mode_configs import config_story
            total_waves = config_story.TOTAL_WAVES  # 25
        else:
            total_waves = config.TOTAL_WAVES  # 20

        if current_wave in config.BOSS_WAVES:
            # 보스 웨이브 클리어 - 선택 화면 표시
            if current_wave >= total_waves:
                # 마지막 웨이브(20)도 보스이므로 선택 가능
                # 하지만 계속하기를 누르면 21웨이브로 가거나 완료 처리
                pass
            game_data["game_state"] = config.GAME_STATE_BOSS_CLEAR
            print(f"INFO: Boss Wave {current_wave} cleared! Choose to continue or return to base.")
        elif current_wave >= total_waves:
            # 게임 클리어!
            game_data["game_state"] = config.GAME_STATE_VICTORY
            # 승리 BGM 재생
            if sound_manager:
                sound_manager.play_bgm("victory", loops=0, fade_ms=2000)
            print("INFO: ALL WAVES CLEARED! VICTORY!")
        else:
            # 다음 웨이브로 증가
            game_data["current_wave"] += 1
            # [Option B] 크레딧만 지급, 레벨업 없이 바로 다음 웨이브 준비
            game_data["game_state"] = config.GAME_STATE_WAVE_PREPARE
            print(f"INFO: Preparing Wave {game_data['current_wave']}...")


# =========================================================
# 🎬 스테이지 시스템
# =========================================================

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


# =========================================================
# 랜덤 이벤트 시스템
# =========================================================

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


def get_wave_scaling(wave: int) -> Dict:
    """웨이브의 난이도 스케일링 정보를 반환합니다."""
    if wave in config.WAVE_SCALING:
        return config.WAVE_SCALING[wave]
    # 범위를 벗어난 경우 마지막 정의된 웨이브 설정 사용
    max_defined_wave = max(config.WAVE_SCALING.keys())
    return config.WAVE_SCALING[max_defined_wave]


def select_enemy_type(wave: int) -> str:
    """
    현재 웨이브에 따라 적 타입을 확률 기반으로 선택합니다.

    Args:
        wave: 현재 웨이브 번호

    Returns:
        선택된 적 타입 이름 (ENEMY_TYPES 키)
    """
    distribution = config.WAVE_ENEMY_TYPE_DISTRIBUTION.get(wave, {"NORMAL": 1.0})

    # 가중치 기반 랜덤 선택
    enemy_types = list(distribution.keys())
    weights = list(distribution.values())

    return random.choices(enemy_types, weights=weights, k=1)[0]


# =========================================================
# 1. 스폰 관련 함수
# =========================================================


def spawn_enemy(enemies: List[Enemy], screen_size: Tuple[int, int], game_data: Dict):
    """화면 바깥쪽 임의의 위치에 적을 스폰합니다. (웨이브 스케일링 적용)"""
    SCREEN_WIDTH, SCREEN_HEIGHT = screen_size
    padding = 50

    # 웨이브 스케일링 가져오기
    current_wave = game_data.get("current_wave", 1)
    scaling = get_wave_scaling(current_wave)

    # 보스 웨이브인지 확인
    is_boss_wave = current_wave in config.BOSS_WAVES

    if is_boss_wave:
        # Wave 5: 보스들을 랜덤 위치에서 스폰 (순차 스폰은 handle_spawning에서 관리)
        if current_wave == 5:
            # 이미 목표 보스 수만큼 스폰되었는지 체크
            target_boss_count = scaling.get("target_kills", 3)
            boss_spawn_count = game_data.get("boss_sequential_spawn_count", 0)
            if boss_spawn_count >= target_boss_count:
                return None  # 이미 목표 보스 수 도달

            # 화면 상단의 랜덤 위치에서 스폰
            x = random.randint(100, SCREEN_WIDTH - 100)
            y = -padding * 2
            boss_name = "The Swarm Queen"
        # 기타 보스 웨이브 (10, 15, 20): 화면 중앙 상단에서 스폰
        else:
            # 이미 보스가 스폰되었는지 체크 (handle_spawning에서 플래그 설정됨)
            boss_already_spawned = game_data.get(f"boss_spawned_wave_{current_wave}", False)
            if not boss_already_spawned:
                return None  # 플래그가 설정되지 않았으면 스폰 안함 (handle_spawning 통해서만 스폰)

            x = SCREEN_WIDTH // 2
            y = -padding * 2

            if current_wave == 10:
                boss_name = "The Void Core"
            elif current_wave == 15:
                boss_name = "The Dark Commander"
            elif current_wave == 20:
                boss_name = "The Final Overlord"
            else:
                boss_name = f"Boss Wave {current_wave}"

        # 보스 생성 (wave_number 전달)
        new_enemy = Boss(pygame.math.Vector2(x, y), SCREEN_HEIGHT, boss_name, current_wave)
    else:
        # 스토리 모드: 적이 화면 상단에서만 스폰
        game_mode = config.GAME_MODE
        if game_mode == "story":
            # 스토리 모드: 화면 상단에서만 스폰
            x = random.randint(50, SCREEN_WIDTH - 50)
            y = -padding
        else:
            # 일반 적 스폰 위치 (화면 밖 랜덤)
            side = random.choice(["top", "bottom", "left", "right"])

            if side == "top":
                x = random.randint(0, SCREEN_WIDTH)
                y = -padding
            elif side == "bottom":
                x = random.randint(0, SCREEN_WIDTH)
                y = SCREEN_HEIGHT + padding
            elif side == "left":
                x = -padding
                y = random.randint(0, SCREEN_HEIGHT)
            else:  # right
                x = SCREEN_WIDTH + padding
                y = random.randint(0, SCREEN_HEIGHT)

        # 일반 적 생성 (추적 확률 및 타입 포함)
        chase_prob = scaling.get("chase_prob", 1.0)
        enemy_type = select_enemy_type(current_wave)
        new_enemy = Enemy(pygame.math.Vector2(x, y), SCREEN_HEIGHT, chase_prob, enemy_type)

    # 웨이브 스케일링 적용
    new_enemy.hp *= scaling["hp_mult"]
    new_enemy.max_hp = new_enemy.hp
    new_enemy.speed *= scaling["speed_mult"]
    new_enemy.damage *= scaling.get("damage_mult", 1.0)  # 공격력 배율 적용

    enemies.append(new_enemy)
    return new_enemy  # 생성된 적 반환


def handle_spawning(
    enemies: List[Enemy], screen_size: Tuple[int, int], current_time: float, game_data: Dict, effects: List = None, sound_manager = None
):
    """
    적 스폰 로직을 관리합니다. (웨이브별 스폰 속도 조정 + 최대 적 수 제한)
    """
    # 게임이 실행 중일 때만 스폰
    if game_data["game_state"] != config.GAME_STATE_RUNNING:
        return

    # 웨이브별 최대 적 수 체크
    current_wave = game_data.get("current_wave", 1)
    max_enemies = config.MAX_ENEMIES_ON_SCREEN.get(current_wave, 20)

    # 현재 살아있는 적의 수 확인
    alive_enemies = sum(1 for enemy in enemies if enemy.is_alive)

    if alive_enemies >= max_enemies:
        # 최대 적 수에 도달했으면 스폰 중지
        return

    # 웨이브 스케일링 가져오기
    scaling = get_wave_scaling(current_wave)

    # ========== cleanup 페이즈 체크 (모든 웨이브 공통) ==========
    wave_phase = game_data.get("wave_phase", "normal")
    if wave_phase != "normal":
        # cleanup 또는 victory_animation 페이즈면 스폰 중지
        return

    # ========== 보스 웨이브 스폰 로직 ==========
    is_boss_wave = current_wave in config.BOSS_WAVES

    if current_wave == 5:

        # Wave 5는 3마리의 보스를 순차적으로 스폰
        target_boss_count = scaling["target_kills"]  # 3
        boss_spawn_count = game_data.get("boss_sequential_spawn_count", 0)

        # 모든 보스를 이미 스폰했으면 종료
        if boss_spawn_count >= target_boss_count:
            return

        # 순차 스폰 딜레이 계산
        boss_spawn_delay = game_data.get("boss_sequential_spawn_delay", 3.0)
        wave_start_time = game_data.get("wave_start_time", current_time)

        # 다음 보스 스폰 시간 = 웨이브 시작 시간 + (보스 번호 * 딜레이)
        next_boss_spawn_time = wave_start_time + (boss_spawn_count * boss_spawn_delay)

        # 아직 스폰 시간이 되지 않았으면 대기
        if current_time < next_boss_spawn_time:
            return

        # 스폰 카운터 증가 (spawn_enemy 호출 전에 증가시켜 중복 스폰 방지)
        game_data["boss_sequential_spawn_count"] = boss_spawn_count + 1

        # 보스 스폰
        new_enemy = spawn_enemy(enemies, screen_size, game_data)

        # 스폰 포털 효과 추가
        if new_enemy and effects is not None:
            create_spawn_effect((new_enemy.pos.x, new_enemy.pos.y), effects)

            # 보스 스폰 시 특별 효과
            if hasattr(new_enemy, 'is_boss') and new_enemy.is_boss:
                SCREEN_WIDTH, SCREEN_HEIGHT = screen_size
                # 보스 스폰 사운드
                if sound_manager:
                    sound_manager.play_sfx("boss_spawn")
                # 충격파
                create_shockwave((new_enemy.pos.x, new_enemy.pos.y), "BOSS_SPAWN", effects)
                # 보스 이름 텍스트
                boss_name = getattr(new_enemy, 'boss_name', 'BOSS')
                create_dynamic_text(f"{boss_name} #{boss_spawn_count + 1} HAS APPEARED!", (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3), "BOSS_SPAWN", effects)

        return

    # ========== Wave 10, 15, 20 단일 보스 스폰 로직 ==========
    if is_boss_wave and current_wave != 5:
        # 이미 보스가 스폰되었는지 체크
        boss_already_spawned = game_data.get(f"boss_spawned_wave_{current_wave}", False)
        if boss_already_spawned:
            # 보스 웨이브에서 보스가 이미 스폰됨 - 추가 스폰 없음
            return

        # 보스 스폰 플래그 설정 (spawn_enemy 호출 전에 설정하여 중복 스폰 방지)
        game_data[f"boss_spawned_wave_{current_wave}"] = True

        # 보스 스폰
        new_enemy = spawn_enemy(enemies, screen_size, game_data)

        # 스폰 포털 효과 추가
        if new_enemy and effects is not None:
            create_spawn_effect((new_enemy.pos.x, new_enemy.pos.y), effects)

            # 보스 스폰 시 특별 효과
            if hasattr(new_enemy, 'is_boss') and new_enemy.is_boss:
                SCREEN_WIDTH, SCREEN_HEIGHT = screen_size
                # 보스 스폰 사운드
                if sound_manager:
                    sound_manager.play_sfx("boss_spawn")
                # 충격파
                create_shockwave((new_enemy.pos.x, new_enemy.pos.y), "BOSS_SPAWN", effects)
                # 보스 이름 텍스트
                boss_name = getattr(new_enemy, 'boss_name', 'BOSS')
                create_dynamic_text(f"{boss_name} HAS APPEARED!", (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3), "BOSS_SPAWN", effects)

        return

    # ========== 일반 웨이브 스폰 로직 ==========
    # 웨이브별 스폰 간격 조정
    BASE_SPAWN_INTERVAL = getattr(config, "ENEMY_SPAWN_INTERVAL", 1.0)
    spawn_interval = BASE_SPAWN_INTERVAL / scaling["spawn_rate"]  # spawn_rate가 높을수록 빠르게 스폰

    # game_data에서 스폰 시간 로드
    last_spawn_time = game_data.get("last_enemy_spawn_time", 0.0)

    if current_time - last_spawn_time >= spawn_interval:
        # 웨이브 스케일링이 적용된 적 스폰
        new_enemy = spawn_enemy(enemies, screen_size, game_data)

        # 스폰 포털 효과 추가
        if new_enemy and effects is not None:
            create_spawn_effect((new_enemy.pos.x, new_enemy.pos.y), effects)

            # 보스 스폰 시 특별 효과
            if hasattr(new_enemy, 'is_boss') and new_enemy.is_boss:
                SCREEN_WIDTH, SCREEN_HEIGHT = screen_size
                # 보스 스폰 사운드
                if sound_manager:
                    sound_manager.play_sfx("boss_spawn")
                # 충격파
                create_shockwave((new_enemy.pos.x, new_enemy.pos.y), "BOSS_SPAWN", effects)
                # 보스 이름 텍스트
                boss_name = getattr(new_enemy, 'boss_name', 'BOSS')
                create_dynamic_text(f"{boss_name} HAS APPEARED!", (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3), "BOSS_SPAWN", effects)

        # game_data에 스폰 시간 저장
        game_data["last_enemy_spawn_time"] = current_time 


def spawn_gem(
    gems: List[CoinGem | HealItem], screen_size: Tuple[int, int], current_time: float, game_data: Dict
):
    """
    일정 확률로 힐링 젬을 스폰합니다.
    """
    # global LAST_GEM_SPAWN_TIME # 제거
    
    HEAL_GEM_SPAWN_INTERVAL = 10.0  # 10초마다 힐링 젬 스폰 기회
    HEAL_GEM_SPAWN_CHANCE = 0.5  # 50% 확률

    # game_data에서 스폰 시간 로드
    last_gem_spawn_time = game_data.get("last_gem_spawn_time", 0.0) 

    if current_time - last_gem_spawn_time >= HEAL_GEM_SPAWN_INTERVAL:
        if random.random() < HEAL_GEM_SPAWN_CHANCE:
            SCREEN_WIDTH, SCREEN_HEIGHT = screen_size
            x = random.randint(50, SCREEN_WIDTH - 50)
            y = random.randint(50, SCREEN_HEIGHT - 50)

            new_heal_gem = HealItem((x, y), SCREEN_HEIGHT)
            gems.append(new_heal_gem)
        # game_data에 스폰 시간 저장
        game_data["last_gem_spawn_time"] = current_time 


# =========================================================
# 2. 업데이트 및 충돌 처리 함수
# =========================================================


def get_next_level_threshold(current_level: int) -> int:
    """다음 레벨업에 필요한 킬 수를 계산합니다."""
    BASE = config.LEVEL_UP_KILL_BASE
    GROWTH = config.LEVEL_UP_KILL_GROWTH
    
    if current_level == 1:
        return BASE
    else:
        return int(BASE * (GROWTH ** (current_level - 1)))


def update_game_objects(
    player: Player,
    enemies: List[Enemy],
    bullets: List[Bullet],
    gems: List[CoinGem | HealItem],
    effects: List,
    screen_size: Tuple[int, int],
    dt: float,
    current_time: float,
    game_data: Dict,
    damage_numbers: List[DamageNumber] = None,
    damage_number_manager: DamageNumberManager = None,
    screen_shake = None,
    sound_manager = None,
    death_effect_manager = None,
):
    """
    모든 게임 객체를 업데이트하고 충돌을 처리합니다.

    Args:
        damage_numbers: (deprecated) 기존 데미지 숫자 리스트
        damage_number_manager: (권장) 데미지 누적 매니저
    """
    SCREEN_WIDTH, SCREEN_HEIGHT = screen_size

    # 1. 객체 업데이트
    # Player.update()에 current_time 전달 (체력 재생을 위해)
    player.update(dt, screen_size, current_time)

    # 2. 적 업데이트 (플레이어 위치 추적, 분리 행동 적용)
    # Time Freeze 효과 적용
    effective_dt = 0.0 if player.time_freeze_active else dt

    for enemy in enemies:
        enemy.update(player.pos, effective_dt, enemies, screen_size, current_time)

    # 3. 총알 업데이트
    for bullet in bullets:
        bullet.update(dt, screen_size)

    # 4. 이펙트 업데이트는 main.py의 update_visual_effects()에서 처리됨

    # 4.5. 데미지 넘버 업데이트
    if damage_number_manager is not None:
        damage_number_manager.update(dt)
    elif damage_numbers is not None:
        for dmg_num in damage_numbers:
            dmg_num.update(dt, current_time)

    # 5. 충돌 처리

    # 5.1 총알 vs 적 충돌
    for bullet in bullets:
        if not bullet.is_alive:
            continue

        hit_enemy = None
        for enemy in enemies:
            if not enemy.is_alive:
                continue

            if bullet.hitbox.colliderect(enemy.hitbox):
                was_alive = enemy.is_alive
                is_boss = hasattr(enemy, 'is_boss') and enemy.is_boss

                enemy.take_damage(bullet.damage, player)  # Execute 스킬용

                # 적 피격 사운드
                if sound_manager:
                    sound_manager.play_sfx("enemy_hit")

                # 속성 스킬: Frost Bullets (슬로우)
                if player.has_frost and not is_boss:
                    enemy.is_slowed = True
                    enemy.slow_ratio = player.frost_slow_ratio
                    enemy.slow_timer = config.ATTRIBUTE_SKILL_SETTINGS["FROST"]["duration"]
                    enemy.speed = enemy.base_speed * (1 - enemy.slow_ratio)

                # 속성 스킬: Deep Freeze (완전 동결)
                if player.has_deep_freeze and not is_boss:
                    if random.random() < player.freeze_chance:
                        enemy.is_frozen = True
                        enemy.freeze_timer = config.ATTRIBUTE_SKILL_SETTINGS["DEEP_FREEZE"]["duration"]

                # 속성 스킬: Chain Lightning (번개 체인)
                if player.has_lightning:
                    from objects import LightningEffect
                    chain_range = config.ATTRIBUTE_SKILL_SETTINGS["LIGHTNING"]["chain_range"]
                    chain_damage = bullet.damage * config.ATTRIBUTE_SKILL_SETTINGS["LIGHTNING"]["damage_ratio"]
                    chain_count = player.lightning_chain_count

                    # 현재 적에서 시작하여 가장 가까운 적들에게 체인
                    chained_enemies = [enemy]
                    current_pos = enemy.pos

                    for _ in range(chain_count):
                        # 가장 가까운 적 찾기
                        closest_enemy = None
                        closest_distance = float('inf')

                        for other_enemy in enemies:
                            if other_enemy.is_alive and other_enemy not in chained_enemies:
                                distance = (other_enemy.pos - current_pos).length()
                                if distance <= chain_range and distance < closest_distance:
                                    closest_enemy = other_enemy
                                    closest_distance = distance

                        if closest_enemy:
                            # 번개 시각 효과 추가
                            try:
                                effects.append(LightningEffect(current_pos, closest_enemy.pos))
                            except:
                                pass  # LightningEffect가 없으면 무시

                            chained_enemies.append(closest_enemy)
                            closest_enemy.take_damage(chain_damage)
                            create_hit_particles((closest_enemy.pos.x, closest_enemy.pos.y), effects)
                            current_pos = closest_enemy.pos
                        else:
                            break

                # 데미지 넘버 생성 (매니저 사용 시 누적, 아니면 개별 표시)
                if damage_number_manager is not None:
                    # 적 id 사용하여 데미지 누적
                    damage_number_manager.add_damage(
                        bullet.damage,
                        (enemy.pos.x, enemy.pos.y - 20),  # 적 머리 위에 표시
                        target_id=id(enemy)
                    )
                elif damage_numbers is not None:
                    damage_num = DamageNumber(bullet.damage, (enemy.pos.x, enemy.pos.y))
                    damage_numbers.append(damage_num)

                # 적이 방금 사망한 경우
                if was_alive and not enemy.is_alive:
                    # 적 사망 시 누적 데미지 즉시 표시
                    if damage_number_manager is not None:
                        damage_number_manager.flush_target(id(enemy))

                    # 적 사망 사운드
                    if sound_manager:
                        if is_boss:
                            sound_manager.play_sfx("explosion", volume_override=1.0)
                        else:
                            sound_manager.play_sfx("enemy_death")

                    # 사망 효과 (Shatter Effect 등)
                    if death_effect_manager:
                        death_effect_manager.trigger_death_effect(enemy)

                    # 폭발 파티클 생성
                    create_explosion_particles((enemy.pos.x, enemy.pos.y), effects)

                    # 속성 스킬: Explosive Bullets (적 사망 시 폭발)
                    if player.has_explosive:
                        from objects import Shockwave
                        explosion_radius = config.ATTRIBUTE_SKILL_SETTINGS["EXPLOSIVE"]["radius"]
                        explosion_damage = bullet.damage * config.ATTRIBUTE_SKILL_SETTINGS["EXPLOSIVE"]["damage_ratio"]

                        # 폭발 시각 효과 추가
                        effects.append(Shockwave(
                            center=(enemy.pos.x, enemy.pos.y),
                            max_radius=explosion_radius,
                            duration=0.4,
                            color=(255, 150, 50),  # 주황색
                            width=4
                        ))

                        # 폭발 범위 내 적들에게 데미지
                        for other_enemy in enemies:
                            if other_enemy != enemy and other_enemy.is_alive:
                                distance = (other_enemy.pos - enemy.pos).length()
                                if distance <= explosion_radius:
                                    other_enemy.take_damage(explosion_damage)
                                    create_hit_particles((other_enemy.pos.x, other_enemy.pos.y), effects)

                                    # 속성 스킬: Chain Reaction (연쇄 폭발)
                                    # 폭발로 죽은 적도 폭발 (재귀적 효과는 깊이 제한으로 방지)
                                    if player.has_chain_explosion and not other_enemy.is_alive:
                                        # 간단한 연쇄: 폭발 파티클만 추가 (무한 루프 방지)
                                        create_explosion_particles((other_enemy.pos.x, other_enemy.pos.y), effects)

                    # 속성 스킬: Static Field (정전기장 생성)
                    if player.has_static_field:
                        from objects import StaticField
                        static_field = StaticField(
                            pos=(enemy.pos.x, enemy.pos.y),
                            radius=config.ATTRIBUTE_SKILL_SETTINGS["STATIC_FIELD"]["radius"],
                            duration=config.ATTRIBUTE_SKILL_SETTINGS["STATIC_FIELD"]["duration"],
                            damage_per_sec=config.ATTRIBUTE_SKILL_SETTINGS["STATIC_FIELD"]["damage_per_sec"]
                        )
                        effects.append(static_field)

                    # 보스 처치 시 특별 효과
                    if is_boss:
                        # 충격파
                        create_shockwave((enemy.pos.x, enemy.pos.y), "BOSS_DEATH", effects)
                        # 화면 떨림
                        if screen_shake:
                            trigger_screen_shake("BOSS_DEATH", screen_shake)
                        # 타임 슬로우
                        create_time_slow_effect(effects)
                        # 보스 이름 텍스트
                        boss_name = getattr(enemy, 'boss_name', 'BOSS')
                        create_dynamic_text(f"{boss_name} DEFEATED!", (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2), "BOSS_SPAWN", effects)
                    else:
                        # 일반 적 사망 시 작은 화면 떨림
                        if screen_shake:
                            trigger_screen_shake("ENEMY_DEATH", screen_shake)

                    # 힐링 젬 스폰 로직 (적 사망 시 10% 확률)
                    if random.random() < 0.1:
                        new_heal_gem = HealItem((enemy.pos.x, enemy.pos.y), SCREEN_HEIGHT)
                        gems.append(new_heal_gem)
                else:
                    # 피격 파티클 (보스 또는 일반 적)
                    if is_boss:
                        create_boss_hit_particles((enemy.pos.x, enemy.pos.y), effects)
                        if screen_shake:
                            trigger_screen_shake("BOSS_HIT", screen_shake)
                    else:
                        create_hit_particles((enemy.pos.x, enemy.pos.y), effects)

                # 피어싱(관통) 여부 확인
                if not player.is_piercing:
                    bullet.is_alive = False  # 관통이 아니면 총알 제거

                hit_enemy = enemy
                break  # 한 적에게 맞으면 다음 총알로 넘어갑니다. (관통이 아닌 경우)

        # 충돌 이펙트 생성
        if hit_enemy:
            impact = AnimatedEffect((bullet.pos.x, bullet.pos.y), SCREEN_HEIGHT, config.IMPACT_FX_IMAGE_PATH, "HITIMPACT")
            effects.append(impact)

            # 총알 충격파 효과 생성 (적의 내부에서 시작하여 밖으로 확장, 다중 파동)
            # 총알이 날아가는 방향으로 오프셋하여 적의 안쪽 깊숙이 배치
            if hasattr(bullet, 'direction') and bullet.direction.length_squared() > 0:
                # 총알이 날아가는 방향으로 오프셋 → 적의 내부로 들어감
                offset_distance = 20  # 픽셀 (15 → 20, 더 깊숙이)
                impact_pos = pygame.math.Vector2(bullet.pos.x, bullet.pos.y) + bullet.direction * offset_distance
            else:
                impact_pos = pygame.math.Vector2(bullet.pos.x, bullet.pos.y)

            # 다중 파동 효과 생성
            settings = config.SHOCKWAVE_SETTINGS["BULLET_HIT"]
            wave_count = settings.get("wave_count", 3)
            wave_interval = settings.get("wave_interval", 0.08)

            for i in range(wave_count):
                # 각 파동마다 약간의 지연을 가진 충격파 생성
                from objects import Shockwave
                shockwave = Shockwave(
                    center=(impact_pos.x, impact_pos.y),
                    max_radius=settings["max_radius"],
                    duration=settings["duration"],
                    color=settings["color"],
                    width=settings["width"],
                    delay=i * wave_interval  # 지연 시간 추가
                )
                effects.append(shockwave)

    # 5.2 적 vs 플레이어 충돌
    # 먼저 모든 적의 화상 상태를 초기화
    for enemy in enemies:
        if enemy.is_alive:
            enemy.is_burning = False

    # 충돌 확인 및 화상 상태 설정
    for enemy in enemies:
        if not enemy.is_alive:
            continue
        if player.hitbox.colliderect(enemy.hitbox):
            # 플레이어와 접촉 중 - 화상 이미지 활성화
            enemy.is_burning = True
            # KAMIKAZE 타입: 자폭 처리
            if hasattr(enemy, 'explode_on_contact') and enemy.explode_on_contact and not enemy.has_exploded:
                explosion_damage = getattr(enemy, 'explosion_damage', 20.0)
                player.take_damage(explosion_damage)
                enemy.is_alive = False  # 적 즉시 사망
                enemy.has_exploded = True

                # 플레이어 피격 사운드 및 화면 떨림
                if sound_manager:
                    sound_manager.play_sfx("player_hit")
                    sound_manager.play_sfx("explosion")  # 폭발 사운드

                if screen_shake:
                    trigger_screen_shake("ENEMY_DEATH", screen_shake)  # 강한 진동

                # 폭발 이펙트 생성 (옵션)
                if effects is not None:
                    explosion_effect = AnimatedEffect(
                        (enemy.pos.x, enemy.pos.y),
                        SCREEN_HEIGHT,
                        config.EXPLOSION_IMAGE_PATH,
                        "EXPLOSION",
                        frame_duration=0.05,
                        total_frames=1
                    )
                    effects.append(explosion_effect)

                continue  # 다음 적으로 이동

            # 일반 공격 (Enemy.attack 메서드 사용, 쿨타임 체크 포함)
            if enemy.attack(player, current_time):
                # 플레이어 피격 사운드
                if sound_manager:
                    sound_manager.play_sfx("player_hit")

                # 플레이어 피격 시 화면 떨림
                if screen_shake:
                    trigger_screen_shake("PLAYER_HIT", screen_shake)

    # 5.2.5 보스 Burn 발사체 vs 플레이어 충돌
    for enemy in enemies:
        if hasattr(enemy, 'is_boss') and enemy.is_boss and enemy.is_alive:
            if hasattr(enemy, 'check_burn_collision_with_player'):
                burn_damage = enemy.check_burn_collision_with_player(player)
                if burn_damage > 0:
                    player.take_damage(burn_damage)
                    # 플레이어 피격 사운드
                    if sound_manager:
                        sound_manager.play_sfx("player_hit")
                    # 플레이어 피격 시 화면 떨림
                    if screen_shake:
                        trigger_screen_shake("PLAYER_HIT", screen_shake)

    # 5.3 젬 vs 플레이어 충돌
    for gem in gems:
        # 젬 자석 효과를 위해 update를 호출합니다.
        gem.update(dt, player)

        if player.hitbox.colliderect(gem.hitbox):
            if isinstance(gem, CoinGem):
                # CoinGem.collect(game_data)는 uncollected_score를 증가시킵니다.
                if gem.collect(game_data):
                    # 코인 획득 사운드
                    if sound_manager:
                        sound_manager.play_sfx("coin_pickup")
            elif isinstance(gem, HealItem):
                # HealItem.collect(player)는 player의 HP를 회복시킵니다.
                if gem.collect(player):
                    # 힐 아이템 획득 사운드
                    if sound_manager:
                        sound_manager.play_sfx("heal_pickup") 


    # 6. 객체 정리
    # 킬 카운트 업데이트 및 코인 드롭 (도망 성공한 적 제외)
    # 중복 카운트 방지: _kill_counted 플래그 사용
    for enemy in enemies:
        if not enemy.is_alive:
            # 화면 밖으로 도망 성공한 적만 제외
            # (퇴각 중이라도 공격으로 사망하면 escaped=False이므로 카운트됨)
            if getattr(enemy, 'escaped', False):
                continue  # 도망 성공한 적은 무시

            # 이미 카운트된 적은 스킵
            if getattr(enemy, '_kill_counted', False):
                continue

            enemy._kill_counted = True  # 카운트 완료 표시
            game_data["kill_count"] += 1
            game_data["wave_kills"] += 1  # 웨이브 킬 카운트
            game_data["kills_this_wave"] = game_data.get("kills_this_wave", 0) + 1  # 스토리 모드용

            # 코인 젬 드롭 (코인 배율 적용)
            base_coins = config.BASE_COIN_DROP_PER_KILL
            coin_mult = getattr(enemy, 'coin_multiplier', 1.0)
            actual_coins = int(base_coins * coin_mult)

            for _ in range(actual_coins):
                coin_gem = CoinGem((enemy.pos.x, enemy.pos.y), SCREEN_HEIGHT)
                gems.append(coin_gem)

            # SUMMONER 타입: 사망 시 작은 적 소환
            if hasattr(enemy, 'summon_on_death') and enemy.summon_on_death:
                summon_count = getattr(enemy, 'summon_count', 0)
                current_wave = game_data.get("current_wave", 1)
                scaling = get_wave_scaling(current_wave)

                for i in range(summon_count):
                    # 소환된 적은 NORMAL 타입의 0.3배 HP로 생성
                    offset_x = random.uniform(-50, 50)
                    offset_y = random.uniform(-50, 50)
                    spawn_pos = pygame.math.Vector2(enemy.pos.x + offset_x, enemy.pos.y + offset_y)

                    summoned_enemy = Enemy(spawn_pos, SCREEN_HEIGHT, 1.0, "NORMAL")
                    summoned_enemy.hp = summoned_enemy.max_hp * 0.3  # 30% HP
                    summoned_enemy.max_hp = summoned_enemy.hp
                    summoned_enemy.speed *= scaling["speed_mult"]
                    summoned_enemy.damage *= scaling.get("damage_mult", 1.0)

                    enemies.append(summoned_enemy)

    # 궁극기: Orbital Strike 데미지 처리
    for strike in player.orbital_strikes:
        if strike["active"]:
            settings = config.ULTIMATE_SETTINGS["ORBITAL_STRIKE"]
            for enemy in enemies:
                if enemy.is_alive:
                    dist = (enemy.pos - strike["pos"]).length()
                    if dist <= settings["strike_radius"]:
                        enemy.take_damage(settings["damage_per_strike"])
                        # 레이저 피격 효과 추가 (선택 사항)

    # 웨이브 클리어 체크 - wave_phase가 'normal'일 때만 여기서 처리
    # cleanup 페이즈는 wave_mode.py에서 별도로 처리함
    wave_phase = game_data.get('wave_phase', 'normal')
    if wave_phase == 'normal' and game_data["game_state"] == config.GAME_STATE_RUNNING and check_wave_clear(game_data):
        # cleanup 페이즈로 전환 (wave_mode에서 처리)
        # 여기서는 클리어 처리하지 않음 - wave_mode._trigger_wave_transition()에서 처리
        pass

    # 죽은 객체/수집된 객체 제거
    enemies[:] = [e for e in enemies if e.is_alive]
    bullets[:] = [b for b in bullets if b.is_alive]
    # CoinGem과 HealItem 모두 객체 내부에 collected 상태를 가질 것으로 가정하고 이 로직을 유지
    gems[:] = [
        g
        for g in gems
        if not (hasattr(g, 'collected') and g.collected)
    ]
    # effects는 update_visual_effects()에서 정리됨

    # 데미지 넘버 정리
    if damage_numbers is not None:
        damage_numbers[:] = [d for d in damage_numbers if not d.is_finished]


# =========================================================
# 3. 그리기 관련 함수
# =========================================================


def draw_objects(
    screen: pygame.Surface,
    player_list: List[Player], # main.py에서 리스트로 전달하므로 player_list로 받습니다.
    enemies: List[Enemy],
    bullets: List[Bullet],
    gems: List[CoinGem | HealItem],
    effects: List[AnimatedEffect],
):
    """모든 게임 객체를 그립니다."""

    player = player_list[0] # 리스트에서 플레이어 객체 추출

    # 1. 젬 그리기 (가장 아래)
    for gem in gems:
        # collected 상태를 객체 내부에서 관리한다고 가정하고, 이 로직을 유지
        if not (hasattr(gem, 'collected') and gem.collected):
            gem.draw(screen)

    # 2. 적 그리기
    for enemy in enemies:
        enemy.draw(screen)
        # 보스 Burn 발사체 그리기
        if hasattr(enemy, 'is_boss') and enemy.is_boss:
            if hasattr(enemy, 'draw_burn_projectiles'):
                enemy.draw_burn_projectiles(screen)

    # 3. 플레이어 그리기
    player.draw(screen)

    # 4. 총알 그리기
    for bullet in bullets:
        bullet.draw(screen)

    # 5. AnimatedEffect 그리기 (가장 위) - 나머지 효과는 draw_visual_effects에서 처리
    from objects import AnimatedEffect
    for effect in effects:
        if isinstance(effect, AnimatedEffect):
            effect.draw(screen)


# =========================================================
# 4. 전술 업그레이드 함수
# =========================================================


def generate_tactical_options(player: Player, game_data: Dict) -> List[Dict]:
    """플레이어에게 제공할 4개의 전술 업그레이드 옵션을 무작위로 생성합니다. (웨이브별 스킬 풀 적용)"""

    # 1. 현재 웨이브에 맞는 스킬 풀 가져오기
    current_wave = game_data.get("current_wave", 1)
    skill_pool_key = config.get_skill_pool_for_wave(current_wave)
    allowed_skill_ids = config.WAVE_SKILL_POOLS[skill_pool_key]

    # 2. 전체 옵션 중 현재 웨이브에서 허용된 스킬만 필터링
    all_options = config.TACTICAL_UPGRADE_OPTIONS
    wave_filtered_options = [opt for opt in all_options if opt["id"] in allowed_skill_ids]

    # 3. 이미 활성화된 토글 옵션 & 선행 조건 미충족 스킬 제외
    available_options = []
    for option in wave_filtered_options:
        # 토글 스킬 중복 체크
        is_toggle = option.get("type") == "toggle"
        is_active = False

        if is_toggle:
            if option["action"] == "toggle_piercing" and player.is_piercing:
                is_active = True
            elif option["action"] == "toggle_coin_magnet" and player.has_coin_magnet:
                is_active = True

        if is_active:
            continue

        # 선행 조건 체크 (requires 필드)
        requires = option.get("requires")
        if requires:
            # requires가 있는 스킬은 해당 속성을 플레이어가 가지고 있어야 함
            if requires == "explosive" and not player.has_explosive:
                continue
            elif requires == "lightning" and not player.has_lightning:
                continue
            elif requires == "frost" and not player.has_frost:
                continue

        available_options.append(option)

    # 4. 최대 4개의 옵션을 무작위로 선택
    num_options = min(4, len(available_options))

    if num_options > 0:
        selected_options = random.sample(available_options, num_options)
    else:
        # 사용 가능한 옵션이 없으면 빈 리스트
        selected_options = []

    # 선택된 옵션을 무작위로 섞습니다.
    random.shuffle(selected_options)
    
    # 4. 선택된 옵션에 1부터 순차적인 인덱스를 부여
    final_options = []
    for i, option in enumerate(selected_options):
        # UI에서 키를 인덱스(1-based)로 사용하도록 수정
        final_options.append({"key_index": i + 1, **option})
        
    return final_options


def check_and_activate_synergies(player: Player):
    """플레이어의 스킬 조합을 확인하여 시너지를 활성화합니다."""

    for synergy in config.SYNERGIES:
        # 이미 활성화된 시너지는 스킵
        if synergy["effect"] in player.active_synergies:
            continue

        # 필요한 스킬들을 모두 획득했는지 확인
        required_actions = synergy["requires"]
        has_all_requirements = all(
            action in player.acquired_skills for action in required_actions
        )

        if has_all_requirements:
            player.active_synergies.append(synergy["effect"])
            # Remove emojis from description for console output
            desc_clean = synergy['description'].encode('ascii', 'ignore').decode('ascii')
            print(f"INFO: SYNERGY ACTIVATED: {synergy['name']} - {desc_clean}")

            # 시너지 보너스 적용
            effect = synergy["effect"]
            bonus = synergy["bonus"]

            if effect == "tank_build":
                # 체력 재생 2배
                player.regeneration_rate *= bonus.get("regen_mult", 2.0)

            elif effect == "treasure_hunter":
                # 코인 드롭 3배
                player.coin_drop_multiplier *= bonus.get("coin_mult", 3.0)

            # 다른 시너지들은 전투 중에 체크 (explosive_pierce, lightning_storm 등)


def handle_tactical_upgrade(
    option_index: int, # 인덱스 (0부터 시작)
    player: Player,
    enemies: List[Enemy],
    bullets: List[Bullet],
    gems: List[CoinGem | HealItem],
    effects: List[AnimatedEffect],
    game_data: Dict,
    current_tactical_options: List[Dict], # 현재 선택 가능한 옵션 목록
    player_upgrades: Dict[str, int]
):
    """
    선택된 전술 업그레이드 옵션을 플레이어에게 적용하고 게임 상태를 복귀시킵니다.
    """
    if option_index >= len(current_tactical_options):
        print(f"ERROR: Invalid option index selected: {option_index}")
        return

    # 1. 선택된 옵션 찾기
    selected_option = current_tactical_options[option_index]

    action_method_name = selected_option["action"]
    value = selected_option.get("value", 0)

    # 스킬 선택 정보 (print 문은 인코딩 문제로 제거)
    # print(f"INFO: Selected skill: {selected_option['name']} (Action: {action_method_name})")

    # 스킬 획득 기록
    player.acquired_skills[action_method_name] = player.acquired_skills.get(action_method_name, 0) + 1

    # --- 1. 무기 관련 업그레이드 (기본 화력) ---
    if selected_option["type"] == "weapon":
        weapon = player.weapon

        if action_method_name == "increase_damage":
            weapon.increase_damage(value)
        elif action_method_name == "decrease_cooldown":
            weapon.decrease_cooldown(value)
        elif action_method_name == "add_bullet":
            weapon.add_bullet()

    # --- 2. 속성 스킬 (Explosive, Lightning, Frost) ---
    elif selected_option["type"] == "attribute":
        if action_method_name == "add_explosive":
            player.has_explosive = True
            print("INFO: Explosive Bullets activated! Enemies explode on death.")

        elif action_method_name == "add_chain_explosion":
            player.has_chain_explosion = True
            print("INFO: Chain Reaction activated! Explosions trigger more explosions.")

        elif action_method_name == "add_lightning":
            player.has_lightning = True
            player.lightning_chain_count = int(value)
            print(f"INFO: Chain Lightning activated! Bullets chain to {value} enemies.")

        elif action_method_name == "add_static_field":
            player.has_static_field = True
            print("INFO: Static Field activated! Enemies leave electric damage zones.")

        elif action_method_name == "add_frost":
            player.has_frost = True
            player.frost_slow_ratio = value
            print(f"INFO: Frost Bullets activated! Enemies slowed by {int(value*100)}%.")

        elif action_method_name == "add_deep_freeze":
            player.has_deep_freeze = True
            player.freeze_chance = value
            print(f"INFO: Deep Freeze activated! {int(value*100)}% chance to freeze enemies.")

    # --- 3. 플레이어 스탯 업그레이드 ---
    elif selected_option["type"] == "player":
        if action_method_name == "increase_max_hp":
            player.increase_max_hp(int(value))
        elif action_method_name == "increase_speed":
            player.increase_speed(int(value))
        elif action_method_name == "add_damage_reduction":
            player.damage_reduction += value
            player.damage_reduction = min(player.damage_reduction, 0.75)  # 최대 75% 감소
            print(f"INFO: Damage Reduction increased to {int(player.damage_reduction*100)}%")
        elif action_method_name == "add_regeneration":
            player.regeneration_rate += value
            print(f"INFO: Regeneration activated! +{player.regeneration_rate} HP/sec")

    # --- 4. 토글 업그레이드 ---
    elif selected_option["type"] == "toggle":
        if action_method_name == "toggle_piercing":
            player.is_piercing = True
            print("INFO: Piercing activated!")
        elif action_method_name == "toggle_coin_magnet":
            player.has_coin_magnet = True
            print("INFO: Coin Magnet activated!")

    # --- 5. 게임 유틸리티 ---
    elif selected_option["type"] == "game":
        if action_method_name == "coin_recovery":
            uncollected_score = game_data.get("uncollected_score", 0)
            if uncollected_score > 0:
                ratio = value if value > 0 else 0.5
                recovery_amount = int(uncollected_score * ratio)

                game_data["score"] += recovery_amount
                game_data["uncollected_score"] = 0

                # 필드 위의 모든 코인 젬 제거
                new_gems = [g for g in gems if not isinstance(g, CoinGem)]
                gems[:] = new_gems

                print(f"INFO: Coin Recovery! Gained {recovery_amount} coins.")

        elif action_method_name == "add_lucky_drop":
            player.coin_drop_multiplier += value
            print(f"INFO: Lucky Drop! Coin drops increased to {int(player.coin_drop_multiplier*100)}%")

        elif action_method_name == "add_exp_boost":
            player.exp_multiplier += value
            print(f"INFO: Experience Boost! EXP gain increased to {int(player.exp_multiplier*100)}%")

    # --- 6. 지원 유닛 (Companion) ---
    elif selected_option["type"] == "companion":
        if action_method_name == "add_turret":
            player.turret_count += int(value)
            # 터렛은 자동으로 쿨다운 UI 상단에 배치됨
            # pending_turrets에 배치할 개수 저장
            if "pending_turrets" not in game_data:
                game_data["pending_turrets"] = 0
            game_data["pending_turrets"] += int(value)
            print(f"INFO: Auto Turret acquired! Total: {player.turret_count}. Auto-placed above cooldown UI.")

        elif action_method_name == "add_drone":
            import math
            from objects import Drone

            player.drone_count += int(value)

            # 드론 생성 - main.py에서 drones 리스트 접근 필요
            # 드론은 즉시 생성되어 플레이어 주변에 배치됨
            # 하지만 utils.py에서는 drones 리스트에 접근할 수 없으므로
            # game_data에 임시 저장
            if "pending_drones" not in game_data:
                game_data["pending_drones"] = []

            # 새로운 드론 추가 시 모든 드론의 각도를 재계산하여 균등 분포 유지
            # 예: 2개 → 3개 추가 시, 총 5개를 72도 간격으로 재배치
            new_angles = []
            angle_step = (2 * math.pi) / player.drone_count

            for i in range(player.drone_count):
                orbit_angle = i * angle_step
                new_angles.append(orbit_angle)

            # 기존 pending_drones를 새로운 균등 분포 각도로 교체
            game_data["pending_drones"] = new_angles

            print(f"INFO: Drone Companion acquired! Total: {player.drone_count} drones (evenly distributed)")

    # --- 7. 고급 스킬 (Wave 11-15) ---
    # 29. Bullet Storm - +1 총알 + 50% 연사력
    if action_method_name == "add_bullet_storm":
        player.weapon.add_bullet()
        player.weapon.decrease_cooldown(0.5)
        print("INFO: Bullet Storm activated! More bullets, faster fire!")

    # 30. Execute - 체력 20% 이하 적 즉사
    elif action_method_name == "add_execute":
        player.execute_threshold = value
        print(f"INFO: Execute activated! Instant kill enemies below {int(value*100)}% HP!")

    # 31. Phoenix Rebirth - 사망 시 1회 부활 (120초 쿨다운)
    elif action_method_name == "add_phoenix":
        player.has_phoenix = True
        player.phoenix_cooldown = 0.0  # 쿨다운 완료 상태로 시작
        print("INFO: Phoenix Rebirth activated! You will revive once upon death (120s CD)")

    # 32. Diamond Skin - 30% 영구 데미지 감소
    elif action_method_name == "add_diamond_skin":
        player.damage_reduction += value
        player.damage_reduction = min(player.damage_reduction, 0.75)
        print(f"INFO: Diamond Skin activated! Total damage reduction: {int(player.damage_reduction*100)}%")

    # 33. Berserker - 체력 30% 이하 시 +100% 데미지
    elif action_method_name == "add_berserker":
        player.has_berserker = True
        print("INFO: Berserker activated! +100% damage when HP < 30%!")

    # 34. Starfall - 5킬마다 별똥별 소환
    elif action_method_name == "add_starfall":
        player.has_starfall = True
        player.starfall_kill_counter = 0
        print("INFO: Starfall activated! Stars rain down every 5 kills!")

    # 35. Arcane Mastery - 모든 속성 효과 +50%
    elif action_method_name == "add_arcane_mastery":
        player.has_arcane_mastery = True
        print("INFO: Arcane Mastery activated! All elemental effects boosted by 50%!")

    # 36. Second Chance - 15% 확률로 치명타 회피
    elif action_method_name == "add_second_chance":
        player.second_chance_rate = value
        print(f"INFO: Second Chance activated! {int(value*100)}% chance to dodge fatal damage!")

    # 시너지 체크
    check_and_activate_synergies(player)

    # 공통: 레벨업 확정 및 게임 상태 복귀
    handle_level_up(game_data)

    # 웨이브 클리어 레벨업인 경우 웨이브 준비 화면으로
    if game_data.get("wave_clear_levelup", False):
        # 웨이브 클리어 후 레벨업 → 다음 웨이브 준비 화면으로
        game_data["game_state"] = config.GAME_STATE_WAVE_PREPARE
        game_data["wave_clear_levelup"] = False  # 플래그 초기화
        print(f"INFO: Level up complete! Prepare for Wave {game_data['current_wave']}...")
    else:
        # 킬 기반 레벨업 → 게임 재개
        game_data["game_state"] = config.GAME_STATE_RUNNING


# =========================================================
# 5. 게임 리셋 함수
# =========================================================

def reset_game(screen_size: Tuple[int, int], player_upgrades: Dict[str, int]):
    """
    새로운 게임 세션을 위해 모든 객체와 데이터를 초기화합니다.
    """
    game_data = reset_game_data()
    
    # Player 객체 생성 시 영구 업그레이드 정보를 전달합니다.
    player = Player(
        pos=pygame.math.Vector2(screen_size[0] // 2, screen_size[1] // 2), 
        screen_height=screen_size[1], 
        upgrades=player_upgrades
    )
    
    enemies: List[Enemy] = []
    bullets: List[Bullet] = []
    gems: List[CoinGem | HealItem] = []
    effects: List[AnimatedEffect] = [] # HitImpact 대신 AnimatedEffect 사용

    # 스폰 시간을 game_data 내부 값으로 초기화
    game_data["last_enemy_spawn_time"] = 0.0
    game_data["last_gem_spawn_time"] = 0.0

    return player, enemies, bullets, gems, effects, game_data


# =========================================================
# 시각 효과 헬퍼 함수들
# =========================================================

def create_explosion_particles(pos: Tuple[float, float], particles: List) -> None:
    """적 처치 시 폭발 파티클 생성"""
    from objects import Particle

    settings = config.PARTICLE_SETTINGS["EXPLOSION"]
    count = settings["count"]
    colors = settings["colors"]
    size_range = settings["size_range"]
    lifetime_range = settings["lifetime_range"]
    speed_range = settings["speed_range"]

    for _ in range(count):
        # 랜덤 방향
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(speed_range[0], speed_range[1])
        velocity = pygame.math.Vector2(math.cos(angle), math.sin(angle)) * speed

        # 랜덤 색상, 크기, 수명
        color = random.choice(colors)
        size = random.randint(size_range[0], size_range[1])
        lifetime = random.uniform(lifetime_range[0], lifetime_range[1])

        particle = Particle(pos, velocity, color, size, lifetime, gravity=True)
        particles.append(particle)


def create_hit_particles(pos: Tuple[float, float], particles: List) -> None:
    """일반 피격 시 파티클 생성"""
    from objects import Particle

    settings = config.PARTICLE_SETTINGS["HIT"]
    count = settings["count"]
    colors = settings["colors"]
    size_range = settings["size_range"]
    lifetime_range = settings["lifetime_range"]
    speed_range = settings["speed_range"]

    for _ in range(count):
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(speed_range[0], speed_range[1])
        velocity = pygame.math.Vector2(math.cos(angle), math.sin(angle)) * speed

        color = random.choice(colors)
        size = random.randint(size_range[0], size_range[1])
        lifetime = random.uniform(lifetime_range[0], lifetime_range[1])

        particle = Particle(pos, velocity, color, size, lifetime, gravity=False)
        particles.append(particle)


def create_boss_hit_particles(pos: Tuple[float, float], particles: List) -> None:
    """보스 피격 시 강화된 파티클 생성"""
    from objects import Particle

    settings = config.PARTICLE_SETTINGS["BOSS_HIT"]
    count = settings["count"]
    colors = settings["colors"]
    size_range = settings["size_range"]
    lifetime_range = settings["lifetime_range"]
    speed_range = settings["speed_range"]

    for _ in range(count):
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(speed_range[0], speed_range[1])
        velocity = pygame.math.Vector2(math.cos(angle), math.sin(angle)) * speed

        color = random.choice(colors)
        size = random.randint(size_range[0], size_range[1])
        lifetime = random.uniform(lifetime_range[0], lifetime_range[1])

        particle = Particle(pos, velocity, color, size, lifetime, gravity=True)
        particles.append(particle)


def create_shockwave(pos: Tuple[float, float], shockwave_type: str, effects: List) -> None:
    """충격파 효과 생성 (BOSS_SPAWN, BOSS_DEATH, BOSS_ATTACK)"""
    from objects import Shockwave

    if shockwave_type not in config.SHOCKWAVE_SETTINGS:
        return

    settings = config.SHOCKWAVE_SETTINGS[shockwave_type]
    shockwave = Shockwave(
        center=pos,
        max_radius=settings["max_radius"],
        duration=settings["duration"],
        color=settings["color"],
        width=settings["width"]
    )
    effects.append(shockwave)


def create_spawn_effect(pos: Tuple[float, float], effects: List) -> None:
    """적 스폰 포털 효과 생성"""
    from objects import SpawnEffect

    spawn_effect = SpawnEffect(
        pos=pos,
        duration=config.SPAWN_EFFECT_DURATION,
        max_size=config.SPAWN_EFFECT_SIZE
    )
    effects.append(spawn_effect)


def create_dynamic_text(text: str, pos: Tuple[float, float], text_type: str, effects: List) -> None:
    """동적 텍스트 효과 생성 (BOSS_SPAWN, CRITICAL)"""
    from objects import DynamicTextEffect

    if text_type not in config.DYNAMIC_TEXT_SETTINGS:
        return

    settings = config.DYNAMIC_TEXT_SETTINGS[text_type]
    dynamic_text = DynamicTextEffect(
        text=text,
        size=settings["size"],
        color=settings["color"],
        pos=pos,
        duration_frames=settings["duration_frames"],
        shake_intensity=settings["shake_intensity"]
    )
    effects.append(dynamic_text)


def trigger_screen_shake(shake_type: str, screen_shake: 'ScreenShake') -> None:
    """화면 떨림 트리거 (PLAYER_HIT, BOSS_HIT, BOSS_SPAWN, BOSS_DEATH, ENEMY_DEATH)"""
    if shake_type not in config.SCREEN_SHAKE_SETTINGS:
        return

    settings = config.SCREEN_SHAKE_SETTINGS[shake_type]
    screen_shake.start_shake(
        intensity=settings["intensity"],
        duration_frames=settings["duration"]
    )


def create_time_slow_effect(effects: List) -> None:
    """타임 슬로우 효과 생성 (보스 처치 시)"""
    from objects import TimeSlowEffect

    settings = config.TIME_SLOW_SETTINGS["BOSS_DEATH"]
    time_slow = TimeSlowEffect(
        slow_factor=settings["slow_factor"],
        duration=settings["duration"]
    )
    effects.append(time_slow)


def update_visual_effects(effects: List, dt: float, screen_size: Tuple[int, int] = None, enemies: List = None) -> None:
    """모든 시각 효과 업데이트 (파티클, 충격파, 텍스트 등)"""
    from objects import Particle, Shockwave, DynamicTextEffect, SpawnEffect, TimeSlowEffect, StaticField, ScreenFlash, WaveTransitionEffect, PlayerVictoryAnimation, ReviveTextEffect, LightningEffect

    for effect in effects[:]:
        if isinstance(effect, (Particle, Shockwave, SpawnEffect)):
            effect.update(dt)
            if not effect.is_alive:
                effects.remove(effect)
        elif isinstance(effect, LightningEffect):
            effect.update(dt)
            if not effect.is_alive:
                effects.remove(effect)
        elif isinstance(effect, DynamicTextEffect):
            effect.update(dt)
            if not effect.is_alive:
                effects.remove(effect)
        elif isinstance(effect, TimeSlowEffect):
            effect.update(dt)
            if not effect.is_active:
                effects.remove(effect)
        elif isinstance(effect, StaticField):
            effect.update(dt)
            if enemies:
                effect.apply_damage(enemies, dt)
            if not effect.is_active:
                effects.remove(effect)
        elif isinstance(effect, ScreenFlash):
            effect.update(dt)
            if not effect.is_alive:
                effects.remove(effect)
        elif isinstance(effect, WaveTransitionEffect):
            effect.update(dt)
            if not effect.is_alive:
                effects.remove(effect)
        elif isinstance(effect, PlayerVictoryAnimation):
            effect.update(dt)
            if not effect.is_alive:
                effects.remove(effect)
        elif isinstance(effect, ReviveTextEffect):
            effect.update(dt)
            if not effect.is_alive:
                effects.remove(effect)
        elif isinstance(effect, AnimatedEffect):
            # 기존 AnimatedEffect는 current_time 필요
            current_time = pygame.time.get_ticks() / 1000.0
            effect.update(dt, current_time)
            if effect.is_finished:
                effects.remove(effect)


# =========================================================
# 터렛 자동 배치 함수 (wave_mode, story_mode 공통)
# =========================================================

def calculate_turret_positions(turret_count: int, screen_size: Tuple[int, int], turret_spacing: int = 100) -> List[Tuple[float, float]]:
    """
    터렛 배치 위치 계산 (쿨다운 UI 상단, 좌우 균형)

    Args:
        turret_count: 배치할 터렛 총 개수
        screen_size: 화면 크기 (width, height)
        turret_spacing: 터렛 간 간격 (기본 100)

    Returns:
        터렛 위치 리스트 [(x1, y1), (x2, y2), ...]
    """
    if turret_count <= 0:
        return []

    base_x = screen_size[0] // 2
    base_y = screen_size[1] - 60 - 100  # 쿨다운 UI 상단

    positions = []
    for i in range(turret_count):
        if turret_count == 1:
            pos_x = base_x
        elif turret_count == 2:
            pos_x = base_x - turret_spacing // 2 + i * turret_spacing
        else:
            half_width = (turret_count - 1) * turret_spacing / 2
            pos_x = base_x - half_width + i * turret_spacing

        positions.append((pos_x, base_y))

    return positions


def auto_place_turrets(turrets: List, game_data: Dict, screen_size: Tuple[int, int],
                       turret_class, sound_manager=None) -> int:
    """
    터렛을 쿨다운 UI 상단에 자동 배치

    Args:
        turrets: 터렛 리스트 (수정됨)
        game_data: 게임 데이터 딕셔너리
        screen_size: 화면 크기
        turret_class: Turret 클래스 (from objects import Turret)
        sound_manager: 사운드 매니저 (옵션)

    Returns:
        배치된 터렛 수
    """
    pending = game_data.get("pending_turrets", 0)
    if pending <= 0:
        return 0

    # 새 터렛 추가
    for _ in range(pending):
        turrets.append(turret_class(pos=(0, 0)))  # 임시 위치

    # 전체 터렛 위치 재계산
    total_count = len(turrets)
    positions = calculate_turret_positions(total_count, screen_size)

    for i, turret in enumerate(turrets):
        if i < len(positions):
            turret.pos.x = positions[i][0]
            turret.pos.y = positions[i][1]

    game_data["pending_turrets"] = 0

    if sound_manager:
        sound_manager.play_sfx("turret_place")

    print(f"INFO: {pending} turret(s) auto-placed. Total: {total_count}")
    return pending


# =========================================================
# Ship Ability 발동 처리 (wave_mode, story_mode 공통)
# =========================================================

def trigger_ship_ability(player, enemies: List, effects: List,
                        effect_system=None, sound_manager=None,
                        silent: bool = False) -> bool:
    """
    함선 특수 능력 발동 및 시각/사운드 효과 처리

    Args:
        player: Player 객체
        enemies: 적 리스트
        effects: 이펙트 리스트
        effect_system: EffectSystem 인스턴스 (시각 효과용, 옵션)
        sound_manager: SoundManager 인스턴스 (사운드용, 옵션)
        silent: True면 로그 출력 안함

    Returns:
        능력 발동 성공 여부
    """
    if not player or not hasattr(player, 'use_ship_ability'):
        return False

    ability_type = getattr(player, 'ship_ability_type', None)

    if not player.use_ship_ability(enemies, effects):
        return False

    # 시각 효과 생성 (effect_system이 있는 경우만)
    if effect_system:
        if ability_type == "bomb_drop":
            effect_system.create_bomb_explosion(
                effects, player.pos.copy(),
                getattr(player, 'bomb_radius', 200)
            )
        elif ability_type == "shield":
            effect_system.create_shield_effect(effects, player.pos.copy())
        elif ability_type == "cloaking":
            effect_system.create_cloak_effect(effects, player.pos.copy())
        elif ability_type == "evasion_boost":
            effect_system.create_evasion_effect(effects, player.pos.copy())

    # 사운드 재생
    if sound_manager:
        ability_sounds = {
            "bomb_drop": "ability_bomb",
            "shield": "ability_shield",
            "cloaking": "ability_cloak",
            "evasion_boost": "ability_evasion"
        }
        sfx_name = ability_sounds.get(ability_type)
        if sfx_name:
            sound_manager.play_sfx(sfx_name)

    # 로그 출력
    if not silent:
        ability_info = player.get_ship_ability_info() if hasattr(player, 'get_ship_ability_info') else None
        ability_name = ability_info['name'] if ability_info else ability_type
        print(f"INFO: Ship ability '{ability_name}' activated!")

    return True


def draw_visual_effects(screen: pygame.Surface, effects: List, screen_offset: pygame.math.Vector2 = None) -> None:
    """모든 시각 효과 그리기"""
    from objects import Particle, Shockwave, DynamicTextEffect, SpawnEffect, TimeSlowEffect, StaticField, ScreenFlash, WaveTransitionEffect, ReviveTextEffect, LightningEffect

    if screen_offset is None:
        screen_offset = pygame.math.Vector2(0, 0)

    for effect in effects:
        if isinstance(effect, (Particle, Shockwave, SpawnEffect, AnimatedEffect, StaticField, ScreenFlash, WaveTransitionEffect, ReviveTextEffect, LightningEffect)):
            effect.draw(screen)
        elif isinstance(effect, DynamicTextEffect):
            effect.draw(screen, screen_offset)