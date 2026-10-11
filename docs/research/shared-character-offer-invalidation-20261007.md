# Shared TW/CN stale character-offer invalidation after common mutation

PHASE1 source accounting only. Previous goal turn made progress: a common
created-character location identity resolver and native location projection
were added. No build/test/native/server execution, production DB access,
migration or deployment. Native levels, fonts/text conversion, frozen TW
deletion behavior, accounts/saves/chat/IME and unrelated features are preserved.

## Why the storage callback cannot be promoted directly

Current TW Application deletion checks its existing auth/name/online/movement/
guild-owner restrictions, then calls its existing common erase_owned transaction.
Migration and repository source show a multi-level FK graph with both cascading
and non-cascading character dependencies. Neither that TW permission policy nor
a root-only SQL DELETE is the recovered CN native operation. These sources are
retained as context without edits or execution. Native19's identity resolver
does not consume an operation, authorize deletion or update shared saved state.

The already sealed CN completion evidence shows02status0 -> local cached07
compaction ->0204/world03 wait ->account0A/reconnect. It does not prove server
permissions or delete storage. Copies of its original hashed primary spans
are reused, not counted as newly recovered paths. Full native reply issuers
and1E's exceptional continuation remain open.

## Concrete shared admission source change

SharedWorldAdmission now supports a prepared, registry-bound, move-only,
single-use CharacterOfferInvalidation plan for an exact common account/role ID.
It includes every currently offered match across TW and CN grants, independent
of their wire slot/name/resource IDs. Every affected entry's generation, account
session, world session, reservation, target, full offer/native bytes, deadline,
stage, invalidation set and offer_revision are captured for a current-state check.
New matching grants, removed/replaced entries or changed source state reject
the plan. An identical account reselection advances offer_revision, so it also
supersedes a previously prepared plan. Revision increments are checked for
overflow before preparation/selection; an exhausted revision cannot wrap.

Preparation performs all copying/set/vector allocation before the actual save
transaction. The actual native operation owner must execute real rules and
storage work, check this plan immediately before COMMIT, then after successful
COMMIT apply it without callbacks/yields on the same serial game executor.
Application uses only non-allocating map lookup/set swaps and revision changes;
all entries are checked before any in-memory mutation. A moved-from, consumed,
cross-registry or stale plan cannot apply. Empty plans are legitimate when no
grant currently offered the mutated common ID. Registry must outlive the plan.

This is an in-process integration primitive, not a database transaction,
durable replay receipt or native deletion permission. The actual owner/storage
link is still missing; none of these methods is called by a new live handler.
Crash recovery and cross-process credential/operation revocation remain separate.
Never apply a plan before SQL COMMIT or keep it across an asynchronous mutation
without rechecking and re-preparing its exact current scope.

## Exact invalidation and preservation behavior

- character_offered returns false for the invalidated character and continues
  to recognize unaffected IDs in an existing WorldOwned ticket.
- offered_source returns absent when any character in its complete native offer
  is invalidated. Old raw07/other adapter bytes are retained as historical
  source, never rewritten into a guessed compacted offer or silently paired
  with a shorter ID list.
- reserve and commit reject stale offers. Actual reselect with a newly qualified
  offer clears that entry's invalidation and advances its offer_revision.
- world_owned keeps the exact current WorldOwned generation/session/reservation.
  It can support the real terminal drain/release even when the old offer source
  is invalid. Other accounts/grants and unaffected active role membership are
  preserved; this primitive does not evict actors or close native connections.
- Existing release/cancel/expire/native encoding and existing TW delete callback
  remain in place. Until a real mutation calls this new primitive, invalidation
  sets are empty and existing admission behavior is preserved.

## Accounting and next integration

Two shared C++ files add one common lifecycle capability with prepare/current/
apply stages; no new CN opcode, phase binding, complete gameplay route, live
delete handler, DB transaction or native reply issuer. The same common IDs and
storage remain default; no _tw/_cn table or independent CN DB is introduced.
TW/CN C2S156 each, TW S2C252 lengths, CN S2C account6/world206/battle68 are
unchanged. Whole-game denominator/completed/percentage stay unknown.

Next bind the actual native operation/offline owner and complete save/dependency
transaction to this postcommit invalidation, then real02/1E/03 reply suppliers
and generation-safe close/reconnect. Continue native creation/map/18 and all
indirect/deferred/state/variant source gaps without promoting TW CUSTOM policy
into CN evidence.
