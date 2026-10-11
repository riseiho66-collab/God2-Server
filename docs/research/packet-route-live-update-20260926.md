# Persistent route update and migration compatibility — 2026-09-26

The persistent loopback service on port 2592 was still running an older
executable while the new multi-slot C2S26/S2C41 route was present only in the
Release build. There were zero established connections before the update.
The previous executable, configuration and an online SQLite backup are in
`artifacts/releases/packet-route-update-20260926-01/`.

The first isolated launch with a copy of the real config and backed-up player
database failed at migration validation. `src/db/Migration.cpp` migration 19
had lost one leading space before `CHECK(...)`; the deployed database stores
the complete original SQL text and correctly rejects such edits. Restoring
that exact space repaired the compatibility failure. No historic migration
meaning or stored player row was rewritten. A permanent test now pins the
deployed migration 1..21 history digest to catch future accidental edits.

The rebuilt binary was staged with the live settings except for port, database
and log paths. It sent the 19-byte native seed on 2598, applied migrations
through 21, passed `quick_check`, and preserved all existing account and
character rows. The latest-binary isolated three-character scenario passed
both town/door/battle/visibility cases (2/2); its S2C82 assertion was aligned
to the documented 30-second initial command window. The migration pin test
passed (1/1).

The persistent executable was then updated to SHA-256
`53ace407735073fa55e1ee53e92fb892f02621b8f1ee2f0d4b55c51841c3a1e3`.
It listens on loopback 2592 and sends the 19-byte seed. Live SQLite now has
schema 21, `quick_check=ok`, four accounts and three recovered characters;
account, character and position rows match their pre-update backup exactly.
This deploys the multi-slot code, but `diagnostic_world_supply=false` in the
persistent configuration, so C2S26 item use is still an isolated diagnostic
route rather than a newly enabled public gameplay feature. No physical client
acceptance for slots 5/12 was claimed.

The existing live log also contains unsupported world records, including an
opcode `6D` two-byte logical record. Its original producer meaning and state
effect are not yet established. Keep fail-closed behavior until the current
client's producer and consumer path is identified; do not add a guessed no-op
route. The next packet investigation should start from that native producer,
then pin layout and state before implementing a handler.
