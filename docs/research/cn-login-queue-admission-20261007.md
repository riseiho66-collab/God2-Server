# CN login and world admission queue completion

Phase 1 source integration, 2026-10-07. No compilation, test, native/server/Lua
execution, asset loading, database access, migration or deployment. Native
formats, complete opaque source requirements, text conversion, authentication
verification, TW frozen routes and levels stay unchanged.

## Concrete gap and resulting source behavior

The old account composition completed the held credential read immediately after
calling void send for1D, each directory aggregate and0A. Those calls only posted
work to the network strand. They did not report whether its bounded queue could
accept the entire sequence. World00-to1F and1A-to02/2A had the same distinction:
constructing/installing an owner was treated as output queue acceptance.

CnTransportSession::send_batch now takes already complete native aggregates.
It reserves their pending frame slots, validates each existing0xA00 logical
limit, and prepares all encrypted frames plus a replacement output deque on the
network strand before publishing the whole batch. The existing256-frame and
1MiB wire-queue budgets stay operational bounds, not native game rules. Existing
queued frame order and each native frame's key/checksum/framing are preserved;
no records are split, no S2C length table is reused for C2S, and no new opcode
is introduced. The unchanged CnTransport encoder is const and starts feedback
from its existing per-frame initial_previous value.

The queue completion is posted once to the serial game executor. Its work guard
keeps that executor's work outstanding until the result is handled. Rejected,
closing or capacity-exhausted submissions fail and close; a failed post does
not mark a completion successfully posted. Ordinary send uses a one-aggregate
batch without a user completion. This is source implementation only; scheduling,
allocation failures and shutdown still require the later comprehensive phase.

## Three existing native continuations

| Existing request / phase | Complete supplied output | Queue result and authority before the next read |
|---|---|---|
| CN Account04 | 1D, ordered04/05/06 directory aggregates,0A | SharedAccountSuccess checks the same authenticated connection, account, grant generation and current deadline. confirm_account_success_queue clears only that connection's unpublished grant marker. compose_native_login no longer acknowledges from attach's returned pointer. |
| CN World00 | 125-byte1F | SharedWorldSelection keeps credential ingress suspended until its queue completion, then rechecks original account offer bytes, ordered common IDs and current character ownership. |
| CN World1A | One complete02-before2A aggregate | SharedWorldSelection rechecks the exact pending character, ready owner, stored position/handle and normal-scene snapshot. SharedWorldPreparation then rechecks its common presence generation and actual reservation before completing1A. |

Neither account/world attach's returned owner nor install_selected_ingress's
true return value is native success. The latter means a queue result is pending;
the preparation owner must not also complete1A synchronously. Failure releases
only the generation-qualified visibility/presence lease and actual reservation;
the existing ReleaseOnce guard prevents duplicate reservation release.

Unpublished account output has a separate cleanup marker. A transport can close
before its queue callback reaches game, so callback-only revoke was insufficient:
account detach could already have cleared the owned account_session. Cleanup now
revokes that exact unpublished grant before detach. Once the entire success
sequence is queue-confirmed, cleanup uses the original detach behavior, preserving
an account's selected handoff for its independently authenticated world socket.
World ticket release retains its existing exact generation/reservation scope.

Queue acceptance proves local queue ownership only. It cannot prove that all
bytes were written to TCP, received by the client, passed the client-local0A
mutex gate, or became a playable world. A later disconnect may interrupt any
TCP sequence; this change does not make socket delivery atomic.

## Native provenance and remaining suppliers

Pinned CN image:582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8.
Account0047FE30 receives1D/directory/0A; native0A copies all16 billing bytes and
then passes its separate local mutex gate. Preserve prior
cn-account-success-owner-01 and cn-billing-byte5-agent-01 evidence.
World00444EC0/0044D240 consume1F through the existing normal/transfer paths;
004813C0 produces1A,0047E4D0 consumes status02, and00481190 consumes begin2A.
Prior cn-world-selection-owner-01 and cn-selected-world-preparation-01 evidence
remain immutable. No new machine-code finding is claimed by this queue change.

Actual seed,1D/billing0A/summary07/full1F/status02/begin2A values and their
account/character lineage remain required. This source never zero-fills opaque
fields, reflects04 as issued1D, generates a success key, selects billing paytype,
or fabricates a spawn/actor handle. Actual allocator, bootstrap, rules, scene
controls, transfer lifecycle, TW common-world admission and production plan are
still incomplete. The ordinary entry remains inactive for CN and web hosting.

Accounting:10 existing C++ source files modified;3 existing completion chains
extended. New native opcode/phase/variant bindings0, new complete bidirectional
routes0. CN25/TW2 partial unhosted owner chains and CN63/TW8 source bindings
remain unchanged. Whole-game route total/completion percentage remain unknown.
The source snapshots, callback path graph and prior provenance are saved in
artifacts/integration/packet-connections-20261006/cn-login-queue-admission-01.
