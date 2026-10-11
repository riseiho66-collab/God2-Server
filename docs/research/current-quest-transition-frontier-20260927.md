# Quest transition consumer frontier — 2026-09-27

## Result

**One additional native notification contract is qualified; no new original
acceptance, completion, branch, consumption, or reward rule was recovered.**

The current S2C `DB` consumer has an explicit MissionEnd sound notification:
subtype 1 selects sound key 603, whose pinned source row is
`603,MissionEnd.wav`. Subtype 2 selects a sound WORD from the packet. These
branches do not write the quest journal or inventory. They can accompany an
already-authorized outcome; playing this sound is not evidence that such an
outcome occurred, nor permission to grant rewards.

The current server already has strict `7A` dialogue projection and C2S85/86
codecs, owned journal restoration via DB4/5, bound knowledge conversations,
and the separately gated daily display route. Its `RecoveredQuestSync` covers
DB4/5, not the newly qualified sound-only DB1/2 branches. No runtime change is
required merely to manufacture a completion signal while the original
transition rules remain unknown. The parent was informed of the notification
layout and this limitation before this report was completed.

This lane did not repeat the concurrent full `004584A0` / 418-definition
parser work. It read the recent native-quest audits, owned journal/daily
integration reports, existing dialogue/close/instance evidence, current
reconstruction, and current server routes. No shared source, runtime, database,
client, desktop, or production state was changed.

## Pins and reproduction

| Input | SHA256 |
| --- | --- |
| Current God2.exe | `6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98` |
| Native mapped image | `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763` |
| Data2/Snd/commsnd.csvZ | `e5704115a5ec39cd97f9712dd5bfb1163e502671faaae65d7f45d9e541a11f0d` |
| Decoded sound source | `b34f206476b0b307fdbc153b1322c680698fc3bf41f29102a4aa1c1a8cc6dc5f` |
| Data2/Snd/MissionEnd.wav, 79,220 bytes | `29192eb5cae137878d2848e4e603aaffb834d437cb47a6de16bcdc122cb1f711` |

All addresses below are VAs, image base `00400000`. The sound source's
physical line 606 contains key 603; source ordinal is not inferred from the
filename. Exact row bytes/hash are in the receipt. RIFF/WAVE header and file
hash were checked without playback.

```powershell
$env:PYTHONPATH='artifacts/tooling/crypto-oracle-python'
python -m tools.strike_lab.current_quest_transition_frontier_20260927 --output artifacts/research/quest-transition-frontier-20260927/evidence.json
python -O -m tools.strike_lab.current_quest_transition_frontier_20260927 --output artifacts/research/quest-transition-frontier-20260927/optimized.json
```

The independent tool qualifies current PE spans against the mapped image and
uses explicit checks that survive optimized Python. It executes 63 complete
notification/default-branch cases, plus three exact-record fixture rejects.
Receipts retain native sound arguments, instruction counts, source pins,
direct-reference lists and disassembly. No game process is launched.

## Newly qualified DB notification

The actual current length-table entry `00401324 + 4*DB` points to
`00401246`, whose original execution returns **13 logical bytes**. The world
dispatch table selects `0046B44E`; `0046B464` passes logical+1 into
`004854F0`. This is the same fixed record family used by journal updates.

| Logical offset | Width | DB1 | DB2 |
| --- | --- | --- | --- |
| 0 | BYTE | DB | DB |
| 1 | BYTE | 1 | 2 |
| 2..8 | 7 bytes | Not read on this branch | Not read on this branch |
| 9..10 | WORD | Not read; always sound 603 | Raw little-endian sound key |
| 11..12 | 2 bytes | Not read | Not read |

Canonical zero-filled **notification examples**, without gameplay authority:

```
DB 01 00 00 00 00 00 00 00 00 00 00 00
DB 02 00 00 00 00 00 00 00 5B 02 00 00
```

Both select source sound 603. Native instructions:

- `00485516` pushes constant `025B`; `0048551B` calls `0044DB90` to obtain
  a sound slot. `00485536` calls `0044E320(slot,603,0,0,0,0,0)`.
- `00485543` reads WORD `[payload+8]`, i.e. logical+9. Calls at
  `0048554E` / `00485569` perform the corresponding slot lookup and play
  request. Only the low WORD of the sound argument is significant.
- `0044E320` constructs paths from `Data2/Snd` and the sound manager's
  25-byte-stride filename catalog when a real device is present.
- DB subtype 3 instead branches into role-effect consumers `0052E490` or
  `0052EF00`; it is not a hidden journal/reward update. Its rendering branch
  was statically inspected only and is not newly qualified here.

The oracle runs the complete original sound constructor `0044D9F0`, which
leaves device pointer zero and the sound-enabled flag one. It then runs
complete `004854F0 -> 0044DB90 -> 0044E320` through actual returns; every
reached game callee executes original instructions. Only imported
`timeGetTime` is adapted. With this explicit absent-device state, the play
routine takes its original no-device exit. This qualifies selection, packet
reads and state effects, **not audible playback, successful WAV loading, a
real sound device, or actual-client acceptance**.

Cases vary ignored bytes as 00/A5/FF, subtype 1 versus 2, source-backed sound
603, and adversarial sound words 0/1/669/1023/1024/32767/32768/65535. Additional
subtypes 0/6/255 take the actual default return. Every case checks the whole
2.25 MiB UI area, including nonzero journal and 50-slot inventory sentinels,
is unchanged; all native writes are confined to stack, SEH head, or sound
manager. The packet and original code also remain unchanged. It does not
claim resource preservation across unexecuted real-device callbacks.

The adversarial sound keys are **not** an emission whitelist. `0044DB90`
uses a signed short comparison; high-bit words can reach the negative-index
domain if used by later filename logic. A future server serializer should
restrict supplied keys to a verified nonempty source entry in the 0..1023
catalog domain. The fixed DB1 notification avoids a caller-selected key.

## Dialogue request frontier: already qualified, no new rule producer

The current bounded direct-call audit finds exactly these calls to the C2S85
producer `00497DC0`:

| Call VA | Consumer state | Meaning established |
| --- | --- | --- |
| 004C8447 | Close path, high-flag exactly 1 | Echo stored request/reply/context, then clear flag |
| 004C84B8 | Pending-reply flush helper | Same echo; no eligibility/reward calculation |
| 004C8589 | Confirm/select action | Stored reply, or mode-4 choice 0..7 |

`004C84A0` has one direct caller, `00496776`, inside the NPC37 producer.
This explains why another NPC interaction can first flush a pending85. It was
already executed in `current-knowledge-menu-text-lifecycle-20260926.md` and
`current-npc-interaction-20260921.md`; this lane does not rebrand it as a new
quest transition. The audit pins the exact caller set to detect future changes.

The input branch selects a reply using UI page/choice state. It does not join
Mission_data IDs with NPCMissionMessage keys or ACTMIS serials. A successful
confirm sets UI+AFF04 so close suppresses86. Mode4 with a high-flag reply can
produce two85 records; C2S86 retains source-lowWORD and pointer-derived upper
WORD. These established facts rule out treating each85/86 as a durable
acceptance/completion identifier.

Current `RecoveredWorldService` deliberately routes standalone85/86 only to
the bound quest callback. Current knowledge-menu issuance uses its qualified
reply configuration; the native double85 edge is not a newly demonstrated
failure of that configured route. General future conversations must preserve
the existing producer batching/opaque-tail evidence and authenticate issued
conversation state before permitting any mutation.

## Journal and ACTMIS field readers

The current bounded direct-call audit finds only two callers of the journal
slot writer `004C9670`: `00485665` and `004856A6`, respectively DB4 and DB5.
The writer stores a server-supplied DWORD, recomputes page count and optionally
refreshes UI. The journal list click handler `004C9260` reads a selected saved
DWORD, resolves lowWORD definition plus `max(highWORD-1,0)` description,
updates selected value UI+232EB8 and calls the text renderer. It has no packet
append, item debit, reward calculation or transition increment.

The literal-displacement audit retains all current references to UI+C2104 and
resource+B2C58/B2C5C. The latter are ACTMIS count/table fields. Their observed
roles remain initialization, destruction, native source parsing and the
category-20 requirement-text reader at `004B9F8D`. The category-20 serial is
an input instance WORD+8 supplied by the existing3B copy path; the display
consumer does not generate that serial or enforce inventory counts.

These are scoped direct-reference findings, not proof against computed or
indirect references elsewhere in the executable. No pointer/ID equality was
used to fabricate a join between the separate namespaces.

## Integration decision and exact remaining authority

The new notification can be serialized after an independently verified event;
it supplies no event predicate. No original quest is newly eligible for
activation from this audit. Before a playable original transition is claimed,
the server still needs:

1. An issued NPC/conversation binding to a specific quest namespace and valid
   response, rather than shared text-key or numeric-ID resemblance.
2. Original acceptance, branching, kill/collection event and repeat/reset
   conditions, with the corresponding journal value supplied by authority.
3. Source-backed item consumption/reward quantities and a durable transaction
   policy. ACTMIS text quantities alone are not such a transaction.
4. A current-client end-to-end outcome, including owned persistence and replay
   rejection. The MissionEnd filename or an audible notification does not
   substitute for that outcome.

No acceptance/complete/reward rule was added to the server or asserted as
recovered. This is an additional source-backed notification and a bounded
consumer/producer audit, with the remaining authority kept explicit.
