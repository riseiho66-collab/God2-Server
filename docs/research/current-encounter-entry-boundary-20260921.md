# World encounter entry boundary

Current Application emits diagnostic82 on the first accepted world Tick, once
per session. Timer36 then triggers diagnostic participant/battle binding. There
is no general encounter selection or movement-triggered encounter service in
src/scripts. RecoveredMovementService validates current scene2/15 navigation
and transactionally commits position before ACK, but selects no monsters.
Thus the successful diagnostic battle/resume is not ordinary encounter play.

## Verified reusable protocol

RecoveredBattleEntry now encodes/parses the existing nine-byte82 contract:
opcode plus two raw little-endian uint32 contexts. It is shared by Application
and RecoveredBattleBootstrap, replacing their separate byte assembly. Existing
zero-context diagnostic wire is unchanged. No encounter ID/map ID/monster ID
meaning is assigned to these opaque fields.

Authority: current-battle-entry-20260919.md, pinned native image SHA256
149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763.
Native world dispatch6AE12 writes contexts; initializer111409 consumes them.
Do not send82 to the already-active battle dispatcher as an entry operation.

Validation: server/bootstrap build; recovered_battle_bootstrap CTest;20 original
instruction harness tests in test_current_battle_entry.py. C++ tests cover exact
endian bytes, every truncation, oversized input, wrong opcode and high-bit/all-bit
context round trips. This turn runs no new live client acceptance.

## Next integration requirements

Use server-accepted committed location, not unvalidated client coordinates, as
encounter input. Keep zone/monster selection provenance explicit and use only
qualified entries; no wild-monster stats can be inferred from identity alone.
Before granting client control reserve/load the owned battle and saved resources.
Repeated encounter setup must not reseed an existing role/XP row, heal resources,
or reuse a settled battle ID. Existing level-snapshot probe intentionally rejects
existing roles, so it is not a reusable normal encounter initializer.

Any custom encounter distribution/rules remain default-off until documented
balance and current-client own-server acceptance. No production promotion or
encounter completeness is claimed by the new codec.

## Committed movement input

RecoveredMovementService::move_committed now returns ACK bytes, optional saved
baseline, committed RecoveredPosition and displaced_steps. The legacy move API
delegates to this path, retaining wire behavior. No result is returned until all
requests validate and the repository CAS succeeds. Displacement counts actual
coordinate changes in the accepted batch, not request count or endpoint distance;
stationary records count zero, a move out and back counts two. One whole batch
still commits one position revision. This is a C++ transaction result, not an
official encounter formula, probability or persisted encounter event/queue.

Tests cover rejected-batch absence of position writes, exact returned DB state,
reconnect baseline, stationary record, multi-record round trip with one revision,
ownership and stale-save rejection. god2-server/god2-tests build and
recovered_movement_service/recovered_position_repository CTests pass.
Encounter selection still needs its explicit policy and provenance; no callback
is invoked after a committed transaction that could fail and make callers retry
an already-applied move. Caller must also handle ACK/transition transport and
world/battle state ordering before normal encounter acceptance can be claimed.

## Movement-triggered candidate

CUSTOM-0014 adds default-off diagnostic_battle_after_movement. World-ready
binding preallocates a per-session boolean. A successful move_committed result
with displaced_steps>0 sets it without allocating a post-commit event. Existing
movement ACK is returned normally. A subsequent accepted singleton world Tick
may emit82 through the existing once-per-session guard. Disconnect removes the
flag. There is no custom randomness, monster distribution or repeated encounter.
Config requires diagnostic transition plus participants and rejects combination
with checkpoint resume; inherited loopback/isolated DB requirements remain.

Build/config/movement checks qualify candidate setup only. The native runner
still disallows simultaneous movement probing and battle transition and must
be adapted to observe pre-battle movement without stopping the run. Until that
test is executed, ACK/transition ordering and this trigger's native acceptance
remain unverified. No default config was enabled and no production promotion
occurred.
