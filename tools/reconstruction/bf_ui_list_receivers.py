"""Bounded current-native S2C receivers supplying the two C2S BF row arrays."""
import hashlib
import json
import struct

import capstone

from .archive_inputs import ArchivedInputs, SERVER
from .packet_connection_inventory import BASE, IMAGE, PIN, LENGTH_TABLE, WORLD_TABLE


OUT = SERVER / 'artifacts/integration/packet-connections-20261006/bf-ui-list-receivers-v4.json'
RECEIVERS = {
    0xee: (0x690ee, 0xcdf90, 0xce131, 'even mode 6-byte source rows'),
    0xf5: (0x69100, 0xce140, 0xce285, 'related fixed UI record, not a row-list source'),
    0xf3: (0x69112, 0xce290, 0xce4f2, 'odd mode compressed 48-byte destination rows'),
    0xef: (0x69124, 0xd19a0, 0xd1a23, 'related 2-byte UI quantity update'),
}


def recover():
    reader = ArchivedInputs()
    try:
        raw = reader.read(IMAGE)
    finally:
        reader.close()
    if hashlib.sha256(raw).hexdigest() != PIN:
        raise ValueError('Pinned native image changed')
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    rows = []
    for opcode, (dispatch, begin, end, purpose) in RECEIVERS.items():
        if struct.unpack_from('<I', raw, WORLD_TABLE + 4 * opcode)[0] - BASE != dispatch:
            raise ValueError(f'World dispatch changed: {opcode:02X}')
        leaf = struct.unpack_from('<I', raw, LENGTH_TABLE + 4 * opcode)[0] - BASE
        leaf_bytes = raw[leaf:leaf + 6]
        logical_size = struct.unpack_from('<i', leaf_bytes, 1)[0] if leaf_bytes[0] == 0xb8 else None
        body = raw[begin:end]
        ins = list(md.disasm(body, BASE + begin))
        if not ins or ins[-1].address + ins[-1].size != BASE + end:
            raise ValueError(f'Unaligned native slice: {opcode:02X}')
        rows.append({
            'opcode': f'{opcode:02X}', 'world_dispatch_rva': f'{dispatch:X}',
            'length_leaf_rva': f'{leaf:X}', 'logical_size': logical_size,
            'consumer_rva': f'{begin:X}', 'consumer_end_rva_exclusive': f'{end:X}',
            'purpose': purpose, 'sha256': hashlib.sha256(body).hexdigest(),
            'bytes_hex': body.hex(),
            'instructions': [{'rva': f'{i.address - BASE:X}',
                              'instruction': f'{i.mnemonic} {i.op_str}'} for i in ins],
        })
    return {
        'format': 'god2-current-native-bf-ui-list-receivers-v4',
        'native_image': IMAGE, 'native_sha256': PIN,
        'method': 'PINNED_LENGTH_WORLD_DISPATCH_AND_BOUNDED_CONSUMER_DISASSEMBLY',
        'receivers': rows,
        'ee': {'header_logical_bytes': 9, 'count_offsets': [5, 6, 8],
               'mode_offset': 7, 'mode_mapping': '1..4 -> even UI 0/2/4/6',
               'rows': '6-byte source rows copied to UI+96980 with stride6',
               'logical_size_formula': '9+6*(count5+count6+count8)'},
        'f3': {'header_logical_bytes': 9, 'count_offsets': [5, 6, 8],
               'mode_offset': 7, 'mode_mapping': '1..4 -> odd UI 1/3/5/7',
               'first_group': 'count5 variable rows: 8-byte prefix with prefix byte4=N, then N u16 and N u8',
               'later_groups': 'count6 and count8 rows of 6 bytes each',
               'destination': 'UI+96BA4 with stride48'},
        'limits': [
            'EE diagnostic length mismatch continues in native; bounded source encoder must use exact formula.',
            'F3 native copy uses a 0x808 local frame; source emission must bound length and UI destination count.',
            'These are input-list provenance for C2S BF, not proof of purchase or server-side ownership.',
            'F5 and EF touch related UI state but do not populate both row arrays.',
        ],
        'builds_tests_client_execution_deployment': False,
    }


def main():
    if OUT.exists():
        raise FileExistsError('Preserve prior native evidence')
    OUT.write_text(json.dumps(recover(), ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(OUT)


if __name__ == '__main__':
    main()
