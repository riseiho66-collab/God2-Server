from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/strike_lab'))
import post6b_event_proof as proof


class Post6BEventProofTests(unittest.TestCase):
    def test_pinned_sources_and_bytes(self):
        self.assertEqual(proof.source_gate()['status'], 'PASS')
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / proof.IMAGE
            target.parent.mkdir(parents=True)
            target.write_bytes(b'changed source')
            with self.assertRaisesRegex(ValueError, 'SHA256 mismatch'):
                proof.source_gate(directory)
        with patch.dict(proof.PINNED_BYTES, {0x12506: '90'}):
            with self.assertRaisesRegex(ValueError, 'instruction bytes mismatch'):
                proof.source_gate()

    def test_algebra_has_no_solver_claims_and_no_global_closure(self):
        result = proof.run_proof(backend='finite-algebra')
        self.assertEqual(result['query'], 'Q_POST6B_DIRECTION')
        self.assertEqual(result['method'], 'EVENT_FIRST_WP')
        for event in ('client_first', 'server_first', 'connection_transition', 'local_transition'):
            self.assertEqual(result[event], 'UNKNOWN')
        self.assertIsNone(result['must_direction'])
        self.assertIsNone(result['minimal_discriminant'])
        self.assertEqual(result['concrete_unknowns_recovered'], 0)
        self.assertFalse(result['proof_complete'])
        self.assertEqual(result['local_state_change']['predicate'], 'queued_prior != 0')
        self.assertEqual(result['prior_Q_evidence'], 'NONE')
        self.assertEqual(result['proof']['checks'], [])
        self.assertFalse(result['proof']['solver_executed'])
        self.assertFalse(result['four_event_full_proof'])
        self.assertFalse(result['global_unsat'])
        self.assertFalse(result['H0_recovered'])
        self.assertEqual(len(result['full_scope_events']), 4)
        self.assertTrue(all(e['status'] == 'UNKNOWN' for e in result['full_scope_events'].values()))
        self.assertEqual({b['kind'] for b in result['unmodeled_boundaries']},
                         {'UNMODELED_CALL', 'UNMODELED_CALLER'})

    def test_actual_z3_queries_export_and_cores_replay(self):
        z3, _ = proof._load_z3(ROOT)
        if z3 is None:
            self.skipTest('Z3 not locally available; no solver claim made')
        result = proof.run_proof(backend='z3')
        self.assertTrue(result['proof']['verified'])
        checks = {c['name']: c for c in result['proof']['checks']}
        self.assertEqual(checks['conditional_change_witness']['result'], 'SAT')
        self.assertNotEqual(checks['conditional_change_witness']['witness']['queued_prior'], 0)
        self.assertEqual(checks['conditional_iff_counterexample']['result'], 'UNSAT')
        for name in ('zero_prior_unmodeled_call', 'zero_prior_unmodeled_caller'):
            self.assertEqual(checks[name]['result'], 'SAT')
            self.assertEqual(checks[name]['witness']['queued_prior'], 0)
        for check in checks.values():
            with self.subTest(query=check['name']):
                replay = z3.Solver()
                replay.from_string(check['smtlib'])
                self.assertEqual(str(replay.check()).upper(), check['result'])
                if check['result'] == 'UNSAT':
                    self.assertTrue(check['unsat_core'])
                    core = z3.Solver()
                    declarations = '\n'.join(
                        '(declare-fun ' + name + ' () (_ BitVec 32))'
                        for name in ('H0', 'queued_prior', 'ECX_after_read', 'Q_after_store'))
                    assertions = '\n'.join('(assert ' + check['tracked_constraints'][label] + ')'
                                           for label in check['unsat_core'])
                    core.from_string(declarations + '\n' + assertions)
                    self.assertEqual(core.check(), z3.unsat)

    def test_unavailable_backend_and_unknown_are_not_promoted(self):
        with patch.object(proof, '_load_z3', return_value=(None, 'not installed')):
            self.assertEqual(proof.run_proof()['proof']['backend'], 'FINITE_ALGEBRA')
            with self.assertRaises(RuntimeError):
                proof.run_proof(backend='z3')
        with patch.object(proof, '_load_z3', return_value=(object(), None)), \
                patch.object(proof, '_solver_checks', return_value={'verified': False}):
            self.assertEqual(proof.run_proof()['verdict'], 'UNKNOWN')


if __name__ == '__main__':
    unittest.main()
