"""Synthetic native row parsing checks; not runtime evidence."""
import sys
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[2]/'tools/research'))
from startup_closure_ledgers import steps


class NativeRows(unittest.TestCase):
    def test_register_backed_instruction_only(self):
        text = ('eax=00000001 ebx=00000000\n'
                'eip=0054a446 esp=001aff00 ebp=001aff74\n'
                'cs=0023 ss=002b\nGod2+0x14a446:\n'
                '0054a446 59              pop ecx\n'
                '0054a447 85c0            test eax,eax\n')
        rows = steps(text)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['pc'], 0x54a446)
        self.assertTrue(rows[0]['boundary_agreement'])

    def test_wrong_disassembly_address_not_bound(self):
        text = 'eax=00000001\neip=0054a446 esp=001aff00\ncs=0023\nGod2:\n0054a447 59 pop ecx\n'
        self.assertEqual(steps(text), [])


if __name__ == '__main__':
    unittest.main()
