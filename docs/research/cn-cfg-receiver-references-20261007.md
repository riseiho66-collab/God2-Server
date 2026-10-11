# CN entry-rooted receiver reference frontier, 2026-10-07

The previous work round saved common character-offer invalidation source. The
owner's subsequent level acknowledgement preserves every native level field,
display, progression cap and curve. No level change is included here.

This round extends the earlier straight-line computed-reference scan rather
than repeating its empty candidate set as new recovery. The pinned PE is read
as a file using unique section backing, with functions.tsv as bounded metadata.
An entry-rooted worklist decodes successors at direct branch targets, including
instructions after an invalid byte in the earlier linear disassembly prefix.
Each conditional branch propagates to both successors without assuming flags
or branch feasibility. Direct jumps propagate only to their target. A join
retains a register or explicit stack constant only when predecessor values
agree; loops converge conservatively. Only converged states produce candidates.

Full-register arithmetic wraps at32 bits. Known subregister reads, MOVZX/MOVSX,
signed arithmetic shift and register XCHG supplement the older model. Partial
or unmodelled writes invalidate full-register facts. Calls invalidate all facts;
no calling convention, callee preservation or returned constant is assumed.
Explicit native stack values are bounded to32 entries; stack writes and explicit
ESP mutation invalidate them. Memory loads, including on-disk IAT DWORDs, are
never treated as loaded callable addresses. Direct branches leaving metadata,
indirect branches, invalid decode and resource-budget exhaustion remain explicit
frontiers. This is neither a whole-program CFG nor a runtime reachability proof.

The initial model draft is retained separately. Source review identified that
POP ESP can pivot the native stack, rather than merely pop one tracked cell;
the adopted model explicitly invalidates remaining stack facts. Implicit string
stores also invalidate stack facts. The current findings come from that revised
model; prior draft counts are not substituted for current evidence.

The artifact retains findings, exact candidate derivations, entry-rooted edges
and native spans newly decoded beyond the prior linear prefix. These spans and
instruction sites are research units, never new packets or complete routes.
An empty candidate set closes only this bounded analysis domain. It cannot
prove0047DE70 or004812B0 dead, assign their network phase, or join either to a
known C2S request solely because its opcode or message wording matches.

Next recover actual pointer registration or upstream owner construction from
encoded/memory/interprocedural paths beyond this domain. Preserve the existing
direct/raw/straight-line findings separately. All request/handler/transaction/
storage/reply/consumer gaps remain qualified in the current ledger. Whole-game
route total and completion percentage remain null. No build, tests, client,
server, Lua, resource-loader execution, production DB or deployment occurs.
