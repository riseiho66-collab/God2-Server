"""Bounded dispatch inventory and a new received-result WORD exclusion.

No complete monster attributes are recovered. The new 83/0D kind-zero writer
feeds a signed display amount, not a four-stat initialization record.
"""
import hashlib
import json
import struct

from .current_battle_entry import (
    BASE, BATTLE, SP, STACK, NativeRun, pinned_image, IMAGE_SHA256,
    UC_HOOK_MEM_READ, UC_HOOK_MEM_WRITE, UC_X86_REG_EIP, UC_X86_REG_EBX,
    UC_X86_REG_EBP,
)
from .current_damage_formula import RECEIVE_RANGES, MANAGER, PACKET, SOURCE, GATE, OUT
from unicorn import UC_MEM_WRITE

runtime_mutation_enabled = False
SPANS = {
    'dispatch': (0x114332, 0x1145c0),
    'opcode_targets': (0x114634, 0x11465c),
    'opcode_indices': (0x11465c, 0x1146ca),
    '86_targets': (0x1146cc, 0x1146e8),
    '83_targets': (0x1171ac, 0x1171d4),
    '83_indices': (0x1171d4, 0x1171eb),
    '83_actor_targets': (0x12cc3c, 0x12cc98),
    'kind_zero_writer': (0x12ca3a, 0x12caba),
    'result_style_lookup': (0x12c000, 0x12c0b3),
    'result_style_store': (0x12c1c4, 0x12c1f0),
    'style_table': (0x171600, 0x17160d),
    'secondary_table': (0x171610, 0x171653),
    'consumer_prefix': (0x1287cd, 0x128829),
    'consumer_format': (0x128829, 0x12886d),
    'amount_format': (0x19d970, 0x19d977),
}
RECEIVE = (*RECEIVE_RANGES, SPANS['kind_zero_writer'],
           (0x12a8d0, 0x12ab9a), SPANS['result_style_lookup'],
           (0x12c0c0, 0x12c0f8), SPANS['result_style_store'],
           (0x12cc2f, 0x12cc3c))


class MissingSource(AssertionError):
    """A consumer tried reading an actor amount/style not written by this run."""


def dispatch_tables(image):
    def target(table, index):
        return struct.unpack_from('<I', image, table + index * 4)[0] - BASE
    return {
        'opcode_range': [0x1c, 0x89],
        'default_rva': 0x1145c0,
        'nondefault_opcodes': {
            f'{op:02X}': target(0x114634, image[0x11465c + op - 0x1c])
            for op in range(0x1c, 0x8a)
            if target(0x114634, image[0x11465c + op - 0x1c]) != 0x1145c0},
        '86_subtypes': [target(0x1146cc, i) for i in range(7)],
        '83_subtypes_1_to_23': [target(0x1171ac, image[0x1171d4 + i])
                                for i in range(23)],
        '83_actor_subtypes_1_to_23': [target(0x12cc3c, i) for i in range(23)],
    }


def logical_record(side, word, marker):
    if (type(side) is not int or side not in (0, 1) or
            type(word) is not int or not 0 <= word <= 0xffff or
            type(marker) is not int or not 0 <= marker <= 255):
        raise ValueError('Expected side 0/1, raw WORD and marker BYTE')
    raw = bytearray(15)
    raw[:4] = bytes((0x83, 13, side * 14, marker))
    struct.pack_into('<H', raw, 5 + 2 * side, 1)
    struct.pack_into('<H', raw, 9, word)
    raw[13] = 9  # Native style table entry 9 is 87; secondary entry 0 is 09.
    return bytes(raw)


def _run(n, start, ranges, stops, *, written=None, budget=5000):
    n.visits.clear()
    n.writes.clear()
    trace = {'start_rva': start, 'reads': [], 'writes': []}
    regions = (('packet', PACKET, 15), ('actor', SOURCE, 0x1000),
               ('manager', MANAGER, 0x400), ('local_slot', BATTLE + 0x51, 1),
               ('phase', BATTLE + 0xa9df6b8, 4),
               ('battle_flags', BATTLE + 0xa9e9c6c, 12),
               ('gate_output', GATE, 8), ('stack', STACK, 0x8000),
               ('image', BASE, len(n.image)))

    def memory(vm, kind, address, size, value, _):
        region = next(((name, lo) for name, lo, length in regions
                       if lo <= address and address + size <= lo + length), None)
        rva = vm.reg_read(UC_X86_REG_EIP) - BASE
        if region is None:
            raise AssertionError(f'Unqualified data access {rva:X}: {address:X}/{size}')
        write = kind == UC_MEM_WRITE
        if write and region[0] not in ('stack', 'actor', 'manager', 'battle_flags'):
            raise AssertionError('Unexpected native destination: ' + region[0])
        if (not write and written is not None and SOURCE + 0x27a <= address < SOURCE + 0x286
                and not set(range(address, address + size)) <= written):
            raise MissingSource(f'Unwritten result at RVA {rva:X}, actor+{address-SOURCE:X}')
        raw = ((value & ((1 << (8 * size)) - 1)).to_bytes(size, 'little') if write
               else bytes(vm.mem_read(address, size)))
        trace['writes' if write else 'reads'].append({
            'rva': rva, 'address': address, 'region': region[0],
            'offset': address - region[1], 'size': size, 'hex': raw.hex()})

    hook = n.vm.hook_add(UC_HOOK_MEM_READ | UC_HOOK_MEM_WRITE, memory)
    try:
        n.run(start, ranges, stops, budget=budget)
    finally:
        n.vm.hook_del(hook)
    trace.update(stop_rva=n.stop, visits=list(n.visits))
    return trace


class CompleteAttributesProbe:
    def __init__(self, image=None):
        self.image = pinned_image() if image is None else image
        if hashlib.sha256(self.image).hexdigest() != IMAGE_SHA256:
            raise ValueError('Pinned current image changed')

    def receive(self, side, word, *, index=0, poison=0xa5, actor_present=True):
        if (type(index) is not int or index not in (0, 1, 2) or
                type(poison) is not int or not 0 <= poison <= 255 or
                type(actor_present) is not bool):
            raise ValueError('Bounded three-result window and explicit actor availability required')
        marker = 32 + index
        record = logical_record(side, word, marker)
        n = NativeRun(self.image)
        n.put(STACK, bytes((poison,)) * 0x8000)
        actor = bytearray(bytes((poison,)) * 0x1000)
        actor[0x239] = 1  # Existing action; do not repeat the qualified broad reset.
        struct.pack_into('<h', actor, 0x1a, 0)
        n.put(SOURCE, bytes(actor))
        n.put(PACKET, record)
        n.put(MANAGER, bytes((poison,)) * 0x400)
        n.put(MANAGER + 0x38, bytes(28 * 24))
        n.put32(MANAGER + 0x38 + 24 * side * 14, SOURCE if actor_present else 0)
        n.put(MANAGER + 0x30c, bytes((0xff if index == 0 else 32,)))
        n.put(BATTLE + 0x51, b'\xff')
        n.put32(BATTLE + 0xa9df6b8, 1)
        n.put(BATTLE + 0xa9e9c6c, bytes((poison,)) * 12)
        n.put32(GATE, marker)
        n.put32(OUT, 0)
        n.put32(SP + 0x28, GATE)
        n.put32(SP + 0x2c, OUT)
        n.registers(esp=SP, ebp=PACKET, edi=PACKET, esi=BATTLE, eax=0)
        trace = _run(n, 0x114332, RECEIVE, {0x1143a1})
        return n, bytes(actor), trace

    def consume_amount(self, n, producer):
        written = {a for event in producer['writes'] if event['region'] == 'actor'
                   for a in range(event['address'], event['address'] + event['size'])}
        n.registers(esp=SP, esi=SOURCE, edi=MANAGER, ebx=0, ebp=0)
        prefix = _run(n, 0x1287cd, (SPANS['consumer_prefix'],), {0x128824}, written=written)
        live = {'ebx': n.vm.reg_read(UC_X86_REG_EBX), 'ebp': n.vm.reg_read(UC_X86_REG_EBP)}
        if live != {'ebx': 0x87, 'ebp': 9}:
            raise ValueError('Outside the single qualified display-style path')
        # Independent post-pose island, not a return from unresolved 12A200.
        n.registers(esp=SP, esi=SOURCE, edi=MANAGER, **live)
        consumer = _run(n, 0x128829, (SPANS['consumer_format'], (0x147000, 0x16f000)),
                        {0x12886d}, written=written, budget=100000)
        text = bytes(n.vm.mem_read(SP + 0x18, 20)).split(b'\0', 1)[0]
        return {'pose_prefix': prefix, 'independent_format': consumer,
                'live_registers': live, 'text_ascii': text.decode('ascii')}


def evidence():
    probe = CompleteAttributesProbe()
    examples = []
    for side in (0, 1):
        n, before, trace = probe.receive(side, 0xffe2)
        after = bytes(n.vm.mem_read(SOURCE, len(before)))
        amount = probe.consume_amount(n, trace)
        examples.append({'side': side, 'packet_hex': logical_record(side, 0xffe2, 32).hex(),
                         'authority': 'synthetic input, not official numeric values',
                         'receive': trace, 'consumer': amount,
                         'changed_actor_offsets': [i for i, (a, b) in enumerate(zip(before, after))
                                                   if a != b]})
    return {'image_sha256': IMAGE_SHA256, 'base': BASE, 'rva_equals_file_offset': True,
            'verified_original_monster_attack_defense_values': 0,
            'physical_attack': None, 'physical_defense': None,
            'magical_attack': None, 'magical_defense': None,
            'dispatch_tables': dispatch_tables(probe.image),
            'spans': {k: {'rva_start': lo, 'rva_end_exclusive': hi,
                          'sha256': hashlib.sha256(probe.image[lo:hi]).hexdigest()}
                      for k, (lo, hi) in SPANS.items()},
            'examples': examples}


if __name__ == '__main__':
    print(json.dumps(evidence(), sort_keys=True, indent=2))
