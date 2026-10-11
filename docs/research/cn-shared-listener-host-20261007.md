# CN listener and native login composition in the shared Application

Phase 1 source increment, 2026-10-07. No build, socket listener, client/server,
Lua, native execution, test, asset loader, production database access or release
was run. The ordinary main/config entry still calls the existing TW overload;
no CN endpoint, native success bytes, entitlement, key or deadline is invented.

## Concrete source connections

`Application::run_server(config, SharedServerPlan, duration)` uses the existing
network context and single game thread, AccountRepository,
RecoveredCharacterRepository and read-only NativeMapCatalog. It constructs the
CN host beside the existing TW listeners, starts it in the same startup path,
and stops it before releasing network work. Explicit CN ports cannot conflict
with actual TW bound ports. The original overload forwards a null CN plan and
preserves the existing TW packet handlers, config, storage and frozen features.

`SharedCredentialServer` owns one CN account listener and explicit world
listeners. A connection's role/destination comes from its socket, remains fixed,
and is not guessed from wire opcode, claimed account or Chinese presentation.
Each world destination is unique (group <64, server <10); each port is nonzero.
Factories receive the Application's actual shared repositories, admission
registry and endpoint values. Native seed/account/world controllers are mandatory
before any listener is constructed. There is no permissive fallback controller.

Accept/retry/socket handling uses a network strand. Accepted sockets are posted
with a game work guard to the serial owner, which rechecks stop/capacity before
constructing SharedCredentialConnection with the common account verifier.
Reservation slots bound accepted-but-queued, live and closing transports, in
addition to the game map's size. TCP rejection creates no game success packet.
Transport cleanup retains the existing generation-qualified account/world ticket
release. Network handlers hold only a weak game state; the verifier's worker pool
and state/controller destruction stay on the game owner. Shared repositories and
both executors must outlive drain. The existing exceptional shutdown behavior is
retained; runtime/compiler/lifecycle qualification is deferred to phase 2.

`compose_native_login` supplies actual continuations rather than a mock success:

1. Account credentials independently verified in the existing shared account
   repository -> same connection's authenticated Login pointer -> required full
   native NativeData/catalog/SummarySource -> SharedAccountSuccess::attach ->
   shared issued grant -> ordered 1D/catalog/0A -> existing A6/07 dispatcher.
2. World credentials independently verified -> actual listener Target and unique
   server connection ID -> required native NativeOffer/Selected ->
   SharedWorldSelection::attach -> selected shared ticket/current character
   ownership -> complete 1F -> existing 1A/real Selected continuation.

Complete opaque records and their authority remain supplied prerequisites. The
account directory's enabled destinations must exactly match actual world
listeners, including explicit IPv4 and port. This bounded concrete-address form
does not rewrite native directory bytes or assert support for NAT/wildcard/IPv6
advertisement. Source context and endpoint values are copied where retained;
credential snapshots are not retained by the composition beyond the existing
controller's defined lifetime. Missing or invalid suppliers never become success.

`SharedWorldSelection` now borrows `const NativeMapCatalog&`, matching the real
Application reader. Its lookup and packet/state behavior are unchanged.

TW TcpServer and the CN host both use ConnectionIdentity's process-lifetime
monotonic atomic allocator. IDs start at1, are never client claims, and never
wrap/reuse at exhaustion. This changes no TW frame/auth/chat implementation.

## Provenance and limits

The listener, budget, connection allocator, source composition and lifecycle
policy are server integration policy, not recovered official server algorithms.
The existing native account/world contracts remain the pinned CN build
582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8,
with hashed prior account-success/world-selection/admission/entry evidence.
Prior catalog29 and before-edit sources are preserved in
`cn-shared-listener-host-01`. No historical report or native baseline is replaced.

This closes the absence of a conditional Application lifecycle/listener and the
absence of explicit native success-controller composition **in source**. It does
not close the missing native value issuer or establish formal production hosting.
The production entry does not construct a qualified plan, and no server was run.
Existing39 CN phase-source bindings (28 unique),7 TW bindings (7 unique) and
18 CN/2 TW partial owner chains remain the same. New opcode/phase bindings and
complete gameplay routes are0. All game totals and completion percentage remain
unknown;958 endpoint-index rows are not958 complete game routes.

Remaining: qualified seed/1D/0A/billing/07/1F suppliers, actual source/grant/alias
lineage and credential revision/revocation authority; actual shared scene/world
actor, full02/2A/bootstrap/readiness/later gameplay; TW enrollment in the common
admission/world authority; native variants and the complete directional/state/
indirect/deferred denominator. Full movement permission/5D, live camera/path
scheduler, all gameplay and eventual cross-version interactions remain open.

Next work: recover and implement the missing native supplier fields against the
existing shared storage, starting with 1D/billing and 07 native common-ID lineage;
do not replace them with a TW raw row, zero template or echoed client tail.
