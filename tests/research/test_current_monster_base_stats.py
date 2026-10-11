"""All current EnyName occurrences; synthetic operands never become stats."""
from pathlib import Path
import json
import struct
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.strike_lab.current_monster_base_stats import (
    MonsterLevelProbe, FIELDS, IMAGE_SHA256, GAME_SHA256, GAME_DECODED_SHA256,
    identity_inventory, sha)


class CurrentMonsterBaseStatsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        original_open = Path.open

        def current_only(path, *args, **kwargs):
            parts = [p.lower() for p in path.resolve().parts]
            if any('classic' in p or 'xjz' in p or p == 'legacy-evidence' for p in parts):
                raise AssertionError('Retired source access forbidden')
            return original_open(path, *args, **kwargs)

        guard = patch.object(Path, 'open', current_only)
        guard.start()
        cls.addClassCleanup(guard.stop)
        cls.probe = MonsterLevelProbe()
        cls.report = cls.probe.evidence()

    def test_all_source_occurrences_and_native_battle_joins(self):
        p, report = self.probe, self.report
        counts = report['coverage']
        self.assertEqual(counts['allocated_source_records'], 7815)
        self.assertEqual(counts['lookup_visible_records'], 7791)
        self.assertEqual(counts['shadowed_source_records'], 24)
        self.assertEqual(counts['loaded_groups'], 97)
        self.assertEqual(counts['lookup_visible_groups'], 96)
        self.assertEqual(counts['native_battle_identity_joins_checked'], 7791)
        shared = p.catalog['records']
        self.assertEqual(len(report['records']), len(shared))
        identities = set()
        for row, original in zip(report['records'], shared):
            key = row['identity']
            identity = tuple(key[k] for k in ('bank', 'area_generation', 'area', 'scene', 'ordinal'))
            self.assertNotIn(identity, identities)
            identities.add(identity)
            self.assertEqual(key['source_record_index'], original['source_record_index'])
            self.assertEqual(row['lookup_visible'], original['lookup_visible'])
            self.assertEqual(row['source']['decoded_offset'], original['source_offset'])
            self.assertEqual(sha(bytes.fromhex(original['raw_record_hex'])),
                             row['source']['record_sha256'])
            self.assertEqual(row['source']['record_size'], len(bytes.fromhex(original['raw_record_hex'])))
            self.assertEqual(row['source']['sha256'], GAME_SHA256)
            self.assertEqual(row['source']['decoded_sha256'], GAME_DECODED_SHA256)
        shadowed = [r for r in shared if not r['lookup_visible']]
        self.assertEqual({r['area'] for r in shadowed}, {7})

    def test_level_counterfactuals_are_independent_of_real_identity(self):
        p = self.probe
        row = next(r for r in p.inventory if r['lookup_visible'])
        key = row['identity']
        baseline = p.join(key['area'], key['scene'], key['ordinal'], diagnostic_level=0)
        baseline_metadata = bytes.fromhex(baseline['metadata_hex'])
        for level in (0, 1, 30, 31, 39, 40, 99, 100, 255):
            for poison in (0, 0xa5, 0xff):
                trace = p.join(key['area'], key['scene'], key['ordinal'],
                               diagnostic_level=level, poison=poison, slot=27)
                self.assertEqual(trace['record_pointer'], baseline['record_pointer'])
                metadata = bytes.fromhex(trace['metadata_hex'])
                expected = bytearray(baseline_metadata)
                expected[7] = level
                self.assertEqual(metadata, expected)
                self.assertIn((0x115d2f, 2, 1), trace['packet_reads'])
                self.assertIn(0x115e07, trace['visits'])
                display = p.display_prefix(metadata)
                self.assertFalse(display['formatter_executed'])
                if level <= 30:
                    self.assertEqual(display['format_va'], 0x594310)
                    self.assertEqual(display['argument'], level)
                elif level < 100:
                    self.assertEqual(display['format_va'], 0x594318)
                    expected_pointer = struct.unpack_from('<I', p.image,
                        0x19d278 + 4 * ((level - 30) // 10))[0]
                    self.assertEqual(display['argument'], expected_pointer)
                else:
                    self.assertEqual(display['format_va'], 0x594320)
                    self.assertIsNone(display['argument'])

    def test_every_group_boundary_and_missing_identity(self):
        p = self.probe
        for (area, scene), rows in p.native.enemy_groups.items():
            for ordinal in (0, len(rows) + 1):
                trace = p.join(area, scene, ordinal, diagnostic_level=17)
                self.assertEqual(trace['record_pointer'], 0)
                self.assertEqual(bytes.fromhex(trace['metadata_hex'])[7], 17)
        trace = p.join(2, 15, 1, diagnostic_level=17)
        self.assertEqual(trace['record_pointer'], 0)

    def test_null_authority_survives_json_and_does_not_claim_complete_monsters(self):
        report = json.loads(json.dumps(self.report))
        self.assertIsNone(report['coverage']['true_wild_monster_denominator'])
        self.assertFalse(report['coverage']['all_monster_systems_enumerated'])
        self.assertEqual(report['coverage']['verified_base_stat_records'], 0)
        self.assertEqual(set(report['coverage']['monster_categories']),
                         {'normal', 'boss', 'elite', 'quest', 'event', 'summoned'})
        self.assertTrue(all(v is None for v in report['coverage']['monster_categories'].values()))
        for field in FIELDS:
            authority = report['field_authority'][field]
            self.assertEqual(authority['verified_record_count'], 0)
            self.assertEqual(authority['unresolved_visible_record_count'], 7791)
            for name in ('value', 'source_sha256', 'source_offset'):
                self.assertIsNone(authority[name])
        for row in report['records']:
            self.assertEqual(row['fields'], dict.fromkeys(FIELDS))
            self.assertEqual(row['field_authority'], dict.fromkeys(FIELDS))
            self.assertIsNone(row['monster_category'])
            self.assertFalse(row['runtime_eligible'])

    def test_image_offsets_dispatch_length_and_format_labels(self):
        image = self.probe.image
        self.assertEqual(sha(image), IMAGE_SHA256)
        length_rva = struct.unpack_from('<I', image, 0x1324 + 0x1c * 4)[0] - 0x400000
        self.assertEqual(length_rva, 0x12a6)
        self.assertEqual(image[length_rva:length_rva + 6], bytes.fromhex('b82d000000c3'))
        index = image[0x11465c]
        self.assertEqual(struct.unpack_from('<I', image, 0x114634 + 4 * index)[0], 0x514358)
        self.assertEqual(image[0x194310:0x194328], b'Lv:%d\0\0\0Lv:%s\0\0\0Lv:???\0\0')
        for span in self.report['native_spans'].values():
            lo, hi = span['source_offset'], span['end_offset_exclusive']
            self.assertEqual(span['sha256'], sha(image[lo:hi]))
            self.assertEqual(span['source_sha256'], IMAGE_SHA256)

    def test_descriptor_fixture_never_maps_enemy_payload_and_retains_other_frontiers(self):
        p = self.probe
        self.assertIn('record_arena_unmapped', self.report['descriptor_authority'])
        lo, hi = p.record_base, p.record_base + 26 * len(p.inventory)
        self.assertFalse(any(start < hi and end >= lo for start, end, _ in p.native.vm.mem_regions()))
        self.assertTrue(all(r['native_record_hex'] is None for r in p.inventory))
        frontier = self.report['outside_inventory_frontiers'][0]
        self.assertEqual(frontier['bank'], 'SpecialEnyInfo')
        raw = b'SpecialEnyInfo,1\r\n1,IGS_SPECIAL,0,0,149,1\r\n'
        self.assertEqual(frontier['end_offset_exclusive'] - frontier['decoded_offset'], len(raw))
        self.assertEqual(frontier['section_sha256'], sha(raw))
        self.assertIsNone(frontier['boss_record_count'])

    def test_changed_source_and_invalid_inputs_fail_closed(self):
        p = self.probe
        with self.assertRaisesRegex(ValueError, 'gamedata changed'):
            identity_inventory(SimpleNamespace(game_data=b'changed'))
        for args in ((17, 0, 1), (1, 65536, 1), (1, 0, -1), (True, 0, 1)):
            with self.assertRaises(ValueError):
                p.join(*args, diagnostic_level=1)
        for level in (-1, 256, None):
            with self.assertRaises(ValueError):
                p.join(1, 0, 1, diagnostic_level=level)
        with self.assertRaises(ValueError):
            p.display_prefix(bytes(55))


if __name__ == '__main__':
    unittest.main()
