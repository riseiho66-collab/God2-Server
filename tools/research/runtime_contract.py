"""Strict, bounded normalized runtime evidence contracts; no debugger execution."""
from datetime import datetime
from pathlib import Path, PurePosixPath
import json
import re

MAX_FILES = 64
MAX_TOTAL = 256 * 1024 * 1024
MAX_EVENTS = 20000
MAX_LINE = 16384
SHA = re.compile(r"[0-9a-f]{64}\Z")
ID = re.compile(r"[A-Za-z0-9_-]{1,80}\Z")
ROLES = {"events", "raw_trace", "memory_image", "unpacked_pe", "repaired_pe", "module_pe", "disassembly"}
EVENT_FIELDS = {
    "function_enter": {"bytes_hex"}, "function_exit": {"return_value"},
    "call": {"target_va"},
    "memory_read": {"buffer_va", "size", "after_hex"},
    "memory_write": {"buffer_va", "size", "before_hex", "after_hex"},
    "buffer_created": {"buffer_va", "size"},
    "socket_send": {"buffer_va", "size", "after_hex", "api", "target_va", "direction"},
    "socket_receive": {"buffer_va", "size", "after_hex", "api", "target_va", "direction"},
    "unpack_transition": {"from_va", "to_va", "region_va", "before_hex", "after_hex", "memory_file"},
    "oep_candidate": {"rva", "bytes_hex", "memory_file", "unpacked_file", "continued_event_ids"},
    "import_resolved": {"iat_rva", "target_va", "module_base", "module_file", "module_name", "symbol", "memory_file", "repaired_file"},
    "analysis_probe": {"image_file", "rva", "bytes_hex", "disassembly_file", "decoder", "instruction_count"},
    "counter_evidence": {"gate", "related_event_ids", "reason"},
}
GATES = ("unpack", "oep", "iat", "quality", "network")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def integer(value, label, minimum=0, maximum=0xffffffff):
    require(type(value) is int and minimum <= value <= maximum, f"Invalid integer: {label}")
    return value


def text(value, label, limit=512):
    require(isinstance(value, str) and 0 < len(value) <= limit and not any(ord(c) < 32 for c in value), f"Invalid text: {label}")
    return value


def exact(value, fields, label):
    require(isinstance(value, dict) and set(value) == set(fields), f"Unexpected or missing fields: {label}")


def decode_hex(value):
    require(isinstance(value, str) and len(value) <= 8192 and re.fullmatch(r"(?:[0-9a-fA-F]{2})*", value) is not None, "Invalid bounded hex string")
    return bytes.fromhex(value)


def parse_json(data):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, f"Duplicate JSON key: {key}")
            result[key] = value
        return result
    try:
        return json.loads(data, object_pairs_hook=unique, parse_constant=lambda v: require(False, f"Invalid JSON constant: {v}"))
    except (UnicodeError, RecursionError, json.JSONDecodeError) as error:
        raise ValueError(f"Invalid JSON: {error}") from error


def safe_file(root, relative):
    text(relative, "file path", 200)
    require("\\" not in relative and ":" not in relative, "Only relative POSIX-style bundle paths accepted")
    path = PurePosixPath(relative)
    require(not path.is_absolute() and all(p not in (".", "..") for p in path.parts)
            and str(path) == relative, "Noncanonical bundle path")
    require(all(not p.endswith((".", " ")) and not re.search(r'[<>"|?*]', p)
                and p.split(".")[0].upper() not in {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(10)), *(f"LPT{i}" for i in range(10))}
                for p in path.parts), "Unsafe Windows path")
    result = root / relative
    require(result.resolve().is_relative_to(root) and result.resolve() == result, "Bundle path escape or symlink")
    return result


def read_limit(path, limit):
    with path.open("rb") as stream:
        value = stream.read(limit + 1)
    require(len(value) <= limit, f"File too large: {path.name}")
    return value


def validate_manifest(manifest):
    exact(manifest, {"schema_version", "artifact_id", "session_id", "provenance", "process", "scope", "files"}, "manifest")
    require(type(manifest["schema_version"]) is int and manifest["schema_version"] in (1, 2), "Unsupported manifest version")
    require(isinstance(manifest["artifact_id"], str) and SHA.fullmatch(manifest["artifact_id"]), "Invalid artifact ID")
    require(isinstance(manifest["session_id"], str) and ID.fullmatch(manifest["session_id"]), "Invalid session ID")
    provenance = manifest["provenance"]
    fields = {"tool", "tool_version", "operator", "captured_at", "environment_id", "isolation", "source_kind", "adapter"}
    if manifest["schema_version"] == 2:
        fields |= {"working_copy_sha256", "handling"}
    exact(provenance, fields, "provenance")
    for key, value in provenance.items():
        if key != "handling":
            text(value, key)
    if manifest["schema_version"] == 2:
        require(provenance["working_copy_sha256"] == manifest["artifact_id"], "Working copy must match the original artifact SHA256")
        handling = provenance["handling"]
        exact(handling, {"sensitive", "redacted", "restricted"}, "evidence handling")
        require(all(type(v) is bool for v in handling.values()), "Handling flags must be booleans")
        require(not handling["sensitive"] or handling["restricted"], "Sensitive evidence must be declared restricted")
    require(provenance["tool"] in ("x32dbg", "windbg", "other"), "Unknown producer")
    require(provenance["adapter"] == "god2-normalized-v1", "Unsupported adapter")
    require(provenance["source_kind"] in ("runtime", "synthetic"), "Invalid source kind")
    require(provenance["isolation"] in ("offline", "loopback-only"), "Controlled capture requires declared isolation")
    try:
        require(datetime.fromisoformat(provenance["captured_at"]).utcoffset() is not None, "Capture timestamp needs timezone")
    except (TypeError, ValueError) as error:
        raise ValueError("Invalid capture timestamp") from error
    process = manifest["process"]
    exact(process, {"pid", "architecture", "module_base", "image_size"}, "process")
    integer(process["pid"], "pid", 1)
    require(process["architecture"] == "x86", "This capture contract supports x86 only")
    base = integer(process["module_base"], "module_base", 1)
    size = integer(process["image_size"], "image_size", 1, 128 * 1024 * 1024)
    require(base + size <= 2**32, "Image overflows address space")
    scope = manifest["scope"]
    exact(scope, {"purpose", "ranges"}, "scope")
    require(scope["purpose"] == "network-reconstruction", "Trace scope must be network reconstruction")
    require(isinstance(scope["ranges"], list) and 1 <= len(scope["ranges"]) <= 64, "Invalid scope ranges")
    for interval in scope["ranges"]:
        require(isinstance(interval, list) and len(interval) == 2, "Invalid interval")
        lo, hi = (integer(v, "range", 0, 2**32) for v in interval)
        require(base <= lo < hi <= base + size, "Scope exceeds main image")
    require(isinstance(manifest["files"], list) and 1 <= len(manifest["files"]) <= MAX_FILES, "Invalid file count")
    total, paths, events = 0, set(), 0
    for item in manifest["files"]:
        exact(item, {"path", "role", "size", "sha256"}, "file")
        text(item["path"], "path", 200)
        require(item["path"].casefold() not in paths and item["path"].casefold() != "manifest.json", "Duplicate/reserved path")
        paths.add(item["path"].casefold())
        require(isinstance(item["role"], str) and item["role"] in ROLES, "Invalid attachment role")
        require(isinstance(item["sha256"], str) and SHA.fullmatch(item["sha256"]), "Invalid attachment hash")
        total += integer(item["size"], "file size", 0, 128 * 1024 * 1024)
        events += item["role"] == "events"
    require(total <= MAX_TOTAL and events == 1, "Bundle size limit or missing/duplicate events file")


def validate_events(raw, manifest, files):
    events, ids, last_time = [], set(), -1
    ranges = manifest["scope"]["ranges"]
    for line in raw.splitlines():
        require(line and len(line) <= MAX_LINE and len(events) < MAX_EVENTS, "Event count/line limit or blank event")
        event = parse_json(line)
        exact(event, {"id", "seq", "timestamp_ns", "thread_id", "pc", "state", "type", "details"}, "event")
        eid = event["id"]
        require(isinstance(eid, str) and ID.fullmatch(eid) and eid not in ids, "Duplicate/invalid event ID")
        ids.add(eid)
        require(integer(event["seq"], "seq") == len(events), "Event sequence must be contiguous from zero")
        stamp = integer(event["timestamp_ns"], "timestamp_ns", 0, 2**63 - 1)
        require(stamp >= last_time, "Events must be time ordered")
        last_time = stamp
        integer(event["thread_id"], "thread_id", 1)
        pc = integer(event["pc"], "pc")
        require(any(lo <= pc < hi for lo, hi in ranges), "Event pc outside research scope")
        text(event["state"], "observed state", 80)
        kind = event["type"]
        require(isinstance(kind, str) and kind in EVENT_FIELDS, "Unknown event type")
        details = event["details"]
        exact(details, EVENT_FIELDS[kind], f"{kind} details")
        for key, value in details.items():
            if key.endswith("_hex"):
                decode_hex(value)
            elif key.endswith("_va") or key in ("rva", "iat_rva", "module_base", "return_value", "size", "instruction_count"):
                integer(value, key)
            elif key.endswith("_file"):
                require(isinstance(value, str) and value in files, "Missing event attachment")
            elif key.endswith("_ids"):
                require(isinstance(value, list) and 1 <= len(value) <= 100 and all(isinstance(v, str) and ID.fullmatch(v) for v in value), "Invalid evidence references")
            elif key == "symbol":
                if type(value) is int:
                    integer(value, "ordinal", 0, 65535)
                else:
                    text(value, "symbol", 256)
            else:
                text(value, key)
        if "size" in details:
            integer(details["size"], "buffer size", 0, 4096)
            require(details["buffer_va"] + details["size"] <= 2**32, "Buffer range overflow")
            for key in ("before_hex", "after_hex"):
                if key in details:
                    require(len(decode_hex(details[key])) == details["size"], "Buffer length/hex mismatch")
        if kind.startswith("socket_"):
            expected = ("TX", {"send", "WSASend"}) if kind == "socket_send" else ("RX", {"recv", "WSARecv"})
            require(details["direction"] == expected[0] and details["api"] in expected[1], "API/direction mismatch")
        if kind == "function_enter":
            require(decode_hex(details["bytes_hex"]), "Function identity requires observed code bytes")
        if kind == "counter_evidence":
            require(details["gate"] in GATES, "Unknown contradicted gate")
        events.append(event)
    for event in events:
        for key in ("continued_event_ids", "related_event_ids"):
            if key in event["details"]:
                refs = event["details"][key]
                require(all(ref in ids and ref != event["id"] for ref in refs), "Dangling/self event reference")
    return events
