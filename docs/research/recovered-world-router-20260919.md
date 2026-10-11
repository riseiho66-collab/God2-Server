# Formal Recovered World Record Routing, 2026-09-19

Follow-up: [basic attack transport](recovered-battle-transport-20260919.md)
adds C2S35/action1 to this typed path with an InBattle game-executor gate.
Application still has no battle policy. The boundary below describes the
earlier world-only delivery; skill actions remain outside the runtime grammar.

## Implemented Boundary

The production Session now parses ordered world records after zero-seed envelope
validation instead of assuming every record is movement. The C2S grammar is
independently grounded in current native producers: 2E (7), exact 30 00 (2),
25 (5), 85 (7), and 86 (5), counting logical opcode bytes. It never uses the
client's different S2C receive lengths. Battle35 remains outside this world path.

`Session::RecoveredCharacterHandlers::world_records` is an optional serial
game-executor callback, mutually exclusive with the existing movement callback.
It receives an ordered span backed by owning variants after independent login,
selected account/character binding and world-tail validation. Nullopt rejects;
an empty result accepts without inventing a response. Returned bytes must be
complete checksum-valid recovered frames before entering the bounded S2C queue.
Logical response validity, authorization and transactional mutations belong to
the game policy, not to the envelope parser. Callback exceptions fail closed.

TCP fragmentation/coalescing, including the first frame following the exact
world-tail boundary, remain supported. All complete available frames are checked
before invoking a game handler. Incomplete following frames remain buffered.
This is not a claim that all TCP reads form a native gameplay transaction.

Application still installs only its existing movement service. The legacy
fallback checks the whole available record batch BEFORE any movement callback,
rejecting 25/85/86 rather than acknowledging unknown gameplay. No new quest/item
authority, reward, consumption, persistence mutation or placeholder Lua policy
was introduced. Existing movement acknowledgements and persistence remain wired.
The generic fixture dispatcher and 1000-series opcodes are not used for this path.

## Native Evidence

The current image hash remains
`149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
`current_quest_action` proves 85's two words, context and unwritten stack byte.
`current_quest_close` now completes C8350 in a declared empty-UI environment and
proves 86's source low word plus saved this-pointer high word. Neither residue
is padding or an established gameplay identifier.

Native sequences include 85 alone, 86 alone, 86 then85, and mode4 85 then85.
Successful ordinary action sets AFF04, suppressing86. Close's follow-up85 tail
is a return-address byte in this fixture, not a protocol constant. Capacity can
reach the real flush boundary between requests. No invented pair/dedup rule is
added to the server. Populated cleanup, locks, actual flush/send and original
server authorization remain unqualified. No live-client acceptance is claimed.

## Verification

Main built the full Release solution. Native close tests passed 20/20 in 1.783s;
the updated source-pinned protocol audit passed 13/13 in 9.760s. Permanent
native-to-C++ tests passed 2/2 in 0.271s, including all 256 possible native85
stack tails and the four original close/action sequences.

Final selected CTest passed 42/42 in 102.12 seconds after all 86 changes. Five
older artifact/gate/environment suites were excluded; ordinary fixture suites
are regression evidence only. The expanded bounded socket suite took 31.26s
and has an explicit 90-second CTest deadline.

The Session socket suite covers every split of a mixed frame, tail/frame and
multi-frame coalescing, exact order/raw fields, authentication/world binding,
missing/ambiguous handlers, malformed suffix/checksum, wrong-state input,
tick-only/no-response continuation, rejection/exception, invalid/truncated or
oversized responses, concatenated valid responses, and close during a callback.
Handlers in this suite are explicitly synthetic policies, not original quests.

The actual server executable's loopback movement/persistence suite passed 9/9
in 26.098s after 86 integration. It includes whole-batch rejection for uninstalled
25/85/86 policies before any position commit, account/profile invariance,
duplicate bindings, ring wrap, obstacles, restart recovery and database errors.
Temporary test databases only; no player database was changed by these checks.

## Open Main Goal

All original packet/gameplay coverage is still incomplete. The audit now has
three TRANSPORT_ROUTE entries distinct from configured RUNTIME_ROUTE and live
CLIENT_ACCEPTED. Next work must recover and install actual dialogue/item rules
and original state producers, rather than count a callback as restored gameplay.
True original-client world and battle acceptance remain required.
