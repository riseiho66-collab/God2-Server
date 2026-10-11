# CN flag0 resource replacement and plain MAP cells

Previous round made progress: same-MDT retained-MBD camera requests now produce
real full-nine geometry and a generation-bound cache commit. This round connects
the different-MDT flag0 branch through actual MDT/MDL/model-ROM/.map loading and
resource/cache commit. Two C++ files are added and six existing files change.
This is source integration, not a complete world/movement route or acceptance.
No build, tests, asset reader, Lua, game, server, production DB or deployment runs.
Native fonts, Traditional/Simplified conversion and frozen features are preserved.

## Load flag changes the native path

Primary00470C90 assembly pushes0 at00470F27 before call00470F37 to00462980
(absent current resource), and at00471030 before call00471046 (different current
resource).00462980 reads MDT, changes its extension to.mdl and calls004642A0.
At00463440 it compares its third stack argument to0;0046344E jumps to00463E7B
when zero, skipping the.mbd/00463F10 branch.0045EDF0 initializes the new resource
and its terrain filename. This flag0 path must not be implemented by reusing
initial flag1 CAN/MBD loading or by inventing an MBD neighborhood.

00470C90 then uses0045E7F0 for independent.map files when that terrain filename
is empty. Different resources set prior center(-1,-1);0046D460 clears every slot
valid flag without rotating pointers. The requested ASCII axes/delimiter must
qualify, then MDT width/height clamp them to1..size-2. The loaded full-nine branch
uses row-major generated names and0046F630's compositor. Failed/null slot native
success is a separate unresolved variant, not a full-nine success claim.

## Plain MAP parser and exact cell bytes

0045E7F0 calls004657E0, which uses plain fopen("r"). There is no preferred Z
reader or05/16 decoding on this path. Header MAP is case-sensitive; section labels
are compared with__stricmp. Version comparisons are lexical againstv1.0/v1.1;
only these two recovered layouts are supported here, not arbitrary later tokens.
The order is MAPSIZE, TileNum, SpriteNum, TileIdx, Pass, LinkIdx, then PalNum for
v1.1. Dimensions are signed integers, data row-major.00466EE0 allocates via
0076C3BF->__calloc_base, explicitly initializing eight bytes per cell.

TileNum writes LE16 at+4, TileIdx at+0, LinkIdx at+2, truncating parsed signed32
values to16 bits. SpriteNum writes the low four bits at byte+7. Pass writes its
low two bits to bits4/5 of byte+7, then duplicates bit4 to bit6.0046F630 extracts
bit6 for terrain passability. PalNum writes its low five bits at byte+6; v1.0
retains the proven calloc value. Other high bits remain initialized allocation
data, not guessed gameplay fields. Native closes after the final required
section, so trailing text is ignored. Missing/failed numeric reads are explicit
errors; unchecked native scanf/uninitialized-stack variants remain open.

## Actual source chain and retained replacement

CnStandaloneMapAsset preserves all eight-byte cells. CnSceneAssets now has a
shared physical MDT/MDL/model-ROM loader with an explicit native MBD flag:
initial loading supplies true, replacement false. CnOutdoorSceneResources retains
absence of MBD as absence, alongside actual MDT dimensions, models, ROM-derived
heights and plain resource identity. Identity parsing is shared with same-MDT
qualification. No new gameplay table, alternate client resource or guessed ID
is introduced.

prepare_standalone_switch accepts an exact ASCII camera request under the
explicit CN Data2/map root, rejects unqualified axes/root aliases/parent escape,
loads the actual flag0 profile, clamps against its MDT and reads all nine plain
MAP payloads. The supported compositor requires actual21x21 cells and applies
the current MDL/model-ROM declared object traversal. The privately constructed
candidate retains source paths, resource profile, nine decoded chunks and grid.

CnOutdoorWindow's assets overload only uses this loader for a different current
MDT. It preserves allocation labels, reloads every coordinate and binds the
prepared resource/grid to the current private cache identity/generation. The
same-resource MBD path still uses its existing retained bytes. On commit, the
cache generation is checked first; actual replacement resources and the full
standalone snapshot are retained before returning the conditional camera result.
Nothing applies actor camera state, commits player position, grants permission
or sends a packet. An old/replayed candidate cannot install a resource.

## Open continuation

Same-resource standalone rotation and valid-byte reuse still need integration;
the source currently reports absence rather than rereading valid files and
calling it native reuse. Missing/null/partial loads, other MAP versions/dimensions,
nonalphabet/high-byte axes, runtime ROM/frame changes and render reset callbacks
00473A20/0046C280 remain open. Actual camera/viewport/map34/prefix ownership,
WorldOwner, common scene/position/cache transaction, timing/pending/reset/full5D,
TW/CN publication, Application/listeners and all remaining gameplay paths remain.
Added opcode/phase bindings0, complete routes0, deployment0; whole-game
total/completed/percentage remain null. New immutable evidence preserves ten
native functions, thirteen strings, old source baselines and the flag0 discovery.
