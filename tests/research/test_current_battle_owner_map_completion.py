"""Retained original C3080 map initialization returns to 81F0D."""
import unittest
import test_current_battle_owner_map_label as label
from tools.strike_lab import current_battle_bootstrap as boot
from unicorn.x86_const import UC_X86_REG_EIP, UC_X86_REG_ESP


class CurrentBattleOwnerMapCompletionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixture = label.CurrentBattleOwnerMapLabelTests
        fixture.setUpClass()
        fixture().test_coordinate_writer_and_native_label_return()
        fixture().test_sources_and_write_footprint_preserved()
        cls.b, cls.n = b, n = fixture.b, fixture.n
        cls.before = {at: bytes(n.vm.mem_read(at, size)) for at, size in (
            (boot.OWNER, boot.OWNER_SIZE), (boot.MOUSE, boot.MOUSE_SIZE),
            (boot.DISPLAY, boot.DISPLAY_STATE_SIZE),
            (boot.RENDERER, 0x291000))}
        cls.calls = b.complete_owner_map_panel()

    def test_native_controls_and_real_caller_return(self):
        self.assertEqual(self.calls[0x106c70], 11)
        self.assertEqual(self.calls[0x1073e0], 9)
        self.assertEqual(self.calls[0x104e30], 1)
        self.assertEqual(self.calls[0x105230], 1)
        self.assertEqual(self.calls[0xc3a50], 1)
        self.assertEqual(self.calls[0xc35e4], 1)
        self.assertEqual(self.n.vm.reg_read(UC_X86_REG_EIP), boot.BASE + 0x81f0d)
        self.assertEqual(self.n.vm.reg_read(UC_X86_REG_ESP), boot.SP - 0x34)
        self.assertEqual(self.b.counts[boot.ENTRY], 1)

    def test_exact_object_writes_and_unchanged_sources(self):
        for base in (boot.OWNER, boot.MOUSE, boot.DISPLAY):
            expected = bytearray(self.before[base])
            for _, at, size, value in self.b.owner_map_completion_writes:
                if base <= at < base + len(expected):
                    expected[at - base:at - base + size] = value.to_bytes(size, 'little')
            self.assertEqual(bytes(self.n.vm.mem_read(base, len(expected))), bytes(expected))
        self.assertEqual(bytes(self.n.vm.mem_read(boot.RENDERER, 0x291000)), self.before[boot.RENDERER])
        self.b.owner_map_metadata._verify_records(bound=True)
        for at in (boot.OWNER - 16, boot.OWNER + boot.OWNER_SIZE):
            self.assertEqual(bytes(self.n.vm.mem_read(at, 16)), b'\xa5' * 16)
        with self.assertRaises(ValueError):
            self.b.complete_owner_map_panel()


if __name__ == '__main__':
    unittest.main()
