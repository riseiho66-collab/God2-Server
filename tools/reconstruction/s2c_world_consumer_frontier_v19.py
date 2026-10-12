"""Retain native rows; add only the qualified independent E6 format class."""
import hashlib
import json
from pathlib import Path

SERVER = Path(__file__).resolve().parents[2]
ROOT = SERVER / 'artifacts/integration/packet-connections-20261006'


def main():
    previous = ROOT / 's2c-world-consumer-frontier-v18.json'
    out = ROOT / 's2c-world-consumer-frontier-v19.json'
    if out.exists():
        raise FileExistsError('Preserve prior frontier evidence')
    original = previous.read_bytes()
    value = json.loads(original)
    ledger_raw = (ROOT / 'packet-route-ledger.json').read_bytes()
    ledger = json.loads(ledger_raw)
    existing = {r['opcode'] for r in value['entries']
                if 'INDEPENDENT_FORMAT_ONLY' in r.get('ledger_classifications', [])}
    current = set(ledger['independent_s2c_format_only'])
    if current - existing != {'E6'} or existing - current:
        raise ValueError('Expected exactly one new independent E6 class')
    rows = [r for r in value['entries'] if r['opcode'] == 'E6']
    if len(rows) != 1:
        raise ValueError('Expected one existing E6 row')
    row = rows[0]
    if (row['dispatch_class'], row['logical_size'], row['length_kind'],
        row['world_dispatch_rva'], row['ledger_classifications']) != (
            'NONDEFAULT', 13, 'fixed', '691EB', []):
        raise ValueError('Pinned E6 row differs')
    row['ledger_classifications'].append('INDEPENDENT_FORMAT_ONLY')
    nondefault = [r for r in value['entries'] if r['dispatch_class'] == 'NONDEFAULT']
    frontier = [r['opcode'] for r in nondefault if not r['ledger_classifications']]
    value['counts']['s2c_nondefault_independent_format_only_opcodes'] = len(current)
    value['counts']['s2c_nondefault_without_route_ledger_classification'] = len(frontier)
    # Prior named increments remain historical observations, retained verbatim.
    value.update(format='god2-current-native-s2c-world-consumer-frontier-v19',
                 method='RETAINED_NATIVE_ROWS_PLUS_INDEPENDENT_E6_DIRECT_COPY_FORMAT',
                 ledger_sha256=hashlib.sha256(ledger_raw).hexdigest(),
                 previous_frontier_sha256=hashlib.sha256(original).hexdigest(),
                 supersedes_classification_only=previous.name,
                 frontier_nondefault_opcodes=frontier,
                 round328_new_independent_format_opcodes=['E6'],
                 round328_new_complete_gameplay_routes=0,
                 round328_classification_evidence=[
                     'src/protocol/RecoveredPetEggStatus.h',
                     'docs/research/tw-native-e6-petegg-input-source-20261012.md'])
    with out.open('x', encoding='utf8') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(dict(artifact=str(out), counts=value['counts'])))


if __name__ == '__main__':
    main()
