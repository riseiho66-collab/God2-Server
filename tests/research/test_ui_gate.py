import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[2]/'tools/strike_lab'))
from ui_gate import REQUIRED_TRUE, Rendezvous, atomic_json, preflight, readiness


def health():
    return dict.fromkeys(REQUIRED_TRUE, True) | {
        'pid': 123, 'server_count': 1, 'selected_entry_id': 0}


def waiting(max_wait=None):
    gate = Rendezvous('test', max_wait)
    gate.refresh(health(), 0)
    for state in ('REPLAY_GOLDEN_PREFIX', 'SERVER_AUTO_SELECTED',
                  'ARM_POST_GATE_OBSERVERS', 'UI_GATE_READY', 'WAIT_EXTERNAL_UI'):
        gate.transition(state, 0)
    return gate


class UiGateTests(unittest.TestCase):
    def test_every_prerequisite_required(self):
        self.assertEqual(readiness(health()), [])
        for key in health():
            with self.subTest(key=key):
                missing = health()
                del missing[key]
                self.assertIn(key, readiness(missing))

    def test_selected_zero_not_false(self):
        for value in (None, False, '0', 1):
            h = health() | {'selected_entry_id': value}
            self.assertIn('selected_entry_id', readiness(h))

    def test_default_wait_unbounded(self):
        gate = waiting()
        gate.refresh(health(), 10**12)
        self.assertEqual(gate.state, 'WAIT_EXTERNAL_UI')
        self.assertTrue(gate.snapshot()['ui_gate_ready'])

    def test_operator_limit(self):
        gate = waiting(5)
        gate.refresh(health(), 5)
        self.assertEqual(gate.termination_reason, 'OPERATOR_MAX_WAIT')

    def test_bad_limits(self):
        for value in (0, -1, float('nan'), float('inf')):
            with self.assertRaises(ValueError):
                Rendezvous('test', value)

    def test_health_loss_clears_readiness(self):
        for key, reason in (('client_alive', 'CLIENT_EXIT'),
                            ('server_alive', 'SERVER_EXIT'),
                            ('socket_alive', 'UI_GATE_SESSION_EXPIRED'),
                            ('observer_alive', 'FATAL_OBSERVER_FAILURE')):
            gate = waiting()
            gate.refresh(health() | {key: False}, 1)
            self.assertFalse(gate.snapshot()['ui_gate_ready'])
            self.assertEqual(gate.termination_reason, reason)

    def test_callback_not_success(self):
        gate = waiting()
        self.assertTrue(gate.observe({'run_id': 'test', 'pid': 123,
                                     'runtime_verified': True, 'kind': 'UI_PATH_A_HIT'}, 1))
        self.assertEqual(gate.state, 'WAIT_EXTERNAL_UI')

    def test_event_resumes_same_run(self):
        gate = waiting()
        self.assertTrue(gate.observe({'run_id': 'test', 'pid': 123,
                                     'runtime_verified': True, 'kind': 'NEW_CONNECT'}, 2))
        self.assertEqual(gate.state, 'POST_GATE_EVENT')
        self.assertEqual(gate.events[0]['observed_monotonic'], 2)
        self.assertFalse(gate.snapshot()['ui_gate_ready'])

    def test_wrong_identity_and_click_not_evidence(self):
        gate = waiting()
        valid = {'run_id': 'test', 'pid': 123, 'runtime_verified': True, 'kind': 'NEW_CONNECT'}
        for delta in ({'run_id': 'old'}, {'pid': 999}, {'runtime_verified': False},
                      {'kind': 'UI_ACTION_COMPLETED'}):
            self.assertFalse(gate.observe(valid | delta, 1))
        self.assertEqual(gate.events, [])

    def test_no_implicit_transitions(self):
        gate = Rendezvous('test')
        with self.assertRaises(ValueError):
            gate.transition('WAIT_EXTERNAL_UI', 0)
        gate = waiting()
        with self.assertRaises(ValueError):
            gate.transition('POST_GATE_EVENT', 0)

    def test_cleanup_only_owned_objects(self):
        owned, unrelated = Mock(), Mock()
        owned.poll.return_value = None
        gate = waiting()
        gate.owned_processes.append(owned)
        gate.cancel()
        self.assertEqual(gate.cleanup_owned(), [])
        owned.terminate.assert_called_once()
        unrelated.terminate.assert_not_called()

    def test_atomic_output_does_not_write_protocol_truth(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            truth = root/'state.json'
            truth.write_bytes(b'unchanged')
            output = root/'ui_gate.json'
            gate = waiting()
            atomic_json(output, gate.snapshot())
            gate.cancel()
            atomic_json(output, gate.snapshot())
            self.assertFalse(json.loads(output.read_text())['ui_gate_ready'])
            self.assertEqual(truth.read_bytes(), b'unchanged')
            self.assertEqual(sorted(p.name for p in root.iterdir()), ['state.json', 'ui_gate.json'])

    def test_missing_adapter_cannot_pass_dry_check(self):
        with tempfile.TemporaryDirectory() as directory:
            report = preflight(directory, directory)
            self.assertFalse(report['ui_gate_ready'])
            self.assertFalse(report['client_launched'])
            self.assertIn('long_lived_adapter', report['blockers'])

    def test_character_observer_is_not_required(self):
        self.assertEqual(readiness(health()), [])
        self.assertFalse(any('character' in key for key in REQUIRED_TRUE))

    def test_operator_cancel(self):
        gate = waiting()
        gate.cancel()
        self.assertEqual(gate.state, 'CLEANUP')
        self.assertFalse(gate.snapshot()['ui_gate_ready'])

    def test_send_resumes(self):
        gate = waiting()
        self.assertTrue(gate.observe({'run_id':'test','pid':123,
                                     'runtime_verified':True,'kind':'NEW_CLIENT_TX'}, 2))
        self.assertEqual(gate.state, 'POST_GATE_EVENT')


if __name__ == '__main__':
    unittest.main()
