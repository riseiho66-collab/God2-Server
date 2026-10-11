"""All-line current table index for attack/defense source discovery.

Labels and prose are evidence locations, not wild-monster numeric authority.
Only current Data/Data2/Data3 CSV/CSVZ bodies are read. Binary/ROM payloads
and executable producer analysis are outside this lexical index.
"""
import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import re

from .omega_assets import decode_csvz

ROOT = Path(__file__).resolve().parents[2]
CLIENT = ROOT.parent / 'God2'
TREES = ('Data', 'Data2', 'Data3')
MAX_FILE, MAX_TOTAL, MAX_FILES = 8 << 20, 32 << 20, 128
LABELS = {
    'physical_attack': ('physical_attack', 'physical attack', '\u7269\u653b', '\u7269\u7406\u653b\u64ca', '\u7269\u7406\u653b\u64ca\u529b'),
    'physical_defense': ('physical_defense', 'physical defense', '\u7269\u9632', '\u7269\u7406\u9632\u79a6', '\u7269\u7406\u9632\u79a6\u529b'),
    'magical_attack': ('magical_attack', 'magic_attack', '\u9b54\u653b', '\u6cd5\u653b', '\u6cd5\u8853\u653b\u64ca', '\u9b54\u6cd5\u653b\u64ca'),
    'magical_defense': ('magical_defense', 'magic_defense', '\u9b54\u9632', '\u6cd5\u9632', '\u6cd5\u8853\u9632\u79a6', '\u9b54\u6cd5\u9632\u79a6'),
}
MENTIONS = re.compile('|'.join(re.escape(term) for terms in LABELS.values() for term in terms), re.I)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def reparse(path):
    return path.is_symlink() or bool(getattr(path.lstat(), 'st_file_attributes', 0) & 0x400)


def table_files():
    files = []
    for tree in TREES:
        root = CLIENT / tree
        if any(reparse(p) for p in (root, *root.parents)):
            raise ValueError('Current table root must not traverse a reparse point')
        for directory, dirs, names in os.walk(root, followlinks=False):
            folder = Path(directory)
            if len(folder.relative_to(root).parts) > 12:
                raise ValueError('Table directory depth bound')
            if any(reparse(folder / name) for name in dirs):
                raise ValueError('Reparse directory prevents complete table inventory')
            for name in names:
                path = folder / name
                if path.suffix.lower() in ('.csv', '.csvz'):
                    if reparse(path) or not path.is_file():
                        raise ValueError('Current table is not a regular file')
                    files.append(path)
                    if len(files) > MAX_FILES:
                        raise ValueError('Table file count bound')
    return sorted(files, key=lambda p: p.relative_to(CLIENT).as_posix().lower())


def scan_table(plain):
    if len(plain) > MAX_FILE:
        raise ValueError('Decoded table byte bound')
    offset, line_count = 0, 0
    matches, exact, decode_failures = [], [], 0
    for number, content in enumerate(plain.split(b'\n'), 1):
        if offset == len(plain):
            break
        raw = content + (b'\n' if offset + len(content) < len(plain) else b'')
        line_count = number
        if len(raw) > 65536:
            raise ValueError('Physical line bound')
        body = raw.removesuffix(b'\n').removesuffix(b'\r')
        try:
            text = body.decode('cp950')
        except UnicodeDecodeError:
            decode_failures += 1
            text = body.decode('cp950', errors='replace')
        if MENTIONS.search(text):
            matches.append({'line': number, 'decoded_offset': offset, 'length': len(raw), 'sha256': sha(raw)})
            fields = body.split(b',')  # Original table tokenizer uses literal commas.
            column_offset = offset
            cells = []
            for column, field in enumerate(fields):
                label = field.decode('cp950', errors='replace').strip().lower()
                for kind, terms in LABELS.items():
                    if label in terms:
                        cells.append({'column': column, 'decoded_offset': column_offset,
                                      'label_hex': field.hex(), 'search_category': kind})
                column_offset += len(field) + 1
            if cells:
                exact.append({**matches[-1], 'field_count': len(fields),
                              'first_field_hex': fields[0].hex(), 'labels': cells,
                              'interpretation': 'Exact label cells only; schema and numeric ownership unqualified'})
        offset += len(raw)
    if offset != len(plain):
        raise AssertionError('Full decoded byte coverage differs')
    return {'lines_scanned': line_count, 'bytes_scanned': offset,
            'cp950_invalid_lines': decode_failures, 'mention_rows': matches, 'exact_label_rows': exact}


def discover():
    records, raw_total, plain_total = [], 0, 0
    for path in table_files():
        if path.stat().st_size > MAX_FILE:
            raise ValueError('Current source byte bound')
        raw = path.read_bytes()
        plain = decode_csvz(raw, limit=MAX_FILE) if path.suffix.lower() == '.csvz' else raw
        raw_total += len(raw)
        plain_total += len(plain)
        if max(raw_total, plain_total) > MAX_TOTAL:
            raise ValueError('Aggregate current table byte bound')
        records.append({'path': path.relative_to(CLIENT).as_posix(), 'raw_sha256': sha(raw),
                        'plain_sha256': sha(plain), 'raw_bytes': len(raw), 'plain_bytes': len(plain),
                        **scan_table(plain)})
    labels = Counter(label['search_category'] for file in records
                     for row in file['exact_label_rows'] for label in row['labels'])
    return {'scope': 'Every physical line of current Data/Data2/Data3 CSV and CSVZ files only',
            'file_count': len(records), 'raw_bytes': raw_total, 'decoded_bytes': plain_total,
            'lines_scanned': sum(r['lines_scanned'] for r in records),
            'mention_rows': sum(len(r['mention_rows']) for r in records),
            'exact_label_cells': dict(labels), 'files': records,
            'original_monster_values_recovered': 0, 'database_promotions': 0,
            'limits': ['Lexical matches do not prove numeric meaning or monster identity',
                       'No native loader or consumer execution in this index',
                       'Non-table binary/ROM contents remain outside scope',
                       'Invalid CP950 lines retain byte provenance; text matching is not exhaustive']}


def summary(report):
    return {**{k: v for k, v in report.items() if k != 'files'},
            'matching_files': [{'path': f['path'], 'mention_rows': len(f['mention_rows']),
                                'exact_label_rows': f['exact_label_rows'],
                                'cp950_invalid_lines': f['cp950_invalid_lines']}
                               for f in report['files'] if f['mention_rows']]}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--summary', action='store_true')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    report = discover()
    if args.output:
        output = args.output.resolve()
        if output.parent != (ROOT / 'artifacts/research').resolve() or output.exists():
            raise ValueError('Output must be a new file in artifacts/research')
        output.write_text(json.dumps(report, indent=2, ensure_ascii=True) + '\n', encoding='utf-8')
    print(json.dumps(summary(report) if args.summary else report, ensure_ascii=True))
