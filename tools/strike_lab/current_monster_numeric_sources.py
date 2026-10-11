"""Bounded current Data2 numeric-source discovery; JSON stdout, no promotion.

Only the fixed current Data2 tree and pinned mapped image are opened. CSVZ/MDTZ
use the existing decoder. Other binary bodies remain semantically unexamined.
No identity sweep, original loader execution, legacy helper, or runtime runs.
"""
import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import re
import struct

from .omega_assets import decode_csvz
from .current_skill_identity import decode_definitions, SOURCE_SHA256 as SKILL_SHA

ROOT = Path(__file__).resolve().parents[2]
CLIENT = ROOT.parent / 'God2'
DATA = CLIENT / 'Data2'
IMAGE = ROOT / 'artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin'
IMAGE_SHA = '149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
GAME_SHA = '70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731'
GAME_PLAIN_SHA = '75c3c37947a64b0917fbf8e546884d9bf893fe6a606d3e2b8f3b1857966b1815'
MAX_FILES, MAX_FILE, MAX_TOTAL, MAX_PLAIN = 12000, 8 << 20, 128 << 20, 32 << 20
MEDIA = {'.romz', '.wav'}
TEXT = {'.csvz', '.csv', '.mdtz', '.lua', '.txt', '.ini', '.json', '.xml', '.tsv'}
REQUESTED = ('level', 'hp', 'mp', 'constitution', 'strength', 'intelligence', 'speed',
             'physical_attack', 'physical_defense', 'magical_attack', 'magical_defense',
             'metal', 'wood', 'water', 'fire', 'earth', 'base_experience', 'capturable',
             'skill_assignments', 'drop_items', 'drop_rates')
LABELS = {
    'level': ('level', 'lv', '\u7b49\u7d1a', '\u602a\u7269\u7b49\u7d1a'),
    'hp': ('hp', 'maxhp', '\u751f\u547d\u503c'), 'mp': ('mp', 'maxmp', '\u6cd5\u529b\u503c'),
    'constitution': ('constitution', '\u9ad4\u529b'),
    'strength': ('strength', '\u529b\u91cf', '\u8155\u529b'),
    'intelligence': ('intelligence', '\u667a\u529b'), 'speed': ('speed', '\u901f\u5ea6'),
    'physical_attack': ('physical_attack', '\u7269\u653b'),
    'physical_defense': ('physical_defense', '\u7269\u9632'),
    'magical_attack': ('magical_attack', '\u9b54\u653b'),
    'magical_defense': ('magical_defense', '\u9b54\u9632'),
    'elements': ('\u91d1', '\u6728', '\u6c34', '\u706b', '\u571f', '\u4e94\u884c'),
    'experience': ('exp', 'experience', '\u7d93\u9a57', '\u7d93\u9a57\u503c'),
    'capture': ('capturable', 'capture', '\u6355\u6349', '\u53ef\u6355\u6349'),
    'skills': ('skill', 'skill_id', '\u6280\u80fd', '\u5929\u8ce6'),
    'items': ('item_id', '\u9700\u6c42\u7269\u54c1id'),
    'quantity': ('\u6578\u91cf', '\u9700\u6c42\u6578\u91cf'),
    'probability': ('drop_rate', 'probability', '\u6a5f\u7387', '\u6389\u843d\u7387'),
    'effect_value': ('\u57fa\u672c\u503c', '\u6cd5\u5bf6\u6578\u503c'),
}
EXCLUDED_SECTIONS = {'EnyName', 'EnyNameTotal', 'NPCAppearData', 'SpecialEnyInfo'}
PRIOR = {
    'ChangeDollCard.csvZ': ('already_covered_card_not_wild_stats', 'current-monster-combat-stats-20260920.md'),
    'ChangeDollEffect.csvZ': ('card_effect_definitions_not_monster_assignments', 'current-combat-effect-values-20260920.md'),
    'NewCombatPet_Category.csvZ': ('companion_category_not_wild_stats', 'companion-growth-evidence-20260919.md'),
    'NewCombatPet_QualityStar.csvZ': ('companion_quality_values_not_wild_stats', 'companion-growth-evidence-20260919.md'),
    'NewCombatPet_AllInnate.csvZ': ('innate_definitions_not_monster_assignments', 'companion-growth-evidence-20260919.md'),
    'NewCombatPet_Innate.csvZ': ('innate_pools_without_wild_identity_binding', 'companion-growth-evidence-20260919.md'),
    'eny.csvZ': ('already_covered_visual_records', 'monster-stats-skills-audit-20260919.md'),
    'FightEny.csvZ': ('already_covered_visual_records', 'monster-stats-skills-audit-20260919.md'),
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def is_reparse(path):
    stat = path.lstat()
    return path.is_symlink() or bool(getattr(stat, 'st_file_attributes', 0) & 0x400)


def current_files():
    root = DATA.resolve()
    if is_reparse(DATA) or any(is_reparse(parent) for parent in DATA.parents):
        raise ValueError('Current source root traverses a reparse point')
    files, skipped = [], []
    for directory, dirs, names in os.walk(root, followlinks=False):
        folder = Path(directory)
        if len(folder.relative_to(root).parts) > 12:
            raise ValueError('Current file depth bound')
        for name in list(dirs):
            path = folder / name
            if is_reparse(path):
                dirs.remove(name)
                skipped.append({'path': path.relative_to(root).as_posix(), 'reason': 'reparse_directory'})
        for name in names:
            path = folder / name
            if is_reparse(path) or not path.resolve().is_relative_to(root):
                skipped.append({'path': path.relative_to(root).as_posix(), 'reason': 'reparse_file'})
                continue
            if path.is_file():
                files.append(path)
                if len(files) > MAX_FILES:
                    raise ValueError('Current file count bound')
    return sorted(files, key=lambda p: p.relative_to(root).as_posix().lower()), skipped


def bounded_read(path):
    root = DATA.resolve()
    path = Path(path)
    resolved = path.resolve()
    if not resolved.is_relative_to(root) or is_reparse(path):
        raise ValueError('Only current Data2 files may be read')
    for parent in path.parents:
        if parent == root:
            break
        if is_reparse(parent):
            raise ValueError('Reparse source ancestor')
    if path.stat().st_size > MAX_FILE:
        raise ValueError('Per-file byte bound')
    with path.open('rb') as stream:
        raw = stream.read(MAX_FILE + 1)
    if len(raw) > MAX_FILE:
        raise ValueError('Per-file byte bound')
    return raw


def line_evidence(raw, line, offset):
    fields = raw.rstrip(b'\r\n').split(b',')
    return {'line': line, 'decoded_offset': offset, 'length': len(raw), 'sha256': sha(raw),
            'raw_hex': raw.hex(), 'fields_hex': [value.hex() for value in fields]}


def table_outline(plain, *, game=False):
    """Lexical headers/section declarations, never a guessed gameplay schema."""
    schemas, sections, offset = [], [], 0
    for number, raw in enumerate(plain.split(b'\n'), 1):
        raw += b'\n' if offset + len(raw) < len(plain) else b''
        start, offset = offset, offset + len(raw)
        # Prior identity namespaces are excluded from content qualification.
        if game and (7887 <= start < 140789 or 2500836 <= start < 2781824):
            continue
        fields = raw.rstrip(b'\r\n').split(b',')
        if len(fields) >= 2 and re.fullmatch(rb'[A-Za-z][A-Za-z0-9_]{1,40}', fields[0]) and fields[1].isdigit():
            tag = fields[0].decode('ascii')
            if tag not in EXCLUDED_SECTIONS:
                sections.append({'tag': tag, 'declared_number': int(fields[1]),
                                 'count_semantics': 'unqualified_lexical_declaration',
                                 **line_evidence(raw, number, start)})
        if number > 80 or fields[0].strip().isdigit():
            continue
        matches = []
        for index, field in enumerate(fields):
            # Byte offsets/hex are authority; this decoding is a search aid only.
            label = field.decode('cp950', errors='replace').strip().lower()
            for meaning, terms in LABELS.items():
                if label in terms or meaning == 'level' and re.fullmatch(r'lv\d+', label):
                    matches.append({'column': index, 'label_hex': field.hex(), 'search_category': meaning})
        if matches:
            schemas.append({**line_evidence(raw, number, start), 'matches': matches,
                            'interpretation': 'literal_labels_only; no_numeric_field_assignment'})
    return {'schemas': schemas, 'section_declarations': sections,
            'search_scope': 'first80_lines_exact_column_labels_and_all_lexical_section_declarations',
            'excluded_decoded_spans': [[7887, 140789], [2500836, 2781824]] if game else []}


def native_reference(image, literal_rva, literal, operand_rva, call_rva, target):
    if (image[literal_rva:literal_rva + len(literal) + 1] != literal + b'\0'
            or struct.unpack_from('<I', image, operand_rva)[0] != 0x400000 + literal_rva
            or image[call_rva] != 0xe8
            or call_rva + 5 + struct.unpack_from('<i', image, call_rva + 1)[0] != target):
        raise ValueError('Pinned native reference mismatch')
    return {'authority': 'static_literal_operand_and_call_binding; not_executed_here',
            'literal_rva': literal_rva, 'literal_hex': literal.hex(), 'operand_rva': operand_rva,
            'call_rva': call_rva, 'target_rva': target,
            'call_hex': image[call_rva:call_rva + 5].hex(), 'image_sha256': IMAGE_SHA}


def build_report():
    image = IMAGE.read_bytes()
    if sha(image) != IMAGE_SHA:
        raise ValueError('Current image hash changed')
    paths, skipped = current_files()
    inventory, tables, candidates, plain_by_path = [], [], [], {}
    total_read = total_plain = 0
    for path in paths:
        relative = path.relative_to(DATA.resolve()).as_posix()
        extension, size = path.suffix.lower(), path.stat().st_size
        entry = {'path': 'Data2/' + relative, 'extension': extension, 'size': size,
                 'sha256': None, 'content_status': 'media_not_read', 'runtime_eligible': False}
        inventory.append(entry)
        if extension in MEDIA:
            continue
        if total_read + size > MAX_TOTAL:
            raise ValueError('Aggregate read byte bound')
        try:
            raw = bounded_read(path)
        except ValueError as error:
            entry['content_status'] = 'not_read_bound_or_path_rejected'
            entry['reason'] = str(error)
            continue
        total_read += len(raw)
        entry.update(sha256=sha(raw), prefix_hex=raw[:32].hex(), content_status='hashed_binary_semantics_unexamined')
        if relative == 'Patch/Comm/gamedata.csvZ' and sha(raw) != GAME_SHA:
            raise ValueError('Current gamedata hash changed')
        if relative == 'Fight/Spg/cbspec2.bin':
            if sha(raw) != SKILL_SHA:
                raise ValueError('Current skill source hash changed')
            definitions = decode_definitions(raw)
            candidates.append({'path': entry['path'], 'sha256': entry['sha256'],
                'status': 'qualified_skill_definition_envelope_only',
                'why_unqualified': 'No wild-monster ownership or original numeric field semantics supplied by this envelope.',
                'schema': {'version': '1.03', 'group_stride': 0x6e04, 'record_size': 110,
                           'definition_count': len(definitions), 'numeric_payload_semantics': None},
                'source_records': [{'bank': d.kind, 'id': d.id, 'source_offset': d.source_offset,
                                    'length': len(d.raw), 'sha256': sha(d.raw)} for d in definitions.values()],
                'native_reference': native_reference(image, 0x19c5e4, b'data2\\fight\\spg\\cbspec2.bin',
                                                     0x110c22, 0x110c45, 0x12d3b0),
                'prior_audit': 'current-skill-catalog-loader-20260920.md',
                'wild_monster_values': None, 'runtime_eligible': False})
            entry['content_status'] = 'known_skill_envelope; numeric_payload_not_reinterpreted'
        if extension not in TEXT:
            continue
        try:
            plain = decode_csvz(raw, limit=MAX_FILE) if raw[:2] == b'\x05\x16' else raw
        except ValueError as error:
            entry.update(content_status='decode_failed', decode_error=str(error))
            continue
        total_plain += len(plain)
        if total_plain > MAX_PLAIN:
            raise ValueError('Aggregate decoded byte bound')
        if relative == 'Patch/Comm/gamedata.csvZ' and sha(plain) != GAME_PLAIN_SHA:
            raise ValueError('Current decoded gamedata changed')
        entry.update(decoded_sha256=sha(plain), decoded_size=len(plain), content_status='decoded_text_outline')
        if path.name in ('ChangeDollCard.csvZ', 'eny.csvZ', 'FightEny.csvZ'):
            entry['content_status'] = 'prior_card_or_visual_analysis_not_repeated'
            entry['prior_audit'] = PRIOR[path.name][1]
            continue
        outline = table_outline(plain, game=relative == 'Patch/Comm/gamedata.csvZ')
        tables.append({'path': entry['path'], 'sha256': entry['sha256'],
                       'decoded_sha256': entry['decoded_sha256'], **outline})
        if extension == '.csvz':
            plain_by_path[relative] = plain
        if outline['schemas']:
            prior = PRIOR.get(path.name)
            candidates.append({'path': entry['path'], 'sha256': entry['sha256'],
                'decoded_sha256': entry['decoded_sha256'], 'schema': outline['schemas'],
                'section_declarations': outline['section_declarations'],
                'status': prior[0] if prior else 'literal_column_labels_candidate_only',
                'prior_audit': prior[1] if prior else None,
                'why_unqualified': 'Labels and numeric tokens do not establish a wild-monster identity, '
                    'numeric consumer, or original probability unit/denominator. No values promoted.',
                'wild_monster_values': None, 'runtime_eligible': False})
    game = next(t for t in tables if t['path'] == 'Data2/Patch/Comm/gamedata.csvZ')
    for tag, literal, operand, call, target in (
            ('FightPetSkill', 0x18a038, 0x567d3, 0x56813, 0x58920),
            ('NewFightPet2Skill', 0x18a024, 0x5681e, 0x5685e, 0x58ac0)):
        section = next(s for s in game['section_declarations'] if s['tag'] == tag)
        candidates.append({'path': game['path'], 'sha256': game['sha256'],
            'decoded_sha256': game['decoded_sha256'], 'schema': section,
            'status': 'skill_mapping_section_not_monster_assignment',
            'native_reference': native_reference(image, literal, tag.encode(), operand, call, target),
            'prior_audit': 'companion-growth-evidence-20260919.md',
            'why_unqualified': 'Source declarations and static loader calls are real; '
                'no wild-monster owner or numeric effect/cost/drop-rate producer is qualified.',
            'wild_monster_values': None, 'runtime_eligible': False})
    category = plain_by_path['Patch/Comm/NewCombatPet_Category.csvZ']
    token = b'Base100_Index37'
    token_offsets = [m.start() for m in re.finditer(token, category)]
    # Preserve the concrete unresolved token; do not invent its advertised base.
    unresolved_token = {'path': 'Data2/Patch/Comm/NewCombatPet_Category.csvZ',
        'sha256': next(row['sha256'] for row in inventory
                       if row['path'] == 'Data2/Patch/Comm/NewCombatPet_Category.csvZ'),
        'decoded_sha256': sha(category), 'token_hex': token.hex(), 'decoded_offsets': token_offsets,
        'mapped_image_occurrences': [m.start() for m in re.finditer(token, image)],
        'native_reference': native_reference(image, 0x189fa0, b'CategoryDetailNum',
                                             0x56ac1, 0x56b01, 0x5c640),
        'authority': 'literal_token_only; neither_Base100_nor_Index37_is_a_recovered_stat'}
    extensions = Counter(row['extension'] for row in inventory)
    disqualified_scalar = {'kind': 'already_qualified_dynamic_incoming_scalar_consumer',
        'image_sha256': IMAGE_SHA, 'start_rva': 0x1173a0, 'end_rva_exclusive': 0x117472,
        'span_sha256': sha(image[0x1173a0:0x117472]), 'call_rva': 0x11740a, 'callee_rva': 0x12d970,
        'logical_opcode': 0x86, 'subtype': 1, 'side': 0,
        'packet_to_actor': [{'packet_offset': 9, 'actor_offset': 0xdec, 'size': 4},
                            {'packet_offset': 5, 'actor_offset': 0xdf4, 'size': 4}],
        'prior_proof': ['tools/strike_lab/current_battle_scalar_result.py',
                        'tests/research/test_current_battle_scalar_result.py'],
        'source_recovery_eligible': False,
        'why_disqualified': 'Already qualified logical86 subtype1 side0-only incoming scalar copy, '
            'not a numeric producer or original monster source. Do not repeat as a recovery target.',
        'runtime_eligible': False}
    if image[0x11740a] != 0xe8 or 0x11740f + struct.unpack_from('<i', image, 0x11740b)[0] != 0x12d970:
        raise ValueError('Prior scalar consumer call binding changed')
    numeric_target = {'kind': 'conditional_companion_category_full_loader_and_consumer_check',
        'path': unresolved_token['path'], 'sha256': unresolved_token['sha256'],
        'decoded_sha256': unresolved_token['decoded_sha256'],
        'call_rva': 0x56b01, 'callee_rva': 0x5c640,
        'native_reference': unresolved_token['native_reference'],
        'current_qualified_scope': 'companion_pet_category_only', 'wild_monster_binding': None,
        'prior_proof': 'docs/research/companion-growth-evidence-20260919.md',
        'prior_qualified_row_span': [0x5c6a6, 0x5c9b5],
        'prior_read_columns': list(range(9)), 'prior_unread_columns': [9, 10, 11],
        'wholly_unexamined': False, 'full_loader_executed_in_prior_proof': False,
        'required_next_proof': 'Only if still unexamined by main, inspect the full 5C640 loader and '
            'downstream consumers for actual reads of columns9..11 and Base100_Index37. '
            'The qualified row interval does not read them; do not rerun that proof. '
            'Keep this pet-category-only unless an original wild-monster numeric binding is proven.',
        'runtime_eligible': False}
    return {'schema': 'current-monster-numeric-sources-v1',
        'scope': {'root': str(DATA.resolve()), 'max_files': MAX_FILES, 'per_file_byte_limit': MAX_FILE,
                  'read_byte_limit': MAX_TOTAL, 'decoded_byte_limit': MAX_PLAIN,
                  'only_current_files_and_pinned_image': True, 'native_execution_performed': False,
                  'binary_absence_claim': False, 'retired_sources_used': False},
        'summary': {'files_enumerated': len(inventory), 'extension_counts': dict(sorted(extensions.items())),
                    'files_hashed': sum(row['sha256'] is not None for row in inventory),
                    'source_bytes_read': total_read, 'decoded_bytes': total_plain,
                    'text_outlines': len(tables), 'candidate_count': len(candidates),
                    'qualified_wild_monster_numeric_sources': 0,
                    'unexamined_binary_files': sum(row['content_status'] == 'hashed_binary_semantics_unexamined'
                                                  for row in inventory)},
        'inventory': inventory, 'inventory_sha256': sha(json.dumps(inventory, sort_keys=True).encode()),
        'skipped_links': skipped, 'text_outlines': tables, 'candidates': candidates,
        'unresolved_literal': unresolved_token, 'numeric_next_target': numeric_target,
        'disqualified_source_recovery_targets': [disqualified_scalar],
        'field_authority': {field: {'qualified_values': None, 'verified_monster_records': 0}
                            for field in REQUESTED},
        'all_monster_numeric_data_complete': False, 'runtime_eligible': False,
        'limitations': ['Exact-label search is not semantic exhaustion of text or executable code.',
                       'Hashed binary bodies were not interpreted or decompressed; media bodies were not read.',
                       'Current-only source discovery does not supply original server-generated values.']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--summary', action='store_true')
    args = parser.parse_args()
    report = build_report()
    if args.summary:
        report = {key: report[key] for key in ('scope', 'summary', 'inventory_sha256',
                  'numeric_next_target', 'disqualified_source_recovery_targets',
                  'all_monster_numeric_data_complete', 'limitations')}
    print(json.dumps(report, ensure_ascii=True, separators=(',', ':')))


if __name__ == '__main__':
    main()
