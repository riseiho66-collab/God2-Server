# Current Monster Drop Rules, Lane E, 2026-09-20

## Delivery and Scope

This lane owns exactly three new files:

- `tools/strike_lab/current_monster_drop_rules.py`
- `tests/research/test_current_monster_drop_rules.py`
- `docs/research/current-monster-drop-rules-20260920.md`

New evidence establishes a bounded native item-definition producer, battle-result
item-slot consumer/state producer, and subsequent item-name consumer. It does
not establish a monster award producer. In particular, the item branch can
describe equipment lost by the player. Treating it as an original monster drop
table would reverse the meaning of an established branch.

The machine-readable report retains all 7,815 occurrence keys from
`current_monster_inventory.pinned_catalog()`: 7,791 visible occurrences in 96
groups and 24 superseded occurrences, across 97 source group declarations.
These are occurrence counts, not a unique-species or ALL-boss denominator.
Normal, boss, elite, event, quest and summoned coverage remains requested;
classification and variant identity remain `null` for every occurrence.

No retired source or old drop audit is used. No database, runtime registration,
shared file, network, live process, desktop UI, or child agent is involved.
The native UI routines below execute only inside offline Unicorn memory.
EXP display code is deliberately stopped before its first load at `0x118c6f`.

## Exact Sources

All offsets below are byte offsets; native-image offsets equal RVAs at base
`0x400000`. The complete report includes raw bytes and SHA-256 for every listed
native span, as well as full source identity and per-occurrence row provenance.

| Source | SHA-256 |
| --- | --- |
| `artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin` | `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763` |
| Current client `Data2/Patch/Comm/gamedata.csvZ` | `70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731` |
| Decoded gamedata | `75c3c37947a64b0917fbf8e546884d9bf893fe6a606d3e2b8f3b1857966b1815` |
| Current client `Data2/Patch/Comm/message.csvZ` | `5cd34cce66feae96d947cd45e32984765ce625673c0fb19c73cb63d7d9178598` |
| Decoded message | `370bd6ed9b4892f57190fc7a8dab14061b3e844b0aa9d0171611a9cbab61b5f8` |

The current client root is `C:/Users/risei/Desktop/God2/God2`; the research root
is `C:/Users/risei/Desktop/God2/God2-Server`. Hash or size mismatches fail closed.
The existing `NativeItemMetadata` helper reads only the pinned image and
gamedata on this path. It executes the original tokenizer, row conversion,
RomMaps lookup and index store. Its sole CRT decimal adapter is inherited;
the new result/name consumer replaces no game call and patches no instruction.

## New Native Proof

The existing static receive chain is checked against the current image:
receive opcode `0x89` map byte at `0x119a8d` selects index 24 and handler
`0x1195cc`; queue map byte at `0x1146c9` selects index 8 and `0x114582`.
The call at `0x11459a` targets consumer `0x118bf0`. Size table entry `0x1548`
targets `0x1240`, whose original immediate return is 57. Transport framing and
the receive queue are not executed by this lane.

For a concrete source-to-consumer test, the existing native item loader reads
the exact current `MIS:4660` row, physical line 7636, decoded offset 545749
(`0x853d5` in gamedata, not in the executable). The row including CRLF hashes to
`1d5844ff1c5ce9643326308f39c3ae618bdf89649370fab66ca4ff047429238e`.
This is an item-definition probe, not a claim that any monster drops item 4660.

| Step | Original RVAs | Observed result |
| --- | --- | --- |
| Item record production and publication | `0x59420`, `0x59a20` | Parsed record is published under numeric item key 4660. |
| Item lookup | `0x59a60` | Low WORD indexes owner `+0xb2d40`, only below unsigned `0x7f58`. |
| Result entry loop | `0x118c13` through `0x118c3d` | Four entries at logical offsets 17, 25, 33, 41, stride 8. |
| Entry gate | `0x118c16` through `0x118c1a` | Signed DWORD must be strictly positive. |
| Result slot call | `0x118c21` -> `0x853d0` | Passes entry DWORD and zero-based slot index. |
| Item resource resolution | `0x8541b` -> `0x9b720` -> `0x59a60` | Consumes low WORD item key; returns record WORDs `+0x116/+0x118`. |
| Control setter | `0x8543b` -> `0x1068c0` | Native disabled-handle branch returns normally; no renderer substitution. |
| Slot state production | `0x85443` | Stores low WORD key at UI `+0x23d618 + 2*slot`. |
| Subsequent name consumer | `0x850fa` through `0x85194` | Reads those four slots, looks up each numeric key, concatenates names at record `+8`. |

The exact source probe produces icon group 37 and action WORD `0xffff` before
asset binding. These are resource fields, not drop groups or weights. The name
loop emits four source names separated by the native comma at image `0x18f1f4`.
It executes as an independent checkpoint on the same VM and native-produced
slot state; this is not a claim that the complete UI caller ran.

The result consumer is run continuously from `0x118bf0` to a qualified stop.
Each positive entry additionally compares its WORD at entry `+4` against
`0xffff` at `0x118c26`. Any match sets a local flag. With spectator state zero,
that flag selects global `0x5b8b5c` through `0x118cc3` and reaches the formatter
call boundary `0x118c5a`. The report derives the selected message from the
actual formatter argument pointer and native-bound message globals.

The native binding loop `0x11125f..0x1112a5` resolves that global to ProgramMsg
298. Its exact CP950 text hex is `b17ab1bcb8a8a548a455b8cbb3c63a`, meaning
"You dropped the following equipment:". The row is message line 2324, decoded
offset `0x169a0`, SHA-256 including CRLF
`40cb0b5887524d5e32d0ec194d2dc2a5eaaf8d8c79e34b8d751f08785271b4e5`.
An explicit nonzero spectator precondition instead selects ProgramMsg 293.
Neither UI branch condition is promoted to a monster drop condition.

## Counterfactuals and Bounds

The report contains 14 deterministic synthetic cases, clearly marked as such.
The tests additionally vary the marker in every slot and exercise signed limits.

- Four positive keys produce four original WORD stores and four numeric item lookups.
- Zero and negative signed DWORDs skip lookup, store, and marker test. Prior slot
  state survives; skipped entries are not automatically cleared by this slice.
- Changing positive DWORD high bits preserves the low-WORD item lookup and slot
  write. This does not establish quantity semantics for the high bits.
- Marker WORD values 0, 1 and 65534 do not select the loss message; 65535 does,
  in any positive slot. A marker on a skipped entry has no effect.
- Changing entry `+6..7` to `0xffff` leaves the observed trace and result unchanged.
  Those bytes are unread within the qualified item consumer, not globally unused.
- Lookup boundary `0x7f58` and an explicitly uninstalled fixture key take the
  original fallback `(65, 0xffff)` while the result slot still receives its key.
  Uninstalled fixture key 1 does not mean key 1 is absent from the original game.
- Selectors 1, 2, 3, 4 and `0xffffffff` never enter this item loop.
- An active control reaches the original renderer CALL boundary `0x106927` and
  stops before executing it. No renderer result or later slot write is invented.

All result packets, prior slot contents, spectator flags and control handles are
synthetic preconditions. The item source row and message bytes are original;
their appearance in a synthetic result packet is not an observed award.
Instruction allowlists, 20,000-instruction/one-second bounds, read-only packet
memory, exact packet-read boundaries, slot write bounds, adjacent canaries, and
unchanged item-record checks constrain execution. The name loop has a separately
initialized stack checkpoint. Native functions are not patched or skipped.

## Coverage and Remaining Frontier

Every source occurrence includes the complete pinned identity tuple, visibility,
source line, decoded byte offset, raw row and row SHA-256. No name or art join is
used. `drop_items`, `drop_rates`, `quantity`, `conditions`, `group_weights`,
`rate_denominator`, `rate_unit`, and `monster_drop_join` are explicitly `null`
for all 7,815 source occurrences, including all 7,791 visible occurrences.
Verified join count zero is an evidence count, not a zero drop probability.

The next concrete native frontier is the original award producer for the four
entry DWORDs at `17 + 8*i` and adjacent WORDs at `21 + 8*i`, with a demonstrated
binding to monster occurrence and variant identity. Original candidate item
sets, quantity arithmetic, executable eligibility conditions, group selection,
and the rate unit/denominator must be established there or in another proven
producer. No call to the EnyName lookup occurs in the executed item-result/name
path. That bounded observation does not establish absence elsewhere.

There is no sample-frequency estimate, weight-to-percent conversion, inferred
maximum of four monster drops, received-loot-as-full-table assumption, or
description-derived formula. This lane is ready for main review; ALL-monster
drop reconstruction remains open.

## Reproduction

From the research root, full machine-readable JSON is emitted to stdout without
creating an additional owned artifact:

```powershell
python -B -m tools.strike_lab.current_monster_drop_rules
python -B -m tools.strike_lab.current_monster_drop_rules --summary
python -B -m unittest discover -s tests/research -p test_current_monster_drop_rules.py -v
```

Validation: 14 focused tests passed. Full inventory provenance and unresolved
coverage are checked for every occurrence, independently of the bounded native
item probe. The previously completed 7,791 native enemy lookups are not rerun
or claimed as new drop evidence.
