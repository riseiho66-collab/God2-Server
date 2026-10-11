"""Preserve classification of existing scoped pet, clock and appearance routes."""
import json

from .archive_inputs import SERVER
from .s2c_world_consumer_frontier import recover


OUT = SERVER / 'artifacts/integration/packet-connections-20261006/s2c-world-consumer-frontier-v10.json'


def main():
    if OUT.exists():
        raise FileExistsError('Preserve prior frontier evidence')
    value = recover()
    value['format'] = 'god2-current-native-s2c-world-consumer-frontier-v10'
    value['supersedes_classification_only'] = 's2c-world-consumer-frontier-v9.json'
    value['new_classification_evidence'] = [
        'src/handlers/RecoveredOwnedCompanions.cpp',
        'src/core/Application.cpp',
        'src/protocol/RecoveredWorldClock.h',
        'src/protocol/RecoveredPlayerAppearanceUpdate.h',
    ]
    value['new_scoped_source_reply_opcodes'] = ['E3', 'FB']
    value['new_scoped_source_push_opcodes'] = ['1A']
    value['new_config_gated_visibility_push_opcodes'] = ['DA']
    OUT.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'artifact': str(OUT), 'counts': value['counts']}))


if __name__ == '__main__':
    main()
