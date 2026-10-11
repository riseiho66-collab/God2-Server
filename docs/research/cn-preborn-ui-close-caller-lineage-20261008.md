# CN local preborn UI close callers and unphased84 boundary

Round `20261008-cn-preborn-ui-close-caller-lineage`; PHASE1 file/source only.
Previous138 was progress: actual choice consumers and common handoff sealed.
Saved152 current files first; retain prior212-file seal and all earlier evidence.

## Two different primary helpers

Pinned CN PE SHA256
`582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8`.
`005342B0` (43B) is a complete15-site local normal CFG. It reads the WORD
at offset0 of the object pointed to by `[actual_this+430AC]`, then calls
`00481440` at005342D2 with opcode84, body pointer and body length2. Its
logical record has3 bytes. **WORD0 means offset0, not the literal value zero.**
There is no proved request/reply pairing, native root, connection stage or server
operation. The exact operand differs from the object+90 family WORD in138.

`005342E0` (56B) is a different local GUI helper. It retains scene this in ESI,
reads signed WORD handle `[scene+1C8500]`, requires handle>=0 and BYTE GUI-slot
flags at `scene+78074+handle*2A08` to have20 set. It sets ECX=scene+7785C,
calls0044E7F0 with that handle, restores the same scene ECX, then **tail-jumps**
to004A89A0 at00534311. No direct native84 emission exists in this wrapper.
No absence of sends in arbitrary descendant callbacks is claimed.

`0044E7F0` (317B) uses its own GUI-root pointer and slot+818; with caller
scene+7785C this is the exact same scene+78074 table. Where flags&2 and&20
are set, it writes `(oldFlags&3)|4`, updates dirty rectangles and cleans GUI
items. The native wrapper checks20; the helper independently checks2.
These are local renderer/UI operands, not server ownership or a wire cancel.

`004A89A0` is only14 metadata bytes: it compares `[scene+81CB]` to0,
returns at004A89AD for zero, otherwise branches to **004A8470**. The
decompiler expands the tail target into its pseudo-body; neighboring
004A89B0 is a different function and is not the branch target. The actual
273B004A8470 source/normal CFG is retained. Its declared body updates existing
chat/UI presentation through helpers; frozen chat/client source is not changed.
Both out-of-metadata tail boundaries remain explicit rather than being labeled
complete local CFGs. No native/API invocation or runtime behavior was observed.

## Actual callers and searches

Nine primary E8 callsites target005342E0:
0049798E,004C4174,004CD9CD,004CDA9B,004CFCC3,004CFDCD,
004FEA43,00508A23,00534877. Each site is checked as an entry-rooted decoded
instruction in its own primary metadata, or in prior129's qualified extended
534810 CFG. Other GUI-open helpers and the preborn item7 event call this local
wrapper; it is not an84 sender wrapper.534810 requires event bit1, clear bit2
and signed item7 on that branch, then returns0. Timing across all roots is open.

Full file-backed-section E8/E9 syntactic target scanning adds all sections and
relative tail candidates to the prior130 bounded search. There are zero such
candidates to5342B0 and nine to5342E0. Those candidate sets are recorded before
CFG qualification; raw bytes alone are not calls. Literal VA/RVA searches are
also retained, including any unqualified aliases/data candidates. Empty direct
searches **do not prove global unreachability**. Indirect/computed/repaired-load
sources, original root/phase and native subject-to-common mapping stay open.

## Source and accounting

Added `CnPrebornSubjectRequest`, a standalone exact3-byte84 reader retaining
the complete WORD object-start operand. It is explicitly **unphased format
only**. No WORLD parser/handler, guessed cancel,84->A0 reply, permission,
table, rule or success reply was added. It remains unavailable as a gameplay
route until actual native call/root/stage and common authority are qualified.

This M1 source/caller-boundary increment retains primary metadata, bytes, CFGs,
direct-call operands and scoped search completeness. It does not count local
UI close contexts as packets or add a new native phase. Existing common
preborn/window/choice source and all frozen C++/Lua behavior are unchanged.

New standalone unphased format1, qualified local-close direct contexts9;
new opcode/phase associations/network owner/complete routes0. Whole-game
denominator/completed/percentage remain null. Continue the native indirect84
root and actual common authority/providers/rows/rules/save/replay/Application,
full TW/CN/PC/web/WSS/all gameplay/numeric64/coin99999999999/stack99 and later
comprehensive build/test/repair/recoverable release. No build/test/native/C++/
Lua/API/client/server execution, DB access/migration or deployment. Accounts,
saves, auth, chat, IME, portraits, native fonts/text conversion, levels, clients
and historical baselines remain unchanged.
