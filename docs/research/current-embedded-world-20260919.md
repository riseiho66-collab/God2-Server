# Current Embedded World Actor and Scene Tail

## Original Placement

Current mapped image SHA-256:
`149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
Source pins and decompression checks are inherited from the current cold actor,
scene, music and viewport helpers. No retired corpus is read by this helper.

The actual caller at RVA `65424..65435` sets ECX to the world, obtains the
actor with `LEA EAX,[EBP+1539683C]`, and pushes that pointer as the first
argument to `100180`. At `100831`, the scene code reads the kind byte from
`[ESI+1539684C]`, the same actor's +10 byte. The former standalone actor at
`07800000` cannot satisfy this embedded-object contract.

`NativeWorldActor` now exposes an overridable actor address and bounded storage
extent. Its default remains the earlier standalone fixture. Scene and music
helpers use that address consistently. New `NativeEmbeddedWorld` selects
`WORLD+1539683C`; original `681CF..68851` initializes it directly, including
the cold resource preload. No initialized actor is copied and no kind byte is
patched to force the branch. The standalone actor address is not mapped here.

The actor extent used for poison/input initialization is `469C`, ending at
the first native NPC pool (`WORLD+1539AED8`). The native role pool ends exactly
at the actor start. This avoids overwriting neighbors with the standalone
fixture's deliberately oversized `6000`-byte region. Adjacent 16-byte snapshots
and all native empty pool record IDs are checked, not silently reset afterward.
The extent is a tested storage boundary, not a claim that every actor field's
meaning is known.

## Scene Continuation

After original scene loading `1004F5..10078F`, the new helper executes
`10078F..100930` continuously: actual music resolution and absent-device
failure branch, camera and pool propagation, embedded actor kind selection,
initial movement-ring enqueue, and the ProgramMsg binding. It stops before
the scene function epilogue. One-shot/prerequisite checks prevent replaying
the camera subtraction or treating an unloaded scene as initialized.

The first attempted run reached `100912` but faulted on a write-protected
message pointer. PE metadata identifies VA `5B8ACC` as `.data`, section RVA
`182000`, characteristics `C0000040` (read/write, non-executable). The fixture
now maps only the containing `5B8000` page read/write, without code patching
or granting execute permission. The permission correction is independently
checked against the original PE section header in the test.

Expected source-backed initial path uses area 2, kind 2, scene 15. The retained
world-entry body remains an explicit lab input, NOT proof of original starting
attributes. Camera projection is `(1240,540)` before and `(840,240)` after the
original viewport code. The kind-2 branch reaches `1008B1` without executing
`10083A` or the previously failing unrelated UI path. ProgramMsg selection
uses the image's WORD selector at VA `59B948` and the actual loaded message
pointer table, not a supplied text pointer. Native `15AB0` is literally `RET 8`
in this image; executing it does not establish a network send.

## Movement Ring Contract

Original `103640` resets the three control bytes. `1036B0` enqueues the exact
DWORD pair read from world +224/+228 into ring world +234. The initial control
bytes are `(count=1, head=0, tail=1)`. This is the native client's movement
ring, not an invented server queue or a map-coordinate policy.

The original full predicate `103680` compares `(tail+1)%40` to head, permitting
39 entries. Tests dequeue the scene's first point through `103700`, fill all
39 entries across tail wrap, check that the next enqueue returns zero without
overwriting the ring, then dequeue all points. Enqueue stores full DWORDs;
dequeue sign-extends the LOW WORD of each coordinate. High-bit probes distinguish
that native behavior from a guessed 32-bit read. Empty dequeue leaves its
output unchanged. These isolated probes preserve/restore their test state.

## Scope and Reproduction

```powershell
python -B -m unittest tests.research.test_current_embedded_world tests.research.test_current_world_music -v
```

The music suite exercises the previous standalone-address path as a shared
helper regression. The embedded suite covers actual caller argument assembly,
native in-place initialization, neighbor integrity, scene tail, data permissions,
ring bounds/widths and one-shot guards.

Main verification: the combined suite passed **15/15** (six embedded-world
tests and nine existing music tests) in **299.631 seconds**. Selected CTest
passed **34/34** in **14.24 seconds**, excluding the same five pre-existing
artifact/gate/environment suites. The separate actor regression revealed an
obsolete retired-source test; its result was excluded and the test removed,
as documented in `legacy-data-retirement-20260919.md`.

The earlier graphics/UI prefix `100180..1004F5`, real display/sound devices,
full lifecycle teardown, live world entry and playable server E2E remain
unqualified. This does not change C++/Lua gameplay, invent formulas or enable
runtime packets. It closes the isolated-actor mismatch in the native scene
oracle without changing the full project's acceptance criteria.
