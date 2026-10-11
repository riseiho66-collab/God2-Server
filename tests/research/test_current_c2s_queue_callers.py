"""Pin qualified queue call anchors while keeping candidate counts honest."""

import unittest

from tools.strike_lab import current_c2s_queue_callers as callers


class CurrentC2SQueueCallersTests(unittest.TestCase):
    def test_direct_call_candidates_include_independent_native_anchors(self):
        report = callers.build_report()
        rvas = {int(row["call_rva"], 16) for row in report["rows"]}
        # These five call sites have separately checked producer arguments.
        self.assertTrue({0x97DF3, 0x9637B, 0x1191E0, 0x157B8, 0x11770} <= rvas)
        self.assertEqual(report["direct_call_candidates"], len(rvas))
        self.assertEqual(report["queue_rva"], "0132E0")
        self.assertTrue(all(row["evidence"] == "DIRECT_CALL_BYTE_CANDIDATE_ONLY" for row in report["rows"]))


if __name__ == "__main__":
    unittest.main()
