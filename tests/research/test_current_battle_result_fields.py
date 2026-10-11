"""Pinned current instructions only; synthetic inputs, no code replacement."""
from dataclasses import replace
import hashlib
from pathlib import Path
import random
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'artifacts/tooling/crypto-oracle-python'))
from tools.strike_lab import current_battle_result_fields as model
from unicorn import (Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE,
                     UC_HOOK_MEM_READ, UC_HOOK_MEM_WRITE,
                     UC_PROT_READ, UC_PROT_EXEC)
from unicorn.x86_const import (UC_X86_REG_EAX, UC_X86_REG_EBX, UC_X86_REG_ECX, UC_X86_REG_EDX,
    UC_X86_REG_EBP, UC_X86_REG_ESI, UC_X86_REG_EDI, UC_X86_REG_EIP,
    UC_X86_REG_ESP, UC_X86_REG_EFLAGS)

BASE, STACK, SP, RETURN = 0x400000, 0x3000000, 0x3002000, 0x3003000
BATTLE, ENTITY, INPUT_PAGE = 0x5000000, 0x6000000, 0x6100000
CONTEXT = BATTLE + 0x144938
DISPATCH = BATTLE + 0xa9e9cb1
RESULT_RECORD = DISPATCH - 1
CACHED = BATTLE + 0xa9e9c74
RANGES = ((0x1200, 0x1216), (0x124c, 0x1252),
          (0x1193c4, 0x1193e7), (0x114321, 0x114358),
          (0x114464, 0x11447a), (0x1144ae, 0x1144b6),
          (0x117480, 0x1174fc), (0x12c3e0, 0x12c425),
          (0x11e6e0, 0x11e76a), (0x126270, 0x126289))


class CurrentBattleResultFieldsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image = (ROOT / 'artifacts/capture_work/host-20260918-1430/output/'
                     'native-master-01-stable.bin').read_bytes()
        if hashlib.sha256(cls.image).hexdigest() != model.IMAGE_SHA256:
            raise AssertionError('Pinned current image changed; re-audit required')

    def machine(self):
        vm = Uc(UC_ARCH_X86, UC_MODE_32)
        vm.mem_map(BASE, (len(self.image) + 4095) & ~4095,
                   UC_PROT_READ | UC_PROT_EXEC)
        vm.mem_write(BASE, self.image)
        for address, size in ((STACK, 0x4000), (BATTLE, 4096),
                              (CONTEXT & ~4095, 4096),
                              (DISPATCH & ~4095, 4096),
                              (ENTITY, 4096), (INPUT_PAGE, 4096)):
            vm.mem_map(address, size)
        self.trace, self.reads, self.writes = [], [], []
        self.stops, self.allowed_writes = set(), ()

        def code(machine, address, size, _):
            rva = address - BASE
            if rva in self.stops:
                machine.emu_stop()
                return
            if not any(lo <= rva and rva + size <= hi for lo, hi in RANGES):
                raise AssertionError(f'Outside closed code ranges: {rva:X}')
            self.trace.append(rva)

        def write(machine, access, address, size, value, _):
            if not any(lo <= address and address + size <= hi for lo, hi in
                       ((STACK, STACK + 0x3000), *self.allowed_writes)):
                raise AssertionError(f'Unexpected native write: {address:X}/{size}')
            if not STACK <= address < STACK + 0x3000:
                self.writes.append((address, size, value))

        def read(machine, access, address, size, value, _):
            self.reads.append((address, size))

        vm.hook_add(UC_HOOK_CODE, code)
        vm.hook_add(UC_HOOK_MEM_WRITE, write)
        vm.hook_add(UC_HOOK_MEM_READ, read)
        return vm

    def run_native(self, vm, entry, stops=(), args=(), registers=()):
        self.trace.clear()
        self.reads.clear()
        self.writes.clear()
        self.stops = set(stops)
        vm.mem_write(STACK, b'\xa5' * 0x3000)
        vm.mem_write(SP, struct.pack('<' + 'I' * (len(args) + 1), RETURN, *args))
        for reg in (UC_X86_REG_EAX, UC_X86_REG_ECX, UC_X86_REG_EDX,
                    UC_X86_REG_EBP, UC_X86_REG_ESI, UC_X86_REG_EDI):
            vm.reg_write(reg, 0xa5a50000)
        vm.reg_write(UC_X86_REG_ESP, SP)
        vm.reg_write(UC_X86_REG_EFLAGS, 2)
        for reg, value in registers:
            vm.reg_write(reg, value)
        vm.emu_start(BASE + entry, RETURN, count=2000)
        end = vm.reg_read(UC_X86_REG_EIP)
        self.assertIn(end, {RETURN} | {BASE + stop for stop in stops})
        if end == RETURN:
            self.assertEqual(vm.reg_read(UC_X86_REG_ESP), SP + 4)
        return end - BASE

    @staticmethod
    def record(position=0, value=0x12345678, word=0x89ab, poison=0xa5):
        raw = bytearray([poison] * 17)
        raw[0], raw[1], raw[2] = 0x86, 3, position
        struct.pack_into('<HI', raw, 3, word, value)
        return bytes(raw)

    @staticmethod
    def state(marker=0, local_slot=0, poison=0xa5):
        entity = bytearray([poison] * 4096)
        struct.pack_into('<h', entity, 0x1a, marker)
        return model.State(3, local_slot, 0xfedcba98, bytes(entity))

    def compare(self, vm, record, state, at_end=True):
        expected = model.consume(record, state)
        pointer = INPUT_PAGE + (4096 - 17 if at_end else 0)
        vm.mem_write(INPUT_PAGE, b'\xcc' * 4096)
        vm.mem_write(pointer, record)
        vm.mem_write(BATTLE, b'\xa5' * 4096)
        vm.mem_write(BATTLE + 0x51, bytes([state.local_slot]))
        vm.mem_write(DISPATCH & ~4095, b'\xa5' * 4096)
        vm.mem_write(RESULT_RECORD, record)
        vm.mem_write(CACHED, struct.pack('<I', state.cached_dword))
        vm.mem_write(CONTEXT & ~4095, b'\0' * 4096)
        vm.mem_write(CONTEXT + 0x38 + record[2] * 24,
                     struct.pack('<I', ENTITY if state.entity is not None else 0))
        vm.mem_write(ENTITY, state.entity if state.entity is not None else b'\xa5' * 4096)
        pages = (BATTLE, DISPATCH & ~4095, CONTEXT & ~4095, ENTITY, INPUT_PAGE)
        before = {p: bytearray(vm.mem_read(p, 4096)) for p in pages}
        self.allowed_writes = ((RESULT_RECORD + 5, RESULT_RECORD + 9), (CACHED, CACHED + 4),
                               (ENTITY + 0xdb8, ENTITY + 0xdbc),
                               (ENTITY + 0x278, ENTITY + 0x27a))
        stop = self.run_native(vm, 0x114332, (0x126270, 0x1144b6),
            registers=((UC_X86_REG_EBP, pointer), (UC_X86_REG_EDI, RESULT_RECORD),
                       (UC_X86_REG_ESI, BATTLE)))
        self.assertEqual(stop, expected.next_consumer or 0x1144b6)
        self.assertTrue({0x1144b1, 0x117480, 0x12c3e0, 0x11e6e0} <= set(self.trace))
        struct.pack_into('<I', before[DISPATCH & ~4095], CACHED & 4095,
                         expected.cached_dword)
        result_offset = RESULT_RECORD & 4095
        before[DISPATCH & ~4095][result_offset:result_offset + 17] = expected.record
        if expected.entity is not None:
            before[ENTITY][:] = expected.entity
        for page in pages:
            self.assertEqual(bytes(vm.mem_read(page, 4096)), bytes(before[page]))
        wanted = []
        value = struct.unpack_from('<I', expected.record, 5)[0]
        if record[5] & 1:
            wanted.append((RESULT_RECORD + 5, 4, 1))
        if expected.side == 0 and expected.slot == state.local_slot:
            wanted.append((CACHED, 4, value))
        if expected.next_consumer:
            wanted += [(ENTITY + 0xdb8, 4, value),
                       (ENTITY + 0x278, 2, struct.unpack_from('<H', record, 3)[0])]
            self.assertEqual(vm.reg_read(UC_X86_REG_ECX), CONTEXT)
            stack = vm.reg_read(UC_X86_REG_ESP)
            self.assertEqual(struct.unpack('<II', vm.mem_read(stack, 8)),
                             (BASE + 0x12c421, ENTITY))
        self.assertEqual(self.writes, wanted)
        input_reads = [(address - pointer, size) for address, size in self.reads
                       if pointer <= address < pointer + 17]
        self.assertEqual(input_reads, [(0, 1)])
        result_reads = [(address - RESULT_RECORD, size) for address, size in self.reads
                        if RESULT_RECORD <= address < RESULT_RECORD + 17]
        wanted_reads = [(1, 1), (2, 1), (5, 1)]
        if expected.side == 0 and expected.slot == state.local_slot:
            wanted_reads.append((5, 4))
        if expected.next_consumer:
            wanted_reads += [(5, 4), (3, 2)]
        self.assertEqual(result_reads, wanted_reads)
        return expected

    def test_native_size_receive_and_state_dispatch(self):
        vm = self.machine()
        self.run_native(vm, 0x1200, args=(0x86,))
        self.assertEqual(vm.reg_read(UC_X86_REG_EAX), 17)
        self.assertEqual(struct.unpack_from('<I', self.image, 0x1324 + 4 * 0x86)[0],
                         BASE + 0x124c)
        pointer = INPUT_PAGE
        vm.mem_write(pointer, self.record())
        self.run_native(vm, 0x1193c4, (0x1195b1,),
                        registers=((UC_X86_REG_ESI, pointer),))
        self.assertEqual(self.image[0x119a04 + 0x86], 3)
        self.assertEqual(self.image[0x11465c + 0x86 - 0x1c], 5)
        self.run_native(vm, 0x114321, (0x11432d,), registers=(
            (UC_X86_REG_ESI, BATTLE), (UC_X86_REG_EAX, 17),
            (UC_X86_REG_EBX, BATTLE + 0xa9ea4b0)))
        self.assertEqual(vm.reg_read(UC_X86_REG_EDI), RESULT_RECORD)
        self.assertEqual(vm.reg_read(UC_X86_REG_ECX), BATTLE + 0xa9ea4b0)
        self.assertEqual(struct.unpack('<III', vm.mem_read(SP - 12, 12)),
                         (RESULT_RECORD, 17, 0))
        for state, target in enumerate((0x11447a, 0x11449e, 0x1144d8,
                                        0x1144ae, 0x1144c8, 0x1144be, 0x11447a)):
            vm.mem_write(DISPATCH, bytes([state]))
            self.run_native(vm, 0x114332, (target,), registers=(
                (UC_X86_REG_EBP, pointer), (UC_X86_REG_ESI, BATTLE)))

    def test_native_all_positions_and_local_mirror(self):
        vm = self.machine()
        for position in range(28):
            for local in range(14):
                self.compare(vm, self.record(position), self.state(local_slot=local))

    def test_native_bit_patterns_and_word_widths(self):
        vm = self.machine()
        values = [0, 1, 2, 3, 0x7fffffff, 0x80000000, 0xfffffffe, 0xffffffff]
        values += [1 << bit for bit in range(32)] + [(1 << bit) | 1 for bit in range(32)]
        for value in values:
            for word in (0, 1, 0x7fff, 0x8000, 0xffff):
                for position in (0, 13, 14, 27):
                    self.compare(vm, self.record(position, value, word), self.state())

    def test_native_null_and_signed_entity_gate(self):
        vm = self.machine()
        for marker in (-32768, -1, 0, 1, 32767):
            for value in (0, 3, 0x80000000, 0xffffffff):
                for position in (0, 14, 27):
                    state = self.state(marker)
                    self.compare(vm, self.record(position, value), state)
                    self.compare(vm, self.record(position, value), replace(state, entity=None))

    def test_native_opaque_bytes_and_input_page_edges(self):
        vm = self.machine()
        for offset in range(9, 17):
            for value in range(256):
                raw = bytearray(self.record())
                raw[offset] = value
                self.compare(vm, bytes(raw), self.state(), at_end=bool(value & 1))

    def test_native_explicit_random_snapshots(self):
        vm = self.machine()
        rng = random.Random(0x86117480)
        for _ in range(256):
            entity = rng.randbytes(4096)
            state = model.State(3, rng.randrange(14), rng.getrandbits(32), entity)
            raw = bytearray(rng.randbytes(17))
            raw[0], raw[1], raw[2] = 0x86, 3, rng.randrange(28)
            self.compare(vm, bytes(raw), state)

    def test_exact_next_consumer_reads_transmitted_bits(self):
        vm = self.machine()
        self.compare(vm, self.record(value=0x80000040), self.state())
        # Continue the existing native call stack, stopping after the +DB8 load.
        self.stops = {0x126289}
        self.trace.clear()
        self.reads.clear()
        vm.emu_start(BASE + 0x126270, RETURN, count=100)
        self.assertEqual(vm.reg_read(UC_X86_REG_EIP), BASE + 0x126289)
        self.assertEqual(vm.reg_read(UC_X86_REG_EDX), 0x80000040)
        self.assertIn((ENTITY + 0xdb8, 4), self.reads)

    def test_research_bounds_fail_closed(self):
        raw, state = self.record(), self.state()
        for length in range(17):
            with self.assertRaises(ValueError):
                model.consume(raw[:length], state)
        for bad in (raw + b'\0', raw * 2, b'\x14\0' + raw + b'\0', bytearray(raw)):
            with self.assertRaises(ValueError):
                model.consume(bad, state)
        for opcode in range(256):
            if opcode != 0x86:
                with self.assertRaises(ValueError):
                    model.consume(bytes([opcode]) + raw[1:], state)
        for position in range(28, 256):
            with self.assertRaises(ValueError):
                model.consume(self.record(position), state)
        for discriminator in range(256):
            if discriminator != 3:
                with self.assertRaises(ValueError):
                    model.consume(raw[:1] + bytes([discriminator]) + raw[2:], state)
        for change in ({'dispatch_state': 0}, {'dispatch_state': True},
                       {'local_slot': 14}, {'local_slot': -1},
                       {'cached_dword': -1}, {'cached_dword': 2**32},
                       {'entity': b''}, {'entity': bytearray(4096)}):
            with self.assertRaises(ValueError):
                replace(state, **change)
        with self.assertRaises(ValueError):
            model.consume(raw, None)


if __name__ == '__main__':
    unittest.main()
