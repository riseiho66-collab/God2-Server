"""C++ codec output into pinned native stores and original EXP-bar conversion."""
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest

from test_current_role_progression import progression
from test_current_battle_command import build_fixture
from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_ECX, UC_X86_REG_ESP


class RoleProgressCodecTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='god2-role-progress-')
        cls.addClassCleanup(cls.temp.cleanup)
        cls.executable = build_fixture(Path(cls.temp.name), 'test_recovered_role_progress.cpp')

    def test_cpp_bounds_and_lossless_update(self):
        subprocess.run([str(self.executable)], check=True, timeout=20, capture_output=True)

    def test_cpp_output_to_native_role_companion_and_exp_conversion(self):
        values = (0, 1, 99, 100, 101, 2499, 2500, 9999, 10000, 32768, 65535)
        records = [b'\x2b' + struct.pack('<IIIHHHH', 76, 0x12345678, 26, 0x89ab, 0xa5c3, value, 4321)
                   for value in values]
        encoded = subprocess.run([str(self.executable), '--batch'], input='\n'.join(r.hex() for r in records)+'\n',
                                 text=True, capture_output=True, check=True, timeout=20).stdout.splitlines()
        self.assertEqual(len(encoded), len(records))
        for value, original, line in zip(values, records, encoded):
            with self.subTest(progress=value):
                fields = line.split()
                wire = bytes.fromhex(fields[0])
                self.assertEqual(wire, original)
                self.assertEqual(tuple(map(int, fields[1:])), (76,26,value,0x12345678,0x89ab,4321))
                p = progression.NativeProbe()
                p.vm.mem_write(p.BODY, wire[1:])
                p.vm.mem_write(p.STACK, struct.pack('<II', 0, p.BODY))
                p.vm.mem_write(p.ACTOR+0x26, b'\x37')
                before = bytes(p.vm.mem_read(p.ACTOR, 0x100))
                p.run(0xe6390, 0xe63c5)
                expected = bytearray(before)
                for src, dst, width in ((1,0x5c,4),(9,0x64,4),(17,0x58,2)):
                    expected[dst:dst+width] = wire[src:src+width]
                self.assertEqual(bytes(p.vm.mem_read(p.ACTOR,0x100)), bytes(expected))
                p.vm.mem_write(p.ACTOR+0xd0, struct.pack('<I',p.COMPANION))
                p.vm.mem_write(p.COMPANION,b'\xa5'*0x80)
                p.vm.reg_write(UC_X86_REG_ESP,p.STACK)
                p.vm.reg_write(UC_X86_REG_ECX,p.UI)
                p.run(0xaa3f0,0xaa422)
                companion = bytearray(b'\xa5'*0x80)
                for src,dst,width in ((5,0x2c,4),(13,0x34,2),(19,0x28,2)):
                    companion[dst:dst+width] = wire[src:src+width]
                self.assertEqual(bytes(p.vm.mem_read(p.COMPANION,0x80)),bytes(companion))
                p.vm.reg_write(UC_X86_REG_ESP,p.STACK)
                p.vm.reg_write(UC_X86_REG_ECX,p.UI)
                p.vm.mem_write(p.STACK,struct.pack('<II',0,p.ACTOR))
                before = bytes(p.vm.mem_read(p.ACTOR,0x100))
                p.run(0xac2c0,0xac2ff,((0xac2c0,0xac2ff),(0x149630,0x149657)))
                scale=struct.unpack('<f',bytes.fromhex('0ad7233c'))[0]
                rounded=struct.unpack('<f',struct.pack('<f',value*scale))[0]
                self.assertEqual(p.vm.reg_read(UC_X86_REG_EAX),int(rounded))
                self.assertEqual(bytes(p.vm.mem_read(p.ACTOR,0x100)),before)
                self.assertEqual(bytes(p.vm.mem_read(p.BODY,20)),wire[1:])


if __name__ == '__main__':
    unittest.main()
