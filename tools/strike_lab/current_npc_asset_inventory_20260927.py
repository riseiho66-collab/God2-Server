"""Bounded current-client asset inventory; does not infer NPC placements."""
import argparse
import collections
import csv
import hashlib
import json
from pathlib import Path
import re
import struct

import pefile
from omega_assets import decode_csvz

CLIENT_SHA = '6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98'
ROOT = Path(__file__).resolve().parents[2]
CLIENT = ROOT.parent / 'God2'
RECON = ROOT.parent.parent / 'God2-解殼EXE原始碼重建'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def run(client, reconstruction):
    executable = (client / 'God2.exe').read_bytes()
    if sha(executable) != CLIENT_SHA:
        raise ValueError('Current client SHA256 mismatch')
    pe = pefile.PE(data=executable)
    image = pe.get_memory_mapped_image()
    base = pe.OPTIONAL_HEADER.ImageBase
    data2 = client / 'Data2'
    files = sorted((p for p in data2.rglob('*') if p.is_file()), key=lambda p: str(p).lower())
    manifest, map_headers = [], []
    for path in files:
        with path.open('rb') as stream:
            header = stream.read(256)
        record = {'path': path.relative_to(data2).as_posix(), 'size': path.stat().st_size,
                  'header_16_hex': header[:16].hex(), 'first_256_sha256': sha(header)}
        manifest.append(record)
        if b'MAP v1.1' in header or b'MAPSIZE' in header:
            map_headers.append({**record, 'header_hex': header.hex()})
    tables, animations, errors = [], [], []
    for path in files:
        ext = path.suffix.lower()
        if ext not in ('.csvz', '.rtb'):
            continue
        data = path.read_bytes()
        record = {'path': path.relative_to(data2).as_posix(), 'size': len(data), 'sha256': sha(data)}
        if ext == '.csvz':
            try:
                decoded = decode_csvz(data)
                # Filename hints only, not proof that a table is loaded in this language mode.
                record.update(decoded_size=len(decoded), decoded_sha256=sha(decoded),
                              language_filename_hint='gb' if 'gb' in path.stem.lower() else 'not_gb',
                              first_four_lines_hex=[x.hex() for x in decoded.splitlines()[:4]])
                tables.append(record)
            except ValueError as error:
                errors.append({**record, 'error': str(error)})
        else:
            if len(data) < 14:
                errors.append({**record, 'error': 'RTB shorter than header'})
                continue
            objects, frames = struct.unpack_from('<hh', data, 8)
            expected = 14 + objects * 52 + objects * frames * 12
            record.update(magic_hex=data[:8].hex(), objects=objects, frames=frames,
                          flags_hex=data[12:14].hex(), expected_size=expected,
                          exact_layout=data[:8] == b'rtbv1.0\0' and objects >= 0 and frames >= 0 and expected == len(data))
            animations.append(record)
    binary_path = data2 / 'Fight/Spg/cbspec2.bin'
    binary = binary_path.read_bytes()
    binary_record = {'path': binary_path.relative_to(data2).as_posix(), 'sha256': sha(binary),
                     'size': len(binary), 'magic_hex': binary[:4].hex(),
                     'native_52d3b0_exact_size': len(binary) == 4 + 0x1b810 and binary[:4] == b'1.03'}
    decompiled = reconstruction / 'decompiled'
    with (decompiled / 'functions.tsv').open(encoding='utf-8') as stream:
        functions = list(csv.DictReader(stream, delimiter='\t'))
    entries = {int(r['entry'], 16): r for r in functions}
    addresses = [0x411bb0, 0x412740, 0x4129e0, 0x412aa0, 0x412b50, 0x411ad0,
                 0x412310, 0x412250, 0x413060, 0x412440, 0x411d30,
                 0x438d80, 0x43ff50, 0x42f330, 0x42f1f0, 0x5109d0, 0x52d3b0]
    source_proofs = []
    for address in addresses:
        row = entries[address]
        start, end = int(row['entry'], 16), int(row['end'], 16)
        source = decompiled / row['pseudocode_file']
        source_proofs.append({'entry': hex(start), 'end_inclusive': hex(end),
                             'native_range_sha256': sha(image[start-base:end-base+1]),
                             'pseudocode_path': row['pseudocode_file'],
                             'pseudocode_sha256': sha(source.read_bytes())})
    configurations = []
    for name in ('config.ini', 'config_gb.ini', 'config2.ini', 'config2_gb.ini'):
        path = client / 'Data3' / name
        configurations.append({'path': 'Data3/' + name, 'present': path.is_file(),
                               'sha256': sha(path.read_bytes()) if path.is_file() else None})
    literals = []
    pattern = re.compile(rb'(?:\.ini|\.dat|\.bin|\.csv|\.map)(?:\x00|$)', re.I)
    for match in re.finditer(rb'[ -~]{5,}', image):
        if not pattern.search(match.group()):
            continue
        literals.append({'va': hex(base+match.start()), 'ascii': match.group().decode('ascii')})
    with (decompiled / 'source-path-xrefs.tsv').open(encoding='utf-8') as stream:
        source_refs = [r for r in csv.DictReader(stream, delimiter='\t')
                       if any(term in r['source_path'].lower() for term in ('npc', 'network.cpp', 'map.cpp'))]
    # Counts describe physical supplied files; identical decoded tables and GB variants
    # are not promoted to distinct Taiwan gameplay authorities.
    duplicates = collections.defaultdict(list)
    for row in tables:
        duplicates[row['decoded_sha256']].append(row['path'])
    return {'schema': 'god2-current-npc-asset-inventory-v1', 'client_sha256': CLIENT_SHA,
            'scope': 'Data2 filename inventory, all CSVZ decoding, RTB structural qualification, selected current native readers; no retired sources',
            'files': manifest, 'map_text_header_candidates': map_headers,
            'map_header_scan_scope': 'First 256 raw bytes of every Data2 file; not recursive archive decompression',
            'extension_counts': dict(sorted(collections.Counter(p.suffix.lower() for p in files).items())),
            'csvz': tables, 'csvz_decode_errors': errors,
            'csvz_unique_decoded_sha256': len(duplicates),
            'csvz_identical_decoded_groups': [v for v in duplicates.values() if len(v) > 1],
            'rtb': animations, 'skill_binary': binary_record, 'configuration_paths': configurations,
            'embedded_configuration_literals': literals, 'source_proofs': source_proofs,
            'relevant_original_source_path_refs': source_refs,
            'native_map_writer_43ff50_fields': [
                {'name': 'TileNum', 'source': 'signed WORD cell+4'},
                {'name': 'SpriteNum', 'source': 'BYTE cell+7 & 0x0f'},
                {'name': 'TileIdx', 'source': 'signed WORD cell+0'},
                {'name': 'Pass', 'source': '(BYTE cell+7 & 0x30) >> 4'},
                {'name': 'LinkIdx', 'source': 'signed WORD cell+2'},
                {'name': 'PalNum', 'source': 'BYTE cell+6 & 0x1f'}],
            'qualified_new_native_npc_placements': [],
            'unresolved_edge': 'No binding recovered from scene cell LinkIdx to native NPC instance/catalog identity and facing; original S2C72 or original server placement source still required.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--client', type=Path, default=CLIENT)
    parser.add_argument('--reconstruction', type=Path, default=RECON)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = run(args.client, args.reconstruction)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'output': str(args.output), 'sha256': sha(args.output.read_bytes()),
                      'files': len(result['files']), 'csvz': len(result['csvz']),
                      'decode_errors': len(result['csvz_decode_errors']), 'rtb': len(result['rtb']),
                      'rtb_non_exact': sum(not r['exact_layout'] for r in result['rtb']),
                      'qualified_placements': 0}))
    if result['csvz_decode_errors'] or any(not r['exact_layout'] for r in result['rtb']):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
