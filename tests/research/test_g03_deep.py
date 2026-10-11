"""Synthetic stop validation, never usable as real runtime evidence."""
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[2]/'tools/research'))
from formalize_g03_deep import observe


class DeepStopTests(unittest.TestCase):
    def trace(self):
        points = [('PACKED',0x702001),('SOURCE',0x7023bf),('CANDIDATE',0x54a3e8),
            ('CALLEE_A',0x54f12a),('INTERNAL_A',0x77000000),('RETURN_A',0x54a446),
            ('CALLEE_B',0x54df7c),('INTERNAL_B',0x77001000),('RETURN_B',0x54a458),('WINDOW_END',0x5479bd)]
        rows = [f'DEEP_{name} pid=1 tid=2 pc={pc:x} time={i+1:x}' +
                (' base=400000' if name=='PACKED' else ' target=54a3e8' if name=='SOURCE' else '') for i,(name,pc) in enumerate(points)]
        return '\n'.join(rows)+'\neip=007023bf esp=001aff74\n001aff74  0054a3e8\neip=0054a3e8 esp=001aff78\n'

    def test_complete_trace_and_reject_thread_change(self):
        self.assertEqual(observe(self.trace())['RETURN_B']['pc'], 0x54a458)
        with self.assertRaises(ValueError):
            observe(self.trace().replace('tid=2', 'tid=3', 1))

    def test_reject_missing_stop_and_missing_native_registers(self):
        for bad in (self.trace().replace('DEEP_RETURN_A', 'MISSING'), self.trace().replace('esp=001aff78', 'esp=001aff74')):
            with self.assertRaises(ValueError):
                observe(bad)


if __name__ == '__main__':
    unittest.main()
