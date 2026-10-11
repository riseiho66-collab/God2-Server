# Private desktop original-client playtest (2026-09-23)

The current launcher-built client SHA256
`ae997bbe726afaaee3a02ff9b718eff03f3d726002bc6aa36ce66a1964241f7f`
was started by `God2PrivateDesktop` on a separate Windows desktop. The
runner's unconditional argument quoting originally caused the client's raw
command-line parser to return two arguments and exit before graphics. The
runner now quotes only arguments that need it. CDB then observed startup
parse count 4, graphics success 1, and WinSock startup. The private desktop
observer captured a rendered main menu without switching the owner's input
desktop. Holding a targeted `WM_LBUTTONDOWN` for 300 ms advanced the menu;
immediately posting down/up did not.

The deployed client has its server port embedded in `.w10fix`: passing 2598
on its command line still connected to 2592. A disposable, SHA-pinned copy
changed exactly one `.w10fix` immediate from 2592 to 2598. CDB verified the
loopback `connect` sockaddr bytes `02 00 0a 26 7f 00 00 01` before any actual
connection. The deployed client remained unchanged. The isolated server used
port 2598 and a separate SQLite database, while the player's persistent
service remained on 2592. The disposable client was deleted after testing.

Private-window automation logged in with synthetic test credentials, selected
the server and channel, created a female character, entered the town, and
performed three mouse-driven movements. Screenshots and commands are in
`artifacts/playtests/private-game-2598-20260923-01/client-existing` and
`client-new-path`. The first character reached saved position (58,60),
revision 6. A second fresh character reached the same saved position and
revision. A third fresh account also created, entered town, and moved.

The initial slow post-creation selection failed with the client's
"selection network timeout" dialog. The server recorded `Post-selection next
C2S contract unknown` on the independent character connection. Repeating
creation but waiting without selecting reproduced the cause: after five
seconds the original client sent `05 00 2D 2D 22` (logical `30 00`) while
the session was still awaiting character selection. This is the same
five-second periodic tick proven by the native client test in
`docs/research/current-periodic-tick-20260919.md`. The earlier recovered
session accepted it only during world initialization and gameplay.

`src/net/Session.cpp` now validates that exact decoded idle tick before
character selection, including fragmented and coalesced TCP reads. It sends
no fabricated response and still rejects malformed ticks or multiple
character actions. `tests/test_session_state.cpp` covers partial ticks,
two ticks coalesced with selection, a bad checksum and a different opcode;
the full `session_state` suite passed. The original client was then held at
the post-creation character screen long enough to send multiple ticks. The
server logged each accepted tick; the same connection subsequently selected
character 5, accepted the world initializer, rendered town, and committed a
movement to (61,62), revision 2. Evidence is in
`artifacts/playtests/private-game-2598-20260923-01/client-afterfix-slow`
and `stdout-afterfix.log`.

The production server was rebuilt with this fix and restarted on 2592 with
the original persistent SQLite database. Its deployed Release executable
SHA256 is `adb09e534f7a8e975dbf390e795727591c8096d420068ffedd9a42294a52e05f`.
At the final check, PID 5344 listened on 2592, SQLite `quick_check` returned
`ok`, and a synthetic loopback connection received the 19-byte handshake.
The diagnostic battle feature stayed off in persistent configuration.

## Original-client NPC flow on the private desktop

The direct original-client test then reached the two diagnostic town guides.
The first guide (target 1606) opened a seven-page dialogue, but confirmation
initially raised `Incomplete quest catalog` and did not save progress. The
private SQLite test database had zero `native_quest_descriptions`; the
persistent server database already had the complete 2014-row catalog. With
the private server stopped, `python -m tools.strike_lab.import_native_quests`
verified the pinned client `Mission_data` hashes, backed up the private
database, and imported all 418 missions and 2014 descriptions. This preserved
the quest provenance check instead of bypassing it.

With the private server restarted, the original client clicked guide 1606,
turned all seven pages, and confirmed stage 1. It then clicked guide 1607,
turned five pages, and confirmed stage 2. It returned to 1606, turned seven
pages, and confirmed stage 3. The server logged each accepted NPC request and
each confirmed stage. SQLite recorded stage 3, revision 3, and exactly one
item 5569 in the diagnostic inventory; `PRAGMA quick_check` returned `ok`.
After client restart and login, the server logged journal restoration at
stage 3, revision 3; the character rendered in town and the reward row stayed
at quantity 1. Captures, click responses, and server logs are under
`artifacts/playtests/private-game-2598-20260923-01/client-npc-retry`,
`client-npc-relogin`, and `stdout-npc-retry.log`.

The private client was launched directly, so some title/map and NPC dialogue
text appears garbled in captures; this run is not language acceptance evidence.
At this NPC test stage, natural doorway transition, battle, and the Win10/11
language path through Locale Emulator had not been checked.

## Physical doorway test and pending context repair

The same private desktop test clicked the town ground to walk character 4
from (113,70) to the source-linked entrance (86,70). The server committed
CUSTOM-0025 and the original client visibly rendered indoor scene 15 at
(16,19), but the session immediately disconnected. The server's pending
receipt had been limited to `1C 01 00 00 00`, which came from an earlier
native-function test. A bounded private-server diagnostic captured the
physical client's exact pending `1C 04 00 01 00` (caller word 4, config
word 1). Both are five-byte logical records; the added acceptance applies
only to an owned pending doorway transfer. Other context values and use
without `door_routes` remain rejected by the new `diagnostic_door` test.

With the patched server and a cloned isolated test database, visible clicks
walked through the town entrance and the indoor exit on the same connection.
The first isolated retry completed one full roundtrip, then disconnected
immediately after committing its second exit, before a pending receipt could
be logged; that run is retained as failed evidence. A fresh private run with
pending-batch telemetry completed three consecutive visible roundtrips on
one connection. All six receipts were exactly `04 00 01 00`, one context
record per batch, and all six were accepted. Final save was town2/4/86,71,
revision101; quest stage3/revision3 and item5569/count1 were unchanged,
and SQLite `quick_check` returned `ok`. The actual client process remained
connected after the third exit. Evidence is in `door-retry2` and
`door-retry3` under the private-game playtest directory. The exact rejected
packet for the `door-retry2` second exit was not captured in that run; later
private tests below identify two normal-client doorway packet patterns that
the earlier server rejected.

The Release server with the narrow context change was started on 2592 as
PID24724 after verifying no established player sessions. Focused CTests
`diagnostic_door`, `config`, `recovered_movement_service`, and
`recovered_quest_sync` passed; its binary SHA256 is
`2631f4a495973539e2de4aa9b12145d0f86b40cef0b2193bcab6c92552fea5f7`.
The persistent SQLite catalog contains2014 descriptions, `quick_check` is
`ok`, and the port2592 handshake is19 bytes. A second visible physical
player acceptance on the persistent service remains outstanding.

## Movement during doorway handoff

Further private-desktop testing reproduced a doorway disconnect with a long
ground click from town (86,71). The client stepped onto the entrance (86,70)
and queued another old-scene step before the next five-second tick. The
previous server withheld S2C61 until that tick and rejected the extra move.
`door-stress` contains the failed click and `movement-reject` records the
rejected first movement. This is a client-driven timing defect, not a
quest-journal close request.

The doorway handler now returns the committed S2C5D movement ACK followed by
S2C61 in that order, in the same response. The next isolated original-client
run showed a second native variant: one logical client frame held both the
exact context receipt `1C 04 00 01 00` and the destination's first movement
to indoor (17,18), sequence1. Rejecting that two-record frame still closed
the session. The pending-transfer handler now accepts only an exact context
followed by one movement record, finishes the transfer/ring reset, and sends
that movement through the normal ownership, sequence and navigation gates.
Single-record context continues to work. `door-immediate2` contains the
rejected pair; `door-combined` contains the accepted pair.

In `door-combined`, two long-click entries reached indoor20,11, and both
subsequent visible walks returned to town86,71 on the same connection. The
first destination step was accepted on each entry, all four scene contexts
completed, and there were no world-policy rejections. Final SQLite save was
area2/scene4/86,71/revision143; quest stage3/revision3 and item5569/count1
were unchanged, with `quick_check=ok`. The private client and server were
stopped and the disposable port2598 EXE was removed after testing. The
captured structural context+movement frame is covered by
`recovered_world_records`; `diagnostic_door`, `recovered_movement_service`,
and `recovered_quest_sync` also passed.

The new Release server started on persistent port2592 after a
zero-established-session check. The final logging-label rebuild runs as
PID15244; its SHA256 is
`3a551cff343993a7fc439c24a56f13e5c178000dc6c95f1414ee848b2af82f28`.
The persistent database still
has2014 descriptions, `quick_check=ok`, and a19-byte handshake. The doorway
remains labeled CUSTOM-0025 because destination pairing and trigger policy
are not recovered official server rules. The private direct client run does
not certify Win10/11 language rendering or combat playability.
