# CN retained standalone MAP cache reuse

Previous round made progress: native flag0 different-MDT loading and full-nine
resource/cache commit were added. This round connects the same-MDT standalone
branch to the retained actual payloads. Four existing C++ files change, no new
C++ file or opcode binding is added. Source paths remain unhosted by the actual
WorldOwner/Application. No build, tests, loader, Lua, client/server, production DB
or deployment runs. Native fonts, Traditional/Simplified conversion, accounts,
saves and frozen chat/IME/authentication/portraits remain unchanged.

## Native reuse contract

00470C90 compares current MDT identity before loading. Equal mode0 resources
retain the current origin/21 center.0046D460 clears every slot+54 when either
delta magnitude exceeds1; otherwise it rotates pointers horizontally first,
then vertically, invalidating only recycled edges.00470C90 walks slots row-major:
valid+54 updates slot+3C without reading a file, invalid+54 invokes0045E7F0
when the retained resource's terrain filename is empty. The successful loader
sets+64/+68 coordinates and+54; a failed loader deletes the slot and leaves null.
0046F630 then composes actual terrain and model overlays. Native success may
coexist with failed/null slots; this round covers complete loaded-nine only.

The state with unchanged clamped center retains all slots. Horizontal/vertical
and diagonal shifts preserve their actual surviving payloads. Larger shifts
invalidate every payload for reload. These are static native conditions, not
executed test cases or extra counted wire opcodes.

## Concrete source connection

CnOutdoorWindow.rotated_slots is the shared recovered pointer/validity transform
for MBD and standalone branches. Allocation labels are internal identities that
move with pointers, not client addresses, model runtime handles or wire IDs.
prepare_standalone_reuse requires the actual current private camera generation,
equal MDT identity, no retained MBD and the active standalone snapshot whose
resource pointer and center match this cache. The MDT clamp applies without a
fabricated MBD neighborhood.

For each rotated valid slot it finds the old allocation label, confirms the
actual coordinates and retains its decoded CnStandaloneMapAsset and historical
source path. The disk is never consulted for valid slots. For invalid slots only,
the private CnSceneAssets.read_standalone_chunk checks the explicit CN profile
root, formats the actual native axis-coded name, reads plain MAP text and requires
the recovered21x21 payload. It never reloads MDT/MDL/model ROMs on a same-resource
switch or falls back to MBD/TW resources. Missing bytes are absence/errors.

The profile source manifest is retained; its last nine slot-ordered source paths
are replaced by the resulting reused/new path order. Candidate construction is
private. Real chunks and the actual retained MDL/model-ROM declared traversal
form the next grid. The camera candidate, grid, slots, reload flags and next
standalone snapshot share the current cache identity/generation. Commit installs
the new snapshot after the cache CAS succeeds; same-MDT reuse explicitly reports
resource_replaced=false, while the previous different-MDT path remains true.
No packet, actor-camera mutation, permission or player-position write is added.

## Newly bounded model refresh frontier

00470C90 calls00473A20 and0046C280 only when prior and loaded centers differ,
after grid composition.00473A20 traverses the prior5x5 chunk groups, gets the
actual current-resource model registry through00470010, and calls0046BD50 for
their linked objects.0046BD50 conditionally cleans runtime model slots when the
object+3C ushort is below0x1000, then writes the full object+3C asFFFFFFFF.
This renderer slot is distinct from outdoor slot allocation labels and server
actor handles.00473A20 also invalidates map+1058/+105C to-1.

0046C280 requires mode0, changed cached center, current resource and center slot.
It sets map+1058/+105C to the new center, traverses its bounded5x5 chunk groups
and selects model type7. Actual center+5C/+60 render offsets, the native5x5
offset table and resource+2A42EC registry feed0046A4E0. The table is preserved
as a raw pinned span; no generated actor/render defaults are substituted.
These refresh operations remain source recovery work because actual runtime
object handles/frame state/renderer registry are not implemented by static MDL
declared geometry. No claim of full rendered-client equivalence is made.

Partial/null/failed slot success, other MAP dimensions/versions, high-byte or
nonalphabet axes, runtime objects/frames, model refresh and real camera/viewport/
map34/prefix ownership remain open. Common scene/position/cache transaction,
movement timing/pending/reset/full5D, TW/CN publication, WorldOwner/Application
and all other gameplay paths still need integration. Added complete routes0;
whole-game route total/completed/percentage remain null. Immutable evidence keeps
eight native functions, one table, old baselines and these four source changes.
