"""Bounded operand inventory and indexed-record counterexample.

Equal displacements do not prove equal structures or original skill formulas.
The linear sweep is a candidate index, not a control-flow or alias proof.
"""
import json
import struct

from .current_battle_entry import (
    BASE, SP, STACK, BATTLE, CONTEXT, NET, NativeRun, pinned_image, IMAGE_SHA256,
    UC_X86_REG_ESP, UC_X86_REG_ECX, UC_HOOK_MEM_READ, UC_X86_REG_EIP,
)
from capstone import Cs, CS_ARCH_X86, CS_MODE_32, CS_AC_READ
from capstone.x86 import X86_OP_MEM, X86_REG_ESP, X86_REG_EBP


def inventory():
    image = pinned_image()
    decoder = Cs(CS_ARCH_X86, CS_MODE_32)
    decoder.detail = True
    decoder.skipdata = True
    hits, skipped = [], 0
    for ins in decoder.disasm(image[0x1000:0x170000], BASE + 0x1000):
        if not ins.id:
            skipped += ins.size
            continue
        for op in ins.operands:
            if (op.type == X86_OP_MEM and op.size == 2 and
                    op.mem.disp in (0x5e, 0x60, 0x62, 0x64) and
                    op.mem.base not in (X86_REG_ESP, X86_REG_EBP)):
                hits.append(dict(rva=ins.address - BASE, instruction=ins.mnemonic,
                                 operands=ins.op_str, displacement=op.mem.disp,
                                 base=ins.reg_name(op.mem.base),
                                 index=ins.reg_name(op.mem.index), access=op.access))
    return {'image_sha256': IMAGE_SHA256, 'range': [0x1000, 0x170000],
            'authority': 'STATIC_OPERAND_CANDIDATES_NOT_FORMULAS',
            'skipped_bytes': skipped, 'candidates': hits,
            'limits': ['linear sweep may misalign code or decode data',
                       'only direct WORD displacements, excluding ESP/EBP',
                       'aliases, rebased pointers and wider loads not covered']}


def indexed_counterexample(index, value):
    if (type(index) is not int or not 0 <= index < 128 or
            type(value) is not int or not 0 <= value <= 65535):
        raise ValueError('Outside synthetic index/WORD bounds')
    n = NativeRun()
    field = CONTEXT + index * 0x268 + 0x60
    n.put32(CONTEXT + 8, NET)
    n.put(field, struct.pack('<H', value))
    n.registers(eax=index, edi=CONTEXT, esp=SP)
    reads = []

    def read(vm, access, address, size, unused, data):
        if vm.reg_read(UC_X86_REG_EIP) - BASE == 0xfd5db:
            reads.append([address, size])

    hook = n.vm.hook_add(UC_HOOK_MEM_READ, read)
    try:
        # Earlier index lookup is NOT executed; input EAX is explicitly supplied.
        n.run(0xfd5c2, ((0xfd5c2, 0xfd5ed),), {0x1091c0}, budget=100)
    finally:
        n.vm.hook_del(hook)
    sp = n.vm.reg_read(UC_X86_REG_ESP)
    return {'stop_rva': n.stop, 'field_read': reads,
            'argument': n.get32(sp + 4),
            'callee_this': n.vm.reg_read(UC_X86_REG_ECX),
            'row_start': CONTEXT + index * 0x268 + 0x18,
            'field_offset_from_row': 0x48,
            'source_unchanged': bytes(n.vm.mem_read(field, 2)) == struct.pack('<H', value)}


def wide_image_inventory():
    """Read/address candidates across the original scan, including wider loads."""
    image = pinned_image()
    decoder = Cs(CS_ARCH_X86, CS_MODE_32)
    decoder.detail = True
    decoder.skipdata = True
    hits, skipped = [], 0
    for ins in decoder.disasm(image[0x1000:0x170000], BASE + 0x1000):
        if not ins.id:
            skipped += ins.size
            continue
        if any(op.type == X86_OP_MEM and op.mem.base not in (X86_REG_ESP, X86_REG_EBP)
               and op.mem.disp < 0x66 and op.mem.disp + op.size > 0x5e
               and op.access & CS_AC_READ for op in ins.operands):
            hits.append({'rva': ins.address - BASE, 'instruction': ins.mnemonic,
                         'operands': ins.op_str})
    return {'image_sha256': IMAGE_SHA256, 'range': [0x1000, 0x170000],
            'candidates': hits, 'skipped_bytes': skipped,
            'authority': 'UNQUALIFIED_OVERLAPPING_OPERAND_INDEX',
            'limits': ['linear decoding can include data', 'LEA is not a memory read',
                       'equal offsets do not bind skill structures',
                       'rebased aliases and ESP/EBP operands remain outside scope']}


def translation_candidate(old_x, old_y, new_x, new_y):
    """10A646 prefix only; explicit object and new-value stack fixtures."""
    if any(type(v) is not int or not -32768 <= v <= 32767
           for v in (old_x, old_y, new_x, new_y)):
        raise ValueError('Expected signed WORD diagnostic inputs')
    n = NativeRun()
    snapshot = bytearray(b'\xa5' * 0x80)
    struct.pack_into('<hh', snapshot, 0x4c, old_x, old_y)
    struct.pack_into('<4I', snapshot, 0x58, 100, 200, 300, 400)
    n.put(CONTEXT, bytes(snapshot))
    n.put32(BATTLE + 8, NET)
    n.put32(SP + 0x18, new_x & 0xffffffff)
    n.put32(SP + 0x1c, new_y & 0xffffffff)
    n.registers(esi=CONTEXT, ebp=BATTLE)
    n.run(0x10a646, ((0x10a646, 0x10a67d),), {0x10a67d}, budget=40)
    return {'before': bytes(snapshot), 'after': bytes(n.vm.mem_read(CONTEXT, len(snapshot))),
            'stop_rva': n.stop, 'writes': n.writes,
            'callee_executed': False, 'skill_pointer_bound': False}


def wide_battle_inventory():
    """Include wider overlaps, EBP operands and LEA address candidates."""
    image = pinned_image()
    decoder = Cs(CS_ARCH_X86, CS_MODE_32)
    decoder.detail = True
    decoder.skipdata = True
    hits = []
    for ins in decoder.disasm(image[0x110000:0x131000], BASE + 0x110000):
        if not ins.id:
            continue
        if any(op.type == X86_OP_MEM and op.mem.base != X86_REG_ESP and
               op.mem.disp < 0x66 and op.mem.disp + op.size > 0x5e
               for op in ins.operands):
            hits.append({'rva': ins.address - BASE, 'instruction': ins.mnemonic,
                         'operands': ins.op_str})
    return {'range': [0x110000, 0x131000], 'candidates': hits,
            'authority': 'UNQUALIFIED_OVERLAPPING_OPERAND_INDEX',
            'limits': ['linear sweep includes possible embedded data',
                       'LEA is an address candidate, not a memory read',
                       'arbitrary aliases and ESP-based operands remain outside scope']}


def range_field_consumer(actor, reach, masks, *, secondary=False):
    """114A35 through both original getters and full target-mask calculation."""
    if (type(actor) is not int or not 0 <= actor < 14 or
            type(reach) is not int or not 0 <= reach <= 255 or
            type(secondary) is not bool or type(masks) is not tuple or
            len(masks) != 2 or any(type(v) is not int or not 0 <= v < 0x4000 for v in masks)):
        raise ValueError('Expected bounded actor, reach byte, two masks and branch')
    n = NativeRun()
    manager = BATTLE + 0x144938
    n.put32(BATTLE + 0xa9e9c38, 0 if secondary else 1)
    n.put32(BATTLE + 0xa9e9c3c, 1 if secondary else 0)
    n.put(BATTLE + 0x51, bytes([13 if secondary else actor,
                              actor if secondary else 13]))
    n.put32(BATTLE + 0x64, 0xa5a50000 | (255 if secondary else reach))
    n.put32(BATTLE + 0x68, 0xa5a50000 | (reach if secondary else 255))
    n.put(manager + 0x2f4, struct.pack('<2I', *masks))
    n.put(BATTLE + 0x434, b'\xa5' * 8)
    n.registers(esi=BATTLE, esp=SP)
    reads = []

    def read(vm, access, address, size, unused, data):
        if BATTLE + 0x64 <= address < BATTLE + 0x6c:
            reads.append([vm.reg_read(UC_X86_REG_EIP) - BASE, address - BATTLE, size])

    hook = n.vm.hook_add(UC_HOOK_MEM_READ, read)
    try:
        n.run(0x114a35, ((0x114a35, 0x114a5e), (0x1156e0, 0x11571c),
                         (0x11ec70, 0x11ee84)), {0x114a5e}, budget=5000)
    finally:
        n.vm.hook_del(hook)
    return {'stop_rva': n.stop, 'stack_after': n.vm.reg_read(UC_X86_REG_ESP),
            'masks': list(struct.unpack('<2I', n.vm.mem_read(BATTLE + 0x434, 8))),
            'range_reads': reads,
            'outside_stack_writes': [w for w in n.writes if not STACK <= w[1] < STACK + 0x8000],
            'input_masks_unchanged': bytes(n.vm.mem_read(manager + 0x2f4, 8)) == struct.pack('<2I', *masks),
            'instructions': len(n.visits)}


if __name__ == '__main__':
    result = inventory()
    result['indexed_counterexample'] = indexed_counterexample(1, 1234)
    result['wide_battle'] = wide_battle_inventory()
    result['range_binding'] = [range_field_consumer(0, reach, (0x3fff, 0x3fff)) for reach in (0, 1, 3)]
    print(json.dumps(result, sort_keys=True))
