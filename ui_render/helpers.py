# ui_render/helpers.py
# Helper functions and classes for UI rendering

import pygame
import math
from typing import Tuple
import config


# =========================================================
# 폰트 헬퍼 함수 - 인라인 폰트 대신 중앙 관리 폰트 사용
# =========================================================
def get_font(size_key: str) -> pygame.font.Font:
    """
    중앙 관리 폰트를 반환합니다.
    config.UI_FONTS가 초기화되지 않았으면 인라인 폰트 생성 (폴백)

    size_key: "huge", "large", "medium", "small", "tiny", "micro",
              "mega", "ultra", "icon",
              "light_large", "light_medium", "light_small", etc.
    """
    if config.UI_FONTS and size_key in config.UI_FONTS:
        return config.UI_FONTS[size_key]

    # 폴백: 아직 초기화 안됐으면 기본 폰트 사용
    fallback_sizes = {
        "ultra": 100, "mega": 72, "icon": 50, "huge": 48,
        "large": 36, "medium": 24, "small": 20, "tiny": 18, "micro": 15
    }
    # light_ 접두사 제거 후 크기 찾기
    base_key = size_key.replace("light_", "").replace("regular_", "")
    size = fallback_sizes.get(base_key, 24)
    return pygame.font.Font(None, size)


# =========================================================
# 0. 이모지 렌더링 헬퍼 함수
# =========================================================

def render_text_with_emoji(
    text: str,
    font: pygame.font.Font,
    color: Tuple[int, int, int],
    emoji_font_size: str = "MEDIUM"
) -> pygame.Surface:
    """
    이모지와 일반 텍스트를 분리해서 렌더링하고 합칩니다.
    emoji_font_size: "SMALL", "MEDIUM", "LARGE", "HUGE" 중 하나
    """
    # config에서 이모지 폰트 가져오기
    emoji_font = config.EMOJI_FONTS.get(emoji_font_size, None)

    if emoji_font is None or not config.EMOJI_FONTS:
        # 이모지 폰트가 없으면 일반 폰트로만 렌더링
        return font.render(text, True, color)

    # config.UI_ICONS의 모든 이모지를 집합으로 만들기
    emoji_chars = set(config.UI_ICONS.values())
    # 별 문자도 추가 (★ ☆)
    emoji_chars.add("★")
    emoji_chars.add("☆")

    # 이모지와 일반 텍스트를 분리
    parts = []
    current_text = ""
    current_emoji = ""

    i = 0
    while i < len(text):
        char = text[i]
        char_code = ord(char)

        # 이모지인지 확인: config.UI_ICONS에 있거나, 넓은 유니코드 범위
        is_emoji = (
            char in emoji_chars or  # config에 정의된 이모지
            char_code > 0x1F000 or  # 이모지 유니코드 범위
            (0x2000 <= char_code <= 0x2BFF) or  # Miscellaneous Symbols
            char_code == 0xFE0F  # Variation Selector (이모지 변형)
        )

        if is_emoji:
            # 일반 텍스트가 있으면 저장
            if current_text:
                parts.append(("text", current_text))
                current_text = ""

            # 이모지 수집 (variation selector 포함 가능)
            current_emoji = char
            # 다음 문자가 variation selector면 포함
            if i + 1 < len(text) and ord(text[i + 1]) == 0xFE0F:
                current_emoji += text[i + 1]
                i += 1  # variation selector 건너뛰기

            parts.append(("emoji", current_emoji))
            current_emoji = ""
        else:
            current_text += char

        i += 1

    if current_text:
        parts.append(("text", current_text))

    # 각 부분을 렌더링
    surfaces = []
    for part_type, content in parts:
        if part_type == "emoji":
            surf = emoji_font.render(content, True, color)
        else:
            surf = font.render(content, True, color)
        surfaces.append(surf)

    # 하나의 Surface로 합치기
    if not surfaces:
        return font.render("", True, color)

    total_width = sum(s.get_width() for s in surfaces)
    max_height = max(s.get_height() for s in surfaces)

    combined = pygame.Surface((total_width, max_height), pygame.SRCALPHA)
    combined.fill((0, 0, 0, 0))  # 투명 배경

    x = 0
    for surf in surfaces:
        # 세로 중앙 정렬
        y = (max_height - surf.get_height()) // 2
        combined.blit(surf, (x, y))
        x += surf.get_width()

    return combined


# =========================================================
# HPBarShake 클래스 (피격 시 HP바 흔들림 효과)
# =========================================================

class HPBarShake:
    """
    데미지를 받았을 때 HP바가 흔들리는 효과를 관리하는 클래스.
    데미지 비율에 따라 흔들림 강도가 조절됩니다.
    """
    def __init__(self):
        self.is_active = False
        self.start_time = 0.0
        self.duration = 0.3  # 0.3초 지속
        self.intensity = 0  # 흔들림 강도 (픽셀)
        self.offset_x = 0
        self.offset_y = 0

    def trigger(self, damage_ratio: float):
        """
        흔들림 효과를 트리거합니다.

        Args:
            damage_ratio: 받은 데미지 / 최대 HP 비율 (0.0 ~ 1.0)
        """
        self.is_active = True
        self.start_time = pygame.time.get_ticks() / 1000.0
        # 데미지 비율에 따른 흔들림 강도 (3 ~ 10 픽셀)
        self.intensity = int(3 + damage_ratio * 7)

    def update(self) -> Tuple[int, int]:
        """
        흔들림 효과를 업데이트하고 오프셋을 반환합니다.

        Returns:
            Tuple[int, int]: (offset_x, offset_y) 흔들림 오프셋
        """
        if not self.is_active:
            return (0, 0)

        current_time = pygame.time.get_ticks() / 1000.0
        elapsed = current_time - self.start_time

        if elapsed >= self.duration:
            self.is_active = False
            self.offset_x = 0
            self.offset_y = 0
            return (0, 0)

        # 점점 감소하는 진폭
        progress = elapsed / self.duration
        decay = 1.0 - progress
        current_intensity = int(self.intensity * decay)

        # 빠른 주기로 흔들림 (사인파 기반)
        shake_speed = 50  # 흔들림 속도
        self.offset_x = int(math.sin(elapsed * shake_speed) * current_intensity)
        self.offset_y = int(math.cos(elapsed * shake_speed * 0.7) * current_intensity * 0.5)

        return (self.offset_x, self.offset_y)

    def get_offset(self) -> Tuple[int, int]:
        """현재 흔들림 오프셋을 반환합니다."""
        return (self.offset_x, self.offset_y)
