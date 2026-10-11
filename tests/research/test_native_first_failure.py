"""Synthetic schema fixtures only: these are not GOD2 native evidence."""

from copy import deepcopy
import hashlib
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/native_lab"))
from first_failure import validate_first_failure


class FirstFailureTests(unittest.TestCase):
    def setUp(self):
        self.packet = bytes([7, 0])
        self.trace = {
            "source": "NATIVE_LAB_CAPTURE", "trace_id": "synthetic-rejection",
            "direction": "SERVER_FIRST",
            "packet_sha256": hashlib.sha256(self.packet).hexdigest(),
            "handler": {"image_sha256": "a" * 64, "rva": 16,
                        "executed": True, "sequence": 1},
            "predicate": {
                "executed": True, "first_failure": True, "sequence": 3,
                "handler_rva": 16, "instruction_rva": 32,
                "observed_predicate": "synthetic observed comparison", "taken": False,
                "packet_operands": [{"source": "packet_direct_read", "offset": 0,
                                     "size": 2, "byteorder": "little", "value": 7,
                                     "read_sequence": 2, "read_rva": 24}],
            },
            "success_branch": {
                "source": "NATIVE_LAB_CAPTURE", "trace_id": "synthetic-success",
                "image_sha256": "a" * 64, "handler_rva": 16, "instruction_rva": 32,
                "executed": True, "taken": True, "event": "SYNTHETIC_EVENT",
                "event_observed": True, "path_to_event_observed": True,
                "branch_sequence": 4, "event_sequence": 5,
            },
        }

    def validate(self, trace):
        return validate_first_failure(trace, packet=self.packet,
                                      requested_success="SYNTHETIC_EVENT")

    def assertBlocked(self, trace):
        result = self.validate(trace)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertIsNone(result["constraint"])

    def test_no_native_trace_is_explicitly_blocked(self):
        self.assertEqual(validate_first_failure(), {
            "status": "BLOCKED", "reason": "native_trace_required", "constraint": None})
        for value in (None, [], "trace", {}, True):
            self.assertBlocked(value)

    def test_every_evidence_field_is_required(self):
        paths = [(key,) for key in self.trace]
        for group in ("handler", "predicate", "success_branch"):
            paths.extend((group, key) for key in self.trace[group])
        paths.extend(("predicate", "packet_operands", 0, key)
                     for key in self.trace["predicate"]["packet_operands"][0])
        for path in paths:
            for replacement in ("delete", None, [], {}):
                with self.subTest(path=path, replacement=replacement):
                    trace = deepcopy(self.trace)
                    parent = trace
                    for key in path[:-1]:
                        parent = parent[key]
                    if replacement == "delete":
                        del parent[path[-1]]
                    else:
                        parent[path[-1]] = replacement
                    self.assertBlocked(trace)

    def test_conflicting_or_guessed_evidence_is_blocked(self):
        changes = [
            ((), "direction", "UNKNOWN"), ((), "source", "EMULATED"),
            ((), "packet_sha256", "b" * 64),
            (("handler",), "executed", False), (("handler",), "rva", True),
            (("predicate",), "handler_rva", 17),
            (("predicate",), "sequence", 1),
            (("predicate",), "first_failure", False),
            (("predicate",), "taken", 0),
            (("predicate", "packet_operands", 0), "offset", -1),
            (("predicate", "packet_operands", 0), "offset", 2),
            (("predicate", "packet_operands", 0), "size", True),
            (("predicate", "packet_operands", 0), "value", 8),
            (("predicate", "packet_operands", 0), "source", "guessed_derivation"),
            (("predicate", "packet_operands", 0), "read_sequence", 3),
            (("success_branch",), "trace_id", "synthetic-rejection"),
            (("success_branch",), "image_sha256", "b" * 64),
            (("success_branch",), "handler_rva", 17),
            (("success_branch",), "instruction_rva", 33),
            (("success_branch",), "taken", False),
            (("success_branch",), "event", "UNREQUESTED_EVENT"),
            (("success_branch",), "path_to_event_observed", False),
            (("success_branch",), "event_sequence", 4),
        ]
        for path, key, value in changes:
            with self.subTest(path=path, key=key, value=value):
                trace = deepcopy(self.trace)
                parent = trace
                for component in path:
                    parent = parent[component]
                parent[key] = value
                self.assertBlocked(trace)

    def test_packet_and_request_are_required(self):
        for packet in (None, b"", bytearray(self.packet), b"other"):
            self.assertEqual(validate_first_failure(
                self.trace, packet=packet, requested_success="SYNTHETIC_EVENT"
            )["status"], "BLOCKED")
        self.assertEqual(validate_first_failure(
            self.trace, packet=self.packet)["status"], "BLOCKED")

    def test_valid_schema_only_returns_observed_constraint(self):
        before = deepcopy(self.trace)
        result = self.validate(self.trace)
        self.assertEqual(result["status"], "EVIDENCE_VALIDATED")
        self.assertEqual(result["constraint"]["instruction_rva"], 32)
        self.assertIs(result["constraint"]["required_branch_taken"], True)
        self.assertEqual(self.trace, before)
        result["constraint"]["packet_operands"][0]["value"] = 999
        self.assertEqual(self.trace, before)


if __name__ == "__main__":
    unittest.main()
