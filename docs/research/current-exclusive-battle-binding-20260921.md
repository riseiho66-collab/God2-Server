# Exclusive in-process battle binding

CUSTOM-0008 binding previously checked only session ID. A second session could
bind the same character or battle ID to an independent mutable Battle instance.
RecoveredBattleService::bind now rejects either collision against existing Bound
records before emplacement. Character identity uses the repository-global ID,
not an account/character pair that could admit inconsistent ownership.

Existing bindings are the sole occupancy source, so failed binds create no claim;
remove and successful terminal release remove occupancy with the binding. All
operations remain confined to the existing game executor. This is an admission
invariant, not a native gameplay rule or multiplayer battle implementation.

Tests cover same character/new session/new battle, changed-account same character,
different character/same battle ID, unchanged original state after rejection,
rejected session lacking command authority, independent character/battle admission
and action isolation, and removal followed by successful rebinding. Existing
terminal release, transaction rollback and diagnostic combat tests remain enabled.
Release server and dedicated tests build passed; service suite passed10 repeats.

Limitations: different service instances/processes still require shared ownership
coordination. Removing an in-memory binding is not proof that a durable encounter
can be discarded or restarted. The repository outstanding-reservation guard remains
separate. Durable battle snapshots, reconnect admission/resume and normal repeated
encounters are not completed by this change. No new client runtime proof claimed.
