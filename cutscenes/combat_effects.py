"""
cutscenes/combat_effects.py
Combat-related cutscene effects (cannon, bunker, combat motion)
"""

import pygame
import math
import random
from typing import Tuple, List, Optional
from pathlib import Path
from cutscenes.base import BaseCutsceneEffect, render_dialogue_box


class CannonShell:
    """포신에서 발사되는 포탄"""

    def __init__(
        self,
        start_pos: Tuple[float, float],
        target_pos: Tuple[float, float],
        screen_size: Tuple[int, int],
    ):
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
        if (
            self.pos.x < -margin
            or self.pos.x > self.screen_size[0] + margin
            or self.pos.y < -margin
            or self.pos.y > self.screen_size[1] + margin
        ):
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

            trail_surf = pygame.Surface(
                (trail_size * 2, trail_size * 2), pygame.SRCALPHA
            )
            pygame.draw.circle(
                trail_surf, (r, g, b, alpha), (trail_size, trail_size), trail_size
            )
            screen.blit(
                trail_surf,
                (int(trail_pos.x - trail_size), int(trail_pos.y - trail_size)),
            )

        if not self.is_alive:
            return

        # 글로우 효과
        glow_surf = pygame.Surface(
            (self.glow_size * 2, self.glow_size * 2), pygame.SRCALPHA
        )
        pygame.draw.circle(
            glow_surf,
            (255, 200, 100, 100),
            (self.glow_size, self.glow_size),
            self.glow_size,
        )
        screen.blit(
            glow_surf,
            (int(self.pos.x - self.glow_size), int(self.pos.y - self.glow_size)),
        )

        # 포탄 본체
        pygame.draw.circle(
            screen, (255, 220, 150), (int(self.pos.x), int(self.pos.y)), self.size
        )
        pygame.draw.circle(
            screen, (255, 255, 200), (int(self.pos.x), int(self.pos.y)), self.size // 2
        )


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

    def __init__(
        self, screen_size: Tuple[int, int], position: Tuple[float, float] = None
    ):
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
                screen_size[0] * 0.85, screen_size[1] * 0.75
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

    def _select_target(
        self, player_pos: Optional[Tuple[float, float]], enemies: List = None
    ) -> pygame.math.Vector2:
        """발사 대상 선택 - 가장 가까운 적 우선"""
        # 가장 가까운 적 찾기
        if enemies:
            closest_enemy = None
            closest_dist = float("inf")
            for enemy in enemies:
                if hasattr(enemy, "is_alive") and enemy.is_alive:
                    dist = (
                        (enemy.pos.x - self.base_pos.x) ** 2
                        + (enemy.pos.y - self.base_pos.y) ** 2
                    ) ** 0.5
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
            random.uniform(self.screen_size[1] * 0.1, self.screen_size[1] * 0.4),
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
            self.base_pos.y + math.sin(self.current_angle) * effective_length,
        )

    def update(
        self,
        dt: float,
        player_pos: Optional[Tuple[float, float]] = None,
        enemies: List = None,
    ):
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
            screen_size=self.screen_size,
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
        pygame.draw.circle(
            screen, (60, 55, 50), (int(self.base_pos.x), int(self.base_pos.y)), 25
        )
        pygame.draw.circle(
            screen, (80, 75, 70), (int(self.base_pos.x), int(self.base_pos.y)), 20
        )

        # 포신 본체
        muzzle_pos = self._get_muzzle_position()
        barrel_points = self._get_barrel_polygon()
        pygame.draw.polygon(screen, (70, 65, 60), barrel_points)

        # 포신 하이라이트
        highlight_offset = pygame.math.Vector2(
            -math.sin(self.current_angle) * 3, math.cos(self.current_angle) * 3
        )
        highlight_start = self.base_pos + highlight_offset
        highlight_end = muzzle_pos + highlight_offset
        pygame.draw.line(
            screen,
            (90, 85, 80),
            (int(highlight_start.x), int(highlight_start.y)),
            (int(highlight_end.x), int(highlight_end.y)),
            3,
        )

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
            math.cos(self.current_angle), math.sin(self.current_angle)
        )
        # 수직 벡터
        perpendicular = pygame.math.Vector2(-direction.y, direction.x)

        # 반동 적용된 길이
        effective_length = self.barrel_length - self.recoil_offset

        # 4개의 꼭지점
        half_width = self.barrel_width / 2
        base_left = self.base_pos + perpendicular * half_width
        base_right = self.base_pos - perpendicular * half_width
        tip_left = (
            self.base_pos
            + direction * effective_length
            + perpendicular * (half_width * 0.7)
        )
        tip_right = (
            self.base_pos
            + direction * effective_length
            - perpendicular * (half_width * 0.7)
        )

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
            pygame.draw.line(
                screen,
                (255, 80, 80),
                (int(start.x), int(start.y)),
                (int(end.x), int(end.y)),
                2,
            )

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
            screen.blit(
                surf, (int(muzzle_pos.x - actual_size), int(muzzle_pos.y - actual_size))
            )

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
        extensions = ["jpg", "png", "png", "png", "png"]
        try:
            for i in range(5):
                img_path = Path(
                    f"assets/images/vfx/combat/combat_motion_0{i}.{extensions[i]}"
                )
                if img_path.exists():
                    img = pygame.image.load(str(img_path)).convert()
                    scaled = pygame.transform.scale(img, self.screen_size)
                    self.motion_frames.append(scaled)
                else:
                    print(f"WARNING: {img_path} not found")

            if len(self.motion_frames) > 0:
                print(
                    f"INFO: CombatMotionEffect loaded ({len(self.motion_frames)} frames)"
                )
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

    def update_player_movement(
        self, is_moving: bool, dt: float, player_pos=None, move_direction=None
    ):
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
            eased = decel_progress**2  # ease-in quad
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
            eased = 0.2 * (t**2)  # ease-in quad
        else:
            # 후반 50%: 빠르게 확대 (나머지 80% 진행)
            t = (intro_progress - 0.5) / 0.5
            eased = 0.2 + 0.8 * (1 - (1 - t) ** 2)  # ease-out quad

        # 원형 마스크 반경: 작은 원 → 전체 화면을 덮을 만큼 확대
        # 대각선 길이를 기준으로 최대 반경 계산
        max_radius = math.sqrt(sw**2 + sh**2)
        min_radius = 60  # 시작 반경 (더 큰 원으로 시작)
        current_radius = min_radius + (max_radius - min_radius) * eased

        # 첫 번째 모션 프레임
        base_frame = self.motion_frames[0]

        # 원형 마스크 Surface 생성
        mask_surf = pygame.Surface(self.screen_size, pygame.SRCALPHA)

        # 원형 클리핑 영역에 속도감 이미지 그리기
        # 원 내부만 보이도록 마스크 적용
        pygame.draw.circle(
            mask_surf, (255, 255, 255, 255), (int(px), int(py)), int(current_radius)
        )

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
            pygame.draw.circle(
                screen,
                edge_color,
                (int(px), int(py)),
                int(current_radius),
                edge_thickness,
            )

        # 방사형 속도선 제거됨

    def _draw_warp_lines(
        self, screen: pygame.Surface, cx: int, cy: int, progress: float, alpha: int
    ):
        """워프 속도선 그리기 (원형 가장자리에서 바깥으로 뻗어나감)"""
        import math

        line_count = 16  # 방사선 개수 (32 → 16으로 축소)
        sw, sh = self.screen_size
        max_radius = math.sqrt(sw**2 + sh**2)

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

            pygame.draw.line(
                line_surf,
                color,
                (int(start_x), int(start_y)),
                (int(end_x), int(end_y)),
                thickness,
            )

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
            flash_alpha = int(200 * (1 - intro_progress**0.5))
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
