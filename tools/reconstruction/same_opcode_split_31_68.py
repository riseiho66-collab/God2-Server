"""Pinned native receive-side split for C2S and S2C opcodes 31/68.

Records table identities and bounded original instructions only. Matching
opcode numbers do not prove a request/reply relation or server authority.
"""
import hashlib
import json
import struct

import capstone

from .archive_inputs import ArchivedInputs, SERVER
from .packet_connection_inventory import IMAGE, PIN, BASE, LENGTH_TABLE, WORLD_TABLE


SLICES = (
    (0x69FA9, 0x69FBB, 'S2C31 dispatch calls companion-row updater AA200'),
    (0x6ABF3, 0x6AC58, 'S2C68 dispatch reads body fields and calls UI 9BED0'),
    (0x9BED0, 0x9BFAF, 'S2C68 UI receiver stores arguments and checks widget 232DD8'),
)


def recover():
    reader = ArchivedInputs()
    try:
        raw = reader.read(IMAGE)
    finally:
        reader.close()
    if hashlib.sha256(raw).hexdigest() != PIN:
        raise ValueError('Pinned mapped image changed')
    table = {}
    for opcode, logical_size, dispatch in ((0x31, 29, 0x69FA9), (0x68, 13, 0x6ABF3)):
        leaf = struct.unpack_from('<I', raw, LENGTH_TABLE+4*opcode)[0]-BASE
        actual_dispatch = struct.unpack_from('<I', raw, WORLD_TABLE+4*opcode)[0]-BASE
        if raw[leaf:leaf+6] != bytes((0xB8,logical_size,0,0,0,0xC3)) or actual_dispatch != dispatch:
            raise ValueError(f'S2C {opcode:02X} length/dispatch changed')
        table[f'{opcode:02X}'] = {
            'length_leaf_rva': f'{leaf:X}', 'logical_size': logical_size,
            'world_dispatch_rva': f'{dispatch:X}', 'default_dispatch': False,
        }
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    slices = []
    for begin, end, purpose in SLICES:
        body = raw[begin:end]
        ins = list(md.disasm(body, BASE+begin))
        if not ins or ins[-1].address+ins[-1].size != BASE+end:
            raise ValueError(f'Unaligned native receive slice {begin:X}')
        slices.append({
            'begin_rva': f'{begin:X}', 'end_rva_exclusive': f'{end:X}',
            'purpose': purpose, 'bytes_hex': body.hex(),
            'sha256': hashlib.sha256(body).hexdigest(),
            'instructions': [
                {'rva': f'{i.address-BASE:X}', 'instruction': f'{i.mnemonic} {i.op_str}'}
                for i in ins
            ],
        })
    return {
        'format': 'god2-current-native-same-opcode-31-68-receive-split-v1',
        'native_image': IMAGE, 'native_sha256': PIN,
        'method': 'PINNED_TABLE_AND_BOUNDED_RECEIVER_DISASSEMBLY',
        's2c': table,
        's2c31': {'consumer_rva': 'AA200', 'source_binding': 'RecoveredDeityState::Status',
                  'request_causality_with_c2s31': 'UNPROVEN'},
        's2c68': {'consumer_rva': '9BED0', 'logical_body_reads':
                  ['WORD +3', 'DWORD +5', 'BYTE +9', 'BYTE +10'],
                  'ui_widget_offset': '232DD8',
                  'request_causality_with_c2s68': 'UNPROVEN'},
        'slices': slices,
        'tests_builds_client_execution_live_mutation': False,
    }


def main():
    out = SERVER/'artifacts/integration/packet-connections-20261006/same-opcode-31-68-receive-split-v1.json'
    if out.exists():
        raise FileExistsError('Preserve prior native evidence')
    out.write_text(json.dumps(recover(), ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(out)


if __name__ == '__main__':
    main()
