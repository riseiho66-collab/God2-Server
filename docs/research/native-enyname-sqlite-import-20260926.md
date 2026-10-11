# Current-client EnyName display identities in SQLite

The current client `Data2/Patch/Comm/gamedata.csvZ` is pinned at SHA-256
`70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731`.
Its `EnyName` loader at RVA `0x5a1a0` and lookup at `0x5a0a0` establish an
area/scene/ordinal **display** selector. The decoded catalog contains 7,815
source occurrences. The repeated area generation supersedes 24 occurrences,
leaving 7,791 visible selector rows. Area 2, scene 0 (Island01) has 27 visible
rows. The source label is retained verbatim but is not a proven global monster
identifier.

Migration 20 adds `native_enemy_display_catalog`; each row retains source line,
decoded offset, raw record, row SHA-256, raw name bytes, generation and lookup
visibility. `native_data_sources` retains the current source and image hashes.
`tools/strike_lab/import_native_enemy_display.py` verifies the pinned source
before writing, creates a SQLite backup, imports transactionally, refuses a
conflicting catalog and can be rerun without duplicating rows. C++
`NativeEnemyDisplayCatalog::lookup` reads only the final visible selector row.
`resolve_normal_enemy_display` decodes the qualified normal-enemy `S2C 1C`
area/scene/ordinal fields into that SQLite lookup. It rejects other variants.

Verification on 2026-09-26 used a SQLite online backup of `god2.db` at
`artifacts/playtests/native-enyname-import-20260926-01/isolated.db`. The import
reported 7,815 rows, of which 7,791 are visible and 24 superseded. C++ read
back Island01 ordinals 1 and 27 with the expected source lines and name bytes;
ordinal 1 was resolved through a 45-byte `S2C 1C` identity record;
ordinal 28 was absent. A second import inserted zero rows; changing one row in
an in-memory copy caused a conflict rejection. `quick_check` and
`foreign_key_check` passed. All rows in 21 pre-existing tables, excluding the
new source declaration and migration ledger, matched the pre-import backup.
The `native_enemy_display_catalog` and `import_native_enemy_display` CTests
passed (2/2). Port 2592 was not restarted.

This is a server-side **display identity source**, not an encounter or combat
implementation. No server encounter placement, wild-monster HP/MP, attack,
defense, level, EXP, skill or drop value is recovered here. The qualified
`S2C 1C` area/scene/ordinal fields can be checked against this catalog; the
current gameplay sender does not yet use this reader. A complete packet join
still needs a build-matched original server monster row or observed sender,
plus original-client acceptance of the corresponding world encounter and
battle messages. The existing diagnostic battle retains its documented custom
fixture identity and values.
