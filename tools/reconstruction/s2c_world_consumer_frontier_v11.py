"""Preserve classification of existing saved-role and saved-journal pushes."""
import json

from .archive_inputs import SERVER
from .s2c_world_consumer_frontier import recover


OUT = SERVER / 'artifacts/integration/packet-connections-20261006/s2c-world-consumer-frontier-v11.json'


def main():
    if OUT.exists():
        raise FileExistsError('Preserve prior frontier evidence')
    value = recover()
    value['format'] = 'god2-current-native-s2c-world-consumer-frontier-v11'
    value['supersedes_classification_only'] = 's2c-world-consumer-frontier-v10.json'
    value['new_classification_evidence'] = [
        'src/core/Application.cpp',
        'src/db/SqliteRoleAuxiliaryRepository.cpp',
        'src/protocol/RecoveredRoleAuxiliary.h',
        'src/db/SqliteQuestJournalRepository.cpp',
        'src/protocol/RecoveredQuestSync.h',
    ]
    value['new_saved_state_source_push_opcodes'] = ['2C', 'DB']
    OUT.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'artifact': str(OUT), 'counts': value['counts']}))


if __name__ == '__main__':
    main()
