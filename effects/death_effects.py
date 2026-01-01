'''
Death Effects - Enemy death animations and effects
적 사망 효과 - 파편, 소용돌이, 픽셀화 등

Extracted from objects.py
'''
import pygame
import math
import random
from typing import Tuple, List

# Import shared effect classes from screen_effects
from .screen_effects import BurstParticle, DissolveEffect, FadeEffect, ImplodeEffect


# ============================================================
# Shatter Fragment
# ============================================================

class ShatterFragment:
    """적 사망 시 생성되는 이미지 파편"""

    def __init__(
        self,
        image_piece: pygame.Surface,
        pos: pygame.math.Vector2,
        velocity: pygame.math.Vector2,
        rotation_speed: float,
    ):
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


# ============================================================
# Vortex Effect
# ============================================================

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
        particle_count = 20
        for i in range(particle_count):
            angle = (i / particle_count) * math.pi * 4  # 2바퀴 나선
            distance = random.uniform(30, 80)
            speed = random.uniform(80, 150)
            color = random.choice(
                [
                    (100, 150, 255),  # 파란색
                    (150, 100, 255),  # 보라색
                    (200, 150, 255),  # 연보라색
                ]
            )
            self.spiral_particles.append(
                {
                    "angle": angle,
                    "distance": distance,
                    "speed": speed,
                    "color": color,
                    "size": random.uniform(2, 5),
                    "alpha": 255,
                }
            )

    def update(self, dt: float):
        if not self.is_alive:
            return

        self.lifetime += dt

        # 확대 중에는 회전 느리게, 축소 시작 후 가속 회전
        if self.lifetime < self.expand_duration:
            self.rotation += 180 * dt  # 느린 회전
        else:
            # 점점 빨라지는 회전 (가속)
            shrink_progress = (self.lifetime - self.expand_duration) / (
                self.max_lifetime - self.expand_duration
            )
            acceleration = 1.0 + shrink_progress * 3
            self.rotation += 720 * dt * acceleration

        # 파티클 업데이트 (중심으로 수렴)
        for p in self.spiral_particles:
            p["angle"] += dt * 5  # 나선 회전
            p["distance"] = max(0, p["distance"] - p["speed"] * dt)
            p["alpha"] = max(0, p["alpha"] - 200 * dt)

        if self.lifetime >= self.max_lifetime:
            self.is_alive = False

    def draw(self, screen: pygame.Surface):
        if not self.is_alive:
            return

        progress = min(self.lifetime / self.max_lifetime, 1.0)

        # 나선 파티클 그리기 (뒤에)
        for p in self.spiral_particles:
            if p["alpha"] > 0 and p["distance"] > 0:
                px = self.pos.x + math.cos(p["angle"]) * p["distance"]
                py = self.pos.y + math.sin(p["angle"]) * p["distance"]
                color_with_alpha = (*p["color"], int(p["alpha"]))
                surf = pygame.Surface(
                    (int(p["size"] * 2), int(p["size"] * 2)), pygame.SRCALPHA
                )
                pygame.draw.circle(
                    surf,
                    color_with_alpha,
                    (int(p["size"]), int(p["size"])),
                    int(p["size"]),
                )
                screen.blit(surf, (int(px - p["size"]), int(py - p["size"])))

        # 확대→축소 애니메이션
        if self.lifetime < self.expand_duration:
            # Phase 1: 확대
            expand_progress = self.lifetime / self.expand_duration
            scale = 1.0 + (self.expand_scale - 1.0) * (
                1.0 - (1.0 - expand_progress) ** 2
            )
        else:
            # Phase 2: 급격한 축소 (빨려들어감)
            shrink_progress = (self.lifetime - self.expand_duration) / (
                self.max_lifetime - self.expand_duration
            )
            scale = self.expand_scale * (1.0 - shrink_progress) ** 1.5

        new_width = max(1, int(self.original_size[0] * scale))
        new_height = max(1, int(self.original_size[1] * scale))

        # 이미지 스케일링 및 회전
        scaled_image = pygame.transform.scale(
            self.original_image, (new_width, new_height)
        )
        rotated_image = pygame.transform.rotate(scaled_image, self.rotation)

        # 투명도 + 색조 변화 (파란색으로)
        if self.lifetime < self.expand_duration:
            alpha = 255
        else:
            shrink_progress = (self.lifetime - self.expand_duration) / (
                self.max_lifetime - self.expand_duration
            )
            alpha = int(255 * (1.0 - shrink_progress**2))
        rotated_image.set_alpha(alpha)

        # 파란색 오버레이 (차원 균열 느낌) - 축소 시작 후에만
        if self.lifetime >= self.expand_duration:
            shrink_progress = (self.lifetime - self.expand_duration) / (
                self.max_lifetime - self.expand_duration
            )
            if shrink_progress > 0.2:
                tint_surf = pygame.Surface(rotated_image.get_size(), pygame.SRCALPHA)
                tint_alpha = int(100 * (shrink_progress - 0.2) / 0.8)
                tint_surf.fill((100, 150, 255, tint_alpha))
                rotated_image.blit(
                    tint_surf, (0, 0), special_flags=pygame.BLEND_RGBA_ADD
                )

        # 그리기
        rect = rotated_image.get_rect(center=(int(self.pos.x), int(self.pos.y)))
        screen.blit(rotated_image, rect)

        # 마지막 플래시 효과
        if progress > 0.85:
            flash_alpha = int(200 * (progress - 0.85) / 0.15)
            flash_size = int(30 * (1.0 - (progress - 0.85) / 0.15))
            if flash_size > 0:
                flash_surf = pygame.Surface(
                    (flash_size * 2, flash_size * 2), pygame.SRCALPHA
                )
                pygame.draw.circle(
                    flash_surf,
                    (200, 220, 255, flash_alpha),
                    (flash_size, flash_size),
                    flash_size,
                )
                screen.blit(
                    flash_surf,
                    (int(self.pos.x - flash_size), int(self.pos.y - flash_size)),
                )


# ============================================================
# Pixelate Effect
# ============================================================

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
        self.phase = "pixelate"  # 'pixelate' -> 'scatter'
        self.scatter_started = False

        # 타이밍 설정 (2배 연장)
        self.pixelate_duration = 0.8  # 픽셀화 단계 시간
        self.scatter_duration = 1.2  # 분해 단계 시간

    def _create_pixel_blocks(self, block_size: int = 8):
        """픽셀 블록 생성 (분해용)"""
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
                    self.pos.x + offset_x, self.pos.y + offset_y
                )

                # 랜덤 속도 (아래로 떨어짐 + 좌우 흩어짐)
                angle = (
                    random.uniform(-math.pi / 3, math.pi / 3) - math.pi / 2
                )  # 위쪽 반원
                speed = random.uniform(50, 150)
                velocity = pygame.math.Vector2(
                    math.cos(angle) * speed * 0.5,
                    random.uniform(30, 100),  # 아래로 떨어짐
                )

                self.pixel_blocks.append(
                    {
                        "image": block_surf,
                        "pos": block_pos,
                        "velocity": velocity,
                        "alpha": 255,
                        "blink_timer": random.uniform(0, 0.5),  # 깜빡임 타이머
                        "gravity": random.uniform(150, 250),
                    }
                )

    def update(self, dt: float):
        if not self.is_alive:
            return

        self.lifetime += dt

        # 페이즈 전환 (pixelate_duration 후 분해 시작)
        if self.phase == "pixelate" and self.lifetime >= self.pixelate_duration:
            self.phase = "scatter"
            if not self.scatter_started:
                self._create_pixel_blocks(block_size=8)
                self.scatter_started = True

        # 분해 페이즈: 블록 업데이트
        if self.phase == "scatter":
            for block in self.pixel_blocks:
                # 중력 적용
                block["velocity"].y += block["gravity"] * dt
                block["pos"] += block["velocity"] * dt

                # 깜빡임
                block["blink_timer"] -= dt
                if block["blink_timer"] <= 0:
                    block["blink_timer"] = random.uniform(0.05, 0.15)

                # 페이드아웃
                scatter_progress = (
                    self.lifetime - self.pixelate_duration
                ) / self.scatter_duration
                block["alpha"] = max(0, int(255 * (1.0 - scatter_progress)))

        if self.lifetime >= self.max_lifetime:
            self.is_alive = False

    def draw(self, screen: pygame.Surface):
        if not self.is_alive:
            return

        progress = min(self.lifetime / self.max_lifetime, 1.0)

        if self.phase == "pixelate":
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
                    pixelated.blit(
                        glitch_surf, (0, 0), special_flags=pygame.BLEND_RGB_ADD
                    )

            # 그리기
            rect = pixelated.get_rect(center=(int(self.pos.x), int(self.pos.y)))
            screen.blit(pixelated, rect)

        else:
            # 분해 단계: 블록들이 흩어짐
            for block in self.pixel_blocks:
                if block["alpha"] <= 0:
                    continue

                # 깜빡임 효과
                if block["blink_timer"] < 0.03:
                    continue  # 깜빡임 중 안 보임

                block_img = block["image"].copy()
                block_img.set_alpha(block["alpha"])

                rect = block_img.get_rect(
                    center=(int(block["pos"].x), int(block["pos"].y))
                )
                screen.blit(block_img, rect)


# ============================================================
# Death Effect Manager
# ============================================================

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
            "pixelate": True,
        }

        # 적 유형별 죽음 효과 매핑
        self.enemy_type_effects = {
            "NORMAL": "shatter",  # 일반: 파편화
            "TANK": "implode",  # 탱크: 내파 (무거운 느낌)
            "RUNNER": "fade",  # 러너: 빠른 페이드 (빠른 적)
            "SUMMONER": "vortex",  # 소환사: 소용돌이 (마법적 느낌)
            "SHIELDED": "dissolve",  # 보호막: 디졸브 (보호막 소멸)
            "KAMIKAZE": "particle_burst",  # 카미카제: 폭발 파티클
            "RESPAWNED": "pixelate",  # 리스폰: 픽셀화 (디지털 글리치)
        }

    def create_shatter_effect(
        self,
        enemy_image: pygame.Surface,
        enemy_pos: pygame.math.Vector2,
        grid_size: int = 4,
    ):
        """이미지 파편화 효과 생성

        Args:
            enemy_image: 적 이미지
            enemy_pos: 적 위치
            grid_size: 파편 그리드 크기 (4x4 = 16조각)
        """
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
                piece_rect = pygame.Rect(
                    col * piece_width, row * piece_height, piece_width, piece_height
                )
                piece = enemy_image.subsurface(piece_rect).copy()

                # 파편 시작 위치 (적 중심 기준)
                offset_x = (col - grid_size / 2 + 0.5) * piece_width
                offset_y = (row - grid_size / 2 + 0.5) * piece_height
                frag_pos = pygame.math.Vector2(
                    enemy_pos.x + offset_x, enemy_pos.y + offset_y
                )

                # 폭발 방향 (중심에서 바깥으로)
                angle = math.atan2(offset_y, offset_x)
                speed = random.uniform(150, 300)  # 속도 무작위
                velocity = pygame.math.Vector2(
                    math.cos(angle) * speed,
                    math.sin(angle) * speed
                    - random.uniform(50, 150),  # 위쪽으로 약간 튀어오름
                )

                # 회전 속도 무작위
                rotation_speed = random.uniform(-360, 360)

                # 파편 생성
                fragment = ShatterFragment(piece, frag_pos, velocity, rotation_speed)
                self.fragments.append(fragment)

    def create_particle_burst(
        self, pos: pygame.math.Vector2, color: tuple, count: int = 30
    ):
        """파티클 폭발 효과 생성

        Args:
            pos: 폭발 위치
            color: 파티클 색상
            count: 파티클 개수
        """
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(100, 250)
            velocity = pygame.math.Vector2(
                math.cos(angle) * speed,
                math.sin(angle) * speed - random.uniform(0, 100),
            )
            size = random.uniform(2, 5)

            particle = BurstParticle(pos.copy(), velocity, color, size)
            self.particles.append(particle)

    def create_dissolve_effect(
        self, enemy_image: pygame.Surface, enemy_pos: pygame.math.Vector2
    ):
        """디졸브 효과 생성"""
        effect = DissolveEffect(enemy_image, enemy_pos)
        self.dissolve_effects.append(effect)

    def create_fade_effect(
        self, enemy_image: pygame.Surface, enemy_pos: pygame.math.Vector2
    ):
        """페이드 효과 생성"""
        effect = FadeEffect(enemy_image, enemy_pos)
        self.fade_effects.append(effect)

    def create_implode_effect(
        self, enemy_image: pygame.Surface, enemy_pos: pygame.math.Vector2
    ):
        """내파 효과 생성"""
        effect = ImplodeEffect(enemy_image, enemy_pos)
        self.implode_effects.append(effect)

    def create_vortex_effect(
        self, enemy_image: pygame.Surface, enemy_pos: pygame.math.Vector2
    ):
        """소용돌이 효과 생성"""
        effect = VortexEffect(enemy_image, enemy_pos)
        self.vortex_effects.append(effect)

    def create_pixelate_effect(
        self, enemy_image: pygame.Surface, enemy_pos: pygame.math.Vector2
    ):
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
        if hasattr(enemy, "image") and enemy.image:
            enemy_image = enemy.image
        else:
            # 임시 이미지 생성 (적 크기에 맞춤)
            enemy_image = pygame.Surface(
                (int(enemy.size * 2), int(enemy.size * 2)), pygame.SRCALPHA
            )
            pygame.draw.circle(
                enemy_image,
                enemy.color,
                (int(enemy.size), int(enemy.size)),
                int(enemy.size),
            )

        # 사망 효과용 확대 이미지 생성 (1.3배 확대로 폭발감 연출)
        death_scale = 1.3
        if hasattr(enemy, "is_boss") and enemy.is_boss:
            death_scale = 1.5  # 보스는 더 크게 확대

        scaled_width = int(enemy_image.get_width() * death_scale)
        scaled_height = int(enemy_image.get_height() * death_scale)
        scaled_image = pygame.transform.smoothscale(
            enemy_image, (scaled_width, scaled_height)
        )

        # 적 유형에 따라 효과 선택
        enemy_type = getattr(enemy, "enemy_type", "NORMAL")
        effect_name = self.enemy_type_effects.get(enemy_type, self.current_effect)

        # 보스는 항상 shatter (큰 파편 효과)
        if hasattr(enemy, "is_boss") and enemy.is_boss:
            effect_name = "shatter"

        # 선택된 효과 발동 (확대된 이미지 사용)
        self._apply_effect(
            effect_name,
            scaled_image,
            enemy.pos,
            getattr(enemy, "color", (255, 100, 100)),
        )

    def _apply_effect(
        self,
        effect_name: str,
        enemy_image: pygame.Surface,
        enemy_pos: pygame.math.Vector2,
        enemy_color: tuple,
    ):
        """실제 효과 적용"""
        if effect_name == "shatter" and self.enabled_effects.get("shatter", True):
            self.create_shatter_effect(enemy_image, enemy_pos)

        elif effect_name == "particle_burst" and self.enabled_effects.get(
            "particle_burst", True
        ):
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
