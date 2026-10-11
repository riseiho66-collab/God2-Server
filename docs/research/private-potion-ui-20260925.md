# Original-client potion UI gap (2026-09-25)

Scope: the disposable unpacked `God2-private-lab-2598.exe` (SHA256
`dff8e8ec2db96b666d14c5eb5d1d9d2ff6ad73dc24b8e6b5a39734e63f6c24cb`)
on a private Windows desktop, an independent port 2598 C++ server, and a SQLite
backup of the prepared diagnostic-supply fixture. The persistent port 2592
process and player save were not used. `tools/strike_lab/private_potion_ui.py`
records stages without switching the input desktop. The explicit backup source
and initial HP/MP/item count are in
`artifacts/playtests/private-potion-ui-20260925-08/fixture.json`.

Run 08 authenticated account 1, selected character 1, and received the world
initializer. The original client displayed the MED02 3107 item in inventory
slot 0; a read-only process-memory search found its exact 24-byte slot record.
The saved item remained 3107/count 3/revision 1, and resources remained
HP 52/120, MP 2/80/revision 11. A targeted double-click and self-target click
in earlier isolated runs, followed in run 08 by a drag toward the visible
shortcut row and F1, did not yield a C2S26 record or any database mutation.
The server received only periodic world ticks. These are failed UI-trigger
attempts, not evidence that the previously qualified C2S26 server route is
broken or that an ordinary human action also fails.

The original image SHA256
`149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`
has two direct RVA AE520 callsites: AB675 and AE3EA. AB650..AB68B checks
virtual keys 0x70..0x79 before calling AE520 with a shortcut index. AE270..
AE407 handles an action-row event; AE3EA also calls AE520. The live action
record bank at UI+A3D18, read after the synthetic drag, did not contain item
3107. This narrows the missing step to getting the original UI to assign or
activate the item shortcut. The targeted PostMessage mouse/key events may not
reproduce the client's actual mouse-capture or keyboard-state path. The exact
user input gesture and full item action callback remain unqualified.

Additional original-image trace: AE020, AEC99 and AEE47 call AF780, which
looks up the item definition, requires flag 0x10, and stores a kind-0 action
record in UI+A3D18. The AEC99 path checks a selected inventory slot at
UI+855F0, a nonnegative UI+232DC8 and a source-mode bit 0x20 before mapping
the inventory item into action slot BX-10. Run 09 tried a single item click
followed by an apparent action-slot click and F1 on the same private client;
again only ticks reached the server and the save was unchanged. This does not
identify a missing C2S26 parser.

Run 10 read UI fields after inventory opening, item click, apparent shortcut
drag, apparent shortcut click and posted F1. UI+855F0 and UI+A4158 were -1
after every completed action; action records never contained 3107. Because a
selection may only live during mouse hold, run 11 read those fields between
events. The original client set UI+855F0 to slot 0 on item mouse-down, kept it
at 0 through the drag, then returned it to -1 after button-up. The matching
source index at UI+232DC8 was 23 and its mode byte was 0x23, satisfying the
observed 0x20 source-bit gate in AEC20..AEC99. The client received the click
and selected the saved item; the destination did not become a shortcut record.
The state snapshots are in
`artifacts/playtests/private-potion-ui-20260925-11/ui-result.json`.

The only nonnegative UI+855F0 writers found in the bounded original-image
scan are RVA9AF12 and 9ED69; the latter stores the clicked slot on a button
event. RVA AD62E constructs the panel whose ID is saved at UI+232E54; the
world event dispatcher calls AE270 for that ID. Run 12 pressed three visible
buttons in the right-side inventory panel, and run 13 pressed three top-bar
icons. During and after each mouse hold, UI+A4158 remained -1 and the action
bank did not change. These specific positions did not reach the action-slot
handler. They do not exclude other positions, a different panel mode, or a
physical input sequence that PostMessage does not reproduce. Results are in
the run 12 and 13 `ui-result.json` files in the same playtests directory.

Earlier `artifacts/runs/native-supply-use-20260921-01` remains the stronger
same-socket packet and response proof: the original item producer sent C2S26
against the isolated server, which consumed two units and raised MP 2->52->80.
That probe invoked native client code by a diagnostic thunk; it did not
establish physical inventory UI use. Keep the two acceptance stages separate.

Next: locate the live UI+232E54 widget geometry and mode, then deliver a
physical inventory-to-action-slot gesture on the private desktop without
altering gameplay memory. Only after a real UI-to-C2S26 transaction
should the physical use path be marked accepted. No production source, config,
binary or persistent service changed in this experiment.

## 2026-09-26 native shortcut completion

The live widget ID 12 has a baseline 800x600 rectangle `(87,0)-(545,75)`.
Its visible button children 0-9 and shortcut children 10-19 share ten
`39x39` rectangles across the top row. The shortcut children have flag `0x84`
and were previously omitted by a diagnostic reader that selected only flag
bit 0. Original image RVA AD6AA..AD6D7 constructs children 10-19, and RVA
AE270..AE3EA dispatches their events. The first shortcut rectangle is
`(91,3)-(130,42)`.

Run 17 (`artifacts/playtests/private-potion-ui-20260926-17/ui-result.json`)
dragged slot 0 to the center of native child 10. Original-client memory
changed the first six-byte action record from `010001000000` to
`0000230c0000` (kind 0, item 3107). F1 then changed the isolated server DB
from item count 3 to 2 and MP 2/80 to 52/80. The run's post-use memory
reader failed because its slot pattern required count 3. This was a reader
error, not a failed transaction.

The reader now accepts slot counts 3, 2, or 1. Run 18 repeated the gesture
with a fresh isolated DB and completed all assertions: item 3107 count 3->2,
MP 2->52, client window still alive, and action record still assigned after
F1. See `artifacts/playtests/private-potion-ui-20260926-18/ui-result.json`.
This qualifies the original-client inventory-to-shortcut-to-C2S26-to-server
path for the private unpacked client build. It does not qualify all item
types, all targets, or the current production client binary; the private
runner uses the separately pinned port-2598 unpacked test image. The live
port-2592 server, user desktop, production DB, and client files were untouched.

## 2026-09-26 current deployed EXE recheck

The owner's current `God2.exe` is SHA256
`6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98`
(3,202,560 bytes). It differs substantially from the earlier private test
image. A hash-pinned disposable copy changed only file offset `0x114E9` from
`0x20` to `0x26`, changing the original `push 2592` startup TCP port immediate
to `push 2598`; all other bytes remained identical. This isolated the current
client from the owner's running port-2592 service without altering `God2.exe`.

The copy did not create a game window when launched through the older Locale
Emulator. A direct launch on the private desktop did create `XianJieWndClass`.
Run 20 therefore launched it directly against a fresh independent port-2598
server/SQLite clone. The same physical inventory drag to native shortcut child
10 followed by F1 passed: item 3107 count 3->2, MP 2/80->52/80, action record
kind 0/item 3107 retained, game window alive, and SQLite `quick_check=ok`. See
`artifacts/playtests/private-potion-ui-20260926-20/ui-result.json` and
`tools/strike_lab/private_current_client_variant.py`. This extends the
specific C2S26 potion path acceptance to the currently deployed EXE's code,
with only the one-byte private port redirect. It does not certify all item
types, targets, or the complete game protocol.

## HP potion `3101` socket follow-up, 2026-09-26

The same `C2S 26` item route now has an automated isolated own-server TCP
regression for item `3101`, using the qualified six-byte target/item/slot/tail
shape. It starts with owned slot 0 holding three items and saved resources
HP 20/120, MP 2/80. The server emits an inventory update retaining item 3101
with count 2 and a resource update HP 120/120, MP 2/80. SQLite revisions both
advance from 1 to 2. A second valid request at full HP has no reply and does
not consume another item; a subsequent movement ACK succeeds. Existing battle
→ MP potion → second battle regression also passes. The supply, Lua and socket
CTests pass 3/3. This qualifies an authoritative **socket route and saved
state**, not the current client's physical HP-potion gesture.

`artifacts/playtests/private-hp-potion-20260926-01` is a separate SQLite
backup prepared for that physical gesture. The execution environment's
automatic review rejected the private-desktop launch command before it ran and
also rejected removal of the disposable port-2598 client copy. No private
server listened on 2598, the clone retained its initial HP/item values, and
no `God2-current-lab-2598.exe` process was running when checked. The copy
remains at `../God2/God2-current-lab-2598.exe`; it is not the deployed client.
No original-client HP-potion acceptance is claimed. The port-2592 service and
player database were unchanged.
