# Atomic diagnostic battle settlement

## Follow-up: owned experience reads

The repository now exposes load_experience(account,character), returning an
optional CharacterExperience with total and design_id. A single LEFT JOIN
checks ownership while distinguishing absent XP from a persisted zero. Reads
never seed resources, XP or battles. Signed SQLite integer/type validation
rejects corrupt totals, and unqualified provenance is rejected. Settlement
uses this same reader inside its transaction instead of a separate XP decoder.

Tests extend the disk close/reopen and independent-connection settlement case
to load25/CUSTOM-0012 through the public API, including a new repository after
all earlier connections close. Separate tests check missing/zero, foreign and
invalid owners, signed64 maximum and deliberately corrupted fields. This is
storage readback qualification, not a live login or an EXP-bar refresh. The
next step must bind committed totals to a qualified progression policy and
the native display; no threshold or initial experience has been invented.

Migration8 adds empty character_experience and battle_settlements. It neither
seeds character resources nor awards existing characters experience. All rows
retain CUSTOM-0012 provenance. This is server storage, not a recovered formula.

The server-only settle_battle API uses BEGIN IMMEDIATE to validate ownership,
reservation identity and expected resources, increment the resource revision,
add an explicit bounded test award and write one canonical-request ledger row.
Readback verifies all three writes; exceptions and commit failure roll back.
Exact retries return the recorded result without writing resources or experience.
Different requests under the same battle ID fail, including changed awards.
Replaying an old result after a later battle cannot restore its earlier HP/MP.
Losses cannot award positive experience in this diagnostic policy.

Application uses this API only for Finished battles under the existing
default-off diagnostic_battle_resources gates. The winner comes from the C++
Battle snapshot, not client control or result messages. The supplied award is
ZERO; native zero-award outcome packets remain unchanged. Intermediate rounds
retain resource CAS. C++ owns transactions; Lua combat arithmetic is unchanged.

## Verification

- Repository tests: exact replay, changed outcome/award, foreign owner, missing
  reservation, stale resources, loss, signed64 experience overflow, failures at
  each write and corruption/deletion at readback. All preserve atomicity.
- Disk tests: close/reopen before settlement, two independent connections racing
  the same request, close/reopen after settlement and retry. One ledger entry,
  one resource revision increment and one test award25, not25 twice.
- database, recovered_character_repository and recovered_position_repository
  each passed10 consecutive runs after rebuilding the new tests.
- Fresh own-server client run native-player-atomic-settlement-20260921-01:
  NATIVE_MOVEMENT_PATH_COMPLETED, three skill commands, five natural animation
  completions without fallback, terminal HP76/max120/MP26/max80 revision4,
  one settlement for reservation1, totalXP0, world movement18,12 revision3.
  The ledger binds pre-terminal HP76/MP34 revision3 to HP76/MP26 and winner0.
  Regression reads the saved run and SQLite read-only; it is not a new live run.

## Remaining scope

Nonzero25 exists only as repository-test input, not a gameplay reward schedule.
No native monster EXP, level curve, item drops, balance approval, nonzero client
award projection or production activation is claimed. Reservation exclusivity,
abandoned-battle recovery and fully durable authoritative battle snapshots are
still open. In particular, a reservation alone does not authorize a terminal
outcome: only the trusted C++ caller supplies it. These tests do not claim
power-loss recovery or rendered UI/physical-input acceptance. The live runner
invokes native functions and keeps historical world_accepted classification
separate from the narrow battle-return/movement result.
