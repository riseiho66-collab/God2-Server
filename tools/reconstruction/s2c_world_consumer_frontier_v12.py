"""Preserve classification of existing saved role and vital WORLD pushes."""
import json

from .archive_inputs import SERVER
from .s2c_world_consumer_frontier import recover


OUT = SERVER / 'artifacts/integration/packet-connections-20261006/s2c-world-consumer-frontier-v12.json'


def main():
    if OUT.exists():
        raise FileExistsError('Preserve prior frontier evidence')
    value = recover()
    value['format'] = 'god2-current-native-s2c-world-consumer-frontier-v12'
    value['supersedes_classification_only'] = 's2c-world-consumer-frontier-v11.json'
    value['new_classification_evidence'] = [
        'src/handlers/RecoveredPlayerSnapshot.cpp',
        'src/protocol/RecoveredRoleLevel.h',
        'src/protocol/RecoveredRoleVitals.h',
        'src/core/Application.cpp',
    ]
    value['new_saved_player_source_push_opcodes'] = ['22', '24']
    value['overlapping_existing_reply_opcode'] = ['22']
    OUT.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'artifact': str(OUT), 'counts': value['counts']}))


if __name__ == '__main__':
    main()
