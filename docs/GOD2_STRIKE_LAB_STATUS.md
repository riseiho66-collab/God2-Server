# STRIKE LAB Results - 2026-09-19

## Actual Progress

Four Release x64 artifacts built in `build-strike-lab/Release`: native launcher,
snapshot-diff and loopback frontends plus a read-only debugger-host probe DLL.
The EXEs use the local Python research backend; the probe is not an injected
API-hook DLL. See `tools/strike_lab/README.md` for coverage and limitations.

Final comparable captures:

- `artifacts/probe-runs/lab-direct-final-01`
- `artifacts/probe-runs/lab-equivalent-final-01`
- `artifacts/probe-runs/direct-vs-equivalent-final-01.json`

Both profiles pass argument parsing and stop naturally on the same failure
route at 0x45B7A4, before the known null-format crash. Both observe exactly two
string-table writes, zero final count/pointer, no table-loader/initializer
entry, and no monitored Winsock entry. Summary/module/file/resource results
are equal. Contexts, PID/TID, timestamps and addresses of OS allocations can
differ; equality of summary does not imply complete behavioral equivalence.

The equivalent profile adds known private-launcher env/config context only.
No evidence yet establishes equivalence to the historical official launcher.
Temporary working-copy configs were restored after each run. No remote IP,
test credential, packet response, semantic client patch or policy change was
used. No listener was opened. No subagents were started.

## String Table

Object base 0x5E053C is corroborated at writer EDX and failure EBP.
Count is a WORD at +0xB2C64; pointer is a DWORD at +0xB2C60.

Observed writes:

- Instruction 0x455998 writes count=0; hardware trap PC is 0x45599F.
- Instruction 0x45599F writes pointer=0; hardware trap PC is 0x4559A5.

Both old and new values are zero. No nonzero value or later clear was seen.
This refutes NEVER_WRITTEN for this monitored interval and does not support
WRITTEN_THEN_CLEARED. Disassembly preceding a hardware trap is retained; only
the adjacent field-store instruction is used, not unreliable earlier backward
disassembly or unwound frames.

Narrow static field-xref analysis identifies loader 0x458FF0. Dispatch call
0x456682 selects it after matching header `SystemMessage` at 0x58A070.
The function allocates a 16-byte-per-entry table, stores its pointer at
0x459012, and updates count at 0x459112. The input-file loader is 0x456130.
Actual source filename and successful load remain UNKNOWN.

Final runs arm and retain an inventory of breakpoints for these entries,
dispatch and initializer return. None is hit before the existing validation
failure. Classification: INITIALIZER_NOT_CALLED **within the restored-candidate
to failure window**. A missing resource file has not been demonstrated.

## Compatibility And Network

Report directory: `artifacts/reports/strike-lab-final-20260919`.

`api-compat-checks.json` contains two adjacent load/byte-compare/branch static
candidates, at 0x45B662 and 0x45B893, both using slot 0x5707BC. Only the first
is runtime observed here: expected 0x83, actual export begins FF 25, JE not
taken. Purpose and a supported remedy remain unverified. Do not patch it.

`cross-build-check.json` compares only the relevant on-disk region of God2.exe
and God2-run.exe. Both remain packed; equal packed region bytes do not certify
equal restored checks or failure behavior. God2-run.exe was not launched.

`network-root-candidates.json` records sixteen static references to already
observed Winsock pointer candidates. These are not runtime network hits and
do not establish a destination, frame or opcode. 6001 remains an argument.

Hyper-V's Get-VM command exists but inventory was denied to the current account.
No compatible owner-controlled VM was verified or launched. No elevation or
policy change was attempted for this inventory.

## Preserved Attempts

`lab-direct-01`: extension path escaping failed. `lab-direct-02`: a pre-entry
API breakpoint interrupted the old entry-only driver. `lab-direct-03`: graphics
driver reads exhausted the 800-event budget. `lab-direct-04`: conditional
breakpoint display required an explicit event marker. All outputs remain.

`lab-direct-05`, `lab-equivalent-01`, and `lab-initializer-01` established the
first complete observation window. The final pair repeats this with source
hashes, effective-machine metadata, early API coverage and breakpoint inventory.
Earlier S0 extension PCs lacked machine typing and are not execution evidence.

## Remaining Work

Verification: Release build succeeded for all four targets. The full research
unittest suite passed 95 tests in 115.941 seconds, including six new lab tests.
The actual loopback EXE rejected non-connect evidence before creating its
output directory or binding a socket. Original and working-copy God2.exe both
retain SHA-256 `fb72296cab5950b74d8f7c98155145f7c5f58749c3011adb0540325b60749dd1`.
Temporary display/endpoint settings are absent again, and no God2/CDB/lab
listener processes remained at the final check. No server C++ gameplay build
or client network integration test was claimed by this research test result.

The first lab version does not yet offer arbitrary launch-context overrides,
fully correlated nested API returns, qualified last-error capture, asynchronous
Winsock buffers, or a complete historical launcher replica. Those limitations
are explicit, not passed milestones.

The next operational requirement is a supported, isolated compatibility test
environment or evidence of a natural startup prerequisite that changes B002.
Do not fabricate string-table entries or guess protocol responses to continue.
Full startup, Winsock, first TX, login and world remain unachieved. G03 remains
NEED_MORE_EVIDENCE; G04+ unverified. Prior G02 receipts are not reissued.
