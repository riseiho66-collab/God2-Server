"""Pinned native action evidence and full occurrence accounting, no live client."""
import json
import struct
import unittest

from tools.strike_lab import current_monster_skill_assignments as m


class CurrentMonsterSkillAssignmentsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = m.evidence()
        cls.probe = m.NativeSkillActions()

    def stage(self, bank=0, skill_id=1, position=14, cached=(), poison=0xa5):
        p = self.probe
        before = m.diagnostic_actor(poison=poison, cached=cached)
        p.install_actors({position: before})
        record = m.diagnostic_record(bank, skill_id, position)
        return before, record

    def test_full_occurrence_coverage_nulls_and_exact_source(self):
        report = json.loads(json.dumps(self.report))
        catalog = m.pinned_catalog()
        coverage = report['coverage']
        self.assertEqual([coverage[k] for k in ('source_records', 'lookup_visible_records',
                         'superseded_records', 'source_groups', 'lookup_visible_groups')],
                         [7815, 7791, 24, 97, 96])
        for row, source in zip(report['records'], catalog['records'], strict=True):
            self.assertEqual(row['identity'], {k: source[k] for k in row['identity']})
            self.assertEqual(row['lookup_visible'], source['lookup_visible'])
            self.assertEqual(row['source']['decoded_offset'], source['source_offset'])
            self.assertEqual(row['source']['record_sha256'], m.sha(bytes.fromhex(source['raw_record_hex'])))
            self.assertEqual(row['source']['sha256'], m.SOURCE_SHA)
            self.assertEqual(row['source']['decoded_sha256'], m.PLAIN_SHA)
            self.assertEqual(row['fields'], dict.fromkeys(m.FIELDS))
            self.assertEqual(row['field_sources'], dict.fromkeys(m.FIELDS))
            self.assertIsNone(row['monster_classification'])
        self.assertFalse(coverage['all_monster_systems_enumerated'])
        self.assertIsNone(coverage['all_boss_denominator'])
        self.assertIsNone(coverage['unique_species_denominator'])
        self.assertFalse(report['runtime_eligible'])

    def test_every_definition_native_producer_and_consumer(self):
        cases = self.report['diagnostics']['cases']
        self.assertEqual(len(cases), 448)
        self.assertEqual({(c['bank'], c['id']) for c in cases}, set(self.probe.definitions))
        self.assertEqual({c['diagnostic_position'] for c in cases}, set(range(28)))
        for case in cases:
            definition = self.probe.definitions[case['bank'], case['id']]
            self.assertEqual(case['definition_source_offset'], definition.source_offset)
            self.assertEqual(case['definition_sha256'], m.sha(definition.raw))
            self.assertIsNone(case['monster_identity'])
        self.assertFalse(self.report['action_binding']['continuous_producer_to_consumer'])

    def test_same_id_different_bank_append_duplicate_and_consumer(self):
        p = self.probe
        before, record = self.stage(bank=1, skill_id=1, cached=(p.pointer(0, 1),))
        producer = p.produce(record, gate=0x6b, phase_started=True)
        expected = bytearray(before)
        struct.pack_into('<I', expected, m.CACHE + 4, p.pointer(1, 1))
        self.assertEqual(p.actor(14), expected)
        self.assertIn((0x116dc1, m.actor_address(14) + m.CACHE + 4, 4, p.pointer(1, 1)), producer['writes'])
        again = p.produce(record, gate=0x6b, phase_started=True)
        self.assertEqual(p.actor(14), expected)
        self.assertEqual([w for w in producer['writes'] if w[0] == 0x116dc1],
                         [w for w in again['writes'] if w[0] == 0x116dc1])
        consumer = p.consume(record, target_side=0, target_slot=0)
        expected[m.SELECTED] = 1
        struct.pack_into('<I', expected, m.CURRENT, p.pointer(1, 1))
        self.assertEqual(p.actor(14), expected)
        self.assertEqual(consumer['stop_rva'], 0x12c7d8)
        self.assertIn(0x11e75a, producer['pcs'])
        self.assertIn(0x12c75e, consumer['pcs'])
        self.assertNotIn(0x5f490, producer['pcs'])
        packet_reads = {(address - m.RECORD, size) for _, address, size in producer['reads']
                        if m.RECORD <= address < m.RECORD + 15}
        self.assertTrue({(2, 1), (11, 1), (12, 1)} <= packet_reads)

    def test_position_changes_actor_without_mutating_other_actor(self):
        p = self.probe
        for position in range(28):
            other = (position + 1) % 28
            snapshots = {position: m.diagnostic_actor(poison=0xa5),
                         other: m.diagnostic_actor(poison=0x5a)}
            p.install_actors(snapshots)
            record = m.diagnostic_record(3, 111, position)
            trace = p.produce(record, gate=0x6b, phase_started=True)
            self.assertEqual(trace['stop_rva'], 0x116df1)
            self.assertEqual(p.actor(other), snapshots[other])
            self.assertEqual(struct.unpack_from('<I', p.actor(position), m.CACHE)[0], p.pointer(3, 111))

    def test_first_hole_last_slot_and_native_full_cache_alias(self):
        p = self.probe
        pointers = tuple(p.pointer(0, i) for i in range(1, 52))
        for cached, slot in ((pointers[:50], 50), (pointers, 51),
                             ((pointers[0], 0, pointers[2]), 1)):
            before, record = self.stage(skill_id=60, cached=cached)
            trace = p.produce(record, gate=0x6b, phase_started=True)
            expected = bytearray(before)
            struct.pack_into('<I', expected, m.CACHE + slot * 4, p.pointer(0, 60))
            self.assertEqual(p.actor(14), expected)
            self.assertEqual(trace['stop_rva'], 0x116df1)
            self.assertNotIn(0x116d76, trace['pcs'])
            consumer = p.consume(record, target_side=0, target_slot=0)
            self.assertEqual(consumer['stop_rva'], 0x12c790 if slot == 51 else 0x12c7d8)
        self.assertEqual(m.CACHE + 51 * 4, m.CURRENT)

    def test_consumer_missing_pair_does_not_supply_ownership(self):
        p = self.probe
        before, record = self.stage(bank=2, cached=(p.pointer(0, 1), p.pointer(1, 1)))
        trace = p.consume(record, target_side=1, target_slot=13)
        self.assertEqual(trace['stop_rva'], 0x12c790)
        self.assertEqual(p.actor(14), before)
        self.assertNotIn(0x2c70, trace['pcs'])

    def test_unpopulated_pairs_native_producer_has_no_membership_check(self):
        p = self.probe
        for bank, skill_id in ((0, 0), (0, 122), (4, 1), (255, 255)):
            before, record = self.stage(bank=bank, skill_id=skill_id)
            trace = p.produce(record, gate=0x6b, phase_started=True)
            self.assertEqual(trace['stop_rva'], 0x116df1)
            pointer = m.BATTLE + 0xa924d12 + 110 * skill_id + 0x6e04 * bank
            expected = bytearray(before)
            struct.pack_into('<I', expected, m.CACHE, pointer)
            self.assertEqual(p.actor(14), expected)
            with self.assertRaises(ValueError):
                p.pointer(bank, skill_id)

    def test_gate_phase_invalid_and_missing_actor_boundaries(self):
        p = self.probe
        for gate, phase, stop in ((0x6c, True, 0x1143ba), (0x6b, False, 0x116b14)):
            before, record = self.stage()
            trace = p.produce(record, gate=gate, phase_started=phase)
            self.assertEqual(trace['stop_rva'], stop)
            self.assertEqual(p.actor(14), before)
        for position in (28, 255):
            p.install_actors({})
            trace = p.produce(m.diagnostic_record(0, 1, position), gate=0x6b, phase_started=True)
            self.assertEqual(trace['stop_rva'], 0x116c03)
        p.install_actors({})
        record = m.diagnostic_record(0, 1, 14)
        self.assertEqual(p.produce(record, gate=0x6b, phase_started=True)['stop_rva'], 0x117152)
        self.assertEqual(p.consume(record, target_side=0, target_slot=0)['stop_rva'], m.RETURN)

    def test_all_span_hashes_and_contract_rejections(self):
        for name, (lo, hi) in m.SPANS.items():
            span = self.report['native_spans'][name]
            self.assertEqual(span['source_offset'], lo)
            self.assertEqual(span['end_offset_exclusive'], hi)
            self.assertEqual(span['sha256'], m.sha(self.probe.image[lo:hi]))
            self.assertEqual(span['source_sha256'], m.IMAGE_SHA256)
        for raw in (b'', bytes(15), m.diagnostic_record(0, 1, 14)[:-1]):
            with self.assertRaises(ValueError):
                self.probe.produce(raw, gate=0x6b, phase_started=True)
        with self.assertRaises(ValueError):
            self.probe.install_actors({28: m.diagnostic_actor(poison=0xa5)})
        with self.assertRaises(ValueError):
            self.probe.install_actors({14: m.diagnostic_actor(poison=0xa5, cached=(0x1234,))})


if __name__ == '__main__':
    unittest.main()
