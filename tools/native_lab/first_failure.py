"""Validate a bounded native first-failure record; never solve or execute it.

The caller must supply evidence from its trusted native trace collector. This
checks consistency, not trace authenticity. Only direct packet reads are supported;
transformed operands remain blocked until their observed derivation is supported.
No record, including a valid one, certifies handler or clean-client acceptance.
"""

from copy import deepcopy
import hashlib
import re


def _text(value):
    return isinstance(value, str) and bool(value.strip())


def _uint(value):
    return type(value) is int and 0 <= value < 2**32


def _sha(value):
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def validate_first_failure(trace=None, *, packet=None, requested_success=None):
    """Return BLOCKED without complete, mutually consistent native evidence.

    RVAs and values are integers, branch directions are booleans, and sequence
    numbers order observations within trace_id. Predicate text is opaque observed
    data: it is never parsed, evaluated, inferred, or converted into instructions.
    """
    def blocked(reason):
        return {"status": "BLOCKED", "reason": reason, "constraint": None}

    if not isinstance(trace, dict) or trace.get("source") != "NATIVE_LAB_CAPTURE":
        return blocked("native_trace_required")
    if not _text(trace.get("trace_id")) or trace.get("direction") != "SERVER_FIRST":
        return blocked("native_server_first_evidence_required")
    if not isinstance(packet, bytes) or not packet:
        return blocked("candidate_packet_required")
    if trace.get("packet_sha256") != hashlib.sha256(packet).hexdigest():
        return blocked("packet_identity_mismatch")
    if not _text(requested_success):
        return blocked("requested_success_required")

    handler = trace.get("handler")
    if not isinstance(handler, dict) or not (
        _sha(handler.get("image_sha256"))
        and _uint(handler.get("rva"))
        and handler.get("executed") is True
        and _uint(handler.get("sequence"))
    ):
        return blocked("native_handler_identity_required")

    predicate = trace.get("predicate")
    if not isinstance(predicate, dict) or not (
        predicate.get("executed") is True
        and predicate.get("first_failure") is True
        and _uint(predicate.get("sequence"))
        and predicate["sequence"] > handler["sequence"]
        and predicate.get("handler_rva") == handler["rva"]
        and type(predicate.get("handler_rva")) is int
        and _uint(predicate.get("instruction_rva"))
        and _text(predicate.get("observed_predicate"))
        and type(predicate.get("taken")) is bool
    ):
        return blocked("executed_first_predicate_required")

    operands = predicate.get("packet_operands")
    if not isinstance(operands, list) or not operands:
        return blocked("packet_derived_operands_required")
    for operand in operands:
        if not isinstance(operand, dict):
            return blocked("packet_derived_operands_required")
        offset, size = operand.get("offset"), operand.get("size")
        if not (
            operand.get("source") == "packet_direct_read"
            and _uint(offset) and type(size) is int and size in (1, 2, 4)
            and offset + size <= len(packet)
            and operand.get("byteorder") in ("little", "big")
            and _uint(operand.get("read_sequence"))
            and handler["sequence"] < operand["read_sequence"] < predicate["sequence"]
            and _uint(operand.get("read_rva"))
            and _uint(operand.get("value"))
        ):
            return blocked("packet_read_evidence_required")
        actual = int.from_bytes(packet[offset:offset + size], operand["byteorder"])
        if operand["value"] != actual:
            return blocked("packet_operand_mismatch")

    success = trace.get("success_branch")
    if not isinstance(success, dict) or not (
        success.get("source") == "NATIVE_LAB_CAPTURE"
        and _text(success.get("trace_id"))
        and success["trace_id"] != trace["trace_id"]
        and success.get("image_sha256") == handler["image_sha256"]
        and type(success.get("handler_rva")) is int
        and success["handler_rva"] == handler["rva"]
        and type(success.get("instruction_rva")) is int
        and success["instruction_rva"] == predicate["instruction_rva"]
        and success.get("executed") is True
        and type(success.get("taken")) is bool
        and success["taken"] != predicate["taken"]
        and success.get("event") == requested_success
        and success.get("event_observed") is True
        and success.get("path_to_event_observed") is True
        and _uint(success.get("branch_sequence"))
        and _uint(success.get("event_sequence"))
        and success["branch_sequence"] < success["event_sequence"]
    ):
        return blocked("requested_success_branch_evidence_required")

    return {
        "status": "EVIDENCE_VALIDATED",
        "reason": None,
        "constraint": {
            "instruction_rva": predicate["instruction_rva"],
            "observed_predicate": predicate["observed_predicate"],
            "packet_operands": deepcopy(operands),
            "required_branch_taken": success["taken"],
        },
    }
