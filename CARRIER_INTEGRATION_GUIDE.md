# Droid Carrier 통합 가이드 (1단계)

## ✅ 완료된 작업

1. **이미지 파일 이동**
   - `chaos_droid_carrier.png` → `assets/images/gameplay/enemies/`
   - `coli_bacteria.png` → `assets/images/gameplay/enemies/`

2. **적 타입 추가** (`config/entities.py:167-195`)
   - `DROID_CARRIER`: 캐리어 적 (드로이드 투하)
   - `SPHERE_DROID`: 스피어 드로이드 (캐리어가 투하)

3. **DroidCarrier 클래스** (`entities/droid_carrier.py`)
   - 화면 상단 진입 → 좌우 이동 → 드로이드 10개 순차 투하 (2초 간격) → 퇴장
   - 피격 시 HP 젬 드롭 (1회)

4. **SpawnSystem에 carrier 로직 추가** (`systems/spawn_system.py`)
   - `try_spawn_carrier()`: 짝수 웨이브에 캐리어 스폰
   - `update_carriers()`: 캐리어 업데이트 및 드로이드 투하
   - `check_carrier_hit()`: 캐리어 피격 처리

## 🔧 남은 작업: Wave Mode 통합

`modes/wave_mode.py`에 다음 코드를 추가해야 합니다.

### 1. __init__ 메서드에 carrier 리스트 추가

```python
def __init__(self, screen_size, game_data, sound_manager):
    # ... 기존 코드 ...

    # Carrier 리스트 추가
    self.carriers = []  # DroidCarrier 리스트
    self.carrier_spawned_this_wave = False  # 웨이브당 1회 스폰 제어
```

### 2. _update_running 메서드에 carrier 업데이트 추가

```python
def _update_running(self, dt: float, current_time: float):
    # ... 기존 코드 (플레이어 업데이트 등) ...

    # === Carrier 업데이트 (드로이드 투하) ===
    for carrier in self.carriers[:]:  # 복사본으로 순회
        newly_spawned = carrier.update(dt, current_time)
        self.enemies.extend(newly_spawned)  # 투하된 드로이드 추가

        # 죽은 캐리어 제거
        if carrier.dead:
            self.carriers.remove(carrier)

    # ... 기존 코드 (게임 객체 충돌 등) ...
```

### 3. _update_running 메서드에 carrier 스폰 추가

```python
# 웨이브 페이즈에 따른 처리
wave_phase = self.game_data.get('wave_phase', 'normal')

if wave_phase == 'normal':
    # === Carrier 스폰 (짝수 웨이브, 보스 제외, 웨이브당 1회) ===
    current_wave = self.game_data.get('current_wave', 1)
    if not self.carrier_spawned_this_wave:
        # 조건 체크: Wave 6+, 짝수, 보스 아님
        if (current_wave >= 6 and
            current_wave % 2 == 0 and
            current_wave not in config.BOSS_WAVES):

            # Carrier 생성
            from entities.droid_carrier import DroidCarrier
            carrier = DroidCarrier(
                screen_size=self.screen_size,
                current_wave=current_wave
            )
            self.carriers.append(carrier)
            self.carrier_spawned_this_wave = True
            print(f"INFO: Carrier spawned at Wave {current_wave}")

    # ... 기존 코드 (적 스폰 등) ...
```

### 4. start_wave에서 carrier_spawned_this_wave 리셋

```python
# 웨이브 시작 시 (어디선가 start_wave를 호출하는 곳에)
self.carrier_spawned_this_wave = False  # 새 웨이브 시작 시 리셋
```

### 5. 플레이어 총알과 Carrier 충돌 처리

```python
# 플레이어 총알 업데이트 부분에 추가
for bullet in self.bullets[:]:
    # 기존 적과의 충돌 처리...

    # === Carrier와의 충돌 처리 ===
    for carrier in self.carriers:
        if carrier.hitbox.colliderect(bullet.rect):
            # 피격 처리
            should_drop_gem = carrier.take_damage(bullet.damage)

            # HP 젬 드롭
            if should_drop_gem:
                from entities.collectibles import HealItem
                heal_item = HealItem(
                    pos=pygame.math.Vector2(carrier.pos.x, carrier.pos.y),
                    heal_amount=1
                )
                self.gems.append(heal_item)
                print("INFO: HP gem dropped from carrier!")

            # 총알 제거
            if bullet in self.bullets:
                self.bullets.remove(bullet)
            break
```

### 6. Carrier 렌더링

```python
def _draw_game_objects(self, screen):
    # ... 기존 렌더링 ...

    # === Carrier 렌더링 ===
    for carrier in self.carriers:
        carrier.draw(screen)

    # ... 적, 플레이어 렌더링 ...
```

## 🎮 동작 방식

1. **Wave 6, 8, 10, 12...** (짝수, 보스 제외)
2. 웨이브 시작 직후 Carrier 1개 등장
3. 화면 상단에서 진입 → 좌우 이동
4. 2초마다 드로이드 1개씩 투하 (총 10개)
5. 드로이드는 일반 적처럼 행동 (웨이브 킬 카운트 미포함)
6. Carrier 피격 시 HP 젬 1개 드롭 (1회만)
7. 모든 드로이드 투하 후 위로 퇴장

## 🧪 테스트 방법

1. 게임 시작 → Wave 6 도달
2. 화면 상단에 Carrier 등장 확인
3. Carrier 공격 → HP 젬 드롭 확인
4. 드로이드 10개 투하 확인
5. Carrier 퇴장 확인

## 📝 주의사항

- 드로이드는 **웨이브 킬 카운트에 미포함** (보너스 적)
- Carrier 피격 HP 젬은 **1회만** 드롭
- 보스 웨이브(5, 10, 15, 20)에서는 등장 안함
