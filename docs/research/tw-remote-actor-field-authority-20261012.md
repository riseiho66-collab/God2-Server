# TW remote actor field authority, round298

This round recovers native field consumers and current source lifetimes. It adds
no gameplay branch, opcode, packet emission, schema, executable patch or hosted
route. All production sources remain unchanged. Complete TW/game percentages
remain unknown. Static byte disassembly and source accounting are not gameplay
tests or native acceptance.

Evidence directory:
`C:/Users/risei/.codex/artifact-archives/god2-server/20261012/tw-remote-actor-fields-298`.
The native mapped image is pinned to
`149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`;
the original PE is pinned to
`5fcf8cbfaf31d2635b4541886336293249cde61c0877de6f5a435cc2b9559fde`.
Selected spans are compared with their PE section bytes. This does not prove
global mapped-image/PE equivalence. Existing complete6F/insert spans overlap
round292; newly selected downstream functions are accounted separately.
The nine selected code spans contain3857 bytes/1286 instruction sites. Two
overlap the earlier full6F/insert evidence; seven newly selected downstream
functions contain1822 bytes/628 sites. These are bounded selection counts,
not newly discovered gameplay paths or whole-client coverage.

## Exact fields and limits

Offsets below include the opcode. The native case increments EBX past it at
4695CB; insert4FC1C0 therefore uses body offsets one less than logical offsets.
The table describes observed reads and stores, not original server rules.

| Logical field | Qualified consumer | Source requirement |
| --- | --- | --- |
| DWORD1 bits0..11 | 4FC2C3..2D0 writes actor+0 identity | Actual leased native handle, bounded to12bits; common character ID alone is insufficient. |
| DWORD1 bits12..13 | 4FC39A..3A2 writes actor+260 | Raw two-bit selector; its game meaning is still open. |
| DWORD1 bits14..20 | 469941..9963 resource resolution;4FC44D..456 writes actor+40 | Ordinary appearance selector has a qualified2A projection, but requires current appearance and resource ownership. |
| DWORD1 bits21..24 | 4FC38C..397 writes actor+7A | Exact four-bit field; no inferred level, guild or permission semantics. |
| DWORD1 bit25 | 4695F6..9765 controls three-text conversion against531C10 | Packet text-language selector compared with the actual receiver language. Current common-name projection requires an equal-selector receiver witness; the bit does not identify protocol, receiver, identity or permission. |
| DWORD1 bits26..28 | 4FC23E..26B maps1..7 to0..6, otherwise0 | Rendering input; original gameplay producer remains open. |
| DWORD1 bits29..31 | 4FC35A..36C maps nonzero values down by1 | Raw selector stored at actor+3A; original gameplay producer remains open. |
| DWORD5 bits0..4 | No direct read in the complete selected6F case/insert | Preserve opaque bytes; bounded non-observation is not permission to zero them. |
| DWORD5 bits5..7 | 4FC462..483 maps1..6 to0..5, otherwise0 | Separate rendering input; do not merge it with the first packed selector. |
| DWORD5 bits8..14 | 4FC270..2AA and33F..348 reads seven bits, stores actor+34 | Qualified normal2A component projection exists; a stale entry snapshot is not current equipment. |
| DWORD5 bit15 | 4FC22D..238 stores complemented bit at actor+25C | A downstream name-render colour branch, not PK/permission authority. |
| WORD7 | 4FC211..21E writes actor+60;4FC4AC..51D uses status | Full status word. Role allocation points are a different domain despite equal width. |
| DWORD9 | No direct load in complete selected6F case/insert | Opaque. This does not exclude indirect/alias readers elsewhere in the client. |
| DWORD13 | 4695C8..95F1 and4FC370..389 extract15-bit coordinates | Use current owned position; retain the two low kind bits with separately qualified map semantics. |
| DWORD17 | 4FC26D/277 copies exactly to actor+220 | Exact copy, unresolved meaning. Do not replace it with HP, coordinates, guild ID or zero. |
| Bytes21..28 | Resource path plus4FC27D..28C stores two DWORDs | Current owned appearance; normal and transformation branches remain distinct. |
| Text29/45/61 | 4FC2C3..33D copies to actor+4/+14/+24 | Primary name, qualified editable secondary role text, and an unresolved third display field. All three need actual sources. |
| WORD77, bytes79/80 | 4FC292..296 and3A8..3B8 stores actor+262/+264/+265 | Preserve transformation and scalar fields; ordinary appearance projection cannot stand in for every variant. |

The new colour trace follows actual ID lookup in4FBB50 to509B60, then509990.
The complemented bit is an input to a white/yellow branch; another supplied
byte's low bit can override it with0xFF. This is a renderer dependency, not proof
of which server event should set the bit. Original insert and update status
priorities remain distinct, as documented in the earlier remote actor contract.
Complete4FD770 also consumes the high status byte. Status bit12 affects the
appearance palette and text input; bit13 supplies a separate display toggle.
These dependencies must be retained by a future complete actor issuer; merely
copying ordinary appearance bytes does not qualify every status variant.

An exploratory whole-text operand census found other+220 operands. Selected
leads use Main/local objects rather than a qualified remote actor base. They are
retained as excluded leads; there is no proven remote actor+220 read or original
server producer from that scan. Opaque children, aliases and indirect paths
remain open. The full packet is still mandatory.

## Current authority is not the entry delivery witness

`SharedTaiwanNativeWorldEntryOfferSource.cpp` invokes the entry snapshot writer
before initial delivery. `SharedWorldPresence::commit_owned_step` instead commits
the common character position through `commit_position`; it does not refresh
the raw2A snapshot. Equipment publication uses its distinct committed equipment
snapshot and a visibility appearance receipt. A current owner/generation check
on an immutable `Session::NormalWorldInitialization::Data` proves its lifetime,
not that its original Entry bytes incorporate later movement or equipment.
`OwnedTaiwanPkAppearanceSource.h:167` currently requires the stored2A, original
initialization and lease entry coordinates to agree. The audit therefore records
a concrete stationary-entry restriction, rather than claiming this source
already provides post-movement current actor material. Relaxing its guard would
not recover the missing current raw-state lineage.

The future complete actor issuer must read the same owned common root, current
position/revision, current equipment/appearance and source revisions in one
qualified readset. It must also account for every packed field, actual secondary
and third text, receiver profile, resource result and complete directed audience.
An old2A, diagnostic6F template or retained owner receipt cannot supply missing
values. Ready population alone does not establish visibility eligibility.

`RecoveredRoleLevel::state_word()` is used as remaining allocation points by
`with_base_stats_and_points`; it cannot supply actor+60 status. The old
`RecoveredVisibility::set_fight_title` updates its diagnostic cached6F/5E path;
it is not the full-source authority for the new private return plan. Likewise,
a common guild membership/name is not evidence that text61 or DWORD17 carries
that data. Historical text binding establishes the three display destinations
without qualifying a guild/title meaning for the third field.

Round297's actual common first-name source remains intact. The qualified
secondary role-text repository/projection exists, but full current actor,
remaining fields, resource and complete selection sources are still missing.
The next source task must consume current mutation owners and their revisions,
rather than add another unfed callback or promote the diagnostic actor template.

## Accounting

Source changes0; new connected branches0; new opcodes0; complete gameplay
routes0. Mixed source segments279, CUSTOM records132 and reviewed groups26
remain unchanged. TW C2S candidate union156; world parser74 = limited50,
control11, unconnected13. TW S2C supported lengths252 = fixed230 + variable22;
reply48, push11, gated4, unclassified117. Battle index110, specialised9;
86selectors7/cases6;83actions23/scalar projections2. TW unhosted chains3,
bindings38/unique34. CN unhosted chains35, bindings93/unique71; historical
CN C2S156/S2C phase-opcodes280/lengths253 have different scopes. CN increment0.
Full route denominator and TW/game percentages remain null.

No build, compiler, tests, runtime, native execution, VM, emulator, codec,
game database/SQL, migration, activation or deployment occurred. Frozen
accounts/saves/authentication/chat/IME/fonts/conversion/client executables and
CN/web sources are preserved. The989 captured source files are byte-integrity
inputs, not989 manually reviewed files. Worker read scopes and seals delimit
the actual native and source claims.
