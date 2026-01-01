# modes/base_mode.py
"""
GameMode 베이스 클래스
모든 게임 모드의 공통 인터페이스 및 기능 정의
"""

import pygame
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from engine.game_engine import GameEngine

import config
# Entity imports from new modules
from entities.player import Player
from entities.enemies import Enemy
from entities.weapons import Bullet
from entities.collectibles import CoinGem, HealItem
from entities.support_units import Turret, Drone
# Effect classes from effects modules and objects
from effects.combat_effects import DamageNumberManager
from effects.death_effects import DeathEffectManager
from effects.game_animations import SpawnEffect
from effects.screen_effects import (
    ScreenShake, Particle, Shockwave, DynamicTextEffect,
    TimeSlowEffect, DamageFlash, LevelUpEffect
)
from ui_render import HPBarShake


@dataclass
class ModeConfig:
    """
    모드별 설정값
    각 모드는 이 설정을 오버라이드하여 고유한 동작 정의
    """
    # 모드 식별
    mode_name: str = "base"

    # 원근법 설정
    perspective_enabled: bool = True
    perspective_apply_to_player: bool = True
    perspective_apply_to_enemies: bool = True
    perspective_apply_to_bullets: bool = True
    perspective_apply_to_gems: bool = True

    # 플레이어 설정
    player_speed_multiplier: float = 1.0
    player_start_pos: tuple = (960, 540)
    player_afterimages_enabled: bool = True

    # 배경 설정
    background_type: str = "parallax"  # "parallax", "static", "tilemap"
    parallax_enabled: bool = True
    meteor_enabled: bool = True

    # UI 설정
    show_wave_ui: bool = True
    show_stage_ui: bool = False
    show_minimap: bool = False
    show_skill_indicators: bool = True

    # 게임플레이 설정
    wave_system_enabled: bool = True
    spawn_system_enabled: bool = True
    random_events_enabled: bool = True

    # 에셋 프리픽스 (모드별 에셋 구분용)
    asset_prefix: str = "default"


class GameMode(ABC):
    """
    게임 모드 베이스 클래스

    모든 게임 모드는 이 클래스를 상속하고 추상 메서드를 구현해야 함.
    공통 기능은 베이스 클래스에서 제공.
    """

    def __init__(self, engine: "GameEngine"):
        """
        모드 초기화

        Args:
            engine: 게임 엔진 참조
        """
        self.engine = engine
        self.screen = engine.screen
        self.screen_size = engine.screen_size
        self.asset_manager = engine.asset_manager
        self.sound_manager = engine.sound_manager
        self.fonts = engine.fonts

        # 모드 설정 로드
        self.config = self.get_config()

        # 모드 상태
        self.is_paused = False
        self.game_state = config.GAME_STATE_RUNNING

        # 게임 데이터 (모드별로 관리)
        self.game_data: Dict[str, Any] = {}

        # 공통 객체 리스트
        self.player: Optional[Player] = None
        self.enemies: List[Enemy] = []
        self.bullets: List[Bullet] = []
        self.gems: List[CoinGem | HealItem] = []
        self.effects: List = []
        self.damage_numbers: List = []  # (deprecated) 기존 호환용
        self.turrets: List[Turret] = []
        self.drones: List[Drone] = []

        # 공통 시스템
        self.screen_shake = ScreenShake()
        self.death_effect_manager = DeathEffectManager()

        # 데미지 숫자 매니저 (누적 시스템)
        # accumulate_window: 데미지 누적 시간 (초)
        # show_ticks: 개별 작은 데미지도 표시할지
        # max_numbers: 화면에 표시할 최대 숫자 수
        self.damage_number_manager = DamageNumberManager(
            accumulate_window=0.4,
            show_ticks=False,
            max_numbers=15
        )

        # 타임 스케일 (슬로우 모션용)
        self.time_scale = 1.0

        # 타겟팅 시스템 (더블클릭으로 적 타겟 지정)
        self.targeted_enemy: Optional[Enemy] = None  # 현재 타겟 적
        self.last_click_time: float = 0.0  # 마지막 클릭 시간
        self.double_click_threshold: float = 0.3  # 더블클릭 판정 시간 (초)
        self.target_animation_time: float = 0.0  # 타겟 표시 애니메이션

        # 커스텀 커서 (전투 중 타겟팅 마크)
        self.custom_cursor_enabled: bool = False
        self.cursor_animation_time: float = 0.0

        # 시각적 피드백 효과 (하위 모드에서 초기화)
        self.damage_flash = None
        self.level_up_effect = None
        self.hp_bar_shake = None
        self.previous_hp: float = 0.0  # HP 변화 감지용

    # ===== 시각적 피드백 초기화 (공통) =====

    def _init_visual_feedback_effects(self):
        """
        시각적 피드백 효과 초기화 (wave, story, siege 모드 공통)

        - DamageFlash: 피격 시 화면 빨간색 플래시
        - LevelUpEffect: 레벨업 시 시각 효과
        - HPBarShake: HP바 흔들림 효과
        """
        self.damage_flash = DamageFlash(self.screen_size)
        self.level_up_effect = LevelUpEffect(self.screen_size)
        self.hp_bar_shake = HPBarShake()
        self.previous_hp = 0.0

    def _trigger_damage_feedback(self, hp_before: float):
        """
        데미지 피드백 효과 트리거 (HP 감소 시 호출)

        Args:
            hp_before: 데미지 적용 전 HP
        """
        if not self.player or not self.damage_flash:
            return

        if hp_before > self.player.hp:
            damage_taken = hp_before - self.player.hp
            damage_ratio = damage_taken / self.player.max_hp
            self.damage_flash.trigger(damage_ratio)
            if self.hp_bar_shake:
                self.hp_bar_shake.trigger(damage_ratio)

    def _update_visual_feedback(self, dt: float):
        """시각적 피드백 효과 업데이트"""
        if self.damage_flash:
            self.damage_flash.update()
        if self.hp_bar_shake:
            self.hp_bar_shake.update()
        if self.level_up_effect:
            self.level_up_effect.update(dt)

    # ===== 커스텀 커서 (기지 모드용) =====

    def _load_base_cursor(self) -> pygame.Surface:
        """기지용 커스텀 커서 로드"""
        cursor_path = config.ASSET_DIR / "images" / "items" / "mouse_action.png"
        try:
            if cursor_path.exists():
                cursor_img = pygame.image.load(str(cursor_path)).convert_alpha()
                cursor_size = 64  # 2배 크기
                cursor_img = pygame.transform.smoothscale(cursor_img, (cursor_size, cursor_size))
                return cursor_img
        except Exception as e:
            print(f"WARNING: Failed to load base cursor: {e}")
        return None

    def _render_base_cursor(self, screen: pygame.Surface, cursor_img: pygame.Surface):
        """기지용 커스텀 커서 렌더링"""
        if cursor_img:
            mouse_pos = pygame.mouse.get_pos()
            cursor_rect = cursor_img.get_rect(center=mouse_pos)
            screen.blit(cursor_img, cursor_rect)

    def _enable_custom_cursor(self):
        """커스텀 커서 활성화 (기본 마우스 숨김)"""
        pygame.mouse.set_visible(False)

    def _disable_custom_cursor(self):
        """커스텀 커서 비활성화 (기본 마우스 복원)"""
        pygame.mouse.set_visible(True)

    # ===== 추상 메서드 (반드시 구현) =====

    @abstractmethod
    def get_config(self) -> ModeConfig:
        """모드별 설정 반환 - 반드시 오버라이드"""
        pass

    @abstractmethod
    def init(self):
        """모드 초기화 - 반드시 오버라이드"""
        pass

    @abstractmethod
    def update(self, dt: float, current_time: float):
        """게임 로직 업데이트 - 반드시 오버라이드"""
        pass

    @abstractmethod
    def render(self, screen: pygame.Surface):
        """화면 렌더링 - 반드시 오버라이드"""
        pass

    @abstractmethod
    def handle_event(self, event: pygame.event.Event):
        """이벤트 처리 - 반드시 오버라이드"""
        pass

    # ===== 라이프사이클 메서드 (선택적 오버라이드) =====

    def on_enter(self):
        """모드 시작 시 호출"""
        print(f"INFO: Entering {self.config.mode_name} mode")

        # 원근법 설정 적용
        config.PERSPECTIVE_ENABLED = self.config.perspective_enabled
        config.PERSPECTIVE_APPLY_TO_PLAYER = self.config.perspective_apply_to_player
        config.PERSPECTIVE_APPLY_TO_ENEMIES = self.config.perspective_apply_to_enemies
        config.PERSPECTIVE_APPLY_TO_BULLETS = self.config.perspective_apply_to_bullets
        config.PERSPECTIVE_APPLY_TO_GEMS = self.config.perspective_apply_to_gems

    def on_exit(self):
        """모드 종료 시 호출 (정리 작업)"""
        print(f"INFO: Exiting {self.config.mode_name} mode")

        # 사운드 정지
        self.sound_manager.stop_bgm()

        # 객체 정리
        self._clear_all_game_objects()

    def _clear_all_game_objects(self):
        """
        모든 게임 객체 초기화 (재시작, 모드 종료 시 사용)

        하위 모드에서 추가 객체가 있으면 super()._clear_all_game_objects() 호출 후
        자체 객체도 정리하면 됨.
        """
        self.enemies.clear()
        self.bullets.clear()
        self.gems.clear()
        self.effects.clear()
        self.turrets.clear()
        self.drones.clear()
        self.damage_numbers.clear()

        # 매니저 초기화
        if hasattr(self, 'damage_number_manager') and self.damage_number_manager:
            self.damage_number_manager.damage_numbers.clear()
            self.damage_number_manager.accumulated_damage.clear()

        if hasattr(self, 'death_effect_manager') and self.death_effect_manager:
            self.death_effect_manager.fragments.clear()
            self.death_effect_manager.particles.clear()
            self.death_effect_manager.dissolve_effects.clear()
            self.death_effect_manager.fade_effects.clear()
            self.death_effect_manager.implode_effects.clear()
            self.death_effect_manager.vortex_effects.clear()
            self.death_effect_manager.pixelate_effects.clear()

        # 타겟팅 초기화
        self.targeted_enemy = None

        print(f"INFO: All game objects cleared")

    def on_pause(self):
        """다른 모드가 위에 올라올 때 호출"""
        self.is_paused = True
        self.sound_manager.pause_bgm()
        print(f"INFO: Paused {self.config.mode_name} mode")

    def on_resume(self, return_data: Optional[Dict] = None):
        """위의 모드가 종료되고 복귀할 때 호출"""
        self.is_paused = False
        self.sound_manager.resume_bgm()
        print(f"INFO: Resumed {self.config.mode_name} mode")

        if return_data:
            self._handle_return_data(return_data)

    def _handle_return_data(self, data: Dict):
        """서브모드에서 반환된 데이터 처리 - 오버라이드 가능"""
        pass

    # ===== 모드 전환 요청 메서드 =====

    def request_push_mode(self, mode_class, **kwargs):
        """엔진에 새 모드 추가 요청"""
        self.engine.push_mode(mode_class, **kwargs)

    def request_pop_mode(self, return_data: Optional[Dict] = None):
        """엔진에 현재 모드 종료 요청"""
        self.engine.pop_mode(return_data)

    def request_switch_mode(self, mode_class, **kwargs):
        """엔진에 모드 교체 요청"""
        self.engine.switch_mode(mode_class, **kwargs)

    def request_quit(self):
        """엔진에 게임 종료 요청"""
        self.engine.quit()

    # ===== 공통 업데이트 로직 =====

    def update_common(self, dt: float, current_time: float):
        """
        공통 업데이트 로직 (한 번 작성, 모든 모드에서 사용)

        Args:
            dt: 델타 타임
            current_time: 현재 시간
        """
        from game_logic import update_visual_effects

        # 타임 스케일 체크
        self.time_scale = 1.0
        for effect in self.effects:
            if isinstance(effect, TimeSlowEffect) and effect.is_active:
                self.time_scale = effect.get_time_scale()
                break

        # 실제 게임 시간 (타임 슬로우 적용)
        scaled_dt = dt * self.time_scale

        # 화면 떨림 업데이트
        self.screen_offset = self.screen_shake.update()

        # 시각 효과 업데이트
        update_visual_effects(self.effects, dt, self.screen_size, self.enemies)

        # 사망 효과 업데이트
        self.death_effect_manager.update(dt)

        return scaled_dt

    def update_player(self, dt: float, current_time: float):
        """플레이어 업데이트 (오토파일럿 지원)"""
        if not self.player:
            return

        keys = pygame.key.get_pressed()

        # 플레이어 이동 처리 (키보드 + 마우스 클릭 목표)
        self.player.move(keys, dt, self.screen_size, current_time, self.game_data)
        self.player.update_movement_effects(dt)

    def handle_mouse_click(self, event: pygame.event.Event) -> bool:
        """
        마우스 클릭 처리:
        - 좌클릭: 클릭 위치로 이동 (더블클릭 시 적 타겟팅)
        - 우클릭: 타겟 적 또는 가까운 적에게 공격

        Returns:
            bool: 이벤트가 처리되었으면 True
        """
        if not self.player:
            return False

        if event.type != pygame.MOUSEBUTTONDOWN:
            return False

        mouse_pos = event.pos
        import time
        current_time = time.time()

        # 좌클릭: 클릭 위치로 이동 또는 더블클릭 시 적 타겟팅
        if event.button == 1:
            # 더블클릭 감지
            time_since_last_click = current_time - self.last_click_time
            self.last_click_time = current_time

            if time_since_last_click <= self.double_click_threshold:
                # 더블클릭: 클릭 위치에 적이 있으면 타겟 지정
                clicked_enemy = self._find_enemy_at_position(mouse_pos)
                if clicked_enemy:
                    self.targeted_enemy = clicked_enemy
                    self.target_animation_time = 0.0  # 애니메이션 리셋
                    print(f"INFO: Target locked on enemy!")
                    return True

            # 일반 클릭: 이동
            self.player.set_mouse_target(mouse_pos)
            return True

        # 우클릭: 타겟 적 또는 가까운 적에게 공격
        if event.button == 3:
            # 공격 시 CombatMotionEffect 즉시 종료
            if hasattr(self, 'combat_motion_effect') and self.combat_motion_effect:
                self.combat_motion_effect.stop_effect()

            # 타겟이 있고 살아있으면 타겟 공격, 아니면 가까운 적 공격
            if self.targeted_enemy and self.targeted_enemy.is_alive:
                attack_enemy = self.targeted_enemy
            else:
                attack_enemy = self.player.find_nearest_enemy(self.enemies)
                # 타겟이 죽었으면 해제
                if self.targeted_enemy and not self.targeted_enemy.is_alive:
                    self.targeted_enemy = None

            direction = self.player.get_direction_to_enemy(attack_enemy)

            if self.player.weapon.can_shoot():
                # 적 방향으로 총알 발사
                target_pos = self.player.pos + direction * 1000  # 방향으로 먼 지점
                self.player.weapon.fire(
                    self.player.pos, target_pos, self.bullets,
                    self.player.is_piercing, self.player
                )
                if hasattr(self, 'sound_manager') and self.sound_manager:
                    self.sound_manager.play_sfx("shoot")
            return True

        return False

    def _find_enemy_at_position(self, pos: tuple) -> Optional[Enemy]:
        """주어진 위치에 있는 적 찾기"""
        import pygame
        click_pos = pygame.math.Vector2(pos)

        for enemy in self.enemies:
            if not enemy.is_alive:
                continue
            # 적 이미지 크기를 고려한 히트박스 (기본 50x50 또는 실제 크기)
            enemy_size = getattr(enemy, 'size', 50)
            if hasattr(enemy, 'current_image') and enemy.current_image:
                enemy_size = max(enemy.current_image.get_width(), enemy.current_image.get_height())

            # 클릭 위치가 적 범위 내인지 확인
            distance = (click_pos - enemy.pos).length()
            if distance <= enemy_size / 2 + 10:  # 약간의 여유 추가
                return enemy
        return None

    def update_targeting(self, dt: float):
        """타겟팅 시스템 업데이트"""
        # 타겟 애니메이션 시간 업데이트
        self.target_animation_time += dt

        # 타겟이 죽었으면 해제
        if self.targeted_enemy and not self.targeted_enemy.is_alive:
            self.targeted_enemy = None

    def render_target_marker(self, screen: pygame.Surface):
        """타겟 적에게 과녁 표시 렌더링"""
        if not self.targeted_enemy or not self.targeted_enemy.is_alive:
            return

        import math
        enemy = self.targeted_enemy
        pos = (int(enemy.pos.x), int(enemy.pos.y))

        # 애니메이션 효과
        pulse = 0.8 + 0.2 * math.sin(self.target_animation_time * 6)
        rotation = self.target_animation_time * 60  # 회전 속도

        # 과녁 크기 (적 크기 기반)
        enemy_size = getattr(enemy, 'size', 50)
        if hasattr(enemy, 'current_image') and enemy.current_image:
            enemy_size = max(enemy.current_image.get_width(), enemy.current_image.get_height())

        base_radius = int(enemy_size / 2 + 15)
        radius = int(base_radius * pulse)

        # 과녁 서피스 생성 (투명)
        marker_size = radius * 2 + 20
        marker_surf = pygame.Surface((marker_size, marker_size), pygame.SRCALPHA)
        center = (marker_size // 2, marker_size // 2)

        # 색상 (빨간색 계열, 펄스 효과)
        red_intensity = int(200 + 55 * pulse)
        target_color = (red_intensity, 50, 50, 200)
        inner_color = (255, 100, 100, 150)

        # 외곽 원
        pygame.draw.circle(marker_surf, target_color, center, radius, 3)

        # 내부 원
        inner_radius = int(radius * 0.6)
        pygame.draw.circle(marker_surf, inner_color, center, inner_radius, 2)

        # 중심점
        pygame.draw.circle(marker_surf, (255, 80, 80, 220), center, 5)

        # 십자선 (회전)
        line_length = radius + 8
        for i in range(4):
            angle = math.radians(rotation + i * 90)
            start_dist = inner_radius + 5
            end_dist = line_length

            start_x = center[0] + math.cos(angle) * start_dist
            start_y = center[1] + math.sin(angle) * start_dist
            end_x = center[0] + math.cos(angle) * end_dist
            end_y = center[1] + math.sin(angle) * end_dist

            pygame.draw.line(marker_surf, target_color,
                           (start_x, start_y), (end_x, end_y), 2)

        # 코너 마커 (회전하는 L자 모양)
        corner_size = 12
        for i in range(4):
            angle = math.radians(rotation + i * 90 + 45)
            corner_dist = radius - 5

            cx = center[0] + math.cos(angle) * corner_dist
            cy = center[1] + math.sin(angle) * corner_dist

            # L자 모양
            angle1 = angle - math.radians(45)
            angle2 = angle + math.radians(45)

            p1 = (cx + math.cos(angle1) * corner_size, cy + math.sin(angle1) * corner_size)
            p2 = (cx, cy)
            p3 = (cx + math.cos(angle2) * corner_size, cy + math.sin(angle2) * corner_size)

            pygame.draw.lines(marker_surf, (255, 150, 150, 180), False,
                            [p1, p2, p3], 2)

        # 화면에 블릿
        screen.blit(marker_surf, (pos[0] - marker_size // 2, pos[1] - marker_size // 2))

    def enable_custom_cursor(self, enabled: bool = True):
        """커스텀 커서 활성화/비활성화"""
        self.custom_cursor_enabled = enabled
        pygame.mouse.set_visible(not enabled)

    def update_custom_cursor(self, dt: float):
        """커스텀 커서 애니메이션 업데이트"""
        if self.custom_cursor_enabled:
            self.cursor_animation_time += dt

    def render_custom_cursor(self, screen: pygame.Surface):
        """흰색 타겟팅 마크 커서 렌더링"""
        if not self.custom_cursor_enabled:
            return

        import math
        mouse_pos = pygame.mouse.get_pos()

        # 애니메이션 효과
        pulse = 0.9 + 0.1 * math.sin(self.cursor_animation_time * 8)
        rotation = self.cursor_animation_time * 45  # 느린 회전

        # 커서 크기
        base_size = 20
        size = int(base_size * pulse)

        # 커서 서피스 생성
        cursor_size = size * 2 + 10
        cursor_surf = pygame.Surface((cursor_size, cursor_size), pygame.SRCALPHA)
        center = (cursor_size // 2, cursor_size // 2)

        # 흰색 타겟팅 마크
        white = (255, 255, 255, 230)
        white_dim = (200, 200, 200, 180)

        # 외곽 원
        pygame.draw.circle(cursor_surf, white, center, size, 2)

        # 내부 원
        inner_size = int(size * 0.5)
        pygame.draw.circle(cursor_surf, white_dim, center, inner_size, 1)

        # 중심점
        pygame.draw.circle(cursor_surf, white, center, 3)

        # 십자선 (회전)
        line_length = size + 6
        gap = inner_size + 2
        for i in range(4):
            angle = math.radians(rotation + i * 90)

            start_x = center[0] + math.cos(angle) * gap
            start_y = center[1] + math.sin(angle) * gap
            end_x = center[0] + math.cos(angle) * line_length
            end_y = center[1] + math.sin(angle) * line_length

            pygame.draw.line(cursor_surf, white,
                           (start_x, start_y), (end_x, end_y), 2)

        # 코너 마커 (대각선 방향)
        corner_dist = size - 3
        for i in range(4):
            angle = math.radians(rotation + i * 90 + 45)
            cx = center[0] + math.cos(angle) * corner_dist
            cy = center[1] + math.sin(angle) * corner_dist

            # 작은 점
            pygame.draw.circle(cursor_surf, white_dim, (int(cx), int(cy)), 2)

        # 화면에 블릿 (마우스 위치 중심)
        screen.blit(cursor_surf,
                   (mouse_pos[0] - cursor_size // 2,
                    mouse_pos[1] - cursor_size // 2))

    def update_objects(self, dt: float):
        """게임 객체 업데이트 (총알, 터렛, 드론)"""
        # 터렛 업데이트
        for turret in self.turrets[:]:
            turret.update(dt, self.enemies, self.bullets)
            if not turret.is_alive:
                self.turrets.remove(turret)

        # 드론 업데이트
        for drone in self.drones[:]:
            drone.update(dt, self.enemies, self.bullets)
            if not drone.is_alive:
                self.drones.remove(drone)

        # 총알 업데이트
        for bullet in self.bullets[:]:
            bullet.update(dt, self.screen_size)
            if not bullet.is_alive:
                self.bullets.remove(bullet)

    # ===== 공통 렌더링 로직 =====

    def render_common(self, screen: pygame.Surface):
        """
        공통 게임 객체 렌더링 (한 번 작성, 모든 모드에서 사용)

        Args:
            screen: pygame 화면 Surface
        """
        from game_logic import draw_visual_effects

        # 젬 그리기
        for gem in self.gems:
            gem.draw(screen)

        # 터렛 그리기
        for turret in self.turrets:
            turret.draw(screen)

        # 드론 그리기
        for drone in self.drones:
            drone.draw(screen)

        # 적 그리기 (Y 위치 기준 정렬)
        sorted_enemies = sorted(self.enemies, key=lambda e: e.pos.y)
        for enemy in sorted_enemies:
            enemy.draw(screen)

        # 플레이어 그리기
        if self.player:
            self.player.draw(screen)

        # 총알 그리기
        for bullet in self.bullets:
            bullet.draw(screen)

        # 시각 효과 그리기
        screen_offset = getattr(self, 'screen_offset', (0, 0))
        draw_visual_effects(screen, self.effects, screen_offset)

        # 사망 효과 그리기
        self.death_effect_manager.draw(screen)

        # 데미지 넘버 그리기 (매니저 우선 사용)
        if hasattr(self, 'damage_number_manager') and self.damage_number_manager:
            self.damage_number_manager.draw(screen)
        else:
            for dmg_num in self.damage_numbers:
                dmg_num.draw(screen)

    # ===== 공통 이벤트 처리 =====

    def handle_common_events(self, event: pygame.event.Event) -> bool:
        """
        공통 이벤트 처리

        Args:
            event: pygame 이벤트

        Returns:
            이벤트가 처리되었으면 True
        """
        current_state = self.game_data.get("game_state", config.GAME_STATE_RUNNING)

        if event.type == pygame.KEYDOWN:
            # ESC: 종료 확인 (BOSS_CLEAR 상태에서는 특별 처리)
            if event.key == pygame.K_ESCAPE:
                # BOSS_CLEAR 상태에서는 ESC를 개별 핸들러에서 처리
                if current_state != config.GAME_STATE_BOSS_CLEAR:
                    self.game_data["previous_game_state"] = current_state
                    self.game_data["game_state"] = config.GAME_STATE_QUIT_CONFIRM
                    return True

            # P: 일시정지
            if event.key == pygame.K_p:
                if current_state == config.GAME_STATE_RUNNING:
                    self.game_data["game_state"] = config.GAME_STATE_PAUSED
                elif current_state == config.GAME_STATE_PAUSED:
                    self.game_data["game_state"] = config.GAME_STATE_RUNNING
                return True

            # F1: 설정 메뉴
            if event.key == pygame.K_F1:
                if current_state in [config.GAME_STATE_RUNNING, config.GAME_STATE_PAUSED]:
                    self.game_data["previous_game_state"] = current_state
                    self.game_data["game_state"] = config.GAME_STATE_SETTINGS
                return True

        return False

    # ===== 미션 완료 처리 (공통) =====

    def _complete_mission_and_return(self, mission_type: str = "side"):
        """
        미션 완료 처리 후 BaseHub로 귀환 (wave_mode, siege_mode, story_mode 공통)

        Args:
            mission_type: 미션 타입 ("side", "siege", "story" 등)
        """
        import json
        from pathlib import Path

        # 현재 미션 정보
        current_mission = self.engine.shared_state.get('current_mission')
        mission_data = self.engine.shared_state.get('mission_data')

        if current_mission:
            # 미션 완료 처리
            completed_missions = self.engine.shared_state.get('completed_missions', [])
            if current_mission not in completed_missions:
                completed_missions.append(current_mission)
                self.engine.shared_state['completed_missions'] = completed_missions

            # 보상 지급
            if mission_data and 'rewards' in mission_data:
                rewards = mission_data['rewards']
                if hasattr(rewards, 'credits') and rewards.credits > 0:
                    current_credits = self.engine.shared_state.get('global_score', 0)
                    self.engine.shared_state['global_score'] = current_credits + rewards.credits

            # 진행 저장
            self._save_mission_progress()

            print(f"INFO: {mission_type.capitalize()} mission {current_mission} completed!")

        # 미션 상태 초기화
        self.engine.shared_state['current_mission'] = None
        self.engine.shared_state['mission_data'] = None
        self.engine.shared_state['is_side_mission'] = False
        self.engine.shared_state['from_briefing'] = False

        # BaseHub로 귀환
        from modes.base_hub_mode import BaseHubMode
        self.request_switch_mode(BaseHubMode)

    def _save_mission_progress(self):
        """미션 진행 상황 저장 (공통)"""
        import json
        from pathlib import Path

        completed_missions = self.engine.shared_state.get('completed_missions', [])
        credits = self.engine.shared_state.get('global_score', 0)

        # 현재 저장 데이터 로드
        save_path = Path("saves/campaign_progress.json")
        try:
            if save_path.exists():
                with open(save_path, 'r', encoding='utf-8') as f:
                    save_data = json.load(f)
            else:
                save_data = {}

            # 업데이트
            save_data['completed_missions'] = completed_missions
            save_data['credits'] = credits

            # 저장
            save_path.parent.mkdir(parents=True, exist_ok=True)
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, indent=2)

            print(f"INFO: Mission progress saved")

        except Exception as e:
            print(f"WARNING: Failed to save mission progress: {e}")

    # ===== 유틸리티 메서드 =====

    def get_player_screen_pos(self) -> tuple:
        """플레이어 화면 위치 반환"""
        if self.player:
            return (int(self.player.pos.x), int(self.player.pos.y))
        return (self.screen_size[0] // 2, self.screen_size[1] // 2)

    def spawn_player(self, pos: tuple = None, upgrades: dict = None, ship_type: str = None):
        """플레이어 생성"""
        if pos is None:
            pos = self.config.player_start_pos

        if upgrades is None:
            upgrades = self.engine.shared_state.get("player_upgrades", {})

        # 함선 타입 (shared_state에서 가져오거나 기본값 사용)
        if ship_type is None:
            ship_type = self.engine.shared_state.get("current_ship", config.DEFAULT_SHIP)
            print(f"DEBUG: spawn_player - current_ship from shared_state: {ship_type}")

        self.player = Player(
            pos=pygame.math.Vector2(pos),
            screen_height=self.screen_size[1],
            upgrades=upgrades,
            ship_type=ship_type
        )

        # 모드별 플레이어 설정 적용
        if not self.config.player_afterimages_enabled:
            self.player.disable_afterimages = True

        print(f"INFO: Player spawned at {pos} with ship: {ship_type}")


print("INFO: base_mode.py loaded")
