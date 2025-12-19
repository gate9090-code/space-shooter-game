# asset_manager.py

import pygame
from typing import Dict, Tuple, List, Optional
from pathlib import Path
import config  # config.py에서 상수(색상 등)를 임포트합니다.


class AssetManager:
    """게임 자원(이미지, 폰트) 관리 및 캐싱"""

    # 이미지 캐시 (클래스 레벨 유지)
    _cache: Dict[Path, Dict[Tuple[int, int], pygame.Surface]] = {}

    def __init__(self):
        """AssetManager 인스턴스 초기화 및 폰트 캐시 생성"""
        self.font_cache: Dict[int, pygame.font.Font] = {}
        self.emoji_font_cache: Dict[int, pygame.font.Font] = {}

        # config에서 FONT_PATH를 로드 (없을 경우 None)
        self.font_path = getattr(config, "FONT_PATH", None)

    @classmethod
    def get_image(cls, path: Path, size: Tuple[int, int]) -> pygame.Surface:
        """이미지를 로드하고 지정된 크기로 조정 후 캐싱"""
        if path not in cls._cache:
            cls._cache[path] = {}

        if size not in cls._cache[path]:
            try:
                # 💡 [핵심] 이미지 로드 및 조정
                image = pygame.image.load(path).convert_alpha()
                image = pygame.transform.scale(image, size)
                cls._cache[path][size] = image
            except pygame.error as e:
                print(f"이미지 로드 오류: {path}, {e}")
                # 오류 발생 시 임시 빨간색 Surface 사용 (경로 오류 해결)
                dummy_surface = pygame.Surface(size, pygame.SRCALPHA)
                dummy_surface.fill(config.RED) 
                cls._cache[path][size] = dummy_surface

        return cls._cache[path][size]

    def get_font(self, size: int) -> pygame.font.Font:
        """지정된 크기의 폰트를 로드하고 캐싱합니다."""
        # 1. 캐시 확인
        if size in self.font_cache:
            return self.font_cache[size]

        # 2. 폰트 로드 시도
        try:
            font_obj = None
            
            # 폰트 경로가 있고 파일이 존재하면 로드
            if self.font_path and Path(self.font_path).exists():
                font_obj = pygame.font.Font(str(Path(self.font_path)), size)
            else:
                # 경로가 없거나 파일이 없으면 기본 폰트 사용
                if self.font_path is not None:
                     print(f"WARNING: Font file not found at {self.font_path}. Using default font.")
                font_obj = pygame.font.Font(None, size)
            
            self.font_cache[size] = font_obj
            return font_obj
        except Exception as e:
            print(f"폰트 로드 오류: {e}. 기본 폰트 사용.")
            # 폰트 로드 실패 시에도 기본 폰트 사용을 시도
            font_obj = pygame.font.Font(None, size)
            self.font_cache[size] = font_obj
            return font_obj

    def get_emoji_font(self, size: int) -> pygame.font.Font:
        """이모지 렌더링을 위한 이모지 전용 폰트를 로드하고 캐싱합니다."""
        # 1. 캐시 확인
        if size in self.emoji_font_cache:
            return self.emoji_font_cache[size]

        # 2. 이모지 폰트 로드 시도 (Windows: Segoe UI Emoji)
        try:
            # Windows 시스템 폰트에서 이모지 폰트 찾기
            emoji_font = pygame.font.SysFont("Segoe UI Emoji", size)

            # 폰트가 제대로 로드되지 않았다면 fallback
            if emoji_font is None:
                emoji_font = pygame.font.SysFont("Apple Color Emoji", size)  # macOS

            if emoji_font is None:
                emoji_font = pygame.font.SysFont("Noto Color Emoji", size)  # Linux

            # 그래도 없으면 기본 폰트
            if emoji_font is None:
                print("WARNING: Emoji font not found. Using default font.")
                emoji_font = pygame.font.Font(None, size)

            self.emoji_font_cache[size] = emoji_font
            return emoji_font

        except Exception as e:
            print(f"이모지 폰트 로드 오류: {e}. 기본 폰트 사용.")
            # 오류 시 기본 폰트 사용
            emoji_font = pygame.font.Font(None, size)
            self.emoji_font_cache[size] = emoji_font
            return emoji_font