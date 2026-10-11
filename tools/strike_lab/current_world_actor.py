"""Source-backed actor initialization and scene resource-group lookups.

Runs original scalar writes, group queries and post-preload actor setup.
The cold resource-bank call 682F1..68315 is NOT executed by this oracle.
"""
import csv
import hashlib
import io
import struct

from .current_world_role_resources import (
    NativeWorldRoleResources, ROOT, BASE, WORLD, ACTOR, COMPONENT_MANAGER, WORLD_COMPONENTS)
from .current_indoor_resources import SP, SCRATCH
from .omega_assets import decode_csvz
from .recover_companions import parse_sections
from .current_monster_inventory import parse_enemy_catalog
from unicorn import UC_HOOK_CODE, UC_PROT_READ, UC_PROT_WRITE
from unicorn.x86_const import (UC_X86_REG_EAX, UC_X86_REG_EBX, UC_X86_REG_EBP,
                              UC_X86_REG_EDI, UC_X86_REG_ESI, UC_X86_REG_ESP)
from unicorn.x86_const import UC_X86_REG_EIP

CAT = WORLD+0xa7e05f0
PETDRV = WORLD+0xa7f2e64
UI = WORLD+0xa7f2f6c
MANAGER = WORLD+0xaa364b8
MESSAGES = 0x7000000
OWNER_POISON = 0x30000000
NPC_GROUPS_OFFSET = 0xd2e4a
NPC_AREA_STRIDE = 9941
NPC_GROUP_STRIDE = 142


class NativeWorldActor(NativeWorldRoleResources):
    actor_address = ACTOR
    actor_storage_size = 0x6000

    def __init__(self, appearance=None):
        super().__init__(appearance)
        self._prepare_component_manager()
        self._prepare_actor_sources(copy_manager=COMPONENT_MANAGER)

    def _prepare_actor_sources(self, *, copy_manager=None):
        self._map_rw(WORLD, 4096)
        self._map_rw(WORLD+0xa7e0000, 0x9a000)
        self._map_rw(WORLD+0xaa25000, 0x3000)
        self._map_rw(MANAGER & ~4095, 0x172000)
        self._map_rw((WORLD+0x1539ad70) & ~4095, 4096)
        self._map_rw(self.actor_address, self.actor_storage_size)
        self._map_rw(MESSAGES, NPC_GROUPS_OFFSET+17*NPC_AREA_STRIDE)
        if copy_manager is not None:
            self.vm.mem_write(MANAGER, bytes(self.vm.mem_read(copy_manager, 0x170000)))
        self.counter = MANAGER+0x121fc
        self._load_cat()
        self._load_program_messages()
        self._load_npc_groups()
        self._load_enemy_groups()
        self.vm.mem_write(WORLD+0xaa36480, struct.pack('<I', MESSAGES))
        self.vm.reg_write(UC_X86_REG_EBP, WORLD)
        self.vm.reg_write(UC_X86_REG_EDI, 0x5b5668)
        self._slice(0x64a15, 0x64a59)
        self.vm.reg_write(UC_X86_REG_EBP, WORLD)
        self._slice(0x6506c, 0x650e3)
        self.call(0x64200, this=PETDRV)
        self.vm.reg_write(UC_X86_REG_EBP, WORLD)
        self._slice(0x64ec5, 0x64eeb)
        self.vm.mem_write(WORLD+0xa7e05ec, struct.pack('<I', OWNER_POISON))
        self.visits = []
        for rva in (0x681cf, 0x5aa70, 0x5a000, 0x607d0, 0x68315,
                    0x61270, 0x64280, 0x68120, 0x97fe0):
            self.hooks.append(self.vm.hook_add(UC_HOOK_CODE, self._visit,
                                              begin=BASE+rva, end=BASE+rva))

    def _map_rw(self, address, size):
        first, last = address & ~4095, (address+size+4095) & ~4095
        regions = list(self.vm.mem_regions())
        for page in range(first, last, 4096):
            if not any(start <= page <= end for start, end, _ in regions):
                self.vm.mem_map(page, 4096, UC_PROT_READ | UC_PROT_WRITE)

    def _slice(self, start, stop):
        hook = self.vm.hook_add(UC_HOOK_CODE,
                               lambda vm, address, size, data: vm.emu_stop(),
                               begin=BASE+stop, end=BASE+stop)
        try:
            self.run(start, stop)
        finally:
            self.vm.hook_del(hook)

    def _visit(self, vm, address, size, data):
        self.visits.append(address-BASE)

    def _source(self, relative, raw_sha, plain_sha, *, decoded_limit=1024*1024):
        path = ROOT.parent / 'God2' / relative
        if path.stat().st_size > 1024*1024:
            raise ValueError('Actor source size bound')
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != raw_sha:
            raise ValueError('Actor source identity changed: '+relative)
        plain = decode_csvz(raw, limit=decoded_limit)
        if hashlib.sha256(plain).hexdigest() != plain_sha:
            raise ValueError('Actor decoded identity changed: '+relative)
        return plain

    def _load_cat(self):
        plain = self._source('Data/Patch/Cat.csvZ',
            '9a1fad6c037cb276910b5d1a99a7c7755d8e723fa8dd4d5bc65c4d2c366d5bed',
            'b518ebba78180078a6ac784c7c107d6563d72042eacb51ad0153305040dbe4c0')
        rows = list(csv.reader(io.StringIO(plain.decode('latin1'))))
        start = int(rows[0][2])
        self.cat_rows = rows[start-1:]
        if start != 5 or [int(row[1]) for row in self.cat_rows] != list(range(1, 9)):
            raise ValueError('Unexpected current Cat rows')
        self.call(0x5e0f0, this=CAT)
        self.vm.mem_write(CAT+8, struct.pack('<H', 11))
        for line, row in zip(plain.splitlines(keepends=True)[start-1:], self.cat_rows):
            if any(len(row[i].encode('latin1')) >= 8 for i in (3, 4, 5)):
                raise ValueError('Cat native string bound')
            self.vm.mem_write(SCRATCH, line+b'\0')
            self.call(0x51be0, SCRATCH, this=CAT)
            self.vm.reg_write(UC_X86_REG_ESP, SP)
            self.vm.reg_write(UC_X86_REG_EBX, CAT)
            self._slice(0x5e20a, 0x5e329)
            if self.vm.reg_read(UC_X86_REG_ESP) != SP:
                raise AssertionError('Cat row stack imbalance')
        self.cat_before_localization = bytes(self.vm.mem_read(CAT+0x121ec, 16*44))

    def _load_program_messages(self):
        plain = self._source('Data2/Patch/Comm/message.csvZ',
            '5cd34cce66feae96d947cd45e32984765ce625673c0fb19c73cb63d7d9178598',
            '370bd6ed9b4892f57190fc7a8dab14061b3e844b0aa9d0171611a9cbab61b5f8')
        section = parse_sections(plain, ('ProgramMsg',))['ProgramMsg']
        self.program_rows = section['records']
        if len(self.program_rows) != 1080:
            raise ValueError('Unexpected ProgramMsg count')
        self.program_pointers = self.allocate(1080*4)
        self.vm.mem_write(MESSAGES+0xb2c68, struct.pack('<I', self.program_pointers))
        self.vm.mem_write(MESSAGES+8, struct.pack('<H', 2))
        for row in self.program_rows:
            # 2530 opens the decompressed stream as "rt" (VA 582378).
            # 51A90 passes fgets' LF to 51BE0: removing it loses the last field.
            line = bytes.fromhex(row['raw_record_hex']).replace(b'\r\n', b'\n')
            if len(line) >= 2048:
                raise ValueError('ProgramMsg row bound')
            self.vm.mem_write(SCRATCH, line+b'\0')
            self.call(0x51be0, SCRATCH, this=MESSAGES)
            self.vm.reg_write(UC_X86_REG_ESP, SP)
            self.vm.reg_write(UC_X86_REG_EBX, MESSAGES)
            self.vm.reg_write(UC_X86_REG_EBP, 1080)
            self._slice(0x58cd4, 0x58d67)
            if self.vm.reg_read(UC_X86_REG_ESP) != SP:
                raise AssertionError('ProgramMsg row stack imbalance')

    def _load_npc_groups(self):
        plain = self._source('Data2/Patch/Comm/gamedata.csvZ',
            '70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731',
            '75c3c37947a64b0917fbf8e546884d9bf893fe6a606d3e2b8f3b1857966b1815',
            decoded_limit=4*1024*1024)
        self.game_data = plain
        self.npc_group_rows = parse_sections(plain, ('NPCList',))['NPCList']['records']
        if len(self.npc_group_rows) != 451:
            raise ValueError('Unexpected NPCList row count')
        groups, areas, lines = {}, {}, []
        # Validate the complete source before the original unchecked row writer.
        for row in self.npc_group_rows:
            line = bytes.fromhex(row['raw_record_hex']).replace(b'\r\n', b'\n')
            fields = next(csv.reader([line.decode('ascii')], strict=True))
            if len(line) >= 2048 or not 2 <= len(fields) <= 7:
                raise ValueError('NPCList row bound')
            values = [int(field) for field in fields]
            area, scene = values[:2]
            if not 0 <= area < 17 or not 0 <= scene <= 255:
                raise ValueError('NPCList area/scene bound')
            if any(not 1 <= code <= 0x7fffffff for code in values[2:]):
                raise ValueError('NPCList resource code bound')
            areas.setdefault(area, set()).add(scene)
            group = groups.setdefault((area, scene), [])
            group.extend(values[2:])
            if len(areas[area]) > 70 or len(group) > 70:
                raise ValueError('NPCList native group capacity')
            lines.append(line)
        self.npc_group_codes = groups
        self.vm.mem_write(MESSAGES+8, struct.pack('<H', 7))
        for line in lines:
            self.vm.mem_write(SCRATCH, line+b'\0')
            self.call(0x51be0, SCRATCH, this=MESSAGES)
            self.vm.reg_write(UC_X86_REG_ESP, SP)
            self.vm.reg_write(UC_X86_REG_EBP, MESSAGES)
            self._slice(0x5a91d, 0x5aa3f)
            if self.vm.reg_read(UC_X86_REG_ESP) != SP:
                raise AssertionError('NPCList row stack imbalance')

    def _load_enemy_groups(self):
        catalog = parse_enemy_catalog(self.game_data)
        self.enemy_identity_records = catalog['records']
        self.enemy_groups = catalog['groups']
        self.enemy_group_offsets = catalog['group_offsets']
        self.enemy_loaded_groups = catalog['loaded_groups']
        self.enemy_stream = catalog['stream']
        self.enemy_stream_position = 0
        self.enemy_calloc_calls = []
        for rva in (0x147a95, 0x147e23):
            if rva not in getattr(self, 'bank_service_rvas', ()):
                self.hooks.append(self.vm.hook_add(UC_HOOK_CODE, self._service,
                                                  begin=BASE+rva, end=BASE+rva))
        prior_file = bytes(self.vm.mem_read(MESSAGES+4, 4))
        prior_width = bytes(self.vm.mem_read(MESSAGES+8, 2))
        self.vm.mem_write(MESSAGES+4, struct.pack('<I', 0x80020000))
        self.vm.mem_write(MESSAGES+8, struct.pack('<H', 10))
        try:
            if self.call(0x5a1a0, 7931, this=MESSAGES) != 1:
                raise AssertionError('Original EnyName loader failed')
            if self.enemy_stream_position != len(self.enemy_stream):
                raise AssertionError('Original EnyName loader left unread source rows')
        finally:
            self.vm.mem_write(MESSAGES+4, prior_file)
            self.vm.mem_write(MESSAGES+8, prior_width)

    def _service(self, vm, address, size, context):
        rva = address-BASE
        if rva not in (0x147a95, 0x147e23):
            return super()._service(vm, address, size, context)
        sp = vm.reg_read(UC_X86_REG_ESP)
        ret = self.u32(sp)
        arg = lambda index: self.u32(sp+4+4*index)
        if rva == 0x147e23:
            if ret not in (BASE+0x5a1de, BASE+0x5a223):
                raise AssertionError('Unqualified world calloc caller')
            width, count = arg(0), arg(1)
            if (ret == BASE+0x5a1de and (width, count) != (26, 7815)
                    or ret == BASE+0x5a223 and (width != 12 or not 1 <= count <= 256)):
                raise AssertionError('EnyName allocation bound')
            result = self.allocate(width*count)
            self.enemy_calloc_calls.append((width, count, result))
        else:
            if ret != BASE+0x51ab0 or arg(1) != 4096 or arg(2) != 0x80020000:
                raise AssertionError('Unqualified world fgets caller')
            start = self.enemy_stream_position
            end = self.enemy_stream.find(b'\n', start)
            end = len(self.enemy_stream) if end < 0 else end+1
            if end-start >= arg(1):
                raise AssertionError('EnyName fgets destination bound')
            result = 0
            if end > start:
                vm.mem_write(arg(0), self.enemy_stream[start:end]+b'\0')
                self.enemy_stream_position = end
                result = arg(0)
        self.calls.add(rva)
        vm.reg_write(UC_X86_REG_EAX, result)
        vm.reg_write(UC_X86_REG_ESP, sp+4)
        vm.reg_write(UC_X86_REG_EIP, ret)

    def _initialize_actor_components(self):
        self.call(0xff370, this=WORLD_COMPONENTS)

    def initialize(self, body, *, name=b'BoundHero', prior_flags=0, override=False):
        # Reuse the parent input constraints, without running its isolated slice
        # or copying post-hoc field results. This method owns its continuous tail.
        if (len(body) != 36 or body[6] != 27 or body[32:34] != b'\0\0'
                or not 1 <= (body[24] & 63) <= 16
                or (struct.unpack_from('<I', body)[0] >> 16) & 0x7f):
            raise ValueError('Only retained normal mounted appearance subset')
        block = bytearray(body[12:20])
        block[1] &= 31
        block[3] &= 31
        if block != bytes.fromhex('0100010001603100') or body[13] >> 5 > 6 or body[15] >> 5 > 6:
            raise ValueError('Outside retained component subset')
        if not 1 <= len(name) <= 20 or b'\0' in name or not name.isascii():
            raise ValueError('Bounded ASCII test name required')
        if not 0 <= prior_flags <= 0xffffffff:
            raise ValueError('Prior actor flags must be a DWORD')
        self._initialize_actor_components()
        vm = self.vm
        vm.mem_write(self.actor_address, b'\xa5'*self.actor_storage_size)
        vm.mem_write(self.actor_address+0x44, struct.pack('<I', prior_flags))
        vm.mem_write(SP+0x14, bytes(4))
        vm.mem_write(SP+0x28, bytes(body))
        vm.mem_write(SCRATCH+0x3000, name+b'\0')
        vm.mem_write(SP+0x15c, struct.pack('<III', SCRATCH+0x3000,
                                           self.actor_address, SCRATCH+0x4000))
        vm.mem_write(SCRATCH+0x4000, b'\xa5'*8)
        vm.mem_write(WORLD+0x1539ad70, bytes([0x10 if override else 0]))
        vm.reg_write(UC_X86_REG_ESP, SP)
        vm.reg_write(UC_X86_REG_EBX, WORLD)
        vm.reg_write(UC_X86_REG_ESI, 0)
        if getattr(self, 'cold_preload_enabled', False):
            self._slice(0x681cf, 0x68851)
        else:
            self._slice(0x681cf, 0x682f1)
            if vm.reg_read(UC_X86_REG_ESP) != SP:
                raise AssertionError('Actor pre-scene stack imbalance')
            # The retained slice-only oracle keeps its preload gap explicit.
            vm.reg_write(UC_X86_REG_ESI, MANAGER)
            self._slice(0x68315, 0x68851)
        if vm.reg_read(UC_X86_REG_ESP) != SP or vm.reg_read(UC_X86_REG_EAX) != 1:
            raise AssertionError('Actor tail did not reach success epilogue')
        return bytes(vm.mem_read(self.actor_address, 0x4699))
