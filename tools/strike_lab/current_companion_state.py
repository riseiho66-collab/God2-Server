"""Lossless S2C31 decoding and its bounded original deity-state projection.

Only the scalar prefix ending BEFORE RVA AA2AF is modeled. This neither creates
deities nor runs selection, paging or UI refresh effects after that boundary.
Field names describe bytes and stores; legacy gameplay labels are not authority.
"""
from dataclasses import dataclass
import struct


IMAGE_SHA = '149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
OPCODE, RECORD_SIZE = 0x31, 29
DISPATCH_RVA, CONSUMER_RVA, SCALAR_STOP_RVA = 0x69fa9, 0xaa200, 0xaa2af
COUNT_OFFSET, ROWS_OFFSET, ROW_STRIDE = 0xd4, 0xd8, 0x3ec


@dataclass(frozen=True)
class DeityStatusRecord:
    """Exact logical record, including the opcode and six ignored bytes."""

    raw: bytes

    def __post_init__(self):
        if not isinstance(self.raw, bytes):
            raise TypeError('Record must be immutable bytes')
        if len(self.raw) != RECORD_SIZE or self.raw[0] != OPCODE:
            raise ValueError('Expected exactly one 29-byte S2C31 logical record')

    @property
    def selector_raw(self):
        return self.raw[1]

    @property
    def selector_signed(self):
        return struct.unpack_from('<b', self.raw, 1)[0]

    @property
    def scalar_u8(self):
        return self.raw[2]

    @property
    def widened_u16(self):
        return struct.unpack_from('<5H', self.raw, 3)

    @property
    def copied_words(self):
        return struct.unpack_from('<4H', self.raw, 17)

    @property
    def split_word_raw(self):
        return struct.unpack_from('<H', self.raw, 25)[0]

    @property
    def low15(self):
        return self.split_word_raw & 0x7fff

    @property
    def high1(self):
        return self.split_word_raw >> 15

    @property
    def opaque_13_16(self):
        return self.raw[13:17]

    @property
    def opaque_27_28(self):
        return self.raw[27:29]

    def encode(self):
        return self.raw


def decode_deity_status(raw):
    """Decode a logical record, not a transport frame or a record batch."""
    if not isinstance(raw, (bytes, bytearray, memoryview)):
        raise TypeError('Record must be bytes-like')
    return DeityStatusRecord(bytes(raw))


@dataclass(frozen=True)
class ScalarProjection:
    matched_index: int | None
    state: bytes


def project_deity_status_scalar(state, logical):
    """Predict only AA200..AA2AF writes against supplied actor memory.

The byte count and WORD keys are existing client state, not owned catalog rows.
All unmatched state, opaque bytes and trailing memory survive exactly. A missing
key is a no-op. The first WORD equal to the sign-extended packet byte wins.
"""
    record = decode_deity_status(logical)
    if not isinstance(state, (bytes, bytearray, memoryview)):
        raise TypeError('State must be bytes-like')
    state = bytes(state)
    if len(state) < ROWS_OFFSET:
        raise ValueError('Truncated actor header')
    count = state[COUNT_OFFSET]
    if len(state) < ROWS_OFFSET + count * ROW_STRIDE:
        raise ValueError('Truncated declared deity rows')
    for index in range(count):
        row = ROWS_OFFSET + index * ROW_STRIDE
        if struct.unpack_from('<h', state, row)[0] != record.selector_signed:
            continue
        result = bytearray(state)
        result[row + 2] = record.scalar_u8
        for offset, value in zip(range(0x44, 0x58, 4), record.widened_u16):
            struct.pack_into('<I', result, row + offset, value)
        result[row + 0x38:row + 0x40] = record.raw[17:25]
        struct.pack_into('<H', result, row + 0x28, record.low15)
        result[row + 0x5a] = record.high1
        return ScalarProjection(index, bytes(result))
    return ScalarProjection(None, state)
