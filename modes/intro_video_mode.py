# modes/intro_video_mode.py
"""
IntroVideoMode - 인트로 영상 재생 모드
게임 시작 시 인트로 영상을 재생하고 메인 메뉴로 전환
"""

import pygame
from pathlib import Path

from modes.base_mode import GameMode, ModeConfig


class IntroVideoMode(GameMode):
    """
    인트로 영상 재생 모드

    특징:
    - 게임 시작 시 인트로 영상 재생
    - ESC 또는 클릭으로 스킵 가능
    - 영상 완료 또는 스킵 시 메인 메뉴로 전환
    """

    def get_config(self) -> ModeConfig:
        """인트로 영상 모드 설정"""
        return ModeConfig(
            mode_name="intro_video",
            perspective_enabled=False,
            background_type="static",
            parallax_enabled=False,
            wave_system_enabled=False,
        )

    def init(self):
        """인트로 영상 모드 초기화"""
        self.game_data = {}

        # 영상 경로 (프로젝트 루트 기준 절대 경로)
        project_root = Path(__file__).parent.parent
        self.video_path = project_root / "assets" / "videos" / "game_intro_01.mp4"

        # 영상 재생 상태
        self.video_playing = False
        self.video_finished = False
        self.skip_requested = False

        # OpenCV 비디오 캡처
        self.video_capture = None
        self.frame_surface = None

        # 프레임 오프셋 (화면 중앙 배치용)
        self.frame_offset_x = 0
        self.frame_offset_y = 0

        # 타이밍
        self.video_fps = 30
        self.frame_timer = 0.0
        self.frame_interval = 1.0 / self.video_fps

        # 페이드 효과
        self.fade_alpha = 0
        self.fade_speed = 500.0
        self.fading_out = False

        # 스킵 힌트 표시 타이머
        self.skip_hint_timer = 0.0
        self.skip_hint_delay = 2.0

        # 영상 로드
        self._load_video()

    def _load_video(self):
        """영상 파일 로드"""
        if not self.video_path.exists():
            self.video_finished = True
            return

        try:
            import cv2
            self.video_capture = cv2.VideoCapture(str(self.video_path))

            if not self.video_capture.isOpened():
                self.video_finished = True
                return

            # 영상 정보
            self.video_fps = self.video_capture.get(cv2.CAP_PROP_FPS)
            if self.video_fps <= 0:
                self.video_fps = 30
            self.frame_interval = 1.0 / self.video_fps

            self.video_width = int(self.video_capture.get(cv2.CAP_PROP_FRAME_WIDTH))
            self.video_height = int(self.video_capture.get(cv2.CAP_PROP_FRAME_HEIGHT))

            self.video_playing = True
            self._read_next_frame()

        except ImportError:
            self.video_finished = True
        except Exception:
            self.video_finished = True

    def _read_next_frame(self):
        """다음 프레임 읽기"""
        if not self.video_capture or not self.video_playing:
            return False

        try:
            import cv2
            ret, frame = self.video_capture.read()

            if not ret:
                self.video_playing = False
                self.fading_out = True
                return False

            # BGR → RGB 변환
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # 화면 크기에 맞게 스케일링
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

        except Exception:
            self.video_playing = False
            self.fading_out = True
            return False

    def update(self, dt: float, current_time: float):
        """업데이트"""
        self.skip_hint_timer += dt

        if self.video_finished or self.skip_requested:
            self._go_to_main_menu()
            return

        # 페이드아웃 처리
        if self.fading_out:
            self.fade_alpha += self.fade_speed * dt
            if self.fade_alpha >= 255:
                self.fade_alpha = 255
                self.video_finished = True
            return

        # 프레임 업데이트
        if self.video_playing:
            self.frame_timer += dt
            while self.frame_timer >= self.frame_interval:
                self.frame_timer -= self.frame_interval
                if not self._read_next_frame():
                    if not self.fading_out:
                        self.fading_out = True
                    break

    def render(self, screen: pygame.Surface):
        """렌더링"""
        screen.fill((0, 0, 0))

        if self.frame_surface:
            screen.blit(self.frame_surface, (self.frame_offset_x, self.frame_offset_y))

        # 스킵 힌트 (2초 후 표시)
        if self.skip_hint_timer >= self.skip_hint_delay and not self.fading_out:
            self._render_skip_hint(screen)

        # 페이드 오버레이
        if self.fade_alpha > 0:
            fade_surface = pygame.Surface(self.screen_size, pygame.SRCALPHA)
            fade_surface.fill((0, 0, 0, int(self.fade_alpha)))
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

    def handle_event(self, event: pygame.event.Event):
        """이벤트 처리"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._skip_video()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                self._skip_video()

    def _skip_video(self):
        """영상 스킵"""
        if not self.fading_out and not self.video_finished:
            self.fading_out = True
            self.video_playing = False

    def _go_to_main_menu(self):
        """인트로 종료 후 MainMenuMode로 전환 (배경 이미지 표시)"""
        if self.video_capture:
            self.video_capture.release()
            self.video_capture = None

        from modes.main_menu_mode import MainMenuMode
        self.request_switch_mode(MainMenuMode)

    def on_exit(self):
        """모드 종료 시 정리"""
        if self.video_capture:
            self.video_capture.release()
            self.video_capture = None
        super().on_exit()
