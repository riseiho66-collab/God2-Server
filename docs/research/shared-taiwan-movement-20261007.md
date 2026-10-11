# TW-origin common native movement source, 2026-10-07

One conditional TW owner chain connects the actual Session movement callback's
parsed2E request to common position CAS, actual scene/actor publication, every
registered TW/CN observer's native5E, and the supplied complete TW5D response.
This is source integration, not formal hosting, complete gameplay or acceptance.
No existing TW movement service/serializer/policy, CN source or script is changed.

## Native recovery

Read-only verified archive supplies the exact mapped TW image hash
`149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
CN current native PE hash remains
`582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8`.
All below TW addresses are RVAs; CN addresses are VAs.

- TW15790..157C5 writes LE16 X/Y and ring byte, then queues six body bytes
  through132E0. Body byte5 is unwritten stack residue, retained by the existing
  parser. It is neither mount state, requiredFF nor permission.
- TW1036B0..1036FB increments write index modulo40. This controller qualifies
  only ordinary native index0..39, without adopting an initial/pending policy.
- TW102700..1027B2 classifies adjacent dx/dy: (0,-1)=0, (+1,-1)=1,
  (+1,0)=2, (+1,+1)=3, (0,+1)=4, (-1,+1)=5, (-1,0)=6, (-1,-1)=7;
  zero displacement retains actor+2C. Native code asserts dx/dy outside -1..1;
  preparation rejects this unqualified input instead of proceeding past asserts.
  Current CN00539150 has the independently recovered same table. Its605-byte
  function and original C are bounded snapshots checked against prior evidence.
- TW102F20..102FE1's eight-direction coordinate probe reaches the actual map's
  46FF0 getter at102FCB and rejects raw zero at102FD2. The direction table at
  102FE4 has eight actual case addresses, retained as data rather than code.
  Raw cell2 remains distinct; nonzero is a necessary local predicate, not all
  native path search/corner/dynamic entity or original server permissions.
- TW WORLD5D length2 dispatch692FA..69345 stores its byte atworld+231,
  unconditionally invokes103700 to pop a pending point and6CC00 to publish.
  This proves complete format and consumer effect, not that the server echoes
  a request index. Full native5D remains mandatory WorldOwner output.
- TW WORLD5E length13 and actual consumer69A60 differ from CN length17. The
  previously sealed common publication uses each recipient's full retained
  native actor record, not conversion of TW wire bytes into a CN template.

The new Lua source `scripts/tw/native_movement.lua` implements only the proven
TW direction and raw-cell predicates. Opaque tail/index never enter Lua or
become direction. The current CN script is preserved byte for byte. These
client predicates do not recover original server movement authority.

## Actual source chain and ownership

`SharedTaiwanMovement::attach` binds the actual TW Session, account/character,
active lease generation, and identical common presence/visibility owners as CN.
The Session must have accepted its native world tail and actually be InWorld.
The real scene owner attaches it during owned entry; a per-connection dispatcher
invokes `handle(Session&, span<RecoveredMovement::Request>)`. Its signature
matches the actual Session movement callback, which queues returned full TW
envelopes. A world-record dispatcher may invoke it for2E runs while retaining
other records. Formal Application installation is still open; no default router
or borrowed legacy CUSTOM service is silently installed.

Each step loads the common saved map/coordinates/revision. `WorldOwner::scene`
must read the actual native destination cell/direction/resource/frame/window
context and provide the real matching scene-owner revision. Missing data returns
nullopt. Lua prepares geometry; `authorize` must qualify actual pending/reset,
timing, permissions, collision/path/corner, transfer/battle and supply full5D.
No all-pass grid, fabricated revision, guessed rate, initial ring, index echo,
empty handler or default success exists in this controller.

Full5D framing and every actual observer's private incarnation/5E allocations
precede the common repository position CAS. Actor/scene/current observer set is
rechecked after authority callbacks. Exactly one shared saved-position commit
occurs per authorized request through existing `commit_owned_step`, retaining
map identity and exact expected revision. No parallel TW/CN position tables or
CN DB import is introduced. The actual owner publishes actor/direction/cache,
then common publication submits all registered observers' own TW13/CN17-byte5E
and advances their retained coordinates. The prepared TW5D envelope is returned
to the actual Session response queue. It is neither an ACK receipt nor rendering
proof. Geometry/state/visibility changes outside this preserved-state adjacent
variant require additional recovered native inputs.

Every request format in a run is checked before any step mutation; permissions
remain per step. The response buffer is reserved before the first commit. Later
failure retains an already committed prefix: no rollback after a peer may have
seen a move. Cleanup tries visibility and presence independently and closes
only the same still-current generation's actual Session. Transport-owned entry
cleanup remains the final lifecycle owner. Reentry must load saved state.

## Remaining and accounting

Actual Application/listeners/dispatcher registration, common world/scene owner,
native data/position/cache/lifecycle suppliers, complete timing/pending/reset and
full5D byte authority remain open. This controller's common5E projection remains
limited to state-preserving adjacent positions <=0x7FF, native visible low12
identity, and already registered peers. Larger positions/IDs, dynamic state,
61/reset/transfer/recovery/battle/path/speed variants remain open. Input uint16
coordinates are never truncated to fit; packet index is not movement speed.

Added5 C++ source files, one Lua source, one TW conditional owner chain and
three TW phase/packet source associations(2E/5D/5E). New opcode values0,
complete routes0. CN bindings39/unique28 and17 partial chains stay unchanged;
TW conditional chains1->2, dual total18->19. Full game denominator/percentage
remain unknown. Existing TW/CN input census and historical reports are preserved.

Previous goal turn was progress: actual TW Session entry/tail/cleanup extension
was sealed. This round executes only static native reading/disassembly/source
accounting. No build, tests, Lua, resource loading, server/client execution,
production database access, deployment, font or conversion change occurs.
