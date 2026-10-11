"""Retained-state MP synchronization and eligibility; not inferred cast debit."""
import struct

from .current_skill_mp_gate import NativeSkillMpGate, BASE, OWNER, ROLE, SP, reg
from unicorn import UC_PROT_READ, UC_PROT_WRITE

PACKET = 0x3500000


class NativeSkillMpSync(NativeSkillMpGate):
    def __init__(self):
        self.updating = False
        super().__init__()
        self.vm.mem_map(PACKET, 4096, UC_PROT_READ)

    def code(self, vm, address, size, context):
        if not self.updating:
            return super().code(vm, address, size, context)
        rva = address - BASE
        if rva == 0xe63c5:
            vm.emu_stop()
            return
        if not (0x69eb0 <= rva and rva + size <= 0x69ebf or
                0xe6390 <= rva and rva + size <= 0xe63c5):
            raise AssertionError(f'Unexpected role sync instruction: {rva:x}')

    def apply_current_vitals(self, raw):
        if type(raw) is not bytes or len(raw) != 21 or raw[0] != 0x2b:
            raise ValueError('An explicit complete 21-byte logical S2C2B is required')
        before = bytes(self.vm.mem_read(ROLE, 4096))
        expected = bytearray(before)
        expected[0x5c:0x60] = raw[1:5]
        expected[0x64:0x68] = raw[9:13]
        expected[0x58:0x5a] = raw[17:19]
        self.vm.mem_write(PACKET, raw)
        self.vm.reg_write(reg.UC_X86_REG_ESP, SP)
        self.vm.reg_write(reg.UC_X86_REG_EBX, PACKET)
        self.vm.reg_write(reg.UC_X86_REG_EBP, (OWNER - 0xa7f2f6c) & 0xffffffff)
        self.vm.reg_write(reg.UC_X86_REG_EFLAGS, 2)
        self.vm.mem_protect(ROLE, 4096, UC_PROT_READ | UC_PROT_WRITE)
        self.updating = True
        try:
            self.vm.emu_start(BASE + 0x69eb0, BASE + 0xe63c5, count=100)
        finally:
            self.updating = False
            self.vm.mem_protect(ROLE, 4096, UC_PROT_READ)
        if self.vm.reg_read(reg.UC_X86_REG_EIP) != BASE + 0xe63c5:
            raise AssertionError('Role receive prefix did not reach the declared refresh boundary')
        if bytes(self.vm.mem_read(ROLE, 4096)) != bytes(expected):
            raise AssertionError('Original receive changed unexpected role state')
        if bytes(self.vm.mem_read(PACKET, 21)) != raw:
            raise AssertionError('Input packet changed')
        return struct.unpack_from('<I', expected, 0x64)[0]
