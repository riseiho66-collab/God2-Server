# CN native frame clock and movement ordering, 2026-10-07

Previous goal turn was progress: native renderer initialization/frame/cache
source sealed under catalog26. This round integrates actual0048A4D0 clock
semantics into that existing independent frame source and recovers the ordering
between path/motion/2E producer and pending-ring insertion. Actual scheduler,
runtime owner/viewport/state inputs, server permission/full5D and formal hosting
remain open. No new opcode, partial owner chain or complete route is counted.

## Primary clock sequence, not a guessed timer

Pinned CN PE SHA256:
`582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8`.

0048A519 calls005395E0 BEFORE normal loop timing initialization. At0048A53E,
the client calls the indirect clock through slot007EBCB4 (recovered C names it
timeGetTime_exref), then reads
runtime signed frame-rate DAT008964CC. Primary0048A550..0048A556 is signed
IDIV32 of1000 by that value. The recovered C misleadingly represents the
divisor as a longlong; primary instructions own the width. Quotient stores
into+89B210; tick goes to+89B1FC and+89B214, counters+89B204/+89B208 become0,
debug+231 becomes0. The timing helper models the post-initialization retained
slice, not the earlier uninitialized/preexisting005395E0 invocation. Frame
rate zero is a division fault, not a successful elapsed default; raw negative
quotient bits are preserved rather than guessing a permitted configuration.

0048A782 calls0048AA10; that actual world update calls005395E0 at0048BCA3.
005395E0 state8 calls005393B0, which consumes PREVIOUS retained+89B210 elapsed.
Only after0048AA10 returns3 and actual DAT00886060 is nonzero does0048A79D take
a NEW timeGetTime sample. This sample is too late to drive the motion just
published. Using current sample difference in that motion would shift native
cadence by one iteration.

At0048A7AB..0048A7C9, if first sample is unsigned less than retained frame-base
+89B1FC, a SECOND actual timeGetTime call occurs. That second sample replaces
base+89B1FC and current+89B200, and resets frame counters+89B204/+89B208. Crucially,
previous+89B214 is NOT reset before subtraction.0048A7D5 subtracts that old
previous tick using DWORD wrap arithmetic.0048A7E1..0048A7FA clamps the NEXT
elapsed to5..200 inclusive;0048A804 finally stores current sample to previous
tick. The reset condition compares sample against frame base, not previous tick.
No second call occurs in the non-reset branch. Arbitrary epochs, assumed FPS,
server timestamps, packet counts and saved-position CAS are not substitutes.

The pinned PE's protected/rebuilt declared import table does not expose a named
timeGetTime import at this slot; its raw bytes are60000070. Those bytes are not
promoted to a resolved runtime pointer. Native clock call sites and arithmetic
are pinned primary evidence; Windows API identity is recovered-source naming
and still needs actual loader/runtime qualification in phase2. The source
receives actual clock observations and never calls this raw PE slot.

## Concrete source ordering

`CnNativeFrameClock` retains actual frame base, previous tick and stored elapsed.
It provides the primary signed initialization and the normal post-update timing
slice, including exact conditional second-sample shape, unsigned subtraction,
next-iteration clamp and counter-reset instruction. It does not call a timer,
reset the previous tick early or turn loop continuation into server permission.
Unrecovered message/render/exit/fixed-cadence branches remain owner work.

`SharedNativeMovementScene` now consumes actual retained clock state instead of
an arbitrary supplied elapsed. It checks continuity against the last published
clock on the same current ready common lease. The native motion computation
uses that state's stored elapsed. After actual cache/camera/native model
publication, it invokes the mandatory actual completed-loop clock observer;
only then does it calculate and publish the NEXT native clock through its actual
owner callback. Received before-state must equal the state used for that motion.
Published next clock is retained for subsequent frames. Missing/mismatched clock
observations or failed callback after scene mutation invalidate the owner and
require formal host disconnect/reentry. Mutation callbacks cannot reenter it.

No default observer, timer or clock publisher is supplied. Actual loop status3,
DAT00886060 and conditional timeGetTime samples must come from the applicable
owned runtime path. This source path is not yet scheduled or hosted in
Application. Initial00473120 invocation, mode/state12 transitions, all native
path/deferred-notification/model/resource owners and actual viewport inputs are
still mandatory. The timing slice leaves common DB position untouched and emits
no5D/5E. Camera/cache/clock/model publications are ordered, not ACID.

## 2E send precedes pending-ring fullness check

00539150 initializes axis velocity/travel first. At005392CB it calls004937B0,
which handles actual region/remote actor presentation and, only when native
world+1478088 exists, calls00481600.00481600 writes the two u16 coordinates and
one index and queues payload6 for2E; final stack payload byte remains unwritten.

AFTER that producer call,005392D0..005392EC reads write+236/read+235 and checks
whether(write+1)%40==read. If not full, it stores the point, increments count+234,
advances write and changes motion state/direction; if full,0053939B calls native
00539BF0 reset. The packet may therefore precede a failed local ring insertion.
This invalidates any proposed server rule equating pending-ring space with
permission to send, or treating native ring insertion success as server ack
success. No such rule is installed. Actual5D byte still has an unresolved server
value contract; existing private full-reply authority remains mandatory.

005395E0 both-axis completion can consume deferred005385F0, increment path+34,
start the next segment via00539150, update actual target+224/+228 or finish at
state0 and47FE20. Normal frame completion and server5D queue pop are separate
events; their ordering/state/variants remain explicit recovery work.

## Accounting

Two new C++ files, two existing C++ files changed; existing native motion/cache,
TW routes, client/font/text conversion and Lua source unchanged. Exact prior
source, seven native function extents/ASM and bounded native call records are
sealed. CN18/TW2/combined20 partial owner chains and CN39/TW7 phase associations
unchanged. Full routes added0; game route total/percentage unknown. No build,
tests, asset loaders, Lua, game/client/server execution, production DB or deploy.
