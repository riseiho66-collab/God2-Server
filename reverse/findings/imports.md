# On-Disk Import Inventory

Source: PE-001, original packed God2.exe. PowerShell walked the import descriptors at RVA 0x00302FAC (directory size 884), using OriginalFirstThunk when available and FirstThunk otherwise. Names were read as ASCII; ordinal entries are retained without speculative export-name resolution.

| DLL | FirstThunk RVA | Visible symbols |
| --- | --- | --- |
| kernel32.dll | 0x00302F5C | GetProcAddress, GetModuleHandleA, LoadLibraryA |
| ws2_32.dll | 0x003031CD | ordinal 12 |
| ddraw.dll | 0x003031D5 | DirectDrawCreate |
| dsound.dll | 0x003031DD | ordinal 1 |
| winmm.dll | 0x003031E5 | mmioOpenA |
| imm32.dll | 0x003031ED | ImmGetIMEFileNameA |
| crashrpt.dll | 0x003031F5 | CrashRptAddFile |
| user32.dll | 0x003031FD | CreateWindowExA |
| gdi32.dll | 0x00303205 | ArcTo |
| comdlg32.dll | 0x0030320D | GetFileTitleA |
| winspool.drv | 0x00303215 | DocumentPropertiesA |
| advapi32.dll | 0x0030321D | RegSetValueExA |
| shell32.dll | 0x00303225 | DragAcceptFiles |
| comctl32.dll | 0x0030322D | ordinal 17 |
| olepro32.dll | 0x00303235 | ordinal 251 |
| ole32.dll | 0x0030323D | CreateStreamOnHGlobal |
| wininet.dll | 0x00303245 | InternetOpenA |

17 descriptors and 19 visible imported symbols were enumerated. The IAT data-directory entry itself is zero; descriptor thunk locations are still present. No named connect/send/recv/WSARecv/WSASend entry was observed in this on-disk inventory. This does not establish their absence at runtime: GetProcAddress/LoadLibraryA and packing can hide the eventual import set.

## Recovery Record Required

For each restored thunk record original/dump/repaired hashes, thunk RVA, runtime pointer, owning loaded module/version, export name or ordinal, resolver evidence and unresolved reason. Check whether imports are forwarding to other modules. Distinguish original program imports from unpacker imports.

No IAT reconstruction was performed. The above is a packed-file inventory, not a repaired import table or network xref list.
