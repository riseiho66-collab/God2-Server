# G02 Human Review Handoff

Status: P0 prepared; P1 awaiting an owner-designated independent human.
This document is an agent-produced evidence index, not a review or approval.
G02 consistency is READY_FOR_REVIEW; certification remains BLOCKED/UNREVIEWED.
No reviewer identity, policy, attestation, approval or promotion is supplied.

## Review Package

From the server repository root, open
`artifacts/capture_requests/g02-human-review-20260918/review-g02.json`.
The adjacent `test-report.txt` contains labeled automated regression transcripts,
not human findings. `package-files.json` inventories the handoff files by SHA256.
`capture-validation.json`, `gate-status.json` and `vault-verification.json` are
fresh automated checks; none replace examination of native evidence.

Capture: `6e1ed0632ab7559cb8d21871f59a43ab75fb2157dda9b58fab4242dabccdfbde`.
Original: `fb72296cab5950b74d8f7c98155145f7c5f58749c3011adb0540325b60749dd1`.
Below, C means `artifacts/runtime/<capture>/`; A means
`artifacts/clients/<original>/`. Resolve these against this repository.
Capture attachments and their exact hashes/sizes are listed in C/manifest.json.
Raw evidence remains restricted and must not be uploaded to public services.

## Required Examination

Every row needs the human's own finding; all approval checks start false.

| # | Question | Evidence and examination |
| --- | --- | --- |
| 1 | Original provenance | A/metadata.json, A/hashes.json and vault-verification.json; check original bytes and source provenance, not the candidate alone. Static vault metadata is historical, not runtime gate status. |
| 2 | Working-copy identity | C/host-request.json, C/launch.json, C/manifest.json working_copy_sha256; compare with the original hash. |
| 3 | Native trace | Read C/native-cdb.log and debugger-commands.txt together, including register output and actual step commands, not only printed labels. |
| 4 | Packed entry | Native log line 97: PID 0x4390, TID 0x560, base 0x400000, PC 0x702001; inspect preceding stop/register output. |
| 5 | Transfer source | Lines 107-116: PC 0x7023BF, opcode C3 / RET; inspect the cleared breakpoints and following native step. |
| 6 | Stack target | Lines 113-118: target 0x54A3E8 and stack contents at 0x1AFF74. |
| 7 | Same-thread continuation | Lines 122-127, 157, 165: same PID/TID, target then 0x54A3E9 and 0x54A3EB. This short sequence is not established normal startup. |
| 8 | Before/after images | C/before.bin and after.bin: each 0x307000 bytes, native export records at lines 102 and 149; verify full-file hashes and offset mapping. |
| 9 | Restored region | Compare image offset 0x14A3E8 for 32 bytes: before zero, after starts 55 8B EC 6A FF 68 D8 6A 57 00 68 A8 A6 54 00 64; compare native db rows and C/events.jsonl event-1. |
| 10 | Derived transformation | C/derivation.json and unpacked-candidate.exe; inspect all raw offset/size changes and candidate entry, preserve parent hashes. This is neither repaired PE nor verified analysis image. |
| 11 | Network restriction | C/firewall.json, host-request.json, host-probe.json; inspect 34 bidirectional Block rules over 17 copied EXEs and active profiles. |
| 12 | Isolation limitations | Host stayed online; restrictions are program-scoped, not VM/filesystem isolation. External child executables are not covered. Manifest loopback-only must not imply host offline. |
| 13 | Regression relevance | Adjacent test-report.txt: historical Debug/Release 16/16, Python 66, vault 3/3; inspect actual transcripts. Unit tests do not prove unpacking. |
| 14 | Contradictions | Inspect gate-status.json counter-evidence and the concerns below; absence of registered counter events is not proof that no contradiction exists. |

## Unresolved Interpretation And Limits

- Native !vprot reports current PAGE_READWRITE (lines 138/146), while instruction
  execution is observed. AllocationProtect is a distinct field. Explanation is
  unresolved; candidate section characteristics remain 0xC0000040. The reviewer
  must decide its G02 relevance, not silently treat executable permission as proven.
- The stop at 0x54A40E is a call instruction location, not evidence that its call
  executed or that its import identity was resolved. No G03/G04 claim follows.
- Earlier startup attempts printed unconditional success-like labels at an OS
  termination address. They were not imported. Their raw files remain under
  artifacts/capture_work/host-20260918-1430/output for comparison/history.
- ACL hardening initially broke access; recovery and unchanged capture identity
  are documented in HOST_RUNTIME_CAPTURE_20260918.md. No evidence bytes were
  edited to pass validation.
- Local reviewer strings and hashes are not authenticated human identities or
  cryptographic signatures. The owner must choose a genuinely independent person.

## Human Action And Stop Condition

The owner designates an independent reviewer and manages review-policy.json as
described in ../tools/research/GATE_REVIEW.md. The agent must not create that policy
or identity. The reviewer personally examines all rows, records findings and
reproduction results, then supplies decision, rationale, timestamp, attestation
and checks in the request. REJECT remains a legitimate outcome.

Only the human-controlled workflow may submit and explicitly promote an approved
review; submission alone is not a certificate. Refresh status and counter-evidence
before acting. Do not approve solely because automated validation passed.

P3 and later work remain paused pending genuine G02 approval/promotion. Existing
certificate chains require the same artifact AND Capture ID at every gate.
A new extended G03 capture will therefore need its own G02 review/certificate
under the current implementation before a G03 certificate can chain to it.
The existing sealed capture must never be amended to add future events. No
cross-capture trust rule is weakened by this handoff.
