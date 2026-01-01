'''
Transition Effects - Scene and background transitions
전환 효과 - 씬 및 배경 전환 효과

Extracted from objects.py
'''
import pygame
import math
import random
from typing import Tuple
from pathlib import Path
import config


# ============================================================
# Wave Transition Effect
# ============================================================

class WaveTransitionEffect:
    """웨이브 전환 효과 - 화면 어두워짐과 동시에 이미지가 중앙에서 서서히 등장 (외곽 페이드 적용)"""

    # 페이즈 상수
    PHASE_DARKEN = 0  # 화면 어두워지면서 이미지 등장
    PHASE_SHOW_IMAGE = 1  # 이미지 유지
    PHASE_BRIGHTEN = 2  # 화면 밝아지면서 이미지 사라짐
    PHASE_DONE = 3  # 완료

    def __init__(
        self,
        screen_size: Tuple[int, int],
        image_path: str = None,
        darken_duration: float = 3.5,
        image_duration: float = 2.0,
        brighten_duration: float = 3.0,
    ):
        self.screen_size = screen_size
        self.darken_duration = darken_duration  # 아주 느리게: 3.5초
        self.image_duration = image_duration  # 유지: 2초
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
                path = Path(image_path)
                if path.exists():
                    loaded_img = pygame.image.load(str(path)).convert_alpha()
                    # 화면 크기에 맞게 스케일 (비율 유지, 85% 크기 - 더 크게)
                    img_w, img_h = loaded_img.get_size()
                    scale = min(
                        screen_size[0] * 0.85 / img_w, screen_size[1] * 0.85 / img_h
                    )
                    new_size = (int(img_w * scale), int(img_h * scale))
                    self.original_image = pygame.transform.smoothscale(
                        loaded_img, new_size
                    )
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
            eased_progress = progress**0.7  # ease-out
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
                eased_progress = progress**0.5  # 더 천천히 시작
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
                eased_progress = progress**2  # 천천히 사라짐
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
                        scaled_img = pygame.transform.smoothscale(
                            self.image, (new_w, new_h)
                        )
                    else:
                        scaled_img = self.image
                else:
                    scaled_img = self.image

                # 이미지 중앙 배치
                img_rect = scaled_img.get_rect(
                    center=(self.screen_size[0] // 2, self.screen_size[1] // 2)
                )
                img_copy = scaled_img.copy()
                img_copy.set_alpha(img_alpha)
                screen.blit(img_copy, img_rect)


# ============================================================
# Background Transition Effect
# ============================================================

class BackgroundTransition:
    """배경 전환 효과 클래스 - 웨이브 시작 시 배경 이미지 전환"""

    def __init__(
        self,
        old_bg: pygame.Surface,
        new_bg: pygame.Surface,
        screen_size: Tuple[int, int],
        effect_type: str,
        duration: float,
    ):
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
            small_surf = pygame.transform.scale(
                self.old_bg, (small_width, small_height)
            )

            # 업스케일 (픽셀화 효과)
            pixelated = pygame.transform.scale(
                small_surf, (self.screen_width, self.screen_height)
            )
            screen.blit(pixelated, (0, 0))
        # 후반부: 새 배경 역픽셀화
        else:
            pixel_progress = (progress - 0.5) * 2
            pixel_size = int(20 - 19 * pixel_progress)
            pixel_size = max(1, pixel_size)

            small_width = max(1, self.screen_width // pixel_size)
            small_height = max(1, self.screen_height // pixel_size)
            small_surf = pygame.transform.scale(
                self.new_bg, (small_width, small_height)
            )

            pixelated = pygame.transform.scale(
                small_surf, (self.screen_width, self.screen_height)
            )
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


# ============================================================
# Parallax Layer
# ============================================================

class ParallaxLayer:
    """배경 패럴랙스 레이어 - 별 배경 (반짝임 효과 포함)"""

    def __init__(
        self,
        screen_size: Tuple[int, int],
        star_count: int,
        speed_factor: float,
        star_size: int,
        color: Tuple[int, int, int],
        twinkle: bool = False,
    ):
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
            self.stars.append(
                {
                    "pos": pygame.math.Vector2(x, y),
                    "brightness": 1.0,  # 현재 밝기 (0.0 ~ 1.5)
                    "twinkle_timer": 0.0,  # 반짝임 타이머
                    "twinkle_duration": 0.0,  # 반짝임 지속 시간
                    "is_twinkling": False,  # 반짝이고 있는지
                }
            )

    def update(
        self,
        dt: float,
        player_velocity: pygame.math.Vector2 = None,
        speed_multiplier: float = 1.0,
    ):
        """레이어 업데이트 - 플레이어 속도에 반응 + 반짝임"""
        # 속도 배율 적용
        current_speed_factor = self.base_speed_factor * speed_multiplier

        if player_velocity is None:
            # 기본 스크롤
            scroll_speed = 50 * current_speed_factor * dt
            for star_data in self.stars:
                star_data["pos"].y += scroll_speed
        else:
            # 플레이어 움직임에 반응
            for star_data in self.stars:
                star_data["pos"].x -= player_velocity.x * current_speed_factor * dt
                star_data["pos"].y -= player_velocity.y * current_speed_factor * dt

        # 화면 밖으로 나간 별 재배치
        for star_data in self.stars:
            star = star_data["pos"]
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
                if star_data["is_twinkling"]:
                    # 반짝임 진행
                    star_data["twinkle_timer"] += dt
                    progress = (
                        star_data["twinkle_timer"] / star_data["twinkle_duration"]
                    )

                    if progress >= 1.0:
                        # 반짝임 종료
                        star_data["is_twinkling"] = False
                        star_data["brightness"] = 1.0
                    else:
                        # 사인파로 밝기 변화
                        brightness_range = config.STAR_TWINKLE_SETTINGS[
                            "brightness_range"
                        ]
                        star_data["brightness"] = 1.0 + (
                            brightness_range[1] - 1.0
                        ) * math.sin(progress * math.pi * 2)
                else:
                    # 반짝임 시작 확률
                    if random.random() < config.STAR_TWINKLE_SETTINGS["twinkle_chance"]:
                        star_data["is_twinkling"] = True
                        star_data["twinkle_timer"] = 0.0
                        duration_range = config.STAR_TWINKLE_SETTINGS[
                            "twinkle_duration"
                        ]
                        star_data["twinkle_duration"] = random.uniform(
                            duration_range[0], duration_range[1]
                        )

    def draw(self, screen: pygame.Surface):
        """레이어 그리기 (반짝임 효과 적용)"""
        for star_data in self.stars:
            star = star_data["pos"]
            brightness = star_data["brightness"]

            # 밝기에 따라 색상 조정
            adjusted_color = tuple(min(255, int(c * brightness)) for c in self.color)

            pygame.draw.circle(
                screen, adjusted_color, (int(star.x), int(star.y)), self.star_size
            )
