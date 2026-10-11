"""Native actor -> catalog -> CAN -> indoor resources, without a display device.

The cold actor includes the original resource preload, followed by the 1004F5
scene path. Progress timing remains fixed-clock; no graphics device executes.
"""
import hashlib
import struct

from .current_world_actor import ROOT, BASE, WORLD, ACTOR, UI, MESSAGES
from .current_cold_world_actor import NativeColdWorldActor
from .current_world_role_resources import CWD
from .current_indoor_resources import NativeIndoorResources, SURFACE, SP, SCRATCH
from .world_atlas import parse_catalog
from .omega_assets import decode_csvz
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import (UC_X86_REG_EAX, UC_X86_REG_EBP, UC_X86_REG_EDI,
                              UC_X86_REG_ESI, UC_X86_REG_ESP, UC_X86_REG_EIP)

SCENE_BRIDGE, MAP_MANAGER = 0x7400000, 0x7410000
CAN_PATH = 'data2/map/island01/island01.can'
INDOOR_PATH = 'data2/map/island01/indoor/'


class NativeWorldScene(NativeColdWorldActor):
    def __init__(self, appearance=None):
        super().__init__(appearance)
        self.scene_visits, self.scene_files, self.scene_attempts = [], {}, []
        self._map_rw(MESSAGES, 0xe0000)
        self._map_rw(UI+0x8aa30, 8)
        self._map_rw(UI+0xcff70, 4)
        self._map_rw(SCENE_BRIDGE, 4096)
        self._map_rw(MAP_MANAGER, 0x2000)
        self._load_catalog()
        self._load_scene_sources()
        # The cold bank constructor already installed these OS adapters.
        for rva in (0x1490ad, 0x149b00, 0x15ada3, 0x15aaaa, 0x15ae6e,
                    0x15aebe, 0x15afca, 0x158a58):
            if rva not in self.bank_service_rvas:
                self.hooks.append(self.vm.hook_add(UC_HOOK_CODE, self._service,
                                                   begin=BASE+rva, end=BASE+rva))
        for rva in (0x59d80, 0x44f70, 0xc3ea0, 0x48300, 0x37900, 0x49330):
            self.hooks.append(self.vm.hook_add(UC_HOOK_CODE, self._scene_visit,
                                               begin=BASE+rva, end=BASE+rva))
        self.call(0x27400, this=SURFACE)
        self.call(0x42a60, this=MAP_MANAGER)
        # Explicit RGB555 fixture surface, null optional device owner. Neither
        # the small bridge nor actor's poison owner is a claimed live renderer.
        self.vm.mem_write(MAP_MANAGER+0x1678, struct.pack('<II', SURFACE, 0))
        self.vm.mem_write(SCENE_BRIDGE+0xbc, struct.pack('<I', MAP_MANAGER))
        self.vm.mem_write(WORLD+0xa7e05dc, struct.pack('<I', SCENE_BRIDGE))
        self.vm.mem_write(UI+0xcff70, struct.pack('<I', MESSAGES))
        self.scene_started = self.scene_loaded = False

    def _load_catalog(self):
        path = ROOT.parent/'God2/Data2/Patch/Comm/gamedata.csvZ'
        if path.stat().st_size > 1024*1024:
            raise ValueError('Map catalog source bound')
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != '70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731':
            raise ValueError('Pinned map catalog changed')
        plain = decode_csvz(raw, limit=4*1024*1024)
        if hashlib.sha256(plain).hexdigest() != '75c3c37947a64b0917fbf8e546884d9bf893fe6a606d3e2b8f3b1857966b1815':
            raise ValueError('Pinned map catalog decode changed')
        self.catalog = parse_catalog(plain)
        if len(self.catalog) != 144:
            raise ValueError('Unexpected map row count')
        self.catalog_records = self.allocate(144*0x1a4)
        self.vm.mem_write(MESSAGES+0xd2aba, struct.pack('<HI', 144, self.catalog_records))
        self.vm.mem_write(MESSAGES+8, struct.pack('<H', 24))
        lines = plain.split(b'\n')
        for ordinal, row in enumerate(self.catalog):
            line = (lines[row['source_line']-1]+b'\n').replace(b'\r\n', b'\n')
            if len(line) >= 4096:
                raise ValueError('Map row input bound')
            self.vm.mem_write(SCRATCH, line+b'\0')
            self.call(0x51be0, SCRATCH, this=MESSAGES)
            self.vm.reg_write(UC_X86_REG_ESP, SP)
            self.vm.reg_write(UC_X86_REG_EBP, MESSAGES)
            self.vm.mem_write(SP+0x14, struct.pack('<I', ordinal*0x1a4))
            self.vm.mem_write(SP+0x1c, struct.pack('<II', ordinal, 144))
            self._slice(0x59ad7, 0x59d67)
            if self.vm.reg_read(UC_X86_REG_ESP) != SP:
                raise AssertionError('Map row stack imbalance')

    def _load_scene_sources(self):
        sources = {
            CAN_PATH: 'f2b9ca9dc4dcebcd1c1c40de14ea63f1b2061993f644c49b9c7baca9ce2d2f97',
            INDOOR_PATH+'groceryl.hmdz': '42d769c0ff328db3e1e295e17208d0db7a0ff12608976f952dae800ff79c3c00',
            INDOOR_PATH+'grol.romz': '20e5a8be548993e9d17cca9b2d9292b150f73b7907ed720256132ef4659bce6c',
        }
        for relative, digest in sources.items():
            path = ROOT.parent/'God2'/relative
            if path.stat().st_size > 8*1024*1024:
                raise ValueError('Scene source bound')
            raw = path.read_bytes()
            if hashlib.sha256(raw).hexdigest() != digest:
                raise ValueError('Pinned scene source changed: '+relative)
            if relative.endswith('.hmdz'):
                self.hmd_raw = raw
                self.hmd = decode_csvz(raw, limit=1024*1024)
                self.scene_files[relative[:-1]] = self.hmd
            else:
                self.scene_files[relative] = raw
                if relative.endswith('.romz'):
                    self.decoded['grol.romz'] = decode_csvz(raw, limit=8*1024*1024)
        self.can = self.scene_files[CAN_PATH]
        self.validate_hmd_decompression()

    def _scene_visit(self, vm, address, size, data):
        self.scene_visits.append(address-BASE)

    def _service(self, vm, address, size, context):
        rva = address-BASE
        if rva in (0x1490ad, 0x149b00, 0x15ada3, 0x15aaaa, 0x15ae6e,
                    0x15aebe, 0x15afca, 0x158a58):
            return NativeIndoorResources._service(self, vm, address, size, context)
        if rva in (0x147af7, 0x158e89):
            sp = vm.reg_read(UC_X86_REG_ESP)
            if self.string(self.u32(sp+8)) == b'%s\\%s':
                value = self.string(self.u32(sp+12))+b'\\'+self.string(self.u32(sp+16))
                if len(value) >= 260:
                    raise AssertionError('Scene path buffer bound')
                if rva == 0x158e89:
                    self.cstring(self.u32(sp+4), value)
                else:
                    vm.mem_write(self.u32(sp+4), value+b'\0')
                vm.reg_write(UC_X86_REG_EAX, len(value) if rva == 0x147af7 else 0)
                vm.reg_write(UC_X86_REG_ESP, sp+4)
                vm.reg_write(UC_X86_REG_EIP, self.u32(sp))
                return
        if rva == 0x14716f and hasattr(self, 'scene_files'):
            sp = vm.reg_read(UC_X86_REG_ESP)
            path = self.string(self.u32(sp+4)).decode('ascii').replace('\\', '/').lower()
            prefix = CWD.decode().replace('\\', '/').lower()+'/'
            relative = path[len(prefix):] if path.startswith(prefix) else path
            if relative in (CAN_PATH, INDOOR_PATH+'groceryl.hmd', INDOOR_PATH+'groceryl.hmdz',
                            INDOOR_PATH+'grol.rom', INDOOR_PATH+'grol.romz'):
                if self.string(self.u32(sp+8)) not in (b'rb', b'rt'):
                    raise AssertionError('Scene files are read only')
                self.scene_attempts.append(relative)
                result = 0
                if relative in self.scene_files:
                    self.opens.append(relative)
                    result = 0x80000000+4*len(self.opens)
                    self.handles[result] = [self.scene_files[relative], 0]
                self.active_name = 'grol.romz'
                vm.reg_write(UC_X86_REG_EAX, result)
                vm.reg_write(UC_X86_REG_ESP, sp+4)
                vm.reg_write(UC_X86_REG_EIP, self.u32(sp))
                return
        return super()._service(vm, address, size, context)

    def enter_scene(self, body, *, name=b'BoundHero'):
        if (len(body) != 36 or struct.unpack_from('<H', body, 24)[0] != (2 | (15 << 6))
                or (struct.unpack_from('<I', body, 28)[0] & 3) != 2):
            raise ValueError('Only qualified retained indoor scene')
        if self.scene_started:
            raise ValueError('Fresh scene only; reload lifecycle is not qualified')
        self.scene_started = True
        self.initialize(body, name=name)
        self.vm.reg_write(UC_X86_REG_ESP, SP)
        self.vm.reg_write(UC_X86_REG_ESI, WORLD)
        self.vm.reg_write(UC_X86_REG_EDI, self.actor_address)
        self.vm.mem_write(SP+0x38, struct.pack('<I', 1))
        self._slice(0x1004f5, 0x10078f)
        if self.vm.reg_read(UC_X86_REG_ESP) != SP:
            raise AssertionError('Scene continuation stack imbalance')
        self.scene_loaded = True
        return self.u32(MAP_MANAGER+0x1030)
