# CN host Context to native login composition

Round `20261008-cn-shared-login-composition-context-source` (149). PHASE1 static
source/files only. No build, tests, client/server/C++ execution, Windows API,
database access, import, migration, restart or deployment.

## Applied source bridge

The prior round exposed the existing same-SQLite account snapshot reader in
`SharedServerPlan::Context`. This round applies the M2 agent's reviewed two-file
proposal to existing `SharedLoginComposition.h/.cpp`:

- `SharedLoginSourceFactory` takes the actual borrowed host Context and returns
  a fully qualified `SharedLoginSources` value. It is required, never defaulted.
- `make_native_login_controller_factory` returns exactly
  `decltype(SharedServerPlan::controllers)`. Its retained factory is invoked
  after the existing host has bound its real account/world sockets. The adapter
  directly calls `compose_native_login(context, std::move(sources))`; this is
  now a real conditional source caller in `src`, rather than a declaration or
  proposed pseudocode.
- Before calling external preparation, the adapter requires the snapshot
  reader to own the same accounts backend, plus actual admission/listener
  owners. Selected stored profile Config must reference precisely
  `context.account_snapshots`; existing Prepare/Authority/owns_accounts and
  snapshot revision/current checks remain mandatory.

Exactly one explicit account supplier form remains required: direct native
account, issued profile, or stored issued profile. Complete metadata40/billing16,
real entitlement/catalog/deadline observers, full character summaries and actual
world offer/preparation must come from their owners. Exactly one real seed or
explicit operational policy and one qualified client-group source are required.
No reflected login tail, guessed opaque bytes, fixed success, empty account,
zero actors, substitute native gameplay rules or alternate database are added.

The host still invokes its provided `plan.controllers` at its original site.
No formal plan assigns the new helper yet; Main still chooses the ordinary null
CN-plan overload. A source helper caller is not evidence of activated login or
complete bidirectional gameplay. Actual per-account Prepare/Authority, native
snapshot producer, world reservation/bootstrap/gameplay and shared TW/CN online
authority remain unconfigured. This proposal removes a concrete composition
dependency gap without fabricating those providers.

## Constructor and lifetime

The host creates/binds/listens and mints the registry before invoking its factory,
but starts accepting only after valid controllers exist. At factory time,
`bound_endpoints()` can return the real sockets; `listeners.observe()` cannot
provide an active Snapshot until managed start. A source factory must retain
the exact shared registry and defer active directory Plan creation to the real
per-account preparation callback after start. It must not create that Plan from
an inactive constructor-time observation.

Context and endpoint references expire after the factory invocation. The adapter
captures only its owned factory; external callbacks must retain shared owners,
copy endpoint values and use repository references/pointers whose database
lifetime covers transport/authentication/controller drain. The helper cannot
inspect callback captures or prove that their authors obey this contract.
Existing composition retains its own admission/listeners/client groups and
repository pointers. Shutdown invalidates the same registry before closing
connections, with controller destruction on the game owner. Exceptions and
missing inputs abort composition; none becomes successful empty controllers.

The agent's original patch/findings remain immutable as an unapplied proposal.
The root receipt records review and application separately. Before snapshots,
actual source diff/origins, ledger/goal additions and current catalog retain both
stages rather than replacing historical evidence.

## Parallel native evidence

The title-boundary agent qualifies startup749C34->749A75, the table interval
7EBF1C..7EC258(exclusive) passed to78C88C `__initterm`, and cell7EBF50(index13)
pointing to402D40. The table-rooted initializer has a complete local normal CFG:
ECX=8AF1D8;402D45 calls449880;402D55 returns. Pinned PE initial bytes at this
global object's D54CE/CF are0000. The actual resource pointer's binding to that
global object and all intervening writes remain unqualified. Therefore the
current WORLD32 selector4 string remains UNKNOWN; initial PE zeros are not a
current native empty-string supplier. Independent42CA20 caller remains OPEN.
Bounded fixed-reference searches do not prove global dead code. The agent keeps
startup external frontiers explicit and retains9 metadata functions/1,430 bytes,
a64-byte initializer envelope and17 exact sites, without summing overlap into
packet coverage.

The receiver agent shows the metadata range for475D40 truncated the reachable
475F5B `RET4` instruction. The unique normal predecessor475F5A POP EBP falls
through; reading precisely one more PE byte at475F5D completes the rooted CFG
(181 sites; returns475F50 and475F5B; no local frontier). The same-owner4748D0
getter has36 sites and reads signed16 image height. This adds no receiver caller
or phase;47DE70/4812B0 remain unresolved and the inventory stays14/12. The next
precise source is4AA490's tail edges to4D2740/4D2710 with actual ECX qualification.

## Accounting and continuation

New native login composition factory1, exact stored-context reader binding1;
new opcode0, phase source binding0, owner chain0, full bidirectional route0.
Agent local graphs/table roots are evidence increments, not whole-game coverage.
CN source binding records/distinct tuples stay91/69; TW10/10; partial owners38.
Whole-game total/completed/percentage remain null. Full TW/CN/native PC/web scope,
WSS/Origin, numeric64, stack99, unchanged native levels/fonts/text conversion and
frozen accounts/saves/auth/chat/IME/portraits are retained. Actual provider/source
factory/plan/world/presence/save/replay/committed issuer remain the next M2/M3 work.
