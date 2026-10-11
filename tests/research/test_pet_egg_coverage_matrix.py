"""Whole-source denominators, native matrix outcomes and evidence defects."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.strike_lab import pet_egg_coverage_matrix as matrix

ARTIFACT = ROOT / 'artifacts/research/pet-egg-coverage-matrix-20260920.json'
GROUP_COUNTS = {
    'ItemType': 46, 'GOD': 34, 'PET': 147, 'COM': 2070, 'NCP': 1165,
    'GodLevel': 4, 'FightPetSkill': 254, 'NewFightPet2Skill': 255, 'CategoryNum': 16,
    'NewCombatPet_Category': 464, 'NewCombatPet_AllInnate': 144,
    'NewCombatPet_Innate': 41, 'PetDesignDesc': 381, 'NewCombatPet_QualityStar': 2,
}
PHYSICAL_COUNTS = {'gamedata': 29672, 'message': 3106, 'NewCombatPet_Category': 469,
                   'NewCombatPet_QualityStar': 7, 'NewCombatPet_AllInnate': 149,
                   'NewCombatPet_Innate': 45, 'PetDesignDesc': 386}


class PetEggCoverageMatrixTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.decoded, cls.evidence, cls.eggs, cls.definitions = matrix.inputs(matrix.DEFAULT_CLIENT)
        cls.report = json.loads(ARTIFACT.read_bytes())

    def validate(self, report):
        matrix.validate_report(report, self.decoded, self.evidence, self.eggs, self.definitions)

    def test_complete_current_sources_have_exact_offsets_hashes_and_denominators(self):
        self.validate(self.report)
        inventory = self.report['source_inventory']
        self.assertEqual(inventory['physical_rows'], 33834)
        self.assertEqual(inventory['growth_rows'], 5023)
        self.assertEqual(inventory['selected_text_rows'], 17)
        self.assertEqual({k: len(v['lines']) for k, v in inventory['growth_groups'].items()}, GROUP_COUNTS)
        self.assertEqual({k: v['physical_row_count'] for k, v in inventory['files'].items()}, PHYSICAL_COUNTS)
        for name, file in inventory['files'].items():
            offset = 0
            for line, row in enumerate(file['rows'], 1):
                self.assertEqual(row['line'], line)
                self.assertEqual(row['offset'], offset)
                raw = self.decoded[name][offset:offset + row['length']]
                self.assertEqual(matrix.growth.digest(raw), row['sha256'])
                offset += row['length']
            self.assertEqual(offset, len(self.decoded[name]))
        for group in inventory['growth_groups'].values():
            self.assertEqual(len(group['lines']), len(set(group['lines'])))
        # Preserve the actual inconsistent declaration; never invent five rows.
        category = inventory['growth_groups']['NewCombatPet_Category']
        self.assertEqual(category['declared_count'], 469)
        self.assertEqual(len(category['lines']), 464)

    def test_all_egg_definitions_are_joined_by_exact_source_not_id_arithmetic(self):
        rows = self.report['egg_guard']['entries']
        expected = [(tag, r['source_line']) for tag, section in
                    matrix.growth.parse_sections(self.decoded['gamedata'], ('EGG', 'SPP')).items()
                    for r in section['records']]
        self.assertEqual([(r['section'], r['source']['source_line']) for r in rows], expected)
        self.assertEqual(len(rows), 55)
        self.assertEqual(len({r['source_key'] for r in rows}), 55)
        self.assertEqual(self.report['counts']['egg_sections'], {'EGG': 27, 'SPP': 28})
        self.assertEqual(self.report['egg_guard']['definition_denominator'], 16127)
        self.assertEqual(self.report['egg_guard']['unjoined'], [])
        for row in rows:
            join = row['join']
            self.assertEqual(join['status'], 'source_qualified')
            self.assertFalse(join['native_metadata_loader_verified'])
            self.assertEqual(join['definition']['raw_fields_hex'], row['source']['fields_hex'])
            self.assertEqual(join['definition']['source_line'], row['source']['source_line'])
            self.assertEqual(len(row['guard_cases']), 256)
            self.assertEqual(sum(c['kind'] == 'return' for c in row['guard_cases']), 31)
            self.assertEqual(sum(c['kind'] == 'assert' for c in row['guard_cases']), 225)
            self.assertEqual([c['value'] for c in row['presence_transition']], [0x58b, 1])
        keys = {r['source_key'] for r in rows}
        self.assertIn(9426, keys)
        self.assertNotIn(9326, keys)

    def test_missing_ambiguous_or_damaged_definition_never_gets_fake_pointer(self):
        entry = self.eggs[0]
        key = entry['source_key']
        definition = next(d for d in self.definitions if d['client_item_id'] == key)
        damaged = copy.deepcopy(definition)
        damaged['raw_fields_hex'][4] = '00'
        for definitions, reason in (([], 'missing'), ([definition, definition], 'ambiguous'),
                                     ([damaged], 'source_mismatch')):
            with self.subTest(reason=reason):
                join = matrix.join_definition(entry, definitions)
                self.assertEqual((join['status'], join['reason']), ('unjoined', reason))
                native = matrix.EggGuard([entry], [join])
                self.assertEqual(native.pointers, {})
                self.assertEqual(native.run(45, key), matrix.expected_guard(45, key, False))

    def test_all_slots_dispatches_aux_states_patterns_and_rejections(self):
        report = self.report['instance']
        self.assertEqual(len(report['patterns']), 36)
        self.assertEqual(len(set(report['patterns'])), 36)
        self.assertTrue(set(1 << bit for bit in range(32)) <= set(report['patterns']))
        cases = report['cases']
        coordinates = [(r['slot'], r['dispatch'], r['auxiliary'], r['packed']) for r in cases]
        self.assertEqual(len(coordinates), len(set(coordinates)))
        self.assertEqual(len(cases), 8024)
        self.assertEqual(len(report['per_slot']), 256)
        for row in report['per_slot']:
            s = row['slot']
            self.assertEqual(row['cases'], 144 if s < 50 else 4)
            self.assertEqual(row['intercepted'], 72 if 38 <= s <= 41 else 0)
            self.assertEqual(row['rejected'], 4 if s >= 50 else 0)
            self.assertEqual(row['ui_copied'], 144 if s < 30 or s in (42, 43) else 0)
        self.assertEqual(self.report['counts']['instance_in_store_cases'], 7200)
        self.assertEqual(self.report['counts']['instance_rejection_cases'], 824)
        self.assertEqual(self.report['counts']['instance_interceptions'], 288)
        self.assertEqual(self.report['counts']['instance_copies'], 6912)
        self.assertEqual(self.report['counts']['native_growth_rows'], 470)
        self.assertEqual(self.report['counts']['ui_copies'], 4608)
        self.assertEqual(self.report['counts']['ui_blocked_stale'], 2304)
        self.assertTrue(all(c['packet_stale_ui_preserved'] for c in cases))
        self.assertEqual(len(report['entry_gates']), 212)

    def test_every_quality_star_pair_mode_and_noise_has_real_table_provenance(self):
        cases = self.report['display']['cases']
        self.assertEqual(len(cases), 1024)
        for mode in (1, 256):
            for noise in (0, 0xff00ffff):
                rows = [c for c in cases if c['mode'] == mode and c['packed'] & 0xff00ffff == noise]
                self.assertEqual(len(rows), 256)
                self.assertEqual({(r['quality'][0], r['star'][0]) for r in rows},
                                 {(q, s) for q in range(16) for s in range(16)})
                self.assertTrue(all(len(r['table_reads']) == 2 for r in rows))
        self.assertEqual(self.report['display']['source_lines'], [5, 7])

    def test_native_rows_and_zero_display_values_do_not_authorize_rules(self):
        native = self.report['native_growth_rows']
        self.assertEqual(native['status'], 'verified_bounded_original_row_execution')
        self.assertEqual(native['GodLevel']['rows'], 4)
        self.assertEqual(native['CategoryDetailNum']['rows'], 464)
        self.assertEqual(native['quality_star']['QualityValue']['word_count'], 16)
        self.assertEqual(native['quality_star']['StarValue']['word_count'], 16)
        self.assertFalse(native['growth_formula_verified'])
        self.assertFalse(native['gameplay_runtime_verified'])
        self.assertEqual(self.report['unknown_rules'], dict.fromkeys(matrix.UNKNOWN))
        self.assertEqual(self.report['display']['cases'][0]['quality'], [0, 0])
        for row in self.report['egg_guard']['entries']:
            self.assertTrue(all(v is None for v in row['unknown'].values()))
            self.assertFalse(row['runtime_eligible'])

    def test_source_and_join_omission_duplicate_and_corruption_defects_are_caught(self):
        def omit_growth(r):
            r['source_inventory']['growth_groups']['NCP']['lines'].pop()
            r['source_inventory']['growth_rows'] -= 1
            r['counts']['growth_rows'] -= 1

        def duplicate_source(r):
            rows = r['source_inventory']['files']['message']['rows']
            rows[-1] = copy.deepcopy(rows[-2])

        def duplicate_egg(r):
            r['egg_guard']['entries'][-1] = copy.deepcopy(r['egg_guard']['entries'][0])

        def wrong_join(r):
            r['egg_guard']['entries'][0]['join']['definition']['raw_fields_hex'][0] = '30'

        for defect in (omit_growth, duplicate_source, duplicate_egg, wrong_join):
            with self.subTest(defect=defect.__name__):
                changed = copy.deepcopy(self.report)
                defect(changed)
                with self.assertRaises(ValueError):
                    self.validate(changed)

    def test_outcome_stale_display_coverage_and_default_defects_are_caught(self):
        def invalid_success(r):
            c = next(c for c in r['instance']['cases'] if c['slot'] == 255)
            c['copied'], c['stop_rva'] = True, 0x98e2d

        def stale_changed(r):
            c = next(c for c in r['instance']['cases'] if c['ui'] and not c['ui']['copied'])
            c['ui']['stale_preserved'] = False

        def duplicate_display(r):
            r['display']['cases'][-1] = copy.deepcopy(r['display']['cases'][0])

        def wrong_table_value(r):
            r['display']['cases'][0]['quality'][1] = 15

        def invented_timer(r):
            r['unknown_rules']['incubation_timer'] = 20 * 3600

        def invented_probability(r):
            r['egg_guard']['entries'][0]['unknown']['success_probability'] = 0

        def invented_native_rule(r):
            r['native_growth_rows']['growth_formula_verified'] = True

        for defect in (invalid_success, stale_changed, duplicate_display, wrong_table_value,
                       invented_timer, invented_probability, invented_native_rule):
            with self.subTest(defect=defect.__name__):
                changed = copy.deepcopy(self.report)
                defect(changed)
                with self.assertRaises(ValueError):
                    self.validate(changed)

    def test_fast_matrix_runner_keeps_native_boundaries_and_write_guards(self):
        image = matrix.instance.qualified_image(matrix.DEFAULT_IMAGE)
        native = matrix.MatrixInstance(image)
        native.prepare()
        with self.assertRaisesRegex(AssertionError, 'Unexpected native instruction'):
            native.run(0x98e05, (0x98e0a,), ('slot_guard_and_store',))
        native.prepare()
        native.reg('ECX', native.UI)
        with self.assertRaisesRegex(AssertionError, 'Out-of-bound native write'):
            native.run(0x869e0, (0x86a04,), ('ui_reset',))
        native.deadline = 0
        with self.assertRaisesRegex(ValueError, 'deadline'):
            native.packet_store(0, matrix.instance.record_for(0))
        altered = image[:-1] + bytes((image[-1] ^ 1,))
        with self.assertRaisesRegex(ValueError, 'native image'):
            matrix.MatrixInstance(altered)

    def test_cli_reexecutes_full_native_matrix_and_matches_artifact_bytes(self):
        result = subprocess.run([sys.executable, '-B', '-m', 'tools.strike_lab.pet_egg_coverage_matrix',
                                 '--output', str(ARTIFACT), '--check'], cwd=ROOT,
                                capture_output=True, text=True, timeout=300)
        self.assertEqual(result.returncode, 0, result.stderr)
        summary = json.loads(result.stdout)
        self.assertTrue(summary['checked'])
        self.assertEqual(summary['counts'], self.report['counts'])
        self.assertEqual(summary['sha256'], matrix.growth.digest(ARTIFACT.read_bytes()))
        self.assertEqual(summary['bytes'], ARTIFACT.stat().st_size)


if __name__ == '__main__':
    unittest.main()
