# CN issued account source (2026-10-08)

Round `20261008-cn-issued-account-source`, PHASE1 source only. The previous
goal turn made concrete progress: explicit own-server transport seed source,
catalog115 and its67-file delivery seal. This round reread the current sources
and captured26 before-context files before edits. No build, tests, RNG/native/
client/server/codec/C++ reader/Lua/browser execution, database access, migration
or deployment. All current accounts/saves and frozen features are preserved.

## Reuse actual native evidence

Pinned PE32 client SHA256:
`582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8`.
Retained historical findings: `cn-admission-contract-agent-01`,
`cn-account-tail-agent-01`, `cn-billing-byte5-agent-01`. They already establish
the1D replacement/world00 resend relation and the unknown-field limits. This
round does not promote them into newly recovered field semantics.

Three current file-backed metadata envelopes were retained again as primary
operands:0047FE30 2,009B,004814D0 212B,004468F0 638B, total2,859B. They are
bounded spans, not whole-program CFG proofs;0047FE30's retained span ends in a
jump back to its existing epilogue rather than an assertion that all callers
and branches were exhausted. No client was loaded or run.

004468F0 copies native24-byte account and132-byte credential fields, ending
at payload9B.0047FE30 compares received1D strings at004802AE..004802E2,
then004802F9 copies all204 payload bytes to the retained login record. The
comparison routine at0076DD7D is the previously identified native case-insensitive
CRT string path; our qualified integration continues exact credential echo,
not unproven case-changing server serialization. Bytes after the terminators
are preserved from the independently verified native request's credential
fields; they are not claimed to recover official padding conventions.

Actual fields: payload9C u32 account ID andA0 u32 check_key.004814D0 reads
those at00481536/2D and emits all204 bytes through00481440 at00481579..84.
Incoming account04 can contain stale prior ID/key; it cannot supply authority.
A4..CB is40 additional native bytes: local serial/version, provider byteA8,
group byteA9 and remaining opaque tail. Client-local group writes and raw
provider UI effects do not recover the account server's serializer or rights.
S2C0A payload16 includes opaque byte5; it must not be normalized or zero-filled.

## Source producer now implemented

`SharedIssuedAccountSource` supplies a real optional source factory for the
existing `SharedLoginSources.account` continuation. Composition selects exactly
one existing full native account callback or explicit `issued_account_source`;
both present is rejected, absence remains rejected. Transport seed and world
suppliers remain independent and mandatory. The ordinary Application/main
still select no CN plan, so this is source integration, not activation.

The caller supplies an actual profile owner through `Prepare(Scope)`; raw
credentials are not passed to that storage/entitlement preparation callback.
It returns all40 metadata bytes, all16 billing bytes, an explicit nonzero source
revision, a mandatory Current observation, actual deadline/catalog/summaries,
and optional existing naming sources. A Profile has no default constructor;
its factory rejects missing/wrong-width bytes, scope/revision or observer.
No persisted data, profile values, rights, paytype, deadlines or unknown bytes
are invented. Empty catalog/summaries and elapsed supplied deadlines reject.

The new source assembles each205-byte1D from156 bytes of the exact verified
native request's account/credential fields, the independently verified common
account ID, a separately issued4-byte check_key, and the ACTUAL40-byte profile
payload. No incoming04 ID/key/metadata tail is reflected. All17 bytes of0A
are its known opcode plus the ACTUAL16-byte billing profile; even byte5 is kept.
This is a source-form implementation supported by the bounded consumer, not
recovery of official server emission/opaque-field rules.

`WindowsSystemCngV1` check_key generation is explicit OWN-server operation,
using a separate4-byte `BCryptGenRandom` call. It is neither the16-byte handshake
seed nor a derivative of it. Windows documents the null handle requirement
for `BCRYPT_USE_SYSTEM_PREFERRED_RNG`, size in bytes and checked return status:
[BCryptGenRandom primary documentation](https://learn.microsoft.com/en-us/windows/win32/api/bcrypt/nf-bcrypt-bcryptgenrandom).
CNG failure returns no source; no fixed value, reflected key, counter/time/PID
generator, retry or fallback. Zero can be legitimate actual output. Existing
shared admission rejects reused account/key tuples within its own registry
lifetime; it does not promise collision-free RNG or durable restart revocation.

## Actual lifetime and publication

The factory is owned by the constructing serial game thread. Copies retain the
same increasing connection-ID gate; a verified source attempt consumes its ID
even on failure. Preparation/verification/RNG/from_source is guarded against
reentry. The existing composition first checks the original connection's token/
Login identity before invoking this source. A publicly constructed
CredentialResult alone is insufficient: the verifier-issued private token must
be present and current. Its current-value semantics and credential ABA/revision
limitations are unchanged, not silently promoted into durable authority.

Current captures the immutable native Profile, weak original Login, actual
verifier token, generated key, account/session and supplied deadline. At
Prepared/BeforeIssue/BeforePublish it compares complete literal metadata and
billing, original credential fields, verified ID and the exact generated key.
Prepared explicitly lacks catalog/deadline; the later two stages must contain
the same supplied deadline and a nonempty actual serialized catalog. The real
profile Current must qualify that complete catalog, rights, revision and source
lifetime. It is mandatory and observational; a matching revision number alone
does not prove source authority. Credential continuity is reread around it.

The actual SharedAccountSuccess path still issues the shared grant, installs
the existing selection owner, serializes the catalog once for its output,
queues1D/catalog/0A behind its real held IO barrier, and invokes BeforePublish
before bytes can leave. No source predicate is invoked after release. Full
credential-record temporaries are wiped on discard; Current construction
precedes credential copying, and the existing NativeData owns/wipes its full1D.
The new profile stores no password, Login copy or full1D. No live record is
written to logs, files, SQLite or Lua by this producer.

## Limits and next frontier

New literal1D/0A source assembler1, explicit own-server key issuer1, existing
login source binding strengthened1. Native field semantics/opcode/phase/
complete owner chain/complete bidirectional route additions0. Total/completed/
percentage remain unknown. No storage schema/table was introduced or split;
common accounts and existing tables stay unchanged.

The actual native profile/billing/entitlement/revision/catalog/deadline owner
is still unconfigured. This implementation eliminates manual whole1D assembly
for the known authority fields when that owner is supplied; it does not claim
the missing40/16 payload sources exist. Native07 and complete world1F/02/2A/6F/
equipment/scene/ACT suppliers, TW registry, PC/web/WSS hosting, all gameplay,
numeric widening and direction/state/variant denominator remain open. Next:
connect actual directory records to the real listener endpoint registry and
continue native profile/opaque-field recovery without inventing values.
