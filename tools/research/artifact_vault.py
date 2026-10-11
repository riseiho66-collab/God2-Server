"""Content-addressed GOD2 research artifacts. Never executes a client."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import sqlite3
import sys
import tempfile
from datetime import datetime, timezone

import pefile

MAX_FILE = 128 * 1024 * 1024
SHA = re.compile(r"[0-9a-f]{64}\Z")
ANALYZER = "god2-pe-static-v1/pefile-2024.8.26"


def json_bytes(value):
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n").encode()


def digest(data):
    return {"sha256": hashlib.sha256(data).hexdigest(),
            "md5": hashlib.md5(data, usedforsecurity=False).hexdigest(), "size": len(data)}


def bounded_read(path):
    with Path(path).open("rb") as stream:
        data = stream.read(MAX_FILE + 1)
    if len(data) > MAX_FILE:
        raise ValueError("Artifact exceeds 128 MiB research limit")
    return data


def inspect_pe(data):
    """PE declarations are observations, not claims about runtime behavior."""
    if pefile.__version__ != "2024.8.26":
        raise ValueError("Install pinned tools/research/requirements.txt")
    try:
        pe = pefile.PE(data=data, fast_load=True)
    except pefile.PEFormatError as error:
        raise ValueError(f"Invalid PE: {error}") from error
    try:
        sections = []
        for section in pe.sections:
            offset, size = section.PointerToRawData, section.SizeOfRawData
            if size and (offset > len(data) or size > len(data) - offset):
                raise ValueError("Truncated section raw data")
            sections.append({"name": section.Name.rstrip(b"\0").decode("ascii", "backslashreplace"),
                             "rva": section.VirtualAddress, "virtual_size": section.Misc_VirtualSize,
                             "raw_offset": offset, "raw_size": size,
                             "characteristics": section.Characteristics,
                             "raw_sha256": hashlib.sha256(data[offset:offset + size]).hexdigest()})
        if len(sections) != pe.FILE_HEADER.NumberOfSections:
            raise ValueError("Incomplete PE section table")
        pe.parse_data_directories(directories=[pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_IMPORT"]])
        imports = []
        for descriptor in getattr(pe, "DIRECTORY_ENTRY_IMPORT", []):
            imports.append({"dll": descriptor.dll.decode("ascii", "backslashreplace"),
                            "first_thunk_rva": descriptor.struct.FirstThunk,
                            "symbols": [{"name": entry.name.decode("ascii", "backslashreplace") if entry.name else None,
                                         "ordinal": entry.ordinal,
                                         "iat_rva": entry.address - pe.OPTIONAL_HEADER.ImageBase}
                                        for entry in descriptor.imports]})
        packed = any(s["name"].lower() in (".aspack", ".adata") for s in sections)
        return {"machine": pe.FILE_HEADER.Machine,
                "architecture": {0x14c: "x86", 0x8664: "x64"}.get(pe.FILE_HEADER.Machine, "other"),
                "pe_timestamp": pe.FILE_HEADER.TimeDateStamp,
                "pe_timestamp_trusted": False,
                "image_base": pe.OPTIONAL_HEADER.ImageBase,
                "entry_rva": pe.OPTIONAL_HEADER.AddressOfEntryPoint,
                "entry_va": pe.OPTIONAL_HEADER.ImageBase + pe.OPTIONAL_HEADER.AddressOfEntryPoint,
                "size_of_headers": pe.OPTIONAL_HEADER.SizeOfHeaders,
                "size_of_image": pe.OPTIONAL_HEADER.SizeOfImage,
                "sections": sections, "imports": imports,
                "parser_warnings": pe.get_warnings(),
                "packer_status": "ASPACK_LIKE_INDICATORS" if packed else "UNKNOWN",
                "packer_confidence": "HYPOTHESIS" if packed else "UNKNOWN"}
    finally:
        pe.close()


class Vault:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.clients = self.root / "clients"

    def location(self, artifact_id):
        if not SHA.fullmatch(artifact_id):
            raise ValueError("Artifact ID must be a lowercase SHA256")
        path = self.clients / artifact_id
        if path.resolve() != path:
            raise ValueError("Symlink/reparse-point artifact paths are not accepted")
        return path

    def connect(self, readonly=False):
        if readonly:
            db = sqlite3.connect((self.root / "research.db").as_uri() + "?mode=ro", uri=True)
            if db.execute("PRAGMA user_version").fetchone()[0] != 1:
                db.close()
                raise ValueError("Unsupported research database version")
            return db
        self.root.mkdir(parents=True, exist_ok=True)
        db = sqlite3.connect(self.root / "research.db")
        db.execute("PRAGMA foreign_keys=ON")
        version = db.execute("PRAGMA user_version").fetchone()[0]
        if version not in (0, 1):
            db.close()
            raise ValueError("Unsupported research database version")
        with db:
            db.execute("CREATE TABLE IF NOT EXISTS artifacts (id TEXT PRIMARY KEY, parent TEXT REFERENCES artifacts(id), metadata_sha256 TEXT NOT NULL, kind TEXT NOT NULL)")
            db.execute("CREATE TABLE IF NOT EXISTS sources (artifact TEXT REFERENCES artifacts(id), path TEXT NOT NULL, observed_at TEXT NOT NULL, PRIMARY KEY(artifact,path))")
            db.execute("CREATE TABLE IF NOT EXISTS evidence (id TEXT PRIMARY KEY, artifact TEXT NOT NULL REFERENCES artifacts(id), kind TEXT NOT NULL, confidence TEXT NOT NULL, claim TEXT NOT NULL)")
            db.execute("PRAGMA user_version=1")
        return db

    def verify(self, artifact_id, check_index=True, _ancestors=frozenset()):
        if artifact_id in _ancestors or len(_ancestors) >= 64:
            raise ValueError("Cyclic or excessively deep artifact provenance")
        folder = self.location(artifact_id)
        raw_metadata = bounded_read(folder / "metadata.json")
        metadata = json.loads(raw_metadata)
        hashes = json.loads(bounded_read(folder / "hashes.json"))
        if metadata["schema_version"] != 1 or metadata["artifact_id"] != artifact_id:
            raise ValueError("Metadata identity/version mismatch")
        if metadata["kind"] not in ("original", "unpacked"):
            raise ValueError("Unknown artifact kind")
        slot = "original" if metadata["kind"] == "original" else "unpacked"
        binary = folder / slot / "client.exe"
        if binary.resolve() != binary:
            raise ValueError("Binary must not be a symlink/reparse point")
        data = bounded_read(binary)
        actual = digest(data)
        if actual != metadata["hashes"] or actual["sha256"] != artifact_id:
            raise ValueError("Binary hash/size mismatch")
        if hashes != {"binary": actual, "metadata_sha256": hashlib.sha256(raw_metadata).hexdigest()}:
            raise ValueError("Metadata manifest mismatch")
        if metadata["analyzer"] != ANALYZER or inspect_pe(data) != metadata["pe"]:
            raise ValueError("Static analysis metadata mismatch")
        parent = metadata["parent_artifact"]
        if (metadata["kind"] == "original" and parent is not None) or (metadata["kind"] == "unpacked" and parent is None):
            raise ValueError("Invalid provenance relation")
        if parent is not None:
            if parent == artifact_id or not (self.location(parent) / "metadata.json").is_file():
                raise ValueError("Missing or self-referencing parent")
            self.verify(parent, _ancestors=_ancestors | {artifact_id})
        if check_index:
            db = self.connect(readonly=True)
            try:
                row = db.execute("SELECT metadata_sha256,parent,kind FROM artifacts WHERE id=?", (artifact_id,)).fetchone()
                if row != (hashes["metadata_sha256"], parent, metadata["kind"]):
                    raise ValueError("Research index disagrees with artifact manifest")
            finally:
                db.close()
        return metadata

    def ingest(self, source, kind="original", parent=None):
        source = Path(source).resolve(strict=True)
        if kind not in ("original", "unpacked"):
            raise ValueError("Unknown artifact kind")
        if kind == "original" and parent is not None:
            raise ValueError("Original artifacts have no claimed parent")
        if kind == "unpacked" and parent is None:
            raise ValueError("Derived images require a parent artifact")
        if parent is not None:
            self.verify(parent)
        data = bounded_read(source)
        hashes = digest(data)
        artifact_id = hashes["sha256"]
        if parent == artifact_id:
            raise ValueError("A derived artifact must differ from its parent")
        metadata = {"schema_version": 1, "artifact_id": artifact_id, "kind": kind,
                    "parent_artifact": parent, "hashes": hashes, "analyzer": ANALYZER,
                    "ingested_at": datetime.now(timezone.utc).isoformat(),
                    "initial_source": str(source), "pe": inspect_pe(data),
                    "analysis_status": "STATIC_ONLY", "oep_status": "UNKNOWN",
                    "unpack_status": "NOT_ATTEMPTED" if kind == "original" else "UNVERIFIED_CANDIDATE",
                    "compatibility_status": "RESEARCH_PARTIAL_COMPATIBILITY"}
        target = self.location(artifact_id)
        self.clients.mkdir(parents=True, exist_ok=True)
        if target.exists():
            existing = self.verify(artifact_id, check_index=False)
            if (existing["kind"], existing["parent_artifact"]) != (kind, parent):
                raise ValueError("Existing artifact has different provenance; refusing overwrite")
        else:
            staging = Path(tempfile.mkdtemp(prefix=".ingest-", dir=self.clients))
            try:
                for name in ("original", "unpacked", "memory_images", "imports"):
                    (staging / name).mkdir()
                slot = "original" if kind == "original" else "unpacked"
                (staging / slot / "client.exe").write_bytes(data)
                raw_metadata = json_bytes(metadata)
                (staging / "metadata.json").write_bytes(raw_metadata)
                (staging / "hashes.json").write_bytes(json_bytes({"binary": hashes, "metadata_sha256": hashlib.sha256(raw_metadata).hexdigest()}))
                # Publish a complete artifact directory; never replace a known artifact.
                staging.rename(target)
            finally:
                if staging.exists():
                    if staging.resolve().parent != self.clients.resolve() or not staging.name.startswith(".ingest-"):
                        raise ValueError("Unsafe staging cleanup path")
                    shutil.rmtree(staging)
        metadata = self.verify(artifact_id, check_index=False)
        metadata_sha = hashlib.sha256(bounded_read(target / "metadata.json")).hexdigest()
        db = self.connect()
        try:
            with db:
                known = db.execute("SELECT metadata_sha256,parent,kind FROM artifacts WHERE id=?", (artifact_id,)).fetchone()
                if known is not None and known != (metadata_sha, parent, kind):
                    raise ValueError("Existing research record changed; refusing re-index")
                db.execute("INSERT OR IGNORE INTO artifacts VALUES(?,?,?,?)", (artifact_id, parent, metadata_sha, kind))
                db.execute("INSERT OR IGNORE INTO sources VALUES(?,?,?)", (artifact_id, str(source), datetime.now(timezone.utc).isoformat()))
                db.execute("INSERT OR IGNORE INTO evidence VALUES(?,?,?,?,?)", (f"STATIC-PE-{artifact_id}", artifact_id, "STATIC_PE", "CONFIRMED_STATIC", "On-disk PE declarations only; not runtime behavior or verified protocol"))
        finally:
            db.close()
        self.verify(artifact_id)
        return {"artifact_id": artifact_id, "path": str(target), "kind": kind}

    def ids(self):
        if not self.clients.exists():
            return []
        return sorted(p.name for p in self.clients.iterdir() if SHA.fullmatch(p.name))


def candidate(metadata, va):
    rva = va - metadata["pe"]["image_base"]
    matches = [s for s in metadata["pe"]["sections"]
               if s["rva"] <= rva < s["rva"] + max(s["virtual_size"], s["raw_size"])]
    if len(matches) > 1:
        raise ValueError("Ambiguous overlapping section mapping")
    section = matches[0] if matches else None
    backed = section is not None and rva - section["rva"] < section["raw_size"]
    return {"artifact_id": metadata["artifact_id"], "candidate_va": va, "candidate_rva": rva,
            "section": section["name"] if section else None, "file_backed": backed,
            "file_offset": section["raw_offset"] + rva - section["rva"] if backed else None,
            "oep_confidence": "UNKNOWN", "requires": "Observed unpack transition and runtime validation"}


def compare(left, right):
    def imports(meta):
        # pefile may attach a lookup-table name to ordinal imports. Preserve the
        # on-disk ordinal rather than presenting that hint as a named import.
        return {f"{entry['dll'].lower()}!{('#' + str(symbol['ordinal'])) if symbol['ordinal'] is not None else symbol['name']}"
                for entry in meta["pe"]["imports"] for symbol in entry["symbols"]}
    a, b = imports(left), imports(right)
    return {"left": left["artifact_id"], "right": right["artifact_id"],
            "scope": "ON_DISK_PE_ONLY", "function_matching": "NOT_PERFORMED",
            "protocol_differences": "UNKNOWN",
            "changed_headers": {key: {"left": left["pe"][key], "right": right["pe"][key]}
                                for key in ("machine", "image_base", "entry_rva", "size_of_image", "pe_timestamp")
                                if left["pe"][key] != right["pe"][key]},
            "common_imports": sorted(a & b), "removed_imports": sorted(a - b), "added_imports": sorted(b - a),
            "left_sections": left["pe"]["sections"], "right_sections": right["pe"]["sections"]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2] / "artifacts")
    parser.add_argument("--output", type=Path, help="Create a new JSON report; refuses to overwrite")
    commands = parser.add_subparsers(dest="command", required=True)
    ingest = commands.add_parser("ingest")
    ingest.add_argument("source", type=Path)
    ingest.add_argument("--kind", choices=["original", "unpacked"], default="original")
    ingest.add_argument("--parent")
    verify = commands.add_parser("verify")
    verify.add_argument("artifact", default="all", nargs="?")
    commands.add_parser("list")
    diff = commands.add_parser("compare")
    diff.add_argument("left"); diff.add_argument("right")
    oep = commands.add_parser("candidate")
    oep.add_argument("artifact"); oep.add_argument("--va", required=True, type=lambda value: int(value, 0))
    args = parser.parse_args(argv)
    vault = Vault(args.root)
    try:
        if args.command == "ingest":
            result = vault.ingest(args.source, args.kind, args.parent)
        elif args.command in ("verify", "list"):
            ids = vault.ids() if args.command == "list" or args.artifact == "all" else [args.artifact]
            if args.command == "verify" and not ids:
                raise ValueError("No artifacts to verify")
            result = [{"artifact_id": key, "integrity": "PASS", "analysis_status": vault.verify(key)["analysis_status"]} for key in ids]
        elif args.command == "compare":
            result = compare(vault.verify(args.left), vault.verify(args.right))
        else:
            result = candidate(vault.verify(args.artifact), args.va)
        if args.output:
            with args.output.open("x", encoding="utf-8") as output:
                output.write(json_bytes(result).decode())
        print(json.dumps(result, indent=2))
        return 0
    except (ValueError, OSError, sqlite3.Error, KeyError, TypeError) as error:
        print(f"Research error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
