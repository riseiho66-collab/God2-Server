"""Pinned current-client battle-entry instruction islands, never live success.

Every run starts with explicit synthetic registers/memory and stops before an
unqualified call. Islands after that stop are independent precondition tests.
No callee is replaced, no instruction patched, no host process is attached.
"""
import hashlib
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'artifacts/tooling/crypto-oracle-python'))
from unicorn import (Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE,
                     UC_HOOK_MEM_READ, UC_HOOK_MEM_WRITE, UC_PROT_READ,
                     UC_PROT_WRITE, UC_PROT_EXEC)
from unicorn.x86_const import (UC_X86_REG_EAX, UC_X86_REG_EBX, UC_X86_REG_ECX,
                               UC_X86_REG_EDX, UC_X86_REG_EBP, UC_X86_REG_ESI,
                               UC_X86_REG_EDI, UC_X86_REG_ESP, UC_X86_REG_EIP)

IMAGE = ROOT / 'artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin'
IMAGE_SHA256 = '149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
BASE = 0x400000
WORLD, BATTLE, CONTEXT = 0x4000000, 0x5000000, 0x3000000
STACK, PACKET_PAGE, DESCRIPTOR = 0x3100000, 0x3200000, 0x3300000
ROOT_OBJECT, RENDERER, RESOURCES, NET = 0x6000000, 0x6100000, 0x6200000, 0x6300000
SP, RETURN = STACK + 0x4000, 0x7fff0000
UI = WORLD + 0xa7f2f6c
OPCODE, LOGICAL_SIZE = 0x82, 9
runtime_mutation_enabled = False


def pinned_image():
    image = IMAGE.read_bytes()
    if hashlib.sha256(image).hexdigest() != IMAGE_SHA256:
        raise ValueError('Pinned current image SHA256 mismatch')
    return image


def record_fields(record):
    """Exact logical record contract, not a transport-frame encoder."""
    if type(record) is not bytes or len(record) != LOGICAL_SIZE or record[0] != OPCODE:
        raise ValueError('Expected exactly nine logical bytes beginning with 82')
    return struct.unpack_from('<II', record, 1)


class NativeRun:
    """Sparse, bounded original execution; unknown control flow fails closed."""

    def __init__(self, image=None):
        image = pinned_image() if image is None else image
        if hashlib.sha256(image).hexdigest() != IMAGE_SHA256:
            raise ValueError('Pinned current image SHA256 mismatch')
        self.image = image
        self.vm = Uc(UC_ARCH_X86, UC_MODE_32)
        size = (len(image) + 4095) & ~4095
        self.vm.mem_map(BASE, size, UC_PROT_READ | UC_PROT_EXEC)
        self.vm.mem_write(BASE, image)
        self.pages = set(range(BASE, BASE + size, 4096))
        self.map(STACK, 0x8000)
        self.map(RETURN, 4096)
        self.vm.mem_protect(RETURN, 4096, UC_PROT_READ | UC_PROT_EXEC)
        self.vm.reg_write(UC_X86_REG_ESP, SP)
        self.put32(SP, RETURN)
        self.visits, self.writes = [], []
        self.stop = None

    def map(self, address, size):
        for page in range(address & ~4095, (address + size + 4095) & ~4095, 4096):
            if page not in self.pages:
                self.vm.mem_map(page, 4096, UC_PROT_READ | UC_PROT_WRITE)
                self.pages.add(page)

    def put(self, address, data):
        self.map(address, len(data))
        self.vm.mem_write(address, data)

    def put32(self, address, value):
        self.put(address, struct.pack('<I', value))

    def get32(self, address):
        return struct.unpack('<I', self.vm.mem_read(address, 4))[0]

    def registers(self, **values):
        for name, value in values.items():
            self.vm.reg_write(globals()['UC_X86_REG_' + name.upper()], value)

    def run(self, start, ranges, stops, budget=10000):
        self.stop = None
        def instruction(vm, address, size, _):
            rva = address - BASE
            if address == RETURN or rva in stops:
                self.stop = address if address == RETURN else rva
                vm.emu_stop()
                return
            if not any(lo <= rva and rva + size <= hi for lo, hi in ranges):
                raise AssertionError(f'Unqualified instruction RVA {rva:X}')
            self.visits.append(rva)

        def write(vm, access, address, size, value, _):
            self.writes.append((vm.reg_read(UC_X86_REG_EIP) - BASE, address, size, value))

        hooks = [self.vm.hook_add(UC_HOOK_CODE, instruction),
                 self.vm.hook_add(UC_HOOK_MEM_WRITE, write)]
        try:
            self.vm.emu_start(BASE + start, RETURN + 1, count=budget)
            if self.stop is None:
                raise AssertionError('Instruction budget exhausted without qualified stop')
        finally:
            for hook in hooks:
                self.vm.hook_del(hook)
        return self


def native_length(opcode=OPCODE):
    if type(opcode) is not int or not 0 <= opcode <= 255:
        raise ValueError('Expected byte opcode')
    n = NativeRun()
    n.put32(SP + 4, opcode)
    n.run(0x15840, [(0x15840, 0x15850), (0x1000, 0x1013),
                    (0x1200, 0x1324)], set())
    return n.vm.reg_read(UC_X86_REG_EAX)


def world_entry(record, *, negative_handles=False, closed_ui=False,
                closed_handle=-1, closing_category=0, queued_suffix=None, wire_frame=None):
    """Start at opcode load; default stop 6AE2D, optional real cleanup to 6AE34.

    The optional fixture explicitly supplies fifteen signed -1 handles. It
    qualifies only their original no-work branches, not active entity cleanup.
    closed_ui additionally supplies explicit inactive controls for all three
    cleanup calls. It reaches the state4 write continuously, not initialization.
    queued_suffix starts at the real function entry using a decoded native
    receive buffer. Socket polling stops at10D20; no socket result is invented.
    """
    record_fields(record)
    if (type(closed_ui) is not bool or type(closed_handle) is not int or
            not -32768 <= closed_handle < 0 or type(closing_category) is not int or
            not 0 <= closing_category <= 0xffffffff):
        raise ValueError('Expected explicit closed-control fixture values')
    if queued_suffix is not None and (not closed_ui or type(queued_suffix) is not bytes or
                                      len(record) + len(queued_suffix) > 0xc00):
        raise ValueError('Receive fixture requires closed UI and a bounded decoded queue')
    if wire_frame is not None and (queued_suffix is None or type(wire_frame) is not bytes or
                                  not 4 <= len(wire_frame) <= 0xa03 or
                                  struct.unpack_from('<H', wire_frame)[0] != len(wire_frame)):
        raise ValueError('Expected one bounded recovered wire envelope')
    n = NativeRun()
    packet = PACKET_PAGE + 4096 - len(record)
    n.put(packet, record)
    n.put(CONTEXT, b'\xa5' * 0x3ec)
    n.put32(SP + 0x1704, CONTEXT)
    n.put32(SP + 0x2c, 3)
    n.registers(ebx=packet, ebp=WORLD)
    ranges = [(0x68b4e, 0x68b68), (0x6ae12, 0x6ae4d)]
    stops = {0x6ae2d}
    if negative_handles or closed_ui:
        n.put(UI + 0x232e7c, b'\xff' * 30)
        n.put32(UI + 0x232ebc, 0x6400000)
        ranges += [(0x857e0, 0x85852), (0x6d340, 0x6d3ee), (0x6e490, 0x6e4ff)]
        stops = {0x6ae34, 0x6d376, 0x6e4c8}
    if closed_ui:
        control = 0x6401000
        n.put32(UI + 0x574c0, control)
        n.put32(control + 0x24, 0)
        for offset in (0x232e16, 0x232e20, 0x232dd2, 0x232e08,
                       0x232e5e, 0x232dd8, 0x232dae, 0x232e3e,
                       0x232e46, 0x232e36, 0x232e38, 0x232e56,
                       0x232dce, 0x232dd0, 0x855f0, 0xa3d02,
                       0xa4158, 0x57960):
            n.put(UI + offset, struct.pack('<h', closed_handle))
        n.put(UI + 0x88790, b'\0\0')
        n.put32(UI + 0x23d5e4, closing_category)
        n.put32(UI + 0x23d5e8, 0xa5a5a5a5)
        # Native BC2E0 writes this data global. Code pages remain read/execute.
        n.vm.mem_protect(0x592000, 4096, UC_PROT_READ | UC_PROT_WRITE)
        n.put(0x5926b0, b'\x34\x12')
        ranges += [(0x814f0, 0x8158f), (0xec3c0, 0xec447),
                   (0xf1900, 0xf1956), (0x71390, 0x71482),
                   (0xf7eb0, 0xf80bc), (0x9c190, 0x9c24a),
                   (0x9dd40, 0x9de2f), (0x6f3d0, 0x6f42e),
                   (0x77750, 0x7778d), (0xc4c50, 0xc4d12),
                   (0xf6410, 0xf644d), (0xbc2a0, 0xbc2f1),
                   (0x7c9e0, 0x7cac9), (0xc9bd0, 0xc9c57),
                   (0xa7550, 0xa75c4)]
        stops = {0x6b517}

    def packet_read(vm, access, address, size, value, _):
        if PACKET_PAGE <= address < PACKET_PAGE + 4096:
            if not packet <= address or address + size > packet + len(record):
                raise AssertionError('Read outside supplied logical record')

    n.vm.hook_add(UC_HOOK_MEM_READ, packet_read)
    if queued_suffix is None:
        return n.run(0x68b4e, ranges, stops)

    logical = record + queued_suffix
    n.map(NET, 0x5000)
    if wire_frame is None:
        n.put(NET + 0x758 + 0xc10, logical)
        n.put32(NET + 0x758 + 0x1810, len(logical))
        n.put32(NET + 0x758 + 0x1814, 0)
    else:
        codec, source = NET + 0x758, 0x6b00000
        n.registers(ecx=codec, esp=SP)
        n.put32(SP, RETURN)
        n.run(0x10490, [(0x10370, 0x104f6)], set(), budget=100000)
        n.put32(codec + 8, 1)
        n.put(source, wire_frame)
        n.put(SP, struct.pack('<3I', RETURN, source, len(wire_frame)))
        n.registers(ecx=codec, esp=SP)
        n.run(0x10ab0, [(0x10670, 0x10774), (0x10910, 0x10914),
                       (0x10a10, 0x10ae4)], set(), budget=100000)
        count = n.get32(codec + 0x1810)
        if (n.vm.reg_read(UC_X86_REG_EAX) != len(logical) or count != len(logical) or
                bytes(n.vm.mem_read(codec + 0xc10, count)) != logical):
            raise ValueError('Original frame decoder rejected or disagreed with supplied logical fixture')
        n.registers(esp=SP)
        n.put32(SP, RETURN)
    n.put(NET + 0x2cb8, b'\x01')
    n.put32(NET + 0x2cc0, 0)
    n.put32(WORLD + 0xa7e05e0, NET)
    n.put32(WORLD + 0x15396840, 1)
    n.put32(WORLD + 0xaa25ed4, 0)
    n.vm.mem_protect(0x5b4000, 4096, UC_PROT_READ | UC_PROT_WRITE)
    n.put32(0x5b4da8, 0)  # Explicit disabled native diagnostic file handle.
    n.put32(SP + 4, CONTEXT)
    n.registers(ecx=WORLD, ebx=0xdeadbe01, ebp=0xdeadbe02,
                esi=0xdeadbe03, edi=0xdeadbe04)
    ranges += [(0x68ae0, 0x68b68), (0x6b517, 0x6b5d3),
               (0x147b50, 0x147b7f), (0x13420, 0x135d1),
               (0x13650, 0x1368b), (0x15af0, 0x15b4b),
               (0x12520, 0x12554), (0x10af0, 0x10b68),
               (0x15840, 0x15850), (0x1000, 0x1013), (0x1200, 0x1324)]
    return n.run(0x68ae0, ranges, {0x10d20})


def state_tail():
    """Independent suffix: assumes all three preceding calls returned."""
    n = NativeRun()
    n.put32(SP + 0x2c, 3)
    return n.run(0x6ae40, [(0x6ae40, 0x6ae4d)], {0x6b517})


def main_state_selector(record):
    """Independent main-loop return=4 fixture; stop before 66920."""
    record_fields(record)
    n = NativeRun()
    n.put(SP + 0x238, b'\xa5' * 0x3ec)
    n.put(SP + 0x260, record[1:])
    n.put32(WORLD + 0xa7e05e0, NET)
    n.put32(NET + 0x40d4, 0)  # Explicit absent optional connection object.
    n.registers(eax=4, ebx=WORLD)
    return n.run(0x65653, [(0x65638, 0x65644), (0x65653, 0x656a0)], {0x6569b})


def initialization_prefix(context):
    """Independent 1112C0 entry fixture, stopping before 181B0 at 1113D8."""
    if type(context) is not bytes or len(context) != 0x3ec:
        raise ValueError('Expected explicit 0x3EC-byte transition context')
    n = NativeRun()
    n.put(CONTEXT, context)
    n.put(DESCRIPTOR, struct.pack('<7I', ROOT_OBJECT, CONTEXT, UI,
                                  0x6500000, RESOURCES, 0, 0x6600000))
    for offset, value in ((0x428, 0x6700000), (0x424, 0x6800000),
                          (0x42c, RENDERER), (0x438, NET)):
        n.put32(ROOT_OBJECT + offset, value)
    n.put32(RENDERER + 0xa0, 0x6900000)
    n.put32(RENDERER + 0xac, 0x6a00000)
    n.put32(BATTLE + 0x28, RESOURCES)
    n.put(RESOURCES + 0xb2c6c, b'\0\0')  # Explicit empty string table.
    n.map(BATTLE, 0x1000)
    n.map(BATTLE + 0xa9ea4c8, 4)
    n.map(BATTLE + 0x144964, 4)
    n.vm.mem_protect(0x5b8000, 4096, UC_PROT_READ | UC_PROT_WRITE)
    n.put32(SP + 4, DESCRIPTOR)
    n.registers(ecx=BATTLE)
    return n.run(0x1112c0, [(0x1112c0, 0x1113dd)], {0x1113d8})


def world_descriptor_prefix():
    """Original main-loop descriptor construction, before state dispatch."""
    n = NativeRun()
    for offset, value in ((0xa7e05c4, ROOT_OBJECT), (0xaa3647c, 0x6500000),
                          (0xaa36480, RESOURCES)):
        n.put32(WORLD + offset, value)
    n.registers(ecx=WORLD)
    return n.run(0x655e0, [(0x655e0, 0x65638)], {0x65638})


def initialization_copy(context):
    """Independent post-service copy island; stop before 11FC40 at 111424."""
    if type(context) is not bytes or len(context) != 0x3ec:
        raise ValueError('Expected explicit 0x3EC-byte transition context')
    n = NativeRun()
    n.put(CONTEXT, context)
    n.put(BATTLE, b'\xcc' * 0x500)
    n.registers(ebx=CONTEXT, ebp=BATTLE, esi=CONTEXT, edi=BATTLE + 0x48)
    return n.run(0x111409, [(0x111409, 0x111429)], {0x111424})


def battle_dispatch(opcode):
    """Independent post-queue switch; stop before executing selected case."""
    if type(opcode) is not int or not 0 <= opcode <= 255:
        raise ValueError('Expected byte opcode')
    n = NativeRun()
    n.put(PACKET_PAGE, bytes([opcode]))
    n.registers(ebp=PACKET_PAGE, eax=0xdeadbe00)
    targets = {struct.unpack_from('<I', n.image, 0x114634 + 4 * i)[0] - BASE
               for i in range(10)}
    targets.add(0x1145c0)
    return n.run(0x114332, [(0x114332, 0x114358)], targets)


def report():
    record = bytes([OPCODE]) + struct.pack('<II', 0x12345678, 0x9abcdeff)
    entry = world_entry(record)
    cleanup = world_entry(record, negative_handles=True)
    closed = world_entry(record, closed_ui=True)
    context = bytes(entry.vm.mem_read(CONTEXT, 0x3ec))
    prefix = initialization_prefix(context)
    copied = initialization_copy(context)
    return {
        'sha256': IMAGE_SHA256, 'base': hex(BASE), 'opcode': hex(OPCODE),
        'logical_size': native_length(), 'fields': list(record_fields(record)),
        'world_stop_before_call': hex(entry.stop), 'next_callee': '0x857e0',
        'negative_handles_stop_before_call': hex(cleanup.stop), 'next_cleanup': '0x814f0',
        'closed_ui_dispatch_stop': hex(closed.stop),
        'closed_ui_continuous_state': closed.get32(SP + 0x2c),
        'closed_ui_requires_explicit_inactive_controls': True,
        'independent_state_tail': state_tail().get32(SP + 0x2c),
        'independent_main_stop': hex(main_state_selector(record).stop),
        'independent_init_prefix_stop': hex(prefix.stop),
        'independent_init_copy_stop': hex(copied.stop),
        'battle_fields': [copied.get32(BATTLE + 0x3c), copied.get32(BATTLE + 0x40)],
        'battle_dispatch_82_target': hex(battle_dispatch(OPCODE).stop),
        'continuous_world_to_battle_proven': False, 'runtime_mutation_enabled': False,
    }


if __name__ == '__main__':
    print(json.dumps(report(), indent=2))
