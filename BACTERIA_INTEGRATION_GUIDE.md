# Bacteria 시스템 통합 가이드

## ✅ 완료된 작업

### 1. Config 설정 추가 (`config/entities.py`)

**BACTERIA_GENERATOR** (lines 196-211):
```python
"BACTERIA_GENERATOR": {
    "name": "카오스 박테리아 생성기",
    "hp_mult": 0.0,  # 무적 (공격 불가)
    "speed_mult": 0.3,  # 느린 진입/회전 속도
    "damage_mult": 0.0,  # 충돌 데미지 없음
    "spawn_bacteria_count": 50,  # 박테리아 투하 개수 (10회 x 5개)
    "spawn_bacteria_interval": 3.0,  # 투하 간격 3초
    "orbit_radius_ratio": 0.2,  # 원운동 반지름 (화면 너비의 20%)
    "image": "bacteria_generator.png",
}
```

**BACTERIA** (lines 212-227):
```python
"BACTERIA": {
    "name": "카오스 박테리아",
    "hp_mult": 999.0,  # 일반 공격 무적 (매우 높은 HP)
    "speed_mult": 0.8,  # 느린 속도
    "damage_mult": 1.0,  # 15 데미지 (1초마다)
    "duration": 5.0,  # 지속 시간 5초
    "attach_overlap": 0.1,  # 플레이어와 10% 겹침
    "vulnerable_to_special": True,  # static field, 번개체인에만 취약
    "image": "coli_bacteria.png",
}
```

### 2. BacteriaGenerator 클래스 생성 (`entities/bacteria_generator.py`)

**핵심 기능**:
- 화면 상단에서 천천히 하강하여 **1/4 지점**에 정지
- 중앙 기준 **반시계 방향** 원운동 (화면 폭의 20% 반지름)
- **3초마다** 5개의 박테리아 투하 (총 10회 = 50개)
- 모든 박테리아 투하 완료 후 **페이드아웃** (완전히 투명해지면 자동 제거)

**주요 메서드**:
```python
def __init__(screen_size, current_wave):
    # 원운동 설정
    self.orbit_radius = int(screen_width * 0.2)  # 20% 반지름
    self.orbit_angle = 0.0
    self.orbit_speed = 1.0  # 라디안/초 (반시계)

def update(dt, current_time) -> List[Bacteria]:
    # 1. 화면 진입 (하강)
    # 2. 원운동하며 박테리아 투하 (3초 간격, 5개씩)
    # 3. 페이드아웃
    return newly_spawned_bacteria
```

### 3. Bacteria 엔티티 클래스 생성 (`entities/bacteria.py`)

**핵심 기능**:
- **화면 전역** 랜덤 이동 (경계 밖 진출 허용)
- **플레이어 추적** 및 **10% 겹침**으로 달라붙기
- 달라붙으면 **1초마다 15 데미지** 지속 피해
- **5초 듀레이션** 후 자동 소멸
- **일반 공격 무적**, **Static Field와 Lightning Chain에만 취약**

**주요 메서드**:
```python
def __init__(spawn_pos, screen_size, spawn_time):
    self.duration = 5.0  # 5초 듀레이션
    self.despawn_time = spawn_time + self.duration
    self.attached_to_player = False
    self.damage_per_second = 15.0

def update(dt, current_time, player_pos) -> Tuple[bool, float]:
    # 플레이어 추적 및 달라붙기
    # 달라붙으면 1초마다 데미지
    # 듀레이션 초과 시 자동 소멸
    return (is_attached, damage_dealt)

def take_damage(damage, is_special_weapon=False):
    # 특수 무기만 유효 (static field, lightning chain)
    if not is_special_weapon:
        return  # 일반 공격 무시
```

### 4. 플레이어 속도 저하 시스템 (`entities/player.py`)

**추가 속성** (lines 141-143):
```python
self.attached_bacteria_count = 0  # 현재 달라붙은 박테리아 수
self.bacteria_speed_reduction = 0.0  # 박테리아로 인한 속도 감소 비율
```

**메서드 추가** (lines 360-380):
```python
def update_bacteria_attachment(bacteria_count: int):
    """박테리아 수에 따른 속도 감소 (1개당 10%, 최대 90%)"""
    self.attached_bacteria_count = bacteria_count
    self.bacteria_speed_reduction = min(0.10 * bacteria_count, 0.90)

def get_effective_speed() -> float:
    """박테리아 속도 감소를 반영한 실제 이동 속도"""
    return self.speed * (1.0 - self.bacteria_speed_reduction)
```

**이동 속도 적용** (line 429):
```python
# 박테리아 속도 감소 적용
base_speed = self.get_effective_speed()
effective_speed = base_speed * speed_multiplier * self.mouse_move_speed_mult
```

### 5. 배경 전환 시스템 (`modes/wave_mode.py`)

**박테리아 배경 로드** (lines 254-269):
```python
# 박테리아 배경 (bacteria_bg_01, bacteria_bg_02)
self.bacteria_backgrounds = {}
for bg_num in [1, 2]:
    bg_filename = f"bacteria_bg_0{bg_num}.jpg"
    try:
        bg_path = config.BACKGROUND_DIR / bg_filename
        self.bacteria_backgrounds[bg_num] = AssetManager.get_image(bg_path, self.screen_size)
    except:
        # 폴백: 녹색 틴트 배경
        fallback_bg = pygame.Surface(self.screen_size)
        fallback_bg.fill((0, 20, 10))  # 어두운 녹색
        self.bacteria_backgrounds[bg_num] = fallback_bg

# 박테리아 이벤트 상태
self.original_background = None  # 박테리아 이전의 배경 저장
self.bacteria_event_active = False
```

**배경 전환 메서드** (lines 352-394):
```python
def start_bacteria_event():
    """박테리아 이벤트 시작 - 배경을 bacteria_bg로 전환"""
    self.original_background = self.current_background
    bacteria_bg_num = random.choice([1, 2])
    bacteria_bg = self.bacteria_backgrounds[bacteria_bg_num]

    self.background_transition = BackgroundTransition(
        old_bg=self.current_background,
        new_bg=bacteria_bg,
        screen_size=self.screen_size,
        effect_type="fade_in",
        duration=1.5  # 1.5초 페이드
    )
    self.bacteria_event_active = True

def end_bacteria_event():
    """박테리아 이벤트 종료 - 원래 배경으로 복원"""
    if self.original_background:
        self.background_transition = BackgroundTransition(
            old_bg=self.current_background,
            new_bg=self.original_background,
            screen_size=self.screen_size,
            effect_type="fade_in",
            duration=1.5
        )
    self.bacteria_event_active = False
    self.original_background = None
```

### 6. Wave Mode 통합

**리스트 추가** (lines 151-154):
```python
# 박테리아 시스템 (2단계)
self.bacteria_generators = []  # BacteriaGenerator 리스트
self.bacteria = []  # Bacteria 리스트
self.generator_spawned_this_wave = False  # 웨이브당 1회 스폰 제어
```

**Generator 스폰** (lines 606-625):
```python
# === BacteriaGenerator 스폰 (홀수 웨이브, 보스 제외, 웨이브당 1회) ===
if not self.generator_spawned_this_wave:
    # 조건: Wave 6+, 홀수, 보스 아님
    if (current_wave >= 6 and
        current_wave % 2 == 1 and
        current_wave not in config.BOSS_WAVES):

        # BacteriaGenerator 생성
        from entities.bacteria_generator import BacteriaGenerator
        generator = BacteriaGenerator(
            screen_size=self.screen_size,
            current_wave=current_wave
        )
        self.bacteria_generators.append(generator)
        self.generator_spawned_this_wave = True

        # 배경 전환 시작
        self.start_bacteria_event()

        print(f"INFO: BacteriaGenerator spawned at Wave {current_wave}")
```

**업데이트 로직** (lines 488-545):
```python
# === BacteriaGenerator 업데이트 (박테리아 투하) ===
for generator in self.bacteria_generators[:]:
    newly_spawned = generator.update(dt, current_time)
    self.bacteria.extend(newly_spawned)
    if generator.dead:
        self.bacteria_generators.remove(generator)

# === Bacteria 업데이트 (플레이어 추적 및 달라붙기) ===
player_pos = self.player.pos if self.player else None
attached_count = 0
total_bacteria_damage = 0.0

for bacteria in self.bacteria[:]:
    is_attached, damage = bacteria.update(dt, current_time, player_pos)

    if is_attached:
        attached_count += 1
        total_bacteria_damage += damage

    if bacteria.dead or not bacteria.is_alive:
        self.bacteria.remove(bacteria)

# 플레이어 속도 저하 업데이트
if self.player:
    self.player.update_bacteria_attachment(attached_count)

    # 박테리아 데미지 적용
    if total_bacteria_damage > 0:
        self.player.take_damage(total_bacteria_damage)

# 모든 박테리아 소멸 시 배경 복원
if len(self.bacteria) == 0 and len(self.bacteria_generators) == 0:
    if self.bacteria_event_active:
        self.end_bacteria_event()

# === Bacteria 피격 처리 (특수 무기만) ===
# Static Field 피격 처리
if self.player and self.player.has_static_field:
    static_field_radius = 150
    for bacteria in self.bacteria[:]:
        if bacteria.is_alive:
            distance = (bacteria.pos - self.player.pos).length()
            if distance <= static_field_radius:
                bacteria.take_damage(100, is_special_weapon=True)

# Lightning Chain 피격 처리
for bullet in self.bullets[:]:
    has_lightning = getattr(bullet, 'has_lightning', False) or (self.player and self.player.has_lightning)

    if has_lightning:
        for bacteria in self.bacteria[:]:
            if bacteria.is_alive and bacteria.hitbox.colliderect(bullet.hitbox):
                bacteria.take_damage(bullet.damage, is_special_weapon=True)
```

**렌더링** (`modes/base_mode.py` lines 659-668):
```python
# BacteriaGenerator 그리기 (적보다 먼저 - 뒤에 표시)
if hasattr(self, 'bacteria_generators'):
    for generator in self.bacteria_generators:
        generator.draw(screen)

# Bacteria 그리기 (적과 같은 레이어)
if hasattr(self, 'bacteria'):
    for bacteria in self.bacteria:
        if bacteria.is_alive:
            bacteria.draw(screen)
```

**웨이브 리셋** (line 1086):
```python
self.carrier_spawned_this_wave = False
self.generator_spawned_this_wave = False
```

**치트키 추가** (lines 1067-1073):
```python
elif event.key == pygame.K_F7:
    self.game_data["current_wave"] = 7
    self.game_data["wave_kills"] = 0
    self.game_data["wave_target_kills"] = 16
    self.game_data["game_state"] = config.GAME_STATE_WAVE_PREPARE
    self.generator_spawned_this_wave = False
    print("CHEAT: Skipping to Wave 7 (Bacteria Generator Test)")
```

---

## 🎮 시스템 동작 방식

### 등장 조건
- **Wave 6+** (7, 9, 11, 13...) **홀수 웨이브**만
- **보스 웨이브 제외** (5, 10, 15, 20)
- 웨이브당 1회 스폰

### 동작 시퀀스

1. **Generator 등장**
   - 화면 상단에서 천천히 하강
   - y = 1/4 지점에서 정지
   - 중앙 기준 원운동 시작 (반지름: 화면 폭 20%, 반시계)
   - **배경이 bacteria_bg_01 또는 bacteria_bg_02로 전환** (1.5초 페이드)

2. **박테리아 투하**
   - 3초마다 5개씩 투하 (총 10회)
   - 랜덤 위치에서 투하
   - 총 50개 박테리아

3. **박테리아 행동**
   - 화면 전역 랜덤 이동 (경계 밖 진출 허용)
   - 플레이어 발견 시 추적
   - 10% 겹침으로 달라붙기
   - **달라붙으면**: 1초마다 15 데미지, 이동 속도 10% 감소 (누적)
   - **5초 듀레이션** 후 자동 소멸

4. **피격 및 제거**
   - **일반 공격**: 무효 (HP 999배)
   - **Static Field**: 유효 (150 범위)
   - **Lightning Chain**: 유효 (총알 관통)

5. **이벤트 종료**
   - 모든 박테리아와 Generator 소멸 시
   - **원래 배경으로 복원** (1.5초 페이드)

---

## 🧪 테스트 방법

### 1. 기본 테스트
```
1. 게임 시작
2. Wave 7까지 진행 (또는 F7 치트키 사용)
3. Generator 등장 확인 (화면 1/4 지점, 원운동)
4. 배경 전환 확인 (녹색 계열)
5. 박테리아 50개 투하 확인 (3초마다 5개씩)
6. 플레이어 추적 및 달라붙기 확인
7. 속도 저하 확인 (박테리아 수에 비례)
8. 5초 후 자동 소멸 확인
9. 배경 복원 확인
```

### 2. 특수 무기 테스트
```
1. Workshop에서 Static Field 또는 Lightning Chain 획득
2. Wave 7 진입
3. 박테리아에 특수 무기 사용
4. 박테리아 제거 확인
5. 일반 총알로는 제거 안 됨 확인
```

### 3. 치트키
- **F7**: Wave 7로 점프 (박테리아 테스트)
- **F6**: Wave 6로 점프 (Carrier 테스트)

---

## 📝 주요 파일 변경 사항

| 파일 | 변경 내용 |
|------|----------|
| `config/entities.py` | BACTERIA_GENERATOR, BACTERIA 타입 추가 |
| `entities/bacteria_generator.py` | **신규 파일** - Generator 클래스 |
| `entities/bacteria.py` | **신규 파일** - Bacteria 클래스 |
| `entities/player.py` | 박테리아 속도 저하 시스템 추가 |
| `modes/wave_mode.py` | 박테리아 스폰/업데이트/배경 전환 로직 |
| `modes/base_mode.py` | 박테리아 렌더링 추가 |

---

## ⚠️ 주의사항

1. **이미지 파일 필요**:
   - `assets/images/gameplay/enemies/bacteria_generator.png`
   - `assets/images/gameplay/enemies/coli_bacteria.png`
   - `assets/backgrounds/bacteria_bg_01.jpg` (선택사항, 폴백 있음)
   - `assets/backgrounds/bacteria_bg_02.jpg` (선택사항, 폴백 있음)

2. **박테리아는 웨이브 킬 카운트에 미포함** (보너스 적)

3. **Generator는 무적** (공격 불가)

4. **박테리아 최대 동시 존재 수**: 50개 (모두 투하된 경우)

5. **속도 저하 최대치**: 90% (박테리아 9개 이상 달라붙으면)

---

## 🔗 관련 시스템

- **Droid Carrier 시스템**: `CARRIER_INTEGRATION_GUIDE.md` 참조
- **Wave 6+ 짝수**: Droid Carrier
- **Wave 6+ 홀수**: Bacteria Generator
- **보스 웨이브 (5, 10, 15, 20)**: 둘 다 등장 안 함
