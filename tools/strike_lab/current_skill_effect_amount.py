"""Original received-operand -> actor effect slot -> text-call dataflow.

Receive-to-store is continuous. Text generation is a separately declared native
caller entry using the same VM/actor. Neither stage computes server damage.
"""
import struct
from .current_battle_entry import NativeRun, SP, STACK, BASE, UC_X86_REG_ESP
from .current_damage_formula import MANAGER, SOURCE, TARGET

RECORD, DEFINITION = 0x6800000, 0x6801000
RANGES = ((0x12c83f, 0x12c865), (0x12b060, 0x12b17d),
          (0x12b60d, 0x12b621), (0x11e6e0, 0x11e76a),
          (0x1224a0, 0x1224b6))


def receive_amount(raw, *, slot=0, state=3, poison=0xa5):
    if type(raw) is not bytes or len(raw) != 14:
        raise ValueError('Explicit 14-byte consumer record required, not a wire frame')
    if (type(slot) is not int or not 0 <= slot < 28 or
            type(state) is not int or state not in (3, 23) or
            type(poison) is not int or not 0 <= poison <= 255):
        raise ValueError('Outside explicit effect-store fixture bounds')
    n = NativeRun()
    n.put(RECORD, raw)
    n.put(MANAGER + 0x38, bytes(28 * 24))
    n.put32(MANAGER + 0x38, SOURCE)
    n.put32(MANAGER + 0x50, TARGET)
    n.put(MANAGER + 0xa7fbccc, struct.pack('<4I', 10, 20, 30, 40))
    actor = bytearray(bytes((poison,)) * 4096)
    struct.pack_into('<H', actor, 0x1a, 0)
    actor[0x1e9], actor[0x239], actor[0x277] = state, slot, 0
    n.put(SOURCE, bytes(actor))
    n.put(TARGET, bytes(actor))
    n.actor_before = bytes(actor)
    n.put32(SP + 0x20, 0)
    n.put32(SP + 0x24, 0)
    n.put32(SP + 0x28, 0)
    n.registers(esp=SP, esi=RECORD, ebx=MANAGER, edi=1,
                eax=0xa5000000, ecx=0xb6000000, edx=0xc7000000)
    n.run(0x12c83f, RANGES, {0x12b621}, budget=1000)
    if n.vm.reg_read(UC_X86_REG_ESP) != SP - 0x70:
        raise AssertionError('Original caller/callee stack differs')
    amount = struct.unpack_from('<H', raw, 8)[0]
    expected = bytearray(actor)
    struct.pack_into('<H', expected, 0x28a + slot * 2, amount)
    if (bytes(n.vm.mem_read(SOURCE, 4096)) != expected or
            bytes(n.vm.mem_read(TARGET, 4096)) != actor or
            bytes(n.vm.mem_read(RECORD, len(raw))) != raw):
        raise AssertionError('Effect amount or unrelated source changed')
    outside_stack = [w for w in n.writes if not STACK <= w[1] < STACK + 0x8000]
    if outside_stack != [(0x12b619, SOURCE + 0x28a + slot * 2, 2, amount)]:
        raise AssertionError('Unexpected native effect-store write')
    return n


def describe_slot_zero(n, definition):
    """Separate original125866 caller stage; not skipped intermediate rendering."""
    if type(definition) is not bytes or len(definition) != 110:
        raise ValueError('Explicit skill definition required')
    n.put(DEFINITION, definition)
    n.put32(SOURCE + 0xec4, DEFINITION)
    n.registers(esp=SP, esi=SOURCE, ebp=MANAGER, ecx=0)
    n.put(SP + 0x50, b'\xa5' * 1024)
    n.visits.clear()
    n.writes.clear()
    n.run(0x125866, ((0x125866, 0x125889), (0x126120, 0x126263),
                    (0x147000, 0x16f000)), {0x125889}, budget=200000)
    if n.vm.reg_read(UC_X86_REG_ESP) != SP:
        raise AssertionError('Text caller stack differs')
    if bytes(n.vm.mem_read(DEFINITION, 110)) != definition:
        raise AssertionError('Definition changed')
    if any(not (STACK <= at and at + size <= STACK + 0x8000) for _, at, size, _ in n.writes):
        raise AssertionError('Text caller wrote outside private stack')
    output = bytes(n.vm.mem_read(SP + 0x50, 1024))
    return output[:output.index(b'\0')]


def consume_skill_amount(bank, skill_id, word, *, target_position=1, logical_record=None):
    """Continuous12C520 entry to effect store with native skill selection/state."""
    from .current_monster_skill_assignments import (
        NativeSkillActions, diagnostic_actor, diagnostic_record, RECORD as ACTION_RECORD,
        MANAGER as ACTION_MANAGER, actor_address, SPANS)
    from .current_battle_entry import RETURN, UC_HOOK_MEM_READ, UC_X86_REG_EIP
    if type(word) is not int or not 0 <= word <= 65535:
        raise ValueError('Explicit unsigned received WORD required')
    if type(bank) is not int or type(skill_id) is not int:
        raise ValueError('Explicit native skill identity required')
    if type(target_position) is not int or not 0<=target_position<28 or target_position==0:
        raise ValueError('Explicit non-source target position required')
    fixture = NativeSkillActions()
    pointer = fixture.pointer(bank, skill_id)
    source = bytearray(diagnostic_actor(poison=0xa5, cached=(pointer,)))
    target = bytearray(diagnostic_actor(poison=0x7d))
    for actor in (source, target):
        struct.pack_into('<H', actor, 0x1a, 0)
        actor[0x277] = 0
    # Deliberately unrelated pre-call action state;12A8D0 must publish state3.
    source[0x1e9] = 0xa5
    fixture.install_actors({0: bytes(source), target_position: bytes(target)})
    n = fixture.n
    raw = bytearray(diagnostic_record(bank, skill_id, 0))
    struct.pack_into('<H', raw, 9, word)
    if logical_record is not None:
        if (type(logical_record) is not bytes or len(logical_record)!=15 or
                logical_record[:3]!=bytes((0x83,3,0)) or
                logical_record[11:13]!=bytes((skill_id,bank)) or
                struct.unpack_from('<H',logical_record,9)[0]!=word):
            raise ValueError('Mismatched explicit logical skill effect')
        masks=[0,0];masks[target_position//14]=1<<(target_position%14)
        if struct.unpack_from('<HH',logical_record,5)!=tuple(masks):
            raise ValueError('Logical target mask does not match native caller')
        raw=bytearray(logical_record)
    n.put(ACTION_RECORD, bytes(raw))
    n.put32(ACTION_MANAGER + 0x309, 0xa5a5a5a5)
    n.put(ACTION_MANAGER + 0xa7fbccc, struct.pack('<4I', 10, 20, 30, 40))
    n.put(SP, struct.pack('<6I', RETURN, ACTION_RECORD + 1, 0, 0, target_position//14, target_position%14))
    n.registers(esp=SP, ecx=ACTION_MANAGER)
    reads = []

    def read(vm, access, address, size, value, data):
        if ACTION_RECORD <= address < ACTION_RECORD + 4096:
            if address + size > ACTION_RECORD + 15:
                raise AssertionError('Action record overread')
            reads.append((vm.reg_read(UC_X86_REG_EIP) - BASE, address - ACTION_RECORD, size))

    hook = n.vm.hook_add(UC_HOOK_MEM_READ, read)
    try:
        n.run(0x12c520, (SPANS['action_consumer_prefix'], (0x12c731, 0x12c865),
                         (0x12c4b0, 0x12c4e8), (0x12a8d0, 0x12ab9c),
                         *RANGES[1:]), {0x12b621}, budget=3000)
    finally:
        n.vm.hook_del(hook)
    expected = {actor_address(0): source, actor_address(target_position): target}
    for _, at, size, value in n.writes:
        if STACK <= at and at + size <= STACK + 0x8000:
            continue
        if at == ACTION_MANAGER + 0x309 and size == 1:
            continue
        for base, snapshot in expected.items():
            if base <= at and at + size <= base + len(snapshot):
                snapshot[at-base:at-base+size] = value.to_bytes(size, 'little')
                break
        else:
            raise AssertionError(f'Action escaped known actor objects: {at:X}')
    for base, snapshot in expected.items():
        if bytes(n.vm.mem_read(base, len(snapshot))) != snapshot:
            raise AssertionError('Unaccounted actor mutation')
    if (n.get32(actor_address(0) + 0xec4) != pointer or
            n.vm.mem_read(actor_address(0) + 0x1e9, 1)[0] != 3 or
            bytes(n.vm.mem_read(actor_address(0) + 0x28c, 2)) != struct.pack('<H', word) or
            bytes(n.vm.mem_read(ACTION_RECORD, 15)) != raw):
        raise AssertionError('Native selected-skill/state/amount source changed')
    if (0x12c845, 9, 2) not in reads:
        raise AssertionError('Expected action-record amount read missing')
    n.effect_record_reads = reads
    return n
