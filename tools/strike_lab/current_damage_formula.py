"""Native received-delta aggregation and actor-scalar application proof.

This recovers arithmetic on supplied results, not attack/defense-to-damage.
Execution stages are explicit; no renderer/formatter call is stubbed or resumed.
"""
import argparse
import hashlib
import json
import struct

from .current_battle_entry import (
    BASE, BATTLE, SP, STACK, RETURN, NativeRun, pinned_image,
    UC_HOOK_MEM_READ, UC_X86_REG_EIP, UC_X86_REG_ESP, UC_X86_REG_EAX,
)
from .recover_combat_rules import IMAGE_SHA256

MANAGER = BATTLE + 0x144938
PACKET = BATTLE + 0xa9e9cb0
SOURCE, TARGET, GATE, OUT = 0x6900000, 0x6902000, 0x6800000, 0x6800004
DIRTY = MANAGER + 0xa89785c
MASK32 = 0xffffffff
RECEIVE_RANGES = (
    (0x114332, 0x1143a1), (0x116ae0, 0x116b19),
    (0x116bb1, 0x116c9c), (0x117142, 0x1171a9),
    (0x1169f0, 0x116a7c), (0x11e5e0, 0x11e62b), (0x11e6e0, 0x11e76a),
    (0x12c520, 0x12c5d3), (0x12ca2d, 0x12ca3a),
    (0x12caba, 0x12cbde), (0x12bfc0, 0x12bfd6),
)
CLAMP_RANGES = ((0x128a70, 0x128abd), (0x128ac0, 0x128b0d))
SLICES = {
    'received_result_accumulator': (0x12caba, 0x12cb8e),
    'selector_jump_targets': (0x12cc98, 0x12ccac),
    'selector_byte_table': (0x12ccac, 0x12ccc1),
    'application_prefix': (0x12b870, 0x12b8de),
    'application_first_after_format': (0x12bb84, 0x12bb98),
    'application_second': (0x12bbda, 0x12bbea),
    'actor_scalar_0_add_clamp': CLAMP_RANGES[0],
    'actor_scalar_1_add_clamp': CLAMP_RANGES[1],
}


def signed(value, bits):
    value &= (1 << bits) - 1
    return value - (1 << bits) if value & (1 << (bits - 1)) else value


def apply_scalar_bits(old, delta, cap):
    """128A70/128AC0: x86 wrapping ADD, JNS, then signed CMP/JLE."""
    for value in (old, delta, cap):
        if type(value) is not int or not 0 <= value <= MASK32:
            raise ValueError('Expected raw DWORD inputs')
    total = (old + delta) & MASK32
    if total & 0x80000000:
        return 0
    return cap if total > signed(cap, 32) else total


def logical_record(delta_word, selector=0, marker=1):
    if (type(delta_word) is not int or not 0 <= delta_word <= 65535 or
            type(selector) is not int or selector not in (0, 1, 2, 3, 4, 5, 7, 8, 9, 20) or
            type(marker) is not int or not 0 <= marker <= 255):
        raise ValueError('Outside qualified 83/0D fixture inputs')
    raw = bytearray(15)
    raw[:4] = bytes((0x83, 13, 0, marker))
    struct.pack_into('<H', raw, 5, 2)  # Target side zero, slot one.
    struct.pack_into('<H', raw, 9, delta_word)
    struct.pack_into('<H', raw, 11, 1)  # Nonzero kind selects accumulation arm.
    raw[13] = selector
    return bytes(raw)


def actor_snapshot(*, scalars=(100, 50, 200, 80), accumulators=(0, 0), poison=0xa5):
    raw = bytearray(bytes((poison,)) * 0x1000)
    raw[0x239] = 1  # Existing action state: native must not reset all accumulators.
    struct.pack_into('<h', raw, 0x1a, 0)
    struct.pack_into('<h', raw, 0x2c4, 0)
    struct.pack_into('<2I', raw, 0xb60, *accumulators)
    struct.pack_into('<4I', raw, 0xde8, *scalars)
    return bytes(raw)


class DamageDataflowProof:
    def __init__(self, image=None):
        self.image = pinned_image() if image is None else image
        if hashlib.sha256(self.image).hexdigest() != IMAGE_SHA256:
            raise ValueError('Pinned current image SHA256 mismatch')

    def receive(self, record, *, source=None, target=None):
        if (type(record) is not bytes or len(record) != 15 or
                record != logical_record(struct.unpack_from('<H', record, 9)[0],
                                         record[13], record[3])):
            raise ValueError('Expected bounded 83/0D source0/target1 logical record')
        source = actor_snapshot() if source is None else source
        target = actor_snapshot() if target is None else target
        if any(type(raw) is not bytes or len(raw) != 0x1000 for raw in (source, target)):
            raise ValueError('Expected complete actor snapshots')
        if source[0x239] == 0 or struct.unpack_from('<h', source, 0x2c4)[0] != 0:
            raise ValueError('This prefix qualifies existing state and accumulator slot zero')
        n = NativeRun(self.image)
        n.put(PACKET, record)
        n.put(MANAGER, b'\xa5' * 0x310)
        n.put(MANAGER + 0x38, bytes(28 * 24))
        n.put32(MANAGER + 0x38, SOURCE)
        n.put32(MANAGER + 0x50, TARGET)
        n.put(SOURCE, source)
        n.put(TARGET, target)
        n.put(BATTLE + 0x51, b'\xff')
        n.put32(BATTLE + 0xa9df6b8, 1)
        for offset in (0xa9e9c6c, 0xa9e9c74, 0xa9ea4c4, 0xa9df6c0):
            n.put32(BATTLE + offset, 0xa5a5a5a5)
        n.put32(GATE, record[3])
        n.put32(OUT, 0xa5a5a5a5)
        n.put32(SP + 0x28, GATE)
        n.put32(SP + 0x2c, OUT)
        n.registers(ebp=PACKET, edi=PACKET, esi=BATTLE, eax=0)
        n.record_reads = []

        def read(vm, access, address, size, value, data):
            if PACKET <= address < PACKET + 0x20:
                if address + size > PACKET + len(record):
                    raise AssertionError('Read beyond logical record')
                n.record_reads.append((vm.reg_read(UC_X86_REG_EIP) - BASE,
                                       address - PACKET, size))

        hook = n.vm.hook_add(UC_HOOK_MEM_READ, read)
        try:
            n.run(0x114332, RECEIVE_RANGES, {0x1143a1}, budget=5000)
        finally:
            n.vm.hook_del(hook)
        return n

    def application_prefix(self, n):
        """Separate original function entry; stop immediately after target lookup."""
        n.put32(SP, RETURN)
        n.put32(SP + 4, SOURCE)
        n.registers(esp=SP, ecx=MANAGER)
        n.visits.clear()
        n.writes.clear()
        n.run(0x12b870, ((0x12b870, 0x12b8de), (0x11e6e0, 0x11e76a)),
              {0x12b8de}, budget=512)
        pointer = n.get32(n.vm.reg_read(UC_X86_REG_ESP) + 0x5c)
        return pointer, n.vm.reg_read(UC_X86_REG_EAX)

    def apply_after_format(self, n, *, pointer, target=TARGET, selected=True):
        """Independent 12BB84 live-ins, not a resumed or faked formatter return.

        The caller prefix above supplies the accumulator pointer and target.
        Formatting/resource setup between the two stages remains unexecuted.
        """
        if pointer != SOURCE + 0xb60 or target != TARGET or type(selected) is not bool:
            raise ValueError('Outside qualified application live-ins')
        n.put32(SP + 0x6c, pointer)
        n.put32(MANAGER + 0x2dc, target if selected else 0)
        n.put32(DIRTY, 0xa5a5a5a5)
        n.registers(esp=SP, esi=MANAGER, edi=target)
        n.visits.clear()
        n.writes.clear()
        n.run(0x12bb84, ((0x12bb84, 0x12bb98), (0x12bbda, 0x12bbea),
                         *CLAMP_RANGES), {0x12bbea}, budget=512)
        return struct.unpack('<4I', n.vm.mem_read(target + 0xde8, 16))

    def direct_scalar(self, channel, old, delta, cap, *, selected=True):
        apply_scalar_bits(old, delta, cap)
        if type(channel) is not int or channel not in (0, 1) or type(selected) is not bool:
            raise ValueError('Expected scalar channel 0/1 and explicit selection')
        n = NativeRun(self.image)
        n.put(TARGET, b'\xa5' * 0x1000)
        n.put32(TARGET + 0xde8 + 4 * channel, old)
        n.put32(TARGET + 0xdf0 + 4 * channel, cap)
        n.put32(MANAGER + 0x2dc, TARGET if selected else 0)
        n.put32(DIRTY, 0xa5a5a5a5)
        n.put(SP, struct.pack('<3I', RETURN, TARGET, delta))
        n.registers(esp=SP, ecx=MANAGER)
        n.data_reads = []

        def read(vm, access, address, size, value, data):
            if not STACK <= address < STACK + 0x8000:
                n.data_reads.append((vm.reg_read(UC_X86_REG_EIP) - BASE, address, size))

        hook = n.vm.hook_add(UC_HOOK_MEM_READ, read)
        try:
            n.run(CLAMP_RANGES[channel][0], CLAMP_RANGES, set(), budget=128)
        finally:
            n.vm.hook_del(hook)
        return n


def evidence():
    proof = DamageDataflowProof()
    demonstrations = []
    for word, selector in ((0xffe2, 0), (0xffe2, 9), (7, 20), (7, 7)):
        n = proof.receive(logical_record(word, selector),
                          source=actor_snapshot(accumulators=(10, 20)))
        accumulated = list(struct.unpack('<2I', n.vm.mem_read(SOURCE + 0xb60, 8)))
        record_reads = [{'rva': hex(rva), 'offset': offset, 'bytes': size}
                        for rva, offset, size in n.record_reads]
        pointer, target = proof.application_prefix(n)
        result = proof.apply_after_format(n, pointer=pointer, target=target)
        demonstrations.append({'received_word': word, 'selector': selector,
            'before_accumulators': [10, 20], 'after_accumulators': accumulated,
            'record_reads': record_reads, 'prefix_accumulator_offset': pointer - SOURCE,
            'prefix_target_matches': target == TARGET,
            'actor_before_de8_dec_df0_df4': [100, 50, 200, 80],
            'actor_after_de8_dec_df0_df4': list(result),
            'independent_stages': ['114332..1143A1', '12B870..12B8DE', '12BB84..12BBEA']})
    return {'image_sha256': IMAGE_SHA256, 'image_base': '0x400000',
        'slices': {name: {'rva_start': hex(lo), 'rva_end_exclusive': hex(hi),
                          'sha256': hashlib.sha256(proof.image[lo:hi]).hexdigest()}
                   for name, (lo, hi) in SLICES.items()},
        'computational_result': 'Received signed-WORD accumulation or replacement, '
            'then wrapping DWORD addition with sign-floor and signed-cap comparison.',
        'authority': 'Client result application. Attack/defense transformation and '
            'skill coefficient are not established by these executed paths.',
        'demonstrations': demonstrations}


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    print(json.dumps(evidence(), ensure_ascii=True, sort_keys=True, indent=2))


if __name__ == '__main__':
    main()
