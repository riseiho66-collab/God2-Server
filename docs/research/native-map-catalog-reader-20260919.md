# Native map catalog reader, 2026-09-19

## Scope

`god2::NativeMapCatalog` adds a SQLite read boundary for stored native map catalog
records. It does not enable runtime C++ or Lua consumption, map selection, spawn
selection, coordinate interpretation, or any other gameplay behavior. No retired
source or actual database contents were used to implement this reader.

The constructor borrows a non-null `sqlite3*`. The caller retains connection
ownership, lifetime, and synchronization responsibilities. Every lookup creates
and finalizes its own statement through the existing `SqliteSupport` helpers.
The reader performs no writes, migrations, external file reads, or transactions.

## Schema and API contract

The reader expects main's default SQLite migration 4 to provide these non-null
columns:

- `native_data_sources`: `dataset_id TEXT` primary key, `source_path TEXT`,
  `source_sha256 TEXT`, `decoded_sha256 TEXT`, `native_image_sha256 TEXT`,
  `source_section TEXT`, `loader_rva TEXT`, `lookup_rva TEXT`, `row_count INTEGER`.
- `native_map_catalog`: `dataset_id TEXT` foreign key to the source,
  `source_record_index INTEGER`, `source_line INTEGER`, `record_sha256 TEXT`, `raw_record BLOB`,
  `area INTEGER` in 1..16, `scene INTEGER` in 0..1023, `kind INTEGER` in 0..3.
  Primary key: `(dataset_id, source_record_index)`. Unique key:
  `(dataset_id, area, scene)`.

`NativeMapCatalog::current_dataset_id` is `current-map-catalog-v1`.
`lookup(dataset_id, area, scene)` accepts signed 64-bit selectors to check bounds
before any narrowing. The dataset must be nonempty, contain no NUL, and fit the
SQLite text binding limit. Parameters are bound, never interpolated into SQL.

The result is `std::optional<NativeMapRecord>`:

- No matching catalog key returns `std::nullopt`, including an unknown dataset.
- A match returns owning strings and a byte vector, including every stored source
  provenance field, record index, source line, record hash, and bounded selectors.
- Invalid input, corrupt matched data, duplicate matches, and SQLite errors throw
  the existing `DatabaseError`; they never become a missing result.

The query uses one left join and `LIMIT 2`. A matching catalog record without its
source is rejected, even if foreign key enforcement was disabled. A second
joined result is rejected. The normal lookup uses the schema's unique selector
index; it does not enumerate the dataset or verify unrelated records.

All returned columns are checked for exact SQLite storage type before conversion.
Record indexes must be in 0..32766; source lines must be positive and a matched
source's declared row count must be in 1..32767. Raw records must be BLOBs of
1..4095 bytes and are copied without interpretation. These limits match migration
4. Source text fields must be nonempty and NUL-free. SHA-256 fields must contain
exactly 64 lowercase ASCII hexadecimal characters, also matching migration 4.

Hash validation is shape validation, not cryptographic recomputation or proof of
native origin. The source path, section and RVA text are preserved, not resolved
or interpreted. The reader does not assert dataset completeness, recount rows,
or infer a relationship between source line and declared row count. Main added
and tested the required record-index-less-than-row-count invariant.
No raw bytes are decoded as coordinates or spawn values. Authentic source
verification, digest computation, and transactional import remain importer work.

## Standalone test handoff

`tests/test_native_map_catalog.cpp` owns its `main`. Main should exclude it from
the aggregate test source glob and register a separate executable, using C++20,
SQLite, and these implementation units (or their existing library target):

- `src/db/NativeMapCatalog.cpp`
- `src/db/Migration.cpp`
- `src/db/SqliteMigrationManager.cpp`

Every fixture opens only `:memory:` and migrates through
`default_sqlite_migrations()` / `SqliteMigrationManager`. Missing migration 4 is
an explicit test failure. Fixtures label their paths, section, and raw bytes as
test-only synthetic data; their hashes and RVAs are synthetic placeholders.

Tests cover empty and missing results, selector/storage endpoints and invalid selectors,
parameter binding, exact provenance and embedded binary-byte preservation,
independent result copies, statement cleanup, connection lifetime, query-only
operation, dataset isolation, orphan rejection, malformed types and bounds,
hash shape, NULL results, duplicate records/sources, and SQLite schema errors.
CHECK bypasses and temporary shadow views deliberately expose corrupt rows to
the reader without modifying migration definitions. The temporary views also
exercise REAL selectors that SQLite INTEGER affinity would otherwise normalize.

Main registered `native_map_catalog`, compiled it under the shared C++20 build,
and ran its CTest successfully. This delegated change does not
edit CMake, migrations, the importer, or any real database. Storage/read readiness
does not enable a runtime feature or certify the dataset's provenance.
