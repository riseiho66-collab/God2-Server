"""Execute a pinned client handler slice with synthetic state, not a live login.

Input comes from the C++ loopback candidate. Stop BEFORE the packet-consumption
call; no queue, authentication, UI transition or world acceptance is inferred.
"""
import hashlib
import struct
import sys
import unittest

import test_character_list_candidate_server as candidate
import test_post_server_select_server as post_select

sys.path.insert(0, str(post_select.ROOT / 'artifacts/tooling/crypto-oracle-python'))
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_MEM_WRITE, UC_PROT_READ, UC_PROT_EXEC
from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_EBX, UC_X86_REG_ESP, UC_X86_REG_EIP


IMAGE = post_select.ROOT / 'artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin'
IMAGE_SHA = '149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
ENTRY, STOP = 0x4148B9, 0x41495E
STACK, BODY, OBJECT, OUTPUT, CONVERTED = 0x3000000, 0x3100000, 0x3200000, 0x3300000, 0x3400000


class CurrentCharacterListHandlerTests(unittest.TestCase):
    server = post_select.PostSelectServerTests.server
    prefix = post_select.PostSelectServerTests.prefix
    candidate_server = candidate.CharacterListCandidateServerTests.candidate_server
    receive_candidate = candidate.CharacterListCandidateServerTests.receive_candidate

    @classmethod
    def setUpClass(cls):
        cls.image = IMAGE.read_bytes()
        if hashlib.sha256(cls.image).hexdigest() != IMAGE_SHA:
            raise AssertionError('Current mapped client image identity changed')

    def run_slice(self, plain, converted):
        self.assertEqual(len(plain), 78)
        self.assertEqual(plain[:3], b'\x4e\x00\x07')
        self.assertLessEqual(plain[3],2)
        self.assertEqual(plain[-1], sum(value + 0x3c for value in plain[:-1]) & 255)
        vm = Uc(UC_ARCH_X86, UC_MODE_32)
        vm.mem_map(0x414000, 4096, UC_PROT_READ | UC_PROT_EXEC)
        vm.mem_write(0x414000, self.image[0x14000:0x15000])
        for address, size in ((STACK, 4096), (BODY, 4096), (OBJECT, 0x5000),
                              (OUTPUT, 4096), (CONVERTED, 4096)):
            vm.mem_map(address, size)
            vm.mem_write(address, b'\xa5' * size)
        # Logical input is read-only and retains guards on either side.
        opcode = BODY + 0x100 + 2
        vm.mem_write(BODY + 0x100, plain)
        vm.mem_protect(BODY, 4096, UC_PROT_READ)
        sp = STACK + 0x800
        output = OUTPUT + 0x100
        converted_output = CONVERTED + 0x100 if converted else 0
        vm.mem_write(sp + 0x28, struct.pack('<II', output, converted_output))
        # Nonempty conversion reuses EBX and restores the saved session object
        # from this entry's established stack frame at RVA 14948.
        vm.mem_write(sp + 0x10, struct.pack('<I', OBJECT))
        vm.reg_write(UC_X86_REG_ESP, sp)
        vm.reg_write(UC_X86_REG_EAX, opcode)
        vm.reg_write(UC_X86_REG_EBX, OBJECT)
        writes = []

        def written(uc, access, address, size, value, context):
            writes.append((address, size))

        vm.hook_add(UC_HOOK_MEM_WRITE, written)
        vm.emu_start(ENTRY, STOP, timeout=100000, count=1024)
        self.assertEqual(vm.reg_read(UC_X86_REG_EIP), STOP, 'Bounded handler failed to reach consume call')
        self.assertEqual(bytes(vm.mem_read(output, 74)), plain[3:77])
        self.assertEqual(bytes(vm.mem_read(OBJECT + 0x4200, 1)), bytes([plain[4] & 1]))
        self.assertEqual(bytes(vm.mem_read(output - 1, 1)), b'\xa5')
        self.assertEqual(bytes(vm.mem_read(output + 74, 1)), b'\xa5')
        if converted:
            expected=bytearray(124);expected[0]=plain[3]
            for i in range(plain[3]):
                source=plain[5+36*i:41+36*i];dest=4+40*i
                name=source[:16].split(b'\0')[0]
                self.assertLess(len(name),16,'Unterminated wire name')
                expected[dest:dest+len(name)]=name
                for src,target in ((16,28),(17,29),(18,32)):
                    expected[dest+target]=source[src]
                expected[dest+34]=source[19]&7
            self.assertEqual(bytes(vm.mem_read(converted_output, 124)), bytes(expected))
            self.assertEqual(bytes(vm.mem_read(converted_output - 1, 1)), b'\xa5')
            self.assertEqual(bytes(vm.mem_read(converted_output + 124, 1)), b'\xa5')
        else:
            self.assertEqual(bytes(vm.mem_read(CONVERTED, 4096)), b'\xa5' * 4096)
        allowed = [(output, output + 74), (OBJECT + 0x4200, OBJECT + 0x4201), (sp - 4, sp)]
        if converted:
            allowed.append((converted_output, converted_output + 124))
            allowed.append((sp + 0x1c, sp + 0x20))
        for address, size in writes:
            self.assertTrue(any(start <= address and address + size <= end for start, end in allowed),
                            'Write outside pinned character-list handler destinations')

    def test_dispatch_and_length_table_match_candidate(self):
        self.assertEqual(self.image[0x14838:0x1483f], bytes.fromhex('8a0880f907747a'))
        self.assertEqual(struct.unpack_from('<I', self.image, 0x1340)[0], 0x4012D6)
        self.assertEqual(self.image[0x12d6:0x12dc], bytes.fromhex('b84b000000c3'))

    def test_cpp_wire_reaches_empty_handler_consume_boundary(self):
        with self.candidate_server() as (client, root):
            self.prefix(client)
            client.sendall(post_select.REQUEST.read_bytes())
            plain = self.receive_candidate(client)
        for converted in (False, True):
            with self.subTest(converted=converted):
                self.run_slice(plain, converted)

    def test_flags_are_not_high_byte_of_character_count(self):
        with self.candidate_server() as (client, root):
            self.prefix(client)
            client.sendall(post_select.REQUEST.read_bytes())
            plain = bytearray(self.receive_candidate(client))
        for flags in (1, 2, 255):
            with self.subTest(flags=flags):
                # Deliberately mutated synthetic input, never sent to the real client.
                plain[4] = flags
                plain[-1] = sum(value + 0x3c for value in plain[:-1]) & 255
                self.run_slice(bytes(plain), True)


if __name__ == '__main__':
    unittest.main()
