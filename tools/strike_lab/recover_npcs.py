"""Recover a bounded Classic NPC spawn definition slice; never enable runtime spawns."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sqlite3

from .omega_assets import decode_csvz

MIGRATION = 'database/schema/103_publish_live_stage3_stage7_runtime_slice.sql'
CODEC = 'src/God2.ClassicServer.Runtime/OfficialNpcReplicationWireCodec.cs'
CLIENT_NPC = 'Data2/Patch/NPC.csvZ'
MAX_BYTES = 8 * 1024 * 1024
MAX_ROWS = 4096  # Import resource bound, not a game rule.


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(',', ':'))


def read_source(root, relative):
    path = (root / relative).resolve()
    if not path.is_relative_to(root):
        raise ValueError('Source escapes root')
    with path.open('rb') as stream:
        raw = stream.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError('Source exceeds importer byte bound')
    return raw


def parse_spawn_insert(raw):
    """Use SQLite's parser for this literal INSERT, in an isolated memory DB."""
    if len(raw) > MAX_BYTES:
        raise ValueError('SQL exceeds importer byte bound')
    text = raw.decode('utf-8-sig')
    matches = list(re.finditer(
        r'INSERT INTO `god2_game`\.`npc_spawns`\s*'
        r'\((?P<columns>[^)]+)\)\s*VALUES\s*(?P<values>.*?)'
        r'\s*ON DUPLICATE KEY UPDATE', text, re.S))
    if len(matches) != 1:
        raise ValueError('Expected exactly one literal NPC spawn INSERT')
    match = matches[0]
    columns = match['columns'].strip()
    if not re.fullmatch(r'`[a-z_][a-z0-9_]*`(?:\s*,\s*`[a-z_][a-z0-9_]*`)*', columns):
        raise ValueError('Unsupported column syntax')
    names = re.findall(r'`([a-z_][a-z0-9_]*)`', columns)
    if len(names) != len(set(names)):
        raise ValueError('Duplicate column')
    literal = r"(?:-?[0-9]+|NULL|'(?:[^'\\]|'')*')"
    value_row = rf'\(\s*{literal}(?:\s*,\s*{literal})*\s*\)'
    if not re.fullmatch(rf'{value_row}(?:\s*,\s*{value_row})*', match['values']):
        raise ValueError('Only integer, NULL and SQL string literals are supported')
    with sqlite3.connect(':memory:', isolation_level=None) as db:
        db.row_factory = sqlite3.Row
        db.execute('CREATE TABLE recovered (' + columns + ')')
        # Source SQL may only insert literals into this one memory table.
        db.set_authorizer(lambda action, arg1, arg2, dbname, trigger:
                          sqlite3.SQLITE_OK if (action == sqlite3.SQLITE_INSERT
                          and arg1 == 'recovered') or action == sqlite3.SQLITE_SELECT
                          else sqlite3.SQLITE_DENY)
        try:
            db.execute('INSERT INTO recovered (' + columns + ') VALUES ' + match['values'])
        except sqlite3.Error as exc:
            raise ValueError('Unsupported or malformed literal spawn INSERT') from exc
        finally:
            db.set_authorizer(None)
        rows = [dict(row) for row in db.execute('SELECT * FROM recovered').fetchmany(MAX_ROWS + 1)]
    if not rows or len(rows) > MAX_ROWS:
        raise ValueError('Spawn row count outside importer bounds')
    seen = set()
    for row in rows:
        for key in ('spawn_id', 'npc_id', 'map_id', 'observed_client_entity_handle'):
            if type(row.get(key)) is not int or row[key] <= 0:
                raise ValueError('Missing or invalid source identifier: ' + key)
        for key in ('position_x', 'position_y'):
            if type(row.get(key)) is not int or not 0 <= row[key] <= 0x7fff:
                raise ValueError('Coordinates outside Classic codec 15-bit range')
        if row['spawn_id'] in seen:
            raise ValueError('Duplicate spawn_id')
        seen.add(row['spawn_id'])
    return sorted(rows, key=lambda row: row['spawn_id'])


def provenance(archive, file, raw, table=None, record_id=None, record=None):
    result = {'source_archive': archive, 'file': file, 'table': table,
              'record_id': record_id, 'sha256': digest(raw)}
    if record is not None:
        result['record_sha256'] = digest(canonical(record).encode('ascii'))
        result['record_hash_encoding'] = 'sorted compact ASCII JSON of source_fields'
    return result


def build_npcs(classic_root, xjz_root, client_root):
    classic, xjz, client = (Path(p).resolve() for p in (classic_root, xjz_root, client_root))
    raw = read_source(classic, MIGRATION)
    codec = read_source(classic, CODEC)
    codec_text = codec.decode('utf-8-sig')
    placements = []
    for row in parse_spawn_insert(raw):
        handle, x, y = (row[k] for k in ('observed_client_entity_handle', 'position_x', 'position_y'))
        pattern = rf'\b{handle}\s*=>\s*position\.X == {x} && position\.Y == {y}\b'
        if not re.search(pattern, codec_text):
            raise ValueError('Spawn lacks matching IsCapturedPosition consumer evidence')
        if any(row.get(k) != 'Verified' for k in (
                'wire_evidence_status', 'identity_evidence_status', 'coordinate_evidence_status')):
            raise ValueError('Selected slice contains an unverified legacy spawn')
        frames = re.findall(r'\b[0-9A-Fa-f]{48}\b', row.get('admin_note', ''))
        if len(frames) != 1 or digest(bytes.fromhex(frames[0])[2:23]) != row.get('application_message_sha256', '').lower():
            raise ValueError('Archived application frame hash does not match source claim')
        placements.append({
            'source_fields': row,
            'provenance': provenance('classic-20260820', MIGRATION, raw,
                                     'god2_game.npc_spawns', row['spawn_id'], row),
            'consumer_evidence': provenance('classic-20260820', CODEC, codec,
                                            record_id='IsCapturedPosition/Validate'),
            'coordinates': {'x': x, 'y': y, 'source_fields': ['position_x', 'position_y'],
                            'units': 'legacy packed-coordinate integer; physical scale unknown',
                            'qualification': 'archived SQL definition matched to legacy codec; current runtime unvalidated'},
            'map': {'legacy_map_id': row['map_id'], 'source_field': 'map_id',
                    'current_area': None, 'current_scene': None, 'crosswalk_status': 'unknown'},
            'runtime_eligible': False,
        })

    client_raw = read_source(client, CLIENT_NPC)
    decoded = decode_csvz(client_raw, limit=MAX_BYTES)
    lines = decoded.splitlines()
    header = lines[0].split(b',') if lines else []
    if len(header) < 3 or header[0] != b'NPC':
        raise ValueError('Unsupported current NPC table header')
    start = int(header[2])
    if not 2 <= start <= len(lines):
        raise ValueError('NPC data start outside table')
    template_rows = []
    for line_number, line in enumerate(lines[start - 1:], start):
        if not line.strip():
            continue
        fields = line.split(b',')
        if len(fields) != 10 or len(line) > 4095:
            raise ValueError('Unsupported NPC template row width')
        template_rows.append({'record_id': line_number, 'raw_hex': line.hex(),
                              'sha256': digest(line)})
    if len(template_rows) > MAX_ROWS:
        raise ValueError('Template row count exceeds importer bound')

    database = (xjz / 'xjz_evidence.sqlite').resolve()
    if not database.is_relative_to(xjz):
        raise ValueError('Evidence DB escapes root')
    # Never open the archived DB with write permissions or execute its stored SQL.
    inventories = []
    with sqlite3.connect(database.as_uri() + '?mode=ro', uri=True) as db:
        db.execute('PRAGMA query_only=ON')
        for table, kind in (
            ('npc_template', 'template_offsets_not_placements'),
            ('gamedata_npc_appear_template', 'appearance_definitions_not_placements'),
            ('gamedata_npc_list_row', 'visual_groups_not_placements'),
            ('npc_interaction_sample', 'interaction_samples_not_spawn_coordinates')):
            schema = db.execute('SELECT sql FROM sqlite_master WHERE type=\'table\' AND name=?', (table,)).fetchone()
            if schema is None:
                raise ValueError('Missing expected XJZ evidence table: ' + table)
            inventories.append({'table': table, 'classification': kind,
                                'rows': db.execute('SELECT COUNT(*) FROM "' + table + '"').fetchone()[0],
                                'schema': schema[0], 'schema_sha256': digest(schema[0].encode('utf-8'))})
    with database.open('rb') as stream:
        db_hash = hashlib.file_digest(stream, 'sha256').hexdigest()
    return {
        'schema': 'god2-npc-placement-recovery-v1',
        'scope': 'Classic migration 103 capture-backed definitions only; not a final migrated database snapshot',
        'status': 'definitions_extracted_current_integration_unresolved',
        'counts': {'placement_definitions': len(placements), 'current_map_bindings': 0,
                   'runtime_integrated': 0, 'current_template_rows': len(template_rows)},
        'placements': placements,
        'current_templates': {'provenance': provenance('current-client', CLIENT_NPC, client_raw),
                              'decoded_sha256': digest(decoded),
                              'classification': 'template_fields_not_world_spawns',
                              'rows': template_rows},
        'xjz_inventory': {'source_archive': 'xjz-20260820', 'file': 'xjz_evidence.sqlite',
                          'sha256': db_hash, 'tables': inventories},
        'unknown': ['current-client map crosswalk', 'physical coordinate scale',
                    'current-client NPC appearance binding', 'spawn conditions and complete map coverage'],
        'excluded': ['Classic migration 116 quest/guide coordinate matches are not observed placements',
                     'NPC.csvZ template offsets, quest mentions and minimap labels are not world spawns',
                     'current-scenes.json scene slots do not establish placements'],
        'next_hook': 'Resolve archived map_id using Classic maps client_map_id/client_area_id evidence against current world_atlas/world_scenes selectors, then pass qualified definitions to the main runtime loader.',
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for root in ('classic', 'xjz', 'client'):
        parser.add_argument('--' + root + '-root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    output = args.output.resolve()
    if any(output.is_relative_to(root.resolve()) for root in (
            args.classic_root, args.xjz_root, args.client_root)):
        parser.error('Output must be outside every source root')
    result = build_npcs(args.classic_root, args.xjz_root, args.client_root)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n', encoding='ascii', newline='\n')
    print(json.dumps(result['counts'], sort_keys=True))


if __name__ == '__main__':
    main()
