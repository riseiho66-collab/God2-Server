"""Retained 2A record -> C++ frame -> pinned decoder and actor projection.

Synthetic memory only: rendering, asset loading and resource helpers are stubbed.
This tests field consumption, not resource presence, live world or appearance.
"""
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess
import unittest

import test_current_route_advertisement as routes
import test_current_world_appearance as appearance
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_EBX, UC_X86_REG_ESI
from unicorn.x86_const import UC_X86_REG_ESP, UC_X86_REG_EIP

ROOT=Path(__file__).resolve().parents[2]
WORLD,ACTOR,SP=0x4000000,0x3700000,routes.SP


class CurrentWorldEntryTests(unittest.TestCase):
    vm=routes.CurrentRouteAdvertisementTests.vm
    call=routes.CurrentRouteAdvertisementTests.call
    run_to=routes.CurrentRouteAdvertisementTests.run_to
    decode=routes.CurrentRouteAdvertisementTests.decode

    @classmethod
    def setUpClass(cls):
        cls.fixture=json.loads((ROOT/'tests/fixtures/recovered-world-entry.json').read_text())
        cls.body=bytes.fromhex(cls.fixture['body_hex'])
        cls.image=(ROOT/'artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin').read_bytes()
        if hashlib.sha256(cls.image).hexdigest()!=cls.fixture['client_image_sha256']:
            raise AssertionError('Current client image changed')
        cls.binary=ROOT/'build/tests/Release/recovered-world-entry.exe'

    def wire(self,local_id):
        return bytes.fromhex(subprocess.check_output(
            [str(self.binary),'--dump',str(local_id)],text=True,timeout=5).strip())

    def test_retained_source_checksum_record_and_hashes(self):
        f=self.fixture
        source=Path(f['legacy_source']).read_bytes()
        self.assertEqual(hashlib.sha256(source).hexdigest(),f['legacy_source_sha256'])
        def constant(name):
            match=re.search(name+r'\s*=\s*Convert.FromHexString\(\s*"([0-9A-F]+)',source.decode())
            self.assertIsNotNone(match)
            return bytes.fromhex(match.group(1))
        stream=constant(f['legacy_stream_field']);key=constant(f['legacy_key_field'])
        self.assertEqual(hashlib.sha256(stream).hexdigest(),f['legacy_stream_sha256'])
        offset=f['source_frame_offset'];wire=stream[offset:offset+f['source_frame_size']]
        self.assertEqual(hashlib.sha256(wire).hexdigest(),f['source_frame_sha256'])
        plain=bytearray(wire);previous=f['legacy_initial_feedback']
        for i in range(2,len(plain)):
            previous=key[(i-2)&255]^((plain[i]+3-previous)&255);plain[i]=previous
        self.assertEqual(plain[-1],sum(b+0x3c for b in plain[:-1])&255)
        start=f['decoded_record_offset']
        self.assertEqual(plain[start:start+f['logical_record_size']],b'\x2a'+self.body)
        self.assertEqual(hashlib.sha256(self.body).hexdigest(),f['body_sha256'])
        size_fn=struct.unpack_from('<I',self.image,0x1324+4*0x2a)[0]-routes.BASE
        self.assertEqual(self.image[size_fn:size_fn+6],b'\xb8\x25\x00\x00\x00\xc3')

    def prepared_projection(self,body):
        vm=self.vm()
        vm.mem_map(ACTOR,0x6000)
        vm.mem_write(ACTOR,b'\xa5'*0x6000)
        # Only pages actually accessed by this bounded actor-projection path.
        offsets=(0,0xa7e05ec,0xa7f2f3c,0xaa36480,0x1539ad70,
                 0xa7f27d8,0xaac3708,0xaa25ec4,0x1539aed2)
        for page in sorted({(WORLD+offset)&~4095 for offset in offsets}):
            vm.mem_map(page,4096)
        vm.mem_write(SP+0x14,bytes(4))  # Initialized by 68177 before the receive.
        vm.mem_write(SP+0x28,bytes(body))
        vm.mem_write(SP+0x15c,struct.pack('<III',routes.BODY+0x800,ACTOR,routes.OUTPUT+0x800))
        vm.mem_write(routes.BODY+0x800,b'BoundHero\0')
        vm.reg_write(UC_X86_REG_ESP,SP)
        vm.reg_write(UC_X86_REG_EBX,WORLD)
        vm.reg_write(UC_X86_REG_ESI,0)
        return vm

    def project(self,body,expected_map=(2,15)):
        vm=self.prepared_projection(body);calls=[]
        # Callee-cleaned argument byte counts, with optional resource results null.
        services={0x5aa70:8,0x5a000:8,0x607d0:4,0x61ad0:20,
                  0x61270:16,0xff450:8,0xffa20:8,0x64280:4,0x68120:4}
        def service(uc,address,size,context):
            rva=address-routes.BASE
            if rva not in services:return
            sp=uc.reg_read(UC_X86_REG_ESP);count=services[rva]
            values=struct.unpack('<'+'I'*(1+count//4),uc.mem_read(sp,4+count))
            calls.append((rva,values[1:]))
            uc.reg_write(UC_X86_REG_EAX,0)
            uc.reg_write(UC_X86_REG_ESP,sp+4+count)
            uc.reg_write(UC_X86_REG_EIP,values[0])
        vm.hook_add(UC_HOOK_CODE,service)
        self.run_to(vm,0x681cf,0x68851)
        self.assertEqual(vm.reg_read(UC_X86_REG_EAX),1)
        self.assertEqual(bytes(vm.mem_read(ACTOR+0x4699,0x6000-0x4699)),b'\xa5'*(0x6000-0x4699))
        self.assertEqual(bytes(vm.mem_read(ACTOR+0xb7,10)),b'BoundHero\0')
        # mov cx/dx and push pass unspecified upper halves; callees consume
        # byte/word parameters. Do not interpret register residue as a map ID.
        resource=next(args for rva,args in calls if rva==0x5aa70)
        self.assertEqual((resource[0]&255,resource[1]&65535),expected_map)
        scene=next(args for rva,args in calls if rva==0x61ad0)
        self.assertEqual((scene[0]&255,scene[1]&65535,*scene[2:]),(*expected_map,0,0,WORLD))
        return vm

    def test_cpp_map_fields_reach_native_actor_and_resource_arguments(self):
        def command(area,scene):
            return [str(self.binary),'--dump','217','0','0','17','13',str(area),str(scene)]
        baseline=self.decode(self.vm(),bytes.fromhex(subprocess.check_output(
            command(2,15),text=True,timeout=5).strip()))
        for area,scene in ((2,4),(2,15),(1,0),(16,1023),(1,255),(16,256)):
            with self.subTest(area=area,scene=scene):
                wire=bytes.fromhex(subprocess.check_output(command(area,scene),text=True,timeout=5).strip())
                plain=self.decode(self.vm(),wire)
                self.assertEqual(plain[:27],baseline[:27])
                self.assertEqual(plain[29:-1],baseline[29:-1])
                vm=self.project(plain[3:-1],(area,scene))
                self.assertEqual(bytes(vm.mem_read(ACTOR+0x10,1)),b'\x02')
                self.assertEqual(struct.unpack('<H',vm.mem_read(ACTOR+0x18,2))[0],area)
                self.assertEqual(struct.unpack('<I',vm.mem_read(ACTOR+0x14,4))[0],scene)
                self.assertEqual(struct.unpack('<4I',vm.mem_read(ACTOR,16)),(217,1,17,13))
        for area,scene in ((0,4),(17,4),(63,4),(2,1024),(65536,4),(2,65536)):
            result=subprocess.run(command(area,scene),capture_output=True,timeout=5)
            self.assertNotEqual(result.returncode,0)
            self.assertFalse(result.stdout)

    def test_cpp_kind_is_independent_of_map_and_coordinates(self):
        prefix=[str(self.binary),'--dump','217','0','0','110','110','2','4']
        baseline=None
        for kind in range(4):
            wire=bytes.fromhex(subprocess.check_output(prefix+[str(kind)],text=True,timeout=5).strip())
            plain=self.decode(self.vm(),wire)
            masked=bytearray(plain[:-1]);masked[31]&=0xfc
            if baseline is None:baseline=masked
            self.assertEqual(masked,baseline)
            vm=self.project(plain[3:-1],(2,4))
            self.assertEqual(bytes(vm.mem_read(ACTOR+0x10,1)),bytes([kind]))
            self.assertEqual(struct.unpack('<I',vm.mem_read(WORLD+0x22c,4))[0],kind)
            self.assertEqual(struct.unpack('<4I',vm.mem_read(ACTOR,16)),(217,1,110,110))
            self.assertEqual(struct.unpack('<H',vm.mem_read(ACTOR+0x18,2))[0],2)
        for kind in (4,255,65536):
            result=subprocess.run(prefix+[str(kind)],capture_output=True,timeout=5)
            self.assertNotEqual(result.returncode,0)
            self.assertFalse(result.stdout)

    def test_cpp_frame_original_decoder_and_full_scalar_projection(self):
        for identity in (1,217,16383):
            with self.subTest(identity=identity):
                plain=self.decode(self.vm(),self.wire(identity))
                self.assertEqual(plain[:3],b'\x28\x00\x2a')
                self.assertEqual(plain[5:-1],self.body[2:])
                vm=self.project(plain[3:-1])
                fields=struct.unpack('<7I',vm.mem_read(ACTOR,28))
                self.assertEqual(fields[:4],(identity,1,17,13))
                self.assertEqual(bytes(vm.mem_read(ACTOR+0x10,1)),b'\x02')
                self.assertEqual(struct.unpack('<I',vm.mem_read(ACTOR+0x14,4))[0],15)
                self.assertEqual(struct.unpack('<H',vm.mem_read(ACTOR+0x18,2))[0],2)

    def test_current_area_bounds_reject_before_resource_helpers(self):
        for area in (0,17,63):
            with self.subTest(area=area):
                body=bytearray(self.body);body[24]=(body[24]&0xc0)|area
                vm=self.prepared_projection(body)
                self.run_to(vm,0x681cf,0x6885e)
                self.assertEqual(bytes(vm.mem_read(ACTOR,0x6000)),b'\xa5'*0x6000)

    def test_cpp_restored_coordinates_reach_original_actor(self):
        for x,y in ((17,13),(18,12),(0,0),(1,32767),(32767,1),(32767,32767),(255,256),(1024,1023)):
            with self.subTest(x=x,y=y):
                wire=bytes.fromhex(subprocess.check_output(
                    [str(self.binary),'--dump','217','0','0',str(x),str(y)],text=True,timeout=5).strip())
                baseline=self.decode(self.vm(),bytes.fromhex(subprocess.check_output(
                    [str(self.binary),'--dump','217','0','0'],text=True,timeout=5).strip()))
                plain=self.decode(self.vm(),wire)
                self.assertEqual(plain[:31],baseline[:31])
                self.assertEqual(plain[35:-1],baseline[35:-1])
                self.assertEqual(plain[31]&3,baseline[31]&3)
                vm=self.project(plain[3:-1])
                self.assertEqual(struct.unpack('<4I',vm.mem_read(ACTOR,16)),(217,1,x,y))
        for x,y in ((32768,0),(0,65535)):
            result=subprocess.run([str(self.binary),'--dump','217','0','0',str(x),str(y)],
                                  capture_output=True,timeout=5)
            self.assertNotEqual(result.returncode,0)
            self.assertFalse(result.stdout)

    def test_cpp_owned_variants_reach_original_component_setters(self):
        appearance.CurrentWorldAppearanceTests.setUpClass()
        harness=appearance.CurrentWorldAppearanceTests()
        baseline_variants,baseline_keys=harness.world(self.body)
        for first in range(7):
            for second in range(7):
                with self.subTest(first=first,second=second):
                    wire=bytes.fromhex(subprocess.check_output(
                        [str(self.binary),'--dump','217',str(first),str(second)],
                        text=True,timeout=5).strip())
                    plain=self.decode(self.vm(),wire)
                    profile=harness.profile(0,first,second)
                    expected=bytearray(appearance.appearance_projection(self.body,profile))
                    expected[20:24]=bytes((second<<5,0,0,0))
                    self.assertEqual(plain[3:-1],expected)
                    projected=self.project(plain[3:-1])
                    self.assertEqual(bytes(projected.mem_read(ACTOR+0x458c,4)),bytes(expected[20:24]))
                    variants,keys=harness.world(plain[3:-1])
                    self.assertEqual(variants,[first,second,*baseline_variants[2:]])
                    self.assertEqual(keys,baseline_keys)

    def test_identity_overflow_is_rejected_not_truncated(self):
        for identity in (0,16384,2**64-1):
            result=subprocess.run([str(self.binary),'--dump',str(identity)],capture_output=True,timeout=5)
            self.assertNotEqual(result.returncode,0)
            self.assertFalse(result.stdout)


if __name__=='__main__':unittest.main()
