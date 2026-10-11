"""Bounded original S2C34 writer on a caller's existing character/catalog VM.

No catalog loader, ownership inference, refresh, or diagnostic replacement.
The caller qualifies catalog provenance; the standalone tests use raw bytes.
"""
import struct

from unicorn import UC_HOOK_MEM_READ, UC_PROT_READ, UC_PROT_WRITE

from tools.strike_lab.current_battle_character_binding import (
    BASE, COUNT_OFFSET, ROOT_SIZE, ROW_COUNT, ROWS_OFFSET, ROW_STRIDE,
    NativeBattleCharacterBinding,
)


CATALOG_OFFSET = 0xa924d7c
CATALOG_BANKS, BANK_STRIDE, ENTRY_SIZE = 4, 0x6e04, 0x6e
CATALOG_SIZE = CATALOG_BANKS * BANK_STRIDE
CATALOG_POINTER = 0x4504
LEARNED_COUNT, LEARNED_FLAGS, LEARNED_POINTERS = 0x1f0, 0x1f1, 0x258
MAX_LEARNED, PACKET_LENGTH = 100, 4
DISPATCH, RETURN, DUPLICATE_STOP, REFRESH_STOP = 0x69fdf, 0x69fec, 0xaa72b, 0xaa7bf
# Exclude the assertion, duplicate diagnostic, and every refresh instruction.
WRITER_RANGES = ((DISPATCH, RETURN), (0xaa660, 0xaa6be),
                 (0xaa6d5, DUPLICATE_STOP), (0xaa74f, REFRESH_STOP),
                 (0xaa7f3, 0xaa82a))


class NativeBattleLearnedSkills:
    """Compose with NativeBattleCharacterBinding; all memory stays in its VM.

    ``battle+A924D7C`` must already contain a caller-qualified current catalog.
    This class does not certify how it was loaded. CPU context is restored;
    original writes and the binding's dedicated scratch writes are retained.
    Scratch stack [sp-100,sp+100) and packet [packet,packet+4) must be disjoint
    from each other, the image, actor, catalog, and packet-source pointer slot.
    """

    def __init__(self, character, *, battle):
        if not isinstance(character, NativeBattleCharacterBinding):
            raise TypeError('Existing NativeBattleCharacterBinding required')
        self.character, self.vm = character, character.vm
        self.battle, self.catalog = battle, battle + CATALOG_OFFSET
        self._check_layout()

    def _check_layout(self):
        n = self.character
        spans = ((n.root, n.root + ROOT_SIZE, UC_PROT_READ | UC_PROT_WRITE),
                 (n.ui + 0x86888, n.ui + 0x8688c, UC_PROT_READ),
                 (n.sp - 0x100, n.sp + 0x100, UC_PROT_READ | UC_PROT_WRITE),
                 (n.packet, n.packet + PACKET_LENGTH, UC_PROT_READ | UC_PROT_WRITE),
                 (self.catalog, self.catalog + CATALOG_SIZE, UC_PROT_READ),
                 (BASE, BASE + len(n.image), UC_PROT_READ))
        if not 0 <= self.battle < 2**32:
            raise ValueError('Battle address outside 32-bit bounds')
        regions = sorted(self.vm.mem_regions())
        for index, (lo, hi, permission) in enumerate(spans):
            if not 0 <= lo < hi <= 2**32:
                raise ValueError('Learned-skill storage outside 32-bit bounds')
            if any(lo < z and a < hi for a, z, _ in spans[:index]):
                raise ValueError('Learned-skill storage spans overlap')
            cursor = lo
            for a, z, protection in regions:
                if a <= cursor <= z and protection & permission == permission:
                    cursor = min(hi, z + 1)
                if cursor == hi:
                    break
            if cursor != hi:
                raise ValueError('Learned-skill storage unmapped or lacks permissions')

    def _run(self, start, stop, ranges, *, registers, writable):
        n = self.character
        self._check_layout()
        readable = ((n.sp - 0x100, n.sp + 0x100),
                    (n.packet, n.packet + PACKET_LENGTH),
                    (n.root, n.root + ROOT_SIZE),
                    (n.ui + 0x86888, n.ui + 0x8688c),
                    (self.catalog, self.catalog + CATALOG_SIZE))

        def guard_read(vm, access, address, size, value, data):
            if not any(a <= address and address + size <= z for a, z in readable):
                raise AssertionError(f'Unqualified learned-skill read {address:X}')

        hook = self.vm.hook_add(UC_HOOK_MEM_READ, guard_read)
        try:
            return n._run(start, stop, ranges, registers=registers, writable=writable)
        finally:
            self.vm.hook_del(hook)

    def publish_catalog_pointer(self):
        """Original 687EB..68804, with ECX explicitly staged as battle owner.

        The preceding manager read at 687DB is not executed. The contiguous
        slice also zeros root+A8 at 687F1; it does not initialize other state.
        """
        n = self.character
        trace = self._run(0x687eb, 0x68804, ((0x687eb, 0x68804),),
                          registers={'ECX': self.battle, 'EBP': n.root},
                          writable=((n.root + 0xa8, n.root + 0xac),
                                    (n.root + CATALOG_POINTER, n.root + CATALOG_POINTER + 4)))
        if n.u32(n.root + CATALOG_POINTER) != self.catalog:
            raise AssertionError('Original catalog publication differs')
        return trace

    def _entry(self, bank, entry):
        if not 0 <= bank < CATALOG_BANKS or not 1 <= entry <= 255:
            raise ValueError('Catalog bank/entry outside packet bounds')
        count = self.character.u32(self.catalog + bank * BANK_STRIDE)
        if not 1 <= count <= 256 or entry > count:
            raise ValueError('Catalog entry outside populated bank count')
        pointer = self.catalog + bank * BANK_STRIDE + 4 + (entry - 1) * ENTRY_SIZE
        record = bytes(self.vm.mem_read(pointer, ENTRY_SIZE))
        if record[:2] != bytes((entry, bank)) or not any(record[2:]):
            raise ValueError('Nonzero catalog record with matching identity required')
        return pointer

    def _existing_identity(self, pointer):
        offset = pointer - self.catalog
        if not 0 <= offset < CATALOG_SIZE:
            raise ValueError('Existing learned pointer outside catalog bounds')
        bank, within = divmod(offset, BANK_STRIDE)
        slot, remainder = divmod(within - 4, ENTRY_SIZE)
        if within < 4 or remainder or not 0 <= slot < 255:
            raise ValueError('Existing learned pointer is not a packet-addressable record')
        entry = slot + 1
        if self._entry(bank, entry) != pointer:
            raise AssertionError('Catalog record address differs')
        return bank, entry

    def write_learned_skill(self, raw):
        """Execute explicit logical [34, unsigned row key, bank, entry].

        Returns a native trace plus ``outcome``, ``row``, and ``pointer``.
        ``appended`` stops BEFORE AA7BF refresh; ``duplicate`` stops BEFORE
        AA72B diagnostic setup (no mutation, not a completed duplicate return).
        ``full`` and ``no_matching_row`` return normally to 69FEC. Counts above
        capacity, ambiguous row keys, zero/unpopulated entries, and invalid
        existing pointers are rejected before packet or actor writes.
        """
        n = self.character
        if type(raw) is not bytes or len(raw) != PACKET_LENGTH or raw[0] != 0x34:
            raise ValueError('Explicit 4-byte logical S2C34 required')
        self._check_layout()
        if n.u32(n.ui + 0x86888) != n.source:
            raise ValueError('Original packet-source binding required')
        if n.u32(n.root + CATALOG_POINTER) != self.catalog:
            raise ValueError('Original catalog pointer publication required')
        key, bank, entry = raw[1:]
        pointer = self._entry(bank, entry)
        count = self.vm.mem_read(n.source + COUNT_OFFSET, 1)[0]
        if count > ROW_COUNT:
            raise ValueError('Source row count exceeds sixteen rows')
        rows = [n.source + ROWS_OFFSET + i * ROW_STRIDE for i in range(count)]
        matches = [row for row in rows if struct.unpack('<H', self.vm.mem_read(row, 2))[0] == key]
        if len(matches) > 1:
            raise ValueError('Ambiguous matching row keys')
        row = matches[0] if matches else None
        stop, outcome, writable = RETURN, 'no_matching_row', ()
        if row is not None:
            learned = self.vm.mem_read(row + LEARNED_COUNT, 1)[0]
            if learned > MAX_LEARNED:
                raise ValueError('Learned count exceeds one hundred slots')
            if learned == MAX_LEARNED:
                outcome = 'full'
            else:
                identities = [self._existing_identity(n.u32(row + LEARNED_POINTERS + i * 4))
                              for i in range(learned)]
                if (bank, entry) in identities:
                    stop, outcome = DUPLICATE_STOP, 'duplicate'
                else:
                    stop, outcome = REFRESH_STOP, 'appended'
                    writable = ((row + LEARNED_COUNT, row + LEARNED_COUNT + 1),
                                (row + LEARNED_FLAGS + learned, row + LEARNED_FLAGS + learned + 1),
                                (row + LEARNED_POINTERS + learned * 4,
                                 row + LEARNED_POINTERS + learned * 4 + 4))
        # Validate code before touching even the scratch packet.
        for first, last in WRITER_RANGES:
            if bytes(self.vm.mem_read(BASE + first, last - first)) != n.image[first:last]:
                raise ValueError('Original executable bytes changed in supplied VM')
        self.vm.mem_write(n.packet, raw)
        trace = self._run(DISPATCH, stop, WRITER_RANGES,
                          registers={'EBX': n.packet, 'EBP': (n.ui - 0xa7f2f6c) & 0xffffffff},
                          writable=writable)
        trace.update(outcome=outcome, row=row, pointer=pointer)
        return trace
