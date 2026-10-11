import unittest

from tools.strike_lab.beta_skill_amount_probe import AmountProbe, run


class BetaSkillAmountTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = run()

    def test_all_beta_definitions_and_amount_boundaries(self):
        self.assertEqual(self.report['skill_definitions'], 333)
        self.assertEqual(self.report['passed'], 3330)
        self.assertTrue(all(x['logical_marker_word'] == x['stored_word'] for x in self.report['cases']))

    def test_both_sides_and_signed_boundary(self):
        rows = self.report['cases']
        self.assertEqual({x['side'] for x in rows}, {0, 1})
        self.assertTrue(all(x['signed_interpretation'] == -32768 for x in rows if x['stored_word'] == 32768))

    def test_native_attack_defense_gates_do_not_scale_amount(self):
        gates = self.report['formatter_gate_cases']
        self.assertEqual(len(gates), 60)
        for row in gates:
            self.assertEqual(len(row['calls']), int(row['gate'] != 0))
            for call in row['calls']:
                self.assertEqual(call['amount'], row['input_amount'])

    def test_reject_out_of_bounds_markers(self):
        probe = AmountProbe()
        for value in (-1, 65536):
            with self.assertRaises(ValueError):
                probe.evaluate((0, 1), value)

    def test_mp_gate_all_skills_both_native_entry_points(self):
        rows = self.report['mp_gate_cases']
        self.assertEqual(len({(x['bank'], x['id']) for x in rows}), 333)
        self.assertEqual({x['mode'] for x in rows}, {'selected', 'indexed'})
        for row in rows:
            self.assertEqual(row['allowed'], int(row['record_67'] != 0 and row['mp'] >= row['displayed_cost']))
