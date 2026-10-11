"""Pinned RoleDoll ROMZ through the original uncached loader, without a client.

Uses the indoor oracle's bounded CRT/memory adapters but constructs only a ROM
bank and explicit RGB555 format input. No graphics device or renderer executes.
"""
import hashlib
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'artifacts/tooling/crypto-oracle-python'))
from unicorn import (Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE,
                     UC_HOOK_MEM_READ, UC_HOOK_MEM_WRITE, UC_PROT_READ,
                     UC_PROT_WRITE, UC_PROT_EXEC)
from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_ESP, UC_X86_REG_EIP
from .current_indoor_resources import NativeIndoorResources, BASE, SURFACE, STACK, SCRATCH
from .omega_assets import decode_csvz

BANK, STRIDE = 0x6000000, 0x1514
DIRECTORY = 'data2/rom/roledoll/'
IMAGE_SHA = '149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
ASSETS = {
    'r01w800.romz': (
        'd64f1c25bc93fcedd4920347e70fc55d6385a5c188043ffcc3a96725c2d72440',
        '53018d6aec69d67ba5611cbe307cc08ebe9920a3a127d9d77bc86662e7fd7071'),
    'r01f002.romz': (
        '0229239796e372609539121890ed4afa64cefe5d3d1b01adff58ca1ddab874d0',
        '9742ca3c81787acd58af2a5af943b1f2b7501ed80bf672be3a85cda64d9f77ba'),
    'r02f002.romz': (
        'fe544837905075a6d46c2217f169a762edee63c04739f6e31a0e11b64c7c5120',
        '5401efd34ab14c5215e3604ad2802bca7a47b79ac9af0c033649f85ff4ab4b5d'),
}


def source_assets(client_root):
    files, decoded = {}, {}
    for name, (raw_sha, decoded_sha) in ASSETS.items():
        path = Path(client_root) / DIRECTORY / name
        if path.stat().st_size > 1024*1024:
            raise ValueError('RoleDoll source size bound')
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != raw_sha:
            raise ValueError('Pinned RoleDoll source changed: '+name)
        plain = decode_csvz(raw, limit=1024*1024)
        if hashlib.sha256(plain).hexdigest() != decoded_sha:
            raise ValueError('Pinned RoleDoll decode changed: '+name)
        files[DIRECTORY+name], decoded[name] = raw, plain
    return files, decoded


class NativeRoleDollResources(NativeIndoorResources):
    heap_start_address = 0x9000000
    heap_end_address = 0x11000000
    bank_capacity = 4*1024*1024

    def __init__(self, client_root=ROOT.parent / 'God2'):
        image = (ROOT / 'artifacts/capture_work/host-20260918-1430/output/'
                 'native-master-01-stable.bin').read_bytes()
        if hashlib.sha256(image).hexdigest() != IMAGE_SHA:
            raise ValueError('Pinned original image changed')
        self.files, self.decoded = source_assets(client_root)
        self.vm = vm = Uc(UC_ARCH_X86, UC_MODE_32)
        image_size = (len(image)+4095) & ~4095
        vm.mem_map(BASE, image_size, UC_PROT_READ | UC_PROT_EXEC)
        vm.mem_write(BASE, image)
        self.handles, self.opens, self.attempts = {}, [], []
        self.allocations, self.freed = {}, set()
        self.heap, self.heap_limit = self.heap_start_address, self.heap_end_address
        self.seh_accesses, self.calls = set(), set()
        self.locks, self.exit_callbacks = {}, []
        self.os_apis, self.find_first = {}, -1
        self.native_visits, self.parser_inputs = [], []
        self.active_name = None
        self.hooks = []
        for address, size in ((0, 4096), (BANK, 0x2a3000),
                              (SURFACE, 0x100000), (STACK, 0x80000), (SCRATCH, 0x10000)):
            vm.mem_map(address, size, UC_PROT_READ | UC_PROT_WRITE)
        vm.mem_write(0, struct.pack('<I', 0xffffffff))
        for page in (0x5b0000, 0x5b4000, 0x5b5000):
            vm.mem_protect(page, 4096, UC_PROT_READ | UC_PROT_WRITE)
        self.hooks.append(vm.hook_add(UC_HOOK_MEM_READ | UC_HOOK_MEM_WRITE,
                                     self._seh, begin=0, end=4095))
        # Only CRT allocation/file/string functions and fail-closed diagnostics.
        for rva in (0x14716f, 0x147182, 0x1474ab, 0x1474dc, 0x14785c, 0x1477a3,
                    0x147973, 0x1479ff, 0x15b406, 0x15b42f,
                    0x149657, 0x149a00, 0x151de0, 0x14741f,
                    0x2c70, 0x2dc0, 0x1070, 0x1651a4):
            self.hooks.append(vm.hook_add(UC_HOOK_CODE, self._service,
                                         begin=BASE+rva, end=BASE+rva))
        self.find_first = self.u32(0x57042c)
        vm.mem_map(self.find_first & ~4095, 4096, UC_PROT_READ | UC_PROT_EXEC)
        self.hooks.append(vm.hook_add(UC_HOOK_CODE, self._service,
                                     begin=self.find_first, end=self.find_first))
        for rva in (0x29820, 0x1ec0, 0x2a1d0, 0x2c090, 0x2d250, 0x2d930, 0x28740):
            self.hooks.append(vm.hook_add(UC_HOOK_CODE, self._observe,
                                         begin=BASE+rva, end=BASE+rva))
        self.call(0x2030)
        self.call(0x29700, this=BANK)
        # Explicit fixture capacity; native ROM pool allocation remains original.
        self.call(0x297e0, self.bank_capacity, this=BANK)
        vm.mem_write(SURFACE+0x1210, struct.pack('<3H', 0x7c00, 0x3e0, 0x1f))
        vm.mem_write(SURFACE+0x121a, bytes((10, 5, 0)))
        self.call(0x2b180, SURFACE, this=BANK)

    def _observe(self, vm, address, size, context):
        rva = address-BASE
        self.native_visits.append(rva)
        if rva == 0x2a1d0:
            sp = vm.reg_read(UC_X86_REG_ESP)
            pointer, slot, length = struct.unpack('<3I', vm.mem_read(sp+4, 12))
            expected = self.decoded[self.active_name]
            if length != len(expected)+3:
                raise AssertionError('Unexpected native decompression buffer length')
            if bytes(vm.mem_read(pointer, len(expected))) != expected:
                raise AssertionError('Original RoleDoll decompression differs from source')
            self.parser_inputs.append((self.active_name, slot, len(expected)))

    def _service(self, vm, address, size, context):
        if address != BASE+0x14716f:
            return super()._service(vm, address, size, context)
        sp = vm.reg_read(UC_X86_REG_ESP)
        path = self.string(self.u32(sp+4)).decode('ascii').replace('\\', '/').lower()
        if self.string(self.u32(sp+8)) != b'rb':
            raise AssertionError('RoleDoll virtual filesystem is read-only')
        if path not in {DIRECTORY+name for name in ASSETS}:
            raise AssertionError('Unqualified RoleDoll path: '+path)
        self.calls.add(0x14716f)
        self.attempts.append(path)
        result = 0
        if path in self.files:
            self.opens.append(path)
            result = 0x80000000+4*len(self.opens)
            self.handles[result] = [self.files[path], 0]
        # Missing qualified files produce actual fopen NULL; no resource handle.
        vm.reg_write(UC_X86_REG_EAX, result)
        vm.reg_write(UC_X86_REG_ESP, sp+4)
        vm.reg_write(UC_X86_REG_EIP, self.u32(sp))

    def load(self, name, slot):
        if name not in ASSETS or not 0 <= slot <= 0xffff:
            raise ValueError('Qualified RoleDoll filename and WORD slot required')
        if slot < 512 and self.u32(BANK+STRIDE*slot) != 0xffffffff:
            raise ValueError('Uncached loader requires an empty slot')
        self.active_name = name
        self.vm.mem_write(SCRATCH, (DIRECTORY+name).replace('/', '\\').encode()+b'\0')
        return self.call(0x29820, SCRATCH, slot, this=BANK)
