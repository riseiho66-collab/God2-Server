# CN initial camera source, 2026-10-07

This round integrates the normal mode0 initial camera projection into the
existing common world-entry/native scene owner. It adds no opcode, partial owner
chain or complete route. Native frame timing, viewport and full5D permission
authority and formal Application hosting remain open. Earlier source and reports
are retained without rewriting their claims.

## Exact initial placement and projection

Pinned CN PE SHA256:
`582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8`.

At00538293..005382A1,00537D40 supplies actual actor x and actor y+1 to0046C780.
That function selects/loads the actual center via004663A0/0046C830 and subtracts
the selected native map origins. Its outputs are already retained as
`InitialWorldPlacement.local_x/local_y_plus_one`; raw2E coordinates or an
unclamped packet-derived /21 center are not substitutes.

The initial mode0 path calls00470C10 at005383E9. At00470C4E..00470C78, this adds
21 to both local inputs and calls004751C0 with dimensions63/63, then subtracts
1680 and840 pixels. Primary instructions004751DC..004751EA use the first63
argument to form64; the sixth stack argument is present at the caller but not
read by this pinned callee. Preserve this distinction from the recovered C
signature. X=(x+y)*40 and Y=(64-x+y-2)*20 at the transformed local inputs.

At0053842F/0053843B the actual initial camera additionally subtracts fixed400
and300 pixels. These are native constants, not half of a guessed desktop
viewport. The resulting simplified local formulas are
X=40*(local_x+local_y_plus_one)-400 and
Y=20*(20-local_x+local_y_plus_one)-300. The
implementation retains the explicit native transformed inputs and operation
order. Every promoted signed32 intermediate must fit; wrapped native coordinate
variants stay open rather than silently clamping or treating overflow as valid.

This result precedes00473120. Only a successful native cache-switch return at
00538462..00538480 subtracts actual map+1048/+104C from the camera. The pure
projection does not assume that success or create those offsets. Existing
qualified camera/cache preparation and successful commit own that rebase.

## Source integration

`CnOutdoorCamera::initial_mode0_before_cache_switch` consumes the actual native
initial placement. `SharedInitialScene` computes it from its retained outdoor
resource snapshot and rejects an unrepresentable projection during preparation.
`SharedNativeMovementScene` adopts that same seed with its exact one-use initial
owner. The public seed accessor checks the actual connection/common lease,
ready state, original saved position and scene revision, initial cache
generation, no pending mutation and no published live camera. It ceases to
qualify after a movement/cache change. Indoor mode2 supplies no mode0 seed.

The seed is explicitly pre-cache-switch and initial-only. It does not complete
the initial camera/cache invocation or actual runtime camera publication. Actual
viewport and loaded tile dimensions remain mandatory for0046CE10/00473120.
MDT/MBD chunk counts and native MDT dtime cannot replace those values.

## Ongoing frame camera differs from a logical movement step

At005393D3..00539418,005393B0 converts elapsed native+89B210 to unsigned elapsed
using SSE signed conversion plus table[sign], multiplies each axis velocity
at+24/+28 by elapsed then native binary32 scale at007F58B8, and adds retained
axis residues+1C/+20. The pinned scale bytes are `6f12833a`
(binary32 approximately0.0010000000474974513). The correction doubles at
007ED2A0 are0 and4294967296. The primary positive/negative rounding constants
are binary32+0.5 at007ED104 and-0.5 at007F1170. CVTTSS2SI truncates; native
fractional comparisons then round ties away from zero and retain new residues.
Remaining travel+14/+18 clamps each axis independently; completed axes clear
residue. Only both completed axes produce return1.

At00539506..00539517 the camera receives these actual frame pixel deltas. Only
00473120 success at00539539 rebases the camera and remote actor/model owners
via004FC490/005321A0.004FC5A0/00532240/0041FF90 receive camera updates separately.
No evidence establishes one animation frame/cache transition per2E request or
per common position CAS. The existing permit field is now named
`actual_native_frame_view`, correcting the older after-step wording without
inventing a scheduler, elapsed time, velocity, residues or runtime authority.
Standalone independent frame events still need actual lifecycle integration.

## Accounting and limits

Six existing C++ source files changed, no new C++ file, owner chains unchanged
CN18/TW2/combined20; phase associations unchanged CN39/TW7. Complete routes
added0. Whole-game directional/state/variant total and percentage remain unknown.
Exact before/after source receipts, native C/PE/ASM spans and constant bytes are
sealed separately. No build, gameplay tests, Lua, asset loaders, client/server
execution, production DB, deployment, font or text-conversion change occurred.
