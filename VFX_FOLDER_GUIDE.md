# VFX 폴더 시스템 가이드 - 이미지만 넣으면 자동 인식!

## 🎯 개요

이미지 파일을 폴더에 넣기만 하면 **코드 수정도, JSON 편집도 필요 없이** 자동으로 새로운 효과가 생성됩니다!

---

## 📁 폴더 구조

```
assets/images/vfx/combat/
├── hit_effects/          # 총알 적중 효과
│   ├── ring_normal.png
│   ├── ring_fire.png
│   └── ring_electric.png
├── critical_effects/     # 크리티컬 효과
│   └── burst.png
├── boss_effects/         # 보스 전용 효과
│   └── explosion.png
└── skill_effects/        # 스킬 효과
    └── meteor.png
```

---

## 🚀 사용 방법

### **Step 1: 이미지 준비**
- 포맷: PNG (투명 배경)
- 권장 크기: 360x360px 이상

### **Step 2: 폴더에 복사**
```bash
# 예: 새로운 얼음 효과 추가
cp my_ice_effect.png assets/images/vfx/combat/hit_effects/ring_ice.png
```

### **Step 3: 끝!**
```python
# 게임 코드에서 바로 사용 가능
vfx = get_vfx_manager()
effects = vfx.create_multi_shockwave(pos, "hit_effects", "ring_ice")
```

---

## 🎨 자동 생성 규칙

### 파일명 → 효과 이름
| 파일 경로 | 카테고리 | 효과 이름 |
|----------|---------|----------|
| `hit_effects/ring_fire.png` | `hit_effects` | `ring_fire` |
| `critical_effects/burst.png` | `critical_effects` | `burst` |
| `boss_effects/explosion.png` | `boss_effects` | `explosion` |

### 자동 설정값
폴더에서 로드된 효과는 기본 설정 적용:
```python
{
    "max_size": 240,        # 크기
    "duration": 0.8,        # 지속 시간
    "color_tint": [255, 255, 255],  # 색상 (흰색 = 원본)
    "wave_count": 3,        # 파동 개수
    "wave_interval": 0.1    # 파동 간격
}
```

---

## 🔧 고급: JSON으로 커스터마이징

폴더 효과를 JSON에서 **재정의**할 수 있습니다:

```json
{
  "hit_effects": {
    "ring_fire": {
      "image": "assets/images/vfx/combat/hit_effects/ring_fire.png",
      "max_size": 350,
      "duration": 1.2,
      "color_tint": [255, 100, 50],
      "wave_count": 7,
      "wave_interval": 0.08
    }
  }
}
```

**우선순위**: JSON 설정 > 폴더 자동 설정

---

## 📊 시스템 동작 방식

```
┌─────────────────────────────────────────┐
│  1. VFXManager 초기화                    │
└──────────────┬──────────────────────────┘
               │
        ┌──────┴──────┐
        │             │
        ▼             ▼
┌──────────────┐  ┌──────────────────┐
│ JSON 로드     │  │ 폴더 스캔         │
│ (우선순위 높음)│  │ (자동 인식)       │
└──────┬───────┘  └──────┬───────────┘
       │                 │
       └────────┬────────┘
                ▼
    ┌────────────────────────┐
    │  효과 병합               │
    │  - JSON 효과 유지        │
    │  - 폴더 효과 추가        │
    └────────────────────────┘
```

---

## 🎯 실전 예제

### 예제 1: 속성 총알 시스템

#### 1단계: 이미지 준비
```
hit_effects/
├── element_fire.png
├── element_ice.png
├── element_thunder.png
└── element_poison.png
```

#### 2단계: 게임 코드
```python
from systems.vfx_manager import get_vfx_manager

vfx = get_vfx_manager()

# 총알 속성에 따라 자동으로 다른 효과
element = bullet.element  # "fire", "ice", "thunder", "poison"
effect_name = f"element_{element}"

effects = vfx.create_multi_shockwave(
    center=(bullet.pos.x, bullet.pos.y),
    category="hit_effects",
    variant=effect_name  # "element_fire", "element_ice", ...
)
```

### 예제 2: 적 타입별 효과

#### 1단계: 폴더 구조
```
boss_effects/
├── dragon_hit.png
├── golem_hit.png
└── demon_hit.png
```

#### 2단계: 코드
```python
# 보스 이름으로 효과 자동 선택
boss_type = enemy.boss_name.lower()  # "dragon", "golem", "demon"
effect_name = f"{boss_type}_hit"

effects = vfx.create_multi_shockwave(pos, "boss_effects", effect_name)
```

---

## 🔍 디버깅

### 로드된 효과 확인
```python
from systems.vfx_manager import get_vfx_manager

vfx = get_vfx_manager()
all_effects = vfx.list_effects()

for category, variants in all_effects.items():
    print(f"{category}:")
    for variant in variants:
        config = vfx.get_effect_config(category, variant)
        source = config.get("source", "json")
        print(f"  - {variant} (from {source})")
```

출력 예:
```
hit_effects:
  - normal (from json)
  - fire (from json)
  - ring_electric (from folder)
  - ring_fire (from folder)
critical_effects:
  - default (from json)
  - burst (from folder)
```

---

## ⚙️ 설정 조합

### 방법 1: 폴더만 사용 (가장 간단)
- 이미지만 폴더에 복사
- 기본 설정 자동 적용
- 빠른 프로토타입

### 방법 2: 폴더 + JSON (추천)
- 폴더에 이미지 추가 (자동 인식)
- JSON에서 일부만 커스터마이징
- 유연성과 편의성 균형

### 방법 3: JSON만 사용
- 모든 설정을 JSON에 명시
- 세밀한 제어
- 협업 시 명확한 문서화

---

## 🎓 팁과 요령

### 1. 네이밍 컨벤션
```
카테고리_타입_속성.png

예시:
hit_fire_small.png
hit_fire_large.png
boss_dragon_death.png
skill_meteor_impact.png
```

### 2. 이미지 최적화
- PNG 압축 도구 사용 (TinyPNG 등)
- 불필요한 메타데이터 제거
- 360x360 ~ 512x512 권장

### 3. 버전 관리
```
old/                  # 백업 폴더
hit_effects/
├── ring_v1.png      # 이전 버전
└── ring_v2.png      # 새 버전
```

---

## 🐛 문제 해결

### Q: 이미지를 추가했는데 인식 안 돼요
A:
1. 파일 확장자가 `.png`인지 확인
2. 카테고리 폴더가 정확한지 확인
3. 게임 재시작 또는 `vfx.reload_config()` 호출

### Q: 효과는 있는데 보이지 않아요
A:
1. 이미지 투명도 확인 (완전 투명이면 안 보임)
2. `max_size` 값 확인 (너무 작으면 안 보임)
3. `color_tint` 확인 ([0,0,0]은 검정색)

### Q: 폴더 효과와 JSON 효과 중 뭐가 우선인가요?
A: **JSON이 우선**입니다. 같은 이름이면 JSON 설정 사용.

---

## 📈 성능 고려사항

### 이미지 캐싱
- 폴더 스캔 시 **모든 이미지 미리 로드**
- 게임 시작 시 한 번만 실행
- 런타임 성능 영향 없음

### 권장 사항
- 폴더당 이미지: 10개 이하
- 총 이미지 수: 50개 이하
- 이미지 크기: 512x512 이하

---

## 🎉 결론

**폴더 시스템 = 가장 쉬운 방법**

1. 이미지 만들기/다운로드
2. 폴더에 복사
3. 끝!

코드도 JSON도 필요 없이, **이미지만으로 무한한 효과**를 만들 수 있습니다! 🎨✨

---

## 📚 관련 문서
- `VFX_SYSTEM_GUIDE.md` - 전체 시스템 가이드
- `assets/config/vfx_effects.json` - JSON 설정 예제
- `test_vfx_system.py` - 인터랙티브 테스트
