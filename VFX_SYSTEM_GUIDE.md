# VFX System - 이미지 기반 효과 자동화 가이드

## 📖 개요

이미지만 교체하면 코드 수정 없이 다양한 시각 효과를 만들 수 있는 시스템입니다.

### 주요 특징
- ✅ **JSON 설정 기반** - 코드 수정 없이 효과 추가/변경
- ✅ **이미지 캐싱** - 메모리 효율적, 빠른 성능
- ✅ **다중 효과** - 하나의 이미지로 다양한 변형 생성
- ✅ **실시간 리로드** - 게임 재시작 없이 설정 변경 가능

---

## 🚀 빠른 시작

### 1. 새로운 효과 추가하기

#### 방법 A: JSON 파일만 편집 (추천)

`assets/config/vfx_effects.json` 편집:

```json
{
  "hit_effects": {
    "laser": {
      "image": "assets/images/vfx/combat/laser_ring.png",
      "max_size": 200,
      "duration": 0.5,
      "color_tint": [100, 200, 255],
      "wave_count": 2,
      "wave_interval": 0.08
    }
  }
}
```

#### 방법 B: 기존 이미지 재사용

같은 이미지로 색상만 바꿔서 다른 효과:

```json
{
  "hit_effects": {
    "plasma": {
      "image": "assets/images/vfx/combat/purse_ring_effect.png",
      "max_size": 300,
      "duration": 0.9,
      "color_tint": [255, 0, 255],
      "wave_count": 5,
      "wave_interval": 0.1
    }
  }
}
```

### 2. 게임 코드에서 사용하기

```python
from systems.vfx_manager import get_vfx_manager

# VFXManager 가져오기
vfx_manager = get_vfx_manager()

# 효과 생성 (단일)
shockwave = vfx_manager.create_shockwave(
    center=(bullet.pos.x, bullet.pos.y),
    category="hit_effects",
    variant="fire"
)
effects.append(shockwave)

# 효과 생성 (다중 파동)
shockwaves = vfx_manager.create_multi_shockwave(
    center=(enemy.pos.x, enemy.pos.y),
    category="boss_effects",
    variant="death"
)
effects.extend(shockwaves)
```

### 3. 조건별 효과 사용

```python
# 플레이어 속성에 따라 다른 효과
if player.has_fire_bullets:
    effects_list = vfx_manager.create_multi_shockwave(pos, "hit_effects", "fire")
elif player.has_ice_bullets:
    effects_list = vfx_manager.create_multi_shockwave(pos, "hit_effects", "ice")
else:
    effects_list = vfx_manager.create_multi_shockwave(pos, "hit_effects", "normal")

# 크리티컬 히트
if is_critical:
    effects_list = vfx_manager.create_multi_shockwave(pos, "critical_effects", "default")

# 보스 전용 효과
if enemy.is_boss:
    effects_list = vfx_manager.create_multi_shockwave(pos, "boss_effects", "hit")
```

---

## 📁 파일 구조

```
working/
├── assets/
│   ├── config/
│   │   └── vfx_effects.json          # 효과 설정 (JSON)
│   └── images/
│       └── vfx/
│           └── combat/
│               ├── purse_ring_effect.png  # 기본 링 이미지
│               ├── laser_ring.png         # 레이저 효과
│               ├── fire_ring.png          # 불 효과
│               └── ice_ring.png           # 얼음 효과
├── systems/
│   └── vfx_manager.py                # VFXManager 클래스
├── effects/
│   └── screen_effects.py             # ImageShockwave 클래스
└── test_vfx_system.py                # 테스트 스크립트
```

---

## 🎨 JSON 설정 상세

### 설정 파라미터

```json
{
  "category_name": {
    "variant_name": {
      "image": "경로/이미지.png",        // 이미지 파일 경로
      "max_size": 240,                  // 최대 크기 (픽셀)
      "duration": 0.8,                  // 지속 시간 (초)
      "color_tint": [255, 255, 255],    // RGB 색상 틴트
      "wave_count": 3,                  // 파동 개수
      "wave_interval": 0.1,             // 파동 간격 (초)
      "description": "설명"              // 주석 (선택사항)
    }
  }
}
```

### 파라미터 설명

| 파라미터 | 타입 | 설명 | 예시 |
|---------|------|------|------|
| `image` | string | 이미지 파일 경로 | `"assets/images/vfx/combat/ring.png"` |
| `max_size` | int | 최대 크기 (픽셀) | `240` = 지름 240px |
| `duration` | float | 애니메이션 시간 (초) | `0.8` = 0.8초 동안 확장 |
| `color_tint` | [int, int, int] | RGB 색상 틴트 (0-255) | `[255, 100, 50]` = 주황색 |
| `wave_count` | int | 생성할 파동 개수 | `3` = 3개 연속 |
| `wave_interval` | float | 파동 사이 시간 (초) | `0.1` = 0.1초 간격 |

---

## 💡 사용 예시

### 예시 1: 속성 총알 시스템

```python
# game_logic/wave_manager.py 수정
from systems.vfx_manager import get_vfx_manager

vfx_manager = get_vfx_manager()

# 총알 적중 시
def on_bullet_hit(bullet, enemy, effects):
    # 총알 속성에 따라 다른 효과
    if hasattr(bullet, 'element'):
        variant = bullet.element  # "fire", "ice", "electric"
    else:
        variant = "normal"

    shockwaves = vfx_manager.create_multi_shockwave(
        center=(bullet.pos.x, bullet.pos.y),
        category="hit_effects",
        variant=variant
    )
    effects.extend(shockwaves)
```

### 예시 2: 레벨에 따른 효과

```json
{
  "player_skills": {
    "level_1": {
      "image": "assets/images/vfx/combat/basic_skill.png",
      "max_size": 200,
      "duration": 0.6,
      "color_tint": [200, 200, 200],
      "wave_count": 2
    },
    "level_2": {
      "image": "assets/images/vfx/combat/advanced_skill.png",
      "max_size": 280,
      "duration": 0.8,
      "color_tint": [255, 200, 100],
      "wave_count": 4
    },
    "level_3": {
      "image": "assets/images/vfx/combat/ultimate_skill.png",
      "max_size": 400,
      "duration": 1.2,
      "color_tint": [255, 100, 255],
      "wave_count": 8
    }
  }
}
```

---

## 🧪 테스트

### 테스트 스크립트 실행

```bash
python test_vfx_system.py
```

### 조작법
- **마우스 클릭** - 효과 생성
- **1-9** - 효과 선택
- **←/→** - 효과 순환
- **R** - 설정 리로드
- **C** - 효과 전부 클리어
- **H** - 도움말 토글

---

## 🎯 실전 적용 예시

### 전투 시스템에 적용

```python
# game_logic/wave_manager.py (Line 414-429)

# 기존 코드:
from effects.screen_effects import ImageShockwave
settings = config.SHOCKWAVE_SETTINGS["BULLET_HIT"]
for i in range(wave_count):
    shockwave = ImageShockwave(...)
    effects.append(shockwave)

# 새 코드:
from systems.vfx_manager import get_vfx_manager
vfx_manager = get_vfx_manager()

# 총알 속성 확인
effect_variant = "normal"
if hasattr(bullet, 'element'):
    effect_variant = bullet.element

shockwaves = vfx_manager.create_multi_shockwave(
    center=(impact_pos.x, impact_pos.y),
    category="hit_effects",
    variant=effect_variant
)
effects.extend(shockwaves)
```

---

## 🖼️ 이미지 제작 가이드

### 권장 사양
- **포맷**: PNG (투명 배경 지원)
- **크기**: 360x360px 이상 (정사각형)
- **투명도**: 알파 채널 필수
- **중심**: 이미지 중앙에 효과 배치

### 디자인 팁
1. **대비**: 밝은 색상, 높은 대비
2. **여백**: 가장자리에 여백 두기 (10% 이상)
3. **그라디언트**: 중심에서 가장자리로 페이드
4. **디테일**: 과하지 않게 (확대/축소됨)

### 예시 이미지
```
purse_ring_effect.png - 기본 흰색 링 (현재 사용 중)
├─ 중심: 투명
├─ 링: 흰색, 부드러운 그라디언트
└─ 가장자리: 페이드 아웃
```

---

## 🔧 고급 활용

### 1. 실시간 설정 리로드

```python
# 게임 중 설정 변경 후
vfx_manager.reload_config()
```

### 2. 사용 가능한 효과 목록 확인

```python
effects_list = vfx_manager.list_effects()
print(effects_list)
# {
#   "hit_effects": ["normal", "fire", "ice", "electric"],
#   "critical_effects": ["default"],
#   "boss_effects": ["hit", "death"]
# }
```

### 3. 특정 효과 설정 가져오기

```python
config = vfx_manager.get_effect_config("hit_effects", "fire")
print(config)
# {
#   "image": "...",
#   "max_size": 280,
#   "duration": 1.0,
#   ...
# }
```

---

## 🐛 문제 해결

### Q: 효과가 보이지 않아요
A: 다음을 확인하세요:
1. 이미지 파일 경로가 올바른지
2. `vfx_manager.preload_images()` 호출되었는지
3. `effects` 리스트에 추가되었는지
4. `update_visual_effects()`에서 업데이트되는지

### Q: 색상이 안 바뀌어요
A: `color_tint` 값을 [0, 0, 0]으로 하면 검정색이 됩니다. [255, 255, 255]은 원본 색상입니다.

### Q: JSON 파일 수정 후 반영이 안 돼요
A: 게임을 재시작하거나 `vfx_manager.reload_config()` 호출하세요.

---

## 📈 성능 최적화

### 이미지 캐싱
- 같은 이미지는 한 번만 로드
- 메모리 효율적
- 여러 효과가 동일 이미지 공유

### 권장 사항
- 이미지 크기: 512x512 이하
- 동시 효과: 50개 이하
- 이미지 수: 20개 이하

---

## 🎓 추가 학습 자료

### 관련 파일
- `systems/vfx_manager.py` - VFXManager 구현
- `effects/screen_effects.py` - ImageShockwave 구현
- `assets/config/vfx_effects.json` - 효과 설정
- `test_vfx_system.py` - 사용 예제

### 확장 가능성
- 스프라이트 시트 지원
- 프레임 애니메이션
- 파티클 시스템 통합
- 셰이더 효과
