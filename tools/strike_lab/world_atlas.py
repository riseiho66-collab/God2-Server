"""Import the current client's map catalog without inventing world placements."""
import argparse
import hashlib
import json
from pathlib import Path, PureWindowsPath
import re

from .omega_assets import decode_csvz

SECTION = b'Map_City_Coordniate'
SOURCE = 'Data2/Patch/Comm/gamedata.csvZ'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def relative_asset(value):
    try:
        text = value.decode('ascii')
    except UnicodeDecodeError as error:
        raise ValueError('Non-ASCII map asset path needs explicit byte-path handling') from error
    path = PureWindowsPath(text)
    if not text or path.is_absolute() or path.drive or path.root or '..' in path.parts or ':' in text:
        raise ValueError('Map asset path escapes its client subtree')
    return path.as_posix()


def parse_catalog(decoded):
    # Original 51AE0/51B50 split byte fields on commas, not quoted CSV rules.
    lines = decoded.split(b'\n')
    sections = [i for i, line in enumerate(lines) if line.startswith(SECTION+b',')]
    if len(sections) != 1:
        raise ValueError('Expected one map catalog section')
    start = sections[0]
    count = int(lines[start].rstrip(b'\r').split(b',')[1])
    if not 1 <= count <= 32767 or start+count >= len(lines):
        raise ValueError('Invalid map catalog count')
    result, seen = [], set()
    for index, raw in enumerate(lines[start+1:start+count+1]):
        raw = raw.rstrip(b'\r')
        fields = raw.split(b',')
        if not 14 <= len(fields) <= 24 or any(b'\0' in field for field in fields):
            raise ValueError('Invalid map record width or embedded NUL')
        # Original loader copies into fixed 16/64 byte string fields.
        for column, capacity in ((0,16),(1,16),(2,16),(8,64),(9,64),(10,64)):
            if len(fields[column]) >= capacity:
                raise ValueError('Map string exceeds original loader capacity')
        if any(len(field) >= 16 for field in fields[14:]):
            raise ValueError('Map layer label exceeds original loader capacity')
        # The original atoi path maps absent numeric strings to zero; the
        # current oldreborn row actually leaves layer dimensions blank.
        numeric = {column:int(fields[column] or b'0') for column in (3,4,5,6,7,11,12,13)}
        area, kind, scene = (numeric[i] for i in (3,4,5))
        if not 1 <= area <= 16 or not 0 <= scene <= 1023 or not 0 <= kind <= 3:
            raise ValueError('Map selector exceeds current packed-field bounds')
        if any(not 0 <= numeric[i] <= 32767 for i in (6,7,11,12)) or not 1 <= numeric[13] <= 32767:
            raise ValueError('Invalid map coordinate/dimension value')
        key = area | (scene << 6)
        if key in seen:
            raise ValueError('Duplicate packed map selector')
        seen.add(key)
        map_path = fields[10]
        # The Umg catalog row has one leading separator. Audit it under the
        # map subtree while retaining the untouched source field above.
        if map_path[:1] in (b'\\',b'/') and map_path[1:2] not in (b'\\',b'/'):
            map_path = map_path[1:]
        result.append({
            'source_record_index':index, 'source_line':start+index+2,
            'source_record_sha256':digest(raw), 'raw_fields_hex':[f.hex() for f in fields],
            'area':area, 'scene':scene, 'packed_selector':key, 'kind':kind,
            'asset_stem':fields[1].decode('ascii'),
            'region_name_bytes':fields[0].hex(), 'map_name_bytes':fields[2].hex(),
            'catalog_x':numeric[6], 'catalog_y':numeric[7],
            'layer_width':numeric[11], 'layer_height':numeric[12],
            'layers_per_row':numeric[13],
            'mdt_relative':'Data2/map/'+relative_asset(map_path),
            'music_relative':relative_asset(fields[8]),
            'fight_music_relative':relative_asset(fields[9]),
            'layer_labels_bytes':[f.hex() for f in fields[14:]],
            'spawn':None, 'collision':None,
        })
    return result


def asset_variants(root, relative):
    result = []
    for suffix in ('', 'Z'):
        path = root / (relative+suffix)
        if not path.resolve().is_relative_to(root.resolve()):
            raise ValueError('Asset symlink escapes client root')
        if not path.is_file():
            continue
        raw = path.read_bytes()
        plain = decode_csvz(raw) if suffix else raw
        header = re.search(rb'(?:^|\r?\n)MAPNUM[ \t]+([0-9]+)[ \t]+([0-9]+)(?:\r?\n|$)', plain)
        result.append({'path':relative+suffix, 'sha256':digest(raw),
                       'decoded_sha256':digest(plain), 'decoded_size':len(plain),
                       'mapnum':[int(header[1]),int(header[2])] if header else None})
    return result


def build_atlas(client_root):
    root = Path(client_root).resolve()
    source = root/SOURCE
    if not source.resolve().is_relative_to(root):
        raise ValueError('Catalog source escapes client root')
    raw = source.read_bytes()
    decoded = decode_csvz(raw)
    records = parse_catalog(decoded)
    for record in records:
        record['mdt_variants'] = asset_variants(root, record['mdt_relative'])
        stem = str(PureWindowsPath(record['mdt_relative']).with_suffix('')).replace('\\','/')
        record['companion_files'] = {}
        for extension in ('.mdl','.mbd','.mmb'):
            variants = []
            for suffix in ('','Z'):
                path = root/(stem+extension+suffix)
                if not path.resolve().is_relative_to(root):
                    raise ValueError('Map companion escapes client root')
                if path.is_file():
                    variants.append({'path':stem+extension+suffix,'size':path.stat().st_size})
            record['companion_files'][extension[1:]] = variants
    return {
        'schema':'god2-current-map-atlas-v1',
        'source':{'file':SOURCE,'sha256':digest(raw),'decoded_sha256':digest(decoded),
                  'section':SECTION.decode(),'loader_rva':'0x59a80','lookup_rva':'0x59d80'},
        'qualification':'CURRENT_CLIENT_DATA; parser/lookup qualification is separate from live rendering',
        'coordinate_policy':'catalog_x/y are raw catalog values, not player/NPC spawn positions; units unqualified',
        'asset_policy':'present plain/Z alternatives retained; filesystem presence does not prove runtime selection or rendering',
        'counts':{'maps_total':len(records),'maps_imported':len(records),
                  'maps_with_mdt':sum(bool(r['mdt_variants']) for r in records),
                  'maps_server_loaded':0,'maps_runtime_validated':0,'npc_placements_imported':0,
                  'monster_spawns_imported':0,'teleports_imported':0},
        'maps':records,
    }


def qualify_selector(atlas, area, scene):
    records = [r for r in atlas['maps'] if (r['area'],r['scene']) == (area,scene)]
    return {'area':area,'scene':scene,'catalog_match':bool(records),
            'records':records, 'runtime_accepted':False,
            'reason':'FOUND_IN_CURRENT_CATALOG' if records else 'ABSENT_FROM_CURRENT_CATALOG'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--client', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--selector', type=int, nargs=2, metavar=('AREA','SCENE'))
    args = parser.parse_args()
    output = args.output.resolve()
    if output.is_relative_to(args.client.resolve()):
        parser.error('Atlas output must not modify the original client directory')
    atlas = build_atlas(args.client)
    if args.selector:
        atlas['selector_qualification'] = qualify_selector(atlas, *args.selector)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(atlas,indent=2,sort_keys=True)+'\n',encoding='ascii')
    print(json.dumps(atlas['counts'],sort_keys=True))
    if args.selector:
        print(atlas['selector_qualification']['reason'])


if __name__ == '__main__':
    main()
