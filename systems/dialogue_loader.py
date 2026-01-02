# systems/dialogue_loader.py
"""
DialogueLoader - JSON 기반 대화 스크립트 로더

대화와 배경 이미지를 쉽게 편집할 수 있도록 JSON 파일에서 로드합니다.

사용법:
    loader = DialogueLoader(Path("assets/data/episodes/ep1/scripts"))
    scene = loader.load_scene("act1_opening")
    dialogues = scene.get("dialogues", [])
    background = scene.get("background")
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any


class DialogueLoader:
    """JSON 기반 대화 스크립트 로더"""

    def __init__(self, scripts_path: Path | str):
        """
        Args:
            scripts_path: JSON 스크립트 파일들이 있는 폴더 경로
        """
        self.scripts_path = Path(scripts_path)
        self.cache: Dict[str, dict] = {}

    # 빈 씬 데이터 (Graceful 처리용)
    EMPTY_SCENE = {"dialogues": [], "background": "", "title": "", "location": ""}

    def load_scene(self, scene_id: str) -> dict:
        """
        장면 데이터 로드 (캐싱 지원, Graceful 처리)

        Args:
            scene_id: 장면 ID (예: "act1_opening", "act1_m1")

        Returns:
            장면 데이터 딕셔너리 (절대 None 반환 안 함, 에러 시 빈 데이터 반환)
        """
        # scene_id가 없거나 빈 문자열이면 빈 데이터 반환
        if not scene_id:
            return self.EMPTY_SCENE.copy()

        # 캐시 확인
        if scene_id in self.cache:
            return self.cache[scene_id]

        # JSON 파일 탐색
        json_path = self.scripts_path / f"{scene_id}.json"
        if not json_path.exists():
            print(f"INFO: Scene '{scene_id}' not found, skipping (no error)")
            return self.EMPTY_SCENE.copy()

        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # dialogues 필드 보장
            if "dialogues" not in data:
                data["dialogues"] = []

            # 캐시에 저장
            self.cache[scene_id] = data
            print(f"INFO: Loaded scene from JSON: {scene_id}")
            return data

        except json.JSONDecodeError as e:
            print(f"WARNING: Invalid JSON in '{scene_id}': {e} (returning empty)")
            return self.EMPTY_SCENE.copy()
        except Exception as e:
            print(f"WARNING: Failed to load '{scene_id}': {e} (returning empty)")
            return self.EMPTY_SCENE.copy()

    def get_scene_data(self, scene_id: str) -> Optional[dict]:
        """load_scene의 별칭"""
        return self.load_scene(scene_id)

    def get_background(self, scene_id: str) -> Optional[str]:
        """
        배경 이미지 파일명 반환

        Args:
            scene_id: 장면 ID

        Returns:
            배경 이미지 파일명 (예: "bg_ruins.jpg") 또는 None
        """
        scene = self.load_scene(scene_id)
        return scene.get("background") if scene else None

    def get_dialogues(self, scene_id: str) -> List[dict]:
        """
        대화 리스트 반환

        Args:
            scene_id: 장면 ID

        Returns:
            대화 딕셔너리 리스트 [{"speaker": "...", "text": "..."}, ...]
        """
        scene = self.load_scene(scene_id)
        return scene.get("dialogues", []) if scene else []

    def get_title(self, scene_id: str) -> Optional[str]:
        """장면 타이틀 반환"""
        scene = self.load_scene(scene_id)
        return scene.get("title") if scene else None

    def get_location(self, scene_id: str) -> Optional[str]:
        """장면 위치 반환"""
        scene = self.load_scene(scene_id)
        return scene.get("location") if scene else None

    def list_scenes(self) -> List[str]:
        """
        사용 가능한 모든 장면 ID 목록

        Returns:
            장면 ID 리스트 (JSON 파일명에서 .json 제외)
        """
        if not self.scripts_path.exists():
            return []
        return sorted([f.stem for f in self.scripts_path.glob("*.json")])

    def reload_scene(self, scene_id: str) -> Optional[dict]:
        """
        캐시를 무시하고 장면 다시 로드

        Args:
            scene_id: 장면 ID

        Returns:
            장면 데이터 딕셔너리 또는 None
        """
        # 캐시에서 제거
        if scene_id in self.cache:
            del self.cache[scene_id]
        return self.load_scene(scene_id)

    def clear_cache(self):
        """모든 캐시 삭제"""
        self.cache.clear()

    def scene_exists(self, scene_id: str) -> bool:
        """
        장면 파일이 존재하는지 확인

        Args:
            scene_id: 장면 ID

        Returns:
            True if exists, False otherwise
        """
        json_path = self.scripts_path / f"{scene_id}.json"
        return json_path.exists()


# 전역 로더 인스턴스 (선택적 사용)
_global_loader: Optional[DialogueLoader] = None


def get_dialogue_loader(scripts_path: Path | str | None = None) -> DialogueLoader:
    """
    전역 DialogueLoader 인스턴스 반환

    Args:
        scripts_path: 스크립트 경로 (첫 호출 시에만 사용)

    Returns:
        DialogueLoader 인스턴스
    """
    global _global_loader

    if _global_loader is None:
        if scripts_path is None:
            # 기본 경로 사용 (에피소드 시스템)
            import config
            scripts_path = config.ASSET_DIR / "data" / "episodes" / "ep1" / "scripts"
        _global_loader = DialogueLoader(scripts_path)

    return _global_loader


print("INFO: dialogue_loader.py loaded")
