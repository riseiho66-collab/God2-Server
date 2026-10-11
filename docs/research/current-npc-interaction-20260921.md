# Native NPC Interaction Path

Pinned mapped image SHA256:
`149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
Image base400000, addresses below are RVAs. No retired files, fabricated
native quest assignments or official-server traffic is used.

## Connected NPC Branch

World input at66D5C selects first NPC pool world+1539AED8 and calls CAD10.
The executed slice begins66D75 AFTER that unexecuted hit test, with explicit
slot and hit-result inputs. Original CD010 reads slot coordinates from
pool+80/+84+472*slot, rejecting unsigned slot>=256. The caller checks
abs(npc_x-role_x)<=3 AND abs(npc_y-role_y)<=3 against world+224/+228;
diagonal(3,3) passes. It then requires hit result37 (hex), not an inferred
quest opcode or NPC type name.

CCFE0 reads the identity DWORD at pool+70+472*slot; identityFFFF rejects.
CCD80 then performs original CCF80 identity lookup. With the explicitly
null per-entry pointer at+1EC it returns1; the nonnull local sequence branch
is not qualified here. Caller66E1B invokes96750 with the exact identity and
ECX=world+A7F2F6C. Tests execute this connected branch until96750, without
substituting any native callee. NPC records/role position/world owner are
synthetic. No spawn, rendering, actual click or live hit test is asserted.

## Original Request Producer

96750 rejects signed-negative target values BEFORE the OS tick call.
A separate continuous slice starts96763 AFTER that unexecuted call with an
explicit tick result. Unsigned(now-previous)>1000 is required, including
32-bit wrap. Blocked attempts do not enqueue or update the timestamp.

Allowed attempts run original C84A0, then132E0, ending at original ret4.
With no pending dialogue and optional UI pointer+CFF5C=null, the logical
request is five bytes:37 followed by the original32-bit target argument.
The low word is rewritten from DI; the high word remains the original
argument, NOT uninitialized padding. Stored UI selected identity+85AC0
is narrowed to16 bits; the outgoing high word still survives for wide
synthetic targets. Native actor identity domain is not established by these
width tests and must not be widened in server policy without evidence.

When global5B7BEC==1, C84A0 first invokes97DC0 with pending request/reply,
queues85, clears the flag, and then37 follows in the same queue. Thus
85+37 is a real original-producer ordering, not automatically malicious
mixed input. Existing standalone diagnostic85 handling is NOT broadened
here: future atomic batch authorization must validate both operations.

## Verification and Next Step

`ctest --test-dir build -C Release -R current_quest_variable_length --output-on-failure`

Native tests cover nine distance positions, last/invalid slot, sentinel
identity, mismatched hit result, negative target entry guards, clock boundary
and wrap, outgoing target widths, stored narrowing and pending85+37 ordering.
The native image stays read/execute;20,000-instruction bounded execution
has checked stop points and stack ABI. No native game-function stubs.

This identifies an NPC-pool request path, not the complete server meaning
or every NPC service. Next: prove hit-test selection/identity from an actual
own-server spawned NPC, capture natural37 transport, then bind an owned,
in-range NPC conversation. Quest ID, quest prerequisites and rewards remain
separate native-evidence/custom-provenance work; no production activation.

## C++ Structural Integration

RecoveredNpcInteraction preserves the full32-bit raw target in a five-byte
record. RecoveredWorldRecords now emits that typed record and parses original
85+37 in order. It does not import an S2C length rule, narrow the high word,
validate NPC existence or grant interaction authority. Signed-negative and
sentinel values can be represented structurally; gameplay must reject targets
outside its proven identity domain, including cases the native producer will
not normally emit. No authorization callback or response is enabled.

Compiled recovered-world-records CLI round-trips the exact original-machine
output for four target widths and the pending85+37 combination. C++ tests
cover all truncated prefixes, invalid suffixes, exact single-record size,
zero/high/signed-bit targets, frame integrity and lossless reconstruction.
World policy tests confirm standalone37, ticks, repeated37, pending85+37,
and both movement orderings remain rejected without invoking callbacks.
The established diagnostic conversation remains standalone85-only.

Server, record and service targets build. CTest recovered_world_records,
recovered_world_service, recovered_quest_sync and current_quest_variable_length
pass. This is transport grammar integration, not a spawned NPC or completed
quest. Existing RecoveredNpcSpawn contains retained historical coordinates
and opaque fields; those are not activated as current-world placement evidence.

## Spawn-to-Interaction Identity and Position Chain

The oracle now executes original CC621..CC690 with a readonly synthetic
21-byte72 record directly into a staged NPC pool slot. It then runs the
original range/identity path66D75 without copying calculated expected fields
over the resulting slot. This closes the memory provenance between inbound
scalar writer and outbound target selection:

`72 low WORD at1 -> CC62F actor DWORD0 -> CCFE0 -> CCF80/CCD80 -> 96750 -> 37 target`

`72 packed DWORD17 -> CC681/CC68D actor+10/+14 -> CD010 -> 66DA4/66DBA distance gates`

Primary0,42,3793,3954,65534,65535 each run with secondary0 andABCD at
slot255. All write the primary only as identity; no secondary high word is
retained in that pool identity. PrimaryFFFF is rejected at the interaction
sentinel. Primary0 reaching the producer is only local instruction behavior,
not a declaration that NPC0 is a valid server actor. The producer output for
each admitted case is fed to the compiled C++ world grammar and round-trips.

Packed position(7,13) with low bits3 writes(7,13) and passes relative to
role(10,10); changing only y to14 blocks. Thus real native stored coordinates,
not separately supplied test coordinates, govern this boundary. Original
record bytes remain unchanged. Fourteen quest research test methods pass.

These are connected memory slices with explicit stops, not a full NPC spawn:
catalog/resource lookup, slot allocation, sprite construction, hit testing,
actual clock API, optional local sequence and graphics are still excluded.
No current-native placement is inferred from the diagnostic selectors or
coordinates. Next live work must qualify those dependencies before a normal
NPC interaction is claimed. No formal database or gameplay rule changed.

## Real Client Resource Readiness

Opt-in `--observe-npc-state` reads the native active resource bank and both
256-slot NPC pools at the first world frame. It never writes game state or
calls NPC constructors. The guard requires world-frame observation, caps
the table read, reads fixed-stride records and follows no pointers from them.
Run native-npc-resource-state-20260921-02 reads all319 catalog records,
retaining loaded records plus five explicitly inspected candidates.

Observed bank0,319 records:

| Absolute ordinal | Path basename | Loaded slot | Actions | Palette |
| --- | --- | --- | --- | --- |
| 20 | npc2721.ROM | 8 | 16 | 6 |
| 81 | npc2782.ROM | -1 | 16 | 6 |
| 87 | npc2788.ROM | -1 | 16 | 6 |
| 237 | npc2643.ROM | 9 | 8 | 6 |
| 318 | npc2401.ROM | 7 | 8 | 1 |

Both real NPC pools are empty. The scene-preload default and its two resources
are loaded; the older two isolated spawn-test resources are not. Slots7/8/9
are this run's actual allocation order, not wire identifiers or fixed values
to hard-code. This changes the next experiment: select a current-native
NPCAppearData record referencing the already-loaded scene resources, instead
of emitting a retained record that silently requires an unloaded sprite.
Do not equate ordinal20 with a template ID or infer world placement from it.

Both runs end NATIVE_SAVED_POSITION_RESTORED/error null, not full-world
acceptance. Saved resources, positions, battle checkpoints and settlements
are unchanged. These measurements establish readiness and empty pools, not
visible sprites or a player click. Live NPC generation remains the next gate.

## Build-Matched Template Selection

Current gamedata.csvZ (SHA25670a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731)
contains4043 NPCAppearData definitions, maximum selector6224. Source template
531 has appearance code21;3557 has2143. Both source rows have the flag column
that yields native4000. They are candidate test templates, not a recovered
placement of those NPCs in area2/scene15.

Read-only native-npc-template-state-20260921-02 observes the actual resource
catalog at owner+121EA+94*selector. Each94-byte record preserves the original
source name bytes; WORD+10(hex) is4000 and WORD+12(hex) is21/2143. Their
qualified catalog-group mapping leads to absolute NPC resource rows20/237,
which this run already loaded. No legacy definition or coordinate was used.

First capture -01 retained correct raw94-byte records, but its derived
flags/resource_byte fields used decimal offsets10/12 and are INVALID.
Those artifacts remain unchanged as negative evidence. The observer is fixed
to hex offsets10/12 and a16-bit appearance_code, then a fresh -02 capture
is checked against pinned current CSV bytes and raw native record bytes.
Do not use the invalid derived -01 fields for generation.

Next spawn experiment can use template531 and its existing resource21,
with any diagnostic placement/opaque packet fields explicitly labeled test
choices. No native location, quest association or service assignment is
established by matching an appearance. Both real NPC pools remain empty;
generation, full constructor/renderer and real interaction are still required.

## Own-Server Live NPC Creation

Default-off diagnostic_quest_npc requires the existing isolated quest-dialogue
configuration, inheriting loopback, diagnostic DB and world-only prerequisites.
CUSTOM-0018 DiagnosticQuestNpc sends template531/resource21 at diagnostic17,12.
Direction0/state1/selector-high3/remaining-zero fields are explicit unqualified
test inputs, not a captured original spawn or a claim of original placement.
No retained legacy spawn bytes/coordinates are used. Server prepends a framed
72 before its separate7A dialogue on the accepted first tick.

native-quest-npc-spawn-20260921-01 observes both pools empty before sending.
After real client receive/dispatch and subsequent dialogue return, first pool
slot0 contains identity531, x17,y12. The second pool remains empty. Loaded
resources and appearance rows are unchanged; no extra resource-slot injection,
client actor memory writes or fake constructor returns were used. Result is
NATIVE_QUEST_DIALOGUE_CONSUMER_RETURNED/error null, world_accepted false.

This is real server-to-client NPC object creation, not just a decoded record.
No screenshot or physical selection was taken; renderer visibility/hit-test
and resulting37 exchange remain unverified. The dialogue is still sent by
the diagnostic tick, NOT in response to clicking this NPC. Database resources,
positions, checkpoints and settlements remain unchanged. Regression covers
empty-to-one-object transition, exact identity/position, immutable resources,
one send and no policy rejection. Config tests enforce default-off and DB gates.

## Live Original37 Request from Observed NPC

`--probe-npc-request` uses the existing dialogue probe/transport harness, but
records action NPC_REQUEST_96750_SELECTION_BYPASSED. It requires the exact
observed spawned actor531 at17,12 before invoking the original96750 with that
identity. The bounded owned thunk preserves flags/general registers and stack,
passes one target argument and resumes the original caller after return.
No outgoing record or clock state is written. It bypasses hit testing and
distance selection, so it is NOT proof of normal mouse interaction.

native-npc-request-20260921-01 queues exactly3713020000 from empty state,
returns with the same stack pointer, then original transport sends8 bytes.
Decoded/checksummed logical bytes match the native queue and compiled C++
grammar. Server closes with policy/response rejection after parsing; no
diagnostic85 confirmation is accepted. This proves NPC531 target preservation
through real transport, not authority or a quest response. The earlier
dialogue was still automatic test setup, not a result of this37 request.

Packet identification now recognizes standalone C2S37 structurally, retains
the full target and leaves state/authorization unverified. Captured old
metadata remains unchanged; regression decodes the retained raw evidence.
Next: server-owned NPC visibility/map/range validation and a37-triggered
conversation response, instead of tick-triggered dialogue. Then qualify
native hit testing/visible selection and actual quest state transitions.

## Request-Triggered Dialogue Accepted

The diagnostic NPC option now sends72 ONLY on its first tick. Ordinary
diagnostic dialogue without NPC preserves its prior behavior. The completed
world binding marks the spawned NPC once. Standalone37 loads the owned
character's saved position and requires area2/scene15, raw target531 and
x14..20,y9..15 around17,12. This custom server policy mirrors the recovered
client per-axis3 range; it is not a recovered official server rule. Response
bytes are prepared before one-shot conversation opening. Battle, mixed input,
missing saved position, wrong identity and replay remain rejected.

The harness now invokes original96750 from a world frame AFTER observing
the actual spawned NPC, before any dialogue exists. It does not modify
position or hit testing; selection is still bypassed. Result fields reuse
the quest_confirm probe harness with explicit NPC action metadata.

native-npc-dialogue-response-20260921-01:
original37 send sequence340 ->7A entry352 -> normal return354.
Server records one DIAGNOSTIC_NPC_REQUEST_ACCEPTED and no automatic
DIAGNOSTIC_QUEST_DIALOGUE_SENT or policy rejection. Thus the dialogue is a
response to the real request, not a tick-driven substitute. Source and output
position/resource/checkpoint/settlement rows remain identical.

Unit checks cover pre-spawn, duplicate spawn, wrong owner/character/target,
high-word aliases, area/scene mismatch, four out-of-range edges, four valid
corners, duplicate opening and post-consumption replay. This run ends after
dialogue consumption;85 confirmation after this newly triggered dialogue,
NPC hit-test/presentation, quests and rewards remain unqualified. The proven
native85+37 compound ordering is still not generally authorized.

## Single-Connection Conversation Round Trip

Opt-in --complete-npc-conversation continues after the request-triggered7A
return. The harness archives the NPC request probe/return/transport separately,
then calls original C8500 and resumes normal execution. It never constructs
or enqueues the85 bytes itself. Existing request-only experiments retain their
stop behavior. The native calls still bypass physical input/hit testing.

Run native-npc-conversation-complete-20260921-01 completes:
spawn531 -> original37 -> server target/position acceptance ->7A entry/header/
return -> original85 -> server one-shot confirmation acceptance -> world frame.
Both sends use the same socket; retained wire/plain hashes, queue equality,
ordered sequences and stack pointers are checked.37 logical3713020000 and
85 prefix85341202009A match the bound target/conversation. Final85 byte remains
uninterpreted stack residue. Server logs exactly one acceptance for each stage,
no automatic dialogue-send marker, and no policy rejection.

Resources, positions, battle checkpoints and settlements remain unchanged.
This closes protocol-level conversation with an actual own-server/current-client
exchange, not quests: no journal change, acceptance criterion, objective,
reward or persistent quest state has been implemented. Next gameplay work
must bind a documented quest and its persistence transaction; normal visual
selection and repeat-conversation lifecycle also remain separate acceptance gates.

## Diagnostic Journal Projection

Run native-npc-journal-projection-20260921-01 extends the same-connection
conversation with DB/subtype4, slot0, packedValue1 after accepted85. Encoding
precedes conversation consumption. CUSTOM-0018 owns this test reference; it
does not identify an authoritative accepted quest or a native NPC/quest link.

Original C9670 entry sequence370 receives arguments0/1. All15 journal DWORDs
are initially zero. Return371 reaches the original caller at entrySP+12 and
the journal contains1 followed by14zeros. Confirmation send358 precedes both;
world frame373 follows. Server logs one NPC request and one confirmation
acceptance, with no policy rejection. Saved resources, position, battle
checkpoint and settlement rows match the source diagnostic database.

The observer waits for the original consumer return instead of ending at send
completion. The saved-evidence regression checks the exact60-byte before/after
state, ABI, same socket and event order. This proves receipt and memory update,
not visible journal rendering, objective completion, rewards or persistence.
world_accepted remains false; no production configuration enables this probe.

## Full Journal Restore Encoding

RecoveredQuestSync::encodeJournalLogical now accepts exactly15 packed values
and the build-matched description counts. It emits all15 subtype4 records in
slot order, including zeros, so a restore cannot leave stale later slots.
Nonzero references must resolve through the recovered description bounds;
one invalid reference rejects the entire batch before any bytes are returned.
Raw single-record encoding remains available for evidence work. Zero remains
an empty slot, while packed1 and packed0x10001 are retained distinctly even
though the native resolver selects the same description.

This is a transport prerequisite, not a persistent quest implementation:
QuestRepository is still a reserved interface. Authoritative acceptance,
objectives, reward transactions, catalog provenance in saved records and
fresh-session replay must be implemented and verified before production use.
The new offline native regression overwrites all15 slots and then clears all15;
it does not claim socket delivery or visible journal acceptance.

## Isolated Journal Persistence

Migration13 adds diagnostic_quest_journal without altering existing migrations.
SqliteRecoveredCharacterRepository stores15 little-endian DWORDs, revision,
catalog source SHA256 and CUSTOM-0018 provenance. Owned lookup distinguishes
missing projection from a stored empty projection. Commit validates description
references, compares the entire expected snapshot in a transaction, forbids
silent catalog replacement, increments revision and verifies readback.

Temporary-database tests cover wrong-owner read/write, stale initial snapshot,
invalid reference, changed source, injected UPDATE failure rollback, successful
revision advance, disk reopen and clearing. Database, config, recovered character
repository, recovered position repository and quest-sync CTest suites pass.
Build of god2-tests and god2-server succeeds.

No Application path calls this storage yet. This is not a quest-state schema or
reward ledger; Lua gameplay and authoritative transitions remain separate work.
Before projecting a loaded row, the caller must verify its source against the
actual loaded catalog and call the checked full-journal encoder. A stored hash
is provenance, not automatic proof of catalog contents or native quest authority.

## Native Description Catalog Import

Migration14 and tools.strike_lab.import_native_quests preserve the pinned
Mission_data display rows in native_quest_descriptions with the existing
native_data_sources provenance contract. The importer verifies compressed and
decoded source hashes, contiguous one-based mission order, ordered descriptions,
counts and each original row hash. The418 mission definitions yield2014
description rows. Each stores source line, raw row and display indexes; these
are not parsed completion conditions, NPC links or rewards.

Import into configured god2.db inserted2014 rows after server migration, with
backup artifacts/db-backups/native-quests-0f8e50122d774d14bf12c897725aa438.sqlite.
No gameplay writes or rule activation occurred. Three importer tests pass for
full import/idempotence, conflict refusal and injected transaction rollback;
database/repository and existing skill/map importer suites also pass.
The server still needs a catalog reader and explicit journal runtime binding;
this import alone does not provide quest gameplay or fresh-session acceptance.

## C++ Description Counts Reader

SqliteRecoveredCharacterRepository::load_quest_description_counts reads source
identity and all ordered display rows in one SQL snapshot. It requires the
pinned source/decoded/image hashes and native loader/consumer provenance, all418
contiguous missions, consistent per-mission counts and2014 total descriptions.
This checks the imported metadata structure, not a new hash of the original
client file; the pinned importer remains the source-byte verifier.

The read-only native-quest-catalog-reader executable verifies configured god2.db
returns418 counts totaling2014. The Python import suite compares every C++ count
against the current source and rejects changed source identity or a missing
last mission without output. All four importer methods and the database and
recovered-character repository suites pass. No runtime journal replay yet.

## Live Durable Confirmation

The isolated diagnostic NPC85 route now commits its journal before consuming
the one-shot confirmation. Failure leaves in-memory confirmation retryable;
wrong-owner/duplicate requests never enter the commit callback. Tests inject a
real SQLite UPDATE failure, retry and verify only one committed revision.

native-npc-journal-persist-20260921-01 failed before protocol execution because
the direct runner lacked the package import path. Fixed runner bootstrap;
run02 reaches NATIVE_NPC_CONVERSATION_CONFIRM_TRANSPORT_OBSERVED without error.
Its reopened database contains character1, revision1, CUSTOM-0018, pinned
Mission_data source hash and15 DWORDs [1,0,...,0], exactly matching the native
C9670 return snapshot. One confirmation acceptance and a subsequent world
frame are observed. Catalog2014 rows are imported into the isolated DB before
listening. Saved-evidence, repository and quest-sync suites pass.

This closes same-run confirmation persistence and native receipt only. New
connection replay, physical UI, actual quest progress and rewards remain open.

## Fresh-Connection Journal Replay

native-journal-relogin-20260921-01 uses a copy of persist-run02 database and
a new native client/server connection. The accepted diagnostic NPC tick appends
the checked195-byte full journal after72, framed together. Saved source identity
must match the pinned imported catalog; invalid references abort instead of
silently clearing the journal. Loading does not update the saved revision.

The observer detects a saved journal and watches all15 C9670 calls in order,
checks each slot/value and return ABI, then waits for a subsequent world frame.
It does not issue an NPC or confirmation probe in this branch. Result is
NATIVE_SAVED_JOURNAL_RESTORED with no error: slot0=1 and slots1..14=0.
The run database journal, resources, position, checkpoint and settlement rows
match its source. There is one restore log and no confirmation acceptance.
Four targeted suites pass, including saved-run replay checks.

This closes diagnostic fresh-session native-memory journal restoration, not
physical journal UI acceptance or native quest completion/reward semantics.
world_accepted remains false and diagnostic-only configuration remains intact.

## Native Dialogue Cancellation

The isolated standalone86 route now cancels only the bound owner's open,
unconsumed conversation. Opaque payload words, including the native client
pointer high word, are not gameplay authorization. Cancellation consumes this
diagnostic conversation without journal writes or rewards; duplicate/unopened/
wrong-owner cancel and confirmation after cancellation are rejected.

native-npc-cancel-20260921-01 uses original C8350 after the existing37 ->7A
exchange. The5-byte logical86 reaches natural transport; server logs exactly
one cancellation then the native world loop returns. Journal table stays empty.
Regression checks retained wire/plain hashes, queue equality, pointer residue,
ABI and ordered transport/frame observations. Native-call probing is explicitly
not physical UI input. Reopening conversations and full gameplay remain open.

## ACTMIS Requirement Display Import

Migration15 and import_native_quest_requirements preserve169 pinned ActMis.csvZ
records in native_quest_requirement_display. Serial is the native lookup key,
not a Mission_data join. Each row retains the source line/hash/raw bytes and
four ordered little-endian u16 item/u8 quantity pairs, including zero pairs.
No compaction, mission association, inventory deduction or reward is inferred.

The original x86 parser/category20 consumer suite passes all9 methods, including
all169 rows and the non-compaction/narrowing behavior. Import regression checks
all pair bytes, idempotence, conflict refusal and rollback of both records and
source metadata on injected failure. Existing database/repository suites pass.

Configured god2.db imported169 rows with DISPLAY_ONLY authority after backup
artifacts/db-backups/native-quests-911b7dd6288644f8b253c0a2860a67cf.sqlite.
Existing2014 mission description rows were unchanged. The serial-to-quest
relationship and server completion/award rules remain unknown, not implemented.

## Cancellation Reopen Policy

CUSTOM-0018 now permits a new owned/in-range NPC37 after cancellation. The
prospective request word is encoded before opening; successful reopen increments
it from0x1234 and resets only the cancelled conversation's consumption state.
An old85 cannot confirm the new generation.0xffff exhaustion rejects further
reopen rather than reusing words. Successfully confirmed conversations remain
terminal pending a real quest lifecycle policy.

Unit tests exercise every request word through0xffff, range refusal without
advancing the word, wrong owner, stale confirmation and successful new-word
confirmation. Three targeted suites pass and server builds. Existing captured
single-conversation regressions still pass; these do NOT certify a second live
conversation under this new policy. That native-client run remains open.
Because86 contains no proven generation identity, cancellation uses the bound
ordered session and never authorizes rewards or journal writes.

## Same-Connection Reopen Acceptance

native-npc-reopen-20260921-01 closes the prior native-call repeat-exchange gap:
37 ->7A(request1234) ->86 ->37 ->7A(request1235) ->85 ->journal return ->world
frame, all four C2S sends on the same socket. The observer archives the first
conversation, waits1.1s before the next original96750 call for its native throttle,
then invokes originalC8500 for confirmation. It does not patch dialogue or
throttle state. Final85 prefix is85351202009a, proving the new header was used.

Server accepts two NPC requests, one cancellation and one confirmation without
policy rejection. The journal has one revision1 row matching the native15-DWORD
snapshot. Saved-evidence tests verify packet hashes, exact payloads, same socket,
ordered events, both request words and final persistence. Three targeted suites
pass. Physical input/UI, official server policy and full quest gameplay remain
unqualified; world_accepted is still false.

## Fresh Town Live NPC Render Objects (2026-09-23)

`native-fresh-town-npc-hit-handle-20260923-01` used a fresh character and the
isolated server. At the original client's native world frame, its first town
NPC pool contained identities 1606 and 1607 at (110,69) and (112,70).
Read-only observation found projected coordinates (480,440) and (600,420).
The actor sprite handles at +0xA were 9 and 14. Following the native pool's
renderer pointer and the original renderer/command strides showed type-2
primary objects and type-2 surface commands. Both primary objects referenced
loaded resource slot 11, matching their actor records. The actor WORD at
+0xC was 0 and 1. Original `CAD10` compares that WORD (via
`[esi-0x28]` when `esi=actor+0x34`) with the input manager's selected handle;
on equality it writes the hit result `0x37` and the actor slot. Thus +0xC is
tracked as a hit handle, not as a second sprite handle. The observer now fails
if a primary object or command is inactive
or its resource differs from the actor.

This confirms that the original client allocated connected native render
objects for both NPCs during the normal world frame. It does not establish
actual device pixels, hit-test success, physical click acceptance, or quest
completion. The historical `world_accepted=false` classifier is not evidence
against this narrower live observation.

## Physical NPC Selection on Own Server (2026-09-23)

`native-ui-npc-click-20260923-01` restored a saved town character at (110,70)
against the isolated C++ server, with diagnostic NPC1606 at (110,69). The
Computer Use screenshot of the original client showed both NPC sprites and the
player character. A screen click on NPC1606 caused the unmodified client to
send decoded C2S `080037460600002f` (`packet-decode-0707.json`): logical `37`,
little-endian identity `1606`, valid native codec checksum and matching client
plaintext. The server replied, and the original client displayed the NPC's
1/7-page dialogue window. The screen capture is `npc-dialogue-page1.jpg` in
the same run directory. This closes the prior gap between a physically selected
NPC, the original hit-test/producer path, natural transport and visible first
dialogue page on our server.

The run was configured to wait for external movement and ended `HARD_TIMEOUT`
after no movement occurred. It should not be treated as a movement failure or
a full NPC conversation success. Repeated screen clicks on the visible next
page and cancel controls did not advance or close the page in this run. No
natural C2S85/86, journal mutation or quest reward was established by this
physical-input run. The timing or control handling of those buttons is the next
UI path to diagnose; earlier native-call page advancement/confirmation remains
separate evidence.

## Live Dialogue Button Dispatch (2026-09-23)

The read-only `--observe-ui-npc-buttons` mode now records original `C85B0`
entry/return state and natural C2S `37/85/86` packets as separate event files.
It does not call or patch the button handler. In
`native-ui-npc-button-trace-20260923-01`, the original client again sent
`080037460600002f` for NPC1606 and opened page 1/7. A screen click over the
next-page arrow reached `C85B0` as button 3 with event flags `32`; native page
index stayed 0 of 7. The original dispatcher advances only for flag bit 1,
so this observed event was pointer motion/hover, not a page activation.

That run ended in a diagnostic writer error on the second button event:
`lab.write_json` intentionally creates files once, while the new observer
initially reused one filename. The observer now writes a distinct file per
event. The follow-up `native-ui-npc-button-trace-20260923-02` had no NPC
request; external input moved the character from (110,70) to (102,69), and
the native client/save agreement ended `NATIVE_UI_WORLD_MOVEMENT_SAVED`.
Input ownership for that movement was not established. These runs did not
establish a physical button press; the later page gate below does.

The earlier `native-ui-npc-controls-20260923-01` independently recorded a
natural C2S `86` after C2S `37`, and the dialogue window later closed. The
Computer Use call around that time reported external user input, so the exact
actor/action causing `86` is unattributed. No physical-input quest confirmation
or reward has been claimed.

## Dedicated Passive NPC UI Gate (2026-09-23)

The previous external movement runner could terminate on an accidental ground
click while an NPC dialogue test was in progress. `--ui-npc-dialogue` now uses
the same isolated saved town entry but observes natural NPC packets, live page
and widget state, and `C85B0` button events without using the movement success
condition or a native-call input page. It can stop at `open`, `page`, `cancel`
or `confirm`; the last two outcomes explicitly claim only a packet sent, not
server acceptance. Evidence files use distinct names for every button/packet
event so successive events cannot trigger the prior exclusive-create error.

`native-ui-npc-open-gate-20260923-01` reached
`NATIVE_UI_NPC_DIALOGUE_OPEN` with error null: decoded natural C2S
`080037460600002f` targeted1606, and the original client then held native
page index0/count7 with widget61. The follow-up page gate
`native-ui-npc-page-gate-20260923-01` ended `HARD_TIMEOUT` with no C2S37:
the Windows screen tool could not keep focus on this game while another
process's system-error window occupied the desktop. This is no evidence for
or against physical page activation.

`native-ui-npc-page-gate-20260923-02` subsequently reached
`NATIVE_UI_NPC_PAGE_ADVANCED` with error null. The original client sent natural
C2S `080037460600002f` for NPC1606 and held page index0/count7/widget61.
The live `C85B0` trace in `ui-npc-button-0635.json` recorded button3 with
event flag1 and native page index0→1 on return. This confirms that the
physical next-page control works against this server. The user also reported
successful page flipping. Final-page confirmation and its server-side quest
effect remain separate acceptance gates.

`native-ui-npc-confirm-gate-20260923-01` reached natural C2S85
`0a0085341202009a008d` after four observed button3 flag1 page advances
on NPC1607 (page count5). The isolated server logged
`DIAGNOSTIC_QUEST_CONFIRM_ACCEPTED ... no_quest_progress_no_rewards`.
The passive gate had ended immediately on the send, causing the debugger to
close the client; this run did not observe post-confirm rendering or establish
a native crash. The gate now watches a further three seconds after C2S85.

`native-ui-npc-confirm-follow-20260923-01` instead recorded natural C2S86
`0f00860100811a2e6e00470001c21f`: the current client placed a five-byte
dialogue close and a seven-byte movement record in one logical world batch.
The server had required a standalone close and disconnected with
`Recovered world policy or response rejected`. The diagnostic handler now
checks the bound conversation, processes the movement through its existing
policy, then consumes the close and returns the movement ACK. This is limited
to the exact close-then-movement pair. The decoded captured batch and bound
cancellation state have focused executable checks. Live reconnection and
post-confirm stability were not observed in
`native-ui-npc-confirm-follow-20260923-02`: it ended `HARD_TIMEOUT` with the
client connected, world ticks continuing and no natural NPC packet. The owner
reported that the separate Windows game window was not visible in the Codex
workspace during that run. A further visible original-client interaction is
still required to qualify the fix.

`native-ui-npc-confirm-follow-20260923-03` reached
`NATIVE_UI_NPC_CONFIRM_POST_SEND_STABLE`: natural C2S85 was accepted and a
native world frame returned three seconds later with no observed client
exception. The owner then clicked NPC1607 again; natural C2S37 was sent but
the server rejected it because the non-progress diagnostic confirmation had
not rearmed the conversation. That handler now rearms after successful commit.
`native-ui-npc-reopen-gate-20260923-01` subsequently reached
`NATIVE_UI_NPC_REOPENED`: second C2S37 was accepted and the original client
returned to page index0/count5/widget61 on the same connection. This verifies
the physical confirm/reopen sequence in the diagnostic conversation. The
runner intentionally closes its debugged game at the reached gate; that
normal test teardown must not be reported as a client crash.

The mixed close/movement branch initially restricted sessions to `InWorld`.
The existing world-entry path can retain `CharacterSelected` while its
world-ready movement binding is valid. The branch now uses the same bounded
states as the standalone NPC route and requires a bound opened conversation.
`test_physical_npc_close_and_ground_move_share_one_frame` replays the captured
logical body `860100811a2e6e00470001c2` against the isolated C++ server:
it receives movement ACK, preserves the connection, and opens NPC1607 again
with next request word0x1235. The separate physical cancel/movement run
`native-ui-npc-cancel-move-gate-20260923-01` timed out after black-screen
capture produced no NPC request; live UI acceptance of that mixed packet
remains open.

## Private desktop click probe (2026-09-24)

`artifacts/playtests/private-npc-unpacked-20260924-01` copied the live account
database into an isolated test database, placed test character 1 at (111,70),
and launched the unpacked client through the native C++ launcher on a private
desktop. Both runs reached the world, and the server logged guide spawn.
The game window client area was 1920x1009. Mouse messages aimed using earlier
1024x768 NPC projections moved the character instead; no new natural C2S37
was observed. These runs are an input-coordinate failure, not evidence that
NPC selection or the service-side quest handler fails. The probe now skips
NPC clicks in an unqualified viewport. The persistent server and original
database were restored and checked after each run.

The later private memory probe found live NPC actors 1606=(110,69) and
1607=(112,70), with 800x600 world projections (480,440) and (600,420).
Posted mouse messages at those projected points still triggered ground movement
rather than C2S37. Actor location is known, but this private posted-message
path is not a qualified NPC click method.

## Same-frame confirmation and next interaction (2026-09-24)

The original UI can queue logical C2S85 followed by C2S37 in one encrypted
world frame. The diagnostic town handler now preflights both operations,
commits the current quest stage, rearms the bound conversation, then emits the
journal and next-dialogue responses. This remains CUSTOM-0021 quest progress,
not a recovered original quest rule.

`test_fresh_town_spawn_and_npc_without_saved_position` now sends that compound
frame to an isolated Release server. It verifies the stage-1 journal, NPC1607's
next dialogue and request word, the later stage-2/reward sequence, database
persistence and restart. The focused test passed. The Release server and
`recovered-quest-sync` assertions also passed.

With zero established connections, the persistent service was restarted with
the tested `build-monster-trace` binary (SHA256
`946b1e0630e2341acbbb950664fc0bc05e3550422159ff57d0cebf562fef7667`).
PID 22496 listens on loopback port 2592. Its pre-restart database backup is
`artifacts/releases/town-chat-welcome-20260924/db-before-npc-batch-20260924.db`.
After restart SQLite `quick_check` returned `ok`, and account/character counts
matched the backup. An original-client click/confirm on this new binary remains
unverified; the isolated socket test is not substituted for that acceptance.
