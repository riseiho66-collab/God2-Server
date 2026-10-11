"""Execute the unclassified 119E30 arithmetic island, not a damage formula.

Synthetic live-ins explicitly bypass the unqualified function prefix. No calls
are stubbed, no image bytes are patched, and no authoritative actor is written.
"""
import hashlib
import json

from .current_battle_entry import (
    BASE, BATTLE, SP, NativeRun, pinned_image, IMAGE_SHA256,
    UC_HOOK_MEM_READ, UC_PROT_READ, UC_X86_REG_EIP, UC_X86_REG_EBX,
)

START, END, ALTERNATE = 0x11a08f, 0x11a10e, 0x11a281
SLICE_SHA256 = 'eab22c1e2a8535a23911dfbdc51d8e86a59b2c0d0692790721ba47e496cbdd77'
MASK = 0xffffffff


def signed(value):
    return value - 0x100000000 if value & 0x80000000 else value


class ProjectionProof:
    def __init__(self):
        self.image = pinned_image()
        if hashlib.sha256(self.image[START:END]).hexdigest() != SLICE_SHA256:
            raise ValueError('Arithmetic slice hash mismatch')

    def run(self, current, supplied, descriptor, mode, *, row=0, column=0, slot=0):
        limits = ((current, MASK), (supplied, MASK), (descriptor, 255),
                  (mode, MASK), (row, 3), (column, 1), (slot, 13))
        if any(type(v) is not int or not 0 <= v <= limit for v, limit in limits):
            raise ValueError('Outside explicit synthetic live-in bounds')
        n = NativeRun(self.image)
        address = BATTLE + 0xa9ea505 + row * 32 + column * 8
        value_address = address + 3
        n.put(address, bytes([descriptor]))
        n.put32(value_address, supplied)
        for page in {address & ~4095, value_address & ~4095}:
            n.vm.mem_protect(page, 4096, UC_PROT_READ)
        n.put32(SP + 0x20, address)
        n.put32(SP + 0x2c, 0x153d4a1 + row * 4)
        n.put32(SP + 0x1c, BATTLE)
        n.put32(SP + 0x2d8, mode)
        n.put32(SP + 0x18, slot)
        n.put32(SP + 0x9c + slot * 4, current)
        n.registers(ebp=column, eax=0xa5a5a5a5, ebx=0xa5a5a5a5)
        reads = []

        def read(vm, access, addr, size, value, data):
            if address <= addr < value_address + 4:
                reads.append((vm.reg_read(UC_X86_REG_EIP) - BASE, addr, size))

        hook = n.vm.hook_add(UC_HOOK_MEM_READ, read)
        try:
            n.run(START, ((START, END),), {END, ALTERNATE}, budget=100)
        finally:
            n.vm.hook_del(hook)
        return {
            'inputs': dict(current=current, supplied=supplied, descriptor=descriptor,
                           mode=mode, row=row, column=column, slot=slot),
            'projected': n.get32(SP + 0x9c + slot * 4),
            'zero_branch': n.vm.reg_read(UC_X86_REG_EBX),
            'stop_rva': n.stop, 'instructions': len(n.visits),
            'reads': reads, 'writes': n.writes,
            'source_unchanged': (n.vm.mem_read(address, 1) == bytes([descriptor]) and
                                 n.get32(value_address) == supplied),
        }


def evidence():
    proof = ProjectionProof()
    cases = [(100, 20, 0x31, 1), (100, 20, 0x31, 0),
             (50, 20, 0x31, 1), (100, 0x40000000, 0x21, 1),
             (100, MASK, 0x11, 1), (100, 20, 0x33, 1)]
    return {'authority': 'NATIVE_ISOLATED_ARITHMETIC_NOT_DAMAGE_FORMULA',
            'image_sha256': IMAGE_SHA256, 'slice_sha256': SLICE_SHA256,
            'missing': ['populated input producer', 'live entry reachability',
                        'attack/defense binding', 'authoritative writeback'],
            'cases': [proof.run(*args) for args in cases]}


if __name__ == '__main__':
    print(json.dumps(evidence(), sort_keys=True))
