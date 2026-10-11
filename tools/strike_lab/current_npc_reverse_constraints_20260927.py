"""Source-backed NPC location constraints and native direction independence.

Diagnostic 72 records are not original-server captures or runtime placements.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import pefile
from .omega_assets import decode_csvz
from .world_atlas import parse_catalog
from .current_npc_record import NativeNpcRecord, qualified_image, RANGES, BASE

ROOT = Path(__file__).resolve().parents[2]
CLIENT = ROOT.parent / 'God2'
MISSION_SHA = '659c8f38ffd9c34107969b449afd16488665a08970110910c9aed8448a0bb716'
CATALOG_SHA = '70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731'
CLIENT_SHA = '6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98'
CASES = [(1488, '廚師梁禎', 2936, 108, 110), (1492, '李樂', 2937, 113, 69),
         (1494, '阿銀嬸', 2938, 69, 72), (1496, '馬老伯', 2939, 68, 116)]


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def audit():
    image = qualified_image()
    exe = (CLIENT/'God2.exe').read_bytes()
    require(sha(exe) == CLIENT_SHA, 'Current client changed')
    current = pefile.PE(data=exe).get_memory_mapped_image()
    for name in ('selectors', 'new_actor_scalars', 'alternate_new_position'):
        start, end = RANGES[name]
        require(current[start:end] == image[start:end], 'Native inspected span differs')
    mission = (CLIENT/'Data2/Patch/Comm/Mission_data.csvZ').read_bytes()
    catalog = (CLIENT/'Data2/Patch/Comm/gamedata.csvZ').read_bytes()
    require(sha(mission) == MISSION_SHA and sha(catalog) == CATALOG_SHA, 'Source changed')
    lines = decode_csvz(mission).splitlines()
    cat = decode_csvz(catalog).splitlines()
    start = next(i for i, row in enumerate(cat) if row.startswith(b'NPCAppearData,'))
    count = int(cat[start].split(b',')[1])
    templates = cat[start+1:start+1+count]
    maps = [m for m in parse_catalog(decode_csvz(catalog))
            if bytes.fromhex(m['map_name_bytes']).decode('cp950') == '果力村']
    require(len(maps) == 1 and (maps[0]['area'], maps[0]['scene']) == (13,12), 'Map join changed')
    native = NativeNpcRecord(image)
    results = []
    for line, name, template, x, y in CASES:
        raw = lines[line-1]
        text = raw.decode('cp950')
        require('果力村的'+name in text, 'Explicit source map/name context changed')
        require(re.search(re.escape(name)+r'\('+str(x)+'/'+str(y)+r'\)', text), 'Source location changed')
        candidates = [row for row in templates if row.split(b',')[1].decode('cp950') == name]
        require(len(candidates) == 1 and int(candidates[0].split(b',')[0]) == template, 'Name join ambiguous')
        vectors = []
        for direction in range(8):
            record = bytearray(21)
            record[0] = 0x72
            struct.pack_into('<I', record, 1, template)
            record[9] = direction << 5
            struct.pack_into('<I', record, 17, (x << 2) | (y << 17))
            # A diagnostic maximum tests selector independence; it is not a
            # claim that source row count equals the native sparse key limit.
            selected = native.selectors(bytes(record), 32767)
            require(not selected['fault'] and selected['selected'], 'Diagnostic selector rejected')
            observed = native.position(bytes(record))
            require(not observed['fault'] and (observed['x'], observed['y']) == (x, y), 'Position slice mismatch')
            require(observed['direction_slice'] == direction, 'Direction slice mismatch')
            vectors.append({'direction_input': direction, 'stored_direction': observed['direction_slice'],
                            'synthetic_catalog_max': 32767,
                            'constructor_ebx_instance_fixture': 0x5a5a,
                            'stored_x': observed['x'], 'stored_y': observed['y'],
                            'selector_stop_rva': hex(selected['stop_rva']),
                            'position_stop_rva': hex(observed['stop_rva']),
                            'diagnostic_logical_hex': record.hex()})
        results.append({'npc_name': name, 'template_candidate': template,
                        'source_line': line, 'source_record_hex': raw.hex(), 'source_record_sha256': sha(raw),
                        'template_record_hex': candidates[0].hex(), 'template_record_sha256': sha(candidates[0]),
                        'map_candidate': {'area': 13, 'scene': 12, 'kind': maps[0]['kind'],
                                          'source_line': maps[0]['source_line'],
                                          'source_record_sha256': maps[0]['source_record_sha256']},
                        'text_target_x': x, 'text_target_y': y, 'native_direction': None,
                        'direction_candidates_not_eliminated_by_tested_slices': list(range(8)),
                        'native_slice_vectors': vectors, 'runtime_eligible': False})
    return {'status': 'PASS', 'schema': 'god2-npc-reverse-constraints-v1',
            'client_sha256': CLIENT_SHA, 'mission_source_sha256': MISSION_SHA,
            'catalog_source_sha256': CATALOG_SHA, 'source_constraints': results,
            'native_vector_count': 32, 'complete_placements_recovered': 0,
            'runtime_mutation_enabled': False,
            'scope': 'Actual text coordinates + unique exact-name candidates; explicit diagnostic selector/constructor slices.',
            'limitations': ['Text target position is not proven server spawn origin, roaming rule or world instance identity.',
                            'Map context is a textual constraint, not the 72 record world-scene authority.',
                            'All eight directions satisfy inspected native slices for the same source coordinates.',
                            'No full resource constructor, graphical acceptance or original server capture.']}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    result = audit()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'status': 'PASS', 'constraints': 4, 'native_vectors': 32, 'complete_placements': 0}))


if __name__ == '__main__':
    main()
