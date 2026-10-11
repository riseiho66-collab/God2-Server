"""Bounded current-image clock stages on an existing Unicorn VM.

Only explicit logical S2C1A and explicit timeGetTime DWORDs are inputs. The
writer returns normally; the C3080 clock consumer stops before C36AE's UI read.
No resource preload, UI execution, live clock, or replacement game functions.
"""
import hashlib
from pathlib import Path
import struct

from unicorn import (UC_HOOK_CODE, UC_HOOK_MEM_READ, UC_HOOK_MEM_WRITE,
                     UC_MEM_WRITE, UC_PROT_READ, UC_PROT_WRITE, UC_PROT_EXEC)
from unicorn import x86_const as x86


BASE = 0x400000
IMAGE = Path(__file__).resolve().parents[2] / (
    'artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin')
IMAGE_SHA = '149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
SOURCE_OFFSET, SOURCE_POINTER = 0x90, 0x86888
TIMESTAMP, VALUE = 0x44ac, 0x44b0
CHARACTER_SIZE = 0x469c
OPCODE, PACKET_LENGTH = 0x1a, 4
DISPATCH, WRITER, WRITER_RETURN = 0x6b022, 0xc35f0, 0x6b02f
UI_CALLER, CONSUMER, UI_BOUNDARY = 0xc3117, 0xc3640, 0xc36ae
SPLITTER, SPLITTER_END, FLOAT_TO_INT = 0xc3710, 0xc374f, 0x149630
CLOCK_IAT, CLOCK_TARGET = BASE + 0x1707bc, 0x74147860
FLOAT_SCALE = BASE + 0x171240
WRITER_RANGES = ((DISPATCH, WRITER_RETURN), (WRITER, 0xc363e))
CONSUMER_RANGES = ((UI_CALLER, 0xc311e), (CONSUMER, UI_BOUNDARY),
                   (SPLITTER, SPLITTER_END), (FLOAT_TO_INT, 0x149657))


def _dword(value, label):
    if type(value) is not int or not 0 <= value <= 0xffffffff:
        raise ValueError(f'Explicit unsigned DWORD {label} required')
    return value


class NativeWorldClock:
    """Caller-owned VM, owner, character root, stack and packet storage.

    ``owner+86888`` must already equal ``character+90``. Only the pointer slot
    and eight clock bytes need mapping, not the full objects. ``sp`` requires
    RW [sp-100,sp+100); ``packet`` requires four RW bytes. Scratch must be
    dedicated, disjoint from live data. CPU (including x87), scratch stack and
    packet bytes are restored even on failure. Successful native writer stores
    persist. An interrupted writer may have partial stores; no receipt is issued.

    Call only while the VM is stopped, outside an active emu_start/hook. Existing
    hooks remain installed. The OS entry is an emulation stop, so an older host
    clock hook cannot silently replace this helper's explicit external input.
    """

    def __init__(self, vm, *, owner, character, sp, packet):
        self.image = IMAGE.read_bytes()
        if hashlib.sha256(self.image).hexdigest() != IMAGE_SHA:
            raise ValueError('Unqualified current image')
        self.vm = vm
        self.owner = _dword(owner, 'owner address')
        self.character = _dword(character, 'character address')
        self.sp = _dword(sp, 'scratch stack address')
        self.packet = _dword(packet, 'packet address')
        self.source = character + SOURCE_OFFSET
        self._written_state = None
        self._check_layout()

    def _mapped(self, lo, hi, permission):
        if not 0 <= lo < hi <= 2**32:
            raise ValueError('Clock storage outside 32-bit bounds')
        cursor = lo
        for a, z, protection in sorted(self.vm.mem_regions()):
            if a <= cursor <= z and protection & permission == permission:
                cursor = min(hi, z + 1)
            if cursor == hi:
                return
        raise ValueError('Clock storage unmapped or lacks permissions')

    def _check_layout(self):
        spans = ((self.character, self.character + CHARACTER_SIZE),
                 (self.owner + SOURCE_POINTER, self.owner + SOURCE_POINTER + 4),
                 (self.sp - 0x100, self.sp + 0x100),
                 (self.packet, self.packet + PACKET_LENGTH),
                 (BASE, BASE + len(self.image)))
        for i, (lo, hi) in enumerate(spans):
            if not 0 <= lo < hi <= 2**32:
                raise ValueError('Clock storage outside 32-bit bounds')
            if any(lo < z and a < hi for a, z in spans[:i]):
                raise ValueError('Clock storage spans overlap')
        for lo, hi in spans[2:4]:
            self._mapped(lo, hi, UC_PROT_READ | UC_PROT_WRITE)

    def _binding(self, *, writing=False):
        slot = self.owner + SOURCE_POINTER
        self._mapped(slot, slot + 4, UC_PROT_READ)
        self._mapped(self.source + TIMESTAMP, self.source + VALUE + 4,
                     UC_PROT_READ | (UC_PROT_WRITE if writing else 0))
        if struct.unpack('<I', self.vm.mem_read(slot, 4))[0] != self.source:
            raise ValueError('Original owner packet-source binding required')

    def _state(self):
        return bytes(self.vm.mem_read(self.source + TIMESTAMP, 8))

    def _verify(self, ranges, *, clock):
        for first, last in ranges:
            self._mapped(BASE + first, BASE + last, UC_PROT_READ | UC_PROT_EXEC)
            if bytes(self.vm.mem_read(BASE + first, last - first)) != self.image[first:last]:
                raise ValueError('Original executable bytes changed in supplied VM')
        if clock:
            for address in (CLOCK_IAT, FLOAT_SCALE):
                self._mapped(address, address + 4, UC_PROT_READ)
                if bytes(self.vm.mem_read(address, 4)) != self.image[address-BASE:address-BASE+4]:
                    raise ValueError('Pinned clock import or arithmetic constant changed')

    def _run(self, start, stop, ranges, *, registers, arguments=(), clock_ms=None,
             raw=None, readable=(), writable=()):
        self._check_layout()
        self._verify(ranges, clock=clock_ms is not None)
        vm = self.vm
        stack_span = (self.sp - 0x100, self.sp + 0x100)
        readable = (stack_span, *readable)
        writable = (stack_span, *writable)
        if clock_ms is not None:
            readable += ((CLOCK_IAT, CLOCK_IAT + 4), (FLOAT_SCALE, FLOAT_SCALE + 4))
        saved = vm.context_save()
        stack = bytes(vm.mem_read(stack_span[0], 0x200))
        packet = bytes(vm.mem_read(self.packet, PACKET_LENGTH))
        trace = {'start': start, 'stop': stop, 'pcs': [], 'reads': [], 'writes': [],
                 'clock_calls': [], 'packet': raw, 'external_clock_ms': clock_ms}
        self.last_trace = trace
        hooks, mapped_clock = [], False

        def code(vm, address, size, _):
            rva = address - BASE
            if rva == stop:
                vm.emu_stop()
                return
            if not any(a <= rva and rva + size <= z for a, z in ranges):
                raise AssertionError(f'Unqualified clock-stage PC {rva:X}')
            trace['pcs'].append(rva)
            if len(trace['pcs']) > 512:
                raise AssertionError('Clock instruction bound exhausted')

        def memory(vm, access, address, size, value, _):
            pc = vm.reg_read(x86.UC_X86_REG_EIP) - BASE
            writing = access == UC_MEM_WRITE
            allowed = writable if writing else readable
            if not any(a <= address and address + size <= z for a, z in allowed):
                raise AssertionError(f'Unqualified clock-stage memory access {address:X}/{size}')
            if not writing:
                value = int.from_bytes(vm.mem_read(address, size), 'little')
            trace['writes' if writing else 'reads'].append((pc, address, size, value))

        try:
            if clock_ms is not None and not any(a <= CLOCK_TARGET <= z for a, z, _ in vm.mem_regions()):
                vm.mem_map(CLOCK_TARGET & ~4095, 4096, UC_PROT_READ | UC_PROT_EXEC)
                mapped_clock = True
            if raw is not None:
                vm.mem_write(self.packet, raw)
            vm.mem_write(self.sp, struct.pack('<' + 'I' * (len(arguments) + 1),
                                             BASE + stop, *arguments))
            vm.reg_write(x86.UC_X86_REG_ESP, self.sp)
            vm.reg_write(x86.UC_X86_REG_EFLAGS, 2)
            # Explicit conventional x87 environment, independent of the caller.
            vm.reg_write(x86.UC_X86_REG_FPCW, 0x37f)
            vm.reg_write(x86.UC_X86_REG_FPSW, 0)
            vm.reg_write(x86.UC_X86_REG_FPTAG, 0xffff)
            for name, value in registers.items():
                vm.reg_write(getattr(x86, 'UC_X86_REG_' + name), value)
            hooks.append(vm.hook_add(UC_HOOK_CODE, code))
            hooks.append(vm.hook_add(UC_HOOK_MEM_READ | UC_HOOK_MEM_WRITE, memory))
            pc = BASE + start
            for _ in range(2):
                # Stop BEFORE the imported entry's hooks/instructions. The real
                # indirect CALL and its IAT read/return-address push still run.
                vm.emu_start(pc, CLOCK_TARGET if clock_ms is not None else BASE + stop,
                             count=512, timeout=1000000)
                pc = vm.reg_read(x86.UC_X86_REG_EIP)
                if pc == BASE + stop:
                    break
                if pc != CLOCK_TARGET or clock_ms is None or trace['clock_calls']:
                    raise AssertionError('Clock stage exhausted its execution bound')
                sp = vm.reg_read(x86.UC_X86_REG_ESP)
                if not stack_span[0] <= sp <= stack_span[1] - 4:
                    raise AssertionError('Clock adapter stack outside scratch')
                ret = struct.unpack('<I', vm.mem_read(sp, 4))[0]
                if ret != BASE + (0xc35f9 if start == DISPATCH else 0xc365d):
                    raise AssertionError('Unqualified imported clock caller')
                trace['clock_calls'].append({'name': 'WINMM!timeGetTime',
                    'iat': CLOCK_IAT, 'target': CLOCK_TARGET, 'value': clock_ms,
                    'return': ret, 'stack_read': (sp, 4, ret)})
                vm.reg_write(x86.UC_X86_REG_EAX, clock_ms)
                vm.reg_write(x86.UC_X86_REG_ESP, sp + 4)
                vm.reg_write(x86.UC_X86_REG_EIP, ret)
                pc = ret
            if vm.reg_read(x86.UC_X86_REG_EIP) != BASE + stop:
                raise AssertionError('Clock stage did not reach its exact boundary')
            if clock_ms is not None and len(trace['clock_calls']) != 1:
                raise AssertionError('Explicit clock input was not consumed exactly once')
            trace['registers'] = {name: vm.reg_read(getattr(x86, 'UC_X86_REG_' + name))
                                  for name in ('EAX', 'ECX', 'EDX', 'ESP', 'EIP')}
            if start == SPLITTER:
                trace['hours'] = vm.mem_read(self.sp + 0x40, 1)[0]
                trace['minutes'] = vm.mem_read(self.sp + 0x44, 1)[0]
        finally:
            for hook in hooks:
                vm.hook_del(hook)
            vm.mem_write(stack_span[0], stack)
            vm.mem_write(self.packet, packet)
            vm.context_restore(saved)
            if mapped_clock:
                vm.mem_unmap(CLOCK_TARGET & ~4095, 4096)
        return trace

    def write_clock(self, raw, *, clock_ms):
        """Execute 6B022 -> complete C35F0 -> 6B02F; retain only native stores.

        Logical packet is [1A, byte, byte, byte]. All 0..255 payload values are
        accepted as by the original writer; there is no invented civil-time gate.
        """
        if type(raw) is not bytes or len(raw) != PACKET_LENGTH or raw[0] != OPCODE:
            raise ValueError('Explicit 4-byte logical S2C1A required')
        _dword(clock_ms, 'external clock_ms')
        self._binding(writing=True)
        self._written_state = None
        trace = self._run(DISPATCH, WRITER_RETURN, WRITER_RANGES,
            registers={'EBX': self.packet, 'EBP': (self.owner - 0xa7f2f6c) & 0xffffffff},
            clock_ms=clock_ms, raw=raw,
            readable=((self.owner + SOURCE_POINTER, self.owner + SOURCE_POINTER + 4),
                      (self.packet, self.packet + PACKET_LENGTH)),
            writable=((self.source + TIMESTAMP, self.source + VALUE + 4),))
        if trace['registers']['ESP'] != self.sp:
            raise AssertionError('Original packet writer stack imbalance')
        self._written_state = self._state()
        trace['state'] = self._written_state
        trace['timestamp'], trace['value'] = struct.unpack('<II', trace['state'])
        trace['outcome'] = 'writer_returned'
        return trace

    def read_clock(self, *, clock_ms, state=None):
        """Actual C3080 call at C3119, through C3640/C3710, before UI C36AE.

        Requires this instance's successful writer receipt, or an explicit
        eight-byte timestamp/value snapshot equal to the current VM bytes.
        Supplying a snapshot asserts input provenance; it does not write memory.
        """
        _dword(clock_ms, 'external clock_ms')
        self._binding()
        expected = self._written_state if state is None else state
        if type(expected) is not bytes or len(expected) != 8:
            raise ValueError('Explicit clock source state or original writer receipt required')
        if self._state() != expected:
            raise ValueError('Clock source state differs from explicit input or writer receipt')
        trace = self._run(UI_CALLER, UI_BOUNDARY, CONSUMER_RANGES,
            registers={'ESI': self.owner}, clock_ms=clock_ms,
            readable=((self.owner + SOURCE_POINTER, self.owner + SOURCE_POINTER + 4),
                      (self.source + TIMESTAMP, self.source + VALUE + 4)))
        trace['hours'] = trace['registers']['EAX'] & 0xff
        trace['minutes'] = trace['registers']['EDX'] & 0xff
        trace['state'] = expected
        trace['outcome'] = 'before_ui_handle_read'
        return trace

    def split_clock(self, value):
        """Execute full C3710 for an explicit unsigned DWORD; no UI or clock."""
        _dword(value, 'clock value')
        return self._run(SPLITTER, SPLITTER_END, ((SPLITTER, SPLITTER_END),),
            registers={}, arguments=(value, self.sp + 0x40, self.sp + 0x44))
