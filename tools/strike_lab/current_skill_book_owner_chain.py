"""Native owner-row identity through original skill-book lookup; UI continuation not run."""

import struct

from .current_skill_book_binding import NativeSkillBookBinding


class NativeSkillBookOwnerChain(NativeSkillBookBinding):
    CODE = NativeSkillBookBinding.CODE + ((0xFE520, 0xFE592),)

    def run(self, start, stop):
        if start != 0xFE520:
            return super().run(start, stop)
        self.active_code = True
        self.stop_address = self.BASE + stop
        try:
            self.vm.emu_start(self.BASE + start, self.stop_address,
                              count=500000, timeout=3000000)
        finally:
            self.active_code = False
        if self.vm.reg_read(self.x86.UC_X86_REG_EIP) != self.stop_address:
            raise AssertionError('Original owner-to-book lookup did not reach bounded stop')

    def owner_book(self, kind, skill_id, *, page=0):
        if type(kind) is not int or not 0 <= kind <= 3:
            raise ValueError('Original skill kind must be 0..3')
        if type(skill_id) is not int or not 1 <= skill_id <= 255:
            raise ValueError('Original skill identity must be 1..255')
        if type(page) is not int or not 0 <= page <= 4:
            raise ValueError('Page outside staged owner row table')
        slot = page * 10
        self.vm.mem_write(self.INPUT, bytes((skill_id, kind)) + b'\xA5' * (4096 - 2))
        self.vm.mem_write(self.OWNER + 0xAB1C, struct.pack('<I', page))
        self.vm.mem_write(self.OWNER + 0xA918, struct.pack('<I', slot + 1))
        self.vm.mem_write(self.OWNER + 0xA788 + 4 * slot, struct.pack('<I', self.INPUT))
        self.vm.mem_write(self.SP - 0x100, b'\xA5' * 0x200)
        self.vm.mem_write(self.SP, struct.pack('<I', self.RETURN))
        self.reg('ESP', self.SP)
        self.reg('ECX', self.OWNER)
        self.reg('EFLAGS', 2)
        self.visited = []
        self.comparisons = []
        self.branch_trace = []
        self.lookup_active = True
        try:
            self.run(0xFE520, 0xFE592)
        finally:
            self.lookup_active = False
        sp = self.vm.reg_read(self.x86.UC_X86_REG_ESP)
        if sp != self.SP - 32:
            raise AssertionError('Original owner selector stack changed')
        actor_ptr = struct.unpack('<I', self.vm.mem_read(sp + 0x18, 4))[0]
        item_ptr = struct.unpack('<I', self.vm.mem_read(sp + 0x14, 4))[0]
        if actor_ptr != self.INPUT or item_ptr != self.vm.reg_read(self.x86.UC_X86_REG_EAX):
            raise AssertionError('Original owner/book pointer publication differs')
        if item_ptr == 0:
            return {'page': page, 'slot': slot, 'kind': kind, 'skill_id': skill_id,
                    'item_id': None, 'item_ptr': 0, 'tail_12c': None, 'code': None,
                    'lookup_keys': tuple(self.visited), 'source_line': None}
        matches = [(key, raw) for key, (address, raw) in self.records.items() if address == item_ptr]
        if len(matches) != 1:
            raise AssertionError('Original book lookup did not select one pinned source record')
        item_id, raw = matches[0]
        return {'page': page, 'slot': slot, 'kind': kind, 'skill_id': skill_id,
                'item_id': item_id, 'item_ptr': item_ptr,
                'tail_12c': raw[0x12C], 'code': raw[0x11C:0x12C].split(b'\0', 1)[0].decode('ascii'),
                'lookup_keys': tuple(self.visited), 'source_line': self.sources[item_id]['source_line']}
