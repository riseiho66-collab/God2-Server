# Persistent map panel and multi-character route (2026-09-23)

The previously isolated scene transfer code rejected character IDs other than 1,
even when the selected character owned a completed guide, map item 5569 and the
required saved location. `src/core/Application.cpp` now uses the session-bound
character identity and checks the same position, quest/inventory provenance,
pending context receipt and movement-service owner/snapshot constraints.

`artifacts/playtests/map-enable-20260923-01/setup.py` cloned the separate
completed-guide laboratory database and created account3/character3 with a
valid reward receipt at town110,70. Before the fix, the original-format
dual-socket `probe.py` entered the world, requested map item5569 from slot0,
then got EOF. After the fix, the same probe received native scene record
`61c203000046001a00`, acknowledged the exact context, and saved character3 at
area2/scene15/17,13/revision54. The character's stage3 progress and item5569
remained intact. This is socket and SQLite evidence for a second owned
character, not physical client rendering.

The separate `panel_probe.py` cloned the completed-guide database with only
`map_probe` enabled. It received logical `3f0100` after original-format
`25c1150000`, kept the socket open, and confirmed no changes to positions,
guide progress, inventory or reward receipts. This tests the custom
non-consuming map panel response without sending the character indoors.
Release `diagnostic_door`, `config`, `recovered_movement_service` and
`recovered_quest_sync` tests pass 4/4.

The persistent loopback service now enables **only** `map_probe` in addition
to the prior guide quest. A parsed configuration comparison confirms only that
field changed. Its pre-activation database backup is
`artifacts/playtests/map-enable-20260923-01/persistent-before-map.sqlite`
(SHA256 `e17e17fa4486d3791d1c760db33df906e88816eee942a59a4e1d322e62b07e5b`);
the prior config is `persistent-before-map.server-config.json` in the same
directory. The server was restarted as PID23528 on127.0.0.1:2592 and the
synthetic-account persistent login/world/NPC smoke test passed again.

Indoor transfer remains disabled in the persistent configuration because a
complete return route and visible black-screen outcome are not yet accepted.
The map response and its item-to-panel association remain CUSTOM-0023; actual
rendered panel appearance and player input are still unverified.
