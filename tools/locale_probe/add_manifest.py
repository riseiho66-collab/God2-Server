"""Add a manifest without repacking an ASPack executable's existing sections.

Research utility; it builds a new resource directory and leaves resource data at
their original RVAs. It never modifies the input file.
"""

import argparse
import pathlib
import struct

import pefile


def align(value, unit):
    return (value + unit - 1) // unit * unit


def make_directory(pe, manifest, resource_rva):
    root = []
    if hasattr(pe, "DIRECTORY_ENTRY_RESOURCE"):
        for kind in pe.DIRECTORY_ENTRY_RESOURCE.entries:
            names = []
            for name in kind.directory.entries:
                langs = []
                for lang in name.directory.entries:
                    d = lang.data.struct
                    langs.append((lang.id, (d.OffsetToData, d.Size, d.CodePage, d.Reserved)))
                names.append((str(name.name) if name.name else name.id, langs))
            root.append((str(kind.name) if kind.name else kind.id, names))
    root.append((24, [(1, [(1033, (resource_rva, len(manifest), 0, 0))])]))
    # Root entries are sorted by named entries first, then numeric IDs.
    blob = bytearray()
    manifest_offset = None

    def reserve(n):
        off = len(blob)
        blob.extend(b"\0" * n)
        return off

    def build(entries, depth=0):
        ordered = sorted(entries, key=lambda item: (0, item[0]) if isinstance(item[0], str) else (1, item[0]))
        off = reserve(16 + len(ordered) * 8)
        named = sum(isinstance(key, str) for key, _ in ordered)
        struct.pack_into("<IIHHHH", blob, off, 0, 0, 0, 0, named, len(ordered) - named)
        for i, (key, child) in enumerate(ordered):
            if isinstance(key, str):
                encoded = key.encode("utf-16le")
                name_off = reserve(2 + len(encoded))
                struct.pack_into("<H", blob, name_off, len(key))
                blob[name_off + 2:name_off + 2 + len(encoded)] = encoded
                name_field = 0x80000000 | name_off
            else:
                name_field = key
            if depth < 2:
                child_field = 0x80000000 | build(child, depth + 1)
            else:
                data_off = reserve(16)
                struct.pack_into("<IIII", blob, data_off, *child)
                child_field = data_off
                if key == 1033 and child[0] == resource_rva:
                    nonlocal manifest_offset
                    manifest_offset = data_off
            struct.pack_into("<II", blob, off + 16 + i * 8, name_field, child_field)
        return off

    build(root)
    padding = align(len(blob), 4) - len(blob)
    blob.extend(b"\0" * padding)
    manifest_data_offset = len(blob)
    blob.extend(manifest)
    if manifest_offset is None:
        raise ValueError("Manifest data entry missing")
    struct.pack_into("<I", blob, manifest_offset, resource_rva + manifest_data_offset)
    return blob


def add_manifest(source, manifest):
    pe = pefile.PE(data=source)
    if pe.OPTIONAL_HEADER.Magic != 0x10B:
        raise ValueError("Only PE32 is supported")
    section_align = pe.OPTIONAL_HEADER.SectionAlignment
    file_align = pe.OPTIONAL_HEADER.FileAlignment
    last = pe.sections[-1]
    new_rva = align(last.VirtualAddress + max(last.Misc_VirtualSize, last.SizeOfRawData), section_align)
    raw = align(len(source), file_align)
    blob = make_directory(pe, manifest, new_rva)
    raw_size = align(len(blob), file_align)
    section_table = pe.DOS_HEADER.e_lfanew + 24 + pe.FILE_HEADER.SizeOfOptionalHeader
    header = section_table + pe.FILE_HEADER.NumberOfSections * 40
    if header + 40 > pe.OPTIONAL_HEADER.SizeOfHeaders or any(source[header:header + 40]):
        raise ValueError("No spare section header")
    output = bytearray(source)
    output.extend(b"\0" * (raw + raw_size - len(output)))
    output[raw:raw + len(blob)] = blob
    struct.pack_into("<8sIIIIIIHHI", output, header, b".langrs\0", len(blob), new_rva,
                     raw_size, raw, 0, 0, 0, 0, 0x40000040)
    struct.pack_into("<H", output, pe.DOS_HEADER.e_lfanew + 6, pe.FILE_HEADER.NumberOfSections + 1)
    struct.pack_into("<I", output, pe.OPTIONAL_HEADER.get_file_offset() + 56,
                     align(new_rva + len(blob), section_align))
    struct.pack_into("<I", output, pe.OPTIONAL_HEADER.get_file_offset() + 64, 0)
    directory = pe.OPTIONAL_HEADER.DATA_DIRECTORY[2].get_file_offset()
    struct.pack_into("<II", output, directory, new_rva, len(blob))
    return bytes(output)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("source", type=pathlib.Path)
    p.add_argument("manifest", type=pathlib.Path)
    p.add_argument("output", type=pathlib.Path)
    args = p.parse_args()
    args.output.write_bytes(add_manifest(args.source.read_bytes(), args.manifest.read_bytes()))
