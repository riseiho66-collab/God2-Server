# CN native path completion and5D distinction, 2026-10-07

Previous goal turn was progress: native prior-frame elapsed/post-frame timing
source sealed under catalog27. This round connects actual005395E0 path
completion ordering into that existing source and recovers5D's empty/pop/sign
behavior. No new opcode, partial owner chain or complete route is counted.
Actual runtime path/deferred notification/segment/reset suppliers, server
permission/full5D and formal Application hosting remain open.

## Separate native events

Pinned CN PE SHA256:
`582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8`.

005393B0 advances renderer camera pixels from elapsed/velocity/residue; only
both axes complete return1.005395E0 at0053961F compares that result to1. If
incomplete, native returns1 without path advancement. A full native path finish
returns0 instead; these native function returns are NOT server5D values.

For both-axis completion,00539624..00539642 first consumes an actual pending
notification at owner+89B244 through005385F0 using+89B240 and clears the pending
flag. It then reads actual path count+38 and increments cursor+34 at0053964F.
No new guessed path or default empty notification is supplied.

If incremented cursor>=count-1,005396AB..005396E0 sets actor target+224/+228
to the LAST native path point, sets state+30 to0, invokes00537800/0047FE20,
and returns0. Its address expressions+34+count*8/+38+count*8 refer to actual
point[count-1], not an extra point[count]. Reading past the actual path would
incorrectly mix path state and camera fields.

Otherwise0053965C..00539676 invokes00539150 with point[new_cursor],
point[new_cursor+1] and actual ring write byte+236. Only a successful call then
sets target to point[new_cursor] and invokes0047FE20. Failure executes actual
00539BF0 reset and still leaves005395E0 return1; no server-reply byte is inferred.
Next-segment native2E sending still precedes its local ring-full check.

## Actual bounded native path

00535D80 at00535E0C supplies0x3C (60) capacity to004866A0, with count+38 and
point array+3C. Sixty pairs end exactly before camera+21C. Its alternate
pathfinder/append branches and out-of-buffer append variants remain recovery
work; the new source never extrapolates missing points or replaces them by zeros.
005375C0 can replace a path during an active segment: it retains the actual
current starting point, seeds count1, builds from the actual next point and
sets cursor0 without beginning an additional segment. That case cannot be
reconstructed solely from the shared server's latest saved position.

`CnNativePathCompletion` consumes exact actual cursor, count and all active path
points AFTER native deferred-notification handling. It qualifies representable
in-buffer counts1..60, cursor0..count-1 and exact point count. The pure plan
supplies cursor increment and either native finish target/return0 or next
segment/success target/return1. It creates no C2S/S2C packet and grants no move.
Malformed/count0/wrapped/overcapacity and unknown path/reset variants stay open.

## Source lifecycle integration

On a completed renderer frame, `SharedNativeMovementScene` now requires actual
deferred/path and native path-publication callbacks BEFORE mutating camera/cache.
Incomplete frames do not require or invoke them. After camera/native model
publication, it invokes actual deferred-notification handling and gets the real
current path snapshot, computes the bounded plan, and publishes through the
actual native segment/finish owner. Only after those stages does the existing
post-update clock observer sample new ticks for the next frame. Every stage
rechecks the same ready connection/common lease and guards callback reentry.

No default runtime callback is provided. Native segment/ring admission/reset,
actor/model targets and path cursor publication remain with their actual owner;
the plan does not claim these callbacks implemented. Unsupported publication
after scene mutation invalidates the owner for formal host disconnect/reentry.
Renderer path targets are not common-authority character position commits;
there is no new DB write or5D/5E. Camera/path/model/clock publication is ordered,
not one ACID transaction. Native scheduler/viewport/initial camera invocation,
other modes/transfers/battle, runtime object/alias/null variants and TW view
remain open.

## Actual5D consumer differs from animation completion

World consumer0048FCC0 case5D at00490535..00490562 stores payload byte into
owner+231, initializes two local coordinates to0 and calls005368F0 on+234.
There is no branch on the payload byte around that pop.005368F0 tests read+1
against write+2, not count or reply value. If nonempty it sign-extends each
queued point's LOW16 bits into signed32, decrements count byte and advances
read modulo40. It preserves both local zeros if empty. At00490567..0049058D
the consumer invokes00493E70 with the resulting coordinates regardless.

Thus an empty queue is not a silent no-op at the complete consumer, and a5D
payload cannot be labeled success/failure/ring-index echo from these instructions.
Native ring-pop return itself is not an ack result; recovered C shows quotient
from division, whose return is unused by the actual dispatcher. The protocol
source comment now records these exact qualifications. Its parser/wire bytes,
current complete native reply supplier and shared gameplay route remain unchanged.

## Accounting

Two new C++ files, three existing C++ files changed (CnMovement comment only).
Seven exact native function C/PE/ASM extents are sealed with prior source and
catalog receipts. Source model/path integration is conditional and unhosted.
CN18/TW2/combined20 partial owner chains and CN39/TW7 phase associations remain
unchanged. New full routes0; whole-game total/percentage unknown. No build,
tests, Lua, asset loader, game/server/client execution, production DB, deployment,
client/font or text-conversion change.
