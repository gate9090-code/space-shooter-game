# VFX 제작 워크플로우 - 개발자와 아티스트 협업 가이드

## 🎯 전체 흐름

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│ 아티스트     │────▶│ VFX Editor   │────▶│ 개발자       │
│ (이미지 제작)│     │ (효과 제작)   │     │ (게임 적용)  │
└─────────────┘     └──────────────┘     └──────────────┘
      │                     │                     │
      │  PNG 파일           │  JSON 설정          │  게임 코드
      ▼                     ▼                     ▼
   Photoshop          vfx_editor.py         game_logic/
   GIMP                                     wave_manager.py
   등등                                     etc.
```

---

## 👨‍🎨 아티스트 역할

### 준비물
- PNG 이미지 파일 (투명 배경)
- VFX Editor 툴 실행 환경

### 작업 과정
1. 이미지 제작/다운로드
2. VFX Editor 실행
3. 드래그 앤 드롭으로 이미지 로드
4. 슬라이더로 효과 조정
5. 프리뷰로 확인
6. 저장 버튼 클릭
7. **개발자에게 알림**

### 전달 정보
```
효과 완성!
- 이름: fire_explosion
- 카테고리: boss_effects
- 용도: 보스 사망 시 폭발
- 파일: fire_explosion.png
```

---

## 👨‍💻 개발자 역할

### 아티스트로부터 받은 정보 확인
```
효과: fire_explosion
카테고리: boss_effects
```

### 게임 코드에 적용
```python
from systems.vfx_manager import get_vfx_manager

vfx = get_vfx_manager()

# 보스 사망 시
if boss.hp <= 0:
    effects = vfx.create_multi_shockwave(
        center=(boss.pos.x, boss.pos.y),
        category="boss_effects",
        variant="fire_explosion"
    )
    self.effects.extend(effects)
```

### 완료!
- JSON 파일은 이미 VFX Editor가 저장함
- 이미지는 자동으로 폴더 스캔에서 인식
- 코드만 추가하면 끝

---

## 🔄 반복 프로세스

### 수정 요청 시
```
개발자: "불 효과가 너무 작아요. 더 크게 해주세요."
   ↓
아티스트: VFX Editor 열기 → 슬라이더 조정 → 저장
   ↓
개발자: 게임 재시작 (자동 반영)
   ↓
확인 → OK!
```

---

## 📂 파일 구조

### 아티스트가 작업하는 곳
```
assets/images/vfx/combat/
├── hit_effects/          # 여기에 이미지 저장
│   └── fire_explosion.png
├── critical_effects/
├── boss_effects/
└── skill_effects/
```

### 자동 생성되는 설정
```
assets/config/vfx_effects.json  # VFX Editor가 자동 저장
```

### 개발자가 수정하는 곳
```
game_logic/
├── wave_manager.py       # 전투 로직
├── helpers.py            # 효과 생성 헬퍼
systems/
└── vfx_manager.py        # VFX 시스템 (건드릴 필요 없음)
```

---

## 🎮 3가지 사용 방법 비교

### 방법 1: 자동 (폴더만)
**아티스트**: 이미지를 폴더에 복사
**개발자**: 코드에서 파일명으로 사용

```python
# 이미지: hit_effects/lightning.png
effects = vfx.create_multi_shockwave(pos, "hit_effects", "lightning")
```

**장점**: 가장 빠름
**단점**: 기본 설정만 사용

---

### 방법 2: VFX Editor (추천!)
**아티스트**: VFX Editor로 커스터마이징 + 저장
**개발자**: 동일하게 코드 작성

```python
# VFX Editor에서 저장한 효과
effects = vfx.create_multi_shockwave(pos, "boss_effects", "fire_explosion")
```

**장점**: 디자이너가 완전한 제어
**단점**: JSON 파일 생성됨 (문제 아님)

---

### 방법 3: JSON 직접 편집
**아티스트**: 이미지만 제공
**개발자**: JSON 파일 직접 작성

```json
{
  "boss_effects": {
    "fire_explosion": {
      "image": "...",
      "max_size": 500,
      ...
    }
  }
}
```

**장점**: 가장 정밀한 제어
**단점**: 프로그래밍 지식 필요

---

## 🚀 빠른 시작 (개발자용)

### 1. VFX Editor 실행
```bash
python vfx_editor.py
```

### 2. 아티스트에게 알림
"VFX Editor로 효과 만들어주세요!"

### 3. 완성 통보 받으면
```python
# 게임 코드에 추가
vfx = get_vfx_manager()
effects = vfx.create_multi_shockwave(pos, "category", "effect_name")
self.effects.extend(effects)
```

### 4. 끝!

---

## 💡 실전 예제

### 시나리오: 속성 총알 시스템 구현

#### 요구사항
- 불, 얼음, 전기 3가지 속성
- 각각 다른 효과

#### 아티스트 작업
1. VFX Editor 실행
2. 불 효과 제작 (주황색, 큰 크기)
3. 얼음 효과 제작 (파란색, 작은 크기)
4. 전기 효과 제작 (노란색, 빠른 파동)
5. 각각 저장:
   - `element_fire`
   - `element_ice`
   - `element_electric`

#### 개발자 작업
```python
# 총알 속성에 따라 자동 매칭
element = bullet.element  # "fire", "ice", "electric"
effect_name = f"element_{element}"

effects = vfx.create_multi_shockwave(
    center=(bullet.pos.x, bullet.pos.y),
    category="hit_effects",
    variant=effect_name
)
self.effects.extend(effects)
```

#### 결과
- 불 총알 → 주황색 큰 효과
- 얼음 총알 → 파란색 작은 효과
- 전기 총알 → 노란색 빠른 효과

**코드 3줄로 완성!**

---

## 🎓 개발자 팁

### 효과 미리보기
```python
vfx = get_vfx_manager()
all_effects = vfx.list_effects()
print(all_effects)
```

### 실시간 리로드
```python
# 게임 실행 중 설정 변경 시
vfx.reload_config()
```

### 조건부 효과
```python
if is_critical:
    effects = vfx.create_multi_shockwave(pos, "critical_effects", "default")
elif enemy.is_boss:
    effects = vfx.create_multi_shockwave(pos, "boss_effects", "hit")
else:
    effects = vfx.create_multi_shockwave(pos, "hit_effects", "normal")
```

---

## 📊 성능 고려사항

### 이미지 최적화
- PNG 압축 권장
- 512x512 이하 유지
- 불필요한 메타데이터 제거

### 동시 효과 수
- 화면에 50개 이하 권장
- 폴더 이미지: 20개 이하
- JSON 효과: 제한 없음

### 캐싱
- 이미지는 자동 캐싱
- 메모리 효율적
- 게임 시작 시 한 번만 로드

---

## 🐛 문제 해결

### 효과가 안 보여요
1. JSON 파일 확인
2. 이미지 경로 확인
3. 폴더 구조 확인
4. `vfx.reload_config()` 호출

### VFX Editor 오류
1. pygame_gui 설치 확인: `pip install pygame_gui`
2. 이미지 포맷 확인 (PNG만 가능)
3. 권한 문제 확인

---

## ✅ 체크리스트

### 아티스트
- [ ] PNG 이미지 준비
- [ ] VFX Editor 실행
- [ ] 효과 제작 및 저장
- [ ] 개발자에게 알림

### 개발자
- [ ] 효과 이름 확인
- [ ] 카테고리 확인
- [ ] 게임 코드 추가
- [ ] 테스트

---

## 🎉 결론

**VFX Editor = 협업의 핵심**

- ✅ 아티스트: 코드 몰라도 OK
- ✅ 개발자: 설정 신경 안 써도 OK
- ✅ 빠른 반복 개발
- ✅ 실시간 피드백

**효과 제작 시간: 5분 → 30초** 🚀
