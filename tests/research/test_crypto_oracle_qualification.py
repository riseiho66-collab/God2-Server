import copy
import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/crypto_oracle"))
from qualification import evaluate_qualification


def ref(kind, record):
    raw = json.dumps(record, sort_keys=True).encode()
    return {"type": kind, "sha256": hashlib.sha256(raw).hexdigest(), "raw_hex": raw.hex()}


def packets(run="offline", session="corpus", live=False):
    result = []
    for direction in ("C2S", "S2C"):
        for sequence in (1, 2):
            record = dict(run_id=run, session_id=session, vector_id=f"{direction}-{sequence}",
                          direction=direction, sequence=sequence, input_hex=f"0{sequence}",
                          state_before_hex=f"0{sequence}", oracle_output_hex="ab",
                          clean_output_hex="ab", oracle_state_after_hex=f"0{sequence + 1}",
                          clean_state_after_hex=f"0{sequence + 1}")
            if live:
                record.update(client_output_hex="ab", client_state_after_hex=f"0{sequence + 1}")
                acceptance = {key: record[key] for key in
                              ("run_id", "session_id", "vector_id", "direction")}
                acceptance.update(consumer="clean_parser" if direction == "C2S" else "original_client",
                                  result="accepted", parser_event_id=f"event-{direction}-{sequence}")
                record["acceptance"] = ref("parser_acceptance_v1", acceptance)
            result.append(ref("live_packet_v1" if live else "oracle_diff_vector_v1", record))
    return result


def report():
    return dict(capsule_corpus_pass=True, output_mismatches=0, state_mismatches=0,
                brute_force_count=0, run_id="offline", session_id="corpus",
                offline_vectors=packets(), live_sessions=[])


def session(label):
    return dict(label=label, run_id="run-" + label, session_id="session-" + label,
                seed_sha256=hashlib.sha256(("seed-" + label).encode()).hexdigest(),
                key_sha256=hashlib.sha256(("key-" + label).encode()).hexdigest(),
                backend="Clean", fresh=True, c2s_count=2, s2c_count=2,
                packets=packets("run-" + label, "session-" + label, live=True))


class QualificationTests(unittest.TestCase):
    def denied(self, value):
        result = evaluate_qualification(value)
        self.assertIs(result["CRYPTO_RECOVERED"], False)
        self.assertIs(result["promotion_blocked"], True)
        return result

    def test_offline_can_only_qualify_offline(self):
        result = self.denied(report())
        self.assertEqual(result["status"], "ORACLE_EQUIVALENT_OFFLINE")
        self.assertEqual(result["offline_errors"], [])
        self.assertIn("ADAPTER_REQUIRED", result["next_live_gate"])

    def test_boolean_claims_are_not_evidence(self):
        value = report()
        value.update(offline_vectors=[], CRYPTO_RECOVERED=True, live_sessions=[True, True],
                     runtime_validated=True, trusted_runtime_adapter=True)
        self.assertEqual(self.denied(value)["status"], "ORACLE_EVIDENCE_REJECTED")

    def test_numeric_flags_reject_bool_string_negative_missing_and_nonzero(self):
        for field in ("output_mismatches", "state_mismatches", "brute_force_count"):
            for invalid in (False, True, "0", -1, 1, None, 0.0):
                with self.subTest(field=field, invalid=invalid):
                    value = report()
                    value[field] = invalid
                    self.assertTrue(self.denied(value)["offline_errors"])

    def test_fake_or_missing_raw_hash_denied(self):
        for change in ({"sha256": "0" * 64}, {"raw_hex": ""}, {"type": "PASS"}):
            value = report()
            value["offline_vectors"][0].update(change)
            self.assertTrue(self.denied(value)["offline_errors"])

    def test_duplicate_content_with_new_id_denied(self):
        value = report()
        vector = json.loads(bytes.fromhex(value["offline_vectors"][0]["raw_hex"]))
        vector.update(vector_id="renamed", sequence=2)
        value["offline_vectors"][1] = ref("oracle_diff_vector_v1", vector)
        self.assertIn("duplicate vector content", " ".join(self.denied(value)["offline_errors"]))

    def test_raw_mismatch_identity_sequence_and_continuity_denied(self):
        for field, invalid in (("clean_output_hex", "ac"), ("clean_state_after_hex", "ff"),
                               ("run_id", "other"), ("sequence", True),
                               ("state_before_hex", "ff"), ("direction", [])):
            value = report()
            vector = json.loads(bytes.fromhex(value["offline_vectors"][1]["raw_hex"]))
            vector[field] = invalid
            value["offline_vectors"][1] = ref("oracle_diff_vector_v1", vector)
            self.assertTrue(self.denied(value)["offline_errors"])

    def test_same_key_seed_run_or_session_denied(self):
        for field in ("key_sha256", "seed_sha256", "run_id", "session_id"):
            value = report()
            a, b = session("A"), session("B")
            b[field] = a[field]
            value["live_sessions"] = [ref("live_session_v1", item) for item in (a, b)]
            self.assertIn("repeated " + field, " ".join(self.denied(value)["missing_evidence"]))

    def test_structurally_complete_live_claims_still_need_trusted_adapter(self):
        value = report()
        value["live_sessions"] = [ref("live_session_v1", session(label)) for label in ("A", "B")]
        result = self.denied(value)
        self.assertEqual(len(result["missing_evidence"]), 1)
        self.assertIn("adapter absent", result["missing_evidence"][0])

    def test_live_acceptance_boolean_and_counts_denied(self):
        value = report()
        a = session("A")
        a["c2s_count"] = True
        packet = json.loads(bytes.fromhex(a["packets"][0]["raw_hex"]))
        packet["acceptance"] = True
        a["packets"][0] = ref("live_packet_v1", packet)
        value["live_sessions"] = [ref("live_session_v1", a), ref("live_session_v1", session("B"))]
        missing = " ".join(self.denied(value)["missing_evidence"])
        self.assertIn("typed raw reference required", missing)
        self.assertIn("count mismatch", missing)

    def test_malformed_report_and_duplicate_json_keys(self):
        for value in (None, [], True, {}, {"live_sessions": [{}, {}]}):
            self.assertTrue(self.denied(value)["offline_errors"])
        value = report()
        raw = b'{"run_id":"one","run_id":"two"}'
        value["offline_vectors"][0] = dict(type="oracle_diff_vector_v1", raw_hex=raw.hex(),
                                          sha256=hashlib.sha256(raw).hexdigest())
        self.assertTrue(self.denied(value)["offline_errors"])

    def test_report_is_not_mutated_or_raw_data_returned(self):
        value = report()
        before = copy.deepcopy(value)
        result = self.denied(value)
        self.assertEqual(value, before)
        self.assertNotIn("raw_hex", json.dumps(result))


if __name__ == "__main__":
    unittest.main()
