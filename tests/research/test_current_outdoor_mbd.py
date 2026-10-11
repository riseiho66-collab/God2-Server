"""Pinned town blocks against original 40790; CRT read/seek adapters only.

Synthetic MBD owner and destination object; not a full loader or collision test.
"""
import hashlib
import struct
import subprocess
import sys
import unittest

import test_current_route_advertisement as routes
sys.path.insert(0, str(routes.ROOT))
from tools.strike_lab.omega_assets import decode_csvz
from tools.strike_lab.outdoor_mbd import parse_mbd, project_base_window, apply_model_pass, apply_model_points, BLOCK_BYTES
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_ECX, UC_X86_REG_ESP, UC_X86_REG_EIP


class CurrentOutdoorMbdTests(unittest.TestCase):
    vm = routes.CurrentRouteAdvertisementTests.vm
    call = routes.CurrentRouteAdvertisementTests.call
    run_to = routes.CurrentRouteAdvertisementTests.run_to

    @classmethod
    def setUpClass(cls):
        cls.image = (routes.ROOT / 'artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin').read_bytes()
        if hashlib.sha256(cls.image).hexdigest() != routes.IMAGE_SHA:
            raise AssertionError('Current image changed')
        cls.directory = routes.ROOT.parent / 'God2/Data2/map/island01/CityI1'
        cls.data = (cls.directory / 'cityi1.mbd').read_bytes()
        if hashlib.sha256(cls.data).hexdigest() != 'cf4a4f14f9e5377fa47b4f115d44b1fc90c5c9dff0e3e0f358d781ab8c1030ae':
            raise AssertionError('Current town MBD changed')

    def test_every_town_block_matches_native_reader(self):
        self.assertEqual(decode_csvz((self.directory/'cityI1.mbdZ').read_bytes()), self.data)
        parsed = parse_mbd(self.data)
        self.assertEqual((parsed['width'], parsed['height']), (9, 9))
        self.assertEqual(sum(block is not None for block in parsed['blocks']), 66)
        vm = self.vm()
        owner, table, target, cells = routes.NET, routes.BODY, routes.OUTPUT, routes.OUTPUT+0x100
        vm.mem_write(owner+8, struct.pack('<5I', 9, 9, table, 340, 0x1234))
        vm.mem_write(table, self.data[16:340])
        vm.mem_write(target, struct.pack('<3I', cells, 21, 21))
        state = {'position': 0, 'reads': 0, 'seeks': 0}

        def service(uc, address, size, context):
            rva = address-routes.BASE
            if rva not in (0x1477a3, 0x14785c, 0x2c70):
                return
            if rva == 0x2c70:
                self.fail('Native block index assertion')
            sp = uc.reg_read(UC_X86_REG_ESP)
            ret = struct.unpack('<I', uc.mem_read(sp, 4))[0]
            if rva == 0x1477a3:
                handle, offset, origin = struct.unpack('<3I', uc.mem_read(sp+4, 12))
                self.assertEqual((handle, origin), (0x1234, 0))
                state['position'] = offset
                state['seeks'] += 1
                result = 0
            else:
                dest, width, count, handle = struct.unpack('<4I', uc.mem_read(sp+4, 16))
                self.assertEqual((dest, width, count, handle), (cells, BLOCK_BYTES, 1, 0x1234))
                data = self.data[state['position']:state['position']+width]
                self.assertEqual(len(data), width)
                uc.mem_write(dest, data)
                state['position'] += width
                state['reads'] += 1
                result = 1
            uc.reg_write(UC_X86_REG_EAX, result)
            uc.reg_write(UC_X86_REG_ESP, sp+4)
            uc.reg_write(UC_X86_REG_EIP, ret)

        vm.hook_add(UC_HOOK_CODE, service)
        poison = b'\xa5' * BLOCK_BYTES
        for index, expected in enumerate(parsed['blocks']):
            with self.subTest(index=index):
                vm.mem_write(cells, poison)
                self.call(vm, 0x40790, index % 9, index // 9, owner, this=target)
                self.assertEqual(vm.reg_read(UC_X86_REG_ESP), routes.SP+16)
                self.assertEqual(vm.reg_read(UC_X86_REG_EAX), int(expected is not None))
                self.assertEqual(bytes(vm.mem_read(cells, BLOCK_BYTES)), poison if expected is None else expected)
        self.assertEqual((state['reads'], state['seeks']), (66, 66))

    def test_native_town_streaming_neighborhood_gate(self):
        # 45AA0 calls 412E0 before replacing the 3x3 outdoor block window.
        parsed = parse_mbd(self.data)
        vm = self.vm()
        owner, table = routes.NET, routes.BODY
        vm.mem_write(owner+8, struct.pack('<III', 9, 9, table))
        vm.mem_write(table, self.data[16:340])
        accepted = []
        for y in range(9):
            for x in range(9):
                expected = all(
                    0 <= bx < 9 and 0 <= by < 9 and
                    parsed['blocks'][by*9+bx] is not None
                    for by in range(y-1, y+2) for bx in range(x-1, x+2))
                self.call(vm, 0x412e0, x, y, this=owner)
                self.assertEqual(vm.reg_read(UC_X86_REG_EAX), int(expected), (x, y))
                self.assertEqual(vm.reg_read(UC_X86_REG_ESP), routes.SP+12)
                if expected:
                    accepted.append((x, y))
        self.assertTrue(accepted)
        self.assertLess(len(accepted), 49)
        print('Native town 3x3 gate accepted centers:', accepted)

    def test_native_town_coordinate_center_selection(self):
        parsed = parse_mbd(self.data)
        vm = self.vm()
        owner, table, output = routes.NET, routes.BODY, routes.OUTPUT
        vm.mem_write(owner+8, struct.pack('<III', 9, 9, table))
        vm.mem_write(table, self.data[16:340])

        def available(x, y):
            return all(0 <= bx < 9 and 0 <= by < 9 and
                       parsed['blocks'][by*9+bx] is not None
                       for by in range(y-1, y+2) for bx in range(x-1, x+2))

        def select(x, y):
            cx, cy = int(x/21), int(y/21)
            if available(cx, cy):
                return cx, cy
            return next(((bx, by) for by in range(cy-1, cy+2)
                         for bx in range(cx-1, cx+2) if available(bx, by)), None)

        # Every legal town coordinate, plus signed division and block boundaries.
        coordinates = [(x, y) for y in range(189) for x in range(189)]
        edges = (-43, -42, -22, -21, -20, -1, 0, 20, 21, 188, 189, 210)
        coordinates.extend((x, y) for y in edges for x in edges)
        cpp = subprocess.check_output(
            [str(routes.ROOT/'build/tests/Release/recovered-town-navigation.exe'), '--centers'],
            input=''.join(f'{x} {y}\n' for x, y in coordinates), text=True, timeout=15).splitlines()
        self.assertEqual(len(cpp), len(coordinates))
        successes = 0
        for index, (x, y) in enumerate(coordinates):
            expected = select(x, y)
            self.assertEqual(cpp[index], 'none' if expected is None else f'{expected[0]} {expected[1]}')
            vm.mem_write(output, b'\xa5'*8)
            vm.reg_write(UC_X86_REG_ESP, routes.SP)
            vm.reg_write(UC_X86_REG_ECX, owner)
            vm.mem_write(routes.SP, struct.pack('<5I', routes.RETURN,
                         x & 0xffffffff, y & 0xffffffff, output, output+4))
            # Pure bounded loops: avoid a timer thread per coordinate, but keep
            # an instruction budget and require the actual native return.
            vm.emu_start(routes.BASE+0x41350, routes.RETURN, count=5000)
            self.assertEqual(vm.reg_read(UC_X86_REG_EIP), routes.RETURN)
            self.assertEqual(vm.reg_read(UC_X86_REG_EAX), int(expected is not None), (x, y))
            self.assertEqual(vm.reg_read(UC_X86_REG_ESP), routes.SP+20)
            actual = bytes(vm.mem_read(output, 8))
            self.assertEqual(actual, b'\xa5'*8 if expected is None else struct.pack('<ii', *expected), (x, y))
            successes += expected is not None
        print('Native center selections checked:', len(coordinates), 'successful:', successes)

    def test_import_bounds_reject_malformed_inputs(self):
        for length in (0, 7, 15, 16, 339, len(self.data)-1):
            with self.subTest(length=length), self.assertRaises(ValueError):
                parse_mbd(self.data[:length])
        for offset, value in ((8, 0), (8, 257), (12, 0), (16, 1),
                              (16, len(self.data)), (16, 341)):
            data = bytearray(self.data)
            struct.pack_into('<I', data, offset, value)
            with self.subTest(offset=offset, value=value), self.assertRaises(ValueError):
                parse_mbd(data)
        data = bytearray(self.data); data[7] = ord('3')
        with self.assertRaises(ValueError):
            parse_mbd(data)

    def test_all_town_neighborhoods_match_native_base_window(self):
        parsed = parse_mbd(self.data)
        vm = self.vm()
        manager, storage = 0x3800000, 0x3900000
        vm.mem_map(manager, 0x2000)
        vm.mem_map(storage, 9*0x2000)
        initial = bytes((i*37+11)&255 for i in range(63*63))
        for center_y in range(9):
            for center_x in range(9):
                blocks = []
                for dy in (-1,0,1):
                    for dx in (-1,0,1):
                        x,y = center_x+dx,center_y+dy
                        blocks.append(parsed['blocks'][y*9+x] if 0<=x<9 and 0<=y<9 else None)
                pointers = []
                for index,block in enumerate(blocks):
                    pointer = storage+index*0x2000
                    pointers.append(pointer if block is not None else 0)
                    if block is not None:
                        vm.mem_write(pointer+8,struct.pack('<II',pointer+0x100,21))
                        vm.mem_write(pointer+0x100,block)
                vm.mem_write(manager+0xfdc,struct.pack('<9I',*pointers))
                vm.mem_write(manager+0x50,initial)
                vm.reg_write(UC_X86_REG_ESP,routes.SP)
                vm.reg_write(UC_X86_REG_ECX,manager)
                self.run_to(vm,0x47440,0x474e6)
                self.assertEqual(bytes(vm.mem_read(manager+0x50,63*63)),
                                 project_base_window(blocks,initial),(center_x,center_y))

    def test_island01_city_approach_matches_native_base_window(self):
        # The next monster-bearing scene has an independently pinned block file.
        path=routes.ROOT.parent/'God2/Data2/map/island01/island01.mbd'
        source=path.read_bytes()
        self.assertEqual(hashlib.sha256(source).hexdigest(),
                         'b574654e5859e048ea0047c0de36b70addc5e90f2349b9796016ea6792f75f80')
        parsed=parse_mbd(source)
        self.assertEqual((parsed['width'],parsed['height']),(35,37))
        vm=self.vm()
        manager,storage=0x3800000,0x3900000
        vm.mem_map(manager,0x2000)
        vm.mem_map(storage,9*0x2000)
        initial=bytes([255])*3969
        for center_y in range(8,11):
            for center_x in range(21,24):
                blocks=[]
                for dy in (-1,0,1):
                    for dx in (-1,0,1):
                        x,y=center_x+dx,center_y+dy
                        blocks.append(parsed['blocks'][y*35+x])
                pointers=[]
                for index,block in enumerate(blocks):
                    pointer=storage+index*0x2000
                    pointers.append(pointer if block is not None else 0)
                    if block is not None:
                        vm.mem_write(pointer+8,struct.pack('<II',pointer+0x100,21))
                        vm.mem_write(pointer+0x100,block)
                vm.mem_write(manager+0xfdc,struct.pack('<9I',*pointers))
                vm.mem_write(manager+0x50,initial)
                vm.reg_write(UC_X86_REG_ESP,routes.SP)
                vm.reg_write(UC_X86_REG_ECX,manager)
                self.run_to(vm,0x47440,0x474e6)
                self.assertEqual(bytes(vm.mem_read(manager+0x50,3969)),
                                 project_base_window(blocks,initial),(center_x,center_y))

    def test_window_bit_isolation_and_import_bounds(self):
        vm = self.vm()
        manager, slot, cells = 0x3800000, routes.NET, routes.BODY
        vm.mem_map(manager,0x2000)
        block = bytearray(BLOCK_BYTES)
        for index in range(441):
            block[index*8:index*8+8] = bytes([255]*7+[index&255])
        vm.mem_write(slot+8,struct.pack('<II',cells,21))
        vm.mem_write(cells,bytes(block))
        vm.mem_write(manager+0xfdc+4*4,struct.pack('<I',slot))
        vm.mem_write(manager+0x50,b'\xa5'*(63*63))
        vm.reg_write(UC_X86_REG_ESP,routes.SP)
        vm.reg_write(UC_X86_REG_ECX,manager)
        self.run_to(vm,0x47440,0x474e6)
        expected=project_base_window([None]*4+[block]+[None]*4,b'\xa5'*(63*63))
        self.assertEqual(bytes(vm.mem_read(manager+0x50,63*63)),expected)
        vm.mem_write(manager+0x103c,struct.pack('<II',105,105))
        for x,y in ((84,84),(105,105),(125,125),(146,146),(83,105),(147,105),(105,83),(105,147)):
            self.call(vm,0x46ff0,x,y,this=manager)
            local_x,local_y=x-105+21,y-105+21
            value=expected[local_y*63+local_x] if 0<=local_x<63 and 0<=local_y<63 else 0
            self.assertEqual(vm.reg_read(UC_X86_REG_EAX),value)
        for blocks,initial in (([],bytes(3969)),([None]*9,b''),([b'bad']+[None]*8,bytes(3969))):
            with self.assertRaises(ValueError):
                project_base_window(blocks,initial)

    def test_complete_native_builder_with_model_pass_overlays(self):
        manager, terrain, storage = 0x3800000, 0x3900000, 0x3a00000
        for positions in (((84,84),), ((62,62),), ((125,125),),
                          ((63,84),(84,63),(84,84)), ((84,84),(84,84))):
            with self.subTest(positions=positions):
                vm = self.vm()
                vm.mem_map(0,4096)
                vm.mem_map(manager,0x2000)
                vm.mem_map(terrain,0x3000)
                vm.mem_map(storage,0x20000)
                slot,block,table,empty,header = storage,storage+0x100,storage+0x1000,storage+0x1200,storage+0x1300
                vm.mem_write(slot+8,struct.pack('<II',block,21))
                vm.mem_write(slot+0x64,struct.pack('<II',4,4))
                vm.mem_write(block,bytes([0,0,0,0,0,0,0,64])*441)
                vm.mem_write(manager+0xfdc,struct.pack('<9I',*([slot]*9)))
                vm.mem_write(manager+0x1024,struct.pack('<I',terrain))
                vm.mem_write(terrain+0x1464,struct.pack('<III',table,9,9))
                entries=[empty]*81;entries[4*9+4]=header
                vm.mem_write(table,struct.pack('<81I',*entries))
                vm.mem_write(header+8,struct.pack('<I',storage+0x2000))
                expected=bytes([1])*(63*63)
                for index,(x,y) in enumerate(positions):
                    node=storage+0x2000+index*0x2000
                    model=node+0x100
                    frame=index%2
                    width,height=5,7
                    cells=bytes((0,1,2,255)[(i+index)%4] for i in range(width*height))
                    vm.mem_write(node+4,struct.pack('<I',node+0x2000 if index+1<len(positions) else 0))
                    vm.mem_write(node+0x14,struct.pack('<ii',x,y))
                    vm.mem_write(node+0x2c,struct.pack('<II',model,frame))
                    vm.mem_write(model+0x2c,struct.pack('<iiii',-1,-1,-1,-1))
                    vm.mem_write(model+0x4c+frame*36,struct.pack('<III',model+0x500,width,height))
                    vm.mem_write(model+0x500,cells)
                    expected=apply_model_pass(expected,x-4*21+21,y-4*21+21,width,height,cells)
                self.call(vm,0x47440,this=manager)
                self.assertEqual(vm.reg_read(UC_X86_REG_ESP),routes.SP+4)
                self.assertEqual(bytes(vm.mem_read(manager+0x50,63*63)),expected)
                self.assertEqual(struct.unpack('<I',vm.mem_read(manager+0x10,4))[0],1)

    def test_model_pass_input_bounds(self):
        base=bytes([1])*3969
        for args in ((b'',0,0,1,1,b'\0'),(base,0,0,0,1,b''),
                     (base,0,0,1,513,bytes(513)),(base,0,0,2,2,b'\0'),
                     (base,32768,0,1,1,b'\0')):
            with self.assertRaises(ValueError):
                apply_model_pass(*args)

    def test_special_points_bounds_and_clipping(self):
        base=bytes(3969)
        result=apply_model_points(base,0,0,((2,3),(-1,0)))
        self.assertEqual(result[4*63+1],2)
        self.assertEqual(result.count(2),1)
        self.assertEqual(apply_model_points(base,62,62,((2,3),(-1,0))),base)
        for args in ((b'',0,0,((0,0),(0,0))), (base,0,0,()),
                     (base,0,0,((32768,0),(0,0)))):
            with self.assertRaises(ValueError):
                apply_model_points(*args)

    def test_native_manager_constructor_preserves_window_bytes(self):
        vm=self.vm()
        vm.mem_map(0,4096)
        manager=0x3800000
        vm.mem_map(manager,0x2000)
        poison=bytes((i*17+3)&255 for i in range(3969))
        vm.mem_write(manager+0x50,poison)
        self.call(vm,0x42a60,this=manager)
        self.assertEqual(vm.reg_read(UC_X86_REG_EAX),manager)
        self.assertEqual(vm.reg_read(UC_X86_REG_ESP),routes.SP+4)
        self.assertEqual(bytes(vm.mem_read(manager+0x50,3969)),poison)
        self.assertEqual(bytes(vm.mem_read(manager+0xfdc,36)),bytes(36))
        self.assertEqual(struct.unpack('<ii',vm.mem_read(manager+0x103c,8)),(-21,-21))


if __name__ == '__main__':
    unittest.main()
