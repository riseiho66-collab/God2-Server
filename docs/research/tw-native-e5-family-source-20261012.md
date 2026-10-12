# Round327: the remaining E5 direct families

RecoveredE5Update now exposes the other three native direct-family operands
and exact inventory destinations. The known full9 E5 incoming record remains
lossless. No Application handler, owned mutation, saved-instance grant or
authoritative issuer is activated. Direct consumer qualification is source
progress; new complete gameplay routes0 and whole-game percentage unknown.

## Family0: direct inventory property writes

Known4A3320 family0 calls complete4A32D0..4A331C with the original world ECX.
Native S=body5&3F, V=DWORD body0..3 and I=sign-extended body4 BYTE. There is no
slot range, key, metadata or owner guard in the complete direct function.
S30 writes low16(V) to WORD world+8561E+24*I (inventory row12h); S31 replaces
low15 bits of WORD world+85620+24*I (row14h), preserving bit15. All other S
return without a direct write. This function has no child call or GUI refresh.

The view retains even a negative native index as an operand, never granting
that index access to server state. Structural parse does not sanitize it to a
valid bag slot. Both destinations are opaque instance properties, not stack
quantity or inferred durability/quality/consumption rules.

## Family2: an existing E3 row

Complete4A33F0..4A36EC receives world ECX. Body4 must be42..44; its selected
52-byte row is world+A6D8+52*(slot-42). Row WORD1C must be nonzero. Complete
4A29A0 additionally validates stored row BYTE26 in42..44, key3391..3778 or
5DC1..6D60 inclusive and actual459A60 metadata lookup. There is no equality
check between incoming and stored slot. Numeric range is not lookup success,
ownership or an acquisition. The known guard functions receive no new-method
credit. Table4A3748 has34 translation bytes into23 target DWORDs at4A36EC.

Offsets below belong to the existing E3 body52, not FB72 or incoming E5 body8.
Masks describe only replaced bits; all other bits remain preserved.

| S | E3 direct write |
|---|---|
|0|BYTE23=V low8|
|1|DWORD18 bits10..23=V low14|
|2|BYTE22=V low8; separate inventory row14h DWORD low8 update|
|3/4/5/6|WORD0/2/4/6=V low16|
|7|BYTE21=V low8|
|8/9|DWORD10 bits12..21 /22..31=V low10|
|10/11|DWORD14 bits12..21 /22..31=V low10|
|12|DWORD18 high8=V low8|
|13/14/15|BYTE1E/1F/20=V low8|
|16|WORD24=V low16|
|17/18/19/20|DWORD8/0C/10/14 low12=V low12|
|33|DWORD30=V, full32 raw|
|21..32,34..63|No direct row write; conditional refresh still possible|

Unlike family3 selector19, family2 selector19 jumps after its single write.
Existing E3 getters supply display-field context only, never growth, food,
restore history or original intrinsic stats. Active slot44 selectors1/3/4/5/6
call independent HUD children after the direct write. Native widget state can
refresh4A1CF0/49B850. Those child effects remain OPEN.

## Family1: world scalars and later live rereads

Complete4D6DD0..4D7083 admits only body4==45. It uses the same world ECX rather
than the PET2 panel. No metadata/key/count guard occurs. Selectors21..32 use
the12-target table4D7084. The core mask/insert operands are:

| S | World DWORD | Replaced mask | Incoming bits |
|---|---|---|---|
|21/22/23/24|44|0000007F/00003F80/001FC000/0FE00000|V low7 shifted0/7/14/21|
|25|44|10000000|V low1 shifted28|
|26|4C|03FC0000|V low8 shifted18|
|27/28|48/4C|0003FFFF|V low18|
|29|48|FFFC0000|V low14 shifted18|
|32|44|C0000000|V low2 shifted30|

Selectors30/31 and out-of-range selectors have no direct core write but can
refresh4D5970 under the original widget guard. Selector32 separately calls
4D53F0. Neither child nor scalar names establish an authoritative entity/rule.

21/22/23/24/28 first compare the old field lowBYTE with incoming body0 unsigned
using complete4D6DB0. The marker is00FF0000 for old<new,000000FF otherwise.
For28 the comparison sees old low8 even though the core update replaces18 bits.
They write distinct marker DWORDs and flags, call4D7E40 ->opaque507150, call
declared winmm!timeGetTime, then reread current scalar and signed world BYTE8
to synchronize inventory. The API was only identified from PE imports.

| S | Live scalar read | Destination relative to24-byte row |
|---|---|---|
|21/22/23/24|world44 bits0..6/7..13/14..20/21..27|BYTE10/11/12/13, full BYTE write|
|28|world4C low18|DWORD0C, full DWORD write and high14 cleared|

The actual row index is signed context BYTE8, not wire slot45. Opaque child
effects have not been excluded, so the later inventory value/index cannot be
predicted from incoming V. The first unsealed implementation draft did that;
root corrected it before independent review/sealing/commit. Final source
exposes only the required live reread descriptors, without a supplied-state
wrapper, inventory value, mutation or fabricated success. Markers/flags/clock/
control/UI effects remain explicit additional obligations.

## Family3 address correction and source boundaries

Native arithmetic58EC*24=85620. Family3 S2 affects inventory row14h DWORD
bits8..14, not row0/count. Family0 S31 and family2 S2 share that property area
with different widths/masks; similarity does not authorize merging their
rules. Full20-byte instance metadata starts at inventory row+4, so row14h
corresponds to metadata10h. The current326 source document is corrected;
old sealed326 evidence and initial erroneous wording remain immutable. An
independent correction package retains exact native address instructions.

All new views are read-only. The earlier family3 double-write and conditional
metadata guards remain intact. Native32 masks/WORD/BYTE widths are retained;
this does not establish the owner's64-bit wire/object/display extension or
native99 quantity mutation, and native levels remain unchanged.

## Custody and round accounting

Both full inputs are hashed149c/5fc references. Family0/2 package retains6
cuts,965codeB/126dataB, including known guards;19 members/38387B, seal
410319ee1b2db1a53e275dccdecea2352be5931a27b2e07a4238ae8b04fbeceb.
Family1 retains10cuts842codeB/72dataB, including prior32690codeB/24dataB;
27 members/49083B, seal3212be8ee222c7b521e0566ffbebb5b72f57d60a107396ef70e21aa8987e6719.
Family3 correction retains4 members/4493B, seal
9fa79a412d8a6754317c0c2eb3795f5260eb07b45993aeaa462d591dce58cedc.
All three exclusive packages are under
C:/Users/risei/.codex/artifact-archives/god2-server/20261012;
no full-image copy, retired input or game SQL reader was used. Mechanical
complete functions are not global byte novelty or whole-game coverage.

Existing E5 independent format class remains one opcode: counts unchanged.
TW C2S156 candidates/world74=partial50/control11/unconnected13, S2C252,
independent10/unclassified116/reply48/push11/gated4; CN C2S156/S2Cphase280/
length253; mixed282/groups26/pending10/CUSTOM135. New opcode/phase/complete
route increments0; denominator/TW completion/whole completion null.

PHASE1 source/hash/PE/Capstone and unique static accounting only: no build,
compiler/test/native/runtime/VM/emulator/resource codec, game DB/SQL, migration,
activation, deployment or client edit. Full TW/CN/web/shared tables/common64/
coin99999999999/stack99/native levels and saves/auth/chat/IME/portraits/native
fonts/text conversion remain active requirements. True E5 issuer and all
affected-state rules/storage/replies/recovery, D6 previous-instance history and
debit, actual secondary parent phase and the full route denominator stay OPEN.
