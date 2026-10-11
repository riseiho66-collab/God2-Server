"""Export bounded offline decoded-buffer dumps to enemy capture JSONL.

Reads explicit slices of existing binary dumps with supplied full-file SHA256;
does not attach/read a live process, sniff packets, decrypt, infer a buffer,
or manufacture an official observation. Layout is caller-supplied and audited
separately. PCAP/TCP wire is intentionally not accepted as decoded logical data.
"""
import argparse
import hashlib
import json
from pathlib import Path


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def export(manifest_path, output):
    if output.exists():
        raise ValueError("New output required; never overwrite evidence")
    if manifest_path.stat().st_size > 8 * 1024 * 1024:
        raise ValueError("Manifest size bound")
    manifest_bytes = manifest_path.read_bytes()
    spec = json.loads(manifest_bytes)
    if spec.get("schema") != "enemy-decoded-slices-v1":
        raise ValueError("Explicit decoded slice schema required")
    header = spec.get("capture")
    if not isinstance(header, dict) or header.get("stage") != "decoded_s2c_pre_dispatch_logical":
        raise ValueError("Explicit PRE-DISPATCH S2C decoded stage required")
    if header.get("kind") != "capture" or header.get("schema") != "enemy-passive-jsonl-v1":
        raise ValueError("Capture header required")
    rows = spec.get("events")
    if not isinstance(rows, list) or len(rows) > 100000:
        raise ValueError("Bounded ordered dump events required")
    dumps, seen, records = {}, {}, [dict(header)]
    retained_bytes = 0
    records[0]["slice_manifest_sha256"] = digest(manifest_bytes)
    last = -1
    for row in rows:
        sequence = row.get("sequence")
        if not isinstance(sequence, int) or isinstance(sequence, bool) or sequence <= last:
            raise ValueError("Strictly ordered integer dump-event sequence required")
        last = sequence
        if row.get("kind") == "boundary":
            records.append(row)
            continue
        if row.get("kind") != "slice":
            raise ValueError("Only decoded slice or explicit boundary allowed")
        observation_id = row.get("observation_id")
        if not isinstance(observation_id, str) or not observation_id or len(observation_id) > 256:
            raise ValueError("Capture-side observation ID required for export deduplication")
        path = Path(row["dump_path"])
        if not path.is_absolute():
            path = manifest_path.parent / path
        path = path.resolve()
        expected_sha = row.get("dump_sha256")
        if not isinstance(expected_sha, str) or len(expected_sha) != 64:
            raise ValueError("Explicit full dump SHA256 required")
        if path not in dumps:
            if path.stat().st_size > 32 * 1024 * 1024:
                raise ValueError("Decoded dump bound; provide targeted dump rather than entire process")
            raw = path.read_bytes()
            retained_bytes += len(raw)
            if retained_bytes > 32 * 1024 * 1024:
                raise ValueError("Aggregate decoded dump bound; split capture into bounded manifests")
            dumps[path] = (raw, digest(raw))
        raw, actual_sha = dumps[path]
        if actual_sha != expected_sha:
            raise ValueError("Original dump SHA256 mismatch")
        offset, length = row.get("file_offset"), row.get("logical_length")
        if (not isinstance(offset, int) or isinstance(offset, bool) or offset < 0 or
            not isinstance(length, int) or isinstance(length, bool) or not 1 <= length <= 4096 or
            offset + length > len(raw)):
            raise ValueError("Explicit bounded logical slice offset/length required")
        payload = raw[offset:offset + length]
        signature = (actual_sha, offset, length, row.get("virtual_address"))
        if observation_id in seen:
            if seen[observation_id] != signature:
                raise ValueError("One observation ID references different evidence")
            continue  # Same capture event exported twice; not identical packets at different events.
        seen[observation_id] = signature
        records.append({"kind": "record", "direction": "S2C", "sequence": sequence,
            "timestamp": row.get("timestamp"), "hex": payload.hex(),
            "dump_evidence": {"observation_id": observation_id, "path": str(path),
                "dump_sha256": actual_sha, "file_offset": offset,
                "logical_length": length, "slice_sha256": digest(payload),
                "virtual_address_claimed": row.get("virtual_address"),
                "layout_evidence": row.get("layout_evidence")}})
    serialized = [json.dumps(row, ensure_ascii=False) + "\n" for row in records]
    if sum(len(row.encode("utf-8")) for row in serialized) > 32 * 1024 * 1024:
        raise ValueError("Exported JSONL bound; split capture into bounded manifests")
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8", newline="\n") as stream:
        stream.writelines(serialized)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    export(args.manifest.resolve(), args.output.resolve())


if __name__ == "__main__":
    main()
