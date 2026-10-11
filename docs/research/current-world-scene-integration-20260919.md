# Actor to native indoor scene integration

## Result and exact boundary

The C++ retained 2A frame is decoded by the original client codec, then passed
to `NativeWorldActor` and the following actual scene continuation in the SAME
VM. Original `1004F5..10078F` now runs continuously through map lookup, complete
CAN reading, real UI bounds update, scene-kind selection, indoor HMD/ROM loading
and the caller's coordinate projection. No native callee in that scene interval
is stubbed. Seven new tests passed in 59.670 seconds.

This is not the complete world initializer or live rendered-world acceptance.
The actor helper still explicitly omits its earlier resource-preload interval
`68290..68315`; inspection identifies `61AD0` as the double resource-bank
preloader, not the HMD scene loader. No successful return was substituted for
it. That remaining gap is separate from the scene continuation qualified here.
The next instruction after `10078F` leads into music selection/playback,
camera adjustment and further world/UI initialization, not a proven ready world.

Both legacy corpora were searched for `61AD0`, `619D0`, `616A0` and `5AA70`
in C++, headers, C# and Markdown, with no corresponding implementation found.
Existing current-map-atlas, scene-resolver, indoor-resource and actor evidence
was reused. No new spawn location or packet was inferred from a missing UI row.

## Sources and input

Pinned image SHA-256:
`149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
Addresses are hexadecimal RVAs relative to `400000`.

The current map catalog is `Data2/Patch/Comm/gamedata.csvZ`:

- compressed SHA-256 `70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731`
- decoded SHA-256 `75c3c37947a64b0917fbf8e546884d9bf893fe6a606d3e2b8f3b1857966b1815`
- input bound 1 MiB, decode bound 4 MiB; actual decoded size 2783008 bytes

The structured catalog parser establishes the 144-row section and validates
field bounds. Each actual source line, with CRLF-to-LF text-mode conversion,
goes through original `51BE0`, followed by original `59AD7..59D67` field writes.
An explicitly allocated zeroed 144*1A4 array and count supply the allocation
boundary; full `59A80` file iteration/calloc is not claimed. Unlike the earlier
map atlas test, native tokenization is not replaced with prefilled fields.
All 144 records, their strings/packed coordinates/dimensions/layer labels and
original `59D80` lookups are compared against independent source parsing.

CAN/HMD/ROM hashes and the plain-HMD fixture policy are unchanged from
`current-scene-resolution-20260919.md` and `current-indoor-resources-20260919.md`.
The compressed HMD is independently decoded and byte-compared with original
`1EC0` output before exposing its decoded plain file. The HMDZ temp-file path
remains outside this fixture. Actual groL.ROMZ decompression, parsing, native
resource/renderer-object allocation and model/grid construction all execute.

## Joined execution

1. Actual C++ `recovered-world-entry --dump 217` output passes through the pinned
   native decoder, then native common actor initialization with five real
   RoleDoll/mount resources. Actor position remains (17,13), area2/scene15/kind2.
2. `1004FC/10050C` perform the original area-base lookup and path construction.
   `12F550` executes against the same explicit virtual working directory as
   the role-resource oracle, not a replacement path resolver.
3. `100524 -> 6C620 -> 44F70` reads current Island01.can. All 36 records and
   all 130 indices match source bytes; scene15 selects record12.
4. **Actual `C3EA0` runs**, replacing the prior scene test's UI-helper stub.
   Area2/scene15 is absent from the 144-row UI catalog, while area2/scene0 exists.
   The original fallback stores base catalog dimensions **735,777** into
   UI+8AA30/+8AA34. These are UI bounds, not the indoor navigation grid size.
5. Kind2 takes `10069F..100747`, selecting `indoor/groceryl.hmd` from CAN.
   `6C5A0 -> 48300 -> 362F0 -> 37900` executes through actual return. The map
   manager is mode2/type11 with a real constructed indoor object and 31x31 grid.
   Role resource slots coexist with a separate scene ROM bank in the same VM.
6. The original caller at `10077A..10078A` increments grid y BEFORE `49330`.
   For (17,13), it therefore projects (17,14) to **(1240,540)**, the cell interior
   established by prior projection tests. The actual inverse returns (17,13).
   No manual +40/+20 patch or guessed screen coordinate is installed.

The scene control's small bridge object, RGB555 surface, null optional device
owner and fresh-load branch input `[ESP+38]=1` are explicit fixture inputs,
not a reconstructed live graphics/window environment. The actor's separate
renderer-owner pointer remains poison and is never dereferenced. There is no
frame presentation, actual camera or movement input in this oracle.

## Guards and verification

Additional adapters only implement bounded sprintf/CString path formatting,
allowlisted read-only virtual scene files, and the already qualified indoor
CRT/lock/rectangle semantics. No native UI helper, map resolver or loader is
patched. Code remains RX, private pages RW/NX, calls retain instruction/time
and stack/SEH checks. Paths outside the pinned file namespace fail closed.

Only the retained area2/scene15/kind2 subset is accepted. A second attempt is
rejected, including after an interrupted first attempt; resource reload and
rollback are not claimed. Bad lengths/selectors and changed catalog identity
are rejected before more native scene work. Bad CAN magic is exercised through
the real loader on a fresh map manager and produces zero, no populated CAN
tables and no leaked virtual file. Successful loads leave locks balanced and
FS:[0] restored; all model grids and the full navigation grid match source.

Run `python -B tests/research/test_current_world_scene.py -v`.
No runtime session state, C++/Lua ownership, spawn coordinate, packet body,
gameplay formula, inventory entitlement or quest reward is changed by this work.

## Combined regression and separate live startup

The combined preview/indoor/scene-resolver/actor run passed 28 tests in 149.209
seconds. Together with the seven new scene tests, this is 35 distinct tests.
Preview now exercises original action-frame stepping and wrap for the three
qualified head/face assets; it does not qualify device presentation or the
complete preview component loop. See current-preview-role-resources-20260919.md.

A separate fresh native run, `scene-integration-prefix-20260919-01`, launched
the existing working copy with MODE_COMPAT, zero-ui-prefix, warning-input-trace
and auto-pagefile-capacity, bounded to 60 seconds. The @oai/sky desktop tool
successfully observed the actual 800x600 client main menu. No desktop input,
login, server selection or world entry was performed. Screenshot observation
was live tool output, not a saved image artifact. The runner's own screenshot
capture remained disabled; it is not the source of this visual observation.

Runtime evidence independently records WSAStartup success, no 905/916 warning,
no connection and no transmitted packet. The terminal HARD_TIMEOUT was a
bounded main-menu wait, not a protocol rejection or a rendered-world success.
`pagefile-acceptance.json` qualifies only the existing scoped effective-capacity
compatibility: one result-buffer translation, real disk API call and restoration,
host pagefile settings unchanged. It does not establish a complete login prefix.

Post-run inspection found no God2.exe or god2-server.exe left running. Working
copy display.settings and ctserver.ini were restored to their original absence;
ddraw.ini matches original-config-2.bin. The strike state now records read-only
desktop observation availability without promoting its historical post-selection
frontier or claiming input qualification. Remaining world-entry, renderer and
gameplay boundaries above are unchanged.

## Embedded actor and scene tail follow-up

`current-embedded-world-20260919.md` now records original initialization at
`WORLD+1539683C`, the original caller pointer, and the scene/music/camera/
movement-ring/message tail through `100930`. The earlier graphics/UI prefix
and live device/client acceptance remain unqualified. No initialized actor
copy or forced branch substitutes for the real placement.

## Cold preload joined, 2026-09-19 follow-up

The earlier 682F1..68315 actor gap is now closed in the scene's default path.
`NativeWorldScene` uses `NativeColdWorldActor`, constructing the real double
bank directly at WORLD+AA364B8. It runs the original 681CF..68851 actor path
continuously, including full 61AD0 and its ENY/NPC catalogs and ROM loads.
Actual native NPC/enemy queries supply the initial scene inputs; they are not
replaced with null groups. The initial EnyName lookup legitimately returns null.

The three NPC resources occupy slots 0..2; five role/mount resources occupy
3..7. Actor mount slot is therefore 7, not the earlier slice fixture's 4.
The indoor loader adds its separate grol.romz, so nine native ROM parser inputs
are checked. Both catalog banks and their populated/unpopulated caches have
separate source-based tests. Detailed limits are recorded in
`current-world-resource-banks-20260919.md`.

Main scene suite: **8/8 passed in 99.872 seconds**. No loader success stub,
guessed NPC coordinate, spawn rule or packet substitution was added. The
fixed progress clock exercises two real increments without the timed repaint
branch; device/audio/camera/pool continuation after 10078F and live original
client/server world acceptance remain unqualified. C++/Lua ownership is unchanged.
