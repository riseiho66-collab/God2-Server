# Current protocol coverage gap audit, 2026-09-19

Owner requirement: **all original packets must be implemented and connected to
the formal server**. That requirement is **not complete**. This bounded sidecar
provides a reproducible native receive-size census and 19 selected current
contract/route findings. The audit itself implements no runtime packet route or
original game rule. A subsequent main change added typed Session transport for
25/85/86 and reaudited this report; Application gameplay authority is still absent.
Counts below are not a percentage of all original packets.

Latest addition: S2C86 discriminator3 is a lossless `CODEC_ONLY` contract,
distinct from the five-byte C2S86 dialogue-close transport. Current status
counts are10 codec-only,1 native-only,5 transport routes and3 runtime routes.
All selected live-client acceptance statuses remain UNKNOWN. See
[result flags codec](recovered-battle-result-flags-20260919.md).
The fourth transport route is C2S35/action1 basic attack, gated by InBattle on
the game executor; Application battle policy remains absent. See
[battle transport](recovered-battle-transport-20260919.md).
The fifth transport route is distinct C2S35/action0B control input, with the
same conservative InBattle gate and no inferred acknowledgement/turn semantics.

Only new files owned by this audit:

- `tools/strike_lab/current_protocol_coverage.py`
- `tests/research/test_current_protocol_coverage.py`
- `docs/research/current-protocol-coverage-20260919.md`

No CMake, shared runtime, main, worldhost, existing tests or helpers were edited.
No descendants, external evidence corpus, client launch, sockets or deployment.
Historical snapshot bytes and fixture handler names are not protocol authority.

## Reproduce

From `C:/Users/risei/Desktop/God2/God2-Server`:

```powershell
python -B tools/strike_lab/current_protocol_coverage.py --json
python -B tests/research/test_current_protocol_coverage.py -v
```

The tool prints JSON only. It does not write generated artifacts. It uses the
existing local Unicorn dependency under `artifacts/tooling/crypto-oracle-python`.
The JSON contains every query result, table offset, executed leaf, instruction
trace, native span hash, selected producer argument bytes, formal file hash,
source line anchor, route gap and next integration point.

Authority is the current mapped image
`artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin`,
SHA-256 `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
Base is `400000`; all native locations below are hexadecimal RVAs/file offsets.
The full image hash is required before execution. No native code is patched.

## Complete Length Census

`134C8` calls `15840`, which calls `1000`, which calls `1200`.
`1004` masks its argument to one byte. `1204` compares against `FD`; `120F`
jumps through DWORD table `1324`. Thus there are **254 actual table entries**
(`00..FD`), not 256; `FE/FF` execute the out-of-range leaf `131E`.

| Domain | Count | Actual native result |
| --- | ---: | --- |
| Fixed receive contracts | 230 | Positive total logical record size, including opcode |
| Variable receive contracts | 22 | `-2`, leaf `1318` |
| Unsupported receive values | 4 | `-1`; table entries `21/25`, plus out-of-range `FE/FF` |
| All queried byte values | 256 | Every value executed through the complete query chain |

Variable opcodes: `19 20 5C 63 65 7A 98 A2 A7 AB AF B0 B5 BE CC D8 DC DD EE F3 FC FD`.
Every fixed value and its leaf is present in `native_catalog.rows`; unknown
packet semantics remain `NOT_ASSESSED`, even when the length is known.

The variable receive path reads three header bytes, then `13521` reads a
little-endian WORD at logical offset 1 as the **total** logical length.
`13558` compares the buffered count with that length. Bounded native probes
starting at `1351F` with exactly three synthetic header bytes show:

- `0,1,2,3`: buffered-count-satisfied branch at `135C9`. This is not validation
  of malformed short records or evidence of whole-client acceptance.
- `27,2559`: needs-body-byte boundary `13560`.
- `2560`: limit branch `1359A`; `2561,65535`: assertion boundary `13534`.

Assertion handling, socket reception and later processing are not executed.
The length census uses RX image pages, bounded stack/table reads, stack-only
writes, at most 64 instructions and a 100 ms budget per invocation. Tests also
exercise all 256 opcodes with both `000001xx` and `FFFFFFxx` query arguments.

## Direction And State

The receive classification comes from `134C8` and the world acquisition chain:
`68B24 -> 13420`, `68B47 -> 13650`, then opcode read `68B50` and table jump
`68B61 -> [6B5D4 + opcode*4]`. It is not inferred from filenames.

Battle has another consumer: `114315..11432D` queries `15840` and copies from
its battle buffer; `114332..114351` maps opcode minus `1C` through byte table
`11465C` and jump table `114634`. `38`, `87`, and `89` all hit the world default
`6B517`, but have battle cases `114525`, `114518`, and `114582`. A world default
does not mean the opcode lacks a client consumer. Full battle-buffer transport
handoff is outside the executed census.

| Logical opcode | Receive query | Independently anchored C2S producer |
| --- | ---: | --- |
| `85` | 2 | `97DC0`, arguments at `97DE7`, queue call `97DF3`: 1 + 6 = 7 bytes |
| `25` | unsupported | `96350`, arguments at `96372`, queue call `9637B`: 1 + 4 = 5 |
| `35` | 4 | `118E50`, arguments at `1191DB`, queue call `1191E0`: 1 + 16 = 17 |
| `2E` | 5 | `15790`, arguments at `157AF`, queue call `157B8`: 1 + 6 = 7 |
| `30` | 19 | `11750`, arguments at `11764`, queue call `11770`: 1 + 1 = 2 |

All these producers call original queue append `132E0`: opcode stored at
`13320`, payload copied at `13338/13340`, count updated at `1334C`.
Argument signatures and relative calls are checked against the pinned image.
The audit executes the existing `current_quest_action` bounded producer through
the native queue: synthetic mode-1/page state produces `85 34 12 02 00 9A A5`,
seven queued bytes, stopping before close handling at `C8350`. `A5` is poisoned
untouched stack storage, not a recovered field/default. Other producer rows
are static pinned argument/call evidence in this audit, not new full executions.

`C2S0002` is an outer capture-stage/frame label, **not logical opcode `02`**.
`RecoveredC2S0002::parse` checks a 176-byte frame, decodes a 173-byte logical
buffer and permits expected logical opcode `04` or `00`. Independent receive
query `02` returns 23. This audit claims no C2S02 producer from the outer label.

## Formal Route Findings

Statuses have deliberately different meanings:

- `CODEC_ONLY`: offline codec or model, without a qualified formal runtime route.
- `TRANSPORT_ROUTE`: typed Session parsing and an optional game-thread callback
  exist, but no authoritative Application handler is installed. Structural
  socket tests do not establish the corresponding original gameplay operation.
- `RUNTIME_ROUTE`: inspected conditional source path from framing/state gate to
  callback/emitter. Does not mean enabled in a running server or client accepted.
- `CLIENT_ACCEPTED`: requires a matching live current-client transaction through
  the formal route. None is claimed here. Native probes cannot earn this status.
- `NATIVE_ONLY`: current native contract, without a separately identified codec
  or qualified formal route. A synthetic fixture is not a production codec.

Selected findings: **10 CODEC_ONLY, 1 NATIVE_ONLY, 5 TRANSPORT_ROUTE,
3 RUNTIME_ROUTE**.
All 19 have client acceptance `UNKNOWN`. These are selected findings, not an
inventory of every login, character, initialization or world-entry route.

| Direction/state | Contract and native anchor | Formal status / unresolved work |
| --- | --- | --- |
| S2C Battle | `86`, 17 bytes, discriminator3; `114464 -> 117480 -> 12C3E0` | CODEC_ONLY: RecoveredBattleResultFlags; field normalization and lossless bytes, no runtime emitter or battle authority |
| S2C World | `72`, 21 bytes; `6A68B`, `6AA89 -> CC380` | CODEC_ONLY: RecoveredNpcRecord/RecoveredNpcSpawn have no inspected runtime call site; establish scene-owned placement/selector/opaque fields |
| S2C World | `DB`, 13 bytes; `6B44E -> 854F0 -> C9670` | CODEC_ONLY: RecoveredQuestSync, subtypes 4/5; authoritative journal values, quest transitions, rewards and persistence unknown |
| S2C World | `3B`, 25 bytes; `6A029 -> 98DD0`, store `98E2B` | CODEC_ONLY: RecoveredInstanceUpdate; opaque instance construction/ownership unknown |
| S2C World | `41`, 5 bytes; `6A04D -> 991E0` | CODEC_ONLY: RecoveredInventory; visible projection is not inventory authority |
| S2C Battle | `89`, 57 bytes; `114582`, gated call `11459A -> 118BF0` | CODEC_ONLY: RecoveredBattleExperience; display fields are not award formulas |
| S2C Battle | `38`, 2 bytes; `114525 -> 117560 -> 11C7F0` | CODEC_ONLY: current_skill_selection model; server producer, state authority and timing unknown |
| S2C Battle | `87`, 3 bytes; `114518 -> 117540 -> 11C520` | CODEC_ONLY: following-WORD helper in RecoveredSkillCommand; no emitter/learning authority |
| S2C World | `31`, 29 bytes; `69FA9 -> AA200` | CODEC_ONLY: current_progression_source bounded model; actor/scalar construction and progression rules unknown |
| C2S UI/World | `25`, 5 bytes; producer above | TRANSPORT_ROUTE: RecoveredWorldRecords -> optional Session world_records callback; no Application item operation/ownership handler |
| C2S Battle | `35`, 17 bytes, action 1 | TRANSPORT_ROUTE: typed Session callback after InBattle gate; Application battle creation, turn/target rules and results missing |
| C2S Battle | `35`, 17 bytes, action 0B | TRANSPORT_ROUTE: distinct ControlRequest after InBattle gate; no Application control/turn policy |
| C2S Battle | `35`, 17-byte records, kind 0 action 03/83 | CODEC_ONLY: RecoveredSkillCommand sequence subset; costs, eligibility and effects missing |
| S2C World | `7A`, variable; `6ABD7 -> C7F10` | NATIVE_ONLY: mode-1 header slice; current_quest_action.fixture is decoded synthetic input, not a wire emitter |
| C2S quest UI | `85`, 7 bytes; `C8500 -> 97DC0 -> 132E0` | TRANSPORT_ROUTE: RecoveredQuestAction -> ordered world_records callback; default Application movement policy still rejects; context/replay/quest authority missing |
| C2S quest UI | `86`, 5 bytes; `C8350 -> C83A2 -> 132E0` | TRANSPORT_ROUTE: source low word and saved pointer high word preserved; no Application close/quest policy or mandatory 85/86 pair inferred |
| C2S WorldTailAccepted | `2E`, 7 bytes | RUNTIME_ROUTE: frame splitter -> movement callback -> service -> position commit; original speed policy still unknown |
| C2S WorldTailAccepted | `30 00`, 2 bytes | RUNTIME_ROUTE: exact tick accepted/consumed; no inferred reply or gameplay mutation |
| S2C World | `5D`, 2 bytes; consumer `692FA` | RUNTIME_ROUTE: RecoveredMovementService::move -> RecoveredMovement::ack -> Session write queue |

`Session::Impl::read` at `WorldTailAccepted` now calls `feed_world` if a complete
world handler configuration exists. `RecoveredWorldRecords::parse_frame` checks
the envelope, then preserves ordered typed C2S records for `30 00`, seven-byte
`2E`, five-byte `25`, seven-byte `85`, five-byte `86`, and 17-byte `35` actions
1/0B. This grammar uses native producers,
not the different S2C length table. Malformed complete batches cannot reach a
game callback. Incomplete TCP frames remain buffered.

`Session::RecoveredCharacterHandlers::world_records` is optional and mutually
exclusive with the prior movement callback. It receives owning decoded records
through a borrowed span on the serial game executor, after account/character
binding and world-tail validation. Nullopt rejects; empty bytes explicitly mean
no reply. Nonempty responses must be complete checksum-valid recovered frames
before entering the bounded network queue. The policy owns logical S2C grammar,
authorization and transactions; envelope validation is not a quest implementation.

Application still installs only `movement`. That fallback checks the whole
available batch and rejects any non-movement/non-tick record BEFORE submitting
movement to game code. Thus 25/85/86 do not become silently accepted or mutate
player state simply because a structural transport route now exists.

`Application.cpp` registers movement callbacks only under recovered dual
connection/world-entry/movement configuration. It connects `world_ready` to
`RecoveredMovementService::bind`, and `movement` to `move`. The service validates
its local policy, commits position, and returns ACK frames to the Session queue.
This is actual source wiring, not evidence that the original movement rules
are complete. Tick-only batches resume reads without calling the movement service.

`RegisterHandlers.cpp` registers fixture handlers through `OpcodeDispatcher`;
`Opcode.h` explicitly labels their 1000/2000-series numbers placeholders.
`God2ProtocolSpec::try_decode` reads a u16 opcode at frame+2 on that separate
path. Names such as NpcHandler/BattleHandler do not wire current `85`/`35`.

The old scalar-snapshot claim is anchored separately: current
`Session::Impl::accept_world_tail` explicitly leaves that replay diagnostic-only,
and does not call a scalar builder. Native `31 -> AA200` establishes consumer
layout/state writes, not selected-character values, snapshot direction by name,
bootstrap timing or a reply obligation. No historical values are promoted.

## Next Concrete Integrations

1. The direction-aware splitter and ordered typed callback now exist. Before
   extending them again, qualify each additional producer and state separately;
   battle opcode35 is deliberately not admitted to the world grammar.
2. Install an authoritative `world_records` policy in Application only after
   the corresponding original rules are recovered. Provide an account/character-
   bound service under `src/handlers` for pending
   dialogue state. Native `C7F10`, `C8780/C8920`, `C8500`, and `97DC0` are the
   concrete next evidence points for request/reply/context rules. Do not label
   receipt as quest acceptance or grant rewards while those rules are unknown.
3. The typed world router now uses `RecoveredInventoryItemRequest::decode` for
   C2S25; inventory authority and an Application handler are still absent. `41` and `3B`
   codecs can represent qualified projections; they do not provide item-use,
   ownership, consumption or source-construction rules.
4. Introduce explicit recovered battle state/callbacks before routing C2S35 to
   `RecoveredBattleCommand::parse_logical` or
   `RecoveredSkillCommand::parse_sequence`. Native battle `38/87/89` consumers
   identify future S2C contracts; they provide no cast authorization, combat
   resolution or award formulas. Fixture BattleHandler registration is unrelated.
5. The typed callback response now uses the recovered S2C queue. Produce
   qualified `72/DB/41/3B` and later battle/scalar projections, using
   `RecoveredWorldFrame::encode`. Sources, state gates and authoritative values
   must be established per contract; a generic validated envelope is insufficient.
   `RecoveredQuestSync::encodeSlotLogical/clearSlotLogical` can be integrated
   after the service establishes an authoritative visible-journal transition.

The current frame codec explicitly covers only the zero-seed recovered lab
connection. `Session::send(Packet)` reaches `Session::Impl::enqueue`, which
rejects recovered mode with "Fixture packet refused in recovered mode".
Typed emitters must use the recovered byte-frame response path; calling generic
send or extending fixture handlers does not establish that route.

Each eventual route needs frame/record rejection checks, correct state/ownership,
callback execution and actual response-queue evidence. A separate live current
client transaction is needed for CLIENT_ACCEPTED. This audit supplies none of
the missing original rules and does not satisfy the owner's completion criterion.

## Source Snapshot And Verification

The tool reads only immediate C++ files in `src/net`, `src/handlers`,
`src/protocol`, plus `src/core/Application.cpp` and explicitly named current
research models. It reports hashes and line anchors. Runtime conclusions are
a dated manual inspection, not a general C++ call-graph analysis. It refuses
changes to these route-defining files until reaudited:

| File | SHA-256 |
| --- | --- |
| src/net/Session.cpp | `dcdbef776a7f645bde3f116763215cee67ff2ca0f20b6135640e0b8347dcd85a` |
| src/net/Session.h | `5bf7d52a9d2185ba1191a397ef64635a28d7f47009675f70cddaf59f6a09531f` |
| src/protocol/RecoveredWorldRecords.h | `ff6aafd68e46914491f3b43dd0502519d857b38f4363c0cedbfb03002dbb9dcc` |
| src/protocol/RecoveredBattleCommand.h | `f88e6ba32bb6de0753281694cdc97a89ae9867b8a885cb8bb3e81cc7bfcc221c` |
| src/protocol/RecoveredQuestAction.h | `dfcc2420bbd2c3fbfee02796da1008afb5e88e1dc52be9356877ed0df1db48f3` |
| src/protocol/RecoveredQuestClose.h | `e0e6c1136a9265ea0ab3c7c10f8af01a6db1c2fa66939b8b72d8b5dc64425974` |
| src/protocol/RecoveredMovement.h | `4924afbabc17ed26e8de05147036167c8f05d5cdb0180138a3cfb08e3733ae72` |
| src/core/Application.cpp | `fd5edec740a94784b24252fc2915fe4db7eebf0ee93549e9a49a1b77536ea369` |
| src/handlers/RecoveredMovementService.cpp | `6fd21ea5019690613eb272eb4f4d423cfb10095e71cc046e3598786ade602419` |

Application was re-inspected after adding its database-backed skill catalog Lua
callback. The recovered movement bindings and absence of authoritative
`world_records` policy are unchanged. The updated source pin does not promote
any transport or codec entry to gameplay/client acceptance. All 13 coverage
regressions passed against this snapshot.

Session/typed parser were reaudited again for C2S35/actions1 and0B transport. The
InBattle check precedes the callback on the game executor; Application still
does not install battle authority. The13 coverage tests pass in12.901s against
the current hashes above, including direction collision and source drift checks.

Focused verification: **13 tests passed**. They cover all 254 native entries
and both defaults, complete variable/unsupported sets, 512 high-byte aliases,
variable-size boundaries, producer/receiver length collisions, independent
battle dispatch, original quest85 queue bytes, status separation, source-drift
rejection, image mismatch rejection and the complete JSON CLI. Native quest
execution has the existing 20,000-instruction cap. CLI execution is bounded to
30 seconds by the test. Main independently reran the updated audit: 13/13 in
9.760 seconds, including actual native close/action sequences. Production integration tests are tracked separately in the
gameplay continuation report. No live-client test is claimed by this audit.
