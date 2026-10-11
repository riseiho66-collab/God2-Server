"""Pinned current-client target setup, not skill damage or coefficients.

RVA 11EE90 and its complete 11EDA0 -> 11ED00 -> 11ECA0/11EC70 path.
Only explicit two-side, fourteen-slot snapshots and byte-sized source fields
are admitted. These checks are this research model's bounds, not native guards.
"""
from dataclasses import dataclass
import struct

from .current_skill_identity import IMAGE_SHA256, RECORD_SIZE

# DWORDs in the pinned image, checked independently by the native tests.
ROW_MASKS = (0x3000, 0x0e00, 0x01e0, 0x001f,
             0x001f, 0x01e0, 0x0e00, 0x3000)  # RVA 171BF8
ROW_SLOTS = (12, 9, 5, 0, 0, 5, 9, 12)  # RVA 171C18
MODE_VALUES = (0, 1, 2, 3, 4, 1, 1, 1, 1, 1, 1, 1, 1, 2, 7, 1, 3, 2)
MODE_ROWS = {
    6: ROW_MASKS,  # RVA 171C38
    7: (0, 0x400, 0xc0, 0xe, 0xe, 0xc0, 0x400, 0),  # RVA 171C58
    15: (0x3000, 0xe00, 0x1e0, 0, 0, 0x1e0, 0xe00, 0x3000),
}


def _uint(value, bits):
    return type(value) is int and 0 <= value < 1 << bits


def _masks(value):
    if (type(value) is not tuple or len(value) != 2 or
            any(not _uint(mask, 32) for mask in value)):
        raise ValueError('Expected two raw DWORD masks')


@dataclass(frozen=True)
class Fields:
    identifier: int
    kind: int
    word_3e: int
    reach_44: int
    mode_45: int

    def __post_init__(self):
        if (not _uint(self.word_3e, 16) or
                any(not _uint(value, 8) for value in
                    (self.identifier, self.kind, self.reach_44, self.mode_45))):
            raise ValueError('Expected raw definition field widths')

    @classmethod
    def from_record(cls, raw):
        if type(raw) is not bytes or len(raw) != RECORD_SIZE:
            raise ValueError('Expected one complete current cbspec2 record')
        return cls(raw[0], raw[1], struct.unpack_from('<H', raw, 0x3e)[0],
                   raw[0x44], raw[0x45])

    @property
    def passes_kind_gate(self):
        """115571..11557D only; does not establish complete cast eligibility."""
        return self.kind != 2 or self.word_3e == 0x0ff5


@dataclass(frozen=True)
class TargetState:
    masks: tuple[int, int]
    saved_masks: tuple[int, int]
    # None is a null type-0 pointer; otherwise signed WORD at pointee +1A.
    entity_words: tuple[int | None, ...]

    def __post_init__(self):
        _masks(self.masks)
        _masks(self.saved_masks)
        if (type(self.entity_words) is not tuple or len(self.entity_words) != 28 or
                any(word is not None and (type(word) is not int or
                    not -32768 <= word <= 32767) for word in self.entity_words)):
            raise ValueError('Expected 28 explicit null/signed-WORD entity states')


@dataclass(frozen=True)
class MaskSetup:
    masks: tuple[int, int]
    saved_masks: tuple[int, int]
    stored_mode: int


def row_index(side, slot):
    """11ECA0, restricted to the two physical sides and fourteen slots."""
    if not _uint(side, 1) or type(slot) is not int or not 0 <= slot < 14:
        raise ValueError('Expected side 0..1 and slot 0..13')
    return next(row for row in range(side * 4, side * 4 + 4)
                if ROW_MASKS[row] & (1 << slot))


def row_distance(side_a, slot_a, side_b, slot_b, masks):
    """11ED00: absolute row delta minus empty strictly intermediate rows.

    Endpoint occupancy is not checked. The result is not damage or a multiplier.
    """
    _masks(masks)
    a, b = sorted((row_index(side_a, slot_a), row_index(side_b, slot_b)))
    return b - a - sum(not (masks[row // 4] & ROW_MASKS[row])
                       for row in range(a + 1, b))


def _reachable(actor, reach, masks):
    # 11EDA0 computes a lower row, scans the far endpoint, then intersects.
    lower = max(row_index(0, actor) - reach, 0)
    upper = 7
    while upper >= lower and row_distance(
            0, actor, upper // 4, ROW_SLOTS[upper], masks) > reach:
        upper -= 1
    result = [0, 0]
    for row in range(lower, upper + 1):
        result[row // 4] |= ROW_MASKS[row]
    return tuple(result[side] & masks[side] for side in range(2))


def target_masks(fields, actor, state):
    """11EE90 including all byte-mode dispatch arms (invalid modes clear output).

    This directly models the helper, even for definitions the caller gate would
    divert. Callers must consult passes_kind_gate separately. Mode zero is not
    valid for the subsequent 11EAD0 helper.
    """
    if not isinstance(fields, Fields) or not isinstance(state, TargetState):
        raise ValueError('Expected explicit fields and target state')
    row = row_index(0, actor)
    masks = list(state.masks)
    if fields.kind == 3 and 8 <= fields.identifier <= 10:
        for index, word in enumerate(state.entity_words):
            if word is not None and word >= 0:
                masks[index // 14] |= 1 << (index % 14)
    masks = tuple(masks)
    mode, reach = fields.mode_45, fields.reach_44
    result = [0, 0]
    saved = state.saved_masks
    if mode in (1, 2, 3, 4, 5, 13, 14, 16):
        result = list(_reachable(actor, reach, masks))
    elif mode in MODE_ROWS:
        rows = MODE_ROWS[mode]
        result[0] = rows[row]
        distance = row_distance(0, actor, 0, 12, masks)
        if row and distance <= reach:
            for index in range(row):
                result[0] |= rows[index]
        elif row >= 2 and distance > 0:
            result[0] |= rows[row - 1]
        upper = 7
        while upper > row and row_distance(
                0, actor, upper // 4, ROW_SLOTS[upper], masks) > reach:
            upper -= 1
        for index in range(row + 1, upper + 1):
            result[index // 4] |= rows[index]
    elif mode in (8, 9, 10):
        slot, mask = (0, 0x1f) if mode == 8 else (4, 0x400)
        for side in range(2):
            if row_distance(0, actor, side, slot, masks) <= reach:
                result[side] = mask
    elif mode == 11:
        result[0] = 1 << actor
    elif mode == 12:
        result[0] = _reachable(actor, reach, masks)[0]
    elif mode == 17:
        # Original also calls 11EDA0; its output is then overwritten.
        result[0] = 1 << actor
        saved = state.masks
    return MaskSetup(tuple(result), saved, mode)


def setup_parameters(mode):
    """11EAD0 return DWORD and out DWORD; no inferred gameplay names."""
    if type(mode) is not int or not 1 <= mode <= 17:
        raise ValueError('Outside native nondiagnostic mode range 1..17')
    return MODE_VALUES[mode], int(mode not in (13, 14, 16))
