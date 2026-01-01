"""
cutscenes/world_effects.py
World and space-related cutscene effects (star maps, planetary effects)
"""

import pygame
import math
import random
from pathlib import Path
from cutscenes.base import BaseCutsceneEffect, render_dialogue_box


class StarMapEffect(BaseCutsceneEffect):
    """
    Act 5 컷씬: 성간 항해 인터페이스 효과

    특징:
    - 별이 빛나는 우주 배경
    - 홀로그램 스타 맵 그리드
    - 이미지가 행성/기지 마커처럼 표시
    - 연결선으로 경로 표시
    """

    # 추가 페이즈 상수 (베이스 클래스 확장)
    PHASE_MARKERS = 10
    PHASE_ROUTE = 11

    def __init__(
        self,
        screen_size: tuple,
        marker_paths: list,
        marker_positions: dict = None,
        route_order: list = None,
        background_path: str = None,
        dialogue_after: list = None,
        sound_manager=None,
        special_effects: dict = None,
        scene_id: str = "starmap_scene",
    ):
        # 베이스 클래스 초기화
        super().__init__(
            screen_size,
            background_path,
            dialogue_after,
            sound_manager,
            special_effects,
            scene_id,
        )

        self.marker_paths = marker_paths
        self.marker_positions = marker_positions or {}
        self.route_order = route_order or []
        self.typing_speed = 25.0  # 오버라이드

        # 배경에 우주 틴트 오버레이 적용
        if background_path:
            self._load_background(background_path, overlay_alpha=150)

        # 별 파티클
        self.stars = []
        self._create_stars()

        # 마커들
        self.markers = []
        self._prepare_markers()

        # 경로
        self.route_progress = 0.0
        self.route_duration = 3.0
        self.route_points = []

        # 마커 애니메이션
        self.marker_animation_progress = 0.0

    def _create_stars(self):
        """배경 별 생성"""
        for _ in range(150):
            self.stars.append(
                {
                    "x": random.randint(0, self.screen_size[0]),
                    "y": random.randint(0, self.screen_size[1]),
                    "size": random.uniform(1, 3),
                    "brightness": random.uniform(0.3, 1.0),
                    "twinkle_speed": random.uniform(1, 4),
                    "twinkle_offset": random.uniform(0, math.pi * 2),
                }
            )

    # _load_background는 베이스 클래스에서 상속

    def _prepare_markers(self):
        """마커 준비"""
        screen_w, screen_h = self.screen_size
        marker_size = 80

        for path in self.marker_paths:
            marker_img = None
            try:
                marker_img = pygame.image.load(path).convert_alpha()
                marker_img = pygame.transform.smoothscale(
                    marker_img, (marker_size, marker_size)
                )
            except Exception as e:
                print(f"WARNING: Failed to load marker: {path} - {e}")
                marker_img = pygame.Surface((marker_size, marker_size), pygame.SRCALPHA)
                pygame.draw.circle(
                    marker_img,
                    (200, 150, 100),
                    (marker_size // 2, marker_size // 2),
                    marker_size // 2,
                )

            filename = Path(path).name
            pos_info = self.marker_positions.get(filename, {})
            rel_pos = pos_info.get("rel_pos", (0.5, 0.5))
            label = pos_info.get("label", "")
            color = pos_info.get("color", (255, 255, 255))

            self.markers.append(
                {
                    "image": marker_img,
                    "filename": filename,
                    "x": int(screen_w * rel_pos[0]),
                    "y": int(screen_h * rel_pos[1]),
                    "label": label,
                    "color": color,
                    "alpha": 0,
                    "scale": 0.5,
                    "pulse": 0.0,
                }
            )

        # 경로 포인트 생성
        for filename in self.route_order:
            for marker in self.markers:
                if marker["filename"] == filename:
                    self.route_points.append((marker["x"], marker["y"]))
                    break

    # set_fonts, _start_dialogue는 베이스 클래스에서 상속

    def _on_fadein_complete(self):
        """페이드인 완료 후 마커 등장 페이즈로 전환"""
        self.phase = self.PHASE_MARKERS
        self.phase_timer = 0.0

    def update(self, dt: float):
        """업데이트 - 마커/경로 고유 로직 추가"""
        if not self.is_alive:
            return

        self.phase_timer += dt

        # 마커 펄스 (항상 업데이트)
        for marker in self.markers:
            marker["pulse"] = 0.5 + 0.5 * math.sin(
                self.phase_timer * 2 + marker["x"] * 0.01
            )

        # 페이즈별 처리
        if self.phase == self.PHASE_FADEIN:
            if self._update_fadein(dt):
                self._on_fadein_complete()

        elif self.phase == self.PHASE_MARKERS:
            self._update_markers(dt)

        elif self.phase == self.PHASE_ROUTE:
            self._update_route(dt)

        elif self.phase == self.PHASE_DIALOGUE:
            if self._update_dialogue(dt):
                self._transition_to_fadeout()

        elif self.phase == self.PHASE_FADEOUT:
            if self._update_fadeout(dt):
                self._on_fadeout_complete()

    def _update_markers(self, dt: float):
        """마커 등장 애니메이션"""
        self.marker_animation_progress += dt * 1.5
        visible_count = int(self.marker_animation_progress)

        for i, marker in enumerate(self.markers):
            if i < visible_count:
                progress = min(1.0, self.marker_animation_progress - i)
                eased = 1.0 - (1.0 - progress) ** 3
                marker["alpha"] = int(255 * eased)
                marker["scale"] = 0.5 + 0.5 * eased

        if visible_count >= len(self.markers):
            self.waiting_for_click = True

    def _update_route(self, dt: float):
        """경로 애니메이션"""
        self.route_progress = min(1.0, self.phase_timer / self.route_duration)

        if self.route_progress >= 1.0:
            self._transition_to_dialogue()

    def _handle_click(self) -> bool:
        """클릭 처리 - 마커 페이즈 추가"""
        if self.phase == self.PHASE_MARKERS and self.waiting_for_click:
            self.phase = self.PHASE_ROUTE
            self.phase_timer = 0.0
            self.waiting_for_click = False
            return True

        # 대화 페이즈는 베이스 클래스 로직 사용
        return super()._handle_click()

    def render(self, screen: pygame.Surface):
        """렌더링"""
        # 배경 또는 우주 배경
        if self.background:
            bg_copy = self.background.copy()
            if self.fade_alpha < 255:
                bg_copy.set_alpha(int(self.fade_alpha))
            screen.blit(bg_copy, (0, 0))
        else:
            screen.fill((5, 5, 20))

        # 별
        self._render_stars(screen)

        # 그리드
        self._render_grid(screen)

        # 경로 (PHASE_ROUTE 이후)
        if self.phase >= self.PHASE_ROUTE:
            self._render_route(screen)

        # 마커들
        for marker in self.markers:
            self._render_marker(screen, marker)

        # 대사
        if self.phase == self.PHASE_DIALOGUE:
            self._render_dialogue(screen)

        # 안내
        if self.waiting_for_click and self.phase == self.PHASE_MARKERS:
            self._render_click_hint(screen, "클릭하여 항로 확인")

    def _render_stars(self, screen: pygame.Surface):
        """별 렌더링"""
        for star in self.stars:
            twinkle = 0.5 + 0.5 * math.sin(
                self.phase_timer * star["twinkle_speed"] + star["twinkle_offset"]
            )
            brightness = int(
                255 * star["brightness"] * twinkle * (self.fade_alpha / 255)
            )
            color = (brightness, brightness, int(brightness * 0.9))
            pygame.draw.circle(
                screen, color, (int(star["x"]), int(star["y"])), int(star["size"])
            )

    def _render_grid(self, screen: pygame.Surface):
        """홀로그램 그리드"""
        grid_surf = pygame.Surface(self.screen_size, pygame.SRCALPHA)
        grid_color = (100, 150, 255, 30)

        # 수평선
        for y in range(0, self.screen_size[1], 50):
            pygame.draw.line(grid_surf, grid_color, (0, y), (self.screen_size[0], y))

        # 수직선
        for x in range(0, self.screen_size[0], 50):
            pygame.draw.line(grid_surf, grid_color, (x, 0), (x, self.screen_size[1]))

        screen.blit(grid_surf, (0, 0))

    def _render_route(self, screen: pygame.Surface):
        """경로 렌더링"""
        if len(self.route_points) < 2:
            return

        # 전체 경로 길이 계산
        total_length = 0
        segments = []
        for i in range(len(self.route_points) - 1):
            p1, p2 = self.route_points[i], self.route_points[i + 1]
            length = math.sqrt((p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2)
            segments.append((p1, p2, length))
            total_length += length

        # 현재 진행 거리
        current_dist = total_length * self.route_progress
        drawn_dist = 0

        route_surf = pygame.Surface(self.screen_size, pygame.SRCALPHA)

        for p1, p2, length in segments:
            if drawn_dist + length <= current_dist:
                # 전체 세그먼트 그리기
                pygame.draw.line(route_surf, (255, 200, 100, 200), p1, p2, 3)
                drawn_dist += length
            elif drawn_dist < current_dist:
                # 부분 세그먼트
                ratio = (current_dist - drawn_dist) / length
                mid_x = p1[0] + (p2[0] - p1[0]) * ratio
                mid_y = p1[1] + (p2[1] - p1[1]) * ratio
                pygame.draw.line(
                    route_surf, (255, 200, 100, 200), p1, (mid_x, mid_y), 3
                )
                break

        screen.blit(route_surf, (0, 0))

    def _render_marker(self, screen: pygame.Surface, marker: dict):
        if marker["alpha"] <= 0:
            return

        img = marker["image"]

        # 스케일
        scaled_w = int(img.get_width() * marker["scale"])
        scaled_h = int(img.get_height() * marker["scale"])
        if scaled_w <= 0 or scaled_h <= 0:
            return
        scaled = pygame.transform.smoothscale(img, (scaled_w, scaled_h))

        # 글로우
        glow_size = int(scaled_w * 1.5)
        glow_surf = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
        glow_alpha = int(80 * marker["pulse"])
        pygame.draw.circle(
            glow_surf,
            (*marker["color"], glow_alpha),
            (glow_size // 2, glow_size // 2),
            glow_size // 2,
        )
        screen.blit(
            glow_surf, (marker["x"] - glow_size // 2, marker["y"] - glow_size // 2)
        )

        # 마커
        scaled.set_alpha(marker["alpha"])
        rect = scaled.get_rect(center=(marker["x"], marker["y"]))
        screen.blit(scaled, rect)

        # 라벨
        if marker["label"] and marker["alpha"] > 200 and "small" in self.fonts:
            label_surf = self.fonts["small"].render(
                marker["label"], True, marker["color"]
            )
            label_x = marker["x"] - label_surf.get_width() // 2
            label_y = marker["y"] + scaled_h // 2 + 10
            screen.blit(label_surf, (label_x, label_y))

    def _render_dialogue(self, screen: pygame.Surface):
        """대화창 렌더링 (초상화 포함)"""
        if not self.dialogue_after or self.current_dialogue_index >= len(
            self.dialogue_after
        ):
            return
        dialogue = self.dialogue_after[self.current_dialogue_index]
        speaker = dialogue.get("speaker", "")
        portrait = self._get_portrait(speaker) if speaker else None

        render_dialogue_box(
            screen,
            self.screen_size,
            self.fonts,
            dialogue,
            self.dialogue_text,
            self.typing_progress,
            self.waiting_for_click,
            box_color=(10, 20, 40, 220),
            border_color=(100, 150, 255),
            text_color=(220, 230, 255),
            box_height=180,
            has_portrait=(portrait is not None),
            portrait=portrait,
        )


# =========================================================
# 안드로메다 세계 효과 (사이버펑크 고대 도시)
# =========================================================
class AndromedaWorldEffect(BaseCutsceneEffect):
    """
    안드로메다 컷씬: 사이버펑크 고대 도시 효과

    특징:
    - 짙은 보라/검은색 하늘 (변화 없음)
    - 네온 회로가 새겨진 피라미드형 건물
    - 홀로그램 고대 문자
    - 제한적 색감 (네온 청록/보라/주황만)
    - 영원한 황혼 분위기
    """

    def __init__(
        self,
        screen_size: tuple,
        background_path: str = None,
        dialogue_after: list = None,
        sound_manager=None,
        special_effects: dict = None,
        scene_id: str = "andromeda_scene",
    ):
        super().__init__(
            screen_size,
            background_path,
            dialogue_after,
            sound_manager,
            special_effects,
            scene_id,
        )

        self.typing_speed = 25.0

        # 안드로메다 색상 팔레트 (제한적)
        self.neon_colors = [
            (0, 255, 255),  # 청록
            (200, 100, 255),  # 보라
            (255, 150, 50),  # 주황
        ]
        self.sky_color = (40, 20, 60)  # 짙은 보라/검은색

        # 피라미드 건물들
        self.buildings = []
        self._create_buildings()

        # 네온 회로 라인
        self.circuit_lines = []
        self._create_circuits()

        # 홀로그램 문자
        self.holo_chars = []
        self._create_hologram_chars()

        # 파티클
        self.particles = []
        self._create_particles()

        # 애니메이션 타이머
        self.glow_timer = 0.0

    def _create_buildings(self):
        """피라미드형 건물 생성"""
        screen_w, screen_h = self.screen_size
        for i in range(5):
            x = random.randint(50, screen_w - 50)
            width = random.randint(80, 150)
            height = random.randint(150, 300)
            color_idx = random.randint(0, len(self.neon_colors) - 1)
            self.buildings.append(
                {
                    "x": x,
                    "y": screen_h - height // 2,
                    "width": width,
                    "height": height,
                    "color": self.neon_colors[color_idx],
                    "glow_offset": random.uniform(0, math.pi * 2),
                }
            )

    def _create_circuits(self):
        """네온 회로 라인 생성"""
        screen_w, screen_h = self.screen_size
        for _ in range(15):
            start_x = random.randint(0, screen_w)
            start_y = random.randint(screen_h // 2, screen_h)
            length = random.randint(50, 150)
            horizontal = random.choice([True, False])
            color_idx = random.randint(0, len(self.neon_colors) - 1)
            self.circuit_lines.append(
                {
                    "start": (start_x, start_y),
                    "length": length,
                    "horizontal": horizontal,
                    "color": self.neon_colors[color_idx],
                    "pulse_offset": random.uniform(0, math.pi * 2),
                }
            )

    def _create_hologram_chars(self):
        """홀로그램 고대 문자 생성"""
        screen_w, screen_h = self.screen_size
        # 간단한 기호들로 고대 문자 표현
        symbols = ["◆", "◇", "○", "△", "▽", "□", "☆", "⬡", "⬢"]
        for _ in range(20):
            self.holo_chars.append(
                {
                    "x": random.randint(50, screen_w - 50),
                    "y": random.randint(50, screen_h - 200),
                    "char": random.choice(symbols),
                    "size": random.randint(15, 30),
                    "alpha": random.randint(50, 150),
                    "drift_speed": random.uniform(0.2, 0.5),
                    "drift_offset": random.uniform(0, math.pi * 2),
                }
            )

    def _create_particles(self):
        """네온 파티클 생성"""
        for _ in range(30):
            self.particles.append(
                {
                    "x": random.randint(0, self.screen_size[0]),
                    "y": random.randint(0, self.screen_size[1]),
                    "size": random.uniform(1, 3),
                    "color": random.choice(self.neon_colors),
                    "speed": random.uniform(10, 30),
                    "alpha": random.randint(100, 200),
                }
            )

    def update(self, dt: float):
        """업데이트"""
        if not self.is_alive:
            return

        self.phase_timer += dt
        self.glow_timer += dt

        # 파티클 이동
        for p in self.particles:
            p["y"] -= p["speed"] * dt
            if p["y"] < 0:
                p["y"] = self.screen_size[1]
                p["x"] = random.randint(0, self.screen_size[0])

        # 페이즈 처리
        if self.phase == self.PHASE_FADEIN:
            if self._update_fadein(dt):
                self._transition_to_dialogue()

        elif self.phase == self.PHASE_DIALOGUE:
            if self._update_dialogue(dt):
                self._transition_to_fadeout()

        elif self.phase == self.PHASE_FADEOUT:
            if self._update_fadeout(dt):
                self._on_fadeout_complete()

    def render(self, screen: pygame.Surface):
        """렌더링"""
        # 배경색 (영원한 황혼)
        screen.fill(self.sky_color)

        # 배경 이미지 (있으면)
        if self.background:
            bg_copy = self.background.copy()
            bg_copy.set_alpha(int(self.fade_alpha * 0.5))
            screen.blit(bg_copy, (0, 0))

        # 피라미드 건물
        self._render_buildings(screen)

        # 네온 회로
        self._render_circuits(screen)

        # 홀로그램 문자
        self._render_hologram(screen)

        # 파티클
        self._render_particles(screen)

        # 스캔라인 효과
        self._render_scanlines(screen)

        # 대사
        if self.phase == self.PHASE_DIALOGUE:
            self._render_dialogue(screen)

    def _render_buildings(self, screen: pygame.Surface):
        """피라미드 건물 렌더링"""
        for bld in self.buildings:
            # 피라미드 형태
            points = [
                (bld["x"], bld["y"]),  # 상단 중앙
                (bld["x"] - bld["width"] // 2, bld["y"] + bld["height"]),  # 좌하단
                (bld["x"] + bld["width"] // 2, bld["y"] + bld["height"]),  # 우하단
            ]

            # 글로우 효과
            glow = 0.5 + 0.5 * math.sin(self.glow_timer * 2 + bld["glow_offset"])
            color = tuple(int(c * glow) for c in bld["color"])

            # 외곽선
            pygame.draw.polygon(screen, color, points, 2)

            # 내부 회로 라인
            for i in range(3):
                y_offset = bld["height"] * (i + 1) // 4
                line_y = bld["y"] + y_offset
                half_width = (
                    bld["width"] * (bld["height"] - y_offset) // (2 * bld["height"])
                )
                pygame.draw.line(
                    screen,
                    (*color[:3], int(100 * glow)),
                    (bld["x"] - half_width, line_y),
                    (bld["x"] + half_width, line_y),
                    1,
                )

    def _render_circuits(self, screen: pygame.Surface):
        """네온 회로 렌더링"""
        circuit_surf = pygame.Surface(self.screen_size, pygame.SRCALPHA)
        for circuit in self.circuit_lines:
            pulse = 0.3 + 0.7 * math.sin(self.glow_timer * 3 + circuit["pulse_offset"])
            alpha = int(200 * pulse)
            color = (*circuit["color"], alpha)

            start = circuit["start"]
            if circuit["horizontal"]:
                end = (start[0] + circuit["length"], start[1])
            else:
                end = (start[0], start[1] - circuit["length"])

            pygame.draw.line(circuit_surf, color, start, end, 2)

        screen.blit(circuit_surf, (0, 0))

    def _render_hologram(self, screen: pygame.Surface):
        """홀로그램 문자 렌더링"""
        if "small" not in self.fonts:
            return

        holo_surf = pygame.Surface(self.screen_size, pygame.SRCALPHA)
        for char in self.holo_chars:
            # 부유 효과
            drift = (
                math.sin(self.glow_timer * char["drift_speed"] + char["drift_offset"])
                * 10
            )
            y = char["y"] + drift

            # 깜빡임
            flicker = 0.5 + 0.5 * math.sin(self.glow_timer * 5 + char["drift_offset"])
            alpha = int(char["alpha"] * flicker)

            color = (0, 255, 255, alpha)  # 청록색
            text = self.fonts["small"].render(char["char"], True, color[:3])
            text.set_alpha(alpha)
            holo_surf.blit(text, (char["x"], y))

        screen.blit(holo_surf, (0, 0))

    def _render_particles(self, screen: pygame.Surface):
        """파티클 렌더링"""
        for p in self.particles:
            alpha = int(p["alpha"] * (self.fade_alpha / 255))
            color = (*p["color"], alpha)
            pygame.draw.circle(
                screen, color, (int(p["x"]), int(p["y"])), int(p["size"])
            )

    def _render_scanlines(self, screen: pygame.Surface):
        """스캔라인 효과 (CRT 느낌)"""
        scanline_surf = pygame.Surface(self.screen_size, pygame.SRCALPHA)
        for y in range(0, self.screen_size[1], 4):
            pygame.draw.line(
                scanline_surf, (0, 0, 0, 30), (0, y), (self.screen_size[0], y)
            )
        screen.blit(scanline_surf, (0, 0))

    def _render_dialogue(self, screen: pygame.Surface):
        """대화창 렌더링"""
        if not self.dialogue_after or self.current_dialogue_index >= len(
            self.dialogue_after
        ):
            return
        dialogue = self.dialogue_after[self.current_dialogue_index]
        speaker = dialogue.get("speaker", "")
        portrait = self._get_portrait(speaker) if speaker else None

        render_dialogue_box(
            screen,
            self.screen_size,
            self.fonts,
            dialogue,
            self.dialogue_text,
            self.typing_progress,
            self.waiting_for_click,
            box_color=(20, 10, 40, 230),
            border_color=(0, 255, 255),
            text_color=(200, 230, 255),
            box_height=180,
            has_portrait=(portrait is not None),
            portrait=portrait,
        )


# =========================================================
# 두 세계 비교 효과 (화면 분할)
# =========================================================
class TwoWorldsEffect(BaseCutsceneEffect):
    """
    두 세계 비교 컷씬: 화면 분할 효과

    특징:
    - 화면 왼쪽: 안드로메다 (사이버펑크 고대 도시, 정적)
    - 화면 오른쪽: 지구 사계절 (다채색, 동적)
    - 점진적으로 오른쪽이 왼쪽을 덮는 애니메이션
    """

    PHASE_SPLIT = 10
    PHASE_MERGE = 11

    def __init__(
        self,
        screen_size: tuple,
        andromeda_bg: str = None,
        earth_bg: str = None,
        dialogue_after: list = None,
        sound_manager=None,
        special_effects: dict = None,
        scene_id: str = "two_worlds_scene",
    ):
        super().__init__(
            screen_size, None, dialogue_after, sound_manager, special_effects, scene_id
        )

        self.typing_speed = 25.0

        # 배경 이미지 로드
        self.andromeda_bg = None
        self.earth_bg = None

        if andromeda_bg:
            try:
                img = pygame.image.load(andromeda_bg).convert()
                self.andromeda_bg = pygame.transform.smoothscale(img, screen_size)
            except:
                pass

        if earth_bg:
            try:
                img = pygame.image.load(earth_bg).convert()
                self.earth_bg = pygame.transform.smoothscale(img, screen_size)
            except:
                pass

        # 분할선 위치 (0.0 ~ 1.0)
        self.split_position = 0.5
        self.target_split = 0.5
        self.merge_progress = 0.0
        self.merge_duration = 3.0

        # 꽃잎 파티클 (지구 쪽)
        self.petals = []
        self._create_petals()

        # 네온 파티클 (안드로메다 쪽)
        self.neon_particles = []
        self._create_neon_particles()

    def _create_petals(self):
        """벚꽃 꽃잎 생성"""
        for _ in range(30):
            self.petals.append(
                {
                    "x": random.randint(self.screen_size[0] // 2, self.screen_size[0]),
                    "y": random.randint(-50, self.screen_size[1]),
                    "size": random.randint(5, 12),
                    "speed_y": random.uniform(20, 50),
                    "speed_x": random.uniform(-20, 20),
                    "rotation": random.uniform(0, 360),
                    "rot_speed": random.uniform(-90, 90),
                    "alpha": random.randint(150, 255),
                }
            )

    def _create_neon_particles(self):
        """네온 파티클 생성"""
        for _ in range(20):
            self.neon_particles.append(
                {
                    "x": random.randint(0, self.screen_size[0] // 2),
                    "y": random.randint(0, self.screen_size[1]),
                    "size": random.uniform(1, 3),
                    "color": random.choice(
                        [(0, 255, 255), (200, 100, 255), (255, 150, 50)]
                    ),
                    "speed": random.uniform(10, 30),
                    "alpha": random.randint(100, 200),
                }
            )

    def _on_fadein_complete(self):
        """페이드인 완료 후 분할 화면 페이즈"""
        self.phase = self.PHASE_SPLIT
        self.phase_timer = 0.0

    def update(self, dt: float):
        """업데이트"""
        if not self.is_alive:
            return

        self.phase_timer += dt

        # 꽃잎 이동
        for petal in self.petals:
            petal["y"] += petal["speed_y"] * dt
            petal["x"] += petal["speed_x"] * dt
            petal["rotation"] += petal["rot_speed"] * dt
            if petal["y"] > self.screen_size[1]:
                petal["y"] = -20
                petal["x"] = random.randint(
                    int(self.screen_size[0] * self.split_position), self.screen_size[0]
                )

        # 네온 파티클 이동
        for p in self.neon_particles:
            p["y"] -= p["speed"] * dt
            if p["y"] < 0:
                p["y"] = self.screen_size[1]
                p["x"] = random.randint(
                    0, int(self.screen_size[0] * self.split_position)
                )

        # 페이즈 처리
        if self.phase == self.PHASE_FADEIN:
            if self._update_fadein(dt):
                self._on_fadein_complete()

        elif self.phase == self.PHASE_SPLIT:
            # 분할 화면 대기 (클릭으로 다음)
            self.waiting_for_click = True

        elif self.phase == self.PHASE_MERGE:
            # 지구가 안드로메다를 덮는 애니메이션
            self.merge_progress = min(1.0, self.phase_timer / self.merge_duration)
            self.split_position = 0.5 - 0.5 * self._ease_out_cubic(self.merge_progress)

            if self.merge_progress >= 1.0:
                self._transition_to_dialogue()

        elif self.phase == self.PHASE_DIALOGUE:
            if self._update_dialogue(dt):
                self._transition_to_fadeout()

        elif self.phase == self.PHASE_FADEOUT:
            if self._update_fadeout(dt):
                self._on_fadeout_complete()

    def _ease_out_cubic(self, t):
        return 1 - pow(1 - t, 3)

    def _handle_click(self) -> bool:
        """클릭 처리"""
        if self.phase == self.PHASE_SPLIT and self.waiting_for_click:
            self.phase = self.PHASE_MERGE
            self.phase_timer = 0.0
            self.waiting_for_click = False
            return True
        return super()._handle_click()

    def render(self, screen: pygame.Surface):
        """렌더링"""
        split_x = int(self.screen_size[0] * self.split_position)

        # 왼쪽: 안드로메다
        if self.andromeda_bg:
            screen.blit(self.andromeda_bg, (0, 0), (0, 0, split_x, self.screen_size[1]))
        else:
            pygame.draw.rect(screen, (40, 20, 60), (0, 0, split_x, self.screen_size[1]))

        # 오른쪽: 지구
        if self.earth_bg:
            screen.blit(
                self.earth_bg,
                (split_x, 0),
                (split_x, 0, self.screen_size[0] - split_x, self.screen_size[1]),
            )
        else:
            pygame.draw.rect(
                screen,
                (100, 150, 200),
                (split_x, 0, self.screen_size[0] - split_x, self.screen_size[1]),
            )

        # 네온 파티클 (안드로메다 쪽)
        for p in self.neon_particles:
            if p["x"] < split_x:
                alpha = int(p["alpha"] * (self.fade_alpha / 255))
                pygame.draw.circle(
                    screen,
                    (*p["color"], alpha),
                    (int(p["x"]), int(p["y"])),
                    int(p["size"]),
                )

        # 꽃잎 (지구 쪽)
        for petal in self.petals:
            if petal["x"] >= split_x:
                self._render_petal(screen, petal)

        # 분할선 (글로우 효과)
        glow_width = 10
        glow_surf = pygame.Surface(
            (glow_width * 2, self.screen_size[1]), pygame.SRCALPHA
        )
        for i in range(glow_width):
            alpha = int(150 * (1 - i / glow_width))
            pygame.draw.line(
                glow_surf,
                (255, 255, 255, alpha),
                (glow_width - i, 0),
                (glow_width - i, self.screen_size[1]),
            )
            pygame.draw.line(
                glow_surf,
                (255, 255, 255, alpha),
                (glow_width + i, 0),
                (glow_width + i, self.screen_size[1]),
            )
        screen.blit(glow_surf, (split_x - glow_width, 0))

        # 라벨
        if self.phase == self.PHASE_SPLIT and "small" in self.fonts:
            # 안드로메다 라벨
            label_a = self.fonts["small"].render("안드로메다", True, (0, 255, 255))
            screen.blit(label_a, (split_x // 2 - label_a.get_width() // 2, 30))

            # 지구 라벨
            label_e = self.fonts["small"].render("지구", True, (255, 200, 150))
            screen.blit(
                label_e,
                (
                    split_x
                    + (self.screen_size[0] - split_x) // 2
                    - label_e.get_width() // 2,
                    30,
                ),
            )

        # 안내
        if self.waiting_for_click and self.phase == self.PHASE_SPLIT:
            self._render_click_hint(screen, "클릭하여 계속")

        # 대사
        if self.phase == self.PHASE_DIALOGUE:
            self._render_dialogue(screen)

    def _render_petal(self, screen: pygame.Surface, petal: dict):
        """벚꽃 꽃잎 렌더링"""
        size = petal["size"]
        surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)

        # 꽃잎 모양 (타원)
        color = (255, 200, 220, petal["alpha"])
        pygame.draw.ellipse(surf, color, (0, size // 2, size * 2, size))

        # 회전
        rotated = pygame.transform.rotate(surf, petal["rotation"])
        rect = rotated.get_rect(center=(petal["x"], petal["y"]))
        screen.blit(rotated, rect)

    def _render_dialogue(self, screen: pygame.Surface):
        """대화창 렌더링"""
        if not self.dialogue_after or self.current_dialogue_index >= len(
            self.dialogue_after
        ):
            return
        dialogue = self.dialogue_after[self.current_dialogue_index]
        speaker = dialogue.get("speaker", "")
        portrait = self._get_portrait(speaker) if speaker else None

        render_dialogue_box(
            screen,
            self.screen_size,
            self.fonts,
            dialogue,
            self.dialogue_text,
            self.typing_progress,
            self.waiting_for_click,
            box_color=(20, 20, 30, 230),
            border_color=(200, 180, 255),
            text_color=(240, 240, 255),
            box_height=180,
            has_portrait=(portrait is not None),
            portrait=portrait,
        )


# =========================================================
# 계절 기억 효과 (빠른 계절 전환)
# =========================================================
