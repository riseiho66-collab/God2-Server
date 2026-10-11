# Current client diagnostic 0x9A and live timer error (2026-09-23)

The original Taiwan 2.40.83 client entered the town display on the isolated
loopback server, then showed a modal error and a black window. The live server
received a 20-byte world frame, decoded 17 logical bytes, and previously
rejected opcode `0x9A`. A bounded native-code trace shows that RVA `2B10`
formats a diagnostic and queues it through `132E0` as opcode `0x9A`.
The format contains a size WORD equal to the logical record size, severity
byte, terminated string, and one copied trailing byte. It carries no gameplay
action. The local frame decoded after this change reported severity 1 and
`timeGetTime`; no credential or chat payload was logged.

Native RVA `5B797` calls `5B920`, whose failed integrity check sends the
report from `5B9F0` and sets the client error flag. Thus the server's old
unknown-opcode disconnect was a consequence of a client error, not evidence
that the disconnect caused the popup. The launcher support's exact-build
patch now skips only the five-byte call at `5B797`; other native checks remain.
This is a local Windows compatibility intervention for the bundled DirectDraw
and locale layer. The causal role of a particular hook has not been isolated.

The server now structurally accepts this native diagnostic as a standalone
no-action record with no response. The observed client report passed the
parser and service, and the server did not disconnect on `0x9A`. A later
client `0x02` frame after the modal was still rejected; its producer and
semantics remain unqualified. The live timer patch has compiled and the
launcher `/self-test` passed, but the user has not yet completed a successful
login and movement retest after the patch. Do not claim the black window fixed.

The separate login failure in the following run reached the game executor
and returned `success=false` after password verification. The owned `test`
account and character remained in SQLite. No password or credential packet
was recorded. Synthetic same-process wrong-password-then-valid-login passed;
the user-facing client currently renders a generic connection error because
the native failure-result packet remains unrecovered.

Verification: Release `god2-server`, `god2-tests`, `recovered-world-records`,
and `recovered-world-service` built; focused CTests `recovered_world_records`,
`recovered_world_service`, `recovered_account_login`, and `session_state`
passed. `test_wrong_password_then_valid_login_same_server` passed on an
isolated loopback server and database. The live client movement check remains
open pending a successful login with the existing account password.

## Unattended original-client black-box retest (2026-09-23)

The owner requested internal testing without interrupting their play session.
The first isolated run (`native-fresh-town-blackbox-20260923-01`) accidentally
reached the already-running persistent server on loopback port 2592; its
`Creation observation requires an empty account list` error was a test-port
collision, not a new client or gameplay failure. Its private database remained
empty. The persistent service was stopped for isolated runs and restored
afterward with its original config and saved database (new PID 11044,
confirmed listening on 2592).

With exclusive loopback port ownership, run
`native-fresh-town-blackbox-20260923-02` used the original client native
functions against a new isolated SQLite database. It completed login, native
character creation and selection, first world frames, and town guide NPC
allocation (`NATIVE_TOWN_GUIDES_ALLOCATED`, error `null`). Run
`native-town-movement-blackbox-20260923-01` then completed three original
native path calls, server ACKs, client idle state, and durable position
`(area 2, scene 4, x64, y64, revision 3)`; SQLite integrity was `ok`.
The longer `native-town-east-blackbox-20260923-01` completed 26 adjacent
native path calls from `(63,64)` to `(89,64)`, with no client error report,
durable position revision 26, and SQLite integrity `ok`. Both movement runs
returned `NATIVE_MOVEMENT_PATH_COMPLETED` with error `null`.

These debugger-mediated native-function probes exercise the current original
client and own server; they do not simulate a physical mouse click, visually
inspect the screen, or exercise the deployed launcher timer patch over a full
interactive session. The runner's `world_accepted=false` is therefore retained.
The client's earlier post-popup black window needs an unattended interactive
reproduction or later owner report before being declared fixed. The native
launcher support `/self-test` regenerated the same client/server/simplified
package hashes in the game directory.

## Extended native gameplay probe

After confirming no game client was connected, the persistent loopback service
was stopped again so the same exclusive-port isolated harness could test the
next gameplay chain. `native-town-fullquest-blackbox-20260923-01` completed
original-client NPC request/confirm calls, all three town guide stages, and a
durable reward receipt (`NATIVE_TOWN_QUEST_THREE_STAGES_AND_REWARD_COMMITTED`).
`native-town-indoor-blackbox-20260923-01` continued through map request,
scene change and native indoor movement; the isolated position was saved at
area 2, scene 15, `(18,12)`, revision 2
(`NATIVE_TOWN_TO_INDOOR_AND_MOVEMENT_COMPLETED`).
`native-town-battle-blackbox-20260923-01` continued through socket battle,
one durable settlement, exit to the world, and three post-battle native path
steps. Its isolated position was saved at area 2, scene 15, `(19,12)`,
revision 5 (`NATIVE_MOVEMENT_PATH_COMPLETED`). All three runs had `error=null`
and SQLite integrity `ok`; all retained `world_accepted=false` because these
are native debugger probes, not a visually observed interactive play session.
The original persistent server config and saved player database were restored;
PID 23864 was confirmed listening on loopback 2592 after the runs.

The collision exposed a harness safety gap. `CppSeedServer` now verifies that
loopback 2592 can be bound exclusively before launching a private server or
client, and raises a clear error when occupied. Its focused 22-test Python
suite passes. The guard was also checked against the restored live listener:
it rejected the occupied port before touching an isolated run database.

## Live recurrence and world-loop timer check

The owner supplied a fresh town screenshot with the same error modal. On the
isolated private test server at `artifacts/playtests/unattended-ui-20260923-01`,
the actual launcher-built client SHA256
`1ca077d8544029c6d2d71416f6661d5378344b696770a6504e9e0016e91caa15`
entered the rendered town. The server logged native diagnostic opcode `0x9A`,
severity 1, text `timeGetTime` at 11:11:59, then a rejected two-byte logical
opcode `0x02` at 11:12:15 after the modal. This contradicts the earlier hope
that the first timer patch fixed the black window.

Read-only process memory from a fresh copy of that build showed RVA `5B797`
already patched to `31 C0 90 90 90`, so the first patch was installed. Native
disassembly of the pinned unpacked Taiwan build identifies a separate path:
world-loop RVA `1187A` calls `5B880`; `5B88D` loads the `winmm!timeGetTime`
IAT address, `5B893` compares its first byte with `83`, and the failure branch
at `5B898` sets the terminal error flag and calls diagnostic sender `2B10`.
The sender argument at `589954` resolves to the exact `timeGetTime` string.
This is a direct code/data match to the live `0x9A` report, rather than an
assumption based on the earlier integrity routine at `5B797`.

The native C++ launcher support now changes only the conditional `JE` opcode
at RVA `5B896` to unconditional `JMP` in its exact-hash client runtime patch;
the success branch, return value and stack contract remain unchanged. Build
`build-native-tools.cmd` passed. A development support executable initially
lacked the player's embedded endpoint resource, so it was immediately rolled
back; a verified player endpoint resource was then inserted into the rebuilt
support. `/self-test` passed and produced patched client SHA256
`ae997bbe726afaaee3a02ff9b718eff03f3d726002bc6aa36ce66a1964241f7f`.
The launcher generated and started that client. Read-only live process memory
showed RVA `5B797 = 31 C0 90 90 90`, RVA `5B896 = EB 21` and the hooked
`timeGetTime` prologue `FF 25`; this proves the new branch patch is active
under the same hook shape that caused the report. Actual post-login movement
with this new build has not yet been observed, so the black-window fix is
still a pending live acceptance check.

The Desktop `GOD2-native-Cpp-v1.0.0-20260923-latest.zip` was replaced
atomically with the updated complete native launcher source and embedded
player support executable (SHA256
`444968e0315fbaea143ac8c1c602fbb94d88dede74d401b17906a5595fb2dcfc`).
ZIP CRC verification passed; it contains 59 C++ source files and no C# source.
The previous Desktop ZIP is retained under the server artifact directory.

## Unattended, no-desktop follow-up

The owner stopped Computer Use and requested internal sandbox operation without
controlling their desktop. The interactive game process had exited before the
follow-up; no further desktop input was sent. An offline comparison of the old
and new `.w10fix` PE sections confirmed that the new 7-byte emission is exactly
`C6 80 96 B8 05 00 EB`, that the prior startup check patch remains present,
and that the terminal jump displacement was adjusted by seven bytes. The
packed original `.text` section cannot be read as the unpacked runtime RVA, so
this check used the patch section rather than asserting on on-disk RVA bytes.

Eighteen focused CTest cases covering Chinese text, login, character list,
world entry/frame, movement, NPC and battle service passed without opening a
game window. The live isolated database passed `PRAGMA integrity_check`, and
its last client diagnostic was the old build's `timeGetTime` report; the new
build has not logged a post-login town session. The isolated listener was
stopped after confirming no established connection, and the owner's persistent
loopback service was restored on port 2592 as PID 25400. These headless tests
do not close the pending interactive black-window acceptance check.

## Internal automated protocol regression

At the owner's request for internal automation, CTest ran without desktop
control. The first 89 cases reached a failure in `network`: the fixture had
not supplied the `ChineseText` converter to `HandlerContext`, so its ordinary
UTF-8 chat was rejected with opcode `0x2FFF` while the test expected the move
reply. This was a test fixture mismatch with the current fixture-mode server,
which lazily constructs the converter before dispatching chat; no production
handler was changed. The fixture now creates the converter from
`resources/opencc` and passes it into the handler context. The rebuilt
`god2-tests` binary passed `network`, `chinese_text` and
`recovered_chat_server` (3/3). The long full suite was stopped after the
failure to focus on root cause; it is not reported as a complete suite pass.
The `network` TCP case exercises login, character selection, world entry,
movement, chat, NPC dialogue and reconnect on an ephemeral loopback port.

## Separate Windows desktop attempt

`God2PrivateDesktop` is a native C++20 runner that creates a named desktop,
starts CDB there with inherited pipes, and checks that the input desktop name
remains unchanged. A Python child reported its private desktop name, and a
signed CDB probe reached its command prompt without changing the owner's
desktop. The native STRIKE harness can opt into this runner with
`GOD2_PRIVATE_DESKTOP=1`; default behavior is unchanged.

An isolated original-client run `native-private-fresh-20260923-01` used the
runner and a private SQLite server. The client called `ExitProcess` from its
startup path before the graphics-return breakpoint; there were zero game
network events and no login/world milestones. Result: `REGRESSION`, not a
successful playtest. The private test server was stopped and the persistent
server restored on loopback 2592 (PID 24756). This desktop mode is therefore
not yet suitable for interactive acceptance of the launcher-built client.

The current packet-contract test `test_recovered_movement_server.py` was then
run against separate ephemeral loopback services without a game window. All
14 tests passed, including original-code-generated movement frames, first town
step, world tail coalescing, batch/ring wrap, blocked move rejection, durable
position restart and reconnect. This proves the server side of the current
movement path under those packet contracts; it does not prove the patched
client's rendered town is free of the timer popup or black screen. The owner's
persistent listener remained active on port 2592 as PID 24756 afterward.

## World timer instruction check

`tests/research/test_world_timer_patch.py` pins the captured unpacked image
(SHA256 `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`)
and the deployed launcher-built client SHA. It extracts the actual emitted
`5B896` branch byte from `.w10fix` and executes original function `45B880`
in an isolated x86 emulator. Four cases passed: the unhooked `83` prologue
returns with no error; a hooked `FF` prologue sets the terminal flag and calls
the diagnostic sender; the launcher branch byte `EB` prevents both under the
same hooked input; and an already-set flag remains set. The diagnostic sender
itself was replaced with a `RET` in the emulator, so the observation is the
native function's branch/flag/call behavior, not a whole game or socket run.
The patch must be used in a fresh client process; it cannot recover a process
that already tripped the flag. The test passed 4/4 without desktop control.

The private desktop startup failure was repeated once with `renderer=gdi` in
the isolated original-client work copy (`native-private-gdi-fresh-20260923-01`).
It again reached CRT `ExitProcess` with code 0 before graphics or network
events. The work-copy `ddraw.ini` bytes were restored to `renderer=auto`, and
the persistent server was restored on port 2592 as PID 25376. Switching this
renderer does not make the private-desktop mode a valid live-game test, so no
further private-desktop game runs are used as acceptance evidence.

A later Windows Sandbox startup probe mapped only a disposable artifact folder
and attempted to write a `ready.txt` marker from guest logon. The Sandbox
launcher was started by the private-desktop runner, but the marker was never
written and the launcher exited while Sandbox background processes remained.
Those user-level session processes were stopped; stopping the protected
`vmmemWindowsSandbox` process was denied by Windows. No game files, account or
server database were mapped into that probe. This mode also cannot supply a
verified unattended gameplay session in the current host state.

After the probe, the deployed player's `/self-test` report and on-disk client
still agree on SHA256
`ae997bbe726afaaee3a02ff9b718eff03f3d726002bc6aa36ce66a1964241f7f`.
The Desktop source ZIP still has SHA256
`444968e0315fbaea143ac8c1c602fbb94d88dede74d401b17906a5595fb2dcfc`.
The persistent loopback server was listening on port 2592 as PID 25376;
no game process or Sandbox session UI process was observed at the final check.
