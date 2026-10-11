"""Preserve S2C classification after FD subtype12 E4 UI offer recovery."""
import json

from .archive_inputs import SERVER
from .s2c_world_consumer_frontier import recover


OUT = SERVER/'artifacts/integration/packet-connections-20261006/s2c-world-consumer-frontier-v7.json'


def main():
    if OUT.exists():
        raise FileExistsError('Preserve prior frontier evidence')
    value = recover()
    value['format'] = 'god2-current-native-s2c-world-consumer-frontier-v7'
    value['supersedes_classification_only'] = 's2c-world-consumer-frontier-v6.json'
    value['new_classification_evidence'] = 'fd12-e4-panel-frontier-v1.json'
    value['new_pending_format_only_variant'] = {'opcode': 'FD', 'subtype': 12,
                                                'scope': 'UPSTREAM_E4_UI_STATE_NOT_CAUSAL_REPLY'}
    OUT.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'artifact': str(OUT), 'counts': value['counts']}))


if __name__ == '__main__':
    main()
