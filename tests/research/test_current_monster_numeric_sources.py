"""Bounded current file provenance and non-promotion, without native loaders."""
from pathlib import Path
import json
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.strike_lab import current_monster_numeric_sources as sources


class CurrentMonsterNumericSourcesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        original_open = Path.open
        opened = []

        def current_only(path, *args, **kwargs):
            resolved = path.resolve()
            if not (resolved.is_relative_to(sources.DATA.resolve()) or resolved == sources.IMAGE.resolve()):
                raise AssertionError('Only current Data2 and pinned image may be opened')
            mode = args[0] if args else kwargs.get('mode', 'r')
            if any(flag in mode for flag in ('w', 'a', '+', 'x')):
                raise AssertionError('Source audit must be read-only')
            opened.append(resolved)
            return original_open(path, *args, **kwargs)

        guard = patch.object(Path, 'open', current_only)
        guard.start()
        cls.addClassCleanup(guard.stop)
        cls.report = sources.build_report()
        cls.opened = opened

    def test_observed_current_inventory_and_explicit_binary_boundary(self):
        r = self.report
        # The bilingual client adds 44 CSVZ assets (45 -gb.csvZ in total).
        # Audit their
        # bytes as current files without promoting them to original stat rules.
        expected = {'.bin': 1, '.can': 14, '.csvz': 109, '.hmdz': 145, '.mbd': 71,
                    '.mbdz': 142, '.mdlz': 142, '.mdtz': 142, '.mmbz': 142,
                    '.romz': 6323, '.rtb': 190, '.wav': 944}
        self.assertEqual(r['summary']['extension_counts'], expected)
        self.assertEqual(r['summary']['files_enumerated'], 8365)
        self.assertEqual(r['summary']['files_hashed'], 1098)
        self.assertEqual(r['summary']['unexamined_binary_files'], 846)
        self.assertEqual(r['summary']['text_outlines'], 248)
        self.assertEqual(r['summary']['source_bytes_read'], 97025533)
        self.assertLess(r['summary']['source_bytes_read'], sources.MAX_TOTAL)
        self.assertEqual(r['skipped_links'], [])
        self.assertEqual(len({row['path'] for row in r['inventory']}), 8365)
        self.assertEqual(sum(row['path'].lower().endswith('-gb.csvz') for row in r['inventory']),45)
        for row in r['inventory']:
            if row['extension'] in sources.MEDIA:
                self.assertIsNone(row['sha256'])
                self.assertEqual(row['content_status'], 'media_not_read')
            else:
                self.assertEqual(len(row['sha256']), 64)
        self.assertFalse(any(path.suffix.lower() in sources.MEDIA for path in self.opened))
        self.assertFalse(r['scope']['binary_absence_claim'])
        self.assertFalse(r['scope']['native_execution_performed'])

    def test_every_candidate_schema_offset_and_hash_matches_current_bytes(self):
        decoded = {}
        for candidate in self.report['candidates']:
            path = sources.CLIENT / candidate['path']
            raw = sources.bounded_read(path)
            self.assertEqual(sources.sha(raw), candidate['sha256'])
            if path.suffix.lower() != '.csvz':
                continue
            plain = decoded.setdefault(candidate['path'], sources.decode_csvz(raw, limit=sources.MAX_FILE))
            self.assertEqual(sources.sha(plain), candidate['decoded_sha256'])
            schema = candidate['schema']
            for row in schema if isinstance(schema, list) else [schema]:
                offset, length = row['decoded_offset'], row['length']
                actual = plain[offset:offset + length]
                self.assertEqual(actual.hex(), row['raw_hex'])
                self.assertEqual(sources.sha(actual), row['sha256'])
                self.assertEqual(row['line'], plain[:offset].count(b'\n') + 1)
                self.assertEqual(row['fields_hex'], [field.hex() for field in actual.rstrip(b'\r\n').split(b',')])
        self.assertEqual(self.report['summary']['candidate_count'], 21)

    def test_strongest_literal_and_native_reader_binding(self):
        token = self.report['unresolved_literal']
        raw = sources.bounded_read(sources.CLIENT / token['path'])
        self.assertEqual(sources.sha(raw), token['sha256'])
        plain = sources.decode_csvz(raw)
        self.assertEqual(sources.sha(plain), token['decoded_sha256'])
        self.assertEqual(len(token['decoded_offsets']), 464)
        self.assertEqual(token['decoded_offsets'][0], 210)
        for offset in token['decoded_offsets']:
            self.assertEqual(plain[offset:offset + 15], b'Base100_Index37')
        self.assertEqual(token['mapped_image_occurrences'], [])
        reference = token['native_reference']
        self.assertEqual((reference['call_rva'], reference['target_rva']), (0x56b01, 0x5c640))
        image = sources.IMAGE.read_bytes()
        with self.assertRaisesRegex(ValueError, 'reference mismatch'):
            sources.native_reference(image, 0x189fa0, b'wrong', 0x56ac1, 0x56b01, 0x5c640)

    def test_skill_definition_envelope_is_not_monster_ownership(self):
        candidate = next(c for c in self.report['candidates'] if c['path'].endswith('cbspec2.bin'))
        self.assertEqual(candidate['schema']['definition_count'], 448)
        self.assertIsNone(candidate['schema']['numeric_payload_semantics'])
        source = sources.bounded_read(sources.CLIENT / candidate['path'])
        for row in candidate['source_records']:
            raw = source[row['source_offset']:row['source_offset'] + row['length']]
            self.assertEqual(sources.sha(raw), row['sha256'])
            self.assertEqual(raw[:2], bytes((row['id'], row['bank'])))
        self.assertEqual(candidate['native_reference']['call_rva'], 0x110c45)
        for c in self.report['candidates']:
            self.assertIsNone(c['wild_monster_values'])
            self.assertFalse(c['runtime_eligible'])
        self.assertTrue(all(row['qualified_values'] is None and row['verified_monster_records'] == 0
                            for row in json.loads(json.dumps(self.report))['field_authority'].values()))
        self.assertFalse(self.report['all_monster_numeric_data_complete'])

    def test_skipped_prior_names_cards_and_search_limit_are_explicit(self):
        paths = {c['path'] for c in self.report['candidates']}
        for name in ('ChangeDollCard', 'eny', 'FightEny'):
            self.assertFalse(any(path.endswith('/' + name + '.csvZ') for path in paths))
        game = next(t for t in self.report['text_outlines'] if t['path'].endswith('/gamedata.csvZ'))
        self.assertEqual(game['excluded_decoded_spans'], [[7887, 140789], [2500836, 2781824]])
        self.assertTrue(sources.EXCLUDED_SECTIONS.isdisjoint(s['tag'] for s in game['section_declarations']))
        # Exact header labels do not turn numeric rows or prose into stat fields.
        outline = sources.table_outline(b'Index,HP,MP\r\n1,100,20\r\n2,HP=999 is a story,0\r\n')
        self.assertEqual(len(outline['schemas']), 1)
        self.assertEqual(outline['schemas'][0]['decoded_offset'], 0)
        self.assertEqual(len(outline['schemas'][0]['matches']), 2)
        target = self.report['numeric_next_target']
        self.assertEqual((target['call_rva'], target['callee_rva']), (0x56b01, 0x5c640))
        self.assertEqual(target['current_qualified_scope'], 'companion_pet_category_only')
        self.assertIsNone(target['wild_monster_binding'])
        self.assertFalse(target['wholly_unexamined'])
        self.assertFalse(target['full_loader_executed_in_prior_proof'])
        self.assertEqual(target['prior_qualified_row_span'], [0x5c6a6, 0x5c9b5])
        self.assertEqual(target['prior_read_columns'], list(range(9)))
        self.assertEqual(target['prior_unread_columns'], [9, 10, 11])
        self.assertEqual(target['prior_proof'], 'docs/research/companion-growth-evidence-20260919.md')

    def test_prior_scalar_proof_is_disqualified_not_proposed_again(self):
        row, = self.report['disqualified_source_recovery_targets']
        self.assertEqual((row['call_rva'], row['callee_rva']), (0x11740a, 0x12d970))
        self.assertEqual((row['logical_opcode'], row['subtype'], row['side']), (0x86, 1, 0))
        self.assertEqual(row['packet_to_actor'], [
            {'packet_offset': 9, 'actor_offset': 0xdec, 'size': 4},
            {'packet_offset': 5, 'actor_offset': 0xdf4, 'size': 4}])
        self.assertEqual(row['prior_proof'], ['tools/strike_lab/current_battle_scalar_result.py',
                                            'tests/research/test_current_battle_scalar_result.py'])
        self.assertFalse(row['source_recovery_eligible'])
        self.assertFalse(row['runtime_eligible'])
        self.assertNotEqual(self.report['numeric_next_target']['callee_rva'], row['callee_rva'])

    def test_fail_closed_paths_sizes_and_pinned_image(self):
        with self.assertRaisesRegex(ValueError, 'Only current Data2'):
            sources.bounded_read(sources.IMAGE)
        with patch.object(sources, 'MAX_FILE', 1):
            with self.assertRaisesRegex(ValueError, 'byte bound'):
                sources.bounded_read(sources.DATA / 'Client.csvZ')
        with patch.object(sources, 'MAX_FILES', 1):
            with self.assertRaisesRegex(ValueError, 'file count bound'):
                sources.current_files()
        with patch.object(sources, 'IMAGE_SHA', 'changed'):
            with self.assertRaisesRegex(ValueError, 'image hash changed'):
                sources.build_report()


if __name__ == '__main__':
    unittest.main()
