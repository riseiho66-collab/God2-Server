# Defeated save: world resource packet

The previous native-client timeout run saved character 4 at HP 0/120,
MP 50/80, resource revision 2 and one `won:false`, XP 0 settlement. A fresh
login could enter the indoor world, but the saved resource projection was
restricted to another isolated database.

`diagnostic_world_resources` remains default off. It can now be enabled on
`town-diagnostic-accounts.db` only with the quest-gated town battle mode,
recovered movement, non-mock login and loopback. The existing account-owned
`S2C24` path reads the saved row once on a later standalone world tick. It
does not seed, heal or write resources. The normal database remains rejected.

The private run `artifacts/playtests/private-defeat-world-resources-20260926-01`
used a SQLite backup, loopback port 2598, the current unpacked EXE with only
the test port changed, and a separate desktop. The installed EXE and running
port-2592 service were untouched. Current-client login, character selection,
world initialization, indoor save restore and a subsequent world tick all
completed. The server sent exactly one saved `S2C24` with HP 0/120 and
MP 50/80; the game process remained alive after the send. SQLite still had
HP 0, revision 2 and one loss settlement. `verify.py` prints
`DEFEATED_WORLD_RESOURCES_CURRENT_CLIENT_PASS`.

An independent backup in `private-defeat-world-resources-20260926-02` repeated
the chain. After `S2C24` and another client world click, further world tick
batches were accepted without a disconnect or saved resource change. A separate
read of `recovered_positions` confirms server-authoritative movement from
area2/scene15 `(18,12)` revision87 in the source backup to `(19,16)` revision91
in the run02 database. Run01 independently reached `(18,14)` revision89.
This confirms movement persistence while HP remains zero; the tick records alone
would not have proved it. Its `verify.py` also
prints `DEFEATED_WORLD_RESOURCES_CURRENT_CLIENT_PASS`. The disposable test EXE
was removed after each run; port 2592 remained on the original server process.

Release build and config, recovered world service, battle service and battle
bootstrap CTests pass. This validates packet delivery and immediate client
continuity, subsequent world ticks and persisted movement after HP-0 login.
The private runs did not inspect role memory at the native consumer or prove
combat readiness, revival or recovery. Those remain separate packet and rule
gaps; no automatic resurrection is inferred.

The HP-0 movement result changes the next priority: login and ordinary world
movement do not require an immediate synthetic heal. The next packet-driven
gameplay check is whether the current client can enter another encounter from
this saved state; a failure must be traced at its actual producer or server
gate before defining a death-return or healing rule.
