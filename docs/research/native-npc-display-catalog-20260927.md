# Full current NPC display catalog in SQLite

Date: 2026-09-27. Authority: `SOURCE_DISPLAY_ONLY`.

All **4,043** `NPCAppearData` rows are qualified against the current compressed source and the accepted saved process-memory receipt. This is the entire section, with direct keys up to 6224. It is not restricted to the four FruitVillage NPCs. No location, facing, spawn, quest rule, combat stat, or server-written cache tail is imported.

## Native and source contract

Current loader VA `004570F0` writes a direct-index record at catalog owner `+0x121EA + key*94`. The static prefix is 28 bytes:

| Offset | Width | Retained field |
|---|---:|---|
| `+00` | 16 | Raw fixed-width display name, including native truncation/NUL |
| `+10` | 2 | Flags: source field 3 low14, field4 lowbit at14, code5001..5003 sets15 |
| `+12` | 2 | Source appearance code |
| `+14` | 2 | Body component |
| `+16` | 2 | Face component |
| `+18` | 2 | Head component |
| `+1A` | 2 | Weapon component |

For codes 5001–5003 the native loader packs fields5..8 into head/face/body/weapon respectively. The importer reproduces these writes and long-name truncation, then compares **all 28 bytes for every row** to the saved native 94-byte record prefix. Source records 1156 and 3472 contain only five fields; their observed static prefixes still match exactly. The default-zero bytes used in the projection are qualified by this complete comparison, not assumed to be generic initialization guarantees for another build.

The 66-byte suffix is deliberately excluded. `0045BA30` writes server F8 cache information there; importing it as native NPC stats would misclassify received or unspecified state. Native layout evidence: `current_memory_catalog_layout_20260927.py`, current `004570f0` disassembly/decompilation and `artifacts/research/memory-catalog-layout-20260927/evidence.json`.

Pins:

- Source: `Data2/Patch/Comm/gamedata.csvZ`, SHA `70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731`.
- Decoded SHA: `75c3c37947a64b0917fbf8e546884d9bf893fe6a606d3e2b8f3b1857966b1815`.
- Receipt: `artifacts/research/live-memory-references-20260927-02/memory-result.json`, SHA `1f3de6e0f62c340b20447c3b868907103b01caa64074688ebf47e9b5c725930a`.
- Receipt-associated current client: `6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98`.
- Qualified dataset SHA: `b770c11e516b488adba54ab7b2bee5d1fee3eaf1c5deb3dafe2e22962ccd343c`.

The dataset digest covers all rows ordered by key. Each row contributes little-endian `key:u16, source_line:u32, decoded_offset:u32, raw_length:u32`, followed by the exact CP950 raw source line without its line ending, then prefix28. Each raw record also has a separately verified SHA. Memory addresses, process identifiers and mutable suffixes are not catalog fields.

## Implementation and integration

`NativeNpcDisplayCatalog(sqlite3*)` checks the connection without querying tables. `schema()` supplies independent `native_npc_display_sources` and `native_npc_display_rows` DDL for parent migration33 integration. `count()` returns zero only for a completely empty catalog. `lookup(uint16_t key)` returns an optional source-bound record; unknown keys return no record only after whole-catalog validation.

Every call validates the exact source metadata, all 4,043 row hashes, cardinality, ordering/bounds and aggregate digest in one consistent read transaction. Missing rows, orphan rows, extra source rows, changed raw bytes, changed prefix, or altered provenance throw `DatabaseError`. The reader borrows an existing transaction without committing it. BCrypt SHA256 is linked on Windows; unsupported platforms fail explicitly. Return fields include full source bytes, line/offset/hash, prefix28, name16, flags and six display words. No encoding conversion discards original bytes.

`tools/strike_lab/import_native_npc_display.py` verifies compressed/decoded source pins, the entire receipt hash, accepted receipt status, unique source/memory keys, source line and record hashes, and the exact prefix comparison before starting a write transaction. It inserts both tables atomically, verifies exact readback and database integrity, and is idempotent only for byte-identical data. Conflicting or incomplete data is rejected, not repaired or replaced. Source-only import performs no player-row writes.

Explicit invocation after migration:

```powershell
python -m tools.strike_lab.import_native_npc_display --database <explicit-existing-disposable-or-reviewed-target.db>
```

`--client` and `--memory-receipt` override locations without weakening pins. `--install-schema` explicitly creates these two tables for isolated imports. The importer does not discover a production config, run migrations, launch a process or open process memory. Backup/release selection and formal promotion are parent responsibilities.

## Verification

- Python source/memory full match: **4,043 / 4,043**.
- `python -m unittest tests.research.test_native_npc_display`: **7 PASS**.
- `python -O -m unittest tests.research.test_native_npc_display`: **7 PASS**.
- Independent MSVC C++20 `/W4 /WX /O2 /DNDEBUG` build: PASS.
- Standalone `test_native_npc_display.cpp`: full count, representative lookup including component/short rows, unknown lookup, six corruption/rollback cases, empty catalog and borrowed transaction checks: PASS.

The C++ fixture is an explicitly marked disposable SQLite database populated by the real importer; tests reject an unmarked database. Independent artifacts were placed under system temporary `god2-npc-display-20260927`. No shared server executable, production database, client memory, client files or desktop were modified. This report establishes source/catalog integration readiness; formal database promotion and gameplay NPC placement remain separate claims.
