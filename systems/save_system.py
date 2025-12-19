# systems/save_system.py
"""
SaveSystem - 게임 진행 상황 저장/불러오기 시스템
웨이브 모드의 진행 상황을 저장하여 다음 로그인 시 이어서 플레이 가능
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime


class SaveSystem:
    """
    게임 저장 시스템

    저장 항목:
    - 현재 웨이브
    - 플레이어 스탯 (HP, 레벨 등)
    - 획득한 스킬들
    - 무기 업그레이드 상태
    - 점수
    - 영구 업그레이드
    - 캠페인 진행 상황 (ACT/Episode 해금, 함선, 업그레이드)
    """

    SAVE_VERSION = 2  # 저장 파일 버전 (호환성 관리용)

    def __init__(self, save_dir: str = "saves"):
        """
        저장 시스템 초기화

        Args:
            save_dir: 저장 파일 디렉토리
        """
        self.save_dir = Path(save_dir)
        self.save_dir.mkdir(exist_ok=True)
        self.wave_save_file = self.save_dir / "wave_progress.json"
        self.campaign_save_file = self.save_dir / "campaign_progress.json"

    def save_wave_progress(
        self,
        game_data: Dict[str, Any],
        player_data: Dict[str, Any],
        player_upgrades: Dict[str, int],
    ) -> bool:
        """
        웨이브 모드 진행 상황 저장

        Args:
            game_data: 게임 데이터 (웨이브, 점수 등)
            player_data: 플레이어 데이터 (스킬, 무기 등)
            player_upgrades: 영구 업그레이드 레벨

        Returns:
            저장 성공 여부
        """
        try:
            save_data = {
                "version": self.SAVE_VERSION,
                "saved_at": datetime.now().isoformat(),
                "game_data": {
                    "current_wave": game_data.get("current_wave", 1),
                    "score": game_data.get("score", 0),
                    "player_level": game_data.get("player_level", 1),
                    "kill_count": game_data.get("kill_count", 0),
                },
                "player_data": player_data,
                "player_upgrades": player_upgrades,
            }

            with open(self.wave_save_file, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, indent=2, ensure_ascii=False)

            print(f"INFO: Wave progress saved - Wave {game_data.get('current_wave', 1)}")
            return True

        except Exception as e:
            print(f"ERROR: Failed to save wave progress: {e}")
            return False

    def load_wave_progress(self) -> Optional[Dict[str, Any]]:
        """
        웨이브 모드 진행 상황 불러오기

        Returns:
            저장된 데이터 또는 None
        """
        try:
            if not self.wave_save_file.exists():
                print("INFO: No wave save file found")
                return None

            with open(self.wave_save_file, 'r', encoding='utf-8') as f:
                save_data = json.load(f)

            # 버전 체크
            if save_data.get("version") != self.SAVE_VERSION:
                print(f"WARNING: Save version mismatch (file: {save_data.get('version')}, current: {self.SAVE_VERSION})")
                # 현재는 버전 1만 있으므로 그냥 로드

            print(f"INFO: Wave progress loaded - Wave {save_data['game_data']['current_wave']}")
            return save_data

        except json.JSONDecodeError as e:
            print(f"ERROR: Corrupted save file: {e}")
            return None
        except Exception as e:
            print(f"ERROR: Failed to load wave progress: {e}")
            return None

    def has_wave_save(self) -> bool:
        """저장된 웨이브 진행이 있는지 확인"""
        return self.wave_save_file.exists()

    def get_save_info(self) -> Optional[Dict[str, Any]]:
        """
        저장 파일 요약 정보 (메뉴 표시용)

        Returns:
            저장 정보 요약 또는 None
        """
        save_data = self.load_wave_progress()
        if not save_data:
            return None

        return {
            "wave": save_data["game_data"]["current_wave"],
            "score": save_data["game_data"]["score"],
            "level": save_data["game_data"]["player_level"],
            "saved_at": save_data.get("saved_at", "Unknown"),
        }

    def delete_wave_save(self) -> bool:
        """웨이브 저장 파일 삭제"""
        try:
            if self.wave_save_file.exists():
                self.wave_save_file.unlink()
                print("INFO: Wave save file deleted")
            return True
        except Exception as e:
            print(f"ERROR: Failed to delete wave save: {e}")
            return False

    # ==================== 캠페인 저장/로드 ====================

    def save_campaign_progress(
        self,
        global_score: int,
        current_ship: str,
        unlocked_ships: list,
        player_upgrades: Dict[str, Any],
        completed_episodes: Dict[str, list],
        current_act: int = 1,
    ) -> bool:
        """
        캠페인 진행 상황 저장

        Args:
            global_score: 누적 점수 (크레딧)
            current_ship: 현재 선택된 함선
            unlocked_ships: 해금된 함선 목록
            player_upgrades: Workshop 업그레이드 상태
            completed_episodes: 완료된 에피소드 {act_id: [episode_ids]}
            current_act: 현재 진행 중인 ACT

        Returns:
            저장 성공 여부
        """
        try:
            save_data = {
                "version": self.SAVE_VERSION,
                "saved_at": datetime.now().isoformat(),
                "campaign": {
                    "global_score": global_score,
                    "current_ship": current_ship,
                    "unlocked_ships": unlocked_ships,
                    "player_upgrades": player_upgrades,
                    "completed_episodes": completed_episodes,
                    "current_act": current_act,
                }
            }

            with open(self.campaign_save_file, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, indent=2, ensure_ascii=False)

            print(f"INFO: Campaign progress saved - Score: {global_score}, ACT: {current_act}")
            return True

        except Exception as e:
            print(f"ERROR: Failed to save campaign progress: {e}")
            return False

    def load_campaign_progress(self) -> Optional[Dict[str, Any]]:
        """
        캠페인 진행 상황 불러오기

        Returns:
            저장된 캠페인 데이터 또는 None
        """
        try:
            if not self.campaign_save_file.exists():
                print("INFO: No campaign save file found")
                return None

            with open(self.campaign_save_file, 'r', encoding='utf-8') as f:
                save_data = json.load(f)

            # 버전 체크
            if save_data.get("version", 1) < self.SAVE_VERSION:
                print(f"WARNING: Campaign save version mismatch, migrating...")
                save_data = self._migrate_campaign_save(save_data)

            print(f"INFO: Campaign progress loaded - Score: {save_data['campaign']['global_score']}")
            return save_data.get("campaign", {})

        except json.JSONDecodeError as e:
            print(f"ERROR: Corrupted campaign save file: {e}")
            return None
        except Exception as e:
            print(f"ERROR: Failed to load campaign progress: {e}")
            return None

    def _migrate_campaign_save(self, old_data: Dict[str, Any]) -> Dict[str, Any]:
        """이전 버전 저장 파일 마이그레이션"""
        # 버전 1에서 2로 마이그레이션 (필요시 추가)
        old_data["version"] = self.SAVE_VERSION
        return old_data

    def has_campaign_save(self) -> bool:
        """저장된 캠페인 진행이 있는지 확인"""
        return self.campaign_save_file.exists()

    def get_campaign_info(self) -> Optional[Dict[str, Any]]:
        """
        캠페인 저장 파일 요약 정보 (메뉴 표시용)

        Returns:
            저장 정보 요약 또는 None
        """
        campaign_data = self.load_campaign_progress()
        if not campaign_data:
            return None

        # 완료된 에피소드 수 계산
        completed_count = sum(
            len(eps) for eps in campaign_data.get("completed_episodes", {}).values()
        )

        return {
            "global_score": campaign_data.get("global_score", 0),
            "current_ship": campaign_data.get("current_ship", "FIGHTER"),
            "current_act": campaign_data.get("current_act", 1),
            "completed_episodes": completed_count,
            "unlocked_ships_count": len(campaign_data.get("unlocked_ships", ["FIGHTER"])),
        }

    def delete_campaign_save(self) -> bool:
        """캠페인 저장 파일 삭제"""
        try:
            if self.campaign_save_file.exists():
                self.campaign_save_file.unlink()
                print("INFO: Campaign save file deleted")
            return True
        except Exception as e:
            print(f"ERROR: Failed to delete campaign save: {e}")
            return False

    def get_default_campaign_data(self) -> Dict[str, Any]:
        """기본 캠페인 데이터 반환 (새 게임용)"""
        import config
        return {
            "global_score": getattr(config, 'INITIAL_CAMPAIGN_CREDITS', 500),
            "current_ship": "FIGHTER",
            "unlocked_ships": ["FIGHTER"],
            "player_upgrades": {},
            "completed_episodes": {},
            "current_act": 1,
        }


def extract_player_save_data(player) -> Dict[str, Any]:
    """
    Player 객체에서 저장할 데이터 추출

    Args:
        player: Player 인스턴스

    Returns:
        저장 가능한 딕셔너리 형태의 플레이어 데이터
    """
    return {
        # 기본 스탯
        "hp": player.hp,
        "max_hp": player.max_hp,
        "speed": player.speed,

        # 무기 스탯
        "weapon": {
            "damage": player.weapon.damage,
            "cooldown": player.weapon.cooldown,
            "bullet_count": player.weapon.bullet_count,
            "spread_angle": player.weapon.spread_angle,
        },

        # 전투 속성
        "is_piercing": player.is_piercing,
        "has_explosive": player.has_explosive,
        "explosive_radius": player.explosive_radius,
        "has_chain_explosion": player.has_chain_explosion,
        "has_lightning": player.has_lightning,
        "lightning_chain_count": player.lightning_chain_count,
        "has_static_field": player.has_static_field,
        "has_frost": player.has_frost,
        "frost_slow_ratio": player.frost_slow_ratio,
        "has_deep_freeze": player.has_deep_freeze,
        "freeze_chance": player.freeze_chance,

        # 방어 속성
        "damage_reduction": player.damage_reduction,
        "regeneration_rate": player.regeneration_rate,

        # 유틸리티 속성
        "coin_drop_multiplier": player.coin_drop_multiplier,
        "exp_multiplier": player.exp_multiplier,
        "has_coin_magnet": player.has_coin_magnet,

        # 지원 유닛
        "turret_count": player.turret_count,
        "drone_count": player.drone_count,

        # 획득한 스킬
        "acquired_skills": dict(player.acquired_skills),
        "active_synergies": list(player.active_synergies),

        # 고급 스킬 속성
        "execute_threshold": player.execute_threshold,
        "has_phoenix": player.has_phoenix,
        "has_berserker": player.has_berserker,
        "has_starfall": player.has_starfall,
        "has_arcane_mastery": player.has_arcane_mastery,
        "second_chance_rate": player.second_chance_rate,
    }


def apply_player_save_data(player, save_data: Dict[str, Any]):
    """
    저장된 데이터를 Player 객체에 적용

    Args:
        player: Player 인스턴스
        save_data: 저장된 플레이어 데이터
    """
    # 기본 스탯
    player.hp = save_data.get("hp", player.hp)
    player.max_hp = save_data.get("max_hp", player.max_hp)
    player.speed = save_data.get("speed", player.speed)

    # 무기 스탯
    weapon_data = save_data.get("weapon", {})
    if weapon_data:
        player.weapon.damage = weapon_data.get("damage", player.weapon.damage)
        player.weapon.cooldown = weapon_data.get("cooldown", player.weapon.cooldown)
        player.weapon.bullet_count = weapon_data.get("bullet_count", player.weapon.bullet_count)
        player.weapon.spread_angle = weapon_data.get("spread_angle", player.weapon.spread_angle)

    # 전투 속성
    player.is_piercing = save_data.get("is_piercing", False)
    player.has_explosive = save_data.get("has_explosive", False)
    player.explosive_radius = save_data.get("explosive_radius", 100.0)
    player.has_chain_explosion = save_data.get("has_chain_explosion", False)
    player.has_lightning = save_data.get("has_lightning", False)
    player.lightning_chain_count = save_data.get("lightning_chain_count", 0)
    player.has_static_field = save_data.get("has_static_field", False)
    player.has_frost = save_data.get("has_frost", False)
    player.frost_slow_ratio = save_data.get("frost_slow_ratio", 0.0)
    player.has_deep_freeze = save_data.get("has_deep_freeze", False)
    player.freeze_chance = save_data.get("freeze_chance", 0.0)

    # 방어 속성
    player.damage_reduction = save_data.get("damage_reduction", 0.0)
    player.regeneration_rate = save_data.get("regeneration_rate", 0.0)

    # 유틸리티 속성
    player.coin_drop_multiplier = save_data.get("coin_drop_multiplier", 1.0)
    player.exp_multiplier = save_data.get("exp_multiplier", 1.0)
    player.has_coin_magnet = save_data.get("has_coin_magnet", False)

    # 지원 유닛
    player.turret_count = save_data.get("turret_count", 0)
    player.drone_count = save_data.get("drone_count", 0)

    # 획득한 스킬
    player.acquired_skills = dict(save_data.get("acquired_skills", {}))
    player.active_synergies = list(save_data.get("active_synergies", []))

    # 고급 스킬 속성
    player.execute_threshold = save_data.get("execute_threshold", 0.0)
    player.has_phoenix = save_data.get("has_phoenix", False)
    player.has_berserker = save_data.get("has_berserker", False)
    player.has_starfall = save_data.get("has_starfall", False)
    player.has_arcane_mastery = save_data.get("has_arcane_mastery", False)
    player.second_chance_rate = save_data.get("second_chance_rate", 0.0)

    print(f"INFO: Player data loaded - HP: {player.hp}/{player.max_hp}, Skills: {len(player.acquired_skills)}")


# 전역 인스턴스
_save_system: Optional[SaveSystem] = None


def get_save_system() -> SaveSystem:
    """전역 저장 시스템 인스턴스 반환"""
    global _save_system
    if _save_system is None:
        _save_system = SaveSystem()
    return _save_system


print("INFO: save_system.py loaded")
