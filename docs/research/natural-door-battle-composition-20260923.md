# Natural doorway and map panel battle composition (2026-09-23)

The completed-town diagnostic battle previously required manual map-item scene
transfer and a literal character ID of 1. Those conditions prevented the
existing persistent route (map panel plus movement-triggered doors) and a
second owned character from entering the isolated battle fixture.

`Config.cpp` now accepts an explicit `battle_after_quest` plus
`door_after_battle` combination with `door_routes`, `map_probe`, and no manual
scene probe. The previous manual-transfer combination remains available.
`Application.cpp` keeps the map-panel response in this natural-door mode and
uses the authenticated session account/character to check saved indoor18,12,
completed guide stage3, and the pinned slot0 item5569 receipt. The default is
still off. The standalone remote-actor fixture retains its own ID1 guard.

`artifacts/playtests/battle-natural-20260923-01/probe.py` uses a SQLite backup
of the isolated second-owner character3 fixture and original-format two-socket
frames. `--route` passed: map panel response `3f0100`, town86,71→86,70,
doorway receipt into indoor16,19, seven legal indoor moves to18,12, then the
single battle entry `82 00000000 00000000`. The saved position ended at
area2/scene15/18,12/revision91 with stage3 and reward unchanged. The direct
indoor restore path also passed. `--unqualified` removed the reward from the
clone and confirmed no battle entry. Each clone passed SQLite quick_check.

Release server and tests built; config, doorway, town navigation, battle service,
battle transaction and battle bootstrap tests passed (6/6). The first broad
CTest run was stopped after 21 passing cases while `session_state` was still
running; a later dedicated `session_state` run passed in 94.94 seconds. No
claim of a full green suite is made. The loopback persistent service restarted
on port2592 after the build and retains `battle_after_quest=false` and all
other battle flags false. No user account or persistent world save was changed.

At that first checkpoint, battle settlement and post-battle return remained
untested. The socket continuation below covers those steps; visual client
interaction, original encounter trigger, and combat balance remain open.

After the restart, original-format login and character-list smoke passed on
the persistent port2592. Its SQLite quick_check is OK; the user's character2
remains town59,55/revision9. The persistent config still has
`battle_after_quest=false`.

## Original-format socket continuation

The same isolated character3 `--route --settle` run now uses the native client
skill command `3500030037000001000000000001000000` captured in
`native-town-battle-door-20260923-01`. It receives the server's participant
vitals, commits one winning skill action, then sends the captured separate
control receipt `35000b0000000001000000000000000000`. The server returns the
outcome record and resumes world movement. The saved resource row is
HP100/120, MP42/80, revision2; one durable battle settlement records victory
and XP0. These are CUSTOM-0012 test values, not original game balance.

After battle, the original-format socket walks eight legal indoor cells from
18,12 to the exit16,20. The movement queue correctly restarts at sequence1
on world return. The door transfers to town86,71/revision100, the town guide
projection appears, and the map item again returns `3f0100` on that same
connection. `reconnect.py` starts fresh server and client sockets from this
save; town guide and map panel restore, a further tick does not reenter battle,
and all seven tracked position/quest/inventory/resource/battle tables compare
equal before and after reconnect. Both runs pass SQLite quick_check.

This closes the isolated original-format socket chain through battle, doorway
return, and cold reconnect for the second owner. Native client visual
operation and physical input in a private desktop are still unverified; the
encounter trigger and combat balance remain custom. The persistent battle
switch remains off.

## Settled fight reconnect guard

An additional isolated test exposed a repeat trigger: after settlement while
still at indoor18,12, a cold reconnect's second world tick sent another battle
entry. The per-session encounter counter resets on reconnect, so it cannot
enforce the single completed-quest fight. `SqliteRecoveredCharacterRepository`
now answers whether this owned character already has a CUSTOM-0012 battle
settlement. The town battle gate checks that durable result after the existing
saved-position, quest and reward checks. An unsettled reservation does not
suppress the encounter, and a settlement for another owner does not count.

The pre-fix `reconnect.py --indoor` test failed because the server sent the
duplicate entry. After the fix, the same settled indoor save stays in the
world with no second battle and accepts a legal move to19,12/revision84;
quest, item, resource, reservation and settlement rows remain equal.
`run_all.py` repeats five cases from a fresh
isolated source: missing reward, first battle settlement at indoor18,12,
indoor cold reconnect, full map/door/battle/return route, and town cold
reconnect. It reports PASS in `artifacts/playtests/battle-natural-20260923-01/`
`acceptance.json`, with source SHA256
`6831f29e48412170996b54b4dc0ab057deebe7256c77896a7518c4264256caa9`.
The repository test covers new, pending, settled, foreign-owner and reopened
database states. Release build and the focused tests passed. The persistent
server was restarted with the new binary but its battle feature remains off;
the user's character2 save is still town59,55/revision9 and SQLite quick_check
is OK.

The later broad 196-case suite started four expensive native-data tests in
parallel. Three coverage generators passed; the four long-running battle-map
emulation cases showed CPU progress but were stopped to avoid spending more
time on unrelated coverage. The changed repository, battle service,
transaction and config tests all pass, as do the five socket acceptance cases.
