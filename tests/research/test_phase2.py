import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools/research'))
from trace_qualification.phase2 import marker, return_matches


class Phase2Tests(unittest.TestCase):
    def test_marker(self):
        self.assertEqual(marker('P2_STOP pc=00531e28 eax=4\n')['pc'],0x531e28)
        with self.assertRaises(ValueError):
            marker('no marker')

    def test_stdcall_return(self):
        entry=dict(pid=1,tid=2,ret=0x1000,sp=0x2000,time=10,api='connect')
        ret=dict(pid=1,tid=2,pc=0x1000,sp=0x2010,time=11)
        self.assertTrue(return_matches(entry,ret))
        for key,value in [('pid',3),('tid',3),('pc',0x1004),('sp',0x2004),('time',9)]:
            self.assertFalse(return_matches(entry,dict(ret,**{key:value})))


if __name__=='__main__':
    unittest.main()
