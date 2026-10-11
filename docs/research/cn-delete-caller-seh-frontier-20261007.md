# CN deletion higher callers, UI switches and CRT startup roots

PHASE1 primary file-only research; no native/DLL/emulation/build/test/SQL execution or deployment. Native levels unchanged. Pinned CN SHA256 582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8.

Actual rel32 call chain: CRT00749A75 at00749B68 ->00405A60 at00405F25 ->0044A470 at0044A599/0044A84E ->00446BD0 at004483E4 ->0047E960. Separate0043DBA0 at0043DBD4 also calls deletion; no direct caller found in this bounded target census does not prove it is dead or never used indirectly. Byte matches and entry-rooted instruction alignment are separate.

Four primary guarded switch tables contain48 entries. UI state index26 selects00448383 and reaches the deletion call. The expansion adds1142 entry-rooted instruction sites; these are code coverage, not packet/route counts. Truncation, exception transfers and unqualified jumps remain explicit.

Higher0044A470 registers007C76FF throughFS:[0]. Adapter usesFuncInfo00857C2C: magic19930522, maxState3, try-count0, ESType0, EHflags1. Three unwind actions are cleanup, not an EIP skip/repair. Prior local UI00857958 and CRT top-level filter evidence are retained unchanged.

CRT startup has a different SEH4 frame:00749A75 passesScopeTable0087CED8 to00749E10, which installs007529C0 and XORs the table with the actual cookie. Its table names filter00749B96 and handler00749BAA. Filter loads actual exception code/pointers and calls0078A0E0. Negative filter returns disposition0 in the actual handler; positive filter unwinds/transfers to the handler. The unmanaged handler path calls0078A589, not a deletion wrapper resumption. Actual per-thread signal actions can invoke indirect callbacks; their loaded values and context changes are not qualified by file-only decoding. No native1E result or whole-program absence of repair is claimed.

The original startup metadata span ends before filter/handler/epilogue. Primary ScopeTable pointers and normal branch targets provide additional roots; the bounded recovered spans are retained separately without overwriting metadata size or older snapshots.

Before WinMain, __initterm_e consumes the10-entry C range and __initterm the207-entry C++ range: 215 nonzero distinct callback roots, 214 without an exact functions.tsv entry. A zero file TLS callback is therefore not complete startup coverage. Each actual pointer seed has a primary bounded CFG and open frontier; bounds use next declared entry/seed, section backing and4096-byte budget, not an assumed exact function end. Calls are not followed.

Next follow those actual initializer callees and indirect/dynamic exception/code-patch registration, particularly the first CRT initializer and referenced helpers. These roots are not new opcodes or completed native gameplay. Existing common CAS/auth/native decoder behavior remains unchanged; only the decoder provenance comment links this new frontier. TW/CN permission/guild/replay/full02/03/hosting and CN1E remain open.

New owner chains0, phase source bindings0, complete bidirectional routes0. Whole-game denominator and completion percentage remain null.
