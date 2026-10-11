"""Bounded create-preview -> normal S2C2A component-consumer equivalence.

Runs pinned x86 in synthetic Unicorn memory only; no subprocess, UI, sockets,
assets, database, or production serializer. Resource lookup results are stubs.
"""
import hashlib
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'artifacts/tooling/crypto-oracle-python'))
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn import UC_PROT_READ, UC_PROT_EXEC
from unicorn.x86_const import (
    UC_X86_REG_EAX, UC_X86_REG_EBX, UC_X86_REG_EBP, UC_X86_REG_ECX,
    UC_X86_REG_EDI, UC_X86_REG_ESI, UC_X86_REG_ESP, UC_X86_REG_EIP,
)

BASE, STACK, MAIN, ACTOR, RESOURCE, RECORD, WORLD = (
    0x400000, 0x3000000, 0x3100000, 0x3400000, 0x3500000, 0x3800000, 0x4000000,
)
SP = STACK + 0x2000
SHA = '149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'


def appearance_projection(body, profile):
    """Research-only masked projection; caller supplies valid owned C and B."""
    if len(body) != 36 or len(profile) != 40:
        raise ValueError('Expected 36-byte 2A body and 40-byte create profile')
    result = bytearray(body)
    result[13] = (result[13] & 0x1f) | ((profile[32] & 7) << 5)
    result[15] = (result[15] & 0x1f) | (profile[36] & 0xe0)
    return bytes(result)


class CurrentWorldAppearanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image = (ROOT / 'artifacts/capture_work/host-20260918-1430/output/'
                     'native-master-01-stable.bin').read_bytes()
        if hashlib.sha256(cls.image).hexdigest() != SHA:
            raise AssertionError('Pinned current client image changed')

    def vm(self, derived=2, binary_sensitive=False):
        vm = Uc(UC_ARCH_X86, UC_MODE_32)
        size = (len(self.image) + 4095) & ~4095
        vm.mem_map(BASE, size)
        vm.mem_write(BASE, self.image)
        vm.mem_protect(BASE, size, UC_PROT_READ | UC_PROT_EXEC)
        for address, length in ((STACK, 0x4000), (MAIN, 0x180000),
                                (ACTOR, 0x6000), (RESOURCE, 0x170000), (RECORD, 0x1000)):
            vm.mem_map(address, length)
        for offset in (0xa7e04d0, 0x1539ad70):
            vm.mem_map((WORLD + offset) & ~4095, 4096)
        vm.mem_write(STACK, b'\xa5' * 0x4000)
        vm.mem_write(ACTOR, b'\xa5' * 0x6000)
        vm.mem_write(RECORD + 0x1e, struct.pack('<H', 73))
        vm.mem_write(RECORD + 0x2a, bytes([derived]))
        vm.mem_write(RECORD + 0x11e, struct.pack('<H', 74))
        vm.mem_write(RECORD + 0x12a, bytes([3]))
        # Synthetic table entries 0/1 both return the same zero lookup modifier.
        vm.mem_write(RESOURCE + 0x682e0 + 0x121f6, struct.pack('<H', 2))
        lookups = []

        def stub(uc, address, size, context):
            rva = address - BASE
            services = {0x52460: (20, RECORD), 0x106c30: (8, 73),
                        0x63640: (12, 0), 0x63ad0: (12, 0)}
            if rva not in services:
                return
            count, result = services[rva]
            sp = uc.reg_read(UC_X86_REG_ESP)
            values = struct.unpack('<' + 'I' * (1 + count // 4), uc.mem_read(sp, 4 + count))
            if rva == 0x52460:
                # Original 52460 treats the resource key arguments as bytes.
                lookups.append(tuple(value & 255 for value in values[1:]))
                if binary_sensitive and values[1] & 255:
                    result = RECORD + 0x100
            uc.reg_write(UC_X86_REG_EAX, result)
            uc.reg_write(UC_X86_REG_ESP, sp + 4 + count)
            uc.reg_write(UC_X86_REG_EIP, values[0])

        vm.hook_add(UC_HOOK_CODE, stub)
        return vm, lookups

    def run_to(self, vm, start, stop):
        vm.emu_start(BASE + start, BASE + stop, timeout=1000000, count=20000)
        self.assertEqual(vm.reg_read(UC_X86_REG_EIP), BASE + stop)
        self.assertEqual(vm.reg_read(UC_X86_REG_ESP), SP)

    @staticmethod
    def profile(binary, first, second):
        profile = bytearray(40)
        profile[:10] = b'BoundHero\0'
        profile[29], profile[31] = binary + 1, 1
        profile[32], profile[33], profile[36] = first, binary, second << 5
        struct.pack_into('<H', profile, 38, binary | (8 << 4) | (9 << 10))
        return bytes(profile)

    def preview(self, profile, derived=2, binary_sensitive=False):
        vm, lookups = self.vm(derived, binary_sensitive)
        vm.mem_write(MAIN + 0x15280, profile)
        vm.mem_write(MAIN + 0x178cdc, struct.pack('<I', RECORD))
        vm.mem_write(SP + 0x1c, struct.pack('<I', MAIN))
        vm.reg_write(UC_X86_REG_EDI, MAIN)
        vm.reg_write(UC_X86_REG_ESP, SP)
        self.run_to(vm, 0x9a08, 0x9bbb)
        block = bytes(vm.mem_read(SP + 0x10, 8))
        variants = [vm.mem_read(MAIN + 0x15e38 + 8 + 6*i, 1)[0] for i in range(4)]
        self.assertEqual(bytes(vm.mem_read(MAIN + 0x15280, 40)), profile)
        return block, variants, lookups

    def world(self, body, derived=2, override=False, binary_sensitive=False):
        vm, lookups = self.vm(derived, binary_sensitive)
        vm.mem_write(SP + 0x28, body)
        vm.mem_write(WORLD + 0x1539ad70, bytes([0x10 if override else 0]))
        vm.reg_write(UC_X86_REG_ESP, SP)
        vm.reg_write(UC_X86_REG_EBP, ACTOR)
        vm.reg_write(UC_X86_REG_EBX, WORLD)
        vm.reg_write(UC_X86_REG_ESI, RESOURCE)
        # Enter after scene setup, stop before later actor/scalar initialization.
        # Original 61270, 63780, 63c90/52420, 63de0/526c0 and setters execute.
        self.run_to(vm, 0x68315, 0x68558)
        variants = [vm.mem_read(WORLD + 0xa7e04d0 + 8 + 6*i, 1)[0] for i in range(4)]
        self.assertEqual(bytes(vm.mem_read(ACTOR + 0x4584, 12)), body[12:24])
        self.assertEqual(struct.unpack('<I', vm.mem_read(ACTOR + 0x28, 4))[0], body[13] >> 5)
        self.assertEqual(bytes(vm.mem_read(SP + 0x28, 36)), body)
        self.assertEqual(bytes(vm.mem_read(ACTOR + 0x4594, 0x6000 - 0x4594)),
                         b'\xa5' * (0x6000 - 0x4594))
        return variants, lookups

    def test_original_sender_preserves_projected_profile_fields(self):
        for binary in (0, 1):
            profile = self.profile(binary, 6, 5)
            internal = bytearray(profile)
            internal[29] -= 1
            internal[31] -= 1
            internal[38] &= 0xf0
            vm, _ = self.vm()
            vm.mem_write(MAIN + 0x15280, bytes(internal))
            vm.reg_write(UC_X86_REG_ECX, MAIN)
            vm.reg_write(UC_X86_REG_ESP, SP + 0x3c)
            self.run_to(vm, 0xc160, 0xc1bb)
            self.assertEqual(bytes(vm.mem_read(SP + 0x10, 40)), profile)

    def test_all_owned_variants_and_binary_lookup_limitation(self):
        for binary in (0, 1):
            for first in range(7):
                for second in range(7):
                    with self.subTest(binary=binary, first=first, second=second):
                        profile = self.profile(binary, first, second)
                        block, preview_variants, preview_keys = self.preview(profile)
                        expected = bytes([binary, first << 5, binary, second << 5,
                                          binary, 0, 0x80 | binary, 0])
                        self.assertEqual(block, expected)
                        # Supply preview resource inputs for comparison only.
                        # The binary nibbles are NOT part of the safe projection.
                        body = bytearray(36)
                        body[12:20] = block
                        body[13] ^= 0xe0
                        body[15] ^= 0xe0
                        body = appearance_projection(body, profile)
                        self.assertEqual(body[12:20], block)
                        world_variants, world_keys = self.world(body)
                        self.assertEqual(world_variants, [first, second, 0, 0])
                        self.assertEqual(world_variants, preview_variants)
                        self.assertEqual([key[1] for key in preview_keys], [0, 2, 1, 2, 3])
                        self.assertEqual(world_keys[:1] + world_keys[2:],
                                         preview_keys[:1] + preview_keys[2:])
                        # Preview has not yet assigned component 2's nibble at
                        # its component-1 derived lookup. World reads final B16.
                        self.assertEqual(preview_keys[1], (0, 2, 0, 0, 0))
                        self.assertEqual(world_keys[1], (binary, 2, 0, 0, 0))

    def test_lookup_branch_and_variant_override_boundaries(self):
        profile = self.profile(1, 6, 4)
        block, _, _ = self.preview(profile)
        for selector in (0, 1):
            for derived in (0, 2):
                with self.subTest(selector=selector, derived=derived):
                    _, expected_variants, expected_keys = self.preview(profile, derived)
                    body = bytearray(36)
                    body[6] = selector
                    body[12:20] = block
                    variants, keys = self.world(bytes(body), derived)
                    self.assertEqual(variants, expected_variants)
                    self.assertEqual(keys[:1] + keys[2:], expected_keys[:1] + expected_keys[2:])
                    self.assertEqual((expected_keys[1][0], keys[1][0]), (0, 1))
                    variants, overridden_keys = self.world(bytes(body), derived, override=True)
                    self.assertEqual(variants, [7, 7, 7, 7])
                    self.assertEqual(overridden_keys, keys)

    def test_binary_candidate_can_change_component_one_derived_lookup(self):
        profile = self.profile(1, 3, 4)
        block, _, preview_keys = self.preview(profile, binary_sensitive=True)
        body = bytearray(36)
        body[12:20] = block
        _, world_keys = self.world(bytes(body), binary_sensitive=True)
        self.assertEqual(preview_keys[1], (0, 2, 0, 0, 0))
        self.assertEqual(world_keys[1], (1, 2, 0, 0, 0))
        self.assertEqual(preview_keys[2], (1, 1, 0, 2, 0))
        self.assertEqual(world_keys[2], (1, 1, 0, 3, 0))

    def test_variant_projection_preserves_original_resource_lookup_keys(self):
        profile = self.profile(1, 6, 5)
        body = bytearray(36)
        body[12:24] = bytes.fromhex('b1 19 c0 07 d1 65 81 e3 42 56 78 90')
        before, before_keys = self.world(bytes(body))
        after, after_keys = self.world(appearance_projection(body, profile))
        self.assertEqual(after_keys, before_keys)
        self.assertEqual(after, [6, 5, *before[2:]])

    def test_masks_preserve_every_unowned_bit_and_ignore_unrelated_profile_fields(self):
        masks = {13: 0xe0, 15: 0xe0}
        profile = self.profile(1, 2, 5)
        changed = bytearray(profile)
        changed[29], changed[31] = 7, 5
        changed[33] = 0
        changed[36] |= 31
        changed[37] = 255
        struct.pack_into('<H', changed, 38, (3 << 4) | (4 << 10))
        for seed in (0, 0x55, 0xaa, 0xff):
            body = bytes((seed + i * 17) & 255 for i in range(36))
            projected = appearance_projection(body, profile)
            self.assertEqual(projected, appearance_projection(body, changed))
            for i in range(36):
                self.assertEqual((projected[i] ^ body[i]) & (255 ^ masks.get(i, 0)), 0)


if __name__ == '__main__':
    unittest.main()
