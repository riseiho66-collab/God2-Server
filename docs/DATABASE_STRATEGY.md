# Database architecture and owner requirements (2026-10-15)

This document supersedes the historical accounts/characters-only design example. It describes the actual current source and the owner's migration/configuration requirements; planned features are not installed storage or verified imports.

## Current source status

SQLite is the implemented backend. The ordinary migration history reaches49; explicitly qualified guild branches extend50..53. Native delivery, inventory, PK, beast, learning and other storage can be installed through separate explicit extension contracts. The source declaration dictionary contains123 distinct literal table names, including optional, historical and transient migration tables. This is not a live database inventory.

MySqlDatabase and MySqlMigrationManager remain unsupported. SqliteToMysqlExportTool::export_sql(Database&,path) still refuses full database export until an actual consistent source reader and complete audited schema mappings exist. The new write_mysql80_snapshot path formats a caller-owned typed image; it is not an actual SQLite snapshot reader, migration or target import validation. No live DB was opened or changed for this source phase.

## Physical names and per-table TXT documentation

All physical table and column identifiers use English/ASCII. Preserve existing identifiers and IDs until a separately reviewed reversible migration is actually needed. Chinese explanations belong in docs/database/tables/<exact_table_name>.txt, one file per declared table. Source metadata and emitted DDL comments refer to the English TXT filename. Player names, text and other legitimate Chinese data retain their original UTF-8.

Each TXT identifies the English table name, purpose, source/installation scope and the English-to-Chinese column meanings. Include actual type, units, limits and relations only where positively established. Unknown raw fields explicitly say their semantics are unconfirmed; do not turn an offset, word index or native byte sequence into a guessed gameplay property. Historical/optional/transient definitions are labeled separately from formal installed storage.

Native snapshots and source catalogs are not player-authoritative balance data. Preserve their full original bytes, build/record provenance and source hashes. Binary fields are deliberate binary storage, not arbitrary text; do not decode CP950/CP936 packets as UTF-8 or discard them merely to make a dump look readable. Known readable projections and TXT explanations are additive.

## Equipment and item definitions

The owner's intended editable definition model separates weapons, armor, treasures (法寶) and general items. Native category/type evidence determines mapping; names alone are insufficient. Do not put all definition-specific fields into one universal item-definition table.

A definition describes the base item. A player's individual equipment instance owns its instance ID, +N enhancement level, binding, durability and positively recovered additional properties. Different instances of the same base item can be +0/+1/+3 simultaneously. Weapon, armor and treasure enhancement parameters are distinct typed rule families; changing a base definition must not overwrite other players' individual states.

General medicines, materials, quest items and ordinary consumables share a readable general-item definition with explicit categories when their structure is the same. Split a special-item family only if its fields, ownership/instance lifecycle or rule model genuinely differ. Do not create a separate table for every display category. Armor subcategories follow actual native slots/types; treasure-specific growth is not assumed identical to ordinary armor.

Existing common bag, warehouse, trade, ownership and settlement ledgers remain shared. They reference qualified category/definition/instance identities and retain quantity, bind and ownership semantics. Definition separation is not permission to duplicate all ownership rows or bypass native IDs and saved constraints. New authoritative tables and enhancement formulas are planned: no physical tables were renamed, split or populated here.

## Data-driven core and reload behavior

Daily numerical adjustments must not require recompiling the C++ core. Move positively recovered skill costs/multipliers, equipment/treasure enhancement parameters, monster definitions, drop rates, EXP curves, shop prices and quest rewards into clear typed domain tables, rather than opaque machine-code/JSON payloads or a universal untyped key-value table.

C++20 owns networking, native layout, authoritative state, transactions, checked64 arithmetic and the backend-neutral repository interfaces. Lua owns gameplay rule execution. Both read the same actual versioned configuration snapshot; the native client BIN evidence remains the default formula/data authority. Editable custom overrides must keep an explicit design/provenance marker and never overwrite the original native evidence.

The intended load flow is: one consistent read -> validate the complete candidate -> publish one immutable configuration version. A battle, settlement or transaction retains its selected version through completion. Invalid or incomplete reloads retain the previous complete version; no half-new parameters. Do not issue SQL for each packet or hit. Configuration documents must state whether a change takes effect at reload, next battle/login or service restart. New wire formats and fundamental systems can still require C++ changes.

This reload service and domain-table promotion are not yet implemented. MySQL support requires actual backend repositories and migrations, not simply changing the connection string or converting a dump. SQLite and MySQL must use the same common authoritative tables and gameplay interfaces; incompatible protocol snapshots retain the existing _tw/_cn scope where necessary.

## MySQL8.0 export contract

The export target is MySQL8.0, with explicit reviewed minor-version/capability requirements. The initial typed format uses MySQL8.0.17+ with utf8mb4_0900_bin and an explicit16KB InnoDB-page capability. Identifiers remain English, DDL comments point to per-table TXT, and genuine Chinese cell values remain UTF-8. Signed/unsigned64 values serialize as exact decimal integers; native binary cells serialize as hex bytes. No narrowing, floating-point/JSON number conversion, prefix-key truncation or text replacement.

A real export must use one existing-file READONLY connection and one consistent snapshot, without initialize(), migrate(), schema installation, SQL writes or gameplay owners. Capture all installed tables, columns, PK/UNIQUE/FK/CHECK constraints, indexes, triggers/views, optional extension/version identities, sqlite_sequence high-water values and complete typed rows. A missing audited mapping refuses the export; it must not silently drop a trigger or constraint.

Current SQLite schemas include typeof/GLOB/instr/substr/hex/printf/strftime checks, partial unique indexes, trigger-based cleanup/collision rules, composite foreign keys and WITHOUT ROWID layouts. These cannot be converted safely by global string replacements. SQLite migration sql_text remains original source history and must never be treated as the MySQL backend's migration history.

The typed formatting slice supports explicit PK/UNIQUE models only. It owns all image containers before invoking output streams, validates types/UTF-8/widths/NULLs/key duplicates and target limits before first output, and sorts rows by the full typed primary key. It does not claim to map arbitrary SQLite constraints, validate an actual read snapshot, certify source digests, publish an output file atomically, or verify a target import.

Full file export requires a fresh exclusive temporary output, no overwrite or source/WAL/SHM/journal aliases, complete source-count/digest reports and no-replace publication. MySQL DDL is not transactionally rolled back with the data. Target must be fresh/empty, preserve IDs/sequences, retain referential actions and check orphans. Disabling foreign-key checks and re-enabling them alone is not proof of validity. Real import/reload/backend tests remain deferred to the authorized concentrated verification phase.

Primary references:
- https://dev.mysql.com/doc/refman/8.0/en/hexadecimal-literals.html
- https://dev.mysql.com/doc/refman/8.0/en/charset-binary-collations.html
- https://dev.mysql.com/doc/refman/8.0/en/innodb-limits.html
- https://dev.mysql.com/doc/refman/8.0/en/create-table-check-constraints.html

## Preservation and acceptance

Preserve accounts, saves, ownership, transactional histories and all frozen features. No destructive schema cleanup is implied. Keep C++/Lua ownership, original native source hashes, shared64 domains, the exact coin cap99999999999/stack99/native levels, 453 Traditional primary skill names/client formulas/current-maximum-HP poison10th and common TW/CN/four browser support.

PHASE1 is source integration only: no product/database/export execution, SQL reads/writes against an actual database, builds/tests, runtime migration, import, activation or deployment. A completed formatter/dictionary is not a completed MySQL backend, data-driven gameplay integration or TW100%.