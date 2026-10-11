# Crypto Runtime Qualification (AGENT-D)

Parent integration update: God2Probe now emits key hashes/socket and paired binary
evidence; crypto_runtime_observer.py adds RX pre-decode/client-checksum correlation
and TX pre-transform plaintext comparison. These additions passed mocked observer
tests, not live validation. The availability inspection below describes the
pre-integration runner. Fresh nonzero seed, official UI transport, actual opcode/
state acceptance and promotion remain unresolved. Historical replay is now
UNIQUE_CANDIDATE in artifacts/crypto/decrypt-strike-02, never CODEX_VERIFIED.

Inspection date: 2026-09-19. Scope: feasibility and CPU-only regression.
No original client, server, debugger session, UI input, or new loopback session
was launched. No existing scripts, configuration, or session state was changed.

## Parent Handoff

Fresh bidirectional key/state/parser validation is BLOCKED, not completed.
The approved computer-use skill and guidance were read before checking native
availability. Importing `@oai/sky` in `node_repl` succeeded. The actual read-only
`sky.list_windows()` call failed: `Computer Use native pipe is unavailable:
failed to connect native pipe: ... (os error 2)` (system cannot find the file).
This is an observed transport failure, not an inference from browser-only tools.
No alternate UI automation or helper protocol was used. Restore the official
Computer Use transport before attempting an unattended client UI workflow.

Smallest executable regression command, from this repository:

```powershell
python -B tests/research/test_crypto_bounds.py
```

Existing no-client runner prerequisite command (documented, NOT executed here;
its output-writability check briefly creates a temporary file):

```powershell
.\build-strike-lab\Release\god2-strike-runner.exe --ui-gate-check
```

Smallest stock rendezvous command for a new session, for parent review only:

```powershell
.\build-strike-lab\Release\god2-strike-runner.exe --ui-gate-rendezvous --run-id crypto-local-20260919-d01
```

NOT presently an authorized executable route under the no-unofficial-UI-bypass
constraint: it automatically enables network strike, enter-game and test-login;
`apex.py` calls `window_snapshot.enter_game`/`submit_test_login`, and launches
the custom `--native-dialog` helper (`native_dialog.cpp` uses BM_CLICK).
An official sky-driven external UI adapter must replace those input paths first.
Do not reuse the run ID if it exists. Rendezvous has an unbounded default wait;
the optional `--ui-gate-max-wait 120` bounds it. No CLI currently supplies a fresh
nonzero seed or complete bidirectional crypto tracing. There is consequently no
existing one-command qualified fresh-key capture to report.

## Available Paths And Limits

- Present on disk: `build-strike-lab/Release/god2-strike-runner.exe`,
  `God2Probe.dll` in that directory, `build/Release/god2-server.exe`, and native
  x64 CDB at `C:/Program Files/WindowsApps/Microsoft.WinDbg_1.2606.22001.0_x64__8wekyb3d8bbwe/amd64/cdb.exe`.
  Presence does not certify current signatures, firewall readiness or launchability.
- `frontend.cpp` forwards to `tools/strike_lab/apex.py`; its C++ listener binds
  `127.0.0.1:2592`. Working client: `artifacts/capture_work/host-20260918-1430/client`.
  Capture outputs go to a new `artifacts/runs/<run-id>` directory, including
  `c2s`, `s2c`, `network`, logs, and structured events. Capture profiles temporarily
  change client configuration and restore it; therefore none were run here.
- `ui_gate.py` preflight checks binaries, golden prefix, client identity, frozen
  state consistency, loopback configuration and output writability. Native driver
  separately requires signed x64 CDB, non-elevated execution and work-copy firewall
  readiness. Shared working-copy/session ownership, port availability and those
  launch guards remain to be checked at execution time. Do not disturb an active run.
- `apex.py` traces initial handler/install/return at 0x410e80/0x410e9f/0x410ec2
  and frame input at 0x4124d0. Its installed-seed dump reads only 16 bytes.
  The packet extension reads 256 key bytes at codec+0x2420 and feedback at +0x2556.
  Automatic `!God2Probe.packet` capture is limited to a matched full `send` return
  at 0x412506 with ESI retained as codec and length 4..258. This is not a general
  S2C decoder/parser trace. AGENT-A's static confirmation below establishes that
  the recovered transform does not write feedback back after a packet.
- `packet_probe.cpp` reports key/feedback source addresses but does not emit full
  key snapshots or paired state transitions. CPU brute candidates explicitly remain
  unverified; an 8-bit checksum hit is insufficient evidence of correct decryption.
- No GPU work was requested or performed. CPU regression needs none. Graphical
  client startup without GPU hardware was not tested; do not infer that capability
  from CPU-only decoder success or historical captures.

## Necessary Hooks Before Fresh Validation

AGENT-A static findings supplied by the parent: encode 0x410690 and decode
0x4106F0 load initial feedback from codec+0x2556 on each packet, reset key index
to zero on every entry, wrap key access with i%256, and do not write feedback or
offset back. The enabled DWORD at codec+8 must be nonzero. At 0x4104d0..0x4104f1,
feedback is initialized to `-sum(K)&255`. TX and RX use the same field layout
(key at +0x2420); this does not establish one object across all connections.
The recovered model is `packet_reset`, not `directional_chained`. These are
attributed static findings, not fresh runtime observations by AGENT-D. No separate
AGENT-A completion document was present among crypto-named docs at this check.

1. Supply a run-owned external UI rendezvous using official `node_repl`/`sky`
   observations and inputs; retain unique returned window identity, fresh screenshots
   or accessibility indexes, and refresh after every action. Disable custom dialog,
   menu and login input helpers. No owner manual click is part of the proposed route.
2. Add an isolated nonzero-seed server profile and matching key expansion/response
   handling. Current `seed_fixture` modes, `RecoveredZeroSeedKey.h` and recovered
   response helpers implement the frozen zero-seed contract. A new process/session
   using that contract is fresh execution of a fixture, NOT fresh-key validation.
3. At verified transform entry and matching return in each direction, capture full
   256-byte key, initial/final feedback, codec pointer, relevant flags and receive
   cursor/length, PID/TID/socket, sequence, and exact input/output spans. Correlate
   seed install and expansion with those objects. Enforce the statically established
   packet reset for every frame; independently record TX/RX object IDs and connection
   identity rather than assuming object identity across directions or connections.
   Pre/post snapshots check runtime agreement with that model, not a chaining hypothesis.
4. Capture parser entry/return, declared length/opcode, consumed bytes and acceptance
   or rejection. Reassemble TCP frames independently of send/recv chunk boundaries;
   handle partial I/O and record unmatched returns. Validate offline decode against
   captured plaintext and parser acceptance, including consecutive frames in both
   directions, not only checksums. Keep lab credential plaintext out of summaries.
5. Bind evidence to this new run, client/DLL hashes, exact seed and pre/post state.
   Existing golden traces are controls only. Do not rename/replay old traces as fresh.

The zero-seed fixture's first 16 key bytes are zero. Its six-byte oracle admits
multiple equivalent offsets and cannot independently establish an offset. Capture
larger packets that exercise distinguishing key bytes and compare actual parser
plaintext. Fresh arbitrary nonzero-seed validation remains unproven.

## Regression Scope

`tests/research/test_crypto_bounds.py` calls the actual `God2DecodePacket` export
from the existing DLL through ctypes. Fixed RNG seed 0x60D2 drives 256 cases with
valid positive controls (including lengths 4 and 258), invalid lengths, header high
bits, mismatched header lengths, checksum mutations, invalid key sizes, feedback
above 255 and insufficient output capacities: 2048 ABI calls total. Every pointer
refers to an allocated buffer and every advertised source/key span is allocated.
Output has leading/trailing canaries; rejected calls must leave all output untouched,
and inputs/keys must remain unchanged. No arbitrary invalid pointers are passed.

Synthetic random keys exercise the decoder ABI; they do not prove the original
client derives or uses those keys. The existing frozen-frame test remains the
stock zero-seed control. These tests are bounded deterministic regression, not
guard-page/ASan coverage and not runtime crypto qualification.

Executed results: `python -B tests/research/test_crypto_bounds.py` passed (one
test, 2048 ABI calls); `python -B tests/research/test_packet_probe_dll.py` passed
(five existing tests). Both loaded the existing DLL; no rebuild was performed.
Only this new document and the new regression file were written by AGENT-D.
