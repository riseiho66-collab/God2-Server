"""Pin the native beast-panel selector/slot crosslink without executing a client.

The same UI byte participates in C2S6B lane0 and in the S2C41 panel-close
comparison. Equality at the latter site does not establish a universal
selector == physical slot invariant for persisted beast instances.
"""
import hashlib
import json

import capstone

from .archive_inputs import ArchivedInputs, SERVER
from .packet_connection_inventory import BASE, IMAGE, PIN


SLICES = (
    (0xA0470, 0xA04AD, "C2S6B lane0 food control reads dragged slot and UI+85ABD"),
    (0xA0840, 0xA0879, "S2C4C snapshot byte3 is copied into UI+85ABD"),
    (0x9FB40, 0x9FBC9, "S2C4B receiver assigns its argument to UI+85ABD in all exits"),
    (0x992A9, 0x992BD, "S2C41 compares inventory slot to UI+85ABD before close"),
)


def recover():
    reader = ArchivedInputs()
    try:
        raw = reader.read(IMAGE)
    finally:
        reader.close()
    if hashlib.sha256(raw).hexdigest() != PIN:
        raise ValueError("Mapped image SHA256 changed")
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    slices = []
    for start, end, purpose in SLICES:
        body = raw[start:end]
        instructions = list(md.disasm(body, BASE + start))
        if not instructions or instructions[-1].address + instructions[-1].size != BASE + end:
            raise ValueError(f"Unaligned native slice {start:X}..{end:X}")
        slices.append({
            "rva": f"{start:X}", "end_rva_exclusive": f"{end:X}",
            "purpose": purpose, "sha256": hashlib.sha256(body).hexdigest(),
            "bytes_hex": body.hex(),
            "instructions": [
                {"rva": f"{i.address-BASE:X}", "instruction": f"{i.mnemonic} {i.op_str}"}
                for i in instructions
            ],
        })
    return {
        "format": "god2-native-companion6b-panel-slot-link-v1",
        "mapped_image": {"path": IMAGE, "sha256": PIN},
        "method": "PINNED_BOUNDED_STATIC_DISASSEMBLY",
        "crosslink": {
            "c2s6b_lane0": "logical 6B|dragged_inventory_slot|UI+85ABD|00",
            "s2c4c": "logical byte3 is copied to UI+85ABD",
            "s2c4b": "receiver argument derived from logical byte1 is copied to UI+85ABD",
            "s2c41": "logical byte3 inventory slot is compared to UI+85ABD; equality calls 49FBD0",
            "qualified_conclusion": "UI+85ABD is the live selected-panel byte and the lane0 target byte; S2C41 uses it as a close comparator for a physical inventory slot",
            "not_proven": [
                "all native panel selectors equal persistent physical inventory slots",
                "the current server CUSTOM-0085 stable selector equals its inventory_slot",
                "food class, consumption, effect, server authority, or causal S2C reply",
            ],
        },
        "current_source": {
            "selection": "src/db/SqliteBeastSnapshotRepository.cpp open_owned_panel emits saved panel selector in S2C4B",
            "custody": "StoredBeastSnapshot keeps inventory_slot and panel.selector separately; no equality invariant is imposed",
            "risk": "Do not treat a S2C41 panel-close comparison as authority to rewrite or consume a selected beast at that physical slot",
        },
        "new_complete_routes": 0,
        "tests_builds_client_execution_live_mutation": False,
    }


def main():
    out = SERVER / "artifacts/integration/packet-connections-20261006/companion6b-panel-slot-link-v1.json"
    if out.exists():
        raise FileExistsError("Preserve prior native evidence")
    out.write_text(json.dumps(recover(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"artifact": str(out), "method": "STATIC_NATIVE_REVIEW"}))


if __name__ == "__main__":
    main()
