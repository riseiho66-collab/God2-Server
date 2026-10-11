"""Pin the current-native S2C BE list / BF indexed-update consumer dependency.

This is static native source accounting. It does not assert that C2S BF causes
either S2C packet, nor recover server-side shop transaction authority.
"""
import hashlib
import json
import struct

import capstone

from .archive_inputs import ArchivedInputs, SERVER
from .packet_connection_inventory import IMAGE, PIN, BASE, LENGTH_TABLE, WORLD_TABLE


SLICES = (
    (0x6b219, 0x6b238, 'S2C BE and BF world table branches'),
    (0x72560, 0x7267b, 'S2C BE establishes one region and copies count rows'),
    (0x72680, 0x727a3, 'S2C BF updates one existing region/slot row'),
)


def recover():
    reader = ArchivedInputs()
    try:
        raw = reader.read(IMAGE)
    finally:
        reader.close()
    if hashlib.sha256(raw).hexdigest() != PIN:
        raise ValueError('Native mapped image changed')
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    slices = []
    for start, end, purpose in SLICES:
        body = raw[start:end]
        instructions = list(md.disasm(body, BASE + start))
        if not instructions or instructions[-1].address + instructions[-1].size != BASE + end:
            raise ValueError(f'Unaligned S2C panel slice {start:X}')
        slices.append({'rva': f'{start:X}', 'end_rva_exclusive': f'{end:X}',
                       'purpose': purpose, 'sha256': hashlib.sha256(body).hexdigest(),
                       'bytes_hex': body.hex(),
                       'instructions': [{'rva': f'{ins.address-BASE:X}',
                                        'instruction': f'{ins.mnemonic} {ins.op_str}'}
                                       for ins in instructions]})
    leaves = {}
    for opcode, expected_leaf, expected_code, expected_world in (
        (0xbe, 0x1318, bytes.fromhex('b8feffffffc3'), 0x6b219),
        (0xbf, 0x12fa, bytes.fromhex('b81d000000c3'), 0x6b22b),
    ):
        leaf = struct.unpack_from('<I', raw, LENGTH_TABLE + opcode*4)[0] - BASE
        world = struct.unpack_from('<I', raw, WORLD_TABLE + opcode*4)[0] - BASE
        if leaf != expected_leaf or raw[leaf:leaf+6] != expected_code or world != expected_world:
            raise ValueError(f'S2C {opcode:02X} length or dispatch changed')
        leaves[f'{opcode:02X}'] = {'length_leaf_rva': f'{leaf:X}',
                                  'length_leaf_bytes_hex': raw[leaf:leaf+6].hex(),
                                  'world_dispatch_rva': f'{world:X}'}
    return {
        'format': 'god2-current-native-s2c-be-bf-panel-static-v2',
        'native_image': IMAGE, 'native_sha256': PIN,
        'method': 'PINNED_BOUNDED_DISASSEMBLY_ONLY',
        'length_and_dispatch': leaves,
        'be': {
            'logical_size': '5 + 24 * count, variable U16 length',
            'body': 'total logical length U16, row count BYTE, region BYTE, then count 24-byte rows',
            'native_length_relation': 'consumer compares U16-1 with 24*count+4; mismatch takes a diagnostic call and then continues, so the server codec enforces the relation before emission',
            'region_state': 'client state byte +855ED must be 2; region stored +839A4',
            'row_storage': 'region 1200-byte slab at +839CC; 50 rows of 24 bytes',
            'row_copy': 'for each row, signed row byte1 is slot; copies row bytes4..23 into UI slot bytes4..23 and row bytes0..1 into slot bytes0..1',
            'native_bounds_limit': 'row count and signed region/slot are not authoritatively clamped before indexed write in inspected consumer; server emission must guard region0..5, count<=50 and slot0..49 independently'
        },
        'bf': {
            'logical_size': 29,
            'body': 'region BYTE0, raw BYTE1..3, record key BYTE4, slot BYTE5, raw BYTE6..7, row payload20 bytes at8..27',
            'prerequisite': 'client state byte +855ED ==2 and region equals last stored +839A4',
            'slot_update': 'signed region and slot index into same 50x24-per-region store; copies body8..27 to row4..23 and body4/5 to row0/1',
            'native_bounds_limit': 'diagnostic branches for invalid region/slot do not themselves prevent subsequent write; server must guard region0..5 and slot0..49'
        },
        'c2s_bf_to_s2c_be_bf_causality': 'NOT_PROVEN',
        'slices': slices,
        'tests_builds_client_execution_live_mutation': False,
    }


def main():
    out = SERVER / 'artifacts/integration/packet-connections-20261006/bf-s2c-panel-static-v2.json'
    if out.exists():
        raise FileExistsError('Preserve prior native evidence')
    out.write_text(json.dumps(recover(), ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'artifact': str(out), 'method': 'STATIC_SOURCE_ONLY'}))


if __name__ == '__main__':
    main()
