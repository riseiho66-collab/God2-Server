# CN complete native03 and terminal write-before-close source

PHASE1 source/PE recovery only. No build, test, client/server execution,
production DB access, migration or deployment. Previous goal turn is progress:
it implemented current native19/common identity resolution and owner rechecks.
This round supplies a missing terminal transport prerequisite and new bounded
primary03 return/caller evidence, not a native reply issuer or completed route.

## Primary format and distinct consumers

Pinned CN SHA256:
582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8.
00567B50 range-checks opcode<=FE and jumps through00567CA4. Index3's DWORD at
00567CB0 selects00567B69: MOV EAX,3; POP EBP; RET. The logical03 record therefore
contains opcode plus two payload bytes. This pre-existing table fact is reused.
0047D8D0 first reads opcode, obtains that length, and reads remaining bytes before
returning0.00480B10 waits for a complete03 and then locally returns0/clears flags;
it does not inspect either payload byte. Their semantics/issuance remain unknown.
Ignoring payload bytes cannot justify an opcode-only or zero-filled reply.

An independent world-dispatch branch is now captured from primary bytes:
0048FD66 jumps through004929D8 with opcode inESI, bounded<=FD. Index3 at004929E4
selects00492936. This epilogue sets EAX8 before its cookie check/RET4, and reads
no03 payload. Retained decompiled C omits this return value. The known caller
0048B180 then subtracts4,3,1; original EAX8 takes0048B198's004AC020 call and
EAX1/exit. This is a different phase result than the pre-world waiter's0; neither
8 nor0 is a recovered value to serialize into03. Cookie/callee execution and
all indirect/state variants have not been run or globally exhausted.

CnPreWorldCloseReply preserves an entire actual3-byte03 record. Its constructor
is private, read() requires exact size/opcode and copies all three bytes, and
record_bytes() returns the retained record. There is no default ACK generator,
payload meaning, inferred success field or reason-to-word conversion.

## Required final output and exact world ownership

Existing close() clears output immediately. Queue acceptance alone cannot
ensure a required terminal native reply is written before that cleanup.
SharedCredentialConnection.close_after_native_world_reply now requires a complete
native03, mandatory actual terminal-owner predicate and write completion.
It checks current authenticated World role/account/session and exact committed
admission ticket before queueing, then repeats owner/identity/ticket checks on
the game executor when the existing send_batch callback returns. No incoming
slot/name/reason supplies the phase predicate. The actual operation owner must
hold ingress suspended and quiesce its later output until completion.

One terminal_world_reply_pending_ guard prevents a second terminal submission
from queuing a duplicate reply or cancelling the first merely for repetition.
The caller-owned complete record passes through unchanged native encryption and
framing. After successful queue acceptance it invokes transport drain_and_close.
The terminal callback reports local TCP write completion, distinct from the
earlier queue callback and from peer receipt or native client acceptance.

SharedWorldAdmission.world_owned checks exact current WorldOwned stage, grant
generation, world session and reservation. The connection exposes that ticket
query for the terminal path. It does not require a still-valid character offer,
which a real deletion transaction may invalidate before0204. Existing offer,
character and account queries retain their behavior; no ticket is reissued.

## Drain lifecycle and failure ownership

The additive Draining state and atomic drain_requested flag prevent further
logical ingress/output once the drain is requested. Existing accepted output
retains its frame order,256-frame/1-MiB budgets and immutable buffer ownership.
An already pending async_write continues; no duplicate front-buffer write is
started. When the queue empties after successful writes, the transport posts
the one-shot written(true) callback to game and then follows its existing socket
close/OnClosed cleanup. An already empty queue is likewise locally written;
this does not assert that the client read the bytes.

Forced close, socket error, rejected ingress or a20-second drain deadline ends
through written(false) when still pending and the same cleanup. The20-second
value is an operational drain budget, not an official game wait/auth deadline
or reuse of the client's30-second timer. A drain requires all earlier accepted
queue operations resolved; outstanding executor-send requests at transition
fail rather than silently counting unsent data as delivered. Callback posting
uses the existing game work-guard and an atomic once flag. Intentional closing
does not convert a completed local write result into a queue-acceptance failure.

Only this connection's existing AdmissionCleanup releases its ticket/scene
owner; no other account, browser tab or newer grant generation is detached.
Ordinary account C2S0A remains a no-reply terminal request. This increment does
not change native packet widths, text conversion, levels, fonts, save schema,
databases or the four existing browser routing paths.

## Scope and peer handoff

The actual0200/0204 ingress/phase/operation owner and03 supplier are still absent.
No caller yet installs the new terminal path as a playable/native close handler.
The source API is conditional infrastructure; it cannot invent the missing two
bytes, native reason rules, save ordering, deletion authorization or other03
world-dispatch variants. Native19 still needs its real rule/online-owner/CAS/
atomic save transaction, duplicate owner and pending-offer invalidation, full
02/1E data and qualified1E continuation. Formal source composition/hosting remains
open. Centralized later tests must cover drain/forced-close/deadline/queue races;
none were run in this phase.

The authorized web peer reported source-only complete2A appearance resource
loading, TW HeroDoll/Drv lookups and per-world bitmap cancellation/release.
Its frontend tests/resource hashes remain frontend evidence, not server native
acceptance. CN resource tables remain missing and cannot be substituted withTW
tables. Receipt was acknowledged in the authorized peer chat; server protocol
widths/endpoints and the peer's frontend-only ownership remain unchanged.

Accounting: one terminal write source chain, one exact committed-ticket query
and one read-only03 view; zero new hosted controls/phase bindings or complete
bidirectional gameplay routes. TW/CN C2S156 each; TW supported S2C lengths252;
CN S2C account6/world206/battle68. Whole-game total/completed count/percentage
remain null. Primary metadata spans and source snapshots are sealed separately;
no historical acceptance/import/packet baseline is overwritten.
