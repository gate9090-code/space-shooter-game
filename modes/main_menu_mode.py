# modes/main_menu_mode.py
"""
MainMenuMode - 메인 메뉴 모드
통합 게임 흐름: 새 게임 → 오프닝 → BaseHub
"""

import pygame
from pathlib import Path
from typing import Optional

from modes.base_mode import GameMode, ModeConfig
from mode_configs import config_base
from systems.save_system import get_save_system


class MainMenuMode(GameMode):
    """
    메인 메뉴 모드 (통합 게임 흐름)

    특징:
    - 인트로 이미지 페이드인
    - 새 게임: 오프닝 컷씬 → BaseHub
    - 이어하기: 저장된 진행 로드
    - 설정/종료
    """

    def get_config(self) -> ModeConfig:
        """메인 메뉴 설정"""
        return ModeConfig(
            mode_name="main_menu",
            perspective_enabled=False,
            background_type="static",
            parallax_enabled=False,
            wave_system_enabled=False,
        )

    def init(self):
        """메인 메뉴 초기화"""
        self.game_data = {}

        # 저장 시스템
        self.save_system = get_save_system()

        # 인트로 이미지 로드
        self._load_intro_image()

        # 페이드인 효과
        self.fade_alpha = 0.0
        self.fade_speed = 40.0  # 초당 알파 증가량 (천천히)
        self.fade_complete = False

        # 저장된 게임 진행 확인 (캠페인 진행 상태)
        self.has_campaign_save = self._check_campaign_save()
        self.campaign_save_info = self._get_campaign_save_info() if self.has_campaign_save else None

        # 버튼 정의 (새 게임 / 이어하기 / 설정 / 종료)
        self._init_buttons()

        # 선택된 액션
        self.selected_action: Optional[str] = None

        print("INFO: MainMenuMode initialized (Unified Flow)")

    def _load_intro_image(self):
        """인트로 이미지 로드"""
        self.intro_image = None
        self.intro_rect = None

        intro_path = Path("assets/images/ui/intro_start_01.png")
        if intro_path.exists():
            try:
                self.intro_image = pygame.image.load(str(intro_path)).convert_alpha()
                # 이미지 크기 조정 (화면 상단 60% 영역에 맞춤)
                target_height = int(self.screen_size[1] * 0.55)
                aspect_ratio = self.intro_image.get_width() / self.intro_image.get_height()
                target_width = int(target_height * aspect_ratio)

                # 화면 너비를 초과하면 너비 기준으로 조정
                if target_width > self.screen_size[0] - 40:
                    target_width = self.screen_size[0] - 40
                    target_height = int(target_width / aspect_ratio)

                self.intro_image = pygame.transform.smoothscale(
                    self.intro_image, (target_width, target_height)
                )
                # 상단 중앙 배치
                self.intro_rect = self.intro_image.get_rect(
                    midtop=(self.screen_size[0] // 2, 30)
                )
                print(f"INFO: Loaded intro image: {intro_path}")
            except Exception as e:
                print(f"WARNING: Failed to load intro image: {e}")
        else:
            print(f"WARNING: Intro image not found: {intro_path}")

    def _check_campaign_save(self) -> bool:
        """캠페인 저장 파일 존재 여부 확인"""
        save_path = Path("saves/campaign_progress.json")
        return save_path.exists()

    def _get_campaign_save_info(self) -> dict:
        """캠페인 저장 정보 로드"""
        import json
        save_path = Path("saves/campaign_progress.json")
        try:
            if save_path.exists():
                with open(save_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return {
                    "current_mission": data.get("current_mission", "act1_m1"),
                    "completed_missions": data.get("completed_missions", []),
                    "credits": data.get("credits", 0),
                    "current_act": data.get("current_act", 1),
                }
        except Exception as e:
            print(f"WARNING: Failed to load campaign save: {e}")
        return {}

    def _init_buttons(self):
        """버튼 초기화 - 새 게임 / 이어하기 / 설정 / 종료"""
        screen_width, screen_height = self.screen_size

        # 인트로 이미지 하단 기준으로 버튼 시작 위치 계산
        if self.intro_rect:
            start_y = self.intro_rect.bottom + 35
        else:
            start_y = int(screen_height * 0.55) + 35

        # 버튼 크기
        button_width = 320
        button_height = 55
        spacing = 18  # 버튼 간격

        center_x = screen_width // 2

        # 메인 버튼들 (세로 배치)
        self.buttons = {}

        # 새 게임 버튼 (항상 표시)
        self.buttons["new_game"] = {
            "rect": pygame.Rect(center_x - button_width // 2, start_y, button_width, button_height),
            "text": "NEW GAME",
            "desc": "Start a new adventure",
            "color": (60, 140, 200),  # 파란색
            "hover_color": (80, 170, 240),
        }

        # 이어하기 버튼 (저장된 진행이 있을 때만 활성화)
        continue_y = start_y + button_height + spacing
        self.buttons["continue"] = {
            "rect": pygame.Rect(center_x - button_width // 2, continue_y, button_width, button_height),
            "text": "CONTINUE",
            "desc": self._get_continue_desc(),
            "color": (60, 160, 100) if self.has_campaign_save else (60, 60, 70),
            "hover_color": (80, 200, 130) if self.has_campaign_save else (60, 60, 70),
            "enabled": self.has_campaign_save,
        }

        # 설정 버튼 (작은 버튼, 하단)
        settings_y = continue_y + button_height + spacing + 20
        settings_width = 140
        settings_height = 45

        self.buttons["settings"] = {
            "rect": pygame.Rect(center_x - settings_width - 15, settings_y, settings_width, settings_height),
            "text": "SETTINGS",
            "desc": "",
            "color": (80, 80, 100),
            "hover_color": (100, 100, 130),
        }

        # 종료 버튼
        self.buttons["quit"] = {
            "rect": pygame.Rect(center_x + 15, settings_y, settings_width, settings_height),
            "text": "QUIT",
            "desc": "",
            "color": (140, 60, 60),
            "hover_color": (180, 80, 80),
        }

    def _get_continue_desc(self) -> str:
        """이어하기 버튼 설명 텍스트"""
        if not self.has_campaign_save or not self.campaign_save_info:
            return "No save data"

        act = self.campaign_save_info.get("current_act", 1)
        mission = self.campaign_save_info.get("current_mission", "act1_m1")
        credits = self.campaign_save_info.get("credits", 0)

        return f"Act {act} - {credits} credits"

    def update(self, dt: float, current_time: float):
        """메인 메뉴 업데이트"""
        # 페이드인 효과
        if not self.fade_complete:
            self.fade_alpha += self.fade_speed * dt
            if self.fade_alpha >= 255:
                self.fade_alpha = 255
                self.fade_complete = True

        # 선택된 액션이 있으면 처리
        if self.selected_action:
            self._handle_action(self.selected_action)
            self.selected_action = None

    def _handle_action(self, action: str):
        """선택된 액션 처리"""
        if action == "new_game":
            self._start_new_game()
        elif action == "continue":
            self._continue_game()
        elif action == "settings":
            self._open_settings()
        elif action == "quit":
            self.request_quit()

    def _start_new_game(self):
        """새 게임 시작 → 오프닝 컷씬 → BaseHub"""
        from modes.base_hub_mode import BaseHubMode

        # 새 게임 플래그 설정
        self.engine.shared_state['is_new_game'] = True
        self.engine.shared_state['show_opening'] = True
        self.engine.shared_state['current_mission'] = "act1_m1"
        self.engine.shared_state['completed_missions'] = []
        self.engine.shared_state['current_act'] = 1

        # 기존 저장 데이터 초기화
        self._reset_campaign_save()

        # BaseHub로 이동 (오프닝 컷씬은 BaseHub에서 처리)
        self.request_push_mode(BaseHubMode)
        print("INFO: Starting new game → BaseHub")

    def _continue_game(self):
        """저장된 게임 이어하기"""
        from modes.base_hub_mode import BaseHubMode

        if not self.has_campaign_save:
            return

        # 저장된 진행 상태 로드
        self.engine.shared_state['is_new_game'] = False
        self.engine.shared_state['show_opening'] = False

        if self.campaign_save_info:
            self.engine.shared_state['current_mission'] = self.campaign_save_info.get("current_mission", "act1_m1")
            self.engine.shared_state['completed_missions'] = self.campaign_save_info.get("completed_missions", [])
            self.engine.shared_state['current_act'] = self.campaign_save_info.get("current_act", 1)
            self.engine.shared_state['global_score'] = self.campaign_save_info.get("credits", 0)

        self.request_push_mode(BaseHubMode)
        print("INFO: Continuing game from save")

    def _open_settings(self):
        """설정 화면 (TODO: 구현)"""
        print("INFO: Settings not implemented yet")

    def _reset_campaign_save(self):
        """캠페인 저장 데이터 초기화"""
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
            print("INFO: Campaign save reset")
        except Exception as e:
            print(f"WARNING: Failed to reset campaign save: {e}")

    def render(self, screen: pygame.Surface):
        """메인 메뉴 렌더링"""
        # 배경 (어두운 그라데이션)
        screen.fill((10, 10, 25))

        # 인트로 이미지 (페이드인)
        self._render_intro_image(screen)

        # 버튼 (페이드 완료 후에만 표시)
        if self.fade_alpha >= 200:
            ui_alpha = min(255, (self.fade_alpha - 200) * 4.6)
            self._render_buttons(screen, ui_alpha)

        # 치트 모드 표시
        if config_base.CHEAT_ENABLED and self.fade_complete:
            self._render_cheat_indicator(screen)

    def _render_intro_image(self, screen: pygame.Surface):
        """인트로 이미지 렌더링 (페이드인)"""
        if self.intro_image and self.intro_rect:
            # 페이드인 효과 적용
            if self.fade_alpha < 255:
                temp_image = self.intro_image.copy()
                temp_image.set_alpha(int(self.fade_alpha))
                screen.blit(temp_image, self.intro_rect)
            else:
                screen.blit(self.intro_image, self.intro_rect)

    def _render_buttons(self, screen: pygame.Surface, alpha: float = 255):
        """메인 버튼 렌더링 (새 게임 / 이어하기 / 설정 / 종료)"""
        mouse_pos = pygame.mouse.get_pos()

        for action, button_info in self.buttons.items():
            rect = button_info["rect"]
            enabled = button_info.get("enabled", True)
            is_hover = rect.collidepoint(mouse_pos) and enabled

            # 버튼 배경 Surface 생성 (알파 지원)
            btn_surface = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)

            # 버튼 색상
            base_color = button_info.get("hover_color" if is_hover else "color", (60, 80, 120))
            if not enabled:
                base_color = (50, 50, 60)  # 비활성화 색상

            bg_color = (*base_color, int(alpha * 0.85))
            border_color = tuple(min(255, c + 40) for c in base_color) + (int(alpha),)

            # 버튼 그리기
            pygame.draw.rect(btn_surface, bg_color, (0, 0, rect.width, rect.height), border_radius=10)
            pygame.draw.rect(btn_surface, border_color, (0, 0, rect.width, rect.height), 2, border_radius=10)

            # 호버 효과: 상단 하이라이트
            if is_hover:
                highlight = pygame.Surface((rect.width - 8, 3), pygame.SRCALPHA)
                highlight.fill((255, 255, 255, int(alpha * 0.4)))
                btn_surface.blit(highlight, (4, 4))

            screen.blit(btn_surface, rect.topleft)

            # 텍스트 색상
            text_color = (255, 255, 255) if enabled else (120, 120, 130)

            # 메인 텍스트
            text = self.fonts["medium"].render(button_info["text"], True, text_color)
            text.set_alpha(int(alpha))

            # 설명이 있으면 텍스트를 위로 올리고 설명 추가
            desc = button_info.get("desc", "")
            if desc:
                text_rect = text.get_rect(centerx=rect.centerx, centery=rect.centery - 8)
                screen.blit(text, text_rect)

                # 설명 텍스트 (작게)
                desc_color = (180, 180, 190) if enabled else (90, 90, 100)
                desc_text = self.fonts["small"].render(desc, True, desc_color)
                desc_text.set_alpha(int(alpha * 0.8))
                desc_rect = desc_text.get_rect(centerx=rect.centerx, centery=rect.centery + 12)
                screen.blit(desc_text, desc_rect)
            else:
                text_rect = text.get_rect(center=rect.center)
                screen.blit(text, text_rect)

    def _render_cheat_indicator(self, screen: pygame.Surface):
        """치트 모드 표시"""
        cheat_text = self.fonts["small"].render("CHEAT MODE", True, (255, 255, 0))
        cheat_rect = cheat_text.get_rect(bottomright=(self.screen_size[0] - 20, self.screen_size[1] - 20))
        screen.blit(cheat_text, cheat_rect)

    def handle_event(self, event: pygame.event.Event):
        """이벤트 처리"""
        # 페이드인 완료 전에는 입력 무시
        if self.fade_alpha < 200:
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = event.pos

            # 버튼 클릭 확인
            for action, button_info in self.buttons.items():
                enabled = button_info.get("enabled", True)
                if button_info["rect"].collidepoint(mouse_pos) and enabled:
                    self.selected_action = action
                    if hasattr(self, 'sound_manager') and self.sound_manager:
                        self.sound_manager.play_sfx("select")
                    return

        elif event.type == pygame.KEYDOWN:
            # 단축키
            if event.key == pygame.K_n:  # N: New Game
                self.selected_action = "new_game"
            elif event.key == pygame.K_c and self.has_campaign_save:  # C: Continue
                self.selected_action = "continue"
            elif event.key == pygame.K_ESCAPE:  # ESC: Quit
                self.request_quit()
            elif event.key == pygame.K_RETURN:  # Enter: New Game (기본)
                self.selected_action = "new_game"


print("INFO: main_menu_mode.py loaded (Unified Flow)")
