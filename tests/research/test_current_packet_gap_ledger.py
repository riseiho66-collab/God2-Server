"""Guard the packet inventory against direction and coverage inflation."""

import unittest

from tools.strike_lab import current_packet_gap_ledger as ledger


class CurrentPacketGapLedgerTests(unittest.TestCase):
    def test_native_receive_table_is_not_world_parser_coverage(self):
        report = ledger.build_report()
        self.assertEqual(report["s2c_receive_lengths"]["fixed"], 230)
        self.assertEqual(report["s2c_receive_lengths"]["variable"], 22)
        self.assertEqual(report["s2c_receive_lengths"]["unsupported"], 4)
        self.assertIsNone(report["whole_game_completion_percent"])

        cases = report["c2s_world_parser"]["cases"]
        self.assertEqual(report["c2s_world_parser"]["distinct_opcodes"], 44)
        self.assertEqual(len({case["opcode"] for case in cases}), len(cases))
        self.assertEqual({case["opcode"] for case in cases}, {
            0x1c, 0x1d, 0x1f, 0x20, 0x21, 0x24, 0x25, 0x26, 0x27, 0x28, 0x2e,
            0x29,0x2a,0x2b,0x2c,0x2d,0x2f, 0x30, 0x35, 0x36, 0x37, 0x57, 0x58, 0x5a, 0x66, 0x67, 0x6a, 0x6d, 0x74,
            0x39,0x61,0x62,0x63,0x64,0x65,0x85, 0x86, 0x88, 0x99, 0x9a, 0xa9, 0xd6, 0xd7, 0xd8,
        })
        self.assertTrue(all(case["evidence"] == "FORMAL_C2S_WORLD_PARSER_CASE_ONLY" for case in cases))
        connected = report["newly_connected_c2s_producers"]
        self.assertEqual({row["opcode"] for row in connected}, {0x74,0x88})
        self.assertTrue(all(row["status"] == "CANDIDATE_TRANSPORT_ACCEPTED_CURRENT_CLIENT" for row in connected))
        self.assertTrue(all(row["acceptance"] for row in connected))


if __name__ == "__main__":
    unittest.main()
