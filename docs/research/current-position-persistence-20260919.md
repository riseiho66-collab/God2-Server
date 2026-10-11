# Recovered Position Persistence

## Implemented

`config/recovered-movement.json` now preserves accepted area2/scene15 movement
in SQLite and projects the saved position into the next world-entry2A frame.
First-time characters retain the source17,13 initial position. Unknown saved
scenes and blocked saved cells fail closed; no fabricated fallback or map change.
This is implemented transport/storage behavior, not live rendered-world acceptance.

Migration3 appends `recovered_positions`; migrations1/2 are unchanged. The table
references `recovered_characters`, not the mock-world `characters` table. Profile
bytes and account rows are not rewritten by movement. Schema upgrade tests
start from an existing two-migration database with populated characters.

The new repository methods check ownership even when no position row exists.
A transaction compares the complete expected area/scene/x/y/revision snapshot,
writes one new revision, reads back the exact result and commits. Missing-row
expectations only insert. Revision overflow, stale state, constraint failures,
ignored writes, readback discrepancies and commit errors all reject and roll back.
The revision is a server persistence version, not a GOD2 wire sequence.

The movement service reserves a character when constructing world entry, before
the client sees the coordinates. A second connection cannot reserve that character.
Only the valid world-ready tail activates movement, after checking that the saved
snapshot is unchanged. Disconnect releases the reservation. Invalid batches do
not publish a valid prefix, consume the ring index or commit coordinates.

All successful movement writes happen before memory publication and ACK creation
returns to transport. A later network failure can lose an ACK after commit; the
next connection restores the committed location rather than replaying the old
packet. Ring indices restart with the newly initialized client ring and are never
restored from storage. No distributed online lease or multi-server ownership is
claimed; this remains the single local C++ game-executor deployment.

## Exact Coordinate Evidence

The current pinned image is unchanged:
`149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
Original instructions `68636..68659` read body+28 as an unsigned DWORD:

```text
kind = packed & 3
x = (packed >> 2) & 0x7fff
y = packed >> 17
```

The C++ encoder replaces only x/y, retaining kind and all unrelated body bytes.
Coordinates above32767 reject instead of truncating. Default17,13 output remains
identical to the existing profile-projected frame. Checksums and the exact
zero-seed encoding are recalculated by the existing frame codec.

The original current decoder and full bounded actor projection were executed
against the emitted C++ frames: normal indoor positions, zero, cross-byte values
and32767 boundaries reach actor+8/+12 exactly. Resource/render helpers remain
stubbed as explicitly documented in `test_current_world_entry.py`.

Both historical trees had been searched in `legacy-movement-contract-20260919.md`.
Classic's full-state movement persistence tests informed the transactional
ordering; its `BuildWorldBootstrapAfterHandshake` uses a different saved bootstrap
and portal restoration, so it was not copied into the current2A projection.
XJZ's position DTO is not proof of a packed wire layout. Current instructions,
not a legacy guess, determine the fields above.

## Verification

- Release build succeeds;25 selected core CTest suites pass.
- Combined existing regression run:139 tests in113.236s;136 passed and3
  OS-dependent symlink tests skipped. No failures. Separate evidence-management
  CTest suites were not included in the25 core-suite selection.
- Eight movement loopback tests pass, including fresh server-process restart,
  restored2A coordinates, new-connection ring reset, INSERT/UPDATE failure with
  no ACK, invalid batched-prefix rollback, obstacles and TCP fragmentation.
- Repository tests exercise migration preservation, ownership, stale snapshots,
  every stored field's bounds/types, overflow, injected after-write mutations,
  deferred commit failure and transaction cleanup.
- Service tests reject movement before readiness and external snapshot changes
  both during world entry and after binding. Invalid saved state is not reset.
- Live original-client UI/gameplay validation remains outstanding. Lua gameplay
  scripts and the C++/Lua responsibility split are unchanged.
- The existing movement lab database upgraded and the configured loopback server
  completed a2-second start/clean-stop smoke test with exit0 and Lua loaded.
