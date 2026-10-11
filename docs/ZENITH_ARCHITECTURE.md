# ZENITH Proof-Carrying Reconstruction

ZENITH extends [APEX](APEX_ARCHITECTURE.md); it does not authorize replacing missing
runtime evidence with more architecture. Current executable work is capture intake,
local review/promotion, immutable certificate dependencies and audit. Highest actual
acceptance remains L1. No original client was run for this increment.

## Implemented Boundary

Original artifact SHA256 -> capture manifest SHA256 -> attachment hashes/event IDs
-> content-addressed human review -> content-addressed gate certificate -> audit.

The existing original artifact vault remains authoritative. New review objects live
in a separate research.db extension and `artifacts/proofs`; gameplay god2.db is
not used. The server does not import research/debugger tooling. Status reports now
derive local gate promotion from freshly audited certificates, not edited Markdown.

G02-G04.5 can be promoted only under an owner-installed human review policy, with
runtime evidence and the complete prerequisite chain. This implementation uses
trusted local operator identities, NOT digital signatures. Nothing is promoted in
the real workspace, because neither real capture nor trusted review policy exists.
G05 remains a function-identity foundation, not a certificate issuer.

## Reserved Interfaces

These are schema/interface reservations only. No extra engines, server runtime
dependencies or pretend evidence records are created to populate them.

| Interface / record | Reserved contract | Activation prerequisite |
| --- | --- | --- |
| ContentObject | sha256, schema_version, tool_version, parents, created_at, provenance | Extend beyond current artifact/capture/review objects when real producers exist |
| ClaimDependency / ClaimAudit | claim_id, evidence_ids, dependencies, counterclaims, affected contracts/fixtures/codegen/tests/sessions/docs | Actual reviewed claims; current blast radius is certificates only |
| SignedReviewEnvelope | review_hash, authenticated_principal, signature, key_id, policy_hash, timestamp proof | Owner-managed identity/key policy |
| HardwareTraceAdapter | producer/version, timeline, address-space identity, control-flow events, loss indicators | Controlled Intel PT/ETW/WinDbg source |
| ExecutionCheckpoint | capture_id, timeline_position, registers, memory object IDs, replay constraints | Real time-travel-capable capture |
| BinaryConsensus | engine versions, normalized CFG/calls/constants/accesses, disagreements | Reviewed analysis image; consensus never substitutes for runtime |
| MicroExecution | image/function IDs, registers, input memory, resource limits, output bytes/registers/deltas | Isolated recovered function + runtime comparison fixture |
| BoundedSymbolic / Solver | function/contract ID, constraints, budget, path results, hypotheses | Verified small parser and concrete fixtures |
| ProtocolInvariant / Compiler | reviewed revision/fields/states/invariants, fixtures, generator hash, generated object IDs | Real framing/transforms/dispatch and reviewed contracts |
| RoundTripProof | fixture IDs, encode/decode outcomes, declared semantic equivalence for nonce/time/sequence | Executable real protocol specification |
| ExperimentPlanner | alternatives, controls, intervention, expected information gain, counterfactual outcomes | Discriminating real observations; no numeric VERIFIED threshold |
| SemanticFunction / SemanticType | semantic ID, per-artifact function or offset maps, supporting evidence | Cross-build runtime triangulation |
| RevisionPatch / Fingerprint | base_revision, patch, reviewed handshake features, ambiguity rejection | Multiple verified revisions; never guess from executable names |
| ConformanceResult | build IDs, revision, original-client session, expected/actual state and bytes | Real handshake through persistence/reconnect regression |
| DomainContract | preconditions, commands, events, invariants, authoritative validation | Evidence-backed domain work after core compatibility |
| DeterministicKernel | injectable clock/RNG/IDs/timers, snapshot, seed, config | Golden sessions; no twin replacing real client acceptance |
| FaultMatrix / ChaosRun | baseline fixture, fault schedule, bounds, observed outcomes, reproduction capsule | Meaningful recovered protocol/domain fixtures |
| ResearchCapsule | artifact/capture/evidence/experiment/review/tool object IDs | Exportable reviewed research; current store is not a portable capsule exporter |
| ReproductionCapsule | client/protocol/server build IDs, session, DB snapshot, clock, seed, config, logs | Reproducible server scenario |
| BuildProvenance | source commit or explicit unknown, compiler/tool/dependency versions, protocol hash, DB schema, Lua API | Measured build metadata; no fabricated Git commit |
| PersistenceMigrationProof | row/ID/FK/null/encoding/time/checksum/domain equivalence | Actual gameplay SQLite-to-MariaDB migration |
| LuaContract | required API version, capabilities, deterministic test clock/RNG | Scoped Lua evolution, not raw world/socket/DB authority |
| CausalityEvent | trace/session/character/build IDs, packet/command/event parents, measured stage durations | Real traced flows; later performance budgets from measurements |

The future proof-carrying protocol contract must reference runtime observations,
functions, fixtures, experiments, reviews, regressions and original-client acceptance.
Generated source must be byte-identical for the same DSL and generator inputs.
Production real-protocol mode must reject hypothesis-only core contracts; research
flags do not belong in a production build. None of those future modes/codecs is
enabled by current certificate tooling.

## Acceptance Rules

Runtime truth outranks static consensus. Human review cannot replace absent data.
AI may prepare empty worksheets and run validators but must not provide a human
attestation or authorize itself. Revocation invalidates dependents. Snapshots are
historical, and current audit decides usability.

Core compatibility requires original-client handshake, login, character list,
selection, world entry, heartbeat, movement, reconnect, persistence and golden replay.
Only then may a final client compatibility certificate exist and the core enter
compatibility freeze with mandatory regression/revision impact checks.

Do not implement symbolic/taint/solver/active-learning/formal-verification/twin/
autonomous-agent engines now. Next external input remains one controlled runtime
capture bundle, followed by independent human review. Gameplay expansion stays deferred.
