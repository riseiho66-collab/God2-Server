"""Bounded native critical-candidate investigation; not a critical formula.

Executes unchanged mapped-image instructions in one reusable NativeRun. The RNG
entry is explicitly AFTER the OS TLS getter; action entries take a received
payload and existing actors. No unknown call returns are manufactured.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import struct

from tools.strike_lab.current_battle_entry import (
    BASE, BATTLE, SP, STACK, NativeRun, pinned_image, IMAGE, IMAGE_SHA256,
    UC_HOOK_MEM_READ, UC_X86_REG_EIP, UC_X86_REG_ESP,
)

ROOT = Path(__file__).resolve().parents[2]
ACTOR, TARGET, PAYLOAD, TLS = 0x6900000, 0x6902000, 0x6800000, 0x6801000
runtime_mutation_enabled = False
FORMAT_STOPS = {0x12b401, 0x12b421, 0x12b43a, 0x12b453, 0x12b49c}
RANGES = [(0x147d84, 0x147da1), (0x12a8a2, 0x12a8c6),
          (0x11e6e0, 0x11e76a), (0x1224a0, 0x1224b6),
          (0x12b060, 0x12b4a1), (0x12c520, 0x12c636),
          (0x12c92c, 0x12c972), (0x12ca2d, 0x12cb6b),
          (0x12a8d0, 0x12ab9a)]
SLICES = {
    'rng_core': (0x147d84, 0x147da1),
    'rng_caller': (0x12a7f0, 0x12a8ce),
    'action_producer': (0x12c520, 0x12cc39),
    'action_tables': (0x12cc3c, 0x12ccc1),
    'effect_consumer': (0x12b060, 0x12b847),
    'movement_producer': (0x122b50, 0x122bda),
    'movement_consumer': (0x123025, 0x1230d0),
}
TYPE_OPERATIONS = {**dict.fromkeys(range(6), 'add_a'), 7: 'none', 8: 'none',
                   9: 'add_b', 20: 'replace_a'}


def signed16(value):
    return value if value < 0x8000 else value - 0x10000


def rng_reference(seed):
    next_seed = (seed * 214013 + 2531011) & 0xffffffff
    return next_seed, (next_seed >> 16) & 0x7fff


def word(value):
    if type(value) is not int or not 0 <= value <= 0xffff:
        raise ValueError('Expected unsigned WORD bits')
    return value


class Probe:
    def __init__(self):
        self.image = pinned_image()
        self.n = NativeRun(self.image)

    def reset(self, kind, poison=0, counter=0, a=0, b=0):
        n = self.n
        n.put(STACK, bytes(0x8000))
        n.put(BATTLE, bytes(0x400))
        n.put(BATTLE + 0xa7fbc5c, bytes(0x150))
        for address in (ACTOR, TARGET):
            snapshot = bytearray([poison] * 0x1000)
            struct.pack_into('<H', snapshot, 0x1a, 1)
            snapshot[0x1e9] = kind
            snapshot[0x239] = 1  # Existing collection, not the zero/reset branch.
            snapshot[0x277] = 0
            snapshot[0x234] = 0 if address == ACTOR else 0x80
            struct.pack_into('<I', snapshot, 0xec4, 0)
            struct.pack_into('<H', snapshot, 0x2c4, counter)
            struct.pack_into('<II', snapshot, 0xb60 + counter * 8, a, b)
            n.put(address, bytes(snapshot))
        n.put32(BATTLE + 0x38, ACTOR)
        n.put32(BATTLE + 0x38 + 14 * 24, TARGET)
        n.put(TLS, bytes(0x20))
        n.put(PAYLOAD, bytes(14))
        n.registers(eax=0, ebx=0, ecx=0, edx=0, esi=0, edi=0, ebp=0, esp=SP)
        n.visits.clear()
        n.writes.clear()

    def execute(self, start, stops):
        n, reads = self.n, []

        def read(vm, access, address, size, value, _):
            if PAYLOAD <= address < PAYLOAD + 0x1000:
                if address + size > PAYLOAD + 14:
                    raise AssertionError('Read outside explicit 14-byte payload')
            if not STACK <= address < STACK + 0x8000:
                reads.append((vm.reg_read(UC_X86_REG_EIP) - BASE, address, size))

        hook = n.vm.hook_add(UC_HOOK_MEM_READ, read)
        try:
            n.run(start, RANGES, stops, budget=2000)
        finally:
            n.vm.hook_del(hook)
        writes = [w for w in n.writes if not STACK <= w[1] < STACK + 0x8000]
        for _, address, size, _ in writes:
            if not any(lo <= address and address + size <= hi for lo, hi in
                       [(ACTOR, ACTOR + 0x1000), (TARGET, TARGET + 0x1000),
                        (BATTLE, BATTLE + 0x400), (TLS, TLS + 0x20)]):
                raise AssertionError(f'Unexpected native write {address:X}')
        return {'start_rva': start, 'stop_rva': n.stop,
                'instruction_count': len(n.visits), 'reads': reads, 'writes': writes,
                'trace_sha256': hashlib.sha256(struct.pack(
                    '<' + 'I' * len(n.visits), *n.visits)).hexdigest()}

    def format_result(self, result):
        n = self.n
        sp = n.vm.reg_read(UC_X86_REG_ESP)
        fmt = n.get32(sp + 4)
        offset = fmt - BASE
        if not 0 <= offset < len(self.image):
            raise AssertionError('Non-image format pointer')
        end = self.image.index(b'\0', offset)
        result.update(format_rva=offset, format_hex=self.image[offset:end].hex(),
                      format_text=self.image[offset:end].decode('cp950'),
                      stored_words=list(struct.unpack('<HH', n.vm.mem_read(ACTOR + 0x286, 4))))
        if result['stop_rva'] in (0x12b401, 0x12b49c):
            arg_offset = 12 if result['stop_rva'] == 0x12b401 else 8
            result['numeric_argument'] = struct.unpack('<i', n.vm.mem_read(sp + arg_offset, 4))[0]
        return result

    def rng_to_action(self, seed, poison=0):
        if type(seed) is not int or not 0 <= seed <= 0xffffffff:
            raise ValueError('Expected explicit uint32 TLS seed')
        self.reset(1, poison)
        n = self.n
        n.put32(TLS + 0x14, seed)
        # At RNG core entry, the actual caller has already pushed effect22,
        # type0, value2=0. The return address is its unchanged continuation.
        n.put(SP, struct.pack('<4I', BASE + 0x12a8a2, 0, 0, 0x22))
        n.put32(SP + 0x18, 0)  # target slot
        n.put32(SP + 0x1c, 1)  # target side
        n.registers(eax=TLS, esi=BATTLE, ebx=0)
        result = self.execute(0x147d84, FORMAT_STOPS)
        result.update(seed=seed, poison=poison, next_seed=n.get32(TLS + 0x14))
        return self.format_result(result)

    def action(self, kind, value, type_byte, *, second=0, counter=0,
               a=0, b=0, poison=0):
        if kind not in (1, 4, 13) or not 0 <= type_byte <= 255:
            raise ValueError('Qualified action kinds 1/4/13 and byte type only')
        if not 0 <= counter <= 3:
            raise ValueError('Counter fixture is bounded to 0..3')
        word(value)
        word(second)
        self.reset(kind, poison, counter, a, b)
        n = self.n
        payload = bytearray(14)
        payload[0], payload[2] = kind, 17
        struct.pack_into('<HH', payload, 8, value, second)
        if kind == 1:
            payload[10] = type_byte
        else:
            payload[12] = type_byte
        if kind == 13:
            struct.pack_into('<H', payload, 10, 2)
        n.put(PAYLOAD, bytes(payload))
        n.put(SP, struct.pack('<6I', 0x7fff0000, PAYLOAD, 0, 0, 1, 0))
        n.registers(ecx=BATTLE)
        result = self.execute(0x12c520, FORMAT_STOPS | {0x12cb54, 0x12cb6b})
        result.update(kind=kind, value=value, type_byte=type_byte, second=second,
                      counter=counter, a=a, b=b, poison=poison, payload_hex=payload.hex())
        if kind != 13:
            return self.format_result(result)
        result.update(next_counter=struct.unpack('<H', n.vm.mem_read(ACTOR + 0x2c4, 2))[0],
                      output=list(struct.unpack('<II', n.vm.mem_read(ACTOR + 0xb60 + 8 * counter, 8))))
        return result


def verify_rng(row):
    next_seed, rand15 = rng_reference(row['seed'])
    assert row['next_seed'] == next_seed, 'RNG recurrence/state mismatch'
    assert row['stop_rva'] == 0x12b49c, 'Unexpected RNG consumer'
    assert row['format_rva'] == 0x19d968, 'RNG does not reach HP numeric argument'
    assert row['numeric_argument'] == rand15 % 100, 'Remainder/argument mismatch'
    assert row['stored_words'] == [rand15 % 100, 0], 'Action word producer mismatch'
    assert (0x147d84, TLS + 0x14, 4) in row['reads'], 'Missing native seed read'
    assert any(w[:3] == (0x147d93, TLS + 0x14, 4) for w in row['writes'])


def verify_accumulation(row):
    op = TYPE_OPERATIONS.get(row['type_byte'], 'diagnostic')
    expected = [row['a'], row['b']]
    delta = signed16(row['value'])
    if op == 'add_a':
        expected[0] = (expected[0] + delta) & 0xffffffff
    elif op == 'add_b':
        expected[1] = (expected[1] + delta) & 0xffffffff
    elif op == 'replace_a':
        expected[0] = delta & 0xffffffff
    assert row['output'] == expected, 'Signed addition/replacement mismatch'
    assert row['next_counter'] == row['counter'] + 1, 'Index update mismatch'
    assert row['stop_rva'] == (0x12cb54 if op == 'diagnostic' else 0x12cb6b)
    if op not in ('none', 'diagnostic'):
        producer = {'add_a': 0x12cb2d, 'add_b': 0x12cb3a, 'replace_a': 0x12cb47}[op]
        assert (producer, PAYLOAD + 8, 2) in row['reads'], 'Missing received WORD source'


def build_report():
    p = Probe()
    # Inverting the odd LCG multiplier selects exact output-boundary states;
    # these are explicit counterfactual seeds, never claimed live observations.
    inverse = pow(214013, -1, 1 << 32)
    seeds = {0, 1, 0x7fffffff, 0x80000000, 0xffffffff}
    for value in (0, 1, 49, 50, 98, 99, 100, 101, 199, 200, 32767):
        for low in (0, 0xffff):
            for high in (0, 0x80000000):
                seeds.add((((value << 16) | low | high) - 2531011) * inverse & 0xffffffff)
    rng = [p.rng_to_action(seed, poison) for seed in sorted(seeds) for poison in (0, 0xa5)]
    for row in rng:
        verify_rng(row)
    arithmetic = [p.action(13, value, selector, counter=index, a=a, b=b)
                  for selector in range(21)
                  for index, (value, a, b) in enumerate(((1, 0xffffffff, 0x7fffffff),
                                                       (0xffff, 0, 0x80000000),
                                                       (0x8000, 32767, 65535),
                                                       (0x7fff, 0x7fffffff, 0xffffffff)))]
    for row in arithmetic:
        verify_accumulation(row)
    received = [p.action(kind, value, selector, second=0x8123, poison=poison)
                for kind in (1, 4) for value in (1, 0x7fff, 0x8000, 0xffff)
                for selector in (0, 1, 3, 5, 6, 7, 8, 9, 20, 128, 255)
                for poison in (0, 0xa5)]
    for row in received:
        expected_second = 0 if row['kind'] == 1 else row['second']
        assert row['stored_words'] == [row['value'], expected_second]
        if 'numeric_argument' in row:
            assert row['numeric_argument'] == signed16(row['value'])
    image = p.image
    return {
        'schema': 1, 'critical_formula_status': 'UNPROVED',
        'runtime_mutation_enabled': False,
        'scope': 'Original instruction islands with explicit synthetic live-ins; no live gameplay claim',
        'image': {'path': IMAGE.relative_to(ROOT).as_posix(), 'sha256': IMAGE_SHA256,
                  'size': len(image), 'base': BASE, 'file_offset_equals_rva': True},
        'slices': {name: {'start_rva': lo, 'end_exclusive_rva': hi,
                          'sha256': hashlib.sha256(image[lo:hi]).hexdigest()}
                   for name, (lo, hi) in SLICES.items()},
        'proven': {
            'rng': 'u32(seed*214013+2531011); (next>>16)&32767; signed idiv100 remainder -> action value1',
            'result_arithmetic': 'received signed WORD added modulo 2^32, replaced, or ignored by exact type dispatch',
            'type_operations': {str(i): TYPE_OPERATIONS.get(i, 'diagnostic') for i in range(21)},
            'received_values': 'Kinds1/4 preserve WORD bits; numeric formatting sign-extends, never doubles in tested prefixes',
        },
        'unproved': ['critical-stat identity and producer', 'trigger threshold/comparison',
                     'critical bit meaning', 'critical multiplier and operation order',
                     'critical rounding/clamps', 'binding described skill 2x to native arithmetic',
                     'authoritative server rule or complete client absence'],
        'boundaries': ['RNG starts at147D84 after unexecuted TLS getter14E001; TLS pointer supplied',
                       'Action starts at12C520 with14-byte payload and existing actor table; no socket/packet dispatch',
                       'Formatter147AF7 and diagnostic402C70 are not executed or stubbed',
                       'No earlier action/actor creation, reset branch, or later rendering is claimed'],
        'counts': {'rng_counterfactuals': len(rng), 'arithmetic_counterfactuals': len(arithmetic),
                   'received_counterfactuals': len(received), 'total': len(rng) + len(arithmetic) + len(received),
                   'arithmetic_stops': dict(sorted(Counter(f'{r["stop_rva"]:06X}' for r in arithmetic).items()))},
        'rng_cases': rng, 'arithmetic_cases': arithmetic, 'received_cases': received,
    }


def serialize(report):
    return json.dumps(report, ensure_ascii=True, sort_keys=True, indent=2) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = build_report()
    args.output.write_text(serialize(report), encoding='utf-8', newline='\n')
    print(json.dumps(report['counts'], sort_keys=True))
    print('Critical chance/multiplier: UNPROVED')


if __name__ == '__main__':
    main()
