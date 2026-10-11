"""Bounded pet2 action -> native outbound queue, not original monster stats."""
import hashlib
import json
import struct

from .current_battle_entry import (
    NativeRun, pinned_image, IMAGE_SHA256, BASE, STACK, SP, RETURN,
    UC_X86_REG_EIP, UC_X86_REG_ESP,
)
from unicorn import (UC_HOOK_CODE, UC_HOOK_MEM_READ, UC_HOOK_MEM_WRITE,
                     UC_HOOK_MEM_READ_UNMAPPED, UC_MEM_WRITE, UcError)


PANEL, OWNER, QUEUE = 0x7000000, 0x7100000, 0x7200000
INVENTORY = OWNER + 0x8560c
QUEUE_COUNT, QUEUE_BYTES = 0x36c4, 0x36c8
SPANS = {
    'pet2_display': (0xa40c0, 0xa4dc4),
    'pet2_open': (0xa50f0, 0xa51ef),
    'pet2_action_caller': (0xa55f0, 0xa59fc),
    'action_table': (0xa59fc, 0xa5a3c),
    'native_queue': (0x132e0, 0x13368),
}


def static_evidence(image):
    if hashlib.sha256(image).hexdigest() != IMAGE_SHA256:
        raise ValueError('Pinned image changed')
    calls = ((0xa5664, 0xa53c0), (0xa5736, 0x132e0), (0xa57ff, 0x132e0),
             (0xa51e7, 0xa40c0), (0xa538b, 0xa40c0))
    for pc, target in calls:
        if image[pc] != 0xe8 or pc + 5 + struct.unpack_from('<i', image, pc + 1)[0] != target:
            raise AssertionError(f'Call changed at {pc:X}')
    dispatch = [v - BASE for v in struct.unpack_from('<8I', image, 0xa59fc)]
    if dispatch[4:] != [0xa5741, 0xa578b, 0xa578b, 0xa578b]:
        raise AssertionError('Pet2 action dispatch changed')
    return dict(calls=[dict(rva=p, target=t) for p, t in calls],
                dispatch_table_rva=0xa59fc, dispatch=dispatch,
                spans={name: dict(start_rva=a, end_rva_exclusive=z,
                                 sha256=hashlib.sha256(image[a:z]).hexdigest())
                       for name, (a, z) in SPANS.items()})


def run_action(*, control=0x18, pet_slot=43, item_slot=7, poison=0xa5,
               event_flags=0x20, queued_count=0, lock_pointer=0,
               missing_inventory=False, image=None):
    """Original post-tooltip island; all owner/UI/queue inputs are diagnostic.

    Does not run FB reception, rendering, socket flush, or lock helpers.
    A missing inventory page stops on its first attempted native read.
    """
    if (control not in range(0x17, 0x1b) or pet_slot not in (42, 43, 44)
            or item_slot is not None and not 0 <= item_slot < 30
            or poison not in range(256) or event_flags not in (0x20, 0x60)
            or not 0 <= queued_count <= 0xa00
            or lock_pointer not in (0, 0x12345678)):
        raise ValueError('Outside bounded diagnostic action inputs')
    n = NativeRun(image)
    evidence = static_evidence(n.image)
    n.put(PANEL, bytes([poison]) * 0x1000)
    n.put32(PANEL + 0xdc, OWNER)
    n.put(PANEL + 0xd8, bytes([pet_slot]))
    records_before = bytes(n.vm.mem_read(PANEL, 0xd8))
    if not missing_inventory:
        n.put(INVENTORY, bytes(24 * 30))
        if item_slot is not None:
            n.put(INVENTORY + 24 * item_slot, b'\x01')
            n.put32(INVENTORY + 24 * item_slot + 4,
                    0x4010 if control == 0x17 else 0x400f)
    n.put32(OWNER + 0x86874, QUEUE)
    n.put(QUEUE, b'\xcc' * 0x5000)
    n.put32(QUEUE + QUEUE_COUNT, queued_count)
    n.put32(QUEUE + 0x40d4, lock_pointer)
    n.put(SP - 0x100, bytes([poison]) * 0x200)
    # A5682 is after A55F0's three register saves and excluded tooltip call.
    n.put32(SP + 0xc, RETURN)
    n.put32(SP + 0x10, control)
    n.put32(SP + 0x14, event_flags)
    n.registers(ebx=PANEL, esi=control, esp=SP)
    events, calls, missing = [], [], []

    def region(address):
        for name, start, length in (
                ('pet2', PANEL, 0x1000), ('inventory', INVENTORY, 24 * 30),
                ('owner_queue_pointer', OWNER + 0x86874, 4),
                ('queue', QUEUE, 0x5000), ('stack', STACK, 0x8000),
                ('image', BASE, len(n.image))):
            if start <= address < start + length:
                return name, address - start
        return 'unclassified', address

    def memory(vm, access, address, size, value, _):
        writing = access == UC_MEM_WRITE
        name, offset = region(address)
        if writing and name not in ('queue', 'stack'):
            raise AssertionError(f'Unexpected native write to {name}')
        data = value.to_bytes(size, 'little') if writing else bytes(vm.mem_read(address, size))
        events.append(dict(rva=vm.reg_read(UC_X86_REG_EIP) - BASE,
                           access='write' if writing else 'read', address=address,
                           region=name, offset=offset, size=size, hex=data.hex()))

    def code(vm, address, size, _):
        if address == BASE + 0x132e0:
            sp = vm.reg_read(UC_X86_REG_ESP)
            ret, opcode, pointer, length = struct.unpack('<4I', vm.mem_read(sp, 16))
            calls.append(dict(return_rva=ret - BASE, opcode=opcode,
                              payload_pointer=pointer, payload_length=length,
                              payload_hex=bytes(vm.mem_read(pointer, length)).hex()))

    def unavailable(vm, access, address, size, value, _):
        missing.append(dict(rva=vm.reg_read(UC_X86_REG_EIP) - BASE,
                            address=address, size=size))
        return False

    hooks = [n.vm.hook_add(UC_HOOK_CODE, code),
             n.vm.hook_add(UC_HOOK_MEM_READ | UC_HOOK_MEM_WRITE, memory),
             n.vm.hook_add(UC_HOOK_MEM_READ_UNMAPPED, unavailable)]
    try:
        n.run(0xa5682, [(0xa5682, 0xa580a), (0x132e0, 0x13368)],
              {0x13370, 0x11970, 0x11990}, budget=2000)
    except UcError:
        if not missing_inventory or not missing:
            raise
    finally:
        for hook in hooks:
            n.vm.hook_del(hook)
    count = n.get32(QUEUE + QUEUE_COUNT)
    if bytes(n.vm.mem_read(PANEL, 0xd8)) != records_before:
        raise AssertionError('Pet2 numeric/identity records changed')
    if bytes(n.vm.mem_read(BASE, len(n.image))) != n.image:
        raise AssertionError('Pinned instructions changed')
    return dict(start_rva=0xa5682, stop_rva=missing[0]['rva'] if missing else
                None if n.stop == RETURN else n.stop,
                returned=n.stop == RETURN, missing_source=missing,
                fixtures=dict(control=control, pet_slot=pet_slot, item_slot=item_slot,
                              poison=poison, event_flags=event_flags,
                              missing_inventory=missing_inventory),
                queue_count_before=queued_count, queue_count_after=count,
                appended_hex=bytes(n.vm.mem_read(QUEUE + QUEUE_BYTES + queued_count,
                                                count - queued_count)).hex(),
                calls=calls, events=events, visits=n.visits,
                instruction_count=len(n.visits), records_unchanged=True,
                original_monster_values_recovered=0, static=evidence)


def build_report():
    image = pinned_image()
    return dict(schema='current-stat-packet-return-path-v1', image_sha256=IMAGE_SHA256,
                scope='Pet2 post-tooltip action island -> native C2S D6 queue append',
                qualified=run_action(image=image),
                missing_source=run_action(missing_inventory=True, image=image),
                no_matching_item=run_action(item_slot=None, image=image),
                boundary='No FB replay, renderer, socket, transport flush, lock helper, '
                         'wild identity join or C2S/S2C request-reply pairing executed.')


if __name__ == '__main__':
    print(json.dumps(build_report(), sort_keys=True))
