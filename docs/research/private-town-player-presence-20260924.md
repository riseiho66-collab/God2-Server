# Isolated town player presence and door handoff (2026-09-24)

`development.diagnostic_town.player_visibility` enables authenticated player
presence in the existing isolated town diagnostic. It is default off and
requires the loopback dual-connection, source-consensus, spawn-guide and door
route gates. Private client and socket trials did not touch the port 2592
service or its SQLite save.

The original client in a private Windows desktop entered town on the isolated
port 2598. A second authenticated peer received its `0x6F` appearance. A
Traditional `0x2F` common-chat packet from that peer was converted into
Simplified Chinese for the original client, and the peer's `0x2E` movement
produced `0x5D` ACK and `0x5E` player movement. The original client itself
walked into the town-to-indoor door; the service logged a committed 4-to-15
transfer and accepted its scene-context receipt. That private server's
15-minute run ended immediately after the receipt, so the visual session alone
did not establish destination peer reappearance.

`test_town_player_visibility_server.py` completes the cross-scene check with
three authenticated native-protocol sockets and a disposable SQLite clone of a
saved, quest-complete character before its first battle.
It uses the original executable's recovered movement and world-ready builders.
The test verifies town `0x6F` join, `0x5E` movement, `0x73` leave, indoor
`0x6F` rejoin, scene-isolated `0x5C` chat, and saved scene 2/15 position
16/19. The same peer then moves to the qualified battle tile: the observer
gets eight `0x5E` updates, `0x73` at battle entry, and `0x6F` after terminal
release and the next world tick. Settlement count is one and SQLite
`quick_check=ok`. It passed against the new Release binary.
The socket test is not original-client pixel evidence.

The scenario was subsequently extended, using the same isolated sockets and
the already deployed binary, through map item `0x25/0x3F`, battle settlement,
indoor-to-town door transfer, a second map-panel request, town chat, disconnect,
cold login and another saved movement. The observer receives matching `0x73`
leave and `0x6F` join records at each scene boundary. The settled quest fight
does not restart on reconnect. The final save is scene 2/4 at 86,72 with one
battle settlement and SQLite `quick_check=ok`. The extended test passed.

The test exposed an unrelated indoor bootstrap failure: a character with no
saved quest journal generated an empty logical guide frame, which closed the
game connection. The handler now treats the empty guide as a valid zero-byte
reply and still publishes scene presence. The test begins with exactly that
indoor no-journal case, so the regression is covered.

The updated binary is `build-town-visibility/Release/god2-server.exe`, SHA256
`5b66be3149564811175db580e4b7e8bbd04639e937bd47fa36ccaf1e8635127b`.
`god2-tests.exe config` and `recovered-visibility.exe` passed. Door routing,
NPCs, quest journal, battle and inventory remain diagnostic implementations;
the complete client packet inventory is not yet connected.

After the isolated checks, port 2592 had no established game sessions. A
SQLite backup was made under `artifacts/releases/town-presence-20260924/staging/`.
The new binary and config were started once against that backup on port 2598
and shut down cleanly. The old port 2592 process was then stopped and the new
binary started with `artifacts/releases/town-presence-20260924/server-config.json`.
Port 2592 is listening under that binary (PID 16588 at deployment), and the
live SQLite file passed `quick_check`. The old binary and configuration remain
available for rollback; the live database was not reset.
