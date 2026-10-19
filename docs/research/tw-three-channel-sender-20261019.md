# Original-run sender custody for the three-channel native path

Round495 continues CUSTOM-0159 and the full Taiwan-only goal. It implements
Session transport custody needed by the Common53 native action bridge. This
does not activate native guild mutations, select the three-channel default Main,
or certify selectable/switchable channels in the original client.

## Actual transport connection

WorldReplyPushCapture is scoped to the actual GAME world-record callback. A
trusted supplied WorldReplyPushWire runs synchronously for the same Session;
there is no default encoder or inferred native peer/cipher qualification.
Only explicitly captured plain world-record pushes and acceptance pushes for
that Session join the capture. Other Sessions and ordinary unspecialized sends
outside a capture retain their existing paths.

The profile must return one bounded original envelope of logical.size()+3 bytes.
The capture retains each qualified wire frame and original full64 delivery tuple,
not shared_ptr identity: the actual Common sender rebinds equal tuples per send.
It retains each pending original acceptance callback and producer reservation. finish(relative
output offset) registers an exact fragment at the current outer reply base and
returns the original bytes for insertion at that native run position. The
caller must append those bytes unchanged. Neither matching bytes found by
search nor a selected channel label manufactures a private fragment receipt.

The actual Session final callback verifies complete indexed slices and source
identity before NET handoff. The final NET producer verifies its exact complete
wire/current delivery tuple, retains reservations on the actual Write, and
settles original callbacks at the documented FIFO insertion/metadata point.
All three original enqueue branches remain covered. This is Enqueued only;
Written, callback admission, native client ACK and UI publication stay distinct.

Reject, invalidation, close, throwing/dropped posts, bad offsets/wire and source
changes cannot leave acceptance callbacks pending forever or report success.
Callbacks are once-only and retain original source order; callback exceptions
cannot skip later settlement. Per-emission producer bytes/counts survive until
the actual combined Write is removed. The existing NET queue byte/entry budget
still checks the complete final response. Combining frames does not waive
producer accounting or invent atomic remote delivery.

The GAME-only framer and borrowed source closures are not carried to NET in the
pure transport receipt. Explicit scope reentry/framer reentry invalidates the
active capture. A retired capture cannot fall back to direct side sends within its active scope.
A stale finished handle can affect only its own old window/pending work and
cannot invalidate a successor callback or a different active capture.
Observed WorldRecordsWrite and C67-tagged side pushes are refused inside this
new scope, rather than manufacturing their unrelated private provenance.

## Existing provenance and policy

Captured logical sends keep their original GAME status invalidation. Callback
activity is accounted for without creating nonexistent independent side Writes:
the existing WorldCallbackOutput final component represents the real final
Write. Generic receipts are independent of private C67 claim/emission tags.

Deferred C67 insertion must preserve generic fragment ranges and move their
offsets with the actual materialized final reply; insertion inside an immutable
captured fragment refuses. Preexisting exact whole-response observations remain
immutable and conflicting final bytes refuse. No copied native input span,
new native command, SQL grant, automatic input hold or fabricated ACK is added.

The existing full Session response codec gate remains in force. Passing it or
installing a framer callback is not proof of an original native cipher profile.
An actual trusted provider must supply that build/peer provenance before use.

## Future verification and remaining connection

Future C++ cases use an actual DB-free Session socket/login/select/world-tail
fixture with an explicitly labelled test framing profile. They exercise actual
TLS callbacks and FIFO bytes rather than mocked receipt metadata. They are
registered for later verification, not built/run during PHASE1. Cases include
high64 tuple changes/equal rebinds, prefix/plain/Accepted/suffix FIFO, another
Session, once-only/throwing ACKs, empty/relative scopes, stale finished handles,
framer throw/reentry/null/length, offset bounds/tamper, observed push refusal and
producer count limits. They do not execute every admission/normal-response or
C67 coexistence branch, simulate every allocation/post drop, or prove host abort
drain; those require later concentrated verification. Source review
and test source do not certify live gameplay, packet delivery or native UI.

Next mount original-batch Common53 capture/selected-index dispatch in the actual
native mixed handler, with exact Session/world lease, full-batch Current,
original run indices/budgets, sender capture finish offset, active cancellation
and frame/DB lifetime. Deep Common/admission continuation fencing must include
nested fresh captures and every callback path. Later bootstrap/menu continuations
outside the initial capture need the same qualified sender transport profile.
These remain open; transport capability alone is not a native action route.

Default native providers/Main, common64/native actor projection, older guild
bridges, selected Web G, native transfer/save/logout/admission/recovery, all six
channel-switch directions and current-client own-server acceptance remain open.
Full gameplay/formula/SQLite/MySQL obligations persist. No full-game route credit;
denominator/percentage unknown and goal active.

PHASE1 source/static only: no build/tests/Lua/native/VM/codec/game SQL/schema/
migration/import/export/activation/deployment. Reuse the matching unchanged
current-client REA evidence; no new binary behavior is inferred by this source
implementation. Preserve current EXE/BIN and custom126/150.
