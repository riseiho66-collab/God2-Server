"""Native display-pool construction in a non-overlapping world memory layout.

No host display device, live client process or forged renderer return is used.
"""
from .current_embedded_world import NativeEmbeddedWorld, WORLD, BASE
import struct

from .current_world_actor import WORLD_COMPONENTS, MESSAGES
from .current_world_scene import SCENE_BRIDGE
from .current_world_resource_banks import CWD
from .current_indoor_resources import SCRATCH
from .current_world_ui_resource import pinned_sources, ASSET, LITERAL_PATH
from unicorn import UC_PROT_READ, UC_PROT_WRITE
from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_ESP, UC_X86_REG_EIP

DISPLAY_POOL = WORLD + 0x39c
DISPLAY_EXTENT = 0xa7e0134
RECTANGLES = 0x51800000


class NativeWorldDisplay(NativeEmbeddedWorld):
    # The original embedded display pool spans addresses occupied by resources
    # in earlier slice-only fixtures. Allocate those resources elsewhere first.
    heap_start_address = 0x40000000
    heap_end_address = 0x50000000
    renderer_address = 0x51000000
    second_bank_address = 0x51400000

    def _service(self, vm, address, size, context):
        sp = vm.reg_read(UC_X86_REG_ESP)
        if (address == BASE+0x1480b4 and self.u32(sp)-BASE in
                (0x1098db, 0x1099fe, 0x109aee, 0x10aac9)):
            if self.string(self.u32(sp+8)) != b'%s':
                raise AssertionError('Unexpected display sscanf format')
            source = self.string(self.u32(sp+4), limit=32)
            parts = source.split()
            token = parts[0] if parts else b''
            if len(token) > 15 or not token.isascii():
                raise AssertionError('Display name token exceeds qualified ASCII buffer')
            if token:
                vm.mem_write(self.u32(sp+12), token+b'\0')
            vm.reg_write(UC_X86_REG_EAX, 1 if token else 0xffffffff)
            vm.reg_write(UC_X86_REG_ESP, sp+4)
            vm.reg_write(UC_X86_REG_EIP, self.u32(sp))
            return
        return super()._service(vm, address, size, context)

    def _map_rw(self, address, size):
        if address < 0 or size <= 0 or address + size > 0x100000000:
            raise ValueError('World display mapping bound')
        cursor, last = address & ~4095, (address+size+4095) & ~4095
        # Preserve existing regions and permissions; map only contiguous gaps.
        for start, end, _ in sorted(self.vm.mem_regions()):
            if end < cursor:
                continue
            if start >= last:
                break
            if start > cursor:
                self.vm.mem_map(cursor, start-cursor, UC_PROT_READ | UC_PROT_WRITE)
            cursor = max(cursor, end+1)
            if cursor >= last:
                return
        if cursor < last:
            self.vm.mem_map(cursor, last-cursor, UC_PROT_READ | UC_PROT_WRITE)

    def _initialize_actor_components(self):
        super()._initialize_actor_components()
        # Original startup binds before actor initialization, not after it:
        # FF3C0 resets the component IDs, so a late binding would erase them.
        self.call(0xff3c0, self.renderer_address, this=WORLD_COMPONENTS)

    def __init__(self):
        super().__init__()
        self._map_rw(DISPLAY_POOL, DISPLAY_EXTENT)
        self._map_rw(RECTANGLES, 0x12030)
        self.call(0x188a0, this=RECTANGLES)
        self.call(0x188c0, this=RECTANGLES)
        self.call(0x107f30, this=DISPLAY_POOL)
        self.title_bound = False

    def bind_title_resources(self):
        if self.title_bound:
            raise ValueError('Title resources already bound')
        sources, _ = pinned_sources()
        raw, plain = sources[1]
        relative = ASSET.lower()
        name = relative.rsplit('/', 1)[-1]
        self.files[relative], self.decoded[name] = raw, plain
        self.asset_names[relative] = self.asset_names[relative[:-1]] = name
        self.vm.mem_write(SCRATCH, CWD + LITERAL_PATH + b'\0')
        self.title_slot = self.call(0x60a90, SCRATCH, this=self.manager)
        self.checkpoint()
        self.call(0x1081c0, SCENE_BRIDGE, self.renderer_address, RECTANGLES,
                  self.title_slot, MESSAGES, this=DISPLAY_POOL)
        self.vm.mem_write(WORLD+0xaa36484, struct.pack('<I', self.renderer_address))
        self.title_bound = True
        return self.title_slot
