"""Current +0x214 source proof; no world, renderer, or graphics VM.

Runs original 815C0 -> 54720 and the CSV parser/getter. The CSV open/close
boundary supplies decoded, text-mode bytes after independent original 1EC0
decompression. CRT formatting/allocation/stdio are explicit bounded adapters.
"""
import csv
import hashlib
import io
import json
import re
import struct

from .current_role_doll_resources import ROOT, IMAGE_SHA
from .current_indoor_resources import NativeIndoorResources, BASE, STACK, SP, SCRATCH
from .omega_assets import decode_csvz
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE, UC_HOOK_MEM_WRITE
from unicorn.x86_const import (UC_X86_REG_EAX, UC_X86_REG_ECX, UC_X86_REG_ESP, UC_X86_REG_EIP,
                              UC_X86_REG_EBP, UC_X86_REG_EDI)

SOURCE = 'Data2/Patch/FieldComm3.csvZ'
SOURCE_SHA = '197b0952d33bddb6f3682779208dd396fcecbe451c1b9dc68ec86209ed1a7e05'
SOURCE_PLAIN_SHA = '2c76b311dfcfba4ceb2b23c0faf5011339365673bd01c8a4ed371fb174fd43ac'
LITERAL_PATH = b'\\Data3\\Flow\\DTitleGui.ROM'
ASSET = 'Data3/Flow/DTitleGui.ROMZ'
ASSET_SHA = 'aef52204cba53037a97658de390e916fd1d418040f92a6c95e3bd4e766470b92'
ASSET_PLAIN_SHA = '8920aec8158d2fb82814d2a61e101ec4a35f1adfbdc208d249cb56702c99faf2'
UI = 0x6000000
READER = UI + 0xcff74
RECORD_POINTER = READER + 0x121f0
STRIDE, INDEX, PATH_OFFSET, CAPACITY = 0x108, 2, 0x214, 65
CWD = str(ROOT.parent / 'God2').replace('/', '\\').encode('ascii')


def pinned_sources(client_root=ROOT.parent / 'God2'):
    result = []
    for path, raw_sha, plain_sha in (
            (SOURCE, SOURCE_SHA, SOURCE_PLAIN_SHA),
            (ASSET, ASSET_SHA, ASSET_PLAIN_SHA)):
        source = client_root / path
        if source.stat().st_size > 1024 * 1024:
            raise ValueError('UI source size bound')
        raw = source.read_bytes()
        if hashlib.sha256(raw).hexdigest() != raw_sha:
            raise ValueError('Pinned UI source changed: ' + path)
        plain = decode_csvz(raw, limit=1024 * 1024)
        if hashlib.sha256(plain).hexdigest() != plain_sha:
            raise ValueError('Pinned UI decode changed: ' + path)
        result.append((raw, plain))
    rows = list(csv.reader(io.StringIO(result[0][1].decode('latin1'))))
    if rows[0][:3] != ['FightCommon', '1', '5']:
        raise ValueError('Unexpected UI CSV header')
    records = rows[4:]
    if len(records) != CAPACITY or [int(row[0]) for row in records] != list(range(CAPACITY)):
        raise ValueError('Unexpected UI CSV record boundaries')
    if records[INDEX][1].encode('ascii') != LITERAL_PATH:
        raise ValueError('Unexpected literal UI path')
    if any(len(row[1].encode('latin1')) >= 0x104 for row in records):
        raise ValueError('UI CSV path capacity exceeded')
    return result, records


class NativeWorldUIResource(NativeIndoorResources):
    """Reuse bounded memory/CRT services, without constructing other resources."""

    def __init__(self):
        sources, self.rows = pinned_sources()
        self.raw_csv, self.plain_csv = sources[0]
        self.raw_rom, self.plain_rom = sources[1]
        image = (ROOT / 'artifacts/capture_work/host-20260918-1430/output/'
                 'native-master-01-stable.bin').read_bytes()
        if hashlib.sha256(image).hexdigest() != IMAGE_SHA:
            raise ValueError('Pinned original image changed')
        self.vm = vm = Uc(UC_ARCH_X86, UC_MODE_32)
        vm.mem_map(BASE, (len(image) + 4095) & ~4095)
        vm.mem_write(BASE, image)
        for address, size in ((0, 4096), (UI, 0xe3000),
                              (STACK, 0x80000), (SCRATCH, 0x10000)):
            vm.mem_map(address, size)
        vm.mem_write(0, struct.pack('<I', 0xffffffff))
        self.handles, self.opens, self.files = {}, [], {}
        self.allocations, self.freed = {}, set()
        self.heap, self.heap_limit = 0x9000000, 0xa000000
        self.calls, self.seh_accesses = set(), set()
        self.os_apis, self.find_first = {}, self.u32(BASE + 0x17042c)
        self.exit_callbacks, self.hooks = [], []
        self.visits, self.path_copies, self.callocs, self.path_writes = [], [], [], []
        self.getcwd = self.u32(BASE + 0x170428)
        for page in {self.getcwd & ~4095, self.find_first & ~4095}:
            vm.mem_map(page, 4096)
        services = (0x147973, 0x1479ff, 0x15b406, 0x15b42f, 0x14785c,
                    0x1474ab, 0x1474dc, 0x14741f, 0x147af7, 0x147a95,
                    0x1480b4, 0x147e23, 0x2530, 0x27b0, 0x2c70, 0x2dc0)
        for address in [BASE + rva for rva in services] + [self.getcwd, self.find_first]:
            self.hooks.append(vm.hook_add(UC_HOOK_CODE, self._service,
                                         begin=address, end=address))
        for rva in (0x815c0, 0x54720, 0x54776, 0x54800, 0x51ae0, 0x12f550):
            self.hooks.append(vm.hook_add(UC_HOOK_CODE, self._observe,
                                         begin=BASE+rva, end=BASE+rva))
        # Explicit fresh CWD cache and zero-filled reader input, not a live ctor.
        vm.mem_write(BASE + 0x19ddf0, struct.pack('<I', 1))
        self.call(0x2030)
        self.native_decoded = []
        for raw, plain in sources:
            self._check_decompression(raw, plain)
        self.reader_result = self.call(0x815c0, this=UI)
        self.records = self.u32(RECORD_POINTER)
        self.path = self.string(self.records + PATH_OFFSET)
        if self.path != LITERAL_PATH:
            raise AssertionError('Original reader +0x214 differs from source')

    def _check_decompression(self, raw, plain):
        context, output, handle = self.allocate(0xd440), self.allocate(len(plain)+3), 0x81000000
        self.handles[handle] = [raw, 0]
        self.call(0x1760, this=context)
        self.call(0x1ec0, handle, output, this=context)
        decoded = bytes(self.vm.mem_read(output, len(plain)))
        if decoded != plain:
            raise AssertionError('Original UI source decompression mismatch')
        self.call(0x17b0, this=context)
        self.handles.pop(handle)
        self.native_decoded.append(hashlib.sha256(decoded).hexdigest())

    def _observe(self, vm, address, size, context):
        rva = address - BASE
        self.visits.append(rva)
        if rva == 0x51ae0:
            sp = vm.reg_read(UC_X86_REG_ESP)
            if self.u32(sp) == BASE + 0x54805:
                self.path_copies.append((self.u32(sp+4), self.u32(sp+8)))

    def _path_write(self, vm, access, address, size, value, start):
        self.path_writes.append((vm.reg_read(UC_X86_REG_EIP)-BASE,
                                 address-start, size))

    def _service(self, vm, address, size, context):
        rva = address - BASE
        sp = vm.reg_read(UC_X86_REG_ESP)
        arg = lambda index: self.u32(sp+4+index*4)
        result, cleanup = 0, 0
        if address == self.getcwd:
            if arg(0) != 260 or len(CWD) >= arg(0):
                raise AssertionError('CWD buffer bound')
            vm.mem_write(arg(1), CWD+b'\0')
            result, cleanup = len(CWD), 8
        elif rva == 0x2530:
            expected = CWD + b'\\Data2\\Patch\\\\FieldComm3.csv'
            if self.string(arg(0)) != expected:
                raise AssertionError('Unexpected native CSV open: '+repr(self.string(arg(0))))
            self.opens.append(self.string(arg(0)))
            result, cleanup = 0x82000000, 4
            self.handles[result] = [self.plain_csv.replace(b'\r\n', b'\n'), 0]
        elif rva == 0x27b0:
            data, position = self.handles.pop(arg(0))
            if position != len(data):
                raise AssertionError('Native UI reader did not consume entire CSV')
            cleanup = 4
        elif rva == 0x147e23:
            if (arg(0), arg(1)) != (STRIDE, CAPACITY):
                raise AssertionError('Unqualified UI calloc')
            self.callocs.append((arg(0), arg(1)))
            result = self.allocate(arg(0)*arg(1))
            start = result + PATH_OFFSET
            self.hooks.append(vm.hook_add(UC_HOOK_MEM_WRITE, self._path_write,
                                         user_data=start, begin=start,
                                         end=start+0x103))
        elif rva == 0x147a95:
            data, position = self.handles[arg(2)]
            if not 1 < arg(1) <= 4096:
                raise AssertionError('fgets capacity bound')
            if position < len(data):
                end = min(data.find(b'\n', position)+1 or len(data), position+arg(1)-1)
                vm.mem_write(arg(0), data[position:end]+b'\0')
                self.handles[arg(2)][1] = end
                result = arg(0)
        elif rva == 0x1480b4:
            if self.string(arg(1)) != b'%d':
                raise AssertionError('Unqualified UI sscanf')
            match = re.match(rb'\s*([+-]?[0-9]+)', self.string(arg(0)))
            if match:
                vm.mem_write(arg(2), struct.pack('<i', int(match[1])))
                result = 1
        elif rva == 0x147af7:
            fmt = self.string(arg(1))
            if fmt == b'%s\\tmp.%d' and self.u32(sp) == BASE+0x296d:
                values = (self.string(arg(2)), arg(3))
            elif fmt in (b'%s', b'%s%s', b'%s\\%s'):
                values = tuple(self.string(arg(i+2)) for i in range(fmt.count(b'%s')))
            else:
                raise AssertionError('Unqualified UI sprintf '+repr(fmt)+
                                     f' caller {self.u32(sp)-BASE:x}')
            rendered = fmt % values
            if len(rendered) >= 260:
                raise AssertionError('UI path formatting bound')
            vm.mem_write(arg(0), rendered+b'\0')
            result = len(rendered)
        else:
            return super()._service(vm, address, size, context)
        vm.reg_write(UC_X86_REG_EAX, result)
        vm.reg_write(UC_X86_REG_ESP, sp+4+cleanup)
        vm.reg_write(UC_X86_REG_EIP, self.u32(sp))

    def resolve(self):
        """Original path resolver is cdecl, so do not use thiscall call()."""
        self.vm.reg_write(UC_X86_REG_ESP, SP)
        self.vm.mem_write(SP, struct.pack('<II', BASE+0x1000, self.records+PATH_OFFSET))
        self.run(0x12f550)
        if self.vm.reg_read(UC_X86_REG_ESP) != SP+4:
            raise AssertionError('Unexpected resolver cleanup')
        return self.string(self.vm.reg_read(UC_X86_REG_EAX))

    def consumer_path(self):
        """Execute 64CB6..64CE1, stopping before the resource loader call.

        The EBP alias makes the existing reader pointer visible at the exact
        original world displacement, without constructing/mapping a world.
        """
        context = self.vm.context_save()
        stack = bytes(self.vm.mem_read(STACK, 0x80000))
        try:
            self.vm.reg_write(UC_X86_REG_ESP, SP)
            self.vm.reg_write(UC_X86_REG_EBP, (UI-0xa7f2f6c) & 0xffffffff)
            self.vm.reg_write(UC_X86_REG_EDI, 0)
            self.run(0x64cb6, 0x64ce1)
            if self.vm.reg_read(UC_X86_REG_ESP) != SP-4:
                raise AssertionError('Unexpected consumer argument stack')
            return self.string(self.u32(SP-4))
        finally:
            self.vm.mem_write(STACK, stack)
            self.vm.context_restore(context)

    def rom_open_path(self):
        """Original 29820 prefix through its first fopen argument preparation."""
        path = self.consumer_path()
        context = self.vm.context_save()
        stack = bytes(self.vm.mem_read(STACK, 0x80000))
        seh = bytes(self.vm.mem_read(0, 4))
        try:
            self.vm.mem_write(SCRATCH, path+b'\0')
            self.vm.mem_write(SP, struct.pack('<III', BASE+0x1000, SCRATCH, 0))
            self.vm.reg_write(UC_X86_REG_ESP, SP)
            self.vm.reg_write(UC_X86_REG_ECX, 0)
            self.run(0x29820, 0x298ed)
            sp = self.vm.reg_read(UC_X86_REG_ESP)
            if self.string(self.u32(sp+4)) != b'rb':
                raise AssertionError('Unexpected native ROM fopen mode')
            return self.string(self.u32(sp))
        finally:
            self.vm.mem_write(0, seh)
            self.vm.mem_write(STACK, stack)
            self.vm.context_restore(context)


def main():
    native = NativeWorldUIResource()
    print(json.dumps({'source': SOURCE, 'section': 'FightCommon', 'RomIdx': INDEX,
                      'source_line': 7, 'field_offset': hex(PATH_OFFSET),
                      'literal_path': native.path.decode('ascii'),
                      'resolved_path': native.resolve().decode('ascii'),
                      'native_60a90_argument': native.consumer_path().decode('ascii'),
                      'native_29820_first_open': native.rom_open_path().decode('ascii'),
                      'asset': ASSET, 'asset_sha256': ASSET_SHA,
                      'native_decoded_sha256': native.native_decoded,
                      'csv_open_boundary': '2530/27B0 decoded text stream',
                      'renderer_executed': False}, indent=2))


if __name__ == '__main__':
    main()
