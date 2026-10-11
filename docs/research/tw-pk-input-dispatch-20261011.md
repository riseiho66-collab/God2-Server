# TW280: private PK frame dispatch and paired basic resolution

Phase 1 static source work only. No build, compiler, test, runtime, native
client, VM, codec execution, game database SQL, migration or deployment.
CUSTOM-0118 is inactive and does not install an Application PK host.

## Concrete source increment

`OwnedPkOutboxPublication::dispatch_native_basic` accepts a complete decoded
native frame from an actual privately bound Session. Its return is empty only
when that Session ID has no binding. An indexed but wrong, stale, pending or
failed Session rejects; it cannot fall through to diagnostic combat.

The dispatcher first classifies the entire record span. The bounded accepted
grammar is Tick-only, or exactly one control0B with Ticks, or exactly one
basic1 with Ticks. Empty input, duplicate operations, mixed control/basic,
skills, action2 and unrelated records reject before any control or intent is
persisted. This is a deliberately bounded source adapter, not the complete
native35 grammar or proof that original clients never emit mixed frames.

Caller identity, room, relative viewer, header context, battle revision and
grant epoch come from the private Session/hold/Ticket and current room phase.
The caller must still supply a separately current server profile digest equal
to the retained Ticket digest. Retained equality is a fence, not a new issuer
of current profile authority. Tick-only also requires the private binding and
profile fence. Tick supplies no grant, nonce, round, remote ACK or pump permit.

Only numeric BasicParameters are supplied: explicit bounded power, defense
and critical coefficients. No coefficient defaults, client-supplied source,
skill, MP cost, target authority or arbitrary Policy/header are introduced.
Existing canonical selection checks the original basic record's context and
relative target against the actual living opponent. Existing own outbox and
own grant-submitted guards still decide control/intent eligibility.

`resolve_collected_basic` bridges the same actual private pair to the TW279
fresh basic83/88 result producer and existing paired atomic settlement. It
requires both accepted entry Written proofs, clear Session publication tokens,
no in-flight output and no publisher pump. Explicit server execution order,
next-control masks and pure/nonreentrant gameplay Rule remain mandatory.
They are copied by value before callbacks. No first-arrival order, initial
mask, hit-based mask or default Lua policy is substituted.

The resolver fences the actual shared Battle snapshot and full persisted
round document before/after every Rule callback. Same-binding input, resolve
or publish reentry is rejected and poisons that resolution even if the nested
exception is swallowed. A resolution failure closes both Sessions and retains
durable state/locks for recovery. These checks supplement the Rule purity
contract; they do not certify arbitrary callbacks or every external alias.
Neither dispatch, settlement nor write completion performs an inline pump.

## Source and retained-native findings

Session1609..1689 delivers one complete ordinary native frame per callback;
TCP coalescing does not combine frames into one transaction. Matching skill
continuation is a separate bounded exception. RecoveredWorldRecords retains
record order and admits structural mixed-record frames. A valid parser result
does not establish semantic eligibility of each operation.

OwnedPkRound40..74 and repository control/intent paths keep three distinct
gates: accepted private entry Written, own checkpoint outbox submitted, and
own grant submitted. Both controls enter Grants, but a same-frame control/basic
mixture cannot cross the intervening asynchronous grant write. Rejecting the
whole mixture prevents a committed control prefix followed by rejected action.
Fast first control still does not require the peer's entry write to finish.

Session746..763 output staging requires cleared buffered input/pending records
and skill continuation. This work does not discard a tail, weaken that barrier
or pump inside the input callback. A future real host must schedule publication
at a valid later executor boundary after pending tokens clear.

Native worker reread three retained native263 spans, 681 bytes, from the pinned
mapped build149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763.
They support control/basic builder and enqueue edges only. No new PE spans,
original mixed-frame ordering, whole client CFG or native acceptance is claimed.
TW279 basic83 opaque/group/counter policies remain explicitly CUSTOM.

## Actual hosting gap and next work

Application2022 still leaves pk_rooms null. Application2457 rejects absent
diagnostic combat before a future PK input driver could run. Existing
party_sessions, pk_peer and owned_companion_restoration_sources already retain
the genuine normal initialization and Written sources; do not invent another
initialization registry. The new private dispatcher is ready source, not an
installed game callback.

The actual host still needs the pinned Fight archive provider, current profile
issuer, trusted seed and numeric policy, server order/next-mask sources, pure
Lua owner lifetime, explicit idle-boundary output scheduling, and failure and
terminal recovery composition. Later grants remain restricted to round1;
terminal89, saved rewards/settlement, fresh world return and reconnect/restart
remain open. Skills/action2/other35 variants are outside this new basic adapter.
No stub/default configuration is added just to claim an Application connection.

## Accounting

One existing C++ file modified; zero new C++ files. One bounded inactive private
frame/resolution adapter added; zero new opcodes or complete bidirectional
gameplay routes. Source segments262->263; CUSTOM records115->116; reviewed
groups26 unchanged. TW candidates156, world parser74 with limited source50,
control11 and unconnected13; S2C252 (230 fixed/22 variable), reply48, push11,
gated4 unchanged. TW unhosted chains3 and bindings38/unique34; CN chains35 and
bindings93/unique71 unchanged. CN historical C2S156, S2C phase/opcode280 and
length253 remain a separate scope. Full route denominator and percent are null.

TW/CN/web complete scope, shared64 numeric work, saved accounts, auth, chat,
IME, native fonts/text conversion and client binaries remain preserved. The
legacy signed16 result projection remains a limitation, not widened-wire
completion. Peer webv75 claims are metadata pending actual commit/source read;
no server/native acceptance or integration credit is added.

Evidence archive:
C:/Users/risei/.codex/artifact-archives/god2-server/20261011/tw-pk-input-dispatch-280
