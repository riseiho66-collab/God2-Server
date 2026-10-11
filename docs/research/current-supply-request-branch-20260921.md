# Native supply request branch correction

Image SHA256 149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763.
Fresh disassembly and execution of original963C0, lookup59A60 and append132E0;
no game-code substitutions. Offline synthetic UI, inventory and definition
records, not an actual client session or recovered full MED02 initialization.

The previous DiagnosticSupplyService test sends synthetic25 with ID3107. It
proves transaction wiring but NOT a valid native potion request. Do not activate
that Application route. Its Lua and repository layers remain independently useful.

963C0 scans owned-looking client slots29 down to0 by positive signed count and
item low word. It calls59A60 for the definition pointer. IDs divided by100 equal
53 or55 directly call96350 and append25. Other IDs examine definition+11A bit4:

- Missing definition or clear bit: appends26, six payload bytes. Target word is
  copied from the object pointed at UI+8688C; then item word, resolved slot byte,
  and one uninitialized local byte. Target semantic meaning remains unqualified.
- Set bit: calls96550. With its two selected indices negative (fixture), appends
  28 with item word, slot byte, and explicit1; sets UI+85608 to1. Other selected
  indices can gate the request. This does not prove the required server response.

Tests vary definition flags None/0/1/2/8 and three stack canaries. ID3107 emits
263412230c1dXX with target1234 and slot29; XX exactly tracks canary0/A5/FF.
Flags4/5/FF emit28230c0001 and set pending. IDs5301/5501 still emit25 with flag4.
Stack returns balanced; current image hash checked on every native instance.
All three tests in test_current_supply_request_branch.py pass.

Next: load real MED02 row through its original loader and establish definition
11A flags for3107. Qualify target selection and response/pending clearing before
binding26/28 to supply mutation. Do not interpret residual stack bytes as count,
do not infer catalog flag bit placement from English field names, and do not
claim offline synthetic branches establish native current-session acceptance.

## Real MED02 source follow-up

NativeItemMetadata now accepts the exact MED02 section name while resolving its
original first-three-byte tag MED (selector4). An initial MED section attempt
failed closed because that exact source section does not exist; it was corrected
to MED02, not satisfied by substituting rows. Other section selectors unchanged.

All100 current MED02 records execute original59420 parser,59A20 registration,
59A60 lookup and9B720 resource selection under existing code/write guards. Each
result's bytes11A/11B are checked against original source columns14..25. Native
produced record bytes are then copied to a separate request-test VM and original
963C0/59A60/132E0 runs against them. This is explicitly a two-VM byte handoff,
not continuous live loader-to-UI execution. Synthetic slot0/target1234 and stack
canaryA5 remain test inputs. All100 requests match the actual loaded flag branch;
none uses25.

Specifically3107 is source line6360, selector4, flagsFB01: bit04 is clear, and
the native caller emits26 with target1234, item3107, slot0 and residualA5.
This resolves the prior missing-definition uncertainty for its loaded branch.
It does not identify the target word's gameplay identity or prove server effect.

Four supply-branch tests pass (9.884s); existing seven metadata tests also pass
(14.026s), including code mutation rejection, retained-record guards, RomMaps
and EGG/SPP parsing. Next: implement a lossless26 codec, validate target ownership
from live world state, replace the synthetic25 supply admission, and qualify
real client request/reply behavior. No Application route activated by this work.

## Target identity producer-to-reader

The same request-test VM now executes original68629..68636 before963C0: ECX
contains an explicit world identity word, EBP the actor object. Original code
masks ECX with3FFF and stores its DWORD at actor+0. UI+8688C is an explicit
binding to that actor in this fixture. The actual26 caller then reads the stored
low WORD, not the earlier BEEF canary. Twelve combinations of IDs1/217/1234/3FFF
and upper bits0/4000/FFFFC000 preserve the expected target. Real loaded3107
metadata is used. All five branch tests pass in12.175s.

This links the bounded native actor-ID writer to the item request reader, not
the full2A parser, UI pointer installation or live session. Existing lab world
entry maps the owned character ID to local ID only within1..16383; future
Application admission must use that session mapping, not a client-supplied or
truncated database ID. DiagnosticSupplyService rejects zero/out-of-range trusted
target policies. It still cannot prove caller session ownership by itself.

## C2S28 structural server admission (2026-09-25)

`RecoveredSelectionItemRequest` now models the executed RVA96550 output as
`28 item_lo item_hi slot 01`. `RecoveredWorldRecords` parses it as its own typed
record within the bounded world frame and rejects incomplete records and other
last-byte modes. The C++ world-record and service tests pass. The initial
differential test used synthetic flag-4 definitions; the 2026-09-25 follow-up
replaced that input with actual current catalog rows. `RecoveredWorldService`
now has a separate optional C2S28 callback. A single request with optional
ticks may reach it in world state; duplicate requests, mixing with C2S26,
movement or combat, and battle-state use reject before callback. The default
Application supplies no C2S28 callback, so no response, item use, or save
mutation was enabled. The targeted C2S26 supply callback remains distinct.

All 100 current MED02 definitions were rechecked: their byte at +11A is one of
0x40, 0x5B, 0xC0, 0xDB, 0xE0, 0xFB, and none sets bit 0x04. This finding applies
only to MED02, not the other current item sections. Original RVA59420 parsed
the first and last real rows of EGG, SPP, WPN, EQU, TWP and TEQ; their flag
bytes are 0xE4 or 0xF4. Original RVA963C0/96550 then emitted C2S28 for each,
with actual source item ID, chosen fixture slot and final 01. For example:
EGG 9301 -> `28 55 24 00 01`, WPN 1 -> `28 01 00 00 01`, and EQU 1001 ->
`28 E9 03 00 01`. These 12 original-code outputs pass the formal C++ world
decoder as a parser batch; truncation or changing the final byte rejects.
The UI inventory and slot are still offline fixtures, not a live click/socket.
SKB and MED02 boundary samples emit C2S26. This corrects the overly narrow
MED02-only interpretation from the first pass.

The exact current `gamedata.csvZ` source (raw SHA256
`70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731`)
has 4,136 rows in the nine qualified item sections. Source flag column 16,
which matches parsed record +11A bit 0x04 in the native boundary samples, is set
for all 2,668 EGG/SPP/WPN/EQU/TWP/TEQ rows and none of the 1,468
MIS/SKB/MED02 rows. Those whole-section counts are source-column coverage, not
4,136 executed request traces or evidence that all items can be owned/used.

The same pinned image has a possible inventory-response lead: S2C3B dispatch
RVA6A031 calls 98DD0. `current_selection_pending.py` executes that original
dispatch and store to 98E2D, then continues in the same VM to the pending gate
with real native-loaded EGG9301, WPN1 and EQU1001 definitions in separate runs,
a synthetic slot-30 instance and explicit UI mode 1. Original 59A60 looks up
each definition. With pending 0,
98F1E reads the field and the path reaches 98F82, skipping the message. With
pending 1, the same path reaches the call at 98F33 with message ID 0x29D and
receiver UI pointer; 98F38, directly after that call, contains the verified
instruction that clears UI+85608. Both runs write one to the slot count and
leave the pending field unchanged *before* the message call. The original
44E140 message renderer is intentionally not executed, so its return and the
actual pending clear are not claimed. Six native branch runs across the three
categories, two focused tests and a CTest gate pass.

This supports S2C3B as a concrete response candidate, but no same-socket C2S28
to S2C3B exchange or equip/hatch rule has been observed. Next qualify the
original message callback and the inventory transition from an actual item
use on our isolated server before enabling a gameplay handler. Parsing and
branch reachability are only parts of packet connection.

Focused Release build: `god2-server` and `recovered-world-service` succeeded.
CTest `recovered_world_service`, `recovered_world_records`,
`current_world_records` and `recovered_server_routes` passed 4/4. The persistent
server executable was not replaced or restarted; these are source/test results,
not live C2S28 item-use acceptance.
