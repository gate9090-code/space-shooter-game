# entities/support_units.py
# 지원 유닛 클래스 (터렛, 드론)

import pygame
import math
from typing import Tuple, List
from pathlib import Path
import config
from entities.weapons import Bullet


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
                self.image = pygame.transform.scale(
                    original_image, (target_size, target_size)
                )
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
            closest_distance = float("inf")

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
            image_rect = rotated_image.get_rect(
                center=(int(self.pos.x), int(self.pos.y))
            )
            screen.blit(rotated_image, image_rect)
        else:
            # 기본 도형 (이미지 없을 때)
            base_color = (100, 100, 255)
            pygame.draw.circle(
                screen, base_color, (int(self.pos.x), int(self.pos.y)), self.size
            )

            # 포신 (회전하는 선)
            barrel_length = self.size + 10
            barrel_end_x = self.pos.x + math.cos(self.rotation_angle) * barrel_length
            barrel_end_y = self.pos.y + math.sin(self.rotation_angle) * barrel_length
            pygame.draw.line(
                screen,
                (200, 200, 255),
                (int(self.pos.x), int(self.pos.y)),
                (int(barrel_end_x), int(barrel_end_y)),
                4,
            )

        # 사거리 표시 (반투명 원)
        range_surf = pygame.Surface(
            (self.shoot_range * 2, self.shoot_range * 2), pygame.SRCALPHA
        )
        pygame.draw.circle(
            range_surf,
            (100, 100, 255, 30),
            (self.shoot_range, self.shoot_range),
            self.shoot_range,
            1,
        )
        screen.blit(
            range_surf,
            (int(self.pos.x - self.shoot_range), int(self.pos.y - self.shoot_range)),
        )

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
            # 드론 크기를 50% 더 크게 스케일링 (기존 * 2 -> * 3)
            self.image = pygame.transform.scale(
                self.image, (int(self.size * 3), int(self.size * 3))
            )
        else:
            self.image = None

        # 위치 초기화 (원형 궤도)
        import math

        self.pos = pygame.math.Vector2(
            player.pos.x + math.cos(orbit_angle) * self.orbit_radius,
            player.pos.y + math.sin(orbit_angle) * self.orbit_radius,
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
            closest_distance = float("inf")

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
            pygame.draw.circle(
                screen, (255, 255, 200), (int(self.pos.x), int(self.pos.y)), 4
            )

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
                glow_surf = pygame.Surface(
                    (glow_size + 10, glow_size + 10), pygame.SRCALPHA
                )
                glow_rect = pygame.Rect(5, 5, glow_size, glow_size)
                pygame.draw.ellipse(
                    glow_surf, (*glow_color, glow_alpha), glow_rect, max(1, 4 - i)
                )
                screen.blit(
                    glow_surf,
                    (center_x - glow_size // 2 - 5, center_y - glow_size // 2 - 5),
                )

        # 메인 원형 궤도 (점선 효과로 에너지 흐름 표현)
        num_segments = 36  # 원을 구성하는 세그먼트 수
        trail_color_base = (255, 200, 100)
        trail_color_bright = (255, 255, 180)

        points = []
        for i in range(num_segments + 1):
            angle = 2 * math.pi * i / num_segments
            x = center_x + math.cos(angle) * self.orbit_radius
            y = center_y + math.sin(angle) * self.orbit_radius
            points.append((x, y))

        # 회전하는 밝은 구간 효과 (드론 위치 기준)
        drone_segment = (
            int((self.orbit_angle / (2 * math.pi)) * num_segments) % num_segments
        )

        for i in range(num_segments):
            # 드론 위치로부터의 거리에 따른 밝기 계산
            segment_dist = min(
                abs(i - drone_segment), num_segments - abs(i - drone_segment)
            )
            brightness = max(0, 1.0 - segment_dist / (num_segments / 3))

            # 색상 보간
            r = int(
                trail_color_base[0]
                + (trail_color_bright[0] - trail_color_base[0]) * brightness
            )
            g = int(
                trail_color_base[1]
                + (trail_color_bright[1] - trail_color_base[1]) * brightness
            )
            b = int(
                trail_color_base[2]
                + (trail_color_bright[2] - trail_color_base[2]) * brightness
            )

            # 선 굵기 (드론 근처가 더 두꺼움)
            line_width = 1 + int(brightness * 2)

            # 알파값 (드론에서 멀어질수록 투명)
            alpha = int(100 + 155 * brightness * glow_intensity)

            # 세그먼트 그리기
            if i < len(points) - 1:
                start_pos = (int(points[i][0]), int(points[i][1]))
                end_pos = (int(points[i + 1][0]), int(points[i + 1][1]))

                # 투명한 선 그리기
                line_surf = pygame.Surface(
                    (
                        abs(end_pos[0] - start_pos[0]) + 10,
                        abs(end_pos[1] - start_pos[1]) + 10,
                    ),
                    pygame.SRCALPHA,
                )
                local_start = (5, 5)
                local_end = (
                    end_pos[0] - start_pos[0] + 5,
                    end_pos[1] - start_pos[1] + 5,
                )

                pygame.draw.line(
                    line_surf, (r, g, b, alpha), local_start, local_end, line_width
                )
                screen.blit(
                    line_surf,
                    (
                        min(start_pos[0], end_pos[0]) - 5,
                        min(start_pos[1], end_pos[1]) - 5,
                    ),
                )

        # 드론 현재 위치에 밝은 마커 (에너지 노드)
        marker_size = 4 + int(glow_intensity * 2)
        pygame.draw.circle(
            screen, trail_color_bright, (int(self.pos.x), int(self.pos.y)), marker_size
        )
        pygame.draw.circle(
            screen, (255, 255, 255), (int(self.pos.x), int(self.pos.y)), marker_size - 2
        )
