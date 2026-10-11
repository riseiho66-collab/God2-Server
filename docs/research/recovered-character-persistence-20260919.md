# Recovered Character Persistence

## Topology Correction

The original same-socket path below is retained only as a synthetic persistence
regression. Current-client evidence establishes distinct login (L) and character
(G) transports; it must not be presented as the client's real connection flow.
Use `config/recovered-dual-connection.json` for the new two-listener candidate.
See `recovered-dual-connection-20260919.md` for implementation and evidence scope.

## Current Implementation

Opt-in `config/recovered-character-create.json` uses the recovered account
authentication service and the existing `artifacts/recovered-accounts.db`.
Runner option `--recovered-character-create` requires `--recovered-account-auth`
and its existing candidate-mode prerequisites. Original lab modes are unchanged.

```text
authenticated account
  -> A6 -> account-owned 07 list candidate
  -> 1B/48-byte request -> validate -> SQLite commit -> 02/result=0
  -> 18/5 bytes + 1A/41 bytes -> account/id/token check -> 02/result=0
  -> backend CharacterSelected (NOT InWorld)
```

The two post-create frames are buffered across TCP fragments/coalescing. No
unsolicited 07 is appended to the creation acknowledgement: current client
success sends 18 and 1A, and its result waiters discard unsolicited 07.
Only the post-create branch is implemented; normal selection of an existing
character may traverse other states and is not claimed implemented.

On reconnect, a new authenticated session's A6 reads its profiles from SQLite.
This verifies durable profile/list state, not a live UI showing that list.
The original client's state 8 copies the existing selected raw list record;
how the first-create UI populates that record still needs live qualification.

## Storage and Ownership

Migration 2 appends `recovered_characters`; migration 1 remains unchanged.
Each entity has an id, account FK, local slot, creation time, exact 40-byte
profile BLOB, and separately indexed raw name BLOB. The incoming builder's
constant byte 40 is validated; bytes 41..43 are unwritten stack tail and are
not stored as entity fields. The original encoded name is not converted to
UTF-8 or normalized. Name matching is exact byte matching.

Two slots and globally unique raw names are explicit local server policy,
not recovered original-server business rules. Allocation takes the first free
slot inside a transaction. A committed profile is not silently overwritten on
duplicate input. Reads reject inconsistent names, blob sizes, and slots.
Both repository ownership and same-session created-id checks gate selection.
SQL failures and unknown error mappings close without fabricating nonzero
client result codes or exposing names in logs.

No mock `characters` row, HP/MP, class assignment, map, position, or player
world object is created. These are identity/appearance profiles awaiting real
world initialization, not claims of fully playable characters. C++ owns the
network/storage path; existing Lua gameplay architecture remains untouched.

## Populated 07 Candidate Boundary

Current-client proofs are in `original-client-create-profile-20260919.md` and
`current-create-success-next-action-20260919.md`. Name termination, count <=2,
78-byte envelope, checksum, and optional receiver projection are tested.
Populated layout remains explicitly **UNVERIFIED** for the original live UI.

- Name: exact raw bytes, zero-padded 16-byte wire name area.
- W[17]: paired-category C[29], based on matching UI arithmetic.
- W[19]&7: local slot 0/1, an opaque selection token echoed by builder 14C50.
- W[20], W[22] bits 4..7, W[23]: corresponding appearance fields from the
  current create UI's matching resource consumers.
- W[24..31]: four two-byte component records. Current selection renderer
  `8310..852E` walks these records and calls `FFA20` with each second byte's
  high three bits. Current create preview `9A10..9A65` builds the same eight
  bytes from C[32] (component 0 variant), C[33] (binary bank), and C[36]
  bits 5..7 (component 1 variant):
  `C[33], C[32]<<5, C[33], C[36]&E0, C[33], 0, 80|C[33], 0`.
  This projection was connected on 2026-09-23 after the owner observed a
  female creation shown with a mismatched 3D head in the saved-character UI.
  The earlier candidate filled only W[24] and left seven bytes zero. The
  model/portrait fix still requires a fresh current-client visual retest.
- Remaining fields are zero placeholders for unknown server-owned data, not
  recovered original values. C[37], other unproven profile fields, and stats
  are not assigned guessed list semantics. The full profile is preserved.
- Empty-list output retains the earlier historical baseline byte-for-byte.

## Verification

Release build and 19 core CTest suites pass. Tests cover migration from v1,
binary names, ownership, global duplicate names, full accounts, transaction
rollback including deferred commit failure, corrupt stored records, and bounds.
The combined related Python run passes 58 tests, including old prefix, creation,
account, fragmentation, pinned-handler and runner regressions. The new config
also migrated the local account database, bound 127.0.0.1:2592, loaded Lua and
shut down cleanly in a one-second startup check. That check still reports the
existing mock map and is not a world-entry test.

`test_recovered_character_server.py` runs actual loopback C++ processes and
checks commit-before-ack, restart/readback, account isolation, both slots,
duplicate/invalid create rejection, database failure, fragmented creation,
coalesced/fragmented post-create frames and invalid token/checksum/order.

The list sent by C++ is decoded independently and fed to the pinned original
client's 07 handler in Unicorn with synthetic memory, for both raw and optional
converted output; guard writes are checked. The 18 and 1A follow-up bodies come
from executing the original x86 builders (including original bounded string
copy code), stopping before queue/network calls. Builder matrix tests cover
low-byte truncation, selection clamp, forced NULs and untouched stack tail.

None of these tests constitutes a fresh original-client login, rendered role
selection, world entry or playable E2E. The next world contract is still absent.
