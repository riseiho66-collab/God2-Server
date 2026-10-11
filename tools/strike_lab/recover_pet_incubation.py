"""Pinned egg/juvenile tooltip evidence, never authoritative gameplay rules."""
import argparse
import json
import re
from pathlib import Path

from .omega_assets import decode_csvz
from .recover_companions import GAME, digest, parse_sections, read_source, serialize

SOURCE_SHA256 = '70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731'
DECODED_SHA256 = '75c3c37947a64b0917fbf8e546884d9bf893fe6a606d3e2b8f3b1857966b1815'
CAP_LABELS = (
    ('compatibility', '\u5951\u5408\u5ea6\u4e0a\u9650'),
    ('health', '\u5065\u5eb7\u6307\u6578\u4e0a\u9650'),
    ('cleanliness', '\u4e7e\u6de8\u6307\u6578\u4e0a\u9650'),
)
TIME_TEXT = {
    9324: (7, '\u9700\u8981\u4ed9\u7ae5\u7d30\u5fc3\u7167\u9867\u4e00\u5c0f\u6642', 1),
    9325: (8, '\u9700\u898120\u5c0f\u6642\u65b9\u80fd\u5b75\u5316', 20),
}
IMMEDIATE = '\u53ef\u4ee5\u7acb\u523b\u9032\u5316\u7684\u5e7c\u5bf5'
UNSUITABLE = '\u4e0d\u9069\u990a\u6b96'


def extract(raw):
    if digest(raw) != SOURCE_SHA256:
        raise ValueError('Unqualified gamedata build; requalify source before extraction')
    decoded = decode_csvz(raw)
    if digest(decoded) != DECODED_SHA256:
        raise ValueError('Decoded source differs from pinned original')
    sections = parse_sections(decoded, ('ItemType', 'EGG', 'SPP'))
    entries = {}
    for tag, expected_count in (('EGG', 27), ('SPP', 28)):
        section = sections[tag]
        if section['declared_count'] != expected_count:
            raise ValueError('Changed section count')
        for row in section['records']:
            fields = row['fields_cp950_display']
            if len(fields) != 27 or not re.fullmatch(r'[0-9]+', fields[0]):
                raise ValueError('Invalid pinned item record')
            identity = int(fields[0])
            if identity in entries:
                raise ValueError('Duplicate source identity')
            claims = []
            if tag == 'SPP':
                for column, (label, prefix) in enumerate(CAP_LABELS, 10):
                    if not fields[column]:
                        continue
                    match = re.fullmatch(re.escape(prefix) + r'([0-9]+)', fields[column])
                    if not match:
                        raise ValueError('Unrecognized juvenile cap text')
                    claims.append({'kind': label + '_tooltip_cap', 'column': column,
                                   'value': int(match[1]), 'text': fields[column]})
                for column, expected, kind in ((7, IMMEDIATE, 'immediate_evolution_tooltip'),
                                               (9, UNSUITABLE, 'unsuitable_for_breeding_tooltip')):
                    if fields[column] == expected:
                        claims.append({'kind': kind, 'column': column, 'text': expected})
            elif identity in TIME_TEXT:
                column, expected, hours = TIME_TEXT[identity]
                if fields[column] != expected:
                    raise ValueError('Changed incubation text')
                claims.append({'kind': 'care_duration_tooltip', 'column': column,
                               'hours': hours, 'text': expected})
            entries[identity] = {
                'source_key': identity, 'section': tag, 'source': row,
                'claims': claims, 'runtime_eligible': False,
                'unknown': {'growth_formula': None, 'evolution_result_distribution': None,
                            'success_probability': None, 'server_timer_rule': None,
                            'request_result_protocol': None},
            }
    return {
        'schema': 'god2-pet-incubation-text-evidence-v1',
        'source_file': GAME, 'source_sha256': digest(raw),
        'decoded_sha256': digest(decoded),
        'qualification': 'Current-client tooltip evidence only; no runtime rules enabled',
        'runtime_eligible': False,
        'classification_source': [r for r in sections['ItemType']['records']
                                  if r['fields_cp950_display'][2] in ('EGG', 'SPP')],
        'entries': [entries[key] for key in sorted(entries)],
        'relationship_policy': 'Do not turn the legacy item_id+100 join into a hatch rule',
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--client-root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    if args.output.resolve().is_relative_to(args.client_root.resolve()):
        parser.error('Output must be outside client source root')
    result = extract(read_source(args.client_root, GAME))
    payload = serialize(result)
    if args.check:
        if args.output.read_bytes() != payload:
            raise SystemExit('Artifact differs')
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_bytes(payload)
    print(json.dumps({'entries': len(result['entries']), 'sha256': digest(payload),
                      'runtime_eligible': False, 'checked': args.check}))


if __name__ == '__main__':
    main()
