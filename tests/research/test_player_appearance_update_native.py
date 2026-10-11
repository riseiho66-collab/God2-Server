"""Compiled DA bytes -> pinned current native dispatch; no renderer claim.

The inherited oracle enforces current EXE SHA, read-only code, permitted writes,
exact boundary PCs and instruction budget. This test executes until461270 entry
or the missing-actor ignore boundary; it does not stub/execute the renderer.
GOD2_PLAYER_APPEARANCE_TEST_BINARY selects the standalone C++ test executable.
"""
import os
from pathlib import Path
import struct
import subprocess
import sys
import unittest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from tools.strike_lab import current_weapon_appearance_20260926 as native
from unicorn import x86_const as x

BINARY=Path(os.environ.get('GOD2_PLAYER_APPEARANCE_TEST_BINARY',
    ROOT/'artifacts/research/player-appearance-codec-20260926/player-appearance-update.exe'))


class CompiledWireOracle(native.Oracle):
    def route_compiled(self,packet,local,remote,selector,accessory):
        native.require(len(packet)==15 and packet[0]==0xda,'Exact compiled DA record required')
        identity,transform,scalar5,scalar6=struct.unpack_from('<HHBB',packet,1)
        native.require(transform==0,'Only ordinary branch is dynamically qualified here')
        v=self.v
        self.put(native.WORLD+0x1539683c,local)
        for i in range(128):self.put(native.MANAGER+0x18+i*0x268,0xffffffff)
        if remote:
            self.put(native.MANAGER+0x18,identity)
            v.mem_write(native.MANAGER+0x18+0x34,struct.pack('<H',selector))
            v.mem_write(native.MANAGER+0x18+0x40,struct.pack('<H',accessory))
        self.put(native.WORLD+0x15396880,(selector<<18)|(accessory<<10))
        guarded=b'\xcc'*32+packet+b'\xcc'*32
        v.mem_write(native.DATA,guarded)
        scalar_address=native.WORLD+0x1539aed1
        v.mem_write(scalar_address,b'\xa5'*4)
        actors_before=bytes(v.mem_read(native.MANAGER,0x14000))
        for register,value in ((x.UC_X86_REG_ESP,native.SP),(x.UC_X86_REG_EBP,native.WORLD),
                               (x.UC_X86_REG_EBX,native.DATA+32)):
            v.reg_write(register,value)
        self.writes=((scalar_address,scalar_address+4),)
        stop=self.run(0x469369,(0x461270,0x46b517),
            ((0x469369,0x4693cc),(0x469523,0x469541),(0x4fc990,0x4fc9d0),
             (0x503d30,0x503d88),(0x503f61,0x503f94)))
        native.require(stop==(0x461270 if local==identity or remote else 0x46b517),
                       'Compiled identity routed incorrectly (possibly masked)')
        native.require(bytes(v.mem_read(native.DATA,len(guarded)))==guarded,'Compiled wire/canary mutated')
        native.require(bytes(v.mem_read(native.MANAGER,0x14000))==actors_before,'Actor lookup changed actor state')
        native.require(bytes(v.mem_read(scalar_address,4))==
            (bytes((scalar5,0,0,scalar6)) if local==identity else b'\xa5'*4),'Raw scalar mismatch')
        if stop==0x461270:
            sp=v.reg_read(x.UC_X86_REG_ESP)
            first,second,component_pointer,_=struct.unpack('<4I',v.mem_read(sp+4,16))
            native.require((first&0xffff,second&0xffff)==(selector,accessory),'Prior actor selector mismatch')
            native.require(component_pointer==native.DATA+39,'Wrong component wire offset')
            native.require(bytes(v.mem_read(component_pointer,8))==packet[7:],'Full8-byte block lost')


class PlayerAppearanceUpdateNativeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not BINARY.is_file():raise AssertionError('Build standalone player appearance test first or set binary environment override')

    def cpp(self,*args,success=True):
        result=subprocess.run([str(BINARY),*map(str,args)],capture_output=True,text=True,timeout=10,
            creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        self.assertEqual(result.returncode==0,success,result.stderr)
        return result.stdout.strip()

    def test_cpp_contract_and_bad_cli_values(self):
        self.assertIn('Player appearance checks passed:',self.cpp())
        for arguments in (('-1','0','0','0'),('65536','0','0','0'),('0','65536','0','0'),
                          ('0','0','256','0'),('0','0','0','256')):
            self.cpp('--encode',*arguments,'0020004000008000',success=False)
        for components in ('','00'*7,'00'*9,'gg'*8):
            self.cpp('--encode',1,0,7,9,components,success=False)
        for wire in ('','da'+'00'*13,'da'+'00'*15,'36'+'00'*14):
            self.cpp('--roundtrip',wire,success=False)

    def test_existing_49_native_cases(self):
        report=native.verify()
        self.assertEqual((report['status'],report['cases']),('PASS',49))

    def test_cpp_wire_reaches_native_unmasked_self_remote_and_missing_routes(self):
        oracle=CompiledWireOracle()
        target=struct.unpack_from('<I',oracle.image,0x1324+4*0xda)[0]
        oracle.call(target,(),((target,target+6),))
        self.assertEqual(oracle.v.reg_read(x.UC_X86_REG_EAX),15)
        count=0
        for local in (1,217,0x3fff,0x4001,0xffff):
            for identity,remote in ((local,False),(local^0x4000,False),(local^0x4000,True)):
                for selector,accessory,components in ((0,0,'0020004000008000'),
                    (27,3,'ffffffffffffffff'),(91,119,'0001020304050607')):
                    with self.subTest(local=local,identity=identity,remote=remote,selector=selector):
                        scalar5=(count*31)&255;scalar6=255-scalar5
                        packet=bytes.fromhex(self.cpp('--encode',identity,0,scalar5,scalar6,components))
                        self.assertEqual(len(packet),15)
                        self.assertEqual(struct.unpack_from('<HHBB',packet,1),(identity,0,scalar5,scalar6))
                        self.assertEqual(packet[7:],bytes.fromhex(components))
                        # Actual compiled output is the native input memory,
                        # not a separately reconstructed Python packet.
                        oracle.route_compiled(packet,local,remote,selector,accessory)
                        self.assertEqual(self.cpp('--roundtrip',packet.hex()),packet.hex())
                        count+=1
        self.assertEqual(count,45)


if __name__=='__main__':unittest.main()
