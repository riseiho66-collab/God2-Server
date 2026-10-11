# Current Stat Packet Return Path, 2026-09-20

## Result

**The newly executed pet2 outbound branch sends a three-byte control body,
not a 72-byte stat record.** Original `A5682 -> A57FF -> 132E0 -> A5807`
assembles and queues logical `D6 item_slot pet_slot option`, four bytes total.
It reads no bytes from the panel's three stored 72-byte records. New
authoritative monster attribute values recovered: **0**.

The neighboring direct caller also contains `A5736 -> 132E0`, sending B5 with
a four-byte body. Its explicit fields are described below; it is static-only
evidence, not a second emulated branch. Neither send is established as a
request whose response is S2C FB. No causal C2S/FB pairing is inferred from
their proximity in the UI code.

The earlier qualified FB path remains incoming:
`691B0 -> 858B0 -> A52A0`, 73 logical bytes including opcode, 72 body bytes
copied into pet2 storage. That test was **not rerun**. The original numeric
contents of FB, the sender's construction, and any wild-monster identity join
remain unknown to this lane.

The owner's screenshot claim about an offline/local-file implementation is
a useful source lead, not verified numeric evidence. This branch result does
not contradict or prove that implementation, and does not establish that the
whole client lacks local monster data.

## Authority and Provenance Classes

Current mapped image only:
`artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin`;
SHA256 `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
BASE=`400000`; all addresses below are hexadecimal RVAs and raw file offsets.
Byte counts are decimal. `P` is pet2 panel, `O=[P+DC]` world owner,
`Q=[O+86874]` outbound queue.

| Provenance class | Evidence and limit |
| --- | --- |
| Original local file/calculation producer | None newly established for monster capabilities. Existing NCP gamedata metadata lookup is not authority for FB numeric fields. This lane has no file name plus ID-to-original-stat values to report. |
| Previously received values in client storage | Existing FB body -> `P+48h*(slot-42)` at `A52F3`; numeric display reads at A40C0. Local availability after login alone does not distinguish this cache from file-derived values. |
| Client-produced outgoing control bytes | Native branch below creates option constants and selects slots. These are original protocol instructions, not intrinsic monster-stat producers. |
| Diagnostic inputs | All fixture panel/owner/inventory/stack/queue contents, including the example inventory entry and selected slot. The resulting queued bytes are not official observed traffic or original attributes. |

Prerequisites read: `current-monster-inspect-identity-20260920.md` and its
tool; known queue semantics from `current-protocol-coverage-20260919.md` and
`current_quest_action.py`. The new tool reuses sparse `NativeRun` and
`pinned_image` from `current_battle_entry.py`; it does not instantiate the FB
metadata loader, load graphics, or touch live networking.

## Bounded Static Direction Audit

The `A4000..A5400` pet2 window has no direct call to known queue append
`132E0`. `A40C0..A4DC3` uses the selected record for numeric/text display;
its final inline writes clear selection flags in other records at
`A4D69` (+2C high bit) and `A4DA3` (+C high3 bits). Those are local writes,
not evidence of an outbound 72-byte copy.

`A50F0` validates selected slot/key and existing record before opening the
panel; `A51E7 -> A40C0` refreshes it. `A52F5..A5394`, after the already-proved
FB copy, conditionally refreshes an inventory display through
`A5345 -> 9B850`, calls `A5350 -> AD080`, and refreshes pet2 through
`A538B -> A40C0`. It has no direct queue call. These downstream calls were
identified statically, not silently replaced or fully emulated.

Exact direct-call target searches located the relevant button caller
`A55F0..A59FB` via `A5664 -> A53C0`, a function beginning in the requested
window. The remainder of A53C0 and its A5510 helper show metadata/received
record fields feeding a tooltip, not a network buffer: metadata BYTE+11C,
+11E,+120 are compared to record BYTE+3; metadata BYTE+11D,+11F,+121 or
record BYTE+22/+23 pass to A5510, which resolves a two-byte table entry and
calls `B5BE0`. No HP/attack/defense names are assigned to these bytes here.

Other concrete direct callers reviewed locally include `9ABC1/9AC0B`,
`ABE6C`, and `A5CAA`. The latter is in `A5A40`, which updates the same record
from its input pointer, e.g. WORD input+0 -> record+10/+12/+14/+16 at
`A5C3E/A5C47/A5C50/A5C57`. This is another input-to-record edge, not a
file-stat producer; its complete upstream dispatch was not audited here.
No all-opcode/name/file inventory was performed.

### Direct Outbound Builders

| Caller/queue call | Exact payload source | Direction evidence |
| --- | --- | --- |
| `A56E9..A5736 -> 132E0` | Body+0=`2C` at `A570E`; body+1=0 at `A5725`; body+2 WORD from O+85A30, read `A5713`, stored `A5720`; length4 at `A571E`, opcode B5 at `A5731` | Q is loaded from O+86874 at `A572A`; no 72-byte record pointer passed. Meaning of O+85A30 is left opaque. Static only. |
| `A5741..A57FF -> 132E0` | Find active inventory key4010; match index at `A5770`; P+D8 at `A5774/577F`; option4 at `A577A` | Length3 at `A5783`; shares D6 queue call. Executed for control17. |
| `A578B..A57FF -> 132E0` | Find active inventory key400F; match index at `A57BA`; P+D8 at `A57BE/57C8`; control18/19/1A chooses option1/2/3 at `A57CE/A57DB/A57E8` | Length3 at `A57ED`; Q loaded `A57F4`, opcode D6 at `A57FA`. Executed. |

For the latter two branches, the inventory scan examines 30 records of stride
18h at O+8560C. BYTE record+0 must be signed-positive; DWORD record+4 low16
must equal the fixed key. Only the matched loop index is sent. It does not
send the matched item's numeric attributes, its whole record, or pet stats.

The native dispatch at `A5682` consumes caller event flags: mask02 exits via
the close branch; mask20 enters the control table `A59FC`. Control17 selects
A5741; controls18..1A select A578B. These are raw native control numbers,
not newly recovered user-facing command names. The fixture enters after the
excluded tooltip/UI portion of A55F0; it is not a full UI interaction test.

## New Original Execution

The new slice runs continuously from **A5682 through the native queue and
the real `A5807 RET 8`**, to an external return sentinel. No game function
return is supplied, no image instruction is patched, and no network send is
performed. The known queue is the destination, not a fake game callback.

Example, explicitly diagnostic: matched inventory slot7, selected pet slot43,
control18, event flags20 -> `D6 07 2B 01`, **120 instruction visits**.

| Native access | Exact provenance |
| --- | --- |
| `A578B` | P+DC -> O |
| `A5799` | Inventory entry BYTE+0 eligibility |
| `A579F/A57A1/A57A7` | Entry DWORD+4, mask low16, compare400F |
| `A57BA` | Matched loop index -> body+0 at post-prefix ESP+14 |
| `A57BE/A57C8` | P+D8 selected slot -> body+1 |
| `A57CE/A57DB/A57E8` | Immediate1/2/3 -> body+2 |
| `A57F4` | O+86874 -> queue owner Q |
| `A57FF -> 132E0` | Pass opcode D6, stack buffer pointer, length3 |
| `13320` | Write opcode at Q+36C8+old_count |
| `13340` | Three native byte copies from the exact stack buffer to queue |
| `1334C` | Q+36C4 count +=4; real queue RET C at13365 executes |

JSON retains each original memory access's RVA, absolute address, region,
relative offset, size and bytes, all instruction visits, the queue-call
arguments, pinned span hashes, and explicit input classes. Only queue and
stack writes are permitted. The full image and P+0..D7 records are checked
unchanged after each probe. Poison A5/3C/FF changes the entire numeric record
area without changing output; the **only panel reads are +DC and +D8**.

### Guards and Not-Found Behavior

- With the inventory source page deliberately unmapped, the native read
  stops at **A5799**, before any queue call or mutation. No empty or invented
  inventory record is supplied. This is an oracle guard, not a game sanitizer.
- With a present but nonmatching inventory, native control still reaches the
  queue. The source byte at ESP+14 is never rewritten by A57BA, so body+0
  retains the event argument's low byte: flags20 produce `D6 20 2B 01`;
  flags60 produce `D6 60 2B 01`. This is existing stack provenance, not a
  discovered slot, missing-stat fallback, or zero default.
- Full queue stops before `13370` transport flush. A nonzero lock pointer
  stops before `11970`. No lock or socket helper executes. Existing queued
  bytes are retained in the tested nonempty-queue append case.

## Remaining Exact Boundaries

This proves one concrete **short-control outbound** source chain. It does
not prove an inspect request/reply contract or globally exclude other senders.
No local-stat-to-outbound-stats slice can be offered from the present evidence.

Unexpanded calls that bound this result:

- A50F0's UI coordination: `A5177 -> 9C190`, `A5182 -> E7B20`,
  `A518D -> FDD00`, `A5198 -> 6F3D0`, `A51A3 -> D8610`,
  `A51AE -> C9200`, `A51B9 -> A2AE0`, `A51C0 -> 8B920`,
  `A51C7 -> 90DE0`, `A51E0 -> 107B20`. No transitive-network absence claim.
- Post-FB `A5345 -> 9B850` and `A5350 -> AD080`, plus A40C0's display/table
  helpers: not a newly executed outbound flow in this lane.
- Other A55F0 controls: `A56D3 -> F1E50`, `A56DE -> F1890`; record-consuming
  `A586B -> BC350`, `A589A -> BC730`, `A58C9 -> BC910`; scalar subsets at
  `A5929/A5989/A59E4 -> BCB00`. Only short prefixes of those four BC helpers
  were inspected. They begin formatting/display work (including received
  record WORDs+30/+32/+34/+36 at BC424..BC450); their complete subtrees and
  subsequent event handlers are not excluded by the D6 result.
- Exact original FB/E3/3B sender or any local replacement of it remains
  unestablished. A local copy of a prior S2C body is not an intrinsic producer.
  A genuine offline stat claim still needs its local file/calculation read,
  native monster identity mapping, and the actual resulting capability bytes.

## Verification and Stop

```powershell
python -B -m unittest tests.research.test_current_stat_packet_return_path -v
python -B -m tools.strike_lab.current_stat_packet_return_path
```

**4/4 focused tests passed in 0.154 seconds; CLI JSON parsed successfully.**
Tests cover all three pet slots, four raw controls, record poison, exact native
queue writes, missing source, native no-match behavior, nonempty/full queues,
lock boundary, image integrity and narrow input guards. No FB copy/metadata
suite was rerun. Instruction budget is2000; the source-backed code runs only
with explicitly diagnostic state, never claimed as original official values.

Only the matching new tool, test and this document were added for this task.
No shared helper, CMake, production code, DB or other system was changed.
No UI/network operation, old capture/archive, graphics preload or child worker
was used. All test/CLI processes exited; no active process remains.
