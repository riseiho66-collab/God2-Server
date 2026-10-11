"""Pin current-native FD12 item-definition keys without proposing a producer."""

import hashlib
import json
import struct

import capstone

from .archive_inputs import ArchivedInputs, SERVER
from .packet_connection_inventory import BASE, IMAGE, PIN


OUT = SERVER / 'artifacts/integration/packet-connections-20261006/fd12-item-key-frontier-v2.json'
SLICES = (
    ('fd12_item_definition_lookup_loop', 0x956B0, 0x957E6),
    ('fd12_item_slot_selection', 0x957F0, 0x9592A),
    ('fd12_item_detail_key_selector', 0x96070, 0x960BE),
)


def main():
    if OUT.exists():
        raise FileExistsError('Preserve prior FD12 item-key evidence')
    reader = ArchivedInputs()
    try:
        raw = reader.read(IMAGE)
    finally:
        reader.close()
    if hashlib.sha256(raw).hexdigest() != PIN:
        raise ValueError('Pinned native image changed')
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    slices = []
    for name, start, end in SLICES:
        instructions = list(md.disasm(raw[start:end], BASE + start))
        if not instructions or instructions[0].address != BASE + start or \
                instructions[-1].address + instructions[-1].size != BASE + end:
            raise ValueError('Native slice boundary changed: ' + name)
        body = raw[start:end]
        slices.append({
            'name': name, 'begin_rva': f'{start:X}',
            'end_rva_exclusive': f'{end:X}',
            'sha256': hashlib.sha256(body).hexdigest(),
            'bytes_hex': body.hex(),
            'instructions': [
                {'rva': f'{i.address - BASE:X}',
                 'instruction': f'{i.mnemonic} {i.op_str}'}
                for i in instructions
            ],
        })
    table = raw[0x960C0:0x960E0]
    detail_cases = [f'{struct.unpack_from("<I", table, i * 4)[0] - BASE:X}'
                    for i in range(8)]
    if detail_cases != ['96086', '96090', '9609A', '96086',
                        '960A4', '960AE', '96086', '960AE']:
        raise ValueError('FD12 item-detail selector changed')
    value = {
        'format': 'god2-current-native-fd12-item-key-frontier-v2',
        'native_image': IMAGE, 'native_sha256': PIN,
        'method': 'PINNED_FD12_UI_WORD_ARRAY_ITEM_DEFINITION_LOOKUP',
        'upstream_evidence': 'fd12-e4-panel-frontier-v1.json',
        'logical_item_key_offsets': [4 + 2 * i for i in range(9)],
        'item_key_width': 'u16_le',
        'client_ui_copy_destination': 'UI+26108..26119',
        'native_lookup': 'UI+26108+2*index -> item definition manager+0xCFF70 -> 459A60(key)',
        'lookup_item_definition_fields': ['+0x116 signed WORD', '+0x118 signed WORD'],
        'selection': {
            'routine_rva': '957F0',
            'all_nine_indices_when_ui_flags_equal_one': list(range(9)),
            'alternative_six_index_sets': [[1, 2, 4, 5, 7, 8],
                                           [0, 1, 3, 4, 6, 7]],
            'alternative_three_indices': [1, 4, 7],
            'note': 'Mechanical branch enumeration; UI flag meaning and item offer authority remain unknown.',
        },
        'detail_selector': {
            'routine_rva': '96070',
            'switch_table_rva': '960C0',
            'switch_table_bytes_hex': table.hex(),
            'case_rvas_for_inputs_1_to_8': detail_cases,
        },
        'limits': [
            'The nine WORDs are item-definition keys used by the client UI, not pet attributes.',
            'No current-native server producer, item award, selection mutation, or E4 request/reply causality is proved.',
            'FD12 exact logical length and any trailing payload remain unknown.',
        ],
        'slices': slices,
        'tests_builds_client_execution_deployment': False,
    }
    OUT.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'artifact': str(OUT), 'item_key_slots': 9, 'slices': len(slices)}))


if __name__ == '__main__':
    main()
