# Current Monster Skill Assignments: Lane D, 2026-09-20

## New Native Evidence

The current incoming `83`, action discriminator `3`, supplies a skill pair to
the acting participant's cache. That cache is not a recovered repertoire:
the received action itself can add an unseen pair. The later original action
consumer searches the cache, records its slot, and computes the current skill
pointer. Neither operation establishes the server's permission or AI trigger.

Only the three Lane D files are added. No runtime, database, shared source,
network, UI, live process, child agent, or retired archive is used. Older audits'
archive recommendations are not followed. Main retains the original catalog
loader and learned-S2C34 integration; this probe uses pinned catalog bytes as
an explicit memory precondition and does not duplicate either implementation.

Image: `artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin`.
SHA256: `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
Base is `400000`; every RVA below is also its exact file offset.

Skill source: original client `Data2/Fight/Spg/cbspec2.bin`, SHA256
`7676acd93f164d071f7681a3fe74de94d65892759dbf2e69e3c0f748423d2f51`.
The report includes all 448 definition offsets and record hashes, plus image
span offsets and SHA256 values. This is a definition denominator only.

| Native RVA | Qualified contract |
| --- | --- |
| `114332`, `11439C` | Post-copy dispatch into `116AE0` for logical 83. |
| `116BBA` | Logical byte +2 selects side/slot by division/remainder 14. |
| `116D11`, `11E75A` | Real type-0 participant lookup: manager+38+24*(14*side+slot). |
| `116D20`, `116D25` | Logical +11 is skill ID; +12 is bank. |
| `116D36..116D62` | Search up to 51 actor+DF8 pointers; stop at first null or exact ID/bank pair. |
| `116DC1` | Publish pointer at actor+DF8+4*slot. |
| `116DF1` | Stop before resource association lookup `5F490`, with bank/ID arguments already pushed. |
| `12C520`, `12C537` | Separate original consumer entry and real acting-participant lookup. |
| `12C731..12C77F` | Search the same 51 pointers by both bytes; write matched slot to actor+1DF. |
| `12C790` | Missing cache pair: stop before diagnostic call, not a successful rejection/return. |
| `12C7D2` | Write definition pointer to actor+EC4; stop at `12C7D8`. |

Both pointer formulas reduce to:

```text
native = battle + A924D12 + 110*id + 6E04*bank
       = catalog_body + 4 + 6E04*bank + 110*(id-1)
file   = 8 + 6E04*bank + 110*(id-1)
```

The producer and consumer use the same VM, actor table, cache, packet bytes and
catalog. They are two explicitly separate original invocations. The unexecuted
resource/rendering path is not patched, supplied a fake return, or claimed to
have run. This is not complete action playback or a loader qualification.

## Counterfactuals

The executable suite exhausts all 448 populated definition pairs through both
stages, rotating all 28 positions. It does not claim the 448-by-28 Cartesian
product, any captured original action, or monster assignment coverage.

- Same ID in different banks appends a distinct pointer; duplicate pair reuses
  its existing slot. Full actor-byte comparisons preserve unrelated fields.
- Every actor position selects its own pointer-table entry; another actor is
  unchanged. A missing actor supplies no identity or assignment.
- First hole and last valid slot are tested. A full nonmatching 51-entry cache
  reaches slot 51 because `116D65` permits equality; the original store aliases
  actor+EC4. The consumer still cannot find the pair in its 51-entry scan and
  reaches the missing-pair diagnostic. This is a VM-only native boundary fact,
  not a capacity extension or behavior to copy into server code.
- ID zero, unpopulated ID 122 in bank zero, bank four, and FF/FF still produce
  pointer arithmetic. The source-membership check rejects those as definitions;
  it is a research guard, not a recovered native rejection rule.
- Wrong receive gate, unstarted phase, and positions 28/255 stop before the
  corresponding unqualified path. Missing cached identity stops before `2C70`.

Read/write guards bound actor, packet, catalog, stack and manager accesses.
All image code is read/execute; original bytes are checked before each stage.
No intercepted callee result or synthetic packet becomes an original value.

## Machine-Readable Coverage

`pinned_catalog()` supplies every current EnyName occurrence, without name/art
merging: 7,815 source records in 97 source groups, 7,791 lookup-visible records
in 96 groups, and 24 superseded occurrences. These counts are not unique species
or an ALL-boss denominator. Each row preserves its source index, generation,
area/scene/ordinal, visibility, exact decoded offset, line, raw bytes and hash.
Compressed and decoded source hashes are included for every row.

Assignments, use conditions, trigger conditions, observed actions,
classification and variant identity remain JSON null for all source rows.
There are zero verified identity-bound assignment records. Synthetic native
diagnostics are separate from these rows and have null monster identity.
Normal, boss, elite, event, quest and summoned are all requested categories;
this lane does not assert that EnyName enumerates every category or system.

## Remaining Producer

The concrete next input is the original sender/assignment source of `83` action
3, joined to the participant's lifecycle. A real observation requires same
session/lifetime binding from `1C` position byte +1 to `83` acting position +2,
including replacement/removal and variant state. The normal EnyName frontier is
`115E07` with area +9, scene WORD +11 and ordinal WORD +7. Variant WORD +5
branches through `115E25` or `115E70`; they must not be collapsed by name or art.
The other lanes own that participant identity/base-data work.

Even a provenance-qualified received action proves only that observed use.
Full repertoire requires an original assignment table or authoritative
enumeration per identity/variant; original conditions require the decision
producer and its actual predicates, rates, ordering and state. Client cache
matching, receive-phase gates, target selection and skill descriptions cannot
supply those rules. This bounded proof makes no global absence claim.

## Reproduction

Run from the server root; both commands suppress bytecode writes and generate
no files. Full JSON is emitted without `--summary`.

```powershell
python -B -m unittest tests.research.test_current_monster_skill_assignments -v
python -B -m tools.strike_lab.current_monster_skill_assignments --summary
```

Executed result: all 9 focused tests passed, including the 448-pair native
producer/consumer sweep and the complete 7,815-row source/null coverage check.
The summary CLI also completed successfully with 448 diagnostic cases and
7,791 unresolved visible occurrences for each requested field. No runtime
eligibility or all-monster/all-boss completion is asserted. Main reviews and
integrates this lane's three files.
