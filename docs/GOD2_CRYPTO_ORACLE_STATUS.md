# Crypto Oracle Status

Status: **ORACLE_EQUIVALENT_OFFLINE**. `CRYPTO_RECOVERED=false`.
No original client process, GPU or candidate search was used in this work.
Historical UNIQUE_CANDIDATE evidence and --recover-crypto diagnostics are unchanged.

## Delivered

- `build-crypto-oracle/Release/God2CryptoOracle.exe`: local launcher for the
  pinned Unicorn x86 interpreter. Supports init-session, encrypt, decrypt,
  deterministic entry-snapshot replay and batched requests in one process.
- `god2-crypto-diff.exe`: original captured instructions against clean C++.
  Each mismatch reports the first differing output/state byte and enables
  instruction/register/memory trace only for that failing vector.
- `God2CryptoClean.dll` and `src/crypto/God2CryptoClean.*`: arbitrary 16-byte seed
  initialization, separate TX/RX state, key cycling, packet-reset feedback,
  disabled-cipher behavior and raw transforms up to 4096 bytes. No extracted
  executable bytes or lookup table are embedded in clean source.
- `ICryptoBackend`, Clean adapter and a default-off local Python OracleLab adapter.
  OracleLab requires explicit lab/nonproduction mode and numeric loopback identity.
  The adapter performs no socket binding and is not wired into the C++ socket server.
- `generated/crypto_candidate.cpp`: compiled transform candidate mechanically
  emitted from hash-bound static instruction motifs. It is not the production API.

## Capsule And Evidence

`artifacts/crypto-oracle/capsule/capsule.json` binds the original EXE, restored
image, exact function ranges, full source pages, dependencies and lookup table.
Only seven directly reachable functions (540 code bytes) and the declared
1024-byte lookup table are extracted. No API stubs or unrelated client routines.
Tampering, mixed sources, path escapes and unresolved call targets are rejected.
Code/data access, executable ranges, input bounds, instruction count and timeout
are enforced by the emulator. Every memory read/write and code fetch is counted.

Entry snapshots contain registers including EFLAGS, stack, buffers, object and
memory mappings. They are explicitly **SYNTHETIC_EMULATOR_ENTRY**, not claimed
live debugger captures. Replay validates the exact canonical register/map layout
and hashes. Arbitrary live register/stack snapshots are not yet supported.

The capsule, snapshots and corpus remain local, ignored by source control and
excluded from production installation. Corpus inputs are generated crypto-unit
data, never real credentials. Snapshot memory maps contain extracted code and
must not be distributed. A dedicated OS-restricted live-credential store is not
implemented; future live credential import must fail closed or use controlled data.

## Executed Verification

- `artifacts/crypto-oracle/diff-002/differential-report.json`: 32 seeds, 2048
  original-x86 versus C++ TX/RX calls, zero output and full-object state mismatches,
  57.047 seconds. This is the throughput run, not live-client qualification.
- `diff-003`: 3 sessions, 96 calls, upgraded replayable entry snapshots and raw
  clean/oracle corpus fields. Independent raw-evidence corpus audit passes.
- Feedback remained unchanged on 92 nonempty transform calls in the audited
  corpus. Last-input and last-output persistence rules each contradicted 87 calls.
  Key bytes remained unchanged. Offset restart is instruction-proven, not an
  invented persisted state field; protocol transition resets were not observed.
- 53 focused capsule/clean/oracle/guardian/integration tests passed. Injected
  differential faults correctly produce traces and cannot promote recovery.
- 12 focused production CTests passed; the full long-running research suite was
  not rerun. Production Release server/tests build succeeded.
- Production configuration with GOD2_ENABLE_ORACLE_LAB=ON failed as intended.
  An actual local install under `artifacts/crypto-oracle/release-audit` contained
  no oracle tool, Unicorn, capsule, extracted lookup or original God2.exe.
- Five bounded subagents completed and were closed.

## Remaining Boundaries

The dynamic mismatch IR is witnessed, SSA-like data, not a general lifter.
Register-alias normalization and aligned clean-instruction tracing are incomplete;
FIRST_SEMANTIC_DIVERGENCE stays unknown, rather than inventing a root cause.
Static transform generation and differential testing work; automatic initializer
generation and arbitrary-routine lifting are not claimed.

Live cross-oracle capture, automatic future-client corpus append, the nonzero-seed
socket-server path, and two fresh client sessions remain unimplemented/unexecuted.
The official native Computer Use channel was rechecked and still returns native
pipe unavailable, os error 2. No alternative UI input helper was used.

Protocol frontier is unchanged: captured six-byte server-selection C2S;
next direction/response contract not observed. No Character/World packets were
fabricated. Qualification cannot promote until fresh Clean-backend live sessions
A/B prove both directions, parser acceptance, distinct seeds/keys and continuity.

## Reproduce Locally

```powershell
python -m pip install --target artifacts/tooling/crypto-oracle-python -r tools/crypto_oracle/requirements.txt
cmake -S tools/crypto_oracle -B build-crypto-oracle -DGOD2_ENABLE_ORACLE_LAB=ON
cmake --build build-crypto-oracle --config Release
.\build-crypto-oracle\Release\god2-crypto-diff.exe --capsule artifacts/crypto-oracle/capsule/capsule.json --output artifacts/crypto-oracle/new-run --seeds 32 --vectors-per-seed 32
```

Use a new output directory; evidence is never silently overwritten. Original
source files must retain their pinned hashes. These tools require the local
Python/runtime dependencies and are not standalone distributable applications.
Engine API reference: https://www.unicorn-engine.org/docs/tutorial.html
