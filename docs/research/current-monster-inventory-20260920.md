# All-monster scope and current identity inventory

The owner's scope is every monster, including bosses, and every requested field:
level, HP, MP, constitution, strength, intelligence, speed, physical/magical
attack and defense, metal/wood/water/fire/earth, base EXP, and capturability.
The subsequent owner directive adds every monster's original skill assignments,
drop items and drop rates, including the conditions needed to interpret them.
Normal/boss/elite/quest/event/summoned variants must not be merged by name or art.
Classification itself requires original evidence. No retired Classic/XJZ input
is permitted, including as a source of defaults or identity joins.

## Exact denominator boundary

`current_monster_inventory.py` pins current `Data2/Patch/Comm/gamedata.csvZ`
and its decoded bytes. It preserves all 7,815 EnyName source occurrences with
source line, byte offset, raw bytes, row hash, area-generation, area, scene and
one-based native lookup ordinal. The source label is preserved separately;
it is not silently promoted to a globally unique monster ID.

There are 97 source groups and 96 final lookup-visible groups. Original repeated
area replacement makes 24 records inaccessible through the final lookup table;
the inventory retains them as superseded rather than silently deleting them.
The remaining 7,791 lookup identities are not a demonstrated count of unique
wild monsters. Other monster/boss namespaces still require source enumeration.
The report explicitly leaves `unique_wild_monsters=null` and
`all_monster_systems_enumerated=false`.

The parser is shared by the existing original `5A1A0` loader harness, eliminating
separate inventory/native-fixture interpretations. The original `5A0A0` test
now queries every visible ordinal, not only each group's first and last entries.
It also compares every resulting native name with the source-index inventory.

### Current Join Collisions

A read-only grouping of `pinned_catalog()`'s final visible records found:

| Candidate lookup key | Distinct keys | Keys with multiple visible records |
| --- | ---: | ---: |
| `(area, scene, ordinal)` | 7791 | 0 |
| Exact `name_bytes_hex` | 5046 | 608 |
| `source_label` | 2115 | 2070 |

These counts use the source hashes already pinned by the inventory, exclude
the24 superseded rows, and compare raw name bytes without text normalization.
They were calculated with Python `defaultdict(list)` over those7791 records;
no native emulator, database write or name-based classification was used.
Neither a name nor a source label alone is a safe key for attaching recovered
numbers. The unique composite key identifies this lookup namespace only;
special/alternate selectors, source version and the actual numeric consumer
still need to be qualified. It is not a universal species ID or a new stat.

## Data promotion

The generated artifact is
`artifacts/research/current-monster-inventory-20260920.json`.
All 21 requested fields on every source occurrence currently remain JSON null,
not zero, false, or a guessed interpolation. The report tracks each field's
verified and unresolved lookup counts separately. This inventory alone promotes
no stats and is explicitly runtime-ineligible. A packet consumer can prove an
offset/type without proving any original monster's actual value.

Five disjoint first-round workers investigated base stats, attack/defense/elements,
EXP/capture, skill assignments, and drop rules respectively. Their bounded work
was reviewed and closed as listed below. Unknown skill/drop
lists remain null, not an empty list implying no skills/drops; unknown drop rates
remain null, not zero. Global skill/item definitions and individual received
results do not prove a complete monster repertoire, drop table or probability.
Rate promotion additionally requires original units, denominator and conditions.
A native value may enter the formal database only
after its source, field semantics, and exact monster/variant identity are
qualified together. Neither a synthetic test packet nor transformation-card
effects satisfy that requirement. No production DB/schema or C++/Lua gameplay
logic changed in this inventory step.

## Reviewed Lane Deliveries

All five first-round workers delivered, were independently reviewed/retested,
and were closed. This closes their bounded tasks, NOT the all-monster recovery
requirement. No lane supplied identity-bound DB-eligible original monster values.

| Lane | New qualified dataflow | Independent tests | Authority still missing |
| --- | --- | --- | --- |
| Base stats | 1C byte+2 -> display level; all7791 identity joins | 7/7,5.764s | Per-monster base level, HP/MP and four attributes |
| Combat stats | All101 card rows -> signed display;100 identity references | 6/6,12.151s | Wild physical/magical attack/defense and elements |
| EXP/capture | Actor+286 -> capture-result byte/message | 7/7,0.603s | Monster base EXP and capture eligibility |
| Skills | 83/3 -> actor cache -> separate action consumer for448 pairs | 9/9,1.507s | Original monster repertoire and AI predicates |
| Drops | Item source/lookup -> four result slots -> name consumption | 14/14,5.354s | Original monster award producer and probabilities |

Reports: `current-monster-base-stats-20260920.md`,
`current-monster-combat-stats-20260920.md`,
`current-monster-rewards-capture-20260920.md`,
`current-monster-skill-assignments-20260920.md`, and
`current-monster-drop-rules-20260920.md`. These contain exact RVAs, source hashes,
input authority and unexecuted next producers. The drop path's FFFF marker can
select PLAYER EQUIPMENT LOSS, so its slot values must not be mislabeled as a
monster drop table. A received action cache similarly is not a full repertoire.
All normal/BOSS/other-category denominators remain unqualified; no name/art
classification or global absence conclusion was substituted for source proof.

## Special and Alternate Identity Continuation

The separately scoped variant worker was reviewed, independently rerun7/7 in
5.068s, and closed. `current-monster-variant-identity-20260920.md` documents
original5A560/5A120 and bounded115E25/115E70 consumers: one SpecialEnyInfo row,
4051 alternate source identities and256 low-byte selectors. The4051 identities
are already part of the7791 visible EnyName records; do not add them as new
species. The special override retains a composite base identity plus selector,
not an assumed standalone BOSS. Its uninitialized bytes and diagnostic inherited
base payloads cannot enter production. All stat/skill/drop/rate values remain
unresolved; this closes another identity-routing gap, not those field values.

## Reproduction

```powershell
python -B -m tools.strike_lab.current_monster_inventory --output artifacts/research/current-monster-inventory-20260920.json
python -B -m unittest discover -s tests/research -p test_current_monster_inventory.py -v
python -B tests/research/test_current_world_actor.py -v CurrentWorldActorTests.test_complete_original_enemy_loader_and_all_visible_group_records CurrentWorldActorTests.test_enemy_source_bounds_fail_before_native_allocations
```

Verification passed: inventory 8/8 tests in 1.627 seconds; the two original
loader/lookup and malformed-input tests passed in 167.947 seconds. Every one of
7,791 visible identities was queried through original 5A0A0, with all source
record bytes checked against original 5A1A0 output. This is 100% of this pinned
lookup namespace, not 100% of all monster systems or any stat restoration.
Each of the requested fields still has 0 verified values in
this inventory. No live gameplay or BOSS attribute completeness is claimed.
