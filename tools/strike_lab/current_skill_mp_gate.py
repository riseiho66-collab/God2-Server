"""Original client skill MP eligibility predicates, not server debit rules."""
import struct

from .current_skill_effect_fields import Uc, UC_ARCH_X86, UC_MODE_32, UC_PROT_READ, UC_PROT_EXEC, UC_HOOK_CODE, reg
from .current_skill_identity import SOURCE, SOURCE_SHA256, decode_definitions
from .recover_combat_rules import CLIENT, IMAGE, IMAGE_SHA256, read_pinned

BASE, OWNER, ROLE, MENU, DEFINITION, STACK = 0x400000, 0x3000000, 0x3100000, 0x3200000, 0x3300000, 0x3400000
SP, RETURN = STACK + 0x8000, BASE + 0x1000


class NativeSkillMpGate:
    def __init__(self):
        image = read_pinned(IMAGE, IMAGE_SHA256)
        self.definitions = decode_definitions(read_pinned(CLIENT / SOURCE, SOURCE_SHA256))
        self.vm = Uc(UC_ARCH_X86, UC_MODE_32)
        self.vm.mem_map(BASE, (len(image) + 4095) & ~4095, UC_PROT_READ | UC_PROT_EXEC)
        self.vm.mem_write(BASE, image)
        for address, size in ((OWNER, 0x100000), (ROLE, 4096), (MENU, 4096), (DEFINITION, 4096)):
            self.vm.mem_map(address, size, UC_PROT_READ)
        self.vm.mem_map(STACK, 0x10000)
        self.vm.mem_write(OWNER + 0x86888, struct.pack('<I', ROLE))
        self.vm.hook_add(UC_HOOK_CODE, self.code)

    def code(self, vm, address, size, context):
        if address == RETURN:
            vm.emu_stop()
            return
        rva = address - BASE
        if not (0xa9070 <= rva and rva + size <= 0xa90c2 or
                0xa90d0 <= rva and rva + size <= 0xa9110):
            raise AssertionError(f'MP predicate left qualified code: {rva:x}')

    def evaluate(self, raw, mp, *, mode='indexed', index=0, page=0, selected=0,
                 menu_present=True, entry_present=True):
        if type(raw) is not bytes or len(raw) != 110:
            raise ValueError('An explicit original-sized skill record is required')
        if type(mp) is not int or not 0 <= mp <= 0xffffffff:
            raise ValueError('MP must be a raw unsigned DWORD')
        if mode not in ('indexed', 'selected'):
            raise ValueError('Unknown predicate')
        if type(index) is not int or not -0x80000000 <= index < 100:
            raise ValueError('Nonnegative index must fit the staged 100-slot table')
        if type(page) is not int or not 0 <= page <= 3:
            raise ValueError('Page must fit the staged 100-slot table')
        if type(selected) is not int or not -128 <= selected < 25:
            raise ValueError('Selection must fit one staged 25-slot page or be negative')
        if type(menu_present) is not bool or type(entry_present) is not bool:
            raise ValueError('Presence must be explicit boolean')
        slot = index if mode == 'indexed' else page * 25 + selected
        role, menu = bytearray(4096), bytearray(4096)
        struct.pack_into('<I', role, 0x64, mp)
        struct.pack_into('<I', role, 0xd0, MENU if menu_present else 0)
        menu[0x3e8] = page
        if slot >= 0:
            struct.pack_into('<I', menu, 0x258 + 4 * slot, DEFINITION if entry_present else 0)
        self.vm.mem_write(ROLE, bytes(role))
        self.vm.mem_write(MENU, bytes(menu))
        self.vm.mem_write(DEFINITION, raw + b'\xa5' * (4096 - len(raw)))
        self.vm.mem_write(BASE + 0x1b6c79, bytes((selected & 255,)))
        result = self.run_staged_predicate(mode, index)
        if (bytes(self.vm.mem_read(ROLE, 4096)) != bytes(role) or
                bytes(self.vm.mem_read(MENU, 4096)) != bytes(menu) or
                bytes(self.vm.mem_read(DEFINITION, 110)) != raw):
            raise AssertionError('Read-only eligibility predicate modified an input')
        return result

    def run_staged_predicate(self, mode, index):
        """Reuse already staged role/menu state without resetting its MP."""
        if mode not in ('indexed', 'selected') or type(index) is not int or not -0x80000000 <= index < 100:
            raise ValueError('Outside staged predicate bounds')
        self.vm.mem_write(SP, struct.pack('<2I', RETURN, index & 0xffffffff))
        self.vm.reg_write(reg.UC_X86_REG_ESP, SP)
        self.vm.reg_write(reg.UC_X86_REG_ECX, OWNER)
        self.vm.reg_write(reg.UC_X86_REG_EFLAGS, 2)
        entry = 0xa90d0 if mode == 'indexed' else 0xa9070
        self.vm.emu_start(BASE + entry, RETURN, count=1000)
        if (self.vm.reg_read(reg.UC_X86_REG_EIP) != RETURN or
                self.vm.reg_read(reg.UC_X86_REG_ESP) != SP + (8 if mode == 'indexed' else 4)):
            raise AssertionError('Original MP predicate did not return with its expected ABI')
        result = self.vm.reg_read(reg.UC_X86_REG_EAX)
        if result not in (0, 1):
            raise AssertionError('Original predicate returned a nonboolean')
        return bool(result)
