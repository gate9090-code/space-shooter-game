"""
Effect Bridge - 기존 이펙트 시스템과 새 시스템 통합

기존 VFXManager/EffectSystem과 새로운 AdvancedEffectManager를 연결하여
점진적인 마이그레이션을 지원합니다.

사용법:
1. 기존 코드 변경 없이 새 이펙트 시스템 사용 가능
2. 기존 이펙트를 새 시스템으로 점진적 교체 가능
3. 두 시스템 동시 운영 가능
"""

import pygame
from typing import Dict, Any, Optional, Tuple, List
from systems.advanced_effect_system import (
    AdvancedEffectManager,
    get_advanced_effect_manager,
    DynamicEffect,
    CompositeEffect,
)


class EffectBridge:
    """
    이펙트 시스템 브릿지

    기존 VFXManager/EffectSystem API를 유지하면서
    새로운 AdvancedEffectManager로 점진적 전환 지원
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

        self._advanced_manager = get_advanced_effect_manager()
        self._use_advanced = True  # 새 시스템 사용 여부
        self._effect_mapping = self._create_effect_mapping()
        self._initialized = True

        print("INFO: EffectBridge initialized")

    def _create_effect_mapping(self) -> Dict[str, str]:
        """
        기존 이펙트 이름 → 새 이펙트 이름 매핑

        기존 VFXManager에서 사용하던 이름을
        새 AdvancedEffectManager의 이름으로 매핑
        """
        return {
            # 히트 이펙트 매핑
            "hit_effects/normal": "hit_normal",
            "hit_effects/fire": "hit_fire",
            "hit_effects/ice": "hit_ice",
            "hit_effects/electric": "hit_electric",
            "hit_effects/poison": "hit_poison",

            # 크리티컬 이펙트 매핑
            "critical_effects/default": "critical_hit",

            # 보스 이펙트 매핑
            "boss_effects/hit": "boss_hit",
            "boss_effects/death": "boss_death",

            # 스킬 이펙트 매핑
            "skill_effects/meteor": "skill_meteor_impact",
            "skill_effects/heal": "skill_heal",

            # 기타 이펙트 매핑
            "spawn": "spawn_portal",
            "collect_coin": "collect_coin",
            "level_up": "level_up_glow",

            # 레거시 이름 지원
            "normal": "hit_normal",
            "fire": "hit_fire",
            "ice": "hit_ice",
            "electric": "hit_electric",
            "poison": "hit_poison",
            "critical": "critical_hit",
        }

    def set_use_advanced(self, use_advanced: bool):
        """새 이펙트 시스템 사용 여부 설정"""
        self._use_advanced = use_advanced
        print(f"INFO: EffectBridge use_advanced = {use_advanced}")

    # ============================================================
    # 기존 VFXManager API 호환 메서드
    # ============================================================

    def create_shockwave(
        self,
        center: Tuple[float, float],
        category: str = "hit_effects",
        variant: str = "normal"
    ):
        """
        기존 VFXManager.create_shockwave() 호환

        Args:
            center: 중심 위치 (x, y)
            category: 이펙트 카테고리 (예: "hit_effects")
            variant: 이펙트 변형 (예: "normal", "fire")
        """
        if not self._use_advanced:
            # 기존 시스템 사용 (폴백)
            from systems.vfx_manager import get_vfx_manager
            return get_vfx_manager().create_shockwave(center, category, variant)

        # 새 시스템으로 매핑
        effect_key = f"{category}/{variant}"
        mapped_name = self._effect_mapping.get(effect_key, variant)

        return self._advanced_manager.create_effect(mapped_name, center)

    def create_multi_shockwave(
        self,
        center: Tuple[float, float],
        category: str = "hit_effects",
        variant: str = "normal"
    ) -> list:
        """
        기존 VFXManager.create_multi_shockwave() 호환

        여러 개의 연속 충격파 대신
        새 시스템에서는 복합 이펙트 사용
        """
        if not self._use_advanced:
            from systems.vfx_manager import get_vfx_manager
            return get_vfx_manager().create_multi_shockwave(center, category, variant)

        # 새 시스템: 복합 이펙트 생성
        composite_name = self._get_composite_for_variant(variant)
        if composite_name:
            return [self._advanced_manager.create_composite(composite_name, center)]

        # 폴백: 단일 이펙트
        effect_key = f"{category}/{variant}"
        mapped_name = self._effect_mapping.get(effect_key, variant)
        return [self._advanced_manager.create_effect(mapped_name, center)]

    def _get_composite_for_variant(self, variant: str) -> Optional[str]:
        """variant에 맞는 복합 이펙트 이름 반환"""
        composite_map = {
            "fire": "fire_explosion",
            "ice": "ice_explosion",
            "critical": "critical_combo",
        }
        return composite_map.get(variant)

    # ============================================================
    # 기존 EffectSystem API 호환 메서드
    # ============================================================

    def create_explosion(
        self,
        effects: List,
        position: pygame.math.Vector2,
        color: Tuple[int, int, int] = (255, 150, 50),
        particle_count: int = 20,
        speed: float = 200,
    ):
        """
        기존 EffectSystem.create_explosion() 호환

        새 시스템에서는 파티클이 내장된 이펙트 사용
        """
        if not self._use_advanced:
            from systems.effect_system import EffectSystem
            return EffectSystem().create_explosion(effects, position, color, particle_count, speed)

        # 색상에 따른 이펙트 선택
        effect_name = self._select_explosion_by_color(color)
        effect = self._advanced_manager.create_effect(
            effect_name,
            (position.x, position.y),
            overrides={"color_tint": list(color)}
        )
        return effect

    def _select_explosion_by_color(self, color: Tuple[int, int, int]) -> str:
        """색상에 따른 폭발 이펙트 선택"""
        r, g, b = color

        # 색상 분석
        if r > 200 and g < 150 and b < 150:  # 빨강 계열
            return "explosion_particle_burst"
        elif r > 200 and g > 150 and b < 100:  # 주황/노랑 계열
            return "hit_fire"
        elif r < 150 and g > 150 and b > 200:  # 파랑 계열
            return "hit_ice"
        elif r < 150 and g > 200 and b < 150:  # 초록 계열
            return "hit_poison"
        else:
            return "explosion_particle_burst"

    def create_hit_effect(
        self,
        effects: List,
        position: pygame.math.Vector2,
        color: Tuple[int, int, int] = (255, 255, 100),
        particle_count: int = 5,
    ):
        """기존 EffectSystem.create_hit_effect() 호환"""
        if not self._use_advanced:
            from systems.effect_system import EffectSystem
            return EffectSystem().create_hit_effect(effects, position, color, particle_count)

        effect = self._advanced_manager.create_effect(
            "hit_normal",
            (position.x, position.y),
            overrides={"color_tint": list(color)}
        )
        return effect

    def create_dynamic_text(
        self,
        effects: List,
        position: pygame.math.Vector2,
        text: str,
        color: Tuple[int, int, int] = (255, 255, 255),
        size: int = 24,
        duration: float = 1.0,
    ):
        """
        기존 EffectSystem.create_dynamic_text() 호환

        텍스트 이펙트는 기존 시스템 유지 (이미지 기반이 아니므로)
        """
        from effects.screen_effects import DynamicTextEffect
        text_effect = DynamicTextEffect(
            text=text,
            size=size,
            color=color,
            pos=(position.x, position.y),
            duration_frames=int(duration * 60),  # 60fps 기준
        )
        effects.append(text_effect)
        return text_effect

    def create_bomb_explosion(
        self,
        effects: List,
        position: pygame.math.Vector2,
        radius: float = 200,
    ):
        """기존 EffectSystem.create_bomb_explosion() 호환"""
        if not self._use_advanced:
            from systems.effect_system import EffectSystem
            return EffectSystem().create_bomb_explosion(effects, position, radius)

        # 새 시스템: 복합 이펙트 사용
        composite = self._advanced_manager.create_composite(
            "explosion_full",
            (position.x, position.y)
        )

        # 텍스트 효과 추가
        self.create_dynamic_text(effects, position, "BOOM!", (255, 100, 50), 40, 1.0)

        return composite

    # ============================================================
    # 새 시스템 직접 접근 메서드
    # ============================================================

    def create_effect(self, effect_name: str, pos: Tuple[float, float],
                      overrides: Optional[Dict] = None):
        """새 시스템의 이펙트 직접 생성"""
        return self._advanced_manager.create_effect(effect_name, pos, overrides)

    def create_composite(self, composite_name: str, pos: Tuple[float, float]):
        """새 시스템의 복합 이펙트 직접 생성"""
        return self._advanced_manager.create_composite(composite_name, pos)

    def update(self, dt: float):
        """모든 이펙트 업데이트"""
        self._advanced_manager.update(dt)

    def draw(self, screen: pygame.Surface):
        """모든 이펙트 렌더링"""
        self._advanced_manager.draw(screen)

    def clear(self):
        """모든 이펙트 제거"""
        self._advanced_manager.clear()

    def hot_reload(self):
        """설정 핫 리로드"""
        return self._advanced_manager.hot_reload()

    def list_effects(self) -> List[str]:
        """사용 가능한 이펙트 목록"""
        return self._advanced_manager.list_effects()

    def list_composites(self) -> List[str]:
        """사용 가능한 복합 이펙트 목록"""
        return self._advanced_manager.list_composites()

    # ============================================================
    # 편의 메서드 - 게임 상황별 이펙트
    # ============================================================

    def play_enemy_death(self, pos: Tuple[float, float], enemy_type: str = "normal"):
        """
        적 사망 이펙트 재생

        Args:
            pos: 위치
            enemy_type: "normal", "elite", "boss"
        """
        if enemy_type == "boss":
            return self.create_composite("boss_death_full", pos)
        elif enemy_type == "elite":
            return self.create_composite("explosion_full", pos)
        else:
            return self.create_effect("death_dissolve", pos)

    def play_hit(self, pos: Tuple[float, float], damage_type: str = "normal", is_critical: bool = False):
        """
        피격 이펙트 재생

        Args:
            pos: 위치
            damage_type: "normal", "fire", "ice", "electric", "poison"
            is_critical: 크리티컬 여부
        """
        if is_critical:
            return self.create_composite("critical_combo", pos)
        else:
            effect_name = f"hit_{damage_type}"
            return self.create_effect(effect_name, pos)

    def play_skill(self, pos: Tuple[float, float], skill_name: str):
        """
        스킬 이펙트 재생

        Args:
            pos: 위치
            skill_name: "meteor", "heal", "phoenix"
        """
        if skill_name == "meteor":
            return self.create_composite("meteor_full", pos)
        elif skill_name == "heal":
            return self.create_effect("skill_heal", pos)
        elif skill_name == "phoenix":
            return self.create_effect("phoenix_ring", pos)
        else:
            return self.create_effect("shockwave_medium", pos)

    def play_collect(self, pos: Tuple[float, float], item_type: str = "coin"):
        """아이템 획득 이펙트 재생"""
        if item_type == "coin":
            return self.create_effect("collect_coin", pos)
        else:
            return self.create_effect("shockwave_small", pos)

    def play_level_up(self, pos: Tuple[float, float]):
        """레벨업 이펙트 재생"""
        return self.create_composite("level_up_full", pos)

    def play_spawn(self, pos: Tuple[float, float]):
        """스폰 이펙트 재생"""
        return self.create_composite("spawn_full", pos)


# 싱글톤 인스턴스 전역 접근 함수
def get_effect_bridge() -> EffectBridge:
    """EffectBridge 싱글톤 인스턴스 가져오기"""
    return EffectBridge()


# ============================================================
# 테스트 및 데모 코드
# ============================================================

if __name__ == "__main__":
    print("Effect Bridge - Integration Test")
    print("=" * 50)

    # 테스트: 매핑 확인
    bridge = get_effect_bridge()

    print("\nEffect Mapping:")
    for old_name, new_name in bridge._effect_mapping.items():
        print(f"  {old_name:30} -> {new_name}")

    print("\nAvailable Effects:")
    for effect in bridge.list_effects():
        print(f"  - {effect}")

    print("\nAvailable Composites:")
    for composite in bridge.list_composites():
        print(f"  - {composite}")
