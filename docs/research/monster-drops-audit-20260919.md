# Monster Drop Authority Audit - 2026-09-19

## Result and scope

No original, numerically authoritative monster-drop probability was established
in this bounded audit. There ARE usable identity leads: six named monster/item
relations in current-client quest descriptions, two area-based event-item leads,
215 XJZ capture/configuration targets, and a Classic relationship-export path.
These have different authority; none is promoted to an executable original drop
table. An unknown rate is not zero, and a capture target is not an observation.

Roots used below (paths are relative to these exact roots):

- `S`: `C:/Users/risei/Desktop/God2/God2-Server`
- `C`: `C:/Users/risei/Desktop/God2/God2`
- `X`: `S/artifacts/legacy-evidence/xjz-20260820/files/XJZ-Server-Cpp/server_implementation`
- `L`: `C:/God2Evidence/classic-20260820/files/God2-Classic-Server-Formal-Handoff-20260820-020345/ServerSource`

Only this document was written. No runtime integration, stats/skills changes,
world-loader changes, database writes, generated-content changes, client/server
launches, or UI actions. SQLite was opened with URI `mode=ro`; the initial
inspection also set `PRAGMA query_only=ON`. No Classic database was queried.
This is a targeted source audit, not an exhaustive executable disassembly.

## Existing extraction

`S/tools/strike_lab/recover_monsters.py` explicitly retains `drops` as unknown.
`S/docs/research/content-recovery-20260919.md` describes definition extraction,
not gameplay restoration. The saved `S/artifacts/world-atlas/monsters.json`
contains 215 field definitions, 215 battle definitions, 208 Classic template
source rows, 69 spawn candidates, one level claim, zero imported spawn instances
and zero runtime integrations. The two 215-row sets are not 430 unique monsters.
Field indices, battle codes, server monster IDs and item IDs are separate
namespaces until a consumer or explicit binding proves otherwise.

## Current-client identity candidates

Decoded CSVZ line numbers below are one-based. Decoding used the existing
`tools.strike_lab.omega_assets.decode_csvz`; text inspection used CP950. The
item ID is column 0 of `C/Data2/Patch/Comm/gamedata.csvZ`, backed by `ITEM_ID`
in its header. English descriptions below identify the source text, not new
canonical English names.

| Monster/context stated in quest text | Candidate item ID and item line | Quest source line / mission | Supported claim |
| --- | --- | --- | --- |
| Stone monster in Hongmeng realm | 4683, line 7659, sacred platinum | `Mission_data.csvZ:1289`, mission 202 step 4 | Text says the monster drops the material; requested total is 7 |
| Brown bear outside Yulong forest | 3533, line 6870, bear skin | `Mission_data.csvZ:2165`, mission 387 step 4 | Paired bear/tiger and skin wording; requested total is 20 of each |
| Tiger outside Yulong forest | 3556, line 6893, tiger skin | Same line and mission | Same text-level relation; no individual numeric monster ID |
| Large butterfly in Jiuli peninsula | 5091, line 8067, cordyceps | `Mission_data.csvZ:2186`, mission 390 step 7 | Explicit monster/material/location description; requested total is 30 |
| Guocheng giant flower in Jiuli plain | 3406, line 6743, medicinal herb | Same line and mission | Explicit monster/material/location description; requested total is 30 |
| Red-flower butterfly in Cantian forest | 3475, line 6812, red-flower butterfly egg | Same line and mission | Explicit monster/material/location description; requested total is 30 |

All quest paths in this table are under `C/Data2/Patch/Comm/`. Mission headers
are at lines 1285, 2161 and 2179 respectively. The platinum sentence varies the
name slightly within the same sentence; item 4683 matches its full item phrase.
These are client-authored descriptive identity candidates, not proof of a
server-template binding or of unconditional availability. A search of the 215
battle display names for the exact six Chinese monster phrases found no match;
do not manufacture a code using a nearby name or a field-table index.

The totals 7, 20 and 30 describe collection objectives. They establish neither
per-kill quantity nor guaranteed drops. Quest acceptance, party credit, map
selectors, level filters, event dates and eligibility remain unproven.

Additional current-client sources:

- `gamedata.csvZ:15006`: item 17221 (Double-Ten badge) says monsters near Guoli
  village may drop it and identifies an exchange NPC. No monster ID, numeric
  chance or event activation predicate is supplied.
- `gamedata.csvZ:15274`: item 17489 (carnation) says monster drops in Jiuli
  plain, Jiuli peninsula and the barrier area. The instruction to collect 10
  flowers is a crafting/collection target, not a drop stack of 10.
- 332 decoded `gamedata.csvZ` lines contain the exact CP950 phrase for "enemy
  drop item". This includes material descriptions such as item 3401 at line
  6738. It is a text-hit count, not 332 proven monster/item edges. Broader
  hits for drop/defeat wording total 388 lines. Exact phrases for "drop rate"
  and "treasure drop rate" have zero hits in this file; this does not prove
  that all possible rate evidence elsewhere is absent.
- `Mission_data.csvZ` has 2435 lines and declares 418 missions. Five lines
  match drop/treasure-drop wording: 1289, 1640, 1949, 2165, 2186. Line 1640
  only suggests unspecified monsters might drop the requested candy; line
  1949 describes looking for a fallen object, not a monster loot relation.
- `NPCMission01.csvZ` has 1002 lines, declares 1000 messages and has one such
  hit at line 409 (message 407): narrative about lost objects. Do not turn
  NPC dialogue gifts, quest completion rewards or lost objects into drops.
- `eny.csvZ` and `FightEny.csvZ` each decode to 215 definitions. Their headers
  describe visual identities/actions/files, not loot probability fields.
  Current FightEny compressed SHA256 differs from the Classic candidate
  provenance hash `d64392b5f7329bfe9cec03bbfea91de71b96c47569dd93ff53489d66a3874e06`.

## XJZ corpus: measured state

Read-only counts from `X/xjz_evidence.sqlite`:

| Table | Rows | Interpretation |
| --- | ---: | --- |
| map_drop_capture_target | 215 | One unique drop configuration key per target |
| monster_drop_sample | 0 | No observed kills/drop outcomes in this table |
| map_encounter_sample | 0 | No encounter observations in this table |
| combat_loot_award | 0 | No award rows |
| loot_pool_grant_sample | 0 | No grants observed |
| reward_pool_roll_sample | 0 | No reward rolls observed |
| loot_or_choice_pool | 378 | 42 fudai entries, 333 total-list entries, 3 roulette prizes |
| reward_pool_capture_target | 29 | Reward-pool targets, not monster drop tables |
| map_drop_playbook_route | 430 | Capture routes, not 430 drop observations |

All 215 map/drop targets have `drop_service_runnable=1`,
`packet_sample_required=0`, and `drop_packet_evidence_boundary=1`. These flags
describe configured service entry points, not recovered original loot rules.
For example, target 900001 uses `monster_key=monster:1`,
`server_handler_key=resolve_monster_encounter_drop`,
`encounter_config_key=monster.encounter.1`, and `drop_config_key=monster.drop.1`.
Its target output is `monster_drop_sample`, with session, actor, monster key,
map, encounter group, item JSON, modifiers and packet references.

`combat_runtime_config` has 19 rows and `client_config_evidence` has 176;
neither table's row values contains `monster.drop.` or `monster.encounter.`.
This is a bounded check of those two plausible configuration stores, not a
claim that the entire corpus lacks every configuration implementation.
`X/evidence-server-ready-v0.md:1589` names the handler and keys; the exact
per-monster key payload is the next concrete consumer input to retrieve.

`X/evidence-reward-pool-v0.md` explicitly defines pool `weight` as client row
order/display position pending sample validation. It is NOT a probability
numerator. `C/Data2/Patch/Comm/FuDai_ItemList.csvZ` names Index, ITEM_ID, name
and quantity; the Total file declares 24 bags and repeats some prize IDs.
Neither repetition nor display order establishes a denominator or roll count.
Roulette and bag rewards must stay outside the monster drop graph.

## Classic corpus: authority and actual consumer

`L/db/imports/official/drop_tables/drop_tables.official.json` declares and
contains 208 records. All 208 have `runtimeEligibility=false`; zero records
contain actual `dropItems` or `dropRates` fields. The metadata explicitly lists
items, rates, quantities, ownership, party and quest rules as missing.
The directory name `official` does not override `Unverified; EvidenceOnly`.

There is a stronger next candidate than that placeholder JSON:
`L/database/schema/418_publish_monster_drop_gap_evidence_audit.sql:117`
reports 47 legacy `god2.monster_drop_relationships` candidates. This number is
a migration's historical assertion, NOT a measured live database count here.
Its view joins legacy relationships to formal monsters/items and drops, and
reports missing identity mappings. Migration 389 separately offers the chain
`relationship.DropTableId -> drop_tables.MonsterId -> legacy monsters.Code ->
formal monsters.code`; this is a concrete mapping candidate, not evidence that
all cross-build code joins are valid.

The relationship schema in migration 032, lines 41 onward, preserves
`Weight`, `RollType`, `ExclusiveGroup`, `Guaranteed`, quantity bounds,
quest/map/level/event conditions, `SourceFile`, `SourceIdentity`, `SourceHash`
and evidence status. Its `EffectiveDropChance DEFAULT 0` is a disabled/default
value, not measured 0% probability. Migrations 211 and 212 rename the claimed
chance through Original -> Evidence -> Declared; names alone confer no authority.
Migration 389 labels non-null declared values `OfficialEvidence`, copies them
without demonstrated denominator conversion and caps above 9999.99999999.
That migration label must not be treated as independent validation.

Migration 300 explicitly generates SERVER-DESIGNED test drops: item selection
is `monster_id MOD 8`, rates are 0.22/0.20/0.18 for level bands <=30/<=60/>60,
minimum quantity is 1 and maxima are 1/2/3. The group is
`first_wave_material_test`; source is the Chinese label for server design.
The eight possible legacy item IDs are 67632252, 131025371, 732479429,
848042268, 1796148254, 1856301026, 1984980765, 2092591819. These are neither
current client item IDs nor original per-monster loot evidence.

### Probability model actually implemented by Classic

This describes recovered Classic source behavior ONLY, not original GOD2 rules.

- `MariaDbRuntimeData.cs:493` loads enabled formal monster drops with quantity
  bounds, rate, guaranteed flag and source. It does not select rate units,
  drop groups, roll type, weights, exclusive groups or quest/map conditions.
- `MariaDbCombatRewardPolicy.cs` passes `DropRate ?? 0m` into
  `CatalogBackedCombatRewardPolicy` in `CombatRuntime.cs:1546`.
- Eligibility: monster/item IDs >0, minimum >0, maximum >= minimum, and either
  guaranteed or rate >0. For each death, each eligible matching row is checked
  once. Every successful row can grant; there is no exclusive weighted pool
  or fixed-N winner selection in this consumer. Separate checks do not by
  themselves prove statistical independence.
- The check is `guaranteed || R < clamp(rate, 0, 1)`, where
  `R = uint32(SHA256(input)[0:4]) / 4294967295m`. The integer divisor is
  `uint.MaxValue`, not 100, 10000 or sum(weights). The input is a 28-byte
  stack span containing death GUID, drop-table ID and ASCII purpose.
- Exactness caveat: purpose `rate` writes four of the final eight bytes;
  this method does not explicitly initialize the remaining four bytes.
  Thus the intended death/row determinism cannot be guaranteed from this
  method alone. Purpose `quantity` fills all eight bytes.
- Strict `<` means a non-guaranteed nominal rate 1 rejects the maximum hash
  value. Under an explicitly assumed uniform 32-bit hash model, for
  `0 < p <= 1`, acceptance is `ceil(p * (2^32-1)) / 2^32`. This mathematical
  implication is not an empirical or official rate claim.
- Fixed quantity returns minimum. Otherwise quantity is
  `min + hash32(quantity) % (max-min+1)`, inclusive bounds. Modulo need not be
  uniform when the span does not divide 2^32. No additional quantity rolls
  or original-game quantity law is established.
- The reward plan names the killer character. This proves this consumer's
  recipient field, not original ownership/party allocation behavior.

`tests/God2.RecoveredDatabaseImporter.Tests/Fixtures/native-writer-monster-drop.jsonl`
is explicitly a SELFTEST record: monster/drop identity `4102-221`, one observation,
observed rate 0.12, authoritative rate null, disabled default 0. Neither 12%
nor 0% is acceptable original drop authority.

## Concrete next work for the owning agent

1. Start with current mission 390 step 7 and its three exact item definitions
   (3406/3475/5091). Trace the current mission/encounter consumer that resolves
   the named enemies and maps to numeric server identities. Item display names
   and visual monster names must not substitute for that binding. Mission
   387 supplies the next two candidates; mission 202 supplies one more.
2. Obtain a READ-ONLY export of Classic `god2.monster_drop_relationships`
   including source hashes/identities, chance evidence, weight/roll/exclusive
   fields, conditions and `ProductionDropEnabled`. Join both its direct
   MonsterId and the migration-389 code chain, retaining unmatched rows.
   Compare with formal `god2_game.monster_drops`, retaining `drop_rate_unit`,
   source, policy and group. Migration 418's 47-row claim tells exactly what
   candidate set to request; no export or DB service was started here.
3. Follow XJZ target 900001 (then the other 214 keys) into the implementation
   or deployment configuration supplying `monster.drop.1` to
   `resolve_monster_encounter_drop`. Capture-target readiness flags alone
   cannot fill that configuration. Keep any server-designed values labelled.
4. Original exact rates require an authoritative rule/configuration plus its
   consumer: numerator/denominator or weight normalization, roll count,
   no-drop outcomes, exclusive/independent behavior, stack bounds and applied
   conditions. Observed successes and failures can estimate a rate only after
   the trial denominator and conditions are known; observations alone do not
   certify an exact original fraction.

## Reproducibility and hashes

SHA256 is over raw file bytes, not reserialized JSON or decoded text, unless
explicitly stated otherwise. These are observed snapshots; other agents may
subsequently update shared extraction artifacts.

| Root/path | SHA256 |
| --- | --- |
| S/tools/strike_lab/recover_monsters.py | `1b15e041c008f632f9a2b04d7dcb64192ba1746d89802fdb5787a9e9f62a1483` |
| S/docs/research/content-recovery-20260919.md | `d512bbd948b72a672fdbbbe9e71373d246a06d69ebaf444c0c9cd08fff48ec56` |
| S/artifacts/world-atlas/monsters.json | `93c48f2b999cd219f759fac718dcd11596136cc922a98727ad15197baabbe25a` |
| X/xjz_evidence.sqlite | `44048ee3d664f1418e60eaa267d46e4ba118aa3689fae03f7350d544a9fc1774` |
| C/Data2/Patch/eny.csvZ | `6aa84aeb0399e39e0db27eeebf9bb0f8b274fcbd609e1b83be3542a5d53f294c` |
| C/Data2/Patch/FightEny.csvZ | `887f721a429aaa394d79787ccbd42d544cbcc53a878802cd5f8d010e55dc5a6a` |
| C/Data2/Patch/Comm/gamedata.csvZ | `70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731` |
| C/Data2/Patch/Comm/Mission_data.csvZ | `659c8f38ffd9c34107969b449afd16488665a08970110910c9aed8448a0bb716` |
| C/Data2/Patch/Comm/NPCMission01.csvZ | `1ff497204b5cf77cbbccffdf1836d7aeee30e46980ac1e85d8d0a08a0a4bcda7` |
| C/Data2/Patch/Comm/FuDai_ItemList.csvZ | `b7224d4b37b4bf9ab4d1a12f4a4400e829b492adfc26009be9ba38e8dc2749e6` |
| C/Data2/Patch/Comm/FuDai_ItemList_Total.csvZ | `454a2c98e63bde55e70b141d5354a4e7b3cc3c1573880b1c0fb9f3a5ce89d6fd` |
| C/Data2/Patch/Comm/NewRouletteDesc.csvZ | `22a24dca14e6d9dc8738774c57f9e1e6c3031323343e4df582ac435cabcf3570` |
| L/db/imports/official/drop_tables/drop_tables.official.json | `10d6e3226f75cad5acc35ce17de540f1a441810f1a5b055546834af7b3925767` |
| L/src/God2.ClassicServer.Runtime/CombatRuntime.cs | `e8fab0865084e9da5f60386dffad4fc1589204f80e36f52af977cdd6d8d315a9` |
| L/src/God2.ClassicServer.Persistence/MariaDbCombatRewardPolicy.cs | `105d73016d5fbee1be3c30cc45b1c19ad5804e10e3a0698df77df802e71ddd7d` |
| L/src/God2.ClassicServer.Persistence/MariaDbRuntimeData.cs | `aa0b435a8f343c3fc2cc4af7fcaaf8bab34aa6fc4b782378243946a2ea01fbeb` |
| L/database/schema/300_apply_first_wave_monster_drop_server_design.sql | `143566df2a70b530f3d7079f50777f38bfcbe0cfedbf8d60d369233e32e0c0a3` |
| L/database/schema/389_sync_monster_drops_by_formal_monster_code.sql | `c5755b9b5815b9518cd5437dc0b2a83991306adfe6c0f63fe39e08f000a5f8e8` |
| L/database/schema/418_publish_monster_drop_gap_evidence_audit.sql | `86ac63f04757e535f626cf73705ea77f2435e3573c1ab40d8647ba2469e31eb8` |
| L/tests/God2.RecoveredDatabaseImporter.Tests/Fixtures/native-writer-monster-drop.jsonl | `a83799bd9a0e8ebb876d47b04074e022bd7b66f4179de2608be82aa0a9c7db4d` |

Decoded SHA256: gamedata
`75c3c37947a64b0917fbf8e546884d9bf893fe6a606d3e2b8f3b1857966b1815`;
FightEny `30aa86a6001919289090f924bbde727eab5e100ff4db6d71406e60260ed22c40`.

Validation run from S:

```powershell
python -B -m unittest discover -s tests/research -p test_recover_monsters.py -v
```

Result: 8 tests passed in 0.320s. Covers byte identity, deterministic extraction,
source headers, absent fields, no evidence promotion, invalid input rejection,
source overwrite rejection and read-only SQLite counts. These tests validate
the existing extractor; they do not prove original drop rates. Additional
in-memory Python inspections decoded the listed CSVZ sources, counted JSON
records and SQLite rows, and computed the hashes above. No new test file was
needed for this documentation-only deliverable.

Post-write check: PowerShell parsed all 20 raw SHA256 manifest rows above and
recomputed each with `Get-FileHash -Algorithm SHA256`; all 20 matched.
