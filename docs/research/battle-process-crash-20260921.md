# Battle Settlement Process Crash Qualification

The existing disk-reopen and callback rollback tests did not terminate a process
inside the SQLite transaction. This test adds that missing boundary without
changing gameplay, packet contracts, client binaries or production saves.

`tests/test_battle_process_crash.cpp` links the actual repository and battle core.
`tests/research/test_battle_process_crash.py` creates a temporary migrated database
for each fault and launches separate setup, crash and verification processes.
Only the test executable installs SQLite hooks; the server has no crash switch.

Six points are exercised:

- Update hook immediately after character_resources changes.
- Update hook immediately after battle_checkpoints changes.
- Update hook immediately after character_experience changes.
- Update hook immediately after battle_settlements changes.
- Commit hook before commit finishes.
- Immediately after settle_checkpoint returns, before any simulated reply.

Each crash uses std::_Exit with a point-specific exit status, so destructors do
not roll back or close SQLite. A missing hook produces a failing exit code.
The first five cases reopen with the complete original active checkpoint,
HP100/MP50/resource revision2, no XP and no receipt. The post-commit case reopens
with the complete terminal checkpoint, MP42/revision3, XP25 and one receipt.
Each case retries the same terminal request twice, then a second fresh verifier
process checks it again. There is exactly one receipt and XP remains25.

Build and six crash/recovery subcases passed on 2026-09-21:

```text
cmake --build build --config Release --target battle-process-crash
python -B tests/research/test_battle_process_crash.py build/tests/Release/battle-process-crash.exe -v
```

CTest entry: battle_process_crash. These are CUSTOM-0012 isolated fixture
values, not original formulas or balance approval. The result qualifies process
termination atomicity in the current SQLite setup, not power loss, disk hardware
failure, arbitrary journal configurations, native-client reconnect presentation
or full world acceptance. Overall playable progress is not increased merely
because these regression cases pass.
