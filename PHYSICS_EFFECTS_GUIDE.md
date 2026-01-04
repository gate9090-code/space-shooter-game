# 물리 기반 효과 시스템 가이드

## 🎯 개요

`effects/physics_effects.py`에는 중력, 충돌, 바운스 등 물리 시뮬레이션을 포함한 효과들이 구현되어 있습니다.

---

## 📦 1. 보급품 투하 (SupplyDrop)

### 특징
- ✅ 중력 시뮬레이션
- ✅ 지면 충돌 감지
- ✅ 바운스 효과 (최대 3회)
- ✅ 회전 애니메이션
- ✅ 그림자 효과
- ✅ 착지 시 먼지 파티클

### 기본 사용법

```python
from effects.physics_effects import SupplyDrop

# 간단한 수직 낙하
supply = SupplyDrop(
    start_pos=(400, 50),      # 시작 위치
    image_path="bullet_storage.png",
    ground_y=700              # 지면 높이
)

# 게임 루프
supply.update(dt)
supply.draw(screen)
```

### 포물선 투하 (목표 지점 지정)

```python
# 특정 위치로 떨어지도록
supply = SupplyDrop(
    start_pos=(200, 50),
    target_pos=(600, 700),    # 목표 위치
    ground_y=700
)
```

### 파라미터 커스터마이징

```python
supply = SupplyDrop(
    start_pos=(x, y),
    target_pos=(target_x, target_y),
    image_path="bullet_storage.png",

    # 물리 파라미터
    gravity=800.0,           # 중력 (기본 800)
    bounce_factor=0.6,       # 바운스 강도 (0~1, 기본 0.6)
    friction=0.95,           # 마찰 계수 (0~1, 기본 0.95)
    rotation_speed=180.0,    # 회전 속도 (도/초)

    # 외형
    size=64.0,               # 크기
    ground_y=700             # 지면 높이
)
```

### 상태 확인

```python
if supply.is_grounded:
    print("보급품이 착지했습니다!")
    # 플레이어가 획득 가능

if not supply.is_alive:
    print("보급품이 사라졌습니다")
    # 리스트에서 제거
```

---

## 🌊 2. 깊이감 효과 (DepthEffect)

### 특징
- ✅ Z축 이동 시뮬레이션 (원근감)
- ✅ Scale 변화로 깊이 표현
- ✅ 페이드 인/아웃
- ✅ 부드러운 ease-in-out

### 사용 예시: 워프 진입

```python
from effects.physics_effects import DepthEffect

# 우주선이 화면 안쪽으로 빨려들어감
ship_image = player.get_current_image()

warp_effect = DepthEffect(
    image=ship_image,
    start_pos=(player.pos.x, player.pos.y),
    end_pos=(600, 400),       # 포탈 중심
    start_depth=0.0,          # 화면 (크게)
    end_depth=1.0,            # 깊은 곳 (작게)
    duration=1.5,             # 1.5초 동안
    fade_out=True             # 끝에서 사라짐
)

# 게임 루프
warp_effect.update(dt)
warp_effect.draw(screen)
```

### 사용 예시: 적 출현

```python
# 적이 화면 깊은 곳에서 등장
enemy_appear = DepthEffect(
    image=enemy_image,
    start_pos=(400, 300),
    end_pos=(400, 300),       # 같은 위치 (크기만 변화)
    start_depth=1.0,          # 깊은 곳 (작게)
    end_depth=0.0,            # 화면 (크게)
    duration=1.0,
    fade_in=True              # 시작에서 페이드 인
)
```

---

## 🎮 게임 통합 예제

### Wave Mode에서 보급품 투하

```python
# modes/wave_mode.py

from effects.physics_effects import SupplyDrop

class WaveMode:
    def __init__(self):
        self.supply_drops = []

    def spawn_supply_drop(self, target_pos):
        """보급품 투하"""
        # 화면 위 랜덤 위치에서 시작
        start_x = target_pos[0] + random.randint(-50, 50)

        supply = SupplyDrop(
            start_pos=(start_x, -50),
            target_pos=target_pos,
            image_path="bullet_storage.png",
            ground_y=self.screen_height - 50
        )

        self.supply_drops.append(supply)

    def update(self, dt):
        # 보급품 업데이트
        for supply in self.supply_drops[:]:
            supply.update(dt)

            # 사라진 것 제거
            if not supply.is_alive:
                self.supply_drops.remove(supply)
                continue

            # 플레이어와 충돌 체크 (착지한 것만)
            if supply.is_grounded:
                if self.check_collision(self.player, supply):
                    self.collect_supply(supply)
                    self.supply_drops.remove(supply)

    def draw(self, screen):
        # 보급품 그리기
        for supply in self.supply_drops:
            supply.draw(screen)

    def collect_supply(self, supply):
        """보급품 획득"""
        # 탄약 보충, 체력 회복 등
        self.player.ammo += 50
        print("보급품 획득! 탄약 +50")
```

### Episode Mode에서 워프 효과

```python
# modes/episode_mode.py

from effects.physics_effects import DepthEffect

class EpisodeMode:
    def __init__(self):
        self.depth_effects = []

    def warp_to_next_stage(self):
        """다음 스테이지로 워프"""
        # 플레이어 워프 효과
        warp = DepthEffect(
            image=self.player.get_current_image(),
            start_pos=(self.player.pos.x, self.player.pos.y),
            end_pos=(600, 400),
            start_depth=0.0,
            end_depth=1.0,
            duration=2.0,
            fade_out=True
        )
        self.depth_effects.append(warp)

        # 2초 후 실제 스테이지 전환
        self.warp_timer = 2.0

    def update(self, dt):
        # 깊이 효과 업데이트
        for effect in self.depth_effects[:]:
            effect.update(dt)
            if not effect.is_alive:
                self.depth_effects.remove(effect)

    def draw(self, screen):
        for effect in self.depth_effects:
            effect.draw(screen)
```

---

## 🔧 파라미터 조정 가이드

### 중력 (gravity)
- **낮음 (200-400)**: 천천히 떨어짐, 달 중력 느낌
- **보통 (600-800)**: 자연스러운 낙하
- **높음 (1000-1500)**: 빠르게 떨어짐, 긴장감

### 바운스 계수 (bounce_factor)
- **0.0**: 바운스 없음, 즉시 정지
- **0.3-0.5**: 작은 바운스
- **0.6-0.8**: 보통 바운스 (권장)
- **0.9-1.0**: 계속 튕김 (거의 멈추지 않음)

### 마찰 (friction)
- **0.7-0.8**: 빠른 감속
- **0.9-0.95**: 자연스러운 감속 (권장)
- **0.98-1.0**: 거의 감속 안 함

### 회전 속도 (rotation_speed)
- **0**: 회전 없음
- **90-180**: 느린 회전
- **360-720**: 빠른 회전

---

## 🎨 커스터마이징 예제

### 1. 느리게 떨어지는 깃털 효과

```python
feather = SupplyDrop(
    start_pos=(x, y),
    gravity=100,              # 매우 낮은 중력
    bounce_factor=0.3,        # 작은 바운스
    rotation_speed=360,       # 회전
    size=32
)
```

### 2. 빠르게 떨어지는 운석

```python
meteor = SupplyDrop(
    start_pos=(x, y),
    gravity=1500,             # 높은 중력
    bounce_factor=0.1,        # 거의 튕기지 않음
    rotation_speed=720,       # 빠른 회전
    size=80
)
```

### 3. 공처럼 튕기는 효과

```python
bouncy_ball = SupplyDrop(
    start_pos=(x, y),
    gravity=800,
    bounce_factor=0.9,        # 높은 반발
    friction=0.98,            # 낮은 마찰
    rotation_speed=0          # 회전 없음
)
```

---

## 📊 성능 고려사항

### 최적화 팁
1. **동시 보급품 수 제한**: 화면에 10개 이하 권장
2. **파티클 수 조절**: 바운스당 파티클 10-20개
3. **오래된 보급품 제거**: `lifetime` 설정으로 자동 제거
4. **충돌 체크 최적화**: 착지한 것만 체크

### 메모리 사용
- 보급품 1개: ~100KB (이미지 + 파티클)
- 파티클 1개: ~100 bytes

---

## 🐛 문제 해결

### 보급품이 안 보여요
```python
# 이미지 경로 확인
supply = SupplyDrop(
    start_pos=(400, 50),
    image_path="assets/images/gameplay/bullet_storage.png",  # 전체 경로
    ground_y=700
)
```

### 바운스가 너무 많아요
```python
# max_bounces 직접 설정
supply.max_bounces = 1  # 한 번만 튕김
```

### 파티클이 너무 많아요
```python
# _create_impact_particles 메서드 수정
# particle_count = int(10 * ...) → int(5 * ...)
```

---

## 🎓 다음 단계

구현 가능한 추가 효과들:

1. **폭발 파편 시스템** - 사방으로 튕겨나가는 파편
2. **탄피 배출** - 총알 발사 시 회전하며 떨어지는 탄피
3. **모션 트레일** - 고속 이동 시 잔상
4. **워프 포탈** - 소용돌이 + 깊이감 조합

어떤 효과를 다음에 구현하고 싶으신가요?

---

## 📝 테스트

```bash
# 단독 테스트
python effects/physics_effects.py

# 조작법:
# - 마우스 클릭: 클릭한 위치에 보급품 투하
# - Space: 랜덤 위치에 투하
# - C: 모든 보급품 제거
```

---

**즐거운 개발 되세요!** 🚀
