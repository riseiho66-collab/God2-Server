# Current Taiwan native three-channel selection evidence

Owner requirement: three selectable channels after server selection, with
switching. This note qualifies the original login selection UI and routing;
it does not claim three hosted worlds or in-world switching are complete.

Current original God2.exe SHA256:
`aaf0fae66e89c4547244304ecd8f4c2755746ffa6c9b9dfe68a0ff3fd2b4cd48`.
All addresses below are VAs. REA/Ghidra statically decompiled ten procedures
in three successful batches, all targets closed:

- v6:404DA0,413E10,4147D0;
  `ev_f0afccfe302d14f44b758023367fcfaec83c3dbeabbabc7571c1c8fad1f7e82b`.
- v7:4068E0,406FB0,4070B0,407A10;
  `ev_aa37c5b3599c38fa1d9e34cbc8dfcd43963d9fc4c35edfb1edbc76232e45ac5d`.
- v8:406E00,407440,407B00;
  `ev_673afea822042cc719cdaa2b554aa2366def9843a574f91de80168492f67c5bd`.

Raw decompilation, assembly, analysis-image provenance and close receipts are
under C:/Users/risei/.codex/artifact-archives/god2-server/20261019/entry-direction-round485.
Analysis-only seed callers are synthetic, not original call provenance. All13
original PE sections, bytes and section headers/mappings are compared with the
current original. No native function, client, codec or game database ran.

## Three independent selection inputs

407A10 initializes subgroup UI through407440 with the selected group WORD
Main+8F4 and subgroup WORD Main+B40.407461 calls411AB0 for the configured
count;4074B8 calls411AD0 for each configured name. The existing separately
recovered configuration source retains ordered physical slots and their real
count. This count is not supplied by the received mask or number of05 frames.
The new three-channel path still needs exactly three real configured slots;
no current compressed Data3 configuration was decoded or changed this round.

4074CF reads the availability WORD Main+8E+14h*group.4074D7 loads1,
4074DC shifts by subgroup ordinal and4074DE tests the bit. A clear bit takes
4074E6/4074F0 to disable that row; a set bit reaches4075F9/407602 to enable
it.407637/40763E bound this UI loop to eight rows. Consequently mask0007
enables rows0,1,2; mask0003 enables only0,1. This is a bitmask, not a count.
Generic wire_three_channels still preserves supplied opaque04 bytes exactly;
wire_three_available_channels explicitly emits low mask7/high mask0. Neither
producer invents configuration, binds a socket or authorizes a character.

406E00 builds the server-group picker.406E3B..406E49 require an ordinal
below the configured group total and a nonzero mask. Its loop406EAA scans
only physical group ordinals0..9.406E95 stores the actual group ordinal;
406EF9/406F02 map a compressed visible row back through50CFA0. The generic
receive table may contain64 groups; that does not make all64 visible here.
The explicit available-channel producer refuses groups outside this picker.

The selected connection still needs an actual destination.413E10 consumes
04/05/06, preserving the physical current-group endpoint counter across05
rows. Three subgroup records therefore use(k,j)=(0,0),(1,1),(2,2), each with
route ordinal0.407488 begins reading status at table+C5;407631 advances
by290h, consistent with260h*k+30h*j for this diagonal layout. Registered
regression source replays those physical offsets and resolves three distinct
endpoints using synthetic complete07 records with explicit matching keys.
Synthetic test keys do not replace real character snapshot byte32 at runtime.

## Selection and status boundaries

The05 byte at payload+2 is the status used in407519..40759E to choose four
localized label categories:0..80,81..90,91..93,94..255. This bounded trace
does not recover original load computation, admission limits or the full text
catalog. Regardless of category, the set-mask path enables the row. Do not
turn a label category into character-transfer or permission authority.

407B10/407B1A store the selected subgroup row in Main+B40. Event flag4
requests state12h at407B25..407B2D.404DA0 state12h calls40B490;
the existing bounded caller sends the low UI bytes through4147D0's native
A6 builder and awaits07. This is the original login selection route. It
does not establish the unknown in-world switch action or its save/exit/retry
contract. That native trace, full custody and final current-client acceptance
remain open; see docs/THREE_CHANNEL_PLAN_20261019.md.

The implementation remains source only. No builds, tests, runtime activation,
SQL, codec execution, client acceptance or deployment occurred.
