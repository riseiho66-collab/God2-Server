"""Current native scene/camera, explicitly no live renderer or server E2E."""
import json
from pathlib import Path
import struct
import unittest

from tools.strike_lab.current_world_viewport import (
    NativeWorldViewport, WORLD, NPC_POOLS, ROLE_POOL, OPTIONAL_POOL, MAP_MANAGER)

ROOT = Path(__file__).resolve().parents[2]


class NativeWorldViewportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Retained packet is a lab stimulus, not original starting-state policy.
        cls.body = bytes.fromhex(json.loads(
            (ROOT / 'tests/fixtures/recovered-world-entry.json').read_text())['body_hex'])

    def test_loaded_indoor_camera_and_original_pool_propagation(self):
        n = NativeWorldViewport()
        indoor = n.enter_scene(self.body)
        before = struct.unpack('<ii', n.vm.mem_read(WORLD + 0x21c, 8))
        self.assertEqual(before, (1240, 540))
        self.assertEqual(n.position_viewport(), (840, 240))
        self.assertEqual(struct.unpack('<ii', n.vm.mem_read(indoor + 0x6c, 8)), (840, 240))
        for pool in NPC_POOLS:
            self.assertEqual(struct.unpack('<ii', n.vm.mem_read(pool + 0x68, 8)), (840, 240))
            self.assertTrue(all(n.u32(pool + 0x70 + 0x1d8*i) == 0xffffffff for i in range(256)))
        self.assertEqual(struct.unpack('<ii', n.vm.mem_read(ROLE_POOL + 0x10, 8)), (840, 240))
        self.assertTrue(all(n.u32(ROLE_POOL + 0x18 + 0x268*i) == 0xffffffff for i in range(128)))
        self.assertEqual(n.u32(OPTIONAL_POOL + 0x3491a8), 0)
        self.assertEqual(n.u32(WORLD + 0xaa25ec4), 1)
        self.assertEqual(n.u32(MAP_MANAGER + 0x30), 2)
        self.assertIn(0x430b0, n.viewport_visits)
        self.assertIn(0x422d0, n.viewport_visits)
        self.assertEqual(n.viewport_visits.count(0xca7b0), 2)
        self.assertIn(0xfb020, n.viewport_visits)
        self.assertIn(0x30f30, n.viewport_visits)
        self.assertNotIn(0x1ac30, n.viewport_visits)
        self.assertFalse(n.handles)
        self.assertEqual(n.u32(0), 0xffffffff)
        with self.assertRaises(ValueError):
            n.position_viewport()

    def test_requires_loaded_scene(self):
        n = NativeWorldViewport()
        with self.assertRaises(ValueError):
            n.position_viewport()
        self.assertFalse(n.viewport_started)


if __name__ == '__main__':
    unittest.main()
