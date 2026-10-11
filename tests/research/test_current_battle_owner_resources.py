"""Original world owner resource loading and release, without battle preload."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.strike_lab import current_battle_bootstrap as boot
from tools.strike_lab.current_role_doll_resources import BANK, STRIDE


class CurrentBattleOwnerResourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.n = n = boot.BootstrapResources()
        cls.b = b = boot.NativeBattleBootstrap.__new__(boot.NativeBattleBootstrap)
        b.native = n
        b.owner_metadata = boot.NativeItemMetadata(vm=n.vm)
        b._put(boot.MOUSE - 16, b'\xa5' * (boot.MOUSE_SIZE + 32))
        b._put(boot.DISPLAY - 16, b'\xa7' * (boot.DISPLAY_STATE_SIZE + 32))
        b._put32(boot.BRIDGE + 0xa8, boot.DISPLAY)
        b._prepare_owner()

    def test_pinned_field_reader_and_original_selected_slots(self):
        n = self.n
        self.assertEqual(n.string(n.owner_ui_records + 2 * 0x108 + 4), boot.world_ui.LITERAL_PATH)
        self.assertEqual(n.u32(n.owner_ui_records + 2 * 0x108), 2)
        self.assertEqual(n.u32(boot.OWNER + 0xe2164), n.owner_ui_records)
        self.assertIn(boot.world_ui.CWD + b'\\Data2\\Patch\\\\FieldComm3.csv', n.opens)
        for slot, (asset, _, _) in boot.OWNER_UI_ASSETS.items():
            with self.subTest(slot=slot, asset=asset):
                self.assertIn(asset, n.opens)
                self.assertIn((asset, slot, len(n.decoded[asset])), n.parser_inputs)
                self.assertEqual(n.u32(n.owner_ui_records + slot * 0x108), slot)
                self.assertNotEqual(n.u32(boot.OWNER_BANK + slot * STRIDE), 0xffffffff)
        self.assertEqual(n.u32(boot.OWNER_RENDERER + 0xc), boot.OWNER_BANK)
        self.assertNotEqual(n.u32(boot.OWNER_RENDERER + 0xc), BANK)

    def test_original_leave_releases_cached_sprite_before_global_reset(self):
        n, b = self.n, self.b
        self.assertEqual(b.owner_preparation_calls,
                         {0x104160: 1, 0x1041a0: 1, 0x10419b: 1, 0x1042c0: 1})
        self.assertEqual(bytes(n.vm.mem_read(boot.OWNER_PANELS + 0x150c18, 2)), b'\xff\xff')
        stores = [(pc, address, size, value) for pc, address, size, value in b.owner_binding_writes
                  if pc == 0x104306]
        self.assertEqual(stores, [(0x104306, boot.OWNER_PANELS + 0x150c18, 2, 0xffff)])
        self.assertEqual(n.u32(boot.OWNER + 0xcff60), boot.OWNER_RENDERER)

    def test_bank_mapping_and_source_records_do_not_alias(self):
        self.assertGreaterEqual(boot.OWNER_BANK, boot.OWNER + boot.OWNER_SIZE)
        self.assertGreaterEqual(boot.OWNER_RENDERER, boot.OWNER_BANK + 0x2a3000)
        self.assertNotEqual(self.n.u32(boot.OWNER_BANK + 2 * STRIDE), 0xffffffff)
        self.assertEqual(self.n.u32(BANK + 2 * STRIDE), 0xffffffff)
        self.assertNotEqual(self.n.u32(boot.OWNER_BANK + boot.item_binding.SLOT * STRIDE), 0xffffffff)
        self.assertEqual(bytes(self.n.vm.mem_read(boot.OWNER - 16, 16)), b'\xa5' * 16)
        self.assertEqual(bytes(self.n.vm.mem_read(boot.OWNER + boot.OWNER_SIZE, 16)), b'\xa5' * 16)
        with self.assertRaisesRegex(ValueError, 'overlaps'):
            self.n.load_owner_graphics()


if __name__ == '__main__':
    unittest.main()
