# Post-Visibility Core Regression

## Scope

After integrating owned-player Fight transitions, post-battle peer refresh and
native post-battle movement, rebuild all Release targets and check the core
CTest group. This is regression evidence, not full-world or balance acceptance.

## Executed

```powershell
cmake --build build --config Release
ctest --test-dir build -C Release -I 1,65 --output-on-failure --output-junit core-regression-20260921.xml
ctest --test-dir build -C Release -R '^battle_process_crash$' --output-on-failure --output-junit battle-crash-regression-20260921.xml
```

The full Release build passed. All65 selected core tests passed in125.66s.
Selection was the current CTest indices1..65, from recovered_visibility through
cli_invalid_duration, not all189 registered tests. This covers C++/Lua gameplay
fixtures, transport/session guards, accounts/characters/positions, inventory and
quest codecs, native catalog readers, application startup and configuration.
Test names containing native or recovered do not independently certify all
official gameplay semantics.

The separate battle_process_crash test passed in0.67s. It runs the real SQLite
repository in child processes that exit at character_resources,
battle_checkpoints, character_experience, battle_settlements, commit and
after_commit boundaries. New processes verify rollback or the single committed
settlement, then verify again. These are controlled repository fault cases,
not proof of live client crash recovery or every possible storage failure.

## Artifacts

- build/core-regression-20260921.xml SHA256:
  ADAFD9BB39589258D97DE645B4A1B9DE6CF79AC8CBACABFA8240EB6F13049162
- build/battle-crash-regression-20260921.xml SHA256:
  A05B38CFB776F9190273296B5D362BDEBF00639F018108786EE24FCD8CA85100

No production configuration, source client, account or saved player data was
promoted or replaced for this check. No regression failure required a code fix.

## Remaining Acceptance

The recent two-native-client proof remains the isolated single diagnostic
battle, peer refresh and three-step movement/save path documented in
current-remote-actor-contract-20260921.md. Persistent combat recovery in that
combined path, general repeated encounters, PvP, complete content and gameplay
balance remain open. World acceptance is false; these passes do not increase a
measured playability percentage or certify original damage/monster formulas.
