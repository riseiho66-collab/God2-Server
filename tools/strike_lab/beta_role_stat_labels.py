"""Native beta opcode 29 -> status controls, with original asset labels.

Synthetic input proves field semantics, never original monster values.
Only UI formatting/color calls are replaced; packet writer and refresh execute.
"""
import hashlib
import csv
import io
import json
import struct
from pathlib import Path

from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn import x86_const as reg
from .beta_packet_probe import ROOT, IMAGE, SHA
from .current_four_stat_ui_binding import parse_rom, select_action, descriptors
from .omega_assets import decode_csvz

CLIENT = Path('C:/Users/risei/Desktop/god2-test')
# Names are transcribed from the decoded Status_BGOpen image, not guessed.
FIELDS = (
    (0, 0x88, 18, 'constitution_modifier', 102, 130),
    (1, 0x8a, 19, 'strength_modifier', 102, 150),
    (2, 0x8c, 20, 'intelligence_modifier', 102, 170),
    (3, 0x8e, 21, 'speed_modifier', 102, 190),
    (4, 0x9c, 25, 'metal', 44, 216),
    (5, 0xa0, 26, 'wood', 44, 235),
    (6, 0xa4, 27, 'water', 44, 254),
    (7, 0xa8, 28, 'fire', 44, 273),
    (8, 0xac, 29, 'earth', 44, 292),
    (11, 0x94, 24, 'physical_defense', 194, 242),
    (12, 0x92, 23, 'physical_attack', 194, 217),
    (13, 0x98, 31, 'magic_defense', 194, 292),
    (14, 0x96, 30, 'magic_attack', 194, 267),
)


def audit():
    image = IMAGE.read_bytes()
    assert hashlib.sha256(image).hexdigest() == SHA
    assert image[0xa9068:0xa906e] == bytes.fromhex('6a276a266a22')
    table_raw = (CLIENT / 'Data2/Patch/FieldComm3.csvZ').read_bytes()
    assert hashlib.sha256(table_raw).hexdigest() == '881aa300c6c7bf57ed42410a348dbc098e8e55e835d6a3fefc50a4595b71cbb1'
    table = decode_csvz(table_raw)
    rows = list(csv.reader(io.StringIO(table.decode('cp950', errors='replace'))))
    assert any(row[:3] == ['34', '\\Data3\\Flow\\FS2_GUI.rom', 'ROM_FS2_GUI'] for row in rows)
    controls = descriptors(image, 0x150120, 32)
    asset = CLIENT / 'Data3/Flow/FS2_GUI.romZ'
    raw = asset.read_bytes()
    plain = decode_csvz(raw)
    panel, _ = select_action(parse_rom(plain), 38)
    assert panel['pixels_sha256'] == 'c100cbb9401a8336f2c18237aa4cc24d251287aa31235f64c581164bbcb4b234'
    for _, _, control, _, x, y in FIELDS:
        assert (controls[control]['x'], controls[control]['y']) == (x, y)
    base, owner, role, packet, stack = 0x400000, 0x3000000, 0x3200000, 0x3300000, 0x3400000
    vm = Uc(UC_ARCH_X86, UC_MODE_32)
    vm.mem_map(base, (len(image) + 4095) & ~4095)
    vm.mem_write(base, image)
    for addr, size in ((owner, 0x200000), (role, 4096), (packet, 4096), (stack, 65536)):
        vm.mem_map(addr, size)
    vm.mem_write(owner + 0x76bd0, struct.pack('<I', role))
    vm.mem_write(owner + 0x120632, struct.pack('<h', 1))
    formatted = {}

    def hook(uc, address, size, unused):
        rva = address - base
        if rva in (0xe1a30, 0xe1ac0):
            sp = uc.reg_read(reg.UC_X86_REG_ESP)
            ret = int.from_bytes(uc.mem_read(sp, 4), 'little')
            if rva == 0xe1a30:
                ui, handle, control, fmt, value = struct.unpack('<5I', uc.mem_read(sp + 4, 20))
                assert ui == owner + 0xc0b14 and handle & 0xffff == 1
                formatted[control] = {'value': value, 'format_va': hex(fmt)}
            uc.reg_write(reg.UC_X86_REG_ESP, sp + (16 if rva == 0xe1ac0 else 4))
            uc.reg_write(reg.UC_X86_REG_EIP, ret)
        elif not (0xa7b00 <= rva < 0xa7c18 or 0xa7c20 <= rva < 0xa805d):
            raise AssertionError(f'Unexpected native path {rva:x}')

    vm.hook_add(UC_HOOK_CODE, hook)
    cases = []
    for value in (1, 32767, 32768, 65535):
        values = [value] * 15
        values[9:11] = [0, 0]
        formatted.clear()
        vm.mem_write(role, bytes(4096))
        vm.mem_write(packet, b'\x29' + struct.pack('<15H', *values))
        vm.mem_write(stack + 0x8000, struct.pack('<II', stack + 0xff00, packet + 1))
        vm.reg_write(reg.UC_X86_REG_ESP, stack + 0x8000)
        vm.reg_write(reg.UC_X86_REG_ECX, owner)
        vm.emu_start(base + 0xa7b00, stack + 0xff00, count=10000)
        assert vm.reg_read(reg.UC_X86_REG_EIP) == stack + 0xff00
        for index, _, control, _, _, _ in FIELDS:
            expected = value if index >= 4 or value < 32768 else value | 0xffff0000
            assert formatted[control]['value'] == expected
        cases.append({'input_word': value, 'controls': dict(formatted)})
    return {'image_sha256': SHA, 'asset': str(asset),
            'bank_table_sha256': hashlib.sha256(table_raw).hexdigest(),
            'asset_sha256': hashlib.sha256(raw).hexdigest(),
            'decoded_sha256': hashlib.sha256(plain).hexdigest(), 'panel': panel,
            'fields': [{'body_offset': hex(i * 2), 'logical_offset': hex(1 + i * 2),
                        'role_offset': hex(off), 'control': c, 'name': name,
                        'coordinates': [x, y]} for i, off, c, name, x, y in FIELDS],
            'native_cases': cases,
            'scope': 'Original role status writer and refresh, mocked UI sinks. '
                     'Four attribute fields are signed modifiers, not base attributes. '
                     'Words 9/10 are display masks. No monster dataset or damage formula recovered.'}


if __name__ == '__main__':
    report = audit()
    path = ROOT / 'artifacts/research/beta-unpack-20260920/role-stat-labels.json'
    path.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'fields': len(report['fields']), 'cases': len(report['native_cases']), 'report': str(path)}))
