"""Real indoor resources through native constructors/loaders and model lookup.

No UI/device, client process or server socket. CRT/MFC and small Win32 adapters
are explicit. No native model, ROM, renderer-pool or projection helper is stubbed.
"""
import hashlib
import json
import struct
import sys
import unittest

import test_current_route_advertisement as routes
sys.path.insert(0, str(routes.ROOT))
from tools.strike_lab.current_indoor_resources import (
    NativeIndoorResources, INDOOR, MANAGER, SURFACE, SCRATCH, DIRECTORY)
from tools.strike_lab.indoor_navigation import parse_hmd


class CurrentIndoorResourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image = (routes.ROOT/'artifacts/capture_work/host-20260918-1430/output/'
                     'native-master-01-stable.bin').read_bytes()
        if hashlib.sha256(cls.image).hexdigest() != routes.IMAGE_SHA:
            raise AssertionError('Pinned original image changed')
        cls.oracle = cls().fresh()
        cls.load_result = cls.oracle.load_manager()
        cls.indoor = cls.oracle.u32(MANAGER+0x1030)

    def fresh(self):
        fixture = routes.CurrentRouteAdvertisementTests()
        fixture.image = self.image
        return NativeIndoorResources(fixture.vm(), routes.ROOT.parent/'God2')

    def test_full_manager_loader_builds_actual_models_and_navigation(self):
        n, indoor = self.oracle, self.indoor
        self.assertEqual(self.load_result, 1)
        self.assertNotEqual(indoor, INDOOR)
        self.assertEqual((n.u32(MANAGER+0x30), n.u32(MANAGER+0x34)), (2, 11))
        self.assertEqual(n.opens, [DIRECTORY+'groceryl.hmd', DIRECTORY+'grol.romz'])
        asset = parse_hmd(n.hmd)
        models = []
        self.assertEqual(n.u32(indoor+0x98+0x14), len(asset['models']))
        for index, model in enumerate(asset['models']):
            pointer = n.call(0x4c6f0, index, this=indoor+0x98)
            self.assertNotEqual(pointer, 0)
            models.append(pointer)
            for frame, grid in enumerate(model['grids']):
                data, width, height = struct.unpack('<III', n.vm.mem_read(pointer+0x4c+36*frame, 12))
                self.assertEqual((width, height), (grid['width'], grid['height']))
                self.assertEqual(bytes(n.vm.mem_read(data, width*height)), bytes(grid['cells']))
        self.assertEqual(n.u32(indoor+0x30), models[0])
        node = n.u32(indoor+0x5c)
        self.assertEqual(n.u32(indoor+0x68), 1)
        self.assertEqual(n.u32(node+4), 0)
        self.assertEqual(n.u32(node+0x2c), models[1])
        self.assertEqual(struct.unpack('<ii', n.vm.mem_read(node+0x14, 8)), (2, 8))
        pointer, width, height = struct.unpack('<III', n.vm.mem_read(indoor+0x8c, 12))
        expected = json.loads((routes.ROOT/'artifacts/world-atlas/indoor-2-15.json').read_text())
        self.assertEqual((width, height), (31, 31))
        self.assertEqual(bytes(n.vm.mem_read(pointer, width*height)), bytes.fromhex(expected['grid']['cells_hex']))
        self.assertNotEqual(n.u32(indoor+0x2a2f0c), 0)
        self.assertTrue(SURFACE+0x1258 <= n.u32(SURFACE+0xf555c) < SURFACE+0xf5498)

    def test_real_rom_pixels_and_palette_match_independent_decode(self):
        n = self.oracle
        rom = self.indoor+0x2c4
        self.assertEqual(hashlib.sha256(n.rom).hexdigest(),
                         'e76f5966c13b6a74ab9e084a6c0ff7385ca9f0939e5c9d5bb209d33f44c4ea9b')
        self.assertEqual(n.rom[:12], b'IGSROM02\0\0\0\0')
        self.assertEqual([n.u32(rom+at) for at in (0, 4, 0x88, 0x108c)], [6974, 1, 2, 2])
        position, palettes, images = 12, 0, 0
        dimensions = []
        while position < len(n.rom):
            tag = n.rom[position:position+8]
            size = struct.unpack_from('<I', n.rom, position+8)[0]
            data = n.rom[position+12:position+12+size]
            self.assertEqual(len(data), size)
            position += 12+size
            if tag == b'PALETTE1':
                expected = b''.join(struct.pack('<H', v & 0x7fff) for v in struct.unpack('<256H', data))
                self.assertEqual(bytes(n.vm.mem_read(n.u32(rom+8+4*palettes), 512)), expected)
                palettes += 1
            elif tag == b'PCX_RWIF':
                x0, y0, x1, y1 = struct.unpack_from('<4H', data, 4)
                width, height = x1-x0+1, y1-y0+1
                self.assertEqual(struct.unpack_from('<H', data, 66)[0], width)
                pixels, at = bytearray(), 128
                while len(pixels) < width*height:
                    value = data[at]
                    at += 1
                    if value & 0xc0 == 0xc0:
                        count = value & 0x3f
                        self.assertGreater(count, 0)
                        pixels.extend(bytes([data[at]])*count)
                        at += 1
                    else:
                        pixels.append(value)
                self.assertEqual(len(pixels), width*height)
                image = n.u32(rom+0x8c+4*images)
                self.assertEqual(struct.unpack('<3H', n.vm.mem_read(image, 6)), (width, height, 256))
                self.assertEqual(bytes(n.vm.mem_read(n.u32(image+0x14), len(pixels))), pixels)
                self.assertGreater(len(set(pixels)), 32)
                dimensions.append((width, height))
                images += 1
        self.assertEqual((position, palettes, images), (len(n.rom), 1, 2))
        self.assertEqual(dimensions, [(780, 580), (138, 125)])

    def test_loaded_scene_projection_and_cell_center_inverse_for_all_961_cells(self):
        n = self.oracle
        for y in range(31):
            for x in range(31):
                n.vm.mem_write(SCRATCH+0x1000, b'\xa5'*24)
                n.call(0x49330, x, y, SCRATCH+0x1008, SCRATCH+0x100c, this=MANAGER)
                px, py = struct.unpack('<ii', n.vm.mem_read(SCRATCH+0x1008, 8))
                # Original 49B30: pixel basis 40*(x+y), 20*(30-x+y).
                self.assertEqual((px, py), (40*(x+y), 20*(30-x+y)))
                n.call(0x493c0, px, py, SCRATCH+0x1008, SCRATCH+0x100c, this=MANAGER)
                self.assertEqual(struct.unpack('<ii', n.vm.mem_read(SCRATCH+0x1008, 8)), (x, y-1))
                # 49950/499F0 classify 80x40 diamonds. The projection anchor
                # lies on a shared edge; (+40,+20) is the interior cell center.
                n.call(0x493c0, px+40, py+20, SCRATCH+0x1008, SCRATCH+0x100c, this=MANAGER)
                self.assertEqual(struct.unpack('<ii', n.vm.mem_read(SCRATCH+0x1008, 8)), (x, y))
                self.assertEqual(bytes(n.vm.mem_read(SCRATCH+0x1000, 8)), b'\xa5'*8)
                self.assertEqual(bytes(n.vm.mem_read(SCRATCH+0x1010, 8)), b'\xa5'*8)

    def test_native_bad_hmd_version_is_not_fabricated_success(self):
        n = self.fresh()
        n.files[DIRECTORY+'groceryl.hmd'] = n.hmd.replace(b'HMD', b'BAD', 1)
        with self.assertRaisesRegex(AssertionError, 'Native diagnostic 1070'):
            n.load()
        self.assertEqual(n.u32(INDOOR+0x8c), 0)

    def test_missing_rom_and_null_access_fail_closed(self):
        n = self.fresh()
        del n.files[DIRECTORY+'grol.romz']
        with self.assertRaisesRegex(AssertionError, 'Unqualified indoor file'):
            n.load()
        self.assertEqual(n.u32(INDOOR+0x8c), 0)
        n.vm.mem_write(SCRATCH, b'\xa1\0\0\0\0')
        with self.assertRaisesRegex(AssertionError, 'outside native SEH'):
            n.vm.emu_start(SCRATCH, SCRATCH+5, count=1)

    def test_success_releases_files_locks_and_seh_chain(self):
        n = self.oracle
        self.assertFalse(n.handles)
        self.assertTrue(n.locks)
        self.assertTrue(all(depth == 0 for depth in n.locks.values()))
        self.assertEqual(n.u32(0), 0xffffffff)
        self.assertIn(0x2982a, n.seh_accesses)
        self.assertIn(0x48307, n.seh_accesses)
        self.assertEqual(n.exit_callbacks, [0x449fc0])


if __name__ == '__main__':
    unittest.main()
