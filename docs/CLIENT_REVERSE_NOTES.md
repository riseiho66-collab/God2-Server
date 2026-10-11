# Client Static Evidence

## Provenance

Inspection date: 2026-09-18 (Asia/Taipei). Input: C:/Users/risei/Desktop/God2/God2/God2.exe, not God2-run.exe or a launcher. Requirements came from the supplied pasted-text.txt attachment. Method: PowerShell File.ReadAllBytes, BitConverter little-endian PE parsing, ASCII import names, and Get-FileHash SHA256. No client execution or modification.

Evidence ID **PE-001** identifies this exact on-disk artifact and the header/import observations below.

| Property | Observed value |
| --- | --- |
| File size | 679936 bytes |
| SHA256 | FB72296CAB5950B74D8F7C98155145F7C5F58749C3011ADB0540325B60749DD1 |
| DOS signature | MZ |
| PE header file offset | 0x108 |
| PE signature | 0x00004550 |
| Machine | 0x014C (x86) |
| Optional header magic | 0x010B (PE32) |
| Sections | 6 |
| Preferred image base | 0x00400000 |
| AddressOfEntryPoint RVA | 0x00302001 |
| Preferred entry VA | 0x00702001 |
| Entry file offset | 0x000A2C01 |
| SizeOfImage | 3174400 bytes |
| SizeOfHeaders | 1536 bytes |
| Subsystem | 2 (Windows GUI) |
| COFF timestamp | 1484128236; 2017-01-11T09:50:36Z, untrusted metadata |
| Import directory | RVA 0x00302FAC, size 884 |
| IAT data directory | RVA 0, size 0 |

A zero IAT directory does not mean no imports: import descriptors contain FirstThunk pointers. Neither the timestamp nor section names establish compiler identity or an authentic release date.

## Sections

All six section characteristics were 0xC0000040 in this file. Sizes and offsets below are decimal to preserve exact parser output.

| Section | RVA | Virtual size | Raw offset | Raw size |
| --- | ---: | ---: | ---: | ---: |
| .text | 4096 | 1503232 | 1536 | 595968 |
| .rdata | 1507328 | 73728 | 597504 | 22528 |
| .data | 1581056 | 1536000 | 620032 | 39424 |
| .rsrc | 3117056 | 36864 | 659456 | 7168 |
| .aspack | 3153920 | 16384 | 666624 | 13312 |
| .adata | 3170304 | 4096 | 679936 | 0 |

Entry point is within .aspack. First 32 bytes at file offset 0xA2C01:

~~~text
60 E8 03 00 00 00 E9 EB 04 5D 45 55 C3 E8 01 00
00 00 EB 5D BB ED FF FF FF 03 DD 81 EB 00 20 30
~~~

The section names, entry location and sparse import table support the user's ASPack-family hypothesis. They do not prove a particular packer version, a successful unpack, or the program's original entry point.

## OEP Limitation

**REQ-001** is the user-supplied candidate VA 0x0054A3E8, RVA 0x0014A3E8 at the preferred base. It lies within .text's virtual extent but outside .text's raw-backed extent. Consequently, a direct RVA-to-file-offset lookup cannot inspect original instructions at that address in this packed file. Do not read bytes from another section by applying an unchecked offset formula. Confidence in this address being the OEP is **unverified**, regardless of the example confidence supplied in the request.

## What Is Not Established

No unpacked image, repaired IAT, runtime module base, instruction trace, send/recv caller, packet framing, opcode, payload, cipher, compression rule or session flow has been verified. No network capture exists in this deliverable. The visible ws2_32 import is ordinal 12, not a demonstrated SendPacket wrapper; it remains ordinal-labeled until resolved against identified module evidence.

See [imports](../reverse/findings/imports.md), [symbol map](SYMBOL_MAP.md), and [restore plan](EXE_RESTORE_PLAN.md). A second read-only inspection, PE-002, covers the distinct 608256-byte Launcher-src/God2.exe: [sibling comparison](../reverse/findings/sibling_executable.md). It also has an entry in .aspack and sparse imports, not evidence of a completed unpack. PE-001 symbols and candidate addresses must not be transferred to it.
