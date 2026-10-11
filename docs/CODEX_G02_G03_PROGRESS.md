# Codex G02 And G03 Progress

## G02 Decision

G02 **CODEX_VERIFIED**, narrow claim: the observed runtime unpack transition into
restored client bytes occurred. No human attestation or human policy was created.

Certificate: `8d9a22ef63ea9ebd66cb944fc1cf93ac540d898ba4c913d6d3014932363c258b`.
Stored in `artifacts/codex-certificates/<certificate>.json`.
Initial live audit: VALID_CODEX_ONLY. Always audit again before relying on it.
Capture: `6e1ed0632ab7559cb8d21871f59a43ab75fb2157dda9b58fab4242dabccdfbde`.

Fresh regressions: Python 68/68, Debug CTest 16/16, Release CTest 16/16,
artifact verification 3/3; both configurations built successfully.
Native register/stack observations, normalized bytes, original/working hashes,
attachment hashes and independent struct-based candidate reconstruction agreed.
Logs: `artifacts/reports/codex-g02-20260918T154257508979/`.

The previous human ledger remains unchanged and is no longer the operative
project acceptance model. See CODEX_AUTONOMOUS_REVIEW.md. No permission semantics,
stable OEP, repaired imports, normal startup or protocol compatibility is implied.

## Fresh G03 Diagnostic

Run `ai-return-exit`, 2026-09-18T15:48:50 UTC, PID 0x19E8, TID 0x5120.
Original/working/CDB identity and effective program firewall were checked before
launch. Packed entry, RET and candidate entry were reproduced with new mapped
images. The old capture was not modified.

Observed call/return sequence:

1. At 0x54A40E, single-step entered 0x72984C50 in the copied ddraw.dll, loaded at
   0x72960000. This matches module-relative offset 0x24C50 from the prior attempt.
2. Explicit breakpoints were placed at expected return 0x54A414 and ExitProcess.
   The return breakpoint fired first, same PID/TID, with ESP restored to 0x1AFF00.
   EAX was 0x23F00206. This proves the observed return, not the API's semantic name.
3. Sixteen bounded step-over commands followed. The call at 0x54A441 to 0x54F12A
   was stepped over to 0x54A446 with EAX=1. Its internal path was not traced.
4. The branch at 0x54A449 was taken to 0x54A453, where the experiment deliberately
   stopped before the next call. This run was ended by debugger quit, not by a
   newly observed spontaneous ExitProcess hit.

This resolves the missing first-call return observation. It does NOT establish
why the earlier `gu` ended at termination; that attempt remains intact. Never
claim the first call was non-returning based on the earlier log.

Bounded static decoding with Capstone 5.0.7 of the earlier mapped candidate agrees
with the startup instructions and call/branch addresses. This is local structural
correlation, not a complete CFG or a stable-startup proof. Step-over hides callee
internals, so absence of a return to the packer inside those calls is not proven.

Current client memory protection still reads PAGE_READWRITE. Process execution
policy was not captured and the discrepancy remains unresolved.

## G03 Decision

**NEED_MORE_EVIDENCE**, operational class REVIEW_REQUIRED. No G03 certificate.
The diagnostic has not been normalized/ingested as a G03-ready bundle and has no
own G02 certificate. It must not borrow the old capture's certificate. It supports
a longer startup hypothesis but not yet a stable startup path.

Next work: extend beyond 0x54A453 using explicit call/return/exit stops, preserve
branch and protection observations, and obtain a bounded trace of callee internals
where needed. Then normalize the fresh observations and independently check that
capture's own G02 prerequisites before any G03 promotion. G04+ remain unestablished.

Raw outputs are preserved in the original work directory and a restricted
`artifacts/capture_work/ai-return-exit-archive/` with a hash index. No client/DLL
patching, security-policy changes, import reconstruction or packet guesses occurred.
