# Round325: common quantity64 and complete equipment state boundary

Round324 made progress by completing a bounded static request-context cut.
Current checkout was clean at284100068dc920d5d9aa34f075bf18bc46c2ae04.
This round keeps the full TW/CN/web goal active and adds a concrete shared
quantity-domain call in the actual common inventory validator. It does not
provide the missing C28 equip Action or count a new complete gameplay route.

## Actual source change

OwnedInventoryInstance::quantity is uint64. OwnedStackQuantity previously
accepted uint32 input for construction/increase/decrease; a caller passing a
wider common value could lose high bits before its99-domain comparison.
The three input signatures now accept uint64. Construction narrows to BYTE
only after count<=99; increase compares amount against remaining capacity
before addition; decrease compares against the bounded current value before
subtraction. The output remains0..99 in the original bounded BYTE domain.

SqliteOwnedInventoryRepository::valid directly passes the complete common64
quantity to this domain. Its old literal uint64 comparison already rejected
out-of-range stored quantities; this is not a claim of a live saved-quantity
truncation defect. The new call unifies the existing99 policy with the actual
common storage source without introducing narrowing at that call.

An occupied instance still requires nonzero quantity, and unstackable instances
still require exactly1. Empty-cell absence, full instance IDs/acquisition
receipts, aliases, revisions, before/next populations and whole-state CAS are
unchanged. The existing validator is used by load, validate_change and guarded
stage_replace, including both joint equipment transaction paths. The existing
scalar move's two domain calls continue to pass their original bounded values.
Increase/decrease have no new mutation callers and receive no integration
credit. No merge, split, destination, grant, stackability or native metadata
rule is inferred. SQL schema99 constraints and saved values stay unchanged.

CUSTOM-0089 retains the original fields, including historical activation text,
and receives a uniquely named325 addendum. Existing CUSTOM-0092 common custody
is consumed; no new custom ID or balance value is introduced. The source
qualification added here does not remove either native client's30 count clamp,
extend all UI paths or certify full PC/web quantity99 behavior.

## Genuine equipment authority cut

The independent bounded review of22 complete current small source files finds
no original ordinary equipment-to-stat/DA producer in that scope. Definitions
and source columns, full owned20 aliases, D1/D2 observations and saved native
cache/DA witnesses remain distinct from a rules issuer. Current Lua beast
equipment is CUSTOM-0085; ordinary weapon/armor Application branches retain
their historical CUSTOM/fixture qualifications.

A further concrete omission is now explicit:320's three-population
WithEntryState holds custody, native1200+DA15 and full entry40B, but does not
hold self2C/role/resource after-state. The read-visible role auxiliary source
is hard-pinned6bf/CUSTOM-0045 and the PK reader adopts saved values under
CUSTOM-0106. Neither is a149c ordinary-equip stat settlement authority.
Adding another wrapper around the three populations would not supply this
missing state or make their transaction a complete equip/stat transaction.

The next real evidence must identify the current149c ordinary-equip producer
for self2C/22/24 and the owned20-to-DA15 result in the same rules operation.
4E6600/4E6DB0/4E8514 are consumer-side cuts, not producers. Source column1's
separate actual reader or a genuine same-owned20/DA paired transaction remains
a possible mapping frontier; the known481700/41AE70 icon path is not one.
No repeated panel/helper/packed-loop search is credited. Full sender/stat/
self/observer order, original eligibility/replay/destination and post-COMMIT
recovery remain necessary for the actual Action.

## Accounting and limits

Two existing C++ source files changed; one common64 quantity-validation call
added. New native methods/bytes/opcodes and complete gameplay routes0.
TW C2S156 candidates; world74=partial50/control11/unconnected13;67.6% remains
partial parser coverage only. S2C252=fixed230/variable22. CN C2S156, S2C
phase280 and length253 remain separate scopes. Mixed282/groups26/pending10/
CUSTOM135 unchanged. Whole-game denominator and completion percentages null.

PHASE1 source read/edit, exact file custody and static accounting only. No
compiler/build/test/runtime/native/VM/emulator/resource codec, game DB/SQL,
migration, activation, deployment or client modification. Native wire/layout,
shared tables, CN/web, numeric64/coin99999999999/stack99/native levels, saves,
authentication/chat/IME/portraits/fonts/text conversion remain within the
original scope. No current-client acceptance is claimed.

The immutable authority review is at
`C:/Users/risei/.codex/artifact-archives/god2-server/20261012/tw-equipment-authority-source-review-325`;
24 members/129027B (25 files/134008B including seal), seal SHA256
`3401440af868639515c2f2a093dd4d74d1e7a14bcdb1bb4eddae8ba2018a6686`.
Source before/after and unique round report are retained separately under
`C:/Users/risei/.codex/artifact-archives/god2-server/20261012/tw-owned-quantity64-source-325`.
