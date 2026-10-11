"""Directed original-native evasion binding and nearby RNG dataflow.

This proves supplied-result consumption and a numeric-display RNG path, not
an accuracy/evasion probability formula. No original callee is substituted.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys
import time

from .recover_combat_rules import IMAGE, IMAGE_SHA256, read_pinned

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'artifacts/tooling/crypto-oracle-python'))
from unicorn import (Uc, UC_ARCH_X86, UC_MODE_32, UC_PROT_READ, UC_PROT_EXEC,
                     UC_HOOK_CODE, UC_HOOK_MEM_READ, UC_HOOK_MEM_WRITE)
from unicorn import x86_const as reg

BASE, STACK, SP, RETURN = 0x400000, 0x3000000, 0x3008000, 0x300f000
BATTLE, ACTOR, TARGET, INPUT, THREAD = 0x5000000, 0x6000000, 0x6001000, 0x6100000, 0x6200000
CONTEXT = BATTLE + 0x144938
RECORD = BATTLE + 0xa9e9cb0
CONTROL = STACK + 0xe000
RANGES = (
    (0x1252, 0x1258), (0x114332, 0x1143a1), (0x116ae0, 0x116b02),
    (0x116bb1, 0x116cb2), (0x117152, 0x117188), (0x1169f0, 0x116a7c),
    (0x11e5e0, 0x11e62b), (0x11e6e0, 0x11e76a),
    (0x12c520, 0x12c636), (0x12a8d0, 0x12a9cf),
    (0x12b060, 0x12b248), (0x12b32c, 0x12b4a4),
    (0x1224a0, 0x1224b6), (0x147d7f, 0x147da1),
    (0x12a89d, 0x12a8c6), (0x12c000, 0x12c0b3), (0x12c0c0, 0x12c2b3),
)
SLICES = (
    ('action_queue_dispatch', 0x114332, 0x1143a1),
    ('incoming_action_parser', 0x116bb1, 0x116cad),
    ('incoming_action_forward', 0x117152, 0x117188),
    ('action_record_consumer', 0x12c520, 0x12c636),
    ('action_state_setup', 0x12a8d0, 0x12a9cf),
    ('evasion_text_decision', 0x12b3c2, 0x12b4a4),
    ('outcome_action_map', 0x171600, 0x17160d),
    ('secondary_action_map', 0x171610, 0x171653),
    ('outcome_state_consumer', 0x12c0c0, 0x12c2b3),
    ('rng_producer', 0x12a7f0, 0x12a8ce),
    ('crt_rng', 0x147d7f, 0x147da1),
    ('evasion_label', 0x19ce48, 0x19ce4d),
    ('numeric_format', 0x19d968, 0x19d96f),
)


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def fixture(outcome=8, amount=123, secondary=0):
    if not (type(outcome) is int and 0 <= outcome <= 255
            and type(amount) is int and -32768 <= amount <= 32767
            and type(secondary) is int and 0 <= secondary <= 255):
        raise ValueError('Expected byte outcome/secondary and signed WORD amount')
    record = bytearray(15)
    record[0:4] = bytes((0x83, 1, 0, 1))
    struct.pack_into('<HH', record, 5, 0, 1)  # Side-1 slot-0 target mask.
    struct.pack_into('<h', record, 9, amount)
    record[11], record[12] = outcome, secondary
    return bytes(record)


class NativeHit:
    def __init__(self, image):
        require(hashlib.sha256(image).hexdigest() == IMAGE_SHA256, 'Pinned image mismatch')
        self.image = image
        self.vm = Uc(UC_ARCH_X86, UC_MODE_32)
        self.vm.mem_map(BASE, (len(image) + 4095) & ~4095, UC_PROT_READ | UC_PROT_EXEC)
        self.vm.mem_write(BASE, image)
        self.pages = sorted({BATTLE, CONTEXT & ~4095, RECORD & ~4095,
            (BATTLE + 0xa9df6b8) & ~4095, (CONTEXT + 0xa7fbccc) & ~4095,
            ACTOR, TARGET, INPUT, THREAD})
        self.vm.mem_map(STACK, 0x10000)
        for page in self.pages:
            self.vm.mem_map(page, 4096)
        self.stops, self.trace, self.reads, self.writes = set(), [], [], []
        self.calls = []
        self.vm.hook_add(UC_HOOK_CODE, self._code)
        self.vm.hook_add(UC_HOOK_MEM_READ | UC_HOOK_MEM_WRITE, self._memory)

    def get(self, name):
        return self.vm.reg_read(getattr(reg, 'UC_X86_REG_' + name))

    def set(self, name, value):
        self.vm.reg_write(getattr(reg, 'UC_X86_REG_' + name), value)

    def write(self, address, fmt, *values):
        self.vm.mem_write(address, struct.pack(fmt, *values))

    def read(self, address, fmt):
        return struct.unpack(fmt, self.vm.mem_read(address, struct.calcsize(fmt)))

    def _code(self, vm, address, size, _):
        rva = address - BASE
        if address == RETURN or rva in self.stops:
            vm.emu_stop()
            return
        require(any(lo <= rva and rva + size <= hi for lo, hi in RANGES),
                f'Outside qualified instructions: {rva:06X}')
        self.trace.append(rva)
        if rva in (0x12b060, 0x12c520, 0x12c0c0):
            count = 8 if rva == 0x12b060 else 5
            self.calls.append(dict(rva=rva, arguments=list(self.read(self.get('ESP') + 4,
                                                                    '<' + 'I' * count))))

    def _memory(self, vm, access, address, size, value, _):
        from unicorn import UC_MEM_WRITE
        event = dict(rva=self.get('EIP') - BASE, address=address, size=size)
        if access == UC_MEM_WRITE:
            require(STACK <= address and address + size <= STACK + 0x10000 or
                    any(p <= address and address + size <= p + 4096 for p in self.pages),
                    'Native write escaped fixture data')
            if not STACK <= address < STACK + 0x10000:
                self.writes.append(dict(event, value=value))
        elif not STACK <= address < STACK + 0x10000:
            self.reads.append(event)

    def prepare(self, *, flags=0, target_state=0, poison=0):
        for page in self.pages:
            self.vm.mem_write(page, bytes(4096))
        for entity, marker in ((ACTOR, 0), (TARGET, 1)):
            self.vm.mem_write(entity, bytes([poison]) * 4096)
            self.write(entity + 0x1a, '<H', marker)
            self.write(entity + 0x16, '<H', 0xffff)
            self.write(entity + 0x277, '<B', 0)
            self.write(entity + 0x239, '<B', 1)  # Qualified noninitial action-record slice.
            self.write(entity + 0xdb8, '<I', flags)
        self.write(ACTOR + 0x234, '<BB', 0, 0x80)
        self.write(ACTOR + 0x1e9, '<BBB', 1, 0, 0)
        self.write(TARGET + 0x1eb, '<B', target_state)
        self.write(TARGET + 0x232, '<B', 0)
        self.write(CONTEXT + 0x38, '<I', ACTOR)
        self.write(CONTEXT + 0x38 + 14 * 24, '<I', TARGET)
        self.write(BATTLE + 0xa9df6b8, '<I', 1)  # Already initialized battle fixture.
        self.write(CONTEXT + 0xa7fbccc + 14 * 8, '<II', 100, 200)
        self.vm.mem_write(STACK, b'\xa5' * 0x10000)
        self.write(CONTROL, '<I', 1)

    def execute(self, entry, *, args=(), registers=None, stops=(), frame=None):
        self.trace, self.reads, self.writes, self.calls = [], [], [], []
        self.stops = set(stops)
        words = (RETURN, *args) if frame is None else frame
        self.write(SP, '<' + 'I' * len(words), *words)
        for name in ('EAX', 'EBX', 'ECX', 'EDX', 'EBP', 'ESI', 'EDI'):
            self.set(name, 0)
        self.set('ESP', SP)
        self.set('EFLAGS', 2)
        for name, value in (registers or {}).items():
            self.set(name, value)
        self.vm.emu_start(BASE + entry, RETURN, count=20000)
        end = self.get('EIP')
        require(end == RETURN or end - BASE in self.stops, 'Native instruction budget exhausted')
        return end

    def format_result(self):
        require(self.get('EIP') == BASE + 0x147af7, 'Did not reach original formatter entry')
        caller, destination, pointer = self.read(self.get('ESP'), '<III')
        end = self.image.index(b'\0', pointer - BASE)
        text = self.image[pointer - BASE:end]
        return dict(format_rva=pointer - BASE, format_hex=text.hex(),
            format_text=text.decode('cp950'), caller_return_rva=caller - BASE,
            numeric_argument=self.read(self.get('ESP') + 12, '<i')[0]
                if b'%' in text else None,
            stop_rva=0x147af7, calls=self.calls.copy(),
            reads=self.reads.copy(), writes=self.writes.copy(),
            trace_sha256=hashlib.sha256(b''.join(struct.pack('<I', r) for r in self.trace)).hexdigest(),
            executed_instructions=len(self.trace))

    def incoming(self, record, **state):
        if type(record) is not bytes or len(record) != 15 or record[:2] != b'\x83\x01':
            raise ValueError('Qualified input is one 15-byte S2C83 action-kind-1 record')
        if record[2] != 0 or record[3] != 1 or record[5:9] != b'\0\0\x01\0':
            raise ValueError('Qualified fixture requires actor 0 and side-1 slot-0 target')
        self.prepare(**state)
        pointer = INPUT + 4096 - len(record)
        self.vm.mem_write(pointer, record)
        self.vm.mem_write(RECORD, record)
        self.write(SP + 0x28, '<I', CONTROL)
        before = {p: bytes(self.vm.mem_read(p, 4096)) for p in self.pages}
        self.execute(0x114332, registers=dict(EBP=pointer, EDI=RECORD, ESI=BATTLE),
                     stops=(0x147af7,))
        result = self.format_result()
        require(bytes(self.vm.mem_read(pointer, 15)) == record, 'Original input mutated')
        require(bytes(self.vm.mem_read(RECORD, 15)) == record, 'Copied action input mutated')
        require({0x116ae0, 0x12c520, 0x12a8d0, 0x12b060, 0x12b412} <= set(self.trace),
                'Supplied-outcome route was not executed continuously')
        require(not any(0x147d7f <= r < 0x147da1 for r in self.trace),
                'Unexpected RNG on supplied-outcome path')
        # Verify every changed fixture byte is accounted for by observed writes.
        for page, original in before.items():
            expected = bytearray(original)
            for write in self.writes:
                if page <= write['address'] < page + 4096:
                    offset, size = write['address'] - page, write['size']
                    expected[offset:offset + size] = int(write['value']).to_bytes(size, 'little')
            require(bytes(self.vm.mem_read(page, 4096)) == expected, 'Unaccounted fixture mutation')
        return dict(result, input_hex=record.hex(), supplied_outcome=record[11],
                    amount=struct.unpack_from('<h', record, 9)[0])

    def rng_core(self, seed):
        if type(seed) is not int or not 0 <= seed <= 0xffffffff:
            raise ValueError('RNG seed must be a DWORD')
        self.write(THREAD + 0x14, '<I', seed)
        self.execute(0x147d84, registers=dict(EAX=THREAD))
        require(self.get('ESP') == SP + 4, 'RNG body stack mismatch')
        require(self.writes == [dict(rva=0x147d93, address=THREAD + 0x14, size=4,
                                     value=self.read(THREAD + 0x14, '<I')[0])],
                'RNG changed unexpected state')
        return dict(seed=seed, next_seed=self.read(THREAD + 0x14, '<I')[0], value=self.get('EAX'))

    def rng_call_boundary(self):
        self.execute(0x12a89d, stops=(0x14e001,))
        chain = list(self.read(self.get('ESP'), '<II'))
        require(chain == [BASE + 0x147d84, BASE + 0x12a8a2], 'Unexpected native RNG/TLS calls')
        return dict(stop_rva=0x14e001, return_chain_rvas=[v - BASE for v in chain],
                    boundary='Real calls executed; TLS helper and OS imports NOT_EXECUTED')

    def local_numeric_tail(self, random_value):
        if type(random_value) is not int or not 0 <= random_value <= 32767:
            raise ValueError('Expected original RNG output domain 0..32767')
        self.prepare()
        # Explicit continuation inputs after 12A89D's RNG call: three already
        # pushed arguments and two local target coordinates. No TLS return stub.
        self.write(SP + 0x14, '<II', 0, 1)
        self.execute(0x12a8a2, frame=(0, 0, 0x22), registers=dict(
            EAX=random_value, EBX=0, ESI=CONTEXT), stops=(0x147af7,))
        return self.format_result()

    def action_binding(self, outcome, *, target_state=0, secondary=34):
        if type(outcome) is not int or not 0 <= outcome < 13:
            raise ValueError('Expected qualified action-map byte 0..12')
        if not (type(secondary) is int and 0 <= secondary < 67
                and type(target_state) is int and 0 <= target_state <= 255):
            raise ValueError('Expected secondary 0..66 and target state byte')
        self.prepare(target_state=target_state)
        self.execute(0x12c000, args=(0, 0, outcome, secondary, 1), registers=dict(ECX=CONTEXT))
        require(self.get('ESP') == SP + 24, 'Action consumer stack mismatch')
        return dict(outcome=outcome, mapped_action=self.image[0x171600 + outcome],
            secondary=secondary, mapped_secondary=self.image[0x171610 + secondary],
            actor_action=self.read(ACTOR + 0x1eb, '<B')[0],
            actor_raw_action=self.read(ACTOR + 0x1e8, '<B')[0],
            target_prior_action=target_state, writes=self.writes.copy(), calls=self.calls.copy())


def build_report(image=None):
    image = read_pinned(IMAGE, IMAGE_SHA256) if image is None else image
    native = NativeHit(image)
    incoming = [native.incoming(fixture(outcome, amount))
                for outcome in (0, 6, 7, 8, 9, 11, 12)
                for amount in (-32768, -1, 0, 1, 32767)]
    rng = []
    for seed in (0, 1, 2, 0x12345678, 0x7fffffff, 0x80000000, 0xffffffff):
        core = native.rng_core(seed)
        rng.append(dict(core, numeric_tail=native.local_numeric_tail(core['value'])))
    return dict(schema='current-hit-formula-evidence-v1', image_sha256=IMAGE_SHA256,
        qualification='OFFLINE_ORIGINAL_NATIVE_SLICES; synthetic state and logical input',
        hit_probability_formula='NOT_RECOVERED', accuracy_evasion_stat_inputs='UNIDENTIFIED',
        observed_decision='Supplied unsigned result byte == 8 selects original evasion text',
        probability_threshold='No RNG comparison in the executed outcome consumer or numeric producer tail',
        nearest_rng='32-bit CRT state update; 15-bit output; remainder 100 feeds numeric argument, not outcome',
        boundaries=['Formatting/rendering stops at 147AF7',
            'RNG body begins at 147D84 after unexecuted TLS helper 14E001',
            'Numeric tail begins at 12A8A2 with explicit continuation state',
            'No socket receive, original server execution, or live E2E'],
        next_missing_link='Original producer choosing logical S2C83 byte +11 for action-kind 1; '
            'connect accuracy/evasion stats and RNG threshold to that byte before asserting a hit formula',
        slices=[dict(name=name, start_rva=lo, end_rva_exclusive=hi,
                     sha256=hashlib.sha256(image[lo:hi]).hexdigest(), raw_hex=image[lo:hi].hex())
                for name, lo, hi in SLICES],
        counts=dict(incoming_cases=len(incoming), rng_seed_cases=len(rng), action_binding_cases=16),
        incoming=incoming, rng=rng, rng_call_boundary=native.rng_call_boundary(),
        action_binding=[native.action_binding(o, target_state=t, secondary=s)
                        for o in (0, 7, 8, 11) for t in (0, 3) for s in (0, 34)])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args(argv)
    started = time.perf_counter()
    report = build_report()
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=True, sort_keys=True, indent=2) + '\n',
                               encoding='utf-8', newline='\n')
    print(json.dumps(dict({key: report[key] for key in ('qualification', 'hit_probability_formula',
        'observed_decision', 'nearest_rng', 'next_missing_link', 'counts')},
        elapsed_seconds=round(time.perf_counter() - started, 3)), sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
