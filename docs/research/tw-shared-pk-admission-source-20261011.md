# TW263 shared PK admission source audit

## Result and scope

This round establishes the next concrete ordinary shared-PK source frontier and corrects an initially suspected native waiting-entry deadlock. It changes no C++ source, native wire, option, schema, database, client, battle state or existing CUSTOM design. No new CUSTOM-0104 rule is introduced. Zero new gameplay routes/opcodes are completed. TW whole-game route denominator and completion percentage remain unknown.

Read-only source analysis and bounded native static qualification are separate from tests, builds, compiler/runtime/native execution, codec execution, DB/SQL access and deployment; none of those operations were performed. The existing Taiwan-first/shared TW-CN-web objective and frozen features remain applicable. This document does not claim that the shared PK backend is Application-hosted or that two native clients can currently enter a shared room.

Archive root: `C:/Users/risei/.codex/artifact-archives/god2-server/20261011/tw-shared-pk-admission-source-263`.

## Actual admission edge and one shared battle

`src/core/Application.cpp` around the existing `pk_peer`/C69 integration declares `std::unique_ptr<OwnedPkInvitationService::RoomAuthority> pk_rooms` without assigning an implementation. The same source explicitly logs room authority as unavailable. The existing SQLite factory is not called by Application. Consequently the current C69 path cannot reserve a working room or publish a usable room invitation through a real shared-room authority.

The existing peer observation is substantive: it locks the exact Session through the current party-session owner; captures world and battle generations; retains the actual companion restoration material, private normal-world initialization, normal-entry prefix and corresponding submitted write receipts before inspecting Session fields; verifies full account/character/phase/position and repeatable generation/reentry fences; and rereads the owned saved prefix. These observations establish a qualified world peer and actual written world initialization. They do not supply a battle profile or grant.

`OwnedPkInvitationService` already separates serial invitations from room authority. Its abstract `prepare/current/commit/abandon` interface requires exact pair/reservation identity and one common room. `OwnedPkRoomState` and `SqliteOwnedPkRoomRepository` already model one mutable Battle per durable room, with canonical player positions0/14 and two relative native views. Do not replace that with two independent Battle instances.

The missing hosting edge is more than assigning a pointer: before common commit, both exact recipients need reserved/held ordered entry capacity and input barriers; admission must preserve one shared activation and exact Session battle-generation changes. Partial transport failure needs explicit recovery rather than treating a durable outbox row as two delivered clients. Current world-record sender phase rules and the skill publication transport are not a battle-entry capability; the latter permits its own qualified87/38/86-5 subset after InBattle/common readiness, not the82/86-4/1C/88 entry sequence.

## Real owned sources presently available

| Source | What it supplies | What it does not establish |
| --- | --- | --- |
| RecoveredCharacterRepository role/resources/position | Owner-qualified raw25 role, level/four base attributes, current/max HP/MP, full saved identity and revisions; explicit CUSTOM-0012/0013 state | Four authoritative physical/magical combat totals, skills, appearance17 or native battle contexts |
| Actual Application private normal-entry/companion readset | Exact current Session owner/generation, saved companion material/prefix and private written world-entry receipts | Battle authority, battle actor construction, command grant or native ACK |
| SqliteRoleAuxiliaryRepository raw61 | Four DWORD display operands at the qualified auxiliary offsets, provenance/origin/revision | Authoritative combat formulas/equipment aggregation; accepted CUSTOM_TEST_NOT_NATIVE and older6bf image are not current149c native combat evidence |
| SqlitePlayerAppearanceRepository | Old-build packed8 components, scalar/transform fields and owner/revision/provenance | Complete current battle86/4 opaque17, actual renderer construction or a certified world-to-battle transform |
| NativeWorldEntrySnapshotRepository | Version-keyed complete raw2A37, root/position/source metadata and revision | Witness freshness by itself, full combat profile or battle grant |
| NativeEquipmentSnapshotRepository | Current149c full inventory+DA15, actual actor handle, root/source/revision metadata | Complete battle appearance17, derived combat totals, S1C opaque45 or owned skill action policy |

Role base attributes Con/Str/Int/Speed are not physical/magical attack/defense totals. Lua's existing damage function consumes supplied attack/defense inputs; attribute allocation does not derive the missing totals. The only actual Application battle actor-stat producers found in this audit are explicitly diagnostic constants. Existing role auxiliary display data must not silently replace the absent authoritative combat profile. A SHA256 digest proves binding to bytes, not the origin or semantic authority of those bytes.

The current same-build inventory/DA publication source is a real owned world appearance path; it is useful input to a future profile producer. However, the complete battle86/4 fields and resource/constructor mapping cannot be filled with zeros or diagnostic templates merely because packed8 fields resemble world appearance operands.

## Existing entry/backend contracts and absent producers

`RecoveredPkEntryProjection::Player` requires complete typed S1C45 identity, complete ordinary86/4 appearance, and qualified HP/MP records. Each `View` requires caller-supplied complete raw82 contexts, coherent S88 friendly bulk/counter and exact17-byte primary86/5 material. The existing projection preserves opaque fields, inserts both appearances before either player identity, maps the viewer's own player to slot0 and opponent to14, and verifies `identity_word == full character <=0xFFF` plus player variant/level/resources. It has no ordinary Application input producer.

`prepare_waiting` preserves the qualified future grant separately while omitting its final17 bytes from the initial logical entry. The repository's InitialControl phase then waits for both exact0B notifications before exposing a separate grant epoch. Entry outbox submitted flags are queue-submission records, not native processing/ACK. InitialControl never accepts an action, and one viewer's fast input cannot advance the other viewer's unsubmitted grant.

`SqliteOwnedPkRoomRepository::Input` receives resources, roles, actors, seed, an external profile digest and initial0B masks. It binds all of them, exact raw entries, grants and contexts into its private readset. `owners_current` rereads saved resources/role/position and old pending-battle state, but does not reread a full combat/appearance/skill profile. The four combat totals still originate in caller-provided BattleActor values. Existing appearance/auxiliary/world writers are not integrated with the new shared-room owner locks. Adding an adapter before these supplier/lifecycle gaps are closed would invent authority.

Initial0B masks are explicit caller inputs. `OwnedPkRound::masks_valid` only bounds them to the two existing slot0 positions; it does not establish their actual native values. Fresh later-round grant/counter inputs and two-view result templates are still absent. The repository deliberately refuses later-round raw grant publication. These limits remain open.

## Native selector finding and withdrawn hypothesis

An initial hypothesis combined native initialization of primary selector+51 toFF with the0B sender's actor-byte upper-bound check and suggested that waiting entry must retain an opening86/5. No source edits were made under that hypothesis. Further native static analysis disproved the claimed unconditional deadlock: the normal-player S1C continuation can independently set primary selector+51 before the waiting-control notification.

The qualified conditional chain uses current mapped149c image addresses:

- Initializer51143A writes primary selectorFF.
- The actual local-role alias is closed:465176 takes the address ofMain+1539683C,465183 passes it as argument2 to468160, and4681F6 loads that argument intoEBP. The2A path reads bodyDWORD0 at4685EB, normalizes only bits23..25, masks with3FFF at468629, and storesRole+0 at468633. Main4657CA later reads that same local identity DWORD;4657D6 writes it into transitionT+0. Initializer511415..51141A copies the transition'sFB DWORDs to Battle+48, so local identity is not either raw82 context DWORD.
- Player S1C continuation51635F/516363 requires side0;516369 reads the actual copiedBattle+48 DWORD and51636E compares it to the full incoming S1C identity WORD. On that branch51637A obtains the actual slot and516382 stores primary selector+51.
- The earlier516166 branch tests the renderer HANDLE against exactlyFFFFFFFF (`!= -1`), not signed>=0. Further normal-player branch guards at516210/51621A and opaque5221B0/521F20/5220E0 calls precede selector publication. An unconstructed actor cannot be treated as established merely because the raw identity matches; the source chain is conditional on these calls returning normally.
- Native515A94/515AC8 passes primary selector into initial0B, and518E79/518E7E rejects actor bytes greater than0E. This makes the selector source relevant, but does not prove every waiting entry fails without86/5.

The world2A low3FFF identity assignment and local-role alias are now statically connected to the copied battle local DWORD. This establishes that concrete input edge, not normal construction or processing of the complete entry; do not replace the actual copied local DWORD with an arbitrary narrowed common ID. The current projection already checks the supplied player identity against full character<=0xFFF. Adding another identical guard would not connect a missing producer.

The native S1C selector-write suffix does not establish initial0B masks. The inspected complete initializer5112C0..5118D9 (RET4), S1C top-level path and88 top-level path have no direct44C/45C mask writes; this includes the516382..5163DD suffix. The initializer's final51A980 and other descendants remain opaque. Opaque descendants and other state writers remain open. The actual0B builder reads the target BYTE array atBattle+44C and count DWORD atBattle+45C. It rejects signedcount>14, initializes its outgoing mask DWORD to0, and only conditionally skips target accumulation when count<=0; positive targets are split by side=target/14 and bit=target%14. No current source proves the actual initialcount0. Therefore no zero-mask derivation, unconditional control-liveness guarantee or extra opening grant is introduced. The historical prepare/prepare_waiting API, bytes, repository tickets/readsets and policy are preserved.

## Next concrete implementation sequence

1. Recover the actual ordinary world2A/DA packed8 to complete battle86/4 producer, including resource selector/opaque fields and transform variants, using retained owner-qualified same-build input. The actual local-role identity alias is now qualified; resolve the remaining renderer/resource and opaque-call prerequisites needed for normal S1C selector assignment. A plausible eight-byte overlap is insufficient.
2. Establish a real authoritative owned combat/skill profile supplier. Bind full root/resources/role/equipment/appearance/skill revisions and provenance; explicitly decide and document any server-designed formulas rather than relabeling display bytes as native rules. Include those writers in shared admission/active-room exclusion and current-source checks.
3. Obtain real complete battle contexts, S1C material, S88 counter/bulk, initial grant and initial0B readset. Only then add an owned profile/entry preparer at the actual C69 admission edge, with exact Session/private-entry fences before fields. Do not add an uncalled facade or fabricate opaque templates.
4. Implement the actual RoomAuthority adapter with two-peer held entry preparation, exact lifecycle transitions and one common durable Battle. Keep the two-phase initial0B→separate grant epoch barrier, ordinary/result input bounds and partial-I/O recovery explicit. Establish terminal/reconnect/owner-lock recovery before production enablement.

The bounded progress this round is a source/native authority map and a corrected next frontier. It is not a completed shared-PK route, a deployment, acceptance, rendered client result or whole-game percentage increase.

## Preserved evidence

Source worker full before:59 files /17,939,977 bytes; manifest SHA256 `bcd3e410c1269cf220e3df6cbc01e9df4ac9436c716946b324f21793a874eac5`. Additional whole source/document inputs:24 files /137,318 bytes; manifest SHA256 `463e50eeea0db5e24882730ec461be05f8d9c4b04c6929250a88cb897ab9efc7`. The first readonly analysis records the withdrawn hypothesis and no-edit status; SHA256 `bc57fd2550d93e3d01318d12ff226794fd442afd9d1a7999ad1fc101deed1870`.

Native terminal: `agents/native/seal.json` SHA256 `4f2d0a03f4fa8dc734a94775602596f21af62c2dccbb2bd08196ecbc046f9962`,115 members /7,007,643 bytes. Native findings SHA256 `0a8fdb87e2cd9e87f34b82e9cf46ad28bfa13fa46d159d2f110f551046b96e4d`. The qualified mapped image is3,174,400 bytes with SHA256 `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`; the originalPE is3,183,616 bytes with SHA256 `5fcf8cbfaf31d2635b4541886336293249cde61c0877de6f5a435cc2b9559fde`. Their whole images differ; selected qualified spans agree. Native retained41 read spans,16,868 summed raw bytes/14,077 union raw bytes and4,977 summed instruction sites; exploratory unaligned spans are not source-qualified, and full-image retention is not code coverage. No opaque descendants were manufactured or executed.

Independent review's terminal seal is recorded by the root round report, avoiding a circular document/seal dependency. Existing TW259..262 seals and source history are retained unchanged.
