"""Same-owner packet/selector state and retained original 81C20 continuation."""
import struct
import unittest

import test_current_battle_participant_controls as controls
from tools.strike_lab import current_battle_bootstrap as boot
from unicorn.x86_const import UC_X86_REG_EIP, UC_X86_REG_ESP


class CurrentBattleOwnerBridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixture = controls.CurrentBattleParticipantControlTests
        fixture.setUpClass()
        check = fixture()
        check.test_all_28_real_control_calls_and_returns()
        check.test_native_handle_storage_and_each_control_record()
        check.test_unused_records_and_source_catalog_are_retained()
        cls.b, cls.n = fixture.b, fixture.n
        cls.character_before = cls.b.character_prepared
        cls.owner_before = bytes(cls.n.vm.mem_read(boot.OWNER, boot.OWNER_SIZE))
        cls.pending_stack = bytes(cls.n.vm.mem_read(boot.SP - 0x1c, 0x24))
        with check.assertRaisesRegex(ValueError, 'produced appearance'):
            cls.b.continue_owner_bridge_prefix()
        # Explicit diagnostic body; no monster values or owned appearance claim.
        body = bytearray(b'\x6d' * 36)
        body[12:20] = bytes.fromhex('0163014001603100')
        cls.body = bytes(body)
        cls.b.prepare_character_appearance(cls.body)
        cls.appearance_result = cls.b.character_prepared
        check.assertEqual(bytes(cls.n.vm.mem_read(boot.SP - 0x1c, 0x24)), cls.pending_stack)
        check.assertEqual(cls.n.vm.reg_read(UC_X86_REG_EIP), boot.BASE + 0x11177d)
        check.assertEqual(cls.n.vm.reg_read(UC_X86_REG_ESP), boot.SP - 0x1c)
        cls.calls = cls.b.continue_owner_bridge_prefix()

    def test_objects_do_not_alias_and_character_uses_actual_owner(self):
        spans = [(boot.OWNER - 16, boot.OWNER + boot.OWNER_SIZE + 16),
                 (boot.CHARACTER_ROOT, boot.CHARACTER_ROOT + len(self.b.character_prepared)),
                 (boot.CHARACTER_STACK, boot.CHARACTER_STACK + 0x4000),
                 (boot.CHARACTER_PACKET, boot.CHARACTER_PACKET + 4096),
                 (boot.OWNER_DESCRIPTOR, boot.OWNER_DESCRIPTOR + 60),
                 (boot.BATTLE, boot.SECOND_LIST + 0x270)]
        for index, (lo, hi) in enumerate(spans):
            for other_lo, other_hi in spans[index + 1:]:
                self.assertTrue(hi <= other_lo or other_hi <= lo)
        self.assertEqual(boot.CHARACTER_UI, boot.OWNER)
        self.assertEqual(self.b.character.ui, boot.OWNER)
        self.assertEqual(self.n.u32(boot.OWNER + 0x86888), boot.CHARACTER_ROOT + 0x90)
        self.assertEqual(self.n.u32(boot.OWNER + 0x8688c), boot.CHARACTER_ROOT)

    def test_original_descriptor_stores_and_panel_constructor(self):
        n, b = self.n, self.b
        for offset, value in ((0xcff58, boot.BRIDGE), (0xcff5c, boot.MESSAGES),
                              (0xcff60, boot.OWNER_RENDERER), (0xcff64, boot.INPUT),
                              (0xcff68, boot.MOUSE), (0xcff6c, boot.ROOT_OBJECT),
                              (0xcff70, b.owner_metadata.TABLE)):
            self.assertEqual(n.u32(boot.OWNER + offset), value)
        self.assertEqual(b.owner_preparation_calls, {0x104160: 1, 0x1041a0: 1, 0x10419b: 1, 0x1042c0: 1})
        self.assertEqual(struct.unpack('<4I2H', n.vm.mem_read(boot.OWNER_PANELS, 20)),
                         (boot.BRIDGE, boot.MOUSE, boot.OWNER_RENDERER, boot.MESSAGES, 2, 0))
        expected = bytearray(b.owner_initial)
        for _, address, size, value in b.owner_binding_writes:
            if boot.OWNER <= address < boot.OWNER + boot.OWNER_SIZE:
                offset = address - boot.OWNER
                expected[offset:offset + size] = value.to_bytes(size, 'little')
        self.assertEqual(b.owner_prepared, expected)

    def test_appearance_is_original_writer_not_relaxed_read_guard(self):
        expected = bytearray(self.character_before)
        expected[0x4584:0x458c] = self.body[12:20]
        struct.pack_into('<I', expected, 0x28, 3)
        self.assertEqual(self.appearance_result, expected)
        writes = [(pc, address - boot.CHARACTER_ROOT, size, value)
                  for pc, address, size, value in self.b.appearance_stage['writes']
                  if boot.CHARACTER_ROOT <= address < boot.CHARACTER_ROOT + len(expected)]
        self.assertEqual(writes, [(0x68330, 0x4584, 4, int.from_bytes(self.body[12:16], 'little')),
                                 (0x6833f, 0x4588, 4, int.from_bytes(self.body[16:20], 'little')),
                                 (0x68348, 0x28, 4, 3)])
        self.assertIn((0x81c5a, boot.CHARACTER_ROOT + 0x28, 2), self.b.character_reads)
        with self.assertRaisesRegex(AssertionError, 'Unqualified character'):
            self.b._character_read(self.n.vm, 0, boot.CHARACTER_ROOT + 0x1c, 4, 0, None)

    def test_real_pending_call_reaches_mode_one_resource_boundary(self):
        self.assertEqual(self.calls, {pc: 1 for pc in (
            0x81c20, 0x1041a0, 0x104470, 0x25c80, 0x83410, 0x1a920, 0x81f08)})
        self.assertEqual(self.n.vm.reg_read(UC_X86_REG_EIP), boot.BASE + 0xc3080)
        self.assertEqual(self.n.vm.reg_read(UC_X86_REG_ESP), boot.SP - 0x3c)
        self.assertEqual(self.n.u32(boot.SP - 0x3c), boot.BASE + 0x81f0d)
        self.assertEqual(self.n.u32(boot.SP - 0x38), boot.CHARACTER_ROOT)
        self.assertEqual(self.b.counts[boot.ENTRY], 1)
        self.assertEqual(self.n.vm.mem_read(boot.OWNER + 0xe216c, 1), b'\x01')
        self.assertEqual(self.n.vm.mem_read(boot.OWNER + 0x232da4, 256), b'\xff' * 256)
        self.assertEqual(struct.unpack('<3I', self.n.vm.mem_read(boot.OWNER + 0x232ec0, 12)), (0, 0, 1))
        self.assertEqual(self.n.vm.mem_read(boot.OWNER + 0x232f36, 2), b'\x01\0')

    def test_visibility_is_written_by_original_surface_setter(self):
        handle = int.from_bytes(self.n.vm.mem_read(boot.OWNER_PANELS + 0x150c18, 2), 'little')
        self.assertLess(handle, 0x1000)
        resource = int.from_bytes(self.n.vm.mem_read(boot.OWNER_RENDERER + 0x10 + handle * 0x290 + 0xe, 2), 'little')
        self.assertLess(resource, 0x1388)
        destination = self.n.u32(boot.OWNER_RENDERER + 4) + resource * 200 + 0x125b
        writes = [(address, size, value) for pc, address, size, value in self.b.owner_bridge_writes
                  if pc == 0x25cb3]
        self.assertEqual(writes, [(destination, 1, 1)])
        self.assertEqual(bytes(self.n.vm.mem_read(destination, 1)), b'\x01')

    def test_exact_character_change_and_other_state_retained(self):
        expected = bytearray(self.appearance_result)
        expected[0x92:0x94] = b'\x03\0'
        self.assertEqual(self.b.character_prepared, expected)
        self.assertEqual(bytes(self.n.vm.mem_read(boot.CHARACTER_ROOT, len(expected))), expected)
        expected_owner = bytearray(self.owner_before)
        for _, address, size, value in self.b.owner_bridge_writes:
            if boot.OWNER <= address < boot.OWNER + boot.OWNER_SIZE:
                offset = address - boot.OWNER
                expected_owner[offset:offset + size] = value.to_bytes(size, 'little')
        self.assertEqual(bytes(self.n.vm.mem_read(boot.OWNER, boot.OWNER_SIZE)), expected_owner)
        for at in (boot.OWNER - 16, boot.OWNER + boot.OWNER_SIZE):
            self.assertEqual(bytes(self.n.vm.mem_read(at, 16)), b'\xa5' * 16)
        self.assertEqual(bytes(self.n.vm.mem_read(self.b.skill_catalog['destination'],
                                               len(self.b.skill_catalog['body']))), self.b.skill_catalog['body'])

    def test_repeated_or_missing_inputs_do_not_resume(self):
        with self.assertRaises(ValueError):
            self.b.continue_owner_bridge_prefix()
        for body in (b'', self.body[:-1], self.body + b'\0', self.body):
            with self.assertRaises(ValueError):
                self.b.prepare_character_appearance(body)


if __name__ == '__main__':
    unittest.main()
