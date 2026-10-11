"""Focused current-only original variant loader/lookup/consumer checks."""
from pathlib import Path
import json
import struct
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.strike_lab.current_monster_variant_identity import (
    VariantIdentityProbe, SECTION, SECTION_START, SECTION_END, SECTION_SHA,
    SPECIAL, RESULT, DIAGNOSTIC, BASE, SP, PACKET, SPANS, IMAGE_SHA256,
    GAME_SHA256, GAME_DECODED_SHA256, FIELDS, sha)
from unicorn import UcError


class CurrentMonsterVariantIdentityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        original_open = Path.open

        def current_only(path, *args, **kwargs):
            if any('classic' in p.lower() or 'xjz' in p.lower()
                   or p.lower() == 'legacy-evidence' for p in path.resolve().parts):
                raise AssertionError('Retired source access forbidden')
            return original_open(path, *args, **kwargs)

        guard = patch.object(Path, 'open', current_only)
        guard.start()
        cls.addClassCleanup(guard.stop)
        cls.probe = VariantIdentityProbe()
        cls.report = cls.probe.evidence()

    def test_complete_current_special_source_and_original_loader(self):
        p, r = self.probe, self.report
        self.assertEqual(p.plain[SECTION_START:SECTION_END], SECTION)
        self.assertEqual(sha(SECTION), SECTION_SHA)
        self.assertEqual(sha(p.plain), GAME_DECODED_SHA256)
        self.assertEqual(r['source']['sha256'], GAME_SHA256)
        self.assertEqual(r['coverage']['special_source_rows'], 1)
        self.assertEqual(r['coverage']['special_native_rows_loaded'], 1)
        row = r['special_records'][0]
        self.assertEqual(bytes.fromhex(row['raw_record_hex']), b'1,IGS_SPECIAL,0,0,149,1\r\n')
        self.assertEqual(row['decoded_offset'], 2781799)
        self.assertEqual(p.plain.splitlines(keepends=True)[row['source_line'] - 1],
                         bytes.fromhex(row['raw_record_hex']))
        self.assertEqual(p.loaded_record, b'\x02\x95' + bytes(4) + b'\xa5' * 20)
        self.assertEqual(p.stream_position, len(p.stream))
        self.assertEqual(p.allocations, [(26, SPECIAL)])
        self.assertNotIn(0x5a1a0, p.loader_trace['visits'])
        for rva in (0x5a560, 0x51a90, 0x51be0, 0x51b50, 0x51ba0, 0x5a85d):
            self.assertIn(rva, p.loader_trace['visits'])
        written = {i for offset, size in p.loader_trace['special_writes']
                   for i in range(offset, offset + size)}
        self.assertEqual(written, set(range(6)))

    def test_malloc_poison_and_inherited_bytes_are_not_source_values(self):
        for poison in (0, 0xa5, 0xff):
            p = VariantIdentityProbe(allocation_poison=poison)
            self.assertEqual(p.loaded_record[:6], b'\x02\x95' + bytes(4))
            self.assertEqual(p.loaded_record[6:], bytes((poison,)) * 20)
            for header, name in ((0, b''), (0xab, b'DiagnosticBase'), (0xff, b'123456789ABCDEF')):
                trace = p.lookup(1, header=header, name=name)
                self.assertEqual(trace['eax'], RESULT)
                self.assertEqual(bytes.fromhex(trace['result_hex']),
                                 bytes(((header & 0xf0) | 2, 149)) + name.ljust(16, b'\0')
                                 + bytes((poison,)) * 8)
            self.assertEqual(bytes(p.vm.mem_read(SPECIAL, 26)), p.loaded_record)

    def test_all_low_byte_selectors_and_original_packet_rewrite(self):
        p = self.probe
        rows = self.report['selector_counterfactuals']
        self.assertEqual([r['selector'] for r in rows], list(range(256)))
        for row in rows:
            s = row['selector']
            self.assertEqual(row['record_pointer'], RESULT if s == 1 else p.record_base)
            self.assertEqual(row['special_lookup_called'], s != 0)
            self.assertEqual(row['variant_after'],
                             0x1c00 if s == 0 else (0x400 if s == 1 else 0x1400) | s)
        for poison in (0, 0xa5, 0xff):
            for variant in (0x0001, 0x0401, 0x1c01, 0x8001, 0x9c01):
                t = p.join(1, 0, 1, variant, poison=poison)
                before, after = bytes.fromhex(t['packet_before_hex']), bytes.fromhex(t['packet_after_hex'])
                self.assertEqual(t['edx'], RESULT)
                self.assertEqual(t['packet_writes'], [(0x115e47, 5, 2)])
                self.assertEqual(before[:5] + before[7:], after[:5] + after[7:])
                self.assertEqual(struct.unpack_from('<H', after, 5)[0], (variant & 0xe3ff) | 0x400)
                self.assertEqual(bytes.fromhex(t['metadata_hex'])[7], 23)
        t = self.report['special_consumer']['trace']
        self.assertIn(0x115e25, t['visits'])
        self.assertIn(0x5a17f, t['visits'])
        self.assertEqual(t['stop_rva'], 0x115e77)

    def test_complete_alternate_namespace_without_payload_reads(self):
        p, r = self.probe, self.report
        expected = [row for row in p.catalog['records'] if row['lookup_visible']
                    and row['area'] == 0 and row['scene'] in (2, 3, 13)]
        self.assertEqual(r['coverage']['alternate_scenes'], {'2': 816, '3': 2070, '13': 1165})
        self.assertEqual(len(r['alternate_records']), 4051)
        self.assertEqual([row['source_record_index'] for row in r['alternate_records']],
                         [row['source_record_index'] for row in expected])
        regions = list(p.vm.mem_regions())
        for actual, source in zip(r['alternate_records'], expected):
            for key, value in source.items():
                self.assertEqual(actual[key], value)
            pointer = p.record_base + 26 * source['source_record_index']
            self.assertEqual(actual['native_pointer'], pointer)
            self.assertFalse(any(lo <= pointer <= hi for lo, hi, _ in regions))
            self.assertIsNone(actual['monster_classification'])
        for scene, flags in ((2, 0), (3, 0x8000), (13, 0x4000)):
            count = len(p.catalog['groups'][0, scene])
            for ordinal in (0, count + 1, 0x3fff):
                self.assertEqual(p.join(16, 65535, flags | ordinal, 0x4001)['edx'], 0)
            for variant in (0x4000, 0x4001, 0x40ff, 0x5c01, 0xc001):
                t = p.join(2, 15, flags | 1, variant)
                self.assertEqual(t['edx'], p.record_base + 26 * p.catalog['group_offsets'][0, scene])
                self.assertNotIn(0x115e25, t['visits'])
                self.assertEqual(t['packet_before_hex'], t['packet_after_hex'])
        # Both ordinal flags choose scene 3: 0x8000 takes precedence.
        t = p.join(16, 65535, 0xc001, 0x4001)
        self.assertEqual(t['edx'], p.record_base + 26 * p.catalog['group_offsets'][0, 3])

    def test_dispatch_and_missing_base_prevent_special_lookup(self):
        p = self.probe
        self.assertEqual(struct.unpack_from('<4I', p.image, 0x11662c),
                         tuple(BASE + x for x in (0x115df1, 0x116149, 0x115df1, 0x11608b)))
        for bits, stop in ((0x2000, 0x116149), (0x6000, 0x11608b)):
            t = p.join(1, 0, 1, bits | 1)
            self.assertEqual(t['stop_rva'], stop)
            self.assertNotIn(0x115e25, t['visits'])
            self.assertNotIn(0x115e70, t['visits'])
        t = p.join(2, 15, 1, 0x0401)
        self.assertEqual(t['stop_rva'], 0x116037)
        self.assertNotIn(0x115e25, t['visits'])
        self.assertEqual(t['packet_before_hex'], t['packet_after_hex'])
        t = p.join(1, 0, 1, 0x0400)
        self.assertNotIn(0x115e25, t['visits'])

    def test_direct_lookup_fallback_and_zero_underflow(self):
        p = self.probe
        for selector in (2, 255, 256, 32768, 65535):
            t = p.lookup(selector)
            self.assertEqual(t['eax'], DIAGNOSTIC)
            self.assertNotIn(0x5a156, t['visits'])
        # Original 5A120 has only an upper bound; the consumer bypasses zero.
        with self.assertRaises((UcError, AssertionError)):
            p.lookup(0)
        self.assertFalse(any(lo <= SPECIAL - 26 <= hi for lo, hi, _ in p.vm.mem_regions()))
        self.assertEqual(p.lookup(1)['eax'], RESULT)

    def test_pins_null_authority_and_bounded_execution(self):
        p = self.probe
        self.assertEqual(sha(p.image), IMAGE_SHA256)
        r = json.loads(json.dumps(self.report))
        for name, (lo, hi) in SPANS.items():
            self.assertEqual(r['native_spans'][name]['sha256'], sha(p.image[lo:hi]))
        self.assertFalse(r['runtime_eligible'])
        self.assertFalse(r['coverage']['all_monster_systems_enumerated'])
        self.assertIsNone(r['coverage']['boss_record_count'])
        self.assertIsNone(r['coverage']['all_monsters_including_boss_denominator'])
        self.assertEqual(r['coverage']['verified_stat_skill_drop_assignments'], 0)
        self.assertEqual(r['special_records'][0]['fields'], dict.fromkeys(FIELDS))
        self.assertIsNone(r['special_records'][0]['monster_classification'])
        self.assertIn('independently_staged', r['authority']['enyname'])
        self.assertEqual(r['authority']['diagnostic_payload_indices'], [0])
        p._reset(PACKET)
        with self.assertRaisesRegex(AssertionError, 'budget exhausted'):
            p._run(0x115c90, {0x115e77}, budget=1)
        for args in ((17, 0, 1, 1), (True, 0, 1, 1), (1, 0, -1, 1), (1, 0, 1, 65536)):
            with self.assertRaises(ValueError):
                p.join(*args)
        for selector in (-1, 65536, True):
            with self.assertRaises(ValueError):
                p.lookup(selector)
        with self.assertRaises(ValueError):
            p.stage_diagnostic_base(7815)
        with patch('tools.strike_lab.current_monster_variant_identity.IMAGE_SHA256', 'changed'):
            with self.assertRaisesRegex(ValueError, 'image hash changed'):
                VariantIdentityProbe()
        with patch('tools.strike_lab.current_monster_variant_identity.GAME_SHA256', 'changed'):
            with self.assertRaisesRegex(ValueError, 'source hash changed'):
                VariantIdentityProbe()


if __name__ == '__main__':
    unittest.main()
