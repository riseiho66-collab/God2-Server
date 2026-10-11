# TW276 retained private-ticket PK recovery

This round adds CUSTOM-0114 same-process recovery of one shared PK Battle from
an existing genuine private Ticket. It does not reconstruct Prepared or its
private source observations from JSON, reconnect Sessions, install Application
RoomAuthority, resend packets, or implement world return. The original owned
entry, combat, formulas and numeric limitations retain their recorded origins.

The implementation changes SqliteOwnedPkRoomRepository.h/.cpp and
OwnedPkRoomState.h. All work is static source reading, editing and receipt
accounting. No compiler, build, tests, server/native runtime, codec execution,
game-database SQL, schema installation, migration or deployment was run.

## Original-ticket and runtime ownership

Previously Ticket retained its immutable Input, durable id and complete readset,
but had no original repository issuer. It now additionally retains a private
stable shared issuer. Only the new claim/recovery methods require that issuer;
legacy ticket comparison and persisted readset bytes remain unchanged. Copying
the repository shares its actual connection and issuer/claim registry. A fresh
repository instance cannot use another issuer's Ticket for these new methods.
This is an actual retained private object boundary, not a caller origin string,
checkpoint JSON, room id, digest, or regenerated seed.

claim_runtime returns a privately minted move-only RuntimeClaim. The issuer
registry retains only a weak reference per room. A live claim cannot be copied,
shared with a second RoomState, replaced or displaced. Expired entries alone
are removed before a new claim. RoomState stores the claim alongside its Ticket
and Battle, in both ordinary activate and restore_retained. Failed staging
releases its claim by normal RAII; destroying the previous actual RoomState is
necessary before another State can restore that room. Recovery snapshots do
not contain a runtime claim and cannot authorize two mutable Battles by copying.

All room and database operations require the existing single actual game
executor and connection-owner discipline. A shared issuer mutex excludes only
the claim registry's expired cleanup/lookup/insertion, including repository
copies. It does not make SQLite, the repository or RoomState thread-safe and
is not a database-file-global singleton, cross-process lease or restart
authority. Repository copies share the namespace; unrelated
new issuers remain distinct and reject these foreign retained Tickets.

## One durable observation

recover_retained requires SQLite autocommit and opens its own explicit BEGIN
read scope. It issues no DML, schema installation or source callbacks. This
differs from the existing SqliteSupport Transaction helper, which uses BEGIN
IMMEDIATE. Failure rolls back the read scope and changes no saved data,
room phase, owner lock, outbox bytes or submission flag.

The loader recomputes the complete retained Input readset and compares it with
the original private Ticket readset. Within the same SQL snapshot it requires
active or finished state, the persisted full readset and CUSTOM-0086 design,
both exact member locks and exactly two members. Account, full character,
Session, Application PK world generation and prebattle generation remain exact.
Existing owners_current checks continue to require the admitted saved resources,
role and position, and absence of an unrelated diagnostic pending battle.

It deliberately does not use RESERVED current/initial, old appearance.current,
private world initialization current or live auxiliary/equipment/title fences.
Those source observations are frozen at admission and their InWorld lifetimes
expire during battle. Source provenance remains retained in the genuine Input;
this round does not refresh it or turn stored totals into original-native rules.

CheckpointCodec and Battle::restore validate canonical complete checkpoint/RNG,
id, revision, LegacyCustom profile and resource bounds. checkpoint_owned_pair
also compares the complete admitted topology: exactly slots0 and14 with the
same controllers, maxima, dual attack and dual defense. Only current HP/MP may
change. Active/finished living-side/winner conditions remain validated. At
revision1 the entire checkpoint, including RNG, must equal the original initial
Battle checkpoint. Later recovery restores the exact current RNG string; it
never rebuilds current state from the initial seed or replays retained intents.

Existing read_round runs inside this same observation and validates canonical
round SQL/document revision, checkpoint battle revision, state/Terminal,
headers and original command contexts, notification bounds/permanent first
observations, legacy initial masks and first notification revision fences.
The entire round remains retained, including phase, round number, grant epoch,
controls, grant submissions, masks and canonical intents. Resolved intents in
ResultsControl/Terminal are historical results; recovery does not reauthorize
their old MP cost against the already consumed current MP or apply them again.

## Complete outbox history

The loader reads every outbox row, including submitted rows, ordered by actual
revision/viewer. Each actual revision must have exactly viewer0 and viewer1,
nonempty bytes within the existing max logical size and a strict0/1 submitted
flag. The first pair is revision1 with exact original Prepared entry bytes;
the final pair must equal the current checkpoint revision. Revisions increase
by1 or2, preserving the existing two-action settlement that queues only its
final revision. It does not require a row at every intermediate battle revision.

All older pairs must already be submitted, matching existing settlement's
barrier. Current controls imply that viewer's current outbox was submitted;
Grants/Collect/Ready require both current submissions. ResultsControl may retain
one notification while its peer is pending. Terminal output can still be
unsubmitted. Grant epoch is not interpreted as an outbox revision.

RetainedOutbox exposes a read-only snapshot descriptor containing complete
stored bytes, original Session/PK-world/prebattle+1 delivery identity and the
original submitted flag. No submitted bit is reset and no transport is invoked.
Historical result bytes remain opaque bounded stored output; current checkpoint
and readset do not independently rederive or certify their original semantics.
No new fixed total-history quota is imposed. Aggregate size_t overflow and
allocation failure fail without mutation; a long valid history is not deleted
or silently truncated to make recovery succeed.

## Real RoomState rebinding and final fence

RetainedRecovery has a private constructor and only const getters for the
genuine Ticket, current checkpoint, canonical round and full outbox snapshot.
retained_recovery_current reloads under another complete consistent read scope
and compares checkpoint including RNG, complete round document, all rows,
submission flags and delivery identities. It does not compare just revisions
or digests, and requires the same private issuer namespace.

RoomState.restore_retained first rejects an already bound local room, claims
the runtime owner and restores the retained checkpoint. It preallocates the
entire future map node before calling the final durable-current fence. After
that fence it transfers the existing node into the real room map without a new
allocation, source callback, action, SQL write or socket send. The resulting
Room uses the existing persistent round/command/outbox methods with the exact
retained Ticket, not a diagnostic Battle or two independent participant Battles.

This fence is a consistent observation followed by publication on the existing
serial owner. External database writers can still mutate after the read scope
ends; no transaction is held across arbitrary in-memory publication and no
cross-process atomic DB/runtime ownership claim is made. Existing subsequent
checkpoint/round CAS checks still apply. Full writer interlocks and lifecycle
recovery remain separate.

## Boundaries and remaining work

The source increment is retained-ticket loader plus actual single-room
rebinding, with no new wire opcode, complete gameplay route or completion
percentage. Existing default flags, schemas and native packet layouts remain.
No native ACK, queue acceptance, rendering or successful reconnect is inferred
from an outbox submitted flag or restored Battle.

Recovery requires the original Ticket and its source object graph, exact borrowed
repositories/connection and original issuer to survive. A process restart that
loses those private objects remains unsupported. Sessions/common transport
identity, departure markers, active admission operation recovery, pending socket
writes, terminal settlement/owner-lock release and genuine world re-entry are
not restored here. Application PK hosting remains uninstalled. Recovered
initial grants do not create later-round grants, learned skills or turn policy.
Existing signed legacy combat/wire limitations and the separately authorized
64-bit extension remain unchanged.

The independent lifecycle/source audit is retained at the TW276 archive's
agents/native/seal.json, SHA256
48e289369645add2aaba069700bc646f8587de96b3b39c85ef32a6853752beb8;
findings SHA256
6639d57a4978cde218b4b4a59f5fd646664917601772d249a39ee2d056b895ef.
Its baseline audit is not a review of subsequently edited code. Full candidate,
diff, final source and independent review receipts are recorded separately in
this round's archive. Independent review terminal pins belong to the root round
report, avoiding mutable circular seals in this document.

The first complete candidate is preserved unchanged. Refinement2 adds only
the shared claim-registry mutex and explicit self-contained standard includes,
following the reviewer/root concurrency boundary finding. The database and
actual game-executor contract remain unchanged.
