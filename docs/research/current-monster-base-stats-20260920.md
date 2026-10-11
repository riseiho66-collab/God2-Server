# Current Monster Base Stats: Lane A

This is one bounded producer-frontier step, not completion of all-monster stat
recovery. **Verified native base values: zero** for level, HP, MP, constitution,
strength, intelligence, and speed. Every source occurrence retains seven null
values and seven null field-authority entries. No DB/runtime integration is
eligible. Names, art, resource numbers, and diagnostic packet operands supply
no wild-monster base values or normal/boss/elite/quest/event/summoned labels.

## Source and Coverage

The main task owns `current_monster_inventory.py`. This lane consumes its
`pinned_catalog`/`parse_enemy_catalog`; it does not implement a second source
loader or run the heavyweight original loader in its focused tests.

- Image: `artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin`.
  SHA256 `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
- Current client: `Data2/Patch/Comm/gamedata.csvZ`.
  Raw SHA256 `70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731`;
  decoded SHA256 `75c3c37947a64b0917fbf8e546884d9bf893fe6a606d3e2b8f3b1857966b1815`.
- Source revalidated: 7,815 allocated occurrences in 97 groups; 7,791 final
  lookup-visible occurrences in 96 groups. The repeated area 7 declaration
  supersedes 24 occurrences, which remain separately reported.
- Every one of the 7,791 visible keys passes the new original battle-prefix
  lookup check. This count measures identity-routing coverage, not recovered
  stat records or a universal monster population.

Aggregation join: `source_record_index` (zero-based), `area_generation`
(one-based declaration index), `area`, `scene`, `ordinal` (one-based), with
bank `EnyName`. Source line, decoded byte offset, record size/hash, name bytes,
and source column 0 are retained. Source column 0 is not promoted to a server
template ID. No name/resource deduplication occurs. Alternate banks and
special overrides are not merged into these keys. Their category and the
true-wild-monster denominator remain null.

## New Native Proof

Addresses are hexadecimal RVAs, equal to mapped-image file offsets, BASE
`400000`. Original S2C logical `1C` has length 45 (`12A6`); the original queue
table selects `114358`, whose call at `11435B` targets `115C90`.

The probe executes continuously from `115C90` to **before `115E0C`**, including
original participant-slot lookup `11E6E0` and EnyName lookup `5A0A0`. It uses
an explicitly empty participant slot and a synthetic 45-byte record. The
qualified branch is WORD packet `+5 = 0400`, with no special override.

| Input | Native producer/consumer | Proven meaning |
| --- | --- | --- |
| BYTE packet +2 | `115D2F`, shift `115D38`, store `115D3D/115DD7` | Metadata byte +7, later consumed as a displayed level selector |
| WORD packet +7 | `115DDB`, push `115E01` | EnyName ordinal |
| BYTE packet +9 | `115E02`, push `115E06` | EnyName area |
| WORD packet +11 | `115DFA`, push `115E05` | EnyName scene |
| Three identity arguments | `115E07 -> 5A0A0` | Actual lookup computes record pointer; no source label/name join |

Standalone execution uses descriptor fixtures built from the shared pinned
inventory. The 26-byte enemy-record arena is **unmapped**: original code can
compute its address but cannot read a purported stat or even its name. This
is an explicit descriptor adapter, not a claim that this lane reran the
original loader. Passing `MonsterLevelProbe(existing_native_actor)` instead
reuses its loaded descriptors/records after source/group cross-checks.

A separate bounded run from `12D02A` stops before formatter calls `12D045` or
`12D088`. Image strings at `194310/194318/194320` are `Lv:%d`, `Lv:%s`, and
`Lv:???`. Values 0..30 supply the numeric argument; 31..99 select the original
string pointer table at `19D278` using `(value-30)//10`; >=100 selects `???`.
No formatter, UI, graphics, process, or network operation executes.

Counterfactuals vary levels 0,1,30,31,39,40,99,100,255 and register/stack poison
00/A5/FF. The original identity pointer is unchanged; only metadata byte +7
changes. Invalid ordinals 0 and count+1 are checked for every visible group,
as is absent area2/scene15. These diagnostics establish routing/display
semantics only. None is an original server value.

Static continuation `121A30..121A4C` copies 56 metadata bytes to actor `+DB0`.
That continuation is recorded as static evidence and is not executed here.
It neither fills nor proves the separate scalar storage starting at `+DE8`.
No HP/MP/four-attribute producer is qualified by this prefix.

## Exact Remaining Frontier

For level, recover the **original sender of S2C1C byte +2**, retaining the
area/scene/ordinal plus variant WORD +5, and establish whether the value is
a base level or encounter/display level. An actual identity-bound producer
is still required for each of HP, MP, constitution, strength, intelligence,
and speed. Their authority source/hash/offset remain null rather than being
assigned to unrelated actor or UI fields.

`SpecialEnyInfo` immediately follows EnyName at decoded offset **2781781**,
ending at **2781824**. The exact 43-byte section declares one row,
`1,IGS_SPECIAL,0,0,149,1`; SHA256
`c3d480f60ba45441c3dfc40fe2c61e420a9e79f32570a5b640f08b82652cc4ad`.
Original loader `5A560` and override lookup `5A120` are the next unexecuted
namespace frontier. Battle call `115E25` passes the low byte of packet WORD
+5 after the normal lookup. This row is **not identified as a boss**.

Separate branch `115E4D..115E77`, call `115E70`, looks up area0 and scene3/13/2
using flags in WORD +7 and its low14 ordinal when WORD +5 has bits `6000`.
This branch remains unexecuted here. Other monster systems and all requested
boss/elite/quest/event/summoned variants remain required; no global absence
or exhaustive-system claim follows from EnyName coverage.

## Verification and Delivery

`python -B tests/research/test_current_monster_base_stats.py -v`

Seven focused tests passed in 5.718 seconds. They cover all source occurrences,
all visible native joins, every
group's invalid ordinals, counterfactual level independence, exact native
hash/offset/dispatch/format evidence, unmapped enemy payloads, remaining
namespace boundaries, null JSON authority, and rejected inputs.

`python -B -m tools.strike_lab.current_monster_base_stats` emits the complete
machine-readable report on stdout. It has no output-file or DB mutation path.
Only this lane's tool, test, and research document are changed. An initial
development smoke check reused the full actor constructor; a duplicate test
startup was stopped when shared-loader coordination arrived. Final tests use
only the lightweight descriptor fixture; main owns full-loader regression.
