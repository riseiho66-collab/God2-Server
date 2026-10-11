"""Current actor skill-action cache evidence, never an inferred monster repertoire.

The CLI emits JSON to stdout only. Explicit synthetic action/actor diagnostics
qualify native data flow; no synthetic value is promoted to original ownership.
Catalog bytes are a pinned memory precondition, not a duplicated file loader.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from .current_battle_entry import (
    BASE, BATTLE, SP, STACK, RETURN, NativeRun, pinned_image, IMAGE, IMAGE_SHA256,
    UC_HOOK_MEM_READ, UC_HOOK_MEM_WRITE, UC_X86_REG_EIP,
)
from .current_monster_inventory import pinned_catalog, SOURCE, SOURCE_SHA, PLAIN_SHA
from .current_skill_identity import (
    SOURCE as SKILL_SOURCE, SOURCE_SHA256 as SKILL_SHA, decode_definitions,
)

ROOT = Path(__file__).resolve().parents[2]
MANAGER, CATALOG = BATTLE + 0x144938, BATTLE + 0xa924d7c
RECORD, GATE = BATTLE + 0xa9e9cb0, 0x6800000
ACTORS, ACTOR_SIZE = 0x6900000, 0x1000
CACHE, CAPACITY, CURRENT, SELECTED = 0xdf8, 51, 0xec4, 0x1df
FIELDS = ('skill_assignments', 'use_conditions', 'trigger_conditions', 'observed_actions')
SPANS = {
    'dispatch': (0x114332, 0x1143a1),
    'action_prefix': (0x116ae0, 0x116c9c),
    'action_cache_producer': (0x116cf5, 0x116df6),
    'target_scan': (0x11e5e0, 0x11e62b),
    'actor_lookup': (0x11e6e0, 0x11e76a),
    'action_consumer_prefix': (0x12c520, 0x12c5d3),
    'skill_consumer': (0x12c731, 0x12c7d8),
    'consumer_null_return': (0x12cc2f, 0x12cc39),
    'action_dispatch_table': (0x1171ac, 0x1171eb),
    'consumer_dispatch_table': (0x12cc3c, 0x12cc98),
    'enemy_identity_join_frontier': (0x115df1, 0x115e77),
    'cache_reset_reference': (0x11ff12, 0x11ff2c),
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def actor_address(position):
    return ACTORS + position * 0x2000


class NativeSkillActions:
    """Reusable isolated VM, explicit actor bytes, unchanged native instructions.

    Producer runs from the real post-copy dispatch to BEFORE resource lookup
    116DF1. Consumer is a separate invocation of 12C520 on the SAME VM and actor;
    the intervening resource/UI path is neither skipped in-flight nor simulated.
    """
    def __init__(self, client=ROOT.parent / 'God2'):
        self.image = pinned_image()
        self.source = (Path(client) / SKILL_SOURCE).read_bytes()
        if sha(self.source) != SKILL_SHA:
            raise ValueError('Current skill source SHA256 mismatch')
        self.definitions = decode_definitions(self.source)
        self.definition_pointers = {CATALOG + d.source_offset - 4
                                    for d in self.definitions.values()}
        self.n = NativeRun(self.image)
        self.n.put(CATALOG, self.source[4:])
        self.n.put(MANAGER + 0x38, bytes(28 * 6 * 4))
        self.n.put32(MANAGER + 0x20, 0x6a00000)  # Opaque; never dereferenced.
        self.snapshots = {}
        self.record = None

    def pointer(self, bank, skill_id):
        definition = self.definitions.get((bank, skill_id))
        if definition is None:
            raise ValueError('No populated pinned skill definition')
        return CATALOG + definition.source_offset - 4

    def install_actors(self, snapshots):
        """Caller-owned exact snapshots; missing positions explicitly null."""
        for position, raw in snapshots.items():
            if (type(position) is not int or not 0 <= position < 28
                    or type(raw) is not bytes or len(raw) != ACTOR_SIZE):
                raise ValueError('Expected position 0..27 and exact actor bytes')
            for pointer in struct.unpack_from('<51I', raw, CACHE):
                if pointer and pointer not in self.definition_pointers:
                    raise ValueError('Existing cache pointer outside pinned definitions')
        self.n.put(MANAGER + 0x38, bytes(28 * 6 * 4))
        for position, raw in snapshots.items():
            self.n.put(actor_address(position), raw)
            self.n.put32(MANAGER + 0x38 + position * 24, actor_address(position))
        self.snapshots = dict(snapshots)

    def actor(self, position):
        if position not in self.snapshots:
            raise ValueError('No supplied actor')
        return bytes(self.n.vm.mem_read(actor_address(position), ACTOR_SIZE))

    def _run(self, start, ranges, stops):
        n = self.n
        for lo, hi in ranges:
            if bytes(n.vm.mem_read(BASE + lo, hi - lo)) != self.image[lo:hi]:
                raise ValueError('Original instruction bytes changed')
        n.visits, n.writes = [], []
        reads = []
        stack_span = (STACK, STACK + 0x8000)
        actor_spans = [(actor_address(p), actor_address(p) + ACTOR_SIZE)
                       for p in self.snapshots]
        readable = [stack_span, *actor_spans, (BASE, BASE + len(self.image)),
                    (RECORD, RECORD + 15), (GATE, GATE + 4),
                    (MANAGER + 0x20, MANAGER + 0x24),
                    (MANAGER + 0x38, MANAGER + 0x38 + 28 * 24),
                    (CATALOG, CATALOG + len(self.source) - 4),
                    (BATTLE + 0xa9df6b8, BATTLE + 0xa9df6bc)]
        writable = [stack_span, *actor_spans,
                    (BATTLE + 0xa9df6b8, BATTLE + 0xa9df6bc),
                    (BATTLE + 0xa9e9c6c, BATTLE + 0xa9e9c70),
                    (MANAGER + 0x309, MANAGER + 0x30a)]

        def read(vm, access, address, size, value, _):
            if not any(lo <= address and address + size <= hi for lo, hi in readable):
                raise AssertionError(f'Unqualified read {address:x}')
            reads.append((vm.reg_read(UC_X86_REG_EIP) - BASE, address, size))

        def write(vm, access, address, size, value, _):
            if not any(lo <= address and address + size <= hi for lo, hi in writable):
                raise AssertionError(f'Unqualified write {address:x}')

        hooks = [n.vm.hook_add(UC_HOOK_MEM_READ, read),
                 n.vm.hook_add(UC_HOOK_MEM_WRITE, write)]
        try:
            n.run(start, ranges, stops, budget=12000)
        finally:
            for hook in hooks:
                n.vm.hook_del(hook)
        return {'start_rva': start, 'stop_rva': n.stop, 'pcs': list(n.visits),
                'reads': reads, 'writes': list(n.writes),
                'input_authority': 'synthetic_diagnostic_only'}

    def produce(self, record, *, gate, phase_started):
        """Logical S2C83 action 3, exactly 15 bytes, no transport claim.

        Byte +2 is packed actor position; +11/+12 are skill ID/bank. Unsupported
        pairs are admitted here to test native unchecked pointer arithmetic;
        the resulting pointer is NEVER a qualified definition or assignment.
        """
        if (type(record) is not bytes or len(record) != 15 or record[:2] != b'\x83\x03'
                or type(gate) is not int or not 0 <= gate <= 255
                or type(phase_started) is not bool):
            raise ValueError('Explicit S2C83 action-3 record, byte gate and phase required')
        self.record = record
        n = self.n
        n.put(RECORD, record)
        n.put32(GATE, gate)
        n.put32(BATTLE + 0xa9df6b8, int(phase_started))
        n.put32(SP + 0x28, GATE)
        n.registers(esp=SP, ebp=RECORD, edi=RECORD, esi=BATTLE, eax=0)
        return self._run(0x114332,
                         [SPANS[k] for k in ('dispatch', 'action_prefix',
                          'action_cache_producer', 'target_scan', 'actor_lookup')],
                         {0x1143ba, 0x116b14, 0x116c03, 0x116df1, 0x117152})

    def consume(self, record, *, target_side, target_slot):
        """Independent consumer call, no fabricated return from resource lookup.

        Explicit target arguments are diagnostic live-ins; the previous producer
        actor pointer/cache remain in place. Stop immediately after EC4 store,
        or before original missing-cache assertion. Not complete action playback.
        """
        if (type(record) is not bytes or len(record) != 15 or record[:2] != b'\x83\x03'
                or not 0 <= record[2] < 28 or type(target_side) is not int
                or not 0 <= target_side < 2 or type(target_slot) is not int
                or not 0 <= target_slot < 14):
            raise ValueError('Explicit action-3 consumer record/target required')
        n = self.n
        n.put(RECORD, record)
        side, slot = divmod(record[2], 14)
        n.put(SP, struct.pack('<6I', RETURN, RECORD + 1, side, slot, target_side, target_slot))
        n.registers(esp=SP, ecx=MANAGER)
        return self._run(0x12c520,
                         [SPANS[k] for k in ('action_consumer_prefix', 'actor_lookup',
                          'skill_consumer', 'consumer_null_return')],
                         {0x12c7d8, 0x12c790})


def diagnostic_actor(*, poison, cached=()):
    """Explicit test memory, not original actor values or default repertoire."""
    data = bytearray(bytes((poison,)) * ACTOR_SIZE)
    data[0x239] = 1  # Isolate the non-clearing prefix branch.
    data[CACHE:CURRENT] = bytes(CAPACITY * 4)
    if len(cached) > CAPACITY:
        raise ValueError('Diagnostic cache exceeds physical capacity')
    for index, pointer in enumerate(cached):
        struct.pack_into('<I', data, CACHE + 4 * index, pointer)
    return bytes(data)


def diagnostic_record(bank, skill_id, position):
    """Labeled synthetic record; no assignment fact can be emitted from this."""
    record = bytearray.fromhex('83 03 0e 6b ee 01 00 00 00 34 12 01 00 ca fe')
    record[2], record[11], record[12] = position, skill_id, bank
    return bytes(record)


def diagnose_all_definitions(probe):
    """Exhaust 448 populated pairs, rotating all 28 positions; NOT monsters."""
    checks = []
    for index, ((bank, skill_id), definition) in enumerate(probe.definitions.items()):
        position = index % 28
        record = diagnostic_record(bank, skill_id, position)
        probe.install_actors({position: diagnostic_actor(poison=0xa5)})
        producer = probe.produce(record, gate=record[3], phase_started=True)
        expected = probe.pointer(bank, skill_id)
        if (producer['stop_rva'] != 0x116df1
                or struct.unpack_from('<I', probe.actor(position), CACHE)[0] != expected):
            raise AssertionError('Native action cache producer differs')
        consumer = probe.consume(record, target_side=0, target_slot=0)
        actor = probe.actor(position)
        if (consumer['stop_rva'] != 0x12c7d8 or actor[SELECTED] != 0
                or struct.unpack_from('<I', actor, CURRENT)[0] != expected
                or bytes(probe.n.vm.mem_read(expected, 110)) != definition.raw):
            raise AssertionError('Native action consumer/source pair differs')
        checks.append({'bank': bank, 'id': skill_id, 'diagnostic_position': position,
                       'definition_source_offset': definition.source_offset,
                       'definition_sha256': sha(definition.raw),
                       'synthetic_record_hex': record.hex(),
                       'producer_store_rva': 0x116dc1, 'consumer_store_rva': 0x12c7d2,
                       'cache_pointer': expected, 'monster_identity': None})
    return checks


def evidence(client=ROOT.parent / 'God2'):
    catalog = pinned_catalog(client)
    probe = NativeSkillActions(client)
    diagnostics = diagnose_all_definitions(probe)
    rows = []
    for source in catalog['records']:
        rows.append({
            'identity': {key: source[key] for key in
                         ('source_record_index', 'area_generation', 'area', 'scene', 'ordinal')},
            'identity_bank': 'EnyName', 'lookup_visible': source['lookup_visible'],
            'source': {'file': SOURCE, 'sha256': SOURCE_SHA, 'decoded_sha256': PLAIN_SHA,
                       'decoded_offset': source['source_offset'], 'line': source['source_line'],
                       'record_sha256': source['record_sha256'],
                       'raw_record_hex': source['raw_record_hex']},
            'monster_classification': None, 'variant_identity': None,
            'fields': dict.fromkeys(FIELDS), 'field_sources': dict.fromkeys(FIELDS),
        })
    visible = sum(row['lookup_visible'] for row in rows)
    return {
        'schema': 'current-monster-skill-assignments-v1', 'runtime_eligible': False,
        'requested_scope': ['normal', 'boss', 'elite', 'event', 'quest', 'summoned'],
        'image': {'file': str(IMAGE), 'sha256': IMAGE_SHA256, 'base': BASE,
                  'rva_equals_file_offset': True},
        'native_spans': {name: {'source_offset': lo, 'end_offset_exclusive': hi,
                               'source_sha256': IMAGE_SHA256, 'sha256': sha(probe.image[lo:hi])}
                         for name, (lo, hi) in SPANS.items()},
        'definition_source': {'file': SKILL_SOURCE, 'sha256': SKILL_SHA,
                              'count': len(probe.definitions),
                              'authority': 'global_definitions_not_monster_assignments'},
        'coverage': {'source_records': len(rows), 'lookup_visible_records': visible,
                     'superseded_records': len(rows) - visible,
                     'source_groups': len(catalog['loaded_groups']),
                     'lookup_visible_groups': len(catalog['groups']),
                     'unique_species_denominator': None, 'all_boss_denominator': None,
                     'all_monster_systems_enumerated': False,
                     'field_coverage': {f: {'verified_visible_records': 0,
                                            'unresolved_visible_records': visible,
                                            'unresolved_source_records': len(rows)} for f in FIELDS}},
        'action_binding': {
            'opcode': 0x83, 'logical_size': 15, 'action_discriminator': 3,
            'packed_actor_offset': 2, 'skill_id_offset': 11, 'bank_offset': 12,
            'actor_pointer': 'manager+0x38+24*(14*side+slot), type 0',
            'cache_offset': CACHE, 'cache_capacity': CAPACITY,
            'cache_semantics': 'received-action association, not full repertoire or permission',
            'native_pointer': 'battle+0xA924D12+110*id+0x6E04*bank',
            'definition_file_offset': '8+0x6E04*bank+110*(id-1)',
            'producer_stop_before_call': 0x116df1, 'unexecuted_resource_lookup': 0x5f490,
            'consumer_separate_entry': 0x12c520, 'consumer_stop_after_store': 0x12c7d8,
            'continuous_producer_to_consumer': False,
            'repertoire': None, 'ai_trigger_conditions': None,
        },
        'diagnostics': {'authority': 'synthetic_inputs_only',
                        'scope': 'all 448 definitions; rotating all 28 actor positions, not Cartesian product',
                        'cases': diagnostics},
        'remaining_frontier': {
            'needed_producer': 'Original sender/assignment source for 83 action 3, with participant lifecycle identity',
            'identity_binding': 'Join same-session 1C slot byte +1 to 83 actor byte +2; '
                                'qualify normal area +9, scene WORD +11, ordinal WORD +7, '
                                'variant WORD +5 through 115E07/115E25/115E70 and actor lifetime',
            'identity_join_verified_here': False,
            'required_for_repertoire': 'An original assignment table or authoritative enumeration per identity and variant',
            'required_for_triggers': 'Original AI/decision producer, including predicates, rates, ordering and state',
            'absence_claim': False,
        },
        'records': rows,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--client', type=Path, default=ROOT.parent / 'God2')
    parser.add_argument('--summary', action='store_true')
    args = parser.parse_args()
    report = evidence(args.client)
    if args.summary:
        report.pop('records')
        report['diagnostics']['case_count'] = len(report['diagnostics'].pop('cases'))
    print(json.dumps(report, ensure_ascii=True, sort_keys=True))


if __name__ == '__main__':
    main()
