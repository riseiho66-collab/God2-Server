"""Current S2C41 occupancy and C2S25 structure; no client, sockets or shared build.

Runs original decrypt/checksum, receive parser, world dispatch and full consumer.
No instructions or callees are stubbed. Synthetic inactive UI state is explicit;
this proves occupancy writes, not resource-loaded/live UI or character birth.
"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile
import unittest

import test_current_route_advertisement as routes
from unicorn import UC_HOOK_CODE, UC_HOOK_MEM_WRITE, UC_PROT_READ, UC_PROT_WRITE
from unicorn.x86_const import (UC_X86_REG_EAX, UC_X86_REG_EBP,
                               UC_X86_REG_EBX, UC_X86_REG_ECX, UC_X86_REG_EIP, UC_X86_REG_ESP)

ROOT = Path(__file__).resolve().parents[2]
WORLD = 0x4000000
UI = WORLD + 0xa7f2f6c
SLOTS = UI + 0x8560c
COMPANION_UI, MANAGER, PACKET_PAGE = 0x3700000, 0x3730000, 0x3740000


def build_fixture(directory):
    source = ROOT / 'tests/test_recovered_inventory.cpp'
    executable = directory / ('inventory.exe' if os.name == 'nt' else 'inventory')
    compiler = next((shutil.which(n) for n in ('cl', 'clang++', 'g++', 'c++')
                     if shutil.which(n)), None)
    environment = None
    if not compiler and os.name == 'nt':
        vswhere = Path(os.environ.get('ProgramFiles(x86)', 'C:/Program Files (x86)')) / (
            'Microsoft Visual Studio/Installer/vswhere.exe')
        installation = subprocess.check_output([str(vswhere), '-latest', '-products', '*',
            '-requires', 'Microsoft.VisualStudio.Component.VC.Tools.x86.x64',
            '-property', 'installationPath'], text=True, timeout=30).strip()
        if not installation:
            raise RuntimeError('Standalone inventory test requires C++20')
        vcvars = Path(installation) / 'VC/Auxiliary/Build/vcvars64.bat'
        settings = subprocess.check_output(f'cmd.exe /d /s /c ""{vcvars}" >nul && set"',
                                           text=True, timeout=30)
        environment = dict(line.split('=', 1) for line in settings.splitlines()
                           if '=' in line and not line.startswith('='))
        path = next(v for k, v in environment.items() if k.lower() == 'path')
        compiler = shutil.which('cl.exe', path=path)
    if not compiler:
        raise RuntimeError('Standalone inventory test requires C++20')
    if Path(compiler).name.lower() in ('cl', 'cl.exe'):
        command = [compiler, '/nologo', '/std:c++20', '/EHsc', '/W4', '/WX',
                   '/I' + str(ROOT / 'src'), str(source), '/Fe:' + str(executable),
                   '/Fo:' + str(directory / 'inventory.obj')]
    else:
        command = [compiler, '-std=c++20', '-Wall', '-Wextra', '-Werror',
                   '-I', str(ROOT / 'src'), str(source), '-o', str(executable)]
    result = subprocess.run(command, cwd=directory, env=environment,
                            text=True, capture_output=True, timeout=60)
    if result.returncode:
        raise AssertionError(result.stdout + result.stderr)
    return executable


class CurrentInventoryTests(unittest.TestCase):
    vm = routes.CurrentRouteAdvertisementTests.vm
    call = routes.CurrentRouteAdvertisementTests.call
    decode = routes.CurrentRouteAdvertisementTests.decode

    def run_to(self, vm, entry, stop):
        # An instruction cap bounds every slice without creating a timer thread
        # for each of the exhaustive composition oracle's small native calls.
        vm.emu_start(routes.BASE + entry, routes.BASE + stop, count=100000)
        self.assertEqual(vm.reg_read(UC_X86_REG_EIP), routes.BASE + stop,
                         'Original slice did not reach its bounded stop')

    @classmethod
    def setUpClass(cls):
        cls.image = (ROOT / 'artifacts/capture_work/host-20260918-1430/output/'
                     'native-master-01-stable.bin').read_bytes()
        if hashlib.sha256(cls.image).hexdigest() != routes.IMAGE_SHA:
            raise AssertionError('Pinned current image changed')
        cls.temp = tempfile.TemporaryDirectory(prefix='god2-inventory-test-')
        cls.addClassCleanup(cls.temp.cleanup)
        cls.executable = build_fixture(Path(cls.temp.name))

    def candidate(self, *arguments):
        return bytes.fromhex(subprocess.check_output([str(self.executable), *arguments],
                                                     text=True, timeout=5).strip())

    def parser_vm(self, logical):
        vm = self.vm()
        codec = routes.NET + 0x758
        vm.mem_write(routes.NET + 0x2cb8, b'\x01')
        vm.mem_write(codec + 0xc10, logical)
        vm.mem_write(codec + 0x1810, struct.pack('<II', len(logical), 0))
        vm.mem_write(0x5b4da8, bytes(4))
        return vm

    def parser_call(self, vm, entry):
        stop = routes.STACK + 0x3ff0
        vm.mem_write(routes.SP, struct.pack('<II', stop, 1))
        vm.reg_write(UC_X86_REG_ESP, routes.SP)
        vm.reg_write(UC_X86_REG_ECX, routes.NET)
        self.run_to(vm, entry, stop - routes.BASE)
        return vm.reg_read(UC_X86_REG_EAX)

    def consumer_vm(self):
        vm = self.vm()
        vm.mem_map(UI & ~4095, 0x234000)
        vm.mem_map(COMPANION_UI, 0x22000)
        vm.mem_map(MANAGER, 4096)
        vm.mem_map(PACKET_PAGE, 4096)
        # Inactive UI controls and selected slots. Companion UI pointer is real
        # mapped memory, manager mode != 1, item-category bits retain 0xa5a5.
        vm.mem_write(UI + 0x232dc8, b'\xff\xff')
        vm.mem_write(UI + 0x232dd6, b'\xff\xff')
        vm.mem_write(UI + 0x232ebc, struct.pack('<I', COMPANION_UI))
        vm.mem_write(COMPANION_UI + 0x21236, b'\xff')
        vm.mem_write(UI + 0x574c0, struct.pack('<I', MANAGER))
        vm.mem_write(UI + 0x71, b'\x01')  # Original D71F0 early-out predicate.
        vm.mem_write(SLOTS - 16, b'\xa5' * (50 * 24 + 32))
        # The upper canary includes selected-slot byte UI+85ABD = A5 (>49).
        return vm

    def consume(self, vm, record, scalar_only=False):
        self.assertEqual(len(record), 5)
        packet = PACKET_PAGE + 4096 - len(record)
        vm.mem_protect(PACKET_PAGE, 4096, UC_PROT_READ | UC_PROT_WRITE)
        vm.mem_write(packet, record)
        vm.mem_protect(PACKET_PAGE, 4096, UC_PROT_READ)
        vm.reg_write(UC_X86_REG_ESP, routes.SP)
        vm.reg_write(UC_X86_REG_EBP, WORLD)
        vm.reg_write(UC_X86_REG_EBX, packet)
        vm.reg_write(UC_X86_REG_EAX, record[0])
        stop = (0x992a9 if 0 < record[4] < 128 else 0x99268) if scalar_only else 0x6b517
        # A precise hook keeps the stop effective when a prior full-consumer
        # execution cached a translated block spanning a later scalar stop.
        hook = vm.hook_add(UC_HOOK_CODE, lambda uc, address, size, context: uc.emu_stop(),
                           begin=routes.BASE + stop, end=routes.BASE + stop)
        try:
            self.run_to(vm, 0x68b61, stop)
        finally:
            vm.hook_del(hook)
        if not scalar_only:
            self.assertEqual(vm.reg_read(UC_X86_REG_ESP), routes.SP)

    def encode_updates(self, updates):
        return self.candidate('--updates', *(str(field) for update in updates for field in update))

    def assert_update_composition(self, consumer, updates):
        wire = self.encode_updates(updates)
        logical = self.decode(self.vm(), wire)[2:-1]
        self.assertEqual(logical, b''.join(struct.pack('<BHBB', 0x41, *update)
                                          for update in updates))
        self.assertEqual(self.candidate('--decode-wire', wire.hex()), logical)
        parser = self.parser_vm(logical)
        expected = bytearray(consumer.mem_read(SLOTS - 16, 50 * 24 + 32))
        writes = []
        hook = consumer.hook_add(UC_HOOK_MEM_WRITE,
            lambda uc, access, address, size, value, context: writes.append((address, size)))
        try:
            for index, (item, slot, count) in enumerate(updates):
                self.assertEqual(self.parser_call(parser, 0x13420), 0)
                self.assertEqual(struct.unpack('<I', parser.mem_read(routes.NET + 0x2cc0, 4))[0], 5)
                pointer = self.parser_call(parser, 0x13650)
                record = bytes(parser.mem_read(pointer, 5))
                self.assertEqual(record, logical[5 * index:5 * index + 5])
                writes.clear()
                # Positive counts stop before resource-dependent refresh; clear
                # values execute the complete original dispatcher and consumer.
                occupied = 0 < count < 128
                try:
                    self.consume(consumer, record, scalar_only=occupied)
                except Exception as error:
                    error.add_note(f'Record {record.hex()} at RVA '
                                   f'{consumer.reg_read(UC_X86_REG_EIP) - routes.BASE:#x}')
                    raise
                expected[16 + slot * 24] = count if occupied else 0
                expected[20 + slot * 24:22 + slot * 24] = struct.pack('<H', item if occupied else 0)
                self.assertEqual(bytes(consumer.mem_read(SLOTS - 16, len(expected))), expected,
                                 (index, item, slot, count))
                for address, size in writes:
                    allowed = routes.STACK <= address and address + size <= routes.STACK + 0x4000
                    allowed |= address == SLOTS + 24 * slot and size == 1
                    allowed |= address == SLOTS + 24 * slot + 4 and size == 4
                    self.assertTrue(allowed, f'Unexpected update write {address:#x}/{size}')
                self.parser_call(parser, 0x13670)
            self.assertEqual(struct.unpack('<I', parser.mem_read(
                routes.NET + 0x758 + 0x1814, 4))[0], len(logical))
        finally:
            consumer.hook_del(hook)

    def test_encoder_native_all_slots_and_raw_counts_in_composed_frames(self):
        consumer = self.consumer_vm()
        # Ten complete 50-slot scalar snapshots per frame, below the existing
        # 0xa00 envelope cap. The same native state survives all 26 frames.
        counts = list(range(1, 128)) + [0] + list(range(128, 256))
        for start in range(0, len(counts), 10):
            updates = [(((count * 257) ^ (slot * 197 + 0x1234)) & 0xffff, slot, count)
                       for count in counts[start:start + 10] for slot in range(50)]
            with self.subTest(counts=counts[start:start + 10]):
                self.assert_update_composition(consumer, updates)

    def test_encoder_snapshot_replacement_duplicate_order_and_residual_bytes(self):
        consumer = self.consumer_vm()
        # Deliberately varied residual bytes ensure stores retain each slot's
        # own upper ID word and metadata, not just a repeated A5 sentinel.
        initial = bytearray(b'\xa5' * (50 * 24 + 32))
        for slot in range(50):
            initial[16 + 24 * slot:16 + 24 * (slot + 1)] = bytes(
                (slot * 17 + offset * 29) & 255 for offset in range(24))
        consumer.mem_write(SLOTS - 16, bytes(initial))
        # Scalar-only checks avoid activating metadata-dependent clear effects
        # while verifying all 21 retained bytes under distinct initial values.
        for slot in range(50):
            records = self.decode(self.vm(), self.encode_updates(
                [(0x9234, slot, 127), (0xffff, slot, 128)]))[2:-1]
            self.consume(consumer, records[:5], scalar_only=True)
            self.consume(consumer, records[5:], scalar_only=True)
            initial[16 + 24 * slot] = 0
            initial[20 + 24 * slot:22 + 24 * slot] = bytes(2)
            self.assertEqual(bytes(consumer.mem_read(SLOTS - 16, len(initial))), initial)

        consumer = self.consumer_vm()
        boundary_ids = (0, 1, 255, 256, 0x7fff, 0x8000, 0xffff, 0x9234)
        snapshot = [(boundary_ids[slot % len(boundary_ids)], slot, 127) for slot in range(50)]
        self.assert_update_composition(consumer, snapshot)
        updates = []
        for slot in reversed(range(50)):
            updates += [(0xffff, slot, 1), (0xffff, slot, 1), (0x9234, slot, 0),
                        (0x8000, slot, 7), (0, slot, 1), (0x1234, slot, 255),
                        (0x4321, slot, 127)]
        self.assert_update_composition(consumer, updates)
        self.assert_update_composition(consumer, [(0, slot, 0) for slot in range(50)])

    def test_composed_response_truncation_integrity_and_invalid_late_record(self):
        updates = [(0x9234, slot, 127) for slot in range(50)]
        wire = self.encode_updates(updates)
        logical = self.decode(self.vm(), wire)[2:-1]

        def rejected(frame):
            result = subprocess.run([str(self.executable), '--decode-wire', frame.hex()],
                                    text=True, capture_output=True, timeout=5)
            self.assertEqual(result.returncode, 2, frame.hex())
            self.assertEqual(result.stdout, '')

        for length in range(len(wire)):
            rejected(wire[:length])
        rejected(wire + b'\0')
        rejected(wire + wire)
        for offset in (0, 1):
            corrupt = bytearray(wire)
            corrupt[offset] ^= 1
            rejected(bytes(corrupt))
        for checksum_byte in range(256):
            if checksum_byte != wire[-1]:
                rejected(wire[:-1] + bytes((checksum_byte,)))

        # Correct transport checksums cannot legitimize partial S2C41 records.
        # Every shorter complete-record prefix remains a valid update batch;
        # there is no evidence of a required 50-record transaction on the wire.
        for length in range(1, len(logical)):
            framed = self.candidate('--frame-logical', logical[:length].hex())
            self.assertEqual(self.decode(self.vm(), framed)[2:-1], logical[:length])
            if length % 5:
                rejected(framed)
            else:
                self.assertEqual(self.candidate('--decode-wire', framed.hex()), logical[:length])
        for invalid in (bytes((0x25, 0, 0, 49, 1)), bytes((0x41, 0, 0, 50, 1)),
                        bytes((0x41, 0, 0, 255, 1))):
            for index in (0, 25, 49):
                changed = logical[:index * 5] + invalid + logical[index * 5 + 5:]
                framed = self.candidate('--frame-logical', changed.hex())
                self.assertEqual(self.decode(self.vm(), framed)[2:-1], changed)
                rejected(framed)

    def test_original_parser_partial_tail_after_each_snapshot_slot(self):
        logical = self.decode(self.vm(), self.encode_updates(
            [(0x9234, slot, 127) for slot in range(50)]))[2:-1]
        # Exact exhaustion starts the socket-read path in the original parser;
        # this offline fixture only exercises already-buffered partial records.
        for length in (n for n in range(1, len(logical)) if n % 5):
            with self.subTest(length=length):
                parser = self.parser_vm(logical[:length])
                for index in range(length // 5):
                    self.assertEqual(self.parser_call(parser, 0x13420), 0)
                    pointer = self.parser_call(parser, 0x13650)
                    self.assertEqual(bytes(parser.mem_read(pointer, 5)), logical[index * 5:index * 5 + 5])
                    self.parser_call(parser, 0x13670)
                self.assertEqual(self.parser_call(parser, 0x13420), 1)
                self.assertEqual(struct.unpack('<I', parser.mem_read(routes.NET + 0x2cc0, 4))[0], length % 5)

    def test_encoder_rejects_invalid_fields_without_partial_output(self):
        bad_updates = [(), ('1',), ('1', '49'), ('1', '49', '1', '2')]
        for fields in (('65536', '0', '1'), ('-1', '0', '1'), ('1', '50', '1'),
                       ('1', '255', '1'), ('1', '256', '1'), ('1', '-1', '1'),
                       ('1', '0', '256'), ('1', '0', '-1'), ('1', '0', 'bad')):
            bad_updates += [fields, ('37428', '49', '127', *fields)]
        bad_updates.append(tuple(['1', '49', '1'] * 513))
        for fields in bad_updates:
            result = subprocess.run([str(self.executable), '--updates', *fields],
                                    text=True, capture_output=True, timeout=5)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(result.stdout, '')
        maximum = [(0x9234, 49, 1)] * 512
        wire = self.encode_updates(maximum)
        self.assertEqual(len(wire), 2563)
        logical = struct.pack('<BHBB', 0x41, 0x9234, 49, 1) * 512
        self.assertEqual(self.decode(self.vm(), wire)[2:-1], logical)
        self.assertEqual(self.candidate('--decode-wire', wire.hex()), logical)

    def test_standalone_cpp_and_current_dispatch(self):
        subprocess.run([str(self.executable)], check=True, timeout=5)
        self.assertEqual(struct.unpack_from('<I', self.image, 0x1324 + 4*0x41)[0],
                         routes.BASE + 0x12ac)
        self.assertEqual(self.image[0x12ac:0x12b2], b'\xb8\x05\0\0\0\xc3')
        self.assertEqual(struct.unpack_from('<I', self.image, 0x6b5d4 + 4*0x41)[0],
                         routes.BASE + 0x6a04d)

    def test_cpp_empty_batch_original_crypto_parser_and_all_fifty_consumers(self):
        wire = self.candidate('--dump')
        self.assertEqual(len(wire), 253)
        plain = self.decode(self.vm(), wire)
        logical = plain[2:-1]
        self.assertEqual(logical, b''.join(bytes((0x41, 0, 0, slot, 0))
                                           for slot in range(50)))
        parser = self.parser_vm(logical)
        consumer = self.consumer_vm()
        writes = []
        consumer.hook_add(UC_HOOK_MEM_WRITE,
            lambda uc, access, address, size, value, context: writes.append((address, size)))
        expected = bytearray(b'\xa5' * (50 * 24 + 32))
        for slot in range(50):
            self.assertEqual(self.parser_call(parser, 0x13420), 0)
            self.assertEqual(struct.unpack('<I', parser.mem_read(routes.NET+0x2cc0, 4))[0], 5)
            pointer = self.parser_call(parser, 0x13650)
            record = bytes(parser.mem_read(pointer, 5))
            self.assertEqual(record, logical[5*slot:5*slot+5])
            self.consume(consumer, record)
            expected[16 + 24*slot] = 0
            expected[20 + 24*slot:22 + 24*slot] = bytes(2)
            self.assertEqual(bytes(consumer.mem_read(SLOTS-16, len(expected))), expected)
            self.parser_call(parser, 0x13670)
        self.assertEqual(struct.unpack('<I', parser.mem_read(routes.NET+0x758+0x1814, 4))[0], 250)
        for address, size in writes:
            allowed = routes.STACK <= address and address+size <= routes.STACK+0x4000
            allowed |= any(address == SLOTS+24*s and size == 1 or
                           address == SLOTS+24*s+4 and size == 4 for s in range(50))
            self.assertTrue(allowed, f'Unexpected consumer write {address:#x}/{size}')

    def test_native_slot_bounds_and_signed_count_field_oracle(self):
        for slot in (0, 29, 30, 37, 38, 41, 42, 44, 45, 46, 49, 50, 127, 128, 255):
            for count in (0, 1, 30, 127, 128, 255):
                with self.subTest(slot=slot, count=count):
                    vm = self.consumer_vm()
                    record = bytes((0x41, 0x34, 0x92, slot, count))
                    # For positive counts, the full renderer needs a real item
                    # catalog. Stop before all secondary effects for field proof.
                    vm.mem_write(routes.BODY, record[1:])
                    vm.mem_write(routes.SP, struct.pack('<II', routes.RETURN, routes.BODY))
                    vm.reg_write(UC_X86_REG_ESP, routes.SP)
                    vm.reg_write(UC_X86_REG_ECX, UI)
                    stop = 0x99268 if count == 0 or count >= 128 else 0x992a9
                    if slot >= 50:
                        stop = 0x992f5
                    self.run_to(vm, 0x991e0, stop)
                    expected = bytearray(b'\xa5' * (50 * 24 + 32))
                    if slot < 50:
                        expected[16 + 24*slot] = count if 0 < count < 128 else 0
                        expected[20 + 24*slot:22 + 24*slot] = (b'\x34\x92'
                            if 0 < count < 128 else bytes(2))
                    self.assertEqual(bytes(vm.mem_read(SLOTS-16, len(expected))), expected)
                    result = subprocess.run([str(self.executable), '--decode', record.hex()],
                                            text=True, capture_output=True, timeout=5)
                    self.assertEqual(result.returncode, 0 if slot < 50 else 2)
                    if slot < 50:
                        self.assertEqual(tuple(map(int, result.stdout.split())), (0x9234, slot, count))

    def test_original_populate_then_cpp_clear_preserves_residual_metadata(self):
        clear = self.decode(self.vm(), self.candidate('--dump'))[2:-1]
        for slot in range(50):
            vm = self.consumer_vm()
            # Native positive-count scalar path, bounded before UI refresh and
            # without pretending that the synthetic item has loaded resources.
            vm.mem_write(routes.BODY, struct.pack('<HBB', 0x9234, slot, 7))
            vm.mem_write(routes.SP, struct.pack('<II', routes.RETURN, routes.BODY))
            vm.reg_write(UC_X86_REG_ESP, routes.SP)
            vm.reg_write(UC_X86_REG_ECX, UI)
            self.run_to(vm, 0x991e0, 0x992a9)
            populated = bytes(vm.mem_read(SLOTS + 24*slot, 24))
            self.assertEqual(populated[0], 7)
            self.assertEqual(populated[4:6], b'\x34\x92')
            if slot <= 37:
                self.call(vm, 0x98d30, slot, this=UI)
                self.assertEqual(vm.reg_read(UC_X86_REG_EAX), SLOTS + 24*slot)
            self.consume(vm, clear[5*slot:5*slot+5])
            expected = bytearray(populated)
            expected[0] = 0
            expected[4:6] = bytes(2)
            self.assertEqual(bytes(vm.mem_read(SLOTS + 24*slot, 24)), expected)
            if slot <= 37:
                self.call(vm, 0x98d30, slot, this=UI)
                self.assertEqual(vm.reg_read(UC_X86_REG_EAX), 0)
            self.consume(vm, clear[5*slot:5*slot+5])
            self.assertEqual(bytes(vm.mem_read(SLOTS + 24*slot, 24)), expected)

    def test_black_box_truncated_extended_wrong_opcode_and_slot(self):
        record = bytes((0x41, 0, 0, 49, 0))
        malformed = [record[:n] for n in range(5)] + [record+b'\0', b'\x40'+record[1:],
                    bytes((0x41, 0, 0, 50, 0)), bytes((0x41, 0, 0, 255, 0))]
        for logical in malformed:
            result = subprocess.run([str(self.executable), '--decode', logical.hex()],
                                    capture_output=True, timeout=5)
            self.assertEqual(result.returncode, 2)
        for slot in ('50', '255', '-1', 'garbage'):
            self.assertEqual(subprocess.run([str(self.executable), '--clear', slot],
                             capture_output=True, timeout=5).returncode, 2)
        for slot in (0, 49):
            plain = self.decode(self.vm(), self.candidate('--clear', str(slot)))
            self.assertEqual(plain[2:-1], bytes((0x41, 0, 0, slot, 0)))

    def test_original_parser_truncation_and_native_checksum_rejection(self):
        # Exhaustion returns incomplete through the original 12520 read path.
        # The VM has no socket service or patched parser result.
        for length in range(1, 5):
            vm = self.parser_vm(bytes((0x41, 0, 0, 49, 0))[:length])
            self.assertEqual(self.parser_call(vm, 0x13420), 1)
            self.assertEqual(struct.unpack('<I', vm.mem_read(routes.NET+0x2cc0, 4))[0], length)
        wire = self.candidate('--dump')
        plain = bytearray(self.decode(self.vm(), wire))
        plain[-1] ^= 1
        vm = self.vm()
        vm.mem_write(routes.BODY, bytes(plain))
        self.call(vm, 0x10750, routes.BODY, len(plain))
        self.assertEqual(vm.reg_read(UC_X86_REG_EAX), 0)

    def test_native_map_control_candidate_record_length(self):
        for value in range(256):
            logical=bytes((0x3f,value,255-value))
            parser=self.parser_vm(logical+b'\x3f\x01')
            self.assertEqual(self.parser_call(parser,0x13420),0)
            pointer=self.parser_call(parser,0x13650)
            self.assertEqual(bytes(parser.mem_read(pointer,3)),logical)
            self.parser_call(parser,0x13670)
            self.assertEqual(self.parser_call(parser,0x13420),1)
            self.assertEqual(struct.unpack('<I',parser.mem_read(routes.NET+0x2cc0,4))[0],2)

    def test_native_map_control_candidate_dispatch(self):
        # Native3F -> C3890 -> C3840 ->1052E0. Synthetic valid scene and
        # inactive resource handles avoid external renderer calls, not stubs.
        self.assertEqual(struct.unpack_from('<I',self.image,0x6b5d4+4*0x3f)[0],0x46b034)
        for value in (1,2,127,128,255):
            with self.subTest(value=value):
                vm=self.consumer_vm()
                scene=PACKET_PAGE+0x100
                vm.mem_write(UI+0x8aa4c,struct.pack('<I',scene))
                vm.mem_write(scene,bytes(0x200))
                vm.mem_write(UI+0x232f58,bytes(4))
                vm.mem_write(UI+0x232da8,struct.pack('<h',0))
                vm.mem_write(UI+0x232e56,struct.pack('<h',-1))
                node=UI+0xe2988
                vm.mem_write(node,bytes(10760))
                vm.mem_write(node,struct.pack('<H',0x10))
                vm.mem_write(node+4,struct.pack('<H',0xffff))
                vm.mem_write(node+0x28,struct.pack('<i',-1))
                vm.mem_write(PACKET_PAGE,bytes((0x3f,value,0xa5)))
                before_inventory=bytes(vm.mem_read(SLOTS,50*24))
                seen=[]
                vm.hook_add(UC_HOOK_CODE,lambda uc,address,size,data:seen.append(address))
                vm.reg_write(UC_X86_REG_EBP,WORLD)
                vm.reg_write(UC_X86_REG_EBX,PACKET_PAGE)
                vm.reg_write(UC_X86_REG_EAX,0x3f)
                vm.reg_write(UC_X86_REG_ESP,routes.SP)
                self.run_to(vm,0x68b61,0x6b517)
                self.assertEqual(vm.reg_read(UC_X86_REG_ESP),routes.SP)
                for address in (0x4c3890,0x4c3840,0x5052e0):self.assertIn(address,seen)
                self.assertEqual(bytes(vm.mem_read(node,2)),b'\x20\x00')
                self.assertEqual(bytes(vm.mem_read(SLOTS,50*24)),before_inventory)

    def test_native_map_control_candidate_rejection_branches(self):
        for value,scene_flags,scene_id,blocked,message in (
                (0,0,0,0,0x330),(1,3,0,0,0x32f),
                (1,0,0x1741,0,0x369),(1,0,0,1,0x369)):
            with self.subTest(value=value,scene_flags=scene_flags,scene_id=scene_id,blocked=blocked):
                vm=self.consumer_vm()
                scene=PACKET_PAGE+0x100
                vm.mem_write(UI+0x8aa4c,struct.pack('<I',scene))
                vm.mem_write(scene,bytes(0x200))
                vm.mem_write(scene+0xf4,struct.pack('<I',scene_flags))
                vm.mem_write(scene+0xf0,struct.pack('<H',scene_id))
                vm.mem_write(UI+0x232f58,struct.pack('<I',blocked))
                vm.mem_write(PACKET_PAGE,bytes((0x3f,value,0xa5)))
                before=bytes(vm.mem_read(UI,0x233000))
                vm.reg_write(UC_X86_REG_EBP,WORLD)
                vm.reg_write(UC_X86_REG_EBX,PACKET_PAGE)
                vm.reg_write(UC_X86_REG_EAX,0x3f)
                vm.reg_write(UC_X86_REG_ESP,routes.SP)
                # Stop before the message renderer; do not fake its return.
                self.run_to(vm,0x68b61,0x75d60)
                sp=vm.reg_read(UC_X86_REG_ESP)
                self.assertEqual(struct.unpack('<I',vm.mem_read(sp+4,4))[0],message)
                self.assertEqual(bytes(vm.mem_read(UI,len(before))),before)

    def test_native_owned_map_item_selects_c2s25(self):
        path=ROOT/'artifacts/runs/native-town-map-item-catalog-20260921-01/native-town-map-item-catalog-20260921-01-result.json'
        record=bytes.fromhex(json.loads(path.read_text())['town_reward_item']['record_hex'])
        self.assertEqual((len(record),record[0x11a]),(396,0xf1))
        resource,item=0x3800000,0x38bf000
        for slot,gate in ((0,0),(29,0),(30,0),(49,0),(128,0),(255,0),(0,1)):
            with self.subTest(slot=slot,gate=gate):
                vm=self.consumer_vm()
                vm.mem_map(resource,0xc0000)
                vm.mem_write(resource+0xb2d40+4*5569,struct.pack('<I',item))
                vm.mem_write(item,record)
                vm.mem_write(UI+0xcff70,struct.pack('<I',resource))
                vm.mem_write(UI+0x866e4,struct.pack('<I',gate))
                vm.mem_write(UI+0x86874,struct.pack('<I',routes.NET))
                vm.mem_write(SLOTS,bytes(50*24))
                if slot<50:
                    vm.mem_write(SLOTS+24*slot,b'\x01')
                    vm.mem_write(SLOTS+24*slot+4,struct.pack('<H',5569))
                vm.mem_write(routes.NET+0x36c4,bytes(4))
                before=bytes(vm.mem_read(UI,0x233000))
                seen=[]
                vm.hook_add(UC_HOOK_CODE,lambda uc,address,size,data:seen.append(address))
                # Full original slot wrapper, reverse ownership search, metadata
                # lookup, category branch, producer and queue append. No stubs.
                self.call(vm,0x96390,slot,this=UI)
                self.assertEqual(vm.reg_read(UC_X86_REG_ESP),routes.SP+8)
                self.assertEqual(bytes(vm.mem_read(UI,len(before))),before)
                size=struct.unpack('<I',vm.mem_read(routes.NET+0x36c4,4))[0]
                accepted=slot<30 and not gate
                self.assertEqual(size,5 if accepted else 0)
                if accepted:
                    wire=bytes(vm.mem_read(routes.NET+0x36c8,5))
                    self.assertEqual(wire[:4],struct.pack('<BHB',0x25,5569,slot))
                    self.assertIn(0x459a60,seen)
                    self.assertIn(0x496350,seen)
                    self.assertIn(0x4132e0,seen)
                    self.assertNotIn(0x496550,seen)
                    self.assertEqual(bytes(vm.mem_read(item,396)),record)
                else:
                    self.assertNotIn(0x496350,seen)

    def produce_item_request(self, item_argument, slot_argument, third_argument, gate=0):
        vm = self.consumer_vm()
        vm.mem_write(UI + 0x866e4, struct.pack('<I', gate))
        vm.mem_write(UI + 0x86874, struct.pack('<I', routes.NET))
        queue = routes.NET + 0x36c8
        # Nonempty queue proves append behavior and provides both-side canaries.
        prefix = b'\x6a\x91\xe7'
        vm.mem_write(routes.NET + 0x36c4, struct.pack('<I', len(prefix)))
        vm.mem_write(queue, prefix + b'\xa5' * 21)
        before_ui = bytes(vm.mem_read(UI, 0x233000))
        writes = []
        vm.hook_add(UC_HOOK_MEM_WRITE,
            lambda uc, access, address, size, value, context: writes.append((address, size)))
        # Run the entire original producer AND queue append, including returns.
        # Queue is below flush threshold; optional lock pointer is zero.
        self.call(vm, 0x96350, item_argument, slot_argument, third_argument, this=UI)
        self.assertEqual(vm.reg_read(UC_X86_REG_ESP), routes.SP + 16)
        self.assertEqual(bytes(vm.mem_read(UI, len(before_ui))), before_ui)
        size = struct.unpack('<I', vm.mem_read(routes.NET + 0x36c4, 4))[0]
        self.assertEqual(size, len(prefix) + (0 if gate else 5))
        self.assertEqual(bytes(vm.mem_read(queue, len(prefix))), prefix)
        self.assertEqual(bytes(vm.mem_read(queue + size, 24 - size)), b'\xa5' * (24 - size))
        for address, length in writes:
            allowed = routes.STACK <= address and address + length <= routes.STACK + 0x4000
            if not gate:
                allowed |= address == routes.NET + 0x36c4 and length == 4
                allowed |= queue + len(prefix) <= address and address + length <= queue + size
            self.assertTrue(allowed, f'Unexpected item producer write {address:#x}/{length}')
        return bytes(vm.mem_read(queue + len(prefix), size - len(prefix)))

    def test_item_request_original_producer_cpp_fields_and_raw_bounds(self):
        # Exhaust each u8 independently of native caller assumptions. Zero and
        # out-of-owned-range slots are structurally preserved, NOT authorized.
        cases = [(value | ((255 - value) << 8), (197 * value + 17) & 255, value)
                 for value in range(256)]
        cases += [(item, slot, tail) for item, slot, tail in
                  ((0, 0, 255), (1, 49, 128), (255, 50, 127), (256, 127, 1),
                   (0x7fff, 128, 0), (0x8000, 255, 49), (0xffff, 49, 50))]
        for item, slot, tail in cases:
            with self.subTest(item=item, slot=slot, tail=tail):
                record = self.produce_item_request(
                    (tail << 24) | 0x00ee0000 | item, 0xabcdef00 | slot,
                    0x10203040 ^ tail)
                self.assertEqual(record, struct.pack('<BHBB', 0x25, item, slot, tail))
                result = subprocess.run([str(self.executable), '--decode-item-request',
                                         record.hex()], text=True, capture_output=True, timeout=5)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(tuple(map(int, result.stdout.split())), (item, slot, tail))

    def test_item_request_opaque_tail_unused_argument_and_original_gate(self):
        for tail in (0, 1, 127, 128, 255):
            for third in (0, 1, 0x12345678, 0xffffffff):
                for overwritten_byte in (0, 0xff):
                    record = self.produce_item_request(
                        (tail << 24) | (overwritten_byte << 16) | 0x9234, 49, third)
                    self.assertEqual(record, bytes((0x25, 0x34, 0x92, 49, tail)))
        for gate in (1, 0x80000000, 0xffffffff):
            self.assertEqual(self.produce_item_request(0xffee9234, 49, 1, gate), b'')

    def test_item_request_black_box_rejects_nonrecords(self):
        record = bytes((0x25, 0x34, 0x92, 49, 0xff))
        malformed = [record[:n] for n in range(5)]
        malformed += [record + b'\0', record * 2]
        malformed += [bytes((opcode,)) + record[1:] for opcode in range(256) if opcode != 0x25]
        for logical in malformed:
            result = subprocess.run([str(self.executable), '--decode-item-request', logical.hex()],
                                    capture_output=True, timeout=5)
            self.assertEqual(result.returncode, 2, logical.hex())
        for malformed_hex in ('2', 'zz', '25349231fg', '25 49231ff'):
            self.assertEqual(subprocess.run([str(self.executable), '--decode-item-request',
                                            malformed_hex], capture_output=True, timeout=5).returncode, 2)

    def test_black_box_guard_pages_exact_record_boundaries(self):
        for mode, opcode in (('--guarded-decode', 0x41),
                             ('--guarded-decode-item-request', 0x25)):
            record = bytes((opcode, 0x34, 0x92, 49, 0xff))
            cases = [(record[:n], False) for n in range(5)]
            cases += [(record, True)]
            cases += [(record + bytes(n), False) for n in range(1, 6)]
            cases += [(record * 2, False), (bytes((opcode ^ 1,)) + record[1:], False)]
            for logical, accepted in cases:
                with self.subTest(mode=mode, logical=logical.hex()):
                    result = subprocess.run([str(self.executable), mode, logical.hex()],
                                            text=True, capture_output=True, timeout=5)
                    self.assertEqual(result.returncode, 0 if accepted else 2, result.stderr)
                    self.assertEqual(result.stdout, '37428 49 255\n' if accepted else '')

    def test_slot_update_black_box_all_wrong_opcodes_and_invalid_slots(self):
        cases = [bytes((opcode, 0x34, 0x92, 49, 0xff))
                 for opcode in range(256) if opcode != 0x41]
        cases += [bytes((0x41, 0x34, 0x92, slot, 0xff)) for slot in range(50, 256)]
        for logical in cases:
            with self.subTest(logical=logical.hex()):
                result = subprocess.run([str(self.executable), '--guarded-decode', logical.hex()],
                                        text=True, capture_output=True, timeout=5)
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertEqual(result.stdout, '')

    def test_item_request_guarded_raw_fields_are_not_slot_update_rules(self):
        # Producer evidence preserves all u8 slot/tail values; S2C bounds and
        # signed-count clearing cannot be imported into C2S structural decoding.
        for value in range(256):
            item = value | ((255 - value) << 8)
            record = struct.pack('<BHBB', 0x25, item, value, 255 - value)
            with self.subTest(value=value):
                result = subprocess.run([str(self.executable), '--guarded-decode-item-request',
                                         record.hex()], text=True, capture_output=True, timeout=5)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(tuple(map(int, result.stdout.split())), (item, value, 255 - value))


if __name__ == '__main__':
    unittest.main()
