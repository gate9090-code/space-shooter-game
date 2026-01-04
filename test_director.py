import pygame
import config
from pathlib import Path

pygame.init()

# 이미지 경로 확인
director_path = config.ASSET_DIR / "images" / "ui" / "training_director.png"
print(f"Looking for: {director_path}")
print(f"Exists: {director_path.exists()}")

if director_path.exists():
    try:
        img = pygame.image.load(str(director_path))
        print(f"Image loaded successfully!")
        print(f"Size: {img.get_size()}")
        print(f"Has alpha: {img.get_flags() & pygame.SRCALPHA}")
    except Exception as e:
        print(f"ERROR loading: {e}")
else:
    print("File not found!")
    # 다른 경로 시도
    alt_path = Path("assets/images/ui/training_director.png")
    print(f"Alternative path exists: {alt_path.exists()}")

pygame.quit()
