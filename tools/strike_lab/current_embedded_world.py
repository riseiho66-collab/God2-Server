"""In-place native actor -> indoor scene -> music/camera/movement-ring tail.

The earlier 100180..1004F5 graphics/UI prefix is not executed. This oracle
stops before the function epilogue; it is not a live renderer or world E2E.
"""
import struct

from .current_world_actor import BASE, WORLD
from .current_world_viewport import NativeWorldViewport, NPC_POOLS, ROLE_POOL
from .current_world_music import NativeWorldMusicMixin
from .current_indoor_resources import SP
from unicorn import UC_HOOK_CODE, UC_PROT_READ, UC_PROT_WRITE
from unicorn.x86_const import UC_X86_REG_ESI, UC_X86_REG_EDI, UC_X86_REG_ESP

EMBEDDED_ACTOR = WORLD + 0x1539683c
ACTOR_EXTENT = 0x469c
RING = WORLD + 0x234


class NativeEmbeddedWorld(NativeWorldMusicMixin, NativeWorldViewport):
    actor_address = EMBEDDED_ACTOR
    # Bounded actor storage ends where the original first NPC pool begins.
    # Do not inherit the isolated fixture's oversized 0x6000 poison fill.
    actor_storage_size = ACTOR_EXTENT

    def __init__(self):
        super().__init__()
        if ROLE_POOL + 0x1342c != self.actor_address:
            raise AssertionError('Original role/actor adjacency changed')
        if self.actor_address + self.actor_storage_size != NPC_POOLS[0]:
            raise AssertionError('Original actor/NPC adjacency changed')
        self.install_music(absent_device_fixture=True)
        # PE .data (RVA182000, characteristics C0000040) contains the native
        # message-pointer slot at VA5B8ACC. No executable page is made writable.
        self.vm.mem_protect(BASE+0x1b8000, 4096, UC_PROT_READ | UC_PROT_WRITE)
        self.tail_visits = []
        for rva in (0x100831, 0x10083a, 0x1008b1, 0x103640, 0x1036b0,
                    0x103680, 0x100912, 0x15ab0):
            self.hooks.append(self.vm.hook_add(UC_HOOK_CODE, self._tail_visit,
                                               begin=BASE+rva, end=BASE+rva))

    def _tail_visit(self, vm, address, size, context):
        self.tail_visits.append(address-BASE)

    def finish_scene(self):
        if not self.scene_loaded:
            raise ValueError('Native scene must be loaded before its tail')
        if self.viewport_started:
            raise ValueError('Fresh scene only; lifecycle reload is not qualified')
        self.viewport_started = True
        self.vm.reg_write(UC_X86_REG_ESI, WORLD)
        self.vm.reg_write(UC_X86_REG_EDI, self.actor_address)
        self.vm.reg_write(UC_X86_REG_ESP, SP)
        self._slice(0x10078f, 0x100930)
        if self.vm.reg_read(UC_X86_REG_ESP) != SP:
            raise AssertionError('Scene tail stack imbalance')
        self.viewport_positioned = True
        return struct.unpack('<ii', self.vm.mem_read(WORLD+0x21c, 8))
