"""Compiled server epoch policy through the pinned native clock consumer."""
import os
from pathlib import Path
import subprocess
import unittest
import test_current_world_clock as oracle


class WorldClockServerNativeTests(unittest.TestCase):
    def test_compiled_policy_native_writer_and_ui_arithmetic(self):
        binary=Path(os.environ['GOD2_WORLD_CLOCK_CODEC_BINARY'])
        oracle.CurrentWorldClockTests.setUpClass()
        native=oracle.CurrentWorldClockTests(methodName='runTest')
        native.setUp()
        for epoch in (-(2**63),-14401,-14400,-1,0,1,3599,3600,14399,14400,2**63-1):
            with self.subTest(epoch=epoch):
                raw=bytes.fromhex(subprocess.check_output([str(binary),'--epoch',str(epoch)],text=True).strip())
                phase=epoch%14400
                self.assertEqual(raw,bytes((0x1a,phase//3600,(phase//60)%60,phase%60)))
                write=native.n.write_clock(raw,clock_ms=1000)
                self.assertEqual(write['value'],6*phase)
                self.assertEqual(write['timestamp'],1000)
                for now in (1000,11000):
                    read=native.n.read_clock(clock_ms=now)
                    total=6*phase+(6*(now-1000)*8589935//8589934592)
                    self.assertEqual((read['hours'],read['minutes']),((total//3600)%24,(total//60)%60))


if __name__=='__main__':
    unittest.main()
