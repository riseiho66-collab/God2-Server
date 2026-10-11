"""Inspect complete unpacked resource envelopes and source tables, offline."""
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import struct
import sys


def rom_envelope(root, entry):
    data = (root / entry['output']).read_bytes()
    if hashlib.sha256(data).hexdigest() != entry['decoded_sha256']:
        raise ValueError('Decoded ROM changed: ' + entry['source'])
    if data[:12] != b'IGSROM02\0\0\0\0':
        raise ValueError('ROM header: ' + entry['source'])
    position, counts, sizes, unknown, actions = 12, Counter(), Counter(), [], []
    palette_sizes = []
    ended, actindex = False, None
    known = {b'ACTINDEX', b'ACTBLOCK', b'PALETTE1', b'PCX_RWIF', b'TGA_RWIF',
             b'ACT_DATA', b'ACT_STEP', b'ACT_POOL', b'FILE_END',
             b'PCA_RWIF', b'PCX_DATA', b'PCS_DATA'}
    additional_images = Counter()
    while position < len(data):
        if position + 12 > len(data):
            raise ValueError('Truncated ROM chunk header: ' + entry['source'])
        tag, size = struct.unpack_from('<8sI', data, position)
        end = position + 12 + size
        if end > len(data):
            raise ValueError('Truncated ROM chunk body: ' + entry['source'])
        name = tag.decode('ascii', errors='backslashreplace')
        counts[name] += 1
        sizes[name] += size
        if tag not in known:
            unknown.append({'tag_hex': tag.hex(), 'offset': position, 'size': size})
        if tag in (b'PCA_RWIF', b'PCX_DATA', b'PCS_DATA'):
            if size < 128 or data[position + 12:position + 16] != b'\x0a\x05\x01\x08':
                raise ValueError('Additional PCX header profile: ' + entry['source'])
            additional_images[name] += 1
        if tag == b'ACTINDEX':
            if size != 2:
                raise ValueError('ACTINDEX width: ' + entry['source'])
            actindex, = struct.unpack_from('<H', data, position + 12)
        elif tag == b'ACT_DATA':
            if size != 48:
                raise ValueError('ACT_DATA width: ' + entry['source'])
            raw = data[position + 12:end]
            values = struct.unpack_from('<6i', raw)
            actions.append({'id': values[0], 'offset': position,
                            'name': raw[24:].split(b'\0', 1)[0].decode('cp950', errors='backslashreplace'),
                            'raw_name_hex': raw[24:].hex(),
                            'declared_steps': values[4], 'declared_pools': values[5],
                            'step_chunks': 0, 'pool_chunks': 0})
        elif tag == b'ACT_STEP':
            if not actions or size % 10:
                raise ValueError('ACT_STEP boundary: ' + entry['source'])
            actions[-1]['step_chunks'] += 1
        elif tag == b'ACT_POOL':
            if not actions or size != 10:
                raise ValueError('ACT_POOL boundary: ' + entry['source'])
            actions[-1]['pool_chunks'] += 1
        elif tag == b'PALETTE1':
            # Some true-color resources supply an empty palette. Record the
            # actual width; the 512-byte indexed profile is not universal.
            palette_sizes.append(size)
        elif tag == b'FILE_END':
            if size != 0 or end != len(data):
                raise ValueError('FILE_END/trailing boundary: ' + entry['source'])
            ended = True
        position = end
    if not ended:
        raise ValueError('ROM FILE_END missing: ' + entry['source'])
    mismatch = [a for a in actions if (a['step_chunks'], a['pool_chunks']) != (a['declared_steps'], a['declared_pools'])]
    return {'source': entry['source'], 'decoded_sha256': entry['decoded_sha256'],
            'bytes_accounted': position, 'actindex': actindex,
            'chunks': dict(counts), 'payload_bytes': dict(sizes), 'unknown_chunks': unknown,
            'palette_sizes': palette_sizes,
            'additional_pcx_header_matches': dict(additional_images),
            'action_count_mismatches': mismatch, 'actions': actions}


def bmp_envelope(root, entry):
    data = (root / entry['output']).read_bytes()
    if hashlib.sha256(data).hexdigest() != entry['decoded_sha256']:
        raise ValueError('Decoded MMB changed')
    if len(data) < 54 or data[:2] != b'BM':
        raise ValueError('MMB BMP header')
    size, = struct.unpack_from('<I', data, 2)
    offset, = struct.unpack_from('<I', data, 10)
    dib, width, height, planes, depth, compression = struct.unpack_from('<IiiHHI', data, 14)
    if size != len(data) or not 54 <= offset <= size or dib != 40 or planes != 1:
        raise ValueError('MMB BMP envelope')
    return {'source': entry['source'], 'decoded_sha256': entry['decoded_sha256'],
            'bytes': size, 'pixel_offset': offset, 'width': width, 'height': height,
            'depth': depth, 'compression': compression, 'use': 'minimap image'}


def source_rows(root, manifest, source, header_lines):
    entry = next(e for e in manifest if e['source'] == source)
    data = (root / entry['output']).read_bytes()
    if hashlib.sha256(data).hexdigest() != entry['decoded_sha256']:
        raise ValueError('Source table changed')
    rows, offset = [], 0
    for line_number, raw in enumerate(data.splitlines(keepends=True), 1):
        if line_number > header_lines:
            fields = raw.rstrip(b'\r\n').split(b',')
            rows.append({'line': line_number, 'offset': offset,
                         'fields': [f.decode('cp950', errors='backslashreplace') for f in fields],
                         'raw_hex': raw.hex()})
        offset += len(raw)
    return {'source': source, 'source_sha256': entry['source_sha256'],
            'decoded_sha256': entry['decoded_sha256'], 'rows': rows,
            'authority': 'Exact source tokens only; no inferred battle arithmetic or unit conversions.'}


def run(root):
    manifest = json.loads((root / 'manifest.json').read_text(encoding='utf-8'))
    roms = [e for e in manifest if e['extension'] == '.romz']
    with ThreadPoolExecutor(max_workers=4) as pool:
        envelopes = list(pool.map(lambda e: rom_envelope(root, e), roms))
    chunks, payload = Counter(), Counter()
    for rom in envelopes:
        chunks.update(rom['chunks'])
        payload.update(rom['payload_bytes'])
    # Keep source offsets for every action and fully account for each ROM file.
    (root / 'rom-chunks.json').write_text(json.dumps(envelopes, ensure_ascii=False, indent=2), encoding='utf-8')
    maps = [bmp_envelope(root, e) for e in manifest if e['extension'] == '.mmbz']
    (root / 'minimap-images.json').write_text(json.dumps(maps, indent=2), encoding='utf-8')
    tables = [source_rows(root, manifest, 'Data2/Patch/Comm/' + name + '.csvZ', skip)
              for name, skip in (('NewCombatPet_AllInnate', 5), ('NewCombatPet_Innate', 4),
                                 ('NewCombatPet_Category', 5), ('ChangeDollCard', 5))]
    (root / 'useful-source-rows.json').write_text(json.dumps(tables, ensure_ascii=False, indent=2), encoding='utf-8')
    summary = {'rom_files': len(envelopes), 'rom_bytes_fully_accounted': sum(e['bytes_accounted'] for e in envelopes),
               'rom_chunks': dict(chunks), 'rom_payload_bytes': dict(payload),
               'unknown_rom_chunks': sum(len(e['unknown_chunks']) for e in envelopes),
               'rom_action_count_mismatches': sum(len(e['action_count_mismatches']) for e in envelopes),
               'rom_palette_size_counts': dict(Counter(size for e in envelopes for size in e['palette_sizes'])),
               'minimap_bmp_files': len(maps),
               'source_table_rows': {t['source']: len(t['rows']) for t in tables},
               'rtb_files': sum(e['extension'] == '.rtb' for e in manifest),
               'rtb_fully_accounted': sum(e['extension'] == '.rtb' and e.get('structure', {}).get('fully_accounted', False) for e in manifest),
               'claim_boundary': 'Chunk-size accounting covers all ROM bytes; known payloads are not all independently semantically decoded. No wild-stat or spawn authority follows from this scan.'}
    (root / 'content-summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(summary, ensure_ascii=True))


if __name__ == '__main__':
    run(Path(sys.argv[1]).resolve())
