# systems/skill_system.py
"""
SkillSystem - 스킬 로직 시스템
폭발, 번개, 빙결 등 모든 스킬 처리
모든 모드에서 공유
"""

import pygame
import random
import math
from typing import List, Optional
import config
from objects import Player, Enemy


class SkillSystem:
    """
    스킬 시스템 - 모든 모드에서 공유하는 스킬 로직

    기능:
    - 스킬 적용 (폭발, 번개, 빙결 등)
    - 스킬 이펙트 생성
    - 시너지 효과 처리
    """

    def __init__(self):
        """스킬 시스템 초기화"""
        # 스킬 핸들러 매핑
        self.skill_handlers = {
            "explosive": self._handle_explosive,
            "lightning": self._handle_lightning,
            "frost": self._handle_frost,
            "static_field": self._handle_static_field,
            "execute": self._handle_execute,
            "starfall": self._handle_starfall,
        }

    def apply_skill(
        self,
        skill_id: str,
        player: Player,
        targets: List[Enemy],
        effects: List,
        position: pygame.math.Vector2 = None,
        **kwargs
    ) -> int:
        """
        스킬 적용

        Args:
            skill_id: 스킬 ID
            player: 플레이어
            targets: 대상 적 리스트
            effects: 이펙트 리스트
            position: 스킬 발동 위치
            **kwargs: 추가 인자

        Returns:
            스킬로 처치한 적 수
        """
        handler = self.skill_handlers.get(skill_id)
        if handler:
            return handler(player, targets, effects, position, **kwargs)
        return 0

    def update_passive_skills(
        self,
        player: Player,
        enemies: List[Enemy],
        effects: List,
        dt: float,
        current_time: float,
    ):
        """
        패시브 스킬 업데이트 (매 프레임 호출)

        Args:
            player: 플레이어
            enemies: 적 리스트
            effects: 이펙트 리스트
            dt: 델타 타임
            current_time: 현재 시간
        """
        if not player:
            return

        # 정적 필드 (Static Field)
        if player.has_static_field:
            self._update_static_field(player, enemies, effects, dt, current_time)

        # 피닉스 리버스 쿨다운
        if hasattr(player, 'phoenix_cooldown') and player.phoenix_cooldown > 0:
            player.phoenix_cooldown = max(0, player.phoenix_cooldown - dt)

        # 재생 (Regeneration) - 사망 상태면 회복 안 함
        if player.regeneration_rate > 0 and not getattr(player, 'is_dead', False) and player.hp > 0:
            player.hp = min(player.max_hp, player.hp + player.regeneration_rate * dt)

    def _handle_explosive(
        self,
        player: Player,
        targets: List[Enemy],
        effects: List,
        position: pygame.math.Vector2,
        **kwargs
    ) -> int:
        """폭발 스킬 처리"""
        from utils import create_explosion_particles
        from objects import Shockwave

        if not player.has_explosive or not position:
            return 0

        kills = 0
        radius = player.explosive_radius

        # 폭발 이펙트
        create_explosion_particles(effects, position)
        effects.append(Shockwave(position, radius))

        # 범위 내 적에게 데미지
        for enemy in targets[:]:
            if not enemy.is_alive:
                continue

            distance = position.distance_to(enemy.pos)
            if distance < radius:
                # 거리에 따른 데미지 감소
                damage_ratio = 1.0 - (distance / radius) * 0.5
                damage = config.EXPLOSIVE_DAMAGE * damage_ratio

                enemy.take_damage(damage)

                if not enemy.is_alive:
                    kills += 1

                    # 연쇄 폭발 체크
                    if player.has_chain_explosion and random.random() < config.CHAIN_EXPLOSION_CHANCE:
                        kills += self._handle_explosive(
                            player, targets, effects, enemy.pos,
                            chain_count=kwargs.get('chain_count', 0) + 1
                        )

        return kills

    def _handle_lightning(
        self,
        player: Player,
        targets: List[Enemy],
        effects: List,
        position: pygame.math.Vector2,
        **kwargs
    ) -> int:
        """번개 체인 스킬 처리"""
        from objects import LightningEffect

        if not player.has_lightning or not position:
            return 0

        kills = 0
        chain_count = player.lightning_chain_count
        chain_range = config.LIGHTNING_CHAIN_RANGE
        damage = config.LIGHTNING_DAMAGE

        hit_enemies = []
        current_pos = position

        for i in range(chain_count):
            # 가장 가까운 적 찾기
            nearest_enemy = None
            nearest_distance = float('inf')

            for enemy in targets:
                if not enemy.is_alive or enemy in hit_enemies:
                    continue

                distance = current_pos.distance_to(enemy.pos)
                if distance < chain_range and distance < nearest_distance:
                    nearest_enemy = enemy
                    nearest_distance = distance

            if not nearest_enemy:
                break

            # 번개 이펙트
            effects.append(LightningEffect(current_pos, nearest_enemy.pos))

            # 데미지 적용
            nearest_enemy.take_damage(damage)
            hit_enemies.append(nearest_enemy)

            if not nearest_enemy.is_alive:
                kills += 1

            current_pos = nearest_enemy.pos

        return kills

    def _handle_frost(
        self,
        player: Player,
        targets: List[Enemy],
        effects: List,
        position: pygame.math.Vector2,
        **kwargs
    ) -> int:
        """빙결 스킬 처리"""
        if not player.has_frost or not position:
            return 0

        kills = 0
        slow_ratio = player.frost_slow_ratio
        freeze_chance = player.freeze_chance if player.has_deep_freeze else 0

        for enemy in targets:
            if not enemy.is_alive:
                continue

            distance = position.distance_to(enemy.pos)
            if distance < config.FROST_RANGE:
                # 슬로우 적용
                enemy.apply_slow(slow_ratio, config.FROST_DURATION)

                # 딥 프리즈 체크 (완전 빙결)
                if freeze_chance > 0 and random.random() < freeze_chance:
                    enemy.apply_freeze(config.DEEP_FREEZE_DURATION)

        return kills

    def _handle_static_field(
        self,
        player: Player,
        targets: List[Enemy],
        effects: List,
        position: pygame.math.Vector2,
        **kwargs
    ) -> int:
        """정적 필드 스킬 처리"""
        # 패시브 - _update_static_field에서 처리
        return 0

    def _update_static_field(
        self,
        player: Player,
        enemies: List[Enemy],
        effects: List,
        dt: float,
        current_time: float,
    ):
        """정적 필드 업데이트 (매 프레임)"""
        if not player.has_static_field:
            return

        # 설정값 가져오기
        static_field_settings = config.ATTRIBUTE_SKILL_SETTINGS.get("STATIC_FIELD", {})
        tick_interval = static_field_settings.get("tick_interval", 0.5)
        radius = static_field_settings.get("radius", 180)
        damage_per_sec = static_field_settings.get("damage_per_sec", 10)

        # 틱 데미지 간격 체크
        if not hasattr(player, 'static_field_last_tick'):
            player.static_field_last_tick = 0

        if current_time - player.static_field_last_tick < tick_interval:
            return

        player.static_field_last_tick = current_time

        # 틱당 데미지 계산
        tick_damage = damage_per_sec * tick_interval

        # 범위 내 적에게 틱 데미지
        for enemy in enemies:
            if not enemy.is_alive:
                continue

            distance = player.pos.distance_to(enemy.pos)
            if distance < radius:
                enemy.take_damage(tick_damage)

    def _handle_execute(
        self,
        player: Player,
        targets: List[Enemy],
        effects: List,
        position: pygame.math.Vector2,
        **kwargs
    ) -> int:
        """처형 스킬 처리 (낮은 HP 적 즉사)"""
        from objects import ExecuteEffect

        if player.execute_threshold <= 0:
            return 0

        kills = 0
        threshold = player.execute_threshold

        for enemy in targets[:]:
            if not enemy.is_alive:
                continue

            hp_ratio = enemy.hp / enemy.max_hp
            if hp_ratio <= threshold:
                # 처형 시각 효과 추가
                effects.append(ExecuteEffect(enemy.pos))
                enemy.hp = 0
                enemy.is_alive = False
                kills += 1

        return kills

    def _handle_starfall(
        self,
        player: Player,
        targets: List[Enemy],
        effects: List,
        position: pygame.math.Vector2,
        **kwargs
    ) -> int:
        """별똥별 스킬 처리 (궁극기)"""
        from objects import StarfallEffect

        if not player.has_starfall:
            return 0

        kills = 0

        # 랜덤 위치에 별똥별 생성
        for _ in range(config.STARFALL_COUNT):
            star_pos = pygame.math.Vector2(
                random.uniform(100, kwargs.get('screen_width', 1920) - 100),
                random.uniform(100, kwargs.get('screen_height', 1080) - 100)
            )
            effects.append(StarfallEffect(star_pos))

            # 범위 데미지
            for enemy in targets:
                if not enemy.is_alive:
                    continue

                distance = star_pos.distance_to(enemy.pos)
                if distance < config.STARFALL_RADIUS:
                    enemy.take_damage(config.STARFALL_DAMAGE)

                    if not enemy.is_alive:
                        kills += 1

        return kills


print("INFO: skill_system.py loaded")
