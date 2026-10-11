# Current native world viewport, 2026-09-19

Follow-up: `current-embedded-world-20260919.md` adds a separate in-place actor
host and qualifies the previously failing continuation through `100930`.
The isolated viewport host documented below intentionally retains its older
`100831` boundary. Its historical failure is not a current global blocker.

## Qualified boundary

`tools/strike_lab/current_world_viewport.py` extends `NativeWorldScene` with
unchanged current-image execution at RVA `1007B0..100831`. The native image
pin and current CAN/HMD/ROM source pins are inherited from the existing scene
and cold-resource oracles. The retained 36-byte world-entry body is an explicit
lab stimulus, not an original starting-state policy or a captured live session.

The existing actor/cold-resource/scene path produces projected `(1240, 540)`.
Native camera code subtracts its original 400/300 constants, selects manager
mode 2, and calls `46520`, `430B0`, `422D0` and `103C70`. The resulting origin
is `(840, 240)` in the world, indoor manager, both NPC pools and role pool.
The indoor source prop participates in the actual projection/update path.

The two NPC pools use complete native constructor `CA680`, and the role pool
uses `FABB0`. All 256+256 NPC records and 128 role records remain empty, with
their original ID=-1 initialization. Unused owner dependencies are explicit
unmapped poison pointers, not fake successful renderers. Optional effect-pool
initialization executes only `30D7C..30D93`; its nested resources are NOT
constructed. Native `30F30` encounters its actual null-renderer branch, so
`1AC30` is not claimed executed.

The initial two-test viewport suite passed in 151.328 seconds. Tests check
actual origin propagation, function visits, empty record IDs, open-handle
cleanup, restored SEH head, prerequisite rejection and one-shot lifecycle.
This is native-code execution in a bounded memory/OS fixture, not a display
device, visible game world or original-client/server E2E acceptance.
After restoring this exact boundary following the failed longer extension,
both tests passed again in 150.203 seconds.

## Explicit next boundary

An attempted extension to `100930` FAILED at original RVA `1077FA` with an
unmapped read. It was not accepted or hidden by a successful-return stub.
The inherited lab places its initialized actor at `0x07800000`, whereas
`100831` reads the actor embedded at `WORLD+0x1539683C` (kind at +0x10).
Those are not aliases. The uninitialized embedded state selects an unrelated
UI path and eventually faults. The harness was restored to stop at `100831`.

The next integration must initialize the actor at its actual world-relative
placement and requalify neighboring storage/lifecycle. Do not copy selected
fields merely to force the branch. Movement-ring initialization, post-scene
message binding and the function epilogue are NOT qualified by this viewport
test. Music `10078F..1007B0` is a separate composable oracle; see its own
delivery for the source selector and explicitly absent sound-device branch.
Its delivered joint test now executes music and this viewport interval
continuously through `100831`; the worker reported all nine music tests
passing in 179.129 seconds. The embedded-actor boundary is still unchanged.

No gameplay formula, runtime packet policy, C++/Lua ownership or original
client file was modified by this viewport work.
