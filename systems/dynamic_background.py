# systems/dynamic_background.py
"""
Dynamic Background System
웨이브별 색상 변환 + 적 처치 시 시각 효과
"""

import pygame
import numpy as np
from pathlib import Path
from typing import Dict, Tuple, Optional
import config


class DynamicBackground:
    """
    동적 배경 시스템
    - 원본 이미지의 붉은색 영역을 웨이브별로 다른 색상으로 변환
    - 적 처치 시 펄스/플래시 효과
    """

    # 웨이브별 색상 설정 (Hue shift in degrees, saturation multiplier, brightness multiplier)
    WAVE_COLORS = {
        1: {"name": "Red (Original)", "hue_shift": 0, "sat_mult": 1.0, "bright_mult": 1.0},
        2: {"name": "Orange", "hue_shift": 30, "sat_mult": 1.1, "bright_mult": 1.05},
        3: {"name": "Yellow", "hue_shift": 60, "sat_mult": 1.0, "bright_mult": 1.1},
        4: {"name": "Cyan", "hue_shift": 180, "sat_mult": 1.0, "bright_mult": 1.0},
        5: {"name": "Purple", "hue_shift": 270, "sat_mult": 1.1, "bright_mult": 0.95},
    }

    def __init__(self, screen_size: Tuple[int, int]):
        self.screen_size = screen_size
        self.original_image: Optional[pygame.Surface] = None
        self.current_background: Optional[pygame.Surface] = None
        self.wave_backgrounds: Dict[int, pygame.Surface] = {}

        # 킬 이펙트 관련
        self.kill_flash_alpha = 0
        self.kill_flash_color = (255, 255, 255)
        self.kill_pulse_scale = 1.0
        self.kill_pulse_active = False

        # 배경 펄스 효과
        self.pulse_overlay: Optional[pygame.Surface] = None
        self.pulse_alpha = 0
        self.pulse_decay = 200  # 초당 감소량

        # 색상 시프트 애니메이션
        self.color_shift_progress = 0
        self.color_shift_target = 0
        self.color_shift_speed = 50  # 초당 진행도

    def load_base_image(self, image_path: str) -> bool:
        """원본 이미지 로드"""
        try:
            path = Path(image_path)
            if path.exists():
                self.original_image = pygame.image.load(str(path)).convert()
                self.original_image = pygame.transform.scale(self.original_image, self.screen_size)
                print(f"INFO: DynamicBackground loaded: {image_path}")
                return True
            else:
                print(f"WARNING: Image not found: {image_path}")
                return False
        except Exception as e:
            print(f"ERROR: Failed to load image: {e}")
            return False

    def generate_wave_backgrounds(self):
        """모든 웨이브용 배경 미리 생성"""
        if self.original_image is None:
            print("WARNING: No original image loaded")
            return

        for wave_num, color_config in self.WAVE_COLORS.items():
            self.wave_backgrounds[wave_num] = self._create_color_shifted_bg(
                color_config["hue_shift"],
                color_config["sat_mult"],
                color_config["bright_mult"]
            )
            print(f"INFO: Generated wave {wave_num} background: {color_config['name']}")

    def _create_color_shifted_bg(self, hue_shift: int, sat_mult: float, bright_mult: float) -> pygame.Surface:
        """색상 변환된 배경 생성 (HSV 조작)"""
        if self.original_image is None:
            surface = pygame.Surface(self.screen_size)
            surface.fill((0, 0, 0))
            return surface

        # pygame Surface를 numpy 배열로 변환
        arr = pygame.surfarray.array3d(self.original_image).astype(np.float32)

        # RGB to HSV 변환 (수동 구현 - OpenCV 없이)
        r, g, b = arr[:, :, 0] / 255.0, arr[:, :, 1] / 255.0, arr[:, :, 2] / 255.0

        max_c = np.maximum(np.maximum(r, g), b)
        min_c = np.minimum(np.minimum(r, g), b)
        diff = max_c - min_c

        # Hue 계산
        h = np.zeros_like(max_c)

        # max == r
        mask_r = (max_c == r) & (diff > 0)
        h[mask_r] = (60 * ((g[mask_r] - b[mask_r]) / diff[mask_r]) + 360) % 360

        # max == g
        mask_g = (max_c == g) & (diff > 0)
        h[mask_g] = (60 * ((b[mask_g] - r[mask_g]) / diff[mask_g]) + 120) % 360

        # max == b
        mask_b = (max_c == b) & (diff > 0)
        h[mask_b] = (60 * ((r[mask_b] - g[mask_b]) / diff[mask_b]) + 240) % 360

        # Saturation 계산
        s = np.where(max_c > 0, diff / max_c, 0)

        # Value (밝기)
        v = max_c

        # 붉은색 영역만 선택 (Hue 0-30 또는 330-360)
        red_mask = ((h >= 0) & (h <= 40)) | ((h >= 320) & (h <= 360))
        # 충분한 채도가 있는 픽셀만
        red_mask = red_mask & (s > 0.2) & (v > 0.1)

        # Hue 시프트 적용 (붉은색 영역만)
        h[red_mask] = (h[red_mask] + hue_shift) % 360

        # Saturation 조정
        s[red_mask] = np.clip(s[red_mask] * sat_mult, 0, 1)

        # Value (밝기) 조정
        v[red_mask] = np.clip(v[red_mask] * bright_mult, 0, 1)

        # HSV to RGB 변환
        c = v * s
        x = c * (1 - np.abs((h / 60) % 2 - 1))
        m = v - c

        r_out = np.zeros_like(h)
        g_out = np.zeros_like(h)
        b_out = np.zeros_like(h)

        # H 범위별 RGB 계산
        mask = (h >= 0) & (h < 60)
        r_out[mask], g_out[mask], b_out[mask] = c[mask], x[mask], 0

        mask = (h >= 60) & (h < 120)
        r_out[mask], g_out[mask], b_out[mask] = x[mask], c[mask], 0

        mask = (h >= 120) & (h < 180)
        r_out[mask], g_out[mask], b_out[mask] = 0, c[mask], x[mask]

        mask = (h >= 180) & (h < 240)
        r_out[mask], g_out[mask], b_out[mask] = 0, x[mask], c[mask]

        mask = (h >= 240) & (h < 300)
        r_out[mask], g_out[mask], b_out[mask] = x[mask], 0, c[mask]

        mask = (h >= 300) & (h < 360)
        r_out[mask], g_out[mask], b_out[mask] = c[mask], 0, x[mask]

        r_final = ((r_out + m) * 255).astype(np.uint8)
        g_final = ((g_out + m) * 255).astype(np.uint8)
        b_final = ((b_out + m) * 255).astype(np.uint8)

        # 결과 배열 생성
        result_arr = np.stack([r_final, g_final, b_final], axis=2)

        # numpy 배열을 pygame Surface로 변환
        result_surface = pygame.surfarray.make_surface(result_arr)

        return result_surface

    def set_wave(self, wave_num: int):
        """현재 웨이브 설정"""
        if wave_num in self.wave_backgrounds:
            self.current_background = self.wave_backgrounds[wave_num]
        elif wave_num in self.WAVE_COLORS:
            # 아직 생성 안됐으면 즉시 생성
            config_data = self.WAVE_COLORS[wave_num]
            self.current_background = self._create_color_shifted_bg(
                config_data["hue_shift"],
                config_data["sat_mult"],
                config_data["bright_mult"]
            )
            self.wave_backgrounds[wave_num] = self.current_background
        else:
            # 5웨이브 이후는 원본 사용
            self.current_background = self.original_image

    def trigger_kill_effect(self, kill_count: int = 1, is_last_enemy: bool = False):
        """적 처치 시 효과 트리거

        Args:
            kill_count: 처치한 적 수
            is_last_enemy: 마지막 적인지 여부
        """
        if is_last_enemy:
            # 마지막 적 처치 - 강한 효과
            self.pulse_alpha = 200
            self.brightness_boost = 0.5
            self.brightness_boost_decay = 1.0
            self.pulse_decay = 150  # 느리게 감소
        else:
            # 일반 킬 - 약한 효과
            self.pulse_alpha = 40 + min(kill_count * 10, 30)  # 40~70
            self.brightness_boost = 0.1
            self.brightness_boost_decay = 3.0  # 빠르게 감소
            self.pulse_decay = 300  # 빠르게 감소

        # 웨이브별 펄스 색상
        wave_colors = {
            1: (255, 80, 80),     # 밝은 빨강
            2: (255, 200, 80),    # 밝은 주황
            3: (255, 255, 120),   # 밝은 노랑
            4: (80, 255, 255),    # 밝은 시안
            5: (220, 120, 255),   # 밝은 보라
        }
        current_wave = getattr(self, '_current_wave', 1)
        self.kill_flash_color = wave_colors.get(current_wave, (255, 255, 255))

    def update(self, dt: float):
        """매 프레임 업데이트"""
        # 펄스 알파 감소
        if self.pulse_alpha > 0:
            self.pulse_alpha = max(0, self.pulse_alpha - self.pulse_decay * dt)

        # 밝기 부스트 감소
        if hasattr(self, 'brightness_boost') and self.brightness_boost > 0:
            decay_rate = getattr(self, 'brightness_boost_decay', 2.0)
            self.brightness_boost = max(0, self.brightness_boost - decay_rate * dt)

    def draw(self, screen: pygame.Surface):
        """배경 그리기"""
        # 기본 배경
        if self.current_background:
            screen.blit(self.current_background, (0, 0))
        else:
            screen.fill((0, 0, 0))

        # 밝기 부스트 오버레이 (흰색 반투명)
        if hasattr(self, 'brightness_boost') and self.brightness_boost > 0:
            bright_overlay = pygame.Surface(self.screen_size, pygame.SRCALPHA)
            bright_alpha = int(self.brightness_boost * 100)
            bright_overlay.fill((255, 255, 255, bright_alpha))
            screen.blit(bright_overlay, (0, 0))

        # 킬 펄스 오버레이 (색상 플래시)
        if self.pulse_alpha > 0:
            overlay = pygame.Surface(self.screen_size, pygame.SRCALPHA)
            color_with_alpha = (*self.kill_flash_color, int(self.pulse_alpha))
            overlay.fill(color_with_alpha)
            screen.blit(overlay, (0, 0))

            # 가장자리 강조 효과 (비네팅 역방향)
            if self.pulse_alpha > 50:
                edge_size = 80
                edge_alpha = int(self.pulse_alpha * 0.5)
                # 상단
                top_rect = pygame.Surface((self.screen_size[0], edge_size), pygame.SRCALPHA)
                for i in range(edge_size):
                    alpha = int(edge_alpha * (1 - i / edge_size))
                    pygame.draw.line(top_rect, (*self.kill_flash_color, alpha), (0, i), (self.screen_size[0], i))
                screen.blit(top_rect, (0, 0))
                # 하단
                screen.blit(pygame.transform.flip(top_rect, False, True), (0, self.screen_size[1] - edge_size))

    def get_wave_color_name(self, wave_num: int) -> str:
        """웨이브 색상 이름 반환"""
        if wave_num in self.WAVE_COLORS:
            return self.WAVE_COLORS[wave_num]["name"]
        return "Default"


# 간편 생성 함수
def create_dynamic_background(screen_size: Tuple[int, int], image_path: str) -> DynamicBackground:
    """동적 배경 생성 헬퍼"""
    bg = DynamicBackground(screen_size)
    if bg.load_base_image(image_path):
        bg.generate_wave_backgrounds()
    return bg


print("INFO: dynamic_background.py loaded")
