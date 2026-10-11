# Native Catalog Lua Read Access, 2026-09-19

Production code now supports read-only access to the existing native catalog
through an injected C++ callback. Main completed Application wiring and CMake
registration after the bounded worker delivery. No world policy, spawn inference,
game formulas, network/UI behavior, or actual native experiments are added.

## Formal Integration Verification

`Application.cpp` now installs the callback below after migration, on the existing
game-thread scope. The database outlives Lua. `tests/CMakeLists.txt` registers the
standalone `native_catalog_lua` target and excludes its main from the aggregate.
Release builds of `native-catalog-lua`, `god2-server` and `god2-tests` passed.

`test_formal_recovered_server_lua_reads_all_original_records` in
`tests/research/test_import_native_catalog.py` migrates a temporary database using
the production binary and imports the pinned 144 original records. It then starts
the actual Release server with recovered mode and a test bootstrap that reads
every record through Lua, checking exact selectors, raw bytes, indices, source
lines and hashes. The test verifies fixture mode is false, the success marker
`NATIVE_CATALOG_ALL_144_VERIFIED`, unchanged account/catalog records, and a clean
bounded server exit. Ports are ephemeral; no live original client participates.

Focused CTest passed 5/5 in 7.58 seconds: `native_catalog_lua`,
`import_native_catalog`, `lua`, `database`, and `application_startup`.
The importer suite now contains six tests, including this formal startup check.
Data access is connected; scene selection, spawn policy and playable-world
acceptance remain separate uncompleted work.

## C++ API and Application Hookup

`SqliteDatabase::native_map_catalog() const` returns
`const NativeMapCatalog&`. It checks `migrated_`, including after a failed
remigration, just like the repository accessors. The reader is constructed with
the repositories and destroyed before the SQLite connection. The borrowed reader
must not outlive its database; returned records own their bytes and provenance.

The third constructor argument is optional, preserving existing source callsites:

```cpp
using NativeMapLookup = std::function<std::optional<NativeMapRecord>(
    std::int64_t area, std::int64_t scene)>;

explicit LuaEngine(std::filesystem::path script_root = "scripts",
                   bool fixture_mode = true,
                   NativeMapLookup native_map_lookup = {});
```

The installed construction in `src/core/Application.cpp`, after database
initialization and migration, is:

```cpp
LuaEngine lua(config.script_root, fixture_mode,
    [&database](std::int64_t area, std::int64_t scene) {
        return database.native_map_catalog().lookup(
            NativeMapCatalog::current_dataset_id, area, scene);
    });
```

The existing `SqliteDatabase.h` include exposes the catalog type. Keep `database`
declared before `lua` in the game-thread scope so Lua and all its callbacks are
destroyed first. Do not catch database errors and convert them to `nullopt`.
For another host lifetime model, capture an owning `shared_ptr<SqliteDatabase>`,
or lock a weak pointer and throw when its source has expired.

LuaEngine owns a single callable instance shared by all active/staged VMs. Each
binding captures ownership by value and obtains its Lua state at invocation;
it never captures a constructor-local reference or a prior VM. Callback state
survives successful reload, runtime-error reload, and syntax-error reload.
Failed reload preserves the previous VM and registrations. Calls made while
staging a rejected script still happened: arbitrary host callback side effects
are not rolled back, so production callbacks must remain read-only.
Initialization, invocation, reload and destruction retain the existing same
game-executor-thread contract. Borrowed callback dependencies remain the host's
lifetime responsibility.

## Lua Contract

```lua
local record = native_map_catalog(area, scene)
```

Exactly two numeric, finite, integral arguments are required. Area is `1..16`,
scene is `0..1023`. Integral numeric values such as `1.0` are accepted; strings,
booleans, tables, functions, nil, fractions, NaN, infinities, extra arguments,
and out-of-range values are rejected before calling the host. The host chooses
the dataset; Lua cannot select a dataset, connection, SQL query or filesystem path.

- A matched row returns a newly allocated owning snapshot table.
- A valid absent key returns `nil`.
- An empty callback raises `native_map_catalog unavailable`, in either runtime mode.
- Callback/database exceptions become Lua errors, catchable with `pcall`.
  Uncaught errors retain existing host behavior: script transactions fail,
  protected command/quest calls throw, and event dispatch logs failures.

The snapshot contains exactly these original record fields:

| Field | Lua Value |
| --- | --- |
| `area`, `scene`, `kind` | Integer selectors from the record |
| `source_record_index`, `source_line` | Original integer identities |
| `record_sha256` | Stored hash text |
| `raw_record` | Binary-safe string, preserving NUL and non-UTF-8 bytes |
| `source` | A new provenance table described below |

`source` contains `dataset_id`, `source_path`, `source_sha256`, `decoded_sha256`,
`native_image_sha256`, `source_section`, `loader_rva`, `lookup_rva`, and `row_count`.
All strings and integers are copied; the configured Lua 5.4 integer build retains
the full signed 64-bit source line. No SQLite handle, userdata, setter, live C++
reference, filesystem operation, or inferred gameplay field is exposed.
Scripts may edit their own tables, including the nested source table, without
changing SQLite, another snapshot, or future lookups. Read-only describes access
to the catalog, not an immutable Lua-table metatable.

The C++ reader checks hash *shape*, not cryptographic identity. The Lua binding
passes through the stored provenance and makes no verification claim. Importer
verification remains documented in `native-catalog-import-20260919.md`; exposing
a record does not certify spawns, gameplay rules or live world acceptance.

## Standalone Test Registration

`tests/test_native_catalog_lua.cpp` owns `main()`. Before the `god2-tests` target
is declared, CMake excludes it from the glob and registers a standalone
target linked to the existing core and its transitive dependencies:

```cmake
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_native_catalog_lua\\.cpp$")

add_executable(native-catalog-lua test_native_catalog_lua.cpp)
target_link_libraries(native-catalog-lua PRIVATE god2_core)
add_test(NAME native_catalog_lua COMMAND native-catalog-lua)
set_tests_properties(native_catalog_lua PROPERTIES TIMEOUT 30)
```

After registration:

```powershell
cmake --build build --config Release --target native-catalog-lua
ctest --test-dir build -C Release -R '^native_catalog_lua$' --output-on-failure
```

Tests create private temporary SQLite files, run the production migrations, and
insert explicitly synthetic records, binary data, and invented shape-valid hashes.
The provenance path intentionally names no real source file. No live database,
original archive, retired corpus, or native runtime is used.

Coverage includes migration guards and failed remigration; empty catalogs;
complete raw/provenance snapshots; maximum selector and signed integer values;
strict input validation before host invocation; missing rows; corrupt stored
hash text and missing SQL tables; caught and uncaught errors; unavailable access
in both modes; thread rejection; mutable callback state and dependency lifetime
across successful and failed reloads; release of captured database ownership;
snapshots after data deletion and database closure; and snapshot mutation without
SQLite writes (byte-for-byte database comparison and unchanged `data_version`).

Validation passed on 2026-09-19: isolated MSVC x64 C++20 `/O2 /MD /W4` build of
the standalone test and current LuaEngine, LuaRegistry, ScriptBindings,
SqliteDatabase, NativeMapCatalog, Migration, SqliteMigrationManager and three
SQLite repository sources. Linked only the existing Release Lua, SQLite and
spdlog dependencies. Compilation succeeded; the only warnings were the existing
sol2 header C5321 UTF-8 escape warnings. No shared build outputs were modified.

Execution exited 0 and printed
`Native catalog Lua checks passed (test-only synthetic data)`.
Error logs for invalid inputs, corruption, missing tables, unavailable callbacks,
rejected reloads and a closed source are intentional assertions in this test.
All five test groups passed. Temporary fixture databases/scripts were removed by
the test. This was the worker's isolated validation; main subsequently completed
the formal hookup/build and original-record startup test described above.
No live world or native-client acceptance is claimed.
