"""Repeatable local-file experiment; not a live offline-world implementation."""
import argparse
from collections import Counter
import json
from pathlib import Path

from .current_monster_resource_initialization import NativeMonsterResourceInitialization, ASSETS
from .current_monster_side_initialization import IMAGE_SHA256, ENEMY_ROW_SHA, FIGHT_SHA


def run_case(side):
    native = NativeMonsterResourceInitialization(side)
    resource = native.continue_resource()
    defaults = native.inspect_local_vital_defaults()
    creation = native.continue_actor_creation()
    result = {
        'resource': resource, 'creation': creation,
        'asset_raw_sha256': ASSETS[side][1], 'asset_decoded_sha256': ASSETS[side][2],
        'native_file_opens': native.opens,
        'explicit_diagnostic_participant_record_hex': native.prefix['packet_hex'],
        'default_initializer_separate_islands': {
            'caller_arrays': defaults['arrays'], 'result_raw_words': defaults['result'],
            'native_monster_values': False},
        'creation_visits': {f'{pc:06X}': count for pc, count in native.creation_visits.items()},
        'actor_write_sites': {f'{pc:06X}': count for pc, count in
                              Counter(event[0] for event in native.creation_writes).items()},
        'capabilities': dict.fromkeys(('constitution', 'strength', 'intelligence', 'speed',
                                      'physical_attack', 'physical_defense',
                                      'magical_attack', 'magical_defense', 'hp', 'mp')),
    }
    return native, result


def build_report():
    return {
        'schema': 'current-offline-monster-probe-v1',
        'image_sha256': IMAGE_SHA256, 'enemy_row_sha256': ENEMY_ROW_SHA,
        'fight_table_sha256': FIGHT_SHA,
        'scope': 'Original file loader and retained normal-participant reset/create prefix in Unicorn',
        'network_backend': None, 'live_client_launched': False,
        'all_packets_disabled_in_live_client': False,
        'synthetic_1c_identity_metadata_used': True,
        'stat_update_packets_supplied': [], 'live_offline_world_entered': False,
        'original_stat_values_recovered': 0, 'production_db_modified': False,
        'cases': [run_case(side)[1] for side in (0, 1)],
        'boundary': 'Ends at11602A before participant attachments, display finalization, '
                    'world loop and combat. Does not establish whole-client data absence.',
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    report = build_report()
    serialized = json.dumps(report, indent=2, sort_keys=True) + '\n'
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(serialized, encoding='utf-8')
        print(json.dumps({'report': str(args.output.resolve()),
                          'original_stat_values_recovered': 0,
                          'live_offline_world_entered': False}))
    else:
        print(serialized, end='')


if __name__ == '__main__':
    main()
