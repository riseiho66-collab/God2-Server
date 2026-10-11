"""Preserve S2C classification after native 4D beast-panel consumer join."""
import json

from .archive_inputs import SERVER
from .s2c_world_consumer_frontier import recover


OUT = SERVER / 'artifacts/integration/packet-connections-20261006/s2c-world-consumer-frontier-v9.json'


def main():
    if OUT.exists():
        raise FileExistsError('Preserve prior frontier evidence')
    value = recover()
    value['format'] = 'god2-current-native-s2c-world-consumer-frontier-v9'
    value['supersedes_classification_only'] = 's2c-world-consumer-frontier-v8.json'
    value['new_classification_evidence'] = 'beast-panel-static-contract.json'
    value['new_independent_format_only_opcodes'] = ['4D']
    OUT.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'artifact': str(OUT), 'counts': value['counts']}))


if __name__ == '__main__':
    main()
