# Current offline entry bridge, 2026-09-20

Addresses are hexadecimal RVAs unless prefixed VA. Image base `400000`;
RVA=file offset; pinned image SHA-256
`149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.

## Immediate handoff

At the actual post-EEE0 checkpoint VA `531FE7`, keep the original thread and
application alive. Use the real application pointer (observed VA `5E00F8`),
read its current `+438` and `+440`, and execute this experimental bridge:

```asm
push dword ptr [005E0530h]   ; app+438, existing native network owner
mov eax,00402B00h
call eax                   ; original global binder, cdecl
add esp,4
mov ecx,dword ptr [005E0538h]; app+440, actual constructed world
mov eax,004655E0h
call eax                   ; original world event loop, thiscall, NO args
int 3                      ; record actual EAX/ESP if loop returns
ud2                        ; do not fall through accidentally
```

Exact 32 bytes, also returned by `loop_trampoline()`:
`ff3530055e00b8002b4000ffd083c4048b0d38055e00b8e0554600ffd0cc0f0b`.
The return INT3 is at bridge+`1D`; UD2 is at +`1E`. This helper only builds
bytes; it does not allocate, inject, patch, launch, or access another process.
The binder is native `2B00`: `8b442404a3cc015b00c3`; it stores its argument
to VA `5B01CC`. Normal DE80 performs this binding at `E042..E049`; EEE0 omits it.

No DE80 frame exists in main's CALL-EEE0 experiment. **Do not jump to E0F2,
E0FD, E145, or E2AA from that checkpoint.** They depend on DE80's own EBP/ESP.
Calling the standalone `655E0` function with ECX=world avoids that dependency.

## ABI and lifetime

- `EEE0`: ECX=application, no stack arguments, plain RET. Returns actual
  `64910` EAX unchanged. It binds app+440 and sets app+114BA4=1.
- `64910`: ECX=world; six stack arguments, RET `18`. EEE0 supplies
  `(app, stack_scratch, app+A4, 0, 0, 1)`. The scratch is not fabricated login
  data: when owner+2CB8=0, native `65190` passes NULL to `68160` instead.
- Normal DE80 supplies a login/selection record at its frame+30, app+A4 output,
  the two selected indices from login-object +8F4/+B40, and final flag 1.
  It requires login function `4DA0` to return 1. The experiment bypasses this
  caller; it does not claim that login succeeded.
- `655E0`: ECX=world, no arguments, plain RET; normal caller is `E0F8`, returning
  to `E0FD`. EAX is a loop exit code, not a success boolean. Static exits return
  1..6; keep the actual value. Normal DE80 uses these for exit/relogin choices.
- `67860`: ECX=world, one pointer to the loop's event buffer, RET 4. Do not call
  it with the EEE0 scratch buffer: let `655E0` allocate and pass its own buffer.
- The replacement CALL at VA531FE2 leaves WinMain's pushed display argument on
  the stack because EEE0 uses RET, whereas DE80 uses RET4. Main's observed
  post-EEE0 ESP was `1A1594`; ordinary DE80 return would be `1A1598`. The bridge
  above balances only its own calls. Before any eventual WinMain continuation,
  account for this one pending DWORD exactly once. Remain stopped on loop return
  until main handles teardown; do not fall into WinMain while the loop is active.
- Keep world/app/resources/network owners alive throughout the loop. Native
  application destructor `D880` destroys app+440 via `645A0`, frees it, and then
  destroys the remaining owners. Never call EEE0 again while its prior world is
  running: EEE0 itself destroys/replaces an existing app+440.

## Scene, frame and presentation observations

| RVA (VA) | Observation and exact bytes where relevant |
| --- | --- |
| `65435` (`465435`) | CALL `100180`; bytes `e846ad0900`. ECX=world, arguments `(world+1539683C, 1)` for EEE0's final flag. |
| `6543A` (`46543A`) | Original scene-call return. Main now reports this actual second-run stop, followed by EEE0 EAX=1. |
| `6564E` (`46564E`) | First loop dispatch CALL `67860`, bytes `e80d220000`; return `65653`. Initial dispatcher state is 3. |
| `6791D` (`46791D`) | Repeated frame/message-loop head inside `67860`. |
| `67A0C` (`467A0C`) | Message polling API call, bytes `ff15cc065700`; translation/dispatch at `67A33`/`67A3E`. |
| `67A63` (`467A63`) | CALL frame routine `66B00`, bytes `e898f0ffff`; return `67A68`, value 3 continues rendering. |
| `67BC5` (`467BC5`) | CALL presentation path `32A20`, bytes `e856aefcff`; return `67BCA`. |
| `32A70` / `32A85` | Actual presentation branches: COM vtable call at +14 or CALL `13CA50`; which executes depends on renderer state. `32A20` can also return without presenting. |
| `67BFF` (`467BFF`) | Normal no-extra-dialog branch back to `6791D`; require repeated frame progress, not just a single entry hit. |

The current catalog has the fallback's area=1, scene=0 (`South001`); fallback
coordinates are original `2E8,326`. Constructor `64527..6453A` zeros the embedded
actor before `688D0` sets its limited defaults. The fallback leaves app+A4
untouched; normal DE80 clears it at `DED0`. For the direct-entry experiment,
inspect app+A4 and require zero, plus both network +2CB8 flags zero; do not
quietly invent state if those checks fail. World actor+4 is zero on this branch.

No new ABI prerequisite remains unidentified. The next empirical blocker is
actual repeated frame/presentation execution and nonblank rendered content.
Scene return or EAX=1 alone does not certify visible world rendering. Leave
the existing transport guards armed; this sidecar does not certify every
future event-loop path as network-free or supply monster data.

## Evidence and verification

Read main's `artifacts/runs/offline-entry-native-20260920-01/offline-result.json`:
real constructor/initializer/null branch, world `1002D020`, actual EAX=1,
patch restored, executable disk unchanged, `offline_world_entered=false`, and
zero original monster values. The later `100180 -> 6543A` observation above is
main's follow-up report; no second-run artifact was independently opened here.

Focused test command, with no manual PYTHONPATH needed (the probe adds the
existing `artifacts/tooling/crypto-oracle-python` import path):
`python -B -m unittest tests.research.test_current_offline_entry_bridge -v`.
**2/2 passed in 0.042 seconds.** It executes original DE80 prologue/epilogue,
EEE0 call setup/epilogue, and the `655E0` prefix up to `67860`'s entry. It verifies
the argument/return stack and exact trampoline bytes. It does not execute the
world initializer, frame body, native devices, or another null-actor test.

All native execution in this sidecar is limited Unicorn ABI evidence; the
real-process evidence belongs to main. The trampoline is explicitly our
experimental bridge. Only this document and its named helper/test are changed.
