# Retained world role resources after battle

Run: `native-player-world-resource-observe-20260921-01`.
Result: `NATIVE_SOCKET_BATTLE_RETURNED_TO_WORLD_LOOP`.

Read-only observation uses UI=[battle+20], role=[UI+86888]. Original code
previously identifies role+5C/+60/+64/+68 as current HP, maximum HP, current MP,
maximum MP (see current-battle-owner-vitals-20260920.md). The observer reads
these 16 bytes at the first action grant and again at world-loop reentry,
reloading the role pointer from the retained UI instead of dereferencing a
freed battle actor.

The historical result key `world_resource_before_battle` means before the first
action, AFTER battle initialization and bootstrap, not pre-battle world entry.
It contains HP76/max120, MP34/max80. After one terminal skill, the battle actor
contains HP76/MP26/max120/max80. World-loop reentry observes the SAME UI and
role pointers with HP76/max120, MP26/max80. SQLite agrees, at revision4.

No new S2C24 packet or debug memory write was added. Existing native battle
handling already updates the retained role source for this path. Adding a
second resource update without a demonstrated need would be premature: native
S2C24 also derives companion HP loss, as verified by current_role_progression.

This qualifies retained source synchronization for one restored diagnostic
skill battle, not visible HUD bars/text, initial world-only login resources,
pet correctness, all battle outcomes or production balance. The missing
world-only login resource acceptance remains open. Tests retain separate
native actor and role field ordering and exact before/after values.

## World-only login gap confirmed

`native-player-world-only-resource-observe-20260921-01` uses a read-only source
backup of the terminal skill save and starts a new server/client WITHOUT battle
transition. It restores the existing character and position18,12, ending with
`NATIVE_SAVED_POSITION_RESTORED`. The first world-frame return reads
UI=world+A7F2F6C, role=[UI+86888], role+5C..6B: ALL FOUR DWORDS ARE ZERO.
The isolated disk database still contains HP100/max120/MP42/max80/revision2.
There is no battle entry in this run.

This is recorded negative evidence, not acceptance. Application currently
loads resources only in diagnostic battle initialization; world_ready binds
movement, and the historical scalar replay remains retired. Do not restore
that retired replay to conceal the missing owned-resource projection.

Next implementation needs an opt-in owned-resource world bootstrap, based on
the current native17-byte S2C24 contract and verified consumer side effects,
followed by live socket consumption at world initialization and post-frame
checks. Native S2C24 body order is HP, MP, maxHP, maxMP; role memory order is
HP, maxHP, MP, maxMP. Both the optional companion HP-loss side effect and
world-ready timing must be respected. No production rule or default resource
values are authorized by this diagnostic finding.

## Opt-in world resource synchronization

Implemented default-off development.diagnostic_world_resources, gated to
non-mock loopback, recovered movement and diagnostic-accounts.db. On the first
validated standalone world tick, Application reads the selected account-owned
resource row and encodes native17-byte24 through RecoveredRoleVitals. There is
no seed/write or historical replay. A missing row produces no resource packet.
The per-session sent marker is removed on disconnect. This is a CUSTOM-0012
saved-state integration experiment, not production balance approval.

Run native-player-world-resource-sync-20260921-01 demonstrated correct packet
input but its observation mistakenly treated ECX (UI) as role. Its memory
output is NOT resource acceptance. The corrected observer dereferences
[ECX+86888]; run native-player-world-resource-sync-20260921-02 is authoritative.
It shows the same role as first world-frame entry, zero resource values before
native E71E0, packet body HP100/MP42/max120/max80, and after full native return
role HP100/max120/MP42/max80. No battle was entered. Saved position18,12 restores;
the database resource revision2 and values are unchanged.

The first world frame still precedes the asynchronous tick/response and can
contain zeros. This run proves subsequent native consumer application, not
zero-flicker initialization or visual HUD correctness. Companion HP behavior
is only qualified by prior bounded native tests, not a live populated companion.
Full live consumer acceptance here does not settle normal gameplay UI, missing
new-character starting resources or production integration.

## Combined world and battle path

`native-player-world-battle-resource-chain-20260921-01` enables both isolated
world resource projection and battle persistence against a backup of the
damaged HP76/MP34/revision3 fixture. Native world24 returns at sequence470;
battle initializer enters489; first grant observes identical role values512;
the skill debits8MP once; world-loop reentry602 retains HP76/MP26. The role
pointer remains identical and SQLite holds revision4. This qualifies ordering
and resource continuity for this combined path, not separate runs joined by
assumption. The source database is not used for writes.

Configuration tests now exercise world projection without battle flags and
reject normal databases, disabled movement, mock login and public listeners.
Four CTests pass after rebuild; the seven recorded resource evidence tests
cover the initial gap, world-only synchronization, battle persistence and this
combined chain. Visual HUD, normal UI gameplay and production balance remain
unqualified.

## Missing-row negative acceptance

Runner option --expect-no-world-resources requires isolated world projection
and movement, with neither restore database nor battle transition. An observed
native resource-consumer call fails this negative fixture. After three native
movement steps the observer continues world frames for at least five seconds.
This is a bounded observation, not proof of indefinite future behavior.

Run native-player-world-missing-resource-20260921-01 finished movement too soon
to prove the missing-row branch executed. It remains an incomplete negative
test, not the authoritative result. Run -02 adds the post-movement window and
a flushed diagnostic absence marker: exactly one marker, no native resource
update, result NATIVE_MOVEMENT_PATH_COMPLETED, position18,12 revision3, and an
empty character_resources table after termination. No implicit HP/MP seed or
DB row is created. Eight resource evidence regressions pass.

This proves the missing-row branch does not block this world/movement path.
It does NOT make the new character combat-ready: authoritative starting
resources and progression rules remain required before normal gameplay.
