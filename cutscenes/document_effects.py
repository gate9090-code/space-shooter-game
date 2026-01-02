"""
cutscenes/document_effects.py
Document-related cutscene effects (classified documents, burning records, film reels)
"""

import pygame
import math
import random
from pathlib import Path
from cutscenes.base import BaseCutsceneEffect, render_dialogue_box


class ClassifiedDocumentEffect:
    """
    Act 2 컷씬: 기밀 문서 뷰어 효과

    새로운 연출 순서:
    1. 건물 중앙 검은문으로 천천히 클로즈업
    2. gate01~04 전체화면으로 자연스럽게 연결
    3. gate 연출 후 캐비닛 등장
    4. 대화 클릭마다 문서 등장 및 화면에 쌓임
    5. 모든 문서 쌓인 후 각 문서 확대→축소→정렬
    6. 대화 종료시 원래 배경으로 복귀
    """

    # 페이즈 정의
    PHASE_ZOOM_IN = 0  # 배경 건물 중앙으로 클로즈업
    PHASE_GATE_SEQUENCE = 1  # gate 이미지 시퀀스 (전체화면 전환)
    PHASE_CABINET_SHOW = 2  # 캐비닛 등장
    PHASE_DIALOGUE = 3  # 대화 + 문서 등장
    PHASE_DOC_REVIEW = 4  # 모든 문서 즉각 정렬
    PHASE_DOC_VIEW = 5  # 정렬 후 대기 - 클릭으로 문서 확대 보기
    PHASE_ZOOM_OUT = 6  # 원래 배경으로 복귀
    PHASE_DONE = 7

    def __init__(
        self,
        screen_size: tuple,
        document_paths: list,
        background_path: str = None,
        dialogue_after: list = None,
        sound_manager=None,
        special_effects: dict = None,
        scene_id: str = "document_scene",
        gate_image_paths: list = None,
    ):
        self.screen_size = screen_size
        self.document_paths = document_paths
        self.background_path = background_path
        self.dialogue_after = dialogue_after or []
        self.sound_manager = sound_manager
        self.special_effects = special_effects or {}
        self.scene_id = scene_id

        self.is_alive = True
        self.phase = self.PHASE_ZOOM_IN
        self.phase_timer = 0.0

        # gate 이미지 경로 (에피소드 리소스 시스템)
        self.gate_image_paths = gate_image_paths or [
            "assets/data/episodes/ep1/cutscene_images/bunker_gate_01.jpg",
            "assets/data/episodes/ep1/cutscene_images/bunker_gate_02.jpg",
            "assets/data/episodes/ep1/cutscene_images/bunker_gate_03.jpg",
        ]

        # 타이밍 설정 (모든 등장 천천히)
        self.zoom_in_duration = 4.5  # 클로즈업 시간 (더 느리게)
        self.gate_transition_duration = 3.0  # 각 gate 이미지 전환 시간 (느리게)
        self.gate_display_duration = 2.5  # 각 gate 이미지 표시 시간 (더 오래)
        self.cabinet_show_duration = 2.0  # 캐비닛 등장 시간 (천천히)
        self.doc_rise_duration = 1.5  # 문서 솟아오르는 시간 (천천히)
        self.doc_review_duration = 0.15  # 각 문서 정렬 시간 (거의 즉각)
        self.zoom_out_duration = 4.0  # 줌아웃 시간 (천천히)

        # 줌 효과
        self.zoom_scale = 1.0  # 현재 줌 배율
        self.zoom_target_scale = 3.0  # 목표 줌 배율 (더 깊이)
        self.zoom_center_x = 0.5  # 줌 중심 X (건물 중앙)
        self.zoom_center_y = 0.38  # 줌 중심 Y (건물 문 위치)

        # 배경
        self.background_original = None
        self.background = None
        if background_path:
            self._load_background(background_path)

        # gate 이미지들
        self.gate_images = []
        self.current_gate_index = 0
        self.gate_transition_progress = 0.0
        self.gate_display_timer = 0.0
        self.gate_state = "display"  # "display" or "transition"
        self._load_gate_images()

        # 캐비닛 이미지
        self.cabinet_image = None
        self.cabinet_y_offset = 0.0
        self._load_cabinet()

        # 문서들
        self.documents = []
        self.doc_final_positions = []  # 정렬된 최종 위치 (먼저 초기화)
        self._prepare_documents()

        # 현재 표시 중인 문서
        self.current_doc_index = -1
        self.doc_rise_progress = 0.0
        self.doc_is_rising = False

        # 문서 리뷰 관련 (즉각 정렬)
        self.review_doc_index = 0
        self.review_state = "arrange_all"  # "arrange_all" (즉각 정렬)
        self.review_progress = 0.0

        # 문서 확대 보기 관련 (PHASE_DOC_VIEW)
        self.viewing_doc_index = -1  # 현재 확대 보기 중인 문서 (-1이면 없음)
        self.view_zoom_progress = 0.0  # 확대/축소 애니메이션 진행도
        self.view_zoom_duration = 0.25  # 확대 애니메이션 시간 (빠르게)
        self.view_state = "idle"  # "idle", "zoom_in", "viewing", "zoom_out"
        self.doc_rects = []  # 각 문서의 클릭 영역

        # 대사 관련
        self.current_dialogue_index = 0
        self.dialogue_text = ""
        self.typing_progress = 0.0
        self.typing_speed = 30.0
        self.waiting_for_click = False

        # 초상화 캐시
        self.portrait_cache = {}

        # 폰트
        self.fonts = {}

        # 콜백
        self.on_complete = None
        self.on_replay_request = None

        # 페이드 효과용
        self.fade_alpha = 0.0

        print(
            f"INFO: ClassifiedDocumentEffect created with {len(self.document_paths)} documents, {len(self.gate_image_paths)} gate images"
        )

    def _load_background(self, path: str):
        """배경 이미지 로드"""
        try:
            img = pygame.image.load(path).convert()
            self.background_original = pygame.transform.smoothscale(
                img, self.screen_size
            )
            self.background = self.background_original.copy()
        except Exception as e:
            print(f"WARNING: Failed to load background: {path} - {e}")
            self.background_original = pygame.Surface(self.screen_size)
            self.background_original.fill((30, 35, 40))
            self.background = self.background_original.copy()

    def _load_gate_images(self):
        """gate 이미지들 로드 (전체화면용)"""
        for path in self.gate_image_paths:
            try:
                img = pygame.image.load(path).convert()
                img = pygame.transform.smoothscale(img, self.screen_size)
                self.gate_images.append(img)
            except Exception as e:
                print(f"WARNING: Failed to load gate image: {path} - {e}")
                # 플레이스홀더
                placeholder = pygame.Surface(self.screen_size)
                placeholder.fill((40, 45, 50))
                self.gate_images.append(placeholder)

        if not self.gate_images:
            # gate 이미지가 하나도 없으면 플레이스홀더 추가
            placeholder = pygame.Surface(self.screen_size)
            placeholder.fill((40, 45, 50))
            self.gate_images.append(placeholder)

    def _load_cabinet(self):
        """캐비닛 이미지 로드"""
        cabinet_path = "assets/data/episodes/ep1/cutscene_images/doc_cabinet.png"
        try:
            img = pygame.image.load(cabinet_path).convert_alpha()
            cabinet_height = int(self.screen_size[1] * 0.55)
            orig_w, orig_h = img.get_size()
            ratio = cabinet_height / orig_h
            cabinet_width = int(orig_w * ratio)
            self.cabinet_image = pygame.transform.smoothscale(
                img, (cabinet_width, cabinet_height)
            )
        except Exception as e:
            print(f"WARNING: Failed to load cabinet: {cabinet_path} - {e}")
            cabinet_width = int(self.screen_size[0] * 0.35)
            cabinet_height = int(self.screen_size[1] * 0.55)
            self.cabinet_image = pygame.Surface(
                (cabinet_width, cabinet_height), pygame.SRCALPHA
            )
            pygame.draw.rect(
                self.cabinet_image, (50, 55, 60), (0, 0, cabinet_width, cabinet_height)
            )
            pygame.draw.rect(
                self.cabinet_image,
                (80, 85, 90),
                (0, 0, cabinet_width, cabinet_height),
                3,
            )
            for i in range(3):
                handle_y = 80 + i * (cabinet_height // 4)
                pygame.draw.rect(
                    self.cabinet_image,
                    (100, 105, 110),
                    (cabinet_width // 2 - 30, handle_y, 60, 15),
                )

    def _prepare_documents(self):
        """문서 이미지 준비 - 원본 비율 유지, 특정 문서만 높이 조정"""
        screen_w, screen_h = self.screen_size

        # 문서 최대 크기
        max_width = int(screen_w * 0.26)
        max_height = int(screen_h * 0.58)

        # 문서 1, 2만 높이 줄임 (파일명 기준)
        height_reduction = {
            "doc_project_ark.png": 0.80,  # 문서 1: 높이 80%로 줄임
            "doc_survivor_list.png": 0.80,  # 문서 2: 높이 80%로 줄임
        }

        # 문서 4만 약간 확대
        scale_up = {
            "doc_transmission.png": 1.05,  # 문서 4: 5% 확대
        }

        for i, path in enumerate(self.document_paths):
            doc_img = None
            filename = Path(path).name

            try:
                doc_img = pygame.image.load(path).convert_alpha()
                orig_w, orig_h = doc_img.get_size()

                # 비율 유지하면서 최대 크기에 맞춤
                ratio = min(max_width / orig_w, max_height / orig_h)

                # 문서 4 확대
                if filename in scale_up:
                    ratio *= scale_up[filename]

                new_w = int(orig_w * ratio)
                new_h = int(orig_h * ratio)

                # 문서 1, 2만 높이 줄임
                if filename in height_reduction:
                    new_h = int(new_h * height_reduction[filename])

                doc_img = pygame.transform.smoothscale(doc_img, (new_w, new_h))
            except Exception as e:
                print(f"WARNING: Failed to load document: {path} - {e}")
                doc_img = pygame.Surface((max_width, max_height), pygame.SRCALPHA)
                doc_img.fill((200, 190, 170))

            self.documents.append(
                {
                    "image": doc_img,
                    "filename": filename,
                    "y_offset": 0.0,
                    "alpha": 255,
                    "visible": False,
                    "scale": 1.0,
                    "pos_x": screen_w // 2,
                    "pos_y": screen_h // 2,
                }
            )

        # 문서 최종 정렬 위치 계산 (가로로 나열)
        self._calculate_final_positions()

    def _calculate_final_positions(self):
        """문서들의 최종 정렬 위치 계산"""
        screen_w, screen_h = self.screen_size
        num_docs = len(self.documents)

        if num_docs == 0:
            return

        # 문서들을 가로로 나열 (축소해서)
        total_width = screen_w * 0.8
        spacing = total_width / (num_docs + 1)
        start_x = screen_w * 0.1 + spacing

        for i in range(num_docs):
            self.doc_final_positions.append(
                {
                    "x": start_x + i * spacing,
                    "y": screen_h * 0.45,
                    "scale": 0.5,  # 축소 비율
                }
            )

    def set_fonts(self, fonts: dict):
        """폰트 설정"""
        self.fonts = fonts

    def update(self, dt: float):
        """업데이트"""
        if not self.is_alive:
            return

        self.phase_timer += dt

        if self.phase == self.PHASE_ZOOM_IN:
            self._update_zoom_in(dt)

        elif self.phase == self.PHASE_GATE_SEQUENCE:
            self._update_gate_sequence(dt)

        elif self.phase == self.PHASE_CABINET_SHOW:
            self._update_cabinet_show(dt)

        elif self.phase == self.PHASE_DIALOGUE:
            self._update_dialogue_phase(dt)

        elif self.phase == self.PHASE_DOC_REVIEW:
            self._update_doc_review(dt)

        elif self.phase == self.PHASE_DOC_VIEW:
            self._update_doc_view(dt)

        elif self.phase == self.PHASE_ZOOM_OUT:
            self._update_zoom_out(dt)

    def _update_zoom_in(self, dt: float):
        """배경 클로즈업 업데이트"""
        progress = min(1.0, self.phase_timer / self.zoom_in_duration)
        # ease-out cubic (천천히 감속)
        eased = 1.0 - (1.0 - progress) ** 3
        self.zoom_scale = 1.0 + (self.zoom_target_scale - 1.0) * eased

        if progress >= 1.0:
            self.phase = self.PHASE_GATE_SEQUENCE
            self.phase_timer = 0.0
            self.current_gate_index = 0
            self.gate_state = "display"
            self.gate_display_timer = 0.0
            self.fade_alpha = 0.0

    def _update_gate_sequence(self, dt: float):
        """gate 이미지 시퀀스 업데이트"""
        if self.gate_state == "display":
            # 현재 이미지 표시 중
            self.gate_display_timer += dt
            if self.gate_display_timer >= self.gate_display_duration:
                # 다음 이미지로 전환 시작
                self.gate_state = "transition"
                self.gate_transition_progress = 0.0
                self.gate_display_timer = 0.0

        elif self.gate_state == "transition":
            # 크로스페이드 전환 중
            self.gate_transition_progress += dt / self.gate_transition_duration

            if self.gate_transition_progress >= 1.0:
                self.gate_transition_progress = 1.0
                self.current_gate_index += 1

                if self.current_gate_index >= len(self.gate_images):
                    # 모든 gate 이미지 완료 -> 캐비닛 등장
                    self.phase = self.PHASE_CABINET_SHOW
                    self.phase_timer = 0.0
                    self.fade_alpha = 255  # 페이드 아웃 시작
                else:
                    self.gate_state = "display"
                    self.gate_display_timer = 0.0

    def _update_cabinet_show(self, dt: float):
        """캐비닛 등장 업데이트"""
        progress = min(1.0, self.phase_timer / self.cabinet_show_duration)
        # ease-out quad
        eased = 1.0 - (1.0 - progress) ** 2
        self.cabinet_y_offset = eased

        # 페이드 인 (gate에서 전환)
        if self.fade_alpha > 0:
            self.fade_alpha = max(0, self.fade_alpha - dt * 200)

        if progress >= 1.0:
            self.phase = self.PHASE_DIALOGUE
            self.phase_timer = 0.0
            self._start_next_document_and_dialogue()

    def _update_dialogue_phase(self, dt: float):
        """대화 + 문서 등장 업데이트"""
        # 문서 솟아오르기 애니메이션
        if self.doc_is_rising:
            self.doc_rise_progress += dt / self.doc_rise_duration
            if self.doc_rise_progress >= 1.0:
                self.doc_rise_progress = 1.0
                self.doc_is_rising = False

        # 대화 타이핑
        if self.current_dialogue_index < len(self.dialogue_after):
            if not self.waiting_for_click:
                self.typing_progress += dt * self.typing_speed
                if self.typing_progress >= len(self.dialogue_text):
                    self.typing_progress = len(self.dialogue_text)
                    self.waiting_for_click = True
        else:
            # 모든 대화 완료 -> 문서 리뷰 페이즈로
            if len(self.documents) > 0:
                self.phase = self.PHASE_DOC_REVIEW
                self.phase_timer = 0.0
                self.review_doc_index = 0
                self.review_state = "arrange_all"  # 즉각 정렬
                self.review_progress = 0.0
            else:
                self.phase = self.PHASE_ZOOM_OUT
                self.phase_timer = 0.0

    def _update_doc_review(self, dt: float):
        """문서 리뷰 - 즉각 정렬 후 DOC_VIEW 페이즈로 전환"""
        self.review_progress += dt / self.doc_review_duration

        if self.review_state == "arrange_all":
            # 모든 문서를 즉각 정렬 위치로 이동
            if self.review_progress >= 1.0:
                # 정렬 완료 -> 문서 확대 보기 페이즈로 전환
                self.phase = self.PHASE_DOC_VIEW
                self.phase_timer = 0.0
                self.view_state = "idle"
                self.viewing_doc_index = -1
                # 문서 클릭 영역 계산
                self._calculate_doc_rects()

    def _update_doc_view(self, dt: float):
        """문서 확대 보기 페이즈 업데이트"""
        if self.view_state == "zoom_in":
            self.view_zoom_progress += dt / self.view_zoom_duration
            if self.view_zoom_progress >= 1.0:
                self.view_zoom_progress = 1.0
                self.view_state = "viewing"

        elif self.view_state == "zoom_out":
            self.view_zoom_progress -= dt / self.view_zoom_duration
            if self.view_zoom_progress <= 0.0:
                self.view_zoom_progress = 0.0
                self.view_state = "idle"
                self.viewing_doc_index = -1

    def _calculate_doc_rects(self):
        """정렬된 문서들의 클릭 영역 계산"""
        self.doc_rects = []
        for i, doc in enumerate(self.documents):
            # visible 여부와 관계없이 모든 문서에 대해 rect 생성
            if i < len(self.doc_final_positions):
                pos = self.doc_final_positions[i]
                orig_w, orig_h = doc["image"].get_size()
                scale = pos["scale"]
                w = int(orig_w * scale)
                h = int(orig_h * scale)
                rect = pygame.Rect(int(pos["x"] - w // 2), int(pos["y"] - h // 2), w, h)
                self.doc_rects.append(rect)
                # 문서를 visible로 설정 (정렬 후에는 모두 보여야 함)
                doc["visible"] = True

    def _update_zoom_out(self, dt: float):
        """원래 배경으로 복귀"""
        progress = min(1.0, self.phase_timer / self.zoom_out_duration)
        # ease-in-out quad
        if progress < 0.5:
            eased = 2 * progress * progress
        else:
            eased = 1 - ((-2 * progress + 2) ** 2) / 2

        self.zoom_scale = (
            self.zoom_target_scale - (self.zoom_target_scale - 1.0) * eased
        )
        self.cabinet_y_offset = 1.0 - eased

        # 문서들 페이드 아웃
        for doc in self.documents:
            doc["alpha"] = int(255 * (1.0 - eased))

        if progress >= 1.0:
            self.phase = self.PHASE_DONE
            self.is_alive = False
            if self.on_complete:
                self.on_complete()

    def _start_next_document_and_dialogue(self):
        """다음 문서와 대화 시작"""
        self.current_doc_index += 1
        if self.current_doc_index < len(self.documents):
            self.documents[self.current_doc_index]["visible"] = True
            self.doc_rise_progress = 0.0
            self.doc_is_rising = True

        if self.current_dialogue_index < len(self.dialogue_after):
            self.dialogue_text = self.dialogue_after[self.current_dialogue_index].get(
                "text", ""
            )
            self.typing_progress = 0.0
            self.waiting_for_click = False

    def handle_event(self, event: pygame.event.Event):
        """이벤트 처리"""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self._handle_click()

        elif event.type == pygame.KEYDOWN:
            if event.key in [pygame.K_SPACE, pygame.K_RETURN]:
                return self._handle_click()

        return False

    def _handle_click(self):
        """클릭 처리"""
        if self.phase == self.PHASE_ZOOM_IN:
            # 줌인 스킵
            self.zoom_scale = self.zoom_target_scale
            self.phase = self.PHASE_GATE_SEQUENCE
            self.phase_timer = 0.0
            self.current_gate_index = 0
            self.gate_state = "display"
            return True

        elif self.phase == self.PHASE_GATE_SEQUENCE:
            # gate 시퀀스 스킵 (다음 이미지로)
            if self.gate_state == "display":
                self.gate_state = "transition"
                self.gate_transition_progress = 0.0
            else:
                self.gate_transition_progress = 1.0
            return True

        elif self.phase == self.PHASE_CABINET_SHOW:
            # 캐비닛 등장 스킵
            self.cabinet_y_offset = 1.0
            self.fade_alpha = 0
            self.phase = self.PHASE_DIALOGUE
            self.phase_timer = 0.0
            self._start_next_document_and_dialogue()
            return True

        elif self.phase == self.PHASE_DIALOGUE:
            if self.waiting_for_click:
                self.current_dialogue_index += 1
                if self.current_dialogue_index < len(self.dialogue_after):
                    self._start_next_document_and_dialogue()
                else:
                    # 모든 대화 완료 -> 문서 리뷰
                    if len(self.documents) > 0:
                        self.phase = self.PHASE_DOC_REVIEW
                        self.phase_timer = 0.0
                        self.review_doc_index = 0
                        self.review_state = "arrange_all"  # 즉각 정렬
                        self.review_progress = 0.0
                    else:
                        self.phase = self.PHASE_ZOOM_OUT
                        self.phase_timer = 0.0
            else:
                self.typing_progress = len(self.dialogue_text)
                self.waiting_for_click = True
            return True

        elif self.phase == self.PHASE_DOC_REVIEW:
            # 리뷰 스킵 (즉각 정렬 완료)
            self.review_progress = 1.0
            return True

        elif self.phase == self.PHASE_DOC_VIEW:
            return self._handle_doc_view_click(pygame.mouse.get_pos())

        return False

    def _handle_doc_view_click(self, mouse_pos):
        """문서 확대 보기 페이즈에서 클릭 처리"""
        if self.view_state == "idle":
            # 문서 클릭 확인
            for i, rect in enumerate(self.doc_rects):
                if rect.collidepoint(mouse_pos):
                    # 해당 문서 확대
                    self.viewing_doc_index = i
                    self.view_state = "zoom_in"
                    self.view_zoom_progress = 0.0
                    return True
            # 빈 공간 클릭 - 줌아웃으로 전환
            self.phase = self.PHASE_ZOOM_OUT
            self.phase_timer = 0.0
            return True

        elif self.view_state == "viewing":
            # 확대 보기 중 클릭 - 축소
            self.view_state = "zoom_out"
            return True

        elif self.view_state == "zoom_in":
            # 확대 중 클릭 - 즉시 확대 완료
            self.view_zoom_progress = 1.0
            self.view_state = "viewing"
            return True

        elif self.view_state == "zoom_out":
            # 축소 중 클릭 - 즉시 축소 완료
            self.view_zoom_progress = 0.0
            self.view_state = "idle"
            self.viewing_doc_index = -1
            return True

        return False

    def render(self, screen: pygame.Surface):
        """렌더링"""
        if self.phase == self.PHASE_ZOOM_IN:
            self._render_zoom_phase(screen)

        elif self.phase == self.PHASE_GATE_SEQUENCE:
            self._render_gate_sequence(screen)

        elif self.phase in [
            self.PHASE_CABINET_SHOW,
            self.PHASE_DIALOGUE,
            self.PHASE_DOC_REVIEW,
        ]:
            self._render_document_phase(screen)

        elif self.phase == self.PHASE_DOC_VIEW:
            self._render_doc_view_phase(screen)

        elif self.phase == self.PHASE_ZOOM_OUT:
            self._render_zoom_out_phase(screen)

        # 마우스 커서 렌더링 (문서 보기 페이즈에서만)
        if self.phase == self.PHASE_DOC_VIEW:
            self._render_cursor(screen)

    def _render_zoom_phase(self, screen: pygame.Surface):
        """줌인 페이즈 렌더링"""
        self._render_zoomed_background(screen)

        # 어두운 오버레이 (건물 내부로 들어가는 느낌)
        darkness = min(220, int((self.zoom_scale - 1.0) * 100))
        dark_overlay = pygame.Surface(self.screen_size, pygame.SRCALPHA)
        dark_overlay.fill((0, 0, 0, darkness))
        screen.blit(dark_overlay, (0, 0))

    def _render_gate_sequence(self, screen: pygame.Surface):
        """gate 이미지 시퀀스 렌더링"""
        if not self.gate_images:
            screen.fill((30, 35, 40))
            return

        if self.gate_state == "display":
            # 현재 이미지만 표시
            if self.current_gate_index < len(self.gate_images):
                screen.blit(self.gate_images[self.current_gate_index], (0, 0))

        elif self.gate_state == "transition":
            # 크로스페이드 전환
            current_img = (
                self.gate_images[self.current_gate_index]
                if self.current_gate_index < len(self.gate_images)
                else None
            )
            next_idx = self.current_gate_index + 1
            next_img = (
                self.gate_images[next_idx] if next_idx < len(self.gate_images) else None
            )

            # ease-in-out 전환
            t = self.gate_transition_progress
            if t < 0.5:
                eased = 2 * t * t
            else:
                eased = 1 - ((-2 * t + 2) ** 2) / 2

            if current_img:
                current_img.set_alpha(int(255 * (1 - eased)))
                screen.blit(current_img, (0, 0))
                current_img.set_alpha(255)

            if next_img:
                next_img.set_alpha(int(255 * eased))
                screen.blit(next_img, (0, 0))
                next_img.set_alpha(255)

    def _render_document_phase(self, screen: pygame.Surface):
        """문서 페이즈 (캐비닛, 대화, 리뷰) 렌더링"""
        screen_w, screen_h = self.screen_size

        # 어두운 배경
        screen.fill((25, 30, 35))

        # 페이드 오버레이 (gate에서 전환 시)
        if self.fade_alpha > 0:
            fade_surf = pygame.Surface(self.screen_size, pygame.SRCALPHA)
            fade_surf.fill((0, 0, 0, int(self.fade_alpha)))
            screen.blit(fade_surf, (0, 0))

        # 캐비닛 렌더링
        if self.cabinet_y_offset > 0:
            self._render_cabinet(screen)

        # 문서 렌더링
        if self.phase == self.PHASE_DIALOGUE:
            self._render_stacked_documents(screen)
        elif self.phase == self.PHASE_DOC_REVIEW:
            self._render_review_documents(screen)

        # 대화 박스
        if self.phase == self.PHASE_DIALOGUE:
            self._render_dialogue(screen)

        # 진행 표시
        if self.phase == self.PHASE_DIALOGUE and self.documents:
            self._render_progress(screen)

    def _render_zoom_out_phase(self, screen: pygame.Surface):
        """줌아웃 페이즈 렌더링"""
        self._render_zoomed_background(screen)

        # 문서들 페이드 아웃
        progress = min(1.0, self.phase_timer / self.zoom_out_duration)
        if progress < 0.3:
            # 초반에는 문서들이 보임
            doc_alpha = int(255 * (1 - progress / 0.3))
            self._render_final_documents(screen, doc_alpha)

    def _render_zoomed_background(self, screen: pygame.Surface):
        """줌된 배경 렌더링"""
        if not self.background_original:
            screen.fill((30, 35, 40))
            return

        screen_w, screen_h = self.screen_size

        zoom_w = screen_w / self.zoom_scale
        zoom_h = screen_h / self.zoom_scale

        center_x = screen_w * self.zoom_center_x
        center_y = screen_h * self.zoom_center_y

        src_x = max(0, center_x - zoom_w / 2)
        src_y = max(0, center_y - zoom_h / 2)

        if src_x + zoom_w > screen_w:
            src_x = screen_w - zoom_w
        if src_y + zoom_h > screen_h:
            src_y = screen_h - zoom_h

        src_rect = pygame.Rect(int(src_x), int(src_y), int(zoom_w), int(zoom_h))

        try:
            zoomed = self.background_original.subsurface(src_rect)
            zoomed = pygame.transform.smoothscale(zoomed, self.screen_size)
            screen.blit(zoomed, (0, 0))
        except:
            screen.blit(self.background_original, (0, 0))

    def _render_cabinet(self, screen: pygame.Surface):
        """캐비닛 렌더링"""
        if not self.cabinet_image:
            return

        screen_w, screen_h = self.screen_size
        cab_w, cab_h = self.cabinet_image.get_size()

        cab_x = screen_w // 2 - cab_w // 2
        cab_y_base = screen_h - cab_h + 30
        cab_y_hidden = screen_h + 50
        cab_y = cab_y_hidden + (cab_y_base - cab_y_hidden) * self.cabinet_y_offset

        screen.blit(self.cabinet_image, (cab_x, int(cab_y)))

    def _render_stacked_documents(self, screen: pygame.Surface):
        """쌓이는 문서들 렌더링"""
        screen_w, screen_h = self.screen_size

        for i, doc in enumerate(self.documents):
            if not doc["visible"]:
                continue

            img = doc["image"]
            img_w, img_h = img.get_size()

            base_x = screen_w // 2
            base_y = screen_h // 2 - 80

            if i == self.current_doc_index:
                # 현재 문서: 솟아오르는 애니메이션
                rise_eased = 1.0 - (1.0 - self.doc_rise_progress) ** 3
                start_y = screen_h + img_h // 2
                doc_y = start_y + (base_y - start_y) * rise_eased
                alpha = int(255 * rise_eased)
                # 약간 기울임
                angle = (1 - rise_eased) * 10
            else:
                # 이전 문서들: 뒤로 쌓임
                stack_offset = self.current_doc_index - i
                doc_y = base_y - stack_offset * 25
                # 좌우로 약간 어긋나게
                offset_x = (stack_offset % 2) * 30 - 15
                base_x += offset_x
                alpha = max(100, 255 - stack_offset * 40)
                angle = (stack_offset % 3 - 1) * 3

            img_copy = img.copy()
            if angle != 0:
                img_copy = pygame.transform.rotate(img_copy, angle)
            img_copy.set_alpha(alpha)

            rect = img_copy.get_rect(center=(base_x, int(doc_y)))
            screen.blit(img_copy, rect)

    def _render_review_documents(self, screen: pygame.Surface):
        """문서들 즉각 정렬 렌더링 (애니메이션 포함)"""
        screen_w, screen_h = self.screen_size

        # 정렬 진행도 (0 -> 1)
        t = min(1.0, self.review_progress)
        eased = 1.0 - (1.0 - t) ** 2  # ease-out

        for i, doc in enumerate(self.documents):
            if not doc["visible"]:
                continue

            img = doc["image"]
            orig_w, orig_h = img.get_size()

            if i < len(self.doc_final_positions):
                pos = self.doc_final_positions[i]

                # 시작 위치 (스택 위치)
                start_x = screen_w // 2 + (i % 2 - 0.5) * 30
                start_y = screen_h // 2 - 80 + i * 15
                start_scale = 1.0

                # 최종 위치
                end_x = pos["x"]
                end_y = pos["y"]
                end_scale = pos["scale"]

                # 보간
                cur_x = start_x + (end_x - start_x) * eased
                cur_y = start_y + (end_y - start_y) * eased
                cur_scale = start_scale + (end_scale - start_scale) * eased

                new_w = int(orig_w * cur_scale)
                new_h = int(orig_h * cur_scale)
                scaled_img = pygame.transform.smoothscale(img, (new_w, new_h))
                rect = scaled_img.get_rect(center=(int(cur_x), int(cur_y)))
                screen.blit(scaled_img, rect)

    def _render_doc_view_phase(self, screen: pygame.Surface):
        """문서 확대 보기 페이즈 렌더링"""
        screen_w, screen_h = self.screen_size

        # 어두운 배경
        screen.fill((25, 30, 35))

        # 캐비닛 (어둡게)
        if self.cabinet_image:
            cab_w, cab_h = self.cabinet_image.get_size()
            cab_x = screen_w // 2 - cab_w // 2
            cab_y = screen_h - cab_h + 30
            dark_cab = self.cabinet_image.copy()
            dark_cab.set_alpha(80)
            screen.blit(dark_cab, (cab_x, cab_y))

        # 확대 보기 중이면 배경 어둡게
        if self.viewing_doc_index >= 0:
            dark_overlay = pygame.Surface(self.screen_size, pygame.SRCALPHA)
            alpha = int(180 * self.view_zoom_progress)
            dark_overlay.fill((0, 0, 0, alpha))
            screen.blit(dark_overlay, (0, 0))

        # 정렬된 문서들 렌더링
        mouse_pos = pygame.mouse.get_pos()
        for i, doc in enumerate(self.documents):
            if not doc["visible"]:
                continue
            if i >= len(self.doc_final_positions):
                continue

            img = doc["image"]
            orig_w, orig_h = img.get_size()
            pos = self.doc_final_positions[i]

            # 확대 보기 중인 문서 처리
            if i == self.viewing_doc_index:
                # 확대 애니메이션
                t = self.view_zoom_progress
                eased = 1.0 - (1.0 - t) ** 2  # ease-out

                # 시작: 정렬 위치
                start_x, start_y = pos["x"], pos["y"]
                start_scale = pos["scale"]

                # 끝: 화면 중앙, 거의 전체화면
                end_x, end_y = screen_w // 2, screen_h // 2
                end_scale = min(screen_w * 0.85 / orig_w, screen_h * 0.85 / orig_h)

                cur_x = start_x + (end_x - start_x) * eased
                cur_y = start_y + (end_y - start_y) * eased
                cur_scale = start_scale + (end_scale - start_scale) * eased

                new_w = int(orig_w * cur_scale)
                new_h = int(orig_h * cur_scale)
                scaled_img = pygame.transform.smoothscale(img, (new_w, new_h))
                rect = scaled_img.get_rect(center=(int(cur_x), int(cur_y)))
                screen.blit(scaled_img, rect)
            else:
                # 다른 문서들 (확대 보기 중이면 숨김)
                if self.viewing_doc_index >= 0:
                    continue

                scale = pos["scale"]
                new_w = int(orig_w * scale)
                new_h = int(orig_h * scale)
                scaled_img = pygame.transform.smoothscale(img, (new_w, new_h))
                rect = scaled_img.get_rect(center=(int(pos["x"]), int(pos["y"])))

                # 호버 효과
                if i < len(self.doc_rects) and self.doc_rects[i].collidepoint(
                    mouse_pos
                ):
                    # 호버 시 밝게 + 테두리
                    pygame.draw.rect(
                        screen, (100, 120, 140), rect.inflate(8, 8), 3, border_radius=5
                    )
                    scaled_img.set_alpha(255)
                else:
                    scaled_img.set_alpha(220)

                screen.blit(scaled_img, rect)

        # 안내 텍스트
        if self.viewing_doc_index < 0 and "small" in self.fonts:
            hint_text = "클릭하여 문서 확대 | 빈 공간 클릭하여 계속"
            hint_surf = self.fonts["small"].render(hint_text, True, (150, 160, 170))
            hint_rect = hint_surf.get_rect(center=(screen_w // 2, screen_h - 40))
            screen.blit(hint_surf, hint_rect)
        elif (
            self.viewing_doc_index >= 0
            and self.view_state == "viewing"
            and "small" in self.fonts
        ):
            hint_text = "클릭하여 닫기"
            hint_surf = self.fonts["small"].render(hint_text, True, (200, 210, 220))
            hint_rect = hint_surf.get_rect(center=(screen_w // 2, screen_h - 40))
            screen.blit(hint_surf, hint_rect)

    def _render_final_documents(self, screen: pygame.Surface, alpha: int):
        """최종 정렬된 문서들 렌더링 (페이드 아웃용)"""
        for i, doc in enumerate(self.documents):
            if not doc["visible"]:
                continue

            img = doc["image"]
            orig_w, orig_h = img.get_size()

            if i < len(self.doc_final_positions):
                pos = self.doc_final_positions[i]
                scale = pos["scale"]
                new_w = int(orig_w * scale)
                new_h = int(orig_h * scale)
                scaled_img = pygame.transform.smoothscale(img, (new_w, new_h))
                scaled_img.set_alpha(alpha)
                rect = scaled_img.get_rect(center=(int(pos["x"]), int(pos["y"])))
                screen.blit(scaled_img, rect)

    def _render_dialogue(self, screen: pygame.Surface):
        """대화 박스 렌더링 (초상화 포함)"""
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
            box_color=(20, 30, 40, 220),
            border_color=(80, 100, 80),
            has_portrait=(portrait is not None),
            portrait=portrait,
        )

    def _get_portrait(self, speaker: str) -> pygame.Surface:
        """초상화 이미지 가져오기 (캐시 사용)"""
        if speaker in self.portrait_cache:
            return self.portrait_cache[speaker]

        try:
            from mode_configs.config_story_dialogue import CHARACTER_PORTRAITS

            path = CHARACTER_PORTRAITS.get(speaker)
        except ImportError:
            path = None

        if path:
            try:
                img = pygame.image.load(path).convert_alpha()
                target_size = (120, 120)
                img = pygame.transform.smoothscale(img, target_size)
                self.portrait_cache[speaker] = img
                return img
            except Exception as e:
                print(f"WARNING: Failed to load portrait for {speaker}: {e}")

        return None

    def _render_progress(self, screen: pygame.Surface):
        """진행 상태 표시"""
        if "small" not in self.fonts:
            return

        total = len(self.documents)
        current = max(1, self.current_doc_index + 1)
        progress_text = f"문서 {current} / {total}"

        hint_surf = self.fonts["small"].render(progress_text, True, (150, 150, 150))
        screen.blit(hint_surf, (50, 30))

    def _render_cursor(self, screen: pygame.Surface):
        """마우스 커서 렌더링 (문서 보기 페이즈에서 사용)"""
        mouse_pos = pygame.mouse.get_pos()

        # 커서 색상 (문서 위에 있으면 밝게)
        cursor_color = (200, 200, 200)

        # 문서 위에 호버 중인지 확인
        is_hovering = False
        if self.viewing_doc_index < 0:  # 확대 보기 중이 아닐 때만
            for rect in self.doc_rects:
                if rect.collidepoint(mouse_pos):
                    cursor_color = (255, 255, 100)  # 노란색으로 강조
                    is_hovering = True
                    break

        # 십자 커서 그리기
        cursor_size = 12 if is_hovering else 10
        line_width = 2

        # 수평선
        pygame.draw.line(
            screen,
            cursor_color,
            (mouse_pos[0] - cursor_size, mouse_pos[1]),
            (mouse_pos[0] + cursor_size, mouse_pos[1]),
            line_width,
        )
        # 수직선
        pygame.draw.line(
            screen,
            cursor_color,
            (mouse_pos[0], mouse_pos[1] - cursor_size),
            (mouse_pos[0], mouse_pos[1] + cursor_size),
            line_width,
        )
        # 중앙 점
        pygame.draw.circle(screen, cursor_color, mouse_pos, 2)


# =========================================================
# Act 3: 손상된 홀로그램 효과
# =========================================================
# Act 3: 불꽃 속 기록 효과 (타들어가는 사진/문서)
# =========================================================
class BurningRecordEffect:
    """
    Act 3 컷씬: 불꽃 속 기록 효과

    특징:
    - 어두운 배경에 불꽃 파티클
    - 큰 이미지가 가장자리부터 타들어감
    - 타는 애니메이션과 함께 이미지 전환
    - 연구소 화재 테마에 맞는 분위기
    """

    PHASE_FADEIN = 0
    PHASE_DISPLAY = 1  # 이미지 + 대화 동시 표시
    PHASE_BURNING = 2  # 타들어가는 애니메이션
    PHASE_FADEOUT = 3
    PHASE_DONE = 4

    def __init__(
        self,
        screen_size: tuple,
        film_paths: list,
        background_path: str = None,
        dialogue_after: list = None,
        sound_manager=None,
        special_effects: dict = None,
        scene_id: str = "burning_scene",
    ):
        self.screen_size = screen_size
        self.film_paths = film_paths
        self.background_path = background_path
        self.dialogue_after = dialogue_after or []
        self.sound_manager = sound_manager
        self.special_effects = special_effects or {}
        self.scene_id = scene_id

        self.is_alive = True
        self.phase = self.PHASE_FADEIN
        self.phase_timer = 0.0

        # 타이밍
        self.fadein_duration = 1.5
        self.fadeout_duration = 1.5
        self.fade_alpha = 0.0
        self.burn_duration = 2.0  # 타들어가는 시간

        # 배경
        self.background = None
        self._load_background(background_path)

        # 이미지 크기 (화면의 40% - 중간 크기, 흩어진 배치)
        screen_w, screen_h = self.screen_size
        self.img_width = int(screen_w * 0.40)
        self.img_height = int(screen_h * 0.50)

        # 이미지들
        self.records = []
        self._prepare_records()

        # 현재 이미지 인덱스
        self.current_record_index = 0

        # 흩어진 배치 위치 (폴라로이드처럼)
        self.scatter_positions = []
        self._setup_scatter_positions()

        # 타들어가는 효과
        self.burn_progress = 0.0  # 0~1 (얼마나 탔는지)
        self.burn_mask = None
        self._create_burn_mask()

        # 불꽃 파티클
        self.fire_particles = []
        self.ember_particles = []  # 불씨/재

        # 대사 관련
        self.current_dialogue_index = 0
        self.dialogue_text = ""
        self.typing_progress = 0.0
        self.typing_speed = 25.0
        self.waiting_for_click = False
        self.dialogue_complete = False

        # 폰트
        self.fonts = {}

        # 콜백
        self.on_complete = None
        self.on_replay_request = None

        # 이미지와 대화 매핑
        self._setup_dialogue_per_image()

        print(f"INFO: BurningRecordEffect created with {len(self.records)} records")

    def _load_background(self, path: str):
        """배경 이미지 로드 - 어두운 불타는 배경"""
        try:
            if path:
                img = pygame.image.load(path).convert()
                img = pygame.transform.scale(img, self.screen_size)
                # 어둡게 + 붉은 톤
                overlay = pygame.Surface(self.screen_size, pygame.SRCALPHA)
                overlay.fill((40, 10, 5, 180))
                img.blit(overlay, (0, 0))
                self.background = img
            else:
                raise Exception("No path")
        except Exception as e:
            # 기본 어두운 배경
            self.background = pygame.Surface(self.screen_size)
            self.background.fill((20, 8, 5))

    def _prepare_records(self):
        """이미지 준비 - 아주 크게"""
        for path in self.film_paths:
            record_img = None
            try:
                record_img = pygame.image.load(path).convert_alpha()
                orig_w, orig_h = record_img.get_size()
                # 꽉 차게 확대
                ratio = max(self.img_width / orig_w, self.img_height / orig_h)
                new_w, new_h = int(orig_w * ratio), int(orig_h * ratio)
                record_img = pygame.transform.smoothscale(record_img, (new_w, new_h))
                # 중앙 크롭
                crop_x = (new_w - self.img_width) // 2
                crop_y = (new_h - self.img_height) // 2
                cropped = pygame.Surface(
                    (self.img_width, self.img_height), pygame.SRCALPHA
                )
                cropped.blit(record_img, (-crop_x, -crop_y))
                record_img = cropped
            except Exception as e:
                print(f"WARNING: Failed to load record: {path} - {e}")
                record_img = pygame.Surface(
                    (self.img_width, self.img_height), pygame.SRCALPHA
                )
                record_img.fill((80, 70, 60, 200))

            filename = Path(path).name
            effect_info = self.special_effects.get(filename, {})

            self.records.append(
                {
                    "image": record_img,
                    "filename": filename,
                    "effect": effect_info.get("effect", None),
                }
            )

    def _setup_scatter_positions(self):
        """폴라로이드처럼 흩어진 배치 위치 설정"""
        screen_w, screen_h = self.screen_size
        center_x, center_y = screen_w // 2, screen_h // 2

        # 각 이미지의 위치, 회전, 스케일 설정
        num_records = len(self.records)
        for _ in range(num_records):
            # 화면 중앙 근처에서 약간씩 흩어진 위치
            offset_x = random.randint(-150, 150)
            offset_y = random.randint(-100, 100)
            x = center_x - self.img_width // 2 + offset_x
            y = center_y - self.img_height // 2 + offset_y

            # 약간의 회전 (-15 ~ +15도)
            rotation = random.uniform(-15, 15)

            self.scatter_positions.append(
                {
                    "x": x,
                    "y": y,
                    "rotation": rotation,
                    "offset_x": offset_x,
                    "offset_y": offset_y,
                }
            )

    def _create_burn_mask(self):
        """타들어가는 마스크 생성 (가장자리부터 안쪽으로)"""
        # 간단한 마스크만 생성 (실제 픽셀 단위는 성능 이슈로 생략)
        self.burn_mask = None  # 오버레이 방식 사용

    def _setup_dialogue_per_image(self):
        """이미지당 대화 수 계산"""
        num_images = len(self.records)
        num_dialogues = len(self.dialogue_after)
        if num_images == 0:
            self.dialogues_per_image = 0
        else:
            self.dialogues_per_image = max(
                1, (num_dialogues + num_images - 1) // num_images
            )

    def set_fonts(self, fonts: dict):
        self.fonts = fonts

    def update(self, dt: float):
        if not self.is_alive:
            return

        self.phase_timer += dt

        # 불꽃 파티클 업데이트 (비활성화)
        # self._update_particles(dt)

        if self.phase == self.PHASE_FADEIN:
            self.fade_alpha = min(255, (self.phase_timer / self.fadein_duration) * 255)
            if self.phase_timer >= self.fadein_duration:
                self.phase = self.PHASE_DISPLAY
                self.phase_timer = 0.0
                self._start_dialogue()

        elif self.phase == self.PHASE_DISPLAY:
            self._update_dialogue(dt)

        elif self.phase == self.PHASE_BURNING:
            # 타들어가는 진행
            self.burn_progress = min(1.0, self.phase_timer / self.burn_duration)
            # 불꽃 파티클 비활성화
            # self._spawn_fire_particles(5)

            if self.burn_progress >= 1.0:
                # 다음 이미지로 전환
                self.current_record_index += 1
                self.burn_progress = 0.0
                self.phase_timer = 0.0

                if self.current_record_index >= len(self.records):
                    self.phase = self.PHASE_FADEOUT
                else:
                    self.phase = self.PHASE_DISPLAY
                    self._start_dialogue()

        elif self.phase == self.PHASE_FADEOUT:
            progress = self.phase_timer / self.fadeout_duration
            self.fade_alpha = 255 * (1.0 - progress)
            if self.phase_timer >= self.fadeout_duration:
                self.phase = self.PHASE_DONE
                self.is_alive = False
                if self.on_complete:
                    self.on_complete()

    def _update_particles(self, dt: float):
        """파티클 업데이트"""
        # 기본 불꽃 파티클 생성
        if self.phase in [self.PHASE_DISPLAY, self.PHASE_BURNING]:
            if random.random() < 0.3:
                self._spawn_fire_particles(1)

        # 파티클 이동 및 소멸
        for p in self.fire_particles[:]:
            p["y"] -= p["speed"] * dt
            p["life"] -= dt
            p["x"] += random.uniform(-30, 30) * dt
            if p["life"] <= 0:
                self.fire_particles.remove(p)

        for p in self.ember_particles[:]:
            p["y"] -= p["speed"] * dt * 0.5
            p["x"] += random.uniform(-50, 50) * dt
            p["life"] -= dt
            if p["life"] <= 0:
                self.ember_particles.remove(p)

    def _spawn_fire_particles(self, count: int):
        """불꽃 파티클 생성 (현재 이미지 위치 기준)"""
        if self.current_record_index >= len(self.scatter_positions):
            return

        pos = self.scatter_positions[self.current_record_index]
        img_x = pos["x"]
        img_y = pos["y"]

        for _ in range(count):
            # 이미지 가장자리 근처에서 생성
            edge = random.choice(["top", "bottom", "left", "right"])
            if edge == "top":
                x = img_x + random.randint(0, self.img_width)
                y = img_y
            elif edge == "bottom":
                x = img_x + random.randint(0, self.img_width)
                y = img_y + self.img_height
            elif edge == "left":
                x = img_x
                y = img_y + random.randint(0, self.img_height)
            else:
                x = img_x + self.img_width
                y = img_y + random.randint(0, self.img_height)

            self.fire_particles.append(
                {
                    "x": x,
                    "y": y,
                    "speed": random.uniform(80, 200),
                    "size": random.randint(3, 12),
                    "life": random.uniform(0.5, 1.5),
                    "color": random.choice(
                        [
                            (255, 200, 50),  # 밝은 노랑
                            (255, 150, 30),  # 주황
                            (255, 100, 20),  # 진한 주황
                            (255, 60, 10),  # 빨강-주황
                        ]
                    ),
                }
            )

            # 불씨도 생성
            if random.random() < 0.3:
                self.ember_particles.append(
                    {
                        "x": x + random.randint(-20, 20),
                        "y": y,
                        "speed": random.uniform(30, 80),
                        "size": random.randint(1, 3),
                        "life": random.uniform(1.0, 3.0),
                    }
                )

    def _start_dialogue(self):
        """현재 대화 시작"""
        if self.current_dialogue_index < len(self.dialogue_after):
            self.dialogue_text = self.dialogue_after[self.current_dialogue_index].get(
                "text", ""
            )
            self.typing_progress = 0.0
            self.waiting_for_click = False
            self.dialogue_complete = False
        else:
            self.dialogue_complete = True

    def _update_dialogue(self, dt: float):
        """대사 업데이트"""
        if self.current_dialogue_index >= len(self.dialogue_after):
            self.dialogue_complete = True
            return

        if not self.waiting_for_click:
            self.typing_progress += dt * self.typing_speed
            if self.typing_progress >= len(self.dialogue_text):
                self.typing_progress = len(self.dialogue_text)
                self.waiting_for_click = True

    def _advance_to_next(self):
        """다음 대화/이미지로 진행"""
        self.current_dialogue_index += 1

        # 일정 대화마다 타들어가기 시작
        if self.dialogues_per_image > 0:
            expected_image = self.current_dialogue_index // self.dialogues_per_image
            if (
                expected_image > self.current_record_index
                and self.current_record_index < len(self.records) - 1
            ):
                self.phase = self.PHASE_BURNING
                self.phase_timer = 0.0
                self.burn_progress = 0.0
                return

        if self.current_dialogue_index < len(self.dialogue_after):
            self._start_dialogue()
        else:
            self.dialogue_complete = True
            if self.current_record_index >= len(self.records) - 1:
                self.phase = self.PHASE_FADEOUT
                self.phase_timer = 0.0

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.phase == self.PHASE_DISPLAY:
                if self.waiting_for_click:
                    self._advance_to_next()
                else:
                    self.typing_progress = len(self.dialogue_text)
                    self.waiting_for_click = True
                return True

        elif event.type == pygame.KEYDOWN:
            if event.key in [pygame.K_SPACE, pygame.K_RETURN]:
                return self.handle_event(
                    pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1)
                )

        return False

    def render(self, screen: pygame.Surface):
        # 배경
        if self.background:
            bg_copy = self.background.copy()
            if self.fade_alpha < 255:
                bg_copy.set_alpha(int(self.fade_alpha))
            screen.blit(bg_copy, (0, 0))

        # 이미지 렌더링
        if self.phase in [self.PHASE_DISPLAY, self.PHASE_BURNING]:
            self._render_burning_record(screen)

        # 불꽃 파티클 (비활성화)
        # self._render_particles(screen)

        # 비네트 (어두운 가장자리)
        self._render_vignette(screen)

        # 대사
        if self.phase == self.PHASE_DISPLAY:
            self._render_dialogue(screen)

    def _render_burning_record(self, screen: pygame.Surface):
        """타들어가는 기록 이미지 렌더링 (폴라로이드처럼 흩어진 배치)"""
        if self.current_record_index >= len(self.records):
            return

        # 현재 이미지의 흩어진 위치 가져오기
        pos = self.scatter_positions[self.current_record_index]
        img_x = pos["x"]
        img_y = pos["y"]
        rotation = pos["rotation"]

        record = self.records[self.current_record_index]
        img = record["image"].copy()

        # 타들어가는 효과 적용
        if self.phase == self.PHASE_BURNING and self.burn_progress > 0:
            self._apply_burn_effect(img)

        # 테두리가 있는 사진 서피스 생성 (탄 종이 느낌)
        border_size = 15
        photo_surf = pygame.Surface(
            (self.img_width + border_size * 2, self.img_height + border_size * 2),
            pygame.SRCALPHA,
        )

        # 탄 종이 테두리 (불규칙한 갈색)
        pygame.draw.rect(
            photo_surf,
            (70, 50, 35, 230),
            (0, 0, photo_surf.get_width(), photo_surf.get_height()),
            border_radius=3,
        )
        # 탄 자국 테두리
        pygame.draw.rect(
            photo_surf,
            (40, 25, 15, 200),
            (0, 0, photo_surf.get_width(), photo_surf.get_height()),
            3,
            border_radius=3,
        )

        # 이미지 배치
        photo_surf.blit(img, (border_size, border_size))

        # 회전 적용
        if rotation != 0:
            photo_surf = pygame.transform.rotate(photo_surf, rotation)

        # 페이드 적용
        if self.fade_alpha < 255:
            photo_surf.set_alpha(int(self.fade_alpha))

        # 회전 후 중앙 정렬을 위한 위치 조정
        rotated_rect = photo_surf.get_rect(
            center=(img_x + self.img_width // 2, img_y + self.img_height // 2)
        )
        screen.blit(photo_surf, rotated_rect)

        # 타는 중이면 가장자리에 빛나는 효과
        if self.phase == self.PHASE_BURNING:
            self._render_burning_edge(
                screen,
                rotated_rect.x,
                rotated_rect.y,
                photo_surf.get_width(),
                photo_surf.get_height(),
            )

    def _apply_burn_effect(self, img: pygame.Surface):
        """이미지에 타들어가는 효과 적용"""
        # 간단한 구현: 가장자리부터 투명하게
        w, h = img.get_size()
        center_x, center_y = w // 2, h // 2
        max_dist = math.sqrt(center_x**2 + center_y**2)

        # burn_progress에 따라 얼마나 탔는지
        burn_radius = max_dist * (1.0 - self.burn_progress)

        # 픽셀 단위 처리는 느리므로 오버레이로 표현
        burn_overlay = pygame.Surface((w, h), pygame.SRCALPHA)

        # 탄 영역 (검은색 + 투명)
        for i in range(20):  # 여러 원으로 그라데이션
            radius = int(burn_radius + i * 10)
            alpha = int(min(255, (i / 20) * 255 * self.burn_progress))
            color = (20, 10, 5, alpha)
            pygame.draw.circle(burn_overlay, color, (center_x, center_y), radius, 5)

        # 가장자리에 주황/빨간 불꽃 색
        edge_radius = int(burn_radius)
        if edge_radius > 10:
            pygame.draw.circle(
                burn_overlay,
                (255, 100, 30, 100),
                (center_x, center_y),
                edge_radius + 5,
                8,
            )
            pygame.draw.circle(
                burn_overlay,
                (255, 200, 50, 80),
                (center_x, center_y),
                edge_radius + 2,
                4,
            )

        img.blit(burn_overlay, (0, 0))

    def _render_burning_edge(
        self,
        screen: pygame.Surface,
        img_x: int,
        img_y: int,
        width: int = None,
        height: int = None,
    ):
        """타는 가장자리 빛 효과"""
        w = width or self.img_width
        h = height or self.img_height
        center_x = img_x + w // 2
        center_y = img_y + h // 2
        max_dist = math.sqrt((w // 2) ** 2 + (h // 2) ** 2)
        burn_radius = int(max_dist * (1.0 - self.burn_progress))

        glow_surf = pygame.Surface(self.screen_size, pygame.SRCALPHA)
        # 빛나는 원 (불꽃 색)
        for i in range(5):
            alpha = 40 - i * 7
            pygame.draw.circle(
                glow_surf,
                (255, 150, 50, max(0, alpha)),
                (center_x, center_y),
                burn_radius + i * 15,
                4,
            )

        screen.blit(glow_surf, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

    def _render_particles(self, screen: pygame.Surface):
        """파티클 렌더링"""
        for p in self.fire_particles:
            alpha = int(255 * (p["life"] / 1.5))
            color = (*p["color"][:3], min(255, alpha))
            surf = pygame.Surface((p["size"] * 2, p["size"] * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, color, (p["size"], p["size"]), p["size"])
            screen.blit(
                surf,
                (int(p["x"] - p["size"]), int(p["y"] - p["size"])),
                special_flags=pygame.BLEND_RGBA_ADD,
            )

        for p in self.ember_particles:
            alpha = int(200 * (p["life"] / 3.0))
            color = (255, 180, 100, min(255, alpha))
            surf = pygame.Surface((p["size"] * 2, p["size"] * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, color, (p["size"], p["size"]), p["size"])
            screen.blit(surf, (int(p["x"] - p["size"]), int(p["y"] - p["size"])))

    def _render_vignette(self, screen: pygame.Surface):
        """비네트 효과 (붉은 톤)"""
        vignette = pygame.Surface(self.screen_size, pygame.SRCALPHA)
        screen_w, screen_h = self.screen_size
        center_x, center_y = screen_w // 2, screen_h // 2
        max_dist = math.sqrt(center_x**2 + center_y**2)

        # 가장자리 어둡게 + 붉은 톤
        for i in range(10):
            radius = int(max_dist * (1.0 - i * 0.08))
            alpha = i * 15
            pygame.draw.circle(
                vignette, (30, 10, 5, alpha), (center_x, center_y), radius, 50
            )

        screen.blit(vignette, (0, 0))

    def _render_dialogue(self, screen: pygame.Surface):
        """대사 박스 렌더링 (초상화 포함)"""
        if not self.dialogue_after or self.current_dialogue_index >= len(
            self.dialogue_after
        ):
            if (
                self.dialogue_complete
                and self.current_record_index < len(self.records) - 1
            ):
                self._render_hint(screen, "클릭하여 다음 기록")
            elif self.dialogue_complete:
                self._render_hint(screen, "클릭하여 계속")
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
            box_color=(30, 15, 10, 220),
            border_color=(150, 80, 40, 150),
            text_color=(255, 240, 220),
            box_height=160,
            has_portrait=(portrait is not None),
            portrait=portrait,
        )

    def _get_portrait(self, speaker: str) -> pygame.Surface:
        """초상화 이미지 가져오기 (캐시 사용)"""
        if speaker in self.portrait_cache:
            return self.portrait_cache[speaker]

        try:
            from mode_configs.config_story_dialogue import CHARACTER_PORTRAITS

            path = CHARACTER_PORTRAITS.get(speaker)
        except ImportError:
            path = None

        if path:
            try:
                img = pygame.image.load(path).convert_alpha()
                target_size = (120, 120)
                img = pygame.transform.smoothscale(img, target_size)
                self.portrait_cache[speaker] = img
                return img
            except Exception as e:
                print(f"WARNING: Failed to load portrait for {speaker}: {e}")

        return None

    def _render_hint(self, screen: pygame.Surface, text: str):
        if "small" not in self.fonts:
            return
        hint_surf = self.fonts["small"].render(text, True, (255, 200, 150))
        x = self.screen_size[0] // 2 - hint_surf.get_width() // 2
        y = self.screen_size[1] - 50
        screen.blit(hint_surf, (x, y))


# DamagedHologramEffect는 BurningRecordEffect의 별칭으로 유지 (호환성)
DamagedHologramEffect = BurningRecordEffect


# =========================================================
# Act 3: 필름 릴 효과 - 이미지 원본 색상 100% 유지
# =========================================================
class FilmReelEffect:
    """
    Act 3 컷씬: 필름 릴 효과

    특징:
    - 이미지 원본 색상 100% 유지 (틴트 없음!)
    - 좌우에 스프로킷 구멍이 있는 필름 프레임
    - 필름이 위에서 아래로 롤링하는 애니메이션
    - 프레임 번호 표시 (FRAME 001)
    - 약한 비네트와 필름 스크래치 효과
    - 간헐적 깜빡임 (옛날 영사기 느낌)
    """

    PHASE_FADEIN = 0
    PHASE_FILM_ROLL = 1  # 필름이 위에서 내려옴
    PHASE_DISPLAY = 2  # 이미지 표시, 대화
    PHASE_FILM_ADVANCE = 3  # 다음 프레임으로 전환 (위로 롤아웃)
    PHASE_FADEOUT = 4
    PHASE_DONE = 5

    def __init__(
        self,
        screen_size: tuple,
        film_paths: list,
        background_path: str = None,
        dialogue_after: list = None,
        sound_manager=None,
        special_effects: dict = None,
        scene_id: str = "film_scene",
    ):
        self.screen_size = screen_size
        self.film_paths = film_paths
        self.background_path = background_path
        self.dialogue_after = dialogue_after or []
        self.sound_manager = sound_manager
        self.special_effects = special_effects or {}
        self.scene_id = scene_id

        self.is_alive = True
        self.phase = self.PHASE_FADEIN
        self.phase_timer = 0.0

        # 타이밍
        self.fadein_duration = 1.5
        self.fadeout_duration = 1.5
        self.roll_duration = 0.8  # 롤링 애니메이션 시간
        self.advance_duration = 0.6  # 다음 프레임 전환 시간
        self.fade_alpha = 0.0

        # 배경 (어둡게 처리하되 붉은 톤은 줄임)
        self.background = None
        self._load_background(background_path)

        # 필름 프레임 크기 (화면의 50% 정도)
        screen_w, screen_h = self.screen_size
        self.film_width = int(screen_w * 0.45)
        self.film_height = int(screen_h * 0.55)

        # 스프로킷 구멍 설정
        self.sprocket_margin = 50  # 좌우 여백 (구멍 영역)
        self.sprocket_hole_radius = 12
        self.sprocket_hole_spacing = 40

        # 필름 전체 프레임 크기 (스프로킷 포함)
        self.frame_width = self.film_width + self.sprocket_margin * 2
        self.frame_height = self.film_height + 80  # 하단에 프레임 번호 공간

        # 이미지들
        self.films = []
        self._prepare_films()

        # 현재 프레임 인덱스
        self.current_frame_index = 0

        # 롤링 애니메이션용
        self.roll_offset = 0.0  # 현재 롤링 오프셋 (픽셀)

        # 필름 효과
        self.flicker_timer = 0.0
        self.flicker_alpha = 0  # 깜빡임 알파 (0~30 정도)
        self.scratch_lines = []  # 스크래치 라인들
        self._generate_scratch_lines()

        # 대사 관련
        self.current_dialogue_index = 0
        self.dialogue_text = ""
        self.typing_progress = 0.0
        self.typing_speed = 25.0
        self.waiting_for_click = False
        self.dialogue_complete = False

        # 폰트
        self.fonts = {}

        # 콜백
        self.on_complete = None
        self.on_replay_request = None

        # 이미지와 대화 매핑
        self._setup_dialogue_per_image()

        print(f"INFO: FilmReelEffect created with {len(self.films)} frames")

    def _load_background(self, path: str):
        """배경 이미지 로드 - 어둡게 (붉은 톤 최소화)"""
        try:
            if path:
                img = pygame.image.load(path).convert()
                img = pygame.transform.scale(img, self.screen_size)
                # 어둡게만 (붉은 톤 없이)
                overlay = pygame.Surface(self.screen_size, pygame.SRCALPHA)
                overlay.fill((20, 20, 25, 200))
                img.blit(overlay, (0, 0))
                self.background = img
            else:
                raise Exception("No path")
        except Exception as e:
            # 기본 어두운 배경
            self.background = pygame.Surface(self.screen_size)
            self.background.fill((15, 15, 20))

    def _prepare_films(self):
        """필름 이미지 준비 - 원본 색상 유지!"""
        for path in self.film_paths:
            film_img = None
            try:
                film_img = pygame.image.load(path).convert_alpha()
                orig_w, orig_h = film_img.get_size()
                # 비율 유지하며 확대
                ratio = max(self.film_width / orig_w, self.film_height / orig_h)
                new_w, new_h = int(orig_w * ratio), int(orig_h * ratio)
                film_img = pygame.transform.smoothscale(film_img, (new_w, new_h))
                # 중앙 크롭
                crop_x = (new_w - self.film_width) // 2
                crop_y = (new_h - self.film_height) // 2
                cropped = pygame.Surface(
                    (self.film_width, self.film_height), pygame.SRCALPHA
                )
                cropped.blit(film_img, (-crop_x, -crop_y))
                film_img = cropped
            except Exception as e:
                print(f"WARNING: Failed to load film: {path} - {e}")
                film_img = pygame.Surface(
                    (self.film_width, self.film_height), pygame.SRCALPHA
                )
                film_img.fill((60, 60, 65, 200))

            filename = Path(path).name
            effect_info = self.special_effects.get(filename, {})

            self.films.append(
                {
                    "image": film_img,
                    "filename": filename,
                    "effect": effect_info.get("effect", None),
                }
            )

    def _generate_scratch_lines(self):
        """필름 스크래치 라인 생성"""
        screen_h = self.screen_size[1]
        # 3~5개의 세로 스크래치 라인
        for _ in range(random.randint(3, 5)):
            self.scratch_lines.append(
                {
                    "x": random.randint(100, self.screen_size[0] - 100),
                    "alpha": random.randint(15, 40),
                    "width": random.randint(1, 2),
                }
            )

    def _setup_dialogue_per_image(self):
        """이미지당 대화 수 계산"""
        num_images = len(self.films)
        num_dialogues = len(self.dialogue_after)
        if num_images == 0:
            self.dialogues_per_image = 0
        else:
            self.dialogues_per_image = max(
                1, (num_dialogues + num_images - 1) // num_images
            )

    def set_fonts(self, fonts: dict):
        self.fonts = fonts

    def update(self, dt: float):
        if not self.is_alive:
            return

        self.phase_timer += dt

        # 필름 깜빡임 효과
        self._update_flicker(dt)

        if self.phase == self.PHASE_FADEIN:
            self.fade_alpha = min(255, (self.phase_timer / self.fadein_duration) * 255)
            if self.phase_timer >= self.fadein_duration:
                self.phase = self.PHASE_FILM_ROLL
                self.phase_timer = 0.0
                self.roll_offset = -self.frame_height  # 화면 위에서 시작

        elif self.phase == self.PHASE_FILM_ROLL:
            # 필름이 위에서 아래로 롤링
            progress = min(1.0, self.phase_timer / self.roll_duration)
            eased = self._ease_out_cubic(progress)
            self.roll_offset = -self.frame_height * (1.0 - eased)

            if progress >= 1.0:
                self.roll_offset = 0
                self.phase = self.PHASE_DISPLAY
                self.phase_timer = 0.0
                self._start_dialogue()

        elif self.phase == self.PHASE_DISPLAY:
            self._update_dialogue(dt)

        elif self.phase == self.PHASE_FILM_ADVANCE:
            # 현재 프레임이 위로 롤아웃
            progress = min(1.0, self.phase_timer / self.advance_duration)
            eased = self._ease_in_cubic(progress)
            self.roll_offset = self.frame_height * eased

            if progress >= 1.0:
                self.current_frame_index += 1
                self.roll_offset = -self.frame_height

                if self.current_frame_index >= len(self.films):
                    self.phase = self.PHASE_FADEOUT
                    self.phase_timer = 0.0
                else:
                    # 다음 프레임 롤인
                    self.phase = self.PHASE_FILM_ROLL
                    self.phase_timer = 0.0

        elif self.phase == self.PHASE_FADEOUT:
            progress = self.phase_timer / self.fadeout_duration
            self.fade_alpha = 255 * (1.0 - progress)
            if self.phase_timer >= self.fadeout_duration:
                self.phase = self.PHASE_DONE
                self.is_alive = False
                if self.on_complete:
                    self.on_complete()

    def _ease_out_cubic(self, t: float) -> float:
        """Ease-out cubic for smooth deceleration"""
        return 1 - pow(1 - t, 3)

    def _ease_in_cubic(self, t: float) -> float:
        """Ease-in cubic for smooth acceleration"""
        return t * t * t

    def _update_flicker(self, dt: float):
        """필름 깜빡임 업데이트"""
        self.flicker_timer += dt
        # 간헐적으로 깜빡임 (2~4초마다)
        if random.random() < dt * 0.3:  # 약 30% 확률/초
            self.flicker_alpha = random.randint(10, 30)
        else:
            self.flicker_alpha = max(0, self.flicker_alpha - dt * 100)

    def _start_dialogue(self):
        """현재 대화 시작"""
        if self.current_dialogue_index < len(self.dialogue_after):
            self.dialogue_text = self.dialogue_after[self.current_dialogue_index].get(
                "text", ""
            )
            self.typing_progress = 0.0
            self.waiting_for_click = False
            self.dialogue_complete = False
        else:
            self.dialogue_complete = True

    def _update_dialogue(self, dt: float):
        """대사 업데이트"""
        if self.current_dialogue_index >= len(self.dialogue_after):
            self.dialogue_complete = True
            return

        if not self.waiting_for_click:
            self.typing_progress += dt * self.typing_speed
            if self.typing_progress >= len(self.dialogue_text):
                self.typing_progress = len(self.dialogue_text)
                self.waiting_for_click = True

    def _advance_to_next(self):
        """다음 대화/이미지로 진행"""
        self.current_dialogue_index += 1

        # 일정 대화마다 다음 프레임으로 전환
        if self.dialogues_per_image > 0:
            expected_image = self.current_dialogue_index // self.dialogues_per_image
            if (
                expected_image > self.current_frame_index
                and self.current_frame_index < len(self.films) - 1
            ):
                self.phase = self.PHASE_FILM_ADVANCE
                self.phase_timer = 0.0
                return

        if self.current_dialogue_index < len(self.dialogue_after):
            self._start_dialogue()
        else:
            self.dialogue_complete = True
            if self.current_frame_index >= len(self.films) - 1:
                self.phase = self.PHASE_FADEOUT
                self.phase_timer = 0.0

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.phase == self.PHASE_DISPLAY:
                if self.waiting_for_click:
                    self._advance_to_next()
                else:
                    self.typing_progress = len(self.dialogue_text)
                    self.waiting_for_click = True
                return True

        elif event.type == pygame.KEYDOWN:
            if event.key in [pygame.K_SPACE, pygame.K_RETURN]:
                return self.handle_event(
                    pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1)
                )

        return False

    def render(self, screen: pygame.Surface):
        # 배경
        if self.background:
            bg_copy = self.background.copy()
            if self.fade_alpha < 255:
                bg_copy.set_alpha(int(self.fade_alpha))
            screen.blit(bg_copy, (0, 0))

        # 필름 프레임 렌더링
        if self.phase in [
            self.PHASE_FILM_ROLL,
            self.PHASE_DISPLAY,
            self.PHASE_FILM_ADVANCE,
        ]:
            self._render_film_frame(screen)

        # 필름 스크래치
        self._render_scratches(screen)

        # 필름 깜빡임
        self._render_flicker(screen)

        # 비네트 (약하게)
        self._render_vignette(screen)

        # 대사
        if self.phase == self.PHASE_DISPLAY:
            self._render_dialogue(screen)

    def _render_film_frame(self, screen: pygame.Surface):
        """필름 프레임 렌더링 - 이미지 원본 그대로!"""
        if self.current_frame_index >= len(self.films):
            return

        screen_w, screen_h = self.screen_size
        center_x = screen_w // 2
        center_y = screen_h // 2

        # 프레임 위치 (롤링 오프셋 적용)
        frame_x = center_x - self.frame_width // 2
        frame_y = center_y - self.frame_height // 2 + int(self.roll_offset)

        # 필름 프레임 서피스 생성
        frame_surf = pygame.Surface(
            (self.frame_width, self.frame_height), pygame.SRCALPHA
        )

        # 필름 베이스 (검은색 필름 스트립)
        pygame.draw.rect(
            frame_surf, (25, 25, 30, 255), (0, 0, self.frame_width, self.frame_height)
        )

        # 좌우 스프로킷 구멍
        hole_start_y = 30
        hole_end_y = self.frame_height - 30
        for y in range(hole_start_y, hole_end_y, self.sprocket_hole_spacing):
            # 왼쪽 구멍
            pygame.draw.circle(
                frame_surf,
                (10, 10, 12, 255),
                (self.sprocket_margin // 2, y),
                self.sprocket_hole_radius,
            )
            # 구멍 테두리
            pygame.draw.circle(
                frame_surf,
                (40, 40, 45, 255),
                (self.sprocket_margin // 2, y),
                self.sprocket_hole_radius,
                2,
            )
            # 오른쪽 구멍
            pygame.draw.circle(
                frame_surf,
                (10, 10, 12, 255),
                (self.frame_width - self.sprocket_margin // 2, y),
                self.sprocket_hole_radius,
            )
            pygame.draw.circle(
                frame_surf,
                (40, 40, 45, 255),
                (self.frame_width - self.sprocket_margin // 2, y),
                self.sprocket_hole_radius,
                2,
            )

        # 이미지 영역 배경 (약간 밝은 회색)
        img_area_x = self.sprocket_margin
        img_area_y = 20
        pygame.draw.rect(
            frame_surf,
            (45, 45, 50, 255),
            (img_area_x, img_area_y, self.film_width, self.film_height),
        )

        # 이미지 원본 그대로 표시! (틴트 없음!)
        film = self.films[self.current_frame_index]
        frame_surf.blit(film["image"], (img_area_x, img_area_y))

        # 이미지 테두리
        pygame.draw.rect(
            frame_surf,
            (60, 60, 65, 255),
            (img_area_x, img_area_y, self.film_width, self.film_height),
            2,
        )

        # 프레임 번호 텍스트
        frame_num_y = img_area_y + self.film_height + 15
        if "small" in self.fonts:
            frame_text = f"FRAME {self.current_frame_index + 1:03d}"
            text_surf = self.fonts["small"].render(frame_text, True, (180, 170, 150))
            text_x = self.frame_width // 2 - text_surf.get_width() // 2
            frame_surf.blit(text_surf, (text_x, frame_num_y))

        # 페이드 적용
        if self.fade_alpha < 255:
            frame_surf.set_alpha(int(self.fade_alpha))

        screen.blit(frame_surf, (frame_x, frame_y))

    def _render_scratches(self, screen: pygame.Surface):
        """필름 스크래치 렌더링"""
        for scratch in self.scratch_lines:
            color = (200, 190, 170, scratch["alpha"])
            scratch_surf = pygame.Surface(
                (scratch["width"], self.screen_size[1]), pygame.SRCALPHA
            )
            scratch_surf.fill(color)
            screen.blit(scratch_surf, (scratch["x"], 0))

    def _render_flicker(self, screen: pygame.Surface):
        """필름 깜빡임 렌더링"""
        if self.flicker_alpha > 0:
            flicker_surf = pygame.Surface(self.screen_size, pygame.SRCALPHA)
            flicker_surf.fill((255, 250, 240, self.flicker_alpha))
            screen.blit(flicker_surf, (0, 0))

    def _render_vignette(self, screen: pygame.Surface):
        """비네트 효과 (약하게, 중립 색상)"""
        vignette = pygame.Surface(self.screen_size, pygame.SRCALPHA)
        screen_w, screen_h = self.screen_size
        center_x, center_y = screen_w // 2, screen_h // 2
        max_dist = math.sqrt(center_x**2 + center_y**2)

        # 가장자리만 약간 어둡게 (중립 톤)
        for i in range(8):
            radius = int(max_dist * (1.0 - i * 0.08))
            alpha = i * 10  # 약한 비네트
            pygame.draw.circle(
                vignette, (15, 15, 20, alpha), (center_x, center_y), radius, 60
            )

        screen.blit(vignette, (0, 0))

    def _render_dialogue(self, screen: pygame.Surface):
        """대사 박스 렌더링 (초상화 포함)"""
        if not self.dialogue_after or self.current_dialogue_index >= len(
            self.dialogue_after
        ):
            if (
                self.dialogue_complete
                and self.current_frame_index < len(self.films) - 1
            ):
                self._render_hint(screen, "클릭하여 다음 프레임")
            elif self.dialogue_complete:
                self._render_hint(screen, "클릭하여 계속")
            return
        dialogue = self.dialogue_after[self.current_dialogue_index]
        speaker = dialogue.get("speaker", "")
        portrait = self._get_portrait(speaker) if speaker else None

        # 중립적인 어두운 색상의 대화 상자
        render_dialogue_box(
            screen,
            self.screen_size,
            self.fonts,
            dialogue,
            self.dialogue_text,
            self.typing_progress,
            self.waiting_for_click,
            box_color=(25, 25, 30, 230),
            border_color=(80, 80, 90, 180),
            text_color=(240, 235, 220),
            box_height=160,
            has_portrait=(portrait is not None),
            portrait=portrait,
        )

    def _render_hint(self, screen: pygame.Surface, text: str):
        if "small" not in self.fonts:
            return
        hint_surf = self.fonts["small"].render(text, True, (180, 175, 160))
        x = self.screen_size[0] // 2 - hint_surf.get_width() // 2
        y = self.screen_size[1] - 50
        screen.blit(hint_surf, (x, y))

    def _reset_for_replay(self):
        """리플레이를 위한 상태 초기화"""
        self.phase = self.PHASE_FADEIN
        self.phase_timer = 0.0
        self.fade_alpha = 0.0
        self.current_frame_index = 0
        self.roll_offset = 0.0
        self.current_dialogue_index = 0
        self.dialogue_text = ""
        self.typing_progress = 0.0
        self.waiting_for_click = False
        self.dialogue_complete = False
        self.is_alive = True


# =========================================================
# Act 4: 깨진 거울 파편 효과 (BaseCutsceneEffect 상속)
# =========================================================
