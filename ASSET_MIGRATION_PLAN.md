# 📦 Assets 폴더 재구조화 계획

**작성일**: 2026-01-02
**목표**: 혼란스러운 assets 폴더 구조를 에피소드 중심으로 명확하게 재구성

---

## 🎯 문제점 분석

### 현재 구조의 혼란
```
assets/
├── data/episodes/        # 76 MB - 에피소드 시스템
│   └── ep1/
│       ├── cutscene_images/
│       ├── portraits/
│       ├── backgrounds/
│       └── audio/
├── story_mode/           # 29 MB - 레거시 스토리 폴더
│   ├── backgrounds/      # 14 MB - ep1/backgrounds와 중복?
│   ├── sounds/           # 8.1 MB
│   ├── reflection/       # 7.5 MB - 회상 컷씬용 배경
│   ├── scripts/          # 28 KB - JSON 스크립트
│   ├── enemies/          # 비어있음
│   ├── skills/           # 비어있음
│   └── ui/               # 비어있음
├── siege_mode/           # 39 MB - 공성 모드 전용?
│   ├── backgrounds/      # 2.6 MB
│   ├── enemies/          # 11 MB
│   ├── tiles/            # 26 MB
│   └── sounds/           # 비어있음
├── wave_mode/            # 0 MB - 빈 폴더
├── images/               # 249 MB - 공용 리소스?
├── sounds/               # 16 MB - 공용 사운드?
├── videos/               # 41 MB
└── fonts/                # 4.5 MB
```

### 혼란 요소
1. **중복 폴더명**: `story_mode/`, `data/episodes/ep1/`, `siege_mode/` - 모두 모드별 리소스인데 계층이 불명확
2. **빈 폴더들**: `story_mode/enemies/`, `story_mode/skills/`, `story_mode/ui/`, `wave_mode/`, `siege_mode/sounds/`
3. **애매한 위치**: `images/`는 공용인지 특정 모드용인지 불명확
4. **레거시 경로 혼재**: 코드에서 `story_mode/backgrounds/`와 `ep1/backgrounds/` 둘 다 참조

---

## ✅ 목표 구조 (에피소드 중심)

```
assets/
├── data/
│   └── episodes/              # 에피소드별 스토리 리소스
│       ├── ep1/               # Episode 1: "폐허의 귀환"
│       │   ├── ep1.json
│       │   ├── backgrounds/   # 스토리 배경 (14MB from story_mode)
│       │   ├── cutscene_images/  # 컷씬 이미지 (38MB)
│       │   ├── portraits/     # 캐릭터 초상화 (12MB)
│       │   ├── audio/
│       │   │   ├── bgm/       # 배경음악 (from story_mode/sounds)
│       │   │   └── sfx/       # 효과음
│       │   └── scripts/       # 대화 스크립트 (28KB from story_mode/scripts)
│       ├── ep2/               # Episode 2 (미래 확장)
│       ├── ep3/
│       ├── ep4/
│       ├── ep5/
│       └── shared/            # 에피소드 간 공용 리소스
│           ├── portraits/
│           ├── audio/
│           └── backgrounds/
├── modes/
│   └── siege/                 # 공성 모드 전용 리소스
│       ├── backgrounds/       # 2.6MB
│       ├── enemies/           # 11MB
│       └── tiles/             # 26MB
├── images/                    # 게임 공통 리소스 (249MB)
│   ├── characters/
│   ├── effects/
│   ├── items/
│   ├── projectiles/
│   ├── skills/
│   ├── ui/
│   └── backgrounds/           # 웨이브 모드 공용 배경
├── sounds/                    # 공통 사운드 (16MB)
├── videos/                    # 동영상 (41MB)
└── fonts/                     # 폰트 (4.5MB)
```

### 핵심 개선점
1. **모드별 명확한 분리**: `data/episodes/` (스토리), `modes/siege/` (공성), `images/` (공통)
2. **빈 폴더 제거**: 불필요한 빈 폴더 모두 삭제
3. **레거시 통합**: `story_mode/` 내용을 `episodes/ep1/`로 완전 이관
4. **reflection 처리**: 회상 컷씬 배경을 `ep1/backgrounds/reflection/` 하위로 이동

---

## 📋 단계별 실행 계획

### ✅ Checkpoint 1: 폴더 구조 분석 완료 (현재 단계)
**상태**: ✅ 완료

---

### 🔄 Checkpoint 2: story_mode 마이그레이션

#### 2.1 backgrounds 이동
```bash
# story_mode/backgrounds/ (14MB) → ep1/backgrounds/
복사 대상: bg_bunker.jpg, bg_ruins.jpg, bg_lab_fire.jpg 등
목적지: assets/data/episodes/ep1/backgrounds/
```

**작업 순서**:
1. `ep1/backgrounds/` 폴더 확인 (이미 존재)
2. `story_mode/backgrounds/*.jpg` → `ep1/backgrounds/` 복사
3. 중복 파일 확인 (덮어쓸지 확인)

#### 2.2 reflection 이동
```bash
# story_mode/reflection/backgrounds/ (7.5MB) → ep1/backgrounds/reflection/
복사 대상: bg_andromeda_city.jpg, bg_autumn_rain.jpg 등
목적지: assets/data/episodes/ep1/backgrounds/reflection/
```

**작업 순서**:
1. `ep1/backgrounds/reflection/` 폴더 생성
2. `story_mode/reflection/backgrounds/*.jpg` 이동
3. `story_mode/reflection/ASSET_REQUIREMENTS.txt` 확인 후 이동 또는 삭제

#### 2.3 sounds 이동
```bash
# story_mode/sounds/ (8.1MB) → ep1/audio/bgm/ or ep1/audio/sfx/
복사 대상: 모든 사운드 파일
목적지: assets/data/episodes/ep1/audio/
```

**작업 순서**:
1. `ep1/audio/bgm/`, `ep1/audio/sfx/` 폴더 확인/생성
2. `story_mode/sounds/` 파일 분류 (BGM vs SFX)
3. 적절한 폴더로 이동

#### 2.4 scripts 이동
```bash
# story_mode/scripts/ (28KB) → ep1/scripts/
복사 대상: act1_opening.json, act2_opening.json 등
목적지: assets/data/episodes/ep1/scripts/
```

**작업 순서**:
1. `ep1/scripts/` 폴더 생성
2. `story_mode/scripts/*.json` 이동

#### 2.5 빈 폴더 삭제
```bash
삭제 대상:
- story_mode/enemies/
- story_mode/skills/
- story_mode/ui/
```

**🛑 체크포인트 확인**:
- [ ] ep1/backgrounds/ 에 모든 배경 이미지 존재
- [ ] ep1/backgrounds/reflection/ 에 회상 배경 존재
- [ ] ep1/audio/ 에 사운드 파일 존재
- [ ] ep1/scripts/ 에 JSON 스크립트 존재
- [ ] story_mode/ 빈 폴더 제거됨

---

### 🔄 Checkpoint 3: siege_mode 마이그레이션

#### 3.1 폴더명 변경
```bash
# siege_mode/ (39MB) → modes/siege/
이동 대상: 전체 폴더
목적지: assets/modes/siege/
```

**작업 순서**:
1. `assets/modes/` 폴더 생성
2. `assets/siege_mode/` → `assets/modes/siege/` 이름 변경
3. 빈 폴더 (`siege_mode/sounds/`) 삭제

**🛑 체크포인트 확인**:
- [ ] modes/siege/backgrounds/ 존재 (2.6MB)
- [ ] modes/siege/enemies/ 존재 (11MB)
- [ ] modes/siege/tiles/ 존재 (26MB)
- [ ] siege_mode/ 폴더 제거됨

---

### 🔄 Checkpoint 4: 빈 폴더 정리

#### 4.1 wave_mode 삭제
```bash
삭제 대상: assets/wave_mode/ (빈 폴더)
```

#### 4.2 기타 빈 폴더 확인
```bash
체크 대상:
- story_mode/ 하위 빈 폴더
- siege_mode/sounds/ (이미 마이그레이션 시 삭제 예정)
```

**🛑 체크포인트 확인**:
- [ ] wave_mode/ 삭제됨
- [ ] 모든 빈 폴더 제거됨

---

### 🔄 Checkpoint 5: 코드 경로 업데이트

#### 5.1 영향받는 파일 목록
```
1. modes/narrative_mode.py       - story_mode/backgrounds, portraits 참조
2. modes/episode_mode.py          - story_mode/backgrounds, scripts 참조
3. modes/reflection_mode.py       - story_mode/reflection 참조
4. systems/dialogue_loader.py     - story_mode/scripts 참조
5. mode_configs/config_story.py   - story_mode/backgrounds 경로 하드코딩
```

#### 5.2 경로 변경 매핑

##### config_story.py (Line 229)
**Before**:
```python
return Path(f"assets/story_mode/backgrounds/{bg_filename}")
```
**After**:
```python
return Path(f"assets/data/episodes/ep1/backgrounds/{bg_filename}")
```

##### narrative_mode.py (Lines 275, 343-344, 436-437, 815-820, 846)
**Before**:
```python
config.ASSET_DIR / "story_mode" / "scripts"
config.ASSET_DIR / "story_mode" / "backgrounds" / target_bg
config.ASSET_DIR / "story_mode" / "reflection" / "backgrounds" / target_bg
config.ASSET_DIR / "story_mode" / "portraits" / f"portrait_{name}.png"
# ... 기타 story_mode 경로들
```
**After**:
```python
config.ASSET_DIR / "data" / "episodes" / "ep1" / "scripts"
config.ASSET_DIR / "data" / "episodes" / "ep1" / "backgrounds" / target_bg
config.ASSET_DIR / "data" / "episodes" / "ep1" / "backgrounds" / "reflection" / target_bg
config.ASSET_DIR / "data" / "episodes" / "ep1" / "portraits" / f"portrait_{name}.png"
```

##### siege 관련 파일 (있다면)
**Before**:
```python
assets/siege_mode/backgrounds/
assets/siege_mode/enemies/
assets/siege_mode/tiles/
```
**After**:
```python
assets/modes/siege/backgrounds/
assets/modes/siege/enemies/
assets/modes/siege/tiles/
```

#### 5.3 episode_resource_loader 업데이트 확인
- `systems/episode_resource_loader.py`는 이미 ep1 구조 지원 중
- 추가 수정 불필요 (우선순위: ep1 → shared → legacy)
- legacy fallback 경로 제거 가능 (story_mode 삭제 후)

**🛑 체크포인트 확인**:
- [ ] config_story.py 경로 업데이트 완료
- [ ] narrative_mode.py 모든 story_mode 참조 제거
- [ ] episode_mode.py 경로 업데이트 완료
- [ ] reflection_mode.py 경로 업데이트 완료
- [ ] dialogue_loader.py 경로 업데이트 완료
- [ ] siege 관련 코드 경로 업데이트 (해당 시)

---

### 🔄 Checkpoint 6: 레거시 폴더 삭제

#### 6.1 삭제 대상
```bash
assets/story_mode/        # 29 MB - 모든 내용이 ep1/로 이동됨
assets/siege_mode/        # 39 MB - modes/siege/로 이동됨
assets/wave_mode/         # 0 MB - 빈 폴더
```

#### 6.2 안전 삭제 절차
1. **백업 확인**: Git 상태 확인, 필요시 커밋
2. **테스트 선행**: Checkpoint 7 테스트 통과 후 삭제
3. **단계적 삭제**:
   ```bash
   # 1단계: 이름 변경 (임시 백업)
   mv assets/story_mode assets/story_mode_OLD
   mv assets/siege_mode assets/siege_mode_OLD

   # 2단계: 게임 테스트 (Checkpoint 7)

   # 3단계: 테스트 통과 시 완전 삭제
   rm -rf assets/story_mode_OLD
   rm -rf assets/siege_mode_OLD
   rm -rf assets/wave_mode
   ```

**🛑 체크포인트 확인**:
- [ ] Git 커밋 완료
- [ ] Checkpoint 7 테스트 통과
- [ ] 레거시 폴더 삭제 완료

---

### 🧪 Checkpoint 7: 종합 테스트

#### 7.1 Episode Mode 테스트
- [ ] Episode Mode 진입 성공
- [ ] 배경 이미지 로드 확인 (bg_ruins.jpg 등)
- [ ] 초상화 로드 확인 (portrait_artemis.jpg 등)
- [ ] 컷씬 이미지 로드 확인 (cutscene_images/)
- [ ] 오디오 재생 확인 (BGM, SFX)
- [ ] 스크립트 로드 확인 (act1_opening.json 등)

#### 7.2 Narrative Mode 테스트
- [ ] Narrative Mode 진입 성공
- [ ] 스토리 배경 표시 확인
- [ ] 회상 컷씬 배경 로드 확인 (reflection/)
- [ ] 대화 스크립트 정상 작동

#### 7.3 Reflection Mode 테스트
- [ ] Reflection Mode 진입 성공
- [ ] 회상 배경 이미지 로드 확인 (bg_autumn_rain.jpg 등)

#### 7.4 Siege Mode 테스트 (해당 시)
- [ ] Siege Mode 진입 성공
- [ ] siege 배경 로드 확인
- [ ] siege 적 이미지 로드 확인
- [ ] siege 타일 이미지 로드 확인

#### 7.5 에러 로그 확인
```bash
게임 실행 후 콘솔 확인:
- "FileNotFoundError" 없는지 확인
- "INFO: Episode loaded" 정상 출력 확인
- "WARNING: Failed to load" 없는지 확인
```

**🛑 체크포인트 확인**:
- [ ] 모든 모드 정상 진입
- [ ] 모든 리소스 로드 성공
- [ ] 에러 로그 없음
- [ ] 게임플레이 정상 작동

---

## 📊 예상 효과

### 공간 절약
- 중복 제거: ~10-15 MB 예상
- 빈 폴더 제거: 구조 명확화

### 구조 개선
| Before | After | 개선점 |
|--------|-------|--------|
| `story_mode/backgrounds/` | `data/episodes/ep1/backgrounds/` | 에피소드 명확화 |
| `siege_mode/` | `modes/siege/` | 모드별 계층 통일 |
| `wave_mode/` (빈 폴더) | 삭제 | 불필요한 폴더 제거 |
| 레거시 경로 혼재 | 단일 경로 | 코드 단순화 |

### 코드 개선
- 경로 참조 일관성 확보
- episode_resource_loader 완전 활용
- 레거시 fallback 경로 제거 가능

---

## ⚠️ 주의사항

### 1. 파일 이동 시 중복 확인
- `story_mode/backgrounds/`와 `ep1/backgrounds/`에 동일 파일명 있을 수 있음
- 이동 전 파일 비교 필요 (크기, 수정일 확인)

### 2. 코드 수정 시 누락 방지
- `story_mode` 문자열 전체 검색 후 모두 수정
- `siege_mode` 문자열도 동일하게 검색

### 3. Git 히스토리 보존
- 파일 이동은 `git mv` 사용 권장
- 대량 이동 시 별도 커밋 생성

### 4. 테스트 철저히
- 각 Checkpoint마다 관련 기능 테스트
- 최종 Checkpoint 7에서 전체 테스트

---

## 🚀 실행 방법

### 옵션 A: 자동 실행 (권장)
```
각 Checkpoint를 순서대로 진행하며, 각 단계마다 사용자 확인 후 다음 단계 진행
```

### 옵션 B: 수동 실행
```
이 문서를 참조하여 사용자가 직접 파일 이동 및 코드 수정
```

---

## 📝 체크리스트 요약

- [x] Checkpoint 1: 폴더 구조 분석 완료
- [ ] Checkpoint 2: story_mode 마이그레이션
  - [ ] 2.1 backgrounds 이동
  - [ ] 2.2 reflection 이동
  - [ ] 2.3 sounds 이동
  - [ ] 2.4 scripts 이동
  - [ ] 2.5 빈 폴더 삭제
- [ ] Checkpoint 3: siege_mode 마이그레이션
  - [ ] 3.1 폴더명 변경
- [ ] Checkpoint 4: 빈 폴더 정리
  - [ ] 4.1 wave_mode 삭제
  - [ ] 4.2 기타 빈 폴더 확인
- [ ] Checkpoint 5: 코드 경로 업데이트
  - [ ] 5.1 config_story.py 수정
  - [ ] 5.2 narrative_mode.py 수정
  - [ ] 5.3 episode_mode.py 수정
  - [ ] 5.4 reflection_mode.py 수정
  - [ ] 5.5 dialogue_loader.py 수정
- [ ] Checkpoint 6: 레거시 폴더 삭제
  - [ ] 6.1 Git 커밋
  - [ ] 6.2 안전 삭제 실행
- [ ] Checkpoint 7: 종합 테스트
  - [ ] 7.1 Episode Mode 테스트
  - [ ] 7.2 Narrative Mode 테스트
  - [ ] 7.3 Reflection Mode 테스트
  - [ ] 7.4 Siege Mode 테스트
  - [ ] 7.5 에러 로그 확인

---

**다음 단계**: Checkpoint 2부터 시작 (사용자 승인 후)
