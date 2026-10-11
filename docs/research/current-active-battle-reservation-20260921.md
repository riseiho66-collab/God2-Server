# Active battle reservation guard

## Defect and change

The previous uniqueness key `(character_id, resource_revision)` allowed a new
battle ID after any combat resource debit, even though the older reservation had
no terminal ledger. A resource revision is not proof of encounter completion.

Under the existing BEGIN IMMEDIATE transaction, reserve_battle now checks all
owned reservations without a settlement. One at the exact current baseline may
return its existing ID for idempotent retry. An older baseline blocks allocation.
More than one outstanding row or wrong provenance fails closed. Successful
terminal settlement permits a later reservation. No migration, deletion, implicit
reward, synthetic loss or automatic saved-state reset is performed.

This is CUSTOM-0012 server storage policy, not recovered gameplay behavior.

## Verification

Release server and tests build passed. Both repository suites passed10 consecutive
runs. Real temporary disk SQLite tests reopen the database, reject overlapping
reservations from two independent connections including concurrent requests, settle
the first battle, then concurrently reserve exactly one next ID. Resource values
remain unchanged by reservation. Close/reopen retains that ID. Existing injected
insert-failure and resource rollback tests still pass. Battle service and TCP
battle service regressions passed in the initial targeted run.

One initial repository test failed because it assumed revision3 after inserting
an explicit settlement. It now checks the next revision relative to the actual
settled baseline; no rollback requirement was removed.

## Open lifecycle work

An idempotent reservation is not an exclusive live-session lease. This guard does
not prevent two processes binding the same ID at the same baseline. Full session
ownership, durable in-progress battle snapshots, reconnect/resume and explicit
abandonment are still required. An abandoned older reservation currently blocks
new combat; it must not be erased or reported recovered. No new current-client
runtime acceptance is claimed for this storage-only change.
