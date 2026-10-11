"""Extract declared recovery amounts, not executable effects, from current source."""
import argparse
from pathlib import Path
import re

from tools.strike_lab.recover_items import build_items, serialize

SOURCE_SHA256 = '70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731'
PATTERNS = (
    (re.compile(r'\u6062\u5fa9\u751f\u547d ([0-9]+)'), 'hp'),
    (re.compile(r'\u6062\u5fa9\u6cd5\u529b ([0-9]+)'), 'mp'),
    (re.compile(r'\u6062\u5fa9\u751f\u547d ([0-9]+)\uff0c\u6cd5\u529b ([0-9]+)'), 'both'),
)


def declared_amounts(raw):
    text = raw.decode('cp950', errors='strict')
    for pattern, kind in PATTERNS:
        match = pattern.fullmatch(text)
        if match:
            amounts = [int(value) for value in match.groups()]
            if any(value < 1 or value > 0x7fffffff for value in amounts):
                return None
            return {'hp': amounts[0] if kind != 'mp' else 0,
                    'mp': amounts[-1] if kind != 'hp' else 0}
    return None


def build(client_root):
    catalog = build_items(client_root)
    if catalog['source']['sha256'] != SOURCE_SHA256:
        raise ValueError('Unqualified supply source build')
    records, unresolved = [], []
    for row in catalog['records']:
        if row['section'] != 'MED02':
            continue
        raw = bytes.fromhex(row['raw_fields_hex'][8])
        try:
            amounts = declared_amounts(raw)
        except UnicodeDecodeError:
            amounts = None
        if amounts is None:
            unresolved.append(row['definition_key'])
            continue
        records.append({key: row[key] for key in ('definition_key', 'client_item_id', 'client_name',
                        'source_line', 'source_record_sha256', 'client_flags')} | {
            'tooltip_column': 8, 'tooltip_raw_hex': raw.hex(), 'declared_recovery': amounts,
            'authority': 'NATIVE_CLIENT_TEXT', 'runtime_eligible': False,
            'server_effect_verified': False})
    return {'schema_version': 1, 'source': catalog['source'], 'records': records,
            'unmatched_med02': unresolved,
            'scope': 'Exact tooltip amounts only. No cap, consumption, target, price, cooldown or server formula inferred.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--client-root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root, output = args.client_root.resolve(), args.output.resolve()
    if output.is_relative_to(root):
        parser.error('Output cannot modify client files')
    result = build(root)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(serialize(result), encoding='utf-8', newline='\n')
    print(f"Exact tooltip declarations: {len(result['records'])}; unmatched MED02: {len(result['unmatched_med02'])}")


if __name__ == '__main__':
    main()
