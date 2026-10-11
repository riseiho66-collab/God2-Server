"""Cross-check live offline-engine evidence, not pixels or monster values."""
import argparse
import hashlib
import json
from pathlib import Path

from .current_offline_entry_bridge import loop_trampoline

ROOT = Path(__file__).resolve().parents[2]
TRANSPORT = ('connect', 'WSAConnect', 'send', 'recv', 'sendto', 'recvfrom',
             'WSASend', 'WSARecv', 'WSASendTo', 'WSARecvFrom')
ORDER = ('ALTERNATE_WORLD_ENTRY', 'WORLD_CONSTRUCTOR', 'WORLD_INITIALIZER',
         'INITIAL_ACTOR_DISPATCH', 'LOCAL_NULL_INPUT_BRANCH', 'SCENE_ENTRY',
         'SCENE_RETURN_TO_WORLD_INITIALIZER', 'EXPERIMENT_CALL_RETURN',
         'WORLD_LOOP_ENTRY', 'WORLD_DISPATCH_ENTRY')


def audit_payload(report):
    errors = []
    events = report.get('events', [])
    stages = [event for event in events if 'stage' in event]
    labels = [event['stage'] for event in stages]
    if report.get('result') != 'THREE_NATIVE_FRAME_PRESENTATION_RETURNS':
        errors.append('Native loop completion marker absent')
    if labels[:len(ORDER)] != list(ORDER):
        errors.append('Original initialization/scene/loop ordering differs')
    if (report.get('network_policy') != 'STOP_BEFORE_TRANSPORT_API' or
            any(event.get('transport_api') for event in events)):
        errors.append('Transport guard or zero-attempt condition failed')
    armed = report.get('armed', '').lower()
    if not all('ws2_32!' + api.lower() in armed for api in TRANSPORT):
        errors.append('Transport breakpoint coverage incomplete')
    prerequisites = report.get('offline_prerequisites', {})
    if prerequisites.get('connected_flags') != [0, 0] or prerequisites.get('prior_world') != 0:
        errors.append('Cold disconnected application evidence absent')
    if not report.get('entry_patch_restored') or not report.get('executable_disk_unchanged'):
        errors.append('Intervention restoration evidence absent')
    if 'hr=0 written=4' not in report.get('timer_restore', ''):
        errors.append('Timer binding restoration incomplete')
    loop = report.get('loop_intervention', {})
    if loop.get('hex') != loop_trampoline().hex() or loop.get('protection') != 'PAGE_EXECUTE_READ':
        errors.append('Loop thunk identity/protection differs')
    returned = report.get('local_world_return', {})
    world = returned.get('world')
    if not world or returned.get('eax') != 1 or returned.get('esp') != report.get('events_start_sp'):
        errors.append('World return/stack contract differs')
    if not report.get('native_scene_call_returned'):
        errors.append('Native scene return evidence absent')
    for event in stages:
        if event.get('pid') != report.get('client_pid'):
            errors.append('Stage belongs to another process')
            break
        if event['stage'] in ('WORLD_CONSTRUCTOR', 'WORLD_INITIALIZER', 'SCENE_ENTRY') and event.get('ecx') != world:
            errors.append('World ownership changed across native stages')
            break
        if event['stage'] == 'INITIAL_ACTOR_DISPATCH' and event.get('initializer_first_argument') != 0:
            errors.append('Actor dispatch was not the NULL-input branch')
            break
    if len({event.get('tid') for event in stages}) != 1:
        errors.append('Native stages changed threads')
    phase, completed = 0, 0
    for event in stages[len(ORDER):]:
        label = event['stage']
        if label == 'WORLD_FRAME_HEAD':
            continue
        if phase == 0 and label == 'WORLD_FRAME_RETURN' and event.get('eax') == 3:
            phase = 1
        elif phase == 1 and label in ('PRESENTATION_COM_CALL', 'PRESENTATION_WRAPPER_CALL'):
            phase = 2
        elif phase == 2 and label == 'PRESENTATION_RETURN' and event.get('eax') == 0:
            phase = 0
            completed += 1
        else:
            errors.append('Frame/presentation order or native return code differs')
            break
    if phase or completed < 3 or any(report.get(key) != completed for key in
            ('native_frame_returns', 'native_presentation_calls', 'native_presentation_returns')):
        errors.append('Repeated frame/presentation counts disagree')
    return {'native_offline_scene_loop_verified': not errors, 'errors': errors,
            'completed_frame_presentations': completed, 'visible_nonblank_world_verified': False,
            'playable_single_player_verified': False, 'original_monster_values_recovered': 0,
            'scope': 'Original live scene initialization and repeated native frame/presentation calls only'}


def review(run):
    run = Path(run).resolve(strict=True)
    if run.parent != (ROOT / 'artifacts/runs').resolve():
        raise ValueError('Expected one existing isolated run directory')
    result_path = run / 'offline-result.json'
    report = json.loads(result_path.read_text(encoding='utf-8'))
    result = audit_payload(report)
    log = run / (run.name + '-native.log')
    if hashlib.sha256(log.read_bytes()).hexdigest() != report.get('native_sha256'):
        result['errors'].append('Raw native log hash mismatch')
        result['native_offline_scene_loop_verified'] = False
    for event in report.get('events', []):
        for memory in event.get('memory_files', []):
            path = Path(memory['path']).resolve(strict=True)
            if path.parent != run or path.stat().st_size != memory['length'] or hashlib.sha256(path.read_bytes()).hexdigest() != memory['sha256']:
                result['errors'].append('Runtime memory evidence identity differs')
                result['native_offline_scene_loop_verified'] = False
    result['result_sha256'] = hashlib.sha256(result_path.read_bytes()).hexdigest()
    result['run'] = str(run)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run', type=Path)
    args = parser.parse_args()
    result = review(args.run)
    output = args.run / 'offline-verification.json'
    output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result))
    raise SystemExit(0 if result['native_offline_scene_loop_verified'] else 1)
