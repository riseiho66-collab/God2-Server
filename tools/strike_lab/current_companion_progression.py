"""Pinned QualityStar -> original display-argument consumer, not stat rules.

Read-only CLI. Reuses the existing row loader solely to prepare native inputs;
new evidence is the unchanged getters, packed selectors and format arguments.
The two argument-building slices stop BEFORE CRT formatting. No fake return,
renderer, packet, upgrade, EXP formula, runtime output or live process is used.
"""
import argparse
from pathlib import Path
import struct

from . import recover_companion_growth as growth


IMAGE_SHA = growth.IMAGE_SHA
SOURCE = 'NewCombatPet_QualityStar'
BASE = 0x400000
RANGES = {
    'quality_getter': (0x5cac0, 0x5cac7),
    'star_getter': (0x5cb20, 0x5cb27),
    'quality_arguments_branch_a': (0xb7dc9, 0xb7e4d),
    'quality_arguments_branch_b': (0xb7eae, 0xb7f12),
    'star_arguments': (0xb7f6e, 0xb7fad),
    'gate': (0xb7db4, 0xb7dc9),
}
STATIC_RANGES = {
    'category_copy_producer': (0x5ca00, 0x5ca63),
    'category_copy_call_and_local_copy': (0xb7a68, 0xb7a9b),
    'second_gate_byte': (0xb7da4, 0xb7dc9),
    'packed_record_argument_load': (0xb7817, 0xb781e),
    'display_function_prologue': (0xb5be0, 0xb5c35),
    'caller_record_argument': (0x87690, 0x876ce),
    'formatter_entry': (0x147af7, 0x147b49),
}


def qualified_inputs(client_root, image_path):
    image_path = Path(image_path)
    image = growth.read_source(image_path.parent, image_path.name)
    if growth.digest(image) != IMAGE_SHA:
        raise ValueError('Unqualified current native image')
    raw = growth.read_source(client_root, growth.source_path(SOURCE))
    if growth.digest(raw) != growth.SOURCE_HASHES[SOURCE][0]:
        raise ValueError('Unqualified current QualityStar source')
    decoded = growth.decode_csvz(raw)
    if growth.digest(decoded) != growth.SOURCE_HASHES[SOURCE][1]:
        raise ValueError('Unqualified decoded QualityStar source')
    return image, decoded


def relative_call(image, rva, target):
    if image[rva] != 0xe8 or rva + 5 + struct.unpack_from('<i', image, rva + 1)[0] != target:
        raise AssertionError('Changed native call binding')
    return {'call_rva': rva, 'target_rva': target}


class NativeProgression(growth._NativeRows):
    """Only CRT decimal parsing is adapted, by the existing row fixture."""

    OWNER = 0x3500000

    def __init__(self, image, decoded):
        if growth.digest(image) != IMAGE_SHA:
            raise ValueError('Unqualified current native image')
        if growth.digest(decoded) != growth.SOURCE_HASHES[SOURCE][1]:
            raise ValueError('Unqualified decoded QualityStar source')
        super().__init__(image)
        rows = growth.parse_auxiliary(SOURCE, decoded)['records']
        self.values = [[growth.decimal(x) for x in growth.fields(row)] for row in rows]
        self.active = False
        self.pcs, self.reads = set(), []
        self.vm.hook_add(self.uc.UC_HOOK_CODE, self._guard)
        self.vm.hook_add(self.uc.UC_HOOK_MEM_READ, self._read)
        self.vm.hook_add(self.uc.UC_HOOK_MEM_WRITE, self._consumer_write)
        for row, offset, dest, entry, stop in zip(
                rows, (0xfc2cc, 0xfc2d0), (self.OUTPUT, self.OUTPUT + 0x100),
                (0x5ca92, 0x5caf2), (0x5caaf, 0x5cb0f)):
            self.vm.mem_write(dest, b'\xa5' * 34)
            self.vm.mem_write(self.TABLE + offset, struct.pack('<I', dest))
            self.tokenize(row, 16)
            self.reg('EDI', self.TABLE)
            self.row(entry, stop, range(16), [(dest, dest + 32)])
            expected = struct.pack('<16H', *[growth.decimal(x) for x in growth.fields(row)])
            if bytes(self.vm.mem_read(dest, 34)) != expected + b'\xa5\xa5':
                raise AssertionError('Existing native row fixture differs')
        self.vm.mem_map(self.OWNER, 0x100000, self.uc.UC_PROT_READ | self.uc.UC_PROT_WRITE)
        self.vm.mem_write(self.OWNER + 0xcff70, struct.pack('<I', self.TABLE))
        # Missing message strings are an explicit boundary condition. Original
        # branches produce null label arguments; the formatter never executes.
        self.vm.mem_write(self.TABLE + 0xb2c6c, b'\0\0')
        for address, size in ((self.OWNER, 0x100000), (self.TABLE, 0x100000),
                              (self.OUTPUT, 0x4000), (self.INPUT, 4096)):
            self.vm.mem_protect(address, size, self.uc.UC_PROT_READ)

    def _guard(self, vm, address, size, context):
        if not self.active:
            return
        rva = address - BASE
        if rva in self.stops:
            return
        if not any(start <= rva < stop for start, stop in RANGES.values()):
            raise AssertionError(f'Unexpected consumer instruction {rva:x}')
        self.pcs.add(rva)

    def _read(self, vm, access, address, size, value, context):
        if self.active and self.OUTPUT <= address < self.OUTPUT + 0x4000:
            self.reads.append((vm.reg_read(self.x86.UC_X86_REG_EIP) - BASE, address, size))

    def _consumer_write(self, vm, access, address, size, value, context):
        if self.active and not self.SP - 0x100 <= address < address + size <= self.SP + 0x14:
            raise AssertionError('Consumer wrote outside bounded stack arguments/local pointer')

    def segment(self, start, stops):
        self.stops = set(stops)
        hooks = [self.vm.hook_add(self.uc.UC_HOOK_CODE, lambda vm, a, s, c: vm.emu_stop(),
                                  begin=BASE + stop, end=BASE + stop) for stop in stops]
        self.active = True
        try:
            self.vm.emu_start(BASE + start, 0, count=300, timeout=1000000)
        finally:
            self.active = False
            for hook in hooks:
                self.vm.hook_del(hook)
        pc = self.vm.reg_read(self.x86.UC_X86_REG_EIP) - BASE
        if pc not in self.stops:
            raise AssertionError('Consumer did not reach an exact boundary')
        return pc

    def prepare(self):
        self.vm.mem_write(self.SP - 0x100, b'\xa5' * 0x300)
        for name in ('EAX', 'EBX', 'ECX', 'EDX', 'ESI', 'EDI', 'EBP'):
            self.reg(name, 0xa5a5a5a5)
        self.reg('EFLAGS', 2)
        self.reg('ESP', self.SP)
        self.pcs.clear()
        self.reads.clear()

    def gate(self, first, second):
        if any(type(x) is not int or not 0 <= x <= 255 for x in (first, second)):
            raise ValueError('Gate inputs must be bytes')
        self.prepare()
        self.vm.mem_write(self.SP + 0x68, bytes((first, second)))
        # B7DA4/B7DAD already extracted the second byte before an intervening
        # string copy. This segment begins at the remaining arithmetic.
        self.reg('EAX', second)
        pc = self.segment(0xb7db4, (0xb7dc9, 0xb7fe8))
        actual_sum = self.vm.reg_read(self.x86.UC_X86_REG_EAX)
        if actual_sum != first + second or (pc == 0xb7dc9) != (first + second == 1):
            raise AssertionError('Native flag sum/branch differs')
        return {'first': first, 'second': second, 'sum': actual_sum, 'admitted': pc == 0xb7dc9}

    def arguments(self, packed, mode):
        if type(packed) is not int or not 0 <= packed <= 0xffffffff or mode not in (1, 0x100):
            raise ValueError('Expected packed DWORD and an admitted boundary mode')
        self.prepare()
        record = b'\xa5' * 12 + struct.pack('<I', packed) + b'\xa5' * 16
        self.vm.mem_write(self.INPUT, record)
        self.vm.mem_write(self.SP + 0x68, struct.pack('<I', mode))
        self.reg('EBP', self.OWNER)
        self.reg('EBX', self.INPUT)
        quality_stop = 0xb7e4d if mode == 1 else 0xb7f12
        self.segment(0xb7dc9, (quality_stop,))
        quality = self.capture_arguments(0x192a04)
        # The formatter and subsequent string copy are not run or stubbed.
        # Start an independent later slice with its declared live-in registers;
        # retain the original Star pointer stored by B7DE1 in this same VM.
        self.reg('ESP', self.SP)
        self.reg('EAX', self.TABLE)
        self.reg('EDX', 0)
        self.segment(0xb7f6e, (0xb7fad,))
        star = self.capture_arguments(0x1929f4)
        qi, si = (packed >> 20) & 15, (packed >> 16) & 15
        if (quality, star) != ((qi, self.values[0][qi]), (si, self.values[1][si])):
            raise AssertionError('Native source-selected numeric arguments differ')
        expected_reads = [(0xb7e38 if mode == 1 else 0xb7efd, self.OUTPUT + 2 * qi, 2),
                          (0xb7f98, self.OUTPUT + 0x100 + 2 * si, 2)]
        if self.reads != expected_reads:
            raise AssertionError('Native table read provenance differs')
        if not {0x5cac0, 0x5cac6, 0x5cb20, 0x5cb26, 0xb7de1} <= self.pcs:
            raise AssertionError('Original getters/local-pointer store did not execute')
        if bytes(self.vm.mem_read(self.INPUT, len(record))) != record:
            raise AssertionError('Packed source record changed')
        return {'packed': packed, 'mode': mode, 'quality': list(quality), 'star': list(star),
                'table_reads': [list(x) for x in self.reads]}

    def capture_arguments(self, format_rva):
        sp = self.vm.reg_read(self.x86.UC_X86_REG_ESP)
        if sp != self.SP - 24:
            raise AssertionError('Unexpected format argument stack')
        dest, fmt, label, index, suffix, value = struct.unpack('<6I', self.vm.mem_read(sp, 24))
        if (dest, fmt, label, suffix) != (self.SP + 0x88, BASE + format_rva, 0, 0):
            raise AssertionError('Unexpected format argument binding')
        return index, value


def build_evidence(client_root, image_path):
    image, decoded = qualified_inputs(client_root, image_path)
    native = NativeProgression(image, decoded)
    rows = growth.parse_auxiliary(SOURCE, decoded)['records']
    cases = [native.arguments((qi << 20) | (si << 16) | noise, mode)
             for mode in (1, 0x100) for noise in (0, 0xff00ffff)
             for qi in range(16) for si in range(16)]
    gates = [native.gate(a, b) for a in (0, 1, 0xa5) for b in (0, 1, 0xa5)]
    calls = [relative_call(image, *pair) for pair in (
        (0xb7dcf, 0x5cac0), (0xb7ddc, 0x5cb20),
        (0xb7e4d, 0x147af7), (0xb7f12, 0x147af7), (0xb7fad, 0x147af7),
        (0xb7a87, 0x5ca00), (0x876c9, 0xb5be0))]
    formats = {hex(rva): image[rva:image.index(b'\0', rva)].decode('ascii')
               for rva in (0x192a04, 0x1929f4)}
    if formats != {'0x192a04': '\n%s:%d (%s+%d) ', '0x1929f4': '%s:%d (%s+%d)'}:
        raise AssertionError('Original format strings differ')
    dependencies = ('recover_companion_growth.py', 'current_npc_resources.py')
    return {
        'schema': 'god2-current-companion-progression-consumer-v1',
        'image_sha256': IMAGE_SHA, 'runtime_eligible': False,
        'classification': 'native_display_argument_selection_only',
        'growth_formula_verified': False, 'experience_thresholds_verified': False,
        'source': {'path': growth.source_path(SOURCE),
                   'sha256': growth.SOURCE_HASHES[SOURCE][0],
                   'decoded_sha256': growth.digest(decoded), 'records': rows},
        'executed_ranges': {name: {'start_rva': start, 'stop_rva_exclusive': stop,
                                   'sha256': growth.digest(image[start:stop])}
                            for name, (start, stop) in RANGES.items()},
        'static_only_ranges': {name: {'start_rva': start, 'stop_rva_exclusive': stop,
                                      'sha256': growth.digest(image[start:stop])}
                               for name, (start, stop) in STATIC_RANGES.items()},
        'calls': calls, 'formats': formats,
        'case_count': len(cases), 'cases_sha256': growth.digest(growth.serialize(cases)),
        'diagonal_examples': [cases[i * 17] for i in range(16)],
        'synthetic_gate_cases': gates,
        'dependencies': {name: growth.digest(Path(__file__).with_name(name).read_bytes())
                         for name in dependencies},
        'execution_boundary': 'Existing row fixture plus original getter/argument slices. '
            'No formatting call executed; Star is a separate slice retaining the original '
            'stored pointer. Zero message count, synthetic record/mode and A5 scratch are '
            'explicit conditions. Only the existing CRT %d row adapter is used. '
            'Consumer code allowlist, read-only native inputs, stack-only writes, exact stops, '
            '300 instructions and 1000000 microseconds per consumer segment.',
        'next_producer': {
            'status': 'static_caller_argument_boundary_not_value_writer',
            'function_rva': 0xb5be0, 'argument_ordinal': 6, 'packed_dword_offset': 12,
            'caller_rva': 0x87690, 'caller_input_argument_ordinal': 3,
            'caller_pass_rva': 0x876b8, 'caller_call_rva': 0x876c9,
            'missing': 'Writer of incoming record +0x0C; level/stat/EXP producer still unverified'},
        'deity_xp_lead': None,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--client-root', type=Path, required=True)
    parser.add_argument('--native-image', type=Path, required=True)
    args = parser.parse_args()
    print(growth.serialize(build_evidence(args.client_root, args.native_image)).decode('ascii'), end='')


if __name__ == '__main__':
    main()
