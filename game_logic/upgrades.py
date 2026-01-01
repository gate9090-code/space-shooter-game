# game_logic/upgrades.py
"""
Upgrade and tactical systems.
Handles tactical upgrade generation, skill application, synergies, and ship abilities.
"""

import pygame
import random
import math
import config
from typing import Dict, List, Tuple
from entities.player import Player
from entities.enemies import Enemy
from entities.weapons import Bullet
from entities.collectibles import CoinGem, HealItem
from effects.combat_effects import AnimatedEffect


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
    from .game_state import handle_level_up

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
            from entities.support_units import Drone

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
