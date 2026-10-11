# Live Offline World Engine, 2026-09-20

## Actual Progress

Two fresh original GOD2 processes completed original local world/scene
initialization and three native frame/presentation cycles each, with no supplied
server packets, listener, login credentials, or desktop input automation.
This is live x86 execution under the existing guarded native CDB, not Unicorn.

| Run | PID | Result |
| --- | --- | --- |
| `offline-entry-prelogin-20260920-01` | 12708 | Original startup reached the pre-login call |
| `offline-entry-native-20260920-01` | 13708 | Original alternate world initializer returned EAX1 |
| `offline-entry-scene-20260920-01` | 22228 | Original100180 scene call/return additionally observed |
| `offline-entry-loop-20260920-01` | 19684 | Three native frame and presentation call/return cycles |
| `offline-entry-loop-20260920-02` | 15792 | Same repeated result in a new process |

This does NOT prove nonblank visible output, interactive movement, encounters,
combat, production-server acceptance, or original monster capability values.
No screenshot was taken. `offline_world_entered` remains false in the broad
existing result field; the precise reviewer field is
`native_offline_scene_loop_verified=true`. Original monster values remain0.

## Isolated Experimental Entry

Only the existing working-copy executable is launched:
`artifacts/capture_work/host-20260918-1430/client/God2.exe`, SHA256
`fb72296cab5950b74d8f7c98155145f7c5f58749c3011adb0540325b60749dd1`.
The launcher verifies its existing effective program firewall rules, signed
Microsoft debugger, original/work-copy identity and non-elevated context.
Transport breakpoints are armed before connect/WSAConnect/send/recv/sendto/
recvfrom/WSASend/WSARecv/WSASendTo/WSARecvFrom. Any hit stops the experiment
before executing that API. Neither successful run hit one of those breakpoints.
These are bounded observed runs, not a claim that all future paths are offline.

Native startup reaches VA531FE2 with application ECX=5E00F8. Both existing
network owners have connected byte+2CB8=0, app+A4=0 and app+440=0. The only
game-code change replaces the five-byte call at531FE2:

- Original `E8 99 BE ED FF`: CALL40DE80, normal login/world flow.
- Experimental `E8 F9 CE ED FF`: CALL40EEE0, native alternate world constructor.

This is our explicit process-local bridge, NOT discovery of a supported
original CLI mode or an authenticated login. Original files are not patched.
EEE0 executes original643B0 and64910. The inactive network owner naturally
selects68160(first_argument=NULL) ->688D0. No login return or monster number
is fabricated. Original100180 returns at6543A, thenEEE0 returns EAX1 to531FE7.

EEE0's plain RET leaves WinMain's pending display argument on the stack, unlike
DE80's RET4. The experiment stops before normal caller continuation. Its second
bridge executes on that same native thread, in a bounded32-byte RX page:

`2B00([app+438]) -> clean cdecl argument -> ECX=[app+440] ->655E0()`

655E0 allocates its own event buffer and enters67860. The bridge has an INT3
return checkpoint followed by UD2; it never silently falls into WinMain.
There is no remote thread, synthetic input event, or invented loop return.
See [exact ABI and byte guard proof](current-offline-entry-bridge-20260920.md).

Other inherited, declared interventions are the existing process-local timer
IAT tail bridge and effective pagefile-capacity query view using actual host
capacity. No OS pagefile policy, registry, firewall policy, credentials or
original installation is changed. Temporary working-copy display configuration
is restored by the existing profile context. The entry call and timer binding
are restored before debugger cleanup; the private RX page lasts only until
the owned process exits. No test process is intentionally left running.

## Frame Evidence

Each successful loop run records:

- Repeated6791D message/frame-loop heads.
- Three67A68 returns from original66B00, EAX3.
- Three32A70 actual COM presentation-call boundaries.
- Three67BCA presentation returns, EAX0.
- Same native process/thread throughout world construction, scene and loop.

Original scene and actor snapshots are saved, including the cold local actor
prefix and GameData header region. The local actor defaults, including area1,
scene0 and coordinates2E8/326, are the built-in branch's inputs, NOT monster
stats or official player state. The original catalog identifies this fallback
scene as South001; visual appearance was not independently inspected.

Each run folder contains raw CDB log/commands, effective firewall evidence,
pagefile policy observations, restored configuration backups, immutable native
result, `offline-result.json`, `local-actor.bin`, and `gamedata-headers.bin`.
The reviewer checks stage order, ownership/thread, NULL input, disconnected
owners, transport guards, real frame/presentation returns, intervention
restoration, thunk identity, raw-log hash and memory-file hashes. It deliberately
refuses to promote these into visible-world or playable-game verification.

## Reproduction

Use a NEW run id; existing evidence is never replaced by the launcher.

```powershell
python -B -m tools.strike_lab.current_offline_client_run --run-id offline-entry-loop-NEW --timeout 90 --enter-local-world --run-world-loop
python -B -m tools.strike_lab.current_offline_run_review artifacts/runs/offline-entry-loop-NEW
```

The runner stops after three frame/presentation returns and closes its owned
process. It is a diagnostic entry, not a standalone playable distribution.

Focused bridge/reviewer tests pass6/6 without a manual PYTHONPATH override.
The first reviewer-test draft accidentally shadowed unittest's `run` method
with a path; the fixture name was corrected before the successful run. The
bridge's initial import-path issue was also fixed and retested. Neither issue
changed game behavior or the recorded runtime results.
Both fresh loop runs passed the independent review. Registered CTest bridge/
review suites also pass2/2. Final process inventory found no GOD2/CDB child
left running, and the bounded ABI worker has been reviewed and closed.

## Next Requirement

Trace local monster creation from this real disconnected world, recording
first writers and original file/calculation provenance for capability fields.
Do not manufacture stat updates to make the world look populated. The available
entry alone does not prove any original wild-monster four-stat/attack/defense
table exists or has been recovered. The C++20/Lua production combat loop and
full original-client/server E2E requirement remain incomplete.
