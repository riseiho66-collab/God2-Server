# Final G03 Qualification Experiments

Decision: **PARTIALLY_QUALIFIED method; G03 NEED_MORE_EVIDENCE**.
G02 certificates remain unchanged; G04 remains deferred.

## New Result

The prior fourth-boundary mismatch was avoided in two fresh experiments by
disabling the gate-entry breakpoint while waiting for its stack-derived
return, then re-enabling it. Both frame-a and frame-b matched 9 of 9 observed
boundaries, including the formerly failing ZwAllocateVirtualMemory boundary.
Each match checks PID/TID, PC, ESP+4, timestamp order, stack return address and
the preserved immediate caller return word. This is not proof of the root
cause of the old mismatch; that explanation remains UNEXPLAINED.

| Run | PID | TID | Boundary matches | Client decode comparisons |
| --- | --- | --- | --- | --- |
| frame-a | 0x4594 | 0x15C4 | 9/9 | 1485, zero mismatches |
| frame-b | 0x14F4 | 0x4414 | 9/9 | 1501, zero mismatches |

Frame-b continued 32 instructions beyond 0x54A46E and stopped at
ntdll!RtlEnterCriticalSection, PC 0x775A43E0, ESP 0x1AFEC4. This establishes
short-window execution beyond the old checkpoint, not completed initialization
or indefinite liveness. The two runs were debugger-terminated after capture;
neither wrapper timed out or reported failure.

## Remaining Qualification Limit

Disabling the gate breakpoint also hides nested transitions during the return
wait. Matching outer context does not prove nested-transition correlation.
The ledger therefore leaves nested_depth and parent_transition_id null.
Native stack-unwind warnings are retained, not interpreted as proven unwinds.
No boundary gap is declared NON_MATERIAL or BOUNDED_EXTERNAL yet.

These are qualification experiments, not the two formal captures required
after qualification. They own no new G02 certificate. A full per-PID DEP and
page-protection timeline has not been captured, so no old DEP result is reused.
The next method must retain visibility of nested events while preserving
the now-reproduced outer return correlation; another identical RET-only run
would not address this remaining limitation.

## Mutation And Counter-Evidence

Page-by-page hashes compared candidate restored .text [0x401000,0x570000)
with first-boundary and completion snapshots for both runs, plus the liveness
snapshot for frame-b. No sampled page changed and no sampled zero-to-code
population appeared. The original targeted 12-byte watches reported no hits.
These snapshots do not exclude transient writes or alternate execution within
unobserved boundary intervals. The watches ended before the final RET step.

The full known packer range [0x702000,0x706000) was checked against recorded
PCs after MODE_WINDOW_BEGIN: no recorded hits. No termination hook or code-write
marker was observed. This is an active negative-evidence search with incomplete
coverage, not proof that packer return, restart or secondary unpack is impossible.

Every parsed client instruction was compared using native decode, Capstone
instruction length and mapped bytes. External rows are EXTERNAL_NATIVE_ONLY.
This comparison establishes no coverage for instructions absent from the log.

The existing two exact-RET observations are preserved formally as
CLAIM_THIRD_INIT_RETURNS, STRONG, with hashes and their narrow same-PID/TID,
coherent-stack scope. They are not downgraded or expanded into full-routine proof.

## Tool Inventory And Deliverables

Local command lookup found no cdb, windbg, x32dbg or x64dbg on PATH.
The Windows Kits x64 debugger directory contained DLLs but no executable
debugger. Repository inventory located the existing x86 CDB toolchain and
its working copy. The working CDB SHA256 is
88f77f5fab6d9d68de421853b263bfca5f3d89f8557eba0769fe3b5f233a12c9.
No tool download or security-policy modification was performed.

Harness: `tools/research/trace_qualification/`.
Derived evidence: `artifacts/reports/g03-final-qualification-20260919/`.
The coverage-v3 file covers boundary segments only, not the entire startup.
Restricted raw archive: `artifacts/capture_work/g03-final-qualification-archive-20260919/`.
Native logs, snapshots, firewall checks, scripts, reviewer dependencies and
reports are retained with a SHA256 index. Prior archives remain untouched.

Five new focused qualification tests passed. Full project regression was not
rerun. No G03 certificate, repaired imports, or protocol claim was issued.
