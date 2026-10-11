# Bounded quest player journal scenarios

2026-09-19. Four executable scenario runs pass against the pinned original x86
instructions. This establishes offline journal projection behavior for DB4/DB5,
not playable main/side quests, server gameplay correctness, or live player E2E.
Unknown rules remain explicitly UNKNOWN, never a zero value or a default rule.

## Deliverables and commands

Only these new files belong to this task:

- `tools/strike_lab/quest_player_scenarios.py`
- `tests/research/test_quest_player_scenarios.py`
- `docs/research/quest-player-scenarios-20260919.md`

From `C:/Users/risei/Desktop/God2/God2-Server`:

```powershell
python -B tests/research/test_quest_player_scenarios.py -v
python -B -m tools.strike_lab.quest_player_scenarios
python -B -m tools.strike_lab.quest_player_scenarios --json
```

The default runner prints source identities, remaining unknown rules and four
scenario results. `--json` additionally prints each recorded action, journal
state and selected source-text bytes/line. Output is stdout only. A failed
identity, native stop, canary, pointer, byte or state assertion fails the run;
missing evidence is an error, not a skip or a successful empty report.

The runner reuses `test_current_quest_record`'s VM/description harness and
`test_current_quest_sync`'s dispatcher, which use the existing route oracle's
bounded x86 execution. It does not call their `setUpClass`, build fixtures, or
launch executables. The new tests forbid subprocess creation with a failing
`subprocess.Popen` guard. There are no client/server processes, UI automation,
sockets, public servers, compiler invocations or shared build outputs. Python
is the offline test runner. No CMake/shared source changes are involved.

## Evidence and authority

Read before implementation: `recover_quests.py`, `test_recover_quests.py`,
`test_current_quest_record.py`, `test_current_quest_sync.py`,
`current-quest-record-20260919.md`, `current-quest-protocol-20260919.md`,
`quest-recovery-20260919.md`, `quest-blackbox-followup-20260919.md`, and
`src/protocol/RecoveredQuestSync.h`.

Original mapped image, base `0x400000`, file offsets equal RVAs:
`artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin`.
SHA-256 `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.

Original source `../God2/Data2/Patch/Comm/Mission_data.csvZ`:
source SHA-256 `659c8f38ffd9c34107969b449afd16488665a08970110910c9aed8448a0bb716`;
decoded SHA-256 `f57cb8d1a9426e2f797c9cdfea32beb07642415ae3e2bb30a8909373a1c0a5f0`.
All three identities are checked before emulation. The extractor validates
headers and structural issues; the harness checks contiguous IDs and description
order before constructing resource arrays from the original text bytes.

Both legacy corpora were consulted first as references, not original authority:

- Classic root `C:/God2Evidence/classic-20260820/files/God2-Classic-Server-Formal-Handoff-20260820-020345/ServerSource`:
  `src/God2.ClassicServer.Protocol/OfficialMissionSlotSyncWire.cs`, SHA-256
  `869fa1db13feea2d34278fac113985f19ca070ea1b7b61c234fd805a4d38291b`,
  describes three-byte DF for another build. It is not this image's DB contract.
  `db/imports/official/quests/quests.official.json` lines 32-45 explicitly list
  missing gameplay semantics/rewards/state and disable gameplay import. Its
  `questType` presentation field is not a proven main/side runtime classifier.
- XJZ root `artifacts/legacy-evidence/xjz-20260820/files/XJZ-Server-Cpp/server_implementation`:
  `evidence-quest-service-template-v0.md`, SHA-256
  `6a81782ed8d137de13c08ce10b16793c8b757e81377cbe633ad401f5c6d697ff`,
  includes inferred names and reconstructed relationships, none adopted here.
  `evidence-quest-reward-capture-target-v0.md`, SHA-256
  `b78bdd4aae70bb7dfc000a86d58f31d29305940bfac01880c31a54c0ae2eff4c`,
  records zero authoritative reward rows/samples. This is missing evidence,
  not evidence that original rewards equal zero. Its separate daily reward
  data is not used as a Mission_data join or an executable reward formula.

## Actual source entries

The scenarios use three actual rows from the 418 definitions/2014 descriptions.
Counts here mean description rows, not objectives required for completion.
Names are preserved as raw CP950 hex in the runner's report.

| Mission ID | Definition line | Description rows | Original name bytes, hex |
| --- | --- | --- | --- |
| 1 | 4 | 2 | `5babb0c2eda5f4b0c85dabb0c2edc251bec9` |
| 165 | 1071 | 29 | `5bafaba550a5f4b0c85db0d3b77cbed4aaa7` |
| 418 | 2427 | 8 | `5ba544bd75a5f4b0c85d20acc9adadb8d1b0a34949` |

ID 418 has the literal title prefix `[\u4e3b\u7dda\u4efb\u52d9]`
(main-line quest); ID 1 has a town-quest title and ID 165 a deity-quest title.
No definition name contains `\u652f\u7dda` (side-line) in this pinned catalog.
These are source-text observations only. Neither non-main title is reclassified
as a side quest. Formal main/side classification and differing gameplay rules
are UNKNOWN. Legacy labels, title words and displayed reward/objective claims
are not counted as runtime verification.

## Native execution boundary

- Synthetic 13-byte logical S2C DB records enter the real dispatcher at RVA
  `68B61`, follow `6B44E -> 854F0 -> C9670`, and return at `6B517` with balanced
  stack. These are test stimuli, not captured traffic or C++ encoder output;
  the new lane makes no additional production codec differential claim.
- Description calls execute `C9550` including its real list-selection helper.
  Click slices begin at `C92EA` with page and click registers staged by the
  existing oracle. Both stop before the renderer at `10F580`. Exact pointers,
  original text plus terminating NUL, and selected packed values are checked.
- Refresh observations hook the actual `C9170` entry without replacing it.
  The closed/uncreated widget follows its real return path. No game functions,
  renderers or quest functions are stubbed; no image instructions are patched.
- Synthetic resource arrays use the original loader's established 40-byte row
  layout; description pointer arrays/text are read-only. This run does not
  execute the source loader. Image and source identities bind it to previous
  loader evidence. Adjacent journal/page canaries are checked after actions.
- The empty initial journal, selection zero, one page and suppression flag one
  are explicit test preconditions. They are not recovered new-character data.
  Page selection is staged, not an emulated page-button/input event; boundary
  probes may stage page 2 even when invalid references yield only one page.

## Scenario results

| Scenario | DB4 | DB5 | Native observations checked |
| --- | --- | --- | --- |
| Receive/page/select/replay/clear | PASS, 31 observations | PASS, 31 observations | Full ordered state sequence and text pointers/bytes |
| Description/slot/truncation bounds | PASS, 43 observations | PASS, 43 observations | Empty fallback, preassertion behavior and read faults |

Lifecycle: receive first-description references for IDs 1/165/418 into slots
0/5/14, inspect and select on all three staged pages, replay slot 14 twice,
replace each with its actual last-description reference, inspect/select again,
clear slots 14/5/0 with duplicate clears, then deliver an old slot-14 record.

Observed exact behavior under those inputs:

- Sparse eligible slots 0/5/14 produce 1/2/3 pages, despite only three occupied
  slots. Clearing 14/5/0 produces 2/1/1 pages; clearing 14 from current page 2
  resets the current page to 0. This is display positioning, not quest counts.
- After the initial receives, two identical slot-14 replays produce cumulative
  refresh-call counts 1/2 for DB4 and 4/5 for DB5. DB4's first slot-14 write
  consumes suppression without refresh; subsequent replays call refresh.
  DB5 refreshes each time. Repeated slot bytes do not imply no side effects.
- DB4 clear preserves the previously selected packed value `0x000801A2`.
  DB5 clear selects zero. Duplicate clears leave slot bytes clear but retain
  the subtype-specific refresh behavior. An old record after clear repopulates
  slot 14 and selects its first description when clicked: no journal consumer
  replay rejection was observed. This says nothing about reward deduplication.
- Mission 1 selector 0 and selector 1 produce the same source text (line 5)
  while retaining distinct packed values 1 and `0x00010001`. Neither selector
  is assigned an acceptance-state meaning. Selector 2 uses its second text;
  selector 3 and `0x8000` select the native empty string, not a completion state.
- Packed values 0, `0xFFFF0000`, 419 and `0xFFFFFFFF` remain stored, while their
  invalid mission references produce empty descriptions. A click on an invalid
  description preserves the selection that existed immediately before the
  click, including any prior DB5 write to that selection.
- Invalid slot indices 15, 255, `0x80000000`, `0xFFFFFFFF` stop before the
  original assertion call at `C9688`. Existing populated slots/pages/flags and
  refresh counts are unchanged. DB4 preserves selection; DB5 has already
  written `0x000801A2` to selection. Assertion continuation is NOT executed.
- For each subtype, all nonempty truncated lengths 1..12 end at an unmapped
  packet boundary and raise a native memory fault, preserving the populated
  journal snapshot. This proves neither graceful native rejection nor server
  validation of malformed traffic. Empty records are outside this dispatcher
  harness; strict codec length checks belong to the pre-existing codec tests.

Verification on 2026-09-19: the final guarded test run exited 0, `Ran 7 tests
in 2.311s`, `OK`. The default CLI passed all four scenario runs, with 148
recorded observations in total. The complete `--json` output was also run and
successfully parsed with PowerShell `ConvertFrom-Json` (exit 0).
No skipped tests or fabricated successful returns. The previous record test's
2855-value sweep and C++ compilation were not rerun or counted as new results.

## Existing unsupported defaults encountered

Read-only findings, not edited and not claimed to execute in a live session:

- `src/game/Quest.h:5-8` labels the structure a placeholder but initializes
  `id = 0` and `state = QuestState::Available`. Neither is established as an
  original initial quest state; UNKNOWN must not be represented by those
  values in an eventual authoritative implementation.
- `scripts/quests/test_quest.lua:2-9` registers synthetic ID 2001, name
  `Welcome to GOD2`, and acceptance/completion logging hooks.
  On the final reread, `scripts/bootstrap.lua:3-5` requires `fixture_bootstrap`
  only under `GOD2_FIXTURE_MODE`, and `scripts/fixture_bootstrap.lua:2,5` guards
  and loads this quest. This supersedes the direct bootstrap require observed
  earlier during the task; the shared change was made outside this lane.
  These are gated demonstration content, not original mission data or verified
  accept/complete rules, and not evidence of unconditional live loading.
- `src/scripting/ScriptQuest.h:7-8` exposes on_accept/on_complete hooks;
  `src/scripting/LuaEngine.cpp:310,314` invokes registered callbacks. Those
  extension points establish no original eligibility, transition or reward
  semantics. `src/db/QuestRepository.h` is explicitly a reserved interface.

These are the quest-related defaults encountered in this bounded read, not a
server-wide data/formula/attribute audit or a finding that all other defaults
are valid. No original attribute/reward values are invented by this task.

## Exact remaining unimplemented or unverified rules

Authoritative main/side classification; prerequisites, level/rebirth and
availability conditions; NPC dialogue and acceptance; objective increments,
branches and dependencies; completion/turn-in; item/EXP/money reward IDs,
amounts, formulas and claim deduplication; abandonment/repeat/reset rules;
ACTMIS/daily namespace joins; persistence and authoritative initial state;
C2S requests and server session authorization; actual page-button/input flow,
open-widget rendering, and live player E2E all remain UNKNOWN or unexecuted.

None is supplied as a guessed default, zero reward, inferred text rule, or
legacy-code authority. This lane closes with runnable journal scenarios and
their evidence; it does not declare main/side quest gameplay implemented.
