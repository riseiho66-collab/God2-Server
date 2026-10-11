# Owned armor transport — 2026-10-02

## Authority and current boundary

This continues the source-only release documented in
[native armor definitions](native-armor-definitions-20261002.md). The source
catalog contains 692 EQU and 662 TEQ definitions from the independently pinned
Taiwan `70a4` source; no retired Classic corpus is used.

The runtime candidate is
`artifacts/research/native-armor-transfer-20261002/candidate-01/god2-server.exe`,
SHA256 `2696f4efc90648aac47df97e5dbbe80cfd1434cac936f2db36c5ec98ff6ad3d3`.
Its 20 runtime source hashes are recorded in `candidate-01/contract.json`.
The current client remains `c5d8f79baa36879851703ac05d2b5caddf44a907677f7de114f568eeaf14f575`.

CUSTOM-0066 qualifies owned instance transport, not native item generation,
original role admission, final equipped attributes or appearance generation.
Its config key is `world.owned_armor_transfers.enabled`, default false. Enabling
requires authenticated recovered world entry and movement, with mock login off.
No catalog import, migration, constructor, login or equipment request grants an
item or silently allocates missing inventory capacity.

## Connected runtime

Migration 42 adds an occupied-only `character_armor_slot_metadata` table and six
reciprocal collision guards against weapon/gem overlays. It retains existing
scalar storage, source provenance and physical slot revisions. Readers cannot
install schema or grant items. EQU must use instance family 2; TEQ must use 26.
This stricter per-source family check is a server consistency policy: the native
lookup masks family flags and does not establish an original admission rule.
The retained upper instance flags are not assigned invented meanings.

| Route | Verified connection | Remaining scope |
| --- | --- | --- |
| C2S 28, bag to equipment | Owned whole-instance equip/same-part swap to source-classified slots 30–33 | Original admission, stat and appearance generation |
| C2S 28, equipment to bag | Owned unequip to the lowest explicitly owned empty bag cell; full bag refusal | Destination selection is CUSTOM-0066 policy |
| C2S 24, bag to bag | Empty move or occupied whole-instance swap, including differing armor parts | No merge or cross-category move |
| S2C 41 / 3B / absolute 41 | Clear then full 20-byte replacement and absolute count | Instance bytes are preserved, not synthesized |
| Authenticated world restore | Saved full bag and armor slots, independent of player-resource availability | No appearance/stat grant |
| Bank/trade bag projection | Explicit owner and before/after scalar snapshots; full weapon/armor/gem bytes | Original eligible MED/money rules remain in force |

Application classifies armor before applying armor projection/transaction
conditions. Non-armor requests retain their existing routing. Mutations require
world readiness, an owned current location, no active battle/trade or pending
scene/island transition. Complete framing is checked before mutation. Repository
preparation, owner/snapshot CAS, pending battle checks, two physical revisions,
projection and full readback occur before commit; failures roll back atomically.

Bank and trade receive immutable, explicitly owned proofs before response
projection. The repository verifies all observed scalar and overlay state after
BEGIN and again after writes/receipt/readback. Trade verifies both players.
Unchanged full instances are rendered intact; only already eligible plain scalar
changes are permitted. This does not make armor, weapons or gems eligible for
banking or trading.

## Original-client acceptance

`artifacts/playtests/private-native-blackbox-armor-transfer-20261002-01/run-result.json`
is accepted against the exact candidate above. The hidden private desktop used
normal native UI double-clicks and drag/release, not injected packets or direct
native function calls. Both language modes used the current client (TW950 and
CN936); no live client binary or user desktop was changed.

Each language performed 14 actual operations:

- Head/body/glove/shoe equip and remove.
- Same-ID head/body swaps with different complete instance bytes.
- One empty bag move and one occupied bag swap with different armor parts.
- Two full-bag unequip refusals, with the next legal wear request succeeding.

Combined: **28/28 operations accepted**, including **24 mutations** (20 C2S28
and four C2S24) and **four refusals**. Full 20-byte instances and provenance were
conserved; other owners and unrelated tables were unchanged. TW and CN relogin
each restored all 34 observed bag/equipment cells without changing saved
revisions. Four actual Application restore messages (initial/relogin for both
languages) carried 136 slot records. Test instances are
`CUSTOM_TEST_NOT_NATIVE`; they do not prove native drops or stat generation.

All six owned server/runner/client PIDs are terminal, read handles are closed,
port 2598 is released, and protected processes/files/desktop checks passed.
The native refusal consumer leaves its pending flag at one; this is observed
native behavior, and the following legal request succeeds. The harness does not
manufacture a pending reset.

Related bank/trade/weapon/armor/database/config/startup CTests passed 16/16.
Additional activation checks cover nonboolean config values, missing native
authentication dependencies and mock login. Frozen chat verification passes
against the unchanged baseline. The separately compiled production factory test
passes 1/1 against true SqliteDatabase, schema42 and the complete catalog: correct
EQU2/TEQ26 read/project, same-key family mismatch refusal, saved-row conservation,
executed receipt-trigger corruption inside a bank transaction, rollback and a
successful normal scalar deposit control.

The separate bank receipt is
`artifacts/playtests/private-native-blackbox-bank-armor-projection-20261002-03/run-result.json`.
Both languages sent actual armor63 requests; Application refused them and full
bag/metadata/receipt/money state remained unchanged. Both clients then completed
10 eligible MED operations each (combined63×6,64×8,65×6), with 20 durable receipts.
All six armor overlays per owner, weapon overlays (two for TW and one for CN),
one gem per owner and their scalar revisions/provenance stayed exact. Native
full20 data agreed with saved state. MED totals stayed10/8 and final vaults were
empty. Other-owner/unrelated rows, source catalog and client remained unchanged;
all four owned processes are terminal and port2598 is released. Loaded pixels
and live two-player trade were not tested by this bank run.

The failed bank run02 is retained with its original ef97 harness and a byte-exact
source backup. Its only defect was a test log matcher expecting `rejected=1`
instead of the real `rejected=true`. The new v03 harness changes those two
matches only. Server/source/client were unchanged. Failed evidence is not
relabeled as accepted; only the completed new run03 is used for release.

## Delivery and open requirements

At this report's creation the formal release remains source-only schema 41;
the candidate above is not yet the installed executable. A separate release
must prove schema 41→42 preservation, exact candidate/native receipts, bank
regression, config delta and empty-player lifecycle. It must never copy an old
save over the live database or run a schema-41 executable against schema 42.

Still open for complete armor gameplay:

1. Original role/class/sex/level restrictions, independently from source text.
2. Final equipped attributes, max HP/MP and combat effect calculation.
3. Item-to-HeroDoll/DA appearance mapping, loaded pixels and peer presentation.
4. Native acquisition/enhancement/economics; no test grants become formal drops.
5. The 68 special definitions without an unambiguous physical part.

Scoped progress: source definitions 1,354/1,354 = 100%; physical source parts
1,286/1,354 = 94.98%; this planned TW/CN transport acceptance 28/28 = 100%.
These are separate scopes. Full armor gameplay and the whole-game native packet
completion percentage remain unproven.
