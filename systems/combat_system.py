# systems/combat_system.py
"""
CombatSystem - 전투 로직 시스템
총알-적 충돌, 플레이어-적 충돌, 데미지 처리 등
모든 모드에서 공유
"""

import pygame
from typing import List, Optional, Tuple
import config
# Entity imports from new modules
from entities.player import Player
from entities.enemies import Enemy
from entities.weapons import Bullet
from entities.collectibles import CoinGem, HealItem


class CombatSystem:
    """
    전투 시스템 - 모든 모드에서 공유하는 전투 로직

    기능:
    - 총알-적 충돌 처리
    - 플레이어-적 충돌 처리
    - 데미지 계산
    - 처치 보상 생성
    """

    def __init__(self):
        """전투 시스템 초기화"""
        pass

    def process_bullet_enemy_collision(
        self,
        bullets: List[Bullet],
        enemies: List[Enemy],
        gems: List,
        effects: List,
        damage_numbers: List,
        screen_shake,
        sound_manager,
        death_effect_manager,
        game_data: dict,
        screen_size: Tuple[int, int],
    ) -> int:
        """
        총알-적 충돌 처리

        Args:
            bullets: 총알 리스트
            enemies: 적 리스트
            gems: 젬 리스트 (드롭용)
            effects: 이펙트 리스트
            damage_numbers: 데미지 넘버 리스트
            screen_shake: 화면 흔들림 매니저
            sound_manager: 사운드 매니저
            death_effect_manager: 사망 효과 매니저
            game_data: 게임 데이터
            screen_size: 화면 크기

        Returns:
            처치한 적 수
        """
        from game_logic import (
            create_hit_particles,
            create_explosion_particles,
            create_boss_hit_particles,
            trigger_screen_shake,
        )
        from effects.combat_effects import DamageNumber

        kills = 0

        for bullet in bullets[:]:
            if not bullet.is_alive:
                continue

            for enemy in enemies[:]:
                if not enemy.is_alive:
                    continue

                # 충돌 체크
                distance = bullet.pos.distance_to(enemy.pos)
                collision_radius = bullet.hitbox.width / 2 + enemy.hitbox.width / 2

                if distance < collision_radius:
                    # 데미지 계산
                    damage = self._calculate_damage(bullet, enemy)

                    # 데미지 적용
                    enemy.take_damage(damage)

                    # 데미지 넘버 생성
                    dmg_num = DamageNumber(
                        pos=enemy.pos.copy(),
                        damage=damage,
                        is_crit=getattr(bullet, 'is_crit', False)
                    )
                    damage_numbers.append(dmg_num)

                    # 히트 이펙트
                    if hasattr(enemy, 'is_boss') and enemy.is_boss:
                        create_boss_hit_particles(effects, bullet.pos)
                    else:
                        create_hit_particles(effects, bullet.pos)

                    # 충격파 효과 추가
                    from effects.screen_effects import ImageShockwave
                    import config
                    settings = config.SHOCKWAVE_SETTINGS.get("BULLET_HIT", {})
                    wave_count = settings.get("wave_count", 3)
                    wave_interval = settings.get("wave_interval", 0.08)

                    for i in range(wave_count):
                        shockwave = ImageShockwave(
                            center=(bullet.pos.x, bullet.pos.y),
                            max_size=settings.get("max_radius", 80) * 2,
                            duration=settings.get("duration", 0.6),
                            delay=i * wave_interval,
                            color_tint=settings.get("color", (255, 255, 255)),
                        )
                        effects.append(shockwave)

                    # 히트 사운드
                    sound_manager.play_sfx("enemy_hit")

                    # 적 처치 확인
                    if not enemy.is_alive:
                        kills += 1

                        # 처치 보상
                        self._spawn_drop(enemy, gems, screen_size, game_data)

                        # 폭발 이펙트
                        create_explosion_particles(effects, enemy.pos)

                        # 사망 효과
                        death_effect_manager.trigger(enemy.pos)

                        # 보스 처치 시 화면 흔들림
                        if hasattr(enemy, 'is_boss') and enemy.is_boss:
                            trigger_screen_shake(screen_shake, intensity=15, duration=0.5)
                            sound_manager.play_sfx("explosion")
                        else:
                            sound_manager.play_sfx("enemy_death")

                        # 통계 업데이트
                        game_data['kills_this_wave'] = game_data.get('kills_this_wave', 0) + 1
                        game_data['wave_kills'] = game_data.get('wave_kills', 0) + 1

                        enemies.remove(enemy)

                    # 관통 총알이 아니면 제거
                    if not getattr(bullet, 'is_piercing', False):
                        if bullet in bullets:
                            bullets.remove(bullet)
                        break

        return kills

    def process_player_enemy_collision(
        self,
        player: Player,
        enemies: List[Enemy],
        effects: List,
        sound_manager,
        current_time: float,
    ) -> bool:
        """
        플레이어-적 충돌 처리

        Args:
            player: 플레이어
            enemies: 적 리스트
            effects: 이펙트 리스트
            sound_manager: 사운드 매니저
            current_time: 현재 시간

        Returns:
            플레이어가 피해를 받았으면 True
        """
        if not player or player.is_invincible:
            return False

        took_damage = False

        # 먼저 모든 적의 화상 상태를 초기화
        for enemy in enemies:
            if enemy.is_alive:
                enemy.is_burning = False

        # 충돌 확인 및 화상 상태 설정
        for enemy in enemies:
            if not enemy.is_alive:
                continue

            # 충돌 체크
            distance = player.pos.distance_to(enemy.pos)
            collision_radius = player.hitbox.width / 2 + enemy.hitbox.width / 2

            if distance < collision_radius:
                # 플레이어와 접촉 중 - 화상 이미지 활성화
                enemy.is_burning = True

                # 쿨다운 체크
                if current_time - player.last_hit_time < player.hit_cooldown:
                    continue

                # 데미지 적용
                damage = getattr(enemy, 'contact_damage', config.ENEMY_CONTACT_DAMAGE)
                damage = damage * (1 - player.damage_reduction)

                player.take_damage(damage)
                player.last_hit_time = current_time

                # 피격 효과
                sound_manager.play_sfx("player_hit")
                took_damage = True

        return took_damage

    def process_player_gem_collision(
        self,
        player: Player,
        gems: List,
        sound_manager,
        game_data: dict,
    ) -> Tuple[int, int]:
        """
        플레이어-젬 충돌 처리

        Args:
            player: 플레이어
            gems: 젬 리스트
            sound_manager: 사운드 매니저
            game_data: 게임 데이터

        Returns:
            (획득한 코인, 획득한 경험치) 튜플
        """
        coins_collected = 0
        exp_collected = 0

        for gem in gems[:]:
            if not gem.is_alive:
                continue

            # 자석 효과 (코인 마그넷)
            magnet_range = config.GEM_MAGNET_RANGE
            if player.has_coin_magnet:
                magnet_range *= 2

            distance = player.pos.distance_to(gem.pos)

            # 자석 범위 내면 플레이어 방향으로 이동
            if distance < magnet_range:
                direction = (player.pos - gem.pos).normalize()
                gem.pos += direction * config.GEM_MAGNET_SPEED * 0.016  # 60fps 기준

            # 수집 범위
            if distance < player.hitbox.width / 2 + gem.hitbox.width / 2:
                if isinstance(gem, CoinGem):
                    # 코인 획득
                    value = int(gem.value * player.coin_drop_multiplier)
                    game_data['score'] = game_data.get('score', 0) + value
                    game_data['uncollected_score'] = game_data.get('uncollected_score', 0) + value
                    coins_collected += value
                    sound_manager.play_sfx("coin_pickup")

                elif isinstance(gem, HealItem):
                    # 힐 아이템 획득
                    heal_amount = gem.heal_amount
                    player.hp = min(player.hp + heal_amount, player.max_hp)
                    sound_manager.play_sfx("heal_pickup")

                gem.is_alive = False
                gems.remove(gem)

        return coins_collected, exp_collected

    def _calculate_damage(self, bullet: Bullet, enemy: Enemy) -> float:
        """
        데미지 계산

        Args:
            bullet: 총알
            enemy: 적

        Returns:
            최종 데미지
        """
        base_damage = bullet.damage

        # 크리티컬 체크
        is_crit = getattr(bullet, 'is_crit', False)
        if is_crit:
            base_damage *= config.CRIT_DAMAGE_MULTIPLIER

        # 적 방어력 적용
        defense = getattr(enemy, 'defense', 0)
        final_damage = max(1, base_damage - defense)

        return final_damage

    def _spawn_drop(
        self,
        enemy: Enemy,
        gems: List,
        screen_size: Tuple[int, int],
        game_data: dict,
    ):
        """
        처치 시 드롭 아이템 생성

        Args:
            enemy: 처치된 적
            gems: 젬 리스트
            screen_size: 화면 크기
            game_data: 게임 데이터
        """
        import random

        # 코인 드롭
        coin_count = getattr(enemy, 'coin_drop', 1)
        if hasattr(enemy, 'is_boss') and enemy.is_boss:
            coin_count = config.BOSS_COIN_DROP

        for _ in range(coin_count):
            offset = pygame.math.Vector2(
                random.uniform(-20, 20),
                random.uniform(-20, 20)
            )
            coin = CoinGem(
                pos=enemy.pos + offset,
                screen_height=screen_size[1],
                value=getattr(enemy, 'coin_value', config.COIN_GEM_VALUE)
            )
            gems.append(coin)

        # 힐 아이템 드롭 (확률)
        heal_chance = config.HEAL_DROP_CHANCE
        if hasattr(enemy, 'is_boss') and enemy.is_boss:
            heal_chance = config.BOSS_HEAL_DROP_CHANCE

        if random.random() < heal_chance:
            heal_item = HealItem(
                pos=enemy.pos.copy(),
                screen_height=screen_size[1],
                heal_amount=config.HEAL_ITEM_AMOUNT
            )
            gems.append(heal_item)


print("INFO: combat_system.py loaded")
