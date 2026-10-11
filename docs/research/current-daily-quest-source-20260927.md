# Current daily quest native display source — 2026-09-27

## Result and qualification

The current PE's complete `457FF0` parser returns1 after all85 original
DayMissionDesc rows. Its original `451A90` line reader, `451BE0` tokenizer,
`451AE0`/`451B50` accessors and copies execute. All85 resulting316-byte records
match independently calculated ordered field writes byte for byte. Original
`458430` returns the entire316-byte record for all85 distinct pairs, including
`(0,0)`. Missing `(255,255)` returns0 and leaves output untouched. A separate
isolated duplicate-key mutation of the second parsed row proves first-match
selection; the original complete table is restored and checked afterward.

This qualifies **NATIVE_PARSED_DISPLAY_ONLY** data. It does not recover daily
acceptance, progression, availability enforcement, reset, completion, item/EXP
awards or original-server NPC namespace resolution. Existing display formatter
`48C040` divides time by100 and R-mode bounds by1000; this audit does not
reinterpret those presentation fields as server conditions or reward formulas.
No production DB, shared runtime, client files or desktop was changed here.

## Pinned inputs and outputs

| Artifact | SHA256 |
| --- | --- |
| Current `../God2/God2.exe` | `6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98` |
| `Data2/Patch/Comm/DayMissionDesc.csvZ` | `4a347d56706946d7004b2bd2118500ffc60844628fa461862b2f6d5320a90e54` |
| Decoded CP950 source | `2848b95b0af99eac10ca4dff61a5533c13917127c4738039e263c60a1be45eaf` |
| All85 parsed316 records concatenated in source order | `df0bc3a96425c3440cd2fefc867840aa10e3ad35c4a3be32e332c6204f30236a` |
| Normal and optimized `parsed.json` cache | `93516cd13f97fd39430d20deae932602f8e21958cc2b6765b88f476f928fd6a9` |

Cache: `artifacts/research/current-daily-quest-source-20260927/parsed.json`;
optimized counterpart `parsed-optimized.json`. Schema:
`god2-current-daily-quest-native316-v1`. It retains source lines6–90, ordinal0–84,
every raw CP950 field, original line endings, raw row hash (excluding line
ending), full parsed316 hex/hash, typed scalar values, bounded string block hex,
and whether each string terminates inside its own block. CP950 presentation uses
backslash replacement for incomplete bytes; the hex bytes remain authority.

Source header is preserved verbatim in cache. Zero-based source columns:

| Column / original label | Offset decimal | Native width / interpretation |
| --- | --- | --- |
| 0 索引, 1 任務分支 | 0,1 | u8 pair, no zero exclusion |
| 3 開始NPC ID | 2 | u16 |
| 10 結束NPCID | 4 | u16 |
| 5 開始時間, 6 結束時間 | 6,8 | u16 raw presentation time |
| 8 轉生等級下限, 9 轉生等級上限 | 10,12 | u16 raw presentation bounds |
| 7 判別方式 | 14 | byte1 for initial R/r, else0 |
| 18 可接次數 | 15 | u8; missing source field becomes0 in actual parser |
| 4 星期(二進位) | 16 | u32 mask; requires8 source bytes, ignores position0, positions1–7 equal ASCII1 set bits0–6 |
| 2 任務名稱 | 20 | 30-byte block |
| 11 任務限制 | 50 | 20-byte block |
| 12–14 任務簡介1–3 | 70,111,152 | 41-byte blocks |
| 15 起點, 16 終點, 17 任務獎勵 | 193,234,275 | 41-byte blocks |

All85 source discriminators are R. Eighty-four weekday masks are127. Ordinal28,
source line34 has source `11100011`, yielding99. The source parser establishes
bit positions, not which named weekday a server clock should assign to each bit.
Eighty rows have19 fields; ordinals58/59/60/63/64 (lines64/65/66/69/70) have12.
Those five actual parser records have empty description/start/end/reward blocks
and accept count0. No missing columns were invented.

## Original string overflow must remain visible

Source lines12–15 (ordinals6–9) each contain42-byte description2 and reward
strings. The native copy includes NUL into nominal41-byte blocks. Description2
spills two bytes into description3, then the later description3 copy overwrites
that spill. Reward spills two bytes into the following row's key, then the next
row's scalar writes overwrite them. After the full parse, these eight blocks
have **no NUL inside their41 bytes**. Rejecting such records as malformed would
reject this exact native catalog. Searching past a block would conflate fields
or rows. Keep the full316 authoritative record; expose bounded41-byte strings
with explicit termination status. The pristine raw text remains separately
available for inspection. Do not silently repair the native316 cache.

## Harness boundary and reproducibility

`tools/strike_lab/current_daily_quest_source_20260927.py` maps the current PE
without changing its code. CRT adapters supply only `calloc547E23`,
`fgets547A95` (text CRLF translation) and existing decimal `sscanf5480B4`.
Allocation size and caller, fgets caller/handle/stack bounds, exact function
returns, stack cleanup, count, all row bytes and all lookup bytes are checked.
Other executed native string helpers and the stack probe are not replaced.
Counts: parser1, line reader85, tokenizer85, string accessor850, numeric
accessor765, lookup88. Bounded maximum is2 million instructions per call.
Input hashes are rechecked after the audit. Checks use exceptions under normal
Python and `-O`; no required removable assert is used.

```powershell
python -m tools.strike_lab.current_daily_quest_source_20260927 --output artifacts/research/current-daily-quest-source-20260927/parsed.json
python -O -m tools.strike_lab.current_daily_quest_source_20260927 --output artifacts/research/current-daily-quest-source-20260927/parsed-optimized.json
```

## Import interface and acceptance

`tools/strike_lab/import_native_daily_quest_parsed.py` exposes
`import_catalog(db, client)` and `pinned_records(client)`. Each import runs a
fresh complete native audit; it never trusts a caller-supplied cached record.
It requires the exact85 original `native_daily_quest_source` rows and the
schema30 table provided by integration. It does not install migrations. Column
order of `native_daily_quest_parsed` is:

`ordinal, source_line, pair_index, pair_branch, logical, source_record_sha256,
client_sha256, source_sha256, decoded_sha256, catalog_sha256, authority`.

`logical` is BLOB316. `ordinal` references raw source `record_index`. Authority
is `NATIVE_PARSED_DISPLAY_ONLY`. Preserve source order and first-match lookup;
do not impose a pair uniqueness rule on the recovered native contract. Import
creates no player states and no executable rules. It rejects a caller-owned
transaction; otherwise one `BEGIN IMMEDIATE` covers inserts, complete readback
and database integrity checks. Existing complete identical data is a no-op;
partial/conflicting source or parsed data is rejected without overwriting it.
All exceptions roll back its transaction.

```powershell
python -m tools.strike_lab.import_native_daily_quest_parsed --self-test
python -O -m tools.strike_lab.import_native_daily_quest_parsed --self-test
```

Both modes pass13 disposable-database cases, saved in `import-tests.json` and
`import-tests-optimized.json`: fresh85, idempotent85, exact readback, partial
parsed rows, altered raw source, missing raw row, wrong raw authority, readback
corruption trigger, abort-on-last-row trigger, altered parsed316, wrong client
identity before transaction, read-only database, and preservation of an active
caller transaction. The two test reports are identical. These tests use actual
current native rows and memory-only databases; hidden-client display acceptance
and formal migration/C++ integration belong to the parent integration lane.
