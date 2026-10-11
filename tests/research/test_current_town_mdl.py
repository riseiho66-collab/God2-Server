"""Actual town MDL Pass bytes through current native parser, no rendering."""
import hashlib
import json
import struct
import subprocess
import unittest

import test_current_indoor_navigation as indoor
from tools.strike_lab.current_monster_binary_producer import parse_mdl, native_mdl_placement
from tools.strike_lab.omega_assets import decode_csvz
from tools.strike_lab.outdoor_mbd import parse_mbd, project_base_window, apply_model_pass, apply_model_points
from tools.strike_lab.town_navigation import canonical_points, build_navigation
from unicorn.x86_const import UC_X86_REG_ESI, UC_X86_REG_EBP, UC_X86_REG_EBX, UC_X86_REG_ESP, UC_X86_REG_ECX, UC_X86_REG_EIP


class CurrentTownMdlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root=indoor.routes.ROOT
        cls.image=(root/'artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin').read_bytes()
        if hashlib.sha256(cls.image).hexdigest()!=indoor.routes.IMAGE_SHA:
            raise AssertionError('Current image changed')
        raw=(root.parent/'God2/Data2/map/island01/CityI1/cityI1.mdlZ').read_bytes()
        if hashlib.sha256(raw).hexdigest()!='bb2b72c2cb368ad9e91046783e1c9638ef02318f589cf462f0c45bbfdce04618':
            raise AssertionError('Current town MDL changed')
        cls.decoded=decode_csvz(raw)
        if hashlib.sha256(cls.decoded).hexdigest()!='59fd88e12c232c89ae8cb73fed4058090e708f963fc9525ededfe157fccfebef':
            raise AssertionError('Town MDL decode changed')
        cls.asset=parse_mdl(cls.decoded,allow_parent_rom=True)

    def native_models(self):
        self.assertEqual(len(self.asset['models']),167)
        self.assertEqual(len(self.asset['tiles']),167)
        self.assertEqual(self.asset['unaccounted_bytes'],0)
        harness=indoor.CurrentIndoorNavigationTests()
        harness.image=self.image
        harness.asset=self.asset
        vm,state=harness.prepared()
        section_end=next(r['end_exclusive'] for r in self.asset['regions'] if r['name']=='ModelDat')
        total_cells=0
        for index,model in enumerate(self.asset['models']):
            with self.subTest(model=index):
                end=self.asset['models'][index+1]['offset'] if index+1<len(self.asset['models']) else section_end
                rows=self.decoded[model['offset']:end].splitlines()
                state['tokens']=[v.decode('ascii') for v in b' '.join(rows[3:]).split()]
                state['token']=0
                address=indoor.MODELS+index*0x1000
                harness.call(vm,0x41560,this=address)
                self.assertEqual(struct.unpack('<8i',vm.mem_read(address+0x2c,32)),tuple([-1]*8))
                self.assertTrue(all(layer[0]==-1 for layer in model['layers'][1:]))
                tile_index,offset_x,offset_y=model['layers'][0]
                tile_fields=self.asset['tiles'][tile_index]['fields']
                self.assertGreater(tile_fields[1],0)
                tile=address+0x800
                # Stop before graphic-resource assertions; explicit nonzero
                # dimensions take the native 4A800 stores without image access.
                vm.reg_write(UC_X86_REG_ESP,indoor.routes.SP)
                vm.reg_write(UC_X86_REG_ECX,tile)
                vm.mem_write(indoor.routes.SP,struct.pack('<Iii',indoor.routes.RETURN,tile_fields[1],tile_fields[2]))
                harness.run_to(vm,0x4a800,0x4a842)
                self.assertEqual(struct.unpack('<ii',vm.mem_read(tile+8,8)),tuple(tile_fields[1:3]))
                vm.mem_write(address+8,struct.pack('<I',tile))
                vm.mem_write(address+0x14,struct.pack('<ii',offset_x,offset_y))
                harness.call(vm,0x41a00,this=address)
                self.assertEqual(struct.unpack('<ii',vm.mem_read(address,8)),
                                 (tile_fields[1]+offset_x,tile_fields[2]+offset_y))
                vm.reg_write(UC_X86_REG_ESI,address)
                vm.reg_write(UC_X86_REG_EBP,0x1234)
                vm.reg_write(UC_X86_REG_EBX,len(model['grids']))
                vm.reg_write(UC_X86_REG_ESP,indoor.routes.SP)
                vm.mem_write(indoor.routes.SP+0x170,struct.pack('<II',0x1234,indoor.routes.BODY))
                harness.run_to(vm,0x4cb26,0x4ce2b)
                self.assertEqual(state['token'],len(state['tokens']))
                actual_points=struct.unpack('<4i',vm.mem_read(address+0x2c,16))
                self.assertEqual(canonical_points(model['extra_8_ints']),
                                 [tuple(actual_points[:2]),tuple(actual_points[2:])])
                for frame,grid in enumerate(model['grids']):
                    pointer,width,height=struct.unpack('<III',vm.mem_read(address+0x4c+frame*36,12))
                    expected=bytes(map(int,self.decoded[grid['start']:grid['end_exclusive']].split()))
                    self.assertEqual((width,height),(grid['width'],grid['height']))
                    self.assertEqual(bytes(vm.mem_read(pointer,width*height)),expected)
                    self.assertEqual(bytes(vm.mem_read(pointer+width*height,16)),b'\xa5'*16)
                    total_cells+=width*height
        self.assertEqual(total_cells,self.asset['pass_cells'])
        return harness,vm

    def test_all_town_pass_frames_match_native_parser(self):
        self.native_models()

    def test_actual_town_windows_match_full_native_composition(self):
        harness,vm=self.native_models()
        raw=(indoor.routes.ROOT.parent/'God2/Data2/map/island01/CityI1/cityi1.mbd').read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(),'cf4a4f14f9e5377fa47b4f115d44b1fc90c5c9dff0e3e0f358d781ab8c1030ae')
        mbd=parse_mbd(raw)
        storage,manager,terrain,table,nodes=0x7000000,0x7100000,0x7200000,0x7300000,0x7400000
        for address,size in ((storage,0x100000),(manager,0x2000),(terrain,0x3000),(table,0x3000),(nodes,0x20000)):
            vm.mem_map(address,size)
        grouped={}
        for index,p in enumerate(self.asset['placements']):
            grouped.setdefault(tuple(p['block']),[]).append((index,p))
        for index,block in enumerate(mbd['blocks']):
            slot=storage+index*0x2000
            if block is not None:
                vm.mem_write(slot+8,struct.pack('<II',slot+0x100,21))
                vm.mem_write(slot+0x64,struct.pack('<II',index%9,index//9))
                vm.mem_write(slot+0x100,block)
            header=table+0x1000+index*32
            vm.mem_write(table+index*4,struct.pack('<I',header))
            harness.call(vm,0x424f0,this=header)
            group=grouped.get((index%9,index//9),[])
            for ordinal,(pi,p) in enumerate(group):
                node=nodes+pi*0x100
                fields=p['fields']
                harness.call(vm,0x41f90,this=node)
                harness.call(vm,0x41fc0,*fields[1:5],indoor.MODELS+fields[0]*0x1000,this=node)
                vm.mem_write(node+0x30,struct.pack('<I',fields[5]))
                harness.call(vm,0x425f0,node,this=header)
            def sort_key(item):
                fields=item[1]['fields']
                model=self.asset['models'][fields[0]]
                tile,_,dy=model['layers'][0]
                return fields[2]+self.asset['tiles'][tile]['fields'][2]+dy
            group.sort(key=sort_key)
            pointer=struct.unpack('<I',vm.mem_read(header+8,4))[0]
            for pi,_ in group:
                self.assertEqual(pointer,nodes+pi*0x100)
                pointer=struct.unpack('<I',vm.mem_read(pointer+4,4))[0]
            self.assertEqual(pointer,0)
        vm.mem_write(terrain+0x1464,struct.pack('<III',table,9,9))
        initial=bytes([0xa5])*3969
        vm.mem_write(manager+0x50,initial)
        harness.call(vm,0x42a60,this=manager)
        self.assertEqual(bytes(vm.mem_read(manager+0x50,3969)),initial)
        vm.mem_write(manager+0x1024,struct.pack('<I',terrain))
        for cy in range(9):
            for cx in range(9):
                blocks=[];pointers=[]
                for dy in (-1,0,1):
                    for dx in (-1,0,1):
                        x,y=cx+dx,cy+dy
                        index=y*9+x
                        block=mbd['blocks'][index] if 0<=x<9 and 0<=y<9 else None
                        blocks.append(block)
                        pointers.append(storage+index*0x2000 if block is not None else 0)
                expected=project_base_window(blocks,initial)
                fresh=project_base_window(blocks,bytes([255])*3969)
                cpp_objects=[]
                if pointers[4]:
                    for gy in range(cy-2,cy+2):
                        for gx in range(cx-2,cx+2):
                            for _,p in grouped.get((gx,gy),[]):
                                f=p['fields'];model=self.asset['models'][f[0]];grid=model['grids'][f[5]]
                                cells=bytes(map(int,self.decoded[grid['start']:grid['end_exclusive']].split()))
                                x,y=f[3]-cx*21+21,f[4]-cy*21+21
                                expected=apply_model_pass(expected,x,y,grid['width'],grid['height'],cells)
                                fresh=apply_model_pass(fresh,x,y,grid['width'],grid['height'],cells)
                                values=struct.unpack('<4i',vm.mem_read(indoor.MODELS+f[0]*0x1000+0x2c,16))
                                expected=apply_model_points(expected,x,y,((values[0],values[1]),(values[2],values[3])))
                                fresh=apply_model_points(fresh,x,y,((values[0],values[1]),(values[2],values[3])))
                                cpp_objects.append([x,y,grid['width'],grid['height'],*values,*cells])
                tokens=[]
                for block in blocks:
                    tokens.append(int(block is not None))
                    if block is not None:tokens.extend(block)
                tokens.append(len(cpp_objects))
                for obj in cpp_objects:tokens.extend(obj)
                binary=indoor.routes.ROOT/'build/tests/Release/recovered-outdoor-window.exe'
                output=subprocess.check_output([str(binary),'--dump'],input=' '.join(map(str,tokens)),
                                               text=True,timeout=10).strip()
                self.assertEqual(output,''.join('??' if v==255 else f'{v:02x}' for v in fresh),(cx,cy))
                vm.mem_write(manager+0x50,initial)
                vm.mem_write(manager+0xfdc,struct.pack('<9I',*pointers))
                vm.reg_write(UC_X86_REG_ESP,indoor.routes.SP)
                vm.reg_write(UC_X86_REG_ECX,manager)
                vm.mem_write(indoor.routes.SP,struct.pack('<I',indoor.routes.RETURN))
                vm.emu_start(indoor.routes.BASE+0x47440,indoor.routes.RETURN,timeout=10000000,count=2000000)
                self.assertEqual(vm.reg_read(UC_X86_REG_EIP),indoor.routes.RETURN,(cx,cy))
                self.assertEqual(vm.reg_read(UC_X86_REG_ESP),indoor.routes.SP+4)
                self.assertEqual(bytes(vm.mem_read(manager+0x50,3969)),expected,(cx,cy))
                initial=expected

    def test_parent_reference_is_opt_in_and_never_general_traversal(self):
        with self.assertRaises(ValueError):
            parse_mdl(self.decoded)
        baseline=parse_mdl(self.decoded,allow_parent_rom=True)
        # Current native CString preserves up to two leading parent components
        # and source subdirectories; this explicit mode never opens references.
        # Qualification: current-mdl-zero-pass-20260927.md, 634 native copies.
        for path in (b'..\\..\\tree03.ROM',b'..\\..\\Island02\\flowernew03.ROM',b"FM'.ROM"):
            with self.subTest(qualified_path=path):
                changed=self.decoded.replace(b'..\\tree03.ROM',path,1)
                parsed=parse_mdl(changed,allow_parent_rom=True)
                self.assertIn(path.decode('ascii'),parsed['rom_references'])
                self.assertEqual(len(parsed['models']),len(baseline['models']))
                self.assertEqual([p['fields'] for p in parsed['placements']],
                                 [p['fields'] for p in baseline['placements']])
                with self.assertRaises(ValueError):
                    parse_mdl(changed)
        for path in (b'..\\..\\..\\tree03.ROM',b'C:\\tree03.ROM',b'\\\\host\\tree03.ROM',
                     b'../tree03.ROM',b'folder\\..\\tree03.ROM',b'\\tree03.ROM'):
            with self.subTest(path=path),self.assertRaises(ValueError):
                parse_mdl(self.decoded.replace(b'..\\tree03.ROM',path,1),allow_parent_rom=True)

    def test_export_is_reproducible_and_keeps_unknown_cells(self):
        root=indoor.routes.ROOT
        result=build_navigation(root.parent/'God2',root/'build/tests/Release/recovered-outdoor-window.exe')
        saved=json.loads((root/'artifacts/world-atlas/town-2-4.json').read_text(encoding='ascii'))
        self.assertEqual(result,saved)
        self.assertFalse(result['runtime_validated'])
        self.assertFalse(result['dynamic_occupancy_included'])
        self.assertEqual(len(result['windows']),81)
        self.assertTrue(any('??' in w['cells_hex'] for w in result['windows']))
        for w in result['windows']:
            self.assertEqual(len(w['cells_hex']),7938)
            self.assertEqual(w['known_cells'],3969-w['cells_hex'].count('??'))
            self.assertEqual(w['sha256'],hashlib.sha256(w['cells_hex'].encode('ascii')).hexdigest())

    def test_all_town_placement_field_projections(self):
        self.assertEqual(len(self.asset['placements']),362)
        self.assertEqual(len(self.asset['groups']),37)
        for placement in self.asset['placements']:
            with self.subTest(offset=placement['offset']):
                result=native_mdl_placement(self.image,placement,len(self.asset['models']))
                self.assertEqual(result['instance_values'][:4],placement['fields'][1:5])
                self.assertEqual(result['extra_store_values'][0],placement['fields'][5])

    def test_native_container_orders_by_pixel_y_plus_model_height(self):
        harness=indoor.CurrentIndoorNavigationTests()
        harness.image=self.image;harness.asset=self.asset
        vm,_=harness.prepared()
        header,nodes,models=0x7000000,0x7001000,0x7010000
        vm.mem_map(header,0x20000)
        for pairs in (((40,10),(10,20),(20,30),(0,50)),
                      ((0,0),(-20,10),(10,-20),(100,0)),
                      ((4,2),(3,2),(2,2),(1,2))):
            harness.call(vm,0x424f0,this=header)
            expected=[]
            for index,(pixel_y,height) in enumerate(pairs):
                node=nodes+index*0x100;model=models+index*0x100
                vm.mem_write(model+4,struct.pack('<i',height))
                harness.call(vm,0x41f90,this=node)
                harness.call(vm,0x41fc0,0,pixel_y&0xffffffff,0,0,model,this=node)
                harness.call(vm,0x425f0,node,this=header)
                expected.append(index)
                expected.sort(key=lambda i:pairs[i][0]+pairs[i][1])
                pointer=struct.unpack('<I',vm.mem_read(header+8,4))[0]
                actual=[];previous=0
                while pointer:
                    self.assertLess(len(actual),len(expected))
                    self.assertEqual(struct.unpack('<I',vm.mem_read(pointer+8,4))[0],previous)
                    actual.append((pointer-nodes)//0x100)
                    previous,pointer=pointer,struct.unpack('<I',vm.mem_read(pointer+4,4))[0]
                self.assertEqual(actual,expected)
                self.assertEqual(struct.unpack('<I',vm.mem_read(header+0xc,4))[0],previous)
                self.assertEqual(struct.unpack('<I',vm.mem_read(header+0x14,4))[0],len(expected))


if __name__=='__main__':
    unittest.main()
