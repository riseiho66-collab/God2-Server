"""Locate direct current-client calls to the qualified C2S queue append.

These are investigation candidates, not a complete producer or opcode census.
Indirect calls, wrapper calls and branch semantics need separate qualification.
"""

import argparse
import json
import struct
from pathlib import Path

import pefile

from tools.strike_lab import current_protocol_coverage as native

QUEUE_RVA = 0x132E0


def find_calls(image):
    pe = pefile.PE(data=image, fast_load=True)
    rows = []
    for section in pe.sections:
        # The unpacked mapped image retains packer-era PE section flags: .text
        # advertises DATA rather than EXECUTE. Use its name and bounded RVA,
        # then independently validate each candidate's call displacement.
        if section.Name.rstrip(b"\x00") != b".text":
            continue
        start = section.VirtualAddress
        stop = min(len(image), start + max(section.Misc_VirtualSize, section.SizeOfRawData))
        for rva in range(start, stop - 4):
            if image[rva] != 0xE8:
                continue
            target = rva + 5 + struct.unpack_from("<i", image, rva + 1)[0]
            if target != QUEUE_RVA:
                continue
            rows.append({
                "call_rva": f"{rva:06X}",
                "section": section.Name.rstrip(b"\x00").decode("ascii", "replace"),
                "preceding_24_hex": image[max(start, rva - 24):rva].hex(),
                "evidence": "DIRECT_CALL_BYTE_CANDIDATE_ONLY",
            })
    return rows


def build_report():
    image = native.qualified_image()
    rows = find_calls(image)
    return {
        "format": "current-c2s-queue-caller-candidates-v1",
        "image_sha256": native.IMAGE_SHA256,
        "queue_rva": f"{QUEUE_RVA:06X}",
        "direct_call_candidates": len(rows),
        "rows": rows,
        "scope": "Byte candidates in executable sections only; no opcode or gameplay meaning inferred",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = json.dumps(build_report(), indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report, encoding="utf-8")
        print(f"wrote {args.output}")
    else:
        print(report, end="")
