# APEX Reconstruction Boundaries

Current implementation scope is Gates 02, 03, 04, 04.5 and the Gate 05 identity
foundation. [Runtime intake](../tools/research/RUNTIME_CAPTURE.md) describes the
implemented contract. No gameplay expansion is part of this increment.

## Ownership

Research: artifact vault -> runtime intake -> consistency assessment -> reviewed
evidence -> future normalized function model -> protocol knowledge -> fixtures
-> protocol DSL -> generated codec. Only the first three stages currently run.

Server: revision adapter -> validated domain command -> game/domain event ->
revision adapter. Lua receives validated domain data and requests actions;
it must not own sockets, packets, protocol state or direct database writes.
Persistence remains repository-owned. No debugger dependencies enter server builds.
Existing mock wire fixtures remain explicitly separate from recovered contracts.

## Reserved Schemas And Interfaces

The following are design reservations, not installed database tables, working
engines or public stable APIs. All future records require `id`, `artifact_id`,
`revision_id` when known, `evidence_ids`, `confidence` and counter-evidence links.
Unknown revision is null, not an invented GOD2 revision. Evidence must retain
capture/event references; no engine may write VERIFIED directly.

| Reserved record/interface | Fields beyond common provenance | Prerequisite |
| --- | --- | --- |
| NormalizedFunction / lift(image, function) | blocks, normalized_instructions, imports, constants, memory_accesses, callees | Independently verified analysis image |
| FunctionMatch / match(a,b) | left_function_id, right_function_id, score, rationale | Valid normalized functions; never implies same protocol |
| ProvenanceEdge / trace(source,sink) | source, transforms, destination, observed_reads, observed_writes | Correlated runtime data flow |
| ConstraintHypothesis / constrain(parser,fixture) | path, predicates, input_fixture_id, bounds | Verified function + concrete fixture; output HYPOTHESIS |
| RecoveredType / recover(accesses) | size_if_known, offsets, widths, access_sites, semantic_names_if_verified | Consistent memory access evidence |
| PacketHypothesis / infer(corpus,events) | direction, state, action, candidate_fields, alternatives | Real buffers and network data path |
| Experiment / plan(unknowns) | controls, one_variable, expected_distinguishing_results, cost, outcome | Testable competing hypotheses |
| OracleObservation / observe(action) | action, expected_ui_world, observed_state, packets, handlers | Controlled real-client session |
| ProtocolContract / generate(reviewed_contract) | revision, packet, direction, opcode, legal_states, fields, fixture_ids | Gate 07-09 evidence, reviewed field contracts |
| GoldenFixture / replay(session) | raw_blob_hash, decoded, ordered_events, direction, state, schema_revision | Verified packets + real session |
| Mismatch / compare(expected,actual) | expected_fixture, actual_blob, offset, state, hypothesis_refs | Real oracle versus rebuilt server |
| Twin / simulate(session) | deterministic_seed, clock, commands, expected_events | Core contracts and golden sessions |
| Mutation / fuzz(fixture,state) | seed_fixture, mutation, initial_state, resource_budget, outcome | Recovered parser/state contracts |

Knowledge graph node kinds are reserved for Artifact, Function, RecoveredType,
GameAction, UIAction, Packet, Opcode, PacketField, State, Handler, CryptoTransform,
CompressionTransform, Evidence, Experiment, Fixture and Session. Edges reserve
CALLS, READS, WRITES, DISPATCHES_TO, CONTAINS, PRODUCES, CAUSES, TRANSITIONS,
SUPPORTS, CONTRADICTS and VALIDATES. These are not populated with guessed data.

The future reviewed DSL is the single source for DTOs, parsers, serializers,
opcode/state maps, textual/JSON decoders, fixtures, tests, docs and Lua debug
views. No duplicate handwritten schema should precede it. Deterministic clock,
RNG and IDs, snapshots, performance baselines and database cutover validation
remain future implementation work, not claims about the current framework.

## Acceptance And Autonomy

L0 framework; L1 artifact; L2 unpack; L3 OEP; L4 IAT; L5 analysis image;
L6 network roots; L7 framing; L8 transforms; L9 dispatch; L10 handshake;
L11 login; L12 character; L13 world; L14 movement; L15 real-client core;
L16 gameplay reconstruction. Every level requires its predecessors.

Read generated status and blockers, choose the highest-value unblocked work,
implement, test, collect evidence, regenerate status, stop at the next external
blocker. Current blocker: one controlled runtime capture bundle, then independent
review. Do not substitute more mock gameplay, a taint engine, concolic engine,
inference engine, DSL generator, behavioral twin or stateful fuzzer for that evidence.
The original client remains the final oracle; neither synthetic tests nor a twin
can establish REAL_CLIENT_CORE_COMPATIBLE.
