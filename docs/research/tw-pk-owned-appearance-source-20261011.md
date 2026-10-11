# TW267 owned PK appearance material

This round connects actual current owned Taiwan appearance material to the existing four-view Fight catalog selection and Prepared/repository readset. It is an opt-in source path under CUSTOM-0105, not a hosted shared-PK admission route, original server packet recovery, renderer acceptance, or complete gameplay. Application still has no assigned shared PK RoomAuthority. No build, compiler, tests, native/VM/codec execution, game database access, migration, activation or deployment occurred.

## Explicit correction of the retained historical frame summary

The actual current `RecoveredWorldEntry::Frame` is `std::array<uint8_t,40>` and carries logical S2A37. Prior TW265/TW266 prose saying Frame42 was incorrect. Their sealed receipts are preserved unchanged. The new source uses the actual typed frame and `RecoveredWorldEntry::Frame{}.size()`, not the historical summary. This correction does not change the native frame or client.

## Actual input and ownership join

`OwnedTaiwanPkAppearanceSource::observe` requires the concrete SqliteAccountRepository, SqliteRecoveredCharacterRepository, SqliteNativeWorldEntrySnapshotRepository, actual SharedWorldPresence, an exact weak Session incarnation, its privately minted NormalWorldInitialization, the actual ready Lease, and the private Committed receipt from the actual SqliteOwnedEquipmentTransaction. Repository/account/character object identities must agree. The shared character repository's `uses_connection` is later compared to the room's actual SQLite connection; the room's internal `owners_` is a separate object on that connection, so pointer equality with that internal object is not used.

The supplier first locks the exact Session and calls `normal_world_initialization_current_on_game` and checks `entry_written` BEFORE reading Session identity, phase or battle generation. It restricts this source to an open InWorld Session with exact session/account/character. The passive local Written receipt is not remote ACK, native reset/catalog acceptance or battle authority. A re-ready/reconnect/old private entry cannot be renewed merely by matching bytes. The Observation retains the original private receipt and weak incarnation, rather than looking up another Session with the same IDs.

The material retains all of:

- Full initial world snapshot: complete common root, position/revision, client/kind/source pins, source record, full raw frame, snapshot revision.
- Actual issued typed frame40, logical37, accepted tail and config flag from the private entry receipt.
- Complete canonical inventory population: root/revision/source, every ordered cell, optional instance with ID/definition/quantity/revision/stackability/acquisition receipt, and every complete native alias.
- Complete native equipment snapshot, exactly1215 bytes:50 x24-byte inventory caches INCLUDING trailing DA15, not1215 plus a further15. Root, current position/revision, actual actor handle, source pins/record and snapshot revision are retained.
- Exact ready Lease including its registry generation, initial pose and actual full native actor WORD; captured Session battle generation.
- Complete projected ordinary17 record and the existing four side-qualified Fight selection receipts.

Both complete inventory and native equipment must remain current under the exact joint private Committed receipt. The receipt is not recreated from a SHA, a public raw snapshot, two independent current reads or an arbitrary caller qualifier. `joint.committed_current` re-reads both populations in its own consistent scope and checks actual common root/current position/no pending battle. The source performs repeated concrete Session/lease/position/world-witness and joint-current reads with game-owner and reentry guards. Borrowed concrete database repositories and connection must outlive the Observation, Prepared and every ticket retaining them; joint/presence are held strongly and Session weakly.

## Initial pose and current movement are different

The world snapshot must match the complete actual issued frame and the Lease's initial position. Decoded S2A geometry must match that initial pose. `presence.saved_position(lease)` must instead match the committed equipment snapshot's current saved position. They may differ after legitimate movement; the source does not demand equality between old entry coordinates and current coordinates. This path restricts the complete entry root to the same actual current joint root. A changed root requires new qualified material, rather than pretending an old raw entry is current.

SharedWorldPresence Lease.generation and Application PK Peer.world_generation are different namespaces. The source retains the former, the room readset retains the latter, and no equality between them is inferred. Repository preflight matches actual observed session/account/root character, battle generation and current saved position to the supplied Peer. The actual Application PK-generation resolver/RoomAuthority linkage remains open; this supplier does not manufacture it.

## CUSTOM-0105 projection and native distinction

The original full world-to-battle producer has not been recovered. CUSTOM-0105 explicitly chooses the current committed DA15 logical7..14 packed eight bytes as S86/4 logical4..11, preserving every high/variant bit. It chooses mode1 and specialWORD0 and canonical zero only for logical12/15/16, which TW265 qualified as unused on the selected complete ordinary branch (the packet pointer is not passed to that branch's children). These values are server policy, not recovered original server bytes or a global ignored-field rule. Other battle modes/special variants are outside this factory.

Both actual entry transformWORD and current DA transformWORD must be zero for this explicit restricted domain. Native world zero transform is sufficient to select the ordinary path, not necessary globally: a nonzero transform rejected by opaque45C100 can also fall back to ordinary. Zero restriction is not inferred from neutral scalar bytes. Complete DA5/6 and entry scalar bytes remain in the retained source/readset, without assigning them action0 or battle fields.

Native267 qualified actual local DA dispatch by full zero-extended DA WORD equality to the local Role DWORD at469369..469386. There is no incoming DA mask. This source therefore requires full DA WORD == equipment actor_handle == Lease.actor_handle == actual entry-bound actor handle. The existing PK projection separately requires Player.character <=0xFFF and S1C identity_word == that common character. The new owned factory additionally requires the minted observed handle == Player.identity.identity_word and the actual observed character == Player.character. A full native handle/common character mismatch is rejected without truncation, alias fabrication or rewriting either identity; broader identity support remains open.

The factory takes actual privately minted Observations and consumes their projected appearance directly, replacing the caller's appearance field. The complete independent Player identity/vitals and View contexts/bulk/grants are still required and validated by the existing projection. This source creates no HP/MP, level, skill, profile, context, actor, grant or room permission. Each relative viewer is rebound at positions0/14 before the catalog resolves all four exact component rows; missing Fight rows reject the Prepared. Resource-row presence is not proof of constructed models, animation assets or equal world/battle rendering.

Different HeroDoll and Fight derived values disprove an equal-derived-value shortcut. They do not prove that identical packed eight bytes are necessarily invalid across the two catalogs: different catalogs may intentionally derive their own resources. This round uses an explicit custom presentation mapping and independent Fight row selection, and makes neither an original producer nor equal visual appearance claim.

## Concrete Prepared and repository consumption

The new `prepare_waiting_notification_owned` factory qualifies the Observations before and after preparing the existing CUSTOM-0104 waiting entry and CUSTOM-0086 catalogued view records. It retains both immutable private Observations in Prepared. No public bool/token reconstruction can mint them.

The repository conditionally adds `owned_appearance_source` to the readset only for this new Prepared mode. It serializes the complete source material, including all inventory instances/aliases and full raw native/world bytes; four Fight rows are already retained by the preceding catalogued mode. Existing factories, legacy raw readset serialization, schema/defaults and later battle behavior remain unchanged when this optional source is absent. Serialized audit material does not recreate a live receipt or authorize a restored ticket by itself.

Concrete source preflight executes before `BEGIN` in exactly `prepare`, RESERVED `current`, RESERVED `initial` and RESERVED `activate`. It requires the actual same connection and exact Peer/material join, then invokes each source's concrete Current. It is intentionally not inside `owners_current` or generic `require_ticket`, because joint Current owns read transactions and requires autocommit. Once active, the battle uses frozen entry audit material; later round/settlement/control/outbox methods do not require the old live world lease or a return to InWorld.

This preflight is not atomic across live Session/lease changes, both participants, SQLite commit and held transport queues. The preflight-to-BEGIN/commit window, both-peer held queue reservation, lifecycle barriers/recovery after partial ordinary I/O, actual profile/skill/vitals source, same shared Battle hosting, Session entry publication and native acceptance remain OPEN. A durable outbox is not socket enqueue, native construction, rendering, ACK or an all-or-nothing client delivery.

## Native source and immutable inputs

Current mapped native image:149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763. Original PE:5fcf8cbfaf31d2635b4541886336293249cde61c0877de6f5a435cc2b9559fde. Whole images are distinct; only explicitly selected matching spans are used. TW267 retained38 inputs and10 bounded spans,66 newly qualified code bytes/19 instruction sites,125 retained qualified bytes,362 read bytes summed/298 unique. Forbidden GUI interiors were not expanded.

The actual normal2A call order is packed pointer at4684E6, bodyDWORD0 bits16..22 at4684E7, bodyBYTE6 at4684E8, then opaque461270. Callee arg1 is body6, arg2 is body0 bits16..22; the first verbal labels were reversed and corrected before implementation. Local DA selectors come from Role44 bits18..25 and10..17, not DA5/6. `463780` uses a signed selector WORD against the actual Drv row count, loading selected row+12 or returning zero out of range. Selector0 does not intrinsically imply action0; actual Drv state and opaque helper behavior remain open.

Native terminal: `agents/native/seal.json` SHA256 df6f7660f05267731db4b901cd31ca2fbf1142448d5b79394ed1b88ca80de613,67 members/6,628,183 B. Findings f663f963cd2a5db7c2130b073838c23b6b39dbb56eacbaca4685fd36cdedf5f8. The source receipt retains all native members and the terminal seal separately; no old native seal was overwritten.

The catalog still pins the exact full historical parsed-field native.json SHA5500950022f789d1372f92fe2dd6ebee936c2e7f5a04b133c45151f3aabd142d and current encoded Fight SHA1195afeeb060d7d81c07e65476da8089d5ab72edea90971d72a07f20863338b8. It is not newly decoded CSV/raw offsets or an old c5d8 runtime qualification for current149c. Its strict duplicate/number/source validation and all four current side selections remain intact.

## Source epochs and remaining accounting

Own full truebefore:86 existing files/18,185,057 B plus explicit absent-before new source/doc. First candidate:three C++ files/62,276 B, manifest9ab652867e943ecb0010e13e3edb30a9115b4eb85dc5729f1981d5821356f85f. Files: NEW `src/game/OwnedTaiwanPkAppearanceSource.h`, modified `src/protocol/RecoveredPkEntryProjection.h`, modified `src/db/SqliteOwnedPkRoomRepository.cpp`. No Application, client, Session, CN/web, auth/chat/fonts/conversion, schema or production-save changes.

Bounded owned appearance supplier -> four resource selections -> Prepared -> reserved admission/readset is source progress. New opcodes, request/reply associations, hosted whole gameplay routes and completed shared-PK admission remain zero. Root owns the route ledger, policy registration and packet report. The independent review terminal is recorded externally in the root round report, avoiding circular document/seal pins.

Final policy pin: docs/custom-designs.json SHA2565fdf0a288b3e36abeecd996a2dc58f5248896c6805497a20884e857a287905e7. Root appended CUSTOM-0105 and preserved all102 older designs. The source worker did not modify the index.

The first candidate is also the final C++ epoch; no code refinement was requested by the independent full static reader. Actual source pins:

- OwnedTaiwanPkAppearanceSource.h:9,684 B, f0087e81b4b0e537c007b48edc55516a515c3f28843da338ac1b0700037be0cd.
- RecoveredPkEntryProjection.h:12,497 B, 2ccc27ea5537f2c0f9af16d8bab7d35543293ab7b9f44af27726296bc440702e.
- SqliteOwnedPkRoomRepository.cpp:40,095 B, 5b37e915e54f5c4b0bfb59fd80bbbacc5d90a8f860e5d49b524e819a1bd8e607.

The two existing files total52,592 B after versus46,535 B before; one source header is new. All other59 captured source files are unchanged. Existing native/client/schema/default behavior is not activated by this opt-in factory. The first draft and this final document epoch are both retained; no historical receipt is overwritten.
