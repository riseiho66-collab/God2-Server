# Current EXE quest frontier, 2026-09-26

## Scope and result

Read-only targeted audit of current client Data2 and the current reconstruction
`C:/Users/risei/Desktop/God2-解殼EXE原始碼重建/decompiled/functions`.
Current God2.exe SHA256 independently read this round:
`6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98`.
Addresses below are **VAs**, image base 400000. New findings are static
decompiler evidence, not newly executed native or live-client acceptance.
No retired corpus, live DB, client execution, or production source changed.

The strongest next edge is the **daily quest list and D8 selection contract**.
The inspected EXE does not turn all418 journal definitions into executable
prerequisite, progression, or reward rules. No new authoritative reward amount
or complete quest transition graph was established. This bounded negative
finding does not prove that no other client file contains useful rules.

## Fresh current-resource inventory

The existing `recover_quests.build_catalog(Path('../God2'))` was run read-only:

| Resource | Actual records | Compressed SHA256 |
| --- | ---: | --- |
| Mission_data.csvZ | 418 definitions, 2014 descriptions | 659c8f38ffd9c34107969b449afd16488665a08970110910c9aed8448a0bb716 |
| ActMis.csvZ | 169 requirement rows | e1e35ee689d12ef265be8620b21f856709976896a46edeb9f31c15622041accf |
| DayMissionDesc.csvZ | 85 rows | 4a347d56706946d7004b2bd2118500ffc60844628fa461862b2f6d5320a90e54 |

All three pass existing structural checks (zero structural issues).
Each `NPCMission01..14.csvZ` contains1000 numeric text IDs; file15 has600.
Together these are continuous1..14600. `DailyMission01.csvZ` has300 text IDs
1..300. This count includes resource entries, not verified playable quests.
Traditional and `-gb` variants are separate resources; they must not be joined
by filename order or interpreted as extra quests.

All scoped quest-named csvZ files decoded successfully using the existing
05/16 LZSS wrapper decoder. No encryption key is needed for these files.

## What the native loaders actually produce

`455780` chooses language and loads numbered NPCMission files;
`456130` dispatches section names. `NPCMissionMessage` calls `457A90`,
which stores text pointers at resource+B2C4C, count B2C48. `Mission_data`
calls `4584A0`, producing40-byte description records at resource+D2AC4.
Neither inspected loader creates reward transactions or prerequisite edges.
Existing journal consumers and 85/86 dialogue contracts remain separately
qualified by the earlier current-quest documents.

New daily edge:

* `456130` dispatches `DailyMissionMessage` to `457E90`: text-pointer table
  resource+FC2D8. `4C7F10` is a concrete text consumer to inspect next.
* `DailyMisDescNum` dispatches to `457FF0`: allocation at resource+FC2E0,
  row stride13C (316), count WORD resource+FC2DC.
* `458430(index:u8, branch:u8, destination)` scans rows for the exact pair,
  copies79 DWORDs (316 bytes), returns1; not-found returns0.
  This **pair namespace is proven** and is not Mission_data's journal ID.

Selected `457FF0` field mappings (source columns are one-based):

| Native row offset | Width | Source |
| --- | --- | --- |
| 0,1 | BYTE each | index, branch (columns1,2) |
| 2,4 | WORD each | start NPC column4, end NPC column11 |
| 6,8 | WORD each | start/end time columns6,7 |
| A,C | WORD each | lower/upper rebirth/level columns9,10 |
| E | BYTE | discriminator column8 starts R/r ->1, otherwise0 |
| F | BYTE | accept-count column19 |
| 10 | DWORD | weekday column5: native checks eight-character string and tests positions1..7 for ASCII1 |
| 14 | text | name column3 |
| 32 | text | restriction column12 |
| 46,6F,98 | text | descriptions columns13..15 |
| C1,EA,113 | text | start/end/reward text columns16..18 |

`48C040` formats time with divide/remainder100 and the R-mode bounds with
divide/remainder1000. It displays the reward string. The inspected function
does not compare current player level, time, or inventory against these fields
and does not parse reward text into an item/EXP award. These fields can support
a native display/import schema now; treating them as server enforcement needs
separate qualification of server policy and namespaces.

## Server-fed daily state and exact next packet work

`4858B0` routes **FD subtype2** to `48B710`, passing pointer+3 from its
extended-record pointer. Full wire framing/length still needs the current
length table and extended-record oracle; do not infer it from this call alone.

`48B710` consumes a fixed-layout payload:

* first160 bytes: capacity40 four-byte entries;
* offsetA0 low BYTE: count; native copies that many DWORDs to panel+20F32
  and stores count at20F30 (there is no visible <=40 clamp here);
* each row bytes0,1 identify the `458430` pair; byte2 is rendered as a count;
  byte3 low6 bits affect availability/color and reject clicking when zero;
* A1 low nibble ->20FD6, A1 high nibble ->20FDE;
* WORD A2 ->20FD4, WORD A4 -> DWORD20FD8, WORD A6 ->20FDC;
* `48B7F0` and `48C040` perform subsequent UI opening/rendering.

Thus the packet supplies per-player availability; the static description file
does not itself create that state. A future encoder must cap entries at40 even
though the native byte count can encode255.

`48B9B0` click controls1A..29 choose the visible row (page*8 + control%8),
reject row.byte3&3F==0, resolve its pair with458430, then construct **D8 body8**:

| Body byte | Proven source |
| --- | --- |
| 0 | 1 |
| 1,2 | daily index, branch |
| 3 | first inventory slot0..29 with low16 key18CA, otherwiseFF |
| 4..5 | start NPC if first control group, end NPC if second (little-endian WORD) |
| 6 | control group1 or2 |
| 7 | retained panel+20FEB; zeroed by48B6C0 initialization, not rewritten in this click branch |

The scan does not test inventory count. A server must independently validate
ownership/count, actor location, dialogue/session state, and request binding.
If item18CA is absent it queues D8 immediately; if present it opens dialog31,
whose confirmation at `483C80 case31` sends the same buffered eight bytes.
Do not call this opcode 'accept quest' yet: the start/end-NPC and item branch
may be navigation/transport interaction. Exact gameplay meaning is OPEN.

The other click path (controls16/2D) queues D8 with DWORD2 then DWORD0,
gated by panel+20FDE==1 and nonzero20FDC. It is a distinct variant, not the
daily pair request above. Controls15/2C open dialog32, whose confirmation
sends BF body8. These variants must not be decoded as one generic quest ID.

## Implementation boundary / next bounded verification

1. Execute457FF0/458430 against the actual85 rows to verify narrowing, weekday
   mapping, zero-key acceptance and duplicate-pair behavior. Import all raw
   fields with file/row provenance; preserve descriptions as text.
2. Execute48B710 with count0/1/40 plus guarded41 and verify the FD length/parser.
   Then execute48B9B0 through132E0 for both start/end controls, item present/
   absent, availability0/nonzero, and dialog31 confirmation. Preserve byte7.
3. Only after that, add strict daily state projection and D8 variant codecs.
   Require stored authority for the list and bound issued requests to their
   session; no automatic quest acceptance or reward from clicking text.
4. Main/side quests still need a proven join across journal Mission_data,
   NPCMissionMessage text IDs, ACTMIS serials, world NPC identities, and server
   transition/reward definitions. Equality of their numeric IDs is not a join.

The existing15-slot DB journal codec can restore saved journal entries now.
Its display coverage (418 definitions/2014 descriptions) must remain distinct
from executable completion, prerequisite, consumption, and reward coverage.

## Same-round native execution and codec follow-up

The delegated follow-up now adds `RecoveredDailyQuestRequest.h` and its focused
C++ test. It is a parser/encoder and issued-list matching helper, with no
Application registration, DB mutation, success response, or gameplay rule.

Fresh Unicorn runs mapped the actual PE sections after checking the current
SHA above. They ran72 combinations of control1A/22, retained tail00/A5/FF,
availability00/01/40/3F, and item18CA absent/at slot0/at slot29. Execution
started at48B9B0 and used actual458430 and4132E0, bounded to5000 instructions.
No game function was replaced. The no-item enabled path returned normally
with exactly `D8 01 07 09 FF 34 12 01 tail` (start) or
`D8 01 07 09 FF CD AB 02 tail` (end). IDs7/9 and NPCs1234/ABCD are synthetic
diagnostic fixtures, not recovered quest bindings. Disabled low-six-bit cases
returned with no append. Item-present cases assembled the matching slot then
stopped **before48BCA3**, the real confirmation branch; this run did not
execute the modal renderer or confirmation callback. Count-zero inventory
still matched18CA, proving the client does not supply a count/ownership gate.

Native48B710 was separately executed to48B7D0 (before the first UI opening
call), with counts0/1/40/41/255. The255 case really copies1020 bytes, exceeding
the40-entry capacity. This is a malformed native input hazard, not permission
to publish255 entries. Rendering/whole-client acceptance remains untested.

Exact current world-table FD target is469245: increment logical pointer past
opcode, pass it and FD to4858B0. Consequently subtype is logical byte3 and
48B710 payload starts at logical byte4. Its final WORD read A6 consumes through
A7, giving the qualified fixed-list size172. The new read-only list guard
requires exactly172, subtype2, matching length word, count<=40.

FD's actual length table pointer401318 returns-2. A fresh original1351F slice
passed12 length cases0/1/2/3/4/171/172/173/2559/2560/2561/65535: values<2560
reach assembly,2560 reaches capacity rejection, greater values assertion.
Native does not impose the content minimum; the new fixed-layout guard does.

Current-code SHA256 pins, RVA intervals with exclusive ends:

| Span | SHA256 |
| --- | --- |
| 8B9B0..8C004 | dd3999fcc9fe6559480451707684b668a48a171178cd613ee67bf2bb6420a305 |
| 58430..58495 | 04d786b7297933b6c04b31ea0e50b0d8088bf301befbf1bf700003bbd7df6d9d |
| 8B710..8B7D0 | 59ebc6f434adf91b145271a41238aea4b95070751140cb9c7dfd4f1d6d865fb9 |
| 132E0..13368 | 139a14d71f308d37f84a5a06989e09763b1954d637a6b5304949fc58ef5168df |

The standalone C++20 test compiled with MSVC /W4 /WX through existing
`test_current_instance_update.build_fixture(..., source=...daily_quest_request.cpp)`
in a temporary directory and exited0. It covers18 producer-shaped vectors,
all256 namespace/slot/side values, opaque roundtrip, both D8 variants,
truncation/extra bytes, binding mismatches, and all256 list counts. Native
execution and codec bounds success do not qualify original rewards or a
playable daily quest. All temporary compiler/native processes exited.
