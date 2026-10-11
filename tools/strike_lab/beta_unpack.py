"""Offline beta ASPack execution. Synthetic APIs, no host code execution."""
import argparse
import hashlib
import json
from pathlib import Path
import struct

import pefile
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_BLOCK, UcError
from unicorn.x86_const import UC_X86_REG_ESP, UC_X86_REG_EAX, UC_X86_REG_EIP, UC_X86_REG_ECX


def unpack(source, output):
    raw = source.read_bytes()
    if hashlib.sha256(raw).hexdigest() != '1326af232a5280a5bf19cfadb434ba66b8b2b2753bd36097ada3ef66474c5cac':
        raise ValueError('Beta executable hash mismatch')
    pe = pefile.PE(data=raw)
    base = pe.OPTIONAL_HEADER.ImageBase
    size = (pe.OPTIONAL_HEADER.SizeOfImage + 4095) & ~4095
    vm = Uc(UC_ARCH_X86, UC_MODE_32)
    vm.mem_map(base, size)
    vm.mem_write(base, pe.get_memory_mapped_image())
    vm.mem_map(0x10000000, 0x200000)
    vm.reg_write(UC_X86_REG_ESP, 0x10100000)
    vm.mem_map(0x20000000, 0x10000)
    vm.mem_map(0x30000000, 0x2000000)
    vm.mem_map(0, 0x10000)
    api = {}
    events = []
    allocation = 0x30000000
    reached = []
    last_block = [None]
    transfer = []
    u32 = lambda a: struct.unpack('<I', vm.mem_read(a, 4))[0]

    def string(a):
        if a < 65536:
            return '#' + str(a)
        out = bytearray()
        for i in range(512):
            b = vm.mem_read(a + i, 1)
            if b == b'\0':
                return out.decode('ascii', errors='backslashreplace')
            out.extend(b)
        raise ValueError('API string bound')

    def stub(name):
        for address, existing in api.items():
            if existing == name:
                return address
        address = 0x20000000 + len(api) * 16
        api[address] = name
        vm.mem_write(address, b'\xc3')
        return address

    for library in pe.DIRECTORY_ENTRY_IMPORT:
        for imp in library.imports:
            name = imp.name.decode() if imp.name else '#' + str(imp.ordinal)
            vm.mem_write(imp.address, struct.pack('<I', stub(name)))

    def hook(uc, address, length, unused):
        nonlocal allocation
        if address == base + 0x1c50fe:
            events.append({'decompressed_bytes': uc.reg_read(UC_X86_REG_EAX)})
        # The stub temporarily installs RET at a section start to flush/probe it.
        if base + 0x1000 <= address < base + 0x12c000:
            probe = (u32(uc.reg_read(UC_X86_REG_ESP)) == base + 0x1c511a
                     and bytes(uc.mem_read(address, 1)) == b'\xc3')
            if not probe:
                reached.append(address)
                transfer.append(last_block[0])
                uc.emu_stop()
                return
        last_block[0] = hex(address)
        if address not in api:
            return
        name = api[address]
        sp = uc.reg_read(UC_X86_REG_ESP)
        arg = lambda i: u32(sp + 4 + 4 * i)
        event = {'api': name, 'return': hex(u32(sp))}
        if name in ('GetModuleHandleA', 'LoadLibraryA'):
            event['module'] = string(arg(0))
            result, argc = 0x70000000, 1
        elif name == 'GetProcAddress':
            event['symbol'] = string(arg(1))
            result, argc = stub(event['symbol']), 2
        elif name == 'VirtualAlloc':
            length = (arg(1) + 4095) & ~4095
            if not length or allocation + length > 0x32000000:
                raise ValueError('Allocation bound')
            result, argc = allocation, 4
            allocation += length
        elif name == 'VirtualFree':
            result, argc = 1, 3
        elif name == 'VirtualProtect':
            uc.mem_write(arg(3), struct.pack('<I', 0x40))
            result, argc = 1, 4
        else:
            raise ValueError('Unsupported API execution: ' + name)
        events.append(event)
        uc.reg_write(UC_X86_REG_EAX, result)
        uc.reg_write(UC_X86_REG_ESP, sp + 4 + 4 * argc)
        uc.reg_write(UC_X86_REG_EIP, u32(sp))

    vm.hook_add(UC_HOOK_BLOCK, hook)
    error = None
    try:
        vm.emu_start(base + pe.OPTIONAL_HEADER.AddressOfEntryPoint, 0, timeout=120000000, count=200000000)
    except (UcError, ValueError) as exc:
        error = str(exc)
    image = bytes(vm.mem_read(base, size))
    output.mkdir(parents=True, exist_ok=True)
    report = {'input_sha256': hashlib.sha256(raw).hexdigest(),
              'image_sha256': hashlib.sha256(image).hexdigest(),
              'stop_eip': hex(vm.reg_read(UC_X86_REG_EIP)),
              'eax': hex(vm.reg_read(UC_X86_REG_EAX)), 'ecx': hex(vm.reg_read(UC_X86_REG_ECX)),
              'reached_original_text': [hex(x) for x in reached], 'error': error,
              'transfer_from_block': transfer,
              'status': 'ANALYSIS_IMAGE_READY' if reached and error is None else 'INCOMPLETE',
              'apis': events, 'synthetic_imports': {hex(k): v for k, v in api.items()},
              'scope': 'Analysis image with synthetic imports; not runnable restored PE'}
    (output / 'unpack.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    (output / 'beta-mapped.bin').write_bytes(image)
    print(json.dumps({k: v for k, v in report.items() if k not in ('apis', 'synthetic_imports')}))
    print(json.dumps(events[-8:]))
    if report['status'] != 'ANALYSIS_IMAGE_READY':
        raise RuntimeError('Unpack did not reach original startup within bounds')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.resolve().is_relative_to(args.source.resolve().parent):
        raise ValueError('Cannot write into original client')
    unpack(args.source, args.output)
