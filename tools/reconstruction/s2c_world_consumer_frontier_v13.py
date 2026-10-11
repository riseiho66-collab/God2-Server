"""Append blacklist reply classifications; preserve all original native rows."""
import hashlib
import json
from pathlib import Path

SERVER = Path(__file__).resolve().parents[2]
ROOT = SERVER / 'artifacts/integration/packet-connections-20261006'


def main():
    previous = ROOT / 's2c-world-consumer-frontier-v12.json'
    out = ROOT / 's2c-world-consumer-frontier-v13.json'
    if out.exists():
        raise FileExistsError('Preserve prior frontier evidence')
    original = previous.read_bytes()
    value = json.loads(original)
    ledger_raw = (ROOT / 'packet-route-ledger.json').read_bytes()
    ledger = json.loads(ledger_raw)
    registered = {op for row in ledger['reviewed_world_source_groups'] for op in row['s2c']}
    existing = {row['opcode'] for row in value['entries']
                if 'REGISTERED_SOURCE_REPLY_OPCODE' in row.get('ledger_classifications', [])}
    if registered - existing != {'A4', 'A5'} or existing - registered:
        raise ValueError('Expected only two new scoped blacklist reply classifications')
    changed = []
    for row in value['entries']:
        if row['opcode'] in ('A4', 'A5'):
            if row['dispatch_class'] != 'NONDEFAULT':
                raise ValueError('Original blacklist consumer classification changed')
            row['ledger_classifications'].insert(0, 'REGISTERED_SOURCE_REPLY_OPCODE')
            changed.append(row['opcode'])
    if sorted(changed) != ['A4', 'A5']:
        raise ValueError('Original blacklist rows missing')
    nondefault = [row for row in value['entries'] if row['dispatch_class'] == 'NONDEFAULT']
    frontier = [row['opcode'] for row in nondefault if not row['ledger_classifications']]
    value['counts']['s2c_nondefault_registered_reply_opcodes'] = sum(
        'REGISTERED_SOURCE_REPLY_OPCODE' in row['ledger_classifications'] for row in nondefault)
    value['counts']['s2c_nondefault_without_route_ledger_classification'] = len(frontier)
    value.update(format='god2-current-native-s2c-world-consumer-frontier-v13',
                 method='RETAINED_PINNED_NATIVE_ROWS_PLUS_TWO_SCOPED_BLACKLIST_REPLY_CLASSIFICATIONS',
                 ledger_sha256=hashlib.sha256(ledger_raw).hexdigest(),
                 supersedes_classification_only=previous.name,
                 previous_frontier_sha256=hashlib.sha256(original).hexdigest(),
                 frontier_nondefault_opcodes=frontier,
                 new_scoped_reply_opcodes=['A4', 'A5'],
                 new_complete_gameplay_routes=0,
                 new_classification_evidence=['src/handlers/OwnedBlacklistService.cpp',
                     'src/core/Application.cpp', 'docs/research/tw-native-blacklist-authority-source-20261010.md'])
    with out.open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'artifact': str(out), 'counts': value['counts']}))


if __name__ == '__main__':
    main()
