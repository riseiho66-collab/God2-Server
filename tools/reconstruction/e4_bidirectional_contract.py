"""Pin current-native C2SE4 UI producers and separate S2CE4 consumer.

Static disassembly only; output proves wire shape, not a server operation.
"""
import hashlib
import json
import struct

import capstone

from .archive_inputs import ArchivedInputs, SERVER
from .packet_connection_inventory import IMAGE, PIN, BASE, LENGTH_TABLE, WORLD_TABLE

SLICES = (
    (0x95afe, 0x95b28, 'C2SE4 operation3 producer'),
    (0x95b30, 0x95c53, 'UI control dispatch and operation0/1/2 producers'),
    (0x691c7, 0x691d9, 'S2CE4 world dispatch to4A3180'),
    (0xa3180, 0xa32bc, 'S2CE4 conditional existing-UI-record consumer'),
)
QUEUE_CALLS = (0x95b1b, 0x95bb3, 0x95bfc, 0x95c46)


def recover():
    reader = ArchivedInputs()
    try:
        raw = reader.read(IMAGE)
    finally:
        reader.close()
    if hashlib.sha256(raw).hexdigest() != PIN:
        raise ValueError('Mapped native image changed')
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    slices = []
    for start, end, purpose in SLICES:
        body = raw[start:end]
        ins = list(md.disasm(body, BASE + start))
        if not ins or ins[-1].address + ins[-1].size != BASE + end:
            raise ValueError(f'Unaligned native slice {start:X}')
        slices.append({'rva': f'{start:X}', 'end_rva_exclusive': f'{end:X}',
                       'purpose': purpose, 'sha256': hashlib.sha256(body).hexdigest(),
                       'bytes_hex': body.hex(),
                       'instructions': [{'rva': f'{i.address-BASE:X}',
                                        'instruction': f'{i.mnemonic} {i.op_str}'}
                                       for i in ins]})
    calls = []
    for pc, operation in zip(QUEUE_CALLS, (3, 0, 1, 2)):
        if raw[pc] != 0xe8 or pc + 5 + struct.unpack_from('<i', raw, pc + 1)[0] != 0x132e0:
            raise ValueError(f'E4 producer target changed at {pc:X}')
        calls.append({'queue_call_rva': f'{pc:X}', 'operation': operation,
                      'call_hex': raw[pc:pc+5].hex()})
    leaf = struct.unpack_from('<I', raw, LENGTH_TABLE + 0xe4*4)[0] - BASE
    dispatch = struct.unpack_from('<I', raw, WORLD_TABLE + 0xe4*4)[0] - BASE
    if raw[leaf:leaf+6] != bytes.fromhex('b811000000c3') or dispatch != 0x691c7:
        raise ValueError('S2CE4 length/dispatch changed')
    return {
        'format': 'god2-current-native-bidirectional-e4-static-v1',
        'native_image': IMAGE, 'native_sha256': PIN,
        'method': 'PINNED_BOUNDED_DISASSEMBLY_ONLY',
        'c2s': {'logical_size': 2, 'body': 'one raw operation BYTE',
                'observed_operations': [0, 1, 2, 3], 'queue_calls': calls,
                'client_conditions': 'UI control/state checks at95B30..95C53; these are not server authority'},
        's2c': {'logical_size': 17, 'length_leaf_rva': f'{leaf:X}',
                'world_dispatch_rva': f'{dispatch:X}',
                'consumer': '4A3180 reads original16-byte body and conditionally mutates an existing UI record',
                'c2s_reply_pairing': 'NOT_PROVEN'},
        'slices': slices,
        'open': ['Actual E4 gameplay operation semantics and server authorization',
                 'owned state/source, storage, Lua rules and response causality',
                 'other producer modes and all indirect callers'],
        'tests_builds_client_execution_live_mutation': False,
    }


def main():
    out = SERVER / 'artifacts/integration/packet-connections-20261006/e4-bidirectional-static-v1.json'
    if out.exists():
        raise FileExistsError('Preserve previous native evidence')
    out.write_text(json.dumps(recover(), ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'artifact': str(out), 'method': 'STATIC_SOURCE_ONLY'}))


if __name__ == '__main__':
    main()
