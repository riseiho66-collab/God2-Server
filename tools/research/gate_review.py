"""Local human-review ledger and fail-closed Gate 02-04.5 certificate auditor."""
from datetime import datetime, timezone
import argparse
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
import uuid

from artifact_vault import json_bytes
from runtime_contract import SHA, exact, parse_json, read_limit, require, safe_file, text
from runtime_checks import assess_bundle

GATE_MAP = {"G02": "unpack", "G03": "oep", "G04": "iat", "G04.5": "quality"}
CHECKS = ("native_trace_reviewed", "artifact_and_module_provenance_confirmed",
          "execution_semantics_confirmed", "regression_results_reviewed",
          "no_unresolved_counter_evidence")
SPECIAL = {"G02": "unpack_transition_and_dump_confirmed",
           "G03": "stable_oep_and_continuation_confirmed",
           "G04": "all_repaired_imports_and_final_targets_confirmed",
           "G04.5": "analysis_image_and_disassembly_independently_checked"}
MAX_OBJECT = 2 * 1024 * 1024
RESOLUTION_STATES = ("OPEN", "RESOLVED_SUPPORT", "RESOLVED_REJECT", "INCONCLUSIVE")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def timestamp(value):
    text(value, "timestamp")
    result = datetime.fromisoformat(value)
    require(result.utcoffset() is not None, "Timestamp needs timezone")
    return result


def tool_version():
    root = Path(__file__).parent
    names = ("artifact_vault.py", "runtime_contract.py", "runtime_checks.py", "runtime_evidence.py", "gate_review.py")
    return "god2-review-v1/" + sha(json_bytes({n: sha((root / n).read_bytes()) for n in names}))


class ReviewStore:
    def __init__(self, root):
        from runtime_evidence import RuntimeStore
        self.runtime = RuntimeStore(root)
        self.root = self.runtime.root
        self.objects = self.root / "proofs"

    def _db(self):
        db = self.runtime.vault.connect()
        with db:
            db.execute("CREATE TABLE IF NOT EXISTS proof_objects(id TEXT PRIMARY KEY, document TEXT NOT NULL)")
        return db

    def _path(self, object_id):
        require(isinstance(object_id, str) and SHA.fullmatch(object_id), "Invalid proof object ID")
        return safe_file(self.root, "proofs/" + object_id + ".json")

    def _policy(self):
        path = safe_file(self.root, "review-policy.json")
        require(path.exists(), "No human-managed review-policy.json; promotion disabled")
        raw = read_limit(path, 16384)
        policy = parse_json(raw)
        exact(policy, {"schema_version", "reviewers"}, "review policy")
        require(type(policy["schema_version"]) is int and policy["schema_version"] == 1, "Unsupported review policy")
        names = policy["reviewers"]
        require(isinstance(names, list) and 1 <= len(names) <= 32, "Policy requires 1-32 human reviewer IDs")
        for name in names:
            text(name, "reviewer", 80)
            require(name == name.strip(), "Reviewer IDs must be trimmed")
        require(len({name.casefold() for name in names}) == len(names), "Duplicate reviewer IDs")
        return policy, sha(raw)

    def _authorized(self, reviewer, operator=None):
        policy, policy_hash = self._policy()
        text(reviewer, "reviewer", 80)
        require(reviewer in policy["reviewers"], "Reviewer is not in the human-managed policy")
        require(operator is None or reviewer.casefold() != operator.strip().casefold(), "Capture producer cannot independently approve their own capture")
        return policy_hash

    def _all(self):
        db = self._db()
        try:
            rows = db.execute("SELECT id,document FROM proof_objects ORDER BY id").fetchall()
        finally:
            db.close()
        require(len(rows) <= 4096, "Proof ledger exceeds bounded v1 capacity")
        found = {p.stem for p in self.objects.glob("*.json")} if self.objects.exists() else set()
        require(found == {row[0] for row in rows}, "Proof ledger/files mismatch; missing or unindexed object")
        result = {}
        for object_id, indexed in rows:
            raw = read_limit(self._path(object_id), MAX_OBJECT)
            require(sha(raw) == object_id and raw.decode("utf-8") == indexed, "Proof object/index integrity mismatch")
            obj = parse_json(raw)
            exact(obj, {"schema_version", "kind", "artifact_id", "capture_id", "created_at", "tool_version", "parents", "payload"}, "proof object")
            require(type(obj["schema_version"]) is int and obj["schema_version"] in (1, 2)
                    and obj["kind"] in ("review", "certificate", "revocation", "resolution"), "Unsupported proof schema/kind")
            require(isinstance(obj["parents"], list) and len(obj["parents"]) <= 2, "Invalid proof parents")
            timestamp(obj["created_at"])
            payload = obj["payload"]
            if obj["kind"] == "review":
                fields = {"gate", "reviewer", "decision", "rationale", "human_attestation", "checks",
                          "evidence_ids", "policy_sha256", "policy_text", "test_report"}
                if obj["schema_version"] == 2:
                    fields.add("resolution_ids")
                exact(payload, fields, "stored review")
                require(not obj["parents"] and payload["gate"] in GATE_MAP, "Invalid review gate/parents")
                exact(payload["checks"], (*CHECKS, SPECIAL[payload["gate"]]), "stored checklist")
                require(all(type(v) is bool for v in payload["checks"].values()), "Invalid stored checklist values")
                require(sha(payload["policy_text"].encode("utf-8")) == payload["policy_sha256"], "Stored policy hash mismatch")
            elif obj["kind"] == "resolution":
                exact(payload, {"gate", "counter_event_id", "state", "reviewer", "rationale", "human_attestation",
                                "evidence_refs", "policy_sha256", "policy_text", "test_report"}, "stored resolution")
                require(obj["schema_version"] == 2 and len(obj["parents"]) <= 1, "Invalid resolution version/history")
                require(payload["state"] in RESOLUTION_STATES and payload["gate"] in GATE_MAP, "Invalid resolution state/gate")
                require(sha(payload["policy_text"].encode("utf-8")) == payload["policy_sha256"], "Stored policy hash mismatch")
            elif obj["kind"] == "certificate":
                exact(payload, {"gate", "scope"}, "stored certificate")
                require(payload["gate"] in GATE_MAP, "Unsupported certificate gate")
            else:
                exact(payload, {"reviewer", "reason", "policy_sha256"}, "stored revocation")
                require(len(obj["parents"]) == 1, "Revocation needs exactly one target")
            result[object_id] = obj
        for object_id, obj in result.items():
            require(all(p in result and p != object_id for p in obj["parents"]), "Missing/self proof parent")
            require(all(result[p]["artifact_id"] == obj["artifact_id"] and result[p]["capture_id"] == obj["capture_id"]
                        for p in obj["parents"]), "Cross-artifact/capture proof dependency")
            if obj["kind"] == "revocation":
                require(result[obj["parents"][0]]["kind"] in ("review", "certificate", "resolution"), "Revocation cannot target a revocation")
            if obj["kind"] == "resolution" and obj["parents"]:
                previous = result[obj["parents"][0]]
                require(previous["kind"] == "resolution" and previous["payload"]["counter_event_id"] == obj["payload"]["counter_event_id"], "Resolution supersedes another counter-evidence record")
                require(timestamp(obj["created_at"]) >= timestamp(previous["created_at"]), "Resolution predates its predecessor")
        return result

    def _put(self, kind, capture, created_at, payload, parents=()):
        self._all()
        bundle = self.runtime.validate_bundle(self.runtime._capture_path(capture))
        obj = {"schema_version": 2 if kind in ("review", "resolution") else 1, "kind": kind, "artifact_id": bundle["manifest"]["artifact_id"],
               "capture_id": capture, "created_at": created_at, "tool_version": tool_version(),
               "parents": list(parents), "payload": payload}
        raw = json_bytes(obj)
        require(len(raw) <= MAX_OBJECT, "Proof object too large")
        object_id = sha(raw)
        path = self._path(object_id)
        db = self._db()
        try:
            with db:
                prior = db.execute("SELECT document FROM proof_objects WHERE id=?", (object_id,)).fetchone()
                if prior is not None:
                    require(prior == (raw.decode(),) and path.read_bytes() == raw, "Existing proof differs")
                    return object_id
                self.objects.mkdir(parents=True, exist_ok=True)
                with path.open("xb") as output:
                    output.write(raw)
                db.execute("INSERT INTO proof_objects VALUES(?,?)", (object_id, raw.decode()))
        finally:
            db.close()
        return object_id

    def _captures(self, artifact):
        db = self.runtime._db()
        try:
            ids = [r[0] for r in db.execute("SELECT id FROM runtime_captures WHERE artifact=?", (artifact,))]
        finally:
            db.close()
        require(len(ids) <= 1024, "Audit exceeds bounded capture capacity")
        return {cid: (self.runtime.assess(cid), self.runtime.validate_bundle(self.runtime._capture_path(cid))) for cid in ids}

    def _resolution_check(self, obj, captures):
        payload = obj["payload"]
        _, bundle = captures[obj["capture_id"]]
        target = next((e for e in bundle["events"] if e["id"] == payload["counter_event_id"]), None)
        require(target is not None and target["type"] == "counter_evidence"
                and target["details"]["gate"] == GATE_MAP[payload["gate"]], "Resolution target does not match counter-evidence")
        require(payload["human_attestation"] is True, "Resolution needs independent human attestation")
        self._authorized(payload["reviewer"], bundle["manifest"]["provenance"]["operator"])
        require(timestamp(obj["created_at"]) >= timestamp(bundle["manifest"]["provenance"]["captured_at"]), "Resolution predates capture")
        require(sha(payload["test_report"]["text"].encode("utf-8")) == payload["test_report"]["sha256"], "Resolution transcript hash mismatch")
        refs = payload["evidence_refs"]
        require(isinstance(refs, list) and len(refs) <= 64, "Invalid resolution evidence references")
        seen = set()
        if payload["state"] == "RESOLVED_SUPPORT":
            require(refs and bundle["manifest"]["provenance"]["source_kind"] == "runtime", "Supporting resolution requires real runtime evidence")
        for ref in refs:
            exact(ref, {"capture_id", "event_id"}, "resolution evidence reference")
            text(ref["capture_id"], "capture reference"); text(ref["event_id"], "event reference")
            key = (ref["capture_id"], ref["event_id"])
            require(key not in seen and ref["capture_id"] in captures, "Duplicate or cross-artifact/missing capture reference")
            seen.add(key)
            assessment, source = captures[ref["capture_id"]]
            require(any(e["id"] == ref["event_id"] and e["type"] != "counter_evidence" for e in source["events"]), "Resolution needs an observed supporting event, not the contradiction itself")
            self._authorized(payload["reviewer"], source["manifest"]["provenance"]["operator"])
            require(timestamp(obj["created_at"]) >= timestamp(source["manifest"]["provenance"]["captured_at"]), "Resolution predates supporting capture")
            if payload["state"] == "RESOLVED_SUPPORT":
                provenance = source["manifest"]["provenance"]
                require(source["manifest"]["schema_version"] == 2 and provenance["source_kind"] == "runtime"
                        and not provenance["handling"]["redacted"], "Supporting evidence must be unredacted runtime v2")
                require(any(f["role"] == "raw_trace" and f["data"] for f in source["files"].values()), "Supporting evidence lacks native trace")
                require(ref["event_id"] in assessment["gates"][GATE_MAP[payload["gate"]]]["evidence_ids"], "Supporting event fails gate mechanical checks")

    def _context(self, artifact, objects):
        captures = self._captures(artifact)
        revoked = {o["parents"][0] for o in objects.values() if o["kind"] == "revocation"}
        states, accepted = [], {cid: set() for cid in captures}
        version = tool_version()
        for cid, (_, bundle) in captures.items():
            for event in bundle["events"]:
                if event["type"] != "counter_evidence":
                    continue
                candidates = {oid: o for oid, o in objects.items() if o["kind"] == "resolution"
                              and o["capture_id"] == cid and o["payload"]["counter_event_id"] == event["id"]}
                heads = set(candidates) - {p for o in candidates.values() for p in o["parents"]}
                state, reason, resolution = "OPEN", "No reviewed resolution", None
                if len(heads) == 1:
                    resolution = next(iter(heads))
                    obj = candidates[resolution]
                    try:
                        require(resolution not in revoked, "Resolution revoked; contradiction reopened")
                        require(obj["tool_version"] == version, "Resolution validator changed; re-review required")
                        self._resolution_check(obj, captures)
                        state, reason = obj["payload"]["state"], "Independent local review recorded"
                    except (ValueError, OSError, KeyError, TypeError) as error:
                        reason = str(error)
                elif heads:
                    reason = "Conflicting resolution heads; fail closed"
                active = bundle["manifest"]["provenance"]["source_kind"] == "runtime"
                if active and state == "RESOLVED_SUPPORT":
                    accepted[cid].add(event["id"])
                states.append({"capture_id": cid, "event_id": event["id"], "gate": event["details"]["gate"],
                               "state": state, "resolution_id": resolution, "reason": reason, "applies_to_runtime": active})
        derived = {cid: (assess_bundle(bundle, resolved_counter_ids=accepted[cid]), bundle) for cid, (_, bundle) in captures.items()}
        return derived, states

    @staticmethod
    def _acknowledgments(states, gate):
        return sorted(s["resolution_id"] for s in states if s["applies_to_runtime"] and s["gate"] == GATE_MAP[gate] and s["state"] == "RESOLVED_SUPPORT")

    def prepare_resolution(self, capture, event_id, destination):
        bundle = self.runtime.validate_bundle(self.runtime._capture_path(capture))
        self.runtime.assess(capture)
        event = next((e for e in bundle["events"] if e["id"] == event_id), None)
        require(event is not None and event["type"] == "counter_evidence" and event["details"]["gate"] in GATE_MAP.values(), "Unsupported/missing counter-evidence target")
        objects = self._all()
        _, states = self._context(bundle["manifest"]["artifact_id"], objects)
        current = next(s for s in states if s["capture_id"] == capture and s["event_id"] == event_id)
        request = {"schema_version": 1, "capture_id": capture, "counter_event_id": event_id,
                   "state": None, "reviewer": None, "reviewed_at": None, "rationale": None,
                   "human_attestation": False, "evidence_refs": [], "test_report": "resolution-report.txt",
                   "supersedes": current["resolution_id"]}
        with Path(destination).open("xb") as output:
            output.write(json_bytes(request))
        return request

    def resolve(self, path):
        path = Path(path).resolve(strict=True)
        request = parse_json(read_limit(path, 65536))
        exact(request, {"schema_version", "capture_id", "counter_event_id", "state", "reviewer", "reviewed_at",
                        "rationale", "human_attestation", "evidence_refs", "test_report", "supersedes"}, "resolution request")
        require(type(request["schema_version"]) is int and request["schema_version"] == 1, "Unsupported resolution request")
        require(request["state"] in RESOLUTION_STATES, "Invalid resolution state")
        text(request["rationale"], "resolution rationale", 4096)
        bundle = self.runtime.validate_bundle(self.runtime._capture_path(request["capture_id"]))
        event = next((e for e in bundle["events"] if e["id"] == request["counter_event_id"] and e["type"] == "counter_evidence"), None)
        require(event is not None and event["details"]["gate"] in GATE_MAP.values(), "Missing/unsupported counter-evidence")
        gate = next(k for k, v in GATE_MAP.items() if v == event["details"]["gate"])
        policy_hash = self._authorized(request["reviewer"], bundle["manifest"]["provenance"]["operator"])
        transcript = read_limit(safe_file(path.parent, request["test_report"]), 256 * 1024)
        require(transcript.strip(), "Resolution requires reproduction/review transcript")
        payload = {k: request[k] for k in ("counter_event_id", "state", "reviewer", "rationale", "human_attestation", "evidence_refs")}
        payload.update(gate=gate, policy_sha256=policy_hash,
                       policy_text=read_limit(safe_file(self.root, "review-policy.json"), 16384).decode("utf-8"),
                       test_report={"sha256": sha(transcript), "text": transcript.decode("utf-8")})
        require(sha(payload["policy_text"].encode()) == policy_hash, "Policy changed during resolution")
        objects = self._all()
        parents = [] if request["supersedes"] is None else [request["supersedes"]]
        for oid, obj in objects.items():
            if obj["kind"] == "resolution" and obj["capture_id"] == request["capture_id"] and obj["payload"] == payload and obj["parents"] == parents and obj["created_at"] == request["reviewed_at"] and obj["tool_version"] == tool_version():
                return oid
        candidates = {oid: o for oid, o in objects.items() if o["kind"] == "resolution" and o["capture_id"] == request["capture_id"] and o["payload"]["counter_event_id"] == request["counter_event_id"]}
        heads = set(candidates) - {p for o in candidates.values() for p in o["parents"]}
        require(set(parents) == heads and len(heads) <= 1, "Resolution must explicitly supersede the current head; branching forbidden")
        if parents:
            require(timestamp(request["reviewed_at"]) >= timestamp(objects[parents[0]]["created_at"]), "Resolution predates predecessor")
        captures = self._captures(bundle["manifest"]["artifact_id"])
        self._resolution_check({"capture_id": request["capture_id"], "created_at": request["reviewed_at"], "payload": payload}, captures)
        return self._put("resolution", request["capture_id"], request["reviewed_at"], payload, parents)

    def prepare(self, capture, gate, destination):
        require(gate in GATE_MAP, "Promotion is implemented only for G02-G04.5")
        artifact = self.runtime.assess(capture)["artifact_id"]
        captures, states = self._context(artifact, self._all())
        assessment = captures[capture][0]
        request = {"schema_version": 2, "capture_id": capture, "gate": gate, "reviewer": None,
                   "reviewed_at": None, "decision": None, "rationale": None, "human_attestation": False,
                   "checks": {key: False for key in (*CHECKS, SPECIAL[gate])},
                   "evidence_ids": assessment["gates"][GATE_MAP[gate]]["evidence_ids"], "test_report": "test-report.txt",
                   "resolution_ids": self._acknowledgments(states, gate)}
        with Path(destination).open("xb") as output:
            output.write(json_bytes(request))
        return request

    def submit(self, path):
        path = Path(path).resolve(strict=True)
        request = parse_json(read_limit(path, 65536))
        exact(request, {"schema_version", "capture_id", "gate", "reviewer", "reviewed_at", "decision", "rationale",
                        "human_attestation", "checks", "evidence_ids", "test_report", "resolution_ids"}, "review request")
        require(type(request["schema_version"]) is int and request["schema_version"] == 2, "Prepare a version 2 review request")
        gate = request["gate"]
        require(isinstance(gate, str) and gate in GATE_MAP, "Unsupported review gate")
        require(request["human_attestation"] is True, "Explicit human review attestation required")
        require(request["decision"] in ("APPROVE", "REJECT"), "Review must APPROVE or REJECT")
        text(request["rationale"], "review rationale", 4096)
        bundle = self.runtime.validate_bundle(self.runtime._capture_path(request["capture_id"]))
        captures, states = self._context(bundle["manifest"]["artifact_id"], self._all())
        assessment = captures[request["capture_id"]][0]
        provenance = bundle["manifest"]["provenance"]
        require(timestamp(request["reviewed_at"]) >= timestamp(provenance["captured_at"]), "Review predates capture")
        policy_hash = self._authorized(request["reviewer"], provenance["operator"])
        checks = request["checks"]
        exact(checks, (*CHECKS, SPECIAL[gate]), "human review checklist")
        require(all(type(v) is bool for v in checks.values()), "Checklist needs booleans")
        refs = request["evidence_ids"]
        require(isinstance(refs, list) and 1 <= len(refs) <= 100 and all(isinstance(e, str) for e in refs)
                and len(set(refs)) == len(refs), "Review needs unique evidence IDs")
        require(set(refs) <= {e["id"] for e in bundle["events"]}, "Review references missing events")
        if request["decision"] == "APPROVE":
            require(request["resolution_ids"] == self._acknowledgments(states, gate), "Review must acknowledge current supporting resolutions")
            require(not any(s["applies_to_runtime"] and s["gate"] == GATE_MAP[gate] and s["state"] != "RESOLVED_SUPPORT" for s in states), "Open/rejected/inconclusive counter-evidence blocks approval")
            require(provenance["source_kind"] == "runtime", "Synthetic capture cannot be approved")
            require(all(checks.values()), "All independent review checks must pass")
            result = assessment["gates"][GATE_MAP[gate]]
            require(result["status"] == "READY_FOR_REVIEW", "Gate is not consistency-ready")
            require(set(result["evidence_ids"]) <= set(refs), "Review omits gate evidence")
        transcript = read_limit(safe_file(path.parent, request["test_report"]), 256 * 1024)
        require(transcript.strip(), "Missing regression/reproduction transcript")
        payload = {k: v for k, v in request.items() if k not in ("schema_version", "capture_id", "reviewed_at", "test_report")}
        payload["policy_sha256"] = policy_hash
        payload["policy_text"] = read_limit(safe_file(self.root, "review-policy.json"), 16384).decode("utf-8")
        require(sha(payload["policy_text"].encode("utf-8")) == policy_hash, "Review policy changed during submission")
        payload["test_report"] = {"sha256": sha(transcript), "text": transcript.decode("utf-8")}
        return self._put("review", request["capture_id"], request["reviewed_at"], payload)

    def audit(self, object_id):
        objects = self._all()
        require(object_id in objects, "Unknown proof object")
        revoked = {o["parents"][0] for o in objects.values() if o["kind"] == "revocation" and o["parents"]}
        memo = {}
        version = tool_version()
        artifact = objects[object_id]["artifact_id"]
        captures, states = self._context(artifact, objects)
        counter_gates = {s["gate"] for s in states if s["applies_to_runtime"] and s["state"] != "RESOLVED_SUPPORT"}

        def visit(oid, ancestry=()):
            require(oid not in ancestry and len(ancestry) < 32, "Proof dependency cycle/depth limit")
            if oid in memo:
                return memo[oid]
            obj = objects[oid]
            reasons = []
            parents = [visit(p, (*ancestry, oid)) for p in obj["parents"]]
            if obj["kind"] not in ("revocation", "resolution") and any(p["status"] != "VALID" for p in parents):
                reasons.append("Dependency invalid; dependent certificate is unusable")
            if oid in revoked:
                reasons.append("Explicitly revoked")
            if obj["kind"] != "revocation" and obj["tool_version"] != version:
                reasons.append("Validator version changed; independent re-review required")
            capture = obj["capture_id"]
            if capture not in captures:
                captures[capture] = (self.runtime.assess(capture), self.runtime.validate_bundle(self.runtime._capture_path(capture)))
            assessment, bundle = captures[capture]
            require(obj["artifact_id"] == bundle["manifest"]["artifact_id"], "Proof artifact mismatch")
            payload = obj["payload"]
            if obj["kind"] == "review":
                try:
                    self._authorized(payload["reviewer"], bundle["manifest"]["provenance"]["operator"])
                except (ValueError, OSError) as error:
                    reasons.append(str(error))
                if payload["decision"] != "APPROVE":
                    reasons.append("Review rejected")
                if not all(payload["checks"].values()) or payload["human_attestation"] is not True:
                    reasons.append("Review checklist/attestation incomplete")
                if sha(payload["test_report"]["text"].encode("utf-8")) != payload["test_report"]["sha256"]:
                    reasons.append("Review test transcript changed")
                gate = payload["gate"]
                if assessment["gates"][GATE_MAP[gate]]["status"] != "READY_FOR_REVIEW":
                    reasons.append("Runtime consistency no longer ready")
                if GATE_MAP[gate] in counter_gates:
                    reasons.append("Unresolved runtime counter-evidence for this artifact/gate")
                if payload.get("resolution_ids", []) != self._acknowledgments(states, gate):
                    reasons.append("Review does not acknowledge current resolutions; independent re-review required")
                if any(o["kind"] == "review" and o["artifact_id"] == obj["artifact_id"] and o["payload"]["gate"] == gate
                       and o["payload"]["decision"] == "REJECT" and other not in revoked for other, o in objects.items()):
                    reasons.append("Unresolved rejection for this capture/gate")
            elif obj["kind"] == "resolution":
                state = next(s for s in states if s["capture_id"] == capture and s["event_id"] == payload["counter_event_id"])
                if state["resolution_id"] != oid:
                    reasons.append("SUPERSEDED resolution; retained as history")
                elif state["reason"] != "Independent local review recorded":
                    reasons.append(state["reason"])
            elif obj["kind"] == "certificate":
                gate = payload["gate"]
                index = list(GATE_MAP).index(gate)
                require(len(obj["parents"]) == (2 if index else 1), "Wrong certificate dependency count")
                review = objects[obj["parents"][0]]
                require(review["kind"] == "review" and review["payload"]["gate"] == gate, "Certificate lacks matching review")
                if index:
                    previous = objects[obj["parents"][1]]
                    require(previous["kind"] == "certificate" and previous["payload"]["gate"] == list(GATE_MAP)[index - 1], "Certificate skips prerequisite gate")
            result = {"object_id": oid, "kind": obj["kind"], "status": "INVALID" if reasons else "VALID",
                      "artifact_id": obj["artifact_id"], "capture_id": capture, "reasons": reasons,
                      "parents": parents, "payload": {**payload, **({"test_report": {"sha256": payload["test_report"]["sha256"], "content": "RESTRICTED_NOT_EMITTED"}} if "test_report" in payload else {})},
                      "authority": "LOCAL_HUMAN_REVIEW_POLICY_NOT_CRYPTOGRAPHIC_IDENTITY"}
            memo[oid] = result
            return result
        result = visit(object_id)
        affected = {object_id}
        while True:
            expanded = affected | {oid for oid, obj in objects.items() if set(obj["parents"]) & affected}
            if expanded == affected:
                break
            affected = expanded
        result["affected_dependents"] = sorted(affected - {object_id})
        return result

    def promote(self, review_id, prerequisite=None):
        audited = self.audit(review_id)
        require(audited["kind"] == "review" and audited["status"] == "VALID", "Review is not valid for promotion")
        review = self._all()[review_id]
        gate = review["payload"]["gate"]
        index = list(GATE_MAP).index(gate)
        parents = [review_id]
        if index:
            require(prerequisite is not None, "Previous gate certificate required")
            previous = self.audit(prerequisite)
            require(previous["kind"] == "certificate" and previous["status"] == "VALID"
                    and previous["capture_id"] == review["capture_id"]
                    and previous["payload"]["gate"] == list(GATE_MAP)[index - 1], "Invalid prerequisite certificate")
            parents.append(prerequisite)
        else:
            require(prerequisite is None, "G02 binds directly to the verified artifact and capture")
        certificate = self._put("certificate", review["capture_id"], review["created_at"],
                                {"gate": gate, "scope": "LOCAL_REVIEWED_RUNTIME_GATE_NOT_PROTOCOL_COMPATIBILITY"}, parents)
        require(self.audit(certificate)["status"] == "VALID", "Certificate is invalid/revoked; cannot reissue silently")
        return certificate

    def revoke(self, object_id, reviewer, reason):
        objects = self._all()
        require(object_id in objects and objects[object_id]["kind"] in ("review", "certificate", "resolution"), "Only reviews/certificates/resolutions can be revoked")
        policy_hash = self._authorized(reviewer)
        text(reason, "revocation rationale", 4096)
        return self._put("revocation", objects[object_id]["capture_id"], datetime.now(timezone.utc).isoformat(),
                         {"reviewer": reviewer, "reason": reason, "policy_sha256": policy_hash}, [object_id])

    def status(self, artifact):
        self.runtime.vault.verify(artifact)
        objects = self._all()
        _, counter_evidence = self._context(artifact, objects)
        certificates = [self.audit(oid) for oid, obj in objects.items() if obj["artifact_id"] == artifact and obj["kind"] == "certificate"]
        valid = {c["payload"]["gate"] for c in certificates if c["status"] == "VALID"}
        revoked = {o["parents"][0] for o in objects.values() if o["kind"] == "revocation"}
        reviews = [{"id": oid, "capture_id": obj["capture_id"], "gate": obj["payload"]["gate"],
                    "decision": obj["payload"]["decision"], "reviewer": obj["payload"]["reviewer"],
                    "rationale": obj["payload"]["rationale"], "revoked": oid in revoked}
                   for oid, obj in objects.items() if obj["kind"] == "review" and obj["artifact_id"] == artifact]
        gates = {gate: "VERIFIED" if gate in valid else "BLOCKED" for gate in GATE_MAP}
        highest = "L1 ARTIFACT_VERIFIED"
        for gate, level in zip(GATE_MAP, ("L2 UNPACK_VERIFIED", "L3 OEP_VERIFIED", "L4 IAT_VERIFIED", "L5 ANALYSIS_IMAGE_VERIFIED")):
            if gate not in valid:
                break
            highest = level
        return {"artifact_id": artifact, "highest_acceptance": highest, "gates": gates,
                "certificates": certificates, "reviews": reviews, "counter_evidence": counter_evidence,
                "next_gate": next((g for g in GATE_MAP if g not in valid), "G05"),
                "next_external_evidence": "Controlled runtime capture and independent human review; no AI promotion.",
                "authority": "LOCAL_HUMAN_REVIEW_POLICY_NOT_CRYPTOGRAPHIC_IDENTITY",
                "scope_limit": "No G05/network-root or protocol compatibility certificate issuer yet."}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2] / "artifacts")
    sub = parser.add_subparsers(dest="command", required=True)
    prepare = sub.add_parser("prepare"); prepare.add_argument("capture"); prepare.add_argument("gate", choices=GATE_MAP); prepare.add_argument("destination", type=Path)
    submit = sub.add_parser("submit"); submit.add_argument("request", type=Path)
    prepare_resolution = sub.add_parser("prepare-resolution"); prepare_resolution.add_argument("capture"); prepare_resolution.add_argument("event"); prepare_resolution.add_argument("destination", type=Path)
    resolve = sub.add_parser("resolve"); resolve.add_argument("request", type=Path)
    promote = sub.add_parser("promote"); promote.add_argument("review"); promote.add_argument("--prerequisite")
    audit = sub.add_parser("audit"); audit.add_argument("object_id")
    status = sub.add_parser("status"); status.add_argument("artifact")
    revoke = sub.add_parser("revoke"); revoke.add_argument("object_id"); revoke.add_argument("--reviewer", required=True); revoke.add_argument("--reason", required=True)
    args = parser.parse_args(argv)
    try:
        store = ReviewStore(args.root)
        if args.command == "prepare":
            result = store.prepare(args.capture, args.gate, args.destination)
        elif args.command == "submit":
            result = {"review_id": store.submit(args.request), "promoted": False}
        elif args.command == "prepare-resolution":
            result = store.prepare_resolution(args.capture, args.event, args.destination)
        elif args.command == "resolve":
            result = {"resolution_id": store.resolve(args.request), "promoted": False}
        elif args.command == "promote":
            result = {"certificate_id": store.promote(args.review, args.prerequisite)}
        elif args.command == "revoke":
            result = {"revocation_id": store.revoke(args.object_id, args.reviewer, args.reason)}
        elif args.command == "audit":
            result = store.audit(args.object_id)
        else:
            result = store.status(args.artifact)
        if args.command in ("submit", "promote", "revoke", "resolve"):
            object_id = next(iter(result.values()))
            artifact = store._all()[object_id]["artifact_id"]
            report_path = store.root / "reports" / ("review-" + uuid.uuid4().hex)
            store.runtime.report(artifact, report_path)
            result["reports"] = str(report_path)
        print(json.dumps(result, indent=2))
        return 2 if args.command == "audit" and result["status"] != "VALID" else 0
    except (ValueError, OSError, KeyError, TypeError, sqlite3.Error) as error:
        print(f"Gate review error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
