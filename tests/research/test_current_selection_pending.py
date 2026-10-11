"""Pinned original S2C3B receive path before the pending-message callback."""
import unittest

from tools.strike_lab import current_selection_pending as pending


class CurrentSelectionPendingTests(unittest.TestCase):
    def test_real_egg_definition_reaches_only_pending_message_call(self):
        cases = pending.run()
        self.assertEqual([(c['source_section'], c['item']) for c in cases],
                         [('EGG', 9301)] * 2 + [('WPN', 1)] * 2 + [('EQU', 1001)] * 2)
        for clear, set_ in zip(cases[::2], cases[1::2]):
            self.assertEqual(clear['slot'], 30)
            self.assertEqual(clear['stop_rva'], 0x98f82)
            self.assertIsNone(clear['message_callback_rva'])
            self.assertEqual(set_['stop_rva'], 0x98f33)
            self.assertEqual(set_['message_callback_rva'], 0x4e140)
            self.assertEqual(set_['pending_before_callback'], 1)
            self.assertEqual((clear['slot_count_before_callback'], set_['slot_count_before_callback']), (1, 1))
        self.assertFalse(any(case['message_callback_executed'] for case in cases))

    def test_unqualified_pending_input_fails_before_execution(self):
        image = pending.instance.qualified_image(pending.IMAGE)
        metadata = pending.NativeItemMetadata()
        definition = metadata.item_row('EGG', 0)['record']
        with self.assertRaises(ValueError):
            pending.run_case(image, definition, 2)
        with self.assertRaises(ValueError):
            pending.run_case(image, bytes(len(definition)), 1)


if __name__ == '__main__':
    unittest.main()
