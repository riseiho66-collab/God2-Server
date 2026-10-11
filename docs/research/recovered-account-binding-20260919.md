# Recovered Account Binding

## Implemented

The original 176-byte credential request now has an opt-in path into the
existing SQLite account repository, executed on the serial game executor.
The network strand pauses reads while that work is outstanding and defers
disconnect completion until the game callback acknowledges it.

- Existing account: verify its password hash, then bind `Session::account_id`.
- Unknown account: reject unless `local_account_registration` is explicitly true.
- Registration: commit the account before binding or queuing any login success.
- Bad credentials, malformed input, unsupported hash or database failure: close
  without inventing a client error-result code and without sending success.
- Login does not fabricate a character, choose a map, or initialize world stats.

The original client input field provenance is recorded in
`tools/strike_lab/c2s0002.py`: account bytes are logical 1..24, password bytes
25..156, with forced final NULs. Account identity is a namespaced lowercase hex
encoding of the exact bytes before NUL (`god2-bytes:`). This preserves bytes;
it is not a claim about client text encoding, display names or case folding.
The repository retains the existing account schema. Passwords use Windows CNG
PBKDF2-HMAC-SHA256 with random salts, never plaintext database values or logs.
The non-Windows hashing backend explicitly fails closed.

## Activation

`config/recovered-account-login.json` opts into both recovered authentication
and local first-login registration, with a separate `artifacts/recovered-accounts.db`.
It is loopback-only, non-mock, and still requires the unverified character-list
candidate opt-in. Other existing configurations preserve their prior behavior.

The existing runner accepts `--recovered-account-auth` only alongside
`--legacy-character-list-candidate` and that option's prerequisites. It selects
the above configuration; it does not supply or automate any UI interaction.
For pre-provisioned-account-only operation set `local_account_registration=false`.

## Verification

On 2026-09-19:

- Release build succeeded.
- The new account configuration bound `127.0.0.1:2592`, loaded the existing Lua
  bootstrap, and exited cleanly after a one-second startup check. The world's
  map remains the existing mock map, not a recovered playable world.
- 16 CTest suites passed (research artifact/gate suites excluded in this run).
- `test_recovered_account_server.py`: 5 tests passed against actual loopback
  C++ processes, including process restart with registration disabled, wrong
  password, empty/corrupt input, fragmented request and forced SQLite failure.
- Existing prefix/character-list/create/fragmentation/current-handler suites:
  26 Python tests passed.
- Runner tests: 18 passed.
- Password-hash unit tests include an independently computed PBKDF2 vector,
  binary input, malformed encodings, fixed rounds and password bounds.

This establishes local wire-to-account persistence and authentication, not
fresh original-client acceptance. No new original-client UI login, character
creation, world entry, or playable-world claim is made. Character creation is
still validated structurally but not committed or acknowledged by this path.
