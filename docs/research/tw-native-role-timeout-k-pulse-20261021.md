# Taiwan native role timeout, row UI and cycle pulse (pass6)

Scope: static REA only. The client was not executed. This supplement corrects the
pass5 unresolved K-initialization lead; it does not recover original server turn,
pairing, damage, pet-growth or grant policy.

## Inputs and retained evidence

Original `C:/Users/risei/Desktop/God2/God2/God2.exe`, SHA256
`aaf0fae66e89c4547244304ecd8f4c2755746ffa6c9b9dfe68a0ff3fd2b4cd48`.
Evidence root (D):
`C:/Users/risei/.codex/artifact-archives/god2-server/20261021/native-material-rules-continuation-pass6/native-rules`.

Two private Ghidra sessions used analyst-only CALL seeds. The original 13 PE
sections were checked byte-identical; synthetic callers are not native callers.
The second analysis input SHA256 is
`e447ed88994f5716182c8d44a099d835080f608cb627d0002ac3ee1acf51020c`;
its provenance is `native-rules-constructors-seeded-v1-provenance.json`.
Both sessions have `close-rules-pass6-{a,b}.json` and matching
`helper-cleanup-rules-pass6-{a,b}.json`: target closed, owned CLI exit 0,
no forced CLI termination, no target execution.

## Two native commands can share one logical flush

Let B be the CWar owner. A is DWORD `B+A9E9C38`, secondary control is DWORD
`B+A9E9C3C`, and W is DWORD `B+A9E9C34`. `5156E0` returns BYTE `B+52` only
when A is zero and secondary control is nonzero; all other cases return BYTE
`B+51`, including both control flags zero. It has no actor HP test.

`513080` computes the signed remaining seconds at `B+A9E9C18` from the configured
timer and elapsed `timeGetTime`, then calls `5129C0`. For negative remaining time,
`5129C0` clamps it to zero. If `B+A9E9C4C != 0`, timeout-once DWORD
`B+A9E9C54 == 0`, and W is zero, it independently does the following in order:

1. A nonzero: `5156E0`, then `518E50(2, actor, 1, B+44C)` at `512E2A`.
2. Secondary control still nonzero: `5156E0`, then the same builder at `512E76`.
3. Set timeout-once to one.

`518E50` consumes A first; otherwise it consumes secondary control. Thus when
both are granted, the first command uses primary BYTE `B+51` and side flag 0,
the second uses secondary BYTE `B+52` and side flag 1. When only secondary is
granted, the first branch is skipped and the second uses side flag 1. Neither
the role selector nor this timeout branch makes a dead-primary HP decision;
the client control flags do not establish the original server's death policy.

For action2 the builder clears the 14-byte target buffer, writes the current
`5156E0` result into its first BYTE, and forces target count to one. The result
is a one-hot mask for that command's actual actor, not a fixed bit-zero mask.
The 16-byte C35 body contains actor BYTE, action BYTE, side BYTE, opaque BYTE,
two target WORDs, shared context DWORD from `B+3C`, and an opaque DWORD. Action2
does not initialize that final local DWORD; receiver validation cannot require
zero or infer an authority value from it. The opaque BYTE is also not a
producer-owned zero.

`4132E0(35, body, 10)` appends 17 bytes (record ID plus body) to the logical
outgoing buffer. It calls `413370` only if `buffer_size + 17 > A00`; it does not
flush after each command. `413370` sends the nonempty buffer and resets its size.
This proves a legitimate combined logical payload, not a particular TCP segment.

Actual `515770` loop order, corroborated by assembly:

| Call site | Operation |
| --- | --- |
| `5159C5` | `513080`, including its `5129C0` timeout tail |
| `5159CD` | `514B70` keyboard handlers |
| `5159F3` | conditional `514890` automatic-input policy |
| `515A4C` | `5140C0` queued incoming battle effects |
| `515AD8` | conditional automatic `518E50(0B, B51, B45C, B44C)` |
| `515AFA` | ordinary end-of-loop `413370` flush |

The timeout pair can therefore precede another automatic 0B in the same flush
when that separate cycle gate is satisfied. Action2 itself does not mark
0B-sent. When the first timeout command leaves secondary control, its cleanup
calls `512620`, which sets `B+45C = 1` and clears the targets. The second timeout
command writes the secondary actor into those targets; its cleanup has no
remaining secondary control and does not call `512620` again. Consequently the
following automatic 0B can have actor `B+51`, side flag 0 and a secondary-actor
one-hot target mask. An unconditional zero-mask requirement for automatic 0B
would reject this native producer path. This is conditional reachability, not
a claim that every timeout generates 0B.

Implementable server contract: preflight the complete original batch; allow
the exact same-epoch primary/secondary timeout pair under the respective real
grants, then serialize the two authoritative effects. A coalesced 0B is input
from before either newly published effect and cannot certify either new edge.
Transport completion is not renderer completion; the native command has no
turn nonce. Preserve this limitation in the explicitly CUSTOM progress policy.

Evidence: `timeout-owner-ui-alias-pass6-v6.json` (5129C0),
`assembly-timeout-double-command-pass6-v7.json`
(`ev_f93929ef64d73ff4d8d2361376b30c3e8f274d865e73b818a678e8e8bd6fb6da`),
`role-timeout-and-multi-flush-pass6-v5.json` (518E50,5156E0),
`assembly-builder-exact-widths-pass6-v8.json`,
`flush-and-material-consumers-pass6-v7.json` (4132E0,413370),
`assembly-battle-loop-flush-pass6-v6.json`,
`assembly-ui-timeout-callsite-pass6-v8.json`,
`level-consumer-and-flush-path-pass6-v9.json`, and
`counter-and-targetcount-writers-pass6-v16.json`
(`ev_e32f1d366728e03b25039968043aaea481a2dfc771bc55abf676f37de7ae4a30`).

## K is an actual manager pulse, not an inferred entry-context mode

`5109D0` constructs the battle manager at `M = B+144938` (assembly `510AC1`).
Therefore manager DWORD `M+2E4` equals the previously named K at `B+144C1C`.
The nearby manager DWORD `M+2E0` is a persistent mode queried by `52AED0`.

`52AEA0(value)` writes both `M+2E0 = value` and `M+2E4 = value`. When value is
nonzero it additionally writes BYTE `M+30C = FF` and BYTE `M+309 = 0`.
The concrete direct native callers are:

| Caller | Condition and write |
| --- | --- |
| `51FC40` at `51FD32` | manager reset; `52AEA0(1)` |
| `516740` at `516779` | first effect of a cycle (`B+A9DF6B8 == 0`); set it to1, then `52AEA0(0)` |
| `516AE0` at `516B1C` | corresponding first S83 cycle; same clear-to-zero transition |
| `5140C0` at `5142DD` | controls28 zero, battleactive `A9DF6C0` nonzero, gate `A9EA4C4` nonzero, incoming queue empty, terminal50 zero; `52AEA0(1)` |

`515770` reads K at `515A61`; when nonzero it clears only K at `515A69`, leaving
the persistent mode unchanged. It then allows 0B if signed wrapped
`counter64 - counter68 >= 0`, or counter64 equals FFFFFFFF, and sent44 is zero.
When K is zero it requires counter64 exactly equals counter68, sent44 zero and
cycle48 equals1. This establishes initialization/reset1 → first-effect0 →
idle/no-controls1 → loop consumes K0. It does not establish original server
counter generation or make context_b a K selector.

Literal-displacement scans were complete over the loaded image for
`B+A9E9C64/68/6C` and K. They do not exclude a computed-address alias. Fresh
`5112C0` assembly initializes counter64 to FFFFFFFF at `5117EE`.
`518A90` receives the S88 DWORD at logical1: on initial counter64FFFFFFFF it
copies that DWORD to64 and68; on later receptions it normally updates64 only.
If latch6C is exactly1 it clears the latch and skips that update once. The
direct literal6C writes recovered in this pass are zero in516740,516AE0 and
that receiver; no set-to1 was found by this literal scan. Counter68's direct
literal writer is the initial S88 branch. Client acceptance of a fixed counter
does not prove the original server sent a fixed value or counted turns.

Evidence: `seeded-constructors-and-k-pass6-v10.json`,
`assembly-war-constructor-offsets-pass6-v11.json`,
`manager-k-setter-pass6-v13.json`
(`ev_aa16401bb26e7f036c791b65df394324b9890887e6546cca167af08cdb58cfb49`),
`incoming-manager-k-setter-pass6-v13.json`,
`k-mode-and-cycle-writers-pass6-v14.json`
(`ev_247d72fcc0f6197762baa8a19bb97c12a9e670ee5bff1a087b014b4237061151`),
`assembly-k-pulse-setter-pass6-v14.json`, `counter*-displacements-pass6-v15.json`,
`assembly-counter-init-pass6-v17.json`, and
`assembly-k-queue-idle-pulse-pass6-v17.json`.

## Row UI and material-consumer boundary

The secondary UI is not missing action9: `50FF00` builds its buttons and the
actual WORD map at59C424 is `[1,2,3,6,9]`. `5103B0` hit-test callback selects
that map and sets pending action. The primary callback `50FE40` uses
button-index+1. `513080` dispatches selected9 through5127C0 to518E50. The
observed construction/callback/role selection does not test pet HP or require
two live actors. This bounded trace is not proof that every generic UI
visibility/disabled state or original server empty-pair rule is recovered.
Existing CUSTOM formation policy must remain explicit until separately proved.

`515C90` is the S1C consumer, directly called by5140C0. It copies logical2 level,
WORD3 identity, WORD5 variant/render fields, WORD7 species/reference, logical9..40
name/opaque bytes and DWORD41 status into its normalized descriptor. A nonzero
status bit0 collapses the received status to1. For wire variant4000, its two
variant bits move from wire bits13..14 to normalized bits14..15, yielding8000.
`52CCD0`'s normalized8000 branch formats the descriptor's high-byte level for
display and resolves species from descriptor+0C (wireWORD7). This consumer
does not derive identity, opaque name or status from E3/FB combat statistics.

Safe explicit CUSTOM material projection can use authoritative saved current/
maximum HP/MP and level to replace only their known fields while pinning every
other template byte/source/metadata. This does not establish a growth formula,
or that untraced combat fields can be excluded from a full material key.

There is a local17-byte appearance builder inside515C90: calls to5177C0 at
515F05 and516112 construct appearance from45A0A0 definitions or fixed5E records.
These are definition/monster paths, not proved WORLD DA or active44 E3/FB
converters. Other direct5177C0 calls are the5140C0 incoming queue path. Thus
the bounded caller evidence does not recover an original server builder for
WORLD2A/DA→86/4 or active44→1C. It must not reclassify CUSTOM0105 byte copies as
native server provenance.

Evidence: `row9-secondary-action-map-pass6-v3.json`,
`row-ui-callback-alias-pass6-v4.json`, `timeout-owner-ui-alias-pass6-v6.json`,
`flush-and-material-consumers-pass6-v7.json`
(`ev_bbc8d5dc0024ffbd58671a43ab85a0ec5566426e476b0afeb085e84cad9ab83a`),
`incoming-1c-material-consumer-pass6-v8.json`,
`incoming-864-material-consumer-pass6-v8.json`, and
`level-consumer-and-flush-path-pass6-v9.json`
(`ev_3293aa043d645eedc40d767cb312dd8b4ad92ac2b3f38702ea23a95e1e366968`).

## Limits and next traces

The initial analysis image did not identify5109D0,5110E0 or507FC0; these failed
items remain in v2/v6 receipts. A new, distinct seeded input resolved them;
the same failed request was not retried unchanged. One mistaken510FE4 request
is retained in v5; the intended50FE40 request succeeded in v6.

Remaining original rules: empty/dead primary-pet swap authority; server initial
pair assignment and fees; actual server S88 counter producer; any computed
alias setting latch6C; complete original material-generation formulas. Next
useful static trace is a precise alias/write analysis for6C and generic UI
button-state writers, not another unchanged decompile of these consumers.
Runtime timing and compatibility acceptance remain unperformed under PHASE1.

Reusable CLI helper: `D/rea-static-worker-v1.mjs`; invoke with the existing
Node runtime, absolute analysis input, a unique evidence directory and tag.
It launches the installed `rea.mjs --mcp` with the existing Ghidra path, accepts
one JSON tool request per stdin line, writes immutable full evidence, and
`{"close":true}` closes the target and owned helper. This helper does not
change MCP registration or install tools.
