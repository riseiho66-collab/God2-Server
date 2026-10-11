import unittest
from tools.strike_lab.beta_resource_writers import run


class ResourceWriterTests(unittest.TestCase):
    def test_original_copy_and_conditional_clamp(self):
        report = run()
        self.assertEqual(len(report['sync_cases']), 12)
        self.assertEqual(len(report['clamp_cases']), 40)

    def test_stat_packet_all_fifteen_fields(self):
        packet = run()['stat_packet']
        self.assertEqual(packet['opcode'], '29')
        self.assertEqual(packet['logical_length'], 31)
        self.assertEqual(len(packet['fields']), 15)
        for case in packet['cases']:
            self.assertEqual(case['input'], case['observed'])
