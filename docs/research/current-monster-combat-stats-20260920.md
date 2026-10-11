# Current monster combat-stat authority, lane B

## Result and coverage

New bounded proof: current `ChangeDollCard.csvZ` numeric columns become signed
card-display values through original x86 loader, lookup, and formatter instructions.
The participant consumer uses the card's area/scene/ordinal to request an enemy
resource identity. **Neither edge establishes wild-monster base combat stats.**
No records are eligible for DB integration from this lane.

The module consumes main's `current_monster_inventory.pinned_catalog()` once,
which checks the current compressed and decoded source hashes. It does not rerun
the heavyweight native enemy loader or independently deduplicate names.
Verified current inventory projection: **7,815 source occurrences in 97 groups;
7,791 lookup-visible occurrences in 96 groups; 24 superseded occurrences**.
There are 16 area declarations; repeated area 7 replaces its earlier descriptors.
Original replacement instruction `5A226` stores the new descriptor pointer.

Every source occurrence has explicit `null` values and unresolved authority for
physical attack, physical defense, magical attack, magical defense, metal, wood,
water, fire, and earth. Per field: **0 verified / 7,791 unresolved visible records**,
plus the 24 preserved superseded records. This is complete lane B coverage of
main's current EnyName domain, **not completion of all-monster recovery**.

Normal, boss, elite, quest, event, and summoned variants remain requested scope.
Classification, true wild-monster denominator, and unexplained bank/variant
semantics remain null. All raw source fields are retained as bytes; no identities
are merged by name or artwork. EnyName is not asserted to exhaust monster systems.

## Exact identity joins

The occurrence join to main is source SHA-256 plus `source_record_index`, with
`area_generation`, `area`, `scene`, and one-based `ordinal` retained verbatim.
Source line, decoded byte offset, raw-field hex, and main's row hash **including
the line ending** accompany each occurrence. This preserves superseded entries
and otherwise identical names/labels in distinct areas, scenes, and generations.

All **101 current card rows** execute the native numeric loader and bounded text
consumer, not just examples. Participant-kind-1 execution produces **100 exact
joins** to final lookup-visible EnyName occurrences. Card 0 takes the native
zero-card branch and has no join. Card references are recorded on their exact
target occurrence but confer no combat-stat authority on that occurrence.

At `1177FF`, the original code reads supplied record byte `+2`: zero branches to
`11890B`, one reaches the card path, and other values branch to `118A79`.
These numeric cases have no established normal/boss/wild semantic classification.
With kind 1 and a nonzero card index at record WORD `+C`, calls `117827 -> 5C100`
and `117844 -> 5C060` validate/select the card. The copied card coordinates are
pushed at `11786E/117872/117873`, stopping before `117874 -> 5A0A0`.
The inspected lookup consumes low BYTE area and low WORD scene/ordinal.
Upper DWORD argument bits are preserved in JSON, not treated as identity data.
This last lookup is not executed in this lane; final-table joins reuse main's
current-source inventory and established lookup semantics.

## Numeric dataflow

All addresses are hexadecimal mapped-image RVAs/file offsets; base VA is `400000`.
The header dispatch `56E3A..56E85` reaches loader `5BB10`; execution stops before
calloc at `5BB3F` with original arguments `(102, 0x30)`. The source declares 101
rows. Resource owner `+D2AAC` is the card table, `+D2AB0` its loaded bound.

Original tokenizer `51BE0`, field selection/conversion `51AE0..51BDC`, row loader,
and record lookup `5C060` execute. Row loading selects columns 0..5 and 8..22;
columns 6/7 labeled monster level/attribute are not selected in this bounded path.
The nine requested fields map as follows (columns are zero-based):

| Field | Column | Record WORD | Native store | Signed display conversion |
| --- | ---: | --- | --- | --- |
| Physical attack | 10 | +16 | 5BD02 | BAE27 |
| Physical defense | 11 | +18 | 5BD20 | BAEB9 |
| Magical attack | 12 | +1A | 5BD3E | BAFAC |
| Magical defense | 13 | +1C | 5BD5C | BB09B |
| Metal | 18 | +26 | 5BDF2 | BB172 |
| Wood | 19 | +28 | 5BE10 | BB203 |
| Water | 20 | +2A | 5BE2E | BB2F5 |
| Fire | 21 | +2C | 5BE4C | BB3E6 |
| Earth | 22 | +2E | 5BE68 | BB4D0 |

The text path `BAC21..BB572` accepts SI selectors `188D`, `188E`, `1891`, reads
instance WORD `+4`, and executes both original card guard and record lookup.
Each nonzero field is sign-extended and supplied to original formatter `147AF7`
using format at RVA `1927A0`. Zero omits the field. The accompanying color argument
is 3 for positive values and 1 for negative values. No actor combat arithmetic
is established by formatting these numbers. The selector live-in is a fixture;
this lane does not qualify its upstream metadata producer.

Concrete source values, illustrative only; all rows are included in JSON:

- Card 5, coordinates `(13,0,5)`: magical attack +5.
- Card 6, coordinates `(13,0,6)`: physical attack +10, physical defense -5.
- Card 90, coordinates `(15,30,2)`: physical defense +5, magical defense -15.

All five element columns in all 101 current card rows are zero. Those are verified
card-record zeros, never wild-monster base values. Tests replace each individual
column with -32768, -1, 0, 32767, and 65535. Original WORD storage and signed
formatting yield 65535 -> -1. Only the selected record WORD changes. Nonzero
element mutations reach their corresponding formatter calls, proving column
mapping despite the actual source's zero entries.

## Reproducibility and boundaries

Only the three lane-owned files were created/edited:

- `tools/strike_lab/current_monster_combat_stats.py`
- `tests/research/test_current_monster_combat_stats.py`
- `docs/research/current-monster-combat-stats-20260920.md`

Read-only current inputs:

| Input | SHA-256 |
| --- | --- |
| Mapped `native-master-01-stable.bin` | `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763` |
| `Data2/Patch/Comm/ChangeDollCard.csvZ` | `4d51b22d51c14bc98b6ec96c16a40384a226e9fa1f90543ea58a36fb4b56ebd2` |
| Decoded card source | `0f04cc27292e4b3bc08c030dce8b2564e2fad52bf0d87f227414d63f4ca6acef` |
| `Data2/Patch/Comm/gamedata.csvZ` | `70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731` |
| Decoded game source | `75c3c37947a64b0917fbf8e546884d9bf893fe6a606d3e2b8f3b1857966b1815` |

JSON includes per-field source/header/column, decoded field offset, row hash
(card hashes exclude CRLF), record offset/width, store/conversion RVAs, image hash,
and slice hashes. Unknown wild values and producer/source pointers remain null.
No inferred coefficient or category is substituted for an unknown.

Declared execution boundaries: decompression and CRLF translation outside VM;
source-checked header count as a live-in; prepared table memory after the calloc
stop; per-row entry after file read; malloc stop/resume with an explicit label
allocation. Original tokenization, conversion, stores, lookup, formatting, and
text append execute without callee stubs. Message-label strings and item/context
pointers are fixtures. Participant inputs are synthetic counterfactuals, not
captures or evidence of actual monster stats. Image memory is read/execute;
bounded instruction ranges, 100,000-instruction/one-second stage limits, stack
checks, and loaded-index validation prevent unqualified continuation.

```powershell
python -B -m unittest discover -s tests/research -p test_current_monster_combat_stats.py -v
python -B -m tools.strike_lab.current_monster_combat_stats --summary
# Omit --summary for full per-occurrence/per-field JSON on stdout; no files written.
```

Six focused tests pass. They check the full source inventory and all card rows,
actual joins, signed numeric and element counterfactuals, unused-column mutations,
selector/kind branches, input bounds, hashes, and original image preservation.
No live/UI/network, DB/runtime/shared-file edits, retired sources, or child agents
were used. Existing research code was a lead; current source bytes and execution
provide the new card-path evidence.

## Remaining exact frontier

The proved card edge ends at `117874 -> 5A0A0`, an enemy resource-identity lookup.
The nine numeric values instead reach signed text formatting in `BAC21..BB572`.
Neither is a wild actor combat-field producer. The next required authority is an
original producer connecting each requested combat field to exact actor identity
and an independently established wild/boss/etc. discriminator. The kind-0 branch
at `11890B`, other-kind branch at `118A79`, and post-lookup continuation at
`117879` are unqualified here. No upstream stat producer address is established,
and no full absence is claimed from this bounded result. All-monster and boss
stat recovery remains unfinished; main must aggregate these unresolved fields
without promoting card values or treating EnyName as an exhaustive denominator.
