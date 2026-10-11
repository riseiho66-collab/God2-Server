"""Current-original-only extraction and bounded native row-consumer checks.

No historical corpus, generated catalog fixture, server, or live client needed.
All positive table records come from the seven pinned current client sources.
"""
import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

from tools.strike_lab import recover_companion_growth as growth


ROOT = Path(__file__).resolve().parents[2]
CLIENT = ROOT.parent / 'God2'
IMAGE = ROOT / 'artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin'


class CurrentGrowthExtractionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sources, cls.decoded = growth.load_current_sources(CLIENT)
        cls.result = growth.build_growth(CLIENT)

    def assert_source_record(self, row, decoded):
        raw = bytes.fromhex(row['raw_record_hex'])
        offset = row['decoded_offset']
        self.assertEqual(decoded[offset:offset + len(raw)], raw)
        self.assertEqual(decoded[:offset].count(b'\n') + 1, row['source_line'])
        self.assertEqual(row, growth.record(raw, row['source_line'], offset))

    def test_all_records_headers_and_selected_text_belong_to_original_bytes(self):
        for section in self.result['sections'].values():
            for row in (section['header'], *section['records']):
                self.assert_source_record(row, self.decoded['gamedata'])
        for name, table in self.result['auxiliary_tables'].items():
            rows = table['preamble'] + table['records'] + table.get('labels', [])
            if 'declaration' in table:
                rows.append(table['declaration'])
            for row in rows:
                self.assert_source_record(row, self.decoded[name])
            ordered = sorted(rows, key=lambda r: r['source_line'])
            self.assertEqual(b''.join(bytes.fromhex(r['raw_record_hex']) for r in ordered),
                             self.decoded[name])
        for section in self.result['text_only_records']:
            name = Path(section['source_file']).stem
            for row in (section['section_header'], *section['records']):
                self.assert_source_record(row, self.decoded[name])
            self.assertFalse(section['runtime_verified'])
            self.assertFalse(section['runtime_eligible'])

    def test_pinned_manifests_and_no_external_corpus_dependencies(self):
        self.assertEqual(len(self.sources), 7)
        self.assertEqual(self.result['sources'], self.sources)
        for name, hashes in growth.SOURCE_HASHES.items():
            manifest = self.sources[growth.source_path(name)]
            raw = (CLIENT / growth.source_path(name)).read_bytes()
            self.assertEqual((growth.digest(raw), growth.digest(self.decoded[name])), hashes)
            self.assertEqual((manifest['size'], manifest['decoded_size']), (len(raw), len(self.decoded[name])))
        self.assertEqual(set(self.result['native_verification']), {'status', 'growth_formula_verified'})
        self.assertEqual(self.result['native_verification']['status'], 'not_run')

    def test_source_label_does_not_infer_runtime_pet_subtype(self):
        labels = self.result['source_category_labels']
        self.assertEqual([row['tag'] for row in labels], ['GOD', 'PET', 'COM', 'NCP'])
        for row in labels:
            self.assertIsNone(row['runtime_subtype'])
            self.assertEqual(row['evidence_class'], 'source_label_only')
            self.assert_source_record(row['source'], self.decoded['gamedata'])
        self.assertEqual({name: section['declared_count'] for name, section in self.result['sections'].items()},
                         {'ItemType': 46, 'GOD': 34, 'PET': 147, 'COM': 2070, 'NCP': 1165,
                          'GodLevel': 4, 'FightPetSkill': 254, 'NewFightPet2Skill': 255, 'CategoryNum': 16})

    def test_unknown_rates_bases_upgrades_and_exp_are_not_zero(self):
        expected = {'growth_rate', 'base_value', 'upgrade_formula', 'experience_thresholds'}
        for family in ('battle_pet', 'deity'):
            concepts = self.result['unknown_contracts'][family]
            self.assertEqual(set(concepts), expected)
            for value in concepts.values():
                self.assertIsNone(value['value'])
                self.assertEqual(value['status'], 'unknown')
                self.assertFalse(value['runtime_eligible'])
                self.assertTrue(value['missing_evidence'])
        self.assertFalse(self.result['runtime_eligible'])
        self.assertEqual(growth.decimal(b'0'), 0)
        for token in (b'', b' ', b'unknown', b'-1', b'1.0'):
            with self.subTest(token=token), self.assertRaises(ValueError):
                growth.decimal(token)

    def test_godlevel_is_four_literal_title_code_records(self):
        rows = self.result['sections']['GodLevel']['records']
        self.assertEqual([growth.fields(row) for row in rows], [
            [bytes.fromhex('a470a550a6ec'), b'1'], [bytes.fromhex('a5bfa550a6ec'), b'2'],
            [bytes.fromhex('b16aa550a6ec'), b'3'], [bytes.fromhex('bbf4a550a6ec'), b'4']])
        self.assertEqual([row['source_line'] for row in rows], list(range(21165, 21169)))

    def test_category_declaration_discrepancy_and_opaque_base_reference(self):
        table = self.result['auxiliary_tables']['NewCombatPet_Category']
        self.assertEqual(table['declared_count_literal'], 469)
        self.assertEqual(table['actual_record_count'], 464)
        self.assertFalse(table['declaration_matches_data_count'])
        rows = [growth.fields(row) for row in table['records']]
        self.assertEqual({row[10] for row in rows}, {b'Base100_Index37'})
        self.assertEqual({len(row) for row in rows}, {12})
        self.assertEqual([(int(row[0]), int(row[1])) for row in rows],
                         [(group, index) for group in range(1, 30) for index in range(16)])

    def test_quality_star_explicit_zero_preserved_without_upgrading_semantics(self):
        table = self.result['auxiliary_tables']['NewCombatPet_QualityStar']
        rows = [[growth.decimal(v) for v in growth.fields(row)] for row in table['records']]
        self.assertEqual(rows, [
            [0, 15, 30, 45, 75, 95, 115, 135, 175, 200, 225, 250, 300, 330, 360, 390],
            [0, 30, 60, 90, 150, 190, 230, 270, 350, 400, 450, 500, 600, 660, 720, 780]])
        self.assertEqual(table['scalar_token_count'], 32)
        self.assertIsNone(self.result['unknown_contracts']['battle_pet']['base_value']['value'])

    def test_auxiliary_missing_extra_and_repaired_count_rejected(self):
        original = self.decoded['NewCombatPet_Category']
        cases = (original.replace(b'CategoryDetailNum,469', b'CategoryDetailNum,464'),
                 original + original.split(b'\n')[-2] + b'\n',
                 original[:original.rfind(b'\n', 0, len(original) - 1) + 1],
                 original.replace(b',Y,Y,N,N,Y,N,', b',Y,,N,N,Y,N,', 1))
        for source in cases:
            with self.subTest(sha=growth.digest(source)), self.assertRaises(ValueError):
                growth.parse_auxiliary('NewCombatPet_Category', source)
        quality = self.decoded['NewCombatPet_QualityStar']
        for source in (quality.replace(b'0,15,30', b',15,30'),
                       quality.replace(b'0,15,30', b'0,65536,30'),
                       quality.replace(b'Lv15', b'Lv16'), quality + b'\n'):
            with self.subTest(sha=growth.digest(source)), self.assertRaises(ValueError):
                growth.parse_auxiliary('NewCombatPet_QualityStar', source)

    def test_raw_bytes_preserve_crcrlf_and_reject_multiline_corruption(self):
        rows = growth.raw_lines(b'1,0\r\r\n2,\r\n3,0')
        self.assertEqual([row['decoded_offset'] for row in rows], [0, 6, 10])
        self.assertEqual(growth.fields(rows[1]), [b'2', b''])
        self.assertEqual(b''.join(bytes.fromhex(r['raw_record_hex']) for r in rows), b'1,0\r\r\n2,\r\n3,0')
        for raw in (b'', b'a\0b\n', b'a\n\nb\n'):
            with self.assertRaises(ValueError):
                growth.raw_lines(raw)

    def test_changed_current_source_rejected_before_extraction(self):
        actual = growth.read_source

        def changed(root, path):
            raw = actual(root, path)
            return raw[:-1] + bytes((raw[-1] ^ 1,))

        with patch.object(growth, 'read_source', side_effect=changed):
            with self.assertRaisesRegex(ValueError, 'Unqualified current source'):
                growth.build_growth(CLIENT)

    def test_native_refuses_changed_table_before_execution(self):
        for name in ('gamedata', 'NewCombatPet_Category', 'NewCombatPet_QualityStar'):
            altered = dict(self.decoded)
            altered[name] += b'\n'
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, 'Unqualified native row source'):
                growth.verify_native_rows(IMAGE, altered)

    def test_native_refuses_changed_image(self):
        with patch.object(growth, 'read_source', return_value=b'unqualified-image'):
            with self.assertRaisesRegex(ValueError, 'Unqualified current native image'):
                growth.verify_native_rows(IMAGE, self.decoded)

    def test_deterministic_serialization_and_independent_unknown_objects(self):
        encoded = growth.serialize(self.result)
        self.assertEqual(growth.serialize(growth.build_growth(CLIENT)), encoded)
        self.assertEqual(growth.serialize(json.loads(encoded)), encoded)
        mutated = copy.deepcopy(self.result)
        mutated['unknown_contracts']['deity']['base_value']['value'] = 0
        self.assertIsNone(mutated['unknown_contracts']['battle_pet']['base_value']['value'])
        self.assertNotEqual(growth.serialize(mutated), encoded)

    def test_cli_summary_needs_only_client_root_and_writes_no_artifact(self):
        result = subprocess.run([sys.executable, '-B', '-m', 'tools.strike_lab.recover_companion_growth',
                                 '--client-root', str(CLIENT), '--summary'], cwd=ROOT,
                                capture_output=True, text=True, timeout=30, check=True)
        value = json.loads(result.stdout)
        self.assertEqual(value['sha256'], growth.digest(growth.serialize(self.result)))
        self.assertEqual(value['sources'], 7)
        self.assertEqual(value['native_verification']['status'], 'not_run')

    def test_cli_rejects_output_into_current_client_before_any_write(self):
        result = subprocess.run([sys.executable, '-B', '-m', 'tools.strike_lab.recover_companion_growth',
                                 '--client-root', str(CLIENT), '--output', str(CLIENT / 'blocked.json')],
                                cwd=ROOT, capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 2)
        self.assertIn('must not overwrite', result.stderr)
        self.assertFalse((CLIENT / 'blocked.json').exists())


class CurrentGrowthNativeTests(unittest.TestCase):
    def test_all_current_rows_execute_with_bounded_writes_and_no_formula_claim(self):
        result = growth.build_growth(CLIENT, IMAGE)
        native = result['native_verification']
        self.assertEqual(native['status'], 'verified_bounded_original_row_execution')
        self.assertEqual(native['image_sha256'], growth.IMAGE_SHA)
        self.assertEqual(native['GodLevel']['rows'], 4)
        self.assertEqual(native['CategoryDetailNum']['rows'], 464)
        self.assertEqual(native['CategoryDetailNum']['unconsumed_columns'], [9, 10, 11])
        self.assertEqual(native['quality_star']['QualityValue']['word_count'], 16)
        self.assertEqual(native['quality_star']['StarValue']['word_count'], 16)
        self.assertFalse(native['growth_formula_verified'])
        self.assertFalse(native['gameplay_runtime_verified'])
        self.assertEqual(result['unknown_contracts'], growth.unknown_contracts())
        image = IMAGE.read_bytes()
        for interval in native['code_ranges'].values():
            self.assertEqual(interval['sha256'], growth.digest(
                image[interval['start_rva']:interval['stop_rva_exclusive']]))
        for binding in native['static_dispatch_bindings'].values():
            self.assertFalse(binding['dispatch_executed'])
        self.assertEqual(native['adapter']['sha256'], growth.digest(
            (ROOT / native['adapter']['path']).read_bytes()))


if __name__ == '__main__':
    unittest.main()
