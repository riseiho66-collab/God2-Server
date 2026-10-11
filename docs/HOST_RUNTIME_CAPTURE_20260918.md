# First Real GOD2 Capture

## Result

Capture ID: `6e1ed0632ab7559cb8d21871f59a43ab75fb2157dda9b58fab4242dabccdfbde`.

G02 consistency assessment: **READY_FOR_REVIEW**. Trust: **UNREVIEWED**.
No reviewer policy, approval or certificate was created. Highest certified level
remains L1 ARTIFACT_VERIFIED. G03-G05 are not verified.

The existing prepare/seal/validate/ingest/assess workflow accepted three observed
events, a native CDB log, two full mapped images and a distinct derived PE
candidate. This is no longer a missing-runtime-capture blocker.

## Environment And Scope

After explicit owner authorization, a complete working copy and a copy of the
installed Microsoft-signed x86 CDB were placed under
`artifacts/capture_work/host-20260918-1430/`. The source and working executable
matched original SHA256
`fb72296cab5950b74d8f7c98155145f7c5f58749c3011adb0540325b60749dd1` before each launch.
CDB version: 10.0.29617.1000; binary SHA256:
`88f77f5fab6d9d68de421853b263bfca5f3d89f8557eba0769fe3b5f233a12c9`.

34 enabled program-specific Block rules cover both directions for all 17 EXEs
in these client/debugger copies. ActiveStore reports Full enforcement (CIM value
1) plus inactive-profile information (value 5); all firewall profiles are enabled
and permit local rules. Native enum arrays are used, not display-string guesses.
Rule group: `GOD2-Research-host-20260918-1430`. Rules are intentionally retained.
No global firewall profile, Application Control or Defender setting was changed.

This is **program-scoped network restriction, not VM/filesystem isolation**.
The host remains online; rules do not constrain arbitrary external child
executables. The manifest's `loopback-only` describes the captured program's
network scope, not the host. A human reviewer must assess this limitation.
Client/debugger launches were non-elevated and bounded to 120 seconds. The
separate elevated helper only installed/queried the owner-authorized rules.
The copied CDB passed a benign x86 debugger probe before any GOD2 launch.

## Direct Observations

Successful transition run: 2026-09-18 14:29:58 UTC.

- Actual client PID: 17296 (`0x4390`); thread: 1376 (`0x560`).
- Actual module base: `0x00400000`; SizeOfImage: 3,174,400 bytes (`0x307000`).
- Packer entry hit: `0x00702001` (`pushad`).
- Transfer source hit: `0x007023BF` (`ret`); stack target: `0x0054A3E8`.
- One native single-step reaches `0x0054A3E8` in the same thread.
- Two further single-steps reach `0x0054A3E9` and `0x0054A3EB`.
- Later stop reaches a startup call instruction at `0x0054A40E`.

The target's prior 32 bytes were zero. Captured restored bytes begin:
`55 8b ec 6a ff 68 d8 6a 57 00 68 a8 a6 54 00 64`.
Native `db` rows are compared against the mapped files during normalization.
Native FILETIME values are converted to Unix nanoseconds without inventing
sub-second timing. Equal native timestamps remain equal.

Neither startup-call execution nor a resolved import is asserted merely because
the debugger stopped at a call instruction. Native continuation is retained for
later OEP review, but no normalized `oep_candidate`/`import_resolved` is submitted.

## Separate Artifacts

The immutable capture directory is `artifacts/runtime/<capture ID>/`:

- `before.bin`: full mapped image at the packer entry, before decompression.
- `after.bin`: full mapped image immediately after the observed RET transfer.
- `unpacked-candidate.exe`: derived PE with raw offsets/sizes mapped to captured
  section contents and the observed target set as a candidate entry.
- `derivation.json`: parent/child hashes and every changed mapping field.
- `native-cdb.log`, debugger commands, process timing and firewall/probe records.

The candidate is not a raw dump or repaired PE. Section flags are preserved;
runtime `!vprot` reported PAGE_READWRITE despite observed instruction execution.
No executable flags or import tables were invented to make G03/G04.5 pass.
Candidate SHA256:
`a4be37679e219d8b00abc504db1e3e3d8d1198096e7a2a08c9f17f56c69ee07c`.
Raw evidence directories have ACLs restricted to the current user, SYSTEM and
Administrators. Capture directories are excluded from source control.

## Earlier Attempts Retained

The first host run created a real client process but failed to create dump files.
Its unconditional PACKER/CANDIDATE labels were printed at an OS termination
address and are **not valid hit evidence**. That attempt was not imported.
The following diagnostic run obtained an initial mapped image and an exit stack,
but did not establish the unpack transfer. Relative dump paths and a software
breakpoint at the packed entry enabled the later successful capture. Original
failed-attempt logs remain untouched; no file/code-security protection was disabled.

## Human Boundary

Worksheet: `artifacts/reports/host-cdb-g02-review-request.json`.
Reviewer, decision, attestation and all approval checkboxes remain unset/false.
An independent authorized human must inspect the native step sequence, mapped
bytes, derived PE transformation, host restriction limitations and regression
results before submitting any approval. The agent does not grant reviewer trust
or promote G02 itself. The previous sandbox policy-denial records remain history.

## Verification And ACL Recovery

Debug/Release builds passed; CTest passed 16/16 in each configuration
(115.75 / 116.73 seconds). Python discovery passed 66 tests in 115.181 seconds.
All three original vault artifacts passed integrity verification. These results
are automated regression evidence, not human approval of the capture.

An ACL-hardening mistake initially removed child-file access. Access to all
sealed/working capture files was restored and the original capture hashes were
revalidated. The first elevated repair request was reported canceled. After the
owner approved a second UAC request, the remaining administrative diagnostic,
working output `firewall-install.json`, was repaired at 2026-09-18 14:42:23 UTC.
Normal-user reading and its recorded SHA256 were verified; the repair helper
and all copied client/debugger processes exited. Its contents are not used as
the successful capture's firewall proof;
the independently queried ActiveStore record `firewall.json` is sealed and readable.
No evidence bytes were changed to resolve the ACL issue. See
`artifacts/reports/host-cdb-acl-status.json` preserves the earlier pending state;
`artifacts/reports/host-cdb-acl-repair-final.json` records the successful repair.

## Primary References

- [Program-specific firewall rules](https://learn.microsoft.com/en-us/powershell/module/netsecurity/new-netfirewallrule)
- [Firewall enforcement states](https://learn.microsoft.com/en-us/windows/win32/fwp/wmi/wfascimprov/msft-netfirewallrule)
- [Native memory export](https://learn.microsoft.com/en-us/windows-hardware/drivers/debuggercmds/-writemem--write-memory-to-file-)
