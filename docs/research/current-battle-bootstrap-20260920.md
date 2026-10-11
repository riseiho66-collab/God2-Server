# Current native battle bootstrap integration

Later same-stack continuations are separate regression stages. Latest battle
frontier: `current-battle-owner-map-panel-20260920.md`, separate native world
resources and the actual C3080 prefix up to, but not executing, C3640. The boundary below is
older; none of these stages claims a full initializer or live battle acceptance.

## Evidence and execution boundary

The image is the current `native-master-01-stable.bin`, SHA256
`149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
Addresses below are RVA, base `400000`. No retired server archive is used.

`current_battle_bootstrap.py` joins the original battle-resource preload and
normal initializer in one VM. After explicit preparation stages, one call to
`run(1112C0,11BC2A)` executes the normal entry without skipped gameplay calls,
fabricated game return values, or instruction patches. The final address is
after all three window constructors return and the11BB80 prefix reads its
two qualified character-source bytes. The11BB80 function has not returned.
It is not a successful return from the complete initializer. The owner is
the still-explicit descriptor `+8` pointer. Its slot44 bytes now come from the
original packet-store instructions in the same VM. The catalog is explicitly
bound to native-loaded current source metadata in the optional qualified mode.

The formal C++ encoder first frames an `82` context plus a following `83`
record. The original world receiver consumes that frame. Its resulting context
is supplied to the bootstrap VM as a second, explicit stage. This is NOT a
single live client/server session or a complete world-to-battle main loop.

## Actual resources, explicit snapshots

The ten original assets and native preload are documented in
`current-battle-resources-20260920.md`. The bootstrap uses their actual returned
handles, native renderer constructor, and original constructor checkpoint tail
`110E72..110E95`. The name registry checkpoints contain ten entries. No CSV
index is substituted for an independently produced resource handle.

The current `Data2/Patch/Comm/message.csvZ` is also pinned:

- Raw SHA256: `5cd34cce66feae96d947cd45e32984765ce625673c0fb19c73cb63d7d9178598`.
- Decoded SHA256: `370bd6ed9b4892f57190fc7a8dab14061b3e844b0aa9d0171611a9cbab61b5f8`.

Original decompression is compared with the decoded source. All 1080 ProgramMsg
records pass through original parsing `51BE0` and row writing `58CD4..58D67`.
Original setter `11F960` binds that reader. The normal UI path copies message
IDs 738, 742, 743 and 750 to its original string buffers; tests compare exact
source bytes. The supplied reader/queue/root/display snapshots remain explicit
fixture preconditions, not captured live state.

The battle object is relocated to `20000000` because its embedded UI occupies
roughly 176 MB. Keeping the smaller resource-only harness's address would alias
the ROM heap. Mapping coalesces unmapped gaps without replacing existing pages;
the regression includes a pre-existing page between two holes. Unowned arena,
display and source bytes are poisoned and checked after execution.

## Proven normal-entry prefix

- Input reset, queue reset and manager initialization execute once.
- All 168 record pointers are established by original entity-record resets.
- Original registry scan/pool reset execute; 33 display setters return.
- The original control strip creates 25 sprites and hides all 25.
- Original UI reset/binding and two dimension queries execute.
- Three further sprites are created, for 28 total handles (0 through 27 in
  this fresh explicit fixture). Resource fields retain the native handles.
- Context words survive from the receiver; source/display/arena guards remain
  intact. The old `111614` call boundary is now crossed normally.

## Controls and battle windows

`111614 -> 34650 -> 34680` binds the actual renderer/resource and explicit
mouse input owner. Original `188C0` resets all 3072 input records and its tail,
preserving the eight unowned bytes at `+12008`. Original `343B0` resets 128
secondary control entries. Every byte of the poisoned main 128-control table,
including unowned bytes, is checked against the native stores.

`111638 -> 104160/1041A0` resets 128 panel records, each containing 106 child
slots, plus the native ordering pool. It creates sprite 28 from FightGUI2
action `61` hex. A read-only observation hook at `111654` captures the reset
state and counters. The hook does not stop emulation, alter registers or write
VM memory. Tests compare the complete panel and mouse snapshots.

`111654 -> 10FB10` then returns normally. Actual original image rectangles
and loaded ProgramMsg strings create window selector 0, ten base controls,
nine label/icon controls and four animated controls. Sprite count reaches43.
All 23 child rectangles and nine label strings are compared with their native
sources, and original returned handles occupy the expected fresh slots.
Original list initialization and nine row setup calls execute, including nine
real `146CF7` formatting calls with their original empty format string.

`11165B -> 10FF00` creates window selector1, six base controls, five label/icon
controls and four animated controls, with its own list control. The count is
now53 native sprite creations and14 original formatting calls. Fifteen further
child rectangles, five strings, handles, list state, and external guards are
checked. `110210` reads the first WORD of slot44 at `110228`, then calls
`9B670 -> 9B720` with that key. The explicit fixture key is `1234` hex,
not a captured player item. No game lookup return is fabricated.

The 25-byte logical `3B` record first round-trips through the formal C++ codec.
A separate preparation stage executes original secondary dispatch `1193C2`
and store `98DD0..98E2D` in this same VM. Five original DWORD writes fill
exactly20 bytes of slot44. Other49 slots, padding, input and canaries remain
unchanged. This stops before the handler's metadata continuation; it is not
the full handler, network reception or a live inventory transaction.

Without `owner_catalog=True`, the unknown catalog pointer at `owner+CFF70`
remains poisoned/read-guarded and execution stops before that read at `9B724`.
Missing or zero-key owner input retains the earlier `110228` boundary; the
cheap boundary-selection regression is not another native run.

The qualified catalog mode currently requires the explicit key4660 fixture.
Original57 RomMaps row loads and complete59420 parsing of current `MIS:4660`
(source line7636, tag-table selector24) execute in this SAME resource VM.
Original59A20 registers the resulting record pointer, which is retained without
allowing a later row to overwrite it. The owner catalog pointer is an explicit
binding to this native-populated table, not a copied record from a separate VM.
Normal initialization calls59A60 and9B720 and reads this exact record after
original resource binding described below. Bound item bytes, guards and map
rows remain unchanged during the normal initializer.
The source icon is51123. This is a synthetic slot fixture, not evidence that a
real character owns this item or that MIS:4660 is valid equipment for slot44.

FFFF is only the row parser's initial action value. Preparation now loads the
pinned MIS03.romZ into native bank slot102 via29820, original decompression and
the ROM parser. This is one statically qualified preload slot, not all57 item
ROMs. Original81700 walks the sparse native index and calls1AE70 to search actual
ROM action IDs. Its original stores change group37 to102 and actionFFFF to122.
See `current-item-action-binding-20260920.md` for pins, caller evidence and
the native rebase-completion guard. Nothing is copied from the sidecar VM.

The constructor tail110E95..110EAB consumes an explicit display-manager
argument and writes battle+30. During normal initialization,20580/27400 reset
the same manager's5000 sprite records. Before the item allocation, every byte
of that pool is compared with the original reset writes and untouched input.
Original9B670/1E710 then return source-backed bitmap/palette/flags. Original
25B60 allocates slot0;25DC0 registers those exact outputs;271E0 hides the sprite
because the second panel's native flags contain10h. The cached item key becomes
4660 and both110210 and10FF00 return normally. No pixel presentation is claimed.
The resource VM retains its existing CRT adapter; no duplicate decimal-call
handler or game-function stub is added.

The existing preview harness's CopyRect/OffsetRect OS adapter is reused only
for those two captured IAT targets. It is not used to intercept game code.
Observed totals are40 copies and38 offsets. Original renderer, record,
control, string-formatting and list functions execute their own instructions.
Exact code-byte checks cover the initializer and newly qualified control paths.
The last ESP is initial ESP minus `54` hex, within the actual11BB80 call.
The first window's completed counters are separately captured at
`111659`, without interrupting the single normal-entry execution.

## Third Window And Next Data Boundary

Original111662 calls110480, which returns at11062C and reaches111667.
It creates panel selector2, four base controls and one animated control from
the original rectangles at59C228/59C238 and resource actions2C/2D/32.
Native sprite handles53/54 and four original empty-string formatter calls bring
the totals to55 sprite creations,43 child controls and18 formatter calls.
CopyRect/OffsetRect totals are46/43. All five child rectangles and the remaining
101 inactive child slots are checked; no new OS adapter or game stub is added.

Its list lives at battle+AB3B1E0, directly after the panel-ID fields. Its valid
header is not an outer panel guard. The third selector is atAB3B1DA, not the
unusedAB3B1D4 field. The first-list preguard also overlaps valid third-list tail
fields; only the actual four-byte gap is treated as a guard. Exact first/second/
third list state and the original panel reset snapshot remain checked.

Descriptor+10 names a distinct CHARACTER_ROOT, not the ProgramMsg
reader. The normal caller passes CHARACTER_ROOT+90 to11BB80. Existing ProgramMsg
loads still use their qualified reader independently. The nine pending arguments
are verified, including the low-WORD resource handle: caller11166A writes onlyAX
and callee11BB80 reads a WORD. Unknown character bytes are not replaced by zeros
or tokenized message text. Without the explicit character packet mode, the
source remains unmapped and the earlier1116A4 boundary is retained.

## Original Character Writers In The Bootstrap VM

Optional `character_row` requires an explicit, qualified19-byte logical S2C30
packet. The regression supplies signed key-100, a terminated Probe100 name and
flag2; these are synthetic branch inputs, not a captured account/owned character.
The independent sidecar additionally exercises16 named rows plus S2C22/31;
those scalar packets are not integrated into the bootstrap fixture here.

Preparation maps a new actor with explicitA5 unknown bytes. Original68120
clears exactly its row storage/count and sets selectionFF; original81C81 and
81D0A/E7C80 publish root+90 to the packet owner. Original69F85/AA040 then consumes
the supplied S2C30, creates one named row, increments count to1 and selects row0.
The reset stops before97FE0 and the append beforeAA1B5 refresh. These are explicit
preparation stages, not a full network dispatch or world-constructor execution.

Every actor-byte change must equal the actual native write trace. A read guard
then rejects any subsequent native read outside that produced-byte footprint.
Normal1112C0 publishes descriptor+10 through111326, sets up all three windows,
constructs the original nine arguments and calls11BB80 without interruption.
Reads11BC18/11BC21 consume exactly root+15F/root+164. The selector's full351C
bytes are checked against original stores, including all16 row pointers at
root+168+i*3EC. The actor and input packet remain unchanged by the consumer.

Selector storage is adjacent to attachment records and other valid state. Its
preparation writes only its own351C bytes. Neighbors are compared with their
actual pre-call snapshots, not overwritten as fabricated guards; the real
four-byte attachment/selector gap remains guarded. See
`current-battle-character-binding-20260920.md` for native writers and prerequisites.

## Verification and remaining work

Twenty-one focused tests cover the joined prefix, messages, context, memory layout,
control/panel resets, both windows, sprites, input validation and rejection of
re-entry. Run:

```powershell
python -B -m unittest tests.research.test_current_battle_bootstrap -q
```

The earlier metadata-only9B690 boundary passed15 tests in97.66s.
Latest bootstrap passes21/21 focused tests in108.605s, including original file
loading of all448 skill definitions and a nonzero S2C34 pointer in the same VM.
Previous registered bootstrap passes19/19 focused tests in108.99s, including the
same-VM S2C30 write-to-normal-source-read chain and exact selector/neighbor bytes.
The third-window-only1116A4 boundary passed17 tests in107.05s.
The previous registered bootstrap passed16/16 focused tests in108.37s. All5000
display-pool reset records and4999 untouched post-item records are compared.
Item lookup/bitmap/registration witnesses distinguish the exact caller return
addresses from other UI calls to the same shared native functions.
The previous packet-store-only boundary passed14 tests in95.03s.
The earlier unseeded prefix passed12/12 in95.768s. The intermediate first-window
boundary passed11/11 in95.570s. The earlier resource7 + bootstrap7 +
participant42 combined result (56/56 in163.477s) is historical.

The stop is11BC2A before the rest of the selector setup, pagination and learned
skill consumers. The new same-VM preparation executes original12D3B0 file loading
and optional S2C34 writes against that retained catalog; its integrated fixture
has one nonzero definition, not an empty learned list. Source and packet fixture
rows do not prove owned skills or monster assignments. See
`current-skill-catalog-loader-20260920.md` for exact stages and boundaries.
The rest of the
initializer are not covered. Participant consumption has separate bounded
tests in `current-battle-participant-20260920.md`, with supplied existing actor
snapshots; it is not yet connected to this initializer. Neither suite proves
server damage authority, actor creation, a live battle, or battle completion.
No production database or runtime combat policy was changed.

## Retained-Stack Selector Continuation

Original11B7B0 now constructs the selector before normal initialization; the
full object footprint is checked. Its actual page-index zero replaces the old
unknown byte precondition. A separate `continue_selector_windows()` resumes the
unchanged11BC2A stack through11A9D0,11ADB0 and11C4B0, stopping at11BC95 before
label/icon population. The initializer is not re-entered and no game return is
faked. See `current-battle-selector-windows-20260920.md` for exact stages and
verification. This continuation does not yet finish11BB80 or qualify live UI.
