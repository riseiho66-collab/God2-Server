# Live diagnostic battle checkpoint persistence

Existing default-off diagnostic_level_snapshot now activates complete battle
checkpoint persistence in Application. After resource/role seed and reservation,
the actual Battle initial checkpoint is committed before binding; its resulting
resource revision is shared with the exchange callback. The callback compares
the stored checkpoint to the exact pre-exchange state including RNG, commits active
exchanges atomically, and uses terminal checkpoint+progression settlement on finish.

All resource diagnostics now use the service's complete checkpoint callback;
only level-snapshot mode writes checkpoint rows. Other resource diagnostics retain
their existing resource-only settlement semantics. No production mode activation,
new stat growth, policy values or modified client executable was introduced.

## Current-client evidence

Run artifacts/runs/native-player-durable-checkpoint-20260921-01/run.json:
NATIVE_MOVEMENT_PATH_COMPLETED, error null. Actual own-server native probe, not
physical UI or visual acceptance. Historical world_accepted remains false.

- Three skill commands; five natural1/1 animation completions, no timeout fallback.
- Level1/progress0 -> level2/progress1250; native progress integer12, award formatter250.
- Final resources HP76/max120/MP26/max80 revision6 (includes initial checkpoint commit).
- One stored terminal checkpoint, battle revision6/winner0/enemyHP0; full actor stats
  and RNG retained. One version3 settlement with XP250 and resource revision6.
- Ledger's previous checkpoint is revision5, enemyHP42/playerMP34. Terminal RNG is
  different, and the exact final document equals battle_checkpoints.document.
- Role snapshot level2/revision2 and saved world position18,12/revision3.

17 read-only saved evidence regressions pass, including exact native/SQLite checks
for this new run. Release server build succeeded. This supersedes earlier notes
that no Application checkpoint caller exists only for this explicit isolated mode.

## Remaining

No receipt-only checkpointing or durable policy snapshot exists yet. Policy tag
does not reconstruct an arbitrary encounter. Fresh-session resume must restore
client battle state, session ownership and action/control admission without replaying
an already committed action. Normal encounters, complete progression balance and
visual acceptance remain open; persistence alone is not completed reconnect.
