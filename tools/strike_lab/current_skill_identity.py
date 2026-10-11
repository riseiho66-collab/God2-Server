"""Current cbspec2 identity and bounded 11C520 selection state, without gameplay."""
from dataclasses import dataclass
import struct

IMAGE_SHA256 = '149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
SOURCE = 'Data2/Fight/Spg/cbspec2.bin'
SOURCE_SHA256 = '7676acd93f164d071f7681a3fe74de94d65892759dbf2e69e3c0f748423d2f51'
GROUP_STRIDE = 0x6e04
RECORD_SIZE = 110
FILE_SIZE = 4 + 4 * GROUP_STRIDE


@dataclass(frozen=True)
class StateIdentity:
    raw: int
    id: int
    kind: int
    alternate_table: bool
    state_bit: bool


def decode_state_word(raw):
    """Exactly the two bytes consumed by 11C520, not an asserted wire opcode."""
    if len(raw) != 2:
        raise ValueError('Expected exactly one two-byte state word')
    word, = struct.unpack('<H', raw)
    return StateIdentity(word, word & 255, (word >> 8) & 63,
                         bool(word & 0x4000), bool(word & 0x8000))


@dataclass(frozen=True)
class Definition:
    id: int
    kind: int
    source_offset: int
    raw: bytes


def decode_definitions(source):
    """Decode source identities only. All other definition bytes stay raw."""
    if len(source) != FILE_SIZE or source[:4] != b'1.03':
        raise ValueError('Expected complete four-group cbspec2 version 1.03')
    result = {}
    for kind in range(4):
        group = 4 + kind * GROUP_STRIDE
        count, = struct.unpack_from('<I', source, group)
        if count > 255:
            raise ValueError('Count exceeds the nonzero one-byte identity subset')
        for ordinal in range(count):
            offset = group + 4 + ordinal * RECORD_SIZE
            raw = bytes(source[offset:offset + RECORD_SIZE])
            if raw[:2] != bytes((ordinal + 1, kind)):
                raise ValueError('Source identity differs from native direct addressing')
            result[kind, ordinal + 1] = Definition(ordinal + 1, kind, offset, raw)
    return result


class SelectionState:
    """Client table subset, never learned ownership or authoritative battle state.

    Caller supplies the current bank. Native accessors admit 16 primary and 3
    alternate banks; physical WORD/pointer arrays admit 100 and 10 entries.
    Overflow is rejected here instead of reproducing unchecked native writes.
    """
    def __init__(self, definitions):
        self.definitions = dict(definitions)
        self._banks = {}

    @staticmethod
    def _key(alternate, bank):
        if type(alternate) is not bool or type(bank) is not int or not (
                0 <= bank < (3 if alternate else 16)):
            raise ValueError('Invalid client selection bank')
        return alternate, bank

    def apply(self, raw, bank):
        identity = decode_state_word(raw)
        key = self._key(identity.alternate_table, bank)
        definition = self.definitions.get((identity.kind, identity.id))
        if definition is None:
            raise ValueError('State identity has no populated source definition')
        entries = self._banks.get(key, [])
        for slot, (previous, existing) in enumerate(entries):
            if (existing.kind, existing.id) == (identity.kind, identity.id):
                # 11C5A9..11C5BC / 11C72F..11C741 replace only bit 15.
                entries[slot] = ((previous & 0x7fff) | (identity.raw & 0x8000), existing)
                return slot
        if len(entries) >= (10 if identity.alternate_table else 100):
            raise ValueError('Client selection table capacity exceeded')
        self._banks.setdefault(key, entries).append((identity.raw, definition))
        return len(entries) - 1

    def entries(self, alternate, bank):
        return tuple(self._banks.get(self._key(alternate, bank), ()))

    def select(self, alternate, bank, slot):
        entries = self.entries(alternate, bank)
        if type(slot) is not int or not 0 <= slot < len(entries):
            raise ValueError('Selection slot out of range')
        return entries[slot]
