# Current Original Skill Catalog, 2026-09-19

This lane promotes the confirmed identities and complete raw records from the
current GOD2 `Data2/Fight/Spg/cbspec2.bin` into formal SQLite storage. It adds no
names, costs, classification, formulas, learned ownership, or battle behavior.
Only the current source and `tools/strike_lab/current_skill_identity.py` supply
data authority. No other corpus or historical evidence supplies records or leads.

## Formal Application Integration

The production `Application` supplies a database-backed `NativeSkillLookup` to
`LuaEngine`. `native_skill_catalog(kind, definition_id)` returns an owning Lua
snapshot with original bytes and provenance, or nil for an absent valid key.
Wrong argument counts/types, nonintegral or out-of-range selectors, unavailable
providers and database errors fail rather than silently inventing a definition.
The callback is retained across successful reloads and failed staged reloads;
the existing game-thread ownership rule is unchanged.

`tests/test_native_skill_lua.cpp` checks binary-safe snapshots, malformed inputs,
provider errors, ownership, successful/failed reloads and thread affinity using
explicit synthetic records. `tests/research/test_native_skill_application.py`
separately migrates a temporary DB with the actual Release server, imports all
448 pinned originals, starts recovered mode and compares every raw byte, offset,
key, digest and provenance field through the real C++/Lua callback. Both passed.
No damage, multiplier or MP-cost field is synthesized. This proves data delivery,
not successful casting or native battle-formula reconstruction.

Main's final Release build passed. Selected CTest passed 46/46 in 115.39s,
excluding the five older artifact/gate/environment suites. The CTest importer
sets its C++ reader executable explicitly, so all 14 importer cases run without
skips. Separate actual-server loopback movement/persistence tests passed 9/9
in 25.867s; coverage audit passed 13/13. These are not original-client E2E proof.

After successful tests, main deployed migration 5 and 448 records to each of
`god2.db` and `artifacts/recovered-accounts.db`. Before migration, the CLI made
SQLite backups `native-skills-89f7a535bf364f7c83a85ce42b03cd2f.sqlite` and
`native-skills-b64119062fba415f96ea82b1302cc59f.sqlite` under `artifacts/db-backups`.
Those private backups may contain account data and must not be published.
Both backups and post-import databases were compared with in-memory pre-import
snapshots: accounts, characters, recovered characters, recovered positions,
map records and other provenance rows were unchanged. Both final datasets match
every original byte and digest; integrity and foreign-key checks pass.

## Pinned Source

| Property | Value |
| --- | --- |
| Dataset | `current-skill-catalog-v1` |
| Source path | `Data2/Fight/Spg/cbspec2.bin` |
| Source size | 112660 bytes |
| Source SHA-256 | `7676acd93f164d071f7681a3fe74de94d65892759dbf2e69e3c0f748423d2f51` |
| Decoded SHA-256 | Same as source: the file is uncompressed |
| Native image SHA-256 | `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763` |
| Loader / lookup anchors | `0x12d3b0` / `0x11c520` |
| Source header | Literal ASCII `1.03`, retained in shared `source_section` |
| Populated definitions | 448 |
| Counts for kind 0 / 1 / 2 / 3 | 121 / 129 / 87 / 111 |
| Record length | 110 bytes |

The proven key is `(kind, definition_id)`, with kind 0..3 and one-based ID 1..255.
The exact source offset is `8 + kind * 0x6e04 + (definition_id - 1) * 110`.
Record bytes 0 and 1 must equal ID and kind respectively. Bytes 2..109 remain
uninterpreted. Unpopulated keys are not synthesized. `source_record_index` is the
zero-based import ordinal in ascending `(kind, definition_id)` order, not a new
native field or selection slot.

## Storage and Reader

`src/db/Migration.cpp` appends migration 5, `native_skill_catalog`. Migration SQL
1..4 remains unchanged; the regression test records their SHA-256 digests.
Migration 5 creates an empty table and never fabricates source rows. It shares
`native_data_sources` provenance with the existing map catalog without refactoring
that catalog. Skill columns are `dataset_id`, `source_record_index`,
`source_offset`, `record_sha256`, `raw_record`, `kind`, and `definition_id`.
Checks enforce numeric bounds, exact offsets, 110-byte BLOBs, the first two raw
bytes, and lowercase SHA-256 text. Both ordinal and lookup identity are unique
within a dataset; provenance is a foreign key.

`NativeSkillCatalog::lookup(dataset, kind, definition_id)` returns an optional
owning `NativeSkillRecord`. `NativeSkillSource` has the same field names as
`NativeMapSource`. Missing valid keys return `nullopt`; invalid selectors, corrupt
matched records, orphaned source joins, duplicates, and SQLite failures throw
`DatabaseError`. The reader uses `SqliteSupport` strict type checks and performs
one joined query, reading at most two matches to expose broken uniqueness.
It verifies exact offsets and raw identity bytes, source bounds, and equal source
and decoded hashes. Hash strings are validated for format by the reader; source
and record digest computation and complete dataset comparison belong to the
importer. The other 108 raw bytes acquire no field semantics in either layer.

The catalog reader borrows its SQLite connection. Returned strings and byte
vectors remain valid after later queries, database mutation, and connection
closure. `SqliteDatabase::native_skill_catalog() const` exposes the const reader
only after successful migration. `NativeSkillCatalog::current_dataset_id`
provides the pinned dataset selector for main's integration.

Historical migration 4 allows some BLOB values through its provenance length
checks. Corruption tests intentionally retain those schema rules and require the
reader to reject the BLOBs as non-text. This does not weaken reader validation or
modify migration 4.

## Import Contract

`tools/strike_lab/import_native_skills.py` exposes `pinned_records(client_root)`
and `import_catalog(connection, client_root)`. It checks source containment,
exact size and SHA-256, decodes with the current identity module, checks all kind
counts and identities, and computes each raw record's SHA-256.

Imports require their own `BEGIN IMMEDIATE` transaction and migration 5. Identical
data is a no-write success. Conflicting provenance, changed records, partial
imports, and orphaned rows are rejected without replacement. The final comparison
includes all rows and provenance, followed by foreign-key and integrity checks.
Any failure rolls back the complete import, including trigger-induced changes.

The CLI follows `import_native_catalog.py`: validate original source first,
resolve the configured SQLite database, reject nonexistent/client-tree targets,
create an SQLite backup in `artifacts/db-backups/native-skills-<uuid>.sqlite`, run
the server with `--config ... --migrate-only`, then import and report JSON.
Deployment command, for main after review:

```powershell
python -B -m tools.strike_lab.import_native_skills --config <server-config.json> --client <current-God2-root> --server-exe <rebuilt-god2-server.exe>
```

The delegated worker did not touch configured databases. Main's reviewed
deployment is recorded in Formal Application Integration above.

## Validation and Integration

Private MSVC C++20 build passed with `/O2 /MD /W4 /WX /permissive-`, using the
existing SQLite library and an output directory under the system temporary
directory. `tests/test_native_skill_catalog.cpp` passed standalone. It covers
upgrade from migration 4, repeated migration, migrated accessor guards, owning
snapshots, missing keys, selector bounds, offset/raw-byte constraints, corruption,
strict types, duplicates, orphan joins, and SQLite errors.

All 14 tests in `tests/research/test_import_native_skills.py` passed with zero
skips when `GOD2_NATIVE_SKILL_READER_TEST` pointed to that private executable.
The suite uses temporary databases and actual pinned source bytes. It verifies
all 448 imported records, each digest and offset, idempotence, conflicts,
transaction rollback, shared map/account preservation, immutable migrations,
source failures before writes, and backup-before-migration ordering. Its optional
C++ bridge checks all 1020 admissible keys, including the 572 absent keys, and
compares every populated raw record to the source through read-only lookup.
The CLI migration call is mocked in that isolated workflow test; actual server
migration/Application/Lua validation belongs to main's integration suite.

```powershell
$env:GOD2_NATIVE_SKILL_READER_TEST = '<native-skill-catalog.exe>'
python -B -m unittest discover -s tests/research -p test_import_native_skills.py -v
```

Main owns CMake target registration, Application/Lua hookup, the separate
`test_native_skill_application.py`, full builds, and deployment. Main reported
its Release build and actual-original Application/Lua test passed before the
final standalone corruption-test correction; those results are not substituted
for main's final rebuild. This lane edited only the assigned DB sources, new
importer, two new tests, and this document.
