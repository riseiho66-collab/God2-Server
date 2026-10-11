"""Current Data/Data3 provenance and fail-closed boundaries; no native execution."""
from pathlib import Path
import struct
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.strike_lab import current_monster_auxiliary_sources as sources


class CurrentMonsterAuxiliarySourcesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        original_open = Path.open
        cls.opened = []

        def current_only(path, *args, **kwargs):
            resolved = path.resolve()
            root = next((r for r in sources.TREES if resolved.is_relative_to(r.resolve())), None)
            if root is None and resolved != sources.IMAGE.resolve():
                raise AssertionError('Only current Data/Data3 and pinned image may be opened')
            if root and any(sources.excluded(Path(p)) for p in resolved.relative_to(root).parts):
                raise AssertionError('Excluded source opened')
            mode = args[0] if args else kwargs.get('mode', 'r')
            if mode != 'rb':
                raise AssertionError('Read-only binary access required')
            cls.opened.append(resolved)
            return original_open(path, *args, **kwargs)

        guard = patch.object(Path, 'open', current_only)
        guard.start()
        cls.addClassCleanup(guard.stop)
        cls.report = sources.build_report()

    def test_inventory_counts_include_unexamined_bodies_and_excluded_config(self):
        summary = self.report['summary']
        self.assertEqual(summary['extension_counts_by_tree'], {
            'Data': {'.csvz': 7, '.romz': 735, '.wav': 10},
            'Data3': {'.csvz': 2, '.romz': 85, '.rtb': 1}})
        self.assertEqual((summary['files_in_scope'], summary['excluded_entries']), (840, 4))
        self.assertEqual((summary['files_hashed'], summary['source_bytes_read']), (10, 27578))
        self.assertEqual((summary['decoded_tables'], summary['decoded_bytes']), (9, 71569))
        self.assertEqual((summary['hashed_binary_semantics_unexamined'],
                          summary['unread_media_bodies'], summary['unexamined_binary_files']), (1, 830, 831))
        self.assertEqual({e['path'] for e in self.report['excluded_entries']},
                         {'Data3/config.iniZ', 'Data3/config2.iniZ',
                          'Data3/config_gb.iniZ', 'Data3/config2_gb.iniZ'})
        self.assertTrue(all(not e['body_read'] for e in self.report['excluded_entries']))
        self.assertEqual(len({r['path'] for r in self.report['inventory']}), 840)
        for row in self.report['inventory']:
            if row['extension'] in sources.MEDIA:
                self.assertIsNone(row['sha256'])
            else:
                self.assertEqual(len(row['sha256']), 64)
        self.assertFalse(any(path.suffix.lower() in sources.MEDIA for path in self.opened))
        self.assertFalse(self.report['scope']['data2_read'])
        self.assertFalse(self.report['scope']['native_execution_performed'])

    def test_every_table_field_and_offset_matches_current_source_bytes(self):
        self.assertEqual({t['path'] for t in self.report['tables']}, set(sources.SOURCES))
        for table in self.report['tables']:
            raw = sources.bounded_read(sources.CLIENT / table['path'])
            self.assertEqual(sources.sha(raw), table['sha256'])
            plain = sources.decode_csvz(raw, limit=sources.MAX_FILE)
            self.assertEqual(sources.sha(plain), table['decoded_sha256'])
            self.assertEqual(b''.join(bytes.fromhex(row['raw_hex']) for row in table['rows']), plain)
            for row in table['rows']:
                offset, size = row['decoded_offset'], row['length']
                actual = plain[offset:offset + size]
                self.assertEqual(sources.sha(actual), row['sha256'])
                self.assertEqual(row['line'], plain[:offset].count(b'\n') + 1)
                self.assertEqual(row['fields_hex'], [v.hex() for v in
                    actual.removesuffix(b'\n').removesuffix(b'\r').split(b',')])
            self.assertEqual(table['schema'], table['rows'][sources.SOURCES[table['path']][2] - 1])

    def test_god_and_spgeft_are_new_candidates_cat_remains_prior_covered(self):
        candidates = {c['path']: c for c in self.report['candidates']}
        self.assertEqual(len(candidates), 3)
        cat = candidates['Data/Patch/Cat.csvZ']
        self.assertEqual(cat['native_reference']['prior_audit'], 'current-world-actor-20260919.md')
        god = candidates['Data/Patch/God.csvZ']
        self.assertEqual(god['schema']['decoded_offset'], 102)
        self.assertEqual([c['column'] for c in god['native_reference']['numeric_columns']], list(range(4, 9)))
        self.assertEqual([c['store_rva'] for c in god['native_reference']['numeric_columns']],
                         [0x5e581, 0x5e59b, 0x5e5b5, 0x5e5cf, 0x5e5e7])
        spg = candidates['Data3/patch/SpgEft.csvZ']
        self.assertEqual(spg['schema']['decoded_offset'], 1091)
        self.assertEqual([c['column'] for c in spg['native_reference']['numeric_columns']], [2, 5])
        self.assertEqual([c['call_rva'] for c in spg['native_reference']['loader_calls']], [0x110c1c, 0x12e9a3])
        for candidate in candidates.values():
            self.assertIn('identity binding', candidate['missing_proof'])
            self.assertIsNone(candidate['wild_monster_values'])

    def test_static_references_are_pinned_bytes_not_native_results(self):
        image = sources.IMAGE.read_bytes()
        self.assertEqual(sources.sha(image), sources.IMAGE_SHA)
        native = self.report['native']
        for span in native['spans'].values():
            self.assertEqual(sources.sha(image[span['start_rva']:span['end_rva_exclusive']]), span['sha256'])
        for reference in native['references'].values():
            for key in ('path_literal', 'file_literal'):
                literal = reference[key]
                start = literal['literal_rva']
                value = bytes.fromhex(literal['literal_hex'])
                self.assertEqual(image[start:start + len(value) + 1], value + b'\0')
                for operand in literal['operand_rvas']:
                    self.assertEqual(struct.unpack_from('<I', image, operand)[0], 0x400000 + start)
            for column in reference['numeric_columns']:
                start = column['call_rva']
                self.assertEqual(start + 5 + struct.unpack_from('<i', image, start + 1)[0], 0x51b50)
                self.assertEqual(image[column['column_push_rva']:column['column_push_rva'] + 2],
                                 bytes((0x6a, column['column'])))
        with patch.object(sources, 'IMAGE_SHA', 'changed'):
            with self.assertRaisesRegex(ValueError, 'image hash changed'):
                sources.native_evidence()
        with patch.dict(sources.SPANS, {'bad_span': (0x5e150, 0x5e160, 'changed')}):
            with self.assertRaisesRegex(ValueError, 'span changed'):
                sources.native_evidence()

    def test_paths_reparse_points_and_sensitive_sources_fail_closed(self):
        for path in (sources.IMAGE, sources.CLIENT / 'Data2/Client.csvZ', sources.CLIENT / 'Save/a.csvZ'):
            with self.assertRaisesRegex(ValueError, 'Only current Data and Data3'):
                sources.bounded_read(path)
        for path in ('Data3/config.iniZ', 'Data3/config2.iniZ', 'Data/Save/a.csvZ',
                     'Data/logs/a.csvZ', 'Data/Classic/a.csvZ', 'Data/XJZ/a.csvZ'):
            with self.assertRaisesRegex(ValueError, 'Excluded source'):
                sources.bounded_read(sources.CLIENT / path)
        original = sources.is_reparse
        for target in (sources.CLIENT / 'Data/Patch', sources.CLIENT / 'Data/Patch/God.csvZ'):
            with patch.object(sources, 'is_reparse', lambda p: p == target or original(p)):
                with self.assertRaisesRegex(ValueError, 'Reparse'):
                    sources.bounded_read(sources.CLIENT / 'Data/Patch/God.csvZ')
                files, skipped = sources.current_files()
                self.assertNotIn(sources.CLIENT / 'Data/Patch/God.csvZ', files)
                self.assertTrue(any(e['reason'] == 'reparse' for e in skipped))
        with patch.object(sources, 'is_reparse', lambda p: p == sources.CLIENT or original(p)):
            with self.assertRaisesRegex(ValueError, 'Reparse'):
                sources.current_files()
            with self.assertRaisesRegex(ValueError, 'Reparse'):
                sources.bounded_read(sources.CLIENT / 'Data/Patch/God.csvZ')

    def test_inventory_read_decode_and_source_pin_bounds(self):
        for setting, message in (('MAX_FILES', 'file count'), ('MAX_ENTRIES', 'entry'),
                                 ('MAX_DEPTH', 'depth')):
            with patch.object(sources, setting, 1):
                with self.assertRaisesRegex(ValueError, message):
                    sources.current_files()
        with patch.object(sources, 'MAX_FILE', 1):
            with self.assertRaisesRegex(ValueError, 'Per-file byte bound'):
                sources.bounded_read(sources.CLIENT / 'Data/Patch/God.csvZ')
        with patch.object(sources, 'MAX_TOTAL', 1):
            with self.assertRaisesRegex(ValueError, 'Aggregate raw byte bound'):
                sources.build_report()
        with patch.object(sources, 'MAX_PLAIN', 1):
            with self.assertRaisesRegex(ValueError, 'expansion exceeds analysis bound'):
                sources.build_report()
        with patch.object(sources, 'MAX_IMAGE', 1):
            with self.assertRaisesRegex(ValueError, 'image byte bound'):
                sources.native_evidence()
        name = 'Data/Patch/Cat.csvZ'
        with patch.dict(sources.SOURCES, {name: ('changed', *sources.SOURCES[name][1:])}):
            with self.assertRaisesRegex(ValueError, 'raw source changed'):
                sources.build_report()

    def test_exact_token_preservation_never_qualifies_a_stat(self):
        rows = sources.table_rows(b'Index,HP,MP,\r\n1,100,20,\n2,3,4,')
        self.assertEqual([r['decoded_offset'] for r in rows], [0, 14, 24])
        self.assertEqual(rows[0]['fields_hex'], ['496e646578', '4850', '4d50', ''])
        self.assertEqual(rows[-1]['fields_hex'], ['32', '33', '34', ''])
        with patch.object(sources, 'MAX_LINES', 1):
            with self.assertRaisesRegex(ValueError, 'line bound'):
                sources.table_rows(b'a\nb\n')
        for row in self.report['field_authority'].values():
            self.assertIsNone(row['qualified_values'])
            self.assertEqual(row['verified_monster_records'], 0)
        self.assertEqual(self.report['summary']['qualified_wild_monster_numeric_values'], 0)
        self.assertFalse(self.report['scope']['binary_absence_claim'])
        self.assertFalse(self.report['all_monster_numeric_data_complete'])
        self.assertFalse(self.report['runtime_eligible'])


if __name__ == '__main__':
    unittest.main()
