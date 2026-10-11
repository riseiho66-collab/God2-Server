# Ordinary armor owned-instance storage proposal — 2026-10-02

Status update: the original proposal below is retained as design history.
CUSTOM-0066 owned-instance repository/service is now implemented and tested but
**inactive**; Application wear/remove integration and live armor acceptance remain
open. Migration41 installs only the native source catalog, not this instance
schema. See [current release and frontier](native-armor-definitions-20261002.md).
The initial review itself performed no runtime operations.

## Current authoritative boundaries

- `src/db/Migration.cpp`, migration11: `diagnostic_inventory_slots` owns scalar
  occupancy for physical slots0..49. Its key is `(character_id,slot)`, with
  item WORD, signed-positive native count domain0..127, physical revision,
  source hash and fixed `CUSTOM-0015` provenance. No armor service may introduce
  a second item/count authority for these same positions.
- Migration28: `character_weapon_slot_metadata` stores full20-byte weapon
  instances and shares the scalar revision. Its SQL CHECK explicitly permits
  only bag0..29 and weapon34. The existing
  `retire_empty_weapon_overlay` trigger deletes only `EMPTY_SLOT_POLICY`
  overlays after a scalar change. Do not widen this table, reinterpret occupied
  WPN/TWP rows or replace its trigger.
- `src/db/SqliteWeaponSlotRepository.cpp`: `domain()` is bag0..29 or34;
  occupied qualified weapons require complete instance metadata. Reads have a
  consistent ReadScope. Writes CAS both scalar and metadata; its current move
  checks the two affected cells, pending battle, callback preparation and two
  readbacks. The new armor repository may use a stronger full-domain snapshot;
  do not rewrite the accepted weapon repository to match it.
- `src/handlers/OwnedWeaponTransferService.h`: `slot()` likewise permits only
  bag0..29 or34. Current weapon28/24 handling and destination policy remain
  unchanged. `src/core/Application.cpp` qualifies only WPN/TWP for this route.
- `src/db/SqliteTeleportGemRepository.cpp`: bag-only full-instance metadata is
  another independent overlay and explicitly refuses weapon-overlay conflict.
  Armor must observe this table as well; scalar occupancy alone does not prove
  an empty/unclaimed metadata domain.
- `src/db/SqliteBankItemsRepository.cpp` and the Application bank qualifier
  admit scalar MED02 items, not arbitrary full-instance armor. Existing bank,
  trade, scalar moves/discard, pet lifecycle and weapon methods gain no armor
  capability merely because armor can now occupy a bag cell.

Current native `28 key:u16 source:u8 01` has no destination. The qualified
consumer pair is clear41, occupied full3B, absolute41; native498DD0 copies20
bytes and4991E0 changes count/low key. Ordinary proposed armor scope is physical
30..33 only. Existing source labels are in
`docs/research/current-player-equipment-frontier-20260926.md`; **labels alone
are not a complete EQU/TEQ-to-slot mapping or an equipment stat formula**.

## Separate schema, one physical occupancy authority

Proposed new table: `character_armor_slot_metadata`, composite FK to existing
`diagnostic_inventory_slots(character_id,slot)`, PK on the same pair. Fields:

| Field | Required contract |
| --- | --- |
| character_id, slot | Owned character; slot0..33 only (bag0..29 or armor30..33). |
| logical20 | BLOB exactly20 bytes, preserved losslessly. |
| revision | Positive INTEGER, equal to the parent scalar physical revision. |
| origin | `NATIVE_CAPTURE_VERIFIED` or `CUSTOM_TEST_NOT_NATIVE`; no relabeling synthetic instances as original item generation. |
| provenance | Nonempty bounded UTF-8 bytes, no NUL; identifies actual instance evidence. |
| source_sha256 | Qualified current definition source, not arbitrary caller input. |
| mapping_evidence_sha256 | Immutable accepted mapping-oracle/catalog artifact. |
| client_code_evidence_sha256 | Qualified native code evidence; do not copy the historical weapon executable hash and present it as current. |
| design_id | Root-assigned stable custom storage/selection-policy ID, after review; not a guessed number in this proposal. |

Use **occupied-only armor overlays**: a row must describe scalar count1 with
key==logical20 lowWORD and an oracle-qualified EQU/TEQ class. An empty scalar
has no armor overlay. On whole-item movement into an empty cell, move all20
bytes and provenance to the destination; delete the source armor overlay with
its exact expected revision and bytes. Clear41 is sufficient for the empty
source, without manufacturing an empty20-byte item. The occupied item retains
all20 bytes; the native client's inactive tail in a cleared cell is not an
extra persistent item or capacity. This also avoids introducing a new inactive
armor overlay into the existing weapon/gem empty-cell policies.

Constructors/load are read only. Explicit schema installation adds empty
tables/guards only and does not create armor instances, duplicate bags, mutate
old saves or invent missing scalar cells. Separately reviewed capacity
allocation, if later needed, may insert **only missing empty scalar30..33** with
owner/pending-battle/full-readback checks; it may not reset, upgrade or repair
present rows. Baseline and scope must be recorded. Until that allocation is
accepted, missing rows mean unavailable capacity, never implicit emptiness.

### Overlay exclusivity

At most one **occupied full-instance overlay** may claim a shared bag cell.
Armor attach/load/plan/commit must check weapon and teleport-gem overlays in the
same consistent snapshot. Occupied foreign overlays always reject. Existing
weapon `EMPTY_SLOT_POLICY` is distinguishable from an occupied foreign item:
only a valid empty scalar with matching weapon revision/origin may be selected
as an empty destination; the existing scalar-update trigger retires that
inactive weapon overlay. Never delete an occupied weapon or gem overlay.

For SQL-level mutual exclusion, propose additive BEFORE INSERT/UPDATE guards
on the new armor table and reciprocal BEFORE INSERT/UPDATE guards on existing
weapon/gem metadata: abort whenever another occupied metadata family claims
the same scalar key. Armor insertion occurs after its scalar update and after
the existing empty-weapon trigger has run. Do not alter existing table CHECKs,
trigger bodies or origin labels. Pre-existing collisions must be detected and
reject activation; adding a guard is not permission to clean up old data.

These reciprocal guards are **proposed additive constraints**, not installed
here. They require regression proof for all legitimate weapon/gem/scalar
writers before release. If their valid transient write order cannot be proven,
do not install an incomplete one-sided mutex and claim global exclusion.

## Snapshot and atomic commit

Proposed `ArmorSnapshot` binds account+character and includes:

1. Complete30 scalar bag cells, plus all four required armor scalar30..33.
   Require contiguous present bag capacity; absent armor cells remain explicit
   unavailable capacity until separately provisioned.
2. Exact armor overlays throughout0..33, and exact observed weapon/gem overlay
   presence,20-byte contents, revisions and provenance for the30 shared bag
   cells. Nonarmor occupied scalar cells remain protected snapshot observations,
   not eligible armor targets. Orphan, duplicate-family, wrong-source,
   scalar/metadata-revision mismatch and unqualified armor-in-armor-slot deny.
3. Protected scalar34..49 present/absent/value observations. These are never
   armor destinations or allocation targets. Capture the current protected
   overlay observations for34 and other known domains without redefining their
   storage ownership. They provide readback protection against trigger damage.

Load under BEGIN/read-only snapshot when not already in a transaction. The
commit must start `BEGIN IMMEDIATE`, recheck the selected owned character, ready
world/scene lease in the service, no pending battle, and exact complete expected
snapshot. Full-snapshot CAS must detect a changed *unused* bag cell, destination
choice changes and foreign overlay attachment, not only the two moved rows.

Pure plan changes exactly two physical scalar slots and their armor overlays.
Both physical revisions advance from their own original position by1, with
signed SQLite INTEGER overflow checked before writes. Item bytes/origin/source/
instance evidence travel together; revisions do not travel with items. No merge,
stack arithmetic, grant or guessed generation occurs. An occupied destination
may swap only another individually qualified armor instance admitted by the
same target-class mapping; never swap weapon/MED/map/gem/pet across this route.

Prepare complete native inventory response and any independently qualified
appearance/stat extras **before COMMIT**. In particular, preflight the entire
frame and mapping/readback failures before exposing after-state to the socket.
Write two scalar CAS rows, delete/update/insert armor overlays with expected
full fields, write a unique server receipt if that design is selected, read
back the receipt and complete snapshot, run preparation, and read back again
after preparation. Only then COMMIT and publish already prepared response.
Any SQL fault, ignored write, changed receipt, third-cell/foreign-overlay
trigger mutation or preparation error rolls back the complete transaction.

If receipt persistence is used, a separate empty
`character_armor_transfer_receipts` table should store unique64hex server token,
owner, operation intent, native source/key, chosen destination, and complete
before/after physical revision+instance/provenance evidence. Do not use raw
client tail01 as a receipt, replay token, split quantity or destination.

## Scoped service and routing

Add a separate armor service; do not generalize/rewrite weapon code.

- `28` source30..33 is an armor operation candidate. Validate the entire batch:
  one request, ordinary idle ticks, and at most one observed final1F00; duplicate
  or mixed mutations deny before any commit. No battle or unready-world route.
- `28` bag0..29 belongs to armor only when the **saved scalar+full armor overlay
  and mapping** qualify it. Do not intercept all bag28 and thereby suppress
  existing weapon28 or pet requests. A claimed EQU/TEQ key with mismatched
  owned state is an explicit armor rejection, not fallback to another grant.
- The mapped equip destination must be30..33. Bag→equipment exchanges only
  with an empty valid destination or same target-class qualified armor.
  Unequip chooses the lowest explicitly owned empty bag cell as a named custom
  selection rule; wire28 itself does not prove the original choice. No empty
  bag means no mutation. A foreign occupied bag cell is never a candidate.
- Keep current weapon24/28, weapon34, bank63/64/65 and pet42..44 routes intact.
  A later armor bag24 extension would need its own separately qualified route.
  Initially reject24 whenever an occupied armor endpoint is involved, before
  scalar fallback; preserve all existing nonarmor24 behavior.
- Cross-family destination rejection is silent/alive or the independently
  qualified generic equipment rejection, never an invented success or a false
  no-password/auth failure. Do not send fake item3B to clear native pending.

The armor-specific dispatch should sit immediately before the existing weapon
transfer block in Application, with a negative/fall-through result distinct
from handled-rejected. Existing weapon classifier must continue to receive
every request that the armor classifier did not own. Mixed-frame preflight is
required even when the first record belongs to a different existing domain.

## Login restoration and shared bag projections

The current first owned-world snapshot block loads player resources before
deity/pet binding, then restores weapon slots, gem slots and companions.
Preserve this order and all frozen authentication/chat/IME behavior. Add a
separate armor snapshot load and `owned_armor_projected` lease; restore only
occupied armor bag cells and explicitly present armor30..33, once after world
admission. Validate the **complete** armor snapshot/projection before sending
any of it. No blanket clear of all30 bag slots.

Current weapon restore already omits occupied nonweapon cells when they lack a
weapon overlay. Preserve that code. Generic bag/supply restore passes at
Application's saved town-bag and diagnostic-world branches must explicitly
defer qualified owned armor cells to the armor projector. The diagnostic supply
branch currently throws on unqualified saved items; failing to add a narrow
armor skip there would break login for an armor-bearing bag. The narrow guard
must use owned valid overlay/catalog qualification, not a permissive item range
or arbitrary client claims. It must not broaden scalar MED/map admission.

Disconnect/logout clear only the new session projection lease. They do not
delete durable armor or affect existing banker, trade, weapon, pet or chat
leases. Relogin restores exact instance bytes and physical revisions without
consumption or new instance attachment.

### Concrete cross-system activation blocker: full-bag resynchronization

Current `Application.cpp`'s `bag_slot_projection` rejects every occupied cell
outside the scalar MED/map/material qualifier. This is **not** only a transfer
eligibility check: the callback is also passed to `RecoveredTradeService` and
`RecoveredBankItemsService` for canonical full-bag synchronization. Trade
opening preflights all30 cells; cancel/disconnect and successful settlement
restore all30. Bank opening projects vault only, but rejected item requests
restore all30 bag cells. Adding an armor item to a bag therefore affects these
existing operations even when the player never offers/deposits that item.

Do not activate armor and conceal this by silently excluding these players
from otherwise valid MED/money operations, clearing armor, serializing its ID
with18zeros, or broadening bank/trade item eligibility. A production integration
requires a separate owner-bound canonical bag projection adapter that resolves
an unchanged cell as scalar, qualified weapon full20, qualified armor full20
or qualified gem full20 while preserving the existing transfer qualifiers.
Use explicit account+character and the expected scalar revision/item/count;
the current `(slot,scalar)` callback alone lacks owner context. Do not derive
ownership from an ambient mutable "current session" or from an item ID.

The adapter must load complete matching metadata consistently, prepare all
records before the relevant transaction commits, reject stale/ambiguous
overlays without partial output, and retain protected full-instance rows through
the existing scalar transaction. Any required additive callback-context wiring
needs its own reviewed regression evidence; it is not implemented in this
proposal. Full-bag trade and bank rejection/cancellation with an unchanged armor
item present are explicit activation gates. The same existing limitation for
other non-scalar instances must remain honestly scoped until qualified.

## Implementation gates after mapping delivery

Before implementation/activation: qualify actual EQU/TEQ fields, native target
class30..33 and any family exclusion using matching current code/source; pin
the catalog and instances; assign the new design ID. Do not use text labels or
category modulo arithmetic as the mapping.

Required meaningful regressions: owner mismatch; full snapshot unused-cell and
foreign-overlay stale changes; same-class armor swaps with differing instance
bytes/revisions; cross-weapon/MED/map/gem/pet rejection; complete bag/full bag;
integer boundaries; second-write and receipt/readback corruption rollback;
prepare throwing after writes; original weapon/gem/scalar empty-cell reuse;
bank/trade/pet/weapon/protected slots unchanged; relogin exact restoration;
both original TW/CN clients against our server. Run the unchanged frozen-chat
baseline before promotion.

Inventory/icon persistence alone does not complete playable armor. Native
3B/41 does not recalculate role stats or update actor appearance. Final armor
activation must also qualify actual wearer restrictions,本人/旁觀者外觀 and
authoritative stat after-state through their actual appropriate consumers;
do not replay first-entry22/24 as a guessed mid-world equipment update or
silently derive combat values from descriptions.
