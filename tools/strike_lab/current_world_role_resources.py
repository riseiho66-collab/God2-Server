"""Original world HeroDoll cache/path/ROM chain in a bounded offline VM.

The input table is original-loader output from AppearanceResources. Only its
allocation-backed container is transferred; game lookups/cache writes/loaders
execute native instructions. No process, UI, socket or graphics device runs.
"""
import csv
import hashlib
import io
import struct

from .current_appearance_resources import (
    AppearanceResources, BANK as WORLD_BANK, RECORDS, INDEX, NODES, STRINGS)
from .current_role_doll_resources import (
    NativeRoleDollResources, BANK as ROM_BANK, ASSETS, DIRECTORY, BASE, ROOT)
from .current_indoor_resources import SP, SCRATCH
from .omega_assets import decode_csvz
from unicorn import UC_HOOK_CODE, UC_HOOK_MEM_WRITE, UC_PROT_READ, UC_PROT_WRITE, UC_PROT_EXEC
from unicorn.x86_const import (UC_X86_REG_EAX, UC_X86_REG_EBX, UC_X86_REG_ESI,
                              UC_X86_REG_EBP, UC_X86_REG_ESP, UC_X86_REG_EIP)

COUNTER = 0x3800000
CWD = b'C:\\god2-fixture'
COMPONENT_MANAGER = 0x4000000
ACTOR, WORLD = 0x7800000, 0x8000000
WORLD_COMPONENTS = WORLD+0xa7e04d0
EXTRA_ASSETS = {
    'r01b000.romz': ('10d0ad29845742074c45aa41751f49064c9f7a2005b3b57dee8066d049c2bf8d',
                    '200cd8b2ac437d7c1967577d0065760fa1703eb52222724c5c210095c7ab65d7'),
    'r02b000.romz': ('950e88b96abfdd7dce5850b18d5f067f4f06e8aa3230d51d4d8f786910b2fe64',
                    '8e037893bf96e55cdd8c14a97cfe9bbae9f5ab412194abc6d13efa44ddf6ab98'),
    'r02w800.romz': ('ff1329300e1db6e9c56a7151404db44789bec811dd7010b25627a6a7b86b0b77',
                    '698427fe8dc1421a9cf3313695e984b2294d36eaf61e61d0ff06cc9b4442cd9a'),
    'r02b600.romz': ('729e3df1a74a137ab9795e823a7006ce3da177ca8b74f879f10e1db1c80b6a2f',
                    '8279e9eefd5e1a7cc01679ff0e502051ba976a5f253d0d0dd4b0d46f84ffc331'),
    'r02f102.romz': ('f2c65947df324f2e5407828c569e9896e5ccf14592f058ff13a40a4b53b412c1',
                    'e2b4b2a7bb4410b6fd50d9bff42c4a0903233d19d54ce55456c43f82ebdbdf24'),
}


class NativeWorldRoleResources(NativeRoleDollResources):
    def __init__(self, appearance=None):
        super().__init__()
        appearance = appearance if appearance is not None else AppearanceResources()
        self.record_by_key = dict(appearance.by_key)
        self.record_baseline = bytes(appearance.vm.mem_read(RECORDS, 918*44))
        if any(self.record_baseline[i*44+30:i*44+32] != b'\xff\xff' for i in range(918)):
            raise ValueError('Expected source-backed unloaded HeroDoll records')
        for address, size in ((WORLD_BANK, 0x60000), (RECORDS, 0x10000),
                              (INDEX, 0x10000), (NODES, 0x10000), (STRINGS, 0x10000)):
            self.vm.mem_map(address, size, UC_PROT_READ | UC_PROT_WRITE)
            self.vm.mem_write(address, bytes(appearance.vm.mem_read(address, size)))
            if address in (INDEX, NODES, STRINGS):
                self.vm.mem_protect(address, size, UC_PROT_READ)
        self.vm.mem_map(COUNTER, 4096, UC_PROT_READ | UC_PROT_WRITE)
        self.vm.mem_write(COUNTER, b'\0\0'+b'\xa5'*14)
        self.counter = COUNTER
        self.component_manager_ready = False
        self.actor_ready = False
        self.asset_names = {DIRECTORY+name: name for name in ASSETS}
        self.cache_writes, self.wrapper_visits, self.full_paths = [], [], []
        self.cwd_calls = 0
        self.hooks.append(self.vm.hook_add(UC_HOOK_MEM_WRITE, self._cache_write,
                                          begin=RECORDS, end=RECORDS+0xffff))
        for page in (0x59d000, 0x5b9000):
            self.vm.mem_protect(page, 4096, UC_PROT_READ | UC_PROT_WRITE)
        self.vm.mem_write(0x59ddf0, struct.pack('<I', 1))
        self.get_directory = self.u32(0x570428)
        if self.get_directory != 0x76601060:
            raise AssertionError('Pinned GetCurrentDirectoryA identity changed')
        self.vm.mem_map(self.get_directory & ~4095, 4096, UC_PROT_READ | UC_PROT_EXEC)
        for address in (BASE+0x158e89, BASE+0x15ad35, BASE+0x147af7,
                        BASE+0x1480b4, self.get_directory):
            self.hooks.append(self.vm.hook_add(UC_HOOK_CODE, self._service,
                                              begin=address, end=address))
        for rva in (0x63de0, 0x526c0, 0x526f0, 0x52680, 0x12f550):
            self.hooks.append(self.vm.hook_add(UC_HOOK_CODE, self._wrapper_visit,
                                              begin=BASE+rva, end=BASE+rva))

    def _wrapper_visit(self, vm, address, size, context):
        self.wrapper_visits.append(address-BASE)

    def _cache_write(self, vm, access, address, size, value, context):
        ordinal, offset = divmod(address-RECORDS, 44)
        if not (ordinal < 918 and offset == 30 and size == 2
                and vm.reg_read(UC_X86_REG_EIP) == BASE+0x526a7):
            raise AssertionError('Non-cache HeroDoll record write')
        self.cache_writes.append((ordinal, value))

    @property
    def next_slot(self):
        return struct.unpack('<H', self.vm.mem_read(self.counter, 2))[0]

    def cache(self, key):
        return struct.unpack('<H', self.vm.mem_read(self.record_by_key[key]+30, 2))[0]

    def load_key(self, *key):
        if (len(key) != 5 or any(not isinstance(n, int) or not 0 <= n <= 255 for n in key)
                or key[1] > 3 or key[4] > 2):
            raise ValueError('Qualified five-byte component/action key required')
        return self.call(0x63de0, ROM_BANK, self.counter, *key, this=WORLD_BANK) & 0xffff

    def _load_component_sources(self):
        for name, (raw_hash, plain_hash) in EXTRA_ASSETS.items():
            raw = (ROOT.parent / 'God2' / DIRECTORY / name).read_bytes()
            plain = decode_csvz(raw, limit=1024*1024)
            if (hashlib.sha256(raw).hexdigest() != raw_hash
                    or hashlib.sha256(plain).hexdigest() != plain_hash):
                raise AssertionError('Pinned component ROM changed: '+name)
            self.files[DIRECTORY+name], self.decoded[name] = raw, plain
            self.asset_names[DIRECTORY+name] = name
        mount_path = 'data2/rom/drv/drv5477.romz'
        raw = (ROOT.parent / 'God2' / mount_path).read_bytes()
        plain = decode_csvz(raw, limit=1024*1024)
        if (hashlib.sha256(raw).hexdigest() != '031ef0c09c44da5c301fedb7dbc31e85249bec92607b6dc115b859ff861164e5'
                or hashlib.sha256(plain).hexdigest() != '30c7809204865213ce19e234cf2e390f3aaefb66400e83881a4aa49467ce208e'):
            raise AssertionError('Pinned retained mount ROM changed')
        self.files[mount_path], self.decoded['drv5477.romz'] = raw, plain
        # The actual Drv row names .ROM. Keep that absent spelling qualified
        # too; original 29820 chooses the compressed .ROMZ on a successful run.
        if (ROOT.parent / 'God2' / mount_path[:-1]).exists():
            raise AssertionError('Unexpected uncompressed retained mount source')
        self.asset_names[mount_path] = self.asset_names[mount_path[:-1]] = 'drv5477.romz'

    def _prepare_component_manager(self):
        self._load_component_sources()
        raw = (ROOT.parent / 'God2/Data2/Patch/DrvDoll.csvZ').read_bytes()
        plain = decode_csvz(raw, limit=1024*1024)
        if (hashlib.sha256(raw).hexdigest() != '502df5822b376ac57c4bf8460bf6d646a3cb6d706b1be36396e73bf69ced1042'
                or hashlib.sha256(plain).hexdigest() != 'de9510e0c5b1171e164b407c931b41e7fc3c5a7b5ffa3aba9193a51063f2dd9f'):
            raise AssertionError('Pinned DrvDoll source changed')
        rows = list(csv.reader(io.StringIO(plain.decode('latin1'))))
        start, count = int(rows[0][2]), int(rows[0][4])
        self.accessory_rows = rows[start-1:]
        if (start, count, len(self.accessory_rows)) != (26, 120, 120):
            raise AssertionError('Unexpected DrvDoll source boundaries')
        self.accessory_records = self.allocate(count*136)
        self.vm.mem_write(WORLD_BANK+0x24f74, struct.pack('<I', self.accessory_records))
        self.vm.mem_write(WORLD_BANK+8, struct.pack('<H', 5))
        for line, row in zip(plain.splitlines(keepends=True)[start-1:], self.accessory_rows):
            if len(row[4].encode('latin1')) >= 128 or len(line) >= 4096:
                raise AssertionError('DrvDoll field bound')
            self.vm.mem_write(SCRATCH, line+b'\0')
            self.call(0x51be0, SCRATCH, this=WORLD_BANK)
            self.vm.reg_write(UC_X86_REG_ESP, SP)
            self.vm.reg_write(UC_X86_REG_ESI, WORLD_BANK)
            self.vm.reg_write(UC_X86_REG_EBX, count)
            self.run(0x6382e, 0x63947)
            if self.vm.reg_read(UC_X86_REG_ESP) != SP:
                raise AssertionError('DrvDoll native row stack mismatch')
        self.vm.mem_map(COMPONENT_MANAGER, 0x170000, UC_PROT_READ | UC_PROT_WRITE)
        self.vm.mem_write(COMPONENT_MANAGER+0x682e0,
                          bytes(self.vm.mem_read(WORLD_BANK, 0x60000)))
        self.vm.mem_write(COMPONENT_MANAGER+0x121f8, struct.pack('<I', ROM_BANK))
        self.vm.mem_write(COMPONENT_MANAGER+0x121fc,
                          struct.pack('<H', self.next_slot)+b'\xa5'*14)
        self.counter = COMPONENT_MANAGER+0x121fc
        self.component_manager_ready = True

    @staticmethod
    def validate_component_block(block):
        if (len(block) != 8 or block[0] not in (0, 1)
                or block[2] != block[0] or block[4] != block[0]
                or block[6] != (0x80 | block[0]) or block[5] or block[7]
                or block[1] & 31 or block[3] & 31
                or block[1] >> 5 > 6 or block[3] >> 5 > 6):
            raise ValueError('Only proven zero-selector preview component blocks')

    def load_components(self, block):
        self.validate_component_block(block)
        if not self.component_manager_ready:
            self._prepare_component_manager()
        self.vm.mem_write(SCRATCH+0x2000, bytes(block))
        self.vm.mem_write(SCRATCH+0x3000, b'\xa5'*28)
        self.call(0x61270, 0, 0, SCRATCH+0x2000, SCRATCH+0x3008, this=COMPONENT_MANAGER)
        if (bytes(self.vm.mem_read(SCRATCH+0x3000, 8)) != b'\xa5'*8
                or bytes(self.vm.mem_read(SCRATCH+0x3014, 8)) != b'\xa5'*8
                or bytes(self.vm.mem_read(SCRATCH+0x2000, 8)) != bytes(block)):
            raise AssertionError('Component output/input canary changed')
        return struct.unpack('<6H', self.vm.mem_read(SCRATCH+0x3008, 12))

    def consume_world_appearance(self, body, *, override=False):
        if (len(body) != 36 or body[6] not in (0, 27) or body[32:34] != b'\0\0'
                or (struct.unpack_from('<I', body)[0] >> 16) & 0x7f):
            raise ValueError('Only qualified normal 2A appearance input')
        if body[6] == 0:
            self.validate_component_block(body[12:20])
        else:
            block = bytearray(body[12:20])
            block[1] &= 31
            block[3] &= 31
            if block != bytes.fromhex('0100010001603100') or body[13] >> 5 > 6 or body[15] >> 5 > 6:
                raise ValueError('Outside retained mounted appearance subset')
        if not self.component_manager_ready:
            self._prepare_component_manager()
        vm = self.vm
        if not self.actor_ready:
            vm.mem_map(ACTOR, 0x6000, UC_PROT_READ | UC_PROT_WRITE)
            vm.mem_map(WORLD_COMPONENTS & ~4095, 4096, UC_PROT_READ | UC_PROT_WRITE)
            vm.mem_map((WORLD+0x1539ad70) & ~4095, 4096, UC_PROT_READ | UC_PROT_WRITE)
            self.actor_ready = True
        self.call(0xff370, this=WORLD_COMPONENTS)
        vm.mem_write(ACTOR, b'\xa5'*0x6000)
        vm.mem_write(SP+0x28, bytes(body))
        vm.mem_write(WORLD+0x1539ad70, bytes([0x10 if override else 0]))
        vm.reg_write(UC_X86_REG_ESP, SP)
        vm.reg_write(UC_X86_REG_EBP, ACTOR)
        vm.reg_write(UC_X86_REG_EBX, WORLD)
        vm.reg_write(UC_X86_REG_ESI, COMPONENT_MANAGER)
        end = BASE+0x68558
        hook = vm.hook_add(UC_HOOK_CODE, lambda uc, address, size, data: uc.emu_stop(),
                          begin=end, end=end)
        try:
            self.run(0x68315, 0x68558)
        finally:
            vm.hook_del(hook)
        if (vm.reg_read(UC_X86_REG_ESP) != SP
                or bytes(vm.mem_read(SP+0x28, 36)) != bytes(body)
                or bytes(vm.mem_read(ACTOR+0x4594, 0x6000-0x4594)) != b'\xa5'*(0x6000-0x4594)):
            raise AssertionError('World appearance stack/input/actor guard changed')
        handles = tuple(struct.unpack('<H', vm.mem_read(WORLD_COMPONENTS+4+6*i, 2))[0]
                        for i in range(4))
        variants = tuple(vm.mem_read(WORLD_COMPONENTS+8+6*i, 1)[0] for i in range(4))
        return handles, variants

    def _service(self, vm, address, size, context):
        rva = address-BASE
        if address not in (BASE+0x158e89, BASE+0x147af7, BASE+0x14716f, BASE+0x1480b4,
                           getattr(self, 'get_directory', -1)):
            return super()._service(vm, address, size, context)
        sp = vm.reg_read(UC_X86_REG_ESP)
        arg = lambda i: self.u32(sp+4+4*i)
        result, cleanup = 0, 0
        if address == getattr(self, 'get_directory', -1):
            if arg(0) != 260 or arg(1) != 0x5b93c4 or self.u32(sp) != BASE+0x12f569:
                raise AssertionError('Unexpected current-directory caller')
            vm.mem_write(arg(1), CWD+b'\0')
            result, cleanup = len(CWD), 8
            self.cwd_calls += 1
        elif rva == 0x1480b4:
            if self.string(arg(1)) != b'%d' or not self.string(arg(0)).strip().isdigit():
                raise AssertionError('Unexpected numeric DrvDoll field')
            vm.mem_write(arg(2), struct.pack('<I', int(self.string(arg(0)))))
            result = 1
        elif rva == 0x158e89:
            if self.string(arg(1)) != b'r%d%c%d%02d':
                raise AssertionError('Unexpected HeroDoll format')
            values = [arg(i) for i in (2, 3, 4, 5)]
            if any(n > 255 for n in values):
                raise AssertionError('HeroDoll format argument bound')
            binary, component, category, ordinal = values
            self.cstring(arg(0), f'r{binary}{chr(component)}{category}{ordinal:02d}'.encode('ascii'))
        elif rva == 0x147af7:
            fmt = self.string(arg(1))
            if fmt == b'%s%s':
                path = self.string(arg(2)) + self.string(arg(3))
            elif fmt == b'%s\\tmp.%d' and self.u32(sp) == BASE+0x296d:
                number = struct.unpack('<i', struct.pack('<I', arg(3)))[0]
                path = self.string(arg(2))+f'\\tmp.{number}'.encode('ascii')
            else:
                raise AssertionError(f'Unexpected role path format {fmt!r}')
            if len(path) >= 260:
                raise AssertionError('Native path buffer bound')
            vm.mem_write(arg(0), path+b'\0')
            result = len(path)
        else:
            path = self.string(arg(0)).decode('ascii').replace('\\', '/').lower()
            prefix = CWD.decode('ascii').replace('\\', '/').lower()+'/'
            if not path.startswith(prefix) or self.string(arg(1)) != b'rb':
                raise AssertionError('World RoleDoll virtual path/mode mismatch')
            relative = path[len(prefix):]
            if relative not in self.asset_names:
                raise AssertionError('Unqualified world RoleDoll path: '+relative)
            self.active_name = self.asset_names[relative]
            self.full_paths.append(path)
            self.attempts.append(relative)
            if relative in self.files:
                self.opens.append(relative)
                result = 0x80000000+4*len(self.opens)
                self.handles[result] = [self.files[relative], 0]
        self.calls.add(rva)
        vm.reg_write(UC_X86_REG_EAX, result)
        vm.reg_write(UC_X86_REG_ESP, sp+4+cleanup)
        vm.reg_write(UC_X86_REG_EIP, self.u32(sp))
