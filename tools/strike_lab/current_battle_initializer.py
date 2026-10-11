"""Continuous pinned initializer prefix, with explicit pre-call memory fixtures.

Start only at 1112C0. No skipped calls, synthetic returns, patched instructions,
host process, or claim of live battle entry. Explicit snapshots select the extent.
"""
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tools.strike_lab.current_battle_entry import (
    NativeRun, BASE, BATTLE, CONTEXT, DESCRIPTOR, ROOT_OBJECT, RENDERER,
    RESOURCES, NET, UI, SP, IMAGE_SHA256, UC_PROT_READ, UC_PROT_WRITE,
    UC_X86_REG_ESP, UC_X86_REG_ECX,
)

INPUT = 0x6800000
DISPLAY = 0x6b00000
MANAGER_RENDERER = 0x6c00000
QUEUE_STORAGE = 0x3400000
QUEUE = BATTLE + 0xa9ea4b0
MANAGER = BATTLE + 0x144938
ARENA = MANAGER + 0xa7fbdac
ARENA_SIZE = 0x9b5e0
RECORD_SIZE = 0xecc
ATTACHMENTS = MANAGER + 0xa89738c
ATTACHMENT_SIZE = 0x2c
DISPLAY_STATE_SIZE = 0xf66e8 + 3096 * 0x8c
REGISTRY = 0x5b4ed8
REGISTRY_COUNT = 20
REGISTRY_POOL_BASE, REGISTRY_POOL_STRIDE = 0x7000000, 0x300000
REGISTRY_POOL_SIZE = 0x10 + 4096 * 0x290
REGISTRY_RANGES = ((0x11145b, 0x11146f), (0x1ad10, 0x1adce))
REGISTRY_BOUNDARY = 0x111469
SOURCE, SOURCE_STATE_SIZE = 0x6900000, 0x8c
MANAGER_SOURCE, MANAGER_SOURCE_STATE_SIZE = 0x6d00000, 0x410
SOURCE_BOUNDARY, MANAGER_SOURCE_BOUNDARY = 0x111489, 0x11149b
SOURCE_RANGES = ((0x111469, 0x11149b),)
ENTRY, BOUNDARY, NEXT_CALLEE = 0x1112c0, 0x111456, 0x20580
runtime_mutation_enabled = False

RANGES = (
    (0x1112c0, 0x11145b), (0x181b0, 0x181b8),
    (0x11d350, 0x11d378), (0x11fc40, 0x11fd6e),
    (0x11e6e0, 0x11e76a), (0x11fde0, 0x11fff6),
    (0x11ca30, 0x11ca5f), (0x11ca90, 0x11cacd),
    (0x11cfb0, 0x11cff9), (0x12aea0, 0x12aec5),
)
# Stop at call instructions, before their execution or any callee side effect.
STOPS = {BOUNDARY, 0x11d367, 0x11e718, 0x11ca48, 0x11cfe5}


def initialize(context, *, queue_allocated=True, occupied_handle=None, display_state=None,
               registry_state=None, source_state=None, manager_source_state=None):
    """Execute from the real entry using a constructed pre-initializer fixture.

    queue_allocated=False proves the missing-buffer assertion boundary.
    occupied_handle supplies a prior bound attachment with one active handle;
    its native cleanup must stop at the unqualified 1B330 call.
    All fixture writes happen before the sole emu_start call.
    An explicit display_state additionally executes20580 continuously, stopping
    at11145B before loading the next unqualified object's pointer.
    registry_state is exactly twenty pool snapshots or None entries. With it,
    execution continues through 1AD10, stopping before the source read at 111469.
    source_state executes the source-dimension read and 205A0 to 111489.
    manager_source_state additionally executes the +40C -> +404 copy to 11149B,
    before reading the unresolved B+83458 pointer. Neither source is constructed.
    """
    if type(context) is not bytes or len(context) != 0x3ec:
        raise ValueError('Expected explicit 0x3EC-byte transition context')
    if type(queue_allocated) is not bool:
        raise ValueError('Expected explicit queue allocation flag')
    if occupied_handle is not None and (type(occupied_handle) is not int or
                                        not 0 <= occupied_handle < 0x1000):
        raise ValueError('Prior active handle must be 0..0xFFF or None')
    if display_state is not None and (type(display_state) is not bytes or
                                      len(display_state) != DISPLAY_STATE_SIZE):
        raise ValueError('Expected explicit bounded display-manager storage')
    if registry_state is not None:
        if (display_state is None or type(registry_state) is not tuple or
                len(registry_state) != REGISTRY_COUNT or
                any(pool is not None and (type(pool) is not bytes or
                    len(pool) != REGISTRY_POOL_SIZE) for pool in registry_state)):
            raise ValueError('Expected display state and twenty explicit registry snapshots/None')
    if source_state is not None and (registry_state is None or
            type(source_state) is not bytes or len(source_state) != SOURCE_STATE_SIZE):
        raise ValueError('Expected registry state and explicit 0x8C-byte source snapshot')
    if manager_source_state is not None and (source_state is None or
            type(manager_source_state) is not bytes or
            len(manager_source_state) != MANAGER_SOURCE_STATE_SIZE):
        raise ValueError('Expected source snapshot and explicit 0x410-byte manager source snapshot')
    n = NativeRun()
    n.put(CONTEXT, context)
    n.put(DESCRIPTOR, struct.pack('<7I', ROOT_OBJECT, CONTEXT, UI,
                                  0x6500000, RESOURCES, 0, 0x6600000))
    for offset, value in ((0x428, 0x6700000), (0x424, INPUT),
                          (0x42c, RENDERER), (0x438, NET)):
        n.put32(ROOT_OBJECT + offset, value)
    n.put(INPUT, b'\xa5' * 16)
    n.put32(RENDERER + 0xa0, SOURCE)
    n.put32(RENDERER + 0xac, 0x6a00000)
    n.put32(RENDERER + 0xa8, DISPLAY)
    n.put32(DISPLAY + 0xf66e0, 0xa5a5a5a5)
    if display_state is not None:
        n.put(DISPLAY - 16, b'\xa5' * 16 + display_state + b'\xa5' * 16)
    n.put(BATTLE, b'\xa5' * 0x500)
    n.put32(BATTLE + 0x28, RESOURCES)
    n.put(RESOURCES + 0xb2c6c, b'\0\0')  # Explicit empty string table.
    n.put(QUEUE, struct.pack('<6I', 0, QUEUE_STORAGE if queue_allocated else 0,
                            0x120, 0x240, 0x1000, 0xa5a5a5a5))
    if queue_allocated:
        n.put(QUEUE_STORAGE, b'\xa5' * 0x1000)
    n.put32(BATTLE + 0xa9ea4c8, 0xa5a5a5a5)
    n.put32(BATTLE + 0xa9e9c74, 0xa5a5a5a5)
    n.put(MANAGER, b'\xa5' * 0x400)
    n.put32(MANAGER + 0xc, MANAGER_RENDERER)
    if source_state is not None:
        n.put(SOURCE - 16, b'\xa5' * 16 + source_state + b'\xa5' * 16)
    if manager_source_state is not None:
        n.put32(MANAGER + 0x14, MANAGER_SOURCE)
        n.put(MANAGER_SOURCE - 16, b'\xa5' * 16 + manager_source_state + b'\xa5' * 16)
    n.put(ARENA - 16, b'\xa5' * (ARENA_SIZE + 16))
    n.put(MANAGER + 0xa7fbc58, b'\xa5' * 0x28)
    n.put(ATTACHMENTS, b'\xa5' * (28 * ATTACHMENT_SIZE + 16))
    for index in range(28):
        n.put32(ATTACHMENTS + index * ATTACHMENT_SIZE + 0x28, 0)
    if occupied_handle is not None:
        n.put32(ATTACHMENTS + 0x28, MANAGER_RENDERER)
        n.put(ATTACHMENTS + 6, struct.pack('<H', occupied_handle))
    # Original initializer writes string-cache globals; executable pages stay RX.
    n.vm.mem_protect(0x5b8000, 4096, UC_PROT_READ | UC_PROT_WRITE)
    n.put32(SP + 4, DESCRIPTOR)
    n.registers(ecx=BATTLE)
    ranges, stops = RANGES, STOPS
    if display_state is not None:
        ranges += ((0x20580, 0x20598), (0x205a0, 0x205e3), (0x273c0, 0x2746f))
        stops = (STOPS - {BOUNDARY}) | {0x11145b}
    active_pools = 0
    if registry_state is not None:
        n.vm.mem_protect(REGISTRY & ~4095, 4096, UC_PROT_READ | UC_PROT_WRITE)
        for index, pool in enumerate(registry_state):
            address = REGISTRY_POOL_BASE + index * REGISTRY_POOL_STRIDE
            n.put32(REGISTRY + index * 4, address if pool is not None else 0)
            if pool is not None:
                n.put(address - 16, b'\xa5' * 16 + pool + b'\xa5' * 16)
                active_pools += 1
        # Deliberately unmapped: 1AD10 must replace incoming ECX from the registry.
        n.put32(BATTLE + 0xa9df6c8, 0xdead0000)
        ranges += REGISTRY_RANGES
        stops = (stops - {0x11145b}) | {REGISTRY_BOUNDARY}
    if source_state is not None:
        ranges += SOURCE_RANGES
        stops = (stops - {REGISTRY_BOUNDARY}) | {SOURCE_BOUNDARY}
    if manager_source_state is not None:
        stops = (stops - {SOURCE_BOUNDARY}) | {MANAGER_SOURCE_BOUNDARY}
    return n.run(ENTRY, ranges, stops, budget=1000000 + active_pools * 3000000)


def report(*, with_registry=False, with_sources=False):
    context = bytearray(0x3ec)
    struct.pack_into('<II', context, 0x28, 0x12345678, 0x9abcdeff)
    options = {}
    with_registry = with_registry or with_sources
    if with_registry:
        display = bytearray(b'\xa7' * DISPLAY_STATE_SIZE)
        struct.pack_into('<II', display, 0, 640, 480)
        options = {'display_state': bytes(display),
                   'registry_state': (None,) * 19 + (b'\xa7' * REGISTRY_POOL_SIZE,)}
    if with_sources:
        source = bytearray(b'\xa7' * SOURCE_STATE_SIZE)
        struct.pack_into('<II', source, 0x84, 913, 577)
        manager_source = bytearray(b'\xa7' * MANAGER_SOURCE_STATE_SIZE)
        struct.pack_into('<I', manager_source, 0x40c, 0xcafebabe)
        options.update(source_state=bytes(source), manager_source_state=bytes(manager_source))
    n = initialize(bytes(context), **options)
    return {
        'sha256': IMAGE_SHA256, 'start_rva': hex(ENTRY),
        'stop_before_instruction_rva': hex(n.stop),
        'stop_before_call_rva': None if with_registry else hex(n.stop),
        'next_call_rva': ('0x1114aa' if with_sources else
                          '0x111484' if with_registry else hex(BOUNDARY)),
        'next_callee_rva': ('0x11fbf0' if with_sources else
                            '0x205a0' if with_registry else hex(NEXT_CALLEE)),
        'unresolved_source_pointer_offset': '0x83458' if with_sources else None,
        'single_continuous_run': True,
        'input_reset_returns': n.visits.count(0x181b7),
        'queue_reset_returns': n.visits.count(0x11d377),
        'record_reset_returns': n.visits.count(0x11fff3),
        'manager_reset_returns': n.visits.count(0x11fd6d),
        'registry_scan_returns': n.visits.count(0x1ad2d),
        'registry_pool_reset_returns': n.visits.count(0x1adcd),
        'battle_fields': [n.get32(BATTLE + 0x3c), n.get32(BATTLE + 0x40)],
        'queue_indices': [n.get32(QUEUE + 8), n.get32(QUEUE + 12)],
        'stack_at_stop': hex(n.vm.reg_read(UC_X86_REG_ESP)),
        'this_at_stop': hex(n.vm.reg_read(UC_X86_REG_ECX)),
        'instruction_visits': len(n.visits),
        'initializer_returned': False, 'live_entry_proven': False,
        'runtime_mutation_enabled': False,
    }


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--registry-prefix', action='store_true')
    parser.add_argument('--source-prefix', action='store_true')
    args = parser.parse_args()
    print(json.dumps(report(with_registry=args.registry_prefix,
                            with_sources=args.source_prefix), indent=2))
