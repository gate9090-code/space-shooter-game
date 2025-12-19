# sound_manager.py

import pygame
from pathlib import Path
from typing import Dict, Optional
import config


class SoundManager:
    """게임 사운드 및 음악 관리 클래스

    사운드 파일이 없어도 정상 작동하며, 파일이 있으면 자동으로 재생합니다.
    """

    def __init__(self):
        """사운드 매니저 초기화"""
        self.enabled = config.SOUND_ENABLED
        self.bgm_volume = config.DEFAULT_BGM_VOLUME
        self.sfx_volume = config.DEFAULT_SFX_VOLUME

        # 사운드 딕셔너리
        self.bgm: Dict[str, Optional[pygame.mixer.Sound]] = {}
        self.sfx: Dict[str, Optional[pygame.mixer.Sound]] = {}

        # 현재 재생 중인 BGM 이름
        self.current_bgm: Optional[str] = None

        # pygame mixer 초기화
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            print("INFO: Sound system initialized successfully")
        except Exception as e:
            print(f"WARNING: Failed to initialize sound system: {e}")
            self.enabled = False
            return

        # 사운드 파일 로드
        self._load_sounds()

    def _load_sounds(self):
        """모든 사운드 파일을 로드합니다 (파일이 없으면 None으로 설정)"""
        # BGM 로드
        for name, path in config.BGM_FILES.items():
            try:
                if Path(path).exists():
                    self.bgm[name] = pygame.mixer.Sound(str(path))
                    print(f"INFO: Loaded BGM: {name} from {path}")
                else:
                    self.bgm[name] = None
                    print(f"INFO: BGM file not found (will skip): {name} at {path}")
            except Exception as e:
                print(f"WARNING: Failed to load BGM {name}: {e}")
                self.bgm[name] = None

        # SFX 로드
        for name, path in config.SFX_FILES.items():
            try:
                if Path(path).exists():
                    self.sfx[name] = pygame.mixer.Sound(str(path))
                    self.sfx[name].set_volume(self.sfx_volume)
                    print(f"INFO: Loaded SFX: {name} from {path}")
                else:
                    self.sfx[name] = None
                    # print(f"INFO: SFX file not found (will skip): {name} at {path}")
            except Exception as e:
                print(f"WARNING: Failed to load SFX {name}: {e}")
                self.sfx[name] = None

    def play_bgm(self, bgm_name: str, loops: int = -1, fade_ms: int = 1000):
        """배경 음악 재생

        Args:
            bgm_name: BGM 이름 (config.BGM_FILES 키)
            loops: 반복 횟수 (-1 = 무한 반복)
            fade_ms: 페이드 인 시간 (밀리초)
        """
        if not self.enabled:
            return

        # 이미 같은 BGM이 재생 중이면 스킵
        if self.current_bgm == bgm_name and pygame.mixer.get_busy():
            return

        # 현재 BGM 중지
        self.stop_bgm(fade_ms=fade_ms)

        # 새 BGM 재생
        if bgm_name in self.bgm and self.bgm[bgm_name] is not None:
            try:
                channel = self.bgm[bgm_name].play(loops=loops, fade_ms=fade_ms)
                if channel:
                    channel.set_volume(self.bgm_volume)
                    self.current_bgm = bgm_name
                    print(f"INFO: Playing BGM: {bgm_name}")
            except Exception as e:
                print(f"WARNING: Failed to play BGM {bgm_name}: {e}")

    def stop_bgm(self, fade_ms: int = 1000):
        """배경 음악 중지

        Args:
            fade_ms: 페이드 아웃 시간 (밀리초)
        """
        if not self.enabled:
            return

        try:
            pygame.mixer.fadeout(fade_ms)
            self.current_bgm = None
        except Exception as e:
            print(f"WARNING: Failed to stop BGM: {e}")

    def pause_bgm(self):
        """배경 음악 일시정지"""
        if not self.enabled:
            return

        try:
            pygame.mixer.pause()
        except Exception as e:
            print(f"WARNING: Failed to pause BGM: {e}")

    def resume_bgm(self):
        """배경 음악 재개"""
        if not self.enabled:
            return

        try:
            pygame.mixer.unpause()
        except Exception as e:
            print(f"WARNING: Failed to resume BGM: {e}")

    def play_sfx(self, sfx_name: str, volume_override: Optional[float] = None):
        """효과음 재생

        Args:
            sfx_name: SFX 이름 (config.SFX_FILES 키)
            volume_override: 볼륨 오버라이드 (None이면 기본 볼륨 사용)
        """
        if not self.enabled:
            return

        if sfx_name in self.sfx and self.sfx[sfx_name] is not None:
            try:
                sound = self.sfx[sfx_name]
                if volume_override is not None:
                    sound.set_volume(volume_override)
                else:
                    sound.set_volume(self.sfx_volume)
                sound.play()
            except Exception as e:
                print(f"WARNING: Failed to play SFX {sfx_name}: {e}")

    def set_bgm_volume(self, volume: float):
        """BGM 볼륨 설정 (0.0 ~ 1.0)"""
        self.bgm_volume = max(0.0, min(1.0, volume))

        # 현재 재생 중인 BGM 볼륨 조정
        if self.current_bgm and pygame.mixer.get_busy():
            try:
                for channel in range(pygame.mixer.get_num_channels()):
                    ch = pygame.mixer.Channel(channel)
                    if ch.get_busy():
                        ch.set_volume(self.bgm_volume)
            except Exception as e:
                print(f"WARNING: Failed to set BGM volume: {e}")

    def set_sfx_volume(self, volume: float):
        """SFX 볼륨 설정 (0.0 ~ 1.0)"""
        self.sfx_volume = max(0.0, min(1.0, volume))

        # 모든 SFX 볼륨 업데이트
        for sound in self.sfx.values():
            if sound is not None:
                sound.set_volume(self.sfx_volume)

    def toggle_sound(self):
        """사운드 시스템 온/오프 토글"""
        self.enabled = not self.enabled
        if not self.enabled:
            self.stop_bgm(fade_ms=500)
        print(f"INFO: Sound system {'enabled' if self.enabled else 'disabled'}")

    def play_wave_bgm(self, wave_number: int):
        """웨이브에 맞는 BGM 재생

        Args:
            wave_number: 웨이브 번호
        """
        bgm_name = config.WAVE_BGM_MAPPING.get(wave_number, "normal")
        self.play_bgm(bgm_name)

    def cleanup(self):
        """사운드 시스템 정리"""
        try:
            self.stop_bgm(fade_ms=500)
            pygame.mixer.quit()
            print("INFO: Sound system cleaned up")
        except Exception as e:
            print(f"WARNING: Error during sound cleanup: {e}")
