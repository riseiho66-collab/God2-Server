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
3. Carry explicit authoritative channel identity through connection/handoff/
   world ownership. Share account/character storage; isolate presence, actors,
   monsters, encounters, proximity and local broadcasts. Audit per-listener
   shared maps before hosting three worlds. TcpServer already uses the one
   process-global next_connection_identity allocator with exhaustion refusal;
   preserve it rather than adding per-channel counters. SharedWorldPresence
   currently excludes a character only inside its own registry, so three hosts
   require a shared exact character/Session/channel reservation owner as well.
   Share the actual L-issued character-list handoff lineage across all G
   endpoints; retain the full snapshot route key and accepted-local-endpoint
   qualification. Independent empty handoff owners cannot authorize G joins.
4. Connect the actual native switch action to one owned transfer: qualify the
   source, save committed progress, retire old scene/output/pending state as
   actual game rules require, reserve the target, then deliver qualified entry
   and scene. Define failure/reconnect recovery. Preserve exclusive character
   ownership, no copied old callback/lease/ACK and no double publication. Do not
   infer costs, eligibility or battle cancellation rules from labels/ports.
5. After source closure, verify original UI selection for all three channels,
   all six directed cross-channel switches, same-channel action, invalid/full/
   unavailable targets, duplicate ownership attempts, disconnect/retry, save
   continuity, world isolation and late old-channel output. Then conduct current
   original-client own-server acceptance. PHASE1 still prohibits build/tests/
   runtime/game SQL/activation/deployment until the required source closure.

Use C++/Lua, English DB identifiers and Chinese per-table TXT if persistent
channel tables are required. Preserve Taiwan-only scope, saves/features and
the project storage limit.
