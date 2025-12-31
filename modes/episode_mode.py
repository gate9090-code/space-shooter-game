# modes/episode_mode.py
"""
EpisodeMode - Episode/Segment 관리 모드
Episode의 각 Segment를 순차적으로 실행하고 전환 관리
"""

import pygame
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

from modes.base_mode import GameMode, ModeConfig
from mode_configs.config_episodes import (
    EpisodeData, SegmentData, SegmentType,
    get_episode, SEGMENT_DEFAULTS
)
import config


# 에피소드별 인트로 동영상 설정
EPISODE_INTRO_VIDEOS = {
    "ep1": "assets/videos/mission_01.mp4",
    # 다른 에피소드의 인트로 동영상도 여기에 추가 가능
    # "ep2": "assets/videos/mission_02.mp4",
}


@dataclass
class EpisodeModeConfig(ModeConfig):
    """Episode 모드 설정"""
    mode_name: str = "episode"
    wave_system_enabled: bool = False
    spawn_system_enabled: bool = False
    show_wave_ui: bool = False


class EpisodeMode(GameMode):
    """
    Episode 관리 모드

    Episode의 Segment들을 순차적으로 실행하고,
    각 Segment 타입에 맞는 서브모드로 전환하거나 내부 처리
    """

    def __init__(self, engine, episode_id: str = None, **kwargs):
        """
        Args:
            engine: 게임 엔진
            episode_id: 실행할 Episode ID
        """
        self.episode_id = episode_id
        self.episode_data: Optional[EpisodeData] = None
        self.current_segment_index: int = 0
        self.segment_state: str = "pending"  # pending, running, completed

        # Segment별 핸들러
        self.segment_handlers = {}

        # 내부 상태
        self.transition_timer: float = 0
        self.is_transitioning: bool = False
        self.fade_alpha: int = 0

        # 배경
        self.current_background: Optional[pygame.Surface] = None

        # 인트로 동영상 관련 상태
        self.intro_video_playing: bool = False
        self.intro_video_finished: bool = False
        self.video_capture = None
        self.frame_surface: Optional[pygame.Surface] = None
        self.frame_offset_x: int = 0
        self.frame_offset_y: int = 0
        self.video_fps: float = 30
        self.frame_timer: float = 0.0
        self.frame_interval: float = 1.0 / 30
        self.video_fade_alpha: int = 0
        self.video_fading_out: bool = False
        self.skip_hint_timer: float = 0.0

        super().__init__(engine)

    def get_config(self) -> ModeConfig:
        return EpisodeModeConfig()

    def init(self):
        """Episode 초기화"""
        # Episode 데이터 로드
        if self.episode_id:
            self.episode_data = get_episode(self.episode_id)

        if not self.episode_data:
            print(f"ERROR: Episode not found: {self.episode_id}")
            self._return_to_hub()
            return

        # current_episode 설정 (NarrativeMode에서 EpisodeResourceLoader 사용)
        # 실제 로드된 에피소드 ID 사용 (별칭 변환 후)
        self.engine.shared_state["current_episode"] = self.episode_data.id

        print(f"INFO: Episode initialized: {self.episode_data.title}")
        print(f"INFO: Total segments: {len(self.episode_data.segments)}")

        # Segment 핸들러 등록
        self._register_segment_handlers()

        # 인트로 동영상 체크 및 로드
        self._check_and_load_intro_video()

        # 첫 Segment 시작 플래그 (인트로 동영상이 없거나 완료 후 시작)
        self._needs_first_segment_start = not self.intro_video_playing

        # 커스텀 커서
        self.custom_cursor = self._load_base_cursor()

    def _check_and_load_intro_video(self):
        """에피소드 인트로 동영상 체크 및 로드"""
        # 에피소드 ID로 인트로 동영상 경로 확인
        video_path = EPISODE_INTRO_VIDEOS.get(self.episode_id)
        if not video_path:
            self.intro_video_finished = True
            return

        # 파일 존재 확인
        if not Path(video_path).exists():
            print(f"INFO: Intro video not found: {video_path}")
            self.intro_video_finished = True
            return

        # 동영상 로드
        try:
            import cv2
            self.video_capture = cv2.VideoCapture(video_path)

            if not self.video_capture.isOpened():
                print(f"WARNING: Failed to open intro video: {video_path}")
                self.intro_video_finished = True
                return

            # 영상 정보
            self.video_fps = self.video_capture.get(cv2.CAP_PROP_FPS)
            if self.video_fps <= 0:
                self.video_fps = 30
            self.frame_interval = 1.0 / self.video_fps

            self.video_width = int(self.video_capture.get(cv2.CAP_PROP_FRAME_WIDTH))
            self.video_height = int(self.video_capture.get(cv2.CAP_PROP_FRAME_HEIGHT))

            self.intro_video_playing = True
            self.intro_video_finished = False
            self.skip_hint_timer = 0.0

            # 첫 프레임 읽기
            self._read_next_video_frame()

            # 마우스 커서 숨기기 (동영상 재생 중)
            pygame.mouse.set_visible(False)

            print(f"INFO: Intro video loaded: {video_path}")

        except ImportError:
            print("WARNING: cv2 not available, skipping intro video")
            self.intro_video_finished = True
        except Exception as e:
            print(f"WARNING: Failed to load intro video: {e}")
            self.intro_video_finished = True

    def _read_next_video_frame(self) -> bool:
        """다음 동영상 프레임 읽기"""
        if not self.video_capture or not self.intro_video_playing:
            return False

        try:
            import cv2
            ret, frame = self.video_capture.read()

            if not ret:
                self.intro_video_playing = False
                self.video_fading_out = True
                return False

            # BGR → RGB 변환
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # 화면 크기에 맞게 스케일링 (비율 유지)
            screen_w, screen_h = self.screen_size
            video_aspect = self.video_width / self.video_height
            screen_aspect = screen_w / screen_h

            if video_aspect > screen_aspect:
                new_width = screen_w
                new_height = int(screen_w / video_aspect)
            else:
                new_height = screen_h
                new_width = int(screen_h * video_aspect)

            frame = cv2.resize(frame, (new_width, new_height))
            frame = frame.swapaxes(0, 1)
            self.frame_surface = pygame.surfarray.make_surface(frame)

            self.frame_offset_x = (screen_w - new_width) // 2
            self.frame_offset_y = (screen_h - new_height) // 2

            return True

        except Exception as e:
            print(f"WARNING: Failed to read video frame: {e}")
            self.intro_video_playing = False
            self.video_fading_out = True
            return False

    def _update_intro_video(self, dt: float):
        """인트로 동영상 업데이트"""
        self.skip_hint_timer += dt

        # 페이드아웃 처리
        if self.video_fading_out:
            self.video_fade_alpha += int(500 * dt)
            if self.video_fade_alpha >= 255:
                self.video_fade_alpha = 255
                self._finish_intro_video()
            return

        # 프레임 업데이트
        if self.intro_video_playing:
            self.frame_timer += dt
            while self.frame_timer >= self.frame_interval:
                self.frame_timer -= self.frame_interval
                if not self._read_next_video_frame():
                    if not self.video_fading_out:
                        self.video_fading_out = True
                    break

    def _render_intro_video(self, screen: pygame.Surface):
        """인트로 동영상 렌더링"""
        screen.fill((0, 0, 0))

        if self.frame_surface:
            screen.blit(self.frame_surface, (self.frame_offset_x, self.frame_offset_y))

        # 스킵 힌트 (2초 후 표시)
        if self.skip_hint_timer >= 2.0 and not self.video_fading_out:
            self._render_skip_hint(screen)

        # 페이드 오버레이
        if self.video_fade_alpha > 0:
            fade_surface = pygame.Surface(self.screen_size, pygame.SRCALPHA)
            fade_surface.fill((0, 0, 0, int(self.video_fade_alpha)))
            screen.blit(fade_surface, (0, 0))

    def _render_skip_hint(self, screen: pygame.Surface):
        """스킵 힌트 렌더링"""
        font = self.fonts.get("small")
        if not font:
            return

        alpha = int(128 + 80 * abs(((pygame.time.get_ticks() // 500) % 2) - 0.5) * 2)
        hint_text = "Press ESC or Click to skip"
        hint_surf = font.render(hint_text, True, (180, 180, 180))
        hint_surf.set_alpha(alpha)
        hint_rect = hint_surf.get_rect(bottomright=(self.screen_size[0] - 30, self.screen_size[1] - 20))
        screen.blit(hint_surf, hint_rect)

    def _skip_intro_video(self):
        """인트로 동영상 스킵"""
        if self.intro_video_playing and not self.video_fading_out:
            self.video_fading_out = True
            self.intro_video_playing = False

    def _finish_intro_video(self):
        """인트로 동영상 종료"""
        if self.video_capture:
            self.video_capture.release()
            self.video_capture = None

        self.intro_video_finished = True
        self.intro_video_playing = False
        self.video_fading_out = False
        self.video_fade_alpha = 0
        self.frame_surface = None

        # 마우스 커서 복원 (커스텀 커서가 있으면 계속 숨김)
        if self.custom_cursor:
            pygame.mouse.set_visible(False)
        else:
            pygame.mouse.set_visible(True)

        # 첫 세그먼트 시작 플래그 설정
        self._needs_first_segment_start = True

        print("INFO: Intro video finished, starting segments")

    def _register_segment_handlers(self):
        """Segment 타입별 핸들러 등록"""
        self.segment_handlers = {
            SegmentType.BRIEFING: self._handle_briefing_segment,
            SegmentType.COMBAT: self._handle_combat_segment,
            SegmentType.DIALOGUE: self._handle_dialogue_segment,
            SegmentType.EXPLORATION: self._handle_exploration_segment,
            SegmentType.REFLECTION: self._handle_reflection_segment,
            SegmentType.CUTSCENE: self._handle_cutscene_segment,
            SegmentType.ENDING: self._handle_ending_segment,
        }

    def _get_current_segment(self) -> Optional[SegmentData]:
        """현재 Segment 가져오기"""
        if not self.episode_data:
            return None
        if self.current_segment_index >= len(self.episode_data.segments):
            return None
        return self.episode_data.segments[self.current_segment_index]

    def _start_current_segment(self):
        """현재 Segment 시작"""
        segment = self._get_current_segment()
        if not segment:
            self._complete_episode()
            return

        self.segment_state = "running"
        print(f"INFO: Starting segment {self.current_segment_index + 1}/{len(self.episode_data.segments)}: {segment.type.name}")

        # 배경 로드
        if segment.background:
            self._load_background(segment.background)

        # Segment 타입별 핸들러 호출
        handler = self.segment_handlers.get(segment.type)
        if handler:
            handler(segment)
        else:
            print(f"WARNING: No handler for segment type: {segment.type}")
            self._advance_to_next_segment()

    def _advance_to_next_segment(self):
        """다음 Segment로 진행"""
        self.current_segment_index += 1
        self.segment_state = "pending"

        if self.current_segment_index >= len(self.episode_data.segments):
            self._complete_episode()
        else:
            # 전환 효과
            self.is_transitioning = True
            self.transition_timer = 0.5
            self.fade_alpha = 0

    def _complete_episode(self):
        """Episode 완료 처리"""
        print(f"INFO: Episode completed: {self.episode_data.title}")

        # 보상 지급
        if self.episode_data.rewards:
            credits = self.episode_data.rewards.get("credits", 0)
            if credits > 0:
                current = self.engine.shared_state.get("global_score", 0)
                self.engine.shared_state["global_score"] = current + credits
                print(f"INFO: Rewarded {credits} credits")

        # 완료 기록
        completed = self.engine.shared_state.get("completed_episodes", [])
        if self.episode_id not in completed:
            completed.append(self.episode_id)
            self.engine.shared_state["completed_episodes"] = completed

        # current_act 업데이트 (Episode의 Act + 1로 진행)
        episode_act = self.episode_data.act
        current_act = self.engine.shared_state.get("current_act", 1)
        if episode_act >= current_act:
            new_act = episode_act + 1
            self.engine.shared_state["current_act"] = new_act
            print(f"INFO: Act progressed to {new_act}")

            # 게임 클리어 체크 (Act 5 완료 시)
            if episode_act == 5:
                self.engine.shared_state["game_cleared"] = True
                print("INFO: Game cleared!")

        # 저장
        self._save_progress()

        # BaseHub로 귀환
        self._return_to_hub()

    def _return_to_hub(self):
        """BaseHub로 귀환"""
        # current_episode 정리
        if "current_episode" in self.engine.shared_state:
            del self.engine.shared_state["current_episode"]

        from modes.base_hub_mode import BaseHubMode
        self.request_switch_mode(BaseHubMode)

    def _save_progress(self):
        """진행 상황 저장"""
        import json
        from pathlib import Path

        save_path = Path("saves/campaign_progress.json")
        try:
            save_data = {}
            if save_path.exists():
                with open(save_path, 'r', encoding='utf-8') as f:
                    save_data = json.load(f)

            save_data["completed_episodes"] = self.engine.shared_state.get("completed_episodes", [])
            save_data["credits"] = self.engine.shared_state.get("global_score", 0)
            save_data["current_act"] = self.engine.shared_state.get("current_act", 1)
            save_data["game_cleared"] = self.engine.shared_state.get("game_cleared", False)

            save_path.parent.mkdir(parents=True, exist_ok=True)
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, indent=2, ensure_ascii=False)

            print("INFO: Episode progress saved")
        except Exception as e:
            print(f"WARNING: Failed to save progress: {e}")

    def _load_background(self, bg_name: str):
        """배경 이미지 로드"""
        try:
            # 여러 경로 시도
            paths = [
                f"assets/story_mode/backgrounds/{bg_name}",
                f"assets/story_mode/reflection/backgrounds/{bg_name}",
                f"assets/images/backgrounds/{bg_name}",
            ]

            for path in paths:
                try:
                    bg = self.asset_manager.load_image(path)
                    if bg:
                        self.current_background = pygame.transform.scale(
                            bg, self.screen_size
                        )
                        return
                except:
                    continue

            # 폴백: 검은 배경
            self.current_background = pygame.Surface(self.screen_size)
            self.current_background.fill((10, 10, 20))

        except Exception as e:
            print(f"WARNING: Failed to load background: {bg_name} - {e}")
            self.current_background = None

    # =========================================================
    # Segment 핸들러
    # =========================================================

    def _handle_briefing_segment(self, segment: SegmentData):
        """BRIEFING Segment 처리 - NarrativeMode로 전환"""
        print(f"INFO: Briefing segment - dialogue_key: {segment.dialogue_key}")

        # NarrativeMode에 데이터 전달
        self.engine.shared_state["narrative_data"] = {
            "type": "BRIEFING",
            "scene_id": segment.dialogue_key,
            "dialogues": [],  # JSON에서 로드됨
            "background": segment.background or "",
            "title": self.episode_data.title if self.episode_data else "",
            "location": segment.location if hasattr(segment, 'location') else "",
        }

        from modes.narrative_mode import NarrativeMode
        self.request_push_mode(NarrativeMode)

    def _handle_combat_segment(self, segment: SegmentData):
        """COMBAT Segment 처리 - CombatMode로 전환"""
        # extra 데이터에서 rounds, enemies, spawn_rate 가져오기 (JSON 로드용)
        extra = segment.extra if hasattr(segment, 'extra') and segment.extra else {}
        rounds = extra.get('rounds') or (len(segment.waves) if segment.waves else 3)
        enemies = extra.get('enemies') or ["scout", "fighter"]
        spawn_rate = extra.get('spawn_rate') or 1.0

        print(f"INFO: Combat segment - rounds: {rounds}, boss: {segment.boss}")

        # CombatMode에 전투 정보 전달
        self.engine.shared_state["combat_data"] = {
            "mode": "story",
            "rounds": rounds,
            "enemies": enemies,
            "boss": segment.boss,
            "background": segment.background or "",
            "spawn_rate": spawn_rate,
            "difficulty": 1.0 + (self.episode_data.act * 0.2) if self.episode_data else 1.0,
        }

        from modes.combat_mode import CombatMode
        self.request_push_mode(CombatMode)

    def _handle_dialogue_segment(self, segment: SegmentData):
        """DIALOGUE Segment 처리 - NarrativeMode로 전환"""
        print(f"INFO: Dialogue segment - dialogue_key: {segment.dialogue_key}")

        # NarrativeMode에 데이터 전달
        self.engine.shared_state["narrative_data"] = {
            "type": "DIALOGUE",
            "scene_id": segment.dialogue_key,
            "dialogues": [],  # JSON에서 로드됨
            "background": segment.background or "",
        }

        from modes.narrative_mode import NarrativeMode
        self.request_push_mode(NarrativeMode)

    def _handle_exploration_segment(self, segment: SegmentData):
        """EXPLORATION Segment 처리 - 탐색 모드"""
        print(f"INFO: Exploration segment - points: {segment.points}")

        # TODO: ExplorationMode 구현 후 연동
        self._advance_to_next_segment()

    def _handle_reflection_segment(self, segment: SegmentData):
        """REFLECTION Segment 처리 - NarrativeMode로 전환 (철학적 성찰)"""
        print(f"INFO: Reflection segment - scene_key: {segment.scene_key}, optional: {segment.optional}")

        # 선택적 씬인 경우 조건 체크
        if segment.optional:
            # 트리거 조건 확인
            if segment.trigger_condition == "first_play":
                seen_reflections = self.engine.shared_state.get("seen_reflections", [])
                if segment.scene_key in seen_reflections:
                    print(f"INFO: Reflection already seen, skipping: {segment.scene_key}")
                    self._advance_to_next_segment()
                    return

        # NarrativeMode (REFLECTION 타입)로 푸시
        self.engine.shared_state["narrative_data"] = {
            "type": "REFLECTION",
            "scene_id": segment.scene_key,
            "dialogues": [],  # JSON에서 로드됨
            "background": segment.background or "",
            "color_tone": getattr(segment, 'color_tone', 'blue'),
        }

        from modes.narrative_mode import NarrativeMode
        self.request_push_mode(NarrativeMode)

    def _handle_cutscene_segment(self, segment: SegmentData):
        """CUTSCENE Segment 처리 - NarrativeMode로 전환 (특수 효과 컷씬)"""
        print(f"INFO: Cutscene segment - effect: {segment.effect}")

        # extra에서 effect_data 가져오기 (JSON에서 로드된 데이터)
        extra = segment.extra if hasattr(segment, 'extra') and segment.extra else {}
        effect_data = extra.get("effect_data", {})

        # segment.images가 있으면 effect_data에 추가 (폴라로이드 등)
        if segment.images:
            # 효과 타입에 따라 적절한 키로 추가
            if segment.effect == "PolaroidMemoryEffect":
                effect_data["polaroid_images"] = segment.images
            elif segment.effect == "ClassifiedDocumentEffect":
                effect_data["document_images"] = segment.images
            elif segment.effect in ("FilmReelEffect", "DamagedHologramEffect"):
                effect_data["hologram_images"] = segment.images
            elif segment.effect == "ShatteredMirrorEffect":
                effect_data["fragment_images"] = segment.images
            elif segment.effect == "StarMapEffect":
                effect_data["marker_images"] = segment.images

        # NarrativeMode (CUTSCENE 타입)로 푸시
        self.engine.shared_state["narrative_data"] = {
            "type": "CUTSCENE",
            "scene_id": segment.dialogue_key if hasattr(segment, 'dialogue_key') else "",
            "dialogues": [],
            "background": segment.background or "",
            "effects": {
                "type": segment.effect,
                "effect_data": effect_data,
            }
        }

        from modes.narrative_mode import NarrativeMode
        self.request_push_mode(NarrativeMode)

    def _handle_ending_segment(self, segment: SegmentData):
        """ENDING Segment 처리 - 엔딩 대화 후 미션 완료"""
        print(f"INFO: Ending segment - dialogue_key: {segment.dialogue_key}")

        # 대화가 있으면 NarrativeMode로 전환
        if segment.dialogue_key:
            self.engine.shared_state["narrative_data"] = {
                "type": "DIALOGUE",
                "scene_id": segment.dialogue_key,
                "dialogues": [],  # JSON에서 로드됨
                "background": segment.background or "",
            }
            # 엔딩 플래그 설정 (NarrativeMode 완료 후 에피소드 완료)
            self.engine.shared_state["ending_segment"] = True

            from modes.narrative_mode import NarrativeMode
            self.request_push_mode(NarrativeMode)
        else:
            # 대화 없으면 바로 완료
            self._complete_episode()

    # =========================================================
    # 게임 루프
    # =========================================================

    def update(self, dt: float, current_time: float):
        """업데이트"""
        # 인트로 동영상 재생 중
        if not self.intro_video_finished:
            self._update_intro_video(dt)
            return

        # 첫 세그먼트 시작 (init에서 플래그 설정됨)
        if getattr(self, '_needs_first_segment_start', False):
            self._needs_first_segment_start = False
            self._start_current_segment()
            return

        # 전환 중
        if self.is_transitioning:
            self.transition_timer -= dt
            self.fade_alpha = min(255, int((0.5 - self.transition_timer) / 0.25 * 255))

            if self.transition_timer <= 0:
                self.is_transitioning = False
                self.fade_alpha = 0
                self._start_current_segment()

    def render(self, screen: pygame.Surface):
        """렌더링"""
        # 인트로 동영상 재생 중
        if not self.intro_video_finished:
            self._render_intro_video(screen)
            return

        # 배경
        if self.current_background:
            screen.blit(self.current_background, (0, 0))
        else:
            screen.fill((10, 10, 20))

        # 전환 효과 (페이드)
        if self.is_transitioning and self.fade_alpha > 0:
            fade_surf = pygame.Surface(self.screen_size, pygame.SRCALPHA)
            fade_surf.fill((0, 0, 0, self.fade_alpha))
            screen.blit(fade_surf, (0, 0))

        # 커스텀 커서
        self._render_base_cursor(screen, self.custom_cursor)

    def handle_event(self, event: pygame.event.Event):
        """이벤트 처리"""
        # 인트로 동영상 재생 중 스킵 처리
        if not self.intro_video_finished:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self._skip_intro_video()
                    return
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    self._skip_intro_video()
                    return
            return

        if event.type == pygame.KEYDOWN:
            # ESC: Episode 중단 확인
            if event.key == pygame.K_ESCAPE:
                # TODO: 확인 다이얼로그
                self._return_to_hub()
                return

            # Space: 전환 중 스킵
            if event.key == pygame.K_SPACE and self.is_transitioning:
                self.is_transitioning = False
                self.fade_alpha = 0
                self._start_current_segment()

    def on_resume(self, return_data: Optional[Dict] = None):
        """서브모드에서 복귀 시"""
        super().on_resume(return_data)

        if return_data:
            # COMBAT 완료 (CombatMode에서 복귀)
            if return_data.get("combat_complete"):
                success = return_data.get("success", True)
                if success:
                    print("INFO: Combat segment completed successfully")
                    self._advance_to_next_segment()
                else:
                    print("INFO: Combat failed - returning to hub")
                    self._return_to_hub()
                return

            # NARRATIVE 완료 (NarrativeMode에서 복귀)
            if return_data.get("narrative_complete"):
                scene_id = return_data.get("scene_id", "")
                narrative_type = return_data.get("narrative_type", "")

                # REFLECTION 타입인 경우 본 씬 기록
                if narrative_type == "REFLECTION":
                    seen = self.engine.shared_state.get("seen_reflections", [])
                    if scene_id and scene_id not in seen:
                        seen.append(scene_id)
                        self.engine.shared_state["seen_reflections"] = seen

                # ENDING 세그먼트였으면 에피소드 완료
                if self.engine.shared_state.get("ending_segment"):
                    self.engine.shared_state["ending_segment"] = False
                    print("INFO: Ending narrative completed - completing episode")
                    self._complete_episode()
                    return

                print(f"INFO: Narrative segment completed: {narrative_type}")
                self._advance_to_next_segment()
                return

            # REFLECTION 완료 (레거시 - ReflectionMode에서 복귀)
            if return_data.get("reflection_complete"):
                scene_key = return_data.get("scene_key")
                if scene_key:
                    seen = self.engine.shared_state.get("seen_reflections", [])
                    if scene_key not in seen:
                        seen.append(scene_key)
                        self.engine.shared_state["seen_reflections"] = seen
                print("INFO: Reflection segment completed")
                self._advance_to_next_segment()
                return

            # EXPLORATION 완료
            if return_data.get("exploration_complete"):
                print("INFO: Exploration segment completed")
                self._advance_to_next_segment()
                return

    # =========================================================
    # 라이프사이클
    # =========================================================

    def on_enter(self):
        super().on_enter()
        if self.custom_cursor:
            self._enable_custom_cursor()

    def on_exit(self):
        # 비디오 리소스 정리
        if self.video_capture:
            self.video_capture.release()
            self.video_capture = None

        self._disable_custom_cursor()
        super().on_exit()


print("INFO: episode_mode.py loaded")
