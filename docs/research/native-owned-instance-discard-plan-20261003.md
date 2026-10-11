# Native 27 owned-instance discard: bounded implementation plan

Status: **PLAN ONLY / INACTIVE / NO RUNTIME CHANGES**. This document proposes
an independent opt-in custody route. A new custom design ID must be allocated
and registered by the integration owner before implementation. Native wire and
client control evidence do not recover original server destruction, bind,
protection, acquisition or ground-drop policy.

## Accepted evidence and exact scope

- Tool: `tools/strike_lab/current_discard_instances_20261003.py`, SHA256
  `8caec0ce92a9d5d122bc745efc99b4ec67009e86a74f198c2120748ca4b14380`.
- Final receipt: `artifacts/research/current-discard-instances-20261003/run03/native.json`,
  SHA256 `6965aba323e3c1a52b68fc4acd8cbeba1b68c7c572dda4eeaf9cb53a1e95218e`.
- 419/419 offline original/current machine cases; session 48751, exit 0.
  1,104 executed instruction entries match mapped original
  `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`
  and current executable
  `c5d8f79baa36879851703ac05d2b5caddf44a907677f7de114f568eeaf14f575`.
- Original gamedata pin:
  `70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731`.
  Selected source records are regenerated with native constructors and current
  row qualification. Discard cases use six representative keys, not every
  armor/weapon catalog row. Header/tail variation and non-MED count>1 are
  artificial preservation/control inputs, never granted-instance evidence.
- Accepted scalar CUSTOM-0061 tool, receipts, service and route are frozen.
  The 419 oracle is not hidden-desktop acceptance and does not prove live
  source selection, quantity edit clamping or server authority.

## Native request, controls and response

| Native branch | Proven behavior |
| --- | --- |
| `49A330`, control 56, event `0x20` | Drag release reaches `49B3F3`; event 1 click alone does not discard. Reads selected WORD at UI+855F0, item WORD at UI+85610+24*slot and quantity BYTE at UI+8560C+24*slot. |
| `49B086..49B09B` | Source 0..29 or special 42/43 reaches discard; equipped 30..34 and other 49 refuse ProgramMsg 820. Special cells are direct fixture transport evidence, not existing-player capacity/admission. |
| `496720`, queue call `496739` | C2S logical5 is `27 itemWORD sourceBYTE quantityBYTE`. Payload4 passes unchanged; UI+866E4 nonzero suppresses queue. No owner/revision/full20/token is carried. |
| `4C9820`, `4C9B70` | Signed count>1 opens quantity mode4; max at UI+23D5EC, selected amount at +23D5E8, raw request at +23D5F0. |
| `4CA470`, control2/event20 | Calls `4C9ED0`; `4CA07C` queues through496720. Completion only checks signed amount>0 and serializes lowBYTE. Direct max7/value8 and128 queue;256 queues0. These are not proven reachable through the edit control. |
| `4CA470`, control3/event20 | Cancels via `4C9BD0/4C9C00`, closes quantity widget and resets mode/selected amount. No request queues. |
| Actor+449E bit `0x10`; `4EAEF0` | Opens confirmation mode5, storing key AFECC/source AFEC8/quantity AFECF/mode AFECE. Some full20 bits affect presentation; no original server protection semantics follow. |
| `4EA770` | Control4 accepts via `4EA81E ->496720`; control3 cancels. `4EB620` closes and mode becomesFF. |
| `4991E0` | S2C41 logical5 is `41 itemWORD sourceBYTE countBYTE`. Clear is `41 0000 slot 00`. It clears count and low key, retaining reserved bytes1..3 and inactive upper18 metadata. Those stale bytes are not a live owned instance. Count must remain1..127 when occupied. |

No native source bag cell is optimistically destroyed by the tested discard
chain before a supplied response. Thus a typed whole discard needs one native
41 clear after successful commit, not an invented drop/loot or a fresh entry
22/24 refresh. Refusal can reproject the existing qualified full20 with the
existing canonical 41-clear /3B-full20 /41-absolute sequence; it must never use
item ID plus18 zeros for an occupied typed item. No response is fabricated when
the stored evidence itself is corrupt or unqualified.

## Present integration gaps

1. `src/core/Application.cpp:1351..1388` implements CUSTOM-0061 with one27 plus
   optional ticks. `:1372` requires the scalar supply policy, so armor, weapons
   and gem overlays do not enter that service. Classification and new handled
   routing must be separate; do not widen `bag_slot_eligible` or edit the scalar
   service/transaction to accommodate typed instances.
2. `InventoryDiscardService.h` delegates to
   `SqliteRecoveredCharacterRepository::commit_inventory_discard`, implemented
   in `src/db/SqliteInventoryDiscard.cpp`. That transaction compares only the
   source scalar and revision, and neither explicitly deletes three occupied
   overlays nor compares a complete owner snapshot. It is not the typed delete
   API. Existing reciprocal triggers require overlay removal before clearing
   an occupied scalar.
3. Bank and player-trade repositories have moves/settlements, not destruction.
   Do not simulate discard with trade to a fake player, banking to a hidden
   slot, scalar zeroing that relies on an implicit trigger, or item generation.
4. `OwnedBagProjectionService::verify_planned_in_transaction` deliberately
   prohibits instance/category changes. Its existing scalar proof must stay
   unchanged; it cannot authorize a typed deletion.
5. The current scalar route has no new typed live lease or typed receipt.
   A new route must reject active trade, world transitions and pending battle
   independently. Do not change old scalar behavior while adding those guards.

## Reusable APIs and the boundaries of reuse

| Existing API | Safe reuse | Additional requirement |
| --- | --- | --- |
| `RecoveredInventoryDiscard::decode/encode` | Same five-byte native request; no new parser shape needed. | Header comment currently names497720; machine evidence is496720. Keep frozen codec unchanged and use the correct address in new documentation. |
| `database.armor_slots().load_snapshot(account,character)` | Authenticated full50 observed scalar cells plus armor/weapons/gems, source/revision/origin evidence; missing cells stay absent. | Its foreign validation is observation validation, not strict WPN/TWP source-type admission. Add independent strict qualification for the new destructive operation. |
| `NativeArmorCatalog::lookup/equipment_slot` + `RecoveredArmorSourceInstance::matches` | Exact per-item EQU2/TEQ26 binding and mapped part30..33. | Unknown/unmapped catalog rows remain rejected. Typed count must1; header family alone is insufficient. |
| `NativeWeaponCatalog::lookup` | Full source396 identity, WPN/TWP source family and definition hash. | Mirror new-only strict logic at `SqliteOwnedInstanceTradeRepository.cpp:105..107`:396bytes, source equipment bit11A&4, exact WPN1/TWP25 instance namespace. Preserve all other header/tail bytes without assigning bind meaning. |
| `RecoveredTeleportGem::displayed_charges` | Existing gem16055/type8 displayed charge domain1..10. | Whole instance quantity1. Discard removes the whole record, not one charge. Keep charge flags, opaque tail and source evidence in the audit before-state. |
| `database.make_bag_projection(...)`, `project`, `capture_proof` | Existing occupied/empty owner-bound encoding and immutable bag observation. | Do not use scalar `project_planned` to clear a typed item. Encode planned empty41 directly and preserve typed pre-state for refusal. Projector weapon-category boolean alone does not prove namespace1 versus25. |
| `SqliteTradeRepository::load_wallet` / `SqliteBankRepository::load_bank` | Optional read-only purse/bank evidence. | Do not provision rows or require bank access to discard an already-owned bag item. |
| `sqlite_detail::Transaction`, `Statement`, typed CAS patterns in0069 | BEGIN IMMEDIATE, exact BLOB/source/provenance/revision conditions, actual changes1, late readback, precommit callbacks. | Existing erase helpers are private; implement new bounded SQL in the independent repository, not modifications to accepted trade/bank routines. |

An independent discard snapshot should own its complete bag50/three-overlay
state and preserve observed existing bank/foreign overlays, wallet/bank values
and receipt histories as immutable evidence where present. Absent rows remain
absent. Do not reuse a bank loader that requires/provisions300 cells just to
make an unrelated bag deletion possible. A trade loader also requires a wallet
and has a two-owner settlement model; it is not the new discard owner model.

## Proposed independent opt-in custody contract

The integration owner should create new repository/service/config/accessor/
empty receipt schema and a new custom design registration. Default disabled;
configuration must require authenticated recovered world entry/movement and
the existing full bag projection support. No grant/capacity or metadata rewrite
is performed during migration, startup or read. Enabling the new option only
admits verified, already-owned typed bag instances. It does not claim native
bind/protection or broaden the old scalar policy.

Input limits:

- Authenticated account and selected character from the live session; never
  trust a client-supplied owner. World ready, initial full bag projected,
  location/scene current, no transition/logout lease and no active trade.
- One native27 plus optional ticks. Duplicate27 or another mutation rejects
  the new batch without any destruction. Preserve the existing frozen chat
  dispatch; if chat coalescing is supported, remove only handled27/ticks and
  pass the remaining chat to its existing handler without rewriting it.
- Ordinary bag source0..29 only and an existing occupied scalar. Equipped
  30..34/special42/43 remain excluded; transport exposure does not create their
  authority. Retain protected guide slot0 behavior when its original custom
  quest guard applies.
- Exact request key equals source scalar key equals overlay key. Exactly one
  qualified typed overlay; count1/request quantity1. Reject absent/multiple/
  missing/cross-family overlays, foreign owner, stale revisions, unknown source,
  exhausted revision, wrong client/source/design pins and unsupported gem
  charge domain. Never reconstruct full20 from the request.
- Scalar MED comparison stays routed to unchanged CUSTOM-0061. Broader quest,
  NPC, pet, shop and unknown item classes are outside this proposal.
- Bank open/mutation context needs an explicit new-route decision: either deny
  while that context is active or invalidate/re-synchronize that context using
  existing public disconnect paths before a permitted mutation. It must not
  silently retain a stale bank snapshot. Current bank service has no public
  `active(session)` query; `permits_items` requires the known target. Track any
  new opt-in lease state in the new route, without changing frozen economic
  rules. The original server policy remains unknown.

Transaction sequence:

1. Read/qualify one consistent complete owner snapshot without DDL/grants.
   Build an immutable plan: exactly one selected typed overlay removed, exactly
   one scalar becomes key0/count0/revision+1, source allocation/hash unchanged.
   All other owner slots/overlays/bank/cash/old receipts are identical.
2. Allocate unique server receipt, exact before/after audit strings/full20 and
   all success/refusal wire before starting writes. Recheck the live account,
   character, scene, ready state and trade/bank lease in preparation.
3. Own BEGIN IMMEDIATE. Recheck authenticated DB ownership, the entire snapshot,
   duplicate receipt and pending battle before writing.
4. Delete only the selected overlay with full20/revision/origin/provenance/
   source/client/design CAS. Require exactly1. Then scalar clear uses key/count/
   revision/source/design CAS and changes exactly1. Do not replace a source
   row or create empty weapon metadata/capacity.
5. Insert an immutable new-design destruction receipt with full20, source
   evidence, authenticated owner, request and before/after snapshots. Expected
   quantity delta is exactly minus1, not conserved quantity: every other item
   and complete20 instance remains unchanged. Wallet, bank and other owners
   must not change. No loot, refunds, currency or ground drops are created.
6. Actual postwrite full snapshot/receipt readback; recheck live lease and late
   pending battle, then repeat readback after any check callback. Any failure,
   trigger mutation, SQL abort, preparation failure or late state change rolls
   back scalar, metadata and receipt together. Do not send a success before
   COMMIT. Returning a committed non-const plan/result must be noexcept-movable;
   no postcommit allocation can turn a committed deletion into a rejection.
7. Only after successful commit deliver prepared41 clear to the still-current
   owner session. On an eligible idle refusal, use the current authoritative
   full20 projection; no whole-world22/24 refresh or generic disconnect.

Wire limitation:27 has no instance revision/nonce. Server full snapshot CAS
rejects changes after capture and immediate repeated deletion of the now-empty
slot. It cannot identify an arbitrarily delayed identical request after that
same slot is later filled with another instance of the same key. Do not claim
native replay tokens or solve that ambiguity by adding undocumented wire data.
Tests must distinguish stale repository snapshots, duplicate coalesced requests
and the separate same-key-later-generation ambiguity.

## Required gates before formal activation

Unit/production adapter/TCP must exercise both owners independently, strict
EQU2/TEQ26 mapping, all four armor parts, WPN1/TWP25 and gem1/10 charges, same-ID
different full20 in two cells, source0/29, exact20/provenance tombstone and other
49-cell preservation. Include default-off scalar fallback, failed ownership,
quantity0/2/128/255, wrong key, empty/protected/equipped/special cells, missing
overlay, bad family/pins, stale full-owner revisions, unrelated overlay/trigger
mutation, SQL failure, audit corruption, latebattle/live-lease change, active
trade, bank context, fragmented/native27+tick framing and duplicate/mixed batches.
Also verify no-grant empty migration, all preexisting typed rows/history and
frozen chat/client/config baselines remain exact.

The next new hidden-desktop harness must use actual native source selection/
hit rectangles and native drag release, not the419 oracle's seeded selected
slot. Two independent TW950/CN936 owners each need:

1. Already-owned EQU/TEQ fixtures for four native parts each, WPN, TWP and
   gem16055 with charges1 and10. This is12 representative typed fixtures per
   owner; state them as disposable CUSTOM_TEST inputs, not native grants.
2. For every representative fixture: confirmation off whole discard,
   confirmation on cancel with exact unchanged DB/native record, and
   confirmation on accept. Use separate existing fixture records and native
   option UI to toggle confirmation; no client memory writes.
3. A same-key/different20 pair: selecting one destroys that exact chosen
   overlay only; the other stays byte/provenance/revision exact. Include source
   bag0 and29 and a genuine cancel before selecting the other.
4. Genuine equipped-source refusal plus active-trade refusal, while the other
   player's50/native bag and persisted data remain unchanged. Do not grant
   reserved42/43 solely to match direct oracle exposure.
5. One scoped MED partial/whole regression through the unchanged scalar route
   if the new dispatch is enabled. Native quantity edit/confirmation, not raw
   packets injected into a live client. TCP malformed quantities remain
   separate negative evidence.
6. Real close/reopen and two actual new client PIDs (not CharacterReady replay)
   restore all surviving complete20s and leave deleted source empty. Both
   owners' SQL, native50 cells, currency, equipped cells, bank/receipt histories
   and unrelated players remain exact except the documented deletion receipts.
   Cleanup proves four client PIDs +server+runner terminal and the private port
   released. Foreground desktop, screenshots and production processes stay
   untouched. Stream large event evidence rather than retaining every complete
   snapshot in a growing in-memory list.

A passing offline419 receipt is foundation evidence only. Full-instance27 is
not implemented or live accepted by this document; original server protection,
destruction/ground-drop rules and unqualified item classes remain OPEN.
