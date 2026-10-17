"""Deterministic current-client companion evidence; no gameplay mutations."""
import argparse
import hashlib
import json
from pathlib import Path
import re

from .omega_assets import decode_csvz

GAME = 'Data2/Patch/Comm/gamedata.csvZ'
MESSAGES = 'Data2/Patch/Comm/message.csvZ'
SECTIONS = ('ItemType', 'GOD', 'PET', 'COM', 'NCP', 'GodLevel',
            'FightPetSkill', 'NewFightPet2Skill')
FAMILY_LABELS = {'GOD': '\u795e\u4ed9\u540d', 'PET': '\u795e\u7378',
                 'COM': '\u7d19\u5a03\u5a03\u5408\u6210\u6230\u5bf5', 'NCP': '\u4e8c\u4ee3\u5bf5'}
# Each mapping is accepted only with an exact current-client message match.
MESSAGE_CLAIMS = {
    508: ('immortal', 'release_notice', '\u795e\u4ed9\u300e%s\u300f\u5df2\u89e3\u653e'),
    509: ('immortal', 'release_restriction', '\u8f49\u751f\u795e\u4ed9\u4e0d\u53ef\u89e3\u653e\uff0c\u89e3\u653e\u5931\u6557'),
    510: ('immortal', 'release_restriction', '\u672c\u8077\u795e\u4ed9\u4e0d\u53ef\u89e3\u653e\uff0c\u89e3\u653e\u5931\u6557'),
    710: ('battle_pet', 'skill_learning_restriction', '\u6230\u5bf5\u76ee\u524d\u689d\u4ef6\u7121\u6cd5\u5b78\u7fd2\u6280\u80fd[%s]'),
    742: ('battle_pet', 'death_notice', '\u4f60\u7684\u6230\u5bf5\u5df2\u7d93\u6b7b\u4ea1'),
    807: ('immortal', 'acquisition_notice', '\u53d6\u5f97\u795e\u4ed9[%s]'),
    845: ('immortal', 'level_cap_release_notice', '\u4f60\u7684\u795e\u4ed9\u5df2\u901a\u904e\u5361\u7b49\u9650\u5236\uff0c\u53ef\u4ee5\u7e7c\u7e8c\u5347\u7d1a\u4e86\uff01'),
    860: ('immortal', 'level_up_notice', '\u606d\u559c!!!\u795e\u4ed9[%s]\u7b49\u7d1a\u63d0\u6607\u4e86\u3002'),
    861: ('battle_pet', 'level_up_notice', '\u606d\u559c!!!\u6230\u5bf5[%s]\u7b49\u7d1a\u63d0\u6607\u4e86\u3002'),
}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def read_source(root, relative):
    root = Path(root).resolve()
    path = root / relative
    if not path.resolve().is_relative_to(root):
        raise ValueError('Source escapes root')
    with path.open('rb') as stream:
        raw = stream.read(64 * 1024 * 1024 + 1)
    if len(raw) > 64 * 1024 * 1024:
        raise ValueError('Source exceeds import bound')
    return raw


def record(raw, line, offset):
    fields = raw.rstrip(b'\r\n').split(b',')
    return {'source_line': line, 'decoded_offset': offset,
            'raw_record_hex': raw.hex(), 'sha256': digest(raw),
            'fields_hex': [f.hex() for f in fields],
            'fields_cp950_display': [f.decode('cp950', errors='backslashreplace') for f in fields]}


def parse_sections(decoded, names):
    # Split only LF: the source has CR CR LF; byte offsets remain untouched.
    lines = decoded.split(b'\n')
    offsets, offset = [], 0
    for line in lines:
        offsets.append(offset)
        offset += len(line) + 1
    result = {}
    for name in names:
        matches = [i for i, line in enumerate(lines) if line.startswith(name.encode('ascii') + b',')]
        if len(matches) != 1:
            raise ValueError('Expected exactly one section: ' + name)
        start = matches[0]
        header = lines[start].rstrip(b'\r').split(b',')
        if len(header) != 2 or not re.fullmatch(rb'[0-9]{1,5}', header[1]):
            raise ValueError('Invalid section count: ' + name)
        count = int(header[1])
        if not 1 <= count <= 32767 or start + count >= len(lines):
            raise ValueError('Invalid section count: ' + name)
        # Section envelopes are structural evidence, not companion field semantics.
        boundary = rb'[A-Za-z][A-Za-z0-9_]*,[0-9]+(?:,|$)'
        end = start + count + 1
        if end < len(lines):
            following = lines[end].rstrip(b'\r')
            if following and not re.match(boundary, following):
                raise ValueError('Undeclared section records: ' + name)
        rows = []
        for i in range(start + 1, start + count + 1):
            if not lines[i].rstrip(b'\r') or b'\0' in lines[i]:
                raise ValueError('Empty or NUL record: ' + name)
            if re.match(boundary, lines[i].rstrip(b'\r')):
                raise ValueError('Section count crosses next header: ' + name)
            raw = lines[i] + (b'\n' if i < len(lines) - 1 else b'')
            rows.append(record(raw, i + 1, offsets[i]))
        result[name] = {'header': record(lines[start] + b'\n', start + 1, offsets[start]),
                        'declared_count': count, 'records': rows}
    return result


def validated_message_record(row):
    # Rebuild every derived field; caller dictionaries are not source authority.
    try:
        raw = bytes.fromhex(row['raw_record_hex'])
        line, offset = row['source_line'], row['decoded_offset']
        if type(line) is not int or line < 1 or type(offset) is not int or offset < 0:
            raise ValueError('Invalid source location')
        if not raw.rstrip(b'\r\n') or b'\0' in raw or b'\n' in raw[:-1]:
            raise ValueError('Invalid raw record')
        canonical = record(raw, line, offset)
        if row != canonical:
            raise ValueError('Record differs from raw bytes')
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError('Inconsistent message record') from error
    return canonical


def message_claims(section):
    records = [validated_message_record(row) for row in section['records']]
    claims = []
    for message_id, (family, kind, expected) in sorted(MESSAGE_CLAIMS.items()):
        matches = [r for r in records if r['fields_hex'][0] == str(message_id).encode().hex()]
        if len(matches) != 1:
            raise ValueError('Missing or duplicate message: ' + str(message_id))
        row = matches[0]
        if len(row['fields_hex']) != 3 or bytes.fromhex(row['fields_hex'][2]) != expected.encode('cp950'):
            raise ValueError('Message text changed: ' + str(message_id))
        claims.append({'message_id': message_id, 'family': family, 'kind': kind,
                       'source_file': MESSAGES, 'text_column': 2,
                       'evidence_class': 'current_client_message_text_only',
                       'runtime_eligible': False, 'text': expected, 'source': row,
                       'unknown': ['trigger consumer', 'state storage', 'wire mapping', 'transaction behavior']})
    return claims


def build_companions(client_root):
    sources = {}
    decoded = {}
    for relative in (GAME, MESSAGES):
        raw = read_source(client_root, relative)
        plain = decode_csvz(raw)
        sources[relative] = {'sha256': digest(raw), 'size': len(raw),
                             'decoded_sha256': digest(plain), 'decoded_size': len(plain)}
        decoded[relative] = plain
    sections = parse_sections(decoded[GAME], SECTIONS)
    for section in sections.values():
        section['source_file'] = GAME
    classification = []
    for tag, family in (('GOD', 'immortal'), ('PET', 'pet_unqualified'),
                        ('COM', 'battle_pet'), ('NCP', 'battle_pet')):
        type_rows = [r for r in sections['ItemType']['records']
                     if r['fields_hex'][2] == tag.encode().hex()]
        if len(type_rows) != 1:
            raise ValueError('Missing or duplicate ItemType: ' + tag)
        if bytes.fromhex(type_rows[0]['fields_hex'][3]) != FAMILY_LABELS[tag].encode('cp950'):
            raise ValueError('Changed family classification label: ' + tag)
        classification.append({'section': tag, 'family': family, 'evidence': type_rows[0],
                               'source_file': GAME,
                               'basis': 'ItemType column 2 section tag and column 3 Chinese label; inspect row descriptions too',
                               'record_count': len(sections[tag]['records'])})
    return {
        'schema': 'god2-companion-evidence-v1', 'sources': sources,
        'qualification': 'Definition and message-text extraction only; no server or client integration',
        'encoding': 'cp950 display only; raw bytes are authoritative; escaped undecodable bytes are not repaired',
        'classification': classification, 'sections': sections,
        'transition_and_restriction_evidence': message_claims(parse_sections(decoded[MESSAGES], ('SystemMessage',))['SystemMessage']),
        'field_policy': 'Zero-based positional fields. No COM/NCP skill-column, flag, requirement, formula or relationship interpretation without consumer proof.',
        'unknown': ['GOD ownership and skill relationships', 'COM/NCP skill-slot relationships and requirements',
                    'summon/growth/fusion packets and formulas', 'PET transport versus other subtype semantics'],
        'next_hooks': [
            'Trace the current Taiwan client GOD loader and identity fields before assigning semantics.',
            'Trace current gamedata COM/NCP loader tail fields to FightPetSkill/NewFightPet2Skill consumers before binding skills.',
            'Trace current Taiwan SystemMessage consumers for imported message IDs before implementing mutations.',
        ],
    }


def serialize(result):
    return (json.dumps(result, ensure_ascii=True, sort_keys=True, indent=2) + '\n').encode('ascii')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--client-root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--check', action='store_true', help='Compare existing artifact without writing')
    args = parser.parse_args()
    # Never allow CLI output into a source tree, including symlink aliases.
    target = args.output.resolve()
    if target.is_relative_to(args.client_root.resolve()):
        parser.error('Output must be outside all source roots')
    result = build_companions(args.client_root)
    output = serialize(result)
    if args.check:
        if args.output.read_bytes() != output:
            raise SystemExit('Artifact differs')
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_bytes(output)
    print(json.dumps({'counts': {k: len(v['records']) for k, v in result['sections'].items()},
                      'message_claims': len(result['transition_and_restriction_evidence']),
                      'sha256': digest(output), 'checked': args.check}, sort_keys=True))


if __name__ == '__main__':
    main()
