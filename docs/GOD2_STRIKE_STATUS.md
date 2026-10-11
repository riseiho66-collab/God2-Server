# GOD2 Strike Status

All eight client milestones remain UNESTABLISHED: connect, handshake, login,
character screen, selection, world entry, stable heartbeat, movement.
No gameplay, database, Lua or protocol implementation was expanded.

G02 unchanged; G03 NEED_MORE_EVIDENCE; G04 onward unverified.
Existing exact RET and two 9/9 outer-boundary results remain valid in their
previous narrow scopes. No new RET-only experiment was run.

## Current Attempt

Implemented a small per-PID/TID TransitionFrameStack with parent/depth,
expected return PC/ESP, caller word, OPEN/RETURNED/LOST states. Mismatches
are retained; neither unwind nor tail transfer is invented.

| Experiment | Result |
| --- | --- |
| stack-a: hardware gate, breakpoint-command logging | TOOL_ERROR: 120-second timeout; ambiguous/duplicate return records |
| stack-b: hardware gate, inline stop logging | FAILED: unmatched return chain |
| prompt-probe: benign x86 cmd under interactive CDB | PROBE_PASS: prompt-synchronized commands work |
| sync-a: prompt-synchronized hardware-gate tracing | FAILED: unmatched old return-site hit |
| sync-b: additionally clear completed return breakpoints | FAILED: three matches, fourth wrong ESP |

For sync-b, transition 3 entered with ESP 0x1AF9D8, expected PC 0x775C9D0C
and ESP 0x1AF9DC. Observed PC matched but ESP was 0x1AFBA0; caller-word
context also mismatched. Cause remains UNEXPLAINED. The active gate method
does not reproduce the successful disabled-gate method's fourth return.

Frame-ledger depths in failed runs are ordering candidates, not verified
nested callback relationships. Hardware gate visibility alone is insufficient.
No method earned two successful nested qualification runs. Therefore
GOD2-MASTER-CAPTURE-01 was not launched and no gate certificate was issued.

The interactive driver checks the existing client/tool hashes, live work-copy
firewall and non-elevated execution, retains commands/native output, and quits
or kills its own process tree on failure. It does not change the original
client or global security policy. This is host capture, not VM isolation.

Next technical change must address mode-aware observation itself (for example,
a separately probed native-architecture debugger), not enlarge instruction
counts or replay the same x86 breakpoint arrangement.

Evidence archive: `artifacts/capture_work/g03-strike-archive-20260919/`.
Four new frame-stack tests cover nested same-site returns, out-of-order return,
identity/context mismatches and duplicate events. Synthetic tests are not
runtime qualification. Full research regression: 84 tests passed in 117.236s
(`python -m unittest discover -s tests/research`). New Python modules also
passed compilation. No capture/debugger processes remain running.
