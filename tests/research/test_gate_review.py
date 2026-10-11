"""Local review-policy fixtures are not real human reviews or client evidence."""
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

import test_runtime_evidence as fixtures

sys.path.insert(0, str(fixtures.RESEARCH))
try:
    import gate_review
finally:
    sys.path.pop(0)


class GateReviewTests(unittest.TestCase):
    setUp = fixtures.RuntimeEvidenceTests.setUp
    event = staticmethod(fixtures.RuntimeEvidenceTests.event)
    attachment = fixtures.RuntimeEvidenceTests.attachment
    write = fixtures.RuntimeEvidenceTests.write
    ready_unpack = fixtures.RuntimeEvidenceTests.ready_unpack
    ready_iat = fixtures.RuntimeEvidenceTests.ready_iat

    def initialize(self, synthetic=False):
        self.ready_iat()
        if synthetic:
            self.manifest["provenance"]["source_kind"] = "synthetic"
        self.write()
        self.capture = self.store.ingest(self.bundle)
        self.review = gate_review.ReviewStore(self.store.root)
        self.policy = self.store.root / "review-policy.json"
        self.policy.write_text(json.dumps({"schema_version": 1, "reviewers": ["fixture-reviewer", "unit-test"]}), encoding="utf-8")

    def review_request(self, gate="G02", decision="APPROVE"):
        path = self.base / "review.json"
        if path.exists():
            path.unlink()
        request = self.review.prepare(self.capture, gate, path)
        request.update(reviewer="fixture-reviewer", reviewed_at="2026-09-18T01:00:00+00:00",
                       decision=decision, rationale="Fabricated unit-test review, never production evidence",
                       human_attestation=True)
        request["checks"] = dict.fromkeys(request["checks"], True)
        path.write_text(json.dumps(request), encoding="utf-8")
        (self.base / "test-report.txt").write_text("Synthetic test transcript, not real client execution\n", encoding="utf-8")
        return path, request

    def approval(self, gate="G02"):
        path, _ = self.review_request(gate)
        return self.review.submit(path)

    def test_prepare_never_supplies_a_human_decision(self):
        self.initialize()
        path = self.base / "empty-review.json"
        request = self.review.prepare(self.capture, "G02", path)
        self.assertIsNone(request["reviewer"])
        self.assertFalse(request["human_attestation"])
        with self.assertRaises(ValueError):
            self.review.submit(path)
        with self.assertRaises(ValueError):
            self.review.prepare(self.capture, "G05", self.base / "unsupported.json")

    def test_missing_policy_and_self_approval_fail_closed(self):
        self.initialize()
        path, request = self.review_request()
        policy = self.policy.read_bytes()
        self.policy.unlink()
        with self.assertRaises(ValueError):
            self.review.submit(path)
        self.policy.write_bytes(policy)
        request["reviewer"] = "unit-test"
        path.write_text(json.dumps(request), encoding="utf-8")
        with self.assertRaises(ValueError):
            self.review.submit(path)

    def test_incomplete_checklist_untrusted_reviewer_and_references_rejected(self):
        self.initialize()
        for field, value in (("human_attestation", 1), ("reviewer", "unknown"),
                             ("evidence_ids", ["missing"]), ("evidence_ids", []),
                             ("test_report", "../outside.txt"), ("reviewed_at", "2020-01-01T00:00:00+00:00")):
            with self.subTest(field=field):
                path, request = self.review_request()
                request[field] = value
                path.write_text(json.dumps(request), encoding="utf-8")
                with self.assertRaises((ValueError, OSError)):
                    self.review.submit(path)
        path, request = self.review_request()
        request["checks"]["execution_semantics_confirmed"] = False
        path.write_text(json.dumps(request), encoding="utf-8")
        with self.assertRaises(ValueError):
            self.review.submit(path)

    def test_synthetic_evidence_cannot_be_approved(self):
        self.initialize(synthetic=True)
        with self.assertRaises(ValueError):
            self.approval()
        path, _ = self.review_request(decision="REJECT")
        rejected = self.review.submit(path)
        with self.assertRaises(ValueError):
            self.review.promote(rejected)

    def test_approval_is_not_promotion_and_content_is_idempotent(self):
        self.initialize()
        approved = self.approval()
        self.assertEqual(approved, self.approval())
        self.assertEqual(self.review.status(self.artifact)["highest_acceptance"], "L1 ARTIFACT_VERIFIED")
        certificate = self.review.promote(approved)
        self.assertEqual(certificate, self.review.promote(approved))
        self.assertEqual(self.review.audit(certificate)["status"], "VALID")
        self.assertEqual(self.review.status(self.artifact)["highest_acceptance"], "L2 UNPACK_VERIFIED")

    def test_revoked_certificate_cannot_be_silently_reissued(self):
        self.initialize()
        approved = self.approval()
        certificate = self.review.promote(approved)
        self.review.revoke(certificate, "fixture-reviewer", "Synthetic withdrawal")
        with self.assertRaises(ValueError):
            self.review.promote(approved)

    def test_prerequisites_required_and_revocation_propagates(self):
        self.initialize()
        certificates = []
        for gate in gate_review.GATE_MAP:
            approved = self.approval(gate)
            if certificates:
                with self.assertRaises(ValueError):
                    self.review.promote(approved)
            certificates.append(self.review.promote(approved, certificates[-1] if certificates else None))
        self.assertEqual(self.review.status(self.artifact)["highest_acceptance"], "L5 ANALYSIS_IMAGE_VERIFIED")
        self.review.revoke(certificates[0], "fixture-reviewer", "Synthetic revocation test")
        self.assertIn(certificates[-1], self.review.audit(certificates[0])["affected_dependents"])
        for certificate in certificates:
            self.assertEqual(self.review.audit(certificate)["status"], "INVALID")
        self.assertEqual(self.review.status(self.artifact)["highest_acceptance"], "L1 ARTIFACT_VERIFIED")

    def test_rejection_blocks_prior_approval_until_explicitly_revoked(self):
        self.initialize()
        certificate = self.review.promote(self.approval())
        path, _ = self.review_request(decision="REJECT")
        rejection = self.review.submit(path)
        self.assertEqual(self.review.audit(certificate)["status"], "INVALID")
        destination = self.base / "rejection-report"
        self.store.report(self.artifact, destination)
        self.assertIn("unresolved rejection", (destination / "CONTRADICTIONS.md").read_text(encoding="utf-8"))
        self.review.revoke(rejection, "fixture-reviewer", "Fixture reviewer resolved contradiction")
        self.assertEqual(self.review.audit(certificate)["status"], "VALID")

    def test_revoked_review_cannot_issue_another_certificate(self):
        self.initialize()
        approved = self.approval()
        self.review.revoke(approved, "fixture-reviewer", "Fixture approval withdrawn")
        with self.assertRaises(ValueError):
            self.review.promote(approved)

    def test_policy_withdrawal_and_validator_change_invalidate(self):
        self.initialize()
        certificate = self.review.promote(self.approval())
        with patch.object(gate_review, "tool_version", return_value="changed"):
            self.assertEqual(self.review.audit(certificate)["status"], "INVALID")
        self.policy.write_text(json.dumps({"schema_version": 1, "reviewers": ["someone-else"]}), encoding="utf-8")
        self.assertEqual(self.review.audit(certificate)["status"], "INVALID")

    def test_proof_and_index_tampering_fail_audit(self):
        self.initialize()
        approved = self.approval()
        path = self.review._path(approved)
        before = path.read_bytes()
        path.write_bytes(before + b"\n")
        with self.assertRaises(ValueError):
            self.review.audit(approved)
        path.write_bytes(before)
        db = self.review._db()
        try:
            with db:
                db.execute("DELETE FROM proof_objects WHERE id=?", (approved,))
        finally:
            db.close()
        with self.assertRaises(ValueError):
            self.review.audit(approved)

    def test_runtime_source_corruption_invalidates_certificate(self):
        self.initialize()
        certificate = self.review.promote(self.approval())
        (self.store.captures / self.capture / "native.log").write_bytes(b"changed")
        with self.assertRaises(ValueError):
            self.review.audit(certificate)

    def test_new_capture_counter_evidence_invalidates_old_certificate(self):
        self.initialize()
        certificate = self.review.promote(self.approval())
        self.manifest["session_id"] = "counter-capture"
        self.events.append(self.event("counter_evidence", dict(gate="unpack", related_event_ids=["event-0"],
                                  reason="Synthetic cross-capture contradiction"), len(self.events)))
        self.write()
        self.store.ingest(self.bundle)
        self.assertEqual(self.review.audit(certificate)["status"], "INVALID")

    def test_runtime_report_uses_review_status_and_revocation(self):
        self.initialize()
        certificate = self.review.promote(self.approval())
        self.assertEqual(self.store.status(self.artifact)["highest_runtime_acceptance"], "L2 UNPACK_VERIFIED")
        self.review.revoke(certificate, "fixture-reviewer", "Synthetic report regression")
        self.assertEqual(self.store.status(self.artifact)["highest_runtime_acceptance"], "L1 ARTIFACT_VERIFIED")


if __name__ == "__main__":
    unittest.main()
