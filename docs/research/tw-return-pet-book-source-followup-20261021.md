# Return, pet selection and first-book continuation — source follow-up

Status: PHASE1 SOURCE_STATIC_ONLY. No compiler, tests, game, codec, SQL,
migration, deployment or native runtime was executed for these changes.

The linked source audit found three concrete breaks: modern WholeBag rejected
all C28 before the actual pet callback; first C25/C26 could reach learning before
its nonempty bootstrap output was Written; and the equivalent C24 reserve move
used a different, weaker transaction. A category comparison also attempted to
compare a type without equality. These are source findings, not observed live
game failures.

## Actual host and save paths

Application classifies the whole original pet batch before WholeBag can execute
an item, bank or movement prefix. C28 admits one qualified pet request in42..44
with Tick and its already-supported trailing1F00. C24 admits one reserve42/43
request with Tick; crossing bag/pet namespaces, active44 C24, duplicate writes
and other mutations reject as a whole. RecoveredWorldService independently
preflights the legacy whole batch. B4 run planning rejects these mixed requests
before splitting. The original Session-owned span is forwarded without copying
the occurrence.

Both actual Application callbacks capture Written INIT, exact phase/battle,
full account/character, actual movement owner and current pose. Pure checks run
after observations and through the final transaction fence. InBattle, pending
scene, replacement INIT, close and changed movement owner/pose cannot commit.

C28 activation and C24 reserve reorder call the same private swap_pet_cells.
It owns both complete expected cells and preparation/current callbacks, shares
one reentry poison per physical sqlite connection across repository facades,
requires its own transaction, rejects legacy unfinished battles and retained PK
or PvE claims, and compares the entire saved population before and after. Every
unchanged third cell, both metadata/stat families, opaque bytes, provenance,
display category and revisions are retained. Only routing bytes and revisions
change under existing CUSTOM-0039 policy. No cell, pet or native formula is
invented. Packet preparation precedes writes. Late source retirement after
COMMIT returns durable/current=false; callers close without success output or
retry and do not claim rollback.

Actual owner, slot, metadata, category and legacy-claim reads plus swap writes
use main-qualified names. Thus the specific final-owner observer that renames
the actual main pet table and supplies a TEMP mirror cannot fake final readback.
Existing namespace checks still reject preexisting shadows/triggers. This is
not a promise against arbitrary trusted connection code deliberately replacing
every main source with an indistinguishable schema/data set. No trace hook,
authorizer hook or deprecated SQLite API is installed by production code.

## Original first-book input

When a claimed C25/C26 finds no learning Entry, actual bootstrap produces its
normal original output, binds its private WorldResponseWrite and holds input.
Only the learning owner can privately park that current original GAME job once.
It retains the original work, records, input lease, receive epoch and ticket;
there is no copied gameplay request, new TTL or public raw-wire replay API.
NET resumes only after physical Written and Released; GAME rechecks the exact
Entry/material, service lifetime and INIT before invoking the same original job.
The original full preflight and debit then run normally. Failed output, close,
release, stop, replacement owner and a second defer cannot debit/retry it.

The returned canonical remains the pass5 one-use actual ReturnContinuation plus
private Session old-to-new INIT chain. Pet42..44 are read freshly from their own
store when preparing the next member; they are not copied into0092 or adopted
from a stale learning token. C24/C28 do not mutate the inventory/equipment/deity
readset, and therefore do not invent a joint material successor. Existing real
bank/movement joint edges, learning publications and C67 successors continue to
advance their own complete graph. Native panel updates retain existing exact
families; no S30 replay, fake pet or ignored stale check is introduced.

## Regression source and limits

test_owned_companions includes whole-batch domain checks, final-read retirement,
unexpected third-cell writes, caught same/different-facade reentry, actual PK/PvE
claims, main-rename/TEMP-view replacement, and both COMMIT STMT and successful
COMMIT PROFILE retirement/write cuts. STMT is explicitly pre-execution;
PROFILE cases cover the separate post-execution durable cut in source.

test_pet_reserve_move exercises the actual shared save with final read failure,
PROFILE durable retirement/write, C24-to-C28 same/different-facade reentry,
main-rename/TEMP-view replacement, claims, full population preservation and
existing reserve wire preparation/rollback cases. Learning graph source cases
cover activation and reserve reorder without retiring unrelated full material.

test_session_state uses real private Session/learning bootstrap receipts for
first C25/C26, verifies identical original record address and one resumption,
then real learning/C67 successor. Release and duplicate-defer cases debit
nothing. Existing returned/NoEntry fixtures remain separate source cases;
these do not constitute combined native runtime or full App acceptance.

All regression source remains unexecuted. Native pet unlock/acquisition,
growth/formulas, arbitrary catalog variants and whole-server acceptance are
not established here. Missing explicitly configured profiles remain fail closed.
