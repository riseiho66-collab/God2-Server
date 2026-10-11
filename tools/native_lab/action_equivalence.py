"""Offline ACTION_CONFIRM_SERVER evidence gate. Never invokes client code.

Runtime evidence must be supplied by an independently reviewed capture reader.
Static correlation is deliberately not converted into runtime observations.
"""

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WIRE = bytes.fromhex("06 00 a3 a3 fd d5")
IMAGE_SHA256 = "149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763"


@dataclass(frozen=True)
class StateWrite:
    """Ordered write, normalized to a reviewed object identity and offset."""

    object_id: str
    offset: int
    before: bytes
    after: bytes
    writer_rva: int


@dataclass(frozen=True)
class ActionEvidence:
    run_id: str
    lane: str
    source: str
    raw_wire: bytes | None = None
    human_confirmed: bool = False
    runtime_trace_source: str | None = None
    image_sha256: str | None = None
    builder_rva: int | None = None
    send_return_rva: int | None = None
    relevant_writes: tuple[StateWrite, ...] | None = None
    writes_complete: bool = False
    write_scope: tuple[str, ...] = ()
    # An independently reviewed trace must bind builder, send and writes to
    # this same action occurrence on the correct UI/game thread.
    action_trace_bound: bool = False
    correct_thread_observed: bool = False
    state_before: str | None = None
    selected_entry_id: int | None = None


def evaluate_equivalence(human: ActionEvidence, lab: ActionEvidence | None) -> dict:
    """Missing proof takes precedence over equivalence or mismatch claims."""
    missing = []
    if not human.human_confirmed or human.lane != "HUMAN_UI":
        missing.append("human.human_confirmed_ui_capture")
    if lab is None:
        missing.append("lab.native_action_capture")
    elif lab.lane != "NATIVE_LAB_CAPTURE":
        missing.append("lab.native_lab_provenance")
    for label, evidence in (("human", human), ("lab", lab)):
        if evidence is None:
            continue
        for field in ("run_id", "source", "runtime_trace_source", "image_sha256",
                      "action_trace_bound", "correct_thread_observed", "write_scope"):
            if not getattr(evidence, field):
                missing.append(f"{label}.{field}")
        for field in ("raw_wire", "builder_rva", "send_return_rva",
                      "state_before", "selected_entry_id"):
            if getattr(evidence, field) is None:
                missing.append(f"{label}.{field}")
        writes = evidence.relevant_writes
        if writes is None or not evidence.writes_complete:
            missing.append(f"{label}.complete_relevant_state_write_trace")
        elif not writes or any(
            not w.object_id or w.offset < 0 or w.writer_rva <= 0
            or not w.before or len(w.before) != len(w.after) for w in writes
        ):
            missing.append(f"{label}.valid_nonempty_state_write_trace")
    if missing:
        return {"action": "ACTION_CONFIRM_SERVER", "status": "UNPROVEN",
                "equivalent": False, "missing_proof": missing, "mismatches": []}
    mismatches = []
    for field in ("raw_wire", "image_sha256", "builder_rva", "send_return_rva",
                  "relevant_writes", "write_scope", "state_before", "selected_entry_id"):
        if getattr(human, field) != getattr(lab, field):
            mismatches.append(field)
    for field, expected in (("raw_wire", WIRE), ("image_sha256", IMAGE_SHA256),
                            ("send_return_rva", 0x12506),
                            ("state_before", "SERVER_AUTO_SELECTED"),
                            ("selected_entry_id", 0)):
        if getattr(human, field) != expected and field not in mismatches:
            mismatches.append(field)
    return {"action": "ACTION_CONFIRM_SERVER",
            "status": "REJECTED" if mismatches else "STRUCTURALLY_EQUIVALENT",
            "equivalent": False, "structurally_equivalent": not mismatches,
            "provenance": "UNTRUSTED_NO_CAPTURE_READER",
            "missing_proof": ["independently_verified_runtime_capture"],
            "mismatches": mismatches}


def frozen_report(root: Path = ROOT) -> dict:
    """Report only existing ui-gate-real-04 and postselect contract evidence."""
    run = root / "artifacts/runs/ui-gate-real-04"
    metadata = json.loads((run / "C2S_SERVER_SELECT_0001.json").read_text())
    contract = json.loads((root / "artifacts/contracts/post-server-select-v1.json").read_text())
    raw = (run / "C2S_SERVER_SELECT_0001.bin").read_bytes()
    if (raw != WIRE or raw != bytes.fromhex(contract["wire_hex"])
            or len(raw) != metadata["length"]
            or hashlib.sha256(raw).hexdigest() != metadata["sha256"]
            or metadata["run_id"] != "ui-gate-real-04"
            or metadata["caller_address_kind"] != "send return address"
            or int(metadata["caller_rva"], 16) != 0x12506):
        raise ValueError("Frozen capture identity mismatch")
    human = ActionEvidence(
        run_id=metadata["run_id"], lane="HUMAN_UI", source=str(run),
        raw_wire=raw, human_confirmed=True,
        send_return_rva=int(metadata["caller_rva"], 16),
        state_before=metadata["state_before"],
    )
    report = evaluate_equivalence(human, None)
    image = root / contract["image"]
    grounded = (contract["image_sha256"] == IMAGE_SHA256
                and hashlib.sha256(image.read_bytes()).hexdigest() == IMAGE_SHA256)
    report["candidate_abi"] = None
    if grounded:
        report["candidate_abi"] = {
            "qualification": "STATIC_CANDIDATE_ONLY_NOT_INVOCATION_READY",
            "image_sha256": IMAGE_SHA256, "image_base": "0x400000",
            "entry_rva": "0x7010", "architecture": "x86",
            "calling_convention": "inferred thiscall",
            "this_register": "ECX = existing UI object", "stack_arguments": [],
            "return": "unspecified; plain ret at RVA 0x7036",
            "evidence": "Path A calls RVA 0x7010 at 0x7093; guarded call to "
                        "0xafb0 with argument 3 at 0x7030. Writes at 0xaff6 "
                        "and 0xaffc target UI+0x178cf0 and UI+0x178cec.",
            "builder_candidate_rva": contract["builder_rva"],
            "builder_callsite_rva": "0xb4cc",
            "builder_this": "[UI+0x15e84]",
            "builder_first_two_arguments": ["low byte of WORD UI+0x8f4",
                                            "low byte of WORD UI+0xb40; meaning unknown"],
            "limitation": "Runtime UI object, guard result, deferred path to builder, "
                          "builder execution and ordered state writes are not proven. "
                          "Builder has additional arguments and a wait path; it is "
                          "not established as a standalone confirm action.",
        }
    report["observed_wire_hex"] = raw.hex(" ")
    report["observed_send_return_rva"] = metadata["caller_rva"]
    return report


if __name__ == "__main__":
    print(json.dumps(frozen_report(), indent=2))
