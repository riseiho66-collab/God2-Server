"""GOD2 APEX offline runtime intake, consistency assessment and generated status."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
import sys
import tempfile
import uuid

from artifact_vault import Vault, json_bytes, inspect_pe
from runtime_contract import (SHA, GATES, MAX_TOTAL, require, read_limit, safe_file, parse_json,
                              validate_manifest, validate_events)
from runtime_checks import assess_bundle
from gate_review import ReviewStore


class RuntimeStore:
    def __init__(self, vault_root):
        self.vault = Vault(vault_root)
        self.root = self.vault.root
        self.captures = self.root / "runtime"

    def _db(self):
        db = self.vault.connect()
        try:
            with db:
                db.execute("CREATE TABLE IF NOT EXISTS runtime_schema(version INTEGER PRIMARY KEY CHECK(version=1))")
                db.execute("INSERT OR IGNORE INTO runtime_schema VALUES(1)")
                require(db.execute("SELECT version FROM runtime_schema").fetchall() == [(1,)], "Unsupported runtime schema")
                db.execute("CREATE TABLE IF NOT EXISTS runtime_captures(id TEXT PRIMARY KEY, artifact TEXT NOT NULL REFERENCES artifacts(id), session_id TEXT NOT NULL, source_kind TEXT NOT NULL, event_count INTEGER NOT NULL, UNIQUE(artifact,session_id))")
                db.execute("CREATE TABLE IF NOT EXISTS runtime_events(capture TEXT NOT NULL REFERENCES runtime_captures(id), event_id TEXT NOT NULL, type TEXT NOT NULL, payload TEXT NOT NULL, PRIMARY KEY(capture,event_id))")
                db.execute("CREATE TABLE IF NOT EXISTS runtime_functions(id TEXT PRIMARY KEY, artifact TEXT NOT NULL REFERENCES artifacts(id), capture TEXT NOT NULL REFERENCES runtime_captures(id), rva INTEGER NOT NULL, code_sha256 TEXT NOT NULL, confidence TEXT NOT NULL CHECK(confidence='HYPOTHESIS'), UNIQUE(capture,rva,code_sha256))")
            return db
        except Exception:
            db.close()
            raise

    def prepare(self, artifact_id, destination):
        metadata = self.vault.verify(artifact_id)
        require(metadata["pe"]["architecture"] == "x86", "Runtime preparation supports x86 clients")
        destination = Path(destination).absolute()
        require(not destination.exists(), "Capture request destination already exists")
        destination.mkdir(parents=True)
        manifest = {"schema_version": 2, "artifact_id": artifact_id, "session_id": "CAPTURE-" + uuid.uuid4().hex,
                    "provenance": {"tool": "x32dbg", "tool_version": "FILL_FROM_TOOL", "operator": "FILL_FROM_OPERATOR",
                                   "captured_at": None, "environment_id": "FILL_FROM_ISOLATED_ENVIRONMENT",
                                   "isolation": "offline", "source_kind": "runtime", "adapter": "god2-normalized-v1",
                                   "working_copy_sha256": None, "handling": {"sensitive": True, "redacted": False, "restricted": True}},
                    "process": {"pid": None, "architecture": "x86", "module_base": None, "image_size": metadata["pe"]["size_of_image"]},
                    "scope": {"purpose": "network-reconstruction", "ranges": []},
                    "files": [{"path": "events.jsonl", "role": "events", "size": 0, "sha256": hashlib.sha256(b"").hexdigest()}]}
        request = {"status": "AWAITING_CONTROLLED_CAPTURE", "artifact_id": artifact_id,
                   "single_external_evidence": "One controlled x86 capture bundle: native trace, normalized events, mapped dump, unpacked candidate, and manifest bound to this artifact.",
                   "preferred_base_not_runtime_base": metadata["pe"]["image_base"],
                   "packed_entry_rva": metadata["pe"]["entry_rva"],
                   "oep_candidate_rva_unverified": 0x14A3E8 if artifact_id == "fb72296cab5950b74d8f7c98155145f7c5f58749c3011adb0540325b60749dd1" else None,
                   "source": str(self.vault.location(artifact_id) / metadata["kind"] / "client.exe"),
                   "instructions": ["Use an isolated working copy with its required client resources; do not execute the vault copy.",
                                    "Record actual base and process ID from the debugger, not PE preferred addresses.",
                                    "Measure WorkingCopySHA256 before launch and verify equality to OriginalArtifactSHA256; do not copy the expected hash without measuring.",
                                    "Keep sensitive raw evidence in an access-controlled local workspace; handling flags do not enforce ACLs.",
                                    "Capture only unpack transition and the network reconstruction scope.",
                                    "Preserve native logs, mapped image and repaired image separately.",
                                    "Normalize observations according to runtime_contract.py; never fill missing observations with guesses.",
                                    "Fill exact file sizes and SHA256 hashes. The template itself cannot be ingested."]}
        (destination / "manifest.json").write_bytes(json_bytes(manifest))
        (destination / "capture_request.json").write_bytes(json_bytes(request))
        (destination / "events.jsonl").write_bytes(b"")
        return request

    def seal(self, path, destination):
        """Hash a completed capture worksheet into a new, validated bundle."""
        source = Path(path).resolve(strict=True)
        manifest = parse_json(read_limit(safe_file(source, "manifest.json"), 1024 * 1024))
        validate_manifest(manifest)
        destination = Path(destination).absolute()
        require(not destination.exists(), "Sealed bundle destination already exists")
        contents, total = {}, 0
        for item in manifest["files"]:
            data = read_limit(safe_file(source, item["path"]), 128 * 1024 * 1024)
            total += len(data)
            require(total <= MAX_TOTAL, "Bundle size limit exceeded")
            item.update(size=len(data), sha256=hashlib.sha256(data).hexdigest())
            contents[item["path"]] = data
        validate_manifest(manifest)
        destination.parent.mkdir(parents=True, exist_ok=True)
        staging = Path(tempfile.mkdtemp(prefix=".seal-", dir=destination.parent))
        try:
            (staging / "manifest.json").write_bytes(json_bytes(manifest))
            for name, data in contents.items():
                output = safe_file(staging, name)
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_bytes(data)
            bundle = self.validate_bundle(staging)
            staging.rename(destination)
            return {"capture_id": bundle["capture_id"], "bundle": str(destination), "trust": "UNREVIEWED"}
        finally:
            if staging.exists():
                require(staging.resolve().parent == destination.parent.resolve() and staging.name.startswith(".seal-"), "Unsafe seal staging cleanup")
                shutil.rmtree(staging)

    def validate_bundle(self, path):
        root = Path(path).resolve(strict=True)
        manifest_path = safe_file(root, "manifest.json")
        raw_manifest = read_limit(manifest_path, 1024 * 1024)
        manifest = parse_json(raw_manifest)
        validate_manifest(manifest)
        artifact = self.vault.verify(manifest["artifact_id"])
        require(artifact["pe"]["architecture"] == manifest["process"]["architecture"], "Artifact/process architecture mismatch")
        require(artifact["pe"]["size_of_image"] == manifest["process"]["image_size"], "Runtime image size differs from source artifact")
        files = {}
        for item in manifest["files"]:
            attachment = safe_file(root, item["path"])
            data = read_limit(attachment, item["size"])
            require(len(data) == item["size"] and hashlib.sha256(data).hexdigest() == item["sha256"], f"Attachment hash/size mismatch: {item['path']}")
            if item["role"] in ("unpacked_pe", "repaired_pe", "module_pe"):
                inspect_pe(data)
            files[item["path"]] = {**item, "data": data}
        event_file = next(f for f in files.values() if f["role"] == "events")
        require(len(event_file["data"]) <= 32 * 1024 * 1024, "Events exceed 32 MiB")
        events = validate_events(event_file["data"], manifest, files)
        require(events, "A capture must contain observed events")
        capture_id = hashlib.sha256(raw_manifest).hexdigest()
        return {"capture_id": capture_id, "manifest": manifest, "raw_manifest": raw_manifest, "files": files, "events": events}

    def _capture_path(self, capture_id):
        require(isinstance(capture_id, str) and SHA.fullmatch(capture_id), "Invalid capture ID")
        path = self.captures / capture_id
        require(path.resolve() == path, "Capture path must not be a symlink/reparse point")
        return path

    def ingest(self, path):
        bundle = self.validate_bundle(path)
        capture_id = bundle["capture_id"]
        target = self._capture_path(capture_id)
        manifest = bundle["manifest"]
        db = self._db()
        try:
            if db.execute("SELECT 1 FROM runtime_captures WHERE id=?", (capture_id,)).fetchone():
                self.assess(capture_id)
                return capture_id
            with db:
                db.execute("INSERT OR IGNORE INTO runtime_captures VALUES(?,?,?,?,?)", (capture_id, manifest["artifact_id"], manifest["session_id"], manifest["provenance"]["source_kind"], len(bundle["events"])))
                row = db.execute("SELECT id FROM runtime_captures WHERE artifact=? AND session_id=?", (manifest["artifact_id"], manifest["session_id"])).fetchone()
                require(row == (capture_id,), "Session ID already belongs to another capture; use a new session ID")
                self.captures.mkdir(parents=True, exist_ok=True)
                if target.exists():
                    require(self.validate_bundle(target)["capture_id"] == capture_id, "Stored capture identity mismatch")
                else:
                    staging = Path(tempfile.mkdtemp(prefix=".runtime-", dir=self.captures))
                    try:
                        (staging / "manifest.json").write_bytes(bundle["raw_manifest"])
                        for name, item in bundle["files"].items():
                            output = safe_file(staging, name)
                            output.parent.mkdir(parents=True, exist_ok=True)
                            output.write_bytes(item["data"])
                        staging.rename(target)
                    finally:
                        if staging.exists():
                            require(staging.resolve().parent == self.captures.resolve() and staging.name.startswith(".runtime-"), "Unsafe runtime staging cleanup")
                            shutil.rmtree(staging)
                for event in bundle["events"]:
                    payload = json_bytes(event).decode()
                    prior = db.execute("SELECT payload FROM runtime_events WHERE capture=? AND event_id=?", (capture_id, event["id"])).fetchone()
                    require(prior is None or prior == (payload,), "Runtime event index conflict")
                    db.execute("INSERT OR IGNORE INTO runtime_events VALUES(?,?,?,?)", (capture_id, event["id"], event["type"], payload))
                    if event["type"] == "function_enter":
                        code_hash = hashlib.sha256(bytes.fromhex(event["details"]["bytes_hex"])).hexdigest()
                        db.execute("INSERT OR IGNORE INTO runtime_functions VALUES(?,?,?,?,?,?)", ("FUNC-" + uuid.uuid4().hex, manifest["artifact_id"], capture_id, event["pc"] - manifest["process"]["module_base"], code_hash, "HYPOTHESIS"))
        finally:
            db.close()
        return capture_id

    def assess(self, capture_id):
        bundle = self.validate_bundle(self._capture_path(capture_id))
        require(bundle["capture_id"] == capture_id, "Stored capture manifest changed")
        db = self._db()
        try:
            row = db.execute("SELECT artifact,session_id,source_kind,event_count FROM runtime_captures WHERE id=?", (capture_id,)).fetchone()
            m = bundle["manifest"]
            require(row == (m["artifact_id"], m["session_id"], m["provenance"]["source_kind"], len(bundle["events"])), "Runtime capture index mismatch")
            indexed = db.execute("SELECT event_id,type,payload FROM runtime_events WHERE capture=? ORDER BY event_id", (capture_id,)).fetchall()
            expected = sorted((e["id"], e["type"], json_bytes(e).decode()) for e in bundle["events"])
            require(indexed == expected, "Runtime event index mismatch")
            functions = db.execute("SELECT artifact,rva,code_sha256,confidence FROM runtime_functions WHERE capture=?", (capture_id,)).fetchall()
            expected_functions = {(m["artifact_id"], e["pc"] - m["process"]["module_base"],
                                   hashlib.sha256(bytes.fromhex(e["details"]["bytes_hex"])).hexdigest(), "HYPOTHESIS")
                                  for e in bundle["events"] if e["type"] == "function_enter"}
            require(len(functions) == len(expected_functions) and set(functions) == expected_functions, "Runtime function index mismatch")
        finally:
            db.close()
        return {"capture_id": capture_id, **assess_bundle(bundle)}

    def status(self, artifact_id):
        self.vault.verify(artifact_id)
        db = self._db()
        try:
            captures = [row[0] for row in db.execute("SELECT id FROM runtime_captures WHERE artifact=? ORDER BY id", (artifact_id,))]
            functions = db.execute("SELECT id,capture,rva,code_sha256,confidence FROM runtime_functions WHERE artifact=? ORDER BY id", (artifact_id,)).fetchall()
        finally:
            db.close()
        assessments = [self.assess(capture) for capture in captures]
        review = ReviewStore(self.root).status(artifact_id)
        return {"artifact_id": artifact_id, "classification": "Research / Partial Compatibility",
                "highest_runtime_acceptance": review["highest_acceptance"], "current_gate": review["next_gate"].removeprefix("G"), "status": "BLOCKED",
                "single_external_evidence": "A controlled runtime capture bundle with native trace and mapped/unpacked images, followed by independent review.",
                "review_audit": review,
                "captures": assessments, "function_candidates": [dict(zip(("id", "capture", "rva", "code_sha256", "confidence"), row)) for row in functions],
                "coverage": {"runtime_captures": len(captures), "verified_packets": 0, "total_real_packets": None,
                             "verified_fields": 0, "total_real_fields": None,
                             "verified_runtime_gates": sum(v == "VERIFIED" for v in review["gates"].values())}}

    def report(self, artifact_id, destination):
        state = self.status(artifact_id)
        destination = Path(destination).absolute()
        require(not destination.exists(), "Report destination already exists; use a new snapshot directory")
        destination.mkdir(parents=True)
        (destination / "status.json").write_bytes(json_bytes(state))
        header = f"Generated from the verified vault and runtime research index.\n\nArtifact: `{artifact_id}`\n\nClassification: Research / Partial Compatibility.\n\n"
        gates = "| Gate | Status | Reason |\n| --- | --- | --- |\n"
        for gate, gate_id in zip(GATES, ("G02", "G03", "G04", "G04.5", "G05")):
            eligible = sum(c["gates"][gate]["status"] == "READY_FOR_REVIEW" for c in state["captures"])
            verdict = state["review_audit"]["gates"].get(gate_id, "BLOCKED")
            reason = "Valid local human-review certificate; see status.json" if verdict == "VERIFIED" else f"{eligible} consistency-ready captures; valid independent review/certificate missing"
            gates += f"| {gate} | {verdict} | {reason} |\n"
        reports = {
            "RECONSTRUCTION_STATUS.md": header + gates + "\nSingle external evidence required: " + state["single_external_evidence"] + "\n",
            "GOD2_PROTOCOL_SPEC.md": header + "Verified runtime contracts: 0. Total required contracts: unknown. No real protocol generated.\n",
            "OPCODE_TABLE.md": header + "Verified real opcodes: 0. Mock opcodes are not research evidence.\n",
            "STATE_MACHINE.md": header + "No verified client state transitions. Observed state labels in a capture are unreviewed annotations.\n",
            "UNKNOWN_FIELDS.md": header + "Critical blockers, in order: unpack transition, OEP execution, IAT resolution, analysis-image quality, network callers. All real packet fields remain unresolved.\n",
        }
        contradictions = []
        for review in state["review_audit"]["reviews"]:
            if review["decision"] == "REJECT":
                disposition = "revoked rejection (retained history)" if review["revoked"] else "unresolved rejection"
                contradictions.append(f"- {review['id']} / {review['gate']}: {disposition}: {review['rationale']}")
        for counter in state["review_audit"]["counter_evidence"]:
            contradictions.append(f"- {counter['capture_id']} / {counter['event_id']} / {counter['gate']}: "
                                  f"{counter['state']}; resolution={counter['resolution_id']}; {counter['reason']}")
        reports["CONTRADICTIONS.md"] = header + ("\n".join(contradictions) if contradictions else "No counter-evidence records imported. This does not prove the absence of contradictions.") + "\n"
        for name, content in reports.items():
            (destination / name).write_text("# " + name.removesuffix(".md").replace("_", " ").title() + "\n\n" + content, encoding="utf-8")
        return state


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2] / "artifacts")
    sub = parser.add_subparsers(dest="command", required=True)
    prepare = sub.add_parser("prepare"); prepare.add_argument("artifact"); prepare.add_argument("destination", type=Path)
    validate = sub.add_parser("validate"); validate.add_argument("bundle", type=Path)
    seal = sub.add_parser("seal"); seal.add_argument("bundle", type=Path); seal.add_argument("destination", type=Path)
    ingest = sub.add_parser("ingest"); ingest.add_argument("bundle", type=Path)
    assess = sub.add_parser("assess"); assess.add_argument("capture")
    status = sub.add_parser("status"); status.add_argument("artifact")
    report = sub.add_parser("report"); report.add_argument("artifact"); report.add_argument("destination", type=Path)
    args = parser.parse_args(argv)
    try:
        store = RuntimeStore(args.root)
        if args.command == "prepare":
            result = store.prepare(args.artifact, args.destination)
        elif args.command == "validate":
            bundle = store.validate_bundle(args.bundle)
            result = {"capture_id": bundle["capture_id"], "events": len(bundle["events"]), "trust": "UNREVIEWED"}
        elif args.command == "seal":
            result = store.seal(args.bundle, args.destination)
        elif args.command == "ingest":
            capture_id = store.ingest(args.bundle)
            artifact_id = store.assess(capture_id)["artifact_id"]
            report_path = store.root / "reports" / ("runtime-" + uuid.uuid4().hex)
            store.report(artifact_id, report_path)
            result = {"capture_id": capture_id, "trust": "UNREVIEWED", "reports": str(report_path)}
        elif args.command == "assess":
            result = store.assess(args.capture)
        elif args.command == "status":
            result = store.status(args.artifact)
        else:
            result = store.report(args.artifact, args.destination)
        print(json.dumps(result, indent=2))
        return 0
    except (ValueError, OSError, KeyError, TypeError, sqlite3.Error) as error:
        print(f"Runtime evidence error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
