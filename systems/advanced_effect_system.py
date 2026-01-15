"""
Advanced Effect System - 확장 가능한 동적 이펙트 시스템

특징:
1. 데이터 주도 (JSON) - 코드 수정 없이 이펙트 추가/수정
2. 스프라이트 시트 애니메이션 지원
3. 이펙트 조합(Composition) - 여러 효과를 하나로 결합
4. 핫 리로드 - 런타임에 이펙트 수정
5. 이징(Easing) 함수 내장
6. 트윈(Tween) 애니메이션 시스템
"""

import pygame
import json
import math
import random
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List, Callable
from dataclasses import dataclass, field
from enum import Enum


# ============================================================
# Easing Functions - 부드러운 애니메이션을 위한 이징 함수들
# ============================================================

class Easing:
    """이징 함수 모음 - 애니메이션의 속도 곡선 정의"""

    @staticmethod
    def linear(t: float) -> float:
        return t

    @staticmethod
    def ease_in_quad(t: float) -> float:
        return t * t

    @staticmethod
    def ease_out_quad(t: float) -> float:
        return 1 - (1 - t) * (1 - t)

    @staticmethod
    def ease_in_out_quad(t: float) -> float:
        return 2 * t * t if t < 0.5 else 1 - pow(-2 * t + 2, 2) / 2

    @staticmethod
    def ease_in_cubic(t: float) -> float:
        return t * t * t

    @staticmethod
    def ease_out_cubic(t: float) -> float:
        return 1 - pow(1 - t, 3)

    @staticmethod
    def ease_in_out_cubic(t: float) -> float:
        return 4 * t * t * t if t < 0.5 else 1 - pow(-2 * t + 2, 3) / 2

    @staticmethod
    def ease_in_elastic(t: float) -> float:
        if t == 0 or t == 1:
            return t
        return -pow(2, 10 * t - 10) * math.sin((t * 10 - 10.75) * (2 * math.pi / 3))

    @staticmethod
    def ease_out_elastic(t: float) -> float:
        if t == 0 or t == 1:
            return t
        return pow(2, -10 * t) * math.sin((t * 10 - 0.75) * (2 * math.pi / 3)) + 1

    @staticmethod
    def ease_out_bounce(t: float) -> float:
        n1, d1 = 7.5625, 2.75
        if t < 1 / d1:
            return n1 * t * t
        elif t < 2 / d1:
            t -= 1.5 / d1
            return n1 * t * t + 0.75
        elif t < 2.5 / d1:
            t -= 2.25 / d1
            return n1 * t * t + 0.9375
        else:
            t -= 2.625 / d1
            return n1 * t * t + 0.984375

    @staticmethod
    def ease_in_back(t: float) -> float:
        c1 = 1.70158
        c3 = c1 + 1
        return c3 * t * t * t - c1 * t * t

    @staticmethod
    def ease_out_back(t: float) -> float:
        c1 = 1.70158
        c3 = c1 + 1
        return 1 + c3 * pow(t - 1, 3) + c1 * pow(t - 1, 2)

    @classmethod
    def get(cls, name: str) -> Callable:
        """이름으로 이징 함수 가져오기"""
        easing_map = {
            "linear": cls.linear,
            "ease_in": cls.ease_in_quad,
            "ease_out": cls.ease_out_quad,
            "ease_in_out": cls.ease_in_out_quad,
            "ease_in_quad": cls.ease_in_quad,
            "ease_out_quad": cls.ease_out_quad,
            "ease_in_out_quad": cls.ease_in_out_quad,
            "ease_in_cubic": cls.ease_in_cubic,
            "ease_out_cubic": cls.ease_out_cubic,
            "ease_in_out_cubic": cls.ease_in_out_cubic,
            "ease_in_elastic": cls.ease_in_elastic,
            "ease_out_elastic": cls.ease_out_elastic,
            "ease_out_bounce": cls.ease_out_bounce,
            "ease_in_back": cls.ease_in_back,
            "ease_out_back": cls.ease_out_back,
        }
        return easing_map.get(name, cls.linear)


# ============================================================
# Sprite Sheet Animator - 스프라이트 시트 애니메이션
# ============================================================

@dataclass
class SpriteSheetConfig:
    """스프라이트 시트 설정"""
    image_path: str
    frame_width: int
    frame_height: int
    frame_count: int
    fps: float = 12.0
    loop: bool = True
    columns: int = 0  # 0이면 자동 계산
    rows: int = 1


class SpriteSheetAnimator:
    """스프라이트 시트 애니메이션 관리"""

    # 캐시: 로드된 스프라이트 시트 프레임들
    _cache: Dict[str, List[pygame.Surface]] = {}

    def __init__(self, config: SpriteSheetConfig):
        self.config = config
        self.frames: List[pygame.Surface] = []
        self.current_frame = 0
        self.elapsed_time = 0.0
        self.frame_duration = 1.0 / config.fps
        self.is_finished = False

        self._load_frames()

    def _load_frames(self):
        """스프라이트 시트에서 프레임 추출"""
        cache_key = f"{self.config.image_path}_{self.config.frame_width}_{self.config.frame_height}"

        if cache_key in SpriteSheetAnimator._cache:
            self.frames = SpriteSheetAnimator._cache[cache_key]
            return

        path = Path(self.config.image_path)
        if not path.exists():
            print(f"WARNING: Sprite sheet not found: {path}")
            return

        try:
            sheet = pygame.image.load(str(path)).convert_alpha()
            sheet_width, sheet_height = sheet.get_size()

            # 열/행 자동 계산
            columns = self.config.columns if self.config.columns > 0 else sheet_width // self.config.frame_width
            rows = self.config.rows if self.config.rows > 0 else sheet_height // self.config.frame_height

            # 프레임 추출
            for row in range(rows):
                for col in range(columns):
                    if len(self.frames) >= self.config.frame_count:
                        break

                    x = col * self.config.frame_width
                    y = row * self.config.frame_height

                    frame = pygame.Surface(
                        (self.config.frame_width, self.config.frame_height),
                        pygame.SRCALPHA
                    )
                    frame.blit(sheet, (0, 0), (x, y, self.config.frame_width, self.config.frame_height))
                    self.frames.append(frame)

            # 캐시에 저장
            SpriteSheetAnimator._cache[cache_key] = self.frames
            print(f"INFO: Loaded {len(self.frames)} frames from {path}")

        except Exception as e:
            print(f"ERROR: Failed to load sprite sheet: {e}")

    def update(self, dt: float):
        """애니메이션 프레임 업데이트"""
        if not self.frames or self.is_finished:
            return

        self.elapsed_time += dt

        if self.elapsed_time >= self.frame_duration:
            self.elapsed_time -= self.frame_duration
            self.current_frame += 1

            if self.current_frame >= len(self.frames):
                if self.config.loop:
                    self.current_frame = 0
                else:
                    self.current_frame = len(self.frames) - 1
                    self.is_finished = True

    def get_current_frame(self) -> Optional[pygame.Surface]:
        """현재 프레임 이미지 반환"""
        if self.frames and 0 <= self.current_frame < len(self.frames):
            return self.frames[self.current_frame]
        return None

    def reset(self):
        """애니메이션 리셋"""
        self.current_frame = 0
        self.elapsed_time = 0.0
        self.is_finished = False


# ============================================================
# Tween Animation - 값 보간 애니메이션
# ============================================================

@dataclass
class TweenConfig:
    """트윈 애니메이션 설정"""
    property_name: str  # 변경할 속성명 (scale, alpha, rotation, x, y 등)
    start_value: float
    end_value: float
    duration: float
    delay: float = 0.0
    easing: str = "linear"
    loop: bool = False
    yoyo: bool = False  # True면 왕복 애니메이션


class Tween:
    """트윈 애니메이션 - 값을 부드럽게 변경"""

    def __init__(self, config: TweenConfig):
        self.config = config
        self.elapsed = 0.0
        self.is_finished = False
        self.is_reversed = False
        self.easing_func = Easing.get(config.easing)
        self._current_value = config.start_value

    @property
    def current_value(self) -> float:
        return self._current_value

    def update(self, dt: float) -> float:
        """트윈 업데이트, 현재 값 반환"""
        if self.is_finished:
            return self._current_value

        self.elapsed += dt

        # 딜레이 처리
        if self.elapsed < self.config.delay:
            self._current_value = self.config.start_value
            return self._current_value

        # 진행 시간 (딜레이 제외)
        active_time = self.elapsed - self.config.delay

        # 진행률 계산
        progress = min(1.0, active_time / self.config.duration)

        # 이징 적용
        eased_progress = self.easing_func(progress)

        # 값 계산
        start = self.config.start_value
        end = self.config.end_value

        if self.is_reversed:
            start, end = end, start

        self._current_value = start + (end - start) * eased_progress

        # 완료 체크
        if progress >= 1.0:
            if self.config.yoyo:
                self.is_reversed = not self.is_reversed
                self.elapsed = self.config.delay
            elif self.config.loop:
                self.elapsed = self.config.delay
            else:
                self.is_finished = True

        return self._current_value

    def reset(self):
        """트윈 리셋"""
        self.elapsed = 0.0
        self.is_finished = False
        self.is_reversed = False
        self._current_value = self.config.start_value


# ============================================================
# Dynamic Effect - 데이터 주도 이펙트
# ============================================================

class DynamicEffect:
    """
    데이터 주도 동적 이펙트

    JSON 설정으로 정의되며, 다음 속성을 지원:
    - 위치, 스케일, 회전, 알파
    - 스프라이트 시트 애니메이션
    - 트윈 애니메이션 (여러 개 동시 적용)
    - 파티클 방출
    - 사운드 재생
    """

    def __init__(self, config: Dict[str, Any], pos: Tuple[float, float]):
        self.config = config
        self.pos = pygame.math.Vector2(pos)
        self.is_alive = True

        # 기본 속성
        self.scale = config.get("scale", 1.0)
        self.alpha = config.get("alpha", 255)
        self.rotation = config.get("rotation", 0.0)
        self.color_tint = tuple(config.get("color_tint", [255, 255, 255]))

        # 지속 시간
        self.duration = config.get("duration", 1.0)
        self.elapsed = 0.0
        self.delay = config.get("delay", 0.0)

        # 이미지/애니메이션
        self.image: Optional[pygame.Surface] = None
        self.animator: Optional[SpriteSheetAnimator] = None
        self._setup_visuals()

        # 트윈 애니메이션들
        self.tweens: List[Tween] = []
        self._setup_tweens()

        # 파티클 설정
        self.particle_emitter: Optional[Dict] = config.get("particles")
        self.particle_timer = 0.0
        self.spawned_particles: List[Dict] = []

    def _setup_visuals(self):
        """이미지 또는 스프라이트 시트 설정"""
        # 스프라이트 시트 애니메이션
        if "sprite_sheet" in self.config:
            sheet_config = self.config["sprite_sheet"]
            self.animator = SpriteSheetAnimator(SpriteSheetConfig(
                image_path=sheet_config["path"],
                frame_width=sheet_config.get("frame_width", 64),
                frame_height=sheet_config.get("frame_height", 64),
                frame_count=sheet_config.get("frame_count", 1),
                fps=sheet_config.get("fps", 12.0),
                loop=sheet_config.get("loop", False),
                columns=sheet_config.get("columns", 0),
                rows=sheet_config.get("rows", 1),
            ))

        # 단일 이미지
        elif "image" in self.config:
            image_path = Path(self.config["image"])
            if image_path.exists():
                try:
                    self.image = pygame.image.load(str(image_path)).convert_alpha()
                except Exception as e:
                    print(f"ERROR: Failed to load effect image: {e}")

    def _setup_tweens(self):
        """트윈 애니메이션 설정"""
        tweens_config = self.config.get("tweens", [])

        for tween_data in tweens_config:
            tween = Tween(TweenConfig(
                property_name=tween_data["property"],
                start_value=tween_data["from"],
                end_value=tween_data["to"],
                duration=tween_data.get("duration", self.duration),
                delay=tween_data.get("delay", 0.0),
                easing=tween_data.get("easing", "linear"),
                loop=tween_data.get("loop", False),
                yoyo=tween_data.get("yoyo", False),
            ))
            self.tweens.append(tween)

    def update(self, dt: float) -> List[Dict]:
        """
        이펙트 업데이트

        Returns:
            생성된 파티클 데이터 리스트
        """
        if not self.is_alive:
            return []

        self.elapsed += dt

        # 딜레이 처리
        if self.elapsed < self.delay:
            return []

        active_time = self.elapsed - self.delay

        # 지속 시간 체크
        if active_time >= self.duration:
            self.is_alive = False
            return []

        # 스프라이트 애니메이션 업데이트
        if self.animator:
            self.animator.update(dt)
            if self.animator.is_finished and not self.animator.config.loop:
                self.is_alive = False

        # 트윈 업데이트
        for tween in self.tweens:
            value = tween.update(dt)

            # 속성에 값 적용
            if tween.config.property_name == "scale":
                self.scale = value
            elif tween.config.property_name == "alpha":
                self.alpha = int(value)
            elif tween.config.property_name == "rotation":
                self.rotation = value
            elif tween.config.property_name == "x":
                self.pos.x = value
            elif tween.config.property_name == "y":
                self.pos.y = value

        # 파티클 방출
        new_particles = []
        if self.particle_emitter:
            new_particles = self._emit_particles(dt)

        return new_particles

    def _emit_particles(self, dt: float) -> List[Dict]:
        """파티클 방출"""
        particles = []

        emit_rate = self.particle_emitter.get("emit_rate", 10)  # 초당 파티클 수
        emit_interval = 1.0 / emit_rate

        self.particle_timer += dt

        while self.particle_timer >= emit_interval:
            self.particle_timer -= emit_interval

            # 파티클 데이터 생성
            particle_data = {
                "pos": (self.pos.x, self.pos.y),
                "velocity": self._random_velocity(),
                "color": self._random_color(),
                "size": random.uniform(
                    self.particle_emitter.get("min_size", 2),
                    self.particle_emitter.get("max_size", 6)
                ),
                "lifetime": random.uniform(
                    self.particle_emitter.get("min_lifetime", 0.3),
                    self.particle_emitter.get("max_lifetime", 1.0)
                ),
                "gravity": self.particle_emitter.get("gravity", True),
            }
            particles.append(particle_data)

        return particles

    def _random_velocity(self) -> Tuple[float, float]:
        """랜덤 속도 벡터 생성"""
        speed_min = self.particle_emitter.get("min_speed", 50)
        speed_max = self.particle_emitter.get("max_speed", 150)
        angle_min = self.particle_emitter.get("angle_min", 0)
        angle_max = self.particle_emitter.get("angle_max", 360)

        speed = random.uniform(speed_min, speed_max)
        angle = math.radians(random.uniform(angle_min, angle_max))

        return (math.cos(angle) * speed, math.sin(angle) * speed)

    def _random_color(self) -> Tuple[int, int, int]:
        """랜덤 색상 선택"""
        colors = self.particle_emitter.get("colors", [[255, 255, 255]])
        color = random.choice(colors)
        return tuple(color)

    def draw(self, screen: pygame.Surface):
        """이펙트 렌더링"""
        if not self.is_alive or self.elapsed < self.delay:
            return

        # 현재 이미지 가져오기
        current_image = None
        if self.animator:
            current_image = self.animator.get_current_frame()
        elif self.image:
            current_image = self.image

        if current_image is None:
            return

        # 스케일 적용
        if self.scale != 1.0:
            new_size = (
                int(current_image.get_width() * self.scale),
                int(current_image.get_height() * self.scale)
            )
            if new_size[0] > 0 and new_size[1] > 0:
                current_image = pygame.transform.scale(current_image, new_size)

        # 회전 적용
        if self.rotation != 0:
            current_image = pygame.transform.rotate(current_image, self.rotation)

        # 색상 틴트 적용
        if self.color_tint != (255, 255, 255):
            tint_surface = pygame.Surface(current_image.get_size(), pygame.SRCALPHA)
            tint_surface.fill((*self.color_tint, 255))
            current_image = current_image.copy()
            current_image.blit(tint_surface, (0, 0), special_flags=pygame.BLEND_RGB_MULT)

        # 알파 적용
        if self.alpha < 255:
            current_image.set_alpha(int(self.alpha))

        # 그리기
        rect = current_image.get_rect(center=(int(self.pos.x), int(self.pos.y)))
        screen.blit(current_image, rect)


# ============================================================
# Effect Composer - 이펙트 조합 시스템
# ============================================================

class CompositeEffect:
    """
    복합 이펙트 - 여러 이펙트를 하나로 조합

    예: 폭발 = 충격파 + 파티클 + 섬광 + 연기
    """

    def __init__(self, effects: List[DynamicEffect]):
        self.effects = effects
        self.is_alive = True

    def update(self, dt: float) -> List[Dict]:
        """모든 하위 이펙트 업데이트"""
        all_particles = []

        for effect in self.effects:
            particles = effect.update(dt)
            all_particles.extend(particles)

        # 모든 이펙트가 끝나면 종료
        self.is_alive = any(e.is_alive for e in self.effects)

        return all_particles

    def draw(self, screen: pygame.Surface):
        """모든 하위 이펙트 렌더링"""
        for effect in self.effects:
            effect.draw(screen)


# ============================================================
# Advanced Effect Manager - 확장된 이펙트 관리자
# ============================================================

class AdvancedEffectManager:
    """
    확장된 이펙트 관리 시스템

    특징:
    - JSON 기반 이펙트 정의
    - 스프라이트 시트 지원
    - 이펙트 조합 지원
    - 핫 리로드 기능
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._effects_config: Dict[str, Dict] = {}
        self._composite_config: Dict[str, List[str]] = {}
        self._active_effects: List[DynamicEffect] = []
        self._active_composites: List[CompositeEffect] = []
        self._particles: List[Dict] = []
        self._config_path: Optional[Path] = None
        self._last_modified: float = 0

        self._initialized = True
        self.load_config()

    def load_config(self, config_path: Optional[str] = None):
        """이펙트 설정 로드"""
        if config_path:
            self._config_path = Path(config_path)
        else:
            self._config_path = Path("assets/config/advanced_effects.json")

        if not self._config_path.exists():
            print(f"INFO: Advanced effects config not found at {self._config_path}, using defaults")
            self._load_defaults()
            return

        try:
            self._last_modified = self._config_path.stat().st_mtime

            with open(self._config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            self._effects_config = data.get("effects", {})
            self._composite_config = data.get("composites", {})

            print(f"INFO: AdvancedEffectManager loaded {len(self._effects_config)} effects, "
                  f"{len(self._composite_config)} composites")

        except Exception as e:
            print(f"ERROR: Failed to load advanced effects config: {e}")
            self._load_defaults()

    def _load_defaults(self):
        """기본 설정 로드"""
        self._effects_config = {
            "default_hit": {
                "image": "assets/images/vfx/combat/purse_ring_effect.png",
                "duration": 0.5,
                "tweens": [
                    {"property": "scale", "from": 0.1, "to": 1.0, "duration": 0.5, "easing": "ease_out"},
                    {"property": "alpha", "from": 255, "to": 0, "duration": 0.5, "easing": "ease_in"}
                ]
            }
        }
        self._composite_config = {}

    def hot_reload(self):
        """설정 파일이 변경되었으면 다시 로드 (핫 리로드)"""
        if self._config_path and self._config_path.exists():
            current_modified = self._config_path.stat().st_mtime
            if current_modified > self._last_modified:
                print("INFO: Hot reloading advanced effects config...")
                self.load_config()
                return True
        return False

    def create_effect(self, effect_name: str, pos: Tuple[float, float],
                      overrides: Optional[Dict] = None) -> Optional[DynamicEffect]:
        """
        이펙트 생성

        Args:
            effect_name: 이펙트 이름 (설정에 정의된 이름)
            pos: 이펙트 위치
            overrides: 설정 덮어쓰기 (선택적)

        Returns:
            생성된 이펙트 또는 None
        """
        if effect_name not in self._effects_config:
            print(f"WARNING: Effect '{effect_name}' not found")
            return None

        config = self._effects_config[effect_name].copy()

        # 덮어쓰기 적용
        if overrides:
            config.update(overrides)

        effect = DynamicEffect(config, pos)
        self._active_effects.append(effect)

        return effect

    def create_composite(self, composite_name: str, pos: Tuple[float, float]) -> Optional[CompositeEffect]:
        """
        복합 이펙트 생성

        Args:
            composite_name: 복합 이펙트 이름
            pos: 이펙트 위치

        Returns:
            생성된 복합 이펙트 또는 None
        """
        if composite_name not in self._composite_config:
            print(f"WARNING: Composite effect '{composite_name}' not found")
            return None

        effect_names = self._composite_config[composite_name]
        effects = []

        for name in effect_names:
            effect = self.create_effect(name, pos)
            if effect:
                effects.append(effect)

        if not effects:
            return None

        composite = CompositeEffect(effects)
        self._active_composites.append(composite)

        return composite

    def update(self, dt: float):
        """모든 활성 이펙트 업데이트"""
        # 핫 리로드 체크 (매 프레임은 비효율적이므로 주기적으로)
        # self.hot_reload()  # 필요시 활성화

        # 일반 이펙트 업데이트
        for effect in self._active_effects[:]:
            particles = effect.update(dt)
            self._particles.extend(particles)

            if not effect.is_alive:
                self._active_effects.remove(effect)

        # 복합 이펙트 업데이트
        for composite in self._active_composites[:]:
            particles = composite.update(dt)
            self._particles.extend(particles)

            if not composite.is_alive:
                self._active_composites.remove(composite)

        # 파티클 업데이트
        self._update_particles(dt)

    def _update_particles(self, dt: float):
        """파티클 업데이트"""
        for particle in self._particles[:]:
            particle["lifetime"] -= dt

            if particle["lifetime"] <= 0:
                self._particles.remove(particle)
                continue

            # 위치 업데이트
            vx, vy = particle["velocity"]
            pos_x, pos_y = particle["pos"]

            pos_x += vx * dt
            pos_y += vy * dt

            # 중력
            if particle.get("gravity", True):
                vy += 300 * dt
                particle["velocity"] = (vx * 0.98, vy)

            particle["pos"] = (pos_x, pos_y)

    def draw(self, screen: pygame.Surface):
        """모든 활성 이펙트 렌더링"""
        # 파티클 그리기
        for particle in self._particles:
            self._draw_particle(screen, particle)

        # 일반 이펙트 그리기
        for effect in self._active_effects:
            effect.draw(screen)

        # 복합 이펙트 그리기
        for composite in self._active_composites:
            composite.draw(screen)

    def _draw_particle(self, screen: pygame.Surface, particle: Dict):
        """파티클 하나 그리기"""
        pos = particle["pos"]
        color = particle["color"]
        size = particle["size"]

        # 수명에 따른 알파
        max_lifetime = particle.get("max_lifetime", 1.0)
        alpha = int(255 * (particle["lifetime"] / max_lifetime))
        alpha = max(0, min(255, alpha))

        # 서피스 생성 및 그리기
        surf = pygame.Surface((int(size * 2), int(size * 2)), pygame.SRCALPHA)
        pygame.draw.circle(surf, (*color, alpha), (int(size), int(size)), int(size))
        screen.blit(surf, (int(pos[0] - size), int(pos[1] - size)))

    def clear(self):
        """모든 이펙트 제거"""
        self._active_effects.clear()
        self._active_composites.clear()
        self._particles.clear()

    def list_effects(self) -> List[str]:
        """사용 가능한 이펙트 목록"""
        return list(self._effects_config.keys())

    def list_composites(self) -> List[str]:
        """사용 가능한 복합 이펙트 목록"""
        return list(self._composite_config.keys())


# 싱글톤 인스턴스 전역 접근 함수
def get_advanced_effect_manager() -> AdvancedEffectManager:
    """AdvancedEffectManager 싱글톤 인스턴스 가져오기"""
    return AdvancedEffectManager()


# ============================================================
# 테스트 코드
# ============================================================

if __name__ == "__main__":
    print("Advanced Effect System - Test")

    # 이징 테스트
    for t in [0.0, 0.25, 0.5, 0.75, 1.0]:
        print(f"  ease_out_bounce({t}) = {Easing.ease_out_bounce(t):.3f}")

    print("\nAvailable easing functions:", list(Easing.get.__code__.co_consts))
