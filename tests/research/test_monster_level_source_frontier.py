"""Keep historical star ranges, exact levels and current identities distinct."""
import json
from pathlib import Path
import tempfile
import unittest

from tools.strike_lab.monster_level_source_frontier_20260927 import (
    indexed_candidates, level_observation)


class MonsterLevelReferenceTests(unittest.TestCase):
    def test_owner_star_ranges_do_not_become_exact_levels(self):
        for literal, low in (('＊', 30), ('１＊', 30), ('2*', 40), ('３＊', 50),
                             ('4*', 60), ('７＊', 90), ('8*', 100)):
            row = level_observation(literal)
            self.assertIsNone(row['historical_exact_level'])
            self.assertEqual(row['historical_level_range'], dict(minimum=low, maximum=low + 9))

    def test_exact_numbers_and_bad_notation(self):
        for literal, value in (('３０', 30), ('32', 32), ('９９', 99)):
            row = level_observation(literal)
            self.assertEqual(row['historical_exact_level'], value)
            self.assertIsNone(row['historical_level_range'])
        for literal in ('0*', '?', '30~39', '-1', '2**'):
            with self.assertRaises(ValueError):
                level_observation(literal)

    def test_same_name_in_different_submaps_is_not_collapsed_or_promoted(self):
        text = ('Title (https://wiki2.gamer.com.tw/wiki.php?n=8591:test)\n'
                '# 冰魂谷\n## 聖狼穴\n尖刺頭目狼〖水〗 | Image | ５＊ |\n'
                '## 傲狼穴\n尖刺\n頭目狼\n〖水〗 | Image | ５＊ |\n')
        name_hex = '尖刺頭目狼'.encode('cp950').hex()
        catalog = dict(records=[dict(lookup_visible=True, name_bytes_hex=name_hex,
            area=1, scene=0, ordinal=1, record_sha256='a' * 64),
            dict(lookup_visible=True, name_bytes_hex=name_hex,
            area=2, scene=0, ordinal=1, record_sha256='b' * 64)])
        with tempfile.TemporaryDirectory() as folder:
            Path(folder, 'web-search-fixture.json').write_text(
                json.dumps(dict(result=text), ensure_ascii=False), encoding='utf-8')
            result = indexed_candidates(folder, catalog)
        self.assertEqual(result['summary']['observed_rows'], 2)
        self.assertEqual({r['map_label'] for r in result['observations']}, {'聖狼穴', '傲狼穴'})
        for row in result['observations']:
            self.assertEqual(len(row['current_name_candidates']), 2)
            self.assertFalse(row['runtime_eligible'])
            self.assertIsNone(row['current_native_level'])
            self.assertIsNone(row['historical_exact_level'])
        self.assertEqual(result['summary']['production_rows_written'], 0)


if __name__ == '__main__':
    unittest.main()
