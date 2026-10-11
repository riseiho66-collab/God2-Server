# Legacy scalar runtime retirement

Date: 2026-09-19. The owner's current directive abandons previously supplied
XJZ/Classic data as reference evidence. No legacy corpus was opened for this
audit. Evidence reviewed here is the active Session implementation,
RecoveredWorldStateCandidate, RecoveredCharacterService, and current research
notes. Native-image findings below are those documented in those notes, not
new native executions performed by this change.

## Decision and provenance

The unconditional 144-byte send in Session::Impl::accept_world_tail was pure
historical scalar replay. Its 141 logical bytes contain opcodes 2B/2C/24/39/22.
The array has no selected-character, account, profile, repository or current
starting-rule input. Deferring it until a valid client initialization tail did
not make the values a reply or authoritative selected attributes.

[Current scalar consumer evidence](current-world-scalar-bootstrap-20260919.md)
documents native image SHA-256
`149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
It establishes the following bounded protocol facts:

| Record | Logical bytes | Current native consumer evidence |
| --- | ---: | --- |
| 2B | 21 | 69EB0 -> E6390/AA3F0; actor/subordinate scalar writes |
| 2C | 61 | 69EDE -> E6600; explicit WORD/DWORD write widths |
| 24 | 17 | 69F4D -> E71E0; actor writes and conditional subordinate reduction |
| 39 | 17 | 6A003 -> AA9E0; conditional subordinate writes |
| 22 | 25 | 69EF0 -> E6B40; byte/word/dword projection |

The same note explicitly leaves live acceptance, timing, semantic stat names,
selected-character values and causal request/reply mapping unproven. Native
parser/consumer execution proves that supplied bytes can be consumed; it does
not independently establish those numeric values as original starting state.
The original-client source for these character values remains UNKNOWN. No
replacement zeros, guessed stats, growth rules or fabricated reply is supplied.

## Runtime change

Removed only the scalar fixture include, automatic enqueue/write, and obsolete
144-byte send log from Session.cpp. The validated tail still advances the
internal state, calls the configured world-ready handler, processes buffered
movement, and resumes reads. No runtime switch can re-enable this fixture send.
RecoveredWorldStateCandidate keeps its exact bytes and encoder for explicit
diagnostic callers, with its non-runtime status stated in the header.

[Current initialization evidence](current-world-initialization-sequence-20260919.md)
proves the C2S 1F00/2300/1C sequence and finds no additional S2C receive waiter
in the inspected post-68160 path before 1C. That structure remains intact.
[Current existing-character selection](current-existing-character-selection-20260919.md)
proves the 1A -> 02/result-WORD-zero path; it remains intact as well.
Authentication, creation, ownership checks, selection and 2A delivery are not
disabled by this change. Tail validation does not itself set InWorld.

## Other audited boundaries

RecoveredCharacterService copies the client's 40-byte profile, validates it,
persists it, and rechecks ownership/token on selection. It does not inject the
scalar array. Its world_entry_candidate delegates to RecoveredWorldEntry with
the owned profile. There is no evidence here to replace that service path.

The existing 128-byte character bootstrap has a native-proven opaque copy
contract but a zero-filled lab payload, not original character attributes.
The 2A candidate has mixed provenance: native layout, two owned-profile variant
projections and substantial current resource/scene execution are documented in
[world-entry evidence](recovered-world-entry-20260919.md) and
[scene integration](current-world-scene-integration-20260919.md). Remaining
retained body values are not thereby proven original starting policy or owned
appearance. Those candidates are not the pure scalar replay removed here;
no full-original or live-world claim is made for them.

The unauthenticated diagnostic character-list fallback in Session remains a
separate legacy-named candidate path; the authenticated path calls the owned
list handler. Broader candidate/content retirement belongs to the coordinating
task. No files, assets, database or other agent's growth/formula work was changed.

## Regression coverage

The existing session_state suite now drives the real recovered Session over
loopback with synthetic handlers and a synthetic peer. It checks existing and
post-create selection, exact handshake/bootstrap/selection/2A bytes, partial
tail silence, complete tail silence, movement after the tail, tail coalesced
with movement, duplicate-tail rejection, wrong-identity rejection, and checksum
rejection. There must be no unexpected bytes before, after, or on rejection of
the tail. Test identities and coordinates are explicit synthetic inputs.

A separate diagnostic assertion pins all 144 encoder bytes captured from the
pre-change C++ diagnostic executable and verifies decoding/checksum against the
retained logical array. Keeping that codec stable does not restore its evidence
value or authorize runtime replay. No legacy JSON fixture or corpus is read by
the new tests. This is server/codec regression coverage, not live original-client
E2E acceptance.

Earlier research notes describing an automatic scalar send are superseded by
this retirement decision. Python integration tests that still require a
144-byte bootstrap or WORLD_STATE_CANDIDATE_SENT need coordinating-task updates;
their expectations are no longer the runtime contract. Those files are outside
this task's write scope and were not edited.

Validation completed:

```text
cmake --build build-net-check --config Debug --target god2-tests recovered-world-entry --parallel 2
ctest --test-dir build-net-check -C Debug --output-on-failure -R '^(session_state|protocol_replay|post_create_select|character_create|recovered_account_login|recovered_world_entry|network)$'
```

Build succeeded. All 7 targeted suites passed (4.99 seconds total); the new
session_state checks passed in 3.26 seconds. The build reported only the
existing Session.cpp getenv deprecation warnings. The native scalar/corpus
Python tests were not run because they read abandoned legacy provenance.
No new original-client process, native-image execution or full world E2E test
was performed.

## Coordinator integration

The coordinator updated Application's obsolete scalar-send warning and the
world-entry/movement Python suites to require silence after the accepted tail.
They no longer load the retired scalar JSON or expect 144 bytes before movement.
The first run failed against the old Release binary; a fresh complete Release
build resolved that mismatch. Final loopback reruns passed: world entry 3/3
(8.282s), movement 8/8 (23.035s). Final core CTest passed 32/32 (9.11s), with the
five pre-existing artifact/gate/environment suites explicitly excluded.
