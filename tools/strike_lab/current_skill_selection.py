"""Bounded current-native 0x38 bank-state transition, not cast authorization."""
from dataclasses import dataclass, replace

IMAGE_SHA256 = '149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'


@dataclass(frozen=True)
class Bank:
    key_word: int
    state_byte: int
    words: tuple[int, ...]
    auxiliary: bytes


@dataclass(frozen=True)
class Transition:
    banks: tuple[Bank, ...]
    current_bank_byte: int
    # Signed AX from 11C7F0; -1 also occurs after a successful state mutation.
    returned_index: int


def _unsigned(value, limit):
    return type(value) is int and 0 <= value < limit


def apply_selection_record(record: bytes, banks: tuple[Bank, ...],
                           current_bank_byte: int) -> Transition:
    """Apply one complete logical 38 record to an explicit bounded snapshot.

    Physical bank capacity (16), 100 WORDs and 100 auxiliary bytes are checked
    here. Native 11C7F0 trusts its bank-count byte and does not impose that cap.
    Key WORDs are opaque values dereferenced from each bank's +2C4 pointer.
    The current byte is raw storage; native compares its signed value.
    """
    if type(record) is not bytes or len(record) != 2 or record[0] != 0x38:
        raise ValueError('Expected exactly one two-byte logical 0x38 record')
    if type(banks) is not tuple or len(banks) > 16:
        raise ValueError('Expected at most 16 explicit banks')
    if not _unsigned(current_bank_byte, 256):
        raise ValueError('Expected raw current-bank byte')
    for bank in banks:
        if (not isinstance(bank, Bank) or
                not _unsigned(bank.key_word, 65536) or
                not _unsigned(bank.state_byte, 256) or
                type(bank.words) is not tuple or len(bank.words) != 100 or
                any(not _unsigned(word, 65536) for word in bank.words) or
                type(bank.auxiliary) is not bytes or len(bank.auxiliary) != 100):
            raise ValueError('Expected bounded raw bank snapshot')

    index, state = record[1] & 31, record[1] >> 5
    if index >= len(banks):
        return Transition(banks, current_bank_byte, -1)
    bank = banks[index]
    if bank.state_byte == 2 and state != 2:
        bank = replace(bank, words=tuple(word & 0x7fff for word in bank.words),
                       auxiliary=bytes(100))
    updated = list(banks)
    updated[index] = replace(bank, state_byte=state)
    returned_index = -1
    if state == 2:
        current_signed = (current_bank_byte if current_bank_byte < 128
                          else current_bank_byte - 256)
        for candidate, other in enumerate(updated):
            if other.key_word == bank.key_word and candidate != current_signed:
                current_bank_byte = candidate
                returned_index = index
                break
    return Transition(tuple(updated), current_bank_byte, returned_index)
