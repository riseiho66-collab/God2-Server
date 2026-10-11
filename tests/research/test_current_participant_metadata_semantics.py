"""Complete bounded metadata semantics suite; no ROM/UI/source-tree preload."""
from pathlib import Path
import json
import struct
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.strike_lab.current_participant_metadata_semantics import (
    ParticipantMetadataProbe, static_xrefs, IMAGE, IMAGE_SHA256, GAME_FILE,
    ACTOR, BASE, METADATA, PACKET, DISPLAY, GETTER_OUTPUT, SPANS, sha)


def block(raw, poison=0x77):
    if len(raw) > 15 or b'\0' in raw:
        raise ValueError('Test string bound')
    return (raw + b'\0').ljust(16, bytes((poison,)))


def centered(raw):
    return b' ' * max(0, (14 - len(raw)) // 2) + raw + b'\0'


class CurrentParticipantMetadataSemanticsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        original_open = Path.open
        allowed = {IMAGE.resolve(), (ROOT.parent / 'God2' / GAME_FILE).resolve()}
        def bounded_open(path, *args, **kwargs):
            if path.resolve() not in allowed:
                raise AssertionError('Unexpected source/ROM/preload access: ' + str(path))
            return original_open(path, *args, **kwargs)
        guard = patch.object(Path, 'open', bounded_open)
        guard.start()
        cls.addClassCleanup(guard.stop)
        cls.p = ParticipantMetadataProbe()

    def assert_no_scalars(self, trace):
        self.assertFalse(any(e['region'] == 'actor' and e['offset'] < 0xdf8
                             and e['offset'] + e['size'] > 0xde8
                             for e in trace['reads'] + trace['writes']))

    def test_static_xrefs_are_bounded_candidates_not_automatic_field_names(self):
        x = self.p.xrefs
        self.assertEqual((x['scan_start_rva'], x['scan_end_rva_exclusive']), (0x110000, 0x12f550))
        self.assertTrue(x['candidate_only'])
        candidates = {r['rva']: r for r in x['direct_displacement_candidates']}
        self.assertEqual(len(candidates), 77)
        for rva in (0x116577, 0x121a3f, 0x12d142):
            self.assertIn(rva, candidates)
        self.assertEqual(x['false_positive_example']['rva'], 0x115c23)
        aliases = {r['rva']: r for r in x['qualified_metadata_alias_windows']}
        self.assertIn('0xe', aliases[0x12d19a]['instruction'])
        self.assertIn('0x1e', aliases[0x12d1ad]['instruction'])
        for r in [*candidates.values(), *aliases.values()]:
            raw = bytes.fromhex(r['hex'])
            self.assertEqual(self.p.image[r['rva']:r['rva'] + len(raw)], raw)
        with self.assertRaisesRegex(ValueError, 'image changed'):
            static_xrefs(b'not the pinned image')

    def test_packet2000_real_merge_copy_and_both_sides_all_slots(self):
        p = self.p
        first, second = block(b'Participant'), block(b'Caption')
        for slot in range(14):
            pair = [p.stage(first, second, side=side, local_slot=slot) for side in (1, 0)]
            self.assertEqual(pair[0]['actor_metadata_hex'], pair[1]['actor_metadata_hex'])
            for r in pair:
                t = r['merge']
                self.assertEqual(t['stop_rva'], 0x116166)
                self.assertIsNone(r['independent_constructor_copy'])
                writes = [e for e in t['writes'] if e['region'] == 'actor_metadata']
                self.assertEqual([(e['rva'], e['offset'], e['size']) for e in writes],
                                 [(0x11615c, i, 4) for i in range(0, 56, 4)])
                self.assertEqual(bytes.fromhex(r['actor_metadata_hex'])[14:46], first + second)
                self.assertEqual(bytes(p.vm.mem_read(ACTOR + 0xde8, 16)), b'\xa5' * 16)
                self.assert_no_scalars(t)
            self.assertEqual(bytes(p.vm.mem_read(PACKET, 45)), bytes.fromhex(pair[-1]['packet_hex']))

    def test_two_real_text_setters_center_and_copy_to_distinct_slots(self):
        p = self.p
        for size in (0, 1, 6, 14, 15):
            first, second = b'N' * size, b'T' * (15 - size)
            p.stage(block(first), block(second))
            for handle in (0, 1, 4095):
                t = p.consume(handle=handle)
                expected = bytearray(b'\xa5' * 0x100)
                struct.pack_into('<i', expected, 0x28, 0)
                expected[0x70:0x70 + len(centered(first))] = centered(first)
                expected[0x81:0x81 + len(centered(second))] = centered(second)
                self.assertEqual(bytes.fromhex(t['display_hex']), expected)
                self.assertEqual(t['stop_rva'], 0x12d1b9)
                self.assertEqual([(c['callee_rva'], c['source']) for c in t['text_calls']],
                    [(0x1097d0, ACTOR + 0xdbe), (0x109e70, ACTOR + 0xdce)])
                self.assertTrue(all(c['this'] == DISPLAY and c['handle'] == handle for c in t['text_calls']))
                for rva in (0x10980e, 0x109851, 0x109eae, 0x109ef4, 0x109871, 0x109f17):
                    self.assertIn(rva, t['visits'])
                self.assertTrue(t['actor_unchanged'])
                self.assert_no_scalars(t)
                result = p.read_secondary(handle=handle)
                self.assertEqual(result['eax'], 1)
                self.assertEqual(bytes.fromhex(result['output_hex']),
                                 centered(second).ljust(64, b'\xa5'))

    def test_terminator_limits_ignore_trailing_packet_bytes(self):
        p = self.p
        outputs = []
        for tail in (0, 0x35, 0xff):
            p.stage(block(b'Name', tail), block(b'LevelLike', tail))
            t = p.consume()
            outputs.append(t['display_hex'])
            reads = [e for e in t['reads'] if e['region'] == 'actor_metadata']
            text_reads = [e for e in reads if e['offset'] >= 14]
            self.assertTrue(all(14 <= e['offset'] and e['offset'] + e['size'] <= 19
                               or 30 <= e['offset'] and e['offset'] + e['size'] <= 40
                               for e in text_reads))
        self.assertEqual(len(set(outputs)), 1)

    def test_unterminated_block_fails_at_actual_native_scan_before_spill(self):
        p = self.p
        for bad in (0, 1):
            p.stage(b'A' * 16 if bad == 0 else block(b'Name'),
                    b'B' * 16 if bad == 1 else block(b'Caption'))
            with self.assertRaisesRegex(AssertionError, 'Unterminated 16-byte'):
                p.consume()
            t = p.last_trace
            scan = 0x10980e if bad == 0 else 0x109eae
            reads = [e for e in t['reads'] if e['rva'] == scan]
            self.assertEqual([e['offset'] for e in reads], list(range(14 + 16 * bad, 30 + 16 * bad)))
            self.assert_no_scalars(t)
            self.assertEqual(bytes(p.vm.mem_read(ACTOR + 0xde8, 16)), b'\xa5' * 16)

    def test_real_display_handle_and_inactive_record_guards(self):
        p = self.p
        p.stage(block(b'Name'), block(b'Caption'))
        for handle, active in ((0x1000, True), (0xffff, True), (0, False)):
            t = p.consume(handle=handle, active=active)
            self.assertEqual(t['stop_rva'], 0x12d1b9)
            self.assertFalse(any(e['region'] == 'display' for e in t['writes']))
            self.assertFalse(any(e['region'] == 'actor_metadata' and e['offset'] >= 14
                                 for e in t['reads']))
            self.assert_no_scalars(t)

    def test_normal_metadata_store_island_and_null_source_guard(self):
        p = self.p
        first = bytes((1, 0, 0, 0)) + b'Z' * 12
        r = p.stage(first, block(b'Secondary'), variant=0x400)
        copy = r['independent_constructor_copy']
        self.assertEqual(r['merge']['stop_rva'], 0x115df1)
        self.assertEqual(copy['stop_rva'], 0x121a4c)
        writes = [e for e in copy['writes'] if e['region'] == 'actor_metadata']
        self.assertEqual([(e['rva'], e['offset'], e['size']) for e in writes],
                         [(0x121a4a, i, 4) for i in range(0, 56, 4)])
        self.assertEqual(bytes(p.vm.mem_read(METADATA, 56)), bytes.fromhex(r['actor_metadata_hex']))
        before = bytes(p.vm.mem_read(ACTOR, 4096))
        missing = p.copy_metadata(source_present=False)
        self.assertFalse(any(e['region'] == 'actor_metadata' for e in missing['reads'] + missing['writes']))
        self.assertEqual([(e['rva'], e['offset'], e['hex']) for e in missing['writes']
                          if e['region'] == 'actor'], [(0x121a34, 0x1ea, '00')])
        self.assertEqual(bytes(p.vm.mem_read(ACTOR, 4096)), before)

    def test_normal_original_identity_coordinates_become_source_name_not_stats(self):
        p = self.p
        name = bytes.fromhex(p.native.row['name_bytes_hex']) + b'\0'
        for side in (1, 0):
            for second in (bytes(range(16)), b'\xff' * 16):
                first = bytes((1, 0x77, 0, 0)) + b'Q' * 12
                p.stage(first, second, variant=0x400, side=side)
                dispatch = p.consume()
                self.assertEqual(dispatch['stop_rva'], 0x12d02a)
                self.assertFalse(dispatch['text_calls'])
                t = p.normal_name()
                self.assertEqual(t['stop_rva'], 0x12d15e)
                self.assertEqual(t['selected_enemy_pointer'], p.record)
                reads = [e for e in t['reads'] if e['region'] == 'actor_metadata']
                self.assertEqual([(e['rva'], e['offset'], e['size']) for e in reads],
                    [(0x12d0c4, 12, 2), (0x12d0c8, 16, 2), (0x12d0d0, 14, 1), (0x12d0ea, 4, 4)])
                writes = [e for e in t['writes'] if e['region'] == 'actor_metadata']
                self.assertEqual({e['rva'] for e in writes}, {0x12d151, 0x12d15c})
                self.assertEqual(b''.join(bytes.fromhex(e['hex']) for e in writes), name)
                after = bytes.fromhex(t['actor_after_hex'])
                self.assertEqual(after[14:14 + len(name)], name)
                self.assertEqual(after[14 + len(name):30], first[len(name):])
                self.assertEqual(after[30:46], second)
                self.assertEqual(after[56:72], b'\xa5' * 16)
                self.assert_no_scalars(t)
                reuse = p.reuse_actor_name()
                self.assertEqual(bytes.fromhex(reuse['output_hex']), name.ljust(64, b'\xa5'))
                self.assertIn(0x116582, reuse['visits'])

    def test_missing_enemy_payload_and_missing_identity_stop_honestly(self):
        p = ParticipantMetadataProbe(enemy_payload=False)
        self.assertFalse(any(lo <= p.record <= hi for lo, hi, _ in p.vm.mem_regions()))
        for side in (0, 1):
            p.stage(bytes((1, 0, 0, 0)) + b'Q' * 12, bytes(16), variant=0x400, side=side)
            t = p.normal_name()
            self.assertEqual(t['stop_rva'], 0x10980e)
            self.assertEqual(t['selected_enemy_pointer'], p.record)
            self.assertFalse(any(e['region'] in ('actor_metadata', 'display') for e in t['writes']))
            self.assertEqual(t['actor_before_hex'], t['actor_after_hex'])
            p.stage(bytes((1, 0, 0xff, 0xff)) + b'Q' * 12, bytes(16), variant=0x400, side=side)
            t = p.normal_name()
            self.assertEqual(t['stop_rva'], 0x12d184)
            self.assertEqual(t['selected_enemy_pointer'], 0)
            self.assertFalse(t['text_calls'])

    def test_poison_preservation_instruction_integrity_and_null_authority(self):
        for poison in (0x3c, 0xff):
            p = ParticipantMetadataProbe(poison=poison)
            p.stage(block(b'Name'), block(b'Caption'))
            t = p.consume()
            self.assertEqual(t['scalar_hex'], bytes((poison,)).hex() * 16)
            self.assertEqual(bytes(p.vm.mem_read(ACTOR + 0xde8, 0x1000 - 0xde8)),
                             bytes((poison,)) * (0x1000 - 0xde8))
        p = self.p
        report = json.loads(json.dumps(p.evidence()))
        self.assertFalse(report['constructor_completed'])
        self.assertFalse(report['runtime_eligible'])
        self.assertEqual(report['game_return_adapters'], [])
        self.assertTrue(all(v is None for v in report['original_numeric_values'].values()))
        self.assertEqual(sha(p.image), IMAGE_SHA256)
        for name, (lo, hi) in SPANS.items():
            self.assertEqual(bytes(p.vm.mem_read(BASE + lo, hi - lo)), p.image[lo:hi])
            self.assertEqual(report['native_spans'][name]['sha256'], sha(p.image[lo:hi]))
        p._registers()
        with self.assertRaisesRegex(AssertionError, 'budget exhausted'):
            p._run(0x121a30, {0x121a4c}, ('constructor_copy_island',), budget=1)
        with self.assertRaises(ValueError):
            p.stage(bytes(15), bytes(16))
        with self.assertRaises(ValueError):
            p.stage(bytes(16), bytes(16), variant=0x6000)


if __name__ == '__main__':
    unittest.main()
