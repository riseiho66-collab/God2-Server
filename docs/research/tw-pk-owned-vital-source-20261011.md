# TW271 owned ordinary HP/MP source

This round connects the exact privately retained TW268 saved resources to complete ordinary S86/0 HP and S86/1 MP records, then consumes those records in the existing two-recipient owned PK entry projection. CUSTOM-0109 explicitly serializes six bytes as zero only because the current qualified native consumer paths do not read them. This is not recovery of an original server producer, a native padding/default claim, a widened native HP profile, or a completed hosted PK route.

Phase 1 remains source-only. No build, compiler, test, runtime, native execution, codec execution, game database/SQL execution, schema installation, migration, activation or deployment was performed. Static source accounting and retained-file hashing are separate from gameplay acceptance.

## Current native contract

The retained mapped image is SHA256 `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`; original PE is `5fcf8cbfaf31d2635b4541886336293249cde61c0877de6f5a435cc2b9559fde`. Selected original-PE and mapped bytes match. They qualify the following bounded ordinary consumer, rather than a guessed wire layout:

| Logical field | S86/0 and S86/1 meaning |
| --- | --- |
| 0 | Opcode 86 |
| 1 | Subtype 0 HP or 1 MP |
| 2 | Relative position, side = position / 14, slot = position % 14 |
| 3..4 | Not read by these qualified paths; CUSTOM-0109 emits zero |
| 5..8 | Maximum, complete unsigned DWORD bits |
| 9..12 | Current, complete unsigned DWORD bits |
| 13..16 | Not read by these qualified paths; CUSTOM-0109 emits zero |

The complete HP top function is `517230..51739C` (end exclusive), and the complete MP top function is `5173A0..517472`. The HP top also serves another subtype branch, but this new producer emits subtype 0 only. The qualified ordinary paths read subtype/position and DWORD5/9, and do not pass the incoming packet pointer or a derived packet pointer to a child. The HP and MP setter paths receive scalar arguments. The local UI callback uses a separate sixteen-byte actor-vital stack snapshot rather than the incoming record. These facts support a bounded six-byte canonical serialization policy; they do not make those bytes globally unused for every subtype or future consumer.

HP can write either relative side when the corresponding native actor exists. MP side1 returns without applying an opponent update. This producer therefore creates each owner's HP and MP at position 0, and the projection emits only the opponent's HP at position 14. Native actor/model construction, UI handles, opaque downstream rendering, delivery and eventual visible acceptance remain separate prerequisites.

The original server values for the six ignored bytes were not recovered. The existing `RecoveredBattleVitals` parser and encoder remain lossless and unchanged, including preservation of nonzero original WORD/tail values on legacy callers. The new zeros apply only to the explicitly requested owned factory under CUSTOM-0109.

## Concrete private supplier

`src/game/OwnedTaiwanPkVitalSource.h` introduces a private `Observation` which contains the exact `OwnedTaiwanPkCombatSource::Observation` minted by TW268. A caller cannot construct a receipt from a digest, a bool, arbitrary resources, a claimed origin label, or a record template. `observe()` requires the actual combat source current before and after validating both complete HP/MP projections.

The source uses `combat.material().resources` directly. `CharacterResources::legacy_vitals()` checks the complete saved 64-bit HP/maxHP before converting to native unsigned DWORD values; unsupported width is rejected, never truncated, wrapped or clamped. HP must be positive for this existing live-entry domain; HP/current and MP/current must not exceed their maxima. The existing TW268 LegacyCustom Battle domain remains unchanged. These restrictions are server admission policy, not proof that the native consumer rejects larger DWORD values. Saved zero MP and zero maxMP remain unchanged: the complete qualified native top/setter paths have no maximum-zero guard or division, but downstream opaque GUI behavior with zero maximum has not been qualified. No maxMP=1 substitute or rendered-success claim is introduced. The owner's 64-bit shared numeric objective remains active; this legacy native entry path does not implement its extended wire/object/display work.

Both ordinary records contain all seventeen bytes. Opcode, subtype and owner position are explicit; maximum/current come entirely from the saved source; only logical3..4 and logical13..16 use the documented custom zero policy. MP zero is a valid saved amount, not an absent-resource fallback. Missing or stale owned data is rejected.

`combat()`, `current()`, `uses_connection()` and `stored_current_in_room_transaction()` retain or delegate the actual private TW268 source. They introduce no independent source revision, database table, writer, permission or formula. Inherited full material includes the complete resources/role/auxiliary rows, root/current position, shared connection, private TW267 normal initialization and joint inventory/equipment source. The historical auxiliary build/provenance remains unchanged under CUSTOM-0106; its stored `NATIVE_CAPTURE_VERIFIED` label is still a custom data-selection filter rather than independent current-native combat authority.

## Projection and complete material

The new opt-in `RecoveredPkEntryProjection::prepare_waiting_notification_owned_vitals` accepts two private owned-player observations, two private owned-vital observations, the existing complete caller-supplied views, and the qualified Fight catalog. It has no caller-supplied `PlayerVitals` argument. For each owner it requires exact private combat-receipt equality with that owner's TW269 player source and current source checks before construction. It constructs the records internally, calls the existing owned-player projection, then repeats vital current checks and all retained player/text current checks before returning the Prepared material. ROOT271-01 added that final complete player/text fence in refinement 2; the full first candidate remains immutable. This repeated observation is not an atomic live-world/SQL/network admission claim.

Prepared retains optional `OwnedVitals` and optional `VitalTemplates`. `VitalTemplates` is two owners by HP/MP, four complete seventeen-byte records, each at source position 0. Their private receipt identity and all raw bytes are retained together. The two recipients receive six S86 vital occurrences:

| Recipient | Own HP0 | Own MP0 | Opponent HP14 |
| --- | --- | --- | --- |
| Viewer0 | Source0 HP | Source0 MP | Source1 HP |
| Viewer1 | Source1 HP | Source1 MP | Source0 HP |

Only the relative position byte is rebound for the opponent HP record; the full source values and canonical bytes remain intact. No side1 MP record is emitted or claimed applied. Recipient-specific names/secondary text and the four side-qualified Fight selections still follow TW269/TW266: each of those four selections retains four component rows, sixteen row references which may repeat. They are not replaced by the vital source.

The waiting entry keeps the existing nine-record grammar: S82, two S86/4 appearances, own S1C, own HP, own MP, opponent S1C, opponent HP, S88. Its logical length remains 305 bytes. The complete entry's vital offsets can be derived from record-size constants: own HP follows Entry + two Appearance + Identity; own MP follows that HP; opponent HP follows own MP + Identity. None of these offsets is a source of values or a permission token.

Old prepare/prepare_waiting/owned-player factories remain available and retain their complete externally supplied vital WORD/tail bytes. Old Prepared records have both new optionals absent. New readset fields are conditional on the owned-vital mode; old tickets/readset serialization are not reinterpreted.

## Room consumption and lifecycle boundary

Root owns the actual `SqliteOwnedPkRoomRepository.cpp` integration and conditional readset. The implemented new path requires complete owned-player and owned-combat sources, exact receipt equality, all four internally reproduced vital templates, and byte-for-byte equality with the six actual entry occurrences after viewer rebind. Template material without the private vital source is rejected. This prevents public Input material from claiming a real receipt while substituting different complete HP/MP records. The internally derived combat profile digest includes the complete new conditional source material. `owned_vital_source` records the CUSTOM-0109 authority, actual native image, bounded ignored-field scope, complete four owner templates and validated linkage to the retained full combat material; it does not replace those rows with a digest or provenance string.

Live/private source checks belong outside the room SQL transaction; concrete stored full-source equality belongs inside the existing RESERVED transaction. The vital source delegates the same TW268 current/closed-read semantics, without introducing nested read scopes or Session callbacks inside room SQL. After activation the shared Battle retains the admitted immutable resources and entry records. This does not add an active live-world lease dependency or silently refresh stats from later saved rows. Source writers, terminal recovery and other existing interlock limits remain explicit.

S88 stays entirely caller-supplied. Its counter DWORD1 and raw118 are actively consumed; this round does not derive a native initial counter from room ID, generation, resources or zero. The fourteen friendly HP/MP pairs remain supplied complete material which existing bootstrap validation requires to match own slot0 and the absent-slot policy. Zero absent values do not prove native pointer safety: the actual S82 initialization/all-fourteen-pointer prerequisite and native actor construction remain separate. S88 does not initialize general opponent MP. Its tail semantics and counter lifecycle are not replaced by the six-byte S86 policy.

The complete S82 contexts and future S86/5 grant remain separately supplied and qualified. The waiting grant schedule and bounded initial0B notification mode remain CUSTOM-0086/CUSTOM-0104. TW270's distinct two-Session held-entry admission still requires actual accepted69, both private holds and durable room activation; this new source does not substitute for transport receipts or establish a native ACK. Application `pk_rooms` installation, world visibility, C35/skill rules, rounds/results, terminal re-entry/reconnect and persistent recovery remain open dependencies.

## Receipts and accounting

Root's full truebefore contains 121 files / 18,598,476 bytes; the worker retained and hash-matched that complete epoch before editing. A bounded eleven-file initial source read/before epoch is also retained. The worker's immutable first candidate contains the new VitalSource header and changed Projection header, complete diff and before/after hashes. Root separately owns repository/policy/account/report material.

The worker first-candidate manifest SHA256 is `14209c37d8b1cedf577eb19ff7d510a8e73572d0db301112135cbf1baaeff41f`; refinement 2 manifest is `4c2d6c77b451490d2399a0dbe4000b185fed698f1aee080749975aff0a1f25e3`. Actual worker source files are VitalSource 3,156 bytes SHA256 `202aedd585c117de9d611d220f65550f55a325f69e0e16bf89f63e2772ae6f8c` and Projection 18,719 bytes SHA256 `2bdf63cee56d107c7d333bef8aea25a10f1245e5c2e31a6e50f9530174d2b406`.

The independent native terminal is `agents/native/seal.json` SHA256 `f8a98546cca3d3a09a89d60048ccf7d811c1658ec59e9ff106c889e58afd0624`, 73 members / 6,587,763 bytes, with findings SHA256 `821ba7b4ebfbf245108128f0fa92e1bae383b17f090126b785c6893b977e89d8`. It retains nineteen full inputs and twenty-two read spans; fifteen qualified spans total 1,683 code bytes / 561 instruction sites. The complete read-span union is 1,788 bytes and is a different quantity from qualified code. These are bounded static evidence quantities, not native-execution coverage or completed packets.

CUSTOM-0109 was appended to the actual policy with all 106 prior records preserved. Policy SHA256 is `58516a05fd88d2bb870ad51f51317d2d87d41abe107d75ba9d70eb411c622d83`. The current native facts and explicit custom serialization remain separate fields. Independent review terminal pins and final combined source/account/report pins are recorded by the root round report to avoid circular document sealing.

Count only the actual owned-vital material source increment. There are no new packet opcodes, no newly registered request/reply pair, and no complete hosted bidirectional PK route claimed by this bounded source work. Parser coverage remains separate from whole-game completion. Full TW completion denominator/percentage remain unknown until the directional/phase/state/variant inventory is complete.
