import unittest

from tools.strike_lab.current_item_battle_reach import source_to_reach, BATTLE
from tools.strike_lab.current_skill_target_setup import _reachable


class ItemReachTests(unittest.TestCase):
    def check_result(self, result):
        reach = result['battle_reach']
        self.assertEqual(result['target_masks'], list(_reachable(0, reach, (0x3fff, 0x3fff))))
        self.assertTrue(result['source_unchanged'])
        first, second = result['stages']
        self.assertEqual(first['outside_stack_writes'], [[0x117968, BATTLE + 0x64, 4, reach]])
        self.assertTrue(all(w[1] in (BATTLE + 0x434, BATTLE + 0x438) and w[2] == 4
                            for w in second['outside_stack_writes']))

    def test_actual_source_records(self):
        for section in ('WPN', 'EQU', 'TWP', 'TEQ'):
            with self.subTest(section=section):
                result = source_to_reach(section)
                self.assertEqual(result['source_value'] & 255, result['metadata_byte120'])
                self.assertEqual(result['battle_reach'], result['metadata_byte120'])
                self.assertEqual(result['stages'][0]['metadata_reads'], [[0x117959, 0x120, 1]])
                self.check_result(result)

    def test_native_missing_lookup_fallback(self):
        result = source_to_reach(missing=True)
        self.assertEqual(result['battle_reach'], 2)
        self.assertEqual(result['stages'][0]['metadata_reads'], [])
        self.check_result(result)

    def test_invalid_section(self):
        with self.assertRaises(ValueError):
            source_to_reach('NCP')


if __name__ == '__main__':
    unittest.main()
