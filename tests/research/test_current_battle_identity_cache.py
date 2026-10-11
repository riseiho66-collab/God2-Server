"""Original cache producer/getters; diagnostic inputs, not native abilities."""
import hashlib
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'artifacts/tooling/crypto-oracle-python'))
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE, UC_HOOK_MEM_READ
from unicorn import UC_HOOK_MEM_WRITE, UC_PROT_READ, UC_PROT_EXEC
from unicorn import x86_const as reg

BASE, OWNER, STACK, INPUT, OUTPUT = 0x400000, 0x20000000, 0x21000000, 0x22000000, 0x23000000
SP, RETURN = STACK + 0x8000, BASE + 0x1000
STRIDE, COUNT = 616, 128
IMAGE_SHA = '149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'


class BattleIdentityCacheTests(unittest.TestCase):
    def setUp(self):
        image = (ROOT / 'artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin').read_bytes()
        self.assertEqual(hashlib.sha256(image).hexdigest(), IMAGE_SHA)
        self.vm = Uc(UC_ARCH_X86, UC_MODE_32)
        size = (len(image) + 4095) & ~4095
        self.vm.mem_map(BASE, size)
        self.vm.mem_write(BASE, image)
        self.vm.mem_protect(BASE, size, UC_PROT_READ | UC_PROT_EXEC)
        for address, size in ((OWNER, 0x14000), (STACK, 0x10000), (INPUT, 4096), (OUTPUT, 4096)):
            self.vm.mem_map(address, size)
        self.vm.mem_write(OWNER, b'\xa5' * 0x14000)
        for slot in range(COUNT):
            self.put(OWNER + 0x18 + STRIDE * slot, 0xffffffff)
        self.put(OWNER + 8, 0)  # No renderer: qualify only the native cache setter.

    def put(self, address, value):
        self.vm.mem_write(address, struct.pack('<I', value))

    def run_native(self, start, ranges, *, args=(), stop=RETURN, registers=None):
        self.vm.mem_write(SP, struct.pack('<' + 'I' * (1 + len(args)), RETURN, *args))
        for name in ('EAX', 'EBX', 'ECX', 'EDX', 'ESI', 'EDI', 'EBP'):
            self.vm.reg_write(getattr(reg, 'UC_X86_REG_' + name), 0)
        for name, value in {'ESP': SP, 'ECX': OWNER, 'EFLAGS': 2, **(registers or {})}.items():
            self.vm.reg_write(getattr(reg, 'UC_X86_REG_' + name), value)
        reads, writes = [], []

        def code(vm, address, size, _):
            self.assertTrue(any(lo <= address - BASE and address - BASE + size <= hi
                                for lo, hi in ranges), hex(address - BASE))

        def read(vm, access, address, size, value, _):
            reads.append((address, size))

        def write(vm, access, address, size, value, _):
            writes.append((address, size))

        hooks = [self.vm.hook_add(UC_HOOK_CODE, code),
                 self.vm.hook_add(UC_HOOK_MEM_READ, read),
                 self.vm.hook_add(UC_HOOK_MEM_WRITE, write)]
        try:
            self.vm.emu_start(BASE + start, stop, count=20000)
            self.assertEqual(self.vm.reg_read(reg.UC_X86_REG_EIP), stop)
        finally:
            for hook in hooks:
                self.vm.hook_del(hook)
        if stop == RETURN:
            self.assertEqual(self.vm.reg_read(reg.UC_X86_REG_ESP), SP + 4 + 4 * len(args))
        return self.vm.reg_read(reg.UC_X86_REG_EAX), reads, writes

    def test_input_to_cache_to_battle_getters_all_slots(self):
        strings = (b'DIAG-NAME', b'DIAG-GROUP', b'DIAG-TITLE')
        for slot in range(COUNT):
            with self.subTest(slot=slot):
                identity = slot + 1
                record = OWNER + 0x18 + STRIDE * slot
                self.put(INPUT, 0xa0000000 | identity)
                for offset, value in zip((0x1c, 0x2c, 0x3c), strings):
                    self.vm.mem_write(INPUT + offset, value + b'\0')
                # Execute the intact copying slice, not FC1C0's resource callees.
                _, _, writes = self.run_native(0xfc2c3, [(0xfc2c3, 0xfc33f)],
                    stop=BASE + 0xfc33f, registers={'EBX': INPUT, 'EBP': record})
                self.assertTrue(all(STACK <= a < STACK + 0x10000 or record <= a < record + 0x34
                                    for a, n in writes))
                outputs = (OUTPUT, OUTPUT + 32, OUTPUT + 64)
                eax, reads, writes = self.run_native(0xfac70,
                    [(0xfac70, 0xfad19), (0xfc960, 0xfc98a)], args=(identity, *outputs))
                self.assertEqual(eax, 1)
                for address, value in zip(outputs, strings):
                    self.assertEqual(bytes(self.vm.mem_read(address, len(value) + 1)), value + b'\0')
                allowed = {(OWNER + 0x18 + STRIDE * i, 4) for i in range(slot + 1)}
                cache_reads = [(a, n) for a, n in reads if OWNER <= a < OWNER + 0x14000]
                self.assertTrue(all((a, n) in allowed or record + 4 <= a and a + n <= record + 0x34
                                    for a, n in cache_reads))
                self.assertFalse(any(OWNER <= a < OWNER + 0x14000 for a, n in writes))
                flag = (slot * 17) & 255
                eax, _, _ = self.run_native(0xfbb50,
                    [(0xfbb50, 0xfbba1), (0xfc960, 0xfc98a)], args=(identity, flag))
                self.assertEqual(eax, 1)
                eax, reads, _ = self.run_native(0xfad20,
                    [(0xfad20, 0xfad61), (0xfc960, 0xfc98a)], args=(identity, OUTPUT + 96))
                self.assertEqual(eax, 1)
                self.assertEqual(bytes(self.vm.mem_read(OUTPUT + 96, 1)), bytes([flag]))
                self.assertTrue(all((a, n) in allowed or (a, n) == (record + 0x7b, 1)
                                    for a, n in reads if OWNER <= a < OWNER + 0x14000))

    def test_missing_identity_does_not_return_unknown_fields(self):
        self.vm.mem_write(OUTPUT, b'\xcc' * 100)
        eax, reads, _ = self.run_native(0xfac70,
            [(0xfac70, 0xfad19), (0xfc960, 0xfc98a)],
            args=(0x1234, OUTPUT, OUTPUT + 32, OUTPUT + 64))
        self.assertEqual(eax, 0)
        self.assertEqual(bytes(self.vm.mem_read(OUTPUT, 1)), b'\0')
        self.assertEqual(bytes(self.vm.mem_read(OUTPUT + 32, 1)), b'\0')
        self.assertEqual(bytes(self.vm.mem_read(OUTPUT + 64, 1)), b'\xcc')
        self.assertEqual([(a, n) for a, n in reads if OWNER <= a < OWNER + 0x14000],
                         [(OWNER + 0x18 + STRIDE * i, 4) for i in range(COUNT)])
        eax, _, _ = self.run_native(0xfad20,
            [(0xfad20, 0xfad61), (0xfc960, 0xfc98a)], args=(0x1234, OUTPUT + 96))
        self.assertEqual(eax, 0)
        self.assertEqual(bytes(self.vm.mem_read(OUTPUT + 96, 1)), b'\0')

    def test_original_world_dispatch_and_role_record_prefix(self):
        for opcode, target in ((0x6f, 0x695c8), (0x73, 0x69a28), (0xb2, 0x6b114)):
            with self.subTest(opcode=opcode):
                self.vm.mem_write(INPUT, bytes([opcode]))
                self.run_native(0x68b4e, [(0x68b4e, 0x68b68)],
                    stop=BASE + target, registers={'EBX': INPUT})
        # The original 6F handler removes the opcode and extracts packed
        # identity/two values before its first UI callee. Do not stub that callee.
        for identity, first, second in ((1, 0, 0), (0xfff, 0x7fff, 0x7fff), (173, 213, 417)):
            self.put(INPUT + 1, identity | 0xa0000000)
            self.put(INPUT + 13, (first << 2) | (second << 17) | 3)
            self.run_native(0x695c8, [(0x695c8, 0x695f1)], stop=BASE + 0x695f1,
                            registers={'EBX': INPUT, 'EBP': 0})
            self.assertEqual(self.vm.reg_read(reg.UC_X86_REG_EBX), INPUT + 1)
            self.assertEqual(self.vm.reg_read(reg.UC_X86_REG_ESP), SP - 12)
            self.assertEqual(struct.unpack('<III', self.vm.mem_read(SP - 12, 12)),
                             (identity, first, second))

    def test_b2_world_handler_to_cache_setter_without_renderer(self):
        record = OWNER + 0x18 + 127 * STRIDE
        self.put(record, 0x1234)
        for flag in (0, 1, 0x7f, 0x80, 0xff):
            self.vm.mem_write(INPUT, struct.pack('<BHB', 0xb2, 0x1234, flag))
            eax, _, writes = self.run_native(0x6b114,
                [(0x6b114, 0x6b12a), (0xfbb50, 0xfbba1), (0xfc960, 0xfc98a)],
                stop=BASE + 0x6b12a,
                registers={'EBX': INPUT, 'EBP': OWNER - 0x15383410})
            self.assertEqual(eax, 1)
            self.assertEqual(self.vm.reg_read(reg.UC_X86_REG_ESP), SP)
            self.assertEqual(bytes(self.vm.mem_read(record + 0x7b, 1)), bytes([flag]))
            self.assertEqual([(a, n) for a, n in writes if OWNER <= a < OWNER + 0x14000],
                             [(record + 0x7b, 1)])

    def test_four_component_values_are_stored_in_role_doll(self):
        image = bytes(self.vm.mem_read(BASE + 0x19b664, 160)).split(b'\0')[0]
        self.assertTrue(image.endswith(b'\\playlib\\RoleDoll.cpp'))
        record = OWNER + 0x18
        words = (0, 1, 0x7fff, 0xffff)
        self.vm.mem_write(INPUT, struct.pack('<4H', *words))
        packed = bytes((3, 0x05, 7, 0x29, 11, 0x53, 13, 0xe7))
        self.vm.mem_write(INPUT + 0x100, packed)
        for force_seven in (False, True):
            with self.subTest(force_seven=force_seven):
                self.vm.mem_write(record + 0x61, bytes([0x10 if force_seven else 0]))
                self.vm.mem_write(record + 0x224, b'\xa5' * 0x34)
                _, _, writes = self.run_native(0xfc130,
                    [(0xfc130, 0xfc1b4), (0xff450, 0xff46d), (0xffa20, 0xffa3b)],
                    args=(INPUT, record, 0, INPUT + 0x100))
                expected_writes = set()
                for i, value in enumerate(words):
                    word_address = record + 0x228 + 6 * i
                    byte_address = record + 0x22c + 6 * i
                    expected_writes.update(((word_address, 2), (byte_address, 1)))
                    self.assertEqual(struct.unpack('<H', self.vm.mem_read(word_address, 2))[0], value)
                    self.assertEqual(bytes(self.vm.mem_read(byte_address, 1)),
                                     bytes([7 if force_seven else packed[2*i + 1] >> 5]))
                    packed_address = record + 0x251 + 2 * i
                    self.assertEqual(bytes(self.vm.mem_read(packed_address, 1)),
                                     bytes([0xa5 if force_seven else (packed[2*i + 1] & 0xe0) | 5]))
                    if not force_seven:
                        expected_writes.add((packed_address, 1))
                self.assertEqual(set((a, n) for a, n in writes if OWNER <= a < OWNER + 0x14000),
                                 expected_writes)


if __name__ == '__main__':
    unittest.main()
