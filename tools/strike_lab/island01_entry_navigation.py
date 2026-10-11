"""Pinned scene 2/0 static windows around the CityI1 map placement.

This is source and C++ projection evidence, not a live scene route or an
encounter authority. Only nine selected windows are exported.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

from .current_monster_binary_producer import parse_mdl
from .omega_assets import decode_csvz
from .outdoor_mbd import (apply_model_pass, apply_model_points,
                          parse_mbd, project_base_window)
from .town_navigation import (MDL_SHA as CITY_MDL_SHA,
                              MDL_DECODED_SHA as CITY_DECODED_SHA,
                              canonical_points, pinned)
from .world_atlas import parse_catalog

MBD_SHA = 'b574654e5859e048ea0047c0de36b70addc5e90f2349b9796016ea6792f75f80'
MBDZ_SHA = '0edf2048eaf0964caa2c373d66b4c1e6129ebeca265c4a63326436c13e6e0a1f'
MDL_SHA = 'cbdc0c946618a1bf4a9b2f221283a17fa58b1f49941b2ea336046851a2519d8d'
DECODED_SHA = '88349e73e0baa95ca773dc54641a23d1baa19dbef25b3313866980ccbde6fce2'
CATALOG_SHA = '70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731'
CENTERS = tuple((x, y) for y in range(8, 11) for x in range(21, 24))


def sha(data):
    return hashlib.sha256(data).hexdigest()


def build(client, executable, centers=CENTERS):
    root = Path(client).resolve()
    folder = root / 'Data2/map/island01'
    if not folder.resolve().is_relative_to(root):
        raise ValueError('Island source escapes client root')
    catalog = parse_catalog(decode_csvz(pinned(root / 'Data2/Patch/Comm/gamedata.csvZ', CATALOG_SHA)))
    scene = [row for row in catalog if (row['area'], row['scene']) == (2, 0)]
    city = [row for row in catalog if (row['area'], row['scene']) == (2, 4)]
    if len(scene) != 1 or scene[0]['kind'] != 1 or not scene[0]['mdt_relative'].lower().endswith('/island01.mdt') or \
       len(city) != 1 or city[0]['kind'] != 0 or not city[0]['mdt_relative'].lower().endswith('/cityi1.mdt'):
        raise ValueError('Current island and town map selectors changed')
    mbd_bytes = pinned(folder / 'island01.mbd', MBD_SHA)
    if decode_csvz(pinned(folder / 'Island01.mbdZ', MBDZ_SHA), limit=4 * 1024 * 1024) != mbd_bytes:
        raise ValueError('Island compressed and plain blocks disagree')
    mbd = parse_mbd(mbd_bytes)
    encoded = pinned(folder / 'Island01.mdlZ', MDL_SHA)
    decoded = decode_csvz(encoded, limit=4 * 1024 * 1024)
    if sha(decoded) != DECODED_SHA:
        raise ValueError('Island model decoded identity changed')
    mdl = parse_mdl(decoded, allow_parent_rom=True)
    if (mbd['width'], mbd['height'], len(mdl['models']), len(mdl['placements'])) != (35, 37, 266, 9875):
        raise ValueError('Island source structure changed')
    city_placements = [placement for placement in mdl['placements']
                       if (placement['attached_reference'] or '').replace('\\', '/').lower().endswith('/cityi1.mdt')]
    if len(city_placements) != 23 or not any(placement['fields'][3:5] == [477, 209]
                                               for placement in city_placements):
        raise ValueError('CityI1 placement anchor changed')
    city_decoded = decode_csvz(pinned(folder / 'CityI1/cityI1.mdlZ', CITY_MDL_SHA),
                              limit=4 * 1024 * 1024)
    if sha(city_decoded) != CITY_DECODED_SHA:
        raise ValueError('Town model decoded identity changed')
    city_mdl = parse_mdl(city_decoded, allow_parent_rom=True)
    parent_placements = [placement for placement in city_mdl['placements']
                         if (placement['attached_reference'] or '').replace('\\', '/').lower().endswith('/island01.mdt')]
    if len(parent_placements) != 23:
        raise ValueError('Town-to-island asset reference count changed')
    if any(sum(layer[0] >= 0 for layer in model['layers']) != 1 or
           model['layers'][0][0] < 0 for model in mdl['models']):
        raise ValueError('Island model layer policy unqualified')
    groups = {}
    for placement in mdl['placements']:
        groups.setdefault(tuple(placement['block']), []).append(placement)

    def order(placement):
        model = mdl['models'][placement['fields'][0]]
        tile, _, dy = model['layers'][0]
        return placement['fields'][2] + mdl['tiles'][tile]['fields'][2] + dy

    for group in groups.values():
        group.sort(key=order)
    binary = Path(executable).resolve()
    if not binary.is_file():
        raise ValueError('Compiled C++ outdoor projector missing')
    windows = []
    for cx, cy in centers:
        blocks = [mbd['blocks'][y * mbd['width'] + x]
                  if 0 <= x < mbd['width'] and 0 <= y < mbd['height'] else None
                  for y in range(cy - 1, cy + 2) for x in range(cx - 1, cx + 2)]
        expected = project_base_window(blocks, bytes([255]) * 3969)
        objects = []
        for gy in range(cy - 2, cy + 2):
            for gx in range(cx - 2, cx + 2):
                for placement in groups.get((gx, gy), []):
                    fields = placement['fields']
                    model = mdl['models'][fields[0]]
                    grid = model['grids'][fields[5]]
                    cells = bytes(map(int, decoded[grid['start']:grid['end_exclusive']].split()))
                    points = canonical_points(model['extra_8_ints'])
                    x, y = fields[3] - cx * 21 + 21, fields[4] - cy * 21 + 21
                    expected = apply_model_pass(expected, x, y, grid['width'], grid['height'], cells)
                    expected = apply_model_points(expected, x, y, points)
                    objects.append([x, y, grid['width'], grid['height'],
                                    *points[0], *points[1], *cells])
        tokens = []
        for block in blocks:
            tokens.append(int(block is not None))
            if block is not None:
                tokens.extend(block)
        tokens.append(len(objects))
        for item in objects:
            tokens.extend(item)
        result = subprocess.run([str(binary), '--dump'], input=' '.join(map(str, tokens)),
                                text=True, capture_output=True, timeout=20, check=True)
        cpp = result.stdout.strip()
        independently_projected = ''.join('??' if value == 255 else f'{value:02x}' for value in expected)
        if cpp != independently_projected:
            raise ValueError(f'Island static projection disagrees with C++ at {cx},{cy}')
        windows.append({'block_x': cx, 'block_y': cy, 'origin_x': cx * 21 - 21,
                        'origin_y': cy * 21 - 21, 'cells_hex': cpp,
                        'known_cells': sum(value != 255 for value in expected),
                        'placement_count': len(objects), 'sha256': sha(cpp.encode('ascii'))})
    overlap = {}
    for window in windows:
        for y in range(63):
            for x in range(63):
                value = window['cells_hex'][(y * 63 + x) * 2:(y * 63 + x) * 2 + 2]
                if value != '??':
                    overlap.setdefault((window['origin_x'] + x, window['origin_y'] + y), set()).add(value)
    conflicts = [{'x': x, 'y': y, 'values': sorted(values)}
                 for (x, y), values in sorted(overlap.items()) if len(values) > 1]
    return {'schema': 'god2-recovered-island01-entry-navigation-v1',
            'area': 2, 'scene': 0, 'kind': 1, 'windows': windows,
            'asset_adjacency_candidates': {
                'town_references_to_island': [placement['fields'][3:5]
                                              for placement in parent_placements],
                'island_references_to_city': [placement['fields'][3:5]
                                              for placement in city_placements],
                'route_verified': False},
            'scope': 'NINE_STATIC_WINDOWS_NEAR_CITYI1; NO_SCENE_ROUTE_OR_ENCOUNTER_AUTHORITY',
            'cross_window': {'covered_coordinates': len(overlap),
                             'conflicts': conflicts,
                             'policy': 'CONFLICTS_REJECT_MOVEMENT_IN_ANY_FUTURE_SERVER_IMPORT'},
            'sources': {'catalog_sha256': CATALOG_SHA,
                        'mbd_sha256': MBD_SHA, 'mbdz_sha256': MBDZ_SHA, 'mdl_sha256': MDL_SHA,
                        'mdl_decoded_sha256': DECODED_SHA,
                        'city_mdl_sha256': CITY_MDL_SHA,
                        'city_mdl_decoded_sha256': CITY_DECODED_SHA,
                        'cpp_projector_sha256': sha(binary.read_bytes())},
            'dynamic_occupancy_included': False, 'server_loaded': False,
            'runtime_validated': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--client', type=Path, required=True)
    parser.add_argument('--executable', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.resolve().is_relative_to(args.client.resolve()):
        parser.error('Output must not modify original client')
    report = build(args.client, args.executable)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n', encoding='ascii')
    print(json.dumps({'windows': len(report['windows']),
                      'known_cells': sum(row['known_cells'] for row in report['windows']),
                      'cross_window_conflicts': len(report['cross_window']['conflicts']),
                      'server_loaded': False, 'runtime_validated': False}))


if __name__ == '__main__':
    main()
