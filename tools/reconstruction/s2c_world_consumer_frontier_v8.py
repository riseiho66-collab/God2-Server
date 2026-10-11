"""Preserve S2C classification after 59/5A/5B/79 consumer recovery."""
import json

from .archive_inputs import SERVER
from .s2c_world_consumer_frontier import recover


OUT = SERVER/'artifacts/integration/packet-connections-20261006/s2c-world-consumer-frontier-v8.json'


def main():
    if OUT.exists():
        raise FileExistsError('Preserve prior frontier evidence')
    value = recover()
    value['format'] = 'god2-current-native-s2c-world-consumer-frontier-v8'
    value['supersedes_classification_only'] = 's2c-world-consumer-frontier-v7.json'
    value['new_classification_evidence'] = 's2c-text-npc-595a5b79-v1.json'
    value['new_independent_format_only_opcodes'] = ['59','5A','5B','79']
    OUT.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'artifact':str(OUT),'counts':value['counts']}))


if __name__=='__main__':main()
