# Actual stored CN character summary to shared login

Round150: `20261008-cn-stored-character-summary-source`. PHASE1 source/files only;
no builds/tests/native/C++/Windows API/server/client/DB execution, schema installation,
import, migration, restart or deployment. Artifact: `cn-common-character-summary-source-provider-01`.

## Data gap and implemented read-through

The M2 agent positively establishes that existing recovered_characters contains
common identity/account/name/slot and40-byte profile, not complete CN07. Existing
role snapshots explicitly require CUSTOM-0013; their25-byte shape does not prove
CN role values. The retained HeroDoll observation reports issued07 rows0, while
its918 rows describe resource definitions. Names/resource filenames cannot supply
flags, visibility, byte18, slot mapping, inactive bytes, appearance/location or
an actual native metadata issuer. Existing account_native_snapshots.metadata has
its own40-byte account meaning and is not a reusable75-byte character summary.

This round implements actual persisted-issuer read-through, without generating
missing values. `NativeCharacterSummarySnapshotRepository` retains account/target/
pinned build, nonzero revision/origin, the complete raw record, explicit ordered
common character ID/name-source bindings and optional entire native role record
with independent revision/origin. The SQLite implementation uses the same actual
account and character objects and connection as Application. A new read-only
`uses_connection` observation on SqliteRecoveredCharacterRepository proves that
identity; it performs no SQL or mutation.

One SELECT cursor joins header, all ordered bindings and existing common account
ownership. Ordinals must be contiguous, character IDs unique and owned by that
account; missing bindings/count mismatch/partial role source/duplicate data fail.
Optional role record/revision/sourceSHA/sourceRecord are all present or all absent.
An actual zero-row record remains distinct from a missing snapshot. No BEGIN,
split header/row read, write, default record or schema-on-read occurs.

`schema()` proposes two shared version-keyed opaque delivery tables,
account_native_character_summaries and account_native_character_summary_rows.
They reference existing accounts/recovered_characters; no gameplay/identity/content
table is duplicated and no TW/CN prefix is used. Raw-storage budgets4096 bytes/rows
and2048 origin bytes are operational limits, not recovered native game caps.
The proposed schema is not registered in migrations or installed/populated.
Child bindings cascade on character removal, so a changed row set cannot silently
retain a complete old header; the reader rejects its count mismatch. Actual
producer/CAS/invalidation/removal/migration/recovery integration remains required
before schema activation. None is claimed complete from this reader.

`SharedStoredCharacterSummarySource` supplies the actual existing
SharedCommonCharacterSummarySource::Prepare. It requires the same repositories,
the fixed CN build, exact full75-byte07, explicit ordered mapping and a real
Authority observer. Optional role values must be actual full25-byteCN22 with
revision/origin, never CUSTOM-0013; unprojectableFF is absent rather than narrowed.
Without an explicit role dependency the original07 level stays untouched.
Common ID membership and NameSource modes are explicit, never name joins,
common-slot inference or an all-visible policy. Existing NativeMetadata checks
also require unique native slots, valid prompt modes and complete raw75 bytes.

The state is game-owner affine and rejects reentry. It owns the entire loaded
snapshot and re-reads equality of the whole tuple (raw record, rows, names modes,
roles, revisions and origins) around actual authority observation at Prepared,
BeforePublish, QueueAccepted and NameSubmission. Authority sees exact original
and projected07, typed rows and the complete common account roots. Existing
Common/selection root checks remain in place, including name/encoding/ownership
changes; snapshot revision or storage existence alone is never permission.
Common-name projection retains the existing byte-preserving implementation.

## Actual composition and lifetime

Database provides an optional backend capability; SqliteDatabase lazily returns
the same-connection reader after its existing migration check. Constructor and
getter perform no SQL, installation or import. Both repositories and the database
must outlive controller/authentication/transport drain.

The conditional Application CN host passes this exact reader in
SharedServerPlan::Context alongside accounts/account snapshot/characters/maps.
Host and typed login factory check that it owns those actual backends. The
explicit stored_character_summaries source form rejects a simultaneous direct
common-character metadata source and a different Context reader. It calls the
new read-through provider, then the existing Common::create and existing native
login composition. All original account/profile/world/seed/client-group/current
checks and held publication behavior remain; bind-time registry versus start-time
directory lifecycle from149 is unchanged.

Main still supplies null CN plan. Actual native07/CN22 snapshot producer/data,
real Authority callbacks, selected source factory/plan, world reservation/entry,
common online presence, per-session TW hooks/save/replay/committed issuer remain
unconfigured. This is an implemented reader/provider/source composition chain,
not activated native login or a completed bidirectional gameplay route.

## Parallel native source and correction

The title agent qualifies actual binding: startup-created login008AF1D8,
constructor44988A LEA ECX,[ESI+464] ->449890 CALL427330 gives resource008AF63C.
The login-to-world chain405F20/405F25->44A470->48CAA0 carries the same login
argument; world+8885C4 retains it;48CB91 adds464 and48CB97 stores world+A69F20.
48D611/617 supplies that resource as cell8 of the actual frame array;4AC8A6/4AC8A9
copies cell8 into UI+65364. The same member's load lineage449F50->428AE0->428C80
is separately qualified. This applies to the proven global-login-created UI form,
not every arbitrary UI object or constructor instance.

This corrects149's resource-relative probe interpretation:8AF1D8 was the outer
login object. Its relative D54CE/CF bytes were not the resource's GodLevel
boundary. The correct addresses are984B0A/B (8AF63C+D54CE/CF), with pinned PE
initial bytes0000. Historical149 seal/probe remain immutable; current evidence
explicitly supersedes that interpretation. No current source populated a guessed
empty string: actual Current/intervening writes/string lifetime remain OPEN and
selector4 remains unresolved. Original32 record/source behavior is unchanged.
The new delivery retains12 primary functions/18,463 bytes,53 exact sites and24
loader pairs;10 local CFGs are closed and2 external frontiers stay explicit.
Startup evidence from149 is not recounted as a new root.

The receiver agent qualifies4AA490's two primary tail targets4D2710/4D2740 and
two path-specific same-scene ECX witnesses. The segmented normal entry graph has
149 sites and no local frontier. Handle fields scene+1C8530/+1C853A/+1C84AC remain
distinct; the existing candidate fragment exclusion is not counted again.
47DE70/4812B0 caller/phase remain unqualified; next precise source is4AE2E0 entry
through4AE367->4E0F30. No global unreachable or complete callee graph is claimed.

## Accounting

New stored summary reader1, real read-through provider1, explicit composition
source binding1; no new opcode/phase/owner chain/full route. CN phase records/
distinct tuples remain91/69, TW10/10, partial owners38. Whole-game denominator,
complete routes and percentage remain null. Data/source shape is separate from
authority, formal hosting, deployment and native acceptance. TW/CN/PC/web/WSS,
numeric64/stack99, unchanged levels/fonts/conversion and frozen accounts/saves/
auth/chat/IME/portraits remain in the full active goal.
