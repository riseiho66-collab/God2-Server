"""Boundary evidence must not promote missing context into qualification."""
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools/research'))
from trace_qualification.review import pair, stack_words


class FrameTests(unittest.TestCase):
    def setUp(self):
        self.entry = dict(pc=0x3000, sp=0x2000, expected=0x1000, pid=1,
                          tid=2, time=10, native_line=1)
        self.returned = dict(pc=0x1000, sp=0x2004, pid=1, tid=2, time=11, native_line=5)
        self.words = {0x2000:0x1000, 0x2004:0x5555}

    def test_valid_context_is_only_partial(self):
        result = pair(self.entry, self.returned, self.words, self.words)
        self.assertEqual(result['result'], 'PARTIALLY_QUALIFIED')
        self.assertIsNone(result['nested_depth'])

    def test_context_change_fails(self):
        result = pair(self.entry, self.returned, self.words, {0x2004:0x9999})
        self.assertEqual(result['result'], 'FAILED')

    def test_missing_return_fails(self):
        self.assertEqual(pair(self.entry, None, self.words, {})['result'], 'FAILED')

    def test_identity_and_order_fail_closed(self):
        for key, value in [('pid',3), ('tid',3), ('sp',0x2010), ('pc',0x1004), ('time',9)]:
            with self.subTest(key=key):
                self.assertEqual(pair(self.entry, dict(self.returned, **{key:value}),
                                      self.words, self.words)['result'], 'FAILED')

    def test_stack_dump_not_command_echo(self):
        self.assertEqual(stack_words(['0:000> dd @esp L8', '001af9d8  775c9d0c 775a492f']),
                         {0x1af9d8:0x775c9d0c, 0x1af9dc:0x775a492f})


if __name__ == '__main__':
    unittest.main()
