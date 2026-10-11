"""Current catalog -> original row loader/lookup, not rendered-map acceptance."""
import hashlib
import json
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.strike_lab.world_atlas import build_atlas, parse_catalog, qualify_selector, relative_asset
import test_current_route_advertisement as routes
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_EBP, UC_X86_REG_ECX
from unicorn.x86_const import UC_X86_REG_EIP, UC_X86_REG_ESP

DATA, ROWS, WORLD = 0x3800000, 0x3900000, 0x4000000


class CurrentMapAtlasTests(unittest.TestCase):
    vm = routes.CurrentRouteAdvertisementTests.vm
    run_to = routes.CurrentRouteAdvertisementTests.run_to
    call = routes.CurrentRouteAdvertisementTests.call

    @classmethod
    def setUpClass(cls):
        cls.image = (ROOT/'artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin').read_bytes()
        if hashlib.sha256(cls.image).hexdigest() != routes.IMAGE_SHA:
            raise AssertionError('Current mapped client changed')
        cls.atlas = build_atlas(ROOT.parent/'God2')
        if cls.atlas['source']['sha256'] != '70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731':
            raise AssertionError('Current catalog changed; requalify source')

    def loaded(self):
        vm = self.vm()
        vm.mem_map(DATA, 0xe0000)
        vm.mem_map(ROWS, 0x10000)
        vm.mem_write(ROWS, b'\xa5'*0x10000)
        records = self.atlas['maps']
        state = {'row':-1}
        def return_from(uc, sp, ret, eax, cleanup=0):
            uc.reg_write(UC_X86_REG_EAX, eax)
            uc.reg_write(UC_X86_REG_ESP, sp+4+cleanup)
            uc.reg_write(UC_X86_REG_EIP, ret)
        def services(uc, address, size, _):
            rva = address-routes.BASE
            if rva not in (0x147e23,0x51a90,0x1480b4):
                return
            sp = uc.reg_read(UC_X86_REG_ESP)
            ret = struct.unpack('<I',uc.mem_read(sp,4))[0]
            if rva == 0x147e23:
                count, stride = struct.unpack('<II',uc.mem_read(sp+4,8))
                self.assertEqual((count,stride),(144,0x1a4))
                uc.mem_write(ROWS, bytes(count*stride))
                return_from(uc,sp,ret,ROWS)
            elif rva == 0x51a90:
                state['row'] += 1
                fields = [bytes.fromhex(s) for s in records[state['row']]['raw_fields_hex']]
                uc.mem_write(DATA+8, struct.pack('<H',len(fields)))
                uc.mem_write(DATA+0x78, bytes(380*24))
                for column, field in enumerate(fields):
                    uc.mem_write(DATA+0x78+380*column, field+b'\0')
                return_from(uc,sp,ret,1)
            else:
                # CRT sscanf("%d"); row accessors and packed-field writes are original.
                source, fmt, dest = struct.unpack('<III',uc.mem_read(sp+4,12))
                self.assertEqual(bytes(uc.mem_read(fmt,3)), b'%d\0')
                value = bytes(uc.mem_read(source,64)).split(b'\0',1)[0]
                uc.mem_write(dest, struct.pack('<i',int(value)))
                return_from(uc,sp,ret,1)
        vm.hook_add(UC_HOOK_CODE, services)
        vm.mem_write(routes.SP, struct.pack('<II',routes.RETURN,len(records)))
        vm.reg_write(UC_X86_REG_ESP, routes.SP)
        vm.reg_write(UC_X86_REG_ECX, DATA)
        vm.emu_start(routes.BASE+0x59a80,routes.RETURN,timeout=5000000,count=2000000)
        self.assertEqual(vm.reg_read(UC_X86_REG_EIP),routes.RETURN)
        self.assertEqual(state['row'],143)
        self.assertEqual(bytes(vm.mem_read(ROWS+144*0x1a4,32)),b'\xa5'*32)
        return vm

    def test_all_current_rows_match_original_loader_and_lookup(self):
        vm = self.loaded()
        for index, record in enumerate(self.atlas['maps']):
            with self.subTest(index=index):
                data = bytes(vm.mem_read(ROWS+index*0x1a4,0x1a4))
                fields = [bytes.fromhex(s) for s in record['raw_fields_hex']]
                for col,offset in ((0,0),(1,0x10),(2,0x20),(8,0x30),(9,0x70),(10,0xb0)):
                    self.assertEqual(data[offset:offset+len(fields[col])+1],fields[col]+b'\0')
                self.assertEqual(struct.unpack_from('<H',data,0xf0)[0],record['packed_selector'])
                self.assertEqual(struct.unpack_from('<I',data,0xf4)[0],
                                 record['kind']|(record['catalog_x']<<2)|(record['catalog_y']<<17))
                self.assertEqual(struct.unpack_from('<HHH',data,0xf8),
                                 (record['layer_width'],record['layer_height'],record['layers_per_row']))
                self.call(vm,0x59d80,record['area'],record['scene'],this=DATA)
                self.assertEqual(vm.reg_read(UC_X86_REG_EAX),ROWS+index*0x1a4)
        self.call(vm,0x59d80,2,15,this=DATA)
        self.assertEqual(vm.reg_read(UC_X86_REG_EAX),0)

    def test_historical_flag_two_skips_normal_map_initializer(self):
        for flag in (0,1,2,3):
            vm = self.vm()
            for page in {(WORLD+offset)&~4095 for offset in (0,0x1539683c)}:
                vm.mem_map(page,4096)
            vm.mem_write(WORLD+0x1539684c,bytes([flag]))
            vm.reg_write(UC_X86_REG_EBP,WORLD)
            vm.reg_write(UC_X86_REG_ESP,routes.SP)
            self.run_to(vm,0x65364,0x653ee if flag==2 else 0x6539c)

    def test_catalog_and_asset_counts_do_not_claim_runtime_validation(self):
        self.assertEqual(self.atlas['counts']['maps_total'],144)
        self.assertEqual(self.atlas['counts']['maps_with_mdt'],134)
        self.assertEqual(self.atlas['counts']['maps_runtime_validated'],0)
        self.assertFalse(qualify_selector(self.atlas,2,15)['catalog_match'])
        self.assertTrue(qualify_selector(self.atlas,2,0)['catalog_match'])
        island = qualify_selector(self.atlas,2,0)['records'][0]
        self.assertEqual(island['mdt_variants'][0]['mapnum'],[35,37])
        self.assertIsNone(island['spawn'])
        self.assertIsNone(island['collision'])
        self.assertEqual(self.atlas,build_atlas(ROOT.parent/'God2'))

    def test_malformed_rows_and_path_traversal_are_rejected(self):
        fields = [bytes.fromhex(s) for s in self.atlas['maps'][0]['raw_fields_hex']]
        def table(rows):
            return b'Map_City_Coordniate,'+str(len(rows)).encode()+b'\r\n'+b'\r\n'.join(rows)+b'\r\nNext,0\r\n'
        row = b','.join(fields)
        for column,value in ((0,b'A'*16),(3,b'17'),(4,b'4'),(5,b'1024'),(6,b'-1'),(10,b'..\\escape.mdt')):
            changed = fields.copy();changed[column]=value
            with self.subTest(column=column),self.assertRaises(ValueError):
                parse_catalog(table([b','.join(changed)]))
        with self.assertRaises(ValueError):parse_catalog(table([row,row]))
        for path in (b'../bad',b'C:\\bad',b'\\\\host\\bad',b'bad:stream'):
            with self.assertRaises(ValueError):relative_asset(path)


if __name__ == '__main__':
    unittest.main()
