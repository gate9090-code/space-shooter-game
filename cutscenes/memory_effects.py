"""
cutscenes/memory_effects.py
Memory-related cutscene effects (polaroid, shattered mirror, dual memory, etc.)
"""

import pygame
import math
import random
from pathlib import Path
from cutscenes.base import BaseCutsceneEffect, render_dialogue_box


class PolaroidMemoryEffect:
    """
    폴라로이드 회상 컷씬 효과

    특징:
    - 배경 이미지 + 어둡게 처리
    - 여러 장의 폴라로이드 사진이 겹쳐서 표시
    - 각 사진은 랜덤 각도로 회전
    - 순차적으로 등장하는 애니메이션
    - 프레임(흰 테두리)은 코드로 자동 생성
    """

    PHASE_FADEIN = 0  # 배경 페이드인
    PHASE_PHOTOS = 1  # 사진 등장
    PHASE_DISPLAY = 2  # 사진 표시 (대기)
    PHASE_DIALOGUE = 3  # 대사 표시
    PHASE_FINAL_ZOOM = 4  # 최종 사진 확대 (memory_survive)
    PHASE_FADEOUT = 5  # 페이드아웃
    PHASE_DONE = 6  # 완료

    def __init__(
        self,
        screen_size: tuple,
        photo_paths: list,
        background_path: str = None,
        dialogue_after: list = None,
        dialogue_per_photo: list = None,
        sound_manager=None,
        special_effects: dict = None,
        scene_id: str = "memory_scene_01",
        voice_system=None,
    ):
        """
        Args:
            screen_size: 화면 크기
            photo_paths: 폴라로이드 사진 경로 리스트
            background_path: 배경 이미지 경로
            dialogue_after: 모든 사진 표시 후 대사 리스트
            dialogue_per_photo: 각 폴라로이드 등장 시 자동 표시되는 대사 리스트
            sound_manager: 효과음 재생용
            special_effects: 특수 효과 설정 (파일명: {effect: "flicker"/"fullscreen_fadeout", ...})
            scene_id: 메모리 씬 식별자 (리플레이용)
            voice_system: 음성 시스템 (VoiceSystem 인스턴스)
        """
        self.screen_size = screen_size
        self.photo_paths = photo_paths
        self.background_path = background_path  # 리플레이용 저장
        self.dialogue_after = dialogue_after or []
        self.dialogue_per_photo = (
            dialogue_per_photo or []
        )  # 각 폴라로이드에 대응하는 대화
        self.sound_manager = sound_manager
        self.special_effects = special_effects or {}
        self.scene_id = scene_id  # 메모리 씬 ID
        self.voice_system = voice_system  # 음성 시스템

        self.is_alive = True
        self.phase = self.PHASE_FADEIN
        self.phase_timer = 0.0

        # 타이밍 (빠르게 조정)
        self.fadein_duration = 1.8
        self.photo_interval = 4.3  # 사진 완전 등장 후 대기 시간 (대화 읽을 시간 포함)
        self.photo_animation_speed = (
            0.20  # 사진 날아오는 속도 (0.12 → 0.20, 약 67% 증가)
        )
        self.display_duration = 2.5  # 전체 사진 표시 후 대기 시간
        self.fadeout_duration = 1.8
        self.fade_alpha = 0.0

        # 사진 확대 효과용 (여러 사진 지원)
        self.final_zoom_duration = 3.0  # 확대 지속 시간
        self.final_zoom_scale = 1.0  # 현재 확대 배율
        self.final_zoom_alpha = 255  # 최종 사진 알파
        self.zoom_photo_indices = []  # 확대 효과 적용할 사진 인덱스 리스트
        self.current_zoom_index = 0  # 현재 확대 중인 사진 인덱스 (리스트 내 위치)
        self.final_photo_index = -1  # 현재 확대 중인 실제 사진 인덱스 (호환성용)

        # 점멸 효과용
        self.flicker_timer = 0.0

        # 배경
        self.background = None
        if background_path:
            self._load_background(background_path)

        # 폴라로이드 사진들
        self.polaroids = []
        self._prepare_polaroids()

        # 현재 표시 중인 사진 개수
        self.visible_count = 0
        self.photo_timer = 0.0

        # 대사 관련 (폴라로이드별 + 마지막 대화)
        self.current_dialogue_index = 0
        self.dialogue_text = ""
        self.typing_progress = 0.0
        self.typing_speed = 30.0  # 타이핑 속도
        self.waiting_for_click = False
        self.current_photo_dialogue_shown = False  # 현재 폴라로이드 대화 표시 완료 여부

        # 초상화 캐시
        self.portrait_cache = {}

        # 폰트
        self.fonts = {}

        # 콜백
        self.on_complete = None
        self.on_replay_request = None  # 리플레이 요청 콜백

        # 리플레이 버튼 관련
        self.replay_button_rect = None
        self.replay_button_hover = False
        self.replay_button_alpha = 0.0  # 버튼 페이드 인 효과

    def _load_background(self, path: str):
        """배경 이미지 로드"""
        try:
            img = pygame.image.load(path).convert()
            self.background = pygame.transform.scale(img, self.screen_size)
        except Exception as e:
            print(f"WARNING: Failed to load background: {path} - {e}")

    def _prepare_polaroids(self):
        """폴라로이드 사진 준비 - 자연스럽게 흩어진 배치"""
        import random

        # 화면 중앙 영역 계산
        screen_w, screen_h = self.screen_size
        center_x = screen_w // 2
        center_y = screen_h // 2 - 50

        # 사진 크기
        photo_size = 260

        # 자연스럽게 흩어진 위치 (테이블 위에 던져놓은 느낌)
        # 흰 테두리가 살짝 겹치는 정도로 배치 - 9장 사진용
        base_positions = [
            (-320, -160),  # 좌상단 - 1번
            (80, -200),  # 중상단 (약간 치우침) - 2번
            (350, -80),  # 우측 - 3번
            (-250, 100),  # 좌하단 - 4번
            (30, 120),  # 중앙 아래 - 5번
            (320, 200),  # 우하단 - 6번
            (-380, 20),  # 좌측 중앙 - 7번
            (-150, -50),  # 중앙 좌측 (memory_ufo용) - 8번
            (0, 0),  # 정중앙 (memory_survive용 - 확대될 사진) - 9번
        ]

        positions = []
        for bx, by in base_positions:
            # 각 위치에 랜덤 오프셋 추가 (자연스러움)
            offset_x = random.randint(-60, 60)
            offset_y = random.randint(-50, 50)
            x = center_x + bx + offset_x
            y = center_y + by + offset_y
            positions.append((x, y))

        # 위치 순서도 섞기 (더 자연스럽게)
        random.shuffle(positions)

        # 다양한 진입 방향 정의 (외부에서 날아오기) - 9개
        entry_directions = [
            ("left", -400, 0),  # 왼쪽에서 - 1번
            ("right", 400, 0),  # 오른쪽에서 - 2번
            ("top", 0, -400),  # 위에서 - 3번
            ("bottom", 0, 400),  # 아래에서 - 4번
            ("top_left", -300, -300),  # 좌상단에서 - 5번
            ("bottom_right", 300, 300),  # 우하단에서 - 6번
            ("left_bottom", -350, 200),  # 좌측 아래에서 - 7번
            ("top_right", 300, -300),  # 우상단에서 (memory_ufo용) - 8번
            ("bottom_left", -300, 300),  # 좌하단에서 (memory_survive용) - 9번
        ]

        for i, path in enumerate(self.photo_paths):
            if i >= len(positions):
                break

            # 이미지 로드
            photo_img = None
            try:
                photo_img = pygame.image.load(path).convert_alpha()
                # 크기 조정
                photo_img = pygame.transform.smoothscale(
                    photo_img, (photo_size, photo_size)
                )
            except Exception as e:
                print(f"WARNING: Failed to load polaroid: {path} - {e}")
                # 플레이스홀더 생성
                photo_img = pygame.Surface((photo_size, photo_size))
                photo_img.fill((100, 100, 100))

            # 폴라로이드 프레임 생성 (낡은 효과)
            # 2번째 사진(인덱스 1)에만 photo_flip_00.png 적용
            framed = self._create_polaroid_frame(photo_img, photo_index=i)

            # 최종 목표 위치
            target_x, target_y = positions[i]

            # 진입 방향 선택 (다양하게)
            direction_name, offset_x, offset_y = entry_directions[
                i % len(entry_directions)
            ]

            # 시작 위치 (화면 외부)
            start_x = target_x + offset_x
            start_y = target_y + offset_y

            # 랜덤 각도 (-18도 ~ +18도) - 더 자연스럽게 기울어짐
            angle = random.uniform(-18, 18)

            # 회전 적용
            rotated = pygame.transform.rotate(framed, angle)

            # 파일명 추출 (특수 효과 확인용)
            filename = Path(path).name
            effect_info = self.special_effects.get(filename, {})
            effect_type = effect_info.get("effect", None)

            # 확대 효과가 적용될 사진 인덱스 저장 (flicker_then_zoom 또는 fullscreen_fadeout)
            if effect_type in ["fullscreen_fadeout", "flicker_then_zoom"]:
                self.zoom_photo_indices.append(i)

            self.polaroids.append(
                {
                    "image": rotated,
                    "original_image": framed,  # 원본 보관 (스케일 조정용)
                    "photo_image": photo_img,  # 원본 사진 (확대용)
                    "pos": [start_x, start_y],  # 현재 위치 (리스트로 변경 - 수정 가능)
                    "target_pos": (target_x, target_y),  # 목표 위치
                    "start_pos": (start_x, start_y),  # 시작 위치
                    "angle": angle,
                    "target_angle": angle
                    + random.uniform(-3, 3),  # 최종 각도 (살짝 변화)
                    "alpha": 0,  # 처음엔 투명
                    "target_alpha": 255,
                    "scale": 0.5,  # 처음엔 작게
                    "target_scale": 1.0,
                    "direction": direction_name,
                    "animation_progress": 0.0,  # 0.0 ~ 1.0
                    "filename": filename,  # 파일명 (특수 효과용)
                    "effect_type": effect_type,  # 특수 효과 타입
                    "flicker_speed": effect_info.get("flicker_speed", 0.3),  # 점멸 속도
                    "flicker_phase": 0.0,  # 점멸 위상
                }
            )

    def _create_polaroid_frame(
        self, photo: pygame.Surface, photo_index: int = 0
    ) -> pygame.Surface:
        """폴라로이드 프레임 생성 - 낡고 빛바랜 효과"""
        import random

        photo_w, photo_h = photo.get_size()

        # 프레임 크기 (테두리 18px, 하단 45px 추가 - 더 크게)
        border = 18
        bottom_margin = 45
        frame_w = photo_w + border * 2
        frame_h = photo_h + border + bottom_margin

        # 프레임 Surface 생성
        frame = pygame.Surface((frame_w, frame_h), pygame.SRCALPHA)

        # 오래된 폴라로이드 색상 (아이보리/크림색, 약간 변색)
        base_color = (245, 240, 225)  # 빛바랜 크림색
        frame.fill(base_color)

        # 불균일한 변색 효과 (노이즈)
        for _ in range(50):
            x = random.randint(0, frame_w - 1)
            y = random.randint(0, frame_h - 1)
            spot_size = random.randint(3, 8)
            # 약간 더 어둡거나 누런 반점
            spot_color = (
                base_color[0] - random.randint(5, 20),
                base_color[1] - random.randint(8, 25),
                base_color[2] - random.randint(10, 30),
            )
            pygame.draw.circle(frame, spot_color, (x, y), spot_size)

        # 가장자리 어둡게 (빛바랜 효과)
        edge_overlay = pygame.Surface((frame_w, frame_h), pygame.SRCALPHA)
        # 상단 가장자리
        for i in range(8):
            alpha = 25 - i * 3
            pygame.draw.line(edge_overlay, (180, 170, 140, alpha), (0, i), (frame_w, i))
        # 하단 가장자리
        for i in range(8):
            alpha = 25 - i * 3
            pygame.draw.line(
                edge_overlay,
                (180, 170, 140, alpha),
                (0, frame_h - 1 - i),
                (frame_w, frame_h - 1 - i),
            )
        # 좌측 가장자리
        for i in range(6):
            alpha = 20 - i * 3
            pygame.draw.line(edge_overlay, (180, 170, 140, alpha), (i, 0), (i, frame_h))
        # 우측 가장자리
        for i in range(6):
            alpha = 20 - i * 3
            pygame.draw.line(
                edge_overlay,
                (180, 170, 140, alpha),
                (frame_w - 1 - i, 0),
                (frame_w - 1 - i, frame_h),
            )
        frame.blit(edge_overlay, (0, 0))

        # 외곽선 (낡은 갈색 톤)
        pygame.draw.rect(frame, (200, 185, 160), (0, 0, frame_w, frame_h), 2)
        # 내부 테두리 (더 밝은 선)
        pygame.draw.rect(frame, (230, 220, 200), (2, 2, frame_w - 4, frame_h - 4), 1)

        # 사진에 약간의 세피아/빈티지 효과 적용
        vintage_photo = self._apply_vintage_effect(photo)

        # 사진 배치
        frame.blit(vintage_photo, (border, border))

        # 사진 테두리 (약간 어두운 선)
        pygame.draw.rect(
            frame,
            (210, 200, 180),
            (border - 1, border - 1, photo_w + 2, photo_h + 2),
            1,
        )

        # 모서리 들뜬 효과 - 2번째 사진(인덱스 1)에만 photo_flip_00.png 적용
        if photo_index == 1:
            flip_overlay = self._load_flip_overlay(
                frame_w,
                frame_h,
                border,
                photo_w,
                photo_h,
                flip_file="photo_flip_00.png",
            )
            if flip_overlay:
                frame.blit(flip_overlay, (0, 0))

        return frame

    def _load_flip_overlay(
        self,
        frame_w: int,
        frame_h: int,
        border: int = 18,
        photo_w: int = 260,
        photo_h: int = 260,
        flip_file: str = "photo_flip.png",
    ) -> pygame.Surface:
        """모서리 들뜬 효과 이미지 로드 - 프레임(흰 테두리)에만 적용"""
        try:
            flip_path = f"assets/story_mode/polaroids/{flip_file}"
            if Path(flip_path).exists():
                img = pygame.image.load(flip_path).convert_alpha()
                # 프레임 크기에 맞게 스케일링
                img = pygame.transform.scale(img, (frame_w, frame_h))

                # 사진 영역을 투명하게 만들기 (프레임만 효과 적용)
                # 사진 영역의 위치: (border, border) ~ (border + photo_w, border + photo_h)
                transparent_rect = pygame.Surface((photo_w, photo_h), pygame.SRCALPHA)
                transparent_rect.fill((0, 0, 0, 0))
                # BLEND_RGBA_MIN: 알파값을 최소화하여 해당 영역을 투명하게
                img.blit(
                    transparent_rect,
                    (border, border),
                    special_flags=pygame.BLEND_RGBA_MIN,
                )

                return img
        except Exception as e:
            print(f"WARNING: Failed to load photo_flip.png: {e}")
        return None

    def _apply_vintage_effect(self, photo: pygame.Surface) -> pygame.Surface:
        """사진에 빈티지/세피아 효과 적용"""
        result = photo.copy()
        w, h = result.get_size()

        # 전체적으로 약간 따뜻한 톤 추가 (세피아 느낌)
        sepia_overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        sepia_overlay.fill((255, 240, 200, 30))  # 따뜻한 세피아 톤
        result.blit(sepia_overlay, (0, 0))

        # 비네트 효과 (가장자리 어둡게)
        vignette = pygame.Surface((w, h), pygame.SRCALPHA)
        for i in range(20):
            alpha = 3 * (20 - i)
            # 상단
            pygame.draw.line(vignette, (0, 0, 0, alpha), (0, i), (w, i))
            # 하단
            pygame.draw.line(vignette, (0, 0, 0, alpha), (0, h - 1 - i), (w, h - 1 - i))
            # 좌측
            pygame.draw.line(vignette, (0, 0, 0, alpha), (i, 0), (i, h))
            # 우측
            pygame.draw.line(vignette, (0, 0, 0, alpha), (w - 1 - i, 0), (w - 1 - i, h))
        result.blit(vignette, (0, 0))

        return result

    def set_fonts(self, fonts: dict):
        """폰트 설정"""
        self.fonts = fonts

    def update(self, dt: float):
        """업데이트"""
        if not self.is_alive:
            return

        self.phase_timer += dt

        if self.phase == self.PHASE_FADEIN:
            progress = min(self.phase_timer / self.fadein_duration, 1.0)
            self.fade_alpha = progress

            if progress >= 1.0:
                self.phase = self.PHASE_PHOTOS
                self.phase_timer = 0.0
                self.photo_timer = 0.0

        elif self.phase == self.PHASE_PHOTOS:
            # 사진 순차 등장 (사진 출현 시작과 동시에 대화 표시)
            self.photo_timer += dt

            # 현재 사진이 완전히 등장했는지 확인
            current_photo_complete = False
            if self.visible_count > 0 and self.visible_count <= len(self.polaroids):
                current_p = self.polaroids[self.visible_count - 1]
                current_photo_complete = current_p["animation_progress"] >= 1.0

            # 다음 사진 등장 조건 (대화 표시보다 먼저 체크)
            if self.visible_count == 0:
                # 첫 번째 사진은 바로 시작
                if self.sound_manager:
                    self.sound_manager.play_sfx("sfx_polaroid")
                self.visible_count = 1
                self.photo_timer = 0.0
                self.current_photo_dialogue_shown = False  # 대화 준비
            elif current_photo_complete and self.visible_count < len(self.polaroids):
                # 현재 사진 완료 + 대화 읽을 시간 후 다음 사진
                if self.photo_timer >= self.photo_interval:
                    if self.sound_manager:
                        self.sound_manager.play_sfx("sfx_polaroid")
                    self.visible_count += 1
                    self.photo_timer = 0.0  # 타이머 리셋
                    self.current_photo_dialogue_shown = False  # 다음 대화 준비
                    self.dialogue_text = ""  # 대화 초기화

            # 폴라로이드 출현과 동시에 대화 자동 표시 (visible_count 증가 직후)
            if self.visible_count > 0 and not self.current_photo_dialogue_shown:
                photo_index = self.visible_count - 1
                if photo_index < len(self.dialogue_per_photo):
                    # 해당 폴라로이드의 대화 시작 (출현 시작 시점)
                    self.dialogue_text = ""
                    self.typing_progress = 0.0
                    self.current_photo_dialogue_shown = True
                    # photo_timer는 이미 0.0으로 설정됨

                    # 폴라로이드별 음성 재생
                    dialogue = self.dialogue_per_photo[photo_index]
                    speaker = dialogue.get("speaker", "")
                    text = dialogue.get("text", "")
                    print(
                        f"DEBUG: Photo {photo_index + 1} - speaker={speaker}, text={text[:30] if text else 'None'}, voice_system={self.voice_system is not None}"
                    )
                    if self.voice_system and speaker and text:
                        import re

                        clean_text = re.sub(r"[▼◀▶]", "", text)
                        self.voice_system.speak(speaker, clean_text)
                        print(
                            f"INFO: Playing voice for {speaker}: {clean_text[:30]}..."
                        )

            # 대화 타이핑 효과 (PHASE_PHOTOS 중에도)
            if self.current_photo_dialogue_shown and self.visible_count > 0:
                photo_index = self.visible_count - 1
                if photo_index < len(self.dialogue_per_photo):
                    self.typing_progress += self.typing_speed * dt
                    char_count = int(self.typing_progress)
                    full_text = self.dialogue_per_photo[photo_index].get("text", "")
                    if char_count >= len(full_text):
                        self.dialogue_text = full_text
                    else:
                        self.dialogue_text = full_text[:char_count]

            # 사진 애니메이션 업데이트 (2배 확대 → 잠시 유지 → 원래 크기로 축소)
            for i, p in enumerate(self.polaroids):
                if i < self.visible_count:
                    # 애니메이션 진행도 업데이트
                    p["animation_progress"] = min(
                        p["animation_progress"] + self.photo_animation_speed * dt, 1.0
                    )
                    progress = p["animation_progress"]

                    # 3단계 애니메이션: 등장(0~0.3) → 확대 유지(0.3~0.6) → 축소(0.6~1.0)
                    if progress < 0.3:
                        # 1단계: 등장 (외부에서 날아오며 2배 크기로)
                        phase_progress = progress / 0.3
                        eased = 1 - pow(1 - phase_progress, 3)  # ease-out-cubic

                        # 위치 보간 (시작 → 목표)
                        start_x, start_y = p["start_pos"]
                        target_x, target_y = p["target_pos"]
                        p["pos"][0] = start_x + (target_x - start_x) * eased
                        p["pos"][1] = start_y + (target_y - start_y) * eased

                        # 알파 증가
                        p["alpha"] = min(int(255 * eased), p["target_alpha"])

                        # 스케일: 0.5 → 2.0 (등장하면서 2배로 확대)
                        p["scale"] = 0.5 + 1.5 * eased

                    elif progress < 0.6:
                        # 2단계: 확대 상태 유지 (2배 크기로 잠시 보여줌)
                        p["pos"][0], p["pos"][1] = p["target_pos"]
                        p["alpha"] = 255
                        p["scale"] = 2.0

                    else:
                        # 3단계: 원래 크기로 축소 (2.0 → 1.0)
                        phase_progress = (progress - 0.6) / 0.4
                        eased = 1 - pow(1 - phase_progress, 2)  # ease-out-quad

                        p["pos"][0], p["pos"][1] = p["target_pos"]
                        p["alpha"] = 255
                        # 스케일: 2.0 → 1.0
                        p["scale"] = 2.0 - 1.0 * eased

                    # 점멸 효과 (flicker 또는 flicker_then_zoom) - 축소 완료 후에만 적용
                    if (
                        p.get("effect_type") in ["flicker", "flicker_then_zoom"]
                        and p["animation_progress"] >= 0.95
                    ):
                        p["flicker_phase"] += dt * (1.0 / p.get("flicker_speed", 0.3))
                        # 느린 점멸 (사인파로 부드럽게)
                        flicker_val = 0.5 + 0.5 * math.sin(p["flicker_phase"] * math.pi)
                        p["alpha"] = int(150 + 105 * flicker_val)  # 150~255 사이

            # 모든 사진 등장 완료
            if self.visible_count >= len(self.polaroids):
                all_complete = all(
                    p["animation_progress"] >= 0.98 for p in self.polaroids
                )
                if all_complete:
                    # 최종 위치로 고정
                    for p in self.polaroids:
                        p["pos"][0], p["pos"][1] = p["target_pos"]
                        # 점멸 효과 (flicker 또는 flicker_then_zoom)는 알파 유지
                        if p.get("effect_type") not in ["flicker", "flicker_then_zoom"]:
                            p["alpha"] = 255
                        p["scale"] = 1.0
                    self.phase = self.PHASE_DISPLAY
                    self.phase_timer = 0.0

        elif self.phase == self.PHASE_DISPLAY:
            # 점멸 효과 업데이트 (DISPLAY 중에도 계속) - flicker_then_zoom도 포함
            for p in self.polaroids:
                if p.get("effect_type") in ["flicker", "flicker_then_zoom"]:
                    p["flicker_phase"] += dt * (1.0 / p.get("flicker_speed", 0.3))
                    flicker_val = 0.5 + 0.5 * math.sin(p["flicker_phase"] * math.pi)
                    p["alpha"] = int(150 + 105 * flicker_val)

            # 잠시 표시
            if self.phase_timer >= self.display_duration:
                # 확대 효과가 적용될 사진이 있으면 FINAL_ZOOM으로 전환
                if len(self.zoom_photo_indices) > 0:
                    self.current_zoom_index = 0
                    self.final_photo_index = self.zoom_photo_indices[0]
                    self.phase = self.PHASE_FINAL_ZOOM
                    self.phase_timer = 0.0
                    self.final_zoom_scale = 1.0
                    self.final_zoom_alpha = 255
                elif self.dialogue_after:
                    self.phase = self.PHASE_DIALOGUE
                    self.phase_timer = 0.0
                    self._prepare_dialogue(0)
                else:
                    self.phase = self.PHASE_FADEOUT
                    self.phase_timer = 0.0

        elif self.phase == self.PHASE_FINAL_ZOOM:
            # 사진 화면 전체로 확대 후 페이드아웃 (여러 사진 순차 처리)
            progress = min(self.phase_timer / self.final_zoom_duration, 1.0)

            # 이징 (ease-in-out)
            if progress < 0.5:
                eased = 2 * progress * progress
            else:
                eased = 1 - pow(-2 * progress + 2, 2) / 2

            # 확대 배율 (1.0 → 화면 가득)
            # 목표 배율: 화면 크기 / 사진 크기 * 약간의 여유
            target_scale = max(self.screen_size[0], self.screen_size[1]) / 260 * 1.2
            self.final_zoom_scale = 1.0 + (target_scale - 1.0) * eased

            # 후반부에 페이드아웃 시작
            if progress > 0.6:
                fade_progress = (progress - 0.6) / 0.4
                self.final_zoom_alpha = int(255 * (1.0 - fade_progress))

            if progress >= 1.0:
                # 다음 확대 사진이 있는지 확인
                self.current_zoom_index += 1
                if self.current_zoom_index < len(self.zoom_photo_indices):
                    # 다음 사진 확대 시작
                    self.final_photo_index = self.zoom_photo_indices[
                        self.current_zoom_index
                    ]
                    self.phase_timer = 0.0
                    self.final_zoom_scale = 1.0
                    self.final_zoom_alpha = 255
                else:
                    # 모든 확대 완료 → 대사 또는 페이드아웃
                    if self.dialogue_after:
                        self.phase = self.PHASE_DIALOGUE
                        self.phase_timer = 0.0
                        self._prepare_dialogue(0)
                    else:
                        self.phase = self.PHASE_FADEOUT
                        self.phase_timer = 0.0

        elif self.phase == self.PHASE_DIALOGUE:
            # 타이핑 효과
            if not self.waiting_for_click:
                self.typing_progress += self.typing_speed * dt
                char_count = int(self.typing_progress)
                full_text = self.dialogue_after[self.current_dialogue_index].get(
                    "text", ""
                )

                if char_count >= len(full_text):
                    self.dialogue_text = full_text
                    self.waiting_for_click = True
                else:
                    self.dialogue_text = full_text[:char_count]

        elif self.phase == self.PHASE_FADEOUT:
            progress = min(self.phase_timer / self.fadeout_duration, 1.0)
            self.fade_alpha = 1.0 - progress

            # 사진 페이드아웃
            for p in self.polaroids:
                p["alpha"] = max(0, int(255 * (1.0 - progress)))

            if progress >= 1.0:
                self.phase = self.PHASE_DONE
                self.is_alive = False
                if self.on_complete:
                    self.on_complete()

    def _get_portrait(self, speaker: str) -> pygame.Surface:
        """초상화 이미지 가져오기 (캐시 사용) - render_dialogue_box가 크기 조정"""
        if speaker in self.portrait_cache:
            return self.portrait_cache[speaker]

        # config_story_dialogue에서 경로 가져오기
        try:
            from mode_configs.config_story_dialogue import CHARACTER_PORTRAITS

            path = CHARACTER_PORTRAITS.get(speaker)
        except ImportError:
            # 폴백: 기본 경로
            portrait_paths = {
                "ARTEMIS": "assets/story_mode/portraits/portrait_artemis.jpg",
                "PILOT": "assets/story_mode/portraits/portrait_pilot.png",
            }
            path = portrait_paths.get(speaker)

        if path:
            try:
                # 원본 크기로 로드 (render_dialogue_box가 화자에 따라 크기 조정)
                img = pygame.image.load(path).convert_alpha()
                self.portrait_cache[speaker] = img
                return img
            except Exception as e:
                print(f"WARNING: Failed to load portrait for {speaker}: {e}")

        return None

    def _prepare_dialogue(self, index: int):
        """대사 준비 및 음성 재생"""
        if 0 <= index < len(self.dialogue_after):
            self.dialogue_text = ""
            self.typing_progress = 0.0
            self.waiting_for_click = False

            # 음성 재생
            dialogue = self.dialogue_after[index]
            speaker = dialogue.get("speaker", "")
            text = dialogue.get("text", "")
            if self.voice_system and speaker and text:
                # 특수 문자 제거 (음성 합성용)
                import re

                clean_text = re.sub(r"[▼◀▶]", "", text)
                self.voice_system.speak(speaker, clean_text)

    def handle_click(self):
        """클릭 처리 - 폴라로이드 등장 중에는 클릭 무시 (자동 진행)"""
        if self.phase == self.PHASE_FADEIN:
            # 페이드인 중 클릭 시 스킵
            self.phase = self.PHASE_PHOTOS
            self.phase_timer = 0.0
            self.fade_alpha = 1.0
            return

        if self.phase == self.PHASE_PHOTOS:
            # 폴라로이드 등장 중에는 클릭 무시 (자동 진행만 허용)
            # 클릭으로 즉시 등장하는 기능 삭제
            return

        if self.phase == self.PHASE_DISPLAY:
            # 최종 사진 확대 효과가 있으면 FINAL_ZOOM으로 전환
            if self.final_photo_index >= 0:
                self.phase = self.PHASE_FINAL_ZOOM
                self.phase_timer = 0.0
                self.final_zoom_scale = 1.0
                self.final_zoom_alpha = 255
            elif self.dialogue_after:
                self.phase = self.PHASE_DIALOGUE
                self.phase_timer = 0.0
                self._prepare_dialogue(0)
            else:
                self.phase = self.PHASE_FADEOUT
                self.phase_timer = 0.0
            return

        if self.phase == self.PHASE_FINAL_ZOOM:
            # 최종 확대 스킵 → 대사 또는 페이드아웃
            if self.dialogue_after:
                self.phase = self.PHASE_DIALOGUE
                self.phase_timer = 0.0
                self._prepare_dialogue(0)
            else:
                self.phase = self.PHASE_FADEOUT
                self.phase_timer = 0.0
            return

        if self.phase == self.PHASE_DIALOGUE:
            # 리플레이 버튼 클릭 체크 (마지막 대사일 때)
            is_last_dialogue = (
                self.current_dialogue_index >= len(self.dialogue_after) - 1
            )
            if is_last_dialogue and self.waiting_for_click and self.replay_button_rect:
                mouse_pos = pygame.mouse.get_pos()
                if self.replay_button_rect.collidepoint(mouse_pos):
                    # 리플레이 요청
                    self._request_replay()
                    return

            if not self.waiting_for_click:
                # 타이핑 스킵
                full_text = self.dialogue_after[self.current_dialogue_index].get(
                    "text", ""
                )
                self.dialogue_text = full_text
                self.waiting_for_click = True
            else:
                # 다음 대사 또는 완료
                self.current_dialogue_index += 1
                if self.current_dialogue_index >= len(self.dialogue_after):
                    self.phase = self.PHASE_FADEOUT
                    self.phase_timer = 0.0
                else:
                    self._prepare_dialogue(self.current_dialogue_index)

    def _request_replay(self):
        """리플레이 요청 - 회상 장면 재시작"""
        print(f"INFO: Replay requested for {self.scene_id}")

        # 콜백이 있으면 호출 (story_mode에서 새 인스턴스 생성)
        if self.on_replay_request:
            self.on_replay_request(self.scene_id)
        else:
            # 콜백 없으면 자체 리셋
            self._reset_for_replay()

    def _reset_for_replay(self):
        """리플레이를 위한 내부 상태 리셋"""
        # 페이즈 리셋
        self.phase = self.PHASE_FADEIN
        self.phase_timer = 0.0
        self.fade_alpha = 0.0

        # 사진 상태 리셋
        self.visible_count = 0
        self.photo_timer = 0.0

        # 폴라로이드 애니메이션 상태 리셋
        for p in self.polaroids:
            p["animation_progress"] = 0.0
            p["pos"][0], p["pos"][1] = p["start_pos"]
            p["alpha"] = 0
            p["scale"] = 0.5
            p["flicker_phase"] = 0.0

        # 줌 효과 리셋
        self.final_zoom_scale = 1.0
        self.final_zoom_alpha = 255
        self.current_zoom_index = 0
        self.final_photo_index = -1

        # 대사 상태 리셋
        self.current_dialogue_index = 0
        self.dialogue_text = ""
        self.typing_progress = 0.0
        self.waiting_for_click = False
        self.current_photo_dialogue_shown = False

        # 리플레이 버튼 상태 리셋
        self.replay_button_alpha = 0.0

        print(f"INFO: {self.scene_id} reset for replay")

    def skip(self):
        """전체 스킵"""
        self.phase = self.PHASE_FADEOUT
        self.phase_timer = 0.0

    def draw(self, screen: pygame.Surface):
        """렌더링"""
        if not self.is_alive and self.phase == self.PHASE_DONE:
            return

        # 배경
        if self.background:
            bg_copy = self.background.copy()
            bg_copy.set_alpha(int(255 * self.fade_alpha))
            screen.blit(bg_copy, (0, 0))
        else:
            screen.fill((30, 30, 40))

        # 어두운 오버레이
        overlay = pygame.Surface(self.screen_size, pygame.SRCALPHA)
        overlay.fill((0, 0, 0, int(150 * self.fade_alpha)))
        screen.blit(overlay, (0, 0))

        # FINAL_ZOOM 단계에서는 최종 사진만 확대 렌더링
        if self.phase == self.PHASE_FINAL_ZOOM and self.final_photo_index >= 0:
            final_p = self.polaroids[self.final_photo_index]
            # 원본 사진 이미지 사용 (프레임 없이)
            photo_img = final_p.get("photo_image")
            if photo_img:
                # 확대 적용
                zoom_w = int(photo_img.get_width() * self.final_zoom_scale)
                zoom_h = int(photo_img.get_height() * self.final_zoom_scale)
                if zoom_w > 0 and zoom_h > 0:
                    zoomed = pygame.transform.smoothscale(photo_img, (zoom_w, zoom_h))
                    zoomed.set_alpha(self.final_zoom_alpha)
                    # 화면 중앙에 배치
                    rect = zoomed.get_rect(
                        center=(self.screen_size[0] // 2, self.screen_size[1] // 2)
                    )
                    screen.blit(zoomed, rect)
            return  # FINAL_ZOOM에서는 다른 사진 렌더링 안함

        # 폴라로이드 사진들
        for i, p in enumerate(self.polaroids):
            if i >= self.visible_count and self.phase == self.PHASE_PHOTOS:
                continue
            if p["alpha"] <= 0:
                continue

            # 스케일 적용
            scaled_w = int(p["image"].get_width() * p["scale"])
            scaled_h = int(p["image"].get_height() * p["scale"])
            if scaled_w > 0 and scaled_h > 0:
                scaled = pygame.transform.smoothscale(p["image"], (scaled_w, scaled_h))
                scaled.set_alpha(int(p["alpha"]))

                rect = scaled.get_rect(center=p["pos"])
                screen.blit(scaled, rect)

        # 대사 (하단) - PHASE_PHOTOS에서도 폴라로이드별 대화 표시
        if (
            self.phase == self.PHASE_PHOTOS
            and self.dialogue_text
            and self.current_photo_dialogue_shown
        ):
            # 폴라로이드별 대화 표시
            self._draw_photo_dialogue(screen)
        elif (
            self.phase in [self.PHASE_DIALOGUE, self.PHASE_DISPLAY]
            and self.dialogue_text
        ):
            self._draw_dialogue(screen)

    def _draw_dialogue(self, screen: pygame.Surface):
        """대사 그리기 - 일반 에피소드 대화창 포맷 사용"""
        if self.current_dialogue_index >= len(self.dialogue_after):
            return

        current_dialogue = self.dialogue_after[self.current_dialogue_index]
        speaker = current_dialogue.get("speaker", "")

        # 초상화 가져오기
        portrait = self._get_portrait(speaker)

        # render_dialogue_box 사용 (일반 에피소드와 동일한 포맷)
        box_x, box_y, box_width, box_height = render_dialogue_box(
            screen=screen,
            screen_size=self.screen_size,
            fonts=self.fonts,
            dialogue=current_dialogue,
            dialogue_text=self.dialogue_text,
            typing_progress=len(self.dialogue_text),
            waiting_for_click=self.waiting_for_click,
            has_portrait=portrait is not None,
            portrait=portrait,
        )

        # 리플레이 버튼 (마지막 대사이고 클릭 대기 중일 때)
        is_last_dialogue = self.current_dialogue_index >= len(self.dialogue_after) - 1
        if is_last_dialogue and self.waiting_for_click:
            box_rect = pygame.Rect(box_x, box_y, box_width, box_height)
            self._draw_replay_button(screen, box_rect)

    def _draw_replay_button(
        self, screen: pygame.Surface, dialogue_box_rect: pygame.Rect
    ):
        """리플레이 버튼 그리기 - 대화 상자 내부 우측 하단"""
        font = self.fonts.get("small")
        if not font:
            return

        # 버튼 알파 페이드 인
        self.replay_button_alpha = min(1.0, self.replay_button_alpha + 0.05)

        # 버튼 크기 및 위치 (대화 상자 내부 우측 하단)
        button_text = "REPLAY"
        button_padding_x = 16
        button_padding_y = 8
        text_surf = font.render(button_text, True, (255, 255, 255))
        button_width = text_surf.get_width() + button_padding_x * 2
        button_height = text_surf.get_height() + button_padding_y * 2

        button_x = dialogue_box_rect.right - button_width - 15
        button_y = dialogue_box_rect.bottom - button_height - 10

        self.replay_button_rect = pygame.Rect(
            button_x, button_y, button_width, button_height
        )

        # 호버 체크
        mouse_pos = pygame.mouse.get_pos()
        self.replay_button_hover = self.replay_button_rect.collidepoint(mouse_pos)

        # 버튼 색상 (호버 시 더 밝게)
        if self.replay_button_hover:
            bg_color = (80, 120, 180, int(220 * self.replay_button_alpha))
            border_color = (150, 200, 255, int(255 * self.replay_button_alpha))
            text_color = (255, 255, 255)
        else:
            bg_color = (50, 70, 100, int(180 * self.replay_button_alpha))
            border_color = (100, 150, 200, int(200 * self.replay_button_alpha))
            text_color = (200, 220, 255)

        # 버튼 배경
        button_surf = pygame.Surface((button_width, button_height), pygame.SRCALPHA)
        pygame.draw.rect(
            button_surf, bg_color, (0, 0, button_width, button_height), border_radius=6
        )
        pygame.draw.rect(
            button_surf,
            border_color,
            (0, 0, button_width, button_height),
            2,
            border_radius=6,
        )

        # 아이콘 (재생 삼각형) + 텍스트
        icon_size = 10
        icon_x = button_padding_x - 2
        icon_y = button_height // 2

        # 재생 아이콘 (삼각형)
        icon_points = [
            (icon_x, icon_y - icon_size // 2),
            (icon_x, icon_y + icon_size // 2),
            (icon_x + icon_size, icon_y),
        ]
        pygame.draw.polygon(button_surf, text_color, icon_points)

        # 텍스트
        text_surf = font.render(button_text, True, text_color)
        text_x = icon_x + icon_size + 6
        text_y = (button_height - text_surf.get_height()) // 2
        button_surf.blit(text_surf, (text_x, text_y))

        screen.blit(button_surf, (button_x, button_y))

    def _draw_photo_dialogue(self, screen: pygame.Surface):
        """폴라로이드별 대화 그리기 (PHASE_PHOTOS 중 자동 표시) - 일반 에피소드 대화창 포맷 사용"""
        # 현재 폴라로이드 인덱스에 해당하는 대화 가져오기
        photo_index = self.visible_count - 1
        if photo_index < 0 or photo_index >= len(self.dialogue_per_photo):
            return

        current_dialogue = self.dialogue_per_photo[photo_index]
        speaker = current_dialogue.get("speaker", "")

        # 초상화 가져오기
        portrait = self._get_portrait(speaker)

        # render_dialogue_box 사용 (일반 에피소드와 동일한 포맷)
        render_dialogue_box(
            screen=screen,
            screen_size=self.screen_size,
            fonts=self.fonts,
            dialogue=current_dialogue,
            dialogue_text=self.dialogue_text,
            typing_progress=len(self.dialogue_text),
            waiting_for_click=False,  # PHASE_PHOTOS에서는 자동 진행
            has_portrait=portrait is not None,
            portrait=portrait,
        )


# =========================================================
# 비행선 진입 & 선회 애니메이션 (1막 오프닝)
# =========================================================
class ShatteredMirrorEffect(BaseCutsceneEffect):
    """
    Act 4 컷씬: 깨진 거울/기억 파편 효과

    특징:
    - 검은 배경에 떠다니는 거울 파편
    - 각 파편 안에 다른 이미지
    - 파편들이 천천히 회전하며 빛 반사
    - 마지막에 합쳐져서 완전한 그림 형성
    """

    # 추가 페이즈 상수 (베이스 클래스 확장)
    PHASE_FRAGMENTS = 10
    PHASE_ASSEMBLE = 11

    def __init__(
        self,
        screen_size: tuple,
        fragment_paths: list,
        background_path: str = None,
        dialogue_after: list = None,
        sound_manager=None,
        special_effects: dict = None,
        scene_id: str = "mirror_scene",
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

        self.fragment_paths = fragment_paths
        self.typing_speed = 25.0  # 오버라이드

        # 어두운 배경 오버레이 적용
        if background_path:
            self._load_background(background_path, overlay_alpha=220)

        # 파편 관련
        self.fragments = []
        self._prepare_fragments()

        self.frag_animation_progress = 0.0
        self.assemble_duration = 3.0

    def _prepare_fragments(self):
        """파편 이미지 준비"""
        screen_w, screen_h = self.screen_size
        frag_size = int(min(screen_w, screen_h) * 0.25)

        # 파편 위치들 (원형 배치)
        center_x, center_y = screen_w // 2, screen_h // 2 - 30
        radius = min(screen_w, screen_h) * 0.25

        for i, path in enumerate(self.fragment_paths):
            frag_img = None
            try:
                frag_img = pygame.image.load(path).convert_alpha()
                frag_img = pygame.transform.smoothscale(
                    frag_img, (frag_size, frag_size)
                )
            except Exception as e:
                print(f"WARNING: Failed to load fragment: {path} - {e}")
                frag_img = pygame.Surface((frag_size, frag_size), pygame.SRCALPHA)
                frag_img.fill((100, 100, 120, 200))

            filename = Path(path).name
            effect_info = self.special_effects.get(filename, {})
            is_final = effect_info.get("is_final", False)

            # 원형 배치 또는 최종 이미지
            if is_final:
                target_x, target_y = center_x, center_y
                start_x, start_y = center_x, center_y
            else:
                angle = (2 * math.pi * i) / max(len(self.fragment_paths) - 1, 1)
                target_x = center_x + radius * math.cos(angle)
                target_y = center_y + radius * math.sin(angle)
                # 시작 위치 (화면 밖에서)
                start_x = center_x + (radius * 2) * math.cos(angle)
                start_y = center_y + (radius * 2) * math.sin(angle)

            self.fragments.append(
                {
                    "image": frag_img,
                    "filename": filename,
                    "is_final": is_final,
                    "x": start_x,
                    "y": start_y,
                    "target_x": target_x,
                    "target_y": target_y,
                    "start_x": start_x,
                    "start_y": start_y,
                    "alpha": 0,
                    "rotation": random.uniform(0, 360),
                    "rotation_speed": random.uniform(-30, 30),
                    "scale": 0.5 if is_final else 1.0,
                    "glow": 0.0,
                }
            )

    # set_fonts는 베이스 클래스에서 상속

    def _on_fadein_complete(self):
        """페이드인 완료 후 파편 등장 페이즈로 전환"""
        self.phase = self.PHASE_FRAGMENTS
        self.phase_timer = 0.0

    def update(self, dt: float):
        """업데이트 - 파편 고유 로직 추가"""
        if not self.is_alive:
            return

        self.phase_timer += dt

        # 파편 회전 (항상 업데이트)
        for frag in self.fragments:
            if not frag["is_final"]:
                frag["rotation"] += frag["rotation_speed"] * dt
            frag["glow"] = 0.5 + 0.5 * math.sin(self.phase_timer * 2 + frag["rotation"])

        # 페이즈별 처리
        if self.phase == self.PHASE_FADEIN:
            if self._update_fadein(dt):
                self._on_fadein_complete()

        elif self.phase == self.PHASE_FRAGMENTS:
            self._update_fragments(dt)

        elif self.phase == self.PHASE_ASSEMBLE:
            self._update_assemble(dt)

        elif self.phase == self.PHASE_DIALOGUE:
            if self._update_dialogue(dt):
                self._transition_to_fadeout()

        elif self.phase == self.PHASE_FADEOUT:
            if self._update_fadeout(dt):
                self._on_fadeout_complete()

    def _update_fragments(self, dt: float):
        """파편 등장 애니메이션"""
        self.frag_animation_progress += dt * 1.2
        visible_count = int(self.frag_animation_progress)

        for i, frag in enumerate(self.fragments):
            if frag["is_final"]:
                continue
            if i < visible_count:
                progress = min(1.0, self.frag_animation_progress - i)
                eased = 1.0 - (1.0 - progress) ** 3
                frag["alpha"] = int(220 * eased)
                frag["x"] = (
                    frag["start_x"] + (frag["target_x"] - frag["start_x"]) * eased
                )
                frag["y"] = (
                    frag["start_y"] + (frag["target_y"] - frag["start_y"]) * eased
                )

        # 모든 파편 등장 후 클릭 대기
        non_final_count = sum(1 for f in self.fragments if not f["is_final"])
        if visible_count >= non_final_count:
            self.waiting_for_click = True

    def _update_assemble(self, dt: float):
        """파편 조립 애니메이션"""
        progress = min(1.0, self.phase_timer / self.assemble_duration)
        eased = 1.0 - (1.0 - progress) ** 2

        # 파편들이 중앙으로 모임
        for frag in self.fragments:
            if not frag["is_final"]:
                frag["alpha"] = int(220 * (1.0 - progress))
                frag["scale"] = 1.0 - 0.5 * progress
            else:
                # 최종 이미지 등장
                frag["alpha"] = int(255 * eased)
                frag["scale"] = 0.5 + 0.5 * eased

        if progress >= 1.0:
            self._transition_to_dialogue()

    def _handle_click(self) -> bool:
        """클릭 처리 - 파편 페이즈 추가"""
        if self.phase == self.PHASE_FRAGMENTS and self.waiting_for_click:
            self.phase = self.PHASE_ASSEMBLE
            self.phase_timer = 0.0
            self.waiting_for_click = False
            return True

        # 대화 페이즈는 베이스 클래스 로직 사용
        return super()._handle_click()

    def render(self, screen: pygame.Surface):
        """렌더링"""
        # 배경
        self._render_background(screen)

        # 파편들 (최종 이미지가 아닌 것들 먼저)
        for frag in self.fragments:
            if not frag["is_final"]:
                self._render_fragment(screen, frag)

        # 최종 이미지
        for frag in self.fragments:
            if frag["is_final"]:
                self._render_fragment(screen, frag)

        # 대사
        if self.phase == self.PHASE_DIALOGUE:
            self._render_dialogue(screen)

        # 안내
        if self.waiting_for_click and self.phase == self.PHASE_FRAGMENTS:
            self._render_click_hint(screen, "클릭하여 진실 확인")

    def _render_fragment(self, screen: pygame.Surface, frag: dict):
        if frag["alpha"] <= 0:
            return

        img = frag["image"]

        # 스케일
        scaled_w = int(img.get_width() * frag["scale"])
        scaled_h = int(img.get_height() * frag["scale"])
        if scaled_w <= 0 or scaled_h <= 0:
            return
        scaled = pygame.transform.smoothscale(img, (scaled_w, scaled_h))

        # 회전 (최종 이미지는 회전 안 함)
        if not frag["is_final"]:
            rotated = pygame.transform.rotate(scaled, frag["rotation"])
        else:
            rotated = scaled

        # 글로우 효과
        glow_surf = pygame.Surface(
            (rotated.get_width() + 20, rotated.get_height() + 20), pygame.SRCALPHA
        )
        glow_alpha = int(50 * frag["glow"])
        pygame.draw.rect(
            glow_surf,
            (150, 180, 255, glow_alpha),
            (0, 0, glow_surf.get_width(), glow_surf.get_height()),
            border_radius=5,
        )
        screen.blit(
            glow_surf,
            (
                frag["x"] - glow_surf.get_width() // 2,
                frag["y"] - glow_surf.get_height() // 2,
            ),
        )

        # 알파
        rotated.set_alpha(frag["alpha"])

        # 위치
        rect = rotated.get_rect(center=(frag["x"], frag["y"]))
        screen.blit(rotated, rect)

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
            box_color=(20, 25, 40, 230),
            border_color=(120, 140, 180),
            text_color=(220, 220, 240),
            box_height=180,
            has_portrait=(portrait is not None),
            portrait=portrait,
        )


# =========================================================
# Act 5: 성간 항해 인터페이스 효과 (BaseCutsceneEffect 상속)
# =========================================================
class DualMemoryEffect(BaseCutsceneEffect):
    """
    이중 회상 컷씬 (Act 3)

    특징:
    - 화면이 둘로 분할
    - 왼쪽: 행복했던 과거 (따뜻한 색조)
    - 오른쪽: 현재의 폐허 (차가운 색조)
    - 두 시간대가 동시에 보임
    """

    PHASE_SPLIT_SCREEN = 10
    PHASE_MERGE = 11

    def __init__(
        self,
        screen_size: tuple,
        past_image_path: str = None,
        present_image_path: str = None,
        dialogue_after: list = None,
        sound_manager=None,
        special_effects: dict = None,
        scene_id: str = "dual_memory_scene",
    ):
        super().__init__(
            screen_size, None, dialogue_after, sound_manager, special_effects, scene_id
        )

        self.typing_speed = 24.0

        # 과거/현재 이미지
        self.past_image = None
        self.present_image = None
        half_size = (screen_size[0] // 2, screen_size[1])

        if past_image_path:
            try:
                img = pygame.image.load(past_image_path).convert()
                self.past_image = pygame.transform.smoothscale(img, half_size)
            except:
                self._create_placeholder_past(half_size)
        else:
            self._create_placeholder_past(half_size)

        if present_image_path:
            try:
                img = pygame.image.load(present_image_path).convert()
                self.present_image = pygame.transform.smoothscale(img, half_size)
            except:
                self._create_placeholder_present(half_size)
        else:
            self._create_placeholder_present(half_size)

        # 분할선 위치
        self.split_x = screen_size[0] // 2
        self.split_wave = 0.0

        # 파티클 (과거: 따뜻한 빛, 현재: 재)
        self.past_particles = []
        self.present_particles = []
        self._create_particles()

        # 색상 오버레이
        self.past_tint = (255, 230, 200)  # 따뜻한 세피아
        self.present_tint = (150, 170, 200)  # 차가운 블루

    def _create_placeholder_past(self, size):
        """과거 이미지 대체"""
        surf = pygame.Surface(size)
        # 따뜻한 그라데이션
        for y in range(size[1]):
            ratio = y / size[1]
            r = int(255 - ratio * 50)
            g = int(200 - ratio * 50)
            b = int(150 - ratio * 50)
            pygame.draw.line(surf, (r, g, b), (0, y), (size[0], y))

        # 집 실루엣
        house_color = (200, 180, 150)
        pygame.draw.rect(surf, house_color, (100, 300, 200, 150))
        pygame.draw.polygon(surf, house_color, [(100, 300), (200, 200), (300, 300)])

        # 태양
        pygame.draw.circle(surf, (255, 220, 100), (350, 100), 50)

        self.past_image = surf

    def _create_placeholder_present(self, size):
        """현재 이미지 대체"""
        surf = pygame.Surface(size)
        # 차가운 그라데이션
        for y in range(size[1]):
            ratio = y / size[1]
            r = int(40 + ratio * 20)
            g = int(50 + ratio * 20)
            b = int(70 + ratio * 20)
            pygame.draw.line(surf, (r, g, b), (0, y), (size[0], y))

        # 폐허 실루엣
        ruin_color = (60, 55, 50)
        # 무너진 건물
        pygame.draw.rect(surf, ruin_color, (80, 320, 100, 130))
        pygame.draw.rect(surf, ruin_color, (200, 280, 80, 170))
        # 잔해
        for i in range(10):
            x = random.randint(50, 350)
            y = random.randint(400, 450)
            w = random.randint(20, 50)
            h = random.randint(10, 30)
            pygame.draw.rect(surf, (50, 45, 40), (x, y, w, h))

        self.present_image = surf

    def _create_particles(self):
        """파티클 생성"""
        half_w = self.screen_size[0] // 2

        # 과거: 빛나는 먼지
        for _ in range(30):
            self.past_particles.append(
                {
                    "x": random.randint(0, half_w),
                    "y": random.randint(0, self.screen_size[1]),
                    "size": random.uniform(2, 4),
                    "speed": random.uniform(-20, 20),
                    "alpha": random.randint(100, 200),
                }
            )

        # 현재: 재/연기
        for _ in range(40):
            self.present_particles.append(
                {
                    "x": random.randint(half_w, self.screen_size[0]),
                    "y": random.randint(0, self.screen_size[1]),
                    "size": random.uniform(3, 6),
                    "speed_y": random.uniform(-30, -10),
                    "speed_x": random.uniform(-10, 10),
                    "alpha": random.randint(50, 100),
                }
            )

    def _on_fadein_complete(self):
        """페이드인 완료"""
        self.phase = self.PHASE_SPLIT_SCREEN
        self.phase_timer = 0.0

    def update(self, dt: float):
        """업데이트"""
        if not self.is_alive:
            return

        self.phase_timer += dt

        # 분할선 웨이브
        self.split_wave += dt * 3
        wave_offset = int(math.sin(self.split_wave) * 5)

        # 파티클 업데이트
        for p in self.past_particles:
            p["y"] += p["speed"] * dt
            if p["y"] < 0 or p["y"] > self.screen_size[1]:
                p["speed"] = -p["speed"]

        for p in self.present_particles:
            p["y"] += p["speed_y"] * dt
            p["x"] += p["speed_x"] * dt
            if p["y"] < -10:
                p["y"] = self.screen_size[1] + 10
                p["x"] = random.randint(self.screen_size[0] // 2, self.screen_size[0])

        # 페이즈 처리
        if self.phase == self.PHASE_FADEIN:
            if self._update_fadein(dt):
                self._on_fadein_complete()

        elif self.phase == self.PHASE_SPLIT_SCREEN:
            if self.phase_timer > 4.0:
                self._transition_to_dialogue()

        elif self.phase == self.PHASE_DIALOGUE:
            if self._update_dialogue(dt):
                self._transition_to_fadeout()

        elif self.phase == self.PHASE_FADEOUT:
            if self._update_fadeout(dt):
                self._on_fadeout_complete()

    def render(self, screen: pygame.Surface):
        """렌더링"""
        half_w = self.screen_size[0] // 2

        # 과거 (왼쪽)
        if self.past_image:
            screen.blit(self.past_image, (0, 0))
            # 따뜻한 오버레이
            warm_overlay = pygame.Surface(
                (half_w, self.screen_size[1]), pygame.SRCALPHA
            )
            warm_overlay.fill((*self.past_tint, 30))
            screen.blit(warm_overlay, (0, 0))

        # 현재 (오른쪽)
        if self.present_image:
            screen.blit(self.present_image, (half_w, 0))
            # 차가운 오버레이
            cold_overlay = pygame.Surface(
                (half_w, self.screen_size[1]), pygame.SRCALPHA
            )
            cold_overlay.fill((*self.present_tint, 40))
            screen.blit(cold_overlay, (half_w, 0))

        # 과거 파티클 (빛)
        for p in self.past_particles:
            glow_surf = pygame.Surface(
                (int(p["size"] * 4), int(p["size"] * 4)), pygame.SRCALPHA
            )
            pygame.draw.circle(
                glow_surf,
                (255, 240, 200, p["alpha"]),
                (int(p["size"] * 2), int(p["size"] * 2)),
                int(p["size"]),
            )
            screen.blit(glow_surf, (int(p["x"]), int(p["y"])))

        # 현재 파티클 (재)
        for p in self.present_particles:
            pygame.draw.circle(
                screen,
                (80, 80, 80, p["alpha"]),
                (int(p["x"]), int(p["y"])),
                int(p["size"]),
            )

        # 분할선 (글로우 효과)
        wave_offset = int(math.sin(self.split_wave) * 5)
        for i in range(-10, 11, 2):
            alpha = 255 - abs(i) * 20
            x = half_w + wave_offset + i
            pygame.draw.line(
                screen,
                (255, 255, 255, max(0, alpha)),
                (x, 0),
                (x, self.screen_size[1]),
                1,
            )

        # 레이블
        if self.phase == self.PHASE_SPLIT_SCREEN and "medium" in self.fonts:
            past_label = self.fonts["medium"].render("과거", True, self.past_tint)
            present_label = self.fonts["medium"].render("현재", True, self.present_tint)

            screen.blit(past_label, (half_w // 2 - past_label.get_width() // 2, 30))
            screen.blit(
                present_label,
                (half_w + half_w // 2 - present_label.get_width() // 2, 30),
            )

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
            box_color=(30, 30, 40, 230),
            border_color=(200, 200, 220),
            text_color=(255, 255, 255),
            box_height=180,
            has_portrait=(portrait is not None),
            portrait=portrait,
        )


class SeasonMemoryEffect(BaseCutsceneEffect):
    """
    계절 기억 컷씬: 빠른 계절 전환 효과

    특징:
    - 봄/여름/가을/겨울 이미지 빠르게 전환
    - 각 계절에 맞는 파티클 효과
    - 감정과 연결된 대사
    """

    PHASE_SEASONS = 10

    def __init__(
        self,
        screen_size: tuple,
        season_images: list = None,
        dialogue_after: list = None,
        sound_manager=None,
        special_effects: dict = None,
        scene_id: str = "season_memory_scene",
    ):
        super().__init__(
            screen_size, None, dialogue_after, sound_manager, special_effects, scene_id
        )

        self.typing_speed = 25.0

        # 계절 이미지 (봄, 여름, 가을, 겨울)
        self.season_images = []
        self.season_names = ["봄", "여름", "가을", "겨울"]
        self.season_colors = [
            (255, 200, 220),  # 봄: 분홍
            (100, 200, 100),  # 여름: 초록
            (255, 180, 100),  # 가을: 주황
            (200, 220, 255),  # 겨울: 하늘색
        ]

        if season_images:
            for path in season_images:
                try:
                    img = pygame.image.load(path).convert()
                    img = pygame.transform.smoothscale(img, screen_size)
                    self.season_images.append(img)
                except:
                    # 대체 색상 배경
                    surf = pygame.Surface(screen_size)
                    idx = len(self.season_images) % 4
                    surf.fill(self.season_colors[idx])
                    self.season_images.append(surf)

        # 최소 4개 보장
        while len(self.season_images) < 4:
            surf = pygame.Surface(screen_size)
            surf.fill(self.season_colors[len(self.season_images)])
            self.season_images.append(surf)

        # 현재 계절 인덱스
        self.current_season = 0
        self.season_timer = 0.0
        self.season_duration = 2.0  # 각 계절 표시 시간
        self.transition_duration = 0.5  # 전환 시간
        self.transitioning = False
        self.transition_progress = 0.0

        # 파티클 (계절별)
        self.particles = []
        self._create_season_particles()

    def _create_season_particles(self):
        """계절별 파티클 생성"""
        self.particles = []
        for _ in range(40):
            self.particles.append(
                {
                    "x": random.randint(0, self.screen_size[0]),
                    "y": random.randint(-50, self.screen_size[1]),
                    "size": random.randint(3, 8),
                    "speed_y": random.uniform(30, 80),
                    "speed_x": random.uniform(-30, 30),
                    "rotation": random.uniform(0, 360),
                    "rot_speed": random.uniform(-180, 180),
                }
            )

    def _on_fadein_complete(self):
        """페이드인 완료 후 계절 전환 페이즈"""
        self.phase = self.PHASE_SEASONS
        self.phase_timer = 0.0
        self.current_season = 0

    def update(self, dt: float):
        """업데이트"""
        if not self.is_alive:
            return

        self.phase_timer += dt

        # 파티클 이동
        for p in self.particles:
            p["y"] += p["speed_y"] * dt
            p["x"] += p["speed_x"] * dt
            p["rotation"] += p["rot_speed"] * dt
            if p["y"] > self.screen_size[1] + 50:
                p["y"] = -50
                p["x"] = random.randint(0, self.screen_size[0])

        # 페이즈 처리
        if self.phase == self.PHASE_FADEIN:
            if self._update_fadein(dt):
                self._on_fadein_complete()

        elif self.phase == self.PHASE_SEASONS:
            self.season_timer += dt

            if self.transitioning:
                self.transition_progress = min(
                    1.0, self.transition_progress + dt / self.transition_duration
                )
                if self.transition_progress >= 1.0:
                    self.transitioning = False
                    self.current_season = (self.current_season + 1) % 4
                    self.season_timer = 0.0
                    self.transition_progress = 0.0

                    # 4계절 완료 시 대화로 전환
                    if self.current_season == 0:
                        self._transition_to_dialogue()
            else:
                if self.season_timer >= self.season_duration:
                    self.transitioning = True
                    self.transition_progress = 0.0

        elif self.phase == self.PHASE_DIALOGUE:
            if self._update_dialogue(dt):
                self._transition_to_fadeout()

        elif self.phase == self.PHASE_FADEOUT:
            if self._update_fadeout(dt):
                self._on_fadeout_complete()

    def render(self, screen: pygame.Surface):
        """렌더링"""
        # 현재 계절 배경
        if self.season_images:
            current_img = self.season_images[self.current_season]

            if self.transitioning and len(self.season_images) > 1:
                # 페이드 전환
                next_season = (self.current_season + 1) % len(self.season_images)
                next_img = self.season_images[next_season]

                current_img.set_alpha(int(255 * (1 - self.transition_progress)))
                screen.blit(current_img, (0, 0))

                next_img.set_alpha(int(255 * self.transition_progress))
                screen.blit(next_img, (0, 0))
            else:
                current_img.set_alpha(int(self.fade_alpha))
                screen.blit(current_img, (0, 0))

        # 계절 파티클
        self._render_particles(screen)

        # 계절 이름
        if self.phase == self.PHASE_SEASONS and "large" in self.fonts:
            season_name = self.season_names[self.current_season]
            color = self.season_colors[self.current_season]

            # 글로우 효과
            glow_alpha = int(
                150 * (1 - self.transition_progress if self.transitioning else 1)
            )
            text = self.fonts["large"].render(season_name, True, color)
            text.set_alpha(glow_alpha)

            x = self.screen_size[0] // 2 - text.get_width() // 2
            y = 50
            screen.blit(text, (x, y))

        # 대사
        if self.phase == self.PHASE_DIALOGUE:
            self._render_dialogue(screen)

    def _render_particles(self, screen: pygame.Surface):
        """계절별 파티클 렌더링"""
        season = self.current_season

        for p in self.particles:
            if season == 0:  # 봄: 꽃잎
                self._render_petal(screen, p, (255, 200, 220))
            elif season == 1:  # 여름: 나뭇잎
                self._render_leaf(screen, p, (100, 200, 100))
            elif season == 2:  # 가을: 낙엽
                self._render_leaf(screen, p, (255, 150, 50))
            elif season == 3:  # 겨울: 눈
                self._render_snow(screen, p)

    def _render_petal(self, screen: pygame.Surface, p: dict, color: tuple):
        """꽃잎 렌더링"""
        size = p["size"]
        surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
        pygame.draw.ellipse(surf, (*color, 200), (0, size // 2, size * 2, size))
        rotated = pygame.transform.rotate(surf, p["rotation"])
        rect = rotated.get_rect(center=(p["x"], p["y"]))
        screen.blit(rotated, rect)

    def _render_leaf(self, screen: pygame.Surface, p: dict, color: tuple):
        """나뭇잎 렌더링"""
        size = p["size"]
        surf = pygame.Surface((size * 2, size), pygame.SRCALPHA)
        # 잎 모양 (다이아몬드)
        points = [(size, 0), (size * 2, size // 2), (size, size), (0, size // 2)]
        pygame.draw.polygon(surf, (*color, 200), points)
        rotated = pygame.transform.rotate(surf, p["rotation"])
        rect = rotated.get_rect(center=(p["x"], p["y"]))
        screen.blit(rotated, rect)

    def _render_snow(self, screen: pygame.Surface, p: dict):
        """눈 렌더링"""
        alpha = int(200 * (self.fade_alpha / 255))
        pygame.draw.circle(
            screen, (255, 255, 255, alpha), (int(p["x"]), int(p["y"])), p["size"]
        )

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
            box_color=(30, 25, 40, 230),
            border_color=(200, 180, 150),
            text_color=(255, 250, 240),
            box_height=180,
            has_portrait=(portrait is not None),
            portrait=portrait,
        )


class BrokenToyEffect(BaseCutsceneEffect):
    """
    부서진 장난감 컷씬 (Act 1)

    특징:
    - 폐허 속에서 발견된 낡은 인형/장난감
    - 천천히 떨어지는 먼지 파티클
    - 그을린 자국, 찢어진 부분 강조
    - 아르테미스의 어린 시절 회상 연결
    """

    PHASE_ZOOM_IN = 10
    PHASE_MEMORIES = 11

    def __init__(
        self,
        screen_size: tuple,
        toy_image_path: str = None,
        dialogue_after: list = None,
        sound_manager=None,
        special_effects: dict = None,
        scene_id: str = "broken_toy_scene",
    ):
        super().__init__(
            screen_size, None, dialogue_after, sound_manager, special_effects, scene_id
        )

        self.typing_speed = 25.0

        # 장난감 이미지
        self.toy_image = None
        self.toy_size = (200, 200)
        self.toy_pos = (screen_size[0] // 2, screen_size[1] // 2)
        self.toy_rotation = 15  # 약간 기울어진 모습

        if toy_image_path:
            try:
                img = pygame.image.load(toy_image_path).convert_alpha()
                self.toy_image = pygame.transform.smoothscale(img, self.toy_size)
            except:
                self._create_placeholder_toy()
        else:
            self._create_placeholder_toy()

        # 줌 애니메이션
        self.zoom_scale = 0.3
        self.target_zoom = 1.0
        self.zoom_speed = 0.5

        # 먼지 파티클
        self.dust_particles = []
        for _ in range(50):
            self.dust_particles.append(
                {
                    "x": random.randint(0, screen_size[0]),
                    "y": random.randint(0, screen_size[1]),
                    "size": random.uniform(1, 3),
                    "speed_y": random.uniform(5, 15),
                    "speed_x": random.uniform(-5, 5),
                    "alpha": random.randint(50, 150),
                }
            )

        # 회상 플래시 효과
        self.flash_alpha = 0
        self.flash_timer = 0.0
        self.memory_flashes = []  # 짧은 회상 이미지들

        # 배경 색상 (폐허/어두운 톤)
        self.bg_color = (30, 25, 20)

    def _create_placeholder_toy(self):
        """대체 장난감 이미지 생성 (곰인형 형태)"""
        surf = pygame.Surface(self.toy_size, pygame.SRCALPHA)

        # 몸통
        body_color = (139, 90, 43, 200)
        pygame.draw.ellipse(surf, body_color, (50, 80, 100, 110))

        # 머리
        pygame.draw.circle(surf, body_color, (100, 60), 45)

        # 귀
        pygame.draw.circle(surf, body_color, (60, 25), 18)
        pygame.draw.circle(surf, body_color, (140, 25), 18)

        # 눈 (하나는 X표시 - 부서진 느낌)
        pygame.draw.circle(surf, (20, 20, 20), (85, 55), 8)
        # X 표시 눈
        pygame.draw.line(surf, (20, 20, 20), (107, 47), (123, 63), 3)
        pygame.draw.line(surf, (20, 20, 20), (107, 63), (123, 47), 3)

        # 코
        pygame.draw.circle(surf, (60, 40, 30), (100, 75), 6)

        # 찢어진 자국 (대각선 선들)
        tear_color = (80, 50, 30, 150)
        pygame.draw.line(surf, tear_color, (70, 100), (90, 140), 2)
        pygame.draw.line(surf, tear_color, (85, 95), (75, 130), 2)

        # 그을린 자국
        burn_surf = pygame.Surface((40, 40), pygame.SRCALPHA)
        pygame.draw.circle(burn_surf, (40, 30, 25, 100), (20, 20), 20)
        surf.blit(burn_surf, (110, 120))

        self.toy_image = surf

    def _on_fadein_complete(self):
        """페이드인 완료 후 줌인 시작"""
        self.phase = self.PHASE_ZOOM_IN
        self.phase_timer = 0.0

    def update(self, dt: float):
        """업데이트"""
        if not self.is_alive:
            return

        self.phase_timer += dt

        # 먼지 파티클 업데이트
        for p in self.dust_particles:
            p["y"] += p["speed_y"] * dt
            p["x"] += p["speed_x"] * dt
            if p["y"] > self.screen_size[1]:
                p["y"] = -10
                p["x"] = random.randint(0, self.screen_size[0])

        # 회상 플래시 효과
        self.flash_timer += dt
        if self.phase == self.PHASE_MEMORIES:
            if self.flash_timer > 2.0:
                self.flash_alpha = max(0, self.flash_alpha - 200 * dt)
                if random.random() < 0.02:
                    self.flash_alpha = 100
                    self.flash_timer = 0

        # 페이즈 처리
        if self.phase == self.PHASE_FADEIN:
            if self._update_fadein(dt):
                self._on_fadein_complete()

        elif self.phase == self.PHASE_ZOOM_IN:
            # 줌인 애니메이션
            self.zoom_scale = min(
                self.target_zoom, self.zoom_scale + self.zoom_speed * dt
            )
            if self.zoom_scale >= self.target_zoom:
                self.phase = self.PHASE_MEMORIES
                self.phase_timer = 0.0
                # 2초 후 대화로 전환
            if self.phase == self.PHASE_MEMORIES and self.phase_timer > 2.0:
                self._transition_to_dialogue()

        elif self.phase == self.PHASE_MEMORIES:
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
        # 배경
        screen.fill(self.bg_color)

        # 폐허 느낌의 그라데이션
        for i in range(20):
            alpha = 10 + i * 3
            y = self.screen_size[1] - i * 30
            pygame.draw.rect(
                screen, (40 + i * 2, 35 + i, 30), (0, y, self.screen_size[0], 30)
            )

        # 먼지 파티클
        for p in self.dust_particles:
            color = (180, 170, 150, p["alpha"])
            surf = pygame.Surface(
                (int(p["size"] * 2), int(p["size"] * 2)), pygame.SRCALPHA
            )
            pygame.draw.circle(
                surf, color, (int(p["size"]), int(p["size"])), int(p["size"])
            )
            screen.blit(surf, (int(p["x"]), int(p["y"])))

        # 장난감
        if self.toy_image:
            scaled_size = (
                int(self.toy_size[0] * self.zoom_scale),
                int(self.toy_size[1] * self.zoom_scale),
            )
            scaled_toy = pygame.transform.smoothscale(self.toy_image, scaled_size)
            rotated_toy = pygame.transform.rotate(scaled_toy, self.toy_rotation)

            toy_rect = rotated_toy.get_rect(center=self.toy_pos)
            screen.blit(rotated_toy, toy_rect)

            # 스포트라이트 효과
            if self.phase in [self.PHASE_ZOOM_IN, self.PHASE_MEMORIES]:
                spotlight = pygame.Surface(self.screen_size, pygame.SRCALPHA)
                center = self.toy_pos
                for r in range(150, 0, -10):
                    alpha = int(30 * (r / 150))
                    pygame.draw.circle(spotlight, (255, 240, 200, alpha), center, r)
                screen.blit(spotlight, (0, 0))

        # 회상 플래시
        if self.flash_alpha > 0:
            flash_surf = pygame.Surface(self.screen_size, pygame.SRCALPHA)
            flash_surf.fill((255, 255, 255, int(self.flash_alpha)))
            screen.blit(flash_surf, (0, 0))

        # 비네트 효과
        vignette = pygame.Surface(self.screen_size, pygame.SRCALPHA)
        for i in range(100):
            alpha = int(i * 1.5)
            pygame.draw.rect(
                vignette,
                (0, 0, 0, alpha),
                (i, i, self.screen_size[0] - i * 2, self.screen_size[1] - i * 2),
                1,
            )
        screen.blit(vignette, (0, 0))

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
            box_color=(40, 30, 25, 230),
            border_color=(150, 120, 80),
            text_color=(255, 250, 240),
            box_height=180,
            has_portrait=(portrait is not None),
            portrait=portrait,
        )


