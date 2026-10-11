"""Extract current-client item definitions; never activate inventory or effects."""
import argparse
import json
from pathlib import Path
import re

from .omega_assets import decode_csvz
from .world_atlas import digest

SOURCE = 'Data2/Patch/Comm/gamedata.csvZ'
# Import resource limits, not assertions about original runtime capacities.
MAX_BYTES = 64 * 1024 * 1024
MAX_ROWS = 100000
MAX_LINE = 16384
MAX_FIELDS = 256
FLAG_NAMES = ('normal_use', 'battle_use', 'equippable', 'use_on_other',
              'hotkey_allowed', 'tradable', 'droppable', 'storable',
              'stackable', 'combine_up', 'combine_down')
LABELS = (
    'ITEM_ID', '\u985e\u5225\u4ee3\u78bc', '\u9053\u5177\u7de8\u865f',
    '\u5716\u78bc(\u540c\u5716\u6a94\u540d\u6a94)', '\u540d\u7a31',
    '\u7cfb\u7d71\u8ce3\u51fa\u50f9\u683c', '\u7cfb\u7d71\u56de\u6536\u50f9\u683c',
    '\u63cf\u8ff0(\u8aaa\u660e1)', '\u9053\u5177\u6548\u679c(\u8aaa\u660e2)',
    '\u88dd\u5099\u7279\u6027(\u8aaa\u660e3)', '\u9053\u5177\u6548\u679c(\u8aaa\u660e4)',
    '\u9053\u5177\u6548\u679c(\u8aaa\u660e5)', '\u9053\u5177\u6548\u679c(\u8aaa\u660e6)',
    '\u7279\u6548\u5716\u78bc', '\u4e00\u822c\u4f7f\u7528', '\u6230\u9b25\u4f7f\u7528',
    '\u53ef\u5426\u88dd\u5099', '\u5c0d\u5225\u4eba\u4f7f\u7528', '\u53ef\u5426\u8a2d\u5b9ahotkey',
    '\u53ef\u5426\u4ea4\u6613', '\u53ef\u5426\u4e1f\u6389', '\u662f\u5426\u653e\u5165\u5009\u5eab',
    '\u662f\u5426\u5806\u758a', '\u5408\u6210\u4e0a\u9762', '\u5408\u6210\u4e0b\u9762')


def number(raw, minimum=0, maximum=2147483647):
    if not re.fullmatch(rb'-?[0-9]{1,10}', raw):
        raise ValueError('Invalid decimal field')
    value = int(raw)
    if not minimum <= value <= maximum:
        raise ValueError('Numeric field exceeds import bounds')
    return value


def lines_of(decoded):
    if len(decoded) > MAX_BYTES or b'\0' in decoded:
        raise ValueError('Oversized table or embedded NUL')
    lines = [line.removesuffix(b'\r') for line in decoded.split(b'\n')]
    if any(len(line) > MAX_LINE for line in lines):
        raise ValueError('Line exceeds import bound')
    return lines


def section(lines, tag, optional=False):
    hits = [i for i, line in enumerate(lines) if line.split(b',', 1)[0] == tag]
    if not hits and optional:
        return []
    if len(hits) != 1:
        raise ValueError('Missing or duplicate section: ' + tag.decode('ascii'))
    start = hits[0]
    header = lines[start].split(b',')
    if len(header) < 2:
        raise ValueError('Missing section count')
    count = number(header[1], maximum=MAX_ROWS)
    end = start + count + 1
    if end > len(lines):
        raise ValueError('Truncated section')
    # A numeric continuation after the declared count means rows would be lost.
    if end < len(lines) and re.match(rb'^[0-9]+,', lines[end]):
        raise ValueError('Undeclared section rows')
    return [(i + 1, lines[i]) for i in range(start + 1, end)]


def provenance(line, raw):
    return {'source_line': line, 'source_record_sha256': digest(raw),
            'raw_fields_hex': [value.hex() for value in raw.split(b',')]}


def display(raw):
    try:
        return raw.decode('cp950')
    except UnicodeDecodeError:
        return None


def parse_items(decoded):
    lines = lines_of(decoded)
    desc = section(lines, b'RowDesc')
    if len(desc) != 1 or desc[0][1].split(b',') != [s.encode('cp950') for s in LABELS]:
        raise ValueError('Unrecognized RowDesc; column mapping cannot be applied')
    types, records, absent, seen_types = [], [], [], set()
    for line, raw in section(lines, b'ItemType'):
        fields = raw.split(b',')
        if not 4 <= len(fields) <= MAX_FIELDS or not re.fullmatch(rb'[A-Z][A-Z0-9]*', fields[2]):
            raise ValueError('Malformed ItemType row')
        low, high = number(fields[0], 1), number(fields[1], 1)
        tag = fields[2]
        if low > high or tag in seen_types:
            raise ValueError('Reversed range or duplicate type')
        seen_types.add(tag)
        name = tag.decode('ascii')
        types.append({**provenance(line, raw), 'section': name,
                      'declared_id_min': low, 'declared_id_max': high,
                      'client_label': display(fields[3])})
        rows = section(lines, tag, optional=tag == b'XXX')
        if not rows:
            absent.append(name)
        seen = set()
        for index, (row_line, row_raw) in enumerate(rows):
            f = row_raw.split(b',')
            short = tag in (b'GOD', b'MAP')
            if not (len(f) == (6 if tag == b'GOD' else 5) if short else 25 <= len(f) <= MAX_FIELDS):
                raise ValueError('Invalid item row width: ' + name)
            item_id = number(f[0], 1)
            if item_id in seen:
                raise ValueError('Duplicate item identity: ' + name)
            seen.add(item_id)
            flags = {}
            for column, flag in enumerate(FLAG_NAMES, 14):
                value = f[column] if not short else b''
                if value not in (b'', b'0', b'1'):
                    raise ValueError('Non-binary client flag')
                flags[flag] = None if value == b'' else value == b'1'
            records.append({
                **provenance(row_line, row_raw), 'source_record_index': index,
                'definition_key': name + ':' + str(item_id), 'client_item_id': item_id,
                'section': name, 'within_declared_type_range': low <= item_id <= high,
                'client_category_code': number(f[1], -2147483648),
                'client_resource_key': display(f[2]), 'client_icon_code': number(f[3]),
                'client_name': display(f[4]),
                'client_description': display(f[7]) if not short else None,
                'client_visual_effect_id': number(f[13]) if not short and f[13] else None,
                'client_flags': flags, 'server_template_id': None, 'stack_limit': None,
                'equipment_slot': None, 'equipment_restrictions': None,
                'server_effect_handler': None, 'runtime_eligible': False,
            })
    records.sort(key=lambda r: (r['section'], r['client_item_id']))
    return {'row_description': provenance(*desc[0]),
            'column_evidence': [{'column': i, 'client_label': s} for i, s in enumerate(LABELS)],
            'types': types, 'absent_sections': absent, 'records': records}


def read_source(root, relative):
    path = root / relative
    if not path.resolve().is_relative_to(root):
        raise ValueError('Source escapes client root')
    with path.open('rb') as stream:
        raw = stream.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError('Source exceeds import bound')
    decoded = decode_csvz(raw, limit=MAX_BYTES)
    return decoded, {'path': relative, 'sha256': digest(raw), 'size': len(raw),
                     'decoded_sha256': digest(decoded), 'decoded_size': len(decoded)}


def build_items(client_root):
    root = Path(client_root).resolve()
    decoded, source = read_source(root, SOURCE)
    result = parse_items(decoded)
    records = result['records']
    return {'schema_version': 1, 'source': source,
            'scope': 'Client static definitions only; no inventory, packets, persistence or Lua effects activated.',
            'text_encoding': 'CP950 display projection; undecodable text is null; raw bytes are authoritative.',
            'unknown_semantics': ['columns >=25', 'server prices/stats', 'stack limits',
                                  'equip slots/restrictions', 'server effect handlers'],
            'field_evidence': 'Zero-based columns from this source RowDesc; section identity from ItemType and exact section tag. GOD/MAP short tails remain raw.',
            'counts': {'definitions': len(records), 'types': len(result['types']),
                       'equippable_flags': sum(r['client_flags']['equippable'] is True for r in records),
                       'stackable_flags': sum(r['client_flags']['stackable'] is True for r in records),
                       'nonzero_visual_effect_ids': sum(bool(r['client_visual_effect_id']) for r in records),
                       'outside_declared_range': sum(not r['within_declared_type_range'] for r in records)},
            **result}


def serialize(result):
    return json.dumps(result, ensure_ascii=True, sort_keys=True, indent=2) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--client-root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root, output = args.client_root.resolve(), args.output.resolve()
    if output.is_relative_to(root):
        parser.error('Output must not modify the client tree')
    result = build_items(root)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(serialize(result), encoding='utf-8', newline='\n')
    print(json.dumps(result['counts'], sort_keys=True))


if __name__ == '__main__':
    main()
