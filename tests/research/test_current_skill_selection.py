"""Current 0x38 native differential oracle; no processes, UI or code stubs."""
from dataclasses import replace
import hashlib
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'artifacts/tooling/crypto-oracle-python'))
from tools.strike_lab import current_skill_selection as selection
from tools.strike_lab import current_skill_identity as identity
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn import UC_PROT_READ, UC_PROT_EXEC
from unicorn.x86_const import (
    UC_X86_REG_EAX, UC_X86_REG_ECX, UC_X86_REG_EDX, UC_X86_REG_EBP,
    UC_X86_REG_ESI, UC_X86_REG_EDI, UC_X86_REG_EIP, UC_X86_REG_ESP,
)

BASE, STACK, SP, RETURN = 0x400000, 0x3000000, 0x3002000, 0x3003000
BATTLE = 0x5000000
SELECTOR = BATTLE + 0xa9dc198
AUX, INPUT, CATALOG = 0x6000000, 0x6100000, 0x6200000
OBJECT_SIZE = 0x3600


class CurrentSkillSelectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image = (ROOT / 'artifacts/capture_work/host-20260918-1430/output/'
                     'native-master-01-stable.bin').read_bytes()
        if hashlib.sha256(cls.image).hexdigest() != selection.IMAGE_SHA256:
            raise AssertionError('Pinned native image changed')
        cls.source = (ROOT.parent / 'God2' / identity.SOURCE).read_bytes()
        if hashlib.sha256(cls.source).hexdigest() != identity.SOURCE_SHA256:
            raise AssertionError('Pinned current definition source changed')

    def machine(self):
        vm = Uc(UC_ARCH_X86, UC_MODE_32)
        vm.mem_map(BASE, (len(self.image) + 4095) & ~4095,
                   UC_PROT_READ | UC_PROT_EXEC)
        vm.mem_write(BASE, self.image)
        for address, size in ((STACK, 0x4000), (SELECTOR & ~4095, 0x5000),
                              (AUX, 0x1000), (INPUT, 0x1000),
                              (CATALOG, 0x1c000)):
            vm.mem_map(address, size)
        vm.mem_protect(INPUT, 0x1000, UC_PROT_READ)
        vm.mem_write(CATALOG, self.source[4:])
        self.trace = []
        self.stops = set()

        def trace(machine, address, size, data):
            rva = address - BASE
            if rva in self.stops:
                machine.emu_stop()
                return
            allowed = ((0x1000, 0x1013), (0x1200, 0x1324),
                       (0x15840, 0x15850), (0x114332, 0x114358),
                       (0x114518, 0x114538), (0x117540, 0x11758b),
                       (0x11c520, 0x11c7bf), (0x11c7f0, 0x11c892),
                       (0x11c8e0, 0x11c92b), (0x11b8c0, 0x11b8fa),
                       (0x11b9a0, 0x11b9d9), (0x11ba90, 0x11bae2),
                       (0x1151a0, 0x1151d0), (0xb0290, 0xb02e8),
                       (0x1153b4, 0x11540f), (0x115421, 0x11542e),
                       (0x1154aa, 0x1154b1))
            if not any(lo <= rva and rva + size <= hi for lo, hi in allowed):
                raise AssertionError(f'Unexpected instruction RVA {rva:X}')
            if rva in (0x117540, 0x117560, 0x11c520, 0x11c7f0, 0x11c8e0):
                self.trace.append(rva)
        vm.hook_add(UC_HOOK_CODE, trace)
        return vm

    @staticmethod
    def banks(count, old=2, keys=None):
        return tuple(selection.Bank(
            keys[i] if keys is not None else 0x9000 + i, old,
            tuple(((j * 313 + i) & 0x7fff) | (0x8000 if j % 2 else 0)
                  for j in range(100)),
            bytes((j + i + 1) & 255 for j in range(100))) for i in range(count))

    def install(self, vm, banks, current):
        blob = bytearray(b'\xa5' * OBJECT_SIZE)
        blob[4:6] = bytes((current, len(banks)))
        struct.pack_into('<I', blob, 0x3518, CATALOG)
        for i, bank in enumerate(banks):
            offset = 0x10 + i * 0x2d0
            struct.pack_into('<I', blob, offset, 3)
            struct.pack_into('<100H', blob, offset + 4, *bank.words)
            blob[offset + 0x25c:offset + 0x2c0] = bank.auxiliary
            blob[offset + 0x2c0] = bank.state_byte
            struct.pack_into('<I', blob, offset + 0x2c4, AUX + i * 0x100)
            vm.mem_write(AUX + i * 0x100, struct.pack('<H', bank.key_word) + bytes(254))
        vm.mem_write(SELECTOR, bytes(blob))
        return blob

    def expected_blob(self, before, result):
        blob = bytearray(before)
        blob[4] = result.current_bank_byte
        for i, bank in enumerate(result.banks):
            offset = 0x10 + i * 0x2d0
            struct.pack_into('<100H', blob, offset + 4, *bank.words)
            blob[offset + 0x25c:offset + 0x2c0] = bank.auxiliary
            blob[offset + 0x2c0] = bank.state_byte
        return bytes(blob)

    def packet(self, vm, record):
        # Any forward overread past the exact record hits an unmapped page.
        pointer = INPUT + 0x1000 - len(record)
        vm.mem_write(pointer, record)
        return pointer

    def invoke(self, vm, entry, args=(), stops=(), seed=0xa5a50000, this=SELECTOR):
        self.stops = set(stops)
        self.trace.clear()
        vm.mem_write(SP, struct.pack('<' + 'I' * (len(args) + 1), RETURN, *args))
        vm.reg_write(UC_X86_REG_ESP, SP)
        vm.reg_write(UC_X86_REG_ECX, this)
        vm.reg_write(UC_X86_REG_EAX, seed)
        vm.reg_write(UC_X86_REG_EDX, seed ^ 0xffffffff)
        vm.emu_start(BASE + entry, RETURN, count=10000)
        end = vm.reg_read(UC_X86_REG_EIP)
        self.assertIn(end, {RETURN} | {BASE + stop for stop in stops})
        if end == RETURN:
            self.assertEqual(vm.reg_read(UC_X86_REG_ESP), SP + 4 + 4 * len(args))
        return vm.reg_read(UC_X86_REG_EAX)

    def compare(self, vm, banks, current, payload, seed=0xa5a50000):
        record = bytes((0x38, payload))
        before = self.install(vm, banks, current)
        expected = selection.apply_selection_record(record, banks, current)
        returned = self.invoke(vm, 0x11c7f0, (self.packet(vm, record) + 1,), seed=seed)
        self.assertEqual(struct.unpack('<h', struct.pack('<H', returned & 65535))[0],
                         expected.returned_index, (current, payload))
        self.assertEqual(bytes(vm.mem_read(SELECTOR, OBJECT_SIZE)),
                         self.expected_blob(before, expected), (current, payload))
        self.assertEqual(self.trace.count(0x11c8e0),
                         int(payload >> 5 == 2 and payload & 31 < len(banks)))
        return expected

    def test_all_payloads_bank_count_boundaries_and_full_object_writes(self):
        vm = self.machine()
        for count in range(17):
            banks = self.banks(count)
            for payload in range(256):
                self.compare(vm, banks, 15, payload)

    def test_all_previous_state_bytes_and_signed_current_byte_boundaries(self):
        vm = self.machine()
        for old in range(256):
            banks = self.banks(1, old)
            for payload in (0, 0x40, 0xe0):
                self.compare(vm, banks, 0, payload)
        banks = self.banks(16)
        for current in (0, 7, 15, 16, 127, 128, 255):
            for payload in range(256):
                self.compare(vm, banks, current, payload, seed=0x1234ffff)

    def test_duplicate_keys_skip_current_and_return_input_not_selected_bank(self):
        vm = self.machine()
        for keys in ((7, 7, 7), (0, 65535, 0), (0x8000, 1, 0x8000)):
            banks = self.banks(3, keys=keys)
            for current in (0, 1, 2, 255):
                for bank in range(3):
                    self.compare(vm, banks, current, 0x40 | bank)
        result = self.compare(vm, self.banks(3, keys=(7, 7, 7)), 0, 0x42)
        self.assertEqual((result.current_bank_byte, result.returned_index), (1, 2))

    def test_no_switch_can_still_mutate_state_and_clear_all_physical_slots(self):
        vm = self.machine()
        result = self.compare(vm, self.banks(1), 0, 0)
        self.assertEqual(result.returned_index, -1)
        self.assertEqual(result.banks[0].state_byte, 0)
        self.assertEqual(result.banks[0].auxiliary, bytes(100))
        self.assertTrue(all(word < 0x8000 for word in result.banks[0].words))
        # Only 3 entries are count-declared in the fixture; slot 99 was cleared too.
        self.assertEqual(result.banks[0].words[99], 99 * 313)

    def test_native_dispatch_sizes_and_wrapper_notification_boundary(self):
        vm = self.machine()
        for opcode, size, arm in ((0x38, 2, 0x114525), (0x87, 3, 0x114518)):
            self.assertEqual(self.invoke(vm, 0x15840, (opcode,)), size)
            index = self.image[0x11465c + opcode - 0x1c]
            self.assertEqual(struct.unpack_from('<I', self.image,
                                               0x114634 + index * 4)[0], BASE + arm)
        for payload in (0x41, 0x40, 0x01, 0xff):
            banks = self.banks(2)
            before = self.install(vm, banks, 0)
            record = bytes((0x38, payload))
            expected = selection.apply_selection_record(record, banks, 0)
            pointer = self.packet(vm, record)
            vm.reg_write(UC_X86_REG_EBP, pointer)
            vm.reg_write(UC_X86_REG_EDI, pointer)
            vm.reg_write(UC_X86_REG_ESI, BATTLE)
            self.invoke(vm, 0x114332, stops=(0x117579, 0x11452d))
            self.assertEqual(bytes(vm.mem_read(SELECTOR, OBJECT_SIZE)),
                             self.expected_blob(before, expected))
            self.assertEqual(vm.reg_read(UC_X86_REG_EIP), BASE +
                             (0x117579 if expected.returned_index >= 0 else 0x11452d))
            self.assertEqual(self.trace[:2], [0x117560, 0x11c7f0])
            if expected.returned_index >= 0:
                self.assertEqual(vm.reg_read(UC_X86_REG_EAX) & 65535,
                                 expected.returned_index)
            else:
                self.assertEqual(vm.reg_read(UC_X86_REG_EAX), 1)

    def test_bank_transition_routes_identity_producer_and_clears_native_state_reader(self):
        vm = self.machine()
        vm.mem_map((BATTLE + 0xa9e9c34) & ~4095, 4096)

        def caller_gate(kind, identifier, blocked=0, mode=1):
            vm.mem_write(BATTLE + 0xa9e9c34, struct.pack('<II', blocked, mode))
            event = AUX + 0xf00
            vm.mem_write(event, bytes((0, 0, kind, 0, identifier)))
            vm.reg_write(UC_X86_REG_ESI, BATTLE)
            vm.reg_write(UC_X86_REG_EDI, event)
            self.invoke(vm, 0x1153b4, stops=(0x115406, 0x1154aa))
            return vm.reg_read(UC_X86_REG_EIP) == BASE + 0x115406

        banks = tuple(replace(b, words=(0,) * 100, auxiliary=bytes(100))
                      for b in self.banks(2))
        self.install(vm, banks, 0)
        for i in range(2):
            vm.mem_write(SELECTOR + 0x10 + i * 0x2d0, bytes(4))
        # Switch bank through the original state handler.
        self.invoke(vm, 0x11c7f0, (self.packet(vm, b'\x38\x41') + 1,))
        self.assertEqual(bytes(vm.mem_read(SELECTOR + 4, 1)), b'\x01')
        for word in (0x8001, 0x8101, 0x036f):
            pointer = self.packet(vm, b'\x87' + struct.pack('<H', word))
            vm.reg_write(UC_X86_REG_EBP, pointer)
            vm.reg_write(UC_X86_REG_EDI, pointer)
            vm.reg_write(UC_X86_REG_ESI, BATTLE)
            self.invoke(vm, 0x114332, stops=(0x114482,))
            self.assertEqual(self.trace, [0x117540, 0x11c520])
        bank = SELECTOR + 0x10 + 0x2d0
        self.assertEqual(struct.unpack('<I', vm.mem_read(bank, 4))[0], 3)
        self.assertEqual(bytes(vm.mem_read(SELECTOR + 0x10, 4)), bytes(4))
        definitions = identity.decode_definitions(self.source)
        for slot, pair in enumerate(((0, 1), (1, 1), (3, 111))):
            self.assertEqual(self.invoke(vm, 0x11b8c0, (slot,)),
                             CATALOG + definitions[pair].source_offset - 4)
            self.assertEqual(self.invoke(vm, 0x11b9a0, (slot,)), int(slot < 2))
            self.assertEqual(caller_gate(*pair), slot < 2)
        for blocked in (1, 2, 0xffffffff):
            self.assertFalse(caller_gate(0, 1, blocked=blocked))
        for mode in (0, 2, 0xffffffff):
            self.assertFalse(caller_gate(0, 1, mode=mode))
        self.assertFalse(caller_gate(0, 2))
        pointers = bytes(vm.mem_read(bank + 0xcc, 12))
        self.invoke(vm, 0x11c7f0, (self.packet(vm, b'\x38\x01') + 1,))
        for slot in range(3):
            self.assertEqual(self.invoke(vm, 0x11b9a0, (slot,)), 0)
        self.assertFalse(caller_gate(0, 1))
        self.assertEqual(bytes(vm.mem_read(bank + 0xcc, 12)), pointers)
        self.assertEqual(struct.unpack('<3H', vm.mem_read(bank + 4, 6)), (1, 0x101, 0x36f))
        # Entering state 2 does not restore cleared bits, including current-bank no-op.
        self.invoke(vm, 0x11c7f0, (self.packet(vm, b'\x38\x41') + 1,))
        self.assertEqual(self.invoke(vm, 0x11b9a0, (0,)), 0)

    def test_full_hotbar_entry_reaches_native_selected_index_write(self):
        self.check_hotbar_selection(0, 1)

    def test_revival_hotbar_reaches_native_selected_index_write(self):
        self.check_hotbar_selection(3, 8)

    def check_hotbar_selection(self, kind, skill_id):
        vm = self.machine()
        ui = 0x7000000
        vm.mem_map(ui, 0xb0000)
        vm.mem_map(BATTLE, 0x1000)
        vm.mem_map((BATTLE + 0xa9e9c34) & ~4095, 4096)
        vm.mem_write(BATTLE + 0x20, struct.pack('<I', ui))
        # Already in skill mode: mode-change/UI callees are outside this proof.
        vm.mem_write(BATTLE + 0x46c, struct.pack('<I', 3))
        vm.mem_write(BATTLE + 0xa9e9c34, struct.pack('<II', 0, 1))
        self.install(vm, self.banks(1), 0)
        bank = SELECTOR + 0x10
        vm.mem_write(bank, struct.pack('<I', 1))
        vm.mem_write(bank + 4, struct.pack('<H', 0x8000 | kind << 8 | skill_id))
        definition = identity.decode_definitions(self.source)[(kind, skill_id)]
        vm.mem_write(bank + 0xcc, struct.pack('<I', CATALOG + definition.source_offset - 4))
        vm.mem_write(ui + 0x86888, struct.pack('<I', AUX))
        for mode in (1, 2):
            vm.mem_write(ui + 0xa3d08, struct.pack('<I', mode))
            for row in ((0, 3, 15) if mode == 1 else (0,)):
                vm.mem_write(AUX + 0xcf, bytes((row,)))
                start = ui + (0xa3d54 + row * 60 if mode == 1 else 0xa4114)
                for hotkey in range(10):
                    vm.mem_write(start, bytes(60))
                    vm.mem_write(start + 6 * hotkey, struct.pack('<HHH', 2, kind, skill_id))
                    vm.mem_write(BATTLE + 0xa9df73c, struct.pack('<i', -1))
                    self.invoke(vm, 0x1151a0, (0x12345678, hotkey),
                                stops=(0x11542e,), this=BATTLE)
                    self.assertEqual(vm.reg_read(UC_X86_REG_EIP), BASE + 0x11542e)
                    self.assertEqual(bytes(vm.mem_read(BATTLE + 0xa9df73c, 4)), bytes(4))
                    self.assertEqual(vm.reg_read(UC_X86_REG_ECX), BATTLE)
                    self.assertEqual(bytes(vm.mem_read(vm.reg_read(UC_X86_REG_ESP), 4)),
                                     struct.pack('<I', 0x12345678))
            for hotkey in (10, 255):
                vm.mem_write(BATTLE + 0xa9df73c, struct.pack('<i', -1))
                self.invoke(vm, 0x1151a0, (0, hotkey), this=BATTLE)
                self.assertEqual(bytes(vm.mem_read(BATTLE + 0xa9df73c, 4)), b'\xff' * 4)

    def test_checked_subset_rejects_malformed_snapshots_without_mutation(self):
        banks = self.banks(1)
        for record in (b'', b'\x38', b'\x38\x00\x00', b'\x87\x00', bytearray(b'\x38\x00')):
            with self.assertRaises(ValueError):
                selection.apply_selection_record(record, banks, 0)
        for current in (-1, 256, True, None):
            with self.assertRaises(ValueError):
                selection.apply_selection_record(b'\x38\x00', banks, current)
        for bad in (list(banks), self.banks(17), (None,),
                    (replace(banks[0], key_word=65536),),
                    (replace(banks[0], state_byte=-1),),
                    (replace(banks[0], words=(0,) * 99),),
                    (replace(banks[0], words=(65536,) * 100),),
                    (replace(banks[0], auxiliary=bytes(99)),)):
            with self.assertRaises(ValueError):
                selection.apply_selection_record(b'\x38\x00', bad, 0)
        self.assertEqual(banks, self.banks(1))


if __name__ == '__main__':
    unittest.main()
