"""
간단한 타이핑 사운드 생성 스크립트
pygame.mixer를 사용하여 짧은 비프음 생성
"""

import pygame
import numpy as np
from pathlib import Path

pygame.mixer.init(frequency=22050, size=-16, channels=1)

def create_typing_sound():
    """짧은 타이핑 사운드 생성 (클릭 소리)"""
    sample_rate = 22050
    duration = 0.05  # 50ms
    frequency = 800  # 800Hz

    # 사운드 생성
    n_samples = int(sample_rate * duration)
    t = np.linspace(0, duration, n_samples, False)

    # 사인파 생성
    wave = np.sin(2 * np.pi * frequency * t)

    # 엔벨로프 적용 (페이드 아웃)
    envelope = np.exp(-t * 50)
    wave = wave * envelope

    # 볼륨 조절
    wave = wave * 0.1

    # 16비트 정수로 변환
    wave = np.int16(wave * 32767)

    # 스테레오로 변환 (2채널)
    stereo_wave = np.zeros((n_samples, 2), dtype=np.int16)
    stereo_wave[:, 0] = wave
    stereo_wave[:, 1] = wave

    # pygame Sound 객체 생성
    sound = pygame.sndarray.make_sound(stereo_wave)

    return sound

def save_typing_sound():
    """타이핑 사운드를 파일로 저장"""
    import wave as wave_module

    sound = create_typing_sound()

    # 디렉토리 생성
    sound_dir = Path("assets/sounds/ui")
    sound_dir.mkdir(parents=True, exist_ok=True)

    # WAV 파일로 저장
    output_path = sound_dir / "sfx_typing.wav"

    # pygame.mixer.Sound를 사용하여 WAV로 저장
    # (내부적으로 wav 형식 사용)
    sample_rate = 22050
    duration = 0.08  # 80ms로 증가 (더 길게)
    frequency = 1200  # 1200Hz로 증가 (더 높은 음)

    n_samples = int(sample_rate * duration)
    t = np.linspace(0, duration, n_samples, False)
    wave_data = np.sin(2 * np.pi * frequency * t)
    envelope = np.exp(-t * 40)  # 더 부드러운 감쇠
    wave_data = wave_data * envelope * 0.3  # 볼륨 30%로 증가
    wave_data = np.int16(wave_data * 32767)

    # WAV 파일 수동 저장
    with wave_module.open(str(output_path), 'w') as wav_file:
        wav_file.setnchannels(1)  # 모노
        wav_file.setsampwidth(2)  # 16비트
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(wave_data.tobytes())

    print(f"[OK] Typing sound created: {output_path}")
    print(f"     Duration: {duration}s, Frequency: {frequency}Hz")

    return output_path

if __name__ == "__main__":
    try:
        path = save_typing_sound()
        print(f"\nTyping sound saved successfully!")
        print(f"File: {path}")
        print(f"Size: {path.stat().st_size} bytes")

        # 테스트 재생
        print("\nTesting sound...")
        sound = pygame.mixer.Sound(str(path))
        sound.play()
        pygame.time.wait(100)
        print("Sound test complete!")

    except Exception as e:
        print(f"[ERROR] Failed to create sound: {e}")
        import traceback
        traceback.print_exc()
