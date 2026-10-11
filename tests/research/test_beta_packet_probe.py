import unittest

from tools.strike_lab.beta_packet_probe import run


class BetaPacketProbeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = run()

    def test_all_byte_opcodes_execute_length_function(self):
        self.assertEqual(self.report['length_evaluations'], 256)

    def test_beta_dispatch_is_not_current_dispatch(self):
        rows = {row['opcode']: row for row in self.report['battle_dispatch']}
        self.assertEqual(len(rows), 14)
        self.assertEqual(rows['0x19']['length_function_result'], 29)
        self.assertEqual(rows['0x80']['length_function_result'], 17)
        self.assertEqual(rows['0x83']['length_function_result'], 13)

    def test_two_receivers_all_28_positions(self):
        cases = self.report['scalar_cases']
        self.assertEqual(len(cases), 56)
        self.assertTrue(all(case['passed'] for case in cases))
        self.assertTrue(all(case['before'] == case['after'] for case in cases if case['slot'] >= 14))
