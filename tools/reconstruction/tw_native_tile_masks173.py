"""Static TW ModelDat/Pass reader recovery with full actual input preservation.

Only local file reads, pure resource decompression, hashes and Capstone run.
No C++, client/server, emulator, API, DB, SQL, build, tests or acceptance run.
"""
from pathlib import Path
import argparse
import hashlib
import json

import capstone
from tools.strike_lab.omega_assets import decode_csvz

ROOT = Path(__file__).resolve().parents[2]
ROUND = ROOT / 'artifacts/integration/packet-connections-20261006/tw-native-mask-material-source-01'
ARTIFACT = ROUND / 'agents/tw-mask-source'
IMAGE = ROOT / 'artifacts/research/enemy-blackbox-20261006/consumer-experiment/inputs/native-image.bin'
ASSET = ROOT.parent / 'God2/Data2/map/island03/cityi2/cityi2.mdlZ'
IMAGE_PIN = '149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
ASSET_PIN = 'cb36dbf46adc611620e1bd7c9b0093955c846f33a849ebf88f6ce57f426813cc'
DECODED_PIN = 'bed2f89dcdb30ed6d7b30c5625423f8bd007ca30eea32ec5406a7ebb7932dd5f'
BEFORE_PIN = 'ec12b1b0d1b67396ae8fa89f8c94efd76753d10f3da2ef01365180147f28e644'
BASE = 0x400000
OWNED = ['src/game/TaiwanNativeTileMasks.h', 'src/game/TaiwanNativeTileMasks.cpp',
         'tools/reconstruction/tw_native_tile_masks173.py']
SPANS = [
    (0x4C980, 0x4CE6B, 'complete actual TW ModelDat model reader, version/layers/anchors/markers/Pass/registration', 'current_target'),
    (0x4D750, 0x4D97B, 'complete ROMFILE/TileModel/ModelDat dispatcher, actual section/count/call sequence', 'current_target'),
    (0x41730, 0x417B2, 'actual rawcell setter signed bounds and lowBYTE input store', 'current_target'),
    (0x41880, 0x419C3, 'actual mask dimensions/allocation/product and zero-dimension branch', 'current_target'),
    (0x41560, 0x415DB, 'actual ModelDat object initializes ten full mask slots and layers/markers', 'current_target'),
    (0x151DE0, 0x151EB0, 'complete native CRT case-insensitive compare, ASCII and locale paths distinguished', 'CRT_boundary_context'),
]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def put(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as stream:
        stream.write(data)


def emit(name, value):
    put(ARTIFACT / name, (json.dumps(value, ensure_ascii=True, indent=2) + '\n').encode())


def copy_file(path, destination):
    raw = path.read_bytes()
    put(ARTIFACT / destination, raw)
    return {'path': path.resolve().as_posix(), 'copy': destination,
            'bytes': len(raw), 'sha256': sha(raw)}


def stage(name):
    rows = [copy_file(ROOT / relative, f'intermediate/{name}/{relative}') for relative in OWNED]
    emit(f'intermediate/{name}/source-origins.json', rows)
    return rows


def recover():
    raw = IMAGE.read_bytes()
    asset = ASSET.read_bytes()
    before = (ROUND / 'before-manifest.json').read_bytes()
    if sha(raw) != IMAGE_PIN or sha(asset) != ASSET_PIN or sha(before) != BEFORE_PIN:
        raise RuntimeError('Actual input differs from pinned source; do not reset baseline')
    plain = decode_csvz(asset)
    if sha(plain) != DECODED_PIN:
        raise RuntimeError('Actual decoded CityI2 source differs')
    ARTIFACT.mkdir(parents=True, exist_ok=True)
    put(ARTIFACT / 'root-before-manifest.json.raw', before)
    emit('root-lineage.json', {'fresh_before_inputs': 1238, 'fresh_before_sha256': BEFORE_PIN,
         'entire_prior172_members_retained': 2047, 'prior_verification': 'parent_receipt',
         'prior_artifacts_unchanged': True})
    emit('new-files-before.json', [{'path': (ROOT / relative).resolve().as_posix(),
         'state': 'absent_in_fresh_parent_before', 'before_copy': None} for relative in OWNED])
    inputs = [copy_file(IMAGE, 'input/native-image.bin'), copy_file(ASSET, 'input/cityi2.mdlZ'),
              copy_file(ROOT / 'tools/strike_lab/omega_assets.py', 'input/omega_assets.py')]
    emit('input-originals.json', inputs)
    put(ARTIFACT / 'input/cityi2.decoded.bin', plain)
    emit('decoded-input.json', {'copy': 'input/cityi2.decoded.bin', 'bytes': len(plain),
         'sha256': sha(plain), 'origin': 'pure file decompression of exact installed original cityi2.mdlZ',
         'raw_source_sha256': ASSET_PIN, 'decoder_input_copy': 'input/omega_assets.py',
         'actual_header_hex': plain[:10].hex(), 'actual_ModelDat_token_offset': plain.index(b'ModelDat'),
         'native_or_Cpp_parser_not_executed': True})
    context = [copy_file(ROOT / relative, f'before-context/{relative}') for relative in [
        'src/game/TaiwanNativeGrid.h', 'src/game/TaiwanNativeGrid.cpp',
        'src/cn/assets/CnHouseMapAsset.h', 'src/cn/assets/CnHouseMapAsset.cpp',
        'src/cn/assets/CnAssetTokens.h', 'docs/research/current-mdl-zero-pass-20260927.md',
        'tools/strike_lab/current_monster_binary_producer.py',
        'tools/strike_lab/current_mdl_zero_pass_20260927.py']]
    emit('context-source-origins.json', context)
    emit('context-scope.json', {'CN_sources': 'lead only; never TW proof',
         'old_zero_pass_tool': 'source read only; native emulation program never run',
         'old_mdl_parser': 'source lead only; not executed as this source qualification',
         'current_native_input': 'direct pinned TW mapped bytes are actual format authority',
         'mutable_root_books_catalog_reports': 'not current pinned'})
    decoder = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    spans, instructions = [], {}
    for index, (start, end, purpose, classification) in enumerate(SPANS):
        data = raw[start:end]
        destination = f'native-spans/s{index:02d}-{BASE+start:08X}-{BASE+end:08X}.bin'
        put(ARTIFACT / destination, data)
        decoded = []
        for instruction in decoder.disasm(data, BASE + start):
            row = {'rva': f'{instruction.address-BASE:08X}', 'va': f'{instruction.address:08X}',
                   'bytes_hex': instruction.bytes.hex(), 'mnemonic': instruction.mnemonic,
                   'operands': instruction.op_str}
            decoded.append(row)
            instructions[instruction.address-BASE] = row
        spans.append({'start_rva': f'{start:08X}', 'end_exclusive_rva': f'{end:08X}',
                      'start_va': f'{BASE+start:08X}', 'end_exclusive_va': f'{BASE+end:08X}',
                      'copy': destination, 'bytes': len(data), 'sha256': sha(data),
                      'purpose': purpose, 'classification': classification, 'instructions': decoded})
    emit('native-spans.json', spans)
    selected = [
        (0x4C9CB, 'actual allocated ModelDat object constructor00441560, not ROM object'),
        (0x4CA09, 'three signed decimal fields for one of three layers'),
        (0x4CA15, 'layer index-1 means absent; source retains original offset declarations'),
        (0x4CA28, 'actual model layer linked to actual TileModel'),
        (0x4CA71, 'exactly three layer groups'),
        (0x4CA7E, 'actual body+8 dereferenced; source rejects absent body'),
        (0x4CAE5, 'versions compared against v1.5; v1.6 takes new frame declarations'),
        (0x4CB31, 'declared frame count signed decimal read'),
        (0x4CB3D, 'initial declared frame count stored at+1BC'),
        (0x4CB5D, 'actual declared frame anchor pair read'),
        (0x4CB7B, 'anchor x retained at+5C+frame*24'),
        (0x4CB7E, 'anchor y retained at+60+frame*24'),
        (0x4CB95, 'native later default-anchor extension reads beyond declared count; unresolved ROM branch not copied'),
        (0x4CBB6, 'actual runtime frame total becomes body ROM frame count, not declared count'),
        (0x4CBC9, 'v1.2 comparison gates eight marker integers'),
        (0x4CC03, 'four declared marker pairs read losslessly'),
        (0x4CC1B, 'actual duplicate-suppression marker helper; source retains declarations without replay'),
        (0x4CC34, 'Pass word scanf read'),
        (0x4CC43, 'Pass compared case-insensitively with actual lowercase literal'),
        (0x4CC8F, 'declared frame count zero reads no Pass dimensions/cells'),
        (0x4CCAF, 'dimension pair read only for v1.6 or newer, parser accepts exact v1.6 only'),
        (0x4CCCB, 'read width and height with %d %d'),
        (0x4CCE0, 'resize setter called even for zero width/height'),
        (0x4CCED, 'height nonpositive skips all cell reads'),
        (0x4CCF7, 'width nonpositive skips all cells within row loop'),
        (0x4CD0B, 'raw cell is signed32 decimal scanf, not a boolean or byte-limited input'),
        (0x4CD1D, 'original rawcell setter actual frame/x/y/value call'),
        (0x4CD4E, 'declared BYTE frame index loop count comparison'),
        (0x4CD63, 'older version ROM-derived masks branch excluded from v1.6 source parser'),
        (0x4CE30, 'native registers actual ModelDat; source parser does not register runtime objects'),
        (0x4D7AF, 'ROMFILE case-insensitive section comparison'),
        (0x4D7DA, 'ROMFILE reader called, not interpreting it as ModelDat'),
        (0x4D8E5, 'TileModel reader dispatched before ModelDat'),
        (0x4D907, 'actual ModelDat literal comparison argument'),
        (0x4D93C, 'ModelDat section signed count read'),
        (0x4D95E, 'each ModelDat declaration dispatches actual0044C980'),
        (0x41588, 'constructor initializes exactly ten complete mask slots'),
        (0x41592, 'each slot pointer initially zero'),
        (0x41598, 'each slot width initially zero'),
        (0x41595, 'each slot height initially zero'),
        (0x415AC, 'actual mask record stride0x24'),
        (0x41735, 'setter frame selector lowBYTE'),
        (0x41793, 'actual width*y row-major offset'),
        (0x41798, 'cell signed decimal value selected lowBYTE'),
        (0x4179C, 'write lowBYTE unchanged'),
        (0x418A1, 'unchanged dimensions branch avoids unnecessary allocation'),
        (0x418B7, 'native width*height DWORD product, overflow domain unsupported in source'),
        (0x419AE, 'retain actual height even when zero'),
        (0x419B4, 'retain actual width even when zero'),
        (0x151E0A, 'CRT ASCII case-folding path for section words'),
        (0x151E33, 'CRT locale-sensitive alternative exists, not claimed reproduced globally'),
    ]
    emit('native-sites.json', [{'rva': f'{rva:08X}', 'va': f'{BASE+rva:08X}',
         'instruction': instructions[rva], 'fact': fact} for rva, fact in selected])
    literal_offsets = [0x1877A0, 0x1877A8, 0x1877BC, 0x1877C4, 0x187844,
                       0x188AE8, 0x188AF0, 0x188B90, 0x188B9C, 0x184954, 0x1823B4]
    literals = []
    for index, start in enumerate(literal_offsets):
        end = raw.index(0, start) + 1
        data = raw[start:end]
        destination = f'native-literals/l{index:02d}-{BASE+start:08X}.bin'
        put(ARTIFACT / destination, data)
        literals.append({'rva': f'{start:08X}', 'va': f'{BASE+start:08X}', 'copy': destination,
                         'bytes': len(data), 'sha256': sha(data), 'raw_hex': data.hex()})
    emit('native-literals.json', literals)
    emit('source-format-facts.json', {'native_image_sha256': IMAGE_PIN, 'version': 'exact v1.6 only',
         'actual_prefix': 'ModelDat count; each model: 3 layer triples, declared count/anchor pairs,4 marker pairs,Pass,frame dimensions/cells',
         'model_identity': 'native section order, not a ROM-object ordinal',
         'frame_identity': 'declared frame index; lowBYTE actual selector selects only an existing declaration',
         'rawcell': 'signed32 decimal input reduced modulo256 by actual native setter',
         'zero_dimensions': 'retain declarations and empty bytes; no cell reads or fake positive Mask',
         'cursor': 'exact next unread byte; no trailing whitespace or following Model consumed',
         'consumption': 'all word/decimal reads include leading whitespace/token begin/end and original signed value',
         'source_ownership': 'immutable full decoded copy and all models/frames/tokens; selected Mask deep copy',
         'no_ROM_object_or_unknown_version_defaults': True, 'new_opcodes': 0, 'complete_routes_added': 0,
         'whole_game_percentage': None, 'source_only': True})
    emit('gaps.json', {'actual_full_map_placement_parser': 'peer-owned, not implemented in this library',
         'decoded_resource_issuer': 'caller supplies exact decoded bytes and actual header/tile count; no runtime loader invented',
         'body_ROM_frame_total': 'native44C980 overwrites+1BC from body; parser only exposes actual declared frames',
         'model_pixel_geometry': 'body/layer2 real native tile/ROM extent required; Pass dimensions are not ModelDat+0/+4',
         'actual_selected_frame_lifecycle': 'actual placement/frame/object/resource-current owner remains required',
         'unsupported_domains': ['unknown versions', 'negative dimensions', 'more than10 declared frames',
                                 'overflowing signed32 decimal/allocation footprint', 'embedded NUL', 'locale-specific nonASCII section words'],
         'runtime_status': 'source-only; no build/test/emulation/native acceptance/deployment'})
    rows = stage('source-01')
    print(json.dumps({'artifact': ARTIFACT.as_posix(), 'spans': len(spans), 'sites': len(selected),
                     'literals': len(literals), 'inputs': inputs, 'owned_sources': rows, 'source_only': True}))


def final():
    rows = [copy_file(ROOT / relative, f'current/{relative}') for relative in OWNED]
    emit('current-source-origins.json', rows)
    emit('delivery.json', {'round': '20261008-tw-native-mask-material-source', 'owned_sources': rows,
         'current_pins_only_owned_stable_originals': True, 'BATCHFINAL_received': True,
         'raw_game_target_spans': 5, 'CRT_context_spans': 1, 'new_opcodes': 0,
         'full_routes_added': 0, 'whole_game_percentage': None, 'source_only': True})
    members = []
    for path in sorted(ARTIFACT.rglob('*')):
        if path.is_file():
            raw = path.read_bytes()
            members.append({'path': path.relative_to(ARTIFACT).as_posix(), 'bytes': len(raw), 'sha256': sha(raw)})
    emit('seal.json', {'format': 'god2-agent-full-artifact-seal-v1', 'members': members,
         'member_count': len(members), 'source_only': True, 'whole_game_percentage': None})
    print(json.dumps({'members': len(members), 'current_originals': len(rows),
                     'seal_sha256': sha((ARTIFACT / 'seal.json').read_bytes()), 'owned_sources': rows}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--final', action='store_true', help='only after parent BATCHFINAL')
    args = parser.parse_args()
    final() if args.final else recover()
