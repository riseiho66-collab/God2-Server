# Persisted test award to native result display

The existing pinned current consumer118BF0 loads the character received-EXP
display DWORD at logical89 offset5, then passes it to formatter852B0 at118C82.
This is a per-battle display contract, NOT the character accumulated-XP update.
See current-battle-experience-20260919.md for current image and message hashes.

## Isolated implementation

CUSTOM-0012 diagnostic_battle_experience defaults to0. Nonzero amounts require
diagnostic_battle_resources and terminal mode, inheriting animated skill,
participant, loopback, non-mock and diagnostic-accounts.db gates. Config rejects
nonintegral, negative, boolean, string and greater-than-signed32 values. The
signed limit follows native display, not an official reward limit.

The trusted Battle winner authorizes the explicit test amount on side0 victory;
loss supplies0. Atomic settlement saves resources, total and ledger before the
Battle snapshot is published. Later accepted terminal control prepares native89
and releases the battle. Only DWORD5 differs from the previously qualified
zero-result fixture. Other recipients, branch selector and opaque fields remain
zero. Failed settlement cannot publish a finished snapshot or emit this reward.
The general lossless RecoveredBattleExperience codec remains unchanged.

This adds no Lua reward formula: the amount is a diagnostic input, not a new
hardcoded monster award. Production reward/growth rules still belong in Lua;
C++ retains authoritative state and database transactions.

## Fresh evidence

Run native-player-test-award-20260921-01 uses explicit test amount25 against
our own isolated server. Result NATIVE_MOVEMENT_PATH_COMPLETED, no error:

- Three skills and two retaliations; five1/1 natural animations, no fallback.
- Native118BF0 entry receives exactly57bytes with DWORD5=25 and all other
  payload bytes zero.
- Breakpoint at original118C82 reads the numeric argument25 at ESP+10 (hex),
  before the original formatter call. The observer does not skip/replace it.
- Full consumer returns EAX1 with its received latch set; result panel returns,
  original battle exit completes and three native movements follow.
- SQLite resources HP76/max120/MP26/max80 revision4; exactly one ledger row,
  won=true, explicit award25, total25, CUSTOM-0012; position18,12 revision3.

Build and CTests config/recovered_battle_bootstrap/recovered_character_repository/
recovered_position_repository pass. Bootstrap tests check zero,25,signed32max,
all non-EXP bytes unchanged and high-bit rejection. Saved-evidence regression
suite passes12 tests, including packet/formatter/database equality and existing
zero-award evidence. Historical evidence tests are not fresh live reruns.

## Limits and next boundary

This supersedes prior notes that Application always supplies zero, ONLY when
the new explicit diagnostic option is nonzero. Defaults and production remain
unchanged. Amount25 is NOT recovered monster EXP or a balanced production award.
No accumulated-XP HUD, level-up threshold, stat growth, item loot, loss-result
live path, crash/reconnect result resend, visual screenshot or normal physical
input acceptance is certified. Native-function probes and historical
world_accepted classification remain separate. The next native boundary is the
character cumulative-XP/level consumer, not guessing that opcode89 credits it.
