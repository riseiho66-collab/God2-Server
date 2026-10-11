# Verification Record

Date: 2026-09-18, Asia/Taipei. Project: C:/Users/risei/Desktop/God2/God2-Server.

## Artifact Integrity Extension

After the C++ baseline below, the independent Python research tool and its CTest
registration were added. C++ source was unchanged. Reconfigured CMake and ran
`ctest --test-dir build -C Release --output-on-failure`: **12/12 passed, 9.93 seconds**.
The new artifact_vault suite contains 17 checks. Python is 3.12.10 with pefile
2024.8.26. All three real captured client artifacts pass read-only integrity
verification. Four input paths were recorded, with identical content deduplicated.
See [RECONSTRUCTION_STATUS.md](RECONSTRUCTION_STATUS.md) for scope and reports.
The Debug result below remains the earlier 11-case C++ baseline.

## Build Environment

- Windows x64; Visual Studio 2022 Community, MSVC toolset 14.44.35207.
- Windows SDK 10.0.26100.0; CMake 4.4.2; C++20.
- Both Debug and Release built successfully, including god2-server.exe,
  protocol-replay.exe and god2-tests.exe.
- Dependency versions and archive SHA256 checks are pinned in cmake/Dependencies.cmake.

Commands executed from the project root:

```powershell
cmake -S . -B build -G "Visual Studio 17 2022" -A x64
cmake --build build --config Debug --parallel 4
ctest --test-dir build -C Debug --output-on-failure
cmake --build build --config Release --parallel 4
ctest --test-dir build -C Release --output-on-failure
```

## Final Results

| Configuration | Result | Measured CTest time |
| --- | --- | --- |
| Debug | 11/11 passed | 2.45 seconds |
| Release | 11/11 passed | 2.10 seconds |

Each named CTest case is a suite or integration scenario with multiple checks:

| Case | Coverage |
| --- | --- |
| packet | Exact endian bytes; integer/float/string round trips; truncation; cursor preservation; buffer aliasing |
| decoder | Every split boundary; byte-at-a-time input; coalesced frames; malformed length; maximum size; identity transforms |
| dispatcher | Registration; duplicate rejection; unknown opcode; malformed handler input; continued dispatch; state rejection |
| lua | Bootstrap and registrations; dialogue validation; copied records; rooted require; errors; reload rollback; instruction budgets |
| session_state | Allowed and rejected login/world/battle/heartbeat states |
| protocol_replay | Valid and invalid hex; truncation; encoded fixtures and parse-error reporting |
| database | Initialization; migrations; foreign keys; prepared bindings; persistence; rollback; immutable migration history |
| network | Actual loopback TCP with three network workers and a separate game thread; complete mock flow; fragmented/coalesced requests |
| config | Modes/backends; loopback-only mock login; integer ranges/types; overflow; path resolution |
| application_startup | Real server executable initializes config/logging/SQLite/Lua/world/TCP, then performs timed shutdown |
| cli_invalid_duration | Negative --run-for value rejected with a nonzero exit code |

The network scenario verifies handshake, mock login, character list, selection,
world entry, movement persistence and broadcast, chat, Lua NPC dialogue,
heartbeat, invalid state, unknown opcode and malformed payload recovery.
It also checks existing-player snapshots, rejection of an already-online
character, recovery when another session wins a select/enter race, malformed
frame disconnect, login-log redaction, and exactly-once disconnect cleanup.
Shutdown closes still-connected clients without the test watchdog intervening.

The application smoke test uses an ephemeral loopback port and a database/log
under build/tests. Repository and Lua fixture tests use memory or temporary
fixtures rather than changing installed client data.

## Manual Executable Checks

- Debug server --run-for 2: listened at 127.0.0.1:7000 and stopped cleanly, exit 0.
- Replay of `04 00 00 10 04 00 05 10`: two frames, length 4,
  opcodes 0x1000 and 0x1005, empty payloads.
- Release replay of `03 00 00 10`: `Packet length is smaller than header`, exit 1.
- Test server processes were stopped; this delivery does not leave a service running.

## Scope And Remaining Work

These checks validate the PLACEHOLDER framework, not GOD2 client compatibility.
No client executable was launched or modified. The original client SHA256 after
work remains FB72296CAB5950B74D8F7C98155145F7C5F58749C3011ADB0540325B60749DD1.

Phase 0 has static evidence and a documented research workflow only. An unpacked
image, repaired IAT, verified OEP, real packet captures, opcodes, crypto and payload
schemas remain unavailable. No claim of successful real-client login is made.

UDP, AOI filtering, complete combat, inventory/shop, real authentication,
MySQL/MariaDB and SQLite export remain deferred. Lua quest/AI/GM registrations
are extension hooks, not complete gameplay systems. Lua instruction budgets
handle accidental loops but are not a hostile-code sandbox or memory quota.
SQLite work runs on the game thread and can delay gameplay under contention.
Linux/macOS builds, sanitizers, long-duration load tests and production operation
were not verified in this Windows delivery.

## APEX Runtime Intake Verification

2026-09-18: after CMake reconfiguration, Release CTest passed **13/13 suites**
in 24.39 seconds. Research suites contain 17 artifact-vault tests and 18 runtime
evidence tests. Runtime tests use temporary fabricated PE files and traces only;
none of these fixtures were imported into the real research vault.

Runtime coverage includes schema/path/hash/ordering checks, capture and index
tampering, sealing without source mutation, synthetic-data blocking, unpack/OEP
consistency, resolved import/export address checks, repaired-image quality,
Winsock name mismatch, counter-evidence, idempotency and generated reports.
Even a fully consistent fabricated bundle cannot become VERIFIED.

All three archived artifacts pass verification again; the original client,
God2-run and Launcher-src executable hashes still match the Gate 01 inventory.
The generated capture request is correctly rejected as incomplete (missing
capture time), rather than being counted as runtime evidence.

See [current generated status](generated/apex-20260918/RECONSTRUCTION_STATUS.md)
and [capture contract](../tools/research/RUNTIME_CAPTURE.md). No debugger adapter
was executed, no real runtime capture exists, and independent runtime review,
forwarded-export handling and asynchronous socket reconstruction remain unverified.

## ZENITH Review Verification

2026-09-18 final Release regression: **14/14 CTest suites passed in 56.60 seconds**.
Python coverage is 49 tests: 17 artifact-vault, 18 runtime-intake, 14 gate-review.
An integration failure caused by deferred module import was fixed before this run;
both standalone research suites and the complete CTest run now pass.

The new suite covers absent reviewer policy, self-approval, missing attestations,
untrusted identities, incomplete checklists, missing evidence references, synthetic
source rejection, review versus promotion, idempotent proof objects, prerequisite
chains, revocation propagation/blast radius, rejected-review resolution, cross-capture
counter-evidence, changed validator version, withdrawn reviewer authority, source/
proof/index corruption, forbidden reissue and generated status/contradiction reports.

All promotion scenarios use temporary fabricated data and fixture reviewer policies.
Some fixtures deliberately declare runtime provenance to exercise the local review
workflow; this demonstrates logic, not real capture authenticity or human identity.
There is no real review-policy.json, review, certificate or capture in the project
vault. The three original executable hashes still match Gate 01, and all archived
artifacts pass integrity verification. No original client was executed or modified.

The [final generated status](generated/zenith-20260918-final/status.json) remains L1,
Gate 02 BLOCKED. Identity signatures, concurrent review service operation, portable
proof export, actual human review and real runtime gate acceptance were not tested.
