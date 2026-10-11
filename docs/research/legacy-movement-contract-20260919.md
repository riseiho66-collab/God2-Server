# Saved legacy movement contract, 2026-09-19

Scope: read-only examination of both requested legacy trees. This report is the only output. No current-client disassembly, production edits, UI, builds, or live connections were performed. Current indoor HMD coordinate/passability consumption remains main's independent task. Offsets and lengths are decimal; bytes and opcodes are hexadecimal; hashes are SHA-256 over file bytes or decoded hex bytes, not the hex text.

Final scope boundary from Main: the current indoor raw HMD `4CB26` parser, `37250` object placement, `36C30` 31x31 grid, and cell-by-cell C++ equality are complete; spawn `(17,13)` has raw cell value `1`. These are Main's reported findings, not independently rechecked here. This round remains grid-focused. The movement material below is a retained implementation boundary for a later task, not authorization to integrate movement or reinterpret cell value 1.

## Result

Classic retains concrete 10-byte C2S movement fixtures, a 5-byte decoded S2C acknowledgement fixture, transport code, and TCP loopback/persistence tests. Its implemented contract is `2E, x:u16le, y:u16le, sequence:u8, state:u8`, with S2C `5D, sequence:u8`. Neither packet carries an actor ID or speed. There is also a later parser-only evidence contract that explicitly withholds these field semantics. Treat the implementation and the evidence qualification as separate claims.

**Critical correction:** `0A0080B8D9C14BA69488` is the same saved wire sample in the July JSON and the retained runtime test. The runtime test and retained full world transport produce `0A002E12000C0001FF72`, namely `(18,12), sequence=1, state=FF`. The July JSON's rolling-XOR result `0A00803859F9125F86D7` yields the stale candidates `(4857,34399)`. These are different interpretations of one packet, not two independent movement formats. The full-transport result passes the retained checksum and round-trips exactly. The old interpretation must not establish coordinate scale, direction, or spawn coordinates. This qualifies the `(4857,34399)` statement in the earlier world-entry provenance report; that report was not edited.

XJZ supplies static transport/speed bindings and state/sample schemas, but **no saved movement/ack bytes were found**. Its database's 38 tables having the inspected raw-packet columns all have zero rows. It cannot independently certify Classic's movement semantics or current-client compatibility.

## Roots And Source Keys

- `C` = `C:\God2Evidence\classic-20260820\files\God2-Classic-Server-Formal-Handoff-20260820-020345\ServerSource`
- `E` = `C/src/God2.ClassicServer.Protocol/Evidence/OfficialProtocolCompletion`
- `R` = `C:\Users\risei\Desktop\God2\God2-Server`
- `X` = `R/artifacts/legacy-evidence/xjz-20260820/files/XJZ-Server-Cpp/server_implementation`

Source keys below expand to these exact files; line references are one-based.

| Key | File |
| --- | --- |
| F | `C/src/God2.ClassicServer.Runtime/OfficialClientWorldProtocolFrames.cs` |
| T | `C/tests/God2.ClassicServer.Runtime.Tests/RuntimeFoundationTests.cs` |
| G | `C/tests/God2.ClassicServer.Runtime.Tests/PacketCorpusGapCryptoTests.cs` |
| H | `C/src/God2.ClassicServer.Runtime/RuntimeFoundation.cs` |
| W | `C/src/God2.ClassicServer.Runtime/WorldContentRuntime.cs` |
| P | `C/src/God2.ClassicServer.Runtime/WorldInteractionRuntime.cs` |
| D | `C/src/God2.ClassicServer.Persistence/MariaDbWorldInteractionRepository.cs` |
| L | `C/src/God2.ClassicServer.Protocol/OfficialLiveMovementWorldBatchWire.cs` |
| K | `C/src/God2.ClassicServer.Protocol/OfficialServerSelectionWire.cs` |
| B | `C/tests/God2.ClassicServer.Protocol.Tests/OfficialLiveMovementWorldBatchWireTests.cs` |
| PT | `C/tests/God2.ClassicServer.Runtime.Tests/WorldMovementPersistenceTests.cs` |

## Exact Fixtures

`wire` means encoded bytes; `plain` means complete decoded length-prefixed frame including checksum. Entries explicitly marked derived are calculations using saved code, not additional captures. The July scenario and trace sequence labels identify the source observation; trace sequence 171 is not movement sequence byte 1.

| ID | Direction / origin | Exact wire hex | Exact plain hex | Retained implementation interpretation |
| --- | --- | --- | --- | --- |
| M1 | C2S; saved literal in T:184-197 and E/`world-protocol-recovery-first-batch.json`:44-50, MoveUp, trace sequence 171 | `0A0080B8D9C14BA69488` | `0A002E12000C0001FF72` | x=18, y=12, seq=1, state=FF |
| M2 | C2S; saved wire/plain pair G:12 | `0A0080BAD7C34DA69488` | `0A002E10000E0001FF72` | x=16, y=14, seq=1, state=FF |
| A13 | S2C; saved decoded assertion T:345-350; wire derived here from F:858-865 | `05004DE6BF` | `05005D1365` | seq=0x13 (19 decimal) |
| A19 | S2C; observed decoded literal B:11; wire derived here | `05004DE0B7` | `05005D196B` | parser-only 5D record; byte 3=0x19 |

Action labels alone cannot establish motion direction, displacement, or speed. A13's test is named `matches_captured_server_frame`, but it constructs an ACK and checks decoded hex; no independent encoded ACK assertion or adjacent C2S/ACK capture is retained there. A19 is explicitly evidence-only in the later codec. Do not present these as a captured chronological request/response transcript.

Ready-to-use **synthetic loopback** bytes, expanded from T:1578-1587, T:1719, and builder T:3712-3728:

| Case | C2S wire | C2S plain | Expected S2C wire / plain |
| --- | --- | --- | --- |
| Destination (16,14), seq 1 | `0A0080BAD7C34DA69488` | `0A002E10000E0001FF72` | `05004DF897` / `05005D0153` |
| Forward sequence gap to (18,16), seq 3 | `0A0080B8D9D54FA89682` | `0A002E1200100003FF78` | `05004DF69F` / `05005D0355` |
| Commit (17,12) -> (17,11), seq 1 | `0A0080B9D8C04AA6948A` | `0A002E11000B0001FF70` | `05004DF897` / `05005D0153` |
| Corrupt M1 checksum | `0A0080B8D9C14BA69489` | do not accept | no movement commit/ACK from the dedicated handler; T:305-314 |

### Byte Layout And Transform

Implemented movement decoding: F:706-740. ACK serialization: F:858-865.

| Decoded frame offset | C2S movement (10 bytes) | S2C ACK (5 bytes) |
| --- | --- | --- |
| 0-1 | total length `0A 00`, u16le | total length `05 00`, u16le |
| 2 | opcode `2E` | opcode `5D` |
| 3-4 | x, u16le | byte 3 echoes sequence; byte 4 checksum |
| 5-6 | y, u16le | absent |
| 7 | sequence byte | absent |
| 8 | state byte; implementation requires `FF` | absent |
| 9 | checksum | absent |

F:82-84 retains the world key. Its first eight bytes, sufficient for all 10-byte movement fixtures, are `FD 9F CA C8 42 A8 69 FE`. F:909-947 initializes previous plaintext to `B0`, leaves length bytes unchanged, and processes offsets 2 through the final checksum:

```text
plain[i] = key[(i-2) & 255] XOR ((wire[i] + 3 - previousPlain) & 255)
wire[i]  = ((key[(i-2) & 255] XOR plain[i]) + previousPlain - 3) & 255
previousPlain = plain[i]
checksum = SUM(plain[i] + 0x3C, i=0..length-2) & 255
```

The checksum expression is K:43-56. `DecodeWorldTransportFrame` uses this transform (F:868-872), despite the private helper being named `DecodeWorldServerFrame`. Do not substitute the separate rolling-XOR `DecodeWorldClientFrame` at F:874-884. Replaying the saved algorithms in memory reproduced M1, M2, A13, A19, and the synthetic positive fixtures with exact round trips, declared lengths, and valid checksums. This verifies retained fixture/code consistency, not a current connection's key or rolling state.

### Fixture Hashes

| ID | SHA-256 wire | SHA-256 plain |
| --- | --- | --- |
| M1 | `F3F9FE5A641394307601988B4716135F9B5B1686C7347AAFBC49799633C9F2A2` | `3FD1C6D304DFE88A59AB785F5616E2CACC8E6BE76C36B53EA8C778CEFE939CA7` |
| M2 | `C3F0E1648041B601C12635A79A23B67003E3A844C93D5FC286FB65F0868031DF` | `24DB53B18237BA21C60E27906EB2C0F802CCCB3936F85CCAFAB5104D43830C4D` |
| A13 | `075B43507E5F6EB7A18612808BD3B139E49E46F0CE849E07393697B824CF1EEE` | `BD974E5A2F9D2DCA8D73755796DB4FDF4962612A4F40B71323429027CC98A753` |
| A19 | `D73B4EAA317198BC4FA56C1FA14C7583295741BE35370A1D427E4F94EAB2549B` | `F0D6473EE85E0E85B3ECBBC6A466CBCA1BC8F01872A6C7B389542F10D44236D3` |

M1's wire hash also matches the independent saved `payloadSha256` in E/`world-protocol-recovery-first-batch.json`:50.

## State, Ownership, IDs, Speed, And Coordinates

These are **saved implementation constraints**, not blanket claims about official server behavior:

- **Authority/ownership:** H:1980 requires the connection's `InWorld` role. H:2020-2067 requires a movement store, selected session character, session-to-map binding, a `PlayerObject`, and a Player entity registry entry. Character ID must match the session; both object and registry map IDs must match the bound map. The packet cannot choose another actor or map because it has no such fields. Persistence takes `session.CharacterId`, not a wire-derived ID. Keep database character ID, runtime entity ID, map ID, and sequence in separate domains.
- **ID limits:** C2S has two u16 values but no u16/u32 actor field; byte 7 is implemented as sequence, not entity ID. F:64-66 separately calls the spawn identifier a u32 `CharacterIdCandidate`, while P:869-875 uses a `long CharacterId`. These distinct representations do not prove identity equivalence. ACK has no character/entity ID, success code, speed, or authoritative coordinates.
- **Sequence:** H:2070-2100 accepts the first sequence as baseline. Thereafter `advance=(incoming-last) mod 256`; reject 0 and 128-255, accept 1-127, log forward gaps. Thus 255 -> 0 is forward; an exact duplicate receives no ACK in this handler. This is not a durable idempotency key and does not validate speed.
- **Coordinates:** F:723-728 interprets unsigned x/y but rejects either above `0x7FFF`. H:2102 keeps authoritative Z; there is no transmitted Z. H:2103-2110 can resolve a portal trigger before the inclusive map-bound check at H:2111-2124. H:2127 treats the values as clicked path destination, not a one-cell movement delta. Direction comes from signs of authoritative position deltas (H:2246 onward), with north = negative y and zero displacement retaining facing; T:317-341 covers all eight directions and no movement.
- **Grid scale evidence:** W:60-89 saves `UnitsPerResourceCell=21`, maximum `0x7FFF`, bounds `0..dimension*21-1`, and division by 21 to resource cells. Its source comment attributes this to `God2_opt` RVAs `0x0008E14C` and `0x00064B90`. This is a retained legacy claim only; no current parser/HMD verification occurred here. It must not override main's current indoor findings.
- **Speed/mode:** no elapsed-time, velocity, travel-distance budget, or passability check appears in H:1973-2243. Any accepted destination inside the checked bounds can be committed immediately. F:717 requires `FF` and labels the result `VisualMountedBaseline`; that name is not proof that `FF` is an official mount bit. E/`WorldProtocolRecovery.Phase31.WalkingRecovery.json`:68-70 leaves scale `NOT_FIXED` and speed `BLOCKED_UNTIL_VALID_WALKING_SAMPLE`; failed appearance-field edits are not valid unmount evidence. Do not invent walking/mounted rates from these samples or confuse combat `Speed` with world velocity.
- **Commit/ACK order:** H:2134-2169 persists first and returns without movement ACK on failure/exception. H:2172-2206 then updates object state, entity registry, visibility, connection sequence/count, and interaction synchronization. H:2208-2209 sends ACK last. The database transaction is atomic; the subsequent in-memory updates and socket send are not one cross-system transaction. Portal synchronization failure can still follow a committed movement and ACK, while disabling portal eligibility.
- **Persistence:** P:973-1010 compares expected map and position, atomically replaces the in-memory record, and increments runtime version. D:196-302 locks the nondeleted character row, compares map/x/y, updates position/direction/version/concurrency token under a transaction and guarded WHERE clause, and rolls back conflicts. It has no client-supplied owner ID.
- **Portal special case:** H:1986-2017 consumes a post-portal movement follow-up by advancing sequence/count and taking coordinates from the rebound authoritative player. It returns before ordinary persistence and ACK. H:2221-2234 separately sends movement ACK before a 150 ms delay and synthetic portal activation. These are special legacy flow choices, not a general ACK timing or movement-speed rule.

### Conflicting Evidence Qualification Must Survive Porting

L:72-77,110,123-135 explicitly says parser-only, no movement/spawn/position/despawn/ack mutation. For the same 10-byte `2E` shape it reads:

```text
u16le @3 = CandidateXOrPathField
u16le @5 = CandidateYOrPathField
u16le @7 = CandidateSequenceOrFlags
bytes @4/@6/@8 also preserved separately
SemanticEvidenceStatus = FieldLayoutRecovered_FieldSemanticsEvidenceBlocked
RuntimeMutationAllowed = false
```

For M1, that third WORD is `0xFF01`, not merely sequence 1. The later evidence codec deliberately does not certify the runtime's split into sequence and mounted state. It also lists C2S companion `33` (10 bytes), and `1D/6D/72/30` sidebands (5 bytes), preserving semantics as blocked. Do not manufacture a `33` fixture or infer a movement/ACK pair from timing alone.

The parser-only flag is **not a global runtime safety gate**: H:1056-1067 invokes the dedicated mutating movement handler before generic protocol routing. Consequently this snapshot contains a working legacy implementation alongside a more conservative evidence boundary. Porting tests and byte layouts does not resolve that contradiction or establish current-client semantics.

## Client And Capture Provenance

- F:70-71 names evidence stream `World-ba1f987593024d32be06b5485b16c9ab-server-to-client` and `God2_opt` official world capture, without an executable hash on that fixture.
- E/`world-protocol-recovery-first-batch.json`:2-10 dates the saved recovery to `2026-07-29T20:56:00Z`, links `Artifacts/OfficialClientFirstContact/Golden/20260730-041612` and `Artifacts/ClientInstrumentation/ElevatedAutomationHost/host-run-20260730-045206/world-capture-matrix/world-packet-matrix.json`. M1 retains return RVA `god2_opt.exe+0x0047BB68`; this is provenance text, not a newly inspected instruction address.
- E/`WorldProtocolRecovery.Phase3.Batch1.json`:3-8 references a later prechange run `host-run-20260730-050252`. Its lines 50-51 preserve both the correct encoded M1 bytes and the older decoded candidate. Retained tests T:182-197 and G:16-32 are the stronger transport-consistency evidence.
- L:81-90 binds its August 18 parser evidence to build `god2-opt-6b127086e0c0`, executable SHA `6B127086E0C00014DE26137B4EC482801E06E0724C5C05C64561D7F9FF32BD9B`, and `Artifacts/ClientInstrumentation/OfficialEvidenceLauncher/8cb0c67c-740e-4246-bd4e-810b703e8d87/auto-campaign-20260818-151602/official-live-movement-evidence-manifest-20260818.json`. It cites ground-move sweeps, standalone-2E rollup, and sweep32 summary. These references do not themselves provide those missing original captures.
- `C/protocol/evidence/battle-v1/client-builds.json`:6-16 independently records that build ID/hash, x86, `OfficialClient/God2_opt.exe`, size 2145792, and candidate version `1.0.0.1`; recorded July 31. It does not directly bind the July 30 movement sample to that executable hash. No current executable was inspected or certified by this task.
- `C/PACKAGE-CONTENTS.md`:3-4 explicitly includes source/tests and excludes generated artifacts, runtime output, reports, binaries, and packet captures. The inspected movement evidence consists of saved literals, extracted metadata, and implementation tests. A complete original packet capture establishing request/ACK adjacency was not found in the scoped retained trees.

## XJZ Findings

Search included C++/C# source, Markdown, manifest, and read-only SQLite inspection, rather than treating capture-target descriptions as packet evidence.

- `X/evidence-client-full-manifest-v0.md`:3 identifies source client directory `C:\Users\risei\Desktop\FS2\XJZ`. Its manifest CSV has asset paths, sizes, and `sha1_head`, not a movement capture's executable SHA-256. The SQLite `client_evidence_file` count is 256. This is client-data provenance, not wire-build equivalence with Classic.
- `X/cpp/xjz_evidence_models.hpp`:3228-3243 defines `CharacterProfileState`: int64 character ID, optional int64 account ID, optional int32 map/x/y, JSON stats/appearance/runtime, and `packet_evidence_boundary=true`. At 5392 onward `TeleportFlowSample` contains actor character ID, source/target maps and coordinates, raw-packet JSON, and packet path. These are storage DTOs, not packed wire layouts or enforced ownership checks.
- `X/evidence-transport-binding-v0.md`:25-37 exposes `speed_bonus_x10` among static bindings and explicitly leaves actual riding state, speed application, coordinates, destination, and packet results to official flow samples. `X/evidence-transport-flow-capture-target-v0.md`:53 says static client data cannot prove actual teleport coordinates or the speed formula.
- `X/evidence-account-character-runtime-v0.md`:3,8,28 distinguishes state/sample slots from verified packet formulas and reports empty samples. Read-only queries independently confirmed zero rows in `character_profile_state`, `character_profile_sync_sample`, `teleport_flow_sample`, `official_memory_capture_sample`, and `evidence_reverse_probe_capture_sample`. `X/data` exists but contains zero files.
- Enumerating SQLite base tables found no names containing `movement`, `move_ack`, or `position`. All 38 tables containing any of `raw_packet`, `raw_packet_json`, `request_packet`, `response_packet`, `packet_hex` have zero rows; all matches in this database were `raw_packet_json`. This negative result is bounded to the specified snapshot, not a claim about every historical XJZ capture.

Read-only reproduction of the key absence checks (SQLite URI `file:xjz_evidence.sqlite?mode=ro`):

```sql
SELECT COUNT(*) FROM character_profile_state;        -- 0
SELECT COUNT(*) FROM character_profile_sync_sample;  -- 0
SELECT COUNT(*) FROM teleport_flow_sample;           -- 0
SELECT COUNT(*) FROM official_memory_capture_sample; -- 0
SELECT COUNT(*) FROM evidence_reverse_probe_capture_sample; -- 0
SELECT COUNT(*) FROM client_evidence_file;           -- 256
```

## Loopback Tests Worth Porting

These tests were inspected, not run in this task. Positive bytes above are concrete inputs/expected outputs; additions below are explicitly proposals, not claims of existing coverage.

| Priority | Existing test/source | Port assertion and limit |
| --- | --- | --- |
| 1 | T:182-197; G:16-32; T:303-314,345-350 | Decode M1/M2, verify field boundaries/checksum, exact re-encode; ACK seq 13 -> decoded A13. Reject bad checksum, state 00, coordinate 8000. Add wrong-length/opcode variants with recomputed checksums so failure cause is isolated. |
| 1 | T:1533-1597 | Real loopback login/world handshake and world-entry gate, then synthetic `(16,14,1)` and `(18,16,3)`. Receive sequence-matching 5-byte ACKs; persist final (18,16), SouthEast; accept/log forward gap; do not enforce a one-cell step rule. This checks legacy destination behavior, not current passability. |
| 1 | T:1673-1755 | From (17,12), send synthetic `(17,11,1)`. Assert persistence, player object, direction North, and runtime version=1 agree. Subsequent NPC interaction uses the new distance authority. Replay identical frame: version and position unchanged; existing test checks rejection log, so add a bounded no-extra-ACK assertion. |
| 1 | PT:21,45,67,89; D:196-302 | All eight directions; atomic position/direction/version update; stale expected position and injected persistence failure leave state unchanged. Extend through loopback to assert no success ACK, no object/registry mutation, and no sequence consumption on failure. |
| 1 | H:1980,2020-2088; B:8-41 | Minimal additions for later integration: two-session ownership rejection, sequence wrap/duplicate rejection, and evidence-only A19 causing no mutation. These are boundaries to preserve, not tests implemented this round. |

Main's independently qualified indoor coordinate/passability tests should govern any current map-cell conversion, blocked destination, path traversal, or speed enforcement. This legacy task supplies bytes and authority-order tests; it does not provide evidence for those current gameplay rules.

## Source Hash Ledger

Computed from the inspected files. Every Classic hash in this table was also found in `C/SOURCE-SHA256-MANIFEST.txt`; no source files were changed.

| Source | SHA-256 |
| --- | --- |
| F | `CB65FA7A8873B0D299A1727D4A388072494C2323168669A5DDDAD3DC39311BCA` |
| T | `5079E87A43D35056A23B291A828B459952FAD179527E6A6E3454C95D008574EF` |
| G | `E80020E6359E6F09E13374B247A195DED1AD9103CC55D06B5D36E12D5B4AC9E1` |
| H | `B546C025A02092257249DC4DAC7A9FC66C992867E241D925EA13E02E07166444` |
| W | `0A2BEEA3CD756FE37FD1F2432E468ED311C9B0A91E4234C5B1096B4A5F6636D5` |
| P | `EB74406A3B684C84FE4F5DCD41BDE4C34F901CABB28C8D0E6F4B251398C2E15B` |
| D | `A0009138E74297649FEB7A988779FE4FEC4F01D09720CB450ED25DED0D44C928` |
| L | `116852FD96A7BF286F485AB76B49A6E4482030C922AED02F34A0B05FDB370610` |
| K | `7D388D13BE3620EC1734DD4EEC4BC26666751994AFC0781C48295ED08C9EA2CA` |
| B | `C34DBD812D7EC16BBFF3A6D6EC77CFEA9A70724FD1831AEC790AAE829E5D60DA` |
| PT | `0C193182403E416C37F666A75540FC57480B6E8F91A0FFC37E852BB4553603B3` |
| E/`world-protocol-recovery-first-batch.json` | `C833149D1DBBCCD2C51F99A9289BC36880252338F0867621F33D9E76926FC014` |
| E/`WorldProtocolRecovery.Phase3.Batch1.json` | `B5B170B5D7CAA2DAEA5EAAD18A6C4DCE4AD06A59C067ACDC0AB9F7887C84E13D` |
| E/`WorldProtocolRecovery.Phase31.WalkingRecovery.json` | `7706AA9280622CEF5C5E4BAFB1AB3256904A9E88C77774C60C5909261F6ADB90` |
| C/`protocol/evidence/battle-v1/client-builds.json` | `C77FB404E76ACF5BDF00B4A671D2FFC32EB644DEF666F30B0BBB025F1690A9EE` |
| C/`PACKAGE-CONTENTS.md` | `B17E225C8094CD2F88D9F65D38F48B5ABA72B1A2A47AD0711189F5D196418FA4` |
| X/`xjz_evidence.sqlite` | `44048EE3D664F1418E60EAA267D46E4BA118AA3689FAE03F7350D544A9FC1774` |
| X/`cpp/xjz_evidence_models.hpp` | `5B168CD198EF8016B4BE5B25B33A0DA7C96D5F8911168963A63CF02FCE9CF0F4` |
| X/`evidence-client-full-manifest-v0.md` | `82B3AFB063484CBB499CEF4F2B7C62E2B4CE60F2CD618649812FB14F52D082BB` |
| X/`evidence-client-full-manifest-v0.csv` | `F71ECA9271C1DD3A8C7391CA45E821D99150694C7F2A9E59EEDF55277E1435E6` |
| X/`evidence-transport-binding-v0.md` | `0313ECC1B8EDB0926DFAD60050674814074466D04304910CEBF6F12611E96D28` |
| X/`evidence-account-character-runtime-v0.md` | `0648C1EAAB8770F28537B02AEB0F430A642D830FC690A522CD689F50ACBDE4B1` |
| X/`evidence-transport-flow-capture-target-v0.md` | `58922624678F9D27FD69CB6E80C00EB5BE280F8F97DB72A6F277A77111F13274` |

Verification performed here: retained byte decoding/encoding and checksum calculations, fixture hashes, source hashes against the Classic manifest, targeted source-line review, and read-only XJZ SQLite counts. No .NET suite or live-client compatibility test was run. Only `docs/research/legacy-movement-contract-20260919.md` was created.
