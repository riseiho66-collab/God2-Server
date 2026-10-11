# Fruit quests: native reward notifications and NPC resource qualification

2026-09-27, current Taiwan EXE SHA256
`6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98`.
No client was launched in this lane. No live DB, production binary, desktop,
Application or shared CMake file was modified.

## Integrable output: native award notice, not cumulative progression

New header `src/protocol/RecoveredQuestRewardNotice.h` provides:

```cpp
using Notice = god2::RecoveredQuestRewardNotice;
auto exp = Notice::logical(Notice::Kind::Experience, committed_exp_award);
auto fame = Notice::logical(Notice::Kind::Reputation, committed_reputation_award);
```

Call only after the authoritative transaction succeeds, using the actual committed
award. Do not replay the award notice as though a reconnect is a new award. The
header encodes a **notification** and does not credit anything, synchronize total
EXP/reputation, choose level thresholds or patch another snapshot.

| Logical offset | Bytes | Value |
|---|---:|---|
| 0 | 1 | `02` |
| 1 | 2 | little-endian SystemMessage644 EXP or626 reputation |
| 3 | 2 | item key0, selects literal text rather than item-name lookup |
| 5 | 16 | ASCII positive decimal amount, NUL padded |
| 21 | 1 | variant0 |
| 22 | 1 | opaque0, qualified fixture choice |

The native length callback is `401234`, logical23. `484AE0` resolves the source
row, wraps the decimal text with `/c3` and `/c9`, and formats the one `%s`.
`484E00` mode1 invokes `47DE00(channel4, colorFF80FF, text)`. The two source rows
from current `message.csvZ` are:

- SystemMessage626: `626,1,得到 %s 名聲值`.
- SystemMessage644: `644,1,你獲得 %s 經驗值。`.

Packed source SHA256 `5cd34cce66feae96d947cd45e32984765ce625673c0fb19c73cb63d7d9178598`;
decoded SHA256 `370bd6ed9b4892f57190fc7a8dab14061b3e844b0aa9d0171611a9cbab61b5f8`.
Exact source lines/raw bytes/hashes are in the evidence JSON.

The transport helper accepts only1..999999999999999 (15 digits). It throws on
zero, excessive amount, or an unknown enum; it never truncates a 64-bit value.
This bound belongs to the packet's 16-byte text field, not a native gameplay cap.
The reward values in `FruitVillageQuestRules` remain CUSTOM-0051 historical-policy
choices. Native message rendering does not certify their original authority.

## Compiled codec and whole consumer verification

```
python -m tools.strike_lab.current_quest_reward_notice_20260927
python -O -m tools.strike_lab.current_quest_reward_notice_20260927 --codec artifacts/research/quest-reward-notice-20260927/build/reward-notice.exe
```

The tool compiles `tests/test_recovered_quest_reward_notice.cpp` with MSVC C++20
`/W4 /WX` in its private artifact build folder, executes its explicit-check tests,
then passes **that executable's output** to the original world dispatch case02.
No shared core build was used. The test has `main`; root owns its CMake registration.

Both normal and `-O` runs pass24 vectors: two message IDs × amounts
1/400/1500/2000/3000/999999999999999 × normal/private chat. Full original
`484E00→484AE0→47DE00→45FF00→47E380` and native formatting execute; there are no
replaced game callees. Test environment relocates pinned source strings and uses
the native absent-widget sentinel; this does not prove a live display-device blit.

Each case verifies exact CP950 formatted bytes and archived row prefix `1A4`,
channel/color, normal visible ring versus private archive behavior, full return,
unchanged role0x5000 bytes, all50 inventory slots, pending state and the entire
God/pet cache0x22000 bytes. Evidence is
`artifacts/research/quest-reward-notice-20260927/evidence.json`.

## Numeric-state candidates rejected or still open

These conclusions are from the current original dispatch and consumers, not
opcode-name guesses:

| S2C | Length | Actual inspected effect |
|---|---:|---|
| `25` | invalid (`40131E` returns-1) | world dispatch points directly to switch join `46B517` |
| `28` | 3 | `4E6BF0` stores WORD actor+90, used by attribute-point UI; no reputation proof |
| `2D` | 17 | copies role name to actor+6 through `4E7180`, plus world name copy |
| `2E` | 5 | `4E73E0` updates status-bit UI and actor+44A4/+44A8 |
| `22` | existing contract | supplied level/maxima/base attributes and EXP-percent WORD; full refresh side effects |
| `2B` | 21 | role HP, MP and percent WORD, plus selected God's HP/progress fields via `4AA3F0` |
| `89` | existing battle contract | received battle-award presentation; not qualified here as a world quest update |

Neither `2D` nor `2E` supplies total EXP or reputation. `2B` must not be assembled
with zero placeholders simply to move the EXP bar: it changes role and God
state. No new cumulative-EXP/reputation state codec is claimed by this lane.
Keep saved numeric awards authoritative on the server, and distinguish the
verified award notification from the still-open client cumulative display route.
An EXP-percent patch also requires a qualified threshold/unit and complete owned
snapshot; arbitrary award-to-percent conversion would fabricate a formula.

## Four NPC resource loads: native positive result, bounded scope

```
python -m tools.strike_lab.current_fruit_npc_resources_20260927
```

This isolated oracle ran the real current CSV tokenizer/resource catalog loader,
ROMZ decompressor, ROM parser and cache access for all four resources. It verifies
every executed native instruction against the current PE as well as the pinned
mapped image:2,222 distinct instruction addresses. Existing bounded platform
adapters provide file I/O, decimal conversion, allocation and the SEH environment;
native asset lookup or game branch results are not replaced.

| NPCAppearData selector | Source flags | Appearance code | NPC.csv zero-based ordinal | Resource |
|---:|---:|---:|---:|---|
|2936|4000hex|23|22|`data2/rom/npc/npc2723.ROM`|
|2937|4000hex|22|21|`data2/rom/npc/npc2722.ROM`|
|2938|4000hex|37|36|`data2/rom/npc/npc2737.ROM`|
|2939|4000hex|33|32|`data2/rom/npc/npc2733.ROM`|

The ordinary72 path resolves category0 and ordinal `appearance_code-1` through
`461580→45F190`. The selector is not a resource ordinal. In the explicitly empty
fixture bank these load to slots0/1/2/3; production must use returned cache slots.
Chef2936's resource row retains final WORD2; do not replace its definition with a
generic all-zero variant row. All319 NPC.csv rows were parsed natively before
loading. Cache misses, successful loads, cache hits without reopened files and
closed adapter file handles were checked.

ROMZ SHA256 values in the above order:

- `bf091ba5ec9bbeca73ee56df403fd1d5f08e69d61e7e3d8f6d90e5d4c1c7f7a7`
- `8f1e9afda5af15417da48a814f1377df4fa992b7d541757442a41bb863388088`
- `0163af44192b9329baecf29105d052d15c80b74778a886459035eeddde573c90`
- `cb7f898995caf8de14ce17500d58068c696ee7ab2aaa6144e2460e933707533e`

Evidence `artifacts/research/fruit-npc-resources-20260927/evidence.json` retains
source rows, packed/decoded hashes, full native76-byte resource records, load
outputs and actual decompression sizes. This proves the four resources can load;
it does **not** qualify a complete S2C72 scene placement, render/hit target,
NPC-facing choice, click event, production route or original coordinate authority.
Those require root's separate current-client integration acceptance.

## Fruit navigation integration delivered afterward

`RecoveredFruitNavigation.h/.cpp` loads only exact JSON SHA256
`a07db1f68dab7294c41d0813da85c134f7c3b454bef352e337d40157c843f55d`
from `artifacts/world-atlas/fruit-13-12.json`. API:
`static load(path) -> RecoveredFruitNavigation`, explicit path constructor,
and `consistent_cell(int,int) -> uint8_t`. It validates189×189, area13,
scene12, kind0, and absence of dynamic occupancy. Unknown255, conflict254,
blocked0 and out-of-bounds all return0; pass values1/2 are preserved.

Pinned raw counts:20,955 blocked,7,768 value1,26 value2,357 conflict and6,615
unknown. This provides7,794 accepted static cells. The four text-coordinate
cells108/110,113/69,69/72,68/116 all have value1; that fact is navigation
qualification, not additional NPC placement authority.

`RecoveredMovementService::TownDiagnostic` appends `fruit_navigation` after
existing fields. A nonempty path loads the qualified map; saved area13/scene12
positions validate against it and restore kind0. The move path now uses these
cells for that exact area/scene. Initial spawn and transfer APIs are unchanged.
Application/Config/CMake remain root-owned and were not edited here.

```
python -m tools.strike_lab.current_fruit_navigation_cpp_20260927
```

Private MSVC C++20 `/W4 /WX` passed: the new standalone navigation test traverses
all35,721 cells and tests constructors/bounds/conflict/unknown; changed, truncated,
empty, oversized and missing sources are rejected. The changed movement
translation unit also compiles to a private object. Eight commands and source
identity are retained in `artifacts/research/fruit-navigation-cpp-20260927/evidence.json`.
No shared core build or DB mutation was used. Saved-position/runtime integration
acceptance remains a separate root test.
