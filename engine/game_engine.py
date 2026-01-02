# engine/game_engine.py
"""
GameEngine - 게임 엔진 코어
모드 스택 관리 및 메인 게임 루프 담당
"""

import pygame
import sys
from typing import List, Dict, Any, Optional, Type
from pathlib import Path

# 상위 디렉토리 임포트를 위한 경로 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

import config
from asset_manager import AssetManager
from sound_manager import SoundManager


class GameEngine:
    """
    게임 엔진 - 모드 스택 관리 및 메인 루프

    기능:
    - 모드 스택 관리 (push, pop, switch)
    - 공유 상태 관리 (모드 간 데이터 전달)
    - 메인 게임 루프 실행
    """

    def __init__(self, screen: pygame.Surface, asset_manager: AssetManager):
        """
        게임 엔진 초기화

        Args:
            screen: pygame 화면 Surface
            asset_manager: 에셋 관리자
        """
        self.screen = screen
        self.asset_manager = asset_manager
        self.screen_size = screen.get_size()

        # 사운드 매니저
        self.sound_manager = SoundManager()

        # 모드 스택 (LIFO)
        self.mode_stack: List["GameMode"] = []

        # 실행 상태
        self.running = True

        # 공유 상태 (모드 간 데이터 전달용)
        self.shared_state: Dict[str, Any] = {
            "player_data": None,          # 플레이어 상태 공유
            "global_score": 0,            # 전역 점수 (코인)
            "player_upgrades": {},        # 영구 업그레이드
            "unlocked_skills": [],        # 해금된 스킬
            "unlocked_modes": ["wave"],   # 해금된 모드
        }

        # 폰트 초기화
        self._init_fonts()

        print("INFO: GameEngine initialized")

    def _init_fonts(self):
        """폰트 초기화"""
        screen_height = self.screen_size[1]

        # =========================================================
        # 폰트 카테고리 시스템
        # =========================================================
        # 1. Bold (제목/강조): huge, large, medium, small
        # 2. Regular (일반): regular_*, 상태 정보용
        # 3. Light (설명/본문): light_*, desc_*, 가독성 향상
        # =========================================================
        self.fonts = {
            # === Bold 폰트 (제목, 레이블, 강조) ===
            "huge": self.asset_manager.get_font(int(screen_height * config.FONT_SIZE_RATIOS["HUGE"])),
            "large": self.asset_manager.get_font(int(screen_height * config.FONT_SIZE_RATIOS["LARGE"])),
            "medium": self.asset_manager.get_font(int(screen_height * config.FONT_SIZE_RATIOS["MEDIUM"])),
            "small": self.asset_manager.get_font(int(screen_height * config.FONT_SIZE_RATIOS["SMALL"])),
            "tiny": self.asset_manager.get_font(int(screen_height * config.FONT_SIZE_RATIOS["TINY"])),
            "micro": self.asset_manager.get_font(int(screen_height * config.FONT_SIZE_RATIOS["MICRO"])),

            # === 효과/특수 폰트 (게임 이펙트용) ===
            "mega": self.asset_manager.get_font(int(screen_height * config.FONT_SIZE_RATIOS["MEGA"])),
            "ultra": self.asset_manager.get_font(int(screen_height * config.FONT_SIZE_RATIOS["ULTRA"])),
            "icon": self.asset_manager.get_font(int(screen_height * config.FONT_SIZE_RATIOS["ICON"])),

            # === Regular 폰트 (일반 텍스트) ===
            "regular_large": self.asset_manager.get_regular_font(int(screen_height * config.FONT_SIZE_RATIOS["LARGE"])),
            "regular_medium": self.asset_manager.get_regular_font(int(screen_height * config.FONT_SIZE_RATIOS["MEDIUM"])),
            "regular_small": self.asset_manager.get_regular_font(int(screen_height * config.FONT_SIZE_RATIOS["SMALL"])),

            # === Light 폰트 (설명, 본문 - 가독성 향상) ===
            "light_large": self.asset_manager.get_light_font(int(screen_height * config.FONT_SIZE_RATIOS["LARGE"])),
            "light_medium": self.asset_manager.get_light_font(int(screen_height * config.FONT_SIZE_RATIOS["MEDIUM"])),
            "light_small": self.asset_manager.get_light_font(int(screen_height * config.FONT_SIZE_RATIOS["SMALL"])),
            "light_tiny": self.asset_manager.get_light_font(int(screen_height * config.FONT_SIZE_RATIOS["TINY"])),
            "light_micro": self.asset_manager.get_light_font(int(screen_height * config.FONT_SIZE_RATIOS["MICRO"])),

            # === 대화창 전용 (더 작은 크기) ===
            "dialogue_medium": self.asset_manager.get_light_font(int(screen_height * config.FONT_SIZE_RATIOS["SMALL"])),
            "dialogue_small": self.asset_manager.get_light_font(int(screen_height * config.FONT_SIZE_RATIOS["TINY"])),

            # === 설명 텍스트 전용 별칭 (가독성 코드용) ===
            "desc": self.asset_manager.get_light_font(int(screen_height * config.FONT_SIZE_RATIOS["SMALL"])),
            "desc_medium": self.asset_manager.get_light_font(int(screen_height * config.FONT_SIZE_RATIOS["MEDIUM"])),
        }

        # 이모지 폰트 (config에 저장)
        config.EMOJI_FONTS["SMALL"] = self.asset_manager.get_emoji_font(
            int(screen_height * config.FONT_SIZE_RATIOS["SMALL"])
        )
        config.EMOJI_FONTS["MEDIUM"] = self.asset_manager.get_emoji_font(
            int(screen_height * config.FONT_SIZE_RATIOS["MEDIUM"])
        )
        config.EMOJI_FONTS["LARGE"] = self.asset_manager.get_emoji_font(
            int(screen_height * config.FONT_SIZE_RATIOS["LARGE"])
        )
        config.EMOJI_FONTS["HUGE"] = self.asset_manager.get_emoji_font(
            int(screen_height * config.FONT_SIZE_RATIOS["HUGE"])
        )

        # UI 폰트 캐시 (ui.py에서 인라인 폰트 대신 사용)
        config.UI_FONTS = self.fonts.copy()

    @property
    def current_mode(self) -> Optional["GameMode"]:
        """현재 활성 모드 반환"""
        return self.mode_stack[-1] if self.mode_stack else None

    def push_mode(self, mode_class: Type["GameMode"], **kwargs):
        """
        새 모드를 스택에 추가 (현재 모드 일시정지)

        Args:
            mode_class: 추가할 모드 클래스
            **kwargs: 모드 초기화 인자
        """
        # 현재 모드 일시정지
        if self.current_mode:
            self.current_mode.on_pause()

        # 새 모드 생성 및 초기화
        new_mode = mode_class(
            engine=self,
            **kwargs
        )
        new_mode.init()
        self.mode_stack.append(new_mode)
        new_mode.on_enter()

        print(f"INFO: Pushed {mode_class.__name__}, stack depth: {len(self.mode_stack)}")

    def pop_mode(self, return_data: Optional[Dict] = None):
        """
        현재 모드 종료, 이전 모드로 복귀

        Args:
            return_data: 이전 모드에 전달할 데이터
        """
        if len(self.mode_stack) <= 1:
            print("WARNING: Cannot pop last mode, use switch_mode or quit")
            return

        # 현재 모드 정리
        exiting_mode = self.mode_stack.pop()
        exiting_mode.on_exit()

        # 이전 모드 재개
        if self.current_mode:
            self.current_mode.on_resume(return_data)

        print(f"INFO: Popped to {self.current_mode.__class__.__name__ if self.current_mode else 'None'}")

    def switch_mode(self, mode_class: Type["GameMode"], **kwargs):
        """
        현재 모드를 완전히 교체 (상태 보존 안함)

        Args:
            mode_class: 전환할 모드 클래스
            **kwargs: 모드 초기화 인자
        """
        # 전환 중 커서 깜빡임 방지 - 숨긴 상태 유지
        pygame.mouse.set_visible(False)

        # 모든 모드 정리
        while self.mode_stack:
            mode = self.mode_stack.pop()
            mode.on_exit()

        # 새 모드 시작
        self.push_mode(mode_class, **kwargs)

        print(f"INFO: Switched to {mode_class.__name__}")

    def quit(self):
        """게임 종료"""
        self.running = False
        print("INFO: Game quit requested")

    def run(self):
        """메인 게임 루프"""
        clock = pygame.time.Clock()

        while self.running and self.current_mode:
            try:
                # 델타 타임 계산
                raw_dt = clock.tick(config.FPS) / 1000.0
                current_time = pygame.time.get_ticks() / 1000.0

                # 이벤트 처리
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False
                    elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                        # ESC 키로 언제나 게임 종료
                        print("INFO: ESC key pressed - Exiting game")
                        self.running = False
                    else:
                        # 현재 모드에 이벤트 전달
                        try:
                            self.current_mode.handle_event(event)
                        except Exception as e:
                            print(f"ERROR: Exception in handle_event: {e}")
                            import traceback
                            traceback.print_exc()

                # 현재 모드 업데이트
                try:
                    self.current_mode.update(raw_dt, current_time)
                except Exception as e:
                    print(f"ERROR: Exception in update: {e}")
                    import traceback
                    traceback.print_exc()

                # 화면 렌더링
                try:
                    self.current_mode.render(self.screen)
                except Exception as e:
                    print(f"ERROR: Exception in render: {e}")
                    import traceback
                    traceback.print_exc()

                # 화면 업데이트
                pygame.display.flip()

            except Exception as e:
                print(f"ERROR: Unhandled exception in game loop: {e}")
                import traceback
                traceback.print_exc()

        # 종료 원인 디버깅
        if not self.running:
            print("INFO: Game loop ended (running=False)")
        elif not self.current_mode:
            print("INFO: Game loop ended (current_mode=None)")
        else:
            print("INFO: Game loop ended (unknown reason)")

    def load_shared_state(self):
        """저장된 공유 상태 로드"""
        from main import load_game_data  # 순환 참조 방지

        upgrades, score, ship, inventory = load_game_data()
        self.shared_state["player_upgrades"] = upgrades
        self.shared_state["global_score"] = score
        self.shared_state["current_ship"] = ship
        self.shared_state["player_inventory"] = inventory

        print(f"INFO: Loaded shared state - Score: {score}")

    def save_shared_state(self):
        """공유 상태 저장"""
        from main import save_game_data  # 순환 참조 방지

        save_game_data(
            self.shared_state.get("global_score", 0),
            self.shared_state.get("player_upgrades", {}),
            self.shared_state.get("current_ship", "FIGHTER"),
            self.shared_state.get("player_inventory", {})
        )

        print("INFO: Saved shared state")


# GameMode 타입 힌트를 위한 전방 선언
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from modes.base_mode import GameMode
