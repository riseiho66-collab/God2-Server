# Runtime Environment Matrix

Generated from local observations. Signed does not mean allowed; UNKNOWN does not mean blocked.

| Environment | Architecture | Isolation | Debugger / tracer | Signed / trusted status | Application Control result | Client execution result | Runtime capture capability | Owner approval required? | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Windows Sandbox / prior headless | x86 | Offline (prior record) | x64dbg headless.exe | NotSigned (inventory) | BLOCKED | Not attempted | Not established | YES: approved tool/lab | BLOCKED_EXTERNAL_POLICY |
| Windows Sandbox / installed Microsoft CDB | x86 | Offline; source read-only; output writable | CDB 10.0.29617.1000 | Valid | PASS | BLOCKED 4551 / event 3077 | Benign x86 debug PASS; GOD2 dump absent | YES: GOD2 authorization/lab | BLOCKED_EXTERNAL_POLICY |
| Existing WinDbg on host | x86/x64 | Host not isolated | Installed Microsoft WinDbg/CDB | Valid (inventory) | UNKNOWN on host | Not attempted | UNKNOWN on host | YES: isolated lab arrangement | UNKNOWN |
| Existing Visual Studio native debugger | x64 IDE / x86 monitor | Host not isolated | devenv / msvsmon | Valid | UNKNOWN | Not attempted | UNKNOWN in approved isolation | YES: isolated lab arrangement | UNKNOWN |
| Dedicated Hyper-V lab | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | Not attempted | UNKNOWN; VM enumeration unavailable | YES: owner/admin lab access | UNKNOWN |
| Owner-approved x86 debugger candidate | x86 | Sandbox candidate, not tested | Signed x32dbg.exe | Valid | UNKNOWN (not headless result) | Not attempted | UNKNOWN | YES: suitable client authorization/lab | UNKNOWN |
| Separate disposable owner VM | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | Not attempted | UNKNOWN; no environment supplied | YES | UNKNOWN |

## Current Blocker

Operational probe: `RUNTIME_ENVIRONMENT_READY` (historical; sandbox stopped).
GOD2 launch: `BLOCKED_EXTERNAL_POLICY`. CDB PID 4844 is NOT a client PID.
No GOD2 execution trace, mapped image, unpack transition or certificate was produced.

Owner/admin must provide an approved isolated lab allowing this exact original GOD2 executable and the Microsoft x86 CDB. Do not disable security controls.

## Evidence

- Inventory: `artifacts/reports/runtime-tool-inventory.json`
- Probe, raw launch output and Code Integrity events: `artifacts/capture_work/sandbox-3b1e597c/output`
- Machine-readable state: `artifacts/reports/runtime-environment-status.json`
- Policy ID: `{0283ac0f-fff1-49ae-ada1-8a933130cad6}`.
- The initial `.ps1` probe was rejected by script execution policy. No policy was changed; subsequent probes used normal native commands through the Sandbox CLI.
- WindowsApps sharing was access-denied; the readable Microsoft tool files were copied to a staging directory with unchanged executable hash/signature. No ACL was altered.

## References

- [CDB command-line options](https://learn.microsoft.com/en-us/windows-hardware/drivers/debugger/cdb-command-line-options)
- [Microsoft error enumeration: 4551](https://source.dot.net/Microsoft.Private.Windows.Core/Generated/Basic.CompilerLog.Util/Basic.CompilerLog.Util.Impl.BasicGeneratedFilesAnalyzerReference/Windows.Win32.WIN32_ERROR.g.cs.html)
