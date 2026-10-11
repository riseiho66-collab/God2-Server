# Saved consumable slots through S2C41 and C2S26

The current client C2S26 request includes a raw inventory slot byte; the
qualified native request producer and server codec preserve it. The recovered
S2C41 record contains item ID, slot and count. Previously the isolated
`diagnostic_world_supply` Application callback projected and admitted only
slot 0 even though `DiagnosticSupplyService` already validated consumable
slots 0..29. A potion saved elsewhere could not be used through this route.
Pinned original-code execution with the current MED02 rows for 3101 and 3107
independently emitted C2S26 with nonzero slot bytes 5 and 12; the focused
native producer test passed. This is producer evidence, not a physical UI use.

The default-off route now queries account-owned saved slots 0..29 together. Only rows
with the pinned item-source hash and an eligible current MED02 policy are
projected. Explicit count-zero tombstones are projected as such. Missing rows
are not interpreted as empty inventory; slots 30..49 are left to their separate
equipment semantics. All selected S2C41 records share one bounded world frame
after saved S2C24 resources. C2S26 reads its requested saved slot, then retains
the existing exact item, character ownership, resource baseline and atomic
inventory/resource transaction checks. No item is created or transferred.

The Release build passed. An isolated own-server socket test imported the
current 71-row MED02 declaration catalog and saved item 3101/count 2 in slot
5, item 3107/count 3 in slot 12, and a separate row in slot 30. The world
initializer projected exactly slots 5 and 12 in one S2C41 frame. Native-shaped
C2S26 requests for both slots changed HP 20/120 to 120/120 and MP 2/80 to
52/80; counts became 1 and 2, with distinct slot revisions 2. Slot 30
remained unchanged; subsequent C2S2E movement was acknowledged. SQLite
`quick_check` passed. The focused CTests passed 4/4.

This is server socket and persistence acceptance, not original-client UI
acceptance for slot 5 or 12. The client had previously accepted a physical
shortcut use of slot 0/item 3107. The CUSTOM-0016 recovery clamp/debit rule
and isolation gate remain. The persistent service on port 2592 and player
database were not changed.

During verification, `recovered_character_repository` exposed an older test
fixture error: it created a schema-16 database then called the current
repository create method, which requires the schema-19 `name_codepage`
column. The test now inserts its legacy character through the schema-16
columns, then verifies that migrating forward preserves the owner and
defaults the codepage to 950. No production migration or save value was
changed for this correction.
