"""Bounded import of area-base CAN scene tables, without world placements."""
import argparse
import json
from pathlib import Path, PureWindowsPath
import struct

from .omega_assets import decode_csvz
from .world_atlas import SOURCE, asset_variants, digest, parse_catalog, relative_asset

MAGIC = b'CAN v1.0'
# Manager +0x126c counts pointers at +0x1270..+0x166f; +0x1068
# holds the scene count, independently capped at 256 by the original assert.
MAX_FILES = 256
MAX_SCENES = 256
RECORD_SIZE = 64
MAX_CAN_SIZE = 16 + MAX_FILES * RECORD_SIZE + MAX_SCENES * 2


def _scene_path(raw):
    relative = relative_asset(raw)
    # Win32 strips trailing dots/spaces and recognizes device names even with
    # extensions. Reject aliases before letting pathlib normalize components.
    parts = raw.decode('ascii').replace('\\', '/').split('/')
    for part in parts:
        if (not part or part in ('.', '..') or part.rstrip(' .') != part
                or any(ord(c) < 32 or c in '<>"|?*' for c in part)
                or PureWindowsPath(part).is_reserved()):
            raise ValueError('Invalid or escaping CAN asset path')
    return relative


def parse_can(raw):
    """Validate exact on-disk lengths before interpreting bounded records."""
    if not 16 <= len(raw) <= MAX_CAN_SIZE or raw[:8] != MAGIC:
        raise ValueError('Invalid CAN header or length')
    file_count = struct.unpack_from('<I', raw, 8)[0]
    if file_count > MAX_FILES:
        raise ValueError('CAN file count exceeds 256 pointer slots')
    scene_count_offset = 12 + file_count * RECORD_SIZE
    if len(raw) < scene_count_offset + 4:
        raise ValueError('Truncated CAN records or scene count')
    scene_count = struct.unpack_from('<I', raw, scene_count_offset)[0]
    if scene_count > MAX_SCENES:
        raise ValueError('CAN scene count exceeds 256 entries')
    indices_offset = scene_count_offset + 4
    if len(raw) != indices_offset + scene_count * 2:
        raise ValueError('Truncated CAN scene indices or trailing bytes')
    files = []
    for index in range(file_count):
        offset = 12 + index * RECORD_SIZE
        record = raw[offset:offset + RECORD_SIZE]
        terminator = record.find(b'\0', 1)
        if terminator == -1:
            raise ValueError('CAN path lacks a NUL within its 63-byte field')
        path = record[1:terminator]
        files.append({
            'file_index': index, 'source_offset': offset,
            'raw_record_hex': record.hex(), 'source_record_sha256': digest(record),
            'raw_tag': record[0], 'raw_path_hex': path.hex(),
            'asset_path': _scene_path(path),
        })
    indices = list(struct.unpack_from('<' + 'H' * scene_count, raw, indices_offset))
    if any(index >= file_count for index in indices):
        raise ValueError('CAN scene file index outside raw records')
    return {'file_count': file_count, 'scene_count': scene_count,
            'files': files, 'scene_file_indices': indices}


def _contained(root, relative, subtree=None):
    path = root / relative
    if not path.resolve().is_relative_to(subtree or root):
        raise ValueError('CAN source or asset path escapes its client subtree')
    return path


def _read_bounded(path, limit):
    with path.open('rb') as stream:
        raw = stream.read(limit + 1)
    if len(raw) > limit:
        raise ValueError('Source file exceeds import length bound')
    return raw


def build_scenes(client_root):
    root = Path(client_root).resolve()
    catalog_raw = _read_bounded(_contained(root, SOURCE), 64 * 1024 * 1024)
    decoded = decode_csvz(catalog_raw)
    catalog = parse_catalog(decoded)
    bases = sorted((r for r in catalog if r['scene'] == 0), key=lambda r: r['area'])
    areas, scenes = [], []
    for base in bases:
        mdt = PureWindowsPath(base['mdt_relative'])
        relative = mdt.with_suffix('.can').as_posix()
        path = _contained(root, relative)
        area = {'area': base['area'], 'catalog_source_record_index': base['source_record_index'],
                'catalog_source_record_sha256': base['source_record_sha256'],
                'base_mdt_relative': base['mdt_relative'], 'can_relative': relative,
                'source': None, 'file_count': 0, 'scene_count': 0,
                'files': [], 'scene_file_indices': []}
        areas.append(area)
        if not path.is_file():
            continue
        raw = _read_bounded(path, MAX_CAN_SIZE)
        area.update(parse_can(raw))
        area['source'] = {'file': relative, 'sha256': digest(raw), 'size': len(raw),
                          'raw_hex': raw.hex()}
        parent = mdt.parent.as_posix()
        subtree = _contained(root, parent).resolve()
        for record in area['files']:
            asset_relative = parent + '/' + record['asset_path']
            for suffix in ('', 'Z'):
                _contained(root, asset_relative + suffix, subtree)
            record['asset_relative'] = asset_relative
            record['asset_variants'] = asset_variants(root, asset_relative)
        for scene, file_index in enumerate(area['scene_file_indices']):
            record = area['files'][file_index]
            scenes.append({'area': base['area'], 'scene': scene,
                           'packed_selector': base['area'] | (scene << 6),
                           'source_file': relative, 'source_sha256': digest(raw),
                           'source_offset': 16 + area['file_count'] * RECORD_SIZE + scene * 2,
                           'file_index': file_index, 'raw_tag': record['raw_tag'],
                           'asset_relative': record['asset_relative'],
                           'asset_variants': record['asset_variants'],
                           'spawn': None, 'collision': None})
    return {
        'schema': 'god2-current-can-scenes-v1',
        'source': {'file': SOURCE, 'sha256': digest(catalog_raw),
                   'decoded_sha256': digest(decoded)},
        'qualification': 'CURRENT_CLIENT_DATA; original-code and live runtime qualification are separate',
        'source_policy': 'catalog(area,0) MDT with .can extension; scene asset paths use its parent directory',
        'tag_policy': 'raw_tag is an uninterpreted CAN byte, not a network kind',
        'asset_policy': 'plain/Z presence does not prove runtime selection, loading or rendering',
        'placement_policy': 'No spawn positions or collision geometry inferred from CAN scene rows',
        'counts': {'areas_total': len(bases),
                   'areas_with_can': sum(a['source'] is not None for a in areas),
                   'files_total': sum(a['file_count'] for a in areas),
                   'files_with_assets': sum(bool(f['asset_variants']) for a in areas for f in a['files']),
                   'scenes_total': len(scenes), 'scenes_imported': len(scenes),
                   'scenes_with_assets': sum(bool(s['asset_variants']) for s in scenes),
                   'scenes_server_loaded': 0, 'scenes_runtime_validated': 0,
                   'npc_placements_imported': 0, 'monster_spawns_imported': 0,
                   'teleports_imported': 0},
        'areas': areas, 'scenes': scenes,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--client', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    output = args.output.resolve()
    if output.is_relative_to(args.client.resolve()):
        parser.error('Scene output must not modify the original client directory')
    result = build_scenes(args.client)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n',
                      encoding='ascii', newline='\n')
    print(json.dumps(result['counts'], sort_keys=True))


if __name__ == '__main__':
    main()
