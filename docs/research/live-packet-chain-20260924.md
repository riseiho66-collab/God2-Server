# Original-client packet chain: town door, quest battle, return (2026-09-24)

The owner set the working priority: connect each packet actually produced by
the original client to an authoritative server operation, then fill the system
gap exposed by that operation. A parsed opcode, emitted reply, and playable
result are separate claims. No overall packet-completion percentage is implied.

## Same-connection acceptance

`artifacts/playtests/private-chain-endtoend-20260924-01/` is an isolated copy
of the save that had already opened item 5569's map through the original
client's inventory UI. The clone started in town (2/4/88/71) at quest stage 3
with one item 5569 and zero battle settlements. No position was edited in this
clone. The original client ran through Locale Emulator on a private Windows
desktop against loopback port 2598. Targeted window messages drove its real UI
handlers without switching the user's input desktop. The private server used
the same Release executable and the same `development` configuration as the
running port 2592 service; database, log and port were isolated.

One world session (`session_id=2`) moved from town into scene 15, walked to
the quest trigger, entered battle, issued a basic attack, received and displayed
the result, returned to the room, walked out to town and moved again. The
ordered server events are in `verification.json` and the frozen `server.log`:

| Boundary | Original client / server evidence | Result |
| --- | --- | --- |
| Town movement and entrance | C2S `2E` movement, S2C movement ACK and scene transfer; door committed scene 4 → 15, then C2S `1C` context | Indoor rendered, same session |
| Quest battle entry | Saved stage 3, item 5569, room position (18,12), C2S `30` tick; S2C `82` entry followed by C2S `36` notification | Original battle view rendered |
| Player attack | C2S `35` initial control (variant 7), basic attack (variant 6), later control receipt (variant 7) | One win and visible result |
| Battle release | C2S `1C` payload `04 00 01 00`; post-battle context accepted | Room rendered again |
| Return to town | C2S `2E` movement, scene 15 → 4 transfer and context plus first destination step in one batch | Town rendered, movement saved to (87,75) |

The server log has one battle transition, no world-policy rejection and no
`session_id=2` disconnect. SQLite has one settlement (win, XP 0), final
position (2/4/87/75/revision 123), quest stage 3, item 5569/count 1, and
`PRAGMA quick_check=ok`. `verify.py` asserts event order, data, unique
settlement and production development-config equivalence. It passed. The
server binary SHA-256 is
`9cecc537ee90d16d574349794374f15a942e287d1a4ce0050f98af39db109f40`.

Screenshots: `door5/` (interior), `battle-watch/` (result), `post-battle/`
(room restored), `exit-door/` (town) and `town-walk/` (continued movement).
The earlier inventory map UI run is recorded in
`docs/research/private-map-item-ui-20260923.md`; the database was cloned
*after* that run, so map use and this same-connection battle are separate
original-client sessions linked by a saved-state copy.

## What this connects and what remains

This is one CUSTOM quest-gated tutorial fight, not a recovered general
encounter rule. Its enemy, one-round balance and XP 0 are explicit diagnostic
policies. The client demonstrated its `35` command route and the server's
single settlement/return path, but this does not cover ordinary repeatable
monsters, loot, broad skills, every NPC/quest, or all possible client opcodes.
The `36` notification was observed immediately at entry and periodically
afterward; it has no combat effect. A later controlled current-client run
([command-window evidence](current-battle-command-window-20260926.md)) shows
the separate `35/action2` record moving from about one second to 31 seconds
when only the S2C82 initial window byte changes. In that no-input scenario,
`action2` is the client's timeout/automatic-defense notice in this state.
The later [timeout/receipt playtest](current-action2-timeout-20260926.md)
connects two repeated isolated no-input turns through a monster response,
client `35/0B` receipt and next grant. Other action2 contexts and native
defense mitigation remain unqualified.

Next packet-driven work should take one original-client action at a time:

1. Discover and connect a repeatable ordinary encounter trigger, then verify
   monster spawn, attack, result, resources, experience and return with the
   original client. If native rules remain unavailable, label a balanced
   server policy CUSTOM and keep it distinct from this tutorial fight.
2. For each other NPC, inventory action, quest and skill, capture the client
   producer record, implement ownership/state checks and reply, then perform
   one live client transaction plus durable-state verification.
3. Keep the route ledger keyed by opcode **and state/action**, since `35`
   contains multiple battle commands and `1C` occurs at several scene/battle
   boundaries. Do not count a codec or timer acceptance as a playable system.

The private test server/client were stopped after the frozen evidence. The
persistent port 2592 server remained listening with the same binary and
configuration.

## C2S `26` potion shortcut acceptance — 2026-09-26

The private original-client run 18 dragged inventory slot 0's item 3107 onto
the native first shortcut child and pressed F1. Its action record became kind 0,
item 3107. Against the isolated server on port 2598, authoritative SQLite state
changed item count 3->2 and MP 2->52/80 while the client stayed alive. This
connects the original physical UI gesture, client item producer, server item
route, and persisted resource/inventory response for this potion. The earlier
same-socket diagnostic producer run independently identified C2S `26` as the
wire opcode. Evidence and remaining build/target limits are in
`docs/research/private-potion-ui-20260925.md` and
`artifacts/playtests/private-potion-ui-20260926-18/ui-result.json`. This is one
item path, not a general inventory-completion percentage.

Run 20 repeated the physical path using a one-byte port-redirected copy of the
current deployed `God2.exe` (SHA256
`6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98`).
It again passed item 3->2 and MP 2->52 with the game window alive and SQLite
`quick_check=ok`; the original file stayed hash-identical. The current build
works on the private desktop when launched directly, without the older Locale
Emulator. Evidence is in
`artifacts/playtests/private-potion-ui-20260926-20/ui-result.json`.

## C2S `25` map-item UI recheck — 2026-09-26

The current deployed client code, in a one-byte port-isolated temporary copy,
double-clicked saved item 5569 in slot 0. The current server's typed C2S25
route reached `DIAGNOSTIC_TOWN_MAP_CANDIDATE` for the bound stage-3 town
character. Item and position remained unchanged, as the documented
CUSTOM-0023 map policy requires; the client window stayed alive and the
isolated SQLite database passed `quick_check`. The current-run packet and
saved-state evidence is in
`artifacts/playtests/private-map-item-current-20260926-02/`. This rechecks
one map item, not every C2S25 item operation or current-build map rendering.

## Next-packet diagnosis added afterward

`RecoveredWorldRecords` now optionally reports the logical offset and opcode
of an unsupported record. `Session` logs those two structural values only
when rejecting the frame. This catches an unknown second record after a valid
first record; it never treats malformed known records or broken envelopes as
unsupported opcodes, and logs no chat text or packet body. The route still
fails closed. This is discovery support for the next client action, not a new
gameplay packet acceptance.

`recovered_world_records` and `session_state` CTests passed 2/2. After
confirming zero established connections, the persistent port 2592 executable
was backed up and updated to SHA-256
`6ddf26332e5b7c93d876a77728a4328c5022e3c43d9d8eb501295c5f1d4ae9bf`.
The restarted process returned the 19-byte handshake and its SQLite
`quick_check` was `ok`. The physical playtest above ran the preceding binary,
retained as `god2-server-before-unsupported-record.exe` in its artifact.

## C2S `9A` mixed-batch integration — 2026-09-24

The native world-record decoder already recognizes the client's `0x9A`
`ClientDiagnostic` record. The application route previously passed the entire
record list into gameplay routing, so a frame containing this diagnostic plus a
valid movement/chat record failed as an unsupported mixed batch. The application
now consumes diagnostic records without a gameplay effect and routes the
remaining records in their original order. A diagnostic-only frame returns an
empty response. No diagnostic text or body is logged or surfaced as game state.

Evidence: `recovered-world-records.exe` and `recovered-world-service.exe` both
pass in the active `build-monster-trace` Release tree. The test covers mixed
`9A` + movement + tick decoding/filtering, diagnostic-only no-op behavior and
normal movement routing. `god2-server.exe` was rebuilt from the same tree and
restarted after confirming no established client connections. The backup is
`artifacts/releases/god2-server-before-c2s9a-filter-20260924.exe` (SHA-256
`946B1E0630E2341ACBBB950664FC0BC05E3550422159FF57D0CEBF562FEF7667`). The
active binary is SHA-256
`354069713D24A4655732700487AAE8037C23F7209905C40F15092A96771FD049`.
Post-restart checks received the 19-byte seed handshake on loopback port 2592,
confirmed the character listener on loopback port 59789, and ran SQLite
`PRAGMA quick_check=ok`. The actual game client has not yet been rerun against
this 9A route, so original-client acceptance for the mixed case remains pending.

### C2S `9A` beside stateful movement and tick on the same TCP session

The own-server loopback regression now composes a structurally valid native
`9A` diagnostic record, a real-format `2E` movement request and `30 00` tick
inside one integrity-checked world frame during the existing three-session
town/indoor/battle lifecycle. The client peer receives the normal movement ACK;
the observer sees the corresponding `5E` update, and the later saved movement
and scene transitions still complete. The early-transfer regression also
continues to pass. Both tests pass against `build-town-visibility` Release.

This advances `9A` from codec/filter-only evidence to the actual Session and
Application TCP route with an authoritative movement side effect. The request
bytes use the recovered producer contract, but this mixed `9A`+`2E` combination
is an own-server protocol regression, not a freshly captured original-client
frame. No C++ runtime code or persistent service binary changed in this
increment; original-client mixed-batch acceptance remains open.
