"""Hash-pinned, local-only x86 crypto capsule. Never launches the client.

Extracted bytes are research artifacts, not source or distribution inputs.
Requires Capstone for instruction-boundary and direct-dependency validation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
LOCAL_PACKAGES = ROOT / 'artifacts/tooling/crypto-oracle-python'
if LOCAL_PACKAGES.is_dir():
    sys.path.insert(0, str(LOCAL_PACKAGES))

from capstone import Cs, CS_ARCH_X86, CS_MODE_32, CS_GRP_CALL, CS_GRP_JUMP, CS_GRP_RET
from capstone.x86 import X86_OP_IMM

DEFAULT_IMAGE = ROOT / "artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin"
DEFAULT_CLIENT = ROOT.parent / "God2/God2.exe"
SOURCE_SHA256 = "149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763"
EXE_SHA256 = "fb72296cab5950b74d8f7c98155145f7c5f58749c3011adb0540325b60749dd1"
IMAGE_BASE = 0x400000
ENTRIES = {"init_session": 0x410570, "encrypt": 0x410690, "decrypt": 0x4106F0}
# Half-open instruction ranges; no alignment padding or neighboring functions.
FUNCTIONS = {
    0x410370: ("derive_helper", 0x4103E4),
    0x410420: ("derive_proof", 0x410487),
    0x410490: ("derive_key", 0x4104F6),
    0x410570: ("init_session", 0x41059A),
    0x410690: ("encrypt", 0x4106E6),
    0x4106F0: ("decrypt", 0x410747),
    0x410910: ("cipher_enabled", 0x410914),
}
ABI = {
    "architecture": "x86", "bits": 32, "byte_order": "little",
    "calling_convention": "thiscall", "object_register": "ECX",
    "object_size": 0x255C, "minimum_crypto_object_size": 0x2557,
    "object_size_basis": "buffer covers constructor's final DWORD at +0x2558; crypto accesses end at +0x2557",
    "fields": {
        "cipher_enabled": {"offset": 8, "size": 4},
        "key": {"offset": 0x2420, "size": 256},
        "proof": {"offset": 0x2520, "size": 16},
        "feedback": {"offset": 0x2556, "size": 1},
    },
    "init_session": {"seed_pointer_stack_offset": 4, "seed_size": 16,
                     "callee_pop_bytes": 4, "sets_cipher_enabled": False},
    "encrypt": {"buffer_pointer_stack_offset": 4, "length_stack_offset": 8,
                "length_type": "int32", "callee_pop_bytes": 8, "in_place": True},
    "decrypt": {"buffer_pointer_stack_offset": 4, "length_stack_offset": 8,
                "length_type": "int32", "callee_pop_bytes": 8, "in_place": True},
    "return_value": "unspecified; consume memory output",
    "packet_state": "key index starts at zero and feedback reloads per call; neither is persisted",
}


class CapsuleError(ValueError):
    """Invalid, mixed, unsupported, or tampered capsule."""


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _source(path: Path, expected: str) -> bytes:
    data = path.read_bytes()
    if _sha(data) != expected:
        raise CapsuleError(f"Untrusted source SHA256: {path}")
    return data


def _slice(image: bytes, address: int, size: int) -> bytes:
    offset = address - IMAGE_BASE
    if offset < 0 or size < 1 or offset + size > len(image):
        raise CapsuleError("Source RVA outside restored image")
    return image[offset:offset + size]


def _discover(image: bytes) -> tuple[list[int], list[dict]]:
    """Follow only decoded direct calls; reject unresolved edges and code gaps."""
    decoder = Cs(CS_ARCH_X86, CS_MODE_32)
    decoder.detail = True
    pending = list(ENTRIES.values())
    visited = set()
    calls = []
    while pending:
        start = pending.pop()
        if start in visited:
            continue
        if start not in FUNCTIONS:
            raise CapsuleError(f"Unapproved call target: {start:#x}")
        visited.add(start)
        _, end = FUNCTIONS[start]
        raw = _slice(image, start, end - start)
        instructions = list(decoder.disasm(raw, start))
        if sum(i.size for i in instructions) != len(raw):
            raise CapsuleError("Incomplete instruction decode")
        by_address = {i.address: i for i in instructions}
        reachable = set()
        work = [start]
        while work:
            address = work.pop()
            if address in reachable:
                continue
            if address not in by_address:
                raise CapsuleError(f"Invalid control-flow boundary: {address:#x}")
            reachable.add(address)
            insn = by_address[address]
            if insn.group(CS_GRP_RET):
                if insn.mnemonic != "ret":
                    raise CapsuleError("Unsupported return")
                continue
            if insn.group(CS_GRP_CALL) or insn.group(CS_GRP_JUMP):
                if len(insn.operands) != 1 or insn.operands[0].type != X86_OP_IMM:
                    raise CapsuleError("Indirect call/jump is forbidden")
                target = insn.operands[0].imm
                if insn.group(CS_GRP_CALL):
                    if target not in FUNCTIONS:
                        raise CapsuleError(f"Unresolved/API call: {target:#x}")
                    pending.append(target)
                    calls.append({"instruction": address, "target": target})
                else:
                    work.append(target)
                    if insn.mnemonic == "jmp":
                        continue
            if insn.mnemonic in {"int", "int3", "syscall", "sysenter", "hlt"}:
                raise CapsuleError("External execution dependency")
            work.append(address + insn.size)
        if reachable != set(by_address):
            raise CapsuleError("Unreachable bytes inside approved function")
    return sorted(visited), sorted(calls, key=lambda item: item["instruction"])


def _manifest(image: bytes, image_path: Path, client_path: Path) -> dict:
    functions, calls = _discover(image)
    regions = []
    pages = set()
    for address in functions:
        name, end = FUNCTIONS[address]
        regions.append({"name": name, "address": address, "size": end - address,
                        "kind": "CODE", "file": f"{name}.bin",
                        "sha256": _sha(_slice(image, address, end - address))})
        pages.update(range((address - IMAGE_BASE) & ~0xFFF,
                           ((end - 1 - IMAGE_BASE) & ~0xFFF) + 0x1000, 0x1000))
    regions.append({"name": "lookup", "address": 0x584C30, "size": 1024,
                    "kind": "CONSTANT_TABLE", "file": "lookup.bin",
                    "sha256": _sha(_slice(image, 0x584C30, 1024))})
    return {
        "format_version": 1, "image_base": IMAGE_BASE,
        "original_exe": {"path": str(client_path), "sha256": EXE_SHA256},
        "restored_image": {"path": str(image_path), "sha256": SOURCE_SHA256},
        "entries": dict(ENTRIES), "regions": regions,
        "code_pages": [{"rva": rva, "sha256": _sha(_slice(image, IMAGE_BASE + rva, 4096))}
                       for rva in sorted(pages)],
        "abi": ABI, "direct_calls": calls, "local_only": True,
    }


def _artifact_path(directory: Path, filename: str) -> Path:
    if not isinstance(filename, str) or not filename or any(c in filename for c in "/\\:") or filename in {".", ".."}:
        raise CapsuleError("Artifact path excursion")
    path = directory / filename
    if path.is_symlink() or path.resolve().parent != directory.resolve():
        raise CapsuleError("Artifact path excursion")
    return path


def extract(capsule_dir: str | Path, image_path: str | Path = DEFAULT_IMAGE,
            client_path: str | Path = DEFAULT_CLIENT) -> Path:
    """Write minimal local artifacts and return the verified capsule.json path."""
    image_path, client_path = Path(image_path).resolve(), Path(client_path).resolve()
    image = _source(image_path, SOURCE_SHA256)
    _source(client_path, EXE_SHA256)
    manifest = _manifest(image, image_path, client_path)
    directory = Path(capsule_dir).resolve()
    directory.mkdir(parents=True, exist_ok=True)
    _artifact_path(directory, ".gitignore").write_text("*\n", encoding="ascii")
    for region in manifest["regions"]:
        _artifact_path(directory, region["file"]).write_bytes(
            _slice(image, region["address"], region["size"]))
    destination = _artifact_path(directory, "capsule.json")
    destination.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    load_capsule(destination)
    return destination


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise CapsuleError(f"Duplicate manifest key: {key}")
        result[key] = value
    return result


def load_capsule(path: str | Path) -> dict:
    """Return a verified manifest; region files are relative to path.parent.

    The editable manifest is not a trust anchor. Rebuild the expected manifest
    from independently pinned source bytes, then compare every extracted range
    to its exact source RVA. The source and original executable must remain local.
    """
    path = Path(path)
    if path.is_symlink():
        raise CapsuleError("Manifest symlink is forbidden")
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_unique_object)
        if type(manifest) is not dict or type(manifest.get("format_version")) is not int or manifest["format_version"] != 1:
            raise CapsuleError("Unsupported capsule format version")
        source_paths = []
        for key, expected_hash in (("restored_image", SOURCE_SHA256), ("original_exe", EXE_SHA256)):
            identity = manifest[key]
            source_path = Path(identity["path"])
            if not source_path.is_absolute() or ".." in source_path.parts:
                raise CapsuleError("Source path must be absolute without traversal")
            if identity["sha256"] != expected_hash:
                raise CapsuleError("Source identity is not pinned")
            source_paths.append(source_path)
        image = _source(source_paths[0], SOURCE_SHA256)
        _source(source_paths[1], EXE_SHA256)
        expected = _manifest(image, *source_paths)
        # JSON comparison preserves numeric types (True must not equal address 1).
        if json.dumps(manifest, sort_keys=True) != json.dumps(expected, sort_keys=True):
            raise CapsuleError("Manifest differs from pinned source contract")
        for region in manifest["regions"]:
            data = _artifact_path(path.parent, region["file"]).read_bytes()
            if _sha(data) != region["sha256"] or data != _slice(image, region["address"], region["size"]):
                raise CapsuleError(f"Artifact differs from pinned source: {region['name']}")
        return manifest
    except (OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
        raise CapsuleError(f"Invalid capsule: {exc}") from exc


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts/crypto-oracle/capsule")
    parser.add_argument("--image", type=Path, default=DEFAULT_IMAGE)
    parser.add_argument("--client", type=Path, default=DEFAULT_CLIENT)
    args = parser.parse_args()
    print(extract(args.output, args.image, args.client))


if __name__ == "__main__":
    main()
