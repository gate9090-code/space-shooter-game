# modes/main_menu_mode.py
"""
MainMenuMode - 인트로 이미지 표시 후 BaseHub로 자동 전환

흐름: 인트로 동영상 → 배경 이미지(전체화면) → BaseHub(인트로 스토리)
"""

import pygame
from pathlib import Path

from modes.base_mode import GameMode, ModeConfig


class MainMenuMode(GameMode):
    """
    인트로 이미지 표시 모드

    - 전체화면 배경 이미지 페이드인
    - 잠시 표시 후 자동으로 BaseHub로 전환
    - 버튼 없음 (클릭/키 입력으로 스킵 가능)
    """

    def get_config(self) -> ModeConfig:
        return ModeConfig(
            mode_name="main_menu",
            perspective_enabled=False,
            background_type="static",
            parallax_enabled=False,
            wave_system_enabled=False,
        )

    def init(self):
        """초기화"""
        self.game_data = {}

        # 배경 이미지 로드 (전체화면)
        self._load_background_image()

        # 페이드인/아웃 효과
        self.fade_alpha = 0.0
        self.fade_speed = 80.0  # 페이드인 속도
        self.fade_state = "fade_in"  # fade_in → display → fade_out → done

        # 표시 시간
        self.display_timer = 0.0
        self.display_duration = 2.0  # 2초간 표시

        print("INFO: MainMenuMode initialized (Auto-transition)")

    def _load_background_image(self):
        """전체화면 배경 이미지 로드"""
        self.background = None

        # 배경 이미지 경로 시도
        bg_paths = [
            Path("assets/images/ui/intro_start_01.png"),
            Path("assets/images/backgrounds/bg_space.jpg"),
            Path("assets/images/backgrounds/intro_bg.jpg"),
        ]

        for bg_path in bg_paths:
            if bg_path.exists():
                try:
                    img = pygame.image.load(str(bg_path)).convert()
                    # 전체화면 크기로 스케일
                    self.background = pygame.transform.smoothscale(
                        img, self.screen_size
                    )
                    print(f"INFO: Loaded background: {bg_path}")
                    return
                except Exception as e:
                    print(f"WARNING: Failed to load {bg_path}: {e}")

        # 폴백: 그라데이션 배경
        self.background = pygame.Surface(self.screen_size)
        for y in range(self.screen_size[1]):
            ratio = y / self.screen_size[1]
            color = (
                int(5 + 15 * ratio),
                int(5 + 10 * ratio),
                int(20 + 30 * ratio)
            )
            pygame.draw.line(self.background, color, (0, y), (self.screen_size[0], y))
        print("INFO: Using gradient background")

    def update(self, dt: float, current_time: float):
        """업데이트"""
        if self.fade_state == "fade_in":
            self.fade_alpha += self.fade_speed * dt
            if self.fade_alpha >= 255:
                self.fade_alpha = 255
                self.fade_state = "display"

        elif self.fade_state == "display":
            self.display_timer += dt
            if self.display_timer >= self.display_duration:
                self.fade_state = "fade_out"

        elif self.fade_state == "fade_out":
            self.fade_alpha -= self.fade_speed * dt
            if self.fade_alpha <= 0:
                self.fade_alpha = 0
                self.fade_state = "done"
                self._go_to_base_hub()

    def render(self, screen: pygame.Surface):
        """렌더링"""
        # 배경 (검정)
        screen.fill((0, 0, 0))

        # 배경 이미지 (페이드 효과)
        if self.background:
            if self.fade_alpha < 255:
                bg_copy = self.background.copy()
                bg_copy.set_alpha(int(self.fade_alpha))
                screen.blit(bg_copy, (0, 0))
            else:
                screen.blit(self.background, (0, 0))

    def handle_event(self, event: pygame.event.Event):
        """이벤트 처리 - 클릭/키 입력으로 스킵"""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._skip_to_hub()
        elif event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_ESCAPE):
                self._skip_to_hub()

    def _skip_to_hub(self):
        """스킵하여 BaseHub로 이동"""
        if self.fade_state != "done":
            self.fade_state = "done"
            self._go_to_base_hub()

    def _go_to_base_hub(self):
        """BaseHub로 전환 (인트로 스토리 표시)"""
        # 새 게임 플래그 설정
        self.engine.shared_state['is_new_game'] = True
        self.engine.shared_state['show_opening'] = True
        self.engine.shared_state['current_mission'] = "act1_m1"
        self.engine.shared_state['completed_missions'] = []
        self.engine.shared_state['current_act'] = 1

        # 캠페인 저장 초기화
        self._reset_campaign_save()

        # BaseHub로 이동
        from modes.base_hub_mode import BaseHubMode
        self.request_switch_mode(BaseHubMode)

    def _reset_campaign_save(self):
        """캠페인 저장 초기화"""
        import json
        save_path = Path("saves/campaign_progress.json")
        try:
            save_path.parent.mkdir(parents=True, exist_ok=True)
            initial_data = {
                "current_mission": "act1_m1",
                "completed_missions": [],
                "current_act": 1,
                "credits": 0,
            }
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(initial_data, f, indent=2)
        except Exception:
            pass


print("INFO: main_menu_mode.py loaded (Simplified)")
