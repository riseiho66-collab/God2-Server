"""Current-build packet inventory with deliberately separate evidence layers.

The client's receive-length table is S2C only. The formal server's world
switch is C2S only. Neither a table entry nor a parser case proves gameplay.
"""

import argparse
import hashlib
import json
from pathlib import Path
import re

from tools.strike_lab import current_protocol_coverage as native

ROOT = Path(__file__).resolve().parents[2]
WORLD = ROOT / "src/protocol/RecoveredWorldRecords.h"
WORLD_SERVICE = ROOT / "src/handlers/RecoveredWorldService.cpp"
APPLICATION = ROOT / "src/core/Application.cpp"
CASE = re.compile(r"(?:^\s*|(?<=:)\s*)case\s+(0x[0-9a-fA-F]+|Recovered\w+::\w+)\s*:", re.M)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def resolve_case(expression):
    if expression.startswith("0x"):
        return int(expression, 16), None
    owner, field = expression.split("::", 1)
    header = ROOT / "src/protocol" / f"{owner}.h"
    if not header.is_file():
        raise ValueError(f"Missing opcode owner: {header}")
    match = re.search(rf"\b{re.escape(field)}\s*=\s*(0x[0-9a-fA-F]+)\b", header.read_text("utf-8"))
    if not match:
        raise ValueError(f"Unresolved opcode constant: {expression}")
    return int(match.group(1), 16), {"path": str(header.relative_to(ROOT)), "sha256": sha256(header)}


def world_parser_cases():
    source = WORLD.read_text("utf-8")
    rows, seen = [], {}
    for match in CASE.finditer(source):
        expression = match.group(1)
        opcode, owner = resolve_case(expression)
        if not 0 <= opcode <= 255:
            raise ValueError(f"Opcode outside byte domain: {expression}")
        if opcode in seen:
            raise ValueError(f"Duplicate C2S switch opcode {opcode:02X}: {seen[opcode]}, {expression}")
        seen[opcode] = expression
        rows.append({
            "opcode": opcode, "opcode_hex": f"{opcode:02X}", "case": expression,
            "line": source.count("\n", 0, match.start()) + 1,
            "owner": owner, "evidence": "FORMAL_C2S_WORLD_PARSER_CASE_ONLY",
        })
    if not rows:
        raise ValueError("No C2S world parser cases found")
    return sorted(rows, key=lambda row: row["opcode"])


def build_report():
    image = native.qualified_image()
    catalog = native.native_catalog(image)
    receive = catalog["counts"]
    parsed = world_parser_cases()
    # Current native FUN_00473e00 emits 74 plus one stack byte. The byte is
    # unwritten in this producer; do not infer a value or server response.
    if image[0x73E0B:0x73E10] != bytes.fromhex("6a01506a74"):
        raise ValueError("C2S74 producer argument binding changed")
    native.call_binding(image, 0x73E10, 0x132E0)
    if image[0x72BD8:0x72BDA] != bytes.fromhex("6a02") or \
       image[0x72BE1:0x72BE6] != bytes.fromhex("6888000000"):
        raise ValueError("C2S88 producer argument binding changed")
    native.call_binding(image, 0x72BF4, 0x132E0)
    if not {0x74,0x88} <= {row["opcode"] for row in parsed}:
        raise ValueError("C2S74/88 formal parser route disappeared")
    for path in (WORLD_SERVICE, APPLICATION):
        source = path.read_text("utf-8")
        for variant in ("ClientOpaque74", "ClientPanelOpen88"):
            if f"std::holds_alternative<RecoveredWorldRecords::{variant}>(records.front())" not in source:
                raise ValueError(f"C2S74/88 runtime forwarding disappeared: {path} {variant}")
    if sum(receive.values()) != 256:
        raise ValueError("Native S2C byte-domain census is incomplete")
    return {
        "format": "current-packet-gap-ledger-v1",
        "native_image_sha256": native.IMAGE_SHA256,
        "world_parser": {"path": str(WORLD.relative_to(ROOT)), "sha256": sha256(WORLD)},
        "panel_runtime_sources": [
            {"path": str(path.relative_to(ROOT)), "sha256": sha256(path)}
            for path in (WORLD_SERVICE, APPLICATION)
        ],
        "s2c_receive_lengths": {
            "byte_domain": 256, "fixed": receive["FIXED"],
            "variable": receive["VARIABLE_U16"], "unsupported": receive["UNSUPPORTED"],
            "meaning": "Length contracts only; no handler, server emitter or client acceptance inferred",
        },
        "c2s_world_parser": {
            "distinct_opcodes": len(parsed), "cases": parsed,
            "meaning": "World-stage parser cases only; excludes login/character stages and unparsed producers",
        },
        "newly_connected_c2s_producers": [{
            "opcode": 0x74, "opcode_hex": "74", "logical_size": 2,
            "producer_rva": "073E00", "queue_call_rva": "073E10",
            "payload": "One stack byte; no producer write qualified",
            "caller": "00473600 local UI mode transition (0/2 to 1)",
            "status": "CANDIDATE_TRANSPORT_ACCEPTED_CURRENT_CLIENT",
            "acceptance": "Hidden-desktop original client Ctrl+F, then native panel control 7; opcode 74 admitted, UI mode 0 to 1",
            "remaining": "Authoritative gameplay effect and formal deployment remain unverified",
        }, {
            "opcode": 0x88, "opcode_hex": "88", "logical_size": 3,
            "producer_rva": "072BD0", "queue_call_rva": "072BF4",
            "payload": "Two raw bytes copied from a UI-selected WORD; meaning unqualified",
            "caller": "00472E80 panel-opening path",
            "status": "CANDIDATE_TRANSPORT_ACCEPTED_CURRENT_CLIENT",
            "acceptance": "Hidden-desktop original client Ctrl+F opens widget 77 and sends opcode 88; no reply observed",
            "remaining": "Authoritative panel response and formal deployment remain unverified",
        }],
        "current_client_acceptance_receipt": "artifacts/playtests/private-panel-88-74-20260930-03/run-result.json",
        "whole_game_completion_percent": None,
        "missing_denominator": [
            "Exhaustive current-client C2S producer and state/variant inventory",
            "Per-route authoritative server handler/response and persistence classification",
            "Per-route current original-client acceptance classification",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="Write the reproducible report to this path")
    arguments = parser.parse_args()
    report = json.dumps(build_report(), ensure_ascii=False, indent=2) + "\n"
    if arguments.output:
        arguments.output.parent.mkdir(parents=True, exist_ok=True)
        arguments.output.write_text(report, encoding="utf-8")
    else:
        print(report, end="")


if __name__ == "__main__":
    main()
