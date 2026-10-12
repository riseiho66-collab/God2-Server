"""Seal only retained static-source artifacts; execute no target code."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DEST = ROOT / "seal.json"
HELPERS = (
    "discover_computed_bias353.py",
    "capture_computed_bank_source353.py",
    "close_computed_callers353.py",
    "seal_computed_bank_source353.py",
)

def digest(blob):
    return hashlib.sha256(blob).hexdigest()

def main():
    if DEST.exists():
        raise SystemExit("Refusing to overwrite immutable seal")
    members = []
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file():
            continue
        blob = path.read_bytes()
        members.append({"name": path.relative_to(ROOT).as_posix(),
                        "bytes": len(blob), "sha256": digest(blob)})
    helper_metadata = []
    for name in HELPERS:
        blob = (ROOT / name).read_bytes()
        assert b"\r" not in blob and not blob.startswith(b"\xef\xbb\xbf"), name
        helper_metadata.append({"name": name, "bytes": len(blob),
                                "sha256": digest(blob)})
    seal = {"schema": "individual-member-sha256-source-seal-v1",
            "round": 353, "static_source_only": True,
            "member_count": len(members),
            "member_bytes": sum(row["bytes"] for row in members),
            "credits": {"method": 0, "opcode": 0, "format": 0, "route": 0},
            "members": members}
    blob = (json.dumps(seal, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    with DEST.open("xb") as output:
        output.write(blob)
    retained = json.loads(DEST.read_bytes())
    for row in retained["members"]:
        actual = (ROOT / row["name"]).read_bytes()
        assert len(actual) == row["bytes"] and digest(actual) == row["sha256"], row["name"]
    assert retained["member_count"] == len(retained["members"])
    assert retained["member_bytes"] == sum(row["bytes"] for row in retained["members"])
    print(json.dumps({"seal": str(DEST), "seal_bytes": len(blob),
                      "seal_sha256": digest(blob),
                      "member_count": retained["member_count"],
                      "member_bytes": retained["member_bytes"],
                      "successful_lf_helpers": helper_metadata}, indent=2))

if __name__ == "__main__":
    main()
