"""Native 1C metadata consumers: branch-dependent name/secondary display text.

Independent instruction slices with explicit operand fixtures, not a completed
constructor. Game functions execute unchanged; no CRT or game returns are
adapted. Only the current image and the shared pinned EnyName source are loaded.
"""
import json
import struct

from capstone import Cs, CS_ARCH_X86, CS_MODE_32, CS_OP_MEM
from .current_monster_side_initialization import (
    MonsterSideInitializationProbe, IMAGE, IMAGE_SHA256, ACTOR, ACTOR_SIZE,
    BASE, SP, METADATA, PACKET, BATTLE, MANAGER, MESSAGES, sha,
    GAME_FILE, GAME_SHA256, GAME_DECODED_SHA256)
from .current_world_actor import NativeWorldActor
from unicorn import UC_HOOK_CODE, UC_HOOK_MEM_READ, UC_HOOK_MEM_WRITE, UC_MEM_WRITE

DISPLAY = 0x2b000000
DISPLAY_STRIDE = 0xa7e0
GETTER_OUTPUT = 0x2c000000
SPANS = {
    'participant_merge': (0x115c90, 0x115df1),
    'slot_lookup': (0x11e6e0, 0x11e76a),
    'packet2000_actor_copy': (0x116149, 0x116166),
    'constructor_copy_island': (0x121a30, 0x121a4c),
    'display_type_dispatch': (0x12ce4b, 0x12ce64),
    'normal_type_dispatch': (0x12cff5, 0x12d02a),
    'two_text_arguments': (0x12d193, 0x12d1b9),
    'primary_text_setter': (0x1097d0, 0x109874),
    'secondary_text_setter': (0x109e70, 0x109f1a),
    'secondary_text_getter': (0x109f20, 0x109f74),
    'normal_enemy_name': (0x12d0c4, 0x12d15e),
    'enemy_lookup': (0x5a0a0, 0x5a11c),
    'actor_name_reuse': (0x116577, 0x11659c),
}
XREF_SCAN = (0x110000, 0x12f550)


def static_xrefs(image):
    """Bounded operand candidates, not automatic actor/type attribution."""
    if sha(image) != IMAGE_SHA256:
        raise ValueError('Pinned image changed')
    dis = Cs(CS_ARCH_X86, CS_MODE_32)
    dis.detail = True
    dis.skipdata = True
    candidates = []
    for ins in dis.disasm(image[XREF_SCAN[0]:XREF_SCAN[1]], XREF_SCAN[0]):
        if ins.id and any(op.type == CS_OP_MEM and 0xdb0 <= op.mem.disp < 0xde8
                          for op in ins.operands):
            candidates.append({'rva': ins.address, 'hex': ins.bytes.hex(),
                               'instruction': ins.mnemonic + ' ' + ins.op_str})
    indirect = []
    for lo, hi in ((0x12d0c4, 0x12d0de), (0x12d193, 0x12d1b9)):
        for ins in dis.disasm(image[lo:hi], lo):
            indirect.append({'rva': ins.address, 'hex': ins.bytes.hex(),
                             'instruction': ins.mnemonic + ' ' + ins.op_str})
    return {'scan_start_rva': XREF_SCAN[0], 'scan_end_rva_exclusive': XREF_SCAN[1],
            'candidate_only': True, 'direct_displacement_candidates': candidates,
            'qualified_metadata_alias_windows': indirect,
            'false_positive_example': {'rva': 0x115c23,
                'reason': 'DD4 indexes ProgramMsg storage here, not actor metadata'}}


class ParticipantMetadataProbe:
    def __init__(self, *, poison=0xa5, enemy_payload=True):
        if type(enemy_payload) is not bool:
            raise ValueError('Expected explicit source availability')
        self.native = MonsterSideInitializationProbe(fight_rows_loaded=False, poison=poison)
        self.vm, self.image = self.native.vm, self.native.image
        self.poison, self.enemy_payload = poison, enemy_payload
        self.xrefs = static_xrefs(self.image)
        self.record = self.native.record
        self.put(MANAGER + 4, '<I', MESSAGES)
        for address in (DISPLAY, GETTER_OUTPUT):
            NativeWorldActor._map_rw(self.native.native, address, 4096)
        if not enemy_payload:
            self.vm.mem_unmap(self.record & ~4095, 4096)
        self.display_record = DISPLAY

    def put(self, address, fmt, *values):
        self.native.put(address, fmt, *values)

    def getreg(self, name):
        return self.native.getreg(name)

    def setreg(self, name, value):
        self.native.setreg(name, value)

    def _registers(self):
        for name in ('EAX', 'EBX', 'ECX', 'EDX', 'ESI', 'EDI', 'EBP'):
            self.setreg(name, self.poison * 0x01010101)
        self.setreg('ESP', SP)
        self.setreg('EFLAGS', 2)

    def _regions(self):
        regions = [
            ('packet', PACKET, 45), ('actor_metadata', ACTOR + 0xdb0, 56),
            ('actor', ACTOR, ACTOR_SIZE), ('merged_metadata', METADATA, 56),
            ('stack', SP - 0x1000, 0x1100), ('manager', MANAGER, 0x400),
            ('battle', BATTLE, 0x2c), ('image', BASE, len(self.image)),
            ('display', self.display_record, 0x100), ('getter_output', GETTER_OUTPUT, 64),
            ('descriptor_headers', MESSAGES + 0xd2d9c, 17 * 8),
            ('record_base', MESSAGES + 0xd2e24, 4),
            ('descriptor_fixture', 0x24000000, 0x10000),
        ]
        if self.enemy_payload:
            regions.append(('enemy_record', self.record, 26))
        return regions

    def _run(self, entry, stops, names, *, writes=(), budget=3000):
        spans = [SPANS[name] for name in names]
        for lo, hi in spans:
            if bytes(self.vm.mem_read(BASE + lo, hi - lo)) != self.image[lo:hi]:
                raise ValueError('Mapped original instructions changed')
        trace = {'entry_rva': entry, 'visits': [], 'reads': [], 'writes': [], 'text_calls': []}
        self.last_trace = trace
        regions = self._regions()
        writable = ((SP - 0x1000, SP + 0x100), *writes)
        text_windows = {}

        def code(vm, address, size, _):
            rva = address - BASE
            if rva in stops:
                vm.emu_stop()
                return
            if not any(lo <= rva and rva + size <= hi for lo, hi in spans):
                raise AssertionError(f'Unqualified original instruction {rva:x}')
            trace['visits'].append(rva)
            if rva in (0x1097d0, 0x109e70):
                ret, handle, pointer = struct.unpack('<III', vm.mem_read(self.getreg('ESP'), 12))
                trace['text_calls'].append({'callee_rva': rva, 'return_rva': ret - BASE,
                    'this': self.getreg('ECX'), 'handle': handle & 0xffff, 'source': pointer})
                scans = (0x10980e, 0x109851) if rva == 0x1097d0 else (0x109eae, 0x109ef4)
                for scan in scans:
                    text_windows[scan] = (pointer, pointer + 16)
            if rva == 0x12d0de:
                trace['selected_enemy_pointer'] = self.getreg('EAX')

        def memory(vm, kind, address, size, value, _):
            rva, write = self.getreg('EIP') - BASE, kind == UC_MEM_WRITE
            if not write and rva in text_windows:
                lo, hi = text_windows[rva]
                if not lo <= address < address + size <= hi:
                    raise AssertionError('Unterminated 16-byte string: native scan would spill')
            region = next(((name, lo) for name, lo, length in regions
                           if lo <= address and address + size <= lo + length), None)
            if region is None or (write and not any(lo <= address and address + size <= hi
                                                    for lo, hi in writable)):
                raise AssertionError(f'Unqualified memory access {address:x}/{size} at {rva:x}')
            raw = ((value & ((1 << (8 * size)) - 1)).to_bytes(size, 'little') if write
                   else bytes(vm.mem_read(address, size)))
            trace['writes' if write else 'reads'].append({'rva': rva, 'address': address,
                'region': region[0], 'offset': address - region[1], 'size': size, 'hex': raw.hex()})

        hooks = [self.vm.hook_add(UC_HOOK_CODE, code),
                 self.vm.hook_add(UC_HOOK_MEM_READ | UC_HOOK_MEM_WRITE, memory)]
        try:
            self.vm.emu_start(BASE + entry, BASE + 0x1000, count=budget)
            stop = self.getreg('EIP') - BASE
            if stop not in stops:
                raise AssertionError('Native instruction budget exhausted')
        finally:
            for hook in hooks:
                self.vm.hook_del(hook)
        trace['stop_rva'] = stop
        return trace

    def stage(self, first, second, *, variant=0x2000, side=0, local_slot=0):
        """Merge real 1C instructions, then copy with real original stores.

        2000 follows its real jump to 116149. Normal 0400 stops before lookup;
        its 121A30 copy is an explicitly independent constructor-tail island.
        """
        if (type(first) is not bytes or len(first) != 16 or type(second) is not bytes
                or len(second) != 16 or type(variant) is not int or variant not in (0x400, 0x2000)
                or type(side) is not int or side not in (0, 1) or type(local_slot) is not int
                or not 0 <= local_slot < 14):
            raise ValueError('Expected two exact blocks and bounded normal/text-branch operands')
        self.native._reset()
        self.vm.mem_write(ACTOR, bytes((self.poison,)) * 4096)
        self.put(ACTOR + 0x1a, '<h', -1)
        self.vm.mem_write(MANAGER + 0x38, bytes(28 * 24))
        position = side * 14 + local_slot
        self.put(MANAGER + 0x38 + 24 * position, '<I', ACTOR)
        packet = bytes((0x1c, position, 23)) + struct.pack('<HHH', 0x1234, variant, 1)
        packet += first + second + bytes(4)
        self.vm.mem_write(PACKET, packet)
        self.setreg('ECX', BATTLE)
        stop = 0x116166 if variant == 0x2000 else 0x115df1
        merge = self._run(0x115c90, {stop},
            ('participant_merge', 'slot_lookup', 'packet2000_actor_copy'),
            writes=((ACTOR + 0xdb0, ACTOR + 0xde8),))
        copy = None
        if variant == 0x400:
            copy = self.copy_metadata()
        metadata = bytes(self.vm.mem_read(ACTOR + 0xdb0, 56))
        if metadata[14:46] != first + second or bytes(self.vm.mem_read(PACKET, 45)) != packet:
            raise AssertionError('Native metadata block provenance mismatch')
        return {'variant': variant, 'side': side, 'position': position,
                'packet_hex': packet.hex(), 'actor_metadata_hex': metadata.hex(),
                'merge': merge, 'independent_constructor_copy': copy,
                'constructor_completed': False, 'input_authority': 'diagnostic_packet_and_actor'}

    def copy_metadata(self, *, source_present=True):
        if type(source_present) is not bool:
            raise ValueError('Expected explicit metadata-source availability')
        self._registers()
        self.put(SP + 0x30, '<I', METADATA if source_present else 0)
        self.setreg('EBP', ACTOR)
        return self._run(0x121a30, {0x121a4c}, ('constructor_copy_island',),
            writes=((ACTOR + 0x1ea, ACTOR + 0x1eb), (ACTOR + 0xdb0, ACTOR + 0xde8)))

    def _display(self, handle, active):
        if type(handle) is not int or not 0 <= handle <= 0xffff or type(active) is not bool:
            raise ValueError('Expected WORD handle and explicit display-active flag')
        self.display_record = DISPLAY + DISPLAY_STRIDE * (handle if handle < 0x1000 else 0)
        NativeWorldActor._map_rw(self.native.native, self.display_record, 0x100)
        self.vm.mem_write(self.display_record, bytes((self.poison,)) * 0x100)
        self.put(self.display_record + 0x28, '<i', 0 if active else -1)
        self.put(ACTOR + 0x1d8, '<H', handle)

    def consume(self, *, handle=0, active=True):
        """Start at original metadata-type dispatch, stop at next dependency.

        This operand fixture points the consumer at actor+DB0. It does not
        claim the full caller always aliases its metadata argument to the actor.
        """
        self._display(handle, active)
        self._registers()
        self.put(SP + 0x68, '<I', ACTOR + 0xdb0)
        self.setreg('EBX', ACTOR)
        self.setreg('EBP', DISPLAY)
        before = bytes(self.vm.mem_read(ACTOR, 4096))
        trace = self._run(0x12ce4b, {0x12d1b9, 0x12d02a, 0x12ce64},
            ('display_type_dispatch', 'normal_type_dispatch', 'two_text_arguments',
             'primary_text_setter', 'secondary_text_setter'),
            writes=((self.display_record + 0x70, self.display_record + 0x92),))
        if bytes(self.vm.mem_read(ACTOR, 4096)) != before:
            raise AssertionError('Text consumer changed actor storage')
        trace.update(display_hex=bytes(self.vm.mem_read(self.display_record, 0x100)).hex(),
                     actor_unchanged=True, scalar_hex=before[0xde8:0xdf8].hex())
        return trace

    def normal_name(self, *, handle=0):
        """Source-backed normal name island, after the level-display dependency."""
        packed = struct.unpack('<I', self.vm.mem_read(ACTOR + 0xdb4, 4))[0]
        if packed & 0xc000 or packed & 0xff0000:
            raise ValueError('Normal EnyName branch without special override only')
        self._display(handle, True)
        self._registers()
        self.put(SP + 0x10, '<I', MANAGER)
        self.setreg('EBX', ACTOR)
        self.setreg('ESI', ACTOR + 0xdb0)
        self.setreg('EBP', DISPLAY)
        before = bytes(self.vm.mem_read(ACTOR, 4096))
        stops = {0x12d15e, 0x12d184}
        if not self.enemy_payload:
            stops.add(0x10980e)
        trace = self._run(0x12d0c4, stops,
            ('normal_enemy_name', 'enemy_lookup', 'primary_text_setter'),
            writes=((ACTOR + 0xdbe, ACTOR + 0xdce),
                    (self.display_record + 0x70, self.display_record + 0x81)))
        after = bytes(self.vm.mem_read(ACTOR, 4096))
        if before[:0xdbe] != after[:0xdbe] or before[0xdce:] != after[0xdce:]:
            raise AssertionError('Normal name consumer changed unrelated actor storage')
        trace.update(actor_before_hex=before[0xdb0:0xdf8].hex(),
            actor_after_hex=after[0xdb0:0xdf8].hex(),
            display_hex=bytes(self.vm.mem_read(self.display_record, 0x100)).hex())
        return trace

    def reuse_actor_name(self):
        """Original follow-on actor+DBE NUL scan/copy, through its real stores."""
        self._registers()
        self.vm.mem_write(GETTER_OUTPUT, bytes((self.poison,)) * 64)
        self.put(SP + 0x10, '<I', GETTER_OUTPUT)
        self.setreg('EAX', ACTOR)
        trace = self._run(0x116577, {0x11659c}, ('actor_name_reuse',),
                          writes=((GETTER_OUTPUT, GETTER_OUTPUT + 16),))
        trace['output_hex'] = bytes(self.vm.mem_read(GETTER_OUTPUT, 64)).hex()
        return trace

    def read_secondary(self, *, handle=0):
        self._registers()
        self.vm.mem_write(GETTER_OUTPUT, bytes((self.poison,)) * 64)
        self.put(SP, '<III', BASE + 0x1000, handle, GETTER_OUTPUT)
        self.setreg('ECX', DISPLAY)
        trace = self._run(0x109f20, {0x1000}, ('secondary_text_getter',),
                          writes=((GETTER_OUTPUT, GETTER_OUTPUT + 17),))
        trace.update(output_hex=bytes(self.vm.mem_read(GETTER_OUTPUT, 64)).hex(),
                     eax=self.getreg('EAX'))
        return trace

    def evidence(self):
        text = self.stage(b'ProbeName\0'.ljust(16, b'X'), b'ProbeCaption\0'.ljust(16, b'Y'))
        text['consumer'] = self.consume()
        text['secondary_getter'] = self.read_secondary()
        normal = self.stage(bytes((1, 0, 0, 0)) + b'Q' * 12,
                            b'NOT_A_STAT\0'.ljust(16, b'R'), variant=0x400)
        normal['dispatch'] = self.consume()
        normal['name_consumer'] = self.normal_name()
        normal['actor_name_reuse'] = self.reuse_actor_name()
        return {'schema': 'current-participant-metadata-semantics-v1',
            'image': {'file': str(IMAGE), 'sha256': IMAGE_SHA256, 'base': BASE,
                      'rva_equals_file_offset': True},
            'static_xrefs': self.xrefs,
            'native_spans': {name: {'start_rva': lo, 'end_rva_exclusive': hi,
                                   'sha256': sha(self.image[lo:hi])}
                             for name, (lo, hi) in SPANS.items()},
            'text_branch': text, 'normal_branch': normal,
            'enemy_source': {'file': GAME_FILE, 'sha256': GAME_SHA256,
                'decoded_sha256': GAME_DECODED_SHA256, **{k: self.native.row[k] for k in
                ('source_record_index', 'source_offset', 'source_line', 'record_sha256',
                 'raw_record_hex', 'area_generation', 'area', 'scene', 'ordinal')}},
            'promoted_semantics': {
                'metadata+E': 'primary displayed name for the executed text branch; '
                    'normal branch first uses area/scene then writes EnyName to actor+DBE',
                'metadata+1E': 'secondary NUL-terminated display text for the executed text branch; '
                    'specific title-system meaning unproven; not consumed by the normal name island'},
            'original_numeric_values': dict.fromkeys(('hp', 'mp', 'constitution', 'strength',
                                                     'intelligence', 'speed')),
            'constructor_completed': False, 'runtime_eligible': False,
            'game_return_adapters': [],
            'remaining': ['normal level/display path before 12D0C4',
                '12D15E onward: color/category UI and later scalar/display consumers',
                '12D1B9 onward: following display bindings',
                'normal constructor ROM dependency at 1206E0 remains outside these slices']}


def main():
    print(json.dumps(ParticipantMetadataProbe().evidence(), separators=(',', ':')))


if __name__ == '__main__':
    main()
