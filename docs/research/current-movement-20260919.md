# Current Indoor Movement Integration

## Scope

Opt-in `config/recovered-movement.json` connects current C2S2E parsing to
`RecoveredMovementService`, the source-derived area2/scene15 indoor grid, and
S2C5D acknowledgements. Existing configurations retain their behavior. The lab
uses a separate SQLite database and loopback listeners; no official endpoint.
C++ owns transport, wire parsing, ownership and navigation validation. Existing
Lua gameplay infrastructure is unchanged; no invented Lua gameplay rule is added.

Qualification is native-code execution plus own-server loopback tests, **not a
live rendered client session**. The persistence follow-up now commits accepted
coordinates before ACK and restores them on reconnect; see
`current-position-persistence-20260919.md`. Speed/timing, diagonal corner policy, entities, scene
transitions and other post-world opcodes are not implemented by this change.
Public session state remains CharacterSelected, not a claim of InWorld.

## Evidence

Current mapped-image SHA-256:
`149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
Both legacy corpora were checked first; see
`legacy-movement-contract-20260919.md`. The old captured key, FF-only body tail,
modulo256 sequence and resource-dimension*21 bounds are not adopted.
All following addresses are hexadecimal RVAs in the current pinned image.

- `15790` builds opcode2E with two WORD coordinates, one BYTE slot and one
  **unwritten stack byte**. The opaque tail is not required to beFF.
- `132E0` queues records; `13370` flushes multiple records through the original
  zero-seed codec. Tests capture at `12501`, before the real socket send.
- `102700..10276B` asserts absolute dx and dy are each less than2. Caller
  `10253F` supplies the ring write index from world+236. World+230 is a speed
  field, not the movement sequence.
- `103640` initializes world+234's ring; `1036B0` enqueues; `103700` dequeues.
  The ring has40 slots, separate count/read/write bytes, and capacity39.
  Initialization enqueues the spawn point: first movement slot is1.
- Handler `692FA` consumes S2C5D: writes its byte to world+231, dequeues the
  oldest point and calls `6CC00`. After an ACK the queued target remains as
  the next baseline. Tests cross the40-slot wrap twice.
- Navigation is the961-byte original/C++-matched grid documented in
  `current-indoor-navigation-20260919.md`, not a rectangular dimension guess.

`test_current_movement.py` executes original builder, codec, ring operations
and ACK consumer. The `6CC00` effect publisher is stubbed and recorded; graphics,
input, timing and actor animation are not exercised. The step precondition test
stops before direction selection. These bounds on the evidence are intentional.

## Server Contract

`RecoveredMovement::parse_batch` validates frame length, checksum and every
logical opcode before returning records. Each record is seven logical bytes;
the native queue limit is0xA00 logical bytes. The exact zero-seed key cycles
after256 bytes. Malformed input cannot partially escape the codec.

The game-executor-owned service reserves an authenticated, owned character at
selection, projects its saved position, and activates movement on the valid
world-ready tail. The saved snapshot must still match at activation.
A duplicate character session cannot evict the existing binding. Each move
must have the next modulo40 slot, adjacent coordinates, and a nonzero raw grid
cell. This is an explicit limited lab policy, not a claim that all movement
conditions are recovered. A batch validates against a copy before publication.
Opaque tail values are ignored. The entire accepted batch is committed through
an ownership-checked SQLite transaction and prior-position comparison before
memory publication or5-byte ACK frames. Connection ring indices are not persisted.

TCP splitting and coalescing are supported, including a completed world tail
with a full first movement frame or a partial frame/header in the same read.
World binding finishes before pending movement is processed. Read buffering and
response queues are bounded; game callbacks gate disconnect cleanup. Invalid
input closes the session instead of inventing a success response.

Navigation is rebuilt from the compiled asset and checked against stored grid
bytes, dimensions, area/scene and the pinned source-hash metadata. This is local
asset consistency validation, not cryptographic authentication of that JSON.
Movement writes only `recovered_positions`, never character profiles or
mock-world character rows. A missing position uses the original17,13 spawn;
an invalid saved scene/cell is rejected, never silently reset.

## Initial Integration Verification

- Release build succeeds; pre-existing getenv deprecation warnings remain.
- 24 selected core CTest suites pass, including codec/service/config tests.
- Native movement tests qualify builder residue, adjacent-step preconditions
  and82 queue/ACK steps using the original consumer.
- Loopback tests cover fragmentation, native batched flush, merged frames,
  ring wrap, real-grid obstacle rejection, invalid length/checksum/sequence,
  duplicate requests, duplicate sessions, reconnect reset and world-tail
  coalescing. Database snapshots must remain unchanged after movement.
- Combined regression:135 tests in106.228s,132 passed and3 OS-dependent symlink
  tests skipped; zero failures. This includes the five movement loopback tests
  and three original-code movement tests alongside login/character/world/map
  regressions. The24 CTest suites exclude the separate artifact-vault,
  runtime-evidence, gate-review, counter-resolution and runtime-environment suites.
- `god2-server --config config/recovered-movement.json --run-for 2` opened
  loopback2592 and an ephemeral character listener, loaded Lua and navigation,
  and stopped cleanly with exit0. No client was connected in this smoke run.
- A bounded independent review identified the world-tail coalescing bug;
  the fix and full/partial-frame regressions were integrated. The review agent
  and earlier codec agent were closed after completing their tasks.

Test qualification is not a live-game completion percentage. Overall playable
progress remains the previous rough10% estimate until real-client world
acceptance is established. No original client UI was launched in this increment.
The later persistence regression results are recorded in the linked follow-up.
