"""Original preview filename cache and component setter over real RoleDoll ROMZ.

The optional control-table subclass allocates native renderer objects offline;
no full preview, graphics device, OS filesystem or client process is exercised.
"""
import csv
import hashlib
import io
import struct

from .current_role_doll_resources import (
    NativeRoleDollResources, ASSETS, BANK, BASE, DIRECTORY, SCRATCH, ROOT, STRIDE)
from .current_appearance_resources import AppearanceResources
from .current_indoor_resources import SP, SURFACE, NativeIndoorResources
from .omega_assets import decode_csvz
from unicorn import UC_HOOK_CODE, UC_PROT_READ, UC_PROT_WRITE, UC_PROT_EXEC
from unicorn.x86_const import (
    UC_X86_REG_EAX, UC_X86_REG_EBX, UC_X86_REG_EBP, UC_X86_REG_EDI,
    UC_X86_REG_ESP, UC_X86_REG_EIP, UC_X86_REG_ECX, UC_X86_REG_ESI)

PREVIEW, RECORDS = 0x7400000, 0x7600000
COMPONENTS = PREVIEW+0x15e38
VIRTUAL_ROOT = 'C:\\RoleDollOracle'
KEYS = {'r1h000': (0, 2, 0, 0, 0), 'r2h000': (1, 2, 0, 0, 0),
        'r1f002': (0, 1, 0, 2, 0), 'r2f002': (1, 1, 0, 2, 0)}


def native_preview_records(client_root=ROOT.parent / 'God2'):
    """Copy actual native-loaded records selected by original table lookup."""
    appearance = AppearanceResources(client_root)
    return {key: appearance.record(appearance.lookup(*lookup))
            for key, lookup in KEYS.items()}


class NativePreviewRoleResources(NativeRoleDollResources):
    def __init__(self, records=None, client_root=ROOT.parent / 'God2'):
        super().__init__(client_root)
        self.records = native_preview_records(client_root) if records is None else records
        self.preview_visits, self.record_pointers = [], {}
        self.current_directory_calls = 0
        vm = self.vm
        vm.mem_map(PREVIEW, 0x180000, UC_PROT_READ | UC_PROT_WRITE)
        vm.mem_map(RECORDS, 4096, UC_PROT_READ | UC_PROT_WRITE)
        for ordinal, key in enumerate(KEYS):
            record = self.records[key]
            if (len(record) != 44 or record[30:32] != b'\xff\xff'
                    or record[32:42].split(b'\0')[0] != key.encode()
                    or record[:30].split(b'\0')[0].decode() not in ASSETS):
                raise ValueError('Expected unloaded source-backed preview record')
            pointer = RECORDS+ordinal*44
            vm.mem_write(pointer, record)
            self.record_pointers[key] = pointer
        for rva in (0x15ada3, 0x15aaaa, 0x15ad35, 0x147e23):
            self.hooks.append(vm.hook_add(UC_HOOK_CODE, self._service,
                                         begin=BASE+rva, end=BASE+rva))
        for rva in (0x4b70, 0x4c0e, 0x4c61, 0x9b45, 0xff450):
            self.hooks.append(vm.hook_add(UC_HOOK_CODE, self._preview_observe,
                                         begin=BASE+rva, end=BASE+rva))
        for page in (0x59d000, 0x5b9000):
            vm.mem_protect(page, 4096, UC_PROT_READ | UC_PROT_WRITE)
        self.get_directory = self.u32(0x570428)
        vm.mem_map(self.get_directory & ~4095, 4096, UC_PROT_READ | UC_PROT_EXEC)
        self.hooks.append(vm.hook_add(UC_HOOK_CODE, self._service,
                                     begin=self.get_directory, end=self.get_directory))
        vm.mem_write(0x59ddf0, struct.pack('<I', 1))
        # Execute the allocation/initialization slice, including all 22 calloc
        # filename buffers. EBP and the pushed size come from 4035/4031.
        vm.reg_write(UC_X86_REG_ESP, SP-4)
        vm.mem_write(SP-4, struct.pack('<I', 0x410))
        vm.reg_write(UC_X86_REG_EBP, PREVIEW)
        self.run_slice(0x40a9, 0x410d)
        if vm.reg_read(UC_X86_REG_ESP) != SP:
            raise AssertionError('Preview cache initialization stack mismatch')
        self.cache = self.u32(PREVIEW+0x178cdc)
        vm.mem_write(PREVIEW+0x15e7c, struct.pack('<I', BANK))
        self.call(0xff370, this=COMPONENTS)

    def run_slice(self, start, stop):
        hook = self.vm.hook_add(UC_HOOK_CODE,
                               lambda vm, address, size, data: vm.emu_stop(),
                               begin=BASE+stop, end=BASE+stop)
        try:
            self.run(start, stop)
        finally:
            self.vm.hook_del(hook)

    def _preview_observe(self, vm, address, size, context):
        self.preview_visits.append(address-BASE)

    def _service(self, vm, address, size, context):
        # Parent initialization also calls this method, before preview APIs exist.
        rva = address-BASE
        if address == getattr(self, 'get_directory', None):
            sp = vm.reg_read(UC_X86_REG_ESP)
            length, pointer = struct.unpack('<2I', vm.mem_read(sp+4, 8))
            value = VIRTUAL_ROOT.encode('ascii')
            if length != 260 or pointer != 0x5b93c4 or len(value)+1 > length:
                raise AssertionError('Unexpected preview current-directory request')
            vm.mem_write(pointer, value+b'\0')
            self.current_directory_calls += 1
            vm.reg_write(UC_X86_REG_EAX, len(value))
            vm.reg_write(UC_X86_REG_ESP, sp+12)
            vm.reg_write(UC_X86_REG_EIP, self.u32(sp))
            return
        if rva == 0x147e23:
            sp = vm.reg_read(UC_X86_REG_ESP)
            count, width = struct.unpack('<2I', vm.mem_read(sp+4, 8))
            if (count, width) != (256, 1):
                raise AssertionError('Unexpected preview calloc dimensions')
            pointer = self.allocate(count*width)
            vm.reg_write(UC_X86_REG_EAX, pointer)
            vm.reg_write(UC_X86_REG_ESP, sp+4)
            vm.reg_write(UC_X86_REG_EIP, self.u32(sp))
            return
        if rva in (0x15ada3, 0x15aaaa, 0x15ad35):
            return NativeIndoorResources._service(self, vm, address, size, context)
        if rva != 0x14716f:
            return super()._service(vm, address, size, context)
        sp = vm.reg_read(UC_X86_REG_ESP)
        path = self.string(self.u32(sp+4)).decode('ascii').replace('\\', '/').lower()
        prefix = VIRTUAL_ROOT.replace('\\', '/').lower()+'/'
        if path.startswith(prefix):
            path = path[len(prefix):]
        if path not in {DIRECTORY+name for name in ASSETS}:
            raise AssertionError('Unqualified preview asset path: '+path)
        if self.string(self.u32(sp+8)) != b'rb':
            raise AssertionError('Preview virtual filesystem is read-only')
        self.active_name = path[len(DIRECTORY):]
        self.calls.add(rva)
        self.attempts.append(path)
        result = 0
        if path in self.files:
            self.opens.append(path)
            result = 0x80000000+4*len(self.opens)
            self.handles[result] = [self.files[path], 0]
        vm.reg_write(UC_X86_REG_EAX, result)
        vm.reg_write(UC_X86_REG_ESP, sp+4)
        vm.reg_write(UC_X86_REG_EIP, self.u32(sp))

    def load_wrapper(self, name, *, uppercase=False):
        if name not in ASSETS:
            raise ValueError('Qualified preview ROM filename required')
        path = VIRTUAL_ROOT+'\\'+(DIRECTORY+name).replace('/', '\\')
        self.cstring(SCRATCH, (path.upper() if uppercase else path).encode())
        return self.call(0x4b70, self.u32(SCRATCH), this=PREVIEW)

    def set_record(self, key, component):
        if key not in KEYS or not isinstance(component, int) or not 0 <= component < 4:
            raise ValueError('Qualified preview key and component required')
        vm = self.vm
        vm.reg_write(UC_X86_REG_ESP, SP)
        vm.reg_write(UC_X86_REG_EAX, self.record_pointers[key])
        vm.reg_write(UC_X86_REG_EBX, component)
        vm.reg_write(UC_X86_REG_EDI, PREVIEW)
        self.run_slice(0x9b00, 0x9b66)
        if vm.reg_read(UC_X86_REG_ESP) != SP:
            raise AssertionError('Preview component slice stack mismatch')
        return struct.unpack('<H', vm.mem_read(COMPONENTS+4+6*component, 2))[0]


CONTROL_TABLE = PREVIEW+0x2808c
RENDERER, HIT_REGIONS = 0x7800000, 0x7b00000
FLOW_PATH = 'data3/flow/flowgui.romz'
FLOW_HASH = '2ad797d15aa6daa6562652fb69d39c9e3dbbdc108965c230c199735c8e682503'
FLOW_DECODED_HASH = '8612c3e4953c54d236eaae7c06d78200f0f6787ee05458bc4b004b1706cea215'


class NativePreviewAnimationResources(NativePreviewRoleResources):
    """Real preview control-handle table; no fabricated 106C30 return value."""
    def __init__(self, records=None, client_root=ROOT.parent / 'God2'):
        super().__init__(records, client_root)
        raw = (client_root/'Data2/Patch/FlowComm.csvZ').read_bytes()
        if hashlib.sha256(raw).hexdigest() != '27a0660b158d0cfcfe6afd5a01fcae91f98732d0f73efdde953b9d98fbe717e1':
            raise ValueError('Pinned FlowComm source changed')
        plain = decode_csvz(raw, limit=1024*1024)
        if hashlib.sha256(plain).hexdigest() != 'ca4c48dc8606081c420973772093848f18f51d3094972e2b500c6955658c053e':
            raise ValueError('Pinned FlowComm decode changed')
        rows = list(csv.reader(io.StringIO(plain.decode('latin1'))))
        self.flow_rows = [row for row in rows if row and row[0].isdigit()]
        if len(self.flow_rows) != 14 or self.flow_rows[0][:2] != ['0', 'FlowGui.ROM']:
            raise ValueError('Unexpected FlowComm preload origin')
        path = client_root/FLOW_PATH
        if path.stat().st_size > 4*1024*1024:
            raise ValueError('FlowGui input size bound')
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != FLOW_HASH:
            raise ValueError('Pinned FlowGui source changed')
        plain = decode_csvz(raw, limit=4*1024*1024)
        if hashlib.sha256(plain).hexdigest() != FLOW_DECODED_HASH:
            raise ValueError('Pinned FlowGui decode changed')
        self.files[FLOW_PATH], self.decoded['flowgui.romz'] = raw, plain
        self.animation_visits, self.lookup_arguments = [], []
        self.control_arguments, self.native_handle_writes = [], []
        self.rect_apis = {self.u32(0x5706c4): 'copy', self.u32(0x5706c8): 'offset'}
        self.os_apis = {0x775b3420: 'initialize', 0x775a43e0: 'enter',
                        0x775a3460: 'leave', 0x750481f0: 'set_rect',
                        0x75047f20: 'intersect_rect'}
        vm = self.vm
        mapped = set()
        for address in (*self.rect_apis, *self.os_apis):
            page = address & ~4095
            if page not in mapped:
                vm.mem_map(page, 4096, UC_PROT_READ | UC_PROT_EXEC)
                mapped.add(page)
            self.hooks.append(vm.hook_add(UC_HOOK_CODE, self._service, begin=address, end=address))
        for address, size in ((RENDERER, 0x291000), (HIT_REGIONS, 0x13000)):
            vm.mem_map(address, size, UC_PROT_READ | UC_PROT_WRITE)
        for rva in (0x104130, 0x104160, 0x1041a0, 0x104ea0, 0x106c70,
                    0x1afe0, 0x106d75, 0x106c30, 0xff490):
            self.hooks.append(vm.hook_add(UC_HOOK_CODE, self._animation_observe,
                                         begin=BASE+rva, end=BASE+rva))
        self.call(0x297e0, 10*1024*1024, this=BANK)
        self.cstring(SCRATCH, (VIRTUAL_ROOT+'\\data3\\flow\\FlowGui.ROM').encode())
        self.flow_loading = True
        try:
            preload = self.call(0x4b70, self.u32(SCRATCH), this=PREVIEW)
        finally:
            self.flow_loading = False
        if preload != 0:
            raise AssertionError('Real FlowGui preload did not occupy initial slot')
        self.call(0x27400, this=SURFACE)
        self.call(0x1aa10, SURFACE, 0, BANK, this=RENDERER)
        self.call(0x18940, this=HIT_REGIONS)
        self.call(0x104130, this=CONTROL_TABLE)
        self.call(0x104160, 0, HIT_REGIONS, RENDERER, 0, 0, 0, this=CONTROL_TABLE)
        self.empty_controls = bytes(vm.mem_read(CONTROL_TABLE+0x818, 128*0x2a08))
        # C8D4's inputs follow the C8C0 prologue. CopyRect/OffsetRect consume
        # original image rectangles; no coordinates are supplied by the oracle.
        vm.reg_write(UC_X86_REG_ESP, SP)
        vm.reg_write(UC_X86_REG_EAX, SP+0x14)
        vm.reg_write(UC_X86_REG_EBP, self.u32(0x5706c4))
        vm.reg_write(UC_X86_REG_ECX, PREVIEW)
        self.run_slice(0xc8d4, 0xc95e)
        self.window_selector = vm.reg_read(UC_X86_REG_EAX) & 0xffff
        if self.window_selector >= 128:
            raise AssertionError('Original window allocation failed')
        # Preserve the original C97C write of the returned window selector;
        # omit the unrelated control 0..18 creation calls that follow it.
        self.run_slice(0xc95e, 0xc983)
        vm.reg_write(UC_X86_REG_ESP, SP)
        vm.reg_write(UC_X86_REG_ESI, PREVIEW)
        vm.reg_write(UC_X86_REG_EDI, CONTROL_TABLE)
        self.run_slice(0xca33, 0xca9c)
        if vm.reg_read(UC_X86_REG_ESP) != SP:
            raise AssertionError('Native preview control setup stack mismatch')
        self.control_selectors = struct.unpack('<4H', vm.mem_read(BASE+0x183424, 8))

    def run(self, start, stop=0x1000, **budgets):
        if getattr(self, 'flow_loading', False):
            budgets.update(instruction_limit=200000000, timeout_us=60000000)
        return super().run(start, stop, **budgets)

    def _animation_observe(self, vm, address, size, context):
        self.animation_visits.append(address-BASE)
        if address == BASE+0x106c70:
            sp = vm.reg_read(UC_X86_REG_ESP)
            self.control_arguments.append(struct.unpack('<11I', vm.mem_read(sp+4, 44)))
        if address == BASE+0x106d75:
            self.native_handle_writes.append((vm.reg_read(UC_X86_REG_ESI)+0x8c2,
                                             vm.reg_read(UC_X86_REG_EAX) & 0xffff))
        if address == BASE+0x106c30:
            sp = vm.reg_read(UC_X86_REG_ESP)
            self.lookup_arguments.append(tuple(v & 0xffff for v in
                                               struct.unpack('<2I', vm.mem_read(sp+4, 8))))

    def _service(self, vm, address, size, context):
        if address in getattr(self, 'rect_apis', {}):
            sp = vm.reg_read(UC_X86_REG_ESP)
            pointer = self.u32(sp+4)
            if self.rect_apis[address] == 'copy':
                vm.mem_write(pointer, bytes(vm.mem_read(self.u32(sp+8), 16)))
                cleanup = 8
            else:
                x, y = struct.unpack('<2i', vm.mem_read(sp+8, 8))
                a, b, c, d = struct.unpack('<4i', vm.mem_read(pointer, 16))
                vm.mem_write(pointer, struct.pack('<4i', a+x, b+y, c+x, d+y))
                cleanup = 12
            vm.reg_write(UC_X86_REG_EAX, 1)
            vm.reg_write(UC_X86_REG_ESP, sp+4+cleanup)
            vm.reg_write(UC_X86_REG_EIP, self.u32(sp))
            return
        if address == BASE+0x14716f:
            sp = vm.reg_read(UC_X86_REG_ESP)
            path = self.string(self.u32(sp+4)).decode().replace('\\', '/').lower()
            prefix = VIRTUAL_ROOT.replace('\\', '/').lower()+'/'
            if path.startswith(prefix):
                path = path[len(prefix):]
            if path in (FLOW_PATH, FLOW_PATH[:-1]):
                if self.string(self.u32(sp+8)) != b'rb':
                    raise AssertionError('FlowGui read-only input required')
                self.active_name = 'flowgui.romz'
                self.attempts.append(path)
                result = 0
                if path in self.files:
                    self.opens.append(path)
                    result = 0x80000000+4*len(self.opens)
                    self.handles[result] = [self.files[path], 0]
                vm.reg_write(UC_X86_REG_EAX, result)
                vm.reg_write(UC_X86_REG_ESP, sp+4)
                vm.reg_write(UC_X86_REG_EIP, self.u32(sp))
                return
        return super()._service(vm, address, size, context)

    def set_animated_record(self, key, component):
        slot = self.set_record(key, component)
        # CD51..CD5B supplies the 99E0 argument from +178CD4. At 9B66 that
        # same argument is [ESP+130], and [ESP+1C] is the saved preview this.
        selector = struct.unpack('<H', self.vm.mem_read(PREVIEW+0x178cd4, 2))[0]
        if selector != self.window_selector:
            raise AssertionError('Preview window selector changed')
        self.vm.mem_write(SP+0x130, struct.pack('<I', selector))
        self.vm.mem_write(SP+0x1c, struct.pack('<I', PREVIEW))
        self.run_slice(0x9b66, 0x9b97)
        if self.vm.reg_read(UC_X86_REG_ESP) != SP:
            raise AssertionError('Native action assignment stack mismatch')
        handle = struct.unpack('<H', self.vm.mem_read(COMPONENTS+6+6*component, 2))[0]
        return slot, handle


class NativePreviewFrameResources(NativePreviewAnimationResources):
    """Original binding/action/frame consumers for the three qualified assets.

    This is a partial head/face fixture, not full 99E0 or a timed renderer loop.
    Unqualified body/weapon components remain native FFFF sentinels.
    """
    def __init__(self, records=None, client_root=ROOT.parent / 'God2'):
        super().__init__(records, client_root)
        vm = self.vm
        self.frame_visits, self.frame_events = [], []
        for rva in (0xff3c0, 0xff420, 0xffad0, 0xffa20, 0xff8e0, 0xffa60,
                    0x1bf30, 0x1ae20, 0x1c360, 0x1c9e3, 0x1e070):
            self.hooks.append(vm.hook_add(UC_HOOK_CODE, self._frame_observe,
                                         begin=BASE+rva, end=BASE+rva))
        # The recovered preview call at 4567 takes +15E80 and binds +15E38.
        # The offline renderer is the same native pool used by CONTROL_TABLE.
        vm.mem_write(PREVIEW+0x15e80, struct.pack('<I', RENDERER))
        vm.reg_write(UC_X86_REG_ESP, SP)
        vm.reg_write(UC_X86_REG_EBP, PREVIEW)
        self.run_slice(0x455a, 0x456c)
        self.bound_components = bytes(vm.mem_read(COMPONENTS, 0x2c))
        vm.reg_write(UC_X86_REG_ESI, PREVIEW)
        self.run_slice(0xcb7b, 0xcb95)
        # Preserve native local-block writes, but not the filename-cache reset
        # at 9A26: full preload/reset lifetime is outside this partial fixture.
        vm.reg_write(UC_X86_REG_EAX, self.cache)
        vm.reg_write(UC_X86_REG_EDI, PREVIEW)
        self.run_slice(0x9a0e, 0x9a26)
        self.run_slice(0x9a2c, 0x9a69)
        self.component_block = bytes(vm.mem_read(SP+0x10, 8))
        if vm.reg_read(UC_X86_REG_ESP) != SP:
            raise AssertionError('Native preview binding/block stack mismatch')

    def _frame_observe(self, vm, address, size, context):
        self.frame_visits.append(address-BASE)
        if address == BASE+0x1c9e3:
            obj = vm.reg_read(UC_X86_REG_EBP)
            event = vm.reg_read(UC_X86_REG_EBX)
            self.frame_events.append((obj, event, bytes(vm.mem_read(event, 10))))

    def select_component(self, key):
        if key not in KEYS:
            raise ValueError('Qualified preview component key required')
        component = KEYS[key][1]
        slot, handle = self.set_animated_record(key, component)
        if slot >= 512 or handle >= 0x1000:
            raise ValueError('Native preview resource or control unavailable')
        vm = self.vm
        vm.mem_write(SP+0x10, self.component_block)
        vm.reg_write(UC_X86_REG_ESI, SP+0x10+2*component)
        vm.reg_write(UC_X86_REG_EDI, COMPONENTS)
        vm.reg_write(UC_X86_REG_EBX, component)
        self.run_slice(0x9b97, 0x9ba6)
        if vm.reg_read(UC_X86_REG_ESP) != SP:
            raise AssertionError('Native preview variant stack mismatch')
        return slot, handle

    def start_preview_action(self):
        """Execute the actual caller's literal action 6 and palette finalizer."""
        self.vm.reg_write(UC_X86_REG_ESP, SP)
        self.vm.mem_write(SP+0x1c, struct.pack('<I', PREVIEW))
        self.run_slice(0x9bbb, 0x9bd5)
        if self.vm.reg_read(UC_X86_REG_ESP) != SP:
            raise AssertionError('Native preview action stack mismatch')

    def component_object(self, component):
        if component not in (1, 2):
            raise ValueError('Only qualified head/face components are supported')
        slot, handle = struct.unpack('<2H', self.vm.mem_read(COMPONENTS+4+6*component, 4))
        if slot >= 512 or handle >= 0x1000:
            raise ValueError('Native preview resource or control unavailable')
        return RENDERER+0x10+handle*0x290

    def step_component(self, component):
        """Consume the next native action step directly; no elapsed-time claim."""
        obj = self.component_object(component)
        slot = struct.unpack('<H', self.vm.mem_read(COMPONENTS+4+6*component, 2))[0]
        bank = BANK+slot*STRIDE
        if (self.u32(obj+0x34) != bank
                or self.u32(obj+0x38) != self.u32(bank+0x1090+4*6)):
            raise ValueError('Native preview action has not been initialized')
        self.call(0x1c360, obj, this=RENDERER)
        return bytes(self.vm.mem_read(obj, 0x74))
