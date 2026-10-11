"""Preserve S2C classification after world-pool and source-push alignment."""
import json

from .archive_inputs import SERVER
from .s2c_world_consumer_frontier import recover


OUT = SERVER/'artifacts/integration/packet-connections-20261006/s2c-world-consumer-frontier-v6.json'


def main():
    if OUT.exists():
        raise FileExistsError('Preserve prior frontier evidence')
    value = recover()
    value['format'] = 'god2-current-native-s2c-world-consumer-frontier-v6'
    value['supersedes_classification_only'] = 's2c-world-consumer-frontier-v5.json'
    value['new_classification_evidence'] = 'docs/research/current-world-pool-removal-and-source-push-20261006.md'
    value['new_independent_format_only_opcodes'] = ['74', '75']
    value['existing_source_push_opcodes_newly_registered'] = ['71', '72', '78']
    value['existing_config_gated_visibility_push_opcodes_newly_registered'] = ['5E', '6F', '73']
    OUT.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'artifact': str(OUT), 'counts': value['counts']}))


if __name__ == '__main__':
    main()
