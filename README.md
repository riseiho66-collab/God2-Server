# 封神2仙界傳 Server

目前只開發台服原生 PC 與其網頁入口 `/tw/native`、`/tw/native-game`。台服繁簡顯示與存檔保留；目前仍為來源整合階段，尚未完成全遊戲驗收。最新範圍見 [AGENTS.md](AGENTS.md)。

**服務端主要使用 C++20＋Lua 5.4，資料儲存使用 SQLite。**
C++ 負責網路、狀態、資料儲存與遊戲整合；Lua 負責既有架構中的遊戲規則。
`tools/` 與 `tests/research/` 內的 Python 是離線逆向、研究、測試與維運工具，
不屬於服務端執行核心，正式服務端啟動不需要 Python。

GitHub 語言占比透過 `.gitattributes` 排除離線工具與研究目錄，呈現服務端實作語言。
這些工具仍保留原始語言與可讀原始碼；語言統計調整不代表歷史腳本已經清理完成。

Private source repository: [riseiho66-collab/God2-Server](https://github.com/riseiho66-collab/God2-Server).
Push notifications and local-only exclusions: [GitHub / Discord updates](docs/GITHUB_DISCORD_UPDATES.md).
Current owner scope and phase restrictions are maintained in [AGENTS.md](AGENTS.md);
the older status sections below remain historical research records.

An independent C++20 + Lua + SQLite-first server framework for authorized GOD2 compatibility research and private testing. The server implements a mock gameplay path while the real client protocol is recovered. It does not reuse TSN/TSM protocol assumptions or claim official source recovery.

## Native-First Data Policy (2026-09-20)

Owner update: use verified original data/rules where available; when unavailable,
implement documented custom designs. This supersedes the original-only blocker
policy. See [provenance rules](docs/IMPLEMENTATION_PROVENANCE.md) and the
[searchable custom design index](docs/custom-designs.json). Custom code/data
must carry stable CUSTOM-NNNN IDs and must never be presented as native.

Existing test fixtures are not automatically production gameplay. Preserve
C++20/Lua ownership, accounts/saves, build-specific protocol validation and
own-server acceptance. Retired legacy corpora remain retired.

### Historical Original-Only Policy (Superseded)

The [active goal acceptance contract](docs/GOAL_ACCEPTANCE.md) includes the
owner's original-only requirement. Missing original evidence leaves an item
open; it is not a completed substitute implementation.

All gameplay data, attributes, growth/EXP tables and formulas require current
original-client evidence. Unknown values must not become guessed defaults.
Bundled mock content is fixture-only, not original gameplay. Previously supplied
XJZ/Classic server corpora are retired and must not be read or imported; their
authorized deletion was blocked by the tool before execution, not completed.
See [source policy](docs/research/content-recovery-20260919.md) and
[retirement record](docs/research/legacy-data-retirement-20260919.md).
The dated sections below include historical framework status, not a current
claim of original-client playability.

## Current Status

The next reconstruction gate now has an executable [artifact vault](tools/research/README.md)
with content hashes, PE metadata, provenance, verification and static comparisons.
See [ordered gate status](docs/RECONSTRUCTION_STATUS.md); this does not imply verified unpacking.

[APEX runtime intake](tools/research/RUNTIME_CAPTURE.md) now supports controlled
capture preparation, sealing, integrity checks, event indexing, Gate 02-05
consistency assessment and generated reports. It is an offline adapter, not a
live debugger. Acceptance remains L1; Gate 02 is BLOCKED on external runtime evidence.

[ZENITH local review](tools/research/GATE_REVIEW.md) adds content-addressed
review/certificate records, explicit promotion and cascading revocation. No trusted
reviewer policy or real certificate has been created. Broader ZENITH interfaces
are [reserved, not implemented](docs/ZENITH_ARCHITECTURE.md).

The server includes TCP sessions, bounded packet framing, state-aware dispatch, mock login, repository-backed character list/selection, world entry, persisted movement, map chat, Lua NPC dialogue, heartbeat, script reload and an offline protocol replay tool. UDP, AOI filtering (interface only), battle mechanics, inventory/shop wire contracts, real authentication, MySQL/MariaDB and database export are deferred. Recovered-client compatibility remains unverified.

> PLACEHOLDER - waiting for real GOD2 reverse engineering result

The codec is little-endian uint16 total length (including the four-byte header), uint16 opcode, then payload. All fixture opcodes are NOT verified GOD2 opcodes. Mock success is not real-client compatibility.

Phase 0 has static PE/header/import evidence for two distinct executables. Both retain ASPack-like structure; neither is a verified unpacked artifact. OEP candidate 0x0054A3E8 is unverified for the original client. No unpacked dump, repaired IAT or real packet schema is available. See [client evidence](docs/CLIENT_REVERSE_NOTES.md) and [sibling comparison](reverse/findings/sibling_executable.md).

## Build

Use CMake 3.24+, a C++20 compiler and a build tool supported by CMake. Windows is the primary platform. Dependencies are downloaded through FetchContent with SHA256 checks: standalone Asio 1.30.2, spdlog 1.14.1, nlohmann/json 3.11.3, sol2 3.3.1, Lua 5.4.8 and SQLite 3.50.4. Initial configuration requires access to the archive hosts.

From the project root:

~~~powershell
cmake -S . -B build
cmake --build build --config Debug
ctest --test-dir build -C Debug --output-on-failure
~~~

CMake builds god2_core, god2-server and protocol-replay. There is no CMakePresets.json. For single-configuration generators, select a configuration at configure time if needed, for example -DCMAKE_BUILD_TYPE=Debug.

## Run

For a multi-configuration Windows build:

~~~powershell
.\build\Debug\god2-server.exe
.\build\Debug\god2-server.exe --config config/server.json --run-for 5
.\build\Debug\protocol-replay.exe "04 00 00 10"
~~~

Debug and Release executables are built in this workspace. For normal local use,
run `.\build\Release\god2-server.exe`; rebuild it with
`cmake --build build --config Release --parallel 4` after source changes.

For a single-configuration build use build/god2-server.exe and build/protocol-replay.exe; on non-Windows platforms omit .exe. The default config is config/server.json, so launch from the project root or supply --config PATH. Paths inside the config resolve from the config file's parent directory's parent, which is the project root in the standard layout.

Default endpoint is 127.0.0.1:7000, with development.mock_login=true. Mock authentication is blocked on non-loopback bind addresses. Setting mock_login=false does not enable real authentication: login is then unsupported.

Default database is god2.db, log file logs/server.log, script root scripts, and bootstrap scripts/bootstrap.lua. The bootstrap loads NPC, quest, monster AI, event and GM examples. --run-for N stops the server after N seconds; omit it for normal operation. SIGINT/SIGTERM also request shutdown.

Replay accepts positional hex, --file PATH containing hex text, or stdin, and reports frame length, opcode, payload and parse errors. The example decodes an empty synthetic handshake frame; it neither connects to a server nor proves the client sends that frame.

## Mock Gameplay

Empty login payload selects username mock. A nonempty login contains exactly three strings: username, password, client_version. Strings have uint16 little-endian UTF-8 byte lengths. Malformed fields are rejected; any field-valid username is accepted without credential verification. The password is discarded and new accounts store !MOCK-NOT-A-PASSWORD-HASH!, explicitly not a password hash.

SQLite generates account and character IDs; do not assume account 1 or character 10001. A new account gets a default TestPlayer character. List/select replies supply the IDs needed for subsequent requests. World entry sends player data and broadcasts PlayerSpawn. Movement saves through CharacterRepository before updating position and broadcasting. [PACKET_FORMAT](docs/PACKET_FORMAT.md) gives exact field order and sizes; [OPCODE_TABLE](docs/OPCODE_TABLE.md) lists fixture values.

Normal packet payload logging is controlled by protocol.packet_dump; login payloads are redacted. Unknown-opcode warnings independently include up to 256 payload bytes even when packet_dump is false.

## Layers And Layout

| Layer | Paths | Responsibility |
| --- | --- | --- |
| C++20 core | src/core, src/net, src/protocol, src/handlers, src/game | Configuration, network I/O, session ownership, codec, state validation and world state |
| Lua content | src/scripting, scripts | NPC dialogue, quest/AI/event/GM callback registration and protected invocation |
| Database | src/db | Backend interfaces, SQLite repositories and transactional migrations |
| Protocol research | docs, reverse, src/tools, tools/protocol_lab | Artifact evidence, contract registry, fixtures and offline replay |
| Verification | tests | Packet, state, replay, Lua, persistence and integration checks |

Networking runs on an Asio worker pool with a strand per session. Handlers, world mutation, Lua and synchronous repository operations run on one serial game executor. This avoids SQLite work inside socket callbacks but does not make database operations asynchronous; slow DB work can stall the game executor.

Lua receives copied game data and narrow content APIs, not sockets, raw packet buffers, Session memory, crypto controls or database handles. SQLite details remain in src/db. See [architecture](docs/SERVER_ARCHITECTURE.md) and [database strategy](docs/DATABASE_STRATEGY.md).

## Phase 0 Research

Follow [EXE_RESTORE_PLAN](docs/EXE_RESTORE_PLAN.md) and [REVERSE_ENGINEERING_PLAN](docs/REVERSE_ENGINEERING_PLAN.md): preserve/hash the original, validate an unpack transition, dump a separate analysis image, reconstruct imports, then trace network callers, framing, transforms, dispatch and payloads. Dynamic restoration and IAT repair remain pending. Every recovered address/schema must cite its executable hash and evidence.

## Extend The Server

- **Real protocol:** replace confirmed framing/transforms in ProtocolSpec and its pipelines, then map recovered wire opcodes and payloads into internal handler schemas and map replies back out. Updating only four framing/transform files is insufficient. Gate real mode on [specification acceptance](docs/GOD2_PROTOCOL_SPEC.md).
- **Opcode:** document direction/state/schema and whether it is fixture or recovered; add the enum/mapping, dispatch registration and state checks, then positive/malformed/wrong-state tests.
- **Handler:** validate state and all fields before mutation; use repositories/domain services; consume the complete payload; register through RegisterHandlers. Unknown opcodes and rejected requests produce string-based mock errors.
- **Lua NPC/quest/AI:** add a script under scripts/npc, quests or monsters; register a unique content ID and callbacks; require it from bootstrap. Player IDs are copied into Lua as decimal strings. NPC dialogue tables are validated and serialized to JSON.
- **Migration:** append the next consecutive migration in src/db/Migration.cpp. Applied migration names and SQL text are immutable and checked at startup. Test fresh creation, upgrade and failure rollback.

Lua hot reload checks script timestamps every two seconds. A replacement VM is staged and retained only on success; failed reload leaves the previous VM active. Registration of quest/AI/GM callbacks does not imply complete gameplay or a network administration interface.

## SQLite First

Only accounts and characters have initial gameplay tables. Repositories hide backend handles/SQL, and migrations record applied schema versions. Inventory/quest/battle schemas await recovered requirements. MySQL/MariaDB and SQLite export remain explicit future work, not working alternatives selected by configuration.

## Roadmap

| Phase | Deliverable |
| --- | --- |
| 0 | Restored analysis image, repaired imports and evidence-backed protocol contract |
| 1 | Placeholder server skeleton and measured verification |
| 2 | Real packet header |
| 3 | Handshake |
| 4 | Login |
| 5 | Character list |
| 6 | Character selection |
| 7 | Enter world |
| 8 | Movement |
| 9 | Chat |
| 10 | NPC / quest |
| 11 | Inventory / shop |
| 12 | Battle |
| 13 | Expanded persistence |
| 14 | MySQL/MariaDB and SQLite export |
| 15 | Administration tools |
| 16 | Stability and scaling |

## Verification

Both Debug and Release C++ builds succeeded with 11 baseline CTest cases passing. After adding the artifact vault, the Release test run passes 12/12, including 17 Python research checks. Coverage includes actual loopback multiplayer sessions, fragmented/coalesced packets, selection-race recovery, world snapshots, persistence, Lua failures and reload rollback, application startup and clean shutdown. Exact commands, results and limitations are recorded in [docs/VERIFICATION.md](docs/VERIFICATION.md). These mock results do not establish real GOD2 compatibility.
