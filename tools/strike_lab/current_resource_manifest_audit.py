"""Read-only current-client patch manifest audit; no network or stat inference."""
import hashlib
import json
from pathlib import Path, PureWindowsPath
import re
from .omega_assets import decode_csvz

ROOT = Path(__file__).resolve().parents[2]
CLIENT = ROOT.parent / 'God2'
MANIFESTS = ('client.godZ', 'client_p.godZ', 'god_crc.txtZ')
DATA_TREES = {'data', 'data2', 'data3'}


def audit():
    sources, records = [], {}
    for name in MANIFESTS:
        raw = (CLIENT / name).read_bytes()
        if len(raw) > 2 << 20:
            raise ValueError('Manifest byte bound')
        plain = decode_csvz(raw, limit=4 << 20)
        sources.append({'path': name, 'sha256': hashlib.sha256(raw).hexdigest(),
                        'decoded_sha256': hashlib.sha256(plain).hexdigest(),
                        'decoded_bytes': len(plain), 'format': '0516_LZSS_no_key'})
        directory = PureWindowsPath('.')
        for line_number, line in enumerate(plain.splitlines(), 1):
            if line.startswith(b'Directory : '):
                directory = PureWindowsPath(line[len(b'Directory : '):].decode('cp950'))
                if directory.is_absolute() or directory.drive or '..' in directory.parts:
                    raise ValueError('Manifest directory escapes client')
                continue
            match = re.fullmatch(rb'\s+([^,]+),\s+(\d+),\s+(\d+),\s+(.+)', line)
            if not match:
                continue
            filename = PureWindowsPath(match[1].strip().decode('cp950'))
            if len(filename.parts) != 1 or filename.drive or filename.name in ('.', '..'):
                raise ValueError('Manifest filename escapes directory')
            relative = directory / filename
            if not relative.parts or relative.parts[0].lower() not in DATA_TREES:
                continue
            key = relative.as_posix().lower()
            row = records.setdefault(key, {'path': relative.as_posix(), 'references': []})
            row['references'].append({'manifest': name, 'line': line_number,
                                      'size': int(match[2]), 'crc32_decimal': int(match[3])})
    for row in records.values():
        local = CLIENT.joinpath(*PureWindowsPath(row['path']).parts)
        if not local.resolve().is_relative_to(CLIENT.resolve()) or local.is_symlink():
            raise ValueError('Current path escape')
        row['present'] = local.is_file()
        row['actual_size'] = local.stat().st_size if row['present'] else None
        row['extension'] = local.suffix.lower()
        row['manifest_sizes_match'] = row['present'] and all(
            r['size'] == row['actual_size'] for r in row['references'])
    missing = [r for r in records.values() if not r['present']]
    changed = [r for r in records.values() if r['present'] and not r['manifest_sizes_match']]
    return {'sources': sources, 'manifest_resource_count': len(records),
            'missing': missing, 'size_mismatch': changed,
            'binary_database_candidates': [r for r in records.values()
                if r['extension'] in ('.bin', '.dat', '.db', '.mdb', '.pak', '.spi', '.enc')],
            'scope': 'Current patch manifests only; existence/size are not schema or CRC validation. No resource body, endpoint, credentials or retired corpus is read. No monster stat or total-client absence is inferred.',
            'records': list(records.values())}


if __name__ == '__main__':
    print(json.dumps(audit(), ensure_ascii=True, indent=2))
