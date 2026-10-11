"""Source-backed native 11C520 -> accessors -> command packing regression."""
import hashlib
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

import test_current_battle_command as battle
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_ECX, UC_X86_REG_EIP, UC_X86_REG_ESP

sys.path.insert(0, str(battle.ROOT))
from tools.strike_lab import current_skill_identity as identity

CATALOG, AUX = 0x6000000, 0x6100000
WORD, TARGET = AUX + 0x200, AUX + 0x300


class CurrentSkillIdentityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image = (battle.ROOT / 'artifacts/capture_work/host-20260918-1430/output/'
                     'native-master-01-stable.bin').read_bytes()
        cls.source_path = battle.ROOT.parent / 'God2' / identity.SOURCE
        cls.source = cls.source_path.read_bytes()
        if hashlib.sha256(cls.image).hexdigest() != identity.IMAGE_SHA256:
            raise AssertionError('Pinned native image changed')
        if hashlib.sha256(cls.source).hexdigest() != identity.SOURCE_SHA256:
            raise AssertionError('Pinned definition source changed')
        cls.definitions = identity.decode_definitions(cls.source)
        output = battle.ROOT / 'artifacts/skill-identity'
        output.mkdir(parents=True, exist_ok=True)
        cls.temp = tempfile.TemporaryDirectory(prefix='native-', dir=output)
        cls.addClassCleanup(cls.temp.cleanup)
        cls.executable = battle.build_fixture(Path(cls.temp.name),
                                               'test_recovered_skill_command.cpp')

    def machine(self):
        vm = battle.ready.CurrentWorldReadyBuilderTests.vm(self)
        vm.mem_map(battle.BATTLE, 4096)
        vm.mem_map(battle.SELECTOR & ~4095, 0x5000)
        vm.mem_map((battle.BATTLE + 0xa9e9c38) & ~4095, 4096)
        vm.mem_map(CATALOG, 0x1c000)
        vm.mem_write(CATALOG, self.source[4:])
        vm.mem_map(AUX, 4096)
        vm.mem_write(battle.BATTLE + 0x10, struct.pack('<I', battle.NET))
        vm.mem_write(battle.BATTLE + 0x44, struct.pack('<I', 1))
        vm.mem_write(battle.NET + 0x2cb8, b'\x01')
        self.calls = []

        def trace(machine, address, size, data):
            rva = address - battle.BASE
            if rva == 0x1191ee:
                machine.emu_stop()
            if rva in (0x11c520, 0x1156a0, 0x11b8c0, 0x11b900, 0x132e0):
                self.calls.append(rva)
            if rva in (0x13370, 0x112130, 0x1120b0):
                raise AssertionError('Unexpected transport or cleanup execution')
        vm.hook_add(UC_HOOK_CODE, trace)
        self.reset_selector(vm)
        return vm

    def reset_selector(self, vm):
        vm.mem_write(battle.SELECTOR, bytes(0x3600))
        vm.mem_write(battle.SELECTOR + 0x3518, struct.pack('<I', CATALOG))
        for bank in range(16):
            vm.mem_write(battle.SELECTOR + 0x2d4 + bank * 0x2d0, struct.pack('<I', AUX))

    def invoke(self, vm, entry, args=(), this=battle.SELECTOR):
        vm.mem_write(battle.SP, struct.pack('<' + 'I' * (len(args) + 1),
                                          battle.ready.RETURN, *args))
        vm.reg_write(UC_X86_REG_ESP, battle.SP)
        vm.reg_write(UC_X86_REG_ECX, this)
        vm.emu_start(battle.BASE + entry, battle.ready.RETURN,
                     timeout=1000000, count=10000)
        self.assertIn(vm.reg_read(UC_X86_REG_EIP),
                      (battle.ready.RETURN, battle.BASE + 0x1191ee))
        return vm.reg_read(UC_X86_REG_EAX)

    def produce(self, vm, word, bank=0):
        alternate = bool(word & 0x4000)
        vm.mem_write(battle.SELECTOR + (0x2d10 if alternate else 4), bytes([bank]))
        vm.mem_write(WORD, struct.pack('<H', word))
        self.invoke(vm, 0x11c520, (WORD,))

    def slots(self, vm, alternate, bank):
        base = battle.SELECTOR + (0x2d14 + bank * 0x54 if alternate else 0x10 + bank * 0x2d0)
        count = struct.unpack('<I', vm.mem_read(base + (0x50 if alternate else 0), 4))[0]
        self.assertLessEqual(count, 10 if alternate else 100)
        return [(struct.unpack('<H', vm.mem_read(base + (0 if alternate else 4) + i * 2, 2))[0],
                 struct.unpack('<I', vm.mem_read(base + (0x14 if alternate else 0xcc) + i * 4, 4))[0])
                for i in range(count)]

    def cpp_batch(self, words, path=None):
        result = subprocess.run([str(self.executable), '--identity-batch',
                                 str(path or self.source_path)],
                                input=''.join(word.hex() + '\n' for word in words),
                                text=True, capture_output=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result.stdout.splitlines()

    def test_source_identity_layout_and_checked_cpp_all_state_words(self):
        self.assertEqual([sum(k == kind for k, _ in self.definitions) for kind in range(4)],
                         [121, 129, 87, 111])
        words = [struct.pack('<H', word) for word in range(65536)]
        results = self.cpp_batch(words)
        self.assertEqual(len(results), 65536)
        for word, output in zip(words, results):
            decoded = identity.decode_state_word(word)
            definition = self.definitions.get((decoded.kind, decoded.id))
            expected = (f'{decoded.raw} {decoded.id} {decoded.kind} '
                        f'{int(decoded.alternate_table)} {int(decoded.state_bit)} '
                        f'{definition.source_offset if definition else "reject"}')
            self.assertEqual(output, expected)
        self.assertEqual(self.cpp_batch([b'', b'\x01', b'\x01\x00\x00']), ['reject'] * 3)

    def test_original_producer_every_populated_definition_both_tables_and_flags(self):
        vm = self.machine()
        for (kind, id_byte), definition in self.definitions.items():
            for flags in (0, 0x4000, 0x8000, 0xc000):
                with self.subTest(kind=kind, id=id_byte, flags=flags):
                    self.reset_selector(vm)
                    word = id_byte | (kind << 8) | flags
                    alternate = bool(flags & 0x4000)
                    self.produce(vm, word)
                    pointer = CATALOG + definition.source_offset - 4
                    self.assertEqual(self.slots(vm, alternate, 0), [(word, pointer)])
                    self.assertEqual(bytes(vm.mem_read(pointer, 110)), definition.raw)
                    selected = self.invoke(vm, 0x11b900 if alternate else 0x11b8c0, (0,))
                    self.assertEqual(selected, pointer)
        self.assertEqual(self.calls.count(0x11c520), 1792)

    def test_native_slots_are_insertion_order_duplicate_updates_keep_slots(self):
        vm = self.machine()
        model = identity.SelectionState(self.definitions)
        for alternate in (False, True):
            for bank in (0, 2) if alternate else (0, 7, 15):
                for value in (0x0079, 0x0101, 0x0001, 0x8079, 0x0079, 0x8101, 0x036f):
                    word = value | (0x4000 if alternate else 0)
                    self.produce(vm, word, bank)
                    slot = model.apply(struct.pack('<H', word), bank)
                    expected = [(raw, CATALOG + d.source_offset - 4)
                                for raw, d in model.entries(alternate, bank)]
                    self.assertEqual(self.slots(vm, alternate, bank), expected)
                    self.assertEqual(self.invoke(vm, 0x11b900 if alternate else 0x11b8c0,
                                                 (slot,)), expected[slot][1])
                self.assertEqual(len(model.entries(alternate, bank)), 4)
        for alternate in (False, True):
            for bank in range(3 if alternate else 16):
                self.assertEqual(self.slots(vm, alternate, bank),
                    [(raw, CATALOG + d.source_offset - 4) for raw, d in model.entries(alternate, bank)])

    def test_original_producer_lookup_and_builder_use_source_id_not_slot(self):
        vm = self.machine()
        for alternate, bank in ((False, 0), (False, 15), (True, 0), (True, 2)):
            self.reset_selector(vm)
            for id_byte in (121, 1, 65):
                self.produce(vm, id_byte | (0x4000 if alternate else 0), bank)
            vm.mem_write(battle.BATTLE + 0xa9e9c38,
                         struct.pack('<II', 0 if alternate else 1, 1 if alternate else 0))
            for slot, id_byte in enumerate((121, 1, 65)):
                vm.mem_write(battle.BATTLE + 0xa9df73c, struct.pack('<i', slot))
                vm.mem_write(battle.NET + 0x36c4, bytes(4))
                self.calls.clear()
                self.invoke(vm, 0x118e50, (3, 0, 1, TARGET), battle.BATTLE)
                output = battle.ready.CurrentWorldReadyBuilderTests.queued(self, vm)
                self.assertEqual(len(output), 17)
                self.assertEqual(output[13:], bytes([id_byte, 0, 0, 0]))
                self.assertEqual(self.calls, [0x1156a0, 0x11b900 if alternate else 0x11b8c0, 0x132e0])
                result = subprocess.check_output([str(self.executable), '--decode', output.hex()],
                                                 text=True, timeout=5)
                self.assertEqual(int(result.split()[-1]), id_byte)

    def test_native_full_table_capacity_and_repeated_updates(self):
        vm = self.machine()
        model = identity.SelectionState(self.definitions)
        for alternate, capacity in ((False, 100), (True, 10)):
            flag = 0x4000 if alternate else 0
            for id_byte in range(1, capacity + 1):
                self.produce(vm, id_byte | flag)
                model.apply(struct.pack('<H', id_byte | flag), 0)
            for id_byte in (capacity, 1, capacity // 2):
                self.produce(vm, id_byte | flag | 0x8000)
                model.apply(struct.pack('<H', id_byte | flag | 0x8000), 0)
            self.assertEqual(self.slots(vm, alternate, 0),
                [(raw, CATALOG + d.source_offset - 4) for raw, d in model.entries(alternate, 0)])
            self.assertEqual(self.invoke(vm, 0x11b900 if alternate else 0x11b8c0,
                                         (capacity,)), 0)
            self.assertEqual(self.invoke(vm, 0x11b900 if alternate else 0x11b8c0,
                                         (0xffffffff,)), 0)

    def test_cpp_source_validation_and_existing_command_assertions(self):
        for offset, replacement in ((0, b'2.00'), (4, struct.pack('<I', 256)),
                                    (4, bytes(4)), (8, b'\x02'), (9, b'\x01')):
            bad = bytearray(self.source)
            bad[offset:offset + len(replacement)] = replacement
            path = Path(self.temp.name) / 'invalid-cbspec2.bin'
            path.write_bytes(bad)
            self.assertEqual(self.cpp_batch([b'\x01\x00'], path), ['1 1 0 0 0 reject'])
        output = subprocess.check_output([str(self.executable)], text=True, timeout=10)
        self.assertIn('assertions passed', output)

    def test_source_and_selection_subset_rejections_do_not_invent_native_guards(self):
        for length in (0, 3, 4, 8, 4 + identity.GROUP_STRIDE, len(self.source) - 1):
            with self.assertRaises(ValueError):
                identity.decode_definitions(self.source[:length])
        for offset, replacement in ((0, b'2.00'), (4, struct.pack('<I', 256)),
                                    (8, b'\x02'), (9, b'\x01')):
            bad = bytearray(self.source)
            bad[offset:offset + len(replacement)] = replacement
            with self.assertRaises(ValueError):
                identity.decode_definitions(bad)
        model = identity.SelectionState(self.definitions)
        for word in (0, 122, 0x0401, 0x3f01, 0xff00):
            with self.assertRaises(ValueError):
                model.apply(struct.pack('<H', word), 0)
        for bank in (-1, 16, 128):
            with self.assertRaises(ValueError):
                model.apply(b'\x01\x00', bank)
        with self.assertRaises(ValueError):
            model.apply(b'\x01\x40', 3)
        for alternate, capacity in ((False, 100), (True, 10)):
            for id_byte in range(1, capacity + 1):
                model.apply(struct.pack('<H', id_byte | (0x4000 if alternate else 0)), 0)
            with self.assertRaises(ValueError):
                model.apply(struct.pack('<H', capacity + 1 | (0x4000 if alternate else 0)), 0)
            self.assertEqual(model.apply(struct.pack('<H', 0x8001 | (0x4000 if alternate else 0)), 0), 0)
            for slot in (-1, capacity, 0x100):
                with self.assertRaises(ValueError):
                    model.select(alternate, 0, slot)
        # Original producer has no source-population check: do not report the
        # decoder's source validation as an original guard or gameplay rule.
        vm = self.machine()
        self.produce(vm, 122)
        self.assertEqual(self.slots(vm, False, 0), [(122, CATALOG + 4 + 121 * 110)])


if __name__ == '__main__':
    unittest.main()
