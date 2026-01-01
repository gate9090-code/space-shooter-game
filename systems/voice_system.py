# systems/voice_system.py
"""
VoiceSystem - 게임 음성 지원 시스템
캐릭터별 TTS(Text-to-Speech) 기능 제공

지원 어댑터:
- pyttsx3: 오프라인 TTS (기본)
- OpenAI TTS: 고품질 온라인 TTS (선택)
- Edge TTS: Microsoft Edge 온라인 TTS (무료)
"""

import threading
import queue
from abc import ABC, abstractmethod
from typing import Dict, Optional
from pathlib import Path


class VoiceAdapter(ABC):
    """TTS 어댑터 추상 클래스"""

    @abstractmethod
    def speak(self, text: str) -> None:
        """텍스트를 음성으로 변환하여 재생"""
        pass

    @abstractmethod
    def stop(self) -> None:
        """현재 재생 중지"""
        pass

    @abstractmethod
    def is_speaking(self) -> bool:
        """현재 재생 중인지 확인"""
        pass

    @abstractmethod
    def set_voice_params(self, **kwargs) -> None:
        """음성 파라미터 설정 (속도, 피치 등)"""
        pass


class Pyttsx3Adapter(VoiceAdapter):
    """pyttsx3 오프라인 TTS 어댑터"""

    def __init__(self, rate: int = 150, volume: float = 1.0, voice_id: Optional[str] = None):
        """
        Args:
            rate: 말하기 속도 (기본 150, 범위 50-300)
            volume: 볼륨 (0.0 ~ 1.0)
            voice_id: 특정 음성 ID (None이면 기본 음성)
        """
        self._engine = None
        self._rate = rate
        self._volume = volume
        self._voice_id = voice_id
        self._speaking = False
        self._initialized = False

    def _ensure_initialized(self):
        """엔진 초기화 (지연 로딩)"""
        if self._initialized:
            return True

        try:
            import pyttsx3
            self._engine = pyttsx3.init()
            self._engine.setProperty('rate', self._rate)
            self._engine.setProperty('volume', self._volume)

            if self._voice_id:
                self._engine.setProperty('voice', self._voice_id)

            self._initialized = True
            return True
        except Exception as e:
            print(f"WARNING: pyttsx3 initialization failed: {e}")
            return False

    def speak(self, text: str) -> None:
        if not self._ensure_initialized():
            return

        self._speaking = True
        try:
            self._engine.say(text)
            self._engine.runAndWait()
        except Exception as e:
            print(f"WARNING: pyttsx3 speak error: {e}")
        finally:
            self._speaking = False

    def stop(self) -> None:
        if self._engine and self._initialized:
            try:
                self._engine.stop()
            except:
                pass
        self._speaking = False

    def is_speaking(self) -> bool:
        return self._speaking

    def set_voice_params(self, **kwargs) -> None:
        if not self._ensure_initialized():
            return

        if 'rate' in kwargs:
            self._rate = kwargs['rate']
            self._engine.setProperty('rate', self._rate)
        if 'volume' in kwargs:
            self._volume = kwargs['volume']
            self._engine.setProperty('volume', self._volume)
        if 'voice_id' in kwargs:
            self._voice_id = kwargs['voice_id']
            self._engine.setProperty('voice', self._voice_id)


class OpenAIAdapter(VoiceAdapter):
    """OpenAI TTS 어댑터 (고품질 온라인)"""

    # OpenAI TTS 음성 옵션
    VOICES = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]

    def __init__(self, api_key: str, voice: str = "nova", speed: float = 1.0):
        """
        Args:
            api_key: OpenAI API 키
            voice: 음성 종류 (alloy, echo, fable, onyx, nova, shimmer)
            speed: 속도 (0.25 ~ 4.0)
        """
        self._api_key = api_key
        self._voice = voice
        self._speed = speed
        self._speaking = False
        self._client = None

    def _ensure_initialized(self):
        if self._client:
            return True
        try:
            from openai import OpenAI
            self._client = OpenAI(api_key=self._api_key)
            return True
        except Exception as e:
            print(f"WARNING: OpenAI initialization failed: {e}")
            return False

    def speak(self, text: str) -> None:
        if not self._ensure_initialized():
            return

        self._speaking = True
        try:
            import tempfile
            import pygame

            response = self._client.audio.speech.create(
                model="tts-1",
                voice=self._voice,
                input=text,
                speed=self._speed
            )

            # 임시 파일로 저장 후 재생
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                response.stream_to_file(f.name)

                # pygame으로 재생
                pygame.mixer.music.load(f.name)
                pygame.mixer.music.play()

                while pygame.mixer.music.get_busy():
                    pygame.time.wait(100)

        except Exception as e:
            print(f"WARNING: OpenAI TTS error: {e}")
        finally:
            self._speaking = False

    def stop(self) -> None:
        try:
            import pygame
            pygame.mixer.music.stop()
        except:
            pass
        self._speaking = False

    def is_speaking(self) -> bool:
        return self._speaking

    def set_voice_params(self, **kwargs) -> None:
        if 'voice' in kwargs and kwargs['voice'] in self.VOICES:
            self._voice = kwargs['voice']
        if 'speed' in kwargs:
            self._speed = max(0.25, min(4.0, kwargs['speed']))


class EdgeTTSAdapter(VoiceAdapter):
    """Microsoft Edge TTS 어댑터 (무료 온라인) - pyttsx3 폴백 지원, SSML 감정 표현 지원"""

    # 한국어 음성 옵션
    KOREAN_VOICES = {
        "female_1": "ko-KR-SunHiNeural",    # 여성 (밝음)
        "female_2": "ko-KR-JiMinNeural",    # 여성 (차분)
        "male_1": "ko-KR-InJoonNeural",     # 남성 (일반)
        "male_2": "ko-KR-BongJinNeural",    # 남성 (깊음)
    }

    # 영어 음성 옵션
    ENGLISH_VOICES = {
        "female_1": "en-US-JennyNeural",
        "female_2": "en-US-AriaNeural",
        "male_1": "en-US-GuyNeural",
        "male_2": "en-US-ChristopherNeural",
    }

    # 감정/스타일 옵션 (SSML mstts:express-as)
    # 주의: 한국어 음성은 일부 스타일만 지원
    EMOTION_STYLES = {
        "default": None,           # 기본 (스타일 없음)
        "cheerful": "cheerful",    # 밝고 활기찬
        "sad": "sad",              # 슬픈
        "angry": "angry",          # 화난
        "fearful": "fearful",      # 두려운
        "excited": "excited",      # 흥분한
        "friendly": "friendly",    # 친근한
        "hopeful": "hopeful",      # 희망찬
        "shouting": "shouting",    # 외치는
        "whispering": "whispering", # 속삭이는
        "terrified": "terrified",  # 공포에 질린
        "serious": "serious",      # 진지한
        "depressed": "depressed",  # 우울한
        "gentle": "gentle",        # 부드러운
        "lyrical": "lyrical",      # 서정적인
    }

    # 텍스트 패턴 기반 자동 감정 감지 (긴박감 패턴 강화)
    # 우선순위: 괄호로 시작하는 지시어 > 긴박 상황 > 일반 감정
    EMOTION_PATTERNS = {
        # 1순위: 괄호로 시작하는 지시어 (가장 먼저 확인)
        "whispering": ["(속삭", "(독백)", "(작게)", "(조용히)", "(생각)", "(혼잣말)"],
        "shouting": ["(외치며)", "(크게)", "(소리치며)"],

        # 2순위: 긴박/위기 상황 (빠르고 높은 톤)
        "terrified": ["공포", "도망쳐", "살려", "무섭", "죽", "끝이야"],
        "fearful": ["...?", "위험해", "두려", "불길", "폭발", "임계점", "붕괴"],

        # 3순위: 경고/흥분 (긴박감)
        "excited": ["!!", "!!!", "와!", "대박", "해냈어", "찾았어", "발견", "통신이야", "살아있어", "있어!"],

        # 4순위: 일반 감정
        "angry": ["젠장", "분노", "화가", "어떻게 감히", "용납", "숙주", "수확"],
        "hopeful": ["희망", "믿어", "할 수 있", "언젠가", "반드시", "기다리", "찾을 거야"],
        "sad": ["슬퍼", "아쉽", "그리워", "눈물", "보고싶"],
        "serious": ["작전", "명령", "보고", "분석", "확률", "데이터", "경고:"],

        # 5순위: 부드러운 감정
        "cheerful": ["고마워", "감사", "다행", "좋았어", "잘됐어"],
        "gentle": ["괜찮아", "걱정마", "함께", "곁에"],
    }

    def __init__(self, voice: str = "ko-KR-SunHiNeural", rate: str = "+0%", pitch: str = "+0Hz",
                 fallback_enabled: bool = True, style: str = None, style_degree: float = 1.0,
                 auto_emotion: bool = True, static_effect: bool = False):
        """
        Args:
            voice: Edge TTS 음성 ID
            rate: 속도 (예: "+10%", "-20%")
            pitch: 피치 (예: "+5Hz", "-10Hz")
            style: 감정/스타일 (예: "cheerful", "sad", "angry")
            style_degree: 스타일 강도 (0.01 ~ 2.0, 기본 1.0)
            auto_emotion: 텍스트 기반 자동 감정 감지 여부
            fallback_enabled: 인터넷 실패 시 pyttsx3 폴백 사용
            static_effect: 치지직 정적 잡음 효과 활성화 (안드로이드/나레이터용)
        """
        self._voice = voice
        self._rate = rate
        self._pitch = pitch
        self._style = style
        self._style_degree = max(0.01, min(2.0, style_degree))
        self._auto_emotion = auto_emotion
        self._speaking = False
        self._fallback_enabled = fallback_enabled
        self._fallback_adapter: Optional[Pyttsx3Adapter] = None
        self._use_fallback = False  # 폴백 모드 활성화 여부
        self._static_effect = static_effect  # 치지직 효과 활성화
        self._static_sound = None  # 정적 잡음 사운드 객체

    def _detect_emotion(self, text: str) -> Optional[str]:
        """텍스트에서 감정 자동 감지"""
        if not self._auto_emotion:
            return self._style

        # 패턴 매칭으로 감정 감지
        for emotion, patterns in self.EMOTION_PATTERNS.items():
            for pattern in patterns:
                if pattern in text:
                    return emotion

        return self._style  # 기본 스타일 반환

    def _build_ssml(self, text: str, emotion: Optional[str] = None) -> str:
        """SSML 텍스트 생성 (감정 표현 포함)"""
        # 감정 스타일 결정
        style = emotion if emotion else self._style

        # 기본 prosody 설정
        prosody_attrs = []
        if self._rate and self._rate != "+0%":
            prosody_attrs.append(f'rate="{self._rate}"')
        if self._pitch and self._pitch != "+0Hz":
            prosody_attrs.append(f'pitch="{self._pitch}"')

        prosody_open = f'<prosody {" ".join(prosody_attrs)}>' if prosody_attrs else ''
        prosody_close = '</prosody>' if prosody_attrs else ''

        # 스타일이 있으면 mstts:express-as 태그 사용
        if style and style in self.EMOTION_STYLES and self.EMOTION_STYLES[style]:
            style_value = self.EMOTION_STYLES[style]
            style_degree_attr = f' styledegree="{self._style_degree}"' if self._style_degree != 1.0 else ''

            ssml = f'''<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis"
                xmlns:mstts="https://www.w3.org/2001/mstts" xml:lang="ko-KR">
                <voice name="{self._voice}">
                    <mstts:express-as style="{style_value}"{style_degree_attr}>
                        {prosody_open}{text}{prosody_close}
                    </mstts:express-as>
                </voice>
            </speak>'''
        else:
            # 스타일 없이 prosody만 적용
            ssml = f'''<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="ko-KR">
                <voice name="{self._voice}">
                    {prosody_open}{text}{prosody_close}
                </voice>
            </speak>'''

        return ssml

    def _get_fallback_adapter(self) -> Optional[Pyttsx3Adapter]:
        """폴백 어댑터 생성 (지연 로딩)"""
        if not self._fallback_enabled:
            return None

        if self._fallback_adapter is None:
            # Edge TTS rate를 pyttsx3 rate로 변환 (예: "+10%" -> 165)
            base_rate = 150
            try:
                rate_str = self._rate.replace("%", "").replace("+", "")
                rate_percent = int(rate_str) if rate_str else 0
                pyttsx3_rate = int(base_rate * (1 + rate_percent / 100))
            except:
                pyttsx3_rate = base_rate

            self._fallback_adapter = Pyttsx3Adapter(rate=pyttsx3_rate)
            print("INFO: pyttsx3 fallback adapter initialized")

        return self._fallback_adapter

    def _get_emotion_adjustments(self, emotion: Optional[str]) -> tuple:
        """감정에 따른 속도/피치 조정값 반환 (긴박감 강화)"""
        # 감정별 속도/피치 조정 (base rate/pitch에 추가)
        emotion_adjustments = {
            # 긴박/위기 상황 (강화됨)
            "excited": ("+20%", "+8Hz"),     # 흥분: 더 빠르고 높게
            "terrified": ("+30%", "+12Hz"),  # 공포: 가장 빠르고 높게 (떨림)
            "fearful": ("+15%", "+10Hz"),    # 두려움: 빠르고 높게
            "shouting": ("+25%", "+10Hz"),   # 외침: 매우 빠르고 높게

            # 일반 감정
            "cheerful": ("+10%", "+3Hz"),    # 밝음: 약간 빠르고 높게
            "sad": ("-15%", "-5Hz"),         # 슬픔: 느리고 낮게
            "depressed": ("-20%", "-8Hz"),   # 우울: 더 느리고 낮게
            "angry": ("+10%", "-8Hz"),       # 화남: 빠르고 낮게 (위협적)
            "hopeful": ("+5%", "+2Hz"),      # 희망: 약간 빠르고 높게
            "whispering": ("-30%", "-10Hz"), # 속삭임: 매우 느리고 낮게
            "serious": ("-5%", "-2Hz"),      # 진지함: 약간 느리고 낮게
            "gentle": ("-10%", "+2Hz"),      # 부드러움: 느리고 약간 높게
        }
        return emotion_adjustments.get(emotion, ("+0%", "+0Hz"))

    def _combine_rate_pitch(self, base: str, adjustment: str) -> str:
        """rate/pitch 값 합산 (예: "+5%" + "+10%" = "+15%")"""
        try:
            # 숫자 추출
            base_num = int(base.replace("%", "").replace("Hz", "").replace("+", ""))
            adj_num = int(adjustment.replace("%", "").replace("Hz", "").replace("+", ""))
            combined = base_num + adj_num

            # 부호와 단위 추가
            sign = "+" if combined >= 0 else ""
            unit = "%" if "%" in base else "Hz"
            return f"{sign}{combined}{unit}"
        except:
            return base

    def _init_static_sound(self):
        """치지직 정적 잡음 사운드 초기화"""
        if self._static_sound is not None:
            return

        try:
            from effects.static_generator import get_static_sound
            self._static_sound = get_static_sound()
            if self._static_sound:
                self._static_sound.set_volume(0.15)  # 볼륨 조절
        except Exception as e:
            print(f"WARNING: Failed to initialize static sound: {e}")
            self._static_sound = None

    def _play_static_effect(self):
        """치지직 효과음 재생"""
        if not self._static_effect:
            return

        try:
            self._init_static_sound()
            if self._static_sound:
                self._static_sound.play()
        except Exception as e:
            print(f"WARNING: Failed to play static sound: {e}")

    def speak(self, text: str) -> None:
        self._speaking = True

        # 이미 폴백 모드라면 pyttsx3 사용
        if self._use_fallback:
            fallback = self._get_fallback_adapter()
            if fallback:
                self._play_static_effect()  # 치지직 효과
                fallback.speak(text)
            self._speaking = False
            return

        try:
            import asyncio
            import tempfile
            import edge_tts
            import pygame

            # pygame 및 mixer 초기화 확인
            if not pygame.get_init():
                pygame.init()
            if not pygame.mixer.get_init():
                pygame.mixer.init()

            # music 모듈 사용 가능 확인
            if not hasattr(pygame.mixer, 'music'):
                raise RuntimeError("pygame.mixer.music not available")

            # 감정 감지 및 속도/피치 조정
            detected_emotion = self._detect_emotion(text)
            rate_adj, pitch_adj = self._get_emotion_adjustments(detected_emotion)
            final_rate = self._combine_rate_pitch(self._rate, rate_adj)
            final_pitch = self._combine_rate_pitch(self._pitch, pitch_adj)

            # 치지직 효과음 재생 (음성 시작 전)
            self._play_static_effect()

            async def _generate_and_play():
                communicate = edge_tts.Communicate(
                    text,
                    self._voice,
                    rate=final_rate,
                    pitch=final_pitch
                )

                # 임시 파일 생성 (먼저 닫고 저장)
                import os
                temp_file = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
                temp_path = temp_file.name
                temp_file.close()

                try:
                    await communicate.save(temp_path)

                    # mixer가 초기화되어 있는지 확인
                    if not pygame.mixer.get_init():
                        pygame.mixer.init()

                    pygame.mixer.music.load(temp_path)
                    pygame.mixer.music.play()

                    while pygame.mixer.music.get_busy():
                        await asyncio.sleep(0.1)
                finally:
                    # 재생 후 임시 파일 삭제
                    try:
                        os.unlink(temp_path)
                    except:
                        pass

            # 이벤트 루프 실행
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(_generate_and_play())
            loop.close()

        except ImportError:
            print("WARNING: edge-tts not installed. Run: pip install edge-tts")
            self._try_fallback(text)
        except Exception as e:
            # 네트워크 오류 등 - 폴백 시도
            error_msg = str(e).lower()
            if any(keyword in error_msg for keyword in ['connection', 'network', 'timeout', 'ssl', 'socket', 'resolve']):
                print(f"WARNING: Edge TTS network error, switching to offline fallback: {e}")
                self._use_fallback = True  # 이후 요청도 폴백 사용
                self._try_fallback(text)
            else:
                import traceback
                print(f"WARNING: Edge TTS error: {e}")
                traceback.print_exc()
                self._try_fallback(text)
        finally:
            self._speaking = False

    def _try_fallback(self, text: str):
        """pyttsx3 폴백 시도"""
        if not self._fallback_enabled:
            return

        fallback = self._get_fallback_adapter()
        if fallback:
            print("INFO: Using pyttsx3 offline fallback")
            fallback.speak(text)

    def stop(self) -> None:
        try:
            import pygame
            pygame.mixer.music.stop()
        except:
            pass

        # 폴백 어댑터도 중지
        if self._fallback_adapter:
            self._fallback_adapter.stop()

        self._speaking = False

    def is_speaking(self) -> bool:
        if self._fallback_adapter and self._fallback_adapter.is_speaking():
            return True
        # pygame mixer 상태도 확인 (실제 재생 중인지)
        try:
            import pygame
            if pygame.mixer.get_init() and hasattr(pygame.mixer, 'music') and pygame.mixer.music.get_busy():
                return True
        except Exception:
            pass
        return self._speaking

    def set_voice_params(self, **kwargs) -> None:
        if 'voice' in kwargs:
            self._voice = kwargs['voice']
        if 'rate' in kwargs:
            self._rate = kwargs['rate']
        if 'pitch' in kwargs:
            self._pitch = kwargs['pitch']

    def reset_fallback(self):
        """폴백 모드 해제 - 다시 Edge TTS 시도"""
        self._use_fallback = False
        print("INFO: Edge TTS fallback mode reset, will try online again")


class SilentAdapter(VoiceAdapter):
    """무음 어댑터 (음성 비활성화 시)"""

    def speak(self, text: str) -> None:
        pass

    def stop(self) -> None:
        pass

    def is_speaking(self) -> bool:
        return False

    def set_voice_params(self, **kwargs) -> None:
        pass


class VoiceSystem:
    """
    게임 음성 시스템

    캐릭터별 음성 설정 및 비동기 음성 재생 관리
    """

    def __init__(self, enabled: bool = True, default_adapter: str = "pyttsx3"):
        """
        Args:
            enabled: 음성 시스템 활성화 여부
            default_adapter: 기본 어댑터 ("pyttsx3", "openai", "edge", "silent")
        """
        self.enabled = enabled
        self.default_adapter = default_adapter

        # 캐릭터별 음성 어댑터
        self._character_voices: Dict[str, VoiceAdapter] = {}

        # 음성 재생 큐 (비동기)
        self._voice_queue: queue.Queue = queue.Queue()
        self._worker_thread: Optional[threading.Thread] = None
        self._running = False

        # 현재 재생 중인 어댑터
        self._current_adapter: Optional[VoiceAdapter] = None

        # 자막 표시용 콜백
        self._subtitle_callback = None

    def start(self):
        """음성 시스템 시작 (백그라운드 스레드)"""
        if not self.enabled:
            return

        self._running = True
        self._worker_thread = threading.Thread(target=self._voice_worker, daemon=True)
        self._worker_thread.start()
        print("INFO: VoiceSystem started")

    def stop(self):
        """음성 시스템 종료"""
        self._running = False

        # 현재 재생 중지
        if self._current_adapter:
            self._current_adapter.stop()

        # 큐 비우기
        while not self._voice_queue.empty():
            try:
                self._voice_queue.get_nowait()
            except:
                pass

        print("INFO: VoiceSystem stopped")

    def _voice_worker(self):
        """백그라운드 음성 재생 워커"""
        while self._running:
            try:
                # 큐에서 음성 요청 가져오기 (1초 대기)
                item = self._voice_queue.get(timeout=1.0)

                if item is None:
                    continue

                character, text, adapter = item

                self._current_adapter = adapter

                # 자막 콜백 호출
                if self._subtitle_callback:
                    self._subtitle_callback(character, text)

                # 음성 재생
                adapter.speak(text)

                self._current_adapter = None
                self._voice_queue.task_done()

            except queue.Empty:
                continue
            except Exception as e:
                print(f"WARNING: Voice worker error: {e}")

    def register_character(self, character_id: str, adapter: VoiceAdapter):
        """
        캐릭터 음성 등록

        Args:
            character_id: 캐릭터 ID (예: "ARTEMIS", "PILOT")
            adapter: 해당 캐릭터의 TTS 어댑터
        """
        self._character_voices[character_id] = adapter
        print(f"INFO: Registered voice for {character_id}")

    def speak(self, character_id: str, text: str):
        """
        캐릭터 음성 재생 (비동기)

        Args:
            character_id: 캐릭터 ID
            text: 대사 텍스트
        """
        if not self.enabled:
            return

        # 캐릭터 어댑터 가져오기
        adapter = self._character_voices.get(character_id)

        if not adapter:
            # 기본 어댑터 사용
            adapter = self._create_default_adapter()

        # 큐에 추가
        self._voice_queue.put((character_id, text, adapter))

    def speak_sync(self, character_id: str, text: str):
        """
        캐릭터 음성 재생 (동기, 대기)

        Args:
            character_id: 캐릭터 ID
            text: 대사 텍스트
        """
        if not self.enabled:
            return

        adapter = self._character_voices.get(character_id)
        if not adapter:
            adapter = self._create_default_adapter()

        # 자막 콜백
        if self._subtitle_callback:
            self._subtitle_callback(character_id, text)

        adapter.speak(text)

    def skip_current(self):
        """현재 재생 중인 음성 스킵"""
        if self._current_adapter:
            self._current_adapter.stop()

    def set_subtitle_callback(self, callback):
        """
        자막 표시 콜백 설정

        Args:
            callback: 함수 (character_id, text) -> None
        """
        self._subtitle_callback = callback

    def _create_default_adapter(self) -> VoiceAdapter:
        """기본 어댑터 생성"""
        if self.default_adapter == "pyttsx3":
            return Pyttsx3Adapter()
        elif self.default_adapter == "edge":
            return EdgeTTSAdapter()
        elif self.default_adapter == "silent":
            return SilentAdapter()
        else:
            return SilentAdapter()

    def is_speaking(self) -> bool:
        """현재 음성 재생 중인지 확인"""
        # 어댑터가 재생 중이면 True
        if self._current_adapter is not None and self._current_adapter.is_speaking():
            return True
        # pygame mixer 상태 직접 확인 (어댑터 상태와 별개로)
        try:
            import pygame
            if pygame.mixer.get_init() and hasattr(pygame.mixer, 'music') and pygame.mixer.music.get_busy():
                return True
        except Exception:
            pass
        # 큐에 대기 중인 음성이 있으면 True
        if not self._voice_queue.empty():
            return True
        return False

    def set_enabled(self, enabled: bool):
        """음성 활성화/비활성화"""
        self.enabled = enabled
        if not enabled:
            self.skip_current()


# 캐릭터 음성 설정 프리셋
CHARACTER_VOICE_PRESETS = {
    # 아르테미스: 밝고 따뜻한 여성 음성
    "ARTEMIS": {
        "adapter": "edge",
        "voice": "ko-KR-SunHiNeural",
        "rate": "+25%",  # 나레이터 기본(+15%) + 10% 더 빠르게
        "pitch": "+5Hz",  # 음 톤 높임 (기존 +2Hz → +5Hz)
    },
    # 파일럿: 차분하고 기계적인 남성 음성
    "PILOT": {
        "adapter": "edge",
        "voice": "ko-KR-InJoonNeural",
        "rate": "+20%",  # 나레이터 기본(+15%) + 5% 더 빠르게
        "pitch": "+0Hz",  # 음 톤 높임 (기존 -3Hz → +0Hz, 보통 톤)
    },
    # 안드로이드 나레이터: 기계적 로봇 음성 (Edge TTS 사용, 빠른 속도, 치지직 효과)
    "NARRATOR": {
        "adapter": "edge",
        "voice": "ko-KR-InJoonNeural",
        "rate": "+15%",  # 빠른 속도로 조정
        "pitch": "-5Hz",  # 약간 낮은 피치로 로봇 느낌 강화
        "static_effect": True,  # 치지직 정적 잡음 효과 활성화
    },
}


def create_voice_system_with_presets(enabled: bool = True) -> VoiceSystem:
    """
    프리셋 설정으로 VoiceSystem 생성

    Args:
        enabled: 음성 활성화 여부

    Returns:
        설정된 VoiceSystem
    """
    system = VoiceSystem(enabled=enabled, default_adapter="edge")

    for char_id, preset in CHARACTER_VOICE_PRESETS.items():
        adapter_type = preset.get("adapter", "edge")

        if adapter_type == "edge":
            adapter = EdgeTTSAdapter(
                voice=preset.get("voice", "ko-KR-SunHiNeural"),
                rate=preset.get("rate", "+0%"),
                pitch=preset.get("pitch", "+0Hz"),
                static_effect=preset.get("static_effect", False)  # 치지직 효과
            )
        elif adapter_type == "pyttsx3":
            adapter = Pyttsx3Adapter(
                rate=preset.get("rate", 150),
                volume=preset.get("volume", 1.0)
            )
        else:
            adapter = SilentAdapter()

        system.register_character(char_id, adapter)

    return system


print("INFO: voice_system.py loaded")
