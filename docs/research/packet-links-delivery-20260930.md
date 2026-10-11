# Packet integration and independent review — 2026-09-30

## Candidate and bounded scope

Candidate SHA256:
`1c2a6d090c6759eca2786adba690ab7da60e6a821ff87c73005e7df01ad72fc5`.
Current client SHA256:
`9be38ef858bc9c63b6f296cae4a8e601ddcfaf614700e725c4bec44065b53336`.

- **C2S24 reserve pet42/43:** complete owned-instance swap with E3/FB projection,
  SQLite transaction/CAS, rollback and cold restoration. Active44 is preserved.
  Native transport is verified; whole-instance swap policy is CUSTOM-0039.
- **C2S20/S2C23 secondary role text:** fixes the observed unsupported20
  disconnect. Canonical text is stored per owned character with explicit CP936/
  CP950, UTF8 and revision; own-client response and cold restoration are wired.
  Durable server policy is CUSTOM-0056. Primary names and common chat are unchanged.
- **C2SD6 pet2 revert intent:** exact structural decoding and owned-state
  inspection keep valid requests connected with explicit diagnostic denial.
  No item is consumed and no pet is altered. The real revert effect is **OPEN**:
  prior-value history, consumption and successful result contract are unqualified.

## Verification

- Registered integration selection: **12/12 CTest suites passed**.
  Log: `artifacts/reports/packet-links-20260930-ctest.log`.
  Includes three TCP suites comprising eight disposable-server test cases.
- Core regression: **9/9 suites passed**: database, decoder, dispatcher, network,
  recovered_account_login, recovered_character_repository,
  recovered_character_list, recovered_movement_service,
  recovered_position_repository.
- Same eight TCP cases under Python optimization: **8/8 passed**; this repeats
  those cases, rather than adding eight new coverage cases.
  Receipt: `artifacts/research/role-text-20260930/tcp-optimized-result.json`.
- Existing frozen-chat baseline verifier passed with its baseline unchanged.
- Formal schema38 database was backed up through a read-only connection and
  upgraded only in isolation: **53 existing tables**, previous schemas and
  migration1..38 preserved. Migration39 adds an empty role-text table; repeating
  the migration is idempotent.
- Original current-client hidden-desktop receipt:
  `artifacts/playtests/private-pet-reserve-20260930-03/run-result.json`.
  SHA256 `70319eb80148b148ab058255cea374c59e10acc0c7ef1ead9b2d201dccdae5cb`.
  Actual42→43→42 dragging and fresh-process restore passed. Actual role UI ASCII
  input emitted20, saved canonical bytes, and23 restored actor/renderer/widget7
  on fresh-process login. All owned processes closed; input desktop and source
  client/config/database were preserved.

## Review repairs

Independent review caught an incompatible base/concrete repository constructor;
the gate now uses the existing concrete repository. WorldRecords' exhaustive
test variant/visitor was updated for both appended types and tests mixed record
roundtrips. Test-only duplicate character names and a duplicate CMake target were
corrected; all affected tests were rebuilt and rerun successfully.

Detailed independent risk review:
`docs/research/packet-links-review-20260930.md`.
The build still reports the existing Session.cpp getenv deprecation warnings;
these are not attributed to the new packet work.

## Completion boundaries

Two bounded usable feature routes have passed current-client acceptance: **2/2
(100%)**. This is not the completion percentage of the whole game's protocol.
D6 effect, peer6F secondary text, original wild-monster stats/spawns, complete
quests, teleport99/A9 authority and dailyD8 rewards remain open. There is no
verified exhaustive denominator for a whole-server completion percentage.

This delivery's release status is tracked separately in its release manifest and
verification; tests on a candidate do not themselves prove production deployment.

## Installed result

Release `artifacts/releases/packet-links-20260930-01` was applied successfully.
Its `verification.json` confirms the tested candidate installed, managed listener
PID32268 using the unchanged formal configuration, schema39, all53 previous
tables preserved, unchanged prior schema/history, and no database-file replacement.
At verification, no existing saved table changed and the new role-text table was
empty. The client hash and frozen-chat baseline remained unchanged. Release-tool
failure and rollback gates separately passed **18/18 tests**. Code/config and
SQLite backups are in that release directory; rollback may never overwrite newer
player saves.
