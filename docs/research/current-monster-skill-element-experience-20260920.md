# Current Monster Skill, Element and Experience Sources: Lane 6

No identity-bound wild-monster/BOSS skill assignment, element value or base EXP
is proved. The concrete new result is a current CSV skill-alias reader and its
actual native consumers, with a source counterexample that prevents treating
every alias as a populated skill. This is source qualification, not recovered
monster coverage. Only this document and its matching tool/test are owned here.

- `docs/research/current-monster-skill-element-experience-20260920.md`
- `tools/strike_lab/current_monster_skill_element_experience.py`
- `tests/research/test_current_monster_skill_element_experience.py`

## New Native Evidence

Pinned image: `artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin`.
SHA256 `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
Base VA `400000`; hexadecimal RVAs equal exact image file offsets.

| Source / native RVA | Bounded conclusion |
| --- | --- |
| `gamedata.csvZ`, FightPetSkill, decoded header offset 2483701, line 21184 | 254 aliases; not 254 monster assignments. |
| `gamedata.csvZ`, NewFightPet2Skill, decoded header offset 2492739, line 21439 | 255 aliases; 50 are literally `SpcA00`. |
| `5896A..58A80`, `58B31..58C47` | Executed original row readers consume columns 0/1 only. Column 0 minus one must equal the explicit sequential row counter. Column 1 becomes two bytes. |
| `58A6A/58A7C`, `58C31/58C43` | Store bank and skill ID at `table + 2*(alias-1)` and the following byte. Owner pointer fields are `D2CC0` and `D2D78`. |
| `A2880..A28FD`, `A4F60..A4FE3` | Executed lookup entries use the low WORD of the alias, the signed WORD count at owner `D2CBC/D2D74`, and the corresponding two-byte table. Stop before `A9710`, with bank, ID and output pointers on the original call stack. |
| `AD9BD/ADA15 -> 59A60`, `ADA46/ADA5C` | Static caller frontier uses an item/template lookup, then template bytes `+11C/+11D`. `59A6F` indexes owner `B2D40 + 4*WORD-key`. This is not the EnyName identity lookup. |
| `ADA97/ADAC7` | Static type-1/type-2 branches select the two alias tables. No wild-monster identity or server permission/AI predicate follows. |
| `5C9B5..5C9DA` | Static tail of the already-known Category reader is loop control/return, with no extra column 9..11 access. Other consumers are not globally excluded. |

The original substring helper `5AC80`, case-insensitive comparison `155980`, and
original `atoi` `148317 -> 14828C` execute. Bank mapping is **A=0, B=3, C=2,
D=1**, not alphabetical bank numbering. The only adapted CRT operation is the
existing narrowly checked `%d` sscanf adapter used by column 0, returning to
`51BC9`. Successful replays use unchanged native instructions. A negative test
changes one VM code byte and verifies rejection before execution; no image file
or game callee is modified.

The concrete ambiguity example is alias **1**: FightPetSkill produces `(0,1)`;
NewFightPet2Skill produces `(1,67)`. A naked alias ID is therefore insufficient.
Source version, section and native consumer must accompany the value.

## Reproducible Data

The tool reads exactly current client `Data2/Patch/Comm/gamedata.csvZ`, current
`Data2/Fight/Spg/cbspec2.bin`, and the pinned image. Raw/decoded gamedata pins:

- Raw: `70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731`.
- Decoded: `75c3c37947a64b0917fbf8e546884d9bf893fe6a606d3e2b8f3b1857966b1815`.
- cbspec2: `7676acd93f164d071f7681a3fe74de94d65892759dbf2e69e3c0f748423d2f51`.

Every one of the 509 rows retains physical line, decoded byte offset, raw hex,
row hash, every field, native writer/consumer RVAs, actual reads/writes and
native pair. All rows run through both stages in the same VM. The original
tokenizer is used; counts, buffers, object pointers and row counters are explicit
synthetic loader prerequisites. This does not execute the full startup loader,
allocation, EOF handling, count publication, rendering or a live client.
The tokenizer width is explicitly supplied from each row's observed field
count: FightPetSkill has 240 four-field and 14 six-field rows; NewFightPet2Skill
has 191 four-field, 14 six-field and 50 three-field rows. All fields survive in
the report, although the row reader requests only columns 0/1. This is not a
qualification of the startup loader's field-count setup.

| Section | Source rows | Distinct pairs | Rows without populated definition |
| --- | ---: | ---: | ---: |
| FightPetSkill | 254 | 238 | 0 |
| NewFightPet2Skill | 255 | 203 | 50 |

All 50 unmatched rows produce `(0,0)` from literal `SpcA00`; first occurrence
is physical line 21460, decoded offset **2493413**, raw `21,SpcA00,NULL\r\n`,
row SHA256 `f46c19f803fba5ff60a902df1fbbce3ef908b5887cd4c3bce398f7497f3fbfc0`.
Even the original alias lookup passes this pair onward.
No interpretation as a valid skill, an empty repertoire, or a removed skill is
proved. Populated-definition offsets/hashes are a cross-check against the
existing cbspec2 identity parser, not execution of a native CSV-to-cbspec2 join.
The 48/448 targeting/behavior work and original catalog loader are not repeated.

`monster_identity_join` and `monster_skill_assignment` remain null on every
alias row; `runtime_eligible` is false. No values from companion tables or cards
are copied to monster records.

## Identity and Remaining Work

Main's handoff is accepted without recalculating pinned_catalog: 7,791 visible
records and 7,791 unique `(area,scene,ordinal)` keys. Names and source labels
are nonunique and are never used for value joins here. The artifact reports
this as handed-off identity context, not locally reproduced coverage.

The next skill proof needs an original monster assignment/decision producer,
joined by actual native identity or a source-versioned composite key and a
qualified consumer. The static template path above does not supply it. Existing
`83/action 3` cache evidence only establishes an incoming action pair; it is
not enumerated repertoire or server eligibility. Its prior proof is not rerun.

No second field family had a comparably concrete new source in this bounded
pass. Five-element values and base EXP remain unproved. The existing `89`
display consumer does not produce identity-bound base EXP; it is not repeated.
The Category tail adds no probability/base-token semantics or wild join.
This is not an absence claim across unexamined binaries or all client code.
Normal/BOSS/elite/event/quest/summoned completeness remains unknown.

## Verification and Process Scope

From `C:/Users/risei/Desktop/God2/God2-Server`:

```powershell
python -B -m unittest tests.research.test_current_monster_skill_element_experience -v
python -B -m tools.strike_lab.current_monster_skill_element_experience --summary
```

Omit `--summary` for full deterministic stdout JSON, including row provenance
and native traces. The tool has no output-file option. Tests cover all 509
source rows, same-index/different-section ambiguity, bank counterfactuals,
invalid/high-WORD alias inputs, definition holes, unchanged neighboring bytes,
source/code pin rejection, null wild authority and static-only frontiers.
Native instruction/read/write bounds and exact stop/stack checks fail closed.

Only the matching three files are written through apply_patch. No shared file,
database, desktop state, current source, build integration or other agent is
modified. No live game/server/UI/network or background process is started.
Focused suite: **7/7 passed in 23.380 seconds**, exit 0. The summary CLI also
completed with exit 0 and the exact counts above. All task-owned foreground
Python verification processes exited; no agents were spawned or persistent
processes left running. There were no writes outside the three delivered files.
