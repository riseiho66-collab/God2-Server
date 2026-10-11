# Recovered Dual Connection

## Scope

This implements the two-transport boundary established by the current pinned
client, not a claim of a fresh client login or playable world. Source evidence:
`current-login-character-socket-topology-20260919.md` and
`current-existing-character-selection-20260919.md`. Original single-socket lab
modes remain regression fixtures; they are not a topology acceptance proof.

Opt in with `config/recovered-dual-connection.json`, or the existing capture
runner's `--recovered-dual-connection` together with its character/account and
zero-UI candidate prerequisites. The runner option adds no desktop actions.

## Implemented Flow

```text
L: seed -> 01/53 -> C2S04 -> account verify/register -> 1D
   -> 04 + 05(actual G address/port) + 06(route ID 1) -> 0A
   -> A6 -> account-owned 07, populated record W[32] = 1
G: independent TCP + seed -> 01/F6 -> C2S00
   -> independently verify stored account/password -> 1F candidate
   -> C2S1A -> verify account-owned saved slot -> 02/result WORD 0
   -> CharacterSelected, NOT InWorld
```

G also supports the implemented 1B profile commit and post-create 18/1A path.
Its cold-start UI reachability remains unqualified. Existing selection does not
require an 18 request/reply. L rejects character creation/selection when the
dual-connection option is enabled. No account ID is borrowed from another socket.
G rejects unregistered accounts even when L first-login registration is enabled.
Passwords stay out of ordinary logs; existing PBKDF2 storage is unchanged.

The listener's port is selected by the OS when `server.character_port` is zero,
then the actual bound value is serialized in 05. This is not a guessed original
G port. Only IPv4 loopback endpoints are supported, with distinct listener ports.
`max_sessions` applies separately to each listener. Process-wide session IDs
avoid collisions in shared disconnect/world callbacks. Both listeners share the
same serial game thread, repositories and existing Lua runtime, and both drain
on server shutdown. No Lua gameplay or world schema was replaced.

## Candidate Boundaries

S2C1F has the current parser's required 124-byte payload and valid zero-seed
envelope/checksum. Its opaque payload is zero-filled as an explicitly unverified
lab candidate; it is not a recovered inventory, status or world schema. Route
record opaque bytes also remain candidate values. Current parser-slice acceptance
in synthetic memory must not be promoted to live rendered-client acceptance.

The 07 populated profile projection and local two-slot/name-uniqueness policies
retain the limitations documented in `recovered-character-persistence-20260919.md`.
Normal selection checks the authenticated account's persisted slot. Invalid
checksums, unknown slots, mismatched credentials and unknown next contracts fail
closed without fabricated client error IDs. Database writes precede create ACKs.

The next known world receive gate is S2C2A, 36 payload bytes. This base
configuration does not send it as zero or guessed coordinates.
The ordinary fixture World still contains mock map 1, but recovered selection
does not instantiate that mock player or enter it.

Follow-up: `recovered-world-entry-20260919.md` documents a separate explicit
opt-in for a hash-pinned historical 2A body plus the current initialization tail.
The base dual-connection configuration described here still stops after selection.

## Verification

Release build and 20 core CTest suites passed after the dual-listener change.
The seven current-client existing-selection Unicorn tests passed, including
01/F6, exact 1F copy length, ordinary 1A without 18, and result-WORD semantics.
A one-second launch of the new configuration bound L at 127.0.0.1:2592 and an
OS-assigned G loopback port, loaded Lua, and shut down cleanly. That startup did
not create an account/profile and was not an original-client session.

Final verification after integration:

- 20 core CTest suites passed (research aggregate suites excluded).
- 59 existing related Python regressions passed: account/profile persistence,
  old single-socket candidates, fragmentation, current builder/handler slices
  and capture runner configuration selection.
- 20 additional/targeted Python tests passed in one run: seven dual-connection
  scenarios, six route-advertisement tests and seven existing-selection slices.
  The dual tests derive G's endpoint from the received 05 frame, create both
  slots via actual C++ TCP/SQLite, restart the process, and select a saved slot
  while independently closing L. Negative cases include wrong credentials,
  G auto-registration, wrong opcode/checksum/slot/account, L character requests,
  and malformed configuration. Packet-dump mode is enabled for privacy checks.
- The route tests compile the C++ header fixture in a private directory and
  pass its actual output through the pinned client's original decoder, checksum,
  04/05/06 handlers and exact/fallback endpoint lookups. Guarded writes and
  boundary ports/route IDs are checked. Only formatting is stubbed in lookup;
  this remains synthetic memory, not live client execution.

Build command: `cmake --build build --config Release --parallel 2`.
Core command: `ctest --test-dir build -C Release --output-on-failure -E
'artifact_vault|runtime_evidence|gate_review|counter_resolution|runtime_environment'`.
Targeted command from `tests/research`: `python -B -m unittest
test_recovered_dual_connection_server test_current_route_advertisement
test_current_existing_character_selection -v`.

Both bounded implementation/test agents were closed after review. No test
server, client or debugger process remained after the checks. No live-client
WORLD, movement or combat acceptance is claimed by these backend tests.
