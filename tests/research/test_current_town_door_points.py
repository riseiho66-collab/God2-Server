"""Current native 49BB0 execution for every recovered town/parent point."""
import hashlib
import json
from pathlib import Path
import struct
import unittest
import pefile
from unicorn.x86_const import UC_X86_REG_EIP, UC_X86_REG_EAX
import test_current_route_advertisement as routes
from tools.strike_lab.current_monster_binary_producer import parse_mdl
from tools.strike_lab.current_town_doors_20260927 import project, pairs
from tools.strike_lab.indoor_navigation import parse_hmd, navigation_inputs
from tools.strike_lab.omega_assets import decode_csvz
from tools.strike_lab.world_scenes import build_scenes


class AllDoorPointTests(unittest.TestCase):
    vm=routes.CurrentRouteAdvertisementTests.vm
    call=routes.CurrentRouteAdvertisementTests.call
    run_to=routes.CurrentRouteAdvertisementTests.run_to

    @classmethod
    def setUpClass(cls):
        cls.image=(routes.ROOT/'artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin').read_bytes()
        if hashlib.sha256(cls.image).hexdigest()!=routes.IMAGE_SHA:
            raise AssertionError('Pinned original image changed')

    def native(self, vm, point):
        vm.mem_write(routes.OUTPUT,b'\xa5'*8)
        self.call(vm,0x49bb0,*point,routes.OUTPUT,routes.OUTPUT+4)
        self.assertEqual(vm.reg_read(UC_X86_REG_EIP),routes.RETURN)
        result=list(struct.unpack('<ii',vm.mem_read(routes.OUTPUT,8)))
        self.assertEqual(result,project(*point))
        return result

    def test_current_executable_projection_matches_pinned_native(self):
        exe=routes.ROOT.parent/'God2/God2.exe'
        raw=exe.read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(),'6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98')
        pe=pefile.PE(data=raw,fast_load=True)
        # Full source point projection through its original return.
        offset=pe.get_offset_from_rva(0x49bb0)
        self.assertEqual(raw[offset:offset+0x55],self.image[0x49bb0:0x49c05])

    def test_all_model_and_room_pairs_execute_original_projection(self):
        root=routes.ROOT.parent/'God2'
        scenes={s['scene']:s for s in build_scenes(root)['scenes'] if s['area']==2}
        vm=self.vm()
        checked=0
        for asset in ['Data2/map/island01/CityI1/cityI1.mdlZ','Data2/map/island01/Island01.mdlZ']:
            mdl=parse_mdl(decode_csvz((root/asset).read_bytes()),allow_parent_rom=True)
            for placement in mdl['placements']:
                if not placement['attached_reference']:continue
                # Only the same source reference scope used by the server bundle.
                ref=placement['attached_reference'].lower()
                if asset.endswith('Island01.mdlZ') and 'cityi1' not in ref:continue
                for i in range(0,8,2):
                    point=mdl['models'][placement['fields'][0]]['extra_8_ints'][i:i+2]
                    if point[0]>=0:
                        self.native(vm,point);checked+=1
        bundle=json.loads((routes.ROOT/'artifacts/world-atlas/town-doors-2.json').read_text())
        for route in bundle['routes']:
            row=scenes[route['scene']]
            variant=row['asset_variants'][0]
            raw=(root/variant['path']).read_bytes()
            decoded=decode_csvz(raw) if variant['path'].lower().endswith('z') else raw
            room=parse_hmd(decoded)
            base,_=navigation_inputs(room)
            side=2*max(base['width'],(base['height']+1)//2)+1
            anchor=side-1-base['width']+(base['width']&1)
            fields=room['models'][room['placements'][0]['model']]['portal_fields']
            expected=pairs(fields,[anchor,0])
            for i in range(0,8,2):
                if fields[i]>=0:
                    native=self.native(vm,fields[i:i+2]);checked+=1
                    self.assertEqual(expected[i//2],[anchor+native[0],native[1]])
            for pair in route['pairs']:
                self.assertIn(pair['indoor_arrival'],expected[:2])
                self.assertIn(pair['indoor_trigger'],expected[2:])
        self.assertGreaterEqual(checked,200)

    def test_scene7_original_window_getter_and_boolean_straight_path(self):
        # Full original46FF0 getter and102BF0 straight path builder, without
        # stubs. Both bytes1 and2 pass the actual TEST EAX/EAX cell consumer;
        # zero truncates the path. A* and arbitrary streaming remain separate.
        vm=self.vm();world=0x3800000;manager=0x3900000;owner=0x3a00000
        vm.mem_map(world,0x4000);vm.mem_map(manager,0x2000);vm.mem_map(owner,0x1000)
        pointer_site=world+0xa7e05dc
        vm.mem_map(pointer_site&~4095,4096)
        vm.mem_write(pointer_site,struct.pack('<I',owner))
        vm.mem_write(owner+0xbc,struct.pack('<I',manager))
        vm.mem_write(manager+0x30,struct.pack('<I',0))
        vm.mem_write(manager+0xfdc+4*4,struct.pack('<I',owner))
        vm.mem_write(manager+0x103c,struct.pack('<II',63,42))
        index=(46-42+21)*63+(82-63+21)
        for value,count in [(0,1),(1,2),(2,2)]:
            vm.mem_write(manager+0x50,b'\x01'*(63*63))
            vm.mem_write(manager+0x50+index,bytes([value]))
            self.call(vm,0x46ff0,82,46,this=manager)
            self.assertEqual(vm.reg_read(UC_X86_REG_EAX),value)
            vm.mem_write(world+0x38,bytes(4))
            self.call(vm,0x102bf0,81,46,82,46,this=world)
            self.assertEqual(struct.unpack('<I',vm.mem_read(world+0x38,4))[0],count)
            self.assertEqual(struct.unpack('<2I',vm.mem_read(world+0x3c,8)),(81,46))
            if value:self.assertEqual(struct.unpack('<2I',vm.mem_read(world+0x44,8)),(82,46))
        atlas=json.loads((routes.ROOT/'artifacts/world-atlas/town-2-4.json').read_text())
        values=[]
        for window in atlas['windows']:
            x,y=82-window['origin_x'],46-window['origin_y']
            if not 0<=x<63 or not 0<=y<63:continue
            values.append(int(window['cells_hex'][2*(y*63+x):2*(y*63+x)+2],16))
        self.assertEqual(set(values),{1,2})
        self.assertTrue(all(values))
        # Actual coordinate-center selector picks3,2 for the exact one-step
        # source81,46 and target82,46. Other covering windows are observations,
        # not proof that those windows are selected for this step.
        data=(routes.ROOT.parent/'God2/Data2/map/island01/CityI1/cityi1.mbd').read_bytes()
        vm.mem_write(routes.NET+8,struct.pack('<III',9,9,routes.BODY))
        vm.mem_write(routes.BODY,data[16:340])
        for x,y in [(81,45),(81,46),(81,47),(82,45),(82,46),(82,47)]:
            self.call(vm,0x41350,x,y,routes.OUTPUT,routes.OUTPUT+4,this=routes.NET)
            self.assertEqual(vm.reg_read(UC_X86_REG_EAX),1)
            self.assertEqual(struct.unpack('<2i',vm.mem_read(routes.OUTPUT,8)),(3,2))

    def test_kunlun_boolean_trigger_native_getter_and_straight_path(self):
        vm=self.vm();world=0x3800000;manager=0x3900000;owner=0x3a00000
        vm.mem_map(world,0x4000);vm.mem_map(manager,0x2000);vm.mem_map(owner,0x1000)
        pointer_site=world+0xa7e05dc;vm.mem_map(pointer_site&~4095,4096)
        vm.mem_write(pointer_site,struct.pack('<I',owner));vm.mem_write(owner+0xbc,struct.pack('<I',manager))
        vm.mem_write(manager+0x30,bytes(4));vm.mem_write(manager+0xfdc+16,struct.pack('<I',owner))
        atlas=json.loads((routes.ROOT/'artifacts/world-atlas/kunlun-4-3.json').read_text())
        report=json.loads((routes.ROOT/'artifacts/world-atlas/kunlun-doors-4.json').read_text())
        tested=0
        for row in report['routes']:
            for pair in row['pairs']:
                x,y=pair['town_trigger'];ax,ay=pair['town_arrival']
                observed=[]
                for i,w in enumerate(atlas['windows']):
                    lx,ly=x-w['origin_x'],y-w['origin_y']
                    if atlas['block_present'][i] and 0<=lx<63 and 0<=ly<63:
                        observed.append(int(w['cells_hex'][2*(ly*63+lx):2*(ly*63+lx)+2],16))
                self.assertTrue(observed and all(value in (1,2) for value in observed))
                # Same original area-independent getter and straight path,
                # preserving actual one-step trigger/arrival coordinates.
                ox,oy=x//21*21,y//21*21
                vm.mem_write(manager+0x103c,struct.pack('<II',ox,oy))
                index=(y-oy+21)*63+x-ox+21
                for value in set(observed):
                    vm.mem_write(manager+0x50,b'\x01'*(63*63));vm.mem_write(manager+0x50+index,bytes([value]))
                    self.call(vm,0x46ff0,x,y,this=manager);self.assertEqual(vm.reg_read(UC_X86_REG_EAX),value)
                    vm.mem_write(world+0x38,bytes(4));self.call(vm,0x102bf0,ax,ay,x,y,this=world)
                    self.assertEqual(struct.unpack('<I',vm.mem_read(world+0x38,4))[0],2)
                    self.assertEqual(struct.unpack('<2I',vm.mem_read(world+0x44,8)),(x,y))
                tested+=1
        self.assertEqual(tested,12)


if __name__=='__main__':unittest.main()
