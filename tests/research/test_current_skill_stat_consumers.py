import unittest

from tools.strike_lab.current_skill_stat_consumers import (
    inventory, indexed_counterexample, wide_battle_inventory, range_field_consumer,
    CONTEXT, NET, SP, BATTLE,
)
from tools.strike_lab.current_skill_target_setup import _reachable


class ConsumerTests(unittest.TestCase):
    def test_pinned_inventory(self):
        report = inventory()
        hits = report['candidates']
        self.assertEqual(len(hits), 13)
        combat = [h for h in hits if 0x110000 <= h['rva'] < 0x131000]
        self.assertEqual([h['rva'] for h in combat],
                         [0x126201, 0x126218, 0x12622f, 0x126246])
        self.assertEqual([h['displacement'] for h in combat], [0x5e, 0x60, 0x62, 0x64])
        self.assertTrue(all(h['instruction'] == 'cmp' for h in combat))
        self.assertTrue(all(h['displacement'] == 0x60 for h in hits if h not in combat))

    def test_native_indexed_record_is_not_skill_field60(self):
        for index in (0, 1, 127):
            for value in (0, 1, 32768, 65535):
                result = indexed_counterexample(index, value)
                self.assertEqual(result['field_read'], [[CONTEXT + index * 0x268 + 0x60, 2]])
                self.assertEqual(result['argument'], value)
                self.assertEqual(result['stop_rva'], 0x1091c0)
                self.assertEqual(result['callee_this'], NET)
                self.assertEqual(result['field_offset_from_row'], 0x48)
                self.assertTrue(result['source_unchanged'])

    def test_bad_live_ins(self):
        for index, value in ((-1, 0), (128, 0), (0, -1), (0, 65536), (True, 1)):
            with self.assertRaises(ValueError):
                indexed_counterexample(index, value)

    def test_wide_scan_includes_rebased_pointer_and_new_getter(self):
        hits = wide_battle_inventory()['candidates']
        self.assertEqual(len(hits), 16)
        self.assertIn(0x11570a, [h['rva'] for h in hits])
        self.assertIn({'rva': 0x11c676, 'instruction': 'lea',
                       'operands': 'esi, [ecx + 0x60]'}, hits)

    def test_actual_range_binding_not_attack_defense(self):
        for actor in (0, 5, 9, 13):
            for reach in (0, 1, 3, 7):
                for masks in ((0x3fff, 0x3fff), (0x1001, 0x20)):
                    for secondary in (False, True):
                        result = range_field_consumer(actor, reach, masks, secondary=secondary)
                        self.assertEqual(tuple(result['masks']), _reachable(actor, reach, masks))
                        self.assertEqual(result['range_reads'],
                                         [[0x115718, 0x68, 1]] if secondary else [[0x11570a, 0x64, 1]])
                        self.assertEqual(result['stop_rva'], 0x114a5e)
                        self.assertEqual(result['stack_after'], SP)
                        self.assertTrue(result['input_masks_unchanged'])
                        self.assertTrue(all(w[1] in (BATTLE + 0x434, BATTLE + 0x438)
                                            and w[2] == 4 for w in result['outside_stack_writes']))

    def test_range_binding_changes_targets(self):
        a = range_field_consumer(0, 0, (0x3fff, 0x3fff))
        b = range_field_consumer(0, 1, (0x3fff, 0x3fff))
        self.assertNotEqual(a['masks'], b['masks'])
        for actor, reach, masks in ((14, 1, (1, 1)), (0, -1, (1, 1)),
                                    (0, 1, (0x4000, 1))):
            with self.assertRaises(ValueError):
                range_field_consumer(actor, reach, masks)


if __name__ == '__main__':
    unittest.main()
