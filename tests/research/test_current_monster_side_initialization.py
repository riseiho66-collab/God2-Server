"""One original identity, both sides, exact data provenance, no ROM preload."""
from pathlib import Path
import json
import struct
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.strike_lab.current_monster_side_initialization import (
    MonsterSideInitializationProbe, IMAGE, IMAGE_SHA256, GAME_FILE, FIGHT_FILE,
    ACTOR, ACTOR_SIZE, BASE, MANAGER, CWD, SPANS, sha)


class CurrentMonsterSideInitializationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        original_open = Path.open
        allowed = {IMAGE.resolve(), (ROOT.parent / 'God2' / GAME_FILE).resolve(),
                   (ROOT.parent / 'God2' / FIGHT_FILE).resolve()}
        def selected_sources_only(path, *args, **kwargs):
            if path.resolve() not in allowed:
                raise AssertionError('Unexpected source/preload: ' + str(path))
            return original_open(path, *args, **kwargs)
        guard = patch.object(Path, 'open', selected_sources_only)
        guard.start()
        cls.addClassCleanup(guard.stop)
        cls.probe = MonsterSideInitializationProbe()

    def test_original_row_writers_and_exact_source_offsets(self):
        p = self.probe
        self.assertEqual(sha(p.image), IMAGE_SHA256)
        self.assertEqual(p.row['source_offset'], 2500917)
        self.assertEqual(p.row['source_line'], 21699)
        self.assertEqual(p.enemy_record[:2], b'\x16\x0f')
        self.assertEqual(p.enemy_record[2:8], bytes.fromhex('a454b84fc06e'))
        self.assertEqual(p.enemy_record[8:], bytes(18))
        self.assertEqual(p.fight_source['decoded_offset'], 2105)
        self.assertEqual(p.fight_source['line'], 55)
        writes = p.source_traces[1]['writes']
        routing = [(e['rva'], e['offset'], e['hex']) for e in writes
                   if e['region'] == 'enemy_record' and e['offset'] < 2]
        self.assertEqual(routing, [(0x5a2e5, 0, '10'), (0x5a2fd, 0, '10'),
                                   (0x5a30a, 1, '0f'), (0x5a323, 0, '16')])
        numeric = [(e['rva'], e['region'], e['offset'], e['hex'])
                   for e in p.source_traces[3]['writes']
                   if e['region'].startswith('fight_side') and e['offset'] < 12]
        self.assertEqual(numeric, [(0x5435b, 'fight_side1', 2, '7f17'),
            (0x54367, 'fight_side0', 2, '7f17'), (0x54378, 'fight_side1', 4, '0100'),
            (0x54385, 'fight_side0', 4, '0100')])
        for side, raw in enumerate(p.fight_records):
            record = bytes.fromhex(raw)
            path = (b'data2\\fight\\eny1\\eny1015.rom' if side == 0
                    else b'data2\\fight\\eny\\eny5015.rom')
            self.assertEqual(record[12:12 + len(path) + 1], path + b'\0')
            self.assertEqual(record[:2], b'\xa5\xa5')  # No invented runtime handle.
            self.assertEqual(record[6:12], b'\xa5' * 6)
        # The original caller binds this same reader, not a name-only table join.
        self.assertEqual(p.image[0x110cdd:0x110ce3], bytes.fromhex('8d8eb0e90200'))
        self.assertEqual(0x110ce9 + struct.unpack_from('<i', p.image, 0x110ce5)[0], 0x54210)

    def test_both_sides_same_actor_all_paired_slots_and_untouched_scalars(self):
        p = self.probe
        original = bytes(p.vm.mem_read(ACTOR, 4096))
        for slot in range(14):
            pair = [p.run(side, local_slot=slot) for side in (1, 0)]
            self.assertEqual(pair[0]['metadata_hex'], pair[1]['metadata_hex'])
            self.assertEqual(pair[0]['actor_before_sha256'], pair[1]['actor_before_sha256'])
            for trace in pair:
                side = trace['side']
                self.assertEqual(trace['record_pointer'], p.record)
                self.assertEqual(trace['actor_address'], ACTOR)
                self.assertEqual(trace['resource_pointer'], p.resource_rows[side])
                self.assertEqual(trace['stop_rva'], 0x1206e0)
                self.assertEqual(trace['actor_before_sha256'], trace['actor_after_sha256'])
                self.assertEqual(trace['scalars_hex'], 'a5' * 16)
                self.assertFalse(any(e['region'] == 'actor' for e in trace['writes']))
                for rva in (0x115e7f, 0x115f2f, 0x115f81, 0x115fc2, 0x120650, 0x1206da):
                    self.assertIn(rva, trace['visits'])
                for rva in (0x1206e0, 0x29820, 0x116000, 0x1216c0, 0x121a30, 0x121a4a):
                    self.assertNotIn(rva, trace['visits'])
                expected_path = (b'data2\\fight\\eny1\\eny1015.rom' if side == 0
                                 else b'data2\\fight\\eny\\eny5015.rom')
                self.assertEqual(bytes.fromhex(trace['requested_path_hex']), CWD + b'\\' + expected_path)
            packet1, packet0 = [bytes.fromhex(t['packet_hex']) for t in pair]
            self.assertEqual([i for i in range(45) if packet1[i] != packet0[i]], [1])
        self.assertEqual(bytes(p.vm.mem_read(ACTOR, 4096)), original)
        self.assertEqual(p.native.u32(MANAGER + 0x38 + (14 + 13) * 24), 0)

    def test_exact_1c_consumed_byte_map_and_table_reads(self):
        p = self.probe
        expected = [(0x115ca8, 1, 1), (0x115d10, 3, 2), (0x115d19, 5, 2),
            (0x115d2f, 2, 1), (0x115d6b, 41, 4), (0x115d88, 9, 4),
            (0x115d99, 13, 4), (0x115da0, 17, 4), (0x115da7, 21, 4),
            (0x115db1, 25, 4), (0x115db8, 29, 4), (0x115dbf, 33, 4),
            (0x115dc6, 37, 4), (0x115ddb, 7, 2), (0x115df1, 5, 2),
            (0x115dfa, 11, 2), (0x115e02, 9, 1), (0x115e0e, 5, 2)]
        for side in (0, 1):
            t = p.run(side)
            reads = [e for e in t['reads'] if e['region'] == 'packet']
            self.assertEqual([(e['rva'], e['offset'], e['size']) for e in reads], expected)
            self.assertEqual({i for e in reads for i in range(e['offset'], e['offset'] + e['size'])},
                             set(range(1, 45)))
            table = [e for e in t['reads'] if e['region'] == 'enemy_record']
            self.assertEqual([(e['rva'], e['offset'], e['hex']) for e in table],
                             [(0x115e7f, 0, '16'), (0x115f2f, 1, '0f')])
            resources = [e for e in t['reads'] if e['region'].startswith('fight_side')]
            self.assertEqual({e['region'] for e in resources}, {'fight_side' + str(side)})
            self.assertTrue(all(12 <= e['offset'] < 41 for e in resources))
            self.assertEqual([(e['rva'], e['offset']) for e in resources if not e['adapter']],
                             [(0x12f57d, 12)])
            self.assertFalse(any(e['region'] == 'packet' for e in t['writes']))

    def test_poison_and_packet_level_are_not_original_stats(self):
        for poison in (0x3c, 0xff):
            p = MonsterSideInitializationProbe(poison=poison)
            for side in (0, 1):
                t = p.run(side, diagnostic_level=255)
                packet = bytes.fromhex(t['packet_hex'])
                expected = bytearray((poison,)) * 56
                expected[:2] = b'\x34\x12'
                expected[4:8] = bytes((poison, (poison & 3) | 4, 0, 255))
                expected[8:14] = bytes.fromhex('010000000100')
                expected[14:46] = packet[9:41]
                self.assertEqual(bytes.fromhex(t['metadata_hex']), expected)
                self.assertEqual(t['scalars_hex'], bytes((poison,)).hex() * 16)
                other = p.run(side, diagnostic_level=0)
                self.assertEqual(t['record_pointer'], other['record_pointer'])
                self.assertEqual([i for i, (a, b) in enumerate(zip(
                    bytes.fromhex(t['metadata_hex']), bytes.fromhex(other['metadata_hex']))) if a != b], [7])

    def test_missing_source_guard_both_sides_has_no_path_or_actor_stores(self):
        p = MonsterSideInitializationProbe(fight_rows_loaded=False)
        for side in (0, 1):
            pointer = p.resource_rows[side]
            self.assertFalse(any(lo <= pointer <= hi for lo, hi, _ in p.vm.mem_regions()))
            t = p.run(side)
            self.assertEqual(t['stop_rva'], 0x12f57d)
            self.assertEqual(t['resource_pointer'], pointer)
            self.assertEqual(p.getreg('EAX'), pointer + 12)
            self.assertNotIn('requested_path_hex', t)
            self.assertNotIn(0x120650, t['visits'])
            self.assertFalse(any(e['region'].startswith('fight_side') for e in t['reads']))
            self.assertFalse(any(e['region'] == 'actor' for e in t['writes']))
            self.assertEqual(t['scalars_hex'], 'a5' * 16)

    def test_initial_dword_is_flags_and_does_not_initialize_scalars(self):
        for side in (0, 1):
            for flags in (0, 1, 0xfefefefe, 0xffffffff):
                t = self.probe.run(side, diagnostic_flags=flags)
                metadata = bytes.fromhex(t['metadata_hex'])
                self.assertEqual(struct.unpack_from('<I', metadata, 8)[0], 1 if flags & 1 else flags)
                self.assertEqual(t['scalars_hex'], 'a5' * 16)
                self.assertFalse(t['scalar_initialization_executed'])

    def test_first_scalar_writes_are_existing_native_fill_not_packet_numbers(self):
        p = MonsterSideInitializationProbe()
        trace = p.reset_actor()
        self.assertFalse(trace['novel_frontier'])
        self.assertEqual([(e['rva'], e['offset'], e['size'], e['hex']) for e in trace['scalar_writes']],
            [(0x11fdfe, off, 4, 'cdcdcdcd') for off in (0xde8, 0xdec, 0xdf0, 0xdf4)])
        self.assertEqual(bytes(p.vm.mem_read(ACTOR + ACTOR_SIZE, 4096 - ACTOR_SIZE)),
                         b'\xa5' * (4096 - ACTOR_SIZE))
        self.assertEqual(bytes.fromhex(trace['metadata_hex']), b'\xff\xff' + bytes(54))
        sides = [p.run(side) for side in (1, 0)]
        self.assertEqual(sides[0]['metadata_hex'], sides[1]['metadata_hex'])
        for t in sides:
            self.assertEqual(t['scalars_hex'], 'cd' * 16)
            self.assertFalse(any(e['region'] == 'actor' for e in t['writes']))

    def test_instruction_integrity_bounds_and_null_authority(self):
        p = MonsterSideInitializationProbe()
        report = json.loads(json.dumps(p.evidence()))
        for name, (lo, hi) in SPANS.items():
            self.assertEqual(bytes(p.vm.mem_read(BASE + lo, hi - lo)), p.image[lo:hi])
            self.assertEqual(report['native_spans'][name]['sha256'], sha(p.image[lo:hi]))
        self.assertTrue(all(value is None for value in report['fields'].values()))
        self.assertFalse(report['runtime_eligible'])
        self.assertFalse(report['constructor_completed'])
        self.assertFalse(report['recruitment_proven'])
        self.assertEqual(p.image[0x1206e0:0x1206ea], bytes.fromhex('8b4d085052e83691f0ff'))
        for side in (True, -1, 2):
            with self.assertRaises(ValueError):
                p.run(side)
        p._reset()
        p.setreg('ECX', 0)
        with self.assertRaisesRegex(AssertionError, 'budget exhausted'):
            p._run(0x115c90, {0x1206e0}, ('participant_prefix',), budget=1)


if __name__ == '__main__':
    unittest.main()
