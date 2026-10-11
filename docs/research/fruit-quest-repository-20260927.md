# Owned FruitVillage collection quest repository

Date: 2026-09-27. Authority: **CUSTOM-0051**. This report covers repository and source-import verification; it does not establish deployment or actual-client acceptance.

## Authority and boundaries

The repository accepts only the immutable recipes in `FruitVillageQuestRules`: missions 234, 236, 237 and 238. Their source bundle distinguishes original quest/NPC/material/dialogue text from adopted historical reward/level information and inferred server policy. The bundle does not recover original server task rules. No additional rule, currency reward, item reward, automatic material grant or native reward formula is accepted.

Persisted position must be area 13, scene 12 and within three units on each axis of the selected recipe's NPC coordinate hint. This range and its use for admission are CUSTOM-0051 policy. A source coordinate hint is not proof of a native world NPC instance. Pending battle blocks mutation. Repetition is once per character and recipe revision.

## Integration API

`src/db/SqliteFruitQuestRepository.{h,cpp}` exposes:

```cpp
SqliteFruitQuestRepository(sqlite3*, SourceGuard);
View load(account, character, mission);
Commit accept(account, character, mission, const View& expected, Prepare = {});
Commit submit(account, character, mission, const View& expected, Prepare = {});
static const char* schema() noexcept;
```

Supply the mandatory guard as a callback calling `NativeFruitQuestSources(raw).require_qualified()`. Constructors check arguments without querying tables or invoking the guard, permitting construction before migrations. Each operation invokes qualification. `load` is read-only and returns the complete comparison snapshot. Mutation requires that exact snapshot to still match inside the write transaction.

`Commit` contains before/after views, encoded journal logical bytes, changed bag slots, and XP/reputation deltas. Send projections and notices **after the method returns successfully**. Optional `Prepare` permits pre-encoding reply buffers before commit; it must perform no network send, transaction reentry or database write. A throwing callback, any callback database write, or changed readback aborts the transaction.

`schema()` supplies the two migration-31 tables `character_fruit_quest_balances` and `character_fruit_quest_progress`. The former stores reputation, fixed-zero currency and revision. The latter stores phase, rule revision, pinned bundle hash and an immutable completion receipt with XP/reputation before, after and delta, plus whether an XP baseline existed. Both retain design `CUSTOM-0051`.

## Atomic state contract

- Ownership comes from `recovered_characters`; saved logical 22 and its revision supply role level. Role bytes, HP/MP and the saved role revision are preserved.
- Existing `character_experience` absolute XP retains its `CUSTOM-0012` provenance. Missing XP reads as explicit initial zero without inserting a row during load. Completion records its delta separately under CUSTOM-0051; it does not relabel the baseline.
- Missing quest balances remain virtual zero during load. Explicit acceptance initializes the zero balance row. It grants neither materials nor XP.
- All 30 bag rows must be explicit. Missing rows are not empty slots. Counts are bounded by 127. Occupied 20-byte instance overlays prevent scalar material consumption, including overlays with a matching material key. Overlay state is part of stale-state comparison.
- Acceptance requires a free journal slot and no existing occurrence of the selected mission. It inserts `(1 << 16) | mission`. Submission removes exactly that mission and preserves every other journal word. Existing nonzero words require a legal native description reference.
- The journal uses the existing CUSTOM-0041 table. A modified snapshot uses origin `CUSTOM_TEST_NOT_NATIVE`, the available non-native origin enum, with explicit CUSTOM-0051 operation provenance; it is never mislabeled as a native capture.
- `BEGIN IMMEDIATE` encloses source qualification, owner/state reread, exact expected-view comparison, pure transition planning, conditional writes and final readback. Stale state, wrong owner, replay, missing facts, unknown recipe, arithmetic overflow, failed SQL or failed preparation rolls back all changes.
- Completion consumes the exact recipe total across scalar slots, increments reputation by one, applies the exact adopted XP reward, persists the once receipt and updates the journal in the same transaction. No currency or item reward path is enabled.

## Immutable source qualification

`NativeFruitQuestSources.{h,cpp}` provides `populated()`, `require_qualified()` and its own `schema()` for migration 32. Empty is distinguishable from qualified, and never authorizes quest use. A deferred standalone read transaction is used; inside an existing repository transaction the reader borrows it without committing or rolling it back.

The single `qualified_fruit_quest_sources` row must match every metadata field and its actual BLOB SHA-256:

- Payload length: **30,421 bytes**.
- Payload SHA-256: `ab3e063564d0e7b351c3abab9e3475419c3a710ec9371b3de4d9b01f44a76541`.
- Current client SHA-256: `6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98`.
- Authority: `PINNED_SOURCE_AND_INFERENCE_BUNDLE`.
- Design: `CUSTOM-0051`.

The hash qualifies the complete immutable source/inference JSON, including provenance distinctions. The historical pinned bytes contain 577 CRLF line endings. The importer explicitly reproduces those bytes on all platforms; an LF-only serialization is a different payload and is rejected. The C++ reader computes the real BLOB hash with Windows BCrypt, rather than trusting the stored hash column. Other platforms fail explicitly until a qualified SHA implementation is supplied.

The repository separately verifies the 418-definition/2,014-description native quest catalog, its source identity, and exact definition/description raw bytes, line numbers and record hashes for all four recipes. Journal references are validated against that catalog.

`tools/strike_lab/import_fruit_quest_sources.py` regenerates the pinned bundle from the existing current-source tool, validates it before any write, and installs it in one transaction. Schema creation requires explicit `--install-schema`. Identical imports are idempotent; a conflicting row, invalid source, trigger failure or readback mismatch cannot replace qualified data or leave partial schema/data. The CLI requires an explicit existing database and rejects databases in the client tree. It performs no player-row writes.

## Verification and reproduction

The standalone C++ suite completed **305 checks**, compiled with C++20, `/W4 /WX /O2 /DNDEBUG`, using an isolated executable and database in the system temporary directory. Coverage includes all four recipes, split material consumption, complete database rollback after late SQL failure, preparation exception/write rejection, owner/replay checks, journal preservation/full journal, instance protection, source corruption, missing facts, two-connection stale state and disk reopen. Fixture role/bag values are synthetic; native quest definitions and descriptions are imported from actual pinned source files.

The CTest wrapper initializes a fresh marked temporary SQLite fixture, imports actual native quest catalogs and the qualified bundle, runs the executable, closes connections and removes its temporary directory. Both ordinary Python and optimized Python runs passed all 305 checks:

```powershell
python -B tests/research/run_fruit_quest_repository.py --executable <fruit-quest-repository.exe>
python -O -B tests/research/run_fruit_quest_repository.py --executable <fruit-quest-repository.exe>
```

The seven importer regression tests passed in both interpreter modes:

```powershell
python -m unittest tests.research.test_import_fruit_quest_sources
python -O -m unittest tests.research.test_import_fruit_quest_sources
```

They cover exact/idempotent import, explicit schema permission, truncated/extra/modified/LF-only payloads, conflicting stored bytes, insertion abort, post-insert corruption and refusal to take over an existing transaction. Mandatory checks remain active under `-O`.

The `fruit_quest_repository` CTest registration calls the wrapper with `$<TARGET_FILE:fruit-quest-repository>` inside the existing Python interpreter guard. Run after parent integration/build:

```powershell
ctest --test-dir build-town-visibility -C Release -R '^fruit_quest_repository$' --output-on-failure
```

These checks use disposable fixture databases and do not alter a production database, running server, client executable or desktop. Application routing, migrations, end-to-end TCP and physical-client acceptance belong to the parent integration and are outside this report's pass claims.
