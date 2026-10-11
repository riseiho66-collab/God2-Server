# Battle S2C88 bulk current vitals

Current image SHA256:
`149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
All addresses/offsets below are hexadecimal RVAs unless labelled otherwise.
Inputs are synthetic diagnostics, not official monster values.

The native length table entry for88 points to123A, returning121 decimal bytes
including the opcode. Battle dispatcher114538 calls118A90 at114550.
118AB0..118ABA obtains the logical pointer and adds1;118BBE passes that body
pointer to12D360 at118BCB. These outer bindings are statically checked, not
claimed as a continuous dispatcher execution.

The complete original12D360 function was executed through its `ret 4`, calling
the actual11E6E0 actor lookup and12D9F0 refresh helper fourteen times. For each
slot0..13, lookup arguments are side0, slot, type0. The two input DWORDs at
logical offsets5+8*slot and9+8*slot are copied unchanged to actor+DE8/+DEC.
Previously established native vitals consumers identify these as current HP/MP.
The source does not supply attack/defense or maximum HP/MP in these pairs.

All28 actor pages (both sides) are compared in full: exactly28 DWORD stores
affect side0 current values; side1 and maximum fields are unchanged. Input is
read-only and original code is RX and unchanged. Negative actor UI handles
select the real12D9F0 early-return branch; no display callee is stubbed. Five
full-width patterns include0,1,7FFFFFFF,80000000,FFFFFFFF. These do not clamp or
calculate stats. Active renderer handles and the118BD8 cleanup remain outside
this execution proof.

Important precondition:12D37D writes through the lookup result without checking
for null. A missing first actor produces an actual emulated unmapped write at
DE8. This is NOT a safe sparse-update packet. It also does not prove that an
inactive slot is null in normal client construction; a complete native roster
must be established before any future emission.

`RecoveredBattleVitalsBatch.h` is an owning C++20 read-only121-byte codec with
bounded slot access. It retains the four leading body bytes and four trailing
bytes without assigning them meanings. Parsing is structural, not roster or
context validation. Emission remains disabled. The fixture checks owned input,
exact roundtrip, out-of-range indices, all opcode bytes, lengths0..122 and opaque
byte preservation, and compares28 values against original stores. Three new
tests pass; no production database data or gameplay handler was changed.

```powershell
python -B -m unittest discover -s tests/research -p test_current_battle_vitals_batch.py -v
```

This closes an unexecuted bulk-value consumer from the earlier attribute audit,
not the missing original wild-stat producer. Verified wild attack/defense values
remain zero. No official live packet, battle E2E or damage formula is established.

## Continuous receiver follow-up

The original118A90 entry is now executed continuously through12D360 and all14
lookups/refresh helpers, stopping on entry to116AC0 (called at118BD8). The local
slot byte B+51 is explicitly FF, so the local role/skill/UI path is not claimed.
The three cleanup callees beyond that boundary are not emulated or stubbed.

Six cases cover initial cached DWORD B+A9E9C64 equal to FFFFFFFF or11223344,
crossed with B+A9E9C6C flags0,1,2. Diagnostic logical+1 DWORD is FEDCBA98 and
logical+118(decimal) BYTE is A7. The actual instructions establish:

- Initial cache FFFFFFFF copies logical+1 into both +A9E9C64 and +A9E9C68.
- Otherwise +A9E9C70 receives20(decimal), and +A9E9C68 stays unchanged.
- Flag exactly1 clears +A9E9C6C without the later overwrite of +A9E9C64.
  With an already initialized cache, this branch NEVER READS logical bytes1..4.
- Other flag values leave that flag unchanged and replace +A9E9C64 from logical+1.
- Logical byte118 is copied to +A9E9C84. WORD +A9E9C78 and DWORDs +A9DEFB0,
  +A9E9C44 and +A9DF6B8 are cleared.
- Starting B+44 at0 sets it and +A9E9C48 to1; other starting states are not tested.
- Every case still copies all28 HP/MP DWORDs exactly. Tail bytes117,119,120 and
  the opcode are not read by this function under these declared conditions.

All nonstack mapped pages are compared against observed bounded writes; source
packet is read-only and the complete mapped image stays unchanged. An initial
test incorrectly expected bytes1..4 to be read on every path. The observed
initialized-cache/flag1 branch corrected that expectation; no native code was
changed. No meaning such as speed, round number, sequence increment or server
authority is assigned to the cached DWORD or flag from storage alone.

Static inspection of116AC0 shows calls to120300 and5F450. The former traverses
two sides,14 positions and6 actor types, clears actor+DF8..EC7 and passes50
subrecords to11FD70 before further resource calls. The latter resets resource
table handles. These are next-step cleanup leads, not executed turn progression
or proof that the client is ready for another action. Four focused tests pass.

## Cleanup actor-pass execution

A separate native run now executes120300 through the complete actor traversal,
stopping before12039D's resource-manager tail. It executes168 original lookups
(2 sides x14 slots x6 types) and8400 calls to the real11FD70 helper. The fixture
provides distinct4096-byte actor pages, negative type5 handles and a null resource
owner at context+28. Thus resource release calls120356/11FDB5 are legitimately
not reached, not replaced. This is not a continuous88-to-full-cleanup return.

Full actor-page comparisons establish the only changes on this branch:

- Actor bytesDF8..EC7 become zero (208 bytes).
- Each of50 eight-byte entries beginning at actor+34 has WORDs at entry+0,+2,+6
  set toFFFF; its entry+4 WORD remains unchanged.
- Current HP/MP and maxima atDE8..DF7, and every other actor byte, are unchanged.

After that run, removing only side1/slot13/type5's pointer causes an actual
unmapped write at12033F while clearing null+DF8. All168 lookups occur; this last
entry cannot safely be omitted merely because it is not a displayed fighter.
The evidence identifies a complete-table precondition, not the normal lifetime
or initialization rules of these objects. A null resource owner is an explicit
diagnostic condition, not a claim about a normally running client.

The existing native harness gained an optional instruction limit (default4000
unchanged); this larger loop uses250000 and must reach the declared stop. Code
remains pinned and unmodified. Five bulk tests plus nine shared-harness scalar
regressions pass (14 total). The first run exposed a Python ctypes bytearray
argument mismatch, corrected by supplying bytes; no native instruction changed.

Remaining: resource-manager cleanup tail, active handles, normal constructor
lifetimes, and the actual next-action readiness gate. No turn permission,
authoritative monster values or original damage formula is inferred.

## Complete inactive-resource receiver return

The follow-up now closes the previously stopped cleanup tail and executes
118A90 ->12D360 ->116AC0 ->120300 ->5F450 ->118BE8/ret4 continuously. Stack
cleanup is checked. This uses168 distinct actor objects, local slot FF, negative
actor handles, a null actor-resource owner,80 inactive graphics entries and an
empty active-graphics list. Explicit pointer/cursor/counter fixtures are not
claimed to come from normal client constructors or a live process.

120300 executes the original2D9E0 ->146CF7 formatter twice, including14CF08 and
the byte writer14D649. At2DA10, the resulting stack strings are read and compared
byte-for-byte with the two original image literals19D644/19D634. The native
289B0 destination is itself a ret in this build; it was not patched or stubbed.
An initial range guard stopped at14D649; disassembly verified that helper before
extending the permitted native instruction interval.

The original28880 resets its cursor;2E000 traverses80 records and2DE30 sets
each inactive record's DWORD0 to0 and WORD28 toFFFF.2DFA0 resets its count and
counter fields404/40C without entering active-resource destruction.5F450 resets
the first two WORDs in each of1028(decimal) resource records, stride76(decimal).
The entire resource table is checked: all other bytes remain poisoned/unchanged.

Before the final continuous run, all actor pages are restored to nonzero scratch
fixtures. Exactly side0/type0 current HP/MP for14 slots changes from the packet;
all168 full pages are then compared, including expected scratch cleanup and
unchanged maxima/other fields. Input is read-only, original image unchanged,
and no callee return value is substituted. There are182 real actor lookups:
14 for the updates and168 for cleanup. Five focused tests pass.

This proves normal function return only under those explicit inactive-resource
conditions. Active graphics destruction, real constructor provenance, local
role UI, dispatcher continuation, next-action permission and live current-client
battle acceptance remain open. No production emission gate is enabled.

## Dispatcher To Receiver To Readiness

The full inactive-resource test now enters the original dispatcher at 114332,
not merely the 118A90 receiver. With logical opcode88 and a nonzero pending
event DWORD (pointer from stack+2C), original 114538..11454B clears A9EA4C4
and takes 1145C0 without entering the receiver. The existing latch A9E9C44=1
remains set. No conclusion about when the real event queue becomes empty is
implied by supplying this synthetic pending DWORD.

With that DWORD zero, the same VM executes 11454D ->118A90 ->12D360 ->116AC0
and all previously qualified cleanup functions through the real RET4, returning
to 114555 with the dispatcher's stack restored. The two native formatted strings,
182 lookups, all168 actor pages, resource table, read-only input and unchanged
image are checked as before. Thus opcode88's binding to the latch-clear function
is executed, not only inferred from a static call target.

Before receipt, the same-state115A59 gate rejects while A9E9C44=1. After receipt,
the latch is zero and the gate reaches115AD8 with action0B on the stack. This
fixture uses initial current counter FFFFFFFF, so the receiver sets both current
and previous counters from the packet; enabled=1 and done/event remain zero.
It does not claim every88 grants permission or that0B is a player attack.
Other counter conditions remain governed by the existing gate tests.

The test stops before114555's subsequent queue-management work and before
115AD8's producer call. It does not prove complete outer dispatch, ordinary
attack rearm, active UI, authoritative turn policy or live gameplay. Five tests
passed in6.402seconds with the extended continuous dispatch coverage.

## Original Ring Consumption After Receipt

The continuous dispatch test now proceeds past114555 to1145C0. A separately
mapped writable scratch record is passed to the receiver; the ring source at
INPUT remains read-only. The native15840 ->1000 ->1200 ->123A lookup returns
121 for opcode88. Its outstanding pushed constant1 is the third argument to
11D3D0 (consume=true), not a second argument consumed by15840's RET4.

11D3D0 copies exactly121 bytes into scratch and advances the read index. With
one complete record in a256-byte ring, reaching the write index resets both
indices to zero. Original11456C sets A9DF6C0=1 and114576 clears A9EA4C4.
Dispatcher stack depth, scratch bytes, immutable source and image are checked.
The existing182 actor lookups, full page/resource comparisons and follow-up
0B readiness check remain in this uninterrupted receiver-to-consumption run.

An additional bounded test starts at114555 with read indices0/135/200/255,
crossed with no trailing record or17 trailing bytes. It covers contiguous,
exact-end and wrapped copy branches. Only121 bytes are consumed; when trailing
bytes exist, the read index advances modulo256 and the write index is preserved.
The source ring is read-only and unchanged in all eight cases. The following
record is deliberately not dispatched; this proves its retention, not acceptance.

Verification: all six bulk-vitals tests passed in5.311seconds. The previous
114555 stop is superseded by1145C0. 12AC20, the subsequent OS clock call, the
outer function return, active graphics and own-server runtime acceptance remain
outside this evidence. No authoritative turn policy or formula is recovered,
and no custom combat design is promoted to production.

## Dispatch Tail To First Real Clock Boundary

The continuous test now runs past1145C0 through1145DB's real call to12AC20,
stopping BEFORE its imported timeGetTime call at12AE2F. This is an earlier
nested OS boundary than the outer1145EA clock call. No clock return is supplied.
The dispatch stack+28 points to an explicit phase byte0. Original12AC20 resets
context+A7FBC64/A7FBC68, scans side0 and side1 type0 for14 slots each and stores
phase0 at context+308. Existing negative actor handles and actor byte1E9=A5
select the inactive branches, leaving all actor pages unchanged by this scan.

The complete run now performs210 native actor lookups:14 scalar updates,
168 cleanup lookups and28 phase-scan lookups. The two counters are verified
zero, phase byte zero, and stack is exactly32 bytes below dispatcher entry at
the nested clock boundary. Full actor, resource-table, ring and code-image
checks still pass. The trace must not contain1145E4: the outer pending-event
clear is after12AC20 returns and has NOT yet executed. The subsequent gate
test remains a separately entered same-memory slice, not a real event-loop
continuation after the outstanding clock call.

Six bulk-vitals tests passed in5.400seconds. This supersedes the1145C0 stop;
active animations, both real OS clock returns and full dispatcher return are
still open. For live continuation, current-live-offline-monster-20260920.md
documents actual world-owned battle/renderer objects and168 actor pointers;
its successful constructor runs do not certify this packet-receive path.
