"""
Game Animations - Player victory, wave clear, base arrival animations
게임 애니메이션 - 승리, 웨이브 클리어, 기지 도착 등

Extracted from objects.py
"""

import pygame
import math
import random
from typing import Tuple
from pathlib import Path
import config


# ============================================================
# Player Victory Animation
# ============================================================


class PlayerVictoryAnimation:
    """플레이어 승리 애니메이션 - 화면 외곽을 시계방향으로 회전 후 하단 중앙으로 이동"""

    PHASE_ORBIT = 0  # 화면 외곽 시계방향 회전
    PHASE_MOVE_DOWN = 1  # 하단 중앙으로 이동
    PHASE_DONE = 2  # 완료

    def __init__(
        self,
        player,
        screen_size: Tuple[int, int],
        orbit_duration: float = 3.5,
        move_duration: float = 2.0,
    ):
        self.player = player
        self.screen_size = screen_size
        self.orbit_duration = orbit_duration  # 회전 시간: 3.5초 (느리게)
        self.move_duration = move_duration  # 이동 시간: 2.0초

        self.age = 0.0
        self.is_alive = True
        self.phase = self.PHASE_ORBIT
        self.on_complete = None  # 완료 시 콜백

        # 시작 위치 저장
        self.start_pos = pygame.math.Vector2(player.pos.x, player.pos.y)

        # 화면 중심
        self.center = pygame.math.Vector2(screen_size[0] // 2, screen_size[1] // 2)

        # 타원 궤도 반경 (축소)
        self.orbit_radius_x = screen_size[0] * 0.38
        self.orbit_radius_y = screen_size[1] * 0.38

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
                self.orbit_end_pos = pygame.math.Vector2(
                    self.player.pos.x, self.player.pos.y
                )
                self.phase = self.PHASE_MOVE_DOWN
                self.age = 0.0  # 시간 리셋

        elif self.phase == self.PHASE_MOVE_DOWN:
            # 하단 중앙으로 서서히 이동
            if self.age < self.move_duration:
                progress = self.age / self.move_duration
                # easing: ease-out
                eased = 1 - ((1 - progress) ** 2)

                # 선형 보간
                self.player.pos.x = (
                    self.orbit_end_pos.x
                    + (self.target_pos.x - self.orbit_end_pos.x) * eased
                )
                self.player.pos.y = (
                    self.orbit_end_pos.y
                    + (self.target_pos.y - self.orbit_end_pos.y) * eased
                )
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
            self.player.image_rect.center = (
                int(self.player.pos.x),
                int(self.player.pos.y),
            )
        if self.player.hitbox:
            self.player.hitbox.center = (int(self.player.pos.x), int(self.player.pos.y))


# ============================================================
# Wave Clear Fireworks Effect
# ============================================================


class WaveClearFireworksEffect:
    """웨이브 클리어 축하 불꽃놀이 효과 - 쿨타임 근처에서 시작하여 위로 이동"""

    def __init__(
        self, screen_size: Tuple[int, int], duration: float = 3.5, is_boss: bool = False
    ):
        """
        Args:
            screen_size: 화면 크기
            duration: 효과 지속 시간 (초)
            is_boss: 보스전 여부 (True면 3개 불꽃, False면 1개만)
        """
        self.screen_size = screen_size
        self.duration = duration
        self.age = 0.0
        self.is_alive = True
        self.is_boss = is_boss

        # 원본 fireworks 이미지 로드
        self.base_image = None
        try:
            if config.WAVE_CLEAR_FIREWORKS_PATH.exists():
                self.base_image = pygame.image.load(
                    str(config.WAVE_CLEAR_FIREWORKS_PATH)
                ).convert_alpha()
                print(
                    f"INFO: Fireworks base image loaded: {self.base_image.get_size()}"
                )
            else:
                print(
                    f"WARNING: Fireworks image not found at {config.WAVE_CLEAR_FIREWORKS_PATH}"
                )
        except Exception as e:
            print(f"ERROR: Failed to load fireworks image: {e}")
            self.base_image = None

        # 불꽃 버스트 설정
        self.fireworks_bursts = []
        if self.base_image:
            # 쿨타임 UI 위치 (화면 하단 중앙)
            cooltime_y = screen_size[1] - 150  # 쿨타임 상부

            if is_boss:
                # 보스전: 3개 불꽃 (중앙 메인 + 좌우 보조) - 삼원색 적용
                burst_configs = [
                    # (delay, start_scale, end_scale, x_ratio, start_y, end_y_offset, rotation_speed, color_tint)
                    (
                        0.0,
                        0.15,
                        0.35,
                        0.50,
                        cooltime_y,
                        -250,
                        15,
                        (255, 100, 100),
                    ),  # 중앙 - 빨강
                    (
                        0.6,
                        0.10,
                        0.20,
                        0.30,
                        cooltime_y,
                        -180,
                        -12,
                        (100, 255, 100),
                    ),  # 좌측 - 초록
                    (
                        0.6,
                        0.10,
                        0.20,
                        0.70,
                        cooltime_y,
                        -180,
                        12,
                        (100, 100, 255),
                    ),  # 우측 - 파랑
                ]
            else:
                # 일반 웨이브: 1개 불꽃만 (중앙) - 원본 색상
                burst_configs = [
                    (
                        0.0,
                        0.15,
                        0.30,
                        0.50,
                        cooltime_y,
                        -220,
                        12,
                        (255, 255, 255),
                    ),  # 중앙만 - 흰색
                ]

            for (
                delay,
                start_scale,
                end_scale,
                x_ratio,
                start_y,
                end_y_offset,
                rot_speed,
                color_tint,
            ) in burst_configs:
                # 시작/종료 위치
                x = int(screen_size[0] * x_ratio)
                end_y = start_y + end_y_offset  # 위로 이동

                self.fireworks_bursts.append(
                    {
                        "delay": delay,
                        "start_scale": start_scale,
                        "end_scale": end_scale,
                        "x": x,
                        "start_y": start_y,
                        "end_y": end_y,
                        "current_y": start_y,
                        "current_scale": start_scale,
                        "rotation": 0.0,
                        "rotation_speed": rot_speed,
                        "color_tint": color_tint,  # RGB 색상 틴트
                    }
                )

            print(
                f"INFO: Created {len(self.fireworks_bursts)} fireworks bursts (boss={is_boss})"
            )

    def update(self, dt: float):
        """효과 업데이트"""
        if not self.is_alive:
            return

        self.age += dt

        # 지속 시간 경과 시 종료
        if self.age >= self.duration:
            self.is_alive = False
            return

        # 각 불꽃 버스트 업데이트 (위치 이동 + 크기 증가 + 회전)
        for burst in self.fireworks_bursts:
            if self.age >= burst["delay"]:
                burst_age = self.age - burst["delay"]

                # 이동 애니메이션 (1.5초 동안 위로 이동하며 커짐)
                move_duration = 1.5
                if burst_age < move_duration:
                    # ease-out 적용 (빠르게 시작, 느리게 끝)
                    progress = burst_age / move_duration
                    eased = 1 - (1 - progress) ** 2

                    # Y 위치 이동
                    burst["current_y"] = (
                        burst["start_y"] + (burst["end_y"] - burst["start_y"]) * eased
                    )

                    # 크기 증가
                    burst["current_scale"] = (
                        burst["start_scale"]
                        + (burst["end_scale"] - burst["start_scale"]) * eased
                    )
                else:
                    # 이동 완료 후 고정
                    burst["current_y"] = burst["end_y"]
                    burst["current_scale"] = burst["end_scale"]

                # 회전 애니메이션
                burst["rotation"] += burst["rotation_speed"] * dt

    def draw(self, screen: pygame.Surface):
        """효과 그리기"""
        if not self.is_alive:
            return

        if not self.base_image:
            return

        # 모든 불꽃 그리기 (작은 것부터 = 깊이감)
        sorted_bursts = sorted(self.fireworks_bursts, key=lambda b: b["current_scale"])

        for burst in sorted_bursts:
            # 딜레이 체크 - 아직 시작 안 됨
            if self.age < burst["delay"]:
                continue

            burst_age = self.age - burst["delay"]

            # 페이드 인/아웃 계산
            fade_in_duration = 0.3
            fade_out_start = 2.0
            fade_out_duration = 0.8

            if burst_age < fade_in_duration:
                # 페이드 인
                alpha = int(255 * (burst_age / fade_in_duration))
            elif burst_age > fade_out_start:
                # 페이드 아웃 (천천히)
                alpha = int(
                    255 * (1.0 - (burst_age - fade_out_start) / fade_out_duration)
                )
                alpha = max(0, alpha)
            else:
                alpha = 255

            if alpha <= 0:
                continue

            # 현재 크기로 이미지 스케일
            target_size = int(
                min(self.screen_size[0], self.screen_size[1]) * burst["current_scale"]
            )
            aspect_ratio = self.base_image.get_height() / self.base_image.get_width()
            img_width = target_size
            img_height = int(target_size * aspect_ratio)

            if img_width <= 0 or img_height <= 0:
                continue

            # 이미지 스케일링
            scaled_img = pygame.transform.smoothscale(
                self.base_image, (img_width, img_height)
            )

            # 색상 틴트 적용 (RGB 곱셈)
            color_tint = burst.get("color_tint", (255, 255, 255))
            if color_tint != (255, 255, 255):
                # 틴트용 임시 surface 생성
                tinted_img = scaled_img.copy()
                tint_surface = pygame.Surface(tinted_img.get_size()).convert_alpha()
                tint_surface.fill(color_tint)
                tinted_img.blit(
                    tint_surface, (0, 0), special_flags=pygame.BLEND_RGB_MULT
                )
                scaled_img = tinted_img

            # 회전 적용
            rotated_img = pygame.transform.rotate(scaled_img, burst["rotation"])

            # 알파 적용
            rotated_img.set_alpha(alpha)

            # 그리기 (중앙 정렬)
            draw_x = burst["x"] - rotated_img.get_width() // 2
            draw_y = int(burst["current_y"]) - rotated_img.get_height() // 2

            screen.blit(rotated_img, (draw_x, draw_y))


# ============================================================
# Return to Base Animation
# ============================================================


class ReturnToBaseAnimation:
    """에피소드 종료 후 기지로 복귀하는 플레이어 우주선 애니메이션"""

    # 애니메이션 단계
    PHASE_ORBIT = "orbit"  # 화면 외곽 시계반대방향 회전
    PHASE_WARP_PORTAL = "warp_portal"  # 워프 포탈 페이드 인/아웃
    PHASE_COMPLETE = "complete"  # 완료

    def __init__(self, player_image, start_pos, screen_size):
        self.original_image = player_image.copy()
        self.screen_width, self.screen_height = screen_size

        # 시작 위치..
        self.start_pos = pygame.math.Vector2(start_pos)
        self.pos = pygame.math.Vector2(start_pos)

        # 화면 중심
        self.center = pygame.math.Vector2(screen_size[0] // 2, screen_size[1] // 2)

        # 타원 궤도 반경 (축소)
        self.orbit_radius_x = screen_size[0] * 0.38
        self.orbit_radius_y = screen_size[1] * 0.38

        # 시작 각도 계산 (현재 위치에서 중심까지의 각도)
        diff = self.start_pos - self.center
        self.start_angle = math.atan2(diff.y, diff.x)

        self.rotation = 0.0
        self.phase = self.PHASE_ORBIT
        self.elapsed = 0.0
        self.is_alive = True
        self.orbit_duration = 4.5  # 회전 시간: 4.5초 (충분한 시간 확보)
        self.ship_alpha = 255  # 우주선 알파값 (페이드 아웃용)

        # 워프 효과 트리거 지점 (화면 좌측 30% - 더 여유있게)
        self.warp_trigger_x = screen_size[0] * 0.3
        self.warp_started = False

        # 회전 완료 시 위치
        self.orbit_end_pos = None

        # 워프 포탈 이미지 (warp_transition.png)
        self.warp_portal_image = None
        self.warp_portal_size = 520  # 포탈 크기 (픽셀) - 30% 확대 (400 * 1.3 = 520)
        self.warp_portal_alpha = 0  # 페이드 인/아웃용 알파값
        self.warp_portal_duration = 1.5  # 페이드 인 + 유지 + 페이드 아웃 총 시간
        self.warp_portal_start_time = 0.0
        self._load_warp_portal_image()

    def update(self, dt):
        if not self.is_alive:
            return
        self.elapsed += dt

        if self.phase == self.PHASE_ORBIT:
            # 타원 궤도를 따라 시계반대방향 회전
            progress = min(
                2.0, self.elapsed / self.orbit_duration
            )  # 최대 2바퀴까지 허용
            # easing: ease-in-out
            eased = (
                progress * progress * (3 - 2 * progress)
                if progress <= 1.0
                else progress
            )

            # 시계반대방향 회전 (-2π = 한 바퀴)
            current_angle = self.start_angle - (2 * math.pi * eased)

            # 타원 궤도 위치 계산
            new_x = self.center.x + math.cos(current_angle) * self.orbit_radius_x
            new_y = self.center.y + math.sin(current_angle) * self.orbit_radius_y

            self.pos.x = new_x
            self.pos.y = new_y

            # 화면 좌측에 가까워지면 워프 포탈 효과 시작
            if not self.warp_started and self.pos.x <= self.warp_trigger_x:
                self.warp_started = True
                self.warp_start_time = self.elapsed
                print(
                    f"INFO: Warp portal triggered at pos=({self.pos.x:.0f}, {self.pos.y:.0f}), elapsed={self.elapsed:.2f}s"
                )

            # 워프 포탈 효과 업데이트  (시작된 이후)
            if self.warp_started:
                warp_elapsed = self.elapsed - self.warp_start_time

                # 우주선 페이드 아웃
                fade_progress = min(1.0, warp_elapsed / 0.8)
                self.ship_alpha = int(255 * (1.0 - fade_progress))

                # 워프 포탈 페이드 인/아웃 (0.5초 페이드인, 0.5초 유지, 0.5초 페이드아웃)
                if warp_elapsed < 0.5:
                    # 페이드 인
                    self.warp_portal_alpha = int(255 * (warp_elapsed / 0.5))
                elif warp_elapsed < 1.0:
                    # 완전히 보임
                    self.warp_portal_alpha = 255
                elif warp_elapsed < 1.5:
                    # 페이드 아웃
                    self.warp_portal_alpha = int(
                        255 * (1.0 - (warp_elapsed - 1.0) / 0.5)
                    )
                else:
                    # 완전히 사라짐
                    self.warp_portal_alpha = 0

                # 워프 포탈 완료 후 애니메이션 종료
                if warp_elapsed >= self.warp_portal_duration:
                    self.phase = self.PHASE_COMPLETE
                    self.is_alive = False
                    print("INFO: Warp portal complete, returning to base")

        elif self.phase == self.PHASE_WARP_PORTAL:
            # 이 페이즈는 사용하지 않음 (ORBIT 중에 워프 포탈 표시)
            pass

    def is_complete(self):
        """애니메이션 완료 여부"""
        return not self.is_alive or self.phase == self.PHASE_COMPLETE

    def _load_warp_portal_image(self):
        """워프 포탈 이미지 로드 (warp_transition.png, 원형 포탈 크기로 스케일)"""
        warp_image_path = Path("assets/images/effects/warp_transition.png")
        if warp_image_path.exists():
            try:
                loaded_img = pygame.image.load(str(warp_image_path)).convert_alpha()
                # 포탈 크기로 스케일링 (400x400)
                self.warp_portal_image = pygame.transform.scale(
                    loaded_img, (self.warp_portal_size, self.warp_portal_size)
                )
            except Exception as e:
                self.warp_portal_image = None
        else:
            self.warp_portal_image = None

    def draw(self, screen):
        if not self.is_alive and self.phase != self.PHASE_COMPLETE:
            return

        # 워프 포탈 이미지 그리기 (워프 시작된 경우, 우주선 위치 중심)
        if self.warp_started and self.warp_portal_image and self.warp_portal_alpha > 0:
            portal_with_alpha = self.warp_portal_image.copy()
            portal_with_alpha.set_alpha(self.warp_portal_alpha)
            portal_rect = portal_with_alpha.get_rect(
                center=(int(self.pos.x), int(self.pos.y))
            )
            screen.blit(portal_with_alpha, portal_rect)

        # 우주선 그리기 (워프 시작되면 페이드 아웃)
        if self.warp_started:
            # 우주선 페이드 아웃
            faded_image = self.original_image.copy()
            faded_image.set_alpha(self.ship_alpha)
            rect = faded_image.get_rect(center=(int(self.pos.x), int(self.pos.y)))
            screen.blit(faded_image, rect)
        else:
            # 워프 효과 전: 일반 렌더링
            rect = self.original_image.get_rect(
                center=(int(self.pos.x), int(self.pos.y))
            )
            screen.blit(self.original_image, rect)


# ============================================================
# Base Arrival Animation
# ============================================================


class BaseArrivalAnimation:
    """기지 복귀 시 우주선이 화면에 진입하는 애니메이션

    워프 포탈이 우측 중앙에 나타남 → 우주선 등장 → 기지 중앙으로 이동하며 축소 → 사라짐
    """

    def __init__(self, player_image, screen_size, base_center_pos):
        """
        Args:
            player_image: 플레이어 우주선 이미지
            screen_size: 화면 크기 (width, height)
            base_center_pos: 기지 중앙 위치 (x, y)
        """
        self.original_image = player_image.copy()
        self.screen_width, self.screen_height = screen_size
        self.base_center = pygame.math.Vector2(base_center_pos)

        # 시작 위치 (화면 우측 중앙, 워프 포탈 위치)
        self.portal_pos = pygame.math.Vector2(screen_size[0] - 150, screen_size[1] / 2)
        self.start_pos = pygame.math.Vector2(self.portal_pos)
        self.pos = pygame.math.Vector2(self.start_pos)

        # 목표 위치 (기지 중앙)
        self.target_pos = pygame.math.Vector2(self.base_center)

        # 애니메이션 설정
        self.portal_duration = 0.8  # 워프 포탈 페이드 인 (0.8초)
        self.ship_appear_delay = 0.4  # 우주선 등장 딜레이 (포탈 페이드인 중)
        self.duration = 3.5  # 총 3.5초 (포탈 0.8초 + 이동 2.7초)
        self.elapsed = 0.0
        self.is_alive = True
        self.is_complete_flag = False

        # 크기 변화 (시작: 100%, 종료: 20% - 워프 포탈 대비 우주선 크기 조정)
        self.start_scale = 1.0
        self.end_scale = 0.2

        # 페이드 아웃 시작 시점 (80% 진행 시점부터)
        self.fade_start_progress = 0.85

        # 워프 포탈 이미지
        self.warp_portal_image = None
        self.warp_portal_size = (
            600  # 포탈 크기 (픽셀) - 기지 진입 시 더 크게 (50% 확대)
        )
        self.warp_portal_alpha = 0
        self._load_warp_portal_image()

    def _load_warp_portal_image(self):
        """워프 포탈 이미지 로드 (warp_transition.png)"""
        warp_image_path = Path("assets/images/effects/warp_transition.png")
        if warp_image_path.exists():
            try:
                loaded_img = pygame.image.load(str(warp_image_path)).convert_alpha()
                # 포탈 크기로 스케일링 (400x400)
                self.warp_portal_image = pygame.transform.scale(
                    loaded_img, (self.warp_portal_size, self.warp_portal_size)
                )
                print(
                    f"INFO: [BaseArrival] Warp portal image loaded ({self.warp_portal_size}x{self.warp_portal_size})"
                )
            except Exception as e:
                print(f"WARNING: [BaseArrival] Failed to load warp portal image: {e}")
                self.warp_portal_image = None
        else:
            print(
                f"WARNING: [BaseArrival] Warp portal image not found at {warp_image_path}"
            )
            self.warp_portal_image = None

    def update(self, dt: float):
        """애니메이션 업데이트"""
        if not self.is_alive:
            return

        self.elapsed += dt
        progress = min(1.0, self.elapsed / self.duration)

        if progress >= 1.0:
            self.is_alive = False
            self.is_complete_flag = True
            return

        # 워프 포탈 페이드 인/아웃 (처음 0.8초 동안)
        if self.elapsed < self.portal_duration:
            # 페이드 인 (0 → 1.0)
            portal_progress = self.elapsed / self.portal_duration
            self.warp_portal_alpha = int(255 * portal_progress)
        else:
            # 페이드 아웃 시작 (우주선 이동 중)
            fade_progress = (self.elapsed - self.portal_duration) / (
                self.duration - self.portal_duration
            )
            self.warp_portal_alpha = int(
                255 * (1.0 - min(1.0, fade_progress * 2))
            )  # 빠르게 페이드 아웃

        # Easing: ease-in-out (부드러운 감속)
        eased = progress * progress * (3 - 2 * progress)

        # 우주선 등장 딜레이 (포탈이 어느정도 보인 후)
        if self.elapsed < self.ship_appear_delay:
            # 우주선은 아직 포탈 위치에 숨김
            self.pos = self.start_pos
        else:
            # 우주선 이동 시작
            move_progress = (self.elapsed - self.ship_appear_delay) / (
                self.duration - self.ship_appear_delay
            )
            move_eased = move_progress * move_progress * (3 - 2 * move_progress)
            self.pos = self.start_pos.lerp(self.target_pos, move_eased)

    def draw(self, screen: pygame.Surface):
        """애니메이션 렌더링"""
        if not self.is_alive and not self.is_complete_flag:
            return

        progress = min(1.0, self.elapsed / self.duration)

        # 워프 포탈 이미지 그리기 (포탈 위치 고정)
        if self.warp_portal_image and self.warp_portal_alpha > 0:
            portal_with_alpha = self.warp_portal_image.copy()
            portal_with_alpha.set_alpha(self.warp_portal_alpha)
            portal_rect = portal_with_alpha.get_rect(
                center=(int(self.portal_pos.x), int(self.portal_pos.y))
            )
            screen.blit(portal_with_alpha, portal_rect)

        # 우주선 그리기 (ship_appear_delay 이후에만 표시)
        if self.elapsed >= self.ship_appear_delay:
            # 크기 계산 (선형 축소)
            current_scale = (
                self.start_scale + (self.end_scale - self.start_scale) * progress
            )

            # 이미지 스케일링
            original_size = self.original_image.get_size()
            new_size = (
                int(original_size[0] * current_scale),
                int(original_size[1] * current_scale),
            )

            if new_size[0] > 0 and new_size[1] > 0:
                scaled_image = pygame.transform.scale(self.original_image, new_size)

                # 페이드 아웃 (85% 진행 시점부터)
                if progress >= self.fade_start_progress:
                    fade_progress = (progress - self.fade_start_progress) / (
                        1.0 - self.fade_start_progress
                    )
                    alpha = int(255 * (1.0 - fade_progress))
                    scaled_image.set_alpha(alpha)

                # 그리기
                rect = scaled_image.get_rect(center=(int(self.pos.x), int(self.pos.y)))
                screen.blit(scaled_image, rect)

    def is_complete(self):
        """애니메이션 완료 여부"""
        return self.is_complete_flag


# ============================================================
# Dialogue Ship Animation
# ============================================================


class DialogueShipAnimation:
    """대화 중 우주선 회전 애니메이션

    화면 중앙 부근에서 중간 크기의 타원 궤도로 계속 회전
    우주선 크기는 120-150% 확대
    """

    def __init__(self, player_image, screen_size, scale=1.35):
        """
        Args:
            player_image: 플레이어 우주선 이미지
            screen_size: 화면 크기 (width, height)
            scale: 우주선 크기 배율 (기본 135% = 1.35)
        """
        self.screen_width, self.screen_height = screen_size

        # 우주선 이미지 확대 (120-150%)
        original_size = player_image.get_size()
        new_size = (int(original_size[0] * scale), int(original_size[1] * scale))
        self.ship_image = pygame.transform.scale(player_image, new_size)

        # 화면 중앙 위치
        self.center = pygame.math.Vector2(screen_size[0] // 2, screen_size[1] // 2)

        # 타원 궤도 설정 (중간 크기: 반경 200-300px)
        self.orbit_radius_x = 250  # 가로 반경
        self.orbit_radius_y = 200  # 세로 반경

        # 회전 설정
        self.orbit_speed = 0.3  # 회전 속도 (라디안/초)
        self.current_angle = 0.0  # 현재 각도

        # 현재 위치
        self.pos = pygame.math.Vector2(self.center)

        self.is_alive = True

    def update(self, dt: float):
        """애니메이션 업데이트"""
        if not self.is_alive:
            return

        # 각도 업데이트 (시계 방향 회전)
        self.current_angle += self.orbit_speed * dt

        # 2π를 넘어가면 리셋 (0-2π 범위 유지)
        if self.current_angle >= 2 * 3.14159265:
            self.current_angle -= 2 * 3.14159265

        # 타원 궤도 위치 계산
        self.pos.x = self.center.x + math.cos(self.current_angle) * self.orbit_radius_x
        self.pos.y = self.center.y + math.sin(self.current_angle) * self.orbit_radius_y

    def draw(self, screen: pygame.Surface):
        """애니메이션 렌더링"""
        if not self.is_alive:
            return

        # 우주선 그리기
        rect = self.ship_image.get_rect(center=(int(self.pos.x), int(self.pos.y)))
        screen.blit(self.ship_image, rect)

    def stop(self):
        """애니메이션 중지"""
        self.is_alive = False


# ============================================================
# Spawn Effect
# ============================================================


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
                screen.blit(
                    surf, (int(self.pos.x - radius - 2), int(self.pos.y - radius - 2))
                )


# ============================================================
# Meteor Effect
# ============================================================


class Meteor:
    """유성 효과 - 화면을 대각선으로 가로지르는 작은 유성 (웨이브당 1개)"""

    # 클래스 변수로 이미지 로드 (한 번만 로드)
    _head_image = None
    _trail_image = None

    def __init__(self, screen_size: Tuple[int, int]):
        self.screen_width, self.screen_height = screen_size
        self.is_alive = True

        # 이미지 로드 (처음 한 번만, use_image가 True일 때만)
        if Meteor._head_image is None and config.METEOR_SETTINGS.get(
            "use_image", False
        ):
            try:
                # config에서 정의된 경로 사용
                if (
                    config.METEOR_HEAD_IMAGE_PATH.exists()
                    and config.METEOR_TRAIL_IMAGE_PATH.exists()
                ):
                    # display가 초기화된 경우에만 convert_alpha 사용
                    if pygame.display.get_surface():
                        head_img = pygame.image.load(
                            str(config.METEOR_HEAD_IMAGE_PATH)
                        ).convert_alpha()
                        trail_img = pygame.image.load(
                            str(config.METEOR_TRAIL_IMAGE_PATH)
                        ).convert_alpha()
                    else:
                        head_img = pygame.image.load(str(config.METEOR_HEAD_IMAGE_PATH))
                        trail_img = pygame.image.load(
                            str(config.METEOR_TRAIL_IMAGE_PATH)
                        )

                    # 크기 조정 (설정에 맞춰)
                    head_scale = config.METEOR_SETTINGS.get("head_scale", 1.5)
                    trail_scale = config.METEOR_SETTINGS.get("trail_scale", 1.2)

                    # 원본 이미지 크기 기반으로 스케일링
                    head_w = int(head_img.get_width() * head_scale)
                    head_h = int(head_img.get_height() * head_scale)
                    trail_w = int(trail_img.get_width() * trail_scale)
                    trail_h = int(trail_img.get_height() * trail_scale)

                    Meteor._head_image = pygame.transform.smoothscale(
                        head_img, (head_w, head_h)
                    )
                    Meteor._trail_image = pygame.transform.smoothscale(
                        trail_img, (trail_w, trail_h)
                    )
                    print(
                        f"INFO: Meteor images loaded successfully (head: {head_w}x{head_h}, trail: {trail_w}x{trail_h})"
                    )
                else:
                    print(
                        f"WARNING: Meteor image files not found at {config.METEOR_HEAD_IMAGE_PATH}"
                    )
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
            self.pos = pygame.math.Vector2(
                -20, random.randint(0, self.screen_height // 2)
            )
            angle = random.uniform(20, 45)  # 우하향 각도

        # 방향 벡터
        self.angle_degrees = angle
        self.velocity = (
            pygame.math.Vector2(
                math.cos(math.radians(angle)), math.sin(math.radians(angle))
            ).normalize()
            * self.speed
        )

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
        if self.pos.x > self.screen_width + 50 or self.pos.y > self.screen_height + 50:
            self.is_alive = False

    def draw(self, screen: pygame.Surface):
        """유성 그리기 (꼬리 트레일 포함)"""
        if not self.is_alive:
            return

        # 이미지가 로드되었고 use_image가 True인 경우에만 이미지 사용
        use_image = config.METEOR_SETTINGS.get("use_image", False)
        if (
            use_image
            and Meteor._head_image is not None
            and Meteor._trail_image is not None
        ):
            # 트레일 그리기 (뒤에서 앞으로, 점점 투명하게)
            if len(self.trail_positions) > 1:
                for i, trail_pos in enumerate(
                    self.trail_positions[:-1]
                ):  # 마지막 위치 제외
                    alpha = int(255 * (i + 1) / len(self.trail_positions))
                    scale = (i + 1) / len(self.trail_positions)

                    # 트레일 이미지 회전 및 크기 조정
                    rotated_trail = pygame.transform.rotate(
                        Meteor._trail_image, -self.angle_degrees
                    )
                    scaled_trail = pygame.transform.scale(
                        rotated_trail,
                        (
                            int(rotated_trail.get_width() * scale),
                            int(rotated_trail.get_height() * scale),
                        ),
                    )

                    # 알파 적용
                    scaled_trail.set_alpha(alpha)

                    # 트레일 그리기
                    rect = scaled_trail.get_rect(
                        center=(int(trail_pos.x), int(trail_pos.y))
                    )
                    screen.blit(scaled_trail, rect)

            # 혜성 본체 그리기 (회전 적용)
            rotated_head = pygame.transform.rotate(
                Meteor._head_image, -self.angle_degrees
            )
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
                screen.blit(
                    trail_surf, (int(trail_pos.x - size), int(trail_pos.y - size))
                )

            # 유성 본체 그리기 (밝게)
            head_color = tuple(min(255, c + 50) for c in self.color)
            pygame.draw.circle(
                screen, head_color, (int(self.pos.x), int(self.pos.y)), self.size
            )


# ============================================================
# Static Field
# ============================================================


class StaticField:
    """적 사망 시 생성되는 정전기장 (Static Field 스킬)"""

    # 클래스 변수: 이미지 로드 (한 번만)
    _image_loaded = False
    _original_image = None

    def __init__(
        self,
        pos: Tuple[float, float],
        radius: float,
        duration: float,
        damage_per_sec: float,
    ):
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
            self.image = pygame.transform.scale(
                StaticField._original_image, (size, size)
            )
        else:
            self.image = None

    @classmethod
    def _load_image(cls):
        """Static Field 이미지 로드"""
        try:
            if config.STATIC_FIELD_IMAGE_PATH.exists():
                cls._original_image = pygame.image.load(
                    str(config.STATIC_FIELD_IMAGE_PATH)
                ).convert_alpha()
                print(
                    f"INFO: Static Field image loaded from {config.STATIC_FIELD_IMAGE_PATH}"
                )
            else:
                print(
                    f"WARNING: Static Field image not found at {config.STATIC_FIELD_IMAGE_PATH}"
                )
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

    def apply_damage(self, enemies, dt: float):
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
                circle_surf = pygame.Surface(
                    (self.radius * 2, self.radius * 2), pygame.SRCALPHA
                )
                pygame.draw.circle(
                    circle_surf,
                    (150, 150, 255, alpha),
                    (self.radius, self.radius),
                    self.radius,
                )
                pygame.draw.circle(
                    circle_surf,
                    (100, 200, 255, min(255, alpha + 50)),
                    (self.radius, self.radius),
                    self.radius,
                    2,
                )
                rect = circle_surf.get_rect(center=(int(self.pos.x), int(self.pos.y)))
                screen.blit(circle_surf, rect)
