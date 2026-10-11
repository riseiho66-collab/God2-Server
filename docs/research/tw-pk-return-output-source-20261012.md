# TW PK return: actual recipient routing and retained WORLD continuation

Round303, baseline `053859a835c35dad55cec20c0cf939617f7f4b25`.
This round recovers concrete source and native dependencies. Production C++
edits, newly connected source branches, new opcodes and completed routes are
all zero. No build, compiler, tests, native/game execution, VM, emulator,
codec execution, game DB/SQL execution, migration, activation or deployment.

## Actual preparation owner and output boundary

`OwnedPkOutboxPublication::terminal_accepted` (560..656) is the actual owner
reached from Session's accepted terminal callback. The second accepted peer
qualifies both exact final writes, terminal contexts, saved resources and the
retained departure, then preallocates two return generations. If configured,
the complete scene source supplies directed actors; private visibility
preparation retains canonical models and records. The final common text,
guild, root and pose read cut follows the terminal SQL reads (round302).
The callback ends by retaining `return_visibility` and `return_preparations`.
It does not send, consume, publish a normal generation, retire markers,
unlock the room or release input. This is the real next integration seam.

The exact current source ordering in `SharedActorVisibility` matters:

- `incoming_records[i]` belongs to returning **recipient** i.
- `outgoing_records[i]` belongs to returning **source** i and can target many
  surviving Sessions. It is not another batch for returning recipient i.
- `actors` and `staged` use canonical `(source.session, recipient.session)`
  keys. A mutual edge occurs in one incoming and the other outgoing list,
  while the canonical model exists once. Sending all list occurrences would
  duplicate that edge.
- The actual receiver is `actor.native.connection.lock()`, qualified against
  `actor.recipient`; `source_connection` is separately retained.
- One surviving observer can occur in both source-indexed outgoing lists.
  Future output must group canonical edges by that actual recipient and
  qualify one ordered queue reservation for it. Existing per-source order
  does not define an authoritative joint order for such an observer. Map
  iteration is not recovered native sender order.

The plan's endpoint predicates qualify actual InWorld/common delivery,
Session/Lease/current battle generation for survivors and private terminal
preparations for returners. They do not reserve the network strand's queue.
An empty actor scene still retains both returning endpoint/generation/input
obligations. Per-receiver actor capacity128 and the configured outgoing
allocation quota256 remain different scopes, not a new native256 rule.

## Distinct completion and failure boundaries

`Session::send_world_records_with_acceptance` (3092..3131) reports success
after `writes.push_back`, before actual socket completion. Its current Ready
terminal guard rejects new output. Ordinary visibility `submit` is also not
an async write receipt. Neither can close the return path unchanged.

`send_common_world_records_with_publication` (2545..2611) retains an exact
held frame and runs game publication before releasing it on the strand. Its
completion reports local queue release, not full socket write. It requires
normal CharacterSelected/InWorld common delivery, so broadening the phase
predicate would bypass the private terminal/return authority.

`send_world_records_observed` (2277..2288) has a real Pending→Written update
in the async_write handler (2069..2081), tied to exact byte pointer and full
transferred size. Its token can only be minted in that exact recipient's
synchronous world callback TLS and normal phase. The second accepted-terminal
callback and a foreign surviving observer do not possess that authority.
Written itself remains local socket completion, not remote client receipt.

`send_native_pk_output` is the battle grant/result path, not a return writer.
Forward `commit/release_native_pk_entry` are likewise not resume operations.
The next transport needs a distinct private ReturnHold and completion owner
for each actual recipient, with exact phase/identity/budget/frame/order and
failure semantics. A public raw-record getter or unfed encoder adds no route.

`close_timeout` is five seconds. The terminal deadline starts in the strand
prepare job (2869), before pair/scene readiness, and is not restarted by
acceptance. Ready requires the real callback ACK, read cancellation and
buffer/write drain; it is not a remote TCP/client epoch. The timer remains
armed, and `terminal_write_allowed` (769..773) rejects new output at Ready.

Return preparation (2899..2938) allocates immutable normal Data and the
original WORLD namespace with checked `prebattle_generation+2`. Neither is
installed live. Existing Written-PK proofs still require the old normal Data,
InBattle and the exact battle delivery identity. Publishing future Data or
setting InWorld early invalidates those proofs; the consumer needs explicit
one-use post-consumption authority, not continued reuse of the old token.

Failure currently preserves durable Finished state, member locks, outputs
and any already committed resources. Return bytes released to recipients
cannot be rolled back as a clean pre-commit failure. Return-specific durable
completion/recovery remains open; old battle submitted flags acknowledge
different output. `restore_retained` needs the original private Ticket and
issuer and does not rehydrate Sessions, holds or source receipts after a
process restart. Disconnect/visibility teardown is not successful return.

## Native receive buffer and pending-record lifetime

Pinned mapped image SHA256:
`149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`;
original PE SHA256:
`5fcf8cbfaf31d2635b4541886336293249cde61c0877de6f5a435cc2b9559fde`.
Selected intervals are compared against their actual PE sections; this is not
a claim that the entire mapped image equals the complete PE file.

The actual world receiver at468AE0 obtains the network owner through
world+A7E05E0. At468B3F..468B4C it calls413650(1), yielding owner+2CC4 as the
record buffer. 413420 reads bytes through412520 on owner+104; that supplier
subobject accesses its embedded ring at+654 (owner+758). It fills the fixed
buffer and tracks its count at+2CC0. 4695CB advances EBX past
the6F opcode before the previously recovered full-body consumer.

The common tail46B517 calls413670(1) to consume/reset the count, then
413420(1) to poll the next record. Consumption does not zero the byte buffer;
the next record can overwrite it. Old bytes at logical DWORD9 therefore do
not establish a permanent actor-state source. This does not prove global
absence of aliases or original server authority for DWORD9/17.

The selected calls415AF0/415B20 both reach412CF0. Its actual three PE bytes
are `xor eax,eax; ret`; this candidate is not a packet-retaining observer.
The other opaque helper54723B receives a global handle; its internals remain
outside this proof.

The one468AE0 stack argument is an outer stack scratch/output threaded from
4655E0 through467860/466B00/467154, not the6F receive buffer. The actual82
entry46AE12 writes output+28/+2C and sets return4. Its common tail consumes82
and polls the next record before468B31 stops on lastOpcode82. A following
record can consequently remain pending in the fixed buffer without dispatch
in that visit. This is a concrete scheduling boundary, not a new ACK or proof
that the pending record is6F. Upstream scratch consumers remain incomplete.
413420 also has a nonzero-count fast path; return0 alone does not certify a
complete/trusted record. Upstream framing/decryption and the state reachability
of secondary receiver519370 remain unqualified.

## Native WORLD processing before the next poll

Previously retained battle→main state3 continuation reaches the normal world
loop. Actual466E47 calls4FB290 before467154 calls468AE0. Newly expanded
4FB290..4FB44E scans128 actors at stride268, skips ID=-1 and invokes movement
and resource/context helpers. It compares actor+48 with four groups of cached
signed context handles, writes actor IDs into output slots and returns a
context category0..4. This is not a recovered server-return ACK or clock.

Complete4FB0D0..4FB272 returns immediately for stateWORD+38 other than8.
For state8, it accumulates float deltas from frame time, clamps integer steps
against remaining axis deltas, increments actor WORD pose+74/+76 and calls
4FCFD0, the resource-position chain retained in302. Completion requires both
axis flags. 4FB060 changes state8 to0 before4FD160; retarget4FB080 forwards
through4FCA90 and stores the next pair on success. Opaque children remain.
This is local movement/render causality, not a saved pose, HP/MP settlement,
common-core timing rule or original packet producer.

50B220/50B2C0/50B350/50B270 return cached signed WORD context values. Their
optional clearing arms require a nonzero second argument; actual4FB290 passes
zero. Complete465FA0..46643C dispatches local negative context codes through
a20-entry/80-byte data table, forwarding retained controller/string inputs.
These context codes are not packet opcodes. The exploratory early end46643A
is excluded; the full instruction boundary is46643C. Controller children and
their eventual producers are not recovered by these selected bodies.

Mode1 actor/resource retirement remains previous296 evidence, not new303
coverage. Combined with ID=-1 skipping, the selected world flow can proceed
to normal polling with an empty actor pool; that does not supply a complete
scene or prove client readiness. No fresh2A/login replay is inferred.

## Accounting and concrete continuation

Archive:
`C:/Users/risei/.codex/artifact-archives/god2-server/20261012/tw-pk-return-output-source-303`.
The current-output audit captures16 complete input files/524,002 bytes with
bounded manual scopes. Native return has11 exact code spans/2,758 bytes/891
sites plus80 data bytes: nine selected callees/2,405 bytes/790 sites versus
referenced289/290/295, two explicit290 overlaps/353 bytes/101 sites. These
are selection scopes, not global novelty or new protocol coverage. Native
buffer has20 qualified spans/2,061 bytes/632 sites plus8 data bytes:18 new
selections versus302/2,005 bytes/616 sites and two explicit6F overlaps/56
bytes/16 sites. Older20260919/20 overlaps are disclosed; the broad captured
world region is only a lead. Both native scopes remain separate.
All990 tracked src files remain byte-unchanged; capture is not full manual
review. No CUSTOM record, source segment or fullroute is added.

Mixed source segments282, CUSTOM records135, source groups26/pending10.
TW C2S candidates156; world parser74=limited50/control11/unconnected13.
TW S2C supported lengths252=fixed230/variable22, reply48/push11/gated4/
unclassified117; battle indexed110/specialized9,86 selectors7/cases6,
83 actions23/projections2. TW unhosted chains3/bindings38/unique34;
CN unhosted chains35/bindings93/unique71. CN historical C2S156,
S2C phase-opcode280 and length253 remain different scopes; CN increment0.
Full game route count, completed-route count, TW and whole-game percentages
remain null. Parser50/74 is not game completion.

Next: finish the exact full6F current opaque/state/resource/directed-scene
issuer and its Application/backend composition. Build actual canonical
recipient batches with qualified joint order, then connect the second
accepted-terminal owner to private returning/surviving-recipient ReturnHolds,
final common/terminal/scene source cut, one-use paired normal/model publication,
exact output completion/failure, terminal/departure retirement, input resume
and durable Finished recovery. Investigate actual buffer aliases/upstream
scratch consumption without substituting stale bytes, zero values or cached
diagnostic actors. Retain skills/rewards, companion resources and shared64
TW/CN/web requirements. Full goal remains active.
