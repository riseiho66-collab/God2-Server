"""Review actual constructor evidence without promoting display/default stats."""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from .current_offline_monster_live import ACTOR_SIZE, STAGES, call_page, identity_record, text_init_page
from .current_offline_run_review import ORDER, ROOT, TRANSPORT


def audit_payload(report):
    errors = []
    probe = report.get('monster_probe', {})
    events = report.get('events', [])
    stages = [event for event in events if 'stage' in event]
    labels = [event['stage'] for event in stages]
    expected = (list(ORDER[:8]) + ['MONSTER_TEXT_BIND_ENTRY', 'MONSTER_TEXT_BIND_RETURN']
                + [STAGES[i][1] for i in sorted(STAGES)] + ['MONSTER_CALL_RETURN'])
    if labels != expected or report.get('result') != 'NATIVE_MONSTER_CONSTRUCTOR_RETURNED':
        errors.append('Full original constructor ordered return not observed')
    if any(e.get('transport_api') for e in events) or report.get('network_policy') != 'STOP_BEFORE_TRANSPORT_API':
        errors.append('Transport guard failed')
    if not all('ws2_32!' + api.lower() in report.get('armed', '').lower() for api in TRANSPORT):
        errors.append('Transport API breakpoint coverage incomplete')
    if (not report.get('entry_patch_restored') or not report.get('executable_disk_unchanged') or
            'hr=0 written=4' not in report.get('timer_restore', '')):
        errors.append('Owned-process patch restoration not established')
    if any(e.get('pid') != report.get('client_pid') for e in stages) or len({e.get('tid') for e in stages}) != 1:
        errors.append('Original stages changed process/thread')
    expected_pc = {label: 0x400000 + rva for rva, label in STAGES.values()}
    if any(e.get('pc') != expected_pc[e['stage']] for e in stages if e['stage'] in expected_pc):
        errors.append('Native stage instruction address differs')
    try:
        page = probe['call_page']
        blob, trap = call_page(page['address'], probe['battle'], probe['side'])
        if (page['hex'] != blob.hex() or page['return_trap'] != page['address'] + trap or
                page['protection'] != 'PAGE_EXECUTE_READ' or
                probe['record_hex'] != identity_record(probe['side']).hex()):
            errors.append('Diagnostic call/input differs')
        binding = probe['text_init']
        text_blob, text_trap = text_init_page(probe['manager'], binding['display'], binding['owner'], binding['gui_handle'])
        if (binding['page']['hex'] != text_blob.hex() or
                binding['page']['return_trap'] != binding['page']['address'] + text_trap or
                binding['page']['protection'] != 'PAGE_EXECUTE_READ' or
                binding['observed_bindings'] != [binding['display'], probe['bindings']['renderer'],
                    binding['owner'], probe['bindings']['game_data'], binding['gui_handle']]):
            errors.append('Native text binding evidence differs')
    except (KeyError, ValueError, TypeError):
        errors.append('Diagnostic call identity absent')
    if (probe.get('stat_update_records_supplied') != 0 or probe.get('return_eax') != 1 or
            not stages or stages[-1].get('sp') != probe.get('entry_sp')):
        errors.append('Native return stack/result or no-stat-input evidence differs')
    returned = report.get('local_world_return', {})
    prerequisites = report.get('offline_prerequisites', {})
    if (returned.get('eax') != 1 or returned.get('world') != probe.get('world') or
            returned.get('esp') != report.get('events_start_sp') or
            prerequisites.get('connected_flags') != [0, 0] or prerequisites.get('prior_world') != 0 or
            not report.get('native_scene_call_returned')):
        errors.append('Cold offline world entry evidence differs')
    if any(e.get('initializer_first_argument') != 0 for e in stages if e['stage'] == 'INITIAL_ACTOR_DISPATCH'):
        errors.append('Offline NULL-input branch not established')
    return {'native_monster_constructor_completed': not errors, 'errors': errors,
            'original_attack_defense_values_recovered': 0, 'original_four_attribute_values_recovered': 0,
            'combat_calculation_verified': False, 'playable_single_player_verified': False,
            'scope': 'Full live identity-only native constructor, not original species capability recovery'}


def review(run):
    run = Path(run).resolve(strict=True)
    if run.parent != (ROOT / 'artifacts/runs').resolve():
        raise ValueError('Expected isolated existing run directory')
    result_path = run / 'offline-result.json'
    report = json.loads(result_path.read_text(encoding='utf-8'))
    result = audit_payload(report)
    log = run / (run.name + '-native.log')
    if hashlib.sha256(log.read_bytes()).hexdigest() != report.get('native_sha256'):
        result['errors'].append('Native debugger log hash differs')
    snapshots = list(report.get('monster_probe', {}).get('memory_files', []))
    for event in report.get('events', []):
        snapshots += event.get('memory_files', [])
    for item in snapshots:
        path = Path(item['path']).resolve(strict=True)
        if (path.parent != run or path.stat().st_size != item['length'] or
                hashlib.sha256(path.read_bytes()).hexdigest() != item['sha256']):
            result['errors'].append('Runtime snapshot identity differs')
    before_path, after_path = run / 'monster-before.bin', run / 'monster-stage-368.bin'
    if before_path.is_file() and after_path.is_file():
        before, after = before_path.read_bytes(), after_path.read_bytes()
        if len(before) != ACTOR_SIZE or len(after) != ACTOR_SIZE:
            result['errors'].append('Native actor size differs')
        else:
            result['changed_byte_offsets'] = [i for i in range(ACTOR_SIZE) if before[i] != after[i]]
            result['known_hp_mp_before_raw_u32'] = struct.unpack_from('<4I', before, 0xde8)
            result['known_hp_mp_after_raw_u32'] = struct.unpack_from('<4I', after, 0xde8)
            result['vital_values_are_original_species_authority'] = False
    else:
        result['errors'].append('Complete before/after actor evidence absent')
    result['native_monster_constructor_completed'] = not result['errors']
    result.update(run=str(run), result_sha256=hashlib.sha256(result_path.read_bytes()).hexdigest())
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run', type=Path)
    args = parser.parse_args()
    result = review(args.run)
    (args.run / 'monster-verification.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result))
    raise SystemExit(0 if result['native_monster_constructor_completed'] else 1)
