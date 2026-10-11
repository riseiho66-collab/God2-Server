"""Pinned logical 86 side1 scalar-copy continuation, never damage production.

This reuses the sparse native harness. All calls/returns are original image
instructions. Explicit inactive graphic snapshots are diagnostic state only;
no visible rendering, actor creation, or original stat source is established.
"""
import struct

from tools.strike_lab.current_battle_entry import (
    BASE, BATTLE, PACKET_PAGE, SP, STACK, NativeRun, UC_X86_REG_EIP,
)
from tools.strike_lab.current_battle_scalar_result import IMAGE_SHA256
from unicorn import UC_HOOK_CODE, UC_HOOK_MEM_READ, UC_HOOK_MEM_INVALID, UC_MEM_READ_UNMAPPED, UcError
from unicorn import x86_const as reg

runtime_mutation_enabled = False
CONTEXT = BATTLE + 0x144938
MANAGER = CONTEXT + 0x310
RECORD = BATTLE + 0xa9e9cb0
OWNER = 0x21000000
ACTORS = 0x22000000
GRAPHICS = 0x30000000
RESOURCE_OWNER = 0x31000000
ACTOR_SIZE, DISPLAY_SIZE, GRAPHIC_SIZE = 0x1000, 0xa7e0, 0x290

RANGES = (
    (0x114332, 0x114358), (0x114464, 0x114482), (0x11449e, 0x1144a6),
    (0x117230, 0x11739c), (0x1173a0, 0x117472), (0x11e6e0, 0x11e76a),
    (0x12d8c0, 0x12d962), (0x12d840, 0x12d8b5),
    (0x109240, 0x109273), (0x108cd0, 0x108d31), (0x108e62, 0x108e66),
    (0x109200, 0x109232), (0x109280, 0x109347), (0x1093dd, 0x1093e2),
    (0x108fc0, 0x108ffe), (0x108f50, 0x108fb1), (0x108e70, 0x108f48),
    (0x149630, 0x149657),
    # Only the original inactive branch of the visibility helper is qualified.
    (0x1b740, 0x1b751), (0x1b815, 0x1b81a), (0x1bdc0, 0x1be50),
)
STOPS = {0x114482, 0x1144a6, 0x108d2c, 0x11e718,
         0x1b751, 0x1bdde, 0x1be45, 0x108ecd, 0x108f23}


def actor_address(position):
    return ACTORS + position * 0x2000


def display_address(handle):
    return MANAGER + 0x1c + handle * DISPLAY_SIZE


def graphic_address(handle):
    return GRAPHICS + 0x10 + handle * GRAPHIC_SIZE


def _snapshots(values, lo, hi, size, name):
    if type(values) is not dict or any(
            type(key) is not int or not lo <= key <= hi or
            type(raw) is not bytes or len(raw) != size
            for key, raw in values.items()):
        raise ValueError(f'Expected explicit {name} snapshots with exact bounds/widths')


def prepare(record, *, entities, displays, owner_value, diagnostic_graphics=None):
    """Install explicit same-state inputs; an absent actor means a null slot.

    diagnostic_graphics=None stops at a graphic helper entry. A dictionary
    supplies exact graphic records, allowing genuine inactive/absent-resource
    returns. Active-resource calls remain stop boundaries. No callee is mocked.
    """
    if (type(record) is not bytes or len(record) != 17 or record[0] != 0x86 or
            record[1] not in (0, 1) or not 14 <= record[2] < 28):
        raise ValueError('Expected one 17-byte logical 86/0,1 side1 record')
    _snapshots(entities, 14, 27, ACTOR_SIZE, 'side1 actor')
    _snapshots(displays, 0, 4095, DISPLAY_SIZE, 'display')
    if type(owner_value) is not int or not 0 <= owner_value <= 0xffffffff:
        raise ValueError('Expected raw owner DWORD')
    if diagnostic_graphics is not None:
        _snapshots(diagnostic_graphics, 0, 4095, GRAPHIC_SIZE, 'diagnostic graphic')

    n = NativeRun()
    n.reads, n.calls, n.fault = [], [], None
    n.stop_set = set(STOPS)
    if diagnostic_graphics is None:
        n.stop_set.update((0x1b740, 0x1bdc0))
    n.put(STACK, b'\xa5' * 0x8000)
    n.put(BATTLE, b'\xa5' * 4096)
    n.put(CONTEXT, b'\xa5' * 0x400)
    n.put(RECORD, record)
    n.put(PACKET_PAGE, record)
    n.put32(BATTLE + 0x83458, OWNER)
    n.put32(OWNER, owner_value)
    n.put32(MANAGER + 4, GRAPHICS)
    allowed_reads = {(PACKET_PAGE, 1), (RECORD + 1, 1), (RECORD + 2, 1),
                     (RECORD + 5, 4), (RECORD + 9, 4),
                     (BATTLE + 0x83458, 4), (OWNER, 4), (MANAGER + 4, 4)}
    allowed_writes = set()
    if diagnostic_graphics is not None:
        n.put32(GRAPHICS + 4, RESOURCE_OWNER)
        allowed_reads.add((GRAPHICS + 4, 4))
    for position in range(14, 28):
        slot = CONTEXT + 0x38 + position * 24
        n.put32(slot, actor_address(position) if position in entities else 0)
        allowed_reads.add((slot, 4))
    for position, raw in entities.items():
        address = actor_address(position)
        n.put(address, raw)
        allowed_reads.update((address + off, size) for off, size in
                             ((0x1a, 2), (0x1d8, 2), (0xde8, 4), (0xdec, 4), (0xdf4, 4)))
        allowed_writes.update(((address + 0xde8, 4), (address + 0xdf0, 4)))
    for handle, raw in displays.items():
        address = display_address(handle)
        n.put(address, raw)
        allowed_reads.update((address + off, 2) for off in
                             (0xa79c, 0xa79e, 0xa7a0, 0xa7a2, 0xa7a4, 0xa7a6))
        allowed_reads.update((address + off, 4) for off in (0xa7a8, 0xa7ac, 0xa7b0, 0xa7b4))
        allowed_writes.add((address + 0x2f, 1))
        allowed_writes.update((address + off, 4) for off in (0xa7a8, 0xa7ac, 0xa7b0, 0xa7b4))
    for handle, raw in (diagnostic_graphics or {}).items():
        address = graphic_address(handle)
        n.put(address, raw)
        allowed_reads.update(((address, 1), (address + 0xe, 2)))
        allowed_writes.update((address + off, 4) for off in (0x50, 0x54, 0x58, 0x5c))

    n.data_before = {page: bytes(n.vm.mem_read(page, 4096)) for page in n.pages
                     if not BASE <= page < BASE + len(n.image)
                     and not STACK <= page < STACK + 0x8000}
    n.allowed_writes = allowed_writes

    def read(vm, access, address, size, value, _):
        pc = vm.reg_read(UC_X86_REG_EIP) - BASE
        n.reads.append((pc, address, size))
        if STACK <= address and address + size <= STACK + 0x8000:
            return
        if BASE <= address and address + size <= BASE + len(n.image):
            return
        if (address, size) not in allowed_reads:
            # The native wrapper has no null check. Let Unicorn report its
            # actual unmapped read at +1A, never turn it into a successful ret.
            if pc == 0x12d8e1 and address == 0x1a and size == 2:
                return
            raise AssertionError(f'Unqualified data read {pc:X}: {address:X}/{size}')

    def fault(vm, access, address, size, value, _):
        pc = vm.reg_read(UC_X86_REG_EIP) - BASE
        n.fault = (pc, access, address, size)
        return False

    n.vm.hook_add(UC_HOOK_MEM_READ, read)
    n.vm.hook_add(UC_HOOK_MEM_INVALID, fault)
    n.registers(eax=0xa5a50000, ebx=0xa5a50000, ecx=0xa5a50000,
                edx=0xa5a50000, ebp=PACKET_PAGE, esi=BATTLE, edi=RECORD, esp=SP)
    n.vm.reg_write(reg.UC_X86_REG_EFLAGS, 2)
    n.vm.reg_write(reg.UC_X86_REG_FPCW, 0x037f)
    n.vm.reg_write(reg.UC_X86_REG_FPSW, 0)
    n.vm.reg_write(reg.UC_X86_REG_FPTAG, 0xffff)
    return n


def consume(record, *, entities, displays, owner_value, diagnostic_graphics=None):
    """One continuous dispatcher run; null dereference is an explicit failure.

    For zero divisors stop before the native unguarded x87 division. Otherwise
    do not interrupt arithmetic. Creation stops at the first 01F040 call site.
    """
    n = prepare(record, entities=entities, displays=displays, owner_value=owner_value,
                diagnostic_graphics=diagnostic_graphics)
    # Stops at division are conditional on the real divisor in the x87 frame.
    stops = n.stop_set - {0x108ecd, 0x108f23}
    def boundary(vm, address, size, _):
        argc = {0x12d8c0: 5, 0x109240: 1, 0x108cd0: 14,
                0x109200: 2, 0x12d840: 4, 0x108fc0: 3, 0x108f50: 3}.get(address - BASE)
        if argc is not None:
            sp = vm.reg_read(reg.UC_X86_REG_ESP)
            n.calls.append((address - BASE, vm.reg_read(reg.UC_X86_REG_ECX),
                            struct.unpack('<' + 'I' * (argc + 1), vm.mem_read(sp, 4 * (argc + 1)))))
        if address - BASE in (0x108ecd, 0x108f23):
            sp = vm.reg_read(reg.UC_X86_REG_ESP)
            if bytes(vm.mem_read(sp + 0x10, 4)) == bytes(4):
                n.stop = address - BASE
                vm.emu_stop()

    hook = n.vm.hook_add(UC_HOOK_CODE, boundary)
    try:
        n.run(0x114332, RANGES, stops, budget=4000)
    except UcError as error:
        if n.fault != (0x12d8e1, UC_MEM_READ_UNMAPPED, 0x1a, 2):
            raise AssertionError(f'Unqualified native memory access: {n.fault}') from error
        n.stop = 0x12d8e1
    finally:
        n.vm.hook_del(hook)
    for pc, address, size, value in n.writes:
        if not STACK <= address < STACK + 0x8000 and (address, size) not in n.allowed_writes:
            raise AssertionError(f'Unqualified data write {pc:X}: {address:X}/{size}')
    return n
