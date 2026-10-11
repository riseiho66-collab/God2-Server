"""Original 28 coordinate pairs and retained normal-entry control creation."""
import struct
import unittest

import test_current_battle_selector_population as population
from tools.strike_lab import current_battle_bootstrap as boot
from unicorn.x86_const import UC_X86_REG_EIP, UC_X86_REG_ESP


class CurrentBattleParticipantControlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixture = population.CurrentBattleSelectorPopulationTests
        fixture.setUpClass()
        check = fixture()
        check.test_original_population_and_third_window_return_on_retained_stack()
        check.test_third_window_and_original_three_bank_reset()
        check.test_nonzero_ownership_is_retained_separately_from_empty_menu_cache()
        check.test_native_name_copy_uses_original_writer_bytes()
        cls.b, cls.n = fixture.b, fixture.n
        cls.before = bytes(cls.n.vm.mem_read(boot.CONTROLS, boot.CONTROLS_SIZE))
        cls.selector_before = bytes(cls.n.vm.mem_read(boot.SELECTOR, 0x351c))
        cls.counts_before = dict(cls.b.counts)
        cls.calls = cls.b.continue_participant_controls()

    def test_native_coordinate_copy_and_exact_original_call_arguments(self):
        b, n = self.b, self.n
        self.assertEqual(boot.CONTROL_POSITIONS + 224, boot.ARENA)
        self.assertEqual(b.control_positions, bytes(n.vm.mem_read(0x571aa8, 224)))
        self.assertEqual(bytes(n.vm.mem_read(boot.CONTROL_POSITIONS, 224)), b.control_positions)
        self.assertEqual([(offset, size) for offset, size, _ in b.control_position_writes],
                         [(offset, 4) for offset in range(0, 224, 4)])
        pairs = list(struct.iter_unpack('<II', b.control_positions))
        self.assertEqual(len(pairs), 28)
        self.assertEqual(b.participant_control_args,
                         [(0x3d, x, y, 4, 0xffffd8f0, 1) for x, y in pairs])

    def test_all_28_real_control_calls_and_returns(self):
        self.assertEqual(self.calls, {pc: 28 for pc in (
            0x1116eb, 0x1116f0, 0x111700, 0x111705, 0x11171d,
            0x111722, 0x111736, 0x11173b, 0x111747, 0x11174c)})
        self.assertEqual(self.n.vm.reg_read(UC_X86_REG_EIP), boot.BASE + 0x11177d)
        self.assertEqual(self.n.vm.reg_read(UC_X86_REG_ESP), boot.SP - 0x1c)
        self.assertEqual(self.b.counts[boot.ENTRY], 1)
        self.assertTrue(self.b.participant_controls_completed)
        for pc, extra in ((0x1afe0, 56), (0x1b560, 28), (0x1e3d0, 28), (0x1e560, 28)):
            self.assertEqual(self.b.counts[pc] - self.counts_before.get(pc, 0), extra, hex(pc))

    def test_native_handle_storage_and_each_control_record(self):
        n, b = self.n, self.b
        self.assertEqual(b.participant_control_ids, list(range(28)))
        self.assertEqual(struct.unpack('<28I', n.vm.mem_read(boot.BATTLE + 0xa9df6cc, 112)), tuple(range(28)))
        self.assertEqual(n.u32(boot.CONTROLS + 0xa420), 28)
        sprites = []
        for index, (x, y) in enumerate(struct.iter_unpack('<II', b.control_positions)):
            record = boot.CONTROLS + 0x20 + index * 0xe8
            for offset, expected in ((0, 4), (4, 0x3d), (8, 0), (0x10, x), (0x14, y),
                                      (0x20, 2), (0x24, 4)):
                self.assertEqual(n.u32(record + offset), expected, (index, hex(offset)))
            sprites.append(n.u32(record + 0xc))
            action, sprite, dx, dy = struct.unpack('<4H', n.vm.mem_read(record + 0xe0, 8))
            self.assertEqual((action, dx, dy), (0x43, 0, 0))
            sprites.append(sprite)
        self.assertEqual(len(set(sprites)), 56)
        self.assertTrue(all(0 <= handle < 4096 for handle in sprites))

    def test_unused_records_and_source_catalog_are_retained(self):
        n, b = self.n, self.b
        start, end = 0x20 + 28 * 0xe8, 0x20 + 128 * 0xe8
        self.assertEqual(bytes(n.vm.mem_read(boot.CONTROLS + start, end - start)), self.before[start:end])
        self.assertEqual(bytes(n.vm.mem_read(boot.SELECTOR, 0x351c)), self.selector_before)
        self.assertEqual(bytes(n.vm.mem_read(boot.CHARACTER_ROOT, len(b.character_prepared))), b.character_prepared)
        self.assertEqual(bytes(n.vm.mem_read(b.skill_catalog['destination'], len(b.skill_catalog['body']))),
                         b.skill_catalog['body'])
        for address, before in b.selector_neighbors.items():
            self.assertEqual(bytes(n.vm.mem_read(address, len(before))), before)

    def test_repeat_is_rejected(self):
        with self.assertRaises(ValueError):
            self.b.continue_participant_controls()


if __name__ == '__main__':
    unittest.main()
