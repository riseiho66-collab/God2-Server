"""Stateful player journal scenarios against the pinned original instructions."""
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.strike_lab import quest_player_scenarios as scenarios


class QuestPlayerScenariosTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        guard = patch('subprocess.Popen', side_effect=AssertionError('No child processes allowed'))
        guard.start()
        cls.addClassCleanup(guard.stop)
        cls.evidence = scenarios.Evidence()

    def test_actual_source_entries_and_no_inferred_side_class(self):
        evidence = self.evidence
        self.assertEqual((len(evidence.missions), sum(map(len, evidence.texts))), (418, 2014))
        self.assertEqual([evidence.source(i)['source_line'] for i in (1, 165, 418)], [4, 1071, 2427])
        self.assertEqual([len(evidence.texts[i - 1]) for i in (1, 165, 418)], [2, 29, 8])
        self.assertTrue(evidence.source(418)['name'].startswith('[\u4e3b\u7dda\u4efb\u52d9]'))
        self.assertTrue(all('\u652f\u7dda' not in m['name'] for m in evidence.missions))
        for mission_id in (1, 165, 418):
            source = evidence.source(mission_id)
            self.assertEqual(source['main_side_classification'], 'UNKNOWN')
            self.assertEqual(bytes.fromhex(source['name_hex']).decode('cp950'), source['name'])

    def test_db4_receive_page_select_replay_clear(self):
        result = scenarios.lifecycle(self.evidence, 4)
        duplicates = [r for r in result['trace'] if r['action'] in ('duplicate', 'replay')]
        self.assertEqual([r['state']['refresh_calls'] for r in duplicates], [1, 2])
        cleared = [r for r in result['trace'] if r['action'] == 'clear']
        self.assertEqual([r['state']['pages'] for r in cleared], [2, 1, 1])
        self.assertEqual([r['state']['selected'] for r in cleared], [0x801a2] * 3)

    def test_db5_receive_page_select_replay_clear(self):
        result = scenarios.lifecycle(self.evidence, 5)
        duplicates = [r for r in result['trace'] if r['action'] in ('duplicate', 'replay')]
        self.assertEqual([r['state']['refresh_calls'] for r in duplicates], [4, 5])
        cleared = [r for r in result['trace'] if r['action'] == 'clear']
        self.assertEqual([r['state']['selected'] for r in cleared], [0, 0, 0])

    def test_db4_invalid_bounds_preserve_populated_state(self):
        scenarios.bounds(self.evidence, 4)

    def test_db5_invalid_bounds_include_preassertion_selection_write(self):
        scenarios.bounds(self.evidence, 5)

    def test_zero_and_one_alias_text_without_aliasing_stored_values(self):
        with scenarios.Player(self.evidence) as player:
            results = []
            for value in (1, 0x10001):
                player.receive(5, 4, value)
                results.append(player.describe(5, click=True))
            self.assertEqual(results[0]['text_hex'], results[1]['text_hex'])
            self.assertEqual([r['source_line'] for r in results], [5, 5])
            self.assertEqual([r['state']['selected'] for r in results], [1, 0x10001])

    def test_identity_mismatch_fails_before_emulation(self):
        with patch.object(Path, 'read_bytes', return_value=b'wrong image'):
            with self.assertRaisesRegex(AssertionError, 'Pinned native image changed'):
                scenarios.Evidence()


if __name__ == '__main__':
    unittest.main()
