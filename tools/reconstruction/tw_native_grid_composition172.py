"""File-only pinned TW grid composition recovery and full-source preservation.

This program decodes static bytes only. It never runs a client, server, C++,
Lua, SQL, API, emulator, build, test or gameplay acceptance.
"""
from pathlib import Path
import argparse
import hashlib
import json

import capstone

ROOT = Path(__file__).resolve().parents[2]
ROUND = ROOT / 'artifacts/integration/packet-connections-20261006/tw-native-grid-composition-source-01'
ARTIFACT = ROUND / 'agents/tw-grid-composition'
IMAGE = ROOT / 'artifacts/research/enemy-blackbox-20261006/consumer-experiment/inputs/native-image.bin'
PIN = '149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
BEFORE_PIN = '0d0b0bed26c2052f436845c9b044aeb8797f2e3524b42419cac8ef341cf4b1cf'
BASE = 0x400000
OWNED = ['src/game/TaiwanNativeGrid.h', 'src/game/TaiwanNativeGrid.cpp',
         'tools/reconstruction/tw_native_grid_composition172.py']
SPANS = [
    (0x49B30, 0x49B68, 'native x/y to initialization pixel coordinates; fifth width, sixth caller height unused', 'new_target'),
    (0x49BB0, 0x49BDC, 'native staggered x/y to diagonal grid coordinates', 'new_target'),
    (0x41F90, 0x41FBC, 'tile instance initializer sets actual frame selector +30 to zero', 'new_target'),
    (0x41FC0, 0x41FE6, 'tile initialization writes pixel/grid coordinates and actual resource link only', 'new_target'),
    (0x36C30, 0x36F24, 'complete prior171 initializer context; extent, stack ledger, projection and ordered overlays', 'prior171_context_not_new_recovery'),
    (0x416B0, 0x41729, 'complete prior171 raw selected-frame getter context including AL1 geometric fallback', 'prior171_context_not_new_recovery'),
]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def put(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as stream:
        stream.write(data)


def emit(name, value):
    put(ARTIFACT / name, (json.dumps(value, ensure_ascii=True, indent=2) + '\n').encode())


def copy_source(relative, destination):
    path = ROOT / relative
    raw = path.read_bytes()
    put(ARTIFACT / destination, raw)
    return {'path': path.resolve().as_posix(), 'relative_path': relative,
            'copy': destination, 'bytes': len(raw), 'sha256': sha(raw)}


def stage(label):
    rows = [copy_source(relative, f'intermediate/{label}/{relative}') for relative in OWNED]
    emit(f'intermediate/{label}/source-origins.json', rows)
    return rows


def recover():
    raw = IMAGE.read_bytes()
    if sha(raw) != PIN:
        raise RuntimeError('Pinned full native mapped image changed')
    before = (ROUND / 'before-manifest.json').read_bytes()
    if sha(before) != BEFORE_PIN:
        raise RuntimeError('Fresh parent before manifest differs; do not reset baseline')
    ARTIFACT.mkdir(parents=True, exist_ok=True)
    put(ARTIFACT / 'root-before-manifest.json.raw', before)
    emit('root-lineage.json', {'before_inputs': 1232, 'before_sha256': BEFORE_PIN,
         'entire_prior171_members': 2067, 'prior_verification': 'parent_receipt',
         'prior_artifacts_never_modified': True})
    emit('new-files-before.json', [{'path': (ROOT / relative).resolve().as_posix(),
         'relative_path': relative, 'state': 'absent_in_fresh_parent_before',
         'before_copy': None} for relative in OWNED])
    input_row = copy_source(IMAGE.relative_to(ROOT).as_posix(), 'native-input/full-mapped-image.bin')
    emit('native-input-originals.json', [input_row])
    before_rows = [copy_source(relative, f'before/{relative}') for relative in [
        IMAGE.relative_to(ROOT).as_posix(), 'src/protocol/RecoveredTaiwanMapCell.h',
        'src/game/SharedTaiwanNativeMovementScene.h']]
    emit('before-source-origins.json', before_rows)
    decoder = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    spans, instructions = [], {}
    for index, (start, end, purpose, classification) in enumerate(SPANS):
        data = raw[start:end]
        destination = f'native-spans/s{index:02d}-{BASE+start:08X}-{BASE+end:08X}.bin'
        put(ARTIFACT / destination, data)
        decoded = []
        for instruction in decoder.disasm(data, BASE + start):
            row = {'va': f'{instruction.address:08X}', 'rva': f'{instruction.address-BASE:08X}',
                   'bytes_hex': instruction.bytes.hex(), 'mnemonic': instruction.mnemonic,
                   'operands': instruction.op_str}
            decoded.append(row)
            instructions[instruction.address-BASE] = row
        spans.append({'start_va': f'{BASE+start:08X}', 'end_exclusive_va': f'{BASE+end:08X}',
                      'start_rva': f'{start:08X}', 'end_exclusive_rva': f'{end:08X}',
                      'purpose': purpose, 'classification': classification, 'copy': destination,
                      'bytes': len(data), 'sha256': sha(data), 'instructions': decoded})
    emit('native-spans.json', spans)
    selected = [
        (0x49B34, 'helper saves ESI; all argument offsets account for this push'),
        (0x49B3D, 'native pixelX begins DWORD x+y'),
        (0x49B43, 'pixelX is 40*(x+y) after fivefold LEA and SHL3'),
        (0x49B48, 'fifth actual argument width; sixth caller height is not read'),
        (0x49B4C, 'width+1 then CDQ/SUB/SAR truncation toward zero'),
        (0x49B56, 'twice the rounded half of width+1'),
        (0x49B5A, 'subtract x, add y-2 before final multiplication20'),
        (0x49B67, 'plain RET; caller owns six pushed arguments'),
        (0x49BB9, 'second staggered argument is signed y'),
        (0x49BC0, 'native signed y/2 truncation toward zero'),
        (0x49BC2, 'gridX=x-trunc(y/2)'),
        (0x49BCA, 'second coordinate begins DWORD y+1'),
        (0x49BD6, 'gridY=x+trunc((y+1)/2)'),
        (0x49BDB, 'plain RET; caller owns four pushed arguments'),
        (0x41FA6, 'initializer writes actual selected frame+30 zero'),
        (0x41FC8, 'store initialization pixelX at +0C'),
        (0x41FCF, 'store initialization pixelY at +10'),
        (0x41FD6, 'store gridX at +14'),
        (0x41FDD, 'store gridY at +18'),
        (0x41FE0, 'store actual resource pointer at +2C; does not select frame'),
        (0x36C98, 'stack ledger S before first sideY push'),
        (0x36C9F, 'outPixelX pointer S+30 after two pushes'),
        (0x36CA7, 'outPixelY pointer S+2C after two pushes'),
        (0x36CB0, 'six-push ESP S-18; saves baseOrigin at S+24'),
        (0x36CBC, 'S-18+44 reads outputPixelY S+2C'),
        (0x36CC0, 'S-18+48 reads outputPixelX S+30'),
        (0x36CC4, 'caller removes six arguments, restores ESP S'),
        (0x36CD2, 'initializer caller passes actual pixels and baseOrigin,0'),
        (0x36CFA, 'base sampling selector actual grid tile instance+30'),
        (0x36D04, 'base loop height is actual frame0 extent, not selected height'),
        (0x36D27, 'base loop width is actual frame0 extent, not selected width'),
        (0x36D47, 'base gridX uses saved baseOrigin S+24'),
        (0x36D79, 'base read uses selected low BYTE frame with frame0 loop coordinates'),
        (0x36D8A, 'base raw AL store unchanged'),
        (0x36D8F, 'base destination out of range asserts then skips store'),
        (0x36DE4, 'actual linked object head and nonempty check'),
        (0x36DF9, 'actual overlay object gridY source +18'),
        (0x36DFC, 'actual overlay object gridX source +14'),
        (0x36E05, 'overlay stack ledger outY pointer S+34 before pushes'),
        (0x36E0E, 'after first push, outX pointer S+18'),
        (0x36E1A, 'S-10+34 loads baseOrigin S+24, not outY'),
        (0x36E1E, 'S-10+28 loads converted overlayX S+18'),
        (0x36E28, 'overlayX adds actual saved baseOrigin'),
        (0x36E2A, 'store combined overlayX at S+18'),
        (0x36E2E, 'caller removes four arguments and restores ESP S'),
        (0x36E36, 'overlay loops use selected frame height'),
        (0x36E4C, 'row gridX begins combined overlay origin S+18'),
        (0x36E5B, 'row gridY begins actual converted outY S+34'),
        (0x36E6C, 'overlay loops use selected frame width'),
        (0x36EAD, 'only actual raw overlay AL zero selects overwrite'),
        (0x36EC1, 'actual zero overwrites destination cell'),
        (0x36EC7, 'overlay destination out of range asserts then skips store'),
        (0x36F0D, 'follow actual linked object +4 in order'),
        (0x416B5, 'selected frame identity is low BYTE of actual selector'),
        (0x41718, 'selected getter preserves actual raw byte'),
        (0x41723, 'known selected mask geometric OOB fallback AL1'),
    ]
    emit('native-sites.json', [{'rva': f'{rva:08X}', 'va': f'{BASE+rva:08X}',
         'instruction': instructions[rva], 'fact': fact,
         'classification': 'new_target' if rva>=0x49B30 or 0x41F90<=rva<0x41FE6
                           else 'prior171_context_not_new_recovery'} for rva, fact in selected])
    emit('stack-ledger.json', {
        'offset_domain': 'hexadecimal_all_offsets_and_push_deltas',
        'base_S': 'ESP immediately before RVA36C98',
        'base_pushes': ['sideY', 'sideX', '&S+2C outPixelY', '&S+30 outPixelX', '0 y', 'baseOrigin x'],
        'base_call_ESP': 'S-18', 'base_origin_saved': 'S-18+3C=S+24',
        'base_outputs': {'pixelX': 'S+30', 'pixelY': 'S+2C'},
        'base_read_outputs': {'pixelY': 'S-18+44=S+2C', 'pixelX': 'S-18+48=S+30'},
        'base_cleanup': 'ADD ESP,18', 'base_helper_ret': 'RET with no immediate',
        'overlay_S': 'same ESP before RVA36E05',
        'overlay_pushes': ['&S+34 outY', '&S+18 outX', 'actual_y', 'actual_x'],
        'overlay_call_ESP': 'S-10', 'overlay_outputs': {'x': 'S+18', 'y': 'S+34'},
        'overlay_reads': ['S-10+34=S+24 saved baseOrigin', 'S-10+28=S+18 converted x'],
        'overlay_combined_x_store': 'S-10+28=S+18', 'overlay_cleanup': 'ADD ESP,10',
        'subsequent_loop_reads': ['S+18 combinedX', 'S+34 convertedY'],
        'earlier_offset_confusion_corrected': 'initial decimal/hex mixed arithmetic was discarded; no unknown origin gap',
    })
    emit('native-composition-facts.json', {
        'format': 'tw-pinned-native-grid-composition-v1', 'input_sha256': PIN,
        'base_side': '2*max(frame0.width,trunc(frame0.height/2)+(frame0.height&1))+1',
        'base_origin_x': '(frame0.width&1)-frame0.width+side-1',
        'base_projection': {'x': 'origin-trunc(row/2)+column', 'y': 'trunc((row+1)/2)+column'},
        'base_loop_extent': 'frame0.width/height', 'base_sample_extent': 'actual selected frame width/height',
        'overlay_projection': {'originX': 'actual_x-trunc(actual_y/2)+baseOrigin',
                               'originY': 'actual_x+trunc((actual_y+1)/2)',
                               'x': 'originX-trunc(row/2)+column',
                               'y': 'originY+trunc((row+1)/2)+column'},
        'overlay_loop_extent': 'actual selected frame width/height',
        'overlay_order': 'complete actual linked head/+4 traversal',
        'overlay_predicate': 'only raw0 writes0; nonzero leaves actual prior rawcell unchanged',
        'clear': 'whole actual square cell matrix to zero before base loop',
        'destination_OOB': 'assert then skip; preserve cleared/base/prior overlay byte',
        'known_complete_selected_mask_OOB': 'native AL1 getter fallback; no movement permission inferred',
        'missing_or_incomplete_selected_mask': 'source rejection, never getter fallback',
        'arithmetic': '32bit native integer operations; source accepts nonoverflow intermediates only',
        'owning_source': 'immutable deep-copy Material and matrix; no generated native addresses',
        'new_target_functions': 4, 'prior171_context_functions_not_new': 2,
        'new_opcodes': 0, 'complete_bidirectional_routes_added': 0,
        'whole_game_percentage': None, 'source_only': True,
    })
    emit('gaps.json', {
        'actual_mask_selection_issuer': 'actual selected masks and selectors are supplied, no issuer invented',
        'actual_complete_ordered_objects_issuer': 'actual complete native list required; source does not enumerate native objects',
        'actual_resource_lifetime': 'generation/identity/cache/frame/material-current supplier still required',
        'native_addresses': 'none generated; derived grid is address-independent and is not a captured map object',
        'authority': 'no collision rights, pending5D, time/sequence, battle/transfer or CN rules supplied',
        'unsupported_source_domains': ['nonpositive/incomplete masks', 'any overflowing native DWORD intermediate',
                                       'matrix or retained mask footprint over UINT32_MAX'],
        'phase': 'source-only; no build/tests/native execution/emulation/deployment/client acceptance',
    })
    rows = stage('source-01')
    print(json.dumps({'artifact': ARTIFACT.as_posix(), 'new_target_spans': 4,
                     'prior171_context_spans': 2, 'native_sites': len(selected),
                     'owned_sources': rows, 'native_input': input_row, 'source_only': True}))


def final():
    rows = [copy_source(relative, f'current/{relative}') for relative in OWNED]
    emit('current-source-origins.json', rows)
    emit('current-sources-list.json', [{key: row[key] for key in ['path', 'copy', 'bytes', 'sha256']}
                                     for row in rows])
    emit('delivery.json', {'round': '20261008-tw-native-grid-composition-source',
         'owned_cpp_files': OWNED[:2], 'owned_research_tool': OWNED[2], 'current_originals': rows,
         'new_target_spans': 4, 'prior171_context_spans': 2, 'new_opcodes': 0,
         'complete_routes_added': 0, 'whole_game_percentage': None, 'source_only': True,
         'BATCHFINAL_received': True, 'mutable_root_books_catalog_reports_not_current_pinned': True})
    members = []
    for path in sorted(ARTIFACT.rglob('*')):
        if path.is_file():
            raw = path.read_bytes()
            members.append({'path': path.relative_to(ARTIFACT).as_posix(),
                            'bytes': len(raw), 'sha256': sha(raw)})
    emit('seal.json', {'format': 'god2-agent-full-artifact-seal-v1', 'members': members,
         'member_count': len(members), 'source_only': True, 'whole_game_percentage': None})
    print(json.dumps({'members': len(members), 'current_originals': len(rows),
                     'seal_sha256': sha((ARTIFACT / 'seal.json').read_bytes()), 'owned_sources': rows}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--final', action='store_true', help='only after explicit parent BATCHFINAL')
    args = parser.parse_args()
    final() if args.final else recover()
