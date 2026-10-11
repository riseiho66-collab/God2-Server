"""Native map source loading and lookups on the retained battle initializer VM."""
import struct
import unittest

import test_current_battle_owner_clock as clock
from tools.strike_lab import current_battle_bootstrap as boot
from unicorn.x86_const import UC_X86_REG_EIP, UC_X86_REG_ESP


class CurrentBattleOwnerMapMetadataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixture = clock.CurrentBattleOwnerClockTests
        fixture.setUpClass()
        fixture().test_real_clock_formats_and_returns_then_creates_map_controls()
        cls.b, cls.n = b, n = fixture.b, fixture.n
        with cls().assertRaises(ValueError):
            b.continue_owner_map_metadata()
        cls.before = (n.vm.reg_read(UC_X86_REG_EIP), n.vm.reg_read(UC_X86_REG_ESP),
                      bytes(n.vm.mem_read(boot.SP - 0x2000, 0x2000)))
        cls.provenance = b.prepare_owner_map_metadata()
        cls.selector = b.prepare_character_map_selector(2)
        cls.after = (n.vm.reg_read(UC_X86_REG_EIP), n.vm.reg_read(UC_X86_REG_ESP),
                     bytes(n.vm.mem_read(boot.SP - 0x2000, 0x2000)))
        cls.owner_before = bytes(n.vm.mem_read(boot.OWNER, boot.OWNER_SIZE))
        cls.renderer_before = bytes(n.vm.mem_read(boot.OWNER_RENDERER, 0x291000))
        cls.battle_before = bytes(n.vm.mem_read(boot.RENDERER, 0x291000))
        cls.calls = b.continue_owner_map_metadata()

    def test_same_vm_native_loader_preserves_retained_call_and_catalog_binding(self):
        b, n = self.b, self.n
        self.assertEqual(self.before, self.after)
        self.assertIs(b.owner_map_metadata.vm, n.vm)
        self.assertEqual(self.provenance['count'], 144)
        self.assertEqual(self.provenance['static_count'], 143)
        self.assertEqual(n.u32(boot.OWNER + 0xcff70), b.owner_metadata.TABLE)
        self.assertEqual(b.owner_map_metadata.table, b.owner_metadata.TABLE)
        self.assertEqual(b.owner_map_metadata.load_trace['pcs'][0x59d55], 144)
        self.assertEqual(b.owner_map_metadata.bind_trace['pcs'][0x59ecc], 143)
        b.owner_map_metadata._verify_records(bound=True)

    def test_original_lookups_cache_and_sprite_arguments(self):
        b, n = self.b, self.n
        self.assertEqual(self.calls[0x59d80], 2)
        self.assertEqual(self.calls[0xc32b6], 1)
        self.assertEqual(self.calls[0xc32cd], 1)
        self.assertEqual(n.vm.reg_read(UC_X86_REG_EIP), boot.BASE + 0xc332c)
        self.assertEqual(n.vm.reg_read(UC_X86_REG_ESP), boot.SP - 0x104)
        selected = b.owner_map_selected
        self.assertEqual(selected['panel_words'], (47, 1))
        self.assertEqual(selected['metadata'], boot.BASE + 0x18b804)
        self.assertEqual(n.u32(boot.OWNER + 0x8aa4c), selected['record'])
        args = struct.unpack('<5I', n.vm.mem_read(boot.SP - 0x104, 20))
        handle = struct.unpack('<H', n.vm.mem_read(boot.OWNER + 0x232da6, 2))[0]
        self.assertEqual((args[0] & 0xffff, args[1] & 0xffff, args[2], args[3], args[4]),
                         (handle, 47, 4, 1, boot.BASE + 0x1b7aa8))
        self.assertIn((0xc3315, selected['metadata'] + 0x20, 2, b'\x2f\x00'),
                      b.owner_map_lookup_reads)
        self.assertEqual(b.counts[boot.ENTRY], 1)

    def test_only_map_cache_changes_and_continuation_is_single_use(self):
        b, n = self.b, self.n
        expected = bytearray(self.owner_before)
        struct.pack_into('<I', expected, 0x8aa4c, b.owner_map_selected['record'])
        self.assertEqual(bytes(n.vm.mem_read(boot.OWNER, boot.OWNER_SIZE)), bytes(expected))
        self.assertEqual(bytes(n.vm.mem_read(boot.OWNER_RENDERER, 0x291000)), self.renderer_before)
        self.assertEqual(bytes(n.vm.mem_read(boot.RENDERER, 0x291000)), self.battle_before)
        self.assertEqual(bytes(n.vm.mem_read(boot.CHARACTER_ROOT, len(b.character_prepared))),
                         b.character_prepared)
        self.assertEqual(bytes(n.vm.mem_read(b.skill_catalog['destination'], boot.skill_catalog.BODY_SIZE)),
                         b.skill_catalog['body'])
        for at in (boot.OWNER - 16, boot.OWNER + boot.OWNER_SIZE):
            self.assertEqual(bytes(n.vm.mem_read(at, 16)), b'\xa5' * 16)
        with self.assertRaises(ValueError):
            b.prepare_owner_map_metadata()
        with self.assertRaises(ValueError):
            b.continue_owner_map_metadata()


if __name__ == '__main__':
    unittest.main()
