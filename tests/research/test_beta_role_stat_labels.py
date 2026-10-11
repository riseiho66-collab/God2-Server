import unittest
from tools.strike_lab.beta_role_stat_labels import audit


class BetaRoleLabelsTest(unittest.TestCase):
    def test_native_packet_to_original_status_labels(self):
        report = audit()
        fields = {f['name']: f for f in report['fields']}
        self.assertEqual(fields['physical_attack']['logical_offset'], '0x19')
        self.assertEqual(fields['physical_defense']['logical_offset'], '0x17')
        self.assertEqual(fields['magic_attack']['logical_offset'], '0x1d')
        self.assertEqual(fields['magic_defense']['logical_offset'], '0x1b')
        self.assertEqual(len(report['native_cases']), 4)
