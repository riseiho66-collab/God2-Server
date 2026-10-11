# Terminal checkpoint settlement

SQLite settle_checkpoint uses the existing settlement transaction implementation,
not a second nested or independent transaction. It requires an active expected
checkpoint at the expected resource revision, matching battle/policy identity,
a strictly newer finished snapshot and exactly one owned actor matching proposed
resources. The supplied won flag must match that actor's victorious side.

Canonical request version3 binds both complete checkpoint documents (including
RNG), policy and checkpoint resource baseline in addition to existing award and
resource request fields. Exact retries return the original ledger result without
rewriting later state. Different requests are rejected. Existing v1/v2 requests
remain unchanged. Legacy settlement rejects an existing checkpoint rather than
leaving it active while issuing an award.

One transaction CASes baseline, writes resources, updates terminal checkpoint,
adds XP and inserts the ledger, then validates exact readback. Failure rolls back
all writes. A subsequent battle reservation becomes available only after ledger
commit. No new migration is needed beyond checkpoint migration10.

Verification: Release server/tests build and database, both repository, TCP battle
service CTests pass. Tests reject bypassing checkpoint with legacy settlement and
wrong victory flag; injected late ledger failure preserves prior active checkpoint,
HP/MP and absent XP. Valid retry commits terminal+XP25 once. Exact replay is stable;
award26 and modified terminal RNG replay fail. Next battle can then be reserved.

## Disk and concurrent replay qualification

The real temporary-database checkpoint test now restores an active battle after
disk reopen, computes a lethal action, and starts two independent SQLite connections
at a shared barrier to submit the identical terminal transaction concurrently.
Both return the same result; resources advance once, XP is25, terminal documents
agree and only one ledger row exists. All connections close before another reopen.
The reopened database retains the terminal/resources/XP tuple and accepts the exact
historical retry without writing. After a later MP mutation, that same retry still
returns its original result without reverting the newer resources; reward26 fails.
The repository suite passed10 consecutive runs including this test. This is not
power-loss testing, cross-process ownership or native-client reconnect acceptance.

## Role projection in the same transaction

settle_checkpoint now accepts optional BattleProgressionCommit, forwarding to the
same existing role/XP CAS and transaction. Version3 canonical request retains the
progression fields as well as checkpoint fields. Parameter omission preserves
non-progression calls. Repository tests now run terminal scenarios both with and
without a role update; late ledger failure rolls back role, resources, XP, terminal
checkpoint and ledger. Success saves exactly the requested CUSTOM-0013 role bytes;
exact replay preserves result, while missing progression or changed level fails.
Release build and all three database/repository suites pass.

The explicit level2/max120/80 bytes are a storage test, not a native or balanced
growth rule. Maxima remain equal to terminal actor resources; no healing introduced.

The preceding storage work did not itself establish Application or native-client
acceptance. Subsequent isolated Application integration is documented in
current-live-level-snapshot-20260921.md and current-second-exchange-recovery-20260921.md.
Actual native level growth, general durable policy/control state, original reward
formulas and normal encounters remain open.

## Disconnect After Commit, Before Result

Source: native-second-exchange-resume-20260921-01/diagnostic-accounts.db.
The retained failed native run committed its terminal skill and completed the
animation, then the service rejected the old terminal receipt rule. It never
delivered the result panel or resumed world movement. The source nevertheless
contains one atomic terminal/XP/role settlement, no pending battle and no saved
position. This is a real connection rejection, not a simulated power failure.

Fresh run native-terminal-disconnect-restore-20260921-01 uses a read-only backup
and the existing default-off world-resource restoration, with battle transition
disabled. The runner qualifies the terminal checkpoint against its ledger,
resource revision and diagnostic provenance before copying it. It does not
reopen the finished battle or replay the reward transaction.

Result NATIVE_SETTLED_BATTLE_RESTORED_TO_WORLD, error null. Native resource return
shows HP76/max120, MP26/max80; role snapshot level2/progress1250. No new battle,
skill or outcome invocation. World position17,13 is the existing diagnostic
initial position because no movement position was saved, not a recovered battle
location or a newly invented spawn policy.

Every SQLite table in source and restored copy compares equal, including schema,
checkpoint, RNG, ledger, role, XP and absence of saved positions. integrity_check
is OK. XP remains250 with exactly one settlement. Source SHA256 before restore
and after verification is
34327d7c61bd2a624e99161634ef6af914b1165eceb7314dbf0a116da0fc31a4.
Saved resource evidence suite passes26 tests.

This qualifies restoration of already committed character state after a lost
result, not re-display of a missed result panel, physical UI acceptance, database
power-loss durability or general reconnect with non-diagnostic encounters.

## First Movement After Lost Result

Run `native-terminal-disconnect-move-20260923-01` starts another fresh server and
client from the same terminal/no-position source. The runner permits exactly one
native movement only under explicit `--terminal-disconnect-restore`; other restore
modes still reject movement probes. Initial position is the diagnostic spawn17,13,
with queue ring010001. The native request returns successfully and the real ACK
`5d01` advances the client ring to010102. Result NATIVE_MOVEMENT_ACK_APPLIED,
error null. SQLite stores area2/scene15/x18/y12/revision1.

Only recovered_positions differs from the source: every battle checkpoint/RNG,
resource, role, XP and settlement row is byte-equal. HP76/MP26, XP250 and one
settlement remain unchanged; integrity_check is OK. The source SHA remains
34327d7c61bd2a624e99161634ef6af914b1165eceb7314dbf0a116da0fc31a4.

Run `native-terminal-disconnect-position-restore-20260923-01` then starts a third
server/client from the moved database. Result
NATIVE_SETTLED_BATTLE_POSITION_RESTORED, error null. Native world state is18,12;
resource return remains HP76/max120 and MP26/max80. No battle entry, skill command
or outcome consumer occurs. All database tables equal the moved source, including
position revision1. The moved source SHA remains
da282706a0c496b7cd9965ef786be28cae4721594e5e7efb8d2d66e8458a659b.

The saved resource evidence suite now passes27 tests. These runs establish the
persisted state sequence `committed battle -> reconnect -> first move/save ->
second reconnect/position restore` with original client functions against our
server. They remain automated native probes rather than physical visual input,
and do not qualify production combat formulas or a universal spawn policy.
