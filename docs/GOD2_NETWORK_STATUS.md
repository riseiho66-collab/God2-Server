# GOD2 Network Strike

Superseded milestone: see GOD2_SERVER_FIRST_STATUS.md. Initial S2C, FIRST_RX and
FIRST_TX are now verified against the C++ seed-exchange mode. The passive-listener
results below remain the historical baseline.

- Furthest verified network milestone: CONNECTED.
- Evidence: artifacts/runs/network-strike-final-02 (repeated final-01 result).
- All four startup regression assertions passed; accepted compatibility code unchanged.
- Socket API: AF_INET / SOCK_STREAM / IPPROTO_TCP, successful socket return.
- socket client return RVA: 0x11D46; connect return RVA: 0x11E3B.
- Actual destination: 127.0.0.1:2592, raw sockaddr preserved under network/.
- connect returned 0 and the local listener accepted the connection.
- Existing firewall rules were retained; loopback succeeded without policy changes.
- Listener sends nothing; captured client stream remains zero bytes.
- FIRST_TX and FIRST_RX are false. No recovered frame or handshake is certified.

## Next Blocker

The client naturally reaches a main menu and then a credential form. Passive
waiting does not initiate a socket. An opt-in visual/PID-verified Enter Game
click and synthetic lab login trigger the real connection. No actual user
credentials are read or logged. Input-message success alone is not login success.

After connection, observed select return RVA 0x10D6D polls for readability and
returns zero; no recv or send was observed in the bounded run. This supports
investigating a server-first greeting, but does not establish its contents.
Only the actual wait callers were disassembled. Stack unwinding is unreliable
and is not treated as a proven caller chain. Do not invent a response payload.

## Run

```powershell
.\build-strike-lab\Release\god2-strike-runner.exe --mode MODE_COMPAT --run-id network-next-01 --timeout 30 --enter-game --test-login
```

Normal runs no longer stop on successful WSAStartup, socket, connect or send.
An optional --milestone-ceiling FIRST_TX/FIRST_RX requests a focused stop.
No ceiling is the default. select is sampled for eight entry/return pairs;
then its breakpoint is removed while recv/send observation remains armed.
Nested API returns are independently correlated (socket calls WSASocketW).
Timeout takes a PID-scoped window snapshot, requests a debugger break-in,
restores the compatibility pointer and terminates the lab process cleanly.
The last successful run ended at its configured timeout, not a client crash.

Current limits: listener is the runner's existing in-process sink, not a spawned
God2LoopbackProbe.exe. Async scatter/gather completion and packet metadata are
not yet verified with real traffic. UI templates reference preserved run images
and are intentionally restricted to this observed client/window size.
