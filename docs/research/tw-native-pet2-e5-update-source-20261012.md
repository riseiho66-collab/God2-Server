# Round326: actual E5 PET2 update source

Added RecoveredE5Update, a lossless read-only source contract for TW S2C E5.
It describes qualified family3 direct write operands. It changes no existing
pet state, admission, storage or Application route and supplies no D6 restore
history, item consumption or server gameplay rule. Complete route increment0.

## Actual incoming source

Pinned mapped image149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763
and original PE5fcf8cbfaf31d2635b4541886336293249cde61c0877de6f5a435cc2b9559fde
agree on all selected cuts. Addresses here are hexadecimal VAs, base400000.
WORLD table cell46B968 selects4691D9, which passes logical+1 to4A3320.
Length cell4016B8 selects4012D0: MOV EAX,9; RET. Thus E5 has logical9/body8,
including two trailing opaque bytes. The earlier A5A40/RVA neighboring update
lead is now joined to a concrete incoming opcode; proximity never paired it
with C2S D6. Historical20260920 four-WORD observations retain their old scope.

Complete4A3320..4A3362 uses body5>>6 and the four-cell4A3364 table. Family3
loads the actual PET2 panel from world+232EBC and calls4A5A40. Families0/1/2
call4A32D0/4D6DD0/4A33F0 and remain opaque in this contract. A second complete
mechanical519370..519908 map supplies translated E5 case519839 ->4A3320.
The secondary method's parent phase ownership remains OPEN; no new battle
phase binding or source-chain count is credited.

## Existing-row guards and exact writes

Complete4A5A40..4A5D05 first checks incoming body4 in42..44. It selects
panel+72*(slot-42), requires nonzero row WORD0, then4A5090 checks stored
row BYTE2 in42..44, key6D61..7F58 inclusive and actual459A60 metadata lookup.
These methods do not compare stored slot to incoming slot. Numeric range alone
cannot stand in for metadata lookup, owner custody or a trusted acquisition.
Existing RecoveredPet2Stats's strict upper endpoint is a different predicate;
this new consumer evidence does not establish a real7F58 definition or authorize
broadening the saved-instance admission contract.

Let V be little-endian DWORD body0..3, S=body5&3F. The original35-byte
translation and18-DWORD target table establish the following direct writes.
Offsets are relative to the existing72-byte FB body, not the incoming E5 body.

| S | Existing body write |
|---|---|
|0|BYTE3=low8(V)|
|1|DWORD8 low24=V low24; upper8 preserved|
|2|DWORD4 bits25..31=V low7; lower25 preserved|
|3/4|DWORD4/0C low14=V low14; other bits preserved|
|5/6|DWORD4/0C bits14..24=V low11; other bits preserved|
|7|BYTE22=low8(V), raw semantics|
|8/9/10/11|WORD24/26/28/2A=low16(V)|
|17/18|WORD10/12=low16(V)|
|19|WORD14 then WORD16, both low16(V)|
|20|WORD16 only=low16(V)|
|34|BYTE23=low8(V), raw semantics|
|12..16,21..33,35..63|No direct row write; conditional refresh tail still runs|

Root caught a meaningful shorthand error in the worker's initial summary:
4A5C50 does not jump over4A5C54/57. Selector19 falls through and writes two
WORDs; selector20 enters at4A5C54 and writes one. REPORT-CORRECTION-02.md is
required alongside the retained original REPORT.md/seal. The source preserves
the actual sequence rather than imposing a symmetric four-stat interpretation.

Selector2 separately changes inventory DWORD bits8..14 at world+8560C+24*slot.
Active slot44 selectors1/3/4/5/6 call independent HUD children4ACEA0/4AC360/
4AC550/4AC740/4AC930. GUI handles/flag20 can refresh4A40C0/49B850. These child
effects remain outside the direct row contract. Both opaque E5 tail bytes and
all unrelated FB bits remain distinct from missing gameplay authority.

## Source and accounting

RecoveredE5Update retains all9 bytes, including unsupported families/selectors
and invalid slot bytes. Its optional family3 field-write view supplies offsets,
widths, masks and inserted bits, with an explicit inventory side-effect flag.
It does not apply writes, call repositories or emit packets. Empty writes mean
only no direct FB write; native conditional refresh is still possible. No
native32-to-common64 extension or new native level/cap is inferred.

A new append-only frontierv18 classifies E5 as INDEPENDENT_FORMAT_ONLY. Native
rows/lengths/dispatch targets and old frontierv17 remain unchanged. Independent
format classes9->10, nondefault ledger-unclassified117->116. Reply48, push11,
gated4, TW candidates156, world74=partial50/control11/unconnected13 and S2C252
remain unchanged. Mixed282/groups26/pending10/CUSTOM135 and CN counts unchanged.
All newly connected bidirectional/opcode gameplay increments0; whole-game
denominator and completion percentages remain null. This is source progress,
not restored PET2 gameplay or current-client acceptance.

Native delivery retains14 cuts:2350 code bytes and136 data bytes; complete
mechanical method maps are not global novelty or whole-game coverage. Worker
seal-02 contains67 members/213199B, SHA256
1ea80a92c447141790e26aa417dad637b77efdc4a836f084282c4745663125f0 under
C:/Users/risei/.codex/artifact-archives/god2-server/20261012/tw-route-frontier-source-review-326.
The first partial capture, initial summary/seal and explicit correction remain
immutable. Full images are hashed references rather than copied members.
The retained capture tool uses exclusive external output; its repository path
adaptation was statically reviewed, not rerun to duplicate the sealed cuts.

PHASE1 file/hash/PE/Capstone/source review and static report only. No build,
compiler, tests, native/runtime/VM/emulator/resource codec, game DB/SQL,
migration, activation, deployment or client change. Existing accounts/saves,
auth/chat/IME/portraits/fonts/text conversion remain preserved. Full TW/CN/web,
shared storage, common64, coin99999999999, stack99 and native levels remain
the active goal. Next source work: E5 families0/1/2 and actual secondary parent
phase; actual gameplay work: source-qualified full after-state/rules/history,
item debit, causal response sequence and original state ownership.
