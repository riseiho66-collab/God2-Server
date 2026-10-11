"""Preserve S2C classification after eight external GM-tool bridge cases."""
import json

from .archive_inputs import SERVER
from .s2c_world_consumer_frontier import recover


OUT = SERVER/'artifacts/integration/packet-connections-20261006/s2c-world-consumer-frontier-v5.json'


def main():
    if OUT.exists():
        raise FileExistsError('Preserve prior frontier evidence')
    value = recover()
    value['format'] = 'god2-current-native-s2c-world-consumer-frontier-v5'
    value['supersedes_classification_only'] = 's2c-world-consumer-frontier-v4.json'
    value['new_classification_evidence'] = 's2c-gm-tool-bridge-v1.json'
    value['new_external_tool_bridge_format_only_opcodes'] = ['7B', '7C', '7D', '7E', '7F', '80', '81', 'F6']
    OUT.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'artifact': str(OUT), 'counts': value['counts']}))


if __name__ == '__main__':
    main()
