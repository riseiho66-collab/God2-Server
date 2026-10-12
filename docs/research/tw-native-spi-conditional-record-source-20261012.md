# TW historical SPI conditional396 source composition (round340)

The historical22 SPI source records now have a separately typed, conditional
396-byte source projection. The projection combines exact raw source text,
finite scalar conversion, the native RomMaps first-match relation and the
original successful-allocation initialization. It does not observe a native
record or establish current resource identity, ownership or action permission.

## Original initialization and preserved bytes

The pinned149c mapped image and5fc original PE remain the inputs. The newly
retained complete54A550..54A5A8 method is88 bytes, contains both returns and
has no callees. It writes the requested byte count using an alignment prefix,
REP STOSD and byte suffix, under valid storage, normal DF-clear x86 calling
conditions and fault-free completion. Zero length writes nothing.

The known547E23 allocator retains the original low32 count*stride product.
Its successful small-block path passes(pointer,0,original product) to54A550
at547E9E. The alternate successful kernel32.dll!HeapAlloc path uses flag8,
HEAP_ZERO_MEMORY. That flag's meaning is supported by the official
[Microsoft HeapAlloc documentation](https://learn.microsoft.com/en-us/windows/win32/api/heapapi/nf-heapapi-heapalloc).
No API or native code was executed; failure/retry/callback branches remain
opaque. Small-block alignment padding beyond the requested product is excluded.

The generic-row allocation uses positive signed-WORD count and396-byte stride;
the category allocation uses1602-byte stride. Their positive products do not
overflow32 bits. Successful allocation is still a prerequisite: neither loader
checks a positive-count null result or certifies complete row population.

The original SPI bank declares737 rows; the retained22 occupy physical source
ordinals517..538. The category bank declares46 rows and SPI is ordinal9.
These give requested products291852 and73692 bytes. Retained count22 and a
token0 key never replace those native counts or physical positions. The row
loader advances396 for every physical read, including a rejected token0.
Projection therefore requires the actual preceding-row reads, correct same
allocated slot, valid key-pointer-table storage and no prior out-of-bounds
write, as well as successful selected-row parsing.

Category byte63D has no unconditional parser initializer. Bounded category
strings do not reach it. If all36 tag comparisons return nonzero, it preserves
its allocated zero. The comparator548810 is not newly qualified here. Under
that explicit premise the lookup/dispatcher forwards selector0 to459420;
unsigned guard4596F8 then jumps directly to459933, skipping category writes.

## Complete selected record writes

The complete generic parser has48 direct EBP-relative stores;20 belong to its
common selector0 path. Name, caption and description copies are additional
record writes. Local description scratch initialization does not clear the
record. The selected22 finite strings fit the native regions and scratch
buffers, so their actual full copies cannot reach neighboring record regions.

| Region | Selected source write | Origin of other bytes |
|---|---|---|
|000..007|token5/6 DWORDs, little endian|all bytes overwritten|
|008..02D|token4 string and NUL, then forced2D NUL|preserved allocation zero|
|02E..053|token7 string and NUL, then forced53 NUL|preserved allocation zero|
|054..111|nonempty tokens8..12 with intervening LF, then NUL|preserved allocation zero|
|112..115|token13/3 lowWORDs, little endian|all bytes overwritten|
|116..117|native first matching RomMaps slot AX|all bytes overwritten|
|118..119|literal WORDFFFF|all bytes overwritten|
|11A|tokens14..21 replace all eight bits|all bits overwritten|
|11B|tokens22..25 replace low four bits|high four bits preserve allocation zero|
|11C..18B|no selector0 parser writes|112 bytes preserve allocation zero|

Forced description scratch[189]=0 occurs before the final record copy but
after the unbounded appends. The selected joined descriptions are26..89 bytes,
so this is not a fixed record111 NUL write. Name/caption forced end bytes occur
after their full copies; they are not general overflow protection.

## Additive server source implementation

`NativePetRoomDefinitionRecordSource` owns the existing resource projection,
meaningful text projection and a separate396-byte conditional array. Its
`lookup_definition_record_source` method opens one read scope on the caller's
connection, validates the complete installed RomMaps57 and SPI22 sources via
the existing resource method before an absent-key return, then reads the text
in the same borrowed scope. Both owning SPI source records must agree.

The array starts at zero under the public initialization premises. Explicit
little-endian stores and bounded copies reproduce the selected writes above.
Missing, empty or corrupt sources remain errors; a source key absent from the
complete installed dataset returns no source projection. A caller-owned
transaction remains its source view and is never committed by the method.

Every required native premise is retained in the public type: exact historical
decoded input and successful rt translation/read/seek, stable compatible
classification and finite conversions, valid successful allocations, complete
row/slot selection and population, all36 nonzero category comparisons,
selector0, stable empty/LF literals, fault-free ordinary helper completion and
no intervening or out-of-bounds writes. The array does not certify that those
premises held in a native process. Current encoded ef297 resource equivalence
and actual loaded bank state remain unobserved.

The historical item SQLv1 pins, readers, text/scalar/resource projections and
importer are unchanged. The frozen four-family
`NativeItemDefinitionObservation` and two-SPI `NativeMapItemCatalog` remain
unchanged. No Main, Migration, gameplay handler or native provider invokes this
method; byte11C=0 in the conditional array cannot grant PetEgg eligibility.

## Evidence and publication

External immutable packages under the owned20261012 archive:

- `tw-native-spi-allocation-zero-source-340`: complete88-byte child and exact
  caller/import/category continuity; previous complete methods receive no new credit.
- `tw-native-spi-generic-record-write-source-340`: all direct/helper stores,
  per-byte masks, preserved tails and excluded category alternatives.
- `round340-spi-conditional-record-source-audit`: independent finite22 source
  composition and per-record conditional byte proofs.
- `round340-spi-conditional-record-implementation`: additive C++ source recipe
  and retained before/after source custody.
- `round340-protocol-source-review`: final independent static review.

The independent22 arrays total8712 bytes; concatenation SHA256 is
`df6d876a3c5cb3b0d59b9cd2f653696b8401ecbbf41fc50c7e72647a55f89afa`.
The12994-byte canonical conditional proof has SHA256
`242ec2de0b202a5f772b48285474fd45aadb03928bec1b1224735253281a3618`.
These hashes describe conditional source composition, not native output.

Exact publication names under `tools/reconstruction`:

- `tw_native_spi_allocation_zero_capture340.py`
- `tw_native_spi_record_writes_capture340.py`
- `tw_native_spi_conditional_record_audit340.py`
- `tw_native_spi_conditional_record_source_capture340.py`

Successful LF capture/implementation scripts are published as exact copies;
earlier probes, drafts, failures and seals remain preserved. Original images
and the large decoded source are hashed/read in place, without bulk copies.
No build, compiler, test, API, native execution, codec, database SQL, migration,
activation or deployment occurred. The unique packet report records zero new
opcode, format, handler, phase binding or completed gameplay route credit.
TW/CN and all four browser endpoints retain the existing common-core goal;
the whole-game denominator and completion percentage remain unknown.
