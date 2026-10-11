"""Bounded current Data/Data3 source audit; static evidence and JSON stdout only.

No Data2 reads, native execution, archive search, or wild-stat promotion. Table
cells remain exact source tokens, even when a static integer reader is known.
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

ROOT = Path(__file__).resolve().parents[2]
CLIENT = ROOT.parent / 'God2'
TREES = (CLIENT / 'Data', CLIENT / 'Data3')
IMAGE = ROOT / 'artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin'
IMAGE_SHA = '149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
MAX_FILES, MAX_ENTRIES, MAX_DEPTH = 2048, 4096, 12
MAX_FILE, MAX_TOTAL, MAX_PLAIN, MAX_IMAGE = 8 << 20, 32 << 20, 8 << 20, 4 << 20
MAX_LINES, MAX_LINE = 4096, 4096
MEDIA = {'.romz', '.wav'}
TABLE_EXTENSIONS = {'.csvz', '.csv', '.mdtz', '.lua', '.txt', '.json', '.xml', '.tsv'}
EXCLUDED_EXTENSIONS = {'.ini', '.iniz', '.cfg', '.log', '.logz'}
EXCLUDED_NAMES = re.compile(
    r'^(?:config|save|logs?|user|account|cache|screenshots?|classic|xjz)(?:[0-9._-]|$)', re.I)
FIELDS = ('level', 'hp', 'mp', 'constitution', 'strength', 'intelligence', 'speed',
          'physical_attack', 'physical_defense', 'magical_attack', 'magical_defense',
          'metal', 'wood', 'water', 'fire', 'earth', 'base_experience', 'capturable',
          'skill_assignments', 'drop_items', 'drop_rates')

# Exact current files, not inferred from historical dates embedded in headers.
# path: raw SHA, decoded SHA, schema line, scope of the observed table
SOURCES = {
    'Data/Patch/Cat.csvZ': (
        '9a1fad6c037cb276910b5d1a99a7c7755d8e723fa8dd4d5bc65c4d2c366d5bed',
        'b518ebba78180078a6ac784c7c107d6563d72042eacb51ad0153305040dbe4c0', 4,
        'previously_covered_character_menu'),
    'Data/Patch/God.csvZ': (
        'fa6673ce89374d135d3109bb1381a1fb0755b18f898af3988f34e1995ad8af44',
        '679ccd778fd63a578d8d41d92cd1a46ead578d92ab6791ce51a16e0eac84b52d', 4,
        'god_selection_menu_not_wild_stats'),
    'Data/Patch/Skill.csvZ': (
        '1dc049cb4ac19fd753c17af64932c40f4e833a1dac92a8d0d33a44529a9a7e16',
        '65421ec3d8167c327c9e9ca0cbccb0cee7688c85388b99e4431c0f7c972a8701', 4,
        'crafting_menu_not_monster_skill_assignments'),
    'Data/Patch/GodDoll.csvZ': (
        '768c3a68cddd1443c5c19207a21b17d00990e596aedd74d27f13d0bde5ef02df',
        '22bedaac6743d190456d5549688019b65415178b7cb8f269156743e7babd0bc1', 36,
        'visual_resource_table_not_combat_stats'),
    'Data/Patch/FightGodDoll01.csvZ': (
        'f463dea42b2f310e264f3e5eba4c35ec7ab84d3f709205a6348e1f176e6e4ee9',
        '86516149963f5f4983f41e2fa4beba2c2218c481ab85fa2ba527d8cc9f32aab7', 36,
        'visual_resource_table_not_combat_stats'),
    'Data/Patch/FightGodDoll05.csvZ': (
        '3d4a9eb66503a28cdae9c1f306d2517b49a12013936a045b0008fd755a623b22',
        '4424ee62a6c72e8f01ffd59eb298371399993e33dad02fec5ce94e76f0797252', 36,
        'visual_resource_table_not_combat_stats'),
    'Data/Patch/IGS.csvZ': (
        '1eb61427d8f0b5d15e3b7d2f6043fe4cccdffbdb455ca05efdaa8c4b1a45a254',
        'a655f8353fddcca9c81aae9eae82b7cf50b3ccee34bf4e3ad7a897881e7128f5', 6,
        'static_program_name_action_list_not_monster_actions'),
    'Data3/patch/SpgEft.csvZ': (
        '28deaec92235298a41485ec324d15b2ea0b6b12fd19db4bbd22870b413f23dad',
        '5fda6887402a9e034caca1ea48c015ebb25e162c41b23f61fcee1374d931b5cf', 38,
        'effect_resources_not_damage_formula_or_monster_ownership'),
    'Data3/patch/comm/Message2.csvZ': (
        'f49d94ba734609d96e948a99367ae7d449269f001766598989f0e120644c4bc9',
        '645f80ed8b8d1135a31024486a6564b03c755a0fe035db48aacbc603d06e86c6', 2,
        'reserved_and_blocked_text_not_numeric_rules'),
}

# Only the three strongest file candidates and their immediate integer helper.
SPANS = {
    'cat_file_and_row_reader': (0x5e150, 0x5e340,
        'c54273c35c46581c576dad0796a571eeb19dd706a22be09a87d852815fc520b8'),
    'god_file_and_row_reader': (0x5e457, 0x5e640,
        'f135678b587335ecd2bad5da9465b5b0ed08ea43cb2568eef0ccbc21edfb811c'),
    'integer_reader_entry': (0x51b50, 0x51b5d,
        '7dafb91342ac20127938197f5c1b8f4c925196358671a7f5c734d68f70a704a3'),
    'integer_conversion': (0x51ba0, 0x51bdc,
        '8ed62b477051dce6b42e1deaecf8574be6323c0dd5bd87450ab0e79668a4d0e5'),
    'spgeft_first_file_call': (0x110bec, 0x110c21,
        '558ddc045badb24d4ecdeb2c2d4a5f77d1599054c320066b0a3ff88ccc1ab87f'),
    'spgeft_second_file_call': (0x12e96d, 0x12e9a8,
        '8672e9b3833f918ad0ffa01ea693e6f403166a3054a8df52bf8557126e1d0260'),
    'spgeft_resource_row_reader': (0x5f2c0, 0x5f448,
        'b5bb5f1dcd77af6971f7f8f71406503f7f2d4eed42192fc28057725d1685a78e'),
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def is_reparse(path):
    return path.is_symlink() or bool(getattr(path.lstat(), 'st_file_attributes', 0) & 0x400)


def reject_links(path):
    if any(is_reparse(p) for p in (path, *path.parents)):
        raise ValueError('Reparse source or ancestor rejected')


def excluded(path):
    return path.suffix.lower() in EXCLUDED_EXTENSIONS or bool(EXCLUDED_NAMES.match(path.name))


def current_files():
    files, skipped, entries = [], [], 0
    for root in TREES:
        reject_links(root)
        for directory, dirs, names in os.walk(root, followlinks=False):
            folder = Path(directory)
            if len(folder.relative_to(root).parts) > MAX_DEPTH:
                raise ValueError('Inventory depth bound')
            for name in sorted(dirs + names):
                entries += 1
                if entries > MAX_ENTRIES:
                    raise ValueError('Inventory entry bound')
                path = folder / name
                reason = 'reparse' if is_reparse(path) else 'excluded_source' if excluded(path) else None
                if reason:
                    directory_entry = name in dirs
                    if directory_entry:
                        dirs.remove(name)
                    skipped.append({'path': path.relative_to(CLIENT).as_posix(), 'reason': reason,
                                    'kind': 'directory' if directory_entry else 'file', 'body_read': False})
                    continue
                if name in names and path.is_file():
                    files.append(path)
                    if len(files) > MAX_FILES:
                        raise ValueError('Inventory file count bound')
            dirs.sort()
    return sorted(files, key=lambda p: p.relative_to(CLIENT).as_posix().lower()), skipped


def bounded_read(path):
    path = Path(os.path.abspath(path))
    root = next((root for root in TREES if path.is_relative_to(root)), None)
    if root is None:
        raise ValueError('Only current Data and Data3 sources may be read')
    if any(excluded(Path(part)) for part in path.relative_to(root).parts):
        raise ValueError('Excluded source must not be opened')
    reject_links(path)
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError('Source escaped current root')
    if path.stat().st_size > MAX_FILE:
        raise ValueError('Per-file byte bound')
    with path.open('rb') as stream:
        raw = stream.read(MAX_FILE + 1)
    if len(raw) > MAX_FILE:
        raise ValueError('Per-file byte bound')
    return raw


def table_rows(plain):
    """Byte-comma fields, preserving physical LF offsets and trailing empties."""
    rows, offset = [], 0
    for number, content in enumerate(plain.split(b'\n'), 1):
        if offset == len(plain):
            break
        raw = content + (b'\n' if offset + len(content) < len(plain) else b'')
        if number > MAX_LINES or len(raw) > MAX_LINE:
            raise ValueError('Table line bound')
        fields = raw.removesuffix(b'\n').removesuffix(b'\r').split(b',')
        rows.append({'line': number, 'decoded_offset': offset, 'length': len(raw),
                     'sha256': sha(raw), 'raw_hex': raw.hex(),
                     'fields_hex': [value.hex() for value in fields]})
        offset += len(raw)
    return rows


def native_evidence():
    reject_links(IMAGE)
    if IMAGE.stat().st_size > MAX_IMAGE:
        raise ValueError('Pinned image byte bound')
    with IMAGE.open('rb') as stream:
        image = stream.read(MAX_IMAGE + 1)
    if len(image) > MAX_IMAGE or sha(image) != IMAGE_SHA:
        raise ValueError('Pinned image hash changed')
    spans = {}
    for name, (lo, hi, expected) in SPANS.items():
        if sha(image[lo:hi]) != expected:
            raise ValueError('Native span changed: ' + name)
        spans[name] = {'start_rva': lo, 'end_rva_exclusive': hi, 'sha256': expected}

    def literal(rva, value, operands):
        if image[rva:rva + len(value) + 1] != value + b'\0':
            raise ValueError('Native literal mismatch')
        for operand in operands:
            if struct.unpack_from('<I', image, operand)[0] != 0x400000 + rva:
                raise ValueError('Native literal operand mismatch')
        return {'literal_rva': rva, 'literal_hex': value.hex(), 'operand_rvas': operands}

    def call(rva, target):
        if image[rva] != 0xe8 or rva + 5 + struct.unpack_from('<i', image, rva + 1)[0] != target:
            raise ValueError('Native call mismatch')
        return {'call_rva': rva, 'target_rva': target, 'bytes_hex': image[rva:rva + 5].hex()}

    def numeric_columns(columns, pushes, calls, stores, base, width):
        result = []
        for index, (column, push, reader, store) in enumerate(zip(columns, pushes, calls, stores)):
            if image[push:push + 2] != bytes((0x6a, column)):
                raise ValueError('Native column push mismatch')
            length = 7 if width == 4 else 8
            displacement = base + index * width
            prefix = b'\x89\x84\x8b' if width == 4 else b'\x66\x89\x84\x8e'
            if image[store:store + length] != prefix + struct.pack('<I', displacement):
                raise ValueError('Native numeric store mismatch')
            result.append({'column': column, 'column_push_rva': push, **call(reader, 0x51b50),
                           'store_rva': store, 'store_hex': image[store:store + length].hex(),
                           'indexed_owner_displacement': displacement, 'width': width})
        return result

    references = {
        'Data/Patch/Cat.csvZ': {
            'path_literal': literal(0x18a240, b'\\Data\\Patch\\', [0x5e163]),
            'file_literal': literal(0x18a238, b'Cat.csv', [0x5e18b]),
            'open_call': call(0x5e1c9, 0x51960), 'index_column': 1, 'record_stride': 44,
            'numeric_columns': numeric_columns(range(6, 11),
                (0x5e290, 0x5e29d, 0x5e2b7, 0x5e2d1, 0x5e2eb),
                (0x5e294, 0x5e2ae, 0x5e2c8, 0x5e2e2, 0x5e2fc),
                (0x5e2a5, 0x5e2bf, 0x5e2d9, 0x5e2f3, 0x5e30b), 0x12204, 4),
            'prior_audit': 'current-world-actor-20260919.md',
            'limit': 'Previously covered CareerType menu reader; no new native execution or wild identity.'},
        'Data/Patch/God.csvZ': {
            'path_literal': literal(0x18a240, b'\\Data\\Patch\\', [0x5e458]),
            'file_literal': literal(0x18a224, b'God.csv', [0x5e486]),
            'open_call': call(0x5e4c4, 0x51960), 'index_column': 1, 'record_stride': 44,
            'numeric_columns': numeric_columns(range(4, 9),
                (0x5e56c, 0x5e579, 0x5e593, 0x5e5ad, 0x5e5c7),
                (0x5e570, 0x5e58a, 0x5e5a4, 0x5e5be, 0x5e5d8),
                (0x5e581, 0x5e59b, 0x5e5b5, 0x5e5cf, 0x5e5e7), 0x125cc, 4),
            'prior_audit': None,
            'limit': 'Protocol-indexed God menu integers; source selection and wild-stat authority unproved.'},
        'Data3/patch/SpgEft.csvZ': {
            'path_literal': literal(0x19c600, b'\\Data3\\Patch\\', [0x110bf2, 0x12e973]),
            'file_literal': literal(0x19c610, b'SpgEft.csv', [0x110bed, 0x12e96e]),
            'loader_calls': [call(0x110c1c, 0x5f2c0), call(0x12e9a3, 0x5f2c0)],
            'index_column': 1, 'record_stride': 76,
            'numeric_columns': numeric_columns((2, 5), (0x5f38a, 0x5f3db),
                (0x5f38e, 0x5f3df), (0x5f39d, 0x5f3ee), 0x121f0, 2),
            'string_columns': [3, 4],
            'limit': 'Resource-ID and sound-index WORDs; no damage formula or monster skill ownership.'},
    }
    return {'path': str(IMAGE), 'sha256': IMAGE_SHA, 'size': len(image), 'base': 0x400000,
            'authority': 'pinned_static_bytes_only; no_native_execution_or_source_open_replay',
            'spans': spans, 'references': references,
            'integer_helper_calls': [call(0x51b55, 0x51ba0), call(0x51bc4, 0x1480b4)],
            'integer_format': literal(0x1823b4, b'%d', [0x51bbf])}


def build_report():
    paths, skipped = current_files()
    inventory, tables, candidates = [], [], []
    total_raw = total_plain = 0
    for path in paths:
        relative = path.relative_to(CLIENT).as_posix()
        size, extension = path.stat().st_size, path.suffix.lower()
        entry = {'path': relative, 'size': size, 'extension': extension, 'sha256': None,
                 'content_status': 'media_body_unexamined', 'runtime_eligible': False}
        inventory.append(entry)
        if extension in MEDIA:
            continue
        if total_raw + size > MAX_TOTAL:
            raise ValueError('Aggregate raw byte bound')
        raw = bounded_read(path)
        total_raw += len(raw)
        if total_raw > MAX_TOTAL:
            raise ValueError('Aggregate raw byte bound')
        entry.update(sha256=sha(raw), content_status='hashed_binary_semantics_unexamined')
        if extension not in TABLE_EXTENSIONS:
            continue
        pin = SOURCES.get(relative)
        if pin and sha(raw) != pin[0]:
            raise ValueError('Current raw source changed: ' + relative)
        # Do not guess another envelope. The existing decoder rejects malformed 0516.
        if extension in {'.csvz', '.mdtz'} or raw[:2] == b'\x05\x16':
            plain = decode_csvz(raw, limit=min(MAX_FILE, MAX_PLAIN - total_plain))
        else:
            plain = raw
        total_plain += len(plain)
        if total_plain > MAX_PLAIN:
            raise ValueError('Aggregate decoded byte bound')
        if pin and sha(plain) != pin[1]:
            raise ValueError('Current decoded source changed: ' + relative)
        rows = table_rows(plain)
        entry.update(content_status='decoded_table_tokens_only', decoded_sha256=sha(plain),
                     decoded_size=len(plain))
        table = {'path': relative, 'sha256': sha(raw), 'decoded_sha256': sha(plain),
                 'decoded_size': len(plain), 'line_count': len(rows), 'rows': rows,
                 'classification': pin[3] if pin else 'unreviewed_decoded_table',
                 'schema': rows[pin[2] - 1] if pin else None,
                 'authority': 'exact_source_fields_only; no_wild_numeric_assignment',
                 'wild_monster_values': None, 'runtime_eligible': False}
        tables.append(table)
    if set(SOURCES) - {table['path'] for table in tables}:
        raise ValueError('Expected current auxiliary table missing or excluded')
    native = native_evidence()
    for table in tables:
        reference = native['references'].get(table['path'])
        if reference is None:
            continue
        candidates.append({key: table[key] for key in
                           ('path', 'sha256', 'decoded_sha256', 'schema', 'classification',
                            'wild_monster_values', 'runtime_eligible')})
        candidates[-1].update(native_reference=reference,
            missing_proof='Original numeric producer/use for a wild monster plus an authoritative '
                          'bank/area/scene/ordinal/variant or participant-lifetime identity binding. '
                          'A Protocol, CareerType, effect ID, matching name or resource is insufficient.')
    status = Counter(row['content_status'] for row in inventory)
    per_tree = {root.name: dict(sorted(Counter(row['extension'] for row in inventory
                if row['path'].startswith(root.name + '/')).items())) for root in TREES}
    return {'schema': 'current-monster-auxiliary-sources-v1',
        'scope': {'roots': [str(root) for root in TREES], 'max_files': MAX_FILES,
                  'max_entries': MAX_ENTRIES, 'max_depth': MAX_DEPTH, 'per_file_byte_limit': MAX_FILE,
                  'raw_byte_limit': MAX_TOTAL, 'decoded_byte_limit': MAX_PLAIN,
                  'image_byte_limit': MAX_IMAGE, 'data2_read': False, 'retired_sources_used': False,
                  'native_execution_performed': False, 'binary_absence_claim': False},
        'summary': {'files_in_scope': len(inventory), 'excluded_entries': len(skipped),
                    'extension_counts_by_tree': per_tree, 'files_hashed': sum(bool(r['sha256']) for r in inventory),
                    'source_bytes_read': total_raw, 'decoded_bytes': total_plain,
                    'decoded_tables': len(tables), 'candidate_count': len(candidates),
                    'unreviewed_decoded_tables': sum(t['classification'] == 'unreviewed_decoded_table' for t in tables),
                    'hashed_binary_semantics_unexamined': status['hashed_binary_semantics_unexamined'],
                    'unread_media_bodies': status['media_body_unexamined'],
                    'unexamined_binary_files': status['hashed_binary_semantics_unexamined'] + status['media_body_unexamined'],
                    'qualified_wild_monster_numeric_sources': 0, 'qualified_wild_monster_numeric_values': 0},
        'inventory': inventory, 'inventory_sha256': sha(json.dumps(inventory, sort_keys=True).encode()),
        'excluded_entries': skipped, 'tables': tables, 'candidates': candidates, 'native': native,
        'field_authority': {field: {'qualified_values': None, 'verified_monster_records': 0} for field in FIELDS},
        'runtime_eligible': False, 'all_monster_numeric_data_complete': False,
        'limitations': ['Nine pinned table classifications and three bounded static readers only.',
                       'All decoded rows retain byte offsets and exact comma fields; labels/tokens are not qualified stats.',
                       'Binary hashes and file extensions do not establish schemas or absence of monster data.',
                       'No content or referenced resource outside Data/Data3 was followed; only the pinned image is additional.',
                       'Actual file selection, formulas, server producers and wild/BOSS identity joins remain unproved.']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--summary', action='store_true')
    args = parser.parse_args()
    report = build_report()
    if args.summary:
        report = {key: report[key] for key in ('scope', 'summary', 'inventory_sha256',
                  'all_monster_numeric_data_complete', 'limitations')}
    print(json.dumps(report, ensure_ascii=True, separators=(',', ':')))


if __name__ == '__main__':
    main()
