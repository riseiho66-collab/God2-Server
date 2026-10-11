# TW265: current owned player appearance to ordinary battle appearance

## Result and scope

This round recovers the selected current-TW ordinary S86/4 consumer readset,
its Fight resource key/family dependency and the exact current owner-material
boundaries. It does not implement a world-to-battle appearance producer. There
are zero C++ changes, zero new CUSTOM policies, zero new source branches and
zero new complete request/reply or gameplay routes. No native execution, asset
decoding, codec execution, build, compiler, test, server, database/SQL,
migration or deployment was performed.

The tempting same-width packed8 copy is rejected. World HeroDoll and battle
HeroDoll_fight are different resource catalogs with different key construction.
An eight-byte field and a valid actor identity do not supply this missing
semantic correspondence. The existing complete17-byte battle record remains
an input contract, not a recovered producer or a native renderer receipt.

The new native observations use the pinned mapped149c build and selected
original-PE spans with the native worker's explicit byte comparisons. They
must not be described as whole mapped-image/PE equivalence. Addresses in the
new native section below are VAs; addresses quoted from the September notes
retain those notes' RVA convention. This work does not reopen the frozen
461AD0/4607D0/461270/501810/502210/4FD160/4FC720/4FC6A0 interiors.

## Complete ordinary S86/4 readset

`RecoveredBattlePlayerAppearance::Record` preserves the complete logical17
record. Its selected accepted profile is opcode86/subtype4, position0..27,
mode1 and specialWORD0. The native bounded ordinary branch and shared tails
qualify the following direct record reads, not all S86 variants:

| Logical offset | Selected ordinary use |
| --- | --- |
| 0/1 | S86/subtype4 dispatch; existing codec retains both |
| 2 | Actual recipient-relative position/side/slot |
| 3 | Mode1 branch selection |
| 4..11 | Complete eight-byte packed resource selectors/variants |
| 12 | No direct read on the selected complete branch |
| 13..14 | Special WORD gate, required zero for this branch |
| 15..16 | No direct reads on the selected complete branch |

The selected branch does not pass its original packet pointer to children;
children receive extracted values, resource rows/string pointers or the
retained56-byte metadata snapshot. This is bounded branch-level negative
readset evidence. It is not permission to discard or silently rewrite bytes
12/15/16 in an existing supplied record, assert them ignored in other modes,
or claim that opaque resource/renderer descendants succeeded. No new
canonical-zero policy or server-generated template was introduced.

## Fight resource families are not World HeroDoll families

The ordinary path's final packed pair at logical10/11 calls `454F60`.
That wrapper selects fixed family1/component3 through `454E50`, with the
packed low nibble, high nibble and low five bits as its qualified selector
inputs. The returned actual row's byte+2A supplies the family for subsequent
component0, component2 and component1 lookups. The separately selected
component2 row supplies byte+2B for component1 ordinal: when that row byte is
at least2 the branch adds logical7 low5 modulo256; otherwise it uses only the
row byte. This is not the final component3 row supplying both derivations.
These values originate in actual resource records, not a caller-designed family.

Battle helper `454E50` formats key `r%d%c%d%c%d%02d`, using side characters
`15` and component characters `bfhw`, and the battle resources under
`\Data2\Fight`. The actual Battle constructor requests
`HeroDoll_fight.csv` loading and establishes catalog ownership at Battle+132740.
The catalog contents are conditional on the runtime loader succeeding; this
static trace does not report a successful current load.
The constructor510BB4 calls loader454B30 with string59C62C
`HeroDoll_fight.csv` and prefix5847D8 `\Data2\Patch`. The bounded loader
uses stride2C records: concatenated columns0/1 supply the lookup key, column3
the filename, column4 is stored at row+2A by454D9C and column5 at row+2B
by454DB9. Reset helper454B00 writes cacheWORD+28=FFFF only when its existing
row count is positive. The constructor454A3F and fresh loader454BA0 set
rowcount+121F0=0; the loader calls reset at454C1B before populating rows, so
454B0A skips the loop. Freshly loaded row cache initial values remain OPEN.
This closes the direct catalog loader
layout without decoding current compressed rows or proving resource handles. The selected readset and family origin are
qualified without inventing successful lookup rows, handles or resource
construction. Loaded catalog/source-row eligibility for a proposed character
remains a required independent input.


The exact helper key is
`r{binary+1}{sidechars[side]}{family}{bfhw[component]}{category}{ordinal:02d}`.
Component0 uses logical4low4/high4 and logical5low5; component2 uses
logical8low4/high4 and logical9low5. Component1 uses logical6low4/high4 plus
the separately derived ordinal above. The high3 bits of logical5/7/9/11
supply per-component variants. The eight packed bytes also reach actual actor
DDE/DE2 through the shared metadata tail. If the initial last-pair lookup
returns null, TEST ESI at5183BD and JE at5183BF skip to success epilogue518A79: returning from this
branch is not proof that an actor/resource was constructed. No default family
is qualified for the missing row.

The root retained the currently available compressed input:

- `HeroDoll_fight.csvZ`, 36,974 bytes,
  SHA256 `1195afeeb060d7d81c07e65476da8089d5ab72edea90971d72a07f20863338b8`.
- Receipt copy: `root/native-resource-inputs/HeroDoll_fight.csvZ` under the
  TW265 archive. `root/native-resource-inputs/source-witness.json` records exact source/current copy.
- The preferred plain `HeroDoll_fight.csv` was absent at the inspected source.
  The compressed bytes were copied/hash-retained without decoding. This does
  not qualify decoded rows, a catalog schema import or current issuer authority.

The independently retained September same149c notes qualify bounded fresh
world/preview HeroDoll relations, with explicit source-selector0 and fresh
native-constructed component domain. They describe `HeroDoll.csv`, its own
world keys/row identities and component derivation. Those historical probes
were not rerun this round. Their matching four primary records in that domain
cannot qualify Fight catalog rows or the battle helper's different key.
Filename coincidence, matching packed widths or matching neutral selector
numbers is insufficient. The original binary1 intermediate row mismatch in
those notes remains retained.

## What the actual server already owns

| Source | Actual retained material | Boundary |
| --- | --- | --- |
| `RecoveredWorldEntryView` | Complete Frame42 decoded to logical37; components logical13..20, transformWORD33..34, scalar35/36 | Entry baseline only; not current after every DA/equipment event |
| `NativeWorldEntrySnapshotRepository` | Full original frame, client/source pins, account/character root, position and revision | Loading a row alone is not a current source receipt |
| `SharedTaiwanStoredWorldEntrySource` | Repeated complete current snapshot/common-root/position/map reads plus actual Supply/Current qualification | No current battle appearance conversion or Fight catalog proof |
| `NativeEquipmentSnapshotRepository` | Complete1215-byte inventory+DA population, actor_handle, common root/position, source/build pins and revision | Actor handle is distinct from full common character identity |
| `SharedTaiwanNativeEquipmentPublicationSource` | Exact writer's private durable Committed token (or joint canonical/equipment token), exact ready lease/actor handle/position and repeated current reads | World publication does not prove battle resources or rendered after-state |
| `RecoveredPkEntryProjection` | Two complete actual S1C identities, two supplied complete86/4 records and exact recipient-relative entry material/readset | Rebinds qualified position only; it has no current-world-to-Fight producer |

The world snapshot's `record` is an encoded zero-seed Frame42, not a raw
37-byte logical message. A source must use `RecoveredWorldEntryView::read`
and preserve the complete original frame. Treating it as logical37 would
shift the component offsets and lose framing provenance.

The equipment population includes a complete DA15. Its layout is actorWORD
logical1/2, transformWORD3/4, scalars5/6 and packed8 logical7..14. It is owned
current material only under the same writer/lease/version/readset fences;
a digest, an arbitrary successful qualification callback or a repository load
without current ownership is not an issuer. The old6bf appearance repository
and fixtures do not supply current149c authority.

## Local DA cache and remote saved state are different

The newly retained current local DA path `503F61..504022` consumes payload+6
(logical7..14), calls opaque461270 and setters, and after opaque502210 copies
both DWORDs to Main+1539ADC0/C4, the Role+4584/+4588 baseline location.
This is a complete local packed8 cache copy at the named source edge, not
merely an odd-byte variant merge. Because the copy occurs after opaque helper
calls, this does not prove those helpers preserved the original payload before
the copy; the direct final DWORD source-load/copy is the qualified fact. It does not qualify all opaque descendants,
a durable server after-state or battle catalog semantics.

Remote `4FC130` instead updates the saved odd-byte high3 bits. Its saved cache
must not be treated as a complete copy of DA's packed8. Conversely, that
remote merge limitation must not be generalized to the local path. A future
owned appearance supplier must specify which actual local/remote material it
retains and when; it cannot infer whole battle renderer state from either one.

## Concrete remaining integration edge

The next useful source increment is a build-qualified World HeroDoll to Fight
catalog correspondence with complete actual source rows and their family/
ordinal derivations. It must retain the relevant current owned world baseline
and equipment/local-DA material under one coherent account/character,
actor_handle, root, position and revision readset, qualify exact resource
eligibility, and repeat those source fences before the existing Prepared
material is admitted. It must supply complete ordinary17 bytes through an
actual issuer rather than fabricate consumed fields from zeros or depend on
an unhosted generic callback.

A bounded implementation may preserve explicitly supplied complete native17
material. Generating a new record still requires either source-owned values
for every retained field or a separately justified, explicitly versioned
wire policy for branch-qualified unused fields. This round chooses neither:
consumed packed selectors remain unmapped across the two catalogs.

The current Application PK peer witness retains normal-world initialization,
root/position and roster information; it does not instantiate `pk_rooms` or
supply complete current combat/skills/battle appearance authority. The real
shared RoomAuthority, two exact entry recipients, held publication/input
barriers and I/O recovery remain distinct OPEN integration work. No two
independent diagnostic Battles, old profile, SHA-only authority or default
zeros were introduced as substitutes.

## Receipts and accounting

Archive root:
`C:/Users/risei/.codex/artifact-archives/god2-server/20261011/tw-pk-player-appearance-source-265`.
Source worker retained all69 root truebefore files, 18,046,809 bytes;
`agents/source/before-manifest.json` SHA256
`887a200b445cf3b3bdb092826cea74a31d9f9defeeee3ea3fe98157f9435dbe5`.
Nineteen full current/historical source inputs are separately retained in
`agents/source/inputs`, 99,066 bytes, with manifest SHA256
`2e6ded2bb9c3984dbbcf7d6e41b9de0c288145119ba43c2f222cb3a87466fd7b`.
The initial rejected same-width producer proposal and the local/remote
correction are retained in worker analysis. No prior native receipt is
replaced. The native terminal receipt is independently retained in
`agents/source/native-sealed`:

- Native seal SHA256
  `e7423bc5e931bf4d3870f084875ed9aacc45b912ac315e860c7be397659c50f2`,
  112 members /6,828,803 bytes.
- Findings SHA256
  `7eab8b2555c250c48163fe02a0cc6c91e0e010c5494d0bc758664008d096ebfe`.
- Thirteen qualified code spans, 4,303 unique bytes and1,324 instruction sites;
  39 total retained read spans,5,584 unique bytes. Exploratory following spans
  and clipped tails are preserved without promoting them to qualified sites.
- Mapped image149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763;
  original PE5fcf8cbfaf31d2635b4541886336293249cde61c0877de6f5a435cc2b9559fde.
  Only the selected compared bytes are equal; whole images are distinct.

All50 captured `src/` inputs,1,412,621 bytes, remain byte-identical to truebefore.
The independent review terminal seal is recorded in the root round report.


### Supplemental address precision correction

The retained native terminal findings use5183BE for the missing-row branch.
The immutable disassembly actually records TEST ESI at5183BD (`85f6`) and
JE at5183BF (`0f84b4060000`) to518A79. This document uses the exact instruction
addresses. The original native seal/findings are preserved unchanged; the
source receipt retains a supplemental correction and the prior document epoch.
The conditional branch semantics and zero-source-change decision are unchanged.


### Supplemental fresh-row cache qualification correction

The original native sealed findings describe row+28 as initiallyFFFF through
454B00. REVIEW265-02 distinguishes that conditional reset helper from the
actual fresh loader:454BA0 sets rowcount0,454C1B calls reset, and454B0A skips
its FFFF-writing loop for count<=0. Constructor454A3F also starts count0.
No fresh-row FFFF initialization is established by these selected bytes; it
remains OPEN. The previous document/seal epochs and immutable native findings
are retained. This correction does not create a resource issuer or source route.


The independent native supplement confirms both precision corrections without
changing the original112-member terminal receipt. Its seal SHA256 is
`c0b17405d04bb688260b74bf1a47360906339fd3c65a487babce0b153a5e3c78`,
17 members /6,427,584 bytes; correction JSON SHA256 is
`ccf6a8b959ac029fd1eb50c61b0ca013e135a97e0576e25165753d8f36ff92fb`.
Its retained copy is `agents/source/native-supplement`. No new native trace
or execution is included; it rechecks the already retained instruction bytes.
Independent review terminal sealing remains in the root round report.
