"""Read-only current-native S2C dispatch frontier for packet connection work.

Length-table entries, non-default dispatch and route-ledger classifications are
separate observations. Neither a dispatch entry nor a registered reply opcode
proves a complete bidirectional gameplay route.
"""
import hashlib
import json
import struct

from .archive_inputs import ArchivedInputs, SERVER
from .packet_connection_inventory import IMAGE, PIN, BASE, LENGTH_TABLE, WORLD_TABLE


ROOT = SERVER/'artifacts/integration/packet-connections-20261006'
DEFAULT = 0x6B517


def recover():
    reader = ArchivedInputs()
    try:
        raw = reader.read(IMAGE)
    finally:
        reader.close()
    if hashlib.sha256(raw).hexdigest() != PIN:
        raise ValueError('Pinned current mapped image changed')
    baseline = json.loads((ROOT/'static-packet-index.json').read_text(encoding='utf-8'))
    ledger = json.loads((ROOT/'packet-route-ledger.json').read_text(encoding='utf-8'))
    if baseline['native_sha256'] != PIN:
        raise ValueError('Existing S2C index belongs to another build')
    reviewed = {op for group in ledger['reviewed_world_source_groups'] for op in group['s2c']}
    pending = {op for group in ledger['pending_world_source_groups']
               for op in group.get('s2c_format_only', [])}
    independent = set(ledger.get('independent_s2c_format_only', {}))
    external_bridge = set(ledger.get('external_s2c_bridge_format_only', {}))
    source_push = set(ledger.get('source_s2c_push_branches', {}))
    config_gated_push = set(ledger.get('config_gated_s2c_visibility_push_branches', {}))
    rows = []
    for opcode in range(256):
        existing = baseline['s2c'][opcode]
        if existing['opcode'] != opcode:
            raise ValueError('S2C index order changed')
        if opcode >= 254:
            if existing['length_kind'] != 'unsupported':
                raise ValueError('Unindexed tail changed')
            rows.append({'opcode': f'{opcode:02X}', 'length_kind': 'unsupported',
                         'dispatch_class': 'UNINDEXED_TAIL'})
            continue
        leaf = struct.unpack_from('<I', raw, LENGTH_TABLE+4*opcode)[0]-BASE
        body = raw[leaf:leaf+6]
        if body[0] == 0xB8 and body[5] == 0xC3:
            size = struct.unpack_from('<i', body, 1)[0]
            kind = 'fixed' if size > 0 else 'u16_variable' if size == -2 else 'needs_static_trace'
        elif body[:4] == bytes.fromhex('83c8ffc3'):
            size, kind = -1, 'unsupported'
        else:
            size, kind = None, 'needs_static_trace'
        target = struct.unpack_from('<I', raw, WORLD_TABLE+4*opcode)[0]-BASE
        if leaf != existing['length_leaf_rva'] or size != existing['logical_size'] or \
           target != existing['world_consumer_rva'] or kind != existing['length_kind']:
            raise ValueError(f'S2C table/index disagreement for {opcode:02X}')
        key = f'{opcode:02X}'
        supported = kind in ('fixed', 'u16_variable')
        classifications = ([name for name, found in (
            ('REGISTERED_SOURCE_REPLY_OPCODE', key in reviewed),
            ('PENDING_FORMAT_ONLY', key in pending),
            ('INDEPENDENT_FORMAT_ONLY', key in independent),
            ('GM_TOOL_BRIDGE_FORMAT_ONLY', key in external_bridge),
            ('REGISTERED_SOURCE_PUSH_BRANCH', key in source_push),
            ('CONFIG_GATED_VISIBILITY_PUSH_BRANCH', key in config_gated_push)) if found] if supported else [])
        rows.append({'opcode': key, 'length_kind': kind, 'logical_size': size,
                     'length_leaf_rva': f'{leaf:X}', 'world_dispatch_rva': f'{target:X}',
                     'dispatch_class': 'NONDEFAULT' if supported and target != DEFAULT else
                                       'DEFAULT' if supported else 'UNSUPPORTED',
                     'ledger_classifications': classifications})
    nondefault = [x for x in rows if x['dispatch_class'] == 'NONDEFAULT']
    default = [x for x in rows if x['dispatch_class'] == 'DEFAULT']
    frontier = [x for x in nondefault if not x['ledger_classifications']]
    counts = {
        's2c_supported_length_entries': len(nondefault)+len(default),
        's2c_supported_nondefault_world_dispatch_entries': len(nondefault),
        's2c_supported_default_world_dispatch_entries': len(default),
        's2c_distinct_nondefault_world_dispatch_rvas': len({x['world_dispatch_rva'] for x in nondefault}),
        's2c_nondefault_registered_reply_opcodes': sum('REGISTERED_SOURCE_REPLY_OPCODE' in x['ledger_classifications'] for x in nondefault),
        's2c_nondefault_pending_format_only_opcodes': sum('PENDING_FORMAT_ONLY' in x['ledger_classifications'] for x in nondefault),
        's2c_nondefault_independent_format_only_opcodes': sum('INDEPENDENT_FORMAT_ONLY' in x['ledger_classifications'] for x in nondefault),
        's2c_nondefault_external_tool_bridge_format_only_opcodes': sum('GM_TOOL_BRIDGE_FORMAT_ONLY' in x['ledger_classifications'] for x in nondefault),
        's2c_nondefault_source_push_branch_opcodes': sum('REGISTERED_SOURCE_PUSH_BRANCH' in x['ledger_classifications'] for x in nondefault),
        's2c_nondefault_config_gated_visibility_push_branch_opcodes': sum('CONFIG_GATED_VISIBILITY_PUSH_BRANCH' in x['ledger_classifications'] for x in nondefault),
        's2c_nondefault_without_route_ledger_classification': len(frontier),
    }
    if counts['s2c_supported_length_entries'] != 252 or len(rows) != 256:
        raise ValueError('S2C table size changed')
    return {
        'format': 'god2-current-native-s2c-world-consumer-frontier-v1',
        'native_image': IMAGE, 'native_sha256': PIN,
        'method': 'PINNED_LENGTH_AND_DISPATCH_TABLE_PLUS_CURRENT_ROUTE_LEDGER',
        'ledger_sha256': hashlib.sha256((ROOT/'packet-route-ledger.json').read_bytes()).hexdigest(),
        'baseline_index_sha256': hashlib.sha256((ROOT/'static-packet-index.json').read_bytes()).hexdigest(),
        'counts': counts,
        'frontier_nondefault_opcodes': [x['opcode'] for x in frontier],
        'entries': rows,
        'limits': [
            'Non-default dispatch is not proof of meaningful consumer execution or gameplay effect.',
            'This is the WORLD dispatch table; DEFAULT here does not exclude a consumer in battle, login, or another state.',
            'A registered S2C reply opcode describes at least one reviewed source branch, not all variants.',
            'Unclassified means absent from this route ledger; research may exist in other documents.',
            'No C2S/S2C causal pairing or whole-game completion percentage is inferred.',
        ],
        'tests_builds_client_execution_live_mutation': False,
    }


def main():
    out = ROOT/'s2c-world-consumer-frontier-v1.json'
    if out.exists():
        raise FileExistsError('Preserve prior frontier evidence')
    value = recover()
    out.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'artifact': str(out), 'counts': value['counts']}))


if __name__ == '__main__':
    main()
