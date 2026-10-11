# CN verified repository source through held login publication

Round: `20261007-cn-credential-source-continuity`. PHASE1 source integration;
no build, native/server/browser execution, test, database access or deployment.
Previous goal turn answered owner status only (no source progress); current
source was reread before this implementation. Levels and frozen TW behavior
remain unchanged. These helpers do not complete an authenticated gameplay route.

## Actual source gap

`SharedAccountVerifier::verify_raw_ui` already resolves the shared repository's
exact byte identity, then its existing ASCII-only folded alias; verifies the
existing PasswordHash on its bounded worker pool; returns on the game owner;
and rereads the original row's username/password_hash before Verified. It
previously passed only outcome and account ID to the delayed account/world
controllers. A matching ID or retained Login pointer could not establish that
the verified row still agreed when source preparation and IO holding completed.

The existing `AccountRepository` and `SqliteAccountRepository` expose
id/username/password_hash/created_at, with no credential revision or revocation
epoch. Their interfaces and storage remain byte-identical. The CN account
success source retains the existing complete issued1D/directory04/05/06/billing0A
order and exact originals; initial world success retains the existing complete
1F source. Pinned client receive evidence is retained from catalog107, not
newly executed or promoted into official server issuance rules.

## Connected source increment

The real verifier now privately issues `VerifiedCredentialSource` from the
exact snapshot its worker verified and its game-owner continuation compared.
No callback/yield intervenes between that comparison and issuance. The token
has no external constructor/current predicate or copy operation; failures and
unverified results carry no token. Its current observer weakly holds the same
verifier state, enforces its owner/stopped lifetime, and rereads the same
AccountRepository row. It requires exact id/username/password_hash equality.
Owned new binding/observation strings are explicitly cleared on destruction;
the existing raw Secret and Login wiping deleters are retained. This is not
a claim that every transient compiler/repository copy is wiped.

`SharedCredentialConnection` weakly binds the token to its actual verified
account and original Login snapshot. `compose_native_login` requires this
same token for both Account04 and independently verified World00 controllers.
It is not transferable merely by reusing another connection's account ID.

The existing account success controller retains its exact token through
BeforeIssue and the final held queue BeforePublish callback, after native issuer
qualification and before grant confirmation. The existing initial1F controller
retains the World00 token and wiping Login only for its held queue publication,
checking after actual character offer qualification. Missing/changed/stopped
sources fail before these success bytes leave. Source lifetime is not extended
into stored gameplay controllers; no obsolete credential/source predicate is
rerun after successful IO barrier release. Current admitted session ownership
continues to use the separate existing admission/ticket authority.

Native LoginStage parsers, failure bytes, PasswordHash format/worker behavior,
TW authentication, Application, native codec, repository, shared admission,
and other world selection methods are preserved. No DB/schema/migration,
native source defaults, raw credential receipts or new opcode were introduced.

## Evidence and open limits

Before snapshots were captured for all edited files before the first mutation.
Source-only delivery records hashes/diffs and preserved bodies, the previous
100-file seal and account receive envelope metadata. No mock repository,
authentication callback, native parser, C++ program, build or test was run.

This is current-value continuity, **not a monotonic credential revision**:
changes reverted between observations (ABA), concurrent external writes after
the last read, cross-process leases, account/entitlement revocation and later
session policy remain open. Never claim a durable source revision from equality.
Actual native seed/issued1D/billing0A/catalog/key/deadline/current policy,
full07/1F/02/2A/6F/equipment/scene/ACT/observer providers, TW common registry
enrollment, formal native PC/web hosting, gameplay/numeric extensions and the
direction/state/variant/indirect/deferred whole-game denominator remain open.

The web peer's `20261007-native-full-appearance` three original SHA-bound files
were read and saved under this round's peer-handoff. Its reported 29780-file
seal and rendering checks were not independently rerun or individually read.
The report remains renderReady=false, releaseEligible=false and gameplay0;
catalog resources/ACT operands do not qualify native cache handles/slots or
server authority. Missing original resources/palette/auxiliary/maps remain
explicit. Its capacity observation 42213693455 bytes is peer-reported; the
server did not remeasure the tree. Production WSS/permissions/credential
lifetimes/replay/duplicate/abuse protection still requires later joint
acceptance; minification/hash/obfuscation alone does not establish authority.

Delta: privately issued credential source1; existing held success paths
strengthened2 (account success and world1F); new native opcodes/phase bindings/
owner chains/complete bidirectional routes0. Whole-game total, complete count
and percentage remain null. Full tests follow all source connections.
