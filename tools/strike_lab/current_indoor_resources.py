"""Bounded native indoor loader oracle, not a live client or graphics device.

CRT/MFC adapters expose a virtual filesystem and bounded memory. The HMD input
is a hash-pinned plain variant cross-checked with original decompression; ROMZ
decompression and all model/resource lookups execute original code. Single-thread
Win32 lock/rectangle adapters and an RGB555 test surface are explicit inputs.
No host files are modified and no real graphics device is created.
"""
import hashlib
import re
import struct

from unicorn import (UC_HOOK_CODE, UC_HOOK_MEM_READ, UC_HOOK_MEM_WRITE,
                     UC_MEM_READ, UC_MEM_WRITE, UC_PROT_READ, UC_PROT_WRITE)
from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_ECX, UC_X86_REG_ESP, UC_X86_REG_EIP
from .omega_assets import decode_csvz

BASE = 0x400000
INDOOR, SURFACE, STACK, SCRATCH = 0x6000000, 0x6400000, 0x6500000, 0x6600000
SP, RETURN = STACK + 0x7f000, BASE + 0x1000
RENDERER = 0x6700000
MANAGER = 0x7000000
DIRECTORY = 'data2/map/island01/indoor/'
ASSETS = {
    'groceryl.hmdz': '42d769c0ff328db3e1e295e17208d0db7a0ff12608976f952dae800ff79c3c00',
    'grol.romz': '20e5a8be548993e9d17cca9b2d9292b150f73b7907ed720256132ef4659bce6c',
}


class NativeIndoorResources:
    def __init__(self, vm, client_root):
        self.vm = vm
        self.files, self.handles, self.opens = {}, {}, []
        self.allocations, self.freed = {}, set()
        self.heap, self.heap_limit = 0x9000000, 0x11000000
        self.seh_accesses, self.calls = set(), set()
        self.locks, self.exit_callbacks = {}, []
        self.hooks = []
        for name, sha in ASSETS.items():
            raw = (client_root / DIRECTORY / name).read_bytes()
            if hashlib.sha256(raw).hexdigest() != sha:
                raise AssertionError('Pinned indoor asset changed: ' + name)
            if name.endswith('.hmdz'):
                self.hmd_raw = raw
                self.hmd = decode_csvz(raw, limit=1024*1024)
                self.files[DIRECTORY + name[:-1]] = self.hmd
            else:
                self.files[DIRECTORY + name] = raw
                self.rom = decode_csvz(raw, limit=8*1024*1024)
        for address, length in ((0, 4096), (INDOOR, 0x2a3000),
                                (SURFACE, 0x100000), (STACK, 0x80000), (SCRATCH, 0x10000),
                                (RENDERER, 0x291000)):
            vm.mem_map(address, length)
        vm.mem_write(0, struct.pack('<I', 0xffffffff))
        for page in (0x5b0000, 0x5b4000, 0x5b5000):
            vm.mem_protect(page, 4096, UC_PROT_READ | UC_PROT_WRITE)
        self.hooks.append(vm.hook_add(UC_HOOK_MEM_READ | UC_HOOK_MEM_WRITE,
                                     self._seh, begin=0, end=4095))
        services = (0x14716f, 0x147182, 0x1474ab, 0x1474dc, 0x14785c, 0x1477a3,
                    0x147973, 0x1479ff, 0x15b406, 0x15b42f, 0x1490ad,
                    0x149657, 0x149a00, 0x151de0, 0x149b00,
                    0x15ada3, 0x15aaaa, 0x15ae6e, 0x15aebe, 0x15afca, 0x15ad35, 0x158a58,
                    0x14741f, 0x2c70, 0x2dc0, 0x1070, 0x1651a4)
        for rva in services:
            self.hooks.append(vm.hook_add(UC_HOOK_CODE, self._service,
                                         begin=BASE+rva, end=BASE+rva))
        self.find_first = self.u32(0x57042c)
        vm.mem_map(self.find_first & ~4095, 4096)
        self.hooks.append(vm.hook_add(UC_HOOK_CODE, self._service,
                                     begin=self.find_first, end=self.find_first))
        # Resolved against captured module bases and the matching SysWOW64 exports.
        self.os_apis = {0x775b3420: 'initialize', 0x775a43e0: 'enter',
                        0x775a3460: 'leave', 0x750481f0: 'set_rect',
                        0x75047f20: 'intersect_rect'}
        for pointer in self.os_apis:
            vm.mem_map(pointer & ~4095, 4096)
            self.hooks.append(vm.hook_add(UC_HOOK_CODE, self._service,
                                         begin=pointer, end=pointer))
        self.call(0x2030)
        self.validate_hmd_decompression()
        self.call(0x362f0, this=INDOOR)
        vm.mem_write(SURFACE+0x1210, struct.pack('<3H', 0x7c00, 0x3e0, 0x1f))
        vm.mem_write(SURFACE+0x121a, bytes((10, 5, 0)))
        self.call(0x2b180, SURFACE, this=INDOOR+0x2c4)
        self.call(0x27400, this=SURFACE)  # Original 5000-entry surface command pool reset.
        self.call(0x1aa10, SURFACE, 0, INDOOR+0x2c4, this=RENDERER)
        vm.mem_write(INDOOR+0x2a2f0c, struct.pack('<I', RENDERER))

    def u32(self, address):
        return struct.unpack('<I', self.vm.mem_read(address, 4))[0]

    def string(self, pointer, limit=1024):
        result = bytearray()
        for offset in range(limit):
            byte = bytes(self.vm.mem_read(pointer+offset, 1))
            if byte == b'\0':
                return bytes(result)
            result.extend(byte)
        raise AssertionError('Unbounded native string')

    def allocate(self, length):
        rounded = (length+4095) & ~4095
        if not 0 < length <= 0x1000000 or self.heap+rounded > self.heap_limit:
            raise AssertionError('Native indoor allocation bound')
        pointer = self.heap
        self.heap += rounded
        self.vm.mem_map(pointer, rounded, UC_PROT_READ | UC_PROT_WRITE)
        self.allocations[pointer] = length
        return pointer

    def cstring(self, destination, value):
        if len(value) > 1024:
            raise AssertionError('CString bound')
        pointer = self.allocate(len(value)+13)
        self.vm.mem_write(pointer, struct.pack('<III', 1, len(value), len(value))+value+b'\0')
        self.vm.mem_write(destination, struct.pack('<I', pointer+12))

    def _seh(self, vm, access, address, size, value, context):
        pc = vm.reg_read(UC_X86_REG_EIP)
        code = bytes(vm.mem_read(pc, 7))
        read = code[:6] == b'\x64\xa1\0\0\0\0'
        write = code in (b'\x64\x89\x25\0\0\0\0', b'\x64\x89\x0d\0\0\0\0')
        if (not BASE <= pc < BASE+0x170000 or address != 0 or size != 4 or
                not ((access == UC_MEM_READ and read) or (access == UC_MEM_WRITE and write))):
            raise AssertionError('Unexpected low-page access outside native SEH')
        self.seh_accesses.add(pc-BASE)

    def run(self, start, stop=RETURN-BASE, *, instruction_limit=50000000, timeout_us=30000000):
        try:
            self.vm.emu_start(BASE+start, BASE+stop, timeout=timeout_us, count=instruction_limit)
        except Exception as error:
            pc = self.vm.reg_read(UC_X86_REG_EIP)-BASE
            raise AssertionError(f'Indoor native failure RVA {pc:x}: {error}') from error
        pc = self.vm.reg_read(UC_X86_REG_EIP)
        if pc != BASE+stop:
            raise AssertionError(f'Indoor execution bound at {pc-BASE:x}; expected {stop:x}')

    def call(self, start, *args, this=INDOOR):
        self.vm.reg_write(UC_X86_REG_ECX, this)
        self.vm.reg_write(UC_X86_REG_ESP, SP)
        self.vm.mem_write(SP, struct.pack('<'+'I'*(len(args)+1), RETURN, *args))
        if start in (0x49330, 0x493c0, 0x4c6f0):
            # Tiny bounded accessors: avoid spawning thousands of timeout threads.
            self.run(start, instruction_limit=1000, timeout_us=0)
        else:
            self.run(start)
        if self.vm.reg_read(UC_X86_REG_ESP) != SP+4+4*len(args):
            raise AssertionError('Unexpected native stack cleanup')
        return self.vm.reg_read(UC_X86_REG_EAX)

    def load(self):
        self.vm.mem_write(SCRATCH, (DIRECTORY+'groceryl.hmd').replace('/', '\\').encode()+b'\0')
        return self.call(0x37900, 0, SCRATCH)

    def validate_hmd_decompression(self):
        context = self.allocate(0xd440)
        output = self.allocate(len(self.hmd)+3)
        handle = 0x80010000
        self.handles[handle] = [self.hmd_raw, 0]
        self.call(0x1760, this=context)
        self.call(0x1ec0, handle, output, this=context)
        if bytes(self.vm.mem_read(output, len(self.hmd))) != self.hmd:
            raise AssertionError('Original HMD decompression differs from plain fixture')
        self.handles.pop(handle)
        self.call(0x17b0, this=context)

    def load_manager(self):
        self.vm.mem_map(MANAGER, 0x2000)
        self.call(0x42a60, this=MANAGER)
        # Explicit test-device bindings, not a recovered live DirectDraw device.
        self.vm.mem_write(MANAGER+0x1678, struct.pack('<II', SURFACE, 0))
        self.vm.mem_write(SCRATCH, (DIRECTORY+'groceryl.hmd').replace('/', '\\').encode()+b'\0')
        return self.call(0x48300, 0, SCRATCH, this=MANAGER)

    def _service(self, vm, address, size, context):
        rva = address-BASE
        self.calls.add(rva)
        sp = vm.reg_read(UC_X86_REG_ESP)
        ret = self.u32(sp)
        arg = lambda index: self.u32(sp+4+4*index)
        this = vm.reg_read(UC_X86_REG_ECX)
        result, cleanup = 0, 0
        if address in self.os_apis:
            api = self.os_apis[address]
            if api in ('initialize', 'enter', 'leave'):
                pointer = arg(0)
                if api == 'initialize':
                    if pointer in self.locks:
                        raise AssertionError('Duplicate critical-section initialization')
                    self.locks[pointer] = 0
                else:
                    if pointer not in self.locks:
                        raise AssertionError('Uninitialized critical section')
                    self.locks[pointer] += 1 if api == 'enter' else -1
                    if self.locks[pointer] < 0:
                        raise AssertionError('Unbalanced critical section')
                cleanup = 4
            elif api == 'set_rect':
                vm.mem_write(arg(0), struct.pack('<4I', *(arg(i) for i in range(1, 5))))
                result, cleanup = 1, 20
            else:
                a = struct.unpack('<4i', vm.mem_read(arg(1), 16))
                b = struct.unpack('<4i', vm.mem_read(arg(2), 16))
                rect = (max(a[0], b[0]), max(a[1], b[1]), min(a[2], b[2]), min(a[3], b[3]))
                result = int(rect[0] < rect[2] and rect[1] < rect[3])
                vm.mem_write(arg(0), struct.pack('<4i', *(rect if result else (0, 0, 0, 0))))
                cleanup = 12
        elif address == self.find_first:
            if ret != BASE+0x297f:
                raise AssertionError('Unexpected virtual temporary-file search')
            result, cleanup = 0xffffffff, 8
        elif rva in (0x2c70, 0x2dc0, 0x1070, 0x1651a4):
            raise AssertionError(f'Native diagnostic {rva:x}, caller {ret-BASE:x}')
        elif rva in (0x147973, 0x15b406):
            result = self.allocate(arg(0))
        elif rva in (0x1479ff, 0x15b42f):
            pointer = arg(0)
            if pointer and (pointer not in self.allocations or pointer in self.freed):
                raise AssertionError('Unknown/double native free')
            self.freed.add(pointer)
        elif rva == 0x14741f:
            self.exit_callbacks.append(arg(0))
        elif rva in (0x15ada3, 0x15aaaa, 0x15ae6e, 0x15aebe):
            pointer = arg(0) if rva in (0x15ada3, 0x15aebe) else self.u32(arg(0))
            self.cstring(this, self.string(pointer))
            result, cleanup = this, 4
        elif rva == 0x15afca:
            self.cstring(arg(0), self.string(self.u32(arg(1)))+self.string(arg(2)))
            result, cleanup = arg(0), 12
        elif rva == 0x158a58:
            count = arg(1)
            if count > 1024:
                raise AssertionError('CString Left bound')
            self.cstring(arg(0), self.string(self.u32(this))[:count])
            result, cleanup = arg(0), 8
        elif rva == 0x15ad35:
            pass  # CString allocations have oracle lifetime, bounded above.
        elif rva == 0x149b00:
            index = self.string(arg(0)).rfind(bytes([arg(1)]))
            result = arg(0)+index if index >= 0 else 0
        elif rva in (0x149657, 0x149a00, 0x151de0):
            left, right = self.string(arg(0)), self.string(arg(1))
            if rva == 0x151de0:
                left, right = left.lower(), right.lower()
            result = ((left > right)-(left < right)) & 0xffffffff
        elif rva == 0x14716f:
            path = self.string(arg(0)).decode('ascii').replace('\\', '/').lower()
            if self.string(arg(1)) not in (b'rb', b'rt'):
                raise AssertionError('Virtual filesystem is read-only')
            if path == DIRECTORY+'groceryl.hmdz':
                result = 0  # Explicit plain-HMD fixture namespace, not a host probe.
            elif path in self.files:
                self.opens.append(path)
                result = 0x80000000+4*len(self.opens)
                self.handles[result] = [self.files[path], 0]
            else:
                raise AssertionError('Unqualified indoor file: '+path)
        elif rva == 0x147182:
            self.handles.pop(arg(0))
        elif rva in (0x1474ab, 0x1474dc):
            handle = self.handles[arg(0)]
            data, position = handle
            result = data[position] if position < len(data) else 0xffffffff
            handle[1] += int(position < len(data))
        elif rva == 0x1477a3:
            if (arg(1), arg(2)) != (0, 0):
                raise AssertionError('Unsupported fseek')
            self.handles[arg(0)][1] = 0
        elif rva == 0x14785c:
            handle = self.handles[arg(3)]
            data, position = handle
            width, count = arg(1), arg(2)
            length = width*count
            if not width or length > 0x1000000 or position+length > len(data):
                raise AssertionError('Bounded fread exceeded input')
            vm.mem_write(arg(0), data[position:position+length])
            handle[1] += length
            result = count
        elif rva == 0x1490ad:
            handle = self.handles[arg(0)]
            for index, fmt in enumerate(self.string(arg(1)).split()):
                match = re.match(rb'\s*(\S+)', handle[0][handle[1]:])
                if not match:
                    break
                token = match[1]
                if fmt == b'%d':
                    if not re.fullmatch(rb'[+-]?[0-9]+', token):
                        break
                    vm.mem_write(arg(index+2), struct.pack('<i', int(token)))
                elif fmt == b'%s' and len(token) < 256:
                    vm.mem_write(arg(index+2), token+b'\0')
                else:
                    raise AssertionError('Unsupported fscanf format '+repr(fmt))
                handle[1] += match.end()
                result += 1
        else:
            raise AssertionError(f'Unhandled adapter {rva:x}')
        vm.reg_write(UC_X86_REG_EAX, result)
        vm.reg_write(UC_X86_REG_ESP, sp+4+cleanup)
        vm.reg_write(UC_X86_REG_EIP, ret)
