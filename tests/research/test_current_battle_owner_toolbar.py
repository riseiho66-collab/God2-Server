"""Real toolbar construction up to the pending character consumer."""
import struct
import unittest
import test_current_battle_owner_map_completion as completion
from tools.strike_lab import current_battle_bootstrap as boot
from unicorn.x86_const import UC_X86_REG_EIP, UC_X86_REG_ESP


class CurrentBattleOwnerToolbarTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixture = completion.CurrentBattleOwnerMapCompletionTests
        fixture.setUpClass()
        fixture().test_native_controls_and_real_caller_return()
        fixture().test_exact_object_writes_and_unchanged_sources()
        cls.b, cls.n = b, n = fixture.b, fixture.n
        with cls().assertRaises(ValueError):
            b.continue_owner_toolbar()
        pending = (n.vm.reg_read(UC_X86_REG_EIP), n.vm.reg_read(UC_X86_REG_ESP),
                   bytes(n.vm.mem_read(boot.SP - 0x2000, 0x2400)))
        b.prepare_owner_toolbar_messages()
        b.prepare_owner_toolbar_cache()
        b.prepare_owner_toolbar_channel()
        cls().assertEqual(pending, (n.vm.reg_read(UC_X86_REG_EIP), n.vm.reg_read(UC_X86_REG_ESP),
                                   bytes(n.vm.mem_read(boot.SP - 0x2000, 0x2400))))
        cls.before = {at: bytes(n.vm.mem_read(at, size)) for at, size in (
            (boot.OWNER, boot.OWNER_SIZE), (boot.MOUSE, boot.MOUSE_SIZE),
            (boot.DISPLAY, boot.DISPLAY_STATE_SIZE), (boot.RENDERER, 0x291000))}
        cls.before[b.owner_toolbar_cache] = bytes(n.vm.mem_read(b.owner_toolbar_cache, 0x3ae54))
        expected_cache = bytearray(b'\xa5' * 0x3ae54)
        for at, size, value in b.owner_toolbar_cache_writes:
            if b.owner_toolbar_cache <= at < b.owner_toolbar_cache + len(expected_cache):
                start = at - b.owner_toolbar_cache
                expected_cache[start:start + size] = value.to_bytes(size, 'little')
        cls().assertEqual(cls.before[b.owner_toolbar_cache], bytes(expected_cache))
        cls.channel_before = bytes(n.vm.mem_read(b.owner_toolbar_channel, 0x67f4))
        expected_channel = bytearray(b'\xa5' * 0x67f4)
        for at, size, value in b.owner_toolbar_channel_writes:
            if b.owner_toolbar_channel <= at < b.owner_toolbar_channel + len(expected_channel):
                start = at - b.owner_toolbar_channel
                expected_channel[start:start + size] = value.to_bytes(size, 'little')
        cls().assertEqual(cls.channel_before, bytes(expected_channel))
        cls().assertEqual(cls.channel_before, bytes(0x67f4))
        cls.calls = b.continue_owner_toolbar()

    def test_native_resource_controls_and_pending_character_call(self):
        self.assertIn(boot.OWNER_UI_ASSETS[9][0], self.n.opens)
        self.assertEqual(len(self.b.owner_toolbar_text_bindings), 17)
        self.assertIn(boot.OWNER_UI_ASSETS[32][0], self.n.opens)
        self.assertEqual(self.calls[0xb0d20], 1)
        self.assertEqual(self.calls[0xb12b0], 1)
        self.assertEqual(self.calls[0x7e800], 1)
        self.assertGreaterEqual(self.calls[0x1057d0], 9)
        self.assertEqual(self.n.vm.reg_read(UC_X86_REG_EIP), boot.BASE + 0xe72d0)
        self.assertEqual(self.n.vm.reg_read(UC_X86_REG_ESP), boot.SP - 0x8c)
        self.assertEqual(struct.unpack('<4I', self.n.vm.mem_read(boot.SP - 0x8c, 16)),
                         (boot.BASE + 0xb129a, boot.CHARACTER_ROOT + 0x90, 0, 0))
        self.assertEqual(self.b.counts[boot.ENTRY], 1)

    def test_exact_writes_and_source_retention(self):
        for base in (boot.OWNER, boot.MOUSE, boot.DISPLAY, self.b.owner_toolbar_cache):
            expected = bytearray(self.before[base])
            for _, at, size, value in self.b.owner_toolbar_writes:
                if base <= at < base + len(expected):
                    expected[at - base:at - base + size] = value.to_bytes(size, 'little')
            self.assertEqual(bytes(self.n.vm.mem_read(base, len(expected))), bytes(expected))
        self.assertEqual(bytes(self.n.vm.mem_read(boot.RENDERER, 0x291000)), self.before[boot.RENDERER])
        self.b.owner_map_metadata._verify_records(bound=True)
        self.assertEqual(bytes(self.n.vm.mem_read(self.b.owner_toolbar_channel, 0x67f4)),
                         self.channel_before)
        with self.assertRaises(ValueError):
            self.b.continue_owner_toolbar()


if __name__ == '__main__':
    unittest.main()
