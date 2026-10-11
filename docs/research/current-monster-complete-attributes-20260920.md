# Battle Attribute Candidate Exclusion

Follow-up: the previously static-only88 bulk writer is now executed and
documented in `current-battle-vitals-batch-20260920.md`. It copies side0 current
HP/MP for14 slots and does not establish wild attack/defense values. The table
below retains this audit's original execution boundaries.

The subtype5 control fields also have executed gate evidence in
`current-battle-command-gate-20260919.md`, including a 2026-09-20 same-state
secondary-grant/dual-command regression. The historical table's static-only
wording is local to this attribute audit, not the project's current gate coverage.

**Zero original monster physical/magical attack/defense values recovered.**
The new executed edge is a received-result WORD bank, not a four-stat record.
Its writer is `12CAAA`; its independently executed reader `128852` passes the
signed WORD to the original `MP %+d` formatter. This excludes this particular
candidate. It does not prove that every battle consumer lacks attack/defense.

Only `current_monster_complete_attributes.py`, its matching research test, and
this document were added. No earlier metadata/HP/MP/card-appearance proof was
rerun. No catalog enumeration, source/archive scan, ROM preload, UI, network,
DB, shared file, production change or child agent was used.

## Pin And Dispatch

Only the current mapped image supplies native instructions and constant data:
`artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin`.
SHA256 `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
BASE `400000`; all addresses and owner offsets below are hexadecimal
RVA/file offsets unless explicitly labelled decimal. Packet offsets include
the opcode. Inputs are synthetic diagnostic bytes, never official values or
evidence that a server sent these amounts.

The actual `114332` switch uses byte indices `11465C..1146CA` and DWORD targets
`114634..11465C` (exclusive ends). There are exactly nine nondefault opcodes
within `1C..89`; the other entries select `1145C0`. This is this dispatcher,
not a claim about every receiver in the executable.

| Opcode | Case / callee | Numeric candidate / prior boundary |
| --- | --- | --- |
| 1C | 114358 / 115C90 | Existing participant metadata/identity proof; excluded from rerun |
| 38 | 114525 / 117560 | 11C7F0 selection update; existing skill-selection proof |
| 83 | 11436B / 116AE0 | Action-indexed fields; new kind-zero 0D branch below |
| 84 | 1143DD / 116740 | Existing effect/action proof through 12C430/12B060; not requalified |
| 85 | 114449 | Gate/length/queue handling, no dedicated attribute callee in this arm |
| 86 | 114464 | Seven-entry subtype switch below |
| 87 | 114518 / 117540 | Existing 11C520 skill-pointer producer |
| 88 | 114538 / 118A90 | Static +1 DWORD -> B+A9E9C64/+68; per-slot pairs, final call 12D360; not executed here |
| 89 | 114582 / 118BF0 | Existing result-slot/EXP/exit proofs; not requalified |

The seven DWORDs `1146CC..1146E8` select:

| 86 subtype | Case / callee | Boundary |
| --- | --- | --- |
| 0,6 | 11447A / 117230 | Shared callee, not proof of identical subtype semantics; 0 already qualified, 6 not extended here |
| 1 | 11449E / 1173A0 | Existing HP/MP record proof |
| 2 | 1144D8 / 117500 | Static controls: +3 byte selects 126060 or 1202D0; no execution claim |
| 3 | 1144AE / 117480 | Existing normalized flags -> actor+DB8, WORD -> +278 |
| 4 | 1144C8 / 1177C0 | Existing card/appearance candidate; excluded from rerun |
| 5 | 1144BE / 117590 | Static slot/control and +5 WORD decimal-digit consumers; no execution claim |

For 83, the first action table `1171D4..1171EB` indexes `1171AC..1171D4`:

| Action (hex) | First target |
| --- | --- |
| 1 | 116C9C |
| 3,17 | 116CF5 (existing skill association) |
| 4,E | 1170CE |
| 5 | 1170D5 |
| 7 | 116ECD (static packed selector -> 12DCC0/resource paths) |
| 8 | 116CC8 (static WORD +9 -> boolean B+488 on selected side) |
| 9 | 11714B |
| D | 117142 |
| F,12 | 116CB2 |
| 2,6,A,B,C,10,11,13,14,15,16 | 117152 |

All eventually reach the separate actor switch in `12C520`; its 23 DWORD
targets occupy `12CC3C..12CC98`. The CLI emits both complete decoded action
tables, not just guessed opcode names. Action D targets `12CA2D`, where
logical WORD +B selects the already-qualified nonzero accumulator or the new
zero branch. Existing `current-damage-formula` only qualifies the nonzero arm.

## New Native Writer

A single continuous run starts at `114332`, calls the real `116AE0`, type-0
lookup `11E6E0`, `12C520`, `12A8D0`, `12C000` and `12C0C0`, then returns to
`1143A1`. No game or CRT callee is replaced. Explicit preconditions are an
already-started phase, matching marker gate, existing actor action byte +239=1,
and a valid actor handle +1A. The same actor address/snapshot is retained
while its slot-zero pointer is installed on side 0 or 1. No wild-actor type
discriminator or original enemy numeric identity is inferred from that fixture.

| Native operation | Exact source and destination |
| --- | --- |
| 12CA2D | Read packet WORD +B=0 to select this branch |
| 12CA43 / 12CA46 | When M+30C is FF, set it to packet BYTE +3 |
| 12CA4C..12CA5B | BYTE index at M+30B = packet[+3] - M[+30C], modulo 256 |
| 12C062 | Read table BYTE image[171600 + packet[+D]] |
| 12C051 | Read table BYTE image[171610 + packet[+E]] |
| 12C1D2 / 12C1E4 | Write these bytes to actor+27A+index / +27D+index |
| 12CA9C / 12CAAA | Read packet WORD +9; write unchanged bits to actor+280+2*index |

The style example uses packet +D=9, +E=0: the native table bytes at `171609`
and `171610` are 87 and 09. Additional actor writes are only action BYTE
+1E7=marker and +1E9=0D. The manager also receives +309=marker, and the
existing battle flag DWORD B+A9E9C6C is cleared. Full actor comparisons prove
all other bytes remain untouched, including every HP/MP field.

For side 0 the complete consumed packet byte set is
`00,01,02,03,05,06,09,0A,0B,0C,0D,0E`. Side 1's target-mask scan additionally
reads `07,08`. Exact ordered reads, widths, values, writes, virtual addresses
and RVAs are emitted in JSON. Packet bytes remain unchanged. The tested index
window 0..2 is a research bound, not a recovered native bounds check. Index 0
uses the native FF-baseline initialization; indices 1/2 declare an existing
baseline of 32 decimal, not a fabricated sequence of prior receipts.

## New Native Consumer

The consumer is explicitly staged, not continuous action playback:

1. Independent prefix `1287CD..128824` reads the receive-written style bytes
   at `128809/12880F` into EBX/EBP. It stops before `128824 -> 12A200`, an
   unresolved pose/resource call. No return value is supplied for that call.
2. Independent post-call island starts at `128829`, with declared actor,
   manager, stack and the previously observed EBX=87/EBP=09 live-ins. Original
   `128852` reads/sign-extends actor+280+2*index; `128865 -> 147AF7` executes
   the original CRT formatter with image string `19D970`, `MP %+d`.
   It writes the actual text to the native stack buffer and stops at `12886D`,
   before the next state write. No HP/MP mutation or renderer is executed.

Diagnostic WORD FFE2 produces literal `MP -30` on both sides. WORDs 007B and
8000 produce `MP +123` and `MP -32768`. These are client display amounts
supplied by the diagnostic packet, not MP base values and not magical attack
or defense. The sender-side computation/source of packet WORD +9 remains
unknown. The trace does not authorize interpreting this bank as four attributes.

Missing actors return through the original code with no actor writes. Changing
the consumer index to a slot never written by the producer raises the explicit
source guard at real native read `128809`; poison cannot become a recovered
style/amount. Image memory is read/execute, complete image bytes are compared
after execution, all native data accesses are region-checked, and code ranges
and instruction budgets are closed. No adapter supplies a game result.

## Verification And Remaining Work

```powershell
python -B -m unittest tests.research.test_current_monster_complete_attributes -v
python -B -m tools.strike_lab.current_monster_complete_attributes
```

Final run: four focused tests passed in 0.095s, including exact table/read assertions.
Coverage is six positive diagnostic cases, both missing-actor sides, one
unwritten-source guard and narrow input validation, not a large suite or a
full-dispatch execution claim. The CLI subprocess exited 0 within its ten-second
bound; JSON parsing verified two native examples, both `MP -30`, and zero
qualified attack/defense values. CLI evidence includes span hashes and all traces.

The inspected new bank is now excluded as a four-stat source. Remaining native
boundaries are `128824 -> 12A200` for continuous playback, and other statically
listed dispatcher branches not executed here. The 88 receiver's `12D360` and
unqualified 83 action/resource branches remain candidates for bounded review,
not evidence of hidden attributes. No local or sender-side four-stat producer
has been established. Physical attack/defense and magical attack/defense stay
null, with **0 usable original monster values**.

## Main Review: Bounded 88 Continuation

After the worker delivery, main independently reran its four tests: 4/4 in
0.093s. Main then followed the remaining 88 candidate using the same pinned
image and `current_battle_entry.NativeRun`, without changing its instructions.
The original length routine returns **121 decimal logical bytes** for88.

Two inline native checks, with actor poison A5 and5A, continuously execute
`114332 -> 118A90 -> 12D360 -> 12D9F0`, returning from the latter two real
callees and stopping **before `118BD8 -> 116AC0`**. Each executes851 instructions.
Preconditions explicitly include local slot FF, battle flag0, counter FFFFFFFF,
all28 type-zero actor pointers, and negative display handles at actor+1D8.
The local-owner update and active display branches therefore remain untested.

`12D360` loops exactly14 times with lookup arguments side0, slot0..13, type0.
For each slot i, logical DWORD `5+8*i` is copied at12D37D to actor+DE8,
and DWORD `9+8*i` at12D388 to actor+DEC. The previously qualified field
semantics identify these as current HP/MP, not maximums or attack/defense.
The test inputs were distinguishable synthetic pairs
`(1001+17*i, 2002+31*i)`, never claimed as actual monster values.

Each check verifies exactly28 actor writes and compares all4096 bytes of all28
actors: only those two DWORDs change on side0; all14 side1 actors, both maximum
fields and other actor bytes remain unchanged. Packet reads match the exact
28 DWORD offsets. Region checks cover all data accesses, packet bytes remain
unchanged, and the complete executable image remains byte-identical. Both
checks pass in one0.328s shell command; no UI or resource loader is executed.

This excludes the tested88 bulk-update branch as a four-stat initialization
source. It does not exclude every88 precondition, prove its official timing or
recover any original species value. Logical byte118 also feeds a battle-local
byte; remaining opaque bytes are not assigned semantics. Cleanup, the subsequent
queue operation, live traffic and sender-side values remain outside this proof.
