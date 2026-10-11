# GOD2 STRIKE LAB

OMEGA continuation: `God2LabLauncher.exe --observer omega --profile
PROFILE_STATICALLY_RECONSTRUCTED_STARTUP --run-id NEW_ID` narrows capture to
loader prerequisites and known network candidates. That profile temporarily
applies source-backed 800x600 DirectDraw INI settings and restores original
bytes. See `docs/GOD2_OMEGA_STATUS.md` for the exact asset and focus callback
blocker. It is not an official-launcher-equivalence claim.

Offline source validation:

```powershell
python tools/strike_lab/god2-systemmessage-validator.py ../God2/Data2/Patch/Comm/message.csvZ
```

First operational version. This is a targeted startup lab, not a completed
protocol reconstruction or a replacement debugger. Original client bytes,
system DLLs, prior captures, and certificates are not modified.

## Build

From the server repository in PowerShell:

```powershell
cmake -S tools/strike_lab -B build-strike-lab -A x64
cmake --build build-strike-lab --config Release --parallel 4
```

Requires VS2022 C++ tools, Windows SDK, local Python 3, and the existing
`build/_deps/json-src/include/nlohmann/json.hpp`. Static `report.py` additionally
uses the already installed Capstone and pefile packages. No downloads occur.

Outputs in `build-strike-lab/Release`:

- `God2LabLauncher.exe`: native command-line frontend to `lab.py` and the
  existing native CDB driver. Runs only the guarded, original-hash working copy.
- `God2Probe.dll`: x64 debugger-host extension, `!God2Probe.snapshot`.
  Reads target memory and debugger context; never injected into the client.
- `God2SnapshotDiff.exe`: compares contexts, modules, paths, resources,
  field-write sequences and the selected 96-byte object region.
- `God2LoopbackProbe.exe`: evidence-gated IPv4 loopback accept/read only.

The three EXEs require this checkout and the Python interpreter recorded at
build time. They are not standalone redistributables. No launcher UI is added.

## Reproduce

Use a new run ID for every invocation; existing evidence is never replaced.
Run profiles sequentially because they share one working copy.

```powershell
.\build-strike-lab\Release\God2LabLauncher.exe --profile PROFILE_DIRECT_DEBUG --run-id lab-direct-next
.\build-strike-lab\Release\God2LabLauncher.exe --profile PROFILE_LAUNCHER_EQUIVALENT --run-id lab-equivalent-next
.\build-strike-lab\Release\God2SnapshotDiff.exe artifacts/probe-runs/lab-direct-next artifacts/probe-runs/lab-equivalent-next --output artifacts/probe-runs/comparison-next.json
```

The launcher-equivalent profile reproduces only the known **private native
launcher** source context: `GOD2_CLASSIC_RESOLUTION=800x600`, generated
`config/display.settings`, and loopback-only `ctserver.ini`. Existing config
bytes are backed up in the run directory and restored in `finally`. This is
not a verified reproduction of the historical official launcher.

Both use the existing working directory and inherited DLL search environment,
with `127.0.0.1 127.0.0.1 6001 1`. Codepage and user locale are recorded, not
changed. Arbitrary cwd, command line, DLL path, creation flags and locale
overrides are intentionally not implemented in this first version; they would
require renewed identity/firewall/context validation. Debug creation flags
differ from the source launcher's undebugged flags=0.

## Observation Boundaries

API entry breakpoints are pre-armed at the initial native debugger stop.
Pre-candidate events are entry-only raw markers. At restored candidate
0x54A3E8, structured entry/return observation begins, together with hardware
write watches on count 0x6931A0 (2 bytes) and pointer 0x69319C (4 bytes).

CDB software breakpoints temporarily use debugger trap instructions in the
debuggee; no semantic instruction patches, forced branches, register writes,
API return substitutions or system DLL changes are used. The extension itself
performs reads only. Native execution-mode proof is not inferred from an
effective-machine display or from the extension's PC alone.

API coverage includes environment, file, resource, registry and all requested
Winsock entry names. High-volume ReadFile/GetFileSize/SetFilePointer/CloseHandle
are restricted to immediate callers inside the client image. This avoids
exhausting the budget on graphics-driver file reads; it is not full-process IO
coverage. Only one API return is pending at a time; nested replacement and
PID/TID/stack mismatch are recorded. Raw stack unwind warnings are retained.

GetLastError/WSA error semantics are not qualified with current local symbols.
WSASend/WSARecv entries are armed but asynchronous/scatter-gather payload
completion is not implemented. Environment values are allowlisted in context
snapshots, and queried environment values are not dumped. No login credentials
are supplied. Raw future network captures must use test credentials only.

S4/S5 snapshots are absent when the SystemMessage initializer is never reached.
The exact external SystemMessage filename remains unknown. INITIALIZER_NOT_CALLED
is scoped to the monitored restored-candidate-to-failure window, not all
possible paths, process lifetimes or builds.

## Loopback Guard

No port is currently runtime confirmed. The listener therefore must not run.
When a real loopback `connect` entry is captured, the launcher can emit
`connect-evidence.json` with a copied, SHA-256-bound native log and a raw
sockaddr marker. Only then use:

```powershell
.\build-strike-lab\Release\God2LoopbackProbe.exe --evidence artifacts/probe-runs/ACTUAL_RUN/connect-evidence.json --output artifacts/probe-runs/NEW_SESSION
```

The first listener sends nothing, accepts one connection, and saves bounded
raw TCP reads (maximum 1 MiB, default 30 seconds). Read chunks are not labeled
protocol packets. `raw.bin` and `session.json` contain bytes and hex. Scripted
responses, plaintext credential processing and packet framing are not added.
Evidence checks prevent accidental guessed-port use, not deliberate forgery
by someone who can rewrite both the log and its metadata.

## Tests

```powershell
python -m unittest discover -s tests/research -p test_strike_lab.py -v
python tools/strike_lab/report.py --run lab-equivalent-final-01 --output artifacts/reports/NEW_REPORT
```

See `docs/GOD2_STRIKE_LAB_STATUS.md` for actual runs, failures and next blocker.
