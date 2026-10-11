"""Compiled level snapshot into native stores and the real post-update clamp shim."""
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest
from test_current_role_progression import progression
from test_current_battle_command import build_fixture
from unicorn.x86_const import UC_X86_REG_ECX, UC_X86_REG_ESP


class RoleLevelCodecTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory(prefix='god2-role-level-')
        cls.addClassCleanup(cls.temp.cleanup)
        cls.executable=build_fixture(Path(cls.temp.name),'test_recovered_role_level.cpp')

    def test_cpp_bounds_lossless_and_level_replacement(self):
        subprocess.run([str(self.executable)],check=True,capture_output=True,timeout=20)

    def test_snapshot_and_actual_following_health_clamp(self):
        for level in (1,2,127,255):
            for hp_max,mp_max in ((120,80),(50,10),(0,80),(120,0),(0xffffffff,0x80000000)):
                with self.subTest(level=level,hp_max=hp_max,mp_max=mp_max):
                    wire=bytearray([0xa5]*25);wire[0]=0x22;wire[1]=level
                    struct.pack_into('<5H',wire,3,123,0,32767,32768,65535)
                    struct.pack_into('<H',wire,13,1250)
                    struct.pack_into('<II',wire,17,hp_max,mp_max)
                    output=subprocess.run([str(self.executable),'--batch'],input=wire.hex()+'\n',
                                          text=True,capture_output=True,check=True,timeout=20).stdout.strip()
                    encoded=bytes.fromhex(output)
                    self.assertEqual(encoded,bytes(wire))
                    p=progression.NativeProbe()
                    p.vm.mem_write(p.BODY,encoded[1:])
                    p.vm.mem_write(p.STACK,struct.pack('<II',0,p.BODY))
                    p.vm.mem_write(p.ACTOR+0x5c,struct.pack('<IIII',76,120,26,80))
                    before=bytes(p.vm.mem_read(p.ACTOR,0x100))
                    trace=p.run(0xe6b40,0xe6bd4)
                    expected=bytearray(before)
                    for src,dst,width in ((1,0x26,1),(3,0x90,2),(13,0x58,2),(17,0x60,4),(21,0x68,4)):
                        expected[dst:dst+width]=encoded[src:src+width]
                    for src,dst in ((5,0x78),(7,0x7c),(9,0x80),(11,0x84)):
                        expected[dst:dst+4]=encoded[src:src+2]+bytes(2)
                    self.assertEqual(bytes(p.vm.mem_read(p.ACTOR,0x100)),bytes(expected))
                    consumed={(address-p.BODY,size) for address,size in trace['reads'] if p.BODY<=address<p.BODY+24}
                    self.assertEqual(consumed,{(0,1),(2,2),(4,2),(6,2),(8,2),(10,2),(12,2),(16,4),(20,4)})
                    # E6B40 later calls E72D0. Execute that actual forwarding shim,
                    # but exclude preceding formatting E6DB0 and later UI drawing.
                    p.vm.reg_write(UC_X86_REG_ESP,p.STACK)
                    p.vm.reg_write(UC_X86_REG_ECX,p.UI)
                    p.vm.mem_write(p.STACK,struct.pack('<IIII',0,p.ACTOR,0,0))
                    if hp_max and mp_max:
                        trace=p.run(0xe72d0,0xac0b2,((0xe72d0,0xe72e4),(0xac070,0xac0b2)))
                        self.assertIn(0xe72df,trace['visited'])
                        struct.pack_into('<I',expected,0x5c,min(76,hp_max))
                        struct.pack_into('<I',expected,0x64,min(26,mp_max))
                    else:
                        p.run(0xe72d0,0xac2ad,((0xe72d0,0xe72e4),(0xac070,0xac2ad)))
                    self.assertEqual(bytes(p.vm.mem_read(p.ACTOR,0x100)),bytes(expected))
                    self.assertEqual(bytes(p.vm.mem_read(p.BODY,24)),encoded[1:])


if __name__=='__main__':
    unittest.main()
