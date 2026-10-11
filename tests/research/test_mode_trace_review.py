"""Synthetic boundary matching; no synthetic input certifies runtime claims."""
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools/research'))
from mode_trace_review import matching_return, exact_ret


class BoundaryTests(unittest.TestCase):
    def test_same_address_different_stack_is_not_return(self):
        a={'pid':1,'tid':2,'expected':0x1000,'sp':0x2000,'time':10}
        b={'pid':1,'tid':2,'pc':0x1000,'sp':0x2004,'time':11}
        self.assertTrue(matching_return(a,b))
        for key,value in [('sp',0x2204),('tid',3),('time',9),('pc',0x1004)]:
            self.assertFalse(matching_return(a,dict(b,**{key:value})))

    def test_marker_without_native_ret_is_rejected(self):
        text='EXACT_RET_BEFORE pid=1 tid=2 pc=0054ed7a sp=001afefc target=0054a46e time=a\nEXACT_RET_AFTER pid=1 tid=2 pc=0054a46e sp=001aff00 time=b\n'
        with self.assertRaises(ValueError):
            exact_ret(text)

    def test_exact_native_step_is_accepted(self):
        text = ('EXACT_RET_BEFORE pid=1 tid=2 pc=0054ed7a sp=001afefc target=0054a46e time=a\n'
                '0054ed7a c3 ret\n001afefc  0054a46e\n0:000> t\n'
                'eip=0054a46e esp=001aff00\n'
                'EXACT_RET_AFTER pid=1 tid=2 pc=0054a46e sp=001aff00 time=b\n')
        result = exact_ret(text)
        self.assertEqual(result['classification'], 'RETURNS')
        self.assertFalse(result['callee_trace_complete'])


if __name__=='__main__':
    unittest.main()
