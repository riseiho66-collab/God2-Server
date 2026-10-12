# Round328: actual E6 scalar input and PetEgg instance boundary

RecoveredPetEggStatus now preserves the native E6 logical13/body12 record
and exposes only its three unconditional incoming DWORD copy operands. This
qualifies one independent S2C format; it does not complete a gameplay route.
RecoveredE5Update also clarifies that its legacy world_offset member is relative
to the primary UI context, not the outer WORLD root.

## Actual received source

Pinned149c WORLD table cell46B96C targets4691EB. The case increments the
logical pointer and forms U=WORLD+A7F2F6C, then calls4D6D20. E5's4691D9
case forms exactly the same U. Length table cell4016BC targets the complete
401246..40124C leaf MOV EAX,0D / RET: logical13 is independently qualified
by the native table, not inferred from three DWORD accesses.

Complete4D6D20..4D6DA8 copies body DWORD0/4/8 to U44/48/4C in that order.
The signed WORD U232E66 comparison is issued before the copies, but its
conditional branch follows them. Negative handle skips later display work,
not the copies. No slot/key/type/metadata/range guard qualifies these incoming
values. The source header returns exact DWORD values from logical1/5/9 and
preserves every raw byte; no packet emission or saved state mutation is enabled.

With an initially nonnegative handle, native code reads current signed BYTE
U8, requires the lowWORD key at U85610+24*index nonzero and calls4D5970.
It calls declared winmm!timeGetTime and stores U8C, then rereads the handle
and requires nonnegative plus widget flag20 before4D7E40(1F,36). Neither the
clock's units nor server incubation rules are inferred from this UI operation.

## The copies are not final state

The existing4D5970..4D5E36 method is retained complete for the needed child
boundary. After existing slot/key guards, successful metadata lookup and opaque
UI calls, it rereads signed U8 and BYTE U85621+24*index. This is inventory
row15h, full20 metadata-tail11h. When bit80 is set,4D5A8B performs
AND DWORD[U+44],F0000000, clearing low28 bits. Its other descendants remain
opaque. Thus E6's three incoming values cannot stand in for the final U state
or the current values later read by E5 family1.

The relevant4D6C80 guard admits unsigned slot0..29 or45, keys2455..24B8 or
24B9..251C inclusive and an actual459A60 lookup. These are existing native
presentation gates, not recovered server ownership, reward or timer authority.

## Full20 instance input is a separate relation

Historical4D53F0..4D58F1 is explicitly declared CPMenu::PetEgg_Open. It uses
prior signed U8 to select inventory row U8560C+24*index, whose full20 tail
begins at row+4. Nonzero lowWORD key and459A60 lookup lead definition BYTE11C
to U9; instance DWORD0 bits16..21 become U3C. Only types0E/0F qualify
bits25..31 as the U3A input: values1..8 map to value-1, otherwise0. The
seven-entry table maps U3A0..6 to U3E7/4/2/1/3/6/5;7/default maps1.
Other types' local BYTE operand lacks a qualified upstream assignment here.

This complete method directly assigns neither U8 nor U44/48/4C. No full20
instance-to-three-scalar formula is recovered. Primary3B case46A029 passes
the same U to498DD0. That receiver copies full20 to the incoming physical
slot, and its slot45/widget branch calls PetEgg_Open, but does not directly
store incoming45 to U8. The just-updated row and the row read by Open cannot
be assumed identical. Actual U8 lifecycle remains OPEN.

These known methods were already inspected in September; recapture supplies
bounded current-byte provenance, not new global-method novelty. No E5/E6,
C2S same-number or other causal request/reply pairing is established. E6's
issuer, complete current state, authoritative rules, persistence, ordered replies
and recovery still require source evidence.

## Custody and accounting

The exclusive external native package is
C:/Users/risei/.codex/artifact-archives/god2-server/20261012/tw-native-e5-egg-input-source-328.
It retains20 cuts,3474codeB/286dataB and46 members/104394B; seal SHA256
7c7210c28761490751928680f58d411165a10fdf539546cce3c58c23a8a35f95.
Every cut agrees with mapped149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763
and original PE5fcf8cbfaf31d2635b4541886336293249cde61c0877de6f5a435cc2b9559fde.
Full images remain hashed references, not new copies. Both static capture scripts
are retained in tools/reconstruction with exclusive outputs; they were not rerun
to duplicate the worker capture. Historical seals and ledger fields are preserved.
Independent source review retains17 members/67064B under external
round328-e6-source-review, seal
d73ba2e1f18ff1ae022d86b884f452f40d1eb8bb0f138348bfa0dc48b667bc7d.
It found no blocking issue and reviewed the exact E6 header SHA256
5af27fed8130f5e313c505e904d0e3fe1899fd0a2713eac04d4c8e709268cc7c.

Frontier v19 adds only E6's independent class, retaining all native rows and
historical named increments. Independent formats10->11; unclassified116->115.
TW C2S156/world74=partial50/control11/unconnected13; S2C252=230fixed+22variable,
nondefault206/default46, reply48/push11/gated4. CN C2S156, S2Cphase280/length253;
mixed282/groups26/pending10/CUSTOM135 unchanged. New gameplay opcode values,
phase bindings, authoritative handlers and complete bidirectional routes0.
Whole-game denominator/TW completion/whole completion remain null; goal active.

PHASE1 only: source/hash/PE/Capstone/unique static accounting. No build/compiler,
tests/native/runtime/VM/emulator/resource codec/game DB or SQL/migration/activation/
deployment/client edit. Full TW/CN/four binary WebSocket paths, shared tables,
common64, coins99999999999, stack99, native levels and frozen saves/auth/chat/IME/
portraits/fonts/text conversion remain active requirements. This native32 receive
view does not satisfy the required extended numeric/wire/object/display paths.
