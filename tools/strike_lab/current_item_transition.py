"""Original S2C41 state -> AE520/96390/963C0 slot resolution -> C2S25.

Offline synthetic inventory, inactive UI and an explicitly empty definition
lookup table. No game code/callee stubs, sockets, client process or grants.
The demonstrated request branch is limited to IDs 5300..5399 and 5500..5599.
"""
import hashlib
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'artifacts/tooling/crypto-oracle-python'))
from unicorn import (Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE,
                     UC_HOOK_MEM_WRITE, UC_PROT_READ, UC_PROT_WRITE, UC_PROT_EXEC)
from unicorn.x86_const import (UC_X86_REG_EAX, UC_X86_REG_EBP, UC_X86_REG_EBX,
                              UC_X86_REG_ECX, UC_X86_REG_EDX, UC_X86_REG_EIP,
                              UC_X86_REG_ESP)

BASE, STACK, NET, WORLD = 0x400000, 0x3000000, 0x3200000, 0x4000000
SP, RETURN = STACK + 0x2000, BASE + 0x1000
UI = WORLD + 0xa7f2f6c
SLOTS = UI + 0x8560c
COMPANION, MANAGER, PACKET, DEFINITIONS = 0x3700000, 0x3730000, 0x3740000, 0x3800000
QUEUE, LENGTH = NET + 0x36c8, NET + 0x36c4
IMAGE_SHA = '149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
REGIONS = ((UI & ~4095, 0x234000), (NET, 0x5000),
           (COMPANION, 0x22000), (MANAGER, 4096), (DEFINITIONS, 0xe0000))


class NativeItemTransition:
    def __init__(self):
        self.image = (ROOT / 'artifacts/capture_work/host-20260918-1430/output/'
                      'native-master-01-stable.bin').read_bytes()
        if hashlib.sha256(self.image).hexdigest() != IMAGE_SHA:
            raise ValueError('Pinned current image changed')
        self.vm = vm = Uc(UC_ARCH_X86, UC_MODE_32)
        vm.mem_map(BASE, (len(self.image) + 4095) & ~4095, UC_PROT_READ | UC_PROT_EXEC)
        vm.mem_write(BASE, self.image)
        for address, size in (*REGIONS, (STACK, 0x4000), (PACKET, 4096)):
            vm.mem_map(address, size, UC_PROT_READ | UC_PROT_WRITE)
        vm.mem_write(STACK, b'\xa5' * 0x4000)
        # Stop the suffix canary before the optional lock pointer at NET+40D4.
        vm.mem_write(QUEUE, b'\x69' * (0xa00 + 8))
        vm.mem_write(LENGTH, struct.pack('<I', 3))
        vm.mem_write(SLOTS - 16, b'\xa5' * (50 * 24 + 32))
        for slot in range(50):
            self.seed_slot(slot, 0, 0)
        vm.mem_write(UI + 0x232dc8, b'\xff\xff')
        vm.mem_write(UI + 0x232dd6, b'\xff\xff')
        vm.mem_write(UI + 0x232ebc, struct.pack('<I', COMPANION))
        vm.mem_write(COMPANION + 0x21236, b'\xff')
        vm.mem_write(UI + 0x574c0, struct.pack('<I', MANAGER))
        vm.mem_write(UI + 0x71, b'\x01')
        vm.mem_write(UI + 0xcff70, struct.pack('<I', DEFINITIONS))
        vm.mem_write(UI + 0x86874, struct.pack('<I', NET))
        vm.mem_protect(DEFINITIONS, 0xe0000, UC_PROT_READ)
        self.writes, self.visits, self.arguments = [], [], []
        vm.hook_add(UC_HOOK_MEM_WRITE, self._write)
        vm.hook_add(UC_HOOK_CODE, self._visit)

    def seed_slot(self, slot, item_id, raw_count):
        """Explicit fixture input, never an inferred inventory grant."""
        if not 0 <= slot < 50:
            raise ValueError('Fixture slot out of range')
        self.vm.mem_write(SLOTS + 24 * slot, bytes((raw_count,)))
        self.vm.mem_write(SLOTS + 24 * slot + 4, struct.pack('<H', item_id))

    def _write(self, vm, access, address, size, value, context):
        self.writes.append((address, size))

    def _visit(self, vm, address, size, context):
        rva = address - BASE
        if rva in (0x68b61, 0x6a04d, 0x991e0, 0x9b850, 0x9b720, 0x9b770,
                   0xae520, 0xae5cd, 0x59a60, 0x96390, 0x963c0, 0x96350, 0x132e0):
            self.visits.append(rva)
        if rva in (0x963c0, 0x96350):
            sp = vm.reg_read(UC_X86_REG_ESP)
            words = 3 if rva == 0x96350 else 1
            self.arguments.append((rva, struct.unpack('<' + 'I' * words,
                                                       vm.mem_read(sp + 4, words * 4))))

    def _run(self, start, stop):
        self.writes.clear()
        self.visits.clear()
        self.arguments.clear()
        hook = self.vm.hook_add(UC_HOOK_CODE, lambda vm, a, s, c: vm.emu_stop(),
                                begin=BASE + stop, end=BASE + stop)
        try:
            self.vm.emu_start(BASE + start, BASE + stop, count=100000)
        finally:
            self.vm.hook_del(hook)
        if self.vm.reg_read(UC_X86_REG_EIP) != BASE + stop:
            raise AssertionError('Original execution did not reach its exact stop')

    def _snapshot(self):
        return {address: bytes(self.vm.mem_read(address, size)) for address, size in REGIONS}

    def _verify(self, before, changes, allowed):
        for address, size in self.writes:
            if not any(low <= address and address + size <= high
                       for low, high in [(STACK, STACK + 0x4000), *allowed]):
                raise AssertionError(f'Unexpected original write {address:X}+{size}')
        for base, old in before.items():
            expected = bytearray(old)
            for address, value in changes:
                if base <= address < base + len(old):
                    expected[address - base:address - base + len(value)] = value
            if bytes(self.vm.mem_read(base, len(old))) != expected:
                raise AssertionError(f'Unexpected state change in region {base:X}')

    def consume(self, logical):
        """Full original dispatch/consumer, not just the scalar prefix."""
        if len(logical) != 5 or logical[0] != 0x41 or logical[3] >= 50:
            raise ValueError('This fixture accepts one valid S2C41 record')
        vm = self.vm
        packet = PACKET + 4096 - 5
        vm.mem_protect(PACKET, 4096, UC_PROT_READ | UC_PROT_WRITE)
        vm.mem_write(packet, logical)
        vm.mem_protect(PACKET, 4096, UC_PROT_READ)
        vm.reg_write(UC_X86_REG_ESP, SP)
        vm.reg_write(UC_X86_REG_EBP, WORLD)
        vm.reg_write(UC_X86_REG_EBX, packet)
        vm.reg_write(UC_X86_REG_EAX, 0x41)
        before = self._snapshot()
        slot = SLOTS + logical[3] * 24
        positive = 0 < logical[4] < 128
        count = logical[4:5] if positive else b'\0'
        item = logical[1:3] if positive else b'\0\0'
        self._run(0x68b61, 0x6b517)
        self._verify(before, [(slot, count), (slot + 4, item)],
                     [(slot, slot + 1), (slot + 4, slot + 8)])
        if vm.reg_read(UC_X86_REG_ESP) != SP:
            raise AssertionError('Original consumer stack imbalance')

    def request(self, argument, *, by_slot=True, via_action=False, incoming_edx=0, gate=0):
        """Run the complete original caller, lookup and append when reached.

        Other ID categories can enter different original paths; this oracle
        deliberately leaves those unmodeled and will fail on unexpected writes.
        """
        vm = self.vm
        vm.mem_write(UI + 0x866e4, struct.pack('<I', gate))
        vm.mem_write(SP, struct.pack('<II', RETURN, argument))
        vm.reg_write(UC_X86_REG_ESP, SP)
        vm.reg_write(UC_X86_REG_ECX, UI)
        vm.reg_write(UC_X86_REG_EDX, incoming_edx)
        size = struct.unpack('<I', vm.mem_read(LENGTH, 4))[0]
        if size + 5 > 0xa00:
            raise ValueError('Offline queue fixture does not execute flushing')
        before = self._snapshot()
        entry = 0xae520 if via_action else (0x96390 if by_slot else 0x963c0)
        self._run(entry, RETURN - BASE)
        final_size = struct.unpack('<I', vm.mem_read(LENGTH, 4))[0]
        if final_size not in (size, size + 5):
            raise AssertionError('Unexpected request branch/record size')
        record = bytes(vm.mem_read(QUEUE + size, final_size - size))
        if record and record[0] != 0x25:
            raise AssertionError('Request is outside the demonstrated C2S25 branch')
        self._verify(before, [(LENGTH, struct.pack('<I', final_size)),
                              (QUEUE + size, record)],
                     [(LENGTH, LENGTH + 4), (QUEUE + size, QUEUE + final_size)])
        if vm.reg_read(UC_X86_REG_ESP) != SP + 8:
            raise AssertionError('Original caller stack imbalance')
        return record


def main():
    native = NativeItemTransition()
    for slot in (3, 29, 49):
        native.consume(struct.pack('<BHBB', 0x41, 5301, slot, 7))
    first = native.request(3, incoming_edx=0xa5ee0000)
    native.consume(struct.pack('<BHBB', 0x41, 5301, 29, 0))
    second = native.request(3, incoming_edx=0xa5ee0000)
    native.consume(struct.pack('<BHBB', 0x41, 5301, 3, 0))
    third = native.request(5301, by_slot=False)
    print(json.dumps({'image_sha256': IMAGE_SHA,
                      'request_before_clear': first.hex(),
                      'request_after_slot29_clear': second.hex(),
                      'request_with_only_slot49_remaining': third.hex(),
                      'server_use_result': None}, indent=2))


if __name__ == '__main__':
    main()
