"""
Story Mode Manager & Game Mode
5 Sets × 5 Waves with checkpoint and resume system
동적 배경 시스템 포함
"""

import json
import pygame
from pathlib import Path
from typing import Dict, Tuple, Optional, List
import sys
sys.path.append(str(Path(__file__).parent.parent))

import config
from mode_configs import config_story
from mode_configs import config_story_dialogue
from modes.base_mode import GameMode, ModeConfig
from systems.combat_system import CombatSystem
from systems.skill_system import SkillSystem
from systems.effect_system import EffectSystem
from systems.spawn_system import SpawnSystem, SpawnConfig
from systems.ui_system import UISystem, UIConfig
from systems.dynamic_background import DynamicBackground
from objects import (
    Player, Enemy, Bullet, ParallaxLayer, Meteor,
    BackgroundTransition, Drone, Turret,
    StoryBriefingEffect, PolaroidMemoryEffect, ShipEntranceEffect,
    DamageFlash, LevelUpEffect, BunkerCannonEffect, CombatMotionEffect,
    ClassifiedDocumentEffect, DamagedHologramEffect, FilmReelEffect,
    ShatteredMirrorEffect, StarMapEffect,
    AndromedaWorldEffect, TwoWorldsEffect, SeasonMemoryEffect
)
from asset_manager import AssetManager
from utils import (
    reset_game_data, start_wave, advance_to_next_wave, check_wave_clear,
    update_game_objects, handle_spawning, spawn_gem, generate_tactical_options,
    handle_tactical_upgrade, update_random_event, get_active_event_modifiers,
    get_next_level_threshold,
)
from ui import (
    draw_hud, draw_pause_and_over_screens, draw_shop_screen,
    draw_tactical_menu, draw_wave_prepare_screen, draw_wave_clear_screen,
    draw_boss_health_bar, draw_victory_screen, draw_skill_indicators,
    draw_random_event_ui, draw_settings_menu, HPBarShake,
)


class StoryModeManager:
    """스토리 모드 진행 관리자"""

    def __init__(self):
        """스토리 모드 매니저 초기화"""
        self.current_wave = 1  # 현재 웨이브 (1-25)
        self.completed_sets = []  # 완료한 세트 리스트
        self.checkpoint_wave = 1  # 체크포인트 웨이브
        self.save_file = Path("story_mode_save.json")

    def get_current_set(self) -> int:
        """
        현재 세트 번호 반환

        Returns:
            세트 번호 (1-5)
        """
        return config_story.get_set_number(self.current_wave)

    def get_wave_in_set(self) -> int:
        """
        현재 세트 내 웨이브 번호 반환 (1-5)

        Returns:
            세트 내 웨이브 번호
        """
        return ((self.current_wave - 1) % config_story.WAVES_PER_SET) + 1

    def is_set_complete(self) -> bool:
        """
        현재 세트가 완료되었는지 확인

        Returns:
            세트 완료 여부
        """
        return config_story.is_set_complete(self.current_wave)

    def on_wave_complete(self):
        """
        웨이브 완료 처리

        Returns:
            Tuple[bool, bool]: (세트 완료 여부, 게임 완료 여부)
        """
        set_complete = self.is_set_complete()
        game_complete = (self.current_wave >= config_story.TOTAL_WAVES)

        # 다음 웨이브로 진행
        if not game_complete:
            self.current_wave += 1

            # 세트 완료 시 체크포인트 업데이트
            if set_complete:
                current_set = self.get_current_set()
                if current_set not in self.completed_sets:
                    self.completed_sets.append(current_set)
                self.checkpoint_wave = config_story.get_checkpoint_wave(self.current_wave)
                self.save_progress()

        return (set_complete, game_complete)

    def on_player_death(self):
        """
        플레이어 사망 시 체크포인트로 복귀
        """
        self.current_wave = self.checkpoint_wave
        print(f"INFO: Returning to checkpoint - Wave {self.checkpoint_wave}")

    def get_set_info(self) -> Dict:
        """
        현재 세트 정보 반환

        Returns:
            세트 정보 딕셔너리
        """
        current_set = self.get_current_set()
        return config_story.SET_INFO.get(current_set, {})

    def get_background_path(self) -> Path:
        """
        현재 웨이브 배경 이미지 경로 반환

        Returns:
            배경 이미지 경로
        """
        return config_story.get_background_path(self.current_wave)

    def get_enemy_scaling(self) -> Dict[str, float]:
        """
        현재 세트의 적 스케일링 정보 반환

        Returns:
            스케일링 배율 딕셔너리 (hp_mult, speed_mult, damage_mult)
        """
        current_set = self.get_current_set()
        return config_story.STORY_ENEMY_SCALING.get(current_set, {
            "hp_mult": 1.0,
            "speed_mult": 1.0,
            "damage_mult": 1.0,
        })

    def get_set_reward(self) -> Dict[str, int]:
        """
        현재 세트 완료 보상 반환

        Returns:
            보상 딕셔너리 (coins, gems)
        """
        current_set = self.get_current_set()
        return config_story.SET_CLEAR_REWARDS.get(current_set, {
            "coins": 0,
            "gems": 0,
        })

    def save_progress(self):
        """진행도 저장"""
        save_data = {
            "current_wave": self.current_wave,
            "completed_sets": self.completed_sets,
            "checkpoint_wave": self.checkpoint_wave,
        }

        try:
            with open(self.save_file, "w", encoding="utf-8") as f:
                json.dump(save_data, f, indent=2)
            print(f"INFO: Story Mode progress saved (Wave {self.current_wave})")
        except Exception as e:
            print(f"ERROR: Failed to save Story Mode progress: {e}")

    def load_progress(self) -> bool:
        """
        진행도 로드

        Returns:
            로드 성공 여부
        """
        if not self.save_file.exists():
            print("INFO: No Story Mode save file found")
            return False

        try:
            with open(self.save_file, "r", encoding="utf-8") as f:
                save_data = json.load(f)

            self.current_wave = save_data.get("current_wave", 1)
            self.completed_sets = save_data.get("completed_sets", [])
            self.checkpoint_wave = save_data.get("checkpoint_wave", 1)

            print(f"INFO: Story Mode progress loaded (Wave {self.current_wave})")
            return True

        except Exception as e:
            print(f"ERROR: Failed to load Story Mode progress: {e}")
            return False

    def reset_progress(self):
        """진행도 초기화 (새 게임)"""
        self.current_wave = 1
        self.completed_sets = []
        self.checkpoint_wave = 1
        print("INFO: Story Mode progress reset")

    def can_resume(self) -> bool:
        """
        이어하기 가능 여부 확인

        Returns:
            이어하기 가능 여부
        """
        return self.save_file.exists() and self.current_wave > 1

    def get_progress_summary(self) -> str:
        """
        진행도 요약 문자열 반환

        Returns:
            진행도 요약 (예: "Set 2 - Wave 8/25")
        """
        current_set = self.get_current_set()
        wave_in_set = self.get_wave_in_set()
        return f"Set {current_set} - Wave {wave_in_set}/5 (Total: {self.current_wave}/25)"


# =========================================================
# StoryMode - 동적 배경 적용 게임 모드
# =========================================================

class StoryMode(GameMode):
    """
    스토리 모드 (동적 배경 시스템)

    특징:
    - 동적 배경 시스템 (웨이브별 색상 변환)
    - 적 처치 시 배경 펄스 효과
    - 5웨이브 클리어 목표
    """

    def get_config(self) -> ModeConfig:
        """스토리 모드 설정"""
        return ModeConfig(
            mode_name="story",
            perspective_enabled=True,
            perspective_apply_to_player=True,
            perspective_apply_to_enemies=True,
            perspective_apply_to_bullets=True,
            perspective_apply_to_gems=True,
            player_speed_multiplier=1.0,
            player_start_pos=(self.screen_size[0] // 2, self.screen_size[1] // 2),
            player_afterimages_enabled=True,
            background_type="dynamic",
            parallax_enabled=True,
            meteor_enabled=True,
            show_wave_ui=True,
            show_stage_ui=False,
            show_minimap=False,
            show_skill_indicators=True,
            wave_system_enabled=True,
            spawn_system_enabled=True,
            random_events_enabled=True,
            asset_prefix="story",
        )

    def init(self):
        """스토리 모드 초기화"""
        config.GAME_MODE = "story"

        # 시스템 초기화
        self.combat_system = CombatSystem()
        self.skill_system = SkillSystem()
        self.effect_system = EffectSystem()
        self.spawn_system = SpawnSystem(SpawnConfig(
            enemy_spawn_interval=1.0,
            enemy_spawn_count=1,
            boss_enabled=True,
        ))
        self.ui_system = UISystem(UIConfig(
            show_hp_bar=True,
            show_score=True,
            show_wave_info=True,
            show_level_info=True,
            show_skill_indicators=True,
        ))

        # 게임 데이터 초기화
        self.game_data = reset_game_data()
        self.game_data['score'] = self.engine.shared_state.get('global_score', 0)
        self.game_data['game_state'] = config.GAME_STATE_WAVE_PREPARE
        self.game_data['wave_phase'] = 'normal'
        self.game_data['max_waves'] = 5  # 스토리 모드는 5웨이브

        # 플레이어 생성
        self.spawn_player(
            pos=self.config.player_start_pos,
            upgrades=self.engine.shared_state.get('player_upgrades', {})
        )

        # 패럴랙스 배경 생성
        self._init_parallax_layers()

        # 유성 효과
        self.meteors: List[Meteor] = []
        self.meteor_spawned_this_wave = False

        # =========================================================
        # 2막 벙커 포신 연출 효과 (동적 배경보다 먼저 초기화)
        # =========================================================
        self.bunker_cannon = BunkerCannonEffect(
            screen_size=self.screen_size,
            position=(self.screen_size[0] * 0.85, self.screen_size[1] - 200)  # 화면 하단 200픽셀 위
        )
        # 포탄 폭발 시 콜백 설정
        self.bunker_cannon.on_shell_explode = self._on_cannon_shell_explode

        # 동적 배경 시스템
        self.dynamic_background: Optional[DynamicBackground] = None
        self._init_dynamic_background()

        # 킬 카운트 추적
        self.last_kill_count = 0
        self.current_wave_bg = 0

        # 설정 메뉴 관련
        self.settings_bars = {}
        self.dragging_bgm = False
        self.dragging_sfx = False

        # 메뉴 버튼 클릭 영역 (마우스 클릭 지원)
        self.menu_button_rects: Dict[str, pygame.Rect] = {}

        # 시각적 피드백 효과
        self.damage_flash = DamageFlash(self.screen_size)
        self.level_up_effect = LevelUpEffect(self.screen_size)
        self.hp_bar_shake = HPBarShake()

        # 전투 모션 효과 (고속 비행 연출)
        self.combat_motion_effect = CombatMotionEffect(self.screen_size)
        self.player_prev_pos = None  # 이동 감지용

        # =========================================================
        # 스토리 시스템 초기화
        # =========================================================
        self.current_set = 1  # 현재 세트 (1-5)
        self.story_manager = StoryModeManager()

        # 컷씬 관련
        self.active_cutscene = None  # 현재 활성 컷씬 (StoryBriefingEffect 또는 PolaroidMemoryEffect)
        self.cutscene_queue = []  # 대기 중인 컷씬들

        # 브리핑 표시 여부
        self.set_briefing_shown = False  # 세트 오프닝 브리핑
        self.memory_cutscene_shown = False  # 1막 회상 컷씬
        self.act_cutscene_shown = False  # Act 2~5 컷씬 표시 여부
        self.boss_intro_shown = False  # 보스 등장 대사 표시 여부
        self.boss_defeat_shown = False  # 보스 처치 대사 표시 여부
        self.set_ending_shown = False  # 세트 엔딩 대사 표시 여부
        self.mid_dialogue_shown_waves = set()  # 중간 대사가 표시된 웨이브 번호들

        # 스토리 상태
        self.story_state = "normal"  # normal, briefing, memory_cutscene, act_cutscene, boss_intro, boss_defeat, ending, mid_dialogue

        # =========================================================
        # 실시간 전투 대사 시스템
        # =========================================================
        self.combat_dialogue_active = False  # 전투 대사 표시 중
        self.combat_dialogue_text = ""  # 현재 대사 텍스트
        self.combat_dialogue_speaker = ""  # 화자 (ARTEMIS, PILOT, SYSTEM)
        self.combat_dialogue_timer = 0.0  # 대사 표시 타이머
        self.combat_dialogue_duration = 3.0  # 대사 표시 시간 (초)
        self.last_kill_milestone = 0  # 마지막 킬 마일스톤
        self.last_hp_threshold = 100  # 마지막 HP 임계값 (%)
        self.shown_enemy_dialogues = set()  # 이미 표시한 특수 적 대사
        self.boss_phase_shown = set()  # 이미 표시한 보스 페이즈 대사

        # =========================================================
        # 웨이브 목표 시스템
        # =========================================================
        self.current_objective = None  # 현재 웨이브 목표
        self.objective_progress = 0  # 목표 진행도
        self.objective_target = 0  # 목표 달성 기준
        self.survival_timer = 0.0  # SURVIVAL 목표용 타이머
        self.defense_hp = 0  # DEFENSE 목표용 방어 대상 HP
        self.defense_max_hp = 0  # DEFENSE 목표 최대 HP
        self.collected_data = 0  # (레거시) 기존 DATA_COLLECT용
        self.total_collected_data = 0  # 컷씬 완료 후 수집된 전체 데이터
        self.escort_progress = 0.0  # ESCORT 목표용 진행률
        self.rescued_count = 0  # RESCUE 목표용 구출 수
        self.rescue_targets = []  # RESCUE 목표용 구출 대상 NPC 리스트

        # =========================================================
        # 환경 메커니즘 시스템
        # =========================================================
        self.environment_timer = 0.0  # 환경 효과 타이머
        self.environment_warning_active = False  # 환경 경고 활성화
        self.safe_zone_radius = 0  # 안전 구역 반경 (화염 수축용)
        self.emp_active = False  # EMP 효과 활성화
        self.emp_timer = 0.0  # EMP 효과 타이머

        print("INFO: StoryMode initialized with story system")

    def _init_parallax_layers(self):
        """패럴랙스 레이어 초기화"""
        self.parallax_layers = []
        for layer_config in config.PARALLAX_LAYERS:
            layer = ParallaxLayer(
                screen_size=self.screen_size,
                star_count=layer_config["star_count"],
                speed_factor=layer_config["speed_factor"],
                star_size=layer_config["star_size"],
                color=layer_config["color"],
                twinkle=layer_config.get("twinkle", False)
            )
            self.parallax_layers.append(layer)

    def _init_dynamic_background(self):
        """스토리 모드 배경 시스템 초기화 (지구 배경)"""
        # 스토리 모드는 정적 배경 이미지 사용
        self.story_background = None
        self.current_bg_path = None
        self._load_story_background(1)  # 1막 배경으로 시작

        # 동적 배경은 사용하지 않음
        self.dynamic_background = None
        print("INFO: StoryMode static background initialized (Earth)")

    def _load_story_background(self, wave_num: int):
        """스토리 모드 배경 이미지 로드"""
        bg_path = config_story.get_background_path(wave_num)

        # 이미 같은 배경이면 스킵
        if str(bg_path) == self.current_bg_path:
            return

        try:
            img = pygame.image.load(str(bg_path)).convert()
            self.story_background = pygame.transform.scale(img, self.screen_size)
            self.current_bg_path = str(bg_path)
            print(f"INFO: Loaded story background: {bg_path}")
        except Exception as e:
            print(f"WARNING: Failed to load story background {bg_path}: {e}")
            # 폴백: 검은 배경
            self.story_background = pygame.Surface(self.screen_size)
            self.story_background.fill((20, 20, 30))

        # 2막 (웨이브 6-10): 벙커 포신 활성화
        current_set = config_story.get_set_number(wave_num)
        if current_set == 2:
            if not self.bunker_cannon.is_active:
                self.bunker_cannon.activate()
                print("INFO: Bunker cannon activated for Act 2")
        else:
            if self.bunker_cannon.is_active:
                self.bunker_cannon.deactivate()
                print("INFO: Bunker cannon deactivated")

    # =========================================================
    # 스토리 컷씬 메서드
    # =========================================================
    def _show_set_briefing(self):
        """세트 오프닝 브리핑 표시"""
        set_num = self.current_set
        briefing_data = config_story_dialogue.get_set_opening(set_num)

        if not briefing_data or not briefing_data.get("dialogues"):
            self.set_briefing_shown = True
            return

        # 배경 이미지 경로
        bg_filename = config_story.STORY_BACKGROUNDS.get(
            (set_num - 1) * 5 + 1, "bg_ruins.jpg"
        )
        bg_path = f"assets/story_mode/backgrounds/{bg_filename}"

        # 1막: 비행선 진입 + 선회 연출 사용
        if set_num == 1:
            entrance_effect = ShipEntranceEffect(
                screen_size=self.screen_size,
                player=self.player,
                dialogue_data=briefing_data["dialogues"],
                background_path=bg_path,
                title=briefing_data.get("title", ""),
                location=briefing_data.get("location", "")
            )
            entrance_effect.set_fonts(self.fonts)
            entrance_effect.on_complete = self._on_briefing_complete

            self.active_cutscene = entrance_effect
            self.story_state = "briefing"
            print(f"INFO: Showing set {set_num} ship entrance effect")
        else:
            # 2막 이후: 기존 브리핑 효과 사용
            briefing = StoryBriefingEffect(
                screen_size=self.screen_size,
                dialogue_data=briefing_data["dialogues"],
                background_path=bg_path,
                title=briefing_data.get("title", ""),
                location=briefing_data.get("location", "")
            )
            briefing.set_fonts(self.fonts)
            briefing.on_complete = self._on_briefing_complete

            self.active_cutscene = briefing
            self.story_state = "briefing"
            print(f"INFO: Showing set {set_num} briefing")

    def _on_cannon_shell_explode(self, pos, damage: float, radius: float):
        """포탄 폭발 콜백 - 범위 내 적에게 데미지"""
        from objects import Shockwave, Particle
        import random

        # 폭발 이펙트 생성
        shockwave = Shockwave(
            center=(pos.x, pos.y),
            max_radius=radius,
            duration=0.4,
            color=(255, 200, 100)
        )
        self.effects.append(shockwave)

        # 파티클 생성
        for _ in range(15):
            particle = Particle(
                pos=(pos.x + random.uniform(-10, 10), pos.y + random.uniform(-10, 10)),
                velocity=pygame.math.Vector2(random.uniform(-150, 150), random.uniform(-150, 150)),
                color=(255, random.randint(150, 200), random.randint(50, 100)),
                lifetime=random.uniform(0.3, 0.6),
                size=int(random.uniform(3, 6))
            )
            self.effects.append(particle)

        # 범위 내 적에게 데미지
        for enemy in self.enemies:
            if not enemy.is_alive:
                continue

            dist = ((enemy.pos.x - pos.x) ** 2 + (enemy.pos.y - pos.y) ** 2) ** 0.5
            if dist <= radius:
                # 거리에 따른 데미지 감소
                damage_mult = 1.0 - (dist / radius) * 0.5
                actual_damage = damage * damage_mult
                enemy.take_damage(actual_damage)

                # 데미지 넘버 표시 (매니저 사용)
                if hasattr(self, 'damage_number_manager') and self.damage_number_manager:
                    self.damage_number_manager.add_damage(
                        int(actual_damage),
                        (enemy.pos.x, enemy.pos.y - 20),
                        target_id=id(enemy)
                    )
                else:
                    from objects import DamageNumber
                    dmg_num = DamageNumber(
                        damage=int(actual_damage),
                        pos=(enemy.pos.x, enemy.pos.y - 20)
                    )
                    self.damage_numbers.append(dmg_num)

    def _on_briefing_complete(self):
        """브리핑 완료 콜백"""
        self.active_cutscene = None
        self.set_briefing_shown = True
        self.story_state = "normal"
        print("INFO: Briefing complete")

        # 브리핑 완료 후 웨이브 시작
        start_wave(self.game_data, pygame.time.get_ticks() / 1000.0, self.enemies)
        self.game_data["game_state"] = config.GAME_STATE_RUNNING

        new_wave = self.game_data["current_wave"]
        self.sound_manager.play_wave_bgm(new_wave)

        # 스토리 배경 업데이트
        self._load_story_background(new_wave)
        self.last_kill_count = 0

        # 전투 모션 효과 리셋 (웨이브당 2회)
        self.combat_motion_effect.reset_wave()

        # =========================================================
        # 새 시스템 초기화 (웨이브 시작 시)
        # =========================================================
        self._init_wave_objective(new_wave)
        self._init_act_mechanics()
        self._reset_combat_dialogue_state()
        self.environment_timer = 0.0

    def _show_memory_cutscene(self):
        """1막 회상 컷씬 표시 (폴라로이드)"""
        memory_data = config_story_dialogue.get_memory_cutscene(1)

        if not memory_data:
            self.memory_cutscene_shown = True
            return

        # 폴라로이드 이미지 경로 리스트
        polaroid_paths = [
            f"assets/story_mode/polaroids/{img}"
            for img in memory_data.get("polaroid_images", [])
        ]

        # 배경 이미지 경로
        bg_filename = config_story.SPECIAL_BACKGROUNDS.get("cemetery", "bg_cemetery.jpg")
        bg_path = f"assets/story_mode/backgrounds/{bg_filename}"

        # 특수 효과 설정 가져오기
        special_effects = memory_data.get("special_effects", {})

        # 씬 ID 생성 (세트 번호 기반)
        scene_id = f"memory_scene_{self.current_set:02d}"

        # 회상 효과 생성
        memory_effect = PolaroidMemoryEffect(
            screen_size=self.screen_size,
            photo_paths=polaroid_paths,
            background_path=bg_path,
            dialogue_after=memory_data.get("dialogue_after", []),
            dialogue_per_photo=memory_data.get("dialogue_per_photo", []),
            sound_manager=self.sound_manager,
            special_effects=special_effects,
            scene_id=scene_id
        )
        memory_effect.set_fonts(self.fonts)
        memory_effect.on_complete = self._on_memory_complete
        memory_effect.on_replay_request = self._on_memory_replay_request

        self.active_cutscene = memory_effect
        self.story_state = "memory_cutscene"

        # 회상 BGM 재생 (있다면)
        if self.sound_manager and memory_data.get("bgm"):
            # TODO: 회상용 BGM 재생
            pass

        print(f"INFO: Showing memory cutscene (scene_id: {scene_id})")

    def _on_memory_replay_request(self, scene_id: str):
        """메모리 씬 리플레이 요청 콜백"""
        print(f"INFO: Replay requested for {scene_id}")

        # 현재 컷씬이 PolaroidMemoryEffect인 경우 자체 리셋 수행
        if self.active_cutscene and hasattr(self.active_cutscene, '_reset_for_replay'):
            self.active_cutscene._reset_for_replay()

    def _on_memory_complete(self):
        """회상 컷씬 완료 콜백"""
        self.active_cutscene = None
        self.memory_cutscene_shown = True
        self.story_state = "normal"
        print("INFO: Memory cutscene complete")

        # 회상 완료 후 다음 웨이브로 진행
        advance_to_next_wave(self.game_data, self.player, self.sound_manager)

    def _show_act_cutscene(self):
        """Act 2~5 컷씬 표시 (기밀문서, 홀로그램, 깨진거울, 스타맵)"""
        try:
            cutscene_data = config_story_dialogue.get_cutscene_data(self.current_set)

            if not cutscene_data:
                self.act_cutscene_shown = True
                print(f"INFO: No cutscene data for Act {self.current_set}")
                return

            cutscene_type = cutscene_data.get("cutscene_type", "")
            bg_filename = cutscene_data.get("background", "bg_bunker.jpg")
            bg_path = f"assets/story_mode/backgrounds/{bg_filename}"
            dialogue_after = cutscene_data.get("dialogue_after", [])
            special_effects = cutscene_data.get("special_effects", {})
            scene_id = f"act_cutscene_{self.current_set:02d}"

            effect = None

            if cutscene_type == "classified_document":
                # Act 2: 기밀 문서 뷰어
                doc_paths = [
                    f"assets/story_mode/documents/{img}"
                    for img in cutscene_data.get("document_images", [])
                ]
                gate_paths = [
                    f"assets/story_mode/documents/{img}"
                    for img in cutscene_data.get("gate_images", [])
                ]
                effect = ClassifiedDocumentEffect(
                    screen_size=self.screen_size,
                    document_paths=doc_paths,
                    background_path=bg_path,
                    dialogue_after=dialogue_after,
                    special_effects=special_effects,
                    scene_id=scene_id,
                    gate_image_paths=gate_paths if gate_paths else None
                )

            elif cutscene_type in ["damaged_hologram", "film_reel"]:
                # Act 3: 필름 릴 효과 (이미지 원본 유지)
                film_paths = [
                    f"assets/story_mode/holograms/{img}"
                    for img in cutscene_data.get("film_images", cutscene_data.get("hologram_images", []))
                ]
                effect = FilmReelEffect(
                    screen_size=self.screen_size,
                    film_paths=film_paths,
                    background_path=bg_path,
                    dialogue_after=dialogue_after,
                    special_effects=special_effects,
                    scene_id=scene_id
                )

            elif cutscene_type == "shattered_mirror":
                # Act 4: 깨진 거울 파편
                frag_paths = [
                    f"assets/story_mode/fragments/{img}"
                    for img in cutscene_data.get("fragment_images", [])
                ]
                effect = ShatteredMirrorEffect(
                    screen_size=self.screen_size,
                    fragment_paths=frag_paths,
                    background_path=bg_path,
                    dialogue_after=dialogue_after,
                    special_effects=special_effects,
                    scene_id=scene_id
                )

            elif cutscene_type == "star_map":
                # Act 5: 성간 항해 인터페이스
                marker_paths = [
                    f"assets/story_mode/starmap/{img}"
                    for img in cutscene_data.get("marker_images", [])
                ]
                marker_positions = cutscene_data.get("marker_positions", {})
                route_order = cutscene_data.get("route_order", [])
                effect = StarMapEffect(
                    screen_size=self.screen_size,
                    marker_paths=marker_paths,
                    marker_positions=marker_positions,
                    route_order=route_order,
                    background_path=bg_path,
                    dialogue_after=dialogue_after,
                    scene_id=scene_id
                )

            if effect:
                effect.set_fonts(self.fonts)
                effect.on_complete = self._on_act_cutscene_complete
                if hasattr(effect, 'on_replay_request'):
                    effect.on_replay_request = self._on_act_cutscene_replay_request

                self.active_cutscene = effect
                self.story_state = "act_cutscene"
                print(f"INFO: Showing Act {self.current_set} cutscene ({cutscene_type}, scene_id: {scene_id})")
            else:
                self.act_cutscene_shown = True
                print(f"WARNING: Unknown cutscene type: {cutscene_type}")

        except Exception as e:
            # 컷씬 생성 실패 시 스킵하고 게임 진행
            print(f"ERROR: Failed to create Act {self.current_set} cutscene: {e}")
            import traceback
            traceback.print_exc()
            self.act_cutscene_shown = True
            self.active_cutscene = None
            self.story_state = "normal"
            # 컷씬 스킵하고 다음 웨이브로 진행
            advance_to_next_wave(self.game_data, self.player, self.sound_manager)

    def _on_act_cutscene_complete(self):
        """Act 2~5 컷씬 완료 콜백"""
        self.active_cutscene = None
        self.act_cutscene_shown = True
        self.story_state = "normal"
        print(f"INFO: Act {self.current_set} cutscene complete")

        # 컷씬 완료 후 데이터 수집 처리
        self._process_cutscene_data_collection()

        # 컷씬 완료 후 다음 웨이브로 진행
        advance_to_next_wave(self.game_data, self.player, self.sound_manager)

    def _process_cutscene_data_collection(self):
        """컷씬 완료 후 데이터 수집 처리"""
        set_info = config_story.SET_INFO.get(self.current_set, {})
        data_count = set_info.get("data_collect_after_cutscene", 0)
        data_name = set_info.get("data_collect_name", "데이터")

        if data_count > 0:
            # 전체 수집 데이터 카운트 증가
            if not hasattr(self, 'total_collected_data'):
                self.total_collected_data = 0
            self.total_collected_data += data_count

            # 데이터 수집 알림 표시
            print(f"INFO: Data collected after cutscene! +{data_count} {data_name}")
            print(f"INFO: Total collected data: {self.total_collected_data}")

            # UI에 수집 알림 표시 (선택적)
            if hasattr(self, 'show_notification'):
                self.show_notification(f"{data_name} x{data_count} 획득!")

    def _on_act_cutscene_replay_request(self, scene_id: str):
        """Act 컷씬 리플레이 요청 콜백"""
        print(f"INFO: Replay requested for {scene_id}")

        if self.active_cutscene and hasattr(self.active_cutscene, '_reset_for_replay'):
            self.active_cutscene._reset_for_replay()

    def _check_act_cutscene_trigger(self, current_wave: int) -> bool:
        """Act 2~5 컷씬 트리거 체크 (전체 웨이브 번호로 비교)"""
        set_info = config_story.SET_INFO.get(self.current_set, {})

        has_cutscene = set_info.get("has_cutscene", False)
        trigger_wave = set_info.get("cutscene_trigger_wave", 0)

        print(f"DEBUG: Act cutscene check - current_wave={current_wave}, set={self.current_set}, "
              f"has_cutscene={has_cutscene}, trigger_wave={trigger_wave}, shown={self.act_cutscene_shown}")

        if has_cutscene:
            # current_wave는 전체 웨이브 번호 (1~25)
            # trigger_wave도 전체 웨이브 번호 (7, 12, 17, 22)
            if current_wave == trigger_wave and not self.act_cutscene_shown:
                print(f"DEBUG: Act cutscene TRIGGERED for Act {self.current_set}")
                return True
        return False

    def _show_wave_mid_dialogue(self, wave_num: int):
        """웨이브 중간 대사 표시"""
        dialogues = config_story_dialogue.get_wave_mid_dialogue(self.current_set, wave_num)

        if not dialogues:
            self.mid_dialogue_shown_waves.add(wave_num)
            return

        # 이 웨이브에서 대사를 표시했음을 기록
        self.mid_dialogue_shown_waves.add(wave_num)

        # 현재 배경 사용
        bg_filename = config_story.STORY_BACKGROUNDS.get(wave_num, "bg_ruins.jpg")
        bg_path = f"assets/story_mode/backgrounds/{bg_filename}"

        briefing = StoryBriefingEffect(
            screen_size=self.screen_size,
            dialogue_data=dialogues,
            background_path=bg_path
        )
        briefing.set_fonts(self.fonts)
        briefing.on_complete = self._on_mid_dialogue_complete

        self.active_cutscene = briefing
        self.story_state = "mid_dialogue"
        print(f"INFO: Wave mid dialogue started for Wave {wave_num} (Act {self.current_set})")

    def _on_mid_dialogue_complete(self):
        """중간 대사 완료 콜백"""
        self.active_cutscene = None
        self.story_state = "normal"

        current_wave = self.game_data["current_wave"]
        wave_in_set = ((current_wave - 1) % config_story.WAVES_PER_SET) + 1

        # 중간 대사 완료 후 회상 컷씬 체크 (1막 웨이브 2 클리어 후)
        if self._check_memory_trigger(wave_in_set):
            self._show_memory_cutscene()
            return

        # 중간 대사 완료 후 Act 컷씬 체크 (같은 웨이브에 컷씬이 있을 수 있음)
        if self._check_act_cutscene_trigger(current_wave):
            self._show_act_cutscene()
            return

        # 컷씬이 없으면 다음 웨이브로 진행
        advance_to_next_wave(self.game_data, self.player, self.sound_manager)

    def _check_mid_dialogue_trigger(self, current_wave: int) -> bool:
        """웨이브 중간 대사 트리거 체크"""
        # 이미 이 웨이브에서 대사를 표시했으면 스킵
        if current_wave in self.mid_dialogue_shown_waves:
            return False

        # WAVE_MID_DIALOGUES에서 (세트번호, 웨이브번호) 키 확인
        dialogues = config_story_dialogue.get_wave_mid_dialogue(self.current_set, current_wave)
        return len(dialogues) > 0

    # =========================================================
    # 보스 대사 관련 함수들
    # =========================================================
    def _show_boss_intro_dialogue(self):
        """보스 등장 대사 표시"""
        dialogues = config_story_dialogue.get_boss_dialogue(self.current_set, "intro")

        if not dialogues:
            self.boss_intro_shown = True
            return

        # 현재 배경 사용
        current_wave = self.game_data["current_wave"]
        bg_filename = config_story.STORY_BACKGROUNDS.get(current_wave, "bg_ruins.jpg")
        bg_path = f"assets/story_mode/backgrounds/{bg_filename}"

        briefing = StoryBriefingEffect(
            screen_size=self.screen_size,
            dialogue_data=dialogues,
            background_path=bg_path
        )
        briefing.set_fonts(self.fonts)
        briefing.on_complete = self._on_boss_intro_complete

        self.active_cutscene = briefing
        self.story_state = "boss_intro"
        print(f"INFO: Boss intro dialogue started for Act {self.current_set}")

    def _on_boss_intro_complete(self):
        """보스 등장 대사 완료 콜백"""
        self.active_cutscene = None
        self.story_state = "normal"
        self.boss_intro_shown = True

        # 보스 등장 대사 완료 후 웨이브 시작
        start_wave(self.game_data, pygame.time.get_ticks() / 1000.0, self.enemies)
        self.game_data["game_state"] = config.GAME_STATE_RUNNING

        new_wave = self.game_data["current_wave"]
        self.sound_manager.play_wave_bgm(new_wave)

        # 스토리 배경 업데이트
        self._load_story_background(new_wave)
        self.last_kill_count = 0

        # 전투 모션 효과 리셋 (웨이브당 2회)
        self.combat_motion_effect.reset_wave()

        # 새 시스템 초기화 (웨이브 시작 시)
        self._init_wave_objective(new_wave)
        self._init_act_mechanics()
        self._reset_combat_dialogue_state()
        self.environment_timer = 0.0

        print(f"INFO: Boss Wave {new_wave} started")

    def _show_boss_defeat_dialogue(self):
        """보스 처치 대사 표시"""
        dialogues = config_story_dialogue.get_boss_dialogue(self.current_set, "defeat")

        if not dialogues:
            self.boss_defeat_shown = True
            return

        # 현재 배경 사용
        current_wave = self.game_data["current_wave"]
        bg_filename = config_story.STORY_BACKGROUNDS.get(current_wave, "bg_ruins.jpg")
        bg_path = f"assets/story_mode/backgrounds/{bg_filename}"

        briefing = StoryBriefingEffect(
            screen_size=self.screen_size,
            dialogue_data=dialogues,
            background_path=bg_path
        )
        briefing.set_fonts(self.fonts)
        briefing.on_complete = self._on_boss_defeat_complete

        self.active_cutscene = briefing
        self.story_state = "boss_defeat"
        print(f"INFO: Boss defeat dialogue started for Act {self.current_set}")

    def _on_boss_defeat_complete(self):
        """보스 처치 대사 완료 콜백"""
        self.active_cutscene = None
        self.story_state = "normal"
        self.boss_defeat_shown = True

    # =========================================================
    # 세트 엔딩 대사 관련 함수들
    # =========================================================
    def _show_set_ending_dialogue(self):
        """세트 엔딩 대사 표시"""
        dialogues = config_story_dialogue.get_set_ending(self.current_set)

        if not dialogues:
            self.set_ending_shown = True
            return

        # 현재 배경 사용
        current_wave = self.game_data["current_wave"]
        bg_filename = config_story.STORY_BACKGROUNDS.get(current_wave, "bg_ruins.jpg")
        bg_path = f"assets/story_mode/backgrounds/{bg_filename}"

        briefing = StoryBriefingEffect(
            screen_size=self.screen_size,
            dialogue_data=dialogues,
            background_path=bg_path
        )
        briefing.set_fonts(self.fonts)
        briefing.on_complete = self._on_set_ending_complete

        self.active_cutscene = briefing
        self.story_state = "ending"
        print(f"INFO: Set ending dialogue started for Act {self.current_set}")

    def _on_set_ending_complete(self):
        """세트 엔딩 대사 완료 콜백"""
        self.active_cutscene = None
        self.story_state = "normal"
        self.set_ending_shown = True

        # 다음 세트로 진행
        advance_to_next_wave(self.game_data, self.player, self.sound_manager)

    # =========================================================
    # 실시간 전투 대사 시스템
    # =========================================================
    def _show_combat_dialogue(self, speaker: str, text: str, duration: float = 3.0):
        """실시간 전투 대사 표시"""
        self.combat_dialogue_active = True
        self.combat_dialogue_speaker = speaker
        self.combat_dialogue_text = text
        self.combat_dialogue_timer = 0.0
        self.combat_dialogue_duration = duration
        print(f"INFO: Combat dialogue - [{speaker}] {text[:30]}...")

    def _update_combat_dialogue(self, dt: float):
        """전투 대사 업데이트"""
        if not self.combat_dialogue_active:
            return

        self.combat_dialogue_timer += dt
        if self.combat_dialogue_timer >= self.combat_dialogue_duration:
            self.combat_dialogue_active = False
            self.combat_dialogue_text = ""
            self.combat_dialogue_speaker = ""

    def _check_combat_dialogue_triggers(self, dt: float):
        """전투 대사 트리거 체크"""
        if self.combat_dialogue_active:
            return  # 이미 대사 표시 중이면 스킵

        current_wave = self.game_data.get("current_wave", 1)

        # 1. 킬 마일스톤 체크
        self._check_kill_milestone_dialogue(current_wave)

        # 2. HP 임계값 체크
        self._check_hp_threshold_dialogue()

        # 3. 특수 적 등장 체크
        self._check_special_enemy_dialogue()

        # 4. 보스 페이즈 대사 체크
        self._check_boss_phase_dialogue()

        # 5. 목표 진행률 대사 체크
        self._check_objective_progress_dialogue()

    def _check_kill_milestone_dialogue(self, current_wave: int):
        """킬 마일스톤 대사 체크"""
        kills = self.game_data.get("kills_this_wave", 0)
        milestones = [5, 10, 15, 20, 25, 30]

        for milestone in milestones:
            if kills >= milestone and self.last_kill_milestone < milestone:
                self.last_kill_milestone = milestone
                dialogue = config_story_dialogue.get_combat_dialogue(
                    "kill_milestone", self.current_set, milestone
                )
                if dialogue:
                    self._show_combat_dialogue(
                        dialogue.get("speaker", "ARTEMIS"),
                        dialogue.get("text", ""),
                        dialogue.get("duration", 2.5)
                    )
                break

    def _check_hp_threshold_dialogue(self):
        """HP 임계값 대사 체크"""
        if not self.player:
            return

        hp_percent = (self.player.hp / self.player.max_hp) * 100
        thresholds = [50, 25, 10]

        for threshold in thresholds:
            if hp_percent <= threshold and self.last_hp_threshold > threshold:
                self.last_hp_threshold = threshold
                dialogue = config_story_dialogue.get_combat_dialogue(
                    "hp_threshold", self.current_set, threshold
                )
                if dialogue:
                    self._show_combat_dialogue(
                        dialogue.get("speaker", "PILOT"),
                        dialogue.get("text", ""),
                        dialogue.get("duration", 2.5)
                    )
                break

    def _check_special_enemy_dialogue(self):
        """특수 적 등장 대사 체크"""
        for enemy in self.enemies:
            if not enemy.is_alive:
                continue

            enemy_type = getattr(enemy, 'enemy_type', None)
            if not enemy_type:
                continue

            # 이미 이 타입 대사를 표시했으면 스킵
            dialogue_key = f"{self.current_set}_{enemy_type}"
            if dialogue_key in self.shown_enemy_dialogues:
                continue

            # 특수 적 타입 체크 (TANK, SUMMONER, KAMIKAZE 등)
            special_types = ["TANK", "SUMMONER", "KAMIKAZE", "HARVESTER", "DISRUPTOR"]
            if enemy_type in special_types:
                self.shown_enemy_dialogues.add(dialogue_key)
                dialogue = config_story_dialogue.get_combat_dialogue(
                    "enemy_spawn", self.current_set, enemy_type
                )
                if dialogue:
                    self._show_combat_dialogue(
                        dialogue.get("speaker", "PILOT"),
                        dialogue.get("text", ""),
                        dialogue.get("duration", 2.5)
                    )
                break

    def _check_boss_phase_dialogue(self):
        """보스 페이즈 대사 체크"""
        boss = next((e for e in self.enemies if hasattr(e, 'is_boss') and e.is_boss and e.is_alive), None)
        if not boss:
            return

        hp_percent = (boss.hp / boss.max_hp) * 100
        phases = [(66, "phase_66"), (33, "phase_33"), (10, "phase_10")]

        for threshold, phase_key in phases:
            dialogue_key = f"{self.current_set}_{phase_key}"
            if hp_percent <= threshold and dialogue_key not in self.boss_phase_shown:
                self.boss_phase_shown.add(dialogue_key)
                dialogue = config_story_dialogue.get_boss_phase_dialogue(
                    self.current_set, phase_key
                )
                if dialogue:
                    self._show_combat_dialogue(
                        dialogue.get("speaker", "BOSS"),
                        dialogue.get("text", ""),
                        dialogue.get("duration", 3.0)
                    )
                break

    def _check_objective_progress_dialogue(self):
        """목표 진행률 대사 체크"""
        if not self.current_objective:
            return

        objective_type = self.current_objective.get("type", "")
        progress_percent = 0

        if objective_type == config_story.WaveObjective.DEFENSE:
            if self.defense_max_hp > 0:
                progress_percent = (1 - self.defense_hp / self.defense_max_hp) * 100
        elif objective_type == config_story.WaveObjective.SURVIVAL:
            if self.objective_target > 0:
                progress_percent = (self.survival_timer / self.objective_target) * 100
        elif objective_type == config_story.WaveObjective.DATA_COLLECT:
            if self.objective_target > 0:
                progress_percent = (self.collected_data / self.objective_target) * 100

        # 50% 진행 시 대사
        if progress_percent >= 50 and not hasattr(self, '_objective_50_shown'):
            self._objective_50_shown = True
            dialogue = config_story_dialogue.get_combat_dialogue(
                "objective_progress", self.current_set, 50
            )
            if dialogue:
                self._show_combat_dialogue(
                    dialogue.get("speaker", "SYSTEM"),
                    dialogue.get("text", ""),
                    dialogue.get("duration", 2.0)
                )

    def _render_combat_dialogue(self, screen: pygame.Surface):
        """실시간 전투 대사 렌더링"""
        if not self.combat_dialogue_active:
            return

        # 화면 상단에 대사 표시
        dialogue_height = 60
        dialogue_y = 80  # HUD 아래

        # 반투명 배경
        dialogue_bg = pygame.Surface((self.screen_size[0], dialogue_height), pygame.SRCALPHA)
        dialogue_bg.fill((0, 0, 0, 180))
        screen.blit(dialogue_bg, (0, dialogue_y))

        # 화자 색상
        speaker_colors = {
            "ARTEMIS": (255, 200, 100),  # 금색
            "PILOT": (100, 200, 255),    # 청색
            "SYSTEM": (200, 200, 200),   # 회색
            "BOSS": (255, 100, 100),     # 적색
        }
        speaker_color = speaker_colors.get(self.combat_dialogue_speaker, (255, 255, 255))

        # 화자 이름
        speaker_font = self.fonts.get("small", self.fonts.get("medium"))
        speaker_text = speaker_font.render(f"[{self.combat_dialogue_speaker}]", True, speaker_color)
        screen.blit(speaker_text, (20, dialogue_y + 8))

        # 대사 텍스트
        dialogue_font = self.fonts.get("medium", self.fonts.get("small"))
        dialogue_text = dialogue_font.render(self.combat_dialogue_text, True, (255, 255, 255))
        screen.blit(dialogue_text, (20, dialogue_y + 30))

        # 페이드 아웃 효과
        if self.combat_dialogue_timer > self.combat_dialogue_duration - 0.5:
            fade_alpha = int(255 * (self.combat_dialogue_duration - self.combat_dialogue_timer) / 0.5)
            fade_overlay = pygame.Surface((self.screen_size[0], dialogue_height), pygame.SRCALPHA)
            fade_overlay.fill((0, 0, 0, 255 - fade_alpha))
            screen.blit(fade_overlay, (0, dialogue_y))

    # =========================================================
    # 웨이브 목표 시스템
    # =========================================================
    def _init_wave_objective(self, wave_num: int):
        """웨이브 목표 초기화"""
        objective_data = config_story.get_wave_objective(wave_num)
        if not objective_data:
            self.current_objective = None
            return

        self.current_objective = objective_data
        objective_type = objective_data.get("type", config_story.WaveObjective.EXTERMINATION)
        self.objective_target = objective_data.get("target", 20)

        # 킬 카운트 초기화 (EXTERMINATION 목표용)
        self.game_data["kills_this_wave"] = 0
        self.last_kill_count = 0

        # 목표 타입별 초기화
        if objective_type == config_story.WaveObjective.SURVIVAL:
            self.survival_timer = 0.0
        elif objective_type == config_story.WaveObjective.DEFENSE:
            self.defense_hp = objective_data.get("defense_hp", 1000)
            self.defense_max_hp = self.defense_hp
            self.game_data["wave_elapsed_time"] = 0  # 방어 시간 초기화
        elif objective_type == config_story.WaveObjective.DATA_COLLECT:
            self.collected_data = 0
        elif objective_type == config_story.WaveObjective.ESCORT:
            self.escort_progress = 0.0
        elif objective_type == config_story.WaveObjective.RESCUE:
            self.rescued_count = 0
            self.rescue_targets = []
            # 구출 대상 NPC 스폰
            self._spawn_rescue_targets(self.objective_target)

        # 진행률 관련 플래그 리셋
        if hasattr(self, '_objective_50_shown'):
            del self._objective_50_shown

        print(f"INFO: Wave {wave_num} objective initialized: {objective_type} (target: {self.objective_target})")

    def _update_wave_objective(self, dt: float):
        """웨이브 목표 업데이트"""
        if not self.current_objective:
            return

        objective_type = self.current_objective.get("type", "")

        if objective_type == config_story.WaveObjective.SURVIVAL:
            self.survival_timer += dt
            self.objective_progress = self.survival_timer

        elif objective_type == config_story.WaveObjective.DEFENSE:
            # 방어 시간 추적
            self.game_data["wave_elapsed_time"] = self.game_data.get("wave_elapsed_time", 0) + dt

            # 방어 대상이 적에게 공격당하는 로직 (간략화)
            for enemy in self.enemies:
                if enemy.is_alive and self._is_near_defense_target(enemy):
                    self.defense_hp -= enemy.damage * dt
            self.objective_progress = self.defense_hp

        elif objective_type == config_story.WaveObjective.ESCORT:
            # 호위 대상이 이동하는 로직
            # 적 수에 따라 진행 속도 조절 (적이 많으면 느림, 적으면 빠름)
            alive_enemies = len([e for e in self.enemies if e.is_alive])
            if alive_enemies == 0:
                progress_rate = 15.0  # 적 없음: 초당 15% (빠름)
            elif alive_enemies <= 3:
                progress_rate = 8.0   # 적 1-3: 초당 8%
            elif alive_enemies <= 6:
                progress_rate = 4.0   # 적 4-6: 초당 4%
            else:
                progress_rate = 2.0   # 적 7+: 초당 2% (느림)

            self.escort_progress += dt * progress_rate
            self.objective_progress = self.escort_progress

        elif objective_type == config_story.WaveObjective.RESCUE:
            # 구출 대상 업데이트 (플레이어 접촉 체크)
            self._update_rescue_targets(dt)
            self.objective_progress = self.rescued_count

    def _is_near_defense_target(self, enemy) -> bool:
        """적이 방어 대상 근처에 있는지 체크"""
        # 간략화된 구현 - 화면 하단 중앙을 방어 대상으로 가정
        defense_pos = (self.screen_size[0] // 2, self.screen_size[1] - 100)
        dist = ((enemy.pos.x - defense_pos[0]) ** 2 + (enemy.pos.y - defense_pos[1]) ** 2) ** 0.5
        return dist < 150

    def _is_escort_under_attack(self) -> bool:
        """호위 대상이 공격받고 있는지 체크"""
        # 간략화된 구현
        for enemy in self.enemies:
            if enemy.is_alive:
                return True
        return False

    def _spawn_rescue_targets(self, count: int):
        """구출 대상 NPC 스폰"""
        import random

        SCREEN_WIDTH, SCREEN_HEIGHT = self.screen_size

        for i in range(count):
            # 화면 상단 랜덤 위치에 스폰
            x = random.randint(100, SCREEN_WIDTH - 100)
            y = random.randint(100, SCREEN_HEIGHT // 3)

            # 간단한 구출 대상 딕셔너리로 관리
            rescue_target = {
                "x": x,
                "y": y,
                "radius": 30,  # 접촉 반경
                "rescued": False,
                "pulse_timer": random.uniform(0, 3.14),  # 깜빡임 효과용
            }
            self.rescue_targets.append(rescue_target)

        print(f"INFO: Spawned {count} rescue targets")

    def _update_rescue_targets(self, dt: float):
        """구출 대상 업데이트 및 구출 체크"""
        if not self.player:
            return

        player_x, player_y = self.player.pos.x, self.player.pos.y

        for target in self.rescue_targets:
            if target["rescued"]:
                continue

            # 깜빡임 타이머 업데이트
            target["pulse_timer"] += dt * 3

            # 플레이어와 거리 체크
            dx = player_x - target["x"]
            dy = player_y - target["y"]
            dist = (dx * dx + dy * dy) ** 0.5

            # 접촉 시 구출
            if dist < target["radius"] + 30:  # 플레이어 반경 고려
                target["rescued"] = True
                self.rescued_count += 1

                # 구출 이펙트
                from objects import Particle
                import random as rnd
                for _ in range(20):
                    particle = Particle(
                        pos=(target["x"], target["y"]),
                        velocity=pygame.math.Vector2(rnd.uniform(-100, 100), rnd.uniform(-150, -50)),
                        color=(100, 255, 150),
                        lifetime=0.8,
                        size=4
                    )
                    self.effects.append(particle)

                # 사운드
                if self.sound_manager:
                    self.sound_manager.play_sfx("heal_pickup")

                print(f"INFO: Rescued {self.rescued_count}/{self.objective_target}")

    def _render_rescue_targets(self, screen: pygame.Surface):
        """구출 대상 렌더링"""
        import math

        for target in self.rescue_targets:
            if target["rescued"]:
                continue

            x, y = int(target["x"]), int(target["y"])
            pulse = 0.7 + 0.3 * math.sin(target["pulse_timer"])
            radius = int(target["radius"] * pulse)

            # 외곽 글로우
            glow_surf = pygame.Surface((radius * 4, radius * 4), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (100, 255, 150, 50), (radius * 2, radius * 2), radius * 2)
            screen.blit(glow_surf, (x - radius * 2, y - radius * 2))

            # 메인 원
            pygame.draw.circle(screen, (100, 255, 150), (x, y), radius, 3)

            # 중앙 아이콘 (사람 모양 간략화)
            pygame.draw.circle(screen, (200, 255, 200), (x, y - 5), 8)  # 머리
            pygame.draw.line(screen, (200, 255, 200), (x, y + 3), (x, y + 15), 3)  # 몸
            pygame.draw.line(screen, (200, 255, 200), (x - 8, y + 8), (x + 8, y + 8), 2)  # 팔

            # "RESCUE" 텍스트
            font = pygame.font.Font(None, 18)
            text = font.render("RESCUE", True, (100, 255, 150))
            text_rect = text.get_rect(center=(x, y - radius - 15))
            screen.blit(text, text_rect)

    def _check_wave_objective_complete(self) -> bool:
        """웨이브 목표 달성 체크"""
        if not self.current_objective:
            # 기본 킬 목표 사용
            return check_wave_clear(self.game_data)

        objective_type = self.current_objective.get("type", "")

        if objective_type == config_story.WaveObjective.EXTERMINATION:
            return self.game_data.get("kills_this_wave", 0) >= self.objective_target

        elif objective_type == config_story.WaveObjective.SURVIVAL:
            return self.survival_timer >= self.objective_target

        elif objective_type == config_story.WaveObjective.DEFENSE:
            # 방어 성공 = 시간 경과 (target 초) 동안 defense_hp > 0 유지
            defense_time = self.objective_target  # target 값을 방어 시간으로 사용
            time_passed = self.game_data.get("wave_elapsed_time", 0) >= defense_time
            return time_passed and self.defense_hp > 0

        elif objective_type == config_story.WaveObjective.DATA_COLLECT:
            return self.collected_data >= self.objective_target

        elif objective_type == config_story.WaveObjective.ESCORT:
            return self.escort_progress >= 100

        elif objective_type == config_story.WaveObjective.RESCUE:
            return self.rescued_count >= self.objective_target

        elif objective_type == config_story.WaveObjective.BOSS_HUNT:
            # 보스 처치
            boss = next((e for e in self.enemies if hasattr(e, 'is_boss') and e.is_boss), None)
            return boss is None or not boss.is_alive

        return check_wave_clear(self.game_data)

    def _render_wave_objective(self, screen: pygame.Surface):
        """웨이브 목표 UI 렌더링"""
        if not self.current_objective:
            return

        objective_type = self.current_objective.get("type", "")
        description = self.current_objective.get("description", "")

        # 목표 UI 위치 (HUD 아래)
        ui_x = self.screen_size[0] - 300
        ui_y = 10

        # 배경
        ui_width = 280
        ui_height = 50
        ui_bg = pygame.Surface((ui_width, ui_height), pygame.SRCALPHA)
        ui_bg.fill((0, 0, 0, 150))
        screen.blit(ui_bg, (ui_x, ui_y))

        # 목표 설명
        font = self.fonts.get("small", self.fonts.get("medium"))
        desc_text = font.render(description, True, (255, 255, 200))
        screen.blit(desc_text, (ui_x + 10, ui_y + 5))

        # 진행률 표시
        progress_text = ""
        progress_color = (100, 255, 100)

        if objective_type == config_story.WaveObjective.SURVIVAL:
            remaining = max(0, self.objective_target - self.survival_timer)
            progress_text = f"남은 시간: {int(remaining)}초"
        elif objective_type == config_story.WaveObjective.DEFENSE:
            hp_percent = (self.defense_hp / self.defense_max_hp) * 100 if self.defense_max_hp > 0 else 0
            defense_time = self.objective_target  # target 값을 방어 시간으로 사용
            elapsed = self.game_data.get("wave_elapsed_time", 0)
            remaining = max(0, defense_time - elapsed)
            progress_text = f"방어 대상: {int(hp_percent)}% | 남은 시간: {int(remaining)}초"
            if hp_percent < 30:
                progress_color = (255, 100, 100)
        elif objective_type == config_story.WaveObjective.DATA_COLLECT:
            progress_text = f"수집: {self.collected_data}/{self.objective_target}"
        elif objective_type == config_story.WaveObjective.ESCORT:
            progress_text = f"호위 진행: {int(self.escort_progress)}%"
        elif objective_type == config_story.WaveObjective.RESCUE:
            progress_text = f"구출: {self.rescued_count}/{self.objective_target}"
        elif objective_type == config_story.WaveObjective.EXTERMINATION:
            kills = self.game_data.get("kills_this_wave", 0)
            progress_text = f"처치: {kills}/{self.objective_target}"

        if progress_text:
            prog_render = font.render(progress_text, True, progress_color)
            screen.blit(prog_render, (ui_x + 10, ui_y + 28))

    # =========================================================
    # 환경 메커니즘 시스템
    # =========================================================
    def _init_act_mechanics(self):
        """Act별 환경 메커니즘 초기화"""
        mechanics = config_story.get_act_mechanics(self.current_set)
        if not mechanics:
            return

        mechanic_type = mechanics.get("type", "")
        print(f"INFO: Act {self.current_set} mechanics initialized: {mechanic_type}")

        # Act별 초기화
        if self.current_set == 3:  # 불타는 연구소
            self.safe_zone_radius = self.screen_size[0] // 2  # 초기 안전 구역
        elif self.current_set == 4:  # 통신 기지
            self.emp_active = False
            self.emp_timer = 0.0

    def _update_act_mechanics(self, dt: float):
        """환경 메커니즘 업데이트"""
        mechanics = config_story.get_act_mechanics(self.current_set)
        if not mechanics:
            return

        self.environment_timer += dt
        mechanic_type = mechanics.get("type", "")

        if mechanic_type == "collapsing_ruins":
            # Act 1: 10초마다 잔해 낙하
            interval = mechanics.get("debris_interval", 10)
            if self.environment_timer >= interval:
                self.environment_timer = 0
                self._spawn_falling_debris()

        elif mechanic_type == "fire_spread":
            # Act 3: 안전 구역 축소
            shrink_rate = mechanics.get("shrink_rate", 5)
            min_radius = mechanics.get("min_radius", 100)
            self.safe_zone_radius = max(min_radius, self.safe_zone_radius - shrink_rate * dt)

        elif mechanic_type == "emp_pulse":
            # Act 4: 30초마다 EMP 파동
            interval = mechanics.get("emp_interval", 30)
            if self.environment_timer >= interval:
                self.environment_timer = 0
                self._trigger_emp_pulse()

        elif mechanic_type == "dimensional_rift":
            # Act 5: 15초마다 차원 균열
            interval = mechanics.get("rift_interval", 15)
            if self.environment_timer >= interval:
                self.environment_timer = 0
                self._spawn_dimensional_rift()

        # EMP 효과 업데이트
        if self.emp_active:
            self.emp_timer -= dt
            if self.emp_timer <= 0:
                self.emp_active = False

    def _spawn_falling_debris(self):
        """낙하 잔해 생성"""
        import random
        from objects import Particle

        # 경고 표시 위치
        warning_x = random.randint(100, self.screen_size[0] - 100)
        self.environment_warning_active = True

        # 경고 후 잔해 낙하 (간략화된 구현)
        print(f"INFO: Falling debris at x={warning_x}")

    def _trigger_emp_pulse(self):
        """EMP 파동 발동"""
        self.emp_active = True
        self.emp_timer = 3.0  # 3초간 스킬 비활성화
        print("INFO: EMP pulse activated!")

    def _spawn_dimensional_rift(self):
        """차원 균열 생성"""
        import random
        rift_x = random.randint(100, self.screen_size[0] - 100)
        rift_y = random.randint(100, self.screen_size[1] - 200)
        print(f"INFO: Dimensional rift at ({rift_x}, {rift_y})")

    def _render_act_mechanics(self, screen: pygame.Surface):
        """환경 메커니즘 렌더링"""
        mechanics = config_story.get_act_mechanics(self.current_set)
        if not mechanics:
            return

        mechanic_type = mechanics.get("type", "")

        if mechanic_type == "fire_spread" and self.safe_zone_radius > 0:
            # 화염 경계 표시 (안전 구역 외곽)
            center = (self.screen_size[0] // 2, self.screen_size[1] // 2)
            pygame.draw.circle(screen, (255, 100, 50), center, int(self.safe_zone_radius), 3)

        if self.emp_active:
            # EMP 효과 오버레이
            emp_overlay = pygame.Surface(self.screen_size, pygame.SRCALPHA)
            emp_alpha = int(100 * (self.emp_timer / 3.0))
            emp_overlay.fill((100, 150, 255, emp_alpha))
            screen.blit(emp_overlay, (0, 0))

            # EMP 경고 텍스트
            font = self.fonts.get("medium")
            emp_text = font.render("EMP ACTIVE - Skills Disabled!", True, (255, 255, 100))
            text_rect = emp_text.get_rect(center=(self.screen_size[0] // 2, 150))
            screen.blit(emp_text, text_rect)

    def _reset_combat_dialogue_state(self):
        """전투 대사 상태 리셋 (웨이브 시작 시)"""
        self.last_kill_milestone = 0
        self.last_hp_threshold = 100
        self.shown_enemy_dialogues.clear()
        self.boss_phase_shown.clear()
        self.combat_dialogue_active = False

    def _check_memory_trigger(self, wave_num: int):
        """회상 컷씬 트리거 체크"""
        set_info = config_story.SET_INFO.get(self.current_set, {})

        if set_info.get("has_memory_cutscene", False):
            trigger_wave = set_info.get("memory_trigger_wave", 2)
            print(f"DEBUG: Memory trigger check - wave_num={wave_num}, trigger_wave={trigger_wave}, "
                  f"current_set={self.current_set}, memory_shown={self.memory_cutscene_shown}")
            if wave_num == trigger_wave and not self.memory_cutscene_shown:
                print("DEBUG: Memory cutscene WILL trigger!")
                return True
        return False

    def update(self, dt: float, current_time: float):
        """스토리 모드 업데이트"""
        # 컷씬 활성화 중이면 컷씬만 업데이트
        if self.active_cutscene:
            self.active_cutscene.update(dt)
            return

        scaled_dt = self.update_common(dt, current_time)
        self._update_background(dt)

        if self.game_data["game_state"] == config.GAME_STATE_RUNNING:
            self._update_running(scaled_dt, current_time)
            # 전투 중 커스텀 커서 활성화
            if not self.custom_cursor_enabled:
                self.enable_custom_cursor(True)
            self.update_custom_cursor(dt)
        else:
            # 전투 외 상태에서 커스텀 커서 비활성화
            if self.custom_cursor_enabled:
                self.enable_custom_cursor(False)

        if self.game_data["game_state"] not in [config.GAME_STATE_OVER, config.GAME_STATE_VICTORY]:
            if self.player and self.player.hp <= 0:
                self._check_game_over()

    def _update_background(self, dt: float):
        """배경 업데이트"""
        for layer in self.parallax_layers:
            layer.update(dt)

        # 유성 효과
        if config.METEOR_SETTINGS.get("enabled", True):
            current_wave = self.game_data.get('current_wave', 1)
            if 'last_meteor_wave' not in self.game_data:
                self.game_data['last_meteor_wave'] = 0
            if current_wave != self.game_data['last_meteor_wave'] and not self.meteor_spawned_this_wave:
                if len(self.meteors) == 0:
                    self.meteors.append(Meteor(self.screen_size))
                    self.meteor_spawned_this_wave = True
                    self.game_data['last_meteor_wave'] = current_wave

        for meteor in self.meteors[:]:
            meteor.update(dt)
            if not meteor.is_alive:
                self.meteors.remove(meteor)
                self.meteor_spawned_this_wave = False

        # 동적 배경 업데이트
        if self.dynamic_background:
            current_wave = self.game_data.get('current_wave', 1)
            self.dynamic_background.update(dt)
            self.dynamic_background._current_wave = current_wave

    def _check_kill_effects(self):
        """킬 이펙트 체크"""
        # 킬 카운트 변화 감지
        current_kills = self.game_data.get('kills_this_wave', 0)
        if current_kills == 0:
            current_kills = self.game_data.get('kill_count', 0)

        if current_kills > self.last_kill_count:
            kill_diff = current_kills - self.last_kill_count
            alive_enemies = len([e for e in self.enemies if e.is_alive])
            is_last_enemy = (alive_enemies == 0)

            # 동적 배경 킬 이펙트
            if self.dynamic_background and config.KILL_PULSE_ENABLED:
                self.dynamic_background.trigger_kill_effect(kill_diff, is_last_enemy)

            self.last_kill_count = current_kills

    def _update_running(self, dt: float, current_time: float):
        """게임 실행 중 업데이트"""
        self.update_player(dt, current_time)
        self.update_targeting(dt)  # 타겟팅 시스템 업데이트
        self.update_objects(dt)

        # HP 변화 감지를 위해 이전 HP 저장
        hp_before = self.player.hp if self.player else 0

        update_game_objects(
            self.player, self.enemies, self.bullets, self.gems,
            self.effects, self.screen_size, dt, current_time,
            self.game_data,
            damage_numbers=None,  # deprecated
            damage_number_manager=self.damage_number_manager,
            screen_shake=self.screen_shake,
            sound_manager=self.sound_manager,
            death_effect_manager=self.death_effect_manager
        )

        # 킬 이펙트 체크 및 DATA_COLLECT 목표 처리
        self._check_kill_effects()

        # HP 감소 감지 → 피격 효과 트리거
        if self.player and hp_before > self.player.hp:
            damage_taken = hp_before - self.player.hp
            damage_ratio = damage_taken / self.player.max_hp
            self.damage_flash.trigger(damage_ratio)
            self.hp_bar_shake.trigger(damage_ratio)

        # 시각적 피드백 효과 업데이트
        self.damage_flash.update()
        self.hp_bar_shake.update()
        self.level_up_effect.update(dt)

        # 전투 모션 효과 (플레이어 이동 추적)
        if self.player:
            is_moving = False
            move_direction = None
            if self.player_prev_pos is not None:
                dx = self.player.pos.x - self.player_prev_pos[0]
                dy = self.player.pos.y - self.player_prev_pos[1]
                is_moving = (abs(dx) > 2 or abs(dy) > 2)  # 일정 이상 움직임 감지
                if is_moving:
                    move_direction = (dx, dy)  # 방향 전환 감지용
            self.player_prev_pos = (self.player.pos.x, self.player.pos.y)
            # 플레이어 위치 전달 (줌/워프 효과 중심점)
            player_pos = (self.player.pos.x, self.player.pos.y)
            self.combat_motion_effect.update_player_movement(is_moving, dt, player_pos, move_direction)

            # 플레이어 피격 시 CombatMotionEffect 이동 시간 리셋
            if hasattr(self.player, 'was_hit_recently') and self.player.was_hit_recently:
                self.combat_motion_effect.reset_move_time()
                self.player.was_hit_recently = False

        self.combat_motion_effect.update(dt)

        # 2막 벙커 포신 업데이트
        if self.bunker_cannon.is_active:
            player_pos = (self.player.pos.x, self.player.pos.y) if self.player else None
            self.bunker_cannon.update(dt, player_pos, self.enemies)

        wave_phase = self.game_data.get('wave_phase', 'normal')

        if wave_phase == 'normal':
            # EXP 바 체크 - 가득 차면 자동으로 레벨업 메뉴 열기 (normal 페이즈에서만)
            level_threshold = get_next_level_threshold(self.game_data["player_level"])
            if self.game_data.get("uncollected_score", 0) >= level_threshold:
                self.game_data["game_state"] = config.GAME_STATE_LEVEL_UP
                self.game_data["tactical_options"] = generate_tactical_options(self.player, self.game_data)
                self.sound_manager.play_sfx("level_up")
                return  # 레벨업 메뉴로 전환, 나머지 업데이트 스킵

            handle_spawning(self.enemies, self.screen_size, current_time,
                           self.game_data, self.effects, self.sound_manager)
            spawn_gem(self.gems, self.screen_size, current_time, self.game_data)
            update_random_event(self.game_data, current_time, dt,
                               self.player, self.gems, self.enemies, self.screen_size)

            # =========================================================
            # 실시간 전투 대사 시스템 업데이트
            # =========================================================
            self._update_combat_dialogue(dt)
            self._check_combat_dialogue_triggers(dt)

            # =========================================================
            # 웨이브 목표 시스템 업데이트
            # =========================================================
            self._update_wave_objective(dt)

            # =========================================================
            # 환경 메커니즘 업데이트
            # =========================================================
            self._update_act_mechanics(dt)

            # 웨이브 클리어 체크 (목표 시스템 사용)
            if self._check_wave_objective_complete():
                self._trigger_wave_transition()

        elif wave_phase == 'cleanup':
            alive_enemies = [e for e in self.enemies if e.is_alive]
            if len(alive_enemies) == 0 and not self.game_data.get('victory_animation_active', False):
                self._start_victory_animation()

        elif wave_phase == 'victory_animation':
            if not self.game_data.get('victory_animation_active', False):
                # 스토리 모드 총 웨이브 수 (25웨이브) 기준으로 승리 판정
                if self.game_data['current_wave'] >= config_story.TOTAL_WAVES:
                    self.game_data["game_state"] = config.GAME_STATE_VICTORY
                else:
                    self.game_data["game_state"] = config.GAME_STATE_WAVE_CLEAR
                self.game_data["wave_phase"] = 'normal'
                self.sound_manager.play_sfx("wave_clear")

        self.skill_system.update_passive_skills(
            self.player, self.enemies, self.effects, dt, current_time
        )

    def _trigger_wave_transition(self):
        """웨이브 전환 처리"""
        # 전투 모션 효과 즉시 종료
        self.combat_motion_effect.is_active = False

        self.game_data['wave_phase'] = 'cleanup'

        from objects import WaveTransitionEffect
        try:
            transition_effect = WaveTransitionEffect(
                screen_size=self.screen_size,
                image_path=config.WAVE_HERO_IMAGE_PATH,
                darken_duration=1.0,
                image_duration=1.5,
                brighten_duration=0.5
            )
            self.effects.append(transition_effect)
        except Exception as e:
            print(f"WARNING: WaveTransitionEffect failed: {e}")

        for enemy in self.enemies:
            if enemy.is_alive:
                enemy.is_retreating = True
                enemy.is_circling = False

        self.gems.clear()
        self.sound_manager.play_sfx("level_up")

        # 레벨업 효과 트리거 (웨이브 클리어)
        self.level_up_effect.trigger(self.game_data["current_wave"])

    def _start_victory_animation(self):
        """승리 애니메이션 시작"""
        from objects import PlayerVictoryAnimation

        self.game_data['victory_animation_active'] = True
        self.game_data['wave_phase'] = 'victory_animation'

        def on_animation_complete():
            self.game_data['victory_animation_active'] = False

        victory_anim = PlayerVictoryAnimation(
            player=self.player,
            screen_size=self.screen_size,
            orbit_duration=2.5,
            move_duration=1.5
        )
        victory_anim.on_complete = on_animation_complete
        self.effects.append(victory_anim)

    def _check_game_over(self):
        """게임 오버 체크"""
        if not self.player or self.player.hp > 0:
            return
        if self.game_data["game_state"] == config.GAME_STATE_OVER:
            return

        if getattr(self.player, 'has_phoenix', False) and getattr(self.player, 'phoenix_cooldown', 999) <= 0:
            self.player.hp = self.player.max_hp
            self.player.is_dead = False
            self.player.phoenix_cooldown = config.PHOENIX_REBIRTH_COOLDOWN_SECONDS
            self._add_revive_effects("Phoenix Rebirth!", (255, 150, 0))
            return

        if self.player.upgrades.get("REINCARNATION", 0) > 0:
            self.player.hp = self.player.max_hp
            self.player.is_dead = False
            self.player.upgrades["REINCARNATION"] -= 1
            self.engine.save_shared_state()
            self._add_revive_effects("Reincarnation!", (255, 80, 80))
            return

        self.game_data["game_state"] = config.GAME_STATE_OVER
        self.engine.save_shared_state()

    def _add_revive_effects(self, text: str, color: Tuple[int, int, int]):
        """부활 효과 추가"""
        from objects import ScreenFlash, ReviveTextEffect
        self.effects.append(ScreenFlash(self.screen_size, color=color, duration=0.4))
        self.effects.append(ReviveTextEffect(text, self.screen_size, color=color, duration=2.0))
        self.sound_manager.play_sfx("level_up")

    # =========================================================
    # 오토파일럿 자동 스킬 발동 (base_mode 오버라이드)
    # =========================================================
    def _trigger_auto_ultimate(self):
        """오토파일럿 궁극기 자동 발동"""
        if self.player and self.player.activate_ultimate(self.enemies):
            print("INFO: [AUTO] Ultimate activated!")

    def _trigger_auto_ability(self):
        """오토파일럿 특수 능력 자동 발동"""
        if not self.player:
            return

        ability_type = getattr(self.player, 'ship_ability_type', None)
        if self.player.use_ship_ability(self.enemies, self.effects):
            print(f"INFO: [AUTO] Ship ability '{ability_type}' activated!")

    def render(self, screen: pygame.Surface):
        """스토리 모드 렌더링"""
        # 컷씬 활성화 중이면 컷씬만 렌더링
        if self.active_cutscene:
            # 새 Effect 클래스들은 render 메서드 사용
            if hasattr(self.active_cutscene, 'render'):
                self.active_cutscene.render(screen)
            else:
                self.active_cutscene.draw(screen)
            return

        # 스토리 모드 배경 (지구)
        if self.story_background:
            screen.blit(self.story_background, (0, 0))
        else:
            screen.fill((20, 20, 30))

        for layer in self.parallax_layers:
            layer.draw(screen)

        # 2막 벙커 포신 배경 레이어 (연기, 포신 본체)
        if self.bunker_cannon.is_active:
            self.bunker_cannon.draw_background_layer(screen)

        for meteor in self.meteors:
            meteor.draw(screen)

        # ===== UI 요소들 (플레이어/적보다 먼저 렌더링) =====
        # HUD (상단 UI)
        draw_hud(screen, self.screen_size, self.fonts["small"], self.player, self.game_data)

        # 보스 체력바
        boss = next((e for e in self.enemies if hasattr(e, 'is_boss') and e.is_boss and e.is_alive), None)
        if boss:
            draw_boss_health_bar(screen, self.screen_size, self.fonts["medium"], boss)

        # 스킬 인디케이터 (쿨다운 UI)
        if self.game_data["game_state"] == config.GAME_STATE_RUNNING:
            draw_skill_indicators(screen, self.screen_size, self.player, pygame.time.get_ticks() / 1000.0)

        # 랜덤 이벤트 UI 및 오토파일럿
        if self.game_data["game_state"] == config.GAME_STATE_RUNNING:
            draw_random_event_ui(screen, self.screen_size, self.game_data)

        # ===== 게임 객체 렌더링 (UI 위에 표시) =====
        self.render_common(screen)

        # 타겟 마커 렌더링 (적 위에 표시)
        self.render_target_marker(screen)

        # RESCUE 목표: 구출 대상 렌더링
        if self.rescue_targets and self.game_data["game_state"] == config.GAME_STATE_RUNNING:
            self._render_rescue_targets(screen)

        # 2막 벙커 포신 전경 레이어 (포탄)
        if self.bunker_cannon.is_active:
            self.bunker_cannon.draw_foreground_layer(screen)

        # =========================================================
        # 실시간 전투 대사 렌더링
        # =========================================================
        if self.game_data["game_state"] == config.GAME_STATE_RUNNING:
            self._render_combat_dialogue(screen)

        # =========================================================
        # 웨이브 목표 UI 렌더링
        # =========================================================
        if self.game_data["game_state"] == config.GAME_STATE_RUNNING:
            self._render_wave_objective(screen)

        # =========================================================
        # 환경 메커니즘 렌더링
        # =========================================================
        if self.game_data["game_state"] == config.GAME_STATE_RUNNING:
            self._render_act_mechanics(screen)

        self._render_overlay(screen)

        # 시각적 피드백 효과 렌더링 (최상위 레이어)
        self.damage_flash.render(screen)
        self.level_up_effect.render(screen)

        # 전투 모션 효과 (고속 비행 연출) - RUNNING 상태에서만
        if self.game_data["game_state"] == config.GAME_STATE_RUNNING:
            self.combat_motion_effect.draw(screen)

        # 커스텀 커서 렌더링 (최상위)
        self.render_custom_cursor(screen)

    def _render_overlay(self, screen: pygame.Surface):
        """상태별 오버레이 렌더링"""
        state = self.game_data["game_state"]

        if state == config.GAME_STATE_SETTINGS:
            self.settings_bars = draw_settings_menu(
                screen, self.screen_size,
                self.fonts["huge"], self.fonts["large"],
                self.fonts["medium"], self.sound_manager
            )
        elif state == config.GAME_STATE_PAUSED:
            self.menu_button_rects = draw_pause_and_over_screens(
                screen, self.screen_size,
                self.fonts["huge"], self.fonts["medium"], self.game_data
            )
        elif state == config.GAME_STATE_OVER:
            self.menu_button_rects = draw_pause_and_over_screens(
                screen, self.screen_size,
                self.fonts["huge"], self.fonts["medium"], self.game_data
            )
        elif state == config.GAME_STATE_SHOP:
            draw_shop_screen(screen, self.screen_size, self.fonts["large"],
                           self.fonts["medium"], self.game_data['score'], self.player.upgrades)
        elif state == config.GAME_STATE_LEVEL_UP:
            draw_tactical_menu(screen, self.screen_size,
                             self.fonts["huge"], self.fonts["medium"], self.game_data)
        elif state == config.GAME_STATE_WAVE_PREPARE:
            draw_wave_prepare_screen(screen, self.screen_size,
                                    self.fonts["huge"], self.fonts["medium"], self.game_data)
        elif state == config.GAME_STATE_WAVE_CLEAR:
            draw_wave_clear_screen(screen, self.screen_size,
                                  self.fonts["huge"], self.fonts["medium"], self.game_data)
        elif state == config.GAME_STATE_VICTORY:
            fonts_dict = {"huge": self.fonts["huge"], "title": self.fonts["large"],
                         "medium": self.fonts["medium"], "small": self.fonts["small"]}
            draw_victory_screen(screen, self.game_data, self.player, fonts_dict)
        elif state == config.GAME_STATE_QUIT_CONFIRM:
            self.ui_system.draw_quit_confirm_overlay(screen, self.screen_size, self.fonts)

    def handle_event(self, event: pygame.event.Event):
        """이벤트 처리"""
        # 컷씬 활성화 중이면 컷씬 이벤트만 처리
        if self.active_cutscene:
            self._handle_cutscene_event(event)
            return

        if self.game_data["game_state"] == config.GAME_STATE_SETTINGS:
            self._handle_settings_event(event)
            return

        if self.handle_common_events(event):
            return

        state = self.game_data["game_state"]

        if state == config.GAME_STATE_RUNNING:
            self._handle_running_event(event)
        elif state == config.GAME_STATE_PAUSED:
            self._handle_paused_event(event)
        elif state == config.GAME_STATE_WAVE_PREPARE:
            self._handle_wave_prepare_event(event)
        elif state == config.GAME_STATE_WAVE_CLEAR:
            self._handle_wave_clear_event(event)
        elif state == config.GAME_STATE_LEVEL_UP:
            self._handle_level_up_event(event)
        elif state == config.GAME_STATE_SHOP:
            self._handle_shop_event(event)
        elif state == config.GAME_STATE_OVER:
            self._handle_game_over_event(event)
        elif state == config.GAME_STATE_VICTORY:
            self._handle_victory_event(event)
        elif state == config.GAME_STATE_QUIT_CONFIRM:
            self._handle_quit_confirm_event(event)

    def _handle_cutscene_event(self, event: pygame.event.Event):
        """컷씬 이벤트 처리"""
        # 새 Effect 클래스들은 handle_event 메서드 사용
        if hasattr(self.active_cutscene, 'handle_event'):
            self.active_cutscene.handle_event(event)
            return

        # 기존 컷씬 클래스들 (handle_click 사용)
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                # ESC로 컷씬 스킵
                if hasattr(self.active_cutscene, 'skip'):
                    self.active_cutscene.skip()
            elif event.key == pygame.K_SPACE or event.key == pygame.K_RETURN:
                # 스페이스/엔터로 다음 대사
                if hasattr(self.active_cutscene, 'handle_click'):
                    self.active_cutscene.handle_click()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # 클릭으로 다음 대사
            if hasattr(self.active_cutscene, 'handle_click'):
                self.active_cutscene.handle_click()

    def _handle_settings_event(self, event: pygame.event.Event):
        """설정 메뉴 이벤트"""
        if event.type == pygame.KEYDOWN and event.key == pygame.K_F1:
            self.game_data["game_state"] = self.game_data.get("previous_game_state", config.GAME_STATE_RUNNING)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_x, mouse_y = event.pos
            if "bgm_bar" in self.settings_bars and self.settings_bars["bgm_bar"].collidepoint(mouse_x, mouse_y):
                self.dragging_bgm = True
            elif "sfx_bar" in self.settings_bars and self.settings_bars["sfx_bar"].collidepoint(mouse_x, mouse_y):
                self.dragging_sfx = True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging_bgm = False
            self.dragging_sfx = False

    def _handle_running_event(self, event: pygame.event.Event):
        """게임 실행 중 이벤트"""
        # 마우스 클릭 처리 (좌클릭 이동, 우클릭 공격)
        if self.handle_mouse_click(event):
            return

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_q:
                self.player.activate_ultimate(self.enemies)
            elif event.key == pygame.K_l:
                self.game_data["previous_game_state"] = self.game_data["game_state"]
                self.game_data["game_state"] = config.GAME_STATE_LEVEL_UP
                self.game_data["skill_view_readonly"] = True
                self.game_data["tactical_options"] = generate_tactical_options(self.player, self.game_data)

    def _handle_wave_prepare_event(self, event: pygame.event.Event):
        """웨이브 준비 이벤트"""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            current_wave = self.game_data["current_wave"]
            wave_in_set = ((current_wave - 1) % config_story.WAVES_PER_SET) + 1

            # 현재 세트 번호 업데이트
            self.current_set = config_story.get_set_number(current_wave)

            # 세트 첫 웨이브일 때 브리핑 표시
            if wave_in_set == 1 and not self.set_briefing_shown:
                self._show_set_briefing()
                return

            # =========================================================
            # 보스 웨이브 시작 시 보스 등장 대사 표시 (세트 5번째 웨이브)
            # =========================================================
            if wave_in_set == config_story.WAVES_PER_SET and not self.boss_intro_shown:
                self._show_boss_intro_dialogue()
                return

            start_wave(self.game_data, pygame.time.get_ticks() / 1000.0, self.enemies)
            self.game_data["game_state"] = config.GAME_STATE_RUNNING

            new_wave = self.game_data["current_wave"]
            self.sound_manager.play_wave_bgm(new_wave)

            # 스토리 배경 업데이트
            self._load_story_background(new_wave)
            self.last_kill_count = 0

            # 전투 모션 효과 리셋 (웨이브당 2회)
            self.combat_motion_effect.reset_wave()

            # =========================================================
            # 새 시스템 초기화 (웨이브 시작 시)
            # =========================================================
            self._init_wave_objective(new_wave)
            self._init_act_mechanics()
            self._reset_combat_dialogue_state()
            self.environment_timer = 0.0

            print(f"INFO: Story Wave {new_wave} started")

    def _handle_wave_clear_event(self, event: pygame.event.Event):
        """웨이브 클리어 이벤트"""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.player and self.player.hp <= 0:
                self._check_game_over()
                return

            current_wave = self.game_data["current_wave"]
            wave_in_set = ((current_wave - 1) % config_story.WAVES_PER_SET) + 1

            # 현재 세트 번호 업데이트 (중요: 컷씬 트리거 체크 전에 수행)
            self.current_set = config_story.get_set_number(current_wave)

            # =========================================================
            # 1. 웨이브 중간 대사 체크 (특정 웨이브 클리어 후)
            # =========================================================
            if self._check_mid_dialogue_trigger(current_wave):
                self._show_wave_mid_dialogue(current_wave)
                return

            # =========================================================
            # 2. 회상 컷씬 트리거 체크 (1막 웨이브 2 클리어 후)
            # =========================================================
            if self._check_memory_trigger(wave_in_set):
                self._show_memory_cutscene()
                return

            # =========================================================
            # 3. Act 2~5 컷씬 트리거 체크 (전체 웨이브 번호로 체크)
            # =========================================================
            if self._check_act_cutscene_trigger(current_wave):
                self._show_act_cutscene()
                return

            # =========================================================
            # 4. 보스 처치 대사 체크 (세트 마지막 웨이브 = 보스 웨이브)
            # =========================================================
            if wave_in_set == config_story.WAVES_PER_SET and not self.boss_defeat_shown:
                self._show_boss_defeat_dialogue()
                return

            # =========================================================
            # 5. 세트 엔딩 대사 체크 (보스 처치 후)
            # =========================================================
            if wave_in_set == config_story.WAVES_PER_SET and self.boss_defeat_shown and not self.set_ending_shown:
                self._show_set_ending_dialogue()
                return

            # 세트 마지막 웨이브 완료 시 다음 세트 브리핑 플래그 초기화
            if wave_in_set == config_story.WAVES_PER_SET:
                self.set_briefing_shown = False
                self.memory_cutscene_shown = False
                self.act_cutscene_shown = False
                self.boss_intro_shown = False
                self.boss_defeat_shown = False
                self.set_ending_shown = False
                self.mid_dialogue_shown_waves.clear()  # 중간 대사 플래그 초기화

            advance_to_next_wave(self.game_data, self.player, self.sound_manager)

    def _handle_level_up_event(self, event: pygame.event.Event):
        """레벨업 이벤트 - 키보드 및 마우스 클릭 지원"""
        option_key = -1

        # 키보드 입력 처리
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_1: option_key = 0
            elif event.key == pygame.K_2: option_key = 1
            elif event.key == pygame.K_3: option_key = 2
            elif event.key == pygame.K_4: option_key = 3
            elif event.key == pygame.K_l:
                if "previous_game_state" in self.game_data:
                    self.game_data["game_state"] = self.game_data["previous_game_state"]
                else:
                    self.game_data["game_state"] = config.GAME_STATE_RUNNING
                self.game_data["tactical_options"] = []
                self.game_data["skill_view_readonly"] = False
                return

        # 마우스 클릭 처리
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = event.pos
            card_rects = self.game_data.get("level_up_card_rects", [])
            for i, card_rect in enumerate(card_rects):
                if card_rect.collidepoint(mouse_pos):
                    option_key = i
                    break

        # 옵션 선택 처리
        if option_key != -1 and not self.game_data.get("skill_view_readonly", False):
            handle_tactical_upgrade(
                option_key, self.player, self.enemies, self.bullets,
                self.gems, self.effects, self.game_data,
                self.game_data["tactical_options"],
                self.engine.shared_state.get("player_upgrades", {})
            )
            if "pending_drones" in self.game_data and len(self.game_data["pending_drones"]) > 0:
                for orbit_angle in self.game_data["pending_drones"]:
                    self.drones.append(Drone(self.player, orbit_angle))
                self.game_data["pending_drones"].clear()

            # 터렛 자동 배치 처리 (쿨다운 UI 상단)
            if self.game_data.get("pending_turrets", 0) > 0:
                self._auto_place_turrets()

            self._check_game_over()

    def _handle_shop_event(self, event: pygame.event.Event):
        """상점 이벤트"""
        if event.type == pygame.KEYDOWN and event.key == pygame.K_c:
            self.engine.shared_state['global_score'] = self.game_data['score']
            self.engine.shared_state['player_upgrades'] = self.player.upgrades
            self.engine.save_shared_state()
            if "previous_game_state" in self.game_data:
                self.game_data["game_state"] = self.game_data["previous_game_state"]
            else:
                self.game_data["game_state"] = config.GAME_STATE_RUNNING

    def _handle_paused_event(self, event: pygame.event.Event):
        """일시정지 이벤트 - 마우스 클릭 지원"""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = event.pos

            # Resume 버튼 클릭
            if "resume" in self.menu_button_rects:
                if self.menu_button_rects["resume"].collidepoint(mouse_pos):
                    self.game_data["game_state"] = config.GAME_STATE_RUNNING
                    self.sound_manager.play_sfx("button_click")
                    return

            # Workshop 버튼 클릭
            if "workshop" in self.menu_button_rects:
                if self.menu_button_rects["workshop"].collidepoint(mouse_pos):
                    self.sound_manager.play_sfx("button_click")
                    self._open_workshop()
                    return

            # Quit 버튼 클릭
            if "quit" in self.menu_button_rects:
                if self.menu_button_rects["quit"].collidepoint(mouse_pos):
                    self.game_data["previous_game_state"] = config.GAME_STATE_PAUSED
                    self.game_data["game_state"] = config.GAME_STATE_QUIT_CONFIRM
                    self.sound_manager.play_sfx("button_click")
                    return

        # 키보드 단축키
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_w:
                # W 키로 Workshop 열기
                self.sound_manager.play_sfx("button_click")
                self._open_workshop()

    def _handle_game_over_event(self, event: pygame.event.Event):
        """게임 오버 이벤트 - 마우스 클릭 지원"""
        # 마우스 클릭 처리
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = event.pos

            # Restart 버튼 클릭
            if "restart" in self.menu_button_rects:
                if self.menu_button_rects["restart"].collidepoint(mouse_pos):
                    self._restart_game()
                    self.sound_manager.play_sfx("button_click")
                    return

            # Quit 버튼 클릭
            if "quit" in self.menu_button_rects:
                if self.menu_button_rects["quit"].collidepoint(mouse_pos):
                    self.request_quit()
                    return

        # 키보드 처리 (기존 유지)
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                self._restart_game()
            elif event.key == pygame.K_ESCAPE:
                self.request_quit()

    def _handle_victory_event(self, event: pygame.event.Event):
        """승리 이벤트 - 미션 완료 후 BaseHub로 귀환"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                # 미션 완료 처리 후 BaseHub로 귀환
                self._complete_mission_and_return()
            elif event.key == pygame.K_r:
                self._restart_game()
            elif event.key == pygame.K_q or event.key == pygame.K_ESCAPE:
                self._complete_mission_and_return()

    def _complete_mission_and_return(self):
        """미션 완료 처리 후 BaseHub로 귀환"""
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

            # 캠페인 진행 저장
            self._save_campaign_progress()

            print(f"INFO: Mission {current_mission} completed!")

        # 미션 상태 초기화
        self.engine.shared_state['current_mission'] = None
        self.engine.shared_state['mission_data'] = None
        self.engine.shared_state['from_briefing'] = False

        # BaseHub로 귀환
        from modes.base_hub_mode import BaseHubMode
        self.request_switch_mode(BaseHubMode)

    def _save_campaign_progress(self):
        """캠페인 진행 상황 저장"""
        import json
        from pathlib import Path
        from mode_configs.config_missions import get_next_main_mission, get_current_act

        completed_missions = self.engine.shared_state.get('completed_missions', [])
        next_mission = get_next_main_mission(completed_missions)
        current_act = get_current_act(completed_missions)
        credits = self.engine.shared_state.get('global_score', 0)

        save_data = {
            "current_mission": next_mission if next_mission else "completed",
            "completed_missions": completed_missions,
            "current_act": current_act,
            "credits": credits,
        }

        save_path = Path("saves/campaign_progress.json")
        try:
            save_path.parent.mkdir(parents=True, exist_ok=True)
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, indent=2)
            print(f"INFO: Campaign progress saved - Act {current_act}, next: {next_mission}")
        except Exception as e:
            print(f"WARNING: Failed to save campaign progress: {e}")

    def _handle_quit_confirm_event(self, event: pygame.event.Event):
        """종료 확인 이벤트"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_y:
                self.engine.save_shared_state()
                self.request_quit()
            elif event.key == pygame.K_n or event.key == pygame.K_ESCAPE:
                if "previous_game_state" in self.game_data:
                    self.game_data["game_state"] = self.game_data["previous_game_state"]
                else:
                    self.game_data["game_state"] = config.GAME_STATE_RUNNING

    def _restart_game(self):
        """게임 재시작"""
        self.game_data = reset_game_data()
        self.game_data['score'] = self.engine.shared_state.get('global_score', 0)
        self.game_data['game_state'] = config.GAME_STATE_WAVE_PREPARE
        self.game_data['max_waves'] = 5

        self.spawn_player(
            pos=self.config.player_start_pos,
            upgrades=self.engine.shared_state.get('player_upgrades', {})
        )

        self.enemies.clear()
        self.bullets.clear()
        self.gems.clear()
        self.effects.clear()
        self.damage_number_manager.clear()
        self.turrets.clear()
        self.drones.clear()
        self.death_effect_manager.clear()

        if self.dynamic_background:
            self.dynamic_background.set_wave(1)
            self.last_kill_count = 0

        # 스토리 컷씬 플래그 초기화
        self.current_set = 1
        self.set_briefing_shown = False
        self.memory_cutscene_shown = False
        self.act_cutscene_shown = False
        self.active_cutscene = None
        self.story_state = "normal"

        # =========================================================
        # 새 시스템 상태 리셋
        # =========================================================
        self._reset_combat_dialogue_state()
        self.current_objective = None
        self.objective_progress = 0
        self.survival_timer = 0.0
        self.defense_hp = 0
        self.collected_data = 0
        self.escort_progress = 0.0
        self.rescued_count = 0
        self.rescue_targets = []  # 구출 대상 초기화
        self.environment_timer = 0.0
        self.emp_active = False
        self.safe_zone_radius = 0

        print("INFO: StoryMode restarted")

    def _auto_place_turrets(self):
        """터렛을 쿨다운 UI 상단에 자동 배치"""
        pending = self.game_data.get("pending_turrets", 0)
        if pending <= 0:
            return

        # 쿨다운 UI 위치 (화면 하단 중앙)
        base_x = self.screen_size[0] // 2
        base_y = self.screen_size[1] - 60 - 100  # 쿨다운 UI 상단 (60 = UI 위치, 100 = 터렛 공간)

        # 새 터렛 추가
        for _ in range(pending):
            self.turrets.append(Turret(pos=(0, 0)))  # 임시 위치

        # 전체 터렛 개수에 따라 위치 재계산 (좌우 균형)
        total_count = len(self.turrets)
        turret_spacing = 100  # 터렛 간 간격

        for i, turret in enumerate(self.turrets):
            if total_count == 1:
                pos_x = base_x
            elif total_count == 2:
                pos_x = base_x - turret_spacing // 2 + i * turret_spacing
            else:
                half_width = (total_count - 1) * turret_spacing / 2
                pos_x = base_x - half_width + i * turret_spacing

            turret.pos.x = pos_x
            turret.pos.y = base_y

        self.game_data["pending_turrets"] = 0
        self.sound_manager.play_sfx("turret_place")
        print(f"INFO: {pending} turret(s) auto-placed. Total: {total_count}")

    def on_exit(self):
        """모드 종료"""
        # 커스텀 커서 비활성화 (원래 커서 복원)
        if self.custom_cursor_enabled:
            self.enable_custom_cursor(False)

        self.engine.shared_state['global_score'] = self.game_data.get('score', 0)
        if self.player:
            self.engine.shared_state['player_upgrades'] = self.player.upgrades
        super().on_exit()

    def _open_workshop(self):
        """Workshop(정비소) 모드 열기"""
        # 현재 상태 저장
        self.engine.shared_state['global_score'] = self.game_data.get('score', 0)
        if self.player:
            self.engine.shared_state['player_upgrades'] = self.player.upgrades

        # WorkshopMode를 현재 모드 위에 push
        from modes.workshop_mode import WorkshopMode
        self.request_push_mode(WorkshopMode)

    def on_resume(self, return_data=None):
        """Workshop에서 돌아올 때 호출"""
        super().on_resume(return_data)
        # Workshop에서 변경된 업그레이드 적용
        self.game_data['score'] = self.engine.shared_state.get('global_score', 0)
        if self.player:
            new_upgrades = self.engine.shared_state.get('player_upgrades', {})
            self.player.upgrades = new_upgrades
            self.player.calculate_stats_from_upgrades()
            print("INFO: Player upgrades applied from Workshop")


print("INFO: story_mode.py loaded")
