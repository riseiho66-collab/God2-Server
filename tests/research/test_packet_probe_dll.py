import ctypes
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/strike_lab'))
from c2s0002 import key


class PacketProbeDllTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dll=ctypes.CDLL(str(ROOT/'build-strike-lab/Release/God2Probe.dll'))
        cls.decode=cls.dll.God2DecodePacket
        ptr=ctypes.POINTER(ctypes.c_ubyte)
        cls.decode.argtypes=[ptr,ctypes.c_uint,ptr,ctypes.c_uint,ctypes.c_uint,ptr,ctypes.c_uint]
        cls.decode.restype=ctypes.c_int
        cls.key=(ctypes.c_ubyte*256)(*key(ROOT))

    def run_decode(self,wire,feedback=0,capacity=None):
        source=(ctypes.c_ubyte*len(wire))(*wire)
        output=(ctypes.c_ubyte*258)(*([0xcc]*258))
        result=self.decode(source,len(wire),self.key,256,feedback,output,258 if capacity is None else capacity)
        return result,bytes(output)

    def test_real_six_byte_decode(self):
        wire=(ROOT/'artifacts/golden/server-select/C2S_0001.bin').read_bytes()
        result,plain=self.run_decode(wire)
        self.assertEqual(result,6)
        self.assertEqual(plain[:6],bytes.fromhex('0600a60000d8'))

    def test_frozen_frames(self):
        root=ROOT/'artifacts/golden/server-list/server-list-one-01'
        for name,opcode in (('S2C_0002.bin',1),('S2C_0003.bin',29),
                            ('S2C_SERVER_LIST_0001.bin',4),('S2C_0004.bin',10),('C2S_0002.bin',4)):
            with self.subTest(name=name):
                wire=(root/name).read_bytes();result,plain=self.run_decode(wire)
                self.assertEqual(result,len(wire));self.assertEqual(plain[2],opcode)

    def test_corruption_refuses_plaintext(self):
        wire=bytearray.fromhex('0600a3a3fdd5');wire[-1]^=1
        result,plain=self.run_decode(wire)
        self.assertEqual(result,-5);self.assertEqual(plain,b'\xcc'*258)

    def test_bad_frame_bounds(self):
        for wire,expected in ((b'\x06\x00',-1),(bytes(259),-1),
                              (bytes.fromhex('0680a3a3fdd5'),-3),
                              (bytes.fromhex('0700a3a3fdd5'),-4)):
            result,plain=self.run_decode(wire)
            self.assertEqual(result,expected);self.assertEqual(plain,b'\xcc'*258)

    def test_feedback_and_capacity_rejected(self):
        self.assertEqual(self.run_decode(bytes.fromhex('0600a3a3fdd5'),feedback=256)[0],-2)
        result,plain=self.run_decode(bytes.fromhex('0600a3a3fdd5'),capacity=5)
        self.assertEqual(result,-6);self.assertEqual(plain,b'\xcc'*258)


if __name__=='__main__':unittest.main()
