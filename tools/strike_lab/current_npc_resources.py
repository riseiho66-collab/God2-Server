"""Bounded native NPC resource oracle; never opens a client process or socket.

The caller supplies a hash-pinned Unicorn VM. CRT file I/O, malloc/free/new,
decimal sscanf and a no-files Win32 FindFirstFileA are adapted. Optional render
pool construction adds single-thread critical sections and SetRect. Native
resource/ROM/decompression/allocator functions execute unchanged. An RGB555
test surface is explicit environment, not a live display or a rendered NPC.
"""
import hashlib
from pathlib import Path
import re
import struct

from unicorn import (UC_HOOK_CODE, UC_HOOK_MEM_READ, UC_HOOK_MEM_WRITE,
                     UC_MEM_READ, UC_MEM_WRITE, UC_PROT_READ, UC_PROT_WRITE)
from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_EBX, UC_X86_REG_EBP
from unicorn.x86_const import UC_X86_REG_ECX, UC_X86_REG_ESI, UC_X86_REG_ESP, UC_X86_REG_EIP

from .omega_assets import decode_csvz

BASE, WORLD = 0x400000, 0x4000000
MANAGER = WORLD + 0xaa364b8
TABLE = MANAGER + 0x3d5d4
ROM, SURFACE, STACK, SCRATCH = 0x6000000, 0x6400000, 0x5000000, 0x6500000
SP, RETURN = STACK + 0x3f000, BASE + 0x1000
RENDERER = 0x6700000
ASSETS = {
    19: ('npc2720', 'bd9ce48fd0b23226858e4efe2a0b3bb42ab37c26314297bbc0f9af2a81b47d8d',
         'ed12b235fd24d7961f7ed8766180c3e56456d5acf71c57a86b92297bd25e2836'),
    81: ('npc2782', '4470c07c172325c302ecf1029003eb30d46edc7cfce87ee8544814bef47c9d8a',
         'f75845298b902d9ce0131b9a746d75dcfdb0ef7705318d6e9adff81d180444a2'),
    87: ('npc2788', '03f8d6922eb618aa0d7cc7efa21944b61dd505a8a9bc503de4eca435ffb685f7',
         '05f2e2de725a6ae0dce266a77a7bf11a54f0b8da4991d3dd9452be75e5a50746'),
}


class NativeNpcResources:
    def __init__(self, vm, client_root, *, extended_decode_budget=False):
        self.vm = vm
        self.extended_decode_budget = extended_decode_budget
        self.files, self.decoded, self.handles = {}, {}, {}
        self.opens, self.allocations = [], {}
        self.native_decodes = []
        self.seh_accesses = set()
        self.renderer_ready = False
        self.locks = {}
        self.heap_next, self.heap_limit = 0x9000000, 0xd000000
        self.hooks = []
        client_root = Path(client_root)
        for ordinal, (name, raw_sha, decoded_sha) in ASSETS.items():
            path = 'Data2/Rom/Npc/' + name + '.ROMZ'
            raw = (client_root / path).read_bytes()
            decoded = decode_csvz(raw, limit=1024*1024)
            if (hashlib.sha256(raw).hexdigest(), hashlib.sha256(decoded).hexdigest()) != (raw_sha, decoded_sha):
                raise AssertionError('Current NPC ROM changed: ' + path)
            self.files[path.lower()] = raw
            self.decoded[ordinal] = decoded
        # The caller already mapped MANAGER's first page for the catalog pointer.
        start = (MANAGER & ~4095) + 4096
        vm.mem_map(start, 0x170000)
        for address, size in ((ROM, 0x2a4000), (SURFACE, 0x2000),
                              (STACK, 0x40000), (SCRATCH, 0x10000), (0, 4096)):
            vm.mem_map(address, size)
        # FS has base zero in this bounded x86 oracle. Permit only the pinned
        # ROM loader's SEH chain accesses, never arbitrary null dereferences.
        vm.mem_write(0, struct.pack('<I', 0xffffffff))
        self.hooks.append(vm.hook_add(UC_HOOK_MEM_READ | UC_HOOK_MEM_WRITE,
                                     self._seh, begin=0, end=4095))
        # Original decompressor globals and ROM ACT_DATA scratch only.
        for page in (0x5b0000, 0x5b5000):
            vm.mem_protect(page, 4096, UC_PROT_READ | UC_PROT_WRITE)
        for rva in (0x14716f, 0x147182, 0x1474ab, 0x1474dc, 0x14785c,
                    0x1477a3, 0x147973, 0x1479ff, 0x1480b4, 0x2c70, 0x2dc0):
            self.hooks.append(vm.hook_add(UC_HOOK_CODE, self._crt,
                                         begin=BASE+rva, end=BASE+rva))
        # 2170 destroys the last decompressor and searches for temporary files.
        # The virtual read-only namespace has none. No host filesystem call.
        self.find_first = struct.unpack('<I', vm.mem_read(0x57042c, 4))[0]
        vm.mem_map(self.find_first & ~4095, 4096)
        self.hooks.append(vm.hook_add(UC_HOOK_CODE, self._crt,
                                     begin=self.find_first, end=self.find_first))
        self.hooks.append(vm.hook_add(UC_HOOK_CODE, self._observe_rom,
                                     begin=BASE+0x2a1d0, end=BASE+0x2a1d0))
        self.call(0x2030)
        self.call(0x28610, this=ROM+0x2a2800)
        self.call(0x286d0, 0x200000, 0x200000, this=ROM+0x2a2800)
        vm.mem_write(SURFACE+0x1210, struct.pack('<3H', 0x7c00, 0x3e0, 0x1f))
        vm.mem_write(SURFACE+0x121a, bytes((10, 5, 0)))
        self.call(0x2b180, SURFACE, this=ROM)

    def _seh(self, vm, access, address, size, value, context):
        pc = vm.reg_read(UC_X86_REG_EIP)
        allowed = {
            BASE+0x2982a: (UC_MEM_READ, b'\x64\xa1\0\0\0\0'),
            BASE+0x29831: (UC_MEM_WRITE, b'\x64\x89\x25\0\0\0\0'),
            BASE+0x29a9d: (UC_MEM_WRITE, b'\x64\x89\x0d\0\0\0\0'),
        }
        if self.renderer_ready:
            allowed.update({
                BASE+0x1aa17: (UC_MEM_READ, b'\x64\xa1\0\0\0\0'),
                BASE+0x1aa1e: (UC_MEM_WRITE, b'\x64\x89\x25\0\0\0\0'),
                BASE+0x1abe3: (UC_MEM_WRITE, b'\x64\x89\x0d\0\0\0\0'),
            })
        expected = allowed.get(pc)
        if (address != 0 or size != 4 or expected is None or
                access != expected[0] or
                bytes(vm.mem_read(pc, len(expected[1]))) != expected[1]):
            raise AssertionError('Unexpected low-page access outside native SEH')
        self.seh_accesses.add(pc-BASE)

    def run(self, entry, stop=RETURN-BASE):
        factor=3 if self.extended_decode_budget else 1
        self.vm.emu_start(BASE+entry, BASE+stop, timeout=15000000*factor, count=20000000*factor)
        pc = self.vm.reg_read(UC_X86_REG_EIP)
        if pc != BASE+stop:
            raise AssertionError(f'Native NPC bound ended at RVA {pc-BASE:x}, expected {stop:x}')

    def call(self, entry, *args, this=TABLE):
        self.vm.reg_write(UC_X86_REG_ECX, this)
        self.vm.reg_write(UC_X86_REG_ESP, SP)
        self.vm.mem_write(SP, struct.pack('<'+'I'*(len(args)+1), RETURN, *args))
        self.run(entry)
        if self.vm.reg_read(UC_X86_REG_ESP) != SP+4+4*len(args):
            raise AssertionError('Unexpected native callee stack cleanup')
        return self.vm.reg_read(UC_X86_REG_EAX)

    def string(self, pointer, limit=512):
        raw = bytes(self.vm.mem_read(pointer, limit))
        if b'\0' not in raw:
            raise AssertionError('Unbounded native string')
        return raw.split(b'\0', 1)[0]

    def _crt(self, vm, address, size, context):
        rva = address-BASE
        sp = vm.reg_read(UC_X86_REG_ESP)
        ret, *args = struct.unpack('<5I', vm.mem_read(sp, 20))
        if address == self.find_first:
            if ret != BASE+0x297f:
                raise AssertionError('Unexpected temporary-file cleanup caller')
            vm.reg_write(UC_X86_REG_EAX, 0xffffffff)
            vm.reg_write(UC_X86_REG_ESP, sp+12)  # FindFirstFileA, stdcall.
            vm.reg_write(UC_X86_REG_EIP, ret)
            return
        if rva in (0x2c70, 0x2dc0):
            raise AssertionError(f'Native assertion/dialog RVA {rva:x}, caller {ret-BASE:x}')
        if rva == 0x147973:
            size = args[0]
            end = self.heap_next + ((size+4095) & ~4095)
            if not 0 < size <= 0x1000000 or end > self.heap_limit:
                raise AssertionError('Native allocation exceeds oracle bound')
            result = self.heap_next
            vm.mem_map(result, end-result)
            self.allocations[result] = size
            self.heap_next = end
        elif rva == 0x1479ff:
            if args[0] and args[0] not in self.allocations:
                raise AssertionError('Free of unknown allocation')
            result = 0
        elif rva == 0x1480b4:
            if self.string(args[1], 4) != b'%d':
                raise AssertionError('Unsupported sscanf format')
            raw = self.string(args[0], 380)
            match = re.match(rb'^[ \t]*([+-]?[0-9]+)', raw)
            result = int(match is not None)
            if match:
                value = int(match[1])
                if not -(1<<31) <= value < (1<<31):
                    raise AssertionError('Decimal exceeds native int')
                vm.mem_write(args[2], struct.pack('<i', value))
        elif rva == 0x14716f:
            path = self.string(args[0]).decode('ascii').replace('\\', '/').lower()
            if path.startswith('./'):
                path = path[2:]
            if self.string(args[1], 4) != b'rb' or path not in self.files:
                raise AssertionError('Native open outside pinned ROM allowlist: '+path)
            self.opens.append(path)
            result = 0x80000000 + 4*len(self.opens)
            self.handles[result] = [self.files[path], 0]
        elif rva == 0x147182:
            self.handles.pop(args[0])
            result = 0
        elif rva in (0x1474ab, 0x1474dc):
            data, position = self.handles[args[0]]
            result = data[position] if position < len(data) else 0xffffffff
            self.handles[args[0]][1] += int(position < len(data))
        elif rva == 0x1477a3:
            if args[1] != 0 or args[2] != 0:  # Only fseek(file, 0, SEEK_SET).
                raise AssertionError('Unexpected native seek')
            self.handles[args[0]][1] = 0
            result = 0
        elif rva == 0x14785c:
            output, width, count, handle = args
            data, position = self.handles[handle]
            length = width*count
            if not width or length > 0x1000000 or position+length > len(data):
                raise AssertionError('Native fread outside pinned input')
            vm.mem_write(output, data[position:position+length])
            self.handles[handle][1] += length
            result = count
        else:
            raise AssertionError('Unimplemented CRT adapter')
        vm.reg_write(UC_X86_REG_EAX, result)
        vm.reg_write(UC_X86_REG_ESP, sp+4)
        vm.reg_write(UC_X86_REG_EIP, ret)

    def _observe_rom(self, vm, address, size, context):
        sp = vm.reg_read(UC_X86_REG_ESP)
        ret, source, slot, length = struct.unpack('<4I', vm.mem_read(sp, 16))
        if ret != BASE+0x299d6 or not self.opens:
            raise AssertionError('Unexpected ROM parser caller')
        ordinal = next(o for o, (name, _, _) in ASSETS.items()
                       if self.opens[-1].endswith('/'+name+'.romz'))
        expected = self.decoded[ordinal]
        if length != len(expected)+3 or bytes(vm.mem_read(source, len(expected))) != expected:
            raise AssertionError('Native LZSS output differs from pinned decoded asset')
        self.native_decodes.append((ordinal, slot, len(expected)))

    def load_csv(self, decoded):
        lines = decoded.replace(b'\r\n', b'\n').splitlines()
        start = int(lines[0].split(b',')[2])-1
        rows = lines[start:]
        if len(rows) != 319:
            raise AssertionError('Pinned NPC table row count changed')
        # 60CC8 supplies eight columns to 5E850. Enter after its prologue,
        # before the real table clear; CSV file-opening/header skipping is external.
        self.vm.reg_write(UC_X86_REG_ESP, SP)
        self.vm.reg_write(UC_X86_REG_EBP, TABLE)
        self.run(0x5e85c, 0x5e8b4)
        self.call(0x51920, 8, this=TABLE+0x121f0)
        ordinal = 0
        for row in rows:
            if len(row) > 4094:
                raise AssertionError('CSV line exceeds native input buffer')
            self.vm.mem_write(SCRATCH, row+b'\n\0')
            self.call(0x51be0, SCRATCH, this=TABLE+0x121f0)
            self.vm.reg_write(UC_X86_REG_ESP, SP)
            self.vm.reg_write(UC_X86_REG_EBP, TABLE)
            self.vm.reg_write(UC_X86_REG_EBX, TABLE+0x121f0)
            self.vm.reg_write(UC_X86_REG_ESI, ordinal)
            self.vm.mem_write(SP+0x128, struct.pack('<I', 8))
            self.run(0x5e9b0, 0x5ebf7)
            ordinal = self.vm.reg_read(UC_X86_REG_ESI)
        return ordinal

    def configure_empty_bank(self):
        # Explicit initially-empty bank: 5E7D0 assigns its next slot counter 0.
        # It is not a claim that the live world's next resource slot is zero.
        self.vm.mem_write(SCRATCH, b'.\\\0')
        self.call(0x5e7d0, 0, ROM, SCRATCH, 0, 0)

    def load_ordinal(self, ordinal):
        if ordinal not in ASSETS:
            raise ValueError('Only explicitly pinned resources are allowed')
        # Executes 5F0E0 -> 5EEC0 -> 29820 -> 1EC0 -> 2A1D0, then commits
        # the actual successful slot and increments the native bank counter.
        return self.call(0x5f0e0, 0, ordinal)

    def initialize_renderer(self):
        """Real NPC render/command pools; no scene, viewport or device binding."""
        if self.renderer_ready:
            raise AssertionError('NPC renderer already initialized')
        vm = self.vm
        vm.mem_map(SURFACE+0x2000, 0xfe000, UC_PROT_READ | UC_PROT_WRITE)
        vm.mem_map(RENDERER, 0x291000, UC_PROT_READ | UC_PROT_WRITE)
        # Constructor registry shared with the original renderer implementation.
        vm.mem_protect(0x5b4000, 4096, UC_PROT_READ | UC_PROT_WRITE)
        self.renderer_apis = {
            0x775b3420: 'initialize', 0x775a43e0: 'enter',
            0x775a3460: 'leave', 0x750481f0: 'set_rect',
        }
        for pointer in self.renderer_apis:
            vm.mem_map(pointer & ~4095, 4096)
        for pointer in (*self.renderer_apis, BASE+0x15b406):
            self.hooks.append(vm.hook_add(UC_HOOK_CODE, self._renderer_service,
                                         begin=pointer, end=pointer))
        self.renderer_ready = True
        self.call(0x27400, this=SURFACE)
        self.call(0x1aa10, SURFACE, 0, ROM, this=RENDERER)

    def _renderer_service(self, vm, address, size, context):
        sp = vm.reg_read(UC_X86_REG_ESP)
        ret, *args = struct.unpack('<6I', vm.mem_read(sp, 24))
        if address == BASE+0x15b406:
            # operator new uses the same bounded allocation contract as malloc.
            self._crt(vm, BASE+0x147973, size, context)
            return
        api = self.renderer_apis[address]
        result, cleanup = 0, 4
        if api == 'set_rect':
            vm.mem_write(args[0], struct.pack('<4I', *args[1:5]))
            result, cleanup = 1, 20
        elif api == 'initialize':
            if args[0] in self.locks:
                raise AssertionError('Duplicate NPC critical-section initialization')
            self.locks[args[0]] = 0
        else:
            if args[0] not in self.locks:
                raise AssertionError('Uninitialized NPC critical section')
            self.locks[args[0]] += 1 if api == 'enter' else -1
            if self.locks[args[0]] < 0:
                raise AssertionError('Unbalanced NPC critical section')
        vm.reg_write(UC_X86_REG_EAX, result)
        vm.reg_write(UC_X86_REG_ESP, sp+4+cleanup)
        vm.reg_write(UC_X86_REG_EIP, ret)
