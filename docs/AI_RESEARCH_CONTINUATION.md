# AI Research Continuation

## Authorization And Trust

The owner explicitly agreed to AI technical review and further controlled captures
while retaining UNREVIEWED status and issuing no human certificates. This relaxes
the research pause only, not the human certificate requirements. No review policy,
reviewer identity, approval, attestation or promotion is created. Old sealed
captures remain unchanged. This document is not a second G02 review package.

## Fresh Diagnostic Attempt

Run: `ai-continuation`, 2026-09-18T15:38:13 UTC.
Source: `artifacts/capture_work/host-20260918-1430/output/`.
Script: `capture-ai-continuation.txt`; native trace: `ai-continuation-stdout.log`.
Original, working executable and CDB hashes were checked by the existing launcher,
which also checked effective program firewall rules before the non-elevated run.
This remains program-scoped network restriction, not VM/filesystem isolation.

Observed PID 0x552C, TID 0x6360, module base 0x400000. The fresh run reproduced
packed entry 0x702001, RET at 0x7023BF and stack target 0x54A3E8. It exported
distinct full before/after images without overwriting the previous capture.

At 0x54A40E, native instruction stepping entered 0x6C224C50. `lm a @eip`
reported the working-copy `client/ddraw.dll`, range 0x6C200000-0x6C26C000;
the observed target RVA is 0x24C50. The top stack word was 0x54A414, the expected
return address. This establishes entry into the observed module, not an exported
API identity. The debugger's nearest-export label is not a verified function name.

The subsequent `gu` stopped at ntdll!NtTerminateProcess+0xC, PC 0x775C9E6C,
not 0x54A414. Subsequent `p` commands failed with No runnable debuggees.
Therefore printed AI_CALL_RETURN and AI_CONTINUATION_END labels are NOT proof of
a call return or continued startup. Do not infer that the function never returned:
the observed trace does not cover every instruction during `gu`.

The exit stack contains KERNEL32!ExitProcess and God2+0x14C7B4, but CDB explicitly
warned that stack unwind information was unavailable and frames may be wrong.
No termination cause, intentional protection check or successful startup is inferred.

Memory queries again report current PAGE_READWRITE in the client image, while
the entered ddraw region reports PAGE_EXECUTE_READ. Both recorded AllocationProtect
as PAGE_EXECUTE_WRITECOPY. The cause of the client protection/execution discrepancy
remains unresolved. No process execution-policy query was captured in this run.

## Disposition

PARTIAL_DIAGNOSTIC_CAPTURE, NOT G03 READY_FOR_REVIEW. No normalized oep_candidate
or import_resolved was fabricated; this attempt was not ingested into the gate
ledger. Raw outputs, command script, loaded-module disk copy and checksums are
retained in a separate restricted diagnostic archive. An end dump exists, but it
was taken after the termination stop and is not normal-startup evidence.

The wrapper exited without timeout; its exit code zero does not mean the client
initialized successfully. No copied client/debugger process remained afterward.

## Next Bounded Experiment

Use explicit breakpoints at the expected return address and process-exit entry
instead of treating `gu` completion as a return. Record exit arguments and stack
before termination. Preserve module disk hashes and distinguish module-relative
addresses from export identities. Capture process execution-policy observations
and protection changes without altering security policies. Do not patch the
client or its DLL to force startup. Independent human certification remains absent.
