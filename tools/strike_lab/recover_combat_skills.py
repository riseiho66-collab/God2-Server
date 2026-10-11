"""Recover current-client SKB definitions; never execute description text as rules."""
import argparse
import hashlib
import json
from pathlib import Path
import re

from .omega_assets import decode_csvz

SOURCE = 'Data2/Patch/Comm/gamedata.csvZ'
MENU_SOURCE = 'Data/Patch/Skill.csvZ'
MAX_BYTES = 64 * 1024 * 1024
CLASSIC = Path('C:/God2Evidence/classic-20260820/files/God2-Classic-Server-Formal-Handoff-20260820-020345/ServerSource')
XJZ = Path('artifacts/legacy-evidence/xjz-20260820/files/XJZ-Server-Cpp/server_implementation')
# Anchored literal labels in description columns, not trailing numeric fields.
LABELS = {
    'mp_cost': r'\u4f7f\u7528\u6d88\u8017\s+([0-9]+)\s+MP',
    'attack_range': r'\u653b\u64ca\u8ddd\u96e2\s+([0-9]+)',
    'target_scope': r'\u7bc4\u570d\s+(.+)',
}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def source_bytes(path):
    with Path(path).open('rb') as stream:
        raw = stream.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError('Source exceeds recovery bound')
    return raw


def record(raw, line, offset):
    return {'source_line': line, 'decoded_offset': offset,
            'raw_record_hex': raw.hex(), 'source_record_sha256': digest(raw),
            'fields': [field.decode('cp950') for field in raw.split(b',')]}


def indexed_lines(raw):
    offset = 0
    for number, line in enumerate(raw.splitlines(keepends=True), 1):
        yield number, offset, line.rstrip(b'\r\n')
        offset += len(line)


def parse_skills(decoded):
    lines = list(indexed_lines(decoded))
    sections = [i for i, (_, _, row) in enumerate(lines) if row.startswith(b'SKB,')]
    if len(sections) != 1:
        raise ValueError('Expected exactly one SKB section')
    start = sections[0]
    section_fields = lines[start][2].split(b',')
    if len(section_fields) != 2 or not section_fields[1].isdigit():
        raise ValueError('Invalid SKB count')
    count = int(section_fields[1])
    if not 0 < count <= 65535 or start + count >= len(lines):
        raise ValueError('Invalid or truncated SKB section')
    headers = [entry for entry in lines if entry[2].startswith(b'ITEM_ID,')]
    if len(headers) != 1:
        raise ValueError('Expected one item header')
    header = record(headers[0][2], headers[0][0], headers[0][1])
    # Only these common item columns are assigned semantics in this slice.
    expected = {0: 'ITEM_ID', 4: '\u540d\u7a31',
                7: '\u63cf\u8ff0(\u8aaa\u660e1)',
                8: '\u9053\u5177\u6548\u679c(\u8aaa\u660e2)',
                9: '\u88dd\u5099\u7279\u6027(\u8aaa\u660e3)',
                10: '\u9053\u5177\u6548\u679c(\u8aaa\u660e4)',
                11: '\u9053\u5177\u6548\u679c(\u8aaa\u660e5)',
                12: '\u9053\u5177\u6548\u679c(\u8aaa\u660e6)'}
    if any(len(header['fields']) <= col or header['fields'][col] != label
           for col, label in expected.items()):
        raise ValueError('Item header differs from supported source labels')
    definitions, seen = [], set()
    for line, offset, raw in lines[start + 1:start + count + 1]:
        entry = record(raw, line, offset)
        fields = entry['fields']
        if len(fields) < 13 or not re.fullmatch(r'[0-9]+', fields[0]):
            raise ValueError('Invalid SKB record')
        item_id = int(fields[0])
        if item_id in seen:
            raise ValueError('Duplicate SKB item ID')
        seen.add(item_id)
        claims = {}
        for key, pattern in LABELS.items():
            matches = [(col, re.fullmatch(pattern, fields[col])) for col in range(7, 13)]
            matches = [(col, match) for col, match in matches if match]
            if len(matches) > 1:
                raise ValueError('Ambiguous description label: ' + key)
            if matches:
                col, match = matches[0]
                value = match[1] if key == 'target_scope' else int(match[1])
                claims[key] = {'value': value, 'source_column': col,
                               'source_text': fields[col], 'authority': 'description_only'}
        entry.update(item_id=item_id, name=fields[4], description_claims=claims)
        definitions.append(entry)
    # A too-small declared count must not silently discard more numeric rows.
    if start + count + 1 < len(lines):
        following = lines[start + count + 1][2].split(b',')[0]
        if following.isdigit():
            raise ValueError('SKB count ends before numeric records')
    return {'section_line': lines[start][0], 'declared_records': count,
            'header': header, 'normalized_field_columns': {'item_id': 0, 'name': 4},
            'definitions': definitions}


def evidence(root, relative, anchor, conclusion):
    raw = source_bytes(root / relative)
    lines = raw.decode('utf-8-sig').splitlines()
    hits = [i + 1 for i, line in enumerate(lines) if anchor in line]
    if not hits:
        raise ValueError('Missing legacy evidence anchor: ' + anchor)
    return {'path': relative, 'sha256': digest(raw), 'anchor': anchor,
            'anchor_lines': hits, 'conclusion': conclusion}


def build_catalog(client_root, classic_root=CLASSIC, xjz_root=XJZ):
    sources, decoded = {}, {}
    root = Path(client_root).resolve()
    for relative in (SOURCE, MENU_SOURCE):
        path = root / relative
        if not path.resolve().is_relative_to(root):
            raise ValueError('Source escapes client root')
        raw = source_bytes(path)
        decoded[relative] = decode_csvz(raw)
        sources[relative] = {'sha256': digest(raw), 'bytes': len(raw),
                             'decoded_sha256': digest(decoded[relative])}
    result = parse_skills(decoded[SOURCE])
    menu = decoded[MENU_SOURCE]
    if not menu.startswith(b'God Menu,'):
        raise ValueError('Unexpected menu table')
    menu_rows = [record(raw, line, offset) for line, offset, raw in indexed_lines(menu)
                 if raw.split(b',')[0].isdigit()]
    legacy = [
        evidence(Path(classic_root), 'src/God2.ClassicServer.Runtime/PhysicalSkillDamageRuntime.cs',
                 'No community-measured physical', 'Community coefficients are not current server authority.'),
        evidence(Path(classic_root), 'src/God2.ClassicServer.Runtime/MagicSkillDamageRuntime.cs',
                 'No community-measured magic', 'Legacy evaluator depends on community coefficients; not ported.'),
        evidence(Path(xjz_root), 'evidence-combat-formula-v0.md', 'packet_evidence_boundary',
                 'Document explicitly leaves final combat equations unresolved.'),
        evidence(Path(xjz_root), 'cpp/xjz_evidence_repository.hpp', 'GetSkillBookTemplate(',
                 'Concrete legacy metadata lookup hook; no current-client runtime ID mapping proved.'),
        evidence(Path(xjz_root), 'cpp/xjz_evidence_models.hpp', 'struct SkillBookTemplate',
                 'Legacy metadata contract; current source rows take precedence over legacy counts.'),
    ]
    return {'schema_version': 1, 'scope': 'current_client_definition_extraction_only',
            'encoding': 'cp950 strict; raw bytes retained', 'sources': sources,
            'column_index_base': 0, 'line_index_base': 1,
            'authority': 'No combat, casting, learning, targeting or EXP rule is enabled.',
            'skills': result, 'menu_raw_records': menu_rows, 'legacy_evidence': legacy,
            'counts': {'skill_books': len(result['definitions']), 'menu_rows': len(menu_rows),
                       **{key: sum(key in row['description_claims'] for row in result['definitions'])
                          for key in LABELS}},
            'unresolved': [
                'No current-client SKB consumer code identified in this bounded slice; header proves only named columns.',
                'Columns beyond the 25-column item header remain raw; no MP/range semantics assigned to trailing numbers.',
                'Book item ID to runtime skill/action ID, learned levels and cast validation are not recovered.',
                'Description MP/range/scope is not server validation or proven target geometry.',
                'Damage, hit, defense, critical, element, randomization and EXP equations are not recovered.'],
            'next_hook': 'lookup_definition(catalog, item_id) returns source-backed metadata. Main can adapt it to the legacy GetSkillBookTemplate(int32_t item_id) boundary; runtime skill-ID mapping and authoritative cast rules still require consumer evidence.'}


def lookup_definition(catalog, item_id):
    """Lookup by item ID only; this does not authorize a cast or compute damage."""
    if type(item_id) is not int:
        raise TypeError('item_id must be an integer')
    for entry in catalog['skills']['definitions']:
        if entry['item_id'] == item_id:
            return entry
    raise KeyError(item_id)


def serialize(catalog):
    return json.dumps(catalog, ensure_ascii=True, indent=2) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--client-root', required=True, type=Path)
    parser.add_argument('--classic-root', type=Path, default=CLASSIC)
    parser.add_argument('--xjz-root', type=Path, default=XJZ)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--item-id', type=int)
    args = parser.parse_args()
    catalog = build_catalog(args.client_root, args.classic_root, args.xjz_root)
    # Restrict generated writes to the lane-owned artifact, never source assets.
    target = Path(__file__).resolve().parents[2] / 'artifacts/world-atlas/combat-skills.json'
    if args.output.resolve() != target.resolve():
        parser.error('--output must be the lane-owned artifacts/world-atlas/combat-skills.json')
    selected = None
    if args.item_id is not None:
        try:
            selected = lookup_definition(catalog, args.item_id)
        except KeyError:
            parser.error('Unknown skill book item ID: ' + str(args.item_id))
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(serialize(catalog), encoding='utf-8', newline='\n')
    print(json.dumps(catalog['counts']))
    if selected is not None:
        print(json.dumps(selected, ensure_ascii=True))


if __name__ == '__main__':
    main()
