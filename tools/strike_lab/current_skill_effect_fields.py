"""Native skill numeric-field consumer; no inferred server coefficients."""
import hashlib
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'artifacts/tooling/crypto-oracle-python'))
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_PROT_READ, UC_PROT_EXEC
from unicorn import UC_HOOK_CODE, UC_HOOK_MEM_READ, UC_HOOK_MEM_WRITE
from unicorn import x86_const as reg
from .current_battle_character_binding import IMAGE, IMAGE_SHA
from .current_skill_identity import SOURCE, SOURCE_SHA256, decode_definitions

BASE, STACK, RECORD, OUTPUT = 0x400000, 0x3000000, 0x4000000, 0x4100000
SP, RETURN = STACK + 0x8000, BASE + 0x1000
FORMATS = (0x19d944, 0x19d938, 0x19d92c, 0x19d920, 0x19d914,
           0x19d908, 0x19d8fc, 0x19d8f0, 0x19d8e4, 0x19d8d4,
           0x19d8c4, 0x19d8b4, 0x19d8a4)


class NativeSkillEffectFields:
    def __init__(self):
        self.image = IMAGE.read_bytes()
        source = (ROOT.parent / 'God2' / SOURCE).read_bytes()
        if (hashlib.sha256(self.image).hexdigest() != IMAGE_SHA or
                hashlib.sha256(source).hexdigest() != SOURCE_SHA256):
            raise ValueError('Current image/catalog changed')
        self.definitions = decode_definitions(source)
        self.formats = [self.image[p:self.image.index(b'\0', p)] for p in FORMATS]
        self.vm = Uc(UC_ARCH_X86, UC_MODE_32)
        self.vm.mem_map(BASE, (len(self.image) + 4095) & ~4095, UC_PROT_READ | UC_PROT_EXEC)
        self.vm.mem_write(BASE, self.image)
        for at, size in ((STACK, 0x10000), (RECORD, 4096), (OUTPUT, 4096)):
            self.vm.mem_map(at, size)
        self.vm.hook_add(UC_HOOK_CODE, self.code)
        self.vm.hook_add(UC_HOOK_MEM_READ, self.read)
        self.vm.hook_add(UC_HOOK_MEM_WRITE, self.write)

    def code(self, vm, address, size, data):
        if address == RETURN:
            vm.emu_stop()
            return
        rva = address - BASE
        if not (0x126120 <= rva and rva + size <= 0x126263 or
                0x147000 <= rva and rva + size <= 0x16f000):
            raise AssertionError(f'Unqualified skill field consumer PC {rva:X}')
        if rva == 0x147af7:
            sp = vm.reg_read(reg.UC_X86_REG_ESP)
            self.format_calls.append(struct.unpack('<4I', vm.mem_read(sp + 4, 16)))

    def read(self, vm, access, address, size, value, data):
        if RECORD <= address < RECORD + 4096:
            self.record_reads.append((address - RECORD, size))

    def write(self, vm, access, address, size, value, data):
        if not (STACK <= address and address + size <= STACK + 0x10000 or
                OUTPUT <= address and address + size <= OUTPUT + 1024):
            raise AssertionError(f'Skill text consumer escaped output/stack: {address:X}')

    def execute(self, raw, amount):
        if type(raw) is not bytes or len(raw) != 110:
            raise ValueError('Explicit 110-byte skill record required')
        if type(amount) is not int or not -32768 <= amount <= 32767:
            raise ValueError('Explicit caller signed-WORD operand required')
        self.vm.mem_write(RECORD, raw + b'\xa5' * (4096 - len(raw)))
        self.vm.mem_write(OUTPUT, b'\xa5' * 4096)
        self.vm.mem_write(SP, struct.pack('<4I', RETURN, OUTPUT, RECORD, amount & 0xffffffff))
        self.vm.reg_write(reg.UC_X86_REG_ESP, SP)
        self.vm.reg_write(reg.UC_X86_REG_EFLAGS, 2)
        self.record_reads, self.format_calls = [], []
        self.vm.emu_start(BASE + 0x126120, RETURN, count=200000, timeout=1000000)
        if (self.vm.reg_read(reg.UC_X86_REG_EIP) != RETURN or
                self.vm.reg_read(reg.UC_X86_REG_ESP) != SP + 16):
            raise AssertionError('Native skill field consumer did not return')
        output = bytes(self.vm.mem_read(OUTPUT, 4096))
        if bytes(self.vm.mem_read(RECORD, 110)) != raw or output[1024:] != b'\xa5' * 3072:
            raise AssertionError('Skill source/output canary changed')
        end = output.index(b'\0', 0, 1024)
        return output[:end]
