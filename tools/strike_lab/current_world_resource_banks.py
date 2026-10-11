"""Original double-bank world resource lifecycle in a bounded offline VM.

No live renderer, client process or network. Native constructors, bank binding,
checkpoint and switch functions execute unchanged with explicit RGB555 input.
Cold preload executes in the VM; progress timing is an explicit clock fixture,
not a claim of a live progress screen or graphics-device acceptance.
"""
import struct
import hashlib
import re

from .current_role_doll_resources import NativeRoleDollResources, BANK, BASE, ROOT
from .current_indoor_resources import SURFACE
from .omega_assets import decode_csvz
from unicorn import UC_HOOK_CODE, UC_PROT_READ, UC_PROT_WRITE, UC_PROT_EXEC
from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_ESP, UC_X86_REG_EIP

SECOND_BANK = 0x11400000
MANAGER = 0x11800000
RENDERER = 0x11c00000
BANK_STRIDE = 0xad610
CWD = b'C:\\god2-fixture'
CSV_SOURCES = {
    'data2/patch/drvdoll.csv': (
        '502df5822b376ac57c4bf8460bf6d646a3cb6d706b1be36396e73bf69ced1042',
        'de9510e0c5b1171e164b407c931b41e7fc3c5a7b5ffa3aba9193a51063f2dd9f'),
    'data2/patch/herodoll.csv': (
        'df2fa65e0b159b18303b2e135cacc690e0e02e4ea12560cacda3f0d8e6ae1359',
        '0ba373ca45d0f4452f1d847fab5f5e194f00501f26a58f082c5352f71fe921c2'),
    'data2/patch/drv.csv': (
        '9af4b2ed4d5b007bfde12f2cff4e9895715903a8ffaf5a356aee011f3fb98f2e',
        '72cd006c121a865e10b7d1e2c655895da16a5e760bad2c8d473bf5663996f6e0'),
    'data/patch/goddoll.csv': (
        '768c3a68cddd1443c5c19207a21b17d00990e596aedd74d27f13d0bde5ef02df',
        '22bedaac6743d190456d5549688019b65415178b7cb8f269156743e7babd0bc1'),
    'data2/patch/eny.csv': (
        '6aa84aeb0399e39e0db27eeebf9bb0f8b274fcbd609e1b83be3542a5d53f294c',
        'e287d331c0c88bdf4342888aa2e8d839c253d8a14910dee2c04f95436075d863'),
    'data2/patch/npc.csv': (
        'b6afccc3a66e8b3b6f291e62cbdb221b370e1bb5146ed6c2c6f2dd94ee38777f',
        '2b6f631eb8b5f34333289c958f07e808d9985ebc21c27c6f6ac48f4d1731df63'),
}
NPC_ASSETS = {
    'data2/rom/npc/npc2401.romz': (
        '4e728a03487842cd09334603dff50e7f52eef3e7c89401597866048db0123e02',
        'd35c29b93dde80c499feafd4fb46e2a609544eed1f6cc5db4891cfff05c4b512'),
    'data2/rom/npc/npc2721.romz': (
        '0c854a40de383269f6dde53cfc87a94d6d27b0cf590357cb6221ca4837110eda',
        '4977df017039bc671199962032d041fc6f3e97d655b3ea7ec546d43801688cae'),
    'data2/rom/npc/npc2643.romz': (
        'ef4625d222b9dc3e0cf182fedfc72ffc4d70e69f4c716c8796d4ecbc973fdc08',
        '92cb6316d08ce79b496bd7deb0f2aacc78fc8afc918e6872f95fbfc28bba7f1d'),
}


class NativeWorldResourceBanks(NativeRoleDollResources):
    second_bank_address = SECOND_BANK
    renderer_address = RENDERER

    def __init__(self, *, manager=MANAGER):
        super().__init__()
        vm = self.vm
        self.manager = manager
        for relative, (raw_sha, plain_sha) in NPC_ASSETS.items():
            raw = (ROOT.parent/'God2'/relative).read_bytes()
            plain = decode_csvz(raw, limit=1024*1024)
            if (hashlib.sha256(raw).hexdigest() != raw_sha
                    or hashlib.sha256(plain).hexdigest() != plain_sha):
                raise ValueError('Pinned preload NPC changed: '+relative)
            self.files[relative], self.decoded[relative] = raw, plain
        self.csv_files, self.csv_sources = {}, {}
        for relative, (raw_sha, plain_sha) in CSV_SOURCES.items():
            raw = (ROOT.parent/'God2'/(relative+'z')).read_bytes()
            plain = decode_csvz(raw, limit=1024*1024)
            if (hashlib.sha256(raw).hexdigest() != raw_sha
                    or hashlib.sha256(plain).hexdigest() != plain_sha):
                raise ValueError('Pinned bank CSV source changed: '+relative)
            # Read-only plain view; verify its bytes with the actual decompressor.
            self.csv_files[relative] = plain.replace(b'\r\n', b'\n')
            self.csv_sources[relative] = plain
            context, output = self.allocate(0xd440), self.allocate(len(plain)+3)
            handle = 0x80010000
            self.handles[handle] = [raw, 0]
            self.call(0x1760, this=context)
            self.call(0x1ec0, handle, output, this=context)
            if bytes(vm.mem_read(output, len(plain))) != plain:
                raise AssertionError('Original bank CSV decompression mismatch')
            self.handles.pop(handle)
            self.call(0x17b0, this=context)
        self.csv_attempts, self.csv_reads = [], []
        self.cwd_calls = 0
        self.tick_count, self.tick_calls = 0, []
        for page in (0x59d000, 0x5b9000):
            vm.mem_protect(page, 4096, UC_PROT_READ | UC_PROT_WRITE)
        vm.mem_write(0x59ddf0, struct.pack('<I', 1))
        self.get_directory = self.u32(0x570428)
        if self.get_directory != 0x76601060:
            raise AssertionError('Unexpected current directory import')
        vm.mem_map(self.get_directory & ~4095, 4096, UC_PROT_READ | UC_PROT_EXEC)
        self.get_tick_count = self.u32(0x5707bc)
        if self.get_tick_count != 0x74147860:
            raise AssertionError('Unexpected tick-count import')
        vm.mem_map(self.get_tick_count & ~4095, 4096, UC_PROT_READ | UC_PROT_EXEC)
        self.bank_service_rvas = {0x147af7, 0x147a95, 0x147e23, 0x1480b4,
                                  0x15aebe, 0x15ada3, 0x15ad35, 0x146cf7}
        for address in (self.get_directory, self.get_tick_count,
                        *(BASE+rva for rva in sorted(self.bank_service_rvas))):
            self.hooks.append(vm.hook_add(UC_HOOK_CODE, self._service,
                                          begin=address, end=address))
        vm.mem_map(self.second_bank_address, 0x2a3000, UC_PROT_READ | UC_PROT_WRITE)
        manager_page = manager & ~4095
        vm.mem_map(manager_page, (manager-manager_page+0x170000+4095) & ~4095,
                   UC_PROT_READ | UC_PROT_WRITE)
        vm.mem_map(self.renderer_address, 0x291000, UC_PROT_READ | UC_PROT_WRITE)
        self.os_apis = {0x775b3420: 'initialize', 0x775a43e0: 'enter',
                        0x775a3460: 'leave', 0x750481f0: 'set_rect',
                        0x75047f20: 'intersect_rect'}
        for pointer in self.os_apis:
            vm.mem_map(pointer & ~4095, 4096, UC_PROT_READ | UC_PROT_EXEC)
            self.hooks.append(vm.hook_add(UC_HOOK_CODE, self._service,
                                          begin=pointer, end=pointer))
        self.bank_visits = []
        for rva in (0x60810, 0x608d0, 0x60a10, 0x60b10, 0x619d0,
                    0x1fdf0, 0x2d9a0, 0x2d9c0, 0x28880, 0x288e0,
                    0x60b80, 0x63bf0, 0x51f20, 0x15a47e, 0x15a6a6,
                    0x63260, 0x63f40, 0x552c0, 0x637b0, 0x61ad0,
                    0x616a0, 0x60c60, 0x5e850, 0x5f0e0, 0x5eec0,
                    0x606d0, 0x60731, 0x2d9e0, 0x289b0):
            self.hooks.append(vm.hook_add(UC_HOOK_CODE, self._bank_visit,
                                          begin=BASE+rva, end=BASE+rva))
        self.call(0x29700, this=self.second_bank_address)
        self.call(0x297e0, self.bank_capacity, this=self.second_bank_address)
        self.call(0x2b180, SURFACE, this=self.second_bank_address)
        self.call(0x27400, this=SURFACE)
        self.call(0x1aa10, SURFACE, 0, BANK, this=self.renderer_address)
        self.call(0x60810, this=self.manager)
        # Native binding's fifth argument is an optional owner/context pointer.
        self.call(0x60a10, SURFACE, self.renderer_address, BANK,
                  self.second_bank_address, 0, this=self.manager)

    def _bank_visit(self, vm, address, size, context):
        self.bank_visits.append(address-BASE)

    def _service(self, vm, address, size, context):
        rva = address-BASE
        if address not in (getattr(self, 'get_directory', -1),
                           getattr(self, 'get_tick_count', -1)) and rva not in (
                0x14716f, 0x147af7, 0x147a95, 0x147e23, 0x1480b4, 0x146cf7):
            return super()._service(vm, address, size, context)
        sp = vm.reg_read(UC_X86_REG_ESP)
        ret = self.u32(sp)
        arg = lambda index: self.u32(sp+4+4*index)
        result, cleanup = 0, 0
        if address == getattr(self, 'get_tick_count', -1):
            if ret != BASE+0x606db or not 0 <= self.tick_count <= 0xffffffff:
                raise AssertionError('Unqualified progress clock call')
            result = self.tick_count
            self.tick_calls.append(result)
        elif address == getattr(self, 'get_directory', -1):
            if arg(0) != 260 or arg(1) != 0x5b93c4 or ret != BASE+0x12f569:
                raise AssertionError('Unqualified bank current-directory call')
            vm.mem_write(arg(1), CWD+b'\0')
            result, cleanup = len(CWD), 8
            self.cwd_calls += 1
        elif rva == 0x147af7:
            fmt = self.string(arg(1))
            if fmt == b'%s%s':
                value = self.string(arg(2))+self.string(arg(3))
            elif fmt == b'%s\\%s' and ret == BASE+0x12f5a9:
                value = self.string(arg(2))+b'\\'+self.string(arg(3))
            elif arg(1) in (0x58a6cc, 0x58a6ac, 0x58a68c, 0x58a668) and arg(2) in (0, 1):
                value = fmt % arg(2)
            else:
                raise AssertionError('Unqualified bank path format')
            if len(value) >= 260:
                raise AssertionError('Bank path exceeds buffer')
            vm.mem_write(arg(0), value+b'\0')
            result = len(value)
        elif rva == 0x146cf7:
            value = self.string(arg(1))
            if ret != BASE+0x2d9fd or b'%' in value or len(value) >= 512:
                raise AssertionError('Unqualified bank diagnostic format')
            vm.mem_write(arg(0), value+b'\0')
            result = len(value)
        elif rva == 0x147e23:
            expected = {BASE+0x6380c: (136, 120), BASE+0x51f9a: (44, 918)}
            if expected.get(ret) != (arg(0), arg(1)):
                raise AssertionError('Unqualified bank calloc')
            result = self.allocate(arg(0)*arg(1))
        elif rva == 0x1480b4:
            value = self.string(arg(0)).lstrip(b' \t\r\n\v\f')
            if self.string(arg(1)) != b'%d':
                raise AssertionError('Unqualified bank numeric conversion')
            match = re.match(rb'[+-]?[0-9]+', value)
            if match:
                number = int(match[0])
                if not -(1 << 31) <= number < (1 << 31):
                    raise AssertionError('Bank numeric conversion exceeds int32')
                vm.mem_write(arg(2), struct.pack('<i', number))
                result = 1
            else:
                result = 0 if value else 0xffffffff
        elif rva == 0x147a95:
            if (ret not in (BASE+0x519e8, BASE+0x51a6e, BASE+0x51ab0)
                    or arg(1) not in (512, 4096) or arg(2) not in self.handles):
                raise AssertionError('Unqualified bank fgets')
            data, position = self.handles[arg(2)]
            end = data.find(b'\n', position)
            end = len(data) if end < 0 else end+1
            if end-position >= arg(1):
                raise AssertionError('Bank CSV row exceeds input buffer')
            if position < len(data):
                vm.mem_write(arg(0), data[position:end]+b'\0')
                self.handles[arg(2)][1] = end
                result = arg(0)
            self.csv_reads.append((arg(2), end-position))
        else:
            path = self.string(arg(0)).decode('ascii').replace('\\', '/').lower()
            prefix = CWD.decode().replace('\\', '/').lower()+'/'
            relative = path[len(prefix):] if path.startswith(prefix) else path
            if relative.startswith('./'):
                relative = relative[2:]
            if relative in NPC_ASSETS:
                if self.string(arg(1)) != b'rb':
                    raise AssertionError('NPC preload view is read-only')
                self.active_name = relative
                self.opens.append(relative)
                result = 0x82000000+4*len(self.opens)
                self.handles[result] = [self.files[relative], 0]
                self.calls.add(rva)
                vm.reg_write(UC_X86_REG_EAX, result)
                vm.reg_write(UC_X86_REG_ESP, sp+4)
                vm.reg_write(UC_X86_REG_EIP, ret)
                return
            if relative not in self.csv_files and not (
                    relative.endswith('z') and relative[:-1] in self.csv_files):
                return super()._service(vm, address, size, context)
            mode = self.string(arg(1))
            self.csv_attempts.append((relative, mode))
            if relative in self.csv_files:
                if mode != b'rt':
                    raise AssertionError('Bank CSV view is text-read only')
                self.opens.append(relative)
                result = 0x81000000+4*len(self.opens)
                self.handles[result] = [self.csv_files[relative], 0]
            elif mode != b'rb':
                raise AssertionError('Unexpected compressed view mode')
        self.calls.add(rva)
        vm.reg_write(UC_X86_REG_EAX, result)
        vm.reg_write(UC_X86_REG_ESP, sp+4+cleanup)
        vm.reg_write(UC_X86_REG_EIP, ret)

    @property
    def active_bank(self):
        return struct.unpack('<i', self.vm.mem_read(self.manager+0x16ce18, 4))[0]

    def select_scene(self, area, scene):
        if (type(area) is not int or type(scene) is not int
                or not 0 <= area <= 65535 or not 0 <= scene <= 65535):
            raise ValueError('Native bank selectors must be WORDs')
        return self.call(0x619d0, area, scene, this=self.manager)

    def checkpoint(self):
        self.call(0x60b10, this=self.manager)

    def reload_character_tables(self):
        return self.call(0x60b80, this=self.manager)

    def bank_state(self, bank):
        if type(bank) is not int or bank not in (0, 1):
            raise ValueError('Bank index must be zero or one')
        block = self.manager+0x121f8+bank*BANK_STRIDE
        pointer, next_slot, saved_slot, area, scene = struct.unpack(
            '<I4H', self.vm.mem_read(block, 12))
        allocator = pointer+0x2a2800
        segment = self.u32(allocator+0x304)
        return {'pointer': pointer, 'next_slot': next_slot, 'saved_slot': saved_slot,
                'area': area, 'scene': scene, 'segment': segment,
                'used': self.u32(allocator+8+12*segment)}
