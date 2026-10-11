"""Typed mode boundary validation, independent of real qualification evidence."""
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools/research'))
from trace_qualification.native_review import validate


class NativeTests(unittest.TestCase):
    def rows(self):
        base = dict(pid=1,tid=2,time=10)
        return [dict(base,eip=0x7000,esp=0x2000,expected=0x1000),
                dict(base,rip=0x7009,rsp=0x2000),dict(base,rip=0x198b,rsp=0x2004),
                dict(base,eip=0x1000,esp=0x2004)]

    def test_typed_match(self):
        self.assertTrue(validate(self.rows()))

    def test_wrong_mode_truncated_registers_fail(self):
        rows = self.rows()
        rows[-1]['eip'] = 0xd61074ac
        self.assertFalse(validate(rows))

    def test_identity_stack_and_order(self):
        for key,value in [('pid',2),('tid',3),('esp',0x2000),('time',9)]:
            rows = self.rows()
            rows[-1][key] = value
            self.assertFalse(validate(rows))


if __name__ == '__main__':
    unittest.main()
