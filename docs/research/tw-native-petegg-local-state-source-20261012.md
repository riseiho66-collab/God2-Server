# TW PetEgg staged local write source (round341)

The actual native pre-action method4D7230 supplies a concrete local write path
for fields also consumed by E5/E6. The new source contract preserves its gates,
unsigned arithmetic and distinct read stages. It does not supply a server
timer, operation rule, owned instance, request lease or causal response.

## Actual branch and arithmetic

Full4D7230..4D78C7 runs on primary U=Main+A7F2F6C before the later UI action
dispatch. Its selected4D76E0 branch requires WORD U+A6D4==0. The field's
gameplay meaning is unknown. It calls the original winmm!timeGetTime import,
then subtracts the current DWORD U8C using low32 arithmetic. CDQ/XOR/SUB
produces the unsigned two's-complement magnitude; CMP/JB admits values>=60000.

For wrapped difference d, sign mask is0-(d>>31), and magnitude is
`(d XOR mask)-mask`, all modulo2^32. At80000000h the result remains80000000h.
The accepted wrapped differences are60000..(2^32-60000), inclusive. This is
native bit arithmetic, not proof of real elapsed time or clock monotonicity.

At4D723D the earlier entry prefix requires a nonzero lowWORD at
U85610+24*signed live U8. That earlier read is not a lease for the fresh U8
later used by4D7733, and supplies no ownership or native slot-range guard.

The branch performs three ordered direct DWORD writes:

| Instruction | Destination | Source value |
|---|---|---|
|4D7718|U4C|first live U4C low18+60 modulo2^18; high14 retained|
|4D7720|U8C|second clock call's returned DWORD|
|4D7733|U85618+24*signed live BYTE U8|second live U4C re-read, masked3FFFF|

The second clock call precedes a fresh U4C read at4D771D. U8 is read afresh
after the U8C write. Those operands must remain separate from the first U4C
and the method's entry row. The row destination is24-byte row+8, or
full20-relative+4. No native slot-range guard is added to this branch.
The literals60 and60000 are retained without inventing their server units.

## Source implementation and limits

`RecoveredPetEggLocalCounterSource` is a standalone C++ source contract. Its
`NativeStageOperands` contains each actual stage operand separately.
`native_difference` uses unsigned low32 arithmetic and a sign-bit mask;
`project` returns only the three ordered direct write values and mathematical
object-relative offsets. It performs no pointer, native, inventory or database
write. A signedBYTE index is converted to a signed64 mathematical offset,
without narrowing its original range or pretending it is an authorized slot.

The public conditions require the applicable same-U native entry path, earlier
live-row gates, valid storage, fault-free calls and values at their exact read
stages. Opaque effects between stages are represented by fresh inputs rather
than assumed absent. Empty projection means this selected branch's gate did
not admit these writes; it does not describe the whole method or its children.
Emission and mutation flags remain false, with no Main, Session or gameplay
caller. Existing E6 status, PetRoom/RomMaps catalogs and frozen code are unchanged.

E6 first copies incoming DWORDs to U44/U48/U4C. Its later refresh can modify
those values, and4D7230 can subsequently modify U4C and the selected row again.
Thus neither an incoming E6 scalar nor this source projection is a final native
state observation. Other pre-action animation/display branches, UI children
and later mutations remain outside the new selected-branch contract.

## Selected-row affinity and pending context

The complete49A330 drag-release path checks a selected drag control, inventory
full20/key/type/metadata and panel gates before calling PetEgg_Open for control45.
It records other UI fields but directly writes no U8. The selected validators
also write no U8. Open consumes live signed U8 after earlier children and at
later rereads. Same-row affinity therefore requires U8==45 at every relevant
read and a stable row/key for a stronger identity comparison.

Known initialization4D4BB3 writes U8=45, but that write does not establish
lifetime invariance across opaque children. Incoming3B slot45 copying also
does not set U8. The selected raw candidate4671A8 is excluded: its EDI has
been replaced by a formal output pointer, so output+8 is not primary U8.

The new pre-action and close-child sources link response-fed fields and local
status/close flags. They expose no demonstrated pending request identity joining
selector-only B1 with F4/E5/E6/E7. The valid F4 receiver directly stores its
list WORD without a direct pending-context gate; outgoing list selection queues
and closes without directly saving the selected index/key/full20. Opaque child
effects remain unknown. Shared U and call order do not establish server authority.

## Evidence and phase accounting

Immutable external341 packages retain complete native ranges, selected excerpts,
source algebra and exact C++ custody. All cuts match pinned149c mapped image and
5fc original PE. Original images are hashed/read in place. Earlier seals remain
unchanged; candidate scans and probes receive no complete-method credit.

- `tw-native-petroom-action-context-source-341`
- `tw-native-petegg-selection-lifecycle-source-341`
- `round341-petegg-local-counter-source-audit`
- `round341-petegg-local-counter-source-implementation`
- `round341-protocol-source-review`

Exact successful script copies under `tools/reconstruction`:

- `tw_native_petroom_action_context_capture341.py`
- `tw_native_petegg_selection_lifecycle_capture341.py`
- `tw_native_petegg_local_counter_audit341.py`
- `tw_native_petegg_local_counter_source_capture341.py`

Successful LF scripts are published as exact source copies without rerunning
completed captures. No C++/API/native/CRT/parser/codec/SQL execution, build,
compiler, tests, migration, activation or deployment occurred. Unique report
`20261012-tw-native-petegg-local-state-source-341` preserves frontier v23 and
all prior ledger fields. New opcode/format/parser/phase/authority/full route
credits remain0. Whole-game denominator and completion percentages remain null;
TW/CN, shared tables, four browser endpoints, common64 domains, explicit coin
cap99999999999, qualified stack99, native levels and frozen features remain
the full active objective.
