# Three-channel native Taiwan delivery plan

Owner requirement: after server selection, offer three channels and switching.
This extends the active Taiwan-only goal. Current production still creates one
character listener and one world context; three-channel gameplay and switching
are not implemented or accepted yet.

1. Bind native selection and switching to actual client group configuration
   with three ordered subgroup slots and full04/05/06 advertisement. Existing
   native table source and current-login-character-socket-topology-20260919.md
   provide bounded evidence. Current-EXE REA in
   research/tw-native-three-channel-selection-20261019.md now proves mask0007
   enables the first three subgroup rows. A mask does not define slot count;
   exactly three real configuration slots remain required. The native group
   picker scans only physical ordinals0..9.07 route keys do not name channels.
   Continue REA for the in-game switch action and its exit/reconnect contract.
2. Publish three distinct bound channel endpoints for that same group/slot
   source. CUSTOM-0159 wire_three_channels preserves supplied opaque bytes and
   existing framing; wire_three_available_channels supplies the proved mask7.
   It is a loopback routing component, not a complete public
   deployment or native list issuer. Keep the one-channel API unchanged. Never
   advertise unhosted ports or alias three labels to one endpoint/world.
   Round487 TaiwanChannelServers now constructs three actual unstarted G
   listeners from complete per-world source facades and exactly three actual
   configuration slots. It publishes only observed bound endpoints (including
   requested port0), installs private accepted-Session/world bindings and
   synchronously closes partial construction on failure. Main/Application has
   not selected this component yet; shared ticket lineage and complete game
   owner/drain lifetimes remain mandatory supplied sources. Existing two Web
   paths also still need selection of the corresponding hosted G endpoint.
   Round488 adds actual stop observations for each listener and all three G
   listeners together. SessionManager removes the exact accepted Session only
   after its GAME cleanup, abandon and application disconnect callbacks finish.
   Accept/retry cancellation and a final GAME marker precede completion. The
   existing Application now waits for both hosted listener observations before
   releasing the network pool work guard, then keeps its original NET/GAME join.
   Callback failure is surfaced after drain; infrastructure abort is distinct
   from completion. This is not a durable save, logout ACK or object-destruction
   receipt and does not select the three-channel owner in Main yet.
   Round489 actual Application now retains its complete mutable gameplay cohort
   in a GAME-owned C++20 suspended frame. The stable coroutine callable and its
   DB/account-hashing host survive that frame. The existing single event loop
   drains before resuming the shutdown tail, with an explicit actual NET-join
   publication checked first. This makes a separately owned cohort possible
   without returning dangling reference captures. It still instantiates only
   one cohort: export sources/tick/retire to the host, build all three cohorts,
   route L issuance by retained selected-channel receipt and compose shared
   handoff/guild invalidation before enabling three listeners in Main.
   Round490 now exports the full final packet/disconnect/authentication,
   account/optional-G source sets and gameplay start/retire/revoke callbacks
   from inside that held frame. Actual G/L/Web construction, routes, signals,
   deadlines and disconnect observation polling run in the process host.
   Borrowed exports unpublish on completion and abort; host-scope retirement
   and GAME transport revocation precede listener destruction. Exactly one
   cohort remains mounted. Next construct three fresh complete Context/source
   frames with the shared custody/L lineage and route actual L receipts.
3. Carry explicit authoritative channel identity through connection/handoff/
   world ownership. Share account/character storage; isolate presence, actors,
   monsters, encounters, proximity and local broadcasts. Audit per-listener
   shared maps before hosting three worlds. TcpServer already uses the one
   process-global next_connection_identity allocator with exhaustion refusal;
   preserve it rather than adding per-channel counters. SharedWorldPresence
   now accepts the shared private SharedChannelCharacterOwnership owner.
   SharedTaiwanChannelWorlds constructs exactly three independent common-world
   containers with that one owner and the same repository/game thread. Pending
   and active characters/Session IDs cannot occupy two of those worlds; actor
   handles remain local. Default standalone hosts still have private owners,
   so Application must explicitly select the one shared three-world collection.
   Share the actual L-issued character-list handoff lineage across all G
   endpoints; retain the full snapshot route key and accepted-local-endpoint
   qualification. Independent empty handoff owners cannot authorize G joins.
4. Connect the actual native switch action to one owned transfer: qualify the
   source, save committed progress, retire old scene/output/pending state as
   actual game rules require, reserve the target, then deliver qualified entry
   and scene. Define failure/reconnect recovery. Preserve exclusive character
   ownership, no copied old callback/lease/ACK and no double publication. Do not
   infer costs, eligibility or battle cancellation rules from labels/ports.
   Round486 current-client REA proves the settings character-logout flow:
   world result2 -> login mode1 -> C2S02/reason1 -> wait S2C03 -> reauthenticate
   and select group/subgroup again. This is a supported native route toward
   switching, not an in-place transfer opcode. Existing immediate03 queue and
   close are not durable-save/cleanup completion receipts. The actual handoff
   owner must keep source custody until those required operations complete.
   Round487 traced483B00/483BB0/507BB0 as a bounded local widget-dismiss path,
   not a recovered target-channel action. Only482305 tests the result for-26;
   4829CF ignores it. Continue at state2 block46597E and the widget's actual
   creation/opening source rather than assigning it a guessed switch opcode.
   Round488 now follows state2 at46597E through481590/4158B0 to return6;
   40DE80 maps return6 to415730(2,2,1), sending G02/reason2 and waiting03.
   This case does not set login mode1 as the separate return2 path does.
   UI+232DE4 creation/name remains open; do not name it a channel action.
   Round489483BD0 now proves the WORD widget-handle write at483C10.483B40
   accepts encoded message text through476570;483A80/483AB0 open encoded/direct
   text with DWORD232F68=1.4820A0 uses that flag to make dismissal request world
   exit. This is a shared message widget with exit-required mode, not evidence
   of channel selection. Qualify469294/465DC5/46B5BD/501FA6 actual containing
   functions and message inputs next; numeric19000 is not named a resource ID.
   Round490 qualifies468AE0 inbound dispatch and original46B5D4[20] ->46928A:
   it passes packet+0D encoded text to483A80, requesting exit after dismissal.
   The receive-state-3 branch also supplies text resourceED to483AB0 when
   world+AA25ED4 is zero. These are inbound/error-message origins, not a player
   channel selector.465DC5/501FA6 roots and actual resourceED text remain open.
5. After source closure, verify original UI selection for all three channels,
   all six directed cross-channel switches, same-channel action, invalid/full/
   unavailable targets, duplicate ownership attempts, disconnect/retry, save
   continuity, world isolation and late old-channel output. Then conduct current
   original-client own-server acceptance. PHASE1 still prohibits build/tests/
   runtime/game SQL/activation/deployment until the required source closure.

Use C++/Lua, English DB identifiers and Chinese per-table TXT if persistent
channel tables are required. Preserve Taiwan-only scope, saves/features and
the project storage limit.
