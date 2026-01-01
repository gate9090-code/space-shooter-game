'''
Screen Effects - Visual feedback effects for game events
화면 효과 - 파티클, 플래시, 쉐이크 등

Extracted from objects.py
'''
import pygame
import math
import random
from typing import Tuple, List, Optional
import config



# ============================================================
# Particle System
# ============================================================

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




# ============================================================
# Screen Flash Effects
# ============================================================

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




# ============================================================
# Screen Shake
# ============================================================

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




# ============================================================
# Text Effects
# ============================================================

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




# ============================================================
# Time Slow Effect
# ============================================================

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




# ============================================================
# Particle Variants
# ============================================================

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




# ============================================================
# Visual Transition Effects
# ============================================================

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




# ============================================================
# Combat Feedback Effects
# ============================================================

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


# ============================================================
# Shockwave Effect
# ============================================================

class Shockwave:
    """충격파 효과 - 중심에서 확장되는 원형 링 (지연 시간 지원)"""

    def __init__(
        self,
        center: Tuple[float, float],
        max_radius: float,
        duration: float = 0.4,
        color: Tuple[int, int, int] = (255, 150, 50),
        width: int = 3,
        delay: float = 0.0,
    ):
        self.center = pygame.math.Vector2(center) if not isinstance(center, pygame.math.Vector2) else center
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
        pygame.draw.circle(
            surf, color_with_alpha, (size // 2, size // 2), current_radius, self.width
        )

        screen.blit(
            surf, (int(self.center.x - size // 2), int(self.center.y - size // 2))
        )


# ============================================================
# Lightning Effect
# ============================================================

class LightningEffect:
    """번개 체인 시각 효과 - 이미지 기반"""

    # 클래스 변수로 이미지 캐싱
    _lightning_image = None
    _image_loaded = False

    def __init__(
        self,
        start_pos: Tuple[float, float],
        end_pos: Tuple[float, float],
        duration: float = 0.4,
    ):
        """
        번개 효과 초기화

        Args:
            start_pos: 시작 위치 (x, y)
            end_pos: 끝 위치 (x, y)
            duration: 지속 시간 (초)
        """
        self.start_pos = pygame.math.Vector2(start_pos)
        self.end_pos = pygame.math.Vector2(end_pos)
        self.duration = duration
        self.elapsed = 0.0
        self.is_alive = True

        # 이미지 로드 (최초 1회만)
        if not LightningEffect._image_loaded:
            LightningEffect._load_image()

        # 이미지 기반 번개 준비
        if LightningEffect._lightning_image:
            self._prepare_image_lightning()
        else:
            self.scaled_image = None

    @classmethod
    def _load_image(cls):
        """번개 이미지 로드 (클래스 메서드)"""
        cls._image_loaded = True
        try:
            from pathlib import Path

            image_path = Path("assets/images/effects/lightning_chain.png")
            if image_path.exists():
                cls._lightning_image = pygame.image.load(
                    str(image_path)
                ).convert_alpha()
            else:
                cls._lightning_image = None
        except:
            cls._lightning_image = None

    def _prepare_image_lightning(self):
        """이미지 기반 번개 준비"""
        # 시작-끝 거리와 각도 계산
        direction = self.end_pos - self.start_pos
        distance = direction.length()

        if distance == 0:
            self.scaled_image = None
            return

        angle = math.degrees(math.atan2(direction.y, direction.x))

        # 이미지를 거리에 맞게 스케일링
        img_width = LightningEffect._lightning_image.get_width()
        scale_factor = distance / img_width if img_width > 0 else 1.0

        scaled_width = int(img_width * scale_factor)
        scaled_height = int(
            LightningEffect._lightning_image.get_height() * scale_factor
        )

        if scaled_width <= 0 or scaled_height <= 0:
            self.scaled_image = None
            return

        self.scaled_image = pygame.transform.scale(
            LightningEffect._lightning_image, (scaled_width, scaled_height)
        )

        # 이미지 회전
        self.rotated_image = pygame.transform.rotate(self.scaled_image, -angle)

        # 렌더링 위치 계산
        rect = self.rotated_image.get_rect()
        rect.center = (
            (self.start_pos.x + self.end_pos.x) / 2,
            (self.start_pos.y + self.end_pos.y) / 2,
        )
        self.render_rect = rect

    def update(self, dt: float):
        """번개 효과 업데이트"""
        self.elapsed += dt
        if self.elapsed >= self.duration:
            self.is_alive = False

    def draw(self, screen: pygame.Surface):
        """번개 효과 그리기"""
        if not self.is_alive:
            return

        # 알파값 계산 (페이드아웃)
        alpha = int(255 * (1.0 - self.elapsed / self.duration))

        if self.scaled_image and hasattr(self, "rotated_image"):
            # 이미지 기반 번개
            temp_image = self.rotated_image.copy()
            temp_image.set_alpha(alpha)
            screen.blit(temp_image, self.render_rect)
        else:
            # 폴백: 프로시저럴 번개
            self._draw_procedural(screen, alpha)

    def _draw_procedural(self, screen: pygame.Surface, alpha: int):
        """프로시저럴 번개 그리기 (이미지가 없을 때 폴백)"""
        # 번개 경로 생성
        points = [self.start_pos]
        direction = self.end_pos - self.start_pos
        distance = direction.length()

        if distance > 0:
            direction = direction.normalize()
            segments = max(3, int(distance / 30))

            for i in range(1, segments):
                progress = i / segments
                base_point = self.start_pos + direction * (distance * progress)
                perpendicular = pygame.math.Vector2(-direction.y, direction.x)
                offset = perpendicular * random.uniform(-15, 15)
                points.append(base_point + offset)

        points.append(self.end_pos)

        # 번개 색상
        colors = [
            (200, 220, 255),
            (255, 255, 255),
            (150, 200, 255),
        ]

        # 번개 그리기
        for width, color in [(5, colors[2]), (3, colors[0]), (1, colors[1])]:
            if len(points) >= 2:
                try:
                    pygame.draw.lines(
                        screen,
                        color,
                        False,
                        [(int(p.x), int(p.y)) for p in points],
                        width,
                    )
                except:
                    pass


# ============================================================
# Skill Effects
# ============================================================

class ExecuteEffect:
    """처형 스킬 시각 효과 - 적이 처형될 때 표시"""

    def __init__(self, pos: Tuple[float, float], duration: float = 0.5):
        self.pos = pygame.math.Vector2(pos)
        self.duration = duration
        self.age = 0.0
        self.is_alive = True

    def update(self, dt: float):
        """효과 업데이트"""
        self.age += dt
        if self.age >= self.duration:
            self.is_alive = False

    def draw(self, screen: pygame.Surface):
        """효과 그리기"""
        if not self.is_alive:
            return

        progress = self.age / self.duration
        alpha = int(255 * (1 - progress))

        # 십자가 모양 그리기
        size = 30
        color = (200, 0, 0, alpha)

        # 세로선
        pygame.draw.line(
            screen,
            color,
            (int(self.pos.x), int(self.pos.y - size)),
            (int(self.pos.x), int(self.pos.y + size)),
            3
        )
        # 가로선
        pygame.draw.line(
            screen,
            color,
            (int(self.pos.x - size), int(self.pos.y)),
            (int(self.pos.x + size), int(self.pos.y)),
            3
        )


class StarfallEffect:
    """별똥별 스킬 시각 효과"""

    def __init__(self, pos: Tuple[float, float], duration: float = 0.8):
        self.pos = pygame.math.Vector2(pos)
        self.duration = duration
        self.age = 0.0
        self.is_alive = True
        self.max_radius = 100

    def update(self, dt: float):
        """효과 업데이트"""
        self.age += dt
        if self.age >= self.duration:
            self.is_alive = False

    def draw(self, screen: pygame.Surface):
        """효과 그리기"""
        if not self.is_alive:
            return

        progress = self.age / self.duration
        current_radius = int(self.max_radius * progress)
        alpha = int(255 * (1 - progress))

        # 밝은 노란색 원형 폭발
        surf = pygame.Surface((current_radius * 2, current_radius * 2), pygame.SRCALPHA)

        # 여러 겹의 원으로 빛나는 효과
        for i in range(3, 0, -1):
            radius = int(current_radius * i / 3)
            layer_alpha = int(alpha * i / 3)
            color = (255, 220, 100, layer_alpha)
            pygame.draw.circle(surf, color, (current_radius, current_radius), radius)

        screen.blit(surf, (int(self.pos.x - current_radius), int(self.pos.y - current_radius)))


# =============================================================================
# 2막 벙커 포신 연출 효과
# =============================================================================

