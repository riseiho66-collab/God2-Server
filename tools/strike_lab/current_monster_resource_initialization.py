"""Continue the original normal-participant resource miss without stat packets.

Source/descriptor preparation is the existing explicit row fixture. The ROM
loader, decompressor, name-cache insertion and return to the participant are
original instructions on the same VM, not transplanted handles.
"""
from collections import Counter
import hashlib
import struct

from .current_role_doll_resources import NativeRoleDollResources, BANK, ROOT
from . import current_monster_side_initialization as actor
from .omega_assets import decode_csvz
from unicorn import UC_HOOK_CODE, UC_HOOK_MEM_READ, UC_HOOK_MEM_WRITE, UC_MEM_WRITE
from unicorn import x86_const as reg

ASSETS = {
    0: ('data2/fight/eny1/eny1015.romz',
        'b4d53c62934136eac00ff9a4c87cea3af522608fc180127206db1c6cc4bd88e4',
        '77e95a2f5f5d0b3a396ea42e8f8c9330a984e21912efd5debb18b797179ed251'),
    1: ('data2/fight/eny/eny5015.romz',
        '1f9a5151bbb3d710776c810cf0d52e3e0bd0b1f1dd9a0b6ab79fb06891d63c12',
        '4cc5569c85c407789e9d3b3a49ec616582d12e4d0259625319d65e5f51892e9f'),
}


class NativeMonsterResourceInitialization(NativeRoleDollResources):
    def __init__(self, side=1):
        if type(side) is not int or side not in ASSETS:
            raise ValueError('Explicit side zero or one required')
        self.monster_asset = None
        super().__init__()
        self.side = side
        name, raw_sha, plain_sha = ASSETS[side]
        path = ROOT.parent / 'God2' / name
        if path.stat().st_size > 1024 * 1024:
            raise ValueError('Monster ROM input bound')
        raw = path.read_bytes()
        plain = decode_csvz(raw, limit=2 * 1024 * 1024)
        if (hashlib.sha256(raw).hexdigest() != raw_sha or
                hashlib.sha256(plain).hexdigest() != plain_sha):
            raise ValueError('Pinned original monster ROM changed')
        self.monster_asset = name
        self.files[name], self.decoded[name] = raw, plain
        self.p = p = actor.MonsterSideInitializationProbe(vm=self.vm)
        self.reset = p.reset_actor()
        self.prefix = p.run(side, diagnostic_level=0, diagnostic_identity_word=0)
        self.actor_before = bytes(self.vm.mem_read(actor.ACTOR, 0x1000))
        self.pending_sp = self.vm.reg_read(reg.UC_X86_REG_ESP)
        self.pending_stack = bytes(self.vm.mem_read(actor.SP - 0x1000, 0x1100))
        # Explicit runtime ownership and registry capacity, not game return values.
        p.put(actor.MANAGER + 8, '<I', BANK)
        p.put(actor.NAMES + 0x408, '<I', 1)
        self.name_storage = self.allocate(256)
        p.put(actor.NAMES + 4, '<I', self.name_storage)
        self.vm.mem_write(self.name_storage, b'\xa5' * 256)
        self.active_name = name
        self.attempted = self.completed = False
        self.hooks.append(self.vm.hook_add(UC_HOOK_CODE, self._service,
            begin=actor.BASE + 0x15ad35, end=actor.BASE + 0x15ad35))

    def _service(self, vm, address, size, context):
        if address != actor.BASE + 0x14716f or not self.monster_asset:
            return super()._service(vm, address, size, context)
        sp = vm.reg_read(reg.UC_X86_REG_ESP)
        path = self.string(self.u32(sp + 4)).decode('ascii').replace('\\', '/').lower()
        prefix = actor.CWD.decode().replace('\\', '/').lower() + '/'
        path = path[len(prefix):] if path.startswith(prefix) else path
        if path not in (self.monster_asset, self.monster_asset[:-1]) or self.string(self.u32(sp + 8)) != b'rb':
            raise AssertionError('Unqualified monster resource file request')
        self.attempts.append(path)
        result = 0
        if path in self.files:
            self.opens.append(path)
            result = 0x80000000 + 4 * len(self.opens)
            self.handles[result] = [self.files[path], 0]
        vm.reg_write(reg.UC_X86_REG_EAX, result)
        vm.reg_write(reg.UC_X86_REG_ESP, sp + 4)
        vm.reg_write(reg.UC_X86_REG_EIP, self.u32(sp))

    def continue_resource(self):
        if (self.attempted or self.vm.reg_read(reg.UC_X86_REG_EIP) != actor.BASE + 0x1206e0 or
                self.u32(actor.MANAGER + 8) != BANK):
            raise ValueError('Untouched original resource-miss continuation required')
        self.attempted = True
        self.continuation_visits, self.actor_writes = Counter(), []
        hooks = []

        def code(vm, address, size, _):
            self.continuation_visits[address - actor.BASE] += 1

        def write(vm, access, address, size, value, _):
            self.actor_writes.append((vm.reg_read(reg.UC_X86_REG_EIP) - actor.BASE,
                                      address - actor.ACTOR, size, value))

        try:
            hooks.append(self.vm.hook_add(UC_HOOK_CODE, code,
                begin=actor.BASE + 0x1206e0, end=actor.BASE + 0x1207cb))
            hooks.append(self.vm.hook_add(UC_HOOK_MEM_WRITE, write,
                begin=actor.ACTOR, end=actor.ACTOR + 0xfff))
            self.run(0x1206e0, 0x115fc7, instruction_limit=15000000, timeout_us=30000000)
        finally:
            for hook in hooks:
                self.vm.hook_del(hook)
        if (self.vm.reg_read(reg.UC_X86_REG_EAX) != 0 or
                self.vm.reg_read(reg.UC_X86_REG_ESP) != actor.FRAME or
                self.u32(actor.NAMES + 0x404) != 1 or
                self.string(self.name_storage) != bytes.fromhex(self.prefix['requested_path_hex']) or
                (self.monster_asset, 0, len(self.decoded[self.monster_asset])) not in self.parser_inputs):
            raise AssertionError('Original resource return/cache state differs')
        if bytes(self.vm.mem_read(actor.ACTOR, 0x1000)) != self.actor_before or self.actor_writes:
            raise AssertionError('Resource construction unexpectedly wrote actor data')
        self.completed = True
        return {'side': self.side, 'asset': self.monster_asset, 'slot': 0,
                'source_identity': (1, 0, 1), 'stop_rva': 0x115fc7,
                'hp_mp_raw_hex': self.actor_before[0xde8:0xdf8].hex(),
                'original_stat_values_recovered': 0}

    def inspect_local_vital_defaults(self):
        """Separate caller/prologue and post-display islands, never a full ctor.

        Real1165C1 argument construction provides both numeric arrays. After
        the actual call/prologue, the separate12D219 island tests the native
        side gate using the same frame. No display-function return is forged.
        """
        if not self.completed or getattr(self, 'defaults_attempted', False):
            raise ValueError('Completed resource stage and unused default probe required')
        self.defaults_attempted = True
        p = self.p
        original_sp = self.vm.reg_read(reg.UC_X86_REG_ESP)
        saved = self.vm.context_save()
        stack = bytes(self.vm.mem_read(actor.SP - 0x1000, 0x1100))
        before = bytes(self.vm.mem_read(actor.ACTOR, 0x1000))
        # These two non-stat owner bindings are explicit fixture inputs.
        owner = 0x2d000000
        for address in (actor.BATTLE + 0xa9ea4c8, actor.BATTLE + 0x83458, owner):
            actor.NativeWorldActor._map_rw(p.native, address, 4)
        p.put(actor.BATTLE + 0xa9ea4c8, '<I', 0)
        p.put(actor.BATTLE + 0x83458, '<I', owner)
        p.put(owner, '<I', 0)
        trace = {'producer_visits': [], 'consumer_visits': [], 'reads': [], 'writes': []}
        phase = 'producer'
        ranges = {'producer': ((0x1165c1, 0x11661c), (0x12ccd0, 0x12cd0b),
                               (0x11e6e0, 0x11e76a)),
                  'consumer': ((0x12d219, 0x12d246), (0x12d2ff, 0x12d329),
                               (0x11e6e0, 0x11e76a))}

        def code(vm, address, size, _):
            pc = address - actor.BASE
            if not any(lo <= pc and pc + size <= hi for lo, hi in ranges[phase]):
                raise AssertionError(f'Outside native default-initializer slice {pc:X}')
            trace[phase + '_visits'].append(pc)

        def memory(vm, access, address, size, value, _):
            pc = vm.reg_read(reg.UC_X86_REG_EIP) - actor.BASE
            write = access == UC_MEM_WRITE
            if write and not (actor.SP - 0x1000 <= address < address + size <= actor.SP + 0x100 or
                              actor.ACTOR + 0xde8 <= address < address + size <= actor.ACTOR + 0xdf8):
                raise AssertionError('Unexpected default initializer write')
            raw = ((value & ((1 << (8 * size)) - 1)).to_bytes(size, 'little') if write
                   else bytes(vm.mem_read(address, size)))
            trace['writes' if write else 'reads'].append((phase, pc, address, size, raw.hex()))

        hooks = [self.vm.hook_add(UC_HOOK_CODE, code),
                 self.vm.hook_add(UC_HOOK_MEM_READ | UC_HOOK_MEM_WRITE, memory)]
        try:
            self.vm.reg_write(reg.UC_X86_REG_ESP, original_sp)
            self.vm.reg_write(reg.UC_X86_REG_EBP, actor.BATTLE)
            self.run(0x1165c1, 0x12cd0b, instruction_limit=1000, timeout_us=1000000)
            sp = self.vm.reg_read(reg.UC_X86_REG_ESP)
            trace['argument_side_slot'] = struct.unpack('<2I', self.vm.mem_read(sp + 0x60, 8))
            trace['array_pointers'] = struct.unpack('<2I', self.vm.mem_read(sp + 0x6c, 8))
            trace['arrays'] = [struct.unpack('<2I', self.vm.mem_read(at, 8)) for at in trace['array_pointers']]
            if (tuple(value & 0xff for value in trace['argument_side_slot']) != (self.side, 0) or
                    trace['arrays'] != [(1, 1), (1, 1)]):
                raise AssertionError(f'Actual default arguments differ: {trace["argument_side_slot"]}, {trace["arrays"]}')
            phase = 'consumer'
            self.run(0x12d219, 0x12d329, instruction_limit=1000, timeout_us=1000000)
            after = bytes(self.vm.mem_read(actor.ACTOR, 0x1000))
            trace['result'] = struct.unpack('<4I', after[0xde8:0xdf8])
            expected = bytearray(before)
            if self.side == 0:
                struct.pack_into('<4I', expected, 0xde8, 1, 1, 1, 1)
            if after != expected:
                raise AssertionError('Native side gate/default write footprint differs')
        finally:
            for hook in hooks:
                self.vm.hook_del(hook)
            self.vm.mem_write(actor.SP - 0x1000, stack)
            self.vm.mem_write(actor.ACTOR, before)
            self.vm.context_restore(saved)
        self.defaults_trace = trace
        return trace

    def continue_actor_creation(self):
        """Resume the real caller through reset and1216C0, not the full client.

        Renderer/slot ownership is an explicit offline prerequisite. Original
        constructors initialize the render pool, effect records and actors;
        preparation preserves the pending participant CPU and stack. No game
        return, stat packet or numerical ability is substituted.
        """
        if (not self.completed or getattr(self, 'creation_attempted', False) or
                self.vm.reg_read(reg.UC_X86_REG_EIP) != actor.BASE + 0x115fc7 or
                self.vm.reg_read(reg.UC_X86_REG_ESP) != actor.FRAME):
            raise ValueError('Untouched resource return required')
        self.creation_attempted = True
        from .current_battle_resources import NativeBattleResources
        from .current_indoor_resources import SURFACE

        vm, p = self.vm, self.p
        saved = vm.context_save()
        stack = bytes(vm.mem_read(actor.SP - 0x1000, 0x1100))
        seh = bytes(vm.mem_read(0, 4))
        renderer = 0x30000000
        actor.NativeWorldActor._map_rw(p.native, renderer, 0x291000)
        NativeBattleResources._prepare_graphics_services(self)
        if self.call(0x1aa10, SURFACE, 0, BANK, this=renderer) != renderer:
            raise AssertionError('Native renderer constructor return differs')
        p.put(actor.MANAGER + 0xc, '<I', renderer)
        p.put(actor.MANAGER + 0x28, '<I', 0)  # Explicit absent optional effect owner.
        self.creation_actors = []
        for position in range(28):
            for kind in range(6):
                pointer = (actor.ACTOR if position == 14 * self.side and kind == 0
                           else 0x2e000000 + (position * 6 + kind) * 0x1000)
                actor.NativeWorldActor._map_rw(p.native, pointer, 0x1000)
                vm.mem_write(pointer, b'\xa5' * 0x1000)
                if kind == 4:
                    effect = 0x2f000000 + position * 0x1000
                    actor.NativeWorldActor._map_rw(p.native, effect, 0x1000)
                    self.call(0x11c9f0, this=effect)
                    self.call(0x11ca30, renderer, this=effect)
                    p.put(pointer + 0xec8, '<I', effect)
                self.call(0x11fde0, pointer, position // 14, position % 14,
                          this=actor.MANAGER)
                p.put(actor.MANAGER + 0x38 + position * 24 + kind * 4, '<I', pointer)
                self.creation_actors.append(pointer)
        positions = actor.MANAGER + 0xa7fbccc
        actor.NativeWorldActor._map_rw(p.native, positions, 224)
        vm.reg_write(reg.UC_X86_REG_ESI, actor.MANAGER)
        self.run(0x11f4c5, 0x11f4ef)
        if bytes(vm.mem_read(positions, 224)) != self.p.image[0x171aa8:0x171b88]:
            raise AssertionError('Original position table copy differs')
        vm.mem_write(actor.SP - 0x1000, stack)
        vm.mem_write(0, seh)
        vm.context_restore(saved)
        self.creation_before = bytes(vm.mem_read(actor.ACTOR, 0x1000))
        self.creation_visits, self.creation_writes = Counter(), []
        tracked = (0x115fc7, 0x116000, 0x120000, 0x11cfb0, 0x11fde0,
                   0x116025, 0x1216c0, 0x121630, 0x1e130, 0x12a7c0,
                   0x12a710, 0x1afe0, 0x1e070, 0x1cd40, 0x121a4a,
                   0x120970, 0x121ab1)

        def code(vm, address, size, _):
            self.creation_visits[address - actor.BASE] += 1

        def write(vm, access, address, size, value, _):
            self.creation_writes.append((vm.reg_read(reg.UC_X86_REG_EIP) - actor.BASE,
                                         address - actor.ACTOR, size, value))

        hooks = [vm.hook_add(UC_HOOK_CODE, code, begin=actor.BASE + pc,
                            end=actor.BASE + pc) for pc in tracked]
        hooks.append(vm.hook_add(UC_HOOK_MEM_WRITE, write,
                                 begin=actor.ACTOR, end=actor.ACTOR + 0xfff))
        try:
            self.run(0x115fc7, 0x11602a, instruction_limit=5000000, timeout_us=10000000)
        finally:
            for hook in hooks:
                vm.hook_del(hook)
        self.creation_after = bytes(vm.mem_read(actor.ACTOR, 0x1000))
        handle = struct.unpack_from('<h', self.creation_after, 0x1a)[0]
        if (vm.reg_read(reg.UC_X86_REG_ESP) != actor.FRAME or handle != 0 or
                self.creation_visits[0x11fde0] != 6 or
                self.creation_visits[0x121ab1] != 1 or
                self.creation_visits[0x1afe0] != 1 or
                self.creation_after[0xde8:0xdf8] != b'\xcd' * 16):
            raise AssertionError('Original reset/create return or write result differs')
        if any(bytes(vm.mem_read(ptr + actor.ACTOR_SIZE, 0x1000 - actor.ACTOR_SIZE)) !=
               b'\xa5' * (0x1000 - actor.ACTOR_SIZE) for ptr in self.creation_actors):
            raise AssertionError('Actor guard changed')
        if bytes(vm.mem_read(actor.BASE, 0x170000)) != self.p.image[:0x170000]:
            raise AssertionError('Original instructions changed')
        return {'side': self.side, 'asset': self.monster_asset,
                'native_start_rva': 0x115fc7, 'native_stop_rva': 0x11602a,
                'native_actor_creation_returned': True, 'render_handle': handle,
                'sequence_count': self.u32(BANK + 0x108c),
                'rom_command_accumulator': struct.unpack_from('<H', self.creation_after, 0x1da)[0],
                'hp_mp_raw_hex': self.creation_after[0xde8:0xdf8].hex(),
                'original_stat_values_recovered': 0, 'full_participant_constructor': False,
                'live_offline_world_entered': False, 'runtime_eligible': False}
