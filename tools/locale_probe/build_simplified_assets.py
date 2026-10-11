"""Build the original client's missing -gb tables from its Taiwan tables."""

import argparse
import hashlib
import json
import pathlib
import struct

from opencc import OpenCC
from tools.strike_lab.omega_assets import decode_csvz


def decode_traditional_source(data):
    """Decode the client tables without discarding HKSCS-only source glyphs.

    CP950 is authoritative for the common bytes. Only sequences it rejects
    are retried as one HKSCS character; remaining source defects are marked.
    """
    result = []
    offset = 0
    recovered = unresolved = 0
    while offset < len(data):
        try:
            result.append(data[offset:].decode("cp950"))
            break
        except UnicodeDecodeError as error:
            start = offset + error.start
            result.append(data[offset:start].decode("cp950"))
            try:
                candidate = data[start:start + 2].decode("big5hkscs")
            except UnicodeDecodeError:
                candidate = ""
            if len(candidate) == 1:
                result.append(candidate)
                recovered += 1
                offset = start + 2
            else:
                result.append("?")
                unresolved += 1
                offset += error.end
    return "".join(result), recovered, unresolved


def tables(client):
    table_dir = client / "Data2/Patch/Comm"
    for path in sorted(table_dir.glob("*.csvZ")):
        if "-gb" in path.stem.lower():
            continue
        relative = path.relative_to(client).as_posix()
        target = relative.replace(".csvZ", "-gb.csvZ")
        if path.name.lower() != "actmis.csvz":
            yield relative, target
    yield "Data3/config2.iniZ", "Data3/config2_gb.iniZ"
    yield "Data3/config.iniZ", "Data3/config_gb.iniZ"


def pack_literal(data):
    result = bytearray(b"\x05\x16" + struct.pack("<I", len(data)) + b"Z")
    for offset in range(0, len(data), 8):
        chunk = data[offset:offset + 8]
        result.append((1 << len(chunk)) - 1)
        result.extend(chunk)
    return bytes(result)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("client", type=pathlib.Path)
    parser.add_argument("output", type=pathlib.Path)
    args = parser.parse_args()
    converter = OpenCC("t2s")
    report = []
    for relative, target in tables(args.client):
        raw = (args.client / relative).read_bytes()
        plain = decode_csvz(raw, limit=20_000_000)
        replacements = plain.decode("cp950", errors="replace").count("\ufffd")
        decoded, recovered, unresolved = decode_traditional_source(plain)
        converted = converter.convert(decoded)
        converted = converted.replace("\u2027", "\u00b7").replace("\u00af", "-")
        encoded = converted.encode("cp936", errors="replace")
        encoding_losses = encoded.count(b"?") - converted.count("?")
        if encoded.count(b"\n") != plain.count(b"\n"):
            raise ValueError(f"Line count changed: {relative}")
        packed = pack_literal(encoded)
        if decode_csvz(packed, limit=20_000_000) != encoded:
            raise ValueError(f"Round trip failed: {target}")
        path = args.output / target
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(packed)
        report.append({"source": relative, "target": target,
                       "source_sha256": hashlib.sha256(raw).hexdigest(),
                       "target_sha256": hashlib.sha256(packed).hexdigest(),
                       "decoded_bytes": len(plain), "translated_bytes": len(encoded),
                       "source_undecodable_characters": replacements,
                       "source_hkscs_recoveries": recovered,
                       "source_unresolved_sequences": unresolved,
                       "target_encoding_replacements": encoding_losses})
    (args.output / "conversion-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
