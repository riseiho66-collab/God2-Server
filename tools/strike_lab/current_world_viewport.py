"""Original indoor viewport and empty-pool camera propagation, no presentation."""
import struct

from .current_world_scene import NativeWorldScene, BASE, WORLD, SCENE_BRIDGE, MAP_MANAGER
from .current_world_actor import OWNER_POISON
from .current_indoor_resources import SP
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_ESI, UC_X86_REG_ESP

NPC_POOLS = (WORLD + 0x1539aed8, WORLD + 0x153b8758)
ROLE_POOL = WORLD + 0x15383410
OPTIONAL_POOL = WORLD + 0x153dc7cc


class NativeWorldViewport(NativeWorldScene):
    def __init__(self, appearance=None):
        super().__init__(appearance)
        self.viewport_started = self.viewport_positioned = False
        self.viewport_visits = []
        for pool in NPC_POOLS:
            self._map_rw(pool, 0x1d878)
            self.call(0xca680, SCENE_BRIDGE, OWNER_POISON, OWNER_POISON,
                      OWNER_POISON, OWNER_POISON, OWNER_POISON, this=pool)
        self._map_rw(ROLE_POOL, 0x1342c)
        self.call(0xfabb0, SCENE_BRIDGE, OWNER_POISON, OWNER_POISON,
                  0, 0xffffffff, this=ROLE_POOL)
        # Only the original scalar constructor tail. Nested resources/device are
        # not constructed; 30F30's optional renderer is legitimately null here.
        self._map_rw(OPTIONAL_POOL, 8)
        self._map_rw(OPTIONAL_POOL + 0x3491a8, 4)
        self.vm.reg_write(UC_X86_REG_ESI, OPTIONAL_POOL)
        self.vm.reg_write(UC_X86_REG_ESP, SP)
        self._slice(0x30d7c, 0x30d93)
        for rva in (0x46520, 0x430b0, 0x422d0, 0x103c70,
                    0xca7b0, 0xfb020, 0x30f30, 0x1ac30):
            self.hooks.append(self.vm.hook_add(UC_HOOK_CODE, self._viewport_visit,
                                               begin=BASE+rva, end=BASE+rva))

    def _viewport_visit(self, vm, address, size, context):
        self.viewport_visits.append(address - BASE)

    def position_viewport(self):
        if not self.scene_loaded:
            raise ValueError('Native scene must be loaded before viewport')
        if self.viewport_started:
            raise ValueError('Fresh viewport only; lifecycle reload is not qualified')
        self.viewport_started = True
        self.vm.reg_write(UC_X86_REG_ESI, WORLD)
        self.vm.reg_write(UC_X86_REG_ESP, SP)
        # The separate music call interval 10078F..1007B0 is not executed here.
        # 100831 reads the world's embedded actor, whereas this inherited lab
        # initializes an isolated actor. Do not fabricate the embedded state.
        self._slice(0x1007b0, 0x100831)
        if self.vm.reg_read(UC_X86_REG_ESP) != SP:
            raise AssertionError('Viewport caller stack imbalance')
        self.viewport_positioned = True
        return struct.unpack('<ii', self.vm.mem_read(WORLD + 0x21c, 8))
