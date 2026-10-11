"""Current-client progression consumers; no inferred server progression rules."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

from .omega_assets import decode_csvz
from .recover_companions import parse_sections

REPO = Path(__file__).resolve().parents[2]
IMAGE = REPO / 'artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin'
IMAGE_SHA256 = '149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
SOURCES = {
    'Data2/Patch/Comm/gamedata.csvZ': '70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731',
    'Data2/Patch/Comm/message.csvZ': '5cd34cce66feae96d947cd45e32984765ce625673c0fb19c73cb63d7d9178598',
}
SPANS = {
    'godlevel_category_dispatch': (0x5668c, 0x566d7),
    'godlevel_loader': (0x5a880, 0x5a8ed),
    'source_text_field_reader': (0x51ae0, 0x51b2c),
    'source_integer_field_reader': (0x51b30, 0x51b43),
    'source_field_and_decimal_conversion': (0x51b60, 0x51bdc),
    'godlevel_text_consumer': (0xaa360, 0xaa3f0),
    's2c2b_companion_consumer': (0xaa3f0, 0xaa476),
    'companion_percent': (0xaa480, 0xaa553),
    's2c2b_role_consumer_and_refresh': (0xe6390, 0xe640f),
    's2c2c_stat_stores': (0xe6600, 0xe6701),
    'stat_modifier_display': (0xe6e61, 0xe6f19),
    's2c24_health_adjustment': (0xe71e0, 0xe72d0),
    'health_clamp_and_display': (0xac070, 0xac1a9),
    'role_exp_bar_conversion': (0xac2c0, 0xac358),
    'float_to_integer': (0x149630, 0x149657),
    's2c2b_and_2c_dispatch': (0x69eb0, 0x69ef0),
    's2c24_and_9f_dispatch': (0x69f4d, 0x69f85),
}
# (body offset, actor offset, width): the four WORDs are sign-extended only
# by the subsequent display reader, not while stored by this packet consumer.
STAT_STORES = (
    (0, 0x88, 2), (4, 0x8a, 2), (8, 0x8c, 2), (12, 0x8e, 2),
    (16, 0xa4, 4), (20, 0xa8, 4), (24, 0xac, 4), (28, 0xb0, 4),
    (32, 0xb4, 4), (36, 0xb8, 2), (40, 0xba, 2),
    (44, 0x98, 4), (48, 0x94, 4), (52, 0xa0, 4), (56, 0x9c, 4),
)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def pinned(path, expected):
    data = Path(path).read_bytes()
    if sha(data) != expected:
        raise ValueError('Source SHA-256 mismatch: ' + str(path))
    return data


def evidence(client_root, image_path=IMAGE):
    image = pinned(image_path, IMAGE_SHA256)
    sources, decoded = {}, {}
    for relative, expected in SOURCES.items():
        raw = pinned(Path(client_root) / relative, expected)
        decoded[relative] = decode_csvz(raw)
        sources[relative] = {'sha256': sha(raw), 'decoded_sha256': sha(decoded[relative])}
    game, messages = (decoded[path] for path in SOURCES)
    table = parse_sections(game, ('GodLevel',))['GodLevel']
    message_table = parse_sections(messages, ('ProgramMsg',))['ProgramMsg']
    selected = [r for r in message_table['records']
                if r['fields_hex'][0] in {str(n).encode().hex() for n in (163, 164, 165)}]
    packets = {}
    for opcode in (0x24, 0x2b, 0x2c, 0x9f):
        length_rva = struct.unpack_from('<I', image, 0x1324 + opcode * 4)[0] - 0x400000
        if image[length_rva] != 0xb8 or image[length_rva + 5] != 0xc3:
            raise ValueError('Unexpected fixed packet length function')
        packets[f'{opcode:02X}'] = {
            'dispatch_rva': struct.unpack_from('<I', image, 0x6b5d4 + opcode * 4)[0] - 0x400000,
            'length_rva': length_rva,
            'logical_length_including_opcode': struct.unpack_from('<I', image, length_rva + 1)[0],
        }
    return {
        'schema': 'current-role-progression-consumers-v1',
        'image_sha256': sha(image), 'sources': sources,
        'address_layout': 'RVA = mapped file offset; VA = 0x400000 + RVA',
        'spans': {name: {'rva': start, 'end_rva_exclusive': end,
                         'raw_hex': image[start:end].hex(), 'sha256': sha(image[start:end])}
                  for name, (start, end) in SPANS.items()},
        'packets': packets,
        'source_schema': {
            'GodLevel': {'source': next(iter(SOURCES)), 'table': table,
                         'dispatch_call_rva': 0x566cd, 'loader_rva': 0x5a880,
                         'count_offset': 0xd2ac8, 'count_storage_width': 1,
                         'field_0': 'NUL-terminated text copied into slot',
                         'field_1': 'decimal slot ID; positive IDs decremented',
                         'slot_offset': 0xd2aca, 'slot_stride': 94,
                         'consumer_rva': 0xaa360, 'destination': '[actor+0xd0]+0x13',
                         'packet_index': 'unsigned byte, zero-based; compared <= signed count byte',
                         'meaning': 'companion category text, not role XP thresholds'},
            'ProgramMsg': {'source': list(SOURCES)[1], 'records': selected,
                           'native_reads': {'163': 0xac132, '164': 0xac16c, '165': 0xaa4c7}},
        },
        'new_state_flows': {
            '2C': {'consumer_rva': 0xe6600, 'stores': STAT_STORES,
                   'modifier_display_rva': 0xe6e61,
                   'meaning': 'server-supplied base-stat modifiers and additional state; no level delta calculation'},
            '2B_companion': {'consumer_rva': 0xaa3f0,
                             'stores': [(4, 0x2c, 4), (12, 0x34, 2), (18, 0x28, 2)],
                             'object': '[actor+0xd0]', 'null_object': 'no stores',
                             'body_bytes_14_15': 'unused in the two inspected 2B consumers'},
            '24': {'consumer_rva': 0xe71e0,
                   'stores': [(0, 0x5c, 4), (4, 0x64, 4), (8, 0x60, 4), (12, 0x68, 4)],
                   'derived_state': 'on role HP decrease, subtract decrease from companion+0x2c with floor zero',
                   'qualification': 'opcode 24 passes mode 0; 9F first calls 0x1037d0, not covered'},
            'health_clamp': {'consumer_rva': 0xac070,
                             'operation': 'unsigned clamp actor+0x5c to +0x60 and +0x64 to +0x68',
                             'guards': 'both maxima nonzero and signed UI WORD +0x232e50 >= 0',
                             'meaning': 'client mutates current HP/MP; does not derive maxima from level'},
            'exp_conversion': {'consumer_rva': 0xac2c0, 'helper_rva': 0x149630,
                               'input': 'unsigned actor WORD +0x58',
                               'operation': 'multiply pinned float32 0.01, round to float32, truncate to integer',
                               'output': 'EAX pushed to UI control 4; actor EXP and level not written',
                               'qualification': 'bar conversion only; not total EXP to level'},
        },
        'open_original_rules': {key: {'status': 'open', 'value': None} for key in (
            'single_level_xp_thresholds', 'cumulative_xp_thresholds', 'level_transition',
            'level_cap', 'hp_mp_growth', 'base_attribute_growth', 'attribute_point_budget')},
        'runtime_verified': False, 'runtime_eligible': False,
        'qualification': 'Original client instructions tested offline with synthetic operands, not original server samples.',
    }


class NativeProbe:
    """Unmodified mapped instructions with explicit allowed ranges and hard limits."""
    BASE, STACK, BODY, ACTOR, UI, BANK, COMPANION = (
        0x400000, 0x3001000, 0x3100000, 0x3200000, 0x4000000, 0x5000000, 0x5200000)

    def __init__(self, image_path=IMAGE):
        sys.path.insert(0, str(REPO / 'artifacts/tooling/crypto-oracle-python'))
        from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_PROT_READ, UC_PROT_EXEC
        from unicorn.x86_const import UC_X86_REG_ESP, UC_X86_REG_ECX
        raw = pinned(image_path, IMAGE_SHA256)
        self.vm = Uc(UC_ARCH_X86, UC_MODE_32)
        self.vm.mem_map(self.BASE, (len(raw) + 4095) & ~4095, UC_PROT_READ | UC_PROT_EXEC)
        self.vm.mem_write(self.BASE, raw)
        for address, size in ((0x3000000, 0x4000), (self.BODY, 0x1000),
                              (self.ACTOR, 0x5000), (self.UI, 0x234000),
                              (self.BANK, 0xd4000), (self.COMPANION, 0x1000)):
            self.vm.mem_map(address, size)
        self.vm.mem_write(self.UI + 0x86888, struct.pack('<I', self.ACTOR))
        self.vm.mem_write(self.UI + 0xcff70, struct.pack('<I', self.BANK))
        self.vm.reg_write(UC_X86_REG_ESP, self.STACK)
        self.vm.reg_write(UC_X86_REG_ECX, self.UI)

    def run(self, start, stop, allowed=(), count=2000):
        if not 1 <= count <= 2000:
            raise ValueError('Instruction bound must be between 1 and 2000')
        from unicorn import UC_HOOK_CODE, UC_HOOK_MEM_READ, UC_HOOK_MEM_WRITE
        from unicorn.x86_const import UC_X86_REG_EIP
        spans = allowed or ((start, stop),)
        visited, reads, writes, escaped = [], [], [], []

        def code(vm, address, size, _):
            rva = address - self.BASE
            visited.append(rva)
            if not any(a <= rva and rva + size <= b for a, b in spans):
                escaped.append(rva)
                vm.emu_stop()

        hooks = [self.vm.hook_add(UC_HOOK_CODE, code),
                 self.vm.hook_add(UC_HOOK_MEM_READ,
                     lambda vm, access, address, size, value, data: reads.append((address, size))),
                 self.vm.hook_add(UC_HOOK_MEM_WRITE,
                     lambda vm, access, address, size, value, data: writes.append((address, size)))]
        try:
            self.vm.emu_start(self.BASE + start, self.BASE + stop, timeout=1000000, count=count)
        finally:
            for hook in hooks:
                self.vm.hook_del(hook)
        if escaped or self.vm.reg_read(UC_X86_REG_EIP) != self.BASE + stop:
            raise AssertionError(f'Native slice escaped or exhausted its bound: {escaped}')
        return {'visited': visited, 'reads': reads, 'writes': writes}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--client-root', type=Path, required=True)
    parser.add_argument('--native-image', type=Path, default=IMAGE)
    args = parser.parse_args()
    print(json.dumps(evidence(args.client_root, args.native_image), sort_keys=True, indent=2))


if __name__ == '__main__':
    main()
