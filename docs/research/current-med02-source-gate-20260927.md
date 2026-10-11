# Current MED02 full source gate — 2026-09-27

## Completed source/storage work

`NativeSupplyCatalog` now validates the full imported71-record catalog on every
`is_imported()` and nonzero `lookup()`, including unknown item queries. One
SQLite read transaction covers source/count/rows/fingerprint; an existing caller
transaction is borrowed without commit or rollback. There is no cached validity
that survives external DB edits. Missing source with any specialized MED02 rows,
renamed datasets, missing rows, wrong typed values or any fingerprint change
throw `DatabaseError`. Only absence of both the current source and all MED02
declarations returns false. This prevents corrupt source from enabling fallback.

The complete pin is
`ebb3882ce833ac8bd45f5b6c341a67ff17039ea3fd30ab31a715d2d6985c4d9b`:
the nine fields of the source row, then all eleven fields of each declaration in
`source_record_index` order. Each field contributes uint32LE byte length followed
by its bytes; integers use decimal ASCII, raw/tooltip use exact CP950 bytes.
The fingerprint covers provenance, raw records, their hashes, tooltip bytes,
amounts, IDs, source locations and use flags. It pins the complete imported71;
it does not pretend that the29 excluded source definitions are imported effects.

Inputs remain:

- Current EXE `6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98`.
- Compressed gamedata `70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731`.
- Decoded gamedata `75c3c37947a64b0917fbf8e546884d9bf893fe6a606d3e2b8f3b1857966b1815`.
- Qualified native image `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.

Source record indices are0–99, lines6354–6453, with itemID=3101+index.
SQLite integers must have INTEGER storage and fit the destination type before
conversion. Amounts are uint32 values0–4000 with at least one nonzero. This
rejects negative or >32-bit values that previously could wrap during casts.
Use flags must be exact1; strings/BLOBs have explicit bounds and storage types.

## Eligible boundary and native request proof

The100 native MED02 definitions have71 exact positive fixed-amount tooltip
declarations:36 HP only,11 MP only,24 both. Eligible IDs are
3101–3115,3139–3145,3147–3161,3167–3200. All have normal-use and hotkey flags.
Excluded IDs are3116–3138,3146,3162–3166; their text includes status removal,
noncombat full/capped restoration, or other descriptions. They are unresolved
for this route, not assumed ineffective. Do not infer revival behavior.

Accepted tooltip grammar is exactly `恢復生命 N`, `恢復法力 N`, or
`恢復生命 N，法力 N` in original CP950. Those numbers are
**NATIVE_CLIENT_TEXT**. Actor-living restriction, HP/MP caps and consuming one
only if state changes remain **CUSTOM-0016**, not original-server rules.

The existing independent original-code test was rerun against all100 actual
definitions: native59420 parser,59A20 registration,59A60 lookup,9B720 selector,
then a separate VM receiving the actual parsed bytes and executing963C0 producer
with59A60/132E0. All100 have metadata+11A bit04 clear and produce **C2S26**, not
C2S22/25/28, in this ordinary-use path. Explicit fixture actor/slot/stack bytes
remain synthetic. Producer wire is `26 target:u16 item:u16 slot:u8 opaque:u8`;
the final byte is residual and is not recovered amount or quantity authority.
This is offline native instruction evidence, not current-client UI acceptance.

## Reproduction and tests

`tools/strike_lab/current_med02_source_gate_20260927.py` reproduces the full pin,
all100 source eligibility boundaries and the exact source/71-row fixture cache.
Normal and `-O` produce identical `source.json` / `source-optimized.json` under
`artifacts/research/current-med02-source-gate-20260927/`, SHA256
`26af4818e72872d1740870bddb1eec1ba8d1b3733eaef79ec3b38c2493b8d6b8`.

`tests/test_native_supply_catalog_integrity.cpp` uses those actual source bytes,
never invented catalog data. Standalone MSVC `/O2 /DNDEBUG /MD /W4` build and test
passed with no warnings. Its26 corruption cases cover partial/source missing,
dataset rename/orphan, raw/hash/tooltip changes, amount changes, negative,
overflow/wrapping, FLOAT/NULL, field types, line/index/ID and use flags. Both a
different valid item and an unknown selector reject when another row is corrupt.
It also tests71/100 lookup coverage, absent source, read-only DB, externally
changed DB reload, no write, and preservation of caller transactions.
Build/test output is `cpp-build-test.txt` in the same artifact directory.

Native all100 loader/producer test passed normal (9.809s) and `-O`; optimized
output is `native100-optimized.txt`. Run:

```powershell
python -m tools.strike_lab.current_med02_source_gate_20260927 --output artifacts/research/current-med02-source-gate-20260927/source.json
python -m unittest tests.research.test_current_supply_request_branch.SupplyRequestBranchTests.test_all_real_med02_rows_loaded_then_routed -v
```

Suggested shared target: `native-supply-catalog-integrity`, link `god2_core`,
define `GOD2_SOURCE_DIR`, register a60-second CTest. This lane did not edit
Application, Config, migrations or CMake. Source qualification and owned-runtime
promotion/current-client acceptance must be reported separately.
