# Skill Book Tail Fields: Original Loader Evidence

## Scope

Independent formula-source investigation of current gamedata.csvZ SKB rows,
not the received battle-result/display path. Existing NativeItemMetadata now
admits the SKB section through the original tag-selector rule and59420 parser.
No production rule, database or C++/Lua runtime was changed.

Pinned gamedata SHA256:
70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731.
Pinned native image SHA256:
149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763.
Addresses below are RVAs, base400000. Columns are zero-based.

## Executed Storage

All381 original SKB occurrences run through native tokenization, item parser,
index publication at59A20, lookup59A60 and existing icon resource consumer9B720.
The original first-match tag selector is6. Resource identity is not a formula.
The existing parser harness explicitly adapts CRT `%d`; game parsing, truncation,
field bounds and stores execute original instructions. This is not execution of
the original entire file-open/dispatch path or the original CRT scanf body.

| Source column | Native operation | Record storage |
| --- | --- | --- |
|26|598C9 calls51AE0 string getter;598D2 forces final NUL|11C..12B|
|27|598D9 calls51B50;598E2 stores AL|12C BYTE|
|28|598E8 calls51B50;598F1 stores AL|12D BYTE|
|29|598F7 calls51B50;598FC stores AL|12E BYTE|

224 rows have30 fields;157 have29. Original51B60 checks requested column against
the supplied field count. A missing column yields zero through51BA0 instead of
reading the previous token buffer. Short-row-after-long-row regression confirms
this behavior. Whole record mutations isolate each trailing numeric field to
its single BYTE destination; surrounding bytes and native record canaries hold.

The source is heterogeneous: column28 includes strings such as15min,30min and999;
column29 includes a nonnumeric unlimited label as well as3..7. Under the current
qualified decimal adapter plus original byte stores,15min yields15,999 yields231,
nonnumeric text yields0,256 yields0, and-1 yields255. These are conversion facts,
NOT duration units, damage percentages, MP debit rules or authoritative defaults.

## Consumer Boundary

Static follow-up, not yet an executed UI qualification: FE65B loads item+12C,
and FE661/FE663 select whether to push a disabled flag or call FE4D0 to search
existing entry identities. FE684 passes the result to10CAA0. FE4D0 compares
two identity bytes over pointers from owner+A91C, bounded by owner+AB10.
This inspected edge is an availability-control path, not damage arithmetic.
No numeric meaning is assigned to12D/12E solely from their source values.

## Verification

`test_current_skill_book_fields.py`:3 methods passed in32.226 seconds.
Coverage includes all381 source rows and native lookups,21 independent tail
mutations, and missing-column retention checks. NativeItemMetadata's prior
section behavior is retained; SKB is an additional explicitly admitted section.

Damage/hit/critical/element formulas remain unverified. This source now has
qualified loader storage but no combat coefficient authority. No guessed
formula is enabled and no retired Classic/XJZ source was used.

## Executed tail-byte and existing-entry flag (2026-09-23)

`current_skill_book_availability.py` executes unchanged pinned current-client
instructions from RVA FE65B through the entry of the FE684 call to 10CAA0.
When the tail byte at item+12C is zero, it also executes the complete original
FE4D0 identity lookup. The image, item, identity, owner and owned entry list
are read-only; only a private stack and separately staged destination context
are writable. The first stage stops before FE684; a second stage executes
that original call continuously through 10CB3C, stopping before further
formatting or callbacks. Code outside these exact ranges is rejected.

The actual flag passed in the second stack argument to 10CAA0 is:

```text
item[0x12C] != 0                 -> 0; lookup skipped
item[0x12C] == 0, identity found -> 0
item[0x12C] == 0, not found      -> 1
```

FE4D0 compares both identity bytes against nonnull pointers in the owner
list. The executed cases cover empty, nonmatching, first/middle/last matching
entries and tail values0,1,255. Source-loaded SKB record indices0 and67 have
tail values0 and1 and follow the matching branches. The downstream prefix
stores the flag at context+0x148+4*index for bounded indices0,5,49. It also
chooses one of two explicitly staged context values for a later call. The
exact destination context is synthetic; this proves the original write and
branch, not an on-screen state. The flag's gameplay meaning is still unknown:
these results do not prove skill learning,
ownership authority, book consumption, cooldown, a damage coefficient or
the server rule. No Lua, C++, database or live server gameplay behavior changed.

Pinned path hashes are FE65B..FE683
`56c49e01e2b00986536f1c8343803771904ef1eccf1ded0aa0a533bcbca41135`
and FE4D0..FE51B
`f81aede56ba1c4fc3916eae5ac3dddb529158861b7b88b36b1ce619a4a3dfce7`.
The 10CAA0..10CB3C prefix hash is
`ddc2f0d706b9534fb4c58d79b537851b7888dcf32154f5b80ae205937648a1d8`.
Four `test_current_skill_book_availability.py` methods pass. The owner identity
producer is followed below; the intervening formatter and later callback
remain necessary before assigning a UI or gameplay semantic.

## Continuous owner identity to parsed book lookup (2026-09-23)

`current_skill_book_owner_chain.py` starts at original FE520 with an explicitly
staged owner row and runs continuously through FE592. FE529 reads the page,
FE52F/FE532 scale it by ten, FE54E reads the row pointer from owner+A788,
FE579/FE580 read its two identity bytes, and FE587 calls the full original
A8E10 lookup. The lookup uses previously source-loaded and indexed current
SKB/PFD metadata, the original formatter, string comparison and 59A60 index
search. FE58E publishes the returned item pointer. No game call is skipped or
return value inserted; input rows and metadata pages remain read-only.

Executed cases bind owner identities kind0/id1, kind0/id96 and kind1/id1 on
pages0,1,4 to current source book items6501,6568,6601. Their parsed
item+12C bytes are0,1,0; these match the separate tail-consumer branch tests.
The current kind0/id68 definition searches all candidates and returns no book
pointer, preserving its unmatched status. The lookup harness's bounded
instruction limit was raised for this full miss, while the original code and
inputs were unchanged. Three `test_current_skill_book_owner_chain.py` methods
pass. This is a continuous owner-to-book pointer proof with synthetic owner
membership, not a live player ownership claim. The original FE592..FE65B
formatting path is not yet connected, so the later flag's end-to-end live UI
meaning and all server learning/cost rules remain open.

## Formal SQLite promotion (2026-09-23)

Migration 18 creates `native_skill_books` and `native_skill_book_bindings`.
`tools/strike_lab/import_native_skill_books.py` re-executes the pinned original
SKB row parser and A8E10 identity lookup before any database write. It stores
all 381 SKB source rows, their original parsed 396-byte records, source line and
decoded offset, record hashes, and 381 verified `(kind, skill_id) -> item_id`
bindings. The 67 skill definitions without an SKB match remain absent from the
binding table; no book is fabricated for them. The table refers to the existing
448-row `current-skill-catalog-v1` dataset by foreign key.

The importer requires an identical pinned skill catalog, backs up the configured
database before migration, and compares every stored row inside one transaction.
An incomplete or altered dataset is rejected without replacement. The configured
`god2.db` was backed up to
`artifacts/db-backups/native-skill-books-bfbd84cb5da149fdb483ea7296e432b1.sqlite`
and advanced from schema 15 to 18. Post-import counts are 381 books, 381
bindings and the preexisting 448 skills; `quick_check` and `foreign_key_check`
pass. `ctest -C Release -R ^import_native_skill_books$` passes.

`NativeSkillBookCatalog` now reads a binding and source-backed original record
from the configured SQLite connection. `Application` supplies this borrowed
reader to Lua as `native_skill_book_catalog(kind, definition_id)`; the Lua
result is an owned metadata snapshot. Missing bindings return nil, invalid
selectors and malformed matched rows fail closed. The C++ reader was also
run against the configured imported database for books 6501 and 6601 and the
known unmatched kind0/id68. The native skill book C++, Lua and importer tests
pass. This is an internal data route, not a player item-use action.

No original-client acceptance for book ownership, learning, cost or combat
follows from these read-only queries. The owner row in the continuous native
probe is staged, FE592..FE65B remains unconnected, and a client item-use
command plus server transaction/response is still needed. The current
diagnostic battle skill seed is independent of this table; it cannot serve
as proof of a normal learning flow.
