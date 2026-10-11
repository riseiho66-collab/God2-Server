# Current NPC Mission Dialogue Request

## Result and authority

A current native request producer is now executable beyond ACTMIS display and
incoming 3B storage: decoded opcode **7A**, mode 1, supplies NPC mission dialogue
state; the action path **C85B0 -> C8500 -> 97DC0 -> 132E0** constructs and queues
logical opcode **85** with six payload bytes. These are hexadecimal opcodes.
This is a bounded request contract, **not a recovered quest acceptance,
completion, turn-in, prerequisite, consumption, or reward rule**.

Only the pinned current image supplies instruction/data authority:

`artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin`

SHA256 `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
Image base is `0x400000`; file offsets equal RVAs. All instruction locations
below are RVAs. Object offsets are relative to the named synthetic object.
No retired archive was opened, searched, or used as a lead. Historical sections
of existing documents are excluded from evidence. No actual mission text or
catalog ID is inferred from the synthetic pointer table.

## Evidence chain

The existing current quest instance and requirements helpers were inspected
first. Their established 3B-to-ACTMIS path is not repeated. Direct references
to resource `B2C58/B2C5C` in this image led to initialization, cleanup, loading,
and the known requirement-text consumer, not an additional eligibility check.
This limited reference search does not prove that no indirect consumer exists.
The action trace instead follows native NPC mission dialogue code.

| RVA | Current native evidence |
| --- | --- |
| `56308`, `56349` | `be08a15800`, `e842170000`: compares section name `NPCMissionMessage` at `18A108`, then calls loader `57A90`. |
| `57AF1` | `89854c2c0b00`: loader stores the table pointer at resource `B2C4C`; `57BF0` stores its word count at `B2C48`. |
| `6B5D4+4*7A` | Dispatch table points to `6ABD7`. |
| `6ABD7..6ABE9` | Reads logical word +9, saves it at image `1B5DC0`, advances record pointer by one, calls `C7F10`. |
| `C7F1E..C7F25` | Signed UI word `232DEE < 0` returns without entering the dialogue setup. |
| `C7F48..C7F5A` | Payload byte +3 -> UI byte `CCD36`; payload byte +2 -> UI word `CCC1C`. |
| `C8086..C812C` | Mode 1 follows the `NPCMissionMessage` count/table at resource `B2C48/B2C4C`. Mode 0, 4 and 5 have other branches and are excluded from inbound execution. |
| `C80B5` | Reads the text pointer at table + `4*(payload.u16[6]-1)`. Fixture uses key 1 and the original empty string at `1B4640`. |
| `C80DC -> C8700 -> 10D310` | Original selection reset executes with synthetic null list entries. No function is replaced. |
| `C80ED..C8104` | With payload byte +10 equal to zero, passes text pointer, payload word +4, and payload word +8 to `C81F0`. |
| `C8201`, `C8208` | Stores request word at image `1B7BFA` and reply word at `1B7BF8`. |
| `C820E..C822E` | Clears image dword `1B7BEC`; unless reply is FFFF, high bit set means flag=1 and reply is masked by 7FFF. FFFF stays FFFF with flag=0. |
| `C85B0..C85EA` | Input event requires nonnegative signed widget word; flag mask 01 and control word 0 call `C8500`. Flag mask 02 takes the close path first. Control values 1/2/3 route to close/previous/next paths. |
| `C8500..C852B` | Allows action on `page == page_count-1`; otherwise requires mode word 4 and signed `page >= sign_extend(UI.CCD32)`. |
| `C852D..C855B` | Negative signed reply word takes close path without constructing 85. Mode 4 uses signed choice word `UI.CCC20`, accepting only 0..7. |
| `C855D..C856D` | Invalid choice calls original error function `75D60` with argument 026E; execution stops at that function entry. No error-string meaning is assigned. |
| `C8574..C8589` | Other modes pass the stored reply word and request word to `97DC0`, first clearing `1B7BEC`. Mode 4 preserves that flag here. |
| `97DC0..97DF3` | Original producer writes two words and UI byte `CCD36` into a stack payload, then calls `132E0` with opcode 85 and length 6. |
| `13320`, `13338`, `13340`, `1334C` | Original queue writer stores opcode, copies one dword plus two bytes, and increments byte count by 7. |
| `C858E` | Writes UI dword `AFF04 = 1` after the producer returns, then calls `C8350`. This state is not quest completion. |

## Exact fields and units

Input to the experiment is a decoded logical record. Its first byte is 7A.
The following offsets are **logical-record byte offsets**, not payload offsets:

| Input offset | Width | Proven use in the tested mode-1 path |
| --- | --- | --- |
| 1 | 2 | Not read in this path; fixture value 27 is not a framing rule. |
| 3 | 1 | Mode 1, widened into UI word `CCC1C`. |
| 4 | 1 | Opaque context byte, copied to UI `CCD36` and echoed in 85. |
| 5 | 2 | Opaque request word, little endian; preserved without sign filtering. |
| 7 | 2 | One-based NPCMissionMessage text-table key; fixture 1 only. |
| 9 | 2 | Reply word, normalized as described above. |
| 11 | 1 | Zero selects the non-formatting text path. |
| 12..26 | 15 | Unread in the tested branch. |

The native incoming length-table entry for 7A points to `1318`, whose exact
bytes `b8feffffffc3` return -2. This is a sentinel, **not a fixed 27-byte
length**. The outer variable-length framing logic is outside this experiment.

Outgoing logical bytes are:

| Offset | Width | Proven origin |
| --- | --- | --- |
| 0 | 1 | 85 |
| 1 | 2 | Stored request word, little endian |
| 3 | 2 | Normalized reply word, or mode-4 choice 0..7, little endian |
| 5 | 1 | Stored context byte |
| 6 | 1 | **Preexisting stack byte, never initialized by this producer** |

The last byte is not a recovered field, zero padding, quantity, or default.
At entry to `97DC0` it resides at `ESP-3`; after allocating eight bytes it is
payload+5. Poison probes 00/55/A5/FF survive unchanged into the queue. Memory
hooks verify that no executed action instruction wrote that address before
the copy. Therefore this lane does not expose a canonical encoder that fills
it with an invented value.

Page and page-count values are 32-bit integers; `page_count-1` wraps at 32 bits.
The threshold and choice are signed 16-bit values. They are UI page/choice
indices, not quest steps or completion counts. Page/choice state is staged
explicitly after the excluded rendering boundary. Only mode 1 is linked to
the inbound NPCMissionMessage fixture; mode-4 tests qualify the actual action
branch with synthetic mode-4 state, not the full mode-4 incoming/text flow.

The queue count and capacity are **bytes**. With no lock object, the native
writer appends when `existing_count + 7 <= 0xA00`. The equality boundary is
executed. Larger counts stop at original flush entry `13370`; nonnull lock
state stops at original lock entry `11970`. Neither is stubbed. A recorded
producer call at either stop is not a successful queue append or network send.

## Execution and integration boundary

1. Enter decoded dispatch at `68B4E` with synthetic outer/UI registers. Execute
   original code through NPCMissionMessage lookup and header normalization.
   Stop at `C8234` before UI setup/rendering. Resource pointer/count, widget,
   list entries and table are synthetic; text pointer targets native empty text.
2. Preserve the resulting request/reply/context globals. Explicitly provide
   page/count/mode/threshold/choice state and a poisoned stack for action.
   Execute `C8500` through the real request producer and queue append. Separate
   input-handler tests execute `C85B0` and its actual dispatch into `C8500`.
3. Stop at `C8350` before close handling, `75D60` before error handling, or
   declared lock/flush boundaries. A gated no-op returns to the sentinel with
   a balanced stack. UI state AFF04 is set only after a successful producer
   return within the unlocked/no-flush fixture.

These are connected provenance slices, not uninterrupted application execution.
There are no native replacements, import stubs, patched instructions, sockets,
UI automation, client launch, or descendant agents. Each slice is bounded to
20,000 instructions and must reach a declared endpoint. The image is read and
execute only except two native global-data pages, which are read/write and
non-executable. Resource/table/input are read-only during execution. Tests
verify unchanged code/resource/input and exact queue writes with canaries.

For later C++/Lua work, expose the opaque request word, reply-or-choice word,
context byte and observed sixth byte as separate evidence fields. Retain the
raw input reply word separately from its normalized client state. Keep the
UI predicates separate from server quest eligibility. Do not install a quest
transition, reward, packet-padding default, or ACTMIS/Mission_data join from
this result. No C++/Lua runtime integration is changed in this lane.

## Reproduction

From `C:/Users/risei/Desktop/God2/God2-Server`:

```powershell
python -B tests/research/test_current_quest_action.py -v
$env:PYTHONPATH = "$PWD/artifacts/tooling/crypto-oracle-python"
python -B -m tools.strike_lab.current_quest_action
python -B -m tools.strike_lab.current_quest_action --json
```

The test runner adds the existing Unicorn dependency directory itself. Both
CLI modes emit stdout only. JSON includes exact fixture bytes, native stop
RVAs, send-call arguments, queue bytes, state, and memory-access traces.
For request=1234, reply=8002, context=9A, mode=1, final page, stack poison=A5,
the native queue contains **`85 34 12 02 00 9a a5`**.

Validation on 2026-09-19: 15 tests pass. Coverage includes current image pins
and section/dispatch anchors, native incoming word normalization, FFFF,
signed/wrapped page boundaries, mode-4 threshold and all eight choices,
negative/out-of-range choices, uninitialized tail provenance, queue capacity
and lock stops, existing-byte/canary preservation, real input-event dispatch,
closed widget, null text-table entry, and unchanged code/resources/input.
Prefixes 1..11 fault on unmapped reads; prefixes 12..27 reach header setup
because the suffix is unread. Prefix 11 already writes context before faulting.
This is not an atomic or complete packet validator.

## Original rules still OPEN, with next native locations

- Original server construction of 7A request/reply/context fields remains
  unresolved. `6ABD7 -> C7F10` is the exact current client input boundary;
  `97DC0` establishes what is returned. These fields are not proven NPC IDs,
  quest IDs, acceptance codes, or completion codes.
- Original server dispatch/validation of C2S 85 remains unresolved. No original
  server executable/handler address is established by the pinned client image.
  The precise handoff is opcode 85 plus the six-byte layout above. Do not infer
  authoritative behavior from this request, or from a reconstructed server.
- Normal text-to-page/choice production remains outside executed coverage.
  It was actively traced to `C8780 -> FFDF0/FFDE0/FFD90`; `C87B4` writes page
  count, `C87DD..C8800` writes mode-4 threshold/bias, and `C8671..C86A0`
  computes/stores choice before `C86C1` calls the recovered action. Those are
  concrete next execution locations, not verified progression rules.
- Close continuation starts at `C8350`; it can construct opcode 86 or later
  call `97DC0` depending on other state. That continuation is excluded, so
  this lane does not claim a complete dialogue exchange or absence of another
  request. Transport flush starts at `13370`; no live acceptance is proven.
- ACTMIS serial selection, owned-quantity validation/consumption, prerequisites,
  quest acceptance/completion, rewards and persistence remain unresolved
  original rules. The earlier `98DD0` incoming instance writer and `B9F9A`
  ACTMIS serial reader still do not supply those rules. This request trace
  does not create a relationship to them or close their evidence gap.

Changed files are exclusively the new `tools/strike_lab/current_quest_action.py`,
`tests/research/test_current_quest_action.py`, and this document. Existing
helpers, shared runtime, Session, CMake and all other owned lanes are untouched.
Emulator evidence is not live playable proof; unresolved gameplay is not done.
