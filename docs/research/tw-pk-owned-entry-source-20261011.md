# TW269 owned complete player S1C source, 2026-10-11

This round implements a complete45-byte normal-player S1C producer from actual privately retained owned material, and consumes it through the existing two-view entry projection, PK Input digest/readset and RESERVED source guards. It advances the concrete entry source chain following TW267 appearance and TW268 combat. It does not recover the original server's complete entry producer, initialize every native actor field, create an Application RoomAuthority, activate a service or complete a playable PK route.

All changes are PHASE1 source only. No build, compiler, tests, runtime, native/VM/codec execution, game database/SQL execution, migration, activation or deployment occurred. Static artifact capture, hashes, JSON accounting and source/document review are separate from gameplay verification. Existing client/auth/chat/IME/fonts/conversion/CN/web behavior and saves remain frozen.

## Actual source audit and chosen increment

`RecoveredPkEntryProjection::Player` previously required a supplied complete S1C45 identity, complete ordinary86/4 appearance and complete HP/MP records. TW267 already supplies the private current owned ordinary appearance and TW268 supplies actual saved role/resources/dual attack/dual defense under explicit CUSTOM-0106 adoption. The missing S1C source was substantive: all bytes9..40 and41..44 are consumed on the player path; they cannot be called padding or filled from diagnostic participants.

The targeted actual source search found complete S1C builders only in isolated diagnostic participants/revival/manual skill inputs. Those templates are excluded from ordinary PK authority. Current concrete common character roots retain the full40-byte profile, including its primary name field and actual name_codepage. The existing `SqliteRoleTextRepository` retains canonical secondary16 bytes, UTF8, codepage and revision, with current149c/CUSTOM-0056 provenance. Its actual table is **character_role_text**. It is not a guessed owned_role_text_0056 table. Missing source rows remain different from a genuinely saved empty secondary string.

Native player text setters establish a bounded semantic correspondence: S1C primary and secondary strings reach renderer fields70 and81, and the existing S23 secondary text reaches the same509E70/field81 setter. This supports a separately labeled custom presentation producer using those actual owned texts. It does not prove the original server emitted the same raw45 bytes or that every native side-list label matches the S1C strings.

The original source for S1C WORD7 and DWORD41 remains unavailable in this targeted audit. CUSTOM-0107 therefore defines a restricted ordinary PK presentation domain: exact variant0x2000, ordinalWORD0 (no extra nonzero ordinal marker), statusDWORD0 (no bit0/status9 or bit6/status149 request), and canonical NUL-terminated string serialization. These are consumed semantic policy values, not native defaults or unused padding. No status, progression, formula or gameplay permission is inferred from the primary name, role stateWORD or secondary text.

The alternative transport audit remains useful but was not implemented this round. Existing native battle skill publication accepts only87/38/86-5 in an already InBattle common-ready Session, so it cannot be reused as82/86-4/1C/88 entry transport. Existing RoomState activation creates one durable shared Battle and both outbox rows, but does not reserve two real Session queues. A later explicit asynchronous entry admission must stage both held frames and input barriers after69 Accept, before common activation; synchronous RoomAuthority commit cannot merely post two queues and claim atomic acceptance. No hold is installed during invitation preparation because that would block the recipient's Accept input.

## Current149c native field qualification

The retained mapped image SHA256 is149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763. Original PE SHA256 is5fcf8cbfaf31d2635b4541886336293249cde61c0877de6f5a435cc2b9559fde. Whole images differ; selected qualified code bytes agree. Native addresses and object offsets here are hexadecimal; logical packet offsets and byte counts are decimal.

| Logical S1C fields | Qualified native use | New source/policy |
| --- | --- | --- |
|0|401394→4012A6 returns logical45; opcode1C|Existing typed codec|
|1|Unsigned position, side=position/14 and slot=position%14;51E6E0 selects actual actor|Existing relative own0/opponent14 policy|
|2|Unsigned displayed level copied to metadataDWORD4 highBYTE/actorDB7|Actual private268 role25 levelBYTE1; no growth formula|
|3..4|FullWORD copied to metadata0/actorDB0; local side0 compares zeroextended WORD with fullBattle48|Actual private267 lease handle==full common character in existing <=0xFFF projection domain; no truncation|
|5..6|Variant mapping; `(raw&0x6000)==0x2000` selects normal-player continuation and exact2000 produces metadata category4000|CUSTOM-0107 exact2000, other variant flags unsupported|
|7..8|FullWORD copied to metadata+C/actorDBC; nonzero also sets side-list bit8; local role continuation can replace lower flags|Explicit CUSTOM ordinal0; original ordinal/state source OPEN|
|9..24|All16 copied to metadata+E/actorDBE;52D19A passes string to5097D0/model+70|Actual owned primary profile name, projected losslessly for recipient|
|25..40|All16 copied to metadata+1E/actorDCE;52D1AD passes string to509E70/model+81|Actual required saved secondary16/UTF8/codepage/revision; same setter as S23|
|41..44|FullDWORD copied to metadata+8; bit0 canonicalizes whole field to1;5221B0 consumes bit0 and changes actor flags;52D329 selects status9, else bit6 selects149, else0 before526430|Explicit CUSTOM statusDWORD0; original status producer OPEN|

Both complete string setters scan through NUL, prefix max(0,14-encodedByteLength)/2 spaces and copy the string plus NUL. The qualified setters do not inspect a codepage field or S1C status as an encoding marker. Therefore per-recipient encoding is explicit server projection policy, independently justified by the actual Session language, not a native charset equivalence derived from flags0. Native status0 and chosen CP950/CP936 are separate decisions.

The45-byte record is not a complete56-byte actor metadata initializer. Metadata0 highWORD and metadata2E..37 (ten bytes) retain previous actor state, as do metadataDWORD4 low10 bits. Opaque521F20/5220E0 and renderer/resource children remain open. Exact renderer handle/model prerequisites, prior arena initialization and ordinary appearance construction are still required; supplying the complete wire record alone does not establish them. The player side-list primary/third strings are separately populated through4FAC70 and local Battle78/88, not proven equal to these two S1C fields.

## Concrete private source and lifetime

NEW `src/game/OwnedTaiwanPkPlayerEntrySource.h` retains the exact private TW268 combat Observation. That receipt already retains the exact private TW267 appearance Observation, full current root/pose/role/resources/auxiliary/inventory/equipment, actual issued normal entry/private generation and same concrete repositories/connection. It is not replaceable with a caller bool, revision number, digest or copied label.

The new source also owns an immutable full `StoredRoleText` copy and the actual16-byte primary profile field, primary codepage, strictly decoded UTF8 and actual role level. The borrowed `SqliteRoleTextRepository` and all retained concrete dependencies must outlive receipts/tickets and drain before shutdown. The only change to that repository is an identity-only uses_connection accessor; writer, schema, reader validation, project behavior and existing C20/S23 integration are unchanged.

Observation requires the same actual SQLite connection for the text reader and retained combat source. The source owns its real game thread/reentry guard. It rejects TEMP name/tbl_name shadows for character_role_text/recovered_characters and requires both actual main tables before and after the closed reads. The retained combat/appearance closed readers independently preserve their full namespace/root/connection checks.

An outside-SQL Current first requalifies the actual combat/appearance/Session receipt, opens its own consistent read scope, checks all captured combat/appearance tuples in that scope, reads the exact secondary row and reconstructs the complete primary/level material, then repeats actual Current after the scope. Missing rows, changed full text/UTF8/codepage/revision/root/role/resources/auxiliary/inventory/equipment or retired private Session generation fail closed. No live Session/presence/joint callback runs inside the SQL transaction.

For RESERVED room transactions, the source instead borrows the actual open room SQL scope and performs only closed concrete full tuple comparisons, including the complete text row and retained268/267 material. It never creates a nested transaction or requires autocommit there. This guard is consumed by actual prepare/current/initial/activate paths before reservation/activation writes. After activation, text/stats/entry readsets remain frozen admission material; active battle does not demand that a retired world lease or subsequently edited auxiliary/text row remain current.

As before, exact closed SQL tuples do not close the live preflight-to-SQL Session/queue window, establish dual-peer held acceptance, or add global writer interlocks. Later active operations retain their existing common owner/resource/role/position checks. No storage migration or name/secondary edit is performed by the new source.

## Encoding and complete45 construction

The current `RecoveredWorldReady` grammar rejects config_flag values above1. Session stores that exact accepted flag in recovered_client_language. The private267 material retains the flag and accepted raw tail. Mapping is therefore exactly flag0→CP950 and flag1→CP936; an arbitrary nonzero flag is not interpreted as a language. Existing protocol selection and language preference remain independent.

This bounded source requires actual primary name_codepage936 or950. Unknown0 is rejected, including ASCII; no inferred source page is introduced. The primary must contain a nonempty NUL-terminated name in its owned16-byte profile field. It is decoded and encoded back exactly using the stored page. Output uses strict LegacyChineseCodec::encode/decode roundtrip, rejects NUL in the encoded prefix and any length above15. It does not call encode_display, which has replacement/truncation behavior. No question-mark fallback, glyph substitution, vocabulary conversion or saved-value rewrite is allowed.

Secondary text uses the unchanged strict `SqliteRoleTextRepository::project` for each recipient page. The full stored row remains retained. A missing row rejects; an actually saved empty canonical string remains a valid supplied source value. Unrepresentable output or more than15 encoded bytes rejects the whole new projection rather than clearing the secondary field or mutating its storage.

The producer builds all45 bytes internally: opcode, relative position, actual level/full identity, explicit exact2000/ordinal0/status0, and both complete canonical16-byte strings. Zeros after each NUL are explicitly custom string serialization; native metadata copies them, so they are not claimed globally unused. No externally supplied S1C identity can substitute for this producer. All source raw profile/text/UTF8/codepage/revision values remain available in the complete readset.

## Actual entry and room consumption

`RecoveredPkEntryProjection::prepare_waiting_notification_owned_players` accepts the two new private observations, separately qualified complete HP/MP templates, actual raw View inputs and actual Fight catalog. Each template's resource kind/current/max must exactly match its private268 source. Opaque vital WORD3/4 and tail13..16 are preserved without being guessed or newly declared unused. The factory supplies each Player's character, complete generated identity, actual267 appearance and checked vitals to the existing owned/catalogued entry path.

The original Player structure held one identity shared across both views. This new factory instead generates the first view in recipient0's actual page and rebuilds the whole second view in recipient1's actual page. Each recipient sees own0 and opponent14. Four complete45 identities are retained in order viewer0 own/other, then viewer1 own/other. No first-view encoded text is merely position-rebound and relabeled for another page. Full ordinary appearance/Fight lookup behavior, friendly HP/MP coherence and waiting-grant schedule remain unchanged.

Prepared retains both privately minted player observations and the four exact generated identities. Existing repository prepare_owned consumes that Prepared and the exact268 combat sources to derive roles/resources/BattleActors/internal digest. Public Input validation additionally requires these same private combat observations and regenerates all four identities for their exact recipient pages. This mode cannot attach a new identity source to unrelated actor/profile material or trust a caller profile hash.

The conditional owned_player_entry_source readset stores CUSTOM-0107 authority/domain, complete primary source16/codepage/UTF8, full secondary16/UTF8/codepage/revision/current149c/CUSTOM0056 identity, actual level, exact recipient pages and all four45 byte records. The existing full267/268 readset already retains the complete common roots, private normal entry/tail/language, full role/resources/auxiliary, inventory/equipment and four side-qualified Fight selections, each with four component rows (sixteen row references, possibly repeated). Existing internal CUSTOM0106 digest includes the new source fields and complete actual entry streams. It remains a binding, not skill authority or proof of original formulas.

Old factories and Inputs without the new private source keep their old bytes/readsets and default behavior. No new Room.h, Session, Application or transport API was needed. One shared Battle remains the backend model; no duplicate mutable battles were introduced.

## Remaining entry authority and next dependency

Raw S82 contexts remain separately supplied complete records. Their original gameplay meaning/producer is not recovered; context_b lowBYTEFF is observer mode, while the local identity comes independently from2A→Role0→T0→Battle48. Do not derive raw contexts from a character or reservation ID.

S88 still needs a supplied qualified full counter/14-pair record; the original counter is not derived from2A/DA/role. Full17-byte86/5 grant material and its action policy remain separate, with the existing waiting initial0B/two-control schedule. Complete supplied vital opaque templates, native renderer prerequisites, learned skills/controlled actor/context policy, actual common RoomAuthority and PK-world-generation resolver remain open.

The next concrete hosting dependency is a distinct asynchronous dual-Session native entry publication after69 Accept. It must reserve both full encoded entries, install actual input barriers without reinterpreting old in-flight world bytes as battle commands, own exact private Session/normal-entry/current source identity and consume both held receipts before single common activation. Precommit cancellation and postcommit partial-I/O recovery must be explicit. Existing skill/world senders cannot be silently broadened or relabeled; ordinary queue submission and local socket success are not client ACK or processing acceptance.

The current native flags/ordinal original producer remains OPEN even though the restricted CUSTOM producer is complete on the wire. This round does not restore original monster attributes, server combat formulas, every S1C variant or complete PK playability. Shared64 money/EXP/damage/HP objectives and exact coin-only cap remain unchanged; legacy unsupported widths continue to reject without clipping.

## Immutable source evidence and accounting

Native terminal agents/native/seal.json SHA7545bec5b662f77b0fa87c8543319d7916a2e78027a7f980a7e6ef706d5a6b8e,67 members/6,719,073 B. Findings SHA54bf908566daeb2f6eba2fecf5e85ff946475e4cf59dc1197af069236e592757. It retained30 full inputs,13 read spans,8 qualified spans/4,869 code bytes/1,566 instruction sites, five new complete functions plus one retained complete function. Selected PE/mapped spans agree; no native code was executed. All67 member hashes were independently matched and full bytes retained by the source worker.

Own truebefore retains111 files/18,448,174 B,82 source files. Supplemental full RoleText.h/.cpp and LegacyChineseCodec.h/.cpp were captured before edits, matching root's separate truebefore: header1450B ae8a94b030287a086683e02410785b92f2da21cd5296def8959bf2d0d80a9511; reader/writer6602B7e5a327bb81224bebd9871f18a458fbe65d855728d2510a94603beb9ab25579e; codec header815B480d7e2db7d55360724bde9fe96d71d5df75a4a77a27e2c56901eb0150dfab30; codec implementation3869B4f1339755eb858558f0ee74e8f37c0c19a331efd71b80ec41133ec5f0763732e.

First candidate four full source files/76,250 B, manifest SHA5bfae35abe544758cd4fab7a9f94a2695f71ee5d817c989791a0965eb8087f78. Paths: NEW src/game/OwnedTaiwanPkPlayerEntrySource.h; modified src/db/SqliteRoleTextRepository.h, src/protocol/RecoveredPkEntryProjection.h, src/db/SqliteOwnedPkRoomRepository.cpp. Complete original before bytes, first candidate and full diff are retained. Independent full code/diff review found zero bounded implementation blockers; no code refinement was requested.

Root registered CUSTOM-0107 append-only: all104 prior records retained,105 total. Policy SHA6f1b5734f737f8de39301d0a1965064fb5d31c85501c7ccc99766002338a0aef. Root owns ledger/book/report. This source adds one bounded custom owned complete player identity/entry material path, zero new opcode values, zero request/reply/phase associations and zero completed hosted gameplay routes. Existing source group counts are not whole-game completion. TW/full-game packet denominator and completion percentage remain unknown. Independent terminal review is recorded externally in the root round report to avoid circular document/seal pins.
