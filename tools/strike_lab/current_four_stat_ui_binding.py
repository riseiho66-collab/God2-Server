"""Current UI labels from original ROM pixels and pinned x86 dataflow.

Read-only static audit, not native execution or a live client render. Labels
are visual transcriptions of decoded asset crops, never inferred from messages.
--images emits PNGs as JSON/base64 on stdout without creating image files.
"""
import argparse
import base64
import csv
import hashlib
import io
import json
from pathlib import Path
import struct

from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_IMM, X86_OP_MEM
from PIL import Image

from .omega_assets import decode_csvz

ROOT = Path(__file__).resolve().parents[2]
CLIENT = ROOT.parent / 'God2'
IMAGE_PATH = ROOT / ('artifacts/capture_work/host-20260918-1430/output/'
                     'native-master-01-stable.bin')
IMAGE_SHA = '149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
CSV_PATH = 'Data2/Patch/FieldComm3.csvZ'
CSV_SHA = '197b0952d33bddb6f3682779208dd396fcecbe451c1b9dc68ec86209ed1a7e05'
CSV_PLAIN_SHA = '2c76b311dfcfba4ceb2b23c0faf5011339365673bd01c8a4ed371fb174fd43ac'
SOURCES = {
    34: ('Data3/Flow/FS2_GUI.romZ',
         '956fbfa857ba578a3d26b8d1973692817e37ea36707a7173cf09282963a360df',
         '6b8cec27e130d3eb488c06aab2bff1a226383d7d03d7ffc6467696fb96529413'),
    29: ('Data3/Flow/God.romZ',
         '8fa680341a565fe84dfcc4e07a856e8d7a3848d5caf8958f51c6f47fe6cbc844',
         '86e767605bfaa7b539a458258c31be7a9cd1199ab67fd19af74e2ded70ad7dd1'),
}
ROLE_LABELS = ('\u7269\u7406\u653b\u64ca', '\u7269\u7406\u9632\u79a6',
               '\u6cd5\u8853\u653b\u64ca', '\u6cd5\u8853\u9632\u79a6')
COMPANION_LABELS = ('\u9ad4\u529b', '\u529b\u91cf', '\u667a\u529b', '\u901f\u5ea6')
RANGES = {
    'role_selection': (0xe66f1, 0xe66fd),
    'role_refresh_argument': (0xe6710, 0xe6719),
    'role_numbers': (0xe6ab0, 0xe6b20),
    'role_panel': (0xe7c80, 0xe7d50),
    'companion_panel': (0xa7d60, 0xa7e0c),
    'companion_selection': (0xa9af0, 0xa9b1c),
    'companion_numbers': (0xa9be1, 0xa9db0),
    'bank_loader': (0x81610, 0x81684),
    'action_selector': (0x1e710, 0x1e777),
    'pool_parser': (0x2a8f3, 0x2a94d),
    'number_update': (0x1077c0, 0x10784a),
    'text_coordinates': (0x2608d, 0x260c3),
    'pcx_span_table': (0x2c239, 0x2c24c),
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def pinned_read(path, expected):
    data = path.read_bytes()
    if sha(data) != expected:
        raise ValueError('Pinned source changed: ' + str(path))
    return data


def decoded_source(path, raw_sha, plain_sha):
    raw = pinned_read(path, raw_sha)
    plain = decode_csvz(raw, limit=2 * 1024 * 1024)
    if sha(plain) != plain_sha:
        raise ValueError('Decoded source changed: ' + str(path))
    return raw, plain


def parse_rom(data, *, name_encoding='ascii'):
    if data[:12] != b'IGSROM02\0\0\0\0':
        raise ValueError('ROM signature')
    palettes, images, actions = [], [], []
    pos, ended = 12, False
    while pos < len(data):
        if pos + 12 > len(data):
            raise ValueError('Truncated chunk header')
        tag, size = struct.unpack_from('<8sI', data, pos)
        end = pos + 12 + size
        if end > len(data):
            raise ValueError('Truncated chunk payload')
        payload = data[pos+12:end]
        chunk = {'offset': pos, 'data': payload, 'tag': tag}
        if tag == b'PALETTE1':
            if size != 512:
                raise ValueError('Palette size')
            palettes.append(chunk)
        elif tag in (b'PCX_RWIF', b'TGA_RWIF'):
            # Both formats increment the native image ordinal.
            images.append(chunk)
        elif tag == b'ACT_DATA':
            if size != 48:
                raise ValueError('Action size')
            meta = struct.unpack_from('<6i', payload)
            actions.append(dict(chunk, meta=meta, steps=[], pools=[],
                                name=payload[24:].split(b'\0', 1)[0].decode(name_encoding)))
        elif tag == b'ACT_STEP':
            if not actions or size % 10:
                raise ValueError('Action step boundary')
            actions[-1]['steps'].append(chunk)
        elif tag == b'ACT_POOL':
            if not actions or size != 10:
                raise ValueError('Action pool boundary')
            actions[-1]['pools'].append(chunk)
        elif tag == b'FILE_END':
            if size or end != len(data):
                raise ValueError('ROM end boundary')
            ended = True
        elif tag not in (b'ACTINDEX', b'ACTBLOCK'):
            raise ValueError('Unexpected ROM chunk: ' + repr(tag))
        pos = end
    if not ended:
        raise ValueError('Missing ROM end')
    for action in actions:
        if (len(action['steps']), len(action['pools'])) != action['meta'][4:6]:
            raise ValueError('Action counts')
    return dict(palettes=palettes, images=images, actions=actions)


def pcx_pixels(data):
    if len(data) < 128 or data[:4] != b'\x0a\x05\x01\x08' or data[65] != 1:
        raise ValueError('Unsupported PCX header')
    x0, y0, x1, y1 = struct.unpack_from('<4H', data, 4)
    width, height = x1-x0+1, y1-y0+1
    stride = struct.unpack_from('<H', data, 66)[0]
    if not (0 < width <= stride <= 1024 and 0 < height <= 1024):
        raise ValueError('PCX dimensions')
    pixels, pos = bytearray(), 128
    for _ in range(height):
        row = bytearray()
        while len(row) < stride:
            if pos >= len(data):
                raise ValueError('Truncated PCX run')
            value, pos = data[pos], pos+1
            count = 1
            if value & 0xc0 == 0xc0:
                count = value & 0x3f
                if not count or pos >= len(data):
                    raise ValueError('Invalid PCX run')
                value, pos = data[pos], pos+1
            if len(row) + count > stride:
                raise ValueError('PCX run crosses row')
            row.extend(bytes([value]) * count)
        pixels.extend(row[:width])
    # PCX_RWIF carries the native 2C239..2C247 per-row span table.
    if len(data)-pos != height*4:
        raise ValueError('PCX_RWIF span table size')
    for left, right in struct.iter_unpack('<2H', data[pos:]):
        if not 0 <= left <= right <= width:
            raise ValueError('PCX_RWIF span boundary')
    return width, height, bytes(pixels)


def select_action(rom, ordinal):
    action = rom['actions'][ordinal]
    steps = action['steps'][0]['data']
    selected = next(steps[i:i+10] for i in range(0, len(steps), 10) if steps[i] == 0)
    pool = action['pools'][selected[3]]
    image_index = struct.unpack_from('<H', pool['data'], 6)[0]
    palette_index = selected[5] & 31
    image_chunk = rom['images'][image_index]
    if image_chunk['tag'] != b'PCX_RWIF':
        raise ValueError('Selected UI image is not PCX')
    width, height, pixels = pcx_pixels(image_chunk['data'])
    palette = rom['palettes'][palette_index]['data']
    result = Image.frombytes('P', (width, height), pixels)
    result.putpalette([channel for value in struct.unpack('<256H', palette)
                       for channel in (((value >> 10) & 31)*255//31,
                                       ((value >> 5) & 31)*255//31, (value & 31)*255//31)])
    return dict(action=ordinal, name=action['name'], action_offset=action['offset'],
                pool_offset=pool['offset'], pool_hex=pool['data'].hex(),
                first_step_hex=selected.hex(), image_index=image_index,
                image_offset=image_chunk['offset'], palette_index=palette_index,
                width=width, height=height, pixels_sha256=sha(pixels),
                palette_sha256=sha(palette)), result


def descriptors(image, start, count):
    result = {}
    for index in range(count):
        offset = start + index * 0x16
        control, sample, x, y = struct.unpack_from('<h16s2h', image, offset)
        if control in result:
            raise ValueError('Duplicate control')
        result[control] = dict(descriptor_rva=offset, control=control, x=x, y=y,
                               sample_hex=sample.split(b'\0', 1)[0].hex())
    return result


def instructions(image, start, end):
    decoder = Cs(CS_ARCH_X86, CS_MODE_32)
    decoder.detail = True
    insns = list(decoder.disasm(image[start:end], start))
    if not insns or insns[-1].address + insns[-1].size != end:
        raise ValueError('Incomplete instruction slice')
    return insns


def number_binding(image, start, end, source_register):
    insns = instructions(image, start, end)
    reads = [i for i in insns if i.mnemonic == 'mov' and len(i.operands) == 2
             and i.operands[1].type == X86_OP_MEM
             and i.reg_name(i.operands[1].mem.base) == source_register]
    pushes = [i.operands[0].imm for i in insns if i.mnemonic == 'push'
              and i.operands[0].type == X86_OP_IMM]
    call = insns[-1]
    if len(reads) != 1 or len(pushes) != 2 or pushes[0] != 0x5823b4:
        raise ValueError('Unexpected numeric argument pattern')
    if call.mnemonic != 'call' or call.operands[0].imm != 0x1077c0:
        raise ValueError('Unexpected number formatter')
    return dict(field_offset=reads[0].operands[1].mem.disp,
                field_width=reads[0].operands[1].size, read_rva=reads[0].address,
                call_rva=call.address, control=pushes[1])


def audit():
    image = pinned_read(IMAGE_PATH, IMAGE_SHA)
    if image[0x1823b4:0x1823b7] != b'%d\0':
        raise ValueError('Numeric format literal')
    _, plain = decoded_source(CLIENT / CSV_PATH, CSV_SHA, CSV_PLAIN_SHA)
    rows = list(csv.reader(io.StringIO(plain.decode('latin1'))))[4:]
    if len(rows) != 65 or [int(r[0]) for r in rows] != list(range(65)):
        raise ValueError('FieldComm3 indices')
    roms, source_info = {}, []
    for slot, (path, raw_sha, plain_sha) in SOURCES.items():
        if rows[slot][1].lstrip('\\').replace('\\', '/') + 'Z' != path:
            raise ValueError('CSV path binding')
        raw, decoded = decoded_source(CLIENT / path, raw_sha, plain_sha)
        roms[slot] = parse_rom(decoded)
        source_info.append(dict(slot=slot, csv_line=slot+5, path=path,
                                raw_size=len(raw), decoded_size=len(decoded),
                                raw_sha256=raw_sha, decoded_sha256=plain_sha))
    panels, images = {}, {}
    for key, slot, action in (('role', 34, 0x26), ('role_muye', 34, 0x43),
                              ('companion', 29, 0)):
        panels[key], images[key] = select_action(roms[slot], action)
        panels[key]['slot'] = slot
    role_desc = descriptors(image, 0x196db8, 32)
    companion_desc = descriptors(image, 0x191ea8, 16)
    companion_origin = struct.unpack_from('<2i', image, 0x191e60)
    bindings = []
    for family, starts, desc, labels, source_register in (
            ('role', ((0xe6acc, 0xe6ae8), (0xe6ab0, 0xe6acc),
                      (0xe6b04, 0xe6b20), (0xe6ae8, 0xe6b04)),
             role_desc, ROLE_LABELS, 'ebx'),
            ('companion', ((0xa9d40, 0xa9d5c), (0xa9d5c, 0xa9d78),
                           (0xa9d78, 0xa9d94), (0xa9d94, 0xa9db0)),
             companion_desc, COMPANION_LABELS, 'edi')):
        for index, ((start, end), label) in enumerate(zip(starts, labels)):
            binding = number_binding(image, start, end, source_register)
            entry = desc[binding['control']]
            x, y = entry['x'], entry['y']
            if family == 'companion':
                x, y = x-companion_origin[0], y-companion_origin[1]
            box = ((120, 210 + index*25, 190, 234 + index*25) if family == 'role'
                   else (20, 161 + index*20, 70, 180 + index*20))
            crop = images[family].crop(box)
            binding.update(family=family, label=label, label_basis='visual asset transcription',
                           descriptor_rva=entry['descriptor_rva'],
                           descriptor_xy=[entry['x'], entry['y']], local_xy=[x, y],
                           label_crop_box=box, label_index_pixels_sha256=sha(crop.tobytes()))
            bindings.append(binding)
    slices = {}
    for key, (start, end) in RANGES.items():
        slices[key] = dict(start=start, end=end, sha256=sha(image[start:end]),
                           disassembly=['%06X %s %s' % (i.address, i.mnemonic, i.op_str)
                                        for i in instructions(image, start, end)])
    return dict(image_sha256=IMAGE_SHA, csv_sha256=CSV_SHA,
                csv_decoded_sha256=CSV_PLAIN_SHA, sources=source_info, panels=panels,
                bindings=bindings, slices=slices, native_executed=False,
                live_render=False, authoritative_monster_values_recovered=0), images, roms


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--images', action='store_true', help='JSON/base64 PNGs to stdout')
    parser.add_argument('--disassembly', action='store_true', help='Include audited x86 slices')
    args = parser.parse_args()
    report, images, _ = audit()
    if args.images:
        output = []
        for name, image in images.items():
            # Nearest-neighbor enlargement preserves the original label pixels.
            crop = (0, 110, image.width, 245) if name == 'companion' else (0, 115, image.width, 310)
            preview = image.crop(crop).convert('RGB')
            preview = preview.resize((preview.width*3, preview.height*3), Image.Resampling.NEAREST)
            buffer = io.BytesIO()
            preview.save(buffer, format='PNG')
            output.append(dict(name=name, original_crop=crop, panel=report['panels'][name],
                               png_base64=base64.b64encode(buffer.getvalue()).decode('ascii')))
        print(json.dumps(output))
    else:
        if not args.disassembly:
            for value in report['slices'].values():
                del value['disassembly']
        print(json.dumps(report, ensure_ascii=True, indent=2))


if __name__ == '__main__':
    main()
