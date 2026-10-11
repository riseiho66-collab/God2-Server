# TW261: isolate party-directory watcher projection conflicts

Phase1 static source only. No compiler/build/tests/runtime/native/codec or game
database/SQL execution, migration, activation or deployment. TW256..260 archives
remain historical. The full TW/CN/web goal remains intact and TW is prioritized.

The existing watcher returned no whole plan when one query encountered a reused
native WORD tombstone, duplicate/own handle, invalid row description, projection
format or issued-capacity conflict. That could suppress another query's A7
invalidation after relevant membership changed, despite its own source qualifying.

CUSTOM-0102 stages each query in a separate copy. A failed intended projection
restores the exact pre-attempt query before preparing a conservative empty full
A7. Its logical bytes are `[A7,05,00,00,00]`: five bytes and zero rows. The native
qualified successful A7 prefix accepts the zero-count length/count geometry and,
if the preceding opaque4D4540 call returns normally, reaches the94-byte AB clear.
Opaque4D4660/3650 and rendered effects remain unqualified. This is a custom conservative
display policy, not a successful intended list, native ACK or original server rule.

The fallback retains every issued-WORD owner tombstone and the original query
material. It resets page0 and clears visible rows, description cache, private
Detail, issued AB Presentation and last_join_request only alongside the prepared
empty A7. The original current recipient source and all existing publication
fences remain required. Other queries continue projection in the same COW plan.

An already source-recorded empty baseline (page0, no visible/description cache,
private Detail/Presentation or last join) needs no repeated empty A7 on ordinary
packets while the same conflict remains. The first required clear is never skipped
when any such material remains. This is source-output idempotence, not client
delivery acknowledgment or retry recovery. Tombstones are not reset by an empty
clear or ordinary re-query; foreign owner reuse remains rejected until actual query
retirement supplies a new ownership ledger.

The Application caller path also reconciles actual current directory state after
its direct prepare fails. It does not publish that rejected request's attempted
listing mutation. A previously registered conflicting query may receive the
conservative empty A7 while other qualified watchers can refresh; an unregistered
query is not fabricated merely to provide a success packet.

Independent static review found that the newly added failure reconciliation
could reenter the directory observer while the wrapper still returned earlier
wire output. Refinement2 immediately checks dispatch->reentered after that call
and returns unavailable, matching the existing ordinary-run reconciliation edge.
The first candidate and this finding are retained as immutable evidence.

All TW260 old-private-entry guards and the separation of private C91 authority
from retained AB presentation remain. Normal A8/A9 eligibility is unchanged;
those deltas cannot substitute for the clearing A7. No new opcode, configuration,
NativeParty rule, Session API, client patch, table, activation or deployment is
introduced. Frozen chat/authentication/IME/fonts/conversion/saves and CN/web remain.

Global snapshot/membership CAS, invalid whole-map sizes, foreign owner/readset,
current entry, allocation, total fanout/framing and ordinary IO failures can still
reject/defer the whole publication. No all-recipient atomic delivery, held send,
Written/ACK or rollback of an already submitted prefix is claimed. Post-battle
private entry renewal, native/common64 mapping, original server policy and opaque
native GUI descendants remain open. Source progress adds no opcode or complete
whole-game route; the whole TW denominator and percentage remain unknown.

Actual source delivery: two existing C++ files, no new C++ file; before688,784
bytes, final691,216 bytes in refinement2. The first candidate691,145 bytes remains
retained. One per-query watcher
isolation branch and one existing direct-prepare-failure reconciliation edge;
these are not new opcodes, request/reply registrations or complete gameplay
routes. Mixed source records245 to246. C2S candidates156, world parser74,
partial gameplay C2S50, limited reply48, source push11, world S2C formats252
and battle index110 are unchanged. Goal mode was actually active at round start.

The old TW258/TW260 whole-plan conflict limitation remains preserved in historical
documents. This round narrows that limitation for the specified deterministic
per-query projection failures only; it does not remove global publication or IO
failure, supply a retry acknowledgment, or prove current native client acceptance.

Evidence:
`C:/Users/risei/.codex/artifact-archives/god2-server/20261011/tw-native-party-watch-conflict-isolation-source-261`.
