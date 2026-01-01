'''
Combat Effects - Damage numbers and combat animations
전투 효과 - 데미지 표시 및 전투 애니메이션

Extracted from objects.py
'''
import pygame
import random
from typing import Tuple, List, Dict
from pathlib import Path
import config
from asset_manager import AssetManager


# ============================================================
# Animated Effect
# ============================================================

class AnimatedEffect:
    """애니메이션을 재생하고 스스로 제거되는 이펙트 클래스"""

    def __init__(
        self,
        pos: Tuple[int, int],
        screen_height: int,
        image_path: Path,
        object_type_key: str,
        frame_duration: float = 0.1,
        total_frames: int = 1,
    ):
        self.pos = pygame.math.Vector2(pos)
        self.start_time = pygame.time.get_ticks() / 1000.0
        self.frame_duration = frame_duration
        self.total_frames = total_frames
        self.is_finished = False

        # 이미지 로드 및 크기 설정 (config.IMAGE_SIZE_RATIOS 사용)
        size_ratio = config.IMAGE_SIZE_RATIOS.get(object_type_key, 0.03)  # 기본값 0.03
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


# ============================================================
# Damage Number System
# ============================================================

class DamageNumber:
    """데미지 숫자를 표시하는 클래스 (누적 데미지 지원)"""

    # 데미지 크기에 따른 폰트/색상 설정
    DAMAGE_TIERS = {
        "small": {
            "threshold": 0,
            "font_size": 20,
            "color": (200, 200, 200),
            "lifetime": 0.8,
        },
        "normal": {
            "threshold": 30,
            "font_size": 26,
            "color": (255, 255, 100),
            "lifetime": 1.2,
        },
        "big": {
            "threshold": 100,
            "font_size": 34,
            "color": (255, 180, 50),
            "lifetime": 1.5,
        },
        "huge": {
            "threshold": 300,
            "font_size": 44,
            "color": (255, 100, 50),
            "lifetime": 2.0,
        },
        "massive": {
            "threshold": 1000,
            "font_size": 56,
            "color": (255, 50, 50),
            "lifetime": 2.5,
        },
    }

    def __init__(
        self,
        damage: float,
        pos: Tuple[float, float],
        is_accumulated: bool = False,
        is_critical: bool = False,
        font: pygame.font.Font = None,
    ):
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
            new_size = (
                int(base_text.get_width() * self.scale),
                int(base_text.get_height() * self.scale),
            )
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
            alpha = int(
                255 * (1 - (elapsed_time - fade_start) / (self.lifetime - fade_start))
            )
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

    def __init__(
        self,
        accumulate_window: float = 0.4,
        show_ticks: bool = False,
        max_numbers: int = 15,
    ):
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

    def add_damage(
        self,
        damage: float,
        pos: Tuple[float, float],
        target_id: int = None,
        is_critical: bool = False,
    ):
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
            self._create_damage_number(
                damage, pos, is_accumulated=False, is_critical=is_critical
            )

    def _add_tick_damage(self, damage: float, pos: Tuple[float, float]):
        """작은 틱 데미지 표시"""
        # 틱 데미지는 작고 빠르게 사라짐
        dmg_num = DamageNumber(damage, pos, is_accumulated=False)
        dmg_num.lifetime = 0.5
        dmg_num.rise_speed = 80
        self.damage_numbers.append(dmg_num)

    def _create_damage_number(
        self,
        damage: float,
        pos: Tuple[float, float],
        is_accumulated: bool = False,
        is_critical: bool = False,
    ):
        """데미지 숫자 생성"""
        dmg_num = DamageNumber(
            damage, pos, is_accumulated=is_accumulated, is_critical=is_critical
        )
        self.damage_numbers.append(dmg_num)

        # 최대 개수 제한
        if len(self.damage_numbers) > self.max_numbers:
            # 가장 오래된 것 제거
            self.damage_numbers = self.damage_numbers[-self.max_numbers :]

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
                    is_critical=acc.get("is_critical", False),
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
                is_critical=acc.get("is_critical", False),
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
