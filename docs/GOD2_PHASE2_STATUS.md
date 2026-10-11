# Phase 2 Startup Results

Native WOW64 qualification remains unchanged. No legacy x86 tracing resumed.
Master 02 and four focused follow-ups used the original-hash work copy with
existing firewall blocks. No remote endpoint, login credential, response
packet, instruction patch, register override or system-policy change was used.

## Progress And Blockers

Both controlled argument sets passed parsing and reached 0x531E28:
`127.0.0.1 127.0.0.1 6001 1` and `127.0.0.1 127.0.0.1 6001 0`.
Only argument 4 varied. Both reached the same later error-display path; no
evidence justified varying IPs or brute-forcing more values.

The baseline progressed into window, audio and graphics initialization, then
read address zero at 0x54CF19. Delivering the first-chance exception to the
client with `gn` produced second-chance exception 0xC000041D. This is not a
normal return or a successfully handled exception.

The earlier check is now directly observed: slot 0x5707BC points to
winmm!timeGetTime (0x74147860 in this session). Client instruction 0x45B662
expects the target's first byte to be 0x83; the native memory dump starts
`FF 25`. JE at 0x45B665 is not taken, and one step reaches 0x45B667.
This proves an implementation-byte check mismatch. It does not establish
why the check exists or authorize modifying the API/check to satisfy it.

At 0x45B7A4 the object string-table count and pointer are both zero. Static
code takes a null format pointer into 0x547AF7, consistent with the captured
fault. The reason the string table is empty remains unknown. Optional NVIDIA
profile-file lookup failures also appeared, but are not classified as client
resource failures merely because CreateFile returned INVALID_HANDLE_VALUE.

## Network Status

No monitored WSAStartup, socket, connect, send, recv, WSASend, WSARecv,
gethostbyname, getaddrinfo or inet_addr entry was observed before these stops.
Port 6001 is a test argument, not yet a runtime-confirmed destination.
No listener was started; no packet or framing claim exists. Full startup,
connection, handshake, login, character screen, world, heartbeat and movement
remain NOT ESTABLISHED. G03 remains NEED_MORE_EVIDENCE; G04 is UNVERIFIED.
Master 02 has raw G02 images but no new certificate. Prior G02 receipts remain.

## Evidence And Checks

Reports: `artifacts/reports/strike-phase2-20260919/` contains
`startup-blockers.json`, `argument-matrix.json` and `scoreboard.json`.
Raw events retain caller stack, API entry arguments, available return values,
timestamps, PID/TID, exception records, module lists and memory snapshots.
Collector changes now check stdcall return stack/identity before accepting
API return correlation. Two focused parser/return-validator tests passed;
the complete project suite was not rerun.

The final native exception in master-02b was initially displayed with forced
x86 registers. That truncated PC is explicitly excluded from usable evidence;
the later collector records native exceptions with typed amd64 registers.
Native exception code and earlier x86 fault remain available in the raw log.

Restricted archive: `artifacts/capture_work/god2-phase2-archive-20260919/`.
All client/debugger processes started for this work have ended.

Next work should establish a supported runtime/compatibility path and the
empty string-table cause without bypassing the validation check, then resume
the Winsock observation. Building guessed network replies cannot resolve
this pre-network blocker.
