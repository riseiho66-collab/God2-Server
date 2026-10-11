# CN ordinary17/18 designated operation ingress

PHASE1 source integration only: no build, tests, native/server execution,
database access, migration or deployment. Levels and all frozen TW/native
features remain unchanged. Previous goal turn made concrete name-producer and
resource recovery progress and sealed catalog68. This round uses those and
earlier native mutation/choice records rather than rediscovering their formats.

## Actual source changes

Added SharedCharacterCreateOperation.h/.cpp and connected it to the existing
SharedWorldSelection receive path and SharedLoginSources/compose_native_login.
CMake's existing recursive src/*.cpp source selection includes the new source;
no build was invoked. The optional source fields default to absent, preserving
existing callers and leaving unavailable native creation unavailable.

The two new conditional source owner chains are:

1. Complete ordinary C2S17 ->current offered07/queued1F ->designated request
   owner/common account/exact world ticket ->required actual create transaction
   result ->complete23-byte native02 ->native send_batch ->queue-owner recheck.
2. Following C2S18 ->the same retained17/current created common character/actual
   offered choices ->SharedCreationLocationIdentity ->required actual choice
   transaction ->complete3-byte native18 ->native queue ->committed-owner recheck.

Both actual supplier functions are required. A parsed request, wire name,
client UI filter, routing index or true local queue callback supplies no native
gameplay permission. No copied TW40-byte profile creator, Lua defaults,
zero-filled native reply, SQL writer or unconditional success is added.

## Identity, storage and state ownership

The operation scope holds verified common account, lifetime-unique world
connection ID and exact shared pointer to this17. A new retry request receives
a new pointer and replaces the designated owner. Equal bytes are not operation
identity or persistent replay handling. The actual writer must enforce semantic
duplicates/replay and atomic CAS in storage; that implementation remains open.

Before the writer, the controller retains the actual account's existing common
IDs. A status0 source must provide a newly committed common row that was absent
from that snapshot, remains uniquely owned by this account, and exactly matches
its supplied row through02 queue acceptance. Raw common fields are compared,
not interpreted as native CN stats/appearance or converted from TW profile.
The transaction's actual nonempty permitted choices are retained with their
order and must fall in the recovered reference domain. The18 input cannot make
its own allowed set, name an arbitrary character or borrow another operation.

Before the18 writer, the existing identity resolver rechecks this request,
actual created row and source choices. The actual writer then consumes its
exclusive pending state under a real revision/CAS and supplies a current
committed result. After that write, the controller deliberately does not compare
the stale pre-choice row; it checks the committed source's predicate and unique
common account/character ownership. The result predicate also receives the
actual18 byte's low3 native slot, which the writer must associate with the common
ID. It is not inferred from common slot, DB ID, ordinal or packed location word.
No requirement to know this association before the choice transaction is added.

Predicates run on the serial game owner, observe actual operation state and
must remain valid for the documented queue phase. Their captures own needed
lifetimes; synchronous sources must not retain borrowed Scope/identity references.
They do not replace an actual writer's lock, transaction, CAS or durable replay
record. A close/queue failure stops this connection; it never silently deletes
or rolls back an already committed saved character. Required durable pending
operation/recovery behavior still belongs to the missing real storage owner.

## Qualified native continuation and limits

Retained 0043D280/0047E900 producer and0047DCC0 consumer establish ordinary17
and fixed02. Status0 continues18; status31h takes its distinct name-collision
retry UI; other nonzero results use their distinct terminal/reselection path.
The source preserves all02 bytes. It changes phase only after native queue
acceptance and rechecks exact scope/current source/new row. Other nonzero
variants do not automatically become retries or successful operations.

Retained0043D472 sends18,0047DB70 consumes18;0043D4AC..B4 copies its first
payload's low3 bits to the cached last07 row before0200/account0A. The second
18 payload byte remains opaque and supplied in full. The new operation does
not synthesize it, rewrite07 or select1A on this world connection. Special1B is
still a different producer/continuation and cannot borrow ordinary17's owner.

The quiescent operation can pass into the existing required-source pre-world
close controller. Creating/choosing/queued phases cannot yield to another
terminal operation. Terminal close still needs actual operation/rule state
and complete native03; a parsed0200/0203/0204 alone is insufficient. After a
real commit, current ticket ownership is checked independently of the old07
offer, which may legitimately have been invalidated. No existing selected-world
dispatcher, credential verification, TW behavior or transport framing is changed.

New source owner chains2; phase/direction/opcode source bindings4 (three new
distinct values because world-selection S2C02 already had another source).
These are unhosted conditional paths, not completed native gameplay routes.
Actual shared create/choice rules and transactions, native02/18/03 issuers,
native19 delete storage/02/1E, Application providers/hosting and native acceptance
remain open. Whole-game denominator/completion percentage stay null. The source
delivery snapshots old sealed evidence without altering its historical claims.
