# Current native quest rules audit — 2026-09-26

## Result

The current client supplies **418 mission definitions and 2,014 description
rows**, **169 ACTMIS requirement-display records**, and **85 daily-description
records**. Extraction is complete for these three pinned tables, with zero
structural issues. This does **not** establish complete executable quest rules.
For each of the 418 missions, original prerequisites, acceptance conditions,
progress transitions, rewards, NPC links and monster links remain unqualified
by these sources. The audit records every mission individually rather than
counting tests as completed quests.

This is a bounded current-source/code audit, not proof that unavailable rules
do not exist elsewhere. No retired corpus, database, running client, network,
desktop, Application, migration or importer was modified or used by this audit.

## Reproducible evidence

```powershell
python -X utf8 -B -m tools.strike_lab.native_quest_rules_audit_20260926 --output artifacts/reports/native-quest-rules-audit-20260926/audit.json
python -X utf8 -B -O -m tools.strike_lab.native_quest_rules_audit_20260926 --output artifacts/reports/native-quest-rules-audit-20260926/audit-optimized.json
```

Both executions passed and produced identical JSON SHA256
`b5a7154efa3614c964eb8209bd4da58650a4362fee6b9627fdb23fd5ffb8bce2`.
The tool uses explicit checks, not optimization-sensitive assertions. Full
source and decoded hashes, columns, per-mission gaps and dialogue file hashes
are in the report. It checks source pins before counting records.

| Source | Observed records | Implementable native scope | Missing authority |
| --- | ---: | --- | --- |
| Mission_data.csvZ | 418 definitions; 2,014 text steps | Exact id, name, declared description count, ordered CP950/raw description bytes; native journal reference projection | The next description is not a proven progression event or completion predicate |
| ActMis.csvZ | 169 records; 676 pairs, 169 nonzero | Native category-20 requirement labels, ordered lookup keys and quantities; scalar widths verified by prior native execution | Association with Mission_data, acquisition/turn-in event, ownership validation, consumption and rewards |
| DayMissionDesc.csvZ | 85 | Raw index/branch/name, NPC references, schedule/condition fields and display strings | Server clock/time units, reset semantics, enforcement, NPC namespace/placement and reward issuance |
| NPCMission01..15.csvZ | 14,600 keys | Exact text-key namespace; dialogue text presentation | Text key to quest/NPC/stage rule, branches, grants |
| DailyMission01.csvZ | 300 keys | Exact daily dialogue text | Daily-description relationship and execution rules |

NPC mission files contain **32 id-only rows** (15 in file01, one in file03,
16 in file07); preserve this shape rather than treating every key as nonempty
dialogue. File15 declares 600 rows; files01..14 each declare 1,000. The audit
finds no duplicate keys across these 15 files. This does not make the texts
authoritative scripts.

### Daily source and null fields

Compressed SHA256:
`4a347d56706946d7004b2bd2118500ffc60844628fa461862b2f6d5320a90e54`.
Decoded SHA256:
`2848b95b0af99eac10ca4dff61a5533c13917127c4738039e263c60a1be45eaf`.

Header-backed columns, one based: index, branch, name, start NPC ID, weekday
raw, start time raw, end time raw, discriminator raw, rebirth lower raw,
rebirth upper raw, end NPC ID, restriction text, description1, description2,
description3, start text, end text, reward text, accept count raw.

Indices **28, 29, 30, 33, 34**, all branch0, at physical lines **64, 65, 66,
69, 70**, contain only 12 columns. Columns13..19 are missing, not zero/empty
authoritative values. Eighty rows contain all 19 columns.

## Current EXE compatibility of existing evidence

Current EXE SHA256
`6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98`.
Prior native memory-image SHA256
`149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.

All six inspected spans match byte for byte after **PE RVA mapping**:

- Mission description lookup RVA `C9581..C95DB`.
- Journal writer `C9670..C9770`.
- ACTMIS row parser `587C4..588E1`.
- ACTMIS category20 display branch `B9F8D..BA060`.
- C2S85 producer `97DC0..97E00`.
- S2C7A receiver header `C7F10..C8240`.

End addresses are exclusive. This requalifies the inspected instructions,
not every transitive callee or a new full client gameplay run. Prior coverage
of 60,420 Mission_data text scenarios remains **text/display coverage**, not
60,420 quests. Prior ACTMIS composition covers 169 rows through bounded
3B-instance-to-tooltip slices, not authoritative collection/turn-in rules.

## Native contracts available for integration

- `RecoveredQuestSync`: S2C DB, 13 logical bytes, subtype4 batch/subtype5
  selected refresh, 15 journal slots. Packed lowWORD selects one-based mission;
  highWORD selects `max(value-1,0)` description. All15 batch records total195
  logical bytes. Clearing a display slot does not establish completion.
- `RecoveredQuestDialogue`, `RecoveredQuestAction`, `RecoveredQuestClose`:
  native dialogue response and C2S85/C2S86 codecs exist. C2S85 is seven bytes,
  preserves request/reply WORDs plus context and opaque stack tail; these are
  conversation fields, not assumed mission identifiers. Successful confirm
  need not send86. C2S86 pointer residue is not a durable quest identity.
- Existing importers already support pinned Mission_data display records and
  ACTMIS `DISPLAY_ONLY` pairs. `load_quest_description_counts()` verifies source
  identity and all2,014 records; owned journal persistence stores the raw15
  values with revisions. This is not a generic authoritative quest engine.
- `QuestRepository.h` remains a reserved interface and `game/Quest.h` a
  placeholder. The implemented town-guide flow uses explicit CUSTOM rules,
  durable stage/reward receipts and native wire projection. Its native text
  and protocol do not establish original stage/reward rules for other quests.

The extractor's `executable_transition_rules=0` is a source-authority count.
Its `server_integrated=0` is historical extractor scope, **not a current count
of runtime integration**. The parent lane is separately implementing the
formal definition/daily catalog import; this audit neither modifies that work
nor reports it as completed.

## New targeted daily parser lead

Static current reconstruction identifies `004569CA` dispatch of
`DailyMisDescNum` to `00457FF0`. The loader allocates316-byte (`0x13C`) rows
at resource+`FC2E0` and increments signed-WORD count+`FC2DC`.
`00458430(index BYTE, branch BYTE, output)` compares the two byte fields and
copies an entire row. Direct callers are `0048B9B0`, `0048C040` (daily UI)
and `00476570` (text formatting).

Observed loader mapping, using zero-based CSV columns:

| Columns | Native row output | Qualification |
| --- | --- | --- |
| 0,1 | BYTE +0,+1 | index/branch narrowing |
| 3,10 | WORD +2,+4 | start/end NPC fields |
| 5,6 | WORD +6,+8 | raw time fields |
| 8,9 | WORD +A,+C | raw rebirth bounds |
| 7 begins R/r | BYTE +E | discriminator flag |
| 18 | BYTE +F | raw accept-count narrowing |
| 4 | DWORD +10 bits | parser tests seven characters after its first character |
| 2,11..17 | strings +14,+32,+46,+6F,+98,+C1,+EA,+113 | name/restriction/descriptions/start/end/reward text |

This is **static decompiler evidence**, not yet an executed parser/eligibility
oracle. Preserve the source bytes first. Next useful proof is executing the
loader and daily UI consumers to establish weekday/time/rebirth display gates,
then tracing the actual accept producer and inbound server-state response.
Even client UI eligibility cannot alone prove original server reward rules.

## Exact missing rules before native quest completion can be claimed

1. An authenticated server-owned offer linking NPC instance, quest namespace,
   conversation and allowed response; numeric equality/text matching is insufficient.
2. Source-backed prerequisite edges and eligibility units, including daily
   clock/reset/rebirth/count semantics; no valid cycle verdict exists yet.
3. Event-to-state transitions, collection/kill targets, branch decisions,
   cancellation and repeat policies; description order alone is insufficient.
4. ACTMIS serial assignment and turn-in consumption policy, with atomic owned
   inventory validation and reward receipt deduplication.
5. Reward types/quantities, XP/currency/attribute formulas, and authoritative
   server outcomes; reward prose is not an executable ledger.
6. Per-quest original-client offer, accept, progress, turn-in, persistence and
   replay acceptance. A catalog import or a successful text renderer is not this test.
