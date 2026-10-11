"""Continue the retained initializer through its native map control creation."""
import struct
import unittest

import test_current_battle_owner_map_metadata as metadata
from tools.strike_lab import current_battle_bootstrap as boot
from unicorn import UC_HOOK_MEM_WRITE
from unicorn.x86_const import UC_X86_REG_ECX, UC_X86_REG_EIP, UC_X86_REG_ESP


class CurrentBattleOwnerMapSpriteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixture = metadata.CurrentBattleOwnerMapMetadataTests
        fixture.setUpClass()
        fixture().test_original_lookups_cache_and_sprite_arguments()
        cls.b, cls.n = b, n = fixture.b, fixture.n
        with cls().assertRaises(ValueError):
            b.continue_owner_map_sprite()
        cls.pending_before = (n.vm.reg_read(UC_X86_REG_EIP), n.vm.reg_read(UC_X86_REG_ESP),
                              bytes(n.vm.mem_read(boot.SP - 0x2000, 0x2400)))
        maps = b.owner_map_metadata
        catalog_before = bytes(n.vm.mem_read(maps.records, 144 * boot.map_metadata.STRIDE))

        def guard_catalog(vm, access, address, size, value, data):
            before = bytes(vm.mem_read(address, size))
            if before != (value & ((1 << (size * 8)) - 1)).to_bytes(size, 'little'):
                raise AssertionError(f'Map load overwrote catalog at {address:X}, '
                                     f'RVA {vm.reg_read(UC_X86_REG_EIP) - boot.BASE:X}')

        hook = n.vm.hook_add(UC_HOOK_MEM_WRITE, guard_catalog,
                            begin=maps.records, end=maps.records + len(catalog_before) - 1)
        try:
            cls.resource = n.load_owner_map(boot.CHARACTER_ROOT)
        finally:
            n.vm.hook_del(hook)
        catalog_after = bytes(n.vm.mem_read(maps.records, len(catalog_before)))
        if catalog_after != catalog_before:
            delta = next(i for i, pair in enumerate(zip(catalog_before, catalog_after)) if pair[0] != pair[1])
            raise AssertionError(f'Host map load altered catalog at offset {delta:X}: '
                                 f'{catalog_before[delta:delta+32].hex()} -> {catalog_after[delta:delta+32].hex()}')
        cls.pending_after = (n.vm.reg_read(UC_X86_REG_EIP), n.vm.reg_read(UC_X86_REG_ESP),
                             bytes(n.vm.mem_read(boot.SP - 0x2000, 0x2400)))
        cls.owner_before = bytes(n.vm.mem_read(boot.OWNER, boot.OWNER_SIZE))
        cls.battle_before = bytes(n.vm.mem_read(boot.RENDERER, 0x291000))
        cls.mouse_before = bytes(n.vm.mem_read(boot.MOUSE, boot.MOUSE_SIZE))
        handle, _, control, _, _ = struct.unpack('<5I', n.vm.mem_read(boot.SP - 0x104, 20))
        cls.control = n.vm.reg_read(UC_X86_REG_ECX) + (handle & 0xffff) * 0x2a08 + control * 100 + 0x8b8
        cls.control_before = bytes(n.vm.mem_read(cls.control, 100))
        cls.calls = b.continue_owner_map_sprite()

    def test_original_control_returns_on_retained_stack(self):
        self.assertEqual(self.pending_before, self.pending_after)
        self.assertEqual((self.resource['group'], self.resource['area']), (47, 2))
        self.assertEqual(self.calls[0x105c20], 1)
        self.assertEqual(self.calls[0x105d3c], 1)
        for pc in (0x18b80, 0x1e7c0, 0x1ef00):
            self.assertEqual(self.calls[pc], 1, hex(pc))
        self.assertEqual(self.control_before[0], 0)
        self.assertEqual(bytes(self.n.vm.mem_read(self.control, 1)), b'\x10')
        mouse_index = struct.unpack('<H', self.n.vm.mem_read(self.control + 8, 2))[0]
        self.assertLess(mouse_index, 0xc00)
        region = boot.MOUSE + mouse_index * 24
        self.assertEqual(self.n.u32(region), 1)
        self.assertEqual(bytes(self.n.vm.mem_read(region + 4, 16)),
                         bytes(self.n.vm.mem_read(self.control + 0x10, 16)))
        self.assertEqual(self.n.vm.reg_read(UC_X86_REG_EIP), boot.BASE + 0xc3331)
        self.assertEqual(self.n.vm.reg_read(UC_X86_REG_ESP), boot.SP - 0xf0)
        self.assertEqual(self.b.counts[boot.ENTRY], 1)

    def test_writes_are_accounted_and_battle_bank_untouched(self):
        expected = bytearray(self.owner_before)
        for _, at, size, value in self.b.owner_map_sprite_writes:
            if boot.OWNER <= at < boot.OWNER + boot.OWNER_SIZE:
                expected[at - boot.OWNER:at - boot.OWNER + size] = value.to_bytes(size, 'little')
        self.assertEqual(bytes(self.n.vm.mem_read(boot.OWNER, boot.OWNER_SIZE)), bytes(expected))
        self.assertEqual(bytes(self.n.vm.mem_read(boot.RENDERER, 0x291000)), self.battle_before)
        mouse = bytearray(self.mouse_before)
        for _, at, size, value in self.b.owner_map_sprite_writes:
            if boot.MOUSE <= at < boot.MOUSE + boot.MOUSE_SIZE:
                mouse[at - boot.MOUSE:at - boot.MOUSE + size] = value.to_bytes(size, 'little')
        self.assertEqual(bytes(self.n.vm.mem_read(boot.MOUSE, boot.MOUSE_SIZE)), bytes(mouse))
        self.b.owner_map_metadata._verify_records(bound=True)
        with self.assertRaises(ValueError):
            self.b.continue_owner_map_sprite()


if __name__ == '__main__':
    unittest.main()
