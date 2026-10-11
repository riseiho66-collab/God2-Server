"""Pinned source references must not silently become destination scene IDs."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.strike_lab.town_scene_links import build_links


class TownSceneLinksTests(unittest.TestCase):
    def test_source_links_preserve_all_aliases_without_promoting_routes(self):
        result = build_links(ROOT.parent/'God2')
        links = result['links']
        self.assertEqual(len(links), 26)
        self.assertEqual(len({r['placement_index'] for r in links}), len(links))
        grocery, = [r for r in links if r['placement_index'] == 80]
        self.assertEqual(grocery['scene_candidates'], [15,50,53,65,73,90])
        self.assertEqual(grocery['can_record_indices'], [12])
        self.assertEqual(grocery['raw_fields'], [68,880,680,88,60,0,-1,-1,1,0])
        self.assertEqual(grocery['raw_model_entry_pairs'], [-1,-1,4,12,-1,-1,4,13])
        self.assertEqual((grocery['decoded_offset'], grocery['decoded_end_exclusive']), (37213,37266))
        for link in links:
            self.assertIsNone(link['destination_scene'])
            self.assertFalse(link['route_verified'])
            self.assertTrue(link['asset_path'].lower().endswith('.hmd'))
            self.assertEqual(len(link['source_record_sha256']), 64)
        self.assertEqual(result, build_links(ROOT.parent/'God2'))


if __name__ == '__main__':
    unittest.main()
