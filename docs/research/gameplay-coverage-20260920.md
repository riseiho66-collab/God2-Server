# Whole-Source Coverage And Remaining Gameplay Work

This replaces small test-function counts as the coverage summary. It measures
the pinned current-client sources and explicit offline behavior matrices, not
playable-game completion. The C++20 core, Lua ownership and production database
are unchanged by this coverage work. No retired archive is used.

## Measured Denominators

| Scope | Source coverage | Executed behavior cases | What passes mean |
| --- | --- | ---: | --- |
| Skill definitions | 448/448 (100%) | 18,816 | Original target helper versus formal C++, 14 actors and three explicit states |
| Mission descriptions | 418/418 missions; 2,014/2,014 text rows (100%) | 60,420 lifecycles; 1,712 boundary cases | Both DB4/DB5 and all15 journal slots, exact text, replay, clearing and peer preservation |
| EGG/SPP entries | 55/55 (100%) | 14,080 guard cases | All byte slots, qualified source-presence joins; not hatch transactions |
| Companion instance input | All50 valid store slots and all206 invalid byte slots | 8,024 | Two dispatches, two auxiliary states, 36 patterns for in-store slots; native copies/interceptions/rejections |
| Quality/Star display | All16x16 selector pairs, two modes, two noise patterns | 1,024 | Exact native table reads and display arguments |
| Growth source records | 5,023/5,023 provenance rows (100%) | 470 native-loaded rows | Original loading of4 title,464 category and2 QualityStar rows; not growth formulas |

The seven companion-source files also have a33,834-physical-row byte/hash ledger.
Physical lines, data records, operations and scenarios are distinct denominators;
they must not be summed into a fabricated feature count. The current extractor's
source groups are not asserted to exhaust every possible pet/gameplay rule.

## Not Completed

- Each of damage, hit, crit, five-element coefficients and resource cost has
  zero verified authoritative formulas across448 definitions. The matrix records
  2,240 unresolved definition/rule pairs, not2,240 known distinct formulas.
  There are294 mode-zero setup cases still unqualified and84 definitions rejected
  by the native kind gate. Helper execution does not authorize actual skill use.
- Mission acceptance, progress triggers, main/side classification, prerequisites,
  rewards and authoritative cross-table relations remain unqualified. The169
  requirement and85 daily rows are separately enumerated; the new lifecycle matrix
  does not execute their gameplay. Earlier bounded requirement-parser evidence
  remains separate. Description selectors are not proven gameplay stages.
- Pet growth/EXP, hatch probabilities and outcomes, timer semantics, costs and
  transactions remain unknown. The egg source index is not a recovered native
  item metadata loader. Slot copies and display values do not establish authority
  for constructing those values on the server.
- Live original-client battle is not certified. Continuous bootstrap reaches
  RVA110228, with53 sprites and38 child controls, but has not returned from the
  entire initializer. A separate20-case original3B store-to-battle-read proof
  identifies owner+85A30 as slot44's first WORD. It does not splice synthetic
  owner data into the bootstrap or qualify the subsequent resource lookup.

No overall playable percentage is calculated: its full acceptance denominator
has not been established. The100% values above apply only to enumerated source
coverage, not functionality, formulas or live gameplay.

## Findings And Regression Policy

- Invalid-slot DB5 writes selection before its assertion; tests preserve this
  observed behavior instead of claiming atomic native rejection.
- NewCombatPet_Category declares469 but contains464 data records; no invented
  extra records are inserted.
- Invalid packet slots, stale UI state, duplicate/omitted entries, wrong hashes,
  changed outcomes and unsupported authority promotion are checked explicitly.
- CTest uses setup fixtures to regenerate each report with actual native runs
  before its audit. A failed generation prevents its audit passing on old JSON.
  Quest and pet audits additionally rerun the native matrix and require exact
  byte-identical reports. Skill audit also checks the formal executable hash.

Run from the server root:

```powershell
ctest --test-dir build -C Release --output-on-failure -R '^(skill_coverage_matrix|quest_coverage_matrix|pet_egg_coverage_matrix|battle_owner_slot_binding)$'
```

Detailed source pins, branch boundaries, individual records and commands:

- [Skills](skill-coverage-matrix-20260920.md)
- [Quests](quest-coverage-matrix-20260920.md)
- [Pets and eggs](pet-egg-coverage-matrix-20260920.md)
- [Battle owner slot source](battle-owner-slot-binding-20260920.md)

The three coverage workers delivered, were reviewed and closed. Independent
main integration verification is recorded in the reconstruction status ledger.

## Subsequent Formula-Focused Batch

At the owner's explicit request the same three workers were immediately reused
for actual damage/hit/critical dataflow, not further coverage accounting.
Their delivered executable findings are:

- [Damage](current-damage-formula-20260920.md): received signed-WORD accumulation,
  replacement, and actor scalar wrapping-add/sign-floor/signed-cap arithmetic.
  Intervening formatting remains an explicit staged-execution boundary.
- [Hit](current-hit-formula-20260920.md): a continuous original incoming action
  path binds supplied outcome8 to the evasion label. No hit probability is
  computed in that bounded path.
- [Critical](current-critical-formula-20260920.md): the original CRT random
  recurrence/modulo100 feeds a numeric action argument; it is not a demonstrated
  critical threshold. Supplied values are not doubled in the tested prefixes.

These change the known computational/dataflow boundaries, not the authoritative
formula-completion denominator. All three workers are closed after review.
