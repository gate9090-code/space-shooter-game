"""
VFX Manager - 이미지 기반 효과 관리 시스템

JSON 설정 파일을 읽어서 다양한 VFX 효과를 자동으로 관리합니다.
이미지만 교체하면 코드 수정 없이 새로운 효과를 만들 수 있습니다.
"""

import json
import pygame
from pathlib import Path
from typing import Dict, Any, Optional, Tuple


class VFXManager:
    """
    VFX 효과 관리자 - 싱글톤 패턴

    기능:
    - JSON 설정 파일에서 효과 정의 자동 로드
    - 이미지 캐싱으로 메모리 효율적 관리
    - 코드 수정 없이 JSON만 편집해서 새 효과 추가
    """

    _instance = None

    def __new__(cls):
        """싱글톤 패턴 구현"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """초기화 (한 번만 실행)"""
        if self._initialized:
            return

        self._effects_config: Dict[str, Dict[str, Dict[str, Any]]] = {}
        self._image_cache: Dict[str, pygame.Surface] = {}
        self._initialized = True
        self._folder_mode = False  # 폴더 기반 모드 플래그

        # 설정 자동 로드
        self.load_config()

        # 폴더 기반 자동 스캔 시도
        self.load_from_folders()

    def load_config(self, config_path: Optional[str] = None):
        """
        JSON 설정 파일에서 효과 정의 로드

        Args:
            config_path: JSON 파일 경로 (기본: assets/config/vfx_effects.json)
        """
        if config_path is None:
            config_path = Path("assets/config/vfx_effects.json")
        else:
            config_path = Path(config_path)

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self._effects_config = json.load(f)

            # 주석 제거
            if "_comment" in self._effects_config:
                del self._effects_config["_comment"]

            print(f"INFO: VFXManager loaded config from {config_path}")
            print(f"INFO: Available effect categories: {list(self._effects_config.keys())}")

            # 모든 이미지 미리 로드 (게임 시작 시 한 번만)
            self._preload_images()

        except FileNotFoundError:
            print(f"WARNING: VFX config not found at {config_path}, using defaults")
            self._load_default_config()
        except json.JSONDecodeError as e:
            print(f"ERROR: Failed to parse VFX config: {e}")
            self._load_default_config()

    def _preload_images(self):
        """모든 효과에서 사용하는 이미지를 미리 로드"""
        loaded_count = 0

        for category, effects in self._effects_config.items():
            for effect_name, config in effects.items():
                image_path = config.get("image")

                if image_path and image_path not in self._image_cache:
                    try:
                        full_path = Path(image_path)
                        if full_path.exists():
                            self._image_cache[image_path] = pygame.image.load(str(full_path)).convert_alpha()
                            loaded_count += 1
                        else:
                            print(f"WARNING: VFX image not found: {image_path}")
                            # 폴백: 기본 링 이미지 사용
                            default_path = "assets/images/vfx/combat/purse_ring_effect.png"
                            if default_path not in self._image_cache:
                                self._image_cache[default_path] = pygame.image.load(default_path).convert_alpha()
                            self._image_cache[image_path] = self._image_cache[default_path]
                    except Exception as e:
                        print(f"ERROR: Failed to load VFX image {image_path}: {e}")

        print(f"INFO: VFXManager preloaded {loaded_count} unique images")

    def load_from_folders(self, base_folder: Optional[str] = None):
        """
        폴더 구조에서 이미지 자동 스캔 및 로드

        폴더 구조:
        assets/images/vfx/combat/
        ├── hit_effects/
        │   ├── ring_normal.png
        │   ├── ring_fire.png
        │   └── ring_ice.png
        ├── critical_effects/
        └── boss_effects/

        Args:
            base_folder: VFX 폴더 기본 경로 (기본: assets/images/vfx/combat)
        """
        if base_folder is None:
            base_folder = Path("assets/images/vfx/combat")
        else:
            base_folder = Path(base_folder)

        if not base_folder.exists():
            print(f"INFO: VFX folder not found at {base_folder}, skipping folder scan")
            return

        loaded_count = 0
        folder_effects = {}

        # 하위 폴더 스캔
        for category_folder in base_folder.iterdir():
            if not category_folder.is_dir():
                continue

            category_name = category_folder.name
            folder_effects[category_name] = {}

            # 폴더 내 이미지 파일 스캔
            for image_file in category_folder.glob("*.png"):
                variant_name = image_file.stem  # 파일명 (확장자 제외)

                # 이미지 로드
                try:
                    image = pygame.image.load(str(image_file)).convert_alpha()
                    self._image_cache[str(image_file)] = image

                    # 기본 설정으로 효과 생성
                    folder_effects[category_name][variant_name] = {
                        "image": str(image_file),
                        "max_size": 240,
                        "duration": 0.8,
                        "color_tint": [255, 255, 255],
                        "wave_count": 3,
                        "wave_interval": 0.1,
                        "source": "folder"  # 폴더에서 로드되었음을 표시
                    }

                    loaded_count += 1
                except Exception as e:
                    print(f"WARNING: Failed to load {image_file}: {e}")

        # JSON 설정과 폴더 스캔 결과 병합
        if folder_effects:
            print(f"INFO: VFXManager scanned folders and found {loaded_count} images")
            for category, variants in folder_effects.items():
                if category not in self._effects_config:
                    self._effects_config[category] = {}
                # 폴더 효과 추가 (JSON 설정 우선)
                for variant, config in variants.items():
                    if variant not in self._effects_config[category]:
                        self._effects_config[category][variant] = config
            self._folder_mode = True

    def _load_default_config(self):
        """기본 설정 로드 (JSON 파일이 없을 때)"""
        self._effects_config = {
            "hit_effects": {
                "normal": {
                    "image": "assets/images/vfx/combat/purse_ring_effect.png",
                    "max_size": 240,
                    "duration": 0.8,
                    "color_tint": [255, 255, 255],
                    "wave_count": 3,
                    "wave_interval": 0.1
                }
            }
        }
        print("INFO: VFXManager using default config")

    def get_effect_config(self, category: str, variant: str = "normal") -> Optional[Dict[str, Any]]:
        """
        효과 설정 가져오기

        Args:
            category: 효과 카테고리 (예: "hit_effects", "critical_effects")
            variant: 효과 변형 (예: "normal", "fire", "ice")

        Returns:
            효과 설정 딕셔너리 또는 None
        """
        if category not in self._effects_config:
            print(f"WARNING: VFX category '{category}' not found")
            return None

        if variant not in self._effects_config[category]:
            print(f"WARNING: VFX variant '{variant}' not found in '{category}'")
            # 폴백: 첫 번째 변형 사용
            first_variant = list(self._effects_config[category].keys())[0]
            return self._effects_config[category][first_variant]

        return self._effects_config[category][variant]

    def get_image(self, image_path: str) -> Optional[pygame.Surface]:
        """
        캐시된 이미지 가져오기

        Args:
            image_path: 이미지 파일 경로

        Returns:
            pygame.Surface 또는 None
        """
        return self._image_cache.get(image_path)

    def create_shockwave(
        self,
        center: Tuple[float, float],
        category: str = "hit_effects",
        variant: str = "normal"
    ):
        """
        설정 기반 충격파 효과 생성

        Args:
            center: 중심 위치 (x, y)
            category: 효과 카테고리
            variant: 효과 변형

        Returns:
            ImageShockwave 객체 또는 None
        """
        from effects.screen_effects import ImageShockwave

        config = self.get_effect_config(category, variant)
        if config is None:
            return None

        image = self.get_image(config["image"])
        if image is None:
            print(f"WARNING: Image not loaded for {category}/{variant}")
            return None

        # ImageShockwave 생성 (이미지 직접 전달)
        return ImageShockwave(
            center=center,
            max_size=config["max_size"],
            duration=config["duration"],
            delay=0.0,
            color_tint=tuple(config["color_tint"]),
            image_override=image  # 커스텀 이미지 전달
        )

    def create_multi_shockwave(
        self,
        center: Tuple[float, float],
        category: str = "hit_effects",
        variant: str = "normal"
    ) -> list:
        """
        다중 파동 충격파 생성 (설정의 wave_count 사용)

        Args:
            center: 중심 위치
            category: 효과 카테고리
            variant: 효과 변형

        Returns:
            ImageShockwave 객체 리스트
        """
        from effects.screen_effects import ImageShockwave

        config = self.get_effect_config(category, variant)
        if config is None:
            return []

        image = self.get_image(config["image"])
        if image is None:
            return []

        shockwaves = []
        wave_count = config.get("wave_count", 3)
        wave_interval = config.get("wave_interval", 0.1)

        for i in range(wave_count):
            shockwave = ImageShockwave(
                center=center,
                max_size=config["max_size"],
                duration=config["duration"],
                delay=i * wave_interval,
                color_tint=tuple(config["color_tint"]),
                image_override=image
            )
            shockwaves.append(shockwave)

        return shockwaves

    def list_effects(self) -> Dict[str, list]:
        """
        사용 가능한 모든 효과 목록 반환

        Returns:
            카테고리별 효과 변형 리스트
        """
        effects_list = {}
        for category, effects in self._effects_config.items():
            effects_list[category] = list(effects.keys())
        return effects_list

    def reload_config(self):
        """설정 파일 다시 로드 (게임 중 효과 변경용)"""
        self._image_cache.clear()
        self.load_config()
        print("INFO: VFXManager config reloaded")


# 싱글톤 인스턴스 전역 접근 함수
_vfx_manager_instance = None

def get_vfx_manager() -> VFXManager:
    """VFXManager 싱글톤 인스턴스 가져오기"""
    global _vfx_manager_instance
    if _vfx_manager_instance is None:
        _vfx_manager_instance = VFXManager()
    return _vfx_manager_instance


if __name__ == "__main__":
    # 테스트 코드
    pygame.init()

    vfx = VFXManager()
    print("\nAvailable effects:")
    for category, variants in vfx.list_effects().items():
        print(f"  {category}: {variants}")

    print("\nTest effect config:")
    config = vfx.get_effect_config("hit_effects", "fire")
    if config:
        print(f"  Fire effect: {config}")
