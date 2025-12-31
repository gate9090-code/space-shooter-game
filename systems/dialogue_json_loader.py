"""
Dialogue JSON Loader
대화 데이터를 JSON 파일에서 로드
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional


class DialogueJSONLoader:
    """JSON 대화 파일 로더"""

    def __init__(self):
        self.dialogues_dir = Path("assets/data/dialogues")
        self._cache = {}

    def _load_json(self, filepath: Path) -> Dict:
        """JSON 파일 로드 (캐싱)"""
        filepath_str = str(filepath)

        if filepath_str in self._cache:
            return self._cache[filepath_str]

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self._cache[filepath_str] = data
                return data
        except Exception as e:
            print(f"WARNING: Failed to load {filepath}: {e}")
            return {}

    # =========================================================
    # Combat Dialogues
    # =========================================================

    def get_combat_message(self, key: str) -> str:
        """전투 메시지 반환"""
        filepath = self.dialogues_dir / "combat" / "combat_messages.json"
        data = self._load_json(filepath)

        msg_data = data.get(key, {})
        return msg_data.get("message", "")

    def get_boss_phase_dialogue(self, boss_id: str, phase: str) -> str:
        """보스 페이즈 대화 반환"""
        filepath = self.dialogues_dir / "combat" / "boss_phases.json"
        data = self._load_json(filepath)

        boss_phases = data.get(boss_id, {})
        return boss_phases.get(phase, "")

    # =========================================================
    # Boss Dialogues
    # =========================================================

    def get_boss_dialogue(self, boss_id: int, phase: str = "intro") -> List[Dict]:
        """보스 대화 반환 (intro 또는 defeat)"""
        filepath = self.dialogues_dir / "bosses" / "boss_dialogues.json"
        data = self._load_json(filepath)

        boss_key = f"boss_{boss_id}"
        boss_data = data.get(boss_key, {})
        return boss_data.get(phase, [])

    # =========================================================
    # Reflection Dialogues
    # =========================================================

    def get_earth_beauty_scene(self, scene_key: str) -> Dict:
        """지구 회상 씬 반환"""
        filepath = self.dialogues_dir / "reflection" / "earth_beauty.json"
        data = self._load_json(filepath)
        return data.get(scene_key, {})

    def get_philosophy_scene(self, scene_key: str) -> Dict:
        """철학 씬 반환"""
        filepath = self.dialogues_dir / "reflection" / "philosophy.json"
        data = self._load_json(filepath)
        return data.get(scene_key, {})

    def get_andromeda_scene(self, scene_key: str) -> Dict:
        """안드로메다 씬 반환"""
        filepath = self.dialogues_dir / "reflection" / "andromeda.json"
        data = self._load_json(filepath)
        return data.get(scene_key, {})

    # =========================================================
    # Convenience Methods
    # =========================================================

    def get_all_combat_messages(self) -> Dict[str, str]:
        """모든 전투 메시지 반환"""
        filepath = self.dialogues_dir / "combat" / "combat_messages.json"
        data = self._load_json(filepath)

        return {key: msg_data.get("message", "") for key, msg_data in data.items()}


# 싱글톤 인스턴스
_dialogue_json_loader = None


def get_dialogue_json_loader() -> DialogueJSONLoader:
    """DialogueJSONLoader 싱글톤 인스턴스 반환"""
    global _dialogue_json_loader
    if _dialogue_json_loader is None:
        _dialogue_json_loader = DialogueJSONLoader()
    return _dialogue_json_loader


# 편의 함수들 (하위 호환성)
def get_boss_dialogue(boss_id: int, phase: str = "intro") -> List[Dict]:
    """보스 대화 반환"""
    return get_dialogue_json_loader().get_boss_dialogue(boss_id, phase)


def get_combat_message(key: str) -> str:
    """전투 메시지 반환"""
    return get_dialogue_json_loader().get_combat_message(key)


def get_boss_phase_dialogue(boss_id: str, phase: str) -> str:
    """보스 페이즈 대화 반환"""
    return get_dialogue_json_loader().get_boss_phase_dialogue(boss_id, phase)


print("INFO: dialogue_json_loader.py loaded")
