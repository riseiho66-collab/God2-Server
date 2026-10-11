"""Synthetic evidence checks; these tests do not execute the original client."""

import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
from native_lab.certification import LEVELS, qualify


class CertificationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def artifact(self, name, data):
        (self.root / name).write_bytes(data)
        return {"path": name, "sha256": hashlib.sha256(data).hexdigest()}

    def fixture(self):
        packet = self.artifact("packet.bin", b"\x06\x00\x01\x00\x00\x00")
        evidence, runs = [], []
        for index, level in enumerate(LEVELS):
            before = self.artifact(f"before-{index}.bin", b"before" + bytes([index]))
            after = self.artifact(f"after-{index}.bin", b"after" + bytes([index]))
            run = dict(schema="native-certification/v1", run_id=f"run-{index}",
                       session_id=f"session-{index}", transition_id="edge", from_state="WAIT",
                       to_state="READY", lane="CLEAN" if index == 2 else "LAB",
                       transport="DIRECT_HANDLER" if index == 0 else "REAL_SOCKET",
                       crypto="LOGICAL" if index == 0 else "CLEAN_CPP",
                       instrumentation="NONE" if index == 2 else "LAB_AGENT",
                       execution="ORIGINAL_NATIVE_CLIENT", result="STATE_ADVANCED",
                       packet=packet, state_before=before, state_after=after)
            evidence.append(dict(level=level, packet=packet, state_before=before,
                                 state_after=after, run=self.artifact(
                                     f"run-{index}.json", json.dumps(run).encode())))
            runs.append(run)
        return evidence, runs

    def rewrite(self, evidence, runs, index):
        evidence[index]["run"] = self.artifact(
            f"run-{index}.json", json.dumps(runs[index]).encode())

    def test_valid_structures_never_certify(self):
        evidence, _ = self.fixture()
        for count in range(4):
            report = qualify(self.root, evidence[:count])
            self.assertEqual(report["structural_level"], count)
            self.assertEqual(report["certification_level"], 0)
            self.assertEqual(report["provenance"], "UNTRUSTED")
            self.assertIn("NO_VERIFIED_ORIGINAL_ACTION_EVIDENCE", report["limitations"])

    def test_caller_booleans_cannot_qualify(self):
        for value in (True, {"level1": True, "level2": True, "level3": True}, [True]):
            report = qualify(self.root, value)
            self.assertEqual(report["structural_level"], 0)
            self.assertEqual(report["certification_level"], 0)
            self.assertTrue(report["errors"])
        evidence, _ = self.fixture()
        evidence[0]["trusted"] = True
        self.assertEqual(qualify(self.root, evidence)["structural_level"], 0)

    def test_missing_or_tampered_artifacts(self):
        for field in ("run", "packet", "state_before", "state_after"):
            for operation in ("remove", "tamper", "empty"):
                with self.subTest(field=field, operation=operation):
                    evidence, _ = self.fixture()
                    path = self.root / evidence[0][field]["path"]
                    if operation == "remove":
                        path.unlink()
                    else:
                        path.write_bytes(b"changed" if operation == "tamper" else b"")
                    self.assertEqual(qualify(self.root, evidence)["structural_level"], 0)

    def test_lanes_modes_and_native_execution_are_required(self):
        for index in range(3):
            for field in ("lane", "transport", "crypto", "instrumentation", "execution", "result"):
                with self.subTest(index=index, field=field):
                    evidence, runs = self.fixture()
                    runs[index][field] = True
                    self.rewrite(evidence, runs, index)
                    self.assertEqual(qualify(self.root, evidence)["structural_level"], index)

    def test_gate_order_and_no_skipping(self):
        evidence, _ = self.fixture()
        for records in ([evidence[1]], [evidence[2]], [evidence[0], evidence[2]], evidence * 2):
            self.assertTrue(qualify(self.root, records)["errors"])

    def test_cross_gate_identity_and_packet_binding(self):
        for field in ("transition_id", "from_state", "to_state", "run_id", "packet"):
            with self.subTest(field=field):
                evidence, runs = self.fixture()
                if field == "packet":
                    runs[1][field] = self.artifact("other.bin", b"other packet")
                    evidence[1][field] = runs[1][field]
                else:
                    runs[1][field] = "run-0" if field == "run_id" else "different"
                self.rewrite(evidence, runs, 1)
                self.assertEqual(qualify(self.root, evidence)["structural_level"], 1)

    def test_run_must_bind_state_artifacts(self):
        evidence, _ = self.fixture()
        evidence[0]["state_after"] = evidence[1]["state_after"]
        self.assertEqual(qualify(self.root, evidence)["structural_level"], 0)

    def test_identical_states_fail(self):
        evidence, runs = self.fixture()
        runs[0]["state_after"] = runs[0]["state_before"]
        evidence[0]["state_after"] = runs[0]["state_after"]
        self.rewrite(evidence, runs, 0)
        self.assertEqual(qualify(self.root, evidence)["structural_level"], 0)

    def test_path_escape_and_invalid_hash_fail(self):
        for name in ("../outside.bin", "C:/outside.bin", "/outside.bin", "file:stream"):
            evidence, _ = self.fixture()
            evidence[0]["run"]["path"] = name
            self.assertEqual(qualify(self.root, evidence)["structural_level"], 0)
        evidence, _ = self.fixture()
        evidence[0]["run"]["sha256"] = True
        self.assertEqual(qualify(self.root, evidence)["structural_level"], 0)

    def test_invalid_json_and_duplicate_fields_fail(self):
        for data in (b"not json", b"[]", b'{"schema":"a","schema":"b"}'):
            evidence, _ = self.fixture()
            evidence[0]["run"] = self.artifact("invalid.json", data)
            self.assertEqual(qualify(self.root, evidence)["structural_level"], 0)

    def test_claimed_provenance_is_not_observer_evidence(self):
        evidence, runs = self.fixture()
        runs[0]["provenance"] = "TRUSTED"
        self.rewrite(evidence, runs, 0)
        report = qualify(self.root, evidence)
        self.assertEqual(report["structural_level"], 0)
        self.assertEqual(report["provenance"], "UNTRUSTED")


if __name__ == "__main__":
    unittest.main()
