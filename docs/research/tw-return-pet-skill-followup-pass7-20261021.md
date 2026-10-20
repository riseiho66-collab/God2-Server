# Return / pet / skill continuation: pass7 source follow-up

Status: SOURCE_STATIC_ONLY. No builds, tests, native/game execution, SQL,
schemas, codecs or deployment were executed. The regression files below are
unexecuted source, not passed tests or native gameplay acceptance.

## New finding and linked corrections

After a genuine Return, learning or C67 produces a new canonical source.
Application's canonical observer accepted learning/selection Current through
OR branches before the material branch containing the normal movement check.
Its successor publisher had the same gap. A saved-row observer could remove the
actual movement binding, set a transfer pending, or replace the binding at the
same coordinates without changing the saved DB tuple or Session INIT. The old
canonical could then be treated as current. The learning commit predicate and
legacy C67 commit likewise lacked that actual normal-world dependency.

This is a source-reachable observer/lifecycle defect. It is not evidence that an
external player can run SQL or that a live client reproduced this sequence.

RecoveredMovementService now exposes a private-constructor pure
WorldLocationObservation. Each newly prepared Position allocates one private
incarnation; regular Position copies, legal movement and transfers retain it.
The observation retains the identity, preventing remove/reprepare at the same
address/coordinates from reviving the old evidence. Prepared-but-unready,
foreign owner/service, pending transfer and wrong-thread reads cannot qualify.
Binding-current and pose-current are separate: a legal committed step keeps its
binding while retiring its previous pose. These observations grant no movement,
inventory, learning, socket publication, combat or normal-world admission.

The original normal companion holder captures the actual binding before its
first saved observers and retains that incarnation across movement, joint item
successors, C67, learning and Return. New per-operation pose capture must first
match the holder's original binding. It cannot rebase history onto a new
same-value binding. The initial sender and every later observer check the same
pure source on both sides of saved reads. A pending initial physical2A Write
defers the first unsent restoration; it does not produce a fake grant or replay
previously sent companion records.

RecoveredNormalCompanionCurrent combines that actual binding/pose observation
with Written private INIT, full owner, normal phase/battle and Application owner
lifetime. Its provider is owned before SQL and invoked only on the GAME thread.
All canonical Current alternatives, ordinary original restoration, learning/C67
successor publication, C24/C28 callbacks and the learning commit's final pure
cut use it. Common-world still uses its existing actual presence/lease source;
it does not borrow normal movement as authority.

Legacy C67 passes its exact active callback/input occurrence plus the owned
pure predicate through the actual companion helper into the full-row selection
transaction. It shares physical-connection exclusion with pet24/28 and rejects
actual retained PK/PvE claims. Existing expected selector, full deity rows and
readback remain required. A post-COMMIT current=false is only the delivery-cut
result: durable data is retained, no success/publication/successor is issued,
and no rollback or retry is claimed. A true value is not future live-row,
Session, socket-Written or casting permission.

The related whole bank Context retains its original opening observation. The
Application classifier also captures the original binding before its first
location/NPC lookup, rechecks after money.open, and cannot qualify a fresh
Context after an observer replaced the binding. The final joint response
checks the same original incarnation before/after its last SQL. Ordinary
movement uses binding-current there and still validates the actual committed
after-pose, so this fix does not lock the player to historical coordinates.

PvE member preparation, retained WorldBefore, return supplier, returned catch-up
and Application ReturnHandoff keep the same original movement incarnation.
During InBattle they use pure binding/pose evidence, not a normal-phase helper.
The actual final Return commit, physical Write and private new INIT remain
required. No S30 replay, fresh restoration, rewritten token or ignored stale
check was added.

## Source cases and review limits

* test_recovered_movement_service: prepared is not ready; legal step retains
  incarnation but retires old pose; same-value remove/reprepare and a foreign
  service cannot adopt an old observation.
* test_session_state: actual first C25 bootstrap and identical deferred original
  job, then book commit with actual Session/ready movement. UPDATE observers
  remove/rebind before commit: no debit. Successful COMMIT PROFILE observers
  remove/rebind: durable debit remains, no success output is published. The
  original close/release/duplicate defer and return/new-INIT cases remain.
* test_owned_companions: actual C67 helper/repository plus ready movement,
  precommit and successful-COMMIT PROFILE removal/same-value replacement, full
  selector/activation preservation, and a direct durable private carrier with
  current=false that cannot be accepted as issued selection or roster successor.

The bank's complete private Session/NPC/lease/full300-cell host fixture was not
created in this pass. Its opening/final source cuts received source review;
focused movement or joint transaction cases are not claimed as that host's
runtime acceptance. The combined full App, native client, NPC catalog variants,
acquisition/capacity rules and every battle rule remain separate acceptance
requirements. This source audit does not establish a completion percentage.
