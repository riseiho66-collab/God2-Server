"""CUSTOM-0058: append a loader to one pinned ISOLATED God2 trial executable.

No remote process injection, import replacement, source overwrite, or formal
client modification. Existing IME/chat sections and every import remain intact.
A new executable, exclusive source backup, adjacent DLL and manifest are created.
The DLL path is absolute, so this disposable test installation is not relocatable.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct

import pefile

ROOT = Path(__file__).resolve().parents[2]
TRIALS = ROOT / 'artifacts/playtests'
INPUT_SHA256 = '9ff8b9c99271e2e528270ce6475f231c338a09daf463c300fe39b62f66258c4f'
DLL_NAME = 'God2ShunyingClone.dll'
SECTION_NAME = b'.syclone'
MARKER = b'GOD2_SHUNYING_BOOTSTRAP_V1\0'


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def aligned(value: int, alignment: int) -> int:
    if alignment <= 0 or alignment & (alignment - 1):
        raise ValueError('PE alignment must be a positive power of two')
    return (value + alignment - 1) & -alignment


def validated_trial(source: Path, output: Path) -> tuple[Path, Path]:
    source, output = source.resolve(strict=True), output.resolve(strict=False)
    trial = source.parent.parent
    if (source.name != 'God2-shunying-manual.exe' or source.parent.name != 'client'
            or trial.parent != TRIALS.resolve() or not trial.name.startswith('private-shunying-manual-')
            or output.parent != source.parent or output == source
            or output.suffix.lower() != '.exe' or output.exists()):
        raise ValueError('Only a new EXE beside a private-shunying-manual-* isolated client is allowed')
    return source, output


def make_patched_image(raw: bytes, absolute_dll: Path) -> tuple[bytes, dict]:
    if sha(raw) != INPUT_SHA256:
        raise ValueError('Input EXE is not the exact pinned unmodified trial; already-patched input is refused')
    return _make_pinned_image(raw, absolute_dll, expected_sha256=INPUT_SHA256)


def _make_pinned_image(raw: bytes, absolute_dll: Path, *, expected_sha256: str) -> tuple[bytes, dict]:
    """Shared append-only primitive; callers must own a concrete release pin.

    The public trial API and CLI retain their original identity/path checks.
    This primitive writes no files and never accepts an unpinned image.
    """
    if len(expected_sha256) != 64 or sha(raw) != expected_sha256:
        raise ValueError('Input EXE does not match the caller-owned exact version pin')
    if MARKER in raw:
        raise ValueError('Bootstrap already present')
    pe = pefile.PE(data=raw, fast_load=False)
    if pe.FILE_HEADER.Machine != 0x14c or pe.OPTIONAL_HEADER.Magic != 0x10b:
        raise ValueError('Only x86 PE32 is supported')
    if pe.FILE_HEADER.Characteristics & 0x2000:
        raise ValueError('Source must be an EXE, not DLL')
    if pe.get_overlay_data_start_offset() is not None:
        raise ValueError('Overlay must be preserved by a separately reviewed installer')
    security = pe.OPTIONAL_HEADER.DATA_DIRECTORY[4]
    if security.VirtualAddress or security.Size:
        raise ValueError('Refusing signed image modification')
    if any(section.Name.rstrip(b'\0') == SECTION_NAME for section in pe.sections):
        raise ValueError('Bootstrap section already exists')
    imports = [imp.address - pe.OPTIONAL_HEADER.ImageBase
               for entry in getattr(pe, 'DIRECTORY_ENTRY_IMPORT', [])
               if entry.dll.lower() == b'kernel32.dll'
               for imp in entry.imports if imp.name == b'LoadLibraryA']
    if len(imports) != 1:
        raise ValueError('Exactly one existing kernel32.LoadLibraryA IAT entry is required; no guessed address')
    iat_rva = imports[0]
    pe.get_offset_from_rva(iat_rva)  # must be backed by a real imported slot
    old_oep = pe.OPTIONAL_HEADER.AddressOfEntryPoint
    if pe.get_offset_from_rva(old_oep) >= len(raw):
        raise ValueError('Original entry point is outside file-backed image')
    header_offset = pe.sections[-1].get_file_offset() + 40
    first_raw = min(section.PointerToRawData for section in pe.sections if section.SizeOfRawData)
    if (header_offset + 40 > min(first_raw, pe.OPTIONAL_HEADER.SizeOfHeaders)
            or any(raw[header_offset:header_offset + 40])):
        raise ValueError('No zero-filled existing section-header slot; will not move original headers')
    section_rva = aligned(max(s.VirtualAddress + max(s.Misc_VirtualSize, s.SizeOfRawData)
                              for s in pe.sections), pe.OPTIONAL_HEADER.SectionAlignment)
    raw_offset = aligned(len(raw), pe.OPTIONAL_HEADER.FileAlignment)
    dll_path = str(absolute_dll.resolve()).encode('ascii')
    if not absolute_dll.is_absolute() or absolute_dll.name != DLL_NAME or b'\0' in dll_path:
        raise ValueError('Absolute local ASCII God2ShunyingClone.dll path required')
    # pushfd; pushad; call next; pop ebx; sub ebx, return-RVA => actual image base.
    # EBX survives stdcall; after LoadLibraryA all original GPRs/EFLAGS/ESP are
    # restored and a relative jump reaches the untouched original entry point.
    prefix = b'\x9c\x60\xe8\0\0\0\0\x5b\x81\xeb' + struct.pack('<I', section_rva + 7)
    string_rva = section_rva + len(prefix) + 6 + 1 + 6 + 1 + 1 + 5
    code = prefix + b'\x8d\x83' + struct.pack('<I', string_rva) + b'\x50'
    code += b'\xff\x93' + struct.pack('<I', iat_rva) + b'\x61\x9d'
    jump_next = section_rva + len(code) + 5
    code += b'\xe9' + struct.pack('<i', old_oep - jump_next)
    if section_rva + len(code) != string_rva:
        raise AssertionError('Bootstrap string displacement mismatch')
    payload = code + dll_path + b'\0' + MARKER
    raw_size = aligned(len(payload), pe.OPTIONAL_HEADER.FileAlignment)
    updated = bytearray(raw + bytes(raw_offset - len(raw)) + payload.ljust(raw_size, b'\0'))
    section_header = struct.pack('<8sIIIIIIHHI', SECTION_NAME.ljust(8, b'\0'), len(payload),
        section_rva, raw_size, raw_offset, 0, 0, 0, 0, 0x60000020)  # RX, code
    updated[header_offset:header_offset + 40] = section_header
    changed_ranges = [(header_offset, header_offset + 40)]
    def field(record, name, value, fmt='<I'):
        at = record.get_field_absolute_offset(name)
        struct.pack_into(fmt, updated, at, value)
        changed_ranges.append((at, at + struct.calcsize(fmt)))
    field(pe.FILE_HEADER, 'NumberOfSections', pe.FILE_HEADER.NumberOfSections + 1, '<H')
    field(pe.OPTIONAL_HEADER, 'AddressOfEntryPoint', section_rva)
    field(pe.OPTIONAL_HEADER, 'SizeOfImage', aligned(section_rva + len(payload), pe.OPTIONAL_HEADER.SectionAlignment))
    field(pe.OPTIONAL_HEADER, 'SizeOfCode', pe.OPTIONAL_HEADER.SizeOfCode + raw_size)
    field(pe.OPTIONAL_HEADER, 'CheckSum', 0)
    check = pefile.PE(data=bytes(updated))
    field(pe.OPTIONAL_HEADER, 'CheckSum', check.generate_checksum())
    for index, original in enumerate(raw):
        if updated[index] != original and not any(a <= index < b for a, b in changed_ranges):
            raise AssertionError('Original image data outside reviewed header fields changed')
    result = bytes(updated)
    check = pefile.PE(data=result)
    if check.OPTIONAL_HEADER.CheckSum != check.generate_checksum():
        raise AssertionError('Output PE checksum mismatch')
    return result, dict(source_sha256=sha(raw), output_sha256=sha(result),
        original_oep_rva=hex(old_oep), bootstrap_rva=hex(section_rva),
        existing_loadlibrarya_iat_rva=hex(iat_rva), new_section=SECTION_NAME.decode(),
        bootstrap_code_hex=code.hex(), dll_absolute_path=str(absolute_dll.resolve()),
        modified_original_byte_ranges=changed_ranges,
        existing_imports_and_sections_preserved=True, source_overwritten=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--dll', type=Path, required=True)
    parser.add_argument('--check-only', action='store_true')
    args = parser.parse_args()
    source, output = validated_trial(args.source, args.output)
    dll_source = args.dll.resolve(strict=True)
    dll_bytes = dll_source.read_bytes()
    dll_pe = pefile.PE(data=dll_bytes)
    if (dll_source.name != DLL_NAME or dll_pe.FILE_HEADER.Machine != 0x14c
            or dll_pe.OPTIONAL_HEADER.Magic != 0x10b or not dll_pe.FILE_HEADER.Characteristics & 0x2000):
        raise ValueError('Built x86 God2ShunyingClone.dll required')
    dll_target = output.parent / DLL_NAME
    backup = source.with_name(source.stem + '.pre-shunying-clone.exe')
    manifest = output.with_suffix('.bootstrap.json')
    for destination in (output, dll_target, backup, manifest):
        if destination.exists():
            raise FileExistsError(f'Refusing overwrite: {destination}')
    raw = source.read_bytes()
    patched, details = make_patched_image(raw, dll_target)
    details.update(source=str(source), output=str(output), backup=str(backup),
        dll_source=str(dll_source), dll_sha256=sha(dll_bytes),
        check_only=args.check_only, status='STATIC_VALIDATED_NOT_GAMEPLAY_ACCEPTANCE')
    if not args.check_only:
        # Exclusive creates avoid overwriting a concurrent operator's artifacts.
        # Preserve partial outputs for inspection if a later write fails.
        for destination, data in ((backup, raw), (dll_target, dll_bytes), (output, patched)):
            with destination.open('xb') as stream:
                stream.write(data)
        if source.read_bytes() != raw or backup.read_bytes() != raw:
            raise RuntimeError('Source or exclusive backup verification failed')
        with manifest.open('x', encoding='utf-8') as stream:
            json.dump(details, stream, ensure_ascii=False, indent=2)
    print(json.dumps(details, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
