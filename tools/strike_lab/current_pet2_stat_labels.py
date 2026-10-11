"""Bind original pet2 ROM labels to FB numeric controls, not wild values."""
import csv
import io
import json
import struct

from .current_four_stat_ui_binding import (
    CLIENT, CSV_PATH, CSV_SHA, CSV_PLAIN_SHA, IMAGE_PATH, IMAGE_SHA,
    decoded_source, pinned_read, parse_rom, select_action, descriptors,
    instructions, sha, X86_OP_MEM, X86_OP_IMM)

ASSET = 'Data3/Flow/petegg.romZ'
RAW_SHA = 'b5b8e903bc3c95b8f3205a51f5c59125396c99ef346eb084ae26cae91ef37d37'
PLAIN_SHA = 'd608021aa5d731ea43526c6ce6643a78e8c786bd08d10fa3462a11e9b0e583e8'
# Labels transcribed from the original decoded background, not placeholder text.
FIELDS = (
    ('physical_attack', '\u7269\u653b', 0x10, 8, 0xa4321, 0xa4343, 85, 143),
    ('physical_defense', '\u7269\u9632', 0x12, 9, 0xa4348, 0xa436d, 85, 163),
    ('magical_attack', '\u9b54\u653b', 0x14, 10, 0xa4372, 0xa4394, 188, 143),
    ('magical_defense', '\u9b54\u9632', 0x16, 11, 0xa4399, 0xa43bb, 188, 163),
    ('strength', '\u529b', 0x24, 13, 0xa43c0, 0xa43e2, 45, 216),
    ('constitution', '\u9ad4', 0x26, 12, 0xa43e7, 0xa440c, 45, 197),
    ('intelligence', '\u667a', 0x28, 14, 0xa4411, 0xa4433, 45, 235),
    ('speed', '\u901f', 0x2a, 15, 0xa4438, 0xa445a, 45, 254),
    ('metal', '\u91d1', 0x18, 20, 0xa445f, 0xa4481, 200, 197),
    ('wood', '\u6728', 0x1a, 21, 0xa4486, 0xa44ab, 200, 216),
    ('water', '\u6c34', 0x1c, 22, 0xa44b0, 0xa44d2, 200, 235),
    ('fire', '\u706b', 0x1e, 23, 0xa44d7, 0xa44f9, 200, 254),
    ('earth', '\u571f', 0x20, 24, 0xa44fe, 0xa4520, 200, 273),
)
PACKED_FIELDS = (
    ('current_hp', 'HP', 4, 4, 0, 0x3fff, 1, 0xa41d7, 0xa41fc, 65, 74),
    ('current_mp', 'MP', 4, 4, 14, 0x7ff, 2, 0xa4201, 0xa4229, 65, 94),
    ('maximum_hp', 'HP', 12, 4, 0, 0x3fff, 3, 0xa422e, 0xa4253, 95, 74),
    ('maximum_mp', 'MP', 12, 4, 14, 0x7ff, 4, 0xa4258, 0xa4283, 95, 94),
    ('level', '等級', 3, 1, 0, 0xff, 5, 0xa4288, 0xa42a9, 118, 46),
    ('star_rank', '星階', 8, 4, 28, 0xf, 17, 0xa45c7, 0xa45e9, 122, 216),
    ('star_rating', '星等', 8, 4, 24, 0xf, 18, 0xa45ee, 0xa4613, 122, 235),
)


def audit():
    image = pinned_read(IMAGE_PATH, IMAGE_SHA)
    _, csv_data = decoded_source(CLIENT / CSV_PATH, CSV_SHA, CSV_PLAIN_SHA)
    rows = list(csv.reader(io.StringIO(csv_data.decode('latin1'))))[4:]
    if int(rows[36][0]) != 36 or rows[36][1].lstrip('\\').replace('\\', '/').lower() != ASSET[:-1].lower():
        raise ValueError('Pet2 bank path changed')
    _, data = decoded_source(CLIENT / ASSET, RAW_SHA, PLAIN_SHA)
    panel, pixels = select_action(parse_rom(data), 75)
    if panel['name'] != 'FPet2_BGOpen' or pixels.size != (252, 427):
        raise ValueError('Pet2 background changed')
    if struct.unpack_from('<4i', image, 0x1913c0) != (0, 0, 252, 427):
        raise ValueError('Panel origin/dimensions changed')
    constructor = instructions(image, 0xa3b20, 0xa3b4e)
    pushes = [i.operands[0].imm for i in constructor if i.mnemonic == 'push' and i.operands[0].type == X86_OP_IMM]
    if pushes != [-1, -1, 0x5913d0, 0x36b0, 0x5913c0, 76, 75, 36]:
        raise ValueError('Pet2 panel resource arguments changed')
    controls = descriptors(image, 0x1913e0, 28)
    if image[0x18e8bc:0x18e8c0] != b'%3d\0':
        raise ValueError('Pet2 number format changed')
    if image[0x19015c:0x190160] != b'%4d\0':
        raise ValueError('Pet2 attribute format changed')
    result = []
    for name, label, offset, control, start, call, x, y in FIELDS:
        code = instructions(image, start, call + 5)
        reads = [i for i in code if i.mnemonic == 'mov' and len(i.operands) == 2
                 and i.operands[1].type == X86_OP_MEM
                 and i.reg_name(i.operands[1].mem.base) == 'ebx']
        pushes = [i.operands[0].imm for i in code if i.mnemonic == 'push' and i.operands[0].type == X86_OP_IMM]
        if (len(reads) != 1 or reads[0].operands[1].mem.disp != offset
                or reads[0].operands[1].size != 2
                or pushes != [0x58e8bc if control in (8, 9, 10, 11) else 0x59015c, control]
                or code[-1].mnemonic != 'call' or code[-1].operands[0].imm != 0x1077c0
                or (controls[control]['x'], controls[control]['y']) != (x, y)):
            raise ValueError('Pet2 field binding changed: ' + name)
        result.append(dict(name=name, visible_label=label, body_offset=offset,
                           logical_offset=offset+1, width=2, control=controls[control],
                           consumer_start_rva=start, consumer_call_rva=call,
                           code_sha256=sha(image[start:call+5])))
    packed = []
    for name, label, offset, width, shift, mask, control, start, call, x, y in PACKED_FIELDS:
        code = instructions(image, start, call + 5)
        reads = [i for i in code if i.mnemonic == 'mov' and len(i.operands) == 2
                 and i.operands[1].type == X86_OP_MEM
                 and i.reg_name(i.operands[1].mem.base) == 'ebx']
        shifts = [i.operands[1].imm for i in code if i.mnemonic == 'shr']
        masks = [i.operands[1].imm for i in code if i.mnemonic == 'and']
        # Byte read and top nibble naturally zero-extend; other fields mask.
        if (len(reads) != 1 or reads[0].operands[1].mem.disp != offset
                or reads[0].operands[1].size != width
                or shifts != ([shift] if shift else [])
                or masks != ([] if name in ('level', 'star_rank') else [mask])
                or (controls[control]['x'], controls[control]['y']) != (x, y)
                or code[-1].mnemonic != 'call' or code[-1].operands[0].imm != 0x1077c0):
            raise ValueError('Pet2 packed binding changed: ' + name)
        pushes = [i.operands[0].imm for i in code if i.mnemonic == 'push'
                  and i.operands[0].type == X86_OP_IMM]
        if len(pushes) != 2 or pushes[1] != control:
            raise ValueError('Pet2 packed control changed: ' + name)
        packed.append(dict(name=name, visible_label=label, body_offset=offset,
                           logical_offset=offset+1, width=width, shift=shift, mask=mask,
                           control=controls[control], consumer_start_rva=start,
                           consumer_call_rva=call, code_sha256=sha(image[start:call+5])))
    return dict(image_sha256=IMAGE_SHA, asset=ASSET, asset_sha256=RAW_SHA,
                decoded_sha256=PLAIN_SHA, panel=panel, bank=36, opcode=0xfb,
                logical_size=73, fields=result, packed_fields=packed, field_names_verified=True,
                verification='static code plus visually inspected original ROM',
                values_source='received FB body, not ROM placeholder numerals',
                wildmonsterjoin_proven=False, original_wild_values_recovered=0,
                combat_formula_verified=False, growth_type_mapping_verified=False,
                level_cap_verified=False, database_promotions=0)


if __name__ == '__main__':
    print(json.dumps(audit(), ensure_ascii=True, indent=2))
