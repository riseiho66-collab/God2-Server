# Atomic SQLite checkpoint and resources

Migration10 creates an empty battle_checkpoints table keyed by existing battle
reservation. Stored values: canonical document, committed resource revision and
reserved policy identity CUSTOM-0012/diagnostic-v1. Existing migrations remain
unchanged; no account, character, historical evidence or live save was reseeded.

Concrete SQLite repository load validates account/character/reservation ownership,
document shape, runtime, identity and policy provenance. commit_checkpoint runs in
BEGIN IMMEDIATE and compares complete expected checkpoint plus expected resources.
Initial snapshot requires battle revision1 and the reserved resource baseline.
Updates require strictly increasing battle revision and matching resource revision.
Exactly one controlled actor must match the proposed HP/maxHP/MP/maxMP. Invalid,
foreign, stale, mismatched, terminal or already-settled writes are rejected.

Resource update and checkpoint upsert/readback share one transaction. Failure rolls
both back. No reward or settlement is created. The initial checkpoint commit also
increments resource revision; it must be used as the new baseline by its caller.

Verification: Release server/tests build succeeded; database and both recovered
repository CTests pass. Tests inject checkpoint insert failure and corrupt post-write
document, proving neither leaves a partial MP debit. Valid retry saves MP50->42 and
enemy HP150->140; stale/duplicate versions fail. A real temporary SQLite file is
closed/reopened before another action, committed, then closed/reopened again with
checkpoint and resources unchanged. This is orderly disk reopen, not a simulated
power-loss durability test or native-client reconnect acceptance.

Limits: API is not installed in Application or RecoveredCharacterRepository's
general interface yet. Existing resource/settlement APIs do not automatically
advance this optional checkpoint. load returns the stored record, not authorization
to resume: caller must match current resources and unsettled reservation before
binding. Policy tag is not a complete policy/receipt snapshot. Terminal checkpoint
integration, compare-and-swap contention tests, durable session ownership, control
receipt recovery and native client resume remain open. Production is not enabled.
