"""Offline evidence preflight, not an observer or a source of certification.

Each level supplies references to a JSON run record and nonempty packet/before/
after artifacts. References contain root-relative path and SHA256. The run binds
those references, run/session/transition identities, semantic endpoints and lane.
Packet artifacts are logical plaintext, including in wire runs, so all three
gates must bind the same candidate. State artifacts contain captured bytes.

These are caller-controlled records. Hash validity establishes integrity only;
no actual trusted observer is installed here and no level can be certified.
"""

from hashlib import sha256
import json
from pathlib import Path, PureWindowsPath
import re


LEVELS = (
    "NATIVE_HANDLER_ACCEPTED",
    "LAB_WIRE_ACCEPTED",
    "CLEAN_CLIENT_CERTIFIED",
)
_MODES = (
    ("LAB", "DIRECT_HANDLER", "LOGICAL", "LAB_AGENT"),
    ("LAB", "REAL_SOCKET", "CLEAN_CPP", "LAB_AGENT"),
    ("CLEAN", "REAL_SOCKET", "CLEAN_CPP", "NONE"),
)
_ARTIFACTS = ("packet", "state_before", "state_after")


class EvidenceError(ValueError):
    """Malformed, mismatched or incomplete evidence."""


def _require(condition, message):
    if not condition:
        raise EvidenceError(message)


def _text(value):
    return isinstance(value, str) and bool(value.strip())


def _read(root, ref):
    _require(isinstance(ref, dict) and set(ref) == {"path", "sha256"},
             "artifact reference requires path and sha256")
    name, digest = ref["path"], ref["sha256"]
    _require(_text(name) and isinstance(digest, str)
             and re.fullmatch(r"[0-9a-f]{64}", digest), "invalid path or sha256")
    relative = Path(name)
    windows = PureWindowsPath(name)
    _require(not relative.is_absolute() and not windows.drive
             and not windows.root and ":" not in name,
             "artifact path must be relative")
    path = (root / relative).resolve()
    _require(path.is_relative_to(root), "artifact escapes evidence root")
    _require(path.is_file(), "artifact is not a file")
    data = path.read_bytes()
    _require(bool(data), "empty artifact")
    _require(sha256(data).hexdigest() == digest, "artifact hash mismatch")
    return data


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        _require(key not in result, "duplicate JSON key")
        result[key] = value
    return result


def _validate(root, evidence, index):
    _require(isinstance(evidence, dict)
             and set(evidence) == {"level", "run", *_ARTIFACTS},
             "level requires run, packet and state references only")
    _require(evidence["level"] == LEVELS[index], "levels must be sequential")
    run = json.loads(_read(root, evidence["run"]), object_pairs_hook=_unique_object)
    fields = {"schema", "run_id", "session_id", "transition_id", "from_state",
              "to_state", "lane", "transport", "crypto", "instrumentation",
              "execution", "result", *_ARTIFACTS}
    _require(isinstance(run, dict) and set(run) == fields, "invalid run record fields")
    _require(run["schema"] == "native-certification/v1", "unsupported run schema")
    for key in ("run_id", "session_id", "transition_id", "from_state", "to_state"):
        _require(_text(run[key]), "invalid run identity or semantic state")
    _require(run["from_state"] != run["to_state"], "no semantic transition")
    _require(tuple(run[k] for k in ("lane", "transport", "crypto", "instrumentation"))
             == _MODES[index], "wrong lane or execution mode")
    _require(run["execution"] == "ORIGINAL_NATIVE_CLIENT"
             and run["result"] == "STATE_ADVANCED", "missing native transition record")
    for key in _ARTIFACTS:
        _require(run[key] == evidence[key], "run artifact binding mismatch")
        _read(root, evidence[key])
    _require(evidence["state_before"]["sha256"] != evidence["state_after"]["sha256"],
             "state captures are identical")
    return run


def qualify(evidence_root, evidence):
    """Return fail-closed qualification plus contiguous structural preflight.

    There is deliberately no trusted=True argument or caller-supplied observer
    callback. A future trusted capture integration needs an independent trust
    boundary; adding fields to these artifacts cannot establish one.
    """
    report = {
        "certification_level": 0,
        "qualification": "UNQUALIFIED",
        "provenance": "UNTRUSTED",
        "structural_level": 0,
        "structurally_validated": [],
        "errors": [],
        "limitations": ["NO_TRUSTED_OBSERVER", "NO_VERIFIED_ORIGINAL_ACTION_EVIDENCE"],
    }
    if not isinstance(evidence, (list, tuple)) or len(evidence) > 3:
        report["errors"].append("expected at most three sequential evidence records")
        return report
    root = Path(evidence_root).resolve()
    identity = None
    run_ids = set()
    for index, item in enumerate(evidence):
        try:
            run = _validate(root, item, index)
            # Session identities belong to individual runs; clean certification
            # must be possible on a fresh connection, not the lab's old socket.
            current = tuple(run[k] for k in
                            ("transition_id", "from_state", "to_state"))
            current += (run["packet"]["sha256"],)
            _require(identity is None or current == identity,
                     "gates must reproduce the same packet/transition")
            _require(run["run_id"] not in run_ids, "each gate requires a distinct run")
            identity = current
            run_ids.add(run["run_id"])
        except (EvidenceError, OSError, ValueError, TypeError, RecursionError):
            # Never echo artifact contents or paths that may contain credentials.
            report["errors"].append(f"INVALID_EVIDENCE_LEVEL_{index + 1}")
            break
        report["structural_level"] = index + 1
        report["structurally_validated"].append(LEVELS[index])
    return report
