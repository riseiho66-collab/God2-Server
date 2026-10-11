# CN native deletion1E: primary exception and code-patch frontier

File-only PHASE1 research. No native/DLL/instruction execution, builds, tests,
database access or deployment. Input is pinned CN PE32 SHA256
`582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8`.
This changes the next recovery action by locating the actual UI EH registration,
its zero catch table, the bounded CRT filter and native code-patch caller targets.
It does not recover whole-program exception closure or the complete1E result.

## Actual local UI exception chain

The retained00446BD0 prologue pushes007C7472 at00446BD5 and installs its current
record inFS:[0] at00446BF7. Its adapter checks two cookies, then sets EAX to
00857958 and jumps0074F0F0. That frame wrapper passes the FuncInfo pointer to
007538BC. The primary nine DWORDs are magic19930522, maxState6, unwind map85797C,
try-count0, try-map0, IP-state count/map0, ESType list0 and EHflags1.
The six unwind actions are cleanup metadata, not six packet/exception outcomes.

Actual007538BC reads FuncInfo+0C/+1C/+20 to enter0075338F. This UI frame's empty
try/ESType maps and flag4 clear do not enter that handler search on non-unwinding
records. The function returns1. Its unwind branch may call cleanup; cleanup
does not prove resumption at47EB63. No repaired EIP is supplied by this local
chain. This is a bounded statement about the registered UI frame's data/consumer,
not proof that every caller or dynamically installed handler rejects the fault.

0074A361 passes0074A370 to the declared SetUnhandledExceptionFilter slot7EB360.
The64-byte filter checks E06D7363,3 exception parameters and C++ magic values;
otherwise it returns EAX0. The matching C++ branch calls0078C429; the bounded
filter does not rewrite an instruction pointer. Clearing/report-fault CRT calls
and `.islands` reference candidates remain distinct from custom repair handlers.
An on-disk IAT value is not an observed loaded API pointer.

The PE file TLS directory declares callback table7EC28C whose first DWORD is0.
Exception and load-config directory headers are0. These facts are not absence
proof for runtime VEH/SEH, dynamically resolved APIs, injected modules or loaded
code changes. Native19/1E still must not use a guessed skip over DB10C0F143.

## Code-modification provenance

Primary00401170 flushes instruction cache then requests protection40, saving
old protection;004011F0 flushes and restores it.004012E0 uses a relocated prefix
and detour writer00401610. This demonstrates a code-modification source exists,
but does not prove it modifies deletion. The bounded005419C0 actual arguments
pair541A90/541950,541AB0/541960,541A50/541890,541A70/5418F0. The four target
resolvers respectively return keybd_event,mouse_event,PostMessageA,PostMessageW.
Other runtime/indirect/higher-caller mutation sources remain open. Existing
native input/IME behavior is neither patched nor rewritten in this round.

The delivery scans exact FF15/FF25 references to six relevant declared API names
within file-backed PE sections, stores metadata owners and separately qualifies
entry-rooted bounded CFG instruction alignment. Byte matches, shared body copies
and thunk references do not prove global reachability or a gameplay denominator.
Decode gaps remain explicit; an unaligned/off-metadata hit is not dead code.

## Web peer receipt

Latest integration contract and relocation source/report are retained by SHA256.
The peer qualified TW445190/CN470C90 ESI-to-EAX return: a partial slot failure
does not mean the outer loader returned0. Slot reuse TW4469F0/CN46D460 applies X
before Y. Reported450 comparisons,116 static relocations,460404 cells and22
partial neighborhoods are frontend-only observations, not server tests or routes.
Missing slots preserve prior bytes; fresh world/binding and immutable publication
remain necessary. Actual raster-cache commit and production camera/walk calls
are pending; renderReady=false, CN resources unavailable, no TW substitution.
Current movement identity/connected/worldActive/source/binding checks and display
preference separation are retained. Four native WS paths/wire are unchanged.
Peer point-in-time capacity data are reported evidence, not a fresh measurement.

## Accounting / next action

No new phase/opcode source binding, owner chain or complete native bidirectional
route. Previous conditional19 common-CAS/02 source remains intact and unhosted.
Next trace real higher-caller or dynamic exception/code mutation registration,
native rule/online/guild/replay receipts and actual02/03 issuance. Neither local
EH metadata nor control8 authorizes saved-character removal. Whole-game
phase/state/variant/indirect/deferred denominator and completion percent remain
unknown/null. Native level fields, limits and curves are unchanged.
