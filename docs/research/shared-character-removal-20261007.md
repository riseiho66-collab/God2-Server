# Common stored-character removal and cross-version offer invalidation

PHASE1 additive source integration only. No build, tests, native/server run,
database access, migrations or deployment. Prior round made progress by adding
the two conditional ordinary17/18 ingress/queue owners and sealing catalog69.
This round adds an actual SQL writer and its common admission coordinator;
native19 permissions/replies and Application hosting remain open.

## Storage identity differs from native name echoes

The existing SqliteRecoveredCharacterRepository::erase_owned checks a stored
name plus common IDs, traverses the recovered root's FK descendants, and removes
the root atomically. Its current TW Application callback checks credential,
active world/movement and effective guild ownership. That callback and the
existing erase_owned.cpp implementation are untouched. Their TW authentication
and gameplay policies are not promoted into CN native authority.

CN19 identity already resolves the exact current07 native slot/raw CP936 name
against actual common row IDs and authenticated credential aliases. Its wire
name is not a common stored name lookup and may differ in encoding. The new
erase_owned_snapshot accepts a copied actual RecoveredCharacter, not CN account,
credential, slot or name claims. It compares ID/account/slot/profile/name_bytes/
created_at/name_codepage/streamer_privilege inside BEGIN IMMEDIATE and again in
the root DELETE predicate. The expected stored name comes from the actual
common40-byte profile. Existing common storage's14-byte name/two-slot constraints
are retained storage bounds, not CN19's producer domain or proof that every CN
character variant is representable. No encoding conversion or table duplication
is introduced. The public snapshot is copied before any predicate can run.

## Actual transaction and rollback source

The additive writer is src/db/SqliteOwnedCharacterRemoval.cpp. It requires
foreign-key enforcement, starts the existing SQLite transaction abstraction,
checks the complete row, invokes a mandatory BeforeErase operation predicate,
and stages the existing battle leaves/FK-descendant cleanup. It then performs
the complete root CAS and invokes a mandatory BeforeCommit predicate before
COMMIT. False or exception rolls back staged root and descendants. Native19
permission/rules/online-owner/replay checks must come from the actual caller;
there is no default true predicate or guessed success/reply.

BeforeCommit runs after the root is staged as deleted. A caller must check its
operation/leases/prepared admission plan rather than reuse an identity predicate
that requires the deleted row still to exist. The predicates observe only,
perform no writes or nested transactions, and never yield/event-pump. The writer
does not execute any predicate between COMMIT and admission application.

FK traversal preserves the existing recovered-root cleanup scope: leaves for
battle IDs, then descendants with a character_id column. It does not invent
ownership of arbitrary JSON/legacy records or non-FK references. Remaining
foreign-key violations abort COMMIT and roll back; this is not a claim that
all future save systems' deletion policies or durable history were recovered.
Real guild succession/online/trade/battle constraints and comprehensive later
save-graph checks remain required in the actual operation owner.

## Common transaction-to-offer connection

SharedCharacterRemoval::commit prepares the existing registry-bound single-use
CharacterOfferInvalidation before any storage changes. Its transaction predicate
checks the plan before and after the actual rule/operation predicate, preventing
the latter from making a stale plan appear current. After a successful SQL
COMMIT it immediately applies the prepared plan on the same serial game owner,
without allocations, callbacks or yields. Every offered TW/CN grant for the exact
common account/character is invalidated; unaffected IDs and the current world's
ticket remain available for the native terminal drain/cleanup.

If the post-commit invariant were ever broken, the coordinator throws an
explicit committed-removal failure, rather than return false implying a rollback
or fabricate a native success. Actual durable operation/recovery/replay and
cross-process invalidation remain open. No SQL changes are performed in PHASE1;
the source is available under the existing CMake recursive src/*.cpp selection.

New common-storage CAS writer1 and storage-to-TW/CN-offer coordinator1. No native
19 ingress, opcode binding, native supplier, schema/table/ID migration, complete
gameplay route or hosting is added. The next owner must connect qualified CN19
identity, actual permission/online/guild constraints, this transaction, complete
native02/1E result and existing03 drain without reusing stale offered07 checks
after commit. Whole-game route count/completion percentage remain null; levels,
frozen native functionality, original fonts and text conversion are unchanged.
