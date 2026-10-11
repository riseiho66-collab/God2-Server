"""Original RomMaps and item row parsing, not authoritative item gameplay."""
import struct

from . import recover_companion_growth as growth
from . import recover_items
from .recover_combat_rules import CLIENT, IMAGE, IMAGE_SHA256, SKILLS, SOURCE_HASHES, read_pinned
from .omega_assets import decode_csvz


class NativeItemMetadata(growth._NativeRows):
    ITEM_SECTIONS = ('EGG', 'SPP', 'MIS', 'WPN', 'EQU', 'TWP', 'TEQ', 'SKB', 'MED02')
    MAPS = 0x3500000
    OWNER = 0x3600000
    RECORD = 0x3700000
    CODE = ((0x51ae0, 0x51cd2), (0x59420, 0x59960), (0x59f47, 0x59fa3),
            (0x59fc0, 0x59ff7), (0x59a20, 0x59a27), (0x59a60, 0x59a7e),
            (0x9b720, 0x9b768), (0x148990, 0x148a5c), (0x147b80, 0x147c7e))

    def __init__(self, *, vm=None):
        self.image = read_pinned(IMAGE, IMAGE_SHA256)
        if vm is not None:
            for low, high in self.CODE:
                if bytes(vm.mem_read(self.BASE + low, high - low)) != self.image[low:high]:
                    raise ValueError('Attached VM native metadata code changed')
        super().__init__(self.image, vm=vm)
        self.retained_key = None
        self.executed = set()
        self.active_code = False
        self.vm.hook_add(self.uc.UC_HOOK_CODE, self._code)
        raw = read_pinned(CLIENT / SKILLS, SOURCE_HASHES[SKILLS])
        self.decoded = decode_csvz(raw)
        self.sections = growth.parse_sections(self.decoded, self.ITEM_SECTIONS)
        for address, size in ((self.MAPS, 0x2000), (self.OWNER, 0x100000), (self.RECORD, 0x1000)):
            self.vm.mem_map(address, size, self.uc.UC_PROT_READ | self.uc.UC_PROT_WRITE)
        lines = self.decoded.split(b'\n')
        offsets, offset = [], 0
        for line in lines:
            offsets.append(offset)
            offset += len(line) + 1
        self.map_rows = [growth.record(lines[number - 1] + b'\n', number, offsets[number - 1])
                         for number, _ in recover_items.section(
                             recover_items.lines_of(self.decoded), b'RomMaps')]
        if len(self.map_rows) != 57:
            raise ValueError('Current RomMaps denominator changed')
        self.vm.mem_write(self.MAPS, b'\xa5' * 0x2000)
        self.vm.mem_write(self.TABLE + 0xd2d54, struct.pack('<H', 57))
        self.vm.mem_write(self.TABLE + 0xd2d58, struct.pack('<I', self.MAPS))
        self.vm.mem_write(self.OWNER + 0xcff70, struct.pack('<I', self.TABLE))
        self._load_maps()

    def _code(self, vm, address, size, context):
        if not self.active_code or address == self.stop_address:
            return
        pc = address - self.BASE
        if pc != 0x1480b4 and not any(low <= pc < high for low, high in self.CODE):
            raise AssertionError(f'Unexpected native metadata instruction: {pc:x}')
        self.executed.add(pc)

    def run(self, start, stop):
        self.active_code = True
        self.stop_address = self.BASE + stop
        try:
            super().run(start, stop)
        finally:
            self.active_code = False

    def _load_maps(self):
        expected = bytearray(b'\xa5' * 0x2000)
        for ordinal, row in enumerate(self.map_rows):
            values = growth.fields(row)
            index, low, high = map(growth.decimal, values[:3])
            if index != ordinal or len(values[3]) >= 128:
                raise ValueError('RomMaps row outside native bounds')
            self.tokenize(row, len(values))
            self.vm.mem_write(self.SP + 0x10, struct.pack('<I', index))
            self.reg('ESI', self.TABLE)
            start = self.MAPS + index * 0x84
            self.row(0x59f47, 0x59fa3, (1, 2, 3), [(start, start + 0x84)])
            struct.pack_into('<HH', expected, index * 0x84, low, high)
            expected[index * 0x84 + 4:index * 0x84 + 5 + len(values[3])] = values[3] + b'\0'
        if bytes(self.vm.mem_read(self.MAPS, 0x2000)) != expected:
            raise AssertionError('Original RomMaps bytes/canaries differ')

    def call(self, entry, *args, this=None, allowed=()):
        self.vm.mem_write(self.SP - 0x600, b'\xa5' * 0x700)
        self.vm.mem_write(self.SP, struct.pack('<' + 'I' * (1 + len(args)), self.RETURN, *args))
        self.reg('ESP', self.SP)
        self.reg('ECX', self.TABLE if this is None else this)
        self.reg('EFLAGS', 2)
        self.allowed = allowed
        self.writes.clear()
        try:
            self.run(entry, self.RETURN - self.BASE)
        finally:
            self.allowed = None
        if self.vm.reg_read(self.x86.UC_X86_REG_ESP) != self.SP + 4 + len(args) * 4:
            raise AssertionError('Native callee stack imbalance')
        return self.vm.reg_read(self.x86.UC_X86_REG_EAX)

    def icon_map(self, value):
        if type(value) is not int or not 0 <= value <= 0xffffffff:
            raise ValueError('Expected a raw DWORD argument')
        return self.call(0x59fc0, value) & 0xffff

    def egg_row(self, section, index):
        if section not in ('EGG', 'SPP') or type(index) is not int:
            raise ValueError('Only current qualified EGG/SPP rows')
        return self.item_row(section, index)

    def section_selector(self,section):
        # Default item families have a direct first-match three-byte tag.
        # A separately qualified category lookup may override this (GOD).
        tags=[]
        for ordinal in range(36):
            at=struct.unpack_from('<I',self.image,0x1897ec+ordinal*4)[0]-self.BASE
            tags.append(self.image[at:self.image.index(0,at)])
        selector=next(i for i,tag in enumerate(tags) if tag[:3]==section.encode()[:3])
        if tags[selector][:3]!=section.encode()[:3]:raise AssertionError('Native tag binding changed')
        return selector

    def item_row(self, section, index, *, retain=False):
        if section not in self.ITEM_SECTIONS or type(index) is not int or type(retain) is not bool:
            raise ValueError('Only current qualified item sections')
        if self.retained_key is not None:
            raise ValueError('Retained native item record cannot be overwritten')
        rows = self.sections[section]['records']
        if not 0 <= index < len(rows):
            raise ValueError('Source row index outside section')
        row = rows[index]
        values = growth.fields(row)
        key = growth.decimal(values[0])
        # 59301's first-match native tag table supplies 59420's branch selector.
        # Use the original first-match three-byte tag rule.
        selector=self.section_selector(section)
        if not 0<=selector<36 or not 0 < key < 0x7f58:
            raise AssertionError('Native section binding changed')
        self.tokenize(row, len(values))
        self.vm.mem_write(self.RECORD, b'\xa5' * 16 + bytes(0x18c) + b'\xa5' * 16)
        record = self.RECORD + 16
        self.call(0x59420, key, record, 0, selector,
                  allowed=((record, record + 0x18c),))
        parsed = bytes(self.vm.mem_read(record, 0x18c))
        if (bytes(self.vm.mem_read(self.RECORD, 16)) != b'\xa5' * 16 or
                bytes(self.vm.mem_read(record + 0x18c, 16)) != b'\xa5' * 16):
            raise AssertionError('Native item row exceeded record')
        # Execute the original index-store instruction, never write its pointer directly.
        self.reg('ESI', self.TABLE)
        self.reg('EAX', key)
        self.reg('EDX', record)
        index_address = self.TABLE + 0xb2d40 + key * 4
        self.allowed = ((index_address, index_address + 4),)
        try:
            self.run(0x59a20, 0x59a27)
        finally:
            self.allowed = None
        if self.call(0x59a60, key) != record:
            raise AssertionError('Original item lookup lost row')
        self.vm.mem_write(self.OUTPUT, b'\xa5' * 16)
        self.call(0x9b720, key, self.OUTPUT + 4, self.OUTPUT + 8, this=self.OWNER,
                  allowed=((self.OUTPUT + 4, self.OUTPUT + 6), (self.OUTPUT + 8, self.OUTPUT + 10)))
        output = bytes(self.vm.mem_read(self.OUTPUT, 16))
        group, action = struct.unpack_from('<H', output, 4)[0], struct.unpack_from('<H', output, 8)[0]
        expected = bytearray(b'\xa5' * 16)
        struct.pack_into('<H', expected, 4, group)
        struct.pack_into('<H', expected, 8, action)
        if output != expected or (group, action) != struct.unpack_from('<HH', parsed, 0x116):
            raise AssertionError('Original resource consumer differs from parsed row')
        # Every call owns a single temporary row. Do not leave prior IDs aliasing it.
        if retain:
            self.retained_key = key
        else:
            self.vm.mem_write(index_address, bytes(4))
        return {'source_line': row['source_line'], 'key': key, 'section': section,
                'selector': selector, 'record': parsed, 'group': group, 'action': action,
                'columns': tuple(self.columns)}
