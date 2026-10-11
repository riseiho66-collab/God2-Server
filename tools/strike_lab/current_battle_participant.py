"""Bounded current-image 83/84 consumption of explicit, already-existing actors.

One continuous original run starts at the post-copy battle opcode switch. This
does not allocate actors, initialize a battle, bind resources, or encode a wire
record. Every supplied handle/pointer is a snapshot precondition, not a result
invented for an intercepted call. Unknown calls stop before CALL executes.
"""
import struct

from tools.strike_lab.current_battle_entry import (
    BASE, BATTLE, SP, NativeRun, UC_HOOK_MEM_READ, UC_X86_REG_EIP,
    UC_X86_REG_ESP,
)

MANAGER = BATTLE + 0x144938
RECORD = BATTLE + 0xa9e9cb0
GATE, OUT = 0x6800000, 0x6800004
ENTITIES, RESOURCE_OWNER, METADATA, EFFECTS = (
    0x6900000, 0x6a00000, 0x6c00000, 0x6d00000,
)
ENTITY_SIZE, EFFECT_STRIDE = 0x1000, 0x214
ACTION_STATE_OFFSET, ACTION_STATE_SIZE = 0xa7fbc5c, 0x150
runtime_mutation_enabled = False


def entity_address(packed_position):
    return ENTITIES + packed_position * 0x2000


def consume(record, *, entities, phase_started=True, gate=None,
            metadata=None, effect_tables=None, local_slot=0xff, action_state=None):
    """Execute 83 subtypes 1/3 or 84 from dispatcher RVA114332.

    entities maps packed position (0..27) to an exact 0x1000-byte type-0 actor
    snapshot. Unlisted slots are explicitly null. metadata maps WORD keys to
    0x114-byte-or-larger snapshots; effect_tables maps 84/85 to packed 0x214-byte
    records. None means stop before the corresponding lookup, not null success.
    gate=None supplies the matching existing gate; -1 stops at its reset call.
    action_state optionally extends the existing caller through original
    12B060/1224A0. Its exact keys are manager_tail (0x150 raw bytes starting at
    M+A7FBC5C) and manager_0c (raw DWORD). No pointed-to resource is installed.
    None preserves the original pre-12B060 stops. Formatting, cleanup, and
    11DC00 calls remain unqualified and stop before CALL.
    """
    if (type(record) is not bytes or len(record) != 15 or
            record[0] not in (0x83, 0x84)):
        raise ValueError('Expected exactly 15 logical bytes beginning with 83/84')
    if record[0] == 0x83 and record[1] not in (1, 3):
        raise ValueError('Only 83 subtypes 1 and 3 are qualified here')
    if type(phase_started) is not bool or not 0 <= local_slot <= 255:
        raise ValueError('Expected explicit phase and local-slot state')
    for position, snapshot in entities.items():
        if (type(position) is not int or not 0 <= position < 28 or
                type(snapshot) is not bytes or len(snapshot) != ENTITY_SIZE):
            raise ValueError('Expected position 0..27 and exact actor snapshot')
    if metadata is not None:
        for key, snapshot in metadata.items():
            if not 0 <= key < 0x7f58 or type(snapshot) is not bytes or len(snapshot) < 0x114:
                raise ValueError('Expected native metadata key and snapshot through +112')
    if effect_tables is not None:
        for family, table in effect_tables.items():
            if (family not in (84, 85) or type(table) is not bytes or
                    len(table) % EFFECT_STRIDE or len(table) > 100 * EFFECT_STRIDE):
                raise ValueError('Expected bounded complete native effect records')
    if action_state is not None:
        if (type(action_state) is not dict or
                set(action_state) != {'manager_tail', 'manager_0c'} or
                type(action_state['manager_tail']) is not bytes or
                len(action_state['manager_tail']) != ACTION_STATE_SIZE or
                type(action_state['manager_0c']) is not int or
                not 0 <= action_state['manager_0c'] <= 0xffffffff):
            raise ValueError('Expected exact raw action manager snapshot and DWORD +0C')

    n = NativeRun()
    n.put(RECORD, record)
    n.put(MANAGER, b'\xa5' * 0x30a)
    n.put(MANAGER + 0x38, bytes(28 * 6 * 4))
    # These two supplied pointers are read, but never dereferenced in this scope.
    n.put32(MANAGER + 0x10, 0x6600000)
    n.put32(MANAGER + 0x20, 0x6601000)
    for position, snapshot in entities.items():
        n.put(entity_address(position), snapshot)
        n.put32(MANAGER + 0x38 + position * 24, entity_address(position))
    n.put32(BATTLE + 0xa9df6b8, int(phase_started))
    for offset in (0xa9e9c6c, 0xa9e9c74, 0xa9ea4c4, 0xa9df6c0):
        n.put32(BATTLE + offset, 0xa5a5a5a5)
    n.put(BATTLE + 0x51, bytes([local_slot]))
    marker = record[3 if record[0] == 0x83 else 8]
    n.put32(GATE, (marker if gate is None else gate) & 0xffffffff)
    n.put32(OUT, 0xa5a5a5a5)
    n.put32(SP + 0x28, GATE)
    n.put32(SP + 0x2c, OUT)
    n.registers(ebp=RECORD, edi=RECORD, esi=BATTLE, eax=0)

    ranges = [
        (0x114332, 0x114449), (0x116740, 0x1169e4),
        (0x116ae0, 0x116cb2), (0x116cf5, 0x116df6),
        (0x117152, 0x1171a9), (0x11e5e0, 0x11e62b),
        (0x11e6e0, 0x11e76a), (0x1169f0, 0x116a7c),
        (0x12c520, 0x12c636), (0x12cc2f, 0x12cc39),
        (0x12c430, 0x12c48b), (0x12a8d0, 0x12ab9a),
    ]
    stops = {
        0x114384, 0x1143f6,  # gate -1: unqualified 12AF90
        0x1143a1, 0x114415, 0x1145c0,  # handler return / gate mismatch
        0x116b14, 0x116771,  # initial phase: unqualified 12AEE0
        0x116c03, 0x1168af, 0x116917, 0x116982, 0x11e718,
        0x116d76, 0x116dd9, 0x12a8f5, 0x12ab1d, 0x12ab77,
        0x116df1,  # association-resource lookup 5F490
        0x12c631, 0x12c486,  # next entity setup call 12B060
    }
    if action_state is not None:
        n.put(MANAGER + ACTION_STATE_OFFSET, action_state['manager_tail'])
        n.put32(MANAGER + 0xc, action_state['manager_0c'])
        ranges += [(0x12b060, 0x12b4a1), (0x12b83d, 0x12b847),
                   (0x1224a0, 0x1224b6)]
        stops -= {0x12c631, 0x12c486}
        stops |= {
            0x12c636, 0x12c48b,  # real 12B060 early return; caller suffix unqualified
            0x12b0c3, 0x12b0f3, 0x12b315, 0x12b34d,
            0x12b36a,  # cleanup 1B330: do not fake release of an active handle
            0x12b397,  # next call 11DC00, with original computed arguments
            0x12b1a0, 0x12b1d2, 0x12b1f3, 0x12b214, 0x12b23b,
            0x12b270, 0x12b287, 0x12b2a5, 0x12b2b9, 0x12b2d4,
            0x12b2e8, 0x12b2fc, 0x12b324, 0x12b401, 0x12b421,
            0x12b43a, 0x12b453, 0x12b49c,  # original calls to 147AF7
        }
    if metadata is None:
        stops.add(0x11696a)
    else:
        n.put32(BATTLE + 0x28, RESOURCE_OWNER)
        n.put(RESOURCE_OWNER + 0xb2d40, bytes(0x7f58 * 4))
        for index, (key, snapshot) in enumerate(metadata.items()):
            address = METADATA + index * 0x10000
            if len(snapshot) > 0x10000 or address + len(snapshot) > EFFECTS:
                raise ValueError('Metadata fixture exceeds reserved arena')
            n.put(address, snapshot)
            n.put32(RESOURCE_OWNER + 0xb2d40 + key * 4, address)
        ranges += [(0x59a60, 0x59a7e), (0x116640, 0x116733)]
        stops |= {0x11668a, 0x1166c1, 0x116714}
        if effect_tables is None:
            stops.add(0x116671)
        else:
            # Missing families explicitly have count zero, hence native miss.
            for family, offset in ((84, 0x8345c), (85, 0x95650)):
                table = effect_tables.get(family, b'')
                address = EFFECTS + (family - 84) * 0x10000
                n.put32(BATTLE + offset + 0x121e8, len(table) // EFFECT_STRIDE)
                n.put32(BATTLE + offset + 0x121ec, address)
                if table:
                    n.put(address, table)
            ranges.append((0x5e0b0, 0x5e0e3))

    n.packet_reads, n.action_reads = [], []

    def packet_read(vm, access, address, size, value, _):
        if (action_state is not None and
                MANAGER + ACTION_STATE_OFFSET <= address <
                MANAGER + ACTION_STATE_OFFSET + ACTION_STATE_SIZE):
            n.action_reads.append((vm.reg_read(UC_X86_REG_EIP) - BASE,
                                   address - MANAGER, size))
        if RECORD <= address < RECORD + 0x20:
            if address + size > RECORD + 15:
                raise AssertionError('Native read beyond supplied logical record')
            n.packet_reads.append((vm.reg_read(UC_X86_REG_EIP) - BASE,
                                   address - RECORD, size))

    hook = n.vm.hook_add(UC_HOOK_MEM_READ, packet_read)
    try:
        return n.run(0x114332, ranges, stops, budget=20000)
    finally:
        n.vm.hook_del(hook)


def pending_arguments(n, count):
    """Raw DWORDs already pushed at the stopped CALL, not a new execution."""
    sp = n.vm.reg_read(UC_X86_REG_ESP)
    return struct.unpack('<' + 'I' * count, n.vm.mem_read(sp, count * 4))
