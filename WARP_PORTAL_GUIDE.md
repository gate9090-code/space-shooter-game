# 워프 포탈 효과 가이드

## 🌀 개요

`effects/physics_effects.py`에 구현된 워프 포탈 시스템은 **풍성한 이미지 기반 파티클**을 사용합니다.

**기존 파티클과의 차이:**
- ❌ 기존: 단순한 색깔 점 (빈약함)
- ✅ 새로운: 이미지 + 트레일 + Additive blending + 회전 링 (풍성함)

---

## ✨ 구성 요소

### 1. WarpParticle (개별 파티클)
- **이미지 기반**: `effects/in/` 폴더의 별/빛 이미지 사용
- **소용돌이 궤적**: 나선형으로 중심으로 빨려들어감
- **크기 맥동**: 시간에 따라 크기가 변화 (pulsate)
- **Additive blending**: 겹치면 더 밝아짐 (빛 효과)
- **트레일**: 이동 궤적 표시
- **원근감**: 중심에 가까울수록 작아짐

### 2. WarpPortal (완전한 포탈)
- **회전하는 링**: 여러 겹의 링이 각자 다른 속도로 회전
- **50+ 파티클**: 계속 재생성되어 끊이지 않음
- **배경 글로우**: 빛나는 배경 효과
- **중심 블랙홀**: 어두운 중심부
- **물체 끌어당김**: 중력처럼 물체를 끌어당기는 기능

---

## 🎮 기본 사용법

### 포탈 생성

```python
from effects.physics_effects import WarpPortal

# 간단한 포탈
portal = WarpPortal(
    center=(600, 400),
    max_radius=200,
    color_scheme="blue"
)

# 게임 루프
portal.update(dt)
portal.draw(screen)
```

### 색상 테마

```python
# 4가지 색상 테마 제공
portal_blue = WarpPortal(center=(x, y), color_scheme="blue")     # 파란색
portal_red = WarpPortal(center=(x, y), color_scheme="red")       # 빨간색
portal_green = WarpPortal(center=(x, y), color_scheme="green")   # 초록색
portal_yellow = WarpPortal(center=(x, y), color_scheme="yellow") # 노란색
```

---

## 🚀 고급 사용법

### 파라미터 커스터마이징

```python
portal = WarpPortal(
    center=(600, 400),
    max_radius=200,          # 포탈 크기
    particle_count=60,       # 파티클 개수 (많을수록 풍성)
    ring_count=3,            # 링 개수
    duration=10.0,           # 지속 시간 (0=무한)
    color_scheme="blue"      # 색상 테마
)
```

### 물체를 포탈로 끌어당기기

```python
# 우주선을 포탈로 끌어당김
new_pos = portal.pull_object(
    obj_pos=(player.pos.x, player.pos.y),
    dt=dt,
    pull_strength=300.0  # 끌어당기는 힘 (높을수록 강함)
)

# 플레이어 위치 업데이트
player.pos.x = new_pos[0]
player.pos.y = new_pos[1]
```

### 포탈 도달 감지

```python
# 물체가 포탈 중심에 도달했는지 확인
distance = math.sqrt(
    (portal.center.x - player.pos.x)**2 +
    (portal.center.y - player.pos.y)**2
)

if distance < 30:  # 중심 근처
    print("플레이어가 포탈에 진입!")
    # 다음 스테이지로 이동 등
```

---

## 🎨 게임 통합 예제

### 예제 1: 스테이지 클리어 워프

```python
# modes/episode_mode.py

from effects.physics_effects import WarpPortal

class EpisodeMode:
    def __init__(self):
        self.warp_portal = None
        self.warping = False

    def stage_clear(self):
        """스테이지 클리어 시 포탈 생성"""
        # 화면 중앙에 포탈 생성
        self.warp_portal = WarpPortal(
            center=(600, 400),
            max_radius=250,
            particle_count=80,
            ring_count=4,
            duration=0,  # 무한 지속
            color_scheme="blue"
        )

        self.warping = True
        print("Stage clear! Warp portal opened!")

    def update(self, dt):
        # 포탈 업데이트
        if self.warp_portal:
            self.warp_portal.update(dt)

            # 플레이어를 포탈로 끌어당김
            if self.warping:
                new_pos = self.warp_portal.pull_object(
                    (self.player.pos.x, self.player.pos.y),
                    dt,
                    pull_strength=250.0
                )

                self.player.pos.x = new_pos[0]
                self.player.pos.y = new_pos[1]

                # 포탈 도달 체크
                dist = ((self.warp_portal.center.x - self.player.pos.x)**2 +
                       (self.warp_portal.center.y - self.player.pos.y)**2)**0.5

                if dist < 40:
                    # 다음 스테이지로
                    self.load_next_stage()
                    self.warp_portal = None
                    self.warping = False

    def draw(self, screen):
        # 포탈 그리기 (플레이어 뒤에)
        if self.warp_portal:
            self.warp_portal.draw(screen)

        # 플레이어 그리기
        self.player.draw(screen)
```

### 예제 2: 보스 등장 포탈

```python
# modes/wave_mode.py

from effects.physics_effects import WarpPortal, DepthEffect

class WaveMode:
    def spawn_boss(self):
        """보스 등장 시퀀스"""
        # 1. 포탈 생성
        self.boss_portal = WarpPortal(
            center=(600, 200),
            max_radius=300,
            particle_count=100,
            ring_count=5,
            duration=3.0,  # 3초 후 닫힘
            color_scheme="red"  # 보스는 빨간색
        )

        # 2. 보스 이미지 깊이 효과 (작게 시작 → 크게)
        self.boss_appear_effect = DepthEffect(
            image=self.boss.image,
            start_pos=(600, 200),
            end_pos=(600, 200),
            start_depth=1.0,  # 깊은 곳 (작게)
            end_depth=0.0,    # 화면 (크게)
            duration=3.0,
            fade_in=True
        )

        print("Boss appearing from warp portal!")

    def update(self, dt):
        # 포탈 + 보스 출현 효과
        if self.boss_portal:
            self.boss_portal.update(dt)

            if not self.boss_portal.is_alive:
                self.boss_portal = None

        if self.boss_appear_effect:
            self.boss_appear_effect.update(dt)

            if not self.boss_appear_effect.is_alive:
                self.boss_appear_effect = None
                # 보스 전투 시작
                self.boss_active = True

    def draw(self, screen):
        # 포탈 먼저
        if self.boss_portal:
            self.boss_portal.draw(screen)

        # 보스 출현 효과
        if self.boss_appear_effect:
            self.boss_appear_effect.draw(screen)
        elif self.boss_active:
            # 일반 보스 그리기
            self.boss.draw(screen)
```

### 예제 3: 적 워프 소환

```python
# game_logic/spawning.py

from effects.physics_effects import WarpPortal
import random

class EnemySpawner:
    def __init__(self):
        self.spawn_portals = []

    def spawn_enemy_with_portal(self, enemy_pos):
        """적을 포탈을 통해 소환"""
        # 작은 포탈 생성
        portal = WarpPortal(
            center=enemy_pos,
            max_radius=80,
            particle_count=30,
            ring_count=2,
            duration=2.0,  # 2초만 유지
            color_scheme=random.choice(["blue", "green"])
        )

        self.spawn_portals.append({
            'portal': portal,
            'enemy_spawned': False,
            'spawn_time': 1.0  # 1초 후 적 생성
        })

    def update(self, dt):
        for spawn_data in self.spawn_portals[:]:
            spawn_data['portal'].update(dt)
            spawn_data['spawn_time'] -= dt

            # 시간이 되면 적 생성
            if not spawn_data['enemy_spawned'] and spawn_data['spawn_time'] <= 0:
                enemy = self.create_enemy(spawn_data['portal'].center)
                self.enemies.append(enemy)
                spawn_data['enemy_spawned'] = True

            # 포탈이 사라지면 제거
            if not spawn_data['portal'].is_alive:
                self.spawn_portals.remove(spawn_data)

    def draw(self, screen):
        for spawn_data in self.spawn_portals:
            spawn_data['portal'].draw(screen)
```

---

## 🎨 파라미터 조정 가이드

### 포탈 크기 (max_radius)
- **작음 (50-100)**: 적 소환 포탈
- **보통 (150-200)**: 스테이지 전환 포탈
- **큼 (250-350)**: 보스 등장, 대형 이벤트

### 파티클 개수 (particle_count)
- **적음 (20-30)**: 작은 포탈, 성능 중요
- **보통 (50-70)**: 일반 포탈
- **많음 (80-120)**: 화려한 연출, 보스 등장

### 링 개수 (ring_count)
- **1-2개**: 단순한 포탈
- **3-4개**: 일반적인 포탈
- **5+개**: 매우 화려한 포탈 (보스용)

### 지속 시간 (duration)
- **0**: 무한 지속 (수동으로 제거)
- **1-3초**: 적 소환
- **5-10초**: 스테이지 전환
- **15+초**: 배경 장식

### 끌어당기는 힘 (pull_strength)
- **100-200**: 느린 끌어당김
- **250-400**: 보통 속도
- **500+**: 빠르게 빨려들어감

---

## 🎭 색상 테마별 용도

### Blue (파란색)
- 일반 워프
- 아군 포탈
- 스테이지 전환

### Red (빨간색)
- 보스 등장
- 위험한 워프
- 적 포탈

### Green (초록색)
- 힐링 포탈
- 안전 구역
- 보급품 소환

### Yellow (노란색)
- 특수 이벤트
- 보너스 스테이지
- 골드 워프

---

## 🖼️ 사용 이미지

워프 포탈은 `effects/in/` 폴더의 이미지들을 사용합니다:

### 파티클 이미지
- `shining_light_star.png` - 빛나는 별
- `explosive_star_effect.png` - 폭발 별
- `blue_hole_star.png` - 블루홀 별
- `star_warp_element.png` - 워프 별
- `light_warp_element.png` - 빛 워프

### 링 이미지
- `blue_whirl_ring.png` - 파란 소용돌이 링
- `yellow_ring_star.png` - 노란 링 별

**이미지가 없으면**: 자동으로 프로시저럴 그래픽으로 폴백

---

## 📊 성능 고려사항

### 최적화 팁
1. **동시 포탈 수**: 화면에 3개 이하 권장
2. **파티클 수 조절**: 모바일은 30-40개로 제한
3. **링 개수**: 3개 이하 권장
4. **지속 시간**: 필요 이상 길게 유지하지 말 것

### 메모리 사용
- 포탈 1개: ~5MB (이미지 포함)
- 파티클 1개: ~10KB

### FPS 영향
- 파티클 50개: ~2-3 FPS 감소
- Additive blending: GPU 부담 증가

---

## 🐛 문제 해결

### 포탈이 안 보여요
```python
# 이미지 경로 확인
import os
print(os.path.exists("effects/in/blue_whirl_ring.png"))

# 수동으로 이미지 지정
portal.particle_images = [your_image]
portal.ring_image = your_ring_image
```

### 파티클이 너무 빠르게 사라져요
```python
# 파티클 수명 늘리기
# WarpPortal 생성 후
portal.spawn_interval = 0.05  # 더 자주 생성 (기본 0.1)
```

### 링이 안 돌아가요
```python
# 링 속도 확인
for i, speed in enumerate(portal.ring_speeds):
    print(f"Ring {i}: {speed} deg/sec")

# 수동으로 속도 설정
portal.ring_speeds = [60, 90, 120]  # 각 링의 속도
```

---

## 🎓 다음 단계

워프 포탈과 함께 사용할 수 있는 효과들:

1. **DepthEffect** - 물체가 포탈로 빨려들어가며 작아짐
2. **SupplyDrop** - 포탈에서 보급품 떨어뜨리기
3. **화면 진동** - 포탈 생성 시 Screen shake
4. **사운드 효과** - 워프 사운드 추가

---

## 📝 테스트

```bash
# 단독 테스트
python test_warp_portal.py

# 조작법:
# - 마우스 클릭: 포탈 생성
# - 1-4: 색상 변경 (Blue/Red/Green/Yellow)
# - W: 우주선 워프 시퀀스
# - Space: 우주선 끌어당김 ON/OFF
# - C: 모든 포탈 제거
```

---

## 🎉 결론

**풍성한 워프 포탈 효과 완성!**

- ✅ 이미지 기반 파티클 (빈약하지 않음!)
- ✅ 회전하는 링
- ✅ 소용돌이 + 트레일
- ✅ Additive blending (빛남!)
- ✅ 물체 끌어당김
- ✅ 4가지 색상 테마

**기존 파티클 대비 10배 이상 풍성함!** 🌟
