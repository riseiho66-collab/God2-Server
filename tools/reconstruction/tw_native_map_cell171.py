"""Recover TW raw map-cell layouts from full pinned bytes, statically only.

No client, emulation, C++, Lua, SQL, API, build or gameplay test is executed.
Outputs are immutable raw native spans and explicit source-only data facts.
"""
from pathlib import Path
import hashlib
import json
import struct

import capstone

ROOT = Path(__file__).resolve().parents[2]
ARTIFACT = ROOT / 'artifacts/integration/packet-connections-20261006/tw-native-movement-scene-source-01/agents/tw-cell-reader'
IMAGE = ROOT / 'artifacts/research/enemy-blackbox-20261006/consumer-experiment/inputs/native-image.bin'
PIN = '149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
BASE = 0x400000
SPANS = [
    (0x46FF0, 0x470AD, 'map mode0 window / mode2 linked-grid getter', True),
    (0x36B60, 0x36BA6, 'linked-grid raw byte getter and signed bounds', True),
    (0x42B50, 0x42B91, 'attribute index4 initialization DWORD lookup', True),
    (0x102F20, 0x102FE1, 'actual ordinary coordinate probe and zero predicate', True),
    (0x102FE4, 0x103004, 'all eight actual probe direction destinations', False),
    (0x36C30, 0x36F24, 'full linked-grid initialization, raw base layer and dynamic zero overlays', True),
    (0x416B0, 0x41729, 'base/overlay raw tile layer selector getter', True),
    (0x36490, 0x364D6, 'grid owner reset clears actual cell-buffer pointer', True),
    (0x36730, 0x367CA, 'grid owner cleanup frees actual cell-buffer and object list', True),
]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def put(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as stream:
        stream.write(data)


def write_json(path, value):
    put(path, (json.dumps(value, ensure_ascii=True, indent=2) + '\n').encode())


def recover():
    raw = IMAGE.read_bytes()
    if digest(raw) != PIN:
        raise RuntimeError('Pinned full mapped TW input differs')
    ARTIFACT.mkdir(parents=True, exist_ok=True)
    copy = 'native-input/full-mapped-image.bin'
    put(ARTIFACT / copy, raw)
    write_json(ARTIFACT / 'native-input-originals.json', [{
        'path': IMAGE.resolve().as_posix(), 'copy': copy,
        'bytes': len(raw), 'sha256': digest(raw), 'mapped_base': f'{BASE:08X}',
    }])
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    spans = []
    instructions = {}
    for index, (start, end, purpose, is_code) in enumerate(SPANS):
        data = raw[start:end]
        copy = f'native-spans/s{index:02d}-{BASE+start:08X}-{BASE+end:08X}.bin'
        put(ARTIFACT / copy, data)
        decoded = []
        if is_code:
            for instruction in md.disasm(data, BASE + start):
                row = {'rva': f'{instruction.address-BASE:08X}', 'va': f'{instruction.address:08X}',
                       'bytes_hex': instruction.bytes.hex(), 'mnemonic': instruction.mnemonic,
                       'operands': instruction.op_str}
                decoded.append(row)
                instructions[instruction.address] = row
        spans.append({'start_rva': f'{start:08X}', 'end_exclusive_rva': f'{end:08X}',
                      'start_va': f'{BASE+start:08X}', 'end_exclusive_va': f'{BASE+end:08X}',
                      'copy': copy, 'bytes': len(data), 'sha256': digest(data),
                      'purpose': purpose, 'kind': 'instructions' if is_code else 'raw_data',
                      'instructions': decoded})
    write_json(ARTIFACT / 'native-spans.json', spans)
    selected = [
        (0x446FF5, 'actual map mode DWORD at+30'),
        (0x446FFA, 'mode0 selects window branch'),
        (0x446FFC, 'only remaining mode2 delegates to linked grid'),
        (0x447005, 'mode2 grid object pointer map+1030'),
        (0x44701D, 'actual grid getter call VA00436B60 / RVA00036B60'),
        (0x44702F, 'mode0 actual initialization attribute4 lookup'),
        (0x442B7E, 'attribute4 DWORD at map+FDC+4*4 = FEC; pointer type not inferred'),
        (0x44705B, 'window native signed centerX at map+103C'),
        (0x447067, 'window localX DWORD bias21'),
        (0x447073, 'window native signed centerY at map+1040'),
        (0x44707F, 'window localY DWORD bias21'),
        (0x447082, 'signed localX upper bound63'),
        (0x447087, 'signed localY upper bound63'),
        (0x44708C, 'signed localX lower bound0'),
        (0x447090, 'signed localY lower bound0'),
        (0x447096, 'row multiplied64 then subtractrow ->stride63'),
        (0x44709F, 'window actual rawbyte at map+50+row*63+column'),
        (0x436B60, 'grid width signedDWORD+90'),
        (0x436B67, 'grid rawcell buffer pointer+8C'),
        (0x436B76, 'signed gridX upper bound width'),
        (0x436B7A, 'signed gridX lower bound0'),
        (0x436B83, 'grid height signedDWORD+94'),
        (0x436B89, 'signed gridY upper bound height'),
        (0x436B8E, 'signed gridY lower bound0'),
        (0x436B92, 'actual row-major width*y address computation'),
        (0x436B97, 'actual grid rawbyte at pointer+row+column'),
        (0x436C68, 'initializer stores computed actual width'),
        (0x436C6E, 'initializer stores same actual height'),
        (0x436C78, 'initializer actual dim squared allocation size'),
        (0x436C84, 'initializer retains actual allocated cell pointer'),
        (0x436D79, 'base-layer native raw getter'),
        (0x436D8A, 'base-layer rawAL written without normalization'),
        (0x436EA8, 'actual linked-object overlay raw getter'),
        (0x436EAD, 'only raw overlayzero selects overwrite'),
        (0x436EC1, 'actual linked-object overlay writes gridzero'),
        (0x441718, 'tile rawbyte getter does not normalize FE/FF'),
        (0x441723, 'tile invalid fallbackAL1 distinct from grid invalid0'),
        (0x502FCB, 'ordinary probe calls actual map getter'),
        (0x502FD2, 'ordinary probe rejects getterzero'),
        (0x43674D, 'actual cell-buffer cleanup frees retained pointer'),
        (0x436755, 'actual cleanup clears cell-buffer pointer'),
    ]
    sites = [{'rva': f'{va-BASE:08X}', 'va': f'{va:08X}',
              'instruction': instructions[va], 'fact': fact} for va, fact in selected]
    write_json(ARTIFACT / 'native-sites.json', sites)
    directions = [{'index': index, 'cell_rva': f'{0x102FE4+index*4:08X}',
                   'cell_va': f'{BASE+0x102FE4+index*4:08X}',
                   'target_va': f'{struct.unpack_from("<I", raw, 0x102FE4+index*4)[0]:08X}',
                   'raw_hex': raw[0x102FE4+index*4:0x102FE8+index*4].hex()}
                  for index in range(8)]
    write_json(ARTIFACT / 'native-layout-facts.json', {
        'format': 'tw-pinned-native-map-cell-layout-v1', 'input_sha256': PIN,
        'map_getter': {'rva': '00046FF0', 'va': '00446FF0'},
        'grid_getter': {'rva': '00036B60', 'va': '00436B60'},
        'initializer': {'rva': '00036C30', 'va': '00436C30'},
        'native_mode0': {'map_mode_offset': 0x30, 'window_raw_offset': 0x50,
                         'side': 63, 'center_x_offset': 0x103C, 'center_y_offset': 0x1040,
                         'index_bias': 21, 'center_arithmetic': 'DWORD_modular_then_signed_bounds',
                         'initialization_attribute4_offset': 0xFEC,
                         'attribute4_type': 'DWORD_nonzero_qualifier_not_proven_pointer'},
        'native_mode2': {'map_grid_pointer_offset': 0x1030, 'grid_cells_pointer_offset': 0x8C,
                         'grid_signed_width_offset': 0x90, 'grid_signed_height_offset': 0x94,
                         'stride': 'actual_native_width', 'row_major': True},
        'raw_values_preserved': [0, 2, 254, 255],
        'raw_value_meanings_not_inferred': True,
        'initializer_has_dynamic_zero_overlays': True,
        'direction_data': directions,
        'native_invalid_modes_or_bounds_getter_value': 0,
        'source_invalid_or_missing_or_bounds_result': 'nullopt_not_a_fabricated_rawbyte',
        'source_mode0_missing_attr4_result': 'reject_even_though_native_assert_continues',
        'source_requires_full_cell_matrix_and_nonwrapped_retained_address_extent': True,
        'actual_native_resource_current_supplier_still_mandatory': True,
        'no_indoor_outdoor_meaning_inferred_from_mode_numbers': True,
        'new_opcodes': 0, 'complete_bidirectional_routes_added': 0,
        'whole_game_percentage': None, 'source_only': True,
    })
    print(json.dumps({'artifact': ARTIFACT.as_posix(), 'native_spans': len(spans),
                      'native_sites': len(sites), 'input_sha256': PIN,
                      'source_only': True}))


if __name__ == '__main__':
    recover()
