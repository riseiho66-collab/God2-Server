# Common movement commit to TW/CN native peer publication

The owner resumed work on2026-10-07 after the sealed null-slot round. This round
connects the existing CN adjacent movement/shared-position source to concrete
version-native peer5E projection and actual TW/CN send APIs. It adds three C++
files and modifies three existing C++ files. No builds, tests, asset loaders,
Lua, client/server, production database or deployment execute. Native fonts,
Chinese text conversion and frozen TW behavior remain unchanged.

## Native wire difference and recovered consumption

Pinned CN582f2695 has fixed logical5E size17. WORLD0048FCC0's branch begins
00490BF2 and ends00490CFE. It reads the exact low16 identity at logical+1,
11-bit X/Y from logical+9, the low7-bit driver selector at logical+3 and the
high7-bit auxiliary selector at logical+9 bits25..31.00490C4A passes the
body at logical+1 to00532800. This receiver searches128 actor entries by
exact low16 identity, preserves previous display coordinates, appends X/Y to
the native40-slot interpolation ring when not full, and applies body+4's
low16 state only when changed.00530410 reads the same exact identity and
returns the previous display-coordinate pair for companion visualization.

WORLD then reads logical+5 bits30..31. Branch1 marks the linked14-bit handle
with8000 and uses logical+13; branch2 marks it with4000 and supplies zero
to the visualization call; other branches preserve the14-bit handle and
use logical+13. These are actual client consumption branches, not recovered
server mount rules. Bytes14..16 and every unresolved bit remain retained.
The reader exposes raw selectors/state only, with no direction inference,
monster stats, equipment authority or manufactured mount fields.

TW149c1b45 has fixed logical5E size13. Native69A60..69B33 reads the same
low16 identity and11-bit X/Y;4FB520/4FC920 enqueue the projected coordinates.
TW's resource/mount consumer differs and has no CN logical+13 field. We read
the exact pinned mapped image through the finalized verified=true archive
without restoring the history/build tree. The additive TW helper changes only
bits0..21 at logical+9 and preserves all other bytes/bits. No existing TW
visibility code, configuration or runtime path is changed.

## Source route and ownership

SharedMovement::WorldOwner::authorize now supplies an Authorization containing
the full native5D and the real owner's already-visible recipients with complete
native5E snapshots. There is no default5D, ring-index echo, all-peer fallback,
new visibility policy or template builder. SharedMovementPublication prepares
all recipient-specific records before the existing common position CAS.

Every supplied recipient must hold an active current lease in the same
SharedWorldPresence registry. Actual socket/session/account/character identity,
world readiness and current same-scene position must match. Duplicate/self
recipients fail before position mutation. Templates must match the source's
actual reserved actor handle and old committed coordinates. TW uses its exact
13-byte record; CN uses17 bytes. X/Y outside11 bits fail this scoped route,
without truncation. TW destinations also require the source handle to fit its
native spawn's12-bit identity; automatic alias allocation is not invented.

The private move-only prepared publication captures this publisher identity,
source lease, exact old position revision, destination and copied output records.
SharedMovement rechecks the candidate together with the actual WorldOwner
immediately before the common persisted-position CAS. After actual actor/cache
publication, deliver requires the exact stored committed position and newer
revision, rechecks all recipients before the first send, and invokes each real
version's transport. It is consumed once even on partial submission failure.
The final supplied5D remains after actor/cache publication and peer submission.

The existing committed-position failure behavior remains: release/close the
mover and retain durable state for fresh recovery; do not rewind a position that
a peer may already have observed. True from deliver means that synchronous send
APIs were submitted; asynchronous queue acceptance, network receipt and native
rendering are not observed. Socket writes remain asynchronous and no game-owner
callback runs between final recipient checks and submissions.

## Scope and remaining work

This is one new conditional, unhosted source chain and CN WORLD5E binding, not
a completed mixed-world route. Actual WorldOwner, visibility/spawn/template
authority, movement timing/pending/reset/full5D suppliers, cache/position atomic
lifecycle, TW enrollment in common presence, login/bootstrap, Application and
listeners are still required. Existing TW CUSTOM0027 membership is deliberately
not mistaken for common ready leases. The new projection can serialize either
version for a CN-origin committed step; TW-origin routing remains open.

All state-changing appearance/mount variants, nonadjacent/path/transfer/battle,
larger coordinate/handle mappings, dynamic actor/resource revisions and the
full directional/phase/state/variant/indirect/deferred denominator remain open.
Full bidirectional route increment0; full game total/completed/percentage null.
The previous stop record is retained as history and the latest execution plan
records the owner's explicit resume instead of starting another goal.
