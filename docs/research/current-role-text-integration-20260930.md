# Current secondary role text: C2S20 / S2C23

## Scope and result

The observed unsupported `20` record in
`artifacts/releases/town-chat-welcome-20260924/server.log:8841` is a native
secondary role text edit. It is independent of the primary name and common
chat. This turn qualifies its wire contract and implements owned storage,
response, and relog restoration in the candidate. The original human label
(title, nickname, or other term) is not established by this evidence.

Candidate tested by the real TCP peer:
`1c2a6d090c6759eca2786adba690ab7da60e6a821ff87c73005e7df01ad72fc5`.
This lane itself did not restart production. The root later installed the tested
candidate in `artifacts/releases/packet-links-20260930-01`; its verification
confirms schema39, preserved existing rows/schema/history and managed PID32268.
The independent hidden-client run described below also accepted ordinary ASCII
UI input, native send, and cold relog receive. Its read-only native buffer
checks are separate evidence from TCP; rendered pixels were not tested.

## Qualified native contract

Current supplied `../God2/God2.exe` SHA256:
`9be38ef858bc9c63b6f296cae4a8e601ddcfaf614700e725c4bec44065b53336`.
The mapped source image is
`artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin`,
SHA256 `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
The relevant native spans were checked against the current PE; old whole-file
pins for unrelated codecs were not silently renewed.

| Direction | Native path | Established behavior |
| --- | --- | --- |
| C2S20 | `496890` through `4132E0` | 17 logical bytes: opcode and 16-byte field. Copy includes the first NUL; remaining local stack bytes are opaque. |
| Input limit | `4B2AE0` case2 and `4E7B20` | `4165D0(...,15)` limits the encoded prefix to 15 bytes. Empty is permitted. |
| S2C23 length | `401324[23] -> 40124C` | Native leaf returns 17, independently of C2S20. |
| S2C23 state | `46B5D4[23] -> 469F02` | Copy logical+1 to `World+15396903`, then call `4B1A00` and `509E70`. |
| Role UI | `481C20 -> 4E7C80`, `4B1A00 -> 4E7C00` | UI+86888 points to local root+90. Secondary string is that pointer+37, displayed as role widget7. |
| World label | `509E70` | Secondary renderer field+81, prefixed by `max(0,14-byte_length)/2` spaces with integer division. |

All addresses and offsets in this report are hexadecimal except explicitly
stated byte counts. Receiver emulation executes only the bounded original
copy slice and stops before the UI/renderer callees. It does not claim to have
rendered the text.

The existing remote actor contract maps S2C6F logical+45 to remote actor+20
and the same secondary renderer field+81. This turn does not implement dynamic
peer updates, and does not claim the whole social system is connected.

## Candidate integration

- `RecoveredRoleText` retains raw producer bytes when decoding/re-encoding the
  request. Its separate canonicalizer removes opaque bytes after the first NUL.
  Only canonical 16-byte fields are accepted by the S2C23 encoder.
- Migration39, `owned_secondary_role_text`, adds `character_role_text` and
  preserves the SQL of migrations1–38. It does not seed text or change names.
- `SqliteRoleTextRepository` stores canonical legacy bytes, UTF8, source
  codepage, revision, source hash, and `CUSTOM-0056`. Construction has no schema
  side effects. Owner validation, `BEGIN IMMEDIATE`, expected revision, and
  readback protect saves; identical values are idempotent.
- CP936/950 input must decode and re-encode exactly. Strict projection to a
  different session codepage returns no display value if conversion loses a
  character or exceeds 15 bytes. It never truncates or substitutes a glyph and
  never changes the saved value while projecting.
- Application accepts one edit plus optional ticks, after world admission,
  owned projection and location binding, with no battle or pending scene.
  It prepares S2C23 before storage and replies after successful commit. The
  owned initialization route restores the value after relog.

These durability, authority, and encoding policies are documented server design
`CUSTOM-0056`; the native producer/receiver does not establish original server
storage, moderation, or mutation rules.

## Verification

Evidence directory: `artifacts/research/role-text-20260930/`.

| Check | Result | Limit |
| --- | --- | --- |
| Native producer and receive copy | 51 cases, normal and Python `-O`, identical JSON | Complete producer/queue, bounded receiver copy; no graphical execution |
| Protocol C++20 | 1329 checks, normal and optimized | Codec, canonicalization, opaque tail, malformed bounds |
| Repository C++20 | 65 checks, normal and optimized, `/W4 /WX` | Migrations38→39, owner/CAS, both encodings, empty clear, rollback, read-only reopen, cascade |
| Independent repository review | 57 checks | CP936→950 byte expansion, unavailable/unknown pages, two connections, busy/CAS, readback-trigger rollback |
| Real candidate TCP | 3 tests, 20.887 seconds | Encrypted fragmentation, save/clear, dirty tail, idempotence, ticks/mixed denial, restart, both languages, owner isolation, unrelated saved-state preservation |
| Actual supplied client | ASCII UI send and cold process relog passed | Window-local input; read-only actor, secondary renderer, and widget7 text buffers, no pixel assertion |

TCP tests use a read-only source fixture backup in a temporary database and
verify the source file hash after cleanup. `tcp-result.json` records the exact
candidate. Native/UI code spans are in `normal.json` and `ui-code-pins.json`.

Python optimization check: all three newly added TCP modules (role text,
reserve move and D6) and their three shared helpers contain zero Python
`assert` statements and zero `__debug__` branches; the full compiled code is
identical with optimize0 and optimize1. The same candidate passed all 8 tests
under `python -O` in 23.859 seconds. See `tcp-optimized-result.json` and
`tcp-optimized-run.log`. This is repeat verification, not extra gameplay
coverage.

## Actual-client receipt

`artifacts/playtests/private-pet-reserve-20260930-03/run-result.json` has SHA256
`70319eb80148b148ab058255cea374c59e10acc0c7ef1ead9b2d201dccdae5cb`.
The receipt identifies the candidate above, `accepted=true`, source files
unchanged, desktop unchanged, and all owned processes closed.

The client used the ordinary HUD button at `(642,584)`, input mode2, ASCII
`WM_CHAR` input of the 15-byte `RoleNativeProof`, and role close control10 at
`(229,21)`. C2S20 resulted in canonical saved bytes
`526F6C654E617469766550726F6F6600`, UTF8 `RoleNativeProof`, CP950, revision1.
The original actor, local secondary renderer, and widget7 static text all
matched. A fresh client process then received S2C23 and restored all three,
with the saved row unchanged.

This qualifies the bounded ASCII edit/save/relogin route in the supplied
client on the own-server candidate. It does not certify CJK IME entry, pixels,
peer secondary-label synchronization, moderation, or a complete social feature.
No screenshot, foreground switch, process-memory write, or native function
injection was used; frozen IME and chat behavior were not changed.

## Native UI path supplied for independent client acceptance

1. Read the HUD widget index at `UI+232DB6`; HUD control5 invokes
   `4B1660 -> 4E79A0 -> 4E79E0`.
2. Read role panel index at `UI+232DDA`; input-enabled flag is20 at
   `UI+E2988+index*2A08`. Opening sets input mode2 at `UI+5BFA4` through
   `4B1A80(2)`. The text input is already active.
3. Control1B is the caret, not a required click target. Its rectangle can be
   invalid for the general button helper. Type through ordinary window input.
4. Role control10 closes and commits through `4E8910 -> 4E7B20 -> 496890`.
   Controls14–17 allocate attributes and are unrelated to this test.
5. Read `actor=uint32(UI+86888)`, secondary string at `actor+37`, and the
   widget7 string copy at fixed `596E54`. Let `local_root=actor-90`,
   `World=local_root-1539683C`, and
   `index=uint16(local_root+4544)`. The local rendered label string is at
   `World+39C+index*A7E0+81` (17-byte field).

Input itself updates some local fields optimistically. Server storage and a
cold relog restoring the actor, widget, and renderer fields provide stronger
evidence that the return packet was consumed. No process-memory write or native
function injection is necessary.

## Measured coverage and remaining gaps

`packet-gap-audit.json` records a fresh bounded census: 256 S2C byte-domain
queries, 254 table entries, 230 fixed lengths, 22 variable lengths and 4
unsupported byte values. **252 supported receive-length entries is not a
denominator for all C2S producers, connected gameplay, or current-client
acceptance.** The preexisting full route audit reports `REAUDIT_REQUIRED` with
7 changed source pins. Its hashes were not merely refreshed.

The current world parser has 25 case labels at this snapshot. Case labels and
variant types are discovery counts; they do not prove authority or completion.
There is no qualified exhaustive producer/handler/client-acceptance denominator
from which to report a whole-server integration percentage.

The three concrete initial audit findings were:

1. **Observed C2S20 disconnect:** now integrated by the work above, with native,
   repository, TCP, and bounded actual-client ASCII acceptance recorded
   independently.
2. **Teleport99/A9 parsed but no runtime authority:**
   `RecoveredWorldRecords.h:222` parses both selections;
   `Application.cpp:710` supplies `RecoveredWorldService::Teleport{}`.
   `RecoveredWorldService.cpp:62` returns rejection when the callback is absent.
   It must not be counted as connected teleport gameplay.
3. **DailyD8 intentions acknowledged without effects:**
   `Application.cpp:957` logs `OWNED_DAILY_NPC_INTENT_UNRESOLVED` with no teleport;
   line959 logs `OWNED_DAILY_CLAIM_INTENT_UNRESOLVED` with no reward and returns an
   empty response. Native display/selection bindings do not establish reward,
   ticket debit, or destination authority.

The bounded actionable integration was the observed C2S20 route. Teleport and
daily mutation remain targeted recovery tasks until their independent authority
is available; accepting their parser shapes is not success.
