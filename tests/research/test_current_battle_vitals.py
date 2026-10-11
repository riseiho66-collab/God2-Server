"""Continuous 86 -> actor -> role vitals stores; explicit offline operands only."""
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_current_battle_scalar_result as scalar
from tools.strike_lab import current_role_progression as progression
from unicorn import x86_const as reg

ROLE, COMPANION, BANK, TEXT = 0x6300000, 0x6400000, 0x6500000, 0x6700000
UI = scalar.AUX + 0x100


class CurrentBattleVitalsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        scalar.CurrentBattleScalarResultTests.setUpClass()
        cls.source = progression.evidence(ROOT.parent / 'God2')

    def prepare(self, slot=0, *, old_hp=100, companion_hp=None):
        n = scalar.CurrentBattleScalarResultTests()
        n.ranges = scalar.RANGES + ((0xe71e0, 0xe72a6), (0xac132, 0xac1a4))
        vm = n.machine()
        for address in (ROLE, COMPANION, UI + 0x86888, UI + 0xcff70,
                        UI + 0x232e50, BANK + 0xb2c68, TEXT, TEXT + 0x1000):
            n.map_page(vm, address)
        vm.mem_write(scalar.BATTLE, b'\xa5' * 4096)
        vm.mem_write(scalar.CONTEXT & ~4095, bytes(4096))
        vm.mem_write(scalar.RECORD & ~4095, b'\xa5' * 4096)
        vm.mem_write(scalar.BATTLE + 0x51, bytes([slot]))
        vm.mem_write(scalar.BATTLE + 0x76, b'\x7b')
        vm.mem_write(scalar.BATTLE + 0x20, struct.pack('<I', UI))
        vm.mem_write(scalar.BATTLE + 0xa9e9c40, struct.pack('<I', 0x12345678))
        vm.mem_write(scalar.ENTITY, n.entity(handle=-1))
        vm.mem_write(scalar.CONTEXT + 0x38 + slot * 24, struct.pack('<I', scalar.ENTITY))
        vm.mem_write(UI + 0x86888, struct.pack('<I', ROLE))
        vm.mem_write(ROLE, b'\xa5' * 4096)
        vm.mem_write(COMPANION, b'\x3c' * 4096)
        vm.mem_write(ROLE + 0x5c, struct.pack('<I', old_hp))
        vm.mem_write(ROLE + 0xd0, struct.pack('<I', 0 if companion_hp is None else COMPANION))
        if companion_hp is not None:
            vm.mem_write(COMPANION + 0x2c, struct.pack('<I', companion_hp))
        n.allowed = ((scalar.ENTITY + 0xde8, scalar.ENTITY + 0xdf8),
                     (ROLE + 0x5c, ROLE + 0x6c), (COMPANION + 0x2c, COMPANION + 0x30))
        return n, vm

    def dispatch(self, n, vm, raw):
        vm.mem_write(scalar.INPUT, raw)
        vm.mem_write(scalar.RECORD, raw)
        before = {page: bytearray(vm.mem_read(page, 4096)) for page in n.pages
                  if not scalar.STACK <= page < scalar.STACK + 0x4000}
        stop = n.execute(vm, 0x114332,
            registers=(('EBP', scalar.INPUT), ('EDI', scalar.RECORD), ('ESI', scalar.BATTLE)),
            stops=(0xe72a6, 0x114482, 0x1144a6, 0x12d8c0))
        for address, size, value in n.writes:
            for index, byte in enumerate(value.to_bytes(size, 'little')):
                at = address + index
                before[at & ~4095][at & 4095] = byte
        for page, expected in before.items():
            self.assertEqual(bytes(vm.mem_read(page, 4096)), expected)
        self.assertEqual(bytes(vm.mem_read(scalar.BASE, len(n.image))), n.image)
        return stop

    @staticmethod
    def words(vm, address, offsets):
        return tuple(struct.unpack('<I', vm.mem_read(address + offset, 4))[0] for offset in offsets)

    def test_both_kinds_continuously_reach_named_role_stores_all_local_slots(self):
        for slot in range(14):
            n, vm = self.prepare(slot)
            for kind in (0, 1):
                with self.subTest(slot=slot, kind=kind):
                    raw = n.record(kind, slot, value5=901 + kind, value9=83 + kind)
                    self.assertEqual(self.dispatch(n, vm, raw), 0xe72a6)
                    self.assertIn((0x117309, 0x11745e)[kind], n.trace)
                    self.assertIn(0xe71e0, n.trace)
                    self.assertNotIn(0xe725e, n.trace)  # Both callers supply mode zero.
                    self.assertEqual(n.trace.count(0x11e6e0), 2)
                    values = self.words(vm, scalar.ENTITY, (0xde8, 0xdec, 0xdf0, 0xdf4))
                    self.assertEqual(values, (83, 47, 901, 203) if kind == 0 else (83, 84, 901, 902))
                    self.assertEqual(self.words(vm, ROLE, (0x5c, 0x64, 0x60, 0x68)), values)
                    self.assertEqual(n.writes, [
                        (scalar.ENTITY + 0xde8 + 4 * kind, 4, 83 + kind),
                        (scalar.ENTITY + 0xdf0 + 4 * kind, 4, 901 + kind),
                        *((ROLE + offset, 4, value) for offset, value in
                          zip((0x5c, 0x64, 0x60, 0x68), values))])
                    self.assertNotIn(0xe72b9, n.trace)  # UI continuation is not emulated.

    def test_full_unsigned_widths_are_copied_not_clamped_or_generated(self):
        values = (0, 1, 0x7fffffff, 0x80000000, 0xffffffff)
        n, vm = self.prepare()
        for kind in (0, 1):
            for current in values:
                for maximum in values:
                    raw = n.record(kind, 0, maximum, current)
                    self.assertEqual(self.dispatch(n, vm, raw), 0xe72a6)
                    offsets = (0x5c, 0x60) if kind == 0 else (0x64, 0x68)
                    self.assertEqual(self.words(vm, ROLE, offsets), (current, maximum))

    def test_hp_restoration_alone_preserves_death_presentation_state(self):
        n, vm = self.prepare(old_hp=0)
        vm.mem_write(scalar.ENTITY + 0xde8, struct.pack('<I', 0))
        vm.mem_write(scalar.ENTITY + 0x1eb, b'\x09')
        vm.mem_write(scalar.ENTITY + 0x232, b'\x09')
        for hp in (1,36,120):
            self.assertEqual(self.dispatch(n, vm, n.record(0,0,120,hp)), 0xe72a6)
            self.assertEqual(self.words(vm,scalar.ENTITY,(0xde8,)), (hp,))
            self.assertEqual(self.words(vm,ROLE,(0x5c,)), (hp,))
            self.assertEqual(bytes(vm.mem_read(scalar.ENTITY+0x1eb,1)), b'\x09')
            self.assertEqual(bytes(vm.mem_read(scalar.ENTITY+0x232,1)), b'\x09')

    def test_real_hp_decrease_branch_updates_companion_and_mp_does_not_repeat_it(self):
        for new_hp, remaining in ((80, 30), (20, 0), (100, 50), (120, 50)):
            n, vm = self.prepare(old_hp=100, companion_hp=50)
            self.assertEqual(self.dispatch(n, vm, n.record(0, 0, 900, new_hp)), 0xe72a6)
            self.assertEqual(self.words(vm, COMPANION, (0x2c,)), (remaining,))
            self.assertEqual(self.dispatch(n, vm, n.record(1, 0, 800, 77)), 0xe72a6)
            self.assertEqual(self.words(vm, COMPANION, (0x2c,)), (remaining,))
            self.assertFalse(any(COMPANION <= address < COMPANION + 4096 for address, _, _ in n.writes))

    def test_nonlocal_or_negative_actor_marker_skips_role_callback(self):
        for kind in (0, 1):
            for negative_marker in (False, True):
                n, vm = self.prepare()
                if negative_marker:
                    vm.mem_write(scalar.ENTITY + 0x1a, struct.pack('<h', -1))
                else:
                    vm.mem_write(scalar.BATTLE + 0x51, b'\x01')
                before = bytes(vm.mem_read(ROLE, 4096))
                self.assertEqual(self.dispatch(n, vm, n.record(kind)), (0x114482, 0x1144a6)[kind])
                self.assertNotIn(0xe71e0, n.trace)
                self.assertEqual(bytes(vm.mem_read(ROLE, 4096)), before)

    def test_original_message_and_printf_arguments_name_retained_native_values(self):
        n, vm = self.prepare()
        for kind, current, maximum in ((0, 83, 901), (1, 84, 902)):
            self.assertEqual(self.dispatch(n, vm, n.record(kind, 0, maximum, current)), 0xe72a6)
        role_before = bytes(vm.mem_read(ROLE, 4096))
        vm.mem_write(UI + 0xcff70, struct.pack('<I', BANK))
        vm.mem_write(UI + 0x232e50, struct.pack('<h', 7))
        vm.mem_write(BANK + 0xb2c68, struct.pack('<IH', TEXT, 164))
        rows = self.source['source_schema']['ProgramMsg']['records']
        messages = {int(bytes.fromhex(row['fields_hex'][0])):
                    bytes.fromhex(row['fields_hex'][1]) + b'\0' for row in rows}
        self.assertEqual(messages[163].hex(), 'a6e5b6713a2025642f256400')
        self.assertEqual(messages[164].hex(), 'aa6bb34e3a2025642f256400')
        for msgid, start, stop, control, current, maximum in (
                (163, 0xac132, 0xac167, 2, 83, 901), (164, 0xac16c, 0xac1a4, 3, 84, 902)):
            address = TEXT + 0x1000 + (msgid - 163) * 0x100
            vm.mem_write(TEXT + 4 * (msgid - 1), struct.pack('<I', address))
            vm.mem_write(address, messages[msgid])
            # Independent display-reader slice; no fake return from the prior UI call.
            n.allowed = ()
            self.assertEqual(n.execute(vm, start,
                registers=(('ESI', UI), ('EBX', ROLE), ('EDI', UI + 0xe2170)), stops=(stop,)), stop)
            sp = vm.reg_read(reg.UC_X86_REG_ESP)
            args = struct.unpack('<6I', vm.mem_read(sp, 24))
            self.assertEqual(args[:1] + args[2:], (UI + 0xe2170, control, address, current, maximum))
            self.assertEqual(args[1] & 0xffff, 7)
            self.assertEqual(bytes(vm.mem_read(args[3], len(messages[msgid]))), messages[msgid])
            self.assertEqual(n.writes, [])
            self.assertEqual(bytes(vm.mem_read(ROLE, 4096)), role_before)


if __name__ == '__main__':
    unittest.main()
