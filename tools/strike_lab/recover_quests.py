"""Extract current-client quest definitions; never manufacture runtime rules."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

from .omega_assets import decode_csvz

PREFIX = 'Data2/Patch/Comm/'
SPECS = {
    'missions': ('Mission_data.csvZ', b'Mission_data', 2, 3),
    'requirements': ('ActMis.csvZ', b'ACTMIS', 3, 4),
    'daily': ('DayMissionDesc.csvZ', b'DailyMisDescNum', 4, 5),
}
# One-based columns, justified by the verbatim header retained in each table.
FIELDS = {
    'missions': {'id': 1, 'name': 2, 'step': 3, 'description': 4},
    'requirements': {'serial': 1, 'item_id_1': 3, 'quantity_1': 4,
                     'item_id_2': 5, 'quantity_2': 6, 'item_id_3': 7,
                     'quantity_3': 8, 'item_id_4': 9, 'quantity_4': 10},
    'daily': {'index': 1, 'branch': 2, 'name': 3, 'start_npc_id': 4,
              'weekday_raw': 5, 'start_time_raw': 6, 'end_time_raw': 7,
              'discriminator_raw': 8, 'rebirth_lower_raw': 9,
              'rebirth_upper_raw': 10, 'end_npc_id': 11,
              'restriction_text': 12, 'description_1': 13,
              'description_2': 14, 'description_3': 15, 'start_text': 16,
              'end_text': 17, 'reward_text': 18, 'accept_count_raw': 19},
}
HEADERS = {
    'missions': '\u7de8\u865f,\u4efb\u52d9\u540d\u7a31,STEP,\u4efb\u52d9\u8aaa\u660e',
    'requirements': '\u4efb\u52d9\u5e8f\u865f,,' + ','.join(
        ['\u9700\u6c42\u7269\u54c1ID', '\u9700\u6c42\u6578\u91cf'] * 4),
    'daily': '\u7d22\u5f15,\u4efb\u52d9\u5206\u652f,\u4efb\u52d9\u540d\u7a31,\u958b\u59cbNPC ID,\u661f\u671f(\u4e8c\u9032\u4f4d),\u958b\u59cb\u6642\u9593,\u7d50\u675f\u6642\u9593,\u5224\u5225\u65b9\u5f0f,\u8f49\u751f\u7b49\u7d1a\u4e0b\u9650,\u8f49\u751f\u7b49\u7d1a\u4e0a\u9650,\u7d50\u675fNPCID,\u4efb\u52d9\u9650\u9650,\u4efb\u52d9\u7c21\u4ecb1,\u4efb\u52d9\u7c21\u4ecb2,\u4efb\u52d9\u7c21\u4ecb3,\u8d77\u9ede,\u7d42\u9ede,\u4efb\u52d9\u734e\u52f5,\u53ef\u63a5\u6b21\u6578',
}
# The spelling is taken literally from the current table.
HEADERS['daily'] = HEADERS['daily'].replace('\u9650\u9650', '\u9650\u5236')


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def display(raw):
    return raw.decode('cp950', errors='backslashreplace')


def integer(raw):
    if not raw or not raw.isdigit():
        raise ValueError('Expected unsigned decimal field, got ' + repr(raw))
    return int(raw)


def parse_table(kind, decoded):
    """Validate the observed layout; preserve every original row and field."""
    name, tag, header_line, section_line = SPECS[kind]
    physical = decoded.split(b'\n')
    lines = list(physical)
    if lines[-1] == b'':
        lines.pop()
    lines = [line.removesuffix(b'\r') for line in lines]
    if len(lines) < section_line:
        raise ValueError('Truncated table: ' + name)
    if lines[header_line - 1] != HEADERS[kind].encode('cp950'):
        raise ValueError('Unrecognized column header: ' + name)
    section = lines[section_line - 1].split(b',')
    if len(section) != 2 or section[0] != tag:
        raise ValueError('Unrecognized section: ' + name)
    declared = integer(section[1])
    if declared > 32767:
        raise ValueError('Section exceeds extraction bound')
    records = []
    for line_number, raw in enumerate(lines[section_line:], section_line + 1):
        fields = raw.split(b',')
        if b'\0' in raw:
            raise ValueError('Embedded NUL in ' + name)
        allowed = {'missions': (3, 4), 'requirements': (10,), 'daily': (12, 19)}[kind]
        if len(fields) not in allowed:
            raise ValueError(f'Unexpected row width: {name}:{line_number}')
        records.append({'source_line': line_number, 'source_record_sha256': digest(raw),
                        'line_ending_hex': ((b'\r' if physical[line_number - 1].endswith(b'\r') else b'')
                            + (b'\n' if line_number < len(physical) else b'')).hex(),
                        'raw_fields_hex': [f.hex() for f in fields],
                        'fields': {key: display(fields[col - 1]) if col <= len(fields) else None
                                   for key, col in FIELDS[kind].items()}})
    return {'source_file': PREFIX + name, 'declared_records': declared,
            'preamble_hex': (b'\n'.join(physical[:section_line])
                             + (b'\n' if len(physical) > section_line else b'')).hex(),
            'header_line': header_line, 'header_fields': HEADERS[kind].split(','),
            'field_columns': FIELDS[kind], 'records': records}


def recover(tables):
    quests, requirements, daily, references, issues = [], [], [], [], []
    current = None
    for row in tables['missions']['records']:
        raw = [bytes.fromhex(v) for v in row['raw_fields_hex']]
        if raw[0]:
            if len(raw) != 3:
                raise ValueError('Mission definition must have three fields')
            current = {'id': integer(raw[0]), 'name': row['fields']['name'],
                       'source_line': row['source_line'], 'step_field': integer(raw[2]),
                       'objectives_text': [], 'prerequisites': 'UNKNOWN',
                       'rewards': 'UNKNOWN', 'conditions': 'UNKNOWN',
                       'transitions': 'UNKNOWN', 'npc_references': 'UNKNOWN',
                       'monster_references': 'UNKNOWN'}
            quests.append(current)
        else:
            if current is None or len(raw) != 4 or raw[1]:
                raise ValueError('Orphan or malformed mission description')
            current['objectives_text'].append({'step': integer(raw[2]),
                'text': row['fields']['description'], 'source_line': row['source_line'],
                'qualification': 'PRESENTATION_TEXT_ONLY'})
    for row in tables['requirements']['records']:
        fields = row['fields']
        serial = integer(fields['serial'].encode('ascii'))
        requirements.append({'serial': serial, 'source_line': row['source_line'],
                             'mission_data_relationship': 'UNKNOWN'})
        for slot in range(1, 5):
            item = integer(fields[f'item_id_{slot}'].encode('ascii'))
            quantity = integer(fields[f'quantity_{slot}'].encode('ascii'))
            references.append({'table': 'requirements', 'source_line': row['source_line'],
                'source_column': 1 + 2 * slot, 'kind': 'item', 'target_id': item,
                'quantity': quantity, 'quantity_column': 2 + 2 * slot,
                'resolution': 'UNKNOWN', 'zero_sentinel_semantics': 'UNKNOWN' if item == 0 else None})
    for row in tables['daily']['records']:
        fields = row['fields']
        daily.append({'index': integer(fields['index'].encode('ascii')),
                      'branch': integer(fields['branch'].encode('ascii')),
                      'source_line': row['source_line'],
                      'mission_data_relationship': 'UNKNOWN', 'transitions': 'UNKNOWN',
                      'reward_rules': 'UNKNOWN', 'condition_rules': 'UNKNOWN'})
        for key in ('start_npc_id', 'end_npc_id'):
            references.append({'table': 'daily', 'source_line': row['source_line'],
                'source_column': FIELDS['daily'][key], 'kind': 'npc', 'role': key,
                'target_id': integer(fields[key].encode('ascii')), 'resolution': 'UNKNOWN'})
    for kind, rows, keys in [('missions', quests, ('id',)),
                              ('requirements', requirements, ('serial',)),
                              ('daily', daily, ('index', 'branch'))]:
        if len(rows) != tables[kind]['declared_records']:
            issues.append({'code': 'record_count_mismatch', 'table': kind,
                           'declared': tables[kind]['declared_records'], 'actual': len(rows)})
        counts = Counter(tuple(row[k] for k in keys) for row in rows)
        for key, count in sorted(counts.items()):
            if count > 1:
                issues.append({'code': 'duplicate_key', 'table': kind, 'key': list(key), 'count': count})
    for quest in quests:
        steps = Counter(obj['step'] for obj in quest['objectives_text'])
        for step, count in sorted(steps.items()):
            if count > 1:
                issues.append({'code': 'duplicate_text_step', 'quest_id': quest['id'], 'step': step})
        # Compare the header STEP field to observed rows without promoting it
        # into a server completion rule or interpreting text as prerequisites.
        if quest['step_field'] != len(quest['objectives_text']):
            issues.append({'code': 'step_field_row_count_difference', 'quest_id': quest['id'],
                           'step_field': quest['step_field'], 'rows': len(quest['objectives_text'])})
    return {'quests': quests, 'requirement_records': requirements, 'daily_records': daily,
            'references': references, 'validation': {
                'structural_issues': issues,
                'missing_target_references': 'UNKNOWN: target catalog namespaces not established',
                'prerequisite_cycles': 'UNKNOWN: no source-backed prerequisite edges',
                'runtime_validity': 'UNKNOWN'},
            'counts': {'mission_definitions': len(quests),
                       'objective_text_rows': sum(len(q['objectives_text']) for q in quests),
                       'requirement_records': len(requirements), 'daily_records': len(daily),
                       'item_reference_slots': sum(r['kind'] == 'item' for r in references),
                       'nonzero_item_reference_slots': sum(r['kind'] == 'item' and r['target_id'] != 0 for r in references),
                       'npc_reference_slots': sum(r['kind'] == 'npc' for r in references),
                       'structural_issues': len(issues), 'executable_transition_rules': 0,
                       'server_integrated': 0}}


def build_catalog(client):
    root = Path(client).resolve()
    tables = {}
    for kind, (name, _, _, _) in SPECS.items():
        path = (root / PREFIX / name).resolve()
        if not path.is_relative_to(root):
            raise ValueError('Source escapes client root')
        with path.open('rb') as stream:
            raw = stream.read(64 * 1024 * 1024 + 1)
        if len(raw) > 64 * 1024 * 1024:
            raise ValueError('Source exceeds extraction bound')
        decoded = decode_csvz(raw)
        table = parse_table(kind, decoded)
        table['source_sha256'] = digest(raw)
        table['decoded_sha256'] = digest(decoded)
        tables[kind] = table
    return {'schema': 'god2-current-quest-definitions-v1',
            'qualification': 'CURRENT_CLIENT_DEFINITIONS_ONLY',
            'text_encoding': 'cp950 display; original field bytes are authoritative',
            'relationship_policy': 'Separate table namespaces; equal IDs are not proven joins. '
                'NPC/item columns are header-backed references with unverified target namespaces. '
                'Text, rewards and condition fields do not define executable rules.',
            'tables': tables, **recover(tables)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--client', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    output = args.output.resolve()
    if output.is_relative_to(args.client.resolve()):
        parser.error('Output must be outside the read-only client tree')
    result = build_catalog(args.client)
    issues = result['validation']['structural_issues']
    if issues:
        parser.exit(1, 'Structural validation failed: ' + str(len(issues))
                    + ' issue(s); first: ' + json.dumps(issues[0], sort_keys=True) + '\n')
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=True, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result['counts'], sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
