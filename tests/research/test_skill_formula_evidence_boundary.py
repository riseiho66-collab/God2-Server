"""Current native supplied values are not recovered skill damage formulas.

Run with -B. Only pinned current-client inputs are read; no DB or process is
started. Synthetic emulator state is not an observed packet or server result.
"""
import copy
from dataclasses import asdict
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'artifacts/tooling/crypto-oracle-python'))

from tools.strike_lab import current_skill_identity as identity
from tools.strike_lab import current_skill_target_setup as targeting
from tools.strike_lab import recover_combat_rules as rules
from unicorn import (Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE,
                     UC_HOOK_MEM_WRITE, UC_PROT_READ, UC_PROT_EXEC)
from unicorn.x86_const import (UC_X86_REG_EAX, UC_X86_REG_ECX,
                               UC_X86_REG_EIP, UC_X86_REG_ESP)

BASE, STACK, BATTLE, ACTOR, INPUT = (
    0x400000, 0x3000000, 0x4000000, 0x5000000, 0x6000000)
CONTEXT = BATTLE + 0x144938
DISPLAY = CONTEXT + 0x310 + 0x1c
SP, RETURN = STACK + 0x2000, BASE + 0x1000
FLAG = INPUT + 0x100
RANGES = ((0x1173a0, 0x117472), (0x12d970, 0x12d9e5),
          (0x11e6e0, 0x11e76a), (0x108fc0, 0x108ffe),
          (0x108f50, 0x108fb1), (0x108e70, 0x108f48),
          (0x11ead0, 0x11eb2e))


class SkillFormulaEvidenceBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image = rules.read_pinned(rules.IMAGE, identity.IMAGE_SHA256)
        cls.definitions = identity.decode_definitions(rules.read_pinned(
            rules.CLIENT / identity.SOURCE, identity.SOURCE_SHA256))
        cls.inventory = rules.build_inventory()

    def machine(self):
        vm = Uc(UC_ARCH_X86, UC_MODE_32)
        vm.mem_map(BASE, (len(self.image) + 4095) & ~4095,
                   UC_PROT_READ | UC_PROT_EXEC)
        vm.mem_write(BASE, self.image)
        for address, size in ((STACK, 0x4000), (BATTLE, 0x1000),
                              (CONTEXT & ~4095, 0xc000),
                              (ACTOR, 0x1000), (INPUT, 0x1000)):
            vm.mem_map(address, size)
        self.trace, self.writes = [], []
        self.write_regions = ()

        def code(machine, address, size, data):
            rva = address - BASE
            self.assertTrue(any(lo <= rva and rva + size <= hi
                                for lo, hi in RANGES),
                            f'Outside qualified native code: {rva:X}')
            self.trace.append(rva)

        def write(machine, access, address, size, value, data):
            self.assertTrue(any(lo <= address and address + size <= hi
                                for lo, hi in ((STACK, STACK + 0x3000),
                                               *self.write_regions)),
                            f'Unexpected native write: {address:X}/{size}')
            if not STACK <= address < STACK + 0x3000:
                self.writes.append((address, size))

        vm.hook_add(UC_HOOK_CODE, code)
        vm.hook_add(UC_HOOK_MEM_WRITE, write)
        return vm

    def invoke(self, vm, entry, args, this=BATTLE, writes=()):
        self.write_regions = writes
        self.trace.clear()
        self.writes.clear()
        vm.mem_write(SP, struct.pack('<' + 'I' * (1 + len(args)), RETURN, *args))
        vm.reg_write(UC_X86_REG_ESP, SP)
        vm.reg_write(UC_X86_REG_ECX, this)
        vm.emu_start(BASE + entry, RETURN, timeout=1000000, count=2048)
        self.assertEqual(vm.reg_read(UC_X86_REG_EIP), RETURN)
        self.assertEqual(vm.reg_read(UC_X86_REG_ESP), SP + 4 * (1 + len(args)))
        return vm.reg_read(UC_X86_REG_EAX)

    def install(self, vm, supplied_5, supplied_9, position=13,
                present=True, handle=0):
        vm.mem_write(BATTLE, b'\xa5' * 0x1000)
        # Avoid the caller's selected-actor UI notification by its native branch.
        vm.mem_write(BATTLE + 0x51, b'\xff')
        vm.mem_write(CONTEXT + 0x38 + 13 * 24,
                     struct.pack('<I', ACTOR if present else 0))
        actor = bytearray(b'\xa5' * 0x1000)
        struct.pack_into('<h', actor, 0x1d8, handle)
        struct.pack_into('<4I', actor, 0xde8, 900, 0x11223344, 100, 0x55667788)
        vm.mem_write(ACTOR, bytes(actor))
        display = bytearray(b'\x5a' * 0xa7e0)
        # Negative native channel handles skip both drawing calls without stubs.
        struct.pack_into('<2h', display, 0xa79c, -1, -1)
        vm.mem_write(DISPLAY, bytes(display))
        buffer = bytearray(b'\xa5' * 13)
        buffer[2] = position
        struct.pack_into('<2I', buffer, 5, supplied_5, supplied_9)
        pointer = INPUT + 0x1000 - len(buffer)
        vm.mem_write(pointer, bytes(buffer))
        return actor, display, bytes(buffer), pointer

    def test_native_caller_preserves_supplied_values_and_clamps_only_display(self):
        for supplied_5, supplied_9 in ((5, 900), (0, 1), (1000, 7),
                                      (0xffffffff, 0x80000000),
                                      (0x80000000, 0xffffffff)):
            with self.subTest(buffer_5=supplied_5, buffer_9=supplied_9):
                vm = self.machine()
                actor, display, buffer, pointer = self.install(vm, supplied_5, supplied_9)
                self.assertEqual(self.invoke(vm, 0x1173a0, (pointer,), writes=(
                    (ACTOR + 0xdec, ACTOR + 0xdf0),
                    (ACTOR + 0xdf4, ACTOR + 0xdf8),
                    (DISPLAY + 0xa7a8, DISPLAY + 0xa7b8))), 1)
                struct.pack_into('<I', actor, 0xdec, supplied_9)
                struct.pack_into('<I', actor, 0xdf4, supplied_5)
                struct.pack_into('<4I', display, 0xa7a8,
                                 100, supplied_5, 100, min(supplied_9, supplied_5))
                self.assertEqual(bytes(vm.mem_read(ACTOR, len(actor))), bytes(actor))
                self.assertEqual(bytes(vm.mem_read(DISPLAY, len(display))), bytes(display))
                self.assertEqual(bytes(vm.mem_read(pointer, len(buffer))), buffer)
                self.assertEqual(self.trace.count(0x11e6e0), 2)
                self.assertEqual(self.trace.count(0x108e70), 2)
                for entry in (0x11740a, 0x12d970, 0x108fc0, 0x108f50):
                    self.assertIn(entry, self.trace)
                self.assertEqual(set(self.writes), {(ACTOR + 0xdec, 4),
                    (ACTOR + 0xdf4, 4), *( (DISPLAY + offset, 4)
                    for offset in (0xa7a8, 0xa7ac, 0xa7b0, 0xa7b4))})

    def test_native_early_returns_do_not_synthesize_a_result(self):
        for position, present, handle in ((14, True, 0), (13, False, 0),
                                          (13, True, -1)):
            with self.subTest(position=position, present=present, handle=handle):
                vm = self.machine()
                actor, display, buffer, pointer = self.install(
                    vm, 5, 900, position, present, handle)
                writes = () if handle == 0 else (
                    (ACTOR + 0xdec, ACTOR + 0xdf0), (ACTOR + 0xdf4, ACTOR + 0xdf8))
                self.assertEqual(self.invoke(vm, 0x1173a0, (pointer,), writes=writes), 1)
                if handle < 0:
                    struct.pack_into('<I', actor, 0xdec, 900)
                    struct.pack_into('<I', actor, 0xdf4, 5)
                    self.assertIn(0x12d970, self.trace)
                else:
                    self.assertNotIn(0x12d970, self.trace)
                    self.assertEqual(self.writes, [])
                self.assertNotIn(0x108fc0, self.trace)
                self.assertEqual(bytes(vm.mem_read(ACTOR, len(actor))), bytes(actor))
                self.assertEqual(bytes(vm.mem_read(DISPLAY, len(display))), bytes(display))
                self.assertEqual(bytes(vm.mem_read(pointer, len(buffer))), buffer)

    def test_pinned_mode14_seven_is_an_opaque_target_setup_value(self):
        definition = self.definitions[0, 40]
        self.assertEqual(definition.source_offset, 0x10ca)
        self.assertEqual(rules.sha256(definition.raw),
                         'fa4d53d4c8e4ef586944f64531dd09de1a57b0a494f31bb743d6105f6838ee8b')
        fields = targeting.Fields.from_record(definition.raw)
        self.assertEqual(asdict(fields), dict(identifier=40, kind=0,
                         word_3e=0, reach_44=5, mode_45=14))
        vm = self.machine()
        vm.mem_write(FLAG, b'\xa5' * 4)
        value = self.invoke(vm, 0x11ead0, (fields.mode_45, FLAG),
                            this=CONTEXT, writes=((FLAG, FLAG + 4),))
        flag, = struct.unpack('<I', vm.mem_read(FLAG, 4))
        self.assertEqual((value, flag), (7, 0))
        self.assertEqual(targeting.setup_parameters(fields.mode_45), (value, flag))
        self.assertEqual(self.writes, [(FLAG, 4)])

    def assert_evidence_boundary(self, inventory):
        # Closed metadata shapes also catch new nested multiplier/rate fields.
        shapes = (
            (inventory['skill_books']['definitions'],
             'source_line decoded_offset raw_record_hex source_record_sha256 fields '
             'item_id name description_claims authority matched_categories '
             'displayed_mp_cost server_resource_cost', 'description_only'),
            (inventory['card_effects']['records'],
             'offset length raw_hex sha256 line fields index authority '
             'description_column matched_categories', 'description_only'),
            (inventory['selection_definitions'],
             'id kind authority offset length raw_hex sha256', 'identity_only'),
        )
        for rows, keys, authority in shapes:
            for row in rows:
                self.assertEqual(set(row), set(keys.split()))
                self.assertEqual(row['authority'], authority)
        for row in inventory['skill_books']['definitions']:
            self.assertIsNone(row['server_resource_cost'])
            self.assertLessEqual(set(row['description_claims']),
                                 {'mp_cost', 'attack_range', 'target_scope'})
            for claim in row['description_claims'].values():
                self.assertEqual(set(claim),
                                 {'value', 'source_column', 'source_text', 'authority'})
                self.assertEqual(claim['authority'], 'description_only')
        for row in inventory['native_evidence']:
            self.assertEqual(set(row), set(
                'id rva_start rva_end_exclusive authority observation offset '
                'length raw_hex sha256'.split()))
            self.assertIn(row['authority'], {'display_arithmetic', 'display_state',
                'numeric_conversion', 'supplied_result_path', 'identity_only'})
        self.assertEqual({row['id'] for row in inventory['rules']}, set(rules.RULES))
        for row in inventory['rules']:
            self.assertEqual(set(row), set(
                'id status server_formula server_coefficients runtime_enabled '
                'skill_book_description_ids card_effect_description_indices '
                'description_search_terms native_evidence_ids boundary'.split()))
            self.assertEqual(row['status'], 'unknown')
            self.assertIsNone(row['server_formula'])
            self.assertIsNone(row['server_coefficients'])
            self.assertIs(row['runtime_enabled'], False)
        self.assertEqual(inventory['counts']['recovered_server_formulas'], 0)

    def test_recovered_metadata_cannot_export_damage_hit_or_crit_formulas(self):
        self.assert_evidence_boundary(self.inventory)

    def test_boundary_detects_in_memory_promotion_negative_controls(self):
        for category in ('damage', 'hit', 'crit'):
            for location in ('description', 'target', 'display', 'rule'):
                with self.subTest(category=category, location=location):
                    changed = copy.deepcopy(self.inventory)
                    if location == 'description':
                        row = changed['skill_books']['definitions'][0]['description_claims']['mp_cost']
                    elif location == 'target':
                        row = next(r for r in changed['selection_definitions']
                                   if (r['kind'], r['id']) == (0, 40))
                    elif location == 'display':
                        row = next(r for r in changed['native_evidence'] if r['id'] == 'display_scale')
                    else:
                        row = next(r for r in changed['rules'] if r['id'] == category)
                        row['server_coefficients'] = {'multiplier': 7}
                    if location != 'rule':
                        row[category + '_multiplier'] = 7
                    with self.assertRaises(AssertionError):
                        self.assert_evidence_boundary(changed)


if __name__ == '__main__':
    unittest.main()
