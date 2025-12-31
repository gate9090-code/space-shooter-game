"""최적화된 대화 추출 스크립트"""
import csv
import json
from pathlib import Path

dialogues = []

# Episode JSON
print('Extracting Episodes...')
episodes_dir = Path('assets/data/episodes')

for ep_json in list(episodes_dir.glob('*/ep*.json')) + list(episodes_dir.glob('ep*.json')):
    if not ep_json.is_file():
        continue

    with open(ep_json, 'r', encoding='utf-8') as f:
        data = json.load(f)
        episode_id = data.get('id', ep_json.stem)
        scenes = data.get('scenes', {})

        for scene_id, scene_data in scenes.items():
            scene_dialogues = scene_data.get('dialogues', [])
            background = scene_data.get('background', '')
            scene_type = scene_data.get('type', 'DIALOGUE')

            prev_background = None
            for idx, dlg in enumerate(scene_dialogues, 1):
                display_bg = '' if prev_background == background else background
                prev_background = background

                dialogues.append({
                    '사용처': f'{episode_id}_{scene_id}' if idx == 1 else '',
                    'scene_id': scene_id if idx == 1 else '',
                    '순서': idx,
                    '화자': dlg.get('speaker', ''),
                    '대화내용': dlg.get('text', ''),
                    '배경이미지': display_bg,
                    '효과': dlg.get('effect', ''),
                    '타입': scene_type if idx == 1 else '',
                    '파일경로': str(ep_json) if idx == 1 else ''
                })

print(f'Episodes: {len(dialogues)} dialogues')

# EARTH_BEAUTY
earth_path = Path('assets/data/dialogues/reflection/earth_beauty.json')
if earth_path.exists():
    with open(earth_path, 'r', encoding='utf-8') as f:
        earth_data = json.load(f)

    for scene_key, scene_data in earth_data.items():
        dlg_list = scene_data.get('dialogues', [])
        scene_bg = scene_data.get('background', '')

        prev_bg = None
        for idx, dlg in enumerate(dlg_list, 1):
            display_bg = '' if prev_bg == scene_bg else scene_bg
            prev_bg = scene_bg

            dialogues.append({
                '사용처': f'EARTH_BEAUTY_{scene_key}' if idx == 1 else '',
                'scene_id': scene_key if idx == 1 else '',
                '순서': idx,
                '화자': dlg.get('speaker', ''),
                '대화내용': dlg.get('text', ''),
                '배경이미지': display_bg,
                '효과': '',
                '타입': 'REFLECTION' if idx == 1 else '',
                '파일경로': str(earth_path) if idx == 1 else ''
            })

# PHILOSOPHY
philo_path = Path('assets/data/dialogues/reflection/philosophy.json')
if philo_path.exists():
    with open(philo_path, 'r', encoding='utf-8') as f:
        philo_data = json.load(f)

    for scene_key, scene_data in philo_data.items():
        dlg_list = scene_data.get('dialogues', [])
        scene_bg = scene_data.get('background', '')

        prev_bg = None
        for idx, dlg in enumerate(dlg_list, 1):
            display_bg = '' if prev_bg == scene_bg else scene_bg
            prev_bg = scene_bg

            dialogues.append({
                '사용처': f'PHILOSOPHY_{scene_key}' if idx == 1 else '',
                'scene_id': scene_key if idx == 1 else '',
                '순서': idx,
                '화자': dlg.get('speaker', ''),
                '대화내용': dlg.get('text', ''),
                '배경이미지': display_bg,
                '효과': '',
                '타입': 'REFLECTION' if idx == 1 else '',
                '파일경로': str(philo_path) if idx == 1 else ''
            })

# ANDROMEDA
andromeda_path = Path('assets/data/dialogues/reflection/andromeda.json')
if andromeda_path.exists():
    with open(andromeda_path, 'r', encoding='utf-8') as f:
        andromeda_data = json.load(f)

    for scene_key, scene_data in andromeda_data.items():
        dlg_list = scene_data.get('dialogues', [])
        scene_bg = scene_data.get('background', '')
        scene_effect = scene_data.get('effect', '')

        prev_bg = None
        for idx, dlg in enumerate(dlg_list, 1):
            display_bg = '' if prev_bg == scene_bg else scene_bg
            prev_bg = scene_bg

            dialogues.append({
                '사용처': f'ANDROMEDA_{scene_key}' if idx == 1 else '',
                'scene_id': scene_key if idx == 1 else '',
                '순서': idx,
                '화자': dlg.get('speaker', ''),
                '대화내용': dlg.get('text', ''),
                '배경이미지': display_bg,
                '효과': scene_effect if idx == 1 else '',
                '타입': 'REFLECTION' if idx == 1 else '',
                '파일경로': str(andromeda_path) if idx == 1 else ''
            })

# BOSS DIALOGUES
boss_dlg_path = Path('assets/data/dialogues/bosses/boss_dialogues.json')
if boss_dlg_path.exists():
    with open(boss_dlg_path, 'r', encoding='utf-8') as f:
        boss_data = json.load(f)

    for boss_id, phases in boss_data.items():
        for phase_name in ['intro', 'defeat']:
            phase_dlgs = phases.get(phase_name, [])
            for idx, dlg in enumerate(phase_dlgs, 1):
                dialogues.append({
                    '사용처': f'BOSS_{phase_name.upper()}_{boss_id}' if idx == 1 else '',
                    'scene_id': f'{boss_id}_{phase_name}' if idx == 1 else '',
                    '순서': idx,
                    '화자': dlg.get('speaker', ''),
                    '대화내용': dlg.get('text', ''),
                    '배경이미지': '',
                    '효과': '',
                    '타입': f'BOSS_{phase_name.upper()}' if idx == 1 else '',
                    '파일경로': str(boss_dlg_path) if idx == 1 else ''
                })

# COMBAT MESSAGES
combat_path = Path('assets/data/dialogues/combat/combat_messages.json')
if combat_path.exists():
    with open(combat_path, 'r', encoding='utf-8') as f:
        combat_data = json.load(f)

    for key, text in combat_data.items():
        dialogues.append({
            '사용처': f'COMBAT_{key}',
            'scene_id': key,
            '순서': 1,
            '화자': 'SYSTEM',
            '대화내용': text,
            '배경이미지': '',
            '효과': '',
            '타입': 'COMBAT',
            '파일경로': str(combat_path)
        })

# BOSS PHASES
boss_phase_path = Path('assets/data/dialogues/combat/boss_phases.json')
if boss_phase_path.exists():
    with open(boss_phase_path, 'r', encoding='utf-8') as f:
        boss_phase_data = json.load(f)

    for boss_id, phases in boss_phase_data.items():
        for phase, text in phases.items():
            dialogues.append({
                '사용처': f'BOSS_PHASE_{boss_id}_{phase}',
                'scene_id': f'{boss_id}_{phase}',
                '순서': 1,
                '화자': 'SYSTEM',
                '대화내용': text,
                '배경이미지': '',
                '효과': '',
                '타입': 'BOSS_PHASE',
                '파일경로': str(boss_phase_path)
            })

# CSV 저장
with open('game_dialogues_all.csv', 'w', encoding='utf-8-sig', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=['사용처', 'scene_id', '순서', '화자', '대화내용', '배경이미지', '효과', '타입', '파일경로'])
    writer.writeheader()
    writer.writerows(dialogues)

print(f'\n총 {len(dialogues)}개 대화 추출 완료 (모든 대화, 최적화 적용)')

# 타입별 통계
type_counts = {}
for dlg in dialogues:
    t = dlg['타입']
    if t:
        type_counts[t] = type_counts.get(t, 0) + 1

print('\n타입별 대화 수:')
for t, cnt in sorted(type_counts.items(), key=lambda x: -x[1]):
    print(f'  {t}: {cnt}')
