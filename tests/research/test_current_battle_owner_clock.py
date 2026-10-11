"""Original packet writer and real clock/control continuation on the battle VM."""
import unittest

import test_current_battle_owner_map_panel as panel
from tools.strike_lab import current_battle_bootstrap as boot
from unicorn.x86_const import UC_X86_REG_EIP, UC_X86_REG_ESP


class CurrentBattleOwnerClockTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixture = panel.CurrentBattleOwnerMapPanelTests
        fixture.setUpClass()
        check = fixture()
        check.test_real_map_window_and_text_calls_reach_clock_boundary()
        check.test_world_window_uses_original_rect_and_independent_resource_bank()
        cls.b, cls.n = b, n = fixture.b, fixture.n
        with cls().assertRaises(ValueError):
            b.continue_owner_map_clock(clock_ms=20000)
        cls.context_before = (n.vm.reg_read(UC_X86_REG_EIP), n.vm.reg_read(UC_X86_REG_ESP),
                              bytes(n.vm.mem_read(boot.SP - 0x1000, 0x1000)))
        cls.character_before = b.character_prepared
        cls.writer = b.prepare_character_clock(b'\x1a\x01\x00\x00', clock_ms=10000)
        cls.context_after = (n.vm.reg_read(UC_X86_REG_EIP), n.vm.reg_read(UC_X86_REG_ESP),
                             bytes(n.vm.mem_read(boot.SP - 0x1000, 0x1000)))
        cls.owner_before = bytes(n.vm.mem_read(boot.OWNER, boot.OWNER_SIZE))
        cls.battle_before = bytes(n.vm.mem_read(boot.RENDERER, 0x291000))
        cls.calls = b.continue_owner_map_clock(clock_ms=20000)

    def test_native_writer_preserves_pending_call_and_qualifies_only_clock(self):
        self.assertEqual(self.context_before, self.context_after)
        self.assertEqual((self.writer['timestamp'], self.writer['value']), (10000, 21600))
        expected = bytearray(self.character_before)
        expected[0x453c:0x4544] = self.writer['state']
        self.assertEqual(self.b.character_prepared, bytes(expected))
        self.assertEqual(self.writer['outcome'], 'writer_returned')
        with self.assertRaises(AssertionError):
            self.b._character_read(self.n.vm, 0, boot.CHARACTER_ROOT + 0x14, 2, 0, None)

    def test_real_clock_formats_and_returns_then_creates_map_controls(self):
        for pc in (0xc3640, 0xc3710, 0xc36de, 0xc311e, 0x149630, 0x1077c0,
                   0x1e500, 0x26700, 0x106550):
            self.assertEqual(self.calls[pc], 1, hex(pc))
        self.assertEqual(self.calls[0x1057d0], 3)
        self.assertEqual(self.b.owner_clock_labels[0]['text'], b'06:01')
        self.assertEqual(self.b.owner_clock_labels[0]['renderer'], boot.OWNER_RENDERER)
        text_record = self.b.owner_clock_text_records[0]
        self.assertEqual(text_record['text'], b'06:01')
        self.assertEqual(self.n.string(text_record['record'] + 0xc), b'06:01')
        self.assertEqual(self.b.owner_clock_samples[0]['value'], 20000)
        self.assertEqual(self.n.vm.reg_read(UC_X86_REG_EIP), boot.BASE + 0xc328b)
        self.assertEqual(self.n.vm.reg_read(UC_X86_REG_ESP), boot.SP - 0xf0)
        self.assertEqual(self.b.counts[boot.ENTRY], 1)

    def test_owner_write_footprint_and_source_retention(self):
        expected = bytearray(self.owner_before)
        for _, at, size, value in self.b.owner_map_clock_writes:
            if boot.OWNER <= at < boot.OWNER + boot.OWNER_SIZE:
                expected[at - boot.OWNER:at - boot.OWNER + size] = value.to_bytes(size, 'little')
        self.assertEqual(bytes(self.n.vm.mem_read(boot.OWNER, boot.OWNER_SIZE)), expected)
        self.assertEqual(bytes(self.n.vm.mem_read(boot.RENDERER, 0x291000)), self.battle_before)
        self.assertEqual(bytes(self.n.vm.mem_read(boot.CHARACTER_ROOT, len(self.b.character_prepared))),
                         self.b.character_prepared)
        for at in (boot.OWNER - 16, boot.OWNER + boot.OWNER_SIZE):
            self.assertEqual(bytes(self.n.vm.mem_read(at, 16)), b'\xa5' * 16)
        with self.assertRaises(ValueError):
            self.b.continue_owner_map_clock(clock_ms=20000)
        with self.assertRaises(ValueError):
            self.b.prepare_character_clock(b'\x1a\0\0\0', clock_ms=0)


if __name__ == '__main__':
    unittest.main()
