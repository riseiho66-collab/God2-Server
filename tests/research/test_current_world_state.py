"""Original dispatcher/scalar consumers of a retained world-state prefix.

Rendering/resource refresh routines are stubbed; no live client acceptance.
Historical values remain evidence, not a newly created character's attributes.
"""
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess
import unittest

import test_current_route_advertisement as routes
from unicorn import UC_HOOK_CODE, UC_PROT_READ, UC_PROT_WRITE
from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_EBP, UC_X86_REG_EBX
from unicorn.x86_const import UC_X86_REG_ECX, UC_X86_REG_EIP, UC_X86_REG_ESP

ROOT = Path(__file__).resolve().parents[2]
WORLD, ACTOR, COMPANION = 0x4000000, 0x3700000, 0x3710000
UI = WORLD + 0xa7f2f6c


class CurrentWorldStateTests(unittest.TestCase):
    vm = routes.CurrentRouteAdvertisementTests.vm
    run_to = routes.CurrentRouteAdvertisementTests.run_to
    decode = routes.CurrentRouteAdvertisementTests.decode
    call = routes.CurrentRouteAdvertisementTests.call

    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads((ROOT/'tests/fixtures/recovered-world-state.json').read_text())
        cls.provenance = json.loads((ROOT/'tests/fixtures/recovered-world-entry.json').read_text())
        cls.logical = bytes.fromhex(cls.fixture['logical_hex'])
        cls.image = (ROOT/'artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin').read_bytes()
        if hashlib.sha256(cls.image).hexdigest() != cls.provenance['client_image_sha256']:
            raise AssertionError('Current mapped client image changed')

    def test_retained_prefix_has_full_frame_checksum_and_exact_record_boundaries(self):
        p, f = self.provenance, self.fixture
        source = Path(p['legacy_source']).read_bytes()
        self.assertEqual(hashlib.sha256(source).hexdigest(), p['legacy_source_sha256'])
        def field(name):
            return bytes.fromhex(re.search(name+r'\s*=\s*Convert.FromHexString\(\s*"([0-9A-F]+)', source.decode())[1])
        stream, key = field(p['legacy_stream_field']), field(p['legacy_key_field'])
        self.assertEqual(hashlib.sha256(stream).hexdigest(), p['legacy_stream_sha256'])
        start = f['source_frame_offset']
        wire = stream[start:start+f['source_frame_size']]
        self.assertEqual(hashlib.sha256(wire).hexdigest(), f['source_frame_sha256'])
        plain, previous = bytearray(wire), p['legacy_initial_feedback']
        for i in range(2, len(plain)):
            previous = key[(i-2)&255] ^ ((plain[i]+3-previous)&255)
            plain[i] = previous
        self.assertEqual(sum(b+60 for b in plain[:-1])&255, plain[-1])
        self.assertEqual(plain[2:143], self.logical)
        self.assertEqual(hashlib.sha256(self.logical).hexdigest(), f['logical_sha256'])
        at = 0
        vm = self.vm()
        for record in f['records']:
            op, size = record['opcode'], record['length']
            self.assertEqual(self.logical[at], op)
            target = struct.unpack_from('<I', self.image, 0x1324+4*op)[0]
            vm.mem_write(routes.SP, struct.pack('<I', routes.BASE+0x1000))
            vm.reg_write(UC_X86_REG_ESP, routes.SP)
            self.run_to(vm, target-routes.BASE, 0x1000)
            self.assertEqual(vm.reg_read(UC_X86_REG_EAX), size)
            self.assertEqual(struct.unpack_from('<I', self.image, 0x6b5d4+4*op)[0],
                             routes.BASE+int(record['dispatch_rva'], 16))
            at += size
        self.assertEqual(at, len(self.logical))

    def projection(self, logical, companion):
        vm = self.vm()
        vm.mem_map(ACTOR, 0x6000)
        vm.mem_map(COMPANION, 0x1000)
        vm.mem_map((UI+0x86888)&~4095, 4096)
        vm.mem_map((UI+0x232ddc)&~4095, 4096)
        vm.mem_write(ACTOR, b'\xa5'*0x6000)
        vm.mem_write(COMPANION, b'\x5a'*0x1000)
        vm.mem_write(ACTOR+0xd0, struct.pack('<I', COMPANION if companion else 0))
        vm.mem_write(UI+0x86888, struct.pack('<I', ACTOR))
        # Exact logical bytes end at a mapped page boundary: unexpected packet
        # reads into a following record are not hidden by zero-filled padding.
        packet_page = 0x3720000
        vm.mem_map(packet_page, 4096)
        packet = packet_page+4096-len(logical)
        vm.mem_write(packet, logical)
        vm.mem_protect(packet_page, 4096, UC_PROT_READ)
        skipped = []
        refresh = {0xe63f0:4, 0xac070:12, 0xac2c0:4, 0xaa480:4,
                   0xe6710:4, 0xe6db0:4, 0xe72d0:12, 0x1077c0:None}
        def service(uc, address, size, _):
            rva = address-routes.BASE
            if rva not in refresh:
                return
            sp = uc.reg_read(UC_X86_REG_ESP)
            ret = struct.unpack('<I', uc.mem_read(sp, 4))[0]
            skipped.append(rva)
            uc.reg_write(UC_X86_REG_EAX, 0)
            uc.reg_write(UC_X86_REG_ESP, sp+4+(refresh[rva] or 0))
            uc.reg_write(UC_X86_REG_EIP, ret)
        vm.hook_add(UC_HOOK_CODE, service)
        vm.reg_write(UC_X86_REG_EBP, WORLD)
        vm.reg_write(UC_X86_REG_EBX, packet)
        vm.reg_write(UC_X86_REG_EAX, logical[0])
        vm.reg_write(UC_X86_REG_ESP, routes.SP)
        self.run_to(vm, 0x68b61, 0x6b517)
        self.assertEqual(vm.reg_read(UC_X86_REG_ESP), routes.SP)
        return bytes(vm.mem_read(ACTOR, 0x6000)), bytes(vm.mem_read(COMPANION, 4096))

    def check_projection(self, logical, companion):
        op, body = logical[0], logical[1:]
        actor, pet = self.projection(logical, companion)
        expected, expected_pet = bytearray(b'\xa5'*0x6000), bytearray(b'\x5a'*4096)
        expected[0xd0:0xd4] = struct.pack('<I', COMPANION if companion else 0)
        fields = {
            0x2b: [(0,0x5c,4),(8,0x64,4),(16,0x58,2)],
            0x2c: [(0,0x88,2),(4,0x8a,2),(8,0x8c,2),(12,0x8e,2),
                   (16,0xa4,4),(20,0xa8,4),(24,0xac,4),(28,0xb0,4),
                   (32,0xb4,4),(36,0xb8,2),(40,0xba,2),(44,0x98,4),
                   (48,0x94,4),(52,0xa0,4),(56,0x9c,4)],
            0x24: [(0,0x5c,4),(4,0x64,4),(8,0x60,4),(12,0x68,4)],
            0x39: [],
            0x22: [(0,0x26,1),(2,0x90,2),(12,0x58,2),(16,0x60,4),(20,0x68,4)]
        }[op]
        for source, dest, size in fields:
            expected[dest:dest+size] = body[source:source+size]
        if op == 0x22:
            for source, dest in ((4,0x78),(6,0x7c),(8,0x80),(10,0x84)):
                expected[dest:dest+4] = body[source:source+2]+b'\0\0'
        if companion:
            if op == 0x2b:
                for source, dest, size in ((4,0x2c,4),(12,0x34,2),(18,0x28,2)):
                    expected_pet[dest:dest+size] = body[source:source+size]
            elif op == 0x39:
                for source, dest, size in ((0,0x2c,4),(8,0x30,4),(4,0x34,2),(12,0x36,2)):
                    expected_pet[dest:dest+size] = body[source:source+size]
            elif op == 0x24:
                old, value, current_pet = 0xa5a5a5a5, int.from_bytes(body[:4],'little'), 0x5a5a5a5a
                if value < old:
                    expected_pet[0x2c:0x30] = max(0,current_pet-(old-value)).to_bytes(4,'little')
        self.assertEqual(actor, bytes(expected))
        self.assertEqual(pet, bytes(expected_pet))

    def test_original_dispatcher_and_scalar_writes_for_retained_records(self):
        at = 0
        for record in self.fixture['records']:
            logical = self.logical[at:at+record['length']]
            for companion in (False, True):
                with self.subTest(opcode=logical[0], companion=companion):
                    self.check_projection(logical, companion)
            at += record['length']

    def test_cpp_candidate_uses_original_decoder_and_checksum(self):
        wire = bytes.fromhex(subprocess.check_output(
            [str(ROOT/'build/tests/Release/recovered-world-entry.exe'), '--dump-state'],
            text=True, timeout=5).strip())
        self.assertEqual(wire[:2], b'\x90\0')
        plain = self.decode(self.vm(), wire)
        self.assertEqual(plain[2:-1], self.logical)

        vm = self.vm()
        codec = routes.NET+0x758
        vm.mem_write(routes.NET+0x2cb8, b'\x01')
        vm.mem_write(codec+0xc10, plain[2:-1])
        vm.mem_write(codec+0x1810, struct.pack('<II', len(self.logical), 0))
        vm.mem_protect(0x5b4da8&~4095, 4096, UC_PROT_READ|UC_PROT_WRITE)
        vm.mem_write(0x5b4da8, bytes(4))
        # RVA 1000 is the actual size dispatcher, so it cannot also be the
        # emulation return sentinel when executing the receive parser.
        def parser_call(entry):
            stop = routes.STACK+0x3ff0
            vm.mem_write(routes.SP, struct.pack('<II', stop, 1))
            vm.reg_write(UC_X86_REG_ESP, routes.SP)
            vm.reg_write(UC_X86_REG_ECX, routes.NET)
            self.run_to(vm, entry, stop-routes.BASE)
        at = 0
        for record in self.fixture['records']:
            parser_call(0x13420)
            self.assertEqual(vm.reg_read(UC_X86_REG_EAX), 0)
            size = struct.unpack('<I', vm.mem_read(routes.NET+0x2cc0, 4))[0]
            self.assertEqual(size, record['length'])
            parser_call(0x13650)
            pointer = vm.reg_read(UC_X86_REG_EAX)
            self.assertEqual(bytes(vm.mem_read(pointer, size)), self.logical[at:at+size])
            parser_call(0x13670)
            self.assertEqual(bytes(vm.mem_read(routes.NET+0x2cc0, 4)), bytes(4))
            at += size
        self.assertEqual(struct.unpack('<I', vm.mem_read(codec+0x1814, 4))[0], at)

    def test_scalar_widths_are_not_inferred_from_historical_zero_padding(self):
        for record in self.fixture['records']:
            for companion in (False, True):
                logical = bytes([record['opcode']])+bytes((i*37+129)&255 for i in range(record['length']-1))
                with self.subTest(opcode=logical[0], companion=companion):
                    self.check_projection(logical, companion)


if __name__ == '__main__':
    unittest.main()
