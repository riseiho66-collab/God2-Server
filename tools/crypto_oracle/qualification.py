"""Independent evidence checks. No execution, runtime attestation, or promotion."""

import hashlib
import json
import re


NEXT_LIVE_GATE = "TYPED_TRUSTED_RUNTIME_ADAPTER_REQUIRED"
_HASH = re.compile(r"[0-9a-f]{64}\Z")


def _identity(value):
    return type(value) is str and bool(value.strip())


def _hex(value):
    if type(value) is not str or len(value) % 2:
        return None
    if re.fullmatch(r"[0-9a-f]*", value) is None:
        return None
    return bytes.fromhex(value)


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def _reference(value, expected_type, errors, path):
    """Check actual raw bytes, never a claimed digest or PASS flag alone."""
    if type(value) is not dict or value.get("type") != expected_type:
        errors.append(path + ": typed raw reference required")
        return None
    raw = _hex(value.get("raw_hex"))
    digest = value.get("sha256")
    if (raw is None or type(digest) is not str or not _HASH.fullmatch(digest)
            or hashlib.sha256(raw).hexdigest() != digest):
        errors.append(path + ": raw reference SHA256 mismatch or missing bytes")
        return None
    try:
        record = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_object)
    except (ValueError, UnicodeError, RecursionError):
        record = None
    if type(record) is not dict:
        errors.append(path + ": raw reference must encode a JSON object")
        return None
    return record


def _vectors(values, run_id, session_id, errors, path, live=False):
    counts = {"C2S": 0, "S2C": 0}
    seen_ids, seen_payloads = set(), set()
    previous = {}
    if type(values) is not list or not values:
        errors.append(path + ": nonempty raw vector references required")
        return counts
    for index, reference in enumerate(values):
        label = f"{path}[{index}]"
        record = _reference(reference, "live_packet_v1" if live else "oracle_diff_vector_v1",
                            errors, label)
        if record is None:
            continue
        direction = record.get("direction")
        vector_id = record.get("vector_id")
        if (record.get("run_id") != run_id or record.get("session_id") != session_id
                or not _identity(vector_id) or type(direction) is not str or direction not in counts):
            errors.append(label + ": run/session/vector/direction identity invalid")
            continue
        if vector_id in seen_ids:
            errors.append(label + ": duplicate vector identity")
        seen_ids.add(vector_id)
        fields = ("input", "state_before", "oracle_output", "clean_output",
                  "oracle_state_after", "clean_state_after")
        decoded = {field: _hex(record.get(field + "_hex")) for field in fields}
        if any(value is None or not value for value in decoded.values()):
            errors.append(label + ": nonempty raw input/output/state bytes required")
            continue
        fingerprint = (direction, decoded["input"], decoded["state_before"],
                       decoded["oracle_output"], decoded["oracle_state_after"])
        if fingerprint in seen_payloads:
            errors.append(label + ": duplicate vector content")
        seen_payloads.add(fingerprint)
        for suffix in ("output", "state_after"):
            if decoded["oracle_" + suffix] != decoded["clean_" + suffix]:
                errors.append(label + ": raw " + suffix + " mismatch")
        sequence = record.get("sequence")
        if type(sequence) is not int or sequence != counts[direction] + 1:
            errors.append(label + ": direction sequence must be contiguous from 1")
        if direction in previous and previous[direction] != decoded["state_before"]:
            errors.append(label + ": state continuity mismatch")
        previous[direction] = decoded["oracle_state_after"]
        counts[direction] += 1
        if live:
            for suffix in ("output", "state_after"):
                if _hex(record.get("client_" + suffix + "_hex")) != decoded["oracle_" + suffix]:
                    errors.append(label + ": three-way " + suffix + " evidence missing/mismatch")
            acceptance = _reference(record.get("acceptance"), "parser_acceptance_v1", errors,
                                    label + ".acceptance")
            expected_consumer = "clean_parser" if direction == "C2S" else "original_client"
            if acceptance is not None and (
                    any(acceptance.get(key) != record.get(key) for key in
                        ("run_id", "session_id", "vector_id", "direction"))
                    or acceptance.get("consumer") != expected_consumer
                    or acceptance.get("result") != "accepted"
                    or not _identity(acceptance.get("parser_event_id"))):
                errors.append(label + ": parser acceptance identity/result invalid")
    for direction, count in counts.items():
        if count < 2:
            errors.append(path + ": at least two " + direction + " packets required")
    return counts


def evaluate_qualification(report):
    """Return JSON-safe diagnostics; CRYPTO_RECOVERED is unconditionally false.

    Hash integrity is not capture provenance. Live records are inspected only to
    explain missing evidence; no user-supplied validator/boolean can attest them.
    """
    offline_errors, live_errors = [], []
    if type(report) is not dict:
        report = {}
        offline_errors.append("report must be an object")
    if report.get("capsule_corpus_pass") is not True:
        offline_errors.append("capsule_corpus_pass must be true with raw evidence")
    for field in ("output_mismatches", "state_mismatches", "brute_force_count"):
        if type(report.get(field)) is not int or report[field] != 0:
            offline_errors.append(field + " must be integer zero")
    run_id, session_id = report.get("run_id"), report.get("session_id")
    if not _identity(run_id) or not _identity(session_id):
        offline_errors.append("offline run_id and session_id required")
    counts = _vectors(report.get("offline_vectors"), run_id, session_id, offline_errors,
                      "offline_vectors")
    sessions = report.get("live_sessions")
    if type(sessions) is not list or len(sessions) != 2:
        live_errors.append("exactly two fresh live sessions A and B required")
        sessions = []
    identities = {key: set() for key in ("run_id", "session_id", "seed_sha256", "key_sha256")}
    labels = set()
    for index, reference in enumerate(sessions):
        path = f"live_sessions[{index}]"
        record = _reference(reference, "live_session_v1", live_errors, path)
        if record is None:
            continue
        label = record.get("label")
        if type(label) is not str or label not in ("A", "B") or label in labels:
            live_errors.append(path + ": distinct A/B labels required")
        if type(label) is str:
            labels.add(label)
        for key, seen in identities.items():
            value = record.get(key)
            valid = _identity(value)
            if key.endswith("sha256"):
                valid = valid and bool(_HASH.fullmatch(value))
            if not valid or value in seen:
                live_errors.append(path + ": missing or repeated " + key)
            if valid:
                seen.add(value)
        if record.get("backend") != "Clean" or record.get("fresh") is not True:
            live_errors.append(path + ": fresh Clean session evidence required")
        actual = _vectors(record.get("packets"), record.get("run_id"), record.get("session_id"),
                          live_errors, path + ".packets", live=True)
        for direction, count in actual.items():
            claimed = record.get(direction.lower() + "_count")
            if type(claimed) is not int or claimed != count:
                live_errors.append(path + ": " + direction + " count mismatch")
    live_errors.append("typed trusted runtime adapter absent; capture provenance, freshness, "
                       "key/seed derivation and parser acceptance are not attested")
    return {
        "status": "ORACLE_EQUIVALENT_OFFLINE" if not offline_errors else "ORACLE_EVIDENCE_REJECTED",
        "CRYPTO_RECOVERED": False,
        "promotion_blocked": True,
        "next_live_gate": NEXT_LIVE_GATE,
        "offline_packet_counts": counts,
        "offline_errors": offline_errors,
        "missing_evidence": live_errors,
    }
