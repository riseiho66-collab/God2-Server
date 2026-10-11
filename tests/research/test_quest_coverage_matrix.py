"""Source completeness, real native coverage, deterministic report and boundaries.

Generate the matrix artifact with its CLI first. This file independently reruns
the complete native matrix once and compares it with that artifact.
"""
from collections import Counter
import copy
import hashlib
import io
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.strike_lab import quest_coverage_matrix as matrix

ARTIFACT = ROOT / 'artifacts/research/quest-coverage-matrix-20260920.json'


class QuestCoverageMatrixTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for target in ('subprocess.Popen', 'socket.socket', 'sqlite3.connect'):
            guard = patch(target, side_effect=AssertionError('Offline matrix only'))
            guard.start()
            cls.addClassCleanup(guard.stop)
        cls.evidence = matrix.scenarios.Evidence()
        cls.artifact_bytes = ARTIFACT.read_bytes()
        cls.report = json.loads(cls.artifact_bytes)

    def test_source_denominators_and_exact_original_rows(self):
        evidence = self.evidence
        self.assertEqual(len(evidence.missions), 418)
        self.assertEqual(sum(map(len, evidence.texts)), 2014)
        self.assertEqual({name: len(table['records'])
                          for name, table in evidence.catalog['tables'].items()},
                         dict(missions=2432, requirements=169, daily=85))
        manifest = matrix.source_manifest(evidence)
        lines = []
        for mission, checked in zip(evidence.missions, manifest):
            self.assertEqual(checked['id'], mission['id'])
            self.assertEqual(checked['source_line'], mission['source_line'])
            self.assertEqual(len(checked['steps']), mission['step_field'])
            for objective, step in zip(mission['objectives_text'], checked['steps']):
                row = evidence.rows[objective['source_line']]
                raw = bytes.fromhex(row['raw_fields_hex'][3])
                self.assertEqual((step['step'], step['source_line']),
                                 (objective['step'], objective['source_line']))
                self.assertEqual(step['source_record_sha256'], row['source_record_sha256'])
                self.assertEqual(step['text_sha256'], hashlib.sha256(raw).hexdigest())
                self.assertEqual(step['text_bytes'], len(raw))
                lines.append(step['source_line'])
        self.assertEqual(len(lines), len(set(lines)))
        source = evidence.catalog['tables']['missions']['records']
        description_lines = {r['source_line'] for r in source if not r['raw_fields_hex'][0]}
        self.assertEqual(set(lines), description_lines)

    def test_case_enumeration_has_no_omissions_or_duplicates(self):
        observed = list(matrix.cases(self.evidence))
        expected = {(m['id'], o['step'], subtype, slot)
                    for m in self.evidence.missions for o in m['objectives_text']
                    for subtype in (4, 5) for slot in range(15)}
        self.assertEqual(len(observed), 60420)
        self.assertEqual(len(set(observed)), len(observed))
        self.assertEqual(set(observed), expected)
        counts = Counter((subtype, slot) for _, _, subtype, slot in observed)
        self.assertEqual(counts, {(subtype, slot): 2014
                                 for subtype in (4, 5) for slot in range(15)})

    def test_complete_native_rerun_matches_cli_artifact_byte_for_byte(self):
        actual = matrix.run(self.evidence)
        self.assertEqual(actual['status'], 'PASS', actual['failures'])
        self.assertEqual(actual['failures'], [])
        matrix.audit_coverage(self.evidence, actual['missions'])
        self.assertEqual(matrix.serialize(actual).encode('utf-8'), self.artifact_bytes)
        coverage = actual['coverage']
        self.assertEqual((coverage['cases_attempted'], coverage['cases_passed'],
                          coverage['cases_expected']), (60420, 60420, 60420))
        self.assertEqual(coverage['lifecycle_operations_passed'], 483360)
        self.assertEqual(coverage['source_byte_checks'], 181260)
        self.assertEqual(coverage['clear_blank_checks'], 60420)
        self.assertEqual(actual['execution'], dict(lifecycle_vms=2, boundary_vms=2,
                                                   retained_trace_entries=0))
        self.assertEqual(actual['boundaries']['cases_passed'], 1712)
        self.assertEqual(actual['boundaries']['counts'], dict(invalid_step=836,
            zero_selector_alias=836, invalid_mission=8, invalid_slot=8,
            truncated_record=24, invalid_slot_selection_writes=4))

    def test_audit_rejects_missing_duplicate_or_wrong_source_coverage(self):
        matrix.audit_coverage(self.evidence, self.report['missions'])
        for mutation in ('missing_mission', 'duplicate_mission', 'missing_step',
                         'duplicate_step', 'missing_slot', 'extra_slot', 'wrong_hash'):
            with self.subTest(mutation=mutation):
                altered = copy.deepcopy(self.report['missions'])
                if mutation == 'missing_mission':
                    altered.pop()
                elif mutation == 'duplicate_mission':
                    altered[-1] = copy.deepcopy(altered[0])
                elif mutation == 'missing_step':
                    altered[0]['steps'].pop()
                elif mutation == 'duplicate_step':
                    altered[0]['steps'][1] = copy.deepcopy(altered[0]['steps'][0])
                elif mutation == 'missing_slot':
                    altered[0]['steps'][0]['passed_slot_masks']['4'] &= ~(1 << 7)
                elif mutation == 'extra_slot':
                    altered[0]['steps'][0]['passed_slot_masks']['5'] |= 1 << 15
                else:
                    altered[0]['steps'][0]['text_sha256'] = '0' * 64
                with self.assertRaises(AssertionError):
                    matrix.audit_coverage(self.evidence, altered)

    def test_duplicate_pass_cannot_inflate_ledger(self):
        manifest = matrix.source_manifest(self.evidence)
        matrix.record_pass(manifest, 2, 1, 4, 7)
        before = copy.deepcopy(manifest)
        with self.assertRaisesRegex(AssertionError, 'Duplicate lifecycle'):
            matrix.record_pass(manifest, 2, 1, 4, 7)
        self.assertEqual(manifest, before)
        with self.assertRaisesRegex(AssertionError, 'Incomplete'):
            matrix.audit_coverage(self.evidence, manifest)

    def test_invalid_case_arguments_rejected_before_native_mutation(self):
        with matrix.NativeMatrix(self.evidence, 4) as native:
            before = bytes(native.player.vm.mem_read(matrix.UI_BASE, 0x240000))
            returns = native.native_returns
            for mission, step, slot in ((0, 1, 0), (419, 1, 0), (2, 0, 0),
                    (2, len(self.evidence.texts[1]) + 1, 0), (2, 1, -1),
                    (2, 1, 15), (2, 65536, 0), (True, 1, 0)):
                with self.subTest(mission=mission, step=step, slot=slot):
                    with self.assertRaises(ValueError):
                        native.lifecycle(mission, step, slot)
                    self.assertTrue(bytes(native.player.vm.mem_read(matrix.UI_BASE, 0x240000)) == before)
                    self.assertEqual(native.native_returns, returns)
            for subtype in (3, 6, 0x104, True):
                with self.assertRaises(ValueError):
                    matrix.validate_case(self.evidence, 2, 1, subtype, 0)

    def test_failed_native_case_is_never_counted_as_passed(self):
        # Fault injection tests report accounting, not simulated native success.
        with patch.object(matrix.NativeMatrix, 'lifecycle',
                          side_effect=AssertionError('Injected lifecycle failure')):
            report = matrix.run(self.evidence)
        self.assertEqual(report['status'], 'FAIL')
        self.assertEqual(report['coverage']['cases_attempted'], 1)
        self.assertEqual(report['coverage']['cases_passed'], 0)
        self.assertEqual(report['coverage']['lifecycle_operations_passed'], 0)
        self.assertEqual(report['coverage']['source_byte_checks'], 0)
        self.assertEqual(report['coverage']['clear_blank_checks'], 0)
        self.assertEqual(report['failures'][0]['case'],
                         dict(mission=1, step=1, subtype=4, slot=0))
        self.assertTrue(all(s['cases_passed'] == 0 and s['passed_slot_masks'] == {'4': 0, '5': 0}
                            for m in report['missions'] for s in m['steps']))

    def test_manifest_rejects_corrupt_source_enumeration(self):
        for mutation in ('duplicate_id', 'duplicate_step', 'wrong_count', 'wrong_text'):
            evidence = copy.copy(self.evidence)
            evidence.missions = copy.deepcopy(self.evidence.missions)
            evidence.texts = [list(texts) for texts in self.evidence.texts]
            if mutation == 'duplicate_id':
                evidence.missions[1]['id'] = 1
            elif mutation == 'duplicate_step':
                evidence.missions[0]['objectives_text'][1]['step'] = 1
            elif mutation == 'wrong_count':
                evidence.missions[0]['step_field'] += 1
            else:
                evidence.texts[0][0] += b'changed'
            with self.subTest(mutation=mutation), self.assertRaises(AssertionError):
                matrix.source_manifest(evidence)

    def test_report_keeps_other_tables_and_gameplay_authority_unknown(self):
        for name, table in self.evidence.catalog['tables'].items():
            reported = self.report['source_tables'][name]
            self.assertEqual(reported['actual_source_records'], len(table['records']))
            for key in ('source_file', 'source_sha256', 'decoded_sha256', 'declared_records'):
                self.assertEqual(reported[key], table[key])
            self.assertEqual(reported['gameplay_runtime_coverage'], 'UNKNOWN')
            self.assertEqual(reported['cross_table_join_authority'], 'UNKNOWN')
            if name != 'missions':
                self.assertIn('runtime coverage UNKNOWN', reported['coverage_scope'])
        self.assertEqual(self.report['unknown_authority'], list(matrix.scenarios.UNKNOWN_RULES))
        self.assertTrue(all(m['main_side_classification'] == 'UNKNOWN'
                            for m in self.report['missions']))
        self.assertEqual(self.report['qualification'], 'OFFLINE_ORIGINAL_NATIVE_TEXT_SCENARIOS_ONLY')

    def test_cli_refuses_output_inside_client_before_running_matrix(self):
        output = ROOT.parent / 'God2' / 'forbidden-matrix.json'
        with patch.object(matrix, 'run') as run, patch('sys.stderr', new=io.StringIO()):
            with self.assertRaises(SystemExit) as error:
                matrix.main(['--output', str(output)])
        self.assertEqual(error.exception.code, 2)
        run.assert_not_called()


if __name__ == '__main__':
    unittest.main()
