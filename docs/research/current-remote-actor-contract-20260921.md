# Current Remote Actor Contract Frontier

Authority: current mapped image native-master-01-stable.bin, SHA256
149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763.
Addresses below are RVAs at base00400000. No retired server corpus is used.

## Qualified Original Instructions

The original length leaves and world dispatch table establish:

| S2C logical opcode | Logical bytes | World case | Observed path |
| --- | --- | --- | --- |
| 6F | 81 | 695C8 | Resource-qualified actor insertion via FB460/FC1C0 |
| 5E | 13 | 69A60 | Existing actor update via FB520 |
| 73 | 5 | 69A28 | Actor removal via FB4F0; additional UI/pool cleanup |

Offsets here include the logical opcode, not the outer frame. Original
695C8..695F1 projects 6F DWORD+13 into x=(packed>>2)&7FFF and
y=(packed>>17)&7FFF; its UI lookup ID is WORD+1 masked to0FFF. FB460 and
FC1C0 also mask the incoming actor identity to12 bits before insertion.

Original69A60..69A82 projects 5E DWORD+9 into x=packed&7FF and
y=(packed>>11)&7FF, with the full WORD+1 as lookup identity. FB520 repeats
that coordinate extraction and calls FC920. It also handles appearance/state
fields: 5E must not yet be treated as an otherwise-zero movement-only message.

FC960 is executed in full: it searches128 records at manager+18, stride268,
compares the DWORD identity without implicit truncation, returns a signed WORD
slot orFFFF. Tests cover first/middle/last occupied slots and missing/high-bit
IDs. The collection is world+15383410, separate from the two NPC pools.

## Integration Consequences

Do not directly expose the current14-bit local character identifier in 6F:
4096 aliases0, and16383 aliases4095 on the insertion path. A bounded consistent
per-world actor ID mapping is needed before multiplayer publication. No new
mapping policy or production ID migration is introduced here.

Do not reuse the15-bit entry coordinate layout for 5E's11-bit fields. Confirm
actual observer movement/state semantics and valid coordinate domain before
encoding the update. The apparent128-record capacity also requires an explicit
visibility limit/overflow policy, not unbounded broadcasts.

## Verification And Next Boundary

tests/research/test_current_remote_actor_contract.py has three passing tests:
native length/dispatch,70 coordinate/identity projections, and full lookup
execution. Image is hash-pinned and RX; the projection slices stop before the
UI call, so they do not certify actor rendering or initialization. Pool entries
are synthetic test setup; full6F resource resolution, strings, FC1C0 stores,
5E motion,73 cleanup and live two-client acceptance remain unqualified.

Next trace FC1C0's full actor record writes, its bounded string requirements and
resource preconditions, then exercise insertion/update/removal through the
original client before enabling server emission. These findings must not be
reported as completed multiplayer functionality.

## Native Store And Bounded Codec Follow-Up

Original FC2C3..FC3BE now executes against synthetic bounded actor/input memory.
It writes the12-bit ID, three NUL-terminated strings from body28/44/60 to
actor4/20/36, appearance selector27 from body4 bits8..14, resource word14 from
the supplied component table,15-bit coordinates at actor64/68, header flags
and final body78/79 bytes. Sixteen combinations of identity and string length
(0,1,14,15) preserve field padding and leave the input unchanged.

A separate negative native test fills the final string through the end of the
80-byte body: the original code copies an extra byte beyond the record before
finding NUL. This establishes missing native bounds, not safe acceptance.

RecoveredRemoteActor.h is a lossless owning81-byte logical6F parser, preserving
all unclassified fields. It additionally requires a NUL within each16-byte
string region at logical29/45/61. This is explicitly a defensive server
admission restriction, not a recovered native rejection condition. It exposes
only the proven ID/x/y projections and can re-encode an already parsed record;
there is no appearance builder and runtime emission remains disabled.

Five native tests pass. The Release C++ codec test covers all truncated lengths,
oversize/opcode rejection, each missing terminator and all16 terminator positions,
every byte value at all80 payload offsets, roundtrip and owned-input lifetime.
Full resource setup, rendering, mutation integration and dual-client acceptance
remain open. This work introduces no gameplay defaults or production emission.

## Complete Non-Rendering Update And Removal Branch

The sixth native test executes FB520 and FB4F0 to their real returns, including
FC960 lookup, FC920/FCCC0 queue insertion, FC900/FC560 cleanup, FFCF0 and10E200.
No function calls are replaced. Setup supplies a synthetic occupied slot63,
absent rendering handles (FFFF), unchanged state word0, and manager flags that
skip optional display operations. This does not qualify allocated resource
cleanup or a complete6F-created actor.

Results: update preserves current coordinates86,71 in actor6C/70 and queues
87,72 at actorAC/B0, advancing the write index at actorAA. The40-slot ring
admits39 queued entries; another update leaves the queue unchanged while full.
The surrounding actor records remain byte-identical. This is bounded queue
behavior, not a verified movement speed/interpolation or backpressure policy.

Cleanup mode matters: manager13418=0 retains identity1234; mode1 writesFFFFFFFF
to free the slot. Removing the absent identity again is a no-op. Updating the
removed identity is also a no-op. The test preserves neighbors throughout.
Before live use, confirm the real world's manager flags rather than assuming
any cleanup call frees the identity. Six native tests pass; runtime emission
remains disabled and whole-world/multiplayer acceptance remains unproven.

## Real Client Pool Baseline

native-remote-pool-baseline-20260921-01 reconnects the actual current client to
our isolated server with the roundtrip save. current_remote_actor_live.py reads
the fixed128-record pool in eight-record blocks and control DWORDs13418/1341C/
13420 without modifying memory. The accepted town world snapshot reports all
three controls as1, zero occupied remote entries, and full record bytes SHA256
0b0ff8a35500703b6280e49875c477203a8309c85c92f8e4bfa8d17ca8cbce3e.

This confirms the real clear_mode=1 precondition for the previously executed
FC560 identity-release branch. It does not prove a73 packet removed a rendered
actor, nor does an empty pool qualify resource loading. All21 database tables
and schema remain identical to the source. A captured regression checks the
scoped result, pool layout/controls/empty entries/hash and database equality.
No6F/5E/73 server emission or client data mutation was added.

## Original Pool Initialization Matches Live Bytes

Original FABB0 executes to its real RET14 and initializes all128 records. Its
complete78,848-byte record region hashes to the exact live baseline above.
Every identity isFFFFFFFF; handles3C/3E/40/44/46/48 areFFFF; movement queue
indices are zero. The three manager controls initialize to1, agreeing with the
live read rather than relying on invented oracle defaults.

The five caller arguments are preserved at manager0/4/8 (DWORDs),13424 (WORD)
and13428 (DWORD). Test pointer sentinels are not dereferenced by this function;
they do not qualify the resource dependencies required by later insertion.
The initial10,000-instruction oracle ceiling expired during the128-record clear;
the bounded ceiling is now100,000 with an explicit instruction-pointer return
assertion as well as stack cleanup validation. Seven native tests pass.

This closes the byte-exact initial pool state, not full remote appearance.
FC1C0 still needs qualified bindings through FC130/FF3C0, scene projection and
render-object allocation before a complete resource-backed6F test can pass.

## Source-Loaded Remote Component Bridge

test_current_remote_actor_resources.py now reuses NativeWorldRoleResources to
parse pinned current appearance sources and load real ROMs through61270. Its
actual six-WORD output is passed to original remote component routine FC130,
after original FF370/FF3C0 initialization against the real offline ROM bank.
There are no invented resource handle values or replacements for these native
component calls. Existing filesystem/OS adapters remain explicitly offline.

Three source-qualified preview appearance combinations (0,0),(2,1),(6,6) store
the first four real handles at actor224+4+6*i and the corresponding variants
at actor224+8+6*i. Every handle is non-FFFF. Original remote calls return with
the correct stack cleanup, preserve the component input, and repeated source
lookups reuse the cache without new opens, parser inputs or slots. The test
passes in37 seconds.

These are explicitly preview-subset test appearances, not invented player
equipment or a verified complete6F packet. The bridge now qualifies resource
selection into remote component state; later render-object allocation, names,
full FC1C0 insertion and actual two-client packet acceptance remain open.

## Resource-Backed Full Insertion And Removal

test_current_remote_actor_full.py now executes FB460 through full FC1C0 with
NativeWorldDisplay's original display pool and source-loaded ROM resources.
Input is an explicit laboratory actor7 named RemoteHero at18,12 with a qualified
preview component block, not a recovered official player's appearance. The
bootstrap body comes from our captured run; scene and coordinates are explicitly
overridden to the offline helper's qualified indoor2/15/17,13 fixture.

The first attempt failed at642AA because the fixture omitted the world's driver
binding. Original643FC derives EBX=world+A7F2E64; original64552 writes it to
world+1538341C (remote manager+C). Running this exact original write binds the
already initialized native driver. No false return or ignored read was added.

After this correction, the test passes in118 seconds: FB460/FC1C0 return with
correct ABI, the record contains identity7, RemoteHero and18,12, and its render
handle is in0..4095. FB4F0 then executes allocated-resource cleanup and leaves
identityFFFFFFFF and render handleFFFF. This supersedes the missing-full-
insertion note above for this explicit laboratory appearance. The C++ owning
codec regression also passes.

This is a complete native insertion/removal call chain in the offline adapters,
not the entire6F world dispatcher, a presented frame, a natural multiplayer
session, or production approval. Resource-backed movement and repeated
replacement plus actual socket reception remain next acceptance requirements.

## Full6F/5E Branches With Two Resource-Backed Actors

The full test now starts at original world cases695C8 (6F) and69A60 (5E),
stopping at the shared dispatcher continuation6B517 with unchanged stack depth.
Thus original resource selection runs inside the case rather than relying on
preselected handle arguments for insertion. Laboratory language metadata uses
the actual original131C10 result; the alternate text-conversion branch remains
outside this test. The captured bootstrap plaintext hash/checksum are checked.

The initial full-dispatch attempt failed atE9B60: the UI's source pointer86888
was not bound. NativeBattleCharacterBinding now executes the existing original
actor+90 derivation and source publication. The test asserts the actual source
list count at3F98 is zero; no poisoned count or fabricated callback skips UI
notification. The intervening general UI startup remains outside the helper.

With this dependency supplied, two original6F branches create actors7 and8.
Original5E queues19,12 for actor7 with real rendering resources. A repeated6F
for7 replaces its record and resets the movement queue. Actor8's entire616-byte
record remains unchanged across update, replacement and removal of7. Both
actors are removed through original FB4F0. The test passes in119 seconds.

This qualifies these offline branches and resource lifecycles. Movement arrival/
interpolation, the complete73 dispatcher (beyond its removal callee), actual
TCP reception, rendered frames and two real connected players remain unproven.
No server broadcasting or production configuration is enabled by this test.

## Complete73 Removal Dispatch

The full resource-backed regression now enters original69A28 for logical73
and returns at6B517 with unchanged stack depth, instead of directly invoking
FB4F0. This includes the original auxiliary NPC removal and UI notification
calls. Actor7 is removed, then removed again; actor8's entire616-byte record
remains unchanged. Removing actor8 also leaves its identityFFFFFFFF and render
handleFFFF. No game callback was bypassed to obtain this result.

Verification: `python -m unittest tests.research.test_current_remote_actor_full -v`
passed one test in118.998 seconds, process exit0. The auxiliary NPC pool and UI
list are empty in this fixture; populated-list behavior is not certified by it.
This closes the complete73-dispatch gap for the qualified offline fixture only.
Movement interpolation, actual socket delivery and two-client visible-world
acceptance remain open. Production emission remains disabled.

## Resource-Backed Remote Movement Completion

The same full regression now consumes the5E queue through originalFCD00,
starts movement through FB080/FCA90, advances it through FB0D0 and returns
to standing through FB060. These are the callees observed in the original
per-frame loop FB33F..FB3A1; this test calls them explicitly, not the whole
world frame loop. The native queue-empty check FCC70 passes before/after
dequeue, and the popped target is19,12.

Original FB080 publishes logical19,12 at movement start, before interpolation
finishes. The test independently requires moving state8, nonzero remaining
screen displacement, completion within1000 laboratory ticks of16, zero final
remaining displacement and screen coordinates equal to their initial values
plus the original displacement. FB060 then sets standing state0. Actor8's
entire616-byte record stays unchanged. Existing replacement/removal checks
still pass after movement. No movement values or native return values are
injected to force completion; the input tick is an explicit offline fixture.

Verification: `python -m unittest tests.research.test_current_remote_actor_full -v`
passed in121.972 seconds, exit0. This proves native interpolation for the
qualified single adjacent step and appearance, not all directions, timing
equivalence, presented pixels, live socket reception or multiplayer acceptance.
The full playable-world goal remains unfinished.

## C++ Move And Remove Records

RecoveredRemoteActor.h now includes owning13-byte5E and5-byte73 codecs,
alongside81-byte6F. Both parse exact logical size/opcode and preserve every
byte on re-encoding. The5E accessors expose full16-bit identity, low16-bit
state and11-bit x/y. The73 identity accessor also keeps16 bits; it does not
reuse6F's12-bit truncation. The auxiliary73 NPC identity transform remains
client behavior, not a replacement for the remote role identity.

No builder invents appearance/unknown bits: a parsed record is required for
encoding. Cases69A87..69AA8 use high bits for appearance selection, so masking
the entire packet down to coordinates would lose native data. All runtime
emission flags remain false and no Application broadcast route changed.

Release target recovered-remote-actor builds and CTest recovered_remote_actor
passes. Added checks cover all truncated sizes, oversize, all256 opcodes,
every single-byte mutation of each body, owning lifetime, maximum identity/
coordinates/state and preservation of high appearance bits around19,12.
These are codec tests, not end-to-end socket or multiplayer acceptance.

## Server Integration Identity Boundary

Current RecoveredMovementService::prepare passes the persisted character ID
directly to RecoveredWorldEntry::wire; RecoveredWorldReady allows1..16383.
Remote6F instead reads12 bits. Therefore direct reuse is not safe for IDs4096
and above, even though5E/73 consume16-bit identities. No broadcast is enabled
and no saved IDs have been rewritten. Application world_ready, committed move,
disconnect and completed scene-transfer paths are the integration boundaries;
the existing fixture Map broadcast is not the recovered wire protocol route.

The owning codecs now offer checked with_identity transformations on an
existing parsed record:6F rejects values above4095;5E/73 reject above65535.
Each transformation preserves every other bit, including6F identity-adjacent
flags. Zero is representable at the codec level, not authorization to assign
it to a player. The API is not an allocator or a cross-message identity map.

Release build and focused CTest pass. Tests exhaust all4096 spawn IDs and
all65536 IDs for each event codec, verify untouched bytes, and reject overflow
including the maximum64-bit value. Remaining integration requires a coherent
session/visibility identity policy across local entry, remote events and client
requests, source-qualified appearance projection and live-client acceptance.

## Isolated Socket Probe Route Prepared

CUSTOM-0026 adds DiagnosticRemoteActor and a default-off Application world
record branch. Explicit diagnostic_remote_actor plus language0/1 requires
authenticated loopback recovered movement and remote-actor-diagnostic.db;
other enabled diagnostic options are rejected. Only character1 at area2,
scene15,17/13 is admitted after normal world tick validation. Non-tick records
are rejected while the probe is active; this is not a playable multiplayer mode.

Validated ticks1/33/65 emit separately framed6F/5E/73 for laboratory actor7,
18/12 to19/12, matching the offline preview appearance. The stage count stops
at65 and disconnect removes session-local progress. No saved actor or gameplay
attributes are added. Tick spacing is a test choice, not a recovered server
policy or a wall-clock guarantee. This route avoids the unimplemented general
online identity allocator by admitting only local1 and synthetic remote7.

Release god2-server, god2-tests and recovered-remote-actor build. Focused CTest
config, recovered_remote_actor, recovered_movement_service and
application_startup all pass. Configuration tests reject non-dedicated DB,
invalid/missing dependencies and competing diagnostics; codec tests qualify
all three laboratory logical records and both language values.

No live probe has been launched yet, no production config changed, and these
tests do not establish the new Application branch's actual socket delivery.
Next: run this explicit mode on a copied isolated indoor save, capture all
three wire/plain records, observe the actual native role pool and verify the
database remains unchanged. Real two-player visibility remains a separate gate.

## Live Observation Gate Prepared

current_remote_actor_live.snapshot now reads actor movement state38, screen
coordinates74/76 and remaining displacement90/94 in addition to logical
coordinates and queue indices. RemoteActorLifecycle requires ordered observed
spawn18/12, completed movement19/12, then disappearance. Movement completion
requires standing state0, empty queue, zero remaining displacement and changed
screen position. Empty pools before spawn do not certify removal; premature
disappearance, unexpected identities, duplicate entries, invalid handles or
queue bounds and incompatible manager controls reject the observation.

This is only an observation gate; it does not certify wire delivery or rendered
pixels, and does not itself launch a client. Captured snapshots are copied to
retain evidence if callers reuse input dictionaries. Four synthetic gate tests
and four existing captured door/reconnect regressions pass. The apex launcher
does not yet expose this probe or feed the gate. Its existing configuration
writer also emits other diagnostic numeric defaults, so the dedicated mode
must omit those explicitly rather than weakening isolation validation.

## Real Socket Lifecycle Accepted In Isolated Probe

The apex launcher now exposes --remote-actor-probe-language, creates a fresh
remote-actor-diagnostic.db without altering another run's database, rejects
competing diagnostic/restore/movement probes and feeds the native frame-return
snapshots into RemoteActorLifecycle. This mode has an8000-event observation
ceiling within the existing timeout, not an unbounded wait.

Attempts01 and02 are retained as failures:01 omitted the existing process-local
Taiwan locale option and exited during -gb resource loading before networking;
02 reached the world but rejected its first tick because a new character has
no position save until movement. The route now permits an absent save for the
existing fixed indoor17/13 bootstrap, while still rejecting any nonmatching
saved position and all movement requests. It does not fabricate a position row.
CUSTOM-0026 timing is now ticks1/3/5 (superseding1/33/65 above).

Run native-remote-actor-lifecycle-20260921-03 completed with
NATIVE_REMOTE_ACTOR_POOL_LIFECYCLE_OBSERVED and no error. Actual S2C frames:
packet0521:6F/84 bytes; packet0837:5E/16 bytes; packet1147:73/8 bytes.
Their captured plaintext hashes, framing and independently recomputed checksum
pass. Actor7 is observed at18/12, screen1240/500 with render handle0, then19/12,
screen1280/480 with queue1/1, movement state0 and zero remaining displacement.
After73 the remote pool is empty. The server logs exactly one stage0/1/2 and
no policy rejection. The fresh DB integrity check passes and recovered_positions
remains empty. Fresh login/character creation did write their own isolated
records; this is NOT an assertion that the entire new database stayed unchanged.

Six remote-observation/config/captured-evidence tests and four captured
door/reconnect tests pass. No official connection, OS locale change, production
configuration promotion or physical desktop action was used. This closes the
single synthetic remote actor's actual socket/native-pool lifecycle gap only;
two real players, visible rendered avatars and general identity/appearance
mapping remain open. world_accepted remains false.

## Local-To-Remote Normal Component Correspondence

Original684CD..684EB (normal2A world initialization) and69941..69963 (normal6F)
both call61270. In the captured bootstrap tested here, the local call takes
selector1 from body6, selector2 from (bodyDWORD0>>16)&7F and the8-byte component
block from body12. The remote case takes selector1 from (bodyDWORD4>>8)&7F,
selector2 from (bodyDWORD0>>14)&7F and the block from body20. These are different
bit positions: copying the local packet's initial words wholesale is incorrect.

The full native resource-backed regression now builds an additional explicit
laboratory actor9 after the lifecycle checks. It projects those selectors and
the8 component bytes from the already captured/local-initialized2A fixture,
enters the complete6F dispatcher and compares each of the four primary
remote component handles and variants against WORLD+A7E04D0's local component
records. All eight comparisons pass. Complete73 then removes actor9.
No component/game call returns are substituted for this comparison.

Verification: full native regression passes in124.494 seconds, exit0. The
captured fixture's selector1 is within the remote7-bit range. This is one
qualified normal appearance correspondence, not all possible selectors or
variant combinations, mounted/transformed branches, names/titles, equipment
ownership, production player projection or visible two-client acceptance.
The current local bootstrap still retains separately documented historical
opaque selectors; correspondence does not certify them as original player
equipment. No production appearance builder was enabled by this test.

## Expanded Variant Qualification

The full regression now iterates the49 combinations of the two currently
projected creation variants0..6. Each case executes original68315..68558
(local data copy, normal resource selection, variant setters), then the full
remote6F branch, compares the four primary handles/variants and removes the
remote record via73. This does not enumerate all equipment or character models.

The first expanded run failed all49 explicit variant-value checks because
the assertion incorrectly treated the variant as a16-bit field (FF00..FF06).
Original FFA20 writes one byte at component+8+6*i; FFA40 also reads one byte.
The comparison now reads16-bit handles and8-bit variants, without interpreting
the adjacent sentinel byte as part of the variant. The failure is retained here
as a test-layout correction, not reported as an original-client defect.

Corrected verification passes: `python -m unittest
tests.research.test_current_remote_actor_full -v`,149.197 seconds, exit0.
All49 combinations match for four primary handles and four variant bytes,
both requested variant values are asserted directly, and every case finishes
with actor9 removed. Earlier insertion, native interpolation, replacement and
complete73 lifecycle checks remain in the same passing test. These49 cases
are offline original-code/resource evidence, not49 real-client socket runs or
general multiplayer/production acceptance.

## C++ Normal Component Projection

RecoveredRemoteActor::with_normal_world_components now transforms an existing
owning6F record from an exact36-byte2A body, following the verified selector
and component-block correspondence. It rejects nonzero local body32/33 or
remote body76/77 (special appearance selectors) and local selector1 above127.
It preserves identity, names, coordinates, language and unrelated bits; only
the two selector fields and8 component bytes are changed. No new spawn record
is fabricated, and this operation does not authorize equipment or certify
resource availability. Runtime emission remains disabled for general actors.

Release recovered-remote-actor builds and focused CTest passes. Tests cover
the49 supported creation-variant combinations, every truncated source length,
oversize input, both bytes of each special selector and selector overflow.
All128 selector values are checked for exact bit relocation and adjacent-flag
preservation; these128 codec checks are not128 native-resource qualifications.
This prepares a reusable component transform for real player projection without
promoting the synthetic RemoteHero fixture into an authoritative player model.

## Exact Session Appearance Projection On Real Client

The isolated CUSTOM-0026 route now retains the exact decoded2A body returned
by RecoveredMovementService::prepare for that session. It uses the checked
C++ normal-component transform when generating6F and erases this transient
body on disconnect. It does not reconstruct a second profile independently or
write projected components to the database. Other laboratory actor fields
remain explicitly synthetic, and generic runtime broadcasting stays disabled.

Native snapshots now include four local/remote resource handles and8-bit
variants. The current launcher requires equality for every observed actor
snapshot, with nonnegative local handles; synthetic tests reject mismatches
and equally missing resources. Earlier captured preview runs retain their
separate lifecycle-only scope and do not retroactively receive this acceptance.

Run native-remote-actor-projected-20260921-01 completed successfully: actual2A,
6F,5E and73 packet evidence; all four handles/variants equal at remote spawn
and movement completion; actor then removed. Regression independently verifies
frame lengths, plaintext hashes/checksums and the actual2A-to6F bit/block
mapping. Fresh diagnostic DB passes integrity and has no saved position rows.
Release server build and12 observation/captured-door regressions pass. Client,
server and debugger processes exited after the run.

This is real single-client socket/native-resource acceptance for the session
bootstrap's normal appearance, not visible pixels, authoritative original
equipment, all avatars or two-player visibility. Those gates remain open.

## Recovered World Push Transport

Session::send_world_records now provides a separate logical S2C push path for
future inter-session delivery. The fixture send(Packet) path remains unchanged
and still refuses recovered-mode output. The new path requires recovered mode
and WorldTailAccepted on the network strand, envelopes bounded logical bytes
with RecoveredWorldFrame, preserves existing ordered async writes and shares
pending-write reservations/count/byte limits with ordinary send. Empty/oversize
inputs, premature use and write-queue overflow fail closed. Closed-session
calls do not revive a connection. No packet payload logging was introduced.

Callers must wait until tail acceptance, not call this from inside the
world_ready callback before the strand commits that state. The application
still owns target visibility, opcode semantics and authorization. A queued
write is not an acknowledgement from the client. No generic actor broadcasting
or player visibility registry has yet been connected to this API.

Release server/tests build. CTest session_state, network and application_startup
pass (91.77 seconds total). New real-loopback synthetic-peer cases check
pre-tail rejection, FIFO pushes, isolation between two connected Sessions,
subsequent movement ACK operation, post-close calls and empty/oversized input.
This is transport/state evidence, not two native clients or rendered avatars.

## Visibility Membership Policy

CUSTOM-0027 RecoveredVisibility prepares per-recipient logical records from
caller-supplied parsed6F/73 records. Same area/scene peers receive symmetric
spawns on entry; remaining same-scene peers receive removal on departure.
No self or cross-scene delivery is generated. The registry rejects duplicate
session/character/native ID, zero identities, incompatible spawn/removal IDs
and encoded scene bounds. It does not assign wire IDs or authorize ownership.

With128 native remote slots,129 total same-scene participants are admitted;
the130th is rejected before membership changes. Delivery-vector allocation
also precedes mutation. Duplicate/unknown departure is idempotent. This is a
custom all-same-scene interest policy, not proof of original range/culling
behavior. Records remain owned copies and no database state changes.

Release recovered-visibility builds; focused visibility/remote-codec CTest
passes. Coverage includes symmetric recipients/identities, cross-area/scene
isolation, collisions, invalid input, reconnect, departure idempotency, full
native capacity, rejection without insertion and slot reuse after leave.
No Application caller or real-client visibility acceptance is added yet.

## Transactional Visibility Scene Change

RecoveredVisibility::transfer now accepts an already-authorized new scene
snapshot for the same session/account/character/native ID. It rejects missing
bindings, ownership/identity substitution and same-scene duplicate transfers.
The destination uses the same scene/bounds/collision/capacity validation as
entry, excluding only the transferring member. No membership is changed before
validation and all delivery allocations complete; the final fixed-size Presence
assignment is statically required to be nonthrowing.

Every old same-scene peer receives the traveller's73; the traveller also
receives73 for each old peer. Only after those removals does the plan contain
new-scene symmetric6F notifications. Other areas/scenes receive nothing. Empty
source/destination sets are valid. The caller must invoke this after authoritative
scene acceptance; this registry neither commits a database transfer nor proves
that network delivery completed. A socket failure remains the caller's cleanup
responsibility, not a rollback of packets already received.

Release build and visibility/codec CTest pass. Added cases verify recipient and
opcode order, account/character/native-ID mismatch, missing/duplicate transfer,
invalid destination, full destination rejection with old membership retained,
capacity recovery after departure and correct recipients when leaving the new
scene. Runtime integration and original-client scene-change acceptance remain
pending; CUSTOM-0027 is not promoted to production.

## State-Preserving Visibility Movement

The registry now routes caller-supplied parsed5E ordinary movement to other
same-scene sessions and updates its stored6F position for later arrivals.
Session/account/character/scene/native ID must match. The current policy only
admits adjacent steps with unchanged state and no extra appearance selectors;
special appearance and unqualified high fields are rejected rather than silently
discarded. This is a bounded supported subset, not a native claim that those
fields are invalid. A same-coordinate repeat produces no delivery. Terrain,
speed, durable commit and sequence authorization remain the caller's responsibility.

Checked6F with_position preserves position-kind bits and all other bytes and
rejects coordinates above15 bits. A5E target itself remains11-bit. Deliveries
are fully allocated before the nonthrowing stored-position assignment. Tests
cover wrong ownership/scene/identity, unsupported state/appearance, distant
steps, no self/cross-scene send, repeat suppression and a subsequent entrant
receiving19/12 rather than the original18/12. Coordinate codec tests enumerate
32768 complementary x/y pairs, preserving every other byte, plus wide overflow
rejections. Release visibility/remote-codec builds and both CTests pass.
Application integration and multiplayer live acceptance remain open.

## Committed Movement Path Handoff

RecoveredMovementService::CommittedMove now includes an owning ordered path
of displaced destinations. A batch ending where it began retains its intervening
steps; stationary requests still receive their existing ACK but add no path item.
Path allocation and batch validation precede commit_position. Failed validation
or persistence throws without returning a path or publishing movement state;
successful batches retain one durable revision and the original ACK sequence.
This supplies the per-step input needed by visibility movement instead of
attempting to broadcast only the batch endpoint. It does not send packets or
activate CUSTOM-0027. Existing appearance, identity and Application integration
gaps remain open.

Release god2-tests and god2-server builds pass. CTest recovered_movement_service,
recovered_world_service, recovered_position_repository, application_startup and
recovered_visibility pass (5/5). Path assertions cover first displacement,
stationary input and a round trip containing an intervening stationary request;
existing invalid-batch and stale-save cases continue to reject.

RecoveredVisibility::move_batch accepts ordered parsed5E records. It stages
position changes and deliveries locally until every step passes ownership,
identity, scene, appearance and adjacency checks. A later invalid step therefore
does not partially update the registry. Single-step move delegates to this same
path. Stationary repeats are suppressed, but round trips retain every displaced
step for each same-scene peer. Empty batches still check session ownership.
Tests verify two recipient streams, cross-scene exclusion, endpoint snapshots
after round trips and unchanged snapshots after a partially valid rejected batch.
The visibility and movement-service CTests pass (2/2). This API still takes
parsed records; committed path-to-record conversion, Application routing and
two-client runtime acceptance remain pending.

## Visibility To TCP Qualification

The Session test peer now permits explicit session and selected-character IDs
while preserving the previous defaults. recovered_visibility_transport completes
the real recovered connection handshake and initialization tail for three TCP
peers with distinct identities. Two share scene2/15; the third occupies2/4.
The registry outputs are routed by actual Session::id through send_world_records.
Wire assertions cover symmetric6F entry, ordered outbound/return5E to only the
other same-scene peer, no self/cross-scene bytes, and73 after the first socket
closes. Repeated explicit cleanup produces no extra bytes and removes membership.

Release god2-tests build and full session_state CTest pass (92.94 seconds).
Authentication handlers and actor records are synthetic fixtures; disconnect
cleanup is invoked by the test. This proves registry-to-Session TCP composition,
not Application integration, independent production accounts, native two-client
rendering or gameplay acceptance. Runtime activation remains disabled.

## Bounded Text Field Projection

Current FC2C3..FC33F independently copies body28/44/60 to actor4/20/36,
including each terminating NUL. RecoveredRemoteActor::with_text_fields now
replaces the corresponding logical29/45/61 fields in an owning record. Inputs
are explicit encoded byte spans, maximum15 bytes with no embedded NUL. All
three are checked before replacement. Each16-byte destination is zero-filled
before copying, preventing stale trailing text. All non-text bytes are preserved.
The helper never truncates a multibyte sequence or performs an encoding guess.
Encoding validity and semantic assignment of the three fields remain caller
responsibilities; the helper does not certify a primary-name/title mapping.

Codec tests check lengths0..15 for all nonzero byte values1..255, all three
overflow/NUL rejection positions, unchanged source and unrelated fields.
The pinned native instruction test adds four distinct field combinations,
including high bytes, empty fields and15-byte boundaries, verifies native
destinations/canaries and unchanged source. All8 native contract tests and both
remote codec/visibility CTests pass. This is byte-copy qualification, not full
6F language conversion, renderer text acceptance or production player emission.

## Native Display Text Binding

The new test executes the original remote FD427..FD45D slice and its complete
1097D0/109E70/109F80 setters, without replacing those calls. Remote actor4/20/36
reach display-object byte buffers70/81/92 respectively. The object stride is
A7E0 and its signed validity field at28 must be nonnegative. These setters prefix
max(0,(14-byte_length)/2) spaces using integer division, then copy the full string
and NUL. Empty strings and14/15-byte boundaries are covered, as are high-byte
inputs. Canary bytes after each result remain unchanged.

Original local1003E0..100422 is then executed with the same strings at local
actor B7/C7/96. It produces byte-identical three display buffers. In particular,
remote logical29 (body28, actor4) shares the local actor+B7 name display setter.
The existing world-entry projection regression independently verifies its supplied
name copied to local+B7. This supports a name-field correspondence; it is not
evidence for a guild/title semantic label for either remaining text field.

All9 remote contract tests pass. The8 world-entry regressions pass with unittest
discovery (their sibling imports require tests/research on the module path; the
initial dotted-module invocation failed that import and was corrected). These
are native instruction/data-path checks, not on-screen text rendering or full
6F language-conversion acceptance. Application multiplayer remains unintegrated.

## Resource-Backed Full6F Display Text Acceptance

test_current_remote_actor_full now reads all three text buffers from the actual
display object allocated by full original6F processing. Initial RemoteHero and
OtherHero records occupy separate native actor/display objects. Replacing actor7
through full6F with a15-byte first field, a separate second field and high-byte
third field produces the expected native centered strings. Replacing it again
with the shorter initial text leaves no displayed suffix. Actor8's complete
616-byte record and all three display strings remain unchanged.

The test uses the original branch, real resource/display pools and matching
native language bit. No name/label setter is stubbed. It continues through the
existing movement, repeated replacement/removal, local appearance projection
and49 variant combinations. The complete test passes in155.221 seconds.
This closes the full matching-language6F to display-buffer check for these
fixtures, not cross-language conversion, font/glyph drawing, real socket delivery
of these changed names, or production player-profile projection.

## Own-Server Profile Name Socket Acceptance

Application's default-off CUSTOM-0026 probe now obtains the selected character
from list_for_account(session.account_id), checks the selected ID and bounded
nonempty profile name, and projects its bytes into logical29. The synthetic
actor7 deliberately mirrors this owner's name; the two other fields stay empty.
This does not create or claim a second authenticated player. No name is added to
ordinary server logs and no persistent profile/position is modified by projection.

The read-only live snapshot now collects three actor strings and the matching
display-object text buffers. The optional text gate checks bounded strings,
original byte-count centering and unchanged text across movement. The live probe
requires both component and text checks; older captured evidence is not silently
upgraded to the new qualification.

Fresh run native-remote-actor-name-20260921-01 completes original client6F/5E/73
reception, movement and removal against the rebuilt own loopback server with
NATIVE_REMOTE_ACTOR_POOL_LIFECYCLE_OBSERVED and no error. Its new regression
independently checks the isolated DB name against the single6F payload, frame
length, plaintext hash and checksum, then compares native actor/display strings
at spawn and movement completion. SQLite integrity is OK; recovered_positions is
empty. All10 live-probe regression tests pass. God2, god2-server and cdb are no
longer running after the run. world_accepted remains false. This certifies the
matching-language test name's socket-to-display-buffer path, not on-screen font
rendering, cross-language names, two real clients or production multiplayer.

## Checked Player Presence Projection

RecoveredPlayerPresence::from_world_entry converts a checksum-validated37-byte
logical2A and caller-authorized valid profile into caller-supplied6F/73 templates.
Session/account/character must be nonzero; character must be1..4095 and exactly
equal the14-bit local ID. No truncation, DB-ID rewrite or implicit allocator is
used. Scene/coordinates come from the actual world entry; coordinates must fit
the11-bit ordinary movement route and the template coordinate-kind must match.
These are current supported-subset restrictions, not native invalidity claims.
Normal components and bounded primary name use the previously qualified mapping;
secondary template strings and unrelated fields are retained, with text padding
normalized. Template correctness and profile ownership remain caller obligations.

Visibility tests cover ID1/4095, mismatched IDs,4096 rejection, position overflow,
kind mismatch, truncated/checksum-corrupt input, identity/name/location output.
The three-peer Session test now builds its presences from each peer's exact sent
world-entry frame instead of independent hard-coded coordinates/identities, with
distinct synthetic profile names. Its walk is17/13 to18/12 and back. This remains
synthetic-account TCP composition, not Application integration. Both visibility
and full Session CTests pass; Session takes93.10 seconds. CUSTOM-0027 remains off.

## Isolated Application Multiplayer Route

Application now integrates CUSTOM-0027 behind default-off
development.diagnostic_player_visibility. Config requires authenticated loopback
recovered movement/world/dual connection, player-visibility-diagnostic.db and
explicit diagnostic_remote_actor_language0..1; competing diagnostic modes are
rejected. Production is still disabled. Earlier notes saying no Application
integration describe the prior stages, not this new isolated route.

World preparation looks up the selected profile under its authenticated account
and builds a checked presence from its exact2A. No visibility is published from
world_ready: the first accepted standalone world tick joins after the Session
tail state is committed. A weak Session registry sends returned logical records
through send_world_records. Successful move_committed paths produce ordered5E
with the character's exact ID, then update the visibility snapshot. Disconnect
clears pending/weak bindings and emits73 to remaining same-scene peers. This mode
uses the ordinary qualified laboratory template, neutral state, indoor navigation
and no transfer/battle/other diagnostic modes. It is not a general gameplay route.

test_player_visibility_server.py launches the real rebuilt Application server,
registers two distinct synthetic accounts/characters in a temporary isolated DB,
and verifies no publication before the first tick, symmetric6F identity/name/
coordinates, two-step5E order, movement ACKs, one durable position revision,
disconnect73, reconnect6F, and invalid-jump rejection without saved-state mutation.
The black-box test passes. It uses original-code-generated movement/world-tail
requests but synthetic TCP peers, not two native clients. Native queue pacing,
larger online-ID allocation, scene-transfer integration, rendered avatars and
production acceptance remain open. Existing production configs are unchanged.

## Distinct Native Probe Identities

The native probe previously hard-coded one public account and character.
--lab-peer0 preserves codexlab/CodexTrial; --lab-peer1 selects the fixed public
codexpeer/CodexPeer pair with the same existing public lab password. Arbitrary
identity input is not accepted. Peer1 requires isolated native-login and character
creation probes. Native control setters and submit functions remain the same.
Stub-callee execution tests verify generated-page arguments/stack cleanup for
both identities; these tests alone are not native login evidence.

Fresh native-remote-actor-peer1-20260921-01 completes the actual original-client
login, creation, world entry and remote actor lifecycle with no reported error.
The recorded peer selector is1. Independent regression reads the selected
character profile as CodexPeer, joins its account to the existing normalized
identity god2-bytes:636f64657870656572, and verifies its name through captured6F,
native actor strings and display buffers. The initial DB assertion expected raw
username text and was corrected to RecoveredAccountLogin's existing byte encoding.
All13 probe/identity tests pass; God2, god2-server and cdb are stopped.

This is a second identity in a separate fresh isolated server run, not concurrent
two-client acceptance. The current launcher still owns a server per run and
shared-server lifecycle/endpoint orchestration remains the next runtime gap.
world_accepted remains false; no production promotion.

## Shared Server Attachment

apex --shared-server-manifest now borrows an existing explicitly identified
Application process instead of starting/stopping a private server. The manifest
schema is god2-shared-loopback-server-v1 with pid, create_time, config,
config_sha256 and two ports. Both manifest/config must be under artifacts/runs.
Attachment checks process generation, the owned build/Release/god2-server.exe,
its unique --config argument, unchanged configuration hash, authenticated isolated
visibility settings and player-visibility-diagnostic.db beneath that config's
directory. Exact live listener ownership must match127.0.0.1:2592 and the second
declared character port. No arbitrary or external endpoint is admitted.

The borrowed process exposes health checks only; attachment close never terminates
the server. CLI guards reject competing single-client diagnostic ownership modes.
The native connect observer recognizes verified shared listeners using the same
allowlist path as an owned C++ server. No server seed events are fabricated.

test_shared_cpp_server launches a real isolated Application process, attaches
twice, closes/recloses one attachment, rejects stale generation/hash/port/PID
manifests and confirms the other attachment and listener remain live. Closing
both still leaves the owner running; only the test owner stops it. The test
passes, apex --help loads successfully, and13 existing probe/identity regressions
pass. Native two-client orchestration and shared-run observation are still not
executed; this change is the required attachment/lifetime support, not acceptance.

## Shared Client Profile Lifetime

Inspection found that independent profile_context calls mutate and restore the
same work-copy config files, so concurrent probes would race even when borrowing
one server. Shared attachment now requires client_profile in the owner manifest:
the exact client root plus SHA256 entries for config/display.settings, ctserver.ini
and ddraw.ini. It verifies these files before and after the native probe, rejects
paths escaping the client root, and never writes/restores those files. Its only
local setting is a scoped process-environment GOD2_CLASSIC_RESOLUTION=800x600.
The owner must apply the normal profile once and keep it until both probes stop.

The real-server attachment test covers nested independent borrowers, unchanged
file bytes, environment restoration, wrong-root rejection and detection of a
mid-probe setting change. It passes; both changed Python modules compile. This
removes the configuration restore race but is not yet the two-client owner
orchestrator or native simultaneous-run evidence. No client files were changed
by this test; it uses a temporary fixture profile under its checked run directory.

## Live Display Pool Erratum and Two-Client Acceptance

Run native-shared-visibility-20260921-04 exposed an observer error: snapshot
read display strings at world+0x39c (local pool). Distinct remote actor names
were correct, but the observer returned the owner's local display text.
Earlier owner-mirroring name/peer1 probes cannot prove remote display strings;
their DB, packet and actor-string evidence remains valid. The configured offline
harness proves its explicit pool binding, not the live world's binding.

Native RVA64D02 selects world+0xaba32e0; RVA65408 supplies that pool to FABB0,
which stores it at manager+8. Snapshot now follows manager+8 and checks the
build-specific remote pool. A memory-reader regression rejects local-pool reads.
Historical capture tests explicitly retain actor-only scope.

Fresh run native-shared-visibility-20260921-05 returned
TWO_NATIVE_PLAYER_POOLS_OBSERVED. Two distinct native processes (17808/4480)
authenticated public lab accounts against one isolated own-server Application.
CodexTrial received native actor1/CodexPeer; CodexPeer received actor2/CodexTrial.
Both original remote display pools contain the OTHER player's centered name,
position17/13 and four valid resource handles. The owner waits for both evidence
markers, cross-checks identities and only then releases both observers. Both
peer run.json reports returned NATIVE_SHARED_PLAYER_VISIBILITY_OBSERVED.
Database integrity and identity/name joins are checked by the capture regression.

Scope is simultaneous native role/display-pool acceptance, not pixel inspection,
moving-player synchronization, reconnect lifecycle or full gameplay. Existing
synthetic movement/lifecycle evidence is not upgraded by this stationary run.
world_accepted remains false; production visibility remains disabled.

Repeat native-shared-visibility-20260921-06 passed with new native processes
15288/18328 and a fresh isolated database after adding the explicit remote-pool
check to the shared observer. Both saved runs are covered by the cross-binding
regression. Remote-actor/public-identity suites pass15 tests; the real shared
server attachment suite passes1 test with tests/research on sys.path. A combined
module invocation initially failed because that existing attachment test imports
its sibling harness by bare module name; explicit search-path setup resolves it.

## Native Peer Departure

shared_visibility_run --observe-departure retains peer0 after the mutual
visibility barrier and permits peer1's owned diagnostic process to finish.
Peer0 qualifies removal only after prior visibility and the matching release
manifest, with the same observing process and original remote display pool.
It continues native world frames until the remote pool is empty; this is not
an empty initial pool accepted as removal.

native-shared-departure-20260921-01 passed with native PIDs15564/20208.
The retained peer observed actor1/CodexPeer, then received exactly one captured
S2C0x73 for identity1 and reached an empty remote pool. The capture regression
checks the eight-byte frame, plaintext hash, checksum, target identity and
unchanged manager/display-pool/local components across removal. Peer0's report
is NATIVE_SHARED_PLAYER_DEPARTURE_OBSERVED; the owner's departure_observed=true.
Negative gate tests reject missing prior visibility/release, another observing
process and the local display pool. This covers own-server disconnect removal,
not moving-peer synchronization, reconnect or rendered-pixel verification.
No production flags were enabled and world_accepted remains false.

## Two Native Clients: Three-Step Movement

shared_visibility_run --observe-movement first requires mutual visibility,
then requests peer1's existing original5024C0 path producer for three steps:
17/13 ->18/12 ->17/13 ->18/12. Peer1 must finish all three ACKs and return to
idle before publishing its completion marker. Peer0 waits for that marker and
checks the remote actor destination, empty movement queue, zero remaining motion
and completed screen coordinates. Neither probe fabricates movement packets.

native-shared-movement-20260921-04 passed with native PIDs18164/4760.
The captured S2C5E sequence contains all three destinations in order for the
other player's identity. Peer1 ACKs are5D01/02/03; peer0's remote queue is3/3,
state0, coordinates18/12, screen1240/500. SQLite contains that character's
area2/scene15/18/12/revision3 and passes integrity_check. The capture regression
checks frame lengths, plaintext hashes, checksums, identities, destinations,
ACKs and committed position. The targeted suites pass18 tests.

Failed runs remain preserved:01 exited during startup;03 stopped before the
mutual visibility barrier. Run02 completed movement but timed out because the
observer expected an incorrect +40 screen-X delta for the diagonal step. Its
actual stationary screen1240/500 exposed that observer error; run04 is a fresh
acceptance after correction and the full-path completion barrier. Startup
intermittency is not resolved by this movement success.

This proves a moving native producer and native remote consumer through the
own-server movement/persistence route. It does not prove simultaneous movement
in both directions, scene transitions, reconnect, pixel rendering, load capacity
or complete gameplay. Production flags remain unchanged.

## Both Native Players Moving

--simultaneous-movement starts the existing three-step native path on both
clients after mutual visibility. Each publishes its own completion marker
atomically, then observes the other producer's completed movement. Both remote
acceptance markers must exist before either observer exits. This prevents a
successful peer from disconnecting before the other finishes its observation.
The flag excludes departure mode; previous single-mover mode is retained.

native-shared-bothmove-20260921-01 passed with PIDs9724/23284. Both peer reports
returned NATIVE_SHARED_PLAYER_MOVEMENT_OBSERVED. Each captured exactly three
S2C5E updates for the OTHER identity:18/12,17/13,18/12. Both local producers
received5D01/02/03; both remote pools ended at18/12,screen1240/500,state0,
queue3/3 and zero remaining motion. The two distinct SQLite character positions
are independently area2/scene15/18/12/revision3; integrity_check is ok.
The saved-run regression checks packet hashes/checksums, identities, names,
ordered destinations, local ACKs, native queue completion and both DB rows.
The targeted suites pass19 tests.

This is concurrent two-client bidirectional movement acceptance, not a claim
of identical wall-clock step timing, network impairment tolerance, population
load, rendered-pixel acceptance or complete gameplay. Startup intermittency and
live reconnect remain open. No production activation or source-client edits.

## Two-Account Server Restart and Position Restore

--restore-database accepts only player-visibility-diagnostic.db under the run
evidence tree with a successful simultaneous-movement owner report. It checks
integrity and two persisted area2/scene15/18/12/revision3 positions, then uses
SQLite read-only-source backup to a fresh isolated run database. The source hash
is preserved. Restore cannot combine movement or departure diagnostics.

Shared native login uses the existing saved-character selection route, requires
one character per account and does not submit character creation. The observer
checks each local position18/12 and reset ring010001, as well as the OTHER
native actor at18/12. The owner verifies position rows did not change. Error
handling now always resets result to FAILED, including late restore validation
errors after both client reports succeed.

native-shared-restore-20260921-01 passed with native PIDs21228/24000, a new
server process and a backup of native-shared-bothmove-20260921-01. Both peer
reports passed. The source SHA256 remains
d35c52bc3a02e9e2476fc3b30560625dafb9c313da7a4105e94c661382bcf02e.
The regression checks original/restored character IDs, owners, profile/name
bytes and position rows, database integrity, single-character login, absence
of creation submission, distinct local identities and native local/remote
coordinates. The targeted suites pass20 tests.

This proves two-account persisted restore across a fresh own-server/client
restart using an unchanged diagnostic backup. It is not a same-live-server
disconnect/reconnect lifecycle test, nor inventory/gameplay persistence or
production activation. Startup intermittency and those broader gates remain open.

## Same Live Server, Both Accounts Reconnect

--reconnect requires the qualified two-account restored database. After the
first native pair completes, the owner leaves the same server and prepared
client profile running, starts a fresh pair with new run IDs, and uses a separate
reconnect evidence directory/barrier. Borrowed attachment revalidates server
PID generation, listeners, config hash and profile. All owned probe processes
remain in the owner's cleanup list. A bounded second-round deadline is enforced.

native-shared-reconnect-20260921-02 passed. Server PID24300/create_time
1789992946.4235027 remains unchanged across both rounds. First native PIDs are
356/23572; the reconnect pair is17080/14164. All four reports accepted native
mutual visibility at saved18/12 with reset local movement rings. Character IDs
are preserved and the two saved position revisions remain3. Source evidence
hash and SQLite integrity pass. The saved-run regression verifies server
identity/config continuity, fresh client PIDs, both native rounds, no creation
submission and unchanged persisted positions. Targeted suites pass21 tests.

Run01 remains FAILED: native startup/selection stopped before the first mutual
visibility barrier. The successful second run does not resolve that intermittent
prefix failure. This test reconnects BOTH clients while the server stays live;
it does not yet keep one client continuously online while its peer reconnects.
No claim of gameplay persistence beyond the checked character/position scope,
production readiness, rendered-pixel acceptance or complete playable world.

## Intermittent Startup Fault: Narrowed Native Site

The failed native-shared-reconnect-20260921-01-peer1 event270 is a first-chance
access violation at459ED2 reading[EBX+1A0], with nullEBX, after the world
initializer and received2A. This is not evidence of a password/protocol checksum
failure. It is also not proof of an unhandled exception: the diagnostic stops
on the first chance and does not run the client's exception handler.

The pinned original59E70 map metadata binder reads signed count atowner+D2ABA
and table pointer atowner+D2ABC. A nonpositive count branches straight to59ED2,
which dereferences table+1A0 without a null check. Existing build-matched
map-metadata research identifies the table as Map_City_Coordniate (144 rows).
test_current_map_catalog_empty_fault executes these ORIGINAL instructions with
a zero-initialized catalog and reproduces exactly459ED2/read1A0/size4. This
establishes a sufficient failure condition, not the historical live count or
the reason the table was absent. The earlier run did not capture that count.

The observer now records the actual count, table pointer, owner, cursor and
bounded stack when that exact stop recurs. It does not suppress exceptions,
change native return values, inject table rows or claim a repair. Two fresh
four-client reconnect runs native-startup-fault-20260921-01/02 both passed;
the fault did not recur there. Targeted suites pass22 tests. The unresolved
next question is the table loader/binder ordering or failure path in a captured
failing session; shared-file contention remains a hypothesis, not a conclusion.

## Live Catalog Loader Timeline

Shared native probes now add read-only breakpoints at459A80 (loader entry),
its actual return address, and first459E70 bind. They record owner address,
signed count, table pointer and event order. No native return values, rows or
branch decisions are modified. FIRST_BIND is disarmed after its first event.

native-maploader-trace-20260921-01 and02 each passed both native login rounds
on one live server (eight native processes total). Run01's four captured traces
are regression-checked: count0/pointer0 on loader entry, count144/nonzero pointer
on return, then count144 with the identical pointer and owner at first bind.
This establishes a live successful-loader baseline rather than just an offline
expectation. Targeted suites pass23 tests. Neither new run reproduced the fault.

The historical failed run's live catalog count remains unknown; it must not be
retroactively labeled a confirmed empty-load event. Breakpoint timing may also
affect intermittency. Next failure must be compared against this entry/return/
bind trace, with loader I/O failure tracing added if no completed load precedes
the null bind. Repeated passing runs are not a repair or proof of absence.

## One Native Peer Stays Online During Rejoin

--held-reconnect starts a fresh isolated pair, waits for mutual visibility, then
lets peer1 finish while retaining peer0. The owner starts a new native peer1
only after peer0 has observed an empty remote pool and the original peer1
process is terminal. The replacement uses the existing-character selection
route and its own manifest/evidence directory, with unchanged server identity.
Peer0 records reappearance; both sides must cross-bind identities before release.

native-held-rejoin-20260921-01 passed. Retained PID24524 remained the same
through presence, empty-pool departure and reappearance; original peer PID19632
was replaced by a new native process. Peer0's final report is
NATIVE_SHARED_PLAYER_REJOIN_OBSERVED. Its captured S2C lifecycle is exactly
6F,73,6F for the same OTHER identity. Native manager, remote display-pool pointer
and local components remain unchanged. The replacement sees the retained local
identity and does not create a new character. No duplicate remote record remains.
The regression checks lifecycle order, frame hashes/checksums, identity and
process continuity, empty intermediate pool and rebuilt native role. Targeted
suites pass24 tests. All owned processes were cleaned up.

This closes the native one-stays-online rejoin observation gap for this isolated
stationary scene. It does not qualify scene transfers, battle interruption,
load capacity, rendered pixels or full gameplay. The intermittent map-loader
failure remains open with read-only diagnostics in place. Production unchanged.

## Native Remote Status Action Selector

Battle/world integration remains deliberately isolated by Config; do not infer
that successful multiplayer movement enables battle presence transitions.
Targeted current-image inspection of original5E ->FB520 identifies a concrete
status consumer. Body+4 low WORD is compared with actor+60; a change stores
the new WORD atFB598. The subsequent four-component loop starts atFB5A2:
actor+61 bit0x10 (WORD bit0x1000) chooses action7; otherwise it takes the source
byte at actor+251+2*component and shifts right5. FB5B6 pushes component index;
FB5BD calls the original component action setter FFA20. FB5C6..FB5D1 repeats
for indices0..3. This status is distinct from movement state actor+38.

The new instruction-slice regression runs the actual read-only pinned image
FB5A2..FB5BD for all65536 status WORDs with sourceA0, checking the sole bit12
dependency. It separately tests every source byte0..255 and all four component
indices with the bit clear/set (2048 combinations), including exact stack args
and receiver address. All10 remote contract tests pass in1.265s.

Scope: verified native selector arithmetic and call arguments only. Action7 is
NOT yet named battle/idle/death; downstream animation completion and upstream
status authority are unqualified. No fixture values were promoted, no protocol
state restriction was relaxed, and no production runtime configuration changed.
Next native link is the upstream producer/other consumers of WORD bit0x1000,
not speculative removal of remote players when a battle starts.

## Original Remote Status To Named Effect Resource (Corrected)

ERRATUM: the first version incorrectly joined the action selectors to
DTitleGui.ROMZ and named them empty/Fight/Help/Watch/dialogue. That mapping is
WITHDRAWN. DTitleGui binds display pool+10, while the selector consumer reads
pool+18. The resource-backed test exposed the missing pool+18 initialization
with native diagnostic2C70/caller1AF2E (invalid graphics handle). Do not use
the withdrawn names for gameplay or protocol emission.

The next original chain is FD770 ->108980 ->1087B0 ->10ADC0. FD770 passes
the status high byte to the display pool. 1087B0 counts/selects the low five
bits; 10ADC0 indexes the eight-byte table at VA59BAA8. Current table entries
select action ordinals0..4 with mode0. The original1AE20 resolver treats these
small values as ordinals (not ACT_DATA source IDs).

The actual bound source is the independently pinned FieldComm3.csvZ row3 resource
Data3/Flow/StateEft.ROMZ. Original64D32 selects inline offset31C,64D5D loads it,
and64D66 stores the loader return into remote display pool+18. Original64F58
also binds that return into local display pool+18. Parsing
that original resource gives the following one-hot status mapping:

| Status WORD | Action ordinal | Source ACT_DATA name | Source action ID |
| --- | --- | --- | --- |
| 0100 | 0 | seal (original name U+5C01) | 20010 |
| 0200 | 1 | sleep (original name U+7720) | 20011 |
| 0400 | 2 | poison (original name U+6BD2) | 20012 |
| 0800 | 3 | confusion (original name U+4E82) | 20013 |
| 1000 | 4 | stone (original name U+77F3) | 20014 |

The added regression executes original FD770 through the actual display
status setup to the icon-setup entry, then independently executes that setup
to the resource-selection call and checks its real stack arguments. It also
executes the original ordinal resolver and compares the pinned ROM action
names. The setup slice supplies a valid diagnostic render handle explicitly;
it does not claim graphics allocation/rendering. Each one-hot case uses a
fresh emulator to avoid cached translation boundaries from another slice.
All11 remote contract tests pass.

This establishes the native StateEft icon selectors and does not establish a
Fight-labelled icon or general battle-membership flag. It does not establish server authorization,
battle-entry timing, high-bit combinations, or functional battle membership.
No state bit is yet enabled in Application; the ordinary movement guard stays
intact until a real-client state-change/restore lifecycle is qualified.

## Resource-Backed Status Roundtrip

The full native remote-actor harness originally bound only DTitleGui; pool+18
remained -1 and status updates reached native invalid-handle diagnostics. It
now loads the pinned StateEft.ROMZ through original60A90, then executes original
64F58..64F5E using that actual return value to bind its configured local display
pool+18. As elsewhere in this offline harness, the remote manager explicitly
uses that pool; it is not confused with the distinct live remote-pool address.

The complete original5E dispatch now passes status sequence0200,0200,0,0200,0
on one real resource-backed actor. Actor+60 and display-object+2C match each
status; enabled states retain a valid graphics handle and its real selected
action byte1 (StateEft sleep). Names and the neighboring actor record/text are
unchanged. The original6F replacement clears the queued stationary records,
and the existing interpolation, replacement/name, removal and49 component
projection cases still pass. No diagnostic bypass or forced renderer result.

python -m unittest tests.research.test_current_remote_actor_full passes1 full
resource-backed test in165.546s. This is offline native dispatch/resource
acceptance, not live socket/pixel observation, original effect duration or
combat authority. The prior invalid-handle failure is retained as the reason
for the binding correction, not relabeled as a passing run.

## Own-Server Native Sleep Status Lifecycle

The existing default-off CUSTOM-0026 single-actor diagnostic now emits five
phases on accepted ticks1/3/5/7/9:6F spawn,5E status0200 at18/12,5E status0 at
18/12,ordinary5E move19/12,73 removal. Ordinary multiplayer movement and its
state-preservation restrictions are unchanged. No effects, costs, damage,
durations or player saves are implemented by this diagnostic sequence.

The read-only status observer follows the real remote display pool, reads
actor+60, display flags, graphic handle/state/action/resource and the bound
StateEft resource slot. It requires active graphic state2/action1/resource
match for sleep, then state1/flags0 on clear before admitting movement/removal.
Skipped status phases or early movement fail. Historical three-phase saved
evidence remains checked with its original lifecycle gate.

native-remote-status-20260921-01 passed with actual loopback C++ server and
current native client: NATIVE_REMOTE_ACTOR_POOL_LIFECYCLE_OBSERVED, five ordered
samples and no error. Captured S2C opcodes are6F,5E,5E,5E,73 and the three5E
status WORDs are0200,0,0. The regression checks hashes/checksums, actual graphics
resource/action/clear state, completed movement/removal and unchanged empty
position saves with database integrity. Wrong resource/action/graphic state
and skipped status phases are negative cases. Targeted suites pass36 tests.

This is live receiver/resource acceptance, not rendered-pixel inspection or
sleep gameplay semantics. Combat/world membership and production remain open;
no native duration, immunity or recovery rule is inferred from an icon.

## All Five Native Status Icons: Live Set/Clear

The same isolated diagnostic now sends one-hot0100/0200/0400/0800/1000 with
an explicit zero clear after each, then ordinary movement/removal. The sequence
uses ticks1..25; it is a test schedule, NOT an original duration rule. The
packet helper rejects every other nonzero WORD, including combined bits.
Its C++ regression exhausts all65536 inputs and checks admitted state/ID/point.

native-remote-status-all-20260921-01 completed the full thirteen-sample native
lifecycle without error. Each of the five named StateEft selectors is checked
against its actual bound resource and action0..4, active graphic state2, clear
state1 and display flags. Stone1000 also selects component action7 for all four
components; each clear restores the local-source component actions. Completed
movement and final removal follow all ten status transitions.

Captured S2C order is6F,eleven5E,73; status WORDs are0100,0,0200,0,0400,0,
0800,0,1000,0,0. Regression replays all samples through the gate, verifies
packet hashes/checksums and SQLite integrity/empty position saves. The old
sleep-only capture remains independently checked. Python suites pass37 tests;
Release builds and CTest recovered_remote_actor/config/application_startup pass
3/3. No production flags, gameplay effects, durations or combat formulas added.

## Remote Fight/Help/Watch Title: Original Low-Byte Consumer

The current pinned image provides a separate title path, not the StateEft
high-byte path. Original 5E update at FB5EB reads actor+60 and prioritizes
low-byte80, then01, then02. Original 6F insert at FC4B9 prioritizes80,
then02, then01. Thus03 selects Fight on update but Watch on insert. This is
an observed client difference, not permission to assign combined flags.

The three branches call10A510 (80),10A430 (01),10A580 (02); no selected
bit calls10A5F0. The first three original functions pass display pool+10
to1BF30, with action ordinals2,1,3 respectively. Pinned DTitleGui actions
at those ordinals are Help, Fight, Watch. This binding is distinct from
pool+18/StateEft. Each path addresses the existing title graphic from
display slot+0xA4, with graphics-bank stride0x290 and base+0x10.

Reproducible tests in test_current_remote_actor_contract.py execute the
unaltered original branch instructions for all256 low bytes on both insert
and update (512 cases), checking the selected callee and render ID. A separate
original-instruction test follows all three title setters to1BF30 and checks
graphic pointer, actual resource slot, ordinal, mode and pinned resource name.
All13 contract tests pass. The emulator stops before the resource call and
does not substitute a success result or claim fresh live title acceptance.

This establishes a native Fight-labelled display consumer, NOT battle entry
authorization, participant membership, opponent stats or battle formulas.
Next qualify01 ->0 against the live remote title graphic while keeping one
observer in the world; only then connect an independently accepted server
battle lifecycle. Formal visibility/battle mode isolation remains unchanged.

## Fight Title Live Socket Qualification

native-remote-fight-title-20260921-01 completed with
NATIVE_REMOTE_ACTOR_POOL_LIFECYCLE_OBSERVED and no error. The default-off
CUSTOM-0026 diagnostic appends WORD01 and zero after the five StateEft pairs,
then moves and removes actor7. Ticks1..29 are only the lab schedule. The
diagnostic helper now admits01 in addition to the previous six values; its
exhaustive65536-input C++ test still rejects all other values.

Fifteen native samples qualify spawn, twelve status transitions, completed
movement and removal. Fight uses title graphic handle15, active state2,
action1 and resource0 matching the actual DTitleGui slot. Clear retains
handle15/action1 but switches the graphic to state1. StateEft remains cleared;
its separate graphic is not mistaken for the title. No pointer or graphic
memory is written by the observer.

The captured regression verifies ordered6F/thirteen5E/73, exact status WORDs,
packet hashes/checksums, all native observation gates, SQLite integrity and
absence of position saves. Negative cases reject wrong title resource/action,
invalid handle, inactive Fight and uncleared title. The two Python suites
pass36 tests; recovered_remote_actor CTest passes. Server/client/debugger
processes exited after the bounded run.

This is a single native client receiving a diagnostic remote actor, NOT a
two-player battle lifecycle, rendered-pixel inspection or production approval.
The next integration boundary is owned-player battle entry/exit broadcasting
to a retained native observer, preserving accepted movement and persistence.

## Owned Visibility Title Projection

RecoveredVisibility now exposes set_fight_title for an independently authorized
battle lifecycle caller. CUSTOM-0027 checks session/account/character/scene,
rejects nonordinary appearance, source states outside0/1 and positions outside
the5E11-bit range. It derives identity/position from registered presence rather
than caller packet bytes. Same-scene peers receive stationary5E; cached6F gets
the matching status for later arrivals. All delivery allocation precedes
mutation. Repeated state is silent, including alone-in-scene transitions.

Registry tests cover wrong bindings, ID4095, no self/cross-scene sends,
late arrival, unchanged nonstatus spawn bytes, unknown-state preservation on
rejection, coordinate overflow, ordinary movement rejection while cached
state1 differs from its packet, clear-then-move and leave/reconnect reset.
This does not establish that every movement during combat is forbidden: the
existing state-preserving move contract remains intact, including its caller's
responsibility for authoritative movement admission.

The Session transport regression additionally sends set/clear/set through the
real framed outbound queue to the same-scene synthetic TCP peer, verifies
duplicate silence and other-scene silence, then disconnects while marked and
checks73 cleanup. This is transport testing, not fresh native battle acceptance.
Application does not yet call this projection from its battle lifecycle;
production_enabled remains false and custom balance is not promoted.
Release recovered_visibility and session_state CTests both pass (95.45s total).

## Application Battle/Visibility Integration: Synthetic Acceptance

The previous absence of Application wiring is superseded for the explicit
default-off diagnostic_visibility_battle mode only. Config requires recovered
authenticated loopback visibility, player-visibility-diagnostic.db and the
animated/player-appearance/participants/terminal single-round battle fixture.
Other diagnostic modes remain excluded. Character1 alone is the laboratory
combatant; entry waits for at least two registered players. This selection is
CUSTOM-0027 test policy, not native encounter logic or general matchmaking.

Fight is broadcast after RecoveredBattleService::bind succeeds, not when82 is
sent. Clear occurs after release_finished_diagnostic succeeds and movement is
resumed. A finished damage snapshot without its qualified receipt cannot clear
the marker. Disconnect retains existing73 cleanup. Existing CUSTOM-0010/0011
combat numbers and lethal test power are reused only inside this diagnostic;
no formula, XP or production balance is promoted.

test_player_visibility_server.py now drives two authenticated synthetic TCP
clients against the actual Application executable/temporary SQLite database.
It verifies observer ticks do not enter battle,82 alone sends no title,
timer36/binding sends01, initial control and lethal action do not clear early,
terminal receipt emits89 to owner and zero5E to observer, then ordinary
movement succeeds and saves18/12 revision1 before73 disconnect removal.
The initial test incorrectly expected83 for the result; corrected against
RecoveredBattleExperience::opcode89, without changing the server to fit it.
Both Application visibility tests pass; expanded config CTest also passes.

This is real server integration with synthetic peers, not a completed two-native
client E2E battle. Next extend the shared native runner with this explicit
mode and keep the observer alive through actual control/terminal processing.
Production remains disabled; world_accepted is not asserted.

## Two Native Clients: Battle And Retained World Observer

native-shared-battle-20260921-03 returns
TWO_NATIVE_BATTLE_TITLE_LIFECYCLE_OBSERVED. Combatant PID18592 completes original
action generation, damage receipt, zero-award outcome, outcome panel/cleanup
and world-loop reentry. Observer PID22564 remains in the world and samples
actor1 title handle15/resource0/action1/state2, then the same handle/resource
with state1 after clear. Captured observer S2C5E status sequence is exactly1,0.
The run uses two original work-copy clients, actual C++ Application and an
isolated database. No official server or user-operated UI is involved.

--observe-battle is mutually exclusive with the shared movement/reconnect/
departure/restore modes. The owner waits for lab peer0 to create character1
before starting peer1. Borrowed attachments verify the battle manifest agrees
with the running config. The queued original action is held for a bounded20s
until the observer confirms Fight. World reentry waits for observed clear;
this is test synchronization, not a recovered game timing requirement.

Failed run01 is preserved: combatant entered battle before its stationary
mutual-visibility marker, so the old barrier timed out. Run02 is also preserved:
reading the combatant's world pool during battle found clear_mode0, render -1
and blank labels, so it correctly failed the stationary-world gate. The final
runner does not weaken that gate or claim both actors remain rendered during
battle. Instead it validates the combatant's original action/world-return
events and the stationary observer's live remote actor/title. Its result name
is distinct from TWO_NATIVE_PLAYER_POOLS_OBSERVED for that reason.

Captured regression checks both native result classifications, distinct PIDs,
required battle milestones, observer active/clear samples replayed through the
current gate, packet hashes/checksums/identity/WORD sequence, database integrity
and no saved positions. Negative synthetic gate tests reject wrong resource,
action, active state, uncleared title and changed process generation. Combined
remote live/contract/lab-identity Python suites pass40 tests.

This closes the combined diagnostic battle-title lifecycle only. Native
post-battle movement/repopulation, persistent combat, PvP, general encounters,
balanced monster/skill data and full playable-world acceptance remain open.
No production enablement or native-formula claim follows from this run.

## Native Post-Battle World Rebuild And Movement

Application now schedules one current-membership refresh after diagnostic
terminal release. The next accepted standalone InWorld tick sends separate
6F frames to the returning player, then clears the pending flag. Disconnect
also clears it. RecoveredVisibility::refresh checks session/account/character/
scene and builds from current members, including their latest cached status
and positions; it neither mutates membership nor broadcasts to everyone else.
This is explicit CUSTOM-0027 recovery policy, not an official server trace.

Registry tests reject wrong bindings and exclude self/other-scene/departed
players; they retain current status and member count. The real Application
synthetic test verifies only one refresh, followed by movement and save.

native-shared-postbattle-20260921-01 passes with post_battle_movement_observed.
Combatant PID23252 finishes battle, reenters world, reconstructs peer2 with
valid display handle, centered CodexPeer name, four resolved components and
clear_mode1, then executes three original movement steps17/13 ->18/12 ->17/13
->18/12. Observer PID23684 sees the same actor1 finish all steps: idle state0,
empty movement queue, zero remaining displacement and screenY reduced40.
The Fight title stays cleared. SQLite stores exactly character1/area2/scene15/
18/12/revision3 and passes integrity_check.

Captured regression verifies two identical peer2 S2C6F frames to the combatant
(initial and post-battle), observer5E states1,0,0,0,0 with the three movement
coordinates, per-packet hashes/checksums, native result classifications,
repopulation/resource/name evidence, distinct stable PIDs and saved revision.
The combined Python suites pass41 tests; registry CTest and both Application
visibility socket tests pass. No desktop pixels are asserted.

This closes the single diagnostic battle -> world rebuild -> movement/save
path against two current native clients. Persistent battle recovery, repeated
general encounters, PvP, content completeness and balance remain separate
open requirements; world_accepted remains false.

## Combined Native Battle With Durable Settlement

Optional diagnostic_battle_resources is now admitted only within the already
strict visibility-battle fixture (or its previously qualified standalone
modes). No skill seed, nonzero reward, revival, world-resource fixture or
general battle mode is newly admitted. --persist-battle requires shared battle
mode; borrowed attachments check the persistence manifest/config agreement.
Existing Application resource_commit/settle_battle is reused without changing
formulas, transaction semantics or production defaults.

Four real-Application synthetic TCP tests pass: ordinary visibility, transient
battle, durable battle and injected settlement failure. The failure uses a
temporary SQLite BEFORE INSERT battle_settlements trigger: the attack produces
no successful reply, the owner is disconnected, the observer receives73, and
resources remain at their baseline with no XP/settlement rows. It does not send
a successful zero-status clear for a failed settlement.

native-shared-durable-20260921-01 passes with distinct native PIDs21696/24384.
The combatant completes original action/damage/outcome/world return and all
three movement steps; the observer sees Fight set/clear and completed movement.
The resource/ledger database reopens with character1 HP100/max120/MP50/max80,
resource revision2, reservation1 at resource revision1, settlement1 at revision2
and total XP0. All values retain CUSTOM-0012 provenance. Position is18/12,
area2/scene15, revision3. Integrity check passes.

Captured regression repeats the full post-battle native/packet assertions and
opens the resource database twice to check the unique reservation/settlement,
resource revision, zero-award experience and no active checkpoint. Combined
Python suites pass42 tests; configuration CTest and the four Application TCP
tests pass. This is committed settlement persistence, NOT restoration of an
unfinished battle: this basic diagnostic does not persist a battle checkpoint.
No official-stat or production-balance claim follows.
