# Server Architecture

The server separates transport, game execution, Lua content, persistence and protocol research. The current wire mode is explicitly placeholder; real GOD2 decoding, authentication and battle mechanics are not implemented.

## Four Layers

| Layer | Owns | Boundary |
| --- | --- | --- |
| C++20 core | Sessions, buffers, codec, dispatch, domain state and scheduling | No game-content logic in main |
| Lua content | NPC dialogue and quest/AI/event/GM callbacks | No sockets, raw buffers, Session pointers, crypto or direct DB |
| Database | Backend abstraction, repositories, migrations | SQL and sqlite3 handles stay in src/db |
| Protocol research | Artifact-bound findings, schemas and replay fixtures | Hypotheses are never promoted as real opcodes |

main parses --config and --run-for, loads configuration and initializes logging. Application starts network workers and a dedicated game thread. The game thread opens SQLite, applies migrations, initializes Lua/bootstrap and world, registers handlers, constructs the listener and starts scheduling. A required initialization failure propagates to startup rather than accepting a partial service.

## Execution And Ownership

The network io_context runs on the configured worker pool. Every Session has a strand owning its socket operations, codec/input accumulator, timers and ordered output queue. Complete packets are posted as a batch to the single game io_context. A session permits only one outstanding game batch and resumes reads after acknowledgment, providing per-session ordering and backpressure.

The serial game executor owns handler dispatch, World/Map mutations, Lua access and repository calls. SQLite operations are synchronous on this executor. They do not block socket callbacks, but a slow query or busy wait can delay all game actions. Moving DB work to a bounded dedicated executor is future scaling work, and would require rechecking session/state before applying results.

Shared session lifetimes and executor work guards span network-to-game handoffs. Output buffers remain owned through asynchronous write completion. Disconnect callbacks remove world membership on the game executor. Shutdown stops scheduler/admission, requests session close, drains work and joins threads. The network context is destroyed before the game context so retained network handlers release game executor guards while their context is still alive.

## Packet Path And Limits

TCP bytes -> session Buffer -> God2ProtocolSpec decode -> complete Packet batch -> game executor -> OpcodeDispatcher -> handler -> repository/Lua/world -> Packet -> session strand -> encode -> ordered async_write.

The placeholder header is LE uint16 total frame length plus LE uint16 opcode. Complete frame size is 4..65535 bytes. The codec handles partial and coalesced input. Session protections include a 1 MiB input/queued-byte budget, 256 outstanding send reservations, 4096 decoded packets per batch, a 120-second idle timer and a five-second close-drain timer. These are implementation limits, not recovered GOD2 rules.

PacketReader checks numeric/string/byte bounds; PacketWriter writes explicit endian bytes. String prefixes count bytes. Handlers reject extra payload bytes. Packet format, examples and exact mock payloads are in [PACKET_FORMAT](PACKET_FORMAT.md).

## State And Gameplay

Handshake accepts Connected; login accepts Connected/Handshaked; character list/select require Authenticated; enter-world requires CharacterSelected; movement/chat/NPC require InWorld; battle action requires InBattle. Heartbeat accepts every non-disconnected state.

Mock login accepts an empty payload or validated username/password/version strings. It discards passwords, creates marker-backed accounts and a default character when needed, and uses SQLite-generated IDs. Character selection checks ownership and rejects online characters while retaining Authenticated state. If another session enters the selected character first, EnterWorld resets Authenticated/character_id=0 and returns an error. Successful entry sends S2C_EnterWorld, broadcasts the newcomer's spawn to everyone including self, then sends the newcomer existing-player snapshots with the same schema. Movement validates mock bounds, persists through the repository, then updates/broadcasts. Chat broadcasts to the map; NPC talk calls Lua and returns validated JSON dialogue.

BattleAction returns an explicit unimplemented error when reached. UDP transport, AOI filtering (interface only), battle mechanics, real authentication and recovered-client compatibility are deferred. World/map/entity and callback scaffolding do not provide complete combat, AI scheduling, quest persistence or inventory/shop. No public wire flow currently establishes full battle gameplay.

## Errors And Logging

Unknown opcodes log session/opcode/payload size and up to 256 payload bytes, then send a string S2C_Error. Invalid states warn and send an error without calling the handler. Caught handler exceptions become Request rejected. Duplicate handler registration is rejected.

protocol.packet_dump controls normal session packet payload logging; C2S login payloads are redacted. Unknown-opcode diagnostics bypass that flag and still include the first 256 bytes. Configuration selects log level/file. Parse failures close the affected session; they do not reinterpret bytes using guessed resynchronization.

## Lua

LuaEngine runs on its initialization/game thread, uses protected calls and an instruction budget, and limits script loading to the script root. Callbacks receive copied records rather than mutable native Session memory. NPC responses are validated before JSON serialization. Player IDs are strings to preserve uint64 precision across Lua numeric configurations.

scripts/bootstrap.lua loads sample NPC, quest, monster AI, event and GM scripts. The 50 ms world scheduler checks script timestamps every 40 ticks when hot_reload is enabled. Reload builds a replacement VM and registrations, committing only on success; errors preserve the previous VM. GM callback registration is not a network-accessible administration service.

## Persistence

SqliteDatabase owns the connection and repositories. It uses a 5000 ms busy timeout and verifies foreign-key enforcement. Migrations run transactionally, store version/name/SQL text and reject changed history or a newer database. Foreign-key and quick integrity checks run before commit. Repository access requires migration completion.

accounts and characters are implemented; character position is persisted by movement. MySQL/MariaDB and export remain unsupported placeholders. See [DATABASE_STRATEGY](DATABASE_STRATEGY.md) for extension and portability decisions.

## Real Protocol Integration

ProtocolSpec isolates framing/encoding and session lifecycle hooks; crypto/compression pipelines are disabled for mock mode. Real framing, transforms, sequence rules and opcodes must come from evidence. Wire payloads also need adapters into the internal handler schema and back into client-expected responses. Editing only God2ProtocolSpec, PacketHeader and two transform files is not a complete compatibility strategy.

## Verification

See [VERIFICATION.md](VERIFICATION.md) for measured build/test/runtime results. Source behavior described here is separate from verified real-client compatibility, which remains blocked by incomplete unpack/IAT and protocol recovery.
