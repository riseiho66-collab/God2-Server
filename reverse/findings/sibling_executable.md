# Sibling Executable Comparison

Evidence **PE-002**, inspected read-only on 2026-09-18 using PowerShell byte parsing and SHA256. No sibling file was executed, copied over the client, or modified. This artifact is distinct from PE-001 and must not inherit its candidate symbols or protocol assumptions.

| Property | Launcher-src/God2.exe (PE-002) | God2/God2.exe (PE-001) |
| --- | --- | --- |
| Size | 608256 bytes | 679936 bytes |
| SHA256 | 831B206C03FA425B0BCB63984EB078DE0433A03108E4BDE91E9AF90D787CD569 | FB72296CAB5950B74D8F7C98155145F7C5F58749C3011ADB0540325B60749DD1 |
| PE header offset | 0x118 | 0x108 |
| Machine / optional magic | 0x014C / 0x010B | 0x014C / 0x010B |
| Preferred base | 0x00400000 | 0x00400000 |
| Entry RVA / preferred VA | 0x0021A001 / 0x0061A001 | 0x00302001 / 0x00702001 |
| Entry file offset | 0x91201 | 0xA2C01 |
| Section count | 7 | 6 |
| SizeOfImage | 2228224 | 3174400 |
| SizeOfHeaders | 1536 | 1536 |
| Subsystem | 2 (GUI) | 2 (GUI) |
| COFF timestamp (untrusted) | 1149124663 | 1484128236 |
| Import directory RVA / size | 0x0021AFAC / 916 | 0x00302FAC / 884 |
| IAT data directory | 0 / 0 | 0 / 0 |

## PE-002 Sections

Numeric sizes and offsets below are decimal. The first six section flags are 0xC0000040; .w10fix flags are 0x60000020.

| Section | RVA | Virtual size | Raw offset | Raw size |
| --- | ---: | ---: | ---: | ---: |
| .text | 4096 | 1286144 | 1536 | 527360 |
| .rdata | 1290240 | 73728 | 528896 | 22528 |
| .data | 1363968 | 802816 | 551424 | 35840 |
| .rsrc | 2166784 | 36864 | 587264 | 7168 |
| .aspack | 2203648 | 16384 | 594432 | 13312 |
| .adata | 2220032 | 4096 | 607744 | 0 |
| .w10fix | 2224128 | 47 | 607744 | 512 |

Entry bytes at 0x91201:

~~~text
60 E8 03 00 00 00 E9 EB 04 5D 45 55 C3 E8 01 00
00 00 EB 5D BB ED FF FF FF 03 DD 81 EB 00 A0 21
~~~

## PE-002 Visible Imports

| DLL | FirstThunk RVA | Symbols |
| --- | --- | --- |
| kernel32.dll | 0x0021AF5C | GetProcAddress, GetModuleHandleA, LoadLibraryA |
| ws2_32.dll | 0x0021B1CD | ordinal 12 |
| ddraw.dll | 0x0021B1D5 | DirectDrawCreateEx |
| dsound.dll | 0x0021B1DD | ordinal 1 |
| winmm.dll | 0x0021B1E5 | mmioDescend |
| imm32.dll | 0x0021B1ED | ImmGetIMEFileNameA |
| crashrpt.dll | 0x0021B1F5 | CrashRptAddFile |
| user32.dll | 0x0021B1FD | RegisterClassA |
| gdi32.dll | 0x0021B205 | SetArcDirection |
| comdlg32.dll | 0x0021B20D | GetFileTitleA |
| winspool.drv | 0x0021B215 | ClosePrinter |
| advapi32.dll | 0x0021B21D | RegOpenKeyExA |
| shell32.dll | 0x0021B225 | DragAcceptFiles |
| comctl32.dll | 0x0021B22D | _TrackMouseEvent |
| wininet.dll | 0x0021B235 | GopherFindFirstFileA |
| olepro32.dll | 0x0021B23D | ordinal 251 |
| ole32.dll | 0x0021B245 | CreateStreamOnHGlobal |

Like PE-001, this has 17 descriptors and 19 imported symbols, with no named connect/send/recv/WSARecv/WSASend entries. Ordinals remain unresolved. Import presence does not prove API use or network packet semantics.

## Conclusion And Limits

This is not evidence of an already-unpacked client. Both entries lie in .aspack, both retain .adata, both have large virtual/raw size gaps and sparse imports, and their entry byte sequences have similar structure. These observations support a packed-image hypothesis without proving packer version or runtime behavior. The smaller file does not expose additional named game-network APIs.

.w10fix is an observed extra section name and layout, not proof of its author, function, correctness or unpack status. No disassembly or provenance chain for that section was recovered. Different hashes/layouts/import names require separate analysis; the relationship between builds remains unverified. God2-run variants were not substituted for either artifact.

OEP candidate 0x0054A3E8 belongs only to the PE-001 hypothesis. Do not transfer it to PE-002 by filename or image base. Dynamic unpacking, IAT reconstruction and real protocol extraction remain pending for both.
