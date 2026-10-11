"""Same-VM current map catalog and image-owned map-panel metadata.

Call only on a stopped native host, outside emu_start/hooks. The existing
owner+CFF70 binding is required and never replaced. No battle preload runs.
"""
from collections import Counter
from contextlib import contextmanager
import hashlib
import re
import struct

from unicorn import (UC_HOOK_BLOCK, UC_HOOK_CODE, UC_HOOK_MEM_READ,
                     UC_HOOK_MEM_WRITE, UC_MEM_WRITE, UC_PROT_READ, UC_PROT_WRITE)
from unicorn import x86_const as x86

from .current_battle_character_binding import BASE, IMAGE, IMAGE_SHA
from .current_world_music import music_source, SOURCE, SOURCE_SHA, PLAIN_SHA, SECTION

OWNER_TABLE = 0xcff70
COUNT, POINTER, STRIDE, PANEL_METADATA = 0xd2aba, 0xd2abc, 0x1a4, 0x1a0
STATIC_RVA, STATIC_COUNT, STATIC_STRIDE = 0x18ac70, 143, 0x34
STATIC_END = STATIC_RVA + STATIC_COUNT * STATIC_STRIDE
PARSER_SIZE = 0x78 + 24 * 380
RETURN = BASE + 0x1000
DECODE_CODE = ((0x1ec0, 0x2021),)
LOAD_CODE = ((0x51920, 0x51958), (0x51a90, 0x51cd2),
             (0x565ab, 0x565f1), (0x59a80, 0x59d7f),
             (0x147b50, 0x147b7f), (0x147b80, 0x147c7e),
             (0x148990, 0x148a5c))
BIND_CODE = ((0x818d6, 0x818e1), (0x67ef0, 0x67f15), (0x59e70, 0x59ee6))
LOOKUP_CODE = ((0x59d80, 0x59df8),)
CONSUMER_CODE = ((0xc328b, 0xc32e2), *LOOKUP_CODE)
SERVICES = (0x1474ab, 0x1474dc, 0x14785c, 0x147a95, 0x147e23,
            0x1480b4, 0x151de0)
# Allocator results must also avoid these reservations if the host has not yet
# mapped its entire battle/owner objects. Existing VM mappings are checked too.
RESERVED = ((0x20000000, 0x2b100000), (0x30000000, 0x30240000),
            (0x31000000, 0x312a3000), (0x31400000, 0x31691000),
            (0x8520000, 0x8525000), (0x6500000, 0x6580000))


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


class NativeOwnerMapMetadata:
    """Attach to ``native.vm`` and allocate only through ``native.allocate``.

    The table's parser scratch and six map count/pointer bytes must be mapped
    RW. A fresh map slot (zero count/pointer) is required; other table sections
    survive. CPU and scratch stack survive successful and failed operations.
    Interrupted loads retain partial native stores and must not be resumed as
    successful loads. No existing host hooks or handles are removed/modified.
    """

    def __init__(self, native, *, owner):
        self.native, self.vm = native, native.vm
        self.image = IMAGE.read_bytes()
        if _sha(self.image) != IMAGE_SHA:
            raise ValueError('Unqualified current image')
        if type(owner) is not int or not 0 < owner < 2**32 - 0x240000:
            raise ValueError('Explicit mapped owner address required')
        if not callable(getattr(native, 'allocate', None)):
            raise ValueError('Host native allocator required')
        self.owner, self.table = owner, self.u32(owner + OWNER_TABLE)
        self._mapped(self.table, self.table + PARSER_SIZE, UC_PROT_READ | UC_PROT_WRITE)
        self._mapped(self.table + COUNT, self.table + POINTER + 4,
                     UC_PROT_READ | UC_PROT_WRITE)
        self._verify((*DECODE_CODE, *LOAD_CODE, *BIND_CODE, *CONSUMER_CODE))
        self._verify(((STATIC_RVA, STATIC_END), (0x18a08c, 0x18a09f),
                      (0x1823b4, 0x1823b7)))
        self.allocations, self.traces = [], []
        self.attempted = self.loaded = False
        self.records = 0
        self.stack = self._allocate(0x10000)
        self.sp = self.stack + 0xf000
        self.descriptor = self.stack + 0xff00

    def u32(self, address):
        return struct.unpack('<I', self.vm.mem_read(address, 4))[0]

    def _mapped(self, lo, hi, permissions):
        if not 0 < lo < hi <= 2**32:
            raise ValueError('Invalid map metadata storage')
        cursor = lo
        for a, z, flags in sorted(self.vm.mem_regions()):
            if a <= cursor <= z and flags & permissions == permissions:
                cursor = min(hi, z + 1)
            if cursor == hi:
                return
        raise ValueError('Map metadata storage unmapped or lacks permissions')

    def _verify(self, ranges):
        for lo, hi in ranges:
            if bytes(self.vm.mem_read(BASE + lo, hi - lo)) != self.image[lo:hi]:
                raise ValueError('Pinned map code/data changed in supplied VM')

    def _binding(self):
        if self.u32(self.owner + OWNER_TABLE) != self.table:
            raise ValueError('Owner catalog binding changed')

    def _allocate(self, length):
        before = [(a, z + 1) for a, z, _ in self.vm.mem_regions()]
        pointer = self.native.allocate(length)
        if (type(pointer) is not int or not 0 < pointer < pointer + length <= 2**32 or
                any(pointer < hi and lo < pointer + length for lo, hi in (*before, *RESERVED))):
            raise ValueError('Host allocator overlaps live/reserved memory')
        self._mapped(pointer, pointer + length, UC_PROT_READ | UC_PROT_WRITE)
        self.allocations.append((pointer, length))
        return pointer

    def _string(self, pointer, limit=380):
        value = bytearray()
        for i in range(limit):
            byte = self.vm.mem_read(pointer + i, 1)[0]
            if byte == 0:
                return bytes(value)
            value.append(byte)
        raise ValueError('Unbounded native metadata string')

    @contextmanager
    def _preserve(self):
        saved = self.vm.context_save()
        stack = bytes(self.vm.mem_read(self.stack, 0x10000))
        try:
            yield
        finally:
            self.vm.mem_write(self.stack, stack)
            self.vm.context_restore(saved)

    def _service(self, vm, address, size, _):
        # A block hook precedes existing CODE adapters. Redirecting here keeps
        # older host calloc/fgets adapters from consuming the same CRT call.
        pc, sp = address - BASE, vm.reg_read(x86.UC_X86_REG_ESP)
        if not self.stack <= sp < self.sp:
            raise AssertionError('CRT call outside private stack')
        ret = self.u32(sp) - BASE
        arg = lambda i: self.u32(sp + 4 + 4 * i)
        self.last_trace['services'][pc] += 1
        if pc in (0x1474ab, 0x1474dc, 0x14785c):
            allowed = {0x1474ab: (0x1ed5, 0x1ee7, 0x1f0a),
                       0x1474dc: (0x1f44, 0x1f65, 0x1f8d, 0x1f9d),
                       0x14785c: (0x1f04,)}
            if self.phase != 'decode' or ret not in allowed[pc]:
                raise AssertionError('Unqualified CSVZ CRT caller')
            handle = arg(3) if pc == 0x14785c else arg(0)
            if handle != self.handle:
                raise AssertionError('Unqualified CSVZ handle')
            if pc == 0x14785c:
                if (arg(1), arg(2), self.position) != (4, 1, 2):
                    raise AssertionError('Unqualified CSVZ header read')
                vm.mem_write(arg(0), self.raw[2:6])
                self.position += 4
                result = 1
            else:
                result = self.raw[self.position] if self.position < len(self.raw) else 0xffffffff
                self.position += int(self.position < len(self.raw))
        elif pc == 0x147e23:
            if self.phase != 'load' or ret != 0x59aad or (arg(0), arg(1)) != (144, STRIDE):
                raise AssertionError('Unqualified map calloc')
            result = self.records = self._allocate(144 * STRIDE)
            vm.mem_write(result, bytes(144 * STRIDE))
            self.last_trace['calloc'] = (144, STRIDE, result)
        elif pc == 0x147a95:
            if (self.phase != 'load' or ret != 0x51ab0 or
                    arg(1) != 4096 or arg(2) != self.handle or self.line >= len(self.lines)):
                raise AssertionError('Unqualified map fgets')
            line = self.lines[self.line]
            vm.mem_write(arg(0), line.replace(b'\r\n', b'\n') + b'\0')
            self.last_trace['source_reads'].append({
                'rva': pc, 'return_rva': ret, 'destination': arg(0),
                'decoded_span': (self.position, self.position + len(line)),
                'source_line': self.rows[self.line]['source_line'], 'sha256': _sha(line)})
            self.position += len(line)
            self.line += 1
            result = arg(0)
        elif pc == 0x1480b4:
            if self.phase != 'load' or ret != 0x51bc9 or self._string(arg(1)) != b'%d':
                raise AssertionError('Unqualified map sscanf')
            token = self._string(arg(0))
            if not re.fullmatch(rb'[+-]?[0-9]+', token):
                raise AssertionError('Unqualified map decimal token')
            vm.mem_write(arg(2), struct.pack('<i', int(token)))
            result = 1
        elif pc == 0x151de0:
            if self.phase != 'bind' or ret != 0x59e95:
                raise AssertionError('Unqualified map name comparison')
            left, right = self._string(arg(0), 16).lower(), self._string(arg(1), 16).lower()
            result = ((left > right) - (left < right)) & 0xffffffff
        else:
            raise AssertionError('Unexpected map service')
        vm.reg_write(x86.UC_X86_REG_EAX, result)
        vm.reg_write(x86.UC_X86_REG_ESP, sp + 4)
        vm.reg_write(x86.UC_X86_REG_EIP, BASE + ret)

    def _run(self, start, stop, ranges, *, registers, arguments=(), decode=False):
        self._binding()
        self._verify(ranges)
        trace = {'start': start, 'stop': stop, 'pcs': Counter(), 'services': Counter(),
                 'reads': [], 'writes': [], 'source_reads': []}
        self.last_trace = trace
        self.traces.append(trace)
        hooks = []

        def code(vm, address, size, _):
            pc = address - BASE
            if pc == stop or pc == 0xc32e2:
                vm.emu_stop()
                return
            if not any(lo <= pc and pc + size <= hi for lo, hi in ranges):
                raise AssertionError(f'Unqualified map instruction {pc:X}')
            trace['pcs'][pc] += 1

        def memory(vm, access, address, size, value, _):
            pc = vm.reg_read(x86.UC_X86_REG_EIP) - BASE
            if access == UC_MEM_WRITE:
                allowed = ((self.stack, self.stack + 0x10000),
                           (self.table + 4, self.table + PARSER_SIZE),
                           (self.table + COUNT, self.table + POINTER + 4),
                           (self.records, self.records + 144 * STRIDE),
                           (self.owner + 0x8aa4c, self.owner + 0x8aa50))
                if not any(lo <= address and address + size <= hi for lo, hi in allowed):
                    raise AssertionError(f'Unexpected map write {address:X}')
                if self.records <= address < self.records + 144 * STRIDE or address >= self.table + COUNT:
                    if not self.stack <= address < self.stack + 0x10000:
                        trace['writes'].append((pc, address, size, value))
            elif (self.table + COUNT <= address < self.table + POINTER + 4 or
                  self.records <= address < self.records + 144 * STRIDE or
                  BASE + STATIC_RVA <= address < BASE + STATIC_END or
                  pc in (0xc328b, 0xc328f, 0xc3294, 0xc32bb, 0xc32c7)):
                trace['reads'].append((pc, address, size, int.from_bytes(vm.mem_read(address, size), 'little')))

        with self._preserve():
            try:
                self.vm.reg_write(x86.UC_X86_REG_ESP, self.sp)
                self.vm.reg_write(x86.UC_X86_REG_EFLAGS, 2)
                self.vm.mem_write(self.sp, struct.pack('<' + 'I' * (1 + len(arguments)),
                                                       RETURN, *arguments))
                for name, value in registers.items():
                    self.vm.reg_write(getattr(x86, 'UC_X86_REG_' + name), value)
                for service in SERVICES:
                    hooks.append(self.vm.hook_add(UC_HOOK_BLOCK, self._service,
                                                 begin=BASE + service, end=BASE + service))
                if decode:
                    # The verified decoder has only internal branches and the
                    # three qualified CRT callees. Avoid tracing every LZ byte.
                    hooks.append(self.vm.hook_add(UC_HOOK_CODE, code,
                                                 begin=BASE + start, end=BASE + start))
                else:
                    hooks.append(self.vm.hook_add(UC_HOOK_CODE, code))
                    hooks.append(self.vm.hook_add(UC_HOOK_MEM_READ | UC_HOOK_MEM_WRITE, memory))
                # Existing hosts may already have translated these CRT entries.
                # Rebuild blocks so the temporary BLOCK adapters precede CODE.
                self.vm.ctl_flush_tb()
                self.vm.emu_start(BASE + start, BASE + stop,
                                  count=300000000 if decode else 3000000,
                                  timeout=90000000 if decode else 10000000)
                pc = self.vm.reg_read(x86.UC_X86_REG_EIP) - BASE
                if pc != stop and not (start == 0xc328b and pc == 0xc32e2):
                    raise AssertionError(f'Map execution bound at {pc:X}, expected {stop:X}')
                trace['frontier'] = pc
                trace['registers'] = {name: self.vm.reg_read(getattr(x86, 'UC_X86_REG_' + name))
                                      for name in ('EAX', 'ECX', 'EDX', 'ESP', 'EIP')}
            finally:
                for hook in hooks:
                    self.vm.hook_del(hook)
                self.vm.ctl_flush_tb()
        return trace

    def _static_bindings(self):
        self._verify(((STATIC_RVA, STATIC_END),))
        result = {}
        for index in range(STATIC_COUNT):
            offset = STATIC_RVA + index * STATIC_STRIDE
            name = self.image[offset:offset + 16].split(b'\0', 1)[0].lower()
            if not name or name in result:
                raise ValueError('Image map names are not unique')
            result[name] = BASE + offset
        if not set(result) <= {row['asset_stem'].lower().encode('ascii') for row in self.rows}:
            # 59E70's missing-name branch reads one record beyond the allocation.
            raise ValueError('Image metadata has an unmatched catalog name')
        return result

    def _verify_records(self, *, bound):
        self._verify(((STATIC_RVA, STATIC_END),))
        if (self.u32(self.table + POINTER) != self.records or
                struct.unpack('<h', self.vm.mem_read(self.table + COUNT, 2))[0] != 144):
            raise AssertionError('Original map count/pointer mismatch')
        for index, row in enumerate(self.rows):
            data = bytes(self.vm.mem_read(self.records + index * STRIDE, STRIDE))
            fields = [bytes.fromhex(value) for value in row['raw_fields_hex']]
            strings = [(col, off, width) for col, off, width in
                       ((0, 0, 16), (1, 0x10, 16), (2, 0x20, 16),
                        (8, 0x30, 64), (9, 0x70, 64), (10, 0xb0, 64))]
            strings += [(14 + i, 0xfe + 16 * i, 16) for i in range(10)]
            for col, off, width in strings:
                value = fields[col] if col < len(fields) else b''
                if data[off:off + width] != value.ljust(width, b'\0'):
                    raise AssertionError('Native map string differs from source')
            packed = row['kind'] | row['catalog_x'] << 2 | row['catalog_y'] << 17
            meta = self.static.get(row['asset_stem'].lower().encode('ascii'), 0) if bound else 0
            if (struct.unpack_from('<H', data, 0xf0)[0] != row['packed_selector'] or
                    struct.unpack_from('<I', data, 0xf4)[0] != packed or
                    struct.unpack_from('<3H', data, 0xf8) !=
                    (row['layer_width'], row['layer_height'], row['layers_per_row']) or
                    data[0xf2:0xf4] != b'\0\0' or data[0x19e:0x1a0] != b'\0\0' or
                    struct.unpack_from('<I', data, PANEL_METADATA)[0] != meta):
                raise AssertionError('Native map scalar/binding differs from source')

    def load(self):
        if self.attempted or bytes(self.vm.mem_read(self.table + COUNT, 6)) != bytes(6):
            raise ValueError('Fresh map slot and one load attempt required')
        self.raw, self.plain, self.rows, self.span = music_source()
        self.static = self._static_bindings()
        self.lines = self.plain[self.span[0]:self.span[1]].splitlines(keepends=True)
        if len(self.lines) != 144 or any(len(line) >= 4096 for line in self.lines):
            raise ValueError('Unqualified map row stream')
        self.attempted = True
        self.handle, self.position, self.phase = 0x8f000001, 0, 'decode'
        context, output = self._allocate(0xd440), self._allocate(len(self.plain) + 16)
        # 1EC0 initializes and uses only its own LZ ring at context+10. It needs
        # no 1760 constructor fields; no global temp-file lifecycle is entered.
        trace = self._run(0x1ec0, RETURN - BASE, DECODE_CODE, decode=True,
                          registers={'ECX': context}, arguments=(self.handle, output))
        decoded = bytes(self.vm.mem_read(output, len(self.plain)))
        if (trace['registers']['EAX'] & 255 != 1 or self.position != len(self.raw) or
                decoded != self.plain or trace['registers']['ESP'] != self.sp + 12):
            raise AssertionError('Original CSVZ decoder did not consume/produce complete source')
        trace['source_reads'].append({'path': SOURCE, 'raw_span': (0, self.position),
                                     'raw_sha256': SOURCE_SHA, 'decoded_sha256': _sha(decoded)})
        # Stream bytes come from THIS VM's original decompressor output.
        self.lines = decoded[self.span[0]:self.span[1]].splitlines(keepends=True)
        parser = bytes(self.vm.mem_read(self.table + 4, PARSER_SIZE - 4))
        try:
            self.phase, self.position, self.line = 'load', self.span[0], 0
            self.vm.mem_write(self.table + 4, struct.pack('<I', self.handle))
            self._run(0x51920, RETURN - BASE, LOAD_CODE,
                      registers={'ECX': self.table}, arguments=(24,))
            with self._preserve():
                self.vm.mem_write(self.sp + 0xc, struct.pack('<I', 144))
                self.vm.mem_write(self.sp + 0x18, SECTION + b'\0')
                self.load_trace = self._run(0x565ab, 0x565f1, LOAD_CODE,
                                            registers={'EDI': self.table})
            if (self.line != 144 or self.position != self.span[1] or
                    self.load_trace['registers']['EAX'] != 1 or
                    self.load_trace['registers']['ESP'] != self.sp):
                raise AssertionError('Original map loader did not finish all source rows')
            self._verify_records(bound=False)
        finally:
            self.vm.mem_write(self.table + 4, parser)
        self.phase = 'bind'
        with self._preserve():
            self.vm.mem_write(self.descriptor + 0x20, struct.pack('<I', self.table))
            self.bind_trace = self._run(0x818d6, 0x818e1, BIND_CODE,
                                        registers={'EDI': self.descriptor, 'ESI': self.owner})
        if self.bind_trace['registers']['ESP'] != self.sp:
            raise AssertionError('Original map binder stack imbalance')
        self._verify_records(bound=True)
        self.loaded = True
        self.provenance = {'image_sha256': IMAGE_SHA, 'source': SOURCE,
                           'source_sha256': SOURCE_SHA, 'decoded_sha256': PLAIN_SHA,
                           'decoded_span': self.span, 'source_lines': (21020, 21163),
                           'table': self.table, 'records': self.records, 'count': 144,
                           'record_sha256': _sha(bytes(self.vm.mem_read(self.records, 144 * STRIDE))),
                           'static_rva': STATIC_RVA, 'static_count': STATIC_COUNT,
                           'static_sha256': _sha(self.image[STATIC_RVA:STATIC_END]),
                           'allocations': tuple(self.allocations)}
        return self

    def lookup(self, area, scene):
        """Execute 59D80, return source provenance for its actual EAX pointer."""
        if not self.loaded:
            raise ValueError('Complete native map load required')
        if any(type(value) is not int or not 0 <= value <= 65535 for value in (area, scene)):
            raise ValueError('Explicit WORD area and scene required')
        self._verify_records(bound=True)
        self.phase = 'lookup'
        trace = self._run(0x59d80, RETURN - BASE, LOOKUP_CODE,
                          registers={'ECX': self.table}, arguments=(area, scene))
        if trace['registers']['ESP'] != self.sp + 12:
            raise AssertionError('Original map lookup stack imbalance')
        pointer = trace['registers']['EAX']
        if not pointer:
            return {'record': 0, 'metadata': 0, 'trace': trace, 'source_line': None}
        index, remainder = divmod(pointer - self.records, STRIDE)
        if remainder or not 0 <= index < 144:
            raise AssertionError('Original map lookup escaped catalog')
        metadata = self.u32(pointer + PANEL_METADATA)
        return {'record': pointer, 'metadata': metadata, 'trace': trace,
                'source_line': self.rows[index]['source_line'],
                'source_record_sha256': self.rows[index]['source_record_sha256'],
                'metadata_rva': metadata - BASE if metadata else None,
                'panel_words': struct.unpack('<Hh', self.vm.mem_read(metadata + 0x20, 4)) if metadata else None}

    def probe_c3080(self, *, character):
        """Diagnostic C328B..C32FD slice, not a retained C3080 continuation.

        EBX is the actual character ROOT (no +90). Reads +14/+18, publishes
        owner+8AA4C and checks the area row's +1A0. CPU/stack are restored;
        the native owner cache write persists. Stops before assertion C32E2
        for a missing area binding, otherwise before C32FD's next UI branch.
        """
        if not self.loaded:
            raise ValueError('Complete native map load required')
        self._verify_records(bound=True)
        self.phase = 'consumer'
        return self._run(0xc328b, 0xc32fd, CONSUMER_CODE,
                         registers={'ESI': self.owner, 'EBX': character, 'EBP': 0})


def attach_and_load(native, *, owner):
    """Load/bind in a supplied stopped host; no second VM or preload is created."""
    return NativeOwnerMapMetadata(native, owner=owner).load()
