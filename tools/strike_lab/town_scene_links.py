"""Current CityI1 explicit indoor asset links, not authorized teleport routes."""
import argparse
import hashlib
import json
from pathlib import Path

from .current_monster_binary_producer import parse_mdl
from .omega_assets import decode_csvz
from .town_navigation import MDL_SHA, MDL_DECODED_SHA, pinned
from .world_scenes import parse_can

CAN_SHA = 'f2b9ca9dc4dcebcd1c1c40de14ea63f1b2061993f644c49b9c7baca9ce2d2f97'


def build_links(client):
    client = Path(client).resolve()
    area = client / 'Data2/map/island01'
    mdl_path = area / 'CityI1/cityI1.mdlZ'
    can_path = area / 'Island01.can'
    for path in (mdl_path, can_path):
        if not path.resolve().is_relative_to(client):
            raise ValueError('Source escapes current client')
    raw = pinned(mdl_path, MDL_SHA)
    decoded = decode_csvz(raw, limit=4*1024*1024)
    if hashlib.sha256(decoded).hexdigest() != MDL_DECODED_SHA:
        raise ValueError('Town decoded identity changed')
    mdl = parse_mdl(decoded, allow_parent_rom=True)
    can = parse_can(pinned(can_path, CAN_SHA))
    links = []
    for index, placement in enumerate(mdl['placements']):
        reference = placement['attached_reference']
        if reference is None or not reference.lower().endswith('.hmd'):
            continue
        target = (mdl_path.parent / reference.replace('\\', '/')).resolve()
        if not target.is_relative_to(area.resolve()):
            raise ValueError('Attached indoor asset escapes pinned area')
        records = [r for r in can['files']
                   if (area / r['asset_path']).resolve() == target]
        record_ids = {r['file_index'] for r in records}
        candidates = [i for i, v in enumerate(can['scene_file_indices']) if v in record_ids]
        fields = placement['fields']
        links.append({
            'placement_index': index,
            'decoded_offset': placement['offset'],
            'decoded_end_exclusive': placement['end_exclusive'],
            'source_record_sha256': placement['sha256'],
            'attached_reference': reference,
            'asset_path': target.relative_to(client).as_posix(),
            'raw_block': placement['block'], 'raw_fields': fields,
            'model_index': fields[0],
            'raw_model_entry_pairs': mdl['models'][fields[0]]['extra_8_ints'],
            'can_record_indices': sorted(record_ids),
            'scene_candidates': candidates,
            'destination_scene': None,
            'route_verified': False,
        })
    return {
        'schema': 'god2-current-town-asset-links-v1',
        'scope': 'EXPLICIT_ASSET_REFERENCES_ONLY_NOT_TELEPORT_ROUTES',
        'area': 2, 'source_scene': 4,
        'sources': {'mdl_sha256': MDL_SHA, 'mdl_decoded_sha256': MDL_DECODED_SHA,
                    'can_sha256': CAN_SHA},
        'links': links,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--client', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.resolve().is_relative_to(args.client.resolve()):
        raise ValueError('Evidence output must be outside original client')
    result = build_links(args.client)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'links': len(result['links']), 'verified_routes': 0,
                      'output': str(args.output)}))


if __name__ == '__main__':
    main()
