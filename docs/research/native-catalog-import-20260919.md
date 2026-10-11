# Native Catalog Database Import, 2026-09-19

## Promoted Data

The current client's 144 `Map_City_Coordniate` rows are now stored in both
configured SQLite databases, not only an atlas JSON or a research report:

- `config/server.json` -> `god2.db`.
- `config/recovered-world-entry.json` -> `artifacts/recovered-accounts.db`.

Source: `Data2/Patch/Comm/gamedata.csvZ`, SHA256
`70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731`.
Decoded SHA256:
`75c3c37947a64b0917fbf8e546884d9bf893fe6a606d3e2b8f3b1857966b1815`.
Native reader/lookup: `59A80` / `59D80`, current pinned image
`149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
The prior `current_world_scene` loader executes original row writes for all
144 records. `world_atlas.parse_catalog` retains original byte fields and
source line/record identities. Retired archives are not inputs.

Migration 4 adds `native_data_sources` and `native_map_catalog`. Dataset
`current-map-catalog-v1` retains compressed/decoded/build hashes, section,
reader addresses, record index, line number, record hash, raw record bytes
(excluding the line terminator), and proven area/scene/kind selectors.
Other raw fields are not relabeled as gameplay rules. In particular, catalog
coordinates do not establish player/NPC/monster spawn positions.

## Import and Verification

`tools/strike_lab/import_native_catalog.py` validates the pinned source before
writing. `god2-server --migrate-only` runs the existing immutable-history
migration manager without logger, Lua or network startup. The importer takes
a SQLite online backup, runs the server migration, then atomically imports
all records under `BEGIN IMMEDIATE`. A byte-for-byte readback, foreign-key
check and quick integrity check precede commit. An identical second import
is a no-op. Conflicting source/records or incomplete datasets fail, without
silently overwriting or filling values. A failed row insert rolls back both
the source and all newly inserted rows. Schema migration is a separate
transaction and can remain applied if the later data import fails.

Executed successfully:

```powershell
python -B -m tools.strike_lab.import_native_catalog --config config/server.json
python -B -m tools.strike_lab.import_native_catalog --config config/recovered-world-entry.json
```

Each command reported `inserted=144`, `rows=144`. Backups:

- Default DB: `artifacts/db-backups/native-catalog-34b48d332e4d403d85c7a920d8561523.sqlite`.
- Recovered DB: `artifacts/db-backups/native-catalog-55f4bb175b4a460892ee28486b4ef999.sqlite`.

Read-only comparison against those backups confirmed unchanged rows in
accounts, characters, recovered_characters and recovered_positions in both
databases. The older default DB did not yet have the latter tables; migration
created them empty. Both targets reported `quick_check=ok` and 144 catalog rows.
Backups contain private account state and are not research/public artifacts.

Six importer tests passed, covering native-byte roundtrip, idempotence,
conflicting provenance, partial/corrupt datasets, injected row failure rollback,
source-pin rejection, outer-transaction rejection and unchanged account data.
They migrate temporary databases using the production server executable. The
sixth test starts the actual recovered-mode server with a test Lua bootstrap,
reads every original record through the production database callback, and checks
all 144 raw records and provenance fields. See `native-catalog-lua-20260919.md`.

The C++20 `NativeMapCatalog` reader is compiled into `god2_core`. Its standalone
test passes owning-result, missing-versus-corrupt, bounds/types, provenance join,
orphan, duplicate and statement-lifetime checks. Main added the invariant
`source_record_index < row_count`. SHA checks in this reader validate shape;
cryptographic source/record identity is checked by the importer, not this reader.

## Still Open

Storage, C++ read access and the Application-owned Lua callback are implemented
and tested. Session/world policy is not yet switched to this catalog, and this
import does not certify a live map,
spawn position, combat rule, growth table or original-client world acceptance.
Those remain active goal requirements, not completed features. Original data
must continue through integration and applicable live acceptance before the
corresponding gameplay feature is marked restored.
