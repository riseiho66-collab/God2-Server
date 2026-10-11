# Owned saved player world-entry projection (2026-09-26)

## Implementation

`handlers/RecoveredPlayerSnapshot.h/.cpp` adds:

```cpp
auto saved = RecoveredPlayerSnapshot::load_for_world_entry(
    repository, session.account_id, session.character_id);
if (saved) {
    auto wire = RecoveredWorldFrame::encode(
        saved->logical_before_companion_binding);
    // Append wire at the qualified fresh world-entry point.
}
```

The helper reads existing owner-qualified resource and role rows. It does not
write or create records. Saved resources retain `CUSTOM-0012` provenance and
saved role snapshots retain `CUSTOM-0013`; replay does not establish native
initial stats or growth. Both rows are reread to detect changes during the
read, but the caller must still serialize entry with account/session mutation.

An existing role snapshot is reproduced byte-for-byte as S2C22, including its
saved level, base stats, progress-display word and opaque bytes. S2C24 follows
with exact saved HP, MP and maxima. Resource-only characters receive only
S2C24. Missing both rows returns no projection. A role without resources,
invalid provenance/revision, bounds error, mismatched maxima, or changed read
throws before a result is returned. Dead characters with saved HP zero are
preserved; maximum MP zero is permitted when current MP is zero.

## Integration ordering

Send only once after the local world actor is initialized, before any S2C30
companion binding. This helper has no diagnostic configuration dependency and
does not own the session-ready check, pending-battle handling or once-per-entry
marker. Parent Application integration owns those checks.

Native S2C24 (`69F4D -> E71E0`) can subtract an HP decrease from an existing
companion's HP. Therefore this projection is not a generic refresh API. Sending
it after restoring a companion requires a separately qualified companion
restoration strategy. S2C22 precedes S2C24 so current vitals are the final role
values. See `current-role-progression-20260919.md` and
`current-world-scalar-bootstrap-20260919.md` for the native consumers.

## Explicit unresolved fields

- `character_experience.total` is cumulative server EXP with `CUSTOM-0012`
  provenance. It is not the S2C2B progress-display word. This helper neither
  reads it nor derives a percentage from an unproven curve.
- There is no saved learned-skill ownership table in the inspected current DB
  schema. `native_skill_catalog` and `native_skill_books` describe definitions,
  not learned ownership. No S2C34 is emitted and no diagnostic S2C30/34 seed is
  promoted. The native writer requires a previously existing matching row;
  see `current-battle-learned-skills-20260920.md`.
- S2C2C is a 61-byte stat-modifier record, not the portrait. No complete owned
  modifier snapshot exists here, so no zero-filled S2C2C is invented.
- The current `RecoveredWorldEntry::decoded(local_id, profile, ...)` already
  copies saved profile appearance to body20..23, consumed at `68370` and by the
  HUD path `ABCED -> ABE80`. This module leaves that existing projection intact.
- Unknown initial HP/MP, stat growth, learned-skill grants, and companion state
  are not supplied by this replay implementation.

## Verification

`tests/test_recovered_player_snapshot.cpp` compiled independently with MSVC
C++20 `/W4`, together with this module only, and passed **28 checks**. It covers
owner rejection, absent data, exact opaque/level/progress preservation,
22-before-24 order, frame roundtrip, resource-only restore, saved dead/zero-MP
states, inconsistent rows, provenance and revision errors, and changed reads.
The fake repository throws for any unexpected read or write; EXP conversion,
seeding and mutation would fail the test.

Standalone test binary: `build/player-snapshot-agent-check/test_recovered_player_snapshot.exe`.
No shared core build, live database mutation, desktop operation or game launch
was performed by this lane. Application integration and actual-client acceptance
are separate parent-owned gates.
