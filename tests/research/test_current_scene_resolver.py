"""Original area/CAN loader and world asset selection, not live rendering."""
import hashlib
import struct
import subprocess
import unittest

import test_current_map_atlas as atlas
import test_current_world_entry as entry
from test_current_map_atlas import routes
from tools.strike_lab.omega_assets import decode_csvz
from unicorn import UC_HOOK_CODE, UC_PROT_READ, UC_PROT_WRITE
from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_ECX, UC_X86_REG_EDI
from unicorn.x86_const import UC_X86_REG_EIP, UC_X86_REG_ESI, UC_X86_REG_ESP

WORLD, ACTOR, RENDERER, MANAGER, HEAP = 0x4000000, 0x4100000, 0x4200000, 0x4300000, 0x4400000


class CurrentSceneResolverTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        atlas.CurrentMapAtlasTests.setUpClass()
        entry.CurrentWorldEntryTests.setUpClass()
        cls.client = routes.ROOT.parent/'God2'
        cls.can = (cls.client/'Data2/map/island01/Island01.can').read_bytes()
        if hashlib.sha256(cls.can).hexdigest() != 'f2b9ca9dc4dcebcd1c1c40de14ea63f1b2061993f644c49b9c7baca9ce2d2f97':
            raise AssertionError('Current scene index changed; requalify source')

    def resolver(self, can=None, expected_map=(2,15)):
        can = self.can if can is None else can
        source = atlas.CurrentMapAtlasTests()
        vm = source.loaded()
        vm.mem_map(0, 4096)  # Synthetic x86 exception-chain storage, not host state.
        for addr, size in ((WORLD,4096),(ACTOR,4096),(RENDERER,4096),
                           (MANAGER,0x2000),(HEAP,0x20000)):
            vm.mem_map(addr,size)
        for offset,value in ((0xaa36480,atlas.DATA),(0xa7e05dc,RENDERER)):
            page = (WORLD+offset)&~4095
            vm.mem_map(page,4096)
            vm.mem_write(WORLD+offset,struct.pack('<I',value))
        vm.mem_protect(0x5b5000,4096,UC_PROT_READ|UC_PROT_WRITE)
        vm.mem_write(RENDERER+0xbc,struct.pack('<I',MANAGER))
        vm.mem_write(MANAGER+0x1670,struct.pack('<I',HEAP))
        vm.mem_write(HEAP,b'\0')
        state = {'position':0,'allocation':HEAP+0x100,'opened':[], 'formatted':[]}

        def string(address):
            result = bytearray()
            for index in range(1024):
                byte = bytes(vm.mem_read(address+index,1))
                if byte == b'\0':
                    return bytes(result)
                result.extend(byte)
            raise AssertionError('Unbounded client string')

        def allocate(data):
            address = state['allocation']
            state['allocation'] += (len(data)+15)&~15
            self.assertLess(state['allocation'],HEAP+0x20000)
            vm.mem_write(address,data)
            return address

        def service(uc,address,size,_):
            rva = address-routes.BASE
            supported = {0x147af7,0x149b00,0x12f550,0x149657,0x14716f,
                         0x14785c,0x147973,0x147182,0x15ada3,0x15aaaa,
                         0x15ad35,0x15ae6e,0x158e89,0xc3ea0,0x2c70}
            if rva not in supported:
                return
            sp = uc.reg_read(UC_X86_REG_ESP)
            ret = struct.unpack('<I',uc.mem_read(sp,4))[0]
            def arg(index):
                return struct.unpack('<I',uc.mem_read(sp+4+index*4,4))[0]
            cleanup, result = 0, 0
            this = uc.reg_read(UC_X86_REG_ECX)
            if rva in (0x147af7,0x158e89):
                dest, fmt, left, right = (arg(i) for i in range(4))
                self.assertEqual(string(fmt),b'%s\\%s')
                value = string(left)+b'\\'+string(right)
                state['formatted'].append(value)
                if rva == 0x147af7:
                    uc.mem_write(dest,value+b'\0')
                    result = len(value)
                else:
                    uc.mem_write(dest,struct.pack('<I',allocate(value+b'\0')))
            elif rva == 0x149b00:
                index = string(arg(0)).rfind(bytes([arg(1)]))
                result = arg(0)+index if index >= 0 else 0
            elif rva == 0x12f550:
                # Host working-directory expansion only; retain native relative path.
                result = arg(0)
            elif rva == 0x149657:
                result = int(string(arg(0)) != string(arg(1)))
            elif rva == 0x14716f:
                self.assertEqual(string(arg(1)),b'rb')
                self.assertEqual(string(arg(0)).lower(),b'\\data2\\map\\island01\\island01.can')
                state['opened'].append(string(arg(0)))
                state['position'] = 0
                result = 0x1234
            elif rva == 0x14785c:
                dest, width, count, handle = (arg(i) for i in range(4))
                self.assertEqual(handle,0x1234)
                size = width*count
                data = can[state['position']:state['position']+size]
                self.assertEqual(len(data),size)
                uc.mem_write(dest,data)
                state['position'] += size
                result = count
            elif rva == 0x147973:
                self.assertEqual(arg(0),64)
                result = allocate(bytes(64))
            elif rva == 0x147182:
                self.assertEqual(arg(0),0x1234)
            elif rva in (0x15ada3,0x15aaaa,0x15ae6e):
                value = arg(0) if rva == 0x15ada3 else struct.unpack('<I',uc.mem_read(arg(0),4))[0]
                uc.mem_write(this,struct.pack('<I',value))
                cleanup, result = 4, this
            elif rva == 0xc3ea0:
                self.assertEqual((arg(0)&65535,arg(1)&65535),expected_map)
                cleanup = 8  # UI bounds refresh, not asset selection.
            elif rva == 0x2c70:
                self.fail('Original client assertion reached')
            uc.reg_write(UC_X86_REG_EAX,result)
            uc.reg_write(UC_X86_REG_ESP,sp+4+cleanup)
            uc.reg_write(UC_X86_REG_EIP,ret)
        vm.hook_add(UC_HOOK_CODE,service)
        return vm,state,string

    def test_original_initializer_resolves_historical_scene_to_indoor_loader(self):
        vm,state,string = self.resolver()
        # Carry actual C++ output through the original decoder and actor parser.
        # Resource helpers in that projection harness remain explicitly stubbed.
        projection = entry.CurrentWorldEntryTests()
        plain = projection.decode(projection.vm(),projection.wire(217))
        actor_vm = projection.project(plain[3:-1])
        actor = bytes(actor_vm.mem_read(entry.ACTOR,28))
        vm.mem_write(ACTOR,actor)
        vm.mem_write(WORLD+0x22c,struct.pack('<I',actor[0x10]))
        vm.reg_write(UC_X86_REG_ESI,WORLD)
        vm.reg_write(UC_X86_REG_EDI,ACTOR)
        vm.reg_write(UC_X86_REG_ESP,routes.SP)
        vm.mem_write(routes.SP+0x38,struct.pack('<I',1))
        vm.emu_start(routes.BASE+0x1004f5,routes.BASE+0x48300,timeout=5000000,count=200000)
        self.assertEqual(vm.reg_read(UC_X86_REG_EIP),routes.BASE+0x48300)
        self.assertEqual(vm.reg_read(UC_X86_REG_ECX),MANAGER)
        sp = vm.reg_read(UC_X86_REG_ESP)
        path = struct.unpack('<I',vm.mem_read(sp+8,4))[0]
        self.assertEqual(string(path).lower(),b'\\data2\\map\\island01\\indoor\\groceryl.hmd')
        self.assertEqual(state['position'],len(self.can))
        self.assertEqual(len(state['opened']),1)
        self.assertEqual(struct.unpack('<I',vm.mem_read(MANAGER+0x1068,4))[0],130)
        self.assertEqual(struct.unpack('<H',vm.mem_read(MANAGER+0x106c+15*2,2))[0],12)
        file_count = struct.unpack_from('<I',self.can,8)[0]
        self.assertEqual(struct.unpack('<I',vm.mem_read(MANAGER+0x126c,4))[0],file_count)
        for index in range(file_count):
            pointer = struct.unpack('<I',vm.mem_read(MANAGER+0x1270+index*4,4))[0]
            self.assertEqual(bytes(vm.mem_read(pointer,64)),self.can[12+index*64:76+index*64])
        self.assertEqual(bytes(vm.mem_read(MANAGER+0x106c,130*2)),self.can[12+file_count*64+4:])
        self.assertEqual(struct.unpack('<II',vm.mem_read(WORLD+0x224,8)),(17,13))
        raw = (self.client/'Data2/map/island01/indoor/groceryL.hmdZ').read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(),'42d769c0ff328db3e1e295e17208d0db7a0ff12608976f952dae800ff79c3c00')
        self.assertTrue(decode_csvz(raw).startswith(b'HMD v1.6'))

    def test_original_can_loader_rejects_wrong_magic(self):
        vm,state,_ = self.resolver(b'NOTACAN!'+self.can[8:])
        path = HEAP+0x1f000
        vm.mem_write(path,b'\\Data2\\map\\island01\\Island01.can\0')
        atlas.CurrentMapAtlasTests().call(vm,0x44f70,path,this=MANAGER)
        self.assertEqual(vm.reg_read(UC_X86_REG_EAX),0)
        self.assertEqual(state['position'],8)
        self.assertEqual(bytes(vm.mem_read(MANAGER+0x1068,0x608)),bytes(0x608))

    def test_town_packet_selects_native_outdoor_loader(self):
        vm,state,string=self.resolver(expected_map=(2,4))
        projection=entry.CurrentWorldEntryTests()
        wire=bytes.fromhex(subprocess.check_output(
            [str(projection.binary),'--dump','217','0','0','110','110','2','4','0'],
            text=True,timeout=5).strip())
        plain=projection.decode(projection.vm(),wire)
        actor_vm=projection.project(plain[3:-1],(2,4))
        actor=bytes(actor_vm.mem_read(entry.ACTOR,28))
        vm.mem_write(ACTOR,actor)
        vm.mem_write(WORLD+0x22c,struct.pack('<I',actor[0x10]))
        vm.reg_write(UC_X86_REG_ESI,WORLD)
        vm.reg_write(UC_X86_REG_EDI,ACTOR)
        vm.reg_write(UC_X86_REG_ESP,routes.SP)
        vm.mem_write(routes.SP+0x38,struct.pack('<I',1))
        vm.emu_start(routes.BASE+0x1004f5,routes.BASE+0x44b80,timeout=5000000,count=200000)
        self.assertEqual(vm.reg_read(UC_X86_REG_EIP),routes.BASE+0x44b80)
        self.assertEqual(vm.reg_read(UC_X86_REG_ECX),MANAGER)
        sp=vm.reg_read(UC_X86_REG_ESP)
        path=struct.unpack('<I',vm.mem_read(sp+8,4))[0]
        self.assertEqual(string(path).lower(),b'\\data2\\map\\island01\\cityi1\\cityi1.mdt')
        self.assertEqual(state['position'],len(self.can))
        self.assertEqual(len(state['opened']),1)
        self.assertEqual(struct.unpack('<II',vm.mem_read(WORLD+0x224,8)),(110,110))


if __name__ == '__main__':
    unittest.main()
