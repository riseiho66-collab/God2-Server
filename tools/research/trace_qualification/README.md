# Trace Qualification Harness

Run from the server repository root. This workflow uses the existing
hash-checked, non-elevated host capture runner and work-copy firewall checks.
It does not issue certificates or alter sealed captures.

`prepare.py frame-a` and `prepare.py frame-b` generate scripts exclusively.
Use `tools/research/host_capture.py capture` with that script and matching
run ID. Existing outputs must never be overwritten. Both runs are already
consumed; design a new named experiment for further execution.

`review.py` consumes both completed logs and emits the qualification,
transition frame ledger, partial coverage map, correlation, code-page samples,
and narrow existing RET claim. Its report destination is exclusive too.

Method: disable the gate-entry software breakpoint while waiting for the
stack-derived return; re-enable it only after a matching boundary return.
Keep the existing instruction budget. Retain native stacks and register dumps.
Frame-b additionally observes 32 instructions after the caller continuation.

Success at a boundary requires PID/TID, PC, ESP+4, ordered timestamps,
stack return address, and the preserved caller return word. This local match
is PARTIALLY_QUALIFIED, never QUALIFIED: disabling gate entry hides possible
nested transitions. Depth and parent frame remain null, not guessed zero.
QUALIFIED is intentionally unreachable until independent nested-transition
and client-continuation validation is implemented and reproduced.

An actual tool failure is TOOL_ERROR; unexplained identity, stack or context
mismatch is FAILED. No absence claim is made for unseen client execution.
Code-page hashes use the established restored .text range [0x401000,0x570000)
at candidate, first boundary, completion and optional liveness samples.
They do not exclude transient changes between samples.
