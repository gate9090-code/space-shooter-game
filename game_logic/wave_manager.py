# game_logic/wave_manager.py
"""
Wave management functions.
Handles wave progression, wave clearing, and wave-specific logic.
"""

import pygame
import random
import config
from typing import Dict, List, Tuple
from entities.player import Player
from entities.enemies import Enemy, Boss
from entities.weapons import Bullet
from entities.collectibles import CoinGem, HealItem
from effects.combat_effects import AnimatedEffect, DamageNumber, DamageNumberManager


def start_wave(game_data: Dict, current_time: float, enemies: List = None):
    """웨이브를 시작합니다. 이전 웨이브의 적들을 제거합니다."""
    from .events import try_trigger_random_event

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
    from .helpers import (
        create_hit_particles, create_boss_hit_particles, create_explosion_particles,
        create_shockwave, trigger_screen_shake, create_time_slow_effect, create_dynamic_text
    )

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
                    from effects.screen_effects import LightningEffect
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
                        from effects.screen_effects import Shockwave
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
                        from effects.game_animations import StaticField
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

            # 다중 파동 효과 생성 (ImageShockwave 사용)
            settings = config.SHOCKWAVE_SETTINGS["BULLET_HIT"]
            wave_count = settings.get("wave_count", 3)
            wave_interval = settings.get("wave_interval", 0.1)

            for i in range(wave_count):
                # 각 파동마다 약간의 지연을 가진 이미지 기반 충격파 생성
                from effects.screen_effects import ImageShockwave
                shockwave = ImageShockwave(
                    center=(impact_pos.x, impact_pos.y),
                    max_size=settings.get("max_radius", 120) * 2,  # 이미지는 지름이므로 반경*2
                    duration=settings.get("duration", 0.8),
                    delay=i * wave_interval,
                    color_tint=settings.get("color", (255, 255, 255)),
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
    from effects.combat_effects import AnimatedEffect
    for effect in effects:
        if isinstance(effect, AnimatedEffect):
            effect.draw(screen)
