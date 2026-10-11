# Native actor6F/5E/73 bound to the common lifecycle

Previous round connected actual TW/CN movement send APIs but required arbitrary
complete peer5E templates from the unhosted WorldOwner. This round replaces
that ad hoc recipient list with an actual common expected-actor registry, native
6F submission, private incarnation tokens, retained5E/6F positions, native73
submission, pool-reset invalidation and existing CN entry/movement/transport
cleanup. Three C++ files are added and six existing C++ files change. No builds,
tests, Lua/resource loaders, client/server, production DB or deployment execute.
Frozen TW runtime behavior, native fonts and text conversion remain unchanged.

## Primary CN findings

Pinned582f2695 WORLD6F has logical size81 and WORLD73 has size5.6F first updates
the party position using the low12 identity and15-bit X/Y at logical+13. It may
convert three16-byte strings depending on packet bit25 versus00405A30, and
resolves appearance resources or the alternate resource-key path before calling
0052F5A0 at00490AA6. Missing four component resources can skip that constructor.
This registry requires the actual scene owner to qualify full native resource
and recipient text/appearance data; transmitting a format is not display proof.

0052F5A0 searches128 entries by low12 identity, cleans an existing instance with
0052FFC0, then calls00532410. That constructor searches forFFFFFFFF, stores the
low12 identity, stores low16 state from body+6 (logical+7), copies the three
strings, installs15-bit X/Y, and initializes interpolation indices/count.
The source does not guess native appearance, layers, driver, flags, strings or
mount data. All81 bytes and the actual complete13/17-byte5E plus five-byte73
are supplied independently by the real owner, retained and matched for identity,
state and current saved coordinates. CN now has its own6F/73 raw record types.

73 dispatch00490BB7..00490BED invokes0052FD40 by exact low16 identity, removes
the companion pool entry using low15|8000, and removes the party reference.
0052FD40 calls0052FFC0, which retires resource handles and conditionally clears
identity toFFFFFFFF when owner+13418==1.0052F170 and005309F0 initialize that flag
to1 and configure128 entries. Other flag/alias/lifecycle variants remain open;
the source128 bound limits its normal expected registry, not observed free client
slots. TW primary69A28..69A5B independently supplies its73 branch and constructor
4FC1C0 starts with the same128-entry pool search. No common opcode is used as
proof of cross-version equivalence.

Important qualification: although ordinary self2A reserves14-bit handles and
5E/73 consume low16, BOTH native6F constructors mask to12 bits. Consequently an
expected remote actor must use an actual reserved handle<=0FFF. The owner must
provide a real mapping for larger handles; the registry never truncates or
allocates aliases. Previous movement evidence and receipts stay historical.

## Actual source chain

SharedActorVisibility holds one exact common ready-source lease and ready
recipient lease per directed visible pair, plus the recipient's actual fixed
TW or CN connection and full native6F/5E/73 data. Same-scene position is a
necessary binding check, not an invented visibility/range policy. The real
scene owner chooses which pairs to show or hide and supplies data/resources.
Duplicates from another lease generation or changed protocol are refused.

show checks socket/account/character/ready identity, actual saved coordinates,
matching native state and all three record identities, bounds the expected
normal registry to128 incoming actors, allocates the node/output first, creates
a private new incarnation and submits full6F. Replacement invalidates previous
tokens, matching native6F's cleanup/reinitialization. Send failure removes the
candidate and closes only the still-current recipient generation for fresh
owner recovery. Submitted actors are expected models, never observed memory,
socket receipts or native rendered acceptance.

SharedMovementPublication automatically prepares every current registered
observer of the mover using private Binding tokens. WorldOwner::Authorization
now supplies only the mandatory full5D; it cannot omit queued peers or construct
arbitrary recipient5E templates. The exact observer set is checked before the
position CAS and again before the first post-CAS send, including new, removed
or replaced bindings during actual owner callbacks. Existing native projection,
position revision, actor/cache publication and TW/CN transport ordering remain.
After each5E API submission, advance updates that same binding's retained spawn
and move coordinates for the next step, preserving all other bytes/bits. The
source distinguishes old expected-model position from the actual committed DB
position instead of falsely requiring DB-before after a successful CAS.

hide invalidates the incarnation before native73 submission. Stale tokens
cannot hide a replacement. A still-current recipient with an unqualified scene
or failed submission is closed for recovery rather than guessing a new-scene
removal. reset_recipient invalidates incoming bindings without manufacturing a
packet when the actual native scene owner resets its pool. That native61/reset
owner route remains unhosted and must call it explicitly.

CN SharedWorldReady and SharedMovement require this exact registry owned by
their same SharedWorldPresence. Ready's existing transport-owned cleanup now
releases visible incidences before the common presence lease; failure paths do
the same. Recipient disconnect removes its incoming bindings without sending
to that departed socket; source disconnect submits stored native73 to qualified
surviving observers. Full lease generations and private identity prevent stale
cleanup from closing/removing a successor. One peer failure does not prevent
cleanup of other incidences. No committed player position is rewound.

## Remaining work and accounting

This adds one conditional unhosted source chain, CN WORLD6F and73 unique source
bindings, and another existing5E binding. No new opcode values or full gameplay
route is counted. Actual world policy/actor allocation/full native data and
resource suppliers, camera/cache/position transaction, timing/pending/reset/full5D,
full-map/scene reset integration, TW common enrollment/cleanup and TW-origin
movement, Application/listeners, native login/bootstrap and every remaining
game route remain incomplete. Dynamic appearance/mount/state/resource/text,
non-normal pool flags, larger handles/coordinates, battle/path/transfer and all
other native variants are open. Total/completed full routes and game percentage
remain unknown/null. No third-party official server is contacted.
