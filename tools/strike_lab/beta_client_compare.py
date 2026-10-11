"""Read-only beta/current source comparison; no gameplay semantics inferred."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import struct

from .omega_assets import decode_csvz


def skill_rows(raw, width):
    stride = 4 + 256 * width
    if width not in (108, 110) or len(raw) != 4 + 4 * stride or raw[:4] != b'1.03':
        raise ValueError('Unrecognized skill envelope')
    rows = {}
    for bank in range(4):
        start = 4 + bank * stride
        count = struct.unpack_from('<I', raw, start)[0]
        if count > 255:
            raise ValueError('Skill count bound')
        for index in range(count):
            offset = start + 4 + index * width
            record = raw[offset:offset + width]
            if record[:2] != bytes((index + 1, bank)):
                raise ValueError('Skill identity mismatch')
            rows[bank, index + 1] = (offset, record)
    return rows


def enemy_rows(plain):
    lines = plain.splitlines()
    starts = [i for i, line in enumerate(lines) if line.startswith(b'EnyName,')]
    if len(starts) != 1:
        raise ValueError('Expected one enemy section')
    start = starts[0]
    expected = int(lines[start + 1].split(b',')[1])
    rows = []
    for line in lines[start + 2:]:
        if line.startswith(b'EnyName'):
            continue
        if not re.match(rb'^\d+,', line):
            break
        rows.append(line)
    if len(rows) != expected:
        raise ValueError('Enemy count mismatch')
    return rows


def compare(beta, current):
    files = []
    decoded = {}
    for path in sorted(beta.rglob('*')):
        if not path.is_file():
            continue
        if path.is_symlink() or not path.resolve().is_relative_to(beta.resolve()):
            raise ValueError('Input link escapes source')
        rel = path.relative_to(beta).as_posix()
        item = {'path': rel, 'size': path.stat().st_size}
        if path.suffix.lower() in ('.csvz', '.iniz', '.mdtz', '.bin', '.exe'):
            if item['size'] > 16 * 1024 * 1024:
                raise ValueError('Source size bound')
            raw = path.read_bytes()
            item['sha256'] = hashlib.sha256(raw).hexdigest()
            other = current / rel
            item['same_current_bytes'] = other.is_file() and other.read_bytes() == raw
            if path.suffix.lower() in ('.csvz', '.iniz', '.mdtz'):
                try:
                    plain = decode_csvz(raw, limit=16 * 1024 * 1024)
                    item['decoded_size'] = len(plain)
                    item['decoded_sha256'] = hashlib.sha256(plain).hexdigest()
                    decoded[rel] = plain
                except ValueError as error:
                    item['decode_error'] = str(error)
        files.append(item)
    data_path = 'Data2/Patch/Comm/gamedata.csvZ'
    old = decoded[data_path]
    new = decode_csvz((current / data_path).read_bytes())
    old_enemies, new_enemies = enemy_rows(old), enemy_rows(new)
    skill_path = 'Data2/Fight/Spg/cbspec2.bin'
    old_skills = skill_rows((beta / skill_path).read_bytes(), 108)
    new_skills = skill_rows((current / skill_path).read_bytes(), 110)
    changes = []
    for key, (offset, raw) in old_skills.items():
        peer = new_skills.get(key)
        changes.append({'bank': key[0], 'id': key[1], 'beta_offset': offset,
                        'beta_record_sha256': hashlib.sha256(raw).hexdigest(),
                        'current_offset': peer[0] if peer else None,
                        'same_first_108': peer is not None and raw == peer[1][:108],
                        'different_byte_offsets': [i for i, (a, b) in enumerate(zip(raw, peer[1]))
                                                   if a != b] if peer else None})
    tags = lambda data: set(re.findall(rb'(?m)^([A-Za-z][A-Za-z0-9_]*),', data))
    return {'scope': 'Static source comparison; not native monster-stat or formula proof',
            'beta_root': str(beta), 'current_root': str(current),
            'summary': {'files': len(files), 'decoded_files': len(decoded),
                        'decode_errors': sum('decode_error' in x for x in files),
                        'beta_enemy_rows': len(old_enemies),
                        'beta_enemy_field_counts': dict(Counter(len(x.split(b',')) for x in old_enemies)),
                        'beta_enemy_rows_present_anywhere_current': sum(x in set(new_enemies) for x in old_enemies),
                        'beta_skills': len(old_skills), 'current_skills': len(new_skills),
                        'skill_prefix_equal': sum(x['same_first_108'] for x in changes),
                        'beta_only_gamedata_tags': [x.decode('ascii') for x in sorted(tags(old) - tags(new))]},
            'files': files, 'skill_comparison': changes,
            'caution': 'Same bank/id is a comparison key, not proven cross-version semantic identity. '
                       'Media and other binary bodies not analyzed. Packed executable not unpacked.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--beta', type=Path, required=True)
    parser.add_argument('--current', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    target = args.output.resolve()
    if any(target.is_relative_to(root.resolve()) for root in (args.beta, args.current)):
        raise ValueError('Output cannot be inside either client')
    report = compare(args.beta, args.current)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, ensure_ascii=True, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report['summary'], sort_keys=True))


if __name__ == '__main__':
    main()
