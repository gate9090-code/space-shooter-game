# systems/spawn_system.py
"""
SpawnSystem - 적/아이템 스폰 시스템
웨이브 기반 적 스폰, 보스 스폰, 젬 스폰 등
모든 모드에서 공유 (설정만 다르게)
"""

import pygame
import random
import math
from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass
import config
# Entity imports from new modules
from entities.enemies import Enemy
from entities.collectibles import CoinGem, HealItem


@dataclass
class SpawnConfig:
    """스폰 설정"""
    # 적 스폰 설정
    enemy_spawn_interval: float = 1.5  # 1.0 → 1.5초로 변경
    enemy_spawn_count: int = 1
    enemy_types: List[str] = None
    enemy_stats_multiplier: float = 1.0

    # 보스 설정
    boss_enabled: bool = True
    boss_spawn_wave: int = 5

    # 젬 스폰 설정
    gem_spawn_interval: float = 5.0
    gem_spawn_chance: float = 0.3

    def __post_init__(self):
        if self.enemy_types is None:
            self.enemy_types = ["normal"]


class SpawnSystem:
    """
    스폰 시스템 - 모든 모드에서 공유하는 스폰 로직

    기능:
    - 적 스폰 (웨이브 기반)
    - 보스 스폰
    - 젬/아이템 스폰
    """

    def __init__(self, spawn_config: SpawnConfig = None):
        """
        스폰 시스템 초기화

        Args:
            spawn_config: 스폰 설정 (모드별로 다르게 전달)
        """
        self.config = spawn_config or SpawnConfig()
        self.last_enemy_spawn_time = 0
        self.last_gem_spawn_time = 0

    def spawn_enemies(
        self,
        enemies: List[Enemy],
        screen_size: Tuple[int, int],
        current_time: float,
        game_data: Dict,
        effects: List = None,
        sound_manager = None,
    ) -> List[Enemy]:
        """
        적 스폰 처리

        Args:
            enemies: 현재 적 리스트
            screen_size: 화면 크기
            current_time: 현재 시간
            game_data: 게임 데이터
            effects: 이펙트 리스트
            sound_manager: 사운드 매니저

        Returns:
            새로 스폰된 적 리스트
        """
        spawned = []

        # 스폰 쿨다운 체크
        if current_time - self.last_enemy_spawn_time < self.config.enemy_spawn_interval:
            return spawned

        # 웨이브 상태 체크
        wave_state = game_data.get('wave_state', 'NOT_STARTED')
        if wave_state != 'IN_PROGRESS':
            return spawned

        # 목표 처치 수 도달 체크
        wave_kills = game_data.get('wave_kills', 0)
        target_kills = game_data.get('wave_target_kills', 0)
        if wave_kills >= target_kills:
            return spawned

        # 현재 웨이브 정보
        current_wave = game_data.get('current_wave', 1)
        wave_info = config.WAVE_CONFIGS.get(current_wave, {})

        # 스폰 수 결정
        spawn_count = wave_info.get('spawn_count', self.config.enemy_spawn_count)

        for _ in range(spawn_count):
            # 최대 적 수 체크
            max_enemies = wave_info.get('max_enemies', config.MAX_ENEMIES_ON_SCREEN)
            if len(enemies) >= max_enemies:
                break

            # 스폰 위치 결정 (화면 가장자리)
            spawn_pos = self._get_spawn_position(screen_size)

            # 적 타입 결정
            enemy_type = self._select_enemy_type(wave_info, current_wave)

            # 적 생성
            enemy = self._create_enemy(enemy_type, spawn_pos, screen_size[1], current_wave)

            if enemy:
                enemies.append(enemy)
                spawned.append(enemy)

                # 스폰 효과
                if effects:
                    from game_logic import create_spawn_effect
                    create_spawn_effect(effects, spawn_pos)

        self.last_enemy_spawn_time = current_time
        return spawned

    def spawn_boss(
        self,
        enemies: List[Enemy],
        screen_size: Tuple[int, int],
        game_data: Dict,
        effects: List = None,
        sound_manager = None,
    ) -> Optional[Enemy]:
        """
        보스 스폰

        Args:
            enemies: 현재 적 리스트
            screen_size: 화면 크기
            game_data: 게임 데이터
            effects: 이펙트 리스트
            sound_manager: 사운드 매니저

        Returns:
            스폰된 보스 (없으면 None)
        """
        current_wave = game_data.get('current_wave', 1)

        # 보스 웨이브 체크
        if current_wave not in config.BOSS_WAVES:
            return None

        # 이미 보스가 있는지 체크
        for enemy in enemies:
            if hasattr(enemy, 'is_boss') and enemy.is_boss:
                return None

        # 보스 스폰 위치 (화면 상단 중앙)
        spawn_pos = pygame.math.Vector2(screen_size[0] / 2, -50)

        # 보스 생성
        boss = self._create_boss(current_wave, spawn_pos, screen_size[1])

        if boss:
            enemies.append(boss)

            # 보스 스폰 효과
            if effects:
                from game_logic import create_spawn_effect
                create_spawn_effect(effects, spawn_pos)

            # 보스 BGM
            if sound_manager:
                sound_manager.play_sfx("boss_spawn")

            print(f"INFO: Boss spawned for wave {current_wave}")

        return boss

    def spawn_gems(
        self,
        gems: List,
        screen_size: Tuple[int, int],
        current_time: float,
        game_data: Dict,
    ) -> List:
        """
        젬 스폰 처리

        Args:
            gems: 현재 젬 리스트
            screen_size: 화면 크기
            current_time: 현재 시간
            game_data: 게임 데이터

        Returns:
            새로 스폰된 젬 리스트
        """
        spawned = []

        # 스폰 쿨다운 체크
        if current_time - self.last_gem_spawn_time < self.config.gem_spawn_interval:
            return spawned

        # 스폰 확률 체크
        if random.random() > self.config.gem_spawn_chance:
            self.last_gem_spawn_time = current_time
            return spawned

        # 스폰 위치 (화면 내 랜덤)
        margin = 100
        spawn_pos = pygame.math.Vector2(
            random.uniform(margin, screen_size[0] - margin),
            random.uniform(margin, screen_size[1] - margin)
        )

        # 젬 타입 결정 (코인 or 힐)
        if random.random() < config.HEAL_SPAWN_CHANCE:
            gem = HealItem(
                pos=spawn_pos,
                screen_height=screen_size[1],
                heal_amount=config.HEAL_ITEM_AMOUNT
            )
        else:
            gem = CoinGem(
                pos=spawn_pos,
                screen_height=screen_size[1],
                value=config.COIN_GEM_VALUE
            )

        gems.append(gem)
        spawned.append(gem)

        self.last_gem_spawn_time = current_time
        return spawned

    def _get_spawn_position(self, screen_size: Tuple[int, int]) -> pygame.math.Vector2:
        """적 스폰 위치 결정 (화면 가장자리)"""
        margin = 50
        side = random.randint(0, 3)

        if side == 0:  # 상단
            return pygame.math.Vector2(
                random.uniform(margin, screen_size[0] - margin),
                -margin
            )
        elif side == 1:  # 하단
            return pygame.math.Vector2(
                random.uniform(margin, screen_size[0] - margin),
                screen_size[1] + margin
            )
        elif side == 2:  # 좌측
            return pygame.math.Vector2(
                -margin,
                random.uniform(margin, screen_size[1] - margin)
            )
        else:  # 우측
            return pygame.math.Vector2(
                screen_size[0] + margin,
                random.uniform(margin, screen_size[1] - margin)
            )

    def _select_enemy_type(self, wave_info: Dict, current_wave: int) -> str:
        """적 타입 선택"""
        enemy_types = wave_info.get('enemy_types', self.config.enemy_types)

        if not enemy_types:
            return "normal"

        # 가중치 기반 선택
        if isinstance(enemy_types, dict):
            total_weight = sum(enemy_types.values())
            rand = random.uniform(0, total_weight)
            current = 0
            for enemy_type, weight in enemy_types.items():
                current += weight
                if rand <= current:
                    return enemy_type
            return list(enemy_types.keys())[0]

        return random.choice(enemy_types)

    def _create_enemy(
        self,
        enemy_type: str,
        position: pygame.math.Vector2,
        screen_height: int,
        current_wave: int,
    ) -> Optional[Enemy]:
        """적 생성"""
        # 웨이브별 스탯 배율
        wave_multiplier = 1.0 + (current_wave - 1) * 0.1

        # 적 타입별 기본 스탯
        enemy_stats = config.ENEMY_TYPES.get(enemy_type, config.ENEMY_TYPES.get("normal", {}))

        try:
            enemy = Enemy(
                pos=position.copy(),
                screen_height=screen_height,
                enemy_type=enemy_type,
                hp=enemy_stats.get('hp', 30) * wave_multiplier * self.config.enemy_stats_multiplier,
                speed=enemy_stats.get('speed', 2.0),
                damage=enemy_stats.get('damage', 10) * wave_multiplier,
            )
            return enemy
        except Exception as e:
            print(f"WARNING: Failed to create enemy: {e}")
            return None

    def _create_boss(
        self,
        current_wave: int,
        position: pygame.math.Vector2,
        screen_height: int,
    ) -> Optional[Enemy]:
        """보스 생성"""
        # 웨이브별 보스 설정
        boss_config = config.BOSS_CONFIGS.get(current_wave, {})

        try:
            boss = Enemy(
                pos=position.copy(),
                screen_height=screen_height,
                enemy_type="boss",
                hp=boss_config.get('hp', 500),
                speed=boss_config.get('speed', 1.5),
                damage=boss_config.get('damage', 20),
                is_boss=True,
            )
            return boss
        except Exception as e:
            print(f"WARNING: Failed to create boss: {e}")
            return None

    def spawn_respawned_enemies(
        self,
        enemies: List[Enemy],
        screen_size: Tuple[int, int],
        current_time: float,
        game_data: Dict,
        effects: List = None,
    ) -> List[Enemy]:
        """
        웨이브 전환 후 리스폰 적(빨간색) 스폰

        Args:
            enemies: 현재 적 리스트
            screen_size: 화면 크기
            current_time: 현재 시간
            game_data: 게임 데이터
            effects: 이펙트 리스트

        Returns:
            새로 스폰된 리스폰 적 리스트
        """
        spawned = []

        # 스폰 쿨다운 체크
        time_since_spawn = current_time - self.last_enemy_spawn_time
        if time_since_spawn < self.config.enemy_spawn_interval:
            return spawned

        # 웨이브 페이즈 체크 (CLEANUP 페이즈에서만 스폰)
        wave_phase = game_data.get('wave_phase', 'normal')
        if wave_phase != 'cleanup':
            return spawned

        current_wave = game_data.get('current_wave', 1)

        # 최대 리스폰 적 수 제한 (현재 화면의 리스폰 적 수 체크)
        respawned_count = sum(1 for e in enemies if hasattr(e, 'is_respawned') and e.is_respawned and e.is_alive)
        max_respawned = 5  # 최대 5마리

        if respawned_count >= max_respawned:
            return spawned

        # 스폰 위치 결정
        spawn_pos = self._get_spawn_position(screen_size)

        # 리스폰 적 생성
        enemy = self._create_respawned_enemy(spawn_pos, screen_size[1], current_wave)

        if enemy:
            enemies.append(enemy)
            spawned.append(enemy)

            # 스폰 효과
            if effects:
                from game_logic import create_spawn_effect
                create_spawn_effect(spawn_pos, effects)

        self.last_enemy_spawn_time = current_time
        return spawned

    def _create_respawned_enemy(
        self,
        position: pygame.math.Vector2,
        screen_height: int,
        current_wave: int,
    ) -> Optional[Enemy]:
        """리스폰 적(빨간색) 생성"""
        # 웨이브 스케일링 정보
        wave_scaling = config.WAVE_SCALING.get(current_wave, {})
        chase_prob = wave_scaling.get('chase_prob', 0.8)

        try:
            enemy = Enemy(
                pos=position.copy(),
                screen_height=screen_height,
                chase_probability=chase_prob,
                enemy_type="RESPAWNED",  # 빨간색 리스폰 적
            )
            # 회전 공격 모드로 설정
            enemy.is_circling = True
            return enemy
        except Exception as e:
            print(f"WARNING: Failed to create respawned enemy: {e}")
            import traceback
            traceback.print_exc()
            return None


print("INFO: spawn_system.py loaded")
