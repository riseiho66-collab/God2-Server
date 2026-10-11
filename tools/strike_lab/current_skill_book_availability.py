"""Bounded original FE65B skill-book flag path; no learning or combat authority."""

import hashlib
import struct

from .current_skill_effect_fields import (
    Uc, UC_ARCH_X86, UC_MODE_32, UC_PROT_READ, UC_PROT_EXEC, UC_HOOK_CODE, reg,
)
from unicorn import UC_PROT_WRITE
from .recover_combat_rules import IMAGE, IMAGE_SHA256, read_pinned


BASE = 0x400000
ITEM, IDENTITY, OWNER, ENTRIES, CONTEXT, STACK = (0x3000000, 0x3010000, 0x3020000,
                                                  0x3030000, 0x3040000, 0x3050000)
SP = STACK + 0x8000
START, STOP = 0xFE65B, 0xFE684


class NativeSkillBookAvailability:
    def __init__(self):
        image = read_pinned(IMAGE, IMAGE_SHA256)
        self.image_hash = hashlib.sha256(image).hexdigest()
        self.path_hash = hashlib.sha256(image[START:STOP]).hexdigest()
        self.lookup_hash = hashlib.sha256(image[0xFE4D0:0xFE51C]).hexdigest()
        self.vm = Uc(UC_ARCH_X86, UC_MODE_32)
        self.vm.mem_map(BASE, (len(image) + 4095) & ~4095, UC_PROT_READ | UC_PROT_EXEC)
        self.vm.mem_write(BASE, image)
        for address, size in ((ITEM, 4096), (IDENTITY, 4096), (OWNER, 0xC000),
                              (ENTRIES, 4096)):
            self.vm.mem_map(address, size, UC_PROT_READ)
        self.vm.mem_map(CONTEXT, 4096, UC_PROT_READ | UC_PROT_WRITE)
        self.vm.mem_map(STACK, 0x10000, UC_PROT_READ | UC_PROT_WRITE)
        self.visited = []
        self.stop_rva = STOP
        self.follow_downstream = False
        self.vm.hook_add(UC_HOOK_CODE, self._code)

    def _code(self, vm, address, size, context):
        rva = address - BASE
        if rva == self.stop_rva:
            vm.emu_stop()
            return
        if not (START <= rva < STOP or 0xFE4D0 <= rva < 0xFE51C or
                (self.follow_downstream and rva == STOP) or
                (self.follow_downstream and 0x10CAA0 <= rva < 0x10CB3D)):
            raise AssertionError(f'Skill-book flag path left bounded original code: {rva:x}')
        self.visited.append(rva)

    def evaluate(self, tail, key, owned=(), *, owner_count=None):
        if type(tail) is not int or not 0 <= tail <= 255:
            raise ValueError('Tail must be a byte')
        if type(key) is not tuple or len(key) != 2 or any(type(v) is not int or not 0 <= v <= 255 for v in key):
            raise ValueError('Identity must be two bytes')
        if type(owned) not in (tuple, list) or len(owned) > 8 or any(
            type(entry) is not tuple or len(entry) != 2 or any(type(v) is not int or not 0 <= v <= 255 for v in entry)
            for entry in owned
        ):
            raise ValueError('Owned list must contain at most eight explicit two-byte identities')
        if owner_count is not None and (type(owner_count) is not int or owner_count != len(owned)):
            raise ValueError('Owner count must match staged entries')

        item = bytearray(4096)
        item[0x12C] = tail
        identity = bytes(key) + b'\xA5' * (4096 - 2)
        owner = bytearray(0xC000)
        struct.pack_into('<i', owner, 0xAB10, len(owned))
        entries = bytearray(4096)
        for index, entry in enumerate(owned):
            address = ENTRIES + index * 16
            struct.pack_into('<I', owner, 0xA91C + 4 * index, address)
            entries[index * 16:index * 16 + 2] = bytes(entry)
        for address, data in ((ITEM, item), (IDENTITY, identity), (OWNER, owner),
                              (ENTRIES, entries), (CONTEXT, b'\xA5' * 4096)):
            self.vm.mem_write(address, bytes(data))
        stack = bytearray(b'\xA5' * 0x100)
        struct.pack_into('<I', stack, 0x80 + 0x18, IDENTITY)
        self.vm.mem_write(SP - 0x80, bytes(stack))
        self.vm.reg_write(reg.UC_X86_REG_ESP, SP)
        self.vm.reg_write(reg.UC_X86_REG_EDX, ITEM)
        self.vm.reg_write(reg.UC_X86_REG_EBP, OWNER)
        self.vm.reg_write(reg.UC_X86_REG_ESI, 0x1234)
        self.vm.reg_write(reg.UC_X86_REG_EDI, CONTEXT)
        self.vm.reg_write(reg.UC_X86_REG_ECX, 0xDEAD0000)
        self.vm.reg_write(reg.UC_X86_REG_EAX, 0xBEEF0000)
        self.vm.reg_write(reg.UC_X86_REG_EFLAGS, 2)
        self.visited = []
        self.stop_rva = STOP
        self.follow_downstream = False
        self.vm.emu_start(BASE + START, BASE + STOP, count=100)
        if self.vm.reg_read(reg.UC_X86_REG_EIP) != BASE + STOP:
            raise AssertionError('Original skill-book flag path did not reach downstream call')
        esp = self.vm.reg_read(reg.UC_X86_REG_ESP)
        if esp != SP - 8 or self.vm.reg_read(reg.UC_X86_REG_ECX) != CONTEXT:
            raise AssertionError('Downstream call ABI differs')
        item_code, selector = struct.unpack('<II', self.vm.mem_read(esp, 8))
        if item_code != 0x1234 or selector not in (0, 1):
            raise AssertionError('Downstream flag or item code differs')
        for address, data in ((ITEM, item), (IDENTITY, identity), (OWNER, owner),
                              (ENTRIES, entries)):
            if bytes(self.vm.mem_read(address, len(data))) != bytes(data):
                raise AssertionError('Original flag path changed a source')
        if 0xFE4D0 in self.visited and tail != 0:
            raise AssertionError('Nonzero tail unexpectedly entered identity lookup')
        return {'selector': selector, 'lookup_entered': 0xFE4D0 in self.visited,
                'item_code': item_code, 'context': CONTEXT,
                'visited': tuple(self.visited)}

    def follow_ui_prefix(self, tail, key, owned=(), *, index=5):
        """Follow the real FE684 call only through 10CB3C; no formatter executes."""
        if type(index) is not int or not 0 <= index < 50:
            raise ValueError('UI index outside bounded original comparison')
        first = self.evaluate(tail, key, owned)
        esp = self.vm.reg_read(reg.UC_X86_REG_ESP)
        self.vm.mem_write(esp, struct.pack('<I', index))
        context = bytearray(4096)
        struct.pack_into('<H', context, 0x224, 0xFFFF)
        struct.pack_into('<H', context, 0x228, 0xFFFF)
        struct.pack_into('<I', context, 0x230, 0x11111111)
        struct.pack_into('<I', context, 0x234, 0x22222222)
        self.vm.mem_write(CONTEXT, bytes(context))
        self.stop_rva = 0x10CB3D
        self.follow_downstream = True
        self.visited = []
        self.vm.emu_start(BASE + STOP, BASE + self.stop_rva, count=100)
        if self.vm.reg_read(reg.UC_X86_REG_EIP) != BASE + self.stop_rva:
            raise AssertionError('Original UI prefix did not reach bounded stop')
        actual = bytes(self.vm.mem_read(CONTEXT, 4096))
        expected = bytearray(context)
        struct.pack_into('<I', expected, 0x148 + 4 * index, first['selector'])
        if actual != expected:
            raise AssertionError('Original UI prefix wrote outside its bounded selector slot')
        chosen = struct.unpack('<I', self.vm.mem_read(SP - 8, 4))[0]
        expected_source = 0x11111111 if first['selector'] else 0x22222222
        if chosen != expected_source:
            raise AssertionError('Original UI prefix chose an unexpected followup source')
        return {'selector': first['selector'], 'stored_at': 0x148 + 4 * index,
                'chosen_source': chosen, 'visited': tuple(self.visited)}
