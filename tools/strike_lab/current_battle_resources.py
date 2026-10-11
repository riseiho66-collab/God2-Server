"""Current FightComm3 -> original ROM preload, not live battle acceptance.

Explicit native stages: reader, name-registry constructor slice, preload loop,
and control consumer. Bounded CRT/MFC/file adapters never replace game callees.
"""
import csv
import hashlib
import io
import struct

from .current_role_doll_resources import NativeRoleDollResources, ROOT, BASE, BANK
from .current_world_ui_resource import NativeWorldUIResource, CWD
from .current_indoor_resources import SP, SURFACE
from .omega_assets import decode_csvz
from unicorn import UC_HOOK_CODE, UC_PROT_READ, UC_PROT_WRITE, UC_PROT_EXEC
from unicorn.x86_const import (UC_X86_REG_EAX, UC_X86_REG_EBX, UC_X86_REG_EBP,
                              UC_X86_REG_ESI, UC_X86_REG_EDI, UC_X86_REG_ESP,
                              UC_X86_REG_EIP)

BATTLE = 0x7000000
READER, MANAGER = BATTLE + 0x71268, BATTLE + 0x144938
RENDERER = 0x7400000
STRIDE, CAPACITY = 0x108, 10
SOURCE = 'Data2/Patch/FightComm3.csvZ'
SOURCE_SHA = 'fd96359b66809968ad8454350417a9aad1a7e0e15cacbaa4788215ef22fb3578'
PLAIN_SHA = '4fe7f229c7a7d95a76f51a8ee7a710763f75f0e3a83a96b79fbaa895cdfbac8c'
ASSETS = {
    'data3/fight/gui/fightgui2.romz': ('6c5db200841255300cae1af0f10d8580ccccb854942877f9ff0f1cf4938bddd2', 'a23bc07c1c9081fa748d4e3a78616f42c52752715d30f544b0a0f9d06f5b40ce'),
    'data2/itmimg/ski01.romz': ('50844735316f6989efc2c56a261ddb830b0815cee9f975745f6a3a0b4c61f6ea', 'af10bdfc63017908062a84fe57845bc9a0e031657b73c26d6d89c6c55bed6939'),
    'data2/itmimg/ski02.romz': ('ccb9daa4af45ae79724e8c2714fd0f2471579def2560ac6a7803f4211b7c496c', '944decc06333c1913e0446898f2e5c708aae40bd0e335d09c4c224f0e86e0b16'),
    'data2/itmimg/ski03.romz': ('866e3b173977dee5afbd60d22a230d4f0234c925bfb3c6f7ab9436ba6d008c1c', 'e64f5b665fe2a20ddbb57ecd3d879671f50980c19cb3228e43711e18ef5d39e9'),
    'data2/itmimg/ski04.romz': ('83b97ef265e7564b19e3da7c6836849d49a0a63a9f3cf8d9a006c37016cfefbd', 'af52f2a69c242f2310df3c5b05d52944ac0ba9647226825563bf9f1e332df442'),
    'data2/fight/gui/eft2_8301.romz': ('46336b61d49807c67b05f253a077a90cae39b0757196877c38299a939d515fea', '48ddaa8115a5e10fad0eaeefc33c1ab62a468ef571abb74c1b338688466ebe6e'),
    'data3/fight/gui/stateicon2.romz': ('4ee8049237945c385d3bc2ec3e47ecc6fc0634fae0536e4a28a11395113f9f1c', '635eb61af20f2f5290940799aed1c7e5cda57673043032037711675ffd1f18c7'),
    'data2/fight/gui/rusebottom.romz': ('6383b9661613db1302966864225ad7905f4ec05b75ea4c9d128309cd7b9ddcff', 'bfecb6ccddced6640356e2a9cc5b84ddb3c1f73f87b71f14ca1903223ff6bc67'),
    'data3/fight/gui/eft2_8302.romz': ('37241f1e1af509e8254b7b182eeaee43b541ecdbfdfa979463f6ffc483723254', '54303d9af579c7b5f5cc4e65b5ab31c843a53643846eaf13a50eeddd80636ed0'),
    'data3/flow/motion.romz': ('efa62f3528d9b9e8d19d3885eca4706f851cc4dbaed62b7438fd80a808c6ed7f', '86a71831926432c81835873bd37de73c3b0bfa1677c968d487a16cf2f9fffd95'),
}


def pinned_sources(root=ROOT.parent / 'God2'):
    files, decoded = {}, {}
    for path, (raw_sha, plain_sha) in {SOURCE: (SOURCE_SHA, PLAIN_SHA), **ASSETS}.items():
        source = root / path
        if source.stat().st_size > 4 * 1024 * 1024:
            raise ValueError('Battle resource source bound')
        raw = source.read_bytes()
        if hashlib.sha256(raw).hexdigest() != raw_sha:
            raise ValueError('Pinned battle resource changed: ' + path)
        plain = decode_csvz(raw, limit=16 * 1024 * 1024)
        if hashlib.sha256(plain).hexdigest() != plain_sha:
            raise ValueError('Pinned battle decode changed: ' + path)
        files[path], decoded[path] = raw, plain
    rows = list(csv.reader(io.StringIO(decoded[SOURCE].decode('latin1'), newline='')))
    if rows[0][:3] != ['FightCommon', '1', '5'] or len(rows) != 14:
        raise ValueError('Battle common CSV shape changed')
    rows = rows[4:]
    if ([r[0] for r in rows] != [str(i) for i in range(CAPACITY)] or
            [r[1].replace('\\', '/').lower() + 'z' for r in rows] != list(ASSETS)):
        raise ValueError('Battle common indices/paths changed')
    return files, decoded, rows


class NativeBattleResources(NativeRoleDollResources):
    bank_capacity = 32 * 1024 * 1024
    battle_address = BATTLE

    def allocate(self, length):
        if length != self.bank_capacity:
            return super().allocate(length)
        # Current battle constructor passes 0x2000000 to its ROM bank.
        if self.heap + length > self.heap_limit:
            raise AssertionError('Battle bank allocation bound')
        pointer = self.heap
        self.heap += length
        self.vm.mem_map(pointer, length, UC_PROT_READ | UC_PROT_WRITE)
        self.allocations[pointer] = length
        return pointer

    def __init__(self):
        self.battle_ready = False
        super().__init__()
        self.battle = self.battle_address
        self.reader, self.manager = self.battle + 0x71268, self.battle + 0x144938
        self.files, self.decoded, self.rows = pinned_sources()
        self.raw_csv, self.plain_csv = self.files[SOURCE], self.decoded[SOURCE]
        self.battle_ready = True
        self.visits, self.native_decoded, self.path_copies = [], [], []
        self.getcwd = self.u32(BASE + 0x170428)
        self.vm.mem_map(self.getcwd & ~4095, 4096, UC_PROT_READ | UC_PROT_EXEC)
        self.vm.mem_map(self.battle, 0x145000, UC_PROT_READ | UC_PROT_WRITE)
        self.vm.mem_protect(0x59d000, 4096, UC_PROT_READ | UC_PROT_WRITE)
        self.vm.mem_write(BASE + 0x19ddf0, struct.pack('<I', 1))
        for address in [self.getcwd, *(BASE + r for r in (
                0x2530, 0x27b0, 0x147af7, 0x147a95, 0x1480b4, 0x147e23,
                0x15ada3, 0x15aaaa, 0x15ad35))]:
            self.hooks.append(self.vm.hook_add(UC_HOOK_CODE, self._service,
                                             begin=address, end=address))
        for rva in (0x54720, 0x54859, 0x110e52, 0x120650, 0x1207c9):
            self.hooks.append(self.vm.hook_add(UC_HOOK_CODE, self._battle_visit,
                                             begin=BASE+rva, end=BASE+rva))
        NativeWorldUIResource._check_decompression(self, self.raw_csv, self.plain_csv)
        self.call(0x546e0, this=self.reader)
        self.vm.reg_write(UC_X86_REG_ESP, SP)
        self.vm.reg_write(UC_X86_REG_EBX, self.reader)
        self.run(0x110bb9, 0x110bec)
        if self.vm.reg_read(UC_X86_REG_ESP) != SP:
            raise AssertionError('Battle CSV native caller stack changed')
        self.records = self.u32(self.reader + 0x121f0)
        self.reader_snapshot = bytes(self.vm.mem_read(self.records, STRIDE * CAPACITY))
        # Execute only the bounded name-registry constructor island. Other
        # manager construction is not certified by this resource oracle.
        self.vm.reg_write(UC_X86_REG_ESI, self.manager)
        self.vm.reg_write(UC_X86_REG_EBP, 0)
        self.run(0x11f4ef, 0x11f55c)
        if self.vm.reg_read(UC_X86_REG_ESP) != SP - 4:
            raise AssertionError('Name-registry constructor boundary changed')
        self.names = self.u32(self.manager + 0x14)
        self.vm.mem_write(self.manager + 8, struct.pack('<I', BANK))
        self.preloaded = False
        self.preload_attempted = False
        self.control_initialized = False
        self.control_attempted = False
        self.renderer_attempted = False

    def _battle_visit(self, vm, address, size, context):
        self.visits.append(address - BASE)

    def _service(self, vm, address, size, context):
        if not self.battle_ready:
            return super()._service(vm, address, size, context)
        rva = address - BASE
        sp = vm.reg_read(UC_X86_REG_ESP)
        arg = lambda i: self.u32(sp + 4 + i * 4)
        result, cleanup = 0, 0
        if rva == 0x2530:
            path = self.string(arg(0))
            if path != CWD + b'\\Data2\\Patch\\\\FightComm3.csv':
                raise AssertionError('Unqualified battle CSV path: ' + repr(path))
            self.opens.append(path)
            result, cleanup = 0x82000000, 4
            self.handles[result] = [self.plain_csv.replace(b'\r\n', b'\n'), 0]
        elif rva == 0x147e23:
            if (arg(0), arg(1)) not in ((STRIDE, CAPACITY), (0x100, 1)):
                raise AssertionError('Unqualified battle calloc')
            result = self.allocate(arg(0) * arg(1))
        elif rva == 0x14716f:
            path = self.string(arg(0)).decode('ascii').replace('\\', '/').lower()
            prefix = CWD.decode().replace('\\', '/').lower() + '/'
            path = path[len(prefix):] if path.startswith(prefix) else path
            if self.string(arg(1)) != b'rb' or path not in set(ASSETS) | {p[:-1] for p in ASSETS}:
                raise AssertionError('Unqualified battle ROM open: ' + path)
            self.attempts.append(path)
            if path in self.files:
                self.opens.append(path)
                result = 0x80000000 + 4 * len(self.opens)
                self.handles[result] = [self.files[path], 0]
                self.active_name = path
        elif address == self.getcwd or rva in (0x27b0, 0x147af7, 0x147a95, 0x1480b4):
            return NativeWorldUIResource._service(self, vm, address, size, context)
        else:
            return super()._service(vm, address, size, context)
        vm.reg_write(UC_X86_REG_EAX, result)
        vm.reg_write(UC_X86_REG_ESP, sp + 4 + cleanup)
        vm.reg_write(UC_X86_REG_EIP, self.u32(sp))

    def preload(self):
        if self.preload_attempted:
            raise ValueError('Fresh preload only; reload is not qualified')
        self.preload_attempted = True
        self.vm.reg_write(UC_X86_REG_ESP, SP)
        self.vm.reg_write(UC_X86_REG_ESI, self.battle)
        self.vm.reg_write(UC_X86_REG_EBP, self.manager)
        self.vm.reg_write(UC_X86_REG_EDI, 0)
        self.run(0x110df2, 0x110e72, instruction_limit=500000000, timeout_us=120000000)
        if self.vm.reg_read(UC_X86_REG_ESP) != SP:
            raise AssertionError('Battle preload stack changed')
        handles = [self.u32(self.records + STRIDE * i) for i in range(CAPACITY)]
        if any(handle >= self.u32(self.names + 0x404) for handle in handles):
            raise AssertionError('Battle preload did not bind every runtime handle')
        self.preloaded = True
        return handles

    def _prepare_renderer(self):
        if not self.preloaded or self.renderer_attempted:
            raise ValueError('Renderer requires fresh completed preload')
        self.renderer_attempted = True
        self.vm.mem_map(RENDERER, 0x291000, UC_PROT_READ | UC_PROT_WRITE)
        self._prepare_graphics_services()
        for rva in (0x1aa10, 0x1afe0, 0x1b560, 0x11149b, 0x1114aa,
                    0x11fbf0, 0x11da10, 0x11db47):
            self.hooks.append(self.vm.hook_add(UC_HOOK_CODE, self._battle_visit,
                                             begin=BASE+rva, end=BASE+rva))
        self.call(0x1aa10, SURFACE, 0, BANK, this=RENDERER)
        self.vm.mem_write(self.manager + 0xc, struct.pack('<I', RENDERER))

    def _prepare_graphics_services(self):
        if self.os_apis:
            return
        self.os_apis = {0x775b3420: 'initialize', 0x775a43e0: 'enter',
                        0x775a3460: 'leave', 0x750481f0: 'set_rect',
                        0x75047f20: 'intersect_rect'}
        for pointer in self.os_apis:
            self.vm.mem_map(pointer & ~4095, 4096, UC_PROT_READ | UC_PROT_EXEC)
            self.hooks.append(self.vm.hook_add(UC_HOOK_CODE, self._service,
                                             begin=pointer, end=pointer))

    def initialize_control_strip(self):
        if not self.preloaded or self.control_attempted:
            raise ValueError('Control initialization requires fresh completed preload')
        self.control_attempted = True
        self._prepare_renderer()
        strip = self.manager + 0xa7fbc80
        self.vm.mem_map(strip & ~4095, 8192, UC_PROT_READ | UC_PROT_WRITE)
        self.vm.mem_write(strip - 16, b'\xa5' * 0x70)
        self.vm.reg_write(UC_X86_REG_ESP, SP)
        self.vm.reg_write(UC_X86_REG_EBP, self.battle)
        self.vm.reg_write(UC_X86_REG_ESI, self.manager)
        # Independent initializer island, consuming the table produced above.
        self.run(0x11149b, 0x1114af)
        if self.vm.reg_read(UC_X86_REG_ESP) != SP:
            raise AssertionError('Battle control caller stack changed')
        self.control_initialized = True
        return bytes(self.vm.mem_read(strip, 0x40))
