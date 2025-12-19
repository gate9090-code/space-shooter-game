# modes/siege_objects.py
"""
Galaga Style Siege Mode Objects
갈라그 스타일 공성 모드 오브젝트

FormationEnemy: 포메이션 기반 적 (진입, 배치, 다이브, 복귀)
WaveManager: 웨이브 스폰 및 관리
"""

import pygame
import math
import random
from typing import List, Tuple, Dict, Optional
from pathlib import Path

# config_siege에서 설정 불러오기
try:
    from mode_configs import config_siege as cfg
except ImportError:
    import mode_configs.config_siege as cfg


# =========================================================
# 베지어 곡선 유틸리티
# =========================================================

def bezier_point(t: float, p0: Tuple[float, float], p1: Tuple[float, float],
                 p2: Tuple[float, float], p3: Tuple[float, float]) -> Tuple[float, float]:
    """3차 베지어 곡선 상의 점 계산"""
    u = 1 - t
    tt = t * t
    uu = u * u
    uuu = uu * u
    ttt = tt * t

    x = uuu * p0[0] + 3 * uu * t * p1[0] + 3 * u * tt * p2[0] + ttt * p3[0]
    y = uuu * p0[1] + 3 * uu * t * p1[1] + 3 * u * tt * p2[1] + ttt * p3[1]

    return (x, y)


def generate_entry_path(entry_type: str, target_pos: Tuple[float, float]) -> List[Tuple[float, float]]:
    """진입 경로 생성 (베지어 곡선 기반)"""
    path_config = cfg.ENTRY_PATHS.get(entry_type, cfg.ENTRY_PATHS["top"])

    start = path_config["start"]
    ctrl1 = path_config["control1"]
    ctrl2 = path_config["control2"]
    end = target_pos

    # 50개의 점으로 경로 생성
    path = []
    for i in range(51):
        t = i / 50.0
        point = bezier_point(t, start, ctrl1, ctrl2, end)
        path.append(point)

    return path


# =========================================================
# FormationEnemy 클래스
# =========================================================

class FormationEnemy:
    """
    갈라그 스타일 포메이션 적

    상태:
    - ENTERING: 곡선을 따라 화면 진입 중
    - IN_FORMATION: 포메이션 위치에서 대기
    - DIVING: 플레이어를 향해 다이브 공격 중
    - RETURNING: 화면 상단으로 복귀 후 포메이션으로 돌아가는 중
    """

    # 상태 상수
    ENTERING = 0
    IN_FORMATION = 1
    DIVING = 2
    RETURNING = 3

    # 클래스 레벨 이미지 캐시
    _images: Dict[str, pygame.Surface] = {}
    _images_loaded = False
    _cached_sizes: Dict[str, Tuple[int, int]] = {}  # 크기 캐시

    @classmethod
    def reset_image_cache(cls):
        """이미지 캐시 강제 리셋"""
        cls._images.clear()
        cls._cached_sizes.clear()
        cls._images_loaded = False
        print("INFO: FormationEnemy image cache reset")

    @classmethod
    def load_images(cls):
        """적 이미지 로드 (크기 변경 시 리로드)"""
        # 크기 변경 감지
        sizes_changed = False
        for enemy_type, config in cfg.ENEMY_TYPES.items():
            new_size = config["size"]
            if cls._cached_sizes.get(enemy_type) != new_size:
                sizes_changed = True
                break

        if cls._images_loaded and not sizes_changed:
            return

        # 크기 변경 시 캐시 클리어
        if sizes_changed:
            cls._images.clear()
            cls._cached_sizes.clear()
            print("INFO: Enemy image cache cleared (size changed)")

        for enemy_type, config in cfg.ENEMY_TYPES.items():
            image_path = cfg.ENEMY_IMAGE_DIR / config["image"]
            size = config["size"]
            try:
                if image_path.exists():
                    img = pygame.image.load(str(image_path)).convert_alpha()
                    img = pygame.transform.scale(img, size)
                    cls._images[enemy_type] = img
                    cls._cached_sizes[enemy_type] = size  # 크기 캐시 저장
                    print(f"INFO: Loaded enemy image: {image_path} size={size}")
                else:
                    print(f"WARNING: Enemy image not found: {image_path}")
            except Exception as e:
                print(f"ERROR: Failed to load enemy image {image_path}: {e}")

        cls._images_loaded = True

    def __init__(self, enemy_type: str, formation_row: int, formation_col: int,
                 entry_type: str = "top", spawn_delay: float = 0.0,
                 screen_size: Tuple[int, int] = None):
        """
        Args:
            enemy_type: "drone", "fighter", "boss"
            formation_row: 포메이션 행 (0부터 시작)
            formation_col: 포메이션 열 (0부터 시작)
            entry_type: "left", "right", "top"
            spawn_delay: 스폰 지연 시간 (초)
            screen_size: 실제 화면 크기 (width, height)
        """
        self.type = enemy_type
        self.config = cfg.ENEMY_TYPES[enemy_type]

        # 실제 화면 크기 저장
        if screen_size:
            self.screen_width = screen_size[0]
            self.screen_height = screen_size[1]
        else:
            self.screen_width = cfg.SCREEN_WIDTH
            self.screen_height = cfg.SCREEN_HEIGHT

        # 상태
        self.state = FormationEnemy.ENTERING
        self.spawn_delay = spawn_delay
        self.waiting_to_spawn = spawn_delay > 0
        self.spawn_timer = 0.0

        # 포메이션 위치 계산 (화면 크기 기반)
        self.formation_row = formation_row
        self.formation_col = formation_col
        self.formation_pos = self._calculate_formation_pos()

        # 진입 경로 (화면 크기 기반)
        self.entry_path = self._generate_entry_path(entry_type)
        self.path_index = 0

        # 현재 위치 (스폰 대기 중에는 화면 밖)
        if self.waiting_to_spawn:
            self.pos = pygame.math.Vector2(-1000, -1000)
        else:
            self.pos = pygame.math.Vector2(self.entry_path[0])

        # 스탯
        self.max_hp = self.config["hp"]
        self.hp = self.max_hp
        self.score = self.config["score"]
        self.dive_score = self.config["dive_score"]
        self.size = self.config["size"]
        self.is_alive = True

        # 이동
        self.entry_speed = self.config["entry_speed"]
        self.dive_speed = self.config["dive_speed"]

        # 발사
        self.fire_rate = self.config["fire_rate"]
        self.bullet_speed = self.config["bullet_speed"]
        self.bullet_damage = self.config["bullet_damage"]
        self.last_fire_time = 0.0

        # 포메이션 흔들림
        self.sway_offset = random.uniform(0, math.pi * 2)  # 랜덤 위상
        self.sway_timer = 0.0

        # 다이브 관련
        self.dive_target = None
        self.zigzag_timer = 0.0
        self.is_diving = False
        self.swoop_start_x = 0.0
        self.swoop_progress = 0.0

        # 이미지 로드 (인스턴스별 크기 적용)
        self.image = self._load_scaled_image()

        # 회전 각도 (진행 방향)
        self.angle = 0.0

    def _load_scaled_image(self) -> pygame.Surface:
        """적 이미지 로드 및 현재 설정 크기로 스케일링"""
        image_path = cfg.ENEMY_IMAGE_DIR / self.config["image"]
        try:
            if image_path.exists():
                img = pygame.image.load(str(image_path)).convert_alpha()
                img = pygame.transform.scale(img, self.size)
                return img
            else:
                print(f"WARNING: Enemy image not found: {image_path}")
                return None
        except Exception as e:
            print(f"ERROR: Failed to load enemy image {image_path}: {e}")
            return None

    def _calculate_formation_pos(self) -> Tuple[float, float]:
        """포메이션 내 목표 위치 계산 (화면 크기 기반, 갈라그 스타일)"""
        cols = cfg.FORMATION["cols"]
        row_spacing = cfg.FORMATION["row_spacing"]

        # 포메이션 너비 (화면의 60%)
        formation_width_ratio = cfg.FORMATION.get("formation_width_ratio", 0.6)
        formation_width = self.screen_width * formation_width_ratio
        col_spacing = formation_width / (cols - 1) if cols > 1 else 0

        # 화면 중앙 정렬
        start_x = (self.screen_width - formation_width) / 2

        # Y 위치 (화면 상단 비율 기반)
        start_y_ratio = cfg.FORMATION.get("start_y_ratio", 0.08)
        start_y = self.screen_height * start_y_ratio

        x = start_x + self.formation_col * col_spacing
        y = start_y + self.formation_row * row_spacing
        return (x, y)

    def _generate_entry_path(self, entry_type: str) -> List[Tuple[float, float]]:
        """진입 경로 생성 (화면 크기 기반)"""
        target_pos = self.formation_pos
        sw = self.screen_width
        sh = self.screen_height

        # 진입 경로 정의
        if entry_type == "left":
            start = (-100, 300)
            ctrl1 = (sw * 0.2, 100)
            ctrl2 = (sw * 0.3, 200)
        elif entry_type == "right":
            start = (sw + 100, 300)
            ctrl1 = (sw * 0.8, 100)
            ctrl2 = (sw * 0.7, 200)
        else:  # top
            start = (sw // 2, -100)
            ctrl1 = (sw // 2 + 150, 150)
            ctrl2 = (sw // 2 - 150, 250)

        # 베지어 곡선으로 경로 생성
        path = []
        for i in range(51):
            t = i / 50.0
            point = bezier_point(t, start, ctrl1, ctrl2, target_pos)
            path.append(point)

        return path

    def update(self, dt: float, current_time: float, player_pos: pygame.math.Vector2,
               bullets: list) -> Optional[int]:
        """
        적 상태 업데이트

        Returns:
            점수 (죽었을 때) 또는 None
        """
        if not self.is_alive:
            return None

        # 스폰 대기 처리
        if self.waiting_to_spawn:
            self.spawn_timer += dt
            if self.spawn_timer >= self.spawn_delay:
                self.waiting_to_spawn = False
                self.pos = pygame.math.Vector2(self.entry_path[0])
            else:
                return None

        # 상태별 업데이트
        if self.state == FormationEnemy.ENTERING:
            self._update_entering(dt)
        elif self.state == FormationEnemy.IN_FORMATION:
            self._update_formation(dt, current_time, player_pos, bullets)
        elif self.state == FormationEnemy.DIVING:
            self._update_diving(dt, current_time, player_pos, bullets)
        elif self.state == FormationEnemy.RETURNING:
            self._update_returning(dt)

        return None

    def _update_entering(self, dt: float):
        """진입 경로 따라 이동"""
        if self.path_index >= len(self.entry_path) - 1:
            # 포메이션 도착
            self.state = FormationEnemy.IN_FORMATION
            self.pos = pygame.math.Vector2(self.formation_pos)
            return

        # 다음 목표점으로 이동
        target = pygame.math.Vector2(self.entry_path[self.path_index + 1])
        direction = target - self.pos
        distance = direction.length()

        if distance > 0:
            direction = direction.normalize()
            # 진행 방향으로 회전
            self.angle = math.degrees(math.atan2(-direction.x, -direction.y))

        move_distance = self.entry_speed * dt

        if move_distance >= distance:
            self.pos = target
            self.path_index += 1
        else:
            self.pos += direction * move_distance

    def _update_formation(self, dt: float, current_time: float,
                          player_pos: pygame.math.Vector2, bullets: list):
        """포메이션 내 대기 (좌우 흔들림)"""
        self.sway_timer += dt

        # 좌우 흔들림 적용
        sway = math.sin(self.sway_timer * cfg.FORMATION["sway_speed"] + self.sway_offset)
        sway_x = sway * cfg.FORMATION["sway_amplitude"]

        self.pos.x = self.formation_pos[0] + sway_x
        self.pos.y = self.formation_pos[1]

        # 각도 리셋 (아래를 향함)
        self.angle = 0

        # 발사 (확률 기반)
        if current_time - self.last_fire_time >= self.fire_rate:
            if random.random() < 0.3:  # 30% 확률로 발사
                self._fire_bullet(player_pos, bullets)
                self.last_fire_time = current_time

    def _update_diving(self, dt: float, current_time: float,
                       player_pos: pygame.math.Vector2, bullets: list):
        """다이브 공격 실행 (갈라그 스타일)"""
        self.is_diving = True

        # 화면 하단 도달 시 즉시 포메이션으로 복귀 (먼저 체크!)
        # 화면 높이의 80% 이상 내려가면 즉시 복귀
        dive_limit_y = self.screen_height * 0.75
        if self.pos.y >= dive_limit_y:
            # 즉시 포메이션 위치로 순간이동
            self.pos.x = self.formation_pos[0]
            self.pos.y = self.formation_pos[1]
            self.state = FormationEnemy.IN_FORMATION
            self.is_diving = False
            self.dive_target = None
            self.zigzag_timer = 0.0
            self.swoop_progress = 0.0
            self.angle = 0  # 각도 리셋
            return  # 복귀 후 즉시 종료

        dive_pattern = self.config.get("dive_pattern", "straight")

        if dive_pattern == "straight":
            self._dive_straight(dt, player_pos)
        elif dive_pattern == "zigzag":
            self._dive_zigzag(dt, player_pos)
        elif dive_pattern == "swoop":
            self._dive_swoop(dt, player_pos)
        else:
            self._dive_straight(dt, player_pos)

        # 다이브 중 발사 (설정에 따라)
        if cfg.DIVE_SETTINGS.get("fire_during_dive", True):
            fire_mult = cfg.DIVE_SETTINGS.get("dive_fire_rate_mult", 0.5)
            if current_time - self.last_fire_time >= self.fire_rate * fire_mult:
                self._fire_bullet(player_pos, bullets)
                self.last_fire_time = current_time

    def _dive_straight(self, dt: float, player_pos: pygame.math.Vector2):
        """직선 다이브 (드론)"""
        if self.dive_target is None:
            self.dive_target = player_pos.copy()

        direction = self.dive_target - self.pos
        if direction.length() > 0:
            direction = direction.normalize()
            self.angle = math.degrees(math.atan2(-direction.x, -direction.y))

        self.pos += direction * self.dive_speed * dt

    def _dive_zigzag(self, dt: float, player_pos: pygame.math.Vector2):
        """지그재그 다이브 (전투기)"""
        self.zigzag_timer += dt

        # 지그재그 오프셋
        zigzag_config = self.config.get("zigzag_amplitude", 80)
        zigzag_freq = self.config.get("zigzag_frequency", 5)
        offset = math.sin(self.zigzag_timer * zigzag_freq) * zigzag_config

        # 목표 위치 (플레이어 + 오프셋)
        target = pygame.math.Vector2(player_pos.x + offset, player_pos.y)
        direction = target - self.pos

        if direction.length() > 0:
            direction = direction.normalize()
            self.angle = math.degrees(math.atan2(-direction.x, -direction.y))

        self.pos += direction * self.dive_speed * dt

    def _dive_boss(self, dt: float, player_pos: pygame.math.Vector2):
        """보스 다이브 (정밀 추적) - 레거시"""
        self._dive_swoop(dt, player_pos)

    def _dive_swoop(self, dt: float, player_pos: pygame.math.Vector2):
        """곡선 다이브 (보스) - 갈라그 스타일"""
        # 다이브 시작점 저장
        if self.dive_target is None:
            self.dive_target = player_pos.copy()
            self.swoop_start_x = self.pos.x
            self.swoop_progress = 0.0

        self.swoop_progress += dt * 0.8  # 다이브 진행도

        # 곡선 경로: 시작점 → 플레이어 방향으로 휘어지며 아래로
        # S자 곡선으로 내려오기
        curve_x = math.sin(self.swoop_progress * math.pi) * 100
        if self.swoop_start_x > self.screen_width / 2:
            curve_x = -curve_x  # 오른쪽에서 시작하면 왼쪽으로 휘기

        target_x = self.dive_target.x + curve_x
        self.pos.x += (target_x - self.pos.x) * 2 * dt
        self.pos.y += self.dive_speed * dt

        # 방향에 따른 회전
        direction = pygame.math.Vector2(target_x - self.pos.x, self.dive_speed)
        if direction.length() > 0:
            direction = direction.normalize()
            self.angle = math.degrees(math.atan2(-direction.x, -direction.y))

    def _update_returning(self, dt: float):
        """포메이션으로 복귀"""
        # 포메이션 위치로 이동
        target = pygame.math.Vector2(self.formation_pos)
        direction = target - self.pos
        distance = direction.length()

        if distance < 5:
            self.pos = target
            self.state = FormationEnemy.IN_FORMATION
            return

        direction = direction.normalize()
        self.angle = math.degrees(math.atan2(-direction.x, -direction.y))

        move_speed = self.entry_speed * 1.5  # 복귀는 빠르게
        self.pos += direction * move_speed * dt

    def _fire_bullet(self, player_pos: pygame.math.Vector2, bullets: list):
        """플레이어를 향해 총알 발사"""
        direction = player_pos - self.pos
        if direction.length() > 0:
            direction = direction.normalize()

        bullet = {
            "pos": self.pos.copy(),
            "vel": direction * self.bullet_speed,
            "damage": self.bullet_damage,
            "is_enemy_bullet": True,
            "size": 8,
            "color": (255, 100, 100)
        }
        bullets.append(bullet)

    def start_dive(self, player_pos: pygame.math.Vector2):
        """다이브 공격 시작"""
        if self.state == FormationEnemy.IN_FORMATION:
            self.state = FormationEnemy.DIVING
            self.dive_target = player_pos.copy()
            self.zigzag_timer = 0.0
            self.is_diving = True

    def take_damage(self, damage: float) -> int:
        """
        데미지 받기

        Returns:
            획득 점수 (죽었을 때), 아니면 0
        """
        if not self.is_alive:
            return 0

        self.hp -= damage
        if self.hp <= 0:
            self.hp = 0
            self.is_alive = False
            # 다이브 중이면 2배 점수
            if self.is_diving:
                return self.dive_score
            return self.score
        return 0

    def get_rect(self) -> pygame.Rect:
        """충돌 판정용 사각형 반환"""
        return pygame.Rect(
            self.pos.x - self.size[0] // 2,
            self.pos.y - self.size[1] // 2,
            self.size[0],
            self.size[1]
        )

    def draw(self, screen: pygame.Surface):
        """적 그리기"""
        if not self.is_alive or self.waiting_to_spawn:
            return

        screen_x = int(self.pos.x)
        screen_y = int(self.pos.y)

        if self.image:
            # 회전 적용
            rotated = pygame.transform.rotate(self.image, self.angle)
            rect = rotated.get_rect(center=(screen_x, screen_y))
            screen.blit(rotated, rect)
        else:
            # 폴백: 색상으로 구분
            colors = {
                "drone": (100, 100, 255),
                "fighter": (100, 255, 100),
                "boss": (255, 100, 100)
            }
            color = colors.get(self.type, (200, 200, 200))
            pygame.draw.circle(screen, color, (screen_x, screen_y), self.size[0] // 2)

        # HP 바 (다이브 중이거나 데미지 받았을 때만)
        if self.hp < self.max_hp or self.is_diving:
            bar_width = self.size[0]
            bar_height = 4
            bar_x = screen_x - bar_width // 2
            bar_y = screen_y - self.size[1] // 2 - 8

            # 배경
            pygame.draw.rect(screen, (60, 0, 0), (bar_x, bar_y, bar_width, bar_height))
            # HP
            hp_ratio = max(0, self.hp / self.max_hp)
            pygame.draw.rect(screen, (0, 255, 0), (bar_x, bar_y, int(bar_width * hp_ratio), bar_height))


# =========================================================
# WaveManager 클래스
# =========================================================

class WaveManager:
    """
    웨이브 스폰 및 관리

    각 웨이브는 드론, 전투기, 보스 수가 정해져 있으며
    순차적으로 스폰됨
    """

    def __init__(self, screen_size: Tuple[int, int] = None):
        self.current_wave = 0
        self.enemies: List[FormationEnemy] = []
        self.wave_active = False
        self.wave_complete = False
        self.all_spawned = False
        self.formation_complete = False

        # 실제 화면 크기 저장
        if screen_size:
            self.screen_width = screen_size[0]
            self.screen_height = screen_size[1]
        else:
            self.screen_width = cfg.SCREEN_WIDTH
            self.screen_height = cfg.SCREEN_HEIGHT

        # 다이브 관리
        self.dive_timer = 0.0
        self.initial_dive_delay = cfg.DIVE_SETTINGS["initial_delay"]
        self.dive_interval = cfg.DIVE_SETTINGS["dive_interval"]
        self.max_divers = cfg.DIVE_SETTINGS["max_divers"]
        self.current_divers = 0
        self.dive_started = False

    def start_wave(self, wave_num: int):
        """웨이브 시작"""
        if wave_num > cfg.TOTAL_WAVES:
            print(f"INFO: All waves completed!")
            return False

        self.current_wave = wave_num
        wave_config = cfg.WAVES.get(wave_num)

        if not wave_config:
            print(f"WARNING: Wave {wave_num} config not found")
            return False

        print(f"INFO: Starting {wave_config['name']}")

        self.enemies = []
        self.wave_active = True
        self.wave_complete = False
        self.all_spawned = False
        self.formation_complete = False
        self.dive_started = False
        self.dive_timer = 0.0
        self.current_divers = 0

        # 적 스폰 큐 생성
        spawn_queue = self._create_spawn_queue(wave_config)

        # FormationEnemy 인스턴스 생성 (화면 크기 전달)
        for spawn_info in spawn_queue:
            enemy = FormationEnemy(
                enemy_type=spawn_info["type"],
                formation_row=spawn_info["row"],
                formation_col=spawn_info["col"],
                entry_type=spawn_info["entry"],
                spawn_delay=spawn_info["delay"],
                screen_size=(self.screen_width, self.screen_height)
            )
            self.enemies.append(enemy)

        self.all_spawned = True
        return True

    def _create_spawn_queue(self, wave_config: dict) -> List[dict]:
        """스폰 큐 생성"""
        spawn_queue = []
        delay = 0.0
        cols = cfg.FORMATION["cols"]  # 동적으로 열 수 가져오기

        # 보스 스폰 (최상단 행 0)
        boss_count = wave_config.get("boss", 0)
        for i in range(boss_count):
            col = (cols // 2 - boss_count // 2) + i  # 중앙 정렬
            spawn_queue.append({
                "type": "boss",
                "row": 0,
                "col": col,
                "entry": "top",
                "delay": delay
            })
            delay += cfg.SPAWN_INTERVAL * 2  # 보스는 간격 2배

        # 전투기 스폰 (행 1, 2)
        fighter_count = wave_config.get("fighter", 0)
        for i in range(fighter_count):
            row = 1 + (i // cols)
            col = i % cols
            entry = "left" if col < cols // 2 else "right"
            spawn_queue.append({
                "type": "fighter",
                "row": row,
                "col": col,
                "entry": entry,
                "delay": delay
            })
            delay += cfg.SPAWN_INTERVAL

        # 드론 스폰 (행 3, 4)
        drone_count = wave_config.get("drone", 0)
        for i in range(drone_count):
            row = 3 + (i // cols)
            col = i % cols
            entry = "left" if col < cols // 2 else "right"
            spawn_queue.append({
                "type": "drone",
                "row": row,
                "col": col,
                "entry": entry,
                "delay": delay
            })
            delay += cfg.SPAWN_INTERVAL

        return spawn_queue

    def update(self, dt: float, current_time: float, player_pos: pygame.math.Vector2,
               bullets: list) -> Tuple[int, bool]:
        """
        웨이브 업데이트

        Returns:
            (획득 점수 합계, 웨이브 완료 여부)
        """
        if not self.wave_active:
            return 0, False

        total_score = 0

        # 모든 적 업데이트
        for enemy in self.enemies:
            score = enemy.update(dt, current_time, player_pos, bullets)
            if score:
                total_score += score

        # 죽은 적 제거 및 다이버 카운트 업데이트
        self.current_divers = sum(1 for e in self.enemies if e.is_alive and e.state == FormationEnemy.DIVING)

        # 포메이션 완성 체크
        if not self.formation_complete:
            in_formation = sum(1 for e in self.enemies if e.is_alive and
                              e.state == FormationEnemy.IN_FORMATION)
            alive_count = sum(1 for e in self.enemies if e.is_alive)

            if alive_count > 0 and in_formation == alive_count:
                self.formation_complete = True
                print("INFO: Formation complete!")

        # 다이브 공격 시작
        if self.formation_complete:
            self.dive_timer += dt

            if not self.dive_started and self.dive_timer >= self.initial_dive_delay:
                self.dive_started = True
                self.dive_timer = 0.0

            if self.dive_started and self.dive_timer >= self.dive_interval:
                self._trigger_dive(player_pos)
                self.dive_timer = 0.0

        # 웨이브 완료 체크
        alive_enemies = [e for e in self.enemies if e.is_alive]
        if len(alive_enemies) == 0:
            self.wave_complete = True
            self.wave_active = False
            print(f"INFO: Wave {self.current_wave} cleared!")

        return total_score, self.wave_complete

    def _trigger_dive(self, player_pos: pygame.math.Vector2):
        """다이브 공격 트리거"""
        if self.current_divers >= self.max_divers:
            return

        # 포메이션에 있는 적 중 랜덤 선택
        formation_enemies = [e for e in self.enemies
                           if e.is_alive and e.state == FormationEnemy.IN_FORMATION]

        if not formation_enemies:
            return

        # 다이브할 적 수 결정
        dive_count = min(
            random.randint(1, 2),
            self.max_divers - self.current_divers,
            len(formation_enemies)
        )

        # 랜덤 선택하여 다이브 시작
        divers = random.sample(formation_enemies, dive_count)
        for enemy in divers:
            enemy.start_dive(player_pos)
            self.current_divers += 1

    def draw(self, screen: pygame.Surface):
        """모든 적 그리기"""
        for enemy in self.enemies:
            enemy.draw(screen)

    def get_wave_name(self) -> str:
        """현재 웨이브 이름 반환"""
        wave_config = cfg.WAVES.get(self.current_wave)
        if wave_config:
            return wave_config.get("name", f"WAVE {self.current_wave}")
        return f"WAVE {self.current_wave}"

    def get_enemies_alive(self) -> int:
        """살아있는 적 수 반환"""
        return sum(1 for e in self.enemies if e.is_alive)

    def get_all_enemy_rects(self) -> List[Tuple[FormationEnemy, pygame.Rect]]:
        """모든 살아있는 적의 (적 객체, Rect) 튜플 리스트 반환"""
        return [(e, e.get_rect()) for e in self.enemies if e.is_alive and not e.waiting_to_spawn]


# =========================================================
# 레거시 호환용 클래스 (빈 구현)
# =========================================================

class TileMap:
    """레거시 호환용 빈 타일맵"""
    def __init__(self, *args, screen_size=None, **kwargs):
        # screen_size가 제공되면 사용, 아니면 기본값 (실제 사용되지 않음)
        if screen_size:
            sw, sh = screen_size
        else:
            sw, sh = 1920, 1080  # 폴백 (레거시 호환)
        self.player_start_pos = (sw // 2, sh - 120)
        self.tower_positions = []
        self.guard_spawns = []
        self.patrol_spawns = []

    def is_walkable(self, x, y):
        return True

    def is_safe_zone(self, x, y):
        return False

    def draw(self, screen, camera_offset=(0, 0)):
        pass


class Tower:
    """레거시 호환용 빈 타워"""
    def __init__(self, *args, **kwargs):
        self.is_alive = False


class DestructibleWall:
    """레거시 호환용 빈 벽"""
    def __init__(self, *args, **kwargs):
        self.is_alive = False


class GuardEnemy:
    """레거시 호환용 빈 경비병"""
    def __init__(self, *args, **kwargs):
        self.is_alive = False


class PatrolEnemy:
    """레거시 호환용 빈 순찰병"""
    def __init__(self, *args, **kwargs):
        self.is_alive = False


print("INFO: siege_objects.py (Galaga Mode) loaded")
