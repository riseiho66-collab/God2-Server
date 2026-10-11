# Current MED02 recovery declarations: SQLite and C2S26

## Source and limits

The active Taiwan client `Data2/Patch/Comm/gamedata.csvZ` has compressed SHA256
`70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731`
and decoded SHA256
`75c3c37947a64b0917fbf8e546884d9bf893fe6a606d3e2b8f3b1857966b1815`.
Its corresponding native image SHA256 is
`149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
The current client MED02 loader at RVA `0x59420` and lookup at `0x59a60`
identify 100 item records. Exactly 71 have a parseable positive HP or MP
recovery amount in the original tooltip and the observed normal-use/hotkey
flags. The remaining 29 are unresolved, not assumed to have no effect.
Examples: item 3101 declares HP 100; 3107 declares MP 50; 3113 declares
HP 500 and MP 150. These values are **NATIVE_CLIENT_TEXT**, not proof of
authoritative server effects or client UI use acceptance.

## Connected route

Migration 21 creates `native_med02_recovery_declarations` with source record
index/line, raw record and tooltip bytes, record SHA256, declared amounts and
use flags, tied to `native_data_sources`. The pinned importer refuses a changed
client source or existing conflicting rows, inserts all 71 declarations in one
transaction and checks SQLite integrity. The C++ catalog verifies the imported
source identity and count before lookup.

The default-off `diagnostic_world_supply` path now uses this same catalog for
owned inventory projection and C2S26 request admission. Without an imported
catalog it retains the previous two-item diagnostic fallback. A qualified
request must still match a world-ready owned character and exact saved slot;
the service uses the native C2S26 shape and persists the inventory/resource
change atomically before the S2C41/S2C24 response. Its living-only behavior,
HP/MP cap and conditional one-item debit remain **CUSTOM-0016**. No item grant
or production activation was added.

## Verification on isolated state

`native_supply_catalog`, `import_native_med02_recovery`,
`same_session_battle_supply_server`, `diagnostic_supply` and `supply_lua`
CTest targets passed 5/5 in the Release build. The imported catalog contains
71/100 MED02 declarations. A separate C++ lookup checked 3101, 3107 and
3113 and rejected an unmatched record. The own-server socket test seeded an
owned item 3113 count 3, HP 20/120 and MP 2/80, authenticated and entered
the world, sent an original-shape C2S26 request, received S2C41/S2C24,
then moved again. SQLite saved HP 120, MP 80, count 2 and revisions 2. The
declared HP 500/MP 150 amounts explain the resulting clamp; the clamp and
debit are still custom rules. The isolated database passed `quick_check` and
foreign-key checks. Comparison against the pre-import backup found no change
to the 21 pre-existing tables.

This qualifies one additional socket and persistence case, **not** general
original-client UI acceptance for 71 items. The original-client UI action for
3107 had previously shown its saved slot, but did not produce a C2S26 in the
private UI run; see `private-potion-ui-20260925.md`. The persistent service on
port 2592 and its player database were not changed by this work. Next native
qualification is to observe ordinary client use actions and complete the 29
unclassified records before broad item activation.
