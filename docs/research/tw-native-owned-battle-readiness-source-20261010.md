# TW254: actual PK readiness consumes owned normal-world source

Phase1 source connection only; no build, test, compiler, gameplay execution,
native execution, codec, game database/SQL execution, migration or deployment.

## Existing source gap and connected change

The actual Application pk_peer resolver used player_visibility.contains as a
readiness condition. That visibility map is populated behind diagnostic
visibility settings, so it could prevent ordinary PK admission before reaching
the still-missing RoomAuthority. Replacing it with a boolean or a historical
last_observed prefix would merely remove the source boundary.

The new readiness path instead reads the actual owned normal initialization,
immutable saved Restoration, exact ordered write observations and expected
receiving prefix for each actual Session. It owns the normal handle, prefix and
receipt vector before SQL observers, rechecks exact map/source identity, full
account/character, phase, battle generation and recovered readiness before and
after source observation. Every receipt must be for its corresponding full
batch and Written, and the actual normal S2A must have written. The complete
saved deity readset and referenced full catalog rows are observed through the
existing normal_entry_prefix_current path. Caught nested readiness observation
poisons the outer operation; missing or stale material fails this PK readiness.

The prior Session Current APIs intentionally require the exact active sender's
world-records callback and cannot be called for another player there.
The new explicit on_game pure Current methods use immutable creator thread
identity minted by the actual posted selection job for normal entry and by
the actual TLS-guarded world sender for write metadata. They check this owner
before game-owned IDs, lock the private weak exact Session for the operation,
then compare the original private incarnation/entry/current owner tuple.
The original TLS APIs retain their behavior. No public first caller nominates
an owner, no callback/barrier is added, and no source is kept alive by a new
strong Session cycle. Both players can now be observed on the actual game owner.

The qualifier is called by the existing pk_peer resolver used by invitation
lookup/current/expiry. Frozen chat and visibility population are unchanged.
This is a source readiness connection, not permanent authority or an atomic
cross-repository snapshot. It does not make a local socket write a remote ACK.

## What remains

pk_rooms remains absent. No invitation, S82, InBattle transition, schema install,
new combat profile, actor grant or stat values are invented by this change.
RoomAuthority still requires actual owned complete player identity/appearance,
raw per-viewer contexts, bulk/grant/mask material, actor/rules inputs and their
underlying current readsets. Existing paired Battle settlement/backend exists;
its actual adapter, dual Session publication and terminal/restart recovery do
not yet exist. A durable outbox insertion is not dual socket write completion.

Native254 confirms that S82 is only its nine-byte wire record. The1004B event is
constructed locally by the client and is not a server wire payload.
Existing CUSTOM0086 viewer positions0/14 are explicit custom topology, not a
universal native deity/actor mapping. Unknown contexts may only be assigned by
an explicitly documented custom policy; they are not silently room IDs or
recovered official semantics. Existing profile40, role/resources/position and
historical6bf auxiliary rows do not constitute full149c battle input provenance.

## Accounting

Three existing C++ files change, no new C++ file. Mixed partial source
segments238→239 are not completed gameplay routes. New complete routes,
opcode values and global native coverage:0. TW C2S156, world S2C252, battle
index110 stay unchanged; full TW route denominator and percentage stay unknown.
Evidence: C:/Users/risei/.codex/artifact-archives/god2-server/20261010/tw-native-owned-battle-admission-source-254.
All before/candidate/final originals and static reviews are retained; filesystem
seals are not gameplay acceptance.
