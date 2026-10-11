"""Pinned S2C 86/0,1 scalar copying and display arithmetic, never damage production.

Research bounds: positions 0..27, explicit entity/display snapshots, x87 extended
precision, nonzero signed divisor whenever a display channel is enabled.
"""
from dataclasses import dataclass, replace
import struct

IMAGE_SHA256 = '149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
runtime_mutation_enabled = False


def _integer(value, lo, hi):
    return type(value) is int and lo <= value <= hi


def _pair(values, lo, hi):
    return (type(values) is tuple and len(values) == 2 and
            all(_integer(value, lo, hi) for value in values))


@dataclass(frozen=True)
class Display:
    handles: tuple[int, int]  # Signed WORDs at display record +A79C/+A79E.
    width: int               # Signed WORD +A7A4.
    height: int              # Signed WORD +A7A6, read only by channel 0.
    divisors: tuple[int, int]    # Raw DWORDs +A7A8/+A7AC.
    numerators: tuple[int, int]  # Raw DWORDs +A7B0/+A7B4.

    def __post_init__(self):
        if (not _pair(self.handles, -32768, 32767) or
                not _integer(self.width, -32768, 32767) or
                not _integer(self.height, -32768, 32767) or
                not _pair(self.divisors, 0, 0xffffffff) or
                not _pair(self.numerators, 0, 0xffffffff)):
            raise ValueError('Expected exact raw display field widths')


@dataclass(frozen=True)
class Draw:
    channel: int
    quotient: int  # Truncated signed 64-bit conversion, not damage.

    @property
    def extent_bits(self):
        return self.quotient & 0xffffffff


def display_update(display, supplied, *, clamp):
    """108FC0 or 108F50, then 108E70 to the first 01BDC0 call.

    With both handles negative the original renderer returns without a draw.
    Clamp comparisons are unsigned; the subsequent divisor load is signed.
    """
    if not isinstance(display, Display) or not _pair(supplied, 0, 0xffffffff):
        raise ValueError('Expected display state and two raw DWORDs')
    if type(clamp) is not bool:
        raise ValueError('Expected explicit clamp/set-divisors choice')
    if clamp:
        display = replace(display, numerators=tuple(
            min(value, limit) for value, limit in zip(supplied, display.divisors)))
    else:
        display = replace(display, divisors=supplied)
    for channel, handle in enumerate(display.handles):
        if handle < 0:
            continue
        divisor = display.divisors[channel]
        divisor = divisor if divisor < 0x80000000 else divisor - 0x100000000
        if divisor == 0:
            raise ValueError('Enabled zero-divisor rendering is outside this model')
        product = display.numerators[channel] * display.width
        quotient = abs(product) // abs(divisor)
        if (product < 0) != (divisor < 0):
            quotient = -quotient
        return display, Draw(channel, quotient)
    return display, None


@dataclass(frozen=True)
class State:
    local_slot: int
    entity: bytes | None
    display: Display

    def __post_init__(self):
        if (not _integer(self.local_slot, 0, 13) or
                not isinstance(self.display, Display) or
                (self.entity is not None and
                 (type(self.entity) is not bytes or len(self.entity) != 4096))):
            raise ValueError('Expected local slot, explicit entity snapshot and display')


@dataclass(frozen=True)
class Result:
    entity: bytes | None
    display: Display
    next_consumer: int | None
    draw: Draw | None = None
    local_scalars: tuple[int, int, int, int] | None = None


def consume(record, state):
    """114332 -> 117230/1173A0 -> setters; stop at a real unqualified call.

    On side 1, kind 0 stops at 12D8C0, while kind 1 returns without lookup.
    Rendering stops at 01BDC0 before any invented successful renderer return.
    """
    if (type(record) is not bytes or len(record) != 17 or record[0] != 0x86 or
            record[1] not in (0, 1) or record[2] >= 28 or not isinstance(state, State)):
        raise ValueError('Expected one qualified logical 86/0,1 record and state')
    kind, position = record[1:3]
    entity, display = state.entity, state.display
    if position >= 14:
        return Result(entity, display, 0x12d8c0 if kind == 0 else None)
    if entity is None:
        return Result(None, display, None)
    output = bytearray(entity)
    value5, value9 = struct.unpack_from('<II', record, 5)
    struct.pack_into('<I', output, 0xde8 + kind * 4, value9)
    struct.pack_into('<I', output, 0xdf0 + kind * 4, value5)
    entity = bytes(output)
    scalars = struct.unpack_from('<4I', entity, 0xde8)
    handle = struct.unpack_from('<h', entity, 0x1d8)[0]
    if 0 <= handle < 0x1000:
        display, draw = display_update(display, scalars[2:], clamp=False)
        if draw is not None:
            return Result(entity, display, 0x1bdc0, draw)
        display, draw = display_update(display, scalars[:2], clamp=True)
        if draw is not None:
            return Result(entity, display, 0x1bdc0, draw)
    if position == state.local_slot and struct.unpack_from('<h', entity, 0x1a)[0] >= 0:
        return Result(entity, display, 0xe71e0, local_scalars=scalars)
    return Result(entity, display, None)
