# Quest Black-Box Integrity Validation, 2026-09-20

## Result and qualification

Three focused regressions pass, with eight parameter cases. They exercise the
original current client's instructions in an offline Unicorn VM, using the
existing `NativeClose` harness and DB dispatcher fixture contract. This is
**original-native, offline, synthetic-state evidence**. No formal loopback
server or live E2E session was run. No new runtime defect was demonstrated.

The added coverage puts dialogue/close and journal sync in the same VM. Existing
tests mostly inspect these paths separately. Packet order here is an adversarial
test schedule, not a recovered gameplay sequence or captured server exchange.

Only these paths were created:

- `tests/research/test_quest_blackbox_integrity.py`
- `docs/research/quest-blackbox-validation-20260920.md`

No shared harness, runtime, CMake, status file, Lua, SQLite, or C++20 code was
changed. No database was opened. No desktop interaction, client process,
external server, child agent, compiler, or build-output write was used. Tests
guard `subprocess.Popen`, `socket.socket`, and `sqlite3.connect` against use.

## Evidence and fixture

Read the existing `quest_player_scenarios.py`, `current_quest_action.py`,
`current_quest_close.py`, `current_quest_instance.py`,
`current_quest_requirements.py`, and relevant research tests/documents first.
No retired archive files were opened or used as authority.

`journal.Evidence()` checks the image and current sibling client Mission_data
pins; `NativeClose` independently qualifies the same image before execution:

| Input | SHA-256 |
| --- | --- |
| `artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin` | `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763` |
| `../God2/Data2/Patch/Comm/Mission_data.csvZ` | `659c8f38ffd9c34107969b449afd16488665a08970110910c9aed8448a0bb716` |
| Decoded Mission_data | `f57cb8d1a9426e2f797c9cdfea32beb07642415ae3e2bb30a8909373a1c0a5f0` |

The journal uses the existing closed-widget precondition, 418-entry catalog
count, synthetic nonnull table pointer, adjacent canaries, and initial zero
slots. Catalog rows are not needed by this closed display path. Packed values
`00010001` and `000801A2` reference descriptions already used in the player
scenarios; they do not establish quest ownership or progression.

Dialogue preparation reuses the existing synthetic request `1234`, reply
`8002`, context `9A`, source dword `DEADBEEF`, and empty UI backing. A three-byte
queue prefix is an opaque preservation canary, not an asserted wire record.
The DB dispatcher setup follows `CurrentQuestSyncTests.dispatch`, relocated
to the existing NativeClose VM, including the outer-object data page already
mapped by `CurrentQuestSyncTests.vm`. Original code and callees are unmodified.
Each native call retains the harness's 20,000-instruction bound.

## Exact findings

1. **Close and sync identity separation, two cases (DB4 and DB5).** Native sync
   fills slots 0 and 14 with `00010001` and `000801A2`; page/count become `(0,3)`.
   DB4 leaves selection zero and consumes suppression at slot 14. DB5 selects
   `000801A2` and leaves suppression one. Direct close returns with exactly
   `86 ef be 00 10 85 34 12 02 00 9a 84` appended after the existing prefix.
   Journal slots, page/count, selection, suppression, and canaries remain
   unchanged. Thus, in these fixtures, selected journal bits do not replace
   the close source word or dialogue request/reply fields. The whole queue
   region through the eight-byte capacity canary is checked against the
   original bytes plus that exact append, not merely against the reported
   append length. Close leaves active/action-state/high-flag zero, choice -1,
   and queue count 15. A subsequent slot-14 sync replacement preserves all
   dialogue globals, close gates, and the entire queue. Repeated close returns
   with no new producer calls or changes to any snapshotted region.

2. **Invalid mode-4 choices, two cases (-1 and 8).** With a populated DB5
   journal, pending high flag, active dialogue, and nonempty queue, action
   stops at the original error entry RVA `75D60`. It does not return success,
   call a request producer, append bytes, or alter the six snapshotted regions.
   Observed memory writes are confined to the stack. The error function and
   its continuation are not executed; this is a boundary result.

3. **Truncated sync, four cases (DB4/DB5 at lengths 9 and 12).** These lengths
   supply a complete slot index but respectively none or three of the four
   packed-value bytes. With dialogue and journal state already populated,
   each faults with `UC_ERR_READ_UNMAPPED` (6): RVA `8565B` for DB4, `85693`
   for DB5. The test pins these PCs so an unrelated fixture fault cannot count
   as a passing malformed-input result. All six regions remain byte-identical,
   input bytes remain unchanged, and no observed non-stack write occurs.

The six byte-for-byte snapshot regions are the full UI allocation, 16 dialogue
global bytes, full queue allocation, close backing, resource allocation, and
NPC text pointer table. Stack/register setup and the input page are intentionally
excluded from equality snapshots; the input record is checked separately.

These results do not establish general packet atomicity. Existing native tests
already show that DB5 invalid-slot handling writes selection before assertion,
and truncated 7A ingestion can change context before faulting. This addition
does not rerun or generalize those cases. It also does not test socket stream
coalescing, transport framing/flush, populated-widget rendering, original
server validation, acceptance, rewards, persistence, or a journal/ACTMIS join.

## Commands and results

Working directory: `C:/Users/risei/Desktop/God2/God2-Server`.

Final focused command, after adding the fault-PC assertions:

```powershell
python -B tests/research/test_quest_blackbox_integrity.py -v
```

Exit 0: `Ran 3 tests in 0.263s`, `OK`; all eight parameter cases passed.
Only this new test file was run, not the research suite. The `-B` flag prevents
Python bytecode output.

After the user's main-integration completion notice, the same focused command
was rerun without test-code changes: exit 0, `Ran 3 tests in 0.250s`, `OK`.
The reported 56 battle tests and five adjacent CTest checks were not rerun or
independently verified by this quest lane. The deliverable remains limited to
the two paths above and is ready for an independent focused rerun.

The same command initially exited 1: three tests, eight setup errors in
0.186s. The combined fixture initially lacked the established outer-object
page. This read-only diagnostic identified the fault:

```powershell
@'
import sys
sys.path.insert(0, 'tests/research')
import test_quest_blackbox_integrity as t
from unicorn import UC_HOOK_MEM_INVALID
case = t.QuestBlackboxIntegrityTests()
case.evidence = t.journal.Evidence()
n = case.native()
n.vm.hook_add(UC_HOOK_MEM_INVALID, lambda vm, access, address, size, value, data: print('unmapped', hex(n.getreg('EIP')-t.q.BASE), hex(address), size) or False)
try:
    case.dispatch(n, t.journal.packet(0, 4, 0x10001))
except t.UcError:
    print('last_trace', [hex(rva) for rva in n.trace[-12:]])
'@ | python -B -
```

Exit 0; observed `unmapped 0x6b44e 0x1aba7e14 4`, trace `68B61, 6B44E`.
Mapping the same data page used by the existing sync fixture resolved all
eight setup errors. The next focused run exited 0 in 0.244s. This was a test
fixture correction, not a native/client/runtime fix. On the final fixture,
that diagnostic no longer faults.

The exact diagnostic used to qualify the four truncation fault PCs was:

```powershell
@'
import sys
sys.path.insert(0, 'tests/research')
import test_quest_blackbox_integrity as t
case = t.QuestBlackboxIntegrityTests()
case.evidence = t.journal.Evidence()
for subtype in (4, 5):
    for length in (9, 12):
        n = case.native(queued_count=3)
        case.dispatch(n, t.journal.packet(14, 5, 0x801a2))
        try:
            case.dispatch(n, t.journal.packet(0, subtype, 0x10001)[:length])
        except t.UcError as error:
            print('subtype', subtype, 'length', length, 'fault_rva', hex(n.getreg('EIP')-t.q.BASE), 'errno', error.errno)
'@ | python -B -
```

Exit 0; DB4 lengths 9/12 both reported `0x8565b`, DB5 lengths 9/12 both
reported `0x85693`; every errno was 6. These observations became assertions
before the final successful run.

`git status --short` exited 1 with `fatal: not a git repository (or any of the
parent directories): .git`. No Git diff/status verification is claimed.
