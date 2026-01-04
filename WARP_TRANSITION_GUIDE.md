# 웨이브 워프 전환 시스템 가이드

## 🎯 변경사항 개요

웨이브 클리어 후 흐름을 개선하여 게임 진행을 부드럽게 만들었습니다.

### ❌ 기존 (문제점)
```
웨이브 클리어 → WAVE_CLEAR 화면 (클릭 대기) → LEVEL_UP → WAVE_PREPARE (클릭 대기) → 다음 웨이브
                    ↑ 화면 1개               ↑ 레벨업           ↑ 화면 2개
```

**문제점:**
- 2개의 대기 화면이 연속으로 나타남
- 게임 흐름이 끊김
- 플레이어가 2번 클릭해야 함

### ✅ 새로운 (워프 포탈)
```
웨이브 클리어 → 워프 포탈 생성 → 우주선 빨려들어감 → LEVEL_UP → WAVE_PREPARE → 다음 웨이브
                    ↑ 자동 진행 (2-3초)          ↑ 레벨업      ↑ 1개 화면만
```

**장점:**
- 1개의 대기 화면만 (WAVE_PREPARE)
- 자동으로 진행되어 부드러움
- 시각적으로 화려한 워프 효과
- 보스 웨이브는 파란색, 일반 웨이브는 초록색

---

## 🌀 워프 시퀀스 동작

### 1. 포탈 생성 (1초)
```python
# 화면 중앙 상단에 포탈 생성
portal = WarpPortal(
    center=(화면 중앙, 250),
    color_scheme="blue" if 보스웨이브 else "green"
)
```

### 2. 우주선 진입 (1-2초)
- 우주선이 포탈로 끌려감
- `pull_strength=200.0`으로 자연스럽게 이동
- 거리 < 40 도달 시 다음 단계

### 3. 포탈 닫힘 (0.5초)
- 우주선이 포탈 중심에 도달
- 자동으로 레벨업 화면 전환
- WAVE_CLEAR 화면 건너뜀

**총 소요 시간: 2.5-3.5초** (자동 진행)

---

## 🎨 색상 의미

### 파란색 포탈 (Blue)
- **보스 웨이브** (5, 10, 15, 20)
- 강력한 전투 후 워프
- 다음 보스로 이동하는 느낌

### 초록색 포탈 (Green)
- **일반 웨이브**
- 안전한 전환
- 다음 전투 준비

---

## 🔧 주요 코드 변경

### 1. 웨이브 클리어 시
```python
# 기존: WAVE_CLEAR 화면으로 전환
game_data["game_state"] = config.GAME_STATE_WAVE_CLEAR

# 새로운: 워프 시퀀스 시작
self._start_warp_sequence()
```

### 2. 워프 시퀀스 업데이트
```python
def _update_warp_sequence(self, dt):
    if self.warp_state == 'portal_opening':
        # 1초간 포탈 생성
    elif self.warp_state == 'ship_warping':
        # 우주선을 포탈로 끌어당김
    elif self.warp_state == 'portal_closing':
        # 레벨업 화면으로 전환
        advance_to_next_wave(...)
```

### 3. 렌더링
```python
# 워프 포탈 렌더링 (게임 객체 위에)
if self.warp_portal:
    self.warp_portal.draw(screen)

# WAVE_CLEAR 화면은 워프 활성화 시 숨김
if not self.warp_active:
    draw_wave_clear_screen(...)
```

---

## 📊 상태 흐름도

```
웨이브 전투
    ↓
목표 달성 (target_kills 또는 전멸)
    ↓
승리 애니메이션 (PlayerVictoryAnimation)
    ↓
┌─────────────────────────┐
│ 워프 시퀀스 시작          │
│                          │
│ 1. portal_opening (1초)  │
│    - 포탈 생성           │
│    - 링 회전 시작        │
│    - 파티클 소용돌이     │
│                          │
│ 2. ship_warping (1-2초)  │
│    - 우주선 끌어당김     │
│    - 포탈 중심으로 이동  │
│                          │
│ 3. portal_closing (0.5초)│
│    - 우주선 진입 완료    │
│    - 포탈 닫힘           │
└─────────────────────────┘
    ↓
레벨업 화면 (LEVEL_UP)
    ↓
웨이브 준비 화면 (WAVE_PREPARE)
    ↓
다음 웨이브 시작
```

---

## 🎮 플레이어 경험

### 기존
1. 웨이브 클리어!
2. "Wave X Cleared!" 화면 → **클릭 대기**
3. 레벨업 선택
4. "Wave X+1 Prepare" 화면 → **클릭 대기**
5. 다음 웨이브 시작

**총 클릭 횟수: 3회** (클리어 화면 + 레벨업 + 준비 화면)

### 새로운
1. 웨이브 클리어!
2. 포탈 생성 + 우주선 자동 진입 → **자동 진행 (2-3초)**
3. 레벨업 선택
4. "Wave X+1 Prepare" 화면 → **클릭 대기**
5. 다음 웨이브 시작

**총 클릭 횟수: 2회** (레벨업 + 준비 화면)
**대기 화면: 1개로 감소**

---

## 🐛 WAVE_CLEAR 화면 역할 (삭제하지 않은 이유)

### 트리거 역할
```python
def _handle_wave_clear_event(self, event):
    # 1. 게임 오버 체크
    if self.player.hp <= 0:
        self._check_game_over()
        return

    # 2. 진행 상황 저장
    self.save_progress()

    # 3. 다음 웨이브로 전환
    advance_to_next_wave(...)
```

### 보존 이유
- 에러 방지 목적으로 코드 유지
- 워프 포탈이 실패할 경우 폴백 경로
- 특수 모드에서 사용 가능성

### 동작 방식
```python
# 워프 포탈 활성화 시 무시
if not self.warp_active:
    draw_wave_clear_screen(...)

# 이벤트도 무시
if not self.warp_active:
    self._handle_wave_clear_event(event)
```

**결과: 워프 포탈이 모든 기능을 대체하지만, 안전장치로 WAVE_CLEAR 코드 유지**

---

## 🚀 테스트 방법

### 1. 일반 웨이브 클리어
```
1. 웨이브 시작
2. 적 처치 (target_kills 달성 또는 전멸)
3. 초록색 포탈 생성 확인
4. 우주선이 자동으로 빨려들어가는지 확인
5. 레벨업 화면으로 자동 전환 확인
```

### 2. 보스 웨이브 클리어 (5, 10, 15, 20)
```
1. 보스 처치
2. 파란색 포탈 생성 확인
3. 워프 효과 확인
4. 레벨업 화면 전환 확인
```

### 3. 예외 상황
```
1. HP가 0인 상태로 클리어
   → 게임 오버로 전환 (정상)

2. 20웨이브 클리어
   → 승리 화면으로 전환 (정상)
```

---

## 🎨 커스터마이징

### 포탈 크기 조정
```python
# wave_mode.py - _start_warp_sequence()
self.warp_portal = WarpPortal(
    max_radius=180,  # 기본값, 크게: 250, 작게: 120
    particle_count=70,
    ring_count=4
)
```

### 끌어당기는 힘 조정
```python
# wave_mode.py - _update_warp_sequence()
new_pos = self.warp_portal.pull_object(
    (self.player.pos.x, self.player.pos.y),
    dt,
    pull_strength=200.0  # 빠르게: 400, 느리게: 100
)
```

### 타이밍 조정
```python
# wave_mode.py - _update_warp_sequence()
if self.warp_state == 'portal_opening':
    if self.warp_timer >= 1.0:  # 포탈 생성 시간 (기본 1초)

elif self.warp_state == 'portal_closing':
    if self.warp_timer >= 0.5:  # 포탈 닫힘 대기 (기본 0.5초)
```

---

## 📝 파일 변경사항

### 수정된 파일
- [modes/wave_mode.py](modes/wave_mode.py) - 워프 시퀀스 로직 추가

### 변경 내용
1. Import 추가: `WarpPortal`, `DepthEffect`
2. 초기화: 워프 포탈 변수 추가
3. 메서드 추가:
   - `_start_warp_sequence()` - 포탈 생성
   - `_update_warp_sequence()` - 워프 진행
4. `update()`: 워프 시퀀스 업데이트 호출
5. `draw()`: 포탈 렌더링 추가
6. 이벤트 처리: WAVE_CLEAR 무시 조건 추가

### 삭제하지 않은 것
- `draw_wave_clear_screen()` - 폴백 용도로 유지
- `_handle_wave_clear_event()` - 에러 방지용 유지
- `GAME_STATE_WAVE_CLEAR` - 시스템 호환성 유지

---

## 🎉 결과

**개선사항:**
- ✅ 게임 흐름 부드럽게 개선
- ✅ 대기 화면 2개 → 1개로 감소
- ✅ 자동 진행으로 사용자 경험 향상
- ✅ 시각적으로 화려한 워프 효과
- ✅ 보스/일반 웨이브 구분 (파란/초록)
- ✅ 에러 방지를 위한 안전장치 유지

**플레이 시간:**
- 기존: 웨이브당 평균 5-10초 대기 (클릭 대기)
- 새로운: 웨이브당 평균 2-3초 자동 전환

**게임 20웨이브 기준:**
- 기존: 100-200초 (1.5-3분) 대기
- 새로운: 40-60초 (1분 이하) 대기

**절감 시간: 약 50-60% 감소!** 🚀
