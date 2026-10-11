"""Complete current EnyName identity inventory, not a wild-monster stat table."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import re

from .omega_assets import decode_csvz

ROOT = Path(__file__).resolve().parents[2]
SOURCE = 'Data2/Patch/Comm/gamedata.csvZ'
SOURCE_SHA = '70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731'
PLAIN_SHA = '75c3c37947a64b0917fbf8e546884d9bf893fe6a606d3e2b8f3b1857966b1815'
FIELDS = ('level', 'hp', 'mp', 'constitution', 'strength', 'intelligence', 'speed',
          'physical_attack', 'magical_attack', 'physical_defense', 'magical_defense',
          'metal', 'wood', 'water', 'fire', 'earth', 'base_experience', 'capturable',
          'skill_assignments', 'drop_items', 'drop_rates')


def parse_enemy_catalog(plain):
    """Preserve every source occurrence and native repeated-area replacement."""
    lines = plain.splitlines(keepends=True)
    starts = [i for i, line in enumerate(lines) if line.startswith(b'EnyName,')]
    if len(starts) != 1 or lines[starts[0]].rstrip(b'\r\n') != b'EnyName,7931':
        raise ValueError('Expected current EnyName section')
    offsets, total_bytes = [], 0
    for line in lines:
        offsets.append(total_bytes)
        total_bytes += len(line)
    cursor = first = starts[0] + 1

    def row():
        nonlocal cursor
        if cursor >= len(lines) or len(lines[cursor]) >= 2048 or b'\0' in lines[cursor]:
            raise ValueError('EnyName input bound')
        raw = lines[cursor]
        cursor += 1
        return next(csv.reader([raw.decode('latin1')], strict=True))

    if row() != ['EnyNameTotal', '7815']:
        raise ValueError('Unexpected EnyName total')
    groups, group_offsets, loaded_groups, records = {}, {}, [], []
    generation = 0
    while len(records) < 7815:
        header = row()
        if len(header) != 3 or header[0] != 'EnyNameIsland_Area':
            raise ValueError('Expected EnyName area')
        area, count = map(int, header[1:])
        if not 0 <= area < 17 or not 1 <= count <= 256:
            raise ValueError('EnyName area bound')
        generation += 1
        for record in records:
            if record['area'] == area:
                record['lookup_visible'] = False
        for key in [key for key in groups if key[0] == area]:
            del groups[key]
            del group_offsets[key]
        for _ in range(count):
            header = row()
            if len(header) != 3 or header[0] != 'EnyNameAreaId_Idx':
                raise ValueError('Expected EnyName scene')
            scene, size = map(int, header[1:])
            if (not 0 <= scene <= 65535 or (area, scene) in groups
                    or not 1 <= size <= 7815 - len(records)):
                raise ValueError('EnyName scene bound')
            entries, group_start = [], len(records)
            for ordinal in range(1, size + 1):
                fields = row()
                if len(fields) not in (6, 10) or len(fields[1].encode('latin1')) > 15:
                    raise ValueError('EnyName record bound')
                numbers = [int(fields[i]) for i in (0, 2, 3, 4, 5)]
                if any(not 0 <= value <= 0x7fffffff for value in numbers):
                    raise ValueError('EnyName numeric bound')
                if 5001 <= numbers[3] <= 5003 and numbers[2] & 1:
                    if len(fields) != 10 or any(not re.fullmatch(
                            '[0-7]' + component + '[0-9][0-9]{1,2}', fields[column])
                            for column, component in ((6, 'h'), (7, 'f'), (8, 'b'), (9, 'w'))):
                        raise ValueError('EnyName component bound')
                raw = lines[cursor - 1]
                records.append({
                    'source_record_index': len(records), 'source_line': cursor,
                    'source_offset': offsets[cursor - 1],
                    'record_sha256': hashlib.sha256(raw).hexdigest(),
                    'raw_record_hex': raw.hex(), 'fields_hex': [f.encode('latin1').hex() for f in fields],
                    'area_generation': generation, 'area': area, 'scene': scene,
                    'ordinal': ordinal, 'lookup_visible': True,
                    'source_label': numbers[0], 'name_bytes_hex': fields[1].encode('latin1').hex(),
                })
                entries.append(fields)
            groups[area, scene] = entries
            group_offsets[area, scene] = group_start
            loaded_groups.append((area, scene, group_start, entries))
    if cursor >= len(lines) or not lines[cursor].startswith(b'SpecialEnyInfo,'):
        raise ValueError('EnyName did not consume exact source envelope')
    return dict(records=records, groups=groups, group_offsets=group_offsets,
                loaded_groups=loaded_groups,
                stream=b''.join(lines[first:cursor]).replace(b'\r\n', b'\n'))


def pinned_catalog(client=ROOT.parent / 'God2'):
    root = Path(client).resolve()
    path = (root / SOURCE).resolve()
    if not path.is_relative_to(root) or path.stat().st_size > 1024 * 1024:
        raise ValueError('Current enemy source path/size bound')
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != SOURCE_SHA:
        raise ValueError('Current enemy source identity changed')
    plain = decode_csvz(raw, limit=4 * 1024 * 1024)
    if hashlib.sha256(plain).hexdigest() != PLAIN_SHA:
        raise ValueError('Current enemy decoded identity changed')
    return parse_enemy_catalog(plain)


def build_inventory(client=ROOT.parent / 'God2'):
    catalog = pinned_catalog(client)
    rows = catalog['records']
    visible = sum(row['lookup_visible'] for row in rows)
    for row in rows:
        row['native_values'] = dict.fromkeys(FIELDS)
        row['monster_classification'] = None
    return {
        'schema': 'god2-current-monster-identity-inventory-v1',
        'source': SOURCE, 'source_sha256': SOURCE_SHA, 'decoded_sha256': PLAIN_SHA,
        'identity_scope': 'EnyName lookup occurrences; not deduplicated monster species',
        'requested_scope': ['normal', 'boss', 'elite', 'quest', 'event', 'summoned'],
        'classification_policy': 'Unproven; never infer class or capturability from a name or art',
        'assignment_policy': 'A global skill/item catalog or one received result does not prove a monster repertoire or drop table',
        'drop_rate_policy': 'Require original probability semantics, unit/denominator and conditions; never infer from guessed weights or a few samples',
        'loader_rva': '0x5a1a0', 'lookup_rva': '0x5a0a0',
        'summary': {'source_records': len(rows), 'source_groups': len(catalog['loaded_groups']),
                    'lookup_visible_records': visible, 'lookup_visible_groups': len(catalog['groups']),
                    'superseded_records': len(rows) - visible, 'unique_wild_monsters': None,
                    'all_monster_systems_enumerated': False},
        'field_coverage': {name: {'verified_lookup_records': 0, 'unresolved_lookup_records': visible,
                                 'verified_percent_of_lookup_records': 0.0} for name in FIELDS},
        'runtime_eligible': False,
        'records': rows,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--client', type=Path, default=ROOT.parent / 'God2')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = build_inventory(args.client)
    target = args.output.resolve()
    if target.is_relative_to(args.client.resolve()):
        raise ValueError('Refusing output inside original client')
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, ensure_ascii=True, sort_keys=True, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'output': str(target), **report['summary']}, sort_keys=True))


if __name__ == '__main__':
    main()
