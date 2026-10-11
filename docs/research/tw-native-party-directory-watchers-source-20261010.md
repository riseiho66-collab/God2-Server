# TW258: owned party-directory watcher propagation

Phase1 source connection only. No build, compiler, tests, game/native runtime,
codec execution, game database/SQL execution, migration, activation or deployment.
TW256 directory and TW257 detail/consent receipts remain immutable history.

## Native consumer boundaries

This source reuses four exact retained TW256 consumer spans, 469 bytes and
182 instruction sites, rather than claiming new global native coverage or new
opcode discovery. The pinned image remains
`149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.

A7 is the complete directory list. Its retained successful copy path at
4D2F80..4D3038 replaces the A7 bank and clears the 94-byte AB detail bank after
an opaque refresh call. This local presentation effect is distinct from
authoritative party consent or server-side pending offers.

A8 logical3 contains a target WORD. The retained prefix at 4D3110..4D317C
removes the first matching visible A7 row, shifts later 44-byte rows forward
stably and decrements the count. A missing ID is a no-op. Later GUI effects
outside that retained prefix are not claimed recovered.

A9 logical27 contains target WORD, flags BYTE and CString23. The consumer at
4D3190..4D31F9 updates flags and copies text **through its first NUL only** into
the A7 row's 22-byte description. It does not clear or replace the old post-NUL
tail. The native copy has no local safe bound; the source policy keeps text at
most20 bytes plus NUL. A9 is an exact delta only if its resulting full22-byte
description equals the desired row, including the retained tail. Otherwise a
complete A7 is required. A23-byte source field is not permission to overflow
the22-byte destination or discard opaque query bytes.

AA logical5 updates the first matching row's flag BYTE; its last BYTE is not
directly read in the retained consumer. CUSTOM-0097 uses canonical flags0 and
there is no qualified independent flags-changing event. This increment does
not invent an AA trigger to increase packet counts.

A8/A9 do not establish the same detail-bank clearing effect as A7. Private
detail/join observations must be invalidated when their relevant source
changes; a full A7 is used when the native detail also needs clearing.

## Explicit CUSTOM-0099 watcher policy

The existing transient, opt-in directory supplies actual watchers from its
owned queries. Each watcher retains the exact Session incarnation, full common
account/character mapping, captured private normal2A observation, current query,
page, actual visible native handles and issued identity tombstones. A public
WORD or newly found weak Session cannot replace that source.

The planner prepares one copy-on-write state and a bounded set of recipient
deliveries. It tracks actual issued description22 bytes so A9 eligibility is
about the client's previous cache material rather than an assumed server row.
A8 applies only to a truly visible same-owner withdrawal. Description-only
updates may use A9 when all other presented fields and retained tail match.
Additions, order/page changes and other structural changes use complete A7.
Issued identities remain tombstones until query retirement; the same WORD
cannot silently be rebound to a different owner. A8/A9 require both no private
detail and no last_join_request: successful C91 consumes the private detail but
may leave the native AB cache visible. A row change then uses A7 to clear it.

C8F publication/update and C8D2 withdrawal propagate their actual directory
changes. C8D retires its exact own query/detail immediately, and mode2 also its
own listing, before any other watcher observation or plan. Failed fanout cannot
retain those rights after window close. World-ready and disconnect attempt
watcher reconciliation and fall back to exact own retirement on failure.
Ordinary handler runs must
participate too: movement, scene changes or battle entry cannot bypass cleanup
merely because the batch contains no directory request. The original handler's
result and framed reply order remain authoritative and preserved.

Recipient logical aggregates, framing geometry and fanout capacity are prepared
before publishing the directory state. Each actual recipient is strongly held
before observation. Private initialization is checked on its recorded game
owner before reading Session-owned identity; common name/role/position and
query observations are reread, then all pure owner/phase/closing/battle/entry
fences follow all observers. Publication requires the exact expected directory
snapshot and unchanged NativeParty state. Every source in a prebuilt caller A7
must still match its second observation before the caller is skipped in fanout.
Missing or stale source retires the exact affected query, without
removing a successor Session or fabricating a replacement source.

Queries, listings, issued maps and recipient fanout use the actual max_sessions
bound; visible rows remain bounded by six. No unbounded retry or duplicate
publication is introduced. Frozen NativeParty pending/answer/roster behavior
and TW257 failed-C90 revocation remain intact.

## Transport and completion limits

One query's foreign-owner issued-WORD tombstone, capacity or framing conflict
can reject the whole watcher plan. It is not automatically retired in isolation;
refresh and new publication can remain delayed until the query is retired.
Ready/disconnect fallback can remove the departing source while other watcher
refresh waits for a later actual event. These remain incomplete variants.
Membership-only native AB refresh after consent, without a directory row change,
also remains open; row-change fallback is not proof of that complete lifecycle.

Ordinary Session.send_world_records encodes and allocates on its IO strand.
Game-side pre-encoding is a geometry/preparation step, not a guarantee of zero
allocation after commit. This path is submission, not held publication,
current-at-release, atomic delivery to all recipients, socket Written or native
acknowledgement. Post-commit failure may leave a delivered prefix; it must not
roll back or retry as if nothing was sent. Failure handling is tied to the exact
query/Session incarnation. Existing common-world held APIs require their actual
presence grants and cannot be borrowed by renaming an ordinary directory send.

Original server discovery/filter/lifecycle/status policy, AA event semantics,
general common64/native identity adaptation, DA-after-entry appearance,
post-battle native identity renewal and the remaining TW gameplay routes remain
open. Whole TW directional/state/variant denominator and completion percentage
remain unknown. Source increments are separate from activation, deployment and
eventual native-client acceptance.

Preserve shared CN/web sources, accounts/saves, chat/filter, IME, authentication,
native fonts and text conversion. Evidence:
`C:/Users/risei/.codex/artifact-archives/god2-server/20261010/tw-native-party-directory-watchers-source-258`.
