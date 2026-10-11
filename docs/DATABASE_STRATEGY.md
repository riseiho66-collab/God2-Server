# Database Strategy

SQLite is the implemented embedded backend. MySQL/MariaDB and an export utility are future work, not fallback implementations that silently write to SQLite. The connection enables foreign keys, uses a 5000 ms busy timeout and exposes repositories only after successful migration. Repository calls currently execute synchronously on the serial game executor.

## Boundary

Game logic -> AccountRepository / CharacterRepository -> Database abstraction -> backend implementation. Keep sqlite3 pointers, SQLite SQL and ROWID assumptions in src/db. Lua and handlers use narrow services/repositories, never raw SQL. InventoryRepository and QuestRepository are extension points until protocol/domain requirements are recovered.

Backend-neutral records need explicit ID widths, strings, timestamps and errors. Define not-found separately from backend failure, constraint failure and retryable contention. Verify ownership of selected characters against the authenticated account at the repository/service boundary.

## Initial Schema

Only accounts and characters are in initial scope. Proposed SQLite migration:

~~~sql
CREATE TABLE accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE characters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    level INTEGER NOT NULL DEFAULT 1,
    job INTEGER NOT NULL DEFAULT 1,
    hp INTEGER NOT NULL DEFAULT 100,
    mp INTEGER NOT NULL DEFAULT 50,
    map_id INTEGER NOT NULL DEFAULT 1,
    x INTEGER NOT NULL DEFAULT 100,
    y INTEGER NOT NULL DEFAULT 100,
    created_at TEXT NOT NULL,
    FOREIGN KEY(account_id) REFERENCES accounts(id)
);
CREATE INDEX idx_characters_account_id ON characters(account_id);
~~~

This is a design example, not an executed migration. Use migration history/version checks rather than assuming CREATE TABLE IF NOT EXISTS verifies an existing schema. Enable and verify foreign-key enforcement per connection before transactions. Parameterize statements. Choose and document busy handling, transaction ownership and connection/thread policy. WAL is an optional deployment decision requiring its own backup/checkpoint policy.

Current mock login discards the supplied password and creates accounts with password_hash=!MOCK-NOT-A-PASSWORD-HASH!. This is a marker, not a credential hash. Empty payload selects username mock; otherwise any field-valid username is accepted without real authentication. SQLite generates account and character IDs: TestPlayer is a default name, not fixed ID 10001. Mock auth requires a loopback bind; default host is 127.0.0.1. Real authentication is unsupported.

## Migrations And Transactions

The migration manager stores consecutive version identifiers, names, full SQL text and application timestamps in schema_migrations. It compares applied names/SQL against the compiled migration list, rejects changed history or a newer schema, applies pending migrations in a transaction and performs foreign-key/quick integrity checks before commit. Append migrations rather than rewriting applied entries. Test clean creation, already-current startup, older-schema upgrade and rollback on injected failure.

Account creation and associated default-character creation need a defined transaction boundary. Update position/map/hp/mp consistently, with clear ownership of write ordering and recovery on disconnect. Avoid blocking database work directly in network callbacks. Bound the work queue and account for canceled sessions.

## Backend Portability

| Concern | SQLite now | MySQL/MariaDB later |
| --- | --- | --- |
| IDs | Signed integer range; generated in repository | BIGINT-compatible IDs; preserve shared range |
| Strings | TEXT with application validation | Explicit VARCHAR limits and matching charset/collation |
| Time | Canonical UTC text policy | Explicit UTC DATETIME conversion policy |
| Constraints | Enable foreign keys per connection | Foreign keys and indexes in backend migrations |
| Transactions | Explicit write transaction/lock policy | Pool and transaction isolation policy |
| Generated IDs | Backend adapter retrieves ID | Backend adapter retrieves ID |
| SQL dialect | Internal SQLite migration/repository SQL | Separate backend implementation |

Username case/normalization and uniqueness must remain consistent across backend collations. SQLite generates IDs; do not assume fixed account/character values or narrow persisted IDs to match examples. Mock wire IDs are checked before uint32 conversion; real wire ID width must be independently recovered.

## Export Gate

SqliteToMysqlExportTool remains a placeholder until it supports schema version checks, a consistent read snapshot, typed/escaped serialization or bound inserts, ID preservation, dependency order (accounts before characters), count/checksum verification, orphan detection, collision policy and a migration report. Test import into an empty target and repeat/failure behavior before retiring SQLite. Protect the source and keep a rollback path.

## Roadmap

1. SQLite, accounts/characters, migrations and mock repositories.
2. Real login/list support and character persistence.
3. Persist world map/position/hp/mp with defined save semantics.
4. Inventory schema after inventory packet/domain recovery.
5. Quest schema after quest flow recovery.
6. Battle/monster/drop schema after battle recovery.
7. MySQL/MariaDB repository and migration implementations.
8. Validated SQLite export/import.

Do not pre-design full inventory, equipment, shop, guild, mail or auction schemas from another game.
