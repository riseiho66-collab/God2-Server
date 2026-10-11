"""Fabricated local-review fixtures, never human attestation in the real vault."""
import json
import unittest
from unittest.mock import patch

import test_gate_review as fixtures


class CounterResolutionTests(unittest.TestCase):
    setUp = fixtures.GateReviewTests.setUp
    event = staticmethod(fixtures.GateReviewTests.event)
    attachment = fixtures.GateReviewTests.attachment
    write = fixtures.GateReviewTests.write
    ready_unpack = fixtures.GateReviewTests.ready_unpack
    ready_iat = fixtures.GateReviewTests.ready_iat
    initialize = fixtures.GateReviewTests.initialize
    review_request = fixtures.GateReviewTests.review_request
    approval = fixtures.GateReviewTests.approval

    def counter(self):
        self.manifest["session_id"] = "counter-session"
        self.events.append(self.event("counter_evidence", dict(gate="unpack", related_event_ids=["event-0"],
                                  reason="Fabricated test contradiction"), len(self.events)))
        self.write()
        self.counter_capture = self.store.ingest(self.bundle)
        self.counter_event = self.events[-1]["id"]

    def resolution_request(self, state="RESOLVED_SUPPORT"):
        path = self.base / "resolution.json"
        if path.exists():
            path.unlink()
        request = self.review.prepare_resolution(self.counter_capture, self.counter_event, path)
        request.update(state=state, reviewer="fixture-reviewer", reviewed_at="2026-09-18T02:00:00+00:00",
                       rationale="Synthetic independent resolution fixture", human_attestation=True,
                       evidence_refs=[{"capture_id": self.capture, "event_id": "event-0"}])
        path.write_text(json.dumps(request), encoding="utf-8")
        (self.base / "resolution-report.txt").write_text("Synthetic resolution transcript secret-marker", encoding="utf-8")
        return path, request

    def state(self):
        return self.review.status(self.artifact)["counter_evidence"][0]["state"]

    def test_open_blocks_and_support_requires_fresh_gate_review(self):
        self.initialize()
        old = self.review.promote(self.approval())
        self.counter()
        self.assertEqual(self.state(), "OPEN")
        with self.assertRaises(ValueError):
            self.approval()
        path, _ = self.resolution_request()
        resolution = self.review.resolve(path)
        self.assertEqual(resolution, self.review.resolve(path))
        self.assertEqual(self.state(), "RESOLVED_SUPPORT")
        self.assertEqual(self.store.assess(self.counter_capture)["gates"]["unpack"]["status"], "BLOCKED")
        self.assertEqual(self.review.audit(old)["status"], "INVALID")
        approved = self.approval()
        self.assertIn(resolution, self.review.audit(approved)["payload"]["resolution_ids"])
        self.assertEqual(self.review.audit(self.review.promote(approved))["status"], "VALID")
        self.assertNotIn("secret-marker", json.dumps(self.review.audit(resolution)))

    def test_all_states_history_and_no_stale_branch(self):
        self.initialize()
        self.counter()
        previous = None
        for state in ("OPEN", "INCONCLUSIVE", "RESOLVED_REJECT", "RESOLVED_SUPPORT"):
            path, request = self.resolution_request(state)
            stale = dict(request)
            current = self.review.resolve(path)
            self.assertEqual(self.state(), state)
            if previous:
                self.assertEqual(self.review.audit(previous)["status"], "INVALID")
            stale["rationale"] = "Different stale request"
            path.write_text(json.dumps(stale), encoding="utf-8")
            with self.assertRaises(ValueError):
                self.review.resolve(path)
            if state != "RESOLVED_SUPPORT":
                with self.assertRaises(ValueError):
                    self.approval()
            previous = current

    def test_revocation_and_policy_loss_reopen_contradiction(self):
        self.initialize()
        self.counter()
        path, _ = self.resolution_request()
        resolution = self.review.resolve(path)
        certificate = self.review.promote(self.approval())
        self.review.revoke(resolution, "fixture-reviewer", "Synthetic retraction")
        self.assertEqual(self.state(), "OPEN")
        self.assertEqual(self.review.audit(certificate)["status"], "INVALID")
        path, _ = self.resolution_request()
        self.review.resolve(path)
        self.policy.unlink()
        self.assertEqual(self.state(), "OPEN")

    def test_attestation_independence_and_support_references_enforced(self):
        self.initialize()
        self.counter()
        for key, value in (("human_attestation", False), ("reviewer", "unit-test"), ("evidence_refs", []),
                           ("evidence_refs", [{"capture_id": "f" * 64, "event_id": "event-0"}]),
                           ("evidence_refs", [{"capture_id": self.counter_capture, "event_id": self.counter_event}])):
            path, request = self.resolution_request()
            request[key] = value
            path.write_text(json.dumps(request), encoding="utf-8")
            with self.subTest(key=key), self.assertRaises((ValueError, KeyError)):
                self.review.resolve(path)

    def test_support_cannot_override_failed_mechanical_checks(self):
        self.initialize()
        self.counter()
        self.events[0]["details"]["after_hex"] = "ff" * 8
        self.manifest["session_id"] = "mechanically-bad"
        self.write()
        self.counter_capture = self.store.ingest(self.bundle)
        path, _ = self.resolution_request()
        self.review.resolve(path)
        self.capture = self.counter_capture
        with self.assertRaises(ValueError):
            self.approval()

    def test_new_counter_not_covered_by_earlier_resolution(self):
        self.initialize()
        self.counter()
        path, _ = self.resolution_request()
        self.review.resolve(path)
        certificate = self.review.promote(self.approval())
        self.manifest["session_id"] = "additional-counter"
        self.write()
        self.store.ingest(self.bundle)
        self.assertEqual(self.review.audit(certificate)["status"], "INVALID")


if __name__ == "__main__":
    unittest.main()
