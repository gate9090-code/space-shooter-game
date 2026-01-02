"""
에피소드 리소스 로더 시스템

에피소드별로 모든 리소스(대화, 배경, 음향, 컷씬 이미지)를 통합 관리합니다.

폴더 구조:
assets/data/episodes/
├── ep1/
│   ├── ep1.json           # 메타데이터 + 모든 장면
│   ├── backgrounds/       # 배경 이미지
│   ├── audio/bgm/         # 배경 음악
│   ├── audio/sfx/         # 효과음
│   ├── cutscene_images/   # 컷씬 이미지 (메모리, 문서, 조각, 홀로그램 등)
│   └── portraits/         # 캐릭터 초상화
├── ep2/
│   └── ...
└── shared/                # 공용 리소스
    ├── portraits/
    ├── audio/
    └── backgrounds/
"""

import json
from pathlib import Path
from typing import Optional, Dict, Any, List


class EpisodeResourceLoader:
    """에피소드별 리소스 통합 로더"""

    # 빈 에피소드 데이터 (Graceful 처리용)
    EMPTY_EPISODE = {
        "id": "",
        "title": "",
        "scenes": {},
        "segments": [],
        "defaults": {}
    }

    # 빈 장면 데이터
    EMPTY_SCENE = {
        "dialogues": [],
        "background": "",
        "bgm": "",
        "title": "",
        "location": ""
    }

    def __init__(self, base_path: Path | str):
        """
        Args:
            base_path: episodes 폴더 경로 (예: assets/episodes)
        """
        self.base_path = Path(base_path)
        self.shared_path = self.base_path / "shared"
        self.current_episode_id: str = ""
        self.current_episode_data: dict = {}
        self.cache: Dict[str, dict] = {}

    def set_episode(self, episode_id: str) -> bool:
        """
        현재 에피소드 설정 및 로드

        Args:
            episode_id: 에피소드 ID (예: "ep1")

        Returns:
            성공 여부 (실패해도 에러 없음)
        """
        self.current_episode_id = episode_id
        self.current_episode_data = self._load_episode(episode_id)
        return bool(self.current_episode_data.get("id"))

    def _load_episode(self, episode_id: str) -> dict:
        """에피소드 JSON 로드 (Graceful 처리)"""
        if not episode_id:
            return self.EMPTY_EPISODE.copy()

        # 캐시 확인
        if episode_id in self.cache:
            return self.cache[episode_id]

        # JSON 파일 경로
        json_path = self.base_path / episode_id / f"{episode_id}.json"

        if not json_path.exists():
            print(f"INFO: Episode '{episode_id}' not found at {json_path}")
            return self.EMPTY_EPISODE.copy()

        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 필수 필드 보장
            if "scenes" not in data:
                data["scenes"] = {}
            if "segments" not in data:
                data["segments"] = []
            if "defaults" not in data:
                data["defaults"] = {}

            # 캐시 저장
            self.cache[episode_id] = data
            print(f"INFO: Episode loaded: {episode_id} ({len(data.get('scenes', {}))} scenes)")
            return data

        except json.JSONDecodeError as e:
            print(f"WARNING: Invalid JSON in episode '{episode_id}': {e}")
            return self.EMPTY_EPISODE.copy()
        except Exception as e:
            print(f"WARNING: Failed to load episode '{episode_id}': {e}")
            return self.EMPTY_EPISODE.copy()

    # === 에피소드 폴더 경로 ===

    def get_episode_path(self, episode_id: str = None) -> Path:
        """에피소드 폴더 경로"""
        ep_id = episode_id or self.current_episode_id
        return self.base_path / ep_id

    # === 리소스 경로 해석 (에피소드 우선, shared 폴백) ===

    def resolve_path(self, resource_type: str, filename: str, episode_id: str = None) -> Optional[Path]:
        """
        리소스 경로 해석 (에피소드 폴더 우선, shared 폴백)

        Args:
            resource_type: "backgrounds", "portraits", "audio/bgm", "audio/sfx", "cutscene_images"
            filename: 파일명 (예: "bg_ruins.jpg")
            episode_id: 에피소드 ID (None이면 현재 에피소드)

        Returns:
            실제 파일 경로 또는 None
        """
        if not filename:
            return None

        ep_id = episode_id or self.current_episode_id

        # 1순위: 에피소드 폴더
        if ep_id:
            ep_path = self.get_episode_path(ep_id) / resource_type / filename
            if ep_path.exists():
                return ep_path

        # 2순위: shared 폴더
        shared_path = self.shared_path / resource_type / filename
        if shared_path.exists():
            return shared_path

        return None

    # === 리소스 타입별 헬퍼 ===

    def get_background(self, filename: str, episode_id: str = None) -> Optional[Path]:
        """배경 이미지 경로"""
        return self.resolve_path("backgrounds", filename, episode_id)

    def get_portrait(self, filename: str, episode_id: str = None) -> Optional[Path]:
        """캐릭터 포트레이트 경로"""
        return self.resolve_path("portraits", filename, episode_id)

    def get_bgm(self, filename: str, episode_id: str = None) -> Optional[Path]:
        """배경 음악 경로"""
        return self.resolve_path("audio/bgm", filename, episode_id)

    def get_sfx(self, filename: str, episode_id: str = None) -> Optional[Path]:
        """효과음 경로"""
        return self.resolve_path("audio/sfx", filename, episode_id)

    def get_effect(self, filename: str, episode_id: str = None) -> Optional[Path]:
        """컷씬 이미지 경로 (구 'effects', 현 'cutscene_images')"""
        return self.resolve_path("cutscene_images", filename, episode_id)

    # === 장면 데이터 접근 ===

    def get_scene(self, scene_name: str) -> dict:
        """
        장면 데이터 반환 (Graceful 처리)

        Args:
            scene_name: 장면 이름 (예: "opening", "mid_01", "ending")

        Returns:
            장면 데이터 딕셔너리 (없으면 빈 데이터)
        """
        if not self.current_episode_data:
            return self.EMPTY_SCENE.copy()

        scenes = self.current_episode_data.get("scenes", {})
        scene = scenes.get(scene_name, {})

        if not scene:
            print(f"INFO: Scene '{scene_name}' not found in episode '{self.current_episode_id}'")
            return self.EMPTY_SCENE.copy()

        # 필수 필드 보장
        if "dialogues" not in scene:
            scene["dialogues"] = []

        return scene

    def get_dialogues(self, scene_name: str) -> List[dict]:
        """장면의 대화 목록 반환"""
        scene = self.get_scene(scene_name)
        return scene.get("dialogues", [])

    def get_scene_background(self, scene_name: str) -> str:
        """장면의 기본 배경 파일명 반환"""
        scene = self.get_scene(scene_name)
        bg = scene.get("background", "")

        # 장면에 배경이 없으면 에피소드 기본값 사용
        if not bg:
            defaults = self.current_episode_data.get("defaults", {})
            bg = defaults.get("background", "")

        return bg

    def get_scene_bgm(self, scene_name: str) -> str:
        """장면의 배경 음악 파일명 반환"""
        scene = self.get_scene(scene_name)
        bgm = scene.get("bgm", "")

        # 장면에 BGM이 없으면 에피소드 기본값 사용
        if not bgm:
            defaults = self.current_episode_data.get("defaults", {})
            bgm = defaults.get("bgm", "")

        return bgm

    # === 세그먼트 접근 ===

    def get_segments(self) -> List[dict]:
        """에피소드의 세그먼트 목록 반환"""
        return self.current_episode_data.get("segments", [])

    def get_segment(self, index: int) -> Optional[dict]:
        """특정 인덱스의 세그먼트 반환"""
        segments = self.get_segments()
        if 0 <= index < len(segments):
            return segments[index]
        return None

    # === 에피소드 메타데이터 ===

    def get_title(self) -> str:
        """에피소드 제목"""
        return self.current_episode_data.get("title", "")

    def get_title_en(self) -> str:
        """에피소드 영문 제목"""
        return self.current_episode_data.get("title_en", "")

    def get_description(self) -> str:
        """에피소드 설명"""
        return self.current_episode_data.get("description", "")

    def get_defaults(self) -> dict:
        """에피소드 기본값"""
        return self.current_episode_data.get("defaults", {})

    # === 효과 데이터 ===

    def get_scene_effect(self, scene_name: str) -> str:
        """장면의 효과 타입 반환"""
        scene = self.get_scene(scene_name)
        return scene.get("effect", "")

    def get_scene_effect_data(self, scene_name: str) -> dict:
        """장면의 효과 데이터 반환"""
        scene = self.get_scene(scene_name)
        return scene.get("effect_data", {})

    # === 에피소드 목록 ===

    def list_episodes(self) -> List[str]:
        """사용 가능한 에피소드 ID 목록"""
        episodes = []

        if not self.base_path.exists():
            return episodes

        for folder in self.base_path.iterdir():
            if folder.is_dir() and folder.name.startswith("ep"):
                json_file = folder / f"{folder.name}.json"
                if json_file.exists():
                    episodes.append(folder.name)

        return sorted(episodes)

    # === 캐시 관리 ===

    def clear_cache(self):
        """캐시 초기화"""
        self.cache.clear()

    def reload_episode(self, episode_id: str = None):
        """에피소드 다시 로드"""
        ep_id = episode_id or self.current_episode_id
        if ep_id in self.cache:
            del self.cache[ep_id]

        if ep_id == self.current_episode_id:
            self.current_episode_data = self._load_episode(ep_id)


# === 전역 로더 인스턴스 ===

_global_episode_loader: Optional[EpisodeResourceLoader] = None


def get_episode_loader(base_path: Path | str = None) -> EpisodeResourceLoader:
    """
    전역 에피소드 로더 인스턴스 반환 (싱글톤)

    Args:
        base_path: episodes 폴더 경로 (최초 호출 시 필요)
    """
    global _global_episode_loader

    if _global_episode_loader is None:
        if base_path is None:
            import config
            base_path = config.ASSET_DIR / "data" / "episodes"
        _global_episode_loader = EpisodeResourceLoader(base_path)

    return _global_episode_loader


print("INFO: episode_resource_loader.py loaded")
