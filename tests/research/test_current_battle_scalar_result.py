"""Current raw image only; continuous native calls with explicit stop boundaries."""
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
from tools.strike_lab import current_battle_scalar_result as model
from unicorn import (Uc, UC_ARCH_X86, UC_MODE_32, UC_PROT_READ, UC_PROT_EXEC,
                     UC_HOOK_CODE, UC_HOOK_MEM_WRITE, UC_HOOK_MEM_READ)
from unicorn import x86_const as reg

BASE, STACK, SP, RETURN = 0x400000, 0x3000000, 0x3002000, 0x3003000
BATTLE, ENTITY, INPUT, AUX = 0x5000000, 0x6000000, 0x6100000, 0x6200000
CONTEXT, RECORD = BATTLE + 0x144938, BATTLE + 0xa9e9cb0
MANAGER = CONTEXT + 0x310
RANGES = ((0x114332, 0x114358), (0x114464, 0x114482),
          (0x11449e, 0x1144a6), (0x117230, 0x11739c),
          (0x1173a0, 0x117472), (0x11e6e0, 0x11e76a),
          (0x12d840, 0x12d8b5), (0x12d970, 0x12d9e5),
          (0x108f50, 0x108fb1), (0x108fc0, 0x108ffe),
          (0x108e70, 0x108f48), (0x149630, 0x149657))


class CurrentBattleScalarResultTests(unittest.TestCase):
    ranges = RANGES

    @classmethod
    def setUpClass(cls):
        cls.image = (ROOT / 'artifacts/capture_work/host-20260918-1430/output/'
                     'native-master-01-stable.bin').read_bytes()
        if hashlib.sha256(cls.image).hexdigest() != model.IMAGE_SHA256:
            raise AssertionError('Current image hash mismatch; re-audit required')

    def machine(self):
        vm = Uc(UC_ARCH_X86, UC_MODE_32)
        vm.mem_map(BASE, (len(self.image) + 4095) & ~4095, UC_PROT_READ | UC_PROT_EXEC)
        vm.mem_write(BASE, self.image)
        self.pages = set()
        for address in (STACK, STACK + 4096, STACK + 8192, STACK + 12288,
                        BATTLE, ENTITY, INPUT, AUX, CONTEXT, RECORD,
                        BATTLE + 0x83458):
            self.map_page(vm, address)
        self.stops, self.allowed = set(), ()
        self.trace, self.writes, self.reads, self.conversions = [], [], [], []

        def code(machine, address, size, _):
            rva = address - BASE
            if rva in self.stops:
                machine.emu_stop()
                return
            if not any(lo <= rva and rva + size <= hi for lo, hi in self.ranges):
                raise AssertionError(f'Unqualified native instruction {rva:X}')
            if rva in (0x108ed6, 0x108f2c):
                self.conversions.append((machine.reg_read(reg.UC_X86_REG_EDX) << 32) |
                                        machine.reg_read(reg.UC_X86_REG_EAX))
            self.trace.append(rva)

        def write(machine, access, address, size, value, _):
            if STACK <= address and address + size <= STACK + 0x3000:
                return
            if not any(lo <= address and address + size <= hi for lo, hi in self.allowed):
                raise AssertionError(f'Unexpected native write {address:X}/{size}')
            self.writes.append((address, size, value & ((1 << (size * 8)) - 1)))

        def read(machine, access, address, size, value, _):
            self.reads.append((address, size))

        vm.hook_add(UC_HOOK_CODE, code)
        vm.hook_add(UC_HOOK_MEM_WRITE, write)
        vm.hook_add(UC_HOOK_MEM_READ, read)
        return vm

    def map_page(self, vm, address):
        page = address & ~4095
        if page not in self.pages:
            vm.mem_map(page, 4096)
            self.pages.add(page)

    def execute(self, vm, entry, args=(), registers=(), stops=(), callee_pop=0, cw=0x037f,
                instruction_limit=4000):
        self.trace.clear()
        self.writes.clear()
        self.reads.clear()
        self.conversions.clear()
        self.stops = set(stops)
        vm.mem_write(STACK, b'\xa5' * 0x3000)
        vm.mem_write(SP, struct.pack('<' + 'I' * (len(args) + 1), RETURN, *args))
        for name in ('EAX', 'EBX', 'ECX', 'EDX', 'ESI', 'EDI', 'EBP'):
            vm.reg_write(getattr(reg, 'UC_X86_REG_' + name), 0xa5a50000)
        vm.reg_write(reg.UC_X86_REG_ESP, SP)
        vm.reg_write(reg.UC_X86_REG_EFLAGS, 2)
        vm.reg_write(reg.UC_X86_REG_FPCW, cw)
        vm.reg_write(reg.UC_X86_REG_FPSW, 0)
        vm.reg_write(reg.UC_X86_REG_FPTAG, 0xffff)
        for name, value in registers:
            vm.reg_write(getattr(reg, 'UC_X86_REG_' + name), value)
        vm.emu_start(BASE + entry, RETURN, count=instruction_limit)
        end = vm.reg_read(reg.UC_X86_REG_EIP)
        self.assertIn(end, {RETURN} | {BASE + stop for stop in stops})
        if end == RETURN:
            self.assertEqual(vm.reg_read(reg.UC_X86_REG_ESP), SP + 4 + callee_pop)
        self.assertEqual(vm.reg_read(reg.UC_X86_REG_FPCW), cw)
        return end - BASE

    @staticmethod
    def display(handles=(-1, -1), divisors=(101, 203), numerators=(79, 59), width=83):
        return model.Display(handles, width, 12, divisors, numerators)

    @staticmethod
    def entity(handle=0, marker=0, scalars=(31, 47, 101, 203)):
        raw = bytearray(b'\xa5' * 4096)
        struct.pack_into('<h', raw, 0x1a, marker)
        struct.pack_into('<h', raw, 0x1d8, handle)
        struct.pack_into('<4I', raw, 0xde8, *scalars)
        return bytes(raw)

    @staticmethod
    def record(kind=0, position=0, value5=109, value9=83):
        raw = bytearray(b'\x5a' * 17)
        raw[:3] = bytes((0x86, kind, position))
        struct.pack_into('<II', raw, 5, value5, value9)
        return bytes(raw)

    @staticmethod
    def display_bytes(display):
        return (struct.pack('<2h', *display.handles) + b'\xa5' * 4 +
                struct.pack('<2h4I', display.width, display.height,
                            *display.divisors, *display.numerators))

    def install_display(self, vm, handle, display):
        pointer = MANAGER + 0x1c + (handle & 0xffff) * 0xa7e0
        tail = pointer + 0xa79c
        self.map_page(vm, tail)
        self.map_page(vm, tail + 27)
        vm.mem_write(tail, self.display_bytes(display))
        return pointer

    def check_draw(self, vm, draw, display):
        sp = vm.reg_read(reg.UC_X86_REG_ESP)
        back, handle, rect = struct.unpack('<III', vm.mem_read(sp, 12))
        self.assertEqual(back - BASE, (0x108ee8, 0x108f3e)[draw.channel])
        self.assertEqual(handle & 0xffff, display.handles[draw.channel])
        words = struct.unpack('<4I', vm.mem_read(rect, 16))
        self.assertEqual(words[2], draw.extent_bits)
        self.assertEqual(self.conversions, [draw.quotient & 0xffffffffffffffff])
        if draw.channel == 0:
            self.assertEqual((words[0], words[1], words[3]), (0, 0, display.height & 0xffffffff))
        else:
            self.assertEqual((words[0], words[1], words[3]), (0xa5a5a5a5,) * 3)
        self.assertIn(0x149630, self.trace)

    def compare(self, vm, raw, state):
        expected = model.consume(raw, state)
        vm.mem_write(BATTLE, b'\xa5' * 4096)
        vm.mem_write(CONTEXT & ~4095, bytes(4096))
        vm.mem_write(RECORD & ~4095, b'\xa5' * 4096)
        vm.mem_write(INPUT, raw)
        vm.mem_write(RECORD, raw)
        vm.mem_write(BATTLE + 0x51, bytes([state.local_slot]))
        vm.mem_write(BATTLE + 0x76, b'\x7b')
        vm.mem_write(BATTLE + 0x20, struct.pack('<I', AUX + 0x100))
        vm.mem_write(BATTLE + 0xa9e9c40, struct.pack('<I', 0x12345678))
        vm.mem_write(BATTLE + 0x83458, struct.pack('<I', AUX))
        vm.mem_write(AUX, struct.pack('<I', 0x89abcdef))
        vm.mem_write(ENTITY, state.entity or b'\xa5' * 4096)
        vm.mem_write(CONTEXT + 0x38 + raw[2] * 24,
                     struct.pack('<I', ENTITY if state.entity is not None else 0))
        handle = struct.unpack_from('<h', state.entity, 0x1d8)[0] if state.entity else -1
        pointer = self.install_display(vm, handle, state.display) if 0 <= handle < 4096 else None
        before = {page: bytearray(vm.mem_read(page, 4096)) for page in self.pages
                  if not STACK <= page < STACK + 0x4000}
        self.allowed = ((ENTITY + 0xde8, ENTITY + 0xdf8),)
        if pointer is not None:
            self.allowed += ((pointer + 0xa7a8, pointer + 0xa7b8),)
        stop = self.execute(vm, 0x114332, registers=(('EBP', INPUT), ('EDI', RECORD),
                           ('ESI', BATTLE)), stops=(0x114482, 0x1144a6, 0x1bdc0, 0xe71e0, 0x12d8c0))
        self.assertEqual(stop, expected.next_consumer or (0x114482, 0x1144a6)[raw[1]])
        self.assertIn((0x117230, 0x1173a0)[raw[1]], self.trace)
        if state.entity is not None and raw[2] < 14:
            self.assertIn((0x12d840, 0x12d970)[raw[1]], self.trace)
            self.assertEqual(self.trace.count(0x11e6e0), 2)
        if expected.entity is not None:
            before[ENTITY][:] = expected.entity
        if pointer is not None:
            blob = self.display_bytes(expected.display)
            for index, byte in enumerate(blob):
                address = pointer + 0xa79c + index
                before[address & ~4095][address & 4095] = byte
        for page, blob in before.items():
            self.assertEqual(bytes(vm.mem_read(page, 4096)), bytes(blob))
        entity_writes = [entry for entry in self.writes if ENTITY <= entry[0] < ENTITY + 4096]
        self.assertEqual(entity_writes, [] if state.entity is None or raw[2] >= 14 else [
            (ENTITY + 0xde8 + raw[1] * 4, 4, struct.unpack_from('<I', raw, 9)[0]),
            (ENTITY + 0xdf0 + raw[1] * 4, 4, struct.unpack_from('<I', raw, 5)[0])])
        wanted_writes = list(entity_writes)
        if pointer is not None and state.entity is not None and raw[2] < 14:
            n0, n1, d0, d1 = struct.unpack_from('<4I', expected.entity, 0xde8)
            wanted_writes += [(pointer + 0xa7a8, 4, d0), (pointer + 0xa7ac, 4, d1)]
            if expected.draw is None:
                for offset, value, limit in ((0xa7b0, n0, d0), (0xa7b4, n1, d1)):
                    wanted_writes.append((pointer + offset, 4, value))
                    if value > limit:
                        wanted_writes.append((pointer + offset, 4, limit))
                self.assertEqual(self.trace.count(0x108e70), 2)
                self.assertLess(self.trace.index(0x108fc0), self.trace.index(0x108f50))
        self.assertEqual(self.writes, wanted_writes)
        self.assertEqual([(a - INPUT, size) for a, size in self.reads
                          if INPUT <= a < INPUT + 17], [(0, 1)])
        for address, size in self.reads:
            if RECORD <= address < RECORD + 17:
                self.assertIn((address - RECORD, size), ((1, 1), (2, 1), (5, 4), (9, 4)))
        if expected.draw:
            self.check_draw(vm, expected.draw, expected.display)
            self.assertNotIn(0x108f50, self.trace)  # Divisor render is earlier than clamp.
        if expected.local_scalars:
            sp = vm.reg_read(reg.UC_X86_REG_ESP)
            back, payload, context, mode, flag = struct.unpack('<5I', vm.mem_read(sp, 20))
            self.assertEqual(back - BASE, (0x11730e, 0x117463)[raw[1]])
            self.assertEqual(struct.unpack('<4I', vm.mem_read(payload, 16)), expected.local_scalars)
            self.assertEqual((context, mode & 255, flag & 255), (0x12345678, 0x7b, 0))
            self.assertEqual(vm.reg_read(reg.UC_X86_REG_ECX), AUX + 0x100)
        if expected.next_consumer == 0x12d8c0:
            sp = vm.reg_read(reg.UC_X86_REG_ESP)
            args = struct.unpack('<6I', vm.mem_read(sp, 24))
            self.assertEqual(args[:3], (BASE + 0x11738d, 0x89abcdef, 1))
            self.assertEqual(args[3] & 255, raw[2] % 14)
            self.assertEqual(args[4:], tuple(reversed(struct.unpack_from('<II', raw, 5))))
        return expected

    def test_dispatch_layout_all_positions_and_entity_gates(self):
        vm = self.machine()
        self.assertEqual(struct.unpack_from('<2I', self.image, 0x1146cc),
                         (BASE + 0x11447a, BASE + 0x11449e))
        for kind in (0, 1):
            for position in range(28):
                for marker in (-32768, -1, 0, 32767):
                    for local in (0, position % 14, 13):
                        state = model.State(local, self.entity(marker=marker), self.display())
                        self.compare(vm, self.record(kind, position), state)
                self.compare(vm, self.record(kind, position), model.State(0, None, self.display()))

    def test_raw_scalar_widths_unsigned_clamps_and_handle_gates(self):
        vm = self.machine()
        values = (0, 1, 101, 0x7fffffff, 0x80000000, 0xfffffffe, 0xffffffff)
        for kind in (0, 1):
            for handle in (-32768, -1, 0, 1, 4095, 4096, 32767):
                for a in values:
                    for b in values:
                        state = model.State(13, self.entity(handle, scalars=(a, b, b, a)),
                                            self.display())
                        self.compare(vm, self.record(kind, 0, a, b), state)

    def test_continuous_divisor_render_stops_before_clamp(self):
        vm = self.machine()
        for kind in (0, 1):
            for handles in ((7, 8), (-1, 8)):
                for width in (-32768, -99, 0, 83, 32767):
                    for divisor in (1, 3, 0x7fffffff, 0x80000000, 0xffffffff):
                        display = self.display(handles, numerators=(0xffffffff, 99), width=width)
                        state = model.State(0, self.entity(scalars=(1, 2, divisor, divisor)), display)
                        self.compare(vm, self.record(kind, value5=divisor, value9=17), state)

    def test_native_direct_clamp_to_display_rounding_and_low_dword(self):
        vm = self.machine()
        for handles in ((7, -1), (-1, 8), (-1, -1)):
            for width in (-32768, -99, 0, 83, 32767):
                for divisor in (1, 3, 100, 0x7fffffff, 0x80000000, 0xffffffff):
                    for cw in (0x037f, 0x077f, 0x0b7f, 0x0f7f):
                        display = self.display(handles, (divisor, divisor), width=width)
                        expected, draw = model.display_update(display, (0xffffffff, 33), clamp=True)
                        pointer = self.install_display(vm, 0, display)
                        self.allowed = ((pointer + 0xa7b0, pointer + 0xa7b8),)
                        stop = self.execute(vm, 0x108f50, (0, 0xffffffff, 33),
                            registers=(('ECX', MANAGER),), stops=(0x1bdc0,), callee_pop=12, cw=cw)
                        self.assertEqual(bytes(vm.mem_read(pointer + 0xa79c, 28)),
                                         self.display_bytes(expected))
                        if draw:
                            self.assertEqual(stop, 0x1bdc0)
                            self.check_draw(vm, draw, expected)
                        else:
                            self.assertEqual(stop, RETURN - BASE)

    def test_direct_helper_handle_low_word_and_invalid_return(self):
        vm = self.machine()
        for entry in (0x108fc0, 0x108f50):
            for handle in (0, 1, 4095, 0x12340001, 4096, 0xffff, 0xabcd1000):
                valid = (handle & 0xffff) < 4096
                display = self.display()
                pointer = self.install_display(vm, handle, display) if valid else None
                self.allowed = () if pointer is None else ((pointer + 0xa7a8, pointer + 0xa7b8),)
                self.execute(vm, entry, (handle, 0xffffffff, 0x80000000),
                             registers=(('ECX', MANAGER),), callee_pop=12)
                if valid:
                    expected, _ = model.display_update(display, (0xffffffff, 0x80000000),
                                                        clamp=entry == 0x108f50)
                    self.assertEqual(bytes(vm.mem_read(pointer + 0xa79c, 28)),
                                     self.display_bytes(expected))
                else:
                    self.assertEqual(self.writes, [])

    def test_native_visible_zero_divisor_reaches_unguarded_divide(self):
        vm = self.machine()
        for handles, stop in (((7, -1), 0x108ecd), ((-1, 8), 0x108f23)):
            pointer = self.install_display(vm, 0, self.display(handles))
            self.allowed = ((pointer + 0xa7a8, pointer + 0xa7b0),)
            self.assertEqual(self.execute(vm, 0x108fc0, (0, 0, 0),
                registers=(('ECX', MANAGER),), stops=(stop,)), stop)
            sp = vm.reg_read(reg.UC_X86_REG_ESP)
            self.assertEqual(bytes(vm.mem_read(sp + 0x10, 4)), bytes(4))
            self.assertNotIn(0x149630, self.trace)

    def test_opaque_record_bytes_and_random_explicit_state(self):
        vm = self.machine()
        for kind in (0, 1):
            for offset in (3, 4, 13, 14, 15, 16):
                for value in range(256):
                    raw = bytearray(self.record(kind))
                    raw[offset] = value
                    self.compare(vm, bytes(raw), model.State(0, self.entity(), self.display()))
        rng = random.Random(0x8612d840)
        for _ in range(256):
            raw = bytearray(rng.randbytes(17))
            raw[:3] = bytes((0x86, rng.randrange(2), rng.randrange(28)))
            scalars = tuple(rng.getrandbits(32) for _ in range(4))
            state = model.State(rng.randrange(14), self.entity(marker=-1, scalars=scalars),
                                self.display())
            self.compare(vm, bytes(raw), state)

    def test_same_actor_side_flip_exposes_packet_copy_not_base_stat_generation(self):
        for slot in range(14):
            with self.subTest(slot=slot):
                vm = self.machine()
                original = self.entity(handle=-1, marker=-1, scalars=(0xa5a5a5a5,) * 4)
                raw = self.record(kind=1, position=slot + 14,
                                  value5=0x11223344, value9=0x55667788)
                self.compare(vm, raw, model.State(13, original, self.display()))
                self.assertEqual(self.writes, [])
                self.assertNotIn(0x11e6e0, self.trace)
                self.assertEqual(bytes(vm.mem_read(ENTITY, 4096)), original)

                # Explicit diagnostic side change, not a native recruitment path.
                vm.mem_write(CONTEXT + 0x38 + (slot + 14) * 24, bytes(4))
                vm.mem_write(CONTEXT + 0x38 + slot * 24, struct.pack('<I', ENTITY))
                self.assertEqual(bytes(vm.mem_read(ENTITY, 4096)), original)
                expected = bytearray(original)
                for value5, value9 in ((0x11223344, 0x55667788), (0, 0xffffffff)):
                    ally_record = self.record(kind=1, position=slot,
                                              value5=value5, value9=value9)
                    vm.mem_write(INPUT, ally_record)
                    vm.mem_write(RECORD, ally_record)
                    stop = self.execute(vm, 0x114332,
                        registers=(('EBP', INPUT), ('EDI', RECORD), ('ESI', BATTLE)),
                        stops=(0x1144a6,))
                    self.assertEqual(stop, 0x1144a6)
                    self.assertIn(0x12d970, self.trace)
                    self.assertEqual(self.trace.count(0x11e6e0), 2)
                    self.assertEqual(self.writes, [(ENTITY + 0xdec, 4, value9),
                                                   (ENTITY + 0xdf4, 4, value5)])
                    struct.pack_into('<I', expected, 0xdec, value9)
                    struct.pack_into('<I', expected, 0xdf4, value5)
                    self.assertEqual(bytes(vm.mem_read(ENTITY, 4096)), bytes(expected))
                self.assertEqual(bytes(vm.mem_read(BASE, len(self.image))), self.image)

    def test_research_input_bounds_and_visible_zero_divisor(self):
        raw = self.record()
        state = model.State(0, self.entity(), self.display())
        for bad in [raw[:n] for n in range(17)] + [raw + b'\0', raw * 2, bytearray(raw)]:
            with self.assertRaises(ValueError):
                model.consume(bad, state)
        for offset, values in ((0, (0, 0x85, 0x87)), (1, range(2, 256)), (2, range(28, 256))):
            for value in values:
                bad = bytearray(raw)
                bad[offset] = value
                with self.assertRaises(ValueError):
                    model.consume(bytes(bad), state)
        with self.assertRaisesRegex(ValueError, 'zero-divisor'):
            model.display_update(self.display((0, -1)), (0, 1), clamp=False)
        for fields in ({'local_slot': 14}, {'entity': b''}, {'display': None}):
            with self.assertRaises(ValueError):
                replace(state, **fields)
        for fields in ({'handles': (32768, 0)}, {'width': -32769},
                       {'divisors': (-1, 2)}, {'numerators': (0, 2**32)}):
            with self.assertRaises(ValueError):
                replace(state.display, **fields)


if __name__ == '__main__':
    unittest.main()
