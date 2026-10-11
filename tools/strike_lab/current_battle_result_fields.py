"""Current S2C 86, record discriminator 3: transmitted result bits, not damage.

Research-only model of 117480 -> 12C3E0, stopping before 126270.
Bounds below belong to this model; they are not recovered server policy.
"""
from dataclasses import dataclass
import struct

IMAGE_SHA256 = '149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
OPCODE, RECORD_SIZE = 0x86, 17
NEXT_CONSUMER = 0x126270
runtime_mutation_enabled = False


@dataclass(frozen=True)
class State:
    dispatch_state: int
    local_slot: int
    cached_dword: int
    # Selected type-0 entity snapshot, or an explicitly null lookup result.
    entity: bytes | None

    def __post_init__(self):
        if type(self.dispatch_state) is not int or self.dispatch_state != 3:
            raise ValueError('Only explicit dispatch state 3 is qualified')
        if type(self.local_slot) is not int or not 0 <= self.local_slot < 14:
            raise ValueError('Expected local slot 0..13')
        if type(self.cached_dword) is not int or not 0 <= self.cached_dword < 2**32:
            raise ValueError('Expected raw cached DWORD')
        if self.entity is not None and (type(self.entity) is not bytes or
                                       len(self.entity) != 4096):
            raise ValueError('Expected explicit 4096-byte entity snapshot or None')


@dataclass(frozen=True)
class Result:
    record: bytes
    side: int
    slot: int
    cached_dword: int
    entity: bytes | None
    next_consumer: int | None


def consume(record, state):
    """Model exactly the qualified prefix, preserving every other byte.

    Logical +2 selects side/slot; +5 DWORD becomes 1 when bit 0 is set.
    A nonnull entity with signed WORD +1A >= 0 receives logical +5 at
    entity +DB8 and logical +3 WORD at +278. No HP/damage meaning is asserted.
    """
    if type(record) is not bytes or len(record) != RECORD_SIZE or record[0] != OPCODE:
        raise ValueError('Expected one 17-byte logical 0x86 record')
    if not isinstance(state, State):
        raise ValueError('Expected explicit result-consumer state')
    if record[1] != state.dispatch_state:
        raise ValueError('Record discriminator must match qualified state 3')
    if record[2] >= 28:
        raise ValueError('Outside qualified two-side fourteen-slot domain')
    side, slot = divmod(record[2], 14)
    word = struct.unpack_from('<H', record, 3)[0]
    value = struct.unpack_from('<I', record, 5)[0]
    normalized = bytearray(record)
    if value & 1:
        value = 1
        struct.pack_into('<I', normalized, 5, value)
    cached = value if side == 0 and slot == state.local_slot else state.cached_dword
    entity, following = state.entity, None
    if entity is not None and struct.unpack_from('<h', entity, 0x1a)[0] >= 0:
        output = bytearray(entity)
        struct.pack_into('<I', output, 0xdb8, value)
        struct.pack_into('<H', output, 0x278, word)
        entity, following = bytes(output), NEXT_CONSUMER
    return Result(bytes(normalized), side, slot, cached, entity, following)
