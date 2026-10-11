# Isolated Lua supply projection

CUSTOM-0016 is a pure Lua rule behind LuaEngine::supply, not an active item-use
handler. It does not grant inventory, change saved data or send packets.

Source MED02 exact tooltip declarations remain independently recorded in
current-supply-tooltip-evidence-20260921.md. Caller supplies trusted recovery
amounts; this function cannot certify their native origin or authorize an item.
No recovery amount comes from C2S25 raw_tail, whose quantity meaning is unproven.

Custom policy: a living actor recovers each resource by min(explicit amount,
missing capacity). Dead actors stay unchanged; no revival. Consume one unit only
if HP or MP increased. Full relevant resources consume none. These cap, death and
consumption rules are NOT established by native tooltip text. Positive max HP,
nonnegative max MP, coherent snapshots and signed32 amounts are required.
C++ checks input/output bounds and Lua boolean consumption; Lua owns projection.
No targets, cooldowns, battle use, equipment modifiers or economy are implemented.

Verification: Release supply-lua, progression-lua and god2-server built. CTest
supply_lua, progression_lua and recovered_character_repository passed (3/3).
Supply tests enumerate 20,475 small-domain projections, then explicit MP2->52,
MP52->80 clamp, MP80 no-op, signed32 maxima, zero max MP, eight invalid inputs
and reload. These are arithmetic regressions, NOT balance or native acceptance.

Next integration: validate explicit owned slot against qualified catalog and
world lifecycle, reject pending battle, prepare native replies before mutation,
commit slot/resource CAS atomically, and qualify client consumption/resource
display on our own server. Missing inventory row must remain unknown, not an
implicit empty slot. No production promotion before balance/client acceptance.

## Transaction integration

DiagnosticSupplyService now provides the internal use boundary (not Application
dispatch). Exact C2S25 shape, item ID, slot bounds, explicit opaque tail, source
hash identity and owned server-held snapshots are checked. Missing slot rejects.
Lua projects resources; a no-op returns no reply or storage write. On consumption,
S2C41 occupancy plus S2C24 vitals are encoded into the lab zero-seed envelope
before committing both saved states via the repository transaction. No outbound
result is returned after a failed commit. Source hash equality is not source
certification; caller still owns qualified catalog and world/session admission.

test_diagnostic_supply.cpp uses real in-memory SQLite and actual LuaEngine:
three explicit test units, MP2->52->80, then no consumption at cap. Wrong item,
slot50, uninitialized slot1, tail1, truncated request, foreign owner, source
mismatch and stale saved snapshot reject. A pending battle rejects consumption
without changing slot/resources. Response frame is decoded to inspect occupancy
and resource projection. Diagnostic-supply and server build; CTest diagnostic_supply,
supply_lua and recovered_character_repository pass (3/3).

No live C2S route, inventory grant, UI test or production policy activation was
added. Repeated same wire with a newly loaded baseline is NOT detected as replay:
C2S25 has no proven request ID. Caller session/admission policy remains necessary;
the stale-snapshot test only establishes CAS semantics. Combined S2C41+24 order
still needs current-client acceptance. This is not a completed supply workflow.

## Native26 correction (supersedes synthetic25 admission above)

RecoveredTargetItemRequest now preserves the seven-byte26 logical record:
opcode, raw target WORD, item WORD, slot byte, residual byte. Exact length/opcode
required; structural codec does not authorize raw values. DiagnosticSupplyService
now uses this codec, rejects25, checks a trusted expected target and limits use
slots to0..29 (native963C0 scan), rather than all50 S2C occupancy slots. Residual
tail is ignored by policy, never a count or replay key. Target-to-character
mapping is still the caller's unqualified live prerequisite, not established by
matching a synthetic1234 word. Application remains unmodified/default inactive.

Updated integration tests cover wrong target, old25 rejection, slot30 rejection,
all256 residual byte roundtrips, a second consumption with changed tailFF,
resource cap/no-op and transactional pending-battle rejection. Diagnostic-supply
and server built; diagnostic_supply/supply_lua/recovered_character_repository
CTest3/3 passed. No live use or production acceptance claimed.

## World grammar and optional routing

RecoveredWorldRecords now parses native26 as a distinct typed record after full
frame validation. RecoveredWorldService has an optional supply callback; all
existing callers omit it and retain rejection. Only one supply plus optional
ticks is routed. Movement/combat/unsupported mixtures, duplicate supply records,
in-battle state and incomplete batches reject before any callback. The callback
must still verify completed world entry, ownership, live local-ID mapping and
catalog eligibility; this change does not attach DiagnosticSupplyService to
Application or grant inventory.

Server and recovered-world-service built. recovered_world_service test passes
with decode, truncation, unknown suffix, default rejection, valid routing and
mixed-batch checks. Existing recovered_server_routes test also passes; this is
not a live login/world/client test. Application supply initialization and real
client acceptance remain the next integration boundary.

## Application candidate (default off)

diagnostic_world_supply now requires diagnostic_world_resources and forbids
diagnostic_battle_transition. It inherits loopback, non-mock recovered movement
and diagnostic-accounts.db restrictions. No ordinary config was enabled and no
existing save database opened by this change.

First resource tick projects explicit saved slot0 only if its source matches
current gamedata and occupied ID is3107. Missing slot fails closed; tombstone is
preserved, other slots never inferred empty. No seeding, grants or automatic
healing. Native41 metadata/UI initialization remains a live qualification risk.

The optional world callback requires this flag and completed resource projection,
loads account-owned slot/resources, restricts slot0, binds raw target to the
current session's character ID under the existing1..16383 lab mapping, and calls
DiagnosticSupplyService with MP50. This is not a permanent entity ID allocator.
Fresh baselines permit repeated legitimate requests; no network request-ID
replay deduplication is claimed. Lua CUSTOM-0016 cap/death/consumption policy and
CUSTOM-0015 atomic storage remain isolated. Next: runner opt-in, explicit test
inventory preparation and native client use/reply observation. Not production.

## Prepared native-test database

diagnostic-supply --prepare-copy accepts only an existing diagnostic-accounts.db
under artifacts/runs and a new immediate child run directory. Source opens
SQLITE_OPEN_READONLY and SQLite backup creates the destination. Only destination
is migrated through actual SqliteDatabase then seeded through atomic repository.
Existing destination refuses overwrite. This is an explicit test executable
operation, not Application login behavior or a production grant.

Prepared artifacts/runs/native-supply-fixture-20260921-01/diagnostic-accounts.db
from native-two-encounters-relogin-20260921-01. Account1/character1 required, HP52,
max120, MP2/max80 and absent slot0 checked before grant. Three3107 units are an
explicit CUSTOM-0016 fixture, tagged CUSTOM-0015 storage with current source hash.
Resource revision10->11 records the atomic inventory transaction; HP/MP unchanged.
Read-only comparison confirms all original tables equal except schema_migrations
and character_resources revision. New slot row is character1/slot0/item3107/count3/
revision1. Accounts, character, role, position, XP, checkpoints and settlement
tables match. Build and diagnostic_supply CTest pass. No client launched yet;
runner flag/probe integration is still pending, so no supply acceptance claimed.

## Live projection accepted, use pending

Runner now exposes --diagnostic-world-supply only with restored isolated world
resources and no battle transition. It passes the flag to the C++ server.
native-supply-projection-20260921-01 reached saved-position restore; run02 adds
read-only native slot capture before completion. Both finished without error.
Run02 slot0 bytes03000000230c000000000000000000000000000000000000 prove
count3/item3107 after server projection. Native resource return remains HP52/120,
MP2/80. All16 SQLite tables match the prepared source fixture exactly, including
inventory and resources: login does not consume or regenerate anything.

test_current_supply_projection.py retains these assertions. This is actual
client-process memory/consumer evidence, not visible icon/UI acceptance. No item
request was induced; next step is original963C0 use with native return handling,
server capture, two resource increases and no-op-at-cap behavior. Broad world
acceptance flag remains false; do not relabel projection as full gameplay.

## Native use sequence accepted

native-supply-use-20260921-01: --probe-supply-use runs original963C0 three times
from a paused native world-frame return. An owned diagnostic thunk preserves
registers/flags and checks return stack/page bytes. It passes item3107; original
lookup/target/slot selection and queue append execute normally. No fabricated
C2S bytes or resource writes. This is a native-call probe, not mouse/UI action.

Result NATIVE_SUPPLY_USE_SEQUENCE_OBSERVED with no error. Actual captured26
packets490/507/524 contain target1/item3107/slot0 and varying residual tails
B5/89/A2, with valid checksums. First response leaves count2/MP52, second
count1/MP80, third remainscount1/MP80 during a three-second observation. HP52
unchanged. SQLite finishes slot revision3/resources revision13, two successful
transactions from prepared revision1/11. Third no-op adds no storage revision.

Saved-evidence test_current_supply_projection.py verifies calls, client-memory
results, all three captured native requests, and final database. Native textMP50
and native protocol are distinct from CUSTOM-0016 clamping/consumption. Visible
icons, ordinary UI interaction, wider item set, supply reconnect and coexistence
with encounter loops remain unqualified; default production mode unchanged.

## Fresh supply relogin

native-supply-relogin-20260921-01 restores a read-only backup of the completed
native-supply-use run. Runner projection expectation now comes from the saved
explicit slot instead of hardcoding the initial count3. It requires one occupied
3107 slot0 record with count1..127; use-probe initial fixture still requires3/MP2.

Fresh native run finishes NATIVE_SAVED_POSITION_RESTORED without error. Client
slot0 is01000000230c000000000000000000000000000000000000 (count1/item3107),
resource return HP52/max120/MP80/max80. No supply probe called on relogin. All16
tables equal the used source, including slot revision3/resource revision13.
Four saved-evidence tests pass. This qualifies saved occupancy/resource restore
after use, not visible inventory rendering, mouse-use acceptance, arbitrary
items or battle/supply coexistence. Full playable-world goal remains incomplete.

## Last-unit native slot use

The probe now invokes original96390 with slot0 rather than963C0 with item3107.
It preserves registers/flags; original slot lookup and downstream caller decide
whether to enqueue. --probe-supply-exhaustion requires supply probe and a separate
explicit one-unit fixture. --prepare-single-copy uses the same read-only backup,
C++ migration and repository grant as the three-unit helper.

native-supply-exhaustion-20260921-01 completed without error. Two native calls
returned; only one26 packet was captured (494, target1/item3107/slot0). First
result clears slot24 bytes tozero and MP2->52, HP52 unchanged. Second empty-slot
call leaves slot/resources unchanged during three-second observation. Stored
slot item0/count0/revision2 and resourcesHP52/MP52/revision12 show one atomic use.
No desktop click or icon-render verification is claimed. Empty-slot relogin and
encounter coexistence remain open. Five saved supply evidence tests pass.

## Empty-slot fresh relogin

Runner now accepts an explicit saved item0/count0 tombstone as well as occupied
3107; it still rejects absent rows and inconsistent ID/count. No inferred grants.
native-supply-empty-relogin-20260921-01 restores a read-only backup of exhaustion
run01, finishes saved-position restore without error, and reads24 zero slot bytes
plus HP52/max120/MP52/max80 from the actual client. All16 database tables remain
equal to the exhaustion source; no supply call, regen or grant occurred. Six
saved evidence tests pass. This closes the narrow empty-slot reconnect case.

Remaining playable-loop integration must address battle admission and transition
ordering. Current diagnostic_world_supply intentionally excludes battle transition;
do not simply remove that gate. Existing second-encounter policy pins the first
settlement baseline, so supplies require an explicitly qualified updated baseline
and observer expectations. Production/UI acceptance remains incomplete.

## Settlement/supply/next-reservation transaction check

Extended actual SQLite+Lua+DiagnosticSupplyService integration test beyond the
pending-reservation refusal. An explicit first terminal settlement leaves HP40/
MP2 and awards25 testXP. Supply consumes the last item and restoresMP52. Replaying
the exact old settlement returns its historical result without overwriting the
new resources or slot. A new reservation with the pre-supply version rejects;
the supplied baseline reserves a distinct battle ID. Pending second reservation
also rejects inventory replenishment. Explicit second settlement leavesHP28/MP44
and totalXP50; replaying the first again changes neither state nor XP.

diagnostic-supply rebuild and CTest pass. These are supplied outcome snapshots,
not actual Battle simulation, native formulas or live two-encounter acceptance.
Application's supply/battle mutual exclusion remains unchanged pending a
dedicated live transition experiment. This test establishes the storage boundary
needed for that integration without relaxing native initialization constraints.

## Live single battle then supply

The previous blanket mutual exclusion is narrowed only for an explicit durable
single terminal three-round battle with world resources, no level-snapshot mode
and no checkpoint resume. Existing default-off isolation remains. Supply callback
additionally requires battle vitals sent and the post-battle context handshake
to have cleared its rounds entry. Pending reservation still rejects storage writes.
Config positive/negative tests pass. No two-encounter policy was relaxed.

native-post-battle-supply-20260921-01 starts from savedHP52/MP80/count1. Actual
client runs three skills and five natural animation completions. It returns to
the same world resource owner at sequence724 with HP28/MP56. Original slot0 use
then sends26 at packet735; source item3107 is consumed, HP28 retained, MP80
received at sequence748. A second empty-slot call remains unchanged through895.
Final database resources28/80/revision17, empty slot revision4 and three total
settlements (two preexisting, one new). This diagnostic battle adds no XP reward.

Result NATIVE_POST_BATTLE_SUPPLY_OBSERVED, no error. Saved-evidence regression
checks order, native request, three commands/five completions and stored result.
This qualifies one battle->world->supply loop in an actual client process under
native-call probes. Normal UI, another encounter after this supply, death and
broader items remain incomplete. No production balance approval or full-world
acceptance follows from the narrow success.

## Next battle from saved post-supply resources

native-after-supply-battle-20260921-01 uses a NEW connection and read-only backup
of the completed post-battle-supply run. Runner admits only its explicit resource
baselineHP28/max120/MP80/max80/revision17 plus depleted slot0/revision4; no resource
or inventory seed. Original client observes28/80 before battle, performs three
skills/five natural animation completions, returns to the same world resource
owner withHP4/MP56. Database resource revision20, four total settlements (one
new), empty slot unchanged. Result NATIVE_SOCKET_BATTLE_RETURNED_TO_WORLD_LOOP,
no error. Eight saved evidence tests pass.

This proves replenished saved resources feed a later real-client fight without
login healing/regrant. It is NOT same-session automatic re-entry after supply;
that remains open. Only4HP remain, so native-first healing support and death/
recovery are now immediate playable-loop gaps. Do not hide them by resettingHP.

## Native-text healing policy

Fresh native item-row parser run confirms MED02 index0 ID3101, source line6354,
flagsFB07 (bit04 clear, original26 branch), with exact text declaringHP100.
DiagnosticSupplyService::current_supply_policy now allowlists3101 HP100 and3107
MP50 against the pinned gamedata hash. Other IDs and invalid target IDs reject.
Application uses this explicit lookup instead of always assuming3107; existing
default-off, slot0, source/CAS and battle-state restrictions remain. No new grant.

Actual SQLite+Lua service test supplies one explicit3101 after its synthetic
settlement case: HP28+100 clamps to120 and MP44 stays44, slot consumed atomically.
The clamp is CUSTOM-0016, not recovered native semantics. Server and test build;
diagnostic_supply passes. This is not live healing acceptance yet. Next use the
HP4/MP56 post-supply-battle save in a separate test copy with explicit healing
inventory, preserving original saves and checking native resource side effects.

## Live low-HP healing

--prepare-healing-copy accepts the explicit HP4/MP56/revision20, empty slot0/
revision4 outcome from native-after-supply-battle. Read-only backup plus actual
repository transaction creates three3101 in a NEW fixture directory; no source
save modified and no HP/MP reset. This diagnostic grant is not native acquisition.

native-healing-use-20260921-01 restores that fixture and executes native96390
slot0 three times. Captured26 packets492/509/526 carry target1/item3101/slot0.
Native role/slot readback: HP4->104->120->120, MP56 unchanged, count3->2->1->1.
Final SQLite resources120/56/revision23,3101/count1/slot revision7: exactly two
successful transactions; full-health third call does not consume. Result
NATIVE_HEALING_USE_SEQUENCE_OBSERVED, no error. Nine saved evidence tests pass.

Native source declares100HP; clamping and no-op consumption are still CUSTOM-0016.
No native death/revival, ordinary mouse interaction, icon render or production
balance qualification is inferred. Companion side effects and sustained same-
session encounter/supply loop still need coverage. Global goal remains active.

## Subsequent same-session socket integration (2026-09-24)

The separate default-off `CUSTOM-0014/CUSTOM-0016` branch now completes
battle → original-shape `C2S 26` supply → second battle in one isolated own-server
TCP session. See [current-same-session-battle-supply-20260924.md](current-same-session-battle-supply-20260924.md).
This supersedes the earlier statement that server-side same-session integration
was untested. An executing original-client combined run and normal UI acceptance
remain open.
