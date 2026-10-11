# Current Battle Exit Prerequisites

Pinned current mapped image SHA256:
`149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
Addresses below are RVAs at base400000. No official service or retired corpus.

## Native Helpers Executed

`current_battle_exit_gate.py` closes two previously unresolved helper calls in
the exit slices documented by current-battle-command-gate-20260919.md:

- 12AED0 returns the actual DWORD at manager+2E0, battle+144C18.
- 85260 selects signed handle UI+232DF0/232DF2 for mode0/1 at UI+23D620.
  A negative handle or other mode returns zero. Otherwise it reads
  UI+E2988+10760*handle and returns bit20 only.
- Starting at1159F8, received-result==1 and manager-ready==1 with latch0
  sets the panel latch then calls85070. Execution stops at that real function
  entry; panel creation and active control operations are not substituted.
- An existing nonzero latch polls85260 even without received-result/ready.
  A positive bit20 result sets battle+44 to5.
- At11583C, stage5 with any nonzero manager-ready reaches115C40, the start
  of cleanup. This is a different predicate from the exact1 opening check.

The synthetic suite covers 3072 mode/handle/flag combinations, 12 initial
panel conditions, a preexisting-latch case and16 next-loop combinations.
Original helpers execute and return normally; no EAX injection, code patches,
resuming past unknown callees or host UI operations are used. The two loop
slices remain independent, not a claim that the intervening frame ran.

## Live Read-Only Snapshot

Run `native-socket-exit-state-20260921-01` repeats two actual socket rounds.
At the second friendly HP receiver return, PID15636/TID6508, sequence555:

| Field | Actual value |
| --- | --- |
| Result received, battle+A9DF6BC | 0 |
| Manager ready, battle+144C18 | 1 |
| Panel latch, battle+A9E9C50 | 0 |
| Stage, battle+44 | 1 |
| Panel mode | 0 |
| Selected signed handle | 14 |
| Control byte | 19 decimal, bit20 clear |

These values were read from the real initialized client after enemyHP114 and
friendlyHP76. Nothing writes them. Offline execution with this snapshot does
not open the panel or reach cleanup. No89 outcome was emitted by this run.

## Remaining Work

Native89 is already a57-byte received result/display contract; its fields do
not establish reward authority. Integrate a separately labeled diagnostic
terminal encounter, real89 consumption, panel lifecycle, original cleanup and
world re-entry before claiming battle completion. Do not force stage5, set
control bit20 or relabel this pre-result snapshot as exit acceptance. Actual
death/result animation, awards, durable state and production balance remain
unqualified. Existing own-server diagnostic remains isolated.

Verification:
`python -B -m unittest tests.research.test_current_battle_exit_gate`
