"""Bounded native beta MP writers, distinguishing synchronization from debit."""
import hashlib
import json
import struct

from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn import x86_const as reg
from .beta_packet_probe import ROOT, IMAGE, SHA


def run():
    image = IMAGE.read_bytes()
    if hashlib.sha256(image).hexdigest() != SHA:
        raise ValueError('Beta image identity mismatch')
    base, owner, role, packet, stack = 0x400000, 0x3000000, 0x3200000, 0x3300000, 0x3400000
    vm = Uc(UC_ARCH_X86, UC_MODE_32)
    vm.mem_map(base, (len(image) + 4095) & ~4095)
    vm.mem_write(base, image)
    for address, size in ((owner, 0x200000), (role, 4096), (packet, 4096), (stack, 65536)):
        vm.mem_map(address, size)
    vm.mem_write(owner + 0x76bd0, struct.pack('<I', role))
    stops = {0xa78bc, 0xa86e6, 0x87381, 0x87479, 0xa7c08}
    bounds = ((0xa7890, 0xa78bc), (0xa86b0, 0xa86e6), (0x87340, 0x87381), (0xa7b00, 0xa7c08))

    def hook(uc, address, size, unused):
        rva = address - base
        if rva in stops:
            uc.emu_stop()
        elif not any(lo <= rva and rva + size <= hi for lo, hi in bounds):
            raise AssertionError(f'Unexpected native path {rva:x}')

    vm.hook_add(UC_HOOK_CODE, hook)

    def execute(entry, arg):
        vm.mem_write(stack + 0x8000, struct.pack('<II', stack + 0xff00, arg))
        vm.reg_write(reg.UC_X86_REG_ESP, stack + 0x8000)
        vm.reg_write(reg.UC_X86_REG_ECX, owner)
        vm.emu_start(base + entry, stack + 0xff00, count=1000)
        if vm.reg_read(reg.UC_X86_REG_EIP) - base not in stops:
            raise AssertionError('Native prefix did not reach boundary')

    copies = []
    for value in (0, 1, 32768, 0x7fffffff, 0x80000000, 0xffffffff):
        for entry in (0xa7890, 0xa86b0):
            vm.mem_write(role, b'\xa5' * 4096)
            words = (value ^ 7, value, value ^ 17, value ^ 31)
            vm.mem_write(packet, struct.pack('<4IH', *words, 123))
            execute(entry, packet)
            actual = struct.unpack('<I', vm.mem_read(role + 0x64, 4))[0]
            expected = words[2 if entry == 0xa7890 else 1]
            if actual != expected:
                raise AssertionError('Sync performed unexpected arithmetic')
            copies.append({'entry': hex(entry), 'input': list(words), 'mp': actual})
    clamps = []
    for hp, mp in ((0, 0), (50, 60), (100, 100), (101, 102), (0xffffffff, 0x80000000)):
        for maxhp, maxmp in ((100, 100), (0, 100), (100, 0), (0xffffffff, 0xffffffff)):
            for handle in (-1, 0):
                vm.mem_write(role + 0x5c, struct.pack('<4I', hp, maxhp, mp, maxmp))
                vm.mem_write(owner + 0x12068e, struct.pack('<h', handle))
                execute(0x87340, role)
                actual = list(struct.unpack('<4I', vm.mem_read(role + 0x5c, 16)))
                enabled = maxhp != 0 and maxmp != 0 and handle >= 0
                expected = [min(hp, maxhp) if enabled else hp, maxhp,
                            min(mp, maxmp) if enabled else mp, maxmp]
                if actual != expected:
                    raise AssertionError('Native clamp differed')
                clamps.append({'before': [hp, maxhp, mp, maxmp], 'handle': handle, 'after': actual})
    if struct.unpack_from('<I', image, 0x65da4 + 0x29 * 4)[0] != base + 0x64bea:
        raise AssertionError('Stat packet dispatch changed')
    lp = struct.unpack_from('<I', image, 0x12f4 + 0x29 * 4)[0] - base
    if image[lp:lp + 6] != b'\xb8\x1f\x00\x00\x00\xc3':
        raise AssertionError('Stat packet length changed')
    fields = [(0x88, 2), (0x8a, 2), (0x8c, 2), (0x8e, 2),
              (0x9c, 4), (0xa0, 4), (0xa4, 4), (0xa8, 4), (0xac, 4),
              (0xb0, 2), (0xb2, 2), (0x94, 2), (0x92, 2), (0x98, 2), (0x96, 2)]
    stat_cases = []
    for values in (list(range(1001, 1016)), [0] * 15, [65535] * 15):
        vm.mem_write(role, b'\xa5' * 4096)
        vm.mem_write(packet, b'\x29' + struct.pack('<15H', *values))
        execute(0xa7b00, packet + 1)
        observed = [int.from_bytes(vm.mem_read(role + off, size), 'little') for off, size in fields]
        if observed != values:
            raise AssertionError('Stat input was not copied exactly')
        stat_cases.append({'input': values, 'observed': observed})
    return {'image_sha256': SHA, 'sync_cases': copies, 'clamp_cases': clamps,
            'stat_packet': {'opcode': '29', 'logical_length': 31, 'cases': stat_cases,
                            'fields': [{'input_word_index': index, 'role_offset': hex(off), 'width': size}
                                       for index, (off, size) in enumerate(fields)],
                            'semantics': 'Unlabeled numeric fields; not identified monster stats'},
            'scope': 'Executed original writer prefixes; stopped before UI calls/ratio computation. '
                     'Input amounts synthetic. Not authoritative combat, debit timing or complete writer coverage.'}


if __name__ == '__main__':
    report = run()
    output = ROOT / 'artifacts/research/beta-unpack-20260920/resource-writers.json'
    output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'sync_cases': len(report['sync_cases']), 'clamp_cases': len(report['clamp_cases']),
                      'stat_packet_cases': len(report['stat_packet']['cases'])}))
