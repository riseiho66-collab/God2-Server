"""Whole-source pet/egg evidence matrix; no authoritative gameplay defaults."""
import argparse
from collections import Counter
from itertools import product
import json
from pathlib import Path
import struct
import time

from . import current_companion_instance as instance
from . import current_companion_progression as progression
from . import current_item_transition as item
from . import recover_companion_growth as growth
from . import recover_items
from . import recover_pet_incubation as incubation

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CLIENT = ROOT.parent / 'God2'
DEFAULT_IMAGE = ROOT / 'artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin'
PATTERNS = (0, 0xffffffff, 0xa5a5a5a5, 0x5a5a5a5a, *(1 << bit for bit in range(32)))
DISPATCHES = ('primary', 'secondary')
MODES = (1, 0x100)
EGG_RANGES = ((0xd6c40, 0xd6c78), (0xd6c80, 0xd6d1e), (0x59a60, 0x59a7e))
UNKNOWN = ('growth_formula', 'experience_thresholds', 'hatch_probability',
           'hatch_result_distribution', 'incubation_timer', 'transaction_rules')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def source_inventory(decoded, evidence):
    files = {}
    for name, data in decoded.items():
        rows, offset = [], 0
        pieces = data.split(b'\n')
        for index, piece in enumerate(pieces):
            if index == len(pieces) - 1 and not piece:
                break
            raw = piece + (b'\n' if index < len(pieces) - 1 else b'')
            rows.append({'line': index + 1, 'offset': offset, 'length': len(raw),
                         'sha256': growth.digest(raw)})
            offset += len(raw)
        require(offset == len(data), 'Source ledger omitted bytes')
        files[name] = {'path': growth.source_path(name), 'decoded_sha256': growth.digest(data),
                       'physical_row_count': len(rows), 'rows': rows}
    groups = {}
    for name, section in evidence['sections'].items():
        groups[name] = {'source': 'gamedata', 'declared_count': section['declared_count'],
                        'header_line': section['header']['source_line'],
                        'lines': [r['source_line'] for r in section['records']]}
    for name, table in evidence['auxiliary_tables'].items():
        groups[name] = {'source': name, 'declared_count': table.get('declared_count_literal'),
                        'lines': [r['source_line'] for r in table['records']]}
    texts = [{'source': Path(t['source_file']).stem, 'section': t['section'],
              'lines': [r['source_line'] for r in t['records']]}
             for t in evidence['text_only_records']]
    return {'files': files, 'growth_groups': groups, 'selected_text_groups': texts,
            'physical_rows': sum(f['physical_row_count'] for f in files.values()),
            'growth_rows': sum(len(g['lines']) for g in groups.values()),
            'selected_text_rows': sum(len(t['lines']) for t in texts)}


def join_definition(entry, definitions):
    candidates = [r for r in definitions if r['client_item_id'] == entry['source_key']]
    if len(candidates) != 1:
        return {'status': 'unjoined', 'reason': 'missing' if not candidates else 'ambiguous',
                'candidate_keys': sorted(r['definition_key'] for r in candidates)}
    definition = candidates[0]
    source = entry['source']
    raw = bytes.fromhex(source['raw_record_hex']).removesuffix(b'\n').removesuffix(b'\r')
    if (definition['section'] != entry['section'] or
            definition['source_line'] != source['source_line'] or
            definition['raw_fields_hex'] != source['fields_hex'] or
            definition['source_record_sha256'] != growth.digest(raw)):
        return {'status': 'unjoined', 'reason': 'source_mismatch',
                'candidate_keys': [definition['definition_key']]}
    return {'status': 'source_qualified', 'definition': definition,
            'native_metadata_loader_verified': False}


class EggGuard:
    """Existing item VM; source-qualified presence index, never fake metadata.

    Original 59A60 only reads a pointer. Rows are raw source bytes, NOT native
    item structures. Reads into those bytes are forbidden by this fixture.
    """
    SOURCE = 0x3900000

    def __init__(self, entries, joins):
        self.deadline = time.monotonic() + 120
        self.native = item.NativeItemTransition()
        self.vm = self.native.vm
        self.vm.mem_map(self.SOURCE, 0x10000, instance.uc.UC_PROT_READ)
        self.pointers = {}
        at = self.SOURCE
        for entry, join in zip(entries, joins):
            if join['status'] != 'source_qualified':
                continue
            raw = bytes.fromhex(entry['source']['raw_record_hex'])
            require(at + len(raw) <= self.SOURCE + 0x10000, 'Egg source arena exhausted')
            self.vm.mem_write(at, raw)
            self.pointers[entry['source_key']] = at
            self.vm.mem_write(item.DEFINITIONS + 0xb2d40 + 4 * entry['source_key'], struct.pack('<I', at))
            at += len(raw)
        self.active = False
        self.vm.hook_add(instance.uc.UC_HOOK_CODE, self._code)
        self.vm.hook_add(instance.uc.UC_HOOK_MEM_WRITE, self._write)
        self.vm.hook_add(instance.uc.UC_HOOK_MEM_READ, self._read)

    def _code(self, vm, address, size, context):
        if not self.active:
            return
        pc = address - item.BASE
        if address in (item.RETURN, item.BASE + 0x2c70):
            vm.emu_stop()
            return
        require(any(a <= pc < z for a, z in EGG_RANGES), 'Unexpected egg instruction')

    def _write(self, vm, access, address, size, value, context):
        if self.active:
            require(item.STACK <= address < address + size <= item.STACK + 0x4000,
                    'Egg guard wrote non-stack state')

    def _read(self, vm, access, address, size, value, context):
        if not self.active:
            return
        require(not self.SOURCE <= address < self.SOURCE + 0x10000,
                'Presence probe unexpectedly dereferenced source as metadata')
        if vm.reg_read(item.UC_X86_REG_EIP) == item.BASE + 0x59a6f:
            self.lookups.append([address, size])

    def run(self, slot, identity):
        require(time.monotonic() < self.deadline, 'Egg matrix exceeded 120-second deadline')
        self.vm.mem_write(item.SP - 0x80, b'\xa5' * 0x100)
        self.vm.mem_write(item.SP, struct.pack('<III', item.RETURN, slot, identity))
        self.vm.reg_write(item.UC_X86_REG_ESP, item.SP)
        self.vm.reg_write(item.UC_X86_REG_ECX, item.UI)
        self.vm.reg_write(instance.x86.UC_X86_REG_EFLAGS, 2)
        self.lookups = []
        self.active = True
        try:
            self.vm.emu_start(item.BASE + 0xd6c80, 0, count=1000)
        finally:
            self.active = False
        pc = self.vm.reg_read(item.UC_X86_REG_EIP)
        sp = self.vm.reg_read(item.UC_X86_REG_ESP)
        require(pc in (item.RETURN, item.BASE + 0x2c70), 'Egg guard did not reach boundary')
        if pc == item.RETURN:
            require(sp == item.SP + 12, 'Egg return stack mismatch')
            outcome = {'kind': 'return', 'value': self.vm.reg_read(item.UC_X86_REG_EAX)}
        else:
            outcome = {'kind': 'assert', 'value': struct.unpack('<I', self.vm.mem_read(sp + 12, 4))[0]}
        outcome['lookup_reads'] = self.lookups
        return outcome


def expected_guard(slot, identity, joined):
    if not (slot < 30 or slot == 45):
        kind, value, reads = 'assert', 0x57a, []
    elif not 9301 <= identity <= 9500:
        kind, value, reads = 'assert', 0x586, []
    else:
        kind, value = ('return', 1) if joined else ('assert', 0x58b)
        reads = [[item.DEFINITIONS + 0xb2d40 + 4 * identity, 4]]
    return {'kind': kind, 'value': value, 'lookup_reads': reads}


def egg_matrix(entries, definitions):
    joins = [join_definition(entry, definitions) for entry in entries]
    native = EggGuard(entries, joins)
    before = native.native._snapshot()
    rows = []
    for entry, join in zip(entries, joins):
        key = entry['source_key']
        outcomes = [dict(slot=slot, **native.run(slot, key)) for slot in range(256)]
        row = {'source_key': key, 'section': entry['section'], 'source': entry['source'],
               'join': join, 'guard_cases': outcomes, 'guard_case_count': len(outcomes),
               'guard_returns': sum(c['kind'] == 'return' for c in outcomes),
               'guard_assertions': sum(c['kind'] == 'assert' for c in outcomes),
               'claims': entry['claims'], 'unknown': entry['unknown'], 'runtime_eligible': False}
        if join['status'] == 'source_qualified':
            address = item.DEFINITIONS + 0xb2d40 + 4 * key
            native.vm.mem_write(address, bytes(4))
            missing = native.run(45, key)
            native.vm.mem_write(address, struct.pack('<I', native.pointers[key]))
            row['presence_transition'] = [missing, native.run(45, key)]
        else:
            row['presence_transition'] = []
        rows.append(row)
    present = {entry['source_key'] for entry in entries}
    absent = [dict(source_key=key, **native.run(45, key))
              for key in range(9301, 9501) if key not in present]
    outside = [dict(source_key=key, **native.run(0, key)) for key in (0, 9300, 9501, 65535)]
    require(before == native.native._snapshot(), 'Egg matrix changed non-stack state')
    return {'entries': rows, 'absent_range_keys': absent, 'outside_range': outside,
            'unjoined': [r['source_key'] for r in rows if r['join']['status'] == 'unjoined'],
            'definition_denominator': len(definitions), 'native_metadata_loader_verified': False,
            'presence_index_policy': 'Only exact source-definition joins receive pointers to raw rows; '
                                     'native record dereferences are forbidden. Not native metadata layout.'}


def instance_coordinates():
    for dispatch, auxiliary, slot in product(DISPATCHES, (0, 1), range(256)):
        for packed in PATTERNS if slot < 50 else (0xf5a39c7e,):
            yield dispatch, auxiliary, slot, packed


def packet_stop(slot, auxiliary):
    if slot >= 50:
        return 0x98fbd
    return 0x98e05 if 38 <= slot <= 41 and auxiliary == 1 else 0x98e2d


class MatrixInstance(instance.NativeInstance):
    """Same helper guards and 300-instruction cap, one matrix wall deadline.

    Avoid starting a native watchdog thread for each tiny slice. The inherited
    instruction hook still rejects unknown code and stops at exact boundaries.
    """
    def __init__(self, image):
        super().__init__(image)
        self.deadline = time.monotonic() + 120

    def run(self, start, stops, names, writes=()):
        require(time.monotonic() < self.deadline, 'Instance matrix exceeded 120-second deadline')
        self.stops = set(stops)
        self.allowed_code = [instance.RANGES[name] for name in names]
        self.allowed_writes = list(writes)
        self.reads, self.writes, self.pcs = [], [], []
        self.active = True
        try:
            self.vm.emu_start(instance.BASE + start, 0, count=300)
        finally:
            self.active = False
        pc = self.reg('EIP') - instance.BASE
        require(pc in self.stops, 'Native slice did not reach exact stop')
        return {'stop_rva': pc, 'reads': self.reads[:], 'writes': self.writes[:],
                'instruction_count': len(self.pcs)}


def ui_selection(native, slot):
    """Reuse original selection slice without ui_copy's per-call poison reset."""
    native.prepare()
    native.vm.mem_write(native.OWNER + 0x855f0, struct.pack('<H', slot))
    native.reg('EBP', native.UI)
    before = bytes(native.vm.mem_read(native.RECORD - 4, 32))
    result = native.run(0x87394, (0x873b3, 0x87430), ('ui_selection_gate', 'ui_copy'),
                        ((native.RECORD, native.RECORD + 23),))
    copied = result['stop_rva'] == 0x87430
    expected = bytearray(before)
    if copied:
        source = bytes(native.vm.mem_read(native.STORE + 24 * slot, 20))
        expected[4:27] = source + source[:2] + bytes((slot,))
    after = bytes(native.vm.mem_read(native.RECORD - 4, 32))
    require(after == expected, 'UI copy/stale bytes or canary differs')
    require(copied or not result['writes'], 'Rejected UI selection wrote state')
    return {'stop_rva': result['stop_rva'], 'copied': copied,
            'stale_preserved': None if copied else after == before,
            'observed_packed': struct.unpack_from('<I', after, 16)[0] if copied else None}


def instance_matrix(image):
    native = MatrixInstance(image)
    native.packet_store(0, instance.record_for(0xf5a39c7e))
    native.ui_copy(0)
    cases = []
    for dispatch, auxiliary, slot, packed in instance_coordinates():
        before = bytes(native.vm.mem_read(native.RECORD, 24))
        result = native.packet_store(slot, instance.record_for(packed), dispatch, auxiliary)
        preserved = bytes(native.vm.mem_read(native.RECORD, 24)) == before
        require(preserved, 'Packet-only slice changed prior UI')
        require(result['stop_rva'] == packet_stop(slot, auxiliary), 'Packet outcome differs')
        selected = ui_selection(native, slot) if result['copied'] else None
        cases.append({'dispatch': dispatch, 'auxiliary': auxiliary, 'slot': slot, 'packed': packed,
                      'stop_rva': result['stop_rva'], 'copied': result['copied'],
                      'packet_stale_ui_preserved': preserved, 'ui': selected})
    gates = []
    for slot, flags in product((*range(50), 0x7fff, 0x8000, 0xffff), (0, 1, 2, 3)):
        before = bytes(native.vm.mem_read(native.RECORD, 24))
        result = native.ui_entry_gate(slot, flags)
        require(not result['writes'], 'UI entry gate wrote state')
        gates.append({'slot_word': slot, 'flags': flags, 'stop_rva': result['stop_rva'],
                      'stale_ui_preserved': bytes(native.vm.mem_read(native.RECORD, 24)) == before})
    return {'patterns': list(PATTERNS), 'cases': cases, 'entry_gates': gates,
            'per_slot': summarize_slots(cases)}


def summarize_slots(cases):
    counts = {slot: Counter() for slot in range(256)}
    for c in cases:
        counter = counts[c['slot']]
        counter['cases'] += 1
        counter['copied' if c['copied'] else 'intercepted' if c['stop_rva'] == 0x98e05 else 'rejected'] += 1
        if c['ui'] is not None:
            counter['ui_copied' if c['ui']['copied'] else 'ui_blocked_stale'] += 1
    return [{'slot': slot, **{key: counts[slot][key] for key in
             ('cases', 'copied', 'intercepted', 'rejected', 'ui_copied', 'ui_blocked_stale')}}
            for slot in range(256)]


def display_matrix(image, decoded):
    native = progression.NativeProgression(image, decoded)
    cases = [native.arguments((qi << 20) | (si << 16) | noise, mode)
             for mode, noise, qi, si in product(MODES, (0, 0xff00ffff), range(16), range(16))]
    gates = [native.gate(a, b) for a, b in product((0, 1, 2, 255), repeat=2)]
    return {'cases': cases, 'gates': gates, 'runtime_eligible': False,
            'classification': 'display_arguments_only',
            'source_lines': [r['source_line'] for r in
                             growth.parse_auxiliary(progression.SOURCE, decoded)['records']]}


def validate_report(report, decoded, evidence, eggs, definitions):
    """Validate exact denominators, identities and observations, not totals alone."""
    require(report['source_inventory'] == source_inventory(decoded, evidence), 'Source coverage/provenance differs')
    require(report['source_manifests'] == evidence['sources'], 'Source manifest differs')
    require(report['image_sha256'] == instance.IMAGE_SHA, 'Image identity differs')
    require(report['runtime_eligible'] is False and report['unknown_rules'] == dict.fromkeys(UNKNOWN),
            'Unproved gameplay rule promoted')
    require(report['growth_unknown_contracts'] == growth.unknown_contracts(), 'Growth unknowns differ')
    native_rows = report['native_growth_rows']
    require(native_rows['status'] == 'verified_bounded_original_row_execution' and
            native_rows['growth_formula_verified'] is False and
            native_rows['gameplay_runtime_verified'] is False, 'Native row evidence promoted')
    require(native_rows['GodLevel']['rows'] == len(evidence['sections']['GodLevel']['records']) and
            native_rows['CategoryDetailNum']['rows'] == len(evidence['auxiliary_tables']['NewCombatPet_Category']['records']),
            'Native row denominator differs')
    require(report['egg_guard']['native_metadata_loader_verified'] is False, 'Unproved metadata loader promoted')
    rows = report['egg_guard']['entries']
    require([r['source_key'] for r in rows] == [e['source_key'] for e in eggs], 'Egg omission/duplicate/order')
    for row, entry in zip(rows, eggs):
        key = entry['source_key']
        join = join_definition(entry, definitions)
        joined = join['status'] == 'source_qualified'
        require(row['join'] == join, 'Definition join differs')
        for field in ('section', 'source', 'claims', 'unknown', 'runtime_eligible'):
            require(row[field] == entry[field], 'Egg source/unknown evidence differs')
        expected = [dict(slot=slot, **expected_guard(slot, key, joined)) for slot in range(256)]
        require(row['guard_cases'] == expected and row['guard_case_count'] == 256, 'Egg guard coverage/outcome differs')
        require(row['guard_returns'] == sum(c['kind'] == 'return' for c in expected) and
                row['guard_assertions'] == sum(c['kind'] == 'assert' for c in expected), 'Per-entry counts differ')
        transitions = [expected_guard(45, key, False), expected_guard(45, key, True)] if joined else []
        require(row['presence_transition'] == transitions, 'Egg stale lookup result')
    require(report['egg_guard']['unjoined'] == [r['source_key'] for r in rows if r['join']['status'] == 'unjoined'],
            'Unjoined entries omitted')
    require(report['egg_guard']['definition_denominator'] == len(definitions), 'Definition denominator differs')
    present = {e['source_key'] for e in eggs}
    require(report['egg_guard']['absent_range_keys'] == [dict(source_key=k, **expected_guard(45, k, False))
            for k in range(9301, 9501) if k not in present], 'Absent range key coverage differs')
    require(report['egg_guard']['outside_range'] == [dict(source_key=k, **expected_guard(0, k, False))
            for k in (0, 9300, 9501, 65535)], 'Outside range coverage differs')
    cases = report['instance']['cases']
    coordinates = list(instance_coordinates())
    require(len(cases) == len(coordinates) and report['instance']['patterns'] == list(PATTERNS), 'Instance denominator differs')
    for c, coordinate in zip(cases, coordinates):
        require(tuple(c[k] for k in ('dispatch', 'auxiliary', 'slot', 'packed')) == coordinate,
                'Instance omission/duplicate/order')
        dispatch, auxiliary, slot, packed = coordinate
        stop = packet_stop(slot, auxiliary)
        require(c['stop_rva'] == stop and c['copied'] is (stop == 0x98e2d), 'Invalid packet outcome')
        require(c['packet_stale_ui_preserved'] is True, 'Packet stale UI differs')
        if stop == 0x98e2d:
            copied = slot < 30 or slot in (42, 43)
            require(c['ui'] == {'stop_rva': 0x87430 if copied else 0x873b3, 'copied': copied,
                    'stale_preserved': None if copied else True,
                    'observed_packed': packed if copied else None}, 'UI selection/copy/stale differs')
        else:
            require(c['ui'] is None, 'Unaccepted packet promoted to UI instance')
    require(report['instance']['per_slot'] == summarize_slots(cases), 'Per-slot counts differ')
    gates = [{'slot_word': s, 'flags': f, 'stop_rva': 0x87372 if s < 0x8000 and f & 1 else 0x874c0,
              'stale_ui_preserved': True}
             for s, f in product((*range(50), 0x7fff, 0x8000, 0xffff), (0, 1, 2, 3))]
    require(report['instance']['entry_gates'] == gates, 'UI gate coverage/outcome differs')
    source_rows = growth.parse_auxiliary(progression.SOURCE, decoded[progression.SOURCE])['records']
    values = [[growth.decimal(v) for v in growth.fields(r)] for r in source_rows]
    expected_display = []
    for mode, noise, qi, si in product(MODES, (0, 0xff00ffff), range(16), range(16)):
        expected_display.append({'packed': qi << 20 | si << 16 | noise, 'mode': mode,
            'quality': [qi, values[0][qi]], 'star': [si, values[1][si]], 'table_reads': [
                [0xb7e38 if mode == 1 else 0xb7efd, 0x3400000 + qi * 2, 2],
                [0xb7f98, 0x3400100 + si * 2, 2]]})
    require(report['display']['cases'] == expected_display, 'Display coverage/provenance differs')
    require(report['display']['runtime_eligible'] is False, 'Display promoted to gameplay')
    require(report['display']['gates'] == [{'first': a, 'second': b, 'sum': a + b, 'admitted': a + b == 1}
            for a, b in product((0, 1, 2, 255), repeat=2)], 'Display gate differs')
    require(report['counts'] == report_counts(report), 'Summary denominator differs')


def report_counts(report):
    eggs, cases = report['egg_guard']['entries'], report['instance']['cases']
    return {'egg_entries': len(eggs), 'egg_sections': dict(Counter(e['section'] for e in eggs)),
            'joined_entries': sum(e['join']['status'] == 'source_qualified' for e in eggs),
            'unjoined_entries': len(report['egg_guard']['unjoined']),
            'egg_guard_cases': sum(e['guard_case_count'] for e in eggs),
            'presence_transition_cases': sum(len(e['presence_transition']) for e in eggs),
            'absent_range_cases': len(report['egg_guard']['absent_range_keys']),
            'outside_range_cases': len(report['egg_guard']['outside_range']),
            'growth_rows': report['source_inventory']['growth_rows'],
            'native_growth_rows': report['native_growth_rows']['GodLevel']['rows'] +
                                  report['native_growth_rows']['CategoryDetailNum']['rows'] + 2,
            'physical_source_rows': report['source_inventory']['physical_rows'],
            'instance_cases': len(cases), 'instance_in_store_cases': sum(c['slot'] < 50 for c in cases),
            'instance_rejection_cases': sum(c['slot'] >= 50 for c in cases),
            'instance_copies': sum(c['copied'] for c in cases),
            'instance_interceptions': sum(c['stop_rva'] == 0x98e05 for c in cases),
            'ui_copies': sum(c['ui'] is not None and c['ui']['copied'] for c in cases),
            'ui_blocked_stale': sum(c['ui'] is not None and not c['ui']['copied'] for c in cases),
            'ui_entry_cases': len(report['instance']['entry_gates']),
            'display_cases': len(report['display']['cases']), 'display_gate_cases': len(report['display']['gates'])}


def inputs(client_root):
    _, decoded = growth.load_current_sources(client_root)
    evidence = growth.build_growth(client_root)
    eggs = incubation.extract(growth.read_source(client_root, incubation.GAME))['entries']
    discovered = growth.parse_sections(decoded['gamedata'], ('EGG', 'SPP'))
    require([(e['section'], e['source']['source_line']) for e in eggs] ==
            [(tag, row['source_line']) for tag, section in discovered.items() for row in section['records']],
            'Egg extractor omitted/reordered current source rows')
    return decoded, evidence, eggs, recover_items.parse_items(decoded['gamedata'])['records']


def build_matrix(client_root=DEFAULT_CLIENT, image_path=DEFAULT_IMAGE):
    decoded, evidence, eggs, definitions = inputs(client_root)
    image = instance.qualified_image(image_path)
    native_rows = growth.verify_native_rows(image_path, decoded)
    report = {'schema': 'god2-pet-egg-coverage-matrix-v1', 'image_sha256': instance.digest(image),
              'runtime_eligible': False, 'unknown_rules': dict.fromkeys(UNKNOWN),
              'growth_unknown_contracts': evidence['unknown_contracts'],
              'source_manifests': evidence['sources'], 'source_inventory': source_inventory(decoded, evidence),
              'native_growth_rows': native_rows, 'egg_guard': egg_matrix(eggs, definitions),
              'instance': instance_matrix(image), 'display': display_matrix(image, decoded[progression.SOURCE]),
              'code_ranges': {f'egg_{a:x}': {'start': a, 'stop_exclusive': z, 'sha256': growth.digest(image[a:z])}
                              for a, z in EGG_RANGES},
              'proven_fields': {
                  'source': ['physical row bytes/hash/offset', 'section membership', 'literal source flags and text'],
                  'guard': ['low-byte slot/range', 'low-word item range', 'source-qualified lookup presence'],
                  'input': ['bounded packet-to-store copies', 'UI selection/copy', 'blocked-path stale UI preservation'],
                  'display': ['quality/star selector nibbles', 'literal table WORDs', 'format argument values'],
                  'native_rows': ['GodLevel title slots', 'Category columns 0..8 only', 'QualityStar WORD loading']},
              'boundaries': [
                  'All seven files have complete physical-row ledgers; 5023 growth-table records are a separate denominator.',
                  'Source flags/labels/text are not native rules. Egg pointers prove qualified presence only, not native metadata layout.',
                  'Native growth execution covers GodLevel, Category and QualityStar row slices only; other rows are source provenance.',
                  'Synthetic input records; original bounded instructions. No transport, live gameplay, ownership or transaction proof.',
                  'Packet slices stop before metadata calls. Auxiliary state 1 interception stops before 961A0, not permanent rejection.',
                  'UI selection starts after unexecuted 9B770. Entry gates stop before that call; formatting never executes.',
                  'Packet helper resets slot-store poison between probes. UI memory is retained to check stale preservation.',
                  'Growth row adapter is existing CRT decimal parsing only; no game-call success stubs.',
                  'One VM per egg, instance, display and growth-row lane. Egg/instance: 1000/300 instructions per call, exact stops, 120-second lane deadlines.',
                  'Existing display/row helpers retain their per-call instruction caps and one-second timeouts.'],
              'dependencies': {name: growth.digest(Path(__file__).with_name(name).read_bytes()) for name in (
                  'current_companion_instance.py', 'current_companion_progression.py', 'current_item_transition.py',
                  'recover_companion_growth.py', 'recover_pet_incubation.py', 'recover_items.py',
                  'recover_companions.py', 'current_npc_resources.py')}}
    report['counts'] = report_counts(report)
    validate_report(report, decoded, evidence, eggs, definitions)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--client-root', type=Path, default=DEFAULT_CLIENT)
    parser.add_argument('--native-image', type=Path, default=DEFAULT_IMAGE)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    if args.check and args.output is None:
        parser.error('--check requires --output')
    if args.output is not None:
        target = args.output.resolve()
        if target.is_relative_to(args.client_root.resolve()) or target == args.native_image.resolve():
            parser.error('Output must not overwrite current evidence')
    start = time.perf_counter()
    report = build_matrix(args.client_root, args.native_image)
    payload = growth.serialize(report)
    if args.output is None:
        print(payload.decode('ascii'), end='')
    else:
        if args.check:
            require(args.output.read_bytes() == payload, 'Matrix artifact differs')
        else:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_bytes(payload)
        print(json.dumps({'counts': report['counts'], 'sha256': growth.digest(payload),
                          'bytes': len(payload), 'elapsed_seconds': round(time.perf_counter() - start, 3),
                          'checked': args.check}, sort_keys=True))


if __name__ == '__main__':
    main()
