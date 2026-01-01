# game_logic/spawning.py
"""
Spawning-related functions.
Handles enemy spawning, gem spawning, and turret placement.
"""

import pygame
import random
import config
from typing import Dict, List, Tuple
from entities.player import Player
from entities.enemies import Enemy, Boss
from entities.collectibles import CoinGem, HealItem


def spawn_enemy(enemies: List[Enemy], screen_size: Tuple[int, int], game_data: Dict):
    """화면 바깥쪽 임의의 위치에 적을 스폰합니다. (웨이브 스케일링 적용)"""
    from .wave_manager import get_wave_scaling, select_enemy_type

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
    from .wave_manager import get_wave_scaling
    from .helpers import create_spawn_effect, create_shockwave, create_dynamic_text

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
        turret_class: Turret 클래스 (from entities.support_units import Turret)
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
