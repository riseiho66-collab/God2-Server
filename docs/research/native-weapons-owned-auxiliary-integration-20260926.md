# Native weapon definitions and owned role auxiliary integration

## Scope and authority

The current native weapon reader yielded 630 WPN and 629 TWP definitions. These
are original **definitions**, not 1,259 owned/equipped player instances. The
original 20-byte instance generator, item admission requirements, equipped final
stat formula and WPN-to-HeroDoll weapon selector remain OPEN. No live weapon,
auxiliary stat, item or equipment grant is made by this release.

Current client SHA256:
`6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98`.
Original mapped image SHA256:
`149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
Source `Data2/Patch/Comm/gamedata.csvZ` SHA256:
`70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731`;
decoded SHA256:
`75c3c37947a64b0917fbf8e546884d9bf893fe6a606d3e2b8f3b1857966b1815`.

## Formal storage and C++/Lua use

Migration27 adds `native_weapon_sources`, `native_weapon_rows` and
`character_role_auxiliary_snapshots`. The weapon import retains original CP950
record bytes, source section/key/index/line/decoded offset, raw record hash and
the native loader's 396-byte parsed record plus hash. Loader RVA59420 and lookup
RVA59A60 are retained. The native definition extraction precedes ROM binding:
initial group0/actionFFFF must not be called the final resource binding.

`import_native_weapons.py` supports the independently extracted cache in
`artifacts/research/native-weapons-20260926/records.json`, but still verifies the
current executable, compressed/decoded source, native image and complete
length-prefixed catalog fingerprint:
`1a6e35c37950d5edada081b184c6b7f6d1f101929d4ccf46004747c8740cde26`.
Conflicts/partial rows reject before overwrite; rollback and full readback are
required. Foreign caller transactions are rejected without closing them.

`NativeWeaponCatalog` validates the complete catalog before returning a record.
It is available from `SqliteDatabase`, checked during server startup, and exposed
to Lua as `native_weapon_catalog(item_id)`. Lua receives a fresh value snapshot,
not live state. Missing keys return nil; invalid selectors and unavailable or
corrupt sources fail. Lua reload preserves the host reader. The authority remains
`NATIVE_PARSED_DEFINITION_ONLY`; no numeric source column is silently a combat
formula or a player instance.

## Connected 2C route

The exact logical record is opcode2C plus60 body bytes. Native consumer4E6600
returns through4E6710. Body DWORD offsets0/4/8/12 feed low WORD modifiers at
actor88/8A/8C/8E. Body36/40 feed positive/negative mask WORDs at actorB8/BA.
The native refresh applies signs; positive bits take precedence over negative
bits. Body44/48/52/56 feed actor98/94/A0/9C respectively:
physical defense/physical attack/magical defense/magical attack.

`RecoveredRoleAuxiliary` retains **all61 original bytes**, including opaque
bytes, masks, padding and high DWORD bits. It must not encode already transformed
actor fields as though they were raw wire values. No signedness, rounding,
equipment multiplier or final combat-value formula is inferred here.

CUSTOM-0045 is the owner/CAS persistence and restore policy, not original stat
generation. Repository reads require the owning account/character, exact codec,
current client pin, revision, bounded provenance and allowed origin. Writes use a
single transaction with CAS and full readback; pending battle rejects. No network
message lets a client submit arbitrary stats. No raw2C row is auto-created.

On fresh completed-world admission, Application loads the owned snapshot before
emitting records, sends the saved base role22/24 first, then raw2C, then owned
companion records and journal. This executes once per world, outside battle.
Missing auxiliary rows send nothing. Raw2C itself does not change role HP/MP or
God memory; native22 has separate HUD/resource side effects described in
`current-weapon-attributes-snapshot-20260926.md`.

## Evidence and applicable limits

- Native original-consumer evidence: 8 role22 cases, 512 complete2C cases,
  258 weapon unpack cases and20 quality/level cases. C++ codec output was also
  consumed by the native2C path. These prove consumer arithmetic/layout and
  preservation, not an original server formula.
- Native weapon appearance oracle:49 cases. DA15-byte character appearance is
  distinct from GodDoll36/37. WPN-to-HeroDoll mapping still missing.
- Native equipment projection oracle:72 transitions,73 UI28 requests,
  16 equipment3C cases and90 sound entry calls. Real WPN ROM binding yields
  group41/action0/1 for WPN1/2; harness relocates ROM chunks and does not perform
  file loading/blit or sound playback. Synthetic 20-byte tails are not native
  legal generated instances. These do not close runtime equipment gameplay.
- `test_native_weapon_catalog.cpp`: real pinned records, corruption/partial/
  empty/unknown rejection, caller transaction/read-only handling, actual DB Lua
  snapshots/invalid arguments/nil/reload. Input DB bytes remain unchanged.
- `test_import_native_weapons.py`:9 tests in normal and `-O`, including real
  source/native-parser samples, source/cache corruption, rollback/idempotence,
  read-only import rejection and imported DB -> C++/Lua integration; no skips.
- Repository test covers wrong owner, CAS, pending battle, invalid provenance,
  abort-trigger rollback and real-file close/reopen. TCP test uses three isolated
  server starts: missing row emits nothing, another character's row never leaks,
  full raw high-bit/mask data returns once and restart preserves all61 bytes and
  resources. These are synthetic test operands, not original combat values.
- Final same-candidate hidden original-client acceptance:
  `artifacts/playtests/private-role-auxiliary-20260926-02/run-result.json`.
  Candidate SHA256 `da47cff7b2d76716dfe5471ea494e80861b6cf8e918d5e044fe4fe80432b5041`.
  Actual read-only actor state is modifiers2/3/4/5, physical77/56, magical99/88,
  unchanged after movement/clock, HP/MP52/120/26/80 unchanged. Journal restoration
  and map close/reopen also accepted. These values are expressly
  CUSTOM_TEST_NOT_NATIVE. No God fixture exists in this run; actual live God
  preservation is not claimed. Input desktop remained Default; client unchanged.

## Formal release

`tools/operations/native_weapons_auxiliary_release.py` stages a SQLite backup,
migrates/imports the exact native definitions, tests the staged C++/Lua reader,
requires final same-candidate hidden acceptance and compares all pre-existing
tables. Apply refuses an active player connection or changed saved state. Config
and client remain unchanged; only schema history extends and the three new tables
are added. Backup/rollback restores DB and EXE together on release failure.

Release folder: `artifacts/releases/native-weapons-auxiliary-20260926-01`.
Actual activation and source/save preservation are recorded in its
`verification.json`; staging alone is not release proof. Production auxiliary
row count must be0. Existing accounts/characters/resources and Kunlun birthplace
configuration are preserved.

Applied and verified: schema27, WPN630/TWP629, unchanged pre-existing player
tables, config/client unchanged, active EXE matches accepted candidate,
production auxiliary rows0. Service PID21144 listening on loopback2592 at
verification. The focused final CTest gate passed12/12 after recompiling
god2-tests: source reader/import, raw codec/repository/TCP, Lua/database/config,
owned companions/player restore, Kunlun birthplace/movement.

## Next native recovery and integration

Trace the equipped instance producer and authoritative28 state transition, using
the current UI49A330 and complete3B/41/3C consumers plus20-byte metadata storage.
Trace DA461270/local503D30/remote4FC990 for WPN-to-HeroDoll selector authority.
Recover final-stat after-state generation separately from tooltip unpacking.
Then connect atomic owned bag/equipment mutation and emit the native accepted
inventory/appearance/stat records. Full equipment playability remains incomplete
until that route and persistence are accepted by the current client.
