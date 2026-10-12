# Round339: common RomMaps source storage and SPI resource projection

The common raw-resource source catalog now preserves all57 historical RomMaps
records and exposes a strict complete-dataset reader and explicit atomic importer.
NativePetRoomSourceCatalog composes that source with its exact22 SPI definitions
in one SQLite transaction view to project the generic parser's WORD116 source.
Both datasets must be installed and complete before a key or range lookup.
This is conditional source implementation. No importer/API/database/native code,
resource decoder, build or test was executed, and no gameplay route is activated.

## Actual loader, lookup and object-field relation

Pinned mapped image149c and originalPE5fcf remain unchanged and hashed in place.
Actual dispatcher CALL456268 targets459EF0, not the earlier459F47 interior
fragment. Complete loader459EF0..459FB7 is199 bytes, range consumer459FC0..
459FF7 is55 bytes, and allocator547E23..547EB0 is141 bytes including its
reachable cold tail after RET547EAB. The three methods total395 code bytes.
These cuts are byte-equal in both images; no method or opcode is recredited.

The literal RomMaps branch requires the preceding category lookup to return0.
The loader takes the converted header count's LOW16 as signedWORD, stores that
count at catalog+D2D54, allocates84h*count bytes before its signed-count gate,
and stores the returned pointer at+D2D58. It has no positive-count null guard.
It consumes at mostcount physical rows. Converted token0 selects the destination
slot; valid duplicate slots can overwrite, invalid slots still consume a row,
and a failed read can leave a suffix unpopulated. Its return1 also covers early
read termination and nonpositive count; it is not a full-population certificate.

For a valid slot, tokens1/2 supply LOW16 range endpoints and token3 is copied
to slot+4. Token4 is unread by this loader. Allocator multiplication is LOW32
without a pre-multiply overflow guard; opaque allocation/zeroing/callback
children and imported HeapAlloc success remain independent conditions. Literal
flag8 alone does not establish a current allocated or initialized bank.

459FC0 reads signedWORD count and searches native slot order. It compares the
argument's LOWWORD against unsigned inclusiveWORD endpoints. First match returns
its slot ordinal; no match supplies AXFFFF, with no wholeEAX signed-1 claim.
Generic parser459933..459943 passes WORD114 to this same catalog lookup and
stores returnedAX into WORD116. Separate WORD118=FFFF remains outside this
resource result. SPI selector0/common-tail initialization is still a condition;
no default11C, category identity, full396, player instance or action permission
is inferred from a resource slot.

## Real text-mode input path

Actual451960 calls402530 and stores its stream for451A90. Both successful final
opener branches use literal rt: fallback opens the original filename, while the
selected compressed branch uses opaque401D20/temporary-file steps before reopen.
Neither a current decoded source nor transform success is observed.

The called mode parser54E343 forms4000h from lowercase t;552D19 forms/stores
low-level fd text bit80h. File refill54EAE3->54EEA7->54EF0C tests that bit.
Its same-buffer CRLF branch skips two input bytes and emits oneLF. A split-buffer
CR requires successful lookahead and, for the relevant regular-file path,
successful seekback. Read errors/nonseekable cases are not generalized.
451A90 and its547A95 line reader do not themselves stripCR;547A95 copies the
translatedLF, and451BE0 removes the finalLF delimiter when copying its token.

Nine complete direct cuts total2208 code bytes plus8 literal bytes. Earlier
qualified451A90/451BE0/parents and402530 coverage remain historical references.
Under a successful stable actual rt stream of the exact retained body+CRLF bytes,
the selected final numeric tokens can therefore satisfy338's normalized-input
premise. Stable compatible ctype during each conversion, actual file/read/seek,
resource output/lifetime and source identity remain explicit unmet conditions.
The older338 seal and its original CRLF gap are preserved;339 adds this conditional
producer proof without relabeling prior evidence or observing native output.

## Exact57 common raw-source catalog

Nonretired historical decoded75c3 is2783008 bytes and remains hashed in place.
Its encoded70a4 lineage is distinct from current encodedef297; no current resource
was decoded. The RomMaps header at line57/offset4374 and rows58..114 occupy
3513 CRLF-inclusive bytes[4374,7887), SHA
1a5c850ba16876b8c28c67d2b1f36c7bcf0670643364f29edc029c6b9cc214e2.

NativeRomMapSourceCatalog pins all57 normalized5-field raw records, their exact
line/offset/body hash, and the complete raw header/provenance. Native token0 slot
and physical source ordinal remain separate fields; both are0..56 only in this
finite dataset. Both path fields are preserved, including source rows whose
paths differ; unread token4 semantics and locale invariance are not invented.
Authority is HISTORICAL_RAW_RESOURCE_SOURCE_ONLY, dataset
tw149c-historical-rommaps-source-v1. Canonical length-prefixed source atoms total
14189 bytes/708 atoms, SHA
99f0feabbc9fd0cddeeddaf6248fbac146e8b11f4a07cc1107cc3a4c71cb959b.

Shared native_raw_resource_source_sets/rows use dataset namespaces. They do not
duplicate TW/CN gameplay tables or fabricate item-family/common-definition IDs
to fit the existing item-specific source schema. The reader uses actual main
tables, guards schema objects, and validates counts, the full envelope and every
raw record with one seed/join SELECT. Independent counts expose orphan rows.
Stored hashes alone cannot qualify changed bytes. Only both installed-empty
tables return an empty vector; partial/missing/corrupt source throws. A caller
transaction is borrowed, otherwise a read transaction is owned.

The explicit importer requires nonnull/autocommit and owns BEGIN IMMEDIATE.
It guards main objects and matching main/TEMP triggers, creates the two source
tables only for an absent schema, validates existing data, inserts only an empty
dataset, then rereads the actual entire dataset before commit. Exact repeats are
idempotent; corrupt/partial source is never replaced. Exceptions roll back schema
and data created by the call. Existing item schema, SQLv1 NULL pins/importer,
MapItem's twoSPI records, saves and frozen behavior are unchanged. CMake's existing
source glob covers the two new files without a build or configuration invocation.

## Concrete conditional C++ composition

lookup_definition_resource holds one outer ReadScope on its connection. Both
nested source readers borrow this same transaction view. It requires a complete
nonempty RomMaps57 dataset and complete nonempty SPI22 before consulting the key.
Thus absent SPI keys cannot skip the other source validation, and unavailable
source cannot silently become a native no-range-match. Missing/empty/corrupt
source is an error; only an absent key after both validations returns none.

All57 index/range inputs are checked and converted before search. Each finite
token0 equals its separately retained slot and source ordinal; token3 fits the
native128-byte destination. The code follows unsigned inclusiveWORD first match
and retains uint16FFFF for a genuine no-match over complete source. It returns
the existing owning scalar/source observation, WORD116 and an owning matching
raw RomMaps record, plus the resource catalog fingerprint. No borrowed SQL/raw
span escapes. No Main/Migration/request/Application calls the new APIs.

194 independently audited numeric source tokens comprise header57,171 RomMaps
index/endpoints and22 SPI icon inputs. All are1..5 ASCII digits, maximum65500,
within signed32 conversion and unsigned16 endpoints; count57 is signedWORD-safe.
57 ranges have lower<=upper and no pairwise overlaps. Header allocation arithmetic
is7524 bytes before alignment. Path3 is at most22 bytes; the finite raw lines fit
the actual line-reader capacity. These are source calculations, not native/API
execution or a general sscanf/overflow model. The audit's canonical23012-byte
conditional numeric source proof hashes
388012cc33c3b86047421438da7f549fbc8b1b442c87af12097138eaa1e6aae5.

| Conditional native slot | Selected SPI records |
|---|---:|
|25|4|
|27|2|
|35|1|
|43|4|
|44|7|
|46|4|

All22 source icon values match; none yieldsFFFF in this pinned source. This result
is qualified by exact normalized inputs/ctype, successful actual line input,
correct-sized live native allocation, full57 native slot population, same catalog
and no bank replacement during lookup, plus SPI common-tail conditions. A coherent
database source view establishes none of those native current-state conditions.
It does not qualify the currentef297 bank, full396, owned/eligible population,
F4 issuer, B1 selection/rules/debit/grant, reply ordering, persistence or recovery.

## Publication and accounting

Successful static source captures are published with original archive placement
semantics; they are not rerun. The seven LF copies under tools/reconstruction are
tw_native_rommaps_loader_capture339.py, tw_native_rommaps_allocation_capture339.py,
tw_native_spi_line_reader_capture339.py, tw_native_rommaps_finite_numeric_capture339.py,
tw_native_rommaps_source_catalog_capture339.py, tw_native_rommaps_temp_guard_capture339.py
and tw_native_rommaps_case_guard_capture339.py. The catalog generator preserves
its initial source stage; the two separately captured guard changes and final
source manifests govern the final importer. All copies are byte-exact to their
respective sealed originals. Failed drafts, correction receipts and heavy
evidence remain in the external archive. All previous seals/parsed ledger fields
and frontier v23 remain intact. This round adds two shared-source C++ files and
composes two existing ones; new opcode/format/parser/phase/handler/complete-route
credit is0. Whole-game/TW denominator and completion remain null.

Next actual full396/current-source qualification, eligibleowned population,
F4 issuer/B1 rules/full reply/storage/recovery and Application hosting remain
open. FullTW/CN/fourWS/sharedtables/common64/coin99999999999/qualifiedstack99/
nativelevels/fonts/textconversion/frozen requirements persist. Native physical
WORD slots/endpoints retain their own widths independently of shared64 gameplay.
PHASE1 permits static source/hash/PE/Capstone/unique-report only; no compiler,
build/tests/runtime/native/VM/codec/gameDBSQL/migrate/activate/deploy.
