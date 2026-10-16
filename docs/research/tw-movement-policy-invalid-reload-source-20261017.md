# Ordinary movement configuration: retain the last valid version — Round442

The actual CUSTOM-0150 DB policy Binding used by the shared Taiwan movement authority now rejects an invalid candidate while retaining the exact previous whole immutable snapshot. This directly implements the owner's failed-reload requirement for this existing policy family. Previously, shape/row/version/content errors escaped Binding::refresh into Authority::authorize's fatal cleanup and ultimately closed the movement Session, even though the old snapshot had never been overwritten.

## Typed content rejection and clean read boundary

OrdinaryMovementPolicyRepository::InvalidSnapshot is a narrow content-rejection category. It may escape load only after its own statements and read transaction have ended cleanly and ownership fences passed. Database errors, unavailable/revoked lifetime, wrong owner, caught reentry, transaction drift, allocation failures and SQL failures remain fatal. The shared Statement API is unchanged.

The actual SQLite loader adds ten typeof projection tags for the existing ten physical fields. Known wrong storage classes, negative/overflowing unsigned values, malformed profile keys, invalid booleans/ranges/design ID, mixed config versions, excess rows and empty candidates are rejected without narrowing or defaulting. The loader catches only InvalidSnapshot into an exception_ptr. The query is destroyed, then the original read.fence, read.finish and operation.fence must all succeed before that rejection is rethrown. A finish/fence error supersedes content rejection. Reading stops at the first invalid or first excess row, retains at most the configured bound, and never publishes a partial candidate. Actual reads were not executed in this source phase.

## Exact previous version and unchanged actual consumer

The cache retains its original shared snapshot pointer before the one repository load. It catches only InvalidSnapshot and may continue only when that exact snapshot is still installed, is nonempty by its original validation, the repository lifetime is available, and the operation is not poisoned. Startup has no old snapshot and still rejects invalid configuration. Candidate validation also uses the typed category for invalid shape/rows, rollback versions and changed contents under an unchanged version. Valid higher versions still publish once as an entire immutable table; valid identical versions preserve pointer identity.

The actual Authority::authorize Binding refresh, Lua rule use, original ticket observation and policy-current fences remain connected and unchanged. A rejected candidate returns the old profile observation, so no movement sequence, position/revision, direction, elapsed clock, fractional credit, initial credit, battle fingerprint or pending ticket is reset. The existing sole-CAS and postcommit credit publication remain byte-identical. There is no SQL retry, fallback after revocation/reentry, new ACK, native rule or second write. Deliberately removing an active profile in an otherwise valid higher whole version retains existing profile-not-found rejection; this round does not invent configuration deletion semantics.

## Qualification and remaining work

This is a C++ source implementation plus independent source review, not a build, test, executed reload, database access or native acceptance. Three existing C++ files change, no new project Python/Lua/CMake files. V78 retains176 of179 pins and updates3; canonical831 to833. One actual partial source increment, zero complete bidirectional routes and no packet-count change. Whole-game denominator and percentage remain unknown.

The existing per-authorize SQL refresh remains an OPEN architectural gap against the required scheduled/admin-driven reload service. This change does not claim that service, all-domain typed DB promotion, actual MySQL8 backend, complete consistent lossless export/full constraints/atomic publication/import, native movement/rate/reset/scene/Main/client ACK/all-writer/affine IO/atomic fanout/full inventory or TW100 completion.

Human 繼續工作 on2026-10-17 resumes the unchanged unfinished TW-first/shared CN/four binaryWS/all-system DB objective after441's historical pause. Preserve453 Traditional-primary/clientBIN skills/current-maximum-HP poison tenth/custom126150/original907/shared64/coin99999999999/stack99/native levels/saves/fonts/IME/auth/text/English DB fields/per-table Chinese TXT. PHASE1 source/static only remains in force;5070 GPU is authorized when useful and unused.
