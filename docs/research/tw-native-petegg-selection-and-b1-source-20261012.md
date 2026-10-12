# Round329: PetEgg selection initialization and B1 action variants

The missing selected-index source has a concrete native initializer:4D4B80
directly writes primary UI BYTE8=45 and DWORD44/48/4C=0. A complete PetEgg
action also qualifies eight B1 selector variants,0..6/9, distinct from the
already supported client-option selectors7/8. RecoveredPetEggControl preserves
this exact logical2 shape as a standalone read-only source contract. No new
world parser, authoritative handler or gameplay success is enabled.

## Actual index source and initialization boundary

U is the primary UI context WORLD+A7F2F6C. Actual primary setup4817C0 passes
its same context to4D4B80 at481A2A; retained original Main setup invocation
qualifies this U relationship. Complete4D4B80..4D4D7E writes zero to U44,
U48 and U4C, WORD U52=FFFF, then at4D4BB3 writes literal2D to BYTE U8. These are local
initialization writes, not E6 packet defaults or a server-owned egg issuance.
Remaining initializer resource/cache/control children stay opaque. The write
point is qualified; final post-child state and lifetime invariance are not.

Complete4D71F0..4D7230 suppresses reset when any BYTE U71/U72/U73 equals1,
or signed WORD U52 is20..27, equals28 or equals19. Otherwise it calls this
initializer, then4D5910. The complete known close method requires nonnegative
signed U232E66 and widget flag20 before clearing BYTE U50 and calling opaque
children; it has no direct U8 assignment. A reset
method and its local guards do not prove every caller or whole UI lifecycle.

This resolves the previous bounded lack of an actual U8 writer. It does not
establish that U8 stays45 across opaque children, that a newly received3B row
is always the current owned instance, or an owned20-to-E6 numerical formula.
E6's later4D5970 child still can clear U44 low28 before future E5 reads.

## Actual primary action and original B1 producer

Main466B00's needed prefix forms EDI=Main+A7F2F6C at466B0E and calls4820A0
at466B9C. Complete4820A0..48314F obtains control/event operands through
504620, compares selected widget WORD against U232E66 at4826F5 and enters
4D6940 at48270A with the same U. The interior click/input source of504620
is opaque, so this is an actual selected dispatch, not complete input ownership.

Complete4D6BA0..4D6BC2 reads the caller argument's low BYTE, loads queue
context from U86874 and calls4132E0 with opcodeB1 and body length1. Therefore
logical2 has only opcode and selector. No slot, key, full20 instance, timestamp
or current-state token is transmitted. The previously qualified496170 setter
and Main setup relation remain historical references, not new global novelty.

Complete4D6940..4D6B72 first calls opaque presentation work: control22 uses
U48 bits18..31 plus459A60 and4D68D0; other controls call49B820. Only afterward
does event bit02 take priority and call4D5910. Otherwise bit20 is required
for the signed control15..24 jump table. Controls15/22 select close/no-B1
routes in that table. Current-state predicates below are reads after this
opaque prefix; earlier snapshots cannot predict the native outcome.

| Control | Selected native result | Additional current-state gate |
|---|---|---|
|19|B1 selector0 or1|U44 bit29 clear selects0; set selects1|
|20|B1 selector2|Common event gate only|
|21|B1 selector3|Common event gate only|
|16|B1 selector4|Inventory row15h low7 !=1;4D7DF0 returns0; U44 bit29 set|
|17|B1 selector5|4D7DF0 returns0; U44 bit29 set|
|18|B1 selector6|4D7DF0 returns0; U44 bit29 set|
|24|B1 selector9|Inventory row15h low7 ==1|
|23|Local4DC710, no direct B1|Inventory row15h low7 ==1|

Inventory reads use current signed U8 and U85621+24*index. Control16 instead
calls4DA680 when row15h low7 equals1. The complete4D68C0 leaf ignores its
argument and returns1; the actual0E/10/11 calls add no eligibility formula.
Complete4D7DF0 returns0 for WORD U52=FFFF or signed30..32, otherwise1.
The action exits on return1, so selectors4/5/6 require return0. If bit29 is
clear after the other gates, the action takes a local message path instead.
No user-visible names, incubation amounts, debit, reward or server timer policy
are inferred from these numeric controls or client presentation guards.

## Shared opcode, separate unresolved gameplay

TaiwanNativeClientOptions still decodes only7/8 for CUSTOM-0100's default-off
preference policy. Its comment now identifies the separate PetEgg variants;
RecoveredWorldRecords and Application behavior are unchanged. PetEgg decode
accepts only0..6/9 and retains the selector byte; its encode returns that same
byte without inventing operands. No E5/E6 or same-number causal reply is proved.
Selectors outside this selected action remain separate B1 recovery tasks.

The historical ledger's B1 control category describes7/8. Its preserved text
is not a current claim that B1 has no gameplay variants. This round adds the
eight unresolved gameplay variants under a unique field; the old opcode-scoped
world counts do not measure this direction/state/variant gap. In particular,
B1's existence in the world parser does not mean PetEgg is parsed or connected.

RecoveredE5Update's inventory destination comment also now uses the native
inventory owner: family3 actually rereads its owner from pet2 context+DC.
It does not assume that every family has an identical context pointer. The
earlier unsealed draft's broader primary-context wording was corrected before
review/sealing; native operands and all functional source remain unchanged.

Whole-game denominator and TW/whole completion remain null. TW C2S156,
world74=partial50/control11/unconnected13, S2C252, independent11/unclassified115;
CN C2S156/S2Cphase280/length253; mixed282/groups26/pending10/CUSTOM135 unchanged.
New known opcode values, world parser opcodes, authority handlers, phase bindings
and complete bidirectional routes0. The new source relation is not gameplay
completion. Original authority must bind the selector to genuine current owned
slot45/full20 and the actual operation/rules/storage/replies/recovery.

PHASE1 source/hash/PE/Capstone/unique static accounting only. No build/compiler/
tests/native/runtime/VM/emulator/resource codec/game DB or SQL/migration/activation/
deployment/client edit. Full TW/CN/four binary WebSocket paths/shared tables/
common64/coin99999999999/stack99/native levels/frozen saves/auth/chat/IME/portraits/
fonts/text conversion remain active. Native32 flags and display state do not
satisfy the owner's required64-bit wire/object/display and numeric mutation paths.

## External custody

Native package:
C:/Users/risei/.codex/artifact-archives/god2-server/20261012/tw-native-petegg-selection-source-329.
Final native17cuts retain7028codeB/66dataB with mapped149c/originalPE5fc equality;
71 sealed members/218425B, seal SHA256
063ca368c8f0f019217214086a6fedca68a401c11b8cd478cc04139f833c84da.
The first partial capture stopped while decoding arbitrary post-return bytes;
it remains separate preserved evidence. The final script retains that boundary
as raw data. Final totals exclude partial duplicates. Full native inputs remain
hashed references; old packages and parsed ledger values are retained.
The final capture script is retained in tools/reconstruction, without rerunning
or overwriting its exclusive output. Whole methods are not global novelty.
Independent source review retains22 members/103559B under external
round329-petegg-source-review; seal
4386ac6eb630f3f5319a99509f5aebbbafcc5f7e9dd62bef5c5010a6eb392401.
The reviewed PetEggControl header SHA256 is
197f7b289ae25dffee85eef07600672982e4b7a440d7b842fbed0db9d2381c35.
Review found no blocking issue; it is static source review, not compilation or
runtime acceptance. The report/source/ledger snapshots are sealed separately.
