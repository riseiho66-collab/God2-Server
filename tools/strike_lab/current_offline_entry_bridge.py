"""Pinned ABI boundaries and bytes for a debugger-owned offline experiment.

No process access, launcher, code patching, or emulated world implementation.
"""
import hashlib
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[2]
IMAGE = ROOT / 'artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin'
SHA256 = '149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
BASE = 0x400000
GUARDS = {
    0xded8: '39 bd 3c 04 00 00',
    0xef75: 'e8 96 59 05 00',
    0xef7a: '8b 4c 24 34 5f 5e 64 89 0d 00 00 00 00 83 c4 38 c3',
    0xe0f2: '8b 8d 40 04 00 00 e8 e3 74 05 00',
    0xe0fd: '89 44 24 10',
    0xe165: '8b 4c 24 10 8d 41 ff',
    0xe2aa: '8b 8c 24 78 03 00 00 5f 5e 5d 33 c0 5b 64 89 0d 00 00 00 00 81 c4 74 03 00 00 c2 04 00',
    0x655bc: '8b 8c 24 64 02 00 00 5f 5e 5d 5b 64 89 0d 00 00 00 00 81 c4 60 02 00 00 c2 18 00',
}


def pinned_image():
    image = IMAGE.read_bytes()
    if hashlib.sha256(image).hexdigest() != SHA256:
        raise ValueError('Current native image hash changed')
    for rva, expected in GUARDS.items():
        value = bytes.fromhex(expected)
        if image[rva:rva + len(value)] != value:
            raise ValueError(f'Native boundary changed at {rva:X}')
    return image


def loop_trampoline(application=0x5e00f8):
    """After EEE0: bind the original global, call the real loop, then break.

    No DE80 frame is assumed. Pending WinMain display argument is left intact.
    The debugger must check app/world prerequisites before entry. UD2 prevents
    falling through if the deliberate return INT3 is accidentally continued.
    """
    return (bytes.fromhex('ff 35') + struct.pack('<I', application + 0x438)
            + bytes.fromhex('b8')
            + struct.pack('<I', BASE + 0x2b00)
            + bytes.fromhex('ff d0 83 c4 04 8b 0d')
            + struct.pack('<I', application + 0x440) + b'\xb8'
            + struct.pack('<I', BASE + 0x655e0)
            + bytes.fromhex('ff d0 cc 0f 0b'))


def boundary_probe():
    """Execute only original prologues, call setup and epilogues.

    Stopping at 64910 does not execute that initializer. Its return/epilogue
    test uses an explicit sentinel EAX, never a simulated successful login.
    """
    packages = str(ROOT / 'artifacts/tooling/crypto-oracle-python')
    if packages not in sys.path:
        sys.path.insert(0, packages)
    from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_PROT_READ, UC_PROT_EXEC
    from unicorn.x86_const import (UC_X86_REG_EAX, UC_X86_REG_EBP,
                                  UC_X86_REG_EBX, UC_X86_REG_ECX,
                                  UC_X86_REG_EDI, UC_X86_REG_ESI,
                                  UC_X86_REG_ESP, UC_X86_REG_EIP)
    image = pinned_image()
    vm = Uc(UC_ARCH_X86, UC_MODE_32)
    vm.mem_map(BASE, len(image))
    vm.mem_write(BASE, image)
    vm.mem_protect(BASE, len(image), UC_PROT_READ | UC_PROT_EXEC)
    stack, app, world = 0x2000000, 0x3000000, 0x5000000
    vm.mem_map(0, 0x1000)
    vm.mem_map(stack, 0x10000)
    vm.mem_map(app, 0x120000)
    sp, stop = stack + 0x8000, stack + 0x1000

    def words(address, *values):
        vm.mem_write(address, struct.pack('<' + 'I' * len(values), *values))

    def read_words(address, count=1):
        return struct.unpack('<' + 'I' * count, vm.mem_read(address, 4 * count))

    def run(start, end):
        vm.emu_start(start, end, count=30000)
        if vm.reg_read(UC_X86_REG_EIP) != end:
            raise AssertionError('Boundary instruction budget exhausted')

    saved = {UC_X86_REG_EBX: 0x11112222, UC_X86_REG_EBP: 0x33334444,
             UC_X86_REG_ESI: 0x55556666, UC_X86_REG_EDI: 0x77778888}
    for register, value in saved.items():
        vm.reg_write(register, value)
    words(0, 0xffffffff)
    words(sp, stop, 1)
    vm.reg_write(UC_X86_REG_ESP, sp)
    vm.reg_write(UC_X86_REG_ECX, app)
    run(BASE + 0xde80, BASE + 0xded8)
    frame = vm.reg_read(UC_X86_REG_ESP)
    assert frame == sp - 0x384
    assert vm.reg_read(UC_X86_REG_EBP) == app
    assert vm.reg_read(UC_X86_REG_EBX) == app + 0xa4
    assert vm.reg_read(UC_X86_REG_EDI) == vm.reg_read(UC_X86_REG_ESI) == 0
    assert read_words(app + 0xa4) == (0,)
    run(BASE + 0xe2aa, stop)
    assert vm.reg_read(UC_X86_REG_ESP) == sp + 8
    assert read_words(0) == (0xffffffff,)
    assert all(vm.reg_read(r) == v for r, v in saved.items())

    outer = sp - 0x40
    words(sp, stop)
    words(outer, saved[UC_X86_REG_EDI], saved[UC_X86_REG_ESI])
    words(outer + 0x34, 0xffffffff)
    vm.reg_write(UC_X86_REG_ESP, outer)
    vm.reg_write(UC_X86_REG_ESI, app)
    vm.reg_write(UC_X86_REG_EAX, world)
    run(BASE + 0xef52, BASE + 0x64910)
    entry = vm.reg_read(UC_X86_REG_ESP)
    call = read_words(entry, 7)
    assert call == (BASE + 0xef7a, app, outer + 0xc, app + 0xa4, 0, 0, 1)
    assert vm.reg_read(UC_X86_REG_ECX) == world
    assert read_words(app + 0x440) == (world,)
    # Supply only the callee's return boundary, not its unexecuted behavior.
    vm.reg_write(UC_X86_REG_ESP, outer)
    vm.reg_write(UC_X86_REG_EAX, 0x87654321)
    run(BASE + 0xef7a, stop)
    assert vm.reg_read(UC_X86_REG_ESP) == sp + 4
    assert vm.reg_read(UC_X86_REG_EAX) == 0x87654321
    assert read_words(0) == (0xffffffff,)

    for offset in (0xa7e05c4, 0xaa3647c):
        vm.mem_map((world + offset) & ~0xfff, 0x1000)
    words(world + 0xa7e05c4, app)
    words(world + 0xaa3647c, 0x12340000, app + 0x444)
    words(sp, stop)
    vm.reg_write(UC_X86_REG_ESP, sp)
    vm.reg_write(UC_X86_REG_ECX, world)
    run(BASE + 0x655e0, BASE + 0x67860)
    loop_call = read_words(vm.reg_read(UC_X86_REG_ESP), 2)
    assert loop_call == (BASE + 0x65653, sp - 0x7ec)
    assert vm.reg_read(UC_X86_REG_ECX) == world
    assert vm.reg_read(UC_X86_REG_ESP) == sp - 0xa2c
    return {'de80_frame_bytes': 0x384, 'eee0_arguments': call[1:],
            'first_loop_call': loop_call, 'world_initializer_executed': False,
            'loop_prefix_only': True, 'frame_function_executed': False}
