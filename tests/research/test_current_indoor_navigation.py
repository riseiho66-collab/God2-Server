"""HMD navigation -> original parser/diamond grid -> C++ byte-for-byte oracle."""
import hashlib
import random
import struct
import subprocess
import sys
import unittest

import test_current_route_advertisement as routes
sys.path.insert(0,str(routes.ROOT))
from tools.strike_lab.indoor_navigation import parse_hmd, navigation_inputs, dump_input, compile_navigation
from tools.strike_lab.omega_assets import decode_csvz
from tools.strike_lab.current_monster_binary_producer import parse_mdl
from tools.strike_lab.world_scenes import parse_can
from tools.strike_lab.town_navigation import MDL_SHA, MDL_DECODED_SHA
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_EBP, UC_X86_REG_EBX
from unicorn.x86_const import UC_X86_REG_ECX, UC_X86_REG_ESI, UC_X86_REG_ESP, UC_X86_REG_EIP
from unicorn.x86_const import UC_X86_REG_EDI

MODELS, INDOOR, HEAP = 0x3800000, 0x3900000, 0x3d00000


class CurrentIndoorNavigationTests(unittest.TestCase):
    vm = routes.CurrentRouteAdvertisementTests.vm
    call = routes.CurrentRouteAdvertisementTests.call
    run_to = routes.CurrentRouteAdvertisementTests.run_to

    @classmethod
    def setUpClass(cls):
        cls.image = (routes.ROOT/'artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin').read_bytes()
        if hashlib.sha256(cls.image).hexdigest() != routes.IMAGE_SHA:
            raise AssertionError('Current mapped image changed')
        raw = (routes.ROOT.parent/'God2/Data2/map/island01/indoor/groceryL.hmdZ').read_bytes()
        if hashlib.sha256(raw).hexdigest() != '42d769c0ff328db3e1e295e17208d0db7a0ff12608976f952dae800ff79c3c00':
            raise AssertionError('Current initial indoor resource changed')
        cls.decoded = decode_csvz(raw)
        cls.asset = parse_hmd(cls.decoded)
        cls.binary = routes.ROOT/'build/tests/Release/recovered-indoor-grid.exe'

    def prepared(self):
        vm = self.vm()
        vm.mem_map(0,4096)
        vm.mem_map(MODELS,0x100000)
        vm.mem_map(INDOOR,0x2a3000)
        vm.mem_map(HEAP,0x200000)
        vm.mem_write(routes.BODY,b'v1.6\0')
        state = {'heap':HEAP,'tokens':[],'token':0,'assertions':0}

        def text(pointer):
            return bytes(vm.mem_read(pointer,100)).split(b'\0',1)[0]

        def service(uc,address,size,_):
            rva = address-routes.BASE
            if rva not in (0x15b406,0x15b42f,0x1490ad,0x149a00,0x151de0,
                           0x15ad35,0x4c6f0,0x2c70):
                return
            sp = uc.reg_read(UC_X86_REG_ESP)
            ret = struct.unpack('<I',uc.mem_read(sp,4))[0]
            def arg(index):return struct.unpack('<I',uc.mem_read(sp+4+4*index,4))[0]
            result,cleanup = 0,0
            if rva == 0x15b406:
                length = arg(0)
                self.assertTrue(0 < length < 1024*1024)
                result = state['heap'];state['heap'] += (length+31)&~15
                self.assertLess(state['heap'],HEAP+0x200000)
                uc.mem_write(result,bytes(length)+b'\xa5'*16)
            elif rva == 0x1490ad:
                self.assertEqual(arg(0),0x1234)
                formats = text(arg(1)).split()
                for index,fmt in enumerate(formats):
                    self.assertLess(state['token'],len(state['tokens']))
                    token = state['tokens'][state['token']];state['token'] += 1
                    if fmt == b'%d':uc.mem_write(arg(index+2),struct.pack('<i',int(token)))
                    elif fmt == b'%s':uc.mem_write(arg(index+2),token.encode()+b'\0')
                    else:self.fail('Unsupported native fscanf format '+repr(fmt))
                result = len(formats)
            elif rva in (0x149a00,0x151de0):
                left,right = text(arg(0)),text(arg(1))
                if rva == 0x151de0:
                    left,right = left.lower(),right.lower()
                result = ((left>right)-(left<right))&0xffffffff
            elif rva == 0x4c6f0:
                self.assertLess(arg(0),len(self.asset['models']))
                result,cleanup = MODELS+arg(0)*0x1000,4
            elif rva == 0x2c70:
                state['assertions'] += 1
                self.fail('Native grid assertion reached')
            uc.reg_write(UC_X86_REG_EAX,result)
            uc.reg_write(UC_X86_REG_ESP,sp+4+cleanup)
            uc.reg_write(UC_X86_REG_EIP,ret)
        vm.hook_add(UC_HOOK_CODE,service)
        return vm,state

    def test_native_model_connection_pairs_and_duplicate_guard(self):
        vm=self.native_asset()
        self.assertEqual(self.asset['models'][0]['portal_fields'],[-1,-1,7,23,-1,-1,8,24])
        self.assertEqual(self.asset['models'][1]['portal_fields'],[-1]*8)
        before=bytes(vm.mem_read(MODELS+0x2c,32))
        # Native setter refuses an existing non-sentinel pair, without mutation.
        self.call(vm,0x41df0,0,7,23,this=MODELS)
        self.assertEqual(vm.reg_read(UC_X86_REG_EAX),0)
        self.assertEqual(bytes(vm.mem_read(MODELS+0x2c,32)),before)
        # A first coordinate of -1 follows the explicit disabled-pair branch.
        self.call(vm,0x41df0,0,0xffffffff,123,this=MODELS)
        self.assertEqual(vm.reg_read(UC_X86_REG_EAX),1)
        self.assertEqual(struct.unpack('<2i',vm.mem_read(MODELS+0x2c,8)),(-1,123))
        self.assertEqual(bytes(vm.mem_read(MODELS+0x34,24)),before[8:])

    def test_original_connection_pair_projection_into_indoor_grid(self):
        vm=self.native_asset()
        self.assertEqual(struct.unpack('<2i',vm.mem_read(INDOOR+0x18,8)),(20,0))
        for index,expected in ((1,(16,19)),(3,(16,20))):
            self.call(vm,0x36f30,routes.BODY+0x700,index,this=INDOOR)
            self.assertEqual(struct.unpack('<2i',vm.mem_read(routes.BODY+0x700,8)),expected)
        # Original36F30 calls49BB0 and adds the loaded placement anchor.
        # This proves grid projection, not doorway activation or destination.

    def test_original_indoor_exit_classifier_requires_kind_and_out_pairs(self):
        vm=self.native_asset()
        manager=MODELS+0x10000
        output=routes.BODY+0x700
        vm.mem_write(manager+0x1030,struct.pack('<I',INDOOR))
        vm.mem_write(manager+0x30,struct.pack('<I',2))
        # Original49250 checks only model pairs2/3, not the entry pair1.
        for rva in (0x49250,0x49000):
            for x,y,accepted,kind in ((16,19,0,99),(16,20,1,3),(15,20,0,99),(18,12,0,99)):
                vm.mem_write(output,struct.pack('<I',99))
                self.call(vm,rva,x,y,output,this=manager)
                self.assertEqual(vm.reg_read(UC_X86_REG_EAX),accepted)
                self.assertEqual(struct.unpack('<I',vm.mem_read(output,4))[0],kind)
        for field,value in ((0x30,0),(0x1030,0)):
            vm.mem_write(manager+field,struct.pack('<I',value))
            vm.mem_write(output,struct.pack('<I',99))
            self.call(vm,0x49250,16,20,output,this=manager)
            self.assertEqual(vm.reg_read(UC_X86_REG_EAX),0)
            self.assertEqual(struct.unpack('<I',vm.mem_read(output,4))[0],99)
            vm.mem_write(manager+0x30,struct.pack('<I',2))
            vm.mem_write(manager+0x1030,struct.pack('<I',INDOOR))

    def test_original_exit_classifier_entire_current_indoor_grid(self):
        vm=self.native_asset()
        manager=MODELS+0x10000
        output=routes.BODY+0x700
        vm.mem_write(manager+0x1030,struct.pack('<I',INDOOR))
        vm.mem_write(manager+0x30,struct.pack('<I',2))
        side,cells=self.output(vm)
        matches=[]
        for y in range(side):
            for x in range(side):
                vm.mem_write(output,struct.pack('<I',99))
                self.call(vm,0x49250,x,y,output,this=manager)
                accepted=vm.reg_read(UC_X86_REG_EAX)
                kind=struct.unpack('<I',vm.mem_read(output,4))[0]
                self.assertIn(accepted,(0,1))
                if accepted:
                    matches.append((x,y,kind))
                    self.assertEqual(cells[y*side+x],1)
                else:self.assertEqual(kind,99)
        self.assertEqual(matches,[(16,20,3)])

    def test_original_screen_exit_query_uses_camera_translation(self):
        vm=self.native_asset()
        manager,bridge=MODELS+0x10000,MODELS+0x20000
        out=routes.BODY+0x700
        vm.mem_write(manager+0x30,struct.pack('<I',2))
        vm.mem_write(manager+0x1030,struct.pack('<I',INDOOR))
        vm.mem_write(bridge+0xbc,struct.pack('<I',manager))
        for camera in ((0,0),(120,80),(-40,16)):
            vm.mem_write(INDOOR+0x6c,struct.pack('<2i',*camera))
            for x,y,expected in ((16,20,1),(16,19,0),(15,20,0),(18,12,0)):
                self.call(vm,0x49330,x,y,out,out+4,this=manager)
                px,py=struct.unpack('<2i',vm.mem_read(out,8))
                #49330 returns a tile boundary; sample40 right/20 below and
                # verify the original inverse before querying the bridge.
                px+=40;py+=20
                self.call(vm,0x493c0,px,py,out,out+4,this=manager)
                self.assertEqual(struct.unpack('<2i',vm.mem_read(out,8)),(x,y))
                # Feed original projected pixels minus camera into original
                # bridge34210 ->49450 ->49000 ->49250, without replacing code.
                self.call(vm,0x34210,(px-camera[0])&0xffffffff,
                          (py-camera[1])&0xffffffff,this=bridge)
                self.assertEqual(vm.reg_read(UC_X86_REG_EAX),expected)
        vm.mem_write(bridge+0xbc,bytes(4))
        self.call(vm,0x34210,0,0,this=bridge)
        self.assertEqual(vm.reg_read(UC_X86_REG_EAX),0)

    def test_current_town_explicit_grocery_reference_and_native_coordinates(self):
        client=routes.ROOT.parent/'God2/Data2/map/island01'
        raw=(client/'CityI1/cityI1.mdlZ').read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(),MDL_SHA)
        decoded=decode_csvz(raw)
        self.assertEqual(hashlib.sha256(decoded).hexdigest(),MDL_DECODED_SHA)
        mdl=parse_mdl(decoded,allow_parent_rom=True)
        matches=[(i,p) for i,p in enumerate(mdl['placements'])
                 if p['attached_reference'] and p['attached_reference'].lower()=='..\\indoor\\groceryl.hmd']
        self.assertEqual([i for i,_ in matches],[80])
        placement=matches[0][1]
        self.assertEqual(placement['fields'],[68,880,680,88,60,0,-1,-1,1,0])
        self.assertEqual(placement['sha256'],'c32b73ebf69f70817e16c7907d97deff921287c46a54b69cf82566082fbd5dd5')
        pairs=mdl['models'][68]['extra_8_ints']
        self.assertEqual(pairs,[-1,-1,4,12,-1,-1,4,13])
        vm=self.native_asset()
        model,obj=MODELS+0x40000,MODELS+0x50000
        vm.mem_write(model+0x2c,b'\xff'*32)
        for i in range(4):
            self.call(vm,0x41df0,i,*(v&0xffffffff for v in pairs[i*2:i*2+2]),this=model)
        vm.mem_write(obj+0x14,struct.pack('<2i',*placement['fields'][3:5]))
        for index,expected in ((1,(86,70)),(3,(86,71))):
            vm.reg_write(UC_X86_REG_ESP,routes.SP)
            vm.reg_write(UC_X86_REG_EDI,obj)
            vm.reg_write(UC_X86_REG_EBP,model)
            vm.reg_write(UC_X86_REG_EBX,index)
            vm.mem_write(routes.SP+0x3c,struct.pack('<i',pairs[index*2+1]))
            vm.mem_write(routes.SP+0x4c,struct.pack('<2I',routes.BODY+0x700,routes.BODY+0x704))
            # Original model-coordinate projection slice; stop before unrelated
            # loader completion. This does not execute a scene transition.
            self.run_to(vm,0x48d4f,0x48d91)
            self.assertEqual(struct.unpack('<2i',vm.mem_read(routes.BODY+0x700,8)),expected)
        can_raw=(client/'Island01.can').read_bytes()
        self.assertEqual(hashlib.sha256(can_raw).hexdigest(),'f2b9ca9dc4dcebcd1c1c40de14ea63f1b2061993f644c49b9c7baca9ce2d2f97')
        can=parse_can(can_raw)
        self.assertEqual(can['files'][12]['asset_path'],'indoor/groceryl.hmd')
        self.assertEqual([i for i,v in enumerate(can['scene_file_indices']) if v==12],[15,50,53,65,73,90])

    def native_asset(self):
        vm,state = self.prepared()
        for index,model in enumerate(self.asset['models']):
            address = MODELS+index*0x1000
            # Rendering-resource references are absent. Only Pass/frame fields
            # execute here, from the v1.6-specific frame-count parser onward.
            vm.mem_write(address+8,struct.pack('<I',routes.BODY+0x800))
            state['tokens'],state['token'] = model['navigation_tokens'],0
            vm.reg_write(UC_X86_REG_ESI,address)
            vm.reg_write(UC_X86_REG_EBP,0x1234)
            vm.reg_write(UC_X86_REG_EBX,len(model['grids']))
            vm.reg_write(UC_X86_REG_ESP,routes.SP)
            vm.mem_write(routes.SP+0x170,struct.pack('<II',0x1234,routes.BODY))
            self.run_to(vm,0x4cb26,0x4ce2b)
            self.assertEqual(state['token'],len(state['tokens']))
            self.assertEqual(struct.unpack('<8i',vm.mem_read(address+0x2c,32)),
                             tuple(model['portal_fields']))
            for frame,grid in enumerate(model['grids']):
                pointer,w,h = struct.unpack('<III',vm.mem_read(address+0x4c+frame*36,12))
                self.assertEqual((w,h),(grid['width'],grid['height']))
                self.assertEqual(bytes(vm.mem_read(pointer,w*h)),bytes(grid['cells']))
        state['tokens'],state['token'] = self.asset['model_tokens'],0
        self.call(vm,0x37250,0x1234,routes.BODY,this=INDOOR)
        self.assertEqual(vm.reg_read(UC_X86_REG_EAX),1)
        self.assertEqual(state['token'],len(state['tokens']))
        self.call(vm,0x36c30,this=INDOOR)
        return vm

    def output(self,vm):
        pointer,w,h = struct.unpack('<III',vm.mem_read(INDOOR+0x8c,12))
        self.assertEqual(w,h)
        self.assertEqual(bytes(vm.mem_read(pointer+w*h,16)),b'\xa5'*16)
        return w,bytes(vm.mem_read(pointer,w*h))

    def cpp(self,base,overlays):
        output = subprocess.check_output([str(self.binary),'--dump'],
            input=dump_input(base,overlays),text=True,timeout=5).split()
        return int(output[0]),bytes.fromhex(output[1])

    def test_current_hmd_original_parsers_and_collision_builder(self):
        vm = self.native_asset()
        side,cells = self.output(vm)
        self.assertEqual(side,31)
        base,overlays = navigation_inputs(self.asset)
        self.assertEqual((base['width'],base['height']),(10,30))
        self.assertEqual([(p['x'],p['y']) for p in overlays],[(2,8)])
        self.assertEqual(self.cpp(base,overlays),(side,cells))
        for x,y in ((17,13),(0,0),(-1,3),(31,0),(0,31)):
            self.call(vm,0x36b60,x&0xffffffff,y&0xffffffff,this=INDOOR)
            expected = cells[y*side+x] if 0<=x<side and 0<=y<side else 0
            self.assertEqual(vm.reg_read(UC_X86_REG_EAX)&255,expected)

    def test_cpp_matches_original_for_row_parities_and_raw_bytes(self):
        rng = random.Random(1926)
        for width,height in ((1,1),(2,3),(3,2),(4,8),(9,15),(10,30),(11,31)):
            base = {'width':width,'height':height,'cells':[rng.randrange(256) for _ in range(width*height)]}
            vm,state = self.prepared()
            vm.mem_write(MODELS+0x4c,struct.pack('<III',HEAP,width,height))
            vm.mem_write(HEAP,bytes(base['cells']))
            state['heap'] = HEAP+0x1000
            vm.mem_write(INDOOR+0x30,struct.pack('<I',MODELS))
            self.call(vm,0x36c30,this=INDOOR)
            self.assertEqual(self.cpp(base,[]),self.output(vm))

    def test_malformed_hmd_is_rejected_before_native_execution(self):
        for bad in (b'',self.decoded.replace(b'v1.6',b'v1.5',1),
                    self.decoded.replace(b'10 30',b'0 30',1),
                    self.decoded.replace(b'10 30',b'513 30',1),
                    self.decoded.replace(b'10 30',b'1_0 30',1),
                    self.decoded.replace(b'Pass',b'Fail',1),self.decoded+b'Unknown 1\n',
                    self.decoded[:self.decoded.index(b'Pass')],self.decoded+b'\0'):
            with self.subTest(bad=bad[:40]),self.assertRaises(ValueError):parse_hmd(bad)

    def test_cpp_overlay_rules_match_original_signed_coordinate_math(self):
        rng = random.Random(3630)
        base = {'width':4,'height':6,'cells':[rng.randrange(1,256) for _ in range(24)]}
        for positions in (((0,-1),),((0,-2),),((1,-3),),((-1,2),),((0,0),(1,0),(0,0))):
            overlays = [{'x':x,'y':y,'grid':{'width':1,'height':2,'cells':[0,173]}}
                        for x,y in positions]
            vm,state = self.prepared()
            def pass_model(index,grid):
                model = MODELS+index*0x1000
                pointer = HEAP+index*0x1000
                vm.mem_write(model+0x4c,struct.pack('<III',pointer,grid['width'],grid['height']))
                vm.mem_write(pointer,bytes(grid['cells']))
                return model
            vm.mem_write(INDOOR+0x30,struct.pack('<I',pass_model(0,base)))
            for index,overlay in enumerate(overlays):
                node = MODELS+0x80000+index*0x100
                model = pass_model(index+1,overlay['grid'])
                vm.mem_write(node+4,struct.pack('<I',node+0x100 if index+1<len(overlays) else 0))
                vm.mem_write(node+0x14,struct.pack('<ii',overlay['x'],overlay['y']))
                vm.mem_write(node+0x2c,struct.pack('<II',model,0))
            vm.mem_write(INDOOR+0x5c,struct.pack('<I',MODELS+0x80000))
            state['heap'] = HEAP+0x10000
            self.call(vm,0x36c30,this=INDOOR)
            self.assertEqual(self.cpp(base,overlays),self.output(vm))

    def test_scene_compiler_preserves_provenance_and_native_grid(self):
        output = compile_navigation(routes.ROOT.parent/'God2',2,15,self.binary)
        side,cells = self.output(self.native_asset())
        self.assertEqual(output['grid']['side'],side)
        self.assertEqual(bytes.fromhex(output['grid']['cells_hex']),cells)
        self.assertEqual(output['grid']['sha256'],hashlib.sha256(cells).hexdigest())
        self.assertEqual(output['grid']['nonzero_cells'],101)
        self.assertFalse(output['server_loaded'])
        self.assertFalse(output['runtime_validated'])
        self.assertEqual(output,compile_navigation(routes.ROOT.parent/'God2',2,15,self.binary))
        with self.assertRaises(ValueError):
            compile_navigation(routes.ROOT.parent/'God2',2,0,self.binary)


if __name__ == '__main__':unittest.main()
