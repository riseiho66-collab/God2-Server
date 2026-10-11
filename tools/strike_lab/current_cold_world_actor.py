"""Continuous original actor initialization including cold resource preload.

Reuses source-table parsing from the slice-only actor oracle, but constructs the
real bank manager in place. No transferred HeroDoll tables or injected cache
handles. The fixed clock covers the no-repaint progress path, not a live device.
"""
import struct

from .current_world_actor import NativeWorldActor, WORLD, MANAGER, BASE
from .current_world_resource_banks import NativeWorldResourceBanks, CWD
from .current_world_role_resources import NativeWorldRoleResources, ASSETS, DIRECTORY
from .current_indoor_resources import NativeIndoorResources
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_ESP


class NativeColdWorldActor(NativeWorldActor, NativeWorldResourceBanks):
    def __init__(self, appearance=None):
        if appearance is not None:
            raise ValueError('Cold actor loads original tables; no transferred appearance input')
        self.asset_names = {DIRECTORY+name: name for name in ASSETS}
        self.cache_writes, self.wrapper_visits, self.full_paths = [], [], []
        # Bypass the slice-only constructor's copied tables while retaining its
        # source parsers and actor assertions. Bank initialization runs once.
        NativeWorldResourceBanks.__init__(self, manager=MANAGER)
        self._load_component_sources()
        self.accessory_records = self.u32(MANAGER+0x682e0+0x24f74)
        self._prepare_actor_sources()
        self._map_rw(WORLD+0x15aad388, 4)
        self.cold_preload_enabled = True
        self.hooks.append(self.vm.hook_add(UC_HOOK_CODE, self._service,
                                          begin=BASE+0x158e89, end=BASE+0x158e89))

    @property
    def next_slot(self):
        return self.bank_state(max(self.active_bank, 0))['next_slot']

    def run(self, start, *args, **kwargs):
        if start == 0x681cf:
            kwargs.setdefault('instruction_limit', 150000000)
            kwargs.setdefault('timeout_us', 90000000)
        return NativeIndoorResources.run(self, start, *args, **kwargs)

    def _service(self, vm, address, size, context):
        rva = address-BASE
        if rva in (0x147a95, 0x147e23):
            sp = vm.reg_read(UC_X86_REG_ESP)
            ret = self.u32(sp)
            if ((rva == 0x147a95 and self.u32(sp+12) == 0x80020000)
                    or (rva == 0x147e23 and ret in (BASE+0x5a1de, BASE+0x5a223))):
                return NativeWorldActor._service(self, vm, address, size, context)
        if rva == 0x158e89:
            return NativeWorldRoleResources._service(self, vm, address, size, context)
        if rva == 0x14716f:
            sp = vm.reg_read(UC_X86_REG_ESP)
            path = self.string(self.u32(sp+4)).decode('ascii').replace('\\', '/').lower()
            prefix = CWD.decode().replace('\\', '/').lower()+'/'
            if path.startswith(prefix) and path[len(prefix):] in self.asset_names:
                return NativeWorldRoleResources._service(self, vm, address, size, context)
        return NativeWorldResourceBanks._service(self, vm, address, size, context)

    def initialize(self, body, **kwargs):
        # Other scenes require their own source-backed ROM allowlists first.
        if len(body) != 36 or struct.unpack_from('<H', body, 24)[0] != (2 | (15 << 6)):
            raise ValueError('Cold actor currently qualifies only initial area 2 / scene 15')
        return super().initialize(body, **kwargs)
