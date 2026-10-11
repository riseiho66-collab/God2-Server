# CN computed receiver-reference frontier, 2026-10-07

Previous goal turn was progress: native path completion and distinct5D consumer
source sealed under catalog28. This round returns to the two unresolved native
receiver phases to extend actual static reachability beyond earlier direct/raw
literal scans. It implements a new bounded reconstruction tool and seals its
primary inputs/results. There is no C++ gameplay change or newly hosted route.

## Earlier evidence remains distinct

Pinned CN PE SHA256:
`582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8`.
0047DE70..0047E05A and004812B0..0048138E remain phase-unresolved. The immutable
earlier cn-receiver-reachability-agent-01 findings already examined exact and
mid-function E8/E9/EB/Jcc transfers, unaligned VA/RVA literal candidates and
adjacent padding. No outside direct entry was established. Literal fragments,
matching prologues, shared mapper/message wording and same opcodes did not prove
selector ownership or dead code. This work does not repeat/promote those scans.

## New bounded constant/indirect analysis

`cn_computed_receiver_references.py` reads the pinned PE and exact native
functions.tsv. It decodes each available recovered function span independently
with detailed native x86 operands, bounded to1MiB per span. It tracks known
32-bit register constants through MOV, LEA with known base/index, ADD/SUB,
XOR/AND/OR, shifts/rotates, INC/DEC/NOT/NEG, three-operand IMUL and explicit
PUSH/POP. Arithmetic retains native32-bit wrapping; partial/unmodeled writes
invalidate register facts. Conditional branches, jumps, calls, returns and
interrupts terminate facts; there is no guessed join or interprocedural state.

The analysis records computed constants inside either helper extent, known
register-indirect transfers and constant push/RET candidates, with exact native
instruction bytes and the derivation that produced each candidate. Target
instruction-boundary membership is tracked separately. Statistics distinguish
all metadata spans, unavailable/oversized/incompletely decoded spans, decoded
bytes, indirect sites and constant-resolved indirect sites. Exact results are
in computed-reference-scan.json, not inferred from a generic progress percentage.

There is no assumption that arbitrary loaded memory equals bytes in the PE.
Encoded pointer tables, mutable memory, relocations, loader changes, runtime
modules, condition-specific CFG joins and obfuscated island closure remain open.
Recovered function metadata can itself omit code; it is a bounded analysis input,
not proof of complete program coverage. Candidate derivation is a static
instruction relation, not runtime acceptance or a confirmed connection phase.

## Owner/phase requirements remain

0047DE70's active+2CB8 owner polls0047D8D0; its1E mapper can return0 and continue,
02 consumes status and flags, and timeout210 is a deletion-related semantic lead.
It still has no proved current producer/selector chain.004812B0's active owner
waits for a received07 payload74; inactive zero return and unexpected opcode
with retained+2CC0 cannot be mistaken for successful server selection. This scan
does not silently pair either helper with a known request or merge them into
already-reachable handlers.

A computed-address or indirect-transfer candidate must next be connected to
actual ECX owner construction/registration, predecessor selector state and
current network receive lifetime. No result alone proves a new live phase. An
empty candidate set narrows this specified straight-line domain only; it does
not prove either receiver unreachable or exhaust the whole-game denominator.

## Accounting and execution

One new research tool and document, no new/modified C++ gameplay source, no
opcode, partial owner chain, newly confirmed phase or complete route counted.
Prior raw findings and complete pinned helper extents are retained in a separate
immutable artifact. The next catalog/report retains unresolved phases rather
than inflating endpoint/route totals. Full-game total/percentage remain unknown.
Only static native/source accounting is performed: no build, tests, asset
loaders, Lua, game/server/client execution, production DB, deployment, client,
font or text-conversion change.
