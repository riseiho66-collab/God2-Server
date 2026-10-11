import copy
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools/strike_lab"))
from frontier_planner import FrontierPlanner


def frontier():
    substrates = {}
    for name, cost in (("VM", 4), ("TRANSACTION", 2), ("HYPERFORK", 3),
                       ("FULL_NATIVE_CLIENT", 20)):
        substrates[name] = {
            "available": True, "qualified": True, "fidelity": True,
            "execution_available": True,
            "failures": [],
            "cost": {"frontier_id": "login", "measured": True, "milliseconds": cost},
        }
    substrates["VM"].update(successful_replays=3, closure=True)
    substrates["TRANSACTION"].update(handler="login_handler", rollback=True, side_effect_safe=True)
    substrates["HYPERFORK"].update(access=True, checkpoint=True, successful_restores=3)
    return {"id": "login", "current_handler": "login_handler", "substrates": substrates}


class FrontierPlannerTests(unittest.TestCase):
    def setUp(self):
        self.planner = FrontierPlanner()

    def test_cheapest_valid_measured_including_native(self):
        data = frontier()
        self.assertEqual(self.planner.plan(data)["selected"], "TRANSACTION")
        data["substrates"]["FULL_NATIVE_CLIENT"]["cost"]["milliseconds"] = 0
        self.assertEqual(self.planner.plan(data)["selected"], "FULL_NATIVE_CLIENT")

    def test_each_accelerated_gate_is_required(self):
        gates = {
            "VM": {"successful_replays": 2, "closure": False},
            "TRANSACTION": {"handler": "old_handler", "rollback": False, "side_effect_safe": False},
            "HYPERFORK": {"access": False, "checkpoint": False, "successful_restores": 2},
        }
        for name, fields in gates.items():
            for field, bad in dict(fields, available=False, qualified=False, fidelity=False).items():
                for value in (bad, None):
                    with self.subTest(name=name, field=field, value=value):
                        data = frontier()
                        data["substrates"][name][field] = value
                        result = self.planner.plan(data)
                        self.assertFalse(result["candidates"][name]["ready"])
                        self.assertNotEqual(result["selected"], name)

    def test_replay_restore_counts_are_integer_success_counts(self):
        for name, field in (("VM", "successful_replays"), ("HYPERFORK", "successful_restores")):
            for value in (True, 3.0, "3", -1, 0, 2, 3, 4):
                with self.subTest(name=name, value=value):
                    data = frontier()
                    data["substrates"][name][field] = value
                    self.assertEqual(self.planner.plan(data)["candidates"][name]["ready"],
                                     type(value) is int and value >= 3)

    def test_missing_current_handler_never_qualifies_transaction(self):
        data = frontier()
        data["current_handler"] = None
        data["substrates"]["TRANSACTION"]["handler"] = None
        self.assertFalse(self.planner.plan(data)["candidates"]["TRANSACTION"]["ready"])

    def test_unknown_cost_never_borrows_or_competes(self):
        invalid = [None, {}, {"frontier_id": "other", "measured": True, "milliseconds": 0},
                   {"frontier_id": "login", "measured": False, "milliseconds": 0}]
        invalid += [{"frontier_id": "login", "measured": True, "milliseconds": value}
                    for value in (None, True, "0", -1, float("nan"), float("inf"))]
        for cost in invalid:
            with self.subTest(cost=cost):
                data = frontier()
                data["substrates"]["TRANSACTION"]["cost"] = cost
                result = self.planner.plan(data)
                self.assertEqual(result["selected"], "HYPERFORK")
                self.assertEqual(result["candidates"]["TRANSACTION"]["cost_status"], "UNKNOWN")
                self.assertIsNone(result["candidates"]["TRANSACTION"]["cost_ms"])
                json.dumps(result, allow_nan=False)

    def test_native_fallback_readiness_and_unknown_cost(self):
        for available in (False, True):
            data = {"id": "next", "substrates": {"FULL_NATIVE_CLIENT": {
                "available": available, "execution_available": True}}}
            result = self.planner.plan(data)
            self.assertEqual(result["selected"], "FULL_NATIVE_CLIENT")
            self.assertEqual(result["ready"], available)
            self.assertEqual(result["reason"], "FULL_NATIVE_FALLBACK")
            self.assertEqual(result["cost_status"], "UNKNOWN")
            self.assertIsNone(result["cost_ms"])
        self.assertFalse(self.planner.plan({"id": "empty"})["ready"])

    def test_qualified_but_unmeasured_accelerators_do_not_win(self):
        data = frontier()
        for evidence in data["substrates"].values():
            evidence.pop("cost")
        result = self.planner.plan(data)
        self.assertEqual(result["selected"], "FULL_NATIVE_CLIENT")
        self.assertTrue(result["ready"])

    def test_native_preflight_pass_does_not_imply_automated_execution(self):
        data = {"id": "SERVER_SELECTION_C2S", "substrates": {
            "FULL_NATIVE_CLIENT": {
                "available": True, "qualified": True, "fidelity": True,
                "preflight_passed": 11, "execution_available": False,
                "execution_error": "sky.list_apps nativepipe unavailable error 2",
            }}, "ui_gate_preflight": {"required": True}, "legacy": {"preserve": True}}
        original = copy.deepcopy(data)
        result = self.planner.plan(data)
        self.assertEqual(result["selected"], "FULL_NATIVE_CLIENT")
        self.assertFalse(result["ready"])
        self.assertEqual(result["execution_status"], "BLOCKED_EXECUTION")
        self.assertEqual(result["candidates"]["FULL_NATIVE_CLIENT"]["reasons"],
                         ["AUTOMATION_UNAVAILABLE"])
        self.assertTrue(all(item["cost_status"] == "UNKNOWN"
                            for item in result["candidates"].values()))
        self.assertEqual(data, original)

    def test_failures_disable_only_the_supplied_frontier(self):
        failed = frontier()
        failed["substrates"]["TRANSACTION"]["failures"] = ["rollback drift"]
        self.assertEqual(self.planner.plan(failed)["selected"], "HYPERFORK")
        self.assertEqual(self.planner.plan(frontier())["selected"], "TRANSACTION")
        for evidence in failed["substrates"].values():
            evidence["failures"] = ["frontier mismatch"]
        result = self.planner.plan(failed)
        self.assertEqual(result["selected"], "FULL_NATIVE_CLIENT")
        self.assertFalse(result["ready"])

    def test_native_explicit_disqualification_blocks_readiness(self):
        for field in ("qualified", "fidelity"):
            data = {"id": "next", "substrates": {"FULL_NATIVE_CLIENT": {"available": True, field: False}}}
            self.assertFalse(self.planner.plan(data)["ready"])

    def test_pure_repeatable_and_stable_ties(self):
        data = frontier()
        for evidence in data["substrates"].values():
            evidence["cost"]["milliseconds"] = 1
        original = copy.deepcopy(data)
        first = self.planner.plan(data)
        self.assertEqual(first["selected"], "VM")
        self.assertEqual(first, self.planner.plan(data))
        first["candidates"]["VM"]["reasons"].append("caller mutation")
        self.assertTrue(self.planner.plan(data)["candidates"]["VM"]["ready"])
        self.assertEqual(data, original)

    def test_frontier_identity_required(self):
        for identity in (None, "", 1):
            with self.assertRaises(ValueError):
                self.planner.plan({"id": identity})


if __name__ == "__main__":
    unittest.main()
