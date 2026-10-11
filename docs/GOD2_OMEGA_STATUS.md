# OMEGA Results - 2026-09-19

## Answer To The Bottleneck

The original SystemMessage asset exists and passes the recovered offline
contract. The current failure is MISSING_CALL, not MISSING_RESOURCE or an
observed FORMAT_REJECTED. The client has not yet reached the table loader.

Exact source: `God2/Data2/Patch/Comm/message.csvZ`, SHA-256
`5cd34cce66feae96d947cd45e32984765ce625673c0fb19c73cb63d7d9178598`.
The existing working copy is byte-identical. No asset was manufactured,
replaced or moved. Decompressed length is 110622 bytes. SystemMessage is at
line 75, raw decompressed offset 4986 (4912 after Windows text-mode CRLF
normalization), with 1950 records and unique IDs 1..1950. CP950 decoding
succeeds; the loader itself handles byte strings, not a proven named encoding.

## Proven Startup Order

Final narrow run: `artifacts/probe-runs/omega-display-01`.

1. Call 0x40DBD0 enters subsystem/graphics initialization 0x4322C0.
2. Its cooperative-level call returns success at 0x53C262 (EAX=0).
3. Before the outer initializer returns, the same thread receives message 7.
4. The message handler takes 0x40E42C, then calls 0x45B630 at 0x40E462.
5. The same run observes timeGetTime bytes FF 25, JE not taken at 0x45B665,
   and execution continuing at 0x45B667 before reaching failure 0x45B7A4.
6. Neither outer continuation 0x40DBD5 nor tables call 0x40DBF3 is reached.

Message 7 is [WM_SETFOCUS](https://learn.microsoft.com/en-us/windows/win32/inputdev/wm-setfocus).
The check therefore blocks this observed reentrant focus path. It is not
merely an unrelated warning, nor a universally proved static dominator.
The earliest missing edge in the monitored predecessor chain is the return
from 0x4322C0 to 0x40DBD5. Earlier known null-format crash evidence explains
why this failure path cannot safely report its message with an empty table;
this run stops before that crash rather than reexecuting it.

The proposed order "strings before graphics" is not the observed program
order. Graphics work and focus callbacks occur before table enumeration.

## Recovered Source Contract

0x40DBDD selects `\Data2\Patch\`; 0x52F550 prefixes cached current directory.
0x455780 enumerates 22 file names with `%scomm\%s`, including `message.csv`.
The language selector chooses the `-gb` variant only when the two stored
language words equal 4 and 2. 0x402530 tries path plus `Z` first, then the
unsuffixed text file. The wrapper has magic 05 16, a little-endian decoded
length, one byte read without validation, and compressed payload at offset 7.

The recovered 0x401D20 algorithm uses a 4096-byte ring, initial cursor 0xFEE,
LSB-first flags and back-references of length low-nibble+3. 0x451BE0 splits
comma-delimited byte fields; this is not quoted CSV. Missing optional string
columns return empty through 0x451AE0 and are valid. The table has 16-byte
in-memory entries, not fixed-size on-disk records.

`tools/strike_lab/god2-systemmessage-validator.py` verifies the original asset
offline. This is not proof that the original runtime loader has executed.
Unknown archive formats and other sections are not declared reconstructed.

## Outputs

`artifacts/reports/omega-final-v2-20260919` contains:

- `systemmessage-dispatch-slice.json`: dataflow, return contract, complete
  local dispatch disassembly and NetworkX intraprocedural dominators.
- `systemmessage-source-candidates.json`: 22 paths and their two variants.
- `systemmessage-validation.json`: exact original/work hashes and validation.
- `initializer-gates.json`: required/observed conditions and missing edge.
- `resource-access-differential.json`: existing asset, absent loader attempt.
- `startup-success-graph.json`: observed versus unexecuted startup order.
- `winsock-ref-clusters.json`: 38 direct callers of the existing 16 thunks,
  with surrounding instructions and focused startup/connect/send/recv groups.

`artifacts/reports/omega-assets-focused-20260919` contains the raw scan and
file-hash manifest: 9273 files, 1212380731 bytes, 79 decoded CSV/CSVZ wrappers,
one decoded SystemMessage candidate and zero read/decode errors. All files
were searched raw for ASCII/UTF-16 tags. 7863 non-CSV wrappers were not decoded;
absence of SystemMessage inside those compressed payloads is NOT claimed.
The initial all-wrapper scan was stopped as noncritical work and preserved
as incomplete. The scan's original `decoded_offset` means normalized text
offset; the final v2 validation explicitly separates raw/text-mode offsets.

## Context Test And Limits

Use `--observer omega --profile PROFILE_STATICALLY_RECONSTRUCTED_STARTUP` on
the existing God2LabLauncher. No claim of official launcher equivalence.
The latest profile also temporarily applies the native launcher's documented
800x600 DirectDraw settings through a structured INI parser. This made no
change to the failure result. Original INI bytes were restored exactly.
Original binary resolution patching was not performed.

OMEGA arms only the relevant predecessor/loader/store/failure sites, the 16
existing network thunks and seven Winsock APIs. It does not arm the old broad
IO trace or hardware field watches. Prior full file/resource observations
support the differential; the new trace provides causal ordering. Store
observations remain absent, not synthesized.

`omega-focus-01` incorrectly labeled argument 0 as the message ID; it is HWND.
Raw arguments remain preserved. `omega-focus-02`, `omega-focus-03` and
`omega-display-01` correctly use argument 1. The latter two also directly
observe the compatibility branch. Earlier OMEGA summaries inherited a zero
write count despite unarmed hardware watches; the final run explicitly marks
that coverage as disabled/unknown instead.

Thirteen focused tests pass: seven lab/profile tests and six decoder/validator
tests. The previous full 95-test research suite was not rerun in this turn.
No new server protocol, packet, listener, login/world progress or gate
promotion is claimed. No subagents were used.

The next unresolved prerequisite is a supported natural execution context
that clears the proven focus/compatibility failure. Merely supplying another
string file is not justified. No client/system API patch, dummy table,
forced branch, security-policy change or guessed reply is permitted or used.
