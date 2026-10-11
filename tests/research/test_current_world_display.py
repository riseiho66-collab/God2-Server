"""Original full display-pool constructor; no live presentation claim."""
import unittest
import struct
from types import SimpleNamespace
from unittest.mock import Mock

from tools.strike_lab.current_world_display import (
    NativeWorldDisplay, DISPLAY_POOL, DISPLAY_EXTENT, RECTANGLES, WORLD_COMPONENTS,
    SCENE_BRIDGE, MESSAGES)
from tools.strike_lab.current_world_ui_resource import ASSET, pinned_sources
from tools.strike_lab.current_world_display import BASE
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32
from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_ESP, UC_X86_REG_EIP


class DisplayMappingTests(unittest.TestCase):
    def test_only_gaps_are_mapped_in_contiguous_runs(self):
        vm = Mock()
        vm.mem_regions.return_value = [(0x3000, 0x3fff, 5), (0x1000, 0x1fff, 1)]
        NativeWorldDisplay._map_rw(SimpleNamespace(vm=vm), 0x1080, 0x4080)
        self.assertEqual([call.args for call in vm.mem_map.call_args_list],
                         [(0x2000, 0x1000, 3), (0x4000, 0x2000, 3)])
        vm.mem_protect.assert_not_called()

    def test_existing_and_invalid_ranges(self):
        vm = Mock()
        vm.mem_regions.return_value = [(0x1000, 0x9fff, 5)]
        host = SimpleNamespace(vm=vm)
        NativeWorldDisplay._map_rw(host, 0x1080, 1)
        vm.mem_map.assert_not_called()
        for address, size in ((-1, 1), (0, 0), (0, -1), (0xffffffff, 2)):
            with self.assertRaises(ValueError):
                NativeWorldDisplay._map_rw(host, address, size)


class DisplayCrtTests(unittest.TestCase):
    def setUp(self):
        self.n = NativeWorldDisplay.__new__(NativeWorldDisplay)
        self.n.vm = self.vm = Uc(UC_ARCH_X86, UC_MODE_32)
        self.vm.mem_map(0x6000000, 0x4000)
        self.sp, self.source, self.fmt, self.dest = (0x6000000+i*0x1000 for i in range(4))

    def invoke(self, source, fmt=b'%s'):
        self.vm.mem_write(self.sp, struct.pack('<IIII', BASE+0x109aee,
                                              self.source, self.fmt, self.dest+8))
        self.vm.mem_write(self.source, source+b'\0')
        self.vm.mem_write(self.fmt, fmt+b'\0')
        self.vm.mem_write(self.dest, b'\xa5'*32)
        self.vm.reg_write(UC_X86_REG_ESP, self.sp)
        self.n._service(self.vm, BASE+0x1480b4, 1, None)

    def test_bounded_sscanf_token_and_eof_semantics(self):
        for source, token in ((b'  BoundHero ', b'BoundHero'), (b'\tName\nOther', b'Name'),
                              (b'123456789012345', b'123456789012345'),
                              (b'', b''), (b' \t\r\n\v\f', b'')):
            self.invoke(source)
            expected = b'\xa5'*8 + (token+b'\0' if token else b'')
            expected += b'\xa5'*(32-len(expected))
            self.assertEqual(bytes(self.vm.mem_read(self.dest, 32)), expected)
            self.assertEqual(self.vm.reg_read(UC_X86_REG_EAX), 1 if token else 0xffffffff)
            self.assertEqual(self.vm.reg_read(UC_X86_REG_ESP), self.sp+4)
            self.assertEqual(self.vm.reg_read(UC_X86_REG_EIP), BASE+0x109aee)

    def test_unsupported_format_name_and_capacity_fail_without_write(self):
        for source, fmt in ((b'x', b'%d'), (b'x'*16, b'%s'), (b'\x81\x40', b'%s')):
            with self.assertRaises(AssertionError):
                self.invoke(source, fmt)
            self.assertEqual(bytes(self.vm.mem_read(self.dest, 32)), b'\xa5'*32)


class WorldDisplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.n = NativeWorldDisplay()

    def test_full_native_pool_and_nonoverlapping_resources(self):
        n = self.n
        self.assertTrue(all(n.u32(DISPLAY_POOL+0x1c+0xa7e0*i) == 0 for i in range(4096)))
        self.assertEqual(n.u32(DISPLAY_POOL+0xa7e001c), 0)
        self.assertEqual(n.u32(DISPLAY_POOL+0xa7e0020), 5)
        for pointer, size in n.allocations.items():
            self.assertFalse(pointer < DISPLAY_POOL+DISPLAY_EXTENT and DISPLAY_POOL < pointer+size)
        for pointer, size in ((n.renderer_address, 0x291000),
                              (n.second_bank_address, 0x2a3000), (RECTANGLES, 0x12030)):
            self.assertFalse(pointer < DISPLAY_POOL+DISPLAY_EXTENT and DISPLAY_POOL < pointer+size)
        self.assertTrue(all(n.u32(RECTANGLES+24*i) == 0 for i in range(3072)))
        self.assertEqual(n.u32(0), 0xffffffff)

    def test_title_native_bank_load_binding_and_component_renderer(self):
        n = self.n
        before = len(n.parser_inputs)
        slot = n.bind_title_resources()
        self.assertEqual(n.u32(DISPLAY_POOL), SCENE_BRIDGE)
        self.assertEqual(n.u32(DISPLAY_POOL+4), n.renderer_address)
        self.assertEqual(n.u32(DISPLAY_POOL+8), RECTANGLES)
        self.assertEqual(n.u32(DISPLAY_POOL+12), MESSAGES)
        self.assertEqual(n.u32(DISPLAY_POOL+16), slot)
        plain = pinned_sources()[0][1][1]
        self.assertEqual(n.parser_inputs[before:],
                         [(ASSET.rsplit('/', 1)[-1].lower(), slot, len(plain))] * 2)
        self.assertFalse(n.handles)
        n._initialize_actor_components()
        self.assertEqual(n.u32(WORLD_COMPONENTS+0x28), n.renderer_address)
        self.assertEqual(bytes(n.vm.mem_read(WORLD_COMPONENTS+4, 24)), b'\xff'*24)
        with self.assertRaises(ValueError):
            n.bind_title_resources()


if __name__ == '__main__':
    unittest.main()
