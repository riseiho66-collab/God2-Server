# Current-client teleport UI contract — 2026-09-26

## Evidence identity and limits

`God2.exe` SHA256 `6BF75EF8AC1E0F6B2240800FF841D205788BD1B6512149584B5386B10F431E98`, image base `0x00400000`. This replaces stale September 20 identity assumptions for the spans discussed here. Work is read-only against the current PE and Ghidra export. No game/client process, production modification, packet transmission, or live acceptance occurred.

Reconstruction artifacts are in the separately organized client reconstruction folder, under `reconstructed/teleport-ui/`: `native-disassembly.txt`, `native-message-ids.json`, `native-localized-messages.json`, `teleport_ui.{hpp,cpp}`, `verify_native.py`, and its result `native-verification.json`. These C++ files are **new project source reconstructed from native behavior**, not the original full game source. Pseudocode and bounded native execution establish the qualified behavior below; renderer mocks do not establish full UI or own-server gameplay acceptance.

Current verification status: the C++20 Release library/probe build and exact instruction/resource extraction succeeded. The first native/C++ differential run was interrupted to honor the user's requested relocation; **no differential pass is claimed**. `native-verification-incomplete.json` preserves that status. The optimized rerun keeps a 3,000-instruction budget per vector and explicit code/stop allowlists, removing costly per-vector timeout watchdogs. Until that rerun completes, new UI branch claims below rest on the preserved current-EXE instructions and resource records; the separately completed earlier teleport producer tests retain their own scope.

## Fixed menu body and native state

The S2C logical dispatcher case `0x6D` invokes receiver `0x004F6360`. Receiver copies exactly seven DWORDs (28 bytes) into owner `+0x790EC`. Framing and dispatcher record-length checks remain a separate protocol layer.

| Body offset | Native use |
|---|---|
| 0..1 | Context WORD, echoed in selection and tested against `0x061E..0x0622` |
| 2..3 | SystemMessage ID; header lookup through resource `+0xB2C60`, count `+0xB2C64` |
| 4 | Low seven bits: destination count. High bit: row enable/cooldown presentation |
| 5 | Minute value substituted into regular-context ready/wait notice |
| 6 | Compared unsigned against 10 to choose free versus numeric price display |
| 7 | Not interpreted by the qualified routines |
| 8+4*i | Destination label/index byte, later copied to selected destination state |
| 9+4*i | Not interpreted by the qualified routines |
| 10+4*i..11+4*i | Little-endian displayed coin cost WORD |

Only **five complete entries** fit the copied body. The native loops do not enforce that limit. Context values are qualified as opaque echoed context tokens and a five-value discriminator; these instructions alone do not prove an item ID, NPC ID, position, ownership, or server action.

Receiver resets `+0x790E4=0`, computes page count `max(1,(count+9)/10)` into `+0x790E8`, calls `0x004F6B30`, and then resets the list selection through `0x0050D310(-1)`. The selected destination DWORD at `+0x790E0` is reset to `-1` inside the successful open path, rather than unconditionally by the receiver.

## Enable, presentation, and event path

`0x004F7090` checks that the dialog index at owner `+0x232E38` is nonnegative, absolute index is below count, and `absolute_index - page*10` is nonnegative. It does **not** enforce a relative row upper bound or the five-entry body bound. It writes label and price columns, then calls `0x0050CAA0(relative_row, enabled)` with `enabled=(flags&0x80)!=0`.

`0x0050CAA0` stores row enable state at list `+0x148+4*row` and chooses disabled coloring when zero. The actual row-event routine `0x0050D8A0` skips zero-state rows. Therefore clear high bit genuinely disables normal row selection; this is more than a guessed color meaning.

Teleport callback `0x004F6A40` invokes row-event processing and only calls `0x004F7160` for a nonnegative returned row with click bit 1. Button/control ID 3 invokes `0x004F72B0`. IDs 0/4 and cancellation bit 2 call `0x004F6A00` and close. `0x004F6A00` queues logical `0x86` with a four-byte payload; this is not a `0x99/0xA9` selection. IDs 1/2 navigate pages through `0x004F6AF0`.

`0x004F7160` computes selection index **clicked_row + page*6**, tests only `index<count`, stores the destination byte to `+0x790E0`, and chooses confirmation text. There is no lower-bound test and no enable-bit recheck in this routine. `0x004F72B0` likewise only checks signed selected DWORD `>0` before building a request. Consequently client enable state cannot replace server validation.

## Current localized text and precise meanings

Initializer `0x004F6450` loads ProgramMsg IDs from WORD table `0x0059A5F0`. Actual current `Data2/Patch/Comm/message.csvZ` rows, raw bytes, source offsets, and resource hash are preserved in `native-localized-messages.json`.

| Native role | Resource ID and current text |
|---|---|
| Label index 0 | ProgramMsg 9: empty text |
| Label indices 1..5 | ProgramMsg 15 葛城, 16 昆吾, 17 韋城, 18 南巢, 506 楓華鎮 |
| Numeric cost | ProgramMsg 14: `%d仙幣` |
| Free price | ProgramMsg 507: `免費` |
| High bit clear | ProgramMsg 509: `（注意：距離下次傳送還有 %d 分鐘，請稍候。）` |
| High bit set | ProgramMsg 510: `（注意：傳送後需等 %d 分鐘之後才能再次傳送喔。）` |
| Free confirmation | ProgramMsg 511: `您要到傳送 %s 這個地方嗎？` |
| Paid confirmation | ProgramMsg 19 `你要花費%d仙幣到` and 20 `%s 這個地點嗎？` |
| No selection | SystemMessage 280 (`0x118`): `請先選擇要傳送的地點。` |

`0x004F6DF0` gives special contexts `0x061E..0x0622` priority over the high-bit header branch. Their header combines the supplied SystemMessage ID with SystemMessage 518: `(注意：等級不到10級無法使用)`. Regular contexts combine the supplied message, SystemMessage 517 `10級以下可免費傳送。`, and the ready/wait minute notice.

The numeric comparison in row rendering is **level < 10**, while the resource wording says `10級以下`. At byte value 10 the native renderer shows a numeric price. Do not replace machine-code behavior with a prose interpretation. Special context confirmation always uses the paid two-line form, even if the row displayed free text because byte 6 is below 10; the menu/UI does not independently enforce level eligibility.

ProgramMsg 415 `此功能尚未開放` and 508 `時辰未到` are loaded into globals by initialization, but the qualified header/row/selection routines do not consume those pointers. Their presence does not establish a generic unavailable-menu switch.

## Paging, open, and close qualifications

`0x004F6DF0` iterates absolute indices from `page*10` **all the way to count**, with no ten-row stop. On the first page it clears rows up to row 9 only if the final loop index is below 10. Rendering and selection therefore disagree on later pages. `0x004F6AF0` decrements for direction 1, increments for every other direction, clamps to `[0,pages-1]`, and redraws only on change.

A defensible server adapter uses at most five entries, which keeps this menu on page zero and avoids reading beyond the received body. This bound is a **project-side safety qualification**, not a recovered native rejection. Label indices must be within the six-element label table; usable selectable entries should use 1..5, since index 0 has empty text and selected value zero is rejected by submission. Destination labels alone do not prove any map or coordinate.

Open routine `0x004F6B30` requires a nonnegative dialog index, dialog flag bit `0x10`, and no bit `0x08` on seven other valid dialog slots at owner offsets `0x232DDC`, `0x232DC8`, `0x232E26`, `0x232E16`, `0x232DAA`, `0x232DC0`, `0x232E28`. Only then does it close conflicting UI, open/activate the teleport dialog, set selection to `-1`, and refresh. Receipt therefore does not guarantee the dialog appears. Close `0x004F6410` invokes `0x00507BB0` only for a valid dialog whose flag contains `0x20`.

## Selection request and server response boundaries

The qualified producer `0x004F72B0`, reached from the teleport callback's submit button, queues:

`opcode (99 or A9), context_lo, context_hi, selected_low_byte, opaque_stack_tail`

It uses `0xA9` for contexts `0x061E..0x0622`, otherwise `0x99`. The final payload byte is not initialized by the producer's field stores; the preceding `PUSH ECX` leaves the owner's high address byte there. It is not a second destination byte or proven reserved zero. Existing `reconstructed/teleport/verify_native.py` independently qualifies this producer behavior. Submission then zeroes the 28-byte body and closes; it does not establish a successful authoritative teleport or validate the price.

The server may produce a **usable** S2C `0x6D` body once it has a qualified triggering route and authoritative destination/context/eligibility data: valid message ID, at most five valid entries, high bit set, and truthful display cost/minute/level fields. A **cooldown** body uses high bit clear and a truthful remaining minute value, so normal rows cannot be selected. An empty count clears displayed entries but retains native header semantics. Do not advertise generic unavailable state by fabricating a cooldown, special context, destination, price, or minute count. An already-qualified general system-message route can explain unavailable functionality without pretending it is a usable teleport menu; which response route applies remains an integration decision requiring evidence.

For incoming `0x99/0xA9`, validate the actor, outstanding offered context, selected entry membership, eligibility/cooldown, and authoritative state before mutation. The UI high bit is not authorization. No destination map/coordinates, payment rule, cooldown duration, or movement response is established by these display/producer functions.

## C2S `0x6D` caller qualification

Dispatcher `0x004961A0` passes logical `0x6D` to the one-byte-zero control producer `0x004157D0`. Current discovered callers include:

| Caller | Concrete trigger visible in current code |
|---|---|
| `0x00498DD0` | Incoming inventory/equipment record for slot 38..41, while `[owner+0x574C0]->+0x24 == 1` |
| `0x00498FD0` | Removal/update of slots 38..41 under the same state check |
| `0x004991E0` | Count reaches zero for slots 38..41 under the same state check |
| `0x004A6760` | UI case `0x24`, gated by `0x0050E7D0` |
| `0x00503AD0` | `0x0050E7D0` reports embedded object `+0xAA36488` state `+0x24 == 0`, then dispatches through embedded owner `+0xA7F2F6C` |
| `0x00501810` | Large UI routine with a saved nonzero state flag; its full semantic trigger remains unqualified |

S2C and C2S opcode numbers occupy separate direction-specific contracts. These callers establish the C2S producer and triggers, but **do not by themselves prove that every C2S `0x6D` should receive a teleport menu**. The outbound opcode must not be paired with the inbound same-number menu solely by numeric equality. Trace the corresponding control-state update consumer or own-server current-client exchange before promoting a universal `0x6D -> menu` handler.
