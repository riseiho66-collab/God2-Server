# Current offline-world entry audit, 2026-09-20

## Result and boundary

**No supported executable CLI or reachable startup entry into a real offline
world was identified in this bounded audit.** There IS native local fallback
code: `68160` with a null first argument takes `688D0`, initializes a minimal
actor, and returns success without the BEGINPLAY waiter. This is positive
evidence of an internal branch, not proof of a launchable offline world.

The concrete blocker is an unmodified, supported entry path from process
startup to the world initializer with the required initialized objects and
inactive connection state. The separate constructor at `EEE0` is a specific
lead, but no direct CALL/JMP or stored absolute pointer to it was found. No
claim of complete absence, dead-code proof, or indirect-call exhaustion follows.

**Original monster values recovered by this audit: ZERO.** The built-in actor
defaults below are not original monster stats. Disabling packets has not been
shown to supply the missing entry prerequisites or authoritative stat data.

No client, launcher, debugger, server, UI session, network connection, or VM
emulation was started. No game patch, configuration change, database access,
old archive access, or shared-source edit occurred. Only this document is
authored; no helper/test file was necessary. Existing proofs were read, not
rerun. Python/Capstone performed read-only static decoding and hash checks.

## Pinned inputs

All native addresses below are hexadecimal RVAs; base VA is `400000`, and
RVA equals file offset in the mapped image. Do not translate these offsets
through the retained packed PE section raw offsets.

| Input | SHA-256 |
| --- | --- |
| `artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin`, 3,174,400 bytes | `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763` |
| Current sibling `God2/God2.exe` | `fb72296cab5950b74d8f7c98155145f7c5f58749c3011adb0540325b60749dd1` |
| Current sibling `God2/God2-run.exe` | `fe4328489aa47ed634b123c5dd4fa21e56c9feed8893c03f1ff5a6f23a1a88e6` |
| Current `God2/Data3/config.iniZ` | `665bdb144f2c89d623e7186f558540cf7cc54adc0a7065e1e056adf32b171da0` |
| Current `God2/Data3/config2.iniZ` | `5408e1da7d9f44b6f71ada16420974e42652c5c4a12f98053b31d99befc3597c` |

The native image hash and all four sibling file hashes were recomputed. The
packed executable and run copy are distinct identities; this audit does not
execute either or infer run-copy behavior from its filename.

## Existing launch and test commands

- Current launcher source `../Launcher-src/launcher-src/God2Launcher.cs:76`
  returns the argument string `220.130.125.10 210.244.30.58 6001 1`.
  `TaiwanSupport.cs` uses that string with a generated run copy. This source
  is a lead, not evidence that every installed launcher binary is identical.
- `tools/strike_lab/lab.py:96` and its README retain the test argument string
  `127.0.0.1 127.0.0.1 6001 1`. `God2LabLauncher.exe` is the project's debugger
  frontend; its `--profile`, `--observer`, and `--run-id` belong to that tool,
  not the game. Loopback arguments do not create a world without a peer.
- Existing `native-args-check-result.json` under the pinned capture output
  records `da @esi` as `127.0.0.1 127.0.0.1 6001 1`, `EAX=4` at VA `531E16`,
  and the taken `jge 531E28`. Its own qualification is
  `OBSERVED_PENDING_REVIEW`, short mode qualification. It proves the retained
  positional parse observation, not world entry.
- `python -B -m unittest tests.research.test_current_world_startup -v` is an
  existing offline Unicorn test command, not a client CLI mode. It was not run.

These are descriptions of existing commands, not proposed launches.

## Actual command-line parser

`14A46E` calls GetCommandLineA through IAT VA `570308`; CRT startup eventually
calls the game's WinMain-shaped function `131D90` at `14A4C3`. Its parser is
not an option-name dispatcher:

| Native anchor | Behavior |
| --- | --- |
| `131DC0..131DD4` | Empty argument string returns before game initialization. |
| `131DF6` | Pushes format VA `59E09C`, literal `%s %s %d %d %s`. |
| `131DFC`, `131E06` | Defaults fourth field at VA `6F4CB4` to 1; clears optional fifth string. |
| `131E0E -> 1480B4` | Calls the CRT scan routine. |
| `131E16..131E25` | Fewer than three successful conversions returns 0; otherwise continues at `131E28`. |
| `131EB0..131ECA -> 132070` | Passes the two strings and third integer into application initialization. |
| `1320EC -> 130440` | Stores string arguments via `1304D0/130520`; masks the integer to 16 bits and stores VA `5B94E0`. |
| `131F0C..131F69` | Fourth field controls display handling, including the explicit 16-bit-window-mode message and 800x600 checks. |
| `131FAA`, `131FE2` | Calls application/device initialization and `DE80`, the normal login/world flow. |

The fifth string occupies a local buffer at stack base `+514`; it is scanned
but no consumer or mode comparison was identified in `131D90..132064`.
There is no demonstrated fifth-argument offline selector. The fourth integer
must not be relabeled as a test/offline flag: its observed consumers concern
display mode and it is passed on through `131D10` and `DE80`.

A bare `--offline` or `--test` is not supported by this parser: it supplies
only one conversion and follows the fewer-than-three exit. No speculative
argument variations were executed.

## Real private-network configuration branch

`DA10` initializes two network owners through `12E70`, at `DCB6` and `DD8D`.
The first host string is copied into the application at `DA38..DA60`, then
passed from application `+220` to the network initializer. `12E7E -> 11BB0`
contains a concrete comparison against the first eight bytes `192.168.`:

| Condition | Selected native path string |
| --- | --- |
| Prefix matches and `131C10` returns zero | `Data3/config2.ini` at `18559C` |
| Prefix matches and `131C10` returns nonzero | `Data3/config2_gb.ini` at `1855B0` |
| Prefix does not match, zero | `Data3/config.ini` at `185570` |
| Prefix does not match, nonzero | `Data3/config_gb.ini` at `185584` |

Comparison is `11BC8..11BDA`; selection converges on `11C32 -> 12740`, the
configuration loader. `131C10` checks locale words against 4 and 2; it is not
an offline switch. Both prefix outcomes share the network initialization
continuation `11C65..11CAD`, including `11C7D -> 143D6E` and `11C9D -> 10500`.
No branch around networking was identified here.

The current compressed configurations were decoded read-only with the
existing `omega_assets.decode_csvz`. `config.iniZ` is an 84-byte decoded
launcher server selection, version 339, endpoint `127.0.0.1`. `config2.iniZ`
is a 959-byte decoded internal server list, version 6, containing endpoints
such as `192.168.8.28`, `192.168.8.53`, `192.168.44.25`, and `192.168.8.52`.
The plain `.ini` variants and both `_gb.iniZ` variants were absent at these
exact current paths. These facts identify a private-server selection branch,
not a local stat store or an offline-world command.

`God2Launcher.player.settings.xml` contains display settings only. Current
`ddraw.ini` includes `devmode=true` alongside renderer/window settings; it is
wrapper configuration and supplies no demonstrated game-world entry branch.

## Internal local fallback and missing entry path

The strongest local-mode evidence is the original world initializer itself:

1. `64910` binds application-owned network, resource, and display objects into
   the world. In particular `649A6..649AC` binds application `+438` to world
   `+A7E05E0`. This is not a self-contained function callable from a shell.
2. `6516D` reads network owner byte `+2CB8`, identified by the existing
   socket-topology proof as its connected/active flag. If zero, `65184` goes
   to `65190`, pushing NULL as the first argument to `68160` at `65194`.
   Otherwise `65186..6518D` passes the caller-supplied value.
3. `68173..6817B` tests that first argument. Nonzero continues to the existing
   BEGINPLAY waiter `681A3 -> 15690`; NULL jumps to `688D0`.
4. `688D0..68921` writes actor fields `+0=0`, `+4=0`, `+8=2E8`, `+C=326`,
   byte `+10=1`, `+14=0`, word `+18=1`; zeros `1141` dwords starting at `+90`;
   writes `+160=actor+168`; returns `EAX=1`, `RET C`. It does not read a monster
   stat file, construct authenticated character state, or establish a renderer.
5. Returning successfully from this branch still leaves the surrounding
   `64910` resource/UI/scene initialization and later game loop unproved for
   this state. It is not evidence of a visible or interactive offline world.

Direct call candidates to `64910` were found at `E0D6` and `EF75`:

- Normal flow `DE80` initializes its state to zero, performs the login/selection
  call `DF87 -> 4DA0`, and requires result 1 at `DF8C..DF8F` before the first
  world construction. Dropping packets alone does not establish that result.
- The separate function `EEE0..EF8A` discards a prior world if present,
  allocates `15AAD38C` bytes, calls constructor `643B0`, and calls `64910` at
  `EF75` with two zero arguments in its six-argument setup. This is an actual
  alternate construction routine, but startup reachability is unresolved.
- A byte-level scan of `.text` (`1000..16FFFF`) found no direct `E8` call or
  `E9` jump targeting `EEE0`; a scan of the mapped image found no DWORD equal
  to its absolute VA `40EEE0`. This excludes those specific reference forms,
  not computed indirect calls, alternate entry into a block, or runtime writes.

The next bounded blocker is therefore **a supported caller/trigger for `EEE0`,
or another unmodified route past the normal login result gate into `64910`
with inactive `+2CB8` and all required owners/resources intact**. Once such a
route is demonstrated, its full scene/game-loop continuation still needs proof.
Clearing a flag manually or directly calling `68160` in Unicorn would only
exercise the internal fallback and would not resolve launch reachability.

## Option/debug/test string checks

ASCII printable runs and UTF-16LE ASCII runs in the pinned image were searched
for offline, standalone, single-player, test-world/testmode, localmode,
nosocket/nonet, debug, command-line, argv, usage, test, local, and option leads.
No named offline/test-world switch with a game-startup consumer was found.
Relevant positive hits were checked against code, not promoted from names:

| Candidate | Actual observed consumer |
| --- | --- |
| `debug.log` at `184AA4` | Pushed at `DE3B` into `1150`; that routine opens fixed `God.log` with mode `w` and stores a file handle. No argument comparison or world entry. |
| `%04dtest` at `18E030` | `74AB0` builds randomized record data and calls `74DB0`; no direct E8/E9 caller or stored absolute pointer to `74AB0` found. Not a CLI parser. |
| `test` at `190160` | Pushed at `950CB` into a repeated UI call `950E6 -> 107710`, along with color and table-derived arguments. Not an option comparison. |
| `Unregserver`, `Unregister`, `Embedding`, `Automation`, `dde`, `p`, `pt` | Library command-line parser `1698F2 -> 16991B` performs comparisons and updates its command-info fields. No observed path from these flags to the game's local world constructor. |
| `CCommandLineInfo` RTTI at `1A1250` | A library type name, not proof that the game WinMain uses this option parser. |

String scans do not prove all hidden commands absent. This audit did not
exhaust indirect control flow or inspect every in-game command handler.

## Existing startup proof is not a launch path

`current-world-startup-20260919.md` expressly limits its result to Unicorn.
`current_world_startup.py` creates and binds VM allocations, installs explicit
resource adapters, starts the slice at `64CB6`, and stops it at `64FE2`.
`enter_full_scene` requires a retained 36-byte indoor fixture and directly calls
`100180`. The four recorded passing tests prove that qualified native slice
and scene function under supplied state. They do not traverse WinMain, bypass
login through a supported command, or run an interactive offline client.

Other read-only references were `current-world-initialization-sequence-20260919.md`,
`current-login-character-socket-topology-20260919.md`, and
`recovered-world-entry-20260919.md`. No broad protocol or pet2 analysis was done.

## Probe decision

No safe executable CLI-only offline probe is supported by the evidence found,
so **no invocation is proposed or run**. A concrete supported trigger and its
prerequisites must be established first; any later executable probe should have
its exact invocation presented before execution. This audit supplies a bounded
negative entry result with positive internal-branch evidence, not an absence
proof and not recovered original monster values.
