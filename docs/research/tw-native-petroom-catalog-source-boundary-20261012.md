# Round335: PetRoom lookup namespace and actual source boundary

The F4 list reader and the selected full20 PetEgg reader use the same native
catalog pointer and lookup namespace. This closes the lookup-source boundary,
but does not identify an eligible owned population, an operation issuer, or an
authoritative B1 gameplay route. Existing F3/F5 codecs remain unchanged. No new
format, parser opcode, phase binding or complete gameplay route is credited.

## Actual catalog and key sources

Pinned mapped image149c and originalPE5fc are hashed in place. Complete lookup
459A60..459A7E compares the unsigned lowWORD with7F58h, masks toFFFFh, and
returns DWORD[catalog+B2D40+4*key]; the other branch returns zero. It does not
select a category or prove that a returned pointer is an owned instance.

Complete row loader4599B0..459A5F reads a signedWORD row count, allocates rows
with396-byte stride and uses source token0 to register row pointers in that
shared table. Registration459A20 is an interior instruction of this loader,
not a separate function. The directly observed positive-key registration has
no matching reader-style7F58h upper guard; this is native-source description,
not permission to admit arbitrary server catalog keys. Duplicate registration
can overwrite a table pointer; this differs from server unique-family checks.

The loader forwards the actual row pointer and category arguments to complete
generic parser459420..45995F. MetadataDWORD0 comes from token5; the independent
token0 registration key must not be replaced with that metadata value. The
list label reads metadata+8, populated from token4 by the generic parser. A
label string is not an item ID or proof of entitlement.

Complete category loader459150..45937D builds1602-byte category rows and scans
36 tag pointers at5897EC..58987C. Complete459380..45941B matches the category
name and returns category ordinal/selector bytes. Historical address4591C0
is an interior token-reader call in459150. Actual section dispatcher
456130..4570D6 calls459380, then4599B0 on a match, and separately recognizes
the itemtype section. These paths distinguish category selection during load
from the category-independent459A60 lookup. The recovered tags are static
native strings; no current resource bank was decoded or imported this round.

Complete4DC710 reads WORDs from primaryU+0A+2*i, filters unsigned1821h..1838h
and calls459A60 using the catalog pointer stored at[U+CFF70]. The full20 PetEgg lookup
span4D5472..4D54B3 uses that same catalog pointer and lookup for its firstWORD.
The same namespace is proved; row identity, slot identity, operation selection,
F4/B1 causality and present contents are separate unresolved facts.

## Existing source qualifications

NativeItemDefinitionObservation retains full396 bytes and the independent
native key for historical70a4 encoded/75c3 decoded catalogs parsed by149c.
SqliteOwnedInventoryRepository::observe_native_definition requires the actual
complete TWP/WPN and EQU/TEQ catalog qualifications and one unique matching key.
No match returns no observation; multiple qualified matches throw DatabaseError.
Those four historical families are not a complete native shared pointer table
or a current PetRoom bank. No database row presence/absence was queried here.
The header now makes that lookup/category distinction explicit; behavior,
catalog data, transactions and saved values are unchanged.

The qualified Host request path supplies an actual C28 occurrence. Its
SharedTaiwanOwnedItemSelectionSource reader selects an exact current
tw149c-item20 owned alias from the supplied key and slot; the reader does not
attest wire receipt, freshness or action permission. Its current scene/session
lease and optional definition observation do not define F4 list eligibility
or a B1 action. SharedTaiwanOwnedItemRequestSource still requires the caller's
complete Action and ordered reply. The actual world B1 parser branch accepts
only the separately gated client-options7/8. Companion storage's pet1/type32
and pet2/type34 instances/catalogs do not directly map F4 words6177..6200 to
their respective accepted COM/NCP keys. These are bounded inspected-source
findings, not whole-program or database absence claims.

## F3/F5 continuity without duplicate credit

Actual WORLD F3 cell46B9A0 selects469112->4CE290; F5 cell46B9A8 selects
469100->4CE140. Both pass the same primaryU=Main+A7F2F6C. Complete F3 is610
bytes with oneRET4; complete F5 is325 bytes with twoRET4. Their direct high-U
contexts are distinct from the low24-WORD F4 array. Opaque children remain
unqualified, so no global absence or final-state claim follows.

Existing RecoveredBFSourceLists already preserves the F3 bounded grammar;
RecoveredOrangeShopUiUpdates already preserves F5raw29 and variants7/8.
RecoveredTaiwanServerRecords already qualifies the -2 marker as record+1
unsignedTOTAL via4134EE..413590. The isolated335 receiver report's framing
OPEN means it did not independently trace that consumer; the separate codec
review appendix references the established source. No codec is duplicated,
and frontier v23 classifications remain byte-identical.

Fresh receiver continuity preserves two caveats: F5's gate uses stored
WORD U+97C88, and it rereads bodyWORD0 after conditional opaque children; the
first tag cannot stand for final state. F3's MOVZX AX,bodyBYTE6 beforePUSH EAX
does not independently clear EAX's upper16 bits. These observations are not
new gameplay rules, format classes or numeric64 projections.

## Custody, integration and remaining work

The exact successful static capture scripts are published as
tools/reconstruction/tw_native_petroom_definition_key_capture335.py and
tools/reconstruction/tw_native_f3_f5_context_capture335.py. They are byte-exact
copies of retained archive originals; their ROOT-relative paths describe the
original archive placement. Publication does not rerun them or copy input
images. Captured bytes/TSVs, PE offsets and individual seals remain external
under C:/Users/risei/.codex/artifact-archives/god2-server/20261012.

Next source boundary: actual bank-qualified eligible population and original
issuer, action-time selection/ownership, B1 operation/rules/timers/debit/grant,
complete ordered replies, persistence/recovery and actual Application hosting.
Keep shared TW/CN/web tables, common64 domains, coin99999999999, qualified
stack99, native levels/fonts/text conversion and frozen saves/features.
Whole TW/game denominator and completion percentage remain null. PHASE1:
static source/hash/PE/Capstone and unique packet report only; no build,
compiler/tests/runtime/native/VM/codec/gameDBSQL/migrate/activate/deploy.
