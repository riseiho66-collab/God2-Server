# Private original-client battle playtest (2026-09-23)

The disposable client ran on a separate Windows desktop against loopback port
2598 and a copied `town-diagnostic-accounts.db`. The production server on 2592
and its database were not used by this playtest. The copied character had a
completed stage-3 town guide, reward item 5569, and a test-only position set to
indoor area 2/scene 15 at (18,12). This position edit is a fixture, not a
natural encounter trigger.

The first physical battle exposed an original-client action-02 notice after
the initial control notice. It had actor 0, side 0, masks 0001/0000, context 0
and zero unwritten fields. `RecoveredBattleService` rejected it, leaving the
client disconnected in the battle view. The service now accepts this one exact
notice for the opted-in completed-town-quest fixture, with no combat effect;
the notice cannot replay or precede initial control. A service test covers
both the accepted sequence and rejected variants.

After a physical target click the original client sent a basic attack, received
combat frames, displayed the result, and returned to the indoor world. The
server settled battle 1 once, with a win, resource revision 2, HP 100/120,
MP 50/80 and XP 0. The client then sent context `04 00 01 00`, which the
earlier post-battle gate rejected. That exact town-fixture context is now
accepted after release; it cannot settle again.

Final private run `artifacts/playtests/private-battle-ui-20260923-01/`
`battle-captures9` shows the original battle view, result, indoor return,
further physical movement and the indoor doorway back to town. SQLite saved
town area 2/scene 4/(86,71)/revision 153, and `quick_check` returned `ok`.
The door committed after battle on the same client connection. A separate
client relogin in `battle-relogin` rendered the saved town position with one
existing settlement and no repeat battle.

This is a narrow CUSTOM diagnostic path. The game was launched directly by
the private desktop runner, so it bypassed the native launcher's Locale
Emulator profile; screenshots contain garbled or missing text. UI language and
normal combat balance are not accepted by this playtest. Natural encounter
rules and broad playable content also remain open.

The five directly related Release tests (`recovered_battle_service`,
`diagnostic_door`, `recovered_movement_service`, `recovered_quest_sync`,
`recovered_world_records`) passed. A broad CTest run reached test 160 of 196
without a failure before it was stopped to avoid delaying the next gameplay
work; it is not a full-suite pass. The production Release server was rebuilt
and restarted on port 2592 with SHA-256
`decbb02369da1c1d3290578bc35ad47321c5996fefe74270f3a14cafd4352678`.
The deployed configuration keeps the isolated
battle flag off. A 19-byte handshake and SQLite `quick_check=ok` passed after
restart.
