# Live pending battle fixture

Runner option --stop-after-first-checkpoint is limited to fresh isolated
diagnostic-level-snapshot, three rounds, animated skill settlement. It stops the
observer after two natural animation completions and checks the SQLite checkpoint
read-only: active, battle revision3, resource revision4, no settlement ledger.
The normal runner cleanup ends the test session; it does not insert a win/loss,
client receipt or award. This is controlled interruption, not power-loss testing.

Run artifacts/runs/native-player-pending-checkpoint-20260921-01/run.json:
NATIVE_FIRST_EXCHANGE_CHECKPOINT_CAPTURED, error null. One native skill command,
two natural1/1 animation completions without timeout. Persisted role HP88/max120,
MP42/max80 at resource revision4; enemyHP96; checkpoint active revision3/winner null
with full RNG. Role snapshot remains level1/revision1. XP and settlement tables
are empty, and no native outcome entry occurred.

18 saved evidence regressions pass including exact checkpoint/resource/no-award
checks. Source database is the preserved fixture for subsequent resume tests; use
a read-only backup into a fresh run directory, never mutate the source.

Boundary: the observer stops at animation completion, not proven client control
receipt acceptance. A resumed session cannot infer receipt/rearm state from this
checkpoint. Durable action admission and policy reconciliation plus native battle
reconstruction still need implementation and a fresh-client continuation run.
Historical world_accepted classifier remains false; no full normal play claim.
