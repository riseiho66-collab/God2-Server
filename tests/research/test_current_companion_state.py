"""Execute pinned S2C31 parser/dispatcher/consumer, without stubs or live UI.

Positive matches stop before AA2AF's first refresh call. Missing keys execute
the full consumer and return to the dispatcher join. Fixtures are historical
bytes or explicit synthetic memory probes, never invented gameplay records.
"""
import hashlib
import json
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'artifacts/tooling/crypto-oracle-python'))
from tools.strike_lab.current_companion_state import (
    CONSUMER_RVA, COUNT_OFFSET, DISPATCH_RVA, IMAGE_SHA, RECORD_SIZE,
    ROWS_OFFSET, ROW_STRIDE, SCALAR_STOP_RVA, DeityStatusRecord,
    decode_deity_status, project_deity_status_scalar,
)
from unicorn import (Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE,
                     UC_HOOK_MEM_WRITE, UC_PROT_READ, UC_PROT_WRITE, UC_PROT_EXEC)
from unicorn.x86_const import (UC_X86_REG_EAX, UC_X86_REG_EBP, UC_X86_REG_EBX,
                               UC_X86_REG_ECX, UC_X86_REG_EIP, UC_X86_REG_ESP)

BASE, STACK, NET, ACTOR, PACKET = 0x400000, 0x3000000, 0x3200000, 0x3700000, 0x3900000
WORLD = 0x4000000
UI = WORLD + 0xa7f2f6c
SP = STACK + 0x2000
HISTORICAL_RECORD = bytes.fromhex(
    '31110200001600000000000000040100001b0029000d00060083090000')


def state_with_keys(keys):
    state = bytearray((i * 29 + 0xa5) & 255
                      for i in range(ROWS_OFFSET + len(keys) * ROW_STRIDE + 16))
    state[COUNT_OFFSET] = len(keys)
    for index, key in enumerate(keys):
        struct.pack_into('<H', state, ROWS_OFFSET + index * ROW_STRIDE, key)
    return bytes(state)


class CurrentCompanionStateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image = (ROOT / 'artifacts/capture_work/host-20260918-1430/output/'
                     'native-master-01-stable.bin').read_bytes()
        if hashlib.sha256(cls.image).hexdigest() != IMAGE_SHA:
            raise AssertionError('Pinned current client image changed')

    def vm(self):
        vm = Uc(UC_ARCH_X86, UC_MODE_32)
        vm.mem_map(BASE, (len(self.image) + 4095) & ~4095, UC_PROT_READ | UC_PROT_EXEC)
        vm.mem_write(BASE, self.image)
        for address, size in ((STACK, 0x4000), (NET, 0x5000), (ACTOR, 0x40000),
                              (PACKET, 4096), ((UI + 0x86888) & ~4095, 4096)):
            vm.mem_map(address, size, UC_PROT_READ | UC_PROT_WRITE)
        vm.mem_write(UI + 0x86888, struct.pack('<I', ACTOR))
        return vm

    def run_to(self, vm, entry, stop):
        # The exact hook also works when a cached block crosses this stop.
        hook = vm.hook_add(UC_HOOK_CODE, lambda uc, a, s, c: uc.emu_stop(),
                           begin=BASE + stop, end=BASE + stop)
        try:
            vm.emu_start(BASE + entry, BASE + stop, count=10000, timeout=1000000)
        finally:
            vm.hook_del(hook)
        self.assertEqual(vm.reg_read(UC_X86_REG_EIP), BASE + stop)

    def call(self, vm, entry, *arguments):
        stop = STACK + 0x3ff0
        vm.mem_write(SP, struct.pack('<' + 'I' * (1 + len(arguments)),
                                     stop, *arguments))
        vm.reg_write(UC_X86_REG_ESP, SP)
        vm.reg_write(UC_X86_REG_ECX, NET)
        self.run_to(vm, entry, stop - BASE)
        return vm.reg_read(UC_X86_REG_EAX)

    def consume(self, vm, state, logical, match):
        vm.mem_write(ACTOR + len(state), b'\x5a' * 16)
        vm.mem_write(ACTOR, state)
        vm.mem_protect(PACKET, 4096, UC_PROT_READ | UC_PROT_WRITE)
        pointer = PACKET + 4096 - len(logical)
        vm.mem_write(pointer, bytes(logical))
        vm.mem_protect(PACKET, 4096, UC_PROT_READ)
        for reg, value in ((UC_X86_REG_ESP, SP), (UC_X86_REG_EBP, WORLD),
                           (UC_X86_REG_EBX, pointer), (UC_X86_REG_EAX, 0x31)):
            vm.reg_write(reg, value)
        writes = []
        hook = vm.hook_add(UC_HOOK_MEM_WRITE,
            lambda uc, access, address, size, value, context: writes.append((address, size)))
        try:
            self.run_to(vm, 0x68b61, SCALAR_STOP_RVA if match else 0x6b517)
        finally:
            vm.hook_del(hook)
        self.assertEqual(bytes(vm.mem_read(ACTOR + len(state), 16)), b'\x5a' * 16)
        if not match:
            self.assertEqual(vm.reg_read(UC_X86_REG_ESP), SP)
        return bytes(vm.mem_read(ACTOR, len(state))), writes

    def check_native(self, vm, state, logical):
        expected = project_deity_status_scalar(state, logical)
        actual, writes = self.consume(vm, state, logical, expected.matched_index is not None)
        self.assertEqual(actual, expected.state)
        allowed = set()
        if expected.matched_index is not None:
            row = ACTOR + ROWS_OFFSET + expected.matched_index * ROW_STRIDE
            allowed = {(row + 2, 1), (row + 0x28, 2), (row + 0x5a, 1)}
            allowed |= {(row + n, 4) for n in range(0x44, 0x58, 4)}
            allowed |= {(row + n, 2) for n in range(0x38, 0x40, 2)}
        nonstack = [(a, n) for a, n in writes if not STACK <= a < STACK + 0x4000]
        self.assertEqual(set(nonstack), allowed)
        self.assertEqual(len(nonstack), len(allowed))
        return expected

    def test_historical_fixture_hash_and_original_record_boundaries(self):
        fixture = json.loads((ROOT / 'tests/fixtures/recovered-world-state.json').read_text())
        prefix = bytes.fromhex(fixture['logical_hex'])
        self.assertEqual(hashlib.sha256(prefix).hexdigest(), fixture['logical_sha256'])
        self.assertEqual(len(HISTORICAL_RECORD), RECORD_SIZE)
        logical = prefix + HISTORICAL_RECORD
        vm, at = self.vm(), 0
        for opcode, length in ((0x2b, 21), (0x2c, 61), (0x24, 17), (0x39, 17),
                               (0x22, 25), (0x31, 29)):
            self.assertEqual(logical[at], opcode)
            target = struct.unpack_from('<I', self.image, 0x1324 + 4 * opcode)[0]
            self.assertEqual(self.call(vm, target - BASE), length)
            at += length
        self.assertEqual(at, len(logical))
        self.assertEqual(logical[len(prefix):], HISTORICAL_RECORD)
        self.assertEqual(decode_deity_status(HISTORICAL_RECORD).opaque_13_16, b'\x04\x01\0\0')
        self.check_native(vm, state_with_keys([0x10, 0x11, 0x12]), HISTORICAL_RECORD)

    def test_current_native_binding(self):
        self.assertEqual(struct.unpack_from('<I', self.image, 0x1324 + 4 * 0x31)[0], BASE + 0x12fa)
        self.assertEqual(struct.unpack_from('<I', self.image, 0x6b5d4 + 4 * 0x31)[0], BASE + DISPATCH_RVA)
        self.assertEqual(self.image[0x69fb1], 0xe8)
        self.assertEqual(0x69fb6 + struct.unpack_from('<i', self.image, 0x69fb2)[0], CONSUMER_RVA)
        self.assertEqual(self.image[0xaa223:0xaa227], bytes.fromhex('660fbe10'))
        self.assertEqual(self.call(self.vm(), 0x12fa), RECORD_SIZE)

    def test_all_selector_bytes_sign_extension_and_first_match(self):
        vm = self.vm()
        for selector in range(256):
            logical = bytes((0x31, selector)) + HISTORICAL_RECORD[2:]
            key = selector if selector < 128 else selector | 0xff00
            # For high bytes, the unsigned WORD is deliberately a wrong key.
            keys = [0x1234, key, key] if selector < 128 else [selector, key, key]
            with self.subTest(selector=selector):
                result = self.check_native(vm, state_with_keys(keys), logical)
                self.assertEqual(result.matched_index, 1)
                if selector >= 128:
                    self.assertIsNone(self.check_native(vm, state_with_keys([selector]), logical).matched_index)

    def test_count_boundaries_missing_key_and_no_insertion(self):
        vm = self.vm()
        for count in (0, 1, 16, 255):
            state = state_with_keys([0x1234] * count)
            self.assertIsNone(self.check_native(vm, state, HISTORICAL_RECORD).matched_index)
            if count:
                keys = [0x1234] * (count - 1) + [0x11]
                self.assertEqual(self.check_native(vm, state_with_keys(keys), HISTORICAL_RECORD).matched_index,
                                 count - 1)

    def test_word_boundaries_widening_split_and_residual_preservation(self):
        vm = self.vm()
        state = state_with_keys([0x11, 0x12])
        for value in (0, 1, 0x7fff, 0x8000, 0xffff):
            raw = bytearray(HISTORICAL_RECORD)
            raw[2] = value & 255
            struct.pack_into('<5H', raw, 3, *([value] * 5))
            struct.pack_into('<4H', raw, 17, *([value] * 4))
            struct.pack_into('<H', raw, 25, value)
            decoded = decode_deity_status(raw)
            self.assertEqual((decoded.low15, decoded.high1), (value & 0x7fff, value >> 15))
            result = self.check_native(vm, state, raw)
            self.assertEqual(self.check_native(vm, result.state, raw).state, result.state)

    def test_opaque_bytes_roundtrip_without_state_effect(self):
        vm = self.vm()
        state = state_with_keys([0x11])
        expected = self.check_native(vm, state, HISTORICAL_RECORD).state
        for offset in (13, 14, 15, 16, 27, 28):
            for value in (0, 0x80, 0xff):
                raw = bytearray(HISTORICAL_RECORD)
                raw[offset] = value
                decoded = decode_deity_status(raw)
                self.assertEqual(decoded.encode(), bytes(raw))
                self.assertEqual(self.check_native(vm, state, raw).state, expected)

    def test_original_parser_requires_all_29_bytes_including_ignored_tail(self):
        for length in range(1, 30):
            with self.subTest(length=length):
                vm = self.vm()
                vm.mem_protect(0x5b4000, 4096, UC_PROT_READ | UC_PROT_WRITE)
                vm.mem_write(0x5b4da8, bytes(4))
                vm.mem_write(NET + 0x2cb8, b'\x01')
                vm.mem_write(NET + 0x758 + 0xc10, HISTORICAL_RECORD[:length])
                vm.mem_write(NET + 0x758 + 0x1810, struct.pack('<II', length, 0))
                self.assertEqual(self.call(vm, 0x13420, 1), 0 if length == 29 else 1)
                if length == 29:
                    self.assertEqual(struct.unpack('<I', vm.mem_read(NET + 0x2cc0, 4))[0], 29)
                    pointer = self.call(vm, 0x13650, 1)
                    self.assertEqual(bytes(vm.mem_read(pointer, 29)), HISTORICAL_RECORD)
        # The consumer itself does not read the ignored trailing two bytes.
        # Parser-level strictness must not be weakened to that read footprint.
        vm, state = self.vm(), state_with_keys([0x11])
        for length in (27, 28):
            actual, _ = self.consume(vm, state, HISTORICAL_RECORD[:length], True)
            self.assertEqual(actual, project_deity_status_scalar(state, HISTORICAL_RECORD).state)

    def test_malformed_records_and_states_rejected_without_mutation(self):
        for raw in [HISTORICAL_RECORD[:n] for n in range(29)] + [
                HISTORICAL_RECORD + b'\0', HISTORICAL_RECORD * 2,
                b'\x30' + HISTORICAL_RECORD[1:]]:
            with self.assertRaises(ValueError):
                decode_deity_status(raw)
        for raw in (None, 29, '31', [0x31] * 29):
            with self.assertRaises(TypeError):
                decode_deity_status(raw)
        state = bytearray(state_with_keys([0x11]))
        before = bytes(state)
        for incomplete in (state[:COUNT_OFFSET], state[:ROWS_OFFSET], state[:ROWS_OFFSET + ROW_STRIDE - 1]):
            with self.assertRaises(ValueError):
                project_deity_status_scalar(incomplete, HISTORICAL_RECORD)
        project_deity_status_scalar(state, HISTORICAL_RECORD)
        self.assertEqual(bytes(state), before)
        raw = bytearray(HISTORICAL_RECORD)
        decoded = decode_deity_status(raw)
        raw[1] = 0
        self.assertEqual(decoded.encode(), HISTORICAL_RECORD)
        with self.assertRaises(TypeError):
            DeityStatusRecord(raw)


if __name__ == '__main__':
    unittest.main()
