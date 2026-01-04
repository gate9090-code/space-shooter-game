"""
물리 기반 효과 시스템 (Physics-Based Effects)

중력, 충돌, 바운스, 마찰 등 물리 시뮬레이션을 포함한 효과들
"""

import pygame
import math
import random
from typing import Tuple, Optional, List
from pathlib import Path


class SupplyDrop:
    """
    보급품 투하 효과 클래스

    특징:
    - 중력 시뮬레이션
    - 지면 충돌 감지
    - 바운스 효과 (튕김)
    - 마찰/감속
    - 회전 애니메이션
    - 착지 시 파티클 효과
    """

    def __init__(
        self,
        start_pos: Tuple[float, float],
        target_pos: Optional[Tuple[float, float]] = None,
        image_path: str = "bullet_storage.png",
        gravity: float = 800.0,  # 픽셀/초^2
        bounce_factor: float = 0.6,  # 반발 계수 (0~1)
        friction: float = 0.95,  # 마찰 계수
        rotation_speed: float = 180.0,  # 도/초
        size: float = 64.0,
        ground_y: Optional[float] = None  # 지면 높이 (None이면 화면 하단)
    ):
        """
        Args:
            start_pos: 시작 위치 (x, y)
            target_pos: 목표 위치 (x, y). None이면 수직 낙하
            image_path: 보급품 이미지 경로
            gravity: 중력 가속도
            bounce_factor: 바운스 강도 (0=튕기지 않음, 1=완전 탄성)
            friction: 수평 마찰 (0~1)
            rotation_speed: 회전 속도
            size: 렌더링 크기
            ground_y: 지면 높이
        """
        self.pos = pygame.math.Vector2(start_pos)
        self.velocity = pygame.math.Vector2(0, 0)
        self.gravity = gravity
        self.bounce_factor = bounce_factor
        self.friction = friction
        self.rotation_speed = rotation_speed
        self.size = size

        # 지면 설정
        if ground_y is None:
            self.ground_y = 720  # 기본 화면 높이
        else:
            self.ground_y = ground_y

        # 목표 위치가 있으면 초기 수평 속도 설정
        if target_pos is not None:
            target_x = target_pos[0]
            # 포물선 운동을 위한 초기 속도 계산
            dx = target_x - start_pos[0]
            # 간단한 추정: 1초 안에 도달
            self.velocity.x = dx / 1.0

        # 이미지 로드
        try:
            full_path = Path(image_path)
            if not full_path.exists():
                # 상대 경로로 시도
                full_path = Path("assets/images/gameplay") / image_path

            self.original_image = pygame.image.load(str(full_path)).convert_alpha()
            self.original_image = pygame.transform.scale(
                self.original_image,
                (int(size), int(size))
            )
        except Exception as e:
            print(f"WARNING: Failed to load supply drop image {image_path}: {e}")
            # 폴백: 간단한 사각형
            self.original_image = pygame.Surface((int(size), int(size)), pygame.SRCALPHA)
            pygame.draw.rect(self.original_image, (100, 150, 200), (0, 0, int(size), int(size)))
            pygame.draw.rect(self.original_image, (255, 255, 255), (0, 0, int(size), int(size)), 2)

        self.image = self.original_image.copy()

        # 상태
        self.rotation = 0.0
        self.is_alive = True
        self.is_grounded = False
        self.bounce_count = 0
        self.max_bounces = 3
        self.age = 0.0
        self.lifetime = 5.0  # 초 후에 사라짐 (픽업 로직 구현 전까지)

        # 파티클 효과용
        self.impact_particles: List['ImpactParticle'] = []

    def update(self, dt: float):
        """물리 시뮬레이션 업데이트"""
        if not self.is_alive:
            return

        self.age += dt

        # 수명 체크
        if self.age > self.lifetime:
            self.is_alive = False
            return

        # 중력 적용 (공중에 있을 때)
        if not self.is_grounded:
            self.velocity.y += self.gravity * dt

        # 위치 업데이트
        self.pos.x += self.velocity.x * dt
        self.pos.y += self.velocity.y * dt

        # 회전 (떨어질 때만)
        if not self.is_grounded:
            self.rotation += self.rotation_speed * dt
            self.rotation %= 360

        # 지면 충돌 감지
        if self.pos.y >= self.ground_y - self.size / 2:
            self.pos.y = self.ground_y - self.size / 2

            # 바운스 처리
            if abs(self.velocity.y) > 50:  # 최소 속도 이상일 때만 튕김
                self.velocity.y = -self.velocity.y * self.bounce_factor
                self.velocity.x *= self.friction  # 수평 마찰
                self.bounce_count += 1

                # 충격 파티클 생성
                self._create_impact_particles()

                # 최대 바운스 도달 시 정지
                if self.bounce_count >= self.max_bounces:
                    self.is_grounded = True
                    self.velocity = pygame.math.Vector2(0, 0)
                    self.rotation_speed = 0
            else:
                # 속도가 느리면 그냥 정지
                self.is_grounded = True
                self.velocity = pygame.math.Vector2(0, 0)
                self.rotation_speed = 0

        # 이미지 회전
        self.image = pygame.transform.rotate(self.original_image, -self.rotation)

        # 파티클 업데이트
        for particle in self.impact_particles[:]:
            particle.update(dt)
            if not particle.is_alive:
                self.impact_particles.remove(particle)

    def _create_impact_particles(self):
        """착지 시 충격 파티클 생성"""
        import random

        # 바운스 강도에 따라 파티클 개수 결정
        particle_count = int(10 * abs(self.velocity.y) / 200)
        particle_count = min(particle_count, 20)

        for _ in range(particle_count):
            angle = random.uniform(120, 60)  # 위쪽으로 퍼짐
            speed = random.uniform(50, 150)

            particle = ImpactParticle(
                pos=(self.pos.x, self.ground_y),
                angle=angle,
                speed=speed,
                color=(150, 150, 150),
                size=random.uniform(2, 5)
            )
            self.impact_particles.append(particle)

    def draw(self, screen: pygame.Surface):
        """화면에 그리기"""
        if not self.is_alive:
            return

        # 파티클 먼저 그리기 (뒤에)
        for particle in self.impact_particles:
            particle.draw(screen)

        # 보급품 그리기
        rect = self.image.get_rect(center=(int(self.pos.x), int(self.pos.y)))
        screen.blit(self.image, rect)

        # 그림자 효과 (지면에 가까울수록 진하게)
        if not self.is_grounded:
            shadow_y = self.ground_y
            distance_to_ground = shadow_y - self.pos.y
            shadow_alpha = max(0, 255 - int(distance_to_ground * 2))
            shadow_size = int(self.size * 0.6)

            shadow_surf = pygame.Surface((shadow_size, shadow_size // 3), pygame.SRCALPHA)
            pygame.draw.ellipse(shadow_surf, (0, 0, 0, shadow_alpha), (0, 0, shadow_size, shadow_size // 3))
            shadow_rect = shadow_surf.get_rect(center=(int(self.pos.x), int(shadow_y)))
            screen.blit(shadow_surf, shadow_rect)


class ImpactParticle:
    """충격 파티클 (먼지, 파편 등)"""

    def __init__(
        self,
        pos: Tuple[float, float],
        angle: float,  # 각도 (도)
        speed: float,
        color: Tuple[int, int, int],
        size: float = 3.0,
        gravity: float = 400.0,
        lifetime: float = 0.5
    ):
        self.pos = pygame.math.Vector2(pos)

        # 각도를 라디안으로 변환하여 속도 벡터 계산
        rad = math.radians(angle)
        self.velocity = pygame.math.Vector2(
            speed * math.cos(rad),
            -speed * math.sin(rad)  # y축은 아래가 양수
        )

        self.color = color
        self.size = size
        self.gravity = gravity
        self.lifetime = lifetime
        self.age = 0.0
        self.is_alive = True

    def update(self, dt: float):
        """업데이트"""
        self.age += dt

        if self.age > self.lifetime:
            self.is_alive = False
            return

        # 중력 적용
        self.velocity.y += self.gravity * dt

        # 위치 업데이트
        self.pos += self.velocity * dt

    def draw(self, screen: pygame.Surface):
        """그리기"""
        if not self.is_alive:
            return

        # 페이드 아웃
        alpha = int(255 * (1 - self.age / self.lifetime))
        current_size = int(self.size * (1 - self.age / self.lifetime))

        if current_size > 0:
            surf = pygame.Surface((current_size * 2, current_size * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (*self.color, alpha), (current_size, current_size), current_size)
            screen.blit(surf, (int(self.pos.x - current_size), int(self.pos.y - current_size)))


class DepthEffect:
    """
    깊이감 효과 (Z축 이동 시뮬레이션)

    Scale + Position 변화로 원근감 표현
    예: 워프 포탈, 적 출현 등
    """

    def __init__(
        self,
        image: pygame.Surface,
        start_pos: Tuple[float, float],
        end_pos: Tuple[float, float],
        start_depth: float = 0.0,  # 0=화면, 1=깊은 곳
        end_depth: float = 1.0,
        duration: float = 1.0,
        fade_in: bool = True,
        fade_out: bool = False
    ):
        """
        Args:
            image: 렌더링할 이미지
            start_pos: 시작 위치
            end_pos: 끝 위치
            start_depth: 시작 깊이 (0~1)
            end_depth: 끝 깊이 (0~1)
            duration: 지속 시간
            fade_in: 페이드 인 여부
            fade_out: 페이드 아웃 여부
        """
        self.original_image = image
        self.start_pos = pygame.math.Vector2(start_pos)
        self.end_pos = pygame.math.Vector2(end_pos)
        self.start_depth = start_depth
        self.end_depth = end_depth
        self.duration = duration
        self.fade_in = fade_in
        self.fade_out = fade_out

        self.age = 0.0
        self.is_alive = True

        # 현재 상태
        self.current_pos = self.start_pos.copy()
        self.current_depth = start_depth
        self.current_image = image

    def update(self, dt: float):
        """업데이트"""
        if not self.is_alive:
            return

        self.age += dt

        if self.age >= self.duration:
            self.is_alive = False
            return

        # 진행도 (0~1)
        progress = self.age / self.duration

        # Ease-in-out 곡선
        eased = self._ease_in_out(progress)

        # 위치 보간
        self.current_pos = self.start_pos.lerp(self.end_pos, eased)

        # 깊이 보간
        self.current_depth = self.start_depth + (self.end_depth - self.start_depth) * eased

        # Scale 계산 (깊이에 따라)
        # depth=0 → scale=1.0, depth=1 → scale=0.1
        scale = 1.0 - self.current_depth * 0.9

        # 이미지 변환
        new_size = (
            int(self.original_image.get_width() * scale),
            int(self.original_image.get_height() * scale)
        )

        if new_size[0] > 0 and new_size[1] > 0:
            self.current_image = pygame.transform.scale(self.original_image, new_size)

            # 페이드 효과
            alpha = 255
            if self.fade_in and progress < 0.2:
                alpha = int(255 * (progress / 0.2))
            if self.fade_out and progress > 0.8:
                alpha = int(255 * ((1 - progress) / 0.2))

            if alpha < 255:
                self.current_image.set_alpha(alpha)

    def _ease_in_out(self, t: float) -> float:
        """Ease-in-out 곡선"""
        if t < 0.5:
            return 2 * t * t
        else:
            return 1 - 2 * (1 - t) * (1 - t)

    def draw(self, screen: pygame.Surface):
        """그리기"""
        if not self.is_alive or self.current_image is None:
            return

        rect = self.current_image.get_rect(center=(int(self.current_pos.x), int(self.current_pos.y)))
        screen.blit(self.current_image, rect)


# 테스트 코드
if __name__ == "__main__":
    import sys

    pygame.init()
    screen = pygame.display.set_mode((1200, 800))
    pygame.display.set_caption("Physics Effects Test")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 24)

    # 효과 리스트
    supply_drops: List[SupplyDrop] = []

    print("=== Physics Effects Test ===")
    print("Controls:")
    print("  Click - Drop supply at mouse position")
    print("  Space - Drop supply at random position")
    print("  C - Clear all supplies")

    running = True
    while running:
        dt = clock.tick(60) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.MOUSEBUTTONDOWN:
                # 마우스 클릭 위치에 보급품 투하
                drop = SupplyDrop(
                    start_pos=(event.pos[0], 50),
                    target_pos=(event.pos[0], 700),
                    image_path="bullet_storage.png",
                    ground_y=700
                )
                supply_drops.append(drop)
                print(f"Supply dropped at x={event.pos[0]}")

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    # 랜덤 위치에 보급품 투하
                    import random
                    x = random.randint(100, 1100)
                    drop = SupplyDrop(
                        start_pos=(x, 50),
                        target_pos=(x + random.randint(-100, 100), 700),
                        ground_y=700
                    )
                    supply_drops.append(drop)

                elif event.key == pygame.K_c:
                    supply_drops.clear()
                    print("All supplies cleared")

        # 배경
        screen.fill((30, 30, 40))

        # 지면 표시
        pygame.draw.line(screen, (100, 100, 100), (0, 700), (1200, 700), 2)

        # 보급품 업데이트 및 그리기
        for drop in supply_drops[:]:
            drop.update(dt)
            if not drop.is_alive:
                supply_drops.remove(drop)
            else:
                drop.draw(screen)

        # UI
        info_text = font.render(f"Supplies: {len(supply_drops)} | Click to drop | Space=Random | C=Clear", True, (255, 255, 255))
        screen.blit(info_text, (10, 10))

        pygame.display.flip()

    pygame.quit()
    print("Test completed")


# ========================================
# 워프홀 효과 시스템
# ========================================

class WarpParticle:
    """
    워프홀 파티클 - 빛나는 입자

    특징:
    - 이미지 기반 렌더링
    - 소용돌이 궤적 (나선형)
    - 크기 맥동 (pulsate)
    - Additive blending으로 빛남
    - 트레일 효과
    """

    def __init__(
        self,
        center: Tuple[float, float],
        initial_distance: float,
        initial_angle: float,
        image: pygame.Surface,
        color_tint: Tuple[int, int, int] = (255, 255, 255),
        spiral_speed: float = 2.0,  # 회전 속도 (라디안/초)
        pull_speed: float = 100.0,  # 빨려들어가는 속도
        size_range: Tuple[float, float] = (0.3, 1.0),
        pulsate_speed: float = 3.0,
        lifetime: float = 3.0
    ):
        self.center = pygame.math.Vector2(center)
        self.distance = initial_distance  # 중심으로부터의 거리
        self.angle = initial_angle  # 각도 (라디안)
        self.original_image = image
        self.color_tint = color_tint
        self.spiral_speed = spiral_speed
        self.pull_speed = pull_speed
        self.size_range = size_range
        self.pulsate_speed = pulsate_speed
        self.lifetime = lifetime

        self.age = 0.0
        self.is_alive = True

        # 트레일
        self.trail_positions = []
        self.max_trail_length = 8

        # 현재 위치 계산
        self._update_position()

    def _update_position(self):
        """각도와 거리로부터 실제 위치 계산"""
        self.pos = pygame.math.Vector2(
            self.center.x + self.distance * math.cos(self.angle),
            self.center.y + self.distance * math.sin(self.angle)
        )

    def update(self, dt: float):
        """업데이트"""
        if not self.is_alive:
            return

        self.age += dt

        # 수명 체크
        if self.age > self.lifetime:
            self.is_alive = False
            return

        # 소용돌이 회전
        self.angle += self.spiral_speed * dt

        # 중심으로 빨려들어감
        self.distance -= self.pull_speed * dt

        # 중심 도달 시 사라짐
        if self.distance <= 10:
            self.is_alive = False
            return

        # 위치 업데이트
        self._update_position()

        # 트레일 추가
        self.trail_positions.append(self.pos.copy())
        if len(self.trail_positions) > self.max_trail_length:
            self.trail_positions.pop(0)

    def draw(self, screen: pygame.Surface):
        """그리기"""
        if not self.is_alive:
            return

        # 트레일 그리기 (뒤에서 앞으로)
        for i, trail_pos in enumerate(self.trail_positions):
            trail_alpha = int(150 * (i / len(self.trail_positions)))
            trail_size = int(3 * (i / len(self.trail_positions)))

            if trail_size > 0:
                trail_surf = pygame.Surface((trail_size * 2, trail_size * 2), pygame.SRCALPHA)
                pygame.draw.circle(
                    trail_surf,
                    (*self.color_tint, trail_alpha),
                    (trail_size, trail_size),
                    trail_size
                )
                screen.blit(trail_surf, (int(trail_pos.x - trail_size), int(trail_pos.y - trail_size)), special_flags=pygame.BLEND_ADD)

        # 크기 맥동 (sin 파형)
        pulsate_factor = 0.8 + 0.2 * math.sin(self.age * self.pulsate_speed * math.pi * 2)

        # 수명에 따른 크기 (처음과 끝에 작게)
        life_factor = min(self.age / 0.3, 1.0) * min((self.lifetime - self.age) / 0.5, 1.0)

        # 거리에 따른 크기 (가까울수록 작게 - 원근감)
        distance_factor = self.distance / 300.0

        # 최종 크기
        size_factor = pulsate_factor * life_factor * distance_factor
        size_factor = max(self.size_range[0], min(self.size_range[1], size_factor))

        # 이미지 스케일
        new_size = (
            max(1, int(self.original_image.get_width() * size_factor)),
            max(1, int(self.original_image.get_height() * size_factor))
        )

        if new_size[0] > 0 and new_size[1] > 0:
            # 이미지 스케일
            scaled_image = pygame.transform.scale(self.original_image, new_size)

            # 색상 틴트 적용
            if self.color_tint != (255, 255, 255):
                tinted = scaled_image.copy()
                tint_overlay = pygame.Surface(new_size, pygame.SRCALPHA)
                tint_overlay.fill((*self.color_tint, 128))
                tinted.blit(tint_overlay, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                scaled_image = tinted

            # Additive blending으로 그리기 (빛나는 효과)
            rect = scaled_image.get_rect(center=(int(self.pos.x), int(self.pos.y)))
            screen.blit(scaled_image, rect, special_flags=pygame.BLEND_ADD)


class WarpPortal:
    """
    완전한 워프 포탈 효과

    구성:
    - 회전하는 링 (여러 겹)
    - 소용돌이 파티클들
    - 중심 블랙홀 효과
    - 빛나는 가장자리
    """

    def __init__(
        self,
        center: Tuple[float, float],
        max_radius: float = 200.0,
        particle_count: int = 50,
        ring_count: int = 3,
        duration: float = 5.0,
        color_scheme: str = "blue"  # "blue", "red", "green", "yellow"
    ):
        """
        Args:
            center: 포탈 중심 위치
            max_radius: 최대 반지름
            particle_count: 파티클 개수
            ring_count: 링 개수
            duration: 지속 시간 (0=무한)
            color_scheme: 색상 테마
        """
        self.center = pygame.math.Vector2(center)
        self.max_radius = max_radius
        self.particle_count = particle_count
        self.ring_count = ring_count
        self.duration = duration

        # 색상 테마
        color_schemes = {
            "blue": [(100, 150, 255), (150, 200, 255), (200, 220, 255)],
            "red": [(255, 100, 100), (255, 150, 150), (255, 200, 200)],
            "green": [(100, 255, 150), (150, 255, 200), (200, 255, 220)],
            "yellow": [(255, 255, 100), (255, 255, 150), (255, 255, 200)]
        }
        self.colors = color_schemes.get(color_scheme, color_schemes["blue"])

        # 파티클 이미지 로드
        self.particle_images = self._load_particle_images()

        # 링 이미지 로드
        self.ring_image = self._load_ring_image()

        # 파티클 생성
        self.particles: List[WarpParticle] = []
        self._spawn_particles()

        # 링 회전 각도
        self.ring_rotations = [0.0] * ring_count
        self.ring_speeds = [random.uniform(30, 90) for _ in range(ring_count)]  # 도/초

        # 상태
        self.age = 0.0
        self.is_alive = True
        self.spawn_timer = 0.0
        self.spawn_interval = 0.1  # 파티클 재생성 간격

    def _load_particle_images(self) -> List[pygame.Surface]:
        """파티클 이미지 로드"""
        images = []
        particle_files = [
            "effects/in/shining_light_star.png",
            "effects/in/explosive_star_effect.png",
            "effects/in/blue_hole_star.png",
            "effects/in/star_warp_element.png",
            "effects/in/light_warp_element.png"
        ]

        for file_path in particle_files:
            try:
                path = Path(file_path)
                if path.exists():
                    img = pygame.image.load(str(path)).convert_alpha()
                    # 크기 조정
                    img = pygame.transform.scale(img, (32, 32))
                    images.append(img)
            except Exception as e:
                print(f"WARNING: Failed to load particle image {file_path}: {e}")

        # 폴백: 기본 원
        if not images:
            fallback = pygame.Surface((32, 32), pygame.SRCALPHA)
            pygame.draw.circle(fallback, (255, 255, 255, 200), (16, 16), 15)
            pygame.draw.circle(fallback, (255, 255, 255, 100), (16, 16), 10)
            images.append(fallback)

        return images

    def _load_ring_image(self) -> Optional[pygame.Surface]:
        """링 이미지 로드"""
        ring_files = [
            "effects/in/blue_whirl_ring.png",
            "effects/in/yellow_ring_star.png"
        ]

        for file_path in ring_files:
            try:
                path = Path(file_path)
                if path.exists():
                    img = pygame.image.load(str(path)).convert_alpha()
                    return img
            except Exception as e:
                print(f"WARNING: Failed to load ring image {file_path}: {e}")

        return None

    def _spawn_particles(self):
        """파티클 생성"""
        for _ in range(self.particle_count):
            # 랜덤 초기 위치 (외곽에서 시작)
            distance = random.uniform(self.max_radius * 0.7, self.max_radius * 1.2)
            angle = random.uniform(0, math.pi * 2)

            # 랜덤 이미지
            image = random.choice(self.particle_images)

            # 랜덤 색상
            color = random.choice(self.colors)

            particle = WarpParticle(
                center=tuple(self.center),
                initial_distance=distance,
                initial_angle=angle,
                image=image,
                color_tint=color,
                spiral_speed=random.uniform(1.5, 3.0),
                pull_speed=random.uniform(80, 120),
                size_range=(0.2, 0.8),
                pulsate_speed=random.uniform(2.0, 4.0),
                lifetime=random.uniform(2.5, 4.0)
            )

            self.particles.append(particle)

    def update(self, dt: float):
        """업데이트"""
        if not self.is_alive:
            return

        self.age += dt

        # 수명 체크
        if self.duration > 0 and self.age > self.duration:
            self.is_alive = False
            return

        # 파티클 업데이트
        for particle in self.particles[:]:
            particle.update(dt)
            if not particle.is_alive:
                self.particles.remove(particle)

        # 파티클 재생성
        self.spawn_timer += dt
        if self.spawn_timer >= self.spawn_interval:
            self.spawn_timer = 0.0

            # 사라진 파티클 수만큼 재생성
            missing_count = self.particle_count - len(self.particles)
            for _ in range(min(missing_count, 3)):  # 한 번에 최대 3개
                distance = random.uniform(self.max_radius * 0.7, self.max_radius * 1.2)
                angle = random.uniform(0, math.pi * 2)
                image = random.choice(self.particle_images)
                color = random.choice(self.colors)

                particle = WarpParticle(
                    center=tuple(self.center),
                    initial_distance=distance,
                    initial_angle=angle,
                    image=image,
                    color_tint=color,
                    spiral_speed=random.uniform(1.5, 3.0),
                    pull_speed=random.uniform(80, 120),
                    size_range=(0.2, 0.8),
                    pulsate_speed=random.uniform(2.0, 4.0),
                    lifetime=random.uniform(2.5, 4.0)
                )

                self.particles.append(particle)

        # 링 회전
        for i in range(len(self.ring_rotations)):
            self.ring_rotations[i] += self.ring_speeds[i] * dt
            self.ring_rotations[i] %= 360

    def draw(self, screen: pygame.Surface):
        """그리기"""
        if not self.is_alive:
            return

        # 1. 배경 글로우 (가장 뒤)
        glow_radius = int(self.max_radius * 1.5)
        glow_surf = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)

        for i in range(3):
            radius = glow_radius - i * 30
            alpha = 20 - i * 5
            pygame.draw.circle(
                glow_surf,
                (*self.colors[0], alpha),
                (glow_radius, glow_radius),
                radius
            )

        glow_rect = glow_surf.get_rect(center=(int(self.center.x), int(self.center.y)))
        screen.blit(glow_surf, glow_rect, special_flags=pygame.BLEND_ADD)

        # 2. 회전하는 링들
        if self.ring_image:
            for i in range(self.ring_count):
                ring_size = int(self.max_radius * 2 * (0.6 + i * 0.2))
                scaled_ring = pygame.transform.scale(self.ring_image, (ring_size, ring_size))

                # 회전
                rotated_ring = pygame.transform.rotate(scaled_ring, self.ring_rotations[i])

                # 투명도 (겹쳐진 느낌)
                rotated_ring.set_alpha(100 + i * 30)

                ring_rect = rotated_ring.get_rect(center=(int(self.center.x), int(self.center.y)))
                screen.blit(rotated_ring, ring_rect)

        # 3. 파티클들 (거리순 정렬 - 멀리 있는 것부터)
        sorted_particles = sorted(self.particles, key=lambda p: p.distance, reverse=True)
        for particle in sorted_particles:
            particle.draw(screen)

        # 4. 중심 블랙홀 효과
        center_radius = int(self.max_radius * 0.15)
        center_surf = pygame.Surface((center_radius * 4, center_radius * 4), pygame.SRCALPHA)

        # 여러 겹의 원으로 블랙홀 표현
        for i in range(5):
            radius = center_radius - i * (center_radius // 6)
            if radius > 0:
                alpha = 255 - i * 40
                pygame.draw.circle(
                    center_surf,
                    (0, 0, 0, alpha),
                    (center_radius * 2, center_radius * 2),
                    radius
                )

        # 가장자리 빛
        pygame.draw.circle(
            center_surf,
            (*self.colors[2], 150),
            (center_radius * 2, center_radius * 2),
            center_radius,
            3
        )

        center_rect = center_surf.get_rect(center=(int(self.center.x), int(self.center.y)))
        screen.blit(center_surf, center_rect)

    def pull_object(self, obj_pos: Tuple[float, float], dt: float, pull_strength: float = 200.0) -> Tuple[float, float]:
        """
        물체를 포탈로 끌어당김

        Args:
            obj_pos: 물체 위치
            dt: 델타 타임
            pull_strength: 끌어당기는 힘

        Returns:
            새로운 위치 (x, y)
        """
        obj_vec = pygame.math.Vector2(obj_pos)
        direction = self.center - obj_vec
        distance = direction.length()

        if distance > 0:
            # 거리에 반비례하는 힘
            force = pull_strength / max(distance, 50)
            velocity = direction.normalize() * force * dt

            new_pos = obj_vec + velocity
            return (new_pos.x, new_pos.y)

        return obj_pos
