# TW266: actual Fight catalog row source for prepared PK appearance

## Result

This round adds a bounded Taiwan Fight resource source to the existing PK
entry preparation and exact repository readset. It consumes actual complete
ordinary S86/4 records and selects four current149c-qualified resource rows
per recipient-side appearance. It does not generate battle appearance from
world packed8, supply account/character authority, instantiate a shared room,
load ROM resources or claim native rendering/acceptance.

The source increment is one catalog-qualified prepared-material path, with
zero new opcodes, phase associations or complete request/reply/gameplay routes.
Existing factories and their serialized readsets remain unchanged. The new
explicit factory retains the selected row material in `Prepared`, and the
repository includes that material only for this explicit new input profile.
No application/default/schema/client/CN/web/chat/font/account/save changes,
new CUSTOM policy, asset decoder, native execution, build, compiler, tests,
server, game database/SQL execution, migration, activation or deployment were
performed. Existing CUSTOM-0086 and optional CUSTOM-0104 stay labeled.

## Exact available input and provenance

The root restored only the exact needed historical audit from the cleanup
archive with verified=true, preserving its original identity:

- `current-armor-mapping-sources-20261002-run02/native.json`,2,853,351 bytes;
  SHA256 `5500950022f789d1372f92fe2dd6ebee936c2e7f5a04b133c45151f3aabd142d`.
- Historical native audit image:
  `c5d8f79baa36879851703ac05d2b5caddf44a907677f7de114f568eeaf14f575`.
  Its native/runtime conclusions are not current149c authority.
- The `resource_tables/HeroDoll_Fight.csvZ` subsection retains3,578 parsed
  records, seven string fields per row, exact recorded source line numbers
  26..3604, with blank data line2852 omitted. All keys are unique.
- Its encoded-source pin is
  `1195afeeb060d7d81c07e65476da8089d5ab72edea90971d72a07f20863338b8`.
  The root independently retained current installed compressed bytes,
  36,974 bytes, and confirmed that exact pin.
- The historical subsection records decoded SHA256
  `7cf2b923aff6f306115e04f9b680efe35724dfb8a78e71e61cdbf284ae976ace`.
  No decoded CSV was recovered/decoded/hash-verified this round; this remains
  explicitly a recorded historical value.

The representation contains valid Unicode Chinese headers/comments. A direct
UTF8 audit found zero U+FFFD codepoints in the Fight table and zero EFBFBD
sequences in the complete JSON. Initial shell output displayed characters
incorrectly and led to an unsupported lossy-data inference; that inference
and its correction are retained. Valid Unicode parsed fields still are not
original CP950/raw decoded CSV lines, byte offsets or a new current CSV parser
qualification. Every recorded field is retained, with this representation
boundary preserved.

All current-consumed columns0/1/3/4/5 are ASCII. Column4 values are1..6;
column5 values are empty/0/1/2/4. The two empty numeric cells are at recorded
lines3303/3304, keys `r111w110` and `r111w111`. Current149c numeric helper
451BA0 uses signedINT `%d` and failed/missing numeric input yields0;
454D9C/454DB9 store AL. The implementation accepts these exact hash-bound
blank cells as that native conversion, checks nonempty integer fields with
strict full signed32 parsing, and retains the original numeric strings.
It does not accept arbitrary malformed or overflow CSV, or copy the historical
native parser as current-build authority. No original delimiter/header parser
or duplicate-key overwrite rule is inferred.

## Current149c row selection

Current mapped149c image is
`149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
Native qualification and old audit data provenance are separate. Original
PE/mapped equality applies to explicitly compared selected bytes, not whole
images. New native addresses below are VAs.

Battle454E50 formats:

`r{binary+1}{sidechars[side]}{family}{bfhw[component]}{category}{ordinal:02d}`

`sidechars` is `15`; position0..13 selects side0, position14..27 side1.
Formatting preserves native decimal minimum width2, without truncating larger
ordinals. Selected ordinary mode1/specialWORD0 fixes component0..3, and low4/
high4/low5 extraction does not itself prove a resource exists.

| Selected row | Actual source |
| --- | --- |
| Component3/family source | logical10low4/high4 and logical11low5 via454F60; fixed family1/component3 |
| Component0 | Family from component3 row+2A; logical4low4/high4,logical5low5 |
| Component2/ordinal source | Same family; logical8low4/high4,logical9low5 |
| Component1 | Same family; logical6low4/high4; ordinal from component2 row+2B, adding logical7low5 modulo256 only when row byte>=2 |

Resource filename comes from archived column3; row+2A/+2B from numeric
columns4/5. The actual current loader/key interpretation is qualified
separately; no successful present native load or resource construction is
asserted. Fresh-row cacheWORD+28 remains OPEN:454B00 resets existing positive
row counts, while fresh loader count0 skips that reset. No FFFF initial cache
value is manufactured.

The selection preserves the full original17-byte input, including logical
12/15/16, whose branch-qualified lack of direct use does not justify a new
canonical-zero producer. Missing any actual source key returns no selection;
the native missing-row success epilogue cannot be promoted to valid material.

## Actual C++ consumption

`src/game/TaiwanNativeFightCatalog.h` is an immutable in-memory TW catalog,
with no schema or SQL changes. `from_archive` copies the complete bounded
input into owned storage before computing SHA256 and parsing. It requires
exact size/full audit hash, historical image/source metadata, complete row
count/order, seven fields, ASCII consumed columns, exact key concatenation,
strict numbers and unique keys. It retains the complete audit bytes and all
parsed source fields/line numbers. Its SHA backend is the existing platform's
Windows BCrypt; unavailable/failed hashing fails closed. It does not trust a
caller-supplied digest, bool, source callback or object lifetime.

Only this factory can construct its immutable internal source; only actual
catalog lookups can construct a `Selection`. The selection owns the catalog
lifetime and full input17, plus exact component0/1/2/3 rows. Moved-from
catalogs/selections fail closed or report empty/invalid storage. The catalog
is a pinned static data source, not a claim that an installed client resource
file was reobserved at each PK request.

`RecoveredPkEntryProjection::prepare_waiting_notification_catalogued` first
uses the existing validated two-player entry path. It then selects resources
AFTER actual recipient-relative position rebinding: viewer0 own0/other14,
viewer1 own0/other14. Four selections are required; either side missing a
resource rejects the preparation. No side canonicalization or borrowed row
from the opposite side is permitted. All complete86/4 bytes remain supplied
and unchanged except the already qualified position rebind. This new explicit
factory retains those four selections in `Prepared`; existing factories retain
no catalog field and keep existing behavior/entry bytes.

`SqliteOwnedPkRoomRepository::readset` conditionally serializes the full17
input for each relative view, all selected row fields/index/line/key and native
numeric bytes, the exact audit/source pins, old audit image and current helper
image separately. The representation is named
`pinned-historical-parsed-fields-v1`; the decoded hash key is explicitly
`recorded_decoded_sha256`. No original raw-row/offset/CP950 claim is made.
An old ticket/readset is not reinterpreted. Ownership/resource/current saved
state validation, two-phase initial controls, separate postcontrol grants,
shared Battle and later exact resolver masks remain the existing paths.

## Why world8 still cannot be copied

The current world helper normalizes category through452260 and formats the
shorter World HeroDoll key. Battle adds side/family and does not use that
world normalization. World component1 derivation uses component2 row+2A;
battle uses component2 row+2B and separate component3 row+2A family.

The restored tables provide concrete counterexamples: all569 distinct Fight
bare keys appear in World, but349 World keys have no Fight bare key. World
`r1h031` has derived value3 while its corresponding Fight row has value4.
Five side-paired Fight keys have differing numeric field strings. Three
(h031/h212/h213) differ in parsed column4 bytes2 versus1; two differ only as
empty versus literal0 in column5, which both become native0. The component2
row column4 is not the family source in this bounded consumer (component3
supplies family), so these are not five proven differing native outcomes.
For example `r212h031` column4=2 versus `r252h031` column4=1 is retained as
row provenance. Matching filenames, key fragments or packed widths do not
authorize copying or collapsing sides.

A positive bounded historical fresh-preview domain is separately retained:
`P=[b,f<<5,b,s<<5,b,0,0x80|b,0]`, b0/1,f/s0..6, action0. Static Fight
lookups on both sides resolve component3w800 to family1, component0b000,
component2h000 with row+2B2 and component1f002. This closes four row selections
for that domain. It is not a current equipped-player supplier, a whole
profile conversion, ROM/render success or a complete ordinary86/4 producer.
The new catalog does not fabricate such a producer from this example.

## Remaining source boundary

A real admission producer must join current owned Frame42/logical37 baseline
and full1215-byte inventory50x24+DA15 snapshot with exact account/character, actor_handle, root,
position, revisions and repeated final current fences. The local DA final
fullDWORD cache and remote odd-high3 saved merge remain distinct; opaque
461270/502210 effects are not newly expanded or asserted to preserve payload.
It must recover or explicitly justify all ordinary86/4 source bytes, current
Fight family/category/ordinal eligibility and equipped-item lineage before
using these immutable catalog selections. A hash or valid resource row grants
no combat/profile/skill authority.

Actual Application `pk_rooms` hosting, RoomAuthority/profile supply,
recipient queue reservation/held entry barriers and I/O recovery remain OPEN.
This is a consumed backend source increment, not a hosted full shared-PK route
or native client acceptance. Existing CN parsers/content were not reused as
TW authority. Frozen gameplay/account/save/client/font/text behavior is intact.

## Receipts

Archive root:
`C:/Users/risei/.codex/artifact-archives/god2-server/20261011/tw-pk-fight-catalog-source-266`.
The source worker retained73 full truebefore files /18,093,503 bytes;
`agents/source/before-manifest.json` SHA256
`6da84538b7cb97952d1ea673791d0e3d56e42be806375a0ebaada46545c0a201`.
Exact historical native.json/extraction receipt and immutable source candidate
are retained. Native terminal seal SHA256
`54e7b7d8a6cc1f9342b92e5b96373b16b6e422b0a347302430d84ccdb2bc8b07`,
73 members /10,399,483 bytes; findings SHA256
`81669497f890413fe9f07791f2067f4d197abc60803e6dfbe3b944c12b68de32`.
Six newly qualified world helper functions comprise847 bytes /257 instruction
sites;15 retained read spans comprise1,264 bytes. Prior TW265 Fight helpers
and corrected cache/address receipts are retained, without counting their
qualification again. No whole mapped-image/PE equality or execution is claimed.

First C++ candidate retained3 files /57,612 bytes. REVIEW266-01 fixes only two
comments which incorrectly inferred Unicode replacement from console display;
no parser/row selection behavior changed. Immutable refinement2 retains3 files
/57,611 bytes (one new header, two modified files):

- Catalog11,076 bytes, SHA256
  `bce9937cdbc084f34a1d211df81d57d33fb3a9806b275d9782955101731c9b0f`.
- Projection10,973 bytes, SHA256
  `437a7ca8c2c1726e083a09853a50808f2bf9395279669c98e6dde05416b85666`.
- Repository35,562 bytes, SHA256
  `c834220fa20c7e3e77165bb991fb27d6d85e35cfe5fe8283fe589e88f28eb5c8`.
- Candidate manifest SHA256
  `d9e1a8b4419d0f862718f27130dade31ecafc2d972a947f110b0b9fc1923d2af`;
  full truebefore diff SHA256
  `57f27876fdfb9bc431c7ff91c06c39c0d90fec099dd547d8b29f6b1802fea2d1`.

The source worker retains exact full native terminal inputs/receipt, current
compressed resources, original audit/extraction receipt, source epochs/diffs,
Unicode correction and full immutable final document. Root owns policy/packet
accounting; this round adds one bounded source-material path and zero complete
routes/opcodes. Independent review terminal is recorded externally in the root
round report to avoid circular document seals.
