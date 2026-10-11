"""Unchanged current native target helpers, explicit state, closed code ranges."""
from dataclasses import replace
import random
import struct
import unittest

import test_current_skill_selection as native
from tools.strike_lab import current_skill_target_setup as model
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE, UC_HOOK_MEM_WRITE
from unicorn import UC_PROT_READ, UC_PROT_EXEC
from unicorn.x86_const import (
    UC_X86_REG_EAX, UC_X86_REG_ECX, UC_X86_REG_EDX, UC_X86_REG_EBP,
    UC_X86_REG_ESI, UC_X86_REG_EDI, UC_X86_REG_EIP, UC_X86_REG_ESP,
)

CONTEXT = native.BATTLE + 0x144938
OUTPUT = native.BATTLE + 0x434
FLAG = native.BATTLE + 0x468
RECORD = native.AUX + 0x800
RANGES = (
    (0x11e6e0, 0x11e76a), (0x11ead0, 0x11eb2e),
    (0x11ec70, 0x11eca0), (0x11eca0, 0x11ecff),
    (0x11ed00, 0x11ed91), (0x11eda0, 0x11ee84),
    (0x11ee90, 0x11f24c),
    (0x115571, 0x11557f), (0x1155bf, 0x1155e9),
    (0x1155f2, 0x115650), (0x1156e0, 0x1156fc),
)


class CurrentSkillTargetSetupTests(native.CurrentSkillSelectionTests):
    # Inherit the pinned source/image loader and existing selection regression.
    # The original harness and its closed ranges are not modified.
    def target_machine(self):
        vm = Uc(UC_ARCH_X86, UC_MODE_32)
        vm.mem_map(native.BASE, (len(self.image) + 4095) & ~4095,
                   UC_PROT_READ | UC_PROT_EXEC)
        vm.mem_write(native.BASE, self.image)
        for address, size in ((native.STACK, 0x4000), (native.BATTLE, 4096),
                              (CONTEXT & ~4095, 4096), (native.AUX, 4096),
                              ((native.BATTLE + 0xa9e9c38) & ~4095, 4096)):
            vm.mem_map(address, size)
        self.executed, self.native_writes = set(), []
        self.target_stops, self.write_regions = set(), ()

        def code(machine, address, size, data):
            rva = address - native.BASE
            if rva in self.target_stops:
                machine.emu_stop()
                return
            if not any(lo <= rva and rva + size <= hi for lo, hi in RANGES):
                raise AssertionError(f'Outside closed native target ranges: {rva:X}')
            self.executed.add(rva)

        def write(machine, access, address, size, value, data):
            if not any(lo <= address and address + size <= hi
                       for lo, hi in ((native.STACK, native.STACK + 0x3000),
                                      *self.write_regions)):
                raise AssertionError(f'Unexpected native write: {address:X}/{size}')
            if not native.STACK <= address < native.STACK + 0x3000:
                self.native_writes.append((address, size, value))

        vm.hook_add(UC_HOOK_CODE, code)
        vm.hook_add(UC_HOOK_MEM_WRITE, write)
        return vm

    def target_invoke(self, vm, entry, args=(), stops=(), writes=(),
                      this=CONTEXT, seed=0xa5a50000):
        self.target_stops, self.write_regions = set(stops), writes
        self.executed.clear()
        self.native_writes.clear()
        vm.mem_write(native.SP, struct.pack('<' + 'I' * (len(args) + 1),
                                           native.RETURN, *args))
        for reg, value in ((UC_X86_REG_ESP, native.SP), (UC_X86_REG_ECX, this),
                           (UC_X86_REG_EAX, seed), (UC_X86_REG_EDX, ~seed & 0xffffffff)):
            vm.reg_write(reg, value)
        vm.emu_start(native.BASE + entry, native.RETURN, count=20000)
        end = vm.reg_read(UC_X86_REG_EIP)
        self.assertIn(end, {native.RETURN} | {native.BASE + stop for stop in stops})
        if end == native.RETURN:
            self.assertEqual(vm.reg_read(UC_X86_REG_ESP), native.SP + 4 + len(args) * 4)
        return vm.reg_read(UC_X86_REG_EAX)

    @staticmethod
    def state(masks=(0x3fff, 0x3fff), words=None):
        return model.TargetState(masks, (0x89abcdef, 0x76543210),
                                 (None,) * 28 if words is None else words)

    def install_target(self, vm, state):
        blob = bytearray(b'\xa5' * 0x308)
        for index, word in enumerate(state.entity_words):
            pointer = native.AUX + index * 0x20 if word is not None else 0
            struct.pack_into('<I', blob, 0x38 + index * 24, pointer)
            if pointer:
                vm.mem_write(pointer, bytes(0x20))
                vm.mem_write(pointer + 0x1a, struct.pack('<h', word))
        struct.pack_into('<4I', blob, 0x2f4, *state.masks, *state.saved_masks)
        vm.mem_write(CONTEXT, bytes(blob))
        vm.mem_write(native.BATTLE, b'\xa5' * 4096)
        return blob

    def compare_masks(self, vm, fields, actor, state):
        before = self.install_target(vm, state)
        expected = model.target_masks(fields, actor, state)
        self.target_invoke(vm, 0x11ee90,
            (OUTPUT, fields.mode_45, actor, fields.reach_44, fields.kind, fields.identifier),
            writes=((OUTPUT, OUTPUT + 8), (CONTEXT + 0x2fc, CONTEXT + 0x308)))
        struct.pack_into('<3I', before, 0x2fc, *expected.saved_masks, expected.stored_mode)
        self.assertEqual(bytes(vm.mem_read(CONTEXT, 0x308)), bytes(before),
                         (fields, actor, state))
        battle = bytearray(b'\xa5' * 4096)
        struct.pack_into('<2I', battle, 0x434, *expected.masks)
        self.assertEqual(bytes(vm.mem_read(native.BATTLE, 4096)), bytes(battle),
                         (fields, actor, state))
        return expected

    def test_target_pinned_tables_and_all_setup_modes(self):
        self.assertEqual(model.IMAGE_SHA256, native.selection.IMAGE_SHA256)
        for rva, values in ((0x171bf8, model.ROW_MASKS), (0x171c18, model.ROW_SLOTS),
                            (0x171bb0, model.MODE_VALUES),
                            (0x171c38, model.MODE_ROWS[6]),
                            (0x171c58, model.MODE_ROWS[7]),
                            (0x171c78, model.MODE_ROWS[15])):
            self.assertEqual(struct.unpack_from('<' + 'I' * len(values), self.image, rva), values)
        vm = self.target_machine()
        for mode in range(1, 18):
            vm.mem_write(native.BATTLE, b'\xa5' * 4096)
            returned = self.target_invoke(vm, 0x11ead0, (mode, FLAG), writes=((FLAG, FLAG + 4),))
            value, flag = model.setup_parameters(mode)
            self.assertEqual(returned, value)
            expected = bytearray(b'\xa5' * 4096)
            struct.pack_into('<I', expected, 0x468, flag)
            self.assertEqual(bytes(vm.mem_read(native.BATTLE, 4096)), bytes(expected))
        for mode in (0, 18, 255, 0xffffffff, 0x80000000):
            with self.assertRaisesRegex(AssertionError, '2C70'):
                self.target_invoke(vm, 0x11ead0, (mode, FLAG), writes=((FLAG, FLAG + 4),))
            self.assertFalse(self.native_writes)

    def test_target_row_distance_all_slots_and_occupancy_rows(self):
        vm = self.target_machine()
        # Every pair of physical positions with all-empty and all-full masks.
        for a in range(28):
            for b in range(28):
                for masks in ((0, 0), (0x3fff, 0x3fff)):
                    args = (a // 14, a % 14, b // 14, b % 14, *masks)
                    actual = self.target_invoke(vm, 0x11ed00, args)
                    self.assertEqual(actual, model.row_distance(*args[:4], masks))
        # Every row-occupancy pattern, every pair of rows, endpoints included.
        for occupied in range(256):
            masks = tuple(sum(model.ROW_MASKS[r] for r in range(side * 4, side * 4 + 4)
                              if occupied & (1 << r)) for side in range(2))
            for a in range(8):
                for b in range(8):
                    args = (a // 4, model.ROW_SLOTS[a], b // 4, model.ROW_SLOTS[b], *masks)
                    self.assertEqual(self.target_invoke(vm, 0x11ed00, args),
                                     model.row_distance(*args[:4], masks))
        self.assertEqual(model.row_distance(0, 12, 1, 12, (0, 0)), 1)
        self.assertEqual(model.row_distance(0, 12, 1, 12, (0x3fff, 0x3fff)), 7)

    def test_target_all_modes_actors_reaches_and_raw_masks(self):
        vm = self.target_machine()
        covered = set()
        for mode in range(1, 18):
            for actor in range(14):
                for reach in (0, 1, 2, 3, 4, 7, 8, 127, 128, 255):
                    for masks in ((0, 0), (0x3fff, 0x3fff), (0x2001, 0x0400),
                                  (0xffffc000, 0xffffffff)):
                        self.compare_masks(vm, model.Fields(1, 0, 0, reach, mode),
                                           actor, self.state(masks))
                        covered.update(self.executed)
        for entry in (0x11ee90, 0x11eda0, 0x11ed00, 0x11eca0, 0x11ec70,
                      0x11ef38, 0x11ef63, 0x11f111, 0x11f16f,
                      0x11f1cd, 0x11f20a, 0x11f21a):
            self.assertIn(entry, covered)
        # Mode-specific masks can contain unoccupied slots; no universal AND.
        self.assertEqual(self.compare_masks(vm, model.Fields(1, 0, 0, 7, 8),
                         12, self.state((0, 0))).masks, (0x1f, 0x1f))
        for mode in (0, 18, 127, 128, 255):
            result = self.compare_masks(vm, model.Fields(1, 0, 0, 255, mode), 0, self.state())
            self.assertEqual(result.masks, (0, 0))

    def test_target_kind3_entity_expansion_and_saved_original_masks(self):
        vm = self.target_machine()
        words = tuple((None, -32768, -1, 0, 1, 32767, None)[i % 7] for i in range(28))
        for kind in (0, 1, 2, 3, 4, 255):
            for identifier in (0, 7, 8, 9, 10, 11, 255):
                for mode in (1, 6, 7, 8, 9, 10, 11, 12, 15, 17):
                    result = self.compare_masks(vm, model.Fields(identifier, kind, 0, 7, mode),
                                                13, self.state((0x80000000, 0), words))
                    self.assertEqual(0x11e6e0 in self.executed,
                                     kind == 3 and 8 <= identifier <= 10)
                    if mode == 17:
                        self.assertEqual(result.saved_masks, (0x80000000, 0))
        rng = random.Random(0x11ee90)
        for _ in range(512):
            state = self.state(tuple(rng.getrandbits(32) for _ in range(2)),
                               tuple(rng.choice((None, -1, 0, 32767)) for _ in range(28)))
            fields = model.Fields(rng.choice((1, 8, 9, 10, 11)), rng.randrange(4),
                                  rng.randrange(65536), rng.randrange(256), rng.randrange(1, 18))
            self.compare_masks(vm, fields, rng.randrange(14), state)

    def test_revival_source_definitions_expand_missing_entities_not_dead_only(self):
        definitions = native.identity.decode_definitions(self.source)
        vm = self.target_machine()
        for identifier, reach in ((8,5),(9,6),(10,7)):
            fields = model.Fields.from_record(definitions[3,identifier].raw)
            self.assertEqual((fields.kind,fields.mode_45,fields.reach_44), (3,1,reach))
            for actor in range(14):
                for target in range(28):
                    for word in (None,-1,0,32767):
                        words = [None] * 28
                        words[actor] = 0
                        words[target] = word
                        initial = (1 << actor, 0)
                        state = self.state(initial, tuple(words))
                        result = self.compare_masks(vm, fields, actor, state)
                        expected = list(initial)
                        if word is not None and word >= 0:
                            expected[target // 14] |= 1 << (target % 14)
                        self.assertEqual(result.masks, tuple(expected), (identifier,actor,target,word))
                        # Existing eligible bits survive even with a null/negative entity.
                        # This helper alone cannot establish dead-only cast eligibility.
                        self.assertTrue(result.masks[0] & (1 << actor))
                        self.assertIn(0x11e6e0, self.executed)
        # The separate auto-revival buff is not this missing-entity expansion.
        buff = model.Fields.from_record(definitions[3,72].raw)
        result = self.compare_masks(vm, buff, 0, self.state((1,0), (0,) * 28))
        self.assertNotIn(0x11e6e0, self.executed)
        self.assertEqual(result.masks, (1,0))

    def test_target_source_fields_gate_and_real_caller_windows(self):
        vm = self.target_machine()
        definitions = native.identity.decode_definitions(self.source)
        gates, diagnostic_modes = 0, 0
        for definition in definitions.values():
            fields = model.Fields.from_record(definition.raw)
            gates += fields.passes_kind_gate
            diagnostic_modes += fields.mode_45 == 0
            vm.mem_write(RECORD, definition.raw)
            vm.reg_write(UC_X86_REG_EBP, RECORD)
            self.target_invoke(vm, 0x115571, stops=(0x11557f, 0x11559a))
            self.assertEqual(vm.reg_read(UC_X86_REG_EIP), native.BASE +
                             (0x11559a if fields.passes_kind_gate else 0x11557f))
            self.compare_masks(vm, fields, definition.id % 14, self.state())
            # Execute the actual source loads, actor accessor, CALL and callee.
            for primary, alternate in ((1, 0), (0, 1), (0x12340000, 1)):
                state = self.state((0x3001, 0x421))
                before = self.install_target(vm, state)
                vm.mem_write(native.BATTLE + 0x51, bytes((3, 12)))
                vm.mem_write(native.BATTLE + 0xa9e9c38, struct.pack('<II', primary, alternate))
                for reg, value in ((UC_X86_REG_ESI, native.BATTLE),
                                   (UC_X86_REG_EDI, CONTEXT), (UC_X86_REG_EBP, RECORD)):
                    vm.reg_write(reg, value)
                actor = 3 if primary else 12
                expected = model.target_masks(fields, actor, state)
                self.target_invoke(vm, 0x1155bf, stops=(0x1155e9,),
                    writes=((OUTPUT, OUTPUT + 8), (CONTEXT + 0x2fc, CONTEXT + 0x308)))
                self.assertIn(0x1155e4, self.executed)
                self.assertIn(0x1156e0, self.executed)
                self.assertEqual(struct.unpack('<2I', vm.mem_read(OUTPUT, 8)), expected.masks)
                struct.pack_into('<3I', before, 0x2fc, *expected.saved_masks, fields.mode_45)
                self.assertEqual(bytes(vm.mem_read(CONTEXT, 0x308)), bytes(before))
            if fields.mode_45:
                vm.reg_write(UC_X86_REG_ESI, native.BATTLE)
                vm.reg_write(UC_X86_REG_EDI, CONTEXT)
                vm.reg_write(UC_X86_REG_EBP, RECORD)
                expected_battle = bytearray(vm.mem_read(native.BATTLE, 4096))
                self.target_invoke(vm, 0x1155f2, stops=(0x115650,),
                                   writes=((native.BATTLE + 0x43c, FLAG + 4),))
                value, flag = model.setup_parameters(fields.mode_45)
                expected_battle[0x43c:0x45a] = bytes(0x1e)
                struct.pack_into('<II', expected_battle, 0x45c, value, 0)
                struct.pack_into('<I', expected_battle, 0x468, flag)
                self.assertEqual(bytes(vm.mem_read(native.BATTLE, 4096)), bytes(expected_battle))
                self.assertIn(0x115614, self.executed)
        self.assertEqual((len(definitions), gates, diagnostic_modes), (448, 364, 7))

    def test_target_checked_subset_rejects_invalid_state(self):
        for mode in (-1, 0, 18, 256, True, None):
            with self.assertRaises(ValueError):
                model.setup_parameters(mode)
        for masks in ([0, 0], (0,), (-1, 0), (0, 1 << 32), (False, 0)):
            with self.assertRaises(ValueError):
                self.state(masks)
        for words in ((None,) * 27, (32768,) * 28, (-32769,) * 28, (True,) * 28):
            with self.assertRaises(ValueError):
                self.state(words=words)
        for actor in (-1, 14, 255, True):
            with self.assertRaises(ValueError):
                model.target_masks(model.Fields(1, 0, 0, 1, 1), actor, self.state())
        for raw in (b'', bytes(109), bytes(111), bytearray(110)):
            with self.assertRaises(ValueError):
                model.Fields.from_record(raw)
        fields = model.Fields(1, 2, 0xff5, 7, 1)
        for name, value in (('identifier', 256), ('kind', -1), ('word_3e', 65536),
                            ('reach_44', True), ('mode_45', None)):
            with self.assertRaises(ValueError):
                replace(fields, **{name: value})


if __name__ == '__main__':
    unittest.main()
