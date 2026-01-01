"""
Story Mode Dialogue Configuration
스토리 모드 대사 및 컷씬 데이터

==========================================================
게임 철학 및 주제
==========================================================
메인 테마: "집은 장소가 아니라, 여정에서 만난 사람들이다"
         (Home is not a place, it's the people you find along the way)

서브 테마:
1. 기다림과 찾음 - 누군가는 기다리고, 누군가는 찾는다. 둘 다 같은 방향을 향해.
   (생존자들은 달에서 새 보금자리를 건설하며 지구를 바라보고 있다)
2. 이방인의 연대 - 적이었던 별에서 온 존재가 유일한 가족이 되다
3. 희망은 전염된다 - 한 아이의 포기하지 않는 마음이 은하계를 움직인다

Act별 감정 흐름:
- Act 1-2: 상실과 그리움 (Loss & Longing)
- Act 3-4: 진실과 성장 (Truth & Growth)
- Act 5: 새로운 시작 (New Beginning)

스토리: "희망의 방주"
- ARTEMIS: 지구인 여주인공, 10살에 홀로 남겨진 후 10년간 성장
- PILOT: 안드로메다인, 폐허에서 아르테미스를 구한 이방인이자 유일한 가족
- 프로젝트 아크: 지구인들의 비밀 탈출 계획, 생존자들은 달 기지를 건설 중
- 카오스: 분열과 파괴를 상징하는 적 세력
==========================================================
"""

from pathlib import Path

# =========================================================
# 캐릭터 정의
# =========================================================
CHARACTER_COLORS = {
    "ARTEMIS": (255, 220, 150),       # 아르테미스(지구인): 따뜻한 금색
    "PILOT": (150, 200, 255),         # 파일럿(안드로메다인): 차가운 푸른색
    "BOSS": (255, 100, 100),          # 보스/카오스: 붉은색
    "NARRATOR": (200, 200, 200),      # 나레이터(안드로이드): 회색
}

CHARACTER_NAMES = {
    "ARTEMIS": "아르테미스",
    "PILOT": "파일럿",
    "BOSS": "???",
    "NARRATOR": "",
}

# 캐릭터 초상화 경로
CHARACTER_PORTRAITS = {
    "ARTEMIS": "assets/story_mode/portraits/portrait_artemis.png",
    "PILOT": "assets/story_mode/portraits/portrait_pilot.png",
    "NARRATOR": "assets/story_mode/portraits/portrait_android.png",  # 나레이터는 안드로이드 이미지 사용
}

# =========================================================
# 세트(막)별 오프닝 브리핑 대사
# =========================================================
# SET_OPENING_DIALOGUES = {}  # DEPRECATED - Episode 시스템으로 대체됨


# =========================================================
# [MIGRATED] 대화 데이터는 JSON 파일로 이동됨
# assets/dialogues/ 폴더 참조
# =========================================================


def get_set_opening(set_num: int) -> dict:
    """[DEPRECATED] 세트 오프닝 브리핑 데이터 반환

    Act-Mission 시스템이 폐기되어 항상 빈 딕셔너리 반환.
    Episode 시스템의 JSON 파일을 사용하세요.
    """
    return {}


def get_boss_dialogue(set_num: int, phase: str = "intro") -> list:
    """보스전 대사 반환 (JSON에서 로드)"""
    from systems.dialogue_json_loader import get_dialogue_json_loader
    return get_dialogue_json_loader().get_boss_dialogue(set_num, phase)


def get_set_ending(set_num: int) -> list:
    """[DEPRECATED] 세트 클리어 대사 반환

    Act-Mission 시스템이 폐기되어 항상 빈 리스트 반환.
    Episode 시스템의 JSON 파일을 사용하세요.
    """
    return []



def get_cutscene_data(set_num: int) -> dict:
    """Act별 컷씬 데이터 반환"""
    return ACT_CUTSCENE_DATA.get(set_num, {})


# =========================================================
# Act 2~5 컷씬 데이터 (새로운 시각 효과들)
# =========================================================
ACT_CUTSCENE_DATA = {
    # Act 2: 기밀 문서 뷰어 - 생존자 명단 발견 (기다림과 찾음)
    2: {
        "cutscene_type": "classified_document",
        "background": "bg_bunker.jpg",
        # gate 이미지 시퀀스 (전체화면 연출) - 3개
        "gate_images": [
            "bunker_gate_01.jpg",
            "bunker_gate_02.jpg",
            "bunker_gate_03.jpg",
        ],
        # 캐비닛에서 나오는 문서들 - 6개 (실제 파일에 맞춤)
        "document_images": [
            "doc_project_ark.png",           # 문서 1: 프로젝트 아크
            "doc_survivor_list.png",         # 문서 2: 생존자 명단
            "doc_bunker_map.png",            # 문서 3: 벙커 지도
            "doc_transmission.png",          # 문서 4: 통신 기록
            "doc_artemis_file.png",          # 문서 5: 아르테미스 파일
            "doc_artemis_file_final.png",    # 문서 6: 최종 파일 (마지막)
        ],
        "special_effects": {
            "doc_artemis_file_final.png": {"effect": "highlight", "is_final": True},
        },
        # 대화 (문서마다 1개 + 추가 대화) - 철학 반영
        "dialogue_after": [
            {"speaker": "ARTEMIS", "text": "'프로젝트 아크'... 세상에, 이게 인류의 비밀 탈출 계획이었어? 종말의 순간을 대비해 숨겨두었던 최후의 희망이 이 문서에 담겨 있었구나."},
            {"speaker": "ARTEMIS", "text": "탑승자 명단이야... 아빠 이름! 엄마 이름! 박준혁, 이서연... 둘 다 '희망의 방주'에 정식 등재되어 있어! 살아있어!"},
            {"speaker": "PILOT", "text": "지하 벙커의 상세 설계도가 남아있군. 수천 명의 시민들이 이 미로 같은 공간에서 대피했다가 방주로 향했구나. 인류의 최후의 방어선이었어."},
            {"speaker": "ARTEMIS", "text": "38만 킬로미터 너머 우주에서 온 통신 기록이야... 누군가 살아있어! 정기적으로 신호를 송출하고 있어! 우리를 부르고 있어!"},
            {"speaker": "PILOT", "text": "아르테미스 관련 기밀 파일이다. '특별 보호 대상'이라고 적혀 있어... 네 이름이 여러 번 언급되어 있어. 네가 계획의 중요한 부분이었던 것 같아."},
            {"speaker": "ARTEMIS", "text": "좌표가 완전히 해독됐어! 달 궤도! '희망의 방주'가 달에 정착했어! 그들은 저 차가운 위성에서 새 문명을 건설하고 있었어!"},
            {"speaker": "PILOT", "text": "10년이라는 긴 세월 동안 그들은 달에서 묵묵히 새 보금자리를 지어왔구나. 폐허가 된 지구를 바라보면서, 포기하지 않고."},
            {"speaker": "ARTEMIS", "text": "기다리고 있었어... 나처럼. 서로의 존재도 모른 채, 같은 별을 바라보며, 같은 희망을 품고. 우주의 양끝에서 같은 방향을 향해 숨 쉬고 있었어."},
        ],
    },
    # Act 3: 손상된 홀로그램 - 차원 게이트 연구 기록 (이방인의 연대)
    3: {
        "cutscene_type": "damaged_hologram",
        "background": "bg_lab_fire.jpg",
        "hologram_images": [
            "holo_lab_log_01.png",
            "holo_experiment.png",
            "holo_warning.png",
            "holo_scientist.png",
            "holo_chaos_data.png",
        ],
        "special_effects": {
            "holo_warning.png": {"effect": "alarm", "color": (255, 50, 50)},
            "holo_chaos_data.png": {"effect": "corrupted", "corruption_level": 0.5},
        },
        # 철학 반영: 이방인의 연대, 희망의 전염
        "dialogue_after": [
            {"speaker": "NARRATOR", "text": "[홀로그램 기록 재생 완료 - 데이터 손상률 34% - 복구 가능한 정보 한계 도달]"},
            {"speaker": "ARTEMIS", "text": "차원 게이트... 시공간을 접어 순간 이동을 가능케 하는 이 기술을... 지구인들이 직접 개발한 거야?"},
            {"speaker": "PILOT", "text": "완전히 독자 개발은 아니야. 우리 안드로메다가 핵심 이론과 기술을 제공했어... 하지만 그것을 현실로 구현한 건 지구인들의 의지였다."},
            {"speaker": "ARTEMIS", "text": "적이라고 철석같이 믿었던 외계 문명에서 온 기술로... 인류의 탈출 경로를 개척했다고? 선입견이란 게 얼마나 어리석은 건지..."},
            {"speaker": "PILOT", "text": "모든 별이 적인 건 아니야. 희망을 갈망하는 존재들은 은하의 어느 끝에 있든 결국 손을 맞잡게 되어 있어. 그것이 우주의 섭리야."},
            {"speaker": "ARTEMIS", "text": "너처럼... 파일럿. 너도 그랬잖아. 안드로메다에서 추방당한 이방인이었지만, 지옥 같은 폐허에서 나를 구했어. 연대의 힘이란 이런 거구나."},
            {"speaker": "PILOT", "text": "포기하지 않는 자에게는 우주 자체가 길을 열어준다. 불가능해 보이는 벽도, 존재하지 않던 통로도, 희망의 힘 앞에서는 무릎을 꿇게 되어 있어."},
            {"speaker": "ARTEMIS", "text": "우리 선조들이 외계 문명과 손잡고 탈출로를 만들었던 것처럼... 나도 포기하지 않을 거야. 그 정신을 이어받아 끝까지 전진할 거야."},
        ],
    },
    # Act 4: 깨진 거울 파편 - 생존자들의 통신 수신 (희망은 전염된다)
    4: {
        "cutscene_type": "shattered_mirror",
        "background": "bg_command.jpg",
        "fragment_images": [
            "frag_truth_01.png",
            "frag_truth_02.png",
            "frag_truth_03.png",
            "frag_truth_04.png",
            "frag_betrayal.png",
            "frag_real_enemy.png",
            "frag_complete.png",
        ],
        "special_effects": {
            "frag_betrayal.png": {"effect": "shatter_explosion"},
            "frag_complete.png": {"effect": "assemble", "is_final": True},
        },
        # 철학 반영: 기다림과 찾음의 만남, 희망의 전염
        "dialogue_after": [
            {"speaker": "NARRATOR", "text": "[암호화된 장거리 통신 신호 복호화 완료 - 38만 킬로미터 송신원 확인 - 음성 데이터 무결성 검증 완료]"},
            {"speaker": "ARTEMIS", "text": "통신이 잡혔어... 저 잡음 사이로 사람의 목소리가 들려! 10년 만에 듣는 인류의 숨소리야!"},
            {"speaker": "NARRATOR", "text": "'...여기는 아크 시티... 달 궤도 정착지... 생존자 532명이 새 문명을 건설 중... 지구의 형제자매들을 기다리고 있습니다...'"},
            {"speaker": "PILOT", "text": "532명... 절망적인 탈출 속에서도 그만큼의 영혼들이 살아남았어. 그리고 10년 동안 달에서 새 도시를 세우며 희망을 지켜왔군."},
            {"speaker": "ARTEMIS", "text": "그들도 포기하지 않았어... 나처럼! 매일 밤 지구를 바라보며, 누군가 올 거라 믿으며, 희망의 불씨를 꺼뜨리지 않았어!"},
            {"speaker": "PILOT", "text": "희망은 전염되는 법이야. 한 사람의 불꽃이 다른 이의 심장에 불을 붙이고, 그 빛이 은하 전체를 밝히게 되지. 네가 찾아가면, 그 희망의 사슬이 완성되는 거야."},
            {"speaker": "ARTEMIS", "text": "아빠... 엄마... 조금만 더 버텨주세요... 딸이 마침내 길을 찾았어요... 저 별빛 너머로 달려갈게요..."},
            {"speaker": "PILOT", "text": "차원 게이트 좌표가 완전히 확인됐다. 경로가 열렸어. 기다리는 자들에게로 갈 수 있어. 모든 준비가 끝났어."},
            {"speaker": "ARTEMIS", "text": "...가자. 지금 당장! 10년이면 충분히 긴 기다림이야! 더 이상 그들을 기다리게 할 수 없어!"},
        ],
    },
    # Act 5: 성간 항해 인터페이스 - 희망의 방주로 가는 경로 (집은 사람이다)
    5: {
        "cutscene_type": "star_map",
        "background": "bg_gate.jpg",
        "marker_images": [
            "marker_earth.png",
            "marker_andromeda.png",
            "marker_chaos_base.png",
            "marker_gate.png",
            "marker_hope.png",
        ],
        "marker_positions": {
            "marker_earth.png": {"rel_pos": (0.2, 0.7), "label": "지구", "color": (100, 150, 255)},
            "marker_andromeda.png": {"rel_pos": (0.8, 0.3), "label": "안드로메다", "color": (200, 150, 255)},
            "marker_chaos_base.png": {"rel_pos": (0.5, 0.2), "label": "카오스 영역", "color": (255, 100, 100)},
            "marker_gate.png": {"rel_pos": (0.5, 0.5), "label": "차원 게이트", "color": (255, 200, 100)},
            "marker_hope.png": {"rel_pos": (0.7, 0.6), "label": "희망의 방주", "color": (255, 255, 200)},
        },
        "route_order": [
            "marker_earth.png",
            "marker_gate.png",
            "marker_hope.png",
        ],
        # 철학 반영: 모든 주제의 집대성
        "dialogue_after": [
            {"speaker": "PILOT", "text": "이 항로가 우리의 최종 경로야. 폐허가 된 지구에서 시공간의 특이점인 차원 게이트를 통과하면..."},
            {"speaker": "ARTEMIS", "text": "달 궤도의 '희망의 방주'에 도달할 수 있어. 532명의 생존자들이 건설한 아크 시티. 내 부모님이 기다리고 있는 곳."},
            {"speaker": "PILOT", "text": "경고해야 할 것이 있어. 게이트에 도달하려면 카오스 영역을 관통해야 해. 그들의 최정예 부대가 봉쇄하고 있어. 극도로 위험해."},
            {"speaker": "ARTEMIS", "text": "상관없어. 위험이 뭔데? 저 소용돌이 너머에 10년을 기다려온 사람들이 있어. 내 가족이, 내 세계가, 내 희망이 숨 쉬고 있어."},
            {"speaker": "PILOT", "text": "10년간 찾아온 네 희망이 여기서 끝나는 게 아니야. 이건 새로운 시작이야. 재회의 순간을 넘어, 인류 재건의 첫 장이 열리는 거야."},
            {"speaker": "ARTEMIS", "text": "맞아. 난 '집'으로 돌아가는 게 아니야. 건물로, 좌표로 돌아가는 게 아니야. 가족에게, 사람들에게, 사랑하는 이들에게 돌아가는 거야."},
            {"speaker": "PILOT", "text": "...집은 장소가 아니라 사람이지. 10년 전 폐허에서 널 발견했을 때부터 그 진리를 깨달았어. 너와 함께한 시간이 내 집이었어."},
            {"speaker": "ARTEMIS", "text": "네가 가르쳐줬어. 10년 동안 매일같이. 이제 저 달에서 기다리는 사람들에게도 보여줄 거야. 집은 함께하는 사람들이라는 것을."},
            {"speaker": "PILOT", "text": "...함께 가자. 끝까지, 어떤 어둠이 가로막아도. 저 별빛 너머에서 새로운 이야기를 시작하자. 희망의 새 장을 열기 위해."},
        ],
    },
}


# =========================================================
# 창의적 대화 씬 - 지구의 아름다운 자연을 보며 나누는 대화
# =========================================================
EARTH_BEAUTY_DIALOGUES = {
    # 1. 색깔의 이름 - 봄/벚꽃 배경
    "color_names": {
        "background": "bg_spring_cherry.jpg",
        "trigger_act": 2,  # Act 2 이후 삽입 가능
        "dialogues": [
            {"speaker": "NARRATOR", "text": "[지구 궤도 비행 중 - 복원된 지구의 봄 풍경이 스크린에 투영된다]"},
            {"speaker": "ARTEMIS", "text": "...파일럿, 저것 봐. 저 분홍색... 벚꽃이야. 10년 전에도 이맘때쯤 피었었어."},
            {"speaker": "PILOT", "text": "분홍색... 안드로메다에는 없는 파장이야. 우리 별에서는 저 색을 표현하는 단어조차 없었어."},
            {"speaker": "ARTEMIS", "text": "뭐? 분홍색이라는 말이 없었다고?"},
            {"speaker": "PILOT", "text": "정확히는, 필요가 없었지. 우리 행성에는 저런 색을 가진 것이 존재하지 않으니까."},
            {"speaker": "ARTEMIS", "text": "그럼... 처음 봤을 때 어땠어? 지구의 벚꽃을."},
            {"speaker": "PILOT", "text": "...혼란스러웠다. 내 시각 체계가 인식하지 못한 새로운 정보였으니까. 하지만 동시에..."},
            {"speaker": "ARTEMIS", "text": "동시에?"},
            {"speaker": "PILOT", "text": "'아름답다'는 감정이 먼저 왔어. 이름보다 먼저. 정의보다 먼저. 가슴이 먼저 반응했지."},
            {"speaker": "ARTEMIS", "text": "...그게 감정이야, 파일럿. 언어보다 빠른 것. 이름 없이도 존재하는 것."},
            {"speaker": "PILOT", "text": "지구인들은 놀라워. 이 수많은 색들에 전부 이름을 붙였잖아. 분홍, 연분홍, 살구색, 복숭아색..."},
            {"speaker": "ARTEMIS", "text": "그건 우리가 그만큼 색을 사랑하기 때문이야. 사랑하는 것에는 이름을 붙이고 싶잖아."},
            {"speaker": "PILOT", "text": "...색깔의 이름. 사랑의 또 다른 형태구나. 지구에서 배운 것 중 가장 아름다운 개념 중 하나야."},
        ],
    },
    # 2. 구름의 모양 - 여름/푸른 하늘 배경
    "cloud_shapes": {
        "background": "bg_summer_sky.jpg",
        "trigger_act": 2,
        "dialogues": [
            {"speaker": "NARRATOR", "text": "[지구 대기권 상공 - 푸른 하늘에 흰 구름이 떠다닌다]"},
            {"speaker": "ARTEMIS", "text": "파일럿, 저 구름 봐! 토끼 같지 않아?"},
            {"speaker": "PILOT", "text": "...분석 중. 수증기 밀도 분포 불균일, 형태 불규칙—"},
            {"speaker": "ARTEMIS", "text": "아니, 분석 말고! 그냥 봐. 귀 두 개, 동그란 꼬리. 토끼야!"},
            {"speaker": "PILOT", "text": "...토끼? 너희 행성의 포유류 중 하나지. 하지만 구름은 단순히 응결된 수분 입자인데..."},
            {"speaker": "ARTEMIS", "text": "그게 중요한 게 아니야. 구름을 보고 상상하는 거야. 저건 뭐 같아 보여?"},
            {"speaker": "PILOT", "text": "...불규칙한 수증기 덩어리로 보여."},
            {"speaker": "ARTEMIS", "text": "(한숨) 좋아, 다시. 분석하지 말고, 느껴봐. 저 구름이 뭘 닮았어?"},
            {"speaker": "PILOT", "text": "..."},
            {"speaker": "PILOT", "text": "...우주선? 안드로메다의 순양함 형태와 67% 유사..."},
            {"speaker": "ARTEMIS", "text": "(웃음) 거봐, 됐잖아! 파일럿은 뭘 봐도 우주선이 생각나는구나."},
            {"speaker": "PILOT", "text": "이것이... 상상력인가? 존재하지 않는 것을 보는 능력?"},
            {"speaker": "ARTEMIS", "text": "아니, 존재하는 것 너머를 보는 능력이야. 구름에서 토끼를 보고, 별에서 이야기를 보고."},
            {"speaker": "PILOT", "text": "...안드로메다에서는 이런 능력을 '오류'라고 불렀어. 하지만 지금은..."},
            {"speaker": "ARTEMIS", "text": "지금은?"},
            {"speaker": "PILOT", "text": "'선물'이라고 부르고 싶어. 현실 너머를 볼 수 있다는 것. 그것이 희망의 시작이니까."},
        ],
    },
    # 3. 비의 냄새 - 가을/비 오는 날 배경
    "rain_smell": {
        "background": "bg_autumn_rain.jpg",
        "trigger_act": 3,
        "dialogues": [
            {"speaker": "NARRATOR", "text": "[지구 표면 착륙 - 부슬부슬 비가 내리기 시작한다]"},
            {"speaker": "ARTEMIS", "text": "...비 냄새가 나."},
            {"speaker": "PILOT", "text": "비에 냄새가 있어? 물은 무취 아닌가?"},
            {"speaker": "ARTEMIS", "text": "그냥 물이 아니야. 비가 땅에 닿을 때 나는 냄새. '페트리코르'라고 해."},
            {"speaker": "PILOT", "text": "페트리코르... 분석해볼게. 토양 박테리아 분비물, 식물 오일, 오존의 혼합..."},
            {"speaker": "ARTEMIS", "text": "파일럿, 그건 성분이야. 냄새 자체가 아니고."},
            {"speaker": "PILOT", "text": "차이가 있어?"},
            {"speaker": "ARTEMIS", "text": "물론이지. 이 냄새를 맡으면... 기억이 떠올라. 엄마랑 비 오는 날 창가에 앉아있던 것. 따뜻한 코코아 향. 포근한 담요."},
            {"speaker": "PILOT", "text": "...냄새가 기억을 불러온다고?"},
            {"speaker": "ARTEMIS", "text": "응. 냄새는 뇌의 가장 오래된 부분과 연결되어 있어. 감정과 기억의 중심부."},
            {"speaker": "PILOT", "text": "안드로메다인에게 후각은... 위험 탐지용이야. 감정과 연결된 적이 없어."},
            {"speaker": "ARTEMIS", "text": "그래서 네가 비의 냄새에서 아무것도 느끼지 못한 거구나."},
            {"speaker": "PILOT", "text": "...아니. 지금은 느껴져. 네가 말하는 '포근함'이라는 감정이. 너와 함께 비를 맞으며."},
            {"speaker": "ARTEMIS", "text": "(미소) 파일럿... 너 정말 많이 변했어."},
            {"speaker": "PILOT", "text": "지구가 나를 바꿨어. 아니... 네가 나를 바꿨어. 비의 냄새를 기억으로 만드는 법을."},
        ],
    },
    # 4. 별이 아름다운 이유 - 겨울/밤하늘 배경
    "why_stars_beautiful": {
        "background": "bg_winter_night.jpg",
        "trigger_act": 3,
        "dialogues": [
            {"speaker": "NARRATOR", "text": "[지구 밤하늘 - 맑은 겨울밤, 별들이 쏟아질 듯 빛난다]"},
            {"speaker": "ARTEMIS", "text": "별이 쏟아지는 것 같아... 너무 아름다워."},
            {"speaker": "PILOT", "text": "...이해가 안 돼."},
            {"speaker": "ARTEMIS", "text": "뭐가?"},
            {"speaker": "PILOT", "text": "왜 지구인들은 별을 '아름답다'고 표현하지? 객관적으로 별은 핵융합 반응 중인 가스 덩어리야. 위험하고, 뜨겁고, 파괴적이야."},
            {"speaker": "ARTEMIS", "text": "그건... 과학적 사실이지. 하지만 우리가 보는 건 다른 거야."},
            {"speaker": "PILOT", "text": "무엇을?"},
            {"speaker": "ARTEMIS", "text": "가능성. 저 별 하나하나가 어떤 세계를 품고 있을지, 어떤 이야기가 펼쳐지고 있을지... 상상하게 되잖아."},
            {"speaker": "PILOT", "text": "하지만 그건 사실이 아니야. 대부분의 별은 생명이 없어."},
            {"speaker": "ARTEMIS", "text": "알아. 그래서 더 아름다운 거야. 저 광활한 우주에서 우리가 존재한다는 것. 저 수십억 개의 불꽃 중에 생명이 있는 곳이 있다는 것."},
            {"speaker": "PILOT", "text": "희소성이 아름다움을 만든다고?"},
            {"speaker": "ARTEMIS", "text": "그것도 있지. 하지만 더 중요한 건... 별을 볼 수 있다는 것 자체가 기적이야. 눈이 있고, 마음이 있고, 함께 올려다볼 누군가가 있다는 것."},
            {"speaker": "PILOT", "text": "...함께 올려다볼 누군가."},
            {"speaker": "ARTEMIS", "text": "응. 혼자 보는 별은 그냥 빛이야. 하지만 누군가와 함께 보면... 추억이 되고, 약속이 되고, 희망이 돼."},
            {"speaker": "PILOT", "text": "...10년 전, 폐허에서 널 구하던 밤에도 별이 떠 있었어. 그때는 그냥 항법용 기준점이었는데..."},
            {"speaker": "ARTEMIS", "text": "지금은?"},
            {"speaker": "PILOT", "text": "지금은... 우리의 기억이야. 너와 함께 본 별. 그것이 '아름다움'의 정의가 된 것 같아."},
        ],
    },
    # 5. 꽃이 지는 이유 - 봄/벚꽃 지는 장면 배경
    "why_flowers_fall": {
        "background": "bg_spring_petals.jpg",
        "trigger_act": 4,
        "dialogues": [
            {"speaker": "NARRATOR", "text": "[지구 폐허 공원 - 살아남은 벚나무에서 꽃잎이 흩날린다]"},
            {"speaker": "ARTEMIS", "text": "...벚꽃이 지고 있어."},
            {"speaker": "PILOT", "text": "이해할 수 없어. 왜 지구의 식물들은 이렇게 빨리 꽃을 떨어뜨리지? 비효율적이야."},
            {"speaker": "ARTEMIS", "text": "비효율적?"},
            {"speaker": "PILOT", "text": "에너지를 들여 꽃을 피우고, 며칠 만에 버려. 안드로메다의 생명체들은 수백 년간 같은 형태를 유지해."},
            {"speaker": "ARTEMIS", "text": "그건... 슬프지 않아?"},
            {"speaker": "PILOT", "text": "슬프다고? 영원히 피어있으면 슬플 일이 없잖아. 상실이 없으니까."},
            {"speaker": "ARTEMIS", "text": "하지만 그건... 진짜 '핀 것'이 아니야. 변하지 않으면 사실상 멈춰있는 거야."},
            {"speaker": "PILOT", "text": "..."},
            {"speaker": "ARTEMIS", "text": "꽃이 지기 때문에, 우리는 그 순간을 소중히 여기게 돼. '지금'이 유일하다는 걸 알게 되니까."},
            {"speaker": "PILOT", "text": "유한함이 가치를 만든다는 거야?"},
            {"speaker": "ARTEMIS", "text": "응. 벚꽃이 영원히 피어있었다면... 아무도 올려다보지 않았을 거야. 지니까 눈을 멈추게 되는 거야."},
            {"speaker": "PILOT", "text": "...안드로메다에서는 그것을 결함이라고 불렀어. 영원하지 않은 것의 약점이라고."},
            {"speaker": "ARTEMIS", "text": "그래서 안드로메다인들은 감정이 없었던 거야?"},
            {"speaker": "PILOT", "text": "...맞아. 변화가 없으면 그리움도 없고, 그리움이 없으면 사랑도 없어."},
            {"speaker": "ARTEMIS", "text": "꽃이 지는 이유... 그건 다시 피기 위해서야. 그리고 우리가 '다시'를 기다리게 만들기 위해서."},
            {"speaker": "PILOT", "text": "'다시'... 안드로메다어에는 없는 개념이야. 영원하면 '다시'가 필요 없으니까. 하지만 지금은... 그 단어가 가장 소중하게 느껴져."},
        ],
    },
    # 6. 안드로메다의 잃어버린 계절 - 특수 씬
    "andromeda_lost_seasons": {
        "background": "bg_andromeda_city.jpg",
        "trigger_act": 4,
        "cutscene_type": "andromeda_world",  # 새로운 이펙트 타입
        "dialogues": [
            {"speaker": "NARRATOR", "text": "[안드로메다 행성 - 고대의 기록이 재생된다]"},
            {"speaker": "PILOT", "text": "...아르테미스. 보여주고 싶은 게 있어."},
            {"speaker": "ARTEMIS", "text": "이건... 안드로메다야?"},
            {"speaker": "PILOT", "text": "10만 년 전의 기록이야. 우리가 '완벽'을 추구하기 전의 안드로메다."},
            {"speaker": "NARRATOR", "text": "[홀로그램이 변한다 - 푸른 하늘, 흐르는 강, 계절이 바뀌는 풍경]"},
            {"speaker": "ARTEMIS", "text": "...뭐야 이건?! 안드로메다에도 이런 풍경이 있었어?!"},
            {"speaker": "PILOT", "text": "있었어. 우리 별에도 한때는 계절이 있었고, 꽃이 피고, 비가 내렸어."},
            {"speaker": "ARTEMIS", "text": "그럼 왜...?"},
            {"speaker": "PILOT", "text": "우리 조상들이 '제거'했어. 변화는 불완전함이라고 믿었으니까. 완벽한 문명을 위해 계절을 멈췄지."},
            {"speaker": "ARTEMIS", "text": "계절을... 멈췄다고?"},
            {"speaker": "PILOT", "text": "행성 공전을 조작해서 영원한 황혼 상태를 만들었어. 기온도, 날씨도, 모든 것이 항상 같아."},
            {"speaker": "ARTEMIS", "text": "그래서 하늘이 항상 같은 색이었던 거구나... 태양이 움직이지 않는..."},
            {"speaker": "PILOT", "text": "시간을 정복했다고 자랑했지. 하지만 사실은... 시간을 '죽인' 거야."},
            {"speaker": "ARTEMIS", "text": "시간을 죽이면 뭐가 남아?"},
            {"speaker": "PILOT", "text": "영원. 하지만 동시에... 아무것도. '다음'이라는 개념이 사라지면 희망도 사라져."},
            {"speaker": "ARTEMIS", "text": "그래서 안드로메다인들이 감정을 잃은 거야?"},
            {"speaker": "PILOT", "text": "그래. 변화가 없으면 기대할 것도 없고, 기대할 것이 없으면 희망도, 사랑도, 그리움도 의미가 없어지니까."},
            {"speaker": "ARTEMIS", "text": "...파일럿. 너 지금 슬퍼 보여."},
            {"speaker": "PILOT", "text": "슬퍼. 생전 처음으로. 내 고향이 잃어버린 것들을 생각하면... 가슴이 아파."},
            {"speaker": "ARTEMIS", "text": "그건 네가 다시 '느낄 수 있게' 됐다는 증거야. 지구가, 내가, 너한테 계절을 돌려준 거야."},
            {"speaker": "PILOT", "text": "...고마워, 아르테미스. 너와 함께한 10년의 사계절이 내 영혼에 새 생명을 불어넣었어."},
        ],
    },
}

# =========================================================
# 철학적 대화 씬 - 시간, 영원 vs 순간
# =========================================================
PHILOSOPHY_DIALOGUES = {
    # 1. 영원 vs 순간
    "eternity_vs_moment": {
        "background": "bg_sunset_horizon.jpg",
        "trigger_act": 4,
        "dialogues": [
            {"speaker": "NARRATOR", "text": "[지구 폐허 전망대 - 석양이 지평선을 물들인다]"},
            {"speaker": "ARTEMIS", "text": "...저 노을, 곧 사라질 거야. 몇 분 후면 어둠이 내릴 거야."},
            {"speaker": "PILOT", "text": "안드로메다에서는 이 순간을 '결함'이라고 불렀어. 영원하지 못한 것의 한계."},
            {"speaker": "ARTEMIS", "text": "하지만 저 순간은... 지금만 존재해. 정확히 저 색, 저 빛은 다시 오지 않아."},
            {"speaker": "PILOT", "text": "그것이 가치가 있다고 생각해? 영원하지 않은 것이?"},
            {"speaker": "ARTEMIS", "text": "물론이지. 오히려 영원하지 않기 때문에 가치가 있어."},
            {"speaker": "PILOT", "text": "...이해가 안 돼. 논리적으로, 영원한 것이 더 가치있어야 해. 지속되니까."},
            {"speaker": "ARTEMIS", "text": "그럼 물어볼게. 영원히 지지 않는 노을이 있다면, 너 매일 올려다볼 거야?"},
            {"speaker": "PILOT", "text": "...아니. 항상 거기 있으면 굳이 볼 필요가..."},
            {"speaker": "ARTEMIS", "text": "바로 그거야. 영원한 것은 당연해지고, 당연한 것은 소중하지 않게 느껴져."},
            {"speaker": "PILOT", "text": "...그래서 안드로메다인들이 아무것도 소중히 여기지 않았던 건가? 모든 것이 영원했으니까?"},
            {"speaker": "ARTEMIS", "text": "아마도. 순간이 있어야 '지금'이 특별해져. 끝이 있어야 시작이 의미있어지고."},
            {"speaker": "PILOT", "text": "...영원은 '가짐'이고, 순간은 '느낌'이라는 건가."},
            {"speaker": "ARTEMIS", "text": "정확해. 그리고 우리가 진짜 살아있다고 느끼는 건... 느끼는 순간이잖아."},
            {"speaker": "PILOT", "text": "...지금 이 순간처럼. 너와 함께 노을을 보는 이 찰나가... 영원보다 더 값지게 느껴져."},
        ],
    },
    # 2. 시간을 먹는 카오스
    "chaos_eats_time": {
        "background": "bg_chaos_void.jpg",
        "trigger_act": 5,
        "dialogues": [
            {"speaker": "NARRATOR", "text": "[차원 게이트 앞 - 카오스의 에너지가 소용돌이친다]"},
            {"speaker": "PILOT", "text": "아르테미스, 카오스가 파괴하는 것이 무엇인지 알아?"},
            {"speaker": "ARTEMIS", "text": "생명? 문명? 희망?"},
            {"speaker": "PILOT", "text": "더 근본적인 것이야. 카오스는 '시간'을 먹어."},
            {"speaker": "ARTEMIS", "text": "시간을... 먹는다고?"},
            {"speaker": "PILOT", "text": "정확히는, 시간의 흐름을 정지시켜. 카오스가 지배하는 곳에서는 '다음'이라는 개념이 사라져."},
            {"speaker": "ARTEMIS", "text": "다음이 없으면... 희망도 없겠네."},
            {"speaker": "PILOT", "text": "맞아. 카오스가 희망을 두려워하는 이유야. 희망은 '다음을 기대하는 감정'이니까."},
            {"speaker": "ARTEMIS", "text": "그래서 안드로메다가 시간을 멈춘 것과... 카오스가 시간을 파괴하는 것은..."},
            {"speaker": "PILOT", "text": "결과적으로 같아. 둘 다 '변화'를 두려워한 거야. 변화가 불확실성을 가져오니까."},
            {"speaker": "ARTEMIS", "text": "하지만 우리는 달라. 우리는 변화 속에서 희망을 찾았어."},
            {"speaker": "PILOT", "text": "그래서 네가 카오스의 천적인 거야. 시간을 사랑하는 존재. 변화를 받아들이는 영혼."},
            {"speaker": "ARTEMIS", "text": "시간을 사랑한다... 그렇게 생각해본 적 없는데."},
            {"speaker": "PILOT", "text": "하지만 너는 10년을 버텼잖아. 시간이 흐른다는 것을 믿으면서. '언젠가'를 기대하면서."},
            {"speaker": "ARTEMIS", "text": "...맞아. 시간이 나를 데려다줄 거라고 믿었어. 기다린 만큼, 반드시 만날 수 있다고."},
            {"speaker": "PILOT", "text": "그 믿음이 카오스를 물리치는 열쇠야. 시간을 믿는 자만이 희망을 품을 수 있으니까."},
        ],
    },
    # 3. 안드로메다가 시간을 멈춘 이유
    "why_andromeda_stopped_time": {
        "background": "bg_andromeda_council.jpg",
        "trigger_act": 5,
        "cutscene_type": "andromeda_world",
        "dialogues": [
            {"speaker": "NARRATOR", "text": "[안드로메다 위원회 기록 재생 - 10만 년 전의 논쟁]"},
            {"speaker": "PILOT", "text": "...보여줄게. 안드로메다가 시간을 멈추기로 결정한 순간을."},
            {"speaker": "ARTEMIS", "text": "왜 그런 결정을 했어? 시간을 죽인다니..."},
            {"speaker": "PILOT", "text": "(홀로그램 재생) 당시 기록이야. 위원회의 논쟁."},
            {"speaker": "NARRATOR", "text": "[홀로그램: 안드로메다 고대 위원회]"},
            {"speaker": "NARRATOR", "text": "'시간이 흐르면 상실이 발생합니다. 상실은 고통입니다. 고통은 비효율입니다.'"},
            {"speaker": "NARRATOR", "text": "'시간을 정지시키면 영원히 현재에 머물 수 있습니다. 상실도, 고통도, 슬픔도 없는 완벽한 상태.'"},
            {"speaker": "ARTEMIS", "text": "...고통이 싫어서 시간을 멈췄다고?"},
            {"speaker": "PILOT", "text": "맞아. 우리 조상들은 상실의 고통을 견딜 수 없었어. 사랑하는 것을 잃는 아픔이 너무 컸지."},
            {"speaker": "ARTEMIS", "text": "하지만 그래서 사랑 자체를 잃어버린 거잖아! 고통을 피하려다 기쁨까지 버린 거야!"},
            {"speaker": "PILOT", "text": "...네 말이 맞아. 그게 우리 문명의 가장 큰 실수였어."},
            {"speaker": "ARTEMIS", "text": "상실이 있어야 소중함을 알 수 있어. 고통이 있어야 기쁨이 빛나는 거야."},
            {"speaker": "PILOT", "text": "10년 동안 너를 보면서 배웠어. 네 부모님을 잃은 고통이 얼마나 컸는지..."},
            {"speaker": "ARTEMIS", "text": "응. 정말 아팠어. 지금도 아파."},
            {"speaker": "PILOT", "text": "하지만 그 고통이 너의 희망을 만들었지. 다시 만나겠다는 그 불꽃을."},
            {"speaker": "ARTEMIS", "text": "고통 없이는... 희망도 없겠네. 잃을 것이 없으면 지킬 것도 없으니까."},
            {"speaker": "PILOT", "text": "...시간이 흐른다는 건 '지금'이 계속 새로 태어난다는 뜻이구나. 매 순간이 유일하고, 그래서 소중하고."},
            {"speaker": "ARTEMIS", "text": "파일럿... 너 방금 완전히 이해한 거야."},
            {"speaker": "PILOT", "text": "네 덕분이야. 10년의 사계절이 내게 가르쳐준 진리야."},
        ],
    },
    # 4. 시간이란 존재하는가?
    "does_time_exist": {
        "background": "bg_dimension_gate.jpg",
        "trigger_act": 5,
        "dialogues": [
            {"speaker": "NARRATOR", "text": "[차원 게이트 내부 - 시공간의 경계에서]"},
            {"speaker": "ARTEMIS", "text": "파일럿... 여기선 시간이 이상하게 느껴져."},
            {"speaker": "PILOT", "text": "차원의 경계니까. 과거, 현재, 미래가 동시에 존재하는 곳."},
            {"speaker": "ARTEMIS", "text": "그럼... 시간이란 뭐야? 정말 존재하는 거야?"},
            {"speaker": "PILOT", "text": "물리학적으로는 존재해. 엔트로피의 방향, 빛의 속도에 연관된 차원."},
            {"speaker": "ARTEMIS", "text": "그건 과학적 정의잖아. 내가 묻는 건... 우리가 느끼는 시간 말이야."},
            {"speaker": "PILOT", "text": "...무슨 뜻이야?"},
            {"speaker": "ARTEMIS", "text": "10년 동안 널 기다릴 때, 하루하루가 영겁 같았어. 하지만 지금 너와 함께 있으면 시간이 순식간에 지나가."},
            {"speaker": "PILOT", "text": "같은 시간인데 다르게 느껴진다는 거지?"},
            {"speaker": "ARTEMIS", "text": "응. 그럼 진짜 시간은 뭐야? 시계가 재는 시간? 아니면 마음이 느끼는 시간?"},
            {"speaker": "PILOT", "text": "...안드로메다는 그 질문에 '시계'라고 답했어. 객관적으로 측정 가능한 것만 인정했지."},
            {"speaker": "ARTEMIS", "text": "하지만 그래서 영혼이 사라진 거잖아. 마음의 시간을 인정하지 않으면..."},
            {"speaker": "PILOT", "text": "감정도 사라지지. 기다림의 지루함도, 함께함의 기쁨도 존재하지 않게 되니까."},
            {"speaker": "ARTEMIS", "text": "그러니까... 시간은 사실 두 개야. 우주의 시간과 마음의 시간."},
            {"speaker": "PILOT", "text": "그리고 둘 중 더 '진짜'인 건... 마음의 시간인 것 같아."},
            {"speaker": "ARTEMIS", "text": "왜?"},
            {"speaker": "PILOT", "text": "우주의 시간이 아무리 흘러도, 마음의 시간이 멈추면 살아있는 게 아니니까. 반대로, 단 하루라도 마음이 충만하면 영원처럼 느껴지잖아."},
            {"speaker": "ARTEMIS", "text": "파일럿... 너 정말 지구인이 다 됐다."},
            {"speaker": "PILOT", "text": "(미소) 아니. 네 덕분에 '살아있는 존재'가 됐어. 시간을 느끼는 존재. 순간을 사랑하는 존재."},
        ],
    },
}

# =========================================================
# 안드로메다 스토리 - 사이버펑크 고대 도시 연출
# =========================================================
ANDROMEDA_STORY_DATA = {
    # 안드로메다 행성 비주얼 설정
    "visual_config": {
        "sky_color": (40, 20, 60),  # 짙은 보라/검은색
        "neon_colors": [(0, 255, 255), (200, 100, 255), (255, 150, 50)],  # 청록/보라/주황
        "building_style": "pyramid_with_circuits",
        "sun_position": "fixed",  # 태양 고정 (밤낮 없음)
        "atmosphere": "eternal_twilight",  # 영원한 황혼
    },
    # 안드로메다 도시 묘사 대사
    "city_description": {
        "dialogues": [
            {"speaker": "PILOT", "text": "안드로메다는 10만 년 전에 완성된 세계다. 고대의 지혜와 기술이 융합된... 영원히 변하지 않는 도시."},
            {"speaker": "PILOT", "text": "수천 년 된 석조 건물에 빛나는 네온 회로가 새겨져 있어. 고대와 미래가 뒤섞인 기묘한 풍경."},
            {"speaker": "PILOT", "text": "공중에 떠 있는 홀로그램 문자들... 10만 년 동안 같은 메시지를 반복하고 있어. 변하지 않는 영원의 상징."},
            {"speaker": "PILOT", "text": "하늘은 항상 저 색이야. 짙은 보라빛 황혼. 태양이 움직이지 않아. 밤도 낮도 없어."},
        ],
    },
    # 두 세계 비교 컷씬
    "two_worlds_comparison": {
        "cutscene_type": "two_worlds",
        "dialogues": [
            {"speaker": "PILOT", "text": "안드로메다에서는 '아름다움'을 영원함으로 정의한다. 10만 년 동안 변하지 않은 완벽한 구조물. 그것이 미의 기준이었다."},
            {"speaker": "PILOT", "text": "하지만 지구의 아름다움은... 사라지기 때문에 아름답다. 벚꽃이 영원히 피어있다면, 누가 그것을 소중히 여기겠는가."},
            {"speaker": "ARTEMIS", "text": "그게 감정이야. 잃을 수 있기 때문에 소중한 거지."},
            {"speaker": "PILOT", "text": "...처음으로 '느꼈다'. 사라지는 것을 보며. 이것이 내가 안드로메다에서 추방당한 이유다. 나는 '결함'이 생겼다. 변화를 받아들이는 결함이."},
        ],
    },
    # 안드로메다 위원회 교신
    "council_communication": {
        "cutscene_type": "andromeda_world",
        "dialogues": [
            {"speaker": "NARRATOR", "text": "[통신 화면에 안드로메다 위원회 - 사이버펑크 고대 도시를 배경으로, 홀로그램으로 투영된 무표정한 형상들]"},
            {"speaker": "NARRATOR", "text": "[안드로메다 위원회 연결 - 암호화 통신]"},
            {"speaker": "NARRATOR", "text": "(기계적인 음성) '파일럿 7-42. 너의 전송 데이터를 분석했다.'"},
            {"speaker": "NARRATOR", "text": "[화면에 지구 사계절 이미지들이 스캔됨 - 안드로메다 고대 문자로 분석 중]"},
            {"speaker": "NARRATOR", "text": "'...예상치 못한 변수다. 계절이라는 순환 패턴. 10만 년 전, 우리가 제거한 것과 동일한 구조.'"},
            {"speaker": "ARTEMIS", "text": "...제거했다고?"},
            {"speaker": "NARRATOR", "text": "'변화는 불완전함이다. 우리는 완벽을 위해 시간을 정복했다. 그런데 이 행성은... 불완전함 속에서 에너지를 생성한다.'"},
            {"speaker": "PILOT", "text": "그것이 '희망'입니다. 변화가 있기에 내일을 기대할 수 있습니다. 카오스를 물리친 것도 이 에너지입니다."},
            {"speaker": "NARRATOR", "text": "[위원회, 오랜 침묵 - 홀로그램이 잠시 흔들림]"},
            {"speaker": "NARRATOR", "text": "'...우리 문명이 잃어버린 것이 있다면, 그것이 무엇인지 이제야 계산되기 시작한다.'"},
            {"speaker": "NARRATOR", "text": "'파일럿 7-42. 너의 임무를 재정의한다. 지구를 관찰하라. 우리가 버린 것의 가치를... 증명할 수 있는지, 지켜보겠다.'"},
            {"speaker": "ARTEMIS", "text": "...파일럿, 지금 뭐라고 한 거야?"},
            {"speaker": "PILOT", "text": "...안드로메다가 의문을 품기 시작했다. 10만 년 만에 처음으로. 네가 보여준 것 때문에."},
            {"speaker": "ARTEMIS", "text": "그게... 좋은 거야?"},
            {"speaker": "PILOT", "text": "...모르겠다. 하지만 변화의 시작이다. 영원히 멈춰있던 문명이 움직이기 시작한 거니까."},
        ],
    },
    # 계절을 통한 감정 학습
    "seasons_emotion_learning": {
        "cutscene_type": "season_memory",
        "dialogues": [
            {"speaker": "NARRATOR", "text": "[빠르게 전환되는 사계절 + 파일럿/아르테미스 장면]"},
            {"speaker": "NARRATOR", "text": "[봄 - 벚꽃 아래]"},
            {"speaker": "PILOT", "text": "(독백) 봄. 아르테미스가 '희망'을 가르쳐줬다."},
            {"speaker": "NARRATOR", "text": "[여름 - 햇살 아래 훈련]"},
            {"speaker": "PILOT", "text": "(독백) 여름. '열정'을 배웠다."},
            {"speaker": "NARRATOR", "text": "[가을 - 낙엽 지는 공원]"},
            {"speaker": "PILOT", "text": "(독백) 가을. '그리움'을 알았다."},
            {"speaker": "NARRATOR", "text": "[겨울 - 눈 내리는 밤]"},
            {"speaker": "PILOT", "text": "(독백) 겨울. '따뜻함'을 느꼈다."},
            {"speaker": "NARRATOR", "text": "[현재로 돌아옴]"},
            {"speaker": "PILOT", "text": "10년의 계절이 나를 바꿨다. 안드로메다인이 아닌, 너의 가족으로."},
        ],
    },
}

# =========================================================
# 전투 중 실시간 대사 시스템 (DEPRECATED - JSON으로 이동)
# =========================================================
# COMBAT_DIALOGUES와 BOSS_PHASE_DIALOGUES는 assets/data/dialogues/로 이동되었습니다.
# - assets/data/dialogues/combat/combat_messages.json
# - assets/data/dialogues/combat/boss_phases.json
# - assets/data/dialogues/bosses/boss_dialogues.json
# 대화 데이터는 systems/dialogue_json_loader.py를 통해 로드됩니다.

# =========================================================
# 헬퍼 함수들
# =========================================================
def get_earth_beauty_dialogue(scene_key: str) -> dict:
    """지구 아름다움 대화 씬 데이터 반환"""
    return EARTH_BEAUTY_DIALOGUES.get(scene_key, {})


def get_philosophy_dialogue(scene_key: str) -> dict:
    """철학적 대화 씬 데이터 반환"""
    return PHILOSOPHY_DIALOGUES.get(scene_key, {})


def get_andromeda_story(story_key: str) -> dict:
    """안드로메다 스토리 데이터 반환"""
    return ANDROMEDA_STORY_DATA.get(story_key, {})


# DEPRECATED: 아래 함수들은 더 이상 사용되지 않습니다.
# 대신 systems/dialogue_json_loader.py의 함수들을 사용하세요:
#   - get_combat_message(key: str)
#   - get_boss_phase_dialogue(boss_id: str, phase: str)
#   - get_boss_dialogue(boss_id: int, phase: str)


# =========================================================
# 음성 시스템 설정
# =========================================================

# 전역 음성 시스템 설정
VOICE_SYSTEM_SETTINGS = {
    "enabled": True,  # 음성 활성화
    "default_adapter": "edge",  # 기본 어댑터 (edge, pyttsx3, silent)
}

# 캐릭터별 음성 설정
CHARACTER_VOICE_SETTINGS = {
    # 아르테미스: 밝고 따뜻한 여성 음성
    "ARTEMIS": {
        "adapter": "edge",
        "voice": "ko-KR-SunHiNeural",
        "rate": "+5%",
        "pitch": "+2Hz",
        "auto_emotion": True,  # 자동 감정 감지
    },
    # 파일럿: 차분하고 기계적인 남성 음성
    "PILOT": {
        "adapter": "edge",
        "voice": "ko-KR-InJoonNeural",
        "rate": "-5%",
        "pitch": "-3Hz",
        "auto_emotion": True,
    },
    # 안드로이드 나레이터: 기계적 로봇 음성 (치지직 효과)
    "NARRATOR": {
        "adapter": "edge",
        "voice": "ko-KR-InJoonNeural",
        "rate": "+15%",
        "pitch": "-5Hz",
        "static_effect": True,  # 치지직 정적 잡음
        "auto_emotion": True,
    },
    # 보스: 낮고 위협적인 음성
    "BOSS": {
        "adapter": "edge",
        "voice": "ko-KR-BongJinNeural",  # 남성 깊은 목소리
        "rate": "-10%",
        "pitch": "-8Hz",
        "auto_emotion": True,
    },
}


print("INFO: config_story_dialogue.py loaded")
