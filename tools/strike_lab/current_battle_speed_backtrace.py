"""Original queued action group -> marker-matched activation, not monster speed.

No 83/0D amount/marker-bank replay, text formatting, time adapter or rendering.
Stop at the actual clock import call after the original activation scan.
"""
import hashlib
import json
import struct

from .current_battle_entry import (
    BASE, BATTLE, SP, STACK, NativeRun, pinned_image, IMAGE_SHA256,
    UC_HOOK_MEM_READ, UC_HOOK_MEM_WRITE, UC_X86_REG_EIP,
)
from unicorn import UC_HOOK_MEM_READ_UNMAPPED, UC_MEM_WRITE, UcError

MANAGER = BATTLE + 0x144938
QUEUE = BATTLE + 0xa9ea4b0
PACKET = BATTLE + 0xa9e9cb0
BUFFER, GATE, ACTORS, RENDER = 0x6800000, 0x6810000, 0x6900000, 0x6a00000
ACTOR_SIZE, STRIDE = 0xecc, 0x2000
DEFAULT_RECORDS = ((17, 7), (5, 7), (17, 8))
runtime_mutation_enabled = False
RANGES = (
    (0x1142f0, 0x1145ea), (0x11d3b0, 0x11d4d2),
    (0x15840, 0x15850), (0x1000, 0x1013), (0x1200, 0x1324),
    (0x116ae0, 0x116b19), (0x116bb1, 0x116c9c), (0x117152, 0x1171a9),
    (0x1169f0, 0x116a7c), (0x11e5e0, 0x11e62b), (0x11e6e0, 0x11e76a),
    (0x12c520, 0x12c5d3), (0x12c8f2, 0x12c92c), (0x12a8d0, 0x12ab9a),
    (0x12af90, 0x12b025), (0x12ac20, 0x12ae2f),
)
SPANS = {
    'queue_peek': (0x11d3b0, 0x11d3c3),
    'queue_copy_pop': (0x11d3d0, 0x11d4d2),
    'dispatcher_copy_gate': (0x1142f0, 0x1143dd),
    'dispatcher_activation_call': (0x1145c0, 0x1145e0),
    'marker_writer': (0x12a949, 0x12a971),
    'action20_receive': (0x12c8f2, 0x12c92c),
    'activation_scan': (0x12ac20, 0x12ae2f),
    'activation_targets': (0x12ae54, 0x12ae84),
    'activation_indices': (0x12ae84, 0x12ae9b),
    'clock_boundary_unexecuted': (0x12ae2f, 0x12ae4f),
}


class MissingSource(AssertionError):
    pass


def logical_record(position, marker):
    raw = bytearray(15)
    raw[:4] = bytes((0x83, 20, position, marker))
    struct.pack_into('<H', raw, 5 + 2 * (position // 14), 1 << (position % 14))
    raw[14] = 28
    return bytes(raw)


def run_group(records=DEFAULT_RECORDS, *, poison=0xa5, missing_render_state=None, image=None):
    """One first-marker group followed by one differently marked pending record.

    Actor objects/handles and render-kind bytes are explicit runtime snapshots.
    They supply no original monster identity, speed value or game return.
    """
    if (type(records) is not tuple or not 2 <= len(records) <= 3 or
            any(type(x) is not tuple or len(x) != 2 or
                type(x[0]) is not int or not 0 <= x[0] < 28 or
                type(x[1]) is not int or not 0 <= x[1] < 255 for x in records) or
            any(x[1] != records[0][1] for x in records[:-1]) or
            records[-1][1] == records[0][1] or
            type(poison) is not int or not 0 <= poison <= 255):
        raise ValueError('Expected bounded marker group and one pending record')
    present = {p for p, _ in records}
    if missing_render_state is not None and (type(missing_render_state) is not int or
                                              missing_render_state not in present):
        raise ValueError('Missing render snapshot must name one supplied actor')
    n = NativeRun(pinned_image() if image is None else image)
    n.put(STACK, bytes((poison,)) * 0x8000)
    n.put(BATTLE, bytes((poison,)) * 0x80)
    n.put(MANAGER, bytes((poison,)) * 0x400)
    n.put(MANAGER + 0x38, bytes(28 * 24))
    n.put32(MANAGER + 0xc, RENDER)
    before = []
    for pos in range(28):
        actor = bytearray(bytes((poison,)) * ACTOR_SIZE)
        struct.pack_into('<H', actor, 0x1a, pos if pos in present else 0xffff)
        actor[0x1e7], actor[0x1e9], actor[0x239] = 255, 0, 1
        before.append(bytes(actor))
        n.put(ACTORS + STRIDE * pos, bytes(actor))
        n.put32(MANAGER + 0x38 + 24 * pos, ACTORS + STRIDE * pos)
        if pos in present and pos != missing_render_state:
            n.put(RENDER + 0x10 + 0x290 * pos, b'\x02')
    raw = b''.join(logical_record(*item) for item in records)
    n.put(BUFFER, raw)
    n.put(QUEUE, struct.pack('<5I', 0, BUFFER, 0, len(raw), 0x1000))
    n.put(PACKET, bytes((poison,)) * 15)
    n.put32(BATTLE + 0xa9ea4c4, 1)
    n.put(BATTLE + 0xa9df6b8, struct.pack('<3I', 1, poison * 0x01010101, 0))
    n.put32(BATTLE + 0xa9df6c4, 0)
    n.put(BATTLE + 0xa9e9c6c, bytes((poison,)) * 12)
    n.put(GATE, struct.pack('<2I', 0xffffffff, 0))
    n.put32(SP + 0x28, GATE)
    n.put32(SP + 0x2c, GATE + 4)
    n.put(BATTLE + 0x51, b'\xff')
    n.put32(BATTLE + 0x10, 0)
    n.put(MANAGER + 0xa7fbc64, bytes((poison,)) * 8)
    n.registers(esp=SP, esi=BATTLE)
    regions = [('stack', STACK, 0x8000), ('image', BASE, len(n.image)),
               ('battle_prefix', BATTLE, 0x80), ('manager', MANAGER, 0x400),
               ('queue', QUEUE, 20), ('queue_continue', QUEUE + 20, 4),
               ('queue_bytes', BUFFER, len(raw)), ('record_copy', PACKET, 15),
               ('gate_output', GATE, 8), ('battle_phase', BATTLE + 0xa9df6b8, 16),
               ('battle_flags', BATTLE + 0xa9e9c6c, 12),
               ('activation_counts', MANAGER + 0xa7fbc64, 8)]
    regions += [(f'actor_{p}', ACTORS + STRIDE * p, ACTOR_SIZE) for p in range(28)]
    regions += [(f'render_kind_{p}', RENDER + 0x10 + 0x290 * p, 1) for p in present]
    trace = {'reads': [], 'writes': []}

    def memory(vm, kind, address, size, value, _):
        region = next(((name, start) for name, start, length in regions
                       if start <= address and address + size <= start + length), None)
        rva = vm.reg_read(UC_X86_REG_EIP) - BASE
        if region is None:
            raise AssertionError(f'Unqualified data access {rva:X}: {address:X}/{size}')
        write = kind == UC_MEM_WRITE
        if not write and region[0] == f'render_kind_{missing_render_state}':
            raise MissingSource(f'Unqualified render source at RVA {rva:X}: {address:X}/{size}')
        if write and (region[0] in ('image', 'queue_bytes', 'battle_prefix') or
                      region[0].startswith('render_kind_')):
            raise AssertionError('Unexpected native writer: ' + region[0])
        data = ((value & ((1 << (size * 8)) - 1)).to_bytes(size, 'little') if write
                else bytes(vm.mem_read(address, size)))
        trace['writes' if write else 'reads'].append({
            'rva': rva, 'address': address, 'region': region[0],
            'offset': address - region[1], 'size': size, 'hex': data.hex()})

    def missing(vm, access, address, size, value, _):
        trace['missing_source'] = (vm.reg_read(UC_X86_REG_EIP) - BASE, address, size)
        return False

    hooks = [n.vm.hook_add(UC_HOOK_MEM_READ | UC_HOOK_MEM_WRITE, memory),
             n.vm.hook_add(UC_HOOK_MEM_READ_UNMAPPED, missing)]
    try:
        n.run(0x1142f0, RANGES, {0x12ae2f}, budget=20000)
    except UcError as error:
        if 'missing_source' not in trace:
            raise
        rva, address, size = trace['missing_source']
        raise MissingSource(f'Unmapped source at RVA {rva:X}: {address:X}/{size}') from error
    finally:
        for hook in hooks:
            n.vm.hook_del(hook)
    def positions(rva):
        return [int(e['region'][6:]) for e in trace['writes']
                if e['rva'] == rva and e['region'].startswith('actor_')]
    trace.update(start_rva=0x1142f0, stop_rva=n.stop, visits=list(n.visits),
                 receive_order=positions(0x12a953), activation_order=positions(0x12add7),
                 queue_cursor=n.get32(QUEUE + 8), selected_marker=n.get32(GATE),
                 activation_count=n.get32(MANAGER + 0xa7fbc64),
                 marker_owner_hex=bytes(n.vm.mem_read(MANAGER + 0x308, 1)).hex(),
                 pending_hex=bytes(n.vm.mem_read(BUFFER + n.get32(QUEUE + 8), 15)).hex())
    return n, before, trace


def evidence():
    image = pinned_image()
    _, _, trace = run_group(image=image)
    return {'image_sha256': IMAGE_SHA256, 'base': BASE, 'rva_equals_file_offset': True,
            'original_monster_speed': None, 'original_monster_attributes_recovered': 0,
            'records': [logical_record(*r).hex() for r in DEFAULT_RECORDS],
            'input_authority': 'synthetic queue and actor-state diagnostics',
            'spans': {name: {'start_rva': lo, 'end_exclusive': hi,
                              'sha256': hashlib.sha256(image[lo:hi]).hexdigest()}
                      for name, (lo, hi) in SPANS.items()}, 'trace': trace}


if __name__ == '__main__':
    print(json.dumps(evidence(), sort_keys=True, indent=2))
