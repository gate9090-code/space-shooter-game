"""
cutscenes/communication_effects.py
Communication-related cutscene effects (holograms, radio waves, countdowns)
"""

import pygame
import math
import random
from pathlib import Path
from cutscenes.base import BaseCutsceneEffect, render_dialogue_box


class HologramMessageEffect(BaseCutsceneEffect):
    """
    아버지 홀로그램 메시지 컷씬 (Act 2)

    특징:
    - 벙커에서 발견된 홀로그램 장치
    - 깜빡이는 홀로그램 투영
    - 아버지의 녹화된 메시지
    - 스캔라인, 글리치 효과
    """

    PHASE_DEVICE_ACTIVATE = 10
    PHASE_HOLOGRAM_FLICKER = 11
    PHASE_MESSAGE_PLAY = 12

    def __init__(
        self,
        screen_size: tuple,
        father_image_path: str = None,
        dialogue_after: list = None,
        sound_manager=None,
        special_effects: dict = None,
        scene_id: str = "hologram_message_scene",
    ):
        super().__init__(
            screen_size, None, dialogue_after, sound_manager, special_effects, scene_id
        )

        self.typing_speed = 22.0

        # 아버지 홀로그램 이미지
        self.father_image = None
        self.hologram_size = (300, 400)
        self.hologram_pos = (screen_size[0] // 2, screen_size[1] // 2 - 50)

        if father_image_path:
            try:
                img = pygame.image.load(father_image_path).convert_alpha()
                self.father_image = pygame.transform.smoothscale(
                    img, self.hologram_size
                )
            except:
                self._create_placeholder_silhouette()
        else:
            self._create_placeholder_silhouette()

        # 홀로그램 효과
        self.hologram_alpha = 0
        self.hologram_flicker = 0.0
        self.glitch_offset = 0
        self.scanline_offset = 0

        # 장치 활성화 파티클
        self.activation_particles = []
        self.device_glow = 0.0

        # 배경 (어두운 벙커)
        self.bg_color = (15, 20, 30)

        # 홀로그램 색상 (청록색)
        self.holo_color = (100, 200, 255)

    def _create_placeholder_silhouette(self):
        """대체 아버지 실루엣 이미지"""
        surf = pygame.Surface(self.hologram_size, pygame.SRCALPHA)

        # 머리
        head_center = (self.hologram_size[0] // 2, 80)
        pygame.draw.circle(surf, (*self.holo_color, 150), head_center, 50)

        # 어깨/상체
        body_points = [
            (self.hologram_size[0] // 2 - 80, 400),
            (self.hologram_size[0] // 2 - 60, 150),
            (self.hologram_size[0] // 2, 130),
            (self.hologram_size[0] // 2 + 60, 150),
            (self.hologram_size[0] // 2 + 80, 400),
        ]
        pygame.draw.polygon(surf, (*self.holo_color, 120), body_points)

        self.father_image = surf

    def _on_fadein_complete(self):
        """페이드인 완료 후 장치 활성화"""
        self.phase = self.PHASE_DEVICE_ACTIVATE
        self.phase_timer = 0.0

    def update(self, dt: float):
        """업데이트"""
        if not self.is_alive:
            return

        self.phase_timer += dt

        # 스캔라인 이동
        self.scanline_offset = (self.scanline_offset + 100 * dt) % self.screen_size[1]

        # 글리치 효과
        if random.random() < 0.05:
            self.glitch_offset = random.randint(-10, 10)
        else:
            self.glitch_offset = int(self.glitch_offset * 0.8)

        # 페이즈 처리
        if self.phase == self.PHASE_FADEIN:
            if self._update_fadein(dt):
                self._on_fadein_complete()

        elif self.phase == self.PHASE_DEVICE_ACTIVATE:
            self.device_glow = min(1.0, self.device_glow + dt * 0.5)
            if self.phase_timer > 2.0:
                self.phase = self.PHASE_HOLOGRAM_FLICKER
                self.phase_timer = 0.0

        elif self.phase == self.PHASE_HOLOGRAM_FLICKER:
            # 홀로그램 깜빡임
            self.hologram_flicker += dt * 10
            flicker_value = (math.sin(self.hologram_flicker * 5) + 1) / 2
            self.hologram_alpha = int(flicker_value * 200)

            if self.phase_timer > 2.0:
                self.phase = self.PHASE_MESSAGE_PLAY
                self.phase_timer = 0.0
                self.hologram_alpha = 200

        elif self.phase == self.PHASE_MESSAGE_PLAY:
            # 안정된 홀로그램
            self.hologram_alpha = 200 + int(math.sin(self.phase_timer * 2) * 30)

            if self.phase_timer > 3.0:
                self._transition_to_dialogue()

        elif self.phase == self.PHASE_DIALOGUE:
            if self._update_dialogue(dt):
                self._transition_to_fadeout()

        elif self.phase == self.PHASE_FADEOUT:
            if self._update_fadeout(dt):
                self._on_fadeout_complete()

    def render(self, screen: pygame.Surface):
        """렌더링"""
        # 배경
        screen.fill(self.bg_color)

        # 벙커 내부 느낌
        for i in range(0, self.screen_size[0], 100):
            pygame.draw.line(screen, (25, 30, 40), (i, 0), (i, self.screen_size[1]), 2)
        for i in range(0, self.screen_size[1], 100):
            pygame.draw.line(screen, (25, 30, 40), (0, i), (self.screen_size[0], i), 2)

        # 장치 (바닥의 원형 플랫폼)
        device_center = (self.screen_size[0] // 2, self.screen_size[1] - 100)
        glow_radius = int(100 + self.device_glow * 50)
        for r in range(glow_radius, 0, -10):
            alpha = int(self.device_glow * 50 * (r / glow_radius))
            pygame.draw.circle(screen, (*self.holo_color, alpha), device_center, r)
        pygame.draw.circle(screen, (50, 60, 80), device_center, 80)
        pygame.draw.circle(screen, self.holo_color, device_center, 80, 3)

        # 홀로그램
        if self.phase in [
            self.PHASE_HOLOGRAM_FLICKER,
            self.PHASE_MESSAGE_PLAY,
            self.PHASE_DIALOGUE,
        ]:
            if self.father_image:
                holo_surf = self.father_image.copy()
                holo_surf.set_alpha(self.hologram_alpha)

                # 글리치 오프셋 적용
                pos = (
                    self.hologram_pos[0]
                    - self.hologram_size[0] // 2
                    + self.glitch_offset,
                    self.hologram_pos[1] - self.hologram_size[1] // 2,
                )
                screen.blit(holo_surf, pos)

                # 스캔라인 효과
                for y in range(0, self.screen_size[1], 4):
                    alpha = 30 if (y + int(self.scanline_offset)) % 8 < 4 else 0
                    if alpha > 0:
                        pygame.draw.line(
                            screen, (0, 0, 0, alpha), (0, y), (self.screen_size[0], y)
                        )

                # 홀로그램 외곽 글로우
                glow_surf = pygame.Surface(self.screen_size, pygame.SRCALPHA)
                glow_rect = pygame.Rect(
                    pos[0] - 20,
                    pos[1] - 20,
                    self.hologram_size[0] + 40,
                    self.hologram_size[1] + 40,
                )
                pygame.draw.rect(
                    glow_surf, (*self.holo_color, 30), glow_rect, border_radius=10
                )
                screen.blit(glow_surf, (0, 0))

        # 페이드
        if self.phase == self.PHASE_FADEIN:
            fade_surf = pygame.Surface(self.screen_size)
            fade_surf.fill((0, 0, 0))
            fade_surf.set_alpha(255 - int(self.fade_alpha))
            screen.blit(fade_surf, (0, 0))

        # 대사
        if self.phase == self.PHASE_DIALOGUE:
            self._render_dialogue(screen)

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
            box_color=(20, 30, 50, 230),
            border_color=(100, 180, 220),
            text_color=(200, 240, 255),
            box_height=180,
            has_portrait=(portrait is not None),
            portrait=portrait,
        )


class RadioWaveEffect(BaseCutsceneEffect):
    """
    어머니 신호 컷씬 (Act 4)

    특징:
    - 통신 기지에서 수신된 희미한 신호
    - 라디오 웨이브 시각화
    - 노이즈 속 어머니 목소리
    - 신호 강도 게이지
    """

    PHASE_SCANNING = 10
    PHASE_SIGNAL_FOUND = 11
    PHASE_VOICE_DETECTED = 12

    def __init__(
        self,
        screen_size: tuple,
        mother_voice_text: str = None,
        dialogue_after: list = None,
        sound_manager=None,
        special_effects: dict = None,
        scene_id: str = "radio_wave_scene",
    ):
        super().__init__(
            screen_size, None, dialogue_after, sound_manager, special_effects, scene_id
        )

        self.typing_speed = 20.0

        # 라디오 웨이브 데이터
        self.wave_data = [0.0] * 200
        self.wave_speed = 50.0
        self.signal_strength = 0.0
        self.target_signal = 0.0

        # 노이즈
        self.noise_intensity = 1.0
        self.noise_particles = []
        for _ in range(100):
            self.noise_particles.append(
                {
                    "x": random.randint(0, screen_size[0]),
                    "y": random.randint(0, screen_size[1]),
                    "size": random.randint(1, 3),
                }
            )

        # 어머니 목소리 텍스트 (신호에서 추출)
        self.mother_voice_text = (
            mother_voice_text or "...아르테미스... 살아있다면... 우리를 찾아..."
        )
        self.decoded_text = ""
        self.decode_progress = 0.0

        # 스캔 주파수
        self.frequency = 0.0
        self.target_frequency = 7.42  # 목표 주파수

        # 배경색
        self.bg_color = (10, 15, 25)

        # 색상
        self.wave_color = (0, 255, 150)
        self.signal_color = (255, 200, 50)

    def _on_fadein_complete(self):
        """페이드인 완료"""
        self.phase = self.PHASE_SCANNING
        self.phase_timer = 0.0

    def update(self, dt: float):
        """업데이트"""
        if not self.is_alive:
            return

        self.phase_timer += dt

        # 웨이브 데이터 업데이트
        self.wave_data.pop(0)
        if (
            self.phase == self.PHASE_SIGNAL_FOUND
            or self.phase == self.PHASE_VOICE_DETECTED
        ):
            # 신호 감지됨: 규칙적인 패턴
            wave_value = math.sin(self.phase_timer * 10) * 0.8
            wave_value += random.uniform(-0.1, 0.1) * self.noise_intensity
        else:
            # 스캔 중: 랜덤 노이즈
            wave_value = random.uniform(-1, 1) * self.noise_intensity

        self.wave_data.append(wave_value)

        # 노이즈 파티클 업데이트
        if random.random() < 0.3:
            for p in self.noise_particles:
                p["x"] = random.randint(0, self.screen_size[0])
                p["y"] = random.randint(0, self.screen_size[1])

        # 페이즈 처리
        if self.phase == self.PHASE_FADEIN:
            if self._update_fadein(dt):
                self._on_fadein_complete()

        elif self.phase == self.PHASE_SCANNING:
            # 주파수 스캔
            self.frequency += dt * 2
            if self.frequency >= self.target_frequency:
                self.phase = self.PHASE_SIGNAL_FOUND
                self.phase_timer = 0.0
                self.signal_strength = 0.3

        elif self.phase == self.PHASE_SIGNAL_FOUND:
            # 신호 강화
            self.signal_strength = min(1.0, self.signal_strength + dt * 0.3)
            self.noise_intensity = max(0.2, 1.0 - self.signal_strength)

            if self.signal_strength >= 0.8:
                self.phase = self.PHASE_VOICE_DETECTED
                self.phase_timer = 0.0

        elif self.phase == self.PHASE_VOICE_DETECTED:
            # 텍스트 디코딩
            self.decode_progress = min(1.0, self.decode_progress + dt * 0.3)
            decoded_len = int(len(self.mother_voice_text) * self.decode_progress)
            self.decoded_text = self.mother_voice_text[:decoded_len]

            if self.decode_progress >= 1.0 and self.phase_timer > 3.0:
                self._transition_to_dialogue()

        elif self.phase == self.PHASE_DIALOGUE:
            if self._update_dialogue(dt):
                self._transition_to_fadeout()

        elif self.phase == self.PHASE_FADEOUT:
            if self._update_fadeout(dt):
                self._on_fadeout_complete()

    def render(self, screen: pygame.Surface):
        """렌더링"""
        screen.fill(self.bg_color)

        # 그리드 배경
        grid_color = (30, 40, 50)
        for x in range(0, self.screen_size[0], 50):
            pygame.draw.line(screen, grid_color, (x, 0), (x, self.screen_size[1]))
        for y in range(0, self.screen_size[1], 50):
            pygame.draw.line(screen, grid_color, (0, y), (self.screen_size[0], y))

        # 노이즈 파티클
        for p in self.noise_particles:
            alpha = int(self.noise_intensity * 150)
            pygame.draw.rect(
                screen, (100, 100, 100, alpha), (p["x"], p["y"], p["size"], p["size"])
            )

        # 라디오 웨이브
        wave_height = 150
        wave_y = self.screen_size[1] // 2
        wave_width = self.screen_size[0] - 100

        points = []
        for i, val in enumerate(self.wave_data):
            x = 50 + int(i * wave_width / len(self.wave_data))
            y = wave_y + int(val * wave_height)
            points.append((x, y))

        if len(points) > 1:
            # 글로우 효과
            for offset in range(3, 0, -1):
                alpha = 100 - offset * 30
                offset_points = [(p[0], p[1] + offset) for p in points]
                pygame.draw.lines(
                    screen, (*self.wave_color[:3], alpha), False, offset_points, 2
                )

            pygame.draw.lines(screen, self.wave_color, False, points, 2)

        # 주파수 표시
        if "medium" in self.fonts:
            freq_text = f"주파수: {self.frequency:.2f} MHz"
            freq_surf = self.fonts["medium"].render(freq_text, True, self.wave_color)
            screen.blit(freq_surf, (50, 50))

        # 신호 강도 게이지
        gauge_x = self.screen_size[0] - 200
        gauge_y = 50
        gauge_width = 150
        gauge_height = 20

        pygame.draw.rect(
            screen, (50, 50, 50), (gauge_x, gauge_y, gauge_width, gauge_height)
        )
        fill_width = int(gauge_width * self.signal_strength)
        if fill_width > 0:
            color = self.signal_color if self.signal_strength > 0.5 else self.wave_color
            pygame.draw.rect(
                screen, color, (gauge_x, gauge_y, fill_width, gauge_height)
            )
        pygame.draw.rect(
            screen, (100, 100, 100), (gauge_x, gauge_y, gauge_width, gauge_height), 2
        )

        if "small" in self.fonts:
            label = self.fonts["small"].render("신호 강도", True, (150, 150, 150))
            screen.blit(label, (gauge_x, gauge_y - 20))

        # 디코딩된 텍스트
        if self.phase == self.PHASE_VOICE_DETECTED and self.decoded_text:
            if "medium" in self.fonts:
                text_y = self.screen_size[1] - 200
                # 글로우 박스
                box_rect = pygame.Rect(50, text_y - 20, self.screen_size[0] - 100, 80)
                pygame.draw.rect(screen, (20, 30, 40, 200), box_rect, border_radius=10)
                pygame.draw.rect(
                    screen, self.signal_color, box_rect, 2, border_radius=10
                )

                decoded_surf = self.fonts["medium"].render(
                    self.decoded_text, True, self.signal_color
                )
                screen.blit(decoded_surf, (70, text_y))

                label = self.fonts["small"].render(
                    "수신된 메시지:", True, (150, 150, 150)
                )
                screen.blit(label, (70, text_y - 25))

        # 스캔 중 텍스트
        if self.phase == self.PHASE_SCANNING and "medium" in self.fonts:
            scan_text = "주파수 스캔 중..."
            alpha = int(128 + 127 * math.sin(self.phase_timer * 5))
            scan_surf = self.fonts["medium"].render(
                scan_text, True, (*self.wave_color[:3], alpha)
            )
            x = self.screen_size[0] // 2 - scan_surf.get_width() // 2
            screen.blit(scan_surf, (x, self.screen_size[1] - 100))

        # 페이드
        if self.phase == self.PHASE_FADEIN:
            fade_surf = pygame.Surface(self.screen_size)
            fade_surf.fill((0, 0, 0))
            fade_surf.set_alpha(255 - int(self.fade_alpha))
            screen.blit(fade_surf, (0, 0))

        # 대사
        if self.phase == self.PHASE_DIALOGUE:
            self._render_dialogue(screen)

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
            box_color=(15, 25, 35, 230),
            border_color=(0, 200, 150),
            text_color=(200, 255, 230),
            box_height=180,
            has_portrait=(portrait is not None),
            portrait=portrait,
        )


class CountdownEffect(BaseCutsceneEffect):
    """
    카운트다운 컷씬 (Act 5)

    특징:
    - 최종 결전 전 카운트다운
    - 긴박한 분위기
    - 숫자가 화면에 크게 표시
    - 각 숫자마다 회상/결의 대사
    """

    PHASE_COUNTDOWN = 10
    PHASE_ZERO = 11

    def __init__(
        self,
        screen_size: tuple,
        countdown_start: int = 10,
        countdown_messages: list = None,
        dialogue_after: list = None,
        sound_manager=None,
        special_effects: dict = None,
        scene_id: str = "countdown_scene",
    ):
        super().__init__(
            screen_size, None, dialogue_after, sound_manager, special_effects, scene_id
        )

        self.typing_speed = 30.0

        # 카운트다운 설정
        self.countdown_start = countdown_start
        self.current_count = countdown_start
        self.count_timer = 0.0
        self.count_interval = 1.5  # 각 숫자 표시 시간

        # 각 숫자별 메시지
        self.countdown_messages = countdown_messages or [
            "모든 것이 이 순간을 위해...",
            "10년의 기다림...",
            "잃어버린 것들을 위해...",
            "가족을 되찾기 위해...",
            "희망을 지키기 위해...",
            "포기하지 않았기에...",
            "함께 싸워왔기에...",
            "이제 마지막...",
            "두려움은 없어...",
            "시작이다!",
        ]

        self.current_message = ""
        self.message_alpha = 0

        # 시각 효과
        self.pulse_scale = 1.0
        self.shake_offset = (0, 0)
        self.warning_flash = 0.0

        # 파티클 (불꽃)
        self.spark_particles = []

        # 배경 색상 (긴박한 빨간 톤)
        self.bg_colors = [
            (20, 10, 15),  # 시작
            (40, 15, 20),  # 중간
            (60, 20, 25),  # 끝
        ]

    def _on_fadein_complete(self):
        """페이드인 완료"""
        self.phase = self.PHASE_COUNTDOWN
        self.phase_timer = 0.0
        self.current_count = self.countdown_start

    def _create_sparks(self):
        """불꽃 파티클 생성"""
        center = (self.screen_size[0] // 2, self.screen_size[1] // 2)
        for _ in range(20):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(100, 300)
            self.spark_particles.append(
                {
                    "x": center[0],
                    "y": center[1],
                    "vx": math.cos(angle) * speed,
                    "vy": math.sin(angle) * speed,
                    "life": 1.0,
                    "color": random.choice(
                        [(255, 200, 100), (255, 150, 50), (255, 100, 50)]
                    ),
                }
            )

    def update(self, dt: float):
        """업데이트"""
        if not self.is_alive:
            return

        self.phase_timer += dt
        self.count_timer += dt

        # 경고 플래시
        self.warning_flash += dt * 10
        flash_intensity = (math.sin(self.warning_flash) + 1) / 2

        # 펄스 효과
        self.pulse_scale = 1.0 + 0.1 * math.sin(self.phase_timer * 5)

        # 화면 흔들림 (카운트가 낮을수록 강해짐)
        shake_intensity = max(0, (5 - self.current_count)) * 2
        self.shake_offset = (
            random.randint(-int(shake_intensity), int(shake_intensity)),
            random.randint(-int(shake_intensity), int(shake_intensity)),
        )

        # 파티클 업데이트
        for p in self.spark_particles[:]:
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            p["vy"] += 200 * dt  # 중력
            p["life"] -= dt * 2
            if p["life"] <= 0:
                self.spark_particles.remove(p)

        # 페이즈 처리
        if self.phase == self.PHASE_FADEIN:
            if self._update_fadein(dt):
                self._on_fadein_complete()

        elif self.phase == self.PHASE_COUNTDOWN:
            if self.count_timer >= self.count_interval:
                self.count_timer = 0
                self.current_count -= 1
                self._create_sparks()

                # 메시지 업데이트
                msg_index = self.countdown_start - self.current_count - 1
                if 0 <= msg_index < len(self.countdown_messages):
                    self.current_message = self.countdown_messages[msg_index]
                    self.message_alpha = 255

                if self.current_count <= 0:
                    self.phase = self.PHASE_ZERO
                    self.phase_timer = 0.0

            # 메시지 페이드
            self.message_alpha = max(0, self.message_alpha - 100 * dt)

        elif self.phase == self.PHASE_ZERO:
            if self.phase_timer > 2.0:
                self._transition_to_dialogue()

        elif self.phase == self.PHASE_DIALOGUE:
            if self._update_dialogue(dt):
                self._transition_to_fadeout()

        elif self.phase == self.PHASE_FADEOUT:
            if self._update_fadeout(dt):
                self._on_fadeout_complete()

    def render(self, screen: pygame.Surface):
        """렌더링"""
        # 배경 그라데이션 (긴박함 증가)
        progress = (
            1 - (self.current_count / self.countdown_start)
            if self.countdown_start > 0
            else 1
        )
        bg_color = [
            int(
                self.bg_colors[0][i]
                + (self.bg_colors[2][i] - self.bg_colors[0][i]) * progress
            )
            for i in range(3)
        ]
        screen.fill(bg_color)

        # 경고 플래시 오버레이
        flash_intensity = (math.sin(self.warning_flash) + 1) / 2
        if self.current_count <= 3:
            flash_surf = pygame.Surface(self.screen_size, pygame.SRCALPHA)
            flash_surf.fill((100, 20, 20, int(flash_intensity * 50)))
            screen.blit(flash_surf, (0, 0))

        # 원형 웨이브 (숫자 주변)
        center = (
            self.screen_size[0] // 2 + self.shake_offset[0],
            self.screen_size[1] // 2 + self.shake_offset[1],
        )

        wave_radius = int(100 + (self.count_timer / self.count_interval) * 200)
        wave_alpha = int(100 * (1 - self.count_timer / self.count_interval))
        if wave_alpha > 0:
            for r in range(wave_radius, wave_radius - 20, -5):
                if r > 0:
                    alpha = int(wave_alpha * (1 - (wave_radius - r) / 20))
                    pygame.draw.circle(screen, (255, 100, 100, alpha), center, r, 2)

        # 카운트다운 숫자
        if self.phase in [self.PHASE_COUNTDOWN, self.PHASE_ZERO]:
            count_text = str(max(0, self.current_count))
            if "xlarge" in self.fonts:
                font = self.fonts["xlarge"]
            elif "large" in self.fonts:
                font = self.fonts["large"]
            else:
                font = pygame.font.Font(None, 200)

            # 글로우 효과
            for glow_offset in range(10, 0, -2):
                glow_color = (255, 100 + glow_offset * 10, 100 + glow_offset * 10)
                glow_surf = font.render(count_text, True, glow_color)
                glow_surf.set_alpha(50 - glow_offset * 4)

                scaled_size = (
                    int(glow_surf.get_width() * self.pulse_scale),
                    int(glow_surf.get_height() * self.pulse_scale),
                )
                scaled = pygame.transform.smoothscale(glow_surf, scaled_size)

                x = center[0] - scaled.get_width() // 2
                y = center[1] - scaled.get_height() // 2 - 50
                screen.blit(scaled, (x, y))

            # 메인 숫자
            number_surf = font.render(count_text, True, (255, 220, 200))
            scaled_size = (
                int(number_surf.get_width() * self.pulse_scale),
                int(number_surf.get_height() * self.pulse_scale),
            )
            scaled = pygame.transform.smoothscale(number_surf, scaled_size)

            x = center[0] - scaled.get_width() // 2
            y = center[1] - scaled.get_height() // 2 - 50
            screen.blit(scaled, (x, y))

        # 메시지
        if self.current_message and self.message_alpha > 0:
            if "medium" in self.fonts:
                msg_surf = self.fonts["medium"].render(
                    self.current_message, True, (255, 230, 200)
                )
                msg_surf.set_alpha(int(self.message_alpha))
                x = center[0] - msg_surf.get_width() // 2
                y = center[1] + 100
                screen.blit(msg_surf, (x, y))

        # 불꽃 파티클
        for p in self.spark_particles:
            alpha = int(255 * p["life"])
            size = int(3 * p["life"])
            if size > 0:
                spark_surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
                pygame.draw.circle(spark_surf, (*p["color"], alpha), (size, size), size)
                screen.blit(spark_surf, (int(p["x"]) - size, int(p["y"]) - size))

        # PHASE_ZERO 특별 효과
        if self.phase == self.PHASE_ZERO:
            # 화면 전체 플래시
            flash_progress = min(1.0, self.phase_timer / 0.5)
            if flash_progress < 1.0:
                flash_surf = pygame.Surface(self.screen_size, pygame.SRCALPHA)
                flash_surf.fill((255, 255, 255, int(255 * (1 - flash_progress))))
                screen.blit(flash_surf, (0, 0))

            # "전투 개시" 텍스트
            if self.phase_timer > 0.5 and "large" in self.fonts:
                battle_text = "전투 개시"
                battle_surf = self.fonts["large"].render(
                    battle_text, True, (255, 200, 150)
                )
                x = center[0] - battle_surf.get_width() // 2
                y = center[1] - battle_surf.get_height() // 2 - 50
                screen.blit(battle_surf, (x, y))

        # 페이드
        if self.phase == self.PHASE_FADEIN:
            fade_surf = pygame.Surface(self.screen_size)
            fade_surf.fill((0, 0, 0))
            fade_surf.set_alpha(255 - int(self.fade_alpha))
            screen.blit(fade_surf, (0, 0))

        # 대사
        if self.phase == self.PHASE_DIALOGUE:
            self._render_dialogue(screen)

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
            box_color=(40, 20, 25, 230),
            border_color=(255, 150, 100),
            text_color=(255, 240, 230),
            box_height=180,
            has_portrait=(portrait is not None),
            portrait=portrait,
        )


# =============================================================================
# LightningEffect - 번개 체인 시각 효과 (이미지 기반)
# =============================================================================


