# main.py
"""
리팩토링된 메인 진입점
GameEngine + 모드 시스템 사용
Timeline 테스트를 위한 첫 번째 수정
"""

import pygame
import sys
from pathlib import Path

import config
from asset_manager import AssetManager
from engine.game_engine import GameEngine
from modes.intro_video_mode import IntroVideoMode


# =========================================================
# 데이터 저장/로드/삭제 함수
# =========================================================

SAVE_FILE_PATH = Path("save_data.json")


def load_game_data():
    """저장된 영구 업그레이드 및 코인 데이터를 로드합니다."""
    import json
사
    default_upgrades = config.INITIAL_PLAYER_UPGRADES
    default_score = 0
    default_ship = "FIGHTER"
    default_inventory = {}

    if SAVE_FILE_PATH.exists():
        try:
            with open(SAVE_FILE_PATH, "r") as f:
                data = json.load(f)

            upgrades = data.get("player_upgrades", default_upgrades)
            score = data.get("score", default_score)
            ship = data.get("current_ship", default_ship)
            inventory = data.get("player_inventory", default_inventory)

            for key, val in default_upgrades.items():
                if key not in upgrades:
                    upgrades[key] = val

            print(f"INFO: Game data loaded from {SAVE_FILE_PATH}")
            return upgrades, score, ship, inventory

        except Exception as e:
            print(f"WARNING: Could not load game data: {e}")
            return default_upgrades, default_score, default_ship, default_inventory
    else:
        print("INFO: No save file found. Loading default data.")
        return default_upgrades, default_score, default_ship, default_inventory


def save_game_data(
    score: int,
    player_upgrades: dict,
    current_ship: str = "FIGHTER",
    player_inventory: dict = None,
):
    """현재 영구 업그레이드 및 코인 데이터를 저장합니다."""
    import json

    if player_inventory is None:
        player_inventory = {}

    data = {
        "score": score,
        "player_upgrades": player_upgrades,
        "current_ship": current_ship,
        "player_inventory": player_inventory,
    }

    try:
        with open(SAVE_FILE_PATH, "w") as f:
            json.dump(data, f, indent=4)
        print(f"INFO: Game data saved to {SAVE_FILE_PATH}")
    except Exception as e:
        print(f"ERROR: Could not save game data: {e}")


def delete_save_file():
    """저장 파일을 삭제합니다."""
    if SAVE_FILE_PATH.exists():
        try:
            SAVE_FILE_PATH.unlink()
            print(f"INFO: Save file deleted: {SAVE_FILE_PATH}")
        except Exception as e:
            print(f"ERROR: Could not delete save file: {e}")


# =========================================================
# 메인 실행
# =========================================================


def main():
    """메인 함수"""
    # 1. Pygame 초기화
    pygame.init()

    # 2. 화면 설정 (전체 화면)
    info = pygame.display.Info()
    screen_size = (info.current_w, info.current_h)
    screen = pygame.display.set_mode(screen_size, pygame.FULLSCREEN)
    pygame.display.set_caption("Space Shooter")

    print(f"INFO: Screen initialized at {screen_size}")

    # 3. 필수 자원 폴더 생성
    try:
        config.ASSET_DIR.mkdir(exist_ok=True)
        config.IMAGE_DIR.mkdir(exist_ok=True)
        config.FONT_DIR.mkdir(exist_ok=True)
        config.BACKGROUND_DIR.mkdir(exist_ok=True)
        print("INFO: Asset folders ready")
    except Exception as e:
        print(f"ERROR: Could not create asset folders: {e}")
        pygame.quit()
        sys.exit(1)

    # 4. 자원 관리자 초기화
    asset_manager = AssetManager()

    # 5. 게임 엔진 생성
    engine = GameEngine(screen, asset_manager)

    # 6. 저장 데이터 로드
    upgrades, score, ship, inventory = load_game_data()
    engine.shared_state["player_upgrades"] = upgrades
    engine.shared_state["global_score"] = score
    engine.shared_state["current_ship"] = ship
    engine.shared_state["player_inventory"] = inventory

    # 7. 인트로 영상으로 시작 (영상 완료 후 메인 메뉴로 전환)
    engine.push_mode(IntroVideoMode)

    # 8. 게임 루프 실행
    print("INFO: Starting game loop")
    engine.run()

    # 9. 종료시 저장
    save_game_data(
        engine.shared_state.get("global_score", 0),
        engine.shared_state.get("player_upgrades", {}),
        engine.shared_state.get("current_ship", "FIGHTER"),
        engine.shared_state.get("player_inventory", {}),
    )

    # 10. 정리
    pygame.quit()
    print("INFO: Game ended")


if __name__ == "__main__":
    main()
