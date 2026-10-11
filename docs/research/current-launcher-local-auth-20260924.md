# Current C++ launcher to own loopback server: account authentication

The owner reported that the launcher displayed a `God2 C++ Support` error and
did not reach the local server. The helper's saved `cpp-launch.error.txt` said
`close the running game before changing client language`. Six earlier
`God2.exe` processes had no main window and no established TCP connection.
They were ended after verifying those conditions; the server process and
persistent account database were left running. The helper's embedded endpoint
resource was `Host=127.0.0.1`, `Port=2592`.

The native C++ helper rebuilt the current unpacked client for `zh-TW` from its
verified base. The resulting `God2.exe` SHA-256 is
`128ab0301fccbd04ead4f04823aaec20929ec5ff483473108bc0fbb346921245`.
Its own offline build self-test produced identical bytes. A private Windows
desktop launched the helper and client without switching the owner's input
desktop or taking screenshots. The game reached an 800×600 window.

On the second private login probe, the original client process (PID 19928)
connected to loopback port 2592. The persistent own-server log records the
same run as session 3 at 15:10:18: seed exchange, `C2S0002` length 176/opcode 4,
successful account bind to the already existing test account ID 1, then
`S2C0003` length 176, the server list and login terminal response. The probe
closed the private game at 15:10:27. No account was added; account count remains
four and SQLite `quick_check` is `ok`.

The live observer originally reported an authentication timeout because it
read the rotating file before the server flushed its `info` messages. The
logger is configured to flush on `warn` for a console-plus-file run; the
subsequent direct socket check caused the buffered session-3 messages to
become visible. `artifacts/runs/launcher-local-check-20260924/verification.json`
freezes the ordered lines and `verify.py` rechecks them. The direct socket
check is session 5 and is **not** counted as original-client acceptance.

This proves that the reported launcher block was removed and that the current
original client sent a valid login to the own server. It does not prove
character selection, world entry or continuous play in this run. The server's
older native world evidence remains separate; further packet work must still
use a current-client world session and durable state checks.

## Owner's later login attempt

At 15:18:07 the owner launched the player version while the private probe was
running separately. Session 6 on the persistent server received the seed
exchange and a structurally valid 176-byte `C2S0002` credential request. The
account repository matched the existing `test` identity (account ID 2) and
reported `existing_account_password_mismatch`; the server did not record or
expose the password. Port 2592 and the independent character port 62616 both
remained listening afterward. This is a credential rejection, not a server
shutdown or a missing network route. The current server closes on this case,
and the client has no qualified, explicit wrong-password response. Recovering
the original login rejection packet remains an open protocol task; do not send
an invented result code to the client.

The separate private probe's test account reached an established character-port
connection, but that TCP observation alone does not certify a rendered world or
normal movement in this run. It was closed after the owner report.
