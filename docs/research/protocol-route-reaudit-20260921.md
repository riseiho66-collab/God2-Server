# Protocol Route Reaudit

Status: REAUDIT_REQUIRED. This is a current-source inventory, not renewed route
certification. Existing route pins and fail-closed full audit remain unchanged.

The retained route audit predates Application's typed world handler. Its guards
still forbid an Application world_records assignment and expect only six case
labels. Current RecoveredWorldRecords additionally parses NPC interaction,
targeted item requests, context/timer notifications and action2 battle records.
Consequently merely refreshing hashes would preserve false missing-route claims.

The new --route-drift mode emits every changed/missing pinned source plus current
case labels and source references. It exits2 on drift, grants no acceptance and
does not run stale formal_contracts. Output is retained in
artifacts/protocol-route-drift-20260921.json. Two discovery tests pass, including
missing files, multiple changes, input immutability, no acceptance on unchanged
pins, and actual CLI failure status with structured output.

Seven current pinned sources differ:

- src/net/Session.cpp
- src/net/Session.h
- src/protocol/RecoveredWorldRecords.h
- src/protocol/RecoveredBattleCommand.h
- src/protocol/RecoveredSkillCommand.h
- src/core/Application.cpp
- src/handlers/RecoveredMovementService.cpp

Next review must inspect Session framing/sequence/deadline/state ownership and
each Application world-policy branch, then distinguish default-off diagnostic
acceptance from production activation. Existing town-chain/map and skill-restart
native runs support their specific configured paths only. Text references,
case counts and successful discovery tests do not certify those routes.
Full current_protocol_coverage remains intentionally failing until the dated
route conclusions, source pins and associated tests are reviewed together.

## Session Bridge Review

Reviewed current Session.cpp feed_world and valid_world_response, plus the
world_records declaration in Session.h. The bridge parses complete envelopes,
stages continuation records, rejects changed sequence identity/interruption/
overflow and uses a nonrenewable five-second pending-skill deadline. A pending
sequence leaving InBattle is rejected. Before posting any policy result, the
game executor rechecks battle-command state. The movement-only fallback rejects
nonmovement/non-tick records rather than silently consuming them.

The typed callback distinguishes nullopt rejection from an accepted empty
response. Nonempty responses must consist of complete checksum-valid recovered
envelopes within the output bound. This post-callback format check does NOT
roll back gameplay writes: each authoritative handler must prevalidate and
commit transactionally. Session cannot alone certify gameplay atomicity.

Application now installs world_records and contains default-off visibility,
NPC conversation, quest progress and battle branches. Therefore the old
transport-only/no-Application-policy conclusion is invalid. Presence of those
branches does not certify every operation or production deployment; their full
handler review remains open and the old route pins are not renewed here.

The Session skill regression now exercises every interior split of the
40-byte two-frame command stream (39 boundaries), not six selected splits.
Additional cases stage a valid prefix then send a bad checksum, invalid frame
length or unknown opcode. Each must close without invoking the gameplay
callback. Existing tests retain mismatch, interruption, expiry, maximum14
records and independent successive-sequence checks. These use real loopback
Session transport with synthetic handlers, not the original client.

Release god2-tests rebuilt successfully. CTest recovered_world_service,
session_state, session_skill_sequence and session_battle_service all pass
(4/4,140.38 seconds). This qualifies the reviewed transport behaviors and
extended negative cases; it does not renew the full formal-route snapshot.

## NPC And Town Reward Transaction Review

Reviewed Application's single-record NPC37/confirm85/cancel86 branches,
DiagnosticQuestConversation and the town progress/reward repository. The
conversation binds session/account/character; current request word, reply and
context must match. Commit runs before consumption, cancellation removes the
pending proposal, and followup gets a new request word without wrapping. Town
confirmation rechecks persisted area/scene/range and the progress snapshot.
The response is constructed before committing progress/reward. Reward requires
stage2, explicit owned empty slot0, source identity, matching revisions and no
unsettled battle. Progress, inventory and unique receipt commit together, with
readback checks. These are reviewed CUSTOM diagnostic policies, not recovered
official quest rules or production authorization.

Extended test_town_guide_atomic_reward injects failures after each of the three
SQL writes, plus a receipt trigger that corrupts inventory count before final
readback. Every attempt must throw, restore prior progress/slot and leave no
receipt. An independent database connection verifies that no partial grant is
visible after rollback. Existing successful retry, stale peer/replay refusal
and disk reopen assertions remain. The initial reader fixture omitted the
repository's mandatory migrate() initialization; that test setup was corrected.
Release rebuild and database/config/town_guide_lua/recovered_character_repository
CTest targets pass4/4. No production code or source pins were changed.

Current native evidence for this branch remains the retained full three-stage
quest and same-connection map-use run. Injection tests are synthetic database
tests, not crash-during-commit or physical-client-input acceptance. Map/scene,
other item operations, visibility and battle branches still need their separate
route conclusions before replacing the old whole-file audit.

## Targeted Supply Route Review

Application's targeted-item callback requires diagnostic_world_supply, completed
world-resource delivery, character1..3FFF before narrowing, slot0 and the
appropriate battle-transition phase. It obtains owned resource/slot snapshots
and selects only qualified policies3101/3107. Therefore no character-ID
truncation defect was found in this caller. DiagnosticSupplyService still
requires caller-proven target mapping; the raw target is not an ownership token.
Its stale 'No Application route enabled' comment now correctly describes the
default-off diagnostic route.

Service verifies request/policy/source/snapshots, asks Lua for the bounded
CUSTOM-0016 projection, allocates the entire occupancy/vitals frame, then uses
the repository's single transaction. Pending battles and both revisions are
checked inside that transaction. A no-op emits no frame and writes nothing;
the custom non-revival policy rejects dead-role restoration by returning no-op.

New service regressions reject every truncated seven-byte request and an
extended record, preserving slot and resources. A dead-role fixture exercises
all256 opaque-tail values: no consumption, no response, no HP/MP or revision
change. Release diagnostic-supply builds; diagnostic_supply, supply_lua,
recovered_world_service and recovered_character_repository pass4/4. No supply
amounts, native formulas or production activation changed. These are service/
repository tests, not fresh original-client acceptance for additional items.
