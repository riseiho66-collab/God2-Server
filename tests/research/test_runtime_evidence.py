"""Offline intake checks using fabricated evidence; no client is executed."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import struct
import tempfile
import unittest

from test_artifact_vault import synthetic_pe


RESEARCH = Path(__file__).resolve().parents[2] / "tools/research"
sys.path.insert(0, str(RESEARCH))
try:
    from runtime_evidence import RuntimeStore
finally:
    sys.path.pop(0)


class RuntimeEvidenceTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name)
        self.store = RuntimeStore(self.base / "vault")
        self.source = self.base / "client.exe"
        self.source.write_bytes(synthetic_pe())
        self.artifact = self.store.vault.ingest(self.source)["artifact_id"]
        self.bundle = self.base / "bundle"
        self.request = self.store.prepare(self.artifact, self.bundle)
        self.manifest = json.loads((self.bundle / "manifest.json").read_bytes())
        self.manifest["provenance"].update(
            tool="other", tool_version="test-1", operator="unit-test",
            captured_at="2026-09-18T00:00:00+00:00", environment_id="temporary-fixture",
            source_kind="synthetic", working_copy_sha256=self.artifact)
        self.manifest["process"].update(pid=1, module_base=0x400000)
        self.manifest["scope"]["ranges"] = [[0x401000, 0x401200]]
        self.events = [self.event("function_enter", {"bytes_hex": "9090909090909090"})]

    @staticmethod
    def event(kind, details, seq=0):
        return dict(id=f"event-{seq}", seq=seq, timestamp_ns=seq + 10,
                    thread_id=1, pc=0x401000, state="observed", type=kind, details=details)

    def attachment(self, name, role, data):
        (self.bundle / name).write_bytes(data)
        self.manifest["files"] = [f for f in self.manifest["files"] if f["path"] != name]
        self.manifest["files"].append(dict(path=name, role=role, size=len(data),
                                           sha256=hashlib.sha256(data).hexdigest()))

    def write(self, raw_events=None):
        if raw_events is None:
            raw_events = b"".join(json.dumps(e).encode() + b"\n" for e in self.events)
        self.attachment("events.jsonl", "events", raw_events)
        (self.bundle / "manifest.json").write_text(json.dumps(self.manifest), encoding="utf-8")

    def ready_unpack(self):
        # A runtime declaration exercises readiness logic, not real execution.
        self.manifest["provenance"]["source_kind"] = "runtime"
        candidate = synthetic_pe(1)
        code = candidate[0x200:0x208]
        memory = bytearray(0x2000)
        memory[0x1000:0x1008] = code
        self.attachment("memory.bin", "memory_image", bytes(memory))
        self.attachment("unpacked.exe", "unpacked_pe", candidate)
        self.attachment("native.log", "raw_trace", b"fabricated unit-test trace\n")
        self.events = [
            self.event("unpack_transition", dict(from_va=0x401080, to_va=0x401000,
                       region_va=0x401000, before_hex="00" * 8,
                       after_hex=code.hex(), memory_file="memory.bin")),
            self.event("oep_candidate", dict(rva=0x1000, bytes_hex=code.hex(),
                       memory_file="memory.bin", unpacked_file="unpacked.exe",
                       continued_event_ids=["event-2"]), 1),
            self.event("function_enter", dict(bytes_hex=code.hex()), 2)]

    def test_prepare_is_an_empty_non_ingestible_request(self):
        self.assertEqual(self.request["status"], "AWAITING_CONTROLLED_CAPTURE")
        self.assertEqual(self.request["artifact_id"], self.artifact)
        self.assertEqual((self.bundle / "events.jsonl").read_bytes(), b"")
        self.assertIsNone(json.loads((self.bundle / "manifest.json").read_bytes())["process"]["module_base"])
        with self.assertRaises(ValueError):
            self.store.validate_bundle(self.bundle)
        with self.assertRaises(ValueError):
            self.store.prepare(self.artifact, self.bundle)

    def test_missing_evidence_never_promotes_gates_or_metadata(self):
        before = self.store.vault.verify(self.artifact)
        self.write()
        capture = self.store.ingest(self.bundle)
        assessment = self.store.assess(capture)
        self.assertEqual(assessment["trust"], "UNREVIEWED")
        for gate in ("unpack", "oep", "iat", "quality", "network"):
            self.assertEqual(assessment["gates"][gate]["status"], "BLOCKED")
            self.assertFalse(assessment["gates"][gate]["verified"])
        self.assertEqual(self.store.vault.verify(self.artifact), before)
        state = self.store.status(self.artifact)
        self.assertEqual(state["highest_runtime_acceptance"], "L1 ARTIFACT_VERIFIED")
        self.assertEqual(state["coverage"]["verified_runtime_gates"], 0)
        self.assertEqual(state["function_candidates"][0]["confidence"], "HYPOTHESIS")

    def test_consistent_unpack_and_oep_only_become_ready_for_review(self):
        self.ready_unpack()
        self.write()
        assessment = self.store.assess(self.store.ingest(self.bundle))
        self.assertEqual(assessment["trust"], "UNREVIEWED")
        for gate in ("unpack", "oep"):
            self.assertEqual(assessment["gates"][gate]["status"], "READY_FOR_REVIEW")
            self.assertFalse(assessment["gates"][gate]["verified"])
        for gate in ("iat", "quality", "network"):
            self.assertEqual(assessment["gates"][gate]["status"], "BLOCKED")
        self.assertEqual(self.store.status(self.artifact)["status"], "BLOCKED")

    def test_synthetic_or_missing_native_trace_blocks_readiness(self):
        for synthetic in (True, False):
            with self.subTest(synthetic=synthetic):
                self.ready_unpack()
                if synthetic:
                    self.manifest["provenance"]["source_kind"] = "synthetic"
                else:
                    self.attachment("native.log", "raw_trace", b"")
                self.manifest["session_id"] = f"case-{synthetic}"
                self.write()
                report = self.store.assess(self.store.ingest(self.bundle))
                self.assertTrue(all(g["status"] == "BLOCKED" for g in report["gates"].values()))

    def test_capture_hash_idempotency_and_conflicting_session(self):
        self.write()
        capture = self.store.ingest(self.bundle)
        self.assertEqual(capture, hashlib.sha256((self.bundle / "manifest.json").read_bytes()).hexdigest())
        stored = self.store.captures / capture
        before = {p.name: p.read_bytes() for p in stored.iterdir()}
        self.assertEqual(self.store.ingest(self.bundle), capture)
        self.assertEqual({p.name: p.read_bytes() for p in stored.iterdir()}, before)
        self.events[0]["state"] = "different"
        self.write()
        with self.assertRaises(ValueError):
            self.store.ingest(self.bundle)
        self.assertEqual({p.name: p.read_bytes() for p in stored.iterdir()}, before)

    def test_attachment_and_source_hash_tamper(self):
        self.write()
        events = self.bundle / "events.jsonl"
        original = events.read_bytes()
        events.write_bytes(original.replace(b"observed", b"tampered"))
        with self.assertRaises(ValueError):
            self.store.validate_bundle(self.bundle)
        events.write_bytes(original)
        binary = self.store.vault.location(self.artifact) / "original/client.exe"
        binary.write_bytes(synthetic_pe(2))
        with self.assertRaises(ValueError):
            self.store.validate_bundle(self.bundle)

    def test_stored_attachment_and_manifest_tamper(self):
        self.write()
        capture = self.store.ingest(self.bundle)
        folder = self.store.captures / capture
        events = folder / "events.jsonl"
        raw = events.read_bytes()
        events.write_bytes(b"tampered")
        for operation in (lambda: self.store.assess(capture), lambda: self.store.ingest(self.bundle),
                          lambda: self.store.status(self.artifact)):
            with self.assertRaises(ValueError):
                operation()
        events.write_bytes(raw)
        manifest = folder / "manifest.json"
        manifest.write_bytes(manifest.read_bytes() + b"\n")
        with self.assertRaises(ValueError):
            self.store.assess(capture)

    def test_index_tamper_is_detected(self):
        self.write()
        capture = self.store.ingest(self.bundle)
        db = self.store.vault.connect()
        try:
            with db:
                db.execute("UPDATE runtime_events SET payload='{}' WHERE capture=?", (capture,))
        finally:
            db.close()
        with self.assertRaises(ValueError):
            self.store.assess(capture)

    def test_paths_and_capture_ids_reject_traversal(self):
        self.write()
        for path in ("../outside", "..\\outside", "/outside", "C:/outside", "./events.jsonl",
                     "nested/../events.jsonl", "events.jsonl:stream"):
            with self.subTest(path=path):
                self.manifest["files"][0]["path"] = path
                (self.bundle / "manifest.json").write_text(json.dumps(self.manifest), encoding="utf-8")
                with self.assertRaises(ValueError):
                    self.store.validate_bundle(self.bundle)
        for capture in ("../outside", "A" * 64, "a" * 63, "a" * 64 + "\n"):
            with self.subTest(capture=capture), self.assertRaises(ValueError):
                self.store.assess(capture)

    def test_artifact_identity_and_image_size_are_validated(self):
        for field, value in (("artifact_id", "../outside"), ("artifact_id", "A" * 64),
                             ("artifact_id", "f" * 64), ("image_size", 0x3000)):
            with self.subTest(field=field, value=value):
                original = copy.deepcopy(self.manifest)
                target = self.manifest if field == "artifact_id" else self.manifest["process"]
                target[field] = value
                self.write()
                with self.assertRaises((ValueError, OSError)):
                    self.store.validate_bundle(self.bundle)
                self.manifest = original

    def test_schema_rejects_extra_missing_duplicate_and_wrong_types(self):
        original = copy.deepcopy(self.manifest)
        for field, value in (("schema_version", True), ("schema_version", 99),
                             ("unexpected", "value"), ("files", [])):
            with self.subTest(field=field, value=value):
                self.manifest = copy.deepcopy(original)
                self.write()
                invalid = copy.deepcopy(self.manifest)
                invalid[field] = value
                (self.bundle / "manifest.json").write_text(json.dumps(invalid), encoding="utf-8")
                with self.assertRaises(ValueError):
                    self.store.validate_bundle(self.bundle)
        self.manifest = original
        self.write()
        path = self.bundle / "manifest.json"
        raw = path.read_bytes()
        path.write_bytes(b'{"schema_version":1,' + raw[1:])
        with self.assertRaises(ValueError):
            self.store.validate_bundle(self.bundle)
        for raw_events in (b"", b"{}\n", b'{"id":"a","id":"b"}\n', b"NaN\n"):
            with self.subTest(raw_events=raw_events):
                self.write(raw_events)
                with self.assertRaises(ValueError):
                    self.store.validate_bundle(self.bundle)

    def test_event_order_addresses_and_required_direction(self):
        send = self.event("socket_send", dict(buffer_va=0x500000, size=2, after_hex="0102",
                          api="send", target_va=0x700000, direction="TX"))
        cases = [("seq", 1), ("seq", True), ("pc", 0x401200), ("pc", -1),
                 ("pc", 2**32), ("thread_id", 0), ("extra", 1), ("type", "unknown")]
        for field, value in cases:
            with self.subTest(field=field, value=value):
                self.events = [copy.deepcopy(send)]
                self.events[0][field] = value
                self.write()
                with self.assertRaises(ValueError):
                    self.store.validate_bundle(self.bundle)
        for field, value in (("direction", None), ("direction", "RX"), ("api", "recv"),
                             ("size", 4097), ("size", True), ("buffer_va", 0xffffffff),
                             ("after_hex", "01"), ("after_hex", "zz"), ("target_va", 2**32)):
            with self.subTest(detail=field, value=value):
                self.events = [copy.deepcopy(send)]
                if value is None:
                    del self.events[0]["details"][field]
                else:
                    self.events[0]["details"][field] = value
                self.write()
                with self.assertRaises(ValueError):
                    self.store.validate_bundle(self.bundle)
        for field, value in (("timestamp_ns", 9), ("id", "event-0"), ("seq", 2)):
            with self.subTest(second_event=field):
                self.events = [copy.deepcopy(send), self.event("function_exit", {"return_value": 0}, 1)]
                self.events[1][field] = value
                self.write()
                with self.assertRaises(ValueError):
                    self.store.validate_bundle(self.bundle)
        self.events = [send]
        self.write()
        self.assertEqual(self.store.validate_bundle(self.bundle)["events"], self.events)

    def test_counter_evidence_blocks_and_references_must_exist(self):
        self.ready_unpack()
        counter = self.event("counter_evidence", dict(gate="unpack",
                             related_event_ids=["missing"], reason="fabricated contradiction"), 3)
        self.events.append(counter)
        self.write()
        with self.assertRaises(ValueError):
            self.store.validate_bundle(self.bundle)
        counter["details"]["related_event_ids"] = ["event-0"]
        self.write()
        assessment = self.store.assess(self.store.ingest(self.bundle))
        self.assertEqual(assessment["gates"]["unpack"]["status"], "BLOCKED")
        self.assertTrue(any(reason.startswith("Counter evidence")
                            for reason in assessment["gates"]["unpack"]["blockers"]))
        self.assertEqual(assessment["gates"]["oep"]["status"], "BLOCKED")

    def test_report_without_captures_preserves_unknowns(self):
        destination = self.base / "report"
        state = self.store.report(self.artifact, destination)
        self.assertEqual(json.loads((destination / "status.json").read_bytes()), state)
        self.assertEqual(state["captures"], [])
        self.assertIsNone(state["coverage"]["total_real_packets"])
        expected = {"RECONSTRUCTION_STATUS.md", "GOD2_PROTOCOL_SPEC.md", "OPCODE_TABLE.md",
                    "STATE_MACHINE.md", "UNKNOWN_FIELDS.md", "CONTRADICTIONS.md", "status.json"}
        self.assertEqual({p.name for p in destination.iterdir()}, expected)
        for name in expected - {"status.json"}:
            self.assertIn(self.artifact, (destination / name).read_text(encoding="utf-8"))
        with self.assertRaises(ValueError):
            self.store.report(self.artifact, destination)

    def test_seal_hashes_worksheet_without_modifying_source(self):
        self.write()
        self.manifest["files"][0].update(size=0, sha256="0" * 64)
        path = self.bundle / "manifest.json"
        path.write_text(json.dumps(self.manifest), encoding="utf-8")
        before = path.read_bytes()
        destination = self.base / "sealed"
        result = self.store.seal(self.bundle, destination)
        self.assertEqual(result["capture_id"], self.store.validate_bundle(destination)["capture_id"])
        self.assertEqual(path.read_bytes(), before)
        with self.assertRaises(ValueError):
            self.store.seal(self.bundle, destination)

    def test_working_copy_and_sensitive_handling_v2(self):
        self.write()
        self.manifest["provenance"]["working_copy_sha256"] = "0" * 64
        self.write()
        with self.assertRaises(ValueError):
            self.store.validate_bundle(self.bundle)
        self.manifest["provenance"]["working_copy_sha256"] = self.artifact
        self.manifest["provenance"]["handling"]["restricted"] = False
        self.write()
        with self.assertRaises(ValueError):
            self.store.validate_bundle(self.bundle)

    def test_legacy_and_redacted_captures_are_preserved_but_not_ready(self):
        self.ready_unpack()
        self.manifest["provenance"]["handling"]["redacted"] = True
        self.write()
        self.assertEqual(self.store.assess(self.store.ingest(self.bundle))["gates"]["unpack"]["status"], "BLOCKED")
        self.manifest["session_id"] = "legacy-fixture"
        self.manifest["schema_version"] = 1
        del self.manifest["provenance"]["handling"]
        del self.manifest["provenance"]["working_copy_sha256"]
        self.write()
        self.assertEqual(self.store.assess(self.store.ingest(self.bundle))["gates"]["unpack"]["status"], "BLOCKED")

    def test_reingest_rejects_capture_function_and_event_index_tamper(self):
        self.write()
        capture = self.store.ingest(self.bundle)
        for statement in ("UPDATE runtime_captures SET event_count=99 WHERE id=?",
                          "UPDATE runtime_events SET type='call' WHERE capture=?",
                          "UPDATE runtime_functions SET rva=0 WHERE capture=?"):
            db = self.store.vault.connect()
            try:
                db.execute(statement, (capture,))
                db.commit()
                with self.assertRaises(ValueError):
                    self.store.ingest(self.bundle)
                if "runtime_captures" in statement:
                    db.execute("UPDATE runtime_captures SET event_count=1 WHERE id=?", (capture,))
                elif "runtime_events" in statement:
                    db.execute("UPDATE runtime_events SET type='function_enter' WHERE capture=?", (capture,))
                else:
                    db.execute("UPDATE runtime_functions SET rva=4096 WHERE capture=?", (capture,))
                db.commit()
            finally:
                db.close()

    def ready_iat(self):
        self.ready_unpack()
        repaired = bytearray(synthetic_pe(1))
        repaired[0x300:] = bytes(0x100)
        struct.pack_into("<II", repaired, 0x98 + 104, 0x1100, 40)
        struct.pack_into("<IIIII", repaired, 0x300, 0x1140, 0, 0, 0x1180, 0x1150)
        struct.pack_into("<II", repaired, 0x340, 0x1160, 0)
        struct.pack_into("<II", repaired, 0x350, 0x1160, 0)
        repaired[0x360:0x367] = b"\0\0send\0"
        repaired[0x380:0x38b] = b"ws2_32.dll\0"
        module = bytearray(synthetic_pe(1))
        module[0x300:] = bytes(0x100)
        struct.pack_into("<II", module, 0x98 + 96, 0x1100, 0x80)
        struct.pack_into("<IIHHIIIIIII", module, 0x300, 0, 0, 0, 0, 0x1160, 1, 1, 1, 0x1140, 0x1144, 0x1148)
        struct.pack_into("<IIH", module, 0x340, 0x1000, 0x1170, 0)
        module[0x360:0x36b] = b"ws2_32.dll\0"
        module[0x370:0x375] = b"send\0"
        memory = bytearray((self.bundle / "memory.bin").read_bytes())
        struct.pack_into("<I", memory, 0x1150, 0x701000)
        self.attachment("memory.bin", "memory_image", bytes(memory))
        self.attachment("repaired.exe", "repaired_pe", bytes(repaired))
        self.attachment("winsock.dll", "module_pe", bytes(module))
        self.attachment("disassembly.txt", "disassembly", b"synthetic test probe only")
        self.events.extend([
            self.event("import_resolved", dict(iat_rva=0x1150, target_va=0x701000, module_base=0x700000,
                       module_file="winsock.dll", module_name="ws2_32.dll", symbol="send",
                       memory_file="memory.bin", repaired_file="repaired.exe"), 3),
            self.event("analysis_probe", dict(image_file="repaired.exe", rva=0x1000,
                       bytes_hex=repaired[0x200:0x208].hex(), disassembly_file="disassembly.txt",
                       decoder="synthetic-test", instruction_count=1), 4),
            self.event("socket_send", dict(buffer_va=0x500000, size=2, after_hex="0102",
                       api="send", target_va=0x701000, direction="TX"), 5)])

    def test_iat_quality_and_network_consistency_without_certification(self):
        self.ready_iat()
        self.write()
        result = self.store.assess(self.store.ingest(self.bundle))
        for gate in ("iat", "quality", "network"):
            self.assertEqual(result["gates"][gate]["status"], "READY_FOR_REVIEW", result)
            self.assertFalse(result["gates"][gate]["verified"])

    def test_network_name_and_iat_address_mismatch_block(self):
        self.ready_iat()
        self.events[-1]["details"]["api"] = "WSASend"
        self.write()
        result = self.store.assess(self.store.ingest(self.bundle))
        self.assertEqual(result["gates"]["network"]["status"], "BLOCKED")
        self.manifest["session_id"] = "bad-iat"
        self.events[3]["details"]["target_va"] += 1
        self.write()
        result = self.store.assess(self.store.ingest(self.bundle))
        self.assertEqual(result["gates"]["iat"]["status"], "BLOCKED")
        self.assertEqual(result["gates"]["quality"]["status"], "BLOCKED")


if __name__ == "__main__":
    unittest.main()
