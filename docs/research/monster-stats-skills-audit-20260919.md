# Monster stats and skills authority audit, 2026-09-19

## Scope and result

Bounded read-only audit of the existing recovery scripts/artifacts, BOTH legacy
corpora below, then targeted current-client tables and existing native skill
consumer evidence. Only this document was written. No game, UI, server, SQL
migration, artifact generator, shared runtime or drop recovery was run/changed.

The strongest additional numeric source is Classic migration 347: **170 external
monster candidate rows with all 16 requested numeric fields populated** (plus a
separate base-EXP field, outside this audit's requested matrix). It is
explicitly provisional external evidence, not original-server capture. There are
33 rows marked `awaiting_authenticated_capture` and 137 marked
`external_public_source_only`. Neither status authorizes current monster stats.
One separate legacy record claims level 6 for Xianhu (U+4ED9 U+72D0), client ID
27 / server ID 30; its HP was withdrawn and runtime eligibility is false.
XJZ contains zero monster stat captures and zero monster skill captures.

This audit confirms concrete source values and consumers, but promotes **zero
current monster stat values or monster-to-skill assignments**. This is a statement
about the inspected evidence, not a claim that all possible recovery is exhausted.

## Exact roots

- `S = C:/Users/risei/Desktop/God2/God2-Server`
- `G = C:/Users/risei/Desktop/God2/God2`
- `C = C:/God2Evidence/classic-20260820/files/God2-Classic-Server-Formal-Handoff-20260820-020345/ServerSource`
- `X = S/artifacts/legacy-evidence/xjz-20260820/files/XJZ-Server-Cpp/server_implementation`

Paths below use these explicit roots. Line numbers are one-based; CSV/SQL tuple
column positions are zero-based. Decoded client text is CP950; original bytes,
not terminal rendering, are authority.

## Per-field evidence matrix

`E` means `C/database/schema/347_import_17173_monster_attribute_numeric_evidence.sql`.
Its INSERT column contract is line 38, source row 1 is line 39, and there are 170
single-line tuples, each with 26 columns. Counts and NULL checks were performed on
the actual tuples using Python's CSV parser (single-quote SQL string delimiter),
without executing SQL. Example numbers below are literal **external source row 1**,
not proposed values for a current monster. No formulas were inferred.

`D` means decoded `G/Data2/Patch/Comm/ChangeDollCard.csvZ`, header line 4.
Its columns label card effects and must not be promoted to wild-monster stats.

| Requested field | E column / exact row-1 value | D column | Confirmed versus unproven |
| --- | --- | --- | --- |
| Level | 2 `source_level` = 1 | 6 | 170 external values; separate legacy Xianhu level 6 claim only; no current identity binding |
| HP | 3 `reference_hp` = 38 | 8 | 170 external values; legacy Xianhu maximumHp is NULL, explicitly withdrawn |
| MP | 4 `reference_mp` = 40 | 9 | 170 external values; no monster MP capture |
| Vitality / constitution | 11 `constitution` = 10 | 14 | 170 external values; import generator maps source `vitality` to SQL `constitution`; not proof of current runtime mapping |
| Strength | 10 `strength` = 25 | 15 | 170 external values; no monster stat capture |
| Intelligence | 12 `intelligence` = 25 | 16 | 170 external values; no monster stat capture |
| Speed | 13 `speed` = 10 | 17 | 170 external values; no monster stat capture |
| Physical attack | 5 `physical_attack` = 29 | 10 | 170 external values; no authoritative current damage/stat consumer binding |
| Physical defense | 7 `physical_defense` = 3 | 11 | 170 external values; no authoritative current defense binding |
| Magical attack | 6 `magic_attack` = 29 | 12 | 170 external values; XJZ capture schema calls it `magical_attack`, but has no rows |
| Magical defense | 8 `magic_defense` = 4 | 13 | 170 external values; XJZ capture schema calls it `magical_defense`, but has no rows |
| Metal | 14 `metal` = 0 | 18 | 170 literal external values; no current monster element-vector binding |
| Wood | 15 `wood` = 0 | 19 | Same boundary; zero here is an explicit source value, not an unknown-field default |
| Water | 16 `water` = 0 | 20 | Same boundary |
| Fire | 17 `fire` = 0 | 21 | Same boundary |
| Earth | 18 `earth` = 50 | 22 | Same boundary; do not normalize, redistribute or derive other elements |
| Skills / slots | E has no skill column | D special-ability columns start at 26 | XJZ 215 probe targets, zero captured monster skill rows; card abilities and skill books do not establish monster assignments |

E row 1 retains Big5 name hex `B5B3A4F2C06E`, candidate EnyName keys
`2:0:1;0:2:512`, join basis `simplified_traditional_normalized_name`, and status
`awaiting_authenticated_capture`. Its external-page hash is
`05658F584060B0F0CF4C31087791B4E4C21A25741D4AB8E43966A9A31B4A764B`.
These are stored provenance claims; the external web page was not fetched or
authenticated in this local audit. Name equality alone cannot resolve variants.
The generator `C/tools/GenerateMonsterAttributeNumericEvidenceMigration.ps1`
identifies the upstream archive entries
`payload/evidence/monster-attributes/17173-monster-table-normalized.csv` and
`payload/evidence/monster-attributes/17173-vitals-cross-check.csv` as the next
source documents for checking these candidate joins.

## Both legacy corpora and concrete consumers

Classic `db/imports/live/monsters/monsters.verified.latest.json`, record 0:
`clientMonsterId=27`, `serverMonsterId=30`, `level=6`,
`levelEvidenceStatus=VerifiedBattleActorDescriptor`, `maximumHp=null`,
`maximumHpEvidenceStatus=WithdrawnSourcePositionMisread`, `runtimeEligible=false`.
Its withdrawal reference is
`Artifacts/RecoveryFinal/monster-hp-claim-withdrawals-20260813.json#xianhu-126`.
Do not resurrect 126 as HP, or confuse the external table's unrelated literal 126
with that withdrawn claim. The original session is
`monsters-semantic-v2-20260811-112856-3ed58e2d`; rechecking that session's actor
descriptor and current identity is a concrete level-recovery step, not done here.

Classic `src/God2.ClassicServer.Persistence/MariaDbCanonicalCatalogRepositories.cs`:
line 89 reads enabled `god2_game.monsters` rows with level, HP/MP, four attributes,
five elements and all four attack/defense fields. Line 95 reads enabled
`god2_game.monster_skills` with monster ID, skill ID, trigger type/value,
probability, cooldown rounds and priority. These are the strongest existing
server consumer contracts. **Enabled is not an authenticity flag**: migration
294 lines 13-23 fills missing HP/MP, attack/defense and elements with server-design
expressions; lines 26-34 label the result provisional/mixed. Its expressions are
not original formulas. A future read-only export needs per-field provenance
alongside these consumer rows before any original-value promotion.

XJZ SQLite was opened with `mode=ro`; live counts were checked:

| Table | Rows | Meaning |
| --- | ---: | --- |
| `monster_stat_capture` | 0 | No observed level/HP/MP/attributes/attack/defense/element records |
| `monster_skill_capture` | 0 | No observed monster skill assignments/effects |
| `monster_skill_probe_template` | 215 | Capture targets, not known skills |
| `monster_stat_reverse_probe_source` | 89 | All `direct_monster_stat_apply=0` |
| `change_doll_card_stats` | 100 | Transformation card references |
| `skill_runtime_capture_target` | 767 | Documented split: 386 character/god, 166 pet, 215 monster targets |

The database's `monster_skill_probe_template` row `probe_id=1` has monster code 1,
`actor_skill_kind=monster_skill`, `wanted_field=monster_skill_slots_and_effects`,
`capture_target_table=monster_skill_capture`, `packet_evidence_boundary=1`.
It contains an observation request, not a skill ID. Reverse-probe `source_id=1`
is `change_doll_monster_stat_group`, explicitly card-effect/identity guidance,
with `direct_monster_stat_apply=0`.

XJZ `cpp/xjz_evidence_repository.hpp` lines 631-643 exposes stat capture targets
and routes. Lines 1552-1563 exposes `FindMonsterStatCaptures`,
`FindMonsterSkillCaptures`, `SaveMonsterStatCapture`, and `SaveMonsterSkillCapture`.
Those are concrete evidence ingestion/read boundaries. The stat schema has
identity/session/map, four base stats, four attack/defense fields, `element`,
raw packet/path and evidence status; the skill schema retains capture ID, skill
ID/name/slot, action kind, effects, raw packet and evidence boundary. An empty
schema is not a recovered stat table.

## Targeted current-client evidence

- `eny.csvZ`: 215 definitions, header line 4, records start line 5. Known fields
  are index column 0, ROM column 1, name column 8. Position-labelled columns are
  visual offsets, not HP/MP, combat attributes or world spawn positions.
- `FightEny.csvZ`: 215 definitions, header line 40, records start line 41.
  Known name/code/ROM/ally ROM columns are 0/1/5/6. Seven rows lack the ROM
  column; preserve absence. No implicit `field index + 1 = battle identity` join.
- `ChangeDollCard.csvZ`: 106 decoded lines, `ChangeDollCount,101` on line 5;
  101 records include index-0 random-card sentinel (line 6) and 100 other cards.
  Line 7 index 1 has literal HP=0, MP=10, vitality=30, speed=-15. These values
  belong to a transformation card; treating them as a wild-monster base vector
  would be mispromotion. Header columns 3/4/5 are Island/Area_id/Name_index,
  useful candidate identity keys only.
- `gamedata.csvZ`: line 21695 is `EnyName,7931`; line 21696 is
  `EnyNameTotal,7815`, followed by island/area grouping markers. These are distinct
  declarations, not a verified single denominator. Line 21699 is exactly
  `1,` + name U+4E09 U+7891 U+9D28 + `,1,0,15,3`; line 21703 is index 5,
  name U+91CE U+72D0, trailing values `1,0,27,3`. No stats semantics are assigned
  to those numeric columns here. This is the current identity/group source for
  the main agent's native enemy loader, not a numeric-stat replacement.
- `gamedata.csvZ` SKB marker line 8915 declares 381 books. Line 8916 is item
  6501, record SHA-256
  `60ecb5b6d632e5439a280cf53fa2b32755c5dc13b2507b4522b6a74dd1d5c2cb`.
  Named description columns 9/10/11 literally state 5 MP, attack range 3,
  single target. The artifact counts 243 MP descriptions, 217 range descriptions,
  275 scope descriptions; all are `description_only`. Four `Skill.csvZ` menu
  rows do not establish monster skill ownership. Trailing numeric SKB columns
  are not promoted to executable costs/range merely because they match text.

Existing current native consumer evidence in
`S/docs/research/current-skill-command-20260919.md` identifies lookup RVA
`0x1156A0`, accessors `0x11B8C0/0x11B900`, and selected-entry packing at
`0x11913D..0x11914B`. For kind 0 it emits entry byte 0; the selection index is
separate. Neither byte is proven to equal an SKB item ID or monster skill ID.
The pinned native image hash is
`149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
This audit read that existing evidence; it did not rerun native emulation.

## Strongest next bounded recovery

1. Preserve all 170 E tuples as candidates with field-level source provenance;
   check the 33 named joins against current EnyName group identity once the main
   loader proves it. Keep transformed-player/card, pet, visual and wild-enemy
   identities separate. This yields useful exact candidates without inventing
   any values or importing Classic design formulas.
2. For skills, trace the producer of the selected-entry byte/kind used by native
   lookup `0x1156A0` and packing `0x11913D`; then require an enemy actor/slot
   binding before associating any SKB definition. A proven client command shape
   alone does not establish enemy AI selection, cost, damage, or cooldown.
3. Use Classic repository lines 89/95 as the eventual stat/skill data contract,
   with provenance checks and actual XJZ capture records as evidence inputs.
   The existing enabled-only queries and 215 empty probe targets cannot supply
   that authority themselves.

## SHA-256 source manifest

| Exact root-relative path | SHA-256 |
| --- | --- |
| S/tools/strike_lab/recover_monsters.py | `1b15e041c008f632f9a2b04d7dcb64192ba1746d89802fdb5787a9e9f62a1483` |
| S/tools/strike_lab/recover_combat_skills.py | `95a7cc17faec2597c9c96aa12f8564273d4433e0728b31780e3feb31cbcccdbc` |
| S/artifacts/world-atlas/monsters.json | `93c48f2b999cd219f759fac718dcd11596136cc922a98727ad15197baabbe25a` |
| S/artifacts/world-atlas/combat-skills.json | `ee64c6b99db2b5aa1188616696656304f608e6ef86700c273992d685240c6e7e` |
| C/database/schema/347_import_17173_monster_attribute_numeric_evidence.sql | `b9b574d48e644688458402152937bc24720bf6d08e5f2e0ff399cfff922be569` |
| C/database/schema/294_apply_monster_combat_stat_server_design_values.sql | `d5c70e5f81550fcc941bea09bfff43a1450c0ac29828e26d0be5e619c00dc9df` |
| C/db/imports/live/monsters/monsters.verified.latest.json | `074d2bd204b4bf7d1c05d997f7f38c6c6e767c1108293c6ba9ff178f790d0999` |
| C/src/God2.ClassicServer.Persistence/MariaDbCanonicalCatalogRepositories.cs | `f31f95755f9b9dbc7a048ccc11b1f74b474a73f5c870f9f1a4c8c3aa22593a27` |
| X/xjz_evidence.sqlite | `44048ee3d664f1418e60eaa267d46e4ba118aa3689fae03f7350d544a9fc1774` |
| X/cpp/xjz_evidence_repository.hpp | `abb65e82ef52406fe0f768c076987b2495b11d32ebc7add605cb298d20bd7520` |
| X/evidence-monster-client-v0.md | `b53e3c7a2b8159effea827171813a56f9d566c8a14cfe87192892adc0bcd0c85` |
| X/evidence-skill-runtime-capture-target-v0.md | `7cf668ef1cf3427a51d27ace060f026cde193f83d85e7a1d37ddeb40bea576a6` |
| G/Data2/Patch/eny.csvZ | `6aa84aeb0399e39e0db27eeebf9bb0f8b274fcbd609e1b83be3542a5d53f294c` |
| G/Data2/Patch/FightEny.csvZ | `887f721a429aaa394d79787ccbd42d544cbcc53a878802cd5f8d010e55dc5a6a` |
| G/Data2/Patch/Comm/ChangeDollCard.csvZ | `4d51b22d51c14bc98b6ec96c16a40384a226e9fa1f90543ea58a36fb4b56ebd2` |
| G/Data2/Patch/Comm/gamedata.csvZ | `70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731` |
| G/Data/Patch/Skill.csvZ | `1dc049cb4ac19fd753c17af64932c40f4e833a1dac92a8d0d33a44529a9a7e16` |
| S/docs/research/current-skill-command-20260919.md | `8f048b54be69c399d6c00b5300cf2c51ee95127153515fa8f5b288a3d776a0a6` |

## Verification

Executed from S with bytecode writes disabled:

```text
python -B -m unittest discover -s tests/research -p test_recover_monsters.py -v
python -B -m unittest discover -s tests/research -p test_recover_combat_skills.py -v
```

Passed 8 monster tests and 6 skill tests. Existing tests already exercise visual
position/legacy-claim non-promotion, withdrawn HP, byte-identical extraction,
description-only skill metadata and fail-closed lookup. No new regression file
was necessary for this documentation-only audit. These tests do not authenticate
the 170 external candidate rows or recover missing original monster stats.

## Main native identity follow-up

Main then implemented `test_legacy_stat_candidate_names_against_original_enemy_lookup`
in `tests/research/test_current_world_actor.py`. The test pins migration 347's
hash, parses its 170 tuples with the standard CSV parser, and takes the 95 keys
from its 33 named rows to the actual original 5A0A0 lookup after complete native
EnyName loading. It does not query a Python name-map in place of the client.

Interpreting each key as current (area, scene, one-based native record ordinal):
72 returned names match the retained Big5 bytes, and 23 do not. All keys agree
for 31 source rows; source row 6 has 15 mismatching keys and source row 16 has
8. Every key resolves to a record, so this is not a missing-memory/empty-table
artifact. These old keys cannot be adopted blindly as current native identities.
Matching names likewise do not authenticate the attached numeric values or
resolve all variant distinctions. No stat value is promoted to original authority.

Exact focused verification:

```powershell
python -B tests/research/test_current_world_actor.py -v CurrentWorldActorTests.test_legacy_stat_candidate_names_against_original_enemy_lookup
```

Passed 1 test in 74.387 seconds, including construction of the original loader
and source-backed tables. This is additional to the 18 actor/scene regressions
reported in `current-world-enemy-groups-20260919.md`, not a live client session.
The wrong-name mappings remain rejection evidence, not automatically repaired
using a nearby name, row number or invented server monster ID.
