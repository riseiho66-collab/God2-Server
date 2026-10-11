"""Bounded current 1C fields 2000/6000; no complete actor or monster claims.

NPCAppearData IDs/names use a native loader projection with independently
staged source locals. Appearance DWORDs, actors and packets are diagnostics.
The complete NPC/EnyName loaders and prior variant sweeps never run here.
"""
import json
import struct

from .current_monster_variant_identity import (
    current_source, sha, IMAGE, IMAGE_SHA256, GAME_FILE, GAME_SHA256,
    GAME_DECODED_SHA256, BASE, SP, RETURN, BATTLE, MANAGER, PACKET, MESSAGES)
from .current_indoor_resources import STACK, SCRATCH
from .recover_companions import parse_sections
from unicorn import (Uc, UC_ARCH_X86, UC_MODE_32, UC_PROT_READ, UC_PROT_WRITE,
                     UC_PROT_EXEC, UC_HOOK_CODE, UC_HOOK_MEM_READ, UC_HOOK_MEM_WRITE,
                     UC_MEM_WRITE)
from unicorn import x86_const as reg

ACTOR, DISPLAY = 0x27000000, 0x28000000
COUNT, RECORDS, STRIDE = MESSAGES + 0x121e8, MESSAGES + 0x121ea, 94
FRAME, METADATA = SP - 0x1a8, SP - 0x1a8 + 0x3c
SECTION_START, SECTION_END = 7887, 140789
SECTION_SHA = 'da509feb26fc89ebdc6adc82cc70d42956e7ba47a0952ea05f55d4b7f2ee35e3'
SPANS = {
    'source_header_dispatch_static': (0x56272, 0x562b8),
    'source_id_guard_static': (0x5711d, 0x57139),
    'source_name_projection': (0x57147, 0x5717d),
    'source_maximum_projection': (0x575ea, 0x575fc),
    'packet_prefix': (0x115c90, 0x115df1),
    'slot_lookup': (0x11e6e0, 0x11e76a),
    'field6000': (0x11608b, 0x116149),
    'actor_metadata_copy': (0x116149, 0x11616b),
    'invalid_actor_diagnostic_prefix': (0x11616b, 0x11619d),
    'actor_call_arguments': (0x1161b4, 0x1161e8),
    'appearance_consumer_prefix': (0x1177c0, 0x117823),
    'dispatch_table_static': (0x11662c, 0x11663c),
}


def namespace(plain):
    if sha(plain) != GAME_DECODED_SHA256 or sha(plain[SECTION_START:SECTION_END]) != SECTION_SHA:
        raise ValueError('Pinned NPCAppearData source changed')
    section = parse_sections(plain, ('NPCAppearData',))['NPCAppearData']
    rows, seen = [], set()
    for index, row in enumerate(section['records']):
        fields = [bytes.fromhex(value) for value in row['fields_hex']]
        identity, name = int(fields[0]), fields[1]
        if (not 1 <= identity < 7000 or identity in seen or len(name) > 15
                or b'\0' in name or len(fields) not in (5, 9)):
            raise ValueError('Current NPC identity projection bounds')
        seen.add(identity)
        rows.append({key: row[key] for key in
                     ('source_line', 'decoded_offset', 'raw_record_hex', 'sha256', 'fields_hex')}
                    | {'source_record_index': index, 'selector': identity, 'name_hex': name.hex(),
                       'monster_classification': None, 'runtime_eligible': False})
    if len(rows) != 4043 or len(seen) != 4043 or max(seen) != 6224:
        raise ValueError('Current NPC source namespace changed')
    return rows


class OtherIdentityProbe:
    def __init__(self):
        self.image = IMAGE.read_bytes()
        if sha(self.image) != IMAGE_SHA256:
            raise ValueError('Pinned native image changed')
        self.rows = namespace(current_source())
        self.by_id = {row['selector']: row for row in self.rows}
        self.vm = Uc(UC_ARCH_X86, UC_MODE_32)
        size = (len(self.image) + 4095) & ~4095
        self.vm.mem_map(BASE, size)
        self.vm.mem_write(BASE, self.image)
        self.vm.mem_protect(BASE, size, UC_PROT_READ | UC_PROT_EXEC)
        for address, size in ((STACK, 0x80000), (SCRATCH, 0x10000), (MESSAGES, 0xe0000),
                              (BATTLE, 4096), (MANAGER & ~4095, 0x2000),
                              (ACTOR, 0x2000), (DISPLAY, 4096),
                              ((BATTLE + 0x83458) & ~4095, 4096),
                              ((BATTLE + 0xa9df740) & ~4095, 4096)):
            self.vm.mem_map(address, size, UC_PROT_READ | UC_PROT_WRITE)
        self.put(BATTLE + 0x28, '<I', MESSAGES)
        self.put(BATTLE + 0x83458, '<I', DISPLAY)
        self.put(DISPLAY + 0x528, '<I', 0xa5a5a5a5)
        self.put(BATTLE + 0xa9df740, '<H', 0x1234)
        self.put(BATTLE + 0xa9df744, '<H', 0x5678)
        self.put(COUNT, '<h', 0)
        self.projection_instructions = 0
        # Only source ID/name locals are staged; original instructions compute
        # slot addresses, copy names, and update the signed maximum selector.
        for row in self.rows:
            identity = row['selector']
            self._reset()
            self.put(SP + 0x10, '<I', identity)
            self.vm.mem_write(SP + 0x3c, bytes.fromhex(row['name_hex']) + b'\0')
            self.setreg('EBP', MESSAGES)
            pointer = RECORDS + STRIDE * identity
            trace = self._run(0x57147, {0x5717d}, ('source_name_projection',),
                              writes=((pointer, pointer + 16),))
            if self.getreg('EDX') != pointer or self.getreg('ESP') != SP - 4:
                raise AssertionError('Native source projection address/stack mismatch')
            self.projection_instructions += len(trace['visits'])
            self.setreg('ECX', identity)
            trace = self._run(0x575ea, {0x575fc}, ('source_maximum_projection',),
                              reads=((COUNT, COUNT + 2),), writes=((COUNT, COUNT + 2),))
            self.projection_instructions += len(trace['visits'])
        self.source_maximum = struct.unpack('<h', self.vm.mem_read(COUNT, 2))[0]
        if self.source_maximum != 6224:
            raise AssertionError('Native source maximum mismatch')

    def put(self, address, fmt, *values):
        self.vm.mem_write(address, struct.pack(fmt, *values))

    def getreg(self, name):
        return self.vm.reg_read(getattr(reg, 'UC_X86_REG_' + name))

    def setreg(self, name, value):
        self.vm.reg_write(getattr(reg, 'UC_X86_REG_' + name), value)

    def _reset(self, poison=0xa5):
        self.vm.mem_write(SP - 0x1000, bytes((poison,)) * 0x1100)
        self.put(SP, '<II', RETURN, PACKET)
        for name in ('EAX', 'EBX', 'ECX', 'EDX', 'ESI', 'EDI', 'EBP'):
            self.setreg(name, poison * 0x01010101)
        self.setreg('ESP', SP)
        self.setreg('EFLAGS', 2)

    def _run(self, start, stops, names, *, reads=(), writes=(), budget=2500):
        ranges = [SPANS[name] for name in names]
        for lo, hi in ranges:
            if bytes(self.vm.mem_read(BASE + lo, hi - lo)) != self.image[lo:hi]:
                raise ValueError('Mapped original instructions changed')
        stack = (SP - 0x1000, SP + 0x100)
        allowed_reads = (stack, (BASE, BASE + len(self.image)), *reads)
        allowed_writes = (stack, *writes)
        trace = {'visits': [], 'reads': [], 'writes': [], 'appearance_call': None}

        def code(vm, address, size, _):
            rva = address - BASE
            if rva in stops:
                vm.emu_stop()
                return
            if not any(lo <= rva and rva + size <= hi for lo, hi in ranges):
                raise AssertionError(f'Unqualified callee/instruction {rva:x}')
            trace['visits'].append(rva)
            if rva == 0x1160b3:
                trace['selected_record_pointer'] = self.getreg('EDI')
            if rva == 0x1177c0:
                sp = self.getreg('ESP')
                ret, pointer = struct.unpack('<II', vm.mem_read(sp, 8))
                if ret != BASE + 0x116117 or pointer != FRAME + 0x2c:
                    raise AssertionError('Unexpected appearance consumer arguments')
                trace['appearance_call'] = {'return_rva': ret - BASE, 'this': self.getreg('ECX'),
                    'argument_pointer': pointer, 'request_hex': bytes(vm.mem_read(pointer, 14)).hex()}

        def memory(vm, access, address, size, value, _):
            write = access == UC_MEM_WRITE
            if not any(lo <= address and address + size <= hi for lo, hi in
                       (allowed_writes if write else allowed_reads)):
                raise AssertionError(f'Unqualified {"write" if write else "read"} '
                                     f'{address:x}/{size} at {self.getreg("EIP") - BASE:x}')
            trace['writes' if write else 'reads'].append((self.getreg('EIP') - BASE, address, size))

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
        trace['stop_rva'] = stop
        return trace

    def join(self, field, selector, *, slot=14, ordinal=0x4321, variant_bits=0,
             actor_present=True, actor_handle=7, poison=0xa5, maximum=None,
             appearance=b'\x12\x34\x56\x78\x9a\xbc\xde\xf0',
             prior_metadata=bytes(range(56)), payload=bytes(range(36))):
        if (any(type(x) is not int for x in (field, selector, slot, ordinal, variant_bits,
                                            actor_handle, poison))
                or field not in (0x2000, 0x6000) or not 0 <= selector <= 65535
                or not 0 <= slot < 28 or not 0 <= ordinal <= 65535
                or not 0 <= variant_bits <= 65535 or variant_bits & 0x6000
                or not -32768 <= actor_handle <= 32767 or not 0 <= poison <= 255
                or type(actor_present) is not bool
                or type(appearance) is not bytes or len(appearance) != 8
                or type(prior_metadata) is not bytes or len(prior_metadata) != 56
                or type(payload) is not bytes or len(payload) != 36
                or maximum is not None and (type(maximum) is not int or not -32768 <= maximum <= 32767)):
            raise ValueError('Bounded other-identity diagnostic inputs required')
        bound = self.source_maximum if maximum is None else maximum
        self.put(COUNT, '<h', bound)
        packet = bytes((0x1c, slot, 23)) + struct.pack('<HHH', selector, field | variant_bits, ordinal) + payload
        self.vm.mem_write(PACKET, packet)
        self.vm.mem_write(MANAGER + 0x38, bytes(28 * 24))
        if actor_present:
            self.put(MANAGER + 0x38 + slot * 24, '<I', ACTOR)
        self.vm.mem_write(ACTOR, bytes((poison,)) * 0x2000)
        self.put(ACTOR + 0x1a, '<h', actor_handle)
        self.vm.mem_write(ACTOR + 0xdb0, prior_metadata)
        before = bytes(self.vm.mem_read(ACTOR, 0x2000))
        self._reset(poison)
        self.setreg('ECX', BATTLE)
        reads = [(PACKET, PACKET + 45), (MANAGER + 0x38, MANAGER + 0x38 + 28 * 24),
                 (ACTOR + 0xdb0, ACTOR + 0xde8), (ACTOR + 0x1a, ACTOR + 0x1c),
                 (BATTLE + 0x28, BATTLE + 0x2c), (COUNT, COUNT + 2),
                 (BATTLE + 0x83458, BATTLE + 0x8345c), (DISPLAY + 0x528, DISPLAY + 0x52c),
                 (BATTLE + 0xa9df740, BATTLE + 0xa9df746)]
        if field == 0x6000 and selector <= bound and selector in self.by_id:
            pointer = RECORDS + STRIDE * selector
            self.vm.mem_write(pointer + 0x14, appearance)
            reads += [(pointer, pointer + len(bytes.fromhex(self.by_id[selector]['name_hex'])) + 1),
                      (pointer + 0x14, pointer + 0x1c)]
        # In-range absent slots are stopped BEFORE the first unbacked name scan.
        stops = {0x1161e8, 0x11619d, 0x1182b9}
        if field == 0x6000 and selector <= bound and selector not in self.by_id:
            stops.add(0x1160b9)
        trace = self._run(0x115c90, stops,
            ('packet_prefix', 'slot_lookup', 'field6000', 'actor_metadata_copy',
             'invalid_actor_diagnostic_prefix', 'actor_call_arguments', 'appearance_consumer_prefix'),
            reads=reads, writes=((ACTOR + 0xdb0, ACTOR + 0xde8),))
        after = bytes(self.vm.mem_read(ACTOR, 0x2000))
        if before[:0xdb0] != after[:0xdb0] or before[0xde8:] != after[0xde8:]:
            raise AssertionError('Actor canary changed')
        if bytes(self.vm.mem_read(PACKET, 45)) != packet:
            raise AssertionError('Original branch changed diagnostic packet')
        trace.update(field=field, selector=selector, packet_hex=packet.hex(),
                     metadata_hex=bytes(self.vm.mem_read(METADATA, 56)).hex(),
                     actor_metadata_hex=after[0xdb0:0xde8].hex(),
                     input_authority='synthetic_packet_actor_and_appearance_dwords',
                     maximum=bound, maximum_authority='source_native_projection' if maximum is None
                     else 'diagnostic_signed_word', actor_present=actor_present)
        if trace['stop_rva'] == 0x1161e8:
            trace['next_call'] = {'callee_rva': 0x1221b0, 'executed': False,
                'this': self.getreg('ECX'), 'arguments': list(struct.unpack('<8I',
                    self.vm.mem_read(self.getreg('ESP'), 32)))}
        return trace

    def evidence(self):
        inventory = []
        for row in self.rows:
            trace = self.join(0x6000, row['selector'])
            name = bytes.fromhex(row['name_hex']) + b'\0'
            if (trace['selected_record_pointer'] != RECORDS + STRIDE * row['selector']
                    or bytes.fromhex(trace['metadata_hex'])[14:14 + len(name)] != name
                    or trace['stop_rva'] != 0x1182b9):
                raise AssertionError('Source-backed native branch identity mismatch')
            inventory.append(row | {'native_record_pointer': trace['selected_record_pointer'],
                                    'native_stop_rva': trace['stop_rva']})
        return {
            'schema': 'current-monster-other-identity-v1',
            'image': {'path': str(IMAGE), 'sha256': IMAGE_SHA256, 'base': BASE, 'rva_equals_file_offset': True},
            'source': {'file': GAME_FILE, 'sha256': GAME_SHA256, 'decoded_sha256': GAME_DECODED_SHA256,
                       'section': 'NPCAppearData', 'decoded_offset': SECTION_START,
                       'end_offset_exclusive': SECTION_END, 'section_sha256': SECTION_SHA},
            'native_spans': {name: {'source_offset': lo, 'end_offset_exclusive': hi,
                                   'sha256': sha(self.image[lo:hi]), 'source_sha256': IMAGE_SHA256}
                             for name, (lo, hi) in SPANS.items()},
            'authority': {'table': 'native_ID_name_and_maximum_projections_from_independently_staged_source_locals',
                          'full_loader_executed': False, 'appearance_dwords': 'explicit_diagnostic_only',
                          'packet_and_actor': 'explicit_diagnostic_only',
                          'sparse_slots': 'stop_before_unbacked_payload_read'},
            'coverage': {'source_rows': len(inventory), 'unique_source_selectors': len(self.by_id),
                         'native_source_projection_instructions': self.projection_instructions,
                         'maximum_selector': self.source_maximum, 'native_field6000_source_joins': len(inventory),
                         'in_range_slots_without_source_row': self.source_maximum + 1 - len(inventory),
                         'verified_stat_skill_drop_assignments': 0, 'all_monsters_including_boss': None,
                         'monster_classification': None, 'all_monster_systems_enumerated': False},
            'field2000': self.join(0x2000, 0xabcd),
            'field6000': self.join(0x6000, self.rows[0]['selector']),
            'field6000_out_of_range': self.join(0x6000, 65535),
            'source_inventory': inventory, 'runtime_eligible': False,
            'remaining_frontier': [
                '1182B9: further actor-slot consumers in original 1177C0; then original return 116117.',
                '1161E8 -> 1221B0: prepared actor call, callee not executed.',
                '11619D -> 2B10: invalid actor-handle diagnostic, callee not executed.',
                '1160B9: in-range sparse slots have no current source row; payload not read.',
                'Original NPC appearance packing, live actor provenance, original 1C sender and classifier; '
                'no stat/skill/drop producer qualified.'],
        }


def main():
    print(json.dumps(OtherIdentityProbe().evidence(), ensure_ascii=True, separators=(',', ':')))


if __name__ == '__main__':
    main()
