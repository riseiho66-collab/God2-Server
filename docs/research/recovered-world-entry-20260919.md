# Recovered World Entry Candidate

## Actual Change

`config/recovered-world-entry.json` opts into the existing dual-connection,
account-owned character path plus this sequence on G:

```text
successful 1A selection -> 02/result WORD zero -> S2C2A/40-byte candidate
  -> C2S logical 1F 00, 23 00, 1C <local-id/config>
  -> WORLD_INITIALIZER_TAIL_ACCEPTED, not InWorld
  -> deferred historical scalar candidate: 2B / 2C / 24 / 39 / 22
```

The existing capture runner has `--recovered-world-entry`, requiring its
dual-connection and zero-UI candidate prerequisites. No desktop action is added.
All older configurations default this option off and retain their exact flows.
C++ owns the framing/account/profile checks. Lua and the gameplay architecture
are unchanged. This branch does not instantiate the unrelated mock-map player.

## Evidence And Field Boundaries

The body is not fabricated. `legacy-world-entry-provenance-20260919.md` identifies
a retained 320-byte outer frame and independent saved decoded prefix containing
the complete 37-byte logical 2A. Source, stream, encoded frame and body hashes
are pinned in `tests/fixtures/recovered-world-entry.json`. The historical frame
checksum passes with its documented historical key/feedback. Those historical
crypto parameters are **not** used by the C++ encoder: the extracted logical body
is framed and encrypted using the already recovered zero-seed lab transform.
The new standalone 40-byte framing is not claimed to have been historically
captured as a standalone frame.

Current-client image SHA:
`149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
Parser `68160` consumes 36 bytes through waiter `15690`. Body offsets are decimal:

| Body | Current consumption | Historical value |
| --- | --- | --- |
| DWORD 0, low 14 bits | Local actor ID, `68629/68633` | 217 |
| DWORD 0, bit 31 | Output flag and world+A7F2F3C, `681FD..68204` | 0 |
| DWORD 0, other bits; DWORD 4 | Several packed resource/appearance flags and selectors | Preserved, not renamed as classes/stats |
| DWORDs 12/16/20 | Actor+4584/+4588/+458C; component resource consumers | Preserved |
| WORD 24, low 6 bits | Area selector, requires 1..16; actor+18 | 2 |
| WORD 24, high 10 bits | Scene selector; actor+14 and resource helper args | 15 |
| DWORD 28, low 2 bits | Actor+10 and world+22C flag | 2 |
| DWORD 28, bits 2..16 / 17..31 | Actor+8/+C position components | 17 / 13 |
| WORD 32 | Optional resource branch; zero takes normal component path | 0 |
| Bytes 34/35 | Actor+4695/+4698 | 0 / 0 |

The recovered numeric scene selectors/components are not a validated map-file
identity, coordinate unit/scale, walkable spawn or original starting-location
policy. In particular, the legacy documentation's map 19 / position 28,34 is
not substituted for the actual values consumed from this record.

The 14-bit local ID is rebound to the authenticated persisted character's
ID, with an explicit 1..16383 bound. Larger IDs fail before selection success is
sent, never silently alias. This bounded lab mapping is not a permanent world
entity allocation scheme. The service rechecks account ownership and valid
stored profile before returning the candidate. The follow-up projection below
also binds two component variants; all remaining body bits are retained.

**Appearance limitation:** `current-world-appearance-20260919.md` qualifies two
3-bit variant fields: body13 bits5..7 from owned profile32, and body15 bits5..7
from owned profile36. The service now projects those fields after ownership and
profile validation. Other appearance/resource fields remain historical, not a
complete projection of the newly created profile. They are never persisted as
that character's gameplay attributes. Startup logs label this limitation.
No HP, MP, equipment, jobs, NPCs or world DB state is invented by this change.

**Map qualification:** the UI catalog has no area2/scene15 row, but subsequent
`current-scene-resolution-20260919.md` proves that kind2 selects the real indoor
grocery asset through the area-base CAN. `current-indoor-resources-20260919.md`
extends that evidence through the complete original 48300 loader with real HMD,
ROM, model and navigation data in an explicit offline device environment.
No map/position bits were replaced with a guessed spawn. Live initialization,
camera/display and rendered-world acceptance remain unqualified.

**Role-resource follow-up:** `current-world-role-resources-20260919.md` now
executes actual world cache/path wrappers, all six 61270 resource outputs and
the normal 68315..68558 appearance slice with native setters and real ROMs.
The retained body's Drv selector 27 is tested separately from unmounted preview
inputs. All 49 projected variant pairs pass C++ encoding, original decoding
and this real-resource chain. This closes that bounded resource dependency;
it does not make the historical mount owned state, complete the selected
profile projection, or establish whole-world rendering.

## Initialization Tail

`current-world-initialization-sequence-20260919.md` recovers the original
post-2A tail: no additional inbound waiter was found before the three C2S requests.
Original `13370/124D0/10960` execution demonstrates that all nine logical bytes
are emitted as one uncompressed 12-byte frame on an empty queue. The C++ bounded
validator also accepts whole-record splits (5+5+8, 7+8, 5+10) and TCP fragments.
It verifies frame length, checksum, exact order/opcodes, zero constants, matching
local ID and the known 0/1 configuration flag. It retains at most 18 bytes and
rejects repeated tails, unknown trailing data, overflow, wrong account selection,
bad identity and bad state. It does not accept a checksum as sufficient proof.

`WORLD_INITIALIZER_TAIL_ACCEPTED` records a valid peer-provided protocol sequence;
a synthetic peer can produce it, so SessionState remains CharacterSelected.
No live rendered world is inferred. The follow-up in
`current-world-scalar-bootstrap-20260919.md` sends a qualified historical scalar
bootstrap only after this tail. It is not a proven request/reply association or
the selected character's true attributes; nothing is persisted from it. The
following gameplay contracts remain to be recovered; current unknown post-tail
data fails closed instead of invoking fixture handlers.

## Verification

- Release build completed and 21 core CTest suites passed.
- The combined Python run passed 92 tests: prior account/profile/dual-connection
  regressions, current decoder/handler/builder slices, runner opt-ins and the new
  world-entry/tail integration. The two bounded agents were closed after review.
- Original current decoder/checksum accepts the C++ 2A frame. The bounded current
  actor projection yields the expected local ID, area/scene selectors and position
  components for IDs 1,217,16383. Area 0,17,63 takes the original rejection branch.
  Rendering/resource helper calls are stubbed; their argument projections and
  guard memory are checked. This is not whole-world initialization acceptance.
- Original tail/queue/encoder execution generates the C2S transport bytes used
  in real loopback C++ server tests, stopping before any socket API.
- New integration tests pass creation/post-create selection, process restart,
  saved-character selection, independent L shutdown, partial checksums and
  grouped/fragmented tail frames; wrong ID/order/constants/checksum are rejected.
  Existing account/profile data stays unchanged by world candidates/tails.
- The new config starts both local listeners, loads Lua, and shuts down cleanly
  in a one-second smoke check without adding accounts or characters.

Remaining acceptance work: bind current profile appearance and actual map/assets,
validate the real original-client initialization and rendered scene, then implement
the requested world-state replies, movement and subsequent gameplay/persistence.
Neither full world entry nor playable-server completion is claimed here.
