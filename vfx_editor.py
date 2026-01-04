"""
VFX Editor - 이미지 효과 제작 툴
아티스트/디자이너가 직접 효과를 만들고 테스트할 수 있는 GUI 툴
"""

import pygame
import pygame_gui
import sys
import json
from pathlib import Path
from typing import Optional, Dict, Any

# VFXManager 임포트
from systems.vfx_manager import VFXManager
from effects.screen_effects import ImageShockwave


class VFXEditor:
    """VFX 효과 편집기 - 드래그앤드롭 + 실시간 프리뷰"""

    def __init__(self):
        pygame.init()

        # 화면 설정
        self.screen_size = (1600, 900)
        self.screen = pygame.display.set_mode(self.screen_size)
        pygame.display.set_caption("VFX Editor - 이미지 효과 제작 툴")
        self.clock = pygame.time.Clock()

        # UI 매니저
        self.ui_manager = pygame_gui.UIManager(self.screen_size, 'assets/ui/theme.json' if Path('assets/ui/theme.json').exists() else None)

        # VFX 매니저
        self.vfx_manager = VFXManager()

        # 현재 로드된 이미지
        self.current_image_path: Optional[str] = None
        self.current_image: Optional[pygame.Surface] = None
        self.image_preview_surface: Optional[pygame.Surface] = None

        # 현재 효과 설정
        self.current_config = {
            "category": "hit_effects",
            "variant": "custom",
            "max_size": 240,
            "duration": 0.8,
            "color_tint": [255, 255, 255],
            "wave_count": 3,
            "wave_interval": 0.1
        }

        # 효과 리스트
        self.effects = []

        # 자동 재생 모드
        self.auto_spawn = False
        self.auto_spawn_timer = 0
        self.auto_spawn_interval = 1.0

        # UI 생성
        self._create_ui()

        # 드래그앤드롭 영역
        self.drop_zone = pygame.Rect(50, 50, 400, 300)

        # 프리뷰 영역
        self.preview_zone = pygame.Rect(500, 50, 1050, 600)

        # 마지막 클릭 위치
        self.last_click_pos = None

        print("\n=== VFX Editor Started ===")
        print("Controls:")
        print("  - Drag & Drop PNG image to the left panel")
        print("  - Adjust sliders to modify effect")
        print("  - Click on preview area to test effect")
        print("  - Press SPACE for auto-spawn mode")
        print("  - Press ENTER to save configuration")
        print("  - Press ESC to quit\n")

    def _create_ui(self):
        """UI 요소 생성"""
        panel_width = 450
        panel_x = 10
        start_y = 370

        # 패널 배경
        self.control_panel_bg = pygame.Rect(panel_x, start_y - 10, panel_width, 510)

        # 제목 레이블
        pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(panel_x + 10, 10, 380, 30),
            text="이미지를 여기로 드래그하세요",
            manager=self.ui_manager
        )

        # 카테고리 선택
        self.category_dropdown = pygame_gui.elements.UIDropDownMenu(
            options_list=['hit_effects', 'critical_effects', 'boss_effects', 'skill_effects'],
            starting_option='hit_effects',
            relative_rect=pygame.Rect(panel_x + 10, start_y, 200, 30),
            manager=self.ui_manager
        )

        # 크기 슬라이더
        pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(panel_x + 10, start_y + 40, 150, 25),
            text=f"크기: {self.current_config['max_size']}",
            manager=self.ui_manager,
            object_id="size_label"
        )
        self.size_slider = pygame_gui.elements.UIHorizontalSlider(
            relative_rect=pygame.Rect(panel_x + 160, start_y + 40, 280, 25),
            start_value=240,
            value_range=(50, 600),
            manager=self.ui_manager,
            object_id="size_slider"
        )

        # 지속시간 슬라이더
        pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(panel_x + 10, start_y + 75, 150, 25),
            text=f"지속시간: {self.current_config['duration']}초",
            manager=self.ui_manager,
            object_id="duration_label"
        )
        self.duration_slider = pygame_gui.elements.UIHorizontalSlider(
            relative_rect=pygame.Rect(panel_x + 160, start_y + 75, 280, 25),
            start_value=0.8,
            value_range=(0.1, 3.0),
            manager=self.ui_manager,
            object_id="duration_slider"
        )

        # 색상 R 슬라이더
        pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(panel_x + 10, start_y + 110, 150, 25),
            text=f"색상 R: {self.current_config['color_tint'][0]}",
            manager=self.ui_manager,
            object_id="color_r_label"
        )
        self.color_r_slider = pygame_gui.elements.UIHorizontalSlider(
            relative_rect=pygame.Rect(panel_x + 160, start_y + 110, 280, 25),
            start_value=255,
            value_range=(0, 255),
            manager=self.ui_manager,
            object_id="color_r_slider"
        )

        # 색상 G 슬라이더
        pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(panel_x + 10, start_y + 145, 150, 25),
            text=f"색상 G: {self.current_config['color_tint'][1]}",
            manager=self.ui_manager,
            object_id="color_g_label"
        )
        self.color_g_slider = pygame_gui.elements.UIHorizontalSlider(
            relative_rect=pygame.Rect(panel_x + 160, start_y + 145, 280, 25),
            start_value=255,
            value_range=(0, 255),
            manager=self.ui_manager,
            object_id="color_g_slider"
        )

        # 색상 B 슬라이더
        pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(panel_x + 10, start_y + 180, 150, 25),
            text=f"색상 B: {self.current_config['color_tint'][2]}",
            manager=self.ui_manager,
            object_id="color_b_label"
        )
        self.color_b_slider = pygame_gui.elements.UIHorizontalSlider(
            relative_rect=pygame.Rect(panel_x + 160, start_y + 180, 280, 25),
            start_value=255,
            value_range=(0, 255),
            manager=self.ui_manager,
            object_id="color_b_slider"
        )

        # 파동 개수 슬라이더
        pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(panel_x + 10, start_y + 215, 150, 25),
            text=f"파동 개수: {self.current_config['wave_count']}",
            manager=self.ui_manager,
            object_id="wave_count_label"
        )
        self.wave_count_slider = pygame_gui.elements.UIHorizontalSlider(
            relative_rect=pygame.Rect(panel_x + 160, start_y + 215, 280, 25),
            start_value=3,
            value_range=(1, 10),
            manager=self.ui_manager,
            object_id="wave_count_slider"
        )

        # 파동 간격 슬라이더
        pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(panel_x + 10, start_y + 250, 150, 25),
            text=f"파동 간격: {self.current_config['wave_interval']}초",
            manager=self.ui_manager,
            object_id="wave_interval_label"
        )
        self.wave_interval_slider = pygame_gui.elements.UIHorizontalSlider(
            relative_rect=pygame.Rect(panel_x + 160, start_y + 250, 280, 25),
            start_value=0.1,
            value_range=(0.01, 0.5),
            manager=self.ui_manager,
            object_id="wave_interval_slider"
        )

        # 저장 버튼
        self.save_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(panel_x + 10, start_y + 290, 210, 40),
            text='저장 (ENTER)',
            manager=self.ui_manager
        )

        # 클리어 버튼
        self.clear_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(panel_x + 230, start_y + 290, 210, 40),
            text='효과 클리어 (C)',
            manager=self.ui_manager
        )

        # 자동 재생 토글
        self.auto_spawn_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(panel_x + 10, start_y + 340, 430, 40),
            text='자동 재생 OFF (SPACE)',
            manager=self.ui_manager,
            object_id="auto_spawn_button"
        )

        # 정보 텍스트박스
        self.info_textbox = pygame_gui.elements.UITextBox(
            html_text="<b>사용법:</b><br>"
                      "1. PNG 이미지를 왼쪽 패널로 드래그<br>"
                      "2. 슬라이더로 효과 조정<br>"
                      "3. 프리뷰 영역 클릭으로 테스트<br>"
                      "4. 마음에 들면 '저장' 버튼 클릭<br>"
                      "<br><b>단축키:</b><br>"
                      "SPACE - 자동 재생<br>"
                      "C - 효과 전부 제거<br>"
                      "ENTER - 설정 저장",
            relative_rect=pygame.Rect(panel_x + 10, start_y + 390, 430, 110),
            manager=self.ui_manager
        )

    def load_image(self, file_path: str):
        """이미지 로드"""
        try:
            self.current_image_path = file_path
            self.current_image = pygame.image.load(file_path).convert_alpha()

            # 프리뷰용 축소 이미지
            preview_size = min(self.drop_zone.width - 20, self.drop_zone.height - 20)
            aspect_ratio = self.current_image.get_width() / self.current_image.get_height()

            if aspect_ratio > 1:
                scaled_width = preview_size
                scaled_height = int(preview_size / aspect_ratio)
            else:
                scaled_height = preview_size
                scaled_width = int(preview_size * aspect_ratio)

            self.image_preview_surface = pygame.transform.scale(
                self.current_image,
                (scaled_width, scaled_height)
            )

            print(f"✓ Image loaded: {Path(file_path).name}")
            print(f"  Size: {self.current_image.get_size()}")

        except Exception as e:
            print(f"✗ Failed to load image: {e}")

    def update_config_from_sliders(self):
        """슬라이더 값으로 설정 업데이트"""
        self.current_config['max_size'] = int(self.size_slider.get_current_value())
        self.current_config['duration'] = round(self.duration_slider.get_current_value(), 2)
        self.current_config['color_tint'] = [
            int(self.color_r_slider.get_current_value()),
            int(self.color_g_slider.get_current_value()),
            int(self.color_b_slider.get_current_value())
        ]
        self.current_config['wave_count'] = int(self.wave_count_slider.get_current_value())
        self.current_config['wave_interval'] = round(self.wave_interval_slider.get_current_value(), 2)
        self.current_config['category'] = self.category_dropdown.selected_option

        # 레이블 업데이트
        self._update_labels()

    def _update_labels(self):
        """레이블 텍스트 업데이트"""
        labels = {
            "size_label": f"크기: {self.current_config['max_size']}",
            "duration_label": f"지속시간: {self.current_config['duration']}초",
            "color_r_label": f"색상 R: {self.current_config['color_tint'][0]}",
            "color_g_label": f"색상 G: {self.current_config['color_tint'][1]}",
            "color_b_label": f"색상 B: {self.current_config['color_tint'][2]}",
            "wave_count_label": f"파동 개수: {self.current_config['wave_count']}",
            "wave_interval_label": f"파동 간격: {self.current_config['wave_interval']}초"
        }

        for obj_id, text in labels.items():
            for element in self.ui_manager.get_root_container().elements:
                if hasattr(element, 'object_ids') and obj_id in element.object_ids:
                    element.set_text(text)

    def create_effect_at(self, pos):
        """지정 위치에 효과 생성"""
        if self.current_image is None:
            print("! No image loaded")
            return

        # 다중 파동 생성
        for i in range(self.current_config['wave_count']):
            effect = ImageShockwave(
                center=pos,
                max_size=self.current_config['max_size'],
                duration=self.current_config['duration'],
                delay=i * self.current_config['wave_interval'],
                color_tint=tuple(self.current_config['color_tint']),
                image_override=self.current_image
            )
            self.effects.append(effect)

    def save_config(self):
        """현재 설정을 JSON 파일로 저장"""
        if self.current_image_path is None:
            print("! No image loaded")
            return

        # 파일명 추출
        image_filename = Path(self.current_image_path).name
        variant_name = Path(self.current_image_path).stem

        # JSON 로드
        json_path = Path("assets/config/vfx_effects.json")
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except:
            config = {}

        # 카테고리 확인
        category = self.current_config['category']
        if category not in config:
            config[category] = {}

        # 효과 추가
        config[category][variant_name] = {
            "image": f"assets/images/vfx/combat/{category}/{image_filename}",
            "max_size": self.current_config['max_size'],
            "duration": self.current_config['duration'],
            "color_tint": self.current_config['color_tint'],
            "wave_count": self.current_config['wave_count'],
            "wave_interval": self.current_config['wave_interval'],
            "description": f"Created with VFX Editor"
        }

        # JSON 저장
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

        print(f"\n✓ Configuration saved!")
        print(f"  Category: {category}")
        print(f"  Variant: {variant_name}")
        print(f"  File: {json_path}")
        print(f"\n→ Use in game:")
        print(f"  vfx.create_multi_shockwave(pos, '{category}', '{variant_name}')\n")

    def run(self):
        """메인 루프"""
        running = True

        while running:
            time_delta = self.clock.tick(60) / 1000.0

            # 이벤트 처리
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_SPACE:
                        self.auto_spawn = not self.auto_spawn
                        status = "ON" if self.auto_spawn else "OFF"
                        self.auto_spawn_button.set_text(f'자동 재생 {status} (SPACE)')
                        print(f"Auto-spawn: {status}")
                    elif event.key == pygame.K_c:
                        self.effects.clear()
                        print("Effects cleared")
                    elif event.key == pygame.K_RETURN:
                        self.save_config()

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if self.preview_zone.collidepoint(event.pos):
                        self.create_effect_at(event.pos)
                        self.last_click_pos = event.pos

                elif event.type == pygame.DROPFILE:
                    # 드래그앤드롭으로 파일 로드
                    self.load_image(event.file)

                elif event.type == pygame_gui.UI_BUTTON_PRESSED:
                    if event.ui_element == self.save_button:
                        self.save_config()
                    elif event.ui_element == self.clear_button:
                        self.effects.clear()
                    elif event.ui_element == self.auto_spawn_button:
                        self.auto_spawn = not self.auto_spawn
                        status = "ON" if self.auto_spawn else "OFF"
                        self.auto_spawn_button.set_text(f'자동 재생 {status} (SPACE)')

                elif event.type == pygame_gui.UI_HORIZONTAL_SLIDER_MOVED:
                    self.update_config_from_sliders()

                elif event.type == pygame_gui.UI_DROP_DOWN_MENU_CHANGED:
                    self.update_config_from_sliders()

                self.ui_manager.process_events(event)

            # 자동 재생
            if self.auto_spawn and self.current_image:
                self.auto_spawn_timer += time_delta
                if self.auto_spawn_timer >= self.auto_spawn_interval:
                    # 랜덤 위치에 효과 생성
                    import random
                    pos = (
                        random.randint(self.preview_zone.left + 50, self.preview_zone.right - 50),
                        random.randint(self.preview_zone.top + 50, self.preview_zone.bottom - 50)
                    )
                    self.create_effect_at(pos)
                    self.auto_spawn_timer = 0

            # UI 업데이트
            self.ui_manager.update(time_delta)

            # 효과 업데이트
            for effect in self.effects[:]:
                effect.update(time_delta)
                if not effect.is_alive:
                    self.effects.remove(effect)

            # 렌더링
            self.screen.fill((30, 30, 35))

            # 드롭 존 그리기
            pygame.draw.rect(self.screen, (50, 50, 60), self.drop_zone, 0, 5)
            pygame.draw.rect(self.screen, (100, 100, 120), self.drop_zone, 3, 5)

            # 이미지 프리뷰
            if self.image_preview_surface:
                preview_rect = self.image_preview_surface.get_rect(center=self.drop_zone.center)
                self.screen.blit(self.image_preview_surface, preview_rect)

            # 컨트롤 패널 배경
            pygame.draw.rect(self.screen, (40, 40, 45), self.control_panel_bg, 0, 5)
            pygame.draw.rect(self.screen, (80, 80, 90), self.control_panel_bg, 2, 5)

            # 프리뷰 존 그리기
            pygame.draw.rect(self.screen, (20, 20, 25), self.preview_zone, 0, 5)
            pygame.draw.rect(self.screen, (60, 60, 70), self.preview_zone, 2, 5)

            # 효과 그리기
            for effect in self.effects:
                effect.draw(self.screen)

            # 마지막 클릭 위치 표시
            if self.last_click_pos and self.preview_zone.collidepoint(self.last_click_pos):
                pygame.draw.circle(self.screen, (100, 255, 100), self.last_click_pos, 5, 1)
                pygame.draw.line(self.screen, (100, 255, 100),
                                (self.last_click_pos[0] - 10, self.last_click_pos[1]),
                                (self.last_click_pos[0] + 10, self.last_click_pos[1]), 1)
                pygame.draw.line(self.screen, (100, 255, 100),
                                (self.last_click_pos[0], self.last_click_pos[1] - 10),
                                (self.last_click_pos[0], self.last_click_pos[1] + 10), 1)

            # UI 그리기
            self.ui_manager.draw_ui(self.screen)

            # 상태 표시
            font = pygame.font.Font(None, 20)
            status_texts = [
                f"Image: {Path(self.current_image_path).name if self.current_image_path else 'None'}",
                f"Active Effects: {len(self.effects)}",
                f"Auto-spawn: {'ON' if self.auto_spawn else 'OFF'}"
            ]
            for i, text in enumerate(status_texts):
                surf = font.render(text, True, (200, 200, 200))
                self.screen.blit(surf, (self.preview_zone.left + 10, self.preview_zone.bottom + 10 + i * 25))

            pygame.display.flip()

        pygame.quit()


if __name__ == "__main__":
    editor = VFXEditor()
    editor.run()
