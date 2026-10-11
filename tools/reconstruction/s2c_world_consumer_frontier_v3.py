"""Preserve S2C classification after OrangeShop F5/EF field recovery."""
import json

from .archive_inputs import SERVER
from .s2c_world_consumer_frontier import recover


OUT = SERVER/'artifacts/integration/packet-connections-20261006/s2c-world-consumer-frontier-v3.json'


def main():
    if OUT.exists():
        raise FileExistsError('Preserve prior frontier evidence')
    value = recover()
    value['format'] = 'god2-current-native-s2c-world-consumer-frontier-v3'
    value['supersedes_classification_only'] = 's2c-world-consumer-frontier-v2.json'
    value['new_classification_evidence'] = 'bf-ui-list-receivers-v4.json'
    value['new_pending_format_only_opcodes'] = ['EF', 'F5']
    OUT.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'artifact':str(OUT),'counts':value['counts']}))


if __name__ == '__main__':
    main()
