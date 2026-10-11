"""One current MBD/MBDZ pair and its native block reader; JSON stdout only.

No resource preload, host file writes, live client, or monster-stat promotion.
Only CRT seek/read returns are adapted during bounded original-code execution.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from .omega_assets import decode_csvz
from .current_battle_entry import NativeRun, BASE, SP, RETURN
from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_ESP

ROOT = Path(__file__).resolve().parents[2]
CLIENT = ROOT.parent / 'God2'
IMAGE = ROOT / 'artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin'
IMAGE_SHA = '149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
PLAIN = CLIENT / 'Data2/map/island01/island01.mbd'
PACKED = CLIENT / 'Data2/map/island01/Island01.mbdZ'
PLAIN_SHA = 'b574654e5859e048ea0047c0de36b70addc5e90f2349b9796016ea6792f75f80'
PACKED_SHA = '0edf2048eaf0964caa2c373d66b4c1e6129ebeca265c4a63326436c13e6e0a1f'
MAX_BYTES = 4 << 20
CELL_SIZE, BLOCK_SIDE = 8, 21
BLOCK_BYTES = CELL_SIZE * BLOCK_SIDE * BLOCK_SIDE
SAMPLE_INDICES = (34, 87, 1294)
FIELDS = ('level', 'hp', 'mp', 'constitution', 'strength', 'intelligence', 'speed',
          'physical_attack', 'physical_defense', 'magical_attack', 'magical_defense',
          'metal', 'wood', 'water', 'fire', 'earth', 'base_experience', 'capturable',
          'skill_assignments', 'drop_items', 'drop_rates')
PINS = {PLAIN: (3035748, PLAIN_SHA), PACKED: (735668, PACKED_SHA),
        IMAGE: (3174400, IMAGE_SHA)}
SPANS = {
    'mbd_extension_to_reader': (0x3cf4c, 0x3cf9f,
        '1d9c85a0d66c20cb657c1d6984d60699e129e6f42e872fe5b909396af07045fc'),
    'header_and_index_reader': (0x408e0, 0x40c55,
        '18ac4028ed126a1a645f41d0bd08315a17c5715dc35f6918171abe748a46e132'),
    'block_reader': (0x40790, 0x40829,
        '83f94eaf4f6b5d7cbc96b857d3a0a6647bade04e7637a7391ce5b69e4aa76879'),
    'block_dimensions': (0x3b712, 0x3b747,
        'd17ccdc4eddf2a5adf81ab0d429d226d95bb5e87cd411f2cdb31750298a5e230'),
    'cell_to_tile_lookup': (0x3b795, 0x3b7db,
        '2aee04217e0cf62545289ce8617aa698717686a60b286fae1e90d817d4e627bb'),
    'cell_word_2_use': (0x3b7db, 0x3b83b,
        '27db4070519a6fd751c3b2ba7ef057e7ac5121e559ada0f4e57342fdaee79e99'),
    'tile_lookup': (0x3b1b0, 0x3b1f8,
        '92172c7cefe24b7c695382786870313bf8ae7f7dd55e240358547b6fe214c7d5'),
    'disqualified_hook_callsite': (0x37f17, 0x37f51,
        '1ee71a63f3135315f685114fe879c6c4a23453b8984be5504bbbcd128ddf250c'),
    'empty_native_hook': (0x38790, 0x387a0,
        '499f1f307c1cb989f968a6b7fcaec591e1828877223d0b0e7e8e8b76cde8c9ca'),
    'older_version_dispatch': (0x3d03f, 0x3d062,
        '52be655a4fd841ef56ed2b95e0aa27c0da4939aade394a3d61cb578ccf4b2e71'),
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read_pinned(path):
    path = Path(path)
    if path not in PINS:
        raise ValueError('Only the fixed current MBD pair and image may be opened')
    for part in (path, *path.parents):
        attributes = getattr(part.lstat(), 'st_file_attributes', 0)
        if part.is_symlink() or attributes & 0x400:
            raise ValueError('Reparse source rejected')
    size, expected = PINS[path]
    if path.stat().st_size != size or size > MAX_BYTES:
        raise ValueError('Pinned source size changed')
    with path.open('rb') as stream:
        raw = stream.read(size + 1)
    if len(raw) != size or sha(raw) != expected:
        raise ValueError('Pinned source hash changed')
    return raw


def parse_mbd(raw):
    """Strict packed-block profile, not a universal parser for every MBD version."""
    if not isinstance(raw, bytes) or not 16 <= len(raw) <= MAX_BYTES:
        raise ValueError('MBD byte bound')
    if raw[:8] != b'MBD v1.2':
        raise ValueError('Only the observed MBD v1.2 profile is qualified')
    width, height = struct.unpack_from('<II', raw, 8)
    if not 1 <= width <= 128 or not 1 <= height <= 128:
        raise ValueError('MBD block dimensions outside analysis bound')
    end = 16 + width * height * 4
    if end > len(raw):
        raise ValueError('Truncated MBD offset table')
    offsets = struct.unpack_from(f'<{width * height}I', raw, 16)
    cursor, present = end, 0
    for offset in offsets:
        if offset == 0:
            continue
        if offset != cursor or offset + BLOCK_BYTES > len(raw):
            raise ValueError('Nonpacked, overlapping or truncated MBD block')
        cursor += BLOCK_BYTES
        present += 1
    if cursor != len(raw):
        raise ValueError('Unaccounted MBD bytes')
    return {'width': width, 'height': height, 'offsets': offsets,
            'index_end': end, 'present_blocks': present,
            'absent_blocks': len(offsets) - present}


def native_evidence(image):
    if sha(image) != IMAGE_SHA:
        raise ValueError('Pinned image changed')
    spans = {}
    for name, (start, end, expected) in SPANS.items():
        if sha(image[start:end]) != expected:
            raise ValueError('Pinned native span changed: ' + name)
        spans[name] = {'start_rva': start, 'end_rva_exclusive': end, 'sha256': expected}
    if image[0x38790:0x387a0] != b'\xc3' + b'\x90' * 15:
        raise ValueError('Empty native hook changed')
    literals = []
    for rva, value, operand in (
            (0x187d1c, b'.mbd', 0x3cf51),
            (0x18816c, b'MBD', 0x40b02),
            (0x187be4, b'nTileIdx<m_nTotalTile', 0x3b1cb),
            (0x187bfc, b'x>=0 && x<m_MBDHead.m_nMapW && y>=0 && y<m_MBDHead.m_nMapH', 0x407c9)):
        if (image[rva:rva + len(value) + 1] != value + b'\0'
                or struct.unpack_from('<I', image, operand)[0] != BASE + rva):
            raise ValueError('Native literal binding changed')
        literals.append({'rva': rva, 'ascii': value.decode('ascii'), 'operand_rva': operand})
    calls = []
    for rva, target in ((0x3cf9a, 0x408e0), (0x40acf, 0x14785c),
                        (0x40ba8, 0x14785c), (0x3b7b1, 0x40790),
                        (0x3b7ce, 0x3b1b0), (0x37f24, 0x40790),
                        (0x37f4c, 0x38790)):
        if image[rva] != 0xe8 or rva + 5 + struct.unpack_from('<i', image, rva + 1)[0] != target:
            raise ValueError('Native call binding changed')
        calls.append({'rva': rva, 'target_rva': target, 'hex': image[rva:rva + 5].hex()})
    return {'sha256': IMAGE_SHA, 'base': BASE, 'rva_equals_file_offset': True,
            'spans': spans, 'literals': literals, 'calls': calls,
            'cell_word_2_use': {
                'cell_offset': 2, 'width': 2, 'signed_read': True,
                'read_rvas': [0x3b810, 0x3b82c], 'compare_rvas': [0x3b814, 0x3b830],
                'comparison_operand': '[esp+10h]', 'decrement_rva': 0x3b836,
                'write_rva': 0x3b837,
                'dataflow': 'After 3B7B1 -> 40790, [esp+34h] is the block buffer and '
                            '[esp+38h] its width; ECX becomes buffer+(row*width+column)*8.',
                'condition': 'Requires the caller guards at 3B7D3..3B7FE; signed value greater '
                             'than [esp+10h] reaches the decrement/store. Other paths skip it.',
                'meaning': None, 'authority': 'static operand use only; not executed'},
            'static_limit': 'Header/consumer paths inspected, not executed; no full loader claim.'}


def native_block(image, raw, index):
    """Execute 40790 only, adapting two bounded CRT calls over actual source bytes."""
    if sha(raw) != PLAIN_SHA:
        raise ValueError('Native block execution requires pinned current MBD bytes')
    layout = parse_mbd(raw)
    if type(index) is not int or not 0 <= index < len(layout['offsets']):
        raise ValueError('Block index outside source')
    n = NativeRun(image)
    owner, grid, table, buffer = 0x3400000, 0x3401000, 0x3402000, 0x3404000
    handle, guard = 0x80010000, b'\xa5' * 16
    # Synthetic addresses/handle only; header, index and payload are original bytes.
    n.put(owner, raw[:16] + struct.pack('<III', table, layout['index_end'], handle))
    n.put(table, raw[16:layout['index_end']])
    n.put(grid, struct.pack('<III', buffer, BLOCK_SIDE, BLOCK_SIDE))
    n.put(buffer - 16, guard + b'\xcc' * BLOCK_BYTES + guard)
    n.put(SP, struct.pack('<4I', RETURN, index % layout['width'], index // layout['width'], owner))
    n.registers(ecx=grid, esp=SP)
    ranges = [(0x40790, 0x40829)]
    n.run(0x40790, ranges, {0x1477a3}, budget=200)
    offset = layout['offsets'][index]
    io = []

    def crt_return(value):
        sp = n.vm.reg_read(UC_X86_REG_ESP)
        ret = n.get32(sp)
        n.registers(eax=value, esp=sp + 4)
        return ret - BASE

    if offset:
        if n.stop != 0x1477a3:
            raise AssertionError('Original block reader did not reach fseek')
        sp = n.vm.reg_read(UC_X86_REG_ESP)
        if tuple(n.get32(sp + 4 + i * 4) for i in range(3)) != (handle, offset, 0):
            raise AssertionError('Native fseek arguments differ from source index')
        io.append({'rva': n.stop, 'operation': 'fseek', 'offset': offset, 'origin': 0})
        n.run(crt_return(0), ranges, {0x14785c}, budget=200)
        sp = n.vm.reg_read(UC_X86_REG_ESP)
        if n.stop != 0x14785c or tuple(n.get32(sp + 4 + i * 4) for i in range(4)) != (
                buffer, BLOCK_BYTES, 1, handle):
            raise AssertionError('Native fread shape differs from 21x21x8 block')
        payload = raw[offset:offset + BLOCK_BYTES]
        n.put(buffer, payload)
        io.append({'rva': n.stop, 'operation': 'fread', 'size': BLOCK_BYTES, 'count': 1})
        n.run(crt_return(1), ranges, set(), budget=200)
    else:
        payload = b'\xcc' * BLOCK_BYTES
    if (n.stop != RETURN or n.vm.reg_read(UC_X86_REG_EAX) != int(bool(offset))
            or n.vm.reg_read(UC_X86_REG_ESP) != SP + 16
            or bytes(n.vm.mem_read(buffer, BLOCK_BYTES)) != payload
            or bytes(n.vm.mem_read(buffer - 16, 16)) != guard
            or bytes(n.vm.mem_read(buffer + BLOCK_BYTES, 16)) != guard):
        raise AssertionError('Native block return, buffer or stack mismatch')
    return {'index': index, 'x': index % layout['width'], 'y': index // layout['width'],
            'source_offset': offset if offset else None, 'return_value': int(bool(offset)),
            'payload_sha256': sha(payload) if offset else None, 'io': io,
            'instruction_count': len(n.visits), 'runtime_eligible': False}


def build_report():
    raw, packed, image = (read_pinned(p) for p in (PLAIN, PACKED, IMAGE))
    decoded = decode_csvz(packed, limit=MAX_BYTES)
    if decoded != raw:
        raise ValueError('Current plain MBD and decoded MBDZ differ')
    layout = parse_mbd(raw)
    samples = []
    for index in SAMPLE_INDICES:
        offset = layout['offsets'][index]
        samples.append({'index': index, 'offset': offset, 'length': BLOCK_BYTES,
                        'sha256': sha(raw[offset:offset + BLOCK_BYTES]),
                        'first_cell_hex': raw[offset:offset + CELL_SIZE].hex()})
    native = native_evidence(image)
    return {
        'scope': 'One fixed current MBD/MBDZ pair; no family-wide or whole-client absence claim.',
        'sources': [{'path': p.relative_to(CLIENT).as_posix(), 'bytes': PINS[p][0],
                     'sha256': PINS[p][1]} for p in (PLAIN, PACKED)],
        'decoded_sha256': sha(decoded), 'plain_equals_decoded': True,
        'structure': {'magic': raw[:8].decode(), 'block_width': layout['width'],
                      'block_height': layout['height'], 'index_offset': 16,
                      'index_entries': len(layout['offsets']), 'index_end': layout['index_end'],
                      'index_sha256': sha(raw[16:layout['index_end']]),
                      'present_blocks': layout['present_blocks'], 'absent_blocks': layout['absent_blocks'],
                      'block_side': BLOCK_SIDE, 'cell_bytes': CELL_SIZE, 'block_bytes': BLOCK_BYTES,
                      'payload_bytes': len(raw) - layout['index_end'], 'unaccounted_bytes': 0,
                      'limit': 'Byte coverage is structural, not full semantic qualification.'},
        'samples': samples, 'native': native,
        'block_execution': [native_block(image, raw, index) for index in (0, *SAMPLE_INDICES)],
        'execution_limit': 'Only 40790 executes; CRT I/O adapted in memory. No native open, '
                           'decompression, version conversion, resource preload or consumer execution.',
        'cell_authority': {'word_0': 'Signed tile index: 3B7C7 -> 3B7CE -> 3B1B0; not monster identity.',
                           'bytes_2_through_7': None},
        'verified_wild_monster_records': 0, 'verified_boss_records': 0,
        'monster_field_authority': dict.fromkeys(FIELDS), 'runtime_eligible': False,
        'disqualified_source_recovery_targets': [{
            'call_rva': 0x37f4c, 'callee_rva': 0x38790,
            **native['spans']['empty_native_hook'],
            'bytes_hex': image[0x38790:0x387a0].hex(),
            'reason': 'Empty native hook: C3 RET followed by 15 NOPs, no cell operands. '
                      'The former proposed consumer frontier is withdrawn; do not reverse trace it.'}],
        'next_unexamined': {
            'call_rva': None, 'callee_rva': None,
            'source_block': {'index': 87, 'start': 0x2fdc, 'end_exclusive': 0x3da4},
            'cell_region': 'bytes +2..+7 of each 8-byte cell; first cell [0x2FDE,0x2FE4)',
            'reason': 'Next consumer unresolved. The local WORD+2 signed comparison/decrement '
                      'is now statically observed at 3B810/3B82C..3B83B, but its field meaning, '
                      'comparison-value provenance and remaining bytes are unqualified. '
                      'No further callee or wild-stat source is nominated.',
            'wild_stat_binding': None},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--summary', action='store_true')
    args = parser.parse_args()
    report = build_report()
    if args.summary:
        report = {key: report[key] for key in (
            'scope', 'sources', 'structure', 'block_execution', 'verified_wild_monster_records',
            'verified_boss_records', 'monster_field_authority', 'disqualified_source_recovery_targets',
            'next_unexamined', 'runtime_eligible')}
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
