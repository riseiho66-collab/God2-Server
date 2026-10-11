# Current command-control transition, 2026-09-19

Bounded worker B. Only the pinned current mapped client image is authority:
`artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin`,
SHA-256 `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`,
base `0x400000`; addresses below are RVAs, equal to image offsets.
No retired evidence, server rules, runtime/session edits, or E2E claim.

## Concrete Handoff

The native command-enable producer is **S2C 86 / discriminator 5 -> 117590**.
Its flag-controlled writes grant `this+A9E9C38` and `this+A9E9C3C`. The command
tail consumes these in priority order, after its cleanup calls. There is a
separate C2S35 action `0B` producer gated by local completion counters/latches,
and a separate S2C89 consumer leading conditionally toward loop exit.
None establishes the server's authoritative turn or permission policy.

Main's typed basic attack / `InBattle` transport remains separate. In particular,
native `this+44 != 0` is not an equality check against a recovered InBattle enum.
Existing current battle/skill command tests supply prequeue contract coverage;
this worker adds transition and transport-boundary evidence only.

## Command Enable And Consumption

Define A=`+A9E9C38`, B=`+A9E9C3C`, W=`+A9E9C34`. W is called a wait/control
marker here only to distinguish its storage, not to assign server semantics.

| Current instructions | Observed transition |
| --- | --- |
| `114332..114351`, opcode table `114634/11465C` | Logical opcode 86 routes to `114464`. |
| `114464..114473`, table `1146CC` | Logical byte +1 equal to 5 routes to `1144BE`; `1144C1` calls `117590` with the logical record. |
| `1175B2..1175DC` | If logical byte +3 bit 0 is set: A=1; actor byte `+51` = logical byte +4 low nibble. |
| `11776E..117793` | If logical byte +3 bit 1 is set: B=1; actor byte `+52` = logical byte +4 high nibble. |
| Same producer slices | Absent flag bits preserve controls and actor bytes. Neither slice writes W. Nibbles can be 15; this does not override the builder's actor guard. |
| `119200..119252` | If A!=0: clear A; set W=1 only if B==0. Otherwise, if B!=0: clear B and set W=1. If both are zero, preserve W. Also set `+46C=-1`. |

Thus, starting from `(A,B,W)=(1,1,0)`, the control slice gives `(0,1,0)`,
then `(0,0,1)`. Re-enabling comes from the incoming producer above, not the
outgoing action byte's continuation bit. A direct builder call does not check W.

`118E50` requires A or B nonzero for basic/skill; action `0B` explicitly bypasses
that first gate at `118E59..118E5F`. It still checks actor low byte <=14, signed
count <=14, and `+44 != 0`. Action 3 additionally needs the real selection
accessor to return nonnull. The normal kind-0 split path requires `+468==0`;
nonzero diverts through `119164 -> 11E910`, outside the split-path proof.
Connectivity is checked at enqueue sites, after earlier state/target accesses.

The postqueue boundary `1191EE` is also reached when disconnected, when the
split skill count is nonpositive, or when its kind takes a no-queue path.
`1191F3 -> 112130(0)` and `1191FB -> 1120B0(0)` precede control consumption.
Tests execute the control slice **after** those calls with explicit registers;
they do not execute or replace the UI helpers. Disconnected builder output is
empty yet reaches this cleanup boundary. Consumption therefore is not a
successful-send acknowledgement.

## Rearm Boundary

The first grant branch calls `115670` at `117693`, then `115740` at `11769A`.
The second grant branch calls `115740` at `117797` only when A is zero.
Both helpers reach `1121F0` iff `+A9E9C28==0` and `+A9E9C64!=-1`.
Tests execute each helper up to that call or its return-side boundary.

Inside `1121F0`, `11223B..112247` sets selected index `+A9DF73C=-1`, W=0,
and `+A9DF760=-1`. This write slice is executed independently, with EBX=0
and EDI=-1 as established by the preceding instructions. Earlier calls
`1121FD -> 112130(1)`, `11221D -> 10B1B0`, `11222B -> 1129C0`, and
`112236 -> 1108C0` remain unexecuted. That is the exact remaining boundary
before claiming an integrated next-input/UI rearm.

## Continuation And Flush

Kind-0 split skill at `119179..1191EC` emits one 17-byte logical record per
target, preserving order. `1191BB` sets action bit 80 on nonfinal records;
`1191C6` restores the original action on the last: `83,...,83,03`.
This is record-sequence framing only, not proof of another turn.

Queue `132E0` checks `queued_length + body_length + 1 > A00` and calls flush
at `132FE` before appending if exceeded. For a 17-byte record, length `9EF`
fits exactly; `9F0` triggers flush. There is no continuation-aware atomic
reservation, so an accumulated sequence can cross a flush boundary.
`115AF7..115AFA` supplies the network object and calls `13370` in the loop.

`13370` skips sending when disconnected or queue length is nonpositive.
Otherwise `133AE -> 124D0 -> 10A90/10B80` encodes the accumulated queue;
the socket-call boundary is `12501`. Native tests preserve queues containing
1, 2, or 14 skill records in a fresh VM, initialize the real zero-seed encoder,
and stop there: total frame sizes 20, 37, 241, with matching LE length prefix.
The queue still holds 17/34/238 bytes at that boundary. The independent
post-send slice `133B3..133CC` clears length at `133B9`, without inspecting a
send result. No socket call or assumed send result is substituted.

## Next Producer And Completion

`115A59..115AD8` conditionally issues C2S35 action **0B** with actor `+51`,
count `+45C`, target pointer `this+44C`. Its exact local predicates are:

- `+A9DF6BC==0` and `+A9E9C44==0` on both paths.
- If `+144C1C!=0`, clear it, then require the wrapped DWORD subtraction
  `(+A9E9C64 - +A9E9C68)` to have sign bit clear, or `+A9E9C64==-1`.
  This uses JNS, not an unbounded signed greater-than comparison.
- Otherwise require `+A9E9C64==+A9E9C68` and `+A9E9C48==1`.

The call is `115AD8 -> 118E50`; builder cleanup sets `+A9E9C44=1` for action
0B at `11925E..11926C`. This is a concrete continuation/control producer.
Calling it a server-required acknowledgement or advancing a server turn would
exceed the evidence. It stays outside the basic attack parser.

Opcode **89** routes to `114582`. If caller-local DWORD pointed to by
`[ESP+2C]` is nonzero, it clears `+A9EA4C4` and defers the consumer. Otherwise
`11459A -> 118BF0` consumes it. The consumer's independent tail
`118E20..118E35` sets `+A9E9C30=0`, `+A9DF6BC=1`; the dispatcher also sets
the latter at `1145B6` after removing the record. Resource/UI work between
entry and tail is not executed by these tests.

The loop at `1159F8` checks `+A9DF6BC==1`, then calls `12AED0`. With its
result equal to 1 and `+A9E9C50==0`, it sets that latch and calls `85070`.
A nonzero latch leads to `85260`; a nonzero result writes `+44=5` at
`115A39`. On the next loop head, `+44==5` calls `12AED0`, and a nonzero
result branches to exit boundary `115C40` at `11584F`. Tests stop at the
unresolved helpers and independently supply result-register snapshots to
verify these branches. They do not claim the helpers return those values in
a real battle, or that a reward/outcome has been applied.

## Verification And Limits

### Continuous Control Producer To Queue (2026-09-20)

The tenth test starts once at115A59 and executes the real115AD8 call into118E50,
the original selection accessor and queue copier, stopping at1191EE before UI
cleanup. It does not call the builder separately or resume across skipped calls.
Three admitted event/counter combinations crossed with connected0/1 give six
runs. Both ordinary grants begin zero, explicitly demonstrating the0B bypass.

With actor3, targets14/27, context12345678 and a real absent-selection fixture,
connected runs enqueue exactly17 bytes:35/03/0B/00, side masks0/2001 and the
unchanged context. Unwritten bytes are not certified constants. Disconnected
runs reach the same boundary but enqueue nothing. The completion latch+ A9E9C44
remains zero at this pre-cleanup stop. All loaded image bytes remain unchanged;
no socket, UI helper or synthetic callee return is used.

The first attempt exposed an unmapped selection-accessor dependency, not a
client failure. A fresh pre-call fixture supplies selector storage and the
explicit -1 selection index; original11B8C0 executes normally. All10 tests pass.
This qualifies local control production only. It does not recover authoritative
turn/ACK policy, execution of the cleanup latch write, or live battle acceptance.

### Continuous Closed-Handle Cleanup (2026-09-20)

`test_builder_cleanup_continuously_consumes_controls_before_clock` extends
execution through the actual post-builder calls to 112130 and 1120B0, stopping
before the timeGetTime import call at 119252. No instruction is skipped, callee
return substituted, or image byte modified. Four initial grant combinations
(1/0, 0/1, 1/1, 0/0), crossed with connected/disconnected, give eight runs.
Ordinary actions start at 118E50; the zero-grant 0B cases start at 115A59 and
execute the gate, producer call, builder, queue and cleanup in one continuation.

Fixtures explicitly provide negative signed UI handles in the battle selector
and world UI, valid cross-object pointers, 28 distinct inactive effect slots,
and no selected skill. These are synthetic closed-handle states, not a captured
visible battle. Original 111CD0, 111D30, 111CC0, 111C30, 111D60, 1127E0 and
98C90 execute and return. All 28 effect references reach 360B0. World tooltip
cleanup clears its two state DWORDs. Battle panel state A9E9C28 and selection
state A9E9C2C clear, 46C becomes FFFFFFFF, and first/second/wait fields match
the separately recovered consumption rule. Connected runs queue 17 bytes;
disconnected runs queue none yet still consume controls. No socket is called.

The 0B latch A9E9C44 remains zero here: its write is after the unexecuted clock
call, so this test does not certify latch completion or the function's final
return. Active UI handles, first-grant rearm and own-server live acceptance
remain open. Control consumption is not delivery acknowledgement and does not
justify enabling a guessed server ACK/turn policy. No production activation,
custom balance promotion or formula recovery follows from this result.

Verification: `python -m unittest discover -s tests/research -p
test_current_battle_command_gate.py -v` passed all 11 tests in 0.578 seconds.

### Post-Clock Return And Duplicate Suppression (2026-09-20)

The twelfth test starts explicitly at 119258 AFTER the timeGetTime import.
EAX is a supplied synthetic timestamp (0 or FFFFFFFF), not an observed OS return.
Actions 1/3/0B, old latch 0/1 and second-grant 0/1 produce 24 cases. Original
12D560, 11BE40, 119B20, 834E0 and 1A950 run without code modification. The
fixture has an empty participant pool, absent text manager and cursor already
selected as 1. Thus no rendering or OS cursor function needs a substituted
return. World cursor fields 232F36/232F38 become 1; battle selection state
A9E9C2C clears and A9E9C14 records the supplied timestamp.

Only action 0B sets A9E9C44 to 1; other actions preserve its previous value.
Without second control, execution reaches the original RET 10, EAX=1 and the
expected stack position, with A9EA4C4=1. With second control it stops BEFORE
115740, leaving that field unchanged; this is not proof of that rearm path.
Re-entering the real 115A59 gate on the same state reaches 115ADD when latched
and 115AD8 otherwise. All image bytes remain unchanged. These are explicit
post-clock and follow-up gate executions, not end-to-end runtime acceptance.

A bounded immediate-displacement search identifies a latch-clear instruction
at 118BC5 in the block before calls 12D360 and 116AC0. This is a next trace
location, not yet proof of its triggering packet, reachability or full return.
Initialization also references the field at 111804. No server ACK opcode is
inferred from either location.

Follow-up: the existing bulk-vitals evidence already identified118A90 as the
S2C88 consumer. The extended `test_current_battle_vitals_batch.py` now executes
the real dispatcher through its full inactive-resource receiver return, then
the same-state115A59 gate. Pending events defer the consumer and preserve the
latch; an admitted88 clears it and permits0B under the documented equal-counter
fixture. See `current-battle-vitals-batch-20260920.md`, Dispatcher To Receiver
To Readiness. This supersedes the missing-trigger qualification above without
claiming general turn permission or complete live dispatch.

Verification: the gate suite passes all 12 tests in 0.904 seconds. Native
formulas, active-handle UI, OS timing and live gameplay remain unqualified.

### Same-State Follow-Up (2026-09-20)

The ninth test, `test_secondary_grant_returns_then_two_commands_share_native_state`,
executes `1175A0` through the actual `1177B5` return with first control already
present and both UI handles negative. Entry is explicitly after the OS clock
call: EAX is a synthetic timestamp, not an emulated or observed OS result.
Flags 02/82 and packed actor bytes 00/7D/ED cover six cases. The original code
copies the timestamp and cached DWORD, sets second control, preserves first
control, and extracts the high-nibble actor without entering UI refresh helpers.

The same VM then executes the original action builder twice, keeping the real
queue and grant fields between calls. Queued records have side bytes 0 then 1;
the independent post-UI control-consumption slice clears first then second.
A third ordinary action returns zero and does not grow the 34-byte queue.
The input record remains unchanged. This closes a synthetic state-transfer gap;
it does not execute the intervening post-builder UI helpers, the OS clock,
normal first-grant rearm, a socket, or a live battle. Actor arguments are supplied
by the fixture, not proven to be selected by live UI. No runtime policy or
server grant emission is enabled. Nine tests passed in the follow-up run.

The eight-test results below are the original handoff, not the current count.

```text
python -B tests/research/test_current_battle_command_gate.py -v
python -B tools/strike_lab/current_battle_command_gate.py
```

Eight tests pass. The second command prints bounded disassembly after whole
image hash verification. The tests execute original instruction bytes, real
selection/queue code via the existing fixture, and the real encoder. No code
patches, helper stubs, client process, sockets, DB, or CMake changes. Explicit
slice entry registers and fresh synthetic memory are not captured live state.
Existing prequeue/typed transport suites were not repeated for this handoff.

Main independently reported this gate suite passing 8/8 in 0.314s and the
selected formal CTest suite passing 54/54 in 160.51s. Those are main's
verification results; this worker's local gate run passed 8/8 in 0.288s.
The bounded disassembly command also completed successfully (584 lines).

Priority next calls, if continuing separately: `1121F0` through its UI helpers
for integrated rearm; `11E910` for the alternate skill aggregation path;
`12AED0`, `85070`, `85260` for completion readiness and exit. No broad catalog,
damage, target ownership, timing, server turn, or gameplay rule is recovered.
