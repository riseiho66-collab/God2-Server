# Door proposal before movement commit (2026-09-23)

The default-off CUSTOM-0025 town/indoor doorway route previously committed a
movement to SQLite and advanced the in-memory movement ring before it asked Lua
for a door proposal. A malformed Lua result or invalid scene pair could then
reject the world callback without sending the already prepared movement ACK.
The persisted position and client queue would diverge.

`RecoveredMovementService::move_committed` now offers a precommit callback. It
validates the entire native movement batch and constructs ACKs, then supplies
the actual active start and target coordinates before any position write or
ring advance. Application asks Lua for CUSTOM-0025's plan there and verifies
the source-pinned destination cell and scene pair. A rejected plan leaves the
move uncommitted. Successful movement still commits once before ACK publication;
the separate later tick emits the scene transition, as in the existing native
doorway capture.

The old Application gate also required an existing SQLite position row to
evaluate the doorway. The first movement from the configured initial town
position has no such row, so stepping directly onto the entrance silently
missed the door. The precommit preview supplies the active start coordinates
without requiring a prior save. This is a service and custom-policy correction;
the doorway trigger, destination and arrival policy remain CUSTOM-0025, not a
recovered official gameplay rule.

Verification:

- `recovered_movement_service` injects a precommit exception and confirms no
  database row or queue sequence is consumed, then retries the same native
  movement successfully. A malformed path never invokes the callback.
- `diagnostic_door` checks the first unsaved town step and the repeated
  town/indoor cycle through the Lua precommit proposal. Destination checks
  reject unsupported scene and out-of-bounds coordinates.
- `test_recovered_movement_server.py` starts an authenticated character with
  no saved position at town86,71. Its first world tick receives both town
  NPC records without writing a position. Its first native-format C2S2E step
  to86,70 receives S2C5D ACK1, then another tick receives S2C61 for indoor16,19. SQLite
  advances from town revision1 to indoor revision2, and the scene context
  receipt is accepted. The test uses reconstructed original-format socket
  packets, not physical original-client input or rendered acceptance.

The first tick had a related defect: guide projection required a SQLite
position row, although the server had already bound the initial location in
memory. `current_location` now returns the authenticated world-ready location
when the database still matches the binding's saved baseline, including an
unsaved initial location with revision0. Town guide projection, nearby NPC
opening and quest confirmation use this bound location. External position
writes and pending transfers invalidate it. Other diagnostic NPC routes retain
their prior saved-position rule.

A second socket case starts at town110,70 with no saved position and imports
the pinned 2,014-row native quest display catalog into its isolated test DB.
The first tick delivers NPCs1606/1607, C2S37 opens NPC1606, and C2S85
confirms the first CUSTOM-0021 guide stage. The client receives S2CDB journal
value0x10001, SQLite records stage1/revision1, and no position row is created.
The later full three-stage and reconnect continuation is documented in
`fresh-town-reward-20260923.md`.
An earlier test attempt without the catalog was correctly rejected as
`Incomplete quest catalog`; it was a fixture setup error, not a bypass of
source validation. None of this establishes original quest rules or physical
client UI operation.

Existing original-client automatic doorway and reconnect captures remain the
prior native evidence for a saved character. A fresh original-client visual
run from an unsaved town character is still needed for that broader claim.
