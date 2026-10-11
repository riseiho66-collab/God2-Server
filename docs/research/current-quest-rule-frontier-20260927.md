# Current quest rule frontier — 2026-09-27

## Concrete new result

Full original `004584A0` now executes to return against all **418 Mission_data definitions and 2,014 descriptions**. Two descriptions differ from the raw source bytes used by the previous staged lookup tests:

| Mission | Zero-based description | Source line | Raw bytes | Native bytes | Native CP950 decoding |
|---|---:|---:|---:|---:|---|
| 60 | 9 | 366 | 416 | 379 | Incomplete final character |
| 168 | 2 | 1121 | 380 | 379 | Incomplete final character |

Original tokenizer `00451BE0` limits each token to **0x17B = 379 bytes** in its 0x17C-byte field buffer. The full loader output proves this behavior on the actual source, rather than applying an assumed display limit. The evidence preserves the complete raw and native hex/hash for both records. Do not repair the truncated CP950 character and call that repaired text the native parser output.

This is a display qualification correction. **New executable prerequisite/progression/reward rules: 0.** No missing numeric reward or completion fields were found in the fully consumed Mission_data envelope.

## Inputs and authority

Read server AGENTS, implementation provenance, goal acceptance, current quest rules/EXE frontier reports, ACTMIS consumer and journal action/close reports, and the latest daily source/lifecycle reports. No retired source, production DB, client process, UI or desktop was used.

* Current God2.exe: `6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98`.
* Mission_data.csvZ: `659c8f38ffd9c34107969b449afd16488665a08970110910c9aed8448a0bb716`.
* Decoded Mission_data: `f57cb8d1a9426e2f797c9cdfea32beb07642415ae3e2bb30a8909373a1c0a5f0`.

The current PE is mapped by section RVA, after checking its complete hash. The unchanged original loader, row reader, tokenizer, numeric/string accessors, stack probe and inline copies execute. Only CRT allocation, fgets text-mode stream and decimal conversion have bounded adapters. This is an offline parser qualification, not quest UI rendering or playable quest completion.

## Complete source-to-record accounting

The source header is literally `編號,任務名稱,STEP,任務說明`. Definitions have three fields; descriptions have four. The native accessor trace records:

| Context | Accessor / source column, zero based | Calls |
|---|---|---:|
| Definition | 451B50 column0, mission ID | 418 |
| Definition | 451AE0 column1, name | 418 |
| Definition | 451B50 column2, description count | 418 |
| Description | 451B50 column2, STEP range check | 2,014 |
| Description | 451AE0 column3, text | 2,014 |

All **2,432 source rows** are consumed. The 40-byte native definition record contains signed-WORD description count at +0, a 34-byte name region at +2, and description-pointer-array DWORD at +36. Every byte before the pointer matches the independently reconstructed source name/count plus calloc padding. There is no reward, prerequisite or event field hidden in this record's padding. The native name copy is bounded to 33 bytes; the tokenizer bound is applied before the copy.

The actual source has sequential mission IDs and STEP labels. Two explicitly isolated input mutations qualify a subtle loader rule:

1. Swapping the first mission's STEP labels 1/2 while retaining physical line order preserves the native text-pointer order.
2. STEP0 leaves the corresponding pointer-array entry null and keeps the second text in its original slot.

Thus STEP is range-checked, but **physical read order** selects the array slot. This is not a native next-step state machine. The diagnostic mutated rows are not imported or relabeled as original source.

The fixture observes 2,433 allocations and a 251,024-byte aligned allocation arena. The output includes the exact parsed record bytes, original text bytes, allocator provenance, field accesses and code-span hashes. Pointer values belong only to this deterministic isolated fixture.

## Runtime impact: preserve raw provenance

Read-only inspection found the present server route does not send Mission_data description text as a native journal payload:

* `tools/strike_lab/import_native_quests.py:40–44` retains the complete `raw_record` and its hash. This is correct source provenance and must not be truncated.
* `src/db/NativeQuestCatalog.cpp:71–81` returns a source record with raw fields. It does not claim its returned text is the native parser's allocated display buffer.
* `src/db/SqliteRecoveredCharacterRepository.cpp:174` loads and validates description counts and source identity.
* `src/db/SqliteQuestJournalRepository.cpp:21` validates catalog counts/owned journal selectors.
* `src/core/Application.cpp:1483–1488` exemplifies journal projection: it validates a packed selector and encodes DB4. Other inspected journal routes likewise send selectors. The client chooses text from its own parsed table.

Therefore no live DB/source rewrite or journal wire change is warranted by this finding. Any future API exposing **native parsed display bytes** must distinguish them from full raw source fields. Custom notifications are a separate contract and do not justify silently shortening preserved source text.

### Existing test/document qualification to correct

`tests/research/test_current_quest_record.py:52` constructs `cls.texts` directly from full raw field3; line87 writes those same full bytes into synthetic VM strings; line187 uses them as expected text. Its loader-instruction check does not execute `4584A0` over the source. Consequently that test still verifies the original selector/lookup behavior, but its two oversized string fixtures do not match current native loaded strings.

`docs/research/current-quest-record-20260919.md:138–142` calls these expected original text bytes a full source comparison. Narrow that statement to the staged selector test or compose it with this full-loader output. Keep the 2,014-description/15-slot coverage count separate from quest completion. Parent owns any shared test/document fixes; this lane changes only its new files.

2026-09-27 parent follow-up: the shared test now executes `MissionNative.parse(418)`
before staging consumer fixtures, retains both raw and native text, and adds the
two long-description DB4/5 cases. The full seven-test suite passed in91.844s.
The historical journal report is corrected to distinguish staged lookup from
actual loader output. No formal source/catalog text was truncated.

## Exact remaining quest-rule edges

Current reconstruction xrefs to resource+`D2AC0/D2AC4` lead to `455AE0` cleanup, `4C9260` journal click, `4C9390` title/list rendering, `4C9550` description selection and `4C9670` journal-slot writer. The inspected consumers do not read the descriptions as executable conditions. `4C9670` recalculates journal page count and refreshes visible UI; it does not award or complete a quest.

Separate already-qualified chains remain distinct:

* DB4/DB5 stores server-supplied packed mission/description selectors. Clearing a slot is not an independently proved completion event.
* Dialogue7A → stored context/request/reply → C2S85/86 is a conversation protocol. The stored words are not automatically Mission_data IDs; mode4 choices and automatic follow-up85 behavior require existing issued-conversation binding.
* Category20 item instance WORD+8 → ACTMIS serial → `4B9F8D` requirement text remains an **instance-to-requirement-display** edge. Native 3B storage assignment is known, but authoritative server assignment, owned-item consumption, and reward issuance are not supplied by that display loader.
* The latest daily lifecycle evidence identifies D8 mode1 start/end controls as NPC transport-oriented, and mode2 as an auxiliary claim request. Their source display fields and per-player list state do not provide the original server reward/transition program.

The next useful source is the authority that fills those server-supplied selectors/instances and maps an issued NPC interaction to prerequisite checks, progress events, consumption and exact rewards. Further execution of a description renderer cannot supply that missing binding. This conclusion concerns the inspected current sources, not a global proof that no additional client resource can contain useful information.

## Reproduce

```powershell
python -m tools.strike_lab.current_quest_rule_frontier_20260927 --output artifacts/research/quest-rule-frontier-20260927/evidence.json
python -O -m tools.strike_lab.current_quest_rule_frontier_20260927 --output artifacts/research/quest-rule-frontier-20260927/evidence-optimized.json
```

Both PASS: full 418/2,014 source parser return and two diagnostic parser cases. Normal and optimized output are byte-identical, SHA256:
`4df4069e445661fa29d8d005e4ff99843e1263137275062b368455795d6cfb19`.

No shared runtime, database, original source asset or client binary was modified. This delivery strengthens source/display correctness and identifies a concrete regression-test correction; it does not claim all 418 quests are executable.
