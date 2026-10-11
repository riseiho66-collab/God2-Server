"""Original skill-book flag path, stopping before the downstream UI call."""

import unittest

from tools.strike_lab.current_item_metadata import NativeItemMetadata
from tools.strike_lab.current_skill_book_availability import CONTEXT, NativeSkillBookAvailability


class SkillBookFlagTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = NativeSkillBookAvailability()

    def test_pinned_original_code_and_branch_table(self):
        native = self.native
        self.assertEqual(native.image_hash,
                         '149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763')
        self.assertEqual(native.path_hash,
                         '56c49e01e2b00986536f1c8343803771904ef1eccf1ded0aa0a533bcbca41135')
        self.assertEqual(native.lookup_hash,
                         'f81aede56ba1c4fc3916eae5ac3dddb529158861b7b88b36b1ce619a4a3dfce7')
        cases = [
            (0, (), 1, True),
            (0, ((3, 4),), 1, True),
            (0, ((1, 2),), 0, True),
            (0, ((3, 4), (1, 2)), 0, True),
            (0, ((3, 4), (5, 6), (1, 2)), 0, True),
            (1, (), 0, False),
            (1, ((1, 2),), 0, False),
            (255, (), 0, False),
            (255, ((3, 4),), 0, False),
        ]
        for tail, owned, selector, lookup in cases:
            with self.subTest(tail=tail, owned=owned):
                result = native.evaluate(tail, (1, 2), owned)
                self.assertEqual((result['selector'], result['lookup_entered']), (selector, lookup))
                self.assertEqual((result['item_code'], result['context']), (0x1234, CONTEXT))

    def test_source_loaded_tail_values_reach_same_original_branch(self):
        metadata = NativeItemMetadata()
        self.assertEqual(len(metadata.sections['SKB']['records']), 381)
        for index, expected in ((0, 0), (67, 1)):
            with self.subTest(source_record=index):
                loaded = metadata.item_row('SKB', index)
                tail = loaded['record'][0x12C]
                self.assertEqual(tail, expected)
                result = self.native.evaluate(tail, (1, 2), ())
                self.assertEqual(result['selector'], 1 if expected == 0 else 0)
                self.assertEqual(result['lookup_entered'], expected == 0)

    def test_native_downstream_prefix_stores_flag_and_selects_source(self):
        for index in (0, 5, 49):
            for tail, owned, flag, source in ((0, (), 1, 0x11111111),
                                              (0, ((1, 2),), 0, 0x22222222),
                                              (255, (), 0, 0x22222222)):
                with self.subTest(index=index, tail=tail, owned=owned):
                    result = self.native.follow_ui_prefix(tail, (1, 2), owned, index=index)
                    self.assertEqual((result['selector'], result['stored_at'], result['chosen_source']),
                                     (flag, 0x148 + 4 * index, source))

    def test_invalid_stage_inputs_are_rejected(self):
        bad = [(-1, (1, 2), ()), (256, (1, 2), ()), (0, (1,), ()),
               (0, (1, 256), ()), (0, (1, 2), ((1,),)),
               (0, (1, 2), ((1, 2),) * 9)]
        for tail, key, owned in bad:
            with self.subTest(tail=tail, key=key, owned=owned):
                with self.assertRaises(ValueError):
                    self.native.evaluate(tail, key, owned)
        for index in (-1, 50, 0.5):
            with self.subTest(index=index):
                with self.assertRaises(ValueError):
                    self.native.follow_ui_prefix(0, (1, 2), index=index)


if __name__ == '__main__':
    unittest.main()
