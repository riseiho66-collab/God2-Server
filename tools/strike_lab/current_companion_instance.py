"""Pinned native opcode 3B -> slot store -> incoming packed UI record.

Research stdout only. Synthetic messages exercise original bounded code; no
game/CRT stubs, socket traffic, runtime data, or growth formulas are supplied.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

# Match the existing research runtime without importing any recovery corpus.
PACKAGES = Path(__file__).resolve().parents[2] / 'artifacts/tooling/crypto-oracle-python'
if str(PACKAGES) not in sys.path:
    sys.path.insert(0, str(PACKAGES))
import unicorn as uc
from unicorn import x86_const as x86


IMAGE_SHA = '149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
BASE = 0x400000
RANGES = {
    'primary_dispatch': (0x68b4c, 0x68b68),
    'primary_case_3b': (0x6a029, 0x6a036),
    'secondary_dispatch': (0x1193c2, 0x1193e7),
    'secondary_case_3b': (0x1194f2, 0x1194fe),
    'slot_guard_and_store': (0x98dd0, 0x98e2d),
    'ui_entry_gate': (0x87350, 0x87372),
    'ui_selection_gate': (0x87394, 0x873b3),
    'ui_copy': (0x873fa, 0x87430),
    'ui_reset': (0x869e0, 0x86a04),
    'caller_stage': (0x87230, 0x8724a),
    'wrapper_entry': (0x87690, 0x876ac),
}
STATIC_RANGES = {
    'primary_buffer_acquisition': (0x68b1c, 0x68b4c),
    'primary_jump_entry_3b': (0x6b6c0, 0x6b6c4),
    'secondary_buffer_acquisition': (0x1193b8, 0x1193c2),
    'secondary_jump_entry_12': (0x119938, 0x11993c),
    'secondary_selector_table': (0x119a04, 0x119b00),
    'buffer_return': (0x13650, 0x13667),
    'receive_buffer_fill': (0x13558, 0x13597),
    'ui_event_to_record': (0x87206, 0x87230),
    'wrapper_to_display': (0x876b1, 0x876ce),
    'display_argument_reload': (0xb7817, 0xb781e),
}
CALLS = ((0x6a031, 0x98dd0), (0x1194f9, 0x98dd0),
         (0x87245, 0x87690), (0x876c9, 0xb5be0),
         (0x68b47, 0x13650), (0x1193bd, 0x13650))


def digest(data):
    return hashlib.sha256(data).hexdigest()


def serialize(value):
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=True) + '\n').encode('ascii')


def qualified_image(path):
    image = Path(path).read_bytes()
    if digest(image) != IMAGE_SHA:
        raise ValueError('Unqualified current native image')
    return image


def bindings(image):
    if digest(image) != IMAGE_SHA:
        raise ValueError('Unqualified current native image')
    for pc, target in CALLS:
        if image[pc] != 0xe8 or pc + 5 + struct.unpack_from('<i', image, pc + 1)[0] != target:
            raise AssertionError('Native direct call changed')
    if struct.unpack_from('<I', image, 0x6b5d4 + 4 * 0x3b)[0] != BASE + 0x6a029:
        raise AssertionError('Primary dispatch changed')
    selector = image[0x119a04 + 0x3b]
    if selector != 12 or struct.unpack_from('<I', image, 0x119908 + 4 * selector)[0] != BASE + 0x1194f2:
        raise AssertionError('Secondary dispatch changed')
    return {'opcode': 0x3b, 'primary_table_entry_rva': 0x6b6c0,
            'secondary_selector': selector, 'secondary_table_entry_rva': 0x119938,
            'secondary_opcodes_for_same_case': [i for i in range(0xfc)
                                               if image[0x119a04 + i] == selector],
            'calls': [{'call_rva': p, 'target_rva': t} for p, t in CALLS]}


class NativeInstance:
    OWNER = 0x12000000
    UI = 0x13000000
    STACK = 0x14000000
    SP = STACK + 0x8000
    BUFFER_PAGE = 0x15000000
    MESSAGE = BUFFER_PAGE + 0x100
    AUX = 0x16000000
    SECONDARY = 0x17000000
    STORE = OWNER + 0x85610
    RECORD = UI + 0x3ac4

    def __init__(self, image):
        self.binding = bindings(image)
        self.vm = uc.Uc(uc.UC_ARCH_X86, uc.UC_MODE_32)
        self.vm.mem_map(BASE, len(image), uc.UC_PROT_ALL)
        self.vm.mem_write(BASE, image)
        self.vm.mem_protect(BASE, len(image), uc.UC_PROT_READ | uc.UC_PROT_EXEC)
        for address, size in ((self.OWNER, 0x100000), (self.UI, 0x4000),
                              (self.STACK, 0x10000), (self.BUFFER_PAGE, 0x1000),
                              (self.AUX, 0x1000), (self.SECONDARY, 0x1000)):
            self.vm.mem_map(address, size, uc.UC_PROT_READ | uc.UC_PROT_WRITE)
        self.put32(self.OWNER + 0x574c0, self.AUX)
        self.put32(self.UI + 0xdc, self.OWNER)
        self.put32(self.SECONDARY + 0x20, self.OWNER)
        for address in (self.BUFFER_PAGE, self.AUX, self.SECONDARY):
            self.vm.mem_protect(address, 0x1000, uc.UC_PROT_READ)
        self.active = False
        self.executed = set()
        self.vm.hook_add(uc.UC_HOOK_CODE, self._code)
        self.vm.hook_add(uc.UC_HOOK_MEM_READ, self._read)
        self.vm.hook_add(uc.UC_HOOK_MEM_WRITE, self._write)

    def put32(self, address, value):
        self.vm.mem_write(address, struct.pack('<I', value))

    def reg(self, name, value=None):
        register = getattr(x86, 'UC_X86_REG_' + name)
        if value is None:
            return self.vm.reg_read(register)
        self.vm.reg_write(register, value)

    def prepare(self):
        self.vm.mem_write(self.SP - 0x100, b'\xa5' * 0x200)
        for name in ('EAX', 'EBX', 'ECX', 'EDX', 'ESI', 'EDI', 'EBP'):
            self.reg(name, 0xa5a5a5a5)
        self.reg('ESP', self.SP)
        self.reg('EFLAGS', 2)  # DF clear: explicit forward-copy precondition.

    def _code(self, vm, address, size, context):
        if not self.active:
            return
        pc = address - BASE
        if pc in self.stops:
            vm.emu_stop()
            return
        if not any(a <= pc < z for a, z in self.allowed_code):
            raise AssertionError(f'Unexpected native instruction {pc:x}')
        self.pcs.append(pc)
        self.executed.add(pc)

    def _read(self, vm, access, address, size, value, context):
        if self.active and not self.STACK <= address < self.STACK + 0x10000:
            self.reads.append([self.reg('EIP') - BASE, address, size])

    def _write(self, vm, access, address, size, value, context):
        if not self.active:
            return
        if self.SP - 0x80 <= address < address + size <= self.SP + 0x40:
            return
        if not any(a <= address < address + size <= z for a, z in self.allowed_writes):
            raise AssertionError(f'Out-of-bound native write {address:x}/{size}')
        self.writes.append([self.reg('EIP') - BASE, address, size, value])

    def run(self, start, stops, names, writes=()):
        self.stops = set(stops)
        self.allowed_code = [RANGES[name] for name in names]
        self.allowed_writes = list(writes)
        self.reads, self.writes, self.pcs = [], [], []
        self.active = True
        try:
            self.vm.emu_start(BASE + start, 0, count=300, timeout=1000000)
        finally:
            self.active = False
        pc = self.reg('EIP') - BASE
        if pc not in self.stops:
            raise AssertionError('Native slice did not reach exact stop')
        return {'stop_rva': pc, 'reads': self.reads[:], 'writes': self.writes[:],
                'instruction_count': len(self.pcs)}

    def packet_store(self, slot, record, dispatch='primary', auxiliary_state=0):
        if type(slot) is not int or not 0 <= slot <= 255 or len(record) != 20:
            raise ValueError('Expected byte slot and exact 20-byte record')
        if dispatch not in ('primary', 'secondary'):
            raise ValueError('Unknown dispatch')
        self.prepare()
        # Message offset 1 and padding are distinct poison, not recovered fields.
        message = bytes((0x3b, 0xd3, slot, 0x69, 0x96)) + record
        self.vm.mem_write(self.MESSAGE - 16, b'\xa5' * 64)
        self.vm.mem_write(self.MESSAGE, message)
        self.vm.mem_write(self.STORE - 16, b'\xa5' * (24 * 50 + 32))
        self.put32(self.AUX + 0x24, auxiliary_state)
        dest = self.STORE + slot * 24
        self.reg('EAX', self.MESSAGE)
        if dispatch == 'primary':
            self.reg('EBP', self.OWNER - 0xa7f2f6c)
            names = ('primary_dispatch', 'primary_case_3b', 'slot_guard_and_store')
            start = 0x68b4c
        else:
            self.reg('EBP', self.SECONDARY)
            names = ('secondary_dispatch', 'secondary_case_3b', 'slot_guard_and_store')
            start = 0x1193c2
        result = self.run(start, (0x98e2d, 0x98fbd, 0x98e05), names, ((dest, dest + 20),))
        copied = result['stop_rva'] == 0x98e2d
        snapshot = bytes(self.vm.mem_read(self.STORE - 16, 24 * 50 + 32))
        expected = bytearray(b'\xa5' * len(snapshot))
        if copied:
            expected[16 + slot * 24:36 + slot * 24] = record
            reads = [[0x98e2b, self.MESSAGE + 5 + i, 4] for i in range(0, 20, 4)]
            writes = [[0x98e2b, dest + i, 4, struct.unpack_from('<I', record, i)[0]]
                      for i in range(0, 20, 4)]
            if [r for r in result['reads'] if r[0] == 0x98e2b] != reads or result['writes'] != writes:
                raise AssertionError('Packet-to-store native width/provenance differs')
        if snapshot != expected or (not copied and result['writes']):
            raise AssertionError('Slot store or neighboring bytes changed unexpectedly')
        if bytes(self.vm.mem_read(self.MESSAGE, len(message))) != message:
            raise AssertionError('Native message changed')
        result.update(slot=slot, dispatch=dispatch, auxiliary_state=auxiliary_state,
                      copied=copied, record_hex=record.hex())
        return result

    def ui_entry_gate(self, slot_word, flags):
        self.prepare()
        self.vm.mem_write(self.OWNER + 0x855f0, struct.pack('<H', slot_word))
        self.put32(self.SP + 8, flags)
        self.reg('ECX', self.UI)
        return self.run(0x87350, (0x87372, 0x874c0), ('ui_entry_gate',))

    def ui_copy(self, slot):
        if type(slot) is not int or not 0 <= slot < 50:
            raise ValueError('UI slice requires a nonnegative in-store slot')
        self.prepare()
        self.vm.mem_write(self.OWNER + 0x855f0, struct.pack('<H', slot))
        self.vm.mem_write(self.RECORD - 4, b'\xa5' * 32)
        self.reg('EBP', self.UI)
        result = self.run(0x87394, (0x873b3, 0x87430),
                          ('ui_selection_gate', 'ui_copy'), ((self.RECORD, self.RECORD + 23),))
        result['copied'] = result['stop_rva'] == 0x87430
        result['slot'] = slot
        source = bytes(self.vm.mem_read(self.STORE + 24 * slot, 20))
        expected = source + source[:2] + bytes((slot,)) if result['copied'] else b'\xa5' * 23
        if bytes(self.vm.mem_read(self.RECORD - 4, 32)) != b'\xa5' * 4 + expected + b'\xa5' * 5:
            raise AssertionError('UI copy or neighboring bytes changed unexpectedly')
        if result['copied']:
            expected_reads = [[0x87416, self.STORE + 24 * slot + i, 4] for i in range(0, 20, 4)]
            expected_writes = [[0x87416, self.RECORD + i, 4, struct.unpack_from('<I', source, i)[0]]
                               for i in range(0, 20, 4)]
            expected_writes += [[0x8741c, self.RECORD + 20, 2, struct.unpack_from('<H', source)[0]],
                                [0x87429, self.RECORD + 22, 1, slot]]
            if [r for r in result['reads'] if r[0] == 0x87416] != expected_reads or result['writes'] != expected_writes:
                raise AssertionError('Store-to-UI native width/provenance differs')
        return result

    def caller_pointer(self):
        self.prepare()
        self.vm.mem_write(self.UI + 0x3adb, b'\x81')
        self.reg('ESI', self.UI)
        self.reg('EDI', self.RECORD)  # 87220 established this before 874D0.
        before = bytes(self.vm.mem_read(self.RECORD, 20))
        result = self.run(0x87230, (0x876ac,), ('caller_stage', 'wrapper_entry'))
        if self.reg('ESI') != self.RECORD or bytes(self.vm.mem_read(self.RECORD, 20)) != before:
            raise AssertionError('Wrapper third-argument record pointer differs')
        arguments = list(struct.unpack('<4I', self.vm.mem_read(self.SP - 16, 16)))
        if arguments != [0x1a6, 0x1b5, self.RECORD, 0xffffff81]:
            raise AssertionError('Caller argument binding differs')
        result['caller_arguments'] = arguments
        return result

    def reset_ui(self):
        self.prepare()
        self.vm.mem_write(self.RECORD - 4, b'\xa5' * 32)
        self.reg('ECX', self.UI)
        result = self.run(0x869e0, (0x86a04,), ('ui_reset',), ((self.RECORD, self.RECORD + 24),))
        if bytes(self.vm.mem_read(self.RECORD - 4, 32)) != b'\xa5' * 4 + b'\0' * 24 + b'\xa5' * 4:
            raise AssertionError('UI reset differs')
        return result


def record_for(packed):
    if type(packed) is not int or not 0 <= packed <= 0xffffffff:
        raise ValueError('Expected packed DWORD')
    return bytes.fromhex('3412c7d8697a8b9cadbecfd0') + struct.pack('<I', packed) + b'\xe1\xf2\x83\x94'


def build_evidence(image_path):
    image = qualified_image(image_path)
    native = NativeInstance(image)
    sample = record_for(0xf5a39c7e)
    slot_cases = [native.packet_store(slot, sample, dispatch)
                  for dispatch in ('primary', 'secondary') for slot in range(256)]
    auxiliary_cases = [native.packet_store(slot, sample, auxiliary_state=state)
                       for slot in (37, 38, 39, 40, 41, 42) for state in (0, 1, 2, 0xffffffff)]
    ui_gates = [dict(slot_word=s, flags=f, **native.ui_entry_gate(s, f))
                for s in (0, 29, 30, 42, 43, 49, 0x7fff, 0x8000, 0xffff)
                for f in (0, 1, 2, 3, 0x100)]
    ui_cases = []
    for slot in range(50):
        native.packet_store(slot, sample)
        ui_cases.append(native.ui_copy(slot))
    # Basis bits prove lossless transport of every DWORD bit, including both
    # selector nibbles and unrelated bits; these are not game instance values.
    packed_values = [0, 0xffffffff, 0xa5a5a5a5, 0x5a5a5a5a] + [1 << i for i in range(32)]
    transfers = []
    for dispatch in ('primary', 'secondary'):
        for slot in (0, 29, 42, 43):
            for packed in packed_values:
                store = native.packet_store(slot, record_for(packed), dispatch)
                ui = native.ui_copy(slot)
                actual = struct.unpack('<I', native.vm.mem_read(native.RECORD + 12, 4))[0]
                if actual != packed:
                    raise AssertionError('Packed DWORD changed in transfer')
                transfers.append({'dispatch': dispatch, 'slot': slot, 'packed': packed,
                                  'observed': actual,
                                  'packet_write': store['writes'][3], 'ui_write': ui['writes'][3]})
    caller = native.caller_pointer()
    reset = native.reset_ui()
    ranges = lambda spans: {name: {'start_rva': a, 'stop_rva_exclusive': z,
                                  'sha256': digest(image[a:z])} for name, (a, z) in spans.items()}
    return {
        'schema': 'god2-current-companion-instance-v1', 'image_sha256': IMAGE_SHA,
        'runtime_eligible': False, 'growth_formula_verified': False,
        'experience_thresholds_verified': False, 'growth_status': 'OPEN',
        'classification': 'native_message_to_slot_store_to_ui_record_copy',
        'bindings': native.binding,
        'binding': {'message_opcode': 0x3b, 'handler_rva': 0x98dd0,
                    'handler_argument_message_offset': 1, 'slot_message_offset': 2,
                    'record_message_offset': 5, 'packed_message_offset': 17,
                    'record_size': 20, 'copy_element_width': 4, 'slot_stride': 24,
                    'store_owner_offset': 0x85610, 'ui_record_offset': 0x3ac4,
                    'packed_record_offset': 12, 'quality_bits': [20, 23], 'star_bits': [16, 19]},
        'executed_ranges': ranges(RANGES), 'static_only_ranges': ranges(STATIC_RANGES),
        'executed_pcs': sorted(native.executed),
        'slot_case_count': len(slot_cases), 'slot_cases_sha256': digest(serialize(slot_cases)),
        'slot_outcomes': {d: {str(s): c['stop_rva'] for s, c in enumerate(
            [x for x in slot_cases if x['dispatch'] == d])} for d in ('primary', 'secondary')},
        'auxiliary_cases': auxiliary_cases, 'ui_entry_gates': ui_gates,
        'ui_selection_cases': ui_cases, 'transfer_count': len(transfers),
        'transfers_sha256': digest(serialize(transfers)), 'transfer_examples': [transfers[0], transfers[-1]],
        'caller_pointer': caller, 'reset': reset,
        'boundaries': [
            'Synthetic opcode-first messages; receive/framing/decryption and live gameplay not executed.',
            'Both native dispatches and handler execute through copy; stop at 98E2D before metadata lookup.',
            'Signed byte slots 0..49 accepted; 38..41 with [owner+574C0]+24 == 1 stop before 961A0.',
            'UI entry gate stops at 87372 before record access/9B770; selection/copy starts at 87394 after that unexecuted call.',
            'UI selection accepts nonnegative slots 0..29,42,43; signed WORD selector is a declared live-in.',
            'Caller slice resumes at 87230 after unexecuted 874D0, with EDI=UI+3AC4; stops before 59A60.',
            'Existing 876B8/876C9 -> B5BE0 sixth-argument binding is static only here; display/getters not retested.',
            'DF=0, little-endian x86 DWORD copies; stack/input/register poison and declared owner links are synthetic.',
            'No callee success stubs; code allowlist, bounded writes, exact stops, 300 instructions and 1 second per slice.',
            'No proof of server-side bit construction, growth/stat/upgrade rules, EXP or a live companion instance.',
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native-image', type=Path, required=True)
    args = parser.parse_args()
    print(serialize(build_evidence(args.native_image)).decode('ascii'), end='')


if __name__ == '__main__':
    main()
