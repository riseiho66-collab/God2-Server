"""CUSTOM-0058: stage the owner-accepted skill against the current formal client.

This dated, version-pinned helper only creates a new release directory. It never
installs, starts processes, changes launcher settings, or copies the private EXE.
The bootstrap names the final local DLL location, not the staging directory.
"""
from __future__ import annotations

import json
from pathlib import Path
import struct

import pefile

from tools.skills import build_shunying_client as data
from tools.skills.install_shunying_clone import _make_pinned_image, sha, DLL_NAME
from tools.strike_lab.current_skill_identity import decode_definitions
from tools.strike_lab.omega_assets import decode_csvz

ROOT = Path(__file__).resolve().parents[2]
CLIENT = ROOT.parent / 'God2'
OUTPUT = ROOT / 'artifacts/releases/shunying-production-20260930/client'
CANDIDATE = ROOT / 'artifacts/custom-skills/shunying/client-candidate'
DLL_SOURCE = ROOT / 'artifacts/playtests/private-shunying-manual-20260930-01/client' / DLL_NAME
EXE_SHA256 = '9be38ef858bc9c63b6f296cae4a8e601ddcfaf614700e725c4bec44065b53336'
DLL_SHA256 = '8d1ec1c4d31af24fe3ff99f8bc452c714f73b327933049d677d891ea61d4a823'
RESOURCE_PINS = {
    data.CATALOG: ('7676acd93f164d071f7681a3fe74de94d65892759dbf2e69e3c0f748423d2f51', '3adcda70a477086da50411fe5d023eec33f915efafd17ec478d55542cae42ea7'),
    data.ICONS: ('50844735316f6989efc2c56a261ddb830b0815cee9f975745f6a3a0b4c61f6ea', '5176a1de20743aa5e3081426b93a84e5a78cfbce1d726b72157e2ff345d9e9ea'),
    data.ROUTES: ('1c68e9e79028dc79f2110e0749bb5bdbe1f6f0cafaa6583006a397192ec1104f', 'dc9ca71bb621f328c3ef1bc7d039dcd1541e05480ab7fe35a8b63e4b209b6cb9'),
    data.DISPLAY_ITEMS: ('70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731', 'ef297a84e828537c4a18c5cf0be3d1c15bc26d5d2f25850ce9f2f030bdb58fa2'),
    data.DISPLAY_ITEMS_GB: ('66c296fa27ebfbaa9434cb3e3707e23b79828b37ce7a0129d439b393ff00a7ff', '68e6017a2319e35af596c23b674ef2cd163296e8ea8ad29acf4e592c0dff9cd8'),
    'Data2/Fight/Spg/spg9006.ROMZ': ('a5a93b93f0e67e57aad426236287575312d31bcaec52c8b7ac60619492c7d411',) * 2,
    'Data2/Fight/Spg/spg9008.rtb': ('ed4b7690d0f9c30d52e6e32ae9c011835c7d2267e3f6406a14683449eca4446a',) * 2,
}
# Exact prologues installed by the accepted DLL (clone_hooks.cpp, 15 hooks).
# Keep this release contract independent of future edits to that source.
HOOKS = (
    (0x12c520, '8b44240c83ec08'), (0x129020, '83ec0c8b442414'),
    (0x11fc40, '83ec10538bd9'), (0x27400, '51535657894c240c'),
    (0x116ae0, '81ec34010000'), (0x1154e0, '515355568bf1'),
    (0x113080, '83ec2055568bf1'), (0x118e50, '83ec10538a5c2418'),
    (0x26ab0, '538b5c2408'), (0x1c360, '83ec185355'),
    (0x1b9c0, '515355568b742414'), (0x1b330, '538bd95556'),
    (0x327a0, '568bf16a00'), (0x32810, '53568bf157'),
    (0x13dd40, '81ec04010000'),
)


def require(condition: bool, message: str):
    if not condition:
        raise ValueError(message)


def verify_hooks(raw: bytes) -> list[dict]:
    pe = pefile.PE(data=raw)
    report = []
    for rva, expected in HOOKS:
        actual = pe.get_data(rva, len(bytes.fromhex(expected)))
        require(actual.hex() == expected, f'Hook signature mismatch at RVA {rva:#x}')
        report.append(dict(rva=hex(rva), bytes=expected))
    return report


def verify_preservation(original: bytes, patched: bytes, details: dict) -> dict:
    before, after = pefile.PE(data=original), pefile.PE(data=patched)
    require(len(after.sections) == len(before.sections) + 1, 'Unexpected section count')
    for old, new in zip(before.sections, after.sections):
        require(old.__pack__() == new.__pack__(), 'Original section header changed')
        require(old.get_data() == new.get_data(), 'Original section content changed')
    def imports(pe):
        return [(entry.dll, [(imp.name, imp.ordinal, imp.address) for imp in entry.imports])
                for entry in pe.DIRECTORY_ENTRY_IMPORT]
    require(imports(before) == imports(after), 'Imports changed')
    require([d.__pack__() for d in before.OPTIONAL_HEADER.DATA_DIRECTORY] ==
            [d.__pack__() for d in after.OPTIONAL_HEADER.DATA_DIRECTORY], 'Data directories changed')
    code = bytes.fromhex(details['bootstrap_code_hex'])
    entry = after.OPTIONAL_HEADER.AddressOfEntryPoint
    require(after.get_data(entry, len(code)) == code, 'Bootstrap code mismatch')
    require(code[:2] == b'\x9c\x60' and code[-7:-5] == b'\x61\x9d' and code[-5] == 0xe9,
            'Bootstrap register/flags preservation mismatch')
    target = entry + len(code) + struct.unpack('<i', code[-4:])[0]
    require(target == before.OPTIONAL_HEADER.AddressOfEntryPoint, 'Entry chain was replaced')
    allowed = details['modified_original_byte_ranges']
    require(all(a == b or any(lo <= i < hi for lo, hi in allowed)
                for i, (a, b) in enumerate(zip(original, patched))), 'Unreviewed original byte changed')
    require(after.OPTIONAL_HEADER.CheckSum == after.generate_checksum(), 'PE checksum invalid')
    verify_hooks(patched)
    return dict(original_sections=len(before.sections), sections_byte_identical=True,
                original_data_directories_and_imports_identical=True,
                registers_flags_restored=True, original_entry_chain_preserved=True,
                original_oep_rva=hex(target), original_port=struct.unpack('<I', before.get_data(0x11ee9, 4))[0],
                all_15_hook_signatures_match=True)


def collect_resources() -> tuple[dict, dict]:
    sources, payloads = {}, {}
    for relative, (source_pin, candidate_pin) in RESOURCE_PINS.items():
        sources[relative] = (CLIENT / relative).read_bytes()
        payloads[relative] = (CANDIDATE / relative).read_bytes()
        require(sha(sources[relative]) == source_pin, f'Formal resource changed; merge/review required: {relative}')
        require(sha(payloads[relative]) == candidate_pin, f'Candidate resource changed: {relative}')
    native = decode_definitions(sources[data.CATALOG])
    combined = decode_definitions(payloads[data.CATALOG])
    require(len(native) == 448 and len(combined) == 453, 'Unexpected catalog record count')
    require(all(combined[key] == value for key, value in native.items()), 'Native skill record changed')
    require(data.make_catalog(sources[data.CATALOG])[0] == payloads[data.CATALOG], 'Skill addition differs')
    require(data.make_routes(sources[data.ROUTES])[0] == payloads[data.ROUTES], 'Route addition differs')
    for relative, simplified in ((data.DISPLAY_ITEMS, False), (data.DISPLAY_ITEMS_GB, True)):
        require(data.make_display_items(sources[relative], simplified=simplified)[0] == payloads[relative],
                'Display metadata addition differs')
    original_chunks = list(data.chunks(decode_csvz(sources[data.ICONS])))
    final_chunks = list(data.chunks(decode_csvz(payloads[data.ICONS])))
    insertion = next(i for i, (tag, _, _) in enumerate(original_chunks) if tag == b'ACT_DATA')
    restored = final_chunks[:insertion] + final_chunks[insertion + 1:len(original_chunks)] + [final_chunks[-1]]
    require([part[2] for part in restored] == [part[2] for part in original_chunks], 'Native icon chunks changed')
    data.render_native_icon(payloads[data.ICONS])
    return payloads, dict(source_sha256={k: sha(v) for k, v in sources.items()},
        output_sha256={k: sha(v) for k, v in payloads.items()}, native_records_preserved=448,
        native_icon_chunks_preserved=len(original_chunks), native_blade3_resources_identical=True,
        existing_route_and_display_bytes_preserved=True)


def prepare() -> tuple[dict, dict]:
    raw = (CLIENT / 'God2.exe').read_bytes()
    require(sha(raw) == EXE_SHA256, 'Formal executable changed; review a new release pin')
    dll = DLL_SOURCE.read_bytes()
    require(sha(dll) == DLL_SHA256, 'Accepted DLL changed; review a new release pin')
    dll_pe = pefile.PE(data=dll)
    require(dll_pe.FILE_HEADER.Machine == 0x14c and dll_pe.OPTIONAL_HEADER.Magic == 0x10b
            and bool(dll_pe.FILE_HEADER.Characteristics & 0x2000), 'Expected x86 DLL')
    hooks = verify_hooks(raw)
    patched, bootstrap = _make_pinned_image(raw, CLIENT / DLL_NAME, expected_sha256=EXE_SHA256)
    preservation = verify_preservation(raw, patched, bootstrap)
    payloads, resources = collect_resources()
    payloads.update({'God2.exe': patched, DLL_NAME: dll})
    report = dict(custom_design_id='CUSTOM-0058', status='STAGED_STATIC_VERIFIED_AWAITING_FORMAL_LAUNCH',
        installed=False, destination=str(CLIENT), source_exe_sha256=EXE_SHA256,
        accepted_dll_source=str(DLL_SOURCE), dll_sha256=DLL_SHA256,
        bootstrap=bootstrap, preservation=preservation, hooks=hooks, resources=resources,
        output_sha256={k: sha(v) for k, v in payloads.items()},
        relocation='Bootstrap uses the exact local formal DLL path; rebuild for a different installation directory.',
        launcher='Native Support verifies existing layout and launches the current God2.exe; no launcher rebuild required. '
                 'Any hash-named runtime copy must be refreshed from this new EXE before launch.')
    return payloads, report


def main():
    payloads, report = prepare()
    handoff = OUTPUT.parent / 'client-release.json'
    require(not handoff.exists(), 'Release handoff already exists')
    sources = dict(report['resources']['source_sha256'], **{'God2.exe': EXE_SHA256})
    existing_dll = CLIENT / DLL_NAME
    sources[DLL_NAME] = sha(existing_dll.read_bytes()) if existing_dll.exists() else None
    # A unique, exclusive staging directory prevents accidental live writes or
    # overwrites of an operator's previous package. All validation precedes it.
    OUTPUT.mkdir(parents=True, exist_ok=False)
    for relative, raw in payloads.items():
        target = OUTPUT / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('xb') as stream:
            stream.write(raw)
        require(sha(target.read_bytes()) == report['output_sha256'][relative], 'Staged readback failed')
    require(sha((CLIENT / 'God2.exe').read_bytes()) == EXE_SHA256, 'Source changed during staging')
    for relative, (pin, _) in RESOURCE_PINS.items():
        require(sha((CLIENT / relative).read_bytes()) == pin, 'Source data changed during staging')
    with (OUTPUT / 'manifest.json').open('x', encoding='utf-8') as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
    with handoff.open('x', encoding='utf-8') as stream:
        json.dump(dict(candidate_folder=str(OUTPUT), target_folder=str(CLIENT),
            files=[dict(path=relative, source_sha256=sources[relative], sha256=sha(raw))
                   for relative, raw in payloads.items()]), stream, indent=2)
    print(json.dumps(dict(output=str(OUTPUT), sha256=report['output_sha256'],
                          preservation=report['preservation']), indent=2))


if __name__ == '__main__':
    main()
