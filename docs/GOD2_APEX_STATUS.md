# GOD2 APEX Runtime Status

Latest network continuation: see GOD2_NETWORK_STATUS.md. SOCKET_CREATED and
CONNECTED are now verified at 127.0.0.1:2592; FIRST_TX remains false. The records
below describe the earlier startup acceptance checkpoint, not the current ceiling.

## Intervention

MODE_OBSERVE adds no compatibility writes (debugger breakpoints still instrument execution).
MODE_COMPAT redirects only GOD2's known timeGetTime pointer at 0x5707BC to
a private eight-byte x86 tail bridge, forwarding to the real API. The bridge
provides the expected leading byte without forcing a branch or API return.
God2Compat.dll is loaded into CDB, not injected into the client. Installation
checks the exact working-copy path, compatibility-site bytes and API symbol.
No archived executable or Windows DLL is patched on disk. Existing network
block rules remain enabled. The pointer is restored before process teardown.

## Result

- Baseline: artifacts/runs/apex-observe-02, OLD_COMPAT_FAILURE.
- Final rebuilt bridge: artifacts/runs/apex-compat-final-01, ACCEPTED.
- Graphics initialization returned with EAX=1.
- Table enumeration and actual SystemMessage loader executed.
- String-table pointer became nonzero; completed count is 1950.
- Same client session continued with Winsock observation armed.
- Latest run: artifacts/runs/apex-native-ui-04, WINSOCK_REACHED, exit code 0.
- Memory warning matched and closed by real BM_CLICK; same-process execution resumed.
- WSAStartup returned 0 at client address 0x411C82 (return RVA 0x11C82).
- PRE_NETWORK_STARTUP is CLEARED; CONNECTED and FIRST_TX remain false.
- No real packet, framing, login or world compatibility is established.
- x86 bridge semantics test passed 5000 calls against real timeGetTime bounds.
  This is a bounded forwarding/ABI test, not a general timing guarantee.

## Next Stop

NativeDialogController is compiled into the runner and CompatHost. No external
UI pipe is required. It checks the exact work-copy executable path, PID/TID,
dialog class, observed title ("\u932f\u8aa4") and exact warning text. It sends one
BM_CLICK and verifies destruction; no memory query, API return, branch or stack
is changed. Native Windows on this host exposes the sole OK button as ID 2;
the controller prefers IDOK, then permits only a sole exact OK-labeled button.
There is no duplicate-click fallback after an ambiguous timeout.

Nine focused Python tests and the real MessageBox fixture passed, including
wrong PID/title/text rejection. Run 01 exposed an exclusive-create scoreboard
bug; run 02 exposed UTF-8 decoding; both are fixed and retained. Run 03 reached
successful WSAStartup twice but subsequently timed out awaiting another stop.
Run 04 stops cleanly at the matched successful WSAStartup return. It does not
attempt socket/connect after that boundary. The next task is network startup
continuation, not memory-warning work. No port is runtime-confirmed yet.

## Run

From the server directory, use a unique run ID:

```powershell
.\build-strike-lab\Release\god2-strike-runner.exe --mode MODE_COMPAT --run-id apex-next-01
```

God2CompatHost.exe offers the same command arguments and shared Python backend;
these are local lab entry points, not standalone redistributable launchers.
Each run writes structured state/events and logs under artifacts/runs/<id>.
Networking capture is pre-armed; only WSAStartup has been exercised so far.
Existing firewall rules may also block loopback. Port 6001 remains unconfirmed.
Automatic cross-run SnapshotDiff integration is not implemented yet.
