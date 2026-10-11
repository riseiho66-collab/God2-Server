"""Unpack current local assets into a new folder; never execute the client.

Raw decoded bytes are authoritative. UTF-8 sidecars and lexical catalogs are
inspection aids, not inferred battle rules or qualified server spawn data.
"""
import argparse
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
import ctypes
import hashlib
import json
from pathlib import Path
import re
import struct

from .omega_assets import decode_csvz
from .current_skill_identity import decode_definitions

MAX_FILE = 64 << 20
MAX_TOTAL_DECODED = 3 << 30
TEXT_EXTENSIONS = {'.csvz', '.iniz', '.mdlz', '.mdtz', '.hmdz', '.can'}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


class NativeDecoder:
    def __init__(self, library):
        self.library = ctypes.CDLL(str(library.resolve()))
        self.function = self.library.decode_asset_lzss
        self.function.argtypes = [ctypes.c_void_p, ctypes.c_size_t,
                                  ctypes.c_void_p, ctypes.c_size_t,
                                  ctypes.c_void_p, ctypes.c_void_p]
        self.function.restype = ctypes.c_int

    def decode(self, raw):
        if len(raw) < 7 or raw[:2] != b'\x05\x16':
            raise ValueError('Missing 05 16 header')
        size, = struct.unpack_from('<I', raw, 2)
        if size > MAX_FILE:
            raise ValueError('Decoded file exceeds bound')
        output = ctypes.create_string_buffer(max(size, 1))
        ring, valid = ctypes.create_string_buffer(4096), ctypes.create_string_buffer(4096)
        status = self.function(raw, len(raw), output, size, ring, valid)
        if status:
            raise ValueError(f'Native decoder rejected input: {status}')
        return output.raw[:size]


def safe_files(client):
    paths = []
    for name in ('Data', 'Data2', 'Data3'):
        for path in (client / name).rglob('*'):
            if path.is_file():
                paths.append(path)
    paths += [p for p in client.iterdir() if p.is_file() and p.suffix.lower() == '.csvz']
    for path in paths:
        for ancestor in (path, *path.parents):
            if ancestor.is_symlink() or getattr(ancestor.lstat(), 'st_file_attributes', 0) & 0x400:
                raise ValueError(f'Reparse point in source path: {path}')
        if not path.resolve().is_relative_to(client) or path.stat().st_size > MAX_FILE:
            raise ValueError(f'Invalid or oversized source: {path}')
    return sorted(paths)


def verify_decoder(decoder, paths):
    # Cover every wrapped extension with one small actual file and malformed
    # boundaries. The optimized decoder must agree with the existing Python
    # reference, including failure instead of an invented ring-tail value.
    chosen = {}
    for path in paths:
        ext = path.suffix.lower()
        if ext.endswith('z') and (ext not in chosen or path.stat().st_size < chosen[ext].stat().st_size):
            chosen[ext] = path
    results = []
    for ext, path in sorted(chosen.items()):
        raw = path.read_bytes()
        expected = decode_csvz(raw, MAX_FILE)
        actual = decoder.decode(raw)
        if actual != expected:
            raise ValueError(f'Reference decoder mismatch: {path}')
        results.append({'extension': ext, 'path': str(path), 'decoded_sha256': sha(actual), 'pass': True})
    invalid = [b'', b'\x05\x16', b'\x05\x16\x01\0\0\0\0',
               b'\x05\x16\x03\0\0\0\0\0\xee\xf0',
               b'\x05\x16\x01\0\0\0\0\xffA\0\0']
    for index, raw in enumerate(invalid):
        rejected = []
        for function in (decoder.decode, decode_csvz):
            try:
                function(raw)
                rejected.append(False)
            except ValueError:
                rejected.append(True)
        if rejected != [True, True]:
            raise ValueError(f'Failure-contract mismatch: {index}: {rejected}')
    return {'actual_file_cases': results, 'malformed_cases_passed': len(invalid)}


def inspect_text(raw, codec):
    decoding = {'codec': codec, 'strict_decode': True}
    try:
        text = raw.decode(codec, errors='strict')
    except UnicodeDecodeError as error:
        # Preserve undefined legacy-codepage bytes visibly rather than dropping
        # an otherwise useful table or silently replacing them with another
        # character. Exact original bytes remain in the decoded file.
        text = raw.decode(codec, errors='backslashreplace')
        decoding.update(strict_decode=False, first_undefined_byte_offset=error.start,
                        display_policy='undefined codepage bytes shown as literal \\xHH; raw file is authoritative')
    # HMD/MDL and CAN are mixed text/binary in some profiles. Do not export a
    # misleading text view just because legacy byte decoding accepts it.
    bad_controls = sum(b < 32 and b not in (9, 10, 13) for b in raw)
    if b'\0' in raw or bad_controls:
        return None, {**decoding, 'binary_controls': bad_controls}
    sections, labels = [], []
    offset = 0
    label_terms = ('等級', '經驗', '成長', '攻擊', '防禦', '命中', '暴擊', '腕力',
                   '體力', '智力', '速度', '技能', '座標', '出生', 'HP', 'MP', 'Level', 'Exp')
    for line_number, line in enumerate(raw.splitlines(keepends=True), 1):
        cells = line.rstrip(b'\r\n').split(b',')
        if len(cells) >= 2 and re.fullmatch(rb'[A-Za-z][A-Za-z0-9_]{1,48}', cells[0]) and cells[1].isdigit():
            sections.append({'tag': cells[0].decode('ascii'), 'number': int(cells[1]),
                             'line': line_number, 'offset': offset,
                             'meaning': 'lexical declaration; count and schema require consumer binding'})
        if line_number <= 80 and not cells[0].strip().isdigit():
            display = line.decode(codec, errors='backslashreplace').rstrip('\r\n')
            if any(term in display for term in label_terms):
                labels.append({'line': line_number, 'offset': offset, 'text': display})
        offset += len(line)
    return text, {**decoding, 'lines': len(raw.splitlines()),
                  'prefix_lines': text.splitlines()[:6], 'sections': sections, 'header_matches': labels}


def extract_one(path, client, output, decoder):
    rel = path.relative_to(client).as_posix()
    before = path.stat()
    raw = path.read_bytes()
    after = path.stat()
    if before.st_size != after.st_size or before.st_mtime_ns != after.st_mtime_ns:
        raise ValueError(f'Source changed during extraction: {rel}')
    entry = {'source': rel, 'source_size': len(raw), 'source_sha256': sha(raw),
             'extension': path.suffix.lower(), 'source_header_hex': raw[:16].hex(),
             'server_eligibility': False}
    wrapped = raw[:2] == b'\x05\x16'
    try:
        plain = decoder.decode(raw) if wrapped else raw
    except ValueError as error:
        return {**entry, 'status': 'decode_failed', 'error': str(error)}
    destination = output / ('decoded' if wrapped else 'passthrough') / (rel + ('.decoded' if wrapped else ''))
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open('xb') as stream:
        stream.write(plain)
    entry.update(status='unpacked' if wrapped else 'uncompressed_copied',
                 output=destination.relative_to(output).as_posix(),
                 decoded_size=len(plain), decoded_sha256=sha(plain),
                 decoded_header_hex=plain[:32].hex())
    if wrapped:
        entry['wrapper_byte_6'] = raw[6]
        entry['declared_size'] = struct.unpack_from('<I', raw, 2)[0]
    if entry['extension'] in TEXT_EXTENSIONS:
        codec = 'cp936' if re.search(r'(?:[-_]gb|lang2)', path.name, re.I) else 'cp950'
        text, metadata = inspect_text(plain, codec)
        entry['text'] = metadata
        if text is not None:
            target = output / 'text-utf8' / (rel + '.txt')
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open('x', encoding='utf-8', newline='') as stream:
                stream.write(text)
            entry['text']['output'] = target.relative_to(output).as_posix()
    if entry['extension'] == '.rtb':
        if len(plain) < 14 or plain[:8] != b'rtbv1.0\0':
            entry['structure'] = {'valid': False}
        else:
            objects, frames = struct.unpack_from('<hh', plain, 8)
            expected = 14 + objects * 52 + objects * frames * 12
            entry['structure'] = {'version': 'rtbv1.0', 'objects': objects, 'frames': frames,
                                  'fully_accounted': objects >= 0 and frames >= 0 and expected == len(plain),
                                  'use': 'animation metadata; not monster battle statistics'}
    if rel == 'Data2/Fight/Spg/cbspec2.bin':
        definitions = decode_definitions(plain)
        records = [{'kind': d.kind, 'id': d.id, 'offset': d.source_offset, 'raw_hex': d.raw.hex()}
                   for d in definitions.values()]
        (output / 'skill-definitions-raw.json').write_text(json.dumps(records, indent=2), encoding='utf-8')
        entry['structure'] = {'version': '1.03', 'records': len(records),
                              'groups': dict(Counter(d.kind for d in definitions.values())),
                              'use': 'qualified identities; remaining numeric bytes retain unverified semantics'}
    return entry


def run(client, output, library):
    client, output = client.resolve(), output.resolve()
    if output.is_relative_to(client) or client.is_relative_to(output):
        raise ValueError('Output must be separate from original client')
    if output.exists():
        raise ValueError('Output already exists; refusing overwrite')
    paths = safe_files(client)
    declared_total = 0
    for path in paths:
        with path.open('rb') as stream:
            header = stream.read(7)
        if header[:2] == b'\x05\x16':
            if len(header) < 7:
                raise ValueError(f'Truncated wrapper: {path}')
            size, = struct.unpack_from('<I', header, 2)
            if size > MAX_FILE:
                raise ValueError(f'Declared file exceeds bound: {path}')
            declared_total += size
    if declared_total > MAX_TOTAL_DECODED:
        raise ValueError('Aggregate expansion exceeds bound')
    decoder = NativeDecoder(library)
    validation = verify_decoder(decoder, paths)
    output.mkdir(parents=True, exist_ok=False)
    print(json.dumps({'event': 'started', 'files': len(paths), 'declared_bytes': declared_total,
                      'output': str(output)}, ensure_ascii=True), flush=True)
    inventory = []
    with ThreadPoolExecutor(max_workers=4) as pool:
        for count, entry in enumerate(pool.map(lambda p: extract_one(p, client, output, decoder), paths), 1):
            inventory.append(entry)
            if count % 1000 == 0:
                print(json.dumps({'event': 'progress', 'processed': count, 'total': len(paths)}), flush=True)
    families = defaultdict(Counter)
    for entry in inventory:
        family = families[entry['extension']]
        family['files'] += 1
        family[entry['status']] += 1
        family['source_bytes'] += entry['source_size']
        family['decoded_bytes'] += entry.get('decoded_size', 0)
    failures = [e for e in inventory if e['status'] == 'decode_failed']
    summary = {'client_root': str(client), 'output': str(output),
               'files': len(inventory), 'unpacked': sum(e['status'] == 'unpacked' for e in inventory),
               'passthrough': sum(e['status'] == 'uncompressed_copied' for e in inventory),
               'failed': len(failures), 'families': dict(families),
               'text_views': sum(bool(e.get('text', {}).get('output')) for e in inventory),
               'decoder_validation': validation,
               'decoder_dll_sha256': sha(library.read_bytes()),
               'decoder_source_sha256': sha(Path(__file__).with_name('native_asset_lzss.cpp').read_bytes()),
               'scope': 'All regular files in Data/Data2/Data3 and five root CSVZ tables; no Save, account, EXE, memory or server mutation.',
               'limits': 'Decompression is verified byte recovery. A numeric token, model position or description is not a qualified server rule.',
               'failed_sources': failures}
    (output / 'manifest.json').write_text(json.dumps(inventory, ensure_ascii=False, indent=2), encoding='utf-8')
    (output / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    text_catalog = [{key: e[key] for key in ('source', 'source_sha256', 'decoded_sha256', 'text')}
                    for e in inventory if 'text' in e]
    (output / 'text-catalog.json').write_text(json.dumps(text_catalog, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({k: summary[k] for k in ('files', 'unpacked', 'passthrough', 'failed', 'text_views', 'output')}, ensure_ascii=True), flush=True)
    if failures:
        raise ValueError('One or more assets were not decoded; inspect explicit failure records')


def refresh_text(output):
    """Refresh only our inspection sidecars, keeping decoded/source bytes intact."""
    inventory = json.loads((output / 'manifest.json').read_text(encoding='utf-8'))
    for entry in inventory:
        if entry['extension'] not in TEXT_EXTENSIONS or 'output' not in entry:
            continue
        raw = (output / entry['output']).read_bytes()
        if sha(raw) != entry['decoded_sha256']:
            raise ValueError(f'Decoded bytes changed: {entry["source"]}')
        codec = 'cp936' if re.search(r'(?:[-_]gb|lang2)', Path(entry['source']).name, re.I) else 'cp950'
        text, metadata = inspect_text(raw, codec)
        entry['text'] = metadata
        if text is not None:
            target = output / 'text-utf8' / (entry['source'] + '.txt')
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open('w', encoding='utf-8', newline='') as stream:
                stream.write(text)
            entry['text']['output'] = target.relative_to(output).as_posix()
    summary = json.loads((output / 'summary.json').read_text(encoding='utf-8'))
    summary['text_views'] = sum(bool(e.get('text', {}).get('output')) for e in inventory)
    summary['escaped_text_views'] = sum(bool(e.get('text', {}).get('output')) and not e['text']['strict_decode'] for e in inventory)
    (output / 'manifest.json').write_text(json.dumps(inventory, ensure_ascii=False, indent=2), encoding='utf-8')
    (output / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    catalog = [{key: e[key] for key in ('source', 'source_sha256', 'decoded_sha256', 'text')}
               for e in inventory if 'text' in e]
    (output / 'text-catalog.json').write_text(json.dumps(catalog, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'text_views': summary['text_views'], 'escaped_text_views': summary['escaped_text_views']}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--client', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--decoder-library', type=Path)
    parser.add_argument('--refresh-text', action='store_true')
    args = parser.parse_args()
    if args.refresh_text:
        refresh_text(args.output.resolve())
    else:
        if args.client is None or args.decoder_library is None:
            parser.error('--client and --decoder-library are required for extraction')
        run(args.client, args.output, args.decoder_library)
