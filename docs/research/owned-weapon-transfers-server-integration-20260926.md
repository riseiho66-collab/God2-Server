# Owned weapon instance28/24 server connection

Date2026-09-26. This connects the current client's weapon inventory requests to
owner-qualified whole-instance persistence and native slot/icon responses. It
does **not** restore complete equipped-character gameplay. Production equipment
remains disabled until appearance, final-stat generation and legal item admission
are qualified. The original objective remains active; this is a required
inventory/transport part of it, not a replacement completion definition.

## Proven original boundaries

Current executable SHA256:
`6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98`.
Source definitions are the pinned630 WPN/629 TWP formal catalog documented in
`native-weapons-owned-auxiliary-integration-20260926.md`.

Native49A330/96550/132E0 produces five-byte `28 key:u16 source:u8 01`;
the trailing1 is not an equip/unequip boolean and there is no destination.
Native496610 produces `24 source:u8 destination:u8`. Ordinary weapon slot is34;
the ordinary bag is0..29. Other equipment/pet/God/egg/talisman domains are not
folded into this route.

Native498DD0 copies a full20-byte instance from `3B count slot opaque:u16
instance[20]`; native4991E0's `41 key:u16 slot:u8 count:u8` only changes count and
lowWORD key. Clearing retains18 inactive bytes. The absolute projection used
here clears both affected slots before sending each nonempty complete3B+41.
No subtractive3C is needed and no fake occupied item clears pending. Native
equipment3B clears pending, while unequip can leave pending1; subsequent genuine
double-click still produces28 and equips normally.

See `current-equipment-instance-projection-20260926.md` and
`current-weapon-fresh-tooltip-20260926.md` for full original consumer/producer
execution and resource/formatter boundaries. WPN2 is **砍刀**; the older icon
projection report's 柴刀 label was a text error, not a different numeric item.

## Storage and authoritative policy

Migration28 adds `character_weapon_slot_metadata`, with a composite foreign key
to the existing `diagnostic_inventory_slots(character_id,slot)`. The scalar
occupancy remains authoritative; no duplicate inventory or empty-slot inference
is introduced. The metadata row retains all20bytes, matching scalar revision,
origin/provenance, current source/client pins and CUSTOM-0046.

Qualified occupied WPN/TWP must have count1, native definition flag04, exact
metadata lowWORD matching its scalar key and origin NATIVE_CAPTURE_VERIFIED or
CUSTOM_TEST_NOT_NATIVE. A missing metadata row for a known weapon is an error;
occupied map/MED rows are not converted to weapons. A pre-existing explicitly
empty scalar row may have no metadata. No acquisition/provisioning method exists
in this repository. The live release creates no instance or metadata rows.

`SqliteWeaponSlotRepository` provides owner-bound lookup, consistent saved-slot
reads and atomic whole-slot transfer/swap. Expected scalar and metadata versions
must agree. Pending battle, stale state, malformed/orphan metadata and wrong
owner reject. Both physical slots advance their own revisions; occupied
instance bytes and provenance travel together. Clearing only changes lowWORD
and occupancy and retains the source's inactive tail. Projection preparation
and full readback execute before commit; callback or SQL failure rolls back
both scalar and metadata rows.

The new trigger retires **only EMPTY_SLOT_POLICY** overlays when another scalar
policy reuses an empty cell. It never deletes an occupied instance. This keeps
map/MED/reward policies compatible without stale metadata revisions; weapon
transactions preserve their captured tails and upsert the new metadata in the
same transaction.

CUSTOM-0046 is the unclaimed original-server policy:

- Bag-source28 equips into an explicitly owned34, swapping its existing weapon.
- Source34 unequips into the lowest explicitly owned empty bag cell. Missing
  cells are never treated as empty. No capacity means no mutation.
- Weapon bag24 moves/swaps complete instances; no stack merge. Empty/same-cell
  requests only reproject, retaining versions.
- Admit only one28 or one24 with ticks/optional trailing1F00. Mixed operations
  preflight before any callback or position change. Reject unsupported requests
  without fake state updates. Nonweapon24 in weapon-only mode is silent/alive,
  rather than falling into a disabled scalar callback that closes the session.
- Restore saved slots once on fresh world admission, before future input, with
  no default item. The optional route requires authenticated world/movement,
  complete source catalog, no battle/pending transfer and matching owned state.
- No DA,2C,22/24 resource or invented combat update is emitted by transfers.

Automatic destination selection is explicitly custom. The native client can
display/equip the synthetic test item, but this does not establish original
level/class/gender restrictions or legal original item generation.

## Own-server verification

`tests/test_weapon_slots.cpp`: formal migration28, owner/CAS/corruption,
full20bytes/provenance swapping, inactive tails, mixed map/MED exclusion,
callback/SQL/readback-trigger rollback, pending battle and close/reopen.
`tests/test_owned_weapon_transfer.cpp`: destination policy, exact native
projection, wrong key/capacity/same-cell handling and frame preflight.

`tests/research/test_owned_weapon_transfers_server.py`: four independent
background server starts, six committed transitions and12 silent/alive
rejections. Covers initial snapshot admission, owned28/24 transfer, exact3B/41
records, restart, full bag, wrong key/domain, other owner, duplicate/mixed
requests, unchanged movement state on rejected mixed input and scalar map reuse
of an inactive overlay. Resources, role/auxiliary, God/pets and other characters
are preserved. These are isolated synthetic operands, not original item grants.

Final same-candidate hidden actual-client acceptance:
`artifacts/playtests/private-weapon-transfers-20260926-03/run-result.json`.
Candidate SHA256:
`1977769ff02076f0653b72dba7722dc60b54b5933cad7185b9f30112f6c0535b`.
Actual native double-click sequence: bag0→34, bag1↔34,34→lowest empty bag0,
bag0→34. All31 explicitly owned slot records,20-byte instances, versions,
provenance and icon binding agree after each step. Each step hovers a different
weapon first, then the target: native cache changes, tooltip widget is open with
renderer and icon matches bound definition/action0 or1 with real image/palette
pointers. Fresh original formatter tests separately validate exact CP950 strings
and levels for both source definitions.

Native pending states are0/0/1/0, matching the complete original consumer oracle.
God/pet/role values and resources remain unchanged in this actual client fixture;
this run includes a God rather than borrowing the earlier noGod acceptance.
Movement/clock and client-alive checks also pass. Input desktop stays Default,
no screenshots or client memory writes are used, and sourceDB/client hashes are
unchanged. The first hidden01 failed due to a read-only inspection pointer error
(B2D40 is an inline pointer array), which was repaired; hidden02 and final03 pass.

Both20-byte test weapons are labeled CUSTOM_TEST_NOT_NATIVE. Their fresh tooltip
uses ordinary weapon class1; this is accepted display input, not original server
instance generation or final damage. A native tooltip range is not a damage
formula, and successful icon updates do not establish a world-weapon appearance.

## Formal installation and remaining work

`tools/operations/owned_weapon_transfers_release.py` verifies final same-candidate
acceptance, stages migration28 on a backup, checks all original tables/trigger
preservation and sources, and installs code/schema with rollback. Configuration
is unchanged; `world.owned_weapon_transfers.enabled` remains absent/false in
production, and metadata row count remains0. Formal release evidence is
`artifacts/releases/owned-weapon-transfers-20260926-01/verification.json`.

Applied verification: schema28, all pre-existing player tables unchanged,
metadata rows0, production equipment disabled, config/client unchanged, active
binary identical to final accepted candidate. Service PID22224 listened on
loopback2592 at verification. Focused CTest17/17 passed, including native source,
role auxiliary regression, companion preservation, scalar inventory, new weapon
repository/policy/TCP/fresh-tooltip, config/database/Lua and Kunlun movement.

Before complete production equipment is enabled, recover the WPN-to-HeroDoll
selector used by DA and authoritative equipment restrictions/final2C after-state
generation. Connect those to the same atomic owned transition and revalidate
wear/swap/unequip/relogin appearance and battle attributes. Keep the current
full-instance transport/persistence invariants; do not solve the gap by dropping
metadata, fabricating stats or relabeling synthetic instances as native items.
