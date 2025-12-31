# objects.py

import pygame
import math
from typing import Tuple, List, Callable, Dict, Optional
from pathlib import Path
import config
from asset_manager import AssetManager
import random

# Core entities imported from entities.core
from entities.core import Weapon, Player, Enemy, Boss, Bullet

# Screen effects imported from effects.screen_effects
from effects.screen_effects import (
    Particle, ScreenFlash, ScreenShake,
    DamageFlash, LevelUpEffect,
    DynamicTextEffect, ReviveTextEffect,
    NebulaParticle, SmokeParticle, BurstParticle,
    DissolveEffect, FadeEffect, ImplodeEffect, TimeSlowEffect
)
# Core entities imported from entities.core
from entities.core import Weapon, Player, Enemy, Boss, Bullet


# =========================================================
# 공통 베이스 클래스: 컷씬 효과용
# =========================================================
class BaseCutsceneEffect:
    """
    모든 컷씬 효과 클래스의 공통 베이스 클래스

    공통 기능:
    - 페이즈 관리 (FADEIN, DISPLAY, DIALOGUE, FADEOUT, DONE)
    - 배경 이미지 로딩
    - 대화 시스템 (타이핑 효과, 클릭 진행)
    - 페이드 인/아웃
    - 이벤트 처리
    - 폰트 관리
    """

    # 공통 페이즈 상수
    PHASE_FADEIN = 0
    PHASE_DISPLAY = 1
    PHASE_DIALOGUE = 2
    PHASE_FADEOUT = 3
    PHASE_DONE = 4

    def __init__(self, screen_size: tuple, background_path: str = None,
                 dialogue_after: list = None, sound_manager=None,
                 special_effects: dict = None, scene_id: str = "base_scene"):
        """
        Args:
            screen_size: 화면 크기 (width, height)
            background_path: 배경 이미지 경로
            dialogue_after: 대사 리스트 [{"speaker": "...", "text": "..."}, ...]
            sound_manager: 효과음 재생용
            special_effects: 특수 효과 설정
            scene_id: 씬 식별자 (리플레이용)
        """
        self.screen_size = screen_size
        self.background_path = background_path
        self.dialogue_after = dialogue_after or []
        self.sound_manager = sound_manager
        self.special_effects = special_effects or {}
        self.scene_id = scene_id

        self.is_alive = True
        self.phase = self.PHASE_FADEIN
        self.phase_timer = 0.0

        # 페이드 설정
        self.fadein_duration = 1.5
        self.fadeout_duration = 1.5
        self.fade_alpha = 0.0

        # 배경
        self.background = None
        if background_path:
            self._load_background(background_path)

        # 대화 관련
        self.current_dialogue_index = 0
        self.dialogue_text = ""
        self.typing_progress = 0.0
        self.typing_speed = 30.0
        self.waiting_for_click = False

        # 초상화 캐시
        self.portrait_cache = {}

        # 폰트
        self.fonts = {}

        # 콜백
        self.on_complete = None
        self.on_replay_request = None

    def _load_background(self, path: str, overlay_alpha: int = 0):
        """
        배경 이미지 로드

        Args:
            path: 이미지 경로
            overlay_alpha: 어두운 오버레이 알파값 (0=없음, 220=어둡게)
        """
        try:
            img = pygame.image.load(path).convert()
            self.background = pygame.transform.smoothscale(img, self.screen_size)

            if overlay_alpha > 0:
                overlay = pygame.Surface(self.screen_size, pygame.SRCALPHA)
                overlay.fill((0, 0, 0, overlay_alpha))
                self.background.blit(overlay, (0, 0))
        except Exception as e:
            print(f"WARNING: Failed to load background: {path} - {e}")
            self.background = pygame.Surface(self.screen_size)
            self.background.fill((20, 20, 30))

    def set_fonts(self, fonts: dict):
        """폰트 설정"""
        self.fonts = fonts

    def _get_portrait(self, speaker: str) -> pygame.Surface:
        """초상화 이미지 가져오기 (캐시 사용)"""
        if speaker in self.portrait_cache:
            return self.portrait_cache[speaker]

        try:
            from mode_configs.config_story_dialogue import CHARACTER_PORTRAITS
            path = CHARACTER_PORTRAITS.get(speaker)
        except ImportError:
            path = None

        if path:
            try:
                img = pygame.image.load(path).convert_alpha()
                target_size = (120, 120)
                img = pygame.transform.smoothscale(img, target_size)
                self.portrait_cache[speaker] = img
                return img
            except Exception as e:
                print(f"WARNING: Failed to load portrait for {speaker}: {e}")

        return None

    def _start_dialogue(self):
        """현재 대화 시작"""
        if self.current_dialogue_index < len(self.dialogue_after):
            self.dialogue_text = self.dialogue_after[self.current_dialogue_index].get("text", "")
            self.typing_progress = 0.0
            self.waiting_for_click = False

    def _update_dialogue(self, dt: float):
        """대화 업데이트 (타이핑 효과)"""
        if self.current_dialogue_index >= len(self.dialogue_after):
            return True  # 대화 완료

        if not self.waiting_for_click:
            self.typing_progress += dt * self.typing_speed
            if self.typing_progress >= len(self.dialogue_text):
                self.typing_progress = len(self.dialogue_text)
                self.waiting_for_click = True

        return False  # 대화 진행 중

    def _advance_dialogue(self):
        """다음 대화로 진행"""
        self.current_dialogue_index += 1
        if self.current_dialogue_index < len(self.dialogue_after):
            self._start_dialogue()
            return False  # 더 있음
        return True  # 대화 완료

    def _update_fadein(self, dt: float) -> bool:
        """페이드인 업데이트. 완료 시 True 반환"""
        progress = min(1.0, self.phase_timer / self.fadein_duration)
        self.fade_alpha = progress * 255
        return progress >= 1.0

    def _update_fadeout(self, dt: float) -> bool:
        """페이드아웃 업데이트. 완료 시 True 반환"""
        progress = min(1.0, self.phase_timer / self.fadeout_duration)
        self.fade_alpha = 255 * (1.0 - progress)
        return progress >= 1.0

    def update(self, dt: float):
        """업데이트 - 서브클래스에서 확장"""
        if not self.is_alive:
            return

        self.phase_timer += dt

        if self.phase == self.PHASE_FADEIN:
            if self._update_fadein(dt):
                self._on_fadein_complete()

        elif self.phase == self.PHASE_DIALOGUE:
            self._update_dialogue(dt)

        elif self.phase == self.PHASE_FADEOUT:
            if self._update_fadeout(dt):
                self._on_fadeout_complete()

    def _on_fadein_complete(self):
        """페이드인 완료 시 호출 - 서브클래스에서 오버라이드"""
        self.phase = self.PHASE_DISPLAY
        self.phase_timer = 0.0

    def _on_fadeout_complete(self):
        """페이드아웃 완료 시 호출"""
        self.phase = self.PHASE_DONE
        self.is_alive = False
        if self.on_complete:
            self.on_complete()

    def _transition_to_fadeout(self):
        """페이드아웃으로 전환"""
        self.phase = self.PHASE_FADEOUT
        self.phase_timer = 0.0

    def _transition_to_dialogue(self):
        """대화 페이즈로 전환"""
        self.phase = self.PHASE_DIALOGUE
        self.phase_timer = 0.0
        self._start_dialogue()

    def handle_event(self, event: pygame.event.Event) -> bool:
        """이벤트 처리 - 공통 로직"""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self._handle_click()

        elif event.type == pygame.KEYDOWN:
            if event.key in [pygame.K_SPACE, pygame.K_RETURN]:
                return self._handle_click()
            elif event.key == pygame.K_ESCAPE:
                self._transition_to_fadeout()
                return True

        return False

    def _handle_click(self) -> bool:
        """클릭 처리 - 서브클래스에서 확장 가능"""
        if self.phase == self.PHASE_DIALOGUE:
            if self.waiting_for_click:
                if self._advance_dialogue():
                    self._transition_to_fadeout()
            else:
                # 타이핑 스킵
                self.typing_progress = len(self.dialogue_text)
                self.waiting_for_click = True
            return True
        return False

    def render(self, screen: pygame.Surface):
        """렌더링 - 서브클래스에서 확장"""
        self._render_background(screen)

    def _render_background(self, screen: pygame.Surface):
        """배경 렌더링"""
        if self.background:
            bg_copy = self.background.copy()
            if self.fade_alpha < 255:
                bg_copy.set_alpha(int(self.fade_alpha))
            screen.blit(bg_copy, (0, 0))
        else:
            screen.fill((20, 20, 30))

    def _render_dialogue(self, screen: pygame.Surface, box_color: tuple = (20, 30, 40, 220),
                         border_color: tuple = (100, 100, 150), text_color: tuple = (220, 220, 220)):
        """대화창 렌더링 (초상화 포함)"""
        if not self.dialogue_after or self.current_dialogue_index >= len(self.dialogue_after):
            return

        dialogue = self.dialogue_after[self.current_dialogue_index]
        speaker = dialogue.get("speaker", "")
        portrait = self._get_portrait(speaker) if speaker else None

        render_dialogue_box(screen, self.screen_size, self.fonts, dialogue,
                           self.dialogue_text, self.typing_progress, self.waiting_for_click,
                           box_color=box_color, border_color=border_color, text_color=text_color,
                           has_portrait=(portrait is not None), portrait=portrait)

    def _render_click_hint(self, screen: pygame.Surface, text: str = "클릭하여 계속"):
        """클릭 힌트 렌더링"""
        if "small" not in self.fonts:
            return

        alpha = int(128 + 127 * math.sin(pygame.time.get_ticks() / 300))
        hint_surf = self.fonts["small"].render(text, True, (200, 200, 200))
        hint_surf.set_alpha(alpha)
        hint_rect = hint_surf.get_rect(midbottom=(self.screen_size[0] // 2, self.screen_size[1] - 20))
        screen.blit(hint_surf, hint_rect)


# =========================================================
# 공통 대화창 렌더링 헬퍼 함수
# =========================================================
def render_dialogue_box(screen: pygame.Surface, screen_size: tuple, fonts: dict,
                        dialogue: dict, dialogue_text: str, typing_progress: float,
                        waiting_for_click: bool, box_color: tuple = (20, 30, 40, 220),
                        border_color: tuple = (100, 100, 150), text_color: tuple = (220, 220, 220),
                        box_height: int = 150, has_portrait: bool = False, portrait: pygame.Surface = None):
    """
    공통 대화창 렌더링 함수

    Args:
        screen: 렌더링할 화면
        screen_size: (width, height) 화면 크기
        fonts: {"small": font, "medium": font} 폰트 딕셔너리
        dialogue: {"speaker": "...", "text": "..."} 대화 데이터
        dialogue_text: 전체 대사 텍스트
        typing_progress: 타이핑 진행률 (0~len)
        waiting_for_click: 클릭 대기 중 여부
        box_color: 박스 배경색 (R, G, B, A)
        border_color: 테두리 색상 (R, G, B) 또는 (R, G, B, A)
        text_color: 대사 텍스트 색상
        box_height: 박스 높이
        has_portrait: 초상화 표시 여부
        portrait: 초상화 Surface (has_portrait=True일 때)
    """
    speaker = dialogue.get("speaker", "") if dialogue else ""

    screen_w, screen_h = screen_size
    box_width = (screen_w - 100) // 2  # 가로 1/2 크기
    box_x = (screen_w - box_width) // 2  # 중앙 정렬
    box_y = screen_h - box_height - 40

    # 박스 배경
    box_surf = pygame.Surface((box_width, box_height), pygame.SRCALPHA)
    pygame.draw.rect(box_surf, box_color, (0, 0, box_width, box_height), border_radius=10)

    # 테두리
    border_col = border_color if len(border_color) == 4 else border_color + (200,)
    pygame.draw.rect(box_surf, border_col, (0, 0, box_width, box_height), 2, border_radius=10)
    screen.blit(box_surf, (box_x, box_y))

    # 텍스트 시작 위치
    text_left_x = box_x + 30
    portrait_width = 0

    # 초상화 (옵션)
    if has_portrait and portrait:
        portrait_width = 120
        portrait_x = box_x + 15
        portrait_y = box_y + (box_height - portrait_width) // 2
        # 초상화 배경
        pygame.draw.circle(screen, (30, 30, 40),
                          (portrait_x + portrait_width // 2, portrait_y + portrait_width // 2),
                          portrait_width // 2 + 5)
        # 초상화 마스킹 (원형)
        mask_surf = pygame.Surface((portrait_width, portrait_width), pygame.SRCALPHA)
        pygame.draw.circle(mask_surf, (255, 255, 255, 255),
                          (portrait_width // 2, portrait_width // 2), portrait_width // 2)
        portrait_copy = portrait.copy()
        portrait_copy = pygame.transform.smoothscale(portrait_copy, (portrait_width, portrait_width))
        portrait_copy.blit(mask_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        screen.blit(portrait_copy, (portrait_x, portrait_y))
        text_left_x = portrait_x + portrait_width + 20

    # 화자 이름
    if speaker and "medium" in fonts:
        try:
            from mode_configs.config_story_dialogue import CHARACTER_COLORS, CHARACTER_NAMES
            name_color = CHARACTER_COLORS.get(speaker, (200, 200, 200))
            name = CHARACTER_NAMES.get(speaker, speaker)
        except ImportError:
            name_color = (200, 200, 200)
            name = speaker

        name_surf = fonts["medium"].render(name, True, name_color)
        screen.blit(name_surf, (text_left_x, box_y + 15))

    # 대사 텍스트 (줄바꿈 처리)
    if "small" in fonts and dialogue_text:
        visible_text = dialogue_text[:int(typing_progress)]
        # 텍스트 영역 너비 계산
        text_area_width = box_width - (text_left_x - box_x) - 30
        line_height = fonts["small"].get_height() + 4
        max_lines = 3  # 최대 줄 수

        # 텍스트를 줄바꿈하여 렌더링
        lines = []
        current_line = ""
        for char in visible_text:
            test_line = current_line + char
            test_width = fonts["small"].size(test_line)[0]
            if test_width > text_area_width and current_line:
                lines.append(current_line)
                current_line = char
            else:
                current_line = test_line
        if current_line:
            lines.append(current_line)

        # 최대 줄 수 제한
        lines = lines[:max_lines]

        # 각 줄 렌더링
        for i, line in enumerate(lines):
            text_surf = fonts["small"].render(line, True, text_color)
            screen.blit(text_surf, (text_left_x, box_y + 55 + i * line_height))

    # 클릭 안내
    if waiting_for_click and "small" in fonts:
        hint = fonts["small"].render("▼", True, (150, 150, 150))
        screen.blit(hint, (box_x + box_width - 50, box_y + box_height - 35))

    return box_x, box_y, box_width, box_height  # 필요시 반환

# =========================================================
# 0. Weapon 클래스 (무기 로직)
# =========================================================
class Weapon:
    def __init__(self, damage: float, cooldown: float, bullet_count: int, spread_angle: float = 5.0):
        self.damage = damage
        self.cooldown = cooldown
        self.bullet_count = bullet_count
        self.spread_angle = spread_angle
        self.time_since_last_shot = 0.0 # 발사 쿨타임 추적

    def update(self, dt: float):
        """무기의 쿨타임을 업데이트합니다."""
        self.time_since_last_shot += dt

    def can_shoot(self) -> bool:
        """현재 발사 가능한지 확인합니다."""
        return self.time_since_last_shot >= self.cooldown

    def fire(self, start_pos: pygame.math.Vector2, target_pos: pygame.math.Vector2, bullets: List, piercing_state: bool, player=None):
        """
        지정된 목표 위치로 총알을 발사합니다.
        """
        if not self.can_shoot():
            return

        self.time_since_last_shot = 0.0 # 쿨타임 초기화

        # 목표 방향 벡터 계산
        direction = target_pos - start_pos
        base_angle = math.atan2(direction.y, direction.x)

        # Berserker 스킬: 저체력 시 데미지 2배
        bullet_damage = self.damage
        if player and hasattr(player, 'has_berserker') and player.has_berserker:
            if player.hp / player.max_hp < 0.3:
                bullet_damage = int(self.damage * 2.0)

        # 발사각 분산 계산
        for i in range(self.bullet_count):
            if self.bullet_count == 1:
                angle_offset = 0
            else:
                # 총알 수에 따라 균등하게 각도를 분산
                angle_spread = self.spread_angle * (self.bullet_count - 1)
                start_offset = -angle_spread / 2
                angle_offset = start_offset + (i * self.spread_angle)

            # 각도를 라디안에서 쿼터니언 (이동 벡터)로 변환
            new_angle = base_angle + math.radians(angle_offset)
            bullet_direction = pygame.math.Vector2(math.cos(new_angle), math.sin(new_angle)).normalize()

            # 새 총알 객체 생성 및 리스트에 추가
            bullet = Bullet(
                start_pos.copy(),
                bullet_direction,
                bullet_damage,
                piercing_state # 피어싱 상태를 Bullet에 전달
            )
            bullets.append(bullet)

    # 전술 레벨업을 위한 메서드 (utils.py에서 호출)
    def increase_damage(self, ratio: float):
        self.damage = int(self.damage * (1 + ratio))
        print(f"INFO: Damage increased to {self.damage}")

    def decrease_cooldown(self, ratio: float):
        self.cooldown = max(0.05, self.cooldown * (1 - ratio))
        print(f"INFO: Cooldown decreased to {self.cooldown:.2f}")

    def add_bullet(self):
        self.bullet_count += 1
        print(f"INFO: Bullet count increased to {self.bullet_count}")

# =========================================================
# 1. 애니메이션/이펙트 클래스
# =========================================================

class AnimatedEffect:
    """애니메이션을 재생하고 스스로 제거되는 이펙트 클래스"""
    def __init__(self, pos: Tuple[int, int], screen_height: int, image_path: Path, object_type_key: str, frame_duration: float = 0.1, total_frames: int = 1):
        self.pos = pygame.math.Vector2(pos)
        self.start_time = pygame.time.get_ticks() / 1000.0
        self.frame_duration = frame_duration
        self.total_frames = total_frames
        self.is_finished = False

        # 이미지 로드 및 크기 설정 (config.IMAGE_SIZE_RATIOS 사용)
        size_ratio = config.IMAGE_SIZE_RATIOS.get(object_type_key, 0.03) # 기본값 0.03
        image_height = int(screen_height * size_ratio)

        # 이미지 크기는 이펙트 종류에 따라 조정 가능하도록 함
        self.image = AssetManager.get_image(image_path, (image_height, image_height))
        self.image_rect = self.image.get_rect(center=(self.pos.x, self.pos.y))

    def update(self, dt: float, current_time: float):
        """애니메이션 프레임을 업데이트합니다."""

        elapsed_time = current_time - self.start_time

        # 단일 프레임 이펙트이므로 바로 종료
        if elapsed_time > self.frame_duration * self.total_frames:
             self.is_finished = True

    def draw(self, screen: pygame.Surface):
        """현재 프레임의 이미지를 화면에 그립니다."""
        if not self.is_finished:
            screen.blit(self.image, self.image_rect)


class DamageNumber:
    """데미지 숫자를 표시하는 클래스 (누적 데미지 지원)"""

    # 데미지 크기에 따른 폰트/색상 설정
    DAMAGE_TIERS = {
        "small": {"threshold": 0, "font_size": 20, "color": (200, 200, 200), "lifetime": 0.8},
        "normal": {"threshold": 30, "font_size": 26, "color": (255, 255, 100), "lifetime": 1.2},
        "big": {"threshold": 100, "font_size": 34, "color": (255, 180, 50), "lifetime": 1.5},
        "huge": {"threshold": 300, "font_size": 44, "color": (255, 100, 50), "lifetime": 2.0},
        "massive": {"threshold": 1000, "font_size": 56, "color": (255, 50, 50), "lifetime": 2.5},
    }

    def __init__(self, damage: float, pos: Tuple[float, float], is_accumulated: bool = False,
                 is_critical: bool = False, font: pygame.font.Font = None):
        self.damage = int(damage)
        self.pos = pygame.math.Vector2(pos)
        self.start_time = pygame.time.get_ticks() / 1000.0
        self.is_finished = False
        self.is_accumulated = is_accumulated  # 누적 데미지 여부
        self.is_critical = is_critical

        # 데미지 티어 결정
        self.tier = self._get_damage_tier()
        tier_data = self.DAMAGE_TIERS[self.tier]

        # 누적 데미지는 더 크게 표시
        font_size = tier_data["font_size"]
        if is_accumulated:
            font_size = int(font_size * 1.3)

        self.lifetime = tier_data["lifetime"]
        self.color = tier_data["color"]

        # 크리티컬은 빨간색
        if is_critical:
            self.color = (255, 50, 100)
            font_size = int(font_size * 1.2)

        # 폰트 설정
        if font is None:
            self.font = pygame.font.Font(None, font_size)
        else:
            self.font = font

        # 초기 스케일 (팝업 효과용)
        self.scale = 1.5 if is_accumulated else 1.0
        self.target_scale = 1.0

        # 텍스트 렌더링
        self._render_text()

        # 랜덤 오프셋 (겹침 방지)
        self.offset_x = random.uniform(-15, 15) if not is_accumulated else 0
        self.pos.x += self.offset_x

        # 위로 떠오르는 속도 (누적은 더 느리게)
        self.rise_speed = 30 if is_accumulated else 60

    def _get_damage_tier(self) -> str:
        """데미지 크기에 따른 티어 반환"""
        tier = "small"
        for tier_name, data in self.DAMAGE_TIERS.items():
            if self.damage >= data["threshold"]:
                tier = tier_name
        return tier

    def _render_text(self):
        """텍스트 렌더링 (스케일 적용)"""
        # 누적 데미지는 ! 추가
        display_text = f"{self.damage}!" if self.is_accumulated else str(self.damage)

        # 기본 텍스트
        base_text = self.font.render(display_text, True, self.color)

        # 스케일 적용
        if self.scale != 1.0:
            new_size = (int(base_text.get_width() * self.scale),
                       int(base_text.get_height() * self.scale))
            self.text = pygame.transform.smoothscale(base_text, new_size)
        else:
            self.text = base_text

        self.text_rect = self.text.get_rect(center=(self.pos.x, self.pos.y))

    def update(self, dt: float, current_time: float):
        """데미지 숫자를 위로 이동시키고 페이드 아웃"""
        elapsed_time = current_time - self.start_time

        if elapsed_time >= self.lifetime:
            self.is_finished = True
            return

        # 스케일 애니메이션 (팝업 효과)
        if self.scale > self.target_scale:
            self.scale = max(self.target_scale, self.scale - dt * 3)
            self._render_text()

        # 위로 떠오름
        self.pos.y -= self.rise_speed * dt
        self.text_rect.center = (self.pos.x, self.pos.y)

        # 페이드 아웃 (후반부에만)
        fade_start = self.lifetime * 0.6
        if elapsed_time > fade_start:
            alpha = int(255 * (1 - (elapsed_time - fade_start) / (self.lifetime - fade_start)))
            self.text.set_alpha(max(0, alpha))

    def draw(self, screen: pygame.Surface):
        """데미지 숫자를 화면에 그립니다."""
        if not self.is_finished:
            screen.blit(self.text, self.text_rect)


class DamageNumberManager:
    """
    데미지 숫자 관리자 - 누적 시스템

    동작 방식:
    1. 같은 대상(적)에게 일정 시간(accumulate_window) 내 발생한 데미지 누적
    2. 누적 시간이 지나면 큰 숫자로 한번에 표시
    3. 개별 작은 틱 데미지는 선택적으로 표시 가능
    """

    def __init__(self, accumulate_window: float = 0.4, show_ticks: bool = False,
                 max_numbers: int = 15):
        """
        Args:
            accumulate_window: 데미지 누적 시간 (초)
            show_ticks: 개별 작은 데미지도 표시할지 여부
            max_numbers: 화면에 표시할 최대 데미지 숫자 수
        """
        self.accumulate_window = accumulate_window
        self.show_ticks = show_ticks
        self.max_numbers = max_numbers

        # 활성 데미지 숫자들
        self.damage_numbers: List[DamageNumber] = []

        # 대상별 누적 데미지 {enemy_id: {"damage": total, "pos": last_pos, "start_time": time}}
        self.accumulated_damage: Dict[int, Dict] = {}

    def add_damage(self, damage: float, pos: Tuple[float, float], target_id: int = None,
                   is_critical: bool = False):
        """
        데미지 추가

        Args:
            damage: 데미지 양
            pos: 표시 위치
            target_id: 대상 식별자 (없으면 누적 안함)
            is_critical: 크리티컬 여부
        """
        current_time = pygame.time.get_ticks() / 1000.0

        # 대상이 있으면 누적
        if target_id is not None:
            if target_id in self.accumulated_damage:
                acc = self.accumulated_damage[target_id]
                acc["damage"] += damage
                acc["pos"] = pos  # 마지막 위치 업데이트
                acc["is_critical"] = acc.get("is_critical", False) or is_critical
            else:
                self.accumulated_damage[target_id] = {
                    "damage": damage,
                    "pos": pos,
                    "start_time": current_time,
                    "is_critical": is_critical,
                }

            # 작은 틱 데미지 표시 (선택적)
            if self.show_ticks and damage < 50:
                self._add_tick_damage(damage, pos)
        else:
            # 대상 없으면 바로 표시
            self._create_damage_number(damage, pos, is_accumulated=False, is_critical=is_critical)

    def _add_tick_damage(self, damage: float, pos: Tuple[float, float]):
        """작은 틱 데미지 표시"""
        # 틱 데미지는 작고 빠르게 사라짐
        dmg_num = DamageNumber(damage, pos, is_accumulated=False)
        dmg_num.lifetime = 0.5
        dmg_num.rise_speed = 80
        self.damage_numbers.append(dmg_num)

    def _create_damage_number(self, damage: float, pos: Tuple[float, float],
                              is_accumulated: bool = False, is_critical: bool = False):
        """데미지 숫자 생성"""
        dmg_num = DamageNumber(damage, pos, is_accumulated=is_accumulated, is_critical=is_critical)
        self.damage_numbers.append(dmg_num)

        # 최대 개수 제한
        if len(self.damage_numbers) > self.max_numbers:
            # 가장 오래된 것 제거
            self.damage_numbers = self.damage_numbers[-self.max_numbers:]

    def update(self, dt: float):
        """업데이트 - 누적 시간 체크 및 데미지 숫자 업데이트"""
        current_time = pygame.time.get_ticks() / 1000.0

        # 누적 데미지 확인 및 표시
        targets_to_remove = []
        for target_id, acc in self.accumulated_damage.items():
            elapsed = current_time - acc["start_time"]

            if elapsed >= self.accumulate_window:
                # 누적 시간 경과 - 큰 숫자로 표시
                self._create_damage_number(
                    acc["damage"],
                    acc["pos"],
                    is_accumulated=True,
                    is_critical=acc.get("is_critical", False)
                )
                targets_to_remove.append(target_id)

        # 표시 완료된 누적 데미지 제거
        for target_id in targets_to_remove:
            del self.accumulated_damage[target_id]

        # 데미지 숫자 업데이트
        for dmg_num in self.damage_numbers:
            dmg_num.update(dt, current_time)

        # 완료된 숫자 제거
        self.damage_numbers = [d for d in self.damage_numbers if not d.is_finished]

    def flush_target(self, target_id: int):
        """특정 대상의 누적 데미지 즉시 표시 (적 사망 시)"""
        if target_id in self.accumulated_damage:
            acc = self.accumulated_damage[target_id]
            self._create_damage_number(
                acc["damage"],
                acc["pos"],
                is_accumulated=True,
                is_critical=acc.get("is_critical", False)
            )
            del self.accumulated_damage[target_id]

    def draw(self, screen: pygame.Surface):
        """모든 데미지 숫자 그리기"""
        for dmg_num in self.damage_numbers:
            dmg_num.draw(screen)

    def clear(self):
        """모든 데미지 숫자 초기화"""
        self.damage_numbers.clear()
        self.accumulated_damage.clear()


# =========================================================
# 2. 플레이어 클래스
# =========================================================

class Player:
    """플레이어 우주선 클래스"""

    def __init__(self, pos: pygame.math.Vector2, screen_height: int, upgrades: Dict[str, int], ship_type: str = None):
        # 0. 영구 업그레이드 저장
        self.upgrades = upgrades

        # 0-1. 함선 타입 설정
        self.ship_type = ship_type or config.DEFAULT_SHIP
        self.ship_data = config.SHIP_TYPES.get(self.ship_type, config.SHIP_TYPES[config.DEFAULT_SHIP])
        self.ship_stats = self.ship_data["stats"]

        # 1. 위치 및 이동
        self.pos = pos
        self.base_speed = config.PLAYER_BASE_SPEED
        self.speed = self.base_speed  # 실제 이동 속도 (업그레이드 적용 후)

        # 2. 체력 스탯
        # 플레이어 초기 최대 체력 (영구 업그레이드 적용 전)
        self.initial_max_hp = config.PLAYER_BASE_HP

        # 영구 업그레이드를 기반으로 스탯 계산 (함선 배율 적용 포함)
        self.calculate_stats_from_upgrades()

        # 최대 체력 (전술 레벨업으로 증가 가능)
        self.max_hp = self.initial_max_hp

        # 현재 체력 (최대치로 시작)
        self.hp = self.max_hp

        # 사망 플래그 (HP가 0이 된 적 있으면 True, 부활 시 False로 리셋)
        self.is_dead = False

        # 3. 이미지 및 히트박스 (함선 크기에 따라 조정)
        ship_size = self.ship_stats.get("size", "medium")
        size_ratio = config.SHIP_SIZE_RATIOS.get(ship_size, config.IMAGE_SIZE_RATIOS["PLAYER"])
        image_size = int(screen_height * size_ratio)

        # 함선 이미지 로드 시도
        ship_image_path = config.ASSET_DIR / "images" / "ships" / self.ship_data.get("image", "fighter_front.png")
        if ship_image_path.exists():
            self.image = AssetManager.get_image(ship_image_path, (image_size, image_size))
        else:
            # 기본 플레이어 이미지 사용
            self.image = AssetManager.get_image(config.PLAYER_SHIP_IMAGE_PATH, (image_size, image_size))
        self.image_rect = self.image.get_rect(center=(self.pos.x, self.pos.y))

        hitbox_size = int(image_size * config.PLAYER_HITBOX_RATIO)
        self.hitbox = pygame.Rect(0, 0, hitbox_size, hitbox_size)
        self.hitbox.center = (int(self.pos.x), int(self.pos.y))

        # 3-1. 전술 레벨업 속성 (무기)
        self.is_piercing = False  # 관통 속성

        # 3-2. 전술 레벨업 속성 (추가 속성)
        self.has_explosive = False  # 폭발 속성
        self.explosive_radius = 100.0  # 폭발 범위
        self.has_chain_explosion = False  # 연쇄 폭발
        self.has_lightning = False  # 번개 속성
        self.lightning_chain_count = 0  # 연쇄 횟수
        self.has_static_field = False  # 정전기장
        self.has_frost = False  # 빙결 속성
        self.frost_slow_ratio = 0.0  # 둔화 비율
        self.has_deep_freeze = False  # 심화 빙결
        self.freeze_chance = 0.0  # 빙결 확률

        # 3-3. 방어 속성
        self.damage_reduction = 0.0  # 피해 감소 비율
        self.regeneration_rate = 0.0  # 초당 HP 회복량
        self.last_regen_time = 0.0  # 마지막 회복 시간

        # 3-4. 유틸리티 속성
        self.coin_drop_multiplier = 1.0  # 코인 드롭 배율
        self.exp_multiplier = 1.0  # 경험치 배율
        self.has_coin_magnet = False  # 코인 자석 효과

        # 3-5. 지원 유닛 (동료 시스템)
        self.turret_count = 0  # 보유한 터렛 슬롯 수
        self.pending_turret_placements = 0  # 배치 대기 중인 터렛 수
        self.drone_count = 0  # 보유한 드론 수

        # 3-6. 획득한 스킬 추적 (스킬 이름: 획득 횟수)
        self.acquired_skills = {}

        # 3-7. 활성화된 시너지 추적 (시너지 효과 이름 리스트)
        self.active_synergies = []

        # 3-8. 스킬 활성화 타임 추적 (스킬 UI 표시용)
        self.skill_last_trigger = {
            'add_explosive': 0.0,
            'add_lightning': 0.0,
            'add_frost': 0.0,
        }

        # 4. 무기 초기화 (함선 배율 + Workshop 업그레이드 적용)
        damage_mult = self.ship_stats.get("damage_mult", 1.0)
        cooldown_mult = self.ship_stats.get("cooldown_mult", 1.0)

        base_cooldown = config.WEAPON_COOLDOWN_BASE

        # 영구 쿨다운 업그레이드 적용
        cd_level = self.upgrades.get("COOLDOWN", 0)
        cd_reduction_ratio = config.PERMANENT_COOLDOWN_REDUCTION_RATIO * cd_level

        # Workshop FIRE_RATE: -10% cooldown per level
        fire_rate_level = self.upgrades.get("FIRE_RATE", 0)
        workshop_cd_reduction = 0.10 * fire_rate_level

        final_cooldown = base_cooldown * (1 - cd_reduction_ratio - workshop_cd_reduction) * cooldown_mult
        final_cooldown = max(0.05, final_cooldown)  # 최소 쿨다운 제한

        # 데미지 계산
        base_damage = config.BULLET_DAMAGE_BASE

        # Workshop DAMAGE: +8% per level
        damage_level = self.upgrades.get("DAMAGE", 0)
        if damage_level > 0:
            base_damage = base_damage * (1 + 0.08 * damage_level)

        # 무기 인스턴스 생성 (함선 데미지 배율 적용)
        self.weapon = Weapon(
            damage=int(base_damage * damage_mult),
            cooldown=final_cooldown,
            bullet_count=1,
            spread_angle=5.0
        )

        # Workshop PIERCING: +1 penetration per level
        piercing_level = self.upgrades.get("PIERCING", 0)
        if piercing_level > 0:
            self.is_piercing = True

        # 5. 히트 플래시 효과 속성
        self.hit_flash_timer = 0.0  # 히트 플래시 타이머
        self.is_flashing = False  # 현재 플래시 중인지
        self.was_hit_recently = False  # 최근 피격 여부 (CombatMotionEffect용)

        # 6. 원본 이미지 저장 (히트 플래시용)
        self.original_image = self.image.copy()

        # 7. 궁극기 시스템 (Q 키)
        self.ultimate_type = "NOVA_BLAST"  # 기본 궁극기 타입
        self.ultimate_charge = config.ULTIMATE_SETTINGS["charge_time"]  # 궁극기 충전 타이머
        self.ultimate_cooldown_timer = 0.0  # 궁극기 쿨다운 타이머
        self.ultimate_active = False  # 궁극기 활성화 상태
        self.ultimate_timer = 0.0  # 궁극기 효과 지속 시간
        self.ultimate_effects = []  # 궁극기 시각 효과 리스트
        # Time Freeze용
        self.time_freeze_active = False
        self.time_freeze_timer = 0.0
        # Orbital Strike용
        self.orbital_strikes = []  # [(target_pos, delay, strike_timer), ...]
        self.orbital_strike_timer = 0.0

        # 9. 고급 스킬 속성 (Wave 11-15)
        self.execute_threshold = 0.0  # Execute: 즉사 체력 임계값 (0.2 = 20%)
        self.has_phoenix = False  # Phoenix Rebirth: 부활 스킬
        self.phoenix_cooldown = 0.0  # Phoenix 쿨다운 타이머 (120초)
        self.has_berserker = False  # Berserker: 저체력 시 공격력 증가
        self.has_starfall = False  # Starfall: 킬마다 별똥별 소환
        self.starfall_kill_counter = 0  # Starfall 킬 카운터
        self.has_arcane_mastery = False  # Arcane Mastery: 모든 속성 효과 +50%
        self.second_chance_rate = 0.0  # Second Chance: 치명타 회피 확률

        # 10. 이동 효과 시스템
        self.velocity = pygame.math.Vector2(0, 0)  # 현재 이동 속도 벡터
        self.trail_particles = []  # 이동 트레일 파티클 [(pos, lifetime, color, size), ...]
        self.afterimages = []  # 잔상 효과 [(image, pos, alpha, lifetime), ...]
        self.last_trail_spawn = 0.0  # 마지막 트레일 생성 시간
        self.trail_spawn_interval = 0.02  # 트레일 생성 간격 (초)
        self.disable_afterimages = False  # 잔상 비활성화 플래그 (공성 모드용)

        # 10-1. 이동 방향 기울기(틸트) 시스템
        self.current_tilt = 0.0  # 현재 기울기 각도 (도)
        self.target_tilt = 0.0  # 목표 기울기 각도 (도)
        self.tilt_speed = 8.0  # 기울기 보간 속도 (클수록 빠르게 기울어짐)
        self.max_tilt_angle = 25.0  # 최대 기울기 각도 (도)
        self.tilt_return_speed = 5.0  # 원위치 복귀 속도

        # 11. 함선 특수 능력 시스템 (E 키)
        self.ship_ability_type = self.ship_data.get("special")  # 함선 특수 능력 타입
        self.ship_ability_cooldown = 0.0  # 능력 쿨다운 타이머
        self.ship_ability_active = False  # 능력 활성화 상태
        self.ship_ability_timer = 0.0  # 능력 지속 시간

        # 함선별 능력 초기화
        self._init_ship_ability()

        # 12. 마우스 이동 시스템
        self.mouse_target = None  # 마우스 클릭 목표 위치 (Vector2 또는 None)
        self.mouse_move_speed_mult = 1.0  # 마우스 이동 속도 배율
        self.mouse_arrival_threshold = 10.0  # 목표 도달 판정 거리 (px)

    def _init_ship_ability(self):
        """함선별 특수 능력 초기화"""
        ability = self.ship_ability_type

        # INTERCEPTOR: Evasion Boost (2초 무적 대시)
        self.evasion_active = False
        self.evasion_duration = 2.0
        self.evasion_cooldown_max = 15.0

        # BOMBER: Bomb Drop (AoE 폭탄)
        self.bomb_damage = 500
        self.bomb_radius = 200
        self.bomb_cooldown_max = 10.0

        # STEALTH: Cloaking (3초 은신)
        self.cloak_active = False
        self.cloak_duration = 3.0
        self.cloak_cooldown_max = 20.0
        self.cloak_alpha = 255  # 은신 시 투명도

        # TITAN: Shield (피해 흡수)
        self.shield_active = False
        self.shield_hp = 0
        self.shield_max_hp = 0
        self.shield_absorption = 0.30  # 30% 피해 흡수
        self.shield_cooldown_max = 25.0
        self.shield_duration = 8.0

        # Titan 함선일 경우 실드 최대치 설정
        if self.ship_type == "TITAN":
            self.shield_max_hp = int(self.max_hp * 0.5)  # 최대 HP의 50%

    def calculate_stats_from_upgrades(self):
        """영구 업그레이드 레벨을 기반으로 플레이어 스탯을 계산합니다. (함선 배율 + Workshop 업그레이드 적용)"""

        # 함선 배율 가져오기
        hp_mult = self.ship_stats.get("hp_mult", 1.0)
        speed_mult = self.ship_stats.get("speed_mult", 1.0)

        # === 기존 영구 업그레이드 (상점) ===
        # 최대 HP 계산 (기존 레벨 시스템)
        hp_level = self.upgrades.get("MAX_HP", 1)
        hp_bonus = config.PERMANENT_MAX_HP_BONUS_AMOUNT * (hp_level - 1)
        base_hp = config.PLAYER_BASE_HP + hp_bonus

        # === Workshop 업그레이드 적용 ===
        # Workshop MAX_HP: +10% per level
        workshop_hp_level = self.upgrades.get("MAX_HP", 0)
        if workshop_hp_level > 0:
            base_hp = base_hp * (1 + 0.10 * workshop_hp_level)

        # 함선 배율 적용
        self.initial_max_hp = int(base_hp * hp_mult)

        # 이동 속도 계산
        speed_level = self.upgrades.get("SPEED", 0)
        speed_bonus = config.PERMANENT_SPEED_BONUS_AMOUNT * speed_level
        base_speed = self.base_speed + speed_bonus

        # Workshop SPEED: +5% per level
        workshop_speed_level = self.upgrades.get("SPEED", 0)
        if workshop_speed_level > 0:
            base_speed = base_speed * (1 + 0.05 * workshop_speed_level)

        # 함선 배율 적용
        self.speed = base_speed * speed_mult

        # === Workshop 스킬 적용 ===
        # Chain Lightning
        if self.upgrades.get("CHAIN_LIGHTNING", 0) > 0:
            self.has_lightning = True
            self.lightning_chain_count = 3

        # Explosive Rounds
        if self.upgrades.get("EXPLOSIVE_ROUNDS", 0) > 0:
            self.has_explosive = True

        # Freeze Shot
        if self.upgrades.get("FREEZE_SHOT", 0) > 0:
            self.has_frost = True
            self.frost_slow_ratio = 0.5

        # Execute
        if self.upgrades.get("EXECUTE", 0) > 0:
            self.execute_threshold = 0.15  # 15% HP 이하 즉사

        # Phoenix Rebirth
        if self.upgrades.get("PHOENIX", 0) > 0:
            self.has_phoenix = True

        # Coin Magnet
        if self.upgrades.get("COIN_MAGNET", 0) > 0:
            self.has_coin_magnet = True

        # Coin Multiplier
        if self.upgrades.get("COIN_MULT", 0) > 0:
            self.coin_drop_multiplier = 1.5

        # HP Regeneration
        if self.upgrades.get("HP_REGEN", 0) > 0:
            self.regeneration_rate = 2.0  # 초당 2 HP 회복

        # Defense (-3% per level)
        defense_level = self.upgrades.get("DEFENSE", 0)
        if defense_level > 0:
            self.damage_reduction = 0.03 * defense_level

    def move(self, keys: Dict, dt: float, screen_size: Tuple[int, int], current_time: float = 0.0, game_data: Dict = None):
        """키 입력 또는 마우스 클릭 목표를 기반으로 플레이어를 이동시키고 이동 효과를 생성합니다."""

        # 이동 벡터 초기화
        velocity = pygame.math.Vector2(0, 0)

        # 키보드 입력에 따라 속도 설정
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            velocity.x = -1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            velocity.x = 1
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            velocity.y = -1
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            velocity.y = 1

        # 키보드 입력이 있으면 마우스 타겟 취소
        if velocity.length_squared() > 0:
            self.mouse_target = None

        # 마우스 이동 목표가 있고 키보드 입력이 없으면 마우스 이동
        if self.mouse_target is not None and velocity.length_squared() == 0:
            to_target = self.mouse_target - self.pos
            dist = to_target.length()

            if dist > self.mouse_arrival_threshold:
                # 목표 방향으로 이동
                velocity = to_target.normalize()
            else:
                # 목표에 도달 - 타겟 클리어
                self.mouse_target = None

        # 보스 웨이브 속도 버프 계산 (20% 증가)
        speed_multiplier = 1.0
        if game_data and game_data.get('current_wave') in config.BOSS_WAVES:
            speed_multiplier = 1.2  # 보스 웨이브에서 20% 속도 증가

        # 대각선 이동 시 속도 보정 (정규화)
        if velocity.length_squared() > 0:
            effective_speed = self.speed * speed_multiplier * self.mouse_move_speed_mult
            velocity = velocity.normalize() * effective_speed * dt
            self.velocity = velocity / dt  # 초당 속도 벡터 저장
            self.pos += velocity

            # 이동 효과 생성 (속도에 따라)
            self._create_movement_effects(current_time)
        else:
            self.velocity = pygame.math.Vector2(0, 0)

        # 화면 경계 제한
        SCREEN_WIDTH, SCREEN_HEIGHT = screen_size
        half_width = self.image_rect.width / 2
        half_height = self.image_rect.height / 2

        self.pos.x = max(half_width, min(self.pos.x, SCREEN_WIDTH - half_width))
        self.pos.y = max(half_height, min(self.pos.y, SCREEN_HEIGHT - half_height))

        # rect 및 hitbox 위치 업데이트
        self.image_rect.center = (int(self.pos.x), int(self.pos.y))
        self.hitbox.center = self.image_rect.center

    def set_mouse_target(self, pos: Tuple[int, int]):
        """마우스 클릭 위치를 이동 목표로 설정합니다."""
        self.mouse_target = pygame.math.Vector2(pos[0], pos[1])

    def clear_mouse_target(self):
        """마우스 이동 목표를 취소합니다."""
        self.mouse_target = None

    # =========================================================
    # 마우스 우클릭 공격 시스템 (가까운 적 타겟팅)
    # =========================================================
    def find_nearest_enemy(self, enemies: list) -> object:
        """
        가장 가까운 적을 찾아 반환합니다.

        Args:
            enemies: 적 객체 리스트

        Returns:
            가장 가까운 적 객체 또는 None
        """
        if not enemies:
            return None

        closest_enemy = None
        closest_dist = float('inf')

        for enemy in enemies:
            if not hasattr(enemy, 'pos'):
                continue
            dist = (enemy.pos - self.pos).length()
            if dist < closest_dist:
                closest_dist = dist
                closest_enemy = enemy

        return closest_enemy

    def get_direction_to_enemy(self, enemy) -> pygame.math.Vector2:
        """
        적 방향으로의 단위 벡터를 반환합니다.

        Args:
            enemy: 적 객체

        Returns:
            적 방향 단위 벡터 또는 (0, -1) (위쪽)
        """
        if enemy is None or not hasattr(enemy, 'pos'):
            return pygame.math.Vector2(0, -1)  # 기본: 위쪽

        to_enemy = enemy.pos - self.pos
        if to_enemy.length() > 0:
            return to_enemy.normalize()
        return pygame.math.Vector2(0, -1)

    '''
    def _create_movement_effects(self, current_time: float):
        """이동 속도와 방향에 따른 시각 효과 생성"""
        import random

        # 속도에 따른 효과 강도 계산
        speed_magnitude = self.velocity.length()
        speed_ratio = speed_magnitude / self.speed  # 0.0 ~ 1.0+

        # 최소 속도 임계값 (너무 느리면 효과 안 나옴)
        if speed_ratio < 0.3:
            return

        # 트레일 생성 주기 체크
        if current_time - self.last_trail_spawn < self.trail_spawn_interval:
            return

        self.last_trail_spawn = current_time

        # 이동 방향의 반대로 파티클 생성
        if self.velocity.length_squared() > 0:
            direction = self.velocity.normalize()
            # 플레이어 뒤쪽에서 파티클 생성
            offset = -direction * (self.image_rect.width * 0.3)
            spawn_pos = self.pos + offset

            # 속도에 따른 파티클 수 (빠를수록 많이)
            particle_count = int(2 + speed_ratio * 3)

            for _ in range(particle_count):
                # 약간의 랜덤 분산
                spread = pygame.math.Vector2(
                    random.uniform(-10, 10),
                    random.uniform(-10, 10)
                )
                particle_pos = spawn_pos + spread


                if speed_ratio < 0.5: # 0.3을 0.5로 변경하여 트레일 색상 변화 구간 확대
                    color = (150, 200, 255)  # 연한 하늘색
                elif speed_ratio < 0.98:
                    color = (100, 100, 255)  # 푸른 보라색
                else:
                    color = (100, 255, 255)  # 고열의 마젠타 (가장 고속)if 
                    
                # 속도에 따른 파티클 크기
                base_size = 3 + speed_ratio * 5
                size = int(base_size + random.uniform(-1, 2))
                size = max(1, size) # 최소 크기 보장
            
            



                # 파티클 수명 (속도가 빠를수록 길게)
                lifetime = 0.3 + speed_ratio * 0.3

                self.trail_particles.append({
                    'pos': particle_pos.copy(),
                    'lifetime': lifetime,
                    'max_lifetime': lifetime,
                    'color': color,
                    'size': size
                })

        # 고속 이동 시 잔상 효과 추가
        if speed_ratio > 0.5:
            # 잔상 생성 (투명도 있는 플레이어 이미지)
            afterimage = self.image.copy()
            
            # 🌟 청록색 플라즈마 필터 추가
            PLASMA_COLOR = (100, 255, 255) 
            afterimage.fill(PLASMA_COLOR, special_flags=pygame.BLEND_RGB_MULT)
            
            
            alpha = int(150 * speed_ratio)  # 속도에 따라 투명도 조절
            afterimage.set_alpha(min(alpha, 255)) # 255 초과 방지
            afterimage.set_alpha(alpha)

            # 잔상에 현재 기울기 적용
            if abs(self.current_tilt) > 0.5:
                afterimage = pygame.transform.rotate(afterimage, self.current_tilt)

            self.afterimages.append({
                'image': afterimage,
                'pos': self.pos.copy(),
                'alpha': alpha,
                'lifetime': 0.3,  # 잔상 지속 시간
                'max_lifetime': 0.3
            })
            '''     

    def _create_movement_effects(self, current_time: float):
        """이동 속도와 방향에 따른 시각 효과 생성"""
        import random

        # 속도에 따른 효과 강도 계산
        speed_magnitude = self.velocity.length()
        speed_ratio = speed_magnitude / self.speed  # 0.0 ~ 1.0+

        # 최소 속도 임계값 (너무 느리면 효과 안 나옴)
        if speed_ratio < 0.3:
            return

        # 트레일 생성 주기 체크
        if current_time - self.last_trail_spawn < self.trail_spawn_interval:
            return

        self.last_trail_spawn = current_time

        # 이동 방향의 반대로 파티클 생성
        if self.velocity.length_squared() > 0:
            direction = self.velocity.normalize()
            # 플레이어 뒤쪽에서 파티클 생성
            offset = -direction * (self.image_rect.width * 0.3)
            spawn_pos = self.pos + offset

            # 속도에 따른 파티클 수 (빠를수록 많이)
            particle_count = int(2 + speed_ratio * 3)

            for _ in range(particle_count):
            # 약간의 랜덤 분산
                spread = pygame.math.Vector2(
                random.uniform(-10, 10),
                random.uniform(-10, 10)
            )
            particle_pos = spawn_pos + spread


        if speed_ratio < 0.5:
            color = (100, 150, 255)  # 파란색
        elif speed_ratio < 0.8:
            color = (150, 200, 255)  # 하늘색
        else:
            color = (255, 215, 0)  # 주황색


            # 속도에 따른 파티클 크기
            size = int(3 + speed_ratio * 5)

            # 파티클 수명 (속도가 빠를수록 길게)
            lifetime = 0.3 + speed_ratio * 0.3

            self.trail_particles.append({
            'pos': particle_pos.copy(),
            'lifetime': lifetime,
            'max_lifetime': lifetime,
            'color': color,
            'size': size
            })

            # 고속 이동 시 잔상 효과 추가 (공성 모드에서는 비활성화)
            if speed_ratio > 0.7 and not self.disable_afterimages:
                # 잔상 생성 (투명도 있는 플레이어 이미지)
                afterimage = self.image.copy()
                alpha = int(100 * speed_ratio)  # 속도에 따라 투명도 조절
                afterimage.set_alpha(alpha)

                # 잔상에 현재 기울기 적용
                if abs(self.current_tilt) > 0.5:
                    afterimage = pygame.transform.rotate(afterimage, self.current_tilt)

                self.afterimages.append({
                    'image': afterimage,
                    'pos': self.pos.copy(),
                    'alpha': alpha,
                    'lifetime': 0.15,  # 잔상 지속 시간
                    'max_lifetime': 0.15
                })    









    def activate_ultimate(self, enemies: List):
        """궁극기를 발동합니다 (Q 키)

        Args:
            enemies: 현재 적 리스트

        Returns:
            bool: 궁극기 발동 성공 여부
        """
        # 충전 확인
        if self.ultimate_charge < config.ULTIMATE_SETTINGS["charge_time"]:
            return False

        # 쿨다운 확인
        if self.ultimate_cooldown_timer > 0:
            return False

        # 궁극기 타입별 효과 발동
        if self.ultimate_type == "NOVA_BLAST":
            self._activate_nova_blast(enemies)
        elif self.ultimate_type == "TIME_FREEZE":
            self._activate_time_freeze(enemies)
        elif self.ultimate_type == "ORBITAL_STRIKE":
            self._activate_orbital_strike(enemies)

        # 쿨다운 시작
        self.ultimate_cooldown_timer = config.ULTIMATE_SETTINGS["cooldown"]
        self.ultimate_charge = 0.0

        print(f"INFO: Ultimate '{self.ultimate_type}' activated!")
        return True

    def _activate_nova_blast(self, enemies: List):
        """Nova Blast 궁극기 - 주변 대규모 폭발"""
        settings = config.ULTIMATE_SETTINGS["NOVA_BLAST"]

        # 폭발 효과 추가
        self.ultimate_effects.append({
            "type": "NOVA_BLAST",
            "pos": self.pos.copy(),
            "radius": 0,
            "max_radius": settings["radius"],
            "timer": settings["duration"],
            "color": settings["color"],
        })

        # 범위 내 모든 적에게 데미지 및 넉백
        for enemy in enemies:
            dist = (enemy.pos - self.pos).length()
            if dist <= settings["radius"]:
                # 데미지 적용
                enemy.take_damage(settings["damage"])

                # 넉백 적용
                if dist > 0:
                    knockback_dir = (enemy.pos - self.pos).normalize()
                    enemy.pos += knockback_dir * settings["knockback"] * (1 - dist / settings["radius"])

    def _activate_time_freeze(self, enemies: List):
        """Time Freeze 궁극기 - 모든 적 시간 정지"""
        settings = config.ULTIMATE_SETTINGS["TIME_FREEZE"]

        self.time_freeze_active = True
        self.time_freeze_timer = settings["duration"]

    def _activate_orbital_strike(self, enemies: List):
        """Orbital Strike 궁극기 - 레이저 공격"""
        settings = config.ULTIMATE_SETTINGS["ORBITAL_STRIKE"]

        # 모든 적 위치에 레이저 타겟 설정
        import random
        targets = []
        for i in range(min(settings["strike_count"], len(enemies) * 2)):
            if enemies:
                target_enemy = random.choice(enemies)
                targets.append({
                    "pos": target_enemy.pos.copy(),
                    "delay": i * settings["strike_interval"],
                    "timer": 0.0,
                    "active": False,
                })

        self.orbital_strikes = targets
        self.orbital_strike_timer = 0.0

    def take_damage(self, damage: float):
        """플레이어가 피해를 입습니다."""
        # 이미 사망 상태면 추가 데미지 무시
        if self.hp <= 0:
            return

        # Second Chance 스킬: 치명타 회피 (사망 직전에만 발동)
        if hasattr(self, 'second_chance_rate') and self.second_chance_rate > 0:
            would_die = (self.hp - damage * (1.0 - self.damage_reduction)) <= 0
            if would_die and random.random() < self.second_chance_rate:
                print(f"INFO: Second Chance! Dodged lethal damage!")
                return  # 피해 무시

        # 피해 감소 적용
        actual_damage = damage * (1.0 - self.damage_reduction)
        self.hp -= actual_damage
        self.hp = max(0, self.hp)

        # 사망 시 플래그 설정
        if self.hp <= 0:
            self.is_dead = True

        # 히트 플래시 트리거
        self.hit_flash_timer = config.HIT_FLASH_DURATION
        self.is_flashing = True

        # 피격 플래그 설정 (CombatMotionEffect 이동 시간 리셋용)
        self.was_hit_recently = True

    def heal(self, amount: float):
        """플레이어의 체력을 회복합니다."""
        # 사망 상태면 회복하지 않음 (게임 오버 상태)
        if self.is_dead or self.hp <= 0:
            return
        self.hp += amount
        self.hp = min(self.hp, self.max_hp)

    def increase_max_hp(self, amount: int):
        """최대 체력을 증가시키고 현재 체력을 비례적으로 조정합니다."""
        if amount <= 0: return

        # HP가 0 이하면 max_hp만 증가 (게임 오버 상태에서는 회복 안 함)
        if self.hp <= 0:
            self.max_hp += amount
            print(f"INFO: Max HP increased to {self.max_hp}, HP remains at 0 (game over state)")
            return

        # 현재 체력 비율 유지
        health_ratio = self.hp / self.max_hp if self.max_hp > 0 else 1.0

        # 최대 체력 증가
        self.max_hp += amount

        # 현재 체력을 비례적으로 증가 (체력 비율 유지)
        self.hp = self.max_hp * health_ratio

        print(f"INFO: Max HP increased to {self.max_hp}, current HP: {self.hp}")

    def increase_speed(self, amount: int):
        """이동 속도를 증가시킵니다."""
        if amount <= 0: return
        self.speed += amount
        print(f"INFO: Speed increased to {self.speed}")

    def add_damage_reduction(self, ratio: float):
        """피해 감소 비율을 추가합니다."""
        if ratio <= 0: return
        self.damage_reduction = min(0.75, self.damage_reduction + ratio)  # 최대 75%
        print(f"INFO: Damage reduction: {self.damage_reduction * 100:.0f}%")

    def add_regeneration(self, rate: float):
        """초당 체력 회복량을 추가합니다."""
        if rate <= 0: return
        self.regeneration_rate += rate
        print(f"INFO: Regeneration rate: {self.regeneration_rate} HP/s")

    def update_regeneration(self, current_time: float):
        """시간에 따라 체력을 회복합니다."""
        # 사망 상태면 회복하지 않음 (게임 오버 상태)
        if self.is_dead or self.hp <= 0:
            return
        if self.regeneration_rate > 0 and self.hp < self.max_hp:
            # 1초마다 회복
            if current_time - self.last_regen_time >= 1.0:
                self.heal(self.regeneration_rate)
                self.last_regen_time = current_time

    def update(self, dt: float, screen_size: Tuple[int, int], current_time: float):
        """플레이어 상태를 업데이트합니다."""
        # 무기 쿨타임 업데이트
        self.weapon.update(dt)

        # 체력 재생 업데이트
        self.update_regeneration(current_time)

        # 히트 플래시 타이머 업데이트
        if self.is_flashing:
            self.hit_flash_timer -= dt
            if self.hit_flash_timer <= 0:
                self.is_flashing = False
                self.image = self.original_image.copy()

        # 궁극기 충전 타이머 업데이트
        if self.ultimate_charge < config.ULTIMATE_SETTINGS["charge_time"]:
            self.ultimate_charge += dt
            self.ultimate_charge = min(self.ultimate_charge, config.ULTIMATE_SETTINGS["charge_time"])

        # 궁극기 쿨다운 타이머 업데이트
        if self.ultimate_cooldown_timer > 0:
            self.ultimate_cooldown_timer -= dt
            self.ultimate_cooldown_timer = max(0, self.ultimate_cooldown_timer)

        # Time Freeze 효과 타이머
        if self.time_freeze_active:
            self.time_freeze_timer -= dt
            if self.time_freeze_timer <= 0:
                self.time_freeze_active = False
                self.time_freeze_timer = 0.0

        # Orbital Strike 타이머 업데이트
        if self.orbital_strikes:
            self.orbital_strike_timer += dt
            for strike in self.orbital_strikes:
                if not strike["active"] and self.orbital_strike_timer >= strike["delay"]:
                    strike["active"] = True
                    strike["timer"] = config.ULTIMATE_SETTINGS["ORBITAL_STRIKE"]["beam_duration"]

                if strike["active"]:
                    strike["timer"] -= dt

            # 완료된 스트라이크 제거
            self.orbital_strikes = [s for s in self.orbital_strikes if s["timer"] > 0 or not s["active"]]

        # 궁극기 시각 효과 업데이트
        for effect in self.ultimate_effects:
            effect["timer"] -= dt
            if effect["type"] == "NOVA_BLAST":
                # 폭발 반경 확장
                progress = 1 - (effect["timer"] / config.ULTIMATE_SETTINGS["NOVA_BLAST"]["duration"])
                effect["radius"] = effect["max_radius"] * progress

        # 완료된 효과 제거
        self.ultimate_effects = [e for e in self.ultimate_effects if e["timer"] > 0]

        # 함선 특수 능력 업데이트
        self._update_ship_ability(dt)

        # 이동 방향 기울기(틸트) 업데이트
        self._update_tilt(dt)

    def _update_tilt(self, dt: float):
        """이동 방향에 따른 기울기 업데이트"""
        # 속도 벡터가 있으면 기울기 목표 계산
        if self.velocity.length() > 0.1:
            # 좌우 이동에 따른 기울기 (X축 속도 기반)
            horizontal_ratio = self.velocity.x / self.speed if self.speed > 0 else 0
            # 최대 기울기 각도로 클램핑
            self.target_tilt = -horizontal_ratio * self.max_tilt_angle

            # 추가: 위/아래 이동 시 약간의 피치 효과 (선택적)
            # vertical_ratio = self.velocity.y / self.speed if self.speed > 0 else 0
            # 위로 이동 시 약간 앞으로 기울기 효과는 2D에서 표현하기 어려우므로 생략
        else:
            # 이동하지 않으면 원위치로 복귀
            self.target_tilt = 0.0

        # 부드러운 보간 (현재 기울기 → 목표 기울기)
        tilt_diff = self.target_tilt - self.current_tilt

        if abs(tilt_diff) > 0.1:
            # 이동 중일 때는 빠르게, 정지 시에는 천천히 복귀
            if self.velocity.length() > 0.1:
                interpolation_speed = self.tilt_speed
            else:
                interpolation_speed = self.tilt_return_speed

            self.current_tilt += tilt_diff * interpolation_speed * dt
        else:
            self.current_tilt = self.target_tilt

        # 각도 클램핑
        self.current_tilt = max(-self.max_tilt_angle, min(self.max_tilt_angle, self.current_tilt))

    def _update_ship_ability(self, dt: float):
        """함선 특수 능력 상태 업데이트"""
        # 쿨다운 감소
        if self.ship_ability_cooldown > 0:
            self.ship_ability_cooldown -= dt
            self.ship_ability_cooldown = max(0, self.ship_ability_cooldown)

        # 능력 활성화 시 타이머 감소
        if self.ship_ability_active:
            self.ship_ability_timer -= dt

            # INTERCEPTOR: Evasion Boost
            if self.ship_ability_type == "evasion_boost":
                if self.ship_ability_timer <= 0:
                    self.evasion_active = False
                    self.ship_ability_active = False
                    self.ship_ability_cooldown = self.evasion_cooldown_max
                    print("INFO: Evasion Boost ended")

            # STEALTH: Cloaking
            elif self.ship_ability_type == "cloaking":
                if self.ship_ability_timer <= 0:
                    self.cloak_active = False
                    self.ship_ability_active = False
                    self.ship_ability_cooldown = self.cloak_cooldown_max
                    self.cloak_alpha = 255
                    print("INFO: Cloaking ended")
                else:
                    # 은신 중 투명도 조절 (깜빡임 효과)
                    import math
                    flicker = 0.3 + 0.2 * math.sin(self.ship_ability_timer * 10)
                    self.cloak_alpha = int(255 * flicker)

            # TITAN: Shield
            elif self.ship_ability_type == "shield":
                if self.ship_ability_timer <= 0 or self.shield_hp <= 0:
                    self.shield_active = False
                    self.ship_ability_active = False
                    self.ship_ability_cooldown = self.shield_cooldown_max
                    print("INFO: Shield ended")

    def use_ship_ability(self, enemies: list = None, effects: list = None) -> bool:
        """함선 특수 능력 사용 (E 키)"""
        # 쿨다운 중이면 사용 불가
        if self.ship_ability_cooldown > 0:
            return False

        # 능력이 없으면 사용 불가
        if self.ship_ability_type is None:
            return False

        # 이미 활성화 중이면 사용 불가
        if self.ship_ability_active:
            return False

        print(f"INFO: Using ship ability: {self.ship_ability_type}")

        # INTERCEPTOR: Evasion Boost (2초 무적 대시)
        if self.ship_ability_type == "evasion_boost":
            self.evasion_active = True
            self.ship_ability_active = True
            self.ship_ability_timer = self.evasion_duration
            # 속도 일시적으로 2배 증가
            self.speed *= 2.0
            return True

        # BOMBER: Bomb Drop (AoE 폭탄) - 즉시 발동
        elif self.ship_ability_type == "bomb_drop":
            self.ship_ability_cooldown = self.bomb_cooldown_max
            # 폭탄 효과 생성 (effects 리스트에 추가)
            if effects is not None:
                bomb_effect = {
                    "type": "bomb_drop",
                    "pos": self.pos.copy(),
                    "radius": self.bomb_radius,
                    "damage": self.bomb_damage,
                    "timer": 0.5,  # 폭발 지속 시간
                    "max_timer": 0.5,
                }
                effects.append(bomb_effect)
            # 범위 내 적에게 피해
            if enemies:
                for enemy in enemies:
                    dist = (enemy.pos - self.pos).length()
                    if dist <= self.bomb_radius:
                        # 거리에 따른 데미지 감소
                        damage_ratio = 1.0 - (dist / self.bomb_radius) * 0.5
                        enemy.take_damage(int(self.bomb_damage * damage_ratio))
            return True

        # STEALTH: Cloaking (3초 은신)
        elif self.ship_ability_type == "cloaking":
            self.cloak_active = True
            self.ship_ability_active = True
            self.ship_ability_timer = self.cloak_duration
            return True

        # TITAN: Shield (피해 흡수)
        elif self.ship_ability_type == "shield":
            self.shield_active = True
            self.shield_hp = self.shield_max_hp
            self.ship_ability_active = True
            self.ship_ability_timer = self.shield_duration
            return True

        return False

    def get_ship_ability_info(self) -> dict:
        """함선 특수 능력 정보 반환 (UI 표시용)"""
        if self.ship_ability_type is None:
            return {"name": "None", "ready": False, "cooldown": 0, "max_cooldown": 0}

        ability_names = {
            "evasion_boost": "Evasion Boost",
            "bomb_drop": "Bomb Drop",
            "cloaking": "Cloaking",
            "shield": "Shield",
        }

        max_cooldowns = {
            "evasion_boost": self.evasion_cooldown_max,
            "bomb_drop": self.bomb_cooldown_max,
            "cloaking": self.cloak_cooldown_max,
            "shield": self.shield_cooldown_max,
        }

        return {
            "name": ability_names.get(self.ship_ability_type, "Unknown"),
            "ready": self.ship_ability_cooldown <= 0 and not self.ship_ability_active,
            "active": self.ship_ability_active,
            "cooldown": self.ship_ability_cooldown,
            "max_cooldown": max_cooldowns.get(self.ship_ability_type, 10.0),
            "timer": self.ship_ability_timer if self.ship_ability_active else 0,
        }

    def is_invulnerable(self) -> bool:
        """무적 상태 확인 (Evasion Boost 또는 Cloaking)"""
        return self.evasion_active or self.cloak_active

    def take_damage_with_shield(self, damage: float) -> float:
        """실드 적용 후 실제 피해량 반환"""
        if self.shield_active and self.shield_hp > 0:
            # 실드로 흡수할 피해량
            absorbed = int(damage * self.shield_absorption)
            self.shield_hp -= absorbed
            if self.shield_hp < 0:
                self.shield_hp = 0
            return damage - absorbed
        return damage

    def update_movement_effects(self, dt: float):
        """이동 효과 업데이트 (파티클 트레일과 잔상)"""
        # 트레일 파티클 업데이트
        for particle in self.trail_particles[:]:
            particle['lifetime'] -= dt
            if particle['lifetime'] <= 0:
                self.trail_particles.remove(particle)

        # 잔상 업데이트
        for afterimage in self.afterimages[:]:
            afterimage['lifetime'] -= dt
            if afterimage['lifetime'] <= 0:
                self.afterimages.remove(afterimage)
            else:
                # 페이드 아웃 효과
                fade_ratio = afterimage['lifetime'] / afterimage['max_lifetime']
                afterimage['image'].set_alpha(int(afterimage['alpha'] * fade_ratio))

    def _calculate_perspective_scale(self, screen_height: int) -> float:
        """Y 위치 기반 원근감 스케일 계산"""
        if not config.PERSPECTIVE_ENABLED or not config.PERSPECTIVE_APPLY_TO_PLAYER:
            return 1.0

        # Y 위치 비율 계산 (0.0 = 상단, 1.0 = 하단)
        depth_ratio = self.pos.y / screen_height
        depth_ratio = max(0.0, min(1.0, depth_ratio))

        # 스케일 계산
        scale = config.PERSPECTIVE_SCALE_MIN + (depth_ratio * (config.PERSPECTIVE_SCALE_MAX - config.PERSPECTIVE_SCALE_MIN))
        return scale

    def draw(self, screen: pygame.Surface):
        """플레이어 객체를 화면에 그립니다."""
        # 원근감 스케일 계산
        perspective_scale = self._calculate_perspective_scale(screen.get_height())

        # 1. 잔상 효과 그리기 (플레이어 뒤에)
        for afterimage in self.afterimages:
            # 잔상에도 원근감 적용
            if config.PERSPECTIVE_ENABLED and config.PERSPECTIVE_APPLY_TO_PLAYER and perspective_scale != 1.0:
                afterimage_scale = self._calculate_perspective_scale(screen.get_height())
                scaled_afterimage = pygame.transform.smoothscale(
                    afterimage['image'],
                    (int(afterimage['image'].get_width() * afterimage_scale),
                     int(afterimage['image'].get_height() * afterimage_scale))
                )
                rect = scaled_afterimage.get_rect(center=(int(afterimage['pos'].x), int(afterimage['pos'].y)))
                screen.blit(scaled_afterimage, rect)
            else:
                rect = afterimage['image'].get_rect(center=(int(afterimage['pos'].x), int(afterimage['pos'].y)))
                screen.blit(afterimage['image'], rect)

        # 2. 트레일 파티클 그리기
        for particle in self.trail_particles:
            # 페이드 아웃 효과
            fade_ratio = particle['lifetime'] / particle['max_lifetime']
            alpha = int(255 * fade_ratio)

            # 파티클 크기도 점점 작아짐
            current_size = max(1, int(particle['size'] * fade_ratio * perspective_scale))

            # 투명도를 가진 서페이스 생성
            particle_surface = pygame.Surface((current_size * 2, current_size * 2), pygame.SRCALPHA)
            pygame.draw.circle(particle_surface, (*particle['color'], alpha),
                             (current_size, current_size), current_size)

            # 파티클 위치에 그리기
            rect = particle_surface.get_rect(center=(int(particle['pos'].x), int(particle['pos'].y)))
            screen.blit(particle_surface, rect)

        # 3. 그릴 이미지 결정 (히트 플래시 적용 + 능력 효과)
        if self.is_flashing:
            # 흰색으로 깜빡임
            flash_surface = self.original_image.copy()
            flash_surface.fill(config.HIT_FLASH_COLOR, special_flags=pygame.BLEND_RGB_ADD)
            draw_image = flash_surface
        elif getattr(self, 'cloak_active', False):
            # 클로킹: 반투명 + 보라색 틴트
            cloak_surface = self.image.copy()
            cloak_surface.set_alpha(80)  # 반투명
            # 보라색 틴트
            tint_surface = pygame.Surface(cloak_surface.get_size(), pygame.SRCALPHA)
            tint_surface.fill((100, 50, 150, 50))
            cloak_surface.blit(tint_surface, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
            draw_image = cloak_surface
        elif getattr(self, 'evasion_active', False):
            # 회피 부스트: 노란색 글로우
            evasion_surface = self.image.copy()
            glow_surface = pygame.Surface(evasion_surface.get_size(), pygame.SRCALPHA)
            glow_surface.fill((255, 255, 100, 60))
            evasion_surface.blit(glow_surface, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
            draw_image = evasion_surface
        else:
            draw_image = self.image

        # 3-1. 이동 방향 기울기(틸트) 적용
        if abs(self.current_tilt) > 0.5:
            # 이미지 회전 (기울기 각도 적용)
            draw_image = pygame.transform.rotate(draw_image, self.current_tilt)

        # 4. 플레이어 이미지 그리기 (원근감 + 틸트 적용)
        if config.PERSPECTIVE_ENABLED and config.PERSPECTIVE_APPLY_TO_PLAYER and perspective_scale != 1.0:
            scaled_image = pygame.transform.smoothscale(
                draw_image,
                (int(draw_image.get_width() * perspective_scale),
                 int(draw_image.get_height() * perspective_scale))
            )
            scaled_rect = scaled_image.get_rect(center=self.image_rect.center)
            screen.blit(scaled_image, scaled_rect)
        else:
            # 기울기가 있을 경우 중심점 유지
            draw_rect = draw_image.get_rect(center=self.image_rect.center)
            screen.blit(draw_image, draw_rect)

        # 5. 궁극기 시각 효과 렌더링
        for effect in self.ultimate_effects:
            if effect["type"] == "NOVA_BLAST":
                # 확장하는 원형 폭발 이펙트
                pygame.draw.circle(screen, effect["color"],
                                   (int(effect["pos"].x), int(effect["pos"].y)),
                                   int(effect["radius"]), 5)

        # 6. Time Freeze 화면 틴트
        if self.time_freeze_active:
            settings = config.ULTIMATE_SETTINGS["TIME_FREEZE"]
            tint = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
            tint.fill(settings["screen_tint"])
            screen.blit(tint, (0, 0))

        # 7. Orbital Strike 레이저 렌더링
        for strike in self.orbital_strikes:
            if strike["active"] and strike["timer"] > 0:
                settings = config.ULTIMATE_SETTINGS["ORBITAL_STRIKE"]
                # 레이저 빔 (빨간 원)
                pygame.draw.circle(screen, settings["color"],
                                   (int(strike["pos"].x), int(strike["pos"].y)),
                                   settings["strike_radius"], 3)
                # 내부 빛나는 효과
                pygame.draw.circle(screen, (255, 200, 200),
                                   (int(strike["pos"].x), int(strike["pos"].y)),
                                   settings["strike_radius"] // 2)

        # 8. Ship Ability: Shield 시각 효과
        if getattr(self, 'shield_active', False):
            shield_hp = getattr(self, 'shield_hp', 0)
            shield_max = getattr(self, 'shield_max_hp', 1)
            shield_ratio = shield_hp / shield_max if shield_max > 0 else 0

            # 보호막 반지름 (플레이어 크기 기반)
            shield_radius = int(max(self.image.get_width(), self.image.get_height()) * 0.8)

            # 펄스 효과 (시간에 따라 크기 변화)
            import math
            pulse = 1.0 + 0.05 * math.sin(pygame.time.get_ticks() * 0.01)
            shield_radius = int(shield_radius * pulse)

            # 쉴드 색상 (HP에 따라 변화)
            if shield_ratio > 0.5:
                shield_color = (100, 180, 255)  # 파랑
            elif shield_ratio > 0.25:
                shield_color = (255, 200, 100)  # 노랑
            else:
                shield_color = (255, 100, 100)  # 빨강

            # 외곽 원 (두꺼운 테두리)
            pygame.draw.circle(screen, shield_color,
                             (int(self.pos.x), int(self.pos.y)),
                             shield_radius, 4)

            # 내부 반투명 원
            shield_surface = pygame.Surface((shield_radius * 2, shield_radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(shield_surface, (*shield_color, 40),
                             (shield_radius, shield_radius), shield_radius)
            screen.blit(shield_surface, (int(self.pos.x) - shield_radius, int(self.pos.y) - shield_radius))


# =========================================================
# 3. 적 클래스
# =========================================================

class Enemy:
    """적 우주선 클래스"""

    def __init__(self, pos: pygame.math.Vector2, screen_height: int, chase_probability: float = 1.0, enemy_type: str = "NORMAL"):

        # 0. 적 타입 설정
        self.enemy_type = enemy_type
        self.type_config = config.ENEMY_TYPES.get(enemy_type, config.ENEMY_TYPES["NORMAL"])

        # 1. 위치 및 이동
        self.pos = pos
        self.speed = config.ENEMY_BASE_SPEED * self.type_config["speed_mult"]
        self.chase_probability = chase_probability  # 플레이어 추적 확률 (0.0 ~ 1.0)
        self.wander_direction = pygame.math.Vector2(random.uniform(-1, 1), random.uniform(-1, 1)).normalize()
        self.wander_timer = 0.0
        self.wander_change_interval = 2.0  # 방황 방향 변경 간격 (초)

        # 2. 스탯 (타입 배율 적용)
        self.max_hp = config.ENEMY_BASE_HP * self.type_config["hp_mult"]
        self.hp = self.max_hp
        self.damage = config.ENEMY_ATTACK_DAMAGE * self.type_config["damage_mult"]
        self.last_attack_time = 0.0
        self.coin_multiplier = self.type_config["coin_mult"]  # 코인 드롭 배율

        # 3. 이미지 및 히트박스 (타입별 크기 적용)
        size_ratio = config.IMAGE_SIZE_RATIOS["ENEMY"]
        image_size = int(screen_height * size_ratio * self.type_config["size_mult"])

        # 이미지 로드 및 색상 tint 적용
        original_image = AssetManager.get_image(config.ENEMY_SHIP_IMAGE_PATH, (image_size, image_size))
        self.color = self.type_config["color_tint"]  # 사망 효과용 색상 저장
        self.size = image_size // 2  # 사망 효과용 크기 저장 (반지름)
        self.image = self._apply_color_tint(original_image, self.color)
        self.image_rect = self.image.get_rect(center=(self.pos.x, self.pos.y))

        hitbox_size = int(image_size * config.ENEMY_HITBOX_RATIO)
        self.hitbox = pygame.Rect(0, 0, hitbox_size, hitbox_size)
        self.hitbox.center = (int(self.pos.x), int(self.pos.y))

        self.is_alive = True
        self.is_boss = False  # 보스 여부

        # 4. 히트 플래시 효과 속성
        self.hit_flash_timer = 0.0
        self.is_flashing = False
        self.original_image = self.image.copy()

        # 5. 속성 스킬 상태 이펙트
        self.is_frozen = False  # 완전 동결 상태
        self.freeze_timer = 0.0
        self.is_slowed = False  # 슬로우 상태
        self.slow_timer = 0.0
        self.slow_ratio = 0.0  # 슬로우 비율 (0.0 ~ 1.0)
        self.base_speed = self.speed  # 기본 속도 저장

        # 6. 포위 공격용 고유 ID (해시값 사용)
        self.enemy_id = id(self)  # 객체의 고유 ID

        # 7. 타입별 특수 능력
        # SHIELDED: 재생 보호막
        self.has_shield = self.type_config.get("has_shield", False)
        self.shield_regen_rate = self.type_config.get("shield_regen_rate", 0.0)
        self.last_regen_time = 0.0

        # SUMMONER: 사망 시 소환
        self.summon_on_death = self.type_config.get("summon_on_death", False)
        self.summon_count = self.type_config.get("summon_count", 0)

        # KAMIKAZE: 자폭
        self.explode_on_contact = self.type_config.get("explode_on_contact", False)
        self.explosion_damage = self.type_config.get("explosion_damage", 0.0)
        self.explosion_radius = self.type_config.get("explosion_radius", 0)
        self.has_exploded = False  # 자폭 여부 (한 번만 폭발)

        # 8. 웨이브 전환 AI 모드
        self.is_respawned = self.type_config.get("is_respawned", False)  # 리스폰 적 여부
        self.is_retreating = False  # 퇴각 모드 (기존 적)
        self.is_circling = False    # 회전 공격 모드 (빨간 적)
        self.circle_angle = random.uniform(0, 2 * math.pi)  # 회전 시작 각도 (랜덤)
        self.retreat_target = None  # 퇴각 목표 위치
        self.escaped = False  # 화면 밖으로 도망 성공 여부 (킬 카운트 제외용)

    def _apply_color_tint(self, image: pygame.Surface, tint_color: tuple) -> pygame.Surface:
        """이미지에 색상 tint를 적용합니다."""
        if tint_color == (255, 255, 255):
            return image  # 원본 색상 그대로

        # 새 surface 생성 (알파 채널 유지)
        tinted = image.copy()

        # 색상 overlay 적용 (BLEND_RGB_MULT 대신 BLEND_RGBA_MULT 사용)
        color_overlay = pygame.Surface(image.get_size(), pygame.SRCALPHA)
        color_overlay.fill((*tint_color, 128))  # 반투명 색상
        tinted.blit(color_overlay, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

        return tinted

    def move_towards_player(self, player_pos: pygame.math.Vector2, dt: float, other_enemies: list = None):
        """플레이어를 향해 이동하되, 다른 적들과 거리를 유지하고 포위 공격합니다."""

        direction = player_pos - self.pos
        distance_to_player = direction.length()

        if direction.length_squared() > 0:
            direction = direction.normalize()

            # 포위 공격: 플레이어 주변에 원형으로 분산
            flank_force = pygame.math.Vector2(0, 0)
            if config.ENEMY_FLANK_ENABLED and distance_to_player < config.ENEMY_FLANK_DISTANCE:
                # 적의 ID를 기반으로 목표 각도 계산 (각 적마다 고유한 각도)
                import math
                base_angle = (self.enemy_id % 360) * (math.pi / 180)  # ID 기반 각도

                # 플레이어 중심으로 목표 위치 계산
                target_offset_x = math.cos(base_angle) * config.ENEMY_FLANK_DISTANCE
                target_offset_y = math.sin(base_angle) * config.ENEMY_FLANK_DISTANCE
                target_pos = pygame.math.Vector2(player_pos.x + target_offset_x, player_pos.y + target_offset_y)

                # 목표 위치로 이동하는 힘
                to_target = target_pos - self.pos
                if to_target.length_squared() > 0:
                    flank_force = to_target.normalize() * 0.5  # 포위 힘

            # 기본 추적 방향에 포위 힘 추가
            direction = direction + flank_force
            if direction.length_squared() > 0:
                direction = direction.normalize()

            # 분리 행동 (Separation): 다른 적들과 거리 유지 - 강화 버전
            separation_force = pygame.math.Vector2(0, 0)
            if other_enemies:
                # 보스는 더 큰 분리 반경 사용
                if hasattr(self, 'is_boss') and self.is_boss:
                    separation_radius = config.ENEMY_SEPARATION_RADIUS * 3.0  # 보스는 3배
                    separation_strength = config.ENEMY_SEPARATION_STRENGTH * 2.0  # 보스는 2배 강도
                else:
                    separation_radius = config.ENEMY_SEPARATION_RADIUS
                    separation_strength = config.ENEMY_SEPARATION_STRENGTH

                separation_count = 0
                for other in other_enemies:
                    if other is not self and other.is_alive:
                        diff = self.pos - other.pos
                        distance = diff.length()

                        # 너무 가까우면 밀어내기
                        if 0 < distance < separation_radius:
                            # 거리에 반비례하는 힘 (가까울수록 강함)
                            # 제곱 반비례로 변경하여 가까울수록 훨씬 강하게
                            force_magnitude = ((separation_radius - distance) / separation_radius) ** 2
                            if distance > 0:
                                diff_normalized = diff.normalize()
                                separation_force += diff_normalized * force_magnitude
                                separation_count += 1

                # 분리 힘 적용 (정규화하지 않고 강도만 곱함)
                if separation_force.length_squared() > 0:
                    # 여러 적과 겹칠수록 더 강한 분리 힘
                    separation_force = separation_force * separation_strength

            # 최종 이동 방향 = 플레이어 추적 + 분리 행동
            # 분리 힘이 강할 때는 추적보다 분리 우선
            separation_magnitude = separation_force.length()
            if separation_magnitude > 1.0:
                # 분리 힘이 강하면 추적 방향의 영향을 줄임
                direction_weight = max(0.3, 1.0 - (separation_magnitude * 0.3))
                final_direction = direction * direction_weight + separation_force
            else:
                final_direction = direction + separation_force

            if final_direction.length_squared() > 0:
                final_direction = final_direction.normalize()

            self.pos += final_direction * self.speed * dt

            # rect 및 hitbox 위치 업데이트
            self.image_rect.center = (int(self.pos.x), int(self.pos.y))
            self.hitbox.center = self.image_rect.center

    def take_damage(self, damage: float, player=None):
        """피해를 입습니다."""
        # Execute 스킬: 체력 임계값 이하 적 즉사
        if player and hasattr(player, 'execute_threshold') and player.execute_threshold > 0:
            hp_ratio = self.hp / self.max_hp
            if hp_ratio <= player.execute_threshold:
                self.hp = 0
                self.is_alive = False
                return  # 즉시 종료

        self.hp -= damage
        if self.hp <= 0:
            self.is_alive = False
        else:
            # 히트 플래시 트리거
            self.hit_flash_timer = config.HIT_FLASH_DURATION
            self.is_flashing = True

    def attack(self, player: 'Player', current_time: float) -> bool:
        """플레이어를 공격합니다. 공격 성공 시 True 반환"""
        if current_time - self.last_attack_time >= config.ENEMY_ATTACK_COOLDOWN:
            player.take_damage(self.damage)
            self.last_attack_time = current_time
            return True
        return False

    def update(self, player_pos: pygame.math.Vector2, dt: float, other_enemies: list = None, screen_size: tuple = None, current_time: float = 0.0):
        """적의 상태를 업데이트합니다."""
        if self.is_alive:
            # SHIELDED 타입: 보호막 재생
            if self.has_shield and self.hp < self.max_hp:
                regen_amount = self.max_hp * self.shield_regen_rate * dt
                self.hp = min(self.max_hp, self.hp + regen_amount)

            # 상태 이펙트 타이머 업데이트
            # 프리즈 상태 업데이트
            if self.is_frozen:
                self.freeze_timer -= dt
                if self.freeze_timer <= 0:
                    self.is_frozen = False
                # 프리즈 상태면 이동 안함
                return

            # 슬로우 상태 업데이트
            if self.is_slowed:
                self.slow_timer -= dt
                if self.slow_timer <= 0:
                    self.is_slowed = False
                    self.speed = self.base_speed  # 속도 복구

            # === 웨이브 전환 AI 모드 ===
            # 1. 퇴각 모드 (기존 적 - 외곽으로 이동)
            if self.is_retreating:
                self._retreat_to_edge(dt, screen_size)
                return

            # 2. 회전 공격 모드 (빨간 적 - 플레이어 주위 회전)
            if self.is_circling:
                self._circle_around_player(player_pos, dt)
                # 히트 플래시 업데이트 후 리턴
                if self.is_flashing:
                    self.hit_flash_timer -= dt
                    if self.hit_flash_timer <= 0:
                        self.is_flashing = False
                        self.image = self.original_image.copy()
                return

            # === 일반 AI 모드 ===
            # 추적 확률에 따라 플레이어를 추적할지 결정
            if random.random() < self.chase_probability:
                # 플레이어를 추적 (다른 적들 정보 전달)
                self.move_towards_player(player_pos, dt, other_enemies)
            else:
                # 방황 모드: 랜덤 방향으로 이동
                self.wander_timer += dt
                if self.wander_timer >= self.wander_change_interval:
                    # 새로운 랜덤 방향 설정
                    self.wander_direction = pygame.math.Vector2(random.uniform(-1, 1), random.uniform(-1, 1)).normalize()
                    self.wander_timer = 0.0

                # 방황 방향으로 이동
                self.pos += self.wander_direction * self.speed * dt * 0.5  # 방황 시 속도 50%
                self.image_rect.center = (int(self.pos.x), int(self.pos.y))
                self.hitbox.center = self.image_rect.center

            # 히트 플래시 타이머 업데이트
            if self.is_flashing:
                self.hit_flash_timer -= dt
                if self.hit_flash_timer <= 0:
                    self.is_flashing = False
                    self.image = self.original_image.copy()

    def _retreat_to_edge(self, dt: float, screen_size: tuple = None):
        """화면 상부로 서서히 퇴각"""
        if screen_size is None:
            screen_size = (1920, 1080)  # 기본값

        # 퇴각 목표: 항상 화면 상부 (현재 x 위치 유지)
        if self.retreat_target is None:
            margin = 100  # 화면 밖 여유
            self.retreat_target = pygame.math.Vector2(self.pos.x, -margin)

        # 목표를 향해 서서히 이동
        direction = self.retreat_target - self.pos
        distance = direction.length()

        if distance > 5:  # 아직 도착 안함
            direction = direction.normalize()
            # 서서히 이동 (속도 0.5배)
            self.pos += direction * self.speed * 0.5 * dt
            self.image_rect.center = (int(self.pos.x), int(self.pos.y))
            self.hitbox.center = self.image_rect.center
        else:
            # 화면 밖 도달 - 제거 대상으로 표시 (도망 성공)
            self.escaped = True  # 공격이 아닌 도망으로 사라짐
            self.is_alive = False

    def _circle_around_player(self, player_pos: pygame.math.Vector2, dt: float):
        """플레이어 주위 80픽셀에서 회전하며 공격 기회를 노림"""
        orbit_radius = 80  # 회전 반경
        orbit_speed = 2.0  # 회전 속도 (rad/s)

        # 회전 각도 업데이트
        self.circle_angle += orbit_speed * dt

        # 목표 위치 계산 (플레이어 주위 원형 궤도)
        target_x = player_pos.x + math.cos(self.circle_angle) * orbit_radius
        target_y = player_pos.y + math.sin(self.circle_angle) * orbit_radius
        target_pos = pygame.math.Vector2(target_x, target_y)

        # 현재 위치에서 목표 위치로 부드럽게 이동
        direction = target_pos - self.pos
        distance = direction.length()

        if distance > 1:
            # 빠르게 궤도로 진입, 궤도 도달 후 회전 유지
            move_speed = self.speed * 2 if distance > orbit_radius else self.speed
            direction = direction.normalize()
            self.pos += direction * move_speed * dt

        self.image_rect.center = (int(self.pos.x), int(self.pos.y))
        self.hitbox.center = self.image_rect.center

    def _calculate_perspective_scale(self, screen_height: int) -> float:
        """Y 위치 기반 원근감 스케일 계산"""
        if not config.PERSPECTIVE_ENABLED or not config.PERSPECTIVE_APPLY_TO_ENEMIES:
            return 1.0

        # Y 위치 비율 계산 (0.0 = 상단, 1.0 = 하단)
        depth_ratio = self.pos.y / screen_height
        depth_ratio = max(0.0, min(1.0, depth_ratio))  # 0~1 범위로 제한

        # 스케일 계산 (상단 = 작게, 하단 = 크게)
        scale = config.PERSPECTIVE_SCALE_MIN + (depth_ratio * (config.PERSPECTIVE_SCALE_MAX - config.PERSPECTIVE_SCALE_MIN))
        return scale

    # ✅ [추가] 화면에 객체를 그리는 draw 메서드
    def draw(self, screen: pygame.Surface):
        """적 객체를 화면에 그리고 체력 바를 표시합니다."""
        # 원근감 스케일 계산
        perspective_scale = self._calculate_perspective_scale(screen.get_height())

        # 히트 플래시 적용
        if self.is_flashing:
            flash_surface = self.original_image.copy()
            flash_surface.fill(config.HIT_FLASH_COLOR, special_flags=pygame.BLEND_RGB_ADD)
            current_image = flash_surface
        else:
            current_image = self.image

        # 원근감 적용된 이미지 생성
        if config.PERSPECTIVE_ENABLED and config.PERSPECTIVE_APPLY_TO_ENEMIES and perspective_scale != 1.0:
            scaled_image = pygame.transform.smoothscale(
                current_image,
                (int(current_image.get_width() * perspective_scale),
                 int(current_image.get_height() * perspective_scale))
            )
            scaled_rect = scaled_image.get_rect(center=self.image_rect.center)
        else:
            scaled_image = current_image
            scaled_rect = self.image_rect

        # 상태 이펙트 시각 효과 (이미지 뒤에 광선 효과)
        if self.is_frozen:
            # 프리즈: 밝은 청백색 광선 효과
            self._draw_glow_effect(screen, (180, 220, 255), intensity=3, layers=3, scale=perspective_scale)
        elif self.is_slowed:
            # 슬로우: 파란색 광선 효과
            self._draw_glow_effect(screen, (100, 150, 255), intensity=2, layers=2, scale=perspective_scale)

        # 이미지 그리기
        screen.blit(scaled_image, scaled_rect)

        # 체력 바 그리기
        self.draw_health_bar(screen, perspective_scale)

    def draw_health_bar(self, screen: pygame.Surface, perspective_scale: float = 1.0):
        """적의 현재 체력을 이미지 위에 작은 바로 표시합니다."""

        # 체력 바를 이미지 너비의 35%로 축소 (1/2 크기, 원근감 스케일 적용)
        bar_width = int(self.image_rect.width * 0.35 * perspective_scale)
        bar_height = max(2, int(3 * perspective_scale))  # 최소 2픽셀
        # 체력 바를 이미지 상단 정중앙에 배치
        bar_x = self.image_rect.centerx - bar_width // 2
        # 이미지 상단에 바로 붙임 (이미지 내부 상단)
        bar_y = self.image_rect.top + 2

        # 배경 (검은색)
        pygame.draw.rect(screen, config.BLACK, (bar_x, bar_y, bar_width, bar_height))

        # 현재 체력 (초록색)
        health_ratio = self.hp / self.max_hp
        current_health_width = int(bar_width * health_ratio)
        pygame.draw.rect(screen, config.GREEN, (bar_x, bar_y, current_health_width, bar_height))

    def _draw_glow_effect(self, screen: pygame.Surface, color: tuple, intensity: int = 2, layers: int = 2, scale: float = 1.0):
        """이미지 윤곽선 기반 광선 효과 (Glow Effect)"""
        # 이미지의 알파 채널을 이용한 마스크 생성
        try:
            # 이미지를 복사하여 마스크 생성
            glow_surface = pygame.Surface(self.image.get_size(), pygame.SRCALPHA)

            # 여러 레이어로 광선 효과 생성
            for layer in range(layers, 0, -1):
                # 각 레이어마다 크기와 투명도 조정
                scale_factor = 1.0 + (layer * intensity * 0.02)  # 2%씩 확대
                scale_factor *= scale  # 원근감 스케일 적용
                alpha = int(80 / layer)  # 레이어마다 투명도 감소

                # 확대된 이미지 생성
                scaled_size = (
                    int(self.image.get_width() * scale_factor),
                    int(self.image.get_height() * scale_factor)
                )
                scaled_image = pygame.transform.scale(self.image, scaled_size)

                # 색상 적용
                colored_surface = scaled_image.copy()
                colored_surface.fill(color + (0,), special_flags=pygame.BLEND_RGBA_MULT)
                colored_surface.fill((255, 255, 255, alpha), special_flags=pygame.BLEND_RGBA_MIN)

                # 중앙 정렬하여 그리기
                offset_x = (scaled_size[0] - self.image.get_width()) // 2
                offset_y = (scaled_size[1] - self.image.get_height()) // 2
                glow_rect = colored_surface.get_rect(center=self.image_rect.center)
                screen.blit(colored_surface, glow_rect)
        except:
            # 광선 효과 실패 시 원형 광선으로 폴백
            for layer in range(layers, 0, -1):
                radius = self.image_rect.width // 2 + layer * intensity
                alpha = int(60 / layer)

                glow_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(glow_surf, color + (alpha,), (radius, radius), radius)
                glow_rect = glow_surf.get_rect(center=self.image_rect.center)
                screen.blit(glow_surf, glow_rect)

# =========================================================
# 4. 총알 클래스
# =========================================================

class Bullet:
    """총알 클래스"""

    def __init__(self, pos: pygame.math.Vector2, direction: pygame.math.Vector2, damage: float, piercing: bool = False):

        # 1. 위치 및 이동
        self.pos = pos
        self.direction = direction.normalize()
        self.speed = config.BULLET_SPEED

        # 2. 스탯
        self.damage = damage
        self.is_alive = True

        # 3. 피어싱 기능
        self.is_piercing = piercing
        self.pierce_count = 0  # 관통한 적 수 (최대값 도달 시 제거)
        self.hit_enemies = set()  # 이미 맞춘 적 ID 집합 (중복 피격 방지)

        # 4. 총알 트레일 (잔상)
        self.trail_positions = []  # 이전 위치들 저장

        # 5. 스폰 시간 (벽 충돌 유예 기간용)
        self.spawn_time = pygame.time.get_ticks()

        # 6. 이미지 및 히트박스
        # bullet_image는 asset_manager에서 공통으로 사용하므로 최초 1회만 로드

    def initialize_image(self, screen_height: int):
        """화면 크기에 맞게 총알 이미지를 초기화합니다."""

        size_ratio = config.IMAGE_SIZE_RATIOS["BULLET"]
        image_size = int(screen_height * size_ratio)

        self.image = AssetManager.get_image(config.PLAYER_BULLET_IMAGE_PATH, (image_size, image_size))
        self.image_rect = self.image.get_rect(center=(self.pos.x, self.pos.y))

        hitbox_size = int(image_size * config.BULLET_HITBOX_RATIO)
        self.hitbox = pygame.Rect(0, 0, hitbox_size, hitbox_size)
        self.hitbox.center = (int(self.pos.x), int(self.pos.y))

    def update(self, dt: float, screen_size: Tuple[int, int]):
        """총알 위치를 업데이트하고, 화면 밖으로 나가면 제거합니다."""

        if not hasattr(self, 'image'):
            # 첫 update 시 이미지 초기화
            self.initialize_image(screen_size[1])

        if self.is_alive:
            # 현재 위치를 트레일에 추가
            self.trail_positions.append(self.pos.copy())

            # 트레일 길이 제한
            if len(self.trail_positions) > config.BULLET_TRAIL_LENGTH:
                self.trail_positions.pop(0)

            self.pos += self.direction * self.speed * dt
            self.image_rect.center = (int(self.pos.x), int(self.pos.y))
            self.hitbox.center = self.image_rect.center

            # 화면 밖으로 나가면 제거
            SCREEN_WIDTH, SCREEN_HEIGHT = screen_size
            if (self.pos.x < -50 or self.pos.x > SCREEN_WIDTH + 50 or
                self.pos.y < -50 or self.pos.y > SCREEN_HEIGHT + 50):
                self.is_alive = False

    def draw(self, screen: pygame.Surface):
        """총알 객체와 트레일을 화면에 그립니다."""
        if self.is_alive:
            # 이미지가 아직 초기화되지 않았다면 폴백 렌더링
            if not hasattr(self, 'image') or self.image is None:
                # 간단한 원으로 그리기 (폴백)
                pygame.draw.circle(screen, (255, 0, 0), (int(self.pos.x), int(self.pos.y)), 20, 0)
                pygame.draw.circle(screen, (255, 255, 0), (int(self.pos.x), int(self.pos.y)), 20, 3)
                return

            # 원근감 스케일 계산
            perspective_scale = self._calculate_perspective_scale(screen.get_height())

            # 원근감 적용된 이미지
            if config.PERSPECTIVE_ENABLED and config.PERSPECTIVE_APPLY_TO_BULLETS and perspective_scale != 1.0:
                scaled_image = pygame.transform.scale(
                    self.image,
                    (int(self.image.get_width() * perspective_scale),
                     int(self.image.get_height() * perspective_scale))
                )
                scaled_rect = scaled_image.get_rect(center=self.image_rect.center)
            else:
                scaled_image = self.image
                scaled_rect = self.image_rect

            # 트레일 그리기 (뒤에서부터 앞으로, 점점 투명하게)
            for i, trail_pos in enumerate(self.trail_positions):
                alpha = int(255 * (i + 1) / len(self.trail_positions) * config.BULLET_TRAIL_ALPHA_DECAY)
                alpha = max(0, min(255, alpha))

                # 트레일용 반투명 서피스 생성
                trail_surf = scaled_image.copy()
                trail_surf.set_alpha(alpha)
                trail_rect = trail_surf.get_rect(center=(int(trail_pos.x), int(trail_pos.y)))
                screen.blit(trail_surf, trail_rect)

            # 총알 본체 그리기
            screen.blit(scaled_image, scaled_rect)

    def _calculate_perspective_scale(self, screen_height: int) -> float:
        """Y 위치 기반 원근감 스케일 계산"""
        if not config.PERSPECTIVE_ENABLED or not config.PERSPECTIVE_APPLY_TO_BULLETS:
            return 1.0

        # Y 위치 비율 계산 (0.0 = 상단, 1.0 = 하단)
        depth_ratio = self.pos.y / screen_height
        depth_ratio = max(0.0, min(1.0, depth_ratio))

        # 스케일 계산
        scale = config.PERSPECTIVE_SCALE_MIN + (depth_ratio * (config.PERSPECTIVE_SCALE_MAX - config.PERSPECTIVE_SCALE_MIN))
        return scale

# =========================================================
# 5. 아이템 클래스
# =========================================================

class CoinGem:
    """코인/젬 클래스 (적을 죽이면 드롭)"""

    COIN_AMOUNT = config.BASE_COIN_DROP_PER_KILL # 코인 획득 시 점수

    def __init__(self, pos: Tuple[float, float], screen_height: int):

        # 1. 위치
        self.pos = pygame.math.Vector2(pos)

        # 2. 상태
        self.collected = False

        # 3. 이미지 및 히트박스
        size_ratio = config.IMAGE_SIZE_RATIOS["COINGEM"]
        image_size = int(screen_height * size_ratio)

        self.image = AssetManager.get_image(config.COIN_GEM_IMAGE_PATH, (image_size, image_size))
        self.image_rect = self.image.get_rect(center=(self.pos.x, self.pos.y))

        hitbox_size = int(image_size * config.GEM_HITBOX_RATIO)
        self.hitbox = pygame.Rect(0, 0, hitbox_size, hitbox_size)
        self.hitbox.center = (int(self.pos.x), int(self.pos.y))

    def update(self, dt: float, player):
        """
        자석 효과가 있으면 플레이어에게 끌어당깁니다.
        """
        # 자석 효과 확인 (player에 has_coin_magnet 속성이 있다면)
        has_coin_magnet = getattr(player, 'has_coin_magnet', False)

        if not self.collected and has_coin_magnet:
            # 플레이어와의 거리 계산
            direction = player.pos - self.pos
            distance = direction.length()

            # 자석 효과 범위 (플레이어 이미지 크기의 10배 정도로 가정)
            MAGNET_RANGE = player.image_rect.width * 10

            if distance < MAGNET_RANGE:
                # 플레이어에게 끌어당기는 속도 (거리와 비례)
                MAGNET_SPEED = 500.0
                if distance > 0:
                    direction = direction.normalize()
                    # 이동 속도를 dt와 MAGNET_SPEED로 계산
                    self.pos += direction * MAGNET_SPEED * dt
                    self.image_rect.center = (int(self.pos.x), int(self.pos.y))
                    self.hitbox.center = self.image_rect.center

    def collect(self, game_data: Dict) -> bool:
        """젬 수집 효과 적용 (점수 증가)"""
        if not self.collected:
            # 영구 코인과 레벨업 점수 모두 증가
            game_data['score'] += self.COIN_AMOUNT
            game_data['uncollected_score'] += self.COIN_AMOUNT
            self.collected = True
            return True
        return False

    def draw(self, screen: pygame.Surface):
        """젬 객체를 화면에 그립니다."""
        if not self.collected:
            # 원근감 스케일 계산
            perspective_scale = self._calculate_perspective_scale(screen.get_height())

            # 원근감 적용된 이미지
            if config.PERSPECTIVE_ENABLED and config.PERSPECTIVE_APPLY_TO_GEMS and perspective_scale != 1.0:
                scaled_image = pygame.transform.scale(
                    self.image,
                    (int(self.image.get_width() * perspective_scale),
                     int(self.image.get_height() * perspective_scale))
                )
                scaled_rect = scaled_image.get_rect(center=self.image_rect.center)
                screen.blit(scaled_image, scaled_rect)
            else:
                screen.blit(self.image, self.image_rect)

    def _calculate_perspective_scale(self, screen_height: int) -> float:
        """Y 위치 기반 원근감 스케일 계산"""
        if not config.PERSPECTIVE_ENABLED or not config.PERSPECTIVE_APPLY_TO_GEMS:
            return 1.0

        # Y 위치 비율 계산 (0.0 = 상단, 1.0 = 하단)
        depth_ratio = self.pos.y / screen_height
        depth_ratio = max(0.0, min(1.0, depth_ratio))

        # 스케일 계산
        scale = config.PERSPECTIVE_SCALE_MIN + (depth_ratio * (config.PERSPECTIVE_SCALE_MAX - config.PERSPECTIVE_SCALE_MIN))
        return scale


class HealItem:
    """체력 회복 아이템 클래스"""

    HEAL_AMOUNT = config.HEAL_AMOUNT # 회복량

    def __init__(self, pos: Tuple[float, float], screen_height: int):

        # 1. 위치
        self.pos = pygame.math.Vector2(pos)

        # 2. 상태
        self.collected = False

        # 3. 이미지 및 히트박스
        size_ratio = config.IMAGE_SIZE_RATIOS["GEMHP"]
        image_size = int(screen_height * size_ratio)

        self.image = AssetManager.get_image(config.GEM_HP_IMAGE_PATH, (image_size, image_size))
        self.image_rect = self.image.get_rect(center=(self.pos.x, self.pos.y))

        hitbox_size = int(image_size * config.GEM_HITBOX_RATIO)
        self.hitbox = pygame.Rect(0, 0, hitbox_size, hitbox_size)
        self.hitbox.center = (int(self.pos.x), int(self.pos.y))

    def update(self, dt: float, player):
        """
        자석 효과가 있으면 플레이어에게 끌어당깁니다.
        """
        # 자석 효과 확인 (player에 has_coin_magnet 속성이 있다면)
        has_coin_magnet = getattr(player, 'has_coin_magnet', False)

        if not self.collected and has_coin_magnet:
            # 플레이어와의 거리 계산
            direction = player.pos - self.pos
            distance = direction.length()

            # 자석 효과 범위 (플레이어 이미지 크기의 10배 정도로 가정)
            MAGNET_RANGE = player.image_rect.width * 10

            if distance < MAGNET_RANGE:
                # 플레이어에게 끌어당기는 속도 (거리와 비례)
                MAGNET_SPEED = 500.0
                if distance > 0:
                    direction = direction.normalize()
                    # 이동 속도를 dt와 MAGNET_SPEED로 계산
                    self.pos += direction * MAGNET_SPEED * dt
                    self.image_rect.center = (int(self.pos.x), int(self.pos.y))
                    self.hitbox.center = self.image_rect.center

    def collect(self, player) -> bool:
        """체력 회복 아이템 수집 효과 적용 (플레이어 HP 회복)"""
        if not self.collected:
            # 플레이어 체력 회복
            player.heal(self.HEAL_AMOUNT)
            self.collected = True
            return True
        return False

    def draw(self, screen: pygame.Surface):
        """젬 객체를 화면에 그립니다."""
        if not self.collected:
            screen.blit(self.image, self.image_rect)


# =========================================================
# 6. 보스 클래스
# =========================================================

class Boss(Enemy):
    """보스 적 클래스 - Enemy를 상속받되 크기와 체력이 훨씬 큼"""

    def __init__(self, pos: pygame.math.Vector2, screen_height: int, boss_name: str = "Boss", wave_number: int = 5):
        # Enemy 초기화를 호출하되, 이미지 크기를 재설정하기 위해 super() 호출 전에 준비

        # 1. 위치 및 이동
        self.pos = pos
        self.speed = config.ENEMY_BASE_SPEED
        self.chase_probability = 1.0  # 보스는 항상 추적
        self.wander_direction = pygame.math.Vector2(0, 0)
        self.wander_timer = 0.0
        self.wander_change_interval = 2.0

        # 2. 스탯
        self.max_hp = config.ENEMY_BASE_HP
        self.hp = self.max_hp
        self.damage = config.ENEMY_ATTACK_DAMAGE
        self.last_attack_time = 0.0

        # 3. 보스 전용 속성
        self.is_boss = True
        self.boss_name = boss_name
        self.wave_number = wave_number

        # 4. 이미지 및 히트박스 (보스 이름에 따라 크기 다르게)
        if boss_name == "The Swarm Queen":
            size_multiplier = 2.0  # 웨이브 5 보스: 2배 크기
        elif boss_name == "The Void Core":
            size_multiplier = 5.0  # 웨이브 10 보스: 5배 크기
        else:
            size_multiplier = 3.0  # 기본 보스: 3배 크기

        size_ratio = config.IMAGE_SIZE_RATIOS["ENEMY"] * size_multiplier
        image_size = int(screen_height * size_ratio)

        self.color = (255, 50, 50)  # 보스 색상 (빨간색)
        self.size = image_size // 2  # 사망 효과용 크기 저장 (반지름)
        self.image = AssetManager.get_image(config.ENEMY_SHIP_IMAGE_PATH, (image_size, image_size))
        self.image_rect = self.image.get_rect(center=(self.pos.x, self.pos.y))

        hitbox_size = int(image_size * config.ENEMY_HITBOX_RATIO)
        self.hitbox = pygame.Rect(0, 0, hitbox_size, hitbox_size)
        self.hitbox.center = (int(self.pos.x), int(self.pos.y))

        self.is_alive = True

        # 5. 히트 플래시 효과 속성 (Enemy에서도 있지만 이미지가 재설정되므로 다시 저장)
        self.hit_flash_timer = 0.0
        self.is_flashing = False
        self.original_image = self.image.copy()

        # 6. 속성 스킬 상태 이펙트 (보스는 영향받지 않지만 속성은 필요)
        self.is_frozen = False
        self.freeze_timer = 0.0
        self.is_slowed = False
        self.slow_timer = 0.0
        self.slow_ratio = 0.0
        self.base_speed = self.speed

        # 7. 포위 공격용 고유 ID
        self.enemy_id = id(self)

        # 8. 보스 패턴 시스템
        self.current_phase = 0  # 현재 페이즈 (0, 1, 2)
        self.current_pattern = None  # 현재 실행 중인 패턴
        self.pattern_timer = 0.0  # 패턴 타이머

        # Circle Strafe 패턴
        self.orbit_angle = 0.0  # 현재 궤도 각도

        # Charge Attack 패턴
        self.is_charging = False
        self.charge_direction = pygame.math.Vector2(0, 0)
        self.last_charge_time = 0.0

        # Berserk 모드
        self.is_berserk = False

        # Summon 패턴
        self.last_summon_time = 0.0
        self.summoned_enemies = []  # 소환된 적 참조 리스트

        # Burn Attack 패턴
        self.last_burn_attack_time = 0.0
        self.burn_projectiles = []  # 발사된 burn 발사체 리스트

    def update(self, player_pos: pygame.math.Vector2, dt: float, other_enemies: list = None, screen_size: tuple = None, current_time: float = 0.0):
        """보스의 상태와 패턴을 업데이트합니다."""
        if not self.is_alive:
            return

        # 페이즈 체크 및 업데이트
        hp_ratio = self.hp / self.max_hp
        if hp_ratio <= 0.33 and self.current_phase < 2:
            self.current_phase = 2
        elif hp_ratio <= 0.66 and self.current_phase < 1:
            self.current_phase = 1

        # Berserk 모드 체크 (HP 25% 이하)
        if hp_ratio <= config.BOSS_PATTERN_SETTINGS["BERSERK"]["hp_threshold"] and not self.is_berserk:
            self.is_berserk = True
            self.speed = self.base_speed * config.BOSS_PATTERN_SETTINGS["BERSERK"]["speed_mult"]
            self.damage = config.ENEMY_ATTACK_DAMAGE * config.BOSS_PATTERN_SETTINGS["BERSERK"]["damage_mult"]

        # 패턴 타이머 업데이트
        self.pattern_timer += dt

        # 소환 패턴 (쿨다운 체크)
        if current_time - self.last_summon_time >= config.BOSS_PATTERN_SETTINGS["SUMMON_MINIONS"]["summon_cooldown"]:
            if random.random() < 0.3:  # 30% 확률로 소환 시도
                self._summon_minions(other_enemies)
                self.last_summon_time = current_time

        # 돌진 패턴 (쿨다운 체크)
        if current_time - self.last_charge_time >= config.BOSS_PATTERN_SETTINGS["CHARGE_ATTACK"]["cooldown"]:
            if random.random() < 0.4:  # 40% 확률로 돌진 시도
                self._start_charge(player_pos)
                self.last_charge_time = current_time

        # Burn 발사체 공격 패턴 (일정 주기로 발사)
        burn_settings = config.BOSS_PATTERN_SETTINGS["BURN_ATTACK"]
        if current_time - self.last_burn_attack_time >= burn_settings["fire_interval"]:
            self._fire_burn_projectiles()
            self.last_burn_attack_time = current_time

        # Burn 발사체 업데이트
        for proj in self.burn_projectiles[:]:
            proj.update(dt, screen_size)
            if not proj.is_alive:
                self.burn_projectiles.remove(proj)

        # 현재 패턴에 따라 이동
        if self.is_charging:
            self._update_charge(dt)
        elif self.current_pattern == "CIRCLE_STRAFE":
            self._update_circle_strafe(player_pos, dt)
        else:
            # 기본 추적 (Enemy의 move_towards_player 사용)
            super().move_towards_player(player_pos, dt, other_enemies)

        # 히트 플래시 타이머 업데이트
        if self.is_flashing:
            self.hit_flash_timer -= dt
            if self.hit_flash_timer <= 0:
                self.is_flashing = False
                self.image = self.original_image.copy()

    def _summon_minions(self, enemy_list: list):
        """미니언을 소환합니다."""
        if enemy_list is None:
            return

        summon_count = config.BOSS_PATTERN_SETTINGS["SUMMON_MINIONS"]["summon_count"].get(self.wave_number, 2)
        minion_hp_ratio = config.BOSS_PATTERN_SETTINGS["SUMMON_MINIONS"]["minion_hp_ratio"]

        for i in range(summon_count):
            # 보스 주변에 랜덤 위치 생성
            offset_x = random.uniform(-100, 100)
            offset_y = random.uniform(-100, 100)
            spawn_pos = pygame.math.Vector2(self.pos.x + offset_x, self.pos.y + offset_y)

            # 미니언 생성 (NORMAL 타입)
            from objects import Enemy  # 순환 참조 방지
            minion = Enemy(spawn_pos, self.image_rect.height * 10, 1.0, "NORMAL")  # screen_height 근사값
            minion.hp = self.max_hp * minion_hp_ratio
            minion.max_hp = minion.hp

            enemy_list.append(minion)
            self.summoned_enemies.append(minion)

    def _fire_burn_projectiles(self):
        """Burn 발사체를 사방으로 발사합니다."""
        burn_settings = config.BOSS_PATTERN_SETTINGS["BURN_ATTACK"]
        projectile_count = burn_settings["projectile_count"]

        # 사방으로 균등하게 발사 (원형 배치)
        for i in range(projectile_count):
            angle = (2 * math.pi / projectile_count) * i
            direction = pygame.math.Vector2(math.cos(angle), math.sin(angle))

            projectile = BurnProjectile(self.pos.copy(), direction)
            self.burn_projectiles.append(projectile)

    def draw_burn_projectiles(self, screen: pygame.Surface):
        """Burn 발사체들을 그립니다."""
        for proj in self.burn_projectiles:
            proj.draw(screen)

    def check_burn_collision_with_player(self, player) -> float:
        """모든 Burn 발사체와 플레이어의 충돌을 검사하고 총 데미지를 반환합니다."""
        total_damage = 0.0
        for proj in self.burn_projectiles[:]:
            if proj.check_collision_with_player(player):
                total_damage += proj.damage
                proj.is_alive = False  # 충돌한 발사체 제거
        return total_damage

    def _start_charge(self, player_pos: pygame.math.Vector2):
        """돌진 공격 시작."""
        self.is_charging = True
        direction = player_pos - self.pos
        if direction.length_squared() > 0:
            self.charge_direction = direction.normalize()
        self.pattern_timer = 0.0

    def _update_charge(self, dt: float):
        """돌진 공격 업데이트."""
        charge_duration = config.BOSS_PATTERN_SETTINGS["CHARGE_ATTACK"]["charge_duration"]

        if self.pattern_timer >= charge_duration:
            self.is_charging = False
            return

        charge_speed = self.base_speed * config.BOSS_PATTERN_SETTINGS["CHARGE_ATTACK"]["charge_speed_mult"]
        self.pos += self.charge_direction * charge_speed * dt

        # 위치 및 hitbox 업데이트
        self.image_rect.center = (int(self.pos.x), int(self.pos.y))
        self.hitbox.center = self.image_rect.center

    def _update_circle_strafe(self, player_pos: pygame.math.Vector2, dt: float):
        """원형 궤도 이동 패턴."""
        orbit_radius = config.BOSS_PATTERN_SETTINGS["CIRCLE_STRAFE"]["orbit_radius"]
        orbit_speed = config.BOSS_PATTERN_SETTINGS["CIRCLE_STRAFE"]["orbit_speed"]

        # 각도 업데이트
        self.orbit_angle += orbit_speed * dt

        # 플레이어 주변 궤도 위치 계산
        target_x = player_pos.x + math.cos(self.orbit_angle) * orbit_radius
        target_y = player_pos.y + math.sin(self.orbit_angle) * orbit_radius
        target_pos = pygame.math.Vector2(target_x, target_y)

        # 목표 위치로 이동
        direction = target_pos - self.pos
        if direction.length_squared() > 0:
            direction = direction.normalize()
            self.pos += direction * self.speed * dt

        # 위치 및 hitbox 업데이트
        self.image_rect.center = (int(self.pos.x), int(self.pos.y))
        self.hitbox.center = self.image_rect.center

    def draw(self, screen: pygame.Surface):
        """보스를 화면에 그립니다. (크로마틱 어버레이션 효과 포함)"""
        # 히트 플래시 적용
        if self.is_flashing:
            flash_surface = self.original_image.copy()
            flash_surface.fill(config.HIT_FLASH_COLOR, special_flags=pygame.BLEND_RGB_ADD)
            self.image = flash_surface

        # 크로마틱 어버레이션 효과 (RGB 분리) - 투명도 유지
        if config.CHROMATIC_ABERRATION_SETTINGS["BOSS"]["enabled"]:
            offset = config.CHROMATIC_ABERRATION_SETTINGS["BOSS"]["offset"]

            # 원본 이미지의 알파 채널 보존
            width, height = self.image.get_size()

            # 빨간 채널 이미지 생성 (투명도 유지)
            red_surface = self.image.copy()
            red_array = pygame.surfarray.pixels3d(red_surface)
            red_alpha = pygame.surfarray.pixels_alpha(red_surface)

            # Green, Blue 채널 제거
            red_array[:, :, 1] = 0
            red_array[:, :, 2] = 0

            # 알파 채널 유지하면서 전체 투명도 조정
            red_alpha[:] = (red_alpha[:] * 0.6).astype('uint8')  # 60% 투명도
            del red_array, red_alpha  # 배열 잠금 해제
            screen.blit(red_surface, (self.image_rect.x - offset, self.image_rect.y))

            # 파란 채널 이미지 생성 (투명도 유지)
            blue_surface = self.image.copy()
            blue_array = pygame.surfarray.pixels3d(blue_surface)
            blue_alpha = pygame.surfarray.pixels_alpha(blue_surface)

            # Red, Green 채널 제거
            blue_array[:, :, 0] = 0
            blue_array[:, :, 1] = 0

            # 알파 채널 유지하면서 전체 투명도 조정
            blue_alpha[:] = (blue_alpha[:] * 0.6).astype('uint8')  # 60% 투명도
            del blue_array, blue_alpha  # 배열 잠금 해제
            screen.blit(blue_surface, (self.image_rect.x + offset, self.image_rect.y))

        # 원본 이미지 (중앙)
        screen.blit(self.image, self.image_rect)

    def _draw_glow_effect(self, screen: pygame.Surface, color: tuple, intensity: int = 2, layers: int = 2):
        """이미지 윤곽선 기반 광선 효과 (Glow Effect) - Boss용"""
        # 보스는 크로마틱 어버레이션이 있어 광선 효과 단순화
        for layer in range(layers, 0, -1):
            radius = self.image_rect.width // 2 + layer * intensity * 2
            alpha = int(60 / layer)

            glow_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, color + (alpha,), (radius, radius), radius)
            glow_rect = glow_surf.get_rect(center=self.image_rect.center)
            screen.blit(glow_surf, glow_rect)


# =========================================================
# 6.5. 보스 Burn 발사체 클래스 (Boss Burn Projectile)
# =========================================================

class BurnProjectile:
    """보스가 발사하는 Burn 발사체 클래스 - 플레이어와 충돌 시 데미지"""

    def __init__(self, pos: pygame.math.Vector2, direction: pygame.math.Vector2):
        """
        Args:
            pos: 발사 위치 (보스 위치)
            direction: 발사 방향 (정규화된 벡터)
        """
        self.pos = pygame.math.Vector2(pos)
        self.direction = direction.normalize() if direction.length_squared() > 0 else pygame.math.Vector2(1, 0)

        # 설정값 로드
        burn_settings = config.BOSS_PATTERN_SETTINGS["BURN_ATTACK"]
        self.speed = burn_settings["projectile_speed"]
        self.damage = burn_settings["damage"]
        self.lifetime = burn_settings["lifetime"]
        self.age = 0.0
        self.is_alive = True

        # 이미지 로드
        image_size = burn_settings["projectile_size"]
        try:
            self.image = AssetManager.get_image(config.ENEMY_SHIP_BURN_IMAGE_PATH, (image_size, image_size))
        except Exception:
            # 이미지 로드 실패 시 기본 서피스 생성
            self.image = pygame.Surface((image_size, image_size), pygame.SRCALPHA)
            pygame.draw.circle(self.image, (255, 100, 50), (image_size // 2, image_size // 2), image_size // 2)

        self.image_rect = self.image.get_rect(center=(int(self.pos.x), int(self.pos.y)))

        # 히트박스 (이미지보다 약간 작게)
        hitbox_size = int(image_size * 0.7)
        self.hitbox = pygame.Rect(0, 0, hitbox_size, hitbox_size)
        self.hitbox.center = (int(self.pos.x), int(self.pos.y))

    def update(self, dt: float, screen_size: tuple = None):
        """발사체 업데이트"""
        if not self.is_alive:
            return

        # 수명 체크
        self.age += dt
        if self.age >= self.lifetime:
            self.is_alive = False
            return

        # 이동
        self.pos += self.direction * self.speed * dt

        # 위치 업데이트
        self.image_rect.center = (int(self.pos.x), int(self.pos.y))
        self.hitbox.center = self.image_rect.center

        # 화면 밖으로 나가면 제거
        if screen_size:
            margin = 100
            if (self.pos.x < -margin or self.pos.x > screen_size[0] + margin or
                self.pos.y < -margin or self.pos.y > screen_size[1] + margin):
                self.is_alive = False

    def draw(self, screen: pygame.Surface):
        """발사체 그리기"""
        if not self.is_alive:
            return

        # 회전 효과 (나이에 따라 회전)
        rotation_angle = self.age * 180  # 초당 180도 회전
        rotated_image = pygame.transform.rotate(self.image, rotation_angle)
        rotated_rect = rotated_image.get_rect(center=self.image_rect.center)

        screen.blit(rotated_image, rotated_rect)

    def check_collision_with_player(self, player) -> bool:
        """플레이어와 충돌 검사"""
        if not self.is_alive:
            return False
        # Player 클래스는 is_dead 속성 사용 (is_alive가 아님)
        if hasattr(player, 'is_dead') and player.is_dead:
            return False

        return self.hitbox.colliderect(player.hitbox)


# =========================================================
# 7. 시각 효과 클래스들 (Visual Effects)
# =========================================================

class Particle:
    """파티클 효과 클래스 - 폭발, 충돌 등에 사용"""

    def __init__(self, pos: Tuple[float, float], velocity: pygame.math.Vector2,
                 color: Tuple[int, int, int], size: int, lifetime: float, gravity: bool = True):
        self.pos = pygame.math.Vector2(pos)
        self.velocity = velocity
        self.color = color
        self.size = size
        self.lifetime = lifetime
        self.age = 0.0
        self.gravity = gravity
        self.is_alive = True

    def update(self, dt: float):
        """파티클 업데이트"""
        self.age += dt
        if self.age >= self.lifetime:
            self.is_alive = False
            return

        # 위치 업데이트
        self.pos += self.velocity * dt

        # 중력 효과
        if self.gravity:
            self.velocity.y += 300 * dt  # 중력 가속도

        # 감속 (공기 저항)
        self.velocity *= 0.98

    def draw(self, screen: pygame.Surface):
        """파티클 그리기"""
        if not self.is_alive:
            return

        # 알파값 계산 (시간에 따라 페이드 아웃)
        alpha = int(255 * (1 - self.age / self.lifetime))
        alpha = max(0, min(255, alpha))

        # 크기 감소
        current_size = max(1, int(self.size * (1 - self.age / self.lifetime)))

        # 반투명 서피스 생성
        surf = pygame.Surface((current_size * 2, current_size * 2), pygame.SRCALPHA)
        color_with_alpha = self.color + (alpha,)
        pygame.draw.circle(surf, color_with_alpha, (current_size, current_size), current_size)

        screen.blit(surf, (int(self.pos.x - current_size), int(self.pos.y - current_size)))


class Shockwave:
    """충격파 효과 - 중심에서 확장되는 원형 링 (지연 시간 지원)"""

    def __init__(self, center: Tuple[float, float], max_radius: float,
                 duration: float, color: Tuple[int, int, int], width: int = 3, delay: float = 0.0):
        self.center = pygame.math.Vector2(center)
        self.max_radius = max_radius
        self.duration = duration
        self.color = color
        self.width = width
        self.delay = delay  # 시작 지연 시간
        self.age = -delay  # 지연 시간만큼 음수로 시작
        self.is_alive = True

    def update(self, dt: float):
        """충격파 업데이트"""
        self.age += dt
        if self.age >= self.duration:
            self.is_alive = False

    def draw(self, screen: pygame.Surface):
        """충격파 그리기"""
        if not self.is_alive or self.age < 0:
            # 아직 지연 시간이 남았으면 그리지 않음
            return

        # 진행도 계산
        progress = self.age / self.duration
        current_radius = int(self.max_radius * progress)

        # 알파값 계산 (시간에 따라 페이드 아웃)
        alpha = int(255 * (1 - progress))
        alpha = max(0, min(255, alpha))

        # 반투명 서피스 생성
        size = current_radius * 2 + 10
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        color_with_alpha = self.color + (alpha,)
        pygame.draw.circle(surf, color_with_alpha, (size // 2, size // 2), current_radius, self.width)

        screen.blit(surf, (int(self.center.x - size // 2), int(self.center.y - size // 2)))


class ScreenFlash:
    """화면 플래시 효과 - 전체 화면에 색상 오버레이"""

    def __init__(self, screen_size: Tuple[int, int], color: Tuple[int, int, int] = (255, 255, 255), duration: float = 0.3):
        self.screen_size = screen_size
        self.color = color
        self.duration = duration
        self.age = 0.0
        self.is_alive = True

    def update(self, dt: float):
        """플래시 업데이트"""
        self.age += dt
        if self.age >= self.duration:
            self.is_alive = False

    def draw(self, screen: pygame.Surface):
        """플래시 그리기"""
        if not self.is_alive:
            return

        # 진행도 계산 (0 → 1)
        progress = self.age / self.duration

        # 알파값 계산 (처음 밝았다가 점점 사라짐)
        alpha = int(150 * (1 - progress))
        alpha = max(0, min(255, alpha))

        # 반투명 오버레이
        surf = pygame.Surface(self.screen_size, pygame.SRCALPHA)
        surf.fill((*self.color, alpha))
        screen.blit(surf, (0, 0))


class WaveTransitionEffect:
    """웨이브 전환 효과 - 화면 어두워짐과 동시에 이미지가 중앙에서 서서히 등장 (외곽 페이드 적용)"""

    # 페이즈 상수
    PHASE_DARKEN = 0      # 화면 어두워지면서 이미지 등장
    PHASE_SHOW_IMAGE = 1  # 이미지 유지
    PHASE_BRIGHTEN = 2    # 화면 밝아지면서 이미지 사라짐
    PHASE_DONE = 3        # 완료

    def __init__(self, screen_size: Tuple[int, int], image_path: str = None,
                 darken_duration: float = 3.5, image_duration: float = 2.0, brighten_duration: float = 3.0):
        self.screen_size = screen_size
        self.darken_duration = darken_duration  # 아주 느리게: 3.5초
        self.image_duration = image_duration    # 유지: 2초
        self.brighten_duration = brighten_duration  # 아주 느리게: 3초
        self.total_duration = darken_duration + image_duration + brighten_duration

        self.age = 0.0
        self.is_alive = True
        self.phase = self.PHASE_DARKEN
        self.on_darken_complete = None

        # 이미지 로드
        self.image = None
        self.original_image = None  # 원본 이미지 저장
        if image_path:
            try:
                from pathlib import Path
                path = Path(image_path)
                if path.exists():
                    loaded_img = pygame.image.load(str(path)).convert_alpha()
                    # 화면 크기에 맞게 스케일 (비율 유지, 85% 크기 - 더 크게)
                    img_w, img_h = loaded_img.get_size()
                    scale = min(screen_size[0] * 0.85 / img_w, screen_size[1] * 0.85 / img_h)
                    new_size = (int(img_w * scale), int(img_h * scale))
                    self.original_image = pygame.transform.smoothscale(loaded_img, new_size)
                    # 외곽 페이드 마스크 적용
                    self.image = self._apply_edge_fade(self.original_image)
                    print(f"INFO: Loaded wave transition image: {path}")
                else:
                    print(f"WARNING: Wave transition image not found: {path}")
            except Exception as e:
                print(f"WARNING: Failed to load wave transition image: {e}")

    def _apply_edge_fade(self, surface: pygame.Surface) -> pygame.Surface:
        """이미지 외곽에 페이드 효과 적용 (비네트)"""
        w, h = surface.get_size()
        result = surface.copy()

        # 페이드 영역 크기 (외곽에서 안쪽으로)
        fade_size = min(w, h) // 6  # 외곽 1/6 영역 페이드

        # 알파 마스크 생성
        mask = pygame.Surface((w, h), pygame.SRCALPHA)
        mask.fill((255, 255, 255, 255))

        # 각 픽셀의 알파값 조절 (외곽으로 갈수록 투명)
        for x in range(w):
            for y in range(h):
                # 각 변까지의 거리
                dist_left = x
                dist_right = w - 1 - x
                dist_top = y
                dist_bottom = h - 1 - y

                # 가장 가까운 변까지의 거리
                min_dist = min(dist_left, dist_right, dist_top, dist_bottom)

                if min_dist < fade_size:
                    # 외곽 영역: 거리에 따라 알파값 감소
                    alpha = int(255 * (min_dist / fade_size))
                    # 부드러운 곡선 적용 (ease-in)
                    alpha = int(255 * ((min_dist / fade_size) ** 1.5))
                    mask.set_at((x, y), (255, 255, 255, alpha))

        # 마스크 적용
        result.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        return result

    def update(self, dt: float):
        """전환 효과 업데이트"""
        self.age += dt

        # 페이즈 결정
        if self.age < self.darken_duration:
            if self.phase != self.PHASE_DARKEN:
                self.phase = self.PHASE_DARKEN
        elif self.age < self.darken_duration + self.image_duration:
            if self.phase == self.PHASE_DARKEN:
                self.phase = self.PHASE_SHOW_IMAGE
                if self.on_darken_complete:
                    self.on_darken_complete()
        elif self.age < self.total_duration:
            if self.phase != self.PHASE_BRIGHTEN:
                self.phase = self.PHASE_BRIGHTEN
        else:
            self.phase = self.PHASE_DONE
            self.is_alive = False

    def draw(self, screen: pygame.Surface):
        """전환 효과 그리기"""
        if not self.is_alive:
            return

        # 어두운 오버레이
        overlay = pygame.Surface(self.screen_size, pygame.SRCALPHA)

        if self.phase == self.PHASE_DARKEN:
            # 점점 어두워짐 (0 → 180) - easing 적용
            progress = self.age / self.darken_duration
            eased_progress = progress ** 0.7  # ease-out
            alpha = int(180 * eased_progress)
        elif self.phase == self.PHASE_SHOW_IMAGE:
            alpha = 180
        elif self.phase == self.PHASE_BRIGHTEN:
            # 점점 밝아짐 (180 → 0) - easing 적용
            brighten_age = self.age - self.darken_duration - self.image_duration
            progress = brighten_age / self.brighten_duration
            eased_progress = 1 - ((1 - progress) ** 0.7)  # ease-in
            alpha = int(180 * (1 - eased_progress))
        else:
            alpha = 0

        alpha = max(0, min(255, alpha))
        overlay.fill((0, 0, 0, alpha))
        screen.blit(overlay, (0, 0))

        # 이미지 표시 - 어두워지는 동안 서서히 등장 (페이드인 + 스케일)
        if self.image:
            img_alpha = 0
            scale_factor = 1.0

            if self.phase == self.PHASE_DARKEN:
                # 어두워지면서 동시에 이미지가 천천히 등장
                progress = self.age / self.darken_duration
                eased_progress = progress ** 0.5  # 더 천천히 시작
                img_alpha = int(255 * eased_progress)
                # 스케일: 0.6 → 1.0 (더 크게 시작)
                scale_factor = 0.6 + 0.4 * eased_progress

            elif self.phase == self.PHASE_SHOW_IMAGE:
                img_alpha = 255
                scale_factor = 1.0

            elif self.phase == self.PHASE_BRIGHTEN:
                # 밝아지면서 이미지 천천히 사라짐
                brighten_age = self.age - self.darken_duration - self.image_duration
                progress = brighten_age / self.brighten_duration
                eased_progress = progress ** 2  # 천천히 사라짐
                img_alpha = int(255 * (1 - eased_progress))
                scale_factor = 1.0

            if img_alpha > 0:
                img_alpha = max(0, min(255, img_alpha))

                # 스케일 적용
                if scale_factor != 1.0:
                    orig_w, orig_h = self.image.get_size()
                    new_w = int(orig_w * scale_factor)
                    new_h = int(orig_h * scale_factor)
                    if new_w > 0 and new_h > 0:
                        scaled_img = pygame.transform.smoothscale(self.image, (new_w, new_h))
                    else:
                        scaled_img = self.image
                else:
                    scaled_img = self.image

                # 이미지 중앙 배치
                img_rect = scaled_img.get_rect(center=(self.screen_size[0] // 2, self.screen_size[1] // 2))
                img_copy = scaled_img.copy()
                img_copy.set_alpha(img_alpha)
                screen.blit(img_copy, img_rect)


class PlayerVictoryAnimation:
    """플레이어 승리 애니메이션 - 화면 외곽을 시계방향으로 회전 후 하단 중앙으로 이동"""

    PHASE_ORBIT = 0       # 화면 외곽 시계방향 회전
    PHASE_MOVE_DOWN = 1   # 하단 중앙으로 이동
    PHASE_DONE = 2        # 완료

    def __init__(self, player, screen_size: Tuple[int, int], orbit_duration: float = 2.5, move_duration: float = 1.5):
        self.player = player
        self.screen_size = screen_size
        self.orbit_duration = orbit_duration  # 회전 시간: 2.5초 (아주 천천히)
        self.move_duration = move_duration    # 이동 시간: 1.5초

        self.age = 0.0
        self.is_alive = True
        self.phase = self.PHASE_ORBIT
        self.on_complete = None  # 완료 시 콜백

        # 시작 위치 저장
        self.start_pos = pygame.math.Vector2(player.pos.x, player.pos.y)

        # 화면 중심
        self.center = pygame.math.Vector2(screen_size[0] // 2, screen_size[1] // 2)

        # 타원 궤도 반경 (화면 외곽)
        self.orbit_radius_x = screen_size[0] * 0.45
        self.orbit_radius_y = screen_size[1] * 0.45

        # 시작 각도 계산 (현재 위치에서 중심까지의 각도)
        diff = self.start_pos - self.center
        self.start_angle = math.atan2(diff.y, diff.x)

        # 목표 위치 (쿨타임 UI 상부, 화면 하단 중앙)
        self.target_pos = pygame.math.Vector2(screen_size[0] // 2, screen_size[1] - 150)

        # 회전 완료 시 위치 (회전 종료 지점)
        self.orbit_end_pos = None

    def update(self, dt: float):
        """애니메이션 업데이트"""
        if not self.is_alive or not self.player:
            return

        self.age += dt

        if self.phase == self.PHASE_ORBIT:
            # 화면 외곽 시계방향 회전 (빠르게)
            if self.age < self.orbit_duration:
                progress = self.age / self.orbit_duration
                # easing: ease-in-out
                eased = progress * progress * (3 - 2 * progress)

                # 시계방향 회전 (2π = 한 바퀴)
                current_angle = self.start_angle + (2 * math.pi * eased)

                # 타원 궤도 위치 계산
                new_x = self.center.x + math.cos(current_angle) * self.orbit_radius_x
                new_y = self.center.y + math.sin(current_angle) * self.orbit_radius_y

                self.player.pos.x = new_x
                self.player.pos.y = new_y
            else:
                # 회전 완료 → 이동 페이즈로 전환
                self.orbit_end_pos = pygame.math.Vector2(self.player.pos.x, self.player.pos.y)
                self.phase = self.PHASE_MOVE_DOWN
                self.age = 0.0  # 시간 리셋

        elif self.phase == self.PHASE_MOVE_DOWN:
            # 하단 중앙으로 서서히 이동
            if self.age < self.move_duration:
                progress = self.age / self.move_duration
                # easing: ease-out
                eased = 1 - ((1 - progress) ** 2)

                # 선형 보간
                self.player.pos.x = self.orbit_end_pos.x + (self.target_pos.x - self.orbit_end_pos.x) * eased
                self.player.pos.y = self.orbit_end_pos.y + (self.target_pos.y - self.orbit_end_pos.y) * eased
            else:
                # 완료
                self.player.pos.x = self.target_pos.x
                self.player.pos.y = self.target_pos.y
                self.phase = self.PHASE_DONE
                self.is_alive = False

                if self.on_complete:
                    self.on_complete()

        # 플레이어 rect 업데이트
        if self.player.image_rect:
            self.player.image_rect.center = (int(self.player.pos.x), int(self.player.pos.y))
        if self.player.hitbox:
            self.player.hitbox.center = (int(self.player.pos.x), int(self.player.pos.y))


class ScreenShake:
    """화면 떨림 효과 관리 클래스"""

    def __init__(self):
        self.intensity = 0.0  # 현재 떨림 강도 (픽셀)
        self.duration = 0     # 남은 지속 시간 (프레임)
        self.offset = pygame.math.Vector2(0, 0)  # 현재 적용할 오프셋

    def start_shake(self, intensity: float, duration_frames: int):
        """떨림 시작 (강도: 픽셀 단위, 지속 시간: 프레임 단위)"""
        # 기존 떨림보다 강하면 덮어쓰기
        if intensity > self.intensity:
            self.intensity = intensity
            self.duration = duration_frames

    def update(self):
        """매 프레임 호출: 떨림 상태 업데이트"""
        if self.duration > 0:
            # 강도 내에서 무작위 오프셋 계산
            self.offset.x = self.intensity * (2 * random.random() - 1)
            self.offset.y = self.intensity * (2 * random.random() - 1)

            # 매 프레임마다 강도와 지속 시간 감소
            self.intensity *= 0.9
            self.duration -= 1

            if self.duration <= 0:
                self.offset = pygame.math.Vector2(0, 0)
                self.intensity = 0
        else:
            self.offset = pygame.math.Vector2(0, 0)

        return self.offset


class DynamicTextEffect:
    """진동, 색상 변화, 페이드 아웃 기능을 가진 동적 텍스트"""

    def __init__(self, text: str, size: int, color: Tuple[int, int, int],
                 pos: Tuple[float, float], duration_frames: int, shake_intensity: int = 3):
        self.text = text
        self.pos = pygame.math.Vector2(pos)
        self.base_color = color
        self.shake_intensity = shake_intensity
        self.duration = duration_frames
        self.frames_passed = 0
        self.is_alive = True

        # 폰트 로드
        self.font = pygame.font.Font(None, size)

    def update(self, dt: float = None):
        """텍스트 업데이트"""
        if not self.is_alive:
            return
        self.frames_passed += 1
        if self.frames_passed >= self.duration:
            self.is_alive = False

    def draw(self, screen: pygame.Surface, screen_offset: pygame.math.Vector2 = None):
        """화면에 그리기"""
        if not self.is_alive:
            return

        if screen_offset is None:
            screen_offset = pygame.math.Vector2(0, 0)

        # 진동 효과
        offset_x = random.randint(-self.shake_intensity, self.shake_intensity)
        offset_y = random.randint(-self.shake_intensity, self.shake_intensity)

        draw_x = self.pos.x + offset_x + screen_offset.x
        draw_y = self.pos.y + offset_y + screen_offset.y

        # 색상 변화 (마지막에 강조)
        current_color = self.base_color
        if self.duration - self.frames_passed < 15:
            if self.frames_passed % 6 < 3:
                current_color = (255, 255, 0)  # 노란색

        # 투명도 (Fade Out)
        alpha = 255
        if self.frames_passed > self.duration * 0.6:
            fade_progress = (self.frames_passed - self.duration * 0.6) / (self.duration * 0.4)
            alpha = 255 - int(255 * fade_progress)
            alpha = max(0, alpha)

        # 텍스트 렌더링
        text_surface = self.font.render(self.text, True, current_color)
        text_surface.set_alpha(alpha)

        screen.blit(text_surface, (int(draw_x), int(draw_y)))


class ReviveTextEffect:
    """부활 텍스트 이펙트 - 화면 중앙에 부활 메시지 표시 (페이드 인/아웃)"""

    def __init__(self, text: str, screen_size: Tuple[int, int],
                 color: Tuple[int, int, int] = (255, 215, 0), duration: float = 2.0):
        self.text = text
        self.screen_size = screen_size
        self.color = color
        self.duration = duration
        self.age = 0.0
        self.is_alive = True

        # 폰트 설정 (큰 글씨)
        self.font = pygame.font.Font(None, 72)

    def update(self, dt: float):
        """업데이트"""
        self.age += dt
        if self.age >= self.duration:
            self.is_alive = False

    def draw(self, screen: pygame.Surface, screen_offset: pygame.math.Vector2 = None):
        """화면에 그리기"""
        if not self.is_alive:
            return

        progress = self.age / self.duration

        # 알파값: 처음 0.3초 페이드인, 마지막 0.5초 페이드아웃
        if progress < 0.15:  # 페이드 인
            alpha = int(255 * (progress / 0.15))
        elif progress > 0.75:  # 페이드 아웃
            alpha = int(255 * (1 - (progress - 0.75) / 0.25))
        else:
            alpha = 255
        alpha = max(0, min(255, alpha))

        # 텍스트 렌더링
        text_surface = self.font.render(self.text, True, self.color)
        text_surface.set_alpha(alpha)

        # 화면 중앙에 배치
        text_rect = text_surface.get_rect(center=(self.screen_size[0] // 2, self.screen_size[1] // 2 - 50))
        screen.blit(text_surface, text_rect)


class TimeSlowEffect:
    """타임 슬로우 효과 - 게임 속도를 일시적으로 감소"""

    def __init__(self, slow_factor: float, duration: float):
        """
        slow_factor: 속도 감소 배율 (0.5 = 50% 속도)
        duration: 지속 시간 (초)
        """
        self.slow_factor = slow_factor
        self.duration = duration
        self.age = 0.0
        self.is_active = True

    def update(self, dt: float):
        """효과 업데이트"""
        self.age += dt
        if self.age >= self.duration:
            self.is_active = False

    def get_time_scale(self) -> float:
        """현재 시간 스케일 반환"""
        if not self.is_active:
            return 1.0

        # 시작과 끝에 부드러운 전환
        progress = self.age / self.duration

        if progress < 0.1:  # 처음 10%는 감속
            t = progress / 0.1
            return 1.0 + (self.slow_factor - 1.0) * t
        elif progress > 0.8:  # 마지막 20%는 가속
            t = (progress - 0.8) / 0.2
            return self.slow_factor + (1.0 - self.slow_factor) * t
        else:
            return self.slow_factor


class ParallaxLayer:
    """배경 패럴랙스 레이어 - 별 배경 (반짝임 효과 포함)"""

    def __init__(self, screen_size: Tuple[int, int], star_count: int,
                 speed_factor: float, star_size: int, color: Tuple[int, int, int], twinkle: bool = False):
        self.screen_width, self.screen_height = screen_size
        self.speed_factor = speed_factor
        self.base_speed_factor = speed_factor  # 기본 속도 저장
        self.star_size = star_size
        self.color = color
        self.twinkle_enabled = twinkle
        self.stars = []

        # 별 생성 (위치 + 반짝임 정보)
        for _ in range(star_count):
            x = random.randint(0, self.screen_width)
            y = random.randint(0, self.screen_height)
            self.stars.append({
                'pos': pygame.math.Vector2(x, y),
                'brightness': 1.0,  # 현재 밝기 (0.0 ~ 1.5)
                'twinkle_timer': 0.0,  # 반짝임 타이머
                'twinkle_duration': 0.0,  # 반짝임 지속 시간
                'is_twinkling': False,  # 반짝이고 있는지
            })

    def update(self, dt: float, player_velocity: pygame.math.Vector2 = None, speed_multiplier: float = 1.0):
        """레이어 업데이트 - 플레이어 속도에 반응 + 반짝임"""
        # 속도 배율 적용
        current_speed_factor = self.base_speed_factor * speed_multiplier

        if player_velocity is None:
            # 기본 스크롤
            scroll_speed = 50 * current_speed_factor * dt
            for star_data in self.stars:
                star_data['pos'].y += scroll_speed
        else:
            # 플레이어 움직임에 반응
            for star_data in self.stars:
                star_data['pos'].x -= player_velocity.x * current_speed_factor * dt
                star_data['pos'].y -= player_velocity.y * current_speed_factor * dt

        # 화면 밖으로 나간 별 재배치
        for star_data in self.stars:
            star = star_data['pos']
            if star.y > self.screen_height:
                star.y = 0
                star.x = random.randint(0, self.screen_width)
            elif star.y < 0:
                star.y = self.screen_height
                star.x = random.randint(0, self.screen_width)

            if star.x > self.screen_width:
                star.x = 0
                star.y = random.randint(0, self.screen_height)
            elif star.x < 0:
                star.x = self.screen_width
                star.y = random.randint(0, self.screen_height)

        # 반짝임 효과 업데이트
        if self.twinkle_enabled and config.STAR_TWINKLE_SETTINGS["enabled"]:
            for star_data in self.stars:
                if star_data['is_twinkling']:
                    # 반짝임 진행
                    star_data['twinkle_timer'] += dt
                    progress = star_data['twinkle_timer'] / star_data['twinkle_duration']

                    if progress >= 1.0:
                        # 반짝임 종료
                        star_data['is_twinkling'] = False
                        star_data['brightness'] = 1.0
                    else:
                        # 사인파로 밝기 변화
                        import math
                        brightness_range = config.STAR_TWINKLE_SETTINGS["brightness_range"]
                        star_data['brightness'] = 1.0 + (brightness_range[1] - 1.0) * math.sin(progress * math.pi * 2)
                else:
                    # 반짝임 시작 확률
                    if random.random() < config.STAR_TWINKLE_SETTINGS["twinkle_chance"]:
                        star_data['is_twinkling'] = True
                        star_data['twinkle_timer'] = 0.0
                        duration_range = config.STAR_TWINKLE_SETTINGS["twinkle_duration"]
                        star_data['twinkle_duration'] = random.uniform(duration_range[0], duration_range[1])

    def draw(self, screen: pygame.Surface):
        """레이어 그리기 (반짝임 효과 적용)"""
        for star_data in self.stars:
            star = star_data['pos']
            brightness = star_data['brightness']

            # 밝기에 따라 색상 조정
            adjusted_color = tuple(min(255, int(c * brightness)) for c in self.color)

            pygame.draw.circle(screen, adjusted_color,
                             (int(star.x), int(star.y)), self.star_size)


class SpawnEffect:
    """적 스폰 포털 효과"""

    def __init__(self, pos: Tuple[float, float], duration: float, max_size: int):
        self.pos = pygame.math.Vector2(pos)
        self.duration = duration
        self.max_size = max_size
        self.age = 0.0
        self.is_alive = True

    def update(self, dt: float):
        """효과 업데이트"""
        self.age += dt
        if self.age >= self.duration:
            self.is_alive = False

    def draw(self, screen: pygame.Surface):
        """포털 그리기"""
        if not self.is_alive:
            return

        progress = self.age / self.duration

        # 크기 애니메이션 (0 → max → 0)
        if progress < 0.5:
            size_factor = progress * 2
        else:
            size_factor = 2 - progress * 2

        current_size = int(self.max_size * size_factor)

        # 회전 각도
        rotation = self.age * 360 * 2  # 2회전/초

        # 알파값
        alpha = int(200 * (1 - progress))

        # 여러 겹의 원 그리기
        for i in range(3):
            radius = current_size - i * 10
            if radius > 0:
                color = (100 + i * 50, 50 + i * 30, 255, alpha)
                surf = pygame.Surface((radius * 2 + 5, radius * 2 + 5), pygame.SRCALPHA)
                pygame.draw.circle(surf, color, (radius + 2, radius + 2), radius, 2)
                screen.blit(surf, (int(self.pos.x - radius - 2), int(self.pos.y - radius - 2)))


class Meteor:
    """유성 효과 - 화면을 대각선으로 가로지르는 작은 유성 (웨이브당 1개)"""

    # 클래스 변수로 이미지 로드 (한 번만 로드)
    _head_image = None
    _trail_image = None

    def __init__(self, screen_size: Tuple[int, int]):
        self.screen_width, self.screen_height = screen_size
        self.is_alive = True

        # 이미지 로드 (처음 한 번만, use_image가 True일 때만)
        if Meteor._head_image is None and config.METEOR_SETTINGS.get("use_image", False):
            try:
                # config에서 정의된 경로 사용
                if config.METEOR_HEAD_IMAGE_PATH.exists() and config.METEOR_TRAIL_IMAGE_PATH.exists():
                    # display가 초기화된 경우에만 convert_alpha 사용
                    if pygame.display.get_surface():
                        head_img = pygame.image.load(str(config.METEOR_HEAD_IMAGE_PATH)).convert_alpha()
                        trail_img = pygame.image.load(str(config.METEOR_TRAIL_IMAGE_PATH)).convert_alpha()
                    else:
                        head_img = pygame.image.load(str(config.METEOR_HEAD_IMAGE_PATH))
                        trail_img = pygame.image.load(str(config.METEOR_TRAIL_IMAGE_PATH))

                    # 크기 조정 (설정에 맞춰)
                    head_scale = config.METEOR_SETTINGS.get("head_scale", 1.5)
                    trail_scale = config.METEOR_SETTINGS.get("trail_scale", 1.2)

                    # 원본 이미지 크기 기반으로 스케일링
                    head_w = int(head_img.get_width() * head_scale)
                    head_h = int(head_img.get_height() * head_scale)
                    trail_w = int(trail_img.get_width() * trail_scale)
                    trail_h = int(trail_img.get_height() * trail_scale)

                    Meteor._head_image = pygame.transform.smoothscale(head_img, (head_w, head_h))
                    Meteor._trail_image = pygame.transform.smoothscale(trail_img, (trail_w, trail_h))
                    print(f"INFO: Meteor images loaded successfully (head: {head_w}x{head_h}, trail: {trail_w}x{trail_h})")
                else:
                    print(f"WARNING: Meteor image files not found at {config.METEOR_HEAD_IMAGE_PATH}")
                    Meteor._head_image = None
                    Meteor._trail_image = None
            except Exception as e:
                print(f"WARNING: Failed to load meteor images: {e}")
                Meteor._head_image = None
                Meteor._trail_image = None

        # 단순화된 설정
        self.speed = random.uniform(*config.METEOR_SETTINGS["speed"])
        self.size = random.randint(*config.METEOR_SETTINGS["size"])
        self.color = config.METEOR_SETTINGS["color"]
        self.trail_length = config.METEOR_SETTINGS["trail_length"]

        # 시작 위치 (화면 상단 랜덤 또는 좌측)
        if random.random() < 0.5:
            # 상단에서 시작
            self.pos = pygame.math.Vector2(random.randint(0, self.screen_width), -20)
            angle = random.uniform(30, 60)  # 아래쪽 각도
        else:
            # 좌측에서 시작
            self.pos = pygame.math.Vector2(-20, random.randint(0, self.screen_height // 2))
            angle = random.uniform(20, 45)  # 우하향 각도

        # 방향 벡터
        import math
        self.angle_degrees = angle
        self.velocity = pygame.math.Vector2(
            math.cos(math.radians(angle)),
            math.sin(math.radians(angle))
        ).normalize() * self.speed

        # 트레일 위치 저장
        self.trail_positions = []

    def update(self, dt: float):
        """유성 업데이트"""
        if not self.is_alive:
            return

        # 현재 위치를 트레일에 추가
        self.trail_positions.append(self.pos.copy())
        if len(self.trail_positions) > self.trail_length:
            self.trail_positions.pop(0)

        # 이동
        self.pos += self.velocity * dt

        # 화면 밖으로 나가면 제거
        if (self.pos.x > self.screen_width + 50 or
            self.pos.y > self.screen_height + 50):
            self.is_alive = False

    def draw(self, screen: pygame.Surface):
        """유성 그리기 (꼬리 트레일 포함)"""
        if not self.is_alive:
            return

        # 이미지가 로드되었고 use_image가 True인 경우에만 이미지 사용
        use_image = config.METEOR_SETTINGS.get("use_image", False)
        if use_image and Meteor._head_image is not None and Meteor._trail_image is not None:
            import math

            # 트레일 그리기 (뒤에서 앞으로, 점점 투명하게)
            if len(self.trail_positions) > 1:
                for i, trail_pos in enumerate(self.trail_positions[:-1]):  # 마지막 위치 제외
                    alpha = int(255 * (i + 1) / len(self.trail_positions))
                    scale = (i + 1) / len(self.trail_positions)

                    # 트레일 이미지 회전 및 크기 조정
                    rotated_trail = pygame.transform.rotate(Meteor._trail_image, -self.angle_degrees)
                    scaled_trail = pygame.transform.scale(
                        rotated_trail,
                        (int(rotated_trail.get_width() * scale),
                         int(rotated_trail.get_height() * scale))
                    )

                    # 알파 적용
                    scaled_trail.set_alpha(alpha)

                    # 트레일 그리기
                    rect = scaled_trail.get_rect(center=(int(trail_pos.x), int(trail_pos.y)))
                    screen.blit(scaled_trail, rect)

            # 혜성 본체 그리기 (회전 적용)
            rotated_head = pygame.transform.rotate(Meteor._head_image, -self.angle_degrees)
            rect = rotated_head.get_rect(center=(int(self.pos.x), int(self.pos.y)))
            screen.blit(rotated_head, rect)

        else:
            # 이미지 로드 실패 시 기본 원 그리기 (폴백)
            # 트레일 그리기 (뒤에서 앞으로, 점점 투명하게)
            for i, trail_pos in enumerate(self.trail_positions):
                alpha = int(255 * (i + 1) / len(self.trail_positions))
                size = max(1, int(self.size * (i + 1) / len(self.trail_positions)))

                # 투명도를 가진 서페이스 생성
                trail_surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
                pygame.draw.circle(trail_surf, (*self.color, alpha), (size, size), size)
                screen.blit(trail_surf, (int(trail_pos.x - size), int(trail_pos.y - size)))

            # 유성 본체 그리기 (밝게)
            head_color = tuple(min(255, c + 50) for c in self.color)
            pygame.draw.circle(screen, head_color, (int(self.pos.x), int(self.pos.y)), self.size)


class NebulaParticle:
    """성운 파티클 - 느리게 흐르는 거대한 색깔 구름"""

    def __init__(self, screen_size: Tuple[int, int]):
        self.screen_width, self.screen_height = screen_size
        self.is_alive = True

        # 랜덤 설정
        settings = config.NEBULA_SETTINGS
        self.pos = pygame.math.Vector2(
            random.randint(-100, self.screen_width + 100),
            random.randint(-100, self.screen_height + 100)
        )
        self.speed = random.uniform(*settings["speed"])
        self.size = random.randint(*settings["size"])
        self.base_alpha = random.randint(*settings["alpha"])
        self.current_alpha = self.base_alpha
        self.color = random.choice(settings["colors"])

        # 펄스 효과
        self.pulse_timer = random.uniform(0, 6.28)  # 0 ~ 2π
        self.pulse_speed = settings["pulse_speed"]

        # 이동 방향 (천천히 아래로)
        import math
        angle = random.uniform(70, 110)  # 대부분 아래 방향
        self.velocity = pygame.math.Vector2(
            math.cos(math.radians(angle)),
            math.sin(math.radians(angle))
        ).normalize() * self.speed

    def update(self, dt: float):
        """성운 파티클 업데이트"""
        if not self.is_alive:
            return

        # 이동
        self.pos += self.velocity * dt

        # 펄스 효과 (밝기 변화)
        import math
        self.pulse_timer += self.pulse_speed * dt
        pulse_factor = 0.7 + 0.3 * math.sin(self.pulse_timer)  # 0.7 ~ 1.0
        self.current_alpha = int(self.base_alpha * pulse_factor)

        # 화면 밖으로 나가면 재배치
        if self.pos.y > self.screen_height + 200:
            self.pos.y = -200
            self.pos.x = random.randint(-100, self.screen_width + 100)
        elif self.pos.y < -200:
            self.pos.y = self.screen_height + 200
            self.pos.x = random.randint(-100, self.screen_width + 100)

        if self.pos.x > self.screen_width + 200:
            self.pos.x = -200
            self.pos.y = random.randint(-100, self.screen_height + 100)
        elif self.pos.x < -200:
            self.pos.x = self.screen_width + 200
            self.pos.y = random.randint(-100, self.screen_height + 100)

    def draw(self, screen: pygame.Surface):
        """성운 파티클 그리기 (그라데이션 효과)"""
        if not self.is_alive:
            return

        # 여러 겹의 원으로 그라데이션 효과
        layers = 5
        for i in range(layers, 0, -1):
            layer_size = int(self.size * i / layers)
            layer_alpha = int(self.current_alpha * i / layers)

            # 투명도를 가진 서페이스 생성
            nebula_surf = pygame.Surface((layer_size * 2, layer_size * 2), pygame.SRCALPHA)
            pygame.draw.circle(nebula_surf, (*self.color, layer_alpha),
                             (layer_size, layer_size), layer_size)
            screen.blit(nebula_surf, (int(self.pos.x - layer_size), int(self.pos.y - layer_size)))


class BackgroundTransition:
    """배경 전환 효과 클래스 - 웨이브 시작 시 배경 이미지 전환"""

    def __init__(self, old_bg: pygame.Surface, new_bg: pygame.Surface,
                 screen_size: Tuple[int, int], effect_type: str, duration: float):
        """
        old_bg: 이전 배경 이미지
        new_bg: 새 배경 이미지
        screen_size: 화면 크기
        effect_type: 전환 효과 종류
        duration: 전환 지속 시간 (초)
        """
        self.old_bg = old_bg
        self.new_bg = new_bg
        self.screen_width, self.screen_height = screen_size
        self.effect_type = effect_type
        self.duration = duration
        self.age = 0.0
        self.is_active = True

        # 전환 효과별 초기화
        if effect_type == "shake_fade":
            self.shake_intensity = 15.0

    def update(self, dt: float):
        """전환 효과 업데이트"""
        if not self.is_active:
            return

        self.age += dt
        if self.age >= self.duration:
            self.is_active = False
            self.age = self.duration

    def get_progress(self) -> float:
        """전환 진행도 (0.0 ~ 1.0)"""
        return min(1.0, self.age / self.duration)

    def draw(self, screen: pygame.Surface):
        """전환 효과 그리기"""
        if not self.is_active and self.age >= self.duration:
            # 전환 완료 - 새 배경만 표시
            screen.blit(self.new_bg, (0, 0))
            return

        progress = self.get_progress()

        # 효과 종류별 전환 렌더링
        if self.effect_type == "fade_in":
            self._draw_fade_in(screen, progress)
        elif self.effect_type == "slide_horizontal":
            self._draw_slide_horizontal(screen, progress)
        elif self.effect_type == "zoom_in":
            self._draw_zoom_in(screen, progress)
        elif self.effect_type == "cross_fade":
            self._draw_cross_fade(screen, progress)
        elif self.effect_type == "flash_zoom":
            self._draw_flash_zoom(screen, progress)
        elif self.effect_type == "vertical_wipe":
            self._draw_vertical_wipe(screen, progress)
        elif self.effect_type == "circular_reveal":
            self._draw_circular_reveal(screen, progress)
        elif self.effect_type == "pixelate":
            self._draw_pixelate(screen, progress)
        elif self.effect_type == "shake_fade":
            self._draw_shake_fade(screen, progress)
        elif self.effect_type == "multi_flash":
            self._draw_multi_flash(screen, progress)
        else:
            # 기본: 즉시 전환
            screen.blit(self.new_bg, (0, 0))

    # ========== 전환 효과 렌더링 메서드들 ==========

    def _draw_fade_in(self, screen: pygame.Surface, progress: float):
        """페이드 인 효과"""
        screen.blit(self.old_bg, (0, 0))

        # 새 배경을 투명도와 함께 그리기
        new_surf = self.new_bg.copy()
        alpha = int(255 * progress)
        new_surf.set_alpha(alpha)
        screen.blit(new_surf, (0, 0))

    def _draw_slide_horizontal(self, screen: pygame.Surface, progress: float):
        """좌→우 슬라이드 효과"""
        offset_x = int(self.screen_width * (1 - progress))

        # 이전 배경 (왼쪽으로 이동)
        screen.blit(self.old_bg, (-int(self.screen_width * progress), 0))

        # 새 배경 (오른쪽에서 들어옴)
        screen.blit(self.new_bg, (offset_x, 0))

    def _draw_zoom_in(self, screen: pygame.Surface, progress: float):
        """중심에서 확대 효과"""
        screen.blit(self.old_bg, (0, 0))

        # 이징 함수 적용 (가속)
        eased_progress = progress * progress

        # 새 배경 스케일링 (0.5 → 1.0)
        scale = 0.5 + 0.5 * eased_progress
        new_width = int(self.screen_width * scale)
        new_height = int(self.screen_height * scale)

        scaled_bg = pygame.transform.scale(self.new_bg, (new_width, new_height))

        # 중앙 배치
        x = (self.screen_width - new_width) // 2
        y = (self.screen_height - new_height) // 2

        alpha = int(255 * progress)
        scaled_bg.set_alpha(alpha)
        screen.blit(scaled_bg, (x, y))

    def _draw_cross_fade(self, screen: pygame.Surface, progress: float):
        """교차 페이드 효과"""
        # 이전 배경 페이드 아웃
        old_surf = self.old_bg.copy()
        old_alpha = int(255 * (1 - progress))
        old_surf.set_alpha(old_alpha)

        # 새 배경 페이드 인
        new_surf = self.new_bg.copy()
        new_alpha = int(255 * progress)
        new_surf.set_alpha(new_alpha)

        screen.fill((0, 0, 0))  # 검은 배경
        screen.blit(old_surf, (0, 0))
        screen.blit(new_surf, (0, 0))

    def _draw_flash_zoom(self, screen: pygame.Surface, progress: float):
        """번쩍임 + 확대 효과 (보스 전용)"""
        # 전반부 (0 ~ 0.2): 화이트 플래시
        if progress < 0.2:
            flash_alpha = int(255 * (1 - progress / 0.2))
            screen.blit(self.old_bg, (0, 0))
            flash_surf = pygame.Surface((self.screen_width, self.screen_height))
            flash_surf.fill((255, 255, 255))
            flash_surf.set_alpha(flash_alpha)
            screen.blit(flash_surf, (0, 0))
        # 후반부 (0.2 ~ 1.0): 줌 인
        else:
            adj_progress = (progress - 0.2) / 0.8
            scale = 0.3 + 0.7 * adj_progress

            new_width = int(self.screen_width * scale)
            new_height = int(self.screen_height * scale)
            scaled_bg = pygame.transform.scale(self.new_bg, (new_width, new_height))

            x = (self.screen_width - new_width) // 2
            y = (self.screen_height - new_height) // 2

            screen.fill((0, 0, 0))
            screen.blit(scaled_bg, (x, y))

    def _draw_vertical_wipe(self, screen: pygame.Surface, progress: float):
        """위→아래 닦아내기 효과"""
        wipe_y = int(self.screen_height * progress)

        # 이전 배경 (아래 부분)
        screen.blit(self.old_bg, (0, 0))

        # 새 배경 (위에서부터 점진적으로)
        if wipe_y > 0:
            new_surf = pygame.Surface((self.screen_width, wipe_y))
            new_surf.blit(self.new_bg, (0, 0))
            screen.blit(new_surf, (0, 0))

    def _draw_circular_reveal(self, screen: pygame.Surface, progress: float):
        """원형 확장 효과"""
        screen.blit(self.old_bg, (0, 0))

        # 원의 최대 반지름 (화면 대각선)
        max_radius = int(math.sqrt(self.screen_width**2 + self.screen_height**2) / 2)
        current_radius = int(max_radius * progress)

        # 마스크 생성
        mask = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        mask.fill((0, 0, 0, 0))

        center = (self.screen_width // 2, self.screen_height // 2)
        pygame.draw.circle(mask, (255, 255, 255, 255), center, current_radius)

        # 새 배경에 마스크 적용
        new_surf = self.new_bg.copy()
        new_surf.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        screen.blit(new_surf, (0, 0))

    def _draw_pixelate(self, screen: pygame.Surface, progress: float):
        """픽셀 분해→재조립 효과"""
        # 전반부: 이전 배경 픽셀화
        if progress < 0.5:
            pixel_progress = progress * 2
            pixel_size = int(1 + 20 * pixel_progress)

            # 다운스케일
            small_width = max(1, self.screen_width // pixel_size)
            small_height = max(1, self.screen_height // pixel_size)
            small_surf = pygame.transform.scale(self.old_bg, (small_width, small_height))

            # 업스케일 (픽셀화 효과)
            pixelated = pygame.transform.scale(small_surf, (self.screen_width, self.screen_height))
            screen.blit(pixelated, (0, 0))
        # 후반부: 새 배경 역픽셀화
        else:
            pixel_progress = (progress - 0.5) * 2
            pixel_size = int(20 - 19 * pixel_progress)
            pixel_size = max(1, pixel_size)

            small_width = max(1, self.screen_width // pixel_size)
            small_height = max(1, self.screen_height // pixel_size)
            small_surf = pygame.transform.scale(self.new_bg, (small_width, small_height))

            pixelated = pygame.transform.scale(small_surf, (self.screen_width, self.screen_height))
            screen.blit(pixelated, (0, 0))

    def _draw_shake_fade(self, screen: pygame.Surface, progress: float):
        """흔들림 + 페이드 효과"""
        # 흔들림 계산
        shake_x = int(self.shake_intensity * (1 - progress) * (2 * random.random() - 1))
        shake_y = int(self.shake_intensity * (1 - progress) * (2 * random.random() - 1))

        # 크로스 페이드
        old_surf = self.old_bg.copy()
        old_alpha = int(255 * (1 - progress))
        old_surf.set_alpha(old_alpha)

        new_surf = self.new_bg.copy()
        new_alpha = int(255 * progress)
        new_surf.set_alpha(new_alpha)

        screen.fill((0, 0, 0))
        screen.blit(old_surf, (shake_x, shake_y))
        screen.blit(new_surf, (0, 0))

    def _draw_multi_flash(self, screen: pygame.Surface, progress: float):
        """다중 번쩍임 효과 (최종 보스)"""
        # 3회 플래시 (0-0.3, 0.35-0.5, 0.55-0.7)
        flash_times = [(0.0, 0.3), (0.35, 0.5), (0.55, 0.7)]

        is_flashing = False
        flash_intensity = 0

        for start, end in flash_times:
            if start <= progress < end:
                is_flashing = True
                flash_progress = (progress - start) / (end - start)
                # 삼각파: 0 → 1 → 0
                if flash_progress < 0.5:
                    flash_intensity = int(255 * (flash_progress * 2))
                else:
                    flash_intensity = int(255 * (2 - flash_progress * 2))
                break

        if is_flashing:
            screen.blit(self.old_bg, (0, 0))
            flash_surf = pygame.Surface((self.screen_width, self.screen_height))
            flash_surf.fill((255, 255, 255))
            flash_surf.set_alpha(flash_intensity)
            screen.blit(flash_surf, (0, 0))
        elif progress >= 0.7:
            # 플래시 이후 페이드
            fade_progress = (progress - 0.7) / 0.3

            old_surf = self.old_bg.copy()
            old_surf.set_alpha(int(255 * (1 - fade_progress)))

            new_surf = self.new_bg.copy()
            new_surf.set_alpha(int(255 * fade_progress))

            screen.fill((0, 0, 0))
            screen.blit(old_surf, (0, 0))
            screen.blit(new_surf, (0, 0))
        else:
            screen.blit(self.old_bg, (0, 0))


# =========================================================
# StaticField (정전기장) - 속성 스킬
# =========================================================

class StaticField:
    """적 사망 시 생성되는 정전기장 (Static Field 스킬)"""

    # 클래스 변수: 이미지 로드 (한 번만)
    _image_loaded = False
    _original_image = None

    def __init__(self, pos: Tuple[float, float], radius: float, duration: float, damage_per_sec: float):
        self.pos = pygame.math.Vector2(pos)
        self.radius = radius
        self.duration = duration
        self.damage_per_sec = damage_per_sec
        self.age = 0.0
        self.is_active = True

        # 이미지 로드 (첫 인스턴스에서만)
        if not StaticField._image_loaded:
            self._load_image()

        # 이미지를 반경에 맞게 스케일링
        if StaticField._original_image is not None:
            size = int(self.radius * 2)
            self.image = pygame.transform.scale(StaticField._original_image, (size, size))
        else:
            self.image = None

    @classmethod
    def _load_image(cls):
        """Static Field 이미지 로드"""
        import config
        try:
            if config.STATIC_FIELD_IMAGE_PATH.exists():
                cls._original_image = pygame.image.load(str(config.STATIC_FIELD_IMAGE_PATH)).convert_alpha()
                print(f"INFO: Static Field image loaded from {config.STATIC_FIELD_IMAGE_PATH}")
            else:
                print(f"WARNING: Static Field image not found at {config.STATIC_FIELD_IMAGE_PATH}")
                cls._original_image = None
        except Exception as e:
            print(f"ERROR: Failed to load Static Field image: {e}")
            cls._original_image = None
        finally:
            cls._image_loaded = True

    def update(self, dt: float):
        """정전기장 업데이트"""
        self.age += dt
        if self.age >= self.duration:
            self.is_active = False

    def apply_damage(self, enemies: List, dt: float):
        """범위 내 적들에게 지속 데미지"""
        for enemy in enemies:
            if enemy.is_alive:
                distance = (enemy.pos - self.pos).length()
                if distance <= self.radius:
                    enemy.take_damage(self.damage_per_sec * dt)

    def draw(self, screen: pygame.Surface):
        """정전기장 그리기"""
        if self.is_active:
            # 시간에 따라 투명도 감소 (100% → 0%)
            alpha_ratio = 1 - (self.age / self.duration)
            alpha = int(255 * alpha_ratio)

            if self.image is not None:
                # 이미지를 사용하여 그리기
                temp_image = self.image.copy()
                temp_image.set_alpha(alpha)
                rect = temp_image.get_rect(center=(int(self.pos.x), int(self.pos.y)))
                screen.blit(temp_image, rect)
            else:
                # 이미지가 없으면 기본 원형으로 그리기 (폴백)
                circle_surf = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(circle_surf, (150, 150, 255, alpha), (self.radius, self.radius), self.radius)
                pygame.draw.circle(circle_surf, (100, 200, 255, min(255, alpha + 50)), (self.radius, self.radius), self.radius, 2)
                rect = circle_surf.get_rect(center=(int(self.pos.x), int(self.pos.y)))
                screen.blit(circle_surf, rect)


# =========================================================
# 11. 동료 유닛 클래스 (Companion System)
# =========================================================

class Turret:
    """고정 설치형 자동 포탑"""

    # 클래스 레벨 이미지 캐시
    _image_cache = None

    def __init__(self, pos: Tuple[float, float]):
        import config

        self.pos = pygame.math.Vector2(pos)
        self.shoot_range = config.TURRET_SETTINGS["shoot_range"]
        self.shoot_cooldown = config.TURRET_SETTINGS["shoot_cooldown"]
        self.damage = config.TURRET_SETTINGS["damage"]
        self.bullet_speed = config.TURRET_SETTINGS["bullet_speed"]
        self.duration = config.TURRET_SETTINGS["duration"]
        self.size = config.TURRET_SETTINGS["size"]

        self.shoot_timer = 0.0
        self.age = 0.0
        self.is_alive = True

        # 회전 각도 (발사 방향 표시용)
        self.rotation_angle = 0.0

        # 이미지 로드 (클래스 캐시 사용)
        self._load_image()

    def _load_image(self):
        """터렛 이미지 로드"""
        from pathlib import Path

        # 클래스 캐시에서 이미지 가져오기
        if Turret._image_cache is not None:
            self.image = Turret._image_cache
            return

        # 이미지 로드 시도
        image_path = Path("assets/images/ui/turret.png")
        if image_path.exists():
            try:
                original_image = pygame.image.load(str(image_path)).convert_alpha()
                # 터렛 크기에 맞게 스케일링 (size * 2 정도)
                target_size = self.size * 2
                self.image = pygame.transform.scale(original_image, (target_size, target_size))
                Turret._image_cache = self.image
                print(f"INFO: Turret image loaded from {image_path}")
            except Exception as e:
                print(f"WARNING: Failed to load turret image: {e}")
                self.image = None
        else:
            print(f"INFO: Turret image not found at {image_path}, using default shape")
            self.image = None

    def update(self, dt: float, enemies: List, bullets: List):
        """터렛 업데이트"""
        if not self.is_alive:
            return

        # 지속시간 감소
        self.age += dt
        if self.age >= self.duration:
            self.is_alive = False
            return

        # 쿨다운 감소
        self.shoot_timer -= dt

        # 범위 내 가장 가까운 적 찾기
        if self.shoot_timer <= 0:
            closest_enemy = None
            closest_distance = float('inf')

            for enemy in enemies:
                if enemy.is_alive:
                    distance = (enemy.pos - self.pos).length()
                    if distance <= self.shoot_range and distance < closest_distance:
                        closest_enemy = enemy
                        closest_distance = distance

            # 적 발견 시 발사
            if closest_enemy:
                direction = (closest_enemy.pos - self.pos).normalize()

                # 총알 생성 (Bullet 클래스 사용)
                bullet = Bullet(self.pos.copy(), direction, self.damage, piercing=False)
                bullet.speed = self.bullet_speed
                bullets.append(bullet)

                # 회전 각도 업데이트 (시각 효과용)
                import math
                self.rotation_angle = math.atan2(direction.y, direction.x)

                self.shoot_timer = self.shoot_cooldown

    def draw(self, screen: pygame.Surface):
        """터렛 그리기"""
        if not self.is_alive:
            return

        import math

        # 이미지가 있으면 이미지 사용, 없으면 기본 도형 사용
        if self.image is not None:
            # 이미지 회전 (발사 방향에 맞춤)
            angle_degrees = -math.degrees(self.rotation_angle)
            rotated_image = pygame.transform.rotate(self.image, angle_degrees)
            image_rect = rotated_image.get_rect(center=(int(self.pos.x), int(self.pos.y)))
            screen.blit(rotated_image, image_rect)
        else:
            # 기본 도형 (이미지 없을 때)
            base_color = (100, 100, 255)
            pygame.draw.circle(screen, base_color, (int(self.pos.x), int(self.pos.y)), self.size)

            # 포신 (회전하는 선)
            barrel_length = self.size + 10
            barrel_end_x = self.pos.x + math.cos(self.rotation_angle) * barrel_length
            barrel_end_y = self.pos.y + math.sin(self.rotation_angle) * barrel_length
            pygame.draw.line(screen, (200, 200, 255),
                            (int(self.pos.x), int(self.pos.y)),
                            (int(barrel_end_x), int(barrel_end_y)), 4)

        # 사거리 표시 (반투명 원)
        range_surf = pygame.Surface((self.shoot_range * 2, self.shoot_range * 2), pygame.SRCALPHA)
        pygame.draw.circle(range_surf, (100, 100, 255, 30),
                          (self.shoot_range, self.shoot_range), self.shoot_range, 1)
        screen.blit(range_surf, (int(self.pos.x - self.shoot_range), int(self.pos.y - self.shoot_range)))

        # 남은 시간 표시
        remaining_time = self.duration - self.age
        font = pygame.font.Font(None, 20)
        time_text = font.render(f"{int(remaining_time)}s", True, (255, 255, 255))
        screen.blit(time_text, (int(self.pos.x - 10), int(self.pos.y + self.size + 5)))


class Drone:
    """플레이어 추적형 공격 드론"""

    def __init__(self, player, orbit_angle: float):
        import config
        from pathlib import Path

        self.player = player  # 플레이어 참조
        self.orbit_radius = config.DRONE_SETTINGS["orbit_radius"]
        self.orbit_speed = config.DRONE_SETTINGS["orbit_speed"]
        self.shoot_range = config.DRONE_SETTINGS["shoot_range"]
        self.shoot_cooldown = config.DRONE_SETTINGS["shoot_cooldown"]
        self.damage = config.DRONE_SETTINGS["damage"]
        self.bullet_speed = config.DRONE_SETTINGS["bullet_speed"]
        self.size = config.DRONE_SETTINGS["size"]

        self.orbit_angle = orbit_angle  # 초기 궤도 각도
        self.shoot_timer = 0.0
        self.is_alive = True

        # 드론 이미지 로드
        drone_image_path = Path("assets/images/units/dron_auto_image.png")
        if drone_image_path.exists():
            self.image = pygame.image.load(str(drone_image_path)).convert_alpha()
            # 드론 크기에 맞게 스케일링
            self.image = pygame.transform.scale(self.image, (int(self.size * 2), int(self.size * 2)))
        else:
            self.image = None

        # 위치 초기화 (원형 궤도)
        import math
        self.pos = pygame.math.Vector2(
            player.pos.x + math.cos(orbit_angle) * self.orbit_radius,
            player.pos.y + math.sin(orbit_angle) * self.orbit_radius
        )
        self.trail_glow_intensity = 0.0  # 글로우 효과 강도
        self.trail_pulse_phase = 0.0  # 펄스 애니메이션 위상

    def update(self, dt: float, enemies: List, bullets: List):
        """드론 업데이트"""
        if not self.is_alive:
            return

        import math

        # 원형 궤도 펄스 애니메이션 업데이트
        self.trail_pulse_phase += dt * 3.0
        self.trail_glow_intensity = 0.5 + 0.5 * math.sin(self.trail_pulse_phase)

        # 궤도 회전
        self.orbit_angle += self.orbit_speed * dt

        # 위치 업데이트 (플레이어 주변 원형 궤도)
        self.pos.x = self.player.pos.x + math.cos(self.orbit_angle) * self.orbit_radius
        self.pos.y = self.player.pos.y + math.sin(self.orbit_angle) * self.orbit_radius

        # 쿨다운 감소
        self.shoot_timer -= dt

        # 범위 내 가장 가까운 적 찾기
        if self.shoot_timer <= 0:
            closest_enemy = None
            closest_distance = float('inf')

            for enemy in enemies:
                if enemy.is_alive:
                    distance = (enemy.pos - self.pos).length()
                    if distance <= self.shoot_range and distance < closest_distance:
                        closest_enemy = enemy
                        closest_distance = distance

            # 적 발견 시 발사
            if closest_enemy:
                direction = (closest_enemy.pos - self.pos).normalize()

                # 총알 생성
                bullet = Bullet(self.pos.copy(), direction, self.damage, piercing=False)
                bullet.speed = self.bullet_speed
                bullets.append(bullet)

                self.shoot_timer = self.shoot_cooldown

    def draw(self, screen: pygame.Surface):
        """드론 그리기"""
        if not self.is_alive:
            return

        import math

        # 타원형 궤도 효과 그리기 (플레이어 주변을 완전히 둘러싸는 형태)
        self._draw_ellipse_orbit(screen)

        if self.image:
            # 이미지가 있으면 이미지 그리기
            image_rect = self.image.get_rect(center=(int(self.pos.x), int(self.pos.y)))
            screen.blit(self.image, image_rect)
        else:
            # 이미지가 없으면 기본 육각형 그리기
            import math
            points = []
            for i in range(6):
                angle = math.pi / 3 * i
                x = self.pos.x + math.cos(angle) * self.size
                y = self.pos.y + math.sin(angle) * self.size
                points.append((int(x), int(y)))

            pygame.draw.polygon(screen, (255, 200, 100), points)
            pygame.draw.polygon(screen, (255, 255, 150), points, 2)

            # 중심점
            pygame.draw.circle(screen, (255, 255, 200), (int(self.pos.x), int(self.pos.y)), 4)

    def _draw_ellipse_orbit(self, screen: pygame.Surface):
        """플레이어 주변을 둘러싸는 원형 궤도 효과 그리기"""
        import math

        # 플레이어 중심 좌표
        center_x = int(self.player.pos.x)
        center_y = int(self.player.pos.y)

        # 원형 크기 (궤도 반지름 기반)
        orbit_diameter = int(self.orbit_radius * 2)

        # 글로우 효과를 위한 여러 겹의 원 그리기
        glow_intensity = self.trail_glow_intensity

        # 외부 글로우 (넓고 투명)
        for i in range(3, 0, -1):
            glow_expand = i * 4
            glow_alpha = int(30 * glow_intensity / i)
            glow_color = (255, 200, 100)

            # 글로우 서피스 생성
            glow_size = orbit_diameter + glow_expand * 2

            if glow_size > 0:
                glow_surf = pygame.Surface((glow_size + 10, glow_size + 10), pygame.SRCALPHA)
                glow_rect = pygame.Rect(5, 5, glow_size, glow_size)
                pygame.draw.ellipse(glow_surf, (*glow_color, glow_alpha), glow_rect, max(1, 4 - i))
                screen.blit(glow_surf, (center_x - glow_size // 2 - 5, center_y - glow_size // 2 - 5))

        # 메인 원형 궤도 (점선 효과로 에너지 흐름 표현)
        num_segments = 36  # 원을 구성하는 세그먼트 수
        trail_color_base = (255, 200, 100)
        trail_color_bright = (255, 255, 180)

        points = []
        for i in range(num_segments + 1):
            angle = (2 * math.pi * i / num_segments)
            x = center_x + math.cos(angle) * self.orbit_radius
            y = center_y + math.sin(angle) * self.orbit_radius
            points.append((x, y))

        # 회전하는 밝은 구간 효과 (드론 위치 기준)
        drone_segment = int((self.orbit_angle / (2 * math.pi)) * num_segments) % num_segments

        for i in range(num_segments):
            # 드론 위치로부터의 거리에 따른 밝기 계산
            segment_dist = min(abs(i - drone_segment), num_segments - abs(i - drone_segment))
            brightness = max(0, 1.0 - segment_dist / (num_segments / 3))

            # 색상 보간
            r = int(trail_color_base[0] + (trail_color_bright[0] - trail_color_base[0]) * brightness)
            g = int(trail_color_base[1] + (trail_color_bright[1] - trail_color_base[1]) * brightness)
            b = int(trail_color_base[2] + (trail_color_bright[2] - trail_color_base[2]) * brightness)

            # 선 굵기 (드론 근처가 더 두꺼움)
            line_width = 1 + int(brightness * 2)

            # 알파값 (드론에서 멀어질수록 투명)
            alpha = int(100 + 155 * brightness * glow_intensity)

            # 세그먼트 그리기
            if i < len(points) - 1:
                start_pos = (int(points[i][0]), int(points[i][1]))
                end_pos = (int(points[i + 1][0]), int(points[i + 1][1]))

                # 투명한 선 그리기
                line_surf = pygame.Surface((abs(end_pos[0] - start_pos[0]) + 10,
                                           abs(end_pos[1] - start_pos[1]) + 10), pygame.SRCALPHA)
                local_start = (5, 5)
                local_end = (end_pos[0] - start_pos[0] + 5, end_pos[1] - start_pos[1] + 5)

                pygame.draw.line(line_surf, (r, g, b, alpha), local_start, local_end, line_width)
                screen.blit(line_surf, (min(start_pos[0], end_pos[0]) - 5,
                                       min(start_pos[1], end_pos[1]) - 5))

        # 드론 현재 위치에 밝은 마커 (에너지 노드)
        marker_size = 4 + int(glow_intensity * 2)
        pygame.draw.circle(screen, trail_color_bright, (int(self.pos.x), int(self.pos.y)), marker_size)
        pygame.draw.circle(screen, (255, 255, 255), (int(self.pos.x), int(self.pos.y)), marker_size - 2)


class ShatterFragment:
    """적 사망 시 생성되는 이미지 파편"""

    def __init__(self, image_piece: pygame.Surface, pos: pygame.math.Vector2,
                 velocity: pygame.math.Vector2, rotation_speed: float):
        """파편 초기화

        Args:
            image_piece: 파편 이미지 조각
            pos: 초기 위치
            velocity: 초기 속도 벡터
            rotation_speed: 회전 속도 (도/초)
        """
        self.original_image = image_piece
        self.image = image_piece.copy()
        self.pos = pos.copy()
        self.velocity = velocity.copy()
        self.rotation = 0.0
        self.rotation_speed = rotation_speed
        self.alpha = 255
        self.lifetime = 0.0
        self.max_lifetime = 1.0  # 1초 후 소멸
        self.gravity = 800.0  # 중력 가속도
        self.is_alive = True

    def update(self, dt: float):
        """파편 업데이트"""
        if not self.is_alive:
            return

        # 물리 업데이트
        self.velocity.y += self.gravity * dt  # 중력 적용
        self.pos += self.velocity * dt
        self.rotation += self.rotation_speed * dt

        # 수명 업데이트
        self.lifetime += dt
        progress = min(self.lifetime / self.max_lifetime, 1.0)

        # 투명도 감소 (점점 투명해짐)
        self.alpha = int(255 * (1.0 - progress))

        # 이미지 회전 및 투명도 적용
        rotated = pygame.transform.rotate(self.original_image, self.rotation)
        self.image = rotated.copy()
        self.image.set_alpha(self.alpha)

        # 수명 종료 체크
        if self.lifetime >= self.max_lifetime:
            self.is_alive = False

    def draw(self, screen: pygame.Surface):
        """파편 그리기"""
        if not self.is_alive or self.alpha <= 0:
            return

        rect = self.image.get_rect(center=(int(self.pos.x), int(self.pos.y)))
        screen.blit(self.image, rect)


class BurstParticle:
    """파티클 폭발용 개별 파티클"""

    def __init__(self, pos: pygame.math.Vector2, velocity: pygame.math.Vector2, color: tuple, size: float):
        self.pos = pos.copy()
        self.velocity = velocity.copy()
        self.color = color
        self.size = size
        self.alpha = 255
        self.lifetime = 0.0
        self.max_lifetime = 1.6  # 1.6초 수명 (2배 연장)
        self.gravity = 600.0
        self.is_alive = True

    def update(self, dt: float):
        if not self.is_alive:
            return

        self.velocity.y += self.gravity * dt
        self.pos += self.velocity * dt
        self.lifetime += dt

        progress = min(self.lifetime / self.max_lifetime, 1.0)
        self.alpha = int(255 * (1.0 - progress))
        self.size = max(1, self.size * (1.0 - progress * 0.5))

        if self.lifetime >= self.max_lifetime:
            self.is_alive = False

    def draw(self, screen: pygame.Surface):
        if not self.is_alive or self.alpha <= 0:
            return

        surf = pygame.Surface((int(self.size * 2), int(self.size * 2)), pygame.SRCALPHA)
        color_with_alpha = (*self.color[:3], self.alpha)
        pygame.draw.circle(surf, color_with_alpha, (int(self.size), int(self.size)), int(self.size))
        screen.blit(surf, (int(self.pos.x - self.size), int(self.pos.y - self.size)))


class DissolveEffect:
    """디졸브(픽셀 소멸) 효과"""

    def __init__(self, enemy_image: pygame.Surface, enemy_pos: pygame.math.Vector2):
        self.original_image = enemy_image.copy()
        self.pos = enemy_pos.copy()
        self.lifetime = 0.0
        self.max_lifetime = 2.0  # 2.0초 (2배 연장)
        self.is_alive = True

        # 픽셀 데이터 추출
        self.width = enemy_image.get_width()
        self.height = enemy_image.get_height()
        self.pixels = []

        import random
        # 픽셀 좌표를 무작위 순서로 저장
        for y in range(self.height):
            for x in range(self.width):
                self.pixels.append((x, y))
        random.shuffle(self.pixels)

    def update(self, dt: float):
        if not self.is_alive:
            return

        self.lifetime += dt
        if self.lifetime >= self.max_lifetime:
            self.is_alive = False

    def draw(self, screen: pygame.Surface):
        if not self.is_alive:
            return

        progress = min(self.lifetime / self.max_lifetime, 1.0)
        visible_pixel_count = int(len(self.pixels) * (1.0 - progress))

        # 임시 서페이스 생성
        temp_surf = self.original_image.copy()
        temp_surf.set_alpha(int(255 * (1.0 - progress * 0.5)))

        # 사라질 픽셀을 투명하게 만들기
        pixel_array = pygame.PixelArray(temp_surf)
        for i in range(visible_pixel_count, len(self.pixels)):
            x, y = self.pixels[i]
            if 0 <= x < self.width and 0 <= y < self.height:
                pixel_array[x, y] = 0  # 투명

        del pixel_array  # PixelArray 해제

        # 그리기
        rect = temp_surf.get_rect(center=(int(self.pos.x), int(self.pos.y)))
        screen.blit(temp_surf, rect)


class FadeEffect:
    """페이드 & 스케일 효과 - 확대→축소 폭발감 연출"""

    def __init__(self, enemy_image: pygame.Surface, enemy_pos: pygame.math.Vector2):
        self.original_image = enemy_image.copy()
        self.pos = enemy_pos.copy()
        self.lifetime = 0.0
        self.max_lifetime = 1.6  # 1.6초 (2배 연장)
        self.is_alive = True
        self.original_size = (enemy_image.get_width(), enemy_image.get_height())

        # 확대→축소 애니메이션 설정
        self.expand_duration = 0.15  # 확대 시간 (0.15초)
        self.expand_scale = 1.2  # 추가 확대 비율 (20% 더 확대)

    def update(self, dt: float):
        if not self.is_alive:
            return

        self.lifetime += dt
        if self.lifetime >= self.max_lifetime:
            self.is_alive = False

    def draw(self, screen: pygame.Surface):
        if not self.is_alive:
            return

        progress = min(self.lifetime / self.max_lifetime, 1.0)

        # 확대→축소 애니메이션
        if self.lifetime < self.expand_duration:
            # Phase 1: 확대 (0 → expand_scale)
            expand_progress = self.lifetime / self.expand_duration
            # ease-out 효과로 부드러운 확대
            scale = 1.0 + (self.expand_scale - 1.0) * (1.0 - (1.0 - expand_progress) ** 2)
        else:
            # Phase 2: 축소 (expand_scale → 0)
            shrink_progress = (self.lifetime - self.expand_duration) / (self.max_lifetime - self.expand_duration)
            # ease-in 효과로 가속되는 축소
            scale = self.expand_scale * (1.0 - shrink_progress ** 0.8)

        new_width = max(1, int(self.original_size[0] * scale))
        new_height = max(1, int(self.original_size[1] * scale))

        # 이미지 스케일링
        scaled_image = pygame.transform.scale(self.original_image, (new_width, new_height))

        # 투명도 적용 (확대 중에는 100%, 축소 중에 페이드아웃)
        if self.lifetime < self.expand_duration:
            alpha = 255
        else:
            shrink_progress = (self.lifetime - self.expand_duration) / (self.max_lifetime - self.expand_duration)
            alpha = int(255 * (1.0 - shrink_progress))
        scaled_image.set_alpha(alpha)

        # 그리기
        rect = scaled_image.get_rect(center=(int(self.pos.x), int(self.pos.y)))
        screen.blit(scaled_image, rect)


class ImplodeEffect:
    """내파(중심으로 수축) 효과 - 확대→축소 폭발감 연출"""

    def __init__(self, enemy_image: pygame.Surface, enemy_pos: pygame.math.Vector2):
        self.original_image = enemy_image.copy()
        self.pos = enemy_pos.copy()
        self.lifetime = 0.0
        self.max_lifetime = 1.2  # 1.2초 (2배 연장)
        self.is_alive = True
        self.rotation = 0.0
        self.original_size = (enemy_image.get_width(), enemy_image.get_height())

        # 확대→축소 애니메이션 설정
        self.expand_duration = 0.12  # 확대 시간 (0.12초, 더 빠르게)
        self.expand_scale = 1.25  # 추가 확대 비율 (25% 더 확대)

    def update(self, dt: float):
        if not self.is_alive:
            return

        self.lifetime += dt

        # 확대 중에는 회전 없음, 축소 시작 후 가속 회전
        if self.lifetime >= self.expand_duration:
            shrink_progress = (self.lifetime - self.expand_duration) / (self.max_lifetime - self.expand_duration)
            # 축소하면서 점점 빨라지는 회전
            rotation_speed = 720 * (1.0 + shrink_progress * 2)  # 720 → 2160 deg/s
            self.rotation += rotation_speed * dt

        if self.lifetime >= self.max_lifetime:
            self.is_alive = False

    def draw(self, screen: pygame.Surface):
        if not self.is_alive:
            return

        # 확대→축소 애니메이션
        if self.lifetime < self.expand_duration:
            # Phase 1: 확대 (폭발 직전 팽창)
            expand_progress = self.lifetime / self.expand_duration
            # ease-out 효과로 부드러운 확대
            scale = 1.0 + (self.expand_scale - 1.0) * (1.0 - (1.0 - expand_progress) ** 2)
        else:
            # Phase 2: 급격한 축소 (빨려들어감)
            shrink_progress = (self.lifetime - self.expand_duration) / (self.max_lifetime - self.expand_duration)
            # ease-in 효과로 가속되는 축소
            scale = self.expand_scale * (1.0 - shrink_progress) ** 2

        new_width = max(1, int(self.original_size[0] * scale))
        new_height = max(1, int(self.original_size[1] * scale))

        # 이미지 스케일링 및 회전
        scaled_image = pygame.transform.scale(self.original_image, (new_width, new_height))
        rotated_image = pygame.transform.rotate(scaled_image, self.rotation)

        # 투명도 적용 (확대 중에는 100%, 축소 끝에 급격히 사라짐)
        if self.lifetime < self.expand_duration:
            alpha = 255
        else:
            shrink_progress = (self.lifetime - self.expand_duration) / (self.max_lifetime - self.expand_duration)
            alpha = int(255 * (1.0 - shrink_progress ** 3))
        rotated_image.set_alpha(alpha)

        # 그리기
        rect = rotated_image.get_rect(center=(int(self.pos.x), int(self.pos.y)))
        screen.blit(rotated_image, rect)


class VortexEffect:
    """소용돌이(차원 균열) 효과 - 확대→축소 회전하며 빨려들어감"""

    def __init__(self, enemy_image: pygame.Surface, enemy_pos: pygame.math.Vector2):
        self.original_image = enemy_image.copy()
        self.pos = enemy_pos.copy()
        self.lifetime = 0.0
        self.max_lifetime = 2.4  # 2.4초 (2배 연장)
        self.is_alive = True
        self.rotation = 0.0
        self.original_size = (enemy_image.get_width(), enemy_image.get_height())

        # 확대→축소 애니메이션 설정
        self.expand_duration = 0.18  # 확대 시간 (0.18초)
        self.expand_scale = 1.15  # 추가 확대 비율 (15% 더 확대)

        # 나선 파티클 리스트
        self.spiral_particles = []
        self._create_spiral_particles()

    def _create_spiral_particles(self):
        """나선형 파티클 생성"""
        import random
        import math

        particle_count = 20
        for i in range(particle_count):
            angle = (i / particle_count) * math.pi * 4  # 2바퀴 나선
            distance = random.uniform(30, 80)
            speed = random.uniform(80, 150)
            color = random.choice([
                (100, 150, 255),  # 파란색
                (150, 100, 255),  # 보라색
                (200, 150, 255),  # 연보라색
            ])
            self.spiral_particles.append({
                'angle': angle,
                'distance': distance,
                'speed': speed,
                'color': color,
                'size': random.uniform(2, 5),
                'alpha': 255
            })

    def update(self, dt: float):
        if not self.is_alive:
            return

        self.lifetime += dt

        # 확대 중에는 회전 느리게, 축소 시작 후 가속 회전
        if self.lifetime < self.expand_duration:
            self.rotation += 180 * dt  # 느린 회전
        else:
            # 점점 빨라지는 회전 (가속)
            shrink_progress = (self.lifetime - self.expand_duration) / (self.max_lifetime - self.expand_duration)
            acceleration = 1.0 + shrink_progress * 3
            self.rotation += 720 * dt * acceleration

        # 파티클 업데이트 (중심으로 수렴)
        for p in self.spiral_particles:
            p['angle'] += dt * 5  # 나선 회전
            p['distance'] = max(0, p['distance'] - p['speed'] * dt)
            p['alpha'] = max(0, p['alpha'] - 200 * dt)

        if self.lifetime >= self.max_lifetime:
            self.is_alive = False

    def draw(self, screen: pygame.Surface):
        if not self.is_alive:
            return

        import math

        progress = min(self.lifetime / self.max_lifetime, 1.0)

        # 나선 파티클 그리기 (뒤에)
        for p in self.spiral_particles:
            if p['alpha'] > 0 and p['distance'] > 0:
                px = self.pos.x + math.cos(p['angle']) * p['distance']
                py = self.pos.y + math.sin(p['angle']) * p['distance']
                color_with_alpha = (*p['color'], int(p['alpha']))
                surf = pygame.Surface((int(p['size'] * 2), int(p['size'] * 2)), pygame.SRCALPHA)
                pygame.draw.circle(surf, color_with_alpha, (int(p['size']), int(p['size'])), int(p['size']))
                screen.blit(surf, (int(px - p['size']), int(py - p['size'])))

        # 확대→축소 애니메이션
        if self.lifetime < self.expand_duration:
            # Phase 1: 확대
            expand_progress = self.lifetime / self.expand_duration
            scale = 1.0 + (self.expand_scale - 1.0) * (1.0 - (1.0 - expand_progress) ** 2)
        else:
            # Phase 2: 급격한 축소 (빨려들어감)
            shrink_progress = (self.lifetime - self.expand_duration) / (self.max_lifetime - self.expand_duration)
            scale = self.expand_scale * (1.0 - shrink_progress) ** 1.5

        new_width = max(1, int(self.original_size[0] * scale))
        new_height = max(1, int(self.original_size[1] * scale))

        # 이미지 스케일링 및 회전
        scaled_image = pygame.transform.scale(self.original_image, (new_width, new_height))
        rotated_image = pygame.transform.rotate(scaled_image, self.rotation)

        # 투명도 + 색조 변화 (파란색으로)
        if self.lifetime < self.expand_duration:
            alpha = 255
        else:
            shrink_progress = (self.lifetime - self.expand_duration) / (self.max_lifetime - self.expand_duration)
            alpha = int(255 * (1.0 - shrink_progress ** 2))
        rotated_image.set_alpha(alpha)

        # 파란색 오버레이 (차원 균열 느낌) - 축소 시작 후에만
        if self.lifetime >= self.expand_duration:
            shrink_progress = (self.lifetime - self.expand_duration) / (self.max_lifetime - self.expand_duration)
            if shrink_progress > 0.2:
                tint_surf = pygame.Surface(rotated_image.get_size(), pygame.SRCALPHA)
                tint_alpha = int(100 * (shrink_progress - 0.2) / 0.8)
                tint_surf.fill((100, 150, 255, tint_alpha))
                rotated_image.blit(tint_surf, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

        # 그리기
        rect = rotated_image.get_rect(center=(int(self.pos.x), int(self.pos.y)))
        screen.blit(rotated_image, rect)

        # 마지막 플래시 효과
        if progress > 0.85:
            flash_alpha = int(200 * (progress - 0.85) / 0.15)
            flash_size = int(30 * (1.0 - (progress - 0.85) / 0.15))
            if flash_size > 0:
                flash_surf = pygame.Surface((flash_size * 2, flash_size * 2), pygame.SRCALPHA)
                pygame.draw.circle(flash_surf, (200, 220, 255, flash_alpha),
                                 (flash_size, flash_size), flash_size)
                screen.blit(flash_surf, (int(self.pos.x - flash_size), int(self.pos.y - flash_size)))


class PixelateEffect:
    """픽셀화(디지털 글리치) 효과 - 레트로 스타일로 분해"""

    def __init__(self, enemy_image: pygame.Surface, enemy_pos: pygame.math.Vector2):
        self.original_image = enemy_image.copy()
        self.pos = enemy_pos.copy()
        self.lifetime = 0.0
        self.max_lifetime = 2.0  # 2.0초 (2배 연장)
        self.is_alive = True
        self.original_size = (enemy_image.get_width(), enemy_image.get_height())

        # 픽셀 블록 리스트 (분해 후)
        self.pixel_blocks = []
        self.phase = 'pixelate'  # 'pixelate' -> 'scatter'
        self.scatter_started = False

        # 타이밍 설정 (2배 연장)
        self.pixelate_duration = 0.8  # 픽셀화 단계 시간
        self.scatter_duration = 1.2   # 분해 단계 시간

    def _create_pixel_blocks(self, block_size: int = 8):
        """픽셀 블록 생성 (분해용)"""
        import random
        import math

        width, height = self.original_size

        for y in range(0, height, block_size):
            for x in range(0, width, block_size):
                # 블록 영역 추출
                block_w = min(block_size, width - x)
                block_h = min(block_size, height - y)

                if block_w <= 0 or block_h <= 0:
                    continue

                # 블록 이미지 추출
                block_rect = pygame.Rect(x, y, block_w, block_h)
                try:
                    block_surf = self.original_image.subsurface(block_rect).copy()
                except:
                    continue

                # 블록 위치 (적 중심 기준)
                offset_x = x - width / 2 + block_w / 2
                offset_y = y - height / 2 + block_h / 2
                block_pos = pygame.math.Vector2(
                    self.pos.x + offset_x,
                    self.pos.y + offset_y
                )

                # 랜덤 속도 (아래로 떨어짐 + 좌우 흩어짐)
                angle = random.uniform(-math.pi / 3, math.pi / 3) - math.pi / 2  # 위쪽 반원
                speed = random.uniform(50, 150)
                velocity = pygame.math.Vector2(
                    math.cos(angle) * speed * 0.5,
                    random.uniform(30, 100)  # 아래로 떨어짐
                )

                self.pixel_blocks.append({
                    'image': block_surf,
                    'pos': block_pos,
                    'velocity': velocity,
                    'alpha': 255,
                    'blink_timer': random.uniform(0, 0.5),  # 깜빡임 타이머
                    'gravity': random.uniform(150, 250)
                })

    def update(self, dt: float):
        if not self.is_alive:
            return

        self.lifetime += dt

        # 페이즈 전환 (pixelate_duration 후 분해 시작)
        if self.phase == 'pixelate' and self.lifetime >= self.pixelate_duration:
            self.phase = 'scatter'
            if not self.scatter_started:
                self._create_pixel_blocks(block_size=8)
                self.scatter_started = True

        # 분해 페이즈: 블록 업데이트
        if self.phase == 'scatter':
            for block in self.pixel_blocks:
                # 중력 적용
                block['velocity'].y += block['gravity'] * dt
                block['pos'] += block['velocity'] * dt

                # 깜빡임
                block['blink_timer'] -= dt
                if block['blink_timer'] <= 0:
                    block['blink_timer'] = random.uniform(0.05, 0.15)

                # 페이드아웃
                scatter_progress = (self.lifetime - self.pixelate_duration) / self.scatter_duration
                block['alpha'] = max(0, int(255 * (1.0 - scatter_progress)))

        if self.lifetime >= self.max_lifetime:
            self.is_alive = False

    def draw(self, screen: pygame.Surface):
        if not self.is_alive:
            return

        progress = min(self.lifetime / self.max_lifetime, 1.0)

        if self.phase == 'pixelate':
            # 픽셀화 단계: 해상도 점점 낮아짐
            pixelate_progress = min(self.lifetime / self.pixelate_duration, 1.0)

            # 픽셀 크기 계산 (1 -> 16)
            pixel_size = int(1 + pixelate_progress * 15)

            # 축소 후 확대로 픽셀화 효과
            small_w = max(1, self.original_size[0] // pixel_size)
            small_h = max(1, self.original_size[1] // pixel_size)

            # 축소
            small_img = pygame.transform.scale(self.original_image, (small_w, small_h))
            # 다시 확대 (픽셀화)
            pixelated = pygame.transform.scale(small_img, self.original_size)

            # 글리치 효과 (RGB 분리)
            if pixelate_progress > 0.5:
                glitch_offset = int(3 * (pixelate_progress - 0.5) / 0.5)
                if glitch_offset > 0:
                    # 빨간색 채널 오프셋
                    glitch_surf = pygame.Surface(self.original_size, pygame.SRCALPHA)
                    glitch_surf.blit(pixelated, (glitch_offset, 0))
                    glitch_surf.set_alpha(50)
                    pixelated.blit(glitch_surf, (0, 0), special_flags=pygame.BLEND_RGB_ADD)

            # 그리기
            rect = pixelated.get_rect(center=(int(self.pos.x), int(self.pos.y)))
            screen.blit(pixelated, rect)

        else:
            # 분해 단계: 블록들이 흩어짐
            import random
            for block in self.pixel_blocks:
                if block['alpha'] <= 0:
                    continue

                # 깜빡임 효과
                if block['blink_timer'] < 0.03:
                    continue  # 깜빡임 중 안 보임

                block_img = block['image'].copy()
                block_img.set_alpha(block['alpha'])

                rect = block_img.get_rect(center=(int(block['pos'].x), int(block['pos'].y)))
                screen.blit(block_img, rect)


class DeathEffectManager:
    """적 사망 효과 관리 클래스"""

    def __init__(self):
        """사망 효과 매니저 초기화"""
        self.fragments = []  # ShatterFragment 리스트
        self.particles = []  # BurstParticle 리스트
        self.dissolve_effects = []  # DissolveEffect 리스트
        self.fade_effects = []  # FadeEffect 리스트
        self.implode_effects = []  # ImplodeEffect 리스트
        self.vortex_effects = []  # VortexEffect 리스트
        self.pixelate_effects = []  # PixelateEffect 리스트

        self.current_effect = "shatter"  # 현재 선택된 효과

        # 모든 효과 활성화
        self.enabled_effects = {
            "shatter": True,
            "particle_burst": True,
            "dissolve": True,
            "fade": True,
            "implode": True,
            "vortex": True,
            "pixelate": True
        }

        # 적 유형별 죽음 효과 매핑
        self.enemy_type_effects = {
            "NORMAL": "shatter",        # 일반: 파편화
            "TANK": "implode",          # 탱크: 내파 (무거운 느낌)
            "RUNNER": "fade",           # 러너: 빠른 페이드 (빠른 적)
            "SUMMONER": "vortex",       # 소환사: 소용돌이 (마법적 느낌)
            "SHIELDED": "dissolve",     # 보호막: 디졸브 (보호막 소멸)
            "KAMIKAZE": "particle_burst", # 카미카제: 폭발 파티클
            "RESPAWNED": "pixelate",    # 리스폰: 픽셀화 (디지털 글리치)
        }

    def create_shatter_effect(self, enemy_image: pygame.Surface, enemy_pos: pygame.math.Vector2,
                             grid_size: int = 4):
        """이미지 파편화 효과 생성

        Args:
            enemy_image: 적 이미지
            enemy_pos: 적 위치
            grid_size: 파편 그리드 크기 (4x4 = 16조각)
        """
        import random
        import math

        if not enemy_image:
            return

        image_width = enemy_image.get_width()
        image_height = enemy_image.get_height()
        piece_width = image_width // grid_size
        piece_height = image_height // grid_size

        # 각 파편 생성
        for row in range(grid_size):
            for col in range(grid_size):
                # 이미지 조각 추출
                piece_rect = pygame.Rect(col * piece_width, row * piece_height,
                                        piece_width, piece_height)
                piece = enemy_image.subsurface(piece_rect).copy()

                # 파편 시작 위치 (적 중심 기준)
                offset_x = (col - grid_size / 2 + 0.5) * piece_width
                offset_y = (row - grid_size / 2 + 0.5) * piece_height
                frag_pos = pygame.math.Vector2(
                    enemy_pos.x + offset_x,
                    enemy_pos.y + offset_y
                )

                # 폭발 방향 (중심에서 바깥으로)
                angle = math.atan2(offset_y, offset_x)
                speed = random.uniform(150, 300)  # 속도 무작위
                velocity = pygame.math.Vector2(
                    math.cos(angle) * speed,
                    math.sin(angle) * speed - random.uniform(50, 150)  # 위쪽으로 약간 튀어오름
                )

                # 회전 속도 무작위
                rotation_speed = random.uniform(-360, 360)

                # 파편 생성
                fragment = ShatterFragment(piece, frag_pos, velocity, rotation_speed)
                self.fragments.append(fragment)

    def create_particle_burst(self, pos: pygame.math.Vector2, color: tuple, count: int = 30):
        """파티클 폭발 효과 생성

        Args:
            pos: 폭발 위치
            color: 파티클 색상
            count: 파티클 개수
        """
        import random
        import math

        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(100, 250)
            velocity = pygame.math.Vector2(
                math.cos(angle) * speed,
                math.sin(angle) * speed - random.uniform(0, 100)
            )
            size = random.uniform(2, 5)

            particle = BurstParticle(pos.copy(), velocity, color, size)
            self.particles.append(particle)

    def create_dissolve_effect(self, enemy_image: pygame.Surface, enemy_pos: pygame.math.Vector2):
        """디졸브 효과 생성"""
        effect = DissolveEffect(enemy_image, enemy_pos)
        self.dissolve_effects.append(effect)

    def create_fade_effect(self, enemy_image: pygame.Surface, enemy_pos: pygame.math.Vector2):
        """페이드 효과 생성"""
        effect = FadeEffect(enemy_image, enemy_pos)
        self.fade_effects.append(effect)

    def create_implode_effect(self, enemy_image: pygame.Surface, enemy_pos: pygame.math.Vector2):
        """내파 효과 생성"""
        effect = ImplodeEffect(enemy_image, enemy_pos)
        self.implode_effects.append(effect)

    def create_vortex_effect(self, enemy_image: pygame.Surface, enemy_pos: pygame.math.Vector2):
        """소용돌이 효과 생성"""
        effect = VortexEffect(enemy_image, enemy_pos)
        self.vortex_effects.append(effect)

    def create_pixelate_effect(self, enemy_image: pygame.Surface, enemy_pos: pygame.math.Vector2):
        """픽셀화 효과 생성"""
        effect = PixelateEffect(enemy_image, enemy_pos)
        self.pixelate_effects.append(effect)

    def update(self, dt: float):
        """모든 효과 업데이트"""
        # 파편 업데이트
        for fragment in self.fragments[:]:
            fragment.update(dt)
            if not fragment.is_alive:
                self.fragments.remove(fragment)

        # 파티클 업데이트
        for particle in self.particles[:]:
            particle.update(dt)
            if not particle.is_alive:
                self.particles.remove(particle)

        # 디졸브 효과 업데이트
        for effect in self.dissolve_effects[:]:
            effect.update(dt)
            if not effect.is_alive:
                self.dissolve_effects.remove(effect)

        # 페이드 효과 업데이트
        for effect in self.fade_effects[:]:
            effect.update(dt)
            if not effect.is_alive:
                self.fade_effects.remove(effect)

        # 내파 효과 업데이트
        for effect in self.implode_effects[:]:
            effect.update(dt)
            if not effect.is_alive:
                self.implode_effects.remove(effect)

        # 소용돌이 효과 업데이트
        for effect in self.vortex_effects[:]:
            effect.update(dt)
            if not effect.is_alive:
                self.vortex_effects.remove(effect)

        # 픽셀화 효과 업데이트
        for effect in self.pixelate_effects[:]:
            effect.update(dt)
            if not effect.is_alive:
                self.pixelate_effects.remove(effect)

    def draw(self, screen: pygame.Surface):
        """모든 효과 그리기"""
        for fragment in self.fragments:
            fragment.draw(screen)

        for particle in self.particles:
            particle.draw(screen)

        for effect in self.dissolve_effects:
            effect.draw(screen)

        for effect in self.fade_effects:
            effect.draw(screen)

        for effect in self.implode_effects:
            effect.draw(screen)

        for effect in self.vortex_effects:
            effect.draw(screen)

        for effect in self.pixelate_effects:
            effect.draw(screen)

    def trigger_death_effect(self, enemy):
        """적 사망 시 효과 발동 (적 유형에 따라 자동 매칭)

        Args:
            enemy: 사망한 Enemy 객체
        """
        # 적 이미지 생성
        if hasattr(enemy, 'image') and enemy.image:
            enemy_image = enemy.image
        else:
            # 임시 이미지 생성 (적 크기에 맞춤)
            enemy_image = pygame.Surface((int(enemy.size * 2), int(enemy.size * 2)), pygame.SRCALPHA)
            pygame.draw.circle(enemy_image, enemy.color,
                             (int(enemy.size), int(enemy.size)), int(enemy.size))

        # 사망 효과용 확대 이미지 생성 (1.3배 확대로 폭발감 연출)
        death_scale = 1.3
        if hasattr(enemy, 'is_boss') and enemy.is_boss:
            death_scale = 1.5  # 보스는 더 크게 확대

        scaled_width = int(enemy_image.get_width() * death_scale)
        scaled_height = int(enemy_image.get_height() * death_scale)
        scaled_image = pygame.transform.smoothscale(enemy_image, (scaled_width, scaled_height))

        # 적 유형에 따라 효과 선택
        enemy_type = getattr(enemy, 'enemy_type', 'NORMAL')
        effect_name = self.enemy_type_effects.get(enemy_type, self.current_effect)

        # 보스는 항상 shatter (큰 파편 효과)
        if hasattr(enemy, 'is_boss') and enemy.is_boss:
            effect_name = "shatter"

        # 선택된 효과 발동 (확대된 이미지 사용)
        self._apply_effect(effect_name, scaled_image, enemy.pos, getattr(enemy, 'color', (255, 100, 100)))

    def _apply_effect(self, effect_name: str, enemy_image: pygame.Surface,
                     enemy_pos: pygame.math.Vector2, enemy_color: tuple):
        """실제 효과 적용"""
        if effect_name == "shatter" and self.enabled_effects.get("shatter", True):
            self.create_shatter_effect(enemy_image, enemy_pos)

        elif effect_name == "particle_burst" and self.enabled_effects.get("particle_burst", True):
            self.create_particle_burst(enemy_pos, enemy_color, count=40)

        elif effect_name == "dissolve" and self.enabled_effects.get("dissolve", True):
            self.create_dissolve_effect(enemy_image, enemy_pos)

        elif effect_name == "fade" and self.enabled_effects.get("fade", True):
            self.create_fade_effect(enemy_image, enemy_pos)

        elif effect_name == "implode" and self.enabled_effects.get("implode", True):
            self.create_implode_effect(enemy_image, enemy_pos)

        elif effect_name == "vortex" and self.enabled_effects.get("vortex", True):
            self.create_vortex_effect(enemy_image, enemy_pos)

        elif effect_name == "pixelate" and self.enabled_effects.get("pixelate", True):
            self.create_pixelate_effect(enemy_image, enemy_pos)

    def set_effect(self, effect_name: str):
        """현재 효과 설정

        Args:
            effect_name: 효과 이름 (shatter, particle_burst, dissolve, fade, implode)
        """
        if effect_name in self.enabled_effects:
            self.current_effect = effect_name
            print(f"INFO: Death effect changed to: {effect_name}")

    def clear(self):
        """모든 효과 제거"""
        self.fragments.clear()
        self.particles.clear()
        self.dissolve_effects.clear()
        self.fade_effects.clear()
        self.implode_effects.clear()
        self.vortex_effects.clear()
        self.pixelate_effects.clear()


# =========================================================
# 스토리 브리핑 효과 (비주얼 노벨 스타일)
# =========================================================
class StoryBriefingEffect:
    """
    스토리 브리핑 효과 - 비주얼 노벨 스타일 대사 시스템

    특징:
    - 배경 이미지 + 어둡게 처리
    - 캐릭터 초상화 표시
    - 타이핑 효과로 대사 표시
    - 클릭으로 다음 대사 진행
    - ESC로 스킵 가능
    """

    PHASE_FADEIN = 0       # 배경 페이드인
    PHASE_DIALOGUE = 1     # 대사 진행 중
    PHASE_FADEOUT = 2      # 페이드아웃
    PHASE_DONE = 3         # 완료

    def __init__(self, screen_size: tuple, dialogue_data: list,
                 background_path: str = None, title: str = "", location: str = ""):
        """
        Args:
            screen_size: 화면 크기 (width, height)
            dialogue_data: 대사 리스트 [{"speaker": "...", "text": "..."}, ...]
            background_path: 배경 이미지 경로 (None이면 어두운 배경)
            title: 타이틀 텍스트 (예: "ACT 1: RETURN TO RUINS")
            location: 위치 텍스트 (예: "DESTROYED CITY")
        """
        self.screen_size = screen_size
        self.dialogue_data = dialogue_data
        self.title = title
        self.location = location

        self.is_alive = True
        self.phase = self.PHASE_FADEIN
        self.phase_timer = 0.0

        # 대사 관련
        self.current_dialogue_index = 0
        self.typing_progress = 0.0
        self.typing_speed = 30.0  # 초당 글자 수
        self.current_text = ""
        self.full_text = ""
        self.waiting_for_click = False

        # 페이드 타이밍
        self.fadein_duration = 0.8
        self.fadeout_duration = 0.5
        self.fade_alpha = 0.0

        # 배경 로드
        self.background = None
        self.background_overlay = None
        if background_path:
            self._load_background(background_path)
        self._create_overlay()

        # 초상화 캐시
        self.portrait_cache = {}

        # 캐릭터 색상 (기본값)
        self.character_colors = {
            "ARTEMIS": (255, 220, 150),
            "PILOT": (150, 200, 255),
            "BOSS": (255, 100, 100),
            "NARRATOR": (200, 200, 200),
            "SYSTEM": (100, 255, 200),
        }

        # 폰트 (나중에 외부에서 설정)
        self.fonts = {}

        # 콜백
        self.on_complete = None

        # 첫 대사 준비
        if self.dialogue_data:
            self._prepare_dialogue(0)

    def _load_background(self, path: str):
        """배경 이미지 로드"""
        try:
            img = pygame.image.load(path).convert()
            self.background = pygame.transform.scale(img, self.screen_size)
        except Exception as e:
            print(f"WARNING: Failed to load background: {path} - {e}")
            self.background = None

    def _create_overlay(self):
        """어두운 오버레이 생성"""
        self.background_overlay = pygame.Surface(self.screen_size, pygame.SRCALPHA)
        self.background_overlay.fill((0, 0, 0, 180))

    def _prepare_dialogue(self, index: int):
        """대사 준비"""
        if 0 <= index < len(self.dialogue_data):
            dialogue = self.dialogue_data[index]
            self.full_text = dialogue.get("text", "")
            self.current_text = ""
            self.typing_progress = 0.0
            self.waiting_for_click = False

    def _get_portrait(self, speaker: str) -> pygame.Surface:
        """초상화 이미지 가져오기 (캐시 사용)"""
        if speaker in self.portrait_cache:
            return self.portrait_cache[speaker]

        # config_story_dialogue에서 경로 가져오기
        try:
            from mode_configs.config_story_dialogue import CHARACTER_PORTRAITS
            path = CHARACTER_PORTRAITS.get(speaker)
        except ImportError:
            # 폴백: 기본 경로
            portrait_paths = {
                "ARTEMIS": "assets/story_mode/portraits/portrait_artemis.jpg",
                "PILOT": "assets/story_mode/portraits/portrait_pilot.png",
            }
            path = portrait_paths.get(speaker)

        if path:
            try:
                img = pygame.image.load(path).convert_alpha()
                # 크기 조정 (200x200 정도)
                target_size = (200, 200)
                img = pygame.transform.smoothscale(img, target_size)
                self.portrait_cache[speaker] = img
                return img
            except Exception as e:
                print(f"WARNING: Failed to load portrait for {speaker}: {e}")

        return None

    def set_fonts(self, fonts: dict):
        """폰트 설정"""
        self.fonts = fonts

    def update(self, dt: float):
        """업데이트"""
        if not self.is_alive:
            return

        self.phase_timer += dt

        if self.phase == self.PHASE_FADEIN:
            # 페이드인
            progress = min(self.phase_timer / self.fadein_duration, 1.0)
            self.fade_alpha = progress

            if progress >= 1.0:
                self.phase = self.PHASE_DIALOGUE
                self.phase_timer = 0.0

        elif self.phase == self.PHASE_DIALOGUE:
            # 타이핑 효과
            if not self.waiting_for_click:
                self.typing_progress += self.typing_speed * dt
                char_count = int(self.typing_progress)

                if char_count >= len(self.full_text):
                    self.current_text = self.full_text
                    self.waiting_for_click = True
                else:
                    self.current_text = self.full_text[:char_count]

        elif self.phase == self.PHASE_FADEOUT:
            # 페이드아웃
            progress = min(self.phase_timer / self.fadeout_duration, 1.0)
            self.fade_alpha = 1.0 - progress

            if progress >= 1.0:
                self.phase = self.PHASE_DONE
                self.is_alive = False
                if self.on_complete:
                    self.on_complete()

    def handle_click(self):
        """클릭 처리"""
        if self.phase == self.PHASE_FADEIN:
            # 페이드인 스킵
            self.phase = self.PHASE_DIALOGUE
            self.phase_timer = 0.0
            self.fade_alpha = 1.0
            return

        if self.phase != self.PHASE_DIALOGUE:
            return

        if not self.waiting_for_click:
            # 타이핑 스킵 - 전체 텍스트 표시
            self.current_text = self.full_text
            self.waiting_for_click = True
        else:
            # 다음 대사로
            self.current_dialogue_index += 1

            if self.current_dialogue_index >= len(self.dialogue_data):
                # 모든 대사 완료 - 페이드아웃
                self.phase = self.PHASE_FADEOUT
                self.phase_timer = 0.0
            else:
                self._prepare_dialogue(self.current_dialogue_index)

    def skip(self):
        """전체 스킵"""
        self.phase = self.PHASE_FADEOUT
        self.phase_timer = 0.0

    def draw(self, screen: pygame.Surface):
        """렌더링"""
        if not self.is_alive and self.phase == self.PHASE_DONE:
            return

        # 배경
        if self.background:
            screen.blit(self.background, (0, 0))
        else:
            screen.fill((10, 10, 20))

        # 오버레이 (페이드 적용)
        overlay = self.background_overlay.copy()
        overlay.set_alpha(int(180 * self.fade_alpha))
        screen.blit(overlay, (0, 0))

        # 페이드인/아웃 중이면 나머지 UI 표시 안함
        if self.phase == self.PHASE_FADEIN and self.fade_alpha < 0.5:
            return
        if self.phase == self.PHASE_FADEOUT and self.fade_alpha < 0.5:
            return

        # UI 알파
        ui_alpha = int(255 * self.fade_alpha)

        # 타이틀/위치
        self._draw_title(screen, ui_alpha)

        # 대사 박스
        self._draw_dialogue_box(screen, ui_alpha)

    def _draw_title(self, screen: pygame.Surface, alpha: int):
        """타이틀 그리기"""
        if not self.title:
            return

        font = self.fonts.get("large") or self.fonts.get("medium")
        if not font:
            return

        # 타이틀
        title_surf = font.render(self.title, True, (255, 255, 255))
        title_surf.set_alpha(alpha)
        title_rect = title_surf.get_rect(midtop=(self.screen_size[0] // 2, 50))
        screen.blit(title_surf, title_rect)

        # 위치
        if self.location:
            small_font = self.fonts.get("small") or font
            loc_surf = small_font.render(self.location, True, (180, 180, 180))
            loc_surf.set_alpha(alpha)
            loc_rect = loc_surf.get_rect(midtop=(self.screen_size[0] // 2, title_rect.bottom + 10))
            screen.blit(loc_surf, loc_rect)

    def _draw_dialogue_box(self, screen: pygame.Surface, alpha: int):
        """대사 박스 그리기"""
        if self.current_dialogue_index >= len(self.dialogue_data):
            return

        dialogue = self.dialogue_data[self.current_dialogue_index]
        speaker = dialogue.get("speaker", "")

        # 대사 박스 영역 (하단 중앙, 가로 1/2 크기)
        box_height = 180
        box_width = (self.screen_size[0] - 100) // 2
        box_x = (self.screen_size[0] - box_width) // 2
        box_rect = pygame.Rect(
            box_x,
            self.screen_size[1] - box_height - 40,
            box_width,
            box_height
        )

        # 박스 배경
        box_surf = pygame.Surface((box_rect.width, box_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(box_surf, (20, 20, 40, 220), (0, 0, box_rect.width, box_rect.height), border_radius=10)
        pygame.draw.rect(box_surf, (100, 100, 150, 200), (0, 0, box_rect.width, box_rect.height), 2, border_radius=10)
        box_surf.set_alpha(alpha)
        screen.blit(box_surf, box_rect.topleft)

        # 초상화 (모든 캐릭터 왼쪽 배치)
        portrait = self._get_portrait(speaker)
        portrait_width = 0
        if portrait:
            portrait_rect = portrait.get_rect()
            portrait_rect.bottomleft = (box_rect.left + 20, box_rect.bottom - 10)

            portrait_copy = portrait.copy()
            portrait_copy.set_alpha(alpha)
            screen.blit(portrait_copy, portrait_rect)
            portrait_width = portrait_rect.width + 30

        # 화자 이름
        name_color = self.character_colors.get(speaker, (255, 255, 255))
        font = self.fonts.get("medium") or self.fonts.get("small")

        # 텍스트 시작 X 위치 (초상화 오른쪽)
        text_left_x = box_rect.left + portrait_width + 20

        if font and speaker and speaker not in ["NARRATOR", "SYSTEM"]:
            # 이름 표시
            display_name = {
                "ARTEMIS": "아르테미스",
                "PILOT": "파일럿",
                "BOSS": "???",
            }.get(speaker, speaker)

            name_surf = font.render(display_name, True, name_color)
            name_surf.set_alpha(alpha)
            name_rect = name_surf.get_rect(topleft=(text_left_x, box_rect.top + 15))
            screen.blit(name_surf, name_rect)
            text_y = name_rect.bottom + 10
        else:
            text_y = box_rect.top + 20

        # 대사 텍스트
        small_font = self.fonts.get("small") or font
        if small_font and self.current_text:
            text_color = (255, 255, 255) if speaker not in ["NARRATOR", "SYSTEM"] else (180, 180, 180)

            # 줄바꿈 처리 (초상화 위치에 따라 텍스트 영역 조정)
            max_width = box_rect.width - portrait_width - 60
            words = self.current_text.split()
            lines = []
            current_line = ""

            for word in words:
                test_line = current_line + (" " if current_line else "") + word
                if small_font.size(test_line)[0] <= max_width:
                    current_line = test_line
                else:
                    if current_line:
                        lines.append(current_line)
                    current_line = word
            if current_line:
                lines.append(current_line)

            # 텍스트 그리기
            for i, line in enumerate(lines):
                text_surf = small_font.render(line, True, text_color)
                text_surf.set_alpha(alpha)
                screen.blit(text_surf, (text_left_x, text_y + i * 28))

        # 클릭 대기 표시
        if self.waiting_for_click:
            indicator_text = "Click to continue..." if self.current_dialogue_index < len(self.dialogue_data) - 1 else "Click to finish..."
            ind_surf = small_font.render(indicator_text, True, (150, 150, 150))
            ind_surf.set_alpha(int(alpha * (0.5 + 0.5 * math.sin(pygame.time.get_ticks() / 300))))
            ind_rect = ind_surf.get_rect(bottomright=(box_rect.right - 20, box_rect.bottom - 15))
            screen.blit(ind_surf, ind_rect)


# =========================================================
# 폴라로이드 회상 효과
# =========================================================
class PolaroidMemoryEffect:
    """
    폴라로이드 회상 컷씬 효과

    특징:
    - 배경 이미지 + 어둡게 처리
    - 여러 장의 폴라로이드 사진이 겹쳐서 표시
    - 각 사진은 랜덤 각도로 회전
    - 순차적으로 등장하는 애니메이션
    - 프레임(흰 테두리)은 코드로 자동 생성
    """

    PHASE_FADEIN = 0       # 배경 페이드인
    PHASE_PHOTOS = 1       # 사진 등장
    PHASE_DISPLAY = 2      # 사진 표시 (대기)
    PHASE_DIALOGUE = 3     # 대사 표시
    PHASE_FINAL_ZOOM = 4   # 최종 사진 확대 (memory_survive)
    PHASE_FADEOUT = 5      # 페이드아웃
    PHASE_DONE = 6         # 완료

    def __init__(self, screen_size: tuple, photo_paths: list,
                 background_path: str = None, dialogue_after: list = None,
                 dialogue_per_photo: list = None,
                 sound_manager=None, special_effects: dict = None,
                 scene_id: str = "memory_scene_01"):
        """
        Args:
            screen_size: 화면 크기
            photo_paths: 폴라로이드 사진 경로 리스트
            background_path: 배경 이미지 경로
            dialogue_after: 모든 사진 표시 후 대사 리스트
            dialogue_per_photo: 각 폴라로이드 등장 시 자동 표시되는 대사 리스트
            sound_manager: 효과음 재생용
            special_effects: 특수 효과 설정 (파일명: {effect: "flicker"/"fullscreen_fadeout", ...})
            scene_id: 메모리 씬 식별자 (리플레이용)
        """
        self.screen_size = screen_size
        self.photo_paths = photo_paths
        self.background_path = background_path  # 리플레이용 저장
        self.dialogue_after = dialogue_after or []
        self.dialogue_per_photo = dialogue_per_photo or []  # 각 폴라로이드에 대응하는 대화
        self.sound_manager = sound_manager
        self.special_effects = special_effects or {}
        self.scene_id = scene_id  # 메모리 씬 ID

        self.is_alive = True
        self.phase = self.PHASE_FADEIN
        self.phase_timer = 0.0

        # 타이밍 (조금 빠르게 조정 - 기존 대비 약 15% 단축)
        self.fadein_duration = 1.8
        self.photo_interval = 4.3  # 사진 완전 등장 후 대기 시간 (대화 읽을 시간 포함)
        self.photo_animation_speed = 0.12  # 사진 날아오는 속도
        self.display_duration = 2.5  # 전체 사진 표시 후 대기 시간
        self.fadeout_duration = 1.8
        self.fade_alpha = 0.0

        # 사진 확대 효과용 (여러 사진 지원)
        self.final_zoom_duration = 3.0  # 확대 지속 시간
        self.final_zoom_scale = 1.0  # 현재 확대 배율
        self.final_zoom_alpha = 255  # 최종 사진 알파
        self.zoom_photo_indices = []  # 확대 효과 적용할 사진 인덱스 리스트
        self.current_zoom_index = 0  # 현재 확대 중인 사진 인덱스 (리스트 내 위치)
        self.final_photo_index = -1  # 현재 확대 중인 실제 사진 인덱스 (호환성용)

        # 점멸 효과용
        self.flicker_timer = 0.0

        # 배경
        self.background = None
        if background_path:
            self._load_background(background_path)

        # 폴라로이드 사진들
        self.polaroids = []
        self._prepare_polaroids()

        # 현재 표시 중인 사진 개수
        self.visible_count = 0
        self.photo_timer = 0.0

        # 대사 관련 (폴라로이드별 + 마지막 대화)
        self.current_dialogue_index = 0
        self.dialogue_text = ""
        self.typing_progress = 0.0
        self.typing_speed = 30.0  # 타이핑 속도
        self.waiting_for_click = False
        self.current_photo_dialogue_shown = False  # 현재 폴라로이드 대화 표시 완료 여부

        # 초상화 캐시
        self.portrait_cache = {}

        # 폰트
        self.fonts = {}

        # 콜백
        self.on_complete = None
        self.on_replay_request = None  # 리플레이 요청 콜백

        # 리플레이 버튼 관련
        self.replay_button_rect = None
        self.replay_button_hover = False
        self.replay_button_alpha = 0.0  # 버튼 페이드 인 효과

    def _load_background(self, path: str):
        """배경 이미지 로드"""
        try:
            img = pygame.image.load(path).convert()
            self.background = pygame.transform.scale(img, self.screen_size)
        except Exception as e:
            print(f"WARNING: Failed to load background: {path} - {e}")

    def _prepare_polaroids(self):
        """폴라로이드 사진 준비 - 자연스럽게 흩어진 배치"""
        import random

        # 화면 중앙 영역 계산
        screen_w, screen_h = self.screen_size
        center_x = screen_w // 2
        center_y = screen_h // 2 - 50

        # 사진 크기
        photo_size = 260

        # 자연스럽게 흩어진 위치 (테이블 위에 던져놓은 느낌)
        # 흰 테두리가 살짝 겹치는 정도로 배치 - 9장 사진용
        base_positions = [
            (-320, -160),   # 좌상단 - 1번
            (80, -200),     # 중상단 (약간 치우침) - 2번
            (350, -80),     # 우측 - 3번
            (-250, 100),    # 좌하단 - 4번
            (30, 120),      # 중앙 아래 - 5번
            (320, 200),     # 우하단 - 6번
            (-380, 20),     # 좌측 중앙 - 7번
            (-150, -50),    # 중앙 좌측 (memory_ufo용) - 8번
            (0, 0),         # 정중앙 (memory_survive용 - 확대될 사진) - 9번
        ]

        positions = []
        for bx, by in base_positions:
            # 각 위치에 랜덤 오프셋 추가 (자연스러움)
            offset_x = random.randint(-60, 60)
            offset_y = random.randint(-50, 50)
            x = center_x + bx + offset_x
            y = center_y + by + offset_y
            positions.append((x, y))

        # 위치 순서도 섞기 (더 자연스럽게)
        random.shuffle(positions)

        # 다양한 진입 방향 정의 (외부에서 날아오기) - 9개
        entry_directions = [
            ("left", -400, 0),      # 왼쪽에서 - 1번
            ("right", 400, 0),      # 오른쪽에서 - 2번
            ("top", 0, -400),       # 위에서 - 3번
            ("bottom", 0, 400),     # 아래에서 - 4번
            ("top_left", -300, -300),   # 좌상단에서 - 5번
            ("bottom_right", 300, 300),  # 우하단에서 - 6번
            ("left_bottom", -350, 200),  # 좌측 아래에서 - 7번
            ("top_right", 300, -300),   # 우상단에서 (memory_ufo용) - 8번
            ("bottom_left", -300, 300),  # 좌하단에서 (memory_survive용) - 9번
        ]

        for i, path in enumerate(self.photo_paths):
            if i >= len(positions):
                break

            # 이미지 로드
            photo_img = None
            try:
                photo_img = pygame.image.load(path).convert_alpha()
                # 크기 조정
                photo_img = pygame.transform.smoothscale(photo_img, (photo_size, photo_size))
            except Exception as e:
                print(f"WARNING: Failed to load polaroid: {path} - {e}")
                # 플레이스홀더 생성
                photo_img = pygame.Surface((photo_size, photo_size))
                photo_img.fill((100, 100, 100))

            # 폴라로이드 프레임 생성 (낡은 효과)
            # 2번째 사진(인덱스 1)에만 photo_flip_00.png 적용
            framed = self._create_polaroid_frame(photo_img, photo_index=i)

            # 최종 목표 위치
            target_x, target_y = positions[i]

            # 진입 방향 선택 (다양하게)
            direction_name, offset_x, offset_y = entry_directions[i % len(entry_directions)]

            # 시작 위치 (화면 외부)
            start_x = target_x + offset_x
            start_y = target_y + offset_y

            # 랜덤 각도 (-18도 ~ +18도) - 더 자연스럽게 기울어짐
            angle = random.uniform(-18, 18)

            # 회전 적용
            rotated = pygame.transform.rotate(framed, angle)

            # 파일명 추출 (특수 효과 확인용)
            filename = Path(path).name
            effect_info = self.special_effects.get(filename, {})
            effect_type = effect_info.get("effect", None)

            # 확대 효과가 적용될 사진 인덱스 저장 (flicker_then_zoom 또는 fullscreen_fadeout)
            if effect_type in ["fullscreen_fadeout", "flicker_then_zoom"]:
                self.zoom_photo_indices.append(i)

            self.polaroids.append({
                'image': rotated,
                'original_image': framed,  # 원본 보관 (스케일 조정용)
                'photo_image': photo_img,  # 원본 사진 (확대용)
                'pos': [start_x, start_y],  # 현재 위치 (리스트로 변경 - 수정 가능)
                'target_pos': (target_x, target_y),  # 목표 위치
                'start_pos': (start_x, start_y),  # 시작 위치
                'angle': angle,
                'target_angle': angle + random.uniform(-3, 3),  # 최종 각도 (살짝 변화)
                'alpha': 0,  # 처음엔 투명
                'target_alpha': 255,
                'scale': 0.5,  # 처음엔 작게
                'target_scale': 1.0,
                'direction': direction_name,
                'animation_progress': 0.0,  # 0.0 ~ 1.0
                'filename': filename,  # 파일명 (특수 효과용)
                'effect_type': effect_type,  # 특수 효과 타입
                'flicker_speed': effect_info.get("flicker_speed", 0.3),  # 점멸 속도
                'flicker_phase': 0.0,  # 점멸 위상
            })

    def _create_polaroid_frame(self, photo: pygame.Surface, photo_index: int = 0) -> pygame.Surface:
        """폴라로이드 프레임 생성 - 낡고 빛바랜 효과"""
        import random

        photo_w, photo_h = photo.get_size()

        # 프레임 크기 (테두리 18px, 하단 45px 추가 - 더 크게)
        border = 18
        bottom_margin = 45
        frame_w = photo_w + border * 2
        frame_h = photo_h + border + bottom_margin

        # 프레임 Surface 생성
        frame = pygame.Surface((frame_w, frame_h), pygame.SRCALPHA)

        # 오래된 폴라로이드 색상 (아이보리/크림색, 약간 변색)
        base_color = (245, 240, 225)  # 빛바랜 크림색
        frame.fill(base_color)

        # 불균일한 변색 효과 (노이즈)
        for _ in range(50):
            x = random.randint(0, frame_w - 1)
            y = random.randint(0, frame_h - 1)
            spot_size = random.randint(3, 8)
            # 약간 더 어둡거나 누런 반점
            spot_color = (
                base_color[0] - random.randint(5, 20),
                base_color[1] - random.randint(8, 25),
                base_color[2] - random.randint(10, 30),
            )
            pygame.draw.circle(frame, spot_color, (x, y), spot_size)

        # 가장자리 어둡게 (빛바랜 효과)
        edge_overlay = pygame.Surface((frame_w, frame_h), pygame.SRCALPHA)
        # 상단 가장자리
        for i in range(8):
            alpha = 25 - i * 3
            pygame.draw.line(edge_overlay, (180, 170, 140, alpha), (0, i), (frame_w, i))
        # 하단 가장자리
        for i in range(8):
            alpha = 25 - i * 3
            pygame.draw.line(edge_overlay, (180, 170, 140, alpha), (0, frame_h - 1 - i), (frame_w, frame_h - 1 - i))
        # 좌측 가장자리
        for i in range(6):
            alpha = 20 - i * 3
            pygame.draw.line(edge_overlay, (180, 170, 140, alpha), (i, 0), (i, frame_h))
        # 우측 가장자리
        for i in range(6):
            alpha = 20 - i * 3
            pygame.draw.line(edge_overlay, (180, 170, 140, alpha), (frame_w - 1 - i, 0), (frame_w - 1 - i, frame_h))
        frame.blit(edge_overlay, (0, 0))

        # 외곽선 (낡은 갈색 톤)
        pygame.draw.rect(frame, (200, 185, 160), (0, 0, frame_w, frame_h), 2)
        # 내부 테두리 (더 밝은 선)
        pygame.draw.rect(frame, (230, 220, 200), (2, 2, frame_w - 4, frame_h - 4), 1)

        # 사진에 약간의 세피아/빈티지 효과 적용
        vintage_photo = self._apply_vintage_effect(photo)

        # 사진 배치
        frame.blit(vintage_photo, (border, border))

        # 사진 테두리 (약간 어두운 선)
        pygame.draw.rect(frame, (210, 200, 180), (border - 1, border - 1, photo_w + 2, photo_h + 2), 1)

        # 모서리 들뜬 효과 - 2번째 사진(인덱스 1)에만 photo_flip_00.png 적용
        if photo_index == 1:
            flip_overlay = self._load_flip_overlay(frame_w, frame_h, border, photo_w, photo_h,
                                                    flip_file="photo_flip_00.png")
            if flip_overlay:
                frame.blit(flip_overlay, (0, 0))

        return frame

    def _load_flip_overlay(self, frame_w: int, frame_h: int,
                              border: int = 18, photo_w: int = 260, photo_h: int = 260,
                              flip_file: str = "photo_flip.png") -> pygame.Surface:
        """모서리 들뜬 효과 이미지 로드 - 프레임(흰 테두리)에만 적용"""
        try:
            flip_path = f"assets/story_mode/polaroids/{flip_file}"
            if Path(flip_path).exists():
                img = pygame.image.load(flip_path).convert_alpha()
                # 프레임 크기에 맞게 스케일링
                img = pygame.transform.scale(img, (frame_w, frame_h))

                # 사진 영역을 투명하게 만들기 (프레임만 효과 적용)
                # 사진 영역의 위치: (border, border) ~ (border + photo_w, border + photo_h)
                transparent_rect = pygame.Surface((photo_w, photo_h), pygame.SRCALPHA)
                transparent_rect.fill((0, 0, 0, 0))
                # BLEND_RGBA_MIN: 알파값을 최소화하여 해당 영역을 투명하게
                img.blit(transparent_rect, (border, border), special_flags=pygame.BLEND_RGBA_MIN)

                return img
        except Exception as e:
            print(f"WARNING: Failed to load photo_flip.png: {e}")
        return None

    def _apply_vintage_effect(self, photo: pygame.Surface) -> pygame.Surface:
        """사진에 빈티지/세피아 효과 적용"""
        result = photo.copy()
        w, h = result.get_size()

        # 전체적으로 약간 따뜻한 톤 추가 (세피아 느낌)
        sepia_overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        sepia_overlay.fill((255, 240, 200, 30))  # 따뜻한 세피아 톤
        result.blit(sepia_overlay, (0, 0))

        # 비네트 효과 (가장자리 어둡게)
        vignette = pygame.Surface((w, h), pygame.SRCALPHA)
        for i in range(20):
            alpha = 3 * (20 - i)
            # 상단
            pygame.draw.line(vignette, (0, 0, 0, alpha), (0, i), (w, i))
            # 하단
            pygame.draw.line(vignette, (0, 0, 0, alpha), (0, h - 1 - i), (w, h - 1 - i))
            # 좌측
            pygame.draw.line(vignette, (0, 0, 0, alpha), (i, 0), (i, h))
            # 우측
            pygame.draw.line(vignette, (0, 0, 0, alpha), (w - 1 - i, 0), (w - 1 - i, h))
        result.blit(vignette, (0, 0))

        return result

    def set_fonts(self, fonts: dict):
        """폰트 설정"""
        self.fonts = fonts

    def update(self, dt: float):
        """업데이트"""
        if not self.is_alive:
            return

        self.phase_timer += dt

        if self.phase == self.PHASE_FADEIN:
            progress = min(self.phase_timer / self.fadein_duration, 1.0)
            self.fade_alpha = progress

            if progress >= 1.0:
                self.phase = self.PHASE_PHOTOS
                self.phase_timer = 0.0
                self.photo_timer = 0.0

        elif self.phase == self.PHASE_PHOTOS:
            # 사진 순차 등장 (한 사진이 완전히 등장한 후 대화 표시 + 인터벌 대기)
            self.photo_timer += dt

            # 현재 사진이 완전히 등장했는지 확인
            current_photo_complete = False
            if self.visible_count > 0 and self.visible_count <= len(self.polaroids):
                current_p = self.polaroids[self.visible_count - 1]
                current_photo_complete = current_p['animation_progress'] >= 1.0

            # 폴라로이드 등장 시 해당 대화 자동 표시
            if current_photo_complete and not self.current_photo_dialogue_shown:
                photo_index = self.visible_count - 1
                if photo_index < len(self.dialogue_per_photo):
                    # 해당 폴라로이드의 대화 시작
                    self.dialogue_text = ""
                    self.typing_progress = 0.0
                    self.current_photo_dialogue_shown = True
                    self.photo_timer = 0.0  # 대화 표시 시작 시점부터 타이머

            # 대화 타이핑 효과 (PHASE_PHOTOS 중에도)
            if self.current_photo_dialogue_shown and self.visible_count > 0:
                photo_index = self.visible_count - 1
                if photo_index < len(self.dialogue_per_photo):
                    self.typing_progress += self.typing_speed * dt
                    char_count = int(self.typing_progress)
                    full_text = self.dialogue_per_photo[photo_index].get("text", "")
                    if char_count >= len(full_text):
                        self.dialogue_text = full_text
                    else:
                        self.dialogue_text = full_text[:char_count]

            # 다음 사진 등장 조건: 현재 사진 완료 + 대화 표시 완료 + 인터벌 경과
            if self.visible_count == 0:
                # 첫 번째 사진은 바로 시작
                if self.sound_manager:
                    self.sound_manager.play_sfx("sfx_polaroid")
                self.visible_count = 1
                self.photo_timer = 0.0
                self.current_photo_dialogue_shown = False
            elif current_photo_complete and self.visible_count < len(self.polaroids):
                # 현재 사진 완료 + 대화 읽을 시간 후 다음 사진
                if self.photo_timer >= self.photo_interval:
                    if self.sound_manager:
                        self.sound_manager.play_sfx("sfx_polaroid")
                    self.visible_count += 1
                    self.photo_timer = 0.0  # 타이머 리셋
                    self.current_photo_dialogue_shown = False  # 다음 대화 준비
                    self.dialogue_text = ""  # 대화 초기화

            # 사진 애니메이션 업데이트 (2배 확대 → 잠시 유지 → 원래 크기로 축소)
            for i, p in enumerate(self.polaroids):
                if i < self.visible_count:
                    # 애니메이션 진행도 업데이트
                    p['animation_progress'] = min(p['animation_progress'] + self.photo_animation_speed * dt, 1.0)
                    progress = p['animation_progress']

                    # 3단계 애니메이션: 등장(0~0.3) → 확대 유지(0.3~0.6) → 축소(0.6~1.0)
                    if progress < 0.3:
                        # 1단계: 등장 (외부에서 날아오며 2배 크기로)
                        phase_progress = progress / 0.3
                        eased = 1 - pow(1 - phase_progress, 3)  # ease-out-cubic

                        # 위치 보간 (시작 → 목표)
                        start_x, start_y = p['start_pos']
                        target_x, target_y = p['target_pos']
                        p['pos'][0] = start_x + (target_x - start_x) * eased
                        p['pos'][1] = start_y + (target_y - start_y) * eased

                        # 알파 증가
                        p['alpha'] = min(int(255 * eased), p['target_alpha'])

                        # 스케일: 0.5 → 2.0 (등장하면서 2배로 확대)
                        p['scale'] = 0.5 + 1.5 * eased

                    elif progress < 0.6:
                        # 2단계: 확대 상태 유지 (2배 크기로 잠시 보여줌)
                        p['pos'][0], p['pos'][1] = p['target_pos']
                        p['alpha'] = 255
                        p['scale'] = 2.0

                    else:
                        # 3단계: 원래 크기로 축소 (2.0 → 1.0)
                        phase_progress = (progress - 0.6) / 0.4
                        eased = 1 - pow(1 - phase_progress, 2)  # ease-out-quad

                        p['pos'][0], p['pos'][1] = p['target_pos']
                        p['alpha'] = 255
                        # 스케일: 2.0 → 1.0
                        p['scale'] = 2.0 - 1.0 * eased

                    # 점멸 효과 (flicker 또는 flicker_then_zoom) - 축소 완료 후에만 적용
                    if p.get('effect_type') in ['flicker', 'flicker_then_zoom'] and p['animation_progress'] >= 0.95:
                        p['flicker_phase'] += dt * (1.0 / p.get('flicker_speed', 0.3))
                        # 느린 점멸 (사인파로 부드럽게)
                        flicker_val = 0.5 + 0.5 * math.sin(p['flicker_phase'] * math.pi)
                        p['alpha'] = int(150 + 105 * flicker_val)  # 150~255 사이

            # 모든 사진 등장 완료
            if self.visible_count >= len(self.polaroids):
                all_complete = all(p['animation_progress'] >= 0.98 for p in self.polaroids)
                if all_complete:
                    # 최종 위치로 고정
                    for p in self.polaroids:
                        p['pos'][0], p['pos'][1] = p['target_pos']
                        # 점멸 효과 (flicker 또는 flicker_then_zoom)는 알파 유지
                        if p.get('effect_type') not in ['flicker', 'flicker_then_zoom']:
                            p['alpha'] = 255
                        p['scale'] = 1.0
                    self.phase = self.PHASE_DISPLAY
                    self.phase_timer = 0.0

        elif self.phase == self.PHASE_DISPLAY:
            # 점멸 효과 업데이트 (DISPLAY 중에도 계속) - flicker_then_zoom도 포함
            for p in self.polaroids:
                if p.get('effect_type') in ['flicker', 'flicker_then_zoom']:
                    p['flicker_phase'] += dt * (1.0 / p.get('flicker_speed', 0.3))
                    flicker_val = 0.5 + 0.5 * math.sin(p['flicker_phase'] * math.pi)
                    p['alpha'] = int(150 + 105 * flicker_val)

            # 잠시 표시
            if self.phase_timer >= self.display_duration:
                # 확대 효과가 적용될 사진이 있으면 FINAL_ZOOM으로 전환
                if len(self.zoom_photo_indices) > 0:
                    self.current_zoom_index = 0
                    self.final_photo_index = self.zoom_photo_indices[0]
                    self.phase = self.PHASE_FINAL_ZOOM
                    self.phase_timer = 0.0
                    self.final_zoom_scale = 1.0
                    self.final_zoom_alpha = 255
                elif self.dialogue_after:
                    self.phase = self.PHASE_DIALOGUE
                    self.phase_timer = 0.0
                    self._prepare_dialogue(0)
                else:
                    self.phase = self.PHASE_FADEOUT
                    self.phase_timer = 0.0

        elif self.phase == self.PHASE_FINAL_ZOOM:
            # 사진 화면 전체로 확대 후 페이드아웃 (여러 사진 순차 처리)
            progress = min(self.phase_timer / self.final_zoom_duration, 1.0)

            # 이징 (ease-in-out)
            if progress < 0.5:
                eased = 2 * progress * progress
            else:
                eased = 1 - pow(-2 * progress + 2, 2) / 2

            # 확대 배율 (1.0 → 화면 가득)
            # 목표 배율: 화면 크기 / 사진 크기 * 약간의 여유
            target_scale = max(self.screen_size[0], self.screen_size[1]) / 260 * 1.2
            self.final_zoom_scale = 1.0 + (target_scale - 1.0) * eased

            # 후반부에 페이드아웃 시작
            if progress > 0.6:
                fade_progress = (progress - 0.6) / 0.4
                self.final_zoom_alpha = int(255 * (1.0 - fade_progress))

            if progress >= 1.0:
                # 다음 확대 사진이 있는지 확인
                self.current_zoom_index += 1
                if self.current_zoom_index < len(self.zoom_photo_indices):
                    # 다음 사진 확대 시작
                    self.final_photo_index = self.zoom_photo_indices[self.current_zoom_index]
                    self.phase_timer = 0.0
                    self.final_zoom_scale = 1.0
                    self.final_zoom_alpha = 255
                else:
                    # 모든 확대 완료 → 대사 또는 페이드아웃
                    if self.dialogue_after:
                        self.phase = self.PHASE_DIALOGUE
                        self.phase_timer = 0.0
                        self._prepare_dialogue(0)
                    else:
                        self.phase = self.PHASE_FADEOUT
                        self.phase_timer = 0.0

        elif self.phase == self.PHASE_DIALOGUE:
            # 타이핑 효과
            if not self.waiting_for_click:
                self.typing_progress += self.typing_speed * dt
                char_count = int(self.typing_progress)
                full_text = self.dialogue_after[self.current_dialogue_index].get("text", "")

                if char_count >= len(full_text):
                    self.dialogue_text = full_text
                    self.waiting_for_click = True
                else:
                    self.dialogue_text = full_text[:char_count]

        elif self.phase == self.PHASE_FADEOUT:
            progress = min(self.phase_timer / self.fadeout_duration, 1.0)
            self.fade_alpha = 1.0 - progress

            # 사진 페이드아웃
            for p in self.polaroids:
                p['alpha'] = max(0, int(255 * (1.0 - progress)))

            if progress >= 1.0:
                self.phase = self.PHASE_DONE
                self.is_alive = False
                if self.on_complete:
                    self.on_complete()

    def _get_portrait(self, speaker: str) -> pygame.Surface:
        """초상화 이미지 가져오기 (캐시 사용)"""
        if speaker in self.portrait_cache:
            return self.portrait_cache[speaker]

        # config_story_dialogue에서 경로 가져오기
        try:
            from mode_configs.config_story_dialogue import CHARACTER_PORTRAITS
            path = CHARACTER_PORTRAITS.get(speaker)
        except ImportError:
            # 폴백: 기본 경로
            portrait_paths = {
                "ARTEMIS": "assets/story_mode/portraits/portrait_artemis.jpg",
                "PILOT": "assets/story_mode/portraits/portrait_pilot.png",
            }
            path = portrait_paths.get(speaker)

        if path:
            try:
                img = pygame.image.load(path).convert_alpha()
                # 크기 조정 (150x150 정도)
                target_size = (150, 150)
                img = pygame.transform.smoothscale(img, target_size)
                self.portrait_cache[speaker] = img
                return img
            except Exception as e:
                print(f"WARNING: Failed to load portrait for {speaker}: {e}")

        return None

    def _prepare_dialogue(self, index: int):
        """대사 준비"""
        if 0 <= index < len(self.dialogue_after):
            self.dialogue_text = ""
            self.typing_progress = 0.0
            self.waiting_for_click = False

    def handle_click(self):
        """클릭 처리 - 폴라로이드 등장 중에는 클릭 무시 (자동 진행)"""
        if self.phase == self.PHASE_FADEIN:
            # 페이드인 중 클릭 시 스킵
            self.phase = self.PHASE_PHOTOS
            self.phase_timer = 0.0
            self.fade_alpha = 1.0
            return

        if self.phase == self.PHASE_PHOTOS:
            # 폴라로이드 등장 중에는 클릭 무시 (자동 진행만 허용)
            # 클릭으로 즉시 등장하는 기능 삭제
            return

        if self.phase == self.PHASE_DISPLAY:
            # 최종 사진 확대 효과가 있으면 FINAL_ZOOM으로 전환
            if self.final_photo_index >= 0:
                self.phase = self.PHASE_FINAL_ZOOM
                self.phase_timer = 0.0
                self.final_zoom_scale = 1.0
                self.final_zoom_alpha = 255
            elif self.dialogue_after:
                self.phase = self.PHASE_DIALOGUE
                self.phase_timer = 0.0
                self._prepare_dialogue(0)
            else:
                self.phase = self.PHASE_FADEOUT
                self.phase_timer = 0.0
            return

        if self.phase == self.PHASE_FINAL_ZOOM:
            # 최종 확대 스킵 → 대사 또는 페이드아웃
            if self.dialogue_after:
                self.phase = self.PHASE_DIALOGUE
                self.phase_timer = 0.0
                self._prepare_dialogue(0)
            else:
                self.phase = self.PHASE_FADEOUT
                self.phase_timer = 0.0
            return

        if self.phase == self.PHASE_DIALOGUE:
            # 리플레이 버튼 클릭 체크 (마지막 대사일 때)
            is_last_dialogue = self.current_dialogue_index >= len(self.dialogue_after) - 1
            if is_last_dialogue and self.waiting_for_click and self.replay_button_rect:
                mouse_pos = pygame.mouse.get_pos()
                if self.replay_button_rect.collidepoint(mouse_pos):
                    # 리플레이 요청
                    self._request_replay()
                    return

            if not self.waiting_for_click:
                # 타이핑 스킵
                full_text = self.dialogue_after[self.current_dialogue_index].get("text", "")
                self.dialogue_text = full_text
                self.waiting_for_click = True
            else:
                # 다음 대사 또는 완료
                self.current_dialogue_index += 1
                if self.current_dialogue_index >= len(self.dialogue_after):
                    self.phase = self.PHASE_FADEOUT
                    self.phase_timer = 0.0
                else:
                    self._prepare_dialogue(self.current_dialogue_index)

    def _request_replay(self):
        """리플레이 요청 - 회상 장면 재시작"""
        print(f"INFO: Replay requested for {self.scene_id}")

        # 콜백이 있으면 호출 (story_mode에서 새 인스턴스 생성)
        if self.on_replay_request:
            self.on_replay_request(self.scene_id)
        else:
            # 콜백 없으면 자체 리셋
            self._reset_for_replay()

    def _reset_for_replay(self):
        """리플레이를 위한 내부 상태 리셋"""
        # 페이즈 리셋
        self.phase = self.PHASE_FADEIN
        self.phase_timer = 0.0
        self.fade_alpha = 0.0

        # 사진 상태 리셋
        self.visible_count = 0
        self.photo_timer = 0.0

        # 폴라로이드 애니메이션 상태 리셋
        for p in self.polaroids:
            p['animation_progress'] = 0.0
            p['pos'][0], p['pos'][1] = p['start_pos']
            p['alpha'] = 0
            p['scale'] = 0.5
            p['flicker_phase'] = 0.0

        # 줌 효과 리셋
        self.final_zoom_scale = 1.0
        self.final_zoom_alpha = 255
        self.current_zoom_index = 0
        self.final_photo_index = -1

        # 대사 상태 리셋
        self.current_dialogue_index = 0
        self.dialogue_text = ""
        self.typing_progress = 0.0
        self.waiting_for_click = False
        self.current_photo_dialogue_shown = False

        # 리플레이 버튼 상태 리셋
        self.replay_button_alpha = 0.0

        print(f"INFO: {self.scene_id} reset for replay")

    def skip(self):
        """전체 스킵"""
        self.phase = self.PHASE_FADEOUT
        self.phase_timer = 0.0

    def draw(self, screen: pygame.Surface):
        """렌더링"""
        if not self.is_alive and self.phase == self.PHASE_DONE:
            return

        # 배경
        if self.background:
            bg_copy = self.background.copy()
            bg_copy.set_alpha(int(255 * self.fade_alpha))
            screen.blit(bg_copy, (0, 0))
        else:
            screen.fill((30, 30, 40))

        # 어두운 오버레이
        overlay = pygame.Surface(self.screen_size, pygame.SRCALPHA)
        overlay.fill((0, 0, 0, int(150 * self.fade_alpha)))
        screen.blit(overlay, (0, 0))

        # FINAL_ZOOM 단계에서는 최종 사진만 확대 렌더링
        if self.phase == self.PHASE_FINAL_ZOOM and self.final_photo_index >= 0:
            final_p = self.polaroids[self.final_photo_index]
            # 원본 사진 이미지 사용 (프레임 없이)
            photo_img = final_p.get('photo_image')
            if photo_img:
                # 확대 적용
                zoom_w = int(photo_img.get_width() * self.final_zoom_scale)
                zoom_h = int(photo_img.get_height() * self.final_zoom_scale)
                if zoom_w > 0 and zoom_h > 0:
                    zoomed = pygame.transform.smoothscale(photo_img, (zoom_w, zoom_h))
                    zoomed.set_alpha(self.final_zoom_alpha)
                    # 화면 중앙에 배치
                    rect = zoomed.get_rect(center=(self.screen_size[0] // 2, self.screen_size[1] // 2))
                    screen.blit(zoomed, rect)
            return  # FINAL_ZOOM에서는 다른 사진 렌더링 안함

        # 폴라로이드 사진들
        for i, p in enumerate(self.polaroids):
            if i >= self.visible_count and self.phase == self.PHASE_PHOTOS:
                continue
            if p['alpha'] <= 0:
                continue

            # 스케일 적용
            scaled_w = int(p['image'].get_width() * p['scale'])
            scaled_h = int(p['image'].get_height() * p['scale'])
            if scaled_w > 0 and scaled_h > 0:
                scaled = pygame.transform.smoothscale(p['image'], (scaled_w, scaled_h))
                scaled.set_alpha(int(p['alpha']))

                rect = scaled.get_rect(center=p['pos'])
                screen.blit(scaled, rect)

        # 대사 (하단) - PHASE_PHOTOS에서도 폴라로이드별 대화 표시
        if self.phase == self.PHASE_PHOTOS and self.dialogue_text and self.current_photo_dialogue_shown:
            # 폴라로이드별 대화 표시
            self._draw_photo_dialogue(screen)
        elif self.phase in [self.PHASE_DIALOGUE, self.PHASE_DISPLAY] and self.dialogue_text:
            self._draw_dialogue(screen)

        # 클릭 힌트 (PHASE_PHOTOS에서는 표시 안함 - 자동 진행)
        if self.phase in [self.PHASE_DISPLAY, self.PHASE_DIALOGUE] and self.waiting_for_click:
            self._draw_click_hint(screen)

    def _draw_dialogue(self, screen: pygame.Surface):
        """대사 그리기 - 초상화 포함"""
        font = self.fonts.get("medium") or self.fonts.get("small")
        small_font = self.fonts.get("small") or font
        if not font:
            return

        # 현재 대사 정보 가져오기
        if self.current_dialogue_index >= len(self.dialogue_after):
            return

        current_dialogue = self.dialogue_after[self.current_dialogue_index]
        speaker = current_dialogue.get("speaker", "")

        # config_story_dialogue에서 색상/이름 가져오기
        try:
            from mode_configs.config_story_dialogue import CHARACTER_COLORS, CHARACTER_NAMES
            text_color = CHARACTER_COLORS.get(speaker, (255, 255, 255))
            speaker_name = CHARACTER_NAMES.get(speaker, speaker)
        except ImportError:
            text_color = (255, 220, 150)
            speaker_name = speaker

        # 초상화 가져오기
        portrait = self._get_portrait(speaker)
        portrait_width = 150 if portrait else 0

        # 대사 박스 (가로 1/2 크기, 중앙 정렬)
        box_height = 120
        box_width = (self.screen_size[0] - 160) // 2
        box_x = (self.screen_size[0] - box_width) // 2
        box_rect = pygame.Rect(
            box_x,
            self.screen_size[1] - box_height - 40,
            box_width,
            box_height
        )

        # 박스 배경
        box_surf = pygame.Surface((box_rect.width, box_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(box_surf, (0, 0, 0, 200), (0, 0, box_rect.width, box_rect.height), border_radius=12)
        pygame.draw.rect(box_surf, text_color + (100,), (0, 0, box_rect.width, box_rect.height), 2, border_radius=12)
        screen.blit(box_surf, box_rect.topleft)

        # 초상화 그리기
        text_left_x = box_rect.left + 25
        if portrait:
            portrait_x = box_rect.left + 15
            portrait_y = box_rect.top + (box_height - portrait_width) // 2
            # 초상화 배경 (원형)
            pygame.draw.circle(screen, (30, 30, 40),
                             (portrait_x + portrait_width // 2, portrait_y + portrait_width // 2),
                             portrait_width // 2 + 5)
            pygame.draw.circle(screen, text_color,
                             (portrait_x + portrait_width // 2, portrait_y + portrait_width // 2),
                             portrait_width // 2 + 5, 2)
            # 초상화 마스킹 (원형)
            mask_surf = pygame.Surface((portrait_width, portrait_width), pygame.SRCALPHA)
            pygame.draw.circle(mask_surf, (255, 255, 255, 255),
                             (portrait_width // 2, portrait_width // 2), portrait_width // 2)
            portrait_copy = portrait.copy()
            portrait_copy.blit(mask_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
            screen.blit(portrait_copy, (portrait_x, portrait_y))
            text_left_x = portrait_x + portrait_width + 20

        # 화자 이름
        if speaker_name:
            name_surf = small_font.render(speaker_name, True, text_color)
            screen.blit(name_surf, (text_left_x, box_rect.top + 15))

        # 대사 텍스트 (여러 줄 처리)
        text_y = box_rect.top + 45
        max_width = box_rect.right - text_left_x - 30
        words = self.dialogue_text.split()
        lines = []
        current_line = ""

        for word in words:
            test_line = current_line + (" " if current_line else "") + word
            if small_font.size(test_line)[0] <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)

        # 텍스트 그리기
        for i, line in enumerate(lines):
            text_surf = small_font.render(line, True, (255, 255, 255))
            screen.blit(text_surf, (text_left_x, text_y + i * 26))

        # 리플레이 버튼 (마지막 대사이고 클릭 대기 중일 때)
        is_last_dialogue = self.current_dialogue_index >= len(self.dialogue_after) - 1
        if is_last_dialogue and self.waiting_for_click:
            self._draw_replay_button(screen, box_rect)

    def _draw_replay_button(self, screen: pygame.Surface, dialogue_box_rect: pygame.Rect):
        """리플레이 버튼 그리기 - 대화 상자 내부 우측 하단"""
        font = self.fonts.get("small")
        if not font:
            return

        # 버튼 알파 페이드 인
        self.replay_button_alpha = min(1.0, self.replay_button_alpha + 0.05)

        # 버튼 크기 및 위치 (대화 상자 내부 우측 하단)
        button_text = "REPLAY"
        button_padding_x = 16
        button_padding_y = 8
        text_surf = font.render(button_text, True, (255, 255, 255))
        button_width = text_surf.get_width() + button_padding_x * 2
        button_height = text_surf.get_height() + button_padding_y * 2

        button_x = dialogue_box_rect.right - button_width - 15
        button_y = dialogue_box_rect.bottom - button_height - 10

        self.replay_button_rect = pygame.Rect(button_x, button_y, button_width, button_height)

        # 호버 체크
        mouse_pos = pygame.mouse.get_pos()
        self.replay_button_hover = self.replay_button_rect.collidepoint(mouse_pos)

        # 버튼 색상 (호버 시 더 밝게)
        if self.replay_button_hover:
            bg_color = (80, 120, 180, int(220 * self.replay_button_alpha))
            border_color = (150, 200, 255, int(255 * self.replay_button_alpha))
            text_color = (255, 255, 255)
        else:
            bg_color = (50, 70, 100, int(180 * self.replay_button_alpha))
            border_color = (100, 150, 200, int(200 * self.replay_button_alpha))
            text_color = (200, 220, 255)

        # 버튼 배경
        button_surf = pygame.Surface((button_width, button_height), pygame.SRCALPHA)
        pygame.draw.rect(button_surf, bg_color, (0, 0, button_width, button_height), border_radius=6)
        pygame.draw.rect(button_surf, border_color, (0, 0, button_width, button_height), 2, border_radius=6)

        # 아이콘 (재생 삼각형) + 텍스트
        icon_size = 10
        icon_x = button_padding_x - 2
        icon_y = button_height // 2

        # 재생 아이콘 (삼각형)
        icon_points = [
            (icon_x, icon_y - icon_size // 2),
            (icon_x, icon_y + icon_size // 2),
            (icon_x + icon_size, icon_y)
        ]
        pygame.draw.polygon(button_surf, text_color, icon_points)

        # 텍스트
        text_surf = font.render(button_text, True, text_color)
        text_x = icon_x + icon_size + 6
        text_y = (button_height - text_surf.get_height()) // 2
        button_surf.blit(text_surf, (text_x, text_y))

        screen.blit(button_surf, (button_x, button_y))

    def _draw_photo_dialogue(self, screen: pygame.Surface):
        """폴라로이드별 대화 그리기 (PHASE_PHOTOS 중 자동 표시)"""
        font = self.fonts.get("medium") or self.fonts.get("small")
        small_font = self.fonts.get("small") or font
        if not font:
            return

        # 현재 폴라로이드 인덱스에 해당하는 대화 가져오기
        photo_index = self.visible_count - 1
        if photo_index < 0 or photo_index >= len(self.dialogue_per_photo):
            return

        current_dialogue = self.dialogue_per_photo[photo_index]
        speaker = current_dialogue.get("speaker", "")

        # config_story_dialogue에서 색상/이름 가져오기
        try:
            from mode_configs.config_story_dialogue import CHARACTER_COLORS, CHARACTER_NAMES
            text_color = CHARACTER_COLORS.get(speaker, (255, 255, 255))
            speaker_name = CHARACTER_NAMES.get(speaker, speaker)
        except ImportError:
            text_color = (255, 220, 150)
            speaker_name = speaker

        # 초상화 가져오기
        portrait = self._get_portrait(speaker)
        portrait_width = 150 if portrait else 0

        # 대사 박스 (하단, 가로 1/2 크기, 중앙 정렬)
        box_height = 120
        box_width = (self.screen_size[0] - 160) // 2
        box_x = (self.screen_size[0] - box_width) // 2
        box_rect = pygame.Rect(
            box_x,
            self.screen_size[1] - box_height - 40,
            box_width,
            box_height
        )

        # 박스 배경
        box_surf = pygame.Surface((box_rect.width, box_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(box_surf, (0, 0, 0, 200), (0, 0, box_rect.width, box_rect.height), border_radius=12)
        pygame.draw.rect(box_surf, text_color + (100,), (0, 0, box_rect.width, box_rect.height), 2, border_radius=12)
        screen.blit(box_surf, box_rect.topleft)

        # 초상화 그리기
        text_left_x = box_rect.left + 25
        if portrait:
            portrait_x = box_rect.left + 15
            portrait_y = box_rect.top + (box_height - portrait_width) // 2
            # 초상화 배경 (원형)
            pygame.draw.circle(screen, (30, 30, 40),
                             (portrait_x + portrait_width // 2, portrait_y + portrait_width // 2),
                             portrait_width // 2 + 5)
            pygame.draw.circle(screen, text_color,
                             (portrait_x + portrait_width // 2, portrait_y + portrait_width // 2),
                             portrait_width // 2 + 5, 2)
            screen.blit(portrait, (portrait_x, portrait_y))
            text_left_x = portrait_x + portrait_width + 20

        # 화자 이름
        if speaker_name:
            name_surf = font.render(speaker_name, True, text_color)
            screen.blit(name_surf, (text_left_x, box_rect.top + 12))

        # 대사 텍스트 (자동 줄바꿈)
        text_y = box_rect.top + 45
        max_width = box_rect.width - (text_left_x - box_rect.left) - 30

        # 줄바꿈 처리
        words = self.dialogue_text.split(' ')
        lines = []
        current_line = ""
        for word in words:
            test_line = current_line + (" " if current_line else "") + word
            test_surf = small_font.render(test_line, True, (255, 255, 255))
            if test_surf.get_width() <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)

        # 텍스트 그리기
        for i, line in enumerate(lines):
            text_surf = small_font.render(line, True, (255, 255, 255))
            screen.blit(text_surf, (text_left_x, text_y + i * 26))

    def _draw_click_hint(self, screen: pygame.Surface):
        """클릭 힌트 그리기"""
        font = self.fonts.get("small")
        if not font:
            return

        alpha = int(128 + 127 * math.sin(pygame.time.get_ticks() / 300))
        hint_surf = font.render("Click to continue...", True, (200, 200, 200))
        hint_surf.set_alpha(alpha)
        hint_rect = hint_surf.get_rect(midbottom=(self.screen_size[0] // 2, self.screen_size[1] - 20))
        screen.blit(hint_surf, hint_rect)


# =========================================================
# 비행선 진입 & 선회 애니메이션 (1막 오프닝)
# =========================================================
class ShipEntranceEffect:
    """
    비행선 진입 효과 - 화면 상단에서 진입 후 폐허 주변 선회

    연출:
    1. 비행선이 화면 상단 밖에서 진입
    2. 화면 중앙의 폐허 건물 주변을 천천히 타원형으로 선회
    3. 선회 중 대화 진행
    4. 대화 완료 후 비행선이 전투 위치(화면 하단)로 이동
    """

    PHASE_ENTRANCE = 0      # 화면 진입
    PHASE_CIRCLING = 1      # 폐허 주변 선회 + 대화
    PHASE_POSITIONING = 2   # 전투 위치로 이동
    PHASE_DONE = 3          # 완료

    def __init__(self, screen_size: tuple, player, dialogue_data: list,
                 background_path: str = None, title: str = "", location: str = ""):
        """
        Args:
            screen_size: 화면 크기 (width, height)
            player: Player 객체 (위치 제어용)
            dialogue_data: 대사 리스트 [{"speaker": "...", "text": "..."}, ...]
            background_path: 배경 이미지 경로
            title: 타이틀 텍스트
            location: 위치 텍스트
        """
        self.screen_size = screen_size
        self.player = player
        self.dialogue_data = dialogue_data
        self.title = title
        self.location = location

        self.is_alive = True
        self.phase = self.PHASE_ENTRANCE
        self.phase_timer = 0.0

        # 진입 애니메이션
        self.entrance_duration = 2.5  # 진입 시간 (초)
        self.start_pos = (screen_size[0] // 2, -100)  # 화면 상단 밖
        self.entrance_end_pos = (screen_size[0] // 2, screen_size[1] // 3)  # 선회 시작 위치

        # 선회 애니메이션
        self.orbit_center = (screen_size[0] // 2, screen_size[1] // 2 - 50)  # 폐허 중심
        self.orbit_radius_x = screen_size[0] // 4  # 타원 가로 반경
        self.orbit_radius_y = screen_size[1] // 6  # 타원 세로 반경
        self.orbit_speed = 0.3  # 선회 속도 (라디안/초)
        self.orbit_angle = -math.pi / 2  # 시작 각도 (상단에서 시작)

        # 전투 위치
        self.battle_pos = (screen_size[0] // 2, int(screen_size[1] * 0.7))
        self.positioning_duration = 1.5

        # 대사 관련
        self.current_dialogue_index = 0
        self.typing_progress = 0.0
        self.typing_speed = 25.0  # 초당 글자 수
        self.current_text = ""
        self.full_text = ""
        self.waiting_for_click = False
        self.dialogue_started = False  # 선회 시작 후 대화 시작
        self.dialogue_start_delay = 1.0  # 선회 시작 후 대화 시작까지 딜레이
        self.dialogue_timer = 0.0

        # 배경 로드
        self.background = None
        if background_path:
            self._load_background(background_path)

        # 초상화 캐시
        self.portrait_cache = {}

        # 캐릭터 색상
        self.character_colors = {
            "ARTEMIS": (255, 220, 150),
            "PILOT": (150, 200, 255),
            "BOSS": (255, 100, 100),
            "NARRATOR": (200, 200, 200),
            "SYSTEM": (100, 255, 200),
        }

        # 폰트
        self.fonts = {}

        # 콜백
        self.on_complete = None

        # 플레이어 원래 이미지/위치 저장
        if player:
            self.original_player_pos = player.pos.copy()
            player.pos = pygame.math.Vector2(self.start_pos)

        # 첫 대사 준비
        if self.dialogue_data:
            self._prepare_dialogue(0)

        print("INFO: ShipEntranceEffect initialized")

    def _load_background(self, path: str):
        """배경 이미지 로드"""
        try:
            img = pygame.image.load(path).convert()
            self.background = pygame.transform.scale(img, self.screen_size)
        except Exception as e:
            print(f"WARNING: Failed to load background: {path} - {e}")

    def _prepare_dialogue(self, index: int):
        """대사 준비"""
        if 0 <= index < len(self.dialogue_data):
            dialogue = self.dialogue_data[index]
            self.full_text = dialogue.get("text", "")
            self.current_text = ""
            self.typing_progress = 0.0
            self.waiting_for_click = False

    def _get_portrait(self, speaker: str) -> pygame.Surface:
        """초상화 이미지 가져오기"""
        if speaker in self.portrait_cache:
            return self.portrait_cache[speaker]

        try:
            from mode_configs.config_story_dialogue import CHARACTER_PORTRAITS
            path = CHARACTER_PORTRAITS.get(speaker)
        except ImportError:
            portrait_paths = {
                "ARTEMIS": "assets/story_mode/portraits/portrait_artemis.jpg",
                "PILOT": "assets/story_mode/portraits/portrait_pilot.png",
            }
            path = portrait_paths.get(speaker)

        if path:
            try:
                img = pygame.image.load(path).convert_alpha()
                target_size = (180, 180)
                img = pygame.transform.smoothscale(img, target_size)
                self.portrait_cache[speaker] = img
                return img
            except Exception as e:
                print(f"WARNING: Failed to load portrait for {speaker}: {e}")

        return None

    def set_fonts(self, fonts: dict):
        """폰트 설정"""
        self.fonts = fonts

    def update(self, dt: float):
        """업데이트"""
        if not self.is_alive:
            return

        self.phase_timer += dt

        if self.phase == self.PHASE_ENTRANCE:
            # 화면 진입 애니메이션
            progress = min(self.phase_timer / self.entrance_duration, 1.0)

            # 이징 (ease-out-cubic)
            eased = 1 - pow(1 - progress, 3)

            # 플레이어 위치 보간
            if self.player:
                new_x = self.start_pos[0] + (self.entrance_end_pos[0] - self.start_pos[0]) * eased
                new_y = self.start_pos[1] + (self.entrance_end_pos[1] - self.start_pos[1]) * eased
                self.player.pos = pygame.math.Vector2(new_x, new_y)

            if progress >= 1.0:
                self.phase = self.PHASE_CIRCLING
                self.phase_timer = 0.0
                self.dialogue_timer = 0.0
                print("INFO: Ship entrance complete, starting circling")

        elif self.phase == self.PHASE_CIRCLING:
            # 선회 애니메이션
            self.orbit_angle += self.orbit_speed * dt

            # 타원 궤도 계산
            orbit_x = self.orbit_center[0] + math.cos(self.orbit_angle) * self.orbit_radius_x
            orbit_y = self.orbit_center[1] + math.sin(self.orbit_angle) * self.orbit_radius_y

            if self.player:
                self.player.pos = pygame.math.Vector2(orbit_x, orbit_y)

            # 대화 시작 딜레이
            self.dialogue_timer += dt
            if not self.dialogue_started and self.dialogue_timer >= self.dialogue_start_delay:
                self.dialogue_started = True

            # 대화 진행
            if self.dialogue_started and self.dialogue_data:
                self._update_dialogue(dt)

        elif self.phase == self.PHASE_POSITIONING:
            # 전투 위치로 이동
            progress = min(self.phase_timer / self.positioning_duration, 1.0)

            # 이징 (ease-in-out-cubic)
            if progress < 0.5:
                eased = 4 * progress * progress * progress
            else:
                eased = 1 - pow(-2 * progress + 2, 3) / 2

            if self.player:
                # 현재 선회 위치에서 전투 위치로
                start_x = self.orbit_center[0] + math.cos(self.orbit_angle) * self.orbit_radius_x
                start_y = self.orbit_center[1] + math.sin(self.orbit_angle) * self.orbit_radius_y

                new_x = start_x + (self.battle_pos[0] - start_x) * eased
                new_y = start_y + (self.battle_pos[1] - start_y) * eased
                self.player.pos = pygame.math.Vector2(new_x, new_y)

            if progress >= 1.0:
                self.phase = self.PHASE_DONE
                self.is_alive = False
                if self.on_complete:
                    self.on_complete()
                print("INFO: ShipEntranceEffect complete")

    def _update_dialogue(self, dt: float):
        """대화 업데이트"""
        if self.current_dialogue_index >= len(self.dialogue_data):
            # 모든 대화 완료 → 전투 위치로 이동
            self.phase = self.PHASE_POSITIONING
            self.phase_timer = 0.0
            return

        if not self.waiting_for_click:
            self.typing_progress += self.typing_speed * dt
            char_count = int(self.typing_progress)

            if char_count >= len(self.full_text):
                self.current_text = self.full_text
                self.waiting_for_click = True
            else:
                self.current_text = self.full_text[:char_count]

    def handle_click(self):
        """클릭 처리"""
        if self.phase == self.PHASE_ENTRANCE:
            # 진입 스킵
            self.phase = self.PHASE_CIRCLING
            self.phase_timer = 0.0
            self.dialogue_timer = 0.0
            if self.player:
                self.player.pos = pygame.math.Vector2(self.entrance_end_pos)
            return

        if self.phase == self.PHASE_CIRCLING and self.dialogue_started:
            if not self.waiting_for_click:
                # 타이핑 스킵
                self.current_text = self.full_text
                self.waiting_for_click = True
            else:
                # 다음 대사
                self.current_dialogue_index += 1
                if self.current_dialogue_index >= len(self.dialogue_data):
                    # 대화 완료
                    self.phase = self.PHASE_POSITIONING
                    self.phase_timer = 0.0
                else:
                    self._prepare_dialogue(self.current_dialogue_index)

    def skip(self):
        """전체 스킵"""
        self.phase = self.PHASE_POSITIONING
        self.phase_timer = 0.0
        if self.player:
            self.player.pos = pygame.math.Vector2(self.battle_pos)

    def draw(self, screen: pygame.Surface):
        """렌더링"""
        if not self.is_alive and self.phase == self.PHASE_DONE:
            return

        # 배경
        if self.background:
            screen.blit(self.background, (0, 0))
        else:
            screen.fill((20, 20, 30))

        # 반투명 오버레이 (분위기)
        overlay = pygame.Surface(self.screen_size, pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 100))
        screen.blit(overlay, (0, 0))

        # 플레이어 그리기
        if self.player:
            # 플레이어 이미지 그리기
            player_rect = self.player.image.get_rect(center=(int(self.player.pos.x), int(self.player.pos.y)))
            screen.blit(self.player.image, player_rect)

        # 타이틀/위치 (진입 중에만)
        if self.phase == self.PHASE_ENTRANCE:
            self._draw_title(screen)

        # 대화 박스 (선회 중 대화 시작 후)
        if self.phase == self.PHASE_CIRCLING and self.dialogue_started and self.dialogue_data:
            if self.current_dialogue_index < len(self.dialogue_data):
                self._draw_dialogue_box(screen)

        # 클릭 힌트
        if self.waiting_for_click:
            self._draw_click_hint(screen)

    def _draw_title(self, screen: pygame.Surface):
        """타이틀 그리기"""
        if not self.title:
            return

        font = self.fonts.get("large") or self.fonts.get("medium")
        if not font:
            return

        # 페이드 인 효과
        alpha = min(int(255 * self.phase_timer / 1.0), 255)

        title_surf = font.render(self.title, True, (255, 200, 100))
        title_surf.set_alpha(alpha)
        title_rect = title_surf.get_rect(center=(self.screen_size[0] // 2, self.screen_size[1] // 6))
        screen.blit(title_surf, title_rect)

        if self.location:
            loc_font = self.fonts.get("medium") or self.fonts.get("small")
            if loc_font:
                loc_surf = loc_font.render(self.location, True, (200, 200, 200))
                loc_surf.set_alpha(alpha)
                loc_rect = loc_surf.get_rect(center=(self.screen_size[0] // 2, self.screen_size[1] // 6 + 40))
                screen.blit(loc_surf, loc_rect)

    def _draw_dialogue_box(self, screen: pygame.Surface):
        """대화 박스 그리기"""
        if not self.dialogue_data or self.current_dialogue_index >= len(self.dialogue_data):
            return

        dialogue = self.dialogue_data[self.current_dialogue_index]
        speaker = dialogue.get("speaker", "")

        # 폰트
        font = self.fonts.get("medium") or self.fonts.get("small")
        if not font:
            return

        # 초상화
        portrait = self._get_portrait(speaker)
        portrait_width = 180 if portrait else 0

        # 대화 박스 영역 (가로 1/2 크기, 중앙 정렬)
        box_margin = 50
        box_height = 140
        box_width = (self.screen_size[0] - box_margin * 2) // 2
        box_x = (self.screen_size[0] - box_width) // 2
        box_y = self.screen_size[1] - box_height - box_margin

        # 박스 배경
        box_surf = pygame.Surface((box_width, box_height), pygame.SRCALPHA)
        pygame.draw.rect(box_surf, (0, 0, 0, 200), (0, 0, box_width, box_height), border_radius=15)
        pygame.draw.rect(box_surf, (100, 100, 120), (0, 0, box_width, box_height), width=2, border_radius=15)
        screen.blit(box_surf, (box_x, box_y))

        # 초상화 (좌측)
        if portrait:
            portrait_y = box_y + (box_height - portrait.get_height()) // 2
            screen.blit(portrait, (box_x + 10, portrait_y))

        # 화자 이름
        try:
            from mode_configs.config_story_dialogue import CHARACTER_NAMES
            speaker_name = CHARACTER_NAMES.get(speaker, speaker)
        except ImportError:
            speaker_name = speaker

        name_color = self.character_colors.get(speaker, (255, 255, 255))

        if speaker_name:
            name_surf = font.render(speaker_name, True, name_color)
            name_x = box_x + portrait_width + 30
            name_y = box_y + 15
            screen.blit(name_surf, (name_x, name_y))

        # 대사 텍스트
        text_x = box_x + portrait_width + 30
        text_y = box_y + 50
        text_width = box_width - portrait_width - 60

        # 줄바꿈 처리
        words = self.current_text.split(' ')
        lines = []
        current_line = ""

        for word in words:
            test_line = current_line + word + " "
            if font.size(test_line)[0] <= text_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word + " "
        if current_line:
            lines.append(current_line)

        # 텍스트 렌더링
        for i, line in enumerate(lines[:3]):  # 최대 3줄
            text_surf = font.render(line.strip(), True, (255, 255, 255))
            screen.blit(text_surf, (text_x, text_y + i * 28))

    def _draw_click_hint(self, screen: pygame.Surface):
        """클릭 힌트"""
        font = self.fonts.get("small")
        if not font:
            return

        alpha = int(128 + 127 * math.sin(pygame.time.get_ticks() / 300))
        hint_surf = font.render("Click to continue...", True, (200, 200, 200))
        hint_surf.set_alpha(alpha)
        hint_rect = hint_surf.get_rect(midbottom=(self.screen_size[0] // 2, self.screen_size[1] - 20))
        screen.blit(hint_surf, hint_rect)


# =========================================================
# 시각적 피드백 효과 클래스들
# =========================================================

class DamageFlash:
    """
    플레이어가 피격당했을 때 화면에 빨간색 플래시 효과를 표시하는 클래스.
    데미지 비율에 따라 플래시 강도가 조절됩니다.
    """
    def __init__(self, screen_size: Tuple[int, int]):
        self.screen_size = screen_size
        self.is_active = False
        self.start_time = 0.0
        self.duration = 0.0
        self.max_alpha = 0
        self.flash_surface = pygame.Surface(screen_size, pygame.SRCALPHA)

    def trigger(self, damage_ratio: float):
        """
        데미지 플래시를 트리거합니다.

        Args:
            damage_ratio: 받은 데미지 / 최대 HP 비율 (0.0 ~ 1.0)
        """
        self.is_active = True
        self.start_time = pygame.time.get_ticks() / 1000.0

        # 데미지 비율에 따라 플래시 강도와 지속시간 조절
        self.max_alpha = int(min(180, 60 + damage_ratio * 200))  # 60 ~ 180
        self.duration = 0.15 + damage_ratio * 0.15  # 0.15 ~ 0.3초

    def update(self) -> bool:
        """
        플래시 효과를 업데이트합니다.

        Returns:
            bool: 플래시가 아직 활성 상태인지 여부
        """
        if not self.is_active:
            return False

        current_time = pygame.time.get_ticks() / 1000.0
        elapsed = current_time - self.start_time

        if elapsed >= self.duration:
            self.is_active = False
            return False

        return True

    def render(self, screen: pygame.Surface):
        """플래시 효과를 화면에 렌더링합니다."""
        if not self.is_active:
            return

        current_time = pygame.time.get_ticks() / 1000.0
        elapsed = current_time - self.start_time
        progress = elapsed / self.duration

        # 빠르게 나타났다가 천천히 사라지는 이징
        if progress < 0.2:
            # 빠르게 나타남 (0 ~ 0.2)
            alpha_progress = progress / 0.2
        else:
            # 천천히 사라짐 (0.2 ~ 1.0)
            alpha_progress = 1.0 - ((progress - 0.2) / 0.8)

        # alpha 값을 0-255 범위로 클램핑
        alpha = max(0, min(255, int(self.max_alpha * alpha_progress)))

        self.flash_surface.fill((255, 0, 0, alpha))
        screen.blit(self.flash_surface, (0, 0))


class LevelUpEffect:
    """
    레벨업 시 화면에 표시되는 시각 효과 클래스.
    골드 색상 글로우, 상승 파티클, 레벨 텍스트를 표시합니다.
    """
    def __init__(self, screen_size: Tuple[int, int]):
        self.screen_size = screen_size
        self.is_active = False
        self.start_time = 0.0
        self.duration = 1.5  # 1.5초 지속
        self.level = 0
        self.particles: List[Dict] = []
        self.glow_surface = pygame.Surface(screen_size, pygame.SRCALPHA)
        self.font = None
        self._init_font()

    def _init_font(self):
        """폰트 초기화"""
        try:
            self.font = pygame.font.Font(None, 72)
        except:
            self.font = pygame.font.SysFont("Arial", 72)

    def trigger(self, level: int):
        """
        레벨업 효과를 트리거합니다.

        Args:
            level: 새로운 레벨
        """
        self.is_active = True
        self.start_time = pygame.time.get_ticks() / 1000.0
        self.level = level
        self._create_particles()

    def _create_particles(self):
        """상승 파티클 생성 (30개)"""
        self.particles = []
        for _ in range(30):
            particle = {
                'x': random.randint(0, self.screen_size[0]),
                'y': self.screen_size[1] + random.randint(0, 50),
                'speed': random.uniform(100, 250),
                'size': random.randint(3, 8),
                'alpha': random.randint(150, 255),
                'color': random.choice([
                    (255, 215, 0),   # 골드
                    (255, 200, 50),  # 밝은 골드
                    (255, 180, 0),   # 오렌지 골드
                    (255, 255, 150), # 밝은 노랑
                ])
            }
            self.particles.append(particle)

    def update(self, dt: float) -> bool:
        """
        레벨업 효과를 업데이트합니다.

        Args:
            dt: 델타 타임

        Returns:
            bool: 효과가 아직 활성 상태인지 여부
        """
        if not self.is_active:
            return False

        current_time = pygame.time.get_ticks() / 1000.0
        elapsed = current_time - self.start_time

        if elapsed >= self.duration:
            self.is_active = False
            return False

        # 파티클 업데이트 (위로 상승)
        for particle in self.particles:
            particle['y'] -= particle['speed'] * dt
            # 페이드 아웃
            particle['alpha'] = max(0, particle['alpha'] - 80 * dt)

        return True

    def render(self, screen: pygame.Surface):
        """레벨업 효과를 화면에 렌더링합니다."""
        if not self.is_active:
            return

        current_time = pygame.time.get_ticks() / 1000.0
        elapsed = current_time - self.start_time
        progress = elapsed / self.duration

        # 1. 골드 화면 글로우 (처음에 강하고 점점 사라짐)
        # alpha 값을 0-255 범위로 클램핑
        glow_alpha = max(0, min(255, int(40 * (1.0 - progress))))
        self.glow_surface.fill((255, 215, 0, glow_alpha))
        screen.blit(self.glow_surface, (0, 0))

        # 2. 파티클 렌더링
        for particle in self.particles:
            if particle['alpha'] > 0 and 0 <= particle['y'] <= self.screen_size[1]:
                alpha = int(particle['alpha'])
                color = (*particle['color'][:3], alpha)
                pygame.draw.circle(
                    screen,
                    color,
                    (int(particle['x']), int(particle['y'])),
                    particle['size']
                )

        # 3. "LEVEL X!" 텍스트 (중앙 상단, 페이드 인/아웃)
        if self.font and progress < 0.8:
            text_alpha = 255
            if progress < 0.1:
                text_alpha = int(255 * (progress / 0.1))
            elif progress > 0.6:
                text_alpha = int(255 * (1.0 - (progress - 0.6) / 0.2))

            text = f"LEVEL {self.level}!"
            text_surf = self.font.render(text, True, (255, 215, 0))
            text_surf.set_alpha(text_alpha)

            # 텍스트 위치 (화면 상단 중앙, 약간 아래로 이동하는 애니메이션)
            text_y = int(80 + 30 * progress)
            text_rect = text_surf.get_rect(center=(self.screen_size[0] // 2, text_y))
            screen.blit(text_surf, text_rect)


# =============================================================================
# 2막 벙커 포신 연출 효과
# =============================================================================

class SmokeParticle:
    """포신 발사 후 연기 파티클"""

    def __init__(self, pos: Tuple[float, float]):
        self.pos = pygame.math.Vector2(pos)
        self.velocity = pygame.math.Vector2(
            random.uniform(-30, 30),
            random.uniform(-60, -30)
        )
        self.size = random.uniform(20, 40)
        self.lifetime = random.uniform(1.5, 2.5)
        self.age = 0.0
        self.is_alive = True

    def update(self, dt: float):
        self.age += dt
        if self.age >= self.lifetime:
            self.is_alive = False
            return

        self.pos += self.velocity * dt
        self.velocity *= 0.97  # 감속
        self.size += 20 * dt   # 확산

    def draw(self, screen: pygame.Surface):
        if not self.is_alive:
            return

        progress = self.age / self.lifetime
        alpha = int(60 * (1 - progress))

        surf = pygame.Surface((int(self.size * 2), int(self.size * 2)), pygame.SRCALPHA)
        pygame.draw.circle(surf, (120, 110, 100, alpha),
                          (int(self.size), int(self.size)), int(self.size))
        screen.blit(surf, (int(self.pos.x - self.size), int(self.pos.y - self.size)))


class CannonShell:
    """포신에서 발사되는 포탄"""

    def __init__(self, start_pos: Tuple[float, float], target_pos: Tuple[float, float],
                 screen_size: Tuple[int, int]):
        self.pos = pygame.math.Vector2(start_pos)
        self.start_pos = pygame.math.Vector2(start_pos)
        self.target_pos = pygame.math.Vector2(target_pos)
        self.screen_size = screen_size

        # 포탄 속성
        self.speed = 800  # 픽셀/초
        self.damage = 500  # 높은 데미지
        self.explosion_radius = 120  # 넓은 폭발 범위

        # 방향 계산
        direction = self.target_pos - self.start_pos
        if direction.length() > 0:
            self.velocity = direction.normalize() * self.speed
        else:
            self.velocity = pygame.math.Vector2(0, -self.speed)

        # 궤적 저장 (트레일 효과)
        self.trail: List[pygame.math.Vector2] = []
        self.trail_max_length = 12

        # 상태
        self.is_alive = True
        self.exploded = False

        # 시각 효과
        self.size = 8
        self.glow_size = 16

    def update(self, dt: float) -> bool:
        """업데이트. 폭발 시 True 반환"""
        if not self.is_alive:
            return False

        # 궤적 저장
        self.trail.append(pygame.math.Vector2(self.pos))
        if len(self.trail) > self.trail_max_length:
            self.trail.pop(0)

        # 이동
        self.pos += self.velocity * dt

        # 화면 밖 체크 (약간의 여유)
        margin = 50
        if (self.pos.x < -margin or self.pos.x > self.screen_size[0] + margin or
            self.pos.y < -margin or self.pos.y > self.screen_size[1] + margin):
            self.is_alive = False
            return False

        # 목표 지점 근처 도달 시 폭발
        dist_to_target = (self.pos - self.target_pos).length()
        if dist_to_target < 30:
            self.explode()
            return True

        return False

    def explode(self):
        """포탄 폭발"""
        self.exploded = True
        self.is_alive = False

    def draw(self, screen: pygame.Surface):
        """포탄 및 트레일 렌더링"""
        if not self.is_alive and not self.exploded:
            return

        # 트레일 그리기 (그라데이션)
        for i, trail_pos in enumerate(self.trail):
            progress = i / max(1, len(self.trail) - 1)
            alpha = int(180 * progress)
            trail_size = int(3 + 4 * progress)

            # 주황색 그라데이션
            r = int(255 * (0.8 + 0.2 * progress))
            g = int(180 * progress)
            b = int(50 * progress)

            trail_surf = pygame.Surface((trail_size * 2, trail_size * 2), pygame.SRCALPHA)
            pygame.draw.circle(trail_surf, (r, g, b, alpha),
                             (trail_size, trail_size), trail_size)
            screen.blit(trail_surf, (int(trail_pos.x - trail_size),
                                    int(trail_pos.y - trail_size)))

        if not self.is_alive:
            return

        # 글로우 효과
        glow_surf = pygame.Surface((self.glow_size * 2, self.glow_size * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (255, 200, 100, 100),
                          (self.glow_size, self.glow_size), self.glow_size)
        screen.blit(glow_surf, (int(self.pos.x - self.glow_size),
                               int(self.pos.y - self.glow_size)))

        # 포탄 본체
        pygame.draw.circle(screen, (255, 220, 150),
                          (int(self.pos.x), int(self.pos.y)), self.size)
        pygame.draw.circle(screen, (255, 255, 200),
                          (int(self.pos.x), int(self.pos.y)), self.size // 2)


class BunkerCannonEffect:
    """
    2막 벙커 포신 연출 효과

    상태 머신:
    - IDLE: 대기 (3-8초 랜덤)
    - AIMING: 목표 조준 (포신 회전)
    - CHARGING: 충전 (경고선 표시)
    - FIRING: 발사 (섬광 + 반동)
    - COOLDOWN: 쿨다운
    """

    # 상태 상수
    STATE_IDLE = "idle"
    STATE_AIMING = "aiming"
    STATE_CHARGING = "charging"
    STATE_FIRING = "firing"
    STATE_COOLDOWN = "cooldown"

    def __init__(self, screen_size: Tuple[int, int], position: Tuple[float, float] = None):
        """
        Args:
            screen_size: 화면 크기
            position: 포신 기준점 위치 (기본: 화면 우측 하단)
        """
        self.screen_size = screen_size

        # 포신 위치 (화면 우측 하단, 배경 건물 위치 추정)
        if position:
            self.base_pos = pygame.math.Vector2(position)
        else:
            self.base_pos = pygame.math.Vector2(
                screen_size[0] * 0.85,
                screen_size[1] * 0.75
            )

        # 포신 크기
        self.barrel_length = 80
        self.barrel_width = 16

        # 회전 각도 (라디안, 0 = 오른쪽, 위쪽이 음수)
        self.current_angle = -math.pi / 4  # -45도 (좌상단 방향)
        self.target_angle = self.current_angle
        self.angle_speed = 1.5  # 라디안/초

        # 반동 효과
        self.recoil_offset = 0.0
        self.recoil_max = 20.0

        # 상태 머신
        self.state = self.STATE_IDLE
        self.state_timer = 0.0
        self.state_duration = random.uniform(3.0, 6.0)

        # 발사 대상
        self.target_pos: Optional[pygame.math.Vector2] = None
        self.fire_pattern = "player"  # player, random_area, sweep

        # 포탄 및 파티클
        self.shells: List[CannonShell] = []
        self.smoke_particles: List[SmokeParticle] = []

        # 머즐 플래시
        self.muzzle_flash_timer = 0.0
        self.muzzle_flash_duration = 0.15

        # 충전 경고선
        self.charge_warning_blink = 0.0

        # 활성화 상태
        self.is_active = False

        # 폭발 효과 콜백 (story_mode에서 설정)
        self.on_shell_explode = None

    def activate(self):
        """포신 활성화"""
        self.is_active = True
        self.state = self.STATE_IDLE
        self.state_timer = 0.0
        self.state_duration = random.uniform(2.0, 4.0)

    def deactivate(self):
        """포신 비활성화"""
        self.is_active = False

    def _select_target(self, player_pos: Optional[Tuple[float, float]],
                       enemies: List = None) -> pygame.math.Vector2:
        """발사 대상 선택 - 가장 가까운 적 우선"""
        # 가장 가까운 적 찾기
        if enemies:
            closest_enemy = None
            closest_dist = float('inf')
            for enemy in enemies:
                if hasattr(enemy, 'is_alive') and enemy.is_alive:
                    dist = ((enemy.pos.x - self.base_pos.x) ** 2 +
                           (enemy.pos.y - self.base_pos.y) ** 2) ** 0.5
                    if dist < closest_dist:
                        closest_dist = dist
                        closest_enemy = enemy

            if closest_enemy:
                self.fire_pattern = "enemy"
                return pygame.math.Vector2(closest_enemy.pos.x, closest_enemy.pos.y)

        # 적이 없으면 랜덤 영역
        self.fire_pattern = "random_area"
        return pygame.math.Vector2(
            random.uniform(self.screen_size[0] * 0.2, self.screen_size[0] * 0.8),
            random.uniform(self.screen_size[1] * 0.1, self.screen_size[1] * 0.4)
        )

    def _calculate_angle_to_target(self) -> float:
        """대상까지의 각도 계산"""
        if not self.target_pos:
            return self.current_angle

        direction = self.target_pos - self.base_pos
        return math.atan2(direction.y, direction.x)

    def _get_muzzle_position(self) -> pygame.math.Vector2:
        """포구 위치 반환 (반동 적용)"""
        effective_length = self.barrel_length - self.recoil_offset
        return pygame.math.Vector2(
            self.base_pos.x + math.cos(self.current_angle) * effective_length,
            self.base_pos.y + math.sin(self.current_angle) * effective_length
        )

    def update(self, dt: float, player_pos: Optional[Tuple[float, float]] = None,
               enemies: List = None):
        """상태 머신 업데이트"""
        if not self.is_active:
            return

        self.state_timer += dt

        # 상태별 처리
        if self.state == self.STATE_IDLE:
            self._update_idle(dt, player_pos, enemies)
        elif self.state == self.STATE_AIMING:
            self._update_aiming(dt)
        elif self.state == self.STATE_CHARGING:
            self._update_charging(dt)
        elif self.state == self.STATE_FIRING:
            self._update_firing(dt)
        elif self.state == self.STATE_COOLDOWN:
            self._update_cooldown(dt)

        # 반동 복구
        if self.recoil_offset > 0:
            self.recoil_offset = max(0, self.recoil_offset - 60 * dt)

        # 포탄 업데이트
        for shell in self.shells[:]:
            exploded = shell.update(dt)
            if exploded and self.on_shell_explode:
                self.on_shell_explode(shell.pos, shell.damage, shell.explosion_radius)
            if not shell.is_alive:
                self.shells.remove(shell)

        # 연기 파티클 업데이트
        for particle in self.smoke_particles[:]:
            particle.update(dt)
            if not particle.is_alive:
                self.smoke_particles.remove(particle)

    def _update_idle(self, dt: float, player_pos, enemies):
        """대기 상태"""
        if self.state_timer >= self.state_duration:
            # 목표 선택 및 조준 시작
            self.target_pos = self._select_target(player_pos, enemies)
            self.target_angle = self._calculate_angle_to_target()
            self._change_state(self.STATE_AIMING, 1.5)

    def _update_aiming(self, dt: float):
        """조준 상태 (포신 회전)"""
        # 각도 보간
        angle_diff = self.target_angle - self.current_angle
        # 최단 경로로 회전
        while angle_diff > math.pi:
            angle_diff -= 2 * math.pi
        while angle_diff < -math.pi:
            angle_diff += 2 * math.pi

        rotate_amount = self.angle_speed * dt
        if abs(angle_diff) < rotate_amount:
            self.current_angle = self.target_angle
        else:
            self.current_angle += rotate_amount if angle_diff > 0 else -rotate_amount

        if self.state_timer >= self.state_duration:
            self._change_state(self.STATE_CHARGING, 0.8)

    def _update_charging(self, dt: float):
        """충전 상태 (경고선)"""
        self.charge_warning_blink += dt * 10

        if self.state_timer >= self.state_duration:
            self._fire()
            self._change_state(self.STATE_FIRING, 0.3)

    def _update_firing(self, dt: float):
        """발사 상태 (섬광)"""
        self.muzzle_flash_timer = self.state_timer

        if self.state_timer >= self.state_duration:
            self._change_state(self.STATE_COOLDOWN, 2.0)

    def _update_cooldown(self, dt: float):
        """쿨다운 상태"""
        if self.state_timer >= self.state_duration:
            self._change_state(self.STATE_IDLE, random.uniform(3.0, 8.0))

    def _change_state(self, new_state: str, duration: float):
        """상태 전환"""
        self.state = new_state
        self.state_timer = 0.0
        self.state_duration = duration

    def _fire(self):
        """포탄 발사"""
        if not self.target_pos:
            return

        muzzle_pos = self._get_muzzle_position()

        # 포탄 생성
        shell = CannonShell(
            start_pos=(muzzle_pos.x, muzzle_pos.y),
            target_pos=(self.target_pos.x, self.target_pos.y),
            screen_size=self.screen_size
        )
        self.shells.append(shell)

        # 반동
        self.recoil_offset = self.recoil_max

        # 연기 생성
        for _ in range(8):
            smoke = SmokeParticle((muzzle_pos.x, muzzle_pos.y))
            self.smoke_particles.append(smoke)

    def draw_background_layer(self, screen: pygame.Surface):
        """배경 레이어에 그릴 요소 (연기, 포신)"""
        if not self.is_active:
            return

        # 연기 파티클 (배경에 블렌딩)
        for particle in self.smoke_particles:
            particle.draw(screen)

        # 포신 베이스 (원형)
        pygame.draw.circle(screen, (60, 55, 50),
                          (int(self.base_pos.x), int(self.base_pos.y)), 25)
        pygame.draw.circle(screen, (80, 75, 70),
                          (int(self.base_pos.x), int(self.base_pos.y)), 20)

        # 포신 본체
        muzzle_pos = self._get_muzzle_position()
        barrel_points = self._get_barrel_polygon()
        pygame.draw.polygon(screen, (70, 65, 60), barrel_points)

        # 포신 하이라이트
        highlight_offset = pygame.math.Vector2(
            -math.sin(self.current_angle) * 3,
            math.cos(self.current_angle) * 3
        )
        highlight_start = self.base_pos + highlight_offset
        highlight_end = muzzle_pos + highlight_offset
        pygame.draw.line(screen, (90, 85, 80),
                        (int(highlight_start.x), int(highlight_start.y)),
                        (int(highlight_end.x), int(highlight_end.y)), 3)

        # 충전 경고선
        if self.state == self.STATE_CHARGING and self.target_pos:
            self._draw_charge_warning(screen)

        # 머즐 플래시
        if self.state == self.STATE_FIRING:
            self._draw_muzzle_flash(screen)

    def _get_barrel_polygon(self) -> List[Tuple[int, int]]:
        """포신 폴리곤 꼭지점 반환"""
        # 포신 방향 벡터
        direction = pygame.math.Vector2(
            math.cos(self.current_angle),
            math.sin(self.current_angle)
        )
        # 수직 벡터
        perpendicular = pygame.math.Vector2(-direction.y, direction.x)

        # 반동 적용된 길이
        effective_length = self.barrel_length - self.recoil_offset

        # 4개의 꼭지점
        half_width = self.barrel_width / 2
        base_left = self.base_pos + perpendicular * half_width
        base_right = self.base_pos - perpendicular * half_width
        tip_left = self.base_pos + direction * effective_length + perpendicular * (half_width * 0.7)
        tip_right = self.base_pos + direction * effective_length - perpendicular * (half_width * 0.7)

        return [
            (int(base_left.x), int(base_left.y)),
            (int(tip_left.x), int(tip_left.y)),
            (int(tip_right.x), int(tip_right.y)),
            (int(base_right.x), int(base_right.y)),
        ]

    def _draw_charge_warning(self, screen: pygame.Surface):
        """충전 경고선 (점선)"""
        if not self.target_pos:
            return

        muzzle_pos = self._get_muzzle_position()

        # 깜박임 효과
        if int(self.charge_warning_blink) % 2 == 0:
            return

        # 점선 그리기
        direction = self.target_pos - muzzle_pos
        if direction.length() == 0:
            return

        direction = direction.normalize()
        distance = (self.target_pos - muzzle_pos).length()

        dash_length = 15
        gap_length = 10
        current_dist = 0

        while current_dist < distance:
            start = muzzle_pos + direction * current_dist
            end_dist = min(current_dist + dash_length, distance)
            end = muzzle_pos + direction * end_dist

            # 빨간색 경고선
            pygame.draw.line(screen, (255, 80, 80),
                           (int(start.x), int(start.y)),
                           (int(end.x), int(end.y)), 2)

            current_dist += dash_length + gap_length

    def _draw_muzzle_flash(self, screen: pygame.Surface):
        """머즐 플래시 (3단계 섬광)"""
        muzzle_pos = self._get_muzzle_position()
        progress = self.muzzle_flash_timer / self.muzzle_flash_duration

        if progress > 1:
            return

        # 섬광 크기 (시간에 따라 감소)
        flash_scale = 1.0 - progress

        # 3단계 글로우
        sizes = [50, 35, 20]
        colors = [
            (255, 255, 200, int(60 * flash_scale)),
            (255, 200, 100, int(120 * flash_scale)),
            (255, 180, 80, int(200 * flash_scale)),
        ]

        for size, color in zip(sizes, colors):
            actual_size = int(size * flash_scale)
            if actual_size <= 0:
                continue

            surf = pygame.Surface((actual_size * 2, actual_size * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, color, (actual_size, actual_size), actual_size)
            screen.blit(surf, (int(muzzle_pos.x - actual_size),
                              int(muzzle_pos.y - actual_size)))

    def draw_foreground_layer(self, screen: pygame.Surface):
        """전경 레이어에 그릴 요소 (포탄)"""
        if not self.is_active:
            return

        for shell in self.shells:
            shell.draw(screen)


class CombatMotionEffect:
    """
    전투 중 고속 비행 연출 효과

    플레이어가 움직일 때 combat_motion 이미지를 화면에 표시
    - 플레이어 위치 중심 줌/워프 인트로
    - 5단계 속도감 이미지 (combat_motion_00~04)
    - 프레임 간 부드러운 크로스페이드 전환
    """

    def __init__(self, screen_size: Tuple[int, int]):
        self.screen_size = screen_size
        self.is_active = False
        self.elapsed = 0.0
        self.duration = 2.0  # 효과 지속 시간 (3초 → 2초로 단축)

        # 5단계 속도 이미지
        self.motion_frames: List[pygame.Surface] = []
        self._load_motion_images()

        # 부드러운 프레임 전환용
        self.frame_progress = 0.0  # 0.0 ~ 4.0 (연속적인 프레임 위치)

        # 발동 조건 추적
        self.player_move_time = 0.0  # 플레이어가 연속 이동한 시간
        self.move_threshold = 3.0  # 3초 이상 이동해야 발동
        self.cooldown = 0.0  # 쿨다운
        self.cooldown_duration = 5.0  # 다음 발동까지 대기 시간

        # 방향 전환 감지용
        self.prev_direction = None  # 이전 이동 방향 (dx, dy 정규화)

        # 효과 파라미터
        self.flash_alpha = 0
        self.image_alpha = 230  # 이미지 불투명도 90% (255 * 0.90 ≈ 230)

        # 줌/워프 인트로
        self.intro_phase = False
        self.intro_elapsed = 0.0
        self.intro_duration = 1.0  # 워프 인트로 지속 시간 (1.2초 → 1초)
        self.player_pos = None  # 플레이어 위치 (줌 중심점)
        self.zoom_scale = 1.0  # 현재 줌 스케일

    def _load_motion_images(self):
        """5단계 속도감 이미지 로드 (combat_motion_00~04)"""
        extensions = ['jpg', 'png', 'png', 'png', 'png']
        try:
            for i in range(5):
                img_path = Path(f"assets/images/effects/combat_motion_0{i}.{extensions[i]}")
                if img_path.exists():
                    img = pygame.image.load(str(img_path)).convert()
                    scaled = pygame.transform.scale(img, self.screen_size)
                    self.motion_frames.append(scaled)
                else:
                    print(f"WARNING: {img_path} not found")

            if len(self.motion_frames) > 0:
                print(f"INFO: CombatMotionEffect loaded ({len(self.motion_frames)} frames)")
        except Exception as e:
            print(f"WARNING: Failed to load combat_motion images: {e}")

    def reset_wave(self):
        """새 웨이브 시작 시 호출"""
        self.cooldown = 0.0
        self.player_move_time = 0.0
        self.is_active = False  # 효과 강제 종료
        self.elapsed = 0.0
        self.frame_progress = 0.0

    def reset_move_time(self):
        """이동 시간 리셋 (적/사물과 충돌 시 호출)"""
        self.player_move_time = 0.0

    def stop_effect(self):
        """효과 즉시 종료 (공격 시 호출)"""
        if self.is_active:
            self.is_active = False
            self.intro_phase = False
            self.elapsed = 0.0
            self.frame_progress = 0.0
            self.player_move_time = 0.0
            self.prev_direction = None

    def update_player_movement(self, is_moving: bool, dt: float, player_pos=None, move_direction=None):
        """플레이어 이동 상태 추적

        Args:
            is_moving: 플레이어가 이동 중인지 여부
            dt: 델타 타임
            player_pos: 플레이어 위치 (x, y) - 줌/워프 중심점
            move_direction: 이동 방향 (dx, dy) - 방향 전환 감지용
        """
        if self.is_active:
            return  # 효과 진행 중엔 추적 안 함

        # 쿨다운 감소
        if self.cooldown > 0:
            self.cooldown -= dt

        if is_moving:
            # 방향 전환 감지
            if move_direction is not None and self.prev_direction is not None:
                # 방향 벡터 내적으로 방향 변화 감지
                # 내적이 0.5 미만이면 45도 이상 방향 전환으로 간주
                import math
                dx, dy = move_direction
                pdx, pdy = self.prev_direction
                # 벡터 정규화
                mag = math.sqrt(dx * dx + dy * dy)
                pmag = math.sqrt(pdx * pdx + pdy * pdy)
                if mag > 0.01 and pmag > 0.01:
                    ndx, ndy = dx / mag, dy / mag
                    npdx, npdy = pdx / pmag, pdy / pmag
                    dot = ndx * npdx + ndy * npdy
                    if dot < 0.5:  # 약 60도 이상 방향 전환
                        self.player_move_time = 0.0  # 누적 시간 리셋

            # 현재 방향 저장
            if move_direction is not None:
                self.prev_direction = move_direction

            self.player_move_time += dt
        else:
            self.player_move_time = 0.0
            self.prev_direction = None

        # 발동 조건 체크
        if self._can_trigger():
            self.trigger(player_pos)

    def _can_trigger(self) -> bool:
        """발동 가능 여부 체크 (2초 이상 연속 이동 시 언제나 발동)"""
        if self.is_active:
            return False
        if self.cooldown > 0:
            return False
        if self.player_move_time < self.move_threshold:
            return False
        if len(self.motion_frames) == 0:
            return False
        return True

    def trigger(self, player_pos=None):
        """효과 발동 (줌/워프 인트로 포함)

        Args:
            player_pos: 플레이어 위치 (x, y) - 줌/워프 중심점
        """
        self.is_active = True
        self.elapsed = 0.0
        self.cooldown = self.cooldown_duration
        self.player_move_time = 0.0

        # 플레이어 위치 저장 (줌 중심점)
        self.player_pos = player_pos

        # 인트로 페이즈 초기화 (줌/워프)
        self.intro_phase = True
        self.intro_elapsed = 0.0
        self.zoom_scale = 1.0  # 줌 스케일 초기화

        # 메인 효과 초기화
        self.frame_progress = 0.0
        self.flash_alpha = 150

        print(f"INFO: CombatMotionEffect triggered with zoom/warp")

    def update(self, dt: float):
        """효과 업데이트"""
        if not self.is_active:
            return

        # 인트로 페이즈 (플레이어 잔상)
        if self.intro_phase:
            self.intro_elapsed += dt
            if self.intro_elapsed >= self.intro_duration:
                self.intro_phase = False
            return  # 인트로 중에는 메인 효과 진행 안 함

        # 메인 효과
        self.elapsed += dt
        progress = self.elapsed / self.duration

        if progress >= 1.0:
            self.is_active = False
            return

        # 연속적인 프레임 진행 (0.0 ~ 4.0 사이를 부드럽게 이동)
        # 가속 구간 (0~70%): 0 → 4
        # 최고속 유지 (70~85%): 4
        # 감속 구간 (85~100%): 4 → 0
        if progress < 0.70:
            # 가속: ease-out 커브로 부드럽게 증가
            accel_progress = progress / 0.70
            eased = 1 - (1 - accel_progress) ** 2  # ease-out quad
            self.frame_progress = eased * 4.0
        elif progress < 0.85:
            # 최고속 유지
            self.frame_progress = 4.0
        else:
            # 감속: ease-in 커브로 부드럽게 감소
            decel_progress = (progress - 0.85) / 0.15
            eased = decel_progress ** 2  # ease-in quad
            self.frame_progress = 4.0 * (1 - eased)

        # 플래시 (빠르게 감소)
        if progress < 0.10:
            self.flash_alpha = int(120 * (1 - progress / 0.10))
        else:
            self.flash_alpha = 0

    def _draw_zoom_warp(self, screen: pygame.Surface, intro_progress: float):
        """줌/워프 효과 그리기 - 플레이어 위치에서 원형으로 시작해 전체 화면으로 확대"""
        if not self.player_pos or len(self.motion_frames) == 0:
            return

        import math

        px, py = self.player_pos
        sw, sh = self.screen_size

        # 커스텀 이징: 초반에 천천히 → 후반에 빠르게
        # 작은 원 상태를 더 오래 볼 수 있도록
        if intro_progress < 0.5:
            # 초반 50%: 천천히 확대 (전체의 20%만 진행)
            t = intro_progress / 0.5
            eased = 0.2 * (t ** 2)  # ease-in quad
        else:
            # 후반 50%: 빠르게 확대 (나머지 80% 진행)
            t = (intro_progress - 0.5) / 0.5
            eased = 0.2 + 0.8 * (1 - (1 - t) ** 2)  # ease-out quad

        # 원형 마스크 반경: 작은 원 → 전체 화면을 덮을 만큼 확대
        # 대각선 길이를 기준으로 최대 반경 계산
        max_radius = math.sqrt(sw ** 2 + sh ** 2)
        min_radius = 60  # 시작 반경 (더 큰 원으로 시작)
        current_radius = min_radius + (max_radius - min_radius) * eased

        # 첫 번째 모션 프레임
        base_frame = self.motion_frames[0]

        # 원형 마스크 Surface 생성
        mask_surf = pygame.Surface(self.screen_size, pygame.SRCALPHA)

        # 원형 클리핑 영역에 속도감 이미지 그리기
        # 원 내부만 보이도록 마스크 적용
        pygame.draw.circle(mask_surf, (255, 255, 255, 255),
                          (int(px), int(py)), int(current_radius))

        # 속도감 이미지를 마스크에 블릿 (BLEND_RGBA_MIN으로 마스크 적용)
        temp_surf = pygame.Surface(self.screen_size, pygame.SRCALPHA)
        temp_surf.blit(base_frame, (0, 0))
        temp_surf.blit(mask_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)

        # 투명도 적용 (30~40% → 알파 75~100)
        temp_surf.set_alpha(self.image_alpha)
        screen.blit(temp_surf, (0, 0))

        # 원형 테두리 효과 (확대되는 원의 가장자리 강조) - 더 오래 표시
        if current_radius < max_radius * 0.95:
            edge_alpha = int(255 * (1 - eased * 0.8))
            edge_color = (200, 220, 255, edge_alpha)
            edge_thickness = max(4, int(12 * (1 - eased)))
            pygame.draw.circle(screen, edge_color,
                             (int(px), int(py)), int(current_radius), edge_thickness)

        # 방사형 속도선 제거됨

    def _draw_warp_lines(self, screen: pygame.Surface, cx: int, cy: int,
                          progress: float, alpha: int):
        """워프 속도선 그리기 (원형 가장자리에서 바깥으로 뻗어나감)"""
        import math

        line_count = 16  # 방사선 개수 (32 → 16으로 축소)
        sw, sh = self.screen_size
        max_radius = math.sqrt(sw ** 2 + sh ** 2)

        # 현재 원형 마스크 반경
        min_radius = 30
        current_radius = min_radius + (max_radius - min_radius) * progress

        line_surf = pygame.Surface(self.screen_size, pygame.SRCALPHA)

        for i in range(line_count):
            angle = (i / line_count) * 2 * math.pi

            # 시작점: 원형 가장자리 바로 바깥
            start_dist = current_radius + 5
            start_x = cx + math.cos(angle) * start_dist
            start_y = cy + math.sin(angle) * start_dist

            # 끝점: 원형 가장자리에서 더 바깥으로
            line_length = 40 + 60 * progress  # 선 길이 (80~200 → 40~100으로 축소)
            end_dist = start_dist + line_length
            end_x = cx + math.cos(angle) * end_dist
            end_y = cy + math.sin(angle) * end_dist

            # 선 색상 (흰색~하늘색, 그라데이션)
            color = (220, 235, 255, alpha)
            thickness = 2 + int(progress * 2)

            pygame.draw.line(line_surf, color,
                           (int(start_x), int(start_y)),
                           (int(end_x), int(end_y)), thickness)

        screen.blit(line_surf, (0, 0))

    def draw(self, screen: pygame.Surface):
        """효과 렌더링 (줌/워프 인트로 + 메인 속도감)"""
        if not self.is_active or len(self.motion_frames) == 0:
            return

        # === 인트로 페이즈: 줌/워프 효과 ===
        if self.intro_phase:
            intro_progress = self.intro_elapsed / self.intro_duration

            # 줌/워프 효과 (플레이어 위치 중심으로 확대 + 방사형 속도선)
            self._draw_zoom_warp(screen, intro_progress)

            # 플래시 오버레이 (워프 시작 시 강한 빛)
            flash_alpha = int(200 * (1 - intro_progress ** 0.5))
            if flash_alpha > 0:
                flash_surf = pygame.Surface(self.screen_size, pygame.SRCALPHA)
                flash_surf.fill((255, 255, 255, flash_alpha))
                screen.blit(flash_surf, (0, 0))
            return

        # === 메인 페이즈: 기존 속도감 이미지 (투명도 적용) ===
        progress = self.elapsed / self.duration

        # 페이드 아웃 알파 계산 (인트로 후이므로 페이드 인 불필요)
        # 기본 투명도(image_alpha)에서 페이드 아웃
        if progress > 0.88:
            fade_factor = 1 - (progress - 0.88) / 0.12
            master_alpha = int(self.image_alpha * fade_factor)
        else:
            master_alpha = self.image_alpha

        # 프레임 블렌딩 계산
        frame_idx = int(self.frame_progress)
        frame_idx = max(0, min(frame_idx, len(self.motion_frames) - 1))
        blend_factor = self.frame_progress - frame_idx  # 0.0 ~ 1.0

        # 블렌딩용 Surface 생성 (SRCALPHA로 투명도 지원)
        blend_surf = pygame.Surface(self.screen_size, pygame.SRCALPHA)

        # 현재 프레임
        current_frame = self.motion_frames[frame_idx]
        blend_surf.blit(current_frame, (0, 0))

        # 다음 프레임과 크로스페이드 (있는 경우)
        next_idx = frame_idx + 1
        if next_idx < len(self.motion_frames) and blend_factor > 0:
            next_frame = self.motion_frames[next_idx]
            next_copy = next_frame.copy()
            next_copy.set_alpha(int(255 * blend_factor))
            blend_surf.blit(next_copy, (0, 0))

        # 마스터 알파 적용 (30~40% 투명도)
        blend_surf.set_alpha(master_alpha)

        screen.blit(blend_surf, (0, 0))

        # 플래시 오버레이
        if self.flash_alpha > 0:
            flash_surf = pygame.Surface(self.screen_size, pygame.SRCALPHA)
            flash_surf.fill((255, 255, 255, self.flash_alpha))
            screen.blit(flash_surf, (0, 0))


# =========================================================
# Act 2: 기밀 문서 뷰어 효과
# =========================================================
class ClassifiedDocumentEffect:
    """
    Act 2 컷씬: 기밀 문서 뷰어 효과

    새로운 연출 순서:
    1. 건물 중앙 검은문으로 천천히 클로즈업
    2. gate01~04 전체화면으로 자연스럽게 연결
    3. gate 연출 후 캐비닛 등장
    4. 대화 클릭마다 문서 등장 및 화면에 쌓임
    5. 모든 문서 쌓인 후 각 문서 확대→축소→정렬
    6. 대화 종료시 원래 배경으로 복귀
    """

    # 페이즈 정의
    PHASE_ZOOM_IN = 0           # 배경 건물 중앙으로 클로즈업
    PHASE_GATE_SEQUENCE = 1     # gate 이미지 시퀀스 (전체화면 전환)
    PHASE_CABINET_SHOW = 2      # 캐비닛 등장
    PHASE_DIALOGUE = 3          # 대화 + 문서 등장
    PHASE_DOC_REVIEW = 4        # 모든 문서 즉각 정렬
    PHASE_DOC_VIEW = 5          # 정렬 후 대기 - 클릭으로 문서 확대 보기
    PHASE_ZOOM_OUT = 6          # 원래 배경으로 복귀
    PHASE_DONE = 7

    def __init__(self, screen_size: tuple, document_paths: list,
                 background_path: str = None, dialogue_after: list = None,
                 sound_manager=None, special_effects: dict = None,
                 scene_id: str = "document_scene",
                 gate_image_paths: list = None):
        self.screen_size = screen_size
        self.document_paths = document_paths
        self.background_path = background_path
        self.dialogue_after = dialogue_after or []
        self.sound_manager = sound_manager
        self.special_effects = special_effects or {}
        self.scene_id = scene_id

        self.is_alive = True
        self.phase = self.PHASE_ZOOM_IN
        self.phase_timer = 0.0

        # gate 이미지 경로 (기본값 - 실제 파일 기준)
        self.gate_image_paths = gate_image_paths or [
            "assets/story_mode/documents/bunker_gate_01.jpg",
            "assets/story_mode/documents/bunker_gate_02.jpg",
            "assets/story_mode/documents/bunker_gate_03.jpg",
        ]

        # 타이밍 설정 (모든 등장 천천히)
        self.zoom_in_duration = 4.5          # 클로즈업 시간 (더 느리게)
        self.gate_transition_duration = 3.0  # 각 gate 이미지 전환 시간 (느리게)
        self.gate_display_duration = 2.5     # 각 gate 이미지 표시 시간 (더 오래)
        self.cabinet_show_duration = 2.0     # 캐비닛 등장 시간 (천천히)
        self.doc_rise_duration = 1.5         # 문서 솟아오르는 시간 (천천히)
        self.doc_review_duration = 0.15      # 각 문서 정렬 시간 (거의 즉각)
        self.zoom_out_duration = 4.0         # 줌아웃 시간 (천천히)

        # 줌 효과
        self.zoom_scale = 1.0                # 현재 줌 배율
        self.zoom_target_scale = 3.0         # 목표 줌 배율 (더 깊이)
        self.zoom_center_x = 0.5             # 줌 중심 X (건물 중앙)
        self.zoom_center_y = 0.38            # 줌 중심 Y (건물 문 위치)

        # 배경
        self.background_original = None
        self.background = None
        if background_path:
            self._load_background(background_path)

        # gate 이미지들
        self.gate_images = []
        self.current_gate_index = 0
        self.gate_transition_progress = 0.0
        self.gate_display_timer = 0.0
        self.gate_state = "display"  # "display" or "transition"
        self._load_gate_images()

        # 캐비닛 이미지
        self.cabinet_image = None
        self.cabinet_y_offset = 0.0
        self._load_cabinet()

        # 문서들
        self.documents = []
        self.doc_final_positions = []  # 정렬된 최종 위치 (먼저 초기화)
        self._prepare_documents()

        # 현재 표시 중인 문서
        self.current_doc_index = -1
        self.doc_rise_progress = 0.0
        self.doc_is_rising = False

        # 문서 리뷰 관련 (즉각 정렬)
        self.review_doc_index = 0
        self.review_state = "arrange_all"  # "arrange_all" (즉각 정렬)
        self.review_progress = 0.0

        # 문서 확대 보기 관련 (PHASE_DOC_VIEW)
        self.viewing_doc_index = -1      # 현재 확대 보기 중인 문서 (-1이면 없음)
        self.view_zoom_progress = 0.0    # 확대/축소 애니메이션 진행도
        self.view_zoom_duration = 0.25   # 확대 애니메이션 시간 (빠르게)
        self.view_state = "idle"         # "idle", "zoom_in", "viewing", "zoom_out"
        self.doc_rects = []              # 각 문서의 클릭 영역

        # 대사 관련
        self.current_dialogue_index = 0
        self.dialogue_text = ""
        self.typing_progress = 0.0
        self.typing_speed = 30.0
        self.waiting_for_click = False

        # 초상화 캐시
        self.portrait_cache = {}

        # 폰트
        self.fonts = {}

        # 콜백
        self.on_complete = None
        self.on_replay_request = None

        # 페이드 효과용
        self.fade_alpha = 0.0

        print(f"INFO: ClassifiedDocumentEffect created with {len(self.document_paths)} documents, {len(self.gate_image_paths)} gate images")

    def _load_background(self, path: str):
        """배경 이미지 로드"""
        try:
            img = pygame.image.load(path).convert()
            self.background_original = pygame.transform.smoothscale(img, self.screen_size)
            self.background = self.background_original.copy()
        except Exception as e:
            print(f"WARNING: Failed to load background: {path} - {e}")
            self.background_original = pygame.Surface(self.screen_size)
            self.background_original.fill((30, 35, 40))
            self.background = self.background_original.copy()

    def _load_gate_images(self):
        """gate 이미지들 로드 (전체화면용)"""
        for path in self.gate_image_paths:
            try:
                img = pygame.image.load(path).convert()
                img = pygame.transform.smoothscale(img, self.screen_size)
                self.gate_images.append(img)
            except Exception as e:
                print(f"WARNING: Failed to load gate image: {path} - {e}")
                # 플레이스홀더
                placeholder = pygame.Surface(self.screen_size)
                placeholder.fill((40, 45, 50))
                self.gate_images.append(placeholder)

        if not self.gate_images:
            # gate 이미지가 하나도 없으면 플레이스홀더 추가
            placeholder = pygame.Surface(self.screen_size)
            placeholder.fill((40, 45, 50))
            self.gate_images.append(placeholder)

    def _load_cabinet(self):
        """캐비닛 이미지 로드"""
        cabinet_path = "assets/story_mode/documents/doc_cabinet.png"
        try:
            img = pygame.image.load(cabinet_path).convert_alpha()
            cabinet_height = int(self.screen_size[1] * 0.55)
            orig_w, orig_h = img.get_size()
            ratio = cabinet_height / orig_h
            cabinet_width = int(orig_w * ratio)
            self.cabinet_image = pygame.transform.smoothscale(img, (cabinet_width, cabinet_height))
        except Exception as e:
            print(f"WARNING: Failed to load cabinet: {cabinet_path} - {e}")
            cabinet_width = int(self.screen_size[0] * 0.35)
            cabinet_height = int(self.screen_size[1] * 0.55)
            self.cabinet_image = pygame.Surface((cabinet_width, cabinet_height), pygame.SRCALPHA)
            pygame.draw.rect(self.cabinet_image, (50, 55, 60), (0, 0, cabinet_width, cabinet_height))
            pygame.draw.rect(self.cabinet_image, (80, 85, 90), (0, 0, cabinet_width, cabinet_height), 3)
            for i in range(3):
                handle_y = 80 + i * (cabinet_height // 4)
                pygame.draw.rect(self.cabinet_image, (100, 105, 110),
                               (cabinet_width // 2 - 30, handle_y, 60, 15))

    def _prepare_documents(self):
        """문서 이미지 준비 - 원본 비율 유지, 특정 문서만 높이 조정"""
        screen_w, screen_h = self.screen_size

        # 문서 최대 크기
        max_width = int(screen_w * 0.26)
        max_height = int(screen_h * 0.58)

        # 문서 1, 2만 높이 줄임 (파일명 기준)
        height_reduction = {
            "doc_project_ark.png": 0.80,     # 문서 1: 높이 80%로 줄임
            "doc_survivor_list.png": 0.80,   # 문서 2: 높이 80%로 줄임
        }

        # 문서 4만 약간 확대
        scale_up = {
            "doc_transmission.png": 1.05,    # 문서 4: 5% 확대
        }

        for i, path in enumerate(self.document_paths):
            doc_img = None
            filename = Path(path).name

            try:
                doc_img = pygame.image.load(path).convert_alpha()
                orig_w, orig_h = doc_img.get_size()

                # 비율 유지하면서 최대 크기에 맞춤
                ratio = min(max_width / orig_w, max_height / orig_h)

                # 문서 4 확대
                if filename in scale_up:
                    ratio *= scale_up[filename]

                new_w = int(orig_w * ratio)
                new_h = int(orig_h * ratio)

                # 문서 1, 2만 높이 줄임
                if filename in height_reduction:
                    new_h = int(new_h * height_reduction[filename])

                doc_img = pygame.transform.smoothscale(doc_img, (new_w, new_h))
            except Exception as e:
                print(f"WARNING: Failed to load document: {path} - {e}")
                doc_img = pygame.Surface((max_width, max_height), pygame.SRCALPHA)
                doc_img.fill((200, 190, 170))

            self.documents.append({
                'image': doc_img,
                'filename': filename,
                'y_offset': 0.0,
                'alpha': 255,
                'visible': False,
                'scale': 1.0,
                'pos_x': screen_w // 2,
                'pos_y': screen_h // 2,
            })

        # 문서 최종 정렬 위치 계산 (가로로 나열)
        self._calculate_final_positions()

    def _calculate_final_positions(self):
        """문서들의 최종 정렬 위치 계산"""
        screen_w, screen_h = self.screen_size
        num_docs = len(self.documents)

        if num_docs == 0:
            return

        # 문서들을 가로로 나열 (축소해서)
        total_width = screen_w * 0.8
        spacing = total_width / (num_docs + 1)
        start_x = screen_w * 0.1 + spacing

        for i in range(num_docs):
            self.doc_final_positions.append({
                'x': start_x + i * spacing,
                'y': screen_h * 0.45,
                'scale': 0.5  # 축소 비율
            })

    def set_fonts(self, fonts: dict):
        """폰트 설정"""
        self.fonts = fonts

    def update(self, dt: float):
        """업데이트"""
        if not self.is_alive:
            return

        self.phase_timer += dt

        if self.phase == self.PHASE_ZOOM_IN:
            self._update_zoom_in(dt)

        elif self.phase == self.PHASE_GATE_SEQUENCE:
            self._update_gate_sequence(dt)

        elif self.phase == self.PHASE_CABINET_SHOW:
            self._update_cabinet_show(dt)

        elif self.phase == self.PHASE_DIALOGUE:
            self._update_dialogue_phase(dt)

        elif self.phase == self.PHASE_DOC_REVIEW:
            self._update_doc_review(dt)

        elif self.phase == self.PHASE_DOC_VIEW:
            self._update_doc_view(dt)

        elif self.phase == self.PHASE_ZOOM_OUT:
            self._update_zoom_out(dt)

    def _update_zoom_in(self, dt: float):
        """배경 클로즈업 업데이트"""
        progress = min(1.0, self.phase_timer / self.zoom_in_duration)
        # ease-out cubic (천천히 감속)
        eased = 1.0 - (1.0 - progress) ** 3
        self.zoom_scale = 1.0 + (self.zoom_target_scale - 1.0) * eased

        if progress >= 1.0:
            self.phase = self.PHASE_GATE_SEQUENCE
            self.phase_timer = 0.0
            self.current_gate_index = 0
            self.gate_state = "display"
            self.gate_display_timer = 0.0
            self.fade_alpha = 0.0

    def _update_gate_sequence(self, dt: float):
        """gate 이미지 시퀀스 업데이트"""
        if self.gate_state == "display":
            # 현재 이미지 표시 중
            self.gate_display_timer += dt
            if self.gate_display_timer >= self.gate_display_duration:
                # 다음 이미지로 전환 시작
                self.gate_state = "transition"
                self.gate_transition_progress = 0.0
                self.gate_display_timer = 0.0

        elif self.gate_state == "transition":
            # 크로스페이드 전환 중
            self.gate_transition_progress += dt / self.gate_transition_duration

            if self.gate_transition_progress >= 1.0:
                self.gate_transition_progress = 1.0
                self.current_gate_index += 1

                if self.current_gate_index >= len(self.gate_images):
                    # 모든 gate 이미지 완료 -> 캐비닛 등장
                    self.phase = self.PHASE_CABINET_SHOW
                    self.phase_timer = 0.0
                    self.fade_alpha = 255  # 페이드 아웃 시작
                else:
                    self.gate_state = "display"
                    self.gate_display_timer = 0.0

    def _update_cabinet_show(self, dt: float):
        """캐비닛 등장 업데이트"""
        progress = min(1.0, self.phase_timer / self.cabinet_show_duration)
        # ease-out quad
        eased = 1.0 - (1.0 - progress) ** 2
        self.cabinet_y_offset = eased

        # 페이드 인 (gate에서 전환)
        if self.fade_alpha > 0:
            self.fade_alpha = max(0, self.fade_alpha - dt * 200)

        if progress >= 1.0:
            self.phase = self.PHASE_DIALOGUE
            self.phase_timer = 0.0
            self._start_next_document_and_dialogue()

    def _update_dialogue_phase(self, dt: float):
        """대화 + 문서 등장 업데이트"""
        # 문서 솟아오르기 애니메이션
        if self.doc_is_rising:
            self.doc_rise_progress += dt / self.doc_rise_duration
            if self.doc_rise_progress >= 1.0:
                self.doc_rise_progress = 1.0
                self.doc_is_rising = False

        # 대화 타이핑
        if self.current_dialogue_index < len(self.dialogue_after):
            if not self.waiting_for_click:
                self.typing_progress += dt * self.typing_speed
                if self.typing_progress >= len(self.dialogue_text):
                    self.typing_progress = len(self.dialogue_text)
                    self.waiting_for_click = True
        else:
            # 모든 대화 완료 -> 문서 리뷰 페이즈로
            if len(self.documents) > 0:
                self.phase = self.PHASE_DOC_REVIEW
                self.phase_timer = 0.0
                self.review_doc_index = 0
                self.review_state = "arrange_all"  # 즉각 정렬
                self.review_progress = 0.0
            else:
                self.phase = self.PHASE_ZOOM_OUT
                self.phase_timer = 0.0

    def _update_doc_review(self, dt: float):
        """문서 리뷰 - 즉각 정렬 후 DOC_VIEW 페이즈로 전환"""
        self.review_progress += dt / self.doc_review_duration

        if self.review_state == "arrange_all":
            # 모든 문서를 즉각 정렬 위치로 이동
            if self.review_progress >= 1.0:
                # 정렬 완료 -> 문서 확대 보기 페이즈로 전환
                self.phase = self.PHASE_DOC_VIEW
                self.phase_timer = 0.0
                self.view_state = "idle"
                self.viewing_doc_index = -1
                # 문서 클릭 영역 계산
                self._calculate_doc_rects()

    def _update_doc_view(self, dt: float):
        """문서 확대 보기 페이즈 업데이트"""
        if self.view_state == "zoom_in":
            self.view_zoom_progress += dt / self.view_zoom_duration
            if self.view_zoom_progress >= 1.0:
                self.view_zoom_progress = 1.0
                self.view_state = "viewing"

        elif self.view_state == "zoom_out":
            self.view_zoom_progress -= dt / self.view_zoom_duration
            if self.view_zoom_progress <= 0.0:
                self.view_zoom_progress = 0.0
                self.view_state = "idle"
                self.viewing_doc_index = -1

    def _calculate_doc_rects(self):
        """정렬된 문서들의 클릭 영역 계산"""
        self.doc_rects = []
        for i, doc in enumerate(self.documents):
            # visible 여부와 관계없이 모든 문서에 대해 rect 생성
            if i < len(self.doc_final_positions):
                pos = self.doc_final_positions[i]
                orig_w, orig_h = doc['image'].get_size()
                scale = pos['scale']
                w = int(orig_w * scale)
                h = int(orig_h * scale)
                rect = pygame.Rect(int(pos['x'] - w // 2), int(pos['y'] - h // 2), w, h)
                self.doc_rects.append(rect)
                # 문서를 visible로 설정 (정렬 후에는 모두 보여야 함)
                doc['visible'] = True

    def _update_zoom_out(self, dt: float):
        """원래 배경으로 복귀"""
        progress = min(1.0, self.phase_timer / self.zoom_out_duration)
        # ease-in-out quad
        if progress < 0.5:
            eased = 2 * progress * progress
        else:
            eased = 1 - ((-2 * progress + 2) ** 2) / 2

        self.zoom_scale = self.zoom_target_scale - (self.zoom_target_scale - 1.0) * eased
        self.cabinet_y_offset = 1.0 - eased

        # 문서들 페이드 아웃
        for doc in self.documents:
            doc['alpha'] = int(255 * (1.0 - eased))

        if progress >= 1.0:
            self.phase = self.PHASE_DONE
            self.is_alive = False
            if self.on_complete:
                self.on_complete()

    def _start_next_document_and_dialogue(self):
        """다음 문서와 대화 시작"""
        self.current_doc_index += 1
        if self.current_doc_index < len(self.documents):
            self.documents[self.current_doc_index]['visible'] = True
            self.doc_rise_progress = 0.0
            self.doc_is_rising = True

        if self.current_dialogue_index < len(self.dialogue_after):
            self.dialogue_text = self.dialogue_after[self.current_dialogue_index].get("text", "")
            self.typing_progress = 0.0
            self.waiting_for_click = False

    def handle_event(self, event: pygame.event.Event):
        """이벤트 처리"""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self._handle_click()

        elif event.type == pygame.KEYDOWN:
            if event.key in [pygame.K_SPACE, pygame.K_RETURN]:
                return self._handle_click()

        return False

    def _handle_click(self):
        """클릭 처리"""
        if self.phase == self.PHASE_ZOOM_IN:
            # 줌인 스킵
            self.zoom_scale = self.zoom_target_scale
            self.phase = self.PHASE_GATE_SEQUENCE
            self.phase_timer = 0.0
            self.current_gate_index = 0
            self.gate_state = "display"
            return True

        elif self.phase == self.PHASE_GATE_SEQUENCE:
            # gate 시퀀스 스킵 (다음 이미지로)
            if self.gate_state == "display":
                self.gate_state = "transition"
                self.gate_transition_progress = 0.0
            else:
                self.gate_transition_progress = 1.0
            return True

        elif self.phase == self.PHASE_CABINET_SHOW:
            # 캐비닛 등장 스킵
            self.cabinet_y_offset = 1.0
            self.fade_alpha = 0
            self.phase = self.PHASE_DIALOGUE
            self.phase_timer = 0.0
            self._start_next_document_and_dialogue()
            return True

        elif self.phase == self.PHASE_DIALOGUE:
            if self.waiting_for_click:
                self.current_dialogue_index += 1
                if self.current_dialogue_index < len(self.dialogue_after):
                    self._start_next_document_and_dialogue()
                else:
                    # 모든 대화 완료 -> 문서 리뷰
                    if len(self.documents) > 0:
                        self.phase = self.PHASE_DOC_REVIEW
                        self.phase_timer = 0.0
                        self.review_doc_index = 0
                        self.review_state = "arrange_all"  # 즉각 정렬
                        self.review_progress = 0.0
                    else:
                        self.phase = self.PHASE_ZOOM_OUT
                        self.phase_timer = 0.0
            else:
                self.typing_progress = len(self.dialogue_text)
                self.waiting_for_click = True
            return True

        elif self.phase == self.PHASE_DOC_REVIEW:
            # 리뷰 스킵 (즉각 정렬 완료)
            self.review_progress = 1.0
            return True

        elif self.phase == self.PHASE_DOC_VIEW:
            return self._handle_doc_view_click(pygame.mouse.get_pos())

        return False

    def _handle_doc_view_click(self, mouse_pos):
        """문서 확대 보기 페이즈에서 클릭 처리"""
        if self.view_state == "idle":
            # 문서 클릭 확인
            for i, rect in enumerate(self.doc_rects):
                if rect.collidepoint(mouse_pos):
                    # 해당 문서 확대
                    self.viewing_doc_index = i
                    self.view_state = "zoom_in"
                    self.view_zoom_progress = 0.0
                    return True
            # 빈 공간 클릭 - 줌아웃으로 전환
            self.phase = self.PHASE_ZOOM_OUT
            self.phase_timer = 0.0
            return True

        elif self.view_state == "viewing":
            # 확대 보기 중 클릭 - 축소
            self.view_state = "zoom_out"
            return True

        elif self.view_state == "zoom_in":
            # 확대 중 클릭 - 즉시 확대 완료
            self.view_zoom_progress = 1.0
            self.view_state = "viewing"
            return True

        elif self.view_state == "zoom_out":
            # 축소 중 클릭 - 즉시 축소 완료
            self.view_zoom_progress = 0.0
            self.view_state = "idle"
            self.viewing_doc_index = -1
            return True

        return False

    def render(self, screen: pygame.Surface):
        """렌더링"""
        if self.phase == self.PHASE_ZOOM_IN:
            self._render_zoom_phase(screen)

        elif self.phase == self.PHASE_GATE_SEQUENCE:
            self._render_gate_sequence(screen)

        elif self.phase in [self.PHASE_CABINET_SHOW, self.PHASE_DIALOGUE, self.PHASE_DOC_REVIEW]:
            self._render_document_phase(screen)

        elif self.phase == self.PHASE_DOC_VIEW:
            self._render_doc_view_phase(screen)

        elif self.phase == self.PHASE_ZOOM_OUT:
            self._render_zoom_out_phase(screen)

    def _render_zoom_phase(self, screen: pygame.Surface):
        """줌인 페이즈 렌더링"""
        self._render_zoomed_background(screen)

        # 어두운 오버레이 (건물 내부로 들어가는 느낌)
        darkness = min(220, int((self.zoom_scale - 1.0) * 100))
        dark_overlay = pygame.Surface(self.screen_size, pygame.SRCALPHA)
        dark_overlay.fill((0, 0, 0, darkness))
        screen.blit(dark_overlay, (0, 0))

    def _render_gate_sequence(self, screen: pygame.Surface):
        """gate 이미지 시퀀스 렌더링"""
        if not self.gate_images:
            screen.fill((30, 35, 40))
            return

        if self.gate_state == "display":
            # 현재 이미지만 표시
            if self.current_gate_index < len(self.gate_images):
                screen.blit(self.gate_images[self.current_gate_index], (0, 0))

        elif self.gate_state == "transition":
            # 크로스페이드 전환
            current_img = self.gate_images[self.current_gate_index] if self.current_gate_index < len(self.gate_images) else None
            next_idx = self.current_gate_index + 1
            next_img = self.gate_images[next_idx] if next_idx < len(self.gate_images) else None

            # ease-in-out 전환
            t = self.gate_transition_progress
            if t < 0.5:
                eased = 2 * t * t
            else:
                eased = 1 - ((-2 * t + 2) ** 2) / 2

            if current_img:
                current_img.set_alpha(int(255 * (1 - eased)))
                screen.blit(current_img, (0, 0))
                current_img.set_alpha(255)

            if next_img:
                next_img.set_alpha(int(255 * eased))
                screen.blit(next_img, (0, 0))
                next_img.set_alpha(255)

    def _render_document_phase(self, screen: pygame.Surface):
        """문서 페이즈 (캐비닛, 대화, 리뷰) 렌더링"""
        screen_w, screen_h = self.screen_size

        # 어두운 배경
        screen.fill((25, 30, 35))

        # 페이드 오버레이 (gate에서 전환 시)
        if self.fade_alpha > 0:
            fade_surf = pygame.Surface(self.screen_size, pygame.SRCALPHA)
            fade_surf.fill((0, 0, 0, int(self.fade_alpha)))
            screen.blit(fade_surf, (0, 0))

        # 캐비닛 렌더링
        if self.cabinet_y_offset > 0:
            self._render_cabinet(screen)

        # 문서 렌더링
        if self.phase == self.PHASE_DIALOGUE:
            self._render_stacked_documents(screen)
        elif self.phase == self.PHASE_DOC_REVIEW:
            self._render_review_documents(screen)

        # 대화 박스
        if self.phase == self.PHASE_DIALOGUE:
            self._render_dialogue(screen)

        # 진행 표시
        if self.phase == self.PHASE_DIALOGUE and self.documents:
            self._render_progress(screen)

    def _render_zoom_out_phase(self, screen: pygame.Surface):
        """줌아웃 페이즈 렌더링"""
        self._render_zoomed_background(screen)

        # 문서들 페이드 아웃
        progress = min(1.0, self.phase_timer / self.zoom_out_duration)
        if progress < 0.3:
            # 초반에는 문서들이 보임
            doc_alpha = int(255 * (1 - progress / 0.3))
            self._render_final_documents(screen, doc_alpha)

    def _render_zoomed_background(self, screen: pygame.Surface):
        """줌된 배경 렌더링"""
        if not self.background_original:
            screen.fill((30, 35, 40))
            return

        screen_w, screen_h = self.screen_size

        zoom_w = screen_w / self.zoom_scale
        zoom_h = screen_h / self.zoom_scale

        center_x = screen_w * self.zoom_center_x
        center_y = screen_h * self.zoom_center_y

        src_x = max(0, center_x - zoom_w / 2)
        src_y = max(0, center_y - zoom_h / 2)

        if src_x + zoom_w > screen_w:
            src_x = screen_w - zoom_w
        if src_y + zoom_h > screen_h:
            src_y = screen_h - zoom_h

        src_rect = pygame.Rect(int(src_x), int(src_y), int(zoom_w), int(zoom_h))

        try:
            zoomed = self.background_original.subsurface(src_rect)
            zoomed = pygame.transform.smoothscale(zoomed, self.screen_size)
            screen.blit(zoomed, (0, 0))
        except:
            screen.blit(self.background_original, (0, 0))

    def _render_cabinet(self, screen: pygame.Surface):
        """캐비닛 렌더링"""
        if not self.cabinet_image:
            return

        screen_w, screen_h = self.screen_size
        cab_w, cab_h = self.cabinet_image.get_size()

        cab_x = screen_w // 2 - cab_w // 2
        cab_y_base = screen_h - cab_h + 30
        cab_y_hidden = screen_h + 50
        cab_y = cab_y_hidden + (cab_y_base - cab_y_hidden) * self.cabinet_y_offset

        screen.blit(self.cabinet_image, (cab_x, int(cab_y)))

    def _render_stacked_documents(self, screen: pygame.Surface):
        """쌓이는 문서들 렌더링"""
        screen_w, screen_h = self.screen_size

        for i, doc in enumerate(self.documents):
            if not doc['visible']:
                continue

            img = doc['image']
            img_w, img_h = img.get_size()

            base_x = screen_w // 2
            base_y = screen_h // 2 - 80

            if i == self.current_doc_index:
                # 현재 문서: 솟아오르는 애니메이션
                rise_eased = 1.0 - (1.0 - self.doc_rise_progress) ** 3
                start_y = screen_h + img_h // 2
                doc_y = start_y + (base_y - start_y) * rise_eased
                alpha = int(255 * rise_eased)
                # 약간 기울임
                angle = (1 - rise_eased) * 10
            else:
                # 이전 문서들: 뒤로 쌓임
                stack_offset = (self.current_doc_index - i)
                doc_y = base_y - stack_offset * 25
                # 좌우로 약간 어긋나게
                offset_x = (stack_offset % 2) * 30 - 15
                base_x += offset_x
                alpha = max(100, 255 - stack_offset * 40)
                angle = (stack_offset % 3 - 1) * 3

            img_copy = img.copy()
            if angle != 0:
                img_copy = pygame.transform.rotate(img_copy, angle)
            img_copy.set_alpha(alpha)

            rect = img_copy.get_rect(center=(base_x, int(doc_y)))
            screen.blit(img_copy, rect)

    def _render_review_documents(self, screen: pygame.Surface):
        """문서들 즉각 정렬 렌더링 (애니메이션 포함)"""
        screen_w, screen_h = self.screen_size

        # 정렬 진행도 (0 -> 1)
        t = min(1.0, self.review_progress)
        eased = 1.0 - (1.0 - t) ** 2  # ease-out

        for i, doc in enumerate(self.documents):
            if not doc['visible']:
                continue

            img = doc['image']
            orig_w, orig_h = img.get_size()

            if i < len(self.doc_final_positions):
                pos = self.doc_final_positions[i]

                # 시작 위치 (스택 위치)
                start_x = screen_w // 2 + (i % 2 - 0.5) * 30
                start_y = screen_h // 2 - 80 + i * 15
                start_scale = 1.0

                # 최종 위치
                end_x = pos['x']
                end_y = pos['y']
                end_scale = pos['scale']

                # 보간
                cur_x = start_x + (end_x - start_x) * eased
                cur_y = start_y + (end_y - start_y) * eased
                cur_scale = start_scale + (end_scale - start_scale) * eased

                new_w = int(orig_w * cur_scale)
                new_h = int(orig_h * cur_scale)
                scaled_img = pygame.transform.smoothscale(img, (new_w, new_h))
                rect = scaled_img.get_rect(center=(int(cur_x), int(cur_y)))
                screen.blit(scaled_img, rect)

    def _render_doc_view_phase(self, screen: pygame.Surface):
        """문서 확대 보기 페이즈 렌더링"""
        screen_w, screen_h = self.screen_size

        # 어두운 배경
        screen.fill((25, 30, 35))

        # 캐비닛 (어둡게)
        if self.cabinet_image:
            cab_w, cab_h = self.cabinet_image.get_size()
            cab_x = screen_w // 2 - cab_w // 2
            cab_y = screen_h - cab_h + 30
            dark_cab = self.cabinet_image.copy()
            dark_cab.set_alpha(80)
            screen.blit(dark_cab, (cab_x, cab_y))

        # 확대 보기 중이면 배경 어둡게
        if self.viewing_doc_index >= 0:
            dark_overlay = pygame.Surface(self.screen_size, pygame.SRCALPHA)
            alpha = int(180 * self.view_zoom_progress)
            dark_overlay.fill((0, 0, 0, alpha))
            screen.blit(dark_overlay, (0, 0))

        # 정렬된 문서들 렌더링
        mouse_pos = pygame.mouse.get_pos()
        for i, doc in enumerate(self.documents):
            if not doc['visible']:
                continue
            if i >= len(self.doc_final_positions):
                continue

            img = doc['image']
            orig_w, orig_h = img.get_size()
            pos = self.doc_final_positions[i]

            # 확대 보기 중인 문서 처리
            if i == self.viewing_doc_index:
                # 확대 애니메이션
                t = self.view_zoom_progress
                eased = 1.0 - (1.0 - t) ** 2  # ease-out

                # 시작: 정렬 위치
                start_x, start_y = pos['x'], pos['y']
                start_scale = pos['scale']

                # 끝: 화면 중앙, 거의 전체화면
                end_x, end_y = screen_w // 2, screen_h // 2
                end_scale = min(screen_w * 0.85 / orig_w, screen_h * 0.85 / orig_h)

                cur_x = start_x + (end_x - start_x) * eased
                cur_y = start_y + (end_y - start_y) * eased
                cur_scale = start_scale + (end_scale - start_scale) * eased

                new_w = int(orig_w * cur_scale)
                new_h = int(orig_h * cur_scale)
                scaled_img = pygame.transform.smoothscale(img, (new_w, new_h))
                rect = scaled_img.get_rect(center=(int(cur_x), int(cur_y)))
                screen.blit(scaled_img, rect)
            else:
                # 다른 문서들 (확대 보기 중이면 숨김)
                if self.viewing_doc_index >= 0:
                    continue

                scale = pos['scale']
                new_w = int(orig_w * scale)
                new_h = int(orig_h * scale)
                scaled_img = pygame.transform.smoothscale(img, (new_w, new_h))
                rect = scaled_img.get_rect(center=(int(pos['x']), int(pos['y'])))

                # 호버 효과
                if i < len(self.doc_rects) and self.doc_rects[i].collidepoint(mouse_pos):
                    # 호버 시 밝게 + 테두리
                    pygame.draw.rect(screen, (100, 120, 140), rect.inflate(8, 8), 3, border_radius=5)
                    scaled_img.set_alpha(255)
                else:
                    scaled_img.set_alpha(220)

                screen.blit(scaled_img, rect)

        # 안내 텍스트
        if self.viewing_doc_index < 0 and "small" in self.fonts:
            hint_text = "클릭하여 문서 확대 | 빈 공간 클릭하여 계속"
            hint_surf = self.fonts["small"].render(hint_text, True, (150, 160, 170))
            hint_rect = hint_surf.get_rect(center=(screen_w // 2, screen_h - 40))
            screen.blit(hint_surf, hint_rect)
        elif self.viewing_doc_index >= 0 and self.view_state == "viewing" and "small" in self.fonts:
            hint_text = "클릭하여 닫기"
            hint_surf = self.fonts["small"].render(hint_text, True, (200, 210, 220))
            hint_rect = hint_surf.get_rect(center=(screen_w // 2, screen_h - 40))
            screen.blit(hint_surf, hint_rect)

    def _render_final_documents(self, screen: pygame.Surface, alpha: int):
        """최종 정렬된 문서들 렌더링 (페이드 아웃용)"""
        for i, doc in enumerate(self.documents):
            if not doc['visible']:
                continue

            img = doc['image']
            orig_w, orig_h = img.get_size()

            if i < len(self.doc_final_positions):
                pos = self.doc_final_positions[i]
                scale = pos['scale']
                new_w = int(orig_w * scale)
                new_h = int(orig_h * scale)
                scaled_img = pygame.transform.smoothscale(img, (new_w, new_h))
                scaled_img.set_alpha(alpha)
                rect = scaled_img.get_rect(center=(int(pos['x']), int(pos['y'])))
                screen.blit(scaled_img, rect)

    def _render_dialogue(self, screen: pygame.Surface):
        """대화 박스 렌더링 (초상화 포함)"""
        if not self.dialogue_after or self.current_dialogue_index >= len(self.dialogue_after):
            return
        dialogue = self.dialogue_after[self.current_dialogue_index]
        speaker = dialogue.get("speaker", "")
        portrait = self._get_portrait(speaker) if speaker else None
        render_dialogue_box(screen, self.screen_size, self.fonts, dialogue,
                           self.dialogue_text, self.typing_progress, self.waiting_for_click,
                           box_color=(20, 30, 40, 220), border_color=(80, 100, 80),
                           has_portrait=(portrait is not None), portrait=portrait)

    def _get_portrait(self, speaker: str) -> pygame.Surface:
        """초상화 이미지 가져오기 (캐시 사용)"""
        if speaker in self.portrait_cache:
            return self.portrait_cache[speaker]

        try:
            from mode_configs.config_story_dialogue import CHARACTER_PORTRAITS
            path = CHARACTER_PORTRAITS.get(speaker)
        except ImportError:
            path = None

        if path:
            try:
                img = pygame.image.load(path).convert_alpha()
                target_size = (120, 120)
                img = pygame.transform.smoothscale(img, target_size)
                self.portrait_cache[speaker] = img
                return img
            except Exception as e:
                print(f"WARNING: Failed to load portrait for {speaker}: {e}")

        return None

    def _render_progress(self, screen: pygame.Surface):
        """진행 상태 표시"""
        if "small" not in self.fonts:
            return

        total = len(self.documents)
        current = max(1, self.current_doc_index + 1)
        progress_text = f"문서 {current} / {total}"

        hint_surf = self.fonts["small"].render(progress_text, True, (150, 150, 150))
        screen.blit(hint_surf, (50, 30))


# =========================================================
# Act 3: 손상된 홀로그램 효과
# =========================================================
# Act 3: 불꽃 속 기록 효과 (타들어가는 사진/문서)
# =========================================================
class BurningRecordEffect:
    """
    Act 3 컷씬: 불꽃 속 기록 효과

    특징:
    - 어두운 배경에 불꽃 파티클
    - 큰 이미지가 가장자리부터 타들어감
    - 타는 애니메이션과 함께 이미지 전환
    - 연구소 화재 테마에 맞는 분위기
    """

    PHASE_FADEIN = 0
    PHASE_DISPLAY = 1         # 이미지 + 대화 동시 표시
    PHASE_BURNING = 2         # 타들어가는 애니메이션
    PHASE_FADEOUT = 3
    PHASE_DONE = 4

    def __init__(self, screen_size: tuple, film_paths: list,
                 background_path: str = None, dialogue_after: list = None,
                 sound_manager=None, special_effects: dict = None,
                 scene_id: str = "burning_scene"):
        self.screen_size = screen_size
        self.film_paths = film_paths
        self.background_path = background_path
        self.dialogue_after = dialogue_after or []
        self.sound_manager = sound_manager
        self.special_effects = special_effects or {}
        self.scene_id = scene_id

        self.is_alive = True
        self.phase = self.PHASE_FADEIN
        self.phase_timer = 0.0

        # 타이밍
        self.fadein_duration = 1.5
        self.fadeout_duration = 1.5
        self.fade_alpha = 0.0
        self.burn_duration = 2.0  # 타들어가는 시간

        # 배경
        self.background = None
        self._load_background(background_path)

        # 이미지 크기 (화면의 40% - 중간 크기, 흩어진 배치)
        screen_w, screen_h = self.screen_size
        self.img_width = int(screen_w * 0.40)
        self.img_height = int(screen_h * 0.50)

        # 이미지들
        self.records = []
        self._prepare_records()

        # 현재 이미지 인덱스
        self.current_record_index = 0

        # 흩어진 배치 위치 (폴라로이드처럼)
        self.scatter_positions = []
        self._setup_scatter_positions()

        # 타들어가는 효과
        self.burn_progress = 0.0  # 0~1 (얼마나 탔는지)
        self.burn_mask = None
        self._create_burn_mask()

        # 불꽃 파티클
        self.fire_particles = []
        self.ember_particles = []  # 불씨/재

        # 대사 관련
        self.current_dialogue_index = 0
        self.dialogue_text = ""
        self.typing_progress = 0.0
        self.typing_speed = 25.0
        self.waiting_for_click = False
        self.dialogue_complete = False

        # 폰트
        self.fonts = {}

        # 콜백
        self.on_complete = None
        self.on_replay_request = None

        # 이미지와 대화 매핑
        self._setup_dialogue_per_image()

        print(f"INFO: BurningRecordEffect created with {len(self.records)} records")

    def _load_background(self, path: str):
        """배경 이미지 로드 - 어두운 불타는 배경"""
        try:
            if path:
                img = pygame.image.load(path).convert()
                img = pygame.transform.scale(img, self.screen_size)
                # 어둡게 + 붉은 톤
                overlay = pygame.Surface(self.screen_size, pygame.SRCALPHA)
                overlay.fill((40, 10, 5, 180))
                img.blit(overlay, (0, 0))
                self.background = img
            else:
                raise Exception("No path")
        except Exception as e:
            # 기본 어두운 배경
            self.background = pygame.Surface(self.screen_size)
            self.background.fill((20, 8, 5))

    def _prepare_records(self):
        """이미지 준비 - 아주 크게"""
        for path in self.film_paths:
            record_img = None
            try:
                record_img = pygame.image.load(path).convert_alpha()
                orig_w, orig_h = record_img.get_size()
                # 꽉 차게 확대
                ratio = max(self.img_width / orig_w, self.img_height / orig_h)
                new_w, new_h = int(orig_w * ratio), int(orig_h * ratio)
                record_img = pygame.transform.smoothscale(record_img, (new_w, new_h))
                # 중앙 크롭
                crop_x = (new_w - self.img_width) // 2
                crop_y = (new_h - self.img_height) // 2
                cropped = pygame.Surface((self.img_width, self.img_height), pygame.SRCALPHA)
                cropped.blit(record_img, (-crop_x, -crop_y))
                record_img = cropped
            except Exception as e:
                print(f"WARNING: Failed to load record: {path} - {e}")
                record_img = pygame.Surface((self.img_width, self.img_height), pygame.SRCALPHA)
                record_img.fill((80, 70, 60, 200))

            filename = Path(path).name
            effect_info = self.special_effects.get(filename, {})

            self.records.append({
                'image': record_img,
                'filename': filename,
                'effect': effect_info.get('effect', None),
            })

    def _setup_scatter_positions(self):
        """폴라로이드처럼 흩어진 배치 위치 설정"""
        screen_w, screen_h = self.screen_size
        center_x, center_y = screen_w // 2, screen_h // 2

        # 각 이미지의 위치, 회전, 스케일 설정
        num_records = len(self.records)
        for _ in range(num_records):
            # 화면 중앙 근처에서 약간씩 흩어진 위치
            offset_x = random.randint(-150, 150)
            offset_y = random.randint(-100, 100)
            x = center_x - self.img_width // 2 + offset_x
            y = center_y - self.img_height // 2 + offset_y

            # 약간의 회전 (-15 ~ +15도)
            rotation = random.uniform(-15, 15)

            self.scatter_positions.append({
                'x': x,
                'y': y,
                'rotation': rotation,
                'offset_x': offset_x,
                'offset_y': offset_y,
            })

    def _create_burn_mask(self):
        """타들어가는 마스크 생성 (가장자리부터 안쪽으로)"""
        # 간단한 마스크만 생성 (실제 픽셀 단위는 성능 이슈로 생략)
        self.burn_mask = None  # 오버레이 방식 사용

    def _setup_dialogue_per_image(self):
        """이미지당 대화 수 계산"""
        num_images = len(self.records)
        num_dialogues = len(self.dialogue_after)
        if num_images == 0:
            self.dialogues_per_image = 0
        else:
            self.dialogues_per_image = max(1, (num_dialogues + num_images - 1) // num_images)

    def set_fonts(self, fonts: dict):
        self.fonts = fonts

    def update(self, dt: float):
        if not self.is_alive:
            return

        self.phase_timer += dt

        # 불꽃 파티클 업데이트 (비활성화)
        # self._update_particles(dt)

        if self.phase == self.PHASE_FADEIN:
            self.fade_alpha = min(255, (self.phase_timer / self.fadein_duration) * 255)
            if self.phase_timer >= self.fadein_duration:
                self.phase = self.PHASE_DISPLAY
                self.phase_timer = 0.0
                self._start_dialogue()

        elif self.phase == self.PHASE_DISPLAY:
            self._update_dialogue(dt)

        elif self.phase == self.PHASE_BURNING:
            # 타들어가는 진행
            self.burn_progress = min(1.0, self.phase_timer / self.burn_duration)
            # 불꽃 파티클 비활성화
            # self._spawn_fire_particles(5)

            if self.burn_progress >= 1.0:
                # 다음 이미지로 전환
                self.current_record_index += 1
                self.burn_progress = 0.0
                self.phase_timer = 0.0

                if self.current_record_index >= len(self.records):
                    self.phase = self.PHASE_FADEOUT
                else:
                    self.phase = self.PHASE_DISPLAY
                    self._start_dialogue()

        elif self.phase == self.PHASE_FADEOUT:
            progress = self.phase_timer / self.fadeout_duration
            self.fade_alpha = 255 * (1.0 - progress)
            if self.phase_timer >= self.fadeout_duration:
                self.phase = self.PHASE_DONE
                self.is_alive = False
                if self.on_complete:
                    self.on_complete()

    def _update_particles(self, dt: float):
        """파티클 업데이트"""
        # 기본 불꽃 파티클 생성
        if self.phase in [self.PHASE_DISPLAY, self.PHASE_BURNING]:
            if random.random() < 0.3:
                self._spawn_fire_particles(1)

        # 파티클 이동 및 소멸
        for p in self.fire_particles[:]:
            p['y'] -= p['speed'] * dt
            p['life'] -= dt
            p['x'] += random.uniform(-30, 30) * dt
            if p['life'] <= 0:
                self.fire_particles.remove(p)

        for p in self.ember_particles[:]:
            p['y'] -= p['speed'] * dt * 0.5
            p['x'] += random.uniform(-50, 50) * dt
            p['life'] -= dt
            if p['life'] <= 0:
                self.ember_particles.remove(p)

    def _spawn_fire_particles(self, count: int):
        """불꽃 파티클 생성 (현재 이미지 위치 기준)"""
        if self.current_record_index >= len(self.scatter_positions):
            return

        pos = self.scatter_positions[self.current_record_index]
        img_x = pos['x']
        img_y = pos['y']

        for _ in range(count):
            # 이미지 가장자리 근처에서 생성
            edge = random.choice(['top', 'bottom', 'left', 'right'])
            if edge == 'top':
                x = img_x + random.randint(0, self.img_width)
                y = img_y
            elif edge == 'bottom':
                x = img_x + random.randint(0, self.img_width)
                y = img_y + self.img_height
            elif edge == 'left':
                x = img_x
                y = img_y + random.randint(0, self.img_height)
            else:
                x = img_x + self.img_width
                y = img_y + random.randint(0, self.img_height)

            self.fire_particles.append({
                'x': x,
                'y': y,
                'speed': random.uniform(80, 200),
                'size': random.randint(3, 12),
                'life': random.uniform(0.5, 1.5),
                'color': random.choice([
                    (255, 200, 50),   # 밝은 노랑
                    (255, 150, 30),   # 주황
                    (255, 100, 20),   # 진한 주황
                    (255, 60, 10),    # 빨강-주황
                ])
            })

            # 불씨도 생성
            if random.random() < 0.3:
                self.ember_particles.append({
                    'x': x + random.randint(-20, 20),
                    'y': y,
                    'speed': random.uniform(30, 80),
                    'size': random.randint(1, 3),
                    'life': random.uniform(1.0, 3.0),
                })

    def _start_dialogue(self):
        """현재 대화 시작"""
        if self.current_dialogue_index < len(self.dialogue_after):
            self.dialogue_text = self.dialogue_after[self.current_dialogue_index].get("text", "")
            self.typing_progress = 0.0
            self.waiting_for_click = False
            self.dialogue_complete = False
        else:
            self.dialogue_complete = True

    def _update_dialogue(self, dt: float):
        """대사 업데이트"""
        if self.current_dialogue_index >= len(self.dialogue_after):
            self.dialogue_complete = True
            return

        if not self.waiting_for_click:
            self.typing_progress += dt * self.typing_speed
            if self.typing_progress >= len(self.dialogue_text):
                self.typing_progress = len(self.dialogue_text)
                self.waiting_for_click = True

    def _advance_to_next(self):
        """다음 대화/이미지로 진행"""
        self.current_dialogue_index += 1

        # 일정 대화마다 타들어가기 시작
        if self.dialogues_per_image > 0:
            expected_image = self.current_dialogue_index // self.dialogues_per_image
            if expected_image > self.current_record_index and self.current_record_index < len(self.records) - 1:
                self.phase = self.PHASE_BURNING
                self.phase_timer = 0.0
                self.burn_progress = 0.0
                return

        if self.current_dialogue_index < len(self.dialogue_after):
            self._start_dialogue()
        else:
            self.dialogue_complete = True
            if self.current_record_index >= len(self.records) - 1:
                self.phase = self.PHASE_FADEOUT
                self.phase_timer = 0.0

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.phase == self.PHASE_DISPLAY:
                if self.waiting_for_click:
                    self._advance_to_next()
                else:
                    self.typing_progress = len(self.dialogue_text)
                    self.waiting_for_click = True
                return True

        elif event.type == pygame.KEYDOWN:
            if event.key in [pygame.K_SPACE, pygame.K_RETURN]:
                return self.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1))

        return False

    def render(self, screen: pygame.Surface):
        # 배경
        if self.background:
            bg_copy = self.background.copy()
            if self.fade_alpha < 255:
                bg_copy.set_alpha(int(self.fade_alpha))
            screen.blit(bg_copy, (0, 0))

        # 이미지 렌더링
        if self.phase in [self.PHASE_DISPLAY, self.PHASE_BURNING]:
            self._render_burning_record(screen)

        # 불꽃 파티클 (비활성화)
        # self._render_particles(screen)

        # 비네트 (어두운 가장자리)
        self._render_vignette(screen)

        # 대사
        if self.phase == self.PHASE_DISPLAY:
            self._render_dialogue(screen)

    def _render_burning_record(self, screen: pygame.Surface):
        """타들어가는 기록 이미지 렌더링 (폴라로이드처럼 흩어진 배치)"""
        if self.current_record_index >= len(self.records):
            return

        # 현재 이미지의 흩어진 위치 가져오기
        pos = self.scatter_positions[self.current_record_index]
        img_x = pos['x']
        img_y = pos['y']
        rotation = pos['rotation']

        record = self.records[self.current_record_index]
        img = record['image'].copy()

        # 타들어가는 효과 적용
        if self.phase == self.PHASE_BURNING and self.burn_progress > 0:
            self._apply_burn_effect(img)

        # 테두리가 있는 사진 서피스 생성 (탄 종이 느낌)
        border_size = 15
        photo_surf = pygame.Surface((self.img_width + border_size * 2, self.img_height + border_size * 2), pygame.SRCALPHA)

        # 탄 종이 테두리 (불규칙한 갈색)
        pygame.draw.rect(photo_surf, (70, 50, 35, 230), (0, 0, photo_surf.get_width(), photo_surf.get_height()), border_radius=3)
        # 탄 자국 테두리
        pygame.draw.rect(photo_surf, (40, 25, 15, 200), (0, 0, photo_surf.get_width(), photo_surf.get_height()), 3, border_radius=3)

        # 이미지 배치
        photo_surf.blit(img, (border_size, border_size))

        # 회전 적용
        if rotation != 0:
            photo_surf = pygame.transform.rotate(photo_surf, rotation)

        # 페이드 적용
        if self.fade_alpha < 255:
            photo_surf.set_alpha(int(self.fade_alpha))

        # 회전 후 중앙 정렬을 위한 위치 조정
        rotated_rect = photo_surf.get_rect(center=(img_x + self.img_width // 2, img_y + self.img_height // 2))
        screen.blit(photo_surf, rotated_rect)

        # 타는 중이면 가장자리에 빛나는 효과
        if self.phase == self.PHASE_BURNING:
            self._render_burning_edge(screen, rotated_rect.x, rotated_rect.y, photo_surf.get_width(), photo_surf.get_height())

    def _apply_burn_effect(self, img: pygame.Surface):
        """이미지에 타들어가는 효과 적용"""
        # 간단한 구현: 가장자리부터 투명하게
        w, h = img.get_size()
        center_x, center_y = w // 2, h // 2
        max_dist = math.sqrt(center_x**2 + center_y**2)

        # burn_progress에 따라 얼마나 탔는지
        burn_radius = max_dist * (1.0 - self.burn_progress)

        # 픽셀 단위 처리는 느리므로 오버레이로 표현
        burn_overlay = pygame.Surface((w, h), pygame.SRCALPHA)

        # 탄 영역 (검은색 + 투명)
        for i in range(20):  # 여러 원으로 그라데이션
            radius = int(burn_radius + i * 10)
            alpha = int(min(255, (i / 20) * 255 * self.burn_progress))
            color = (20, 10, 5, alpha)
            pygame.draw.circle(burn_overlay, color, (center_x, center_y), radius, 5)

        # 가장자리에 주황/빨간 불꽃 색
        edge_radius = int(burn_radius)
        if edge_radius > 10:
            pygame.draw.circle(burn_overlay, (255, 100, 30, 100), (center_x, center_y), edge_radius + 5, 8)
            pygame.draw.circle(burn_overlay, (255, 200, 50, 80), (center_x, center_y), edge_radius + 2, 4)

        img.blit(burn_overlay, (0, 0))

    def _render_burning_edge(self, screen: pygame.Surface, img_x: int, img_y: int, width: int = None, height: int = None):
        """타는 가장자리 빛 효과"""
        w = width or self.img_width
        h = height or self.img_height
        center_x = img_x + w // 2
        center_y = img_y + h // 2
        max_dist = math.sqrt((w // 2)**2 + (h // 2)**2)
        burn_radius = int(max_dist * (1.0 - self.burn_progress))

        glow_surf = pygame.Surface(self.screen_size, pygame.SRCALPHA)
        # 빛나는 원 (불꽃 색)
        for i in range(5):
            alpha = 40 - i * 7
            pygame.draw.circle(glow_surf, (255, 150, 50, max(0, alpha)), (center_x, center_y), burn_radius + i * 15, 4)

        screen.blit(glow_surf, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

    def _render_particles(self, screen: pygame.Surface):
        """파티클 렌더링"""
        for p in self.fire_particles:
            alpha = int(255 * (p['life'] / 1.5))
            color = (*p['color'][:3], min(255, alpha))
            surf = pygame.Surface((p['size'] * 2, p['size'] * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, color, (p['size'], p['size']), p['size'])
            screen.blit(surf, (int(p['x'] - p['size']), int(p['y'] - p['size'])), special_flags=pygame.BLEND_RGBA_ADD)

        for p in self.ember_particles:
            alpha = int(200 * (p['life'] / 3.0))
            color = (255, 180, 100, min(255, alpha))
            surf = pygame.Surface((p['size'] * 2, p['size'] * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, color, (p['size'], p['size']), p['size'])
            screen.blit(surf, (int(p['x'] - p['size']), int(p['y'] - p['size'])))

    def _render_vignette(self, screen: pygame.Surface):
        """비네트 효과 (붉은 톤)"""
        vignette = pygame.Surface(self.screen_size, pygame.SRCALPHA)
        screen_w, screen_h = self.screen_size
        center_x, center_y = screen_w // 2, screen_h // 2
        max_dist = math.sqrt(center_x**2 + center_y**2)

        # 가장자리 어둡게 + 붉은 톤
        for i in range(10):
            radius = int(max_dist * (1.0 - i * 0.08))
            alpha = i * 15
            pygame.draw.circle(vignette, (30, 10, 5, alpha), (center_x, center_y), radius, 50)

        screen.blit(vignette, (0, 0))

    def _render_dialogue(self, screen: pygame.Surface):
        """대사 박스 렌더링 (초상화 포함)"""
        if not self.dialogue_after or self.current_dialogue_index >= len(self.dialogue_after):
            if self.dialogue_complete and self.current_record_index < len(self.records) - 1:
                self._render_hint(screen, "클릭하여 다음 기록")
            elif self.dialogue_complete:
                self._render_hint(screen, "클릭하여 계속")
            return
        dialogue = self.dialogue_after[self.current_dialogue_index]
        speaker = dialogue.get("speaker", "")
        portrait = self._get_portrait(speaker) if speaker else None
        render_dialogue_box(screen, self.screen_size, self.fonts, dialogue,
                           self.dialogue_text, self.typing_progress, self.waiting_for_click,
                           box_color=(30, 15, 10, 220), border_color=(150, 80, 40, 150),
                           text_color=(255, 240, 220), box_height=160,
                           has_portrait=(portrait is not None), portrait=portrait)

    def _get_portrait(self, speaker: str) -> pygame.Surface:
        """초상화 이미지 가져오기 (캐시 사용)"""
        if speaker in self.portrait_cache:
            return self.portrait_cache[speaker]

        try:
            from mode_configs.config_story_dialogue import CHARACTER_PORTRAITS
            path = CHARACTER_PORTRAITS.get(speaker)
        except ImportError:
            path = None

        if path:
            try:
                img = pygame.image.load(path).convert_alpha()
                target_size = (120, 120)
                img = pygame.transform.smoothscale(img, target_size)
                self.portrait_cache[speaker] = img
                return img
            except Exception as e:
                print(f"WARNING: Failed to load portrait for {speaker}: {e}")

        return None

    def _render_hint(self, screen: pygame.Surface, text: str):
        if "small" not in self.fonts:
            return
        hint_surf = self.fonts["small"].render(text, True, (255, 200, 150))
        x = self.screen_size[0] // 2 - hint_surf.get_width() // 2
        y = self.screen_size[1] - 50
        screen.blit(hint_surf, (x, y))


# DamagedHologramEffect는 BurningRecordEffect의 별칭으로 유지 (호환성)
DamagedHologramEffect = BurningRecordEffect


# =========================================================
# Act 3: 필름 릴 효과 - 이미지 원본 색상 100% 유지
# =========================================================
class FilmReelEffect:
    """
    Act 3 컷씬: 필름 릴 효과

    특징:
    - 이미지 원본 색상 100% 유지 (틴트 없음!)
    - 좌우에 스프로킷 구멍이 있는 필름 프레임
    - 필름이 위에서 아래로 롤링하는 애니메이션
    - 프레임 번호 표시 (FRAME 001)
    - 약한 비네트와 필름 스크래치 효과
    - 간헐적 깜빡임 (옛날 영사기 느낌)
    """

    PHASE_FADEIN = 0
    PHASE_FILM_ROLL = 1      # 필름이 위에서 내려옴
    PHASE_DISPLAY = 2        # 이미지 표시, 대화
    PHASE_FILM_ADVANCE = 3   # 다음 프레임으로 전환 (위로 롤아웃)
    PHASE_FADEOUT = 4
    PHASE_DONE = 5

    def __init__(self, screen_size: tuple, film_paths: list,
                 background_path: str = None, dialogue_after: list = None,
                 sound_manager=None, special_effects: dict = None,
                 scene_id: str = "film_scene"):
        self.screen_size = screen_size
        self.film_paths = film_paths
        self.background_path = background_path
        self.dialogue_after = dialogue_after or []
        self.sound_manager = sound_manager
        self.special_effects = special_effects or {}
        self.scene_id = scene_id

        self.is_alive = True
        self.phase = self.PHASE_FADEIN
        self.phase_timer = 0.0

        # 타이밍
        self.fadein_duration = 1.5
        self.fadeout_duration = 1.5
        self.roll_duration = 0.8       # 롤링 애니메이션 시간
        self.advance_duration = 0.6    # 다음 프레임 전환 시간
        self.fade_alpha = 0.0

        # 배경 (어둡게 처리하되 붉은 톤은 줄임)
        self.background = None
        self._load_background(background_path)

        # 필름 프레임 크기 (화면의 50% 정도)
        screen_w, screen_h = self.screen_size
        self.film_width = int(screen_w * 0.45)
        self.film_height = int(screen_h * 0.55)

        # 스프로킷 구멍 설정
        self.sprocket_margin = 50      # 좌우 여백 (구멍 영역)
        self.sprocket_hole_radius = 12
        self.sprocket_hole_spacing = 40

        # 필름 전체 프레임 크기 (스프로킷 포함)
        self.frame_width = self.film_width + self.sprocket_margin * 2
        self.frame_height = self.film_height + 80  # 하단에 프레임 번호 공간

        # 이미지들
        self.films = []
        self._prepare_films()

        # 현재 프레임 인덱스
        self.current_frame_index = 0

        # 롤링 애니메이션용
        self.roll_offset = 0.0  # 현재 롤링 오프셋 (픽셀)

        # 필름 효과
        self.flicker_timer = 0.0
        self.flicker_alpha = 0       # 깜빡임 알파 (0~30 정도)
        self.scratch_lines = []      # 스크래치 라인들
        self._generate_scratch_lines()

        # 대사 관련
        self.current_dialogue_index = 0
        self.dialogue_text = ""
        self.typing_progress = 0.0
        self.typing_speed = 25.0
        self.waiting_for_click = False
        self.dialogue_complete = False

        # 폰트
        self.fonts = {}

        # 콜백
        self.on_complete = None
        self.on_replay_request = None

        # 이미지와 대화 매핑
        self._setup_dialogue_per_image()

        print(f"INFO: FilmReelEffect created with {len(self.films)} frames")

    def _load_background(self, path: str):
        """배경 이미지 로드 - 어둡게 (붉은 톤 최소화)"""
        try:
            if path:
                img = pygame.image.load(path).convert()
                img = pygame.transform.scale(img, self.screen_size)
                # 어둡게만 (붉은 톤 없이)
                overlay = pygame.Surface(self.screen_size, pygame.SRCALPHA)
                overlay.fill((20, 20, 25, 200))
                img.blit(overlay, (0, 0))
                self.background = img
            else:
                raise Exception("No path")
        except Exception as e:
            # 기본 어두운 배경
            self.background = pygame.Surface(self.screen_size)
            self.background.fill((15, 15, 20))

    def _prepare_films(self):
        """필름 이미지 준비 - 원본 색상 유지!"""
        for path in self.film_paths:
            film_img = None
            try:
                film_img = pygame.image.load(path).convert_alpha()
                orig_w, orig_h = film_img.get_size()
                # 비율 유지하며 확대
                ratio = max(self.film_width / orig_w, self.film_height / orig_h)
                new_w, new_h = int(orig_w * ratio), int(orig_h * ratio)
                film_img = pygame.transform.smoothscale(film_img, (new_w, new_h))
                # 중앙 크롭
                crop_x = (new_w - self.film_width) // 2
                crop_y = (new_h - self.film_height) // 2
                cropped = pygame.Surface((self.film_width, self.film_height), pygame.SRCALPHA)
                cropped.blit(film_img, (-crop_x, -crop_y))
                film_img = cropped
            except Exception as e:
                print(f"WARNING: Failed to load film: {path} - {e}")
                film_img = pygame.Surface((self.film_width, self.film_height), pygame.SRCALPHA)
                film_img.fill((60, 60, 65, 200))

            filename = Path(path).name
            effect_info = self.special_effects.get(filename, {})

            self.films.append({
                'image': film_img,
                'filename': filename,
                'effect': effect_info.get('effect', None),
            })

    def _generate_scratch_lines(self):
        """필름 스크래치 라인 생성"""
        screen_h = self.screen_size[1]
        # 3~5개의 세로 스크래치 라인
        for _ in range(random.randint(3, 5)):
            self.scratch_lines.append({
                'x': random.randint(100, self.screen_size[0] - 100),
                'alpha': random.randint(15, 40),
                'width': random.randint(1, 2),
            })

    def _setup_dialogue_per_image(self):
        """이미지당 대화 수 계산"""
        num_images = len(self.films)
        num_dialogues = len(self.dialogue_after)
        if num_images == 0:
            self.dialogues_per_image = 0
        else:
            self.dialogues_per_image = max(1, (num_dialogues + num_images - 1) // num_images)

    def set_fonts(self, fonts: dict):
        self.fonts = fonts

    def update(self, dt: float):
        if not self.is_alive:
            return

        self.phase_timer += dt

        # 필름 깜빡임 효과
        self._update_flicker(dt)

        if self.phase == self.PHASE_FADEIN:
            self.fade_alpha = min(255, (self.phase_timer / self.fadein_duration) * 255)
            if self.phase_timer >= self.fadein_duration:
                self.phase = self.PHASE_FILM_ROLL
                self.phase_timer = 0.0
                self.roll_offset = -self.frame_height  # 화면 위에서 시작

        elif self.phase == self.PHASE_FILM_ROLL:
            # 필름이 위에서 아래로 롤링
            progress = min(1.0, self.phase_timer / self.roll_duration)
            eased = self._ease_out_cubic(progress)
            self.roll_offset = -self.frame_height * (1.0 - eased)

            if progress >= 1.0:
                self.roll_offset = 0
                self.phase = self.PHASE_DISPLAY
                self.phase_timer = 0.0
                self._start_dialogue()

        elif self.phase == self.PHASE_DISPLAY:
            self._update_dialogue(dt)

        elif self.phase == self.PHASE_FILM_ADVANCE:
            # 현재 프레임이 위로 롤아웃
            progress = min(1.0, self.phase_timer / self.advance_duration)
            eased = self._ease_in_cubic(progress)
            self.roll_offset = self.frame_height * eased

            if progress >= 1.0:
                self.current_frame_index += 1
                self.roll_offset = -self.frame_height

                if self.current_frame_index >= len(self.films):
                    self.phase = self.PHASE_FADEOUT
                    self.phase_timer = 0.0
                else:
                    # 다음 프레임 롤인
                    self.phase = self.PHASE_FILM_ROLL
                    self.phase_timer = 0.0

        elif self.phase == self.PHASE_FADEOUT:
            progress = self.phase_timer / self.fadeout_duration
            self.fade_alpha = 255 * (1.0 - progress)
            if self.phase_timer >= self.fadeout_duration:
                self.phase = self.PHASE_DONE
                self.is_alive = False
                if self.on_complete:
                    self.on_complete()

    def _ease_out_cubic(self, t: float) -> float:
        """Ease-out cubic for smooth deceleration"""
        return 1 - pow(1 - t, 3)

    def _ease_in_cubic(self, t: float) -> float:
        """Ease-in cubic for smooth acceleration"""
        return t * t * t

    def _update_flicker(self, dt: float):
        """필름 깜빡임 업데이트"""
        self.flicker_timer += dt
        # 간헐적으로 깜빡임 (2~4초마다)
        if random.random() < dt * 0.3:  # 약 30% 확률/초
            self.flicker_alpha = random.randint(10, 30)
        else:
            self.flicker_alpha = max(0, self.flicker_alpha - dt * 100)

    def _start_dialogue(self):
        """현재 대화 시작"""
        if self.current_dialogue_index < len(self.dialogue_after):
            self.dialogue_text = self.dialogue_after[self.current_dialogue_index].get("text", "")
            self.typing_progress = 0.0
            self.waiting_for_click = False
            self.dialogue_complete = False
        else:
            self.dialogue_complete = True

    def _update_dialogue(self, dt: float):
        """대사 업데이트"""
        if self.current_dialogue_index >= len(self.dialogue_after):
            self.dialogue_complete = True
            return

        if not self.waiting_for_click:
            self.typing_progress += dt * self.typing_speed
            if self.typing_progress >= len(self.dialogue_text):
                self.typing_progress = len(self.dialogue_text)
                self.waiting_for_click = True

    def _advance_to_next(self):
        """다음 대화/이미지로 진행"""
        self.current_dialogue_index += 1

        # 일정 대화마다 다음 프레임으로 전환
        if self.dialogues_per_image > 0:
            expected_image = self.current_dialogue_index // self.dialogues_per_image
            if expected_image > self.current_frame_index and self.current_frame_index < len(self.films) - 1:
                self.phase = self.PHASE_FILM_ADVANCE
                self.phase_timer = 0.0
                return

        if self.current_dialogue_index < len(self.dialogue_after):
            self._start_dialogue()
        else:
            self.dialogue_complete = True
            if self.current_frame_index >= len(self.films) - 1:
                self.phase = self.PHASE_FADEOUT
                self.phase_timer = 0.0

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.phase == self.PHASE_DISPLAY:
                if self.waiting_for_click:
                    self._advance_to_next()
                else:
                    self.typing_progress = len(self.dialogue_text)
                    self.waiting_for_click = True
                return True

        elif event.type == pygame.KEYDOWN:
            if event.key in [pygame.K_SPACE, pygame.K_RETURN]:
                return self.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1))

        return False

    def render(self, screen: pygame.Surface):
        # 배경
        if self.background:
            bg_copy = self.background.copy()
            if self.fade_alpha < 255:
                bg_copy.set_alpha(int(self.fade_alpha))
            screen.blit(bg_copy, (0, 0))

        # 필름 프레임 렌더링
        if self.phase in [self.PHASE_FILM_ROLL, self.PHASE_DISPLAY, self.PHASE_FILM_ADVANCE]:
            self._render_film_frame(screen)

        # 필름 스크래치
        self._render_scratches(screen)

        # 필름 깜빡임
        self._render_flicker(screen)

        # 비네트 (약하게)
        self._render_vignette(screen)

        # 대사
        if self.phase == self.PHASE_DISPLAY:
            self._render_dialogue(screen)

    def _render_film_frame(self, screen: pygame.Surface):
        """필름 프레임 렌더링 - 이미지 원본 그대로!"""
        if self.current_frame_index >= len(self.films):
            return

        screen_w, screen_h = self.screen_size
        center_x = screen_w // 2
        center_y = screen_h // 2

        # 프레임 위치 (롤링 오프셋 적용)
        frame_x = center_x - self.frame_width // 2
        frame_y = center_y - self.frame_height // 2 + int(self.roll_offset)

        # 필름 프레임 서피스 생성
        frame_surf = pygame.Surface((self.frame_width, self.frame_height), pygame.SRCALPHA)

        # 필름 베이스 (검은색 필름 스트립)
        pygame.draw.rect(frame_surf, (25, 25, 30, 255),
                        (0, 0, self.frame_width, self.frame_height))

        # 좌우 스프로킷 구멍
        hole_start_y = 30
        hole_end_y = self.frame_height - 30
        for y in range(hole_start_y, hole_end_y, self.sprocket_hole_spacing):
            # 왼쪽 구멍
            pygame.draw.circle(frame_surf, (10, 10, 12, 255),
                             (self.sprocket_margin // 2, y), self.sprocket_hole_radius)
            # 구멍 테두리
            pygame.draw.circle(frame_surf, (40, 40, 45, 255),
                             (self.sprocket_margin // 2, y), self.sprocket_hole_radius, 2)
            # 오른쪽 구멍
            pygame.draw.circle(frame_surf, (10, 10, 12, 255),
                             (self.frame_width - self.sprocket_margin // 2, y), self.sprocket_hole_radius)
            pygame.draw.circle(frame_surf, (40, 40, 45, 255),
                             (self.frame_width - self.sprocket_margin // 2, y), self.sprocket_hole_radius, 2)

        # 이미지 영역 배경 (약간 밝은 회색)
        img_area_x = self.sprocket_margin
        img_area_y = 20
        pygame.draw.rect(frame_surf, (45, 45, 50, 255),
                        (img_area_x, img_area_y, self.film_width, self.film_height))

        # 이미지 원본 그대로 표시! (틴트 없음!)
        film = self.films[self.current_frame_index]
        frame_surf.blit(film['image'], (img_area_x, img_area_y))

        # 이미지 테두리
        pygame.draw.rect(frame_surf, (60, 60, 65, 255),
                        (img_area_x, img_area_y, self.film_width, self.film_height), 2)

        # 프레임 번호 텍스트
        frame_num_y = img_area_y + self.film_height + 15
        if "small" in self.fonts:
            frame_text = f"FRAME {self.current_frame_index + 1:03d}"
            text_surf = self.fonts["small"].render(frame_text, True, (180, 170, 150))
            text_x = self.frame_width // 2 - text_surf.get_width() // 2
            frame_surf.blit(text_surf, (text_x, frame_num_y))

        # 페이드 적용
        if self.fade_alpha < 255:
            frame_surf.set_alpha(int(self.fade_alpha))

        screen.blit(frame_surf, (frame_x, frame_y))

    def _render_scratches(self, screen: pygame.Surface):
        """필름 스크래치 렌더링"""
        for scratch in self.scratch_lines:
            color = (200, 190, 170, scratch['alpha'])
            scratch_surf = pygame.Surface((scratch['width'], self.screen_size[1]), pygame.SRCALPHA)
            scratch_surf.fill(color)
            screen.blit(scratch_surf, (scratch['x'], 0))

    def _render_flicker(self, screen: pygame.Surface):
        """필름 깜빡임 렌더링"""
        if self.flicker_alpha > 0:
            flicker_surf = pygame.Surface(self.screen_size, pygame.SRCALPHA)
            flicker_surf.fill((255, 250, 240, self.flicker_alpha))
            screen.blit(flicker_surf, (0, 0))

    def _render_vignette(self, screen: pygame.Surface):
        """비네트 효과 (약하게, 중립 색상)"""
        vignette = pygame.Surface(self.screen_size, pygame.SRCALPHA)
        screen_w, screen_h = self.screen_size
        center_x, center_y = screen_w // 2, screen_h // 2
        max_dist = math.sqrt(center_x**2 + center_y**2)

        # 가장자리만 약간 어둡게 (중립 톤)
        for i in range(8):
            radius = int(max_dist * (1.0 - i * 0.08))
            alpha = i * 10  # 약한 비네트
            pygame.draw.circle(vignette, (15, 15, 20, alpha), (center_x, center_y), radius, 60)

        screen.blit(vignette, (0, 0))

    def _render_dialogue(self, screen: pygame.Surface):
        """대사 박스 렌더링 (초상화 포함)"""
        if not self.dialogue_after or self.current_dialogue_index >= len(self.dialogue_after):
            if self.dialogue_complete and self.current_frame_index < len(self.films) - 1:
                self._render_hint(screen, "클릭하여 다음 프레임")
            elif self.dialogue_complete:
                self._render_hint(screen, "클릭하여 계속")
            return
        dialogue = self.dialogue_after[self.current_dialogue_index]
        speaker = dialogue.get("speaker", "")
        portrait = self._get_portrait(speaker) if speaker else None

        # 중립적인 어두운 색상의 대화 상자
        render_dialogue_box(screen, self.screen_size, self.fonts, dialogue,
                           self.dialogue_text, self.typing_progress, self.waiting_for_click,
                           box_color=(25, 25, 30, 230), border_color=(80, 80, 90, 180),
                           text_color=(240, 235, 220), box_height=160,
                           has_portrait=(portrait is not None), portrait=portrait)

    def _render_hint(self, screen: pygame.Surface, text: str):
        if "small" not in self.fonts:
            return
        hint_surf = self.fonts["small"].render(text, True, (180, 175, 160))
        x = self.screen_size[0] // 2 - hint_surf.get_width() // 2
        y = self.screen_size[1] - 50
        screen.blit(hint_surf, (x, y))

    def _reset_for_replay(self):
        """리플레이를 위한 상태 초기화"""
        self.phase = self.PHASE_FADEIN
        self.phase_timer = 0.0
        self.fade_alpha = 0.0
        self.current_frame_index = 0
        self.roll_offset = 0.0
        self.current_dialogue_index = 0
        self.dialogue_text = ""
        self.typing_progress = 0.0
        self.waiting_for_click = False
        self.dialogue_complete = False
        self.is_alive = True


# =========================================================
# Act 4: 깨진 거울 파편 효과 (BaseCutsceneEffect 상속)
# =========================================================
class ShatteredMirrorEffect(BaseCutsceneEffect):
    """
    Act 4 컷씬: 깨진 거울/기억 파편 효과

    특징:
    - 검은 배경에 떠다니는 거울 파편
    - 각 파편 안에 다른 이미지
    - 파편들이 천천히 회전하며 빛 반사
    - 마지막에 합쳐져서 완전한 그림 형성
    """

    # 추가 페이즈 상수 (베이스 클래스 확장)
    PHASE_FRAGMENTS = 10
    PHASE_ASSEMBLE = 11

    def __init__(self, screen_size: tuple, fragment_paths: list,
                 background_path: str = None, dialogue_after: list = None,
                 sound_manager=None, special_effects: dict = None,
                 scene_id: str = "mirror_scene"):
        # 베이스 클래스 초기화
        super().__init__(screen_size, background_path, dialogue_after,
                        sound_manager, special_effects, scene_id)

        self.fragment_paths = fragment_paths
        self.typing_speed = 25.0  # 오버라이드

        # 어두운 배경 오버레이 적용
        if background_path:
            self._load_background(background_path, overlay_alpha=220)

        # 파편 관련
        self.fragments = []
        self._prepare_fragments()

        self.frag_animation_progress = 0.0
        self.assemble_duration = 3.0

    def _prepare_fragments(self):
        """파편 이미지 준비"""
        screen_w, screen_h = self.screen_size
        frag_size = int(min(screen_w, screen_h) * 0.25)

        # 파편 위치들 (원형 배치)
        center_x, center_y = screen_w // 2, screen_h // 2 - 30
        radius = min(screen_w, screen_h) * 0.25

        for i, path in enumerate(self.fragment_paths):
            frag_img = None
            try:
                frag_img = pygame.image.load(path).convert_alpha()
                frag_img = pygame.transform.smoothscale(frag_img, (frag_size, frag_size))
            except Exception as e:
                print(f"WARNING: Failed to load fragment: {path} - {e}")
                frag_img = pygame.Surface((frag_size, frag_size), pygame.SRCALPHA)
                frag_img.fill((100, 100, 120, 200))

            filename = Path(path).name
            effect_info = self.special_effects.get(filename, {})
            is_final = effect_info.get('is_final', False)

            # 원형 배치 또는 최종 이미지
            if is_final:
                target_x, target_y = center_x, center_y
                start_x, start_y = center_x, center_y
            else:
                angle = (2 * math.pi * i) / max(len(self.fragment_paths) - 1, 1)
                target_x = center_x + radius * math.cos(angle)
                target_y = center_y + radius * math.sin(angle)
                # 시작 위치 (화면 밖에서)
                start_x = center_x + (radius * 2) * math.cos(angle)
                start_y = center_y + (radius * 2) * math.sin(angle)

            self.fragments.append({
                'image': frag_img,
                'filename': filename,
                'is_final': is_final,
                'x': start_x,
                'y': start_y,
                'target_x': target_x,
                'target_y': target_y,
                'start_x': start_x,
                'start_y': start_y,
                'alpha': 0,
                'rotation': random.uniform(0, 360),
                'rotation_speed': random.uniform(-30, 30),
                'scale': 0.5 if is_final else 1.0,
                'glow': 0.0,
            })

    # set_fonts는 베이스 클래스에서 상속

    def _on_fadein_complete(self):
        """페이드인 완료 후 파편 등장 페이즈로 전환"""
        self.phase = self.PHASE_FRAGMENTS
        self.phase_timer = 0.0

    def update(self, dt: float):
        """업데이트 - 파편 고유 로직 추가"""
        if not self.is_alive:
            return

        self.phase_timer += dt

        # 파편 회전 (항상 업데이트)
        for frag in self.fragments:
            if not frag['is_final']:
                frag['rotation'] += frag['rotation_speed'] * dt
            frag['glow'] = 0.5 + 0.5 * math.sin(self.phase_timer * 2 + frag['rotation'])

        # 페이즈별 처리
        if self.phase == self.PHASE_FADEIN:
            if self._update_fadein(dt):
                self._on_fadein_complete()

        elif self.phase == self.PHASE_FRAGMENTS:
            self._update_fragments(dt)

        elif self.phase == self.PHASE_ASSEMBLE:
            self._update_assemble(dt)

        elif self.phase == self.PHASE_DIALOGUE:
            if self._update_dialogue(dt):
                self._transition_to_fadeout()

        elif self.phase == self.PHASE_FADEOUT:
            if self._update_fadeout(dt):
                self._on_fadeout_complete()

    def _update_fragments(self, dt: float):
        """파편 등장 애니메이션"""
        self.frag_animation_progress += dt * 1.2
        visible_count = int(self.frag_animation_progress)

        for i, frag in enumerate(self.fragments):
            if frag['is_final']:
                continue
            if i < visible_count:
                progress = min(1.0, self.frag_animation_progress - i)
                eased = 1.0 - (1.0 - progress) ** 3
                frag['alpha'] = int(220 * eased)
                frag['x'] = frag['start_x'] + (frag['target_x'] - frag['start_x']) * eased
                frag['y'] = frag['start_y'] + (frag['target_y'] - frag['start_y']) * eased

        # 모든 파편 등장 후 클릭 대기
        non_final_count = sum(1 for f in self.fragments if not f['is_final'])
        if visible_count >= non_final_count:
            self.waiting_for_click = True

    def _update_assemble(self, dt: float):
        """파편 조립 애니메이션"""
        progress = min(1.0, self.phase_timer / self.assemble_duration)
        eased = 1.0 - (1.0 - progress) ** 2

        # 파편들이 중앙으로 모임
        for frag in self.fragments:
            if not frag['is_final']:
                frag['alpha'] = int(220 * (1.0 - progress))
                frag['scale'] = 1.0 - 0.5 * progress
            else:
                # 최종 이미지 등장
                frag['alpha'] = int(255 * eased)
                frag['scale'] = 0.5 + 0.5 * eased

        if progress >= 1.0:
            self._transition_to_dialogue()

    def _handle_click(self) -> bool:
        """클릭 처리 - 파편 페이즈 추가"""
        if self.phase == self.PHASE_FRAGMENTS and self.waiting_for_click:
            self.phase = self.PHASE_ASSEMBLE
            self.phase_timer = 0.0
            self.waiting_for_click = False
            return True

        # 대화 페이즈는 베이스 클래스 로직 사용
        return super()._handle_click()

    def render(self, screen: pygame.Surface):
        """렌더링"""
        # 배경
        self._render_background(screen)

        # 파편들 (최종 이미지가 아닌 것들 먼저)
        for frag in self.fragments:
            if not frag['is_final']:
                self._render_fragment(screen, frag)

        # 최종 이미지
        for frag in self.fragments:
            if frag['is_final']:
                self._render_fragment(screen, frag)

        # 대사
        if self.phase == self.PHASE_DIALOGUE:
            self._render_dialogue(screen)

        # 안내
        if self.waiting_for_click and self.phase == self.PHASE_FRAGMENTS:
            self._render_click_hint(screen, "클릭하여 진실 확인")

    def _render_fragment(self, screen: pygame.Surface, frag: dict):
        if frag['alpha'] <= 0:
            return

        img = frag['image']

        # 스케일
        scaled_w = int(img.get_width() * frag['scale'])
        scaled_h = int(img.get_height() * frag['scale'])
        if scaled_w <= 0 or scaled_h <= 0:
            return
        scaled = pygame.transform.smoothscale(img, (scaled_w, scaled_h))

        # 회전 (최종 이미지는 회전 안 함)
        if not frag['is_final']:
            rotated = pygame.transform.rotate(scaled, frag['rotation'])
        else:
            rotated = scaled

        # 글로우 효과
        glow_surf = pygame.Surface((rotated.get_width() + 20, rotated.get_height() + 20), pygame.SRCALPHA)
        glow_alpha = int(50 * frag['glow'])
        pygame.draw.rect(glow_surf, (150, 180, 255, glow_alpha),
                        (0, 0, glow_surf.get_width(), glow_surf.get_height()), border_radius=5)
        screen.blit(glow_surf, (frag['x'] - glow_surf.get_width() // 2,
                                frag['y'] - glow_surf.get_height() // 2))

        # 알파
        rotated.set_alpha(frag['alpha'])

        # 위치
        rect = rotated.get_rect(center=(frag['x'], frag['y']))
        screen.blit(rotated, rect)

    def _render_dialogue(self, screen: pygame.Surface):
        """대화창 렌더링 (초상화 포함)"""
        if not self.dialogue_after or self.current_dialogue_index >= len(self.dialogue_after):
            return
        dialogue = self.dialogue_after[self.current_dialogue_index]
        speaker = dialogue.get("speaker", "")
        portrait = self._get_portrait(speaker) if speaker else None

        render_dialogue_box(screen, self.screen_size, self.fonts, dialogue,
                           self.dialogue_text, self.typing_progress, self.waiting_for_click,
                           box_color=(20, 25, 40, 230), border_color=(120, 140, 180),
                           text_color=(220, 220, 240), box_height=180,
                           has_portrait=(portrait is not None), portrait=portrait)


# =========================================================
# Act 5: 성간 항해 인터페이스 효과 (BaseCutsceneEffect 상속)
# =========================================================
class StarMapEffect(BaseCutsceneEffect):
    """
    Act 5 컷씬: 성간 항해 인터페이스 효과

    특징:
    - 별이 빛나는 우주 배경
    - 홀로그램 스타 맵 그리드
    - 이미지가 행성/기지 마커처럼 표시
    - 연결선으로 경로 표시
    """

    # 추가 페이즈 상수 (베이스 클래스 확장)
    PHASE_MARKERS = 10
    PHASE_ROUTE = 11

    def __init__(self, screen_size: tuple, marker_paths: list,
                 marker_positions: dict = None, route_order: list = None,
                 background_path: str = None, dialogue_after: list = None,
                 sound_manager=None, special_effects: dict = None,
                 scene_id: str = "starmap_scene"):
        # 베이스 클래스 초기화
        super().__init__(screen_size, background_path, dialogue_after,
                        sound_manager, special_effects, scene_id)

        self.marker_paths = marker_paths
        self.marker_positions = marker_positions or {}
        self.route_order = route_order or []
        self.typing_speed = 25.0  # 오버라이드

        # 배경에 우주 틴트 오버레이 적용
        if background_path:
            self._load_background(background_path, overlay_alpha=150)

        # 별 파티클
        self.stars = []
        self._create_stars()

        # 마커들
        self.markers = []
        self._prepare_markers()

        # 경로
        self.route_progress = 0.0
        self.route_duration = 3.0
        self.route_points = []

        # 마커 애니메이션
        self.marker_animation_progress = 0.0

    def _create_stars(self):
        """배경 별 생성"""
        for _ in range(150):
            self.stars.append({
                'x': random.randint(0, self.screen_size[0]),
                'y': random.randint(0, self.screen_size[1]),
                'size': random.uniform(1, 3),
                'brightness': random.uniform(0.3, 1.0),
                'twinkle_speed': random.uniform(1, 4),
                'twinkle_offset': random.uniform(0, math.pi * 2),
            })

    # _load_background는 베이스 클래스에서 상속

    def _prepare_markers(self):
        """마커 준비"""
        screen_w, screen_h = self.screen_size
        marker_size = 80

        for path in self.marker_paths:
            marker_img = None
            try:
                marker_img = pygame.image.load(path).convert_alpha()
                marker_img = pygame.transform.smoothscale(marker_img, (marker_size, marker_size))
            except Exception as e:
                print(f"WARNING: Failed to load marker: {path} - {e}")
                marker_img = pygame.Surface((marker_size, marker_size), pygame.SRCALPHA)
                pygame.draw.circle(marker_img, (200, 150, 100), (marker_size // 2, marker_size // 2), marker_size // 2)

            filename = Path(path).name
            pos_info = self.marker_positions.get(filename, {})
            rel_pos = pos_info.get('rel_pos', (0.5, 0.5))
            label = pos_info.get('label', '')
            color = pos_info.get('color', (255, 255, 255))

            self.markers.append({
                'image': marker_img,
                'filename': filename,
                'x': int(screen_w * rel_pos[0]),
                'y': int(screen_h * rel_pos[1]),
                'label': label,
                'color': color,
                'alpha': 0,
                'scale': 0.5,
                'pulse': 0.0,
            })

        # 경로 포인트 생성
        for filename in self.route_order:
            for marker in self.markers:
                if marker['filename'] == filename:
                    self.route_points.append((marker['x'], marker['y']))
                    break

    # set_fonts, _start_dialogue는 베이스 클래스에서 상속

    def _on_fadein_complete(self):
        """페이드인 완료 후 마커 등장 페이즈로 전환"""
        self.phase = self.PHASE_MARKERS
        self.phase_timer = 0.0

    def update(self, dt: float):
        """업데이트 - 마커/경로 고유 로직 추가"""
        if not self.is_alive:
            return

        self.phase_timer += dt

        # 마커 펄스 (항상 업데이트)
        for marker in self.markers:
            marker['pulse'] = 0.5 + 0.5 * math.sin(self.phase_timer * 2 + marker['x'] * 0.01)

        # 페이즈별 처리
        if self.phase == self.PHASE_FADEIN:
            if self._update_fadein(dt):
                self._on_fadein_complete()

        elif self.phase == self.PHASE_MARKERS:
            self._update_markers(dt)

        elif self.phase == self.PHASE_ROUTE:
            self._update_route(dt)

        elif self.phase == self.PHASE_DIALOGUE:
            if self._update_dialogue(dt):
                self._transition_to_fadeout()

        elif self.phase == self.PHASE_FADEOUT:
            if self._update_fadeout(dt):
                self._on_fadeout_complete()

    def _update_markers(self, dt: float):
        """마커 등장 애니메이션"""
        self.marker_animation_progress += dt * 1.5
        visible_count = int(self.marker_animation_progress)

        for i, marker in enumerate(self.markers):
            if i < visible_count:
                progress = min(1.0, self.marker_animation_progress - i)
                eased = 1.0 - (1.0 - progress) ** 3
                marker['alpha'] = int(255 * eased)
                marker['scale'] = 0.5 + 0.5 * eased

        if visible_count >= len(self.markers):
            self.waiting_for_click = True

    def _update_route(self, dt: float):
        """경로 애니메이션"""
        self.route_progress = min(1.0, self.phase_timer / self.route_duration)

        if self.route_progress >= 1.0:
            self._transition_to_dialogue()

    def _handle_click(self) -> bool:
        """클릭 처리 - 마커 페이즈 추가"""
        if self.phase == self.PHASE_MARKERS and self.waiting_for_click:
            self.phase = self.PHASE_ROUTE
            self.phase_timer = 0.0
            self.waiting_for_click = False
            return True

        # 대화 페이즈는 베이스 클래스 로직 사용
        return super()._handle_click()

    def render(self, screen: pygame.Surface):
        """렌더링"""
        # 배경 또는 우주 배경
        if self.background:
            bg_copy = self.background.copy()
            if self.fade_alpha < 255:
                bg_copy.set_alpha(int(self.fade_alpha))
            screen.blit(bg_copy, (0, 0))
        else:
            screen.fill((5, 5, 20))

        # 별
        self._render_stars(screen)

        # 그리드
        self._render_grid(screen)

        # 경로 (PHASE_ROUTE 이후)
        if self.phase >= self.PHASE_ROUTE:
            self._render_route(screen)

        # 마커들
        for marker in self.markers:
            self._render_marker(screen, marker)

        # 대사
        if self.phase == self.PHASE_DIALOGUE:
            self._render_dialogue(screen)

        # 안내
        if self.waiting_for_click and self.phase == self.PHASE_MARKERS:
            self._render_click_hint(screen, "클릭하여 항로 확인")

    def _render_stars(self, screen: pygame.Surface):
        """별 렌더링"""
        for star in self.stars:
            twinkle = 0.5 + 0.5 * math.sin(self.phase_timer * star['twinkle_speed'] + star['twinkle_offset'])
            brightness = int(255 * star['brightness'] * twinkle * (self.fade_alpha / 255))
            color = (brightness, brightness, int(brightness * 0.9))
            pygame.draw.circle(screen, color, (int(star['x']), int(star['y'])), int(star['size']))

    def _render_grid(self, screen: pygame.Surface):
        """홀로그램 그리드"""
        grid_surf = pygame.Surface(self.screen_size, pygame.SRCALPHA)
        grid_color = (100, 150, 255, 30)

        # 수평선
        for y in range(0, self.screen_size[1], 50):
            pygame.draw.line(grid_surf, grid_color, (0, y), (self.screen_size[0], y))

        # 수직선
        for x in range(0, self.screen_size[0], 50):
            pygame.draw.line(grid_surf, grid_color, (x, 0), (x, self.screen_size[1]))

        screen.blit(grid_surf, (0, 0))

    def _render_route(self, screen: pygame.Surface):
        """경로 렌더링"""
        if len(self.route_points) < 2:
            return

        # 전체 경로 길이 계산
        total_length = 0
        segments = []
        for i in range(len(self.route_points) - 1):
            p1, p2 = self.route_points[i], self.route_points[i + 1]
            length = math.sqrt((p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2)
            segments.append((p1, p2, length))
            total_length += length

        # 현재 진행 거리
        current_dist = total_length * self.route_progress
        drawn_dist = 0

        route_surf = pygame.Surface(self.screen_size, pygame.SRCALPHA)

        for p1, p2, length in segments:
            if drawn_dist + length <= current_dist:
                # 전체 세그먼트 그리기
                pygame.draw.line(route_surf, (255, 200, 100, 200), p1, p2, 3)
                drawn_dist += length
            elif drawn_dist < current_dist:
                # 부분 세그먼트
                ratio = (current_dist - drawn_dist) / length
                mid_x = p1[0] + (p2[0] - p1[0]) * ratio
                mid_y = p1[1] + (p2[1] - p1[1]) * ratio
                pygame.draw.line(route_surf, (255, 200, 100, 200), p1, (mid_x, mid_y), 3)
                break

        screen.blit(route_surf, (0, 0))

    def _render_marker(self, screen: pygame.Surface, marker: dict):
        if marker['alpha'] <= 0:
            return

        img = marker['image']

        # 스케일
        scaled_w = int(img.get_width() * marker['scale'])
        scaled_h = int(img.get_height() * marker['scale'])
        if scaled_w <= 0 or scaled_h <= 0:
            return
        scaled = pygame.transform.smoothscale(img, (scaled_w, scaled_h))

        # 글로우
        glow_size = int(scaled_w * 1.5)
        glow_surf = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
        glow_alpha = int(80 * marker['pulse'])
        pygame.draw.circle(glow_surf, (*marker['color'], glow_alpha),
                          (glow_size // 2, glow_size // 2), glow_size // 2)
        screen.blit(glow_surf, (marker['x'] - glow_size // 2, marker['y'] - glow_size // 2))

        # 마커
        scaled.set_alpha(marker['alpha'])
        rect = scaled.get_rect(center=(marker['x'], marker['y']))
        screen.blit(scaled, rect)

        # 라벨
        if marker['label'] and marker['alpha'] > 200 and "small" in self.fonts:
            label_surf = self.fonts["small"].render(marker['label'], True, marker['color'])
            label_x = marker['x'] - label_surf.get_width() // 2
            label_y = marker['y'] + scaled_h // 2 + 10
            screen.blit(label_surf, (label_x, label_y))

    def _render_dialogue(self, screen: pygame.Surface):
        """대화창 렌더링 (초상화 포함)"""
        if not self.dialogue_after or self.current_dialogue_index >= len(self.dialogue_after):
            return
        dialogue = self.dialogue_after[self.current_dialogue_index]
        speaker = dialogue.get("speaker", "")
        portrait = self._get_portrait(speaker) if speaker else None

        render_dialogue_box(screen, self.screen_size, self.fonts, dialogue,
                           self.dialogue_text, self.typing_progress, self.waiting_for_click,
                           box_color=(10, 20, 40, 220), border_color=(100, 150, 255),
                           text_color=(220, 230, 255), box_height=180,
                           has_portrait=(portrait is not None), portrait=portrait)


# =========================================================
# 안드로메다 세계 효과 (사이버펑크 고대 도시)
# =========================================================
class AndromedaWorldEffect(BaseCutsceneEffect):
    """
    안드로메다 컷씬: 사이버펑크 고대 도시 효과

    특징:
    - 짙은 보라/검은색 하늘 (변화 없음)
    - 네온 회로가 새겨진 피라미드형 건물
    - 홀로그램 고대 문자
    - 제한적 색감 (네온 청록/보라/주황만)
    - 영원한 황혼 분위기
    """

    def __init__(self, screen_size: tuple, background_path: str = None,
                 dialogue_after: list = None, sound_manager=None,
                 special_effects: dict = None, scene_id: str = "andromeda_scene"):
        super().__init__(screen_size, background_path, dialogue_after,
                        sound_manager, special_effects, scene_id)

        self.typing_speed = 25.0

        # 안드로메다 색상 팔레트 (제한적)
        self.neon_colors = [
            (0, 255, 255),      # 청록
            (200, 100, 255),    # 보라
            (255, 150, 50),     # 주황
        ]
        self.sky_color = (40, 20, 60)  # 짙은 보라/검은색

        # 피라미드 건물들
        self.buildings = []
        self._create_buildings()

        # 네온 회로 라인
        self.circuit_lines = []
        self._create_circuits()

        # 홀로그램 문자
        self.holo_chars = []
        self._create_hologram_chars()

        # 파티클
        self.particles = []
        self._create_particles()

        # 애니메이션 타이머
        self.glow_timer = 0.0

    def _create_buildings(self):
        """피라미드형 건물 생성"""
        screen_w, screen_h = self.screen_size
        for i in range(5):
            x = random.randint(50, screen_w - 50)
            width = random.randint(80, 150)
            height = random.randint(150, 300)
            color_idx = random.randint(0, len(self.neon_colors) - 1)
            self.buildings.append({
                'x': x,
                'y': screen_h - height // 2,
                'width': width,
                'height': height,
                'color': self.neon_colors[color_idx],
                'glow_offset': random.uniform(0, math.pi * 2),
            })

    def _create_circuits(self):
        """네온 회로 라인 생성"""
        screen_w, screen_h = self.screen_size
        for _ in range(15):
            start_x = random.randint(0, screen_w)
            start_y = random.randint(screen_h // 2, screen_h)
            length = random.randint(50, 150)
            horizontal = random.choice([True, False])
            color_idx = random.randint(0, len(self.neon_colors) - 1)
            self.circuit_lines.append({
                'start': (start_x, start_y),
                'length': length,
                'horizontal': horizontal,
                'color': self.neon_colors[color_idx],
                'pulse_offset': random.uniform(0, math.pi * 2),
            })

    def _create_hologram_chars(self):
        """홀로그램 고대 문자 생성"""
        screen_w, screen_h = self.screen_size
        # 간단한 기호들로 고대 문자 표현
        symbols = ['◆', '◇', '○', '△', '▽', '□', '☆', '⬡', '⬢']
        for _ in range(20):
            self.holo_chars.append({
                'x': random.randint(50, screen_w - 50),
                'y': random.randint(50, screen_h - 200),
                'char': random.choice(symbols),
                'size': random.randint(15, 30),
                'alpha': random.randint(50, 150),
                'drift_speed': random.uniform(0.2, 0.5),
                'drift_offset': random.uniform(0, math.pi * 2),
            })

    def _create_particles(self):
        """네온 파티클 생성"""
        for _ in range(30):
            self.particles.append({
                'x': random.randint(0, self.screen_size[0]),
                'y': random.randint(0, self.screen_size[1]),
                'size': random.uniform(1, 3),
                'color': random.choice(self.neon_colors),
                'speed': random.uniform(10, 30),
                'alpha': random.randint(100, 200),
            })

    def update(self, dt: float):
        """업데이트"""
        if not self.is_alive:
            return

        self.phase_timer += dt
        self.glow_timer += dt

        # 파티클 이동
        for p in self.particles:
            p['y'] -= p['speed'] * dt
            if p['y'] < 0:
                p['y'] = self.screen_size[1]
                p['x'] = random.randint(0, self.screen_size[0])

        # 페이즈 처리
        if self.phase == self.PHASE_FADEIN:
            if self._update_fadein(dt):
                self._transition_to_dialogue()

        elif self.phase == self.PHASE_DIALOGUE:
            if self._update_dialogue(dt):
                self._transition_to_fadeout()

        elif self.phase == self.PHASE_FADEOUT:
            if self._update_fadeout(dt):
                self._on_fadeout_complete()

    def render(self, screen: pygame.Surface):
        """렌더링"""
        # 배경색 (영원한 황혼)
        screen.fill(self.sky_color)

        # 배경 이미지 (있으면)
        if self.background:
            bg_copy = self.background.copy()
            bg_copy.set_alpha(int(self.fade_alpha * 0.5))
            screen.blit(bg_copy, (0, 0))

        # 피라미드 건물
        self._render_buildings(screen)

        # 네온 회로
        self._render_circuits(screen)

        # 홀로그램 문자
        self._render_hologram(screen)

        # 파티클
        self._render_particles(screen)

        # 스캔라인 효과
        self._render_scanlines(screen)

        # 대사
        if self.phase == self.PHASE_DIALOGUE:
            self._render_dialogue(screen)

    def _render_buildings(self, screen: pygame.Surface):
        """피라미드 건물 렌더링"""
        for bld in self.buildings:
            # 피라미드 형태
            points = [
                (bld['x'], bld['y']),  # 상단 중앙
                (bld['x'] - bld['width'] // 2, bld['y'] + bld['height']),  # 좌하단
                (bld['x'] + bld['width'] // 2, bld['y'] + bld['height']),  # 우하단
            ]

            # 글로우 효과
            glow = 0.5 + 0.5 * math.sin(self.glow_timer * 2 + bld['glow_offset'])
            color = tuple(int(c * glow) for c in bld['color'])

            # 외곽선
            pygame.draw.polygon(screen, color, points, 2)

            # 내부 회로 라인
            for i in range(3):
                y_offset = bld['height'] * (i + 1) // 4
                line_y = bld['y'] + y_offset
                half_width = bld['width'] * (bld['height'] - y_offset) // (2 * bld['height'])
                pygame.draw.line(screen, (*color[:3], int(100 * glow)),
                               (bld['x'] - half_width, line_y),
                               (bld['x'] + half_width, line_y), 1)

    def _render_circuits(self, screen: pygame.Surface):
        """네온 회로 렌더링"""
        circuit_surf = pygame.Surface(self.screen_size, pygame.SRCALPHA)
        for circuit in self.circuit_lines:
            pulse = 0.3 + 0.7 * math.sin(self.glow_timer * 3 + circuit['pulse_offset'])
            alpha = int(200 * pulse)
            color = (*circuit['color'], alpha)

            start = circuit['start']
            if circuit['horizontal']:
                end = (start[0] + circuit['length'], start[1])
            else:
                end = (start[0], start[1] - circuit['length'])

            pygame.draw.line(circuit_surf, color, start, end, 2)

        screen.blit(circuit_surf, (0, 0))

    def _render_hologram(self, screen: pygame.Surface):
        """홀로그램 문자 렌더링"""
        if "small" not in self.fonts:
            return

        holo_surf = pygame.Surface(self.screen_size, pygame.SRCALPHA)
        for char in self.holo_chars:
            # 부유 효과
            drift = math.sin(self.glow_timer * char['drift_speed'] + char['drift_offset']) * 10
            y = char['y'] + drift

            # 깜빡임
            flicker = 0.5 + 0.5 * math.sin(self.glow_timer * 5 + char['drift_offset'])
            alpha = int(char['alpha'] * flicker)

            color = (0, 255, 255, alpha)  # 청록색
            text = self.fonts["small"].render(char['char'], True, color[:3])
            text.set_alpha(alpha)
            holo_surf.blit(text, (char['x'], y))

        screen.blit(holo_surf, (0, 0))

    def _render_particles(self, screen: pygame.Surface):
        """파티클 렌더링"""
        for p in self.particles:
            alpha = int(p['alpha'] * (self.fade_alpha / 255))
            color = (*p['color'], alpha)
            pygame.draw.circle(screen, color, (int(p['x']), int(p['y'])), int(p['size']))

    def _render_scanlines(self, screen: pygame.Surface):
        """스캔라인 효과 (CRT 느낌)"""
        scanline_surf = pygame.Surface(self.screen_size, pygame.SRCALPHA)
        for y in range(0, self.screen_size[1], 4):
            pygame.draw.line(scanline_surf, (0, 0, 0, 30), (0, y), (self.screen_size[0], y))
        screen.blit(scanline_surf, (0, 0))

    def _render_dialogue(self, screen: pygame.Surface):
        """대화창 렌더링"""
        if not self.dialogue_after or self.current_dialogue_index >= len(self.dialogue_after):
            return
        dialogue = self.dialogue_after[self.current_dialogue_index]
        speaker = dialogue.get("speaker", "")
        portrait = self._get_portrait(speaker) if speaker else None

        render_dialogue_box(screen, self.screen_size, self.fonts, dialogue,
                           self.dialogue_text, self.typing_progress, self.waiting_for_click,
                           box_color=(20, 10, 40, 230), border_color=(0, 255, 255),
                           text_color=(200, 230, 255), box_height=180,
                           has_portrait=(portrait is not None), portrait=portrait)


# =========================================================
# 두 세계 비교 효과 (화면 분할)
# =========================================================
class TwoWorldsEffect(BaseCutsceneEffect):
    """
    두 세계 비교 컷씬: 화면 분할 효과

    특징:
    - 화면 왼쪽: 안드로메다 (사이버펑크 고대 도시, 정적)
    - 화면 오른쪽: 지구 사계절 (다채색, 동적)
    - 점진적으로 오른쪽이 왼쪽을 덮는 애니메이션
    """

    PHASE_SPLIT = 10
    PHASE_MERGE = 11

    def __init__(self, screen_size: tuple, andromeda_bg: str = None,
                 earth_bg: str = None, dialogue_after: list = None,
                 sound_manager=None, special_effects: dict = None,
                 scene_id: str = "two_worlds_scene"):
        super().__init__(screen_size, None, dialogue_after,
                        sound_manager, special_effects, scene_id)

        self.typing_speed = 25.0

        # 배경 이미지 로드
        self.andromeda_bg = None
        self.earth_bg = None

        if andromeda_bg:
            try:
                img = pygame.image.load(andromeda_bg).convert()
                self.andromeda_bg = pygame.transform.smoothscale(img, screen_size)
            except:
                pass

        if earth_bg:
            try:
                img = pygame.image.load(earth_bg).convert()
                self.earth_bg = pygame.transform.smoothscale(img, screen_size)
            except:
                pass

        # 분할선 위치 (0.0 ~ 1.0)
        self.split_position = 0.5
        self.target_split = 0.5
        self.merge_progress = 0.0
        self.merge_duration = 3.0

        # 꽃잎 파티클 (지구 쪽)
        self.petals = []
        self._create_petals()

        # 네온 파티클 (안드로메다 쪽)
        self.neon_particles = []
        self._create_neon_particles()

    def _create_petals(self):
        """벚꽃 꽃잎 생성"""
        for _ in range(30):
            self.petals.append({
                'x': random.randint(self.screen_size[0] // 2, self.screen_size[0]),
                'y': random.randint(-50, self.screen_size[1]),
                'size': random.randint(5, 12),
                'speed_y': random.uniform(20, 50),
                'speed_x': random.uniform(-20, 20),
                'rotation': random.uniform(0, 360),
                'rot_speed': random.uniform(-90, 90),
                'alpha': random.randint(150, 255),
            })

    def _create_neon_particles(self):
        """네온 파티클 생성"""
        for _ in range(20):
            self.neon_particles.append({
                'x': random.randint(0, self.screen_size[0] // 2),
                'y': random.randint(0, self.screen_size[1]),
                'size': random.uniform(1, 3),
                'color': random.choice([(0, 255, 255), (200, 100, 255), (255, 150, 50)]),
                'speed': random.uniform(10, 30),
                'alpha': random.randint(100, 200),
            })

    def _on_fadein_complete(self):
        """페이드인 완료 후 분할 화면 페이즈"""
        self.phase = self.PHASE_SPLIT
        self.phase_timer = 0.0

    def update(self, dt: float):
        """업데이트"""
        if not self.is_alive:
            return

        self.phase_timer += dt

        # 꽃잎 이동
        for petal in self.petals:
            petal['y'] += petal['speed_y'] * dt
            petal['x'] += petal['speed_x'] * dt
            petal['rotation'] += petal['rot_speed'] * dt
            if petal['y'] > self.screen_size[1]:
                petal['y'] = -20
                petal['x'] = random.randint(int(self.screen_size[0] * self.split_position), self.screen_size[0])

        # 네온 파티클 이동
        for p in self.neon_particles:
            p['y'] -= p['speed'] * dt
            if p['y'] < 0:
                p['y'] = self.screen_size[1]
                p['x'] = random.randint(0, int(self.screen_size[0] * self.split_position))

        # 페이즈 처리
        if self.phase == self.PHASE_FADEIN:
            if self._update_fadein(dt):
                self._on_fadein_complete()

        elif self.phase == self.PHASE_SPLIT:
            # 분할 화면 대기 (클릭으로 다음)
            self.waiting_for_click = True

        elif self.phase == self.PHASE_MERGE:
            # 지구가 안드로메다를 덮는 애니메이션
            self.merge_progress = min(1.0, self.phase_timer / self.merge_duration)
            self.split_position = 0.5 - 0.5 * self._ease_out_cubic(self.merge_progress)

            if self.merge_progress >= 1.0:
                self._transition_to_dialogue()

        elif self.phase == self.PHASE_DIALOGUE:
            if self._update_dialogue(dt):
                self._transition_to_fadeout()

        elif self.phase == self.PHASE_FADEOUT:
            if self._update_fadeout(dt):
                self._on_fadeout_complete()

    def _ease_out_cubic(self, t):
        return 1 - pow(1 - t, 3)

    def _handle_click(self) -> bool:
        """클릭 처리"""
        if self.phase == self.PHASE_SPLIT and self.waiting_for_click:
            self.phase = self.PHASE_MERGE
            self.phase_timer = 0.0
            self.waiting_for_click = False
            return True
        return super()._handle_click()

    def render(self, screen: pygame.Surface):
        """렌더링"""
        split_x = int(self.screen_size[0] * self.split_position)

        # 왼쪽: 안드로메다
        if self.andromeda_bg:
            screen.blit(self.andromeda_bg, (0, 0), (0, 0, split_x, self.screen_size[1]))
        else:
            pygame.draw.rect(screen, (40, 20, 60), (0, 0, split_x, self.screen_size[1]))

        # 오른쪽: 지구
        if self.earth_bg:
            screen.blit(self.earth_bg, (split_x, 0),
                       (split_x, 0, self.screen_size[0] - split_x, self.screen_size[1]))
        else:
            pygame.draw.rect(screen, (100, 150, 200),
                           (split_x, 0, self.screen_size[0] - split_x, self.screen_size[1]))

        # 네온 파티클 (안드로메다 쪽)
        for p in self.neon_particles:
            if p['x'] < split_x:
                alpha = int(p['alpha'] * (self.fade_alpha / 255))
                pygame.draw.circle(screen, (*p['color'], alpha), (int(p['x']), int(p['y'])), int(p['size']))

        # 꽃잎 (지구 쪽)
        for petal in self.petals:
            if petal['x'] >= split_x:
                self._render_petal(screen, petal)

        # 분할선 (글로우 효과)
        glow_width = 10
        glow_surf = pygame.Surface((glow_width * 2, self.screen_size[1]), pygame.SRCALPHA)
        for i in range(glow_width):
            alpha = int(150 * (1 - i / glow_width))
            pygame.draw.line(glow_surf, (255, 255, 255, alpha),
                           (glow_width - i, 0), (glow_width - i, self.screen_size[1]))
            pygame.draw.line(glow_surf, (255, 255, 255, alpha),
                           (glow_width + i, 0), (glow_width + i, self.screen_size[1]))
        screen.blit(glow_surf, (split_x - glow_width, 0))

        # 라벨
        if self.phase == self.PHASE_SPLIT and "small" in self.fonts:
            # 안드로메다 라벨
            label_a = self.fonts["small"].render("안드로메다", True, (0, 255, 255))
            screen.blit(label_a, (split_x // 2 - label_a.get_width() // 2, 30))

            # 지구 라벨
            label_e = self.fonts["small"].render("지구", True, (255, 200, 150))
            screen.blit(label_e, (split_x + (self.screen_size[0] - split_x) // 2 - label_e.get_width() // 2, 30))

        # 안내
        if self.waiting_for_click and self.phase == self.PHASE_SPLIT:
            self._render_click_hint(screen, "클릭하여 계속")

        # 대사
        if self.phase == self.PHASE_DIALOGUE:
            self._render_dialogue(screen)

    def _render_petal(self, screen: pygame.Surface, petal: dict):
        """벚꽃 꽃잎 렌더링"""
        size = petal['size']
        surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)

        # 꽃잎 모양 (타원)
        color = (255, 200, 220, petal['alpha'])
        pygame.draw.ellipse(surf, color, (0, size // 2, size * 2, size))

        # 회전
        rotated = pygame.transform.rotate(surf, petal['rotation'])
        rect = rotated.get_rect(center=(petal['x'], petal['y']))
        screen.blit(rotated, rect)

    def _render_dialogue(self, screen: pygame.Surface):
        """대화창 렌더링"""
        if not self.dialogue_after or self.current_dialogue_index >= len(self.dialogue_after):
            return
        dialogue = self.dialogue_after[self.current_dialogue_index]
        speaker = dialogue.get("speaker", "")
        portrait = self._get_portrait(speaker) if speaker else None

        render_dialogue_box(screen, self.screen_size, self.fonts, dialogue,
                           self.dialogue_text, self.typing_progress, self.waiting_for_click,
                           box_color=(20, 20, 30, 230), border_color=(200, 180, 255),
                           text_color=(240, 240, 255), box_height=180,
                           has_portrait=(portrait is not None), portrait=portrait)


# =========================================================
# 계절 기억 효과 (빠른 계절 전환)
# =========================================================
class SeasonMemoryEffect(BaseCutsceneEffect):
    """
    계절 기억 컷씬: 빠른 계절 전환 효과

    특징:
    - 봄/여름/가을/겨울 이미지 빠르게 전환
    - 각 계절에 맞는 파티클 효과
    - 감정과 연결된 대사
    """

    PHASE_SEASONS = 10

    def __init__(self, screen_size: tuple, season_images: list = None,
                 dialogue_after: list = None, sound_manager=None,
                 special_effects: dict = None, scene_id: str = "season_memory_scene"):
        super().__init__(screen_size, None, dialogue_after,
                        sound_manager, special_effects, scene_id)

        self.typing_speed = 25.0

        # 계절 이미지 (봄, 여름, 가을, 겨울)
        self.season_images = []
        self.season_names = ["봄", "여름", "가을", "겨울"]
        self.season_colors = [
            (255, 200, 220),  # 봄: 분홍
            (100, 200, 100),  # 여름: 초록
            (255, 180, 100),  # 가을: 주황
            (200, 220, 255),  # 겨울: 하늘색
        ]

        if season_images:
            for path in season_images:
                try:
                    img = pygame.image.load(path).convert()
                    img = pygame.transform.smoothscale(img, screen_size)
                    self.season_images.append(img)
                except:
                    # 대체 색상 배경
                    surf = pygame.Surface(screen_size)
                    idx = len(self.season_images) % 4
                    surf.fill(self.season_colors[idx])
                    self.season_images.append(surf)

        # 최소 4개 보장
        while len(self.season_images) < 4:
            surf = pygame.Surface(screen_size)
            surf.fill(self.season_colors[len(self.season_images)])
            self.season_images.append(surf)

        # 현재 계절 인덱스
        self.current_season = 0
        self.season_timer = 0.0
        self.season_duration = 2.0  # 각 계절 표시 시간
        self.transition_duration = 0.5  # 전환 시간
        self.transitioning = False
        self.transition_progress = 0.0

        # 파티클 (계절별)
        self.particles = []
        self._create_season_particles()

    def _create_season_particles(self):
        """계절별 파티클 생성"""
        self.particles = []
        for _ in range(40):
            self.particles.append({
                'x': random.randint(0, self.screen_size[0]),
                'y': random.randint(-50, self.screen_size[1]),
                'size': random.randint(3, 8),
                'speed_y': random.uniform(30, 80),
                'speed_x': random.uniform(-30, 30),
                'rotation': random.uniform(0, 360),
                'rot_speed': random.uniform(-180, 180),
            })

    def _on_fadein_complete(self):
        """페이드인 완료 후 계절 전환 페이즈"""
        self.phase = self.PHASE_SEASONS
        self.phase_timer = 0.0
        self.current_season = 0

    def update(self, dt: float):
        """업데이트"""
        if not self.is_alive:
            return

        self.phase_timer += dt

        # 파티클 이동
        for p in self.particles:
            p['y'] += p['speed_y'] * dt
            p['x'] += p['speed_x'] * dt
            p['rotation'] += p['rot_speed'] * dt
            if p['y'] > self.screen_size[1] + 50:
                p['y'] = -50
                p['x'] = random.randint(0, self.screen_size[0])

        # 페이즈 처리
        if self.phase == self.PHASE_FADEIN:
            if self._update_fadein(dt):
                self._on_fadein_complete()

        elif self.phase == self.PHASE_SEASONS:
            self.season_timer += dt

            if self.transitioning:
                self.transition_progress = min(1.0, self.transition_progress + dt / self.transition_duration)
                if self.transition_progress >= 1.0:
                    self.transitioning = False
                    self.current_season = (self.current_season + 1) % 4
                    self.season_timer = 0.0
                    self.transition_progress = 0.0

                    # 4계절 완료 시 대화로 전환
                    if self.current_season == 0:
                        self._transition_to_dialogue()
            else:
                if self.season_timer >= self.season_duration:
                    self.transitioning = True
                    self.transition_progress = 0.0

        elif self.phase == self.PHASE_DIALOGUE:
            if self._update_dialogue(dt):
                self._transition_to_fadeout()

        elif self.phase == self.PHASE_FADEOUT:
            if self._update_fadeout(dt):
                self._on_fadeout_complete()

    def render(self, screen: pygame.Surface):
        """렌더링"""
        # 현재 계절 배경
        if self.season_images:
            current_img = self.season_images[self.current_season]

            if self.transitioning and len(self.season_images) > 1:
                # 페이드 전환
                next_season = (self.current_season + 1) % len(self.season_images)
                next_img = self.season_images[next_season]

                current_img.set_alpha(int(255 * (1 - self.transition_progress)))
                screen.blit(current_img, (0, 0))

                next_img.set_alpha(int(255 * self.transition_progress))
                screen.blit(next_img, (0, 0))
            else:
                current_img.set_alpha(int(self.fade_alpha))
                screen.blit(current_img, (0, 0))

        # 계절 파티클
        self._render_particles(screen)

        # 계절 이름
        if self.phase == self.PHASE_SEASONS and "large" in self.fonts:
            season_name = self.season_names[self.current_season]
            color = self.season_colors[self.current_season]

            # 글로우 효과
            glow_alpha = int(150 * (1 - self.transition_progress if self.transitioning else 1))
            text = self.fonts["large"].render(season_name, True, color)
            text.set_alpha(glow_alpha)

            x = self.screen_size[0] // 2 - text.get_width() // 2
            y = 50
            screen.blit(text, (x, y))

        # 대사
        if self.phase == self.PHASE_DIALOGUE:
            self._render_dialogue(screen)

    def _render_particles(self, screen: pygame.Surface):
        """계절별 파티클 렌더링"""
        season = self.current_season

        for p in self.particles:
            if season == 0:  # 봄: 꽃잎
                self._render_petal(screen, p, (255, 200, 220))
            elif season == 1:  # 여름: 나뭇잎
                self._render_leaf(screen, p, (100, 200, 100))
            elif season == 2:  # 가을: 낙엽
                self._render_leaf(screen, p, (255, 150, 50))
            elif season == 3:  # 겨울: 눈
                self._render_snow(screen, p)

    def _render_petal(self, screen: pygame.Surface, p: dict, color: tuple):
        """꽃잎 렌더링"""
        size = p['size']
        surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
        pygame.draw.ellipse(surf, (*color, 200), (0, size // 2, size * 2, size))
        rotated = pygame.transform.rotate(surf, p['rotation'])
        rect = rotated.get_rect(center=(p['x'], p['y']))
        screen.blit(rotated, rect)

    def _render_leaf(self, screen: pygame.Surface, p: dict, color: tuple):
        """나뭇잎 렌더링"""
        size = p['size']
        surf = pygame.Surface((size * 2, size), pygame.SRCALPHA)
        # 잎 모양 (다이아몬드)
        points = [(size, 0), (size * 2, size // 2), (size, size), (0, size // 2)]
        pygame.draw.polygon(surf, (*color, 200), points)
        rotated = pygame.transform.rotate(surf, p['rotation'])
        rect = rotated.get_rect(center=(p['x'], p['y']))
        screen.blit(rotated, rect)

    def _render_snow(self, screen: pygame.Surface, p: dict):
        """눈 렌더링"""
        alpha = int(200 * (self.fade_alpha / 255))
        pygame.draw.circle(screen, (255, 255, 255, alpha), (int(p['x']), int(p['y'])), p['size'])

    def _render_dialogue(self, screen: pygame.Surface):
        """대화창 렌더링"""
        if not self.dialogue_after or self.current_dialogue_index >= len(self.dialogue_after):
            return
        dialogue = self.dialogue_after[self.current_dialogue_index]
        speaker = dialogue.get("speaker", "")
        portrait = self._get_portrait(speaker) if speaker else None

        render_dialogue_box(screen, self.screen_size, self.fonts, dialogue,
                           self.dialogue_text, self.typing_progress, self.waiting_for_click,
                           box_color=(30, 25, 40, 230), border_color=(200, 180, 150),
                           text_color=(255, 250, 240), box_height=180,
                           has_portrait=(portrait is not None), portrait=portrait)


class BrokenToyEffect(BaseCutsceneEffect):
    """
    부서진 장난감 컷씬 (Act 1)

    특징:
    - 폐허 속에서 발견된 낡은 인형/장난감
    - 천천히 떨어지는 먼지 파티클
    - 그을린 자국, 찢어진 부분 강조
    - 아르테미스의 어린 시절 회상 연결
    """

    PHASE_ZOOM_IN = 10
    PHASE_MEMORIES = 11

    def __init__(self, screen_size: tuple, toy_image_path: str = None,
                 dialogue_after: list = None, sound_manager=None,
                 special_effects: dict = None, scene_id: str = "broken_toy_scene"):
        super().__init__(screen_size, None, dialogue_after,
                        sound_manager, special_effects, scene_id)

        self.typing_speed = 25.0

        # 장난감 이미지
        self.toy_image = None
        self.toy_size = (200, 200)
        self.toy_pos = (screen_size[0] // 2, screen_size[1] // 2)
        self.toy_rotation = 15  # 약간 기울어진 모습

        if toy_image_path:
            try:
                img = pygame.image.load(toy_image_path).convert_alpha()
                self.toy_image = pygame.transform.smoothscale(img, self.toy_size)
            except:
                self._create_placeholder_toy()
        else:
            self._create_placeholder_toy()

        # 줌 애니메이션
        self.zoom_scale = 0.3
        self.target_zoom = 1.0
        self.zoom_speed = 0.5

        # 먼지 파티클
        self.dust_particles = []
        for _ in range(50):
            self.dust_particles.append({
                'x': random.randint(0, screen_size[0]),
                'y': random.randint(0, screen_size[1]),
                'size': random.uniform(1, 3),
                'speed_y': random.uniform(5, 15),
                'speed_x': random.uniform(-5, 5),
                'alpha': random.randint(50, 150),
            })

        # 회상 플래시 효과
        self.flash_alpha = 0
        self.flash_timer = 0.0
        self.memory_flashes = []  # 짧은 회상 이미지들

        # 배경 색상 (폐허/어두운 톤)
        self.bg_color = (30, 25, 20)

    def _create_placeholder_toy(self):
        """대체 장난감 이미지 생성 (곰인형 형태)"""
        surf = pygame.Surface(self.toy_size, pygame.SRCALPHA)

        # 몸통
        body_color = (139, 90, 43, 200)
        pygame.draw.ellipse(surf, body_color, (50, 80, 100, 110))

        # 머리
        pygame.draw.circle(surf, body_color, (100, 60), 45)

        # 귀
        pygame.draw.circle(surf, body_color, (60, 25), 18)
        pygame.draw.circle(surf, body_color, (140, 25), 18)

        # 눈 (하나는 X표시 - 부서진 느낌)
        pygame.draw.circle(surf, (20, 20, 20), (85, 55), 8)
        # X 표시 눈
        pygame.draw.line(surf, (20, 20, 20), (107, 47), (123, 63), 3)
        pygame.draw.line(surf, (20, 20, 20), (107, 63), (123, 47), 3)

        # 코
        pygame.draw.circle(surf, (60, 40, 30), (100, 75), 6)

        # 찢어진 자국 (대각선 선들)
        tear_color = (80, 50, 30, 150)
        pygame.draw.line(surf, tear_color, (70, 100), (90, 140), 2)
        pygame.draw.line(surf, tear_color, (85, 95), (75, 130), 2)

        # 그을린 자국
        burn_surf = pygame.Surface((40, 40), pygame.SRCALPHA)
        pygame.draw.circle(burn_surf, (40, 30, 25, 100), (20, 20), 20)
        surf.blit(burn_surf, (110, 120))

        self.toy_image = surf

    def _on_fadein_complete(self):
        """페이드인 완료 후 줌인 시작"""
        self.phase = self.PHASE_ZOOM_IN
        self.phase_timer = 0.0

    def update(self, dt: float):
        """업데이트"""
        if not self.is_alive:
            return

        self.phase_timer += dt

        # 먼지 파티클 업데이트
        for p in self.dust_particles:
            p['y'] += p['speed_y'] * dt
            p['x'] += p['speed_x'] * dt
            if p['y'] > self.screen_size[1]:
                p['y'] = -10
                p['x'] = random.randint(0, self.screen_size[0])

        # 회상 플래시 효과
        self.flash_timer += dt
        if self.phase == self.PHASE_MEMORIES:
            if self.flash_timer > 2.0:
                self.flash_alpha = max(0, self.flash_alpha - 200 * dt)
                if random.random() < 0.02:
                    self.flash_alpha = 100
                    self.flash_timer = 0

        # 페이즈 처리
        if self.phase == self.PHASE_FADEIN:
            if self._update_fadein(dt):
                self._on_fadein_complete()

        elif self.phase == self.PHASE_ZOOM_IN:
            # 줌인 애니메이션
            self.zoom_scale = min(self.target_zoom, self.zoom_scale + self.zoom_speed * dt)
            if self.zoom_scale >= self.target_zoom:
                self.phase = self.PHASE_MEMORIES
                self.phase_timer = 0.0
                # 2초 후 대화로 전환
            if self.phase == self.PHASE_MEMORIES and self.phase_timer > 2.0:
                self._transition_to_dialogue()

        elif self.phase == self.PHASE_MEMORIES:
            if self.phase_timer > 2.0:
                self._transition_to_dialogue()

        elif self.phase == self.PHASE_DIALOGUE:
            if self._update_dialogue(dt):
                self._transition_to_fadeout()

        elif self.phase == self.PHASE_FADEOUT:
            if self._update_fadeout(dt):
                self._on_fadeout_complete()

    def render(self, screen: pygame.Surface):
        """렌더링"""
        # 배경
        screen.fill(self.bg_color)

        # 폐허 느낌의 그라데이션
        for i in range(20):
            alpha = 10 + i * 3
            y = self.screen_size[1] - i * 30
            pygame.draw.rect(screen, (40 + i * 2, 35 + i, 30), (0, y, self.screen_size[0], 30))

        # 먼지 파티클
        for p in self.dust_particles:
            color = (180, 170, 150, p['alpha'])
            surf = pygame.Surface((int(p['size'] * 2), int(p['size'] * 2)), pygame.SRCALPHA)
            pygame.draw.circle(surf, color, (int(p['size']), int(p['size'])), int(p['size']))
            screen.blit(surf, (int(p['x']), int(p['y'])))

        # 장난감
        if self.toy_image:
            scaled_size = (int(self.toy_size[0] * self.zoom_scale),
                          int(self.toy_size[1] * self.zoom_scale))
            scaled_toy = pygame.transform.smoothscale(self.toy_image, scaled_size)
            rotated_toy = pygame.transform.rotate(scaled_toy, self.toy_rotation)

            toy_rect = rotated_toy.get_rect(center=self.toy_pos)
            screen.blit(rotated_toy, toy_rect)

            # 스포트라이트 효과
            if self.phase in [self.PHASE_ZOOM_IN, self.PHASE_MEMORIES]:
                spotlight = pygame.Surface(self.screen_size, pygame.SRCALPHA)
                center = self.toy_pos
                for r in range(150, 0, -10):
                    alpha = int(30 * (r / 150))
                    pygame.draw.circle(spotlight, (255, 240, 200, alpha), center, r)
                screen.blit(spotlight, (0, 0))

        # 회상 플래시
        if self.flash_alpha > 0:
            flash_surf = pygame.Surface(self.screen_size, pygame.SRCALPHA)
            flash_surf.fill((255, 255, 255, int(self.flash_alpha)))
            screen.blit(flash_surf, (0, 0))

        # 비네트 효과
        vignette = pygame.Surface(self.screen_size, pygame.SRCALPHA)
        for i in range(100):
            alpha = int(i * 1.5)
            pygame.draw.rect(vignette, (0, 0, 0, alpha), (i, i, self.screen_size[0] - i * 2, self.screen_size[1] - i * 2), 1)
        screen.blit(vignette, (0, 0))

        # 페이드
        if self.phase == self.PHASE_FADEIN:
            fade_surf = pygame.Surface(self.screen_size)
            fade_surf.fill((0, 0, 0))
            fade_surf.set_alpha(255 - int(self.fade_alpha))
            screen.blit(fade_surf, (0, 0))

        # 대사
        if self.phase == self.PHASE_DIALOGUE:
            self._render_dialogue(screen)

    def _render_dialogue(self, screen: pygame.Surface):
        """대화창 렌더링"""
        if not self.dialogue_after or self.current_dialogue_index >= len(self.dialogue_after):
            return
        dialogue = self.dialogue_after[self.current_dialogue_index]
        speaker = dialogue.get("speaker", "")
        portrait = self._get_portrait(speaker) if speaker else None

        render_dialogue_box(screen, self.screen_size, self.fonts, dialogue,
                           self.dialogue_text, self.typing_progress, self.waiting_for_click,
                           box_color=(40, 30, 25, 230), border_color=(150, 120, 80),
                           text_color=(255, 250, 240), box_height=180,
                           has_portrait=(portrait is not None), portrait=portrait)


class HologramMessageEffect(BaseCutsceneEffect):
    """
    아버지 홀로그램 메시지 컷씬 (Act 2)

    특징:
    - 벙커에서 발견된 홀로그램 장치
    - 깜빡이는 홀로그램 투영
    - 아버지의 녹화된 메시지
    - 스캔라인, 글리치 효과
    """

    PHASE_DEVICE_ACTIVATE = 10
    PHASE_HOLOGRAM_FLICKER = 11
    PHASE_MESSAGE_PLAY = 12

    def __init__(self, screen_size: tuple, father_image_path: str = None,
                 dialogue_after: list = None, sound_manager=None,
                 special_effects: dict = None, scene_id: str = "hologram_message_scene"):
        super().__init__(screen_size, None, dialogue_after,
                        sound_manager, special_effects, scene_id)

        self.typing_speed = 22.0

        # 아버지 홀로그램 이미지
        self.father_image = None
        self.hologram_size = (300, 400)
        self.hologram_pos = (screen_size[0] // 2, screen_size[1] // 2 - 50)

        if father_image_path:
            try:
                img = pygame.image.load(father_image_path).convert_alpha()
                self.father_image = pygame.transform.smoothscale(img, self.hologram_size)
            except:
                self._create_placeholder_silhouette()
        else:
            self._create_placeholder_silhouette()

        # 홀로그램 효과
        self.hologram_alpha = 0
        self.hologram_flicker = 0.0
        self.glitch_offset = 0
        self.scanline_offset = 0

        # 장치 활성화 파티클
        self.activation_particles = []
        self.device_glow = 0.0

        # 배경 (어두운 벙커)
        self.bg_color = (15, 20, 30)

        # 홀로그램 색상 (청록색)
        self.holo_color = (100, 200, 255)

    def _create_placeholder_silhouette(self):
        """대체 아버지 실루엣 이미지"""
        surf = pygame.Surface(self.hologram_size, pygame.SRCALPHA)

        # 머리
        head_center = (self.hologram_size[0] // 2, 80)
        pygame.draw.circle(surf, (*self.holo_color, 150), head_center, 50)

        # 어깨/상체
        body_points = [
            (self.hologram_size[0] // 2 - 80, 400),
            (self.hologram_size[0] // 2 - 60, 150),
            (self.hologram_size[0] // 2, 130),
            (self.hologram_size[0] // 2 + 60, 150),
            (self.hologram_size[0] // 2 + 80, 400),
        ]
        pygame.draw.polygon(surf, (*self.holo_color, 120), body_points)

        self.father_image = surf

    def _on_fadein_complete(self):
        """페이드인 완료 후 장치 활성화"""
        self.phase = self.PHASE_DEVICE_ACTIVATE
        self.phase_timer = 0.0

    def update(self, dt: float):
        """업데이트"""
        if not self.is_alive:
            return

        self.phase_timer += dt

        # 스캔라인 이동
        self.scanline_offset = (self.scanline_offset + 100 * dt) % self.screen_size[1]

        # 글리치 효과
        if random.random() < 0.05:
            self.glitch_offset = random.randint(-10, 10)
        else:
            self.glitch_offset = int(self.glitch_offset * 0.8)

        # 페이즈 처리
        if self.phase == self.PHASE_FADEIN:
            if self._update_fadein(dt):
                self._on_fadein_complete()

        elif self.phase == self.PHASE_DEVICE_ACTIVATE:
            self.device_glow = min(1.0, self.device_glow + dt * 0.5)
            if self.phase_timer > 2.0:
                self.phase = self.PHASE_HOLOGRAM_FLICKER
                self.phase_timer = 0.0

        elif self.phase == self.PHASE_HOLOGRAM_FLICKER:
            # 홀로그램 깜빡임
            self.hologram_flicker += dt * 10
            flicker_value = (math.sin(self.hologram_flicker * 5) + 1) / 2
            self.hologram_alpha = int(flicker_value * 200)

            if self.phase_timer > 2.0:
                self.phase = self.PHASE_MESSAGE_PLAY
                self.phase_timer = 0.0
                self.hologram_alpha = 200

        elif self.phase == self.PHASE_MESSAGE_PLAY:
            # 안정된 홀로그램
            self.hologram_alpha = 200 + int(math.sin(self.phase_timer * 2) * 30)

            if self.phase_timer > 3.0:
                self._transition_to_dialogue()

        elif self.phase == self.PHASE_DIALOGUE:
            if self._update_dialogue(dt):
                self._transition_to_fadeout()

        elif self.phase == self.PHASE_FADEOUT:
            if self._update_fadeout(dt):
                self._on_fadeout_complete()

    def render(self, screen: pygame.Surface):
        """렌더링"""
        # 배경
        screen.fill(self.bg_color)

        # 벙커 내부 느낌
        for i in range(0, self.screen_size[0], 100):
            pygame.draw.line(screen, (25, 30, 40), (i, 0), (i, self.screen_size[1]), 2)
        for i in range(0, self.screen_size[1], 100):
            pygame.draw.line(screen, (25, 30, 40), (0, i), (self.screen_size[0], i), 2)

        # 장치 (바닥의 원형 플랫폼)
        device_center = (self.screen_size[0] // 2, self.screen_size[1] - 100)
        glow_radius = int(100 + self.device_glow * 50)
        for r in range(glow_radius, 0, -10):
            alpha = int(self.device_glow * 50 * (r / glow_radius))
            pygame.draw.circle(screen, (*self.holo_color, alpha), device_center, r)
        pygame.draw.circle(screen, (50, 60, 80), device_center, 80)
        pygame.draw.circle(screen, self.holo_color, device_center, 80, 3)

        # 홀로그램
        if self.phase in [self.PHASE_HOLOGRAM_FLICKER, self.PHASE_MESSAGE_PLAY, self.PHASE_DIALOGUE]:
            if self.father_image:
                holo_surf = self.father_image.copy()
                holo_surf.set_alpha(self.hologram_alpha)

                # 글리치 오프셋 적용
                pos = (self.hologram_pos[0] - self.hologram_size[0] // 2 + self.glitch_offset,
                      self.hologram_pos[1] - self.hologram_size[1] // 2)
                screen.blit(holo_surf, pos)

                # 스캔라인 효과
                for y in range(0, self.screen_size[1], 4):
                    alpha = 30 if (y + int(self.scanline_offset)) % 8 < 4 else 0
                    if alpha > 0:
                        pygame.draw.line(screen, (0, 0, 0, alpha), (0, y), (self.screen_size[0], y))

                # 홀로그램 외곽 글로우
                glow_surf = pygame.Surface(self.screen_size, pygame.SRCALPHA)
                glow_rect = pygame.Rect(pos[0] - 20, pos[1] - 20,
                                       self.hologram_size[0] + 40, self.hologram_size[1] + 40)
                pygame.draw.rect(glow_surf, (*self.holo_color, 30), glow_rect, border_radius=10)
                screen.blit(glow_surf, (0, 0))

        # 페이드
        if self.phase == self.PHASE_FADEIN:
            fade_surf = pygame.Surface(self.screen_size)
            fade_surf.fill((0, 0, 0))
            fade_surf.set_alpha(255 - int(self.fade_alpha))
            screen.blit(fade_surf, (0, 0))

        # 대사
        if self.phase == self.PHASE_DIALOGUE:
            self._render_dialogue(screen)

    def _render_dialogue(self, screen: pygame.Surface):
        """대화창 렌더링"""
        if not self.dialogue_after or self.current_dialogue_index >= len(self.dialogue_after):
            return
        dialogue = self.dialogue_after[self.current_dialogue_index]
        speaker = dialogue.get("speaker", "")
        portrait = self._get_portrait(speaker) if speaker else None

        render_dialogue_box(screen, self.screen_size, self.fonts, dialogue,
                           self.dialogue_text, self.typing_progress, self.waiting_for_click,
                           box_color=(20, 30, 50, 230), border_color=(100, 180, 220),
                           text_color=(200, 240, 255), box_height=180,
                           has_portrait=(portrait is not None), portrait=portrait)


class DualMemoryEffect(BaseCutsceneEffect):
    """
    이중 회상 컷씬 (Act 3)

    특징:
    - 화면이 둘로 분할
    - 왼쪽: 행복했던 과거 (따뜻한 색조)
    - 오른쪽: 현재의 폐허 (차가운 색조)
    - 두 시간대가 동시에 보임
    """

    PHASE_SPLIT_SCREEN = 10
    PHASE_MERGE = 11

    def __init__(self, screen_size: tuple, past_image_path: str = None,
                 present_image_path: str = None, dialogue_after: list = None,
                 sound_manager=None, special_effects: dict = None,
                 scene_id: str = "dual_memory_scene"):
        super().__init__(screen_size, None, dialogue_after,
                        sound_manager, special_effects, scene_id)

        self.typing_speed = 24.0

        # 과거/현재 이미지
        self.past_image = None
        self.present_image = None
        half_size = (screen_size[0] // 2, screen_size[1])

        if past_image_path:
            try:
                img = pygame.image.load(past_image_path).convert()
                self.past_image = pygame.transform.smoothscale(img, half_size)
            except:
                self._create_placeholder_past(half_size)
        else:
            self._create_placeholder_past(half_size)

        if present_image_path:
            try:
                img = pygame.image.load(present_image_path).convert()
                self.present_image = pygame.transform.smoothscale(img, half_size)
            except:
                self._create_placeholder_present(half_size)
        else:
            self._create_placeholder_present(half_size)

        # 분할선 위치
        self.split_x = screen_size[0] // 2
        self.split_wave = 0.0

        # 파티클 (과거: 따뜻한 빛, 현재: 재)
        self.past_particles = []
        self.present_particles = []
        self._create_particles()

        # 색상 오버레이
        self.past_tint = (255, 230, 200)  # 따뜻한 세피아
        self.present_tint = (150, 170, 200)  # 차가운 블루

    def _create_placeholder_past(self, size):
        """과거 이미지 대체"""
        surf = pygame.Surface(size)
        # 따뜻한 그라데이션
        for y in range(size[1]):
            ratio = y / size[1]
            r = int(255 - ratio * 50)
            g = int(200 - ratio * 50)
            b = int(150 - ratio * 50)
            pygame.draw.line(surf, (r, g, b), (0, y), (size[0], y))

        # 집 실루엣
        house_color = (200, 180, 150)
        pygame.draw.rect(surf, house_color, (100, 300, 200, 150))
        pygame.draw.polygon(surf, house_color, [(100, 300), (200, 200), (300, 300)])

        # 태양
        pygame.draw.circle(surf, (255, 220, 100), (350, 100), 50)

        self.past_image = surf

    def _create_placeholder_present(self, size):
        """현재 이미지 대체"""
        surf = pygame.Surface(size)
        # 차가운 그라데이션
        for y in range(size[1]):
            ratio = y / size[1]
            r = int(40 + ratio * 20)
            g = int(50 + ratio * 20)
            b = int(70 + ratio * 20)
            pygame.draw.line(surf, (r, g, b), (0, y), (size[0], y))

        # 폐허 실루엣
        ruin_color = (60, 55, 50)
        # 무너진 건물
        pygame.draw.rect(surf, ruin_color, (80, 320, 100, 130))
        pygame.draw.rect(surf, ruin_color, (200, 280, 80, 170))
        # 잔해
        for i in range(10):
            x = random.randint(50, 350)
            y = random.randint(400, 450)
            w = random.randint(20, 50)
            h = random.randint(10, 30)
            pygame.draw.rect(surf, (50, 45, 40), (x, y, w, h))

        self.present_image = surf

    def _create_particles(self):
        """파티클 생성"""
        half_w = self.screen_size[0] // 2

        # 과거: 빛나는 먼지
        for _ in range(30):
            self.past_particles.append({
                'x': random.randint(0, half_w),
                'y': random.randint(0, self.screen_size[1]),
                'size': random.uniform(2, 4),
                'speed': random.uniform(-20, 20),
                'alpha': random.randint(100, 200),
            })

        # 현재: 재/연기
        for _ in range(40):
            self.present_particles.append({
                'x': random.randint(half_w, self.screen_size[0]),
                'y': random.randint(0, self.screen_size[1]),
                'size': random.uniform(3, 6),
                'speed_y': random.uniform(-30, -10),
                'speed_x': random.uniform(-10, 10),
                'alpha': random.randint(50, 100),
            })

    def _on_fadein_complete(self):
        """페이드인 완료"""
        self.phase = self.PHASE_SPLIT_SCREEN
        self.phase_timer = 0.0

    def update(self, dt: float):
        """업데이트"""
        if not self.is_alive:
            return

        self.phase_timer += dt

        # 분할선 웨이브
        self.split_wave += dt * 3
        wave_offset = int(math.sin(self.split_wave) * 5)

        # 파티클 업데이트
        for p in self.past_particles:
            p['y'] += p['speed'] * dt
            if p['y'] < 0 or p['y'] > self.screen_size[1]:
                p['speed'] = -p['speed']

        for p in self.present_particles:
            p['y'] += p['speed_y'] * dt
            p['x'] += p['speed_x'] * dt
            if p['y'] < -10:
                p['y'] = self.screen_size[1] + 10
                p['x'] = random.randint(self.screen_size[0] // 2, self.screen_size[0])

        # 페이즈 처리
        if self.phase == self.PHASE_FADEIN:
            if self._update_fadein(dt):
                self._on_fadein_complete()

        elif self.phase == self.PHASE_SPLIT_SCREEN:
            if self.phase_timer > 4.0:
                self._transition_to_dialogue()

        elif self.phase == self.PHASE_DIALOGUE:
            if self._update_dialogue(dt):
                self._transition_to_fadeout()

        elif self.phase == self.PHASE_FADEOUT:
            if self._update_fadeout(dt):
                self._on_fadeout_complete()

    def render(self, screen: pygame.Surface):
        """렌더링"""
        half_w = self.screen_size[0] // 2

        # 과거 (왼쪽)
        if self.past_image:
            screen.blit(self.past_image, (0, 0))
            # 따뜻한 오버레이
            warm_overlay = pygame.Surface((half_w, self.screen_size[1]), pygame.SRCALPHA)
            warm_overlay.fill((*self.past_tint, 30))
            screen.blit(warm_overlay, (0, 0))

        # 현재 (오른쪽)
        if self.present_image:
            screen.blit(self.present_image, (half_w, 0))
            # 차가운 오버레이
            cold_overlay = pygame.Surface((half_w, self.screen_size[1]), pygame.SRCALPHA)
            cold_overlay.fill((*self.present_tint, 40))
            screen.blit(cold_overlay, (half_w, 0))

        # 과거 파티클 (빛)
        for p in self.past_particles:
            glow_surf = pygame.Surface((int(p['size'] * 4), int(p['size'] * 4)), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (255, 240, 200, p['alpha']),
                             (int(p['size'] * 2), int(p['size'] * 2)), int(p['size']))
            screen.blit(glow_surf, (int(p['x']), int(p['y'])))

        # 현재 파티클 (재)
        for p in self.present_particles:
            pygame.draw.circle(screen, (80, 80, 80, p['alpha']),
                             (int(p['x']), int(p['y'])), int(p['size']))

        # 분할선 (글로우 효과)
        wave_offset = int(math.sin(self.split_wave) * 5)
        for i in range(-10, 11, 2):
            alpha = 255 - abs(i) * 20
            x = half_w + wave_offset + i
            pygame.draw.line(screen, (255, 255, 255, max(0, alpha)), (x, 0), (x, self.screen_size[1]), 1)

        # 레이블
        if self.phase == self.PHASE_SPLIT_SCREEN and "medium" in self.fonts:
            past_label = self.fonts["medium"].render("과거", True, self.past_tint)
            present_label = self.fonts["medium"].render("현재", True, self.present_tint)

            screen.blit(past_label, (half_w // 2 - past_label.get_width() // 2, 30))
            screen.blit(present_label, (half_w + half_w // 2 - present_label.get_width() // 2, 30))

        # 페이드
        if self.phase == self.PHASE_FADEIN:
            fade_surf = pygame.Surface(self.screen_size)
            fade_surf.fill((0, 0, 0))
            fade_surf.set_alpha(255 - int(self.fade_alpha))
            screen.blit(fade_surf, (0, 0))

        # 대사
        if self.phase == self.PHASE_DIALOGUE:
            self._render_dialogue(screen)

    def _render_dialogue(self, screen: pygame.Surface):
        """대화창 렌더링"""
        if not self.dialogue_after or self.current_dialogue_index >= len(self.dialogue_after):
            return
        dialogue = self.dialogue_after[self.current_dialogue_index]
        speaker = dialogue.get("speaker", "")
        portrait = self._get_portrait(speaker) if speaker else None

        render_dialogue_box(screen, self.screen_size, self.fonts, dialogue,
                           self.dialogue_text, self.typing_progress, self.waiting_for_click,
                           box_color=(30, 30, 40, 230), border_color=(200, 200, 220),
                           text_color=(255, 255, 255), box_height=180,
                           has_portrait=(portrait is not None), portrait=portrait)


class RadioWaveEffect(BaseCutsceneEffect):
    """
    어머니 신호 컷씬 (Act 4)

    특징:
    - 통신 기지에서 수신된 희미한 신호
    - 라디오 웨이브 시각화
    - 노이즈 속 어머니 목소리
    - 신호 강도 게이지
    """

    PHASE_SCANNING = 10
    PHASE_SIGNAL_FOUND = 11
    PHASE_VOICE_DETECTED = 12

    def __init__(self, screen_size: tuple, mother_voice_text: str = None,
                 dialogue_after: list = None, sound_manager=None,
                 special_effects: dict = None, scene_id: str = "radio_wave_scene"):
        super().__init__(screen_size, None, dialogue_after,
                        sound_manager, special_effects, scene_id)

        self.typing_speed = 20.0

        # 라디오 웨이브 데이터
        self.wave_data = [0.0] * 200
        self.wave_speed = 50.0
        self.signal_strength = 0.0
        self.target_signal = 0.0

        # 노이즈
        self.noise_intensity = 1.0
        self.noise_particles = []
        for _ in range(100):
            self.noise_particles.append({
                'x': random.randint(0, screen_size[0]),
                'y': random.randint(0, screen_size[1]),
                'size': random.randint(1, 3),
            })

        # 어머니 목소리 텍스트 (신호에서 추출)
        self.mother_voice_text = mother_voice_text or "...아르테미스... 살아있다면... 우리를 찾아..."
        self.decoded_text = ""
        self.decode_progress = 0.0

        # 스캔 주파수
        self.frequency = 0.0
        self.target_frequency = 7.42  # 목표 주파수

        # 배경색
        self.bg_color = (10, 15, 25)

        # 색상
        self.wave_color = (0, 255, 150)
        self.signal_color = (255, 200, 50)

    def _on_fadein_complete(self):
        """페이드인 완료"""
        self.phase = self.PHASE_SCANNING
        self.phase_timer = 0.0

    def update(self, dt: float):
        """업데이트"""
        if not self.is_alive:
            return

        self.phase_timer += dt

        # 웨이브 데이터 업데이트
        self.wave_data.pop(0)
        if self.phase == self.PHASE_SIGNAL_FOUND or self.phase == self.PHASE_VOICE_DETECTED:
            # 신호 감지됨: 규칙적인 패턴
            wave_value = math.sin(self.phase_timer * 10) * 0.8
            wave_value += random.uniform(-0.1, 0.1) * self.noise_intensity
        else:
            # 스캔 중: 랜덤 노이즈
            wave_value = random.uniform(-1, 1) * self.noise_intensity

        self.wave_data.append(wave_value)

        # 노이즈 파티클 업데이트
        if random.random() < 0.3:
            for p in self.noise_particles:
                p['x'] = random.randint(0, self.screen_size[0])
                p['y'] = random.randint(0, self.screen_size[1])

        # 페이즈 처리
        if self.phase == self.PHASE_FADEIN:
            if self._update_fadein(dt):
                self._on_fadein_complete()

        elif self.phase == self.PHASE_SCANNING:
            # 주파수 스캔
            self.frequency += dt * 2
            if self.frequency >= self.target_frequency:
                self.phase = self.PHASE_SIGNAL_FOUND
                self.phase_timer = 0.0
                self.signal_strength = 0.3

        elif self.phase == self.PHASE_SIGNAL_FOUND:
            # 신호 강화
            self.signal_strength = min(1.0, self.signal_strength + dt * 0.3)
            self.noise_intensity = max(0.2, 1.0 - self.signal_strength)

            if self.signal_strength >= 0.8:
                self.phase = self.PHASE_VOICE_DETECTED
                self.phase_timer = 0.0

        elif self.phase == self.PHASE_VOICE_DETECTED:
            # 텍스트 디코딩
            self.decode_progress = min(1.0, self.decode_progress + dt * 0.3)
            decoded_len = int(len(self.mother_voice_text) * self.decode_progress)
            self.decoded_text = self.mother_voice_text[:decoded_len]

            if self.decode_progress >= 1.0 and self.phase_timer > 3.0:
                self._transition_to_dialogue()

        elif self.phase == self.PHASE_DIALOGUE:
            if self._update_dialogue(dt):
                self._transition_to_fadeout()

        elif self.phase == self.PHASE_FADEOUT:
            if self._update_fadeout(dt):
                self._on_fadeout_complete()

    def render(self, screen: pygame.Surface):
        """렌더링"""
        screen.fill(self.bg_color)

        # 그리드 배경
        grid_color = (30, 40, 50)
        for x in range(0, self.screen_size[0], 50):
            pygame.draw.line(screen, grid_color, (x, 0), (x, self.screen_size[1]))
        for y in range(0, self.screen_size[1], 50):
            pygame.draw.line(screen, grid_color, (0, y), (self.screen_size[0], y))

        # 노이즈 파티클
        for p in self.noise_particles:
            alpha = int(self.noise_intensity * 150)
            pygame.draw.rect(screen, (100, 100, 100, alpha),
                           (p['x'], p['y'], p['size'], p['size']))

        # 라디오 웨이브
        wave_height = 150
        wave_y = self.screen_size[1] // 2
        wave_width = self.screen_size[0] - 100

        points = []
        for i, val in enumerate(self.wave_data):
            x = 50 + int(i * wave_width / len(self.wave_data))
            y = wave_y + int(val * wave_height)
            points.append((x, y))

        if len(points) > 1:
            # 글로우 효과
            for offset in range(3, 0, -1):
                alpha = 100 - offset * 30
                offset_points = [(p[0], p[1] + offset) for p in points]
                pygame.draw.lines(screen, (*self.wave_color[:3], alpha), False, offset_points, 2)

            pygame.draw.lines(screen, self.wave_color, False, points, 2)

        # 주파수 표시
        if "medium" in self.fonts:
            freq_text = f"주파수: {self.frequency:.2f} MHz"
            freq_surf = self.fonts["medium"].render(freq_text, True, self.wave_color)
            screen.blit(freq_surf, (50, 50))

        # 신호 강도 게이지
        gauge_x = self.screen_size[0] - 200
        gauge_y = 50
        gauge_width = 150
        gauge_height = 20

        pygame.draw.rect(screen, (50, 50, 50), (gauge_x, gauge_y, gauge_width, gauge_height))
        fill_width = int(gauge_width * self.signal_strength)
        if fill_width > 0:
            color = self.signal_color if self.signal_strength > 0.5 else self.wave_color
            pygame.draw.rect(screen, color, (gauge_x, gauge_y, fill_width, gauge_height))
        pygame.draw.rect(screen, (100, 100, 100), (gauge_x, gauge_y, gauge_width, gauge_height), 2)

        if "small" in self.fonts:
            label = self.fonts["small"].render("신호 강도", True, (150, 150, 150))
            screen.blit(label, (gauge_x, gauge_y - 20))

        # 디코딩된 텍스트
        if self.phase == self.PHASE_VOICE_DETECTED and self.decoded_text:
            if "medium" in self.fonts:
                text_y = self.screen_size[1] - 200
                # 글로우 박스
                box_rect = pygame.Rect(50, text_y - 20, self.screen_size[0] - 100, 80)
                pygame.draw.rect(screen, (20, 30, 40, 200), box_rect, border_radius=10)
                pygame.draw.rect(screen, self.signal_color, box_rect, 2, border_radius=10)

                decoded_surf = self.fonts["medium"].render(self.decoded_text, True, self.signal_color)
                screen.blit(decoded_surf, (70, text_y))

                label = self.fonts["small"].render("수신된 메시지:", True, (150, 150, 150))
                screen.blit(label, (70, text_y - 25))

        # 스캔 중 텍스트
        if self.phase == self.PHASE_SCANNING and "medium" in self.fonts:
            scan_text = "주파수 스캔 중..."
            alpha = int(128 + 127 * math.sin(self.phase_timer * 5))
            scan_surf = self.fonts["medium"].render(scan_text, True, (*self.wave_color[:3], alpha))
            x = self.screen_size[0] // 2 - scan_surf.get_width() // 2
            screen.blit(scan_surf, (x, self.screen_size[1] - 100))

        # 페이드
        if self.phase == self.PHASE_FADEIN:
            fade_surf = pygame.Surface(self.screen_size)
            fade_surf.fill((0, 0, 0))
            fade_surf.set_alpha(255 - int(self.fade_alpha))
            screen.blit(fade_surf, (0, 0))

        # 대사
        if self.phase == self.PHASE_DIALOGUE:
            self._render_dialogue(screen)

    def _render_dialogue(self, screen: pygame.Surface):
        """대화창 렌더링"""
        if not self.dialogue_after or self.current_dialogue_index >= len(self.dialogue_after):
            return
        dialogue = self.dialogue_after[self.current_dialogue_index]
        speaker = dialogue.get("speaker", "")
        portrait = self._get_portrait(speaker) if speaker else None

        render_dialogue_box(screen, self.screen_size, self.fonts, dialogue,
                           self.dialogue_text, self.typing_progress, self.waiting_for_click,
                           box_color=(15, 25, 35, 230), border_color=(0, 200, 150),
                           text_color=(200, 255, 230), box_height=180,
                           has_portrait=(portrait is not None), portrait=portrait)


class CountdownEffect(BaseCutsceneEffect):
    """
    카운트다운 컷씬 (Act 5)

    특징:
    - 최종 결전 전 카운트다운
    - 긴박한 분위기
    - 숫자가 화면에 크게 표시
    - 각 숫자마다 회상/결의 대사
    """

    PHASE_COUNTDOWN = 10
    PHASE_ZERO = 11

    def __init__(self, screen_size: tuple, countdown_start: int = 10,
                 countdown_messages: list = None, dialogue_after: list = None,
                 sound_manager=None, special_effects: dict = None,
                 scene_id: str = "countdown_scene"):
        super().__init__(screen_size, None, dialogue_after,
                        sound_manager, special_effects, scene_id)

        self.typing_speed = 30.0

        # 카운트다운 설정
        self.countdown_start = countdown_start
        self.current_count = countdown_start
        self.count_timer = 0.0
        self.count_interval = 1.5  # 각 숫자 표시 시간

        # 각 숫자별 메시지
        self.countdown_messages = countdown_messages or [
            "모든 것이 이 순간을 위해...",
            "10년의 기다림...",
            "잃어버린 것들을 위해...",
            "가족을 되찾기 위해...",
            "희망을 지키기 위해...",
            "포기하지 않았기에...",
            "함께 싸워왔기에...",
            "이제 마지막...",
            "두려움은 없어...",
            "시작이다!",
        ]

        self.current_message = ""
        self.message_alpha = 0

        # 시각 효과
        self.pulse_scale = 1.0
        self.shake_offset = (0, 0)
        self.warning_flash = 0.0

        # 파티클 (불꽃)
        self.spark_particles = []

        # 배경 색상 (긴박한 빨간 톤)
        self.bg_colors = [
            (20, 10, 15),  # 시작
            (40, 15, 20),  # 중간
            (60, 20, 25),  # 끝
        ]

    def _on_fadein_complete(self):
        """페이드인 완료"""
        self.phase = self.PHASE_COUNTDOWN
        self.phase_timer = 0.0
        self.current_count = self.countdown_start

    def _create_sparks(self):
        """불꽃 파티클 생성"""
        center = (self.screen_size[0] // 2, self.screen_size[1] // 2)
        for _ in range(20):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(100, 300)
            self.spark_particles.append({
                'x': center[0],
                'y': center[1],
                'vx': math.cos(angle) * speed,
                'vy': math.sin(angle) * speed,
                'life': 1.0,
                'color': random.choice([(255, 200, 100), (255, 150, 50), (255, 100, 50)]),
            })

    def update(self, dt: float):
        """업데이트"""
        if not self.is_alive:
            return

        self.phase_timer += dt
        self.count_timer += dt

        # 경고 플래시
        self.warning_flash += dt * 10
        flash_intensity = (math.sin(self.warning_flash) + 1) / 2

        # 펄스 효과
        self.pulse_scale = 1.0 + 0.1 * math.sin(self.phase_timer * 5)

        # 화면 흔들림 (카운트가 낮을수록 강해짐)
        shake_intensity = max(0, (5 - self.current_count)) * 2
        self.shake_offset = (
            random.randint(-int(shake_intensity), int(shake_intensity)),
            random.randint(-int(shake_intensity), int(shake_intensity))
        )

        # 파티클 업데이트
        for p in self.spark_particles[:]:
            p['x'] += p['vx'] * dt
            p['y'] += p['vy'] * dt
            p['vy'] += 200 * dt  # 중력
            p['life'] -= dt * 2
            if p['life'] <= 0:
                self.spark_particles.remove(p)

        # 페이즈 처리
        if self.phase == self.PHASE_FADEIN:
            if self._update_fadein(dt):
                self._on_fadein_complete()

        elif self.phase == self.PHASE_COUNTDOWN:
            if self.count_timer >= self.count_interval:
                self.count_timer = 0
                self.current_count -= 1
                self._create_sparks()

                # 메시지 업데이트
                msg_index = self.countdown_start - self.current_count - 1
                if 0 <= msg_index < len(self.countdown_messages):
                    self.current_message = self.countdown_messages[msg_index]
                    self.message_alpha = 255

                if self.current_count <= 0:
                    self.phase = self.PHASE_ZERO
                    self.phase_timer = 0.0

            # 메시지 페이드
            self.message_alpha = max(0, self.message_alpha - 100 * dt)

        elif self.phase == self.PHASE_ZERO:
            if self.phase_timer > 2.0:
                self._transition_to_dialogue()

        elif self.phase == self.PHASE_DIALOGUE:
            if self._update_dialogue(dt):
                self._transition_to_fadeout()

        elif self.phase == self.PHASE_FADEOUT:
            if self._update_fadeout(dt):
                self._on_fadeout_complete()

    def render(self, screen: pygame.Surface):
        """렌더링"""
        # 배경 그라데이션 (긴박함 증가)
        progress = 1 - (self.current_count / self.countdown_start) if self.countdown_start > 0 else 1
        bg_color = [
            int(self.bg_colors[0][i] + (self.bg_colors[2][i] - self.bg_colors[0][i]) * progress)
            for i in range(3)
        ]
        screen.fill(bg_color)

        # 경고 플래시 오버레이
        flash_intensity = (math.sin(self.warning_flash) + 1) / 2
        if self.current_count <= 3:
            flash_surf = pygame.Surface(self.screen_size, pygame.SRCALPHA)
            flash_surf.fill((100, 20, 20, int(flash_intensity * 50)))
            screen.blit(flash_surf, (0, 0))

        # 원형 웨이브 (숫자 주변)
        center = (self.screen_size[0] // 2 + self.shake_offset[0],
                 self.screen_size[1] // 2 + self.shake_offset[1])

        wave_radius = int(100 + (self.count_timer / self.count_interval) * 200)
        wave_alpha = int(100 * (1 - self.count_timer / self.count_interval))
        if wave_alpha > 0:
            for r in range(wave_radius, wave_radius - 20, -5):
                if r > 0:
                    alpha = int(wave_alpha * (1 - (wave_radius - r) / 20))
                    pygame.draw.circle(screen, (255, 100, 100, alpha), center, r, 2)

        # 카운트다운 숫자
        if self.phase in [self.PHASE_COUNTDOWN, self.PHASE_ZERO]:
            count_text = str(max(0, self.current_count))
            if "xlarge" in self.fonts:
                font = self.fonts["xlarge"]
            elif "large" in self.fonts:
                font = self.fonts["large"]
            else:
                font = pygame.font.Font(None, 200)

            # 글로우 효과
            for glow_offset in range(10, 0, -2):
                glow_color = (255, 100 + glow_offset * 10, 100 + glow_offset * 10)
                glow_surf = font.render(count_text, True, glow_color)
                glow_surf.set_alpha(50 - glow_offset * 4)

                scaled_size = (int(glow_surf.get_width() * self.pulse_scale),
                              int(glow_surf.get_height() * self.pulse_scale))
                scaled = pygame.transform.smoothscale(glow_surf, scaled_size)

                x = center[0] - scaled.get_width() // 2
                y = center[1] - scaled.get_height() // 2 - 50
                screen.blit(scaled, (x, y))

            # 메인 숫자
            number_surf = font.render(count_text, True, (255, 220, 200))
            scaled_size = (int(number_surf.get_width() * self.pulse_scale),
                          int(number_surf.get_height() * self.pulse_scale))
            scaled = pygame.transform.smoothscale(number_surf, scaled_size)

            x = center[0] - scaled.get_width() // 2
            y = center[1] - scaled.get_height() // 2 - 50
            screen.blit(scaled, (x, y))

        # 메시지
        if self.current_message and self.message_alpha > 0:
            if "medium" in self.fonts:
                msg_surf = self.fonts["medium"].render(self.current_message, True, (255, 230, 200))
                msg_surf.set_alpha(int(self.message_alpha))
                x = center[0] - msg_surf.get_width() // 2
                y = center[1] + 100
                screen.blit(msg_surf, (x, y))

        # 불꽃 파티클
        for p in self.spark_particles:
            alpha = int(255 * p['life'])
            size = int(3 * p['life'])
            if size > 0:
                spark_surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
                pygame.draw.circle(spark_surf, (*p['color'], alpha), (size, size), size)
                screen.blit(spark_surf, (int(p['x']) - size, int(p['y']) - size))

        # PHASE_ZERO 특별 효과
        if self.phase == self.PHASE_ZERO:
            # 화면 전체 플래시
            flash_progress = min(1.0, self.phase_timer / 0.5)
            if flash_progress < 1.0:
                flash_surf = pygame.Surface(self.screen_size, pygame.SRCALPHA)
                flash_surf.fill((255, 255, 255, int(255 * (1 - flash_progress))))
                screen.blit(flash_surf, (0, 0))

            # "전투 개시" 텍스트
            if self.phase_timer > 0.5 and "large" in self.fonts:
                battle_text = "전투 개시"
                battle_surf = self.fonts["large"].render(battle_text, True, (255, 200, 150))
                x = center[0] - battle_surf.get_width() // 2
                y = center[1] - battle_surf.get_height() // 2 - 50
                screen.blit(battle_surf, (x, y))

        # 페이드
        if self.phase == self.PHASE_FADEIN:
            fade_surf = pygame.Surface(self.screen_size)
            fade_surf.fill((0, 0, 0))
            fade_surf.set_alpha(255 - int(self.fade_alpha))
            screen.blit(fade_surf, (0, 0))

        # 대사
        if self.phase == self.PHASE_DIALOGUE:
            self._render_dialogue(screen)

    def _render_dialogue(self, screen: pygame.Surface):
        """대화창 렌더링"""
        if not self.dialogue_after or self.current_dialogue_index >= len(self.dialogue_after):
            return
        dialogue = self.dialogue_after[self.current_dialogue_index]
        speaker = dialogue.get("speaker", "")
        portrait = self._get_portrait(speaker) if speaker else None

        render_dialogue_box(screen, self.screen_size, self.fonts, dialogue,
                           self.dialogue_text, self.typing_progress, self.waiting_for_click,
                           box_color=(40, 20, 25, 230), border_color=(255, 150, 100),
                           text_color=(255, 240, 230), box_height=180,
                           has_portrait=(portrait is not None), portrait=portrait)
