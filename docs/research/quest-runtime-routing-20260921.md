# Quest runtime routing boundary

Current worktree audit: Mission_data display coverage exists for418 definitions
and2014 description steps, but that is offline native-text coverage, not quest
gameplay. RecoveredWorldRecords already parses native C2S85 and86. The world
service previously rejected both unconditionally. QuestRepository is still an
empty interface, Quest is a placeholder, and scripts/quests/test_quest.lua is
an example, not an authoritative current-client quest definition.

## Implemented

CUSTOM-0004 adds an optional typed Quest callback to RecoveredWorldService.
Exactly one parsed85 action or86 close is forwarded only for an authenticated
owned character in InWorld. Existing constructors default the callback off.
There is no Application handler activation and no fabricated response.
Mixed operations, multiple quest records, tick-combined quest records, incomplete
world entry, battle, disconnected sessions and missing identities reject before
calling policy. Fields remain opaque and unmodified; callback denial is retained.
The eventual service must authorize its server-owned conversation and perform
atomic domain/storage changes. Client request words are not assumed quest IDs;
close pointer residue is not treated as an identity or completion indicator.

## Verification

Server and recovered-world-service builds succeed. CTest recovered_world_service
and recovered_quest_sync pass. Tests exercise frame encode/parse through typed
dispatch, exact opaque fields, disabled routing, callback denial, session states,
identity absence and both orders of mixed records. A test initially reused a
Disconnected Session, whose terminal state cannot be reversed; it now creates
a fresh Session and explicitly checks disconnected refusal.

This is an integration boundary, not quest completion. Next required work:
server-owned dialogue/session binding, native7A response producer/consumer live
qualification, source-backed quest prerequisites/progression or separately
documented custom fallback, atomic persistence/reward deduplication, and actual
own-server client acceptance. No native formula or quest reward is inferred.

## Isolated outbound candidate integration

CUSTOM-0018 introduces default-off diagnostic_quest_dialogue. Configuration
requires recovered world/movement, non-mock loopback and diagnostic-accounts.db;
battle transition and world-resource projection are excluded. Application
passes the first standalone world tick through the existing world policy, then
queues a mode1/key3 candidate with diagnostic request0x1234/reply2/context0x9A.
These three values are test choices, not native quest or NPC identifiers.
Session's existing initialized-world record gate remains in front of this
callback. The send marker is per connection and removed on disconnect.

No quest action/close handler is activated; no acceptance, progression, reward
or persistent quest mutation is implied. The packet uses the compiled bounded
mode1 encoder and shared frame encoder. Server builds and four targeted tests
(config, world routing, quest sync, variable length) pass. No configuration is
enabled by default. This new outbound Application path has not yet been run
against the native client; next step is lab switch/observer integration and
real consumer qualification before allowing dialogue-driven actions.

## Own-server native consumer run

Lab --diagnostic-quest-dialogue now propagates the explicit config and arms
native C7F10 entry, C8234 header setup and the captured function return address.
It requires isolated own-server world observation and real text-table capture,
and waits for dialogue instead of stopping at the earlier position-restored
milestone. No client state or dialogue input is patched.

artifacts/runs/native-quest-dialogue-20260921-01 finishes
NATIVE_QUEST_DIALOGUE_CONSUMER_RETURNED/error null. The consumer receives exact
compiled mode1/key3 bytes; its signed widget field is61, header request is4660,
reply2, and its stack returns by8 bytes. Event order455/456/457 shows the real
consumer passed its early gate, reached header setup and returned. The source
table remains the real14600-entry table, not the offline synthetic empty text.

The server sends once. Positions, resources, battle checkpoint and settlement
rows remain unchanged versus the source backup. Four targeted suites pass.
No visual screenshot or user-input verification was performed; a normal
function return is not proof of visible text or accepted quest. Next required
work is native dialogue input and the actual85/86 exchange with a server-owned
conversation binding, then authoritative progression/persistence/rewards.

## Native dialogue confirmation queue qualification

Run `native-quest-confirm-20260921-01` adds opt-in `--probe-quest-confirm`
to the isolated dialogue run. After the native consumer returns, a bounded
owned RX thunk saves flags/general registers, calls original C8500 with its
real UI pointer, restores registers and stops. No page/choice/header/queue
state is fabricated. The thunk has a separate emulator preservation test;
that stubbed test is not evidence about game behavior.

The real consumer produced page index0/count1. The queue changed from empty
to exactly seven bytes `85 34 12 02 00 9A 18`; the first six match request1234,
reply2 and context9A from the diagnostic server dialogue. The final byte is
native stack residue, not a required constant. C8500 returned with unchanged
stack pointer. No86 was present in this queue snapshot. Result is
NATIVE_QUEST_CONFIRM_RETURNED, error null, world_accepted false.

This run stops before normal transport flush: it proves native request
production, not server receipt or quest acceptance. It does not exercise a
physical click. Resources, positions, battle checkpoints and settlements
are unchanged from the source backup. Next step is resume original caller,
capture actual transport/server parsing, then authorize the exact server-owned
conversation before implementing quest progression and rewards.

## Natural transport and current policy rejection

Run `native-quest-transport-20260921-01` enables `--observe-quest-transport`.
After the confirming call the debugger resumes the original caller, without
calling a flush function or constructing C2S bytes. Original send returns10
at sequence461. Captured wire and decoded frame have retained SHA256s;
the checksum-valid logical record is exactly `85341202009a18`, equal to
the earlier queue snapshot. A subsequent original world frame is observed.
Result NATIVE_QUEST_CONFIRM_TRANSPORT_OBSERVED, error null, is not acceptance.

Server log then records `Recovered world policy or response rejected` for
session2. This error occurs after record parsing at the world policy callback,
not at the frame checksum/parser. Current Application has no quest handler;
the quest route also requires InWorld while bootstrap may retain
CharacterSelected until movement. Do not remove either guard merely to pass.
The next implementation must bind a server-owned conversation to its account,
character and completed-world session, validate the exact permitted response
and consume it once; request/reply words are not automatically quest IDs.

The packet pipeline now identifies standalone C2S85 structurally and preserves
the opaque tail. It deliberately leaves state consistency unknown and
conversation authorization false. Tests cover captured wire/plain hashes,
checksum, queue-to-wire equality, ordering, opposite direction and incorrect
record lengths. Historical captured metadata is not rewritten by this change.

## Bound diagnostic response accepted

CUSTOM-0018 DiagnosticQuestConversation now binds connection/account/character
only from the completed-world callback. Opening and consuming are one-shot;
zero identities, absent binding, owner mismatch, unexpected request/reply/context,
duplicate open/bind and replayed consumption reject. Opaque stack residue is
not compared. State is confined to the game executor and removed on disconnect.
This is a test conversation, not a quest grant or a reusable gameplay engine.

Application explicitly gates standalone85 by the diagnostic config and
CharacterSelected/InWorld. The completed-world binding is mandatory even when
bootstrap retains CharacterSelected. Normal RecoveredWorldService remains
unchanged and InWorld-only for its optional quest callback; battle and mixed
batches cannot use the diagnostic path. No scripted game rule or reward is
introduced. Config remains default-off, loopback/isolated-database only.

`native-quest-bound-confirm-20260921-01` runs the actual original confirm and
natural transport. Server logs exactly one DIAGNOSTIC_QUEST_CONFIRM_ACCEPTED,
then a handled batch, without policy rejection. A subsequent native world
frame is observed. Resources, saved positions, battle checkpoints and
settlements remain unchanged. Standalone service tests cover invalid identities,
ownership/fields, pre-open consumption, replay, disconnect and varying stack
tail. No full quest progression/persistence/reward or physical UI acceptance.
Next requirement: connect NPC interaction to an identified quest and implement
authoritative progression with provenance, not treat this probe token as a quest.
