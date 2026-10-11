"""Bounded current-original character writers and battle source binding.

All stages run on the supplied VM. No UI, imports, game replacements, archived
fixtures, or implicit character defaults. These stages do not qualify later
skill-list reads or constitute a complete world/battle initialization.
"""
import hashlib
from pathlib import Path
import struct

from unicorn import (UC_HOOK_CODE, UC_HOOK_MEM_READ, UC_HOOK_MEM_WRITE,
                     UC_MEM_WRITE, UC_PROT_READ, UC_PROT_WRITE)
from unicorn import x86_const as x86


BASE = 0x400000
IMAGE_SHA = '149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
IMAGE = Path(__file__).resolve().parents[2] / (
    'artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin')
CHARACTER_ROOT = 0x8520000
ROOT_SIZE, SOURCE_OFFSET = 0x469c, 0x90
CURRENT_OFFSET, COUNT_OFFSET, ROWS_OFFSET, ROW_STRIDE = 0xcf, 0xd4, 0xd8, 0x3ec
ROW_COUNT = 16
CONSUMER_ENTRY, CONSUMER_STOP = 0x11bb80, 0x11bc2a


class NativeBattleCharacterBinding:
    """Use explicit caller-owned mappings and a dedicated scratch stack/packet.

``root`` is the actor base, not its +90 source. ``ui`` needs the pointer slot
at +86888 and the opaque read at +86874 mapped. ``sp`` needs 0x100 bytes below
and 0x100 bytes above; ``packet`` needs 29 bytes. Scratch must not overlap live
caller data. The helper restores CPU context, but intentionally retains native
memory writes and its scratch-stack/packet writes.
"""

    def __init__(self, vm, *, root, ui, sp, packet):
        image = IMAGE.read_bytes()
        if hashlib.sha256(image).hexdigest() != IMAGE_SHA:
            raise ValueError('Unqualified current image')
        self.vm, self.image = vm, image
        self.root, self.source = root, root + SOURCE_OFFSET
        self.ui, self.sp, self.packet = ui, sp, packet

    def u32(self, address):
        return struct.unpack('<I', self.vm.mem_read(address, 4))[0]

    def prepare_new_root(self, snapshot):
        """Map a NEW actor from an explicit snapshot; never invent missing bytes."""
        if type(snapshot) is not bytes or len(snapshot) != ROOT_SIZE:
            raise ValueError('Explicit 0x469C-byte actor snapshot required')
        lo, hi = self.root & ~4095, (self.root + ROOT_SIZE + 4095) & ~4095
        if any(a < hi and lo <= z for a, z, _ in self.vm.mem_regions()):
            raise ValueError('New actor mapping overlaps existing VM memory')
        self.vm.mem_map(lo, hi - lo, UC_PROT_READ | UC_PROT_WRITE)
        self.vm.mem_write(lo, b'\xa5' * (hi - lo))
        self.vm.mem_write(self.root, snapshot)

    def _run(self, start, stop, ranges, *, registers, arguments=(), writable=()):
        # Compare executable bytes in THIS VM, not just the on-disk identity.
        for first, last in ranges:
            if bytes(self.vm.mem_read(BASE + first, last - first)) != self.image[first:last]:
                raise ValueError('Original executable bytes changed in supplied VM')
        saved = self.vm.context_save()
        trace = {'start': start, 'stop': stop, 'pcs': [], 'reads': [], 'writes': []}
        hooks = []

        def code(vm, address, size, _):
            rva = address - BASE
            if rva == stop:
                vm.emu_stop()
                return
            if not any(a <= rva and rva + size <= z for a, z in ranges):
                raise AssertionError(f'Unqualified character-stage PC {rva:X}')
            trace['pcs'].append(rva)

        def memory(vm, access, address, size, value, _):
            pc = vm.reg_read(x86.UC_X86_REG_EIP) - BASE
            if access == UC_MEM_WRITE:
                allowed = ((self.sp - 0x100, self.sp + 0x100), *writable)
                if not any(a <= address and address + size <= z for a, z in allowed):
                    raise AssertionError(f'Unqualified character-stage write {address:X}')
                trace['writes'].append((pc, address, size, value))
            else:
                trace['reads'].append((pc, address, size))

        try:
            self.vm.mem_write(self.sp, struct.pack('<' + 'I' * (len(arguments) + 1),
                                                   self.sp + 0x80, *arguments))
            self.vm.reg_write(x86.UC_X86_REG_ESP, self.sp)
            self.vm.reg_write(x86.UC_X86_REG_EFLAGS, 2)
            for name, value in registers.items():
                self.vm.reg_write(getattr(x86, 'UC_X86_REG_' + name), value)
            hooks = [self.vm.hook_add(UC_HOOK_CODE, code),
                     self.vm.hook_add(UC_HOOK_MEM_READ | UC_HOOK_MEM_WRITE, memory)]
            self.vm.emu_start(BASE + start, BASE + stop, count=30000, timeout=1000000)
            if self.vm.reg_read(x86.UC_X86_REG_EIP) != BASE + stop:
                raise AssertionError('Character stage exhausted its execution bound')
            trace['registers'] = {name: self.vm.reg_read(getattr(x86, 'UC_X86_REG_' + name))
                                  for name in ('EAX', 'ECX', 'EDX', 'EBP', 'ESI', 'EDI', 'ESP')}
        finally:
            for hook in hooks:
                self.vm.hook_del(hook)
            self.vm.context_restore(saved)
        return trace

    def reset_rows(self):
        """Original 68120 reset only; stop before 97FE0 UI-array clearing.

Zero count/rows and FF selection here are native writes, never preparation
defaults. Existing actor statistics outside the reset footprint survive.
"""
        return self._run(0x68120, 0x6814a, ((0x68120, 0x6814a),),
                         registers={'ECX': self.ui}, arguments=(self.root,),
                         writable=((self.root + 0x15f, self.root + 0x165),
                                   (self.root + 0x168, self.root + 0x4028)))

    def bind_packet_source(self):
        """Explicit stages: original actor+90 calculation, then original store.

The UI work between 81C87 and 81D0A is not executed or claimed. The captured
EDI value is used within this same VM; no character memory is transplanted.
"""
        derive = self._run(0x81c81, 0x81c87, ((0x81c81, 0x81c87),),
                           registers={'EBX': self.root})
        publish = self._run(0x81d0a, 0xe7cb1,
                            ((0x81d0a, 0x81d12), (0xe7c80, 0xe7cb1)),
                            registers={'EDI': derive['registers']['EDI'], 'ESI': self.ui},
                            writable=((self.ui + 0x86888, self.ui + 0x8688c),))
        if self.u32(self.ui + 0x86888) != self.source:
            raise AssertionError('Original packet-source binding differs')
        return derive, publish

    def _packet_stage(self, raw, opcode, length, start, stop, ranges):
        if type(raw) is not bytes or len(raw) != length or raw[0] != opcode:
            raise ValueError(f'Explicit {length}-byte logical S2C{opcode:02X} required')
        if self.u32(self.ui + 0x86888) != self.source:
            raise ValueError('Original packet-source binding is required first')
        self.vm.mem_write(self.packet, raw)
        return self._run(start, stop, ranges,
                         registers={'EBX': self.packet, 'EBP': (self.ui - 0xa7f2f6c) & 0xffffffff},
                         writable=((self.root, self.root + ROOT_SIZE),))

    def append_named_row(self, raw):
        """Original S2C30 packet-name branch, stopped before refresh AA1B5.

Requires explicit signed-byte keys with magnitude 100..127, a terminated
16-byte name and flag !=1. Other keys need original 59A60 metadata lookup;
flag 1 has duplicate/skill-count behavior outside this bounded append stage.
No packet or owned row is manufactured by this helper.
"""
        if type(raw) is not bytes or len(raw) != 19 or raw[0] != 0x30:
            raise ValueError('Explicit 19-byte logical S2C30 required')
        key = abs(struct.unpack_from('<b', raw, 1)[0])
        if not 100 <= key <= 127:
            raise ValueError('This key needs original 59A60 name metadata; packet-name branch only')
        if b'\0' not in raw[2:18] or raw[18] == 1:
            raise ValueError('Terminated explicit name and non-duplicate flag required')
        if self.vm.mem_read(self.source + COUNT_OFFSET, 1)[0] >= ROW_COUNT:
            raise ValueError('Original append requires fewer than sixteen existing rows')
        return self._packet_stage(raw, 0x30, 19, 0x69f85, 0xaa1b5,
                                  ((0x69f85, 0x69f92), (0xaa040, 0xaa1b5)))

    def write_role_scalars(self, raw):
        return self._packet_stage(raw, 0x22, 25, 0x69ef0, 0xe6bd4,
                                  ((0x69ef0, 0x69efd), (0xe6b40, 0xe6bd4)))

    def write_role_current_vitals(self, raw):
        """Original S2C2B role stores only, before refresh and companion update."""
        return self._packet_stage(raw, 0x2b, 21, 0x69eb0, 0xe63c5,
                                  ((0x69eb0, 0x69ebf), (0xe6390, 0xe63c5)))

    def write_row_scalars(self, raw):
        if type(raw) is not bytes or len(raw) != 29 or raw[0] != 0x31:
            raise ValueError('Explicit 29-byte logical S2C31 required')
        count = self.vm.mem_read(self.source + COUNT_OFFSET, 1)[0]
        key = struct.unpack_from('<b', raw, 1)[0]
        if count > ROW_COUNT or not any(struct.unpack('<h', self.vm.mem_read(
                self.source + ROWS_OFFSET + i * ROW_STRIDE, 2))[0] == key for i in range(count)):
            raise ValueError('S2C31 needs an existing matching row within sixteen rows')
        return self._packet_stage(raw, 0x31, 29, 0x69fa9, 0xaa2af,
                                  ((0x69fa9, 0x69fb6), (0xaa200, 0xaa2af)))

    def bind_descriptor(self, descriptor):
        """Stage argument wiring only; leave battle+14 to original 111326."""
        self.vm.mem_read(self.root, ROOT_SIZE)
        self.vm.mem_write(descriptor + 0x10, struct.pack('<I', self.root))

    def publish_battle_source(self, *, descriptor, battle):
        if self.u32(descriptor + 0x10) != self.root:
            raise ValueError('Descriptor does not point at this character root')
        return self._run(0x111323, 0x111329, ((0x111323, 0x111329),),
                         registers={'ECX': descriptor, 'EBP': battle},
                         writable=((battle + 0x14, battle + 0x18),))

    def prove_consumer_prefix(self, *, battle):
        """Execute the actual 1116A4 call, stop after the two source-byte reads.

        Caller must supply the battle fields and selector storage used here.
        ESI is staged as PANELS (battle+A9EA59C), as produced at 11162D;
        it is distinct from the packet-routing owner ``self.ui``.
No source row contents or skill lists are read by this prefix. Main should
resume its own pending call separately; CPU context is restored here.
"""
        if self.u32(battle + 0x14) != self.root:
            raise ValueError('Original battle source publication required')
        return self._run(0x111667, CONSUMER_STOP,
                         ((0x111667, 0x1116a9), (CONSUMER_ENTRY, CONSUMER_STOP)),
                         registers={'EBP': battle, 'ESI': battle + 0xa9ea59c},
                         writable=((battle + 0xa9dc198, battle + 0xa9dc198 + 0x351c),))
