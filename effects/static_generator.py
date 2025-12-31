"""
Static sound generator - 라디오 치지직 잡음 생성
"""
import pygame
import numpy as np


def get_static_sound(duration: float = 0.3, sample_rate: int = 22050) -> pygame.mixer.Sound:
    """
    정적 잡음(치지직) 사운드 생성

    Args:
        duration: 사운드 길이 (초)
        sample_rate: 샘플링 레이트

    Returns:
        pygame.mixer.Sound 객체
    """
    try:
        # 샘플 수 계산
        num_samples = int(duration * sample_rate)

        # 화이트 노이즈 생성 (-1.0 ~ 1.0)
        noise = np.random.uniform(-1.0, 1.0, num_samples)

        # 볼륨 엔벨로프 (페이드 인/아웃)
        fade_samples = int(0.05 * sample_rate)  # 50ms 페이드
        envelope = np.ones(num_samples)

        # 페이드 인
        envelope[:fade_samples] = np.linspace(0, 1, fade_samples)

        # 페이드 아웃
        envelope[-fade_samples:] = np.linspace(1, 0, fade_samples)

        # 엔벨로프 적용
        noise = noise * envelope

        # 16비트 정수로 변환 (-32767 ~ 32767)
        noise = (noise * 32767).astype(np.int16)

        # 스테레오로 변환 (2채널)
        stereo_noise = np.column_stack((noise, noise))

        # pygame Sound 객체 생성
        sound = pygame.sndarray.make_sound(stereo_noise)

        return sound

    except Exception as e:
        print(f"WARNING: Failed to generate static sound: {e}")
        return None


print("INFO: static_generator.py loaded")
