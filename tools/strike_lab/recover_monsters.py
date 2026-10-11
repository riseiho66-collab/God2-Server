"""Deterministic monster definition extraction and bounded legacy evidence audit."""
import argparse
import hashlib
import json
from pathlib import Path
import sqlite3

from .omega_assets import decode_csvz
from .world_atlas import digest

LIMIT = 16 * 1024 * 1024
CLIENT_TABLES = ('Data2/Patch/eny.csvZ', 'Data2/Patch/FightEny.csvZ')
CLASSIC_JSON = (
    'db/imports/official/monsters/monsters.official.json',
    'db/imports/official/spawns/spawns.official.json',
    'db/imports/live/monsters/monsters.verified.latest.json',
)
CLASSIC_CODE = (
    'database/schema/295_add_monster_spawn_drop_design_candidates.sql',
    'database/schema/299_apply_first_wave_monster_spawn_server_design.sql',
    'src/God2.ClassicServer.Persistence/MariaDbCanonicalCatalogRepositories.cs',
)
CAPTURE_TABLES = ('monster_stat_capture', 'monster_skill_capture',
                  'map_encounter_sample', 'monster_drop_sample')
UNKNOWN = ('server_template_id', 'level', 'hp', 'mp', 'damage', 'defense',
           'map', 'spawn_x', 'spawn_y', 'spawn_count', 'respawn', 'drops',
           'constitution', 'strength', 'intelligence', 'speed',
           'physical_attack', 'physical_defense', 'magical_attack', 'magical_defense',
           'metal', 'wood', 'water', 'fire', 'earth', 'skills', 'drop_items', 'drop_rates')


def read_source(root, relative):
    root = Path(root).resolve()
    path = (root / relative).resolve()
    if not path.is_relative_to(root):
        raise ValueError('Source escapes input root')
    with path.open('rb') as stream:
        raw = stream.read(LIMIT + 1)
    if len(raw) > LIMIT:
        raise ValueError('Source exceeds bounded import size')
    return raw, {'file': relative, 'sha256': digest(raw), 'size': len(raw)}


def parse_definition(decoded, kind):
    """Use exact source headers; retain unnamed columns and positions as bytes."""
    lines = decoded.splitlines(keepends=True)
    if not lines or kind not in ('field', 'battle'):
        raise ValueError('Missing table or invalid kind')
    first = lines[0].rstrip(b'\r\n').split(b',')
    start = int(first[2]) - 1
    if not 2 <= start < len(lines):
        raise ValueError('Invalid data start line')
    header = lines[start - 1].rstrip(b'\r\n').split(b',')
    # Labels are copied from current-client CP950 headers, not positional guesses.
    expected = ({0: '\u7d22\u5f15', 1: 'ROM \u6a94', 8: '\u540d\u7a31'}
                if kind == 'field' else
                {0: '\u6575\u4eba\u540d\u7a31', 1: '\u6575\u4eba\u4ee3\u865f',
                 5: '\u6a94\u540d', 6: '\u6211\u65b9\u6a94\u540d'})
    if any(i >= len(header) or header[i] != label.encode('cp950')
           for i, label in expected.items()):
        raise ValueError('Unrecognized definition header')
    columns = ({'source_index': 0, 'rom_path': 1, 'name_bytes': 8}
               if kind == 'field' else
               {'monster_code': 1, 'name_bytes': 0, 'rom_path': 5, 'ally_rom_path': 6})
    rows, seen = [], set()
    offset = sum(map(len, lines[:start]))
    blank_count = 0
    for index, raw in enumerate(lines[start:], start + 1):
        current_offset = offset
        offset += len(raw)
        fields = raw.rstrip(b'\r\n').split(b',')
        if not raw.strip():
            blank_count += 1
            continue
        id_column = 0 if kind == 'field' else 1
        if len(raw) > 4096 or len(fields) <= id_column or b'\0' in raw:
            raise ValueError('Invalid definition record')
        identity = int(fields[id_column])
        if identity < 0 or identity in seen:
            raise ValueError('Negative or duplicate definition identity')
        seen.add(identity)
        known = {}
        for key, column in columns.items():
            if column >= len(fields):
                known[key] = {'value': None, 'source_column': column,
                              'header_hex': header[column].hex(), 'present': False}
                continue
            value = fields[column]
            if column == id_column:
                value = identity
            elif key == 'name_bytes':
                value = value.hex()
            else:
                value = value.decode('ascii')
            known[key] = {'value': value, 'source_column': column,
                          'header_hex': header[column].hex(), 'present': True}
        rows.append({'source_line': index, 'source_offset': current_offset,
                     'source_record_sha256': digest(raw), 'raw_record_hex': raw.hex(),
                     'raw_fields_hex': [f.hex() for f in fields], 'known_fields': known,
                     'uninterpreted_columns': [i for i in range(len(fields))
                                               if i not in columns.values()],
                     'unknown_fields': list(UNKNOWN), 'runtime_eligible': False})
    return {'kind': kind, 'header_line': start, 'header_fields_hex': [f.hex() for f in header],
            'preamble_hex': b''.join(lines[:start]).hex(),
            'decoded_sha256': digest(decoded), 'data_start_line': start + 1,
            'source_data_lines': len(lines) - start, 'blank_data_lines': blank_count,
            'records_imported': len(rows), 'records': rows}


def audit_json(root, relative, retain_records=True):
    raw, source = read_source(root, relative)
    data = json.loads(raw)
    records = data['records']
    if not isinstance(records, list) or data['recordCount'] != len(records):
        raise ValueError('Legacy record denominator mismatch')
    result = {'source': source, 'declared_records': data['recordCount'],
              'observed_records': len(records),
              'metadata': {k: v for k, v in data.items() if k != 'records'},
              'authority': 'legacy_claim_only; no current-client identity promotion'}
    if retain_records:
        result['raw_records'] = records
    return result


def audit_xjz(root):
    path = (Path(root).resolve() / 'xjz_evidence.sqlite').resolve()
    if not path.is_relative_to(Path(root).resolve()):
        raise ValueError('Database escapes input root')
    # URI read-only mode also fails if the source is absent; never creates a DB.
    connection = sqlite3.connect(path.as_uri() + '?mode=ro', uri=True)
    try:
        connection.execute('PRAGMA query_only=ON')
        connection.row_factory = sqlite3.Row
        results = {}
        for table in ('monster_visual_template',) + CAPTURE_TABLES:
            count = connection.execute('SELECT COUNT(*) FROM ' + table).fetchone()[0]
            entry = {'source_rows': count}
            if table in CAPTURE_TABLES:
                if count > 32767:
                    raise ValueError('Capture table exceeds import bound')
                records = [dict(r) for r in connection.execute('SELECT * FROM ' + table)]
                entry['raw_records'] = sorted(records, key=lambda r: json.dumps(r, sort_keys=True))
                entry['authority'] = 'legacy_sample; unbound to current definitions'
            results[table] = entry
        with path.open('rb') as stream:
            sha256 = hashlib.file_digest(stream, 'sha256').hexdigest()
        return {'source': {'file': 'xjz_evidence.sqlite', 'sha256': sha256},
                'mode': 'ro', 'tables': results}
    finally:
        connection.close()


def build_monsters(client, classic, xjz):
    tables = []
    for relative, kind in zip(CLIENT_TABLES, ('field', 'battle')):
        raw, source = read_source(client, relative)
        tables.append({'source': source, **parse_definition(decode_csvz(raw), kind)})
    legacy = [audit_json(classic, p, i != 0) for i, p in enumerate(CLASSIC_JSON)]
    code = []
    for relative in CLASSIC_CODE:
        raw, source = read_source(classic, relative)
        code.append({'source': source, 'raw_utf8': raw.decode('utf-8-sig'),
                     'authority': 'legacy_design_or_consumer; not official placement evidence'})
    xjz_audit = audit_xjz(xjz)
    return {
        'schema': 'god2-monster-evidence-v1',
        'qualification': 'Definition extraction only; no runtime/server/client integration',
        'policy': 'Current client definitions win. No implicit field-index/battle-code join. '
                  'Position-labelled visual columns remain uninterpreted, never spawn coordinates. '
                  'Legacy SQL is retained verbatim, never executed or promoted.',
        'counts': {'field_definitions': tables[0]['records_imported'],
                   'battle_definitions': tables[1]['records_imported'],
                   'classic_template_source_rows': legacy[0]['observed_records'],
                   'classic_spawn_candidate_source_rows': legacy[1]['observed_records'],
                   'classic_level_claim_source_rows': legacy[2]['observed_records'],
                   'spawn_instances_imported': 0, 'runtime_integrated': 0},
        'definition_tables': tables, 'legacy_json': legacy, 'legacy_code': code,
        'xjz_audit': xjz_audit, 'spawn_instances': [], 'unknown_fields': list(UNKNOWN),
        'next_hook': {'source': CLASSIC_CODE[2],
                      'query_contains': 'FROM `god2_game`.`monster_spawns` WHERE `enabled`=1',
                      'required_evidence': 'Read-only export of that query with each row source policy; '
                      'prove map/template bindings before creating C++/Lua spawn instances.'},
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('client', 'classic', 'xjz', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args(argv)
    output = args.output.resolve()
    if any(output.is_relative_to(root.resolve()) for root in (args.client, args.classic, args.xjz)):
        parser.error('Output must be outside all original/legacy roots')
    result = build_monsters(args.client, args.classic, args.xjz)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n',
                      encoding='ascii', newline='\n')
    print(json.dumps(result['counts'], sort_keys=True))


if __name__ == '__main__':
    main()
