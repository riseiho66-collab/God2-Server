"""Current S2C31 packed scalar -> percent arguments -> bounded bar geometry.

Research only: synthetic packets, unchanged native instructions, no callee
stubs, socket, renderer, progression table or server formula. Prints JSON only.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

from .omega_assets import decode_csvz

ROOT = Path(__file__).resolve().parents[2]
IMAGE = ROOT / 'artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin'
IMAGE_SHA = '149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
MESSAGE_PATH = 'Data2/Patch/Comm/message.csvZ'
MESSAGE_SHA = '5cd34cce66feae96d947cd45e32984765ce625673c0fb19c73cb63d7d9178598'
DECODED_SHA = '370bd6ed9b4892f57190fc7a8dab14061b3e844b0aa9d0171611a9cbab61b5f8'
BASE = 0x400000
EXECUTED = {
    'logical_opcode_and_length': (0x13497, 0x134ee),
    'length_wrapper': (0x15840, 0x15850),
    'length_opcode_mask': (0x1000, 0x1013),
    'length_dispatch': (0x1200, 0x1216),
    'length_function': (0x12fa, 0x1300),
    'logical_buffer_fill': (0x13558, 0x13592),
    'logical_buffer_short_input': (0x135af, 0x135be),
    'queue_byte_reader': (0x12520, 0x12554),
    'queue_empty': (0x10b50, 0x10b70),
    'queue_copy': (0x10af0, 0x10b4a),
    'length_value': (0x12fa, 0x12ff),
    'primary_opcode_dispatch': (0x68b4c, 0x68b68),
    'packet_dispatch': (0x69fa9, 0x69fbb),
    'packet_scalar_writer': (0xaa200, 0xaa2af),
    'packet_no_match_return': (0xaa2db, 0xaa2e1),
    'row_percent_argument': (0xa9b92, 0xa9ba1),
    'percent_conversion': (0xaa480, 0xaa4c2),
    'truncate_helper': (0x149630, 0x149657),
    'percent_format_arguments': (0xaa4c7, 0xaa508),
    'horizontal_bar_geometry': (0x10618a, 0x106202),
}
STATIC = {
    'frame_decode_into_queue': (0x10ab0, 0x10ae4),
    'frame_decrypt_validate_and_unpack': (0x10a10, 0x10a8d),
    'primary_buffer_acquisition': (0x68b1c, 0x68b68),
    'buffer_pointer_return': (0x13650, 0x13667),
    'length_table_entry': (0x13e8, 0x13ec),
    'dispatch_table_entry': (0x6b698, 0x6b69c),
    'selection_refresh_boundary': (0xaa2af, 0xaa2db),
    'bar_resource_guards_and_query': (0x1060f0, 0x10618a),
    'float_percent_multiplier': (0x171204, 0x171208),
    'float_bar_multiplier': (0x171328, 0x17132c),
    'bar_zero_and_one': (0x1709d0, 0x1709d8),
}
OPEN_RULES = ('single_level_xp_requirements', 'cumulative_xp_requirements',
              'level_transition', 'level_cap', 'hp_mp_growth',
              'base_attribute_growth', 'attribute_point_budget',
              'server_packed_scalar_construction', 'high_bit_gameplay_meaning')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def pinned(path, expected):
    data = Path(path).read_bytes()
    if digest(data) != expected:
        raise ValueError('Unqualified current source: ' + str(path))
    return data


def message_source(client_root):
    raw = pinned(Path(client_root) / MESSAGE_PATH, MESSAGE_SHA)
    decoded = decode_csvz(raw)
    if digest(decoded) != DECODED_SHA:
        raise ValueError('Unqualified decoded message source')
    # Exact current ProgramMsg 165 record, with its original bytes and offset.
    row = decoded[90275:90275 + len(b'165,%6.2f\xa2H\r\n')]
    if row != b'165,%6.2f\xa2H\r\n':
        raise AssertionError('Current ProgramMsg 165 record changed')
    return {'path': MESSAGE_PATH, 'sha256': digest(raw),
            'decoded_sha256': digest(decoded), 'line': 2191,
            'decoded_offset': 90275, 'raw_hex': row.hex(),
            'format_hex': b'%6.2f\xa2H'.hex()}


class NativeSource:
    STACK, SP = 0x3000000, 0x3002000
    UI, ACTOR, BANK = 0x3100000, 0x3400000, 0x3500000
    PACKET_PAGE, PACKET = 0x3700000, 0x3701000 - 29
    CONNECTION = 0x3800000
    ROW = ACTOR + 0xd8
    FORMAT = BANK + 0xb3800

    def __init__(self, image, format_bytes):
        if digest(image) != IMAGE_SHA or format_bytes != b'%6.2f\xa2H':
            raise ValueError('Unqualified native inputs')
        sys.path.insert(0, str(ROOT / 'artifacts/tooling/crypto-oracle-python'))
        import unicorn as uc
        from unicorn import x86_const as x86
        self.uc, self.x86 = uc, x86
        self.vm = uc.Uc(uc.UC_ARCH_X86, uc.UC_MODE_32)
        self.vm.mem_map(BASE, (len(image) + 4095) & ~4095,
                        uc.UC_PROT_READ | uc.UC_PROT_EXEC)
        self.vm.mem_write(BASE, image)
        for address, size in ((self.STACK, 0x4000), (self.UI, 0x234000),
                              (self.ACTOR, 0x1000), (self.BANK, 0xb4000),
                              (self.CONNECTION, 0x4000),
                              (self.PACKET_PAGE, 0x1000)):
            self.vm.mem_map(address, size, uc.UC_PROT_READ | uc.UC_PROT_WRITE)
        self.write32(self.UI + 0x86888, self.ACTOR)
        self.write32(self.UI + 0xcff70, self.BANK)
        self.vm.mem_write(self.UI + 0x232ddc, struct.pack('<H', 7))
        self.vm.mem_write(self.BANK + 0xb2c6c, struct.pack('<H', 165))
        self.write32(self.BANK + 0xb2c68, self.BANK + 0xb3000)
        self.write32(self.BANK + 0xb3000 + 0x290, self.FORMAT)
        self.vm.mem_write(self.FORMAT, format_bytes + b'\0')
        self.vm.mem_protect(self.BANK, 0xb4000, uc.UC_PROT_READ)
        self.vm.mem_protect(self.UI, 0x234000, uc.UC_PROT_READ)
        self.vm.mem_protect(self.PACKET_PAGE, 0x1000, uc.UC_PROT_READ)

    def reg(self, name, value=None):
        register = getattr(self.x86, 'UC_X86_REG_' + name)
        if value is None:
            return self.vm.reg_read(register)
        self.vm.reg_write(register, value)

    def write32(self, address, value):
        self.vm.mem_write(address, struct.pack('<I', value & 0xffffffff))

    def u32(self, address):
        return struct.unpack('<I', self.vm.mem_read(address, 4))[0]

    def prepare(self):
        self.vm.mem_write(self.SP - 0x400, b'\xa5' * 0x800)
        for name in ('EAX', 'EBX', 'ECX', 'EDX', 'ESI', 'EDI', 'EBP'):
            self.reg(name, 0xa5a5a5a5)
        self.reg('ESP', self.SP)
        self.reg('EFLAGS', 2)
        self.reg('FPCW', 0x37f)
        self.reg('FPSW', 0)
        self.reg('FPTAG', 0xffff)

    def run(self, start, stops, ranges, writable=(), count=2048):
        if type(count) is not int or not 1 <= count <= 4096:
            raise ValueError('Instruction bound must be 1..4096')
        trace = {'pcs': [], 'reads': [], 'writes': []}

        def code(vm, address, size, _):
            pc = address - BASE
            if pc in stops:
                vm.emu_stop()
                return
            if not any(a <= pc and pc + size <= z for a, z in ranges):
                raise AssertionError(f'Unallowed native PC {pc:x}')
            trace['pcs'].append(pc)

        def memory(vm, access, address, size, value, _):
            pc = self.reg('EIP') - BASE
            if access == self.uc.UC_MEM_WRITE:
                allowed = ((self.SP - 0x400, self.SP + 0x400), *writable)
                if not any(a <= address and address + size <= z for a, z in allowed):
                    raise AssertionError(f'Unallowed native write {address:x}+{size}')
                trace['writes'].append([pc, address, size, value])
            else:
                trace['reads'].append([pc, address, size])

        hooks = [self.vm.hook_add(self.uc.UC_HOOK_CODE, code),
                 self.vm.hook_add(self.uc.UC_HOOK_MEM_READ | self.uc.UC_HOOK_MEM_WRITE, memory)]
        try:
            self.vm.emu_start(BASE + start, 0, count=count, timeout=1000000)
        finally:
            for hook in hooks:
                self.vm.hook_del(hook)
        trace['stop_rva'] = self.reg('EIP') - BASE
        if trace['stop_rva'] not in stops:
            raise AssertionError('Native slice exhausted bound without reaching stop')
        return trace

    def receive(self, raw):
        """Start with a decoded queue; original opcode lookup obtains length."""
        if type(raw) is not bytes or not 1 <= len(raw) <= 29 or raw[0] != 0x31:
            raise ValueError('Expected 1..29 synthetic S2C31 bytes')
        self.prepare()
        self.vm.mem_write(self.CONNECTION, b'\xa5' * 0x4000)
        self.vm.mem_write(self.CONNECTION + 0x1368, raw)
        self.write32(self.CONNECTION + 0x1f68, len(raw))
        self.write32(self.CONNECTION + 0x1f6c, 0)
        self.write32(self.CONNECTION + 0x2cc0, 0)
        self.reg('ESI', self.CONNECTION)
        trace = self.run(0x13497, (0x13592, 0x135be), tuple(EXECUTED[k] for k in
                         ('logical_opcode_and_length', 'length_wrapper', 'length_opcode_mask',
                          'length_dispatch', 'length_function', 'logical_buffer_fill', 'logical_buffer_short_input',
                          'queue_byte_reader', 'queue_empty', 'queue_copy')),
                         ((self.CONNECTION + 0x1f6c, self.CONNECTION + 0x1f70),
                          (self.CONNECTION + 0x2cc0, self.CONNECTION + 0x2cc4 + 29)), count=4096)
        return {'count': self.u32(self.CONNECTION + 0x2cc0),
                'buffer_hex': bytes(self.vm.mem_read(self.CONNECTION + 0x2cc4, 29)).hex(),
                'trace': trace}

    def packet(self, raw, keys=(1,), buffered=False):
        if (type(raw) is not bytes or len(raw) != 29 or raw[0] != 0x31 or
                len(keys) > 2 or any(type(k) is not int or not -32768 <= k <= 32767 for k in keys)):
            raise ValueError('Expected exact S2C31 and at most two signed WORD keys')
        receive = self.receive(raw) if buffered else None
        self.prepare()
        self.vm.mem_write(self.ACTOR, b'\xa5' * 0x1000)
        self.vm.mem_write(self.ACTOR + 0xd4, bytes((len(keys),)))
        for index, key in enumerate(keys):
            self.vm.mem_write(self.ROW + index * 0x3ec, struct.pack('<h', key))
        self.vm.mem_write(self.PACKET, raw)
        before = bytes(self.vm.mem_read(self.ACTOR, 0x1000))
        self.reg('EBP', (self.UI - 0xa7f2f6c) & 0xffffffff)
        self.reg('EAX', self.CONNECTION + 0x2cc4 if buffered else self.PACKET)
        trace = self.run(0x68b4c, (0xaa2af, 0x6b517),
                         tuple(EXECUTED[k] for k in ('primary_opcode_dispatch', 'packet_dispatch', 'packet_scalar_writer',
                                                    'packet_no_match_return')),
                         ((self.ACTOR, self.ACTOR + 0x1000),))
        if receive is not None:
            trace['receive'] = receive
        return before, bytes(self.vm.mem_read(self.ACTOR, 0x1000)), trace

    def percent(self, index=0):
        if index not in (0, 1):
            raise ValueError('Only the two bounded row positions are mapped')
        self.prepare()
        self.reg('EDI', self.ROW + index * 0x3ec)
        self.reg('ESI', self.UI)
        trace = self.run(0xa9b92, (0xaa4c2,), tuple(EXECUTED[k] for k in
                         ('row_percent_argument', 'percent_conversion', 'truncate_helper')))
        store = next(w for w in trace['writes'] if w[0] == 0xaa4a8)
        bits = bytes(self.vm.mem_read(store[1], 4))
        args = struct.unpack('<4I', self.vm.mem_read(self.reg('ESP'), 16))
        return {'float32_hex': bits.hex(), 'percent_float': struct.unpack('<f', bits)[0],
                'bar_arguments': list(args), 'trace': trace}

    def text_arguments(self, bits):
        if type(bits) is not bytes or len(bits) != 4:
            raise ValueError('Expected captured float32 bytes')
        self.prepare()
        self.reg('ESI', self.UI)
        self.reg('EDI', self.UI + 0xe2170)
        self.vm.mem_write(self.SP + 0x1c, bits)
        trace = self.run(0xaa4c7, (0xaa508,), (EXECUTED['percent_format_arguments'],))
        sp = self.reg('ESP')
        args = list(struct.unpack('<5I', self.vm.mem_read(sp, 20)))
        return {'arguments': args,
                'double_hex': bytes(self.vm.mem_read(sp + 20, 8)).hex(), 'trace': trace}

    def bar(self, integer_percent, width):
        if (type(integer_percent) is not int or not -(1 << 31) <= integer_percent < (1 << 31)
                or type(width) is not int or not 1 <= width <= 4096):
            raise ValueError('Expected signed DWORD percent and bounded synthetic width 1..4096')
        self.prepare()
        self.reg('EBX', 0)
        self.reg('EDI', self.UI + 0xe2170)
        self.reg('ESI', 0)
        self.reg('EBP', 0x24)
        self.vm.mem_write(self.SP + 0x24, struct.pack('<4i', 10, 20, 10 + width - 1, 29))
        self.write32(self.SP + 0x40, integer_percent)
        self.write32(self.SP + 0x44, 0)
        trace = self.run(0x10618a, (0x106202,),
                         (EXECUTED['horizontal_bar_geometry'], EXECUTED['truncate_helper']))
        return {'rectangle': list(struct.unpack('<4i', self.vm.mem_read(self.SP + 0x14, 16))),
                'trace': trace}


def synthetic_packet(word, selector=1):
    """Clearly synthetic operands, not a captured server sample or protocol API."""
    if type(word) is not int or not 0 <= word <= 0xffff or not 0 <= selector <= 255:
        raise ValueError('Expected WORD and selector byte')
    raw = bytearray(b'\xa5' * 29)
    raw[0:3] = bytes((0x31, selector, 37))
    struct.pack_into('<H', raw, 25, word)
    return bytes(raw)


def build_evidence(client_root, image_path=IMAGE):
    image = pinned(image_path, IMAGE_SHA)
    source = message_source(client_root)
    native = NativeSource(image, bytes.fromhex(source['format_hex']))
    native.prepare()
    length_trace = native.run(0x12fa, (0x12ff,), (EXECUTED['length_value'],))
    length = native.reg('EAX')
    if (length != 29 or struct.unpack_from('<I', image, 0x13e8)[0] != BASE + 0x12fa
            or struct.unpack_from('<I', image, 0x6b698)[0] != BASE + 0x69fa9):
        raise AssertionError('Packet bindings changed')
    cases = []
    for word in (0, 1, 99, 100, 9999, 10000, 10001, 32767, 32768, 42768, 65535):
        _, _, packet_trace = native.packet(synthetic_packet(word), buffered=True)
        percent = native.percent()
        text = native.text_arguments(bytes.fromhex(percent['float32_hex']))
        bar = native.bar(percent['bar_arguments'][2], 137)
        cases.append({'wire_word': word, 'stored_low15': word & 0x7fff,
                      'stored_high1': word >> 15, 'packet_trace': packet_trace,
                      'percent': percent, 'text': text, 'bar_width_137': bar})
    def spans(ranges):
        return {key: {'rva': a, 'end_rva_exclusive': z, 'raw_hex': image[a:z].hex(),
                      'sha256': digest(image[a:z])} for key, (a, z) in ranges.items()}
    return {'schema': 'current-progression-source-v1', 'image_sha256': digest(image),
            'address_layout': 'VA = 0x400000 + RVA; file offset = RVA',
            'source': source, 'executed_spans': spans(EXECUTED), 'static_spans': spans(STATIC),
            'logical_length': length, 'length_trace': length_trace, 'cases': cases,
            'source_boundary': 'S2C31 logical bytes 25..26; original server writer unavailable',
            'next_native_evidence': {
                'rva': 0x10acb, 'callee_rva': 0x10a10,
                'output': '[ESI+0xC10], decoded byte count EAX at return RVA 0x10AD0',
                'dependency': 'Original current server frames and accompanying role/companion state, or original server producer code',
                'qualification': 'Static next upstream frame decoder, not executed or a recovered server formula'},
            'units': 'low15 in nominal hundredths of one display percent, not absolute EXP',
            'bar_limit': 'signed integer input clamped to 0..100 for geometry only',
            'open_original_rules': {key: {'status': 'OPEN', 'value': None} for key in OPEN_RULES},
            'runtime_verified': False, 'runtime_eligible': False,
            'qualification': 'Separate bounded slices with explicit live-ins; no whole UI, server or live playable proof'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--client-root', type=Path, required=True)
    parser.add_argument('--native-image', type=Path, default=IMAGE)
    args = parser.parse_args()
    print(json.dumps(build_evidence(args.client_root, args.native_image), sort_keys=True, indent=2))


if __name__ == '__main__':
    main()
