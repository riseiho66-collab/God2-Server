"""One EnyName -> FightEny producer edge, then original 1C construction prefix.

No game return is adapted. Only bounded CRT/MFC string operations are serviced.
Stop before the unresolved ROM-bank pointer; no actor initialization completion,
recruitment, or original combat numbers are inferred from resource selectors.
"""
import json
import struct

from .current_monster_base_stats import (
    IMAGE, IMAGE_SHA256, GAME_FILE, GAME_SHA256, GAME_DECODED_SHA256,
    _LookupFixture, BATTLE, MANAGER, PACKET, sha)
from .current_monster_inventory import pinned_catalog, ROOT, FIELDS
from .current_world_actor import MESSAGES, NativeWorldActor
from .current_indoor_resources import BASE, SP, SCRATCH, RETURN, NativeIndoorResources
from .omega_assets import decode_csvz
from unicorn import (UC_HOOK_CODE, UC_HOOK_MEM_READ, UC_HOOK_MEM_WRITE,
                     UC_MEM_WRITE, UC_PROT_READ, UC_PROT_WRITE)
from unicorn import x86_const as reg

ACTOR, NAMES, HEAP = 0x27000000, 0x28000000, 0x29000000
ACTOR_SIZE = 0xecc
FRAME, METADATA = SP - 0x1a8, SP - 0x16c
READER = BATTLE + 0x2e9b0
FIGHT_FILE = 'Data2/Patch/FightEny.csvZ'
FIGHT_SHA = '887f721a429aaa394d79787ccbd42d544cbcc53a878802cd5f8d010e55dc5a6a'
FIGHT_PLAIN_SHA = '30aa86a6001919289090f924bbde727eab5e100ff4db6d71406e60260ed22c40'
ENEMY_ROW_SHA = '34e14a591490fd9f6444f8776bcc7f0cc39699dfd78a13b2feb097c3636c5f32'
CWD = b'C:\\Oracle'  # Explicit cached environment string, not a host directory.
SPANS = {
    'row_parser': (0x51be0, 0x51cd2),
    'field_accessors': (0x51ae0, 0x51bdc),
    'single_enemy_row': (0x5a2b4, 0x5a516),
    'single_fight_row': (0x54290, 0x54478),
    'participant_prefix': (0x115c90, 0x115e18),
    'normal_resource_producer': (0x115e77, 0x115e89),
    'normal_resource_binding': (0x115f2d, 0x115fc7),
    'enemy_lookup': (0x5a0a0, 0x5a11c),
    'slot_lookup': (0x11e6e0, 0x11e76a),
    'path_expansion': (0x12f550, 0x12f5b2),
    'resource_name_lookup_prefix': (0x120650, 0x1206e0),
    'previously_qualified_actor_reset': (0x11fde0, 0x11fff6),
}
PACKET_FIELDS = (
    (0, 1, 'opcode; not read by this callee'),
    (1, 1, 'position; side=position//14, local_slot=position%14'),
    (2, 1, 'packet-supplied displayed level -> metadata+7'),
    (3, 2, 'packet-supplied identity word -> metadata+0'),
    (5, 2, 'variant/type bitfield; selected normal value 0400'),
    (7, 2, 'EnyName ordinal -> metadata+C and native lookup'),
    (9, 16, 'opaque block -> metadata+E; includes area BYTE+9 and scene WORD+11'),
    (25, 16, 'opaque block -> metadata+1E; no scalar semantics established'),
    (41, 4, 'flags -> metadata+8; if bit0 set, normalized to 1'),
)
SERVICES = {
    0x1489a0: {0x51c0c, 0x51c1d},
    0x147b80: {0x51c4d, 0x5a2c9, 0x5431a},
    0x1480b4: {0x51bc9},
    0x147af7: {0x12f5a9, 0x115fa8},
    0x15ada3: {0x115fbe},
    0x15aaaa: {0x120681},
}


class MonsterSideInitializationProbe:
    """Fixed original identity (EnyName generation1/area1/scene0/ordinal1).

    Descriptor staging reuses the existing lightweight lookup helper. Individual
    row writers execute original code; the whole source loaders do not run.
    One poisoned actor address is retained while only its lookup slot moves.
    """
    def __init__(self, *, fight_rows_loaded=True, poison=0xa5, vm=None):
        if type(fight_rows_loaded) is not bool or type(poison) is not int or not 0 <= poison <= 255:
            raise ValueError('Expected table availability flag and byte poison')
        self.image = IMAGE.read_bytes()
        if sha(self.image) != IMAGE_SHA256:
            raise ValueError('Pinned native image changed')
        self.catalog = pinned_catalog()
        self.row = self.catalog['records'][0]
        if (self.row['record_sha256'] != ENEMY_ROW_SHA
                or (self.row['area_generation'], self.row['area'], self.row['scene'],
                    self.row['ordinal']) != (1, 1, 0, 1)):
            raise ValueError('Pinned enemy occurrence changed')
        self.native = _LookupFixture(self.image, self.catalog, vm=vm)
        self.vm = self.native.vm
        self.poison, self.fight_rows_loaded = poison, fight_rows_loaded
        self.record = self.native.u32(MESSAGES + 0xd2e24)
        self.resource_rows = tuple(BATTLE + 0x40b9c + 92 * (14 + 250 * s) for s in (0, 1))
        for address, size in ((BATTLE, 4096), (MANAGER, 0x400), (ACTOR, 0x1000),
                              (NAMES, 0x410), (HEAP, 4096), (self.record, 26),
                              (READER, 0x78 + 8 * 380 + 4), (0, 4096)):
            NativeWorldActor._map_rw(self.native, address, size)
        self.vm.mem_write(ACTOR, bytes((poison,)) * 0x1000)
        self.put(BATTLE + 0x28, '<I', MESSAGES)
        self.put(MANAGER + 0x14, '<I', NAMES)
        self.vm.mem_write(NAMES, bytes((poison,)) * 0x410)
        self.put(NAMES + 0x404, '<I', 0)  # Explicit empty name registry, no invented handle.
        self.vm.mem_protect(BASE + 0x19d000, 4096, UC_PROT_READ | UC_PROT_WRITE)
        self.vm.mem_protect(BASE + 0x1b9000, 4096, UC_PROT_READ | UC_PROT_WRITE)
        self.put(BASE + 0x19ddf0, '<I', 0)
        self.vm.mem_write(BASE + 0x1b93c4, CWD + b'\0')
        self.source_traces = []
        self._load_enemy_row()
        if fight_rows_loaded:
            self._load_fight_row()

    def put(self, address, fmt, *values):
        self.vm.mem_write(address, struct.pack(fmt, *values))

    def getreg(self, name):
        return self.vm.reg_read(getattr(reg, 'UC_X86_REG_' + name))

    def setreg(self, name, value):
        self.vm.reg_write(getattr(reg, 'UC_X86_REG_' + name), value)

    def _reset(self):
        self.vm.mem_write(SP - 0x1000, bytes((self.poison,)) * 0x1100)
        for name in ('EAX', 'EBX', 'ECX', 'EDX', 'ESI', 'EDI', 'EBP'):
            self.setreg(name, self.poison * 0x01010101)
        self.setreg('ESP', SP)
        self.setreg('EFLAGS', 2)
        self.put(SP, '<II', RETURN, PACKET)

    def _regions(self):
        regions = [
            ('stack', SP - 0x1000, 0x1100), ('packet', PACKET, 45),
            ('source_line', SCRATCH, 256), ('enemy_record', self.record, 26),
            ('actor', ACTOR, ACTOR_SIZE), ('battle', BATTLE, 0x2c),
            ('manager', MANAGER, 0x400), ('registry', NAMES, 0x410),
            ('enemy_parser', MESSAGES, 0x78 + 10 * 380),
            ('enemy_descriptor_headers', MESSAGES + 0xd2d9c, 17 * 8),
            ('enemy_record_base', MESSAGES + 0xd2e24, 4),
            ('descriptor_fixture', 0x24000000, 0x10000),
            ('fight_parser', READER + 4, 0x78 + 8 * 380),
            ('string_heap', HEAP, 4096), ('seh', 0, 4),
            ('image', BASE, len(self.image)),
        ]
        if self.fight_rows_loaded:
            regions += [('fight_side' + str(s), ptr, 92) for s, ptr in enumerate(self.resource_rows)]
        return regions

    def _run(self, start, stops, spans, *, writes=(), budget=10000):
        ranges = [SPANS[name] for name in spans]
        for lo, hi in ranges:
            if bytes(self.vm.mem_read(BASE + lo, hi - lo)) != self.image[lo:hi]:
                raise ValueError('Mapped original instructions changed')
        trace = {'start_rva': start, 'visits': [], 'reads': [], 'writes': [], 'services': []}
        writable = ((SP - 0x1000, SP + 0x100), *writes)
        regions = self._regions()

        def access(address, size, *, write=False, value=None, adapter=False):
            region = next(((name, lo) for name, lo, length in regions
                           if lo <= address and address + size <= lo + length), None)
            if region is None or (write and not any(lo <= address and address + size <= hi
                                                    for lo, hi in writable)):
                raise AssertionError(f'Unqualified memory access {address:x}/{size}')
            raw = value if write else bytes(self.vm.mem_read(address, size))
            event = {'rva': self.getreg('EIP') - BASE, 'address': address,
                     'region': region[0], 'offset': address - region[1], 'size': size,
                     'hex': raw.hex(), 'adapter': adapter}
            trace['writes' if write else 'reads'].append(event)
            return raw

        self._access = access

        def code(vm, address, size, _):
            rva = address - BASE
            if rva in stops:
                vm.emu_stop()
                return
            if rva in SERVICES:
                trace['visits'].append(rva)
                self._service(rva, trace)
                return
            if not any(lo <= rva and rva + size <= hi for lo, hi in ranges):
                raise AssertionError(f'Unqualified original instruction {rva:x}')
            trace['visits'].append(rva)
            if rva == 0x115e0c:
                trace['record_pointer'] = self.getreg('EAX')
            if rva == 0x115f8c:
                trace['resource_pointer'] = self.getreg('ESI')
            if rva == 0x120650:
                pointer = self.native.u32(self.getreg('ESP') + 4)
                trace['requested_path_hex'] = bytes(self.vm.mem_read(pointer, 256)).split(b'\0', 1)[0].hex()

        def memory(vm, kind, address, size, value, _):
            write = kind == UC_MEM_WRITE
            access(address, size, write=write,
                   value=(value & ((1 << (size * 8)) - 1)).to_bytes(size, 'little') if write else None)

        hooks = [self.vm.hook_add(UC_HOOK_CODE, code),
                 self.vm.hook_add(UC_HOOK_MEM_READ | UC_HOOK_MEM_WRITE, memory)]
        try:
            self.vm.emu_start(BASE + start, RETURN, count=budget)
            stop = self.getreg('EIP') - BASE
            if stop not in stops:
                raise AssertionError('Native instruction budget exhausted')
        finally:
            for hook in hooks:
                self.vm.hook_del(hook)
            del self._access
        trace['stop_rva'] = stop
        return trace

    def string(self, pointer, limit=256):
        raw = bytearray()
        for i in range(limit):
            value = self._access(pointer + i, 1, adapter=True)
            if value == b'\0':
                return bytes(raw)
            raw.extend(value)
        raise AssertionError('Bounded CRT string exceeded')

    def _write(self, pointer, raw):
        self._access(pointer, len(raw), write=True, value=raw, adapter=True)
        self.vm.mem_write(pointer, raw)

    def _service(self, rva, trace):
        sp = self.getreg('ESP')
        ret = struct.unpack('<I', self._access(sp, 4, adapter=True))[0]
        if ret - BASE not in SERVICES[rva]:
            raise AssertionError('Unqualified CRT/MFC caller')
        def arg(i):
            return struct.unpack('<I', self._access(sp + 4 + i * 4, 4, adapter=True))[0]
        trace['services'].append({'rva': rva, 'return_rva': ret - BASE})
        cleanup = 0
        if rva == 0x1489a0:
            if arg(1) not in (10, 44):
                raise AssertionError('Unexpected parser delimiter')
            offset = self.string(arg(0)).find(bytes((arg(1),)))
            result = 0 if offset < 0 else arg(0) + offset
        elif rva == 0x147b80:
            if not 0 < arg(2) <= 379:
                raise AssertionError('Bounded source copy exceeded')
            self._write(arg(0), self._access(arg(1), arg(2), adapter=True))
            result = arg(0)
        elif rva == 0x1480b4:
            raw = self.string(arg(0))
            if self.string(arg(1)) != b'%d' or not raw.isdigit() or len(raw) > 5:
                raise AssertionError('Outside selected decimal source fields')
            self._write(arg(2), struct.pack('<I', int(raw)))
            result = 1
        elif rva == 0x147af7:
            fmt = self.string(arg(1))
            if ret - BASE == 0x12f5a9 and fmt == b'%s\\%s':
                raw = self.string(arg(2)) + b'\\' + self.string(arg(3))
            elif ret - BASE == 0x115fa8 and fmt == b'%s':
                raw = self.string(arg(2))
            else:
                raise AssertionError('Outside qualified path formatting')
            if len(raw) >= 256:
                raise AssertionError('Path bound')
            self._write(arg(0), raw + b'\0')
            result = len(raw)
        else:
            source = arg(0)
            if rva == 0x15aaaa:
                source = struct.unpack('<I', self._access(source, 4, adapter=True))[0]
            raw = self.string(source)
            # Reuse the established CString layout helper, while logging its
            # adapter memory accesses separately from original x86 stores.
            owner = self
            class CStringMemory:
                def mem_write(self, pointer, value):
                    owner._write(pointer, value)
            class CStringAllocator:
                vm = CStringMemory()
                def allocate(self, length):
                    pointer = owner.heap_next
                    owner.heap_next += (length + 3) & ~3
                    if owner.heap_next > HEAP + 4096:
                        raise AssertionError('CString heap bound')
                    return pointer
            NativeIndoorResources.cstring(CStringAllocator(), self.getreg('ECX'), raw)
            result, cleanup = self.getreg('ECX'), 4
        self.setreg('EAX', result)
        self.setreg('ESP', sp + 4 + cleanup)
        self.setreg('EIP', ret)

    def _parse(self, raw, parser, width, source):
        self._reset()
        self.vm.mem_write(SCRATCH, raw.replace(b'\r\n', b'\n') + b'\0')
        self.vm.mem_write(parser + 0x78, bytes(width * 380))
        self.put(parser + 8, '<H', width)
        self.put(SP, '<II', RETURN, SCRATCH)
        self.setreg('ECX', parser)
        trace = self._run(0x51be0, {RETURN - BASE}, ('row_parser',),
                          writes=((parser + 0xc, parser + 0x10),
                                  (parser + 0x78, parser + 0x78 + width * 380)))
        if self.getreg('ESP') != SP + 8:
            raise AssertionError('Original parser stack cleanup')
        trace.update(stage='original_row_parser', source=source,
                     input_translation='CRLF -> LF; final LF maps to original CRLF')
        self.source_traces.append(trace)

    def _load_enemy_row(self):
        source = {'file': GAME_FILE, 'decoded_offset': self.row['source_offset'],
                  'row_sha256': ENEMY_ROW_SHA}
        self._parse(bytes.fromhex(self.row['raw_record_hex']), MESSAGES, 10, source)
        self.vm.mem_write(self.record, bytes(26))  # Original loader's calloc contract.
        self._reset()
        self.setreg('EBP', MESSAGES)
        self.setreg('ESI', self.record)
        self.source_traces.append(self._run(0x5a2b4, {0x5a516},
            ('single_enemy_row', 'field_accessors'), writes=((self.record, self.record + 26),)))
        self.source_traces[-1].update(stage='original_enemy_row_writer', source=source)
        self.enemy_record = bytes(self.vm.mem_read(self.record, 26))
        if self.enemy_record[:2] != b'\x16\x0f':
            raise AssertionError('Original row routing bytes changed')

    def _load_fight_row(self):
        path = ROOT.parent / 'God2' / FIGHT_FILE
        if path.stat().st_size > 1024 * 1024:
            raise ValueError('FightEny source bound')
        raw = path.read_bytes()
        if sha(raw) != FIGHT_SHA:
            raise ValueError('Pinned FightEny source changed')
        plain = decode_csvz(raw, limit=1024 * 1024)
        if sha(plain) != FIGHT_PLAIN_SHA:
            raise ValueError('Pinned FightEny decoded source changed')
        line = plain.splitlines(keepends=True)[54]
        if plain[2105:2105 + len(line)] != line or line.split(b',')[1] != b'15':
            raise ValueError('Pinned FightEny row changed')
        self.fight_source = {'file': FIGHT_FILE, 'sha256': FIGHT_SHA,
            'decoded_sha256': FIGHT_PLAIN_SHA, 'decoded_offset': 2105,
            'line': 55, 'raw_hex': line.hex(), 'row_sha256': sha(line)}
        for pointer in self.resource_rows:
            NativeWorldActor._map_rw(self.native, pointer, 92)
            self.vm.mem_write(pointer, bytes((self.poison,)) * 92)
        self._parse(line, READER + 4, 8, self.fight_source)
        self._reset()
        self.setreg('EBX', READER)
        self.setreg('ESI', READER + 4)
        self.put(SP + 0x18, '<I', READER + 4)
        self.source_traces.append(self._run(0x54290, {0x54478},
            ('single_fight_row', 'field_accessors'),
            writes=tuple((p, p + 92) for p in self.resource_rows)))
        self.source_traces[-1].update(stage='original_fight_row_writer', source=self.fight_source)
        self.fight_records = [bytes(self.vm.mem_read(p, 92)).hex() for p in self.resource_rows]

    def reset_actor(self):
        """Replay the ALREADY qualified reset solely to locate first scalar writes.

        This independent prerequisite stage is not claimed as a new constructor
        discovery or as continuous execution from battle entry.
        """
        self._reset()
        self.put(SP, '<IIII', RETURN, ACTOR, 1, 0)
        trace = self._run(0x11fde0, {RETURN - BASE}, ('previously_qualified_actor_reset',),
                          writes=((ACTOR, ACTOR + ACTOR_SIZE),))
        if self.getreg('ESP') != SP + 16:
            raise AssertionError('Original actor reset stack cleanup')
        trace['scalar_writes'] = [x for x in trace['writes'] if x['region'] == 'actor'
                                  and 0xde8 <= x['offset'] < 0xdf8]
        trace['metadata_hex'] = bytes(self.vm.mem_read(ACTOR + 0xdb0, 56)).hex()
        trace['novel_frontier'] = False
        return trace

    def run(self, side, *, local_slot=0, diagnostic_level=23, diagnostic_flags=0x2c2b2a29,
            diagnostic_identity_word=0x1234):
        if (type(side) is not int or side not in (0, 1) or type(local_slot) is not int
                or not 0 <= local_slot < 14 or type(diagnostic_level) is not int
                or not 0 <= diagnostic_level <= 255 or type(diagnostic_flags) is not int
                or not 0 <= diagnostic_flags <= 0xffffffff or
                type(diagnostic_identity_word) is not int or not 0 <= diagnostic_identity_word <= 65535):
            raise ValueError('Outside paired normal-enemy inputs')
        self._reset()
        self.heap_next = HEAP
        self.put(0, '<I', 0xffffffff)
        self.vm.mem_write(MANAGER + 0x38, bytes(28 * 24))
        position = side * 14 + local_slot
        self.put(MANAGER + 0x38 + position * 24, '<I', ACTOR)
        packet = bytearray(range(45))
        packet[:3] = bytes((0x1c, position, diagnostic_level))
        struct.pack_into('<HHH', packet, 3, diagnostic_identity_word, 0x400, 1)
        packet[9] = 1
        struct.pack_into('<H', packet, 11, 0)
        struct.pack_into('<I', packet, 41, diagnostic_flags)
        self.vm.mem_write(PACKET, bytes(packet))
        before = bytes(self.vm.mem_read(ACTOR, 0x1000))
        self.setreg('ECX', BATTLE)
        stop = 0x1206e0 if self.fight_rows_loaded else 0x12f57d
        trace = self._run(0x115c90, {stop}, (
            'participant_prefix', 'normal_resource_producer', 'normal_resource_binding',
            'enemy_lookup', 'slot_lookup', 'path_expansion', 'resource_name_lookup_prefix'),
            writes=((0, 4), (HEAP, HEAP + 4096),
                    (BASE + 0x1b92c0, BASE + 0x1b93c4)))
        after = bytes(self.vm.mem_read(ACTOR, 0x1000))
        if after != before:
            raise AssertionError('Actor or actor guard changed before resource boundary')
        if bytes(self.vm.mem_read(PACKET, 45)) != packet:
            raise AssertionError('Diagnostic packet changed')
        trace.update(side=side, position=position, actor_address=ACTOR,
            packet_hex=packet.hex(), metadata_hex=bytes(self.vm.mem_read(METADATA, 56)).hex(),
            actor_before_sha256=sha(before), actor_after_sha256=sha(after),
            scalars_hex=before[0xde8:0xdf8].hex(),
            unresolved=('ROM bank at manager+8; original load 1206E5 -> 29820'
                        if self.fight_rows_loaded else 'FightEny row path +C not supplied'),
            actor_metadata_store_executed=False, scalar_initialization_executed=False)
        return trace

    def evidence(self):
        sides = [self.run(side) for side in (1, 0)]
        reset = self.reset_actor()
        after_reset = [self.run(side) for side in (1, 0)]
        return {
            'schema': 'current-monster-side-initialization-v1',
            'image': {'file': str(IMAGE), 'sha256': IMAGE_SHA256, 'base': BASE,
                      'rva_equals_file_offset': True},
            'identity': {k: self.row[k] for k in ('source_record_index', 'area_generation',
                                               'area', 'scene', 'ordinal')},
            'enemy_source': {'file': GAME_FILE, 'sha256': GAME_SHA256,
                'decoded_sha256': GAME_DECODED_SHA256, 'decoded_offset': self.row['source_offset'],
                'line': self.row['source_line'], 'row_sha256': ENEMY_ROW_SHA,
                'raw_hex': self.row['raw_record_hex'], 'native_record_hex': self.enemy_record.hex()},
            'fight_source': getattr(self, 'fight_source', None),
            'fight_records_hex': getattr(self, 'fight_records', None),
            'source_traces': self.source_traces,
            'sides': sides, 'previously_qualified_reset': reset,
            'sides_after_reset': after_reset,
            'packet_fields': [{'offset_decimal': off, 'size': size, 'meaning': meaning}
                              for off, size, meaning in PACKET_FIELDS],
            'native_spans': {name: {'start_rva': lo, 'end_rva_exclusive': hi,
                                   'sha256': sha(self.image[lo:hi])}
                             for name, (lo, hi) in SPANS.items()},
            'adapters': ['source-derived descriptor layout', 'one source row per native row writer',
                         'CRT/MFC strings', 'cached diagnostic CWD', 'empty name registry'],
            'fields': dict.fromkeys(FIELDS), 'runtime_eligible': False,
            'constructor_completed': False, 'recruitment_proven': False,
        }


def main():
    print(json.dumps(MonsterSideInitializationProbe().evidence(), separators=(',', ':')))


if __name__ == '__main__':
    main()
