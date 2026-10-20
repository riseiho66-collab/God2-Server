# Native round producer follow-up: pass8

Status: PHASE1 SOURCE_STATIC_ONLY. This lane performed static REA and source
reading only. No build, test, target/game, VM, codec, game SQL/schema or deploy
ran. No production source changed. A client accepting server-supplied order is
not an original server initiative, speed or round-counter formula.

## Input, reuse and new questions

Current Taiwan original God2.exe remains SHA256
`aaf0fae66e89c4547244304ecd8f4c2755746ffa6c9b9dfe68a0ff3fd2b4cd48`.
The already closed pass7 independent analysis input is reused in place:
`C:/Users/risei/.codex/artifact-archives/god2-server/20261021/native-scheduling-material-generation-pass7/native-round/round-independent-pass7.analysis-pe.bin`,
SHA256 `e447ed88994f5716182c8d44a099d835080f608cb627d0002ac3ee1acf51020c`.
Pass7's section-provenance receipt establishes that all13 original PE sections
are identical. The analyst CALL-seed section is not a native caller. No new
binary copy, installation or configuration repair was made.

New evidence root D is
`C:/Users/risei/.codex/artifact-archives/god2-server/20261021/native-scheduling-material-generation-pass8/native-round`.
One existing CLI/helper session, `round-pass8-a`, was opened and closed. The
close and helper-cleanup receipts retain natural CLI exit0; the parent PTY
also exited0. No target was executed.

This pass did not repeat pass7's269 displacement search or the S88 consumer.
It follows two new questions: what actually feeds the battle receive queue,
and whether the actor-arena/resource reset is a computed bulk writer to latchL.
All addresses, offsets, counts prefixed `0x` are hexadecimal; other counts are
decimal. B denotes the CWar owner, M=B+0x144938, Q=B+0xA9EA4B0, and
L=B+0xA9E9C6C. The same trailing offset in different owners is not the same field.

## Incoming order reaches the queue without a local initiative sort

The new direct-caller trace for `0x51D4E0` finds `0x519370` and the analyst
seed only. `0x519370` is called by the actual CWar loop `0x515770`; the latter's
body is reused from current-aaf pass5 evidence rather than reanalysed.

| Actual path | Source and operation |
| --- | --- |
| `0x413420` | Assembles one complete incoming logical record in network-owner `+0x2CC4`, advancing its current byte count. Fixed or variable size is selected through `0x415840`; it is not an actor speed lookup. |
| `0x412520 -> 0x410AF0` | Reads the next byte from the existing network receive buffer. `0x410AF0` copies an available prefix from owner `+0xC10+readCursor` and advances that cursor; it does not compare actors or sort records. This is not a trace of the upstream socket/decrypt implementation. |
| `0x519398 / 0x5193BD` | The battle loop checks record readiness, obtains the pointer through `0x413650`, then dispatches the opcode. |
| `0x5195B5..0x5195C2` | Opcodes1C,38,83,84,85,86,87,88 call `0x415840` for length and append the same record pointer/length through `0x51D4E0` with ECX=Q. |
| `0x5195D0..0x5195E2` | Opcode89 takes the same append route and then sets the local stop-draining flag. This does not establish an animation acknowledgement. |
| `0x5198A6..0x5198B7` | `0x413670` retires the current network record, then `0x413420` checks for the next one. Other non-battle opcodes have separate handlers between these iterations. |

`0x51D4E0` copies the supplied bytes into Q's external circular buffer, in at
most two contiguous pieces, and advances its write cursor. On a successful
append it neither rewrites S83's group/actor fields nor inserts a local sorted
actor list. The selected S83 append branch has no participant-stat, speed,
tie-break or skill-priority lookup. This bounded observation does not claim
that unrelated asynchronous handlers never update actor/UI data.

Current-aaf pass5 evidence already establishes `0x5140C0` consuming these
records and `0x52AC20` selecting the retained marker's actors by side/slot scan.
That existing evidence is a playback consumer. The older149c runtime backtrace
is neither rerun nor used as present-client authority. The new contribution is
the current-aaf upstream record-to-ring source, not a new claim about the
unchanged marker consumer.

Evidence: `queue-function-incoming-pass8-v1.json`
(`ev_9b85ab84efa5c2d01406c4762e39c304a2b7b2e391e160f6c027954ea14038d5`),
`incoming-queue-writer-and-tail-pass8-v2.json`
(`ev_8aa86b07503d33392a4910af67770837744f7257476d77e52f5aec69d03288f7`),
the matching raw instruction receipt v3, and
`computed-bulk-reset-and-network-queue-pass8-v3.json` /
`network-one-byte-source-pass8-v5.json`.

## A concrete receive-ring limit, not a native scheduling formula

`0x510E84` pushes `0x1400` and `0x510EB7..0x510EBD` invokes `0x51D300`
with ECX=Q. The allocator stores a separately allocated5120-byte buffer at
Q+4, capacity at Q+0x10, and zero cursors at Q+8/+0xC. `0x51D350` resets
those cursors; it does not clear an enclosing CWar control page.

The original `0x51D4E0` checks its cursor/capacity conditions and can return
failure. `0x519370` does not branch on that return before consuming the current
network record. Therefore the byte-order conclusion is conditional on valid
buffer state and successful append. It is not a lossless overflow guarantee,
and a transport aggregate limit such as16KiB is not a proof that the pending
battle ring can hold that entire burst. Equality/wrap edge behavior is retained
as the original code, not replaced by an invented server-side capacity policy.

This is a useful source constraint to check against actual projection bursts.
This lane has not demonstrated a current server burst exceeding the native
ring and makes no new production-defect or native-client test claim. Socket
Written and untrusted0B remain separate from proof that a client consumed Q.

## New computed bulk route stays below latchL

`0x5112C0` uses `LEA ESI,[B+0x144938]` at `0x51141C`, then calls
`0x51FC40` with ECX=M. A second direct reset caller is `0x51F970`.
Its actual resource-construction caller `0x5109D0` also forms M at
`0x510AC1` and uses that same base at `0x510DED -> 0x51F970`.

| Recovered write | Exact containing range and qualification |
| --- | --- |
| `0x51FC64` REP STOSD | `0x26D78` DWORDs, starting M+0xA7FBDAC. In B coordinates this is `[B+0xA9406E4, B+0xA9DBCC4)`, ending before L. |
| 168 actor resets | `2*14*6` records, stride0xECC. `0x51FDE0` poisons exactly0x3B3 DWORDs per actor and writes descriptor subfields within that0xECC record; the caller stores the auxiliary pointer at actor+0xEC8. These are the same bounded arena. |
| 28 auxiliary records | Bases start M+0xA89738C, stride0x2C. Their reserved interval ends at B+0xA9DC194, also below L. Reservation does not prove every transitive graphics helper's complete write set. |
| Manager counters | `0x51FD48/0x51FD4E` set DWORDs M+0xA7FBC64/+0xA7FBC68 toFFFFFFFF. These are B+0xA94059C/+0xA9405A0, **not** B+0xA9E9C64/+0xA9E9C68 or L. |
| CWar initializer copy | `0x51141A` copies0xFB DWORDs to B+0x48, ending B+0x434; it cannot reach L. |
| Resource constructor tail | `0x510F04` zeroes0x2B DWORDs at B+0xA9EA4F0, ending B+0xA9EA59C. This begins above L. |

The new selected bulk operations do not establish a set-to1 writer for L.
The four direct L read/clear instructions from pass7 remain prior evidence,
not a repeated whole-image search. No global no-alias conclusion follows:
other constructors, indirect callees, arbitrary bulk writes and computed bases
outside this selected chain have not been exhausted.

`procedure_callers(0x5112C0)` reports only the analyst seed. The raw incoming
reference record includes internal control-flow edges and that seed; it does
not recover the native indirect lifecycle caller. Thus the body and explicit
callee-base arithmetic are evidence, but a missing recovered direct caller
cannot prove that the native initializer is never invoked.

Evidence: `computed-bulk-reset-and-network-queue-pass8-v3.json`
(`ev_41c3a38f8a8720ce869d42d90f3c457ebc1e46b0f5456454028c2d50425c5e70`),
raw reset/initializer receipts v4/v5, second-caller receipts v7/v9, and
`battle-resource-constructor-base-widths-pass8-v8.json`
(`ev_3fbc52771325526b5eb72bd40f3220b91e66ab97bf81af3703c4e937bb49020a`).

## What can and cannot be implemented from this evidence

The usable contract is preservation of successful incoming record order,
explicit queue/capacity/source ownership, distinction of manager and CWar
counters, and the bounded exclusion of these bulk ranges from L. Existing
server-owned CUSTOM scheduling must remain labelled CUSTOM. There is no new
reason here to change core scheduling or fill an unknown latch with1.

The original server ordering is underdetermined by this client path. Keeping
the received S83 bytes fixed leaves the client's selected queue behavior the
same even if a hypothetical server used different intrinsic speed values,
ties, skill priorities or randomness to produce those bytes. This is a logical
non-uniqueness argument, not an executed counterfactual or a claim that every
client function lacks speed information. Merely labelling a received marker
as a rank or counter as a turn number would add an unsupported rule.

The precise missing source is the sender that joins participant identity and
intrinsic/effective speed, applies a comparator/tie/priority/RNG policy, orders
S83 records and assigns group markers/S88 counters. No such sender was found
in the newly traced incoming-byte branch. An original server implementation
or source-qualified original-server capture with independently known input
stats would be needed to distinguish candidate rules; an output sequence
alone still cannot uniquely establish a numeric formula.

For the residual client latch question, the next bounded static step is the
native indirect lifecycle registration/caller of `0x5112C0` and the remaining
enclosing CWar allocation/initialization write ranges. It must trace actual
computed bases, not repeat the same literal-displacement search. The upstream
network socket/decrypt buffer producer is separately not traced here; it is
not assumed to be a battle-speed comparator.

Author review and exact source/evidence SHA pins are retained under D. Static
source closure here is not build, gameplay, animation, Windows compatibility
or original server rule acceptance. The full goal and existing Discord
heartbeat retain their separately paused state.
