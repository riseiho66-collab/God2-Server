"""Lightweight pinned-original clock execution; no resource preload."""
from pathlib import Path
import hashlib
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'artifacts/tooling/crypto-oracle-python'))
from unicorn import (Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE,
                     UC_PROT_READ, UC_PROT_WRITE, UC_PROT_EXEC)
from unicorn import x86_const as x86
from tools.strike_lab import current_world_clock as clock

OWNER, CHARACTER, STACK, PACKET = 0x30000000, 0x2800000, 0x2100000, 0x2200000
SP = STACK + 0x800
SOURCE = CHARACTER + clock.SOURCE_OFFSET
REGISTERS = ('EAX', 'EBX', 'ECX', 'EDX', 'ESI', 'EDI', 'EBP', 'ESP', 'EIP',
             'EFLAGS', 'FPCW', 'FPSW', 'FPTAG', 'FP0', 'FP7', 'XMM0', 'MXCSR')


class CurrentWorldClockTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image = clock.IMAGE.read_bytes()

    def setUp(self):
        self.vm = vm = Uc(UC_ARCH_X86, UC_MODE_32)
        vm.mem_map(clock.BASE, (len(self.image) + 4095) & ~4095,
                   UC_PROT_READ | UC_PROT_EXEC)
        vm.mem_write(clock.BASE, self.image)
        for pointer in (OWNER + clock.SOURCE_POINTER, SOURCE + clock.TIMESTAMP, STACK, PACKET):
            vm.mem_map(pointer & ~4095, 4096, UC_PROT_READ | UC_PROT_WRITE)
            vm.mem_write(pointer & ~4095, b'\xa5' * 4096)
        vm.mem_write(OWNER + clock.SOURCE_POINTER, struct.pack('<I', SOURCE))
        for i, name in enumerate(REGISTERS[:9]):
            vm.reg_write(getattr(x86, 'UC_X86_REG_' + name), 0x12340000 + i * 0x123)
        vm.reg_write(x86.UC_X86_REG_ESP, STACK + 0xe00)
        vm.reg_write(x86.UC_X86_REG_EFLAGS, 0x602)
        vm.reg_write(x86.UC_X86_REG_FPCW, 0xb7f)
        vm.reg_write(x86.UC_X86_REG_FP0, (0x923456789abcdef0, 0x3fff))
        vm.reg_write(x86.UC_X86_REG_FPTAG, 0xfffc)
        vm.reg_write(x86.UC_X86_REG_XMM0, 0x123456789abcdef0123456789abcdef0)
        self.n = clock.NativeWorldClock(vm, owner=OWNER, character=CHARACTER, sp=SP, packet=PACKET)

    def caller(self):
        return (tuple(self.vm.reg_read(getattr(x86, 'UC_X86_REG_' + name)) for name in REGISTERS),
                bytes(self.vm.mem_read(STACK, 4096)), bytes(self.vm.mem_read(PACKET, 4096)),
                tuple(self.vm.mem_regions()))

    def source_page(self):
        return bytes(self.vm.mem_read((SOURCE + clock.TIMESTAMP) & ~4095, 4096))

    def test_pinned_image_dispatch_length_and_import_name_evidence(self):
        b = self.image
        self.assertEqual(hashlib.sha256(b).hexdigest(), clock.IMAGE_SHA)
        self.assertEqual(struct.unpack_from('<I', b, 0x6b5d4 + 0x1a * 4)[0], 0x46b022)
        self.assertEqual(struct.unpack_from('<I', b, 0x1324 + 0x1a * 4)[0], 0x401264)
        self.assertEqual(b[0x1264:0x126a], bytes.fromhex('b804000000c3'))
        self.assertEqual(b[0x6b022:0x6b02f], bytes.fromhex('438d8d6c2f7f0a53e8c1850500'))
        self.assertEqual(struct.unpack_from('<I', b, 0x1707bc)[0], clock.CLOCK_TARGET)
        self.assertEqual(struct.unpack_from('<I', b, 0x17f7bc)[0], 0x17f8d6)
        self.assertEqual(b[0x17f8d8:0x17f8e4], b'timeGetTime\0')
        self.assertEqual(b[0x17fa48:0x17fa52], b'WINMM.dll\0')
        self.assertEqual(struct.unpack_from('<I', b, 0x17f400)[0], 0x17fc8c)
        self.assertEqual(b[0x17fc8e:0x17fc9b], b'GetTickCount\0')
        self.assertNotEqual(struct.unpack_from('<I', b, 0x170400)[0], clock.CLOCK_TARGET)
        self.assertEqual(b[0x171240:0x171244], bytes.fromhex('6f12833a'))

    def test_writer_exact_native_reads_writes_and_caller_preservation(self):
        before, original = self.caller(), self.source_page()
        result = self.n.write_clock(bytes((0x1a, 23, 59, 58)), clock_ms=0xfffffffe)
        value = 6 * (23 * 3600 + 59 * 60 + 58)
        self.assertEqual((result['timestamp'], result['value']), (0xfffffffe, value))
        self.assertEqual(result['outcome'], 'writer_returned')
        self.assertIn(0xc363b, result['pcs'])
        self.assertEqual(result['registers']['ESP'], SP)
        stores = [v for v in result['writes'] if not SP - 0x100 <= v[1] < SP + 0x100]
        self.assertEqual(stores, [(0xc35ff, SOURCE + 0x44ac, 4, 0xfffffffe),
                                  (0xc3634, SOURCE + 0x44b0, 4, value)])
        packet_reads = [v for v in result['reads'] if PACKET <= v[1] < PACKET + 4]
        self.assertEqual(packet_reads, [(0xc360b, PACKET + 1, 1, 23),
                                        (0xc3615, PACKET + 2, 1, 59),
                                        (0xc3623, PACKET + 3, 1, 58)])
        self.assertEqual([v[:3] for v in result['reads'] if v[1] == OWNER + 0x86888],
                         [(0xc35f9, OWNER + 0x86888, 4), (0xc362c, OWNER + 0x86888, 4)])
        self.assertEqual([v[:3] for v in result['reads'] if v[1] == clock.CLOCK_IAT],
                         [(0xc35f3, clock.CLOCK_IAT, 4)])
        self.assertEqual(result['clock_calls'][0]['name'], 'WINMM!timeGetTime')
        self.assertEqual(result['clock_calls'][0]['return'], 0x4c35f9)
        expected = bytearray(original)
        offset = (SOURCE + 0x44ac) & 4095
        expected[offset:offset + 8] = struct.pack('<II', 0xfffffffe, value)
        self.assertEqual(self.source_page(), bytes(expected))
        self.assertEqual(self.caller(), before)

    def test_writer_full_unsigned_byte_domain(self):
        for fields in ((0, 0, 0), (255, 255, 255), (128, 60, 60), (0, 0, 1)):
            with self.subTest(fields=fields):
                result = self.n.write_clock(bytes((0x1a, *fields)), clock_ms=0)
                self.assertEqual(result['value'], 6 * (fields[0]*3600 + fields[1]*60 + fields[2]))
                self.assertEqual(result['timestamp'], 0)

    def test_actual_ui_caller_arithmetic_boundaries_and_wrap(self):
        cases = ((1000, 1000, 0), (1000, 1166, 59), (1000, 1167, 59),
                 (0, 9999, 0), (0, 10000, 0), (0, 10001, 0),
                 (0xfffffff0, 0x20, 3599), (1, 0, 0),
                 (0, 715827882, 0), (0, 715827883, 0),
                 (0, 0xffffffff, 0xffffffff), (0, 1000, 0xfffffffe),
                 (0, 16667, 86399), (0, 10000333, 58))
        for timestamp, now, base_value in cases:
            with self.subTest(timestamp=timestamp, now=now, value=base_value):
                state = struct.pack('<II', timestamp, base_value)
                self.vm.mem_write(SOURCE + clock.TIMESTAMP, state)
                before, source = self.caller(), self.source_page()
                result = self.n.read_clock(clock_ms=now, state=state)
                # Exact rational of pinned float32 3A83126F. x87 computes it;
                # this independent integer expectation preserves pre-scale wrap.
                scaled_delta = (6 * (now - timestamp)) & 0xffffffff
                elapsed = scaled_delta * 8589935 // 8589934592
                total = (base_value + elapsed) & 0xffffffff
                self.assertEqual((result['hours'], result['minutes']),
                                 ((total // 3600) % 24, (total // 60) % 60))
                self.assertEqual(result['outcome'], 'before_ui_handle_read')
                self.assertEqual(result['registers']['EIP'], 0x4c36ae)
                for pc in (0xc3119, 0xc3640, 0xc3687, 0x149630, 0xc36a1, 0xc3710, 0xc374c):
                    self.assertIn(pc, result['pcs'])
                self.assertNotIn(clock.UI_BOUNDARY, result['pcs'])
                reads = [v[:3] for v in result['reads'] if SOURCE <= v[1] < SOURCE + 0x4500]
                self.assertEqual(reads, [(0xc366c, SOURCE + 0x44ac, 4),
                                        (0xc3695, SOURCE + 0x44b0, 4)])
                self.assertTrue(all(SP-0x100 <= v[1] < SP+0x100 for v in result['writes']))
                self.assertEqual(self.source_page(), source)
                self.assertEqual(self.caller(), before)

    def test_full_splitter_unsigned_bounds_and_byte_stores(self):
        for value in (0, 59, 60, 3599, 3600, 86399, 86400, 86460, 0x7fffffff, 0x80000000, 0xffffffff):
            with self.subTest(value=value):
                before = self.caller()
                result = self.n.split_clock(value)
                self.assertEqual((result['hours'], result['minutes']),
                                 ((value // 3600) % 24, (value // 60) % 60))
                self.assertEqual([v for v in result['writes'] if v[1] >= SP],
                    [(0xc372f, SP + 0x44, 1, (value // 60) % 60),
                     (0xc374a, SP + 0x40, 1, (value // 3600) % 24)])
                self.assertEqual(result['registers']['ESP'], SP + 16)
                self.assertEqual(self.caller(), before)

    def test_same_vm_writer_receipt_then_actual_consumer(self):
        self.n.write_clock(bytes((0x1a, 1, 2, 3)), clock_ms=100)
        result = self.n.read_clock(clock_ms=10100)
        self.assertEqual((result['hours'], result['minutes']), (6, 13))
        self.vm.mem_write(SOURCE + clock.TIMESTAMP, bytes(4))
        with self.assertRaisesRegex(ValueError, 'differs'):
            self.n.read_clock(clock_ms=10100)

    def test_missing_source_is_not_implicit_zero(self):
        self.vm.mem_write(SOURCE + clock.TIMESTAMP, bytes(8))
        before = self.caller(), self.source_page()
        for state in (None, b'', bytes(7), bytearray(8)):
            with self.subTest(state=state), self.assertRaisesRegex(ValueError, 'Explicit clock source'):
                self.n.read_clock(clock_ms=0, state=state)
        self.assertEqual((self.caller(), self.source_page()), before)
        result = self.n.read_clock(clock_ms=0, state=bytes(8))
        self.assertEqual((result['hours'], result['minutes']), (0, 0))

    def test_invalid_packet_and_external_clock_rejected_without_mutation(self):
        before = self.caller(), self.source_page()
        for raw in (None, b'', bytes((0x1a, 1, 2)), bytes((0x1a, 1, 2, 3, 4)),
                    bytes((0x1b, 1, 2, 3)), bytearray((0x1a, 1, 2, 3))):
            with self.assertRaises(ValueError):
                self.n.write_clock(raw, clock_ms=0)
        for value in (None, True, -1, 2**32, 0.0):
            with self.assertRaises(ValueError):
                self.n.write_clock(b'\x1a\0\0\0', clock_ms=value)
            with self.assertRaises(ValueError):
                self.n.read_clock(clock_ms=value, state=bytes(8))
            with self.assertRaises(ValueError):
                self.n.split_clock(value)
        with self.assertRaises(TypeError):
            self.n.write_clock(b'\x1a\0\0\0')
        with self.assertRaises(TypeError):
            self.n.read_clock(state=bytes(8))
        self.assertEqual((self.caller(), self.source_page()), before)

    def test_binding_and_layout_fail_closed(self):
        for pointer in (0, CHARACTER, SOURCE + 4):
            self.vm.mem_write(OWNER + clock.SOURCE_POINTER, struct.pack('<I', pointer))
            with self.assertRaisesRegex(ValueError, 'packet-source'):
                self.n.write_clock(b'\x1a\0\0\0', clock_ms=0)
        for kw in ({'packet': SP}, {'sp': CHARACTER + 0x100}, {'character': 0xfffffffe},
                   {'owner': True}, {'packet': 0x4500000}, {'sp': 1}):
            with self.subTest(kw=kw), self.assertRaises(ValueError):
                clock.NativeWorldClock(self.vm, **dict(owner=OWNER, character=CHARACTER,
                                                      sp=SP, packet=PACKET) | kw)

    def test_changed_code_import_and_float_constant_rejected(self):
        for address in (clock.BASE + clock.WRITER, clock.CLOCK_IAT, clock.FLOAT_SCALE):
            saved = bytes(self.vm.mem_read(address, 1))
            self.vm.mem_write(address, bytes((saved[0] ^ 1,)))
            before = self.caller(), self.source_page()
            with self.assertRaisesRegex(ValueError, 'changed'):
                self.n.write_clock(b'\x1a\0\0\0', clock_ms=0)
            self.assertEqual((self.caller(), self.source_page()), before)
            self.vm.mem_write(address, saved)

    def test_missing_or_read_only_fields_cannot_receive_writer_stores(self):
        page = (SOURCE + clock.TIMESTAMP) & ~4095
        before = self.caller(), self.source_page()
        self.vm.mem_protect(page, 4096, UC_PROT_READ)
        with self.assertRaisesRegex(ValueError, 'permissions'):
            self.n.write_clock(b'\x1a\0\0\0', clock_ms=0)
        self.vm.mem_protect(page, 4096, UC_PROT_READ | UC_PROT_WRITE)
        self.assertEqual((self.caller(), self.source_page()), before)
        self.vm.mem_unmap(page, 4096)
        with self.assertRaisesRegex(ValueError, 'unmapped'):
            self.n.read_clock(clock_ms=0, state=bytes(8))

    def test_os_stop_does_not_run_existing_host_clock_adapter(self):
        page = clock.CLOCK_TARGET & ~4095
        self.vm.mem_map(page, 4096, UC_PROT_READ | UC_PROT_EXEC)
        visits = []
        hook = self.vm.hook_add(UC_HOOK_CODE, lambda vm, address, size, data: visits.append(address),
                                begin=clock.CLOCK_TARGET, end=clock.CLOCK_TARGET)
        before = self.caller()
        try:
            result = self.n.write_clock(b'\x1a\0\0\0', clock_ms=0x12345678)
            self.assertEqual(result['timestamp'], 0x12345678)
            self.assertEqual(self.n.read_clock(clock_ms=0x12345678)['hours'], 0)
            self.assertEqual(visits, [])
            self.assertEqual(self.caller(), before)
        finally:
            self.vm.hook_del(hook)

    def test_interrupted_writer_restores_context_stack_and_packet(self):
        def interrupt(vm, address, size, data):
            raise RuntimeError('explicit interruption')
        hook = self.vm.hook_add(UC_HOOK_CODE, interrupt,
                                begin=clock.BASE + 0xc3605, end=clock.BASE + 0xc3605)
        before = self.caller()
        try:
            with self.assertRaisesRegex(RuntimeError, 'interruption'):
                self.n.write_clock(b'\x1a\1\2\3', clock_ms=123)
            self.assertEqual(self.caller(), before)
            self.assertEqual(struct.unpack('<I', self.vm.mem_read(SOURCE + 0x44ac, 4))[0], 123)
            with self.assertRaisesRegex(ValueError, 'receipt'):
                self.n.read_clock(clock_ms=123)
        finally:
            self.vm.hook_del(hook)


if __name__ == '__main__':
    unittest.main()
