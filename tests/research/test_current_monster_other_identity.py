"""Current-only bounded 1C 2000/6000 dataflow; prior variant suite is untouched."""
from pathlib import Path
import json
import struct
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.strike_lab import current_monster_other_identity as other
from unicorn import UcError, UC_ERR_READ_UNMAPPED


class CurrentMonsterOtherIdentityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        original_open = Path.open

        def current_only(path, *args, **kwargs):
            if any('classic' in part.lower() or 'xjz' in part.lower()
                   or part.lower() == 'legacy-evidence' for part in path.resolve().parts):
                raise AssertionError('Retired source access forbidden')
            return original_open(path, *args, **kwargs)

        guard = patch.object(Path, 'open', current_only)
        guard.start()
        cls.addClassCleanup(guard.stop)
        cls.probe = other.OtherIdentityProbe()
        cls.report = cls.probe.evidence()

    def test_complete_source_namespace_and_native_name_projection(self):
        p, r = self.probe, self.report
        self.assertEqual(len(p.rows), 4043)
        self.assertEqual(p.source_maximum, 6224)
        self.assertEqual(r['coverage']['in_range_slots_without_source_row'], 2182)
        self.assertEqual(r['coverage']['native_field6000_source_joins'], 4043)
        self.assertEqual(len(r['source_inventory']), 4043)
        plain = other.current_source()
        for row, actual in zip(p.rows, r['source_inventory']):
            raw = bytes.fromhex(row['raw_record_hex'])
            offset = row['decoded_offset']
            self.assertEqual(plain[offset:offset + len(raw)], raw)
            self.assertEqual(other.sha(raw), row['sha256'])
            self.assertEqual(row['source_line'], plain[:offset].count(b'\n') + 1)
            pointer = other.RECORDS + 94 * row['selector']
            name = bytes.fromhex(row['name_hex']) + b'\0'
            self.assertEqual(bytes(p.vm.mem_read(pointer, len(name))), name)
            self.assertEqual(actual['native_record_pointer'], pointer)
            self.assertEqual(actual['native_stop_rva'], 0x1182b9)
            self.assertIsNone(actual['monster_classification'])
        self.assertEqual(len({row['selector'] for row in p.rows}), 4043)
        self.assertEqual(bytes(p.vm.mem_read(other.BASE + 0x18a12c, 14)), b'NPCAppearData\0')

    def test_field2000_native_actor_copy_and_next_call_arguments(self):
        p = self.probe
        for slot in range(28):
            t = p.join(0x2000, 0xabcd, slot=slot, ordinal=0x9876)
            self.assertEqual(t['stop_rva'], 0x1161e8)
            self.assertIn(0x116149, t['visits'])
            self.assertIn(0x11615c, t['visits'])
            self.assertNotIn(0x11608b, t['visits'])
            self.assertIsNone(t['appearance_call'])
            self.assertEqual(t['actor_metadata_hex'], t['metadata_hex'])
            metadata = bytes.fromhex(t['metadata_hex'])
            self.assertEqual(metadata[:2], b'\xcd\xab')
            self.assertEqual(metadata[12:14], b'\x76\x98')
            self.assertEqual(metadata[14:46], bytes(range(32)))
            self.assertEqual(metadata[46:], bytes(range(46, 56)))
            writes = [(pc, address, size) for pc, address, size in t['writes']
                      if other.ACTOR <= address < other.ACTOR + 0x2000]
            self.assertEqual(writes, [(0x11615c, other.ACTOR + 0xdb0 + 4 * i, 4) for i in range(14)])
            call = t['next_call']
            self.assertFalse(call['executed'])
            self.assertEqual(call['callee_rva'], 0x1221b0)
            self.assertEqual(call['this'], other.MANAGER)
            args = call['arguments']
            self.assertEqual([args[0] & 65535, args[1], args[2] & 65535, args[3], args[4],
                              args[5] & 255, args[6] & 255, args[7]],
                             [0x1234, 10, 0x5678, 0x59, 5000, slot // 14, slot % 14, other.METADATA])
            self.assertFalse(any(other.COUNT <= address < other.RECORDS + 94 * 6225
                                 for _, address, _ in t['reads']))

    def test_field6000_actual_appearance_call_and_diagnostic_dword_flow(self):
        p = self.probe
        selector = p.rows[0]['selector']
        name = bytes.fromhex(p.rows[0]['name_hex']) + b'\0'
        for poison in (0, 0xa5, 255):
            for appearance in (bytes(8), bytes(range(8)), b'\xff' * 8):
                for slot in (0, 14, 27):
                    t = p.join(0x6000, selector, slot=slot, appearance=appearance,
                               poison=poison, variant_bits=0x9fff)
                    self.assertEqual(t['stop_rva'], 0x1182b9)
                    self.assertIn(0x116112, t['visits'])
                    self.assertIn(0x1177c0, t['visits'])
                    self.assertIn(0x11781d, t['visits'])
                    self.assertNotIn(0x117827, t['visits'])
                    call = t['appearance_call']
                    self.assertEqual(call['this'], other.BATTLE)
                    self.assertEqual(call['return_rva'], 0x116117)
                    self.assertEqual(bytes.fromhex(call['request_hex']),
                                     bytes((0, slot, 1)) + appearance + bytes(3))
                    metadata = bytes.fromhex(t['metadata_hex'])
                    self.assertEqual(metadata[14:14 + len(name)], name)
                    self.assertEqual(t['actor_metadata_hex'], bytes(range(56)).hex())
                    self.assertFalse(any(other.ACTOR <= address < other.ACTOR + 0x2000
                                         for _, address, _ in t['writes']))
        t = p.join(0x6000, selector, actor_present=False)
        self.assertEqual(t['stop_rva'], 0x1182b9)
        self.assertEqual(bytes.fromhex(t['metadata_hex'])[46:], bytes(10))

    def test_fallback_sparse_slots_and_signed_boundaries(self):
        p = self.probe
        for selector, maximum in ((6225, None), (65535, None), (32768, 32767), (0, -1), (1, -32768)):
            t = p.join(0x6000, selector, maximum=maximum)
            self.assertIn(0x11611d, t['visits'])
            self.assertEqual(t['stop_rva'], 0x1161e8)
            self.assertIsNone(t['appearance_call'])
            self.assertEqual(t['metadata_hex'], t['actor_metadata_hex'])
            metadata = bytes.fromhex(t['metadata_hex'])
            self.assertEqual(metadata[14], 0)
            self.assertEqual(metadata[15:46], bytes(range(1, 32)))
        holes = [key for key in range(6225) if key not in p.by_id]
        for selector in (0, holes[len(holes) // 2], holes[-1]):
            t = p.join(0x6000, selector)
            self.assertEqual(t['stop_rva'], 0x1160b9)
            self.assertEqual(t['selected_record_pointer'], other.RECORDS + 94 * selector)
            self.assertFalse(any(other.RECORDS <= address < other.RECORDS + 94 * 6225
                                 for _, address, _ in t['reads']))
        self.assertEqual(p.join(0x6000, 6224)['stop_rva'], 0x1182b9)

    def test_actor_preconditions_and_metadata_input_authority(self):
        p = self.probe
        for field, selector in ((0x2000, 65535), (0x6000, 65535)):
            t = p.join(field, selector, actor_handle=-1)
            self.assertEqual(t['stop_rva'], 0x11619d)
            self.assertEqual(t['actor_metadata_hex'], t['metadata_hex'])
            self.assertNotIn(0x2b10, t['visits'])
        for poison in (0, 0xa5, 255):
            for selector in (0, 1, 6224, 65535):
                prior = bytes((0x5a,)) * 56
                t = p.join(0x2000, selector, poison=poison, prior_metadata=prior)
                self.assertEqual(t['stop_rva'], 0x1161e8)
                metadata = bytes.fromhex(t['metadata_hex'])
                self.assertEqual(metadata[:2], struct.pack('<H', selector))
                self.assertEqual(metadata[2:4], prior[2:4])
                self.assertEqual(metadata[46:], prior[46:])
        try:
            p.join(0x2000, 1, actor_present=False)
        except UcError as error:
            self.assertEqual(error.errno, UC_ERR_READ_UNMAPPED)
        except AssertionError as error:
            self.assertIn('Unqualified read 1a/2 at 116149', str(error))
        else:
            self.fail('Original field2000 requires a nonnull existing actor')
        self.assertFalse(any(lo <= 0 <= hi for lo, hi, _ in p.vm.mem_regions()))

    def test_pins_limits_null_authority_and_no_prior_sweeps(self):
        p = self.probe
        r = json.loads(json.dumps(self.report))
        self.assertEqual(other.sha(p.image), other.IMAGE_SHA256)
        for name, (lo, hi) in other.SPANS.items():
            self.assertEqual(r['native_spans'][name]['sha256'], other.sha(p.image[lo:hi]))
        self.assertFalse(r['authority']['full_loader_executed'])
        self.assertFalse(r['runtime_eligible'])
        self.assertIsNone(r['coverage']['all_monsters_including_boss'])
        self.assertIsNone(r['coverage']['monster_classification'])
        self.assertEqual(r['coverage']['verified_stat_skill_drop_assignments'], 0)
        for key in ('field2000', 'field6000', 'field6000_out_of_range'):
            self.assertTrue({0x5a1a0, 0x5a0a0, 0x5a560, 0x5a120, 0x1116a9}.isdisjoint(r[key]['visits']))
        with self.assertRaises(ValueError):
            other.namespace(other.current_source()[:-1])
        with patch.object(other, 'IMAGE_SHA256', 'changed'):
            with self.assertRaisesRegex(ValueError, 'image changed'):
                other.OtherIdentityProbe()
        for args in ((0, 1), (0x4000, 1), (0x2000, -1), (0x6000, 65536)):
            with self.assertRaises(ValueError):
                p.join(*args)
        for kwargs in ({'variant_bits': 0x2000}, {'appearance': bytes(7)}, {'slot': 28},
                       {'maximum': 32768}, {'prior_metadata': bytes(55)}, {'payload': bytes(35)}):
            with self.assertRaises(ValueError):
                p.join(0x2000, 1, **kwargs)
        p._reset()
        with self.assertRaisesRegex(AssertionError, 'budget exhausted'):
            p._run(0x115c90, {0x1161e8}, ('packet_prefix',), budget=1)


if __name__ == '__main__':
    unittest.main()
