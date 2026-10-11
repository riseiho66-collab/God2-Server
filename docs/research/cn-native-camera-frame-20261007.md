# CN independent native camera frame source, 2026-10-07

Previous goal turn was progress: actual initial camera source integrated and
sealed under catalog25. This round integrates native00539150 initialization and
005393B0 frame arithmetic into the existing CN live scene owner, with an
independent frame entry rather than inventing one animation frame per2E or
position CAS. Native movement permission/full5D, actual scheduler/authority,
viewport owner and formal Application hosting remain unresolved mandatory inputs.
No additional opcode, partial owner chain or complete route is counted.

## Native initialization and data

Current pinned PE SHA256:
`582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8`.
00489230 returns007F1CF0+direction*0x30 for eight directions. The exact384 bytes
are retained in this delivery. Each row holds seven binary32 speeds at+0..+18,
axis velocities+1C/+20, signed pixel travel+24/+28 and native short direction
tag+2C. Speed bits are40000000,40133333,402CCCCD,40400000,404CCCCD,40733333,
409CCCCD. These approximately2/2.3/2.7/3/3.2/3.8/4.9 values are renderer speed
multipliers, not recovered server speed/permission rules. Axis velocity pairs
are(-60,-30),(0,-60),(60,-30),(60,0),(60,30),(0,60),(-60,30),(-60,0).
Travel pairs are(-40,-20),(0,-40),(40,-20),(80,0),(40,20),(0,40),(-40,20),(-80,0).

00539207..00539237 chooses the native mount-adjustment branch using real
owner+147C71A, packed+14780C8 mask3FC0000/mask3FC00 and counters+14780B4/+14780D4.
That branch calls00489070 on the actual owner+89B160 table and packed bits10..17.
Its actual loaded table float atindex*0x88+4 passes x87 FLD/FSTP into binary32
before ADDSS/MULSS. Missing table does not qualify as a zero mount coefficient.
0053927E reads actual speed-index byte+230 for the unadjusted branch.005385F0
sets this byte to0 in its unmounted branch or to00489130's resource lookup;
its complete data/notification/ring lifecycle remains open.

`CnNativeCameraMotion::begin` consumes already-qualified direction/index and an
explicit actual adjustment branch/coefficient. It reproduces the native velocity
and travel fields and the explicitly cleared positive-zero residues at
005392B8/005392BF. It handles table indices0..6 only; larger overlapping-field
native index variants are not guessed. It neither queues2E nor invents native
ring admission/ownership. A supplied actual accepted-start receipt is checked
against this initializer before the independent frame advance.

## Frame arithmetic and qualified domain

005393D3..00539418 reads unsigned elapsed native+89B210 using signed-to-double
conversion and{0,2^32} correction, then binary32 conversion. Each axis multiplies
velocity by elapsed, by exact binary32 scale3A83126F, and adds retained residue.
CVTTSS2SI truncates first; native fractional comparisons to+0.5/-0.5 round ties
away from zero. New residue is computed against the rounded integer BEFORE
remaining-travel clipping. Positive/negative travel clips independently when
its remainder crosses zero; completed axes clear residue and zero travel.
Already-zero travel produces delta0 and complete independently. Both axes
complete together produce native return1. Camera receives those pixel deltas
before the existing conditional00473120/cache-switch processing.

The C++ source preserves binary32 operation order with explicit stores and
retains exact speed/scale bits. Promotion covers strict IEEE binary32 nearest
rounding, finite non-subnormal arithmetic and representable signed32 integer
operations. It rejects other rounding modes, NaN/infinity, subnormal arithmetic,
CVTTSS2SI invalid casts and wrapped integer variants; it does not invent a
replacement value. Compiler strict-float/rounding settings still need phase2
qualification: this source has not been built or executed. Source arithmetic
is renderer projection, separate from Lua gameplay permission rules.

## Independent scene lifecycle source

`SharedNativeMovementScene::advance_native_camera_frame` requires the real game
owner, ready connection/common lease, same current DB position, cache generation,
mode0 and no pending logical movement/publication. The mandatory actual frame
authority supplies a strictly newer real generation receipt, actual actor state8,
elapsed, all motion fields, actual pre-frame view/extents/map+34/prefix, and the
real post-commit native publication callback. No default authority or timer is
provided. Before-camera must match this owner's published camera, or the actual
initial seed if no camera has yet been published. Optional start receipts must
match exact initializer fields, including float bits.

The motion result feeds existing camera projection and resource/cache preparation.
If the retained central slot is null,00473120's map+FEC branch skips projection,
loading and visibility updates. The independent frame still advances camera
pixels and sends its actual camera result to the model publisher, retaining
existing visibility flags. `center_slot_present` uses actual retained coordinate
presence (the loaded pointer), not slot+54 validity or a guessed zero grid.
Missing prior visibility does not fabricate flags. Other unknown null branches
remain unresolved.
All assets/candidates qualify before mutation and ownership is rechecked. Only
successful actual cache commit rebases the camera; the callback receives the
offset ONLY for success, plus real travel/residue/completion and native visibility.
It must update the actual remote actor/model/path owners. Camera/cache publication
increments scene revision, so an older logical-movement snapshot is invalidated.
No common position CAS, database mutation,5D or5E occurs for a renderer frame.
Post-commit callback/ownership failure invalidates this owner; formal hosting
must disconnect/reenter. Cache and callback publication are ordered, not ACID.

005395E0 calls005393B0 only at actual actor state8 (state12 uses a separate
transition). A both-axis-complete result can consume deferred notification
005385F0, advance path+34, set next target+224/+228, restart00539150 or return to
state0 and update47FE20. That lifecycle is still supplied by the mandatory
actual authority; `Frame.complete` does not invent path advance, completion ack
or a server permission outcome. Independent scheduler attachment, the initial
00473120 invocation, unknown null/alias/dynamic-object/frame variants, other
modes/transfers/battle and TW's own native camera view remain open.

## Accounting

Two new C++ files; four existing C++ files modified. CN18/TW2/combined20 partial
owner chains remain unchanged; CN39/TW7 phase associations remain unchanged.
Full routes added0; whole-game total and percentage unknown. New immutable
receipts preserve prior source/catalog and exact native data/code extents.
No build, tests, Lua, asset loader, game/client/server execution, production DB,
deployment, font or text-conversion change.
