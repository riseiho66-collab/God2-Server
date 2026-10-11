# Current Quest Close Continuation

## Result and authority

The previously unresolved **C8350** continuation now executes through its real
cleanup callees and returns in an explicit empty-UI fixture. The connected
**C8500 -> 97DC0 -> 132E0 -> C8350** action also returns. No game callee is
replaced with a successful return. This qualifies client request production and
queue ordering, not authoritative quest transitions.

**85 followed by 86 is not required before transport flush.** A successful
action writes `UI.AFF04=1`, suppressing the close branch's 86. The real pending
queue gate `133F0` reaches flush entry `13370` with that 85 alone. Execution stops
before 13370. Neither request production nor reaching this boundary proves a
send, server acceptance, or rewards.

Only current pinned native bytes supply instruction/data authority:

`artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin`

SHA256 `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.

The new `NativeClose` inherits `current_quest_action.NativeAction`: image hash
qualification, original image mapping/protection, decoded 7A ingest, register
and memory helpers, instruction bound, and real 132E0 producer observation.
Image base is `400000`; file offsets equal RVAs. Addresses below are hexadecimal
RVAs unless identified as object offsets. Opcodes 85/86 are hexadecimal.
No retired source content or external material was used, and no descendants
were created. Only the three newly assigned files are owned by this lane.

## Executed sequences

Example fixture: request word `1234`, context byte `9A`, source dword `DEADBEEF`,
this pointer `10000000`, initial AFF00=1/AFF04=0, final page, stack poison A5.
All rows execute original native callees and return to the caller sentinel.

| Entry and state | Appended logical bytes | Ordering |
| --- | --- | --- |
| C8500, mode 1, inbound reply 8002 | `85 34 12 02 00 9a a5` | 85 only |
| C8350, inbound reply 0002 | `86 ef be 00 10` | 86 only |
| C8350, inbound reply 8002 | `86 ef be 00 10 85 34 12 02 00 9a 84` | 86 then 85 |
| C8500, mode 4, choice 3, inbound reply 8002 | `85 34 12 03 00 9a a5 85 34 12 02 00 9a 84` | choice 85 then stored-reply 85 |

Mode 1 ingest is linked to the existing synthetic NPCMissionMessage fixture.
Mode 4 is explicitly staged post-render state; mode-4 inbound/page construction
is not qualified. In each row a subsequent explicit call to original 133F0,
with transport byte `QUEUE.2CB8=1`, stops at 13370 without modifying the queue.
This is a flush-gate probe, not proof of the application's flush scheduling.

## Close state and exact producer bytes

| RVA / exact instruction bytes | Proven behavior |
| --- | --- |
| C8350 `51 56 8bf1` | Saves ECX (this pointer), saves ESI, moves this into ESI. |
| C8354 `6683beee2d230000` | Signed widget word UI.232DEE < 0 returns immediately; no close state changes or requests. |
| C8362 `8b8600ff0a00`, C836A `7445` | AFF00=0 skips the 86 block, but still runs cleanup and the later high-flag branch. |
| C836C `8b8604ff0a00`, C8374 `7531` | Nonzero AFF04 suppresses 86. AFF00 is subsequently cleared. |
| C8376 `8b868c680800`, C8383 `8b08` | Loads pointer at UI.8688C, then reads a dword at that pointer. Its meaning is opaque. |
| C8380 `6a04`, C838B `6886000000` | Producer passes payload length 4 and opcode 86. |
| C8385 `8b44240c`, C8389 `33c8`, C8390 `81e1ffff0000`, C8396 `33c1` | Merge low 16 source bits into saved ECX while preserving its upper 16 bits. |
| C839E `89442410`, C83A2 `e839aff4ff` | Writes the merged stack dword, then calls real 132E0 queue writer. |
| C83A7 `c78600ff0a0000000000` | Clears AFF00 after successful producer return, or after suppressing 86 because AFF04 is nonzero. |
| C842B `a1ec7b5b00`, C8431 `83f801` | After cleanup, only global dword 1B7BEC exactly equal to 1 requests the follow-up 85. Nonzero values 2/FFFFFFFF do not. |
| C8436 `668b15f87b5b00`, C843D `66a1fa7b5b00` | Uses stored reply and request words; this branch has no page, mode, choice, or signed-reply gate. |
| C8447 `e874f9fcff`, C844C `c705ec7b5b0000000000` | Calls 97DC0; clears the high flag only after it returns. |

Thus 86 is emitted exactly when the close widget is nonnegative, AFF00 is
nonzero, and AFF04 is zero. Its logical record is **five bytes**:

| Logical offset | Width | Native origin |
| --- | --- | --- |
| 0 | 1 | Opcode 86 |
| 1 | 2 | Low word of dword `*[UI.8688C]`, little endian |
| 3 | 2 | High word of saved this pointer, little endian |

The four-byte payload is `(this & FFFF0000) | (source_dword & 0000FFFF)`.
The source read is four bytes even though only its low word survives. Varying
source high bits and poison 00/55/A5/FF leaves the pointer-derived payload high
word unchanged. In this fixture it is `00 10`, not zero padding and not an
established game field. Every payload byte is written by C839E; C8350 supplied
the saved pointer. Tests observe both writes. No actual client allocation
address or semantic identifier is inferred from the synthetic pointer.

## 85 action and close ordering

The existing 85 layout is retained: opcode + little-endian request word +
little-endian reply/choice word + context byte + one producer-uninitialized
byte. Total logical size is seven bytes; payload size is six.

- C8500 allows a final page (`page == page_count-1`, 32-bit wrap), or mode 4
  with signed page >= signed 16-bit threshold. Negative signed stored reply
  takes close without the first 85. Mode-4 choices must be signed values 0..7;
  invalid choices stop at native error entry 75D60, argument 026E.
- Non-mode-4 action clears the high flag before 97DC0. After 97DC0 returns,
  C858E sets AFF04=1, then C859A calls C8350. Consequently close emits neither
  86 nor the high-flag follow-up 85 in that successful sequence.
- Mode-4 action sends the choice, preserving the flag. C858E still sets
  AFF04=1, suppressing 86. Cleanup resets the choice to -1. If the flag is 1,
  close then sends the stored normalized reply, not the choice. This produces
  two 85 records; no deduplication or server meaning is established.
- Inbound FFFF remains FFFF with flag 0. With AFF00=1/AFF04=0, C8500 takes
  close without its own 85 and close emits 86. A negative widget at C8350
  bypasses all close work. C8500 itself does not apply that widget gate.

For a fresh poisoned action stack the first 85 tail is the chosen poison, with
no native writer before the copy. For the close-generated 85, the tail is
**84** in the completed fixture: C8426 calls 834E0, pushing return address
`004C842B`; payload+5 later overlaps byte 1 of that stack dword. At the 97DC0
entry it is `ESP-3`. The producer writes payload+0..4 but leaves +5 alone.
Tests capture the last writer at the producer call, before later stack reuse.
The 84 is a concrete call-stack residue, not a protocol constant or padding
rule. The lane exposes observed bytes and their provenance, not a canonical
encoder that invents the tail.

The real input handler C85B0 is also executed. With an open widget, event flag
02 takes close before flag 01 action dispatch. Control 0/flag 01 calls C8500;
control 1/flag 01 calls close; controls 2/3 stop at previous/next page entries
C8720/C8750. Mode-1 action and close events return with ESP advanced by 12.
Mode-4 input can reach further selection processing **after** these requests;
the trace stops at 10D8A0. The fully returned mode-4 result above is the C8500
call, not a claim that the whole mode-4 input handler is qualified.

## Real cleanup and fixture scope

The original cleanup sequence is C8700 -> C7ED0 -> 107BB0 -> optional 1B560 ->
1073E0 (control 4) -> 1073E0 (control 5) -> 834E0 -> high-flag test.

The synthetic post-render fixture makes these branches executable:

- NativeAction's UI mapping is zero-filled, with widget index 0 (also tested
  index 1). Corresponding widget flags at UI.E2988 are zero. The native widget
  routines execute their own empty-state exits; the widget index stays 0.
- The list at UI.CC9D4 has zero columns and zero entries, including the entry
  inspected for index -1. C8700 writes choice FFFF and executes 10D310.
- List backing pointer UI.CC9D8 targets a new read-only synthetic page at
  60000000. Slot 0's resource word at backing+1E is FFFF. C7ED0 calls 10CC60
  five times with the pinned native empty string. Each call executes native
  146CF7/14CF08 empty formatting and 1E500/1E440, whose `resource >= 1388`
  branches return. No formatter or resource setter return is replaced.
- 10DBE0 runs its original 50-iteration zero-column loop and resets selection
  word list+224 to FFFF. Pinned image dword 193E68 is FFFFFFFF, so C83DA's
  unsigned low-word test skips optional selected-graphic cleanup.
- UI.232EC8 is staged to 1. 834E0 writes UI.232F38/UI.232F36=1; original
  1A950 sees the cursor state already equal to 1 and returns naturally.
- Source dword lives at 60000800 in the same read-only page. Request/reply and
  context came from NativeAction's actual mode-1 7A header ingest, which stopped
  at C8234 before excluded rendering. Page/choice/close state is then staged.

These are connected evidence slices, not uninterrupted application execution.
Each run inherits the 20,000-instruction bound. Code stays pinned and executable
but non-writable; only the parent's two data pages are writable and
non-executable. Resource/table/input/backing bytes remain unchanged. No imports,
instructions, or game callees are patched; no client, socket, or UI is launched.

The parent continuation test additionally invokes inherited NativeAction.action,
stops at C8350 with original return address C859F on the live stack, and resumes
that stack without restaging registers or queue. It returns to the original
sentinel with one 85 queued and no 86.

## Queue and partial progress

132E0 appends opcode plus payload to QUEUE.36C8, and adds their total byte size
to QUEUE.36C4. It checks capacity before lock acquisition. Exact-fit capacity
`A00` is accepted. These fixtures bound initial counts to 0..A00; they do not
qualify corrupt counts or signed-overflow behavior.

| Condition | Stop / established progress |
| --- | --- |
| 86 needs five bytes, remaining capacity <5 | 13370 before any append; AFF00 and high flag remain set. |
| Non-mode-4 initial 85 needs seven bytes, remaining <7 | 13370 before append; high flag already cleared, AFF04 not yet set, AFF00 still set. |
| Nonnull lock pointer | 11970 before append; no invented successful lock. |
| 86 then 85, initial count A00-11 | First five bytes append; second producer reaches 13370. AFF00=0, high flag=1. |
| Mode-4 85 then 85, initial count A00-13 | First seven bytes append; second reaches 13370. AFF00=0, AFF04=1, high flag=1. |
| Explicit 133F0, active transport byte, positive queue count | Reaches 13370 regardless of request opcode; no flush instructions execute. |
| Explicit 133F0, inactive transport byte or empty queue | Returns without flushing. |

Producer observation at 132E0 is not evidence of a completed append. Capacity
can force the flush boundary between the two producers, so their pair is not
proven atomic or one transport frame. Tests preserve existing queue bytes and
the eight-byte trailing canary, and verify the native 86 writes are one opcode
byte, one payload dword, and the count dword. Repeated close after successful
86/85 cleanup emits no new requests because AFF00 and the high flag are clear;
this does not establish a general server deduplication rule.

## Formal router handoff and uncertainty

Use the request contract above at the decoded logical-record layer. A later
router can retain the complete six-byte 85 payload and four-byte 86 payload,
separately exposing their observed fields and raw residue bytes. Do not require
85 followed by 86; the qualified sequences include 85 alone, 86 alone, 86/85,
and 85/85. This is not an exhaustive server-valid sequence grammar. Do not
reject 85 tail bytes other than A5/84 or require 86's high word to be 1000.
Those values follow this experiment's state and call stack.

Still unresolved:

- Original server dispatch and validation for either opcode; request/context/
  source meanings, actual 7A construction, and transport framing or flush/send
  success. Logical sizes are producer evidence, not recovered server policy.
- Actual page, text, list, resource, widget, cursor, and source-object setup.
  Empty fixture cleanup proves a bounded path, not populated UI cleanup.
- Explicit populated-state stops: 10D362 (selection entry), 10DBF0 (columns),
  107BED (active widget), 26700/26550 (resource setters), 1B560 (selected graphic),
  1A961 (cursor change), and 2C70 (assertion). Perturbation tests reach selection,
  columns, widget, text resource, cursor and assertion boundaries after 86,
  before follow-up 85. 26550 and 1B560 are declared unexecuted alternate limits.
- C8720/C8750 page navigation, mode-4 event continuation 10D8A0, 75D60 error
  handling, 11970/11990 lock/unlock, and 13370 transport flush. None is given a
  replacement result or resumed past its boundary.
- ACTMIS ownership, quest acceptance/completion, prerequisites, inventory
  consumption, rewards and persistence. No inferred relation or authoritative
  gameplay transition is supplied. No live playable proof.

## Reproduction and validation

From `C:/Users/risei/Desktop/God2/God2-Server`:

```powershell
python -B tests/research/test_current_quest_close.py -v
python -B tests/research/test_current_quest_action.py -v
$env:PYTHONPATH = "$PWD/artifacts/tooling/crypto-oracle-python"
python -B -m tools.strike_lab.current_quest_close
python -B -m tools.strike_lab.current_quest_close --json
```

The tests insert the existing Unicorn dependency directory. Both CLI forms
write stdout only. Full JSON adds instruction traces, native memory events,
state checkpoints, producer arguments and last-writer provenance. No generated
artifact or shared file is required.

Validation on 2026-09-19: 20 close tests pass, covering branch matrices, exact
bytes, opaque fields, stack provenance, canaries, capacity, locks, partial
sequences, actual event dispatch, parent live-stack continuation, populated
boundaries, and unchanged source/input/resource/code. The 15 existing action
tests also pass. Both report modes are exercised.

Owned new files only: `tools/strike_lab/current_quest_close.py`,
`tests/research/test_current_quest_close.py`, and this document. Session and the
85/25/movement typed world-parser lane remain outside this lane's changes.
