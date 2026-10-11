# Dual-client presence check and early-transfer repair (2026-09-24)

## Reproduced failure
The deployed log `artifacts/releases/town-chat-welcome-20260924/server.log`
records session 11 entering the world at 20:14:16, moving from indoor scene 15
to town scene 4 at 20:14:19, then being disconnected on a periodic tick while
the destination context receipt was pending. The first guide/presence tick
had not occurred yet. Guide admission called movement current_location while
transfer_pending was true, obtained no location, and returned rejection before
the later pending-transfer tick guard could run.

Move the exact periodic-tick guard ahead of guide/presence admission. This
keeps the connection alive while awaiting the native context receipt, without
accepting gameplay in an unfinished transfer or manufacturing presence.
The existing receipt path then permits the next tick to join destination peers.

## Regression evidence
`test_town_player_visibility_server.py` now accepts an explicit binary override
GOD2_VISIBILITY_TEST_BINARY and tests the initial indoor exit before any guide
or presence tick. The old build-monster-trace binary failed with an unexpectedly
closed connection; the rebuilt build-town-visibility binary passed. The test
then verifies reciprocal 6F records after destination admission. The existing
town/indoor/battle/chat/reconnect lifecycle also passed, now including ticks
between transfer and receipt.

## Real-client evidence
`artifacts/playtests/dual-presence-20260924-repair` uses private desktops,
independent client folders, port 2598 and a SQLite backup of the owner's saves.
Only copied character positions were changed. Both TW/TW and TW/CN runs showed
test and test1 in each other's native actor pools with valid four-component
resources; targeted private-window captures showed both rendered characters.
TW/CN movement was observed in the other client's pool and rendered frame.
No input desktop switch or foreground user input was used.

The initial fixture startup was rejected because its database basename did
not satisfy the isolated server guard. This was corrected before acceptance.
Failed fixture attempts and stale JSON are not counted as successful tests.

## Scope
This proves same-town two-client presence and a reproduced transfer-disconnect
fix. It does not establish that every historical report of missing characters
had the same cause, nor complete every packet/system in the game. Physical IME
acceptance is outside this change. No client EXE or launcher change is required.
