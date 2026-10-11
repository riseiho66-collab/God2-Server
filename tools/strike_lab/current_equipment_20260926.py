"""Bounded current-EXE equipment producer/guard oracle; no game or DB writes.

The producer and queue run to their real return. Rejection tests stop before
the message renderer. This does not claim complete inventory UI/effect proof.
"""
from pathlib import Path
import hashlib
import json
import struct
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'artifacts/tooling/crypto-oracle-python'))
import pefile
import unicorn as uc
from unicorn import x86_const as x

PIN = '6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98'
BASE, UI, NET, STACK = 0x400000, 0x10000000, 0x20000000, 0x30000000
SP, STOP = STACK + 0x8000, STACK + 0xf000


def require(value, message):
    if not value:
        raise RuntimeError(message)


class EquipmentOracle:
    def __init__(self):
        raw = (ROOT.parent / 'God2/God2.exe').read_bytes()
        require(hashlib.sha256(raw).hexdigest() == PIN, 'Wrong current client')
        pe = pefile.PE(data=raw)
        require(pe.OPTIONAL_HEADER.ImageBase == BASE, 'Wrong image base')
        self.image = pe.get_memory_mapped_image()
        self.vm = v = uc.Uc(uc.UC_ARCH_X86, uc.UC_MODE_32)
        v.mem_map(BASE, (len(self.image)+4095)&~4095, uc.UC_PROT_READ|uc.UC_PROT_EXEC)
        v.mem_write(BASE, self.image)
        for a, n in ((UI, 0x240000), (NET, 0x5000), (STACK, 0x10000)):
            v.mem_map(a, n)
        v.mem_write(UI+0x86874, struct.pack('<I', NET))
        self.allowed = ()
        v.hook_add(uc.UC_HOOK_CODE, self.code)
        v.hook_add(uc.UC_HOOK_MEM_WRITE, self.write)

    def code(self, v, a, size, _):
        if a in (STOP, 0x475d60):
            v.emu_stop()
            return
        require(any(lo <= a and a+size <= hi for lo, hi in self.allowed),
                f'Unqualified instruction {a:x}')

    def write(self, v, access, a, size, value, _):
        require(any(lo <= a and a+size <= hi for lo, hi in
                    ((STACK, STACK+0x10000), (NET+0x36c4, NET+0x40c8),
                     (UI+0x85608, UI+0x8560c))), f'Unexpected write {a:x}')

    def run(self, entry, args):
        v = self.vm
        v.mem_write(SP, struct.pack('<'+'I'*(len(args)+1), STOP, *args))
        for reg, value in ((x.UC_X86_REG_ESP, SP), (x.UC_X86_REG_ECX, UI),
                           (x.UC_X86_REG_EFLAGS, 2)):
            v.reg_write(reg, value)
        v.emu_start(entry, 0, count=5000)
        pc = v.reg_read(x.UC_X86_REG_EIP)
        require(pc in (STOP, 0x475d60), 'Instruction budget exhausted')
        if pc == STOP:
            require(v.reg_read(x.UC_X86_REG_ESP) == SP+4*(len(args)+1), 'Stack imbalance')
        return pc

    def producer(self, key, slot, flag, gate=0, modal=None, modal_flags=0):
        v = self.vm
        self.allowed = ((0x496550, 0x496610), (0x4132e0, 0x413368))
        for off in (0x232dea, 0x232e20):
            v.mem_write(UI+off, b'\xff\xff')
        if modal is not None:
            v.mem_write(UI+modal, b'\0\0')
            v.mem_write(UI+0xe2988, bytes([modal_flags]))
        v.mem_write(UI+0x866e4, struct.pack('<I', gate))
        v.mem_write(UI+0x85608, struct.pack('<I', 0xabcdef01))
        v.mem_write(NET+0x36c4, struct.pack('<I', 3))
        v.mem_write(NET+0x36c8, b'\x11\x22\x33'+b'\xcc'*16)
        stop = self.run(0x496550, (key, slot, flag))
        blocked = gate != 0 or modal is not None and modal_flags & 0x20
        expected = b'' if blocked else bytes([0x28,key&255,key>>8&255,slot&255,flag&255])
        require(stop == (0x475d60 if not gate and blocked else STOP), 'Wrong producer branch')
        require(struct.unpack('<I',v.mem_read(NET+0x36c4,4))[0] == 3+len(expected), 'Queue length')
        require(bytes(v.mem_read(NET+0x36c8,19)) == b'\x11\x22\x33'+expected+b'\xcc'*(16-len(expected)), 'Queue/canary mismatch')
        require(struct.unpack('<I',v.mem_read(UI+0x85608,4))[0] == (0xabcdef01 if blocked else 1), 'Pending state mismatch')
        return expected.hex()

    def deity_guard(self, key, bits):
        self.allowed = ((0x49b5e0, 0x49b670),)
        self.vm.mem_write(UI+0x866ba, bytes([bits]))
        stop = self.run(0x49b5e0, (key,))
        rejected = 7000 < key < 8000 and (
            bits & 3 == 2 and (7100 < key < 7201 or 7400 < key < 7501) or
            bits & 3 == 1 and (7200 < key < 7301 or 7500 < key < 7601))
        require((stop == 0x475d60) == rejected, 'Guard differs from exact ranges')
        if not rejected:
            require(self.vm.reg_read(x.UC_X86_REG_EAX)&255 == 1, 'Guard success byte')
        return rejected


def verify():
    n = EquipmentOracle()
    count = 0
    for slot in range(50):
        for flag in (0, 1, 255):
            n.producer(0xa55a, slot, flag); count += 1
    for gate in (0, 1, 0xffffffff):
        for modal in (None, 0x232dea, 0x232e20):
            for flags in (0, 8, 0x20, 0x28):
                n.producer(1001, 34, 1, gate, modal, flags); count += 1
    guards = sum(n.deity_guard(k,b) for k in range(6999,8002) for b in range(4))
    labels = list(struct.unpack_from('<20H', n.image, 0x1905f0))
    require(labels[:12] == [64,65,66,67,68,69,69,70,64,65,68,69], 'Slot labels changed')
    return dict(client_sha256=PIN, producer_cases=count, guard_cases=4012,
                guard_rejected=guards, slot_label_ids=labels,
                scope='Producer+queue complete; rejection stops before message rendering; no full UI/server acceptance')


if __name__ == '__main__':
    print(json.dumps(verify(), ensure_ascii=False, indent=2))
