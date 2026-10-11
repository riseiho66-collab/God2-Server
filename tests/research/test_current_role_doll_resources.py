"""Offline original-code RoleDoll loader checks, not renderer/E2E acceptance."""
from pathlib import Path
import struct
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.strike_lab.current_role_doll_resources import (
    ASSETS, BANK, BASE, DIRECTORY, SCRATCH, STRIDE, NativeRoleDollResources,
    source_assets)
from unicorn import UC_MEM_READ, UC_PROT_EXEC, UC_PROT_WRITE, UcError
from unicorn.x86_const import UC_X86_REG_EIP


def chunks(data):
    if data[:12] != b'IGSROM02\0\0\0\0':
        raise AssertionError('Unexpected ROM identity')
    position = 12
    while position < len(data):
        if position+12 > len(data):
            raise AssertionError('Truncated ROM chunk header')
        tag = data[position:position+8]
        size = struct.unpack_from('<I', data, position+8)[0]
        position += 12
        if position+size > len(data):
            raise AssertionError('Truncated ROM chunk body')
        yield tag, data[position:position+size]
        position += size


def pcx_pixels(data):
    if data[:4] != bytes((10, 5, 1, 8)) or data[65] != 1:
        raise AssertionError('Unsupported source PCX layout')
    x0, y0, x1, y1 = struct.unpack_from('<4H', data, 4)
    width, height = x1-x0+1, y1-y0+1
    stride = struct.unpack_from('<H', data, 66)[0]
    if not 0 < width <= stride <= 4096 or not 0 < height <= 4096:
        raise AssertionError('PCX dimension bound')
    result, at = bytearray(), 128
    while len(result) < stride*height:
        value = data[at]
        at += 1
        count = 1
        if value & 0xc0 == 0xc0:
            count = value & 0x3f
            value = data[at]
            at += 1
        if not count or len(result)+count > stride*height:
            raise AssertionError('Invalid source PCX run')
        result.extend(bytes([value])*count)
    return width, height, b''.join(result[y*stride:y*stride+width] for y in range(height))


class CurrentRoleDollResourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = NativeRoleDollResources()
        cls.initial = bytes(cls.native.vm.mem_read(BANK, 512*STRIDE))
        cls.results = [cls.native.load(name, slot) for slot, name in enumerate(ASSETS)]

    def test_uncached_original_loader_decompresses_and_populates_each_slot(self):
        n = self.native
        expected = ((4201, 8, 1, 19), (4001, 8, 17, 19), (0, 8, 22, 19))
        self.assertEqual(self.results, [4201, 4001, 0])
        for slot, name in enumerate(ASSETS):
            with self.subTest(name=name):
                self.assertEqual(struct.unpack_from('<I', self.initial, slot*STRIDE)[0], 0xffffffff)
                record = BANK+slot*STRIDE
                self.assertEqual(tuple(n.u32(record+o) for o in (0, 4, 0x88, 0x108c)), expected[slot])
                self.assertEqual(n.u32(record+0x1490), 0)
        self.assertEqual(n.parser_inputs, [(name, slot, len(n.decoded[name]))
                                          for slot, name in enumerate(ASSETS)])
        self.assertEqual(n.opens, [DIRECTORY+name for name in ASSETS])
        for rva in (0x29820, 0x1ec0, 0x2a1d0):
            self.assertEqual(n.native_visits.count(rva), 3)
        self.assertEqual(n.native_visits.count(0x2c090), 39)
        self.assertEqual(n.native_visits.count(0x2d250), 1)
        self.assertIn(0x28740, n.native_visits)
        self.assertEqual(bytes(n.vm.mem_read(BANK+3*STRIDE, 509*STRIDE)), self.initial[3*STRIDE:])

    def test_all_24_palettes_and_40_images_match_source(self):
        n = self.native
        palettes = images = pixels_checked = 0
        for slot, name in enumerate(ASSETS):
            palette_index = image_index = 0
            record = BANK+slot*STRIDE
            for tag, data in chunks(n.decoded[name]):
                if tag == b'PALETTE1':
                    expected = b''.join(struct.pack('<H', v & 0x7fff)
                                        for v in struct.unpack('<256H', data))
                    pointer = n.u32(record+8+4*palette_index)
                    self.assertEqual(bytes(n.vm.mem_read(pointer, 512)), expected)
                    palette_index += 1
                    palettes += 1
                elif tag in (b'PCX_RWIF', b'TGA_RWIF'):
                    image = n.u32(record+0x8c+4*image_index)
                    if tag == b'PCX_RWIF':
                        width, height, expected = pcx_pixels(data)
                        self.assertEqual(struct.unpack('<3H', n.vm.mem_read(image, 6)), (width, height, 256))
                    else:
                        width, height = struct.unpack_from('<2I', data)
                        self.assertEqual((width, height), (1, 1))
                        self.assertEqual(struct.unpack('<3H', n.vm.mem_read(image, 6)), (width, height, 0))
                        self.assertEqual(n.vm.mem_read(image+6, 1), b'\x01')
                        expected = data[8:8+width*height*2]
                        row_offsets = data[8+width*height*2:]
                        self.assertEqual(bytes(n.vm.mem_read(n.u32(image+0x10), height*4)), row_offsets)
                    self.assertEqual(bytes(n.vm.mem_read(n.u32(image+0x14), len(expected))), expected)
                    pixels_checked += width*height
                    image_index += 1
                    images += 1
            self.assertEqual(palette_index, n.u32(record+4))
            self.assertEqual(image_index, n.u32(record+0x88))
        self.assertEqual((palettes, images), (24, 40))
        self.assertGreater(pixels_checked, 20000)

    def test_all_57_actions_steps_and_pools_match_source(self):
        n = self.native
        action_count = steps_checked = pools_checked = 0
        for slot, name in enumerate(ASSETS):
            source = iter(chunks(n.decoded[name]))
            action_index = 0
            for tag, data in source:
                if tag != b'ACT_DATA':
                    continue
                action = n.u32(BANK+slot*STRIDE+0x1090+4*action_index)
                self.assertEqual(bytes(n.vm.mem_read(action, 24)), data[:24])
                self.assertEqual(n.string(action+24), data[24:].split(b'\0', 1)[0])
                steps, pools = struct.unpack_from('<2I', data, 16)
                for step in range(steps):
                    step_tag, step_data = next(source)
                    self.assertEqual(step_tag, b'ACT_STEP')
                    self.assertEqual(len(step_data) % 10, 0)
                    self.assertEqual(struct.unpack('<H', n.vm.mem_read(action+0x430+2*step, 2))[0], len(step_data)//10)
                    pointer = n.u32(action+0x30+4*step)
                    self.assertEqual(bytes(n.vm.mem_read(pointer, len(step_data))), step_data)
                    steps_checked += 1
                for pool in range(pools):
                    pool_tag, pool_data = next(source)
                    self.assertEqual(pool_tag, b'ACT_POOL')
                    self.assertEqual(len(pool_data), 10)
                    pointer = n.u32(action+0x630+4*pool)
                    # 2A8F3..2A964 copy the first nine source bytes; byte nine
                    # is not copied into the native pool object.
                    self.assertEqual(bytes(n.vm.mem_read(pointer, 9)), pool_data[:9])
                    block_tag, block_data = next(source)
                    self.assertEqual(block_tag, b'ACTBLOCK')
                    block = n.u32(pointer+12)
                    self.assertNotEqual(block, 0)
                    if block_data:
                        self.assertEqual(bytes(n.vm.mem_read(block, len(block_data))), block_data)
                    pools_checked += 1
                action_index += 1
                action_count += 1
            self.assertEqual(action_index, n.u32(BANK+slot*STRIDE+0x108c))
        self.assertEqual((action_count, steps_checked, pools_checked), (57, 306, 77))

    def test_missing_real_files_return_native_failure_without_populating_bank(self):
        for name in ASSETS:
            with self.subTest(name=name):
                n = NativeRoleDollResources()
                before = bytes(n.vm.mem_read(BANK, STRIDE))
                del n.files[DIRECTORY+name]
                self.assertEqual(n.load(name, 0), 0xffffffff)
                self.assertEqual(bytes(n.vm.mem_read(BANK, STRIDE)), before)
                self.assertEqual(n.attempts, [DIRECTORY+name]*2)
                self.assertFalse(n.parser_inputs)
                self.assertFalse(n.handles)
                self.assertEqual(n.u32(0), 0xffffffff)

    def test_native_slot_boundary_and_unqualified_inputs_fail_closed(self):
        n = NativeRoleDollResources()
        self.assertEqual(n.load('r01f002.romz', 512), 0xffffffff)
        self.assertFalse(n.attempts)
        with self.assertRaisesRegex(ValueError, 'Qualified RoleDoll'):
            n.load('../unqualified.romz', 0)
        with self.assertRaisesRegex(ValueError, 'empty slot'):
            self.native.load('r01f002.romz', 1)
        with self.assertRaisesRegex(AssertionError, 'allocation bound'):
            n.allocate(0x1000001)
        with self.assertRaisesRegex(AssertionError, 'allocation bound'):
            n.allocate(0)
        n.heap_limit = n.heap
        with self.assertRaisesRegex(AssertionError, 'allocation bound'):
            n.allocate(1)

    def test_source_identity_is_checked_before_execution(self):
        original = Path.read_bytes

        def changed(path):
            data = original(path)
            return bytes([data[0] ^ 1])+data[1:]

        with patch.object(Path, 'read_bytes', changed):
            with self.assertRaisesRegex(ValueError, 'Pinned RoleDoll source changed'):
                source_assets(ROOT.parent / 'God2')

    def test_files_seh_and_memory_permissions(self):
        n = self.native
        self.assertFalse(n.handles)
        self.assertEqual(n.u32(0), 0xffffffff)
        self.assertTrue({0x29707, 0x2970e, 0x29749, 0x2982a, 0x29831, 0x29a9d} <= n.seh_accesses)
        for start, end, permissions in n.vm.mem_regions():
            if start <= BASE+0x29820 <= end:
                self.assertFalse(permissions & UC_PROT_WRITE)
            if start >= BANK:
                # The captured FindFirstFile address is a hook-only API page.
                if start <= n.find_first <= end:
                    continue
                self.assertFalse(permissions & UC_PROT_EXEC)
        fresh = NativeRoleDollResources()
        fresh.vm.reg_write(UC_X86_REG_EIP, BASE+0x29820)
        with self.assertRaisesRegex(AssertionError, 'outside native SEH'):
            fresh._seh(fresh.vm, UC_MEM_READ, 0, 4, 0, None)
        with self.assertRaises(UcError):
            fresh.vm.emu_start(SCRATCH, SCRATCH+1, count=1)


if __name__ == '__main__':
    unittest.main()
