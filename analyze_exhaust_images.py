"""
배기가스 이미지 분석 도구
투명도 분포, 밝기 분포, 실제 컨텐츠 영역 확인
"""
import pygame
import numpy as np
from pathlib import Path

# Pygame 초기화
pygame.init()
# Display surface 생성 (convert_alpha를 위해 필요)
screen = pygame.display.set_mode((100, 100))

# 이미지 경로
ASSET_DIR = Path("assets")
gas1_path = ASSET_DIR / "images" / "effects" / "gas_effect_01.png"
gas2_path = ASSET_DIR / "images" / "effects" / "gas_effect_02.png"

def analyze_image(image_path, name):
    """이미지 분석"""
    print(f"\n{'='*60}")
    print(f"분석: {name} ({image_path.name})")
    print(f"{'='*60}")

    # 이미지 로드
    img = pygame.image.load(str(image_path)).convert_alpha()
    width, height = img.get_size()
    print(f"이미지 크기: {width} x {height}")

    # 픽셀 배열로 변환
    pixels = pygame.surfarray.array3d(img)  # RGB
    alpha = pygame.surfarray.array_alpha(img)  # Alpha

    # 알파 채널 분석
    print(f"\n[알파 채널 분석]")
    print(f"최소 알파: {alpha.min()}")
    print(f"최대 알파: {alpha.max()}")
    print(f"평균 알파: {alpha.mean():.2f}")

    # 불투명한 픽셀(알파 > 10) 찾기
    opaque_mask = alpha > 10
    if opaque_mask.any():
        opaque_y, opaque_x = np.where(opaque_mask.T)  # Transpose for correct orientation

        print(f"\n[불투명한 영역 (알파 > 10)]")
        print(f"상단 경계 (y_min): {opaque_y.min()} ({opaque_y.min()/height*100:.1f}%)")
        print(f"하단 경계 (y_max): {opaque_y.max()} ({opaque_y.max()/height*100:.1f}%)")
        print(f"좌측 경계 (x_min): {opaque_x.min()} ({opaque_x.min()/width*100:.1f}%)")
        print(f"우측 경계 (x_max): {opaque_x.max()} ({opaque_x.max()/width*100:.1f}%)")

        content_height = opaque_y.max() - opaque_y.min() + 1
        content_width = opaque_x.max() - opaque_x.min() + 1
        print(f"실제 컨텐츠 크기: {content_width} x {content_height}")
        print(f"컨텐츠 비율: {content_width/width*100:.1f}% x {content_height/height*100:.1f}%")

    # 밝기 분석 (불투명한 픽셀만)
    if opaque_mask.any():
        print(f"\n[밝기 분석 (불투명한 픽셀만)]")

        # 상단 10% 영역의 평균 밝기
        top_10_line = int(opaque_y.min() + content_height * 0.1)
        y_coords = np.arange(height)[:, None]
        x_coords = np.arange(width)[None, :]

        top_mask = (alpha.T > 10) & (y_coords <= top_10_line)
        if top_mask.any():
            # RGB 채널 평균
            top_pixels = []
            for c in range(3):
                top_pixels.append(pixels[:, :, c].T[top_mask])
            top_brightness = np.mean([np.mean(ch) for ch in top_pixels if len(ch) > 0])
            print(f"상단 10% 평균 밝기: {top_brightness:.1f}")

        # 하단 10% 영역의 평균 밝기
        bottom_10_line = int(opaque_y.max() - content_height * 0.1)
        bottom_mask = (alpha.T > 10) & (y_coords >= bottom_10_line)
        if bottom_mask.any():
            bottom_pixels = []
            for c in range(3):
                bottom_pixels.append(pixels[:, :, c].T[bottom_mask])
            bottom_brightness = np.mean([np.mean(ch) for ch in bottom_pixels if len(ch) > 0])
            print(f"하단 10% 평균 밝기: {bottom_brightness:.1f}")

        # 중앙의 평균 밝기
        center_y = (opaque_y.min() + opaque_y.max()) // 2
        center_mask = (alpha.T > 10) & (np.abs(y_coords - center_y) < content_height * 0.1)
        if center_mask.any():
            center_pixels = []
            for c in range(3):
                center_pixels.append(pixels[:, :, c].T[center_mask])
            center_brightness = np.mean([np.mean(ch) for ch in center_pixels if len(ch) > 0])
            print(f"중앙 평균 밝기: {center_brightness:.1f}")

    # 수직 분포 분석 (10등분)
    print(f"\n[수직 밝기 분포 (10등분)]")
    print("위치(%)  | 평균 알파 | 평균 밝기")
    print("-" * 40)

    for i in range(10):
        y_start = int(height * i / 10)
        y_end = int(height * (i + 1) / 10)

        # 해당 y 범위의 알파 값
        section_alpha = alpha[:, y_start:y_end]

        if section_alpha.size > 0:
            avg_alpha = section_alpha.mean()

            # 밝기는 불투명한 픽셀만
            opaque_pixels = section_alpha > 10
            if opaque_pixels.any():
                section_pixels = []
                for c in range(3):
                    channel = pixels[:, y_start:y_end, c]
                    section_pixels.append(channel[opaque_pixels])
                avg_brightness = np.mean([np.mean(ch) for ch in section_pixels if len(ch) > 0])
            else:
                avg_brightness = 0

            print(f"{i*10:3d}-{(i+1)*10:3d}% | {avg_alpha:9.1f} | {avg_brightness:9.1f}")

# 분석 실행
if gas1_path.exists():
    analyze_image(gas1_path, "화염 배기가스 (gas_effect_01)")
else:
    print(f"ERROR: {gas1_path} not found")

if gas2_path.exists():
    analyze_image(gas2_path, "플라즈마 배기가스 (gas_effect_02)")
else:
    print(f"ERROR: {gas2_path} not found")

print(f"\n{'='*60}")
print("분석 완료!")
print(f"{'='*60}")
