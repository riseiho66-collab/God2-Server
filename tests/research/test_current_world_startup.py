"""Continuous original startup and complete scene function; no live E2E claim."""
import json
from pathlib import Path
import struct
import unittest

from tools.strike_lab.current_world_startup import (
    NativeWorldStartup, WORLD, BASE, DISPLAY_POOL, SECOND_DISPLAY, RECTANGLES, SCENE_BRIDGE)
from tools.strike_lab.current_world_startup_assets import ASSETS
from tools.strike_lab.current_world_actor import WORLD_COMPONENTS, MESSAGES
from tools.strike_lab.current_indoor_resources import SP, RETURN
from unicorn.x86_const import UC_X86_REG_EIP, UC_X86_REG_ESP

ROOT = Path(__file__).resolve().parents[2]


class WorldStartupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.n = n = NativeWorldStartup()
        cls.body = bytes.fromhex(json.loads((ROOT/'tests/fixtures/recovered-world-entry.json')
                                            .read_text())['body_hex'])
        n.bind_startup()
        cls.bound_effect = bytes(n.vm.mem_read(WORLD+0xaa36488, 0x30))
        cls.indoor = n.enter_full_scene(cls.body)

    def test_every_startup_asset_is_parsed_in_both_banks_and_checkpointed(self):
        n = self.n
        expected = []
        for slot, asset in enumerate(ASSETS):
            expected.extend([(asset.asset.rsplit('/', 1)[-1].lower(), slot, asset.decoded_size)]*2)
        self.assertEqual(n.startup_parser_inputs, tuple(expected))
        for state in n.startup_bank_states:
            self.assertEqual(state['next_slot'], len(ASSETS))
            self.assertEqual(state['saved_slot'], len(ASSETS))
        self.assertEqual(n.startup_visits.count(0x60a90), 7)
        self.assertEqual(n.startup_visits.count(0x1081c0), 2)
        for rva in (0x10fa30, 0x10fa50, 0x10dc70, 0x60b10):
            self.assertEqual(n.startup_visits.count(rva), 1)
        self.assertFalse(n.handles)

    def test_original_handle_writers_and_effect_manager_binding(self):
        n = self.n
        for pool in (DISPLAY_POOL, SECOND_DISPLAY):
            self.assertEqual(n.u32(pool), SCENE_BRIDGE)
            self.assertEqual(n.u32(pool+4), n.renderer_address)
            self.assertEqual(n.u32(pool+8), RECTANGLES)
            self.assertEqual(n.u32(pool+12), MESSAGES)
            self.assertEqual(n.u32(pool+16), n.title_slot)
        self.assertEqual(struct.unpack_from('<I', self.bound_effect)[0], n.renderer_address)
        self.assertEqual(struct.unpack_from('<H', self.bound_effect, 0x2c)[0], 4)
        for offset in (4, 6, 8, 10, 12, 0x22):
            self.assertEqual(struct.unpack_from('<H', self.bound_effect, offset)[0], 0xffff)
        self.assertEqual(n.u32(DISPLAY_POOL+0x18), 1)
        self.assertEqual(n.u32(WORLD+0x15383328), 6)
        owner = n.u32(WORLD+0x398)
        self.assertNotEqual(owner, 0)
        self.assertEqual(n.u32(owner), n.renderer_address)
        self.assertEqual(struct.unpack('<H', n.vm.mem_read(owner+8, 2))[0], 5)

    def test_complete_scene_returns_through_real_epilogue_with_real_display_record(self):
        n = self.n
        for rva in (0x100180, 0x100950, 0xff510, 0x108300, 0x1097d0,
                    0x1004f0, 0x1004f5, 0x10078f, 0x100930):
            self.assertEqual(n.scene_entry_visits.count(rva), 1)
        self.assertEqual(n.vm.reg_read(UC_X86_REG_EIP), RETURN)
        self.assertEqual(n.vm.reg_read(UC_X86_REG_ESP), SP+12)
        self.assertEqual(n.u32(0), 0xffffffff)
        self.assertTrue(n.scene_loaded and n.viewport_positioned)
        self.assertNotEqual(self.indoor, 0)
        label = n.u32(WORLD+0x1539ad80)
        self.assertLess(label, 4096)
        record = DISPLAY_POOL+0x1c+label*0xa7e0
        self.assertEqual(n.u32(record), 2)
        self.assertLess(n.u32(record+0x10), 3072)
        self.assertEqual(n.u32(WORLD_COMPONENTS+0x28), n.renderer_address)
        self.assertEqual(struct.unpack('<ii', n.vm.mem_read(WORLD+0x21c, 8)), (840, 240))
        self.assertEqual(n.music_resolver_calls, [(2, 2, 15, 0)])
        self.assertEqual(n.music_results, [0])

    def test_fresh_startup_and_single_scene_guards(self):
        with self.assertRaises(ValueError):
            self.n.bind_startup()
        with self.assertRaises(ValueError):
            self.n.enter_full_scene(self.body)
        with self.assertRaises(ValueError):
            self.n.finish_scene()


if __name__ == '__main__':
    unittest.main()
