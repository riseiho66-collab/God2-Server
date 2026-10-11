# Original participant controls

The same bootstrap VM executes constructor slice11F4C5..11F4EF with explicit
ESI=MANAGER. Original instructions copy28 coordinate pairs (224 bytes) from
VA571AA8 to BATTLE+A940604. All56 stores and complete bytes are checked.
The table ends exactly at ARENA: its final16 bytes are real coordinate data,
not an A5 guard. The baseline test now checks their original source bytes.

An initial run caught the already translated next instruction's stack push
at11F4EF. A strict code-stop hook now stops before it; write bounds were not
relaxed. A small regression pretranslates that block and checks stack retention.

`continue_participant_controls()` resumes the retained1116A9 stack to11177D.
Each original call/return34720,34F60,35860,34A50 and34B60 runs28 times.
Every creation argument matches its original coordinate pair. Native handles
0..27 populate BATTLE+A9DF6CC; all56 sprite handles are distinct and below4096.
Additional native calls:56x1AFE0,28x1B560,28x1E3D0 and28x1E560. The100 unused
control records, selector, character, catalog and selector neighbors survive.
Normal1112C0 still starts exactly once. No game callee/handle is substituted.

Selected CTest passes3/3 in219.73s: coordinate2/2 (0.22s), baseline21/21
(109.31s), participant controls5/5 (110.18s). Small independent tests pass2/2
in0.027s. This proves native control setup, not full1112C0 return or live battle.

Next81C20 resets OWNER+E2170 panels, currently `[08412170,08562DA4)` in this
offline fixture. It overlaps CHARACTER_ROOT `[08520000,0852469C)`. Relocate and
properly publish owner/UI storage before executing that bridge; do not bypass
the character guard. Original817C0..81895 contains the CFF68 mouse binding
writer, a static next target. Separate CHARACTER_UI publication also needs
reconciliation with OWNER. Later dependencies include AD880 and112130.

The latest owner instruction prioritizes actual original monster numeric data;
this battle frontier is recorded for resumption without redoing its tests.
C++/Lua runtime, production database, client files and networking are unchanged.
