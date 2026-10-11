# Current daily-panel lifecycle — 2026-09-27

## Qualified result

Current EXE SHA256:
`6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98`.
All addresses are VA, image base `400000`.

* **Open-list request is C2S `D7 00`, logical length2.** The original menu
  producer `4A6760(0,12)` and menu release handler `4A6D90(27h,20h)` both
  return through original `4132E0` with those bytes. Original `415CE0` length
  table initialization independently produces D7=2 and D8=9.
* **D8 mode2 is the 「每日領取」 button**, not list opening or generic quest
  acceptance. The native text-to-control join is verified below. This names
  the user's requested action; it does not recover original eligibility,
  reward identity/count, cooldown reset or server transaction rules.
* Full FD subtype2 dispatch, ingestion, source lookup, formatting and UI
  refresh **return** for counts0/1/8/9/39/40, four auxiliary contexts and eight
  flag patterns. The fixture has an initialized daily widget with renderer
  handle FFFF. This proves formatted text/calls, not final graphics or actual
  live client acceptance. No original game callee is stubbed.
* S2C7A mode5 selects the separate DailyMissionMessage text table. Four
  source-backed vectors run to **before `4C81F0` renderer entry**. This is a
  bounded slice, not a complete dialogue render or quest progression proof.

The earlier [frontier report](native-quest-exe-frontier-20260926.md) covers
D8 selection/preserved-tail vectors and FD framing. This report advances full
list return, exact button names, actual open request and mode5 source lookup.

## FD172 layout and state

Logical bytes: `FD AC 00 02` followed by **168 bytes**. The length WORD is172
including opcode/length/subtype. Existing outer framing is separate.
`4858B0` passes payload to `48B710` with `this=*(UI+232EBC)`; call this object P.
P+DC points back to UI. P is not the world/role object.

| Payload offset | Width | Native destination / use |
|---|---:|---|
| `0..9F` | 40×4 | entries `{index:u8, branch:u8, current_count:u8, flags:u8}` |
| `A0` | BYTE | count, stored WORD P+20F30; copy count DWORDs to P+20F32 |
| `A1 low4` | nibble | P+20FD6; purchase gate equals1 |
| `A1 high4` | nibble | P+20FDE; daily-claim gate equals1 |
| `A2` | WORD | P+20FD4, displayed purchase item key |
| `A4` | WORD | zero-extended DWORD P+20FD8; displayed `%d` special-sale amount |
| `A6` | WORD | P+20FDC, displayed daily-claim item key |

The final WORD occupies logical bytes170..171: it is part of the fixed list,
not an optional extension. Preserve full owned bytes and both nibbles. Zero
unknown context for newly declared display fixtures; do not populate claim or
purchase fields by guessing rewards. A1 values other than nibble1 are retained
but do not enable the corresponding action. A4's full `65535` is verified to
zero extend, rather than sign extend.

**Hard server bound: count≤40.** Count41 actually writes beyond the 160-byte
array at P+20FD2. The oracle executes malformed ingestion only to48B7D0,
before UI calls, and observes the overflow. Never send/render it. Existing
native code does not impose a 40-entry clamp.

P+20F28 resets page0; P+20F2C=`max(1,ceil(count/8))`. Native ingestion copies
only `count` entries and does not clear old entries after a shorter list.
The final detail refresh in48C040 can look up the end index, including a
one-past entry; it does not establish an extra authoritative row. The real
source includes **valid pair(0,0)** (first row 「煉丹修行一」), so zero pair is
not an empty sentinel. Server issuance must use explicit count/bounds and
source identity; never infer authority from stale client memory or a zero key.

### Flags and native input

`48C040` uses low6 bits for row color: 0→7F7F7F, 1→FFFFFF, 2→00FFFF. Other
nonzero low6 values do not actively choose a new color in this branch.
Both row buttons are enabled only when **low6!=0 AND (flags&C0)==40**.
Native tests cover 00/01/02/40/41/42/81/C1 and inspect the actual calls to
`506AD0`. High bits are not dispensable; `01` and `41` differ visibly.

`48B9B0` itself checks only low6 and source pair lookup. It does not validate
count/high bits if called directly. A server binding should also require
the issued visible/enabled state, rather than model this bypass as permission.

## Exact source-to-button join

Native initialization slice `48AEB3..48AF0A` reads WORD IDs at
`58F2EC..58F34A`, resolves ProgramMsg pointers and writes `5B65F8..5B66B0`.
The oracle executes that original loop, not a Python substitute.

| Daily control(s) | Pointer slot | ProgramMsg | Original text |
|---|---|---:|---|
| `1A..21` | `5B6660..5B667C` | 950 | 傳送至NPC |
| `22..29` | `5B6680..5B669C` | 950 | 傳送至NPC |
| `2C` (icon `15`) | `5B66A8` | 951 | 購買道具 |
| `2D` (icon `16`) | `5B66AC` | 952 | 每日領取 |

`48A6A0` creates these controls. `2A` is previous page, `2B` next page,
`19` closes; right-event bit2 also closes through48B920. Title/header source
ProgramMsg956 names the weekday/time/quest/level/restriction/count/transport
columns. Source descriptions and reward strings remain display text.

`16/2D` with event bit1, P+20FDE==1 and nonzero P+20FDC queues exactly
`D8 02 00 00 00 00 00 00 00`. **It transmits no item key or daily pair**.
The 24 native request cases include invalid/unresolvable keyFFFF: the click
producer still emits mode2. Rendering separately resolves the displayed item
definition. Server authorization must come from its issued owned context.

Row start/end requests retain the already recovered mode1 schema:
`D8 01 index branch item_slot npcLE side tail`, side1=start or2=end.
They point to source start/end NPC IDs. The native item scan looks for18CA,
without a count/ownership test. Source ProgramMsg965 explicitly asks whether
to use an NPC transport item to travel to the quest NPC. If the item is found,
dialog31 confirmation at483C80 sends the buffered eight bytes. If absent,
the selection queues immediately. These are transport-oriented controls, not
evidence of original quest-accept or completion transitions.

Purchase15/2C uses ProgramMsg954 and dialog32; confirmed483C80 sends **BF**,
body `{item:u16,1:u8,1:u8,amount:u32}` from the list context. It is separate
from D8 daily-claim; no store/price transaction is authorized by this report.

## Physical client entry and read-only acceptance

World event4820A0 dispatches HUD widget `UI+232DB6` to4B1660. Its control8
on bit1 toggles the menu through4A65B0/4A65F0, widget `UI+232E4E`. The keyboard
path in4AACD0 checks418490(48h), which requires Ctrl, no Shift/Alt, and the H
key transition: **Ctrl+H**, not bare H.

Menu category state WORD `UI+A3CF4=16h` selects group0. Menu control27h on
release bit20 invokes4A6760(0,12) and emits D7 00. Bit1 starts drag handling;
the release completes this action. The same producer is reachable through
4AE520 for an already configured shortcut record `{type1,group0,index12}`.
Do not write client memory or install such a shortcut merely to claim normal
physical input acceptance.

Daily widget index is signed WORD `UI+232E00`; node address
`UI+E2988+index*2A08`. 48B7F0 opens it only if daily flags20/8 are absent and
the HUD widget `UI+232DD8` is valid with flag10. Therefore delivery before
world UI readiness may store/render data without visibly opening the panel.
This oracle skips native multi-window opening by using absent HUD; the hidden
client lane must verify this actual ready-state transition independently.

For renderer readback, node+4 is the renderer handle. Renderer object pointer
is `*(UI+CFF60)`; render node is `renderer+10+handle*290`. Grid columns use
sprite WORD `render_node+AC+2*column` (506390→41E2B0). Static labels use sprite
WORD `render_node+E` (5077C0→41E500). Sprite system is `*(renderer+4)`;
signed text index is at `sprite_system+1264+sprite*200+2*row`. The text record
is `sprite_system+F66E4+text_index*8C`, string at+C, up to127 bytes. Respect
sentinels and index bounds; markup can be stored as internal segments.

## Daily dialogue namespace and safe integration

S2C7A mode5 consumer4C7F10 uses resource+FC2D4 count and FC2D8 text-pointer
table, selecting `(key-1)*4`. Mode4 uses MultiMessage instead; these are not
interchangeable. IDs must be 1..300, non-null source backed; zero is unsafe
because this mode does not guard against indexing before the pointer table.
Vectors1/2/3/300 select exact CP950 source text and reach4C81F0. No join from
daily `(index,branch)` or start/end NPC to these dialogue IDs was established.

A safe initial runtime integration can restore an explicitly owned full172
list on D7, validate its pinned source pairs/context, and bind subsequent D8
to that session's actual issuance. Keep no-row as no grant. Record validated
interaction separately from progression, teleport or claim success. Reject
unknown pairs, disabled/unissued rows, NPC/side mismatch, unavailable auxiliary
context, stale revision and mixed mutating records. A display-only server must
not emit an invented successful-claim or teleport result for mode2/mode1.

Source pins:

* DayMissionDesc.csvZ SHA256 `4a347d56706946d7004b2bd2118500ffc60844628fa461862b2f6d5320a90e54`;
  output includes exact selected source line, row SHA and decoded SHA.
* message.csvZ compressed `5cd34cce66feae96d947cd45e32984765ce625673c0fb19c73cb63d7d9178598`,
  decoded `370bd6ed9b4892f57190fc7a8dab14061b3e844b0aa9d0171611a9cbab61b5f8`.
* DailyMission01.csvZ compressed `f5b6653b9390b44f4fb6af96bb1247f2d2a5c2d639f5a6fa9e735662f4090d72`,
  decoded `0c424ba0abb49e2f240b323cdbd97b1506c086184acff21649c388924b955556`.

## Reproduce

```powershell
python -m tools.strike_lab.current_daily_quest_lifecycle_20260927 --output artifacts/research/daily-quest-lifecycle-20260927.json
python -O -m tools.strike_lab.current_daily_quest_lifecycle_20260927 --output artifacts/research/daily-quest-lifecycle-20260927-optimized.json
```

PASS: **18 full list returns, 24 auxiliary request cases, 4 mode5 pre-render
slices**, plus native label initialization, D7 direct/menu-release producers,
D7/D8 length initialization and count41 overflow boundary. No game callee
stubs; exact slice hooks only stop at declared boundaries. Source row layouts
are relocated from known field mappings, not newly proven CSV-loader output.
Repeated entries and availability values are synthetic test inputs, not owned
live quest authority. Checks remain active under `-O`; result files are replaced
only after complete success. No runtime, DB, client, desktop or network changes.
