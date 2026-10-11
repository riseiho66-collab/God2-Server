# Controlled Capture Attempt

## Observed Result

No runtime capture or unpacked image was obtained. G02 remains BLOCKED and the
project remains L1 / Research / Partial Compatibility. No reviewer policy,
attestation or certificate was created.

Windows Sandbox `b8b84bab-3ffc-45e2-8caf-f29225e6798c` was started with networking,
clipboard, audio/video input, printer redirection and vGPU disabled. Inside it,
the network probe found no non-loopback IP addresses. Original client and tools
were mapped read-only; only a dedicated output directory was writable.
Client resources were copied inside the disposable sandbox. The measured
original and working-copy SHA256 matched:
`fb72296cab5950b74d8f7c98155145f7c5f58749c3011adb0540325b60749dd1`.

Official x64dbg release 2026.05.27 was downloaded and the archive matched the
published SHA256:
`d41966dfc5b435a372798245300ca0ab7bb8e48bdbf48512c6fb20fcca427697`.
Launch attempts for its x86 `headless.exe` failed before debugger startup.
The captured exception states Application Control blocked execution; Code
Integrity event 3077 names `C:\Debugger\headless.exe` and policy
`{0283ac0f-fff1-49ae-ada1-8a933130cad6}`. No client PID, native trace or memory
dump exists. Empty stdout files are not runtime evidence.

The sandbox was stopped after preserving diagnostics. No host execution of the
client/debugger was attempted and no security policy was disabled. The next
capture requires an approved debugger executable/environment permitted by the
machine's application-control policy, followed by another isolation check.

## Preserved Local Records

`artifacts/capture_work/sandbox-b8b84bab/output/` contains environment probes,
working-copy hashes, launch logs, `startup3-error.txt`, debugger file inventory
and `code-integrity.json`. Treat these local diagnostics as restricted; they
are not sealed runtime bundles. Tool archive/extraction is under
`artifacts/toolchains/`. Both directories are excluded from source control.

## Regression Record

Before modifications, Debug and Release builds succeeded, CTest passed 14/14
in each configuration, and independent Python discovery passed 49 tests.
All three archived artifacts passed integrity verification.

After the counter-resolution and manifest-v2 changes:

- `cmake -S . -B build`: PASS.
- `cmake --build build --config Debug --parallel 4`: PASS.
- `ctest --test-dir build -C Debug --output-on-failure`: 15/15, 119.01 seconds.
- `cmake --build build --config Release --parallel 4`: PASS.
- `ctest --test-dir build -C Release --output-on-failure`: 15/15, 117.81 seconds.
- `python -m unittest discover -s tests/research -p 'test_*.py'`: 57/57, 119.105 seconds.
- `python tools/research/artifact_vault.py verify`: 3/3 PASS, STATIC_ONLY.
- PowerShell parser check of `sandbox_capture.ps1`: PASS. Its final diagnostic
  logging changes are syntax-checked, not runtime-validated after sandbox shutdown.
- Original client SHA256 rechecked unchanged; `wsb list --raw` returned no environments.

The generated `docs/generated/zenith-20260918-resolution/` snapshot records zero
captures, reviews and certificates. Synthetic test fixtures do not establish
human approval or runtime compatibility. No subagents were started for this increment.

## Primary References

- [Windows Sandbox CLI](https://learn.microsoft.com/en-us/windows/security/application-security/application-isolation/windows-sandbox/windows-sandbox-cli)
- [Sandbox configuration](https://learn.microsoft.com/en-us/windows/security/application-security/application-isolation/windows-sandbox/windows-sandbox-configure-using-wsb-file)
- [Pinned official debugger release](https://github.com/x64dbg/x64dbg/releases/tag/2026.05.27)
