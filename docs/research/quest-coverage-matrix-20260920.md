# Current Quest Source Coverage Matrix, 2026-09-20

## Result and scope

**PASS: 60,420 Mission_data lifecycle cases and 1,712 boundary cases.** Every
one of the current client's 418 missions and 2,014 original description steps
was exercised in both DB4 and DB5, at every journal slot 0..14. This materially
extends the selected mission 1/165/418 scenarios.

Qualification is **offline original-native text scenarios with synthetic
stimuli**, not real player/gameplay verification, formal server loopback, or
live E2E. This does not mean quests are complete or gameplay is implemented.

| Current source | Unique source records | Coverage in this deliverable |
| --- | ---: | --- |
| Mission_data | 2,432: 418 definitions + 2,014 descriptions | All descriptions, both forms, all 15 slots |
| ACTMIS requirements | 169 | Source totals and hashes only; runtime coverage UNKNOWN |
| Daily descriptions | 85 | Source totals and hashes only; runtime coverage UNKNOWN |

No joins between those tables are inferred. Authoritative main/side
classification, acceptance, prerequisites, progress, branching, completion,
turn-in, rewards, deduplication, repeat/reset, ownership, persistence, initial
journal state, C2S authorization, rendering, and live E2E remain unknown.
Literal titles and reward/requirement text do not establish these rules.

## Owned paths

Only these four new paths belong to this delivery:

- `tools/strike_lab/quest_coverage_matrix.py`
- `tests/research/test_quest_coverage_matrix.py`
- `docs/research/quest-coverage-matrix-20260920.md`
- `artifacts/research/quest-coverage-matrix-20260920.json`

Existing Evidence/Player, native harnesses, prior quest tests, shared runtime,
CMake, Lua, SQLite, and status files were not edited. No server database,
retired archive, UI, network connection, client process, compiler, or child
agent was used. Tests prohibit subprocess, socket, and SQLite connection
creation. Read-only source enumeration uses the current sibling `God2`.

## Evidence and counting

`quest_player_scenarios.Evidence` validates the original image and Mission_data
source/decoded hashes, source structure, mission order, and step order before
execution. The matrix additionally validates each original description against
its raw source bytes and rejects duplicate description source lines.

Pinned image SHA-256:
`149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.

Mission_data source SHA-256:
`659c8f38ffd9c34107969b449afd16488665a08970110910c9aed8448a0bb716`.

Mission_data decoded SHA-256:
`f57cb8d1a9426e2f797c9cdfea32beb07642415ae3e2bb30a8909373a1c0a5f0`.

The JSON records source and decoded hashes, source paths, declared counts,
actual row counts, and runtime-coverage qualifications for all three tables.
Requirements/daily hashes identify enumerated inputs, not verified gameplay
contracts. Each mission retains its original definition source line, row hash,
name bytes, description count, and UNKNOWN main/side classification. Each
description retains its exact step, source line, source-row hash, text hash,
byte length, passing slot masks for each subtype, and passing case count.

For every description, both masks are 32767 (`0x7fff`), proving all 15 slots;
each description has exactly 30 passed cases. A source-driven coverage audit
requires every mission, step, subtype and slot exactly once. A duplicate pass
cannot increment the ledger. Cases count as passed only after all lifecycle
checks and restoration pass. Failures produce a FAIL report and exit 1;
boundary failures retain the current case and completed boundary counts.

| Measurement | Actual passed count | Meaning |
| --- | ---: | --- |
| Unique missions | 418 | Source definitions represented by checked steps |
| Unique original description steps | 2,014 | Distinct source rows, not operations |
| Lifecycle cases | 60,420 | 2,014 steps x 2 forms x 15 slots |
| Lifecycle native operations | 483,360 | 8 successful native slices per case |
| Original text-byte checks | 181,260 | Read, staged selection, and replay read per case |
| Clear/fallback checks | 60,420 | Empty native description after clearing |
| Additional boundary cases | 1,712 | Separately counted below |

## Native lifecycle and isolation

Two long-lived Player VMs execute the main matrix, one per subtype. Every
case runs receive -> read -> staged select -> replay -> read -> clear ->
blank read -> restore. These are synthetic test schedules, not original
server exchanges or quest progression sequences. Receive/replay/clear/restore
use the original native dispatcher and writer. Both description consumers
check the original source bytes plus NUL at the native-resolved pointer.

All 15 slots begin populated with original first-description references.
After each case, native sync restores the target's baseline so other slots
remain populated throughout the next case. Every operation checks all 15
slots, selected packed value, current page, page count, refresh count,
suppression, and adjacent canaries against the established native contract.
Read/select checks retain the Player oracle's pointer, source-byte, stack,
and state assertions. DB4 and DB5 selection/suppression differences are
preserved; replay is not incorrectly treated as free of refresh side effects.

Player traces are discarded through a zero-capacity deque. The artifact
retains per-source coverage, not hundreds of thousands of memory snapshots.
Two more reused VMs cover boundaries: four VMs total per whole matrix.

The local runner omits the shared harness's per-call wall-clock watchdog,
whose Windows overhead was substantial, but retains its 100,000-instruction
cap and exact stop-PC assertion for every native slice. This is an instance
override in the new tool; shared harness code and original instructions are
unchanged. No game callee or return value is substituted.

## Boundary findings

| Probe | Passed cases | Observed boundary |
| --- | ---: | --- |
| One-past-last description for every mission/form | 836 | Empty fallback through read and click; packed record preserved |
| Selector zero for every mission/form | 836 | Aliases first source text; not counted as another original step |
| Empty/out-of-catalog mission values | 8 | Empty fallback for both consumers |
| Slots 15, 255, 0x80000000, 0xffffffff | 8 | Stop at native assertion call RVA C9688 |
| Prefix lengths 1..12 for DB4 and DB5 | 24 | Expected unmapped input read; full mapped UI allocation unchanged |

Invalid slot DB5 changes selection before the assertion in all four probes.
The entire mapped UI is compared with the pre-call snapshot allowing only
that exact dword change. DB4 permits no UI change. These are successful
regression observations of a non-atomic native boundary, not successful
rejection with no mutation. Assertion continuation is not executed.

Truncation checks assert both fault addresses and PCs. One-byte prefixes
fault at RVA `854FD`; longer prefixes fault at `8565B` (DB4) or `85693`
(DB5). The expected read is beyond the logical input at its unmapped guard
page, not an unrelated unmapped region. Full mapped UI snapshots and journal
state remain unchanged. Python-side invalid mission/step/slot/subtype inputs
are also rejected before native execution or UI mutation.

Description slices stop at renderer entry `10F580`. Page/click registers
are staged; actual page-button dispatch and rendering are not executed.
No transport framing, coalesced socket delivery, server validation, or reward
behavior is established by these cases.

## Reproduction and actual results

From `C:/Users/risei/Desktop/God2/God2-Server`, run in this order:

```powershell
python -B -m tools.strike_lab.quest_coverage_matrix --output artifacts/research/quest-coverage-matrix-20260920.json
python -B tests/research/test_quest_coverage_matrix.py -v
```

CLI: exit 0, status PASS, **18.453 seconds**, 60,420/60,420 lifecycle cases
and 1,712 boundary cases passed. Timing is printed to stdout, not embedded
in deterministic JSON. The artifact uses sorted keys, ASCII JSON and LF
newlines, with no timestamps, durations, machine-specific absolute paths,
or massive traces.

Tests: exit 0, **10 tests in 18.630 seconds**, OK. The tests execute the whole
native matrix again and compare its serialized bytes with the CLI artifact.
They also independently enumerate all 60,420 tuples; audit original source
lines/bytes; reject missing, duplicate, or altered coverage; check invalid
argument isolation; and inject a failure to verify that failed cases and
operations cannot be counted as passed. Failure injection only tests report
accounting and never supplies a simulated native success. No broader suite
was run.

Artifact size: **1,006,381 bytes**. SHA-256:
`e6a7a5cbeaa9db317cc5bcf8cf44ed354afe4795ab0ccff7d9a530a48339f40e`.

The first full CLI run correctly exited 1 after 18.117 seconds: all 60,420
lifecycles passed, but the boundary snapshot started at a non-page-aligned
UI pointer and exceeded its mapped allocation. The snapshot now starts at
the allocation base. A follow-up truncation guard was also corrected to
account for short prefixes whose native value read starts several bytes
beyond the input end; exact observed addresses and PCs are now asserted.
These were local test-fixture corrections, not client/runtime fixes. The
final artifact and independent rerun both passed after those corrections.
