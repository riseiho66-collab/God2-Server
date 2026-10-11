"""Actual startup ROM load/binding sequence followed by full native scene entry.

The pinned original FieldComm3 reader supplies its allocation-backed inline
table. Device dimensions and allocator capacity are explicit lab inputs.
"""
import struct

from .current_world_display import NativeWorldDisplay, WORLD, BASE, RECTANGLES
from .current_world_display import DISPLAY_EXTENT, DISPLAY_POOL, SCENE_BRIDGE
from .current_world_ui_resource import NativeWorldUIResource, STRIDE, CAPACITY
from .current_world_startup_assets import ASSETS, pinned_assets
from .current_world_viewport import ROLE_POOL
from .current_world_scene import MAP_MANAGER
from .current_indoor_resources import SP
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import (UC_X86_REG_EAX, UC_X86_REG_EBP, UC_X86_REG_EDI,
                              UC_X86_REG_ESP, UC_X86_REG_EIP)

SECOND_DISPLAY = WORLD+0xaba32e0


class NativeWorldStartup(NativeWorldDisplay):
    # Both banks must hold the complete pinned startup assets and actor ROMs.
    # This is VM fixture capacity, not a recovered original memory policy.
    bank_capacity = 16*1024*1024

    def __init__(self):
        super().__init__()
        self.startup_bound = False
        self.startup_started = False
        self.startup_visits, self.scene_entry_visits = [], []
        self._map_rw(SECOND_DISPLAY, DISPLAY_EXTENT)
        role_before = bytes(self.vm.mem_read(ROLE_POOL, 64))
        self.call(0x107f30, this=SECOND_DISPLAY)
        if bytes(self.vm.mem_read(ROLE_POOL, 64)) != role_before:
            raise AssertionError('Secondary display constructor overwrote role pool')
        reader = NativeWorldUIResource()
        self.startup_records = self.allocate(STRIDE*CAPACITY)
        self.vm.mem_write(self.startup_records, bytes(reader.vm.mem_read(reader.records, STRIDE*CAPACITY)))
        self._map_rw(WORLD+0xa8d50d0, 4)
        self.vm.mem_write(WORLD+0xa8d50d0, struct.pack('<I', self.startup_records))
        self.vm.mem_write(WORLD+0xaba32dc, struct.pack('<I', self.renderer_address))
        self.vm.mem_write(WORLD+0xaa36484, struct.pack('<I', self.renderer_address))
        self.vm.mem_write(WORLD+0xa7e05c8, struct.pack('<I', RECTANGLES))
        sources = pinned_assets()
        for asset in ASSETS:
            relative = asset.asset.lower()
            name = relative.rsplit('/', 1)[-1]
            self.files[relative], self.decoded[name] = sources[asset.record]
            self.asset_names[relative] = self.asset_names[relative[:-1]] = name
        for rva in (0x64cb6, 0x60a90, 0x60b10, 0x1081c0, 0x10fa30, 0x10fa50, 0x10dc70,
                    0x100180, 0x100950, 0xff510, 0x108300, 0x1097d0, 0x1099fe,
                    0x109aee, 0x1004f0, 0x1004f5, 0x10078f, 0x100930):
            self.hooks.append(self.vm.hook_add(UC_HOOK_CODE, self._startup_visit,
                                               begin=BASE+rva, end=BASE+rva))

    def _startup_visit(self, vm, address, size, data):
        (self.scene_entry_visits if self.startup_bound else self.startup_visits).append(address-BASE)

    def _service(self, vm, address, size, context):
        if address == BASE+0x147af7:
            sp = vm.reg_read(UC_X86_REG_ESP)
            if self.u32(sp)-BASE in {a.load_call_rva-10 for a in ASSETS if a.record != 9} | {0x64e60}:
                if self.string(self.u32(sp+8)) != b'%s':
                    raise AssertionError('Unexpected startup sprintf format')
                value = self.string(self.u32(sp+12), limit=260)
                vm.mem_write(self.u32(sp+4), value+b'\0')
                vm.reg_write(UC_X86_REG_EAX, len(value))
                vm.reg_write(UC_X86_REG_ESP, sp+4)
                vm.reg_write(UC_X86_REG_EIP, self.u32(sp))
                return
        return super()._service(vm, address, size, context)

    def run(self, start, *args, **bounds):
        if start == 0x64cb6:
            bounds.setdefault('instruction_limit', 1500000000)
            bounds.setdefault('timeout_us', 180000000)
        return super().run(start, *args, **bounds)

    def bind_startup(self):
        if self.startup_started or self.title_bound:
            raise ValueError('Startup requires fresh unloaded display banks')
        self.startup_started = True
        parser_start = len(self.parser_inputs)
        self.vm.reg_write(UC_X86_REG_EBP, WORLD)
        self.vm.reg_write(UC_X86_REG_EDI, self.manager)
        self.vm.reg_write(UC_X86_REG_ESP, SP)
        self._slice(0x64cb6, 0x64fe2)
        if self.vm.reg_read(UC_X86_REG_ESP) != SP:
            raise AssertionError('Startup binding stack imbalance')
        self.title_slot = self.u32(DISPLAY_POOL+16)
        self.startup_parser_inputs = tuple(self.parser_inputs[parser_start:])
        self.startup_bank_states = tuple(self.bank_state(i) for i in (0, 1))
        self.title_bound = self.startup_bound = True
        return self.title_slot

    def enter_full_scene(self, body, *, name=b'BoundHero'):
        if not self.startup_bound or self.scene_started:
            raise ValueError('Full scene requires fresh completed startup')
        if (len(body) != 36 or struct.unpack_from('<H', body, 24)[0] != (2 | (15 << 6))
                or (struct.unpack_from('<I', body, 28)[0] & 3) != 2):
            raise ValueError('Only qualified retained indoor scene')
        self.scene_started = True
        self.initialize(body, name=name)
        self.vm.mem_write(SCENE_BRIDGE+0x48, struct.pack('<II', 800, 600))
        self.scene_return = self.call(0x100180, self.actor_address, 1, this=WORLD)
        if self.u32(0) != 0xffffffff:
            raise AssertionError('Full scene left native SEH unbalanced')
        indoor = self.u32(MAP_MANAGER+0x1030)
        if not indoor:
            raise AssertionError('Full scene returned without an indoor model')
        self.scene_loaded = True
        self.viewport_started = self.viewport_positioned = True
        return indoor
