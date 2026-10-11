"""Bounded current-client control transitions; not Session authorization.

All addresses are RVAs in the pinned mapped image, base 0x400000.
Models describe instruction slices with explicit state, not a live turn loop.
"""
from dataclasses import dataclass, replace
import hashlib
from pathlib import Path

IMAGE_SHA256 = '149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
BASE = 0x400000
ROOT = Path(__file__).resolve().parents[2]
IMAGE = ROOT / 'artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin'
runtime_mutation_enabled = False

# Explicit boundaries, including the calls that remain outside native slices.
EVIDENCE_RANGES = (
    (0x118e50, 0x118ee4), (0x118f9d, 0x119075),
    (0x11913d, 0x1192d9), (0x11b8c0, 0x11b941),
    (0x132e0, 0x133d7), (0x124d0, 0x12514),
    (0x114332, 0x114358), (0x114464, 0x11447a),
    (0x1144be, 0x1144c8), (0x1175b2, 0x1175e2),
    (0x11776e, 0x1177b8), (0x115670, 0x115699),
    (0x115740, 0x115767), (0x112230, 0x11224d),
    (0x115a59, 0x115add), (0x115af7, 0x115aff),
    (0x114582, 0x1145c0), (0x118e20, 0x118e3a),
    (0x1159f8, 0x115a40), (0x11583c, 0x115855),
)


def load_image(path=IMAGE):
    image = Path(path).read_bytes()
    if hashlib.sha256(image).hexdigest() != IMAGE_SHA256:
        raise ValueError('Pinned current image changed; re-audit required')
    return image


def _uint(value, bits=32):
    if type(value) is not int or not 0 <= value < 1 << bits:
        raise ValueError(f'Expected raw unsigned {bits}-bit storage')


@dataclass(frozen=True)
class Controls:
    first: int
    second: int
    waiting: int
    first_actor: int = 0xff
    second_actor: int = 0xff

    def __post_init__(self):
        for value in (self.first, self.second, self.waiting):
            _uint(value)
        for value in (self.first_actor, self.second_actor):
            _uint(value, 8)


def grant_controls(record, state):
    """1175B2..1175E2 and 11776E..117795 only, excluding helper effects.

Absent bits preserve previous controls/actors. The producer does not directly
clear +A9E9C34; conditional helpers 115670/115740 can reach 1121F0.
"""
    if (type(record) is not bytes or len(record) != 17 or
            record[:2] != b'\x86\x05' or not isinstance(state, Controls)):
        raise ValueError('Expected current 86/5 logical record and explicit controls')
    return replace(state,
        first=1 if record[3] & 1 else state.first,
        second=1 if record[3] & 2 else state.second,
        first_actor=record[4] & 15 if record[3] & 1 else state.first_actor,
        second_actor=record[4] >> 4 if record[3] & 2 else state.second_actor)


def consume_controls(state):
    """119200..119252, after the two unexecuted cleanup calls return.

This occurs even after a disconnected/empty/unsupported-kind no-queue path.
The first control has priority; waiting is only assigned when the last clears.
"""
    if not isinstance(state, Controls):
        raise ValueError('Expected explicit controls')
    if state.first:
        return replace(state, first=0, waiting=state.waiting if state.second else 1)
    if state.second:
        return replace(state, second=0, waiting=1)
    return state


def continuation_actions(count):
    """1191B2..1191C6: record sequence flags, not a next-turn signal."""
    if type(count) is not int or not 1 <= count <= 14:
        raise ValueError('Expected bounded nonempty kind-0 target list')
    return (0x83,) * (count - 1) + (0x03,)


def disassembly(image):
    """Reproduce only the bounded current instruction evidence."""
    if hashlib.sha256(image).hexdigest() != IMAGE_SHA256:
        raise ValueError('Pinned current image changed; re-audit required')
    from capstone import Cs, CS_ARCH_X86, CS_MODE_32
    decoder = Cs(CS_ARCH_X86, CS_MODE_32)
    for lo, hi in EVIDENCE_RANGES:
        yield f'[{lo:08X}, {hi:08X})'
        for insn in decoder.disasm(image[lo:hi], BASE + lo):
            yield f'{insn.address - BASE:08X} {insn.mnemonic} {insn.op_str}'


if __name__ == '__main__':
    print(f'SHA256 {IMAGE_SHA256}; BASE {BASE:X}; mutation disabled')
    print('\n'.join(disassembly(load_image())))
