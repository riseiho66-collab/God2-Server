"""Current builder instructions + synthetic memory + local C++ TCP, not live UI."""
import hashlib
import socket
import struct
import sys
import unittest

import test_post_server_select_server as prefix
import test_character_list_candidate_server as candidate

sys.path.insert(0, str(prefix.ROOT / 'artifacts/tooling/crypto-oracle-python'))
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_PROT_READ, UC_PROT_EXEC
from unicorn.x86_const import UC_X86_REG_ECX, UC_X86_REG_ESP, UC_X86_REG_EIP
from c2s0002 import key


def builder_payload():
    image = (prefix.ROOT / 'artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin').read_bytes()
    if hashlib.sha256(image).hexdigest() != '149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763':
        raise AssertionError('Current builder image changed')
    vm = Uc(UC_ARCH_X86, UC_MODE_32)
    vm.mem_map(0x414000, 4096, UC_PROT_READ | UC_PROT_EXEC)
    vm.mem_write(0x414000, image[0x14000:0x15000])
    stack, obj, payload = 0x3000800, 0x3100000, 0x3200100
    for address, size in ((0x3000000, 4096), (obj, 0x3000), (0x3200000, 4096)):
        vm.mem_map(address, size)
    vm.mem_write(stack, struct.pack('<II', 0, payload))
    vm.mem_write(obj + 0x2cb8, b'\x01')
    original = b'LabCreate\0' + bytes(5) + bytes(range(15,44))
    vm.mem_write(payload, original)
    vm.reg_write(UC_X86_REG_ESP, stack)
    vm.reg_write(UC_X86_REG_ECX, obj)
    # Stop before the actual queue/flush functions; no I/O is emulated.
    vm.emu_start(0x414cc0, 0x414cda, timeout=100000, count=32)
    if vm.reg_read(UC_X86_REG_EIP) != 0x414cda:
        raise AssertionError('Builder did not reach its queue call')
    arguments = struct.unpack('<III', vm.mem_read(vm.reg_read(UC_X86_REG_ESP), 12))
    if arguments != (0x1b, payload, 44):
        raise AssertionError('Builder opcode/pointer/length changed')
    result = bytes(vm.mem_read(payload, 44))
    expected = bytearray(original); expected[40] = 4
    if result != expected:
        raise AssertionError('Builder modified unexpected payload fields')
    return result


def request_wire(payload, opcode=0x1b):
    plain = bytearray(b'\x30\x00' + bytes([opcode]) + payload + b'\x00')
    plain[-1] = sum(value + 0x3c for value in plain[:-1]) & 255
    k = key(prefix.ROOT)
    wire = bytearray(plain[:2]); previous = 0
    for index, value in enumerate(plain[2:]):
        wire.append(((value ^ k[index]) + previous - 3) & 255)
        previous = value
    return bytes(wire)


class CharacterCreateServerTests(unittest.TestCase):
    server = prefix.PostSelectServerTests.server
    closed = prefix.PostSelectServerTests.closed
    prefix = prefix.PostSelectServerTests.prefix
    candidate_server = candidate.CharacterListCandidateServerTests.candidate_server
    receive_candidate = candidate.CharacterListCandidateServerTests.receive_candidate

    @classmethod
    def setUpClass(cls):
        cls.payload = builder_payload()
        cls.wire = request_wire(cls.payload)

    def select(self, client):
        self.prefix(client)
        client.sendall(prefix.REQUEST.read_bytes())
        self.receive_candidate(client)

    def assert_silent(self, client):
        client.settimeout(.1)
        with self.assertRaises(socket.timeout):
            client.recv(1)
        client.settimeout(1)

    def test_builder_request_is_decoded_after_selection(self):
        with self.candidate_server() as (client, root):
            self.select(client)
            client.sendall(self.wire)
            self.assert_silent(client)
            log = (root / 'stdout.log').read_text()
            self.assertIn('CHARACTER_CREATE_FRAME_VALID', log)
            self.assertIn('creation not committed', log)
            client.sendall(self.wire)
            self.closed(client)

    def test_fragmented_header_and_checksum(self):
        with self.candidate_server() as (client, root):
            self.select(client)
            for chunk in (self.wire[:1], self.wire[1:2], self.wire[2:47]):
                client.sendall(chunk)
                self.assert_silent(client)
                self.assertNotIn('CHARACTER_CREATE_FRAME_VALID', (root / 'stdout.log').read_text())
            client.sendall(self.wire[47:])
            self.assert_silent(client)
            self.assertIn('CHARACTER_CREATE_FRAME_VALID', (root / 'stdout.log').read_text())

    def test_bad_checksum_opcode_and_constant_rejected(self):
        changed = bytearray(self.payload); changed[40] = 3
        cases = (self.wire[:-1] + bytes([self.wire[-1] ^ 1]),
                 request_wire(self.payload, 0x1a), request_wire(changed))
        for wire in cases:
            with self.subTest(kind=cases.index(wire)), self.candidate_server() as (client, root):
                self.select(client)
                client.sendall(wire)
                self.closed(client)
                self.assertNotIn('CHARACTER_CREATE_FRAME_VALID', (root / 'stdout.log').read_text())

    def test_create_before_selection_rejected(self):
        with self.candidate_server() as (client, root):
            self.prefix(client)
            client.sendall(self.wire)
            self.closed(client)
            self.assertNotIn('CHARACTER_CREATE_FRAME_VALID', (root / 'stdout.log').read_text())

    def test_empty_and_unterminated_name_rejected(self):
        for field in (bytes(15), b'A'*15):
            with self.subTest(empty=field[0]==0), self.candidate_server() as (client, root):
                self.select(client)
                invalid=bytearray(self.payload)
                invalid[:15]=field
                client.sendall(request_wire(invalid))
                self.closed(client)
                log=(root/'stdout.log').read_text()
                self.assertIn('Character-create name rejected',log)
                self.assertNotIn('CHARACTER_CREATE_FRAME_VALID',log)

    def test_existing_post_select_mode_unchanged(self):
        with self.server() as (client, root):
            self.prefix(client)
            client.sendall(prefix.REQUEST.read_bytes())
            self.assert_silent(client)
            client.sendall(self.wire)
            self.closed(client)
            self.assertNotIn('CHARACTER_CREATE_FRAME_VALID', (root / 'stdout.log').read_text())


if __name__ == '__main__':
    unittest.main()
