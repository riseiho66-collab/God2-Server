"""Native ABI boundaries only; no live client or successful world claim."""
import unittest

from tools.strike_lab.current_offline_entry_bridge import (
    boundary_probe, loop_trampoline, pinned_image)


class CurrentOfflineEntryBridgeTests(unittest.TestCase):
    def test_original_entry_frames_and_loop_call_boundary(self):
        result = boundary_probe()
        self.assertTrue(result['loop_prefix_only'])
        self.assertFalse(result['world_initializer_executed'])
        self.assertFalse(result['frame_function_executed'])

    def test_experimental_bridge_stops_on_real_loop_return(self):
        pinned_image()
        self.assertEqual(loop_trampoline().hex(),
                         'ff3530055e00b8002b4000ffd083c4048b0d38055e00b8e0554600ffd0cc0f0b')


if __name__ == '__main__':
    unittest.main()
